# EventBus Migration Guide

**Version**: 1.0.0
**Target**: Canvas Controllers and Components
**Timeline**: Week 3-4 of Refactoring

---

## Overview

This guide provides step-by-step instructions for migrating from Qt signal/slot patterns to the EventBus system. The migration preserves backward compatibility while introducing modern event-driven architecture.

---

## Migration Strategy

### Phase 1: Dual Operation (Week 3 Day 4-5)

**Goal**: EventBus operates alongside existing Qt signals
**Breaking Changes**: None
**Duration**: 2 days

#### Actions:
1. Install EventBus system
2. Update controllers to publish to both EventBus and Qt signals
3. Add EventBus subscriptions alongside Qt signal connections
4. Test both systems work identically

#### Example:

```python
# WorkflowController - Phase 1
class WorkflowController(BaseController, EventHandler):
    # Keep existing Qt signals
    workflow_saved = Signal(str)

    def __init__(self, main_window):
        BaseController.__init__(self, main_window)
        EventHandler.__init__(self)

    def save_workflow(self, path: Path):
        # ... save logic ...

        # Emit Qt signal (old)
        self.workflow_saved.emit(str(path))

        # Publish to EventBus (new)
        event = Event(
            type=EventType.WORKFLOW_SAVED,
            source=self.__class__.__name__,
            data={"file_path": str(path)}
        )
        self.publish(event)
```

### Phase 2: New Code Uses EventBus (Week 4 Day 1-2)

**Goal**: All new features use EventBus exclusively
**Breaking Changes**: None (old code still uses Qt signals)
**Duration**: 2 days

#### Actions:
1. New controllers inherit from EventHandler
2. New components subscribe via EventBus
3. Qt widgets use QtSignalBridge for compatibility

#### Example:

```python
# New controller - Pure EventBus
class DebugController(EventHandler):
    def __init__(self):
        super().__init__()
        self._auto_subscribe_decorated_handlers()

    @event_handler(EventType.EXECUTION_STARTED)
    def on_execution_started(self, event: Event):
        # Handle execution start
        pass

    def enable_debug_mode(self):
        event = Event(
            type=EventType.DEBUG_MODE_ENABLED,
            source=self.__class__.__name__,
        )
        self.publish(event)
```

### Phase 3: Incremental Controller Migration (Week 4 Day 3-5)

**Goal**: Convert existing controllers one at a time
**Breaking Changes**: Minimal (isolated to each controller)
**Duration**: 3 days

#### Priority Order:
1. **WorkflowController** (highest impact)
2. **ExecutionController** (high impact)
3. **NodeController** (high impact)
4. **ConnectionController** (medium impact)
5. **PanelController** (medium impact)
6. **MenuController** (low impact)

#### Actions per Controller:
1. Add EventHandler inheritance
2. Replace signal emissions with event publishing
3. Update tests to use EventBus
4. Deprecate Qt signals (mark with warnings)
5. Update documentation

### Phase 4: Qt Signal Removal (Week 5+)

**Goal**: Remove deprecated Qt signals completely
**Breaking Changes**: Yes (coordinated with component updates)
**Duration**: Ongoing

#### Actions:
1. Remove deprecated Qt signal definitions
2. Remove dual-emit code
3. Update all components to use EventBus
4. Keep QtSignalBridge for Qt widget compatibility

---

## Step-by-Step Controller Migration

### Step 1: Add EventHandler Inheritance

**Before**:
```python
from .base_controller import BaseController

class WorkflowController(BaseController):
    def __init__(self, main_window):
        super().__init__(main_window)
```

**After**:
```python
from .base_controller import BaseController
from ..events import EventHandler

class WorkflowController(BaseController, EventHandler):
    def __init__(self, main_window):
        BaseController.__init__(self, main_window)
        EventHandler.__init__(self)
        self._auto_subscribe_decorated_handlers()
```

### Step 2: Map Qt Signals to Event Types

Create a mapping document for your controller:

| Qt Signal | Event Type | Data Fields |
|-----------|-----------|-------------|
| `workflow_created` | `WORKFLOW_NEW` | `name: str` |
| `workflow_loaded` | `WORKFLOW_OPENED` | `file_path: str, name: str` |
| `workflow_saved` | `WORKFLOW_SAVED` | `file_path: str` |
| `workflow_closed` | `WORKFLOW_CLOSED` | - |
| `modified_changed` | `WORKFLOW_MODIFIED` | `is_modified: bool` |

### Step 3: Replace Signal Emissions

**Before**:
```python
def save_workflow(self, path: Path):
    # ... save logic ...
    self.workflow_saved.emit(str(path))
    self.modified_changed.emit(False)
```

**After**:
```python
def save_workflow(self, path: Path):
    # ... save logic ...

    # Publish WORKFLOW_SAVED event
    event = Event(
        type=EventType.WORKFLOW_SAVED,
        source=self.__class__.__name__,
        data={"file_path": str(path)}
    )
    self.publish(event)

    # Publish WORKFLOW_MODIFIED event
    event = Event(
        type=EventType.WORKFLOW_MODIFIED,
        source=self.__class__.__name__,
        data={"is_modified": False}
    )
    self.publish(event)
```

### Step 4: Replace Signal Subscriptions

**Before**:
```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.workflow_controller = WorkflowController(self)
        self.workflow_controller.workflow_saved.connect(self.on_workflow_saved)

    def on_workflow_saved(self, file_path: str):
        self.statusBar().showMessage(f"Saved: {file_path}")
```

**After**:
```python
class MainWindow(QMainWindow, EventHandler):
    def __init__(self):
        QMainWindow.__init__(self)
        EventHandler.__init__(self)

        self.workflow_controller = WorkflowController(self)

        # Subscribe to events
        self.subscribe(EventType.WORKFLOW_SAVED, self.on_workflow_saved)

    def on_workflow_saved(self, event: Event):
        file_path = event.data['file_path']
        self.statusBar().showMessage(f"Saved: {file_path}")
```

### Step 5: Update Tests

**Before**:
```python
def test_workflow_saved_signal(qtbot):
    controller = WorkflowController(None)

    with qtbot.waitSignal(controller.workflow_saved):
        controller.save_workflow(Path("test.json"))
```

**After**:
```python
def test_workflow_saved_event():
    bus = EventBus()
    received_events = []

    def handler(event: Event):
        received_events.append(event)

    bus.subscribe(EventType.WORKFLOW_SAVED, handler)

    controller = WorkflowController(None)
    controller.save_workflow(Path("test.json"))

    assert len(received_events) == 1
    assert received_events[0].type == EventType.WORKFLOW_SAVED
    assert received_events[0].data['file_path'] == "test.json"
```

### Step 6: Cleanup

**Before**:
```python
class WorkflowController(BaseController):
    # Qt signals
    workflow_created = Signal()
    workflow_loaded = Signal(str)
    workflow_saved = Signal(str)
    # ... more signals ...

    def __init__(self, main_window):
        super().__init__(main_window)

    # No cleanup needed for Qt signals
```

**After**:
```python
class WorkflowController(BaseController, EventHandler):
    # No Qt signals needed!

    def __init__(self, main_window):
        BaseController.__init__(self, main_window)
        EventHandler.__init__(self)

    def cleanup(self):
        # Unsubscribe from all events
        super().cleanup()
```

---

## Qt Widget Integration

Qt widgets can't directly use EventHandler (they're QWidgets). Use one of these patterns:

### Pattern 1: QtEventSubscriber

```python
from PySide6.QtWidgets import QWidget
from casare_rpa.presentation.canvas.events import QtEventSubscriber, EventType

class MyPanel(QWidget):
    def __init__(self):
        super().__init__()

        # Create subscriber
        self.event_subscriber = QtEventSubscriber(self)

        # Subscribe to events
        self.event_subscriber.subscribe(EventType.WORKFLOW_SAVED)
        self.event_subscriber.subscribe(EventType.WORKFLOW_OPENED)

        # Connect to slot
        self.event_subscriber.event_received.connect(self.on_event)

    def on_event(self, event: Event):
        if event.type == EventType.WORKFLOW_SAVED:
            self.update_status(f"Saved: {event.data['file_path']}")
        elif event.type == EventType.WORKFLOW_OPENED:
            self.load_workflow(event.data['file_path'])

    def closeEvent(self, event):
        # Cleanup subscriptions
        self.event_subscriber.cleanup()
        super().closeEvent(event)
```

### Pattern 2: QtSignalBridge

```python
from PySide6.QtWidgets import QWidget
from casare_rpa.presentation.canvas.events import QtSignalBridge

class MyWidget(QWidget):
    def __init__(self):
        super().__init__()

        # Create bridge
        self.signal_bridge = QtSignalBridge(self)

        # Connect to category signals
        self.signal_bridge.workflow_event.connect(self.on_workflow_event)
        self.signal_bridge.execution_event.connect(self.on_execution_event)

    def on_workflow_event(self, event: Event):
        # Handle any workflow event
        print(f"Workflow event: {event.type.name}")

    def on_execution_event(self, event: Event):
        # Handle any execution event
        print(f"Execution event: {event.type.name}")
```

### Pattern 3: Composition (Recommended)

```python
from PySide6.QtWidgets import QWidget
from casare_rpa.presentation.canvas.events import EventHandler

class MyWidget(QWidget):
    def __init__(self):
        super().__init__()

        # Create event handler as component
        self.event_handler = EventHandler()

        # Subscribe via component
        self.event_handler.subscribe(
            EventType.WORKFLOW_SAVED,
            self.on_workflow_saved
        )

    def on_workflow_saved(self, event: Event):
        self.statusBar().showMessage(f"Saved: {event.data['file_path']}")

    def closeEvent(self, event):
        # Cleanup
        self.event_handler.cleanup()
        super().closeEvent(event)
```

---

## Common Patterns

### Pattern 1: Controller to Controller Communication

**Before** (Direct signal connection):
```python
class ExecutionController(BaseController):
    execution_started = Signal()

class DebugController(BaseController):
    def __init__(self, execution_controller):
        super().__init__()
        execution_controller.execution_started.connect(self.on_execution_started)

    def on_execution_started(self):
        # Handle execution start
        pass
```

**After** (EventBus):
```python
class ExecutionController(EventHandler):
    def start_execution(self):
        # ... start logic ...
        event = Event(
            type=EventType.EXECUTION_STARTED,
            source=self.__class__.__name__,
        )
        self.publish(event)

class DebugController(EventHandler):
    def __init__(self):
        super().__init__()
        self.subscribe(EventType.EXECUTION_STARTED, self.on_execution_started)

    def on_execution_started(self, event: Event):
        # Handle execution start
        pass
```

### Pattern 2: One-to-Many Broadcasting

**Before** (Multiple signal connections):
```python
class WorkflowController(BaseController):
    workflow_modified = Signal(bool)

class MainWindow:
    def __init__(self):
        self.workflow_controller.workflow_modified.connect(self.update_title)

class StatusBar:
    def __init__(self):
        workflow_controller.workflow_modified.connect(self.update_indicator)

class RecentFiles:
    def __init__(self):
        workflow_controller.workflow_modified.connect(self.update_list)
```

**After** (Single event publish):
```python
class WorkflowController(EventHandler):
    def mark_modified(self):
        event = Event(
            type=EventType.WORKFLOW_MODIFIED,
            source=self.__class__.__name__,
            data={"is_modified": True}
        )
        self.publish(event)  # All subscribers receive

class MainWindow(EventHandler):
    def __init__(self):
        self.subscribe(EventType.WORKFLOW_MODIFIED, self.update_title)

class StatusBar(EventHandler):
    def __init__(self):
        self.subscribe(EventType.WORKFLOW_MODIFIED, self.update_indicator)

class RecentFiles(EventHandler):
    def __init__(self):
        self.subscribe(EventType.WORKFLOW_MODIFIED, self.update_list)
```

### Pattern 3: Event Chains

**Before** (Signal chains):
```python
# Controller A
self.step1_complete.emit()

# Controller B (connects to Controller A)
controller_a.step1_complete.connect(self.do_step2)

# Controller C (connects to Controller B)
controller_b.step2_complete.connect(self.do_step3)
```

**After** (Event chain):
```python
# Controller A
event = Event(type=EventType.STEP1_COMPLETE, source="ControllerA")
self.publish(event)

# Controller B
@event_handler(EventType.STEP1_COMPLETE)
def on_step1_complete(self, event: Event):
    # Do step 2
    event = Event(type=EventType.STEP2_COMPLETE, source="ControllerB")
    self.publish(event)

# Controller C
@event_handler(EventType.STEP2_COMPLETE)
def on_step2_complete(self, event: Event):
    # Do step 3
    pass
```

---

## Checklist

Use this checklist when migrating a controller:

### Pre-Migration
- [ ] Document all Qt signals used by controller
- [ ] Map Qt signals to EventType equivalents
- [ ] Identify all signal connections (subscribers)
- [ ] List all test files that need updating

### During Migration
- [ ] Add EventHandler inheritance
- [ ] Replace signal emissions with event publishing
- [ ] Update all subscribers to use EventBus
- [ ] Add event data to replace signal parameters
- [ ] Update tests to use EventBus
- [ ] Test all functionality works identically
- [ ] Add cleanup() calls where needed

### Post-Migration
- [ ] Remove Qt signal definitions
- [ ] Remove deprecated signal connections
- [ ] Update documentation
- [ ] Run full test suite
- [ ] Performance test (no regression)
- [ ] Code review

---

## Troubleshooting

### Issue: Events not being received

**Symptoms**: Handler not called when event is published

**Solutions**:
1. Verify subscription: `bus.get_metrics()['subscribers']`
2. Check event type matches exactly
3. Ensure EventBus instance is the same (use singleton)
4. Check handler wasn't cleaned up prematurely
5. Add logging to handler to verify it's registered

```python
def on_event(self, event: Event):
    logger.debug(f"Handler called: {event}")  # Add this
    # ... handler logic ...
```

### Issue: Duplicate events

**Symptoms**: Handler called multiple times for single event

**Solutions**:
1. Check for duplicate subscriptions
2. Verify cleanup() is called on controller destruction
3. Check for multiple EventBus instances (should be singleton)

```python
# Check subscribers
metrics = bus.get_metrics()
print(f"Total subscribers: {metrics['subscribers']}")

# EventBus should be singleton
bus1 = EventBus()
bus2 = EventBus()
assert bus1 is bus2  # Should be True
```

### Issue: Memory leak

**Symptoms**: Memory usage grows over time

**Solutions**:
1. Ensure cleanup() is called for all EventHandler instances
2. Check for circular references in event handlers
3. Clear event history periodically for long-running apps

```python
# In controller destructor
def __del__(self):
    self.cleanup()

# Clear history periodically
if len(bus.get_history()) > 1000:
    bus.clear_history()
```

### Issue: Qt widgets not receiving events

**Symptoms**: Qt widgets don't see EventBus events

**Solutions**:
1. Use QtEventSubscriber or QtSignalBridge
2. Process Qt events: `qapp.processEvents()`
3. Check Qt event loop is running

```python
# Use QtEventSubscriber for Qt widgets
class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.subscriber = QtEventSubscriber(self)
        self.subscriber.subscribe(EventType.WORKFLOW_SAVED)
        self.subscriber.event_received.connect(self.on_event)
```

### Issue: Handler errors not visible

**Symptoms**: Event handler fails silently

**Solutions**:
1. Check metrics for error count: `bus.get_metrics()['errors']`
2. Review logs (errors are logged with traceback)
3. Add try/except in handler for debugging

```python
def on_event(self, event: Event):
    try:
        # ... handler logic ...
    except Exception as e:
        logger.exception(f"Handler error: {e}")
        raise  # Re-raise for EventBus to log
```

---

## Performance Tips

### 1. Use Event Filters

Instead of subscribing to all events and filtering in handler:

**Inefficient**:
```python
@event_handler()  # Subscribes to everything
def on_event(self, event: Event):
    if event.type not in [EventType.WORKFLOW_SAVED, EventType.WORKFLOW_OPENED]:
        return
    # Handle event
```

**Efficient**:
```python
# Subscribe to specific events only
self.subscribe(EventType.WORKFLOW_SAVED, self.on_workflow_saved)
self.subscribe(EventType.WORKFLOW_OPENED, self.on_workflow_opened)
```

### 2. Batch Related Events

Instead of emitting event for each change:

**Inefficient**:
```python
for node in nodes:
    event = Event(type=EventType.NODE_PROPERTY_CHANGED, ...)
    self.publish(event)
```

**Efficient**:
```python
# Emit single event for batch
event = Event(
    type=EventType.NODES_UPDATED,
    data={"node_ids": [n.id for n in nodes]}
)
self.publish(event)
```

### 3. Offload Heavy Work

Don't do heavy processing in event handlers:

**Inefficient**:
```python
def on_workflow_saved(self, event: Event):
    # Heavy computation in handler
    result = expensive_operation(event.data)
```

**Efficient**:
```python
def on_workflow_saved(self, event: Event):
    # Queue work for background thread
    self.work_queue.put(lambda: expensive_operation(event.data))
```

---

## Best Practices

1. **Always Cleanup**: Call `cleanup()` when destroying controllers
2. **Use Descriptive Events**: Choose specific event types over generic ones
3. **Include Useful Data**: Add all relevant data to event payload
4. **Handle Errors**: Wrap handler logic in try/except
5. **Document Events**: Document what events are published and subscribed
6. **Test Events**: Write tests for event publishing and handling
7. **Monitor Metrics**: Check metrics periodically for performance issues
8. **Limit History**: Clear history in long-running applications

---

## Resources

- **Full Documentation**: `docs/EVENT_BUS_SYSTEM.md`
- **Example Controller**: `src/casare_rpa/presentation/canvas/controllers/example_workflow_controller.py`
- **Test Examples**: `tests/presentation/canvas/events/`
- **Architecture**: `REFACTORING_ROADMAP.md` Week 3 Day 4

---

**End of Migration Guide**
