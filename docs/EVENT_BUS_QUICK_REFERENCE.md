# EventBus Quick Reference

Quick reference guide for using the EventBus system in CasareRPA Canvas.

---

## Basic Usage

### 1. Subscribe to Events

```python
from casare_rpa.presentation.canvas.events import EventBus, EventType, Event

bus = EventBus()

def on_workflow_saved(event: Event) -> None:
    print(f"Saved: {event.data['file_path']}")

bus.subscribe(EventType.WORKFLOW_SAVED, on_workflow_saved)
```

### 2. Publish Events

```python
from casare_rpa.presentation.canvas.events import Event, EventType

event = Event(
    type=EventType.WORKFLOW_SAVED,
    source="WorkflowController",
    data={"file_path": "/path/to/file.json"}
)

bus.publish(event)
```

### 3. Unsubscribe

```python
bus.unsubscribe(EventType.WORKFLOW_SAVED, on_workflow_saved)
```

---

## Using EventHandler Base Class

```python
from casare_rpa.presentation.canvas.events import EventHandler, event_handler, EventType

class MyController(EventHandler):
    def __init__(self):
        super().__init__()
        self._auto_subscribe_decorated_handlers()

    @event_handler(EventType.WORKFLOW_SAVED)
    def on_workflow_saved(self, event: Event) -> None:
        print(f"Saved: {event.data['file_path']}")

    def save_workflow(self, path: Path) -> None:
        # ... save logic ...

        event = Event(
            type=EventType.WORKFLOW_SAVED,
            source=self.__class__.__name__,
            data={"file_path": str(path)}
        )
        self.publish(event)

    def cleanup(self):
        super().cleanup()  # Auto-unsubscribes
```

---

## Qt Widget Integration

### Using QtEventSubscriber

```python
from PySide6.QtWidgets import QWidget
from casare_rpa.presentation.canvas.events import QtEventSubscriber, EventType

class MyWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.subscriber = QtEventSubscriber(self)
        self.subscriber.subscribe(EventType.WORKFLOW_SAVED)
        self.subscriber.event_received.connect(self.on_event)

    def on_event(self, event: Event):
        if event.type == EventType.WORKFLOW_SAVED:
            self.statusBar().showMessage(f"Saved: {event.data['file_path']}")

    def closeEvent(self, event):
        self.subscriber.cleanup()
        super().closeEvent(event)
```

---

## Common Event Types

### Workflow Events
- `WORKFLOW_NEW` - New workflow created
- `WORKFLOW_OPENED` - Workflow loaded
- `WORKFLOW_SAVED` - Workflow saved
- `WORKFLOW_MODIFIED` - Unsaved changes
- `WORKFLOW_CLOSED` - Workflow closed

### Node Events
- `NODE_ADDED` - Node added
- `NODE_REMOVED` - Node removed
- `NODE_SELECTED` - Node selected
- `NODE_PROPERTY_CHANGED` - Property changed

### Execution Events
- `EXECUTION_STARTED` - Execution started
- `EXECUTION_COMPLETED` - Execution completed
- `EXECUTION_FAILED` - Execution failed
- `EXECUTION_PAUSED` - Execution paused

### UI Events
- `PANEL_TOGGLED` - Panel visibility changed
- `ZOOM_CHANGED` - Canvas zoom changed
- `THEME_CHANGED` - UI theme changed

---

## Event Filters

### Filter by Category

```python
from casare_rpa.presentation.canvas.events import EventFilter, EventCategory

filter = EventFilter(categories=[EventCategory.WORKFLOW])
bus.subscribe_filtered(filter, on_workflow_event)
```

### Filter by Priority

```python
from casare_rpa.presentation.canvas.events import EventPriority

filter = EventFilter(min_priority=EventPriority.HIGH)
bus.subscribe_filtered(filter, on_high_priority_event)
```

### Filter by Source

```python
filter = EventFilter(sources=["WorkflowController"])
bus.subscribe_filtered(filter, on_controller_event)
```

---

## Event Priorities

- `EventPriority.LOW` - Non-critical events
- `EventPriority.NORMAL` - Most events (default)
- `EventPriority.HIGH` - Important UI updates
- `EventPriority.CRITICAL` - System errors

```python
event = Event(
    type=EventType.ERROR_OCCURRED,
    source="System",
    data={"error": "Out of memory"},
    priority=EventPriority.CRITICAL
)
```

---

## Debugging

### View Event History

```python
# Get last 10 events
recent = bus.get_history(limit=10)

# Get workflow events
workflow_events = bus.get_history(category=EventCategory.WORKFLOW)

# Get events from controller
controller_events = bus.get_history(source="WorkflowController")
```

### Check Metrics

```python
metrics = bus.get_metrics()
print(f"Events published: {metrics['events_published']}")
print(f"Events handled: {metrics['events_handled']}")
print(f"Avg handler time: {metrics['avg_handler_time']:.4f}s")
print(f"Errors: {metrics['errors']}")
```

### Clear History

```python
bus.clear_history()
```

---

## Best Practices

1. **Always cleanup**: Call `cleanup()` when destroying components
2. **Use specific events**: Don't use generic events when specific ones exist
3. **Include data**: Add all relevant data to event payload
4. **Handle errors**: Wrap handler logic in try/except
5. **Keep handlers fast**: Offload heavy work to background threads
6. **Document events**: Document what events are published/subscribed

---

## Common Patterns

### Pattern 1: State Change Notification

```python
class WorkflowController(EventHandler):
    def set_modified(self, is_modified: bool):
        self._is_modified = is_modified

        event = Event(
            type=EventType.WORKFLOW_MODIFIED,
            source=self.__class__.__name__,
            data={"is_modified": is_modified}
        )
        self.publish(event)
```

### Pattern 2: Cross-Controller Communication

```python
class DebugController(EventHandler):
    def __init__(self):
        super().__init__()
        self.subscribe(EventType.EXECUTION_STARTED, self.on_execution_started)

    def on_execution_started(self, event: Event):
        # React to execution start
        self.enable_step_controls()
```

### Pattern 3: Event Correlation

```python
correlation_id = f"exec-{uuid.uuid4().hex[:8]}"

# Start event
start_event = Event(
    type=EventType.EXECUTION_STARTED,
    source="ExecutionController",
    correlation_id=correlation_id
)

# Complete event (same correlation_id)
complete_event = Event(
    type=EventType.EXECUTION_COMPLETED,
    source="ExecutionController",
    correlation_id=correlation_id
)
```

---

## Troubleshooting

### Events not received?
1. Check subscription: `bus.get_metrics()['subscribers']`
2. Verify event type matches
3. Ensure EventBus instance is same (singleton)
4. Check cleanup wasn't called prematurely

### Duplicate events?
1. Check for duplicate subscriptions
2. Verify cleanup() is called on destruction
3. EventBus should be singleton (check with `bus1 is bus2`)

### Memory leak?
1. Call cleanup() in destructors
2. Clear event history periodically: `bus.clear_history()`
3. Check for circular references

---

## Full Documentation

- **System Overview**: `docs/EVENT_BUS_SYSTEM.md`
- **Migration Guide**: `docs/EVENT_BUS_MIGRATION_GUIDE.md`
- **Implementation**: `docs/EVENT_BUS_IMPLEMENTATION_SUMMARY.md`

---

**Quick Reference Version**: 1.0.0
