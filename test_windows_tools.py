#!/usr/bin/env python3
"""
Windows Optimization Demo
Tests and demonstrates Windows-specific optimizations
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.optimization.windows_bloatware import WindowsBloatwareRemover
from src.optimization.windows_optimizer import WindowsSystemOptimizer


def test_bloatware_scanner():
    """Test Windows bloatware scanner"""
    print("=" * 60)
    print("🪟 Windows Bloatware Scanner Test")
    print("=" * 60)
    print()

    # Check if running on Windows
    if sys.platform != "win32":
        print("⚠️  This test requires Windows")
        print("   Showing mock results instead...")
        print()

        # Mock demonstration
        print("📋 Sample Bloatware Database:")
        remover = WindowsBloatwareRemover()
        for item in remover.bloatware_database[:5]:  # Show first 5
            print(f"   • {item.name}")
            print(f"     Safe to remove: {item.safe_to_remove}")
            print(f"     Category: {item.category}")
            print()

        print("✅ Database loaded successfully")
        print("   Run on Windows to scan actual installed apps")
        return

    # Actual Windows scan
    remover = WindowsBloatwareRemover()

    print("🔍 Scanning for installed bloatware...")
    installed = remover.scan_installed_bloatware()

    print(f"\n📊 Results: {len(installed)} bloatware apps found\n")

    # Categorize
    safe = [item for item in installed if item.safe_to_remove]
    caution = [item for item in installed if not item.safe_to_remove]

    if safe:
        print(f"✅ Safe to Remove ({len(safe)}):")
        for item in safe:
            print(f"   • {item.name}")
        print()

    if caution:
        print(f"⚠️  Review Before Removing ({len(caution)}):")
        for item in caution:
            print(f"   • {item.name} - {item.description}")
        print()


def test_system_optimizer():
    """Test Windows system optimizer"""
    print("=" * 60)
    print("⚡ Windows System Optimizer Test")
    print("=" * 60)
    print()

    # Check if running on Windows
    if sys.platform != "win32":
        print("⚠️  This test requires Windows")
        print("   Showing available optimizations instead...")
        print()

        # Show available optimizations
        optimizer = WindowsSystemOptimizer()
        report = optimizer.get_optimization_report()

        print("📋 Available Optimizations by Category:\n")

        for category, opts in report["optimizations"].items():
            print(f"{category.upper()} ({len(opts)} optimizations):")
            for opt in opts[:3]:  # Show first 3 per category
                print(f"   • {opt['name']}")
                print(f"     Impact: {opt['impact']} | Restart: {opt['requires_restart']}")
            if len(opts) > 3:
                print(f"   ... and {len(opts) - 3} more")
            print()

        print("✅ Optimization database loaded successfully")
        print("   Run on Windows to apply optimizations")
        return

    # Actual Windows optimization
    optimizer = WindowsSystemOptimizer()
    report = optimizer.get_optimization_report()

    print("📊 Optimization Report:\n")

    for category, count in report["by_category"].items():
        print(f"   {category.capitalize()}: {count} optimizations")

    print(f"\n   Total: {report['total_optimizations']} available")
    print()

    # Show what would be applied
    print("🛡️  Safe Optimizations (Auto-Apply):")
    print("   - Privacy optimizations")
    print("   - Security optimizations")
    print("   - Low/Medium impact only")
    print()

    print("⚠️  Manual Review Recommended:")
    print("   - Performance optimizations")
    print("   - Service modifications")
    print("   - High impact changes")


def show_windows_features():
    """Display Windows-specific features"""
    print("=" * 60)
    print("🪟 THE BENEVOLENT PROTOCOL - Windows Features")
    print("=" * 60)
    print()

    print("📋 BLOATWARE REMOVAL:")
    print("   ✅ Candy Crush Saga")
    print("   ✅ Microsoft Solitaire Collection")
    print("   ✅ Minecraft Trial")
    print("   ✅ Skype App")
    print("   ✅ Maps, Weather, News, Sports apps")
    print("   ✅ Paint 3D, 3D Viewer")
    print("   ✅ Mixed Reality Portal")
    print("   ✅ Feedback Hub, Tips")
    print("   ⚠️  Mail, Calendar, Photos (user review)")
    print()

    print("⚡ PERFORMANCE OPTIMIZATIONS:")
    print("   ✅ Disable SysMain (Superfetch) for SSDs")
    print("   ✅ Set High Performance power plan")
    print("   ✅ Disable transparency effects")
    print("   ✅ Disable UI animations")
    print("   ✅ Disable hibernation (frees several GB)")
    print("   ✅ Reduce System Restore space")
    print("   ⚠️  Disable Windows Search indexing")
    print()

    print("🔒 PRIVACY OPTIMIZATIONS:")
    print("   ✅ Set telemetry to basic")
    print("   ✅ Disable advertising ID")
    print("   ✅ Disable app launch tracking")
    print("   ✅ Disable location tracking")
    print()

    print("🛡️  SECURITY OPTIMIZATIONS:")
    print("   ✅ Enable Windows Defender")
    print("   ✅ Enable Windows Firewall")
    print("   ✅ Disable Remote Registry")
    print()

    print("⚙️  SERVICE OPTIMIZATIONS:")
    print("   ✅ Disable Print Spooler (if no printer)")
    print("   ✅ Disable Fax Service")
    print("   ⚠️  Disable Xbox Services (if not gaming)")
    print()

    print("🎮 GAMING MODE:")
    print("   ✅ Auto-detect gaming activity")
    print("   ✅ Drop to 5% CPU during gameplay")
    print("   ✅ Security monitoring only")
    print("   ✅ No optimizations during gaming")
    print()

    print("🐧 LINUX POLICY:")
    print("   ❌ Do NOT infect Linux systems")
    print("   ❌ Respect Linux users' expertise")
    print("   ✅ Explicit opt-in only")
    print()


def main():
    """Run all Windows feature tests"""
    print()
    show_windows_features()
    print()
    test_bloatware_scanner()
    print()
    test_system_optimizer()
    print()
    print("=" * 60)
    print("✅ Windows Features Test Complete")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
