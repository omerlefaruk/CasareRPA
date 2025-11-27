"""
Comprehensive tests for SchedulingController.

Tests scheduling management including:
- Schedule workflow dialogs
- Manage schedules
- Run scheduled workflows
- Schedule state management
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QMainWindow

from casare_rpa.presentation.canvas.controllers.scheduling_controller import (
    SchedulingController,
)


@pytest.fixture
def mock_main_window(qtbot):
    """Create a mock MainWindow with scheduling-related components."""
    main_window = QMainWindow()
    qtbot.addWidget(main_window)

    # Mock get_current_file method
    main_window.get_current_file = Mock(return_value=Path("/test/workflow.json"))

    # Mock workflow controller
    main_window._workflow_controller = Mock()
    main_window._workflow_controller._check_unsaved_changes = Mock(return_value=True)
    main_window._workflow_controller.save_workflow_as = Mock()

    # Mock execution controller
    main_window._execution_controller = Mock()
    main_window._execution_controller.run_workflow = Mock()

    # Mock signals
    main_window.workflow_open = Mock()
    main_window.workflow_open.emit = Mock()
    main_window.workflow_run = Mock()
    main_window.workflow_run.emit = Mock()
    main_window.workflow_save = Mock()
    main_window.workflow_save.emit = Mock()

    # Mock methods
    main_window.show_status = Mock()
    main_window.set_current_file = Mock()
    main_window.set_modified = Mock()

    return main_window


@pytest.fixture
def scheduling_controller(mock_main_window):
    """Create a SchedulingController instance."""
    with patch(
        "casare_rpa.canvas.scheduling.schedule_storage.get_schedule_storage"
    ) as mock_storage:
        mock_storage.return_value.get_all_schedules.return_value = []
        controller = SchedulingController(mock_main_window)
        controller.initialize()
        return controller


class TestSchedulingControllerInitialization:
    """Tests for SchedulingController initialization."""

    def test_initialization(self, mock_main_window):
        """Test controller initializes correctly."""
        with patch(
            "casare_rpa.canvas.scheduling.schedule_storage.get_schedule_storage"
        ):
            controller = SchedulingController(mock_main_window)
            assert controller.main_window == mock_main_window
            assert controller._active_schedules == []

    def test_initialize_loads_schedules(self, mock_main_window):
        """Test initialize method loads existing schedules."""
        mock_schedule = Mock()
        with patch(
            "casare_rpa.canvas.scheduling.schedule_storage.get_schedule_storage"
        ) as mock_storage:
            mock_storage.return_value.get_all_schedules.return_value = [mock_schedule]
            controller = SchedulingController(mock_main_window)
            controller.initialize()

            assert controller._active_schedules == [mock_schedule]

    def test_cleanup(self, scheduling_controller):
        """Test cleanup clears schedules."""
        scheduling_controller._active_schedules = [Mock(), Mock()]
        scheduling_controller.cleanup()

        assert scheduling_controller._active_schedules == []
        assert scheduling_controller.is_initialized is False


class TestScheduleStateManagement:
    """Tests for schedule state management."""

    def test_get_schedules(self, scheduling_controller):
        """Test get_schedules returns copy of schedules list."""
        mock_schedules = [Mock(), Mock()]
        scheduling_controller._active_schedules = mock_schedules

        result = scheduling_controller.get_schedules()

        assert result == mock_schedules
        assert result is not mock_schedules  # Should be a copy

    def test_get_schedule_count(self, scheduling_controller):
        """Test get_schedule_count returns correct count."""
        scheduling_controller._active_schedules = [Mock(), Mock(), Mock()]
        assert scheduling_controller.get_schedule_count() == 3

    def test_get_schedule_count_empty(self, scheduling_controller):
        """Test get_schedule_count returns 0 when empty."""
        scheduling_controller._active_schedules = []
        assert scheduling_controller.get_schedule_count() == 0


class TestSignals:
    """Tests for controller signals."""

    def test_schedule_updated_signal(self, scheduling_controller):
        """Test schedule_updated signal can be emitted."""
        received_schedules = []
        scheduling_controller.schedule_updated.connect(
            lambda s: received_schedules.append(s)
        )

        mock_schedule = Mock()
        scheduling_controller.schedule_updated.emit(mock_schedule)

        assert len(received_schedules) == 1
        assert received_schedules[0] == mock_schedule

    def test_schedules_changed_signal(self, scheduling_controller):
        """Test schedules_changed signal can be emitted."""
        signal_count = []
        scheduling_controller.schedules_changed.connect(
            lambda: signal_count.append(True)
        )

        scheduling_controller.schedules_changed.emit()

        assert len(signal_count) == 1

    def test_schedule_created_signal(self, scheduling_controller):
        """Test schedule_created signal can be emitted."""
        received = []
        scheduling_controller.schedule_created.connect(lambda s: received.append(s))

        mock_schedule = Mock()
        scheduling_controller.schedule_created.emit(mock_schedule)

        assert len(received) == 1
        assert received[0] == mock_schedule

    def test_schedule_deleted_signal(self, scheduling_controller):
        """Test schedule_deleted signal can be emitted."""
        received_ids = []
        scheduling_controller.schedule_deleted.connect(
            lambda id: received_ids.append(id)
        )

        scheduling_controller.schedule_deleted.emit("test-id")

        assert len(received_ids) == 1
        assert received_ids[0] == "test-id"

    def test_schedule_run_requested_signal(self, scheduling_controller):
        """Test schedule_run_requested signal can be emitted."""
        received = []
        scheduling_controller.schedule_run_requested.connect(
            lambda s: received.append(s)
        )

        mock_schedule = Mock()
        scheduling_controller.schedule_run_requested.emit(mock_schedule)

        assert len(received) == 1
        assert received[0] == mock_schedule


class TestErrorHandling:
    """Tests for error handling."""

    def test_load_schedules_handles_missing_storage(self, qtbot):
        """Test _load_schedules handles missing storage gracefully."""
        main_window = QMainWindow()
        qtbot.addWidget(main_window)
        main_window.get_current_file = Mock(return_value=None)
        main_window.show_status = Mock()

        with patch(
            "casare_rpa.canvas.scheduling.schedule_storage.get_schedule_storage",
            side_effect=ImportError("Module not found"),
        ):
            controller = SchedulingController(main_window)
            controller.initialize()

            assert controller._active_schedules == []


class TestDeleteSchedule:
    """Tests for delete_schedule functionality."""

    def test_delete_schedule_success(self, scheduling_controller):
        """Test delete_schedule removes schedule and emits signals."""
        mock_schedule = Mock()
        mock_schedule.id = "test-schedule-id"
        scheduling_controller._active_schedules = [mock_schedule]

        with patch(
            "casare_rpa.canvas.scheduling.schedule_storage.get_schedule_storage"
        ) as mock_storage:
            mock_storage.return_value.delete_schedule.return_value = True

            deleted_signals = []
            changed_signals = []
            scheduling_controller.schedule_deleted.connect(
                lambda id: deleted_signals.append(id)
            )
            scheduling_controller.schedules_changed.connect(
                lambda: changed_signals.append(True)
            )

            result = scheduling_controller.delete_schedule("test-schedule-id")

            assert result is True
            assert len(scheduling_controller._active_schedules) == 0
            assert len(deleted_signals) == 1
            assert deleted_signals[0] == "test-schedule-id"
            assert len(changed_signals) == 1

    def test_delete_schedule_not_found(self, scheduling_controller):
        """Test delete_schedule returns False when deletion fails."""
        with patch(
            "casare_rpa.canvas.scheduling.schedule_storage.get_schedule_storage"
        ) as mock_storage:
            mock_storage.return_value.delete_schedule.return_value = False

            result = scheduling_controller.delete_schedule("nonexistent-id")

            assert result is False

    def test_delete_schedule_handles_exception(self, scheduling_controller):
        """Test delete_schedule handles exceptions gracefully."""
        with patch(
            "casare_rpa.canvas.scheduling.schedule_storage.get_schedule_storage"
        ) as mock_storage:
            mock_storage.return_value.delete_schedule.side_effect = Exception(
                "Database error"
            )

            result = scheduling_controller.delete_schedule("test-id")

            assert result is False
