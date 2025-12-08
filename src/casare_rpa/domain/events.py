"""
CasareRPA - Domain Event System

Provides event-driven communication between components.
Implements the Observer pattern for loose coupling.

This is the canonical location for event system components (v3.0).
"""

from typing import Any, Callable, Dict, List, Optional
from datetime import datetime
from loguru import logger

from casare_rpa.domain.value_objects.types import EventData, EventType, NodeId


class Event:
    """Represents a single event."""

    # PERFORMANCE: __slots__ reduces memory per instance by ~40%
    # Prevents dynamic __dict__ creation for each Event object
    __slots__ = ("event_type", "data", "node_id", "timestamp")

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
        self._wildcard_handlers: List[EventHandler] = []  # Handlers for all events
        self._event_history: List[Event] = []
        self._max_history_size = 1000  # Limit history to prevent memory issues

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
            except ValueError:
                logger.warning(f"Handler not found for {event_type.name}")

    def subscribe_all(self, handler: EventHandler) -> None:
        """
        Subscribe to all events (wildcard subscription).

        Useful for logging, debugging, or analytics.

        Args:
            handler: Function to call for every event
        """
        if handler not in self._wildcard_handlers:
            self._wildcard_handlers.append(handler)

    def unsubscribe_all(self, handler: EventHandler) -> None:
        """
        Unsubscribe a wildcard handler.

        Args:
            handler: Handler to remove
        """
        try:
            self._wildcard_handlers.remove(handler)
        except ValueError:
            logger.warning("Wildcard handler not found")

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
                # Avoid logging LOG_MESSAGE events to prevent re-entrancy deadlock
                if event.event_type != EventType.LOG_MESSAGE:
                    logger.error(
                        f"Error in event handler for {event.event_type.name}: {e}"
                    )

        # Call wildcard handlers (subscribed to all events)
        for handler in self._wildcard_handlers:
            try:
                handler(event)
            except Exception as e:
                if event.event_type != EventType.LOG_MESSAGE:
                    logger.error(f"Error in wildcard handler: {e}")

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

    def clear_handlers(self, event_type: Optional[EventType] = None) -> None:
        """
        Clear event handlers.

        Args:
            event_type: Specific event type to clear (None for all)
        """
        if event_type:
            self._handlers[event_type] = []
        else:
            self._handlers.clear()

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


# Module-level singleton with thread-safe lazy initialization
import threading

_event_bus_instance: Optional[EventBus] = None
_event_bus_lock = threading.Lock()


def _get_event_bus_singleton() -> EventBus:
    """Get or create the event bus singleton with double-checked locking."""
    _local_instance = _event_bus_instance
    if _local_instance is None:
        with _event_bus_lock:
            _local_instance = _event_bus_instance
            if _local_instance is None:
                _local_instance = EventBus()
                globals()["_event_bus_instance"] = _local_instance
    return _local_instance


def get_event_bus() -> EventBus:
    """
    Get the event bus instance (singleton).

    Thread-safe lazy initialization.

    Returns:
        EventBus instance
    """
    return _get_event_bus_singleton()


def reset_event_bus() -> None:
    """
    Reset the event bus singleton (primarily for testing).

    Thread-safe cleanup of the singleton.
    """
    with _event_bus_lock:
        _local_instance = _event_bus_instance
        if _local_instance is not None:
            _local_instance.clear_handlers()
            _local_instance.clear_history()
        globals()["_event_bus_instance"] = None
    logger.debug("Event bus reset")


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
        logger.info(
            f"Event recording stopped. Recorded {len(self.recorded_events)} events"
        )

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


# Re-export EventType from value_objects for convenience
from casare_rpa.domain.value_objects.types import EventType

__all__ = [
    "Event",
    "EventBus",
    "EventHandler",
    "EventLogger",
    "EventRecorder",
    "EventType",
    "get_event_bus",
    "reset_event_bus",
]
