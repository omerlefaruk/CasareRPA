"""Tests for trigger base classes."""

from datetime import datetime, timedelta
import pytest

from casare_rpa.triggers.base import (
    TriggerEvent,
    BaseTriggerConfig,
)
from casare_rpa.domain.value_objects.trigger_types import (
    TriggerType,
    TriggerStatus,
    TriggerPriority,
)


class TestTriggerType:
    """Tests for TriggerType enum."""

    def test_enum_values(self):
        """Test that enum values are correct."""
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

    def test_all_types_present(self):
        """Test that all expected trigger types exist."""
        types = [t.value for t in TriggerType]
        # 10 original + RSS_FEED + SSE + TELEGRAM + WHATSAPP + GMAIL + SHEETS + DRIVE + CALENDAR
        assert len(types) == 18


class TestTriggerStatus:
    """Tests for TriggerStatus enum."""

    def test_enum_values(self):
        """Test that enum values are correct."""
        assert TriggerStatus.INACTIVE.value == "inactive"
        assert TriggerStatus.STARTING.value == "starting"
        assert TriggerStatus.ACTIVE.value == "active"
        assert TriggerStatus.PAUSED.value == "paused"
        assert TriggerStatus.STOPPING.value == "stopping"
        assert TriggerStatus.ERROR.value == "error"


class TestTriggerPriority:
    """Tests for TriggerPriority enum."""

    def test_enum_values(self):
        """Test that priority values are correct."""
        assert TriggerPriority.LOW.value == 0
        assert TriggerPriority.NORMAL.value == 1
        assert TriggerPriority.HIGH.value == 2
        assert TriggerPriority.CRITICAL.value == 3


class TestTriggerEvent:
    """Tests for TriggerEvent dataclass."""

    def test_default_values(self):
        """Test default values for TriggerEvent."""
        event = TriggerEvent(
            trigger_id="trig_123",
            trigger_type=TriggerType.MANUAL,
            workflow_id="wf_456",
            scenario_id="scen_789",
        )
        assert event.trigger_id == "trig_123"
        assert event.trigger_type == TriggerType.MANUAL
        assert event.workflow_id == "wf_456"
        assert event.scenario_id == "scen_789"
        assert isinstance(event.timestamp, datetime)
        assert event.payload == {}
        assert event.metadata == {}
        assert event.priority == 1

    def test_with_custom_values(self):
        """Test TriggerEvent with custom values."""
        timestamp = datetime(2024, 1, 15, 10, 30, 0)
        payload = {"key": "value"}
        metadata = {"source": "test"}

        event = TriggerEvent(
            trigger_id="trig_123",
            trigger_type=TriggerType.SCHEDULED,
            workflow_id="wf_456",
            scenario_id="scen_789",
            timestamp=timestamp,
            payload=payload,
            metadata=metadata,
            priority=2,
        )

        assert event.timestamp == timestamp
        assert event.payload == payload
        assert event.metadata == metadata
        assert event.priority == 2

    def test_to_dict(self):
        """Test serialization to dictionary."""
        timestamp = datetime(2024, 1, 15, 10, 30, 0)
        event = TriggerEvent(
            trigger_id="trig_123",
            trigger_type=TriggerType.FILE_WATCH,
            workflow_id="wf_456",
            scenario_id="scen_789",
            timestamp=timestamp,
            payload={"file": "test.csv"},
            metadata={"path": "/data"},
            priority=3,
        )

        data = event.to_dict()

        assert data["trigger_id"] == "trig_123"
        assert data["trigger_type"] == "file_watch"
        assert data["workflow_id"] == "wf_456"
        assert data["scenario_id"] == "scen_789"
        assert data["timestamp"] == "2024-01-15T10:30:00"
        assert data["payload"] == {"file": "test.csv"}
        assert data["metadata"] == {"path": "/data"}
        assert data["priority"] == 3

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "trigger_id": "trig_abc",
            "trigger_type": "webhook",
            "workflow_id": "wf_def",
            "scenario_id": "scen_ghi",
            "timestamp": "2024-02-20T15:45:30",
            "payload": {"request": "data"},
            "metadata": {"ip": "127.0.0.1"},
            "priority": 2,
        }

        event = TriggerEvent.from_dict(data)

        assert event.trigger_id == "trig_abc"
        assert event.trigger_type == TriggerType.WEBHOOK
        assert event.workflow_id == "wf_def"
        assert event.scenario_id == "scen_ghi"
        assert event.timestamp == datetime(2024, 2, 20, 15, 45, 30)
        assert event.payload == {"request": "data"}
        assert event.metadata == {"ip": "127.0.0.1"}
        assert event.priority == 2

    def test_from_dict_with_defaults(self):
        """Test deserialization with missing fields uses defaults."""
        data = {
            "trigger_type": "manual",
        }

        event = TriggerEvent.from_dict(data)

        assert event.trigger_id == ""
        assert event.workflow_id == ""
        assert event.scenario_id == ""
        assert event.payload == {}
        assert event.metadata == {}
        assert event.priority == 1


class TestBaseTriggerConfig:
    """Tests for BaseTriggerConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = BaseTriggerConfig(
            id="trig_123",
            name="Test Trigger",
            trigger_type=TriggerType.MANUAL,
            scenario_id="scen_456",
            workflow_id="wf_789",
        )

        assert config.enabled is True
        assert config.priority == 1
        assert config.cooldown_seconds == 0
        assert config.description == ""
        assert config.config == {}
        assert config.trigger_count == 0
        assert config.success_count == 0
        assert config.error_count == 0
        assert config.last_triggered is None
        assert config.created_at is not None

    def test_auto_generated_id(self):
        """Test that ID is auto-generated if empty."""
        config = BaseTriggerConfig(
            id="",
            name="Auto ID Trigger",
            trigger_type=TriggerType.SCHEDULED,
            scenario_id="scen_123",
            workflow_id="wf_456",
        )

        assert config.id.startswith("trig_")
        assert len(config.id) == 13  # "trig_" + 8 hex chars

    def test_custom_config(self):
        """Test with custom configuration values."""
        custom_config = {"frequency": "daily", "time_hour": 9}
        config = BaseTriggerConfig(
            id="trig_custom",
            name="Custom Trigger",
            trigger_type=TriggerType.SCHEDULED,
            scenario_id="scen_123",
            workflow_id="wf_456",
            enabled=False,
            priority=3,
            cooldown_seconds=60,
            description="A custom scheduled trigger",
            config=custom_config,
        )

        assert config.enabled is False
        assert config.priority == 3
        assert config.cooldown_seconds == 60
        assert config.description == "A custom scheduled trigger"
        assert config.config == custom_config

    def test_to_dict(self):
        """Test serialization to dictionary."""
        created = datetime(2024, 1, 1, 12, 0, 0)
        last_triggered = datetime(2024, 1, 15, 10, 30, 0)

        config = BaseTriggerConfig(
            id="trig_serial",
            name="Serial Test",
            trigger_type=TriggerType.FILE_WATCH,
            scenario_id="scen_abc",
            workflow_id="wf_def",
            priority=2,
            config={"watch_path": "/data"},
            created_at=created,
            last_triggered=last_triggered,
            trigger_count=5,
            success_count=4,
            error_count=1,
        )

        data = config.to_dict()

        assert data["id"] == "trig_serial"
        assert data["name"] == "Serial Test"
        assert data["trigger_type"] == "file_watch"
        assert data["scenario_id"] == "scen_abc"
        assert data["workflow_id"] == "wf_def"
        assert data["priority"] == 2
        assert data["config"] == {"watch_path": "/data"}
        assert data["created_at"] == "2024-01-01T12:00:00"
        assert data["last_triggered"] == "2024-01-15T10:30:00"
        assert data["trigger_count"] == 5
        assert data["success_count"] == 4
        assert data["error_count"] == 1

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "id": "trig_from_dict",
            "name": "From Dict Trigger",
            "trigger_type": "webhook",
            "scenario_id": "scen_xyz",
            "workflow_id": "wf_xyz",
            "enabled": False,
            "priority": 3,
            "cooldown_seconds": 30,
            "description": "Loaded from dict",
            "config": {"endpoint": "/hook"},
            "created_at": "2024-03-01T00:00:00",
            "last_triggered": "2024-03-15T12:00:00",
            "trigger_count": 10,
            "success_count": 8,
            "error_count": 2,
        }

        config = BaseTriggerConfig.from_dict(data)

        assert config.id == "trig_from_dict"
        assert config.name == "From Dict Trigger"
        assert config.trigger_type == TriggerType.WEBHOOK
        assert config.enabled is False
        assert config.priority == 3
        assert config.cooldown_seconds == 30
        assert config.description == "Loaded from dict"
        assert config.config == {"endpoint": "/hook"}
        assert config.created_at == datetime(2024, 3, 1, 0, 0, 0)
        assert config.last_triggered == datetime(2024, 3, 15, 12, 0, 0)
        assert config.trigger_count == 10
        assert config.success_count == 8
        assert config.error_count == 2

    def test_from_dict_with_defaults(self):
        """Test deserialization with missing fields uses defaults."""
        data = {
            "trigger_type": "manual",
        }

        config = BaseTriggerConfig.from_dict(data)

        assert config.name == "Untitled Trigger"
        assert config.enabled is True
        assert config.priority == 1
        assert config.cooldown_seconds == 0
        assert config.config == {}
