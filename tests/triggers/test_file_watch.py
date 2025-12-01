"""Tests for file watch trigger module."""

import pytest
from typing import Optional

from casare_rpa.triggers.base import BaseTriggerConfig, TriggerType
from casare_rpa.triggers.implementations.file_watch import FileWatchTrigger


@pytest.fixture
def make_file_watch_config():
    """Factory fixture to create file watch trigger configs."""

    def _make_config(
        config: dict,
        name: str = "Test File Watch Trigger",
        trigger_id: str = "trig_fw_test",
    ) -> BaseTriggerConfig:
        return BaseTriggerConfig(
            id=trigger_id,
            name=name,
            trigger_type=TriggerType.FILE_WATCH,
            scenario_id="scen_123",
            workflow_id="wf_456",
            config=config,
        )

    return _make_config


class TestFileWatchTriggerMetadata:
    """Tests for FileWatchTrigger class metadata."""

    def test_trigger_type(self):
        """Test trigger type is file_watch."""
        assert FileWatchTrigger.trigger_type == TriggerType.FILE_WATCH

    def test_display_name(self):
        """Test display name."""
        assert FileWatchTrigger.display_name == "File Watch"

    def test_description(self):
        """Test description."""
        assert "files change" in FileWatchTrigger.description.lower()

    def test_category(self):
        """Test category."""
        assert FileWatchTrigger.category == "Local"


class TestFileWatchTriggerValidation:
    """Tests for file watch trigger configuration validation."""

    def test_valid_basic_config(self, make_file_watch_config, tmp_path):
        """Test valid basic file watch config."""
        config = make_file_watch_config(
            {
                "watch_path": str(tmp_path),
            }
        )
        trigger = FileWatchTrigger(config)

        valid, error = trigger.validate_config()

        assert valid is True
        assert error is None

    def test_valid_full_config(self, make_file_watch_config, tmp_path):
        """Test valid full file watch config."""
        config = make_file_watch_config(
            {
                "watch_path": str(tmp_path),
                "patterns": ["*.pdf", "*.csv"],
                "recursive": True,
                "events": ["created", "modified"],
                "debounce_ms": 500,
            }
        )
        trigger = FileWatchTrigger(config)

        valid, error = trigger.validate_config()

        assert valid is True
        assert error is None

    def test_missing_watch_path(self, make_file_watch_config):
        """Test missing watch_path."""
        config = make_file_watch_config({})
        trigger = FileWatchTrigger(config)

        valid, error = trigger.validate_config()

        assert valid is False
        assert "watch_path is required" in error

    def test_empty_watch_path(self, make_file_watch_config):
        """Test empty watch_path."""
        config = make_file_watch_config(
            {
                "watch_path": "",
            }
        )
        trigger = FileWatchTrigger(config)

        valid, error = trigger.validate_config()

        assert valid is False
        assert "watch_path is required" in error

    def test_invalid_event_type(self, make_file_watch_config, tmp_path):
        """Test invalid event type."""
        config = make_file_watch_config(
            {
                "watch_path": str(tmp_path),
                "events": ["created", "invalid_event"],
            }
        )
        trigger = FileWatchTrigger(config)

        valid, error = trigger.validate_config()

        assert valid is False
        assert "Invalid event type" in error

    def test_all_valid_event_types(self, make_file_watch_config, tmp_path):
        """Test all valid event types."""
        config = make_file_watch_config(
            {
                "watch_path": str(tmp_path),
                "events": ["created", "modified", "deleted", "moved"],
            }
        )
        trigger = FileWatchTrigger(config)

        valid, error = trigger.validate_config()

        assert valid is True
        assert error is None

    def test_negative_debounce(self, make_file_watch_config, tmp_path):
        """Test negative debounce_ms."""
        config = make_file_watch_config(
            {
                "watch_path": str(tmp_path),
                "debounce_ms": -100,
            }
        )
        trigger = FileWatchTrigger(config)

        valid, error = trigger.validate_config()

        assert valid is False
        assert "debounce_ms must be >= 0" in error

    def test_zero_debounce_valid(self, make_file_watch_config, tmp_path):
        """Test zero debounce_ms is valid."""
        config = make_file_watch_config(
            {
                "watch_path": str(tmp_path),
                "debounce_ms": 0,
            }
        )
        trigger = FileWatchTrigger(config)

        valid, error = trigger.validate_config()

        assert valid is True
        assert error is None


class TestFileWatchTriggerConfigSchema:
    """Tests for file watch trigger config schema."""

    def test_schema_has_required_properties(self):
        """Test schema contains required properties."""
        schema = FileWatchTrigger.get_config_schema()

        assert schema["type"] == "object"
        assert "properties" in schema
        assert "name" in schema["properties"]
        assert "watch_path" in schema["properties"]
        assert "patterns" in schema["properties"]
        assert "recursive" in schema["properties"]
        assert "events" in schema["properties"]
        assert "debounce_ms" in schema["properties"]

    def test_schema_events_enum(self):
        """Test schema has events enum values."""
        schema = FileWatchTrigger.get_config_schema()
        events_schema = schema["properties"]["events"]["items"]

        assert "enum" in events_schema
        expected = ["created", "modified", "deleted", "moved"]
        assert events_schema["enum"] == expected

    def test_schema_patterns_is_array(self):
        """Test schema patterns is array type."""
        schema = FileWatchTrigger.get_config_schema()
        patterns_schema = schema["properties"]["patterns"]

        assert patterns_schema["type"] == "array"
        assert patterns_schema["items"]["type"] == "string"

    def test_schema_recursive_default(self):
        """Test schema recursive default is False."""
        schema = FileWatchTrigger.get_config_schema()
        recursive_schema = schema["properties"]["recursive"]

        assert recursive_schema["type"] == "boolean"
        assert recursive_schema["default"] is False

    def test_schema_debounce_bounds(self):
        """Test schema debounce_ms bounds."""
        schema = FileWatchTrigger.get_config_schema()
        debounce_schema = schema["properties"]["debounce_ms"]

        assert debounce_schema["type"] == "integer"
        assert debounce_schema["minimum"] == 0
        assert debounce_schema["default"] == 1000

    def test_schema_required_fields(self):
        """Test schema required fields."""
        schema = FileWatchTrigger.get_config_schema()

        assert "required" in schema
        assert "name" in schema["required"]
        assert "watch_path" in schema["required"]


class TestFileWatchTriggerInit:
    """Tests for FileWatchTrigger initialization."""

    def test_initialization(self, make_file_watch_config, tmp_path):
        """Test trigger initialization."""
        config = make_file_watch_config({"watch_path": str(tmp_path)})
        trigger = FileWatchTrigger(config)

        assert trigger.config == config
        assert trigger._observer is None
        assert trigger._handler is None
        assert trigger._pending_events == {}


class TestFileWatchTriggerStartErrors:
    """Tests for FileWatchTrigger start errors."""

    @pytest.mark.asyncio
    async def test_start_missing_path_fails(self, make_file_watch_config):
        """Test start fails with missing watch_path."""
        config = make_file_watch_config({"watch_path": ""})
        trigger = FileWatchTrigger(config)

        result = await trigger.start()

        assert result is False
        assert trigger.error_message == "watch_path is required"

    @pytest.mark.asyncio
    async def test_start_nonexistent_path_fails(self, make_file_watch_config):
        """Test start fails with nonexistent path."""
        config = make_file_watch_config(
            {"watch_path": "/nonexistent/path/that/does/not/exist"}
        )
        trigger = FileWatchTrigger(config)

        result = await trigger.start()

        assert result is False
        assert "does not exist" in trigger.error_message

    @pytest.mark.asyncio
    async def test_start_file_instead_of_dir_fails(
        self, make_file_watch_config, tmp_path
    ):
        """Test start fails when path is a file not directory."""
        # Create a file instead of directory
        file_path = tmp_path / "not_a_dir.txt"
        file_path.write_text("content")

        config = make_file_watch_config({"watch_path": str(file_path)})
        trigger = FileWatchTrigger(config)

        result = await trigger.start()

        assert result is False
        assert "not a directory" in trigger.error_message
