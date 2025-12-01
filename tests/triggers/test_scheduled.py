"""Tests for scheduled trigger module."""

import pytest
from typing import Optional

from casare_rpa.triggers.base import BaseTriggerConfig, TriggerType
from casare_rpa.triggers.implementations.scheduled import ScheduledTrigger


@pytest.fixture
def make_scheduled_config():
    """Factory fixture to create scheduled trigger configs."""

    def _make_config(
        config: dict,
        name: str = "Test Scheduled Trigger",
        trigger_id: str = "trig_sched_test",
    ) -> BaseTriggerConfig:
        return BaseTriggerConfig(
            id=trigger_id,
            name=name,
            trigger_type=TriggerType.SCHEDULED,
            scenario_id="scen_123",
            workflow_id="wf_456",
            config=config,
        )

    return _make_config


class TestScheduledTriggerMetadata:
    """Tests for ScheduledTrigger class metadata."""

    def test_trigger_type(self):
        """Test trigger type is scheduled."""
        assert ScheduledTrigger.trigger_type == TriggerType.SCHEDULED

    def test_display_name(self):
        """Test display name."""
        assert ScheduledTrigger.display_name == "Scheduled"

    def test_category(self):
        """Test category."""
        assert ScheduledTrigger.category == "Time-based"


class TestScheduledTriggerValidation:
    """Tests for scheduled trigger configuration validation."""

    def test_valid_daily_frequency(self, make_scheduled_config):
        """Test valid daily frequency config."""
        config = make_scheduled_config(
            {
                "frequency": "daily",
                "time_hour": 9,
                "time_minute": 30,
            }
        )
        trigger = ScheduledTrigger(config)

        valid, error = trigger.validate_config()

        assert valid is True
        assert error is None

    def test_valid_hourly_frequency(self, make_scheduled_config):
        """Test valid hourly frequency config."""
        config = make_scheduled_config(
            {
                "frequency": "hourly",
                "time_minute": 15,
            }
        )
        trigger = ScheduledTrigger(config)

        valid, error = trigger.validate_config()

        assert valid is True
        assert error is None

    def test_valid_weekly_frequency(self, make_scheduled_config):
        """Test valid weekly frequency config."""
        config = make_scheduled_config(
            {
                "frequency": "weekly",
                "day_of_week": 1,  # Tuesday
                "time_hour": 10,
                "time_minute": 0,
            }
        )
        trigger = ScheduledTrigger(config)

        valid, error = trigger.validate_config()

        assert valid is True
        assert error is None

    def test_valid_monthly_frequency(self, make_scheduled_config):
        """Test valid monthly frequency config."""
        config = make_scheduled_config(
            {
                "frequency": "monthly",
                "day_of_month": 15,
                "time_hour": 8,
                "time_minute": 0,
            }
        )
        trigger = ScheduledTrigger(config)

        valid, error = trigger.validate_config()

        assert valid is True
        assert error is None

    def test_valid_cron_frequency(self, make_scheduled_config):
        """Test valid cron frequency config."""
        config = make_scheduled_config(
            {
                "frequency": "cron",
                "cron_expression": "0 9 * * 1-5",  # 9 AM Mon-Fri
            }
        )
        trigger = ScheduledTrigger(config)

        valid, error = trigger.validate_config()

        assert valid is True
        assert error is None

    def test_valid_interval_frequency(self, make_scheduled_config):
        """Test valid interval frequency config."""
        config = make_scheduled_config(
            {
                "frequency": "interval",
                "interval_seconds": 300,  # 5 minutes
            }
        )
        trigger = ScheduledTrigger(config)

        valid, error = trigger.validate_config()

        assert valid is True
        assert error is None

    def test_valid_once_frequency(self, make_scheduled_config):
        """Test valid once frequency config."""
        config = make_scheduled_config(
            {
                "frequency": "once",
                "run_at": "2025-12-31T23:59:59",
            }
        )
        trigger = ScheduledTrigger(config)

        valid, error = trigger.validate_config()

        assert valid is True
        assert error is None

    def test_invalid_frequency(self, make_scheduled_config):
        """Test invalid frequency value."""
        config = make_scheduled_config(
            {
                "frequency": "invalid_frequency",
            }
        )
        trigger = ScheduledTrigger(config)

        valid, error = trigger.validate_config()

        assert valid is False
        assert "Invalid frequency" in error

    def test_invalid_time_hour_too_high(self, make_scheduled_config):
        """Test invalid time_hour (too high)."""
        config = make_scheduled_config(
            {
                "frequency": "daily",
                "time_hour": 25,
            }
        )
        trigger = ScheduledTrigger(config)

        valid, error = trigger.validate_config()

        assert valid is False
        assert "time_hour" in error

    def test_invalid_time_hour_negative(self, make_scheduled_config):
        """Test invalid time_hour (negative)."""
        config = make_scheduled_config(
            {
                "frequency": "daily",
                "time_hour": -1,
            }
        )
        trigger = ScheduledTrigger(config)

        valid, error = trigger.validate_config()

        assert valid is False
        assert "time_hour" in error

    def test_invalid_time_minute(self, make_scheduled_config):
        """Test invalid time_minute."""
        config = make_scheduled_config(
            {
                "frequency": "daily",
                "time_minute": 60,
            }
        )
        trigger = ScheduledTrigger(config)

        valid, error = trigger.validate_config()

        assert valid is False
        assert "time_minute" in error

    def test_invalid_day_of_week(self, make_scheduled_config):
        """Test invalid day_of_week for weekly."""
        config = make_scheduled_config(
            {
                "frequency": "weekly",
                "day_of_week": 7,  # Invalid, should be 0-6
            }
        )
        trigger = ScheduledTrigger(config)

        valid, error = trigger.validate_config()

        assert valid is False
        assert "day_of_week" in error

    def test_invalid_day_of_month_too_high(self, make_scheduled_config):
        """Test invalid day_of_month (too high)."""
        config = make_scheduled_config(
            {
                "frequency": "monthly",
                "day_of_month": 32,
            }
        )
        trigger = ScheduledTrigger(config)

        valid, error = trigger.validate_config()

        assert valid is False
        assert "day_of_month" in error

    def test_invalid_day_of_month_zero(self, make_scheduled_config):
        """Test invalid day_of_month (zero)."""
        config = make_scheduled_config(
            {
                "frequency": "monthly",
                "day_of_month": 0,
            }
        )
        trigger = ScheduledTrigger(config)

        valid, error = trigger.validate_config()

        assert valid is False
        assert "day_of_month" in error

    def test_cron_missing_expression(self, make_scheduled_config):
        """Test cron frequency without expression."""
        config = make_scheduled_config(
            {
                "frequency": "cron",
                "cron_expression": "",
            }
        )
        trigger = ScheduledTrigger(config)

        valid, error = trigger.validate_config()

        assert valid is False
        assert "cron_expression is required" in error

    def test_cron_invalid_format(self, make_scheduled_config):
        """Test cron with invalid format (too few parts)."""
        config = make_scheduled_config(
            {
                "frequency": "cron",
                "cron_expression": "0 9 *",  # Only 3 parts
            }
        )
        trigger = ScheduledTrigger(config)

        valid, error = trigger.validate_config()

        assert valid is False
        assert "Invalid cron expression format" in error

    def test_interval_too_small(self, make_scheduled_config):
        """Test interval frequency with interval < 1."""
        config = make_scheduled_config(
            {
                "frequency": "interval",
                "interval_seconds": 0,
            }
        )
        trigger = ScheduledTrigger(config)

        valid, error = trigger.validate_config()

        assert valid is False
        assert "interval_seconds must be at least 1" in error


class TestScheduledTriggerConfigSchema:
    """Tests for scheduled trigger config schema."""

    def test_schema_has_required_properties(self):
        """Test schema contains required properties."""
        schema = ScheduledTrigger.get_config_schema()

        assert schema["type"] == "object"
        assert "properties" in schema
        assert "name" in schema["properties"]
        assert "frequency" in schema["properties"]

    def test_schema_frequency_enum(self):
        """Test schema has frequency enum values."""
        schema = ScheduledTrigger.get_config_schema()
        freq_schema = schema["properties"]["frequency"]

        assert "enum" in freq_schema
        expected = ["once", "interval", "hourly", "daily", "weekly", "monthly", "cron"]
        assert freq_schema["enum"] == expected

    def test_schema_time_hour_bounds(self):
        """Test schema has correct time_hour bounds."""
        schema = ScheduledTrigger.get_config_schema()
        hour_schema = schema["properties"]["time_hour"]

        assert hour_schema["minimum"] == 0
        assert hour_schema["maximum"] == 23

    def test_schema_time_minute_bounds(self):
        """Test schema has correct time_minute bounds."""
        schema = ScheduledTrigger.get_config_schema()
        minute_schema = schema["properties"]["time_minute"]

        assert minute_schema["minimum"] == 0
        assert minute_schema["maximum"] == 59

    def test_schema_day_of_week_bounds(self):
        """Test schema has correct day_of_week bounds."""
        schema = ScheduledTrigger.get_config_schema()
        dow_schema = schema["properties"]["day_of_week"]

        assert dow_schema["minimum"] == 0
        assert dow_schema["maximum"] == 6

    def test_schema_day_of_month_bounds(self):
        """Test schema has correct day_of_month bounds."""
        schema = ScheduledTrigger.get_config_schema()
        dom_schema = schema["properties"]["day_of_month"]

        assert dom_schema["minimum"] == 1
        assert dom_schema["maximum"] == 31

    def test_schema_required_fields(self):
        """Test schema required fields."""
        schema = ScheduledTrigger.get_config_schema()

        assert "required" in schema
        assert "name" in schema["required"]


class TestScheduledTriggerInit:
    """Tests for ScheduledTrigger initialization."""

    def test_initialization(self, make_scheduled_config):
        """Test trigger initialization."""
        config = make_scheduled_config({"frequency": "daily"})
        trigger = ScheduledTrigger(config)

        assert trigger.config == config
        assert trigger._scheduler is None
        assert trigger._job is None

    def test_get_next_run_before_start(self, make_scheduled_config):
        """Test get_next_run returns None before start."""
        config = make_scheduled_config({"frequency": "daily"})
        trigger = ScheduledTrigger(config)

        assert trigger.get_next_run() is None
