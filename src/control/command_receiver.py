"""
Command Receiver Module
Receives and processes remote instructions
"""

import json
import hashlib
import hmac
import logging
from enum import Enum
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import socket

logger = logging.getLogger(__name__)


class CommandType(Enum):
    """Types of remote commands"""
    # Status commands
    STATUS = "status"
    PING = "ping"
    VERSION = "version"
    
    # Control commands
    STOP = "stop"
    START = "start"
    RESTART = "restart"
    KILL = "kill"
    
    # Operation commands
    SCAN = "scan"
    OPTIMIZE = "optimize"
    PROPAGATE = "propagate"
    QUARANTINE = "quarantine"
    
    # Configuration commands
    UPDATE_CONFIG = "update_config"
    SET_SCHEDULE = "set_schedule"
    SET_TARGETS = "set_targets"
    
    # Update commands
    UPDATE_PROTOCOL = "update_protocol"
    UPDATE_SIGNATURES = "update_signatures"
    
    # Telemetry commands
    REQUEST_REPORT = "request_report"
    REQUEST_LOGS = "request_logs"


@dataclass
class Command:
    """A validated command from remote source"""
    command_id: str
    command_type: CommandType
    timestamp: datetime
    source: str              # Identifier of command source
    parameters: Dict[str, Any]
    signature: str
    expires_at: Optional[datetime]
    
    def is_expired(self) -> bool:
        """Check if command has expired"""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "command_id": self.command_id,
            "command_type": self.command_type.value,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "parameters": self.parameters,
            "signature": self.signature,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }


class CommandReceiver:
    """
    Receives and validates remote commands.
    
    Security measures:
    - HMAC signature verification
    - Command expiration
    - Rate limiting
    - Source allowlist
    - Audit logging
    """
    
    def __init__(self,
                 secret_key: str,
                 allowed_sources: Optional[list] = None,
                 command_timeout: int = 300,  # 5 minutes
                 max_commands_per_minute: int = 10):
        
        self.secret_key = secret_key.encode()
        self.allowed_sources = allowed_sources or []
        self.command_timeout = command_timeout
        self.rate_limit = max_commands_per_minute
        
        self._command_handlers: Dict[CommandType, Callable] = {}
        self._command_history: list = []
        self._rate_limit_tracker: Dict[str, list] = {}
        
        # Register default handlers
        self._register_default_handlers()
    
    def register_handler(self, command_type: CommandType, handler: Callable):
        """Register a handler for a command type"""
        self._command_handlers[command_type] = handler
        logger.info(f"Registered handler for {command_type.value}")
    
    def _register_default_handlers(self):
        """Register built-in command handlers"""
        self.register_handler(CommandType.PING, self._handle_ping)
        self.register_handler(CommandType.STATUS, self._handle_status)
        self.register_handler(CommandType.VERSION, self._handle_version)
    
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify HMAC signature of command payload.
        
        Args:
            payload: Raw command bytes
            signature: Provided signature (hex)
            
        Returns:
            True if signature is valid
        """
        expected = hmac.new(self.secret_key, payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature, expected)
    
    def parse_command(self, raw_data: str, signature: str) -> Optional[Command]:
        """
        Parse and validate a raw command string.
        
        Args:
            raw_data: JSON command string
            signature: HMAC signature
            
        Returns:
            Command object if valid, None otherwise
        """
        try:
            # Verify signature
            if not self.verify_signature(raw_data.encode(), signature):
                logger.warning("Command signature verification failed")
                return None
            
            # Parse JSON
            data = json.loads(raw_data)
            
            # Validate required fields
            required = ["command_id", "command_type", "timestamp", "source"]
            if not all(k in data for k in required):
                logger.warning("Command missing required fields")
                return None
            
            # Parse command type
            try:
                cmd_type = CommandType(data["command_type"])
            except ValueError:
                logger.warning(f"Unknown command type: {data['command_type']}")
                return None
            
            # Check source allowlist
            if self.allowed_sources and data["source"] not in self.allowed_sources:
                logger.warning(f"Command from unauthorized source: {data['source']}")
                return None
            
            # Parse timestamps
            timestamp = datetime.fromisoformat(data["timestamp"])
            expires = None
            if data.get("expires_at"):
                expires = datetime.fromisoformat(data["expires_at"])
            
            # Create command object
            command = Command(
                command_id=data["command_id"],
                command_type=cmd_type,
                timestamp=timestamp,
                source=data["source"],
                parameters=data.get("parameters", {}),
                signature=signature,
                expires_at=expires
            )
            
            # Check expiration
            if command.is_expired():
                logger.warning(f"Command {command.command_id} has expired")
                return None
            
            # Check rate limit
            if not self._check_rate_limit(data["source"]):
                logger.warning(f"Rate limit exceeded for source: {data['source']}")
                return None
            
            return command
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse command JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing command: {e}")
            return None
    
    def _check_rate_limit(self, source: str) -> bool:
        """Check if source is within rate limit"""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # Initialize tracker for source
        if source not in self._rate_limit_tracker:
            self._rate_limit_tracker[source] = []
        
        # Clean old entries
        self._rate_limit_tracker[source] = [
            t for t in self._rate_limit_tracker[source] 
            if t > minute_ago
        ]
        
        # Check limit
        if len(self._rate_limit_tracker[source]) >= self.rate_limit:
            return False
        
        # Record this request
        self._rate_limit_tracker[source].append(now)
        return True
    
    async def execute_command(self, command: Command) -> Dict[str, Any]:
        """
        Execute a validated command.
        
        Args:
            command: Validated Command object
            
        Returns:
            Result dictionary with status and data
        """
        result = {
            "command_id": command.command_id,
            "command_type": command.command_type.value,
            "executed_at": datetime.now().isoformat(),
            "success": False,
            "message": "",
            "data": None
        }
        
        # Record in history
        self._command_history.append({
            "command": command.to_dict(),
            "executed_at": result["executed_at"]
        })
        
        # Get handler
        handler = self._command_handlers.get(command.command_type)
        if not handler:
            result["message"] = f"No handler for command type: {command.command_type.value}"
            logger.error(result["message"])
            return result
        
        # Execute
        try:
            handler_result = await handler(command.parameters)
            result["success"] = True
            result["data"] = handler_result
            result["message"] = "Command executed successfully"
            logger.info(f"Executed command {command.command_id}")
            
        except Exception as e:
            result["message"] = f"Command execution failed: {str(e)}"
            logger.error(f"Command {command.command_id} failed: {e}")
        
        return result
    
    # Default handlers
    
    async def _handle_ping(self, params: Dict) -> Dict:
        """Handle PING command"""
        return {"pong": True, "timestamp": datetime.now().isoformat()}
    
    async def _handle_status(self, params: Dict) -> Dict:
        """Handle STATUS command"""
        return {
            "status": "running",
            "uptime": "N/A",  # Would track actual uptime
            "commands_processed": len(self._command_history),
            "last_command": self._command_history[-1] if self._command_history else None
        }
    
    async def _handle_version(self, params: Dict) -> Dict:
        """Handle VERSION command"""
        return {
            "version": "0.2.0-alpha",
            "protocol_version": "1.0"
        }
    
    def get_command_history(self, limit: int = 100) -> list:
        """Get recent command history"""
        return self._command_history[-limit:]


class CommandListener:
    """
    Listens for incoming commands on a socket.
    """
    
    def __init__(self, 
                 receiver: CommandReceiver,
                 host: str = "127.0.0.1",
                 port: int = 9527):
        
        self.receiver = receiver
        self.host = host
        self.port = port
        self._running = False
        self._server = None
    
    async def start(self):
        """Start listening for commands"""
        self._running = True
        self._server = await asyncio.start_server(
            self._handle_connection,
            self.host,
            self.port
        )
        
        logger.info(f"Command listener started on {self.host}:{self.port}")
        
        async with self._server:
            await self._server.serve_forever()
    
    async def stop(self):
        """Stop listening"""
        self._running = False
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        logger.info("Command listener stopped")
    
    async def _handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle incoming connection"""
        try:
            # Read command data
            data = await reader.read(4096)
            if not data:
                return
            
            # Parse format: {signature}\n{json_payload}
            try:
                signature, payload = data.decode().split('\n', 1)
            except ValueError:
                logger.warning("Malformed command format")
                writer.write(b'ERROR: Invalid format\n')
                await writer.drain()
                return
            
            # Parse and validate command
            command = self.receiver.parse_command(payload, signature)
            if not command:
                writer.write(b'ERROR: Invalid command\n')
                await writer.drain()
                return
            
            # Execute command
            result = await self.receiver.execute_command(command)
            
            # Send response
            response = json.dumps(result) + '\n'
            writer.write(response.encode())
            await writer.drain()
            
        except Exception as e:
            logger.error(f"Error handling connection: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
