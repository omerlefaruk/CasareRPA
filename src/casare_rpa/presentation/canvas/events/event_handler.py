"""
Event handler decorators and base class for Canvas components.

This module provides utilities for creating event-driven components
that subscribe to and handle events from the EventBus.

Features:
    - @event_handler decorator for method-based handlers
    - EventHandler base class for component event handling
    - Automatic subscription/unsubscription management
    - Type-safe event handling patterns

Usage:
    from casare_rpa.presentation.canvas.events import (
        EventHandler, event_handler, EventType, Event
    )

    # Using EventHandler base class
    class MyController(EventHandler):
        def __init__(self):
            super().__init__()

            # Subscribe to events
            self.subscribe(EventType.WORKFLOW_NEW, self.on_workflow_new)

        def on_workflow_new(self, event: Event) -> None:
            print(f"New workflow: {event.data}")

        def cleanup(self):
            # Automatically unsubscribes from all events
            super().cleanup()

    # Using decorator
    class MyComponent:
        def __init__(self):
            self.bus = EventBus()

        @event_handler(EventType.NODE_ADDED)
        def on_node_added(self, event: Event) -> None:
            print(f"Node added: {event.data['node_id']}")
"""

from typing import Callable, Optional
from functools import wraps

from loguru import logger

from casare_rpa.presentation.canvas.events.event import Event, EventFilter
from casare_rpa.presentation.canvas.events.event_types import EventType
from casare_rpa.presentation.canvas.events.event_bus import EventBus


def event_handler(
    event_type: Optional[EventType] = None,
    event_filter: Optional[EventFilter] = None,
) -> Callable:
    """
    Decorator for marking methods as event handlers.

    Can be used with EventType for specific events, EventFilter for
    filtered subscriptions, or no arguments for manual subscription.

    Args:
        event_type: Specific event type to handle (optional)
        event_filter: Custom filter for events (optional)

    Returns:
        Decorated function with event handling metadata

    Examples:
        # Handle specific event type
        @event_handler(EventType.WORKFLOW_SAVED)
        def on_workflow_saved(self, event: Event) -> None:
            print(f"Saved: {event.data['file_path']}")

        # Handle filtered events
        filter = EventFilter(categories=[EventCategory.EXECUTION])
        @event_handler(event_filter=filter)
        def on_execution_event(self, event: Event) -> None:
            print(f"Execution event: {event.type}")

        # Mark handler for manual subscription
        @event_handler()
        def on_custom_event(self, event: Event) -> None:
            print(f"Custom event: {event}")
    """

    def decorator(func: Callable) -> Callable:
        # Store metadata on function
        func._is_event_handler = True
        func._event_type = event_type
        func._event_filter = event_filter

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        # Copy metadata to wrapper
        wrapper._is_event_handler = True
        wrapper._event_type = event_type
        wrapper._event_filter = event_filter

        return wrapper

    return decorator


class EventHandler:
    """
    Base class for components that handle events.

    Provides automatic subscription management and cleanup.
    Subclasses can override event handler methods decorated with
    @event_handler or use the subscribe() method directly.

    Features:
        - Automatic subscription management
        - Cleanup on destruction
        - Type-safe event handling
        - Subscription tracking

    Examples:
        class WorkflowController(EventHandler):
            def __init__(self):
                super().__init__()

                # Manual subscription
                self.subscribe(EventType.WORKFLOW_NEW, self.on_workflow_new)
                self.subscribe(EventType.WORKFLOW_OPENED, self.on_workflow_opened)

            def on_workflow_new(self, event: Event) -> None:
                logger.info(f"New workflow: {event.data}")

            def on_workflow_opened(self, event: Event) -> None:
                logger.info(f"Opened workflow: {event.data['file_path']}")

            def cleanup(self):
                # Automatically unsubscribes from all events
                super().cleanup()

        # Alternative using decorators
        class NodeController(EventHandler):
            def __init__(self):
                super().__init__()
                self._auto_subscribe_decorated_handlers()

            @event_handler(EventType.NODE_ADDED)
            def on_node_added(self, event: Event) -> None:
                logger.info(f"Node added: {event.data['node_id']}")

            @event_handler(EventType.NODE_REMOVED)
            def on_node_removed(self, event: Event) -> None:
                logger.info(f"Node removed: {event.data['node_id']}")
    """

    def __init__(self, event_bus: Optional[EventBus] = None):
        """
        Initialize event handler.

        Args:
            event_bus: EventBus instance to use (defaults to singleton)
        """
        self._event_bus = event_bus or EventBus()
        self._subscriptions: list[tuple[EventType, Callable]] = []
        self._wildcard_subscriptions: list[Callable] = []
        self._filtered_subscriptions: list[tuple[EventFilter, Callable]] = []

    def subscribe(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """
        Subscribe to a specific event type.

        Tracks subscription for automatic cleanup.

        Args:
            event_type: Type of event to subscribe to
            handler: Handler function (can be method)

        Example:
            self.subscribe(EventType.WORKFLOW_SAVED, self.on_workflow_saved)
        """
        self._event_bus.subscribe(event_type, handler)
        self._subscriptions.append((event_type, handler))

        logger.debug(
            f"{self.__class__.__name__} subscribed to {event_type.name}: "
            f"{handler.__name__ if hasattr(handler, '__name__') else handler}"
        )

    def subscribe_all(self, handler: Callable[[Event], None]) -> None:
        """
        Subscribe to all events (wildcard).

        Args:
            handler: Handler function for all events

        Example:
            self.subscribe_all(self.log_all_events)
        """
        self._event_bus.subscribe_all(handler)
        self._wildcard_subscriptions.append(handler)

        logger.debug(
            f"{self.__class__.__name__} subscribed to all events: "
            f"{handler.__name__ if hasattr(handler, '__name__') else handler}"
        )

    def subscribe_filtered(
        self,
        event_filter: EventFilter,
        handler: Callable[[Event], None],
    ) -> None:
        """
        Subscribe to events matching a filter.

        Args:
            event_filter: Filter defining which events to receive
            handler: Handler function for matching events

        Example:
            filter = EventFilter(categories=[EventCategory.WORKFLOW])
            self.subscribe_filtered(filter, self.on_workflow_event)
        """
        self._event_bus.subscribe_filtered(event_filter, handler)
        self._filtered_subscriptions.append((event_filter, handler))

        logger.debug(f"{self.__class__.__name__} subscribed with filter: {event_filter}")

    def unsubscribe(self, event_type: EventType, handler: Callable[[Event], None]) -> bool:
        """
        Unsubscribe from specific event type.

        Args:
            event_type: Event type to unsubscribe from
            handler: Handler function to remove

        Returns:
            bool: True if unsubscribed successfully
        """
        success = self._event_bus.unsubscribe(event_type, handler)

        if success:
            try:
                self._subscriptions.remove((event_type, handler))
            except ValueError:
                pass

            logger.debug(f"{self.__class__.__name__} unsubscribed from {event_type.name}")

        return success

    def unsubscribe_all(self, handler: Callable[[Event], None]) -> bool:
        """
        Unsubscribe from all events (wildcard).

        Args:
            handler: Handler function to remove

        Returns:
            bool: True if unsubscribed successfully
        """
        success = self._event_bus.unsubscribe_all(handler)

        if success:
            try:
                self._wildcard_subscriptions.remove(handler)
            except ValueError:
                pass

            logger.debug(f"{self.__class__.__name__} unsubscribed from all events")

        return success

    def unsubscribe_filtered(
        self,
        event_filter: EventFilter,
        handler: Callable[[Event], None],
    ) -> bool:
        """
        Unsubscribe from filtered events.

        Args:
            event_filter: Filter used for subscription
            handler: Handler function to remove

        Returns:
            bool: True if unsubscribed successfully
        """
        success = self._event_bus.unsubscribe_filtered(event_filter, handler)

        if success:
            try:
                self._filtered_subscriptions.remove((event_filter, handler))
            except ValueError:
                pass

            logger.debug(f"{self.__class__.__name__} unsubscribed from filter")

        return success

    def publish(self, event: Event) -> None:
        """
        Publish an event to the event bus.

        Args:
            event: Event to publish

        Example:
            event = Event(
                type=EventType.WORKFLOW_SAVED,
                source=self.__class__.__name__,
                data={"file_path": str(path)}
            )
            self.publish(event)
        """
        self._event_bus.publish(event)

    def cleanup(self) -> None:
        """
        Cleanup event subscriptions.

        Should be called when component is destroyed.
        Automatically unsubscribes from all events.
        """
        # Unsubscribe from specific events
        for event_type, handler in list(self._subscriptions):
            self._event_bus.unsubscribe(event_type, handler)

        # Unsubscribe from wildcard events
        for handler in list(self._wildcard_subscriptions):
            self._event_bus.unsubscribe_all(handler)

        # Unsubscribe from filtered events
        for event_filter, handler in list(self._filtered_subscriptions):
            self._event_bus.unsubscribe_filtered(event_filter, handler)

        # Clear tracking lists
        self._subscriptions.clear()
        self._wildcard_subscriptions.clear()
        self._filtered_subscriptions.clear()

        logger.debug(f"{self.__class__.__name__} event subscriptions cleaned up")

    def _auto_subscribe_decorated_handlers(self) -> None:
        """
        Automatically subscribe to events based on @event_handler decorators.

        Scans all methods for @event_handler decorator and subscribes them
        to the appropriate events.

        Call this in __init__() to enable automatic subscription:

            def __init__(self):
                super().__init__()
                self._auto_subscribe_decorated_handlers()

        Example:
            class MyController(EventHandler):
                def __init__(self):
                    super().__init__()
                    self._auto_subscribe_decorated_handlers()

                @event_handler(EventType.WORKFLOW_NEW)
                def on_workflow_new(self, event: Event) -> None:
                    print("New workflow!")
        """
        # Scan all methods
        for attr_name in dir(self):
            # Skip private/magic methods
            if attr_name.startswith("_"):
                continue

            attr = getattr(self, attr_name)

            # Check if it's a decorated event handler
            if not callable(attr):
                continue

            if not hasattr(attr, "_is_event_handler"):
                continue

            if not attr._is_event_handler:
                continue

            # Subscribe based on decorator parameters
            if attr._event_type is not None:
                # Type-specific subscription
                self.subscribe(attr._event_type, attr)

            elif attr._event_filter is not None:
                # Filtered subscription
                self.subscribe_filtered(attr._event_filter, attr)

            else:
                # Decorator without parameters - skip auto-subscription
                logger.warning(
                    f"Event handler {attr_name} has @event_handler decorator "
                    "but no event_type or filter - skipping auto-subscription"
                )

        logger.debug(f"{self.__class__.__name__} auto-subscribed decorated handlers")

    def __del__(self):
        """Cleanup on destruction."""
        try:
            self.cleanup()
        except Exception:
            # Ignore cleanup errors during destruction
            pass
