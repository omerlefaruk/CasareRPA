"""
Event system for Canvas UI.

This module provides a unified event bus system for component communication,
replacing scattered Qt signal/slot connections with a centralized, type-safe
event routing mechanism.

Components:
    - EventType: Enumeration of all event types (100+)
    - EventCategory: Event categories for filtering
    - Event: Immutable event data structure with metadata
    - EventPriority: Priority levels for event handling
    - EventFilter: Filter for subscribing to specific events
    - EventBus: Central event routing singleton with caching/metrics
    - EventHandler: Base class and decorators for event handlers
    - QtSignalBridge: Bridge between EventBus and Qt signals
    - EventBatcher: Batches high-frequency events (60fps)
    - LazySubscription: Visibility-based subscription optimization
    - DomainEventBridge: Bridge domain events to presentation layer
    - Event Contracts: TypedDict contracts for event data payloads

Usage:
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

    # Publish events with typed data
    from casare_rpa.presentation.canvas.events.event_contracts import WorkflowNewData

    data: WorkflowNewData = {"workflow_id": "123", "workflow_name": "My Flow"}
    event = Event(
        type=EventType.WORKFLOW_NEW,
        source="WorkflowController",
        data=data
    )
    event_bus.publish(event)

    # Start domain bridge to receive execution events
    bridge = start_domain_bridge()
"""

from casare_rpa.presentation.canvas.events.domain_bridge import (
    DomainEventBridge,
    start_domain_bridge,
)
from casare_rpa.presentation.canvas.events.event import (
    Event,
    EventFilter,
    EventPriority,
)
from casare_rpa.presentation.canvas.events.event_batcher import EventBatcher
from casare_rpa.presentation.canvas.events.event_bus import EventBus
from casare_rpa.presentation.canvas.events.event_handler import (
    EventHandler,
    event_handler,
)
from casare_rpa.presentation.canvas.events.event_types import EventCategory, EventType
from casare_rpa.presentation.canvas.events.lazy_subscription import (
    LazySubscription,
    LazySubscriptionGroup,
)
from casare_rpa.presentation.canvas.events.qt_signal_bridge import (
    QtEventEmitter,
    QtEventSubscriber,
    QtSignalBridge,
)

__all__ = [
    # Core types
    "EventType",
    "EventCategory",
    "Event",
    "EventPriority",
    "EventFilter",
    # Event bus
    "EventBus",
    # Handler utilities
    "EventHandler",
    "event_handler",
    # Qt integration
    "QtSignalBridge",
    "QtEventEmitter",
    "QtEventSubscriber",
    # Performance utilities
    "EventBatcher",
    "LazySubscription",
    "LazySubscriptionGroup",
    # Domain bridge
    "DomainEventBridge",
    "start_domain_bridge",
]
