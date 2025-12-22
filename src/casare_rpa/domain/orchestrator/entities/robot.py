"""Robot domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any, Set

from casare_rpa.utils.datetime_helpers import parse_datetime


class RobotStatus(Enum):
    """Robot connection status."""

    OFFLINE = "offline"
    ONLINE = "online"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class RobotCapability(Enum):
    """Robot capabilities for workload routing."""

    BROWSER = "browser"  # Can run browser automation (Playwright)
    DESKTOP = "desktop"  # Can run desktop automation (UIAutomation)
    GPU = "gpu"  # Has GPU for ML workloads
    HIGH_MEMORY = "high_memory"  # Has high memory for large data processing
    SECURE = "secure"  # In secure network zone
    CLOUD = "cloud"  # Cloud-hosted robot
    ON_PREMISE = "on_premise"  # On-premise robot


@dataclass
class Robot:
    """Robot agent domain entity with behavior and invariants.

    Robots can be assigned to workflows (default robot for a workflow) and can
    handle multiple concurrent jobs up to their max_concurrent_jobs limit.
    """

    id: str
    name: str
    status: RobotStatus = RobotStatus.OFFLINE
    environment: str = "default"
    max_concurrent_jobs: int = 1
    last_seen: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None
    created_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    # Robot capabilities for workload routing
    capabilities: Set[RobotCapability] = field(default_factory=set)
    # Workflow assignments - workflows this robot is default for
    assigned_workflows: List[str] = field(default_factory=list)
    # Current jobs being executed (job IDs)
    current_job_ids: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate domain invariants after initialization."""
        if not self.id or not self.id.strip():
            raise ValueError("Robot ID cannot be empty")
        if not self.name or not self.name.strip():
            raise ValueError("Robot name cannot be empty")
        if self.max_concurrent_jobs < 0:
            raise ValueError(f"max_concurrent_jobs must be >= 0, got {self.max_concurrent_jobs}")
        if len(self.current_job_ids) > self.max_concurrent_jobs:
            raise ValueError(
                f"current_job_ids count ({len(self.current_job_ids)}) cannot exceed "
                f"max_concurrent_jobs ({self.max_concurrent_jobs})"
            )

    @property
    def current_jobs(self) -> int:
        """Get count of current jobs (backward compatibility).

        Returns:
            Number of jobs currently assigned to this robot.
        """
        return len(self.current_job_ids)

    @property
    def is_available(self) -> bool:
        """Check if robot can accept new jobs.

        Returns:
            True if robot is online and has capacity for more jobs.
        """
        return self.status == RobotStatus.ONLINE and self.current_jobs < self.max_concurrent_jobs

    @property
    def utilization(self) -> float:
        """Get robot utilization percentage.

        Returns:
            Percentage of capacity currently in use (0-100).
        """
        if self.max_concurrent_jobs == 0:
            return 0.0
        return (self.current_jobs / self.max_concurrent_jobs) * 100

    def can_accept_job(self) -> bool:
        """Check if robot can accept a new job.

        Same as is_available but with clearer naming for job assignment context.

        Returns:
            True if robot is online and has capacity.
        """
        return self.is_available

    def has_capability(self, capability: RobotCapability) -> bool:
        """Check if robot has a specific capability.

        Args:
            capability: Capability to check for.

        Returns:
            True if robot has the capability.
        """
        return capability in self.capabilities

    def has_all_capabilities(self, capabilities: Set[RobotCapability]) -> bool:
        """Check if robot has all specified capabilities.

        Args:
            capabilities: Set of capabilities to check for.

        Returns:
            True if robot has all specified capabilities.
        """
        return capabilities.issubset(self.capabilities)

    def assign_job(self, job_id: str) -> None:
        """Assign a job to this robot.

        Args:
            job_id: ID of the job to assign.

        Raises:
            RobotUnavailableError: If robot is not in ONLINE status.
            RobotAtCapacityError: If robot is at max concurrent jobs.
            DuplicateJobAssignmentError: If job is already assigned to this robot.
        """
        from casare_rpa.domain.orchestrator.errors import (
            DuplicateJobAssignmentError,
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

        if job_id in self.current_job_ids:
            raise DuplicateJobAssignmentError(
                f"Job {job_id} is already assigned to robot {self.id}"
            )

        self.current_job_ids.append(job_id)

    def complete_job(self, job_id: str) -> None:
        """Mark a job as completed on this robot.

        Args:
            job_id: ID of the completed job.

        Raises:
            InvalidRobotStateError: If job is not assigned to this robot.
        """
        from casare_rpa.domain.orchestrator.errors import InvalidRobotStateError

        if job_id not in self.current_job_ids:
            raise InvalidRobotStateError(f"Job {job_id} is not assigned to robot {self.id}")

        self.current_job_ids.remove(job_id)

    def assign_workflow(self, workflow_id: str) -> None:
        """Assign this robot as default for a workflow.

        Args:
            workflow_id: ID of the workflow to assign.
        """
        if workflow_id not in self.assigned_workflows:
            self.assigned_workflows.append(workflow_id)

    def unassign_workflow(self, workflow_id: str) -> None:
        """Remove workflow assignment from this robot.

        Args:
            workflow_id: ID of the workflow to unassign.
        """
        if workflow_id in self.assigned_workflows:
            self.assigned_workflows.remove(workflow_id)

    def is_assigned_to_workflow(self, workflow_id: str) -> bool:
        """Check if robot is assigned to a workflow.

        Args:
            workflow_id: ID of the workflow to check.

        Returns:
            True if robot is assigned to the workflow.
        """
        return workflow_id in self.assigned_workflows

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

        # Convert string capabilities to enum
        raw_capabilities = data.get("capabilities", [])
        capabilities: Set[RobotCapability] = set()
        for cap in raw_capabilities:
            if isinstance(cap, str):
                try:
                    capabilities.add(RobotCapability(cap))
                except ValueError:
                    pass  # Skip unknown capabilities
            elif isinstance(cap, RobotCapability):
                capabilities.add(cap)

        # Handle backward compatibility for current_jobs field
        current_job_ids = data.get("current_job_ids", [])
        if not current_job_ids and data.get("current_jobs", 0) > 0:
            # Legacy data had count, generate placeholder IDs
            current_job_ids = [f"legacy_job_{i}" for i in range(data["current_jobs"])]

        return cls(
            id=data["id"],
            name=data["name"],
            status=status,
            environment=data.get("environment", "default"),
            max_concurrent_jobs=data.get("max_concurrent_jobs", 1),
            last_seen=parse_datetime(data.get("last_seen")),
            last_heartbeat=parse_datetime(data.get("last_heartbeat")),
            created_at=parse_datetime(data.get("created_at")),
            tags=data.get("tags", []),
            metrics=data.get("metrics", {}),
            capabilities=capabilities,
            assigned_workflows=data.get("assigned_workflows", []),
            current_job_ids=current_job_ids,
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
            "current_jobs": self.current_jobs,  # For backward compatibility
            "current_job_ids": self.current_job_ids,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "tags": self.tags,
            "metrics": self.metrics,
            "capabilities": [cap.value for cap in self.capabilities],
            "assigned_workflows": self.assigned_workflows,
        }
