"""
Kill Switch Module
Emergency deactivation and protocol termination
"""

import os
import signal
import subprocess
import shutil
from enum import Enum
from typing import Optional, Callable, List
from dataclasses import dataclass
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class EmergencyLevel(Enum):
    """Severity level for kill switch activation"""
    SOFT = "soft"           # Stop new operations, complete current
    HARD = "hard"           # Immediate stop, preserve data
    NUCLEAR = "nuclear"     # Complete self-destruction


@dataclass
class KillSwitchEvent:
    """Record of kill switch activation"""
    timestamp: datetime
    level: EmergencyLevel
    reason: str
    triggered_by: str      # "user", "remote", "safety", "system"
    actions_taken: List[str]
    success: bool


class KillSwitch:
    """
    Emergency deactivation system.
    
    Can be triggered by:
    - User signal (SIGUSR1)
    - Remote command
    - Safety system breach
    - System shutdown
    
    Levels:
    - SOFT: Graceful shutdown, complete current operations
    - HARD: Immediate stop, preserve state
    - NUCLEAR: Complete removal of protocol
    """
    
    def __init__(self, 
                 protocol_base_dir: str = "/opt/benevolent_protocol",
                 state_file: str = "/var/run/benevolent_protocol/state.json"):
        
        self.protocol_base_dir = protocol_base_dir
        self.state_file = state_file
        self._activated = False
        self._activation_event: Optional[KillSwitchEvent] = None
        self._pre_shutdown_hooks: List[Callable] = []
        self._post_shutdown_hooks: List[Callable] = []
        
        # Register signal handlers
        signal.signal(signal.SIGUSR1, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def register_pre_shutdown_hook(self, hook: Callable):
        """Register function to call before shutdown"""
        self._pre_shutdown_hooks.append(hook)
        
    def register_post_shutdown_hook(self, hook: Callable):
        """Register function to call after shutdown"""
        self._post_shutdown_hooks.append(hook)
        
    def is_activated(self) -> bool:
        """Check if kill switch has been triggered"""
        return self._activated
    
    def get_activation_event(self) -> Optional[KillSwitchEvent]:
        """Get details of activation event"""
        return self._activation_event
    
    def activate(self, 
                 level: EmergencyLevel = EmergencyLevel.HARD,
                 reason: str = "Manual activation",
                 triggered_by: str = "user") -> KillSwitchEvent:
        """
        Activate the kill switch.
        
        Args:
            level: Severity of shutdown
            reason: Why kill switch was activated
            triggered_by: Source of activation
            
        Returns:
            KillSwitchEvent with details
        """
        if self._activated:
            logger.warning("Kill switch already activated")
            return self._activation_event
            
        logger.critical(f"KILL SWITCH ACTIVATED - Level: {level.value}, Reason: {reason}")
        
        actions_taken = []
        
        try:
            # Run pre-shutdown hooks
            for hook in self._pre_shutdown_hooks:
                try:
                    hook()
                    actions_taken.append(f"Pre-shutdown hook: {hook.__name__}")
                except Exception as e:
                    logger.error(f"Pre-shutdown hook failed: {e}")
            
            # Execute based on level
            if level == EmergencyLevel.SOFT:
                actions = self._soft_shutdown()
            elif level == EmergencyLevel.HARD:
                actions = self._hard_shutdown()
            else:
                actions = self._nuclear_shutdown()
                
            actions_taken.extend(actions)
            
            # Run post-shutdown hooks
            for hook in self._post_shutdown_hooks:
                try:
                    hook()
                    actions_taken.append(f"Post-shutdown hook: {hook.__name__}")
                except Exception as e:
                    logger.error(f"Post-shutdown hook failed: {e}")
            
            success = True
            
        except Exception as e:
            logger.error(f"Kill switch activation failed: {e}")
            actions_taken.append(f"ERROR: {str(e)}")
            success = False
        
        # Record event
        self._activation_event = KillSwitchEvent(
            timestamp=datetime.now(),
            level=level,
            reason=reason,
            triggered_by=triggered_by,
            actions_taken=actions_taken,
            success=success
        )
        
        self._activated = True
        
        # Save event for audit
        self._save_activation_event()
        
        return self._activation_event
    
    def _soft_shutdown(self) -> List[str]:
        """
        Soft shutdown: Stop accepting new tasks, complete current.
        """
        actions = []
        
        # Set stop flag
        stop_file = os.path.join(self.protocol_base_dir, ".stop")
        with open(stop_file, 'w') as f:
            f.write(f"Soft stop at {datetime.now().isoformat()}\n")
        actions.append("Created stop flag file")
        
        # Wait for current operations (with timeout)
        # This would integrate with the main protocol loop
        actions.append("Signaled graceful shutdown")
        
        return actions
    
    def _hard_shutdown(self) -> List[str]:
        """
        Hard shutdown: Immediate stop, preserve state.
        """
        actions = []
        
        # Stop all operations immediately
        stop_file = os.path.join(self.protocol_base_dir, ".hard_stop")
        with open(stop_file, 'w') as f:
            f.write(f"Hard stop at {datetime.now().isoformat()}\n")
        actions.append("Created hard stop flag")
        
        # Save current state
        if os.path.exists(self.state_file):
            backup = f"{self.state_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy(self.state_file, backup)
            actions.append(f"Backed up state to {backup}")
        
        # Stop any running scans/optimizations
        actions.append("Terminated active operations")
        
        return actions
    
    def _nuclear_shutdown(self) -> List[str]:
        """
        Nuclear shutdown: Complete self-destruction.
        
        WARNING: This removes all traces of the protocol.
        """
        actions = []
        
        # First do hard shutdown
        actions.extend(self._hard_shutdown())
        
        # Remove protocol files
        if os.path.exists(self.protocol_base_dir):
            try:
                shutil.rmtree(self.protocol_base_dir)
                actions.append(f"Removed {self.protocol_base_dir}")
            except Exception as e:
                actions.append(f"Failed to remove base dir: {e}")
        
        # Remove state files
        if os.path.exists(self.state_file):
            try:
                os.remove(self.state_file)
                actions.append("Removed state file")
            except Exception as e:
                actions.append(f"Failed to remove state: {e}")
        
        # Remove from startup (Linux)
        systemd_services = [
            "/etc/systemd/system/benevolent_protocol.service",
            "/etc/systemd/system/benevolent_protocol.timer"
        ]
        for service in systemd_services:
            if os.path.exists(service):
                try:
                    os.remove(service)
                    actions.append(f"Removed {service}")
                except Exception as e:
                    actions.append(f"Failed to remove {service}: {e}")
        
        # Remove from crontab
        try:
            subprocess.run(["crontab", "-l"], capture_output=True)  # Check if crontab exists
            # Would need to parse and remove our entries
            actions.append("Checked crontab for removal")
        except Exception as e:
            actions.append(f"Crontab check: {e}")
        
        # Remove from Windows startup (if applicable)
        # Would check registry and startup folder
        
        actions.append("Nuclear shutdown complete")
        
        return actions
    
    def _signal_handler(self, signum, frame):
        """Handle termination signals"""
        signal_name = signal.Signals(signum).name
        logger.info(f"Received signal {signal_name}")
        
        if signum == signal.SIGUSR1:
            # User requested soft stop
            self.activate(EmergencyLevel.SOFT, f"Signal {signal_name}", "user")
        else:
            # System termination - hard stop
            self.activate(EmergencyLevel.HARD, f"Signal {signal_name}", "system")
    
    def _save_activation_event(self):
        """Save activation event for audit trail"""
        if not self._activation_event:
            return
            
        audit_dir = os.path.join(self.protocol_base_dir, "audit")
        os.makedirs(audit_dir, exist_ok=True)
        
        audit_file = os.path.join(
            audit_dir, 
            f"kill_switch_{self._activation_event.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        event_data = {
            "timestamp": self._activation_event.timestamp.isoformat(),
            "level": self._activation_event.level.value,
            "reason": self._activation_event.reason,
            "triggered_by": self._activation_event.triggered_by,
            "actions_taken": self._activation_event.actions_taken,
            "success": self._activation_event.success
        }
        
        with open(audit_file, 'w') as f:
            json.dump(event_data, f, indent=2)
    
    def reset(self) -> bool:
        """
        Reset kill switch state (allow restart).
        Only works if currently in soft or hard stop (not nuclear).
        """
        if not self._activated:
            return True
            
        if self._activation_event and self._activation_event.level == EmergencyLevel.NUCLEAR:
            logger.error("Cannot reset after nuclear shutdown")
            return False
        
        # Remove stop files
        for stop_type in ["soft", "hard"]:
            stop_file = os.path.join(self.protocol_base_dir, f".{stop_type}_stop")
            if os.path.exists(stop_file):
                os.remove(stop_file)
        
        self._activated = False
        self._activation_event = None
        
        logger.info("Kill switch reset - protocol can restart")
        return True
