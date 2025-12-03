"""Schedule domain entity."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

from casare_rpa.domain.orchestrator.entities.job import JobPriority
from casare_rpa.utils.datetime_helpers import parse_datetime


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

    def __post_init__(self):
        """Validate domain invariants after initialization."""
        if not self.id or not self.id.strip():
            raise ValueError("Schedule ID cannot be empty")
        if not self.name or not self.name.strip():
            raise ValueError("Schedule name cannot be empty")
        if not self.workflow_id or not self.workflow_id.strip():
            raise ValueError("Workflow ID cannot be empty")
        if self.run_count < 0:
            raise ValueError(f"Run count must be >= 0, got {self.run_count}")
        if self.success_count < 0:
            raise ValueError(f"Success count must be >= 0, got {self.success_count}")
        if self.success_count > self.run_count:
            raise ValueError(
                f"Success count ({self.success_count}) cannot exceed "
                f"run count ({self.run_count})"
            )

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage.

        Returns:
            Success rate as percentage (0-100).
        """
        if self.run_count == 0:
            return 0.0
        return (self.success_count / self.run_count) * 100

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Schedule":
        """Create Schedule from dictionary.

        Args:
            data: Dictionary with schedule data.

        Returns:
            Schedule instance.
        """
        # Convert string enums to enum instances
        frequency = data.get("frequency")
        if isinstance(frequency, str):
            frequency = ScheduleFrequency(frequency)
        elif isinstance(frequency, ScheduleFrequency):
            pass
        else:
            frequency = ScheduleFrequency.DAILY

        priority = data.get("priority")
        if isinstance(priority, str):
            priority = JobPriority[priority.upper()]
        elif isinstance(priority, int):
            priority = JobPriority(priority)
        elif isinstance(priority, JobPriority):
            pass
        else:
            priority = JobPriority.NORMAL

        return cls(
            id=data["id"],
            name=data["name"],
            workflow_id=data["workflow_id"],
            workflow_name=data.get("workflow_name", ""),
            robot_id=data.get("robot_id"),
            robot_name=data.get("robot_name", ""),
            frequency=frequency,
            cron_expression=data.get("cron_expression", ""),
            timezone=data.get("timezone", "UTC"),
            enabled=data.get("enabled", True),
            priority=priority,
            last_run=parse_datetime(data.get("last_run")),
            next_run=parse_datetime(data.get("next_run")),
            run_count=data.get("run_count", 0),
            success_count=data.get("success_count", 0),
            created_at=parse_datetime(data.get("created_at")),
            created_by=data.get("created_by", ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert Schedule to dictionary.

        Returns:
            Dictionary representation of schedule.
        """
        return {
            "id": self.id,
            "name": self.name,
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "robot_id": self.robot_id,
            "robot_name": self.robot_name,
            "frequency": self.frequency.value,
            "cron_expression": self.cron_expression,
            "timezone": self.timezone,
            "enabled": self.enabled,
            "priority": self.priority.value,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "run_count": self.run_count,
            "success_count": self.success_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by,
        }
