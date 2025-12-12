# Canvas Events Index

Quick reference for Canvas event bus system. Use for fast discovery.

## Overview

| Aspect | Description |
|--------|-------------|
| Purpose | Unified event bus for component communication |
| Files | 10 files |
| Exports | 21 total exports |

## Core Types

| Export | Source | Description |
|--------|--------|-------------|
| `EventType` | `event_types.py` | Enumeration of all event types (100+) |
| `EventCategory` | `event_types.py` | Event categories for filtering |
| `Event` | `event.py` | Immutable event data structure |
| `EventPriority` | `event.py` | Priority levels (HIGH, NORMAL, LOW) |
| `EventFilter` | `event.py` | Filter for subscribing to specific events |

## Event Bus

| Export | Source | Description |
|--------|--------|-------------|
| `EventBus` | `event_bus.py` | Central event routing singleton with caching/metrics |

## Handler Utilities

| Export | Source | Description |
|--------|--------|-------------|
| `EventHandler` | `event_handler.py` | Base class for event handlers |
| `event_handler` | `event_handler.py` | Decorator for handler functions |

## Qt Integration

| Export | Source | Description |
|--------|--------|-------------|
| `QtSignalBridge` | `qt_signal_bridge.py` | Bridge EventBus to Qt signals |
| `QtEventEmitter` | `qt_signal_bridge.py` | Emit Qt signals from events |
| `QtEventSubscriber` | `qt_signal_bridge.py` | Subscribe to events via Qt |

## Performance Utilities

| Export | Source | Description |
|--------|--------|-------------|
| `EventBatcher` | `event_batcher.py` | Batch high-frequency events (60fps) |
| `LazySubscription` | `lazy_subscription.py` | Visibility-based optimization |
| `LazySubscriptionGroup` | `lazy_subscription.py` | Group lazy subscriptions |

## Domain Bridge

| Export | Source | Description |
|--------|--------|-------------|
| `DomainEventBridge` | `domain_bridge.py` | Bridge domain events to presentation |
| `start_domain_bridge()` | `domain_bridge.py` | Start domain event bridge |

## Key Files

| File | Contains |
|------|----------|
| `event_types.py` | EventType, EventCategory enums |
| `event.py` | Event, EventPriority, EventFilter |
| `event_bus.py` | EventBus singleton |
| `event_handler.py` | EventHandler, decorator |
| `qt_signal_bridge.py` | Qt integration |
| `event_batcher.py` | High-frequency event batching |
| `lazy_subscription.py` | Lazy subscription optimization |
| `domain_bridge.py` | Domain event bridge |
| `event_contracts.py` | TypedDict contracts for event data |

## Usage Patterns

```python
from casare_rpa.presentation.canvas.events import (
    EventBus, EventType, Event, EventCategory, EventPriority,
    EventFilter, EventHandler, event_handler, QtSignalBridge,
    DomainEventBridge, start_domain_bridge,
)

# Get event bus instance (singleton)
event_bus = EventBus()

# Subscribe to events
def on_workflow_new(event: Event) -> None:
    print(f"New workflow: {event.data}")

event_bus.subscribe(EventType.WORKFLOW_NEW, on_workflow_new)

# Publish events
event = Event(
    type=EventType.WORKFLOW_NEW,
    source="WorkflowController",
    data={"workflow_id": "123", "workflow_name": "My Flow"}
)
event_bus.publish(event)

# Use decorator
@event_handler(EventType.NODE_SELECTED)
def handle_node_selected(event: Event) -> None:
    node_id = event.data["node_id"]
    print(f"Selected: {node_id}")

# Start domain bridge
bridge = start_domain_bridge()

# Event filtering
filter = EventFilter(
    category=EventCategory.WORKFLOW,
    priority=EventPriority.HIGH,
)
event_bus.subscribe_filtered(filter, handler)

# High-frequency batching
batcher = EventBatcher(interval_ms=16)  # 60fps
batcher.add(EventType.VIEWPORT_CHANGED, handler)
```

## Event Categories

| Category | Events |
|----------|--------|
| WORKFLOW | NEW, OPEN, SAVE, CLOSE, MODIFIED |
| EXECUTION | START, PAUSE, STOP, NODE_STARTED, NODE_COMPLETED |
| NODE | CREATED, DELETED, SELECTED, PROPERTY_CHANGED |
| CONNECTION | CREATED, DELETED |
| VIEWPORT | ZOOM, PAN, FIT |
| UI | PANEL_TOGGLED, THEME_CHANGED |

## Related Modules

| Module | Relation |
|--------|----------|
| `canvas.controllers` | Controllers publish/subscribe |
| `canvas.ui` | UI components subscribe |
| `domain.events` | Domain events bridged |
