"""
CasareRPA - Workflow Execution Events

Typed domain events for workflow execution lifecycle.
Replaces EventType.WORKFLOW_* enum values with typed classes.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from casare_rpa.domain.events.base import DomainEvent
from casare_rpa.domain.value_objects.types import ErrorCode, ExecutionMode


@dataclass(frozen=True)
class WorkflowStarted(DomainEvent):
    """
    Event raised when a workflow begins execution.

    Attributes:
        workflow_id: Unique identifier of the workflow
        workflow_name: Display name of the workflow
        execution_mode: How the workflow is being executed (NORMAL, DEBUG, etc.)
        triggered_by: What triggered the execution (manual, schedule, api, etc.)
        total_nodes: Total number of nodes in the workflow
    """

    workflow_id: str = ""
    workflow_name: str = ""
    execution_mode: ExecutionMode = ExecutionMode.NORMAL
    triggered_by: str = "manual"
    total_nodes: int = 0

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update(
            {
                "workflow_id": self.workflow_id,
                "workflow_name": self.workflow_name,
                "execution_mode": self.execution_mode.name,
                "triggered_by": self.triggered_by,
                "total_nodes": self.total_nodes,
            }
        )
        return result


@dataclass(frozen=True)
class WorkflowCompleted(DomainEvent):
    """
    Event raised when a workflow completes execution successfully.

    Attributes:
        workflow_id: Unique identifier of the workflow
        workflow_name: Display name of the workflow
        execution_time_ms: Total execution time in milliseconds
        nodes_executed: Number of nodes that were executed
        nodes_skipped: Number of nodes that were skipped
    """

    workflow_id: str = ""
    workflow_name: str = ""
    execution_time_ms: float = 0.0
    nodes_executed: int = 0
    nodes_skipped: int = 0

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update(
            {
                "workflow_id": self.workflow_id,
                "workflow_name": self.workflow_name,
                "execution_time_ms": self.execution_time_ms,
                "nodes_executed": self.nodes_executed,
                "nodes_skipped": self.nodes_skipped,
            }
        )
        return result


@dataclass(frozen=True)
class WorkflowFailed(DomainEvent):
    """
    Event raised when a workflow fails due to an error.

    Attributes:
        workflow_id: Unique identifier of the workflow
        workflow_name: Display name of the workflow
        failed_node_id: ID of the node that caused the failure
        error_code: Standardized error code
        error_message: Human-readable error description
        execution_time_ms: Time elapsed before failure
    """

    workflow_id: str = ""
    workflow_name: str = ""
    failed_node_id: Optional[str] = None
    error_code: Optional[ErrorCode] = None
    error_message: str = ""
    execution_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update(
            {
                "workflow_id": self.workflow_id,
                "workflow_name": self.workflow_name,
                "failed_node_id": self.failed_node_id,
                "error_code": self.error_code.name if self.error_code else None,
                "error_message": self.error_message,
                "execution_time_ms": self.execution_time_ms,
            }
        )
        return result


@dataclass(frozen=True)
class WorkflowStopped(DomainEvent):
    """
    Event raised when a workflow is stopped by user action.

    Attributes:
        workflow_id: Unique identifier of the workflow
        stopped_at_node_id: ID of the node where execution was stopped
        reason: Why the workflow was stopped
    """

    workflow_id: str = ""
    stopped_at_node_id: Optional[str] = None
    reason: str = "user_request"

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update(
            {
                "workflow_id": self.workflow_id,
                "stopped_at_node_id": self.stopped_at_node_id,
                "reason": self.reason,
            }
        )
        return result


@dataclass(frozen=True)
class WorkflowPaused(DomainEvent):
    """
    Event raised when a workflow is paused (debug mode).

    Attributes:
        workflow_id: Unique identifier of the workflow
        paused_at_node_id: ID of the node where execution paused
        reason: Why the workflow was paused (breakpoint, step, etc.)
    """

    workflow_id: str = ""
    paused_at_node_id: str = ""
    reason: str = "breakpoint"

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update(
            {
                "workflow_id": self.workflow_id,
                "paused_at_node_id": self.paused_at_node_id,
                "reason": self.reason,
            }
        )
        return result


@dataclass(frozen=True)
class WorkflowResumed(DomainEvent):
    """
    Event raised when a paused workflow resumes execution.

    Attributes:
        workflow_id: Unique identifier of the workflow
        resume_from_node_id: ID of the node where execution resumes
    """

    workflow_id: str = ""
    resume_from_node_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update(
            {
                "workflow_id": self.workflow_id,
                "resume_from_node_id": self.resume_from_node_id,
            }
        )
        return result


@dataclass(frozen=True)
class WorkflowProgress(DomainEvent):
    """
    Event raised to report workflow execution progress.

    Useful for progress bars and parallel execution tracking.

    Attributes:
        workflow_id: Unique identifier of the workflow
        current_node_id: Currently executing node
        completed_nodes: Number of completed nodes
        total_nodes: Total number of nodes
        percentage: Progress percentage (0-100)
    """

    workflow_id: str = ""
    current_node_id: str = ""
    completed_nodes: int = 0
    total_nodes: int = 0
    percentage: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update(
            {
                "workflow_id": self.workflow_id,
                "current_node_id": self.current_node_id,
                "completed_nodes": self.completed_nodes,
                "total_nodes": self.total_nodes,
                "percentage": self.percentage,
            }
        )
        return result


# =============================================================================
# Workflow Structure Events (from Workflow Aggregate)
# =============================================================================


@dataclass(frozen=True)
class NodeAdded(DomainEvent):
    """
    Event raised when a node is added to a workflow.

    Part of Workflow aggregate boundary. Raised through Workflow.add_node().

    Attributes:
        workflow_id: ID of the workflow containing the node
        node_id: ID of the newly added node
        node_type: Type of node (e.g., "ClickElementNode")
        position_x: X coordinate where node was placed
        position_y: Y coordinate where node was placed
    """

    workflow_id: str = ""
    node_id: str = ""
    node_type: str = ""
    position_x: float = 0.0
    position_y: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update(
            {
                "workflow_id": self.workflow_id,
                "node_id": self.node_id,
                "node_type": self.node_type,
                "position": {"x": self.position_x, "y": self.position_y},
            }
        )
        return result


@dataclass(frozen=True)
class NodeRemoved(DomainEvent):
    """
    Event raised when a node is removed from a workflow.

    Part of Workflow aggregate boundary. Raised through Workflow.remove_node().

    Attributes:
        workflow_id: ID of the workflow
        node_id: ID of the removed node
    """

    workflow_id: str = ""
    node_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update(
            {
                "workflow_id": self.workflow_id,
                "node_id": self.node_id,
            }
        )
        return result


@dataclass(frozen=True)
class NodeConnected(DomainEvent):
    """
    Event raised when two nodes are connected.

    Part of Workflow aggregate boundary. Raised through Workflow.connect().

    Attributes:
        workflow_id: ID of the workflow
        source_node: Source node ID
        source_port: Source port name
        target_node: Target node ID
        target_port: Target port name
    """

    workflow_id: str = ""
    source_node: str = ""
    source_port: str = ""
    target_node: str = ""
    target_port: str = ""

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update(
            {
                "workflow_id": self.workflow_id,
                "source_node": self.source_node,
                "source_port": self.source_port,
                "target_node": self.target_node,
                "target_port": self.target_port,
            }
        )
        return result


@dataclass(frozen=True)
class NodeDisconnected(DomainEvent):
    """
    Event raised when a connection is removed.

    Part of Workflow aggregate boundary. Raised through Workflow.disconnect().

    Attributes:
        workflow_id: ID of the workflow
        source_node: Source node ID
        source_port: Source port name
        target_node: Target node ID
        target_port: Target port name
    """

    workflow_id: str = ""
    source_node: str = ""
    source_port: str = ""
    target_node: str = ""
    target_port: str = ""

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update(
            {
                "workflow_id": self.workflow_id,
                "source_node": self.source_node,
                "source_port": self.source_port,
                "target_node": self.target_node,
                "target_port": self.target_port,
            }
        )
        return result


__all__ = [
    # Execution lifecycle events
    "WorkflowStarted",
    "WorkflowCompleted",
    "WorkflowFailed",
    "WorkflowStopped",
    "WorkflowPaused",
    "WorkflowResumed",
    "WorkflowProgress",
    # Structure events (from Workflow Aggregate)
    "NodeAdded",
    "NodeRemoved",
    "NodeConnected",
    "NodeDisconnected",
]
