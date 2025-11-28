"""
Tests for AutosaveController.

Tests autosave functionality including:
- Timer management
- Autosave trigger
- Settings synchronization
- Event publishing
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from PySide6.QtCore import QObject, QTimer

from casare_rpa.presentation.canvas.controllers.autosave_controller import (
    AutosaveController,
)
from casare_rpa.presentation.canvas.events.event_types import EventType


@pytest.fixture
def mock_main_window(qtbot):
    """Create a mock main window."""
    main_window = QObject()
    main_window.get_current_file = Mock(return_value="/path/to/workflow.json")
    main_window.workflow_save = Mock()
    main_window.workflow_save.emit = Mock()
    return main_window


@pytest.fixture
def mock_settings_manager():
    """Create a mock settings manager."""
    manager = Mock()
    manager.is_autosave_enabled = Mock(return_value=True)
    manager.get_autosave_interval = Mock(return_value=5)
    return manager


@pytest.fixture
def autosave_controller(mock_main_window, mock_settings_manager, qtbot):
    """Create an AutosaveController instance."""
    with patch(
        "casare_rpa.utils.settings_manager.get_settings_manager",
        return_value=mock_settings_manager,
    ):
        controller = AutosaveController(mock_main_window)
        controller.initialize()
        yield controller
        controller.cleanup()


class TestAutosaveControllerInitialization:
    """Test controller initialization and cleanup."""

    def test_initialization(self, autosave_controller):
        """Test controller initializes correctly."""
        assert autosave_controller.is_initialized
        assert autosave_controller._autosave_timer is not None

    def test_initialization_starts_timer(
        self, autosave_controller, mock_settings_manager
    ):
        """Test controller starts timer on initialization if enabled."""
        mock_settings_manager.is_autosave_enabled.return_value = True

        # Timer should be active
        assert autosave_controller._autosave_timer.isActive()

    def test_cleanup_stops_timer(self, autosave_controller):
        """Test controller cleanup stops timer."""
        autosave_controller.cleanup()

        assert autosave_controller._autosave_timer is None
        assert not autosave_controller.is_initialized


class TestTimerManagement:
    """Test autosave timer management."""

    def test_enable_autosave(self, autosave_controller):
        """Test enabling autosave."""
        autosave_controller._autosave_timer.stop()

        autosave_controller.enable_autosave(10)

        assert autosave_controller._autosave_timer.isActive()
        # 10 minutes = 600000 ms
        assert autosave_controller._autosave_timer.interval() == 600000

    def test_disable_autosave(self, autosave_controller):
        """Test disabling autosave."""
        autosave_controller.enable_autosave(5)

        autosave_controller.disable_autosave()

        assert not autosave_controller._autosave_timer.isActive()

    def test_update_interval(self, autosave_controller):
        """Test updating autosave interval."""
        autosave_controller.enable_autosave(5)

        autosave_controller.update_interval(15)

        # Should be active with new interval
        assert autosave_controller._autosave_timer.isActive()
        # 15 minutes = 900000 ms
        assert autosave_controller._autosave_timer.interval() == 900000

    def test_update_interval_when_inactive(self, autosave_controller):
        """Test updating interval when timer is inactive."""
        autosave_controller.disable_autosave()

        autosave_controller.update_interval(10)

        # Should remain inactive
        assert not autosave_controller._autosave_timer.isActive()

    def test_is_enabled_true(self, autosave_controller):
        """Test is_enabled when autosave is active."""
        autosave_controller.enable_autosave(5)

        assert autosave_controller.is_enabled() is True

    def test_is_enabled_false(self, autosave_controller):
        """Test is_enabled when autosave is inactive."""
        autosave_controller.disable_autosave()

        assert autosave_controller.is_enabled() is False


class TestAutosaveExecution:
    """Test autosave execution."""

    def test_trigger_autosave_now(self, autosave_controller, mock_main_window):
        """Test manually triggering autosave."""
        autosave_controller.trigger_autosave_now()

        # Should emit workflow_save signal
        mock_main_window.workflow_save.emit.assert_called_once()

    def test_autosave_with_current_file(
        self, autosave_controller, mock_main_window, mock_settings_manager
    ):
        """Test autosave when current file exists."""
        mock_main_window.get_current_file.return_value = "/path/to/workflow.json"
        mock_settings_manager.is_autosave_enabled.return_value = True

        autosave_controller._perform_autosave()

        # Should emit workflow_save signal
        mock_main_window.workflow_save.emit.assert_called_once()

    def test_autosave_without_current_file(self, autosave_controller, mock_main_window):
        """Test autosave when no current file."""
        mock_main_window.get_current_file.return_value = None

        autosave_controller._perform_autosave()

        # Should NOT emit workflow_save signal
        mock_main_window.workflow_save.emit.assert_not_called()

    def test_autosave_when_disabled(
        self, autosave_controller, mock_main_window, mock_settings_manager
    ):
        """Test autosave when disabled in settings."""
        mock_settings_manager.is_autosave_enabled.return_value = False

        autosave_controller._perform_autosave()

        # Should NOT emit workflow_save signal
        mock_main_window.workflow_save.emit.assert_not_called()
        # Should stop timer
        assert not autosave_controller._autosave_timer.isActive()


class TestSignals:
    """Test signal emissions."""

    def test_autosave_triggered_signal(
        self, autosave_controller, mock_main_window, mock_settings_manager
    ):
        """Test autosave_triggered signal is emitted."""
        signal_received = []

        def on_triggered():
            signal_received.append(True)

        autosave_controller.autosave_triggered.connect(on_triggered)
        mock_settings_manager.is_autosave_enabled.return_value = True
        mock_main_window.get_current_file.return_value = "/path/to/workflow.json"

        autosave_controller._perform_autosave()

        assert signal_received == [True]

    def test_autosave_completed_signal(
        self, autosave_controller, mock_main_window, mock_settings_manager
    ):
        """Test autosave_completed signal is emitted."""
        signal_received = []

        def on_completed():
            signal_received.append(True)

        autosave_controller.autosave_completed.connect(on_completed)
        mock_settings_manager.is_autosave_enabled.return_value = True
        mock_main_window.get_current_file.return_value = "/path/to/workflow.json"

        autosave_controller._perform_autosave()

        assert signal_received == [True]

    def test_autosave_failed_signal(self, autosave_controller):
        """Test autosave_failed signal is emitted."""
        signal_received = []

        def on_failed(error_msg):
            signal_received.append(error_msg)

        autosave_controller.autosave_failed.connect(on_failed)

        autosave_controller._handle_autosave_failure("Test error")

        assert signal_received == ["Test error"]


class TestEventPublishing:
    """Test event publishing."""

    def test_autosave_triggered_event_published(
        self, autosave_controller, mock_main_window, mock_settings_manager
    ):
        """Test autosave triggered event is published."""
        with patch.object(autosave_controller._event_bus, "publish") as mock_publish:
            mock_settings_manager.is_autosave_enabled.return_value = True
            mock_main_window.get_current_file.return_value = "/path/to/workflow.json"

            autosave_controller._perform_autosave()

            # Verify events were published
            events_published = [call[0][0] for call in mock_publish.call_args_list]
            event_types = [e.type for e in events_published]

            assert EventType.AUTOSAVE_TRIGGERED in event_types
            assert EventType.AUTOSAVE_COMPLETED in event_types

    def test_autosave_failed_event_published(self, autosave_controller):
        """Test autosave failed event is published."""
        with patch.object(autosave_controller._event_bus, "publish") as mock_publish:
            autosave_controller._handle_autosave_failure("Test error")

            # Verify event was published
            assert mock_publish.called
            event = mock_publish.call_args[0][0]
            assert event.type == EventType.AUTOSAVE_FAILED
            assert event.data["error"] == "Test error"


class TestSettingsSynchronization:
    """Test settings synchronization."""

    def test_update_from_settings_enabled(
        self, autosave_controller, mock_settings_manager
    ):
        """Test updating from settings when enabled."""
        mock_settings_manager.is_autosave_enabled.return_value = True
        mock_settings_manager.get_autosave_interval.return_value = 10

        autosave_controller._update_timer_from_settings()

        assert autosave_controller._autosave_timer.isActive()
        assert autosave_controller._autosave_timer.interval() == 600000  # 10 minutes

    def test_update_from_settings_disabled(
        self, autosave_controller, mock_settings_manager
    ):
        """Test updating from settings when disabled."""
        mock_settings_manager.is_autosave_enabled.return_value = False

        autosave_controller._update_timer_from_settings()

        assert not autosave_controller._autosave_timer.isActive()


class TestEventHandlers:
    """Test event handlers."""

    def test_preferences_updated_event(
        self, autosave_controller, mock_settings_manager
    ):
        """Test preferences updated event handler."""
        from casare_rpa.presentation.canvas.events.event import Event

        mock_settings_manager.is_autosave_enabled.return_value = True
        mock_settings_manager.get_autosave_interval.return_value = 15

        event = Event(type=EventType.PREFERENCES_UPDATED, source="Test", data={})

        autosave_controller._on_preferences_updated(event)

        # Timer should be updated
        assert autosave_controller._autosave_timer.isActive()
        assert autosave_controller._autosave_timer.interval() == 900000  # 15 minutes

    def test_workflow_saved_event(self, autosave_controller):
        """Test workflow saved event handler."""
        from casare_rpa.presentation.canvas.events.event import Event

        event = Event(type=EventType.WORKFLOW_SAVED, source="Test", data={})

        # Should not raise exception
        autosave_controller._on_workflow_saved(event)

    def test_workflow_opened_event(self, autosave_controller):
        """Test workflow opened event handler."""
        from casare_rpa.presentation.canvas.events.event import Event

        event = Event(type=EventType.WORKFLOW_OPENED, source="Test", data={})

        # Should not raise exception
        autosave_controller._on_workflow_opened(event)

    def test_workflow_closed_event(self, autosave_controller):
        """Test workflow closed event handler."""
        from casare_rpa.presentation.canvas.events.event import Event

        event = Event(type=EventType.WORKFLOW_CLOSED, source="Test", data={})

        # Should not raise exception
        autosave_controller._on_workflow_closed(event)


class TestErrorHandling:
    """Test error handling."""

    def test_autosave_without_workflow_save_signal(
        self, mock_main_window, mock_settings_manager
    ):
        """Test autosave when workflow_save signal doesn't exist."""
        with patch(
            "casare_rpa.utils.settings_manager.get_settings_manager",
            return_value=mock_settings_manager,
        ):
            # Remove workflow_save attribute
            delattr(mock_main_window, "workflow_save")

            controller = AutosaveController(mock_main_window)
            controller.initialize()

            mock_settings_manager.is_autosave_enabled.return_value = True
            mock_main_window.get_current_file.return_value = "/path/to/workflow.json"

            # Should handle gracefully
            controller._perform_autosave()

            controller.cleanup()

    def test_autosave_with_exception(
        self, autosave_controller, mock_main_window, mock_settings_manager
    ):
        """Test autosave with exception."""
        mock_settings_manager.is_autosave_enabled.side_effect = Exception("Test error")

        # Should not raise exception
        autosave_controller._perform_autosave()

    def test_enable_autosave_when_not_initialized(self, mock_main_window):
        """Test enabling autosave when timer not initialized."""
        controller = AutosaveController(mock_main_window)
        # Don't call initialize()

        # Should handle gracefully
        controller.enable_autosave(5)
