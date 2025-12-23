"""
Qt Signal Bridge for EventBus integration.

This module provides a bridge between the EventBus and Qt's signal/slot system,
allowing Qt widgets to emit and receive events through Qt signals while the
underlying system uses the EventBus.

This enables:
    - Gradual migration from Qt signals to EventBus
    - Compatibility with existing Qt-based code
    - Cross-thread event handling via Qt's event loop

Usage:
    from casare_rpa.presentation.canvas.events import QtSignalBridge, EventType, Event

    # Create bridge
    bridge = QtSignalBridge()

    # Connect Qt slots to events
    bridge.workflow_event.connect(on_workflow_event)
    bridge.node_event.connect(on_node_event)
    bridge.execution_event.connect(on_execution_event)

    # Publish event (automatically emits Qt signal)
    event = Event(
        type=EventType.WORKFLOW_SAVED,
        source="WorkflowController",
        data={"file_path": "/path/to/workflow.json"}
    )
    bridge.publish(event)  # Emits workflow_event signal
"""

from typing import Optional
from collections.abc import Callable

from loguru import logger
from PySide6.QtCore import QObject, Signal

from casare_rpa.presentation.canvas.events.event import Event
from casare_rpa.presentation.canvas.events.event_bus import EventBus
from casare_rpa.presentation.canvas.events.event_types import EventCategory, EventType


class QtSignalBridge(QObject):
    """
    Bridge between EventBus and Qt signals.

    This class subscribes to all EventBus events and re-emits them as
    Qt signals, allowing Qt widgets to use signal/slot connections
    while maintaining EventBus architecture.

    Signals:
        event_emitted: Generic signal for all events
        workflow_event: Signal for workflow-related events
        node_event: Signal for node-related events
        connection_event: Signal for connection-related events
        execution_event: Signal for execution-related events
        ui_event: Signal for UI-related events
        system_event: Signal for system-related events
        project_event: Signal for project-related events
        variable_event: Signal for variable-related events
        debug_event: Signal for debug-related events
        trigger_event: Signal for trigger-related events

    Example:
        # In a Qt widget
        class MyWidget(QWidget):
            def __init__(self):
                super().__init__()
                self.bridge = QtSignalBridge()

                # Connect to specific category signals
                self.bridge.workflow_event.connect(self.on_workflow_event)
                self.bridge.execution_event.connect(self.on_execution_event)

            def on_workflow_event(self, event: Event) -> None:
                if event.type == EventType.WORKFLOW_SAVED:
                    self.update_title(event.data['file_path'])

            def on_execution_event(self, event: Event) -> None:
                if event.type == EventType.EXECUTION_STARTED:
                    self.show_progress_bar()
    """

    # Generic signal for all events
    event_emitted = Signal(Event)

    # Category-specific signals
    workflow_event = Signal(Event)
    node_event = Signal(Event)
    connection_event = Signal(Event)
    execution_event = Signal(Event)
    ui_event = Signal(Event)
    system_event = Signal(Event)
    project_event = Signal(Event)
    variable_event = Signal(Event)
    debug_event = Signal(Event)
    trigger_event = Signal(Event)

    def __init__(self, event_bus: EventBus | None = None, parent: QObject | None = None):
        """
        Initialize Qt signal bridge.

        Args:
            event_bus: EventBus instance to bridge (defaults to singleton)
            parent: Parent QObject (for Qt ownership)
        """
        super().__init__(parent)

        self._event_bus = event_bus or EventBus()

        # Subscribe to all events from EventBus
        self._event_bus.subscribe_all(self._on_event_bus_event)

        logger.debug("QtSignalBridge initialized")

    def _on_event_bus_event(self, event: Event) -> None:
        """
        Handle event from EventBus and emit appropriate Qt signals.

        Args:
            event: Event from EventBus
        """
        # Emit generic signal
        self.event_emitted.emit(event)

        # Emit category-specific signal
        category = event.category

        if category == EventCategory.WORKFLOW:
            self.workflow_event.emit(event)

        elif category == EventCategory.NODE:
            self.node_event.emit(event)

        elif category == EventCategory.CONNECTION:
            self.connection_event.emit(event)

        elif category == EventCategory.EXECUTION:
            self.execution_event.emit(event)

        elif category == EventCategory.UI:
            self.ui_event.emit(event)

        elif category == EventCategory.SYSTEM:
            self.system_event.emit(event)

        elif category == EventCategory.PROJECT:
            self.project_event.emit(event)

        elif category == EventCategory.VARIABLE:
            self.variable_event.emit(event)

        elif category == EventCategory.DEBUG:
            self.debug_event.emit(event)

        elif category == EventCategory.TRIGGER:
            self.trigger_event.emit(event)

    def publish(self, event: Event) -> None:
        """
        Publish event to EventBus (which will trigger Qt signals).

        This is a convenience method for publishing events that will
        be emitted as Qt signals.

        Args:
            event: Event to publish

        Example:
            event = Event(
                type=EventType.NODE_ADDED,
                source="NodeController",
                data={"node_id": "123"}
            )
            bridge.publish(event)
        """
        self._event_bus.publish(event)

    def cleanup(self) -> None:
        """
        Cleanup signal bridge.

        Unsubscribes from EventBus to prevent memory leaks.
        """
        self._event_bus.unsubscribe_all(self._on_event_bus_event)
        logger.debug("QtSignalBridge cleaned up")

    def __del__(self):
        """Cleanup on destruction."""
        try:
            self.cleanup()
        except Exception:
            # Ignore cleanup errors during destruction
            pass


class QtEventEmitter(QObject):
    """
    Qt-friendly event emitter for controllers and components.

    This class wraps EventBus publishing with Qt signal emission,
    allowing controllers to emit events that work with both EventBus
    subscribers and Qt signal/slot connections.

    Useful for controllers that need to support both EventBus and
    legacy Qt signal code during migration.

    Example:
        class WorkflowController(QObject):
            def __init__(self):
                super().__init__()
                self.emitter = QtEventEmitter(self)

                # Connect to Qt signals if needed
                self.emitter.event_emitted.connect(self.on_event)

            async def save_workflow(self, path: Path) -> None:
                # ... save logic ...

                # Emit event (goes to both EventBus and Qt signals)
                event = Event(
                    type=EventType.WORKFLOW_SAVED,
                    source="WorkflowController",
                    data={"file_path": str(path)}
                )
                self.emitter.emit(event)

            def on_event(self, event: Event) -> None:
                print(f"Event: {event}")
    """

    # Signal emitted for all events
    event_emitted = Signal(Event)

    def __init__(
        self,
        parent: QObject | None = None,
        event_bus: EventBus | None = None,
    ):
        """
        Initialize Qt event emitter.

        Args:
            parent: Parent QObject
            event_bus: EventBus instance (defaults to singleton)
        """
        super().__init__(parent)
        self._event_bus = event_bus or EventBus()

    def emit(self, event: Event) -> None:
        """
        Emit event to both EventBus and Qt signals.

        Args:
            event: Event to emit

        Example:
            event = Event(
                type=EventType.NODE_SELECTED,
                source="NodeController",
                data={"node_id": "123"}
            )
            self.emitter.emit(event)
        """
        # Publish to EventBus
        self._event_bus.publish(event)

        # Emit Qt signal
        self.event_emitted.emit(event)


class QtEventSubscriber(QObject):
    """
    Qt-friendly event subscriber for widgets.

    This class provides Qt signal-based subscription to EventBus events,
    allowing Qt widgets to receive events through signal/slot connections
    instead of callback functions.

    Example:
        class WorkflowPanel(QWidget):
            def __init__(self):
                super().__init__()
                self.subscriber = QtEventSubscriber(self)

                # Subscribe to specific event types
                self.subscriber.subscribe(EventType.WORKFLOW_SAVED)
                self.subscriber.subscribe(EventType.WORKFLOW_OPENED)

                # Connect to signal
                self.subscriber.event_received.connect(self.on_event)

            def on_event(self, event: Event) -> None:
                if event.type == EventType.WORKFLOW_SAVED:
                    self.update_status(f"Saved: {event.data['file_path']}")
                elif event.type == EventType.WORKFLOW_OPENED:
                    self.update_status(f"Opened: {event.data['file_path']}")
    """

    # Signal emitted when subscribed event occurs
    event_received = Signal(Event)

    def __init__(
        self,
        parent: QObject | None = None,
        event_bus: EventBus | None = None,
    ):
        """
        Initialize Qt event subscriber.

        Args:
            parent: Parent QObject
            event_bus: EventBus instance (defaults to singleton)
        """
        super().__init__(parent)
        self._event_bus = event_bus or EventBus()
        self._subscriptions: list[tuple[EventType, Callable]] = []

    def subscribe(self, event_type: EventType) -> None:
        """
        Subscribe to specific event type.

        Events will be emitted via the event_received signal.

        Args:
            event_type: Type of event to subscribe to

        Example:
            subscriber.subscribe(EventType.WORKFLOW_SAVED)
            subscriber.event_received.connect(on_event)
        """

        # Create handler that emits Qt signal
        def handler(event: Event) -> None:
            self.event_received.emit(event)

        self._event_bus.subscribe(event_type, handler)
        self._subscriptions.append((event_type, handler))

        logger.debug(f"QtEventSubscriber subscribed to {event_type.name}")

    def unsubscribe(self, event_type: EventType) -> None:
        """
        Unsubscribe from specific event type.

        Args:
            event_type: Type of event to unsubscribe from
        """
        # Find and remove subscription
        for sub_type, handler in list(self._subscriptions):
            if sub_type == event_type:
                self._event_bus.unsubscribe(event_type, handler)
                self._subscriptions.remove((sub_type, handler))
                logger.debug(f"QtEventSubscriber unsubscribed from {event_type.name}")
                break

    def cleanup(self) -> None:
        """
        Cleanup all subscriptions.

        Should be called when widget is destroyed.
        """
        for event_type, handler in list(self._subscriptions):
            self._event_bus.unsubscribe(event_type, handler)

        self._subscriptions.clear()
        logger.debug("QtEventSubscriber cleaned up")

    def __del__(self):
        """Cleanup on destruction."""
        try:
            self.cleanup()
        except Exception:
            # Ignore cleanup errors during destruction
            pass
