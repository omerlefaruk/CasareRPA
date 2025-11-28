"""
Tests for EventBatcher high-frequency event batching.

Validates that:
- Batchable events are batched (10 events -> 1 batched event)
- Non-batchable events publish immediately
- Timer-based flushing works correctly
- Force flush and clear operations work
"""

import pytest
from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from casare_rpa.presentation.canvas.events.event_batcher import EventBatcher
from casare_rpa.presentation.canvas.events.event_bus import EventBus
from casare_rpa.presentation.canvas.events.event import Event
from casare_rpa.presentation.canvas.events.event_types import EventType


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for Qt tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def event_bus(qapp):
    """Fresh EventBus instance for each test."""
    EventBus.reset_instance()
    bus = EventBus()
    yield bus
    bus.clear_all_subscribers()
    EventBus.reset_instance()


@pytest.fixture
def batcher(qapp, event_bus):
    """Fresh EventBatcher instance for each test."""
    batcher = EventBatcher(interval_ms=50)
    yield batcher
    batcher.clear()


class TestEventBatcherBatchableEvents:
    """Tests for batchable event handling."""

    def test_batchable_events_are_queued(self, batcher, event_bus):
        """Batchable events should be queued, not published immediately."""
        received = []

        def handler(event):
            received.append(event)

        event_bus.subscribe(EventType.VARIABLE_UPDATED, handler)

        event = Event(
            type=EventType.VARIABLE_UPDATED,
            source="test",
            data={"name": "counter", "value": 1},
        )
        batcher.batch(event)

        assert len(received) == 0
        assert batcher.has_pending()
        assert batcher.pending_count() == 1

    def test_multiple_events_batched_into_one(self, batcher, event_bus, qapp):
        """10 events should become 1 batched event."""
        received = []

        def handler(event):
            received.append(event)

        event_bus.subscribe(EventType.VARIABLE_UPDATED, handler)

        for i in range(10):
            batcher.batch(
                Event(type=EventType.VARIABLE_UPDATED, source="test", data={"value": i})
            )

        assert len(received) == 0
        assert batcher.pending_count() == 10

        batcher.flush_now()

        assert len(received) == 1
        assert received[0].data["count"] == 10
        assert len(received[0].data["batched_events"]) == 10
        assert received[0].source == "EventBatcher"

    def test_different_batchable_types_batched_separately(self, batcher, event_bus):
        """Different batchable event types should be batched separately."""
        variable_events = []
        property_events = []

        def variable_handler(event):
            variable_events.append(event)

        def property_handler(event):
            property_events.append(event)

        event_bus.subscribe(EventType.VARIABLE_UPDATED, variable_handler)
        event_bus.subscribe(EventType.NODE_PROPERTY_CHANGED, property_handler)

        for i in range(5):
            batcher.batch(
                Event(type=EventType.VARIABLE_UPDATED, source="test", data={"value": i})
            )

        for i in range(3):
            batcher.batch(
                Event(
                    type=EventType.NODE_PROPERTY_CHANGED,
                    source="test",
                    data={"property": f"prop_{i}"},
                )
            )

        assert batcher.pending_count() == 8

        batcher.flush_now()

        assert len(variable_events) == 1
        assert variable_events[0].data["count"] == 5

        assert len(property_events) == 1
        assert property_events[0].data["count"] == 3

    def test_position_changed_is_batchable(self, batcher, event_bus):
        """NODE_POSITION_CHANGED should be batchable."""
        received = []

        def handler(event):
            received.append(event)

        event_bus.subscribe(EventType.NODE_POSITION_CHANGED, handler)

        for i in range(5):
            batcher.batch(
                Event(
                    type=EventType.NODE_POSITION_CHANGED,
                    source="test",
                    data={"x": i * 10, "y": i * 10},
                )
            )

        assert len(received) == 0
        batcher.flush_now()
        assert len(received) == 1
        assert received[0].data["count"] == 5


class TestEventBatcherNonBatchableEvents:
    """Tests for non-batchable event handling."""

    def test_non_batchable_events_publish_immediately(self, batcher, event_bus):
        """Non-batchable events should publish immediately."""
        received = []

        def handler(event):
            received.append(event)

        event_bus.subscribe(EventType.WORKFLOW_SAVED, handler)

        event = Event(
            type=EventType.WORKFLOW_SAVED,
            source="test",
            data={"file_path": "/test/workflow.json"},
        )
        batcher.batch(event)

        assert len(received) == 1
        assert received[0].data["file_path"] == "/test/workflow.json"
        assert not batcher.has_pending()

    def test_workflow_events_not_batched(self, batcher, event_bus):
        """Workflow events should never be batched."""
        received = []

        def handler(event):
            received.append(event)

        event_bus.subscribe(EventType.WORKFLOW_NEW, handler)

        for i in range(5):
            batcher.batch(
                Event(type=EventType.WORKFLOW_NEW, source="test", data={"index": i})
            )

        assert len(received) == 5
        assert not batcher.has_pending()

    def test_execution_events_not_batched(self, batcher, event_bus):
        """Execution events should publish immediately."""
        received = []

        def handler(event):
            received.append(event)

        event_bus.subscribe(EventType.EXECUTION_STARTED, handler)

        batcher.batch(
            Event(
                type=EventType.EXECUTION_STARTED,
                source="test",
                data={"workflow_id": "123"},
            )
        )

        assert len(received) == 1


class TestEventBatcherTimerBehavior:
    """Tests for timer-based flushing."""

    def test_timer_starts_on_first_batch(self, batcher, event_bus):
        """Timer should start when first batchable event is added."""
        assert not batcher.timer.isActive()

        batcher.batch(
            Event(type=EventType.VARIABLE_UPDATED, source="test", data={"value": 1})
        )

        assert batcher.timer.isActive()

    def test_timer_stopped_after_flush(self, batcher, event_bus):
        """Timer should stop after flush."""
        batcher.batch(
            Event(type=EventType.VARIABLE_UPDATED, source="test", data={"value": 1})
        )

        assert batcher.timer.isActive()
        batcher.flush_now()
        assert not batcher.timer.isActive()

    def test_timer_not_started_for_non_batchable(self, batcher, event_bus):
        """Timer should not start for non-batchable events."""
        batcher.batch(Event(type=EventType.WORKFLOW_SAVED, source="test", data={}))

        assert not batcher.timer.isActive()

    def test_auto_flush_on_timer(self, batcher, event_bus, qapp, qtbot):
        """Events should auto-flush when timer fires."""
        received = []

        def handler(event):
            received.append(event)

        event_bus.subscribe(EventType.VARIABLE_UPDATED, handler)

        for i in range(5):
            batcher.batch(
                Event(type=EventType.VARIABLE_UPDATED, source="test", data={"value": i})
            )

        assert len(received) == 0

        qtbot.wait(100)

        assert len(received) == 1
        assert received[0].data["count"] == 5


class TestEventBatcherUtilityMethods:
    """Tests for utility methods."""

    def test_clear_discards_pending_events(self, batcher, event_bus):
        """clear() should discard pending events without publishing."""
        received = []

        def handler(event):
            received.append(event)

        event_bus.subscribe(EventType.VARIABLE_UPDATED, handler)

        for i in range(5):
            batcher.batch(
                Event(type=EventType.VARIABLE_UPDATED, source="test", data={"value": i})
            )

        assert batcher.pending_count() == 5

        batcher.clear()

        assert batcher.pending_count() == 0
        assert not batcher.has_pending()
        assert not batcher.timer.isActive()
        assert len(received) == 0

    def test_pending_count_accuracy(self, batcher, event_bus):
        """pending_count() should return accurate count."""
        assert batcher.pending_count() == 0

        for i in range(3):
            batcher.batch(
                Event(type=EventType.VARIABLE_UPDATED, source="test", data={"value": i})
            )

        for i in range(2):
            batcher.batch(
                Event(
                    type=EventType.NODE_PROPERTY_CHANGED,
                    source="test",
                    data={"value": i},
                )
            )

        assert batcher.pending_count() == 5

    def test_has_pending_returns_correct_state(self, batcher, event_bus):
        """has_pending() should return correct state."""
        assert not batcher.has_pending()

        batcher.batch(
            Event(type=EventType.VARIABLE_UPDATED, source="test", data={"value": 1})
        )

        assert batcher.has_pending()

        batcher.flush_now()

        assert not batcher.has_pending()

    def test_repr_shows_state(self, batcher, event_bus):
        """__repr__ should show current state."""
        repr_str = repr(batcher)
        assert "EventBatcher" in repr_str
        assert "interval_ms=50" in repr_str
        assert "pending=0" in repr_str

        batcher.batch(
            Event(type=EventType.VARIABLE_UPDATED, source="test", data={"value": 1})
        )

        repr_str = repr(batcher)
        assert "pending=1" in repr_str
        assert "active=True" in repr_str


class TestEventBatcherEdgeCases:
    """Tests for edge cases."""

    def test_flush_with_no_pending_events(self, batcher, event_bus):
        """flush_now() should handle empty pending gracefully."""
        batcher.flush_now()
        assert not batcher.has_pending()

    def test_multiple_flushes(self, batcher, event_bus):
        """Multiple flush calls should work correctly."""
        received = []

        def handler(event):
            received.append(event)

        event_bus.subscribe(EventType.VARIABLE_UPDATED, handler)

        batcher.batch(
            Event(type=EventType.VARIABLE_UPDATED, source="test", data={"value": 1})
        )
        batcher.flush_now()

        batcher.batch(
            Event(type=EventType.VARIABLE_UPDATED, source="test", data={"value": 2})
        )
        batcher.flush_now()

        assert len(received) == 2
        assert received[0].data["count"] == 1
        assert received[1].data["count"] == 1

    def test_batched_events_preserve_original_data(self, batcher, event_bus):
        """Batched events should preserve original event data."""
        received = []

        def handler(event):
            received.append(event)

        event_bus.subscribe(EventType.VARIABLE_UPDATED, handler)

        original_events = [
            Event(
                type=EventType.VARIABLE_UPDATED,
                source=f"source_{i}",
                data={"name": f"var_{i}", "value": i * 100},
            )
            for i in range(3)
        ]

        for event in original_events:
            batcher.batch(event)

        batcher.flush_now()

        batched = received[0].data["batched_events"]
        assert len(batched) == 3

        for i, orig in enumerate(original_events):
            assert batched[i].source == orig.source
            assert batched[i].data == orig.data

    def test_custom_interval(self, qapp, event_bus):
        """Custom interval should be respected."""
        batcher = EventBatcher(interval_ms=100)
        assert batcher.interval_ms == 100

        batcher = EventBatcher(interval_ms=1)
        assert batcher.interval_ms == 1

    def test_batchable_events_constant(self):
        """BATCHABLE_EVENTS should contain expected event types."""
        assert EventType.VARIABLE_UPDATED in EventBatcher.BATCHABLE_EVENTS
        assert EventType.NODE_PROPERTY_CHANGED in EventBatcher.BATCHABLE_EVENTS
        assert EventType.NODE_POSITION_CHANGED in EventBatcher.BATCHABLE_EVENTS

        assert EventType.WORKFLOW_SAVED not in EventBatcher.BATCHABLE_EVENTS
        assert EventType.EXECUTION_STARTED not in EventBatcher.BATCHABLE_EVENTS
