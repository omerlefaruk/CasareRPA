"""
Event Data Contracts for CasareRPA Event Bus System.

This module defines TypedDict contracts for all event data payloads,
ensuring type safety and documentation for event-driven communication.

Usage:
    from casare_rpa.presentation.canvas.events.event_contracts import (
        NodeExecutionStartedData,
        WorkflowSavedData,
    )

    # Type-safe event creation
    data: NodeExecutionStartedData = {
        "node_id": "node_123",
        "node_type": "ClickElementNode",
        "node_name": "Click Login Button",
    }
    event = Event(
        type=EventType.NODE_EXECUTION_STARTED,
        source="ExecutionController",
        data=data
    )
"""

from typing import Any, Dict, List, Optional, TypedDict

# =============================================================================
# NODE EVENTS
# =============================================================================


class NodeExecutionStartedData(TypedDict, total=False):
    """Data for NODE_EXECUTION_STARTED event."""

    node_id: str
    """Unique identifier of the node."""

    node_type: str
    """Type/class name of the node (e.g., 'ClickElementNode')."""

    node_name: str
    """Display name of the node."""


class NodeExecutionCompletedData(TypedDict, total=False):
    """Data for NODE_EXECUTION_COMPLETED event."""

    node_id: str
    """Unique identifier of the node."""

    node_type: str
    """Type/class name of the node."""

    result: Dict[str, Any]
    """Execution result dictionary with 'success' and output data."""

    duration_ms: float
    """Execution duration in milliseconds."""

    output_values: Dict[str, Any]
    """Output port values after execution."""


class NodeExecutionFailedData(TypedDict, total=False):
    """Data for NODE_EXECUTION_FAILED event."""

    node_id: str
    """Unique identifier of the node."""

    node_type: str
    """Type/class name of the node."""

    error: str
    """Error message."""

    error_code: str
    """Standardized error code (e.g., 'ELEMENT_NOT_FOUND')."""

    traceback: Optional[str]
    """Full traceback for debugging."""

    retryable: bool
    """Whether this error is typically retryable."""


class NodeExecutionSkippedData(TypedDict, total=False):
    """Data for NODE_EXECUTION_SKIPPED event."""

    node_id: str
    """Unique identifier of the node."""

    reason: str
    """Reason for skipping (e.g., 'Conditional branch not taken')."""


class NodeAddedData(TypedDict, total=False):
    """Data for NODE_ADDED event."""

    node_id: str
    """Unique identifier of the new node."""

    node_type: str
    """Type/class name of the node."""

    node_name: str
    """Display name of the node."""

    position: tuple[float, float]
    """Canvas position (x, y)."""


class NodeRemovedData(TypedDict, total=False):
    """Data for NODE_REMOVED event."""

    node_id: str
    """Unique identifier of the removed node."""

    node_type: str
    """Type/class name of the node."""


class NodeSelectedData(TypedDict, total=False):
    """Data for NODE_SELECTED event."""

    node_id: str
    """Unique identifier of the selected node."""

    node_ids: List[str]
    """List of all currently selected node IDs (for multi-select)."""


class NodePropertyChangedData(TypedDict, total=False):
    """Data for NODE_PROPERTY_CHANGED event."""

    node_id: str
    """Unique identifier of the node."""

    property_name: str
    """Name of the changed property."""

    old_value: Any
    """Previous value."""

    new_value: Any
    """New value."""


class NodePositionChangedData(TypedDict, total=False):
    """Data for NODE_POSITION_CHANGED event."""

    node_id: str
    """Unique identifier of the node."""

    position: tuple[float, float]
    """New canvas position (x, y)."""

    old_position: tuple[float, float]
    """Previous canvas position (x, y)."""


# =============================================================================
# WORKFLOW EVENTS
# =============================================================================


class WorkflowNewData(TypedDict, total=False):
    """Data for WORKFLOW_NEW event."""

    workflow_id: str
    """Unique identifier of the new workflow."""

    workflow_name: str
    """Name of the workflow."""


class WorkflowOpenedData(TypedDict, total=False):
    """Data for WORKFLOW_OPENED event."""

    file_path: str
    """Path to the opened workflow file."""

    workflow_id: str
    """Unique identifier of the workflow."""

    workflow_name: str
    """Name of the workflow."""


class WorkflowSavedData(TypedDict, total=False):
    """Data for WORKFLOW_SAVED event."""

    file_path: str
    """Path where workflow was saved."""

    workflow_id: str
    """Unique identifier of the workflow."""

    workflow_name: str
    """Name of the workflow."""


class WorkflowModifiedData(TypedDict, total=False):
    """Data for WORKFLOW_MODIFIED event."""

    workflow_id: str
    """Unique identifier of the workflow."""

    modified: bool
    """Whether workflow has unsaved changes."""


class WorkflowClosedData(TypedDict, total=False):
    """Data for WORKFLOW_CLOSED event."""

    workflow_id: str
    """Unique identifier of the closed workflow."""

    file_path: Optional[str]
    """Path of the closed workflow file, if any."""


# =============================================================================
# EXECUTION EVENTS
# =============================================================================


class ExecutionStartedData(TypedDict, total=False):
    """Data for EXECUTION_STARTED event."""

    execution_id: str
    """Unique identifier for this execution run."""

    workflow_id: str
    """Workflow being executed."""

    workflow_name: str
    """Name of the workflow."""

    total_nodes: int
    """Total number of nodes to execute."""

    mode: str
    """Execution mode: 'normal', 'debug', 'validate'."""


class ExecutionCompletedData(TypedDict, total=False):
    """Data for EXECUTION_COMPLETED event."""

    execution_id: str
    """Unique identifier for this execution run."""

    workflow_id: str
    """Workflow that was executed."""

    status: str
    """Final status: 'success', 'failed', 'cancelled'."""

    duration_ms: float
    """Total execution duration in milliseconds."""

    nodes_executed: int
    """Number of nodes that were executed."""

    results: Dict[str, Any]
    """Final execution results/outputs."""


class ExecutionFailedData(TypedDict, total=False):
    """Data for EXECUTION_FAILED event."""

    execution_id: str
    """Unique identifier for this execution run."""

    workflow_id: str
    """Workflow that failed."""

    error: str
    """Error message."""

    error_code: str
    """Standardized error code."""

    failed_node_id: Optional[str]
    """ID of the node that caused the failure."""

    duration_ms: float
    """Duration until failure in milliseconds."""


class ExecutionPausedData(TypedDict, total=False):
    """Data for EXECUTION_PAUSED event."""

    execution_id: str
    """Unique identifier for this execution run."""

    reason: str
    """Reason for pause: 'user', 'breakpoint', 'error'."""

    current_node_id: Optional[str]
    """Node that was executing when paused."""


class ExecutionResumedData(TypedDict, total=False):
    """Data for EXECUTION_RESUMED event."""

    execution_id: str
    """Unique identifier for this execution run."""


class ExecutionStoppedData(TypedDict, total=False):
    """Data for EXECUTION_STOPPED event."""

    execution_id: str
    """Unique identifier for this execution run."""

    reason: str
    """Reason for stop: 'user_cancelled', 'timeout', 'error'."""


# =============================================================================
# CONNECTION EVENTS
# =============================================================================


class ConnectionAddedData(TypedDict, total=False):
    """Data for CONNECTION_ADDED event."""

    connection_id: str
    """Unique identifier for the connection."""

    source_node_id: str
    """ID of the source node."""

    source_port: str
    """Name of the source port."""

    target_node_id: str
    """ID of the target node."""

    target_port: str
    """Name of the target port."""


class ConnectionRemovedData(TypedDict, total=False):
    """Data for CONNECTION_REMOVED event."""

    connection_id: str
    """Unique identifier for the connection."""

    source_node_id: str
    """ID of the source node."""

    target_node_id: str
    """ID of the target node."""


# =============================================================================
# VARIABLE EVENTS
# =============================================================================


class VariableSetData(TypedDict, total=False):
    """Data for VARIABLE_SET / VARIABLE_UPDATED event."""

    name: str
    """Variable name."""

    value: Any
    """New variable value."""

    old_value: Any
    """Previous value (if update)."""

    scope: str
    """Variable scope: 'workflow', 'project', 'global'."""

    node_id: Optional[str]
    """Node that set the variable, if applicable."""


class VariableDeletedData(TypedDict, total=False):
    """Data for VARIABLE_DELETED event."""

    name: str
    """Variable name."""

    scope: str
    """Variable scope that was cleared."""


# =============================================================================
# PROJECT EVENTS
# =============================================================================


class ProjectOpenedData(TypedDict, total=False):
    """Data for PROJECT_OPENED event."""

    project_path: str
    """Path to the project directory."""

    project_name: str
    """Name of the project."""

    scenario_count: int
    """Number of scenarios in the project."""


class ProjectClosedData(TypedDict, total=False):
    """Data for PROJECT_CLOSED event."""

    project_path: str
    """Path to the closed project."""


class ScenarioOpenedData(TypedDict, total=False):
    """Data for SCENARIO_OPENED event."""

    scenario_path: str
    """Path to the scenario file."""

    scenario_name: str
    """Name of the scenario."""

    project_name: str
    """Parent project name."""


# =============================================================================
# DEBUG EVENTS
# =============================================================================


class BreakpointHitData(TypedDict, total=False):
    """Data for BREAKPOINT_HIT event."""

    node_id: str
    """Node where breakpoint was hit."""

    execution_id: str
    """Current execution ID."""

    variables: Dict[str, Any]
    """Current variable values at breakpoint."""


class DebugCallStackUpdatedData(TypedDict, total=False):
    """Data for DEBUG_CALL_STACK_UPDATED event."""

    frames: List[Dict[str, Any]]
    """Call stack frames."""

    current_frame: int
    """Index of current frame."""


# =============================================================================
# UI EVENTS
# =============================================================================


class PanelToggledData(TypedDict, total=False):
    """Data for PANEL_TOGGLED event."""

    panel_name: str
    """Name of the panel."""

    visible: bool
    """Whether panel is now visible."""


class ZoomChangedData(TypedDict, total=False):
    """Data for ZOOM_CHANGED event."""

    zoom_level: float
    """New zoom level (1.0 = 100%)."""

    old_zoom_level: float
    """Previous zoom level."""


class ThemeChangedData(TypedDict, total=False):
    """Data for THEME_CHANGED event."""

    theme: str
    """New theme name: 'dark', 'light', 'system'."""


# =============================================================================
# SYSTEM EVENTS
# =============================================================================


class ErrorOccurredData(TypedDict, total=False):
    """Data for ERROR_OCCURRED event."""

    error: str
    """Error message."""

    error_code: str
    """Standardized error code."""

    source: str
    """Component that generated the error."""

    traceback: Optional[str]
    """Full traceback for debugging."""


class LogMessageData(TypedDict, total=False):
    """Data for LOG_MESSAGE event."""

    level: str
    """Log level: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'."""

    message: str
    """Log message text."""

    source: str
    """Source component/module."""

    timestamp: str
    """ISO timestamp."""


class PerformanceMetricData(TypedDict, total=False):
    """Data for PERFORMANCE_METRIC event."""

    metric_name: str
    """Name of the metric."""

    value: float
    """Metric value."""

    unit: str
    """Unit of measurement (ms, bytes, count, etc.)."""

    context: Dict[str, Any]
    """Additional context."""


# =============================================================================
# TRIGGER EVENTS
# =============================================================================


class TriggerFiredData(TypedDict, total=False):
    """Data for TRIGGER_FIRED event."""

    trigger_id: str
    """Unique identifier of the trigger."""

    trigger_type: str
    """Type of trigger: 'scheduled', 'webhook', 'file_watch', etc."""

    workflow_id: str
    """Workflow to be executed."""

    payload: Dict[str, Any]
    """Trigger payload data."""


class TriggerCreatedData(TypedDict, total=False):
    """Data for TRIGGER_CREATED event."""

    trigger_id: str
    """Unique identifier of the new trigger."""

    trigger_type: str
    """Type of trigger."""

    workflow_id: str
    """Associated workflow."""

    config: Dict[str, Any]
    """Trigger configuration."""


# =============================================================================
# BATCHED EVENTS
# =============================================================================


class BatchedEventsData(TypedDict, total=False):
    """Data for batched event delivery (from EventBatcher)."""

    batched_events: List[Any]
    """List of original events that were batched."""

    count: int
    """Number of events in batch."""


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Node events
    "NodeExecutionStartedData",
    "NodeExecutionCompletedData",
    "NodeExecutionFailedData",
    "NodeExecutionSkippedData",
    "NodeAddedData",
    "NodeRemovedData",
    "NodeSelectedData",
    "NodePropertyChangedData",
    "NodePositionChangedData",
    # Workflow events
    "WorkflowNewData",
    "WorkflowOpenedData",
    "WorkflowSavedData",
    "WorkflowModifiedData",
    "WorkflowClosedData",
    # Execution events
    "ExecutionStartedData",
    "ExecutionCompletedData",
    "ExecutionFailedData",
    "ExecutionPausedData",
    "ExecutionResumedData",
    "ExecutionStoppedData",
    # Connection events
    "ConnectionAddedData",
    "ConnectionRemovedData",
    # Variable events
    "VariableSetData",
    "VariableDeletedData",
    # Project events
    "ProjectOpenedData",
    "ProjectClosedData",
    "ScenarioOpenedData",
    # Debug events
    "BreakpointHitData",
    "DebugCallStackUpdatedData",
    # UI events
    "PanelToggledData",
    "ZoomChangedData",
    "ThemeChangedData",
    # System events
    "ErrorOccurredData",
    "LogMessageData",
    "PerformanceMetricData",
    # Trigger events
    "TriggerFiredData",
    "TriggerCreatedData",
    # Batched events
    "BatchedEventsData",
]
