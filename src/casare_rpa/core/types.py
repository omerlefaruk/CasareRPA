"""
CasareRPA - Core Type Definitions
Enums, type aliases, and constants used throughout the application.
"""

from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union


# ============================================================================
# ENUMS
# ============================================================================


class NodeStatus(Enum):
    """Execution status of a node."""

    IDLE = auto()  # Node has not been executed
    RUNNING = auto()  # Node is currently executing
    SUCCESS = auto()  # Node completed successfully
    ERROR = auto()  # Node encountered an error
    SKIPPED = auto()  # Node was skipped (conditional logic)
    CANCELLED = auto()  # Node execution was cancelled


class PortType(Enum):
    """Type of node port."""

    INPUT = auto()  # Input port (receives data)
    OUTPUT = auto()  # Output port (sends data)
    EXEC_INPUT = auto()  # Execution input (flow control)
    EXEC_OUTPUT = auto()  # Execution output (flow control)


class DataType(Enum):
    """Data types that can flow between nodes."""

    STRING = auto()  # Text data
    INTEGER = auto()  # Integer number
    FLOAT = auto()  # Floating point number
    BOOLEAN = auto()  # True/False value
    LIST = auto()  # List/Array of values
    DICT = auto()  # Dictionary/Object
    ANY = auto()  # Any type (no validation)
    ELEMENT = auto()  # Web element reference
    PAGE = auto()  # Playwright page object
    BROWSER = auto()  # Playwright browser instance


class ExecutionMode(Enum):
    """Execution mode for workflows."""

    NORMAL = auto()  # Standard execution
    DEBUG = auto()  # Step-by-step with breakpoints
    VALIDATE = auto()  # Validate without executing


class EventType(Enum):
    """Types of events that can be emitted."""

    NODE_STARTED = auto()  # Node execution started
    NODE_COMPLETED = auto()  # Node execution completed
    NODE_ERROR = auto()  # Node encountered error
    NODE_SKIPPED = auto()  # Node was skipped
    WORKFLOW_STARTED = auto()  # Workflow execution started
    WORKFLOW_COMPLETED = auto()  # Workflow execution completed
    WORKFLOW_ERROR = auto()  # Workflow encountered error
    VARIABLE_SET = auto()  # Variable was set in context
    LOG_MESSAGE = auto()  # Log message emitted


# ============================================================================
# TYPE ALIASES
# ============================================================================

# Port identifier (node_id.port_name)
PortId = str

# Node unique identifier
NodeId = str

# Connection between two ports (source -> target)
Connection = tuple[PortId, PortId]

# Node configuration dictionary
NodeConfig = Dict[str, Any]

# Port definition
PortDefinition = Dict[str, Union[str, PortType, DataType]]

# Serialized node data
SerializedNode = Dict[str, Any]

# Serialized workflow data
SerializedWorkflow = Dict[str, Any]

# Execution result from a node
ExecutionResult = Optional[Dict[str, Any]]

# Event data
EventData = Dict[str, Any]


# ============================================================================
# CONSTANTS
# ============================================================================

# Schema version for serialization
SCHEMA_VERSION: str = "1.0.0"

# Default timeout for node execution (seconds)
DEFAULT_TIMEOUT: int = 30

# Maximum number of retry attempts
MAX_RETRIES: int = 3

# Port name constants
EXEC_IN_PORT: str = "exec_in"
EXEC_OUT_PORT: str = "exec_out"
