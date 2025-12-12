# Domain Event Bus Reference

CasareRPA uses a typed event bus for decoupled communication between components. All events are immutable frozen dataclasses, providing type safety and IDE autocomplete support.

## Quick Start

```python
from casare_rpa.domain.events import (
    get_event_bus,
    NodeCompleted,
    WorkflowStarted,
)

# Get the singleton event bus
bus = get_event_bus()

# Subscribe to specific event type
def on_node_completed(event: NodeCompleted) -> None:
    print(f"Node {event.node_id} completed in {event.execution_time_ms}ms")

bus.subscribe(NodeCompleted, on_node_completed)

# Publish an event
bus.publish(NodeCompleted(
    node_id="node-123",
    node_type="ClickElementNode",
    workflow_id="wf-456",
    execution_time_ms=150.5,
))
```

## Core Concepts

### Event Bus Singleton

The event bus is a thread-safe singleton accessible globally:

```python
from casare_rpa.domain.events import get_event_bus, reset_event_bus

# Get singleton instance
bus = get_event_bus()

# Reset for testing (clears handlers and history)
reset_event_bus()
```

### Typed Events

All events inherit from `DomainEvent` and are frozen dataclasses:

```python
from dataclasses import dataclass
from casare_rpa.domain.events.base import DomainEvent

@dataclass(frozen=True)
class MyCustomEvent(DomainEvent):
    """Custom event description."""
    my_field: str = ""
    my_value: int = 0

    def to_dict(self) -> dict:
        result = super().to_dict()
        result.update({
            "my_field": self.my_field,
            "my_value": self.my_value,
        })
        return result
```

### Event Immutability

Events are immutable - they cannot be modified after creation:

```python
event = NodeCompleted(node_id="x", execution_time_ms=100)

# This raises FrozenInstanceError:
event.node_id = "y"  # ERROR!

# Create a new event instead:
new_event = NodeCompleted(node_id="y", execution_time_ms=100)
```

---

## EventBus API

### subscribe()

Subscribe a handler to a specific event type.

```python
def subscribe(
    event_type: Type[DomainEvent],
    handler: Callable[[DomainEvent], None],
) -> None
```

**Parameters:**
- `event_type`: The event class to subscribe to
- `handler`: Callback function receiving the event

**Example:**
```python
def handle_workflow_started(event: WorkflowStarted) -> None:
    print(f"Workflow {event.workflow_name} started with {event.total_nodes} nodes")

bus.subscribe(WorkflowStarted, handle_workflow_started)
```

### unsubscribe()

Remove a handler from an event type.

```python
def unsubscribe(
    event_type: Type[DomainEvent],
    handler: Callable[[DomainEvent], None],
) -> None
```

**Example:**
```python
bus.unsubscribe(WorkflowStarted, handle_workflow_started)
```

### subscribe_all()

Subscribe to ALL events (wildcard subscription).

```python
def subscribe_all(handler: Callable[[DomainEvent], None]) -> None
```

**Example:**
```python
def log_all_events(event: DomainEvent) -> None:
    print(f"[{event.event_type_name}] {event.to_dict()}")

bus.subscribe_all(log_all_events)
```

### unsubscribe_all()

Remove a wildcard handler.

```python
bus.unsubscribe_all(log_all_events)
```

### publish()

Publish an event to all subscribers.

```python
def publish(event: DomainEvent) -> None
```

**Parameters:**
- `event`: The event instance to publish

**Behavior:**
1. Event added to history (max 1000 events)
2. Type-specific handlers called
3. Wildcard handlers called
4. Handler errors are logged but don't stop other handlers

**Example:**
```python
bus.publish(NodeStarted(
    node_id="node-123",
    node_type="TypeTextNode",
    workflow_id="wf-456",
))
```

### get_history()

Retrieve event history (most recent first).

```python
def get_history(
    event_type: Optional[Type[DomainEvent]] = None,
    limit: Optional[int] = None,
) -> List[DomainEvent]
```

**Parameters:**
- `event_type`: Filter by event type (optional)
- `limit`: Maximum events to return (optional)

**Example:**
```python
# Get last 10 node completion events
recent_completions = bus.get_history(NodeCompleted, limit=10)

for event in recent_completions:
    print(f"{event.node_id}: {event.execution_time_ms}ms")
```

### clear_history()

Clear the event history.

```python
bus.clear_history()
```

### clear_handlers()

Clear handlers for a specific type or all types.

```python
# Clear handlers for NodeCompleted only
bus.clear_handlers(NodeCompleted)

# Clear ALL handlers
bus.clear_handlers()
```

### get_handler_count()

Get the number of handlers for an event type.

```python
count = bus.get_handler_count(NodeCompleted)
print(f"{count} handlers registered for NodeCompleted")
```

---

## Event Classes Reference

### Node Events

Events related to individual node execution.

#### NodeStarted

Raised when a node begins execution.

```python
@dataclass(frozen=True)
class NodeStarted(DomainEvent):
    node_id: str = ""        # Unique node identifier
    node_type: str = ""      # Node class name (e.g., "ClickElementNode")
    workflow_id: str = ""    # Parent workflow ID
```

**Example:**
```python
bus.publish(NodeStarted(
    node_id="node-001",
    node_type="ClickElementNode",
    workflow_id="wf-123",
))
```

#### NodeCompleted

Raised when a node completes successfully.

```python
@dataclass(frozen=True)
class NodeCompleted(DomainEvent):
    node_id: str = ""
    node_type: str = ""
    workflow_id: str = ""
    execution_time_ms: float = 0.0    # Execution duration
    output_data: Optional[dict] = None # Node output (optional)
```

**Example:**
```python
bus.publish(NodeCompleted(
    node_id="node-001",
    node_type="ExtractTextNode",
    workflow_id="wf-123",
    execution_time_ms=250.5,
    output_data={"text": "Extracted value"},
))
```

#### NodeFailed

Raised when a node encounters an error.

```python
@dataclass(frozen=True)
class NodeFailed(DomainEvent):
    node_id: str = ""
    node_type: str = ""
    workflow_id: str = ""
    error_code: Optional[ErrorCode] = None  # Standardized error code
    error_message: str = ""                  # Human-readable message
    is_retryable: bool = False               # Can this be retried?
```

**Example:**
```python
from casare_rpa.domain.value_objects.types import ErrorCode

bus.publish(NodeFailed(
    node_id="node-001",
    node_type="ClickElementNode",
    workflow_id="wf-123",
    error_code=ErrorCode.SELECTOR_NOT_FOUND,
    error_message="Element #submit-btn not found after 30s",
    is_retryable=True,
))
```

#### NodeSkipped

Raised when a node is skipped (conditional logic).

```python
@dataclass(frozen=True)
class NodeSkipped(DomainEvent):
    node_id: str = ""
    node_type: str = ""
    workflow_id: str = ""
    reason: str = ""    # Why the node was skipped
```

**Example:**
```python
bus.publish(NodeSkipped(
    node_id="node-003",
    node_type="SendEmailNode",
    workflow_id="wf-123",
    reason="Condition 'has_errors' evaluated to False",
))
```

#### NodeStatusChanged

Generic status transition event.

```python
@dataclass(frozen=True)
class NodeStatusChanged(DomainEvent):
    node_id: str = ""
    old_status: Optional[NodeStatus] = None
    new_status: Optional[NodeStatus] = None
```

---

### Workflow Events

Events related to workflow execution lifecycle.

#### WorkflowStarted

Raised when a workflow begins execution.

```python
@dataclass(frozen=True)
class WorkflowStarted(DomainEvent):
    workflow_id: str = ""
    workflow_name: str = ""
    execution_mode: ExecutionMode = ExecutionMode.NORMAL  # NORMAL, DEBUG, etc.
    triggered_by: str = "manual"  # manual, schedule, api, webhook
    total_nodes: int = 0
```

**Example:**
```python
from casare_rpa.domain.value_objects.types import ExecutionMode

bus.publish(WorkflowStarted(
    workflow_id="wf-123",
    workflow_name="Invoice Processing",
    execution_mode=ExecutionMode.NORMAL,
    triggered_by="schedule",
    total_nodes=15,
))
```

#### WorkflowCompleted

Raised when a workflow completes successfully.

```python
@dataclass(frozen=True)
class WorkflowCompleted(DomainEvent):
    workflow_id: str = ""
    workflow_name: str = ""
    execution_time_ms: float = 0.0
    nodes_executed: int = 0
    nodes_skipped: int = 0
```

#### WorkflowFailed

Raised when a workflow fails.

```python
@dataclass(frozen=True)
class WorkflowFailed(DomainEvent):
    workflow_id: str = ""
    workflow_name: str = ""
    failed_node_id: Optional[str] = None
    error_code: Optional[ErrorCode] = None
    error_message: str = ""
    execution_time_ms: float = 0.0
```

#### WorkflowStopped

Raised when a workflow is stopped by user action.

```python
@dataclass(frozen=True)
class WorkflowStopped(DomainEvent):
    workflow_id: str = ""
    stopped_at_node_id: Optional[str] = None
    reason: str = "user_request"
```

#### WorkflowPaused

Raised when a workflow is paused (debug mode).

```python
@dataclass(frozen=True)
class WorkflowPaused(DomainEvent):
    workflow_id: str = ""
    paused_at_node_id: str = ""
    reason: str = "breakpoint"  # breakpoint, step, user_request
```

#### WorkflowResumed

Raised when a paused workflow resumes.

```python
@dataclass(frozen=True)
class WorkflowResumed(DomainEvent):
    workflow_id: str = ""
    resume_from_node_id: str = ""
```

#### WorkflowProgress

Raised to report execution progress.

```python
@dataclass(frozen=True)
class WorkflowProgress(DomainEvent):
    workflow_id: str = ""
    current_node_id: str = ""
    completed_nodes: int = 0
    total_nodes: int = 0
    percentage: float = 0.0  # 0-100
```

**Example:**
```python
bus.publish(WorkflowProgress(
    workflow_id="wf-123",
    current_node_id="node-005",
    completed_nodes=4,
    total_nodes=15,
    percentage=26.67,
))
```

---

### Workflow Structure Events

Events from the Workflow aggregate for structure changes.

#### NodeAdded

Raised when a node is added to a workflow.

```python
@dataclass(frozen=True)
class NodeAdded(DomainEvent):
    workflow_id: str = ""
    node_id: str = ""
    node_type: str = ""
    position_x: float = 0.0
    position_y: float = 0.0
```

#### NodeRemoved

Raised when a node is removed from a workflow.

```python
@dataclass(frozen=True)
class NodeRemoved(DomainEvent):
    workflow_id: str = ""
    node_id: str = ""
```

#### NodeConnected

Raised when nodes are connected.

```python
@dataclass(frozen=True)
class NodeConnected(DomainEvent):
    workflow_id: str = ""
    source_node: str = ""
    source_port: str = ""
    target_node: str = ""
    target_port: str = ""
```

#### NodeDisconnected

Raised when a connection is removed.

```python
@dataclass(frozen=True)
class NodeDisconnected(DomainEvent):
    workflow_id: str = ""
    source_node: str = ""
    source_port: str = ""
    target_node: str = ""
    target_port: str = ""
```

---

### System Events

Events for system-level operations.

#### VariableSet

Raised when a variable is set in execution context.

```python
@dataclass(frozen=True)
class VariableSet(DomainEvent):
    variable_name: str = ""
    variable_value: Any = None
    workflow_id: str = ""
    source_node_id: Optional[str] = None
```

**Example:**
```python
bus.publish(VariableSet(
    variable_name="invoice_total",
    variable_value=1250.00,
    workflow_id="wf-123",
    source_node_id="node-007",
))
```

#### BrowserPageReady

Raised when a browser page is ready.

```python
@dataclass(frozen=True)
class BrowserPageReady(DomainEvent):
    page_id: str = ""
    url: str = ""
    title: str = ""
    browser_type: str = "chromium"  # chromium, firefox, webkit
```

#### LogMessage

Raised when a log message is emitted.

```python
@dataclass(frozen=True)
class LogMessage(DomainEvent):
    level: LogLevel = LogLevel.INFO
    message: str = ""
    source: Optional[str] = None      # Module or node type
    node_id: Optional[str] = None
    workflow_id: Optional[str] = None
    extra_data: Optional[dict] = None
```

#### DebugBreakpointHit

Raised when execution hits a breakpoint.

```python
@dataclass(frozen=True)
class DebugBreakpointHit(DomainEvent):
    node_id: str = ""
    workflow_id: str = ""
    variables: Optional[dict] = None  # Current variable state
```

#### ResourceAcquired

Raised when a shared resource is acquired.

```python
@dataclass(frozen=True)
class ResourceAcquired(DomainEvent):
    resource_type: str = ""  # browser, database, file
    resource_id: str = ""
    workflow_id: str = ""
```

#### ResourceReleased

Raised when a shared resource is released.

```python
@dataclass(frozen=True)
class ResourceReleased(DomainEvent):
    resource_type: str = ""
    resource_id: str = ""
    workflow_id: str = ""
```

---

## Utility Classes

### EventLogger

Log all events to console.

```python
from casare_rpa.domain.events import EventLogger, get_event_bus

logger = EventLogger(log_level="INFO")
logger.subscribe_to_bus(get_event_bus())

# Now all events are logged:
# INFO - Event: NodeCompleted - {"node_id": "x", ...}
```

### EventRecorder

Record events for replay or analysis.

```python
from casare_rpa.domain.events import EventRecorder, get_event_bus

recorder = EventRecorder()
recorder.subscribe_to_bus(get_event_bus())

# Start recording
recorder.start_recording()

# ... run workflow ...

# Stop and export
recorder.stop_recording()
events = recorder.get_recorded_events(NodeCompleted)
export_data = recorder.export_to_dict()
```

---

## Integration Patterns

### Qt Event Bridge

Bridge domain events to Qt signals for UI updates:

```python
from PySide6.QtCore import QObject, Signal
from casare_rpa.domain.events import (
    get_event_bus,
    NodeCompleted,
    WorkflowProgress,
)

class QtEventBridge(QObject):
    """Bridge domain events to Qt signals."""

    node_completed = Signal(str, float)  # node_id, execution_time_ms
    workflow_progress = Signal(str, float)  # workflow_id, percentage

    def __init__(self):
        super().__init__()
        bus = get_event_bus()
        bus.subscribe(NodeCompleted, self._on_node_completed)
        bus.subscribe(WorkflowProgress, self._on_workflow_progress)

    def _on_node_completed(self, event: NodeCompleted) -> None:
        self.node_completed.emit(event.node_id, event.execution_time_ms)

    def _on_workflow_progress(self, event: WorkflowProgress) -> None:
        self.workflow_progress.emit(event.workflow_id, event.percentage)
```

### Async Event Handling

For async handlers, use asyncio:

```python
import asyncio
from casare_rpa.domain.events import get_event_bus, NodeCompleted

async def async_handler(event: NodeCompleted) -> None:
    await some_async_operation(event.node_id)

def sync_wrapper(event: NodeCompleted) -> None:
    """Wrap async handler for sync event bus."""
    asyncio.create_task(async_handler(event))

bus = get_event_bus()
bus.subscribe(NodeCompleted, sync_wrapper)
```

### Unit Testing Events

```python
import pytest
from casare_rpa.domain.events import (
    get_event_bus,
    reset_event_bus,
    NodeCompleted,
)

@pytest.fixture
def clean_event_bus():
    """Provide clean event bus for each test."""
    reset_event_bus()
    yield get_event_bus()
    reset_event_bus()

def test_node_completion_event(clean_event_bus):
    received_events = []

    def handler(event: NodeCompleted) -> None:
        received_events.append(event)

    clean_event_bus.subscribe(NodeCompleted, handler)

    # Publish event
    clean_event_bus.publish(NodeCompleted(
        node_id="test-node",
        execution_time_ms=100,
    ))

    # Assert
    assert len(received_events) == 1
    assert received_events[0].node_id == "test-node"
    assert received_events[0].execution_time_ms == 100
```

---

## Best Practices

1. **Event Naming**: Use past tense (`NodeCompleted`, not `NodeComplete`)
2. **Keep Events Small**: Include only necessary data
3. **Immutability**: Never modify events after creation
4. **Error Handling**: Handlers should catch their own exceptions
5. **Thread Safety**: Event bus is thread-safe; handlers may not be
6. **History Cleanup**: History is auto-limited to 1000 events

---

## Related Documentation

- [REST API Reference](orchestrator-rest.md) - HTTP endpoints
- [WebSocket API Reference](orchestrator-websocket.md) - Real-time streaming
- [Architecture Overview](../../architecture/ddd-patterns.md) - DDD patterns
