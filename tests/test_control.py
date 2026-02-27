"""
Tests for Control Module
Tests kill switch, command receiver, telemetry, heartbeat, and updates
"""

import pytest
import asyncio
import tempfile
import os
import json
from datetime import datetime, timedelta

# Import control modules
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.control.kill_switch import KillSwitch, EmergencyLevel, KillSwitchEvent
from src.control.command_receiver import CommandReceiver, CommandType, Command
from src.control.telemetry_sender import TelemetrySender, TelemetryLevel, TelemetryReport
from src.control.heartbeat_manager import HeartbeatManager, HeartbeatStatus
from src.control.update_receiver import UpdateReceiver, UpdateType, UpdateStatus, ProtocolUpdate


class TestKillSwitch:
    """Tests for Kill Switch module"""
    
    def test_soft_shutdown(self):
        """Test soft shutdown creates stop flag"""
        with tempfile.TemporaryDirectory() as tmpdir:
            ks = KillSwitch(protocol_base_dir=tmpdir)
            
            event = ks.activate(EmergencyLevel.SOFT, "Test soft shutdown", "test")
            
            assert event.success
            assert event.level == EmergencyLevel.SOFT
            assert os.path.exists(os.path.join(tmpdir, ".stop"))
            assert "Created stop flag file" in event.actions_taken
    
    def test_hard_shutdown(self):
        """Test hard shutdown preserves state"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a state file
            state_file = os.path.join(tmpdir, "state.json")
            with open(state_file, 'w') as f:
                json.dump({"test": "data"}, f)
            
            ks = KillSwitch(protocol_base_dir=tmpdir, state_file=state_file)
            
            event = ks.activate(EmergencyLevel.HARD, "Test hard shutdown", "test")
            
            assert event.success
            assert event.level == EmergencyLevel.HARD
            # Check backup was created
            assert any("backup" in action.lower() for action in event.actions_taken)
    
    def test_cannot_reset_after_nuclear(self):
        """Test that nuclear shutdown cannot be reset"""
        with tempfile.TemporaryDirectory() as tmpdir:
            ks = KillSwitch(protocol_base_dir=tmpdir)
            
            ks.activate(EmergencyLevel.NUCLEAR, "Test nuclear", "test")
            
            assert not ks.reset()
    
    def test_activation_tracking(self):
        """Test activation event is tracked"""
        with tempfile.TemporaryDirectory() as tmpdir:
            ks = KillSwitch(protocol_base_dir=tmpdir)
            
            assert not ks.is_activated()
            assert ks.get_activation_event() is None
            
            ks.activate(EmergencyLevel.SOFT, "Test", "test")
            
            assert ks.is_activated()
            assert ks.get_activation_event() is not None


class TestCommandReceiver:
    """Tests for Command Receiver module"""
    
    def test_command_parsing(self):
        """Test parsing a valid command"""
        secret = "test_secret_key"
        receiver = CommandReceiver(secret_key=secret)
        
        # Create command payload
        payload = json.dumps({
            "command_id": "test-001",
            "command_type": "ping",
            "timestamp": datetime.now().isoformat(),
            "source": "test_controller"
        })
        
        # Sign it
        import hmac
        import hashlib
        signature = hmac.new(
            secret.encode(), 
            payload.encode(), 
            hashlib.sha256
        ).hexdigest()
        
        # Parse
        command = receiver.parse_command(payload, signature)
        
        assert command is not None
        assert command.command_id == "test-001"
        assert command.command_type == CommandType.PING
    
    def test_invalid_signature_rejected(self):
        """Test that invalid signatures are rejected"""
        receiver = CommandReceiver(secret_key="secret")
        
        payload = json.dumps({
            "command_id": "test-001",
            "command_type": "ping",
            "timestamp": datetime.now().isoformat(),
            "source": "test_controller"
        })
        
        command = receiver.parse_command(payload, "invalid_signature")
        
        assert command is None
    
    def test_expired_command_rejected(self):
        """Test that expired commands are rejected"""
        secret = "test_secret"
        receiver = CommandReceiver(secret_key=secret)
        
        # Create expired command
        payload = json.dumps({
            "command_id": "test-001",
            "command_type": "ping",
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
            "source": "test_controller",
            "expires_at": (datetime.now() - timedelta(minutes=30)).isoformat()
        })
        
        import hmac
        import hashlib
        signature = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        
        command = receiver.parse_command(payload, signature)
        
        assert command is None
    
    @pytest.mark.asyncio
    async def test_ping_command(self):
        """Test PING command execution"""
        receiver = CommandReceiver(secret_key="test")
        
        command = Command(
            command_id="test-001",
            command_type=CommandType.PING,
            timestamp=datetime.now(),
            source="test",
            parameters={},
            signature="test",
            expires_at=None
        )
        
        result = await receiver.execute_command(command)
        
        assert result["success"]
        assert result["data"]["pong"] == True


class TestTelemetrySender:
    """Tests for Telemetry Sender module"""
    
    def test_report_creation(self):
        """Test creating a telemetry report"""
        sender = TelemetrySender(enabled=False)  # Disabled to avoid network calls
        
        # Record some activity
        sender.record_device_encountered()
        sender.record_device_encountered()
        sender.record_optimization_applied()
        sender.record_threat_removed()
        
        report = sender.create_report()
        
        assert report.devices_encountered == 2
        assert report.optimizations_applied == 1
        assert report.threats_removed == 1
    
    def test_health_status(self):
        """Test health status determination"""
        sender = TelemetrySender(enabled=False)
        
        assert sender.get_health_status() == "healthy"
        
        # Record many errors
        for _ in range(20):
            sender.record_error("test_error")
        
        sender._optimizations_applied = 1  # Low to make error rate high
        
        assert sender.get_health_status() in ["warning", "critical"]
    
    def test_privacy_no_identifiable_data(self):
        """Test that reports contain no identifiable data"""
        sender = TelemetrySender(enabled=False)
        report = sender.create_report()
        
        data = report.to_dict()
        
        # Check no sensitive fields
        assert "ip_address" not in data
        assert "hostname" not in data
        assert "mac_address" not in data
        assert "username" not in data
    
    def test_telemetry_levels(self):
        """Test different telemetry detail levels"""
        sender = TelemetrySender(enabled=False, level=TelemetryLevel.MINIMAL)
        
        minimal_report = sender.create_report(TelemetryLevel.MINIMAL)
        assert "detailed_stats" not in minimal_report.to_dict() or not minimal_report.detailed_stats
        
        detailed_report = sender.create_report(TelemetryLevel.DETAILED)
        assert detailed_report.detailed_stats  # Should have extra data


class TestHeartbeatManager:
    """Tests for Heartbeat Manager module"""
    
    def test_status_tracking(self):
        """Test heartbeat status tracking"""
        manager = HeartbeatManager(endpoint=None)  # No endpoint
        
        assert not manager.is_healthy  # No heartbeat yet
        
        # After a heartbeat cycle (would need to run async in real test)
        # This is a simplified check
        status = manager.get_status()
        
        assert "running" in status
        assert "interval" in status
    
    def test_dead_man_switch(self):
        """Test dead man's switch logic"""
        manager = HeartbeatManager(endpoint=None, interval=60, max_failures=3)
        
        # Without any checkin
        assert not manager.check_dead_man()
        
        # Simulate checkin
        manager._last_checkin = datetime.now()
        assert manager.check_dead_man()
    
    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Test starting and stopping heartbeat"""
        manager = HeartbeatManager(endpoint=None, interval=1)
        
        await manager.start()
        assert manager._running
        
        await manager.stop()
        assert not manager._running


class TestUpdateReceiver:
    """Tests for Update Receiver module"""
    
    def test_update_compatibility_check(self):
        """Test update version compatibility check"""
        update = ProtocolUpdate(
            update_id="test-001",
            update_type=UpdateType.PROTOCOL,
            version="0.3.0",
            released_at=datetime.now(),
            size_bytes=1000,
            checksum_sha256="abc123",
            download_url="http://example.com/update.tar.gz",
            description="Test update",
            requires_restart=True,
            min_version="0.2.0",
            max_version="0.2.99",
            changelog=["Fix 1", "Fix 2"]
        )
        
        assert update.is_compatible("0.2.0")
        assert update.is_compatible("0.2.5")
        assert not update.is_compatible("0.1.0")
        assert not update.is_compatible("0.3.0")
    
    def test_status_tracking(self):
        """Test update system status"""
        receiver = UpdateReceiver()
        
        status = receiver.get_status()
        
        assert "current_version" in status
        assert "auto_update" in status
        assert status["current_version"] == "0.2.0-alpha"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
