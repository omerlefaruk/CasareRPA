"""
CasareRPA - Value Objects

Value objects are immutable objects defined by their attributes rather than identity.
Includes type definitions, ports, and other immutable domain concepts.
"""

from .log_entry import (
    LogLevel,
    LogEntry,
    LogBatch,
    LogQuery,
    LogStats,
    DEFAULT_LOG_RETENTION_DAYS,
    MAX_LOG_BATCH_SIZE,
    OFFLINE_BUFFER_SIZE,
)
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

__all__ = [
    # Enums
    "DataType",
    "ErrorCode",
    "EventType",
    "ExecutionMode",
    "LogLevel",
    "NodeStatus",
    "PortType",
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
    # Value objects
    "LogBatch",
    "LogEntry",
    "LogQuery",
    "LogStats",
    "Port",
]
