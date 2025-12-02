"""
CasareRPA - Domain Layer Type Definitions

This module defines core value objects for the domain layer:
- Enums: DataType, PortType, NodeStatus, ExecutionMode, EventType, ErrorCode
- Type aliases: NodeId, PortId, Connection, NodeConfig, etc.
- Constants: SCHEMA_VERSION, DEFAULT_TIMEOUT, etc.

All types here are framework-agnostic and represent pure domain concepts.
"""

from enum import Enum, auto
from typing import Any, Dict, Optional, Union


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

    # Primitive types
    STRING = auto()  # Text data
    INTEGER = auto()  # Integer number
    FLOAT = auto()  # Floating point number
    BOOLEAN = auto()  # True/False value
    LIST = auto()  # List/Array of values
    DICT = auto()  # Dictionary/Object
    ANY = auto()  # Any type (no validation)
    EXEC = auto()  # Execution flow marker (no data, just triggers execution)

    # Browser automation types
    ELEMENT = auto()  # Web element reference
    PAGE = auto()  # Playwright page object
    BROWSER = auto()  # Playwright browser instance

    # Database types
    DB_CONNECTION = auto()  # Database connection object

    # Office automation types
    WORKBOOK = auto()  # Excel workbook object
    WORKSHEET = auto()  # Excel worksheet object
    DOCUMENT = auto()  # Word/PDF document object

    # Desktop automation types
    WINDOW = auto()  # Desktop window handle
    DESKTOP_ELEMENT = auto()  # Desktop UI element (UIAutomation)

    # Generic object type (for custom/complex objects)
    OBJECT = auto()  # Generic object reference


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
    WORKFLOW_STOPPED = auto()  # Workflow execution stopped by user
    WORKFLOW_PAUSED = auto()  # Workflow execution paused
    WORKFLOW_RESUMED = auto()  # Workflow execution resumed
    WORKFLOW_PROGRESS = auto()  # Workflow progress update (e.g., parallel execution)
    VARIABLE_SET = auto()  # Variable was set in context
    LOG_MESSAGE = auto()  # Log message emitted


class ErrorCode(Enum):
    """
    Standardized error codes for consistent error handling across the application.

    Error codes are grouped by category:
    - 1xxx: General errors
    - 2xxx: Browser/Web errors
    - 3xxx: Desktop automation errors
    - 4xxx: Data/Validation errors
    - 5xxx: Configuration errors
    - 6xxx: Network errors
    - 7xxx: Resource errors
    """

    # General errors (1xxx)
    UNKNOWN_ERROR = 1000
    TIMEOUT = 1001
    CANCELLED = 1002
    NOT_IMPLEMENTED = 1003
    INTERNAL_ERROR = 1004
    INVALID_INPUT = 1005
    PERMISSION_DENIED = 1006

    # Browser/Web errors (2xxx)
    BROWSER_NOT_FOUND = 2000
    BROWSER_LAUNCH_FAILED = 2001
    BROWSER_CLOSED = 2002
    PAGE_NOT_FOUND = 2003
    PAGE_LOAD_FAILED = 2004
    ELEMENT_NOT_FOUND = 2005
    ELEMENT_NOT_VISIBLE = 2006
    ELEMENT_NOT_ENABLED = 2007
    ELEMENT_STALE = 2008
    SELECTOR_INVALID = 2009
    NAVIGATION_FAILED = 2010
    CLICK_FAILED = 2011
    TYPE_FAILED = 2012
    SCREENSHOT_FAILED = 2013
    JAVASCRIPT_ERROR = 2014

    # Desktop automation errors (3xxx)
    WINDOW_NOT_FOUND = 3000
    APPLICATION_LAUNCH_FAILED = 3001
    APPLICATION_NOT_RESPONDING = 3002
    DESKTOP_ELEMENT_NOT_FOUND = 3003
    DESKTOP_ELEMENT_STALE = 3004
    DESKTOP_ACTION_FAILED = 3005
    KEYBOARD_INPUT_FAILED = 3006
    MOUSE_ACTION_FAILED = 3007
    UI_AUTOMATION_ERROR = 3008

    # Data/Validation errors (4xxx)
    VALIDATION_FAILED = 4000
    PARSE_ERROR = 4001
    TYPE_MISMATCH = 4002
    VALUE_OUT_OF_RANGE = 4003
    MISSING_REQUIRED_FIELD = 4004
    DUPLICATE_VALUE = 4005
    INVALID_FORMAT = 4006
    SERIALIZATION_ERROR = 4007
    EXPRESSION_ERROR = 4008

    # Configuration errors (5xxx)
    CONFIG_NOT_FOUND = 5000
    CONFIG_INVALID = 5001
    CONFIG_MISSING_KEY = 5002
    TEMPLATE_ERROR = 5003
    WORKFLOW_INVALID = 5004
    NODE_CONFIG_ERROR = 5005

    # Network errors (6xxx)
    NETWORK_ERROR = 6000
    CONNECTION_REFUSED = 6001
    CONNECTION_TIMEOUT = 6002
    DNS_LOOKUP_FAILED = 6003
    SSL_ERROR = 6004
    HTTP_ERROR = 6005
    API_ERROR = 6006

    # Resource errors (7xxx)
    RESOURCE_NOT_FOUND = 7000
    RESOURCE_LOCKED = 7001
    RESOURCE_EXHAUSTED = 7002
    MEMORY_ERROR = 7003
    DISK_FULL = 7004
    FILE_NOT_FOUND = 7005
    FILE_ACCESS_DENIED = 7006

    @classmethod
    def from_exception(cls, exception: Exception) -> "ErrorCode":
        """
        Map an exception to an appropriate error code.

        Args:
            exception: The exception to map

        Returns:
            The most appropriate ErrorCode
        """
        exc_type = type(exception).__name__
        exc_msg = str(exception).lower()

        # Timeout errors
        if "timeout" in exc_type.lower() or "timeout" in exc_msg:
            return cls.TIMEOUT

        # Browser/Playwright errors
        if "playwright" in exc_type.lower():
            if "element" in exc_msg:
                if "not found" in exc_msg or "no element" in exc_msg:
                    return cls.ELEMENT_NOT_FOUND
                if "stale" in exc_msg:
                    return cls.ELEMENT_STALE
            if "navigation" in exc_msg:
                return cls.NAVIGATION_FAILED
            if "browser" in exc_msg:
                if "closed" in exc_msg:
                    return cls.BROWSER_CLOSED
                return cls.BROWSER_LAUNCH_FAILED

        # Value/Type errors
        if exc_type == "ValueError":
            if "selector" in exc_msg:
                return cls.SELECTOR_INVALID
            return cls.INVALID_INPUT

        if exc_type == "TypeError":
            return cls.TYPE_MISMATCH

        # Network errors
        if "connection" in exc_msg:
            if "refused" in exc_msg:
                return cls.CONNECTION_REFUSED
            if "timeout" in exc_msg:
                return cls.CONNECTION_TIMEOUT
            return cls.NETWORK_ERROR

        if "ssl" in exc_msg or "certificate" in exc_msg:
            return cls.SSL_ERROR

        # File errors
        if exc_type == "FileNotFoundError":
            return cls.FILE_NOT_FOUND

        if exc_type == "PermissionError":
            return cls.PERMISSION_DENIED

        # Memory errors
        if exc_type == "MemoryError":
            return cls.MEMORY_ERROR

        return cls.UNKNOWN_ERROR

    @property
    def category(self) -> str:
        """Get the category name for this error code."""
        code = self.value
        if code < 2000:
            return "General"
        elif code < 3000:
            return "Browser/Web"
        elif code < 4000:
            return "Desktop"
        elif code < 5000:
            return "Data/Validation"
        elif code < 6000:
            return "Configuration"
        elif code < 7000:
            return "Network"
        else:
            return "Resource"

    @property
    def is_retryable(self) -> bool:
        """Check if this error type is typically retryable."""
        retryable_codes = {
            self.TIMEOUT,
            self.NETWORK_ERROR,
            self.CONNECTION_TIMEOUT,
            self.CONNECTION_REFUSED,
            self.ELEMENT_STALE,
            self.DESKTOP_ELEMENT_STALE,
            self.APPLICATION_NOT_RESPONDING,
            self.RESOURCE_LOCKED,
        }
        return self in retryable_codes


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

# Serialized frame data (for node grouping)
SerializedFrame = Dict[str, Any]

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
