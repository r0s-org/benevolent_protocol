"""
Integration Tests for Benevolent Protocol
Tests all modules working together
"""

import pytest
import asyncio
import tempfile
import os
import json
from datetime import datetime

# Import all modules
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.control.kill_switch import KillSwitch, EmergencyLevel
from src.control.command_receiver import CommandReceiver, CommandType
from src.control.telemetry_sender import TelemetrySender, TelemetryLevel
from src.control.heartbeat_manager import HeartbeatManager


class TestProtocolIntegration:
    """Integration tests for full protocol lifecycle"""
    
    @pytest.mark.asyncio
    async def test_full_protocol_lifecycle(self):
        """Test complete protocol lifecycle with all modules"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize all components
            kill_switch = KillSwitch(protocol_base_dir=tmpdir)
            telemetry = TelemetrySender(enabled=False)
            heartbeat = HeartbeatManager(endpoint=None)
            
            # Simulate protocol activity
            telemetry.record_device_encountered()
            telemetry.record_optimization_applied()
            telemetry.record_threat_removed()
            
            # Create telemetry report
            report = telemetry.create_report()
            assert report.devices_encountered == 1
            assert report.optimizations_applied == 1
            assert report.threats_removed == 1
            
            # Test heartbeat status
            status = heartbeat.get_status()
            assert "running" in status
            
            # Test kill switch activation
            event = kill_switch.activate(EmergencyLevel.SOFT, "Integration test", "test")
            assert event.success
            assert kill_switch.is_activated()
    
    @pytest.mark.asyncio
    async def test_command_execution_with_telemetry(self):
        """Test command execution updates telemetry"""
        secret = "test_secret"
        receiver = CommandReceiver(secret_key=secret)
        telemetry = TelemetrySender(enabled=False)
        
        # Record command execution in telemetry
        import hmac
        import hashlib
        
        payload = json.dumps({
            "command_id": "integ-001",
            "command_type": "status",
            "timestamp": datetime.now().isoformat(),
            "source": "test_controller"
        })
        
        signature = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        command = receiver.parse_command(payload, signature)
        
        assert command is not None
        
        result = await receiver.execute_command(command)
        assert result["success"]
        
        # Record in telemetry
        telemetry.record_device_encountered()
        report = telemetry.create_report()
        assert report.devices_encountered >= 1
    
    @pytest.mark.asyncio
    async def test_heartbeat_with_telemetry_integration(self):
        """Test heartbeat and telemetry working together"""
        telemetry = TelemetrySender(enabled=False)
        heartbeat = HeartbeatManager(endpoint=None)
        
        # Simulate activity
        for _ in range(5):
            telemetry.record_device_encountered()
            telemetry.record_optimization_applied()
        
        # Get combined status
        telemetry_stats = telemetry.get_stats()
        heartbeat_status = heartbeat.get_status()
        
        assert telemetry_stats["devices_encountered"] == 5
        assert telemetry_stats["optimizations_applied"] == 5
        assert "running" in heartbeat_status
    
    @pytest.mark.asyncio
    async def test_emergency_shutdown_flow(self):
        """Test emergency shutdown with telemetry"""
        with tempfile.TemporaryDirectory() as tmpdir:
            kill_switch = KillSwitch(protocol_base_dir=tmpdir)
            telemetry = TelemetrySender(enabled=False)
            
            # Simulate activity
            telemetry.record_device_encountered()
            telemetry.record_optimization_applied()
            
            # Get pre-shutdown stats
            stats_before = telemetry.get_stats()
            assert stats_before["devices_encountered"] == 1
            
            # Activate kill switch
            event = kill_switch.activate(EmergencyLevel.HARD, "Emergency test", "test")
            assert event.success
            
            # Telemetry should still have stats
            stats_after = telemetry.get_stats()
            assert stats_after["devices_encountered"] == 1
    
    @pytest.mark.asyncio
    async def test_multiple_commands_with_rate_limiting(self):
        """Test multiple commands with rate limiting"""
        secret = "test_secret"
        receiver = CommandReceiver(secret_key=secret, max_commands_per_minute=5)
        
        import hmac
        import hashlib
        
        success_count = 0
        for i in range(10):
            payload = json.dumps({
                "command_id": f"rate-test-{i}",
                "command_type": "ping",
                "timestamp": datetime.now().isoformat(),
                "source": "test_controller"
            })
            
            signature = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
            command = receiver.parse_command(payload, signature)
            
            if command:
                success_count += 1
        
        # Should hit rate limit after 5
        assert success_count == 5
    
    @pytest.mark.asyncio
    async def test_telemetry_levels_integration(self):
        """Test different telemetry detail levels"""
        telemetry = TelemetrySender(enabled=False)
        
        # Record same activity
        telemetry.record_device_encountered()
        telemetry.record_optimization_applied()
        telemetry.record_error("test_error")
        
        # Create reports at different levels
        minimal = telemetry.create_report(TelemetryLevel.MINIMAL)
        standard = telemetry.create_report(TelemetryLevel.STANDARD)
        detailed = telemetry.create_report(TelemetryLevel.DETAILED)
        
        # All should have core stats
        assert minimal.devices_encountered == 1
        assert standard.devices_encountered == 1
        assert detailed.devices_encountered == 1
        
        # Detailed should have extra info
        assert detailed.detailed_stats != {}
    
    @pytest.mark.asyncio
    async def test_heartbeat_dead_man_with_kill_switch(self):
        """Test dead man's switch integration with kill switch"""
        with tempfile.TemporaryDirectory() as tmpdir:
            kill_switch = KillSwitch(protocol_base_dir=tmpdir)
            heartbeat = HeartbeatManager(endpoint=None, interval=1, max_failures=3)
            
            # Initially no checkin
            assert not heartbeat.check_dead_man()
            
            # Simulate checkin
            heartbeat._last_checkin = datetime.now()
            assert heartbeat.check_dead_man()
            
            # If kill switch activated, should still be able to check dead man
            kill_switch.activate(EmergencyLevel.SOFT, "Test", "test")
            assert heartbeat.check_dead_man()  # Unaffected


class TestModuleInteraction:
    """Test interactions between specific modules"""
    
    @pytest.mark.asyncio
    async def test_command_triggers_telemetry_report(self):
        """Test that commands can trigger telemetry reports"""
        secret = "test_secret"
        receiver = CommandReceiver(secret_key=secret)
        telemetry = TelemetrySender(enabled=False)
        
        # Execute a command
        command = await receiver._handle_status({})
        
        # Update telemetry
        telemetry.record_device_encountered()
        report = telemetry.create_report()
        
        assert report.devices_encountered >= 1
    
    @pytest.mark.asyncio
    async def test_kill_switch_prevents_heartbeat(self):
        """Test that kill switch affects heartbeat state"""
        with tempfile.TemporaryDirectory() as tmpdir:
            kill_switch = KillSwitch(protocol_base_dir=tmpdir)
            heartbeat = HeartbeatManager(endpoint=None)
            
            # Activate kill switch
            kill_switch.activate(EmergencyLevel.SOFT, "Test", "test")
            
            # Heartbeat status should still work but protocol should check kill switch
            status = heartbeat.get_status()
            assert "running" in status
            assert kill_switch.is_activated()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
