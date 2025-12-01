"""Robot domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any

from casare_rpa.utils.datetime_helpers import parse_datetime


class RobotStatus(Enum):
    """Robot connection status."""

    OFFLINE = "offline"
    ONLINE = "online"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"


@dataclass
class Robot:
    """Robot agent domain entity with behavior and invariants."""

    id: str
    name: str
    status: RobotStatus = RobotStatus.OFFLINE
    environment: str = "default"
    max_concurrent_jobs: int = 1
    current_jobs: int = 0
    last_seen: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None
    created_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate domain invariants after initialization."""
        if not self.id or not self.id.strip():
            raise ValueError("Robot ID cannot be empty")
        if not self.name or not self.name.strip():
            raise ValueError("Robot name cannot be empty")
        if self.max_concurrent_jobs < 0:
            raise ValueError(
                f"max_concurrent_jobs must be >= 0, got {self.max_concurrent_jobs}"
            )
        if self.current_jobs < 0:
            raise ValueError(f"current_jobs must be >= 0, got {self.current_jobs}")
        if self.current_jobs > self.max_concurrent_jobs:
            raise ValueError(
                f"current_jobs ({self.current_jobs}) cannot exceed "
                f"max_concurrent_jobs ({self.max_concurrent_jobs})"
            )

    @property
    def is_available(self) -> bool:
        """Check if robot can accept new jobs.

        Returns:
            True if robot is online and has capacity for more jobs.
        """
        return (
            self.status == RobotStatus.ONLINE
            and self.current_jobs < self.max_concurrent_jobs
        )

    @property
    def utilization(self) -> float:
        """Get robot utilization percentage.

        Returns:
            Percentage of capacity currently in use (0-100).
        """
        if self.max_concurrent_jobs == 0:
            return 0.0
        return (self.current_jobs / self.max_concurrent_jobs) * 100

    def assign_job(self, job_id: str) -> None:
        """Assign a job to this robot.

        Args:
            job_id: ID of the job to assign.

        Raises:
            RobotUnavailableError: If robot is not in ONLINE status.
            RobotAtCapacityError: If robot is at max concurrent jobs.
        """
        from casare_rpa.domain.orchestrator.errors import (
            RobotAtCapacityError,
            RobotUnavailableError,
        )

        if self.status != RobotStatus.ONLINE:
            raise RobotUnavailableError(
                f"Robot {self.id} is not online (status: {self.status.value})"
            )

        if self.current_jobs >= self.max_concurrent_jobs:
            raise RobotAtCapacityError(
                f"Robot {self.id} is at capacity ({self.current_jobs}/{self.max_concurrent_jobs})"
            )

        self.current_jobs += 1

    def complete_job(self, job_id: str) -> None:
        """Mark a job as completed on this robot.

        Args:
            job_id: ID of the completed job.

        Raises:
            InvalidRobotStateError: If no jobs are currently running.
        """
        from casare_rpa.domain.orchestrator.errors import InvalidRobotStateError

        if self.current_jobs == 0:
            raise InvalidRobotStateError(
                f"Robot {self.id} has no jobs to complete (current_jobs: 0)"
            )

        self.current_jobs -= 1

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Robot":
        """Create Robot from dictionary.

        Args:
            data: Dictionary with robot data.

        Returns:
            Robot instance.
        """
        # Convert string status to enum
        status = data.get("status")
        if isinstance(status, str):
            status = RobotStatus(status)
        elif isinstance(status, RobotStatus):
            pass
        else:
            status = RobotStatus.OFFLINE

        return cls(
            id=data["id"],
            name=data["name"],
            status=status,
            environment=data.get("environment", "default"),
            max_concurrent_jobs=data.get("max_concurrent_jobs", 1),
            current_jobs=data.get("current_jobs", 0),
            last_seen=parse_datetime(data.get("last_seen")),
            last_heartbeat=parse_datetime(data.get("last_heartbeat")),
            created_at=parse_datetime(data.get("created_at")),
            tags=data.get("tags", []),
            metrics=data.get("metrics", {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert Robot to dictionary.

        Returns:
            Dictionary representation of robot.
        """
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "environment": self.environment,
            "max_concurrent_jobs": self.max_concurrent_jobs,
            "current_jobs": self.current_jobs,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "last_heartbeat": self.last_heartbeat.isoformat()
            if self.last_heartbeat
            else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "tags": self.tags,
            "metrics": self.metrics,
        }
