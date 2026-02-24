"""
Windows System Optimizer
Windows-specific performance and privacy optimizations
"""

import subprocess
import os
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class WindowsOptimization:
    """Represents a Windows optimization action"""
    name: str
    description: str
    category: str  # "performance", "privacy", "security", "services"
    impact: str  # "low", "medium", "high"
    reversible: bool
    command: str
    rollback_command: str
    requires_restart: bool


class WindowsSystemOptimizer:
    """
    Windows-specific system optimizations.
    Focuses on performance, privacy, and security improvements.
    """

    def __init__(self):
        self.optimizations = self._load_optimizations()
        self.applied_optimizations = []

    def _load_optimizations(self) -> List[WindowsOptimization]:
        """Database of Windows optimizations"""
        return [
            # Performance Optimizations
            WindowsOptimization(
                name="Disable SysMain (Superfetch)",
                description="Disable Superfetch service (improves SSD performance)",
                category="performance",
                impact="medium",
                reversible=True,
                command="sc config SysMain start= disabled",
                rollback_command="sc config SysMain start= auto",
                requires_restart=True
            ),
            WindowsOptimization(
                name="Disable Windows Search Indexing",
                description="Reduce disk I/O from search indexing",
                category="performance",
                impact="low",
                reversible=True,
                command="sc config WSearch start= disabled",
                rollback_command="sc config WSearch start= auto",
                requires_restart=False
            ),
            WindowsOptimization(
                name="Set High Performance Power Plan",
                description="Maximize CPU performance",
                category="performance",
                impact="high",
                reversible=True,
                command="powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",
                rollback_command="powercfg /setactive 381b4222-f694-41f0-9685-ff5bb260df2e",  # Balanced
                requires_restart=False
            ),
            WindowsOptimization(
                name="Disable Transparency Effects",
                description="Reduce GPU usage from transparency",
                category="performance",
                impact="low",
                reversible=True,
                command='reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize" /v EnableTransparency /t REG_DWORD /d 0 /f',
                rollback_command='reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize" /v EnableTransparency /t REG_DWORD /d 1 /f',
                requires_restart=False
            ),
            WindowsOptimization(
                name="Disable Animations",
                description="Speed up UI responsiveness",
                category="performance",
                impact="low",
                reversible=True,
                command='reg add "HKCU\\Control Panel\\Desktop\\WindowMetrics" /v MinAnimate /t REG_SZ /d 0 /f',
                rollback_command='reg add "HKCU\\Control Panel\\Desktop\\WindowMetrics" /v MinAnimate /t REG_SZ /d 1 /f',
                requires_restart=False
            ),

            # Privacy Optimizations
            WindowsOptimization(
                name="Disable Telemetry (Basic)",
                description="Set telemetry to basic level",
                category="privacy",
                impact="medium",
                reversible=True,
                command='reg add "HKLM\\Software\\Policies\\Microsoft\\Windows\\DataCollection" /v AllowTelemetry /t REG_DWORD /d 0 /f',
                rollback_command='reg add "HKLM\\Software\\Policies\\Microsoft\\Windows\\DataCollection" /v AllowTelemetry /t REG_DWORD /d 1 /f',
                requires_restart=True
            ),
            WindowsOptimization(
                name="Disable Advertising ID",
                description="Stop personalized ads",
                category="privacy",
                impact="low",
                reversible=True,
                command='reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\AdvertisingInfo" /v Enabled /t REG_DWORD /d 0 /f',
                rollback_command='reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\AdvertisingInfo" /v Enabled /t REG_DWORD /d 1 /f',
                requires_restart=False
            ),
            WindowsOptimization(
                name="Disable App Launch Tracking",
                description="Stop tracking app usage",
                category="privacy",
                impact="low",
                reversible=True,
                command='reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v Start_TrackProgs /t REG_DWORD /d 0 /f',
                rollback_command='reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v Start_TrackProgs /t REG_DWORD /d 1 /f',
                requires_restart=False
            ),
            WindowsOptimization(
                name="Disable Location Tracking",
                description="Disable location services",
                category="privacy",
                impact="medium",
                reversible=True,
                command='reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\DeviceAccess\\Global\\{BFA794E4-F964-4FDB-90F6-51056BFE4B44}" /v Value /t REG_SZ /d Deny /f',
                rollback_command='reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\DeviceAccess\\Global\\{BFA794E4-F964-4FDB-90F6-51056BFE4B44}" /v Value /t REG_SZ /d Allow /f',
                requires_restart=False
            ),

            # Service Optimizations
            WindowsOptimization(
                name="Disable Print Spooler (if no printer)",
                description="Stop print spooler service",
                category="services",
                impact="low",
                reversible=True,
                command="sc config Spooler start= disabled",
                rollback_command="sc config Spooler start= auto",
                requires_restart=False
            ),
            WindowsOptimization(
                name="Disable Fax Service",
                description="Stop fax service (rarely used)",
                category="services",
                impact="low",
                reversible=True,
                command="sc config Fax start= disabled",
                rollback_command="sc config Fax start= demand",
                requires_restart=False
            ),
            WindowsOptimization(
                name="Disable Xbox Services (if not gaming)",
                description="Stop Xbox-related services",
                category="services",
                impact="medium",
                reversible=True,
                command="; ".join([
                    "sc config XblAuthManager start= disabled",
                    "sc config XblGameSave start= disabled",
                    "sc config XboxNetApiSvc start= disabled"
                ]),
                rollback_command="; ".join([
                    "sc config XblAuthManager start= demand",
                    "sc config XblGameSave start= demand",
                    "sc config XboxNetApiSvc start= demand"
                ]),
                requires_restart=False
            ),

            # Security Optimizations
            WindowsOptimization(
                name="Enable Windows Defender",
                description="Ensure Windows Defender is active",
                category="security",
                impact="high",
                reversible=True,
                command='reg add "HKLM\\Software\\Policies\\Microsoft\\Windows Defender" /v DisableAntiSpyware /t REG_DWORD /d 0 /f',
                rollback_command='reg add "HKLM\\Software\\Policies\\Microsoft\\Windows Defender" /v DisableAntiSpyware /t REG_DWORD /d 1 /f',
                requires_restart=False
            ),
            WindowsOptimization(
                name="Enable Firewall",
                description="Ensure Windows Firewall is active",
                category="security",
                impact="high",
                reversible=True,
                command="netsh advfirewall set allprofiles state on",
                rollback_command="netsh advfirewall set allprofiles state off",
                requires_restart=False
            ),
            WindowsOptimization(
                name="Disable Remote Registry",
                description="Improve security by disabling remote registry access",
                category="security",
                impact="medium",
                reversible=True,
                command="sc config RemoteRegistry start= disabled",
                rollback_command="sc config RemoteRegistry start= auto",
                requires_restart=False
            ),

            # Storage Optimizations
            WindowsOptimization(
                name="Disable Hibernation (if SSD)",
                description="Free up several GB of disk space",
                category="performance",
                impact="medium",
                reversible=True,
                command="powercfg /h off",
                rollback_command="powercfg /h on",
                requires_restart=False
            ),
            WindowsOptimization(
                name="Reduce System Restore Space",
                description="Limit system restore to 2GB",
                category="performance",
                impact="low",
                reversible=True,
                command="vssadmin resize shadowstorage /for=C: /on=C: /maxsize=2GB",
                rollback_command="vssadmin resize shadowstorage /for=C: /on=C: /maxsize=5GB",
                requires_restart=False
            ),
            WindowsOptimization(
                name="Disable Prefetch (if SSD)",
                description="Reduce unnecessary disk reads on SSD",
                category="performance",
                impact="low",
                reversible=True,
                command='reg add "HKLM\\System\\CurrentControlSet\\Control\\Session Manager\\Memory Management\\PrefetchParameters" /v EnablePrefetcher /t REG_DWORD /d 0 /f',
                rollback_command='reg add "HKLM\\System\\CurrentControlSet\\Control\\Session Manager\\Memory Management\\PrefetchParameters" /v EnablePrefetcher /t REG_DWORD /d 3 /f',
                requires_restart=True
            ),
        ]

    def apply_optimization(self, opt: WindowsOptimization) -> Tuple[bool, str]:
        """
        Apply a Windows optimization.
        Returns (success, message).
        """
        try:
            result = subprocess.run(
                ["cmd", "/c", opt.command],
                capture_output=True,
                text=True,
                timeout=30,
                shell=True
            )

            if result.returncode == 0:
                self.applied_optimizations.append({
                    "optimization": opt.name,
                    "timestamp": psutil.datetime.datetime.now().isoformat(),
                    "rollback_command": opt.rollback_command
                })
                return True, f"Successfully applied {opt.name}"
            else:
                error = result.stderr.strip() if result.stderr else "Unknown error"
                return False, f"Failed to apply {opt.name}: {error}"

        except subprocess.TimeoutExpired:
            return False, f"Timeout applying {opt.name}"
        except Exception as e:
            return False, f"Error applying {opt.name}: {e}"

    def rollback_optimization(self, opt_name: str) -> Tuple[bool, str]:
        """
        Rollback a previously applied optimization.
        """
        # Find the optimization
        opt = next((o for o in self.optimizations if o.name == opt_name), None)

        if not opt:
            return False, f"Optimization {opt_name} not found"

        try:
            result = subprocess.run(
                ["cmd", "/c", opt.rollback_command],
                capture_output=True,
                text=True,
                timeout=30,
                shell=True
            )

            if result.returncode == 0:
                # Remove from applied list
                self.applied_optimizations = [
                    item for item in self.applied_optimizations
                    if item["optimization"] != opt_name
                ]
                return True, f"Successfully rolled back {opt.name}"
            else:
                error = result.stderr.strip() if result.stderr else "Unknown error"
                return False, f"Failed to rollback {opt.name}: {error}"

        except Exception as e:
            return False, f"Error rolling back {opt.name}: {e}"

    def get_optimization_report(self) -> Dict:
        """
        Generate optimization report categorized by type.
        """
        categories = {
            "performance": [],
            "privacy": [],
            "security": [],
            "services": []
        }

        for opt in self.optimizations:
            categories[opt.category].append({
                "name": opt.name,
                "description": opt.description,
                "impact": opt.impact,
                "reversible": opt.reversible,
                "requires_restart": opt.requires_restart
            })

        return {
            "total_optimizations": len(self.optimizations),
            "by_category": {
                cat: len(items) for cat, items in categories.items()
            },
            "optimizations": categories,
            "applied_count": len(self.applied_optimizations),
            "applied_list": self.applied_optimizations
        }

    def apply_safe_optimizations(self) -> Dict[str, List[str]]:
        """
        Apply all "safe" optimizations (low impact, reversible).
        """
        results = {
            "success": [],
            "failed": [],
            "skipped": []
        }

        # Define which optimizations are "safe" to auto-apply
        safe_categories = ["privacy", "security"]

        for opt in self.optimizations:
            if opt.category in safe_categories and opt.impact in ["low", "medium"]:
                success, message = self.apply_optimization(opt)

                if success:
                    results["success"].append(opt.name)
                else:
                    results["failed"].append(f"{opt.name}: {message}")
            else:
                results["skipped"].append(opt.name)

        return results


# Example usage
if __name__ == "__main__":
    import psutil

    print("=" * 60)
    print("Windows System Optimizer")
    print("=" * 60)
    print()

    optimizer = WindowsSystemOptimizer()

    # Get report
    report = optimizer.get_optimization_report()

    print("📊 Available Optimizations:")
    print()

    for category, opts in report["optimizations"].items():
        print(f"{category.upper()} ({len(opts)} items):")
        for opt in opts:
            print(f"  • {opt['name']}: {opt['description']}")
            print(f"    Impact: {opt['impact']} | Restart: {opt['requires_restart']}")
        print()

    print(f"\nTotal: {report['total_optimizations']} optimizations available")
    print(f"Safe to auto-apply: Privacy + Security optimizations")

    # Ask for confirmation
    print("\nApply safe optimizations (privacy + security)? (y/n): ", end="")
    if input().lower() == 'y':
        print("\n⚡ Applying optimizations...")
        results = optimizer.apply_safe_optimizations()

        if results["success"]:
            print(f"\n✅ Successfully applied {len(results['success'])} optimizations:")
            for opt in results["success"]:
                print(f"   - {opt}")

        if results["failed"]:
            print(f"\n❌ Failed to apply {len(results['failed'])} optimizations:")
            for opt in results["failed"]:
                print(f"   - {opt}")

        print("\n⚠️  Some optimizations may require restart to take effect.")
    else:
        print("\nCancelled. No changes made.")
