"""
Central event bus for Canvas UI component communication.

The EventBus is a singleton that provides centralized event routing,
replacing scattered Qt signal/slot connections with a unified,
type-safe event system.

Features:
    - Type-safe event subscription and publishing
    - Event filtering by type, category, source, priority
    - Priority-based event handling
    - Event history for debugging
    - Performance metrics
    - Thread-safe operation

Usage:
    from casare_rpa.presentation.canvas.events import EventBus, Event, EventType

    # Get singleton instance
    bus = EventBus()

    # Subscribe to events
    def on_workflow_saved(event: Event) -> None:
        print(f"Workflow saved: {event.data['file_path']}")

    bus.subscribe(EventType.WORKFLOW_SAVED, on_workflow_saved)

    # Publish events
    event = Event(
        type=EventType.WORKFLOW_SAVED,
        source="WorkflowController",
        data={"file_path": "/path/to/workflow.json"}
    )
    bus.publish(event)

    # Unsubscribe
    bus.unsubscribe(EventType.WORKFLOW_SAVED, on_workflow_saved)
"""

from typing import Callable, Dict, List, Optional, Tuple, Any
from collections import defaultdict, deque
from threading import RLock
import time

from loguru import logger

from .event import Event, EventFilter
from .event_types import EventType, EventCategory

# Slow handler threshold in seconds (100ms)
SLOW_HANDLER_THRESHOLD_SEC = 0.1


# Type alias for event handler functions
EventHandler = Callable[[Event], None]


class EventBus:
    """
    Singleton event bus for centralized event routing.

    The EventBus allows components to communicate without direct coupling.
    Components publish events when something happens, and other components
    subscribe to events they care about.

    Thread Safety:
        All public methods are thread-safe using a re-entrant lock.

    Performance:
        - Event publishing: O(n) where n = number of subscribers
        - Event subscription: O(1)
        - Event unsubscription: O(n) where n = number of subscribers for that type

    Attributes:
        _instance: Singleton instance (class variable)
        _subscribers: Map of event types to handler lists
        _wildcard_subscribers: Handlers that receive all events
        _filtered_subscribers: Handlers with custom filters
        _history: Recent event history for debugging
        _metrics: Performance metrics
        _lock: Thread safety lock
    """

    _instance: Optional["EventBus"] = None
    _lock_class = RLock()

    def __new__(cls) -> "EventBus":
        """
        Ensure only one instance exists (Singleton pattern).

        Returns:
            EventBus: The singleton instance
        """
        with cls._lock_class:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        """Initialize the event bus (only runs once)."""
        if self._initialized:
            return

        # Subscriber storage
        self._subscribers: dict[EventType, list[EventHandler]] = defaultdict(list)
        self._wildcard_subscribers: list[EventHandler] = []
        self._filtered_subscribers: list[tuple[EventFilter, EventHandler]] = []

        # Event history (for debugging)
        self._history: deque[Event] = deque(maxlen=1000)
        self._history_enabled = True

        # Performance metrics
        self._metrics = {
            "events_published": 0,
            "events_handled": 0,
            "total_handler_time": 0.0,
            "errors": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

        # Filtered subscription cache: (EventType, source) -> List[EventHandler]
        # Cache invalidated on subscribe/unsubscribe for performance optimization
        self._filtered_cache: Dict[Tuple[EventType, str], List[EventHandler]] = {}

        # Thread safety
        self._lock = RLock()

        # Initialization complete
        self._initialized = True

        logger.debug("EventBus initialized")

    def subscribe(
        self,
        event_type: EventType,
        handler: EventHandler,
    ) -> None:
        """
        Subscribe to a specific event type.

        Args:
            event_type: Type of event to subscribe to
            handler: Function to call when event is published

        Raises:
            TypeError: If handler is not callable

        Example:
            def on_node_added(event: Event) -> None:
                print(f"Node added: {event.data['node_id']}")

            bus.subscribe(EventType.NODE_ADDED, on_node_added)
        """
        if not callable(handler):
            raise TypeError(f"Handler must be callable, got {type(handler)}")

        with self._lock:
            if handler not in self._subscribers[event_type]:
                self._subscribers[event_type].append(handler)
                self._invalidate_cache(event_type)
                logger.debug(
                    f"Subscribed to {event_type.name}: "
                    f"{handler.__name__ if hasattr(handler, '__name__') else handler}"
                )

    def subscribe_all(self, handler: EventHandler) -> None:
        """
        Subscribe to all events (wildcard subscription).

        Useful for logging, debugging, or analytics.

        Args:
            handler: Function to call for every event

        Raises:
            TypeError: If handler is not callable

        Example:
            def log_all_events(event: Event) -> None:
                logger.info(f"Event: {event}")

            bus.subscribe_all(log_all_events)
        """
        if not callable(handler):
            raise TypeError(f"Handler must be callable, got {type(handler)}")

        with self._lock:
            if handler not in self._wildcard_subscribers:
                self._wildcard_subscribers.append(handler)
                self._filtered_cache.clear()  # Wildcard affects all events
                logger.debug(f"Subscribed to all events: {handler.__name__}")

    def subscribe_filtered(
        self,
        event_filter: EventFilter,
        handler: EventHandler,
    ) -> None:
        """
        Subscribe to events matching a custom filter.

        Args:
            event_filter: Filter defining which events to receive
            handler: Function to call when matching event is published

        Raises:
            TypeError: If handler is not callable

        Example:
            # Subscribe to all workflow events
            filter = EventFilter(categories=[EventCategory.WORKFLOW])
            bus.subscribe_filtered(filter, on_workflow_event)

            # Subscribe to high-priority execution events
            filter = EventFilter(
                categories=[EventCategory.EXECUTION],
                min_priority=EventPriority.HIGH
            )
            bus.subscribe_filtered(filter, on_critical_execution_event)
        """
        if not callable(handler):
            raise TypeError(f"Handler must be callable, got {type(handler)}")

        with self._lock:
            filter_handler = (event_filter, handler)
            if filter_handler not in self._filtered_subscribers:
                self._filtered_subscribers.append(filter_handler)
                self._filtered_cache.clear()  # Filter may match any event
                logger.debug(f"Subscribed with filter: {event_filter}")

    def unsubscribe(
        self,
        event_type: EventType,
        handler: EventHandler,
    ) -> bool:
        """
        Unsubscribe from a specific event type.

        Args:
            event_type: Type of event to unsubscribe from
            handler: Handler function to remove

        Returns:
            bool: True if handler was found and removed, False otherwise

        Example:
            bus.unsubscribe(EventType.NODE_ADDED, on_node_added)
        """
        with self._lock:
            if event_type in self._subscribers:
                try:
                    self._subscribers[event_type].remove(handler)
                    self._invalidate_cache(event_type)
                    logger.debug(f"Unsubscribed from {event_type.name}")
                    return True
                except ValueError:
                    return False
            return False

    def unsubscribe_all(self, handler: EventHandler) -> bool:
        """
        Unsubscribe from all events (wildcard).

        Args:
            handler: Handler function to remove

        Returns:
            bool: True if handler was found and removed, False otherwise
        """
        with self._lock:
            try:
                self._wildcard_subscribers.remove(handler)
                self._filtered_cache.clear()  # Wildcard affects all events
                logger.debug(f"Unsubscribed from all events: {handler.__name__}")
                return True
            except ValueError:
                return False

    def unsubscribe_filtered(
        self,
        event_filter: EventFilter,
        handler: EventHandler,
    ) -> bool:
        """
        Unsubscribe from filtered events.

        Args:
            event_filter: Filter that was used for subscription
            handler: Handler function to remove

        Returns:
            bool: True if handler was found and removed, False otherwise
        """
        with self._lock:
            filter_handler = (event_filter, handler)
            try:
                self._filtered_subscribers.remove(filter_handler)
                self._filtered_cache.clear()  # Filter may match any event
                logger.debug(f"Unsubscribed from filter: {event_filter}")
                return True
            except ValueError:
                return False

    def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers.

        Events are delivered to:
        1. Type-specific subscribers
        2. Filtered subscribers (if filter matches)
        3. Wildcard subscribers (all events)

        Uses caching for filtered subscriber lists to improve performance
        on repeated events with the same type and source.

        Args:
            event: Event to publish

        Example:
            event = Event(
                type=EventType.WORKFLOW_SAVED,
                source="WorkflowController",
                data={"file_path": "/path/to/workflow.json"}
            )
            bus.publish(event)
        """
        with self._lock:
            # Update metrics
            self._metrics["events_published"] += 1

            # Add to history
            if self._history_enabled:
                self._history.append(event)

            # Log event
            logger.debug(f"Publishing event: {event}")

            # Build cache key: (event_type, source)
            source = event.source if hasattr(event, "source") and event.source else ""
            cache_key = (event.type, source)

            # Check cache for handlers
            if cache_key in self._filtered_cache:
                handlers = self._filtered_cache[cache_key]
                self._metrics["cache_hits"] += 1
            else:
                # Build and cache handler list
                handlers: List[EventHandler] = []

                # 1. Type-specific subscribers
                if event.type in self._subscribers:
                    handlers.extend(self._subscribers[event.type])

                # 2. Filtered subscribers
                for event_filter, handler in self._filtered_subscribers:
                    if event_filter.matches(event):
                        handlers.append(handler)

                # 3. Wildcard subscribers
                handlers.extend(self._wildcard_subscribers)

                # Cache the handler list
                self._filtered_cache[cache_key] = handlers
                self._metrics["cache_misses"] += 1

            # Call all handlers
            for handler in handlers:
                self._call_handler(handler, event)

    def _call_handler(self, handler: EventHandler, event: Event) -> None:
        """
        Call a single event handler with error handling.

        Args:
            handler: Handler function to call
            event: Event to pass to handler
        """
        try:
            start_time = time.perf_counter()

            handler(event)

            elapsed = time.perf_counter() - start_time

            # Update metrics
            self._metrics["events_handled"] += 1
            self._metrics["total_handler_time"] += elapsed

            # Warn if handler is slow
            if elapsed > SLOW_HANDLER_THRESHOLD_SEC:
                handler_name = (
                    handler.__name__ if hasattr(handler, "__name__") else str(handler)
                )
                logger.warning(
                    f"Slow event handler: {handler_name} took {elapsed * 1000:.2f}ms "
                    f"for {event.type.name}"
                )

        except Exception as e:
            self._metrics["errors"] += 1
            handler_name = (
                handler.__name__ if hasattr(handler, "__name__") else str(handler)
            )
            logger.error(
                f"Event handler error: {handler_name} failed processing {event.type.name}: {e}",
                exc_info=True,
            )

    def clear_history(self) -> None:
        """Clear event history."""
        with self._lock:
            self._history.clear()
            logger.debug("Event history cleared")

    def get_history(
        self,
        event_type: Optional[EventType] = None,
        category: Optional[EventCategory] = None,
        source: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[Event]:
        """
        Get event history with optional filtering.

        Args:
            event_type: Filter by event type
            category: Filter by event category
            source: Filter by event source
            limit: Maximum number of events to return

        Returns:
            list[Event]: Filtered event history (most recent first)

        Example:
            # Get all workflow events
            events = bus.get_history(category=EventCategory.WORKFLOW)

            # Get last 10 events
            events = bus.get_history(limit=10)

            # Get all events from WorkflowController
            events = bus.get_history(source="WorkflowController")
        """
        with self._lock:
            # Convert deque to list (most recent first)
            events = list(reversed(self._history))

            # Apply filters
            if event_type is not None:
                events = [e for e in events if e.type == event_type]

            if category is not None:
                events = [e for e in events if e.category == category]

            if source is not None:
                events = [e for e in events if e.source == source]

            # Apply limit
            if limit is not None:
                events = events[:limit]

            return events

    def get_metrics(self) -> dict[str, Any]:
        """
        Get performance metrics.

        Returns:
            dict: Metrics including event counts, timing, errors, and cache stats

        Example:
            metrics = bus.get_metrics()
            print(f"Events published: {metrics['events_published']}")
            print(f"Average handler time: {metrics['avg_handler_time']:.4f}s")
            print(f"Cache hit rate: {metrics['cache_hit_rate']:.2%}")
        """
        with self._lock:
            avg_handler_time = (
                self._metrics["total_handler_time"] / self._metrics["events_handled"]
                if self._metrics["events_handled"] > 0
                else 0.0
            )

            total_cache_accesses = (
                self._metrics["cache_hits"] + self._metrics["cache_misses"]
            )
            cache_hit_rate = (
                self._metrics["cache_hits"] / total_cache_accesses
                if total_cache_accesses > 0
                else 0.0
            )

            return {
                "events_published": self._metrics["events_published"],
                "events_handled": self._metrics["events_handled"],
                "total_handler_time": self._metrics["total_handler_time"],
                "avg_handler_time": avg_handler_time,
                "errors": self._metrics["errors"],
                "subscribers": sum(
                    len(handlers) for handlers in self._subscribers.values()
                ),
                "wildcard_subscribers": len(self._wildcard_subscribers),
                "filtered_subscribers": len(self._filtered_subscribers),
                "history_size": len(self._history),
                "cache_size": len(self._filtered_cache),
                "cache_hits": self._metrics["cache_hits"],
                "cache_misses": self._metrics["cache_misses"],
                "cache_hit_rate": cache_hit_rate,
            }

    def reset_metrics(self) -> None:
        """Reset performance metrics."""
        with self._lock:
            self._metrics = {
                "events_published": 0,
                "events_handled": 0,
                "total_handler_time": 0.0,
                "errors": 0,
                "cache_hits": 0,
                "cache_misses": 0,
            }
            logger.debug("Event bus metrics reset")

    def enable_history(self, enabled: bool = True) -> None:
        """
        Enable or disable event history tracking.

        Args:
            enabled: Whether to track event history
        """
        with self._lock:
            self._history_enabled = enabled
            logger.debug(f"Event history {'enabled' if enabled else 'disabled'}")

    def _invalidate_cache(self, event_type: EventType) -> None:
        """
        Invalidate filtered subscription cache for a specific event type.

        Called when subscriptions change to ensure cache consistency.

        Args:
            event_type: EventType whose cache entries should be invalidated
        """
        keys_to_remove = [k for k in self._filtered_cache.keys() if k[0] == event_type]
        for key in keys_to_remove:
            del self._filtered_cache[key]

    def clear_all_subscribers(self) -> None:
        """
        Clear all event subscribers.

        WARNING: This should only be used during cleanup or testing.
        """
        with self._lock:
            self._subscribers.clear()
            self._wildcard_subscribers.clear()
            self._filtered_subscribers.clear()
            self._filtered_cache.clear()
            logger.warning("All event subscribers cleared")

    @classmethod
    def reset_instance(cls) -> None:
        """
        Reset the singleton instance.

        WARNING: This should only be used during testing.
        Creates a new EventBus instance, discarding the old one.
        """
        with cls._lock_class:
            cls._instance = None
            logger.warning("EventBus instance reset")

    def __repr__(self) -> str:
        """String representation of EventBus."""
        metrics = self.get_metrics()
        return (
            f"EventBus("
            f"subscribers={metrics['subscribers']}, "
            f"events_published={metrics['events_published']}, "
            f"cache_size={metrics['cache_size']}, "
            f"events_handled={metrics['events_handled']}"
            f")"
        )
