# EventBus System Documentation

**Version**: 1.0.0
**Created**: November 27, 2025
**Status**: Production Ready

---

## Overview

The EventBus system provides a unified, type-safe event-driven architecture for Canvas UI component communication. It replaces scattered Qt signal/slot connections with a centralized event routing mechanism, enabling loose coupling between components while maintaining full Qt compatibility.

### Key Benefits

- **Loose Coupling**: Components communicate through events without direct dependencies
- **Type Safety**: Full type hints and compile-time event type checking
- **Debuggability**: Event history tracking and performance metrics
- **Qt Compatibility**: Seamless integration with existing Qt signal/slot code
- **Thread Safety**: Safe concurrent event publishing and subscription
- **Testability**: Easy to mock and test event-driven logic

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Components                            │
│  (Controllers, Views, Panels, Dialogs)                      │
└───────────┬─────────────────────────────────────┬───────────┘
            │                                     │
            │ Subscribe                   Publish │
            ▼                                     ▼
┌───────────────────────────────────────────────────────────┐
│                        EventBus                            │
│  - Event routing                                          │
│  - Subscription management                                │
│  - Event history                                          │
│  - Performance metrics                                    │
└───────────┬───────────────────────────────────────────────┘
            │
            │ Bidirectional
            ▼
┌───────────────────────────────────────────────────────────┐
│                   QtSignalBridge                           │
│  - Qt signal emission                                     │
│  - EventBus → Qt signals                                  │
│  - Qt signals → EventBus                                  │
└───────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. EventType (Enum)

Defines all possible event types in the system.

**Location**: `src/casare_rpa/presentation/canvas/events/event_types.py`

**Categories**:
- Workflow events (20+): NEW, OPENED, SAVED, CLOSED, MODIFIED, etc.
- Node events (20+): ADDED, REMOVED, SELECTED, PROPERTY_CHANGED, etc.
- Connection events (10+): ADDED, REMOVED, VALIDATED, etc.
- Execution events (15+): STARTED, PAUSED, RESUMED, STOPPED, COMPLETED, etc.
- UI events (15+): PANEL_TOGGLED, ZOOM_CHANGED, THEME_CHANGED, etc.
- System events (10+): ERROR_OCCURRED, LOG_MESSAGE, AUTOSAVE_TRIGGERED, etc.
- Project events (10+): PROJECT_CREATED, SCENARIO_OPENED, etc.
- Variable events (5+): VARIABLE_SET, VARIABLE_UPDATED, etc.
- Debug events (5+): DEBUG_MODE_ENABLED, BREAKPOINT_HIT, etc.
- Trigger events (5+): TRIGGER_CREATED, TRIGGER_FIRED, etc.

**Total**: 115+ event types

### 2. Event (Dataclass)

Immutable event object carrying event data.

**Attributes**:
- `type: EventType` - Event type
- `source: str` - Component that emitted the event
- `data: Optional[dict]` - Event payload
- `timestamp: float` - Unix timestamp
- `priority: EventPriority` - Event priority (LOW, NORMAL, HIGH, CRITICAL)
- `event_id: str` - Unique event identifier
- `correlation_id: Optional[str]` - Links related events

### 3. EventBus (Singleton)

Central event routing system.

**Key Methods**:
- `subscribe(event_type, handler)` - Subscribe to specific event type
- `subscribe_all(handler)` - Subscribe to all events (wildcard)
- `subscribe_filtered(filter, handler)` - Subscribe with custom filter
- `publish(event)` - Publish event to all subscribers
- `unsubscribe(event_type, handler)` - Unsubscribe from event type
- `get_history(...)` - Retrieve event history
- `get_metrics()` - Get performance metrics

### 4. EventHandler (Base Class)

Base class for event-driven components.

**Features**:
- Automatic subscription management
- Cleanup on destruction
- Subscription tracking
- Event publishing helper

### 5. QtSignalBridge

Bridge between EventBus and Qt signals.

**Signals**:
- `event_emitted` - Generic signal for all events
- `workflow_event` - Workflow-specific events
- `node_event` - Node-specific events
- `execution_event` - Execution-specific events
- (etc. for each category)

---

## Complete Event Catalog

### Workflow Events

| Event Type | Description | Data Fields |
|-----------|-------------|-------------|
| WORKFLOW_NEW | New workflow created | `name: str` |
| WORKFLOW_OPENED | Workflow loaded from file | `file_path: str, name: str` |
| WORKFLOW_SAVED | Workflow saved to file | `file_path: str` |
| WORKFLOW_SAVE_AS | Workflow saved with new name | `file_path: str, old_path: str` |
| WORKFLOW_CLOSED | Workflow closed | `file_path: Optional[str]` |
| WORKFLOW_MODIFIED | Workflow has unsaved changes | `is_modified: bool` |
| WORKFLOW_VALIDATED | Workflow validation completed | `errors: list[str]` |
| WORKFLOW_VALIDATION_FAILED | Validation found errors | `errors: list[str]` |
| WORKFLOW_IMPORTED | Workflow imported | `file_path: str` |
| WORKFLOW_EXPORTED | Workflow exported | `file_path: str` |
| WORKFLOW_DUPLICATED | Workflow duplicated | `original_id: str, new_id: str` |
| WORKFLOW_RENAMED | Workflow renamed | `old_name: str, new_name: str` |
| WORKFLOW_METADATA_UPDATED | Metadata changed | `metadata: dict` |
| WORKFLOW_UNDO | Undo operation | `action: str` |
| WORKFLOW_REDO | Redo operation | `action: str` |
| WORKFLOW_HISTORY_CLEARED | Undo/redo history cleared | - |
| WORKFLOW_TEMPLATE_APPLIED | Template applied | `template_name: str` |
| WORKFLOW_SAVED_AS_TEMPLATE | Saved as template | `template_name: str` |

### Node Events

| Event Type | Description | Data Fields |
|-----------|-------------|-------------|
| NODE_ADDED | Node added to workflow | `node_id: str, node_type: str, position: dict` |
| NODE_REMOVED | Node removed | `node_id: str` |
| NODE_DUPLICATED | Node duplicated | `original_id: str, new_id: str` |
| NODE_SELECTED | Node selected | `node_id: str` |
| NODE_DESELECTED | Node deselected | `node_id: str` |
| NODE_SELECTION_CHANGED | Selection changed | `selected_nodes: list[str]` |
| NODE_PROPERTY_CHANGED | Node property changed | `node_id: str, property: str, value: Any` |
| NODE_CONFIG_UPDATED | Node configuration updated | `node_id: str, config: dict` |
| NODE_POSITION_CHANGED | Node moved | `node_id: str, x: float, y: float` |
| NODE_RENAMED | Node renamed | `node_id: str, old_name: str, new_name: str` |
| NODE_ENABLED | Node enabled | `node_id: str` |
| NODE_DISABLED | Node disabled | `node_id: str` |
| NODE_BREAKPOINT_ADDED | Breakpoint added | `node_id: str` |
| NODE_BREAKPOINT_REMOVED | Breakpoint removed | `node_id: str` |
| NODES_GROUPED | Nodes grouped | `group_id: str, node_ids: list[str]` |
| NODES_UNGROUPED | Nodes ungrouped | `group_id: str` |
| NODE_CUT | Node cut to clipboard | `node_id: str` |
| NODE_COPIED | Node copied | `node_id: str` |
| NODE_PASTED | Node pasted | `node_id: str` |

### Connection Events

| Event Type | Description | Data Fields |
|-----------|-------------|-------------|
| CONNECTION_ADDED | Connection created | `source_node: str, target_node: str, source_port: str, target_port: str` |
| CONNECTION_REMOVED | Connection deleted | `source_node: str, target_node: str` |
| CONNECTION_SELECTED | Connection selected | `connection_id: str` |
| CONNECTION_DESELECTED | Connection deselected | `connection_id: str` |
| CONNECTION_VALIDATED | Connection validated | `connection_id: str, is_valid: bool` |
| CONNECTION_VALIDATION_FAILED | Validation failed | `connection_id: str, errors: list[str]` |
| CONNECTION_REROUTED | Connection rerouted | `connection_id: str, new_target: str` |
| PORT_CONNECTED | Port connected | `node_id: str, port_name: str` |
| PORT_DISCONNECTED | Port disconnected | `node_id: str, port_name: str` |
| PORT_VALUE_CHANGED | Port value changed | `node_id: str, port_name: str, value: Any` |

### Execution Events

| Event Type | Description | Data Fields |
|-----------|-------------|-------------|
| EXECUTION_STARTED | Workflow execution started | `workflow_id: str, variables: dict` |
| EXECUTION_PAUSED | Execution paused | `current_node: str` |
| EXECUTION_RESUMED | Execution resumed | `current_node: str` |
| EXECUTION_STOPPED | Execution stopped | `reason: str` |
| EXECUTION_COMPLETED | Execution completed successfully | `duration: float, result: dict` |
| EXECUTION_FAILED | Execution failed | `error: str, node_id: str` |
| EXECUTION_CANCELLED | Execution cancelled | `reason: str` |
| NODE_EXECUTION_STARTED | Node execution started | `node_id: str` |
| NODE_EXECUTION_COMPLETED | Node execution completed | `node_id: str, duration: float` |
| NODE_EXECUTION_FAILED | Node execution failed | `node_id: str, error: str` |
| NODE_EXECUTION_SKIPPED | Node execution skipped | `node_id: str, reason: str` |
| EXECUTION_STEP_INTO | Debug: step into | `node_id: str` |
| EXECUTION_STEP_OVER | Debug: step over | `node_id: str` |
| EXECUTION_STEP_OUT | Debug: step out | - |
| BREAKPOINT_HIT | Breakpoint hit | `node_id: str` |

### UI Events

| Event Type | Description | Data Fields |
|-----------|-------------|-------------|
| PANEL_OPENED | Panel opened | `panel_name: str` |
| PANEL_CLOSED | Panel closed | `panel_name: str` |
| PANEL_TOGGLED | Panel visibility toggled | `panel_name: str, visible: bool` |
| PANEL_RESIZED | Panel resized | `panel_name: str, size: dict` |
| PANEL_TAB_CHANGED | Panel tab changed | `panel_name: str, tab: str` |
| ZOOM_CHANGED | Canvas zoom changed | `zoom_level: float` |
| VIEW_CENTERED | View centered | - |
| VIEW_FIT_TO_SELECTION | View fitted to selection | `node_ids: list[str]` |
| MINIMAP_TOGGLED | Minimap visibility toggled | `visible: bool` |
| THEME_CHANGED | UI theme changed | `theme_name: str` |
| PREFERENCES_UPDATED | Preferences updated | `changed_keys: list[str]` |
| HOTKEY_TRIGGERED | Keyboard shortcut triggered | `action: str, key: str` |
| NODE_SEARCH_OPENED | Node search opened | - |
| NODE_FILTER_APPLIED | Node filter applied | `filter: str` |
| COMMAND_PALETTE_OPENED | Command palette opened | - |

### System Events

| Event Type | Description | Data Fields |
|-----------|-------------|-------------|
| LOG_MESSAGE | Log message | `level: str, message: str` |
| ERROR_OCCURRED | Error occurred | `error: str, source: str` |
| WARNING_ISSUED | Warning issued | `warning: str` |
| INFO_MESSAGE | Information message | `message: str` |
| DEBUG_OUTPUT | Debug output | `message: str` |
| PERFORMANCE_METRIC | Performance metric | `metric_name: str, value: float` |
| MEMORY_WARNING | Memory warning | `memory_mb: float` |
| AUTOSAVE_TRIGGERED | Autosave triggered | - |
| AUTOSAVE_COMPLETED | Autosave completed | `file_path: str` |
| AUTOSAVE_FAILED | Autosave failed | `error: str` |

### Project Events

| Event Type | Description | Data Fields |
|-----------|-------------|-------------|
| PROJECT_CREATED | Project created | `project_id: str, name: str` |
| PROJECT_OPENED | Project opened | `project_id: str` |
| PROJECT_CLOSED | Project closed | `project_id: str` |
| PROJECT_RENAMED | Project renamed | `project_id: str, old_name: str, new_name: str` |
| PROJECT_DELETED | Project deleted | `project_id: str` |
| SCENARIO_CREATED | Scenario created | `scenario_id: str, project_id: str` |
| SCENARIO_OPENED | Scenario opened | `scenario_id: str` |
| SCENARIO_DELETED | Scenario deleted | `scenario_id: str` |
| PROJECT_STRUCTURE_CHANGED | Project structure changed | `changes: list[dict]` |

### Variable Events

| Event Type | Description | Data Fields |
|-----------|-------------|-------------|
| VARIABLE_SET | Variable set | `name: str, value: Any, scope: str` |
| VARIABLE_UPDATED | Variable updated | `name: str, old_value: Any, new_value: Any` |
| VARIABLE_DELETED | Variable deleted | `name: str` |
| VARIABLE_CLEARED | All variables cleared | - |
| VARIABLE_SCOPE_CHANGED | Variable scope changed | `name: str, old_scope: str, new_scope: str` |

### Debug Events

| Event Type | Description | Data Fields |
|-----------|-------------|-------------|
| DEBUG_MODE_ENABLED | Debug mode enabled | - |
| DEBUG_MODE_DISABLED | Debug mode disabled | - |
| VARIABLE_INSPECTOR_UPDATED | Variable inspector updated | `variables: dict` |
| EXECUTION_TRACE_UPDATED | Execution trace updated | `trace: list[dict]` |
| WATCH_EXPRESSION_ADDED | Watch expression added | `expression: str` |
| WATCH_EXPRESSION_REMOVED | Watch expression removed | `expression: str` |

### Trigger Events

| Event Type | Description | Data Fields |
|-----------|-------------|-------------|
| TRIGGER_CREATED | Trigger created | `trigger_id: str, type: str` |
| TRIGGER_UPDATED | Trigger updated | `trigger_id: str, changes: dict` |
| TRIGGER_DELETED | Trigger deleted | `trigger_id: str` |
| TRIGGER_ENABLED | Trigger enabled | `trigger_id: str` |
| TRIGGER_DISABLED | Trigger disabled | `trigger_id: str` |
| TRIGGER_FIRED | Trigger fired | `trigger_id: str, workflow_id: str` |

---

## Event Flow Diagram

```
Component A (WorkflowController)
    │
    │ Creates Event
    ▼
┌─────────────────────────────────┐
│ Event(                          │
│   type=WORKFLOW_SAVED,          │
│   source="WorkflowController",  │
│   data={"file_path": "..."}     │
│ )                               │
└─────────────────────────────────┘
    │
    │ publish()
    ▼
┌─────────────────────────────────┐
│        EventBus                 │
│                                 │
│ 1. Add to history               │
│ 2. Update metrics               │
│ 3. Find subscribers             │
│ 4. Call handlers                │
└─────────────────────────────────┘
    │
    ├──────────────┬──────────────┬──────────────┐
    │              │              │              │
    ▼              ▼              ▼              ▼
Component B   Component C   QtSignalBridge  Component D
(Subscribed)  (Filtered)   (All events)    (Wildcard)
    │              │              │              │
    ▼              ▼              ▼              ▼
on_workflow_  on_workflow_   workflow_event  on_any_event()
  saved()      saved()          .emit()
```

---

## Usage Examples

### Basic Subscription and Publishing

```python
from casare_rpa.presentation.canvas.events import EventBus, Event, EventType

# Get event bus
bus = EventBus()

# Subscribe to events
def on_workflow_saved(event: Event) -> None:
    print(f"Workflow saved: {event.data['file_path']}")

bus.subscribe(EventType.WORKFLOW_SAVED, on_workflow_saved)

# Publish event
event = Event(
    type=EventType.WORKFLOW_SAVED,
    source="WorkflowController",
    data={"file_path": "/path/to/workflow.json"}
)
bus.publish(event)
```

### Using EventHandler Base Class

```python
from casare_rpa.presentation.canvas.events import (
    EventHandler, Event, EventType, event_handler
)

class MyController(EventHandler):
    def __init__(self):
        super().__init__()
        self._auto_subscribe_decorated_handlers()

    @event_handler(EventType.WORKFLOW_NEW)
    def on_workflow_new(self, event: Event) -> None:
        print(f"New workflow: {event.data['name']}")

    @event_handler(EventType.WORKFLOW_SAVED)
    def on_workflow_saved(self, event: Event) -> None:
        print(f"Workflow saved: {event.data['file_path']}")

    def save_workflow(self, path: Path) -> None:
        # ... save logic ...

        # Publish event
        event = Event(
            type=EventType.WORKFLOW_SAVED,
            source=self.__class__.__name__,
            data={"file_path": str(path)}
        )
        self.publish(event)
```

### Filtered Subscription

```python
from casare_rpa.presentation.canvas.events import EventFilter, EventCategory

# Subscribe to all workflow events
filter = EventFilter(categories=[EventCategory.WORKFLOW])
bus.subscribe_filtered(filter, on_workflow_event)

# Subscribe to high-priority execution events
filter = EventFilter(
    categories=[EventCategory.EXECUTION],
    min_priority=EventPriority.HIGH
)
bus.subscribe_filtered(filter, on_critical_execution_event)
```

### Qt Integration

```python
from PySide6.QtWidgets import QWidget
from casare_rpa.presentation.canvas.events import QtEventSubscriber, EventType

class MyWidget(QWidget):
    def __init__(self):
        super().__init__()

        # Create subscriber
        self.subscriber = QtEventSubscriber(self)

        # Subscribe to events
        self.subscriber.subscribe(EventType.WORKFLOW_SAVED)
        self.subscriber.subscribe(EventType.WORKFLOW_OPENED)

        # Connect to signal
        self.subscriber.event_received.connect(self.on_event)

    def on_event(self, event: Event) -> None:
        if event.type == EventType.WORKFLOW_SAVED:
            self.statusBar().showMessage(f"Saved: {event.data['file_path']}")
```

---

## Migration Guide

### From Qt Signals to EventBus

**Before (Qt Signals)**:
```python
class WorkflowController(QObject):
    workflow_saved = Signal(str)  # file_path

    def save_workflow(self, path: Path):
        # ... save logic ...
        self.workflow_saved.emit(str(path))

class MainWindow(QMainWindow):
    def __init__(self):
        self.controller = WorkflowController()
        self.controller.workflow_saved.connect(self.on_workflow_saved)

    def on_workflow_saved(self, file_path: str):
        self.statusBar().showMessage(f"Saved: {file_path}")
```

**After (EventBus)**:
```python
class WorkflowController(EventHandler):
    def save_workflow(self, path: Path):
        # ... save logic ...

        event = Event(
            type=EventType.WORKFLOW_SAVED,
            source=self.__class__.__name__,
            data={"file_path": str(path)}
        )
        self.publish(event)

class MainWindow(QMainWindow, EventHandler):
    def __init__(self):
        super().__init__()
        self.subscribe(EventType.WORKFLOW_SAVED, self.on_workflow_saved)

    def on_workflow_saved(self, event: Event):
        self.statusBar().showMessage(f"Saved: {event.data['file_path']}")
```

### Gradual Migration Strategy

1. **Phase 1**: Add EventBus alongside existing Qt signals
   - Publish to both EventBus and Qt signals
   - No breaking changes

2. **Phase 2**: Migrate new code to EventBus
   - All new features use EventBus exclusively
   - Use QtSignalBridge for Qt widget compatibility

3. **Phase 3**: Migrate existing code incrementally
   - Convert one controller at a time
   - Update tests to use EventBus
   - Remove deprecated Qt signals

4. **Phase 4**: Remove Qt signal dependencies
   - Keep only QtSignalBridge for Qt widgets
   - All controller communication via EventBus

---

## Performance Considerations

### Metrics

EventBus tracks performance metrics:
- Events published count
- Events handled count
- Total handler execution time
- Average handler execution time
- Error count
- Subscriber counts

```python
metrics = bus.get_metrics()
print(f"Events published: {metrics['events_published']}")
print(f"Avg handler time: {metrics['avg_handler_time']:.4f}s")
```

### Best Practices

1. **Handler Performance**
   - Keep handlers fast (< 100ms)
   - Offload heavy work to background threads
   - Avoid blocking operations in handlers

2. **Event Frequency**
   - Debounce high-frequency events (e.g., mouse move)
   - Batch related events when possible
   - Use priorities for time-critical events

3. **Memory Management**
   - Always call `cleanup()` when destroying components
   - Unsubscribe from events when no longer needed
   - Limit event history size for long-running applications

4. **Debugging**
   - Use event history for debugging event flow
   - Enable/disable history as needed
   - Monitor metrics for performance issues

---

## Debugging Guide

### Event History

```python
# Get last 10 events
recent = bus.get_history(limit=10)

# Get all workflow events
workflow_events = bus.get_history(category=EventCategory.WORKFLOW)

# Get events from specific source
controller_events = bus.get_history(source="WorkflowController")

# Clear history
bus.clear_history()
```

### Logging

All event operations are logged via loguru:
- Event subscription: `DEBUG` level
- Event publishing: `DEBUG` level
- Handler errors: `ERROR` level with traceback
- Slow handlers: `WARNING` level (> 100ms)

### Common Issues

**Issue**: Handler not being called
- Check subscription is active: `bus.get_metrics()['subscribers']`
- Verify event type matches
- Check if handler was cleaned up

**Issue**: Events not appearing in Qt widgets
- Use QtSignalBridge or QtEventSubscriber
- Process Qt events: `qapp.processEvents()`

**Issue**: Memory leak
- Ensure `cleanup()` is called for all EventHandler instances
- Check for circular references in handlers
- Monitor subscriber count

---

## Testing

### Unit Testing Events

```python
def test_event_subscription():
    bus = EventBus()
    received_events = []

    def handler(event: Event):
        received_events.append(event)

    bus.subscribe(EventType.WORKFLOW_NEW, handler)

    event = Event(type=EventType.WORKFLOW_NEW, source="Test")
    bus.publish(event)

    assert len(received_events) == 1
    assert received_events[0] == event
```

### Mocking EventBus

```python
def test_controller_publishes_event(mocker):
    # Mock EventBus
    mock_bus = mocker.Mock(spec=EventBus)

    # Create controller with mocked bus
    controller = WorkflowController()
    controller._event_bus = mock_bus

    # Perform action
    controller.save_workflow(Path("test.json"))

    # Verify event was published
    mock_bus.publish.assert_called_once()
    event = mock_bus.publish.call_args[0][0]
    assert event.type == EventType.WORKFLOW_SAVED
```

---

## API Reference

See individual module docstrings for complete API documentation:
- `event_types.py` - Event type definitions
- `event.py` - Event class and filters
- `event_bus.py` - EventBus singleton
- `event_handler.py` - EventHandler base class and decorators
- `qt_signal_bridge.py` - Qt integration

---

## Future Enhancements

Potential improvements for future versions:

1. **Event Replay**: Save and replay event sequences for debugging
2. **Event Recording**: Record events during execution for analysis
3. **Remote Events**: Publish events across network (Robot/Orchestrator sync)
4. **Event Validation**: Schema validation for event data
5. **Performance Profiling**: Built-in profiler for event flow
6. **Event Middleware**: Interceptors for event transformation/logging

---

## Support

For questions or issues with the EventBus system:
1. Check this documentation first
2. Review example controller implementations
3. Check test files for usage examples
4. Consult REFACTORING_ROADMAP.md for architecture decisions

---

**End of Document**
