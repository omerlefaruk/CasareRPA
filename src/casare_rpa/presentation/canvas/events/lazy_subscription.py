"""
Lazy event subscription for EventBus optimization.

Provides visibility-based subscription that activates when component becomes
visible and deactivates when hidden, reducing EventBus overhead for panels
that are not currently in view.

Usage:
    from casare_rpa.presentation.canvas.events import LazySubscription, EventType

    class DebugPanel(QDockWidget):
        def __init__(self, parent):
            super().__init__(parent)
            self._lazy_subs = [
                LazySubscription(EventType.NODE_EXECUTION_STARTED, self.on_exec_started, self),
                LazySubscription(EventType.NODE_EXECUTION_COMPLETED, self.on_exec_completed, self),
            ]
"""

from typing import Callable, List, Optional
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QEvent

from loguru import logger

from .event_bus import EventBus
from .event_types import EventType


class LazySubscription:
    """
    Subscription that activates when component becomes visible.

    Wraps QWidget showEvent/hideEvent to automatically subscribe/unsubscribe
    from EventBus, reducing subscription overhead when panels are hidden.

    Attributes:
        event_type: EventType to subscribe to
        handler: Callback function for events
        component: QWidget whose visibility controls subscription
        active: Whether subscription is currently active
    """

    def __init__(
        self,
        event_type: EventType,
        handler: Callable,
        component: QWidget,
    ) -> None:
        """
        Initialize lazy subscription.

        Args:
            event_type: EventType to subscribe to
            handler: Callback function to invoke on event
            component: QWidget whose visibility controls subscription
        """
        self.event_type = event_type
        self.handler = handler
        self.component = component
        self.active = False

        # Store original event handlers
        self._original_show_event = component.showEvent
        self._original_hide_event = component.hideEvent

        # Wrap component's showEvent/hideEvent
        component.showEvent = self._on_show_wrapper(component.showEvent)
        component.hideEvent = self._on_hide_wrapper(component.hideEvent)

        logger.debug(
            f"LazySubscription created for {event_type.name} on "
            f"{component.__class__.__name__}"
        )

    def _on_show_wrapper(self, original_show: Callable) -> Callable:
        """
        Create wrapper for showEvent that activates subscription.

        Args:
            original_show: Original showEvent method

        Returns:
            Wrapped showEvent function
        """

        def wrapper(event: QEvent) -> None:
            self.activate()
            return original_show(event)

        return wrapper

    def _on_hide_wrapper(self, original_hide: Callable) -> Callable:
        """
        Create wrapper for hideEvent that deactivates subscription.

        Args:
            original_hide: Original hideEvent method

        Returns:
            Wrapped hideEvent function
        """

        def wrapper(event: QEvent) -> None:
            self.deactivate()
            return original_hide(event)

        return wrapper

    def activate(self) -> None:
        """Activate subscription (subscribe to EventBus)."""
        if not self.active:
            EventBus().subscribe(self.event_type, self.handler)
            self.active = True
            logger.debug(
                f"LazySubscription activated: {self.event_type.name} on "
                f"{self.component.__class__.__name__}"
            )

    def deactivate(self) -> None:
        """Deactivate subscription (unsubscribe from EventBus)."""
        if self.active:
            EventBus().unsubscribe(self.event_type, self.handler)
            self.active = False
            logger.debug(
                f"LazySubscription deactivated: {self.event_type.name} on "
                f"{self.component.__class__.__name__}"
            )

    def restore_original_handlers(self) -> None:
        """
        Restore original showEvent/hideEvent handlers.

        Should be called when LazySubscription is no longer needed.
        """
        self.deactivate()
        self.component.showEvent = self._original_show_event
        self.component.hideEvent = self._original_hide_event
        logger.debug(
            f"LazySubscription handlers restored for {self.component.__class__.__name__}"
        )


class LazySubscriptionGroup:
    """
    Manages multiple LazySubscriptions for a single component.

    Convenience class to handle multiple event subscriptions that should
    all activate/deactivate together based on component visibility.

    Usage:
        self._lazy_group = LazySubscriptionGroup(self, [
            (EventType.NODE_EXECUTION_STARTED, self.on_exec_started),
            (EventType.NODE_EXECUTION_COMPLETED, self.on_exec_completed),
        ])
    """

    def __init__(
        self,
        component: QWidget,
        subscriptions: List[tuple[EventType, Callable]],
    ) -> None:
        """
        Initialize lazy subscription group.

        Args:
            component: QWidget whose visibility controls subscriptions
            subscriptions: List of (EventType, handler) tuples
        """
        self.component = component
        self._subscriptions: List[LazySubscription] = []

        # Only wrap events once - first subscription handles the wrapping
        if subscriptions:
            first_event_type, first_handler = subscriptions[0]
            first_sub = LazySubscription(first_event_type, first_handler, component)
            self._subscriptions.append(first_sub)

            # Additional subscriptions share the same visibility logic
            for event_type, handler in subscriptions[1:]:
                sub = _SharedVisibilitySubscription(event_type, handler, first_sub)
                self._subscriptions.append(sub)

        logger.debug(
            f"LazySubscriptionGroup created with {len(subscriptions)} subscriptions "
            f"for {component.__class__.__name__}"
        )

    @property
    def active(self) -> bool:
        """Check if subscriptions are active."""
        return bool(self._subscriptions) and self._subscriptions[0].active

    def activate_all(self) -> None:
        """Force activate all subscriptions."""
        for sub in self._subscriptions:
            sub.activate()

    def deactivate_all(self) -> None:
        """Force deactivate all subscriptions."""
        for sub in self._subscriptions:
            sub.deactivate()

    def cleanup(self) -> None:
        """Cleanup and restore original handlers."""
        for sub in self._subscriptions:
            if isinstance(sub, LazySubscription):
                sub.restore_original_handlers()
            else:
                sub.deactivate()
        self._subscriptions.clear()


class _SharedVisibilitySubscription:
    """
    Internal subscription that shares visibility state with primary LazySubscription.

    Used by LazySubscriptionGroup to avoid wrapping showEvent/hideEvent multiple times.
    """

    def __init__(
        self,
        event_type: EventType,
        handler: Callable,
        primary: LazySubscription,
    ) -> None:
        """
        Initialize shared visibility subscription.

        Args:
            event_type: EventType to subscribe to
            handler: Callback function for events
            primary: Primary LazySubscription to mirror state from
        """
        self.event_type = event_type
        self.handler = handler
        self._primary = primary
        self.active = False

        # Hook into primary's activate/deactivate
        original_activate = primary.activate
        original_deactivate = primary.deactivate

        def wrapped_activate() -> None:
            original_activate()
            self.activate()

        def wrapped_deactivate() -> None:
            original_deactivate()
            self.deactivate()

        primary.activate = wrapped_activate
        primary.deactivate = wrapped_deactivate

    def activate(self) -> None:
        """Activate subscription."""
        if not self.active:
            EventBus().subscribe(self.event_type, self.handler)
            self.active = True

    def deactivate(self) -> None:
        """Deactivate subscription."""
        if self.active:
            EventBus().unsubscribe(self.event_type, self.handler)
            self.active = False
