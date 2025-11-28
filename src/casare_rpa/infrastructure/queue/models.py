"""
Job Queue Data Models.

Defines the data structures for jobs in the PgQueuer-based queue system.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from casare_rpa.domain.value_objects.types import NodeId


class JobStatus(str, Enum):
    """Job status in the queue."""

    PENDING = "pending"  # Waiting in queue
    CLAIMED = "claimed"  # Claimed by a robot (visibility timeout active)
    RUNNING = "running"  # Currently executing
    COMPLETED = "completed"  # Successfully completed
    FAILED = "failed"  # Failed (moved to DLQ after max retries)
    CANCELLED = "cancelled"  # Cancelled by user/system


class JobPriority(int, Enum):
    """Job priority levels (higher = more urgent)."""

    LOW = 0
    NORMAL = 5
    HIGH = 10
    URGENT = 15
    CRITICAL = 20


class JobModel(BaseModel):
    """
    Job model for PgQueuer.

    Represents a workflow execution job in the queue.

    Attributes:
        job_id: Unique job identifier
        workflow_json: Serialized workflow JSON
        priority: Job priority (0-20, higher = more urgent)
        tenant_id: Tenant identifier for multi-tenancy
        status: Current job status
        created_at: Job creation timestamp
        claimed_at: When job was claimed by a robot
        completed_at: When job finished (success or failure)
        claimed_by: Robot ID that claimed the job
        retry_count: Number of retry attempts
        max_retries: Maximum retry attempts before DLQ
        visibility_timeout: Seconds before claimed job becomes visible again
        error_message: Error message if failed
        workflow_name: Workflow name for monitoring
        tags: Custom tags for filtering/grouping
    """

    job_id: str = Field(..., description="Unique job identifier")
    workflow_json: str = Field(..., description="Serialized workflow JSON")
    priority: int = Field(
        default=JobPriority.NORMAL,
        ge=0,
        le=20,
        description="Job priority (0-20)",
    )
    tenant_id: Optional[str] = Field(None, description="Tenant ID for multi-tenancy")
    status: JobStatus = Field(
        default=JobStatus.PENDING,
        description="Current job status",
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Job creation timestamp",
    )
    claimed_at: Optional[datetime] = Field(
        None,
        description="When job was claimed",
    )
    completed_at: Optional[datetime] = Field(
        None,
        description="When job finished",
    )

    # Execution tracking
    claimed_by: Optional[str] = Field(None, description="Robot ID that claimed job")
    retry_count: int = Field(default=0, description="Number of retries")
    max_retries: int = Field(default=3, description="Max retries before DLQ")
    visibility_timeout: int = Field(
        default=30,
        description="Visibility timeout in seconds",
    )

    # Error handling
    error_message: Optional[str] = Field(None, description="Error message if failed")
    last_error: Optional[str] = Field(None, description="Most recent error")

    # Metadata
    workflow_name: Optional[str] = Field(None, description="Workflow name")
    workflow_id: Optional[str] = Field(None, description="Workflow instance ID")
    tags: Dict[str, str] = Field(
        default_factory=dict,
        description="Custom tags",
    )

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
        use_enum_values = True

    def to_pgqueuer_payload(self) -> Dict[str, Any]:
        """
        Convert to PgQueuer payload format.

        Returns:
            Dictionary suitable for PgQueuer.enqueue()
        """
        return {
            "job_id": self.job_id,
            "workflow_json": self.workflow_json,
            "priority": self.priority,
            "tenant_id": self.tenant_id,
            "workflow_name": self.workflow_name,
            "workflow_id": self.workflow_id,
            "max_retries": self.max_retries,
            "tags": self.tags,
        }

    @classmethod
    def from_pgqueuer_payload(cls, payload: Dict[str, Any]) -> "JobModel":
        """
        Create JobModel from PgQueuer payload.

        Args:
            payload: PgQueuer job payload

        Returns:
            JobModel instance
        """
        return cls(**payload)

    def mark_claimed(self, robot_id: str) -> None:
        """
        Mark job as claimed by a robot.

        Args:
            robot_id: ID of robot claiming the job
        """
        self.status = JobStatus.CLAIMED
        self.claimed_by = robot_id
        self.claimed_at = datetime.now(timezone.utc)

    def mark_running(self) -> None:
        """Mark job as running."""
        self.status = JobStatus.RUNNING

    def mark_completed(self) -> None:
        """Mark job as successfully completed."""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)

    def mark_failed(self, error: str) -> None:
        """
        Mark job as failed.

        Args:
            error: Error message
        """
        self.status = JobStatus.FAILED
        self.error_message = error
        self.last_error = error
        self.completed_at = datetime.now(timezone.utc)
        self.retry_count += 1

    def mark_cancelled(self, reason: Optional[str] = None) -> None:
        """
        Mark job as cancelled.

        Args:
            reason: Cancellation reason
        """
        self.status = JobStatus.CANCELLED
        self.error_message = reason
        self.completed_at = datetime.now(timezone.utc)

    def should_retry(self) -> bool:
        """
        Check if job should be retried.

        Returns:
            True if retry count < max retries
        """
        return self.retry_count < self.max_retries

    def is_expired(self) -> bool:
        """
        Check if claimed job has exceeded visibility timeout.

        Returns:
            True if job claim has expired
        """
        if not self.claimed_at or self.status != JobStatus.CLAIMED:
            return False

        now = datetime.now(timezone.utc)
        elapsed = (now - self.claimed_at).total_seconds()
        return elapsed > self.visibility_timeout


class DeadLetterQueueEntry(BaseModel):
    """
    Entry in the Dead Letter Queue.

    Jobs that exceed max retries are moved here for manual intervention.
    """

    job: JobModel
    moved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When moved to DLQ",
    )
    reason: str = Field(..., description="Reason for DLQ")
    retry_history: list[str] = Field(
        default_factory=list,
        description="History of retry errors",
    )
