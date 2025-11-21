"""
CasareRPA - Event System
Provides event-driven communication between components.
"""

from typing import Any, Callable, Dict, List, Optional
from datetime import datetime
from loguru import logger

from .types import EventData, EventType, NodeId


class Event:
    """Represents a single event."""

    def __init__(
        self,
        event_type: EventType,
        data: Optional[EventData] = None,
        node_id: Optional[NodeId] = None,
    ) -> None:
        """
        Initialize an event.

        Args:
            event_type: Type of event
            data: Event data payload
            node_id: ID of node that triggered the event (if applicable)
        """
        self.event_type = event_type
        self.data = data or {}
        self.node_id = node_id
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize event to dictionary."""
        return {
            "event_type": self.event_type.name,
            "data": self.data,
            "node_id": self.node_id,
            "timestamp": self.timestamp.isoformat(),
        }

    def __repr__(self) -> str:
        """String representation."""
        node_str = f", node={self.node_id}" if self.node_id else ""
        return f"Event({self.event_type.name}{node_str})"


# Type alias for event handler functions
EventHandler = Callable[[Event], None]


class EventBus:
    """
    Central event bus for publishing and subscribing to events.
    Implements the Observer pattern.
    """

    def __init__(self) -> None:
        """Initialize event bus."""
        self._handlers: Dict[EventType, List[EventHandler]] = {}
        self._event_history: List[Event] = []
        self._max_history_size = 1000  # Limit history to prevent memory issues

        logger.debug("Event bus initialized")

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """
        Subscribe a handler to an event type.

        Args:
            event_type: Type of event to listen for
            handler: Callback function to handle the event
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        self._handlers[event_type].append(handler)
        logger.debug(f"Handler subscribed to {event_type.name}")

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """
        Unsubscribe a handler from an event type.

        Args:
            event_type: Type of event
            handler: Handler to remove
        """
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
                logger.debug(f"Handler unsubscribed from {event_type.name}")
            except ValueError:
                logger.warning(f"Handler not found for {event_type.name}")

    def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribed handlers.

        Args:
            event: Event to publish
        """
        # Add to history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history_size:
            self._event_history.pop(0)

        # Call all handlers for this event type
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in event handler for {event.event_type.name}: {e}")

        logger.debug(f"Event published: {event}")

    def emit(
        self,
        event_type: EventType,
        data: Optional[EventData] = None,
        node_id: Optional[NodeId] = None,
    ) -> None:
        """
        Create and publish an event (convenience method).

        Args:
            event_type: Type of event
            data: Event data
            node_id: Node ID (if applicable)
        """
        event = Event(event_type, data, node_id)
        self.publish(event)

    def get_history(
        self, event_type: Optional[EventType] = None, limit: Optional[int] = None
    ) -> List[Event]:
        """
        Get event history.

        Args:
            event_type: Filter by event type (None for all events)
            limit: Maximum number of events to return

        Returns:
            List of events (most recent first)
        """
        history = self._event_history[::-1]  # Reverse to get most recent first

        if event_type:
            history = [e for e in history if e.event_type == event_type]

        if limit:
            history = history[:limit]

        return history

    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history.clear()
        logger.debug("Event history cleared")

    def clear_handlers(self, event_type: Optional[EventType] = None) -> None:
        """
        Clear event handlers.

        Args:
            event_type: Specific event type to clear (None for all)
        """
        if event_type:
            self._handlers[event_type] = []
            logger.debug(f"Handlers cleared for {event_type.name}")
        else:
            self._handlers.clear()
            logger.debug("All handlers cleared")

    def get_handler_count(self, event_type: EventType) -> int:
        """Get number of handlers for an event type."""
        return len(self._handlers.get(event_type, []))

    def __repr__(self) -> str:
        """String representation."""
        total_handlers = sum(len(handlers) for handlers in self._handlers.values())
        return (
            f"EventBus(event_types={len(self._handlers)}, "
            f"total_handlers={total_handlers}, "
            f"history_size={len(self._event_history)})"
        )


# Global event bus instance (singleton pattern)
_global_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """
    Get the global event bus instance (singleton).

    Returns:
        Global EventBus instance
    """
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
        logger.info("Global event bus created")
    return _global_event_bus


def reset_event_bus() -> None:
    """Reset the global event bus (primarily for testing)."""
    global _global_event_bus
    _global_event_bus = None
    logger.debug("Global event bus reset")


class EventLogger:
    """
    Utility class to log events to console/file.
    Can be subscribed to the event bus.
    """

    def __init__(self, log_level: str = "INFO") -> None:
        """
        Initialize event logger.

        Args:
            log_level: Logging level (INFO, DEBUG, etc.)
        """
        self.log_level = log_level

    def handle_event(self, event: Event) -> None:
        """
        Handle an event by logging it.

        Args:
            event: Event to log
        """
        log_func = getattr(logger, self.log_level.lower(), logger.info)
        node_str = f" [Node: {event.node_id}]" if event.node_id else ""
        log_func(f"Event: {event.event_type.name}{node_str} - {event.data}")

    def subscribe_all(self, event_bus: EventBus) -> None:
        """Subscribe to all event types on the bus."""
        for event_type in EventType:
            event_bus.subscribe(event_type, self.handle_event)
        logger.info("Event logger subscribed to all event types")


class EventRecorder:
    """
    Records events for replay or analysis.
    Useful for debugging and testing.
    """

    def __init__(self) -> None:
        """Initialize event recorder."""
        self.recorded_events: List[Event] = []
        self.is_recording = False

    def start_recording(self) -> None:
        """Start recording events."""
        self.is_recording = True
        self.recorded_events.clear()
        logger.info("Event recording started")

    def stop_recording(self) -> None:
        """Stop recording events."""
        self.is_recording = False
        logger.info(f"Event recording stopped. Recorded {len(self.recorded_events)} events")

    def handle_event(self, event: Event) -> None:
        """
        Handle an event by recording it.

        Args:
            event: Event to record
        """
        if self.is_recording:
            self.recorded_events.append(event)

    def get_recorded_events(self) -> List[Event]:
        """Get all recorded events."""
        return self.recorded_events.copy()

    def export_to_dict(self) -> List[Dict[str, Any]]:
        """Export recorded events as list of dictionaries."""
        return [event.to_dict() for event in self.recorded_events]

    def subscribe_all(self, event_bus: EventBus) -> None:
        """Subscribe to all event types on the bus."""
        for event_type in EventType:
            event_bus.subscribe(event_type, self.handle_event)
        logger.info("Event recorder subscribed to all event types")
