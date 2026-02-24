#!/usr/bin/env python3
"""
Security Hardening Test Suite
Tests vulnerability scanning and hardening functionality
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.protection.vulnerability_scanner import SecurityScanner, VulnerabilitySeverity
from src.protection.security_hardener import SecurityHardener


def test_vulnerability_scanner():
    """Test vulnerability scanning"""
    print("=" * 60)
    print("🔍 VULNERABILITY SCANNER TEST")
    print("=" * 60)
    print()

    scanner = SecurityScanner()

    print(f"Platform: {scanner.platform.upper()}\n")

    print("Scanning system for vulnerabilities...")
    vulnerabilities = scanner.scan_system()

    print(f"\n📊 Scan Results:")
    print(f"   Total Vulnerabilities: {len(vulnerabilities)}\n")

    if vulnerabilities:
        # Group by severity
        by_severity = {}
        for vuln in vulnerabilities:
            sev = vuln.severity.value
            if sev not in by_severity:
                by_severity[sev] = []
            by_severity[sev].append(vuln)

        # Display by severity
        for severity in ["critical", "high", "medium", "low", "info"]:
            if severity in by_severity:
                print(f"{severity.upper()} ({len(by_severity[severity])}):")
                for vuln in by_severity[severity]:
                    print(f"   • {vuln.id}: {vuln.name}")
                    print(f"     Component: {vuln.affected_component}")
                    print(f"     Fix: {vuln.remediation}")
                    print()
    else:
        print("   ✅ No vulnerabilities detected\n")

    return vulnerabilities


def test_security_hardener(vulnerabilities):
    """Test security hardening"""
    print("=" * 60)
    print("🛡️ SECURITY HARDENER TEST")
    print("=" * 60)
    print()

    if not vulnerabilities:
        print("⚠️  No vulnerabilities to harden\n")
        return

    hardener = SecurityHardener()

    print(f"Applying hardening for {len(vulnerabilities)} vulnerabilities...\n")

    results = hardener.harden_system(vulnerabilities)

    # Count results
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    print(f"📊 Hardening Results:")
    print(f"   Total Actions: {len(results)}")
    print(f"   ✅ Successful: {len(successful)}")
    print(f"   ❌ Failed: {len(failed)}\n")

    if successful:
        print("✅ Successfully Applied:")
        for result in successful:
            print(f"   • {result.action}")
            print(f"     {result.message}")
            if result.requires_restart:
                print(f"     ⚠️  Requires restart")
            print()

    if failed:
        print("❌ Failed to Apply:")
        for result in failed:
            print(f"   • {result.action}")
            print(f"     Reason: {result.message}")
            print()


def test_vulnerability_categories():
    """Display vulnerability categories"""
    print("=" * 60)
    print("📁 VULNERABILITY CATEGORIES")
    print("=" * 60)
    print()

    categories = {
        "access_control": {
            "description": "Authentication and authorization issues",
            "examples": ["Weak passwords", "SSH misconfigurations", "UAC disabled"]
        },
        "network_security": {
            "description": "Network-level vulnerabilities",
            "examples": ["Firewall disabled", "Open risky ports", "Insecure protocols"]
        },
        "patch_management": {
            "description": "Outdated software and missing updates",
            "examples": ["Pending updates", "Outdated packages", "Missing security patches"]
        },
        "antimalware": {
            "description": "Antivirus and antimalware issues",
            "examples": ["Defender disabled", "No real-time protection", "Outdated definitions"]
        },
        "file_permissions": {
            "description": "Incorrect file and directory permissions",
            "examples": ["World-writable files", "SUID binaries", "Insecure home directories"]
        },
        "services": {
            "description": "Insecure or unnecessary services",
            "examples": ["Telnet enabled", "Insecure services running", "Unnecessary daemons"]
        },
        "software": {
            "description": "Insecure or vulnerable software",
            "examples": ["Flash Player", "Outdated Java", "Legacy software"]
        },
        "privilege_escalation": {
            "description": "Potential privilege escalation vectors",
            "examples": ["SUID binaries", "Sudo misconfigurations", "Kernel vulnerabilities"]
        }
    }

    for category, info in categories.items():
        print(f"📁 {category.upper()}")
        print(f"   {info['description']}")
        print(f"   Examples:")
        for example in info['examples']:
            print(f"     • {example}")
        print()


def test_linux_hardening_actions():
    """Display Linux hardening actions"""
    print("=" * 60)
    print("🐧 LINUX HARDENING ACTIONS")
    print("=" * 60)
    print()

    actions = [
        {
            "id": "LINUX-001",
            "name": "Update Security Packages",
            "action": "sudo apt update && sudo apt upgrade",
            "reversible": False,
            "impact": "Installs security patches"
        },
        {
            "id": "LINUX-002",
            "name": "Disable SSH Root Login",
            "action": "PermitRootLogin no in /etc/ssh/sshd_config",
            "reversible": True,
            "impact": "Prevents direct root login"
        },
        {
            "id": "LINUX-003",
            "name": "Disable SSH Password Auth",
            "action": "PasswordAuthentication no in /etc/ssh/sshd_config",
            "reversible": True,
            "impact": "Requires SSH keys for authentication"
        },
        {
            "id": "LINUX-005",
            "name": "Enable UFW Firewall",
            "action": "sudo ufw enable",
            "reversible": True,
            "impact": "Blocks unauthorized network access"
        },
        {
            "id": "LINUX-007",
            "name": "Fix World-Writable Files",
            "action": "chmod o-w <files>",
            "reversible": False,
            "impact": "Prevents unauthorized modifications"
        },
        {
            "id": "LINUX-009",
            "name": "Strengthen Password Policy",
            "action": "PASS_MIN_LEN 8 in /etc/login.defs",
            "reversible": True,
            "impact": "Requires stronger passwords"
        },
        {
            "id": "LINUX-010",
            "name": "Enable Auto Updates",
            "action": "Install unattended-upgrades",
            "reversible": True,
            "impact": "Automatic security updates"
        }
    ]

    for action in actions:
        print(f"🔧 {action['id']}: {action['name']}")
        print(f"   Action: {action['action']}")
        print(f"   Reversible: {'✅' if action['reversible'] else '❌'}")
        print(f"   Impact: {action['impact']}")
        print()


def test_windows_hardening_actions():
    """Display Windows hardening actions"""
    print("=" * 60)
    print("🪟 WINDOWS HARDENING ACTIONS")
    print("=" * 60)
    print()

    actions = [
        {
            "id": "WIN-001",
            "name": "Enable Windows Defender",
            "action": "Set-MpPreference -DisableRealtimeMonitoring $false",
            "reversible": True,
            "impact": "Real-time malware protection"
        },
        {
            "id": "WIN-002",
            "name": "Install Windows Updates",
            "action": "Install-Module PSWindowsUpdate; Get-WindowsUpdate -Install",
            "reversible": False,
            "impact": "Installs security patches"
        },
        {
            "id": "WIN-003",
            "name": "Enable Windows Firewall",
            "action": "netsh advfirewall set allprofiles state on",
            "reversible": True,
            "impact": "Network-level protection"
        },
        {
            "id": "WIN-004",
            "name": "Enable User Account Control",
            "action": "Set EnableLUA = 1 in registry",
            "reversible": True,
            "impact": "Prevents unauthorized privilege escalation"
        },
        {
            "id": "WIN-006",
            "name": "Disable Insecure Services",
            "action": "sc config <service> start= disabled",
            "reversible": True,
            "impact": "Reduces attack surface"
        }
    ]

    for action in actions:
        print(f"🔧 {action['id']}: {action['name']}")
        print(f"   Action: {action['action']}")
        print(f"   Reversible: {'✅' if action['reversible'] else '❌'}")
        print(f"   Impact: {action['impact']}")
        print()


def test_security_levels():
    """Display security hardening levels"""
    print("=" * 60)
    print("📊 SECURITY HARDENING LEVELS")
    print("=" * 60)
    print()

    levels = {
        "BASIC": {
            "description": "Essential security measures",
            "actions": [
                "Enable firewall",
                "Enable antivirus/antimalware",
                "Install security updates"
            ],
            "risk": "Low - Essential protections"
        },
        "STANDARD": {
            "description": "Recommended for most systems",
            "actions": [
                "All BASIC measures",
                "Disable insecure protocols",
                "Strengthen authentication",
                "Fix file permissions"
            ],
            "risk": "Medium - May affect some functionality"
        },
        "HIGH": {
            "description": "Enhanced security for sensitive systems",
            "actions": [
                "All STANDARD measures",
                "Disable unnecessary services",
                "Implement strict policies",
                "Advanced hardening"
            ],
            "risk": "High - May break compatibility"
        },
        "MAXIMUM": {
            "description": "Maximum security hardening",
            "actions": [
                "All HIGH measures",
                "Disable all non-essential features",
                "Implement strictest policies",
                "Comprehensive lockdown"
            ],
            "risk": "Very High - Significant functionality impact"
        }
    }

    for level, info in levels.items():
        print(f"🔒 {level}")
        print(f"   {info['description']}")
        print(f"   Actions:")
        for action in info['actions']:
            print(f"     • {action}")
        print(f"   Risk: {info['risk']}")
        print()


def test_safety_features():
    """Display security hardening safety features"""
    print("=" * 60)
    print("🛡️ SECURITY HARDENING SAFETY FEATURES")
    print("=" * 60)
    print()

    print("✅ REVERSIBILITY:")
    print("   • All reversible changes have rollback commands")
    print("   • Configuration files backed up before modification")
    print("   • Changes can be undone individually")
    print()

    print("📦 BACKUPS:")
    print("   • Original files saved to /tmp/benevolent_protocol_backups/")
    print("   • Backups never overwritten")
    print("   • Easy restoration if needed")
    print()

    print("⚠️ RISK ASSESSMENT:")
    print("   • Each action evaluated for impact")
    print("   • Critical changes require explicit consent")
    print("   • High-risk actions documented")
    print()

    print("🔍 VALIDATION:")
    print("   • Changes tested before full application")
    print("   • Error handling for failed actions")
    print("   • Detailed logging of all operations")
    print()

    print("🚨 EMERGENCY RECOVERY:")
    print("   • Factory reset restores system state")
    print("   • Backup files preserved")
    print("   • Manual rollback commands documented")
    print()


def main():
    """Run all security tests"""
    print()
    print("=" * 60)
    print("🔒 SECURITY HARDENING TEST SUITE")
    print("=" * 60)
    print()

    # Display categories
    test_vulnerability_categories()
    print()

    # Display hardening actions
    test_linux_hardening_actions()
    print()

    test_windows_hardening_actions()
    print()

    # Display security levels
    test_security_levels()
    print()

    # Display safety features
    test_safety_features()
    print()

    # Run actual scan
    print("=" * 60)
    print("🔍 ACTUAL SYSTEM SCAN")
    print("=" * 60)
    print()

    vulnerabilities = test_vulnerability_scanner()

    # Test hardening
    print()
    print("=" * 60)
    print("🛡️ ACTUAL HARDENING TEST")
    print("=" * 60)
    print()

    test_security_hardener(vulnerabilities)

    print()
    print("=" * 60)
    print("✅ SECURITY TEST SUITE COMPLETE")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
