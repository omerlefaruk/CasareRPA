# Canvas Events Index

```xml<events_index>
  <!-- Quick reference for Canvas event bus system. Use for fast discovery. -->

  <overview>
    <p>Unified event bus for component communication</p>
    <files>10 files</files>
    <exports>21 total</exports>
  </overview>

  <core_types>
    <e>EventType</e>       <s>event_types.py</s> <d>Enumeration of all event types (100+)</d>
    <e>EventCategory</e>   <s>event_types.py</s> <d>Event categories for filtering</d>
    <e>Event</e>           <s>event.py</s>      <d>Immutable event data structure</d>
    <e>EventPriority</e>   <s>event.py</s>      <d>HIGH, NORMAL, LOW</d>
    <e>EventFilter</e>     <s>event.py</s>      <d>Filter for subscribing to specific events</d>
  </core_types>

  <event_bus>
    <e>EventBus</e>        <s>event_bus.py</s>   <d>Central event routing singleton with caching/metrics</d>
  </event_bus>

  <handler_utils>
    <e>EventHandler</e>    <s>event_handler.py</s> <d>Base class for event handlers</d>
    <e>event_handler</e>   <s>event_handler.py</s> <d>Decorator for handler functions</d>
  </handler_utils>

  <qt_integration>
    <e>QtSignalBridge</e>  <s>qt_signal_bridge.py</s> <d>Bridge EventBus to Qt signals</d>
    <e>QtEventEmitter</e>  <s>qt_signal_bridge.py</s> <d>Emit Qt signals from events</d>
    <e>QtEventSubscriber</e> <s>qt_signal_bridge.py</s> <d>Subscribe to events via Qt</d>
  </qt_integration>

  <performance>
    <e>EventBatcher</e>    <s>event_batcher.py</s> <d>Batch high-frequency events (60fps)</d>
    <e>LazySubscription</e> <s>lazy_subscription.py</s> <d>Visibility-based optimization</d>
    <e>LazySubscriptionGroup</e> <s>lazy_subscription.py</s> <d>Group lazy subscriptions</d>
  </performance>

  <domain_bridge>
    <e>DomainEventBridge</e> <s>domain_bridge.py</s> <d>Bridge domain events to presentation</d>
    <e>start_domain_bridge()</e> <s>domain_bridge.py</s> <d>Start domain event bridge</d>
  </domain_bridge>

  <categories>
    <c>WORKFLOW</c>   <e>NEW, OPEN, SAVE, CLOSE, MODIFIED</e>
    <c>EXECUTION</c>  <e>START, PAUSE, STOP, NODE_STARTED, NODE_COMPLETED</e>
    <c>NODE</c>       <e>CREATED, DELETED, SELECTED, PROPERTY_CHANGED</e>
    <c>CONNECTION</c> <e>CREATED, DELETED</e>
    <c>VIEWPORT</c>   <e>ZOOM, PAN, FIT</e>
    <c>UI</c>         <e>PANEL_TOGGLED, THEME_CHANGED</e>
  </categories>

  <usage>
    <code>
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

# Event filtering
filter = EventFilter(category=EventCategory.WORKFLOW, priority=EventPriority.HIGH)
event_bus.subscribe_filtered(filter, handler)

# High-frequency batching
batcher = EventBatcher(interval_ms=16)  # 60fps
batcher.add(EventType.VIEWPORT_CHANGED, handler)
    </code>
  </usage>

  <related>
    <r>canvas.controllers</r> <d>Controllers publish/subscribe</d>
    <r>canvas.ui</r>         <d>UI components subscribe</d>
    <r>domain.events</r>      <d>Domain events bridged</d>
  </related>
</events_index>
```
