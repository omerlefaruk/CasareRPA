"""
Event system for Canvas UI.

This module provides a unified event bus system for component communication,
replacing scattered Qt signal/slot connections with a centralized, type-safe
event routing mechanism.

Components:
    - EventType: Enumeration of all event types
    - Event: Event data structure with metadata
    - EventBus: Central event routing singleton
    - EventHandler: Base class and decorators for event handlers
    - QtSignalBridge: Bridge between EventBus and Qt signals

Usage:
    from casare_rpa.presentation.canvas.events import (
        EventBus, EventType, Event, QtSignalBridge
    )

    # Get event bus instance
    event_bus = EventBus()

    # Subscribe to events
    def on_workflow_new(event: Event) -> None:
        print(f"New workflow: {event.data}")

    event_bus.subscribe(EventType.WORKFLOW_NEW, on_workflow_new)

    # Publish events
    event = Event(
        type=EventType.WORKFLOW_NEW,
        source="WorkflowController",
        data={"workflow_id": "123"}
    )
    event_bus.publish(event)
"""

from .event_types import EventType, EventCategory
from .event import Event, EventPriority, EventFilter
from .event_bus import EventBus
from .event_handler import EventHandler, event_handler
from .qt_signal_bridge import QtSignalBridge

__all__ = [
    "EventType",
    "EventCategory",
    "Event",
    "EventPriority",
    "EventFilter",
    "EventBus",
    "EventHandler",
    "event_handler",
    "QtSignalBridge",
]
