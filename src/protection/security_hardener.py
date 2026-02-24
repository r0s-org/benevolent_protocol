"""
Security Hardener Module
Applies security patches and hardens system configuration
"""

import subprocess
import os
import re
import platform
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from .vulnerability_scanner import Vulnerability, VulnerabilitySeverity


@dataclass
class HardeningResult:
    """Result of a hardening action"""
    vulnerability_id: str
    action: str
    success: bool
    message: str
    requires_restart: bool
    rollback_command: Optional[str]


class SecurityHardener:
    """
    Applies security patches and hardens system configuration.
    All changes are logged and reversible where possible.
    """

    def __init__(self):
        self.platform = platform.system().lower()
        self.applied_hardening: List[HardeningResult] = []
        self.backup_dir = "/tmp/benevolent_protocol_backups"

    def harden_system(self, vulnerabilities: List[Vulnerability]) -> List[HardeningResult]:
        """
        Apply security hardening for detected vulnerabilities.
        Returns list of results.
        """
        results = []

        for vuln in vulnerabilities:
            if not vuln.is_patchable:
                continue

            result = self._apply_hardening(vuln)
            if result:
                results.append(result)
                self.applied_hardening.append(result)

        return results

    def _apply_hardening(self, vuln: Vulnerability) -> Optional[HardeningResult]:
        """Apply hardening for a specific vulnerability"""

        # Route to appropriate hardening method
        if vuln.id.startswith("LINUX"):
            return self._harden_linux(vuln)
        elif vuln.id.startswith("WIN"):
            return self._harden_windows(vuln)
        elif vuln.id.startswith("NET"):
            return self._harden_network(vuln)

        return None

    def _harden_linux(self, vuln: Vulnerability) -> Optional[HardeningResult]:
        """Apply Linux-specific hardening"""

        # SSH hardening
        if vuln.id == "LINUX-002":  # SSH Root Login
            return self._disable_ssh_root_login()

        elif vuln.id == "LINUX-003":  # SSH Password Auth
            return self._disable_ssh_password_auth()

        elif vuln.id == "LINUX-004":  # SSH Empty Passwords
            return self._disable_ssh_empty_passwords()

        elif vuln.id == "LINUX-005":  # Firewall inactive
            return self._enable_firewall_linux()

        elif vuln.id == "LINUX-006":  # UFW disabled
            return self._enable_ufw()

        elif vuln.id.startswith("LINUX-007"):  # World-writable files
            return self._fix_world_writable(vuln)

        elif vuln.id == "LINUX-009":  # Weak password policy
            return self._strengthen_password_policy()

        elif vuln.id == "LINUX-010":  # Auto updates
            return self._enable_auto_updates()

        return None

    def _harden_windows(self, vuln: Vulnerability) -> Optional[HardeningResult]:
        """Apply Windows-specific hardening"""

        if vuln.id == "WIN-001":  # Defender disabled
            return self._enable_defender()

        elif vuln.id == "WIN-002":  # Updates pending
            return self._install_windows_updates()

        elif vuln.id == "WIN-003":  # Firewall disabled
            return self._enable_firewall_windows()

        elif vuln.id == "WIN-004":  # UAC disabled
            return self._enable_uac()

        elif vuln.id.startswith("WIN-006"):  # Insecure services
            return self._disable_windows_service(vuln)

        return None

    def _harden_network(self, vuln: Vulnerability) -> Optional[HardeningResult]:
        """Apply network hardening"""
        # Network hardening usually requires manual review
        return HardeningResult(
            vulnerability_id=vuln.id,
            action="network_hardening",
            success=False,
            message=f"Network hardening requires manual review: {vuln.name}",
            requires_restart=False,
            rollback_command=None
        )

    # Linux Hardening Methods

    def _disable_ssh_root_login(self) -> HardeningResult:
        """Disable SSH root login"""
        config_file = "/etc/ssh/sshd_config"

        try:
            # Backup original
            self._backup_file(config_file)

            # Read config
            with open(config_file, 'r') as f:
                config = f.read()

            # Replace PermitRootLogin
            new_config = re.sub(
                r'^PermitRootLogin\s+\w+',
                'PermitRootLogin no',
                config,
                flags=re.MULTILINE
            )

            # If not found, add it
            if 'PermitRootLogin' not in config:
                new_config = config + '\nPermitRootLogin no\n'

            # Write new config
            with open(config_file, 'w') as f:
                f.write(new_config)

            return HardeningResult(
                vulnerability_id="LINUX-002",
                action="disable_ssh_root_login",
                success=True,
                message="Disabled SSH root login",
                requires_restart=True,
                rollback_command=f"cp {self.backup_dir}/sshd_config.bak {config_file}"
            )

        except Exception as e:
            return HardeningResult(
                vulnerability_id="LINUX-002",
                action="disable_ssh_root_login",
                success=False,
                message=f"Failed to disable SSH root login: {e}",
                requires_restart=False,
                rollback_command=None
            )

    def _disable_ssh_password_auth(self) -> HardeningResult:
        """Disable SSH password authentication"""
        config_file = "/etc/ssh/sshd_config"

        try:
            self._backup_file(config_file)

            with open(config_file, 'r') as f:
                config = f.read()

            new_config = re.sub(
                r'^PasswordAuthentication\s+\w+',
                'PasswordAuthentication no',
                config,
                flags=re.MULTILINE
            )

            if 'PasswordAuthentication' not in config:
                new_config = config + '\nPasswordAuthentication no\n'

            with open(config_file, 'w') as f:
                f.write(new_config)

            return HardeningResult(
                vulnerability_id="LINUX-003",
                action="disable_ssh_password_auth",
                success=True,
                message="Disabled SSH password authentication (ensure SSH keys are configured)",
                requires_restart=True,
                rollback_command=f"cp {self.backup_dir}/sshd_config.bak {config_file}"
            )

        except Exception as e:
            return HardeningResult(
                vulnerability_id="LINUX-003",
                action="disable_ssh_password_auth",
                success=False,
                message=f"Failed: {e}",
                requires_restart=False,
                rollback_command=None
            )

    def _disable_ssh_empty_passwords(self) -> HardeningResult:
        """Disable SSH empty passwords"""
        config_file = "/etc/ssh/sshd_config"

        try:
            self._backup_file(config_file)

            with open(config_file, 'r') as f:
                config = f.read()

            new_config = re.sub(
                r'^PermitEmptyPasswords\s+\w+',
                'PermitEmptyPasswords no',
                config,
                flags=re.MULTILINE
            )

            if 'PermitEmptyPasswords' not in config:
                new_config = config + '\nPermitEmptyPasswords no\n'

            with open(config_file, 'w') as f:
                f.write(new_config)

            return HardeningResult(
                vulnerability_id="LINUX-004",
                action="disable_ssh_empty_passwords",
                success=True,
                message="Disabled SSH empty passwords",
                requires_restart=True,
                rollback_command=f"cp {self.backup_dir}/sshd_config.bak {config_file}"
            )

        except Exception as e:
            return HardeningResult(
                vulnerability_id="LINUX-004",
                action="disable_ssh_empty_passwords",
                success=False,
                message=f"Failed: {e}",
                requires_restart=False,
                rollback_command=None
            )

    def _enable_firewall_linux(self) -> HardeningResult:
        """Enable Linux firewall"""
        try:
            # Try UFW first
            result = subprocess.run(
                ['ufw', 'enable'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return HardeningResult(
                    vulnerability_id="LINUX-005",
                    action="enable_firewall",
                    success=True,
                    message="Enabled UFW firewall",
                    requires_restart=False,
                    rollback_command="ufw disable"
                )

        except Exception as e:
            return HardeningResult(
                vulnerability_id="LINUX-005",
                action="enable_firewall",
                success=False,
                message=f"Failed to enable firewall: {e}",
                requires_restart=False,
                rollback_command=None
            )

        return HardeningResult(
            vulnerability_id="LINUX-005",
            action="enable_firewall",
            success=False,
            message="Failed to enable firewall",
            requires_restart=False,
            rollback_command=None
        )

    def _enable_ufw(self) -> HardeningResult:
        """Enable UFW firewall"""
        return self._enable_firewall_linux()  # Same action

    def _fix_world_writable(self, vuln: Vulnerability) -> HardeningResult:
        """Fix world-writable files"""
        directory = vuln.affected_component

        try:
            # Find and fix world-writable files
            result = subprocess.run(
                ['find', directory, '-perm', '-002', '-type', 'f'],
                capture_output=True,
                text=True,
                timeout=30
            )

            files = result.stdout.strip().split('\n')
            fixed_count = 0

            for file in files:
                if file:
                    # Remove world-writable permission
                    os.chmod(file, 0o755)
                    fixed_count += 1

            return HardeningResult(
                vulnerability_id=vuln.id,
                action="fix_world_writable",
                success=True,
                message=f"Fixed {fixed_count} world-writable files in {directory}",
                requires_restart=False,
                rollback_command=None  # Manual review recommended
            )

        except Exception as e:
            return HardeningResult(
                vulnerability_id=vuln.id,
                action="fix_world_writable",
                success=False,
                message=f"Failed: {e}",
                requires_restart=False,
                rollback_command=None
            )

    def _strengthen_password_policy(self) -> HardeningResult:
        """Strengthen password policy"""
        config_file = "/etc/login.defs"

        try:
            self._backup_file(config_file)

            with open(config_file, 'r') as f:
                config = f.read()

            # Set minimum password length to 8
            new_config = re.sub(
                r'^PASS_MIN_LEN\s+\d+',
                'PASS_MIN_LEN 8',
                config,
                flags=re.MULTILINE
            )

            if 'PASS_MIN_LEN' not in config:
                new_config = config + '\nPASS_MIN_LEN 8\n'

            with open(config_file, 'w') as f:
                f.write(new_config)

            return HardeningResult(
                vulnerability_id="LINUX-009",
                action="strengthen_password_policy",
                success=True,
                message="Set minimum password length to 8",
                requires_restart=False,
                rollback_command=f"cp {self.backup_dir}/login.defs.bak {config_file}"
            )

        except Exception as e:
            return HardeningResult(
                vulnerability_id="LINUX-009",
                action="strengthen_password_policy",
                success=False,
                message=f"Failed: {e}",
                requires_restart=False,
                rollback_command=None
            )

    def _enable_auto_updates(self) -> HardeningResult:
        """Enable automatic security updates"""
        try:
            # Install unattended-upgrades
            subprocess.run(
                ['apt-get', 'install', '-y', 'unattended-upgrades'],
                check=True,
                capture_output=True,
                timeout=120
            )

            # Enable auto-upgrades
            subprocess.run(
                ['dpkg-reconfigure', '-f', 'noninteractive', 'unattended-upgrades'],
                check=True,
                capture_output=True,
                timeout=30
            )

            return HardeningResult(
                vulnerability_id="LINUX-010",
                action="enable_auto_updates",
                success=True,
                message="Enabled automatic security updates",
                requires_restart=False,
                rollback_command="apt-get remove unattended-upgrades"
            )

        except Exception as e:
            return HardeningResult(
                vulnerability_id="LINUX-010",
                action="enable_auto_updates",
                success=False,
                message=f"Failed: {e}",
                requires_restart=False,
                rollback_command=None
            )

    # Windows Hardening Methods

    def _enable_defender(self) -> HardeningResult:
        """Enable Windows Defender"""
        try:
            result = subprocess.run(
                ['powershell', '-Command', 'Set-MpPreference -DisableRealtimeMonitoring $false'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return HardeningResult(
                    vulnerability_id="WIN-001",
                    action="enable_defender",
                    success=True,
                    message="Enabled Windows Defender real-time protection",
                    requires_restart=False,
                    rollback_command="Set-MpPreference -DisableRealtimeMonitoring $true"
                )

        except Exception as e:
            return HardeningResult(
                vulnerability_id="WIN-001",
                action="enable_defender",
                success=False,
                message=f"Failed: {e}",
                requires_restart=False,
                rollback_command=None
            )

        return HardeningResult(
            vulnerability_id="WIN-001",
            action="enable_defender",
            success=False,
            message="Failed to enable Windows Defender",
            requires_restart=False,
            rollback_command=None
        )

    def _install_windows_updates(self) -> HardeningResult:
        """Install Windows updates"""
        try:
            # This is a simplified version - real implementation would be more robust
            result = subprocess.run(
                ['powershell', '-Command', 'Install-Module PSWindowsUpdate -Force; Import-Module PSWindowsUpdate; Get-WindowsUpdate -Install -AcceptAll'],
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes
            )

            if result.returncode == 0:
                return HardeningResult(
                    vulnerability_id="WIN-002",
                    action="install_updates",
                    success=True,
                    message="Windows updates installed",
                    requires_restart=True,
                    rollback_command=None
                )

        except Exception as e:
            return HardeningResult(
                vulnerability_id="WIN-002",
                action="install_updates",
                success=False,
                message=f"Failed: {e}",
                requires_restart=False,
                rollback_command=None
            )

        return HardeningResult(
            vulnerability_id="WIN-002",
            action="install_updates",
            success=False,
            message="Failed to install Windows updates",
            requires_restart=True,
            rollback_command=None
        )

    def _enable_firewall_windows(self) -> HardeningResult:
        """Enable Windows Firewall"""
        try:
            result = subprocess.run(
                ['netsh', 'advfirewall', 'set', 'allprofiles', 'state', 'on'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return HardeningResult(
                    vulnerability_id="WIN-003",
                    action="enable_firewall",
                    success=True,
                    message="Enabled Windows Firewall for all profiles",
                    requires_restart=False,
                    rollback_command="netsh advfirewall set allprofiles state off"
                )

        except Exception as e:
            return HardeningResult(
                vulnerability_id="WIN-003",
                action="enable_firewall",
                success=False,
                message=f"Failed: {e}",
                requires_restart=False,
                rollback_command=None
            )

        return HardeningResult(
            vulnerability_id="WIN-003",
            action="enable_firewall",
            success=False,
            message="Failed to enable Windows Firewall",
            requires_restart=False,
            rollback_command=None
        )

    def _enable_uac(self) -> HardeningResult:
        """Enable User Account Control"""
        try:
            result = subprocess.run(
                ['powershell', '-Command', 'Set-ItemProperty -Path HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System -Name EnableLUA -Value 1'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return HardeningResult(
                    vulnerability_id="WIN-004",
                    action="enable_uac",
                    success=True,
                    message="Enabled User Account Control",
                    requires_restart=True,
                    rollback_command="Set-ItemProperty -Path HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System -Name EnableLUA -Value 0"
                )

        except Exception as e:
            return HardeningResult(
                vulnerability_id="WIN-004",
                action="enable_uac",
                success=False,
                message=f"Failed: {e}",
                requires_restart=False,
                rollback_command=None
            )

        return HardeningResult(
            vulnerability_id="WIN-004",
            action="enable_uac",
            success=False,
            message="Failed to enable UAC",
            requires_restart=True,
            rollback_command=None
        )

    def _disable_windows_service(self, vuln: Vulnerability) -> HardeningResult:
        """Disable insecure Windows service"""
        service_name = vuln.affected_component

        try:
            result = subprocess.run(
                ['sc', 'config', service_name, 'start=', 'disabled'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                # Also stop the service
                subprocess.run(['sc', 'stop', service_name], capture_output=True, timeout=10)

                return HardeningResult(
                    vulnerability_id=vuln.id,
                    action="disable_service",
                    success=True,
                    message=f"Disabled {service_name} service",
                    requires_restart=False,
                    rollback_command=f"sc config {service_name} start= auto"
                )

        except Exception as e:
            return HardeningResult(
                vulnerability_id=vuln.id,
                action="disable_service",
                success=False,
                message=f"Failed: {e}",
                requires_restart=False,
                rollback_command=None
            )

        return HardeningResult(
            vulnerability_id=vuln.id,
            action="disable_service",
            success=False,
            message=f"Failed to disable {service_name}",
            requires_restart=False,
            rollback_command=None
        )

    # Utility Methods

    def _backup_file(self, filepath: str) -> None:
        """Create backup of file before modification"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

        if os.path.exists(filepath):
            backup_name = os.path.basename(filepath) + '.bak'
            backup_path = os.path.join(self.backup_dir, backup_name)

            # Don't overwrite existing backup
            if not os.path.exists(backup_path):
                subprocess.run(['cp', filepath, backup_path], check=True)

    def rollback_hardening(self, result: HardeningResult) -> bool:
        """Rollback a hardening action"""
        if not result.rollback_command:
            return False

        try:
            subprocess.run(
                result.rollback_command,
                shell=True,
                check=True,
                timeout=30
            )

            self.applied_hardening.remove(result)
            return True

        except:
            return False

    def get_hardening_report(self) -> Dict:
        """Generate hardening report"""
        successful = [r for r in self.applied_hardening if r.success]
        failed = [r for r in self.applied_hardening if not r.success]

        return {
            "total_applied": len(self.applied_hardening),
            "successful": len(successful),
            "failed": len(failed),
            "requires_restart": any(r.requires_restart for r in successful),
            "applied_actions": [
                {
                    "vulnerability": r.vulnerability_id,
                    "action": r.action,
                    "success": r.success,
                    "message": r.message,
                    "requires_restart": r.requires_restart
                }
                for r in self.applied_hardening
            ]
        }


# Example usage
if __name__ == "__main__":
    from vulnerability_scanner import SecurityScanner

    print("=" * 60)
    print("🔒 Security Hardener - Benevolent Protocol")
    print("=" * 60)
    print()

    # Scan first
    scanner = SecurityScanner()
    vulnerabilities = scanner.scan_system()

    print(f"Found {len(vulnerabilities)} vulnerabilities\n")

    # Harden
    hardener = SecurityHardener()
    results = hardener.harden_system(vulnerabilities)

    print(f"Applied {len(results)} hardening actions:\n")

    for result in results:
        status = "✅" if result.success else "❌"
        print(f"{status} {result.action}")
        print(f"   {result.message}")
        if result.requires_restart:
            print(f"   ⚠️  Requires restart")
        print()

    print("\n✅ Security hardening complete")
