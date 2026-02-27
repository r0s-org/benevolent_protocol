"""
Telemetry Sender Module
Sends anonymized status reports to control servers
"""

import json
import hashlib
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import aiohttp
from enum import Enum

logger = logging.getLogger(__name__)


class TelemetryLevel(Enum):
    """Level of detail in telemetry"""
    MINIMAL = "minimal"      # Only critical health data
    STANDARD = "standard"    # Health + basic stats
    DETAILED = "detailed"    # Full diagnostic info


@dataclass
class TelemetryReport:
    """Anonymized telemetry report"""
    report_id: str
    timestamp: datetime
    protocol_version: str
    level: TelemetryLevel
    
    # System health (anonymized)
    platform_type: str           # "linux", "windows", "android"
    health_status: str           # "healthy", "warning", "critical"
    uptime_seconds: int
    
    # Operation stats
    devices_encountered: int
    optimizations_applied: int
    threats_removed: int
    
    # Error tracking
    errors_count: int
    last_error_type: Optional[str]
    
    # Optional detailed data
    detailed_stats: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for transmission"""
        data = {
            "report_id": self.report_id,
            "timestamp": self.timestamp.isoformat(),
            "protocol_version": self.protocol_version,
            "level": self.level.value,
            "platform_type": self.platform_type,
            "health_status": self.health_status,
            "uptime_seconds": self.uptime_seconds,
            "devices_encountered": self.devices_encountered,
            "optimizations_applied": self.optimizations_applied,
            "threats_removed": self.threats_removed,
            "errors_count": self.errors_count,
            "last_error_type": self.last_error_type
        }
        
        if self.level == TelemetryLevel.DETAILED:
            data["detailed_stats"] = self.detailed_stats
        
        return data


class TelemetrySender:
    """
    Sends anonymized telemetry to control servers.
    
    Privacy principles:
    - No personal data (names, IPs, MAC addresses)
    - No file paths or content
    - No system identifiers beyond platform type
    - Opt-out supported
    """
    
    PROTOCOL_VERSION = "0.2.0-alpha"
    
    def __init__(self,
                 endpoint: Optional[str] = None,
                 level: TelemetryLevel = TelemetryLevel.STANDARD,
                 enabled: bool = True,
                 send_interval: int = 3600,  # 1 hour
                 api_key: Optional[str] = None):
        
        self.endpoint = endpoint
        self.level = level
        self.enabled = enabled
        self.send_interval = send_interval
        self.api_key = api_key
        
        # Stats tracking
        self._start_time = datetime.now()
        self._devices_encountered = 0
        self._optimizations_applied = 0
        self._threats_removed = 0
        self._errors: list = []
        self._platform_type = self._detect_platform()
        
        # Transmission tracking
        self._last_sent: Optional[datetime] = None
        self._send_count = 0
        self._failure_count = 0
    
    def _detect_platform(self) -> str:
        """Detect current platform"""
        import platform
        system = platform.system().lower()
        if system == "linux":
            # Check if Android
            try:
                with open("/proc/version", "r") as f:
                    if "android" in f.read().lower():
                        return "android"
            except:
                pass
            return "linux"
        elif system == "windows":
            return "windows"
        elif system == "darwin":
            return "macos"
        return "unknown"
    
    def generate_report_id(self) -> str:
        """Generate unique but anonymous report ID"""
        # Hash of timestamp + random for uniqueness without tracking
        data = f"{datetime.now().isoformat()}-{id(self)}".encode()
        return hashlib.sha256(data).hexdigest()[:16]
    
    def record_device_encountered(self):
        """Record that a new device was encountered"""
        self._devices_encountered += 1
    
    def record_optimization_applied(self):
        """Record that an optimization was applied"""
        self._optimizations_applied += 1
    
    def record_threat_removed(self):
        """Record that a threat was removed"""
        self._threats_removed += 1
    
    def record_error(self, error_type: str, message: str = ""):
        """Record an error (anonymized)"""
        self._errors.append({
            "type": error_type,
            "timestamp": datetime.now().isoformat()
            # Message intentionally NOT included for privacy
        })
        
        # Keep only last 100 errors
        if len(self._errors) > 100:
            self._errors = self._errors[-100:]
    
    def get_uptime(self) -> int:
        """Get uptime in seconds"""
        return int((datetime.now() - self._start_time).total_seconds())
    
    def get_health_status(self) -> str:
        """Determine current health status"""
        error_rate = len(self._errors) / max(1, self._optimizations_applied + 1)
        
        if error_rate > 0.5:
            return "critical"
        elif error_rate > 0.1:
            return "warning"
        else:
            return "healthy"
    
    def create_report(self, level: Optional[TelemetryLevel] = None) -> TelemetryReport:
        """
        Create a telemetry report.
        
        Args:
            level: Override default telemetry level
            
        Returns:
            TelemetryReport ready for transmission
        """
        report_level = level or self.level
        
        # Get last error type
        last_error_type = None
        if self._errors:
            last_error_type = self._errors[-1]["type"]
        
        # Build detailed stats if needed
        detailed_stats = {}
        if report_level == TelemetryLevel.DETAILED:
            detailed_stats = {
                "error_types": list(set(e["type"] for e in self._errors)),
                "uptime_hours": self.get_uptime() / 3600,
                "avg_optimizations_per_device": (
                    self._optimizations_applied / max(1, self._devices_encountered)
                )
            }
        
        return TelemetryReport(
            report_id=self.generate_report_id(),
            timestamp=datetime.now(),
            protocol_version=self.PROTOCOL_VERSION,
            level=report_level,
            platform_type=self._platform_type,
            health_status=self.get_health_status(),
            uptime_seconds=self.get_uptime(),
            devices_encountered=self._devices_encountered,
            optimizations_applied=self._optimizations_applied,
            threats_removed=self._threats_removed,
            errors_count=len(self._errors),
            last_error_type=last_error_type,
            detailed_stats=detailed_stats
        )
    
    async def send_report(self, report: Optional[TelemetryReport] = None) -> bool:
        """
        Send telemetry report to endpoint.
        
        Args:
            report: Report to send, or None to create one
            
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            logger.debug("Telemetry disabled, skipping report")
            return False
        
        if not self.endpoint:
            logger.debug("No telemetry endpoint configured")
            return False
        
        if report is None:
            report = self.create_report()
        
        try:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.endpoint,
                    json=report.to_dict(),
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        self._last_sent = datetime.now()
                        self._send_count += 1
                        logger.info(f"Telemetry report {report.report_id} sent successfully")
                        return True
                    else:
                        self._failure_count += 1
                        logger.warning(f"Telemetry send failed: HTTP {response.status}")
                        return False
                        
        except asyncio.TimeoutError:
            self._failure_count += 1
            logger.error("Telemetry send timeout")
            return False
        except Exception as e:
            self._failure_count += 1
            logger.error(f"Telemetry send error: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current telemetry stats"""
        return {
            "enabled": self.enabled,
            "level": self.level.value,
            "endpoint": self.endpoint,
            "uptime_seconds": self.get_uptime(),
            "devices_encountered": self._devices_encountered,
            "optimizations_applied": self._optimizations_applied,
            "threats_removed": self._threats_removed,
            "errors_count": len(self._errors),
            "reports_sent": self._send_count,
            "send_failures": self._failure_count,
            "last_sent": self._last_sent.isoformat() if self._last_sent else None
        }
    
    def reset_stats(self):
        """Reset all tracked stats"""
        self._devices_encountered = 0
        self._optimizations_applied = 0
        self._threats_removed = 0
        self._errors = []
        self._start_time = datetime.now()
        logger.info("Telemetry stats reset")
    
    def set_enabled(self, enabled: bool):
        """Enable or disable telemetry"""
        self.enabled = enabled
        logger.info(f"Telemetry {'enabled' if enabled else 'disabled'}")
    
    def set_level(self, level: TelemetryLevel):
        """Set telemetry detail level"""
        self.level = level
        logger.info(f"Telemetry level set to {level.value}")
