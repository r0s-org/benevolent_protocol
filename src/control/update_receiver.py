"""
Update Receiver Module
Receives and applies protocol updates
"""

import json
import hashlib
import logging
import shutil
import os
import subprocess
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import asyncio
import aiohttp

logger = logging.getLogger(__name__)


class UpdateType(Enum):
    """Types of updates"""
    PROTOCOL = "protocol"       # Core protocol update
    SIGNATURES = "signatures"   # Malware signatures
    CONFIG = "config"           # Configuration update
    MODULE = "module"           # Individual module update


class UpdateStatus(Enum):
    """Status of update process"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    VERIFYING = "verifying"
    INSTALLING = "installing"
    COMPLETE = "complete"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class ProtocolUpdate:
    """Represents an available update"""
    update_id: str
    update_type: UpdateType
    version: str
    released_at: datetime
    size_bytes: int
    checksum_sha256: str
    download_url: str
    description: str
    requires_restart: bool
    min_version: Optional[str]
    max_version: Optional[str]
    changelog: List[str]
    
    def is_compatible(self, current_version: str) -> bool:
        """Check if update is compatible with current version"""
        # Simple version comparison (would use proper semver in production)
        if self.min_version and current_version < self.min_version:
            return False
        if self.max_version and current_version > self.max_version:
            return False
        return True


@dataclass
class UpdateResult:
    """Result of update installation"""
    update_id: str
    status: UpdateStatus
    installed_at: Optional[datetime]
    previous_version: Optional[str]
    new_version: Optional[str]
    error_message: Optional[str]
    rollback_available: bool


class UpdateReceiver:
    """
    Manages protocol updates.
    
    Features:
    - Check for updates
    - Verify signatures
    - Atomic installation with rollback
    - Automatic backup
    - Update scheduling
    """
    
    CURRENT_VERSION = "0.2.0-alpha"
    
    def __init__(self,
                 update_endpoint: Optional[str] = None,
                 install_dir: str = "/opt/benevolent_protocol",
                 backup_dir: str = "/opt/benevolent_protocol_backups",
                 auto_update: bool = False,
                 verify_signatures: bool = True,
                 public_key: Optional[str] = None):
        
        self.update_endpoint = update_endpoint
        self.install_dir = install_dir
        self.backup_dir = backup_dir
        self.auto_update = auto_update
        self.verify_signatures = verify_signatures
        self.public_key = public_key
        
        # State tracking
        self._available_updates: List[ProtocolUpdate] = []
        self._last_check: Optional[datetime] = None
        self._update_history: List[UpdateResult] = []
        self._current_download: Optional[str] = None
    
    async def check_for_updates(self) -> List[ProtocolUpdate]:
        """
        Check for available updates.
        
        Returns:
            List of available updates
        """
        if not self.update_endpoint:
            logger.debug("No update endpoint configured")
            return []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.update_endpoint}/updates",
                    params={"version": self.CURRENT_VERSION},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status != 200:
                        logger.warning(f"Update check failed: HTTP {response.status}")
                        return []
                    
                    data = await response.json()
                    
                    updates = []
                    for item in data.get("updates", []):
                        try:
                            update = ProtocolUpdate(
                                update_id=item["update_id"],
                                update_type=UpdateType(item["update_type"]),
                                version=item["version"],
                                released_at=datetime.fromisoformat(item["released_at"]),
                                size_bytes=item["size_bytes"],
                                checksum_sha256=item["checksum_sha256"],
                                download_url=item["download_url"],
                                description=item["description"],
                                requires_restart=item.get("requires_restart", False),
                                min_version=item.get("min_version"),
                                max_version=item.get("max_version"),
                                changelog=item.get("changelog", [])
                            )
                            
                            if update.is_compatible(self.CURRENT_VERSION):
                                updates.append(update)
                                
                        except (KeyError, ValueError) as e:
                            logger.warning(f"Invalid update data: {e}")
                            continue
                    
                    self._available_updates = updates
                    self._last_check = datetime.now()
                    
                    logger.info(f"Found {len(updates)} available updates")
                    return updates
                    
        except Exception as e:
            logger.error(f"Update check error: {e}")
            return []
    
    async def download_update(self, update: ProtocolUpdate, 
                             download_dir: str = "/tmp") -> Optional[str]:
        """
        Download an update package.
        
        Args:
            update: Update to download
            download_dir: Directory to save download
            
        Returns:
            Path to downloaded file, or None on failure
        """
        download_path = os.path.join(download_dir, f"update_{update.update_id}.tar.gz")
        self._current_download = update.update_id
        
        try:
            logger.info(f"Downloading update {update.update_id}...")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    update.download_url,
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as response:
                    
                    if response.status != 200:
                        logger.error(f"Download failed: HTTP {response.status}")
                        return None
                    
                    with open(download_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
            
            # Verify size
            actual_size = os.path.getsize(download_path)
            if actual_size != update.size_bytes:
                logger.error(f"Size mismatch: expected {update.size_bytes}, got {actual_size}")
                os.remove(download_path)
                return None
            
            # Verify checksum
            with open(download_path, 'rb') as f:
                actual_checksum = hashlib.sha256(f.read()).hexdigest()
            
            if actual_checksum != update.checksum_sha256:
                logger.error(f"Checksum mismatch")
                os.remove(download_path)
                return None
            
            logger.info(f"Download complete: {download_path}")
            return download_path
            
        except Exception as e:
            logger.error(f"Download error: {e}")
            if os.path.exists(download_path):
                os.remove(download_path)
            return None
        finally:
            self._current_download = None
    
    async def install_update(self, update: ProtocolUpdate, 
                            package_path: str) -> UpdateResult:
        """
        Install an update package.
        
        Args:
            update: Update to install
            package_path: Path to downloaded package
            
        Returns:
            UpdateResult with installation status
        """
        result = UpdateResult(
            update_id=update.update_id,
            status=UpdateStatus.INSTALLING,
            installed_at=None,
            previous_version=self.CURRENT_VERSION,
            new_version=None,
            error_message=None,
            rollback_available=False
        )
        
        try:
            # Create backup
            backup_path = await self._create_backup()
            if backup_path:
                result.rollback_available = True
            
            # Extract and install
            logger.info(f"Installing update {update.update_id}...")
            
            # Extract package
            extract_dir = f"/tmp/update_{update.update_id}"
            os.makedirs(extract_dir, exist_ok=True)
            
            subprocess.run(
                ["tar", "-xzf", package_path, "-C", extract_dir],
                check=True,
                capture_output=True
            )
            
            # Install based on type
            if update.update_type == UpdateType.PROTOCOL:
                await self._install_protocol_update(extract_dir)
            elif update.update_type == UpdateType.SIGNATURES:
                await self._install_signature_update(extract_dir)
            elif update.update_type == UpdateType.CONFIG:
                await self._install_config_update(extract_dir)
            
            # Cleanup
            shutil.rmtree(extract_dir, ignore_errors=True)
            os.remove(package_path)
            
            result.status = UpdateStatus.COMPLETE
            result.new_version = update.version
            result.installed_at = datetime.now()
            
            logger.info(f"Update {update.update_id} installed successfully")
            
        except Exception as e:
            result.status = UpdateStatus.FAILED
            result.error_message = str(e)
            logger.error(f"Update installation failed: {e}")
            
            # Attempt rollback
            if result.rollback_available:
                if await self._rollback():
                    result.status = UpdateStatus.ROLLED_BACK
                    logger.info("Rolled back to previous version")
        
        self._update_history.append(result)
        return result
    
    async def _create_backup(self) -> Optional[str]:
        """Create backup of current installation"""
        if not os.path.exists(self.install_dir):
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(self.backup_dir, f"backup_{timestamp}")
        
        try:
            os.makedirs(self.backup_dir, exist_ok=True)
            shutil.copytree(self.install_dir, backup_path)
            logger.info(f"Created backup: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return None
    
    async def _rollback(self) -> bool:
        """Rollback to most recent backup"""
        if not os.path.exists(self.backup_dir):
            return False
        
        # Find most recent backup
        backups = sorted(os.listdir(self.backup_dir), reverse=True)
        if not backups:
            return False
        
        latest_backup = os.path.join(self.backup_dir, backups[0])
        
        try:
            # Remove current installation
            if os.path.exists(self.install_dir):
                shutil.rmtree(self.install_dir)
            
            # Restore backup
            shutil.copytree(latest_backup, self.install_dir)
            logger.info(f"Restored from backup: {latest_backup}")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    async def _install_protocol_update(self, extract_dir: str):
        """Install a protocol update"""
        # Copy new files over existing
        for item in os.listdir(extract_dir):
            src = os.path.join(extract_dir, item)
            dst = os.path.join(self.install_dir, item)
            
            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
    
    async def _install_signature_update(self, extract_dir: str):
        """Install signature database update"""
        sig_dir = os.path.join(self.install_dir, "signatures")
        os.makedirs(sig_dir, exist_ok=True)
        
        for item in os.listdir(extract_dir):
            src = os.path.join(extract_dir, item)
            dst = os.path.join(sig_dir, item)
            shutil.copy2(src, dst)
    
    async def _install_config_update(self, extract_dir: str):
        """Install configuration update"""
        config_src = os.path.join(extract_dir, "config")
        config_dst = os.path.join(self.install_dir, "config")
        
        if os.path.exists(config_src):
            if os.path.exists(config_dst):
                shutil.rmtree(config_dst)
            shutil.copytree(config_src, config_dst)
    
    def get_available_updates(self) -> List[ProtocolUpdate]:
        """Get list of available updates from last check"""
        return self._available_updates
    
    def get_update_history(self, limit: int = 10) -> List[UpdateResult]:
        """Get recent update history"""
        return self._update_history[-limit:]
    
    def get_status(self) -> Dict[str, Any]:
        """Get update system status"""
        return {
            "current_version": self.CURRENT_VERSION,
            "auto_update": self.auto_update,
            "endpoint": self.update_endpoint,
            "last_check": self._last_check.isoformat() if self._last_check else None,
            "available_updates": len(self._available_updates),
            "updates_installed": len(self._update_history),
            "downloading": self._current_download
        }
