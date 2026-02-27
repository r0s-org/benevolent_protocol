"""
Heartbeat Manager Module
Maintains communication with control servers
"""

import asyncio
import logging
from typing import Optional, Callable, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class HeartbeatStatus:
    """Status of last heartbeat"""
    timestamp: datetime
    success: bool
    latency_ms: Optional[int]
    server_response: Optional[str]
    error_message: Optional[str]


class HeartbeatManager:
    """
    Manages periodic heartbeat signals to control servers.
    
    Features:
    - Configurable interval
    - Automatic retry on failure
    - Latency tracking
    - Dead man's switch (alert if missed heartbeats)
    """
    
    def __init__(self,
                 endpoint: Optional[str] = None,
                 interval: int = 60,          # seconds
                 timeout: int = 10,           # seconds
                 max_failures: int = 3,
                 on_failure: Optional[Callable] = None,
                 on_recovery: Optional[Callable] = None):
        
        self.endpoint = endpoint
        self.interval = interval
        self.timeout = timeout
        self.max_failures = max_failures
        
        # Callbacks
        self.on_failure = on_failure
        self.on_recovery = on_recovery
        
        # State tracking
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._last_heartbeat: Optional[HeartbeatStatus] = None
        self._consecutive_failures = 0
        self._total_heartbeats = 0
        self._successful_heartbeats = 0
        self._last_success: Optional[datetime] = None
        
        # Dead man's switch
        self._dead_man_timeout = interval * max_failures * 2
        self._last_checkin: Optional[datetime] = None
    
    async def start(self):
        """Start heartbeat loop"""
        if self._running:
            logger.warning("Heartbeat already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._heartbeat_loop())
        logger.info(f"Heartbeat started (interval: {self.interval}s)")
    
    async def stop(self):
        """Stop heartbeat loop"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Heartbeat stopped")
    
    async def _heartbeat_loop(self):
        """Main heartbeat loop"""
        while self._running:
            try:
                await self._send_heartbeat()
                await asyncio.sleep(self.interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat loop error: {e}")
                await asyncio.sleep(self.interval)
    
    async def _send_heartbeat(self):
        """Send a single heartbeat"""
        self._total_heartbeats += 1
        start_time = datetime.now()
        
        if not self.endpoint:
            # No endpoint configured - just update internal state
            self._last_heartbeat = HeartbeatStatus(
                timestamp=start_time,
                success=True,
                latency_ms=0,
                server_response="No endpoint configured",
                error_message=None
            )
            self._last_checkin = start_time
            return
        
        try:
            # Send heartbeat request
            import aiohttp
            
            payload = {
                "timestamp": start_time.isoformat(),
                "protocol_version": "0.2.0-alpha",
                "status": "alive"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.endpoint}/heartbeat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    
                    latency = int((datetime.now() - start_time).total_seconds() * 1000)
                    
                    if response.status == 200:
                        response_text = await response.text()
                        self._handle_success(latency, response_text)
                    else:
                        self._handle_failure(f"HTTP {response.status}")
                        
        except asyncio.TimeoutError:
            self._handle_failure("Timeout")
        except Exception as e:
            self._handle_failure(str(e))
    
    def _handle_success(self, latency_ms: int, response: str):
        """Handle successful heartbeat"""
        self._last_heartbeat = HeartbeatStatus(
            timestamp=datetime.now(),
            success=True,
            latency_ms=latency_ms,
            server_response=response,
            error_message=None
        )
        
        self._successful_heartbeats += 1
        self._consecutive_failures = 0
        self._last_success = datetime.now()
        self._last_checkin = datetime.now()
        
        logger.debug(f"Heartbeat OK (latency: {latency_ms}ms)")
        
        # Recovery callback
        if self.on_recovery and self._consecutive_failures > 0:
            try:
                self.on_recovery()
            except Exception as e:
                logger.error(f"Recovery callback error: {e}")
    
    def _handle_failure(self, error: str):
        """Handle failed heartbeat"""
        self._last_heartbeat = HeartbeatStatus(
            timestamp=datetime.now(),
            success=False,
            latency_ms=None,
            server_response=None,
            error_message=error
        )
        
        self._consecutive_failures += 1
        logger.warning(f"Heartbeat failed ({self._consecutive_failures}/{self.max_failures}): {error}")
        
        # Failure callback
        if self.consecutive_failures >= self.max_failures and self.on_failure:
            try:
                self.on_failure(self._consecutive_failures)
            except Exception as e:
                logger.error(f"Failure callback error: {e}")
    
    @property
    def consecutive_failures(self) -> int:
        """Get consecutive failure count"""
        return self._consecutive_failures
    
    @property
    def is_healthy(self) -> bool:
        """Check if heartbeat is healthy"""
        if not self._last_heartbeat:
            return False
        return self._last_heartbeat.success
    
    def check_dead_man(self) -> bool:
        """
        Check dead man's switch.
        Returns True if checkin is recent enough.
        """
        if not self._last_checkin:
            return False
        
        elapsed = datetime.now() - self._last_checkin
        return elapsed.total_seconds() < self._dead_man_timeout
    
    def get_status(self) -> Dict[str, Any]:
        """Get heartbeat status summary"""
        return {
            "running": self._running,
            "endpoint": self.endpoint,
            "interval": self.interval,
            "is_healthy": self.is_healthy,
            "consecutive_failures": self._consecutive_failures,
            "total_heartbeats": self._total_heartbeats,
            "successful_heartbeats": self._successful_heartbeats,
            "success_rate": (
                self._successful_heartbeats / self._total_heartbeats 
                if self._total_heartbeats > 0 else 0
            ),
            "last_heartbeat": (
                self._last_heartbeat.timestamp.isoformat() 
                if self._last_heartbeat else None
            ),
            "last_success": (
                self._last_success.isoformat() 
                if self._last_success else None
            ),
            "dead_man_ok": self.check_dead_man()
        }
    
    async def send_manual_heartbeat(self) -> HeartbeatStatus:
        """Send an immediate heartbeat outside the normal schedule"""
        await self._send_heartbeat()
        return self._last_heartbeat
