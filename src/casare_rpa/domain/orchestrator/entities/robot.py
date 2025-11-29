"""Robot domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any


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

    def is_available(self) -> bool:
        """Check if robot can accept new jobs.

        Returns:
            True if robot is online and has capacity for more jobs.
        """
        return (
            self.status == RobotStatus.ONLINE
            and self.current_jobs < self.max_concurrent_jobs
        )

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
