"""Tests for trigger implementations."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

from casare_rpa.triggers.base import BaseTriggerConfig, TriggerType, TriggerStatus


# ==================== WebhookTrigger Tests ====================


class TestWebhookTrigger:
    """Tests for WebhookTrigger implementation."""

    @pytest.fixture
    def webhook_config(self):
        """Create webhook trigger config."""
        return BaseTriggerConfig(
            id="webhook_1",
            name="Test Webhook",
            trigger_type=TriggerType.WEBHOOK,
            scenario_id="scenario_1",
            workflow_id="workflow_1",
            config={
                "endpoint": "/webhooks/test",
                "auth_type": "none",
                "methods": ["POST"],
            },
        )

    def test_webhook_trigger_import(self):
        """Test that WebhookTrigger can be imported."""
        from casare_rpa.triggers.implementations.webhook import WebhookTrigger

        assert WebhookTrigger.trigger_type == TriggerType.WEBHOOK

    def test_validate_config_valid(self, webhook_config):
        """Test valid webhook configuration."""
        from casare_rpa.triggers.implementations.webhook import WebhookTrigger

        trigger = WebhookTrigger(webhook_config)
        is_valid, error = trigger.validate_config()

        assert is_valid is True
        assert error is None

    def test_validate_config_invalid_endpoint(self, webhook_config):
        """Test invalid endpoint (missing /)."""
        from casare_rpa.triggers.implementations.webhook import WebhookTrigger

        webhook_config.config["endpoint"] = "webhooks/test"  # Missing /
        trigger = WebhookTrigger(webhook_config)
        is_valid, error = trigger.validate_config()

        assert is_valid is False
        assert "start with '/'" in error

    def test_validate_config_invalid_auth_type(self, webhook_config):
        """Test invalid auth type."""
        from casare_rpa.triggers.implementations.webhook import WebhookTrigger

        webhook_config.config["auth_type"] = "oauth2"  # Not supported
        trigger = WebhookTrigger(webhook_config)
        is_valid, error = trigger.validate_config()

        assert is_valid is False
        assert "Invalid auth_type" in error

    def test_validate_config_missing_secret_for_api_key(self, webhook_config):
        """Test that secret is required for api_key auth."""
        from casare_rpa.triggers.implementations.webhook import WebhookTrigger

        webhook_config.config["auth_type"] = "api_key"
        # No secret provided
        trigger = WebhookTrigger(webhook_config)
        is_valid, error = trigger.validate_config()

        assert is_valid is False
        assert "Secret is required" in error

    def test_validate_config_with_hmac_auth(self, webhook_config):
        """Test HMAC auth type validation."""
        from casare_rpa.triggers.implementations.webhook import WebhookTrigger

        webhook_config.config["auth_type"] = "hmac_sha256"
        webhook_config.config["secret"] = "my-secret-key"
        trigger = WebhookTrigger(webhook_config)
        is_valid, error = trigger.validate_config()

        assert is_valid is True
        assert error is None

    def test_validate_config_invalid_method(self, webhook_config):
        """Test invalid HTTP method."""
        from casare_rpa.triggers.implementations.webhook import WebhookTrigger

        webhook_config.config["methods"] = ["POST", "INVALID"]
        trigger = WebhookTrigger(webhook_config)
        is_valid, error = trigger.validate_config()

        assert is_valid is False
        assert "Invalid HTTP method" in error

    @pytest.mark.asyncio
    async def test_start_sets_active_status(self, webhook_config):
        """Test that start() sets status to ACTIVE."""
        from casare_rpa.triggers.implementations.webhook import WebhookTrigger

        trigger = WebhookTrigger(webhook_config)
        result = await trigger.start()

        assert result is True
        assert trigger.status == TriggerStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_stop_sets_inactive_status(self, webhook_config):
        """Test that stop() sets status to INACTIVE."""
        from casare_rpa.triggers.implementations.webhook import WebhookTrigger

        trigger = WebhookTrigger(webhook_config)
        await trigger.start()
        result = await trigger.stop()

        assert result is True
        assert trigger.status == TriggerStatus.INACTIVE


# ==================== ScheduledTrigger Tests ====================


class TestScheduledTrigger:
    """Tests for ScheduledTrigger implementation."""

    @pytest.fixture
    def scheduled_config(self):
        """Create scheduled trigger config."""
        return BaseTriggerConfig(
            id="scheduled_1",
            name="Daily Schedule",
            trigger_type=TriggerType.SCHEDULED,
            scenario_id="scenario_1",
            workflow_id="workflow_1",
            config={
                "frequency": "daily",
                "time_hour": 9,
                "time_minute": 30,
                "timezone": "UTC",
            },
        )

    def test_scheduled_trigger_import(self):
        """Test that ScheduledTrigger can be imported."""
        from casare_rpa.triggers.implementations.scheduled import ScheduledTrigger

        assert ScheduledTrigger.trigger_type == TriggerType.SCHEDULED

    def test_validate_config_daily(self, scheduled_config):
        """Test valid daily configuration."""
        from casare_rpa.triggers.implementations.scheduled import ScheduledTrigger

        trigger = ScheduledTrigger(scheduled_config)
        is_valid, error = trigger.validate_config()

        assert is_valid is True
        assert error is None

    def test_validate_config_invalid_frequency(self, scheduled_config):
        """Test invalid frequency."""
        from casare_rpa.triggers.implementations.scheduled import ScheduledTrigger

        scheduled_config.config["frequency"] = "every_5_minutes"  # Invalid
        trigger = ScheduledTrigger(scheduled_config)
        is_valid, error = trigger.validate_config()

        assert is_valid is False
        assert "Invalid frequency" in error

    def test_validate_config_invalid_hour(self, scheduled_config):
        """Test invalid hour value."""
        from casare_rpa.triggers.implementations.scheduled import ScheduledTrigger

        scheduled_config.config["time_hour"] = 25  # Invalid
        trigger = ScheduledTrigger(scheduled_config)
        is_valid, error = trigger.validate_config()

        assert is_valid is False
        assert "time_hour" in error

    def test_validate_config_invalid_minute(self, scheduled_config):
        """Test invalid minute value."""
        from casare_rpa.triggers.implementations.scheduled import ScheduledTrigger

        scheduled_config.config["time_minute"] = 60  # Invalid
        trigger = ScheduledTrigger(scheduled_config)
        is_valid, error = trigger.validate_config()

        assert is_valid is False
        assert "time_minute" in error

    def test_validate_config_cron_missing_expression(self, scheduled_config):
        """Test cron frequency without expression."""
        from casare_rpa.triggers.implementations.scheduled import ScheduledTrigger

        scheduled_config.config["frequency"] = "cron"
        scheduled_config.config["cron_expression"] = ""  # Missing
        trigger = ScheduledTrigger(scheduled_config)
        is_valid, error = trigger.validate_config()

        assert is_valid is False
        assert "cron_expression is required" in error

    def test_validate_config_cron_valid(self, scheduled_config):
        """Test valid cron configuration."""
        from casare_rpa.triggers.implementations.scheduled import ScheduledTrigger

        scheduled_config.config["frequency"] = "cron"
        scheduled_config.config["cron_expression"] = "0 9 * * *"
        trigger = ScheduledTrigger(scheduled_config)
        is_valid, error = trigger.validate_config()

        assert is_valid is True

    def test_validate_config_interval(self, scheduled_config):
        """Test valid interval configuration."""
        from casare_rpa.triggers.implementations.scheduled import ScheduledTrigger

        scheduled_config.config["frequency"] = "interval"
        scheduled_config.config["interval_seconds"] = 300
        trigger = ScheduledTrigger(scheduled_config)
        is_valid, error = trigger.validate_config()

        assert is_valid is True

    def test_validate_config_weekly_invalid_day(self, scheduled_config):
        """Test invalid day_of_week for weekly schedule."""
        from casare_rpa.triggers.implementations.scheduled import ScheduledTrigger

        scheduled_config.config["frequency"] = "weekly"
        scheduled_config.config["day_of_week"] = 7  # Invalid (0-6)
        trigger = ScheduledTrigger(scheduled_config)
        is_valid, error = trigger.validate_config()

        assert is_valid is False
        assert "day_of_week" in error

    def test_validate_config_monthly_invalid_day(self, scheduled_config):
        """Test invalid day_of_month for monthly schedule."""
        from casare_rpa.triggers.implementations.scheduled import ScheduledTrigger

        scheduled_config.config["frequency"] = "monthly"
        scheduled_config.config["day_of_month"] = 32  # Invalid (1-31)
        trigger = ScheduledTrigger(scheduled_config)
        is_valid, error = trigger.validate_config()

        assert is_valid is False
        assert "day_of_month" in error


# ==================== FileWatchTrigger Tests ====================


class TestFileWatchTrigger:
    """Tests for FileWatchTrigger implementation."""

    @pytest.fixture
    def file_watch_config(self):
        """Create file watch trigger config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield BaseTriggerConfig(
                id="file_watch_1",
                name="File Monitor",
                trigger_type=TriggerType.FILE_WATCH,
                scenario_id="scenario_1",
                workflow_id="workflow_1",
                config={
                    "watch_path": tmpdir,
                    "patterns": ["*.csv", "*.txt"],
                    "events": ["created", "modified"],
                    "recursive": False,
                    "debounce_ms": 500,
                },
            )

    def test_file_watch_trigger_import(self):
        """Test that FileWatchTrigger can be imported."""
        from casare_rpa.triggers.implementations.file_watch import FileWatchTrigger

        assert FileWatchTrigger.trigger_type == TriggerType.FILE_WATCH

    def test_validate_config_valid(self, file_watch_config):
        """Test valid file watch configuration."""
        from casare_rpa.triggers.implementations.file_watch import FileWatchTrigger

        trigger = FileWatchTrigger(file_watch_config)
        is_valid, error = trigger.validate_config()

        assert is_valid is True
        assert error is None

    def test_validate_config_missing_watch_path(self, file_watch_config):
        """Test missing watch_path."""
        from casare_rpa.triggers.implementations.file_watch import FileWatchTrigger

        file_watch_config.config["watch_path"] = ""
        trigger = FileWatchTrigger(file_watch_config)
        is_valid, error = trigger.validate_config()

        assert is_valid is False
        assert "watch_path is required" in error

    def test_validate_config_invalid_event_type(self, file_watch_config):
        """Test invalid event type."""
        from casare_rpa.triggers.implementations.file_watch import FileWatchTrigger

        file_watch_config.config["events"] = ["created", "renamed"]  # 'renamed' invalid
        trigger = FileWatchTrigger(file_watch_config)
        is_valid, error = trigger.validate_config()

        assert is_valid is False
        assert "Invalid event type" in error

    def test_validate_config_negative_debounce(self, file_watch_config):
        """Test negative debounce value."""
        from casare_rpa.triggers.implementations.file_watch import FileWatchTrigger

        file_watch_config.config["debounce_ms"] = -100
        trigger = FileWatchTrigger(file_watch_config)
        is_valid, error = trigger.validate_config()

        assert is_valid is False
        assert "debounce_ms" in error


# ==================== Trigger Registry Tests ====================


class TestTriggerRegistry:
    """Tests for trigger registry."""

    def test_registry_has_all_triggers(self):
        """Test that registry contains all expected triggers."""
        from casare_rpa.triggers.registry import get_trigger_registry

        registry = get_trigger_registry()
        trigger_types = registry.get_all()

        # Should have all main trigger types registered
        expected_types = [
            TriggerType.WEBHOOK,
            TriggerType.SCHEDULED,
            TriggerType.FILE_WATCH,
        ]

        for expected in expected_types:
            assert expected in trigger_types, f"Missing trigger type: {expected}"

    def test_create_webhook_instance(self):
        """Test creating webhook instance from registry."""
        from casare_rpa.triggers.registry import get_trigger_registry
        from casare_rpa.triggers.implementations.webhook import WebhookTrigger

        registry = get_trigger_registry()
        config = BaseTriggerConfig(
            id="test_webhook",
            name="Test",
            trigger_type=TriggerType.WEBHOOK,
            scenario_id="s1",
            workflow_id="w1",
        )

        trigger = registry.create_instance(TriggerType.WEBHOOK, config, None)

        assert isinstance(trigger, WebhookTrigger)
        assert trigger.config.id == "test_webhook"

    def test_create_scheduled_instance(self):
        """Test creating scheduled instance from registry."""
        from casare_rpa.triggers.registry import get_trigger_registry
        from casare_rpa.triggers.implementations.scheduled import ScheduledTrigger

        registry = get_trigger_registry()
        config = BaseTriggerConfig(
            id="test_scheduled",
            name="Test",
            trigger_type=TriggerType.SCHEDULED,
            scenario_id="s1",
            workflow_id="w1",
        )

        trigger = registry.create_instance(TriggerType.SCHEDULED, config, None)

        assert isinstance(trigger, ScheduledTrigger)


# ==================== BaseTrigger Tests ====================


class TestBaseTrigger:
    """Tests for BaseTrigger base class functionality."""

    @pytest.fixture
    def webhook_trigger(self):
        """Create a webhook trigger for testing base class functionality."""
        from casare_rpa.triggers.implementations.webhook import WebhookTrigger

        config = BaseTriggerConfig(
            id="base_test",
            name="Base Test",
            trigger_type=TriggerType.WEBHOOK,
            scenario_id="scenario_1",
            workflow_id="workflow_1",
            config={"auth_type": "none"},
            cooldown_seconds=10,
        )
        return WebhookTrigger(config)

    @pytest.mark.asyncio
    async def test_emit_calls_callback(self, webhook_trigger):
        """Test that emit() calls the event callback."""
        callback = AsyncMock()
        webhook_trigger._event_callback = callback

        await webhook_trigger.start()
        result = await webhook_trigger.emit({"data": "test"})

        assert result is True
        callback.assert_called_once()
        # Verify TriggerEvent was passed
        event = callback.call_args[0][0]
        assert event.payload == {"data": "test"}

    @pytest.mark.asyncio
    async def test_emit_updates_counters(self, webhook_trigger):
        """Test that emit() updates trigger counters."""
        webhook_trigger._event_callback = AsyncMock()
        await webhook_trigger.start()

        initial_count = webhook_trigger.config.trigger_count

        await webhook_trigger.emit({"test": True})

        assert webhook_trigger.config.trigger_count == initial_count + 1

    @pytest.mark.asyncio
    async def test_emit_cooldown_blocks_rapid_firing(self, webhook_trigger):
        """Test that cooldown prevents rapid re-triggering."""
        callback = AsyncMock()
        webhook_trigger._event_callback = callback
        webhook_trigger.config.cooldown_seconds = 60  # Long cooldown

        await webhook_trigger.start()

        # First emit should succeed
        result1 = await webhook_trigger.emit({"first": True})
        assert result1 is True

        # Second emit should be blocked by cooldown
        result2 = await webhook_trigger.emit({"second": True})
        assert result2 is False

        # Callback should only be called once
        assert callback.call_count == 1

    def test_get_info_returns_dict(self, webhook_trigger):
        """Test that get_info() returns expected structure."""
        info = webhook_trigger.get_info()

        assert "id" in info
        assert "name" in info
        assert "type" in info
        assert "status" in info
        assert info["id"] == "base_test"
        assert info["name"] == "Base Test"

    def test_repr(self, webhook_trigger):
        """Test string representation."""
        repr_str = repr(webhook_trigger)

        assert "WebhookTrigger" in repr_str
        assert "Base Test" in repr_str

    def test_is_active_property(self, webhook_trigger):
        """Test is_active property."""
        assert webhook_trigger.is_active is False

        webhook_trigger._status = TriggerStatus.ACTIVE
        assert webhook_trigger.is_active is True
