"""Schedule domain entity."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from .job import JobPriority


class ScheduleFrequency(Enum):
    """Schedule frequency types."""

    ONCE = "once"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CRON = "cron"


@dataclass
class Schedule:
    """Workflow schedule domain entity."""

    id: str
    name: str
    workflow_id: str
    workflow_name: str = ""
    robot_id: Optional[str] = None  # None = any available robot
    robot_name: str = ""
    frequency: ScheduleFrequency = ScheduleFrequency.DAILY
    cron_expression: str = ""
    timezone: str = "UTC"
    enabled: bool = True
    priority: JobPriority = JobPriority.NORMAL
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    success_count: int = 0
    created_at: Optional[datetime] = None
    created_by: str = ""

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage.

        Returns:
            Success rate as percentage (0-100).
        """
        if self.run_count == 0:
            return 0.0
        return (self.success_count / self.run_count) * 100
