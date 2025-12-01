"""
Tests for WorkflowController shutdown signal handling.

Verifies that RuntimeError from deleted signal sources during application
shutdown is properly handled, preventing crashes when:
- Qt objects are garbage collected
- Signals fire during cleanup
- The undo stack's cleanChanged signal triggers after controller deletion

Bug reference: Signal source has been deleted RuntimeError during shutdown.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from PySide6.QtCore import Signal, QObject
from PySide6.QtWidgets import QMainWindow

from casare_rpa.presentation.canvas.controllers.workflow_controller import (
    WorkflowController,
)


class RaisingSignal:
    """
    Fake signal that raises RuntimeError when emit is called.

    Simulates the behavior of a Qt signal whose source object
    has been garbage collected during application shutdown.
    """

    def emit(self, *args, **kwargs):
        raise RuntimeError("Signal source has been deleted")

    def connect(self, *args, **kwargs):
        pass

    def disconnect(self, *args, **kwargs):
        pass


@pytest.fixture
def mock_main_window(qtbot):
    """Create a real QMainWindow with required mocks."""
    main_window = QMainWindow()
    qtbot.addWidget(main_window)

    main_window._central_widget = Mock()
    main_window._central_widget.graph = Mock()
    main_window.show_status = Mock()

    mock_graph = Mock()
    mock_graph.selected_nodes = Mock(return_value=[])
    main_window.get_graph = Mock(return_value=mock_graph)

    main_window._bottom_panel = Mock()
    main_window._bottom_panel.get_validation_errors_blocking = Mock(return_value=[])
    main_window.get_bottom_panel = Mock(return_value=main_window._bottom_panel)

    main_window.action_save = Mock()
    main_window.setWindowTitle = Mock()

    return main_window


@pytest.fixture
def workflow_controller(mock_main_window):
    """Create a WorkflowController instance."""
    controller = WorkflowController(mock_main_window)
    controller.initialize()
    return controller


class TestShutdownSignalHandling:
    """
    Tests for signal emission during shutdown scenarios.

    These tests verify that the WorkflowController properly handles
    RuntimeError exceptions raised when signals fire after their
    source Qt objects have been garbage collected.
    """

    def test_set_current_file_handles_runtime_error(
        self, workflow_controller, mock_main_window
    ) -> None:
        """
        Test set_current_file gracefully handles RuntimeError on signal emit.

        Scenario:
        1. Application is shutting down
        2. Qt garbage collector deletes the WorkflowController
        3. The cleanChanged signal fires from the undo stack
        4. This triggers set_current_file which tries to emit current_file_changed
        5. RuntimeError is raised because the signal source is deleted
        6. The exception should be caught and handled gracefully
        """
        # Replace the signal with one that raises RuntimeError
        workflow_controller.current_file_changed = RaisingSignal()

        test_path = Path("/test/workflow.json")

        # Should not raise - RuntimeError should be caught
        workflow_controller.set_current_file(test_path)

        # State should still be updated before the error
        assert workflow_controller._current_file == test_path

    def test_set_modified_handles_runtime_error(
        self, workflow_controller, mock_main_window
    ) -> None:
        """
        Test set_modified gracefully handles RuntimeError on signal emit.

        This is the most common failure scenario during shutdown:
        1. User closes the application
        2. Qt begins cleanup, undo stack is cleared
        3. cleanChanged(True) signal fires
        4. MainWindow.set_modified() calls WorkflowController.set_modified()
        5. WorkflowController tries to emit modified_changed signal
        6. RuntimeError is raised because Qt object is already deleted
        7. The exception should be caught and execution should stop gracefully
        """
        # Replace the signal with one that raises RuntimeError
        workflow_controller.modified_changed = RaisingSignal()

        # Should not raise - RuntimeError should be caught
        workflow_controller.set_modified(True)

        # State should be updated before the error
        assert workflow_controller._is_modified is True

    def test_set_current_file_returns_early_on_runtime_error(
        self, workflow_controller, mock_main_window
    ) -> None:
        """
        Test that set_current_file returns early after RuntimeError.

        After catching the RuntimeError, the method should return immediately
        without calling _update_window_title(), preventing further errors.
        """
        workflow_controller.current_file_changed = RaisingSignal()

        # Mock _update_window_title to verify it's not called after error
        with patch.object(workflow_controller, "_update_window_title") as mock_update:
            workflow_controller.set_current_file(Path("/test/new.json"))

            # _update_window_title should NOT be called because we return early
            mock_update.assert_not_called()

    def test_set_modified_returns_early_on_runtime_error(
        self, workflow_controller, mock_main_window
    ) -> None:
        """
        Test that set_modified returns early after RuntimeError.

        After catching the RuntimeError, the method should return immediately
        without calling _update_window_title() or _update_save_action().
        """
        workflow_controller.modified_changed = RaisingSignal()

        # Mock methods to verify they're not called after error
        with patch.object(workflow_controller, "_update_window_title") as mock_title:
            with patch.object(
                workflow_controller, "_update_save_action"
            ) as mock_action:
                workflow_controller.set_modified(True)

                # Neither should be called because we return early
                mock_title.assert_not_called()
                mock_action.assert_not_called()

    def test_normal_signal_emission_still_works(
        self, workflow_controller, mock_main_window
    ) -> None:
        """
        Test that normal signal emission still works when not in shutdown.

        Ensures the try/except doesn't break normal operation.
        """
        file_changes = []
        modified_changes = []

        workflow_controller.current_file_changed.connect(
            lambda val: file_changes.append(val)
        )
        workflow_controller.modified_changed.connect(
            lambda val: modified_changes.append(val)
        )

        test_path = Path("/test/workflow.json")
        workflow_controller.set_current_file(test_path)
        workflow_controller.set_modified(True)

        assert len(file_changes) == 1
        assert file_changes[0] == test_path
        assert len(modified_changes) == 1
        assert modified_changes[0] is True

    def test_no_emit_when_value_unchanged(
        self, workflow_controller, mock_main_window
    ) -> None:
        """
        Test that signals don't emit when values haven't changed.

        This is important during shutdown - if the value is the same,
        we skip the emit entirely and avoid the RuntimeError path.
        """
        file_changes = []
        modified_changes = []

        workflow_controller.current_file_changed.connect(
            lambda val: file_changes.append(val)
        )
        workflow_controller.modified_changed.connect(
            lambda val: modified_changes.append(val)
        )

        # Set initial values
        workflow_controller._current_file = None
        workflow_controller._is_modified = False

        # Try to set to same values - should not emit
        workflow_controller.set_current_file(None)
        workflow_controller.set_modified(False)

        assert len(file_changes) == 0
        assert len(modified_changes) == 0


class TestEdgeCases:
    """
    Edge case tests for shutdown-related scenarios.
    """

    def test_multiple_rapid_modifications_during_shutdown(
        self, workflow_controller, mock_main_window
    ) -> None:
        """
        Test handling of rapid modifications just before complete shutdown.

        Simulates the case where multiple events fire in quick succession
        during shutdown, with some succeeding and others failing.
        """
        call_count = {"count": 0}

        class IntermittentRaisingSignal:
            """Signal that raises on every other call."""

            def emit(self, *args):
                call_count["count"] += 1
                if call_count["count"] % 2 == 0:
                    raise RuntimeError("Signal source has been deleted")

            def connect(self, *args):
                pass

            def disconnect(self, *args):
                pass

        workflow_controller.modified_changed = IntermittentRaisingSignal()

        # Rapid modifications - some will succeed, some will "fail" gracefully
        for i in range(5):
            workflow_controller._is_modified = i % 2 == 0  # Alternate state
            workflow_controller.set_modified(i % 2 == 1)  # Force state change

        # Should complete without raising

    def test_state_consistency_after_shutdown_error(
        self, workflow_controller, mock_main_window
    ) -> None:
        """
        Test that internal state remains consistent after shutdown errors.

        Even when signal emission fails, the internal state (_current_file,
        _is_modified) should be properly updated before the error.
        """
        workflow_controller.current_file_changed = RaisingSignal()
        workflow_controller.modified_changed = RaisingSignal()

        # Update both values
        test_path = Path("/test/state_test.json")
        workflow_controller.set_current_file(test_path)
        workflow_controller.set_modified(True)

        # Internal state should be correct
        assert workflow_controller._current_file == test_path
        assert workflow_controller._is_modified is True

        # Properties should expose correct state
        assert workflow_controller.current_file == test_path
        assert workflow_controller.is_modified is True
