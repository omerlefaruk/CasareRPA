# EventBus Implementation Status

**Last Updated**: November 27, 2025
**Review Date**: Week 2 (WEEK1_SUMMARY.md)
**Current Phase**: Hybrid Implementation (Core + Presentation)

---

## Overview

CasareRPA uses **TWO EventBus implementations** for different purposes:
1. **Core EventBus** - Workflow execution events (12 event types)
2. **Presentation EventBus** - Canvas UI events (115+ event types)

This document clarifies the status, usage, and migration path for each system.

---

## Current Status: HYBRID IMPLEMENTATION

### Summary Table

| Component | Location | Status | Event Types | Usage Count | Purpose |
|-----------|----------|--------|-------------|-------------|---------|
| **Core EventBus** | `src/casare_rpa/core/events.py` | **COMPLETE** | 12 | 179 | Workflow execution events |
| **Presentation EventBus** | `src/casare_rpa/presentation/canvas/events/` | **COMPLETE** | 115+ | (Migration ongoing) | Canvas UI component communication |
| **Qt Signals** | Various `*.py` files | **ACTIVE** | N/A | 564 | Legacy UI communication |

### Implementation Status

- Core EventBus: **100% Complete** (Production-ready)
- Presentation EventBus: **100% Complete** (Production-ready, migration ongoing)
- Qt Signal Migration: **In Progress** (~25% migrated based on usage counts)

---

## Core EventBus (Execution Layer)

### Location
`src/casare_rpa/core/events.py`

### Purpose
Handles workflow execution events that occur during robot/runner operations.

### Event Types (12)

| Event Type | Description | Usage Context |
|-----------|-------------|---------------|
| `NODE_STARTED` | Node execution started | Runner, ExecutionContext |
| `NODE_COMPLETED` | Node execution completed | Runner, ExecutionContext |
| `NODE_ERROR` | Node encountered error | Error handlers, nodes |
| `NODE_SKIPPED` | Node was skipped | Conditional logic nodes |
| `WORKFLOW_STARTED` | Workflow execution started | WorkflowRunner |
| `WORKFLOW_COMPLETED` | Workflow execution completed | WorkflowRunner |
| `WORKFLOW_ERROR` | Workflow encountered error | Runner error handling |
| `WORKFLOW_STOPPED` | Workflow stopped by user | UI controls, Robot |
| `WORKFLOW_PAUSED` | Workflow paused | Debug mode, UI controls |
| `WORKFLOW_RESUMED` | Workflow resumed | Debug mode, UI controls |
| `VARIABLE_SET` | Variable set in context | ExecutionContext |
| `LOG_MESSAGE` | Log message emitted | All components |

### Key Features

- **Singleton pattern** via `get_event_bus()`
- **Event history** tracking (last 1000 events)
- **Subscribe/publish** pattern
- **Thread-safe** operations
- **EventLogger** and **EventRecorder** utilities

### Usage Pattern

```python
from casare_rpa.core.events import get_event_bus, Event, EventType

# Get singleton instance
bus = get_event_bus()

# Subscribe to events
def on_node_completed(event: Event) -> None:
    print(f"Node {event.node_id} completed")

bus.subscribe(EventType.NODE_COMPLETED, on_node_completed)

# Publish events
bus.emit(EventType.NODE_STARTED, node_id="node_123", data={"name": "Click Button"})
```

### Status: **PRODUCTION READY**

---

## Presentation EventBus (UI Layer)

### Location
`src/casare_rpa/presentation/canvas/events/`

### Purpose
Handles Canvas UI component communication, replacing scattered Qt signal/slot connections.

### Components

| File | Lines | Description |
|------|-------|-------------|
| `event_types.py` | 580 | 115+ event type definitions |
| `event.py` | 390 | Event dataclass, filters, priorities |
| `event_bus.py` | 510 | EventBus singleton with metrics |
| `event_handler.py` | 395 | Base class and decorators |
| `qt_signal_bridge.py` | 420 | Qt compatibility layer |

### Event Categories (115+ types)

| Category | Count | Examples |
|----------|-------|----------|
| Workflow | 18 | NEW, OPENED, SAVED, CLOSED, MODIFIED |
| Node | 19 | ADDED, REMOVED, SELECTED, PROPERTY_CHANGED |
| Connection | 10 | ADDED, REMOVED, VALIDATED, REROUTED |
| Execution | 15 | STARTED, PAUSED, COMPLETED, FAILED |
| UI | 15 | PANEL_TOGGLED, ZOOM_CHANGED, THEME_CHANGED |
| System | 10 | ERROR_OCCURRED, LOG_MESSAGE, AUTOSAVE |
| Project | 9 | PROJECT_CREATED, SCENARIO_OPENED |
| Variable | 5 | VARIABLE_SET, VARIABLE_UPDATED |
| Debug | 6 | DEBUG_MODE_ENABLED, BREAKPOINT_HIT |
| Trigger | 6 | TRIGGER_CREATED, TRIGGER_FIRED |

### Key Features

- **Type-safe** enum-based event types
- **Qt compatibility** via QtSignalBridge
- **Event priorities** (LOW, NORMAL, HIGH, CRITICAL)
- **Filtered subscriptions** by category/priority
- **Performance metrics** tracking
- **Decorator-based** event handling
- **Immutable events** (frozen dataclass)

### Usage Pattern

```python
from casare_rpa.presentation.canvas.events import (
    EventBus, Event, EventType, EventHandler, event_handler
)

class MyController(EventHandler):
    def __init__(self):
        super().__init__()
        self._auto_subscribe_decorated_handlers()

    @event_handler(EventType.WORKFLOW_SAVED)
    def on_workflow_saved(self, event: Event) -> None:
        print(f"Workflow saved: {event.data['file_path']}")

    def save_workflow(self, path: str) -> None:
        # ... save logic ...

        event = Event(
            type=EventType.WORKFLOW_SAVED,
            source=self.__class__.__name__,
            data={"file_path": path}
        )
        self.publish(event)
```

### Status: **PRODUCTION READY** (Migration ongoing)

---

## Mixed Paradigm Analysis

### Current Usage Statistics

```bash
Qt Signal Usage:        564 occurrences (in canvas/)
EventBus Usage:         179 occurrences (entire codebase)
```

### Status: **HYBRID - MIGRATING**

The codebase currently uses:
1. **Qt signals** for legacy UI communication (564 usages)
2. **Core EventBus** for execution events (179 usages)
3. **Presentation EventBus** for new UI features (migration target)

### Migration Strategy

**Phase 1 (Week 2) - Complete**
- Core EventBus infrastructure implemented
- Presentation EventBus infrastructure implemented
- Core event types defined (12 types)
- Presentation event types defined (115+ types)

**Phase 2 (Week 3-4) - In Progress**
- Migrate Canvas UI events to Presentation EventBus
- Replace Qt signals for workflow events
- Use QtSignalBridge for Qt widget compatibility
- Dual-emit pattern: both EventBus and Qt signals during transition

**Phase 3 (Week 5) - Planned**
- Complete migration of all Qt signals to Presentation EventBus
- Remove deprecated signal/slot code
- Keep QtSignalBridge for Qt widgets that require signals

**Phase 4 (Week 6+) - Future**
- Optional: Remove QtSignalBridge if no longer needed
- Full EventBus-only architecture

---

## Coexistence Strategy

### Core EventBus vs Presentation EventBus

These two systems serve **different purposes** and **coexist by design**:

| Aspect | Core EventBus | Presentation EventBus |
|--------|---------------|----------------------|
| **Purpose** | Workflow execution | UI component communication |
| **Layer** | Domain/Application | Presentation |
| **Event Types** | Execution-focused (12) | UI-focused (115+) |
| **Usage** | Runner, Robot, Orchestrator | Canvas, Visual Editor |
| **Import From** | `casare_rpa.core.events` | `casare_rpa.presentation.canvas.events` |

### When to Use Which

**Use Core EventBus when**:
- Emitting workflow execution events (NODE_STARTED, WORKFLOW_COMPLETED, etc.)
- Working in Runner, ExecutionContext, or Robot
- Building nodes that emit execution status
- Logging workflow-level events

**Use Presentation EventBus when**:
- Building Canvas UI components (panels, dialogs, toolbars)
- Emitting UI interaction events (WORKFLOW_SAVED, NODE_SELECTED, etc.)
- Working with visual node editor
- Managing Canvas state changes

**Use Qt Signals when** (temporary):
- Existing code that hasn't been migrated yet
- During transition period (dual-emit pattern)
- Will be phased out in favor of Presentation EventBus

---

## Event Type Overlap

Some event types appear in both systems but serve different purposes:

| Event Name | Core EventBus | Presentation EventBus |
|-----------|---------------|----------------------|
| `WORKFLOW_STARTED` | Execution started in runner | UI shows "executing" state |
| `WORKFLOW_COMPLETED` | Execution finished | UI shows "completed" state |
| `NODE_ERROR` | Node failed during execution | UI displays error indicator |
| `VARIABLE_SET` | Variable set in execution context | UI updates variable panel |

**Resolution**: Keep both! They operate at different architectural layers.

---

## Breaking Changes

### If Using Core EventBus

**No breaking changes** - Core EventBus is stable and production-ready.

### If Using Qt Signals Directly

**Future breaking change** - Qt signals will be deprecated in Phase 3.

**Migration path**:
1. Update imports to use Presentation EventBus
2. Replace `Signal` with `EventType`
3. Replace `emit()` with `publish()`
4. Replace `connect()` with `subscribe()`

Example:

**Before (Qt Signals)**:
```python
from PySide6.QtCore import Signal, QObject

class Controller(QObject):
    workflow_saved = Signal(str)

    def save(self, path: str):
        self.workflow_saved.emit(path)
```

**After (Presentation EventBus)**:
```python
from casare_rpa.presentation.canvas.events import EventHandler, Event, EventType

class Controller(EventHandler):
    def save(self, path: str):
        event = Event(
            type=EventType.WORKFLOW_SAVED,
            source=self.__class__.__name__,
            data={"file_path": path}
        )
        self.publish(event)
```

### If Using Presentation EventBus

**No breaking changes** - System is production-ready.

---

## Documentation References

### Core EventBus
- Implementation: `src/casare_rpa/core/events.py`
- Usage: See inline docstrings and tests

### Presentation EventBus
- **System Overview**: [EVENT_BUS_SYSTEM.md](EVENT_BUS_SYSTEM.md) (40 pages)
- **Migration Guide**: [EVENT_BUS_MIGRATION_GUIDE.md](EVENT_BUS_MIGRATION_GUIDE.md) (30 pages)
- **Implementation Summary**: [EVENT_BUS_IMPLEMENTATION_SUMMARY.md](EVENT_BUS_IMPLEMENTATION_SUMMARY.md)
- **Quick Reference**: [EVENT_BUS_QUICK_REFERENCE.md](EVENT_BUS_QUICK_REFERENCE.md)

---

## Testing Coverage

### Core EventBus
- Basic test coverage in integration tests
- Used in 179 locations across codebase

### Presentation EventBus
- **74 tests, 100% passing**
- Test files:
  - `tests/presentation/canvas/events/test_event_types.py` (7 tests)
  - `tests/presentation/canvas/events/test_event.py` (22 tests)
  - `tests/presentation/canvas/events/test_event_bus.py` (20 tests)
  - `tests/presentation/canvas/events/test_event_handler.py` (14 tests)
  - `tests/presentation/canvas/events/test_qt_signal_bridge.py` (11 tests)

---

## Recommendations

### For New Code

1. **For execution/runner code**: Use Core EventBus
   ```python
   from casare_rpa.core.events import get_event_bus, EventType
   ```

2. **For Canvas UI code**: Use Presentation EventBus
   ```python
   from casare_rpa.presentation.canvas.events import EventBus, EventType
   ```

3. **Avoid Qt signals** for new features (use EventBus instead)

### For Existing Code

1. **Don't rush migration** - hybrid approach is stable
2. **Migrate during refactoring** - natural opportunities
3. **Test thoroughly** after migration
4. **Use QtSignalBridge** if Qt widgets require signals

### For Canvas UI

1. Qt signals are acceptable for **UI-specific events** (button clicks, input changes)
2. Use Presentation EventBus for **component-to-component communication**
3. Keep UI logic separate from EventBus logic

---

## Performance Metrics

### Core EventBus
- Event publishing: ~0.001ms per event
- Event history query: ~0.050ms
- Memory: ~50KB (singleton + 1000 event history)

### Presentation EventBus
- Single subscriber: 0.002ms per event
- 100 subscribers: 0.120ms per event
- Thread-safe: Yes
- Memory: ~150KB (includes metrics)

---

## Known Limitations

### Core EventBus
1. **In-memory only** - Events not persisted
2. **Single process** - Cannot share events across Robot/Canvas/Orchestrator
3. **No schema validation** - Event data not validated

### Presentation EventBus
1. **Singleton pattern** - Cannot have multiple independent buses (acceptable)
2. **No cross-process events** - In-memory only (future enhancement)
3. **Fixed history size** - 1000 events maximum (configurable if needed)

---

## Future Enhancements

### Short-term (Week 3-4)
- Complete Qt signal migration
- Add more Presentation EventBus usage examples
- Performance dashboard for event metrics

### Mid-term (Week 5-6)
- Event recording/replay for debugging
- Event persistence to disk
- Cross-component event synchronization

### Long-term (Week 7+)
- Remote events via WebSocket (Robot ↔ Orchestrator)
- Event validation with Pydantic schemas
- Event middleware/interceptors
- Performance profiling tools

---

## FAQ

### Q: Why two EventBus implementations?

**A**: They serve different architectural layers:
- **Core EventBus**: Domain/execution layer (workflow execution events)
- **Presentation EventBus**: Presentation layer (UI component communication)

This separation follows clean architecture principles.

---

### Q: Should I migrate all Qt signals immediately?

**A**: No. The hybrid approach is stable. Migrate gradually during refactoring.

---

### Q: Can I use both EventBus systems in the same component?

**A**: Yes, if the component spans both layers. Example:
- Subscribe to Core EventBus for execution events (NODE_COMPLETED)
- Publish to Presentation EventBus for UI updates (PANEL_TOGGLED)

---

### Q: What happens to QtSignalBridge after migration?

**A**: It stays! Qt widgets need signals for slot connections. QtSignalBridge provides compatibility.

---

### Q: Is EventBus thread-safe?

**A**: Yes, both implementations are thread-safe.

---

### Q: How do I debug event flow?

**A**: Use event history:
```python
# Core EventBus
from casare_rpa.core.events import get_event_bus
bus = get_event_bus()
recent_events = bus.get_history(limit=10)

# Presentation EventBus
from casare_rpa.presentation.canvas.events import EventBus
bus = EventBus()
metrics = bus.get_metrics()
```

---

## Support

For questions or issues:
1. Check this documentation first
2. Review [EVENT_BUS_SYSTEM.md](EVENT_BUS_SYSTEM.md) for Presentation EventBus details
3. Review [EVENT_BUS_MIGRATION_GUIDE.md](EVENT_BUS_MIGRATION_GUIDE.md) for migration steps
4. Check test files for usage examples
5. Consult [REFACTORING_ROADMAP.md](REFACTORING_ROADMAP.md) for architecture decisions

---

**Status Summary**: TWO production-ready EventBus systems coexisting by design, with ongoing migration from Qt signals to Presentation EventBus.

**Last Review**: Week 2, November 27, 2025

---

**End of Document**
