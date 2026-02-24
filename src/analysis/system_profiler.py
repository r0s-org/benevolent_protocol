"""
System Profiler Module
Analyzes device hardware, software, and performance characteristics
"""

import psutil
import platform
import subprocess
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SystemProfile:
    """Complete system profile data structure"""
    # Hardware
    cpu_cores: int
    cpu_usage: float
    total_memory: int  # bytes
    available_memory: int  # bytes
    memory_usage: float  # percentage
    total_disk: int  # bytes
    free_disk: int  # bytes
    disk_usage: float  # percentage

    # Software
    os_name: str
    os_version: str
    kernel_version: str
    hostname: str

    # Performance
    load_average: tuple
    running_processes: int
    network_connections: int

    # Security
    firewall_active: bool
    open_ports: List[int]

    # Metadata
    profile_timestamp: str
    protocol_version: str


class SystemProfiler:
    """
    Profiles system hardware, software, and performance.
    Identifies optimization opportunities and security issues.
    """

    def __init__(self):
        self.last_profile: SystemProfile = None

    def profile_system(self) -> SystemProfile:
        """
        Generate complete system profile.
        Returns detailed analysis of current device state.
        """
        profile = SystemProfile(
            # Hardware metrics
            cpu_cores=psutil.cpu_count(),
            cpu_usage=psutil.cpu_percent(interval=1),
            total_memory=psutil.virtual_memory().total,
            available_memory=psutil.virtual_memory().available,
            memory_usage=psutil.virtual_memory().percent,
            total_disk=psutil.disk_usage('/').total,
            free_disk=psutil.disk_usage('/').free,
            disk_usage=psutil.disk_usage('/').percent,

            # Software info
            os_name=platform.system(),
            os_version=platform.release(),
            kernel_version=platform.version(),
            hostname=platform.node(),

            # Performance metrics
            load_average=psutil.getloadavg() if hasattr(psutil, 'getloadavg') else (0, 0, 0),
            running_processes=len(psutil.pids()),
            network_connections=len(psutil.net_connections()),

            # Security assessment
            firewall_active=self._check_firewall(),
            open_ports=self._scan_open_ports(),

            # Metadata
            profile_timestamp=datetime.now().isoformat(),
            protocol_version="0.1.0-alpha"
        )

        self.last_profile = profile
        return profile

    def _check_firewall(self) -> bool:
        """Check if firewall is active"""
        try:
            # Linux: Check iptables/ufw
            result = subprocess.run(
                ['iptables', '-L'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0 and len(result.stdout) > 100
        except:
            # Fallback: Assume firewall inactive
            return False

    def _scan_open_ports(self) -> List[int]:
        """Scan for open network ports"""
        try:
            connections = psutil.net_connections(kind='inet')
            open_ports = list(set([conn.laddr.port for conn in connections
                                   if conn.status == 'LISTEN']))
            return sorted(open_ports)
        except:
            return []

    def analyze_performance(self, profile: SystemProfile) -> Dict[str, Any]:
        """
        Analyze performance metrics and identify issues.
        Returns optimization recommendations.
        """
        analysis = {
            "performance_score": 0,
            "issues": [],
            "recommendations": [],
            "critical": False
        }

        # CPU analysis
        if profile.cpu_usage > 80:
            analysis["issues"].append("High CPU usage")
            analysis["recommendations"].append("Optimize CPU-intensive processes")
            analysis["critical"] = True
        elif profile.cpu_usage > 60:
            analysis["issues"].append("Moderate CPU usage")

        # Memory analysis
        if profile.memory_usage > 85:
            analysis["issues"].append("High memory usage")
            analysis["recommendations"].append("Free up memory or add RAM")
            analysis["critical"] = True
        elif profile.memory_usage > 70:
            analysis["issues"].append("Moderate memory usage")

        # Disk analysis
        if profile.disk_usage > 90:
            analysis["issues"].append("Low disk space")
            analysis["recommendations"].append("Clean up disk space")
            analysis["critical"] = True
        elif profile.disk_usage > 80:
            analysis["issues"].append("Moderate disk usage")

        # Calculate performance score (0-100)
        cpu_score = max(0, 100 - profile.cpu_usage)
        memory_score = max(0, 100 - profile.memory_usage)
        disk_score = max(0, 100 - profile.disk_usage)

        analysis["performance_score"] = (cpu_score + memory_score + disk_score) / 3

        return analysis

    def audit_security(self, profile: SystemProfile) -> Dict[str, Any]:
        """
        Audit security posture.
        Identifies vulnerabilities and security improvements.
        """
        audit = {
            "security_score": 0,
            "vulnerabilities": [],
            "recommendations": [],
            "critical": False
        }

        # Firewall check
        if not profile.firewall_active:
            audit["vulnerabilities"].append("Firewall inactive")
            audit["recommendations"].append("Enable firewall")
            audit["critical"] = True

        # Open ports analysis
        suspicious_ports = [21, 23, 25, 135, 139, 445, 3389]  # Common attack vectors
        found_suspicious = [port for port in profile.open_ports
                            if port in suspicious_ports]

        if found_suspicious:
            audit["vulnerabilities"].append(f"Suspicious open ports: {found_suspicious}")
            audit["recommendations"].append("Close unnecessary ports")
            audit["critical"] = True

        # Too many open ports
        if len(profile.open_ports) > 20:
            audit["vulnerabilities"].append("Many open ports detected")
            audit["recommendations"].append("Audit network services")

        # Calculate security score (0-100)
        firewall_score = 100 if profile.firewall_active else 0
        ports_score = max(0, 100 - (len(profile.open_ports) * 5))
        vulnerabilities_penalty = len(audit["vulnerabilities"]) * 15

        audit["security_score"] = max(0, (firewall_score + ports_score) / 2 - vulnerabilities_penalty)

        return audit

    def get_optimization_opportunities(self, profile: SystemProfile) -> List[Dict[str, Any]]:
        """
        Identify all optimization opportunities.
        Returns prioritized list of improvements.
        """
        opportunities = []

        # Performance analysis
        perf_analysis = self.analyze_performance(profile)
        if perf_analysis["issues"]:
            opportunities.append({
                "type": "performance",
                "priority": "high" if perf_analysis["critical"] else "medium",
                "issues": perf_analysis["issues"],
                "recommendations": perf_analysis["recommendations"],
                "current_score": perf_analysis["performance_score"]
            })

        # Security analysis
        sec_audit = self.audit_security(profile)
        if sec_audit["vulnerabilities"]:
            opportunities.append({
                "type": "security",
                "priority": "critical" if sec_audit["critical"] else "high",
                "vulnerabilities": sec_audit["vulnerabilities"],
                "recommendations": sec_audit["recommendations"],
                "current_score": sec_audit["security_score"]
            })

        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        opportunities.sort(key=lambda x: priority_order.get(x["priority"], 99))

        return opportunities


# Example usage
if __name__ == "__main__":
    profiler = SystemProfiler()
    profile = profiler.profile_system()

    print("=== System Profile ===")
    print(f"OS: {profile.os_name} {profile.os_version}")
    print(f"CPU Cores: {profile.cpu_cores}")
    print(f"CPU Usage: {profile.cpu_usage}%")
    print(f"Memory: {profile.available_memory / (1024**3):.2f} GB / {profile.total_memory / (1024**3):.2f} GB")
    print(f"Disk: {profile.free_disk / (1024**3):.2f} GB free of {profile.total_disk / (1024**3):.2f} GB")
    print(f"Firewall: {'Active' if profile.firewall_active else 'Inactive'}")
    print(f"Open Ports: {profile.open_ports}")

    print("\n=== Optimization Opportunities ===")
    opportunities = profiler.get_optimization_opportunities(profile)
    for opp in opportunities:
        print(f"\n{opp['type'].upper()} - Priority: {opp['priority']}")
        if 'issues' in opp:
            for issue in opp['issues']:
                print(f"  - {issue}")
        if 'vulnerabilities' in opp:
            for vuln in opp['vulnerabilities']:
                print(f"  - {vuln}")
