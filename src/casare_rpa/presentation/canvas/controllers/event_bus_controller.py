"""
Event bus controller for centralized event routing.

Handles event coordination between controllers:
- Cross-controller communication
- Event filtering and logging
- Event history tracking
- Debugging support
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from PySide6.QtCore import Signal, QObject
from loguru import logger

from .base_controller import BaseController


@dataclass
class Event:
    """Represents an event in the system."""

    type: str
    source: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class EventBusController(BaseController):
    """
    Centralized event bus for controller communication.

    Single Responsibility: Event routing and coordination.

    This controller acts as a mediator between other controllers,
    enabling loose coupling and centralized event logging.

    Signals:
        event_dispatched: Emitted when any event is dispatched (Event)
    """

    # Signals
    event_dispatched = Signal(object)  # Event

    def __init__(self, main_window):
        """Initialize event bus controller."""
        super().__init__(main_window)
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_history: List[Event] = []
        self._max_history_size = 1000
        self._event_filtering_enabled = False
        self._filtered_event_types: set = set()

    def initialize(self) -> None:
        """Initialize controller."""
        super().initialize()
        logger.info("EventBusController initialized")

    def cleanup(self) -> None:
        """Clean up resources."""
        super().cleanup()
        logger.info("EventBusController cleanup")
        self._subscribers.clear()
        self._event_history.clear()

    def subscribe(self, event_type: str, callback: Callable[[Event], None]) -> None:
        """
        Subscribe to an event type.

        Args:
            event_type: Type of event to subscribe to
            callback: Function to call when event occurs
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)
            logger.debug(f"Subscribed to event: {event_type}")

    def unsubscribe(self, event_type: str, callback: Callable[[Event], None]) -> None:
        """
        Unsubscribe from an event type.

        Args:
            event_type: Type of event to unsubscribe from
            callback: Callback function to remove
        """
        if event_type in self._subscribers:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)
                logger.debug(f"Unsubscribed from event: {event_type}")

    def dispatch(self, event_type: str, source: str, data: Optional[Dict[str, Any]] = None) -> None:
        """
        Dispatch an event to all subscribers.

        Args:
            event_type: Type of event to dispatch
            source: Source controller/component name
            data: Optional event data
        """
        # Check if event type is filtered
        if self._event_filtering_enabled and event_type in self._filtered_event_types:
            return

        # Create event object
        event = Event(
            type=event_type,
            source=source,
            data=data or {},
        )

        # Add to history
        self._add_to_history(event)

        # Log event
        logger.debug(f"Event dispatched: {event_type} from {source}")

        # Emit signal
        self.event_dispatched.emit(event)

        # Notify subscribers
        subscribers = self._subscribers.get(event_type, [])
        for callback in subscribers:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in event callback for {event_type}: {e}")

    def enable_event_filtering(self, event_types: List[str]) -> None:
        """
        Enable filtering to block specific event types.

        Args:
            event_types: List of event types to filter out
        """
        self._event_filtering_enabled = True
        self._filtered_event_types = set(event_types)
        logger.info(f"Event filtering enabled: {len(event_types)} types filtered")

    def disable_event_filtering(self) -> None:
        """Disable event filtering."""
        self._event_filtering_enabled = False
        self._filtered_event_types.clear()
        logger.info("Event filtering disabled")

    def get_event_history(self, count: Optional[int] = None) -> List[Event]:
        """
        Get recent event history.

        Args:
            count: Number of recent events to return (None for all)

        Returns:
            List of recent events
        """
        if count is None:
            return self._event_history.copy()
        return self._event_history[-count:]

    def clear_event_history(self) -> None:
        """Clear event history."""
        self._event_history.clear()
        logger.info("Event history cleared")

    def get_subscriber_count(self, event_type: Optional[str] = None) -> int:
        """
        Get number of subscribers.

        Args:
            event_type: Specific event type, or None for total count

        Returns:
            Number of subscribers
        """
        if event_type:
            return len(self._subscribers.get(event_type, []))
        return sum(len(subs) for subs in self._subscribers.values())

    def get_event_types(self) -> List[str]:
        """
        Get list of all subscribed event types.

        Returns:
            List of event type names
        """
        return list(self._subscribers.keys())

    def _add_to_history(self, event: Event) -> None:
        """
        Add event to history with size limit.

        Args:
            event: Event to add
        """
        self._event_history.append(event)

        # Trim history if too large
        if len(self._event_history) > self._max_history_size:
            # Remove oldest 20% of events
            remove_count = self._max_history_size // 5
            self._event_history = self._event_history[remove_count:]


# Predefined event types for type safety
class EventTypes:
    """Standard event types used across controllers."""

    # Workflow events
    WORKFLOW_CREATED = "workflow.created"
    WORKFLOW_LOADED = "workflow.loaded"
    WORKFLOW_SAVED = "workflow.saved"
    WORKFLOW_CLOSED = "workflow.closed"
    WORKFLOW_MODIFIED = "workflow.modified"

    # Execution events
    EXECUTION_STARTED = "execution.started"
    EXECUTION_PAUSED = "execution.paused"
    EXECUTION_RESUMED = "execution.resumed"
    EXECUTION_STOPPED = "execution.stopped"
    EXECUTION_COMPLETED = "execution.completed"
    EXECUTION_ERROR = "execution.error"

    # Node events
    NODE_SELECTED = "node.selected"
    NODE_DESELECTED = "node.deselected"
    NODE_DISABLED = "node.disabled"
    NODE_ENABLED = "node.enabled"
    NODE_PROPERTY_CHANGED = "node.property_changed"

    # Connection events
    CONNECTION_CREATED = "connection.created"
    CONNECTION_DELETED = "connection.deleted"

    # Panel events
    PANEL_TOGGLED = "panel.toggled"
    PANEL_TAB_CHANGED = "panel.tab_changed"

    # Validation events
    VALIDATION_STARTED = "validation.started"
    VALIDATION_COMPLETED = "validation.completed"
    VALIDATION_ERROR = "validation.error"
