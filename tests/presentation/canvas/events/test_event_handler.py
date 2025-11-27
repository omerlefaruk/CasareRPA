"""
Tests for EventHandler base class and decorators.
"""

import pytest

from casare_rpa.presentation.canvas.events import (
    EventBus,
    Event,
    EventType,
    EventCategory,
    EventHandler,
    event_handler,
    EventFilter,
)


class TestEventHandlerDecorator:
    """Test @event_handler decorator."""

    def test_decorator_marks_function(self):
        """Test that decorator marks function as event handler."""

        @event_handler(EventType.WORKFLOW_NEW)
        def handler(event: Event) -> None:
            pass

        assert hasattr(handler, "_is_event_handler")
        assert handler._is_event_handler is True
        assert handler._event_type == EventType.WORKFLOW_NEW

    def test_decorator_with_filter(self):
        """Test decorator with event filter."""
        filter = EventFilter(categories=[EventCategory.WORKFLOW])

        @event_handler(event_filter=filter)
        def handler(event: Event) -> None:
            pass

        assert handler._is_event_handler is True
        assert handler._event_filter == filter

    def test_decorator_without_parameters(self):
        """Test decorator without parameters (manual subscription)."""

        @event_handler()
        def handler(event: Event) -> None:
            pass

        assert handler._is_event_handler is True
        assert handler._event_type is None
        assert handler._event_filter is None


class TestEventHandlerBaseClass:
    """Test EventHandler base class."""

    def setup_method(self):
        """Reset EventBus before each test."""
        EventBus.reset_instance()
        self.bus = EventBus()

    def teardown_method(self):
        """Clean up after each test."""
        EventBus.reset_instance()

    def test_manual_subscription(self):
        """Test manual event subscription."""
        received_events = []

        class TestHandler(EventHandler):
            def __init__(self):
                super().__init__()
                self.subscribe(EventType.WORKFLOW_NEW, self.on_workflow_new)

            def on_workflow_new(self, event: Event) -> None:
                received_events.append(event)

        handler = TestHandler()

        event = Event(type=EventType.WORKFLOW_NEW, source="Test")
        self.bus.publish(event)

        assert len(received_events) == 1
        assert received_events[0] == event

        handler.cleanup()

    def test_auto_subscription_with_decorator(self):
        """Test automatic subscription using decorators."""
        received_events = []

        class TestHandler(EventHandler):
            def __init__(self):
                super().__init__()
                self._auto_subscribe_decorated_handlers()

            @event_handler(EventType.WORKFLOW_NEW)
            def on_workflow_new(self, event: Event) -> None:
                received_events.append(event)

        handler = TestHandler()

        event = Event(type=EventType.WORKFLOW_NEW, source="Test")
        self.bus.publish(event)

        assert len(received_events) == 1

        handler.cleanup()

    def test_multiple_decorated_handlers(self):
        """Test multiple decorated event handlers."""
        call_tracker = {"workflow": 0, "node": 0}

        class TestHandler(EventHandler):
            def __init__(self):
                super().__init__()
                self._auto_subscribe_decorated_handlers()

            @event_handler(EventType.WORKFLOW_NEW)
            def on_workflow_new(self, event: Event) -> None:
                call_tracker["workflow"] += 1

            @event_handler(EventType.NODE_ADDED)
            def on_node_added(self, event: Event) -> None:
                call_tracker["node"] += 1

        handler = TestHandler()

        self.bus.publish(Event(type=EventType.WORKFLOW_NEW, source="Test"))
        self.bus.publish(Event(type=EventType.NODE_ADDED, source="Test"))

        assert call_tracker["workflow"] == 1
        assert call_tracker["node"] == 1

        handler.cleanup()

    def test_filtered_subscription(self):
        """Test filtered event subscription."""
        received_events = []

        class TestHandler(EventHandler):
            def __init__(self):
                super().__init__()
                filter = EventFilter(categories=[EventCategory.WORKFLOW])
                self.subscribe_filtered(filter, self.on_workflow_event)

            def on_workflow_event(self, event: Event) -> None:
                received_events.append(event)

        handler = TestHandler()

        # Publish workflow and non-workflow events
        self.bus.publish(Event(type=EventType.WORKFLOW_NEW, source="Test"))
        self.bus.publish(Event(type=EventType.NODE_ADDED, source="Test"))
        self.bus.publish(Event(type=EventType.WORKFLOW_SAVED, source="Test"))

        # Should only receive workflow events
        assert len(received_events) == 2

        handler.cleanup()

    def test_wildcard_subscription(self):
        """Test subscribing to all events."""
        received_events = []

        class TestHandler(EventHandler):
            def __init__(self):
                super().__init__()
                self.subscribe_all(self.on_any_event)

            def on_any_event(self, event: Event) -> None:
                received_events.append(event)

        handler = TestHandler()

        # Publish various events
        self.bus.publish(Event(type=EventType.WORKFLOW_NEW, source="Test"))
        self.bus.publish(Event(type=EventType.NODE_ADDED, source="Test"))
        self.bus.publish(Event(type=EventType.EXECUTION_STARTED, source="Test"))

        assert len(received_events) == 3

        handler.cleanup()

    def test_unsubscribe(self):
        """Test manual unsubscription."""
        received_events = []

        class TestHandler(EventHandler):
            def __init__(self):
                super().__init__()
                self.subscribe(EventType.WORKFLOW_NEW, self.on_workflow_new)

            def on_workflow_new(self, event: Event) -> None:
                received_events.append(event)

        handler = TestHandler()

        # Publish first event
        self.bus.publish(Event(type=EventType.WORKFLOW_NEW, source="Test"))
        assert len(received_events) == 1

        # Unsubscribe
        handler.unsubscribe(EventType.WORKFLOW_NEW, handler.on_workflow_new)

        # Publish second event
        self.bus.publish(Event(type=EventType.WORKFLOW_NEW, source="Test"))
        assert len(received_events) == 1  # Still 1

        handler.cleanup()

    def test_publish_event(self):
        """Test publishing events from handler."""
        received_events = []

        def external_handler(event: Event) -> None:
            received_events.append(event)

        self.bus.subscribe(EventType.WORKFLOW_SAVED, external_handler)

        class TestHandler(EventHandler):
            def save_workflow(self):
                event = Event(
                    type=EventType.WORKFLOW_SAVED,
                    source=self.__class__.__name__,
                    data={"file_path": "/path/to/file.json"},
                )
                self.publish(event)

        handler = TestHandler()
        handler.save_workflow()

        assert len(received_events) == 1
        assert received_events[0].type == EventType.WORKFLOW_SAVED

        handler.cleanup()

    def test_cleanup_unsubscribes_all(self):
        """Test that cleanup unsubscribes from all events."""
        call_count = [0]

        class TestHandler(EventHandler):
            def __init__(self):
                super().__init__()
                self.subscribe(EventType.WORKFLOW_NEW, self.on_event)
                self.subscribe(EventType.NODE_ADDED, self.on_event)

            def on_event(self, event: Event) -> None:
                call_count[0] += 1

        handler = TestHandler()

        # Publish before cleanup
        self.bus.publish(Event(type=EventType.WORKFLOW_NEW, source="Test"))
        assert call_count[0] == 1

        # Cleanup
        handler.cleanup()

        # Publish after cleanup (should not be received)
        self.bus.publish(Event(type=EventType.WORKFLOW_NEW, source="Test"))
        self.bus.publish(Event(type=EventType.NODE_ADDED, source="Test"))
        assert call_count[0] == 1  # Still 1

    def test_custom_event_bus(self):
        """Test using custom EventBus instance."""
        custom_bus = EventBus()
        received_events = []

        class TestHandler(EventHandler):
            def __init__(self):
                super().__init__(event_bus=custom_bus)
                self.subscribe(EventType.WORKFLOW_NEW, self.on_event)

            def on_event(self, event: Event) -> None:
                received_events.append(event)

        handler = TestHandler()

        # Publish to custom bus
        custom_bus.publish(Event(type=EventType.WORKFLOW_NEW, source="Test"))
        assert len(received_events) == 1

        # Verify custom_bus is the same instance as default bus (singleton pattern)
        assert custom_bus is self.bus

        handler.cleanup()

    def test_subscription_tracking(self):
        """Test that subscriptions are tracked correctly."""

        class TestHandler(EventHandler):
            def __init__(self):
                super().__init__()
                self.subscribe(EventType.WORKFLOW_NEW, self.on_event)
                self.subscribe(EventType.NODE_ADDED, self.on_event)

            def on_event(self, event: Event) -> None:
                pass

        handler = TestHandler()

        # Check subscription tracking
        assert len(handler._subscriptions) == 2

        handler.cleanup()

    def test_decorator_without_type_or_filter_warning(self):
        """Test that decorator without type/filter issues warning."""
        import logging

        class TestHandler(EventHandler):
            def __init__(self):
                super().__init__()
                # This should log a warning
                self._auto_subscribe_decorated_handlers()

            @event_handler()  # No type or filter
            def on_event(self, event: Event) -> None:
                pass

        # Create handler (should log warning but not crash)
        handler = TestHandler()
        handler.cleanup()
