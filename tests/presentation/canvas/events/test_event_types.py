"""
Tests for event type definitions.
"""

import pytest

from casare_rpa.presentation.canvas.events import EventType, EventCategory


class TestEventType:
    """Test EventType enum."""

    def test_event_types_exist(self) -> None:
        """Test that all expected event types are defined."""
        # Workflow events
        assert EventType.WORKFLOW_NEW
        assert EventType.WORKFLOW_OPENED
        assert EventType.WORKFLOW_SAVED
        assert EventType.WORKFLOW_CLOSED

        # Node events
        assert EventType.NODE_ADDED
        assert EventType.NODE_REMOVED
        assert EventType.NODE_SELECTED
        assert EventType.NODE_PROPERTY_CHANGED

        # Execution events
        assert EventType.EXECUTION_STARTED
        assert EventType.EXECUTION_COMPLETED
        assert EventType.EXECUTION_FAILED

        # UI events
        assert EventType.PANEL_TOGGLED
        assert EventType.ZOOM_CHANGED
        assert EventType.THEME_CHANGED

    def test_event_type_category(self) -> None:
        """Test that event types return correct category."""
        assert EventType.WORKFLOW_NEW.category == EventCategory.WORKFLOW
        assert EventType.NODE_ADDED.category == EventCategory.NODE
        assert EventType.CONNECTION_ADDED.category == EventCategory.CONNECTION
        assert EventType.EXECUTION_STARTED.category == EventCategory.EXECUTION
        assert EventType.PANEL_TOGGLED.category == EventCategory.UI
        assert EventType.PROJECT_CREATED.category == EventCategory.PROJECT
        assert EventType.VARIABLE_SET.category == EventCategory.VARIABLE
        assert EventType.DEBUG_MODE_ENABLED.category == EventCategory.DEBUG
        assert EventType.TRIGGER_CREATED.category == EventCategory.TRIGGER

    def test_event_type_string_representation(self) -> None:
        """Test string representation of event types."""
        assert str(EventType.WORKFLOW_NEW) == "WORKFLOW_NEW"
        assert repr(EventType.WORKFLOW_NEW) == "EventType.WORKFLOW_NEW"

    def test_event_type_uniqueness(self) -> None:
        """Test that all event types have unique values."""
        values = [e.value for e in EventType]
        assert len(values) == len(set(values)), "Event type values must be unique"

    def test_event_type_count(self) -> None:
        """Test that we have expected number of event types."""
        # Should have 100+ event types
        event_count = len(list(EventType))
        assert event_count >= 100, f"Expected 100+ event types, got {event_count}"


class TestEventCategory:
    """Test EventCategory enum."""

    def test_categories_exist(self) -> None:
        """Test that all expected categories are defined."""
        assert EventCategory.WORKFLOW
        assert EventCategory.NODE
        assert EventCategory.CONNECTION
        assert EventCategory.EXECUTION
        assert EventCategory.UI
        assert EventCategory.SYSTEM
        assert EventCategory.PROJECT
        assert EventCategory.VARIABLE
        assert EventCategory.DEBUG
        assert EventCategory.TRIGGER

    def test_category_values(self) -> None:
        """Test category string values."""
        assert EventCategory.WORKFLOW.value == "workflow"
        assert EventCategory.NODE.value == "node"
        assert EventCategory.EXECUTION.value == "execution"
