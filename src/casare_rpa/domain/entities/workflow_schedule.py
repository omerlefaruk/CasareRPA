"""
WorkflowSchedule domain entity.

Represents a schedule for executing a workflow at specified times.
Pure domain logic - no UI or infrastructure dependencies.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any

from casare_rpa.utils.datetime_helpers import parse_datetime


class ScheduleFrequency(str, Enum):
    """Schedule frequency types."""

    ONCE = "once"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CRON = "cron"


@dataclass
class WorkflowSchedule:
    """
    Workflow schedule entity.

    Represents a schedule configuration for running a workflow
    at specified times (once, hourly, daily, weekly, monthly, or cron).
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    workflow_path: str = ""
    workflow_name: str = ""
    frequency: str = ScheduleFrequency.DAILY
    cron_expression: str = ""
    time_hour: int = 9
    time_minute: int = 0
    day_of_week: int = 0  # 0=Monday
    day_of_month: int = 1
    timezone: str = "local"
    enabled: bool = True
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    run_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    created_at: Optional[datetime] = field(default_factory=datetime.now)
    last_error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "workflow_path": self.workflow_path,
            "workflow_name": self.workflow_name,
            "frequency": self.frequency,
            "cron_expression": self.cron_expression,
            "time_hour": self.time_hour,
            "time_minute": self.time_minute,
            "day_of_week": self.day_of_week,
            "day_of_month": self.day_of_month,
            "timezone": self.timezone,
            "enabled": self.enabled,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "run_count": self.run_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_error": self.last_error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowSchedule":
        """Create from dictionary."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            workflow_path=data.get("workflow_path", ""),
            workflow_name=data.get("workflow_name", ""),
            frequency=data.get("frequency", ScheduleFrequency.DAILY),
            cron_expression=data.get("cron_expression", ""),
            time_hour=data.get("time_hour", 9),
            time_minute=data.get("time_minute", 0),
            day_of_week=data.get("day_of_week", 0),
            day_of_month=data.get("day_of_month", 1),
            timezone=data.get("timezone", "local"),
            enabled=data.get("enabled", True),
            next_run=parse_datetime(data.get("next_run")),
            last_run=parse_datetime(data.get("last_run")),
            run_count=data.get("run_count", 0),
            success_count=data.get("success_count", 0),
            failure_count=data.get("failure_count", 0),
            created_at=parse_datetime(data.get("created_at")),
            last_error=data.get("last_error", ""),
        )

    def calculate_next_run(
        self, from_time: Optional[datetime] = None
    ) -> Optional[datetime]:
        """Calculate the next run time based on frequency."""
        now = from_time or datetime.now()

        if self.frequency == ScheduleFrequency.ONCE:
            # For one-time, next_run should already be set
            return self.next_run if self.next_run and self.next_run > now else None

        elif self.frequency == ScheduleFrequency.HOURLY:
            # Next hour at the specified minute
            next_run = now.replace(minute=self.time_minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(hours=1)
            return next_run

        elif self.frequency == ScheduleFrequency.DAILY:
            # Today or tomorrow at the specified time
            next_run = now.replace(
                hour=self.time_hour, minute=self.time_minute, second=0, microsecond=0
            )
            if next_run <= now:
                next_run += timedelta(days=1)
            return next_run

        elif self.frequency == ScheduleFrequency.WEEKLY:
            # Calculate days until the target weekday
            days_ahead = self.day_of_week - now.weekday()
            if days_ahead < 0:  # Target day already passed this week
                days_ahead += 7

            next_run = now.replace(
                hour=self.time_hour, minute=self.time_minute, second=0, microsecond=0
            ) + timedelta(days=days_ahead)

            if next_run <= now:
                next_run += timedelta(weeks=1)
            return next_run

        elif self.frequency == ScheduleFrequency.MONTHLY:
            # Next occurrence of the specified day of month
            next_run = now.replace(
                day=min(self.day_of_month, 28),  # Safe day
                hour=self.time_hour,
                minute=self.time_minute,
                second=0,
                microsecond=0,
            )
            if next_run <= now:
                # Move to next month
                if now.month == 12:
                    next_run = next_run.replace(year=now.year + 1, month=1)
                else:
                    next_run = next_run.replace(month=now.month + 1)
            return next_run

        elif self.frequency == ScheduleFrequency.CRON:
            # Cron parsing would require APScheduler
            # For now, return None - the scheduler service will handle this
            return None

        return None

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.run_count == 0:
            return 0.0
        return (self.success_count / self.run_count) * 100

    @property
    def frequency_display(self) -> str:
        """Get human-readable frequency string."""
        if self.frequency == ScheduleFrequency.ONCE:
            if self.next_run:
                return f"Once at {self.next_run.strftime('%Y-%m-%d %H:%M')}"
            return "Once"
        elif self.frequency == ScheduleFrequency.HOURLY:
            return f"Hourly at :{self.time_minute:02d}"
        elif self.frequency == ScheduleFrequency.DAILY:
            return f"Daily at {self.time_hour:02d}:{self.time_minute:02d}"
        elif self.frequency == ScheduleFrequency.WEEKLY:
            days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            return f"Weekly on {days[self.day_of_week]} at {self.time_hour:02d}:{self.time_minute:02d}"
        elif self.frequency == ScheduleFrequency.MONTHLY:
            return f"Monthly on day {self.day_of_month} at {self.time_hour:02d}:{self.time_minute:02d}"
        elif self.frequency == ScheduleFrequency.CRON:
            return f"Cron: {self.cron_expression}"
        return self.frequency
