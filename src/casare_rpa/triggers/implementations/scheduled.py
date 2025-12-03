"""
CasareRPA - Scheduled Trigger

Trigger that fires on a schedule (cron, interval, or one-time).
Uses APScheduler for scheduling.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from loguru import logger

from casare_rpa.triggers.base import (
    BaseTrigger,
    BaseTriggerConfig,
    TriggerStatus,
    TriggerType,
)
from casare_rpa.triggers.registry import register_trigger


@register_trigger
class ScheduledTrigger(BaseTrigger):
    """
    Trigger that fires on a schedule.

    Configuration options:
        frequency: Schedule type (once, hourly, daily, weekly, monthly, cron)
        cron_expression: Cron expression for frequency="cron"
        time_hour: Hour of day (0-23)
        time_minute: Minute of hour (0-59)
        day_of_week: Day of week for weekly (0=Monday, 6=Sunday)
        day_of_month: Day of month for monthly (1-31)
        timezone: Timezone name (default: "UTC")
        run_at: ISO timestamp for frequency="once"

    Supports:
    - One-time execution at a specific time
    - Hourly execution at a specific minute
    - Daily execution at a specific time
    - Weekly execution on specific days
    - Monthly execution on specific days
    - Custom cron expressions
    """

    trigger_type = TriggerType.SCHEDULED
    display_name = "Scheduled"
    description = "Trigger workflow on a schedule"
    icon = "clock"
    category = "Time-based"

    def __init__(self, config: BaseTriggerConfig, event_callback=None):
        super().__init__(config, event_callback)
        self._scheduler = None
        self._job = None
        self._task: Optional[asyncio.Task] = None

    def _to_int(self, value: Any, default: int) -> int:
        """Convert value to int, handling string inputs from UI widgets."""
        if value is None:
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    async def start(self) -> bool:
        """Start the scheduled trigger."""
        try:
            from apscheduler.schedulers.asyncio import AsyncIOScheduler
            from apscheduler.triggers.cron import CronTrigger
            from apscheduler.triggers.date import DateTrigger
            from apscheduler.triggers.interval import IntervalTrigger

            self._scheduler = AsyncIOScheduler()

            # Build trigger based on frequency
            config = self.config.config
            frequency = config.get("frequency", "daily")
            timezone = config.get("timezone", "UTC")

            if frequency == "once":
                run_at = config.get("run_at")
                if run_at:
                    if isinstance(run_at, str):
                        run_at = datetime.fromisoformat(run_at)
                    trigger = DateTrigger(run_date=run_at, timezone=timezone)
                else:
                    # Schedule for next available time
                    hour = self._to_int(config.get("time_hour"), 9)
                    minute = self._to_int(config.get("time_minute"), 0)
                    run_at = datetime.now().replace(hour=hour, minute=minute, second=0)
                    if run_at < datetime.now():
                        run_at += timedelta(days=1)
                    trigger = DateTrigger(run_date=run_at, timezone=timezone)

            elif frequency == "hourly":
                minute = self._to_int(config.get("time_minute"), 0)
                trigger = CronTrigger(minute=minute, timezone=timezone)

            elif frequency == "daily":
                hour = self._to_int(config.get("time_hour"), 9)
                minute = self._to_int(config.get("time_minute"), 0)
                trigger = CronTrigger(hour=hour, minute=minute, timezone=timezone)

            elif frequency == "weekly":
                hour = self._to_int(config.get("time_hour"), 9)
                minute = self._to_int(config.get("time_minute"), 0)
                day_of_week = config.get(
                    "day_of_week", "mon"
                )  # APScheduler accepts string
                trigger = CronTrigger(
                    day_of_week=day_of_week, hour=hour, minute=minute, timezone=timezone
                )

            elif frequency == "monthly":
                hour = self._to_int(config.get("time_hour"), 9)
                minute = self._to_int(config.get("time_minute"), 0)
                day = self._to_int(config.get("day_of_month"), 1)
                trigger = CronTrigger(
                    day=day, hour=hour, minute=minute, timezone=timezone
                )

            elif frequency == "cron":
                cron_expr = config.get("cron_expression", "0 9 * * *")
                trigger = CronTrigger.from_crontab(cron_expr, timezone=timezone)

            elif frequency == "interval":
                # Interval-based scheduling (every N seconds)
                interval_seconds = self._to_int(config.get("interval_seconds"), 60)
                trigger = IntervalTrigger(seconds=interval_seconds, timezone=timezone)

            else:
                logger.error(f"Unknown frequency: {frequency}")
                return False

            # Add job to scheduler
            self._job = self._scheduler.add_job(
                self._on_schedule,
                trigger,
                id=f"trigger_{self.config.id}",
                name=self.config.name,
                replace_existing=True,
            )

            self._scheduler.start()
            self._status = TriggerStatus.ACTIVE

            next_run = self._job.next_run_time
            logger.info(
                f"Scheduled trigger started: {self.config.name} "
                f"(frequency: {frequency}, next: {next_run})"
            )
            return True

        except ImportError:
            logger.error(
                "APScheduler not installed. Install with: pip install apscheduler"
            )
            self._status = TriggerStatus.ERROR
            self._error_message = "APScheduler not installed"
            return False
        except Exception as e:
            logger.error(f"Failed to start scheduled trigger: {e}")
            self._status = TriggerStatus.ERROR
            self._error_message = str(e)
            return False

    async def stop(self) -> bool:
        """Stop the scheduled trigger."""
        if self._scheduler:
            try:
                self._scheduler.shutdown(wait=False)
            except Exception as e:
                logger.warning(f"Error shutting down scheduler: {e}")
            self._scheduler = None
            self._job = None

        self._status = TriggerStatus.INACTIVE
        logger.info(f"Scheduled trigger stopped: {self.config.name}")
        return True

    async def _on_schedule(self) -> None:
        """Called when schedule fires."""
        # Check max_runs limit
        max_runs = self._to_int(self.config.config.get("max_runs"), 0)
        if max_runs > 0 and self.config.trigger_count >= max_runs:
            logger.info(
                f"Trigger {self.config.name} reached max_runs ({max_runs}), stopping"
            )
            await self.stop()
            return

        payload = {
            "scheduled_time": datetime.now(timezone.utc).isoformat(),
            "trigger_name": self.config.name,
            "frequency": self.config.config.get("frequency", "daily"),
            "run_number": self.config.trigger_count + 1,
        }

        metadata = {
            "source": "scheduled",
            "next_run": (
                self._job.next_run_time.isoformat()
                if self._job and self._job.next_run_time
                else None
            ),
            "max_runs": max_runs,
            "runs_remaining": max_runs - self.config.trigger_count - 1
            if max_runs > 0
            else None,
        }

        await self.emit(payload, metadata)

        # Check if we just reached max_runs (after emit incremented count)
        if max_runs > 0 and self.config.trigger_count >= max_runs:
            logger.info(
                f"Trigger {self.config.name} completed {max_runs} runs, stopping"
            )
            await self.stop()

    def validate_config(self) -> tuple[bool, Optional[str]]:
        """Validate scheduled trigger configuration."""
        config = self.config.config

        frequency = config.get("frequency", "daily")
        valid_frequencies = [
            "once",
            "interval",
            "hourly",
            "daily",
            "weekly",
            "monthly",
            "cron",
        ]
        if frequency not in valid_frequencies:
            return False, f"Invalid frequency. Must be one of: {valid_frequencies}"

        # Validate interval_seconds for interval frequency
        if frequency == "interval":
            interval_seconds = config.get("interval_seconds", 60)
            if not isinstance(interval_seconds, (int, float)) or interval_seconds < 1:
                return False, "interval_seconds must be at least 1"

        # Validate time values
        hour = config.get("time_hour", 0)
        if not (0 <= hour <= 23):
            return False, "time_hour must be between 0 and 23"

        minute = config.get("time_minute", 0)
        if not (0 <= minute <= 59):
            return False, "time_minute must be between 0 and 59"

        # Validate cron expression
        if frequency == "cron":
            cron_expr = config.get("cron_expression", "")
            if not cron_expr:
                return False, "cron_expression is required for frequency='cron'"

            # Basic validation - APScheduler will do full validation
            parts = cron_expr.split()
            if len(parts) < 5 or len(parts) > 6:
                return False, "Invalid cron expression format"

        # Validate day_of_week for weekly
        if frequency == "weekly":
            dow = config.get("day_of_week", 0)
            if not (0 <= dow <= 6):
                return False, "day_of_week must be between 0 (Monday) and 6 (Sunday)"

        # Validate day_of_month for monthly
        if frequency == "monthly":
            dom = config.get("day_of_month", 1)
            if not (1 <= dom <= 31):
                return False, "day_of_month must be between 1 and 31"

        return True, None

    def get_next_run(self) -> Optional[datetime]:
        """Get the next scheduled run time."""
        if self._job and self._job.next_run_time:
            return self._job.next_run_time
        return None

    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for scheduled trigger configuration."""
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Trigger name"},
                "enabled": {"type": "boolean", "default": True},
                "priority": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 3,
                    "default": 1,
                },
                "cooldown_seconds": {"type": "integer", "minimum": 0, "default": 0},
                "frequency": {
                    "type": "string",
                    "enum": [
                        "once",
                        "interval",
                        "hourly",
                        "daily",
                        "weekly",
                        "monthly",
                        "cron",
                    ],
                    "default": "daily",
                    "description": "Schedule frequency type",
                },
                "interval_seconds": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 86400,
                    "default": 60,
                    "description": "Interval in seconds (for frequency='interval')",
                },
                "cron_expression": {
                    "type": "string",
                    "description": "Cron expression (for frequency='cron')",
                    "examples": ["0 9 * * *", "*/15 * * * *"],
                },
                "time_hour": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 23,
                    "default": 9,
                    "description": "Hour of day (0-23)",
                },
                "time_minute": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 59,
                    "default": 0,
                    "description": "Minute of hour (0-59)",
                },
                "day_of_week": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 6,
                    "default": 0,
                    "description": "Day of week for weekly (0=Monday, 6=Sunday)",
                },
                "day_of_month": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 31,
                    "default": 1,
                    "description": "Day of month for monthly schedules",
                },
                "timezone": {
                    "type": "string",
                    "default": "UTC",
                    "description": "Timezone name",
                    "examples": ["UTC", "America/New_York", "Europe/London"],
                },
                "run_at": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Specific run time for frequency='once'",
                },
                "max_runs": {
                    "type": "integer",
                    "minimum": 0,
                    "default": 0,
                    "description": "Maximum number of runs (0 = unlimited)",
                },
            },
            "required": ["name"],
        }
