"""
CasareRPA - Trigger Base Classes Tests

Comprehensive tests for trigger base classes, enums, and core functionality.
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

import pytest

# Add src to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from casare_rpa.triggers.base import (
    TriggerType,
    TriggerStatus,
    TriggerPriority,
    TriggerEvent,
    BaseTriggerConfig,
    BaseTrigger,
    TriggerEventCallback,
)


# =============================================================================
# TriggerType Enum Tests
# =============================================================================

class TestTriggerType:
    """Tests for TriggerType enum."""

    def test_all_trigger_types_exist(self):
        """Verify all expected trigger types are defined."""
        expected_types = [
            "manual", "scheduled", "webhook", "file_watch", "email",
            "app_event", "form", "chat", "error", "workflow_call"
        ]
        for type_str in expected_types:
            assert TriggerType(type_str) is not None

    def test_trigger_type_values(self):
        """Test trigger type string values."""
        assert TriggerType.MANUAL.value == "manual"
        assert TriggerType.SCHEDULED.value == "scheduled"
        assert TriggerType.WEBHOOK.value == "webhook"
        assert TriggerType.FILE_WATCH.value == "file_watch"
        assert TriggerType.EMAIL.value == "email"
        assert TriggerType.APP_EVENT.value == "app_event"
        assert TriggerType.FORM.value == "form"
        assert TriggerType.CHAT.value == "chat"
        assert TriggerType.ERROR.value == "error"
        assert TriggerType.WORKFLOW_CALL.value == "workflow_call"

    def test_invalid_trigger_type_raises_error(self):
        """Test that invalid trigger type raises ValueError."""
        with pytest.raises(ValueError):
            TriggerType("invalid_type")

    def test_trigger_type_case_sensitive(self):
        """Test that trigger types are case-sensitive."""
        with pytest.raises(ValueError):
            TriggerType("MANUAL")
        with pytest.raises(ValueError):
            TriggerType("Scheduled")


# =============================================================================
# TriggerStatus Enum Tests
# =============================================================================

class TestTriggerStatus:
    """Tests for TriggerStatus enum."""

    def test_all_statuses_exist(self):
        """Verify all expected statuses are defined."""
        expected_statuses = ["inactive", "starting", "active", "paused", "stopping", "error"]
        for status_str in expected_statuses:
            assert TriggerStatus(status_str) is not None

    def test_status_values(self):
        """Test status string values."""
        assert TriggerStatus.INACTIVE.value == "inactive"
        assert TriggerStatus.STARTING.value == "starting"
        assert TriggerStatus.ACTIVE.value == "active"
        assert TriggerStatus.PAUSED.value == "paused"
        assert TriggerStatus.STOPPING.value == "stopping"
        assert TriggerStatus.ERROR.value == "error"


# =============================================================================
# TriggerPriority Enum Tests
# =============================================================================

class TestTriggerPriority:
    """Tests for TriggerPriority enum."""

    def test_priority_values(self):
        """Test priority numeric values."""
        assert TriggerPriority.LOW.value == 0
        assert TriggerPriority.NORMAL.value == 1
        assert TriggerPriority.HIGH.value == 2
        assert TriggerPriority.CRITICAL.value == 3

    def test_priority_ordering(self):
        """Test that priorities are correctly ordered."""
        assert TriggerPriority.LOW.value < TriggerPriority.NORMAL.value
        assert TriggerPriority.NORMAL.value < TriggerPriority.HIGH.value
        assert TriggerPriority.HIGH.value < TriggerPriority.CRITICAL.value


# =============================================================================
# TriggerEvent Tests
# =============================================================================

class TestTriggerEvent:
    """Tests for TriggerEvent dataclass."""

    def test_create_basic_event(self):
        """Test creating a basic trigger event."""
        event = TriggerEvent(
            trigger_id="test_trigger",
            trigger_type=TriggerType.MANUAL,
            workflow_id="workflow_001",
            scenario_id="scenario_001"
        )
        assert event.trigger_id == "test_trigger"
        assert event.trigger_type == TriggerType.MANUAL
        assert event.workflow_id == "workflow_001"
        assert event.scenario_id == "scenario_001"
        assert isinstance(event.timestamp, datetime)
        assert event.payload == {}
        assert event.metadata == {}
        assert event.priority == 1

    def test_create_event_with_payload(self):
        """Test creating event with custom payload."""
        payload = {"file_path": "/test/file.txt", "event": "created"}
        event = TriggerEvent(
            trigger_id="file_trigger",
            trigger_type=TriggerType.FILE_WATCH,
            workflow_id="wf_001",
            scenario_id="sc_001",
            payload=payload
        )
        assert event.payload == payload
        assert event.payload["file_path"] == "/test/file.txt"

    def test_create_event_with_metadata(self):
        """Test creating event with metadata."""
        metadata = {"source": "test", "version": "1.0"}
        event = TriggerEvent(
            trigger_id="test",
            trigger_type=TriggerType.WEBHOOK,
            workflow_id="wf",
            scenario_id="sc",
            metadata=metadata
        )
        assert event.metadata == metadata

    def test_create_event_with_priority(self):
        """Test creating event with different priorities."""
        for priority in [0, 1, 2, 3]:
            event = TriggerEvent(
                trigger_id="test",
                trigger_type=TriggerType.MANUAL,
                workflow_id="wf",
                scenario_id="sc",
                priority=priority
            )
            assert event.priority == priority

    def test_event_to_dict(self):
        """Test serializing event to dictionary."""
        event = TriggerEvent(
            trigger_id="test_trigger",
            trigger_type=TriggerType.SCHEDULED,
            workflow_id="workflow_001",
            scenario_id="scenario_001",
            payload={"key": "value"},
            metadata={"source": "test"},
            priority=2
        )
        data = event.to_dict()

        assert data["trigger_id"] == "test_trigger"
        assert data["trigger_type"] == "scheduled"
        assert data["workflow_id"] == "workflow_001"
        assert data["scenario_id"] == "scenario_001"
        assert data["payload"] == {"key": "value"}
        assert data["metadata"] == {"source": "test"}
        assert data["priority"] == 2
        assert "timestamp" in data

    def test_event_from_dict(self):
        """Test deserializing event from dictionary."""
        data = {
            "trigger_id": "restored_trigger",
            "trigger_type": "webhook",
            "workflow_id": "wf_restored",
            "scenario_id": "sc_restored",
            "timestamp": "2024-01-15T10:30:00",
            "payload": {"data": "restored"},
            "metadata": {"restored": True},
            "priority": 3
        }
        event = TriggerEvent.from_dict(data)

        assert event.trigger_id == "restored_trigger"
        assert event.trigger_type == TriggerType.WEBHOOK
        assert event.workflow_id == "wf_restored"
        assert event.scenario_id == "sc_restored"
        assert event.payload == {"data": "restored"}
        assert event.metadata == {"restored": True}
        assert event.priority == 3

    def test_event_from_dict_missing_optional_fields(self):
        """Test deserializing event with missing optional fields."""
        data = {
            "trigger_id": "minimal",
            "trigger_type": "manual",
            "workflow_id": "wf",
            "scenario_id": "sc"
        }
        event = TriggerEvent.from_dict(data)

        assert event.trigger_id == "minimal"
        assert event.payload == {}
        assert event.metadata == {}
        assert event.priority == 1

    def test_event_roundtrip_serialization(self):
        """Test that event survives serialization roundtrip."""
        original = TriggerEvent(
            trigger_id="roundtrip_test",
            trigger_type=TriggerType.EMAIL,
            workflow_id="wf_round",
            scenario_id="sc_round",
            payload={"nested": {"key": "value"}, "list": [1, 2, 3]},
            metadata={"test": True},
            priority=2
        )

        data = original.to_dict()
        restored = TriggerEvent.from_dict(data)

        assert restored.trigger_id == original.trigger_id
        assert restored.trigger_type == original.trigger_type
        assert restored.workflow_id == original.workflow_id
        assert restored.scenario_id == original.scenario_id
        assert restored.payload == original.payload
        assert restored.metadata == original.metadata
        assert restored.priority == original.priority


# =============================================================================
# BaseTriggerConfig Tests
# =============================================================================

class TestBaseTriggerConfig:
    """Tests for BaseTriggerConfig dataclass."""

    def test_create_basic_config(self):
        """Test creating a basic trigger configuration."""
        config = BaseTriggerConfig(
            id="config_001",
            name="Test Trigger",
            trigger_type=TriggerType.MANUAL,
            scenario_id="scenario_001",
            workflow_id="workflow_001"
        )
        assert config.id == "config_001"
        assert config.name == "Test Trigger"
        assert config.trigger_type == TriggerType.MANUAL
        assert config.enabled is True
        assert config.priority == 1
        assert config.cooldown_seconds == 0

    def test_config_auto_generates_id(self):
        """Test that config auto-generates ID if not provided."""
        config = BaseTriggerConfig(
            id="",
            name="Auto ID Test",
            trigger_type=TriggerType.SCHEDULED,
            scenario_id="sc",
            workflow_id="wf"
        )
        assert config.id.startswith("trig_")
        assert len(config.id) > 5

    def test_config_auto_generates_created_at(self):
        """Test that config auto-generates created_at timestamp."""
        config = BaseTriggerConfig(
            id="test",
            name="Timestamp Test",
            trigger_type=TriggerType.MANUAL,
            scenario_id="sc",
            workflow_id="wf"
        )
        assert config.created_at is not None
        assert isinstance(config.created_at, datetime)

    def test_config_with_all_options(self):
        """Test creating config with all options."""
        config = BaseTriggerConfig(
            id="full_config",
            name="Full Config Test",
            trigger_type=TriggerType.WEBHOOK,
            scenario_id="scenario",
            workflow_id="workflow",
            enabled=False,
            priority=3,
            cooldown_seconds=60,
            description="Test description",
            config={"endpoint": "/webhook", "method": "POST"}
        )
        assert config.enabled is False
        assert config.priority == 3
        assert config.cooldown_seconds == 60
        assert config.description == "Test description"
        assert config.config["endpoint"] == "/webhook"

    def test_config_tracking_fields(self):
        """Test trigger tracking fields."""
        config = BaseTriggerConfig(
            id="tracking_test",
            name="Tracking Test",
            trigger_type=TriggerType.MANUAL,
            scenario_id="sc",
            workflow_id="wf"
        )
        assert config.trigger_count == 0
        assert config.success_count == 0
        assert config.error_count == 0
        assert config.last_triggered is None

    def test_config_to_dict(self):
        """Test serializing config to dictionary."""
        config = BaseTriggerConfig(
            id="serialize_test",
            name="Serialize Test",
            trigger_type=TriggerType.FILE_WATCH,
            scenario_id="sc_001",
            workflow_id="wf_001",
            enabled=True,
            priority=2,
            cooldown_seconds=30,
            description="Test",
            config={"path": "/test"}
        )
        data = config.to_dict()

        assert data["id"] == "serialize_test"
        assert data["name"] == "Serialize Test"
        assert data["trigger_type"] == "file_watch"
        assert data["scenario_id"] == "sc_001"
        assert data["workflow_id"] == "wf_001"
        assert data["enabled"] is True
        assert data["priority"] == 2
        assert data["cooldown_seconds"] == 30
        assert data["description"] == "Test"
        assert data["config"]["path"] == "/test"

    def test_config_from_dict(self):
        """Test deserializing config from dictionary."""
        data = {
            "id": "restored_config",
            "name": "Restored",
            "trigger_type": "scheduled",
            "scenario_id": "sc",
            "workflow_id": "wf",
            "enabled": False,
            "priority": 3,
            "cooldown_seconds": 120,
            "description": "Restored description",
            "config": {"cron": "* * * * *"},
            "trigger_count": 10,
            "success_count": 8,
            "error_count": 2
        }
        config = BaseTriggerConfig.from_dict(data)

        assert config.id == "restored_config"
        assert config.name == "Restored"
        assert config.trigger_type == TriggerType.SCHEDULED
        assert config.enabled is False
        assert config.priority == 3
        assert config.cooldown_seconds == 120
        assert config.trigger_count == 10
        assert config.success_count == 8
        assert config.error_count == 2

    def test_config_roundtrip_serialization(self):
        """Test that config survives serialization roundtrip."""
        original = BaseTriggerConfig(
            id="roundtrip",
            name="Roundtrip Test",
            trigger_type=TriggerType.EMAIL,
            scenario_id="sc",
            workflow_id="wf",
            enabled=True,
            priority=2,
            cooldown_seconds=45,
            description="Round trip test",
            config={"server": "mail.test.com", "port": 993}
        )

        data = original.to_dict()
        restored = BaseTriggerConfig.from_dict(data)

        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.trigger_type == original.trigger_type
        assert restored.enabled == original.enabled
        assert restored.priority == original.priority
        assert restored.cooldown_seconds == original.cooldown_seconds
        assert restored.config == original.config


# =============================================================================
# BaseTrigger Tests (using a concrete implementation)
# =============================================================================

class ConcreteTrigger(BaseTrigger):
    """Concrete implementation for testing BaseTrigger."""

    trigger_type = TriggerType.MANUAL
    display_name = "Test Trigger"
    description = "Trigger for testing"
    icon = "test"
    category = "Testing"

    def __init__(self, config, event_callback=None):
        super().__init__(config, event_callback)
        self._start_called = False
        self._stop_called = False

    async def start(self) -> bool:
        self._start_called = True
        self._status = TriggerStatus.ACTIVE
        return True

    async def stop(self) -> bool:
        self._stop_called = True
        self._status = TriggerStatus.INACTIVE
        return True

    def validate_config(self):
        if not self.config.name:
            return False, "Name is required"
        return True, None


class TestBaseTrigger:
    """Tests for BaseTrigger abstract class functionality."""

    @pytest.fixture
    def trigger_config(self):
        """Create a basic trigger config for testing."""
        return BaseTriggerConfig(
            id="test_trigger_001",
            name="Test Trigger",
            trigger_type=TriggerType.MANUAL,
            scenario_id="scenario_001",
            workflow_id="workflow_001"
        )

    @pytest.fixture
    def trigger(self, trigger_config):
        """Create a concrete trigger instance."""
        return ConcreteTrigger(trigger_config)

    def test_trigger_initialization(self, trigger, trigger_config):
        """Test trigger initializes correctly."""
        assert trigger.config == trigger_config
        assert trigger.status == TriggerStatus.INACTIVE
        assert trigger.error_message is None

    def test_trigger_class_attributes(self, trigger):
        """Test trigger class-level attributes."""
        assert trigger.trigger_type == TriggerType.MANUAL
        assert trigger.display_name == "Test Trigger"
        assert trigger.description == "Trigger for testing"
        assert trigger.icon == "test"
        assert trigger.category == "Testing"

    @pytest.mark.asyncio
    async def test_trigger_start(self, trigger):
        """Test starting a trigger."""
        result = await trigger.start()
        assert result is True
        assert trigger._start_called is True
        assert trigger.status == TriggerStatus.ACTIVE
        assert trigger.is_active is True

    @pytest.mark.asyncio
    async def test_trigger_stop(self, trigger):
        """Test stopping a trigger."""
        await trigger.start()
        result = await trigger.stop()
        assert result is True
        assert trigger._stop_called is True
        assert trigger.status == TriggerStatus.INACTIVE
        assert trigger.is_active is False

    @pytest.mark.asyncio
    async def test_trigger_pause_resume(self, trigger):
        """Test pausing and resuming a trigger."""
        await trigger.start()

        result = await trigger.pause()
        assert result is True
        assert trigger.status == TriggerStatus.PAUSED

        result = await trigger.resume()
        assert result is True
        assert trigger.status == TriggerStatus.ACTIVE

    def test_trigger_validate_config_valid(self, trigger):
        """Test config validation with valid config."""
        is_valid, error = trigger.validate_config()
        assert is_valid is True
        assert error is None

    def test_trigger_validate_config_invalid(self, trigger_config):
        """Test config validation with invalid config."""
        trigger_config.name = ""
        trigger = ConcreteTrigger(trigger_config)
        is_valid, error = trigger.validate_config()
        assert is_valid is False
        assert "Name is required" in error

    @pytest.mark.asyncio
    async def test_trigger_emit_basic(self, trigger_config):
        """Test emitting a trigger event."""
        callback_received = []

        async def callback(event):
            callback_received.append(event)

        trigger = ConcreteTrigger(trigger_config, event_callback=callback)
        await trigger.start()

        result = await trigger.emit({"test": "data"})

        assert result is True
        assert len(callback_received) == 1
        assert callback_received[0].payload == {"test": "data"}
        assert trigger.config.trigger_count == 1
        assert trigger.config.success_count == 1
        assert trigger.config.last_triggered is not None

    @pytest.mark.asyncio
    async def test_trigger_emit_with_metadata(self, trigger_config):
        """Test emitting event with metadata."""
        events = []

        async def callback(event):
            events.append(event)

        trigger = ConcreteTrigger(trigger_config, event_callback=callback)
        await trigger.start()

        await trigger.emit({"data": "test"}, metadata={"source": "unit_test"})

        assert events[0].metadata["source"] == "unit_test"

    @pytest.mark.asyncio
    async def test_trigger_emit_cooldown(self, trigger_config):
        """Test trigger cooldown blocks rapid firing."""
        trigger_config.cooldown_seconds = 60  # 60 second cooldown
        callback_count = 0

        async def callback(event):
            nonlocal callback_count
            callback_count += 1

        trigger = ConcreteTrigger(trigger_config, event_callback=callback)
        await trigger.start()

        # First emit should succeed
        result1 = await trigger.emit({"first": True})
        assert result1 is True
        assert callback_count == 1

        # Second emit should be blocked by cooldown
        result2 = await trigger.emit({"second": True})
        assert result2 is False
        assert callback_count == 1  # Still 1

    @pytest.mark.asyncio
    async def test_trigger_emit_callback_error(self, trigger_config):
        """Test that callback errors are handled gracefully."""
        async def failing_callback(event):
            raise RuntimeError("Callback failed!")

        trigger = ConcreteTrigger(trigger_config, event_callback=failing_callback)
        await trigger.start()

        result = await trigger.emit({"test": "data"})

        assert result is False
        assert trigger.config.error_count == 1
        assert trigger.error_message == "Callback failed!"

    @pytest.mark.asyncio
    async def test_trigger_emit_no_callback(self, trigger_config):
        """Test emitting without a callback still tracks counts."""
        trigger = ConcreteTrigger(trigger_config, event_callback=None)
        await trigger.start()

        result = await trigger.emit({"test": "data"})

        assert result is True
        assert trigger.config.trigger_count == 1

    def test_trigger_get_info(self, trigger):
        """Test getting trigger information."""
        info = trigger.get_info()

        assert info["id"] == "test_trigger_001"
        assert info["name"] == "Test Trigger"
        assert info["type"] == "manual"
        assert info["display_name"] == "Test Trigger"
        assert info["description"] == "Trigger for testing"
        assert info["icon"] == "test"
        assert info["category"] == "Testing"
        assert info["status"] == "inactive"
        assert info["enabled"] is True

    def test_trigger_get_config_schema(self):
        """Test getting configuration schema."""
        schema = ConcreteTrigger.get_config_schema()

        assert schema["type"] == "object"
        assert "properties" in schema
        assert "name" in schema["properties"]
        assert "enabled" in schema["properties"]
        assert "priority" in schema["properties"]

    def test_trigger_get_display_info(self):
        """Test getting display information."""
        info = ConcreteTrigger.get_display_info()

        assert info["type"] == "manual"
        assert info["display_name"] == "Test Trigger"
        assert info["description"] == "Trigger for testing"
        assert info["icon"] == "test"
        assert info["category"] == "Testing"

    def test_trigger_repr(self, trigger):
        """Test trigger string representation."""
        repr_str = repr(trigger)
        assert "ConcreteTrigger" in repr_str
        assert "Test Trigger" in repr_str
        assert "manual" in repr_str
        assert "inactive" in repr_str


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================

class TestTriggerEdgeCases:
    """Edge case and error handling tests."""

    @pytest.mark.asyncio
    async def test_multiple_rapid_emits(self):
        """Test rapid succession of emit calls."""
        config = BaseTriggerConfig(
            id="rapid_test",
            name="Rapid Test",
            trigger_type=TriggerType.MANUAL,
            scenario_id="sc",
            workflow_id="wf",
            cooldown_seconds=0  # No cooldown
        )

        emit_count = 0
        async def callback(event):
            nonlocal emit_count
            emit_count += 1

        trigger = ConcreteTrigger(config, event_callback=callback)
        await trigger.start()

        # Emit 100 times rapidly
        for i in range(100):
            await trigger.emit({"iteration": i})

        assert emit_count == 100
        assert trigger.config.trigger_count == 100

    @pytest.mark.asyncio
    async def test_emit_with_large_payload(self):
        """Test emitting with large payload."""
        config = BaseTriggerConfig(
            id="large_payload",
            name="Large Payload Test",
            trigger_type=TriggerType.MANUAL,
            scenario_id="sc",
            workflow_id="wf"
        )

        received_payload = None
        async def callback(event):
            nonlocal received_payload
            received_payload = event.payload

        trigger = ConcreteTrigger(config, event_callback=callback)
        await trigger.start()

        # Create large payload
        large_payload = {
            "data": "x" * 10000,
            "nested": {"list": list(range(1000))}
        }

        await trigger.emit(large_payload)

        assert received_payload == large_payload

    def test_config_with_special_characters_in_name(self):
        """Test config with special characters in name."""
        config = BaseTriggerConfig(
            id="special_chars",
            name="Test <>&\"' Trigger!@#$%",
            trigger_type=TriggerType.MANUAL,
            scenario_id="sc",
            workflow_id="wf"
        )

        data = config.to_dict()
        restored = BaseTriggerConfig.from_dict(data)

        assert restored.name == "Test <>&\"' Trigger!@#$%"

    def test_config_with_unicode_values(self):
        """Test config with unicode values."""
        config = BaseTriggerConfig(
            id="unicode_test",
            name="テスト トリガー 测试",
            trigger_type=TriggerType.MANUAL,
            scenario_id="sc",
            workflow_id="wf",
            description="Unicode: 日本語 中文 한국어"
        )

        data = config.to_dict()
        restored = BaseTriggerConfig.from_dict(data)

        assert restored.name == "テスト トリガー 测试"
        assert restored.description == "Unicode: 日本語 中文 한국어"

    @pytest.mark.asyncio
    async def test_sync_callback_in_emit(self):
        """Test that sync callbacks work in emit."""
        config = BaseTriggerConfig(
            id="sync_callback",
            name="Sync Callback Test",
            trigger_type=TriggerType.MANUAL,
            scenario_id="sc",
            workflow_id="wf"
        )

        callback_called = False
        def sync_callback(event):
            nonlocal callback_called
            callback_called = True

        trigger = ConcreteTrigger(config, event_callback=sync_callback)
        await trigger.start()
        await trigger.emit({"test": True})

        assert callback_called is True
