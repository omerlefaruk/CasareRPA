"""
CasareRPA - Value Objects

Value objects are immutable objects defined by their attributes rather than identity.
Includes type definitions, ports, and other immutable domain concepts.

NOTE: EventType enum is provided for backward compatibility. New code should prefer
typed domain events from casare_rpa.domain.events (e.g., NodeStarted, NodeCompleted).
"""

from casare_rpa.domain.value_objects.dynamic_port_config import (
    ActionPortConfig,
    DynamicPortSchema,
    PortDef,
)
from casare_rpa.domain.value_objects.execution_metadata import ExecutionMetadata
from casare_rpa.domain.value_objects.log_entry import (
    DEFAULT_LOG_RETENTION_DAYS,
    MAX_LOG_BATCH_SIZE,
    OFFLINE_BUFFER_SIZE,
    LogBatch,
    LogEntry,
    LogLevel,
    LogQuery,
    LogStats,
)
from casare_rpa.domain.value_objects.node_metadata import NodeMetadata
from casare_rpa.domain.value_objects.port import Port
from casare_rpa.domain.value_objects.position import Position
from casare_rpa.domain.value_objects.trigger_types import (
    TriggerPriority,
    TriggerStatus,
    TriggerType,
)
from casare_rpa.domain.value_objects.types import (
    DEFAULT_TIMEOUT,
    EXEC_IN_PORT,
    EXEC_OUT_PORT,
    MAX_RETRIES,
    SCHEMA_VERSION,
    Connection,
    DataType,
    ErrorCode,
    EventData,
    EventType,
    ExecutionMode,
    ExecutionResult,
    NodeConfig,
    NodeId,
    NodeResult,
    NodeState,
    NodeStatus,
    PortDefinition,
    PortId,
    PortType,
    SerializedFrame,
    SerializedNode,
    SerializedWorkflow,
)

__all__ = [
    # Enums
    "DataType",
    "ErrorCode",
    "EventType",
    "ExecutionMode",
    "LogLevel",
    "NodeState",
    "NodeStatus",
    "PortType",
    "TriggerType",
    "TriggerStatus",
    "TriggerPriority",
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
    "DEFAULT_LOG_RETENTION_DAYS",
    "DEFAULT_TIMEOUT",
    "EXEC_IN_PORT",
    "EXEC_OUT_PORT",
    "MAX_LOG_BATCH_SIZE",
    "MAX_RETRIES",
    "OFFLINE_BUFFER_SIZE",
    "SCHEMA_VERSION",
    # Value objects / Dataclasses
    "ExecutionMetadata",
    "LogBatch",
    "LogEntry",
    "LogQuery",
    "LogStats",
    "NodeMetadata",
    "NodeResult",
    "Port",
    "Position",
    # Dynamic port configuration (Super Nodes)
    "PortDef",
    "ActionPortConfig",
    "DynamicPortSchema",
]
