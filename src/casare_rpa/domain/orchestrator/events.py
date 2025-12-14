"""
CasareRPA - Orchestrator Domain Events

Typed domain events for orchestrator operations (robot management, job lifecycle).
All events are immutable frozen dataclasses following DDD 2025 patterns.

Usage:
    from casare_rpa.domain.orchestrator.events import RobotRegistered, get_event_bus

    bus = get_event_bus()
    bus.subscribe(RobotRegistered, handler)
    bus.publish(RobotRegistered(robot_id="x", robot_name="Bot-1"))
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from casare_rpa.domain.events.base import DomainEvent


# =============================================================================
# Robot Events
# =============================================================================


@dataclass(frozen=True)
class RobotRegistered(DomainEvent):
    """Robot connected and registered with orchestrator.

    Published when a robot establishes a WebSocket connection and
    completes the registration handshake.
    """

    robot_id: str = ""
    robot_name: str = ""
    hostname: str = ""
    environment: str = "production"
    capabilities: Tuple[str, ...] = ()
    max_concurrent_jobs: int = 1
    tenant_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize event to dictionary."""
        result = super().to_dict()
        result.update(
            {
                "robot_id": self.robot_id,
                "robot_name": self.robot_name,
                "hostname": self.hostname,
                "environment": self.environment,
                "capabilities": list(self.capabilities),
                "max_concurrent_jobs": self.max_concurrent_jobs,
                "tenant_id": self.tenant_id,
            }
        )
        return result


@dataclass(frozen=True)
class RobotDisconnected(DomainEvent):
    """Robot disconnected from orchestrator.

    Published when a robot's WebSocket connection is closed.
    Includes orphaned job IDs that need to be requeued.
    """

    robot_id: str = ""
    robot_name: str = ""
    orphaned_job_ids: Tuple[str, ...] = ()
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize event to dictionary."""
        result = super().to_dict()
        result.update(
            {
                "robot_id": self.robot_id,
                "robot_name": self.robot_name,
                "orphaned_job_ids": list(self.orphaned_job_ids),
                "reason": self.reason,
            }
        )
        return result


@dataclass(frozen=True)
class RobotHeartbeat(DomainEvent):
    """Robot sent a heartbeat with metrics.

    Published on each heartbeat from a connected robot.
    Contains system metrics for monitoring.
    """

    robot_id: str = ""
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    current_job_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize event to dictionary."""
        result = super().to_dict()
        result.update(
            {
                "robot_id": self.robot_id,
                "cpu_percent": self.cpu_percent,
                "memory_mb": self.memory_mb,
                "current_job_count": self.current_job_count,
            }
        )
        return result


@dataclass(frozen=True)
class RobotStatusChanged(DomainEvent):
    """Robot status changed (online/offline/busy/maintenance).

    Published when a robot's status transitions between states.
    """

    robot_id: str = ""
    old_status: str = ""
    new_status: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize event to dictionary."""
        result = super().to_dict()
        result.update(
            {
                "robot_id": self.robot_id,
                "old_status": self.old_status,
                "new_status": self.new_status,
            }
        )
        return result


# =============================================================================
# Job Events (Orchestrator-side)
# =============================================================================


@dataclass(frozen=True)
class JobSubmitted(DomainEvent):
    """Job submitted to orchestrator queue.

    Published when a new job is enqueued for execution.
    """

    job_id: str = ""
    workflow_id: str = ""
    workflow_name: str = ""
    priority: int = 5
    target_robot_id: str = ""
    tenant_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize event to dictionary."""
        result = super().to_dict()
        result.update(
            {
                "job_id": self.job_id,
                "workflow_id": self.workflow_id,
                "workflow_name": self.workflow_name,
                "priority": self.priority,
                "target_robot_id": self.target_robot_id,
                "tenant_id": self.tenant_id,
            }
        )
        return result


@dataclass(frozen=True)
class JobAssigned(DomainEvent):
    """Job assigned to a robot for execution.

    Published when orchestrator assigns a pending job to an available robot.
    """

    job_id: str = ""
    robot_id: str = ""
    robot_name: str = ""
    workflow_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize event to dictionary."""
        result = super().to_dict()
        result.update(
            {
                "job_id": self.job_id,
                "robot_id": self.robot_id,
                "robot_name": self.robot_name,
                "workflow_id": self.workflow_id,
            }
        )
        return result


@dataclass(frozen=True)
class JobRequeued(DomainEvent):
    """Job requeued after robot rejection or disconnect.

    Published when a job is returned to the queue for reassignment.
    """

    job_id: str = ""
    previous_robot_id: str = ""
    reason: str = ""
    rejected_by_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize event to dictionary."""
        result = super().to_dict()
        result.update(
            {
                "job_id": self.job_id,
                "previous_robot_id": self.previous_robot_id,
                "reason": self.reason,
                "rejected_by_count": self.rejected_by_count,
            }
        )
        return result


@dataclass(frozen=True)
class JobCompletedOnOrchestrator(DomainEvent):
    """Job completed notification received by orchestrator.

    Published when orchestrator receives job completion from robot.
    """

    job_id: str = ""
    robot_id: str = ""
    success: bool = True
    execution_time_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize event to dictionary."""
        result = super().to_dict()
        result.update(
            {
                "job_id": self.job_id,
                "robot_id": self.robot_id,
                "success": self.success,
                "execution_time_ms": self.execution_time_ms,
            }
        )
        return result


@dataclass(frozen=True)
class JobMovedToDLQ(DomainEvent):
    """Job moved to Dead Letter Queue after exhausting retries.

    Published when a job fails and cannot be retried.
    """

    job_id: str = ""
    workflow_id: str = ""
    error_message: str = ""
    retry_count: int = 0
    max_retries: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize event to dictionary."""
        result = super().to_dict()
        result.update(
            {
                "job_id": self.job_id,
                "workflow_id": self.workflow_id,
                "error_message": self.error_message,
                "retry_count": self.retry_count,
                "max_retries": self.max_retries,
            }
        )
        return result


__all__ = [
    # Robot events
    "RobotRegistered",
    "RobotDisconnected",
    "RobotHeartbeat",
    "RobotStatusChanged",
    # Job events
    "JobSubmitted",
    "JobAssigned",
    "JobRequeued",
    "JobCompletedOnOrchestrator",
    "JobMovedToDLQ",
]
