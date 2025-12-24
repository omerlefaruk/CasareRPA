"""
CasareRPA - Domain Layer Type Definitions

This module defines core value objects for the domain layer:
- Enums: DataType, PortType, NodeStatus, NodeState, ExecutionMode, ErrorCode, EventType
- Dataclasses: NodeResult
- Type aliases: NodeId, PortId, Connection, NodeConfig, etc.
- Constants: SCHEMA_VERSION, DEFAULT_TIMEOUT, etc.

NOTE: EventType enum is provided for backward compatibility. New code should prefer
typed domain events from casare_rpa.domain.events (e.g., NodeStarted, NodeCompleted).

All types here are framework-agnostic and represent pure domain concepts.
"""

import sys
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from casare_rpa.domain.value_objects.execution_metadata import ExecutionMetadata


# =============================================================================
# PERFORMANCE: String Interning for Frequently Used Strings
# =============================================================================
# Interned strings share memory and have O(1) identity comparison instead of
# O(n) character-by-character comparison. This is especially useful for:
# - Node type names (compared on every execution)
# - Port names (compared on every connection)
# - Event type names (compared on every publish)

_interned_strings: dict[str, str] = {}


def intern_string(s: str) -> str:
    """
    Intern a string for memory efficiency and fast comparison.

    PERFORMANCE: Interned strings are cached and reused. Comparing
    interned strings with 'is' is O(1) instead of O(n) for '=='.

    Args:
        s: String to intern

    Returns:
        Interned string (may be same object or cached copy)
    """
    # Use Python's built-in sys.intern for small strings
    if len(s) < 50:
        return sys.intern(s)

    # For longer strings, use our own cache
    if s not in _interned_strings:
        _interned_strings[s] = s
    return _interned_strings[s]


def intern_node_type(node_type: str) -> str:
    """Intern a node type name."""
    return intern_string(node_type)


def intern_port_name(port_name: str) -> str:
    """Intern a port name."""
    return intern_string(port_name)


# ============================================================================
# ENUMS
# ============================================================================


class NodeStatus(Enum):
    """Execution status of a node (legacy, use NodeState for new code)."""

    IDLE = auto()  # Node has not been executed
    RUNNING = auto()  # Node is currently executing
    SUCCESS = auto()  # Node completed successfully
    ERROR = auto()  # Node encountered an error
    SKIPPED = auto()  # Node was skipped (conditional logic)
    CANCELLED = auto()  # Node execution was cancelled


class NodeState(Enum):
    """Rich node execution state (Prefect/Airflow pattern).

    Provides more granular execution states than NodeStatus,
    including scheduling and retry states.
    """

    PENDING = auto()  # Not yet scheduled
    SCHEDULED = auto()  # Queued for execution
    RUNNING = auto()  # Currently executing
    SUCCESS = auto()  # Completed successfully
    FAILED = auto()  # Failed with error
    SKIPPED = auto()  # Skipped due to condition
    CANCELLED = auto()  # Cancelled by user/system
    RETRYING = auto()  # Awaiting retry attempt
    UPSTREAM_FAILED = auto()  # Upstream node failed

    def to_node_status(self) -> NodeStatus:
        """Convert to legacy NodeStatus for backward compatibility."""
        mapping = {
            NodeState.PENDING: NodeStatus.IDLE,
            NodeState.SCHEDULED: NodeStatus.IDLE,
            NodeState.RUNNING: NodeStatus.RUNNING,
            NodeState.SUCCESS: NodeStatus.SUCCESS,
            NodeState.FAILED: NodeStatus.ERROR,
            NodeState.SKIPPED: NodeStatus.SKIPPED,
            NodeState.CANCELLED: NodeStatus.CANCELLED,
            NodeState.RETRYING: NodeStatus.RUNNING,
            NodeState.UPSTREAM_FAILED: NodeStatus.SKIPPED,
        }
        return mapping[self]

    @property
    def is_terminal(self) -> bool:
        """Check if this is a terminal state (no further transitions)."""
        return self in {
            NodeState.SUCCESS,
            NodeState.FAILED,
            NodeState.SKIPPED,
            NodeState.CANCELLED,
            NodeState.UPSTREAM_FAILED,
        }

    @property
    def is_running(self) -> bool:
        """Check if node is actively executing."""
        return self in {NodeState.RUNNING, NodeState.RETRYING}


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
    NUMBER = auto()  # Generic number (int or float)
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
    BYTES = auto()  # Binary data



class ExecutionMode(Enum):
    """Execution mode for workflows."""

    NORMAL = auto()  # Standard execution
    DEBUG = auto()  # Step-by-step with breakpoints
    VALIDATE = auto()  # Validate without executing


class EventType(Enum):
    """
    Event types for workflow execution events.

    This enum provides backward compatibility for code using the legacy
    string-based event system. New code should prefer the typed domain events
    from casare_rpa.domain.events (e.g., NodeStarted, NodeCompleted, etc.).

    Migration guide:
        # Old (legacy enum)
        event_bus.subscribe(EventType.NODE_COMPLETED, handler)
        event_bus.emit(EventType.NODE_COMPLETED, data)

        # New (typed events - preferred)
        from casare_rpa.domain.events import NodeCompleted
        event_bus.subscribe(NodeCompleted, handler)
        event_bus.publish(NodeCompleted(node_id="x", node_type="Y"))
    """

    # Node execution events
    NODE_STARTED = auto()
    NODE_COMPLETED = auto()
    NODE_ERROR = auto()
    NODE_SKIPPED = auto()
    NODE_STATUS_CHANGED = auto()

    # Workflow lifecycle events
    WORKFLOW_STARTED = auto()
    WORKFLOW_COMPLETED = auto()
    WORKFLOW_ERROR = auto()
    WORKFLOW_FAILED = auto()
    WORKFLOW_STOPPED = auto()
    WORKFLOW_PAUSED = auto()
    WORKFLOW_RESUMED = auto()
    WORKFLOW_PROGRESS = auto()

    # Variable events
    VARIABLE_SET = auto()

    # System events
    LOG_MESSAGE = auto()
    BROWSER_PAGE_READY = auto()
    DEBUG_BREAKPOINT_HIT = auto()
    RESOURCE_ACQUIRED = auto()
    RESOURCE_RELEASED = auto()


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
NodeConfig = dict[str, Any]

# Port definition
PortDefinition = dict[str, str | PortType | DataType]

# Serialized node data
SerializedNode = dict[str, Any]

# Serialized frame data (for node grouping)
SerializedFrame = dict[str, Any]

# Serialized workflow data
SerializedWorkflow = dict[str, Any]

# Execution result from a node
ExecutionResult = Optional[dict[str, Any]]

# Event data
EventData = dict[str, Any]


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


# ============================================================================
# DATACLASSES
# ============================================================================


@dataclass
class NodeResult:
    """Enhanced execution result with rich metadata.

    Provides structured result handling with flow control signals
    and retry capabilities. Replaces dict-based ExecutionResult
    for new node implementations.

    Attributes:
        success: Whether the node executed successfully.
        data: Output data dictionary (port name -> value).
        error: Error message if failed.
        error_code: Structured error code for programmatic handling.
        metadata: Execution metadata (timing, attempts, context).
        route_to: Override next node ID for dynamic routing.
        loop_back_to: Signal loop continuation to specified node.
        parallel_branches: Fork execution to multiple branches.
        should_retry: Signal that execution should be retried.
        retry_delay_ms: Delay before retry in milliseconds.
    """

    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    error_code: str | None = None
    metadata: Optional["ExecutionMetadata"] = None

    # Flow control signals
    route_to: str | None = None
    loop_back_to: str | None = None
    parallel_branches: list[str] | None = None

    # Retry signals
    should_retry: bool = False
    retry_delay_ms: int = 0

    @classmethod
    def ok(cls, **outputs: Any) -> "NodeResult":
        """Create success result with outputs.

        Args:
            **outputs: Output port values (port_name=value).

        Returns:
            NodeResult with success=True and data populated.

        Example:
            return NodeResult.ok(text="Hello", count=42)
        """
        return cls(success=True, data=outputs)

    @classmethod
    def fail(cls, error: str, code: str = "UNKNOWN_ERROR") -> "NodeResult":
        """Create failure result.

        Args:
            error: Human-readable error message.
            code: Structured error code for programmatic handling.

        Returns:
            NodeResult with success=False and error details.

        Example:
            return NodeResult.fail("Element not found", "ELEMENT_NOT_FOUND")
        """
        return cls(success=False, error=error, error_code=code)

    @classmethod
    def retry(cls, error: str, delay_ms: int = 1000, code: str = "RETRY_REQUESTED") -> "NodeResult":
        """Create result requesting retry.

        Args:
            error: Reason for retry.
            delay_ms: Delay before retry attempt.
            code: Error code.

        Returns:
            NodeResult signaling retry should occur.
        """
        return cls(
            success=False,
            error=error,
            error_code=code,
            should_retry=True,
            retry_delay_ms=delay_ms,
        )

    def with_metadata(self, metadata: "ExecutionMetadata") -> "NodeResult":
        """Create new result with metadata attached.

        Args:
            metadata: Execution metadata to attach.

        Returns:
            New NodeResult with metadata set.
        """
        return NodeResult(
            success=self.success,
            data=self.data,
            error=self.error,
            error_code=self.error_code,
            metadata=metadata,
            route_to=self.route_to,
            loop_back_to=self.loop_back_to,
            parallel_branches=self.parallel_branches,
            should_retry=self.should_retry,
            retry_delay_ms=self.retry_delay_ms,
        )

    @property
    def is_success(self) -> bool:
        """Check if result represents successful execution."""
        return self.success

    @property
    def is_failure(self) -> bool:
        """Check if result represents failed execution."""
        return not self.success
