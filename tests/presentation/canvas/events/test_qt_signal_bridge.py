"""
Tests for Qt Signal Bridge components.

Note: These tests require Qt event loop to be running.
"""

import pytest
from PySide6.QtCore import QCoreApplication

from casare_rpa.presentation.canvas.events import (
    EventBus,
    Event,
    EventType,
    EventCategory,
)
from casare_rpa.presentation.canvas.events.qt_signal_bridge import (
    QtSignalBridge,
    QtEventEmitter,
    QtEventSubscriber,
)


@pytest.fixture
def qapp() -> None:
    """Provide Qt application instance."""
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    yield app
    # Note: Don't quit app as it may be shared across tests


class TestQtSignalBridge:
    """Test QtSignalBridge class."""

    def setup_method(self):
        """Reset EventBus before each test."""
        EventBus.reset_instance()
        self.bus = EventBus()

    def teardown_method(self):
        """Clean up after each test."""
        EventBus.reset_instance()

    def test_bridge_initialization(self, qapp) -> None:
        """Test that bridge initializes correctly."""
        bridge = QtSignalBridge()
        assert bridge is not None
        bridge.cleanup()

    def test_bridge_emits_generic_signal(self, qapp) -> None:
        """Test that bridge emits generic event signal."""
        bridge = QtSignalBridge()
        received_events = []

        def handler(event: Event) -> None:
            received_events.append(event)

        bridge.event_emitted.connect(handler)

        # Publish event to EventBus
        event = Event(type=EventType.WORKFLOW_NEW, source="Test")
        self.bus.publish(event)

        # Process Qt events
        qapp.processEvents()

        assert len(received_events) == 1
        assert received_events[0] == event

        bridge.cleanup()

    def test_bridge_emits_category_signals(self, qapp) -> None:
        """Test that bridge emits category-specific signals."""
        bridge = QtSignalBridge()
        workflow_events = []
        node_events = []

        def workflow_handler(event: Event) -> None:
            workflow_events.append(event)

        def node_handler(event: Event) -> None:
            node_events.append(event)

        bridge.workflow_event.connect(workflow_handler)
        bridge.node_event.connect(node_handler)

        # Publish workflow event
        self.bus.publish(Event(type=EventType.WORKFLOW_NEW, source="Test"))

        # Publish node event
        self.bus.publish(Event(type=EventType.NODE_ADDED, source="Test"))

        qapp.processEvents()

        assert len(workflow_events) == 1
        assert len(node_events) == 1

        bridge.cleanup()

    def test_bridge_publish(self, qapp) -> None:
        """Test publishing through bridge."""
        bridge = QtSignalBridge()
        received_events = []

        def handler(event: Event) -> None:
            received_events.append(event)

        bridge.event_emitted.connect(handler)

        # Publish through bridge
        event = Event(type=EventType.WORKFLOW_SAVED, source="Test")
        bridge.publish(event)

        qapp.processEvents()

        assert len(received_events) == 1

        bridge.cleanup()


class TestQtEventEmitter:
    """Test QtEventEmitter class."""

    def setup_method(self):
        """Reset EventBus before each test."""
        EventBus.reset_instance()
        self.bus = EventBus()

    def teardown_method(self):
        """Clean up after each test."""
        EventBus.reset_instance()

    def test_emitter_initialization(self, qapp) -> None:
        """Test that emitter initializes correctly."""
        emitter = QtEventEmitter()
        assert emitter is not None

    def test_emitter_emits_qt_signal(self, qapp) -> None:
        """Test that emitter emits Qt signal."""
        emitter = QtEventEmitter()
        received_events = []

        def handler(event: Event) -> None:
            received_events.append(event)

        emitter.event_emitted.connect(handler)

        # Emit event
        event = Event(type=EventType.WORKFLOW_NEW, source="Test")
        emitter.emit(event)

        qapp.processEvents()

        assert len(received_events) == 1
        assert received_events[0] == event

    def test_emitter_publishes_to_event_bus(self, qapp) -> None:
        """Test that emitter publishes to EventBus."""
        emitter = QtEventEmitter()
        received_events = []

        def handler(event: Event) -> None:
            received_events.append(event)

        self.bus.subscribe(EventType.WORKFLOW_NEW, handler)

        # Emit event
        event = Event(type=EventType.WORKFLOW_NEW, source="Test")
        emitter.emit(event)

        assert len(received_events) == 1


class TestQtEventSubscriber:
    """Test QtEventSubscriber class."""

    def setup_method(self):
        """Reset EventBus before each test."""
        EventBus.reset_instance()
        self.bus = EventBus()

    def teardown_method(self):
        """Clean up after each test."""
        EventBus.reset_instance()

    def test_subscriber_initialization(self, qapp) -> None:
        """Test that subscriber initializes correctly."""
        subscriber = QtEventSubscriber()
        assert subscriber is not None
        subscriber.cleanup()

    def test_subscriber_receives_events(self, qapp) -> None:
        """Test that subscriber receives subscribed events."""
        subscriber = QtEventSubscriber()
        received_events = []

        def handler(event: Event) -> None:
            received_events.append(event)

        subscriber.event_received.connect(handler)
        subscriber.subscribe(EventType.WORKFLOW_NEW)

        # Publish event to EventBus
        event = Event(type=EventType.WORKFLOW_NEW, source="Test")
        self.bus.publish(event)

        qapp.processEvents()

        assert len(received_events) == 1
        assert received_events[0] == event

        subscriber.cleanup()

    def test_subscriber_filters_events(self, qapp) -> None:
        """Test that subscriber only receives subscribed events."""
        subscriber = QtEventSubscriber()
        received_events = []

        def handler(event: Event) -> None:
            received_events.append(event)

        subscriber.event_received.connect(handler)
        subscriber.subscribe(EventType.WORKFLOW_NEW)

        # Publish subscribed event
        self.bus.publish(Event(type=EventType.WORKFLOW_NEW, source="Test"))

        # Publish non-subscribed event
        self.bus.publish(Event(type=EventType.NODE_ADDED, source="Test"))

        qapp.processEvents()

        # Should only receive workflow event
        assert len(received_events) == 1
        assert received_events[0].type == EventType.WORKFLOW_NEW

        subscriber.cleanup()

    def test_subscriber_unsubscribe(self, qapp) -> None:
        """Test unsubscribing from events."""
        subscriber = QtEventSubscriber()
        received_events = []

        def handler(event: Event) -> None:
            received_events.append(event)

        subscriber.event_received.connect(handler)
        subscriber.subscribe(EventType.WORKFLOW_NEW)

        # Publish first event
        self.bus.publish(Event(type=EventType.WORKFLOW_NEW, source="Test"))
        qapp.processEvents()
        assert len(received_events) == 1

        # Unsubscribe
        subscriber.unsubscribe(EventType.WORKFLOW_NEW)

        # Publish second event (should not be received)
        self.bus.publish(Event(type=EventType.WORKFLOW_NEW, source="Test"))
        qapp.processEvents()
        assert len(received_events) == 1  # Still 1

        subscriber.cleanup()

    def test_subscriber_cleanup(self, qapp) -> None:
        """Test that cleanup unsubscribes all events."""
        subscriber = QtEventSubscriber()
        received_events = []

        def handler(event: Event) -> None:
            received_events.append(event)

        subscriber.event_received.connect(handler)
        subscriber.subscribe(EventType.WORKFLOW_NEW)
        subscriber.subscribe(EventType.NODE_ADDED)

        # Cleanup
        subscriber.cleanup()

        # Publish events (should not be received)
        self.bus.publish(Event(type=EventType.WORKFLOW_NEW, source="Test"))
        self.bus.publish(Event(type=EventType.NODE_ADDED, source="Test"))

        qapp.processEvents()

        assert len(received_events) == 0
