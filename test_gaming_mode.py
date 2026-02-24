#!/usr/bin/env python3
"""
Gaming Mode Detection Test
Demonstrates how the protocol adapts to gaming activity
"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.safety.behavioral_constraints import BehavioralConstraints


def test_mode_detection():
    """Test mode detection system"""
    constraints = BehavioralConstraints()

    print("=" * 60)
    print("THE BENEVOLENT PROTOCOL - Gaming Mode Test")
    print("=" * 60)
    print()

    # Check platform
    if constraints.is_linux():
        print("🐧 Linux detected - Protocol will NOT infect")
        print("   (Linux users know what they're doing)")
        print()
        if constraints.should_infect():
            print("   ✅ Explicit user consent detected - proceeding")
        else:
            print("   ⛔ No explicit consent - staying dormant")
            print()
            return
    else:
        print(f"💻 Platform: {sys.platform}")
        print("   ✅ This platform can be infected")
        print()

    # Detect current mode
    current_mode = constraints.get_current_mode()
    print(f"📊 Current Mode: {current_mode.upper()}")
    print()

    # Get resource limits
    limits = constraints.get_resource_limits()

    print("⚙️  Current Resource Limits:")
    print(f"   Max CPU Usage: {limits['max_cpu_usage']}%")
    print(f"   Max Memory: {limits['max_memory_mb']}MB")
    print(f"   Max Disk I/O: {limits['max_disk_io_mbps']}Mbps")
    print(f"   Max Network: {limits['max_network_mbps']}Mbps")
    print()

    # Gaming detection
    print("🎮 Gaming Detection:")
    is_gaming = constraints.detect_gaming_mode()
    print(f"   Gaming detected: {'YES' if is_gaming else 'NO'}")

    if is_gaming:
        print("   Mode: INVISIBLE - Minimal footprint")
        print("   - Security monitoring only")
        print("   - No optimizations")
        print("   - 5% CPU max")
    else:
        print("   Mode: NORMAL - Standard operations")
        print("   - Light optimization")
        print("   - 30% CPU max")
    print()

    # Idle detection
    print("💤 Idle Detection:")
    is_idle = constraints._is_idle()
    print(f"   User idle: {'YES' if is_idle else 'NO'}")
    if is_idle:
        print("   Mode: AGGRESSIVE - Full optimization")
        print("   - Can use up to 60% CPU")
        print("   - Deep scanning enabled")
    print()

    # Battery check
    print("🔋 Battery Status:")
    battery_saver = constraints._is_battery_saver()
    if battery_saver:
        print("   ⚠️  Low battery - Entering STEALTH mode")
        print("   - Minimal operations")
        print("   - 10% CPU max")
    else:
        print("   ✅ Power OK - Normal operations")
    print()

    # Test action assessment
    print("🔍 Action Assessment Tests:")
    print()

    test_actions = [
        ("optimize_memory", {}),
        ("optimize_cpu", {}),
        ("scan_for_malware", {}),
        ("propagate_to_network", {}),
        ("delete_user_files", {}),  # Should be forbidden
    ]

    for action, context in test_actions:
        risk = constraints.check_action(action, context)

        # Skip forbidden actions in gaming mode
        if current_mode == "gaming" and action not in ["scan_for_malware"]:
            print(f"   ⏸️  {action}: DEFERRED (gaming mode)")
            continue

        if risk.name == "FORBIDDEN":
            print(f"   ❌ {action}: FORBIDDEN")
        elif risk.name in ["CRITICAL", "HIGH"]:
            print(f"   ⚠️  {action}: {risk.name}")
        else:
            print(f"   ✅ {action}: {risk.name}")

    print()
    print("=" * 60)
    print("Mode Detection Test Complete")
    print("=" * 60)


def simulate_gaming_scenario():
    """Simulate mode transitions during gaming"""
    constraints = BehavioralConstraints()

    print("\n" + "=" * 60)
    print("🎮 SIMULATING GAMING SCENARIO")
    print("=" * 60)
    print()

    scenarios = [
        ("User starts game", "gaming"),
        ("User exits game", "normal"),
        ("User leaves computer (10 min)", "idle"),
        ("User returns", "normal"),
        ("Low battery detected", "stealth"),
    ]

    for description, expected_mode in scenarios:
        print(f"📍 {description}")
        print(f"   Expected: {expected_mode.upper()}")

        # Get current limits
        limits = constraints.get_resource_limits()
        print(f"   CPU Limit: {limits['max_cpu_usage']}%")
        print(f"   Memory Limit: {limits['max_memory_mb']}MB")
        print()

        time.sleep(1)  # Simulate time passing

    print("=" * 60)


if __name__ == "__main__":
    print()
    test_mode_detection()

    # Uncomment to simulate gaming scenario
    # simulate_gaming_scenario()
