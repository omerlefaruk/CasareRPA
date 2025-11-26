"""
CasareRPA - Scheduled Trigger Tests

Comprehensive tests for the scheduled trigger implementation.
Tests cron, interval, daily, weekly, monthly, and one-time schedules.
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

# Add src to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from casare_rpa.triggers.base import BaseTriggerConfig, TriggerStatus, TriggerType
from casare_rpa.triggers.implementations.scheduled import ScheduledTrigger


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def base_config():
    """Create a base trigger configuration."""
    return BaseTriggerConfig(
        id="scheduled_test_001",
        name="Test Scheduled Trigger",
        trigger_type=TriggerType.SCHEDULED,
        scenario_id="scenario_001",
        workflow_id="workflow_001",
        config={}
    )


@pytest.fixture
def interval_config(base_config):
    """Create interval-based trigger config."""
    base_config.config = {
        "frequency": "interval",
        "interval_seconds": 5
    }
    return base_config


@pytest.fixture
def daily_config(base_config):
    """Create daily trigger config."""
    base_config.config = {
        "frequency": "daily",
        "time_hour": 9,
        "time_minute": 30,
        "timezone": "UTC"
    }
    return base_config


@pytest.fixture
def weekly_config(base_config):
    """Create weekly trigger config."""
    base_config.config = {
        "frequency": "weekly",
        "time_hour": 10,
        "time_minute": 0,
        "day_of_week": 1,  # Tuesday
        "timezone": "UTC"
    }
    return base_config


@pytest.fixture
def monthly_config(base_config):
    """Create monthly trigger config."""
    base_config.config = {
        "frequency": "monthly",
        "time_hour": 8,
        "time_minute": 0,
        "day_of_month": 15,
        "timezone": "UTC"
    }
    return base_config


@pytest.fixture
def cron_config(base_config):
    """Create cron-based trigger config."""
    base_config.config = {
        "frequency": "cron",
        "cron_expression": "*/5 * * * *",  # Every 5 minutes
        "timezone": "UTC"
    }
    return base_config


@pytest.fixture
def once_config(base_config):
    """Create one-time trigger config."""
    run_at = (datetime.now() + timedelta(hours=1)).isoformat()
    base_config.config = {
        "frequency": "once",
        "run_at": run_at,
        "timezone": "UTC"
    }
    return base_config


# =============================================================================
# Class Attributes Tests
# =============================================================================

class TestScheduledTriggerClassAttributes:
    """Test class-level attributes of ScheduledTrigger."""

    def test_trigger_type(self):
        """Test trigger type is scheduled."""
        assert ScheduledTrigger.trigger_type == TriggerType.SCHEDULED

    def test_display_name(self):
        """Test display name."""
        assert ScheduledTrigger.display_name == "Scheduled"

    def test_description(self):
        """Test description is set."""
        assert "schedule" in ScheduledTrigger.description.lower()

    def test_icon(self):
        """Test icon is set."""
        assert ScheduledTrigger.icon == "clock"

    def test_category(self):
        """Test category is time-based."""
        assert ScheduledTrigger.category == "Time-based"


# =============================================================================
# Initialization Tests
# =============================================================================

class TestScheduledTriggerInit:
    """Test ScheduledTrigger initialization."""

    def test_init_basic(self, base_config):
        """Test basic initialization."""
        trigger = ScheduledTrigger(base_config)
        assert trigger.config == base_config
        assert trigger.status == TriggerStatus.INACTIVE
        assert trigger._scheduler is None
        assert trigger._job is None

    def test_init_with_callback(self, base_config):
        """Test initialization with callback."""
        callback = AsyncMock()
        trigger = ScheduledTrigger(base_config, event_callback=callback)
        assert trigger._event_callback == callback


# =============================================================================
# Configuration Validation Tests
# =============================================================================

class TestScheduledTriggerValidation:
    """Test configuration validation."""

    def test_validate_interval_config(self, interval_config):
        """Test valid interval config validation."""
        trigger = ScheduledTrigger(interval_config)
        is_valid, error = trigger.validate_config()
        assert is_valid is True
        assert error is None

    def test_validate_daily_config(self, daily_config):
        """Test valid daily config validation."""
        trigger = ScheduledTrigger(daily_config)
        is_valid, error = trigger.validate_config()
        assert is_valid is True
        assert error is None

    def test_validate_weekly_config(self, weekly_config):
        """Test valid weekly config validation."""
        trigger = ScheduledTrigger(weekly_config)
        is_valid, error = trigger.validate_config()
        assert is_valid is True
        assert error is None

    def test_validate_monthly_config(self, monthly_config):
        """Test valid monthly config validation."""
        trigger = ScheduledTrigger(monthly_config)
        is_valid, error = trigger.validate_config()
        assert is_valid is True
        assert error is None

    def test_validate_cron_config(self, cron_config):
        """Test valid cron config validation."""
        trigger = ScheduledTrigger(cron_config)
        is_valid, error = trigger.validate_config()
        assert is_valid is True
        assert error is None

    def test_validate_once_config(self, once_config):
        """Test valid one-time config validation."""
        trigger = ScheduledTrigger(once_config)
        is_valid, error = trigger.validate_config()
        assert is_valid is True
        assert error is None

    def test_validate_invalid_frequency(self, base_config):
        """Test invalid frequency is rejected."""
        base_config.config = {"frequency": "invalid_frequency"}
        trigger = ScheduledTrigger(base_config)
        is_valid, error = trigger.validate_config()
        assert is_valid is False
        assert "frequency" in error.lower()

    def test_validate_invalid_interval_seconds(self, base_config):
        """Test invalid interval_seconds is rejected."""
        base_config.config = {
            "frequency": "interval",
            "interval_seconds": 0  # Must be at least 1
        }
        trigger = ScheduledTrigger(base_config)
        is_valid, error = trigger.validate_config()
        assert is_valid is False
        assert "interval_seconds" in error.lower()

    def test_validate_invalid_hour(self, base_config):
        """Test invalid hour is rejected."""
        base_config.config = {
            "frequency": "daily",
            "time_hour": 25,  # Invalid hour
            "time_minute": 0
        }
        trigger = ScheduledTrigger(base_config)
        is_valid, error = trigger.validate_config()
        assert is_valid is False
        assert "hour" in error.lower()

    def test_validate_invalid_minute(self, base_config):
        """Test invalid minute is rejected."""
        base_config.config = {
            "frequency": "daily",
            "time_hour": 9,
            "time_minute": 60  # Invalid minute
        }
        trigger = ScheduledTrigger(base_config)
        is_valid, error = trigger.validate_config()
        assert is_valid is False
        assert "minute" in error.lower()

    def test_validate_invalid_day_of_week(self, base_config):
        """Test invalid day_of_week is rejected."""
        base_config.config = {
            "frequency": "weekly",
            "time_hour": 9,
            "time_minute": 0,
            "day_of_week": 7  # Invalid (must be 0-6)
        }
        trigger = ScheduledTrigger(base_config)
        is_valid, error = trigger.validate_config()
        assert is_valid is False
        assert "day_of_week" in error.lower()

    def test_validate_invalid_day_of_month(self, base_config):
        """Test invalid day_of_month is rejected."""
        base_config.config = {
            "frequency": "monthly",
            "time_hour": 9,
            "time_minute": 0,
            "day_of_month": 32  # Invalid
        }
        trigger = ScheduledTrigger(base_config)
        is_valid, error = trigger.validate_config()
        assert is_valid is False
        assert "day_of_month" in error.lower()

    def test_validate_empty_cron_expression(self, base_config):
        """Test empty cron expression is rejected."""
        base_config.config = {
            "frequency": "cron",
            "cron_expression": ""
        }
        trigger = ScheduledTrigger(base_config)
        is_valid, error = trigger.validate_config()
        assert is_valid is False
        assert "cron_expression" in error.lower()

    def test_validate_invalid_cron_expression_format(self, base_config):
        """Test invalid cron expression format is rejected."""
        base_config.config = {
            "frequency": "cron",
            "cron_expression": "invalid"  # Not enough parts
        }
        trigger = ScheduledTrigger(base_config)
        is_valid, error = trigger.validate_config()
        assert is_valid is False
        assert "cron" in error.lower()


# =============================================================================
# Start/Stop Tests
# =============================================================================

class TestScheduledTriggerStartStop:
    """Test starting and stopping scheduled triggers."""

    @pytest.mark.asyncio
    async def test_start_interval_trigger(self, interval_config):
        """Test starting interval trigger."""
        trigger = ScheduledTrigger(interval_config)

        result = await trigger.start()

        assert result is True
        assert trigger.status == TriggerStatus.ACTIVE
        assert trigger._scheduler is not None
        assert trigger._job is not None

        await trigger.stop()

    @pytest.mark.asyncio
    async def test_start_daily_trigger(self, daily_config):
        """Test starting daily trigger."""
        trigger = ScheduledTrigger(daily_config)

        result = await trigger.start()

        assert result is True
        assert trigger.status == TriggerStatus.ACTIVE

        await trigger.stop()

    @pytest.mark.asyncio
    async def test_start_cron_trigger(self, cron_config):
        """Test starting cron trigger."""
        trigger = ScheduledTrigger(cron_config)

        result = await trigger.start()

        assert result is True
        assert trigger.status == TriggerStatus.ACTIVE

        await trigger.stop()

    @pytest.mark.asyncio
    async def test_stop_trigger(self, interval_config):
        """Test stopping a trigger."""
        trigger = ScheduledTrigger(interval_config)
        await trigger.start()

        result = await trigger.stop()

        assert result is True
        assert trigger.status == TriggerStatus.INACTIVE
        assert trigger._scheduler is None
        assert trigger._job is None

    @pytest.mark.asyncio
    async def test_start_with_invalid_config(self, base_config):
        """Test starting with invalid config fails gracefully."""
        base_config.config = {"frequency": "invalid"}
        trigger = ScheduledTrigger(base_config)

        result = await trigger.start()

        assert result is False
        # Status stays INACTIVE when start fails due to invalid config
        assert trigger.status in (TriggerStatus.INACTIVE, TriggerStatus.ERROR)

    @pytest.mark.asyncio
    async def test_stop_unstarted_trigger(self, interval_config):
        """Test stopping trigger that was never started."""
        trigger = ScheduledTrigger(interval_config)

        result = await trigger.stop()

        assert result is True
        assert trigger.status == TriggerStatus.INACTIVE


# =============================================================================
# Schedule Firing Tests
# =============================================================================

class TestScheduledTriggerFiring:
    """Test trigger firing behavior."""

    @pytest.mark.asyncio
    async def test_interval_trigger_fires(self, interval_config):
        """Test interval trigger fires at correct times."""
        interval_config.config["interval_seconds"] = 1  # 1 second for fast test
        events_received = []

        async def callback(event):
            events_received.append(event)

        trigger = ScheduledTrigger(interval_config, event_callback=callback)
        await trigger.start()

        # Wait for at least 2 fires
        await asyncio.sleep(2.5)

        await trigger.stop()

        assert len(events_received) >= 2

    @pytest.mark.asyncio
    async def test_trigger_payload_content(self, interval_config):
        """Test trigger event payload contains expected data."""
        interval_config.config["interval_seconds"] = 1
        received_event = None

        async def callback(event):
            nonlocal received_event
            received_event = event

        trigger = ScheduledTrigger(interval_config, event_callback=callback)
        await trigger.start()

        await asyncio.sleep(1.5)

        await trigger.stop()

        assert received_event is not None
        assert "scheduled_time" in received_event.payload
        assert "trigger_name" in received_event.payload
        assert "frequency" in received_event.payload
        assert received_event.payload["frequency"] == "interval"

    @pytest.mark.asyncio
    async def test_get_next_run(self, interval_config):
        """Test getting next scheduled run time."""
        trigger = ScheduledTrigger(interval_config)
        await trigger.start()

        next_run = trigger.get_next_run()

        assert next_run is not None
        assert isinstance(next_run, datetime)
        assert next_run > datetime.now(next_run.tzinfo)

        await trigger.stop()

    @pytest.mark.asyncio
    async def test_get_next_run_unstarted(self, interval_config):
        """Test get_next_run returns None when not started."""
        trigger = ScheduledTrigger(interval_config)

        next_run = trigger.get_next_run()

        assert next_run is None


# =============================================================================
# Max Runs Tests
# =============================================================================

class TestScheduledTriggerMaxRuns:
    """Test max_runs functionality."""

    @pytest.mark.asyncio
    async def test_max_runs_stops_trigger(self, interval_config):
        """Test trigger stops after max_runs."""
        interval_config.config["interval_seconds"] = 1
        interval_config.config["max_runs"] = 3
        events_received = []

        async def callback(event):
            events_received.append(event)

        trigger = ScheduledTrigger(interval_config, event_callback=callback)
        await trigger.start()

        # Wait enough time for more than 3 runs
        await asyncio.sleep(5)

        # Trigger should have stopped itself
        assert trigger.status == TriggerStatus.INACTIVE
        assert len(events_received) == 3

    @pytest.mark.asyncio
    async def test_max_runs_zero_means_unlimited(self, interval_config):
        """Test max_runs=0 allows unlimited runs."""
        interval_config.config["interval_seconds"] = 1
        interval_config.config["max_runs"] = 0  # Unlimited
        events_received = []

        async def callback(event):
            events_received.append(event)

        trigger = ScheduledTrigger(interval_config, event_callback=callback)
        await trigger.start()

        await asyncio.sleep(3.5)

        await trigger.stop()

        # Should have more than 3 runs (max_runs doesn't limit)
        assert len(events_received) >= 3

    @pytest.mark.asyncio
    async def test_run_number_in_payload(self, interval_config):
        """Test run_number is included in payload."""
        interval_config.config["interval_seconds"] = 1
        interval_config.config["max_runs"] = 3
        events_received = []

        async def callback(event):
            events_received.append(event)

        trigger = ScheduledTrigger(interval_config, event_callback=callback)
        await trigger.start()

        await asyncio.sleep(4)

        assert len(events_received) >= 1
        # First event should have run_number 1
        assert events_received[0].payload.get("run_number") == 1


# =============================================================================
# Config Schema Tests
# =============================================================================

class TestScheduledTriggerConfigSchema:
    """Test configuration schema."""

    def test_config_schema_structure(self):
        """Test schema has correct structure."""
        schema = ScheduledTrigger.get_config_schema()

        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema

    def test_config_schema_has_frequency(self):
        """Test schema includes frequency property."""
        schema = ScheduledTrigger.get_config_schema()
        props = schema["properties"]

        assert "frequency" in props
        assert "enum" in props["frequency"]
        expected_frequencies = ["once", "interval", "hourly", "daily", "weekly", "monthly", "cron"]
        for freq in expected_frequencies:
            assert freq in props["frequency"]["enum"]

    def test_config_schema_has_interval_seconds(self):
        """Test schema includes interval_seconds property."""
        schema = ScheduledTrigger.get_config_schema()
        props = schema["properties"]

        assert "interval_seconds" in props
        assert props["interval_seconds"]["type"] == "integer"
        assert props["interval_seconds"]["minimum"] == 1

    def test_config_schema_has_cron_expression(self):
        """Test schema includes cron_expression property."""
        schema = ScheduledTrigger.get_config_schema()
        props = schema["properties"]

        assert "cron_expression" in props
        assert props["cron_expression"]["type"] == "string"

    def test_config_schema_has_time_fields(self):
        """Test schema includes time fields."""
        schema = ScheduledTrigger.get_config_schema()
        props = schema["properties"]

        assert "time_hour" in props
        assert props["time_hour"]["minimum"] == 0
        assert props["time_hour"]["maximum"] == 23

        assert "time_minute" in props
        assert props["time_minute"]["minimum"] == 0
        assert props["time_minute"]["maximum"] == 59

    def test_config_schema_has_day_fields(self):
        """Test schema includes day fields."""
        schema = ScheduledTrigger.get_config_schema()
        props = schema["properties"]

        assert "day_of_week" in props
        assert props["day_of_week"]["minimum"] == 0
        assert props["day_of_week"]["maximum"] == 6

        assert "day_of_month" in props
        assert props["day_of_month"]["minimum"] == 1
        assert props["day_of_month"]["maximum"] == 31

    def test_config_schema_has_max_runs(self):
        """Test schema includes max_runs property."""
        schema = ScheduledTrigger.get_config_schema()
        props = schema["properties"]

        assert "max_runs" in props
        assert props["max_runs"]["type"] == "integer"
        assert props["max_runs"]["minimum"] == 0


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================

class TestScheduledTriggerEdgeCases:
    """Edge case and error handling tests."""

    @pytest.mark.asyncio
    async def test_start_already_running(self, interval_config):
        """Test starting an already running trigger."""
        trigger = ScheduledTrigger(interval_config)
        await trigger.start()

        # Try to start again - should handle gracefully
        # (Implementation may vary - could return True or False)
        result = await trigger.start()

        # Just ensure it doesn't crash and is still running
        assert trigger.status == TriggerStatus.ACTIVE

        await trigger.stop()

    @pytest.mark.asyncio
    async def test_multiple_stop_calls(self, interval_config):
        """Test multiple stop calls are safe."""
        trigger = ScheduledTrigger(interval_config)
        await trigger.start()

        await trigger.stop()
        await trigger.stop()  # Should not raise

        assert trigger.status == TriggerStatus.INACTIVE

    def test_hourly_config_validation(self, base_config):
        """Test hourly frequency config validation."""
        base_config.config = {
            "frequency": "hourly",
            "time_minute": 30
        }
        trigger = ScheduledTrigger(base_config)
        is_valid, error = trigger.validate_config()
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_different_timezones(self, daily_config):
        """Test triggers with different timezones."""
        for tz in ["UTC", "America/New_York", "Europe/London", "Asia/Tokyo"]:
            daily_config.config["timezone"] = tz
            trigger = ScheduledTrigger(daily_config)

            result = await trigger.start()
            assert result is True

            next_run = trigger.get_next_run()
            assert next_run is not None

            await trigger.stop()

    @pytest.mark.asyncio
    async def test_cron_with_special_characters(self, base_config):
        """Test various cron expression formats."""
        cron_expressions = [
            "0 9 * * *",      # Daily at 9am
            "*/15 * * * *",   # Every 15 minutes
            "0 0 1 * *",      # First day of month
            "0 12 * * 1-5",   # Weekdays at noon
        ]

        for cron in cron_expressions:
            base_config.config = {
                "frequency": "cron",
                "cron_expression": cron
            }
            trigger = ScheduledTrigger(base_config)

            is_valid, error = trigger.validate_config()
            assert is_valid is True, f"Cron '{cron}' should be valid: {error}"

            result = await trigger.start()
            assert result is True, f"Should start with cron '{cron}'"

            await trigger.stop()

    @pytest.mark.asyncio
    async def test_rapid_start_stop_cycles(self, interval_config):
        """Test rapid start/stop cycles."""
        trigger = ScheduledTrigger(interval_config)

        for _ in range(10):
            await trigger.start()
            assert trigger.status == TriggerStatus.ACTIVE
            await trigger.stop()
            assert trigger.status == TriggerStatus.INACTIVE

    @pytest.mark.asyncio
    async def test_callback_exception_doesnt_stop_trigger(self, interval_config):
        """Test that callback exceptions don't stop the trigger."""
        interval_config.config["interval_seconds"] = 1
        error_count = 0
        success_count = 0

        async def failing_callback(event):
            nonlocal error_count, success_count
            if error_count < 2:
                error_count += 1
                raise RuntimeError("Simulated failure")
            success_count += 1

        trigger = ScheduledTrigger(interval_config, event_callback=failing_callback)
        await trigger.start()

        await asyncio.sleep(4)

        await trigger.stop()

        # Should have continued running despite errors
        assert error_count == 2
        assert success_count >= 1
