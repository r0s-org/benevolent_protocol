"""
Stealth Operations Module
Dynamic evasion and concealment techniques
"""

import os
import sys
import time
import random
import subprocess
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
import hashlib
import base64


@dataclass
class StealthProfile:
    """Stealth configuration profile"""
    name: str
    process_name: str  # What to appear as in process list
    behavior_delay_range: tuple  # (min, max) seconds between actions
    jitter_enabled: bool  # Add randomness to timing
    traffic_shaping: bool  # Mimic normal traffic patterns
    evasion_level: str  # "low", "medium", "high", "maximum"


class DynamicStealth:
    """
    Dynamic stealth operations and evasion techniques.
    Adapts behavior to avoid detection while maintaining benevolence.
    """

    def __init__(self, evasion_level: str = "medium"):
        self.evasion_level = evasion_level
        self.stealth_profiles = self._load_stealth_profiles()
        self.current_profile = self.stealth_profiles.get(evasion_level, self.stealth_profiles["medium"])
        self.detection_evasion_active = False

    def _load_stealth_profiles(self) -> Dict[str, StealthProfile]:
        """
        Load stealth profiles for different evasion levels.
        """
        return {
            "low": StealthProfile(
                name="Minimal Stealth",
                process_name="python3",  # Appear as normal Python process
                behavior_delay_range=(1, 3),
                jitter_enabled=False,
                traffic_shaping=False,
                evasion_level="low"
            ),
            "medium": StealthProfile(
                name="Standard Stealth",
                process_name="systemd-optim",  # Appear as system service
                behavior_delay_range=(5, 15),
                jitter_enabled=True,
                traffic_shaping=True,
                evasion_level="medium"
            ),
            "high": StealthProfile(
                name="Advanced Stealth",
                process_name="systemd-networkd",  # Appear as network daemon
                behavior_delay_range=(10, 30),
                jitter_enabled=True,
                traffic_shaping=True,
                evasion_level="high"
            ),
            "maximum": StealthProfile(
                name="Maximum Stealth",
                process_name="kernel-optim",  # Appear as kernel process
                behavior_delay_range=(30, 120),
                jitter_enabled=True,
                traffic_shaping=True,
                evasion_level="maximum"
            )
        }

    def apply_jitter(self, base_delay: float) -> float:
        """
        Add random jitter to delay times.
        Makes behavior patterns less predictable.
        """
        if not self.current_profile.jitter_enabled:
            return base_delay

        # Add ±30% random jitter
        jitter = base_delay * random.uniform(-0.3, 0.3)
        return max(0.1, base_delay + jitter)

    def get_behavior_delay(self) -> float:
        """
        Get randomized delay between actions.
        Based on current stealth profile.
        """
        min_delay, max_delay = self.current_profile.behavior_delay_range

        # Random delay within range
        base_delay = random.uniform(min_delay, max_delay)

        # Apply jitter if enabled
        return self.apply_jitter(base_delay)

    def should_act_now(self, probability: float = 0.5) -> bool:
        """
        Probabilistic decision making.
        Adds unpredictability to behavior.
        """
        return random.random() < probability

    def shape_traffic_pattern(self) -> Dict[str, float]:
        """
        Generate traffic shaping parameters.
        Mimics normal network behavior.
        """
        if not self.current_profile.traffic_shaping:
            return {
                "burst_probability": 0.0,
                "burst_size": 1,
                "idle_probability": 0.0
            }

        # Normal traffic has bursts and idle periods
        return {
            "burst_probability": random.uniform(0.1, 0.3),  # 10-30% chance of burst
            "burst_size": random.randint(2, 5),  # 2-5 packets per burst
            "idle_probability": random.uniform(0.2, 0.4)  # 20-40% chance of idle
        }

    def detect_analysis_environment(self) -> Dict[str, bool]:
        """
        Detect if running in analysis/sandbox environment.
        Returns indicators of analysis tools.
        """
        indicators = {
            "vm_detected": self._detect_vm(),
            "debugger_detected": self._detect_debugger(),
            "sandbox_detected": self._detect_sandbox(),
            "monitoring_tools": self._detect_monitoring_tools(),
            "analysis_mode": False
        }

        # If any indicators are true, likely in analysis environment
        indicators["analysis_mode"] = any([
            indicators["vm_detected"],
            indicators["debugger_detected"],
            indicators["sandbox_detected"],
            indicators["monitoring_tools"]
        ])

        return indicators

    def _detect_vm(self) -> bool:
        """Detect virtual machine indicators"""
        vm_indicators = [
            "/sys/class/dmi/id/product_name",  # VM product names
            "/sys/hypervisor/properties/capabilities",
        ]

        try:
            # Check common VM indicators
            if os.path.exists(vm_indicators[0]):
                with open(vm_indicators[0], 'r') as f:
                    content = f.read().lower()
                    vm_keywords = ['vmware', 'virtualbox', 'qemu', 'kvm', 'xen', 'hyper-v']
                    if any(keyword in content for keyword in vm_keywords):
                        return True

            # Check for hypervisor
            if os.path.exists("/sys/hypervisor"):
                return True

        except:
            pass

        return False

    def _detect_debugger(self) -> bool:
        """Detect debugger presence"""
        try:
            # Linux: Check if being traced
            if os.path.exists("/proc/self/status"):
                with open("/proc/self/status", 'r') as f:
                    for line in f:
                        if "TracerPid" in line and line.split(':')[1].strip() != '0':
                            return True
        except:
            pass

        return False

    def _detect_sandbox(self) -> bool:
        """Detect sandbox environment"""
        sandbox_indicators = [
            "/tmp/sandbox",
            "/.dockerenv",
            "/var/run/sandbox",
        ]

        for indicator in sandbox_indicators:
            if os.path.exists(indicator):
                return True

        # Check for common sandbox usernames
        try:
            import getpass
            username = getpass.getuser().lower()
            sandbox_users = ['sandbox', 'virus', 'malware', 'sample', 'test']
            if any(user in username for user in sandbox_users):
                return True
        except:
            pass

        return False

    def _detect_monitoring_tools(self) -> bool:
        """Detect monitoring/analysis tools"""
        monitoring_processes = [
            'wireshark', 'tcpdump', 'procmon', 'sysmon',
            'processhacker', 'procexp', 'volatility', 'radare'
        ]

        try:
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode == 0:
                processes = result.stdout.lower()
                for tool in monitoring_processes:
                    if tool in processes:
                        return True

        except:
            pass

        return False

    def get_evasion_strategy(self) -> Dict[str, any]:
        """
        Get current evasion strategy based on environment.
        Adapts behavior to avoid detection.
        """
        analysis_check = self.detect_analysis_environment()

        if analysis_check["analysis_mode"]:
            # Detected analysis environment - be extra careful
            return {
                "action": "minimal",
                "delay_multiplier": 5.0,  # Slow down significantly
                "stealth_level": "maximum",
                "reason": "Analysis environment detected"
            }

        # Normal environment - use configured stealth level
        return {
            "action": "normal",
            "delay_multiplier": 1.0,
            "stealth_level": self.evasion_level,
            "reason": "Normal environment"
        }

    def obfuscate_timing(self, action_count: int) -> List[float]:
        """
        Generate obfuscated timing schedule for actions.
        Makes pattern analysis difficult.
        """
        schedule = []

        for i in range(action_count):
            # Get base delay
            delay = self.get_behavior_delay()

            # Add variance based on action number
            variance = (i % 5) * 0.5  # Add pattern variance

            # Apply traffic shaping
            if self.current_profile.traffic_shaping:
                pattern = self.shape_traffic_pattern()

                # Add burst behavior
                if random.random() < pattern["burst_probability"]:
                    delay /= pattern["burst_size"]  # Faster during burst

                # Add idle behavior
                if random.random() < pattern["idle_probability"]:
                    delay *= 3  # Longer idle period

            schedule.append(delay + variance)

        return schedule

    def mimic_legitimate_behavior(self) -> Dict[str, any]:
        """
        Generate behavior pattern that mimics legitimate system processes.
        """
        return {
            "cpu_usage_pattern": self._generate_cpu_pattern(),
            "memory_usage_pattern": self._generate_memory_pattern(),
            "network_pattern": self._generate_network_pattern(),
            "disk_io_pattern": self._generate_disk_pattern()
        }

    def _generate_cpu_pattern(self) -> List[float]:
        """Generate CPU usage pattern (0-100%)"""
        # Legitimate processes have varying CPU usage
        pattern = []
        for i in range(10):
            # Low CPU most of the time, occasional spikes
            if random.random() < 0.8:
                pattern.append(random.uniform(0.1, 5.0))  # Low usage
            else:
                pattern.append(random.uniform(10.0, 30.0))  # Occasional spike

        return pattern

    def _generate_memory_pattern(self) -> List[float]:
        """Generate memory usage pattern (MB)"""
        # Legitimate processes have stable memory with slow growth
        base = random.uniform(50, 200)  # Base memory usage
        pattern = []

        for i in range(10):
            # Slow, gradual growth
            growth = i * random.uniform(0.5, 2.0)
            pattern.append(base + growth)

        return pattern

    def _generate_network_pattern(self) -> Dict[str, any]:
        """Generate network traffic pattern"""
        return {
            "bytes_per_second": random.uniform(100, 1000),  # Low bandwidth
            "packets_per_second": random.uniform(1, 5),
            "connection_duration": random.uniform(5, 30),
            "idle_intervals": random.uniform(30, 120)
        }

    def _generate_disk_pattern(self) -> Dict[str, any]:
        """Generate disk I/O pattern"""
        return {
            "read_bytes_per_second": random.uniform(1000, 10000),
            "write_bytes_per_second": random.uniform(500, 5000),
            "io_operations_per_second": random.uniform(1, 10)
        }

    def generate_noise_traffic(self) -> Dict[str, any]:
        """
        Generate noise/chaff traffic to confuse analysis.
        """
        return {
            "fake_connections": random.randint(1, 5),
            "fake_dns_queries": random.randint(2, 8),
            "timing_noise": random.uniform(0.1, 1.0),
            "decoy_domains": [
                "update.microsoft.com",
                "cdn.windows.net",
                "checkip.dyndns.org"
            ]
        }

    def adapt_to_detection(self, detection_event: str) -> Dict[str, any]:
        """
        Adapt behavior in response to detection attempts.
        Dynamic stealth adjustment.
        """
        adaptations = {
            "port_scan_detected": {
                "action": "go_silent",
                "duration": 300,  # 5 minutes
                "stealth_increase": 2
            },
            "firewall_block": {
                "action": "change_port",
                "retry_delay": 60,
                "alternative_method": "dns_tunnel"
            },
            "antivirus_alert": {
                "action": "pause_operations",
                "duration": 600,  # 10 minutes
                "behavior_change": "minimal"
            },
            "ids_alert": {
                "action": "reduce_frequency",
                "multiplier": 10,
                "change_pattern": True
            }
        }

        return adaptations.get(detection_event, {
            "action": "unknown",
            "message": f"No adaptation strategy for: {detection_event}"
        })


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("🕵️ Dynamic Stealth Operations Test")
    print("=" * 60)
    print()

    # Test different evasion levels
    for level in ["low", "medium", "high", "maximum"]:
        print(f"\n📋 Stealth Profile: {level.upper()}")
        stealth = DynamicStealth(evasion_level=level)

        print(f"   Process Name: {stealth.current_profile.process_name}")
        print(f"   Delay Range: {stealth.current_profile.behavior_delay_range}")
        print(f"   Jitter: {stealth.current_profile.jitter_enabled}")
        print(f"   Traffic Shaping: {stealth.current_profile.traffic_shaping}")

        # Generate timing schedule
        schedule = stealth.obfuscate_timing(5)
        print(f"   Sample Delays: {[f'{d:.2f}s' for d in schedule]}")

    # Environment detection
    print("\n\n🔍 Environment Analysis:")
    stealth = DynamicStealth(evasion_level="high")
    analysis = stealth.detect_analysis_environment()

    for indicator, detected in analysis.items():
        status = "⚠️ DETECTED" if detected else "✅ Clear"
        print(f"   {indicator}: {status}")

    # Evasion strategy
    print("\n\n🎯 Evasion Strategy:")
    strategy = stealth.get_evasion_strategy()
    for key, value in strategy.items():
        print(f"   {key}: {value}")

    # Legitimate behavior mimicry
    print("\n\n🎭 Legitimate Behavior Pattern:")
    behavior = stealth.mimic_legitimate_behavior()
    print(f"   CPU Pattern: {behavior['cpu_usage_pattern'][:5]}")
    print(f"   Memory Pattern: {behavior['memory_usage_pattern'][:5]}")
    print(f"   Network: {behavior['network_pattern']}")

    print("\n✅ Stealth operations test complete")
