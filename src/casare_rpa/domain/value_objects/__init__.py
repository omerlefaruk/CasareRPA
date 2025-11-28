"""
CasareRPA - Value Objects

Value objects are immutable objects defined by their attributes rather than identity.
Includes type definitions, ports, and other immutable domain concepts.
"""

from .port import Port
from .types import (
    Connection,
    DataType,
    ErrorCode,
    EventData,
    EventType,
    ExecutionMode,
    ExecutionResult,
    NodeConfig,
    NodeId,
    NodeStatus,
    PortDefinition,
    PortId,
    PortType,
    SCHEMA_VERSION,
    DEFAULT_TIMEOUT,
    MAX_RETRIES,
    EXEC_IN_PORT,
    EXEC_OUT_PORT,
    SerializedFrame,
    SerializedNode,
    SerializedWorkflow,
)
from .execution_state import ExecutionState, WorkflowStatus, create_execution_state
from .selector import (
    SelectorStrategy,
    SelectorAttribute,
    SmartSelector,
    create_smart_selector,
)
from .healing_event import (
    HealingTier,
    HealingEvent,
    HealingMetrics,
    create_healing_event,
    create_healing_metrics,
)

__all__ = [
    # Enums
    "DataType",
    "ErrorCode",
    "EventType",
    "ExecutionMode",
    "NodeStatus",
    "PortType",
    "WorkflowStatus",
    "SelectorStrategy",
    "HealingTier",
    # Type aliases
    "Connection",
    "EventData",
    "ExecutionResult",
    "NodeConfig",
    "NodeId",
    "PortDefinition",
    "PortId",
    "SerializedFrame",
    "SerializedNode",
    "SerializedWorkflow",
    # Constants
    "DEFAULT_TIMEOUT",
    "EXEC_IN_PORT",
    "EXEC_OUT_PORT",
    "MAX_RETRIES",
    "SCHEMA_VERSION",
    # Value objects
    "Port",
    "ExecutionState",
    "SelectorAttribute",
    "SmartSelector",
    "HealingEvent",
    "HealingMetrics",
    # Factories
    "create_execution_state",
    "create_smart_selector",
    "create_healing_event",
    "create_healing_metrics",
]
