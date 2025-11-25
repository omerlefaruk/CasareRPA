# API Reference

Core API documentation for CasareRPA's internal interfaces.

## Core Types (`core/types.py`)

### Enums

#### NodeStatus
Execution status of a node.

```python
class NodeStatus(Enum):
    IDLE = auto()       # Node has not been executed
    RUNNING = auto()    # Node is currently executing
    SUCCESS = auto()    # Node completed successfully
    ERROR = auto()      # Node encountered an error
    SKIPPED = auto()    # Node was skipped (conditional logic)
    CANCELLED = auto()  # Node execution was cancelled
```

#### PortType
Type of node port.

```python
class PortType(Enum):
    INPUT = auto()       # Input port (receives data)
    OUTPUT = auto()      # Output port (sends data)
    EXEC_INPUT = auto()  # Execution input (flow control)
    EXEC_OUTPUT = auto() # Execution output (flow control)
```

#### DataType
Data types that can flow between nodes.

```python
class DataType(Enum):
    STRING = auto()    # Text data
    INTEGER = auto()   # Integer number
    FLOAT = auto()     # Floating point number
    BOOLEAN = auto()   # True/False value
    LIST = auto()      # List/Array of values
    DICT = auto()      # Dictionary/Object
    ANY = auto()       # Any type (no validation)
    ELEMENT = auto()   # Web element reference
    PAGE = auto()      # Playwright page object
    BROWSER = auto()   # Playwright browser instance
```

#### ExecutionMode
Execution mode for workflows.

```python
class ExecutionMode(Enum):
    NORMAL = auto()    # Standard execution
    DEBUG = auto()     # Step-by-step with breakpoints
    VALIDATE = auto()  # Validate without executing
```

#### EventType
Types of events that can be emitted.

```python
class EventType(Enum):
    NODE_STARTED = auto()
    NODE_COMPLETED = auto()
    NODE_ERROR = auto()
    NODE_SKIPPED = auto()
    WORKFLOW_STARTED = auto()
    WORKFLOW_COMPLETED = auto()
    WORKFLOW_ERROR = auto()
    WORKFLOW_STOPPED = auto()
    WORKFLOW_PAUSED = auto()
    WORKFLOW_RESUMED = auto()
    VARIABLE_SET = auto()
    LOG_MESSAGE = auto()
```

#### ErrorCode
Standardized error codes grouped by category.

```python
class ErrorCode(Enum):
    # General errors (1xxx)
    UNKNOWN_ERROR = 1000
    TIMEOUT = 1001
    CANCELLED = 1002
    INVALID_INPUT = 1005

    # Browser/Web errors (2xxx)
    BROWSER_NOT_FOUND = 2000
    ELEMENT_NOT_FOUND = 2005
    NAVIGATION_FAILED = 2010

    # Desktop errors (3xxx)
    WINDOW_NOT_FOUND = 3000
    APPLICATION_LAUNCH_FAILED = 3001

    # Data errors (4xxx)
    VALIDATION_FAILED = 4000
    TYPE_MISMATCH = 4002

    # Config errors (5xxx)
    CONFIG_NOT_FOUND = 5000

    # Network errors (6xxx)
    NETWORK_ERROR = 6000

    # Resource errors (7xxx)
    FILE_NOT_FOUND = 7005

    # Properties
    @property
    def category(self) -> str
    @property
    def is_retryable(self) -> bool

    # Methods
    @classmethod
    def from_exception(cls, exception: Exception) -> ErrorCode
```

### Type Aliases

```python
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

# Serialized node/frame/workflow data
SerializedNode = Dict[str, Any]
SerializedFrame = Dict[str, Any]
SerializedWorkflow = Dict[str, Any]

# Execution result from a node
ExecutionResult = Optional[Dict[str, Any]]

# Event data
EventData = Dict[str, Any]
```

### Constants

```python
SCHEMA_VERSION: str = "1.0.0"    # Schema version for serialization
DEFAULT_TIMEOUT: int = 30        # Default timeout (seconds)
MAX_RETRIES: int = 3             # Maximum retry attempts
EXEC_IN_PORT: str = "exec_in"    # Execution input port name
EXEC_OUT_PORT: str = "exec_out"  # Execution output port name
```

---

## BaseNode (`core/base_node.py`)

Abstract base class for all automation nodes.

### Port Class

```python
class Port:
    """Represents a single input or output port on a node."""

    def __init__(
        self,
        name: str,
        port_type: PortType,
        data_type: DataType,
        label: Optional[str] = None,
        required: bool = True,
    ) -> None

    def set_value(self, value: Any) -> None
    def get_value(self) -> Any
    def to_dict(self) -> PortDefinition
```

### BaseNode Class

```python
class BaseNode(ABC):
    """Abstract base class for all automation nodes."""

    # Attributes
    node_id: NodeId
    config: NodeConfig
    status: NodeStatus
    error_message: Optional[str]
    input_ports: Dict[str, Port]
    output_ports: Dict[str, Port]
    node_type: str
    category: str
    description: str
    breakpoint_enabled: bool
    execution_count: int
    last_execution_time: Optional[float]
    last_output: Optional[Dict[str, Any]]

    def __init__(self, node_id: NodeId, config: Optional[NodeConfig] = None)

    # Abstract methods (must implement)
    @abstractmethod
    def _define_ports(self) -> None
        """Define input and output ports for this node."""

    @abstractmethod
    async def execute(self, context: ExecutionContext) -> ExecutionResult
        """Execute the node's logic."""

    @abstractmethod
    def validate(self) -> tuple[bool, List[str]]
        """Validate the node's configuration."""

    # Port management
    def add_input_port(
        self,
        name: str,
        data_type: DataType,
        label: Optional[str] = None,
        required: bool = True
    ) -> Port

    def add_output_port(
        self,
        name: str,
        data_type: DataType,
        label: Optional[str] = None
    ) -> Port

    def add_exec_input(self, name: str = "exec_in") -> Port
    def add_exec_output(self, name: str = "exec_out") -> Port

    def get_input_value(self, port_name: str) -> Any
    def set_output_value(self, port_name: str, value: Any) -> None

    # Status management
    def set_status(self, status: NodeStatus) -> None
    def set_error(self, message: str) -> None
    def clear_error(self) -> None

    # Serialization
    def to_dict(self) -> SerializedNode
    @classmethod
    def from_dict(cls, data: SerializedNode) -> "BaseNode"
```

### Creating a Custom Node

```python
from casare_rpa.core.base_node import BaseNode
from casare_rpa.core.types import DataType, ExecutionResult
from casare_rpa.core.execution_context import ExecutionContext

class MyCustomNode(BaseNode):
    """A custom automation node."""

    category = "Custom"

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_input_port("input_value", DataType.STRING, "Input")
        self.add_output_port("output_value", DataType.STRING, "Output")
        self.add_exec_output()

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        input_val = self.get_input_value("input_value")
        result = input_val.upper()  # Example transformation
        self.set_output_value("output_value", result)
        return {"output_value": result}

    def validate(self) -> tuple[bool, list[str]]:
        errors = []
        if not self.get_input_value("input_value"):
            errors.append("Input value is required")
        return len(errors) == 0, errors
```

---

## ExecutionContext (`core/execution_context.py`)

Runtime context for workflow execution.

```python
class ExecutionContext:
    """Stores variables, shared resources, and execution state."""

    # Attributes
    workflow_name: str
    mode: ExecutionMode
    started_at: datetime
    completed_at: Optional[datetime]
    variables: Dict[str, Any]
    browser: Optional[Browser]
    browser_contexts: List[BrowserContext]
    pages: Dict[str, Page]
    active_page: Optional[Page]
    current_node_id: Optional[NodeId]
    execution_path: list[NodeId]
    errors: list[tuple[NodeId, str]]
    stopped: bool
    desktop_context: Any

    def __init__(
        self,
        workflow_name: str = "Untitled",
        mode: ExecutionMode = ExecutionMode.NORMAL
    )

    # Variable management
    def set_variable(self, name: str, value: Any) -> None
    def get_variable(self, name: str, default: Any = None) -> Any
    def has_variable(self, name: str) -> bool
    def delete_variable(self, name: str) -> None
    def clear_variables(self) -> None

    # Browser management
    def set_browser(self, browser: Browser) -> None
    def get_browser(self) -> Optional[Browser]
    def set_active_page(self, page: Page) -> None
    def get_active_page(self) -> Optional[Page]
    def add_page(self, name: str, page: Page) -> None
    def get_page(self, name: Optional[str] = None) -> Optional[Page]
    def close_page(self, name: str) -> None
    def add_browser_context(self, context: BrowserContext) -> None

    # Desktop context
    def get_desktop_context(self) -> DesktopContext
        """Get or create desktop automation context."""

    # Execution control
    def stop(self) -> None
    def is_stopped(self) -> bool
    def add_error(self, node_id: NodeId, message: str) -> None
    def record_node_execution(self, node_id: NodeId) -> None

    # Cleanup
    async def cleanup(self) -> None
        """Close all resources (browsers, pages, etc.)."""
```

---

## Event System (`core/events.py`)

Publish-subscribe event system for workflow execution.

### EventBus

```python
class EventBus:
    """Singleton event bus for pub/sub communication."""

    @staticmethod
    def get_instance() -> "EventBus"

    def subscribe(
        self,
        event_type: EventType,
        callback: Callable[[EventData], None]
    ) -> None

    def unsubscribe(
        self,
        event_type: EventType,
        callback: Callable[[EventData], None]
    ) -> None

    def emit(self, event_type: EventType, data: Optional[EventData] = None) -> None

    def clear_all(self) -> None

# Convenience function
def get_event_bus() -> EventBus
```

### Usage

```python
from casare_rpa.core.events import get_event_bus, EventType

event_bus = get_event_bus()

# Subscribe to events
def on_node_completed(data):
    print(f"Node {data['node_id']} completed")

event_bus.subscribe(EventType.NODE_COMPLETED, on_node_completed)

# Emit events
event_bus.emit(EventType.NODE_COMPLETED, {"node_id": "node_1"})

# Unsubscribe
event_bus.unsubscribe(EventType.NODE_COMPLETED, on_node_completed)
```

---

## WorkflowSchema (`core/workflow_schema.py`)

Workflow serialization and deserialization.

### WorkflowMetadata

```python
class WorkflowMetadata:
    """Metadata about a workflow."""

    name: str
    description: str
    author: str
    version: str
    tags: List[str]
    created_at: str
    modified_at: str
    schema_version: str

    def to_dict(self) -> Dict[str, Any]
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowMetadata"
```

### NodeConnection

```python
class NodeConnection:
    """Represents a connection between two node ports."""

    source_node: NodeId
    source_port: str
    target_node: NodeId
    target_port: str

    @property
    def source_id(self) -> PortId
    @property
    def target_id(self) -> PortId

    def to_dict(self) -> Dict[str, str]
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "NodeConnection"
```

### WorkflowSchema

```python
class WorkflowSchema:
    """Complete workflow with nodes and connections."""

    metadata: WorkflowMetadata
    nodes: Dict[NodeId, SerializedNode]
    connections: List[NodeConnection]
    frames: List[SerializedFrame]
    variables: Dict[str, Any]
    settings: Dict[str, Any]

    def add_node(self, node_data: SerializedNode) -> None
    def remove_node(self, node_id: NodeId) -> None
    def add_connection(self, connection: NodeConnection) -> None
    def remove_connection(...) -> None
    def get_node(self, node_id: NodeId) -> Optional[SerializedNode]
    def get_connections_from(self, node_id: NodeId) -> List[NodeConnection]
    def get_connections_to(self, node_id: NodeId) -> List[NodeConnection]
    def validate(self) -> tuple[bool, List[str]]

    # Serialization
    def to_dict(self) -> SerializedWorkflow
    @classmethod
    def from_dict(cls, data: SerializedWorkflow) -> "WorkflowSchema"

    # File I/O
    def save_to_file(self, file_path: Path) -> None
    @classmethod
    def load_from_file(cls, file_path: Path) -> "WorkflowSchema"
```

---

## Workflow JSON Schema

```json
{
  "metadata": {
    "name": "string",
    "description": "string",
    "author": "string",
    "version": "string",
    "tags": ["string"],
    "created_at": "ISO 8601 datetime",
    "modified_at": "ISO 8601 datetime",
    "schema_version": "1.0.0"
  },
  "nodes": {
    "node_id": {
      "node_id": "string",
      "node_type": "string",
      "position": [x, y],
      "properties": {
        "property_name": "value"
      }
    }
  },
  "connections": [
    {
      "source_node": "node_id",
      "source_port": "port_name",
      "target_node": "node_id",
      "target_port": "port_name"
    }
  ],
  "frames": [
    {
      "frame_id": "string",
      "title": "string",
      "color": "hex_color",
      "bounds": [x, y, width, height],
      "nodes": ["node_id"],
      "collapsed": false
    }
  ],
  "variables": {
    "variable_name": "value"
  },
  "settings": {
    "stop_on_error": true,
    "timeout": 30,
    "retry_count": 0
  }
}
```
