"""
Android Device Optimizer
Safe optimization for Android devices via ADB
"""

import subprocess
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class AndroidOptimizationLevel(Enum):
    """Android optimization levels"""
    SAFE = "safe"          # Non-root, ADB only
    MODERATE = "moderate"  # Non-root, aggressive ADB
    ROOT = "root"          # Root access required


@dataclass
class AndroidDevice:
    """Represents an Android device"""
    device_id: str
    model: str
    brand: str
    android_version: str
    sdk_version: int
    is_rooted: bool
    is_accessible: bool
    optimization_level: AndroidOptimizationLevel


@dataclass
class AndroidBloatware:
    """Android bloatware definition"""
    package_name: str
    description: str
    safe_to_remove: bool
    category: str
    requires_root: bool


class AndroidOptimizer:
    """
    Optimizes Android devices via ADB.
    Supports non-root (safe) and root (full) optimization.
    """

    def __init__(self):
        self.connected_devices: List[AndroidDevice] = []
        self.bloatware_database = self._load_bloatware_database()

    def _load_bloatware_database(self) -> List[AndroidBloatware]:
        """
        Database of common Android bloatware.
        Organized by manufacturer and carrier.
        """
        return [
            # Samsung Bloatware
            AndroidBloatware(
                package_name="com.samsung.android.app.spage",
                description="Samsung Daily/Bixby Home",
                safe_to_remove=True,
                category="bixby",
                requires_root=False
            ),
            AndroidBloatware(
                package_name="com.samsung.android.bixby.wakeup",
                description="Bixby Voice Wake-up",
                safe_to_remove=True,
                category="bixby",
                requires_root=False
            ),
            AndroidBloatware(
                package_name="com.samsung.android.bixby.agent",
                description="Bixby Agent",
                safe_to_remove=True,
                category="bixby",
                requires_root=False
            ),
            AndroidBloatware(
                package_name="com.samsung.android.app.dressroom",
                description="Samsung Wallpapers",
                safe_to_remove=True,
                category="samsung_apps",
                requires_root=False
            ),
            AndroidBloatware(
                package_name="com.samsung.android.drivelink.stub",
                description="Samsung Car Mode",
                safe_to_remove=True,
                category="samsung_apps",
                requires_root=False
            ),
            AndroidBloatware(
                package_name="com.samsung.android.email.provider",
                description="Samsung Email",
                safe_to_remove=True,
                category="samsung_apps",
                requires_root=False
            ),
            AndroidBloatware(
                package_name="com.samsung.android.gearoplugin",
                description="Samsung Gear Plugin",
                safe_to_remove=True,
                category="samsung_apps",
                requires_root=False
            ),
            AndroidBloatware(
                package_name="com.samsung.android.hmt.vrsvc",
                description="Samsung VR Service",
                safe_to_remove=True,
                category="samsung_apps",
                requires_root=False
            ),
            AndroidBloatware(
                package_name="com.samsung.android.scloud",
                description="Samsung Cloud",
                safe_to_remove=True,
                category="samsung_apps",
                requires_root=False
            ),
            AndroidBloatware(
                package_name="com.samsung.android.sdk.handwriting",
                description="Samsung Handwriting",
                safe_to_remove=True,
                category="samsung_apps",
                requires_root=False
            ),

            # Google Bloatware
            AndroidBloatware(
                package_name="com.google.android.apps.docs",
                description="Google Docs",
                safe_to_remove=True,
                category="google_apps",
                requires_root=False
            ),
            AndroidBloatware(
                package_name="com.google.android.apps.sheets",
                description="Google Sheets",
                safe_to_remove=True,
                category="google_apps",
                requires_root=False
            ),
            AndroidBloatware(
                package_name="com.google.android.apps.slides",
                description="Google Slides",
                safe_to_remove=True,
                category="google_apps",
                requires_root=False
            ),
            AndroidBloatware(
                package_name="com.google.android.apps.photos",
                description="Google Photos (caution: may need)",
                safe_to_remove=False,
                category="google_apps",
                requires_root=False
            ),
            AndroidBloatware(
                package_name="com.google.android.music",
                description="Google Play Music (discontinued)",
                safe_to_remove=True,
                category="google_apps",
                requires_root=False
            ),
            AndroidBloatware(
                package_name="com.google.android.videos",
                description="Google Play Movies",
                safe_to_remove=True,
                category="google_apps",
                requires_root=False
            ),
            AndroidBloatware(
                package_name="com.google.android.apps.magazines",
                description="Google News/Magazines",
                safe_to_remove=True,
                category="google_apps",
                requires_root=False
            ),
            AndroidBloatware(
                package_name="com.google.android.apps.books",
                description="Google Play Books",
                safe_to_remove=True,
                category="google_apps",
                requires_root=False
            ),
            AndroidBloatware(
                package_name="com.google.android.talk",
                description="Google Hangouts",
                safe_to_remove=True,
                category="google_apps",
                requires_root=False
            ),
            AndroidBloatware(
                package_name="com.google.android.feedback",
                description="Google Feedback",
                safe_to_remove=True,
                category="google_apps",
                requires_root=False
            ),

            # Carrier Bloatware (Universal)
            AndroidBloatware(
                package_name="com.android.hiddenmenu",
                description="Carrier Hidden Menu",
                safe_to_remove=True,
                category="carrier",
                requires_root=False
            ),
            AndroidBloatware(
                package_name="com.qualcomm.qti.autoregistration",
                description="Qualcomm Auto Registration",
                safe_to_remove=True,
                category="carrier",
                requires_root=False
            ),
            AndroidBloatware(
                package_name="com.qualcomm.qti.performancemode",
                description="Qualcomm Performance Mode",
                safe_to_remove=True,
                category="carrier",
                requires_root=False
            ),

            # Manufacturer Bloatware (Xiaomi)
            AndroidBloatware(
                package_name="com.mi.android.globalminusscreen",
                description="Xiaomi App Vault",
                safe_to_remove=True,
                category="xiaomi",
                requires_root=False
            ),
            AndroidBloatware(
                package_name="com.xiaomi.mipicks",
                description="Xiaomi App Picker",
                safe_to_remove=True,
                category="xiaomi",
                requires_root=False
            ),
            AndroidBloatware(
                package_name="com.miui.cleanmaster",
                description="Xiaomi Cleaner",
                safe_to_remove=True,
                category="xiaomi",
                requires_root=False
            ),
            AndroidBloatware(
                package_name="com.miui.notes",
                description="Xiaomi Notes",
                safe_to_remove=True,
                category="xiaomi",
                requires_root=False
            ),
            AndroidBloatware(
                package_name="com.xiaomi.midrop",
                description="Xiaomi Mi Drop",
                safe_to_remove=True,
                category="xiaomi",
                requires_root=False
            ),

            # Manufacturer Bloatware (Huawei)
            AndroidBloatware(
                package_name="com.huawei.phoneservice",
                description="Huawei Phone Service",
                safe_to_remove=True,
                category="huawei",
                requires_root=False
            ),
            AndroidBloatware(
                package_name="com.huawei.hwvplayer",
                description="Huawei Video Player",
                safe_to_remove=True,
                category="huawei",
                requires_root=False
            ),
            AndroidBloatware(
                package_name="com.huawei.himovie",
                description="Huawei Movie Player",
                safe_to_remove=True,
                category="huawei",
                requires_root=False
            ),
            AndroidBloatware(
                package_name="com.huawei.hwid",
                description="Huawei ID (caution: may need)",
                safe_to_remove=False,
                category="huawei",
                requires_root=False
            ),

            # Manufacturer Bloatware (OnePlus)
            AndroidBloatware(
                package_name="net.oneplus.forums",
                description="OnePlus Forums",
                safe_to_remove=True,
                category="oneplus",
                requires_root=False
            ),
            AndroidBloatware(
                package_name="net.oneplus.weather",
                description="OnePlus Weather",
                safe_to_remove=True,
                category="oneplus",
                requires_root=False
            ),
            AndroidBloatware(
                package_name="net.oneplus.community",
                description="OnePlus Community",
                safe_to_remove=True,
                category="oneplus",
                requires_root=False
            ),

            # Manufacturer Bloatware (LG)
            AndroidBloatware(
                package_name="com.lge.email",
                description="LG Email",
                safe_to_remove=True,
                category="lg",
                requires_root=False
            ),
            AndroidBloatware(
                package_name="com.lge.lifetracker",
                description="LG Life Tracker",
                safe_to_remove=True,
                category="lg",
                requires_root=False
            ),
            AndroidBloatware(
                package_name="com.lge.music",
                description="LG Music",
                safe_to_remove=True,
                category="lg",
                requires_root=False
            ),

            # Facebook (Often Pre-installed)
            AndroidBloatware(
                package_name="com.facebook.katana",
                description="Facebook App",
                safe_to_remove=True,
                category="social",
                requires_root=False
            ),
            AndroidBloatware(
                package_name="com.facebook.system",
                description="Facebook System",
                safe_to_remove=True,
                category="social",
                requires_root=False
            ),
            AndroidBloatware(
                package_name="com.facebook.appmanager",
                description="Facebook App Manager",
                safe_to_remove=True,
                category="social",
                requires_root=False
            ),
            AndroidBloatware(
                package_name="com.instagram.android",
                description="Instagram",
                safe_to_remove=True,
                category="social",
                requires_root=False
            ),

            # Games (Common Pre-installed)
            AndroidBloatware(
                package_name="com.gameloft.android.ANMP.GloftA8HM",
                description="Asphalt 8 (Game)",
                safe_to_remove=True,
                category="games",
                requires_root=False
            ),
            AndroidBloatware(
                package_name="com.ea.game.pvz2_row",
                description="Plants vs Zombies 2",
                safe_to_remove=True,
                category="games",
                requires_root=False
            ),

            # Utility Apps (Often Bloatware)
            AndroidBloatware(
                package_name="com.cleanmaster.mguard",
                description="Clean Master (Adware)",
                safe_to_remove=True,
                category="utilities",
                requires_root=False
            ),
            AndroidBloatware(
                package_name="com.ifevo.screenrecorder",
                description="Screen Recorder",
                safe_to_remove=True,
                category="utilities",
                requires_root=False
            ),
        ]

    def check_adb_available(self) -> bool:
        """Check if ADB is available on the system"""
        try:
            result = subprocess.run(
                ['adb', 'version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False

    def list_connected_devices(self) -> List[str]:
        """List all connected Android devices"""
        try:
            result = subprocess.run(
                ['adb', 'devices'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                return []

            # Parse device IDs
            devices = []
            for line in result.stdout.split('\n')[1:]:  # Skip header
                if '\t' in line:
                    device_id = line.split('\t')[0]
                    devices.append(device_id)

            return devices

        except:
            return []

    def get_device_info(self, device_id: str) -> Optional[AndroidDevice]:
        """Get detailed information about an Android device"""
        try:
            # Get device properties
            model = self._get_device_property(device_id, 'ro.product.model')
            brand = self._get_device_property(device_id, 'ro.product.brand')
            android_version = self._get_device_property(device_id, 'ro.build.version.release')
            sdk_version_str = self._get_device_property(device_id, 'ro.build.version.sdk')

            # Check if rooted
            is_rooted = self._check_root_access(device_id)

            # Determine optimization level
            if is_rooted:
                optimization_level = AndroidOptimizationLevel.ROOT
            else:
                optimization_level = AndroidOptimizationLevel.SAFE

            return AndroidDevice(
                device_id=device_id,
                model=model or "Unknown",
                brand=brand or "Unknown",
                android_version=android_version or "Unknown",
                sdk_version=int(sdk_version_str) if sdk_version_str else 0,
                is_rooted=is_rooted,
                is_accessible=True,
                optimization_level=optimization_level
            )

        except Exception as e:
            return None

    def _get_device_property(self, device_id: str, prop: str) -> Optional[str]:
        """Get device property via ADB"""
        try:
            result = subprocess.run(
                ['adb', '-s', device_id, 'shell', 'getprop', prop],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                return result.stdout.strip()

        except:
            pass

        return None

    def _check_root_access(self, device_id: str) -> bool:
        """Check if device has root access"""
        try:
            # Try to access root
            result = subprocess.run(
                ['adb', '-s', device_id, 'shell', 'su -c "echo test"'],
                capture_output=True,
                text=True,
                timeout=5
            )

            return result.returncode == 0 and 'test' in result.stdout

        except:
            return False

    def scan_devices(self) -> List[AndroidDevice]:
        """Scan for connected Android devices"""
        if not self.check_adb_available():
            print("❌ ADB not available. Please install Android SDK Platform Tools.")
            return []

        device_ids = self.list_connected_devices()
        devices = []

        for device_id in device_ids:
            device_info = self.get_device_info(device_id)
            if device_info:
                devices.append(device_info)

        self.connected_devices = devices
        return devices

    def get_installed_packages(self, device_id: str) -> List[str]:
        """Get list of installed packages on device"""
        try:
            result = subprocess.run(
                ['adb', '-s', device_id, 'shell', 'pm', 'list', 'packages'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                # Parse package names
                packages = []
                for line in result.stdout.split('\n'):
                    if line.startswith('package:'):
                        package = line.replace('package:', '').strip()
                        packages.append(package)

                return packages

        except:
            pass

        return []

    def scan_bloatware(self, device_id: str) -> List[AndroidBloatware]:
        """Scan device for known bloatware"""
        installed_packages = self.get_installed_packages(device_id)

        found_bloatware = []
        for bloat in self.bloatware_database:
            if bloat.package_name in installed_packages:
                found_bloatware.append(bloat)

        return found_bloatware

    def uninstall_package(self, device_id: str, package_name: str, force: bool = False) -> Tuple[bool, str]:
        """
        Uninstall package from device.
        Returns (success, message).
        """
        try:
            # Use 'pm uninstall -k --user 0' for non-root
            # This disables for current user but keeps package
            cmd = ['adb', '-s', device_id, 'shell', 'pm', 'uninstall', '-k', '--user', '0', package_name]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if 'Success' in result.stdout:
                return True, f"Successfully uninstalled {package_name}"
            else:
                return False, f"Failed to uninstall {package_name}: {result.stdout}"

        except Exception as e:
            return False, f"Error uninstalling {package_name}: {e}"

    def disable_package(self, device_id: str, package_name: str) -> Tuple[bool, str]:
        """Disable package (safer than uninstall)"""
        try:
            cmd = ['adb', '-s', device_id, 'shell', 'pm', 'disable-user', '--user', '0', package_name]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if 'new state: disabled' in result.stdout.lower():
                return True, f"Successfully disabled {package_name}"
            else:
                return False, f"Failed to disable {package_name}: {result.stdout}"

        except Exception as e:
            return False, f"Error disabling {package_name}: {e}"

    def clear_app_cache(self, device_id: str) -> Tuple[bool, str]:
        """Clear all app caches (requires root or specific permissions)"""
        try:
            # Try to clear cache (may require root)
            cmd = ['adb', '-s', device_id, 'shell', 'pm', 'trim-caches', '1G']

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                return True, "Cleared app caches"
            else:
                return False, f"Failed to clear caches: {result.stdout}"

        except Exception as e:
            return False, f"Error clearing caches: {e}"

    def optimize_battery(self, device_id: str) -> Dict[str, Tuple[bool, str]]:
        """Apply battery optimizations"""
        results = {}

        # Disable unnecessary services
        optimizations = [
            ("Disable location", "settings put secure location_providers_allowed -gps,-network"),
            ("Reduce animations", "settings put global window_animation_scale 0.5"),
            ("Reduce transitions", "settings put global transition_animation_scale 0.5"),
            ("Reduce animator", "settings put global animator_duration_scale 0.5"),
        ]

        for name, cmd in optimizations:
            try:
                result = subprocess.run(
                    ['adb', '-s', device_id, 'shell', cmd],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                results[name] = (result.returncode == 0, "Applied" if result.returncode == 0 else "Failed")

            except Exception as e:
                results[name] = (False, str(e))

        return results

    def optimize_performance(self, device_id: str) -> Dict[str, Tuple[bool, str]]:
        """Apply performance optimizations"""
        results = {}

        optimizations = [
            ("Force GPU rendering", "setprop debug.hwui.render_dirty_regions false"),
            ("Disable hardware overlays", "setprop persist.sys.ui.hw false"),
            ("Enable 4x MSAA (GPU)", "setprop debug.egl.hw 1"),
        ]

        for name, cmd in optimizations:
            try:
                result = subprocess.run(
                    ['adb', '-s', device_id, 'shell', cmd],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                results[name] = (result.returncode == 0, "Applied" if result.returncode == 0 else "Failed")

            except Exception as e:
                results[name] = (False, str(e))

        return results

    def get_optimization_report(self, device: AndroidDevice) -> Dict:
        """Generate optimization report for device"""
        bloatware = self.scan_bloatware(device.device_id)

        safe_to_remove = [b for b in bloatware if b.safe_to_remove]
        caution_required = [b for b in bloatware if not b.safe_to_remove]

        return {
            "device": {
                "model": device.model,
                "brand": device.brand,
                "android_version": device.android_version,
                "is_rooted": device.is_rooted,
                "optimization_level": device.optimization_level.value
            },
            "bloatware": {
                "total": len(bloatware),
                "safe_to_remove": len(safe_to_remove),
                "caution_required": len(caution_required),
                "details": {
                    "safe": [{"package": b.package_name, "description": b.description} for b in safe_to_remove],
                    "caution": [{"package": b.package_name, "description": b.description} for b in caution_required]
                }
            },
            "optimizations_available": {
                "battery": ["Disable GPS", "Reduce animations", "Optimize transitions"],
                "performance": ["GPU rendering", "Hardware overlays", "4x MSAA"],
                "storage": ["Clear caches", "Remove bloatware"]
            }
        }


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("📱 Android Device Optimizer")
    print("=" * 60)
    print()

    optimizer = AndroidOptimizer()

    # Check ADB
    if not optimizer.check_adb_available():
        print("❌ ADB not found. Please install Android SDK Platform Tools.")
        print("   Ubuntu/Debian: sudo apt-get install android-tools-adb")
        print("   macOS: brew install android-platform-tools")
        print("   Windows: Download from developer.android.com")
        exit(1)

    print("✅ ADB available\n")

    # Scan devices
    print("🔍 Scanning for connected devices...")
    devices = optimizer.scan_devices()

    if not devices:
        print("❌ No devices found")
        print("\n   Make sure:")
        print("   1. USB debugging is enabled on your Android device")
        print("   2. Device is connected via USB")
        print("   3. You accepted the RSA key fingerprint")
        exit(1)

    print(f"\n✅ Found {len(devices)} device(s)\n")

    for device in devices:
        print(f"📱 Device: {device.model}")
        print(f"   Brand: {device.brand}")
        print(f"   Android: {device.android_version}")
        print(f"   Rooted: {'Yes' if device.is_rooted else 'No'}")
        print(f"   Optimization Level: {device.optimization_level.value}")
        print()

        # Scan bloatware
        print("   🔍 Scanning for bloatware...")
        report = optimizer.get_optimization_report(device)

        if report['bloatware']['total'] > 0:
            print(f"   📊 Found {report['bloatware']['total']} bloatware apps")
            print(f"      ✅ Safe to remove: {report['bloatware']['safe_to_remove']}")
            print(f"      ⚠️  Caution: {report['bloatware']['caution_required']}")

            # Show details
            for item in report['bloatware']['details']['safe'][:5]:
                print(f"         • {item['description']}")
        else:
            print("   ✅ No known bloatware found")

        print()

    print("✅ Scan complete")
