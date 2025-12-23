"""
Scheduling strategies for CasareRPA Orchestrator.

Contains cron expression parsing and human-readable conversion utilities.
Implements the Strategy pattern for different scheduling approaches.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

# Cron aliases for human-readable scheduling
CRON_ALIASES: dict[str, str] = {
    "@yearly": "0 0 1 1 *",
    "@annually": "0 0 1 1 *",
    "@monthly": "0 0 1 * *",
    "@weekly": "0 0 * * 0",
    "@daily": "0 0 * * *",
    "@midnight": "0 0 * * *",
    "@hourly": "0 * * * *",
    "@every_minute": "* * * * *",
    "@every_5_minutes": "*/5 * * * *",
    "@every_10_minutes": "*/10 * * * *",
    "@every_15_minutes": "*/15 * * * *",
    "@every_30_minutes": "*/30 * * * *",
    "@business_hours": "0 9-17 * * 1-5",
    "@weekdays": "0 9 * * 1-5",
    "@weekends": "0 9 * * 0,6",
    "@end_of_month": "0 0 L * *",
    "@first_monday": "0 0 * * 1#1",
    "@last_friday": "0 17 * * 5L",
}


class SchedulingStrategy(ABC):
    """
    Abstract base class for scheduling strategies.

    Implements the Strategy pattern for different scheduling approaches.
    """

    @abstractmethod
    def get_next_run_time(
        self,
        current_time: datetime,
        last_run: datetime | None = None,
    ) -> datetime | None:
        """
        Calculate the next run time based on the strategy.

        Args:
            current_time: Current datetime
            last_run: Optional last execution time

        Returns:
            Next scheduled run time or None if no more runs
        """
        pass

    @abstractmethod
    def validate(self) -> tuple[bool, str | None]:
        """
        Validate the strategy configuration.

        Returns:
            Tuple of (is_valid, error_message)
        """
        pass


class CronExpressionParser:
    """
    Parser for cron expressions with human-readable aliases.

    Supports:
    - Standard 5-field cron: minute hour day month weekday
    - Extended 6-field cron: second minute hour day month weekday
    - Human-readable aliases (@daily, @hourly, etc.)
    - Special syntax (L for last, # for nth weekday)
    """

    FIELD_NAMES = ["minute", "hour", "day", "month", "day_of_week"]
    FIELD_NAMES_6 = ["second", "minute", "hour", "day", "month", "day_of_week"]

    @classmethod
    def parse(cls, expression: str) -> dict[str, str]:
        """
        Parse cron expression into APScheduler trigger kwargs.

        Args:
            expression: Cron expression or alias

        Returns:
            Dict with cron trigger parameters

        Raises:
            ValueError: If expression is invalid
        """
        expression = expression.strip()

        if expression.startswith("@"):
            alias_lower = expression.lower()
            if alias_lower in CRON_ALIASES:
                expression = CRON_ALIASES[alias_lower]
            else:
                raise ValueError(f"Unknown cron alias: {expression}")

        parts = expression.split()

        if len(parts) == 5:
            return dict(zip(cls.FIELD_NAMES, parts, strict=False))
        elif len(parts) == 6:
            return dict(zip(cls.FIELD_NAMES_6, parts, strict=False))
        else:
            raise ValueError(
                f"Invalid cron expression: {expression}. "
                f"Expected 5 or 6 fields, got {len(parts)}"
            )

    @classmethod
    def validate(cls, expression: str) -> tuple[bool, str | None]:
        """
        Validate a cron expression.

        Args:
            expression: Cron expression to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            cls.parse(expression)
            return True, None
        except ValueError as e:
            return False, str(e)

    @classmethod
    def to_human_readable(cls, expression: str) -> str:
        """
        Convert cron expression to human-readable description.

        Args:
            expression: Cron expression

        Returns:
            Human-readable description
        """
        expression = expression.strip()

        for alias, cron in CRON_ALIASES.items():
            if expression.lower() == alias or expression == cron:
                return cls._alias_to_description(alias)

        try:
            parts = cls.parse(expression)
        except ValueError:
            return f"Invalid expression: {expression}"

        return cls._build_description(parts)

    @classmethod
    def _alias_to_description(cls, alias: str) -> str:
        """Get description for cron alias."""
        descriptions = {
            "@yearly": "Once a year at midnight on January 1st",
            "@annually": "Once a year at midnight on January 1st",
            "@monthly": "Once a month at midnight on the 1st",
            "@weekly": "Once a week at midnight on Sunday",
            "@daily": "Once a day at midnight",
            "@midnight": "Once a day at midnight",
            "@hourly": "Once every hour",
            "@every_minute": "Every minute",
            "@every_5_minutes": "Every 5 minutes",
            "@every_10_minutes": "Every 10 minutes",
            "@every_15_minutes": "Every 15 minutes",
            "@every_30_minutes": "Every 30 minutes",
            "@business_hours": "Every hour during business hours (9-17) on weekdays",
            "@weekdays": "At 9 AM on weekdays",
            "@weekends": "At 9 AM on weekends",
            "@end_of_month": "At midnight on the last day of the month",
            "@first_monday": "At midnight on the first Monday of the month",
            "@last_friday": "At 5 PM on the last Friday of the month",
        }
        return descriptions.get(alias.lower(), f"Custom schedule: {alias}")

    @classmethod
    def _build_description(cls, parts: dict[str, str]) -> str:
        """Build description from parsed cron parts."""
        descriptions = []

        minute = parts.get("minute", "*")
        hour = parts.get("hour", "*")
        day = parts.get("day", "*")
        month = parts.get("month", "*")
        dow = parts.get("day_of_week", "*")

        if minute == "*" and hour == "*":
            descriptions.append("Every minute")
        elif minute.startswith("*/"):
            interval = minute[2:]
            descriptions.append(f"Every {interval} minutes")
        elif hour == "*":
            descriptions.append(f"At minute {minute} every hour")
        else:
            if hour.startswith("*/"):
                interval = hour[2:]
                descriptions.append(f"Every {interval} hours at minute {minute}")
            else:
                descriptions.append(f"At {hour}:{minute.zfill(2)}")

        if day != "*":
            if day == "L":
                descriptions.append("on the last day of the month")
            elif "#" in day:
                descriptions.append(f"on day pattern {day}")
            else:
                descriptions.append(f"on day {day}")

        if month != "*":
            month_names = [
                "Jan",
                "Feb",
                "Mar",
                "Apr",
                "May",
                "Jun",
                "Jul",
                "Aug",
                "Sep",
                "Oct",
                "Nov",
                "Dec",
            ]
            try:
                month_idx = int(month) - 1
                if 0 <= month_idx < 12:
                    descriptions.append(f"in {month_names[month_idx]}")
                else:
                    descriptions.append(f"in month {month}")
            except ValueError:
                descriptions.append(f"in month {month}")

        if dow != "*":
            day_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
            if dow == "1-5":
                descriptions.append("on weekdays")
            elif dow == "0,6":
                descriptions.append("on weekends")
            elif "L" in dow:
                descriptions.append(f"on last {dow.replace('L', '')} of month")
            elif "#" in dow:
                parts_dow = dow.split("#")
                if len(parts_dow) == 2:
                    try:
                        day_idx = int(parts_dow[0])
                        occurrence = parts_dow[1]
                        if 0 <= day_idx <= 6:
                            suffix = (
                                "st"
                                if occurrence == "1"
                                else "nd"
                                if occurrence == "2"
                                else "rd"
                                if occurrence == "3"
                                else "th"
                            )
                            descriptions.append(
                                f"on {occurrence}{suffix} {day_names[day_idx]} of month"
                            )
                    except ValueError:
                        descriptions.append(f"on {dow}")
            else:
                try:
                    day_idx = int(dow)
                    if 0 <= day_idx <= 6:
                        descriptions.append(f"on {day_names[day_idx]}")
                    else:
                        descriptions.append(f"on day {dow}")
                except ValueError:
                    descriptions.append(f"on {dow}")

        return " ".join(descriptions)

    @classmethod
    def get_available_aliases(cls) -> dict[str, str]:
        """Get all available cron aliases with descriptions."""
        result = {}
        for alias in CRON_ALIASES:
            result[alias] = cls._alias_to_description(alias)
        return result


class CronSchedulingStrategy(SchedulingStrategy):
    """
    Cron-based scheduling strategy.

    Uses APScheduler's CronTrigger under the hood.
    """

    def __init__(self, cron_expression: str, timezone: str = "UTC"):
        """
        Initialize cron strategy.

        Args:
            cron_expression: Cron expression or alias
            timezone: Timezone for schedule calculations
        """
        self._expression = cron_expression
        self._timezone = timezone
        self._parsed: dict[str, str] | None = None

    @property
    def expression(self) -> str:
        """Get the cron expression."""
        return self._expression

    @property
    def timezone(self) -> str:
        """Get the timezone."""
        return self._timezone

    def get_parsed(self) -> dict[str, str]:
        """Get parsed cron parameters."""
        if self._parsed is None:
            self._parsed = CronExpressionParser.parse(self._expression)
        return self._parsed

    def get_next_run_time(
        self,
        current_time: datetime,
        last_run: datetime | None = None,
    ) -> datetime | None:
        """Calculate next run time based on cron expression."""
        # Delegate to APScheduler's CronTrigger for actual calculation
        # This is a placeholder - actual implementation uses APScheduler
        return None

    def validate(self) -> tuple[bool, str | None]:
        """Validate the cron expression."""
        return CronExpressionParser.validate(self._expression)

    def to_human_readable(self) -> str:
        """Get human-readable description of this schedule."""
        return CronExpressionParser.to_human_readable(self._expression)


class IntervalSchedulingStrategy(SchedulingStrategy):
    """
    Interval-based scheduling strategy.

    Executes at fixed intervals.
    """

    def __init__(self, interval_seconds: int, timezone: str = "UTC"):
        """
        Initialize interval strategy.

        Args:
            interval_seconds: Interval between executions in seconds
            timezone: Timezone for schedule calculations
        """
        self._interval = interval_seconds
        self._timezone = timezone

    @property
    def interval_seconds(self) -> int:
        """Get the interval in seconds."""
        return self._interval

    @property
    def timezone(self) -> str:
        """Get the timezone."""
        return self._timezone

    def get_next_run_time(
        self,
        current_time: datetime,
        last_run: datetime | None = None,
    ) -> datetime | None:
        """Calculate next run time based on interval."""
        from datetime import timedelta

        if last_run is None:
            return current_time
        return last_run + timedelta(seconds=self._interval)

    def validate(self) -> tuple[bool, str | None]:
        """Validate the interval configuration."""
        if self._interval <= 0:
            return False, "Interval must be positive"
        return True, None

    def to_human_readable(self) -> str:
        """Get human-readable description of this schedule."""
        if self._interval < 60:
            return f"Every {self._interval} seconds"
        elif self._interval < 3600:
            minutes = self._interval // 60
            return f"Every {minutes} minute{'s' if minutes > 1 else ''}"
        elif self._interval < 86400:
            hours = self._interval // 3600
            return f"Every {hours} hour{'s' if hours > 1 else ''}"
        else:
            days = self._interval // 86400
            return f"Every {days} day{'s' if days > 1 else ''}"


class OneTimeSchedulingStrategy(SchedulingStrategy):
    """
    One-time scheduling strategy.

    Executes once at a specific datetime.
    """

    def __init__(self, run_at: datetime, timezone: str = "UTC"):
        """
        Initialize one-time strategy.

        Args:
            run_at: Datetime to execute at
            timezone: Timezone for schedule calculations
        """
        self._run_at = run_at
        self._timezone = timezone
        self._executed = False

    @property
    def run_at(self) -> datetime:
        """Get the scheduled run time."""
        return self._run_at

    @property
    def timezone(self) -> str:
        """Get the timezone."""
        return self._timezone

    def get_next_run_time(
        self,
        current_time: datetime,
        last_run: datetime | None = None,
    ) -> datetime | None:
        """Return the scheduled time if not yet executed."""
        if self._executed or last_run is not None:
            return None
        if self._run_at <= current_time:
            return None
        return self._run_at

    def mark_executed(self) -> None:
        """Mark this one-time schedule as executed."""
        self._executed = True

    def validate(self) -> tuple[bool, str | None]:
        """Validate the one-time configuration."""
        if self._run_at is None:
            return False, "Run time must be specified"
        return True, None

    def to_human_readable(self) -> str:
        """Get human-readable description of this schedule."""
        return f"Once at {self._run_at.isoformat()}"


class EventDrivenStrategy(SchedulingStrategy):
    """
    Event-driven scheduling strategy.

    Executes when specific events occur.
    """

    def __init__(
        self,
        event_type: str,
        event_source: str,
        event_filter: dict[str, Any] | None = None,
    ):
        """
        Initialize event-driven strategy.

        Args:
            event_type: Type of event to trigger on
            event_source: Source identifier for events
            event_filter: Optional filter for event data
        """
        self._event_type = event_type
        self._event_source = event_source
        self._event_filter = event_filter or {}

    @property
    def event_type(self) -> str:
        """Get the event type."""
        return self._event_type

    @property
    def event_source(self) -> str:
        """Get the event source."""
        return self._event_source

    @property
    def event_filter(self) -> dict[str, Any]:
        """Get the event filter."""
        return self._event_filter

    def get_next_run_time(
        self,
        current_time: datetime,
        last_run: datetime | None = None,
    ) -> datetime | None:
        """Event-driven schedules don't have a predetermined next run time."""
        return None

    def validate(self) -> tuple[bool, str | None]:
        """Validate the event-driven configuration."""
        if not self._event_type:
            return False, "Event type must be specified"
        if not self._event_source:
            return False, "Event source must be specified"
        return True, None

    def to_human_readable(self) -> str:
        """Get human-readable description of this schedule."""
        return f"On {self._event_type} event from {self._event_source}"


class DependencySchedulingStrategy(SchedulingStrategy):
    """
    Dependency-based scheduling strategy.

    Executes when dependencies are satisfied (DAG execution).
    """

    def __init__(
        self,
        depends_on: list,
        wait_for_all: bool = True,
        trigger_on_success_only: bool = True,
    ):
        """
        Initialize dependency strategy.

        Args:
            depends_on: List of schedule IDs this depends on
            wait_for_all: Whether to wait for all dependencies
            trigger_on_success_only: Only trigger if dependencies succeeded
        """
        self._depends_on = depends_on
        self._wait_for_all = wait_for_all
        self._trigger_on_success_only = trigger_on_success_only

    @property
    def depends_on(self) -> list:
        """Get the dependency list."""
        return self._depends_on

    @property
    def wait_for_all(self) -> bool:
        """Check if waiting for all dependencies."""
        return self._wait_for_all

    @property
    def trigger_on_success_only(self) -> bool:
        """Check if only triggering on success."""
        return self._trigger_on_success_only

    def get_next_run_time(
        self,
        current_time: datetime,
        last_run: datetime | None = None,
    ) -> datetime | None:
        """Dependency schedules don't have a predetermined next run time."""
        return None

    def validate(self) -> tuple[bool, str | None]:
        """Validate the dependency configuration."""
        if not self._depends_on:
            return False, "At least one dependency must be specified"
        return True, None

    def to_human_readable(self) -> str:
        """Get human-readable description of this schedule."""
        mode = "all" if self._wait_for_all else "any"
        deps = ", ".join(self._depends_on[:3])
        if len(self._depends_on) > 3:
            deps += f" (+{len(self._depends_on) - 3} more)"
        return f"After {mode} of: {deps}"
