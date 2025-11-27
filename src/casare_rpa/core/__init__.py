"""
CasareRPA - Core Package
Contains base classes, schemas, and core abstractions.
"""

__version__ = "0.1.0"

# Type definitions and enums
from .types import (
    DataType,
    EventType,
    ExecutionMode,
    NodeStatus,
    PortType,
    NodeId,
    PortId,
    Connection,
    NodeConfig,
    ExecutionResult,
    SerializedNode,
    SerializedWorkflow,
    SCHEMA_VERSION,
)

# Base node class
from .base_node import BaseNode

# Port is now in domain layer, but re-exported here for backward compatibility
from ..domain.value_objects import Port

# Workflow schema and related classes
from .workflow_schema import (
    WorkflowSchema,
    WorkflowMetadata,
    NodeConnection,
)

# Execution context
from .execution_context import ExecutionContext

# Event system
from .events import (
    Event,
    EventBus,
    EventLogger,
    EventRecorder,
    get_event_bus,
    reset_event_bus,
)

# Validation system
from .validation import (
    ValidationResult,
    ValidationIssue,
    ValidationSeverity,
    validate_workflow,
    validate_node,
    validate_connections,
    quick_validate,
)

__all__ = [
    # Version
    "__version__",
    # Types and Enums
    "DataType",
    "EventType",
    "ExecutionMode",
    "NodeStatus",
    "PortType",
    "NodeId",
    "PortId",
    "Connection",
    "NodeConfig",
    "ExecutionResult",
    "SerializedNode",
    "SerializedWorkflow",
    "SCHEMA_VERSION",
    # Base Classes
    "BaseNode",
    "Port",
    # Workflow Schema
    "WorkflowSchema",
    "WorkflowMetadata",
    "NodeConnection",
    # Execution Context
    "ExecutionContext",
    # Event System
    "Event",
    "EventBus",
    "EventLogger",
    "EventRecorder",
    "get_event_bus",
    "reset_event_bus",
    # Validation System
    "ValidationResult",
    "ValidationIssue",
    "ValidationSeverity",
    "validate_workflow",
    "validate_node",
    "validate_connections",
    "quick_validate",
]
