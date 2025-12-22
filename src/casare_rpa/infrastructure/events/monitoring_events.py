"""
Monitoring event bus for real-time dashboard updates.

Provides async pub/sub system for orchestrator-level events:
- Job status changes (pending → running → completed/failed)
- Robot heartbeats (status, resource usage)
- Queue depth changes (jobs enqueued/dequeued)
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Callable, Dict, List, Optional
from threading import Lock
from collections import deque

from loguru import logger


class MonitoringEventType(Enum):
    """Event types for monitoring dashboard."""

    JOB_STATUS_CHANGED = auto()  # Job transitioned to new status
    ROBOT_HEARTBEAT = auto()  # Robot sent heartbeat
    QUEUE_DEPTH_CHANGED = auto()  # Queue depth updated


@dataclass
class MonitoringEvent:
    """
    Event for monitoring dashboard updates.

    Attributes:
        event_type: Type of event
        timestamp: When event occurred
        payload: Event-specific data
        correlation_id: Optional ID for request tracing
    """

    event_type: MonitoringEventType
    timestamp: datetime
    payload: Dict
    correlation_id: Optional[str] = None

    def to_dict(self) -> Dict:
        """Serialize event to dictionary."""
        return {
            "event_type": self.event_type.name,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
            "correlation_id": self.correlation_id,
        }


# Type alias for event handlers (async functions)
EventHandler = Callable[[MonitoringEvent], None]


class MonitoringEventBus:
    """
    Async pub/sub event bus for monitoring events.

    Features:
    - Thread-safe singleton
    - Async event handlers with error isolation
    - Event history ring buffer (debugging)
    - Fire-and-forget pattern (no blocking)

    Usage:
        # Subscribe
        bus = get_monitoring_event_bus()
        async def on_job_change(event: MonitoringEvent):
            print(f"Job {event.payload['job_id']} → {event.payload['new_status']}")

        bus.subscribe(MonitoringEventType.JOB_STATUS_CHANGED, on_job_change)

        # Publish
        await bus.publish(
            MonitoringEventType.JOB_STATUS_CHANGED,
            {"job_id": "123", "new_status": "completed"}
        )
    """

    _instance: Optional["MonitoringEventBus"] = None
    _lock: Lock = Lock()

    def __new__(cls) -> "MonitoringEventBus":
        """Thread-safe singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, max_history: int = 1000):
        """
        Initialize event bus.

        Args:
            max_history: Max events to keep in history buffer
        """
        if self._initialized:
            return

        self._handlers: Dict[MonitoringEventType, List[EventHandler]] = {}
        self._history: deque = deque(maxlen=max_history)
        self._initialized = True

        logger.info("MonitoringEventBus initialized")

    @classmethod
    def get_instance(cls) -> "MonitoringEventBus":
        """Get singleton instance."""
        return cls()

    def subscribe(self, event_type: MonitoringEventType, handler: EventHandler) -> None:
        """
        Subscribe to an event type.

        Args:
            event_type: Type of event to listen for
            handler: Async function with signature: async def handler(event: MonitoringEvent)
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        self._handlers[event_type].append(handler)
        logger.debug(
            f"Handler subscribed to {event_type.name} "
            f"({len(self._handlers[event_type])} total handlers)"
        )

    def unsubscribe(self, event_type: MonitoringEventType, handler: EventHandler) -> None:
        """
        Unsubscribe from an event type.

        Args:
            event_type: Event type
            handler: Handler to remove
        """
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
                logger.debug(f"Handler unsubscribed from {event_type.name}")
            except ValueError:
                logger.warning(f"Handler not found for {event_type.name} during unsubscribe")

    async def publish(
        self,
        event_type: MonitoringEventType,
        payload: Dict,
        correlation_id: Optional[str] = None,
    ) -> None:
        """
        Publish an event to all subscribed handlers.

        Fire-and-forget pattern: returns immediately, handlers run async.
        If a handler fails, logs error but continues with other handlers.

        Args:
            event_type: Type of event
            payload: Event-specific data
            correlation_id: Optional correlation ID for tracing
        """
        # Create event
        event = MonitoringEvent(
            event_type=event_type,
            timestamp=datetime.now(),
            payload=payload,
            correlation_id=correlation_id,
        )

        # Add to history
        self._history.append(event)

        # Get handlers
        if event_type not in self._handlers:
            logger.debug(f"No handlers for {event_type.name}, event logged in history")
            return

        handlers = self._handlers[event_type]
        logger.debug(
            f"Publishing {event_type.name} to {len(handlers)} handlers "
            f"(payload keys: {list(payload.keys())})"
        )

        # Call all handlers concurrently with error isolation
        tasks = []
        for i, handler in enumerate(handlers):
            try:
                # Ensure handler is async
                if asyncio.iscoroutinefunction(handler):
                    tasks.append(handler(event))
                else:
                    logger.warning(f"Handler {i} for {event_type.name} is not async, wrapping")

                    # Wrap sync handler
                    async def wrapped(h=handler, e=event):
                        h(e)

                    tasks.append(wrapped())
            except Exception as e:
                logger.error(f"Error preparing handler {i} for {event_type.name}: {e}")

        if tasks:
            # Run all handlers, don't let one failure stop others
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Log failures
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(
                        f"Handler {i} for {event_type.name} failed: {result}",
                        exc_info=result,
                    )

    def get_history(self, limit: int = 100) -> List[MonitoringEvent]:
        """
        Get recent event history.

        Args:
            limit: Max events to return

        Returns:
            List of recent events (newest first)
        """
        return list(self._history)[-limit:][::-1]

    def get_statistics(self) -> Dict:
        """
        Get event bus statistics for diagnostics.

        Returns:
            Dict with handler counts and recent event count
        """
        handler_counts = {
            event_type.name: len(handlers) for event_type, handlers in self._handlers.items()
        }

        return {
            "initialized": self._initialized,
            "handler_counts": handler_counts,
            "total_handlers": sum(handler_counts.values()),
            "history_size": len(self._history),
            "max_history": self._history.maxlen,
        }

    def clear_all(self) -> None:
        """Clear all subscriptions and history (for testing)."""
        self._handlers.clear()
        self._history.clear()
        logger.debug("All event handlers and history cleared")


def get_monitoring_event_bus() -> MonitoringEventBus:
    """
    Get the singleton MonitoringEventBus instance.

    Returns:
        Singleton event bus instance
    """
    return MonitoringEventBus.get_instance()
