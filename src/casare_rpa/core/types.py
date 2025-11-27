"""
CasareRPA - Core Types (Compatibility Layer)

DEPRECATED: This module is being refactored into the domain layer.

For new code, import from:
    from casare_rpa.domain.value_objects.types import DataType, NodeId, ...

This compatibility layer will be removed in v3.0.
"""

import warnings
from typing import TYPE_CHECKING

# Re-export everything from new location for backward compatibility
from ..domain.value_objects.types import (
    # Enums
    DataType,
    ErrorCode,
    EventType,
    ExecutionMode,
    NodeStatus,
    PortType,
    # Type aliases
    Connection,
    EventData,
    ExecutionResult,
    NodeConfig,
    NodeId,
    PortDefinition,
    PortId,
    SerializedFrame,
    SerializedNode,
    SerializedWorkflow,
    # Constants
    DEFAULT_TIMEOUT,
    EXEC_IN_PORT,
    EXEC_OUT_PORT,
    MAX_RETRIES,
    SCHEMA_VERSION,
)

# Emit deprecation warning on import
if not TYPE_CHECKING:
    warnings.warn(
        "Importing from casare_rpa.core.types is deprecated. "
        "Please import from casare_rpa.domain.value_objects.types instead. "
        "This compatibility layer will be removed in v3.0.",
        DeprecationWarning,
        stacklevel=2
    )

__all__ = [
    # Enums
    "DataType",
    "ErrorCode",
    "EventType",
    "ExecutionMode",
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
    "DEFAULT_TIMEOUT",
    "EXEC_IN_PORT",
    "EXEC_OUT_PORT",
    "MAX_RETRIES",
    "SCHEMA_VERSION",
]
