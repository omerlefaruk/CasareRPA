"""
Lazy event subscription for EventBus optimization.

Provides visibility-based subscription that activates when component becomes
visible and deactivates when hidden, reducing EventBus overhead for panels
that are not currently in view.

Uses Qt event filters for cleaner interception without handler mutation.

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

from typing import Callable, List

from PySide6.QtCore import QEvent, QObject
from PySide6.QtWidgets import QWidget

from loguru import logger

from .event_bus import EventBus
from .event_types import EventType


class LazySubscription(QObject):
    """
    Subscription that activates when component becomes visible.

    Uses Qt event filter to intercept show/hide events and automatically
    subscribe/unsubscribe from EventBus, reducing subscription overhead
    when panels are hidden.

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
        component: "QWidget",
    ) -> None:
        """
        Initialize lazy subscription.

        Args:
            event_type: EventType to subscribe to
            handler: Callback function to invoke on event
            component: QWidget whose visibility controls subscription
        """
        super().__init__()
        self.event_type = event_type
        self.handler = handler
        self.component = component
        self.active = False

        # Install event filter for clean interception
        component.installEventFilter(self)

        logger.debug(
            f"LazySubscription created for {event_type.name} on "
            f"{component.__class__.__name__}"
        )

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """
        Qt event filter to intercept show/hide events.

        Args:
            watched: Object being watched
            event: Event to filter

        Returns:
            False to allow event propagation
        """
        try:
            if watched == self.component:
                if event.type() == QEvent.Type.Show:
                    self.activate()
                elif event.type() == QEvent.Type.Hide:
                    self.deactivate()
        except RuntimeError:
            # Object deleted during event processing
            pass

        # Always allow event to propagate
        return False

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

    def cleanup(self) -> None:
        """
        Remove event filter and deactivate subscription.

        Should be called when LazySubscription is no longer needed.
        """
        self.deactivate()
        self.component.removeEventFilter(self)
        logger.debug(
            f"LazySubscription cleaned up for {self.component.__class__.__name__}"
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
        """Cleanup all subscriptions."""
        for sub in self._subscriptions:
            if isinstance(sub, LazySubscription):
                sub.cleanup()
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
