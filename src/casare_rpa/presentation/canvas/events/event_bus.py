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

from typing import Callable, Dict, List, Optional, Tuple, Any, Set
from collections import defaultdict, deque
from threading import RLock
import time

from loguru import logger

# PERFORMANCE: Event batching for rapid events
# Reduces UI thrashing during fast workflow execution
BATCH_INTERVAL_MS = 16  # ~60fps, batches events within this window

from casare_rpa.presentation.canvas.events.event import Event, EventFilter
from casare_rpa.presentation.canvas.events.event_types import EventType, EventCategory

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

        # PERFORMANCE: Event batching for rapid events
        # Reduces UI updates during fast workflow execution
        self._batched_events: Dict[EventType, Event] = {}
        self._batch_timer: Any = None  # QTimer for deferred flush
        self._last_batch_flush = time.perf_counter()
        self._batchable_types: Set[EventType] = {
            EventType.NODE_EXECUTION_COMPLETED,
            EventType.NODE_EXECUTION_STARTED,
            EventType.VARIABLE_SET,
        }

        # Initialization complete
        self._initialized = True

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
                return True
            except ValueError:
                return False

    def publish_batched(self, event: Event) -> None:
        """
        Publish an event with batching for rapid events.

        PERFORMANCE: Batches rapid events of the same type within 16ms window.
        This reduces UI thrashing during fast workflow execution where
        NODE_COMPLETED events fire in quick succession.

        Args:
            event: Event to publish
        """
        event_type = getattr(event, "type", None) or getattr(event, "event_type", None)

        # Only batch specific event types
        if event_type not in self._batchable_types:
            self.publish(event)
            return

        with self._lock:
            current_time = time.perf_counter()
            elapsed_ms = (current_time - self._last_batch_flush) * 1000

            # If batch window expired, flush and publish immediately
            if elapsed_ms >= BATCH_INTERVAL_MS:
                self._flush_batched_events()
                self.publish(event)
                self._last_batch_flush = current_time
            else:
                # Add to batch (overwrites previous event of same type)
                self._batched_events[event_type] = event
                # Schedule deferred flush if not already scheduled
                self._schedule_batch_flush()

    def _schedule_batch_flush(self) -> None:
        """Schedule a deferred flush of batched events using QTimer."""
        if self._batch_timer is not None:
            return  # Already scheduled

        try:
            from PySide6.QtCore import QTimer

            self._batch_timer = QTimer()
            self._batch_timer.setSingleShot(True)
            self._batch_timer.timeout.connect(self._on_batch_timer_timeout)
            self._batch_timer.start(BATCH_INTERVAL_MS)
        except ImportError:
            # Not in Qt context - flush immediately
            self._flush_batched_events()

    def _on_batch_timer_timeout(self) -> None:
        """Handle batch timer timeout - flush pending events."""
        with self._lock:
            self._batch_timer = None
            self._flush_batched_events()
            self._last_batch_flush = time.perf_counter()

    def _flush_batched_events(self) -> None:
        """Flush all batched events."""
        if not self._batched_events:
            return

        # Publish all batched events
        for event in self._batched_events.values():
            self._publish_internal(event)

        self._batched_events.clear()

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
        self._publish_internal(event)

    def _publish_internal(self, event: Event) -> None:
        """Internal publish implementation."""
        with self._lock:
            # Update metrics
            self._metrics["events_published"] += 1

            # Add to history
            if self._history_enabled:
                self._history.append(event)

            # Build cache key: (event_type, source)
            # Support both "type" (presentation Event) and "event_type" (domain Event)
            source = event.source if hasattr(event, "source") and event.source else ""
            event_type = getattr(event, "type", None) or getattr(event, "event_type", None)
            cache_key = (event_type, source)

            # Check cache for handlers
            if cache_key in self._filtered_cache:
                handlers = self._filtered_cache[cache_key]
                self._metrics["cache_hits"] += 1
            else:
                # Build and cache handler list
                handlers: List[EventHandler] = []

                # 1. Type-specific subscribers
                if event_type in self._subscribers:
                    handlers.extend(self._subscribers[event_type])

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
                handler_name = handler.__name__ if hasattr(handler, "__name__") else str(handler)
                logger.warning(
                    f"Slow event handler: {handler_name} took {elapsed * 1000:.2f}ms "
                    f"for {event.type.name}"
                )

        except Exception as e:
            self._metrics["errors"] += 1
            handler_name = handler.__name__ if hasattr(handler, "__name__") else str(handler)
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

            total_cache_accesses = self._metrics["cache_hits"] + self._metrics["cache_misses"]
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
                "subscribers": sum(len(handlers) for handlers in self._subscribers.values()),
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
