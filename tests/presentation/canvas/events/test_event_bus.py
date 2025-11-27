"""
Tests for EventBus class.
"""

import pytest
import time

from casare_rpa.presentation.canvas.events import (
    EventBus,
    Event,
    EventType,
    EventCategory,
    EventPriority,
    EventFilter,
)


class TestEventBus:
    """Test EventBus class."""

    def setup_method(self):
        """Reset EventBus instance before each test."""
        EventBus.reset_instance()
        self.bus = EventBus()

    def teardown_method(self):
        """Clean up after each test."""
        self.bus.clear_all_subscribers()
        EventBus.reset_instance()

    def test_singleton_pattern(self) -> None:
        """Test that EventBus is a singleton."""
        bus1 = EventBus()
        bus2 = EventBus()

        assert bus1 is bus2

    def test_subscribe_and_publish(self) -> None:
        """Test basic subscribe and publish."""
        received_events = []

        def handler(event: Event) -> None:
            received_events.append(event)

        self.bus.subscribe(EventType.WORKFLOW_NEW, handler)

        event = Event(type=EventType.WORKFLOW_NEW, source="Test")
        self.bus.publish(event)

        assert len(received_events) == 1
        assert received_events[0] == event

    def test_multiple_subscribers(self) -> None:
        """Test multiple subscribers to same event."""
        call_count = [0]

        def handler1(event: Event) -> None:
            call_count[0] += 1

        def handler2(event: Event) -> None:
            call_count[0] += 10

        self.bus.subscribe(EventType.WORKFLOW_NEW, handler1)
        self.bus.subscribe(EventType.WORKFLOW_NEW, handler2)

        event = Event(type=EventType.WORKFLOW_NEW, source="Test")
        self.bus.publish(event)

        assert call_count[0] == 11  # 1 + 10

    def test_unsubscribe(self) -> None:
        """Test unsubscribing from events."""
        received_events = []

        def handler(event: Event) -> None:
            received_events.append(event)

        self.bus.subscribe(EventType.WORKFLOW_NEW, handler)

        # Publish first event
        event1 = Event(type=EventType.WORKFLOW_NEW, source="Test")
        self.bus.publish(event1)

        assert len(received_events) == 1

        # Unsubscribe
        success = self.bus.unsubscribe(EventType.WORKFLOW_NEW, handler)
        assert success

        # Publish second event (should not be received)
        event2 = Event(type=EventType.WORKFLOW_NEW, source="Test")
        self.bus.publish(event2)

        assert len(received_events) == 1  # Still only 1

    def test_subscribe_all(self) -> None:
        """Test wildcard subscription (all events)."""
        received_events = []

        def handler(event: Event) -> None:
            received_events.append(event)

        self.bus.subscribe_all(handler)

        # Publish different event types
        self.bus.publish(Event(type=EventType.WORKFLOW_NEW, source="Test"))
        self.bus.publish(Event(type=EventType.NODE_ADDED, source="Test"))
        self.bus.publish(Event(type=EventType.EXECUTION_STARTED, source="Test"))

        assert len(received_events) == 3

    def test_subscribe_filtered(self) -> None:
        """Test filtered subscription."""
        received_events = []

        def handler(event: Event) -> None:
            received_events.append(event)

        # Subscribe to all workflow events
        filter = EventFilter(categories=[EventCategory.WORKFLOW])
        self.bus.subscribe_filtered(filter, handler)

        # Publish workflow events
        self.bus.publish(Event(type=EventType.WORKFLOW_NEW, source="Test"))
        self.bus.publish(Event(type=EventType.WORKFLOW_SAVED, source="Test"))

        # Publish non-workflow event
        self.bus.publish(Event(type=EventType.NODE_ADDED, source="Test"))

        assert len(received_events) == 2  # Only workflow events

    def test_event_history(self) -> None:
        """Test event history tracking."""
        # Publish some events
        event1 = Event(type=EventType.WORKFLOW_NEW, source="Test")
        event2 = Event(type=EventType.NODE_ADDED, source="Test")
        event3 = Event(type=EventType.EXECUTION_STARTED, source="Test")

        self.bus.publish(event1)
        self.bus.publish(event2)
        self.bus.publish(event3)

        # Get history
        history = self.bus.get_history()

        assert len(history) == 3
        assert history[0] == event3  # Most recent first
        assert history[1] == event2
        assert history[2] == event1

    def test_event_history_filtering(self) -> None:
        """Test filtered event history."""
        # Publish events
        self.bus.publish(Event(type=EventType.WORKFLOW_NEW, source="Controller1"))
        self.bus.publish(Event(type=EventType.NODE_ADDED, source="Controller2"))
        self.bus.publish(Event(type=EventType.WORKFLOW_SAVED, source="Controller1"))

        # Filter by category
        workflow_history = self.bus.get_history(category=EventCategory.WORKFLOW)
        assert len(workflow_history) == 2

        # Filter by source
        controller1_history = self.bus.get_history(source="Controller1")
        assert len(controller1_history) == 2

        # Filter with limit
        limited_history = self.bus.get_history(limit=2)
        assert len(limited_history) == 2

    def test_clear_history(self) -> None:
        """Test clearing event history."""
        self.bus.publish(Event(type=EventType.WORKFLOW_NEW, source="Test"))
        self.bus.publish(Event(type=EventType.NODE_ADDED, source="Test"))

        assert len(self.bus.get_history()) == 2

        self.bus.clear_history()

        assert len(self.bus.get_history()) == 0

    def test_metrics(self) -> None:
        """Test performance metrics."""

        def handler(event: Event) -> None:
            pass

        self.bus.subscribe(EventType.WORKFLOW_NEW, handler)
        self.bus.subscribe(EventType.NODE_ADDED, handler)

        # Publish events
        self.bus.publish(Event(type=EventType.WORKFLOW_NEW, source="Test"))
        self.bus.publish(Event(type=EventType.NODE_ADDED, source="Test"))

        # Get metrics
        metrics = self.bus.get_metrics()

        assert metrics["events_published"] == 2
        assert metrics["events_handled"] == 2
        assert metrics["subscribers"] == 2
        assert "avg_handler_time" in metrics

    def test_reset_metrics(self) -> None:
        """Test resetting metrics."""
        self.bus.publish(Event(type=EventType.WORKFLOW_NEW, source="Test"))

        metrics1 = self.bus.get_metrics()
        assert metrics1["events_published"] == 1

        self.bus.reset_metrics()

        metrics2 = self.bus.get_metrics()
        assert metrics2["events_published"] == 0

    def test_error_handling(self) -> None:
        """Test that handler errors are caught and logged."""
        received_events = []

        def failing_handler(event: Event) -> None:
            raise ValueError("Test error")

        def working_handler(event: Event) -> None:
            received_events.append(event)

        self.bus.subscribe(EventType.WORKFLOW_NEW, failing_handler)
        self.bus.subscribe(EventType.WORKFLOW_NEW, working_handler)

        event = Event(type=EventType.WORKFLOW_NEW, source="Test")
        self.bus.publish(event)

        # Working handler should still receive event
        assert len(received_events) == 1

        # Error should be recorded in metrics
        metrics = self.bus.get_metrics()
        assert metrics["errors"] >= 1

    def test_duplicate_subscription_prevention(self) -> None:
        """Test that duplicate subscriptions are prevented."""
        call_count = [0]

        def handler(event: Event) -> None:
            call_count[0] += 1

        # Subscribe same handler twice
        self.bus.subscribe(EventType.WORKFLOW_NEW, handler)
        self.bus.subscribe(EventType.WORKFLOW_NEW, handler)

        event = Event(type=EventType.WORKFLOW_NEW, source="Test")
        self.bus.publish(event)

        # Handler should only be called once
        assert call_count[0] == 1

    def test_enable_disable_history(self) -> None:
        """Test enabling/disabling history tracking."""
        # Disable history
        self.bus.enable_history(False)

        self.bus.publish(Event(type=EventType.WORKFLOW_NEW, source="Test"))

        assert len(self.bus.get_history()) == 0

        # Re-enable history
        self.bus.enable_history(True)

        self.bus.publish(Event(type=EventType.NODE_ADDED, source="Test"))

        assert len(self.bus.get_history()) == 1

    def test_clear_all_subscribers(self) -> None:
        """Test clearing all subscribers."""

        def handler(event: Event) -> None:
            pass

        self.bus.subscribe(EventType.WORKFLOW_NEW, handler)
        self.bus.subscribe(EventType.NODE_ADDED, handler)
        self.bus.subscribe_all(handler)

        metrics1 = self.bus.get_metrics()
        assert metrics1["subscribers"] > 0 or metrics1["wildcard_subscribers"] > 0

        self.bus.clear_all_subscribers()

        metrics2 = self.bus.get_metrics()
        assert metrics2["subscribers"] == 0
        assert metrics2["wildcard_subscribers"] == 0

    def test_thread_safety(self) -> None:
        """Test basic thread safety (concurrent publishes)."""
        import threading

        received_count = [0]
        lock = threading.Lock()

        def handler(event: Event) -> None:
            with lock:
                received_count[0] += 1

        self.bus.subscribe(EventType.WORKFLOW_NEW, handler)

        def publish_events():
            for _ in range(100):
                self.bus.publish(Event(type=EventType.WORKFLOW_NEW, source="Test"))

        # Create multiple threads
        threads = [threading.Thread(target=publish_events) for _ in range(5)]

        # Start threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Should have received all events
        assert received_count[0] == 500  # 5 threads * 100 events

    def test_invalid_handler_type(self) -> None:
        """Test that non-callable handlers raise TypeError."""
        with pytest.raises(TypeError):
            self.bus.subscribe(EventType.WORKFLOW_NEW, "not_callable")

    def test_unsubscribe_nonexistent_handler(self) -> None:
        """Test unsubscribing non-existent handler returns False."""

        def handler(event: Event) -> None:
            pass

        success = self.bus.unsubscribe(EventType.WORKFLOW_NEW, handler)
        assert not success

    def test_event_bus_repr(self) -> None:
        """Test EventBus string representation."""
        repr_str = repr(self.bus)
        assert "EventBus" in repr_str
        assert "subscribers" in repr_str
