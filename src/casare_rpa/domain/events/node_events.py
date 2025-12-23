"""
CasareRPA - Node Execution Events

Typed domain events for node execution lifecycle.
Replaces EventType.NODE_* enum values with typed classes.
"""

from dataclasses import dataclass
from typing import Any

from casare_rpa.domain.events.base import DomainEvent
from casare_rpa.domain.value_objects.types import ErrorCode, NodeStatus


@dataclass(frozen=True)
class NodeStarted(DomainEvent):
    """
    Event raised when a node begins execution.

    Attributes:
        node_id: Unique identifier of the node
        node_type: Type/class name of the node (e.g., "ClickElementNode")
        workflow_id: ID of the workflow containing this node
    """

    node_id: str = ""
    node_type: str = ""
    workflow_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result.update(
            {
                "node_id": self.node_id,
                "node_type": self.node_type,
                "workflow_id": self.workflow_id,
            }
        )
        return result


@dataclass(frozen=True)
class NodeCompleted(DomainEvent):
    """
    Event raised when a node completes execution successfully.

    Attributes:
        node_id: Unique identifier of the node
        node_type: Type/class name of the node
        workflow_id: ID of the workflow containing this node
        execution_time_ms: How long the node took to execute in milliseconds
        output_data: Output data produced by the node (optional)
    """

    node_id: str = ""
    node_type: str = ""
    workflow_id: str = ""
    execution_time_ms: float = 0.0
    output_data: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result.update(
            {
                "node_id": self.node_id,
                "node_type": self.node_type,
                "workflow_id": self.workflow_id,
                "execution_time_ms": self.execution_time_ms,
                "output_data": self.output_data,
            }
        )
        return result


@dataclass(frozen=True)
class NodeFailed(DomainEvent):
    """
    Event raised when a node encounters an error during execution.

    Attributes:
        node_id: Unique identifier of the node
        node_type: Type/class name of the node
        workflow_id: ID of the workflow containing this node
        error_code: Standardized error code
        error_message: Human-readable error description
        is_retryable: Whether the error is typically retryable
    """

    node_id: str = ""
    node_type: str = ""
    workflow_id: str = ""
    error_code: ErrorCode | None = None
    error_message: str = ""
    is_retryable: bool = False

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result.update(
            {
                "node_id": self.node_id,
                "node_type": self.node_type,
                "workflow_id": self.workflow_id,
                "error_code": self.error_code.name if self.error_code else None,
                "error_message": self.error_message,
                "is_retryable": self.is_retryable,
            }
        )
        return result


@dataclass(frozen=True)
class NodeSkipped(DomainEvent):
    """
    Event raised when a node is skipped (e.g., conditional logic).

    Attributes:
        node_id: Unique identifier of the node
        node_type: Type/class name of the node
        workflow_id: ID of the workflow containing this node
        reason: Why the node was skipped
    """

    node_id: str = ""
    node_type: str = ""
    workflow_id: str = ""
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result.update(
            {
                "node_id": self.node_id,
                "node_type": self.node_type,
                "workflow_id": self.workflow_id,
                "reason": self.reason,
            }
        )
        return result


@dataclass(frozen=True)
class NodeStatusChanged(DomainEvent):
    """
    Event raised when a node's status changes.

    Generic status change event for any status transition.

    Attributes:
        node_id: Unique identifier of the node
        old_status: Previous status
        new_status: New status
    """

    node_id: str = ""
    old_status: NodeStatus | None = None
    new_status: NodeStatus | None = None

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result.update(
            {
                "node_id": self.node_id,
                "old_status": self.old_status.name if self.old_status else None,
                "new_status": self.new_status.name if self.new_status else None,
            }
        )
        return result


__all__ = [
    "NodeStarted",
    "NodeCompleted",
    "NodeFailed",
    "NodeSkipped",
    "NodeStatusChanged",
]
