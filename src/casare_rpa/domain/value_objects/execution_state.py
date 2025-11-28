"""
CasareRPA - Domain Value Object: Execution State

Immutable value object representing the state of workflow execution.
Used by DBOS for automatic state persistence and recovery.

This is PURE domain - no infrastructure dependencies:
- Serializable via Pydantic
- Immutable (frozen dataclass)
- No async/await
- No database/network operations
"""

from typing import Any, Dict, Optional, Set
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

from .types import NodeId


class WorkflowStatus(str, Enum):
    """Workflow execution status."""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class ExecutionState(BaseModel):
    """
    Immutable execution state for workflow.

    Contains all state needed to resume workflow execution after crash:
    - executed_nodes: Set of node IDs already executed
    - current_node_id: ID of currently executing node
    - variables: Workflow variables
    - status: Current workflow status
    - metadata: Additional execution metadata

    Used by DBOS for automatic checkpointing and recovery.

    Example:
        ```python
        state = ExecutionState(
            workflow_id="wf-001",
            workflow_name="Data Processing",
            executed_nodes={"node-1", "node-2"},
            current_node_id="node-3",
            variables={"counter": 10},
            status=WorkflowStatus.RUNNING
        )

        # Serialize for DBOS storage
        state_dict = state.model_dump()

        # Deserialize on recovery
        restored = ExecutionState(**state_dict)
        ```
    """

    # Workflow identification
    workflow_id: str = Field(..., description="Unique workflow instance ID")
    workflow_name: str = Field(..., description="Workflow name")

    # Execution tracking
    executed_nodes: Set[NodeId] = Field(
        default_factory=set, description="Set of node IDs that have been executed"
    )
    current_node_id: Optional[NodeId] = Field(
        default=None, description="ID of currently executing node"
    )

    # Workflow variables
    variables: Dict[str, Any] = Field(
        default_factory=dict,
        description="Workflow variables (must be JSON-serializable)",
    )

    # Status
    status: WorkflowStatus = Field(
        default=WorkflowStatus.PENDING, description="Current workflow execution status"
    )

    # Timestamps
    start_time: datetime = Field(
        default_factory=datetime.now, description="Workflow start time"
    )
    last_update_time: datetime = Field(
        default_factory=datetime.now, description="Last state update time"
    )
    end_time: Optional[datetime] = Field(
        default=None, description="Workflow end time (if completed/failed)"
    )

    # Error tracking
    error_message: Optional[str] = Field(
        default=None, description="Error message if status is FAILED"
    )
    failed_node_id: Optional[NodeId] = Field(
        default=None, description="ID of node that caused failure"
    )

    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (project_id, tenant_id, etc.)",
    )

    # Run-To-Node support
    target_node_id: Optional[NodeId] = Field(
        default=None, description="Target node for Run-To-Node execution"
    )
    subgraph_nodes: Optional[Set[NodeId]] = Field(
        default=None, description="Nodes in subgraph for Run-To-Node"
    )

    # Configuration
    class Config:
        """Pydantic configuration."""

        frozen = False  # Allow updates during execution
        validate_assignment = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            set: lambda v: list(v),  # Sets serialized as lists
        }

    def mark_node_executed(self, node_id: NodeId) -> "ExecutionState":
        """
        Mark a node as executed and return updated state.

        Args:
            node_id: Node ID to mark as executed

        Returns:
            Updated ExecutionState (new instance for immutability)
        """
        new_executed = self.executed_nodes.copy()
        new_executed.add(node_id)

        return self.model_copy(
            update={
                "executed_nodes": new_executed,
                "last_update_time": datetime.now(),
            }
        )

    def set_current_node(self, node_id: Optional[NodeId]) -> "ExecutionState":
        """
        Set the current executing node.

        Args:
            node_id: Current node ID or None

        Returns:
            Updated ExecutionState
        """
        return self.model_copy(
            update={
                "current_node_id": node_id,
                "last_update_time": datetime.now(),
            }
        )

    def update_variables(self, variables: Dict[str, Any]) -> "ExecutionState":
        """
        Update workflow variables.

        Args:
            variables: New variables (merged with existing)

        Returns:
            Updated ExecutionState
        """
        new_vars = self.variables.copy()
        new_vars.update(variables)

        return self.model_copy(
            update={
                "variables": new_vars,
                "last_update_time": datetime.now(),
            }
        )

    def set_variable(self, name: str, value: Any) -> "ExecutionState":
        """
        Set a single workflow variable.

        Args:
            name: Variable name
            value: Variable value (must be JSON-serializable)

        Returns:
            Updated ExecutionState
        """
        new_vars = self.variables.copy()
        new_vars[name] = value

        return self.model_copy(
            update={
                "variables": new_vars,
                "last_update_time": datetime.now(),
            }
        )

    def mark_running(self) -> "ExecutionState":
        """Mark workflow as running."""
        return self.model_copy(
            update={
                "status": WorkflowStatus.RUNNING,
                "last_update_time": datetime.now(),
            }
        )

    def mark_paused(self) -> "ExecutionState":
        """Mark workflow as paused."""
        return self.model_copy(
            update={
                "status": WorkflowStatus.PAUSED,
                "last_update_time": datetime.now(),
            }
        )

    def mark_completed(self) -> "ExecutionState":
        """Mark workflow as completed."""
        return self.model_copy(
            update={
                "status": WorkflowStatus.COMPLETED,
                "end_time": datetime.now(),
                "last_update_time": datetime.now(),
            }
        )

    def mark_failed(
        self, error_message: str, failed_node_id: Optional[NodeId] = None
    ) -> "ExecutionState":
        """
        Mark workflow as failed.

        Args:
            error_message: Error description
            failed_node_id: Optional ID of node that failed

        Returns:
            Updated ExecutionState
        """
        return self.model_copy(
            update={
                "status": WorkflowStatus.FAILED,
                "error_message": error_message,
                "failed_node_id": failed_node_id,
                "end_time": datetime.now(),
                "last_update_time": datetime.now(),
            }
        )

    def mark_stopped(self) -> "ExecutionState":
        """Mark workflow as stopped by user."""
        return self.model_copy(
            update={
                "status": WorkflowStatus.STOPPED,
                "end_time": datetime.now(),
                "last_update_time": datetime.now(),
            }
        )

    def calculate_progress(self, total_nodes: int) -> float:
        """
        Calculate execution progress percentage.

        Args:
            total_nodes: Total number of nodes to execute

        Returns:
            Progress percentage (0-100)
        """
        if total_nodes == 0:
            return 0.0

        # Use subgraph nodes if Run-To-Node is active
        denominator = len(self.subgraph_nodes) if self.subgraph_nodes else total_nodes

        if denominator == 0:
            return 0.0

        return (len(self.executed_nodes) / denominator) * 100

    def is_node_executed(self, node_id: NodeId) -> bool:
        """
        Check if a node has been executed.

        Args:
            node_id: Node ID to check

        Returns:
            True if node was executed
        """
        return node_id in self.executed_nodes

    def should_execute_node(self, node_id: NodeId) -> bool:
        """
        Check if a node should be executed based on subgraph filtering.

        Used for Run-To-Node feature.

        Args:
            node_id: Node ID to check

        Returns:
            True if node should be executed
        """
        if self.subgraph_nodes is None:
            return True  # No filtering - execute all nodes

        return node_id in self.subgraph_nodes

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize to dictionary for DBOS storage.

        Returns:
            Dictionary with all state fields
        """
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionState":
        """
        Deserialize from dictionary.

        Args:
            data: State dictionary

        Returns:
            ExecutionState instance
        """
        # Convert lists back to sets for executed_nodes and subgraph_nodes
        if "executed_nodes" in data and isinstance(data["executed_nodes"], list):
            data["executed_nodes"] = set(data["executed_nodes"])

        if "subgraph_nodes" in data and isinstance(data["subgraph_nodes"], list):
            data["subgraph_nodes"] = set(data["subgraph_nodes"])

        return cls(**data)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ExecutionState("
            f"workflow='{self.workflow_name}', "
            f"status={self.status.value}, "
            f"executed={len(self.executed_nodes)}, "
            f"current={self.current_node_id})"
        )


# ============================================================================
# Factory Functions
# ============================================================================


def create_execution_state(
    workflow_id: str,
    workflow_name: str,
    initial_variables: Optional[Dict[str, Any]] = None,
    target_node_id: Optional[NodeId] = None,
    subgraph_nodes: Optional[Set[NodeId]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> ExecutionState:
    """
    Create a new execution state for workflow execution.

    Args:
        workflow_id: Unique workflow instance ID
        workflow_name: Workflow name
        initial_variables: Optional initial variables
        target_node_id: Optional target node for Run-To-Node
        subgraph_nodes: Optional subgraph nodes for Run-To-Node
        metadata: Optional metadata (project_id, tenant_id, etc.)

    Returns:
        New ExecutionState instance
    """
    return ExecutionState(
        workflow_id=workflow_id,
        workflow_name=workflow_name,
        variables=initial_variables or {},
        target_node_id=target_node_id,
        subgraph_nodes=subgraph_nodes,
        metadata=metadata or {},
        status=WorkflowStatus.PENDING,
    )


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "ExecutionState",
    "WorkflowStatus",
    "create_execution_state",
]
