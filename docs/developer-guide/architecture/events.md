# Typed Domain Events Reference

CasareRPA uses typed domain events (frozen dataclasses) following DDD 2025 patterns. This document provides a complete reference for the event system.

## Overview

Domain events are immutable facts about something that happened in the domain. They are used for:

- Cross-aggregate communication
- Event-driven architecture
- Audit logging
- UI updates via Qt signal bridge

All events are frozen (immutable) dataclasses.

## EventBus

The `EventBus` is a thread-safe singleton for publishing and subscribing to typed events.

### Getting the EventBus

```python
from casare_rpa.domain.events import get_event_bus

bus = get_event_bus()  # Singleton
```

### Subscribing to Events

```python
from casare_rpa.domain.events import NodeCompleted, get_event_bus

def handle_node_completed(event: NodeCompleted) -> None:
    print(f"Node {event.node_id} completed in {event.execution_time_ms}ms")

bus = get_event_bus()
bus.subscribe(NodeCompleted, handle_node_completed)
```

### Publishing Events

```python
from casare_rpa.domain.events import NodeCompleted, get_event_bus

bus = get_event_bus()
bus.publish(NodeCompleted(
    node_id="node_abc123",
    node_type="ClickElementNode",
    workflow_id="wf_xyz789",
    execution_time_ms=150.5,
))
```

### Unsubscribing

```python
bus.unsubscribe(NodeCompleted, handle_node_completed)
```

### Wildcard Subscription

Subscribe to all events:

```python
def log_all_events(event) -> None:
    print(f"Event: {event.event_type_name}")

bus.subscribe_all(log_all_events)
```

### Event History

```python
# Get recent events
history = bus.get_history(NodeCompleted, limit=10)

# Get all recent events
all_history = bus.get_history(limit=50)
```

## Event Classes

### Base Classes

**Location**: `src/casare_rpa/domain/events/base.py`

#### DomainEvent

Base class for all domain events.

```python
@dataclass(frozen=True)
class DomainEvent(ABC):
    event_id: UUID = field(default_factory=uuid4)
    occurred_on: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]: ...
    @property
    def event_type_name(self) -> str: ...
```

#### AggregateEvent

Base class for events raised by aggregates.

```python
@dataclass(frozen=True)
class AggregateEvent(DomainEvent):
    aggregate_id: str = ""
```

---

## Node Events

**Location**: `src/casare_rpa/domain/events/node_events.py`

Events for node execution lifecycle.

### NodeStarted

Raised when a node begins execution.

| Attribute | Type | Description |
|-----------|------|-------------|
| `node_id` | `str` | Unique node identifier |
| `node_type` | `str` | Node class name (e.g., "ClickElementNode") |
| `workflow_id` | `str` | Parent workflow ID |

```python
from casare_rpa.domain.events import NodeStarted

event = NodeStarted(
    node_id="node_abc123",
    node_type="ClickElementNode",
    workflow_id="wf_xyz789",
)
```

### NodeCompleted

Raised when a node completes successfully.

| Attribute | Type | Description |
|-----------|------|-------------|
| `node_id` | `str` | Unique node identifier |
| `node_type` | `str` | Node class name |
| `workflow_id` | `str` | Parent workflow ID |
| `execution_time_ms` | `float` | Execution duration in milliseconds |
| `output_data` | `Optional[Dict]` | Node output data |

```python
from casare_rpa.domain.events import NodeCompleted

event = NodeCompleted(
    node_id="node_abc123",
    node_type="ClickElementNode",
    workflow_id="wf_xyz789",
    execution_time_ms=150.5,
    output_data={"clicked": True},
)
```

### NodeFailed

Raised when a node encounters an error.

| Attribute | Type | Description |
|-----------|------|-------------|
| `node_id` | `str` | Unique node identifier |
| `node_type` | `str` | Node class name |
| `workflow_id` | `str` | Parent workflow ID |
| `error_code` | `Optional[ErrorCode]` | Standardized error code |
| `error_message` | `str` | Human-readable error |
| `is_retryable` | `bool` | Whether error is retryable |

```python
from casare_rpa.domain.events import NodeFailed
from casare_rpa.domain.value_objects.types import ErrorCode

event = NodeFailed(
    node_id="node_abc123",
    node_type="ClickElementNode",
    workflow_id="wf_xyz789",
    error_code=ErrorCode.ELEMENT_NOT_FOUND,
    error_message="Element '#submit-btn' not found",
    is_retryable=True,
)
```

### NodeSkipped

Raised when a node is skipped (e.g., conditional logic).

| Attribute | Type | Description |
|-----------|------|-------------|
| `node_id` | `str` | Unique node identifier |
| `node_type` | `str` | Node class name |
| `workflow_id` | `str` | Parent workflow ID |
| `reason` | `str` | Why the node was skipped |

### NodeStatusChanged

Raised on any status transition.

| Attribute | Type | Description |
|-----------|------|-------------|
| `node_id` | `str` | Unique node identifier |
| `old_status` | `Optional[NodeStatus]` | Previous status |
| `new_status` | `Optional[NodeStatus]` | New status |

---

## Workflow Events

**Location**: `src/casare_rpa/domain/events/workflow_events.py`

### Execution Lifecycle Events

#### WorkflowStarted

Raised when workflow execution begins.

| Attribute | Type | Description |
|-----------|------|-------------|
| `workflow_id` | `str` | Workflow identifier |
| `workflow_name` | `str` | Display name |
| `execution_mode` | `ExecutionMode` | NORMAL, DEBUG, etc. |
| `triggered_by` | `str` | Trigger source (manual, schedule, api) |
| `total_nodes` | `int` | Total nodes in workflow |

```python
from casare_rpa.domain.events import WorkflowStarted
from casare_rpa.domain.value_objects.types import ExecutionMode

event = WorkflowStarted(
    workflow_id="wf_xyz789",
    workflow_name="Login Automation",
    execution_mode=ExecutionMode.NORMAL,
    triggered_by="manual",
    total_nodes=15,
)
```

#### WorkflowCompleted

Raised when workflow completes successfully.

| Attribute | Type | Description |
|-----------|------|-------------|
| `workflow_id` | `str` | Workflow identifier |
| `workflow_name` | `str` | Display name |
| `execution_time_ms` | `float` | Total execution time |
| `nodes_executed` | `int` | Nodes that ran |
| `nodes_skipped` | `int` | Nodes that were skipped |

#### WorkflowFailed

Raised when workflow fails.

| Attribute | Type | Description |
|-----------|------|-------------|
| `workflow_id` | `str` | Workflow identifier |
| `workflow_name` | `str` | Display name |
| `failed_node_id` | `Optional[str]` | Node that caused failure |
| `error_code` | `Optional[ErrorCode]` | Standardized error code |
| `error_message` | `str` | Error description |
| `execution_time_ms` | `float` | Time elapsed before failure |

#### WorkflowProgress

Raised to report execution progress.

| Attribute | Type | Description |
|-----------|------|-------------|
| `workflow_id` | `str` | Workflow identifier |
| `current_node_id` | `str` | Currently executing node |
| `completed_nodes` | `int` | Nodes completed |
| `total_nodes` | `int` | Total nodes |
| `percentage` | `float` | Progress 0-100 |

```python
from casare_rpa.domain.events import WorkflowProgress

event = WorkflowProgress(
    workflow_id="wf_xyz789",
    current_node_id="node_abc123",
    completed_nodes=5,
    total_nodes=15,
    percentage=33.3,
)
```

#### WorkflowPaused

Raised when workflow is paused (debug mode).

| Attribute | Type | Description |
|-----------|------|-------------|
| `workflow_id` | `str` | Workflow identifier |
| `paused_at_node_id` | `str` | Node where paused |
| `reason` | `str` | Why paused (breakpoint, step) |

#### WorkflowResumed

Raised when paused workflow resumes.

| Attribute | Type | Description |
|-----------|------|-------------|
| `workflow_id` | `str` | Workflow identifier |
| `resume_from_node_id` | `str` | Node where resuming |

#### WorkflowStopped

Raised when workflow is stopped by user.

| Attribute | Type | Description |
|-----------|------|-------------|
| `workflow_id` | `str` | Workflow identifier |
| `stopped_at_node_id` | `Optional[str]` | Node where stopped |
| `reason` | `str` | Why stopped |

### Workflow Structure Events

These events are raised by the Workflow aggregate when its structure changes.

#### NodeAdded

Raised when a node is added to workflow.

| Attribute | Type | Description |
|-----------|------|-------------|
| `workflow_id` | `str` | Workflow identifier |
| `node_id` | `str` | New node ID |
| `node_type` | `str` | Node type |
| `position_x` | `float` | X coordinate |
| `position_y` | `float` | Y coordinate |

#### NodeRemoved

Raised when a node is removed.

| Attribute | Type | Description |
|-----------|------|-------------|
| `workflow_id` | `str` | Workflow identifier |
| `node_id` | `str` | Removed node ID |

#### NodeConnected

Raised when nodes are connected.

| Attribute | Type | Description |
|-----------|------|-------------|
| `workflow_id` | `str` | Workflow identifier |
| `source_node` | `str` | Source node ID |
| `source_port` | `str` | Source port name |
| `target_node` | `str` | Target node ID |
| `target_port` | `str` | Target port name |

#### NodeDisconnected

Raised when connection is removed.

| Attribute | Type | Description |
|-----------|------|-------------|
| `workflow_id` | `str` | Workflow identifier |
| `source_node` | `str` | Source node ID |
| `source_port` | `str` | Source port name |
| `target_node` | `str` | Target node ID |
| `target_port` | `str` | Target port name |

---

## System Events

**Location**: `src/casare_rpa/domain/events/system_events.py`

### VariableSet

Raised when a variable is set.

| Attribute | Type | Description |
|-----------|------|-------------|
| `variable_name` | `str` | Variable name |
| `variable_value` | `Any` | New value |
| `workflow_id` | `str` | Workflow context |
| `source_node_id` | `Optional[str]` | Node that set it |

```python
from casare_rpa.domain.events import VariableSet

event = VariableSet(
    variable_name="login_url",
    variable_value="https://app.example.com",
    workflow_id="wf_xyz789",
    source_node_id="node_abc123",
)
```

### BrowserPageReady

Raised when browser page is ready.

| Attribute | Type | Description |
|-----------|------|-------------|
| `page_id` | `str` | Page identifier |
| `url` | `str` | Current URL |
| `title` | `str` | Page title |
| `browser_type` | `str` | chromium, firefox, webkit |

### LogMessage

Raised when a log message is emitted.

| Attribute | Type | Description |
|-----------|------|-------------|
| `level` | `LogLevel` | Log severity |
| `message` | `str` | Log content |
| `source` | `Optional[str]` | Source module/node |
| `node_id` | `Optional[str]` | Node if applicable |
| `workflow_id` | `Optional[str]` | Workflow if applicable |
| `extra_data` | `Optional[Dict]` | Additional data |

### DebugBreakpointHit

Raised when execution hits a breakpoint.

| Attribute | Type | Description |
|-----------|------|-------------|
| `node_id` | `str` | Node with breakpoint |
| `workflow_id` | `str` | Workflow ID |
| `variables` | `Optional[Dict]` | Current variable state |

### ResourceAcquired

Raised when a resource is acquired.

| Attribute | Type | Description |
|-----------|------|-------------|
| `resource_type` | `str` | Resource type (browser, database) |
| `resource_id` | `str` | Resource identifier |
| `workflow_id` | `str` | Acquiring workflow |

### ResourceReleased

Raised when a resource is released.

| Attribute | Type | Description |
|-----------|------|-------------|
| `resource_type` | `str` | Resource type |
| `resource_id` | `str` | Resource identifier |
| `workflow_id` | `str` | Releasing workflow |

---

## Creating Custom Events

To create a custom domain event:

```python
from dataclasses import dataclass
from typing import Any, Dict
from casare_rpa.domain.events.base import DomainEvent

@dataclass(frozen=True)
class CustomOperationCompleted(DomainEvent):
    """Raised when a custom operation completes."""

    operation_id: str = ""
    result_code: int = 0
    metadata: str = ""

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update({
            "operation_id": self.operation_id,
            "result_code": self.result_code,
            "metadata": self.metadata,
        })
        return result
```

---

## Qt Integration

The `QtDomainEventBridge` bridges domain events to Qt signals for UI updates.

**Location**: `src/casare_rpa/presentation/canvas/coordinators/event_bridge.py`

### Available Qt Signals

| Signal | Arguments | Domain Event |
|--------|-----------|--------------|
| `node_started` | node_id, node_type, workflow_id | `NodeStarted` |
| `node_completed` | node_id, node_type, execution_time_ms | `NodeCompleted` |
| `node_failed` | node_id, node_type, error_msg, retryable | `NodeFailed` |
| `workflow_started` | workflow_id, workflow_name, total_nodes | `WorkflowStarted` |
| `workflow_completed` | workflow_id, exec_time_ms, nodes_executed | `WorkflowCompleted` |
| `workflow_progress` | workflow_id, pct, completed, total | `WorkflowProgress` |
| `variable_set` | variable_name, value | `VariableSet` |

### Usage Example

```python
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Slot
from casare_rpa.presentation.canvas.coordinators import QtDomainEventBridge
from casare_rpa.domain.events import get_event_bus

class ExecutionPanel(QWidget):
    def __init__(self):
        super().__init__()

        # Create and start bridge
        self._bridge = QtDomainEventBridge(get_event_bus())
        self._bridge.node_started.connect(self._on_node_started)
        self._bridge.node_completed.connect(self._on_node_completed)
        self._bridge.workflow_progress.connect(self._on_progress)
        self._bridge.start()

    @Slot(str, str, str)
    def _on_node_started(self, node_id: str, node_type: str, workflow_id: str) -> None:
        self.highlight_node(node_id, "running")

    @Slot(str, str, float)
    def _on_node_completed(self, node_id: str, node_type: str, exec_time: float) -> None:
        self.highlight_node(node_id, "completed")

    @Slot(str, float, int, int)
    def _on_progress(self, workflow_id: str, pct: float, completed: int, total: int) -> None:
        self.progress_bar.setValue(int(pct))
```

---

## Utility Classes

### EventLogger

Log all events to console:

```python
from casare_rpa.domain.events import EventLogger, get_event_bus

logger = EventLogger(log_level="DEBUG")
logger.subscribe_to_bus(get_event_bus())
```

### EventRecorder

Record events for replay/analysis:

```python
from casare_rpa.domain.events import EventRecorder, get_event_bus

recorder = EventRecorder()
recorder.subscribe_to_bus(get_event_bus())

# Start recording
recorder.start_recording()

# ... execute workflow ...

# Stop and export
recorder.stop_recording()
events = recorder.export_to_dict()
```

---

## Best Practices

1. **Events are immutable**: Never try to modify an event after creation
2. **Events are self-describing**: The class name indicates what happened
3. **Use specific types**: Subscribe to specific event types, not all events
4. **Handle failures gracefully**: Event handlers should not throw
5. **Keep handlers fast**: Long-running work should be queued elsewhere
6. **Use Unit of Work**: Publish events after successful persistence

## Related Documentation

- [Overview](overview.md) - Architecture overview
- [Layers](layers.md) - Layer documentation
- [Aggregates](aggregates.md) - Workflow aggregate pattern
- [Diagrams](diagrams.md) - Architecture diagrams
