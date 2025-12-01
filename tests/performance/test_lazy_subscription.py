"""
Tests for LazySubscription EventBus optimization.

Validates that:
- Subscription activates on component show
- Subscription deactivates on component hide
- Event handlers receive events only when active
- LazySubscriptionGroup manages multiple subscriptions
"""

import gc
import pytest
from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QApplication, QWidget, QDockWidget
from PySide6.QtCore import QEvent

from casare_rpa.presentation.canvas.events.lazy_subscription import (
    LazySubscription,
    LazySubscriptionGroup,
)
from casare_rpa.presentation.canvas.events.event_bus import EventBus
from casare_rpa.presentation.canvas.events.event import Event
from casare_rpa.presentation.canvas.events.event_types import EventType


# Track all created LazySubscription instances for cleanup
_created_subscriptions = []


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


@pytest.fixture(autouse=True)
def cleanup_lazy_subscriptions():
    """Clean up LazySubscription instances after each test."""
    # Clear before test
    _created_subscriptions.clear()

    yield

    # Clean up all tracked subscriptions after test
    for sub in _created_subscriptions:
        try:
            sub.cleanup()
        except Exception:
            pass
    _created_subscriptions.clear()
    gc.collect()


def _track_subscription(sub):
    """Helper to track a subscription for cleanup."""
    _created_subscriptions.append(sub)
    return sub


@pytest.fixture
def test_widget(qapp):
    """Create test widget for lazy subscription testing."""
    widget = QWidget()
    yield widget
    widget.close()


class TestLazySubscriptionActivation:
    """Tests for subscription activation on show."""

    def test_subscription_not_active_initially(self, event_bus, test_widget):
        """Subscription should not be active before widget is shown."""
        handler = MagicMock()
        lazy_sub = _track_subscription(
            LazySubscription(EventType.WORKFLOW_SAVED, handler, test_widget)
        )

        assert not lazy_sub.active

    def test_subscription_activates_on_show(self, event_bus, test_widget, qtbot):
        """Subscription should activate when widget becomes visible."""
        handler = MagicMock()
        lazy_sub = _track_subscription(
            LazySubscription(EventType.WORKFLOW_SAVED, handler, test_widget)
        )

        assert not lazy_sub.active

        test_widget.show()
        qtbot.waitExposed(test_widget)

        assert lazy_sub.active

    def test_events_received_after_activation(self, event_bus, test_widget, qtbot):
        """Handler should receive events after widget is shown."""
        received_events = []

        def handler(event):
            received_events.append(event)

        lazy_sub = _track_subscription(
            LazySubscription(EventType.WORKFLOW_SAVED, handler, test_widget)
        )

        event = Event(
            type=EventType.WORKFLOW_SAVED,
            source="test",
            data={"file_path": "/test/workflow.json"},
        )
        event_bus.publish(event)

        assert len(received_events) == 0

        test_widget.show()
        qtbot.waitExposed(test_widget)

        event_bus.publish(event)

        assert len(received_events) == 1
        assert received_events[0].data["file_path"] == "/test/workflow.json"


class TestLazySubscriptionDeactivation:
    """Tests for subscription deactivation on hide."""

    def test_subscription_deactivates_on_hide(self, event_bus, test_widget, qtbot):
        """Subscription should deactivate when widget is hidden."""
        handler = MagicMock()
        lazy_sub = _track_subscription(
            LazySubscription(EventType.WORKFLOW_SAVED, handler, test_widget)
        )

        test_widget.show()
        qtbot.waitExposed(test_widget)
        assert lazy_sub.active

        test_widget.hide()

        assert not lazy_sub.active

    def test_events_not_received_after_deactivation(
        self, event_bus, test_widget, qtbot
    ):
        """Handler should not receive events after widget is hidden."""
        received_events = []

        def handler(event):
            received_events.append(event)

        lazy_sub = _track_subscription(
            LazySubscription(EventType.WORKFLOW_SAVED, handler, test_widget)
        )

        test_widget.show()
        qtbot.waitExposed(test_widget)

        event = Event(type=EventType.WORKFLOW_SAVED, source="test", data={"index": 1})
        event_bus.publish(event)

        assert len(received_events) == 1

        test_widget.hide()

        event2 = Event(type=EventType.WORKFLOW_SAVED, source="test", data={"index": 2})
        event_bus.publish(event2)

        assert len(received_events) == 1

    def test_reactivation_on_reshow(self, event_bus, test_widget, qtbot):
        """Subscription should reactivate when widget is shown again."""
        received_events = []

        def handler(event):
            received_events.append(event)

        lazy_sub = _track_subscription(
            LazySubscription(EventType.WORKFLOW_SAVED, handler, test_widget)
        )

        test_widget.show()
        qtbot.waitExposed(test_widget)
        test_widget.hide()

        assert not lazy_sub.active

        test_widget.show()
        qtbot.waitExposed(test_widget)

        assert lazy_sub.active

        event = Event(type=EventType.WORKFLOW_SAVED, source="test", data={"index": 1})
        event_bus.publish(event)

        assert len(received_events) == 1


class TestLazySubscriptionManualControl:
    """Tests for manual activate/deactivate calls."""

    def test_manual_activate(self, event_bus, test_widget):
        """Manual activate should subscribe to EventBus."""
        handler = MagicMock()
        lazy_sub = _track_subscription(
            LazySubscription(EventType.WORKFLOW_SAVED, handler, test_widget)
        )

        assert not lazy_sub.active

        lazy_sub.activate()

        assert lazy_sub.active

        event = Event(type=EventType.WORKFLOW_SAVED, source="test", data={})
        event_bus.publish(event)

        handler.assert_called_once()

    def test_manual_deactivate(self, event_bus, test_widget):
        """Manual deactivate should unsubscribe from EventBus."""
        handler = MagicMock()
        lazy_sub = _track_subscription(
            LazySubscription(EventType.WORKFLOW_SAVED, handler, test_widget)
        )

        lazy_sub.activate()
        assert lazy_sub.active

        lazy_sub.deactivate()
        assert not lazy_sub.active

        event = Event(type=EventType.WORKFLOW_SAVED, source="test", data={})
        event_bus.publish(event)

        handler.assert_not_called()

    def test_activate_idempotent(self, event_bus, test_widget):
        """Multiple activate calls should not add duplicate subscriptions."""
        received_events = []

        def handler(event):
            received_events.append(event)

        lazy_sub = _track_subscription(
            LazySubscription(EventType.WORKFLOW_SAVED, handler, test_widget)
        )

        lazy_sub.activate()
        lazy_sub.activate()
        lazy_sub.activate()

        event = Event(type=EventType.WORKFLOW_SAVED, source="test", data={})
        event_bus.publish(event)

        assert len(received_events) == 1

    def test_deactivate_idempotent(self, event_bus, test_widget):
        """Multiple deactivate calls should not cause errors."""
        handler = MagicMock()
        lazy_sub = _track_subscription(
            LazySubscription(EventType.WORKFLOW_SAVED, handler, test_widget)
        )

        lazy_sub.deactivate()
        lazy_sub.deactivate()
        lazy_sub.deactivate()

        assert not lazy_sub.active


class TestLazySubscriptionOriginalHandlers:
    """Tests for original event handler preservation."""

    def test_cleanup_removes_event_filter(self, event_bus, test_widget, qtbot):
        """cleanup should remove event filter and deactivate subscription."""
        handler = MagicMock()
        lazy_sub = _track_subscription(
            LazySubscription(EventType.WORKFLOW_SAVED, handler, test_widget)
        )

        # Verify initial state
        assert lazy_sub.active is False

        # Activate and verify
        lazy_sub.activate()
        assert lazy_sub.active is True

        # Cleanup should deactivate and remove event filter
        lazy_sub.cleanup()

        assert lazy_sub.active is False

    def test_original_handlers_still_called(self, event_bus, qapp, qtbot):
        """Original show/hide event handlers should still be called."""
        original_show_called = []
        original_hide_called = []

        class TestWidget(QWidget):
            def showEvent(self, event):
                original_show_called.append(True)
                super().showEvent(event)

            def hideEvent(self, event):
                original_hide_called.append(True)
                super().hideEvent(event)

        widget = TestWidget()
        handler = MagicMock()
        lazy_sub = _track_subscription(
            LazySubscription(EventType.WORKFLOW_SAVED, handler, widget)
        )

        widget.show()
        qtbot.waitExposed(widget)

        assert len(original_show_called) == 1

        widget.hide()

        assert len(original_hide_called) == 1

        widget.close()


class TestLazySubscriptionGroup:
    """Tests for LazySubscriptionGroup managing multiple subscriptions."""

    def test_group_creates_multiple_subscriptions(self, event_bus, test_widget):
        """Group should create subscriptions for all provided event types."""
        handlers = [MagicMock() for _ in range(3)]

        group = LazySubscriptionGroup(
            test_widget,
            [
                (EventType.WORKFLOW_SAVED, handlers[0]),
                (EventType.WORKFLOW_NEW, handlers[1]),
                (EventType.NODE_ADDED, handlers[2]),
            ],
        )
        # Track all internal subscriptions
        for sub in group._subscriptions:
            _track_subscription(sub)

        assert len(group._subscriptions) == 3

    def test_group_activates_all_on_show(self, event_bus, test_widget, qtbot):
        """All group subscriptions should activate on widget show."""
        received = {"saved": [], "new": [], "added": []}

        def saved_handler(e):
            received["saved"].append(e)

        def new_handler(e):
            received["new"].append(e)

        def added_handler(e):
            received["added"].append(e)

        group = LazySubscriptionGroup(
            test_widget,
            [
                (EventType.WORKFLOW_SAVED, saved_handler),
                (EventType.WORKFLOW_NEW, new_handler),
                (EventType.NODE_ADDED, added_handler),
            ],
        )
        for sub in group._subscriptions:
            _track_subscription(sub)

        test_widget.show()
        qtbot.waitExposed(test_widget)

        assert group.active

        event_bus.publish(Event(type=EventType.WORKFLOW_SAVED, source="test", data={}))
        event_bus.publish(Event(type=EventType.WORKFLOW_NEW, source="test", data={}))
        event_bus.publish(Event(type=EventType.NODE_ADDED, source="test", data={}))

        assert len(received["saved"]) == 1
        assert len(received["new"]) == 1
        assert len(received["added"]) == 1

    def test_group_deactivates_all_on_hide(self, event_bus, test_widget, qtbot):
        """All group subscriptions should deactivate on widget hide."""
        handler1 = MagicMock()
        handler2 = MagicMock()

        group = LazySubscriptionGroup(
            test_widget,
            [
                (EventType.WORKFLOW_SAVED, handler1),
                (EventType.WORKFLOW_NEW, handler2),
            ],
        )
        for sub in group._subscriptions:
            _track_subscription(sub)

        test_widget.show()
        qtbot.waitExposed(test_widget)
        test_widget.hide()

        assert not group.active

        event_bus.publish(Event(type=EventType.WORKFLOW_SAVED, source="test", data={}))
        event_bus.publish(Event(type=EventType.WORKFLOW_NEW, source="test", data={}))

        handler1.assert_not_called()
        handler2.assert_not_called()

    def test_group_activate_all(self, event_bus, test_widget):
        """activate_all should force activate all subscriptions."""
        handler1 = MagicMock()
        handler2 = MagicMock()

        group = LazySubscriptionGroup(
            test_widget,
            [
                (EventType.WORKFLOW_SAVED, handler1),
                (EventType.WORKFLOW_NEW, handler2),
            ],
        )
        for sub in group._subscriptions:
            _track_subscription(sub)

        group.activate_all()

        assert group.active

        event_bus.publish(Event(type=EventType.WORKFLOW_SAVED, source="test", data={}))
        event_bus.publish(Event(type=EventType.WORKFLOW_NEW, source="test", data={}))

        handler1.assert_called_once()
        handler2.assert_called_once()

    def test_group_deactivate_all(self, event_bus, test_widget, qtbot):
        """deactivate_all should force deactivate all subscriptions."""
        handler = MagicMock()

        group = LazySubscriptionGroup(
            test_widget, [(EventType.WORKFLOW_SAVED, handler)]
        )
        for sub in group._subscriptions:
            _track_subscription(sub)

        test_widget.show()
        qtbot.waitExposed(test_widget)

        assert group.active

        group.deactivate_all()

        assert not group.active

    def test_group_cleanup(self, event_bus, test_widget, qtbot):
        """cleanup should deactivate and clear all subscriptions."""
        handler = MagicMock()
        original_show = test_widget.showEvent

        group = LazySubscriptionGroup(
            test_widget, [(EventType.WORKFLOW_SAVED, handler)]
        )
        for sub in group._subscriptions:
            _track_subscription(sub)

        test_widget.show()
        qtbot.waitExposed(test_widget)

        group.cleanup()

        assert len(group._subscriptions) == 0
        assert test_widget.showEvent == original_show

    def test_empty_group(self, event_bus, test_widget):
        """Empty group should not cause errors."""
        group = LazySubscriptionGroup(test_widget, [])

        assert len(group._subscriptions) == 0
        assert not group.active

        group.activate_all()
        group.deactivate_all()
        group.cleanup()


class TestLazySubscriptionWithDockWidget:
    """Tests with QDockWidget (actual panel type)."""

    def test_dock_widget_lazy_subscription(self, event_bus, qapp, qtbot):
        """LazySubscription should work with QDockWidget panels."""
        dock = QDockWidget("Test Panel")
        received_events = []

        def handler(event):
            received_events.append(event)

        lazy_sub = _track_subscription(
            LazySubscription(EventType.NODE_EXECUTION_STARTED, handler, dock)
        )

        assert not lazy_sub.active

        dock.show()
        qtbot.waitExposed(dock)

        assert lazy_sub.active

        event = Event(
            type=EventType.NODE_EXECUTION_STARTED,
            source="test",
            data={"node_id": "node123"},
        )
        event_bus.publish(event)

        assert len(received_events) == 1
        assert received_events[0].data["node_id"] == "node123"

        dock.hide()
        assert not lazy_sub.active

        # Clean up to prevent event filter errors during teardown
        lazy_sub.cleanup()
        dock.close()


class TestLazySubscriptionEventTypes:
    """Tests for various event types."""

    @pytest.mark.parametrize(
        "event_type",
        [
            EventType.WORKFLOW_SAVED,
            EventType.NODE_EXECUTION_STARTED,
            EventType.NODE_EXECUTION_COMPLETED,
            EventType.VARIABLE_UPDATED,
            EventType.DEBUG_MODE_ENABLED,
            EventType.BREAKPOINT_HIT,
        ],
    )
    def test_various_event_types(self, event_bus, test_widget, qtbot, event_type):
        """LazySubscription should work with various event types."""
        received = []

        def handler(event):
            received.append(event)

        lazy_sub = _track_subscription(
            LazySubscription(event_type, handler, test_widget)
        )

        test_widget.show()
        qtbot.waitExposed(test_widget)

        event = Event(type=event_type, source="test", data={"test": True})
        event_bus.publish(event)

        assert len(received) == 1

        test_widget.hide()
        event_bus.publish(event)

        assert len(received) == 1
