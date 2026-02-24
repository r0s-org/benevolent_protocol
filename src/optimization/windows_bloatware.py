"""
Windows Bloatware Removal Module
Safely removes unnecessary pre-installed software from Windows systems
"""

import subprocess
import psutil
from typing import List, Dict, Tuple
from dataclasses import dataclass
import re


@dataclass
class BloatwareItem:
    """Represents a bloatware application"""
    name: str
    appx_name: str  # Package name for Get-AppxPackage
    description: str
    safe_to_remove: bool  # Some "bloatware" might be useful
    category: str  # "games", "trialware", "tools", etc.
    removal_command: str


class WindowsBloatwareRemover:
    """
    Identifies and safely removes Windows bloatware.
    Uses PowerShell Get-AppxPackage for clean removal.
    """

    def __init__(self):
        self.bloatware_database = self._load_bloatware_database()
        self.removal_log = []

    def _load_bloatware_database(self) -> List[BloatwareItem]:
        """
        Database of known Windows bloatware.
        Conservative approach: only remove clearly unnecessary apps.
        """
        return [
            # Games (almost always unwanted)
            BloatwareItem(
                name="Candy Crush Saga",
                appx_name="king.com.CandyCrushSaga",
                description="Mobile game pre-installed on Windows",
                safe_to_remove=True,
                category="games",
                removal_command="Get-AppxPackage *CandyCrush* | Remove-AppxPackage"
            ),
            BloatwareItem(
                name="Candy Crush Soda Saga",
                appx_name="king.com.CandyCrushSodaSaga",
                description="Another Candy Crush variant",
                safe_to_remove=True,
                category="games",
                removal_command="Get-AppxPackage *CandyCrushSoda* | Remove-AppxPackage"
            ),
            BloatwareItem(
                name="Microsoft Solitaire Collection",
                appx_name="Microsoft.MicrosoftSolitaireCollection",
                description="Card games pre-installed",
                safe_to_remove=True,
                category="games",
                removal_command="Get-AppxPackage *Solitaire* | Remove-AppxPackage"
            ),
            BloatwareItem(
                name="Minecraft",
                appx_name="Microsoft.MinecraftUWP",
                description="Minecraft trial/launcher",
                safe_to_remove=True,
                category="games",
                removal_command="Get-AppxPackage *Minecraft* | Remove-AppxPackage"
            ),
            BloatwareItem(
                name="Royal Revolt 2",
                appx_name="flaregamesGmbH.RoyalRevolt2",
                description="Mobile game",
                safe_to_remove=True,
                category="games",
                removal_command="Get-AppxPackage *RoyalRevolt* | Remove-AppxPackage"
            ),

            # Trialware/OEM Bloatware
            BloatwareItem(
                name="Office Hub (Trial)",
                appx_name="Microsoft.MicrosoftOfficeHub",
                description="Office trial launcher",
                safe_to_remove=True,
                category="trialware",
                removal_command="Get-AppxPackage *MicrosoftOfficeHub* | Remove-AppxPackage"
            ),
            BloatwareItem(
                name="OneNote (UWP)",
                appx_name="Microsoft.Office.OneNote",
                description="UWP OneNote (keep if using OneNote)",
                safe_to_remove=False,  # User might use this
                category="trialware",
                removal_command="Get-AppxPackage *OneNote* | Remove-AppxPackage"
            ),
            BloatwareItem(
                name="Skype App",
                appx_name="Microsoft.SkypeApp",
                description="Skype UWP app (desktop version better)",
                safe_to_remove=True,
                category="trialware",
                removal_command="Get-AppxPackage *SkypeApp* | Remove-AppxPackage"
            ),
            BloatwareItem(
                name="Xbox Game Bar",
                appx_name="Microsoft.XboxGamingOverlay",
                description="Xbox overlay (useful for gamers)",
                safe_to_remove=False,  # Gamers might use this
                category="gaming_tools",
                removal_command="Get-AppxPackage *XboxGamingOverlay* | Remove-AppxPackage"
            ),

            # Microsoft Apps (User Might Want)
            BloatwareItem(
                name="Mail and Calendar",
                appx_name="microsoft.windowscommunicationsapps",
                description="Built-in mail client",
                safe_to_remove=False,  # User might use for email
                category="productivity",
                removal_command="Get-AppxPackage *windowscommunicationsapps* | Remove-AppxPackage"
            ),
            BloatwareItem(
                name="Maps",
                appx_name="Microsoft.WindowsMaps",
                description="Windows Maps app",
                safe_to_remove=True,
                category="tools",
                removal_command="Get-AppxPackage *WindowsMaps* | Remove-AppxPackage"
            ),
            BloatwareItem(
                name="Weather",
                appx_name="Microsoft.BingWeather",
                description="Weather app",
                safe_to_remove=True,
                category="tools",
                removal_command="Get-AppxPackage *BingWeather* | Remove-AppxPackage"
            ),
            BloatwareItem(
                name="News",
                appx_name="Microsoft.BingNews",
                description="Microsoft News app",
                safe_to_remove=True,
                category="tools",
                removal_command="Get-AppxPackage *BingNews* | Remove-AppxPackage"
            ),
            BloatwareItem(
                name="Sports",
                appx_name="Microsoft.BingSports",
                description="Sports news app",
                safe_to_remove=True,
                category="tools",
                removal_command="Get-AppxPackage *BingSports* | Remove-AppxPackage"
            ),
            BloatwareItem(
                name="Finance/Money",
                appx_name="Microsoft.BingFinance",
                description="Finance/stock tracking app",
                safe_to_remove=True,
                category="tools",
                removal_command="Get-AppxPackage *BingFinance* | Remove-AppxPackage"
            ),

            # Creative/Media Apps
            BloatwareItem(
                name="Paint 3D",
                appx_name="Microsoft.MSPaint",
                description="3D painting app",
                safe_to_remove=True,
                category="creative",
                removal_command="Get-AppxPackage *MSPaint* | Remove-AppxPackage"
            ),
            BloatwareItem(
                name="3D Viewer",
                appx_name="Microsoft.Microsoft3DViewer",
                description="3D model viewer",
                safe_to_remove=True,
                category="creative",
                removal_command="Get-AppxPackage *3DViewer* | Remove-AppxPackage"
            ),
            BloatwareItem(
                name="Photos",
                appx_name="Microsoft.Windows.Photos",
                description="Photo viewer (basic but useful)",
                safe_to_remove=False,  # Basic functionality
                category="media",
                removal_command="Get-AppxPackage *Photos* | Remove-AppxPackage"
            ),
            BloatwareItem(
                name="Groove Music",
                appx_name="Microsoft.ZuneMusic",
                description="Music player",
                safe_to_remove=True,
                category="media",
                removal_command="Get-AppxPackage *ZuneMusic* | Remove-AppxPackage"
            ),
            BloatwareItem(
                name="Movies & TV",
                appx_name="Microsoft.ZuneVideo",
                description="Video player",
                safe_to_remove=False,  # Basic functionality
                category="media",
                removal_command="Get-AppxPackage *ZuneVideo* | Remove-AppxPackage"
            ),
            BloatwareItem(
                name="Voice Recorder",
                appx_name="Microsoft.WindowsSoundRecorder",
                description="Audio recorder",
                safe_to_remove=True,
                category="tools",
                removal_command="Get-AppxPackage *SoundRecorder* | Remove-AppxPackage"
            ),

            # System Tools (Usually Safe)
            BloatwareItem(
                name="Alarms & Clock",
                appx_name="Microsoft.WindowsAlarms",
                description="Alarm clock app",
                safe_to_remove=True,
                category="tools",
                removal_command="Get-AppxPackage *WindowsAlarms* | Remove-AppxPackage"
            ),
            BloatwareItem(
                name="Calculator",
                appx_name="Microsoft.WindowsCalculator",
                description="Calculator (actually useful)",
                safe_to_remove=False,  # Basic functionality
                category="tools",
                removal_command="Get-AppxPackage *WindowsCalculator* | Remove-AppxPackage"
            ),
            BloatwareItem(
                name="Camera",
                appx_name="Microsoft.WindowsCamera",
                description="Camera app",
                safe_to_remove=False,  # Might need for webcam
                category="tools",
                removal_command="Get-AppxPackage *WindowsCamera* | Remove-AppxPackage"
            ),
            BloatwareItem(
                name="Feedback Hub",
                appx_name="Microsoft.WindowsFeedbackHub",
                description="Windows feedback tool",
                safe_to_remove=True,
                category="system",
                removal_command="Get-AppxPackage *WindowsFeedbackHub* | Remove-AppxPackage"
            ),
            BloatwareItem(
                name="Get Help",
                appx_name="Microsoft.GetHelp",
                description="Windows help app",
                safe_to_remove=True,
                category="system",
                removal_command="Get-AppxPackage *GetHelp* | Remove-AppxPackage"
            ),
            BloatwareItem(
                name="Get Started / Tips",
                appx_name="Microsoft.Getstarted",
                description="Windows tips app",
                safe_to_remove=True,
                category="system",
                removal_command="Get-AppxPackage *Getstarted* | Remove-AppxPackage"
            ),
            BloatwareItem(
                name="Mixed Reality Portal",
                appx_name="Microsoft.MixedReality.Portal",
                description="VR/AR portal (if no VR headset)",
                safe_to_remove=True,
                category="system",
                removal_command="Get-AppxPackage *MixedReality* | Remove-AppxPackage"
            ),
            BloatwareItem(
                name="OneDrive (UWP)",
                appx_name="Microsoft.MicrosoftSkyDrive",
                description="OneDrive app (desktop version better)",
                safe_to_remove=True,
                category="cloud",
                removal_command="Get-AppxPackage *MicrosoftSkyDrive* | Remove-AppxPackage"
            ),
            BloatwareItem(
                name="People",
                appx_name="Microsoft.People",
                description="Contacts app",
                safe_to_remove=True,
                category="productivity",
                removal_command="Get-AppxPackage *People* | Remove-AppxPackage"
            ),
            BloatwareItem(
                name="Print 3D",
                appx_name="Microsoft.Print3D",
                description="3D printing app",
                safe_to_remove=True,
                category="creative",
                removal_command="Get-AppxPackage *Print3D* | Remove-AppxPackage"
            ),
            BloatwareItem(
                name="Sticky Notes",
                appx_name="Microsoft.MicrosoftStickyNotes",
                description="Sticky notes app",
                safe_to_remove=False,  # User might use
                category="productivity",
                removal_command="Get-AppxPackage *StickyNotes* | Remove-AppxPackage"
            ),
            BloatwareItem(
                name="Wallet",
                appx_name="Microsoft.Wallet",
                description="Payment wallet app",
                safe_to_remove=True,
                category="productivity",
                removal_command="Get-AppxPackage *Wallet* | Remove-AppxPackage"
            ),
        ]

    def scan_installed_bloatware(self) -> List[BloatwareItem]:
        """
        Scan system for installed bloatware.
        Returns list of bloatware apps currently installed.
        """
        installed = []

        try:
            # Get all installed AppX packages
            result = subprocess.run(
                ["powershell", "-Command", "Get-AppxPackage | Select-Object Name"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                installed_packages = result.stdout.lower()

                # Check each bloatware item
                for item in self.bloatware_database:
                    # Check if package name appears in installed packages
                    if item.appx_name.lower() in installed_packages:
                        installed.append(item)

        except Exception as e:
            print(f"Error scanning bloatware: {e}")

        return installed

    def remove_bloatware(self, item: BloatwareItem, force: bool = False) -> Tuple[bool, str]:
        """
        Remove a specific bloatware application.
        Returns (success, message).
        """
        if not item.safe_to_remove and not force:
            return False, f"Refusing to remove {item.name} (marked as potentially useful). Use force=True to override."

        try:
            result = subprocess.run(
                ["powershell", "-Command", item.removal_command],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                self.removal_log.append({
                    "item": item.name,
                    "success": True,
                    "timestamp": psutil.datetime.datetime.now().isoformat()
                })
                return True, f"Successfully removed {item.name}"
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                return False, f"Failed to remove {item.name}: {error_msg}"

        except subprocess.TimeoutExpired:
            return False, f"Timeout while removing {item.name}"
        except Exception as e:
            return False, f"Error removing {item.name}: {e}"

    def remove_all_safe_bloatware(self) -> Dict[str, List[str]]:
        """
        Remove all bloatware marked as safe_to_remove.
        Returns dict with 'success' and 'failed' lists.
        """
        results = {
            "success": [],
            "failed": [],
            "skipped": []
        }

        installed = self.scan_installed_bloatware()

        for item in installed:
            if item.safe_to_remove:
                success, message = self.remove_bloatware(item)

                if success:
                    results["success"].append(item.name)
                else:
                    results["failed"].append(f"{item.name}: {message}")
            else:
                results["skipped"].append(item.name)

        return results

    def get_bloatware_report(self) -> Dict:
        """
        Generate comprehensive bloatware report.
        """
        installed = self.scan_installed_bloatware()

        safe_to_remove = [item for item in installed if item.safe_to_remove]
        user_might_want = [item for item in installed if not item.safe_to_remove]

        # Categorize
        categories = {}
        for item in installed:
            if item.category not in categories:
                categories[item.category] = []
            categories[item.category].append(item.name)

        return {
            "total_installed": len(installed),
            "safe_to_remove_count": len(safe_to_remove),
            "user_might_want_count": len(user_might_want),
            "safe_to_remove": [{"name": item.name, "description": item.description} for item in safe_to_remove],
            "user_might_want": [{"name": item.name, "description": item.description} for item in user_might_want],
            "categories": categories,
            "removal_log": self.removal_log
        }


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("Windows Bloatware Scanner")
    print("=" * 60)
    print()

    remover = WindowsBloatwareRemover()

    # Scan for bloatware
    print("🔍 Scanning for installed bloatware...")
    installed = remover.scan_installed_bloatware()

    print(f"\nFound {len(installed)} bloatware apps installed:\n")

    # Show safe to remove
    safe = [item for item in installed if item.safe_to_remove]
    if safe:
        print("✅ Safe to Remove:")
        for item in safe:
            print(f"   - {item.name}: {item.description}")
        print()

    # Show user might want
    might_want = [item for item in installed if not item.safe_to_remove]
    if might_want:
        print("⚠️  User Might Want (Review):")
        for item in might_want:
            print(f"   - {item.name}: {item.description}")
        print()

    # Ask for confirmation
    print(f"Ready to remove {len(safe)} safe apps? (y/n): ", end="")
    if input().lower() == 'y':
        print("\n🗑️  Removing bloatware...")
        results = remover.remove_all_safe_bloatware()

        if results["success"]:
            print(f"\n✅ Successfully removed {len(results['success'])} apps:")
            for app in results["success"]:
                print(f"   - {app}")

        if results["failed"]:
            print(f"\n❌ Failed to remove {len(results['failed'])} apps:")
            for app in results["failed"]:
                print(f"   - {app}")

        if results["skipped"]:
            print(f"\n⏭️  Skipped {len(results['skipped'])} apps (might be useful)")
    else:
        print("\nCancelled. No changes made.")
