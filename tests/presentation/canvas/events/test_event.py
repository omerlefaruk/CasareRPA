"""
Tests for Event class and related data structures.
"""

import pytest
import time

from casare_rpa.presentation.canvas.events import (
    Event,
    EventType,
    EventCategory,
    EventPriority,
    EventFilter,
)


class TestEventPriority:
    """Test EventPriority enum."""

    def test_priority_ordering(self) -> None:
        """Test that priorities are ordered correctly."""
        assert EventPriority.LOW < EventPriority.NORMAL
        assert EventPriority.NORMAL < EventPriority.HIGH
        assert EventPriority.HIGH < EventPriority.CRITICAL

    def test_priority_comparison(self) -> None:
        """Test priority comparison operators."""
        low = EventPriority.LOW
        high = EventPriority.HIGH

        assert low < high
        assert high > low
        assert low != high


class TestEvent:
    """Test Event class."""

    def test_create_simple_event(self) -> None:
        """Test creating a simple event."""
        event = Event(
            type=EventType.WORKFLOW_NEW,
            source="TestController",
        )

        assert event.type == EventType.WORKFLOW_NEW
        assert event.source == "TestController"
        assert event.data is None
        assert event.priority == EventPriority.NORMAL
        assert isinstance(event.timestamp, float)
        assert isinstance(event.event_id, str)
        assert event.correlation_id is None

    def test_create_event_with_data(self) -> None:
        """Test creating event with data payload."""
        data = {"workflow_id": "123", "name": "My Workflow"}

        event = Event(
            type=EventType.WORKFLOW_SAVED,
            source="WorkflowController",
            data=data,
        )

        assert event.data == data
        assert event.get("workflow_id") == "123"
        assert event.get("name") == "My Workflow"
        assert event.get("nonexistent", "default") == "default"

    def test_create_event_with_priority(self) -> None:
        """Test creating event with custom priority."""
        event = Event(
            type=EventType.ERROR_OCCURRED,
            source="System",
            priority=EventPriority.CRITICAL,
        )

        assert event.priority == EventPriority.CRITICAL
        assert event.is_high_priority()

    def test_event_category(self) -> None:
        """Test that event category is derived from type."""
        event = Event(type=EventType.WORKFLOW_NEW, source="Test")
        assert event.category == EventCategory.WORKFLOW

        event = Event(type=EventType.NODE_ADDED, source="Test")
        assert event.category == EventCategory.NODE

    def test_event_datetime(self) -> None:
        """Test that event timestamp converts to datetime."""
        event = Event(type=EventType.WORKFLOW_NEW, source="Test")

        dt = event.datetime
        assert dt is not None
        assert dt.timestamp() == pytest.approx(event.timestamp, rel=0.001)

    def test_event_has_data(self) -> None:
        """Test has_data method."""
        event = Event(
            type=EventType.WORKFLOW_NEW,
            source="Test",
            data={"key": "value"},
        )

        assert event.has_data("key")
        assert not event.has_data("nonexistent")

    def test_event_to_dict(self) -> None:
        """Test event serialization to dict."""
        event = Event(
            type=EventType.WORKFLOW_SAVED,
            source="WorkflowController",
            data={"file_path": "/path/to/file.json"},
            priority=EventPriority.HIGH,
        )

        d = event.to_dict()

        assert d["type"] == "WORKFLOW_SAVED"
        assert d["category"] == "workflow"
        assert d["source"] == "WorkflowController"
        assert d["data"] == {"file_path": "/path/to/file.json"}
        assert d["priority"] == "HIGH"
        assert "timestamp" in d
        assert "datetime" in d
        assert "event_id" in d

    def test_event_string_representation(self) -> None:
        """Test event string representations."""
        event = Event(
            type=EventType.NODE_ADDED,
            source="NodeController",
            data={"node_id": "123"},
        )

        string = str(event)
        assert "NODE_ADDED" in string
        assert "NodeController" in string
        assert "node_id" in string

    def test_event_validation_invalid_type(self) -> None:
        """Test that invalid event type raises error."""
        with pytest.raises(TypeError):
            Event(
                type="INVALID",  # Should be EventType enum
                source="Test",
            )

    def test_event_validation_empty_source(self) -> None:
        """Test that empty source raises error."""
        with pytest.raises(ValueError):
            Event(
                type=EventType.WORKFLOW_NEW,
                source="",  # Empty source
            )

    def test_event_validation_invalid_data(self) -> None:
        """Test that invalid data type raises error."""
        with pytest.raises(TypeError):
            Event(
                type=EventType.WORKFLOW_NEW,
                source="Test",
                data="invalid",  # Should be dict or None
            )

    def test_event_correlation_id(self) -> None:
        """Test event correlation ID."""
        correlation_id = "exec-123"

        event1 = Event(
            type=EventType.EXECUTION_STARTED,
            source="ExecutionController",
            correlation_id=correlation_id,
        )

        event2 = Event(
            type=EventType.EXECUTION_COMPLETED,
            source="ExecutionController",
            correlation_id=correlation_id,
        )

        assert event1.correlation_id == event2.correlation_id
        assert event1.correlation_id == correlation_id

    def test_event_immutability(self) -> None:
        """Test that events are immutable (frozen dataclass)."""
        event = Event(type=EventType.WORKFLOW_NEW, source="Test")

        with pytest.raises(AttributeError):
            event.type = EventType.WORKFLOW_SAVED  # Should be frozen

    def test_event_unique_ids(self) -> None:
        """Test that event IDs are unique."""
        events = [Event(type=EventType.WORKFLOW_NEW, source="Test") for _ in range(100)]

        event_ids = [e.event_id for e in events]
        assert len(event_ids) == len(set(event_ids)), "Event IDs must be unique"


class TestEventFilter:
    """Test EventFilter class."""

    def test_filter_by_type(self) -> None:
        """Test filtering by event type."""
        filter = EventFilter(types=[EventType.WORKFLOW_NEW, EventType.WORKFLOW_SAVED])

        event1 = Event(type=EventType.WORKFLOW_NEW, source="Test")
        event2 = Event(type=EventType.WORKFLOW_SAVED, source="Test")
        event3 = Event(type=EventType.NODE_ADDED, source="Test")

        assert filter.matches(event1)
        assert filter.matches(event2)
        assert not filter.matches(event3)

    def test_filter_by_category(self) -> None:
        """Test filtering by event category."""
        filter = EventFilter(categories=[EventCategory.WORKFLOW])

        event1 = Event(type=EventType.WORKFLOW_NEW, source="Test")
        event2 = Event(type=EventType.NODE_ADDED, source="Test")

        assert filter.matches(event1)
        assert not filter.matches(event2)

    def test_filter_by_source(self) -> None:
        """Test filtering by event source."""
        filter = EventFilter(sources=["WorkflowController"])

        event1 = Event(type=EventType.WORKFLOW_NEW, source="WorkflowController")
        event2 = Event(type=EventType.WORKFLOW_NEW, source="OtherController")

        assert filter.matches(event1)
        assert not filter.matches(event2)

    def test_filter_by_priority(self) -> None:
        """Test filtering by priority range."""
        filter = EventFilter(min_priority=EventPriority.HIGH)

        event1 = Event(
            type=EventType.WORKFLOW_NEW, source="Test", priority=EventPriority.HIGH
        )
        event2 = Event(
            type=EventType.WORKFLOW_NEW, source="Test", priority=EventPriority.CRITICAL
        )
        event3 = Event(
            type=EventType.WORKFLOW_NEW, source="Test", priority=EventPriority.NORMAL
        )

        assert filter.matches(event1)
        assert filter.matches(event2)
        assert not filter.matches(event3)

    def test_filter_combined(self) -> None:
        """Test filtering with multiple criteria (AND logic)."""
        filter = EventFilter(
            categories=[EventCategory.EXECUTION], min_priority=EventPriority.HIGH
        )

        event1 = Event(
            type=EventType.EXECUTION_STARTED,
            source="Test",
            priority=EventPriority.HIGH,
        )
        event2 = Event(
            type=EventType.EXECUTION_STARTED,
            source="Test",
            priority=EventPriority.NORMAL,
        )
        event3 = Event(
            type=EventType.NODE_ADDED, source="Test", priority=EventPriority.HIGH
        )

        assert filter.matches(event1)  # Matches both criteria
        assert not filter.matches(event2)  # Wrong priority
        assert not filter.matches(event3)  # Wrong category

    def test_filter_string_representation(self) -> None:
        """Test filter string representation."""
        filter = EventFilter(
            types=[EventType.WORKFLOW_NEW], min_priority=EventPriority.HIGH
        )

        string = str(filter)
        assert "WORKFLOW_NEW" in string
        assert "HIGH" in string
