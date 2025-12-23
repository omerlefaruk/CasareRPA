"""
CasareRPA - EventBus

Thread-safe event bus for typed domain events.

Usage:
    from casare_rpa.domain.events import get_event_bus, NodeCompleted

    bus = get_event_bus()
    bus.subscribe(NodeCompleted, handler)
    bus.publish(NodeCompleted(node_id="x", execution_time_ms=100))
"""

import threading
from collections.abc import Callable
from typing import Any, Dict, List, Optional, Type

from loguru import logger

from casare_rpa.domain.events.base import DomainEvent
from casare_rpa.domain.events.system_events import LogMessage

# Handler type alias
EventHandler = Callable[[DomainEvent], None]


class EventBus:
    """
    Event bus for typed domain events.

    AI-HINT: Central pub/sub system for decoupled communication.
    AI-CONTEXT: Use get_event_bus() singleton. Don't instantiate directly.
    AI-WARNING: Handlers run synchronously. Don't block in handlers.

    Thread-safe publish/subscribe for DomainEvent subclasses.

    Common usage:
        bus = get_event_bus()
        bus.subscribe(NodeCompleted, my_handler)
        bus.publish(NodeCompleted(node_id="x", execution_time_ms=100))
    """

    def __init__(self) -> None:
        self._handlers: dict[type[DomainEvent], list[EventHandler]] = {}
        self._wildcard_handlers: list[EventHandler] = []
        self._event_history: list[DomainEvent] = []
        self._max_history_size = 1000
        self._lock = threading.Lock()

    def subscribe(
        self,
        event_type: type[DomainEvent],
        handler: EventHandler,
    ) -> None:
        """Subscribe handler to event type."""
        with self._lock:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            if handler not in self._handlers[event_type]:
                self._handlers[event_type].append(handler)

    def unsubscribe(
        self,
        event_type: type[DomainEvent],
        handler: EventHandler,
    ) -> None:
        """Unsubscribe handler from event type."""
        with self._lock:
            if event_type in self._handlers:
                try:
                    self._handlers[event_type].remove(handler)
                except ValueError:
                    pass

    def subscribe_all(self, handler: EventHandler) -> None:
        """Subscribe to all events (wildcard)."""
        with self._lock:
            if handler not in self._wildcard_handlers:
                self._wildcard_handlers.append(handler)

    def unsubscribe_all(self, handler: EventHandler) -> None:
        """Unsubscribe wildcard handler."""
        with self._lock:
            try:
                self._wildcard_handlers.remove(handler)
            except ValueError:
                pass

    def publish(self, event: DomainEvent) -> None:
        """Publish typed event to all subscribers."""
        with self._lock:
            self._event_history.append(event)
            if len(self._event_history) > self._max_history_size:
                self._event_history.pop(0)
            event_class = type(event)
            handlers = list(self._handlers.get(event_class, []))
            wildcard_handlers = list(self._wildcard_handlers)

        is_log = isinstance(event, LogMessage)

        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                if not is_log:
                    logger.error(f"Handler error for {event_class.__name__}: {e}")

        for handler in wildcard_handlers:
            try:
                handler(event)
            except Exception as e:
                if not is_log:
                    logger.error(f"Wildcard handler error: {e}")

    def get_history(
        self,
        event_type: type[DomainEvent] | None = None,
        limit: int | None = None,
    ) -> list[DomainEvent]:
        """Get event history (most recent first)."""
        with self._lock:
            history = self._event_history[::-1]
        if event_type:
            history = [e for e in history if isinstance(e, event_type)]
        if limit:
            history = history[:limit]
        return history

    def clear_history(self) -> None:
        """Clear event history."""
        with self._lock:
            self._event_history.clear()

    def clear_handlers(self, event_type: type[DomainEvent] | None = None) -> None:
        """Clear handlers for event type (or all)."""
        with self._lock:
            if event_type:
                self._handlers[event_type] = []
            else:
                self._handlers.clear()

    def get_handler_count(self, event_type: type[DomainEvent]) -> int:
        """Get handler count for event type."""
        with self._lock:
            return len(self._handlers.get(event_type, []))


# Singleton
_event_bus_instance: EventBus | None = None
_event_bus_lock = threading.Lock()


def get_event_bus() -> EventBus:
    """Get EventBus singleton."""
    global _event_bus_instance
    if _event_bus_instance is None:
        with _event_bus_lock:
            if _event_bus_instance is None:
                _event_bus_instance = EventBus()
    return _event_bus_instance


def reset_event_bus() -> None:
    """Reset EventBus singleton (for testing)."""
    global _event_bus_instance
    with _event_bus_lock:
        if _event_bus_instance:
            _event_bus_instance.clear_handlers()
            _event_bus_instance.clear_history()
        _event_bus_instance = None


class EventLogger:
    """Log events to console."""

    def __init__(self, log_level: str = "INFO") -> None:
        self.log_level = log_level

    def handle_event(self, event: DomainEvent) -> None:
        log_func = getattr(logger, self.log_level.lower(), logger.info)
        log_func(f"Event: {event.event_type_name} - {event.to_dict()}")

    def subscribe_to_bus(self, event_bus: EventBus) -> None:
        event_bus.subscribe_all(self.handle_event)


class EventRecorder:
    """Record events for replay/analysis."""

    def __init__(self) -> None:
        self.recorded_events: list[DomainEvent] = []
        self.is_recording = False
        self._lock = threading.Lock()

    def start_recording(self) -> None:
        with self._lock:
            self.is_recording = True
            self.recorded_events.clear()

    def stop_recording(self) -> None:
        with self._lock:
            self.is_recording = False

    def handle_event(self, event: DomainEvent) -> None:
        with self._lock:
            if self.is_recording:
                self.recorded_events.append(event)

    def get_recorded_events(self, event_type: type[DomainEvent] | None = None) -> list[DomainEvent]:
        with self._lock:
            events = self.recorded_events.copy()
        if event_type:
            events = [e for e in events if isinstance(e, event_type)]
        return events

    def export_to_dict(self) -> list[dict[str, Any]]:
        with self._lock:
            return [e.to_dict() for e in self.recorded_events]

    def subscribe_to_bus(self, event_bus: EventBus) -> None:
        event_bus.subscribe_all(self.handle_event)


__all__ = [
    "EventBus",
    "EventHandler",
    "EventLogger",
    "EventRecorder",
    "get_event_bus",
    "reset_event_bus",
]
