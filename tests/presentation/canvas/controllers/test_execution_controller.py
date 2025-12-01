"""
Comprehensive tests for ExecutionController.

Tests workflow execution control including:
- Run workflow
- Run to node
- Run single node
- Pause/Resume
- Stop execution
- Execution state management
- Validation before run
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from PySide6.QtWidgets import QMainWindow
from PySide6.QtWidgets import QMessageBox

from casare_rpa.presentation.canvas.controllers.execution_controller import (
    ExecutionController,
)


@pytest.fixture
def mock_main_window(qtbot):
    """Create a real QMainWindow with all required attributes."""
    main_window = QMainWindow()
    qtbot.addWidget(main_window)

    main_window._central_widget = Mock()
    main_window._central_widget.graph = Mock()
    main_window._bottom_panel = Mock()
    main_window._bottom_panel.get_validation_errors_blocking = Mock(return_value=[])
    main_window._bottom_panel.show_validation_tab = Mock()

    # Mock show_status method (used by controller)
    main_window.show_status = Mock()

    # Mock workflow signals
    main_window.workflow_run = Mock()
    main_window.workflow_run.emit = Mock()
    main_window.workflow_pause = Mock()
    main_window.workflow_pause.emit = Mock()
    main_window.workflow_resume = Mock()
    main_window.workflow_resume.emit = Mock()
    main_window.workflow_stop = Mock()
    main_window.workflow_stop.emit = Mock()

    # Mock get_graph method
    mock_graph = Mock()
    mock_graph.selected_nodes = Mock(return_value=[])
    main_window.get_graph = Mock(return_value=mock_graph)

    # Mock get_bottom_panel method
    main_window.get_bottom_panel = Mock(return_value=main_window._bottom_panel)

    # Mock actions
    main_window.action_run = Mock()
    main_window.action_run.setEnabled = Mock()
    main_window.action_pause = Mock()
    main_window.action_pause.setEnabled = Mock()
    main_window.action_pause.setChecked = Mock()
    main_window.action_stop = Mock()
    main_window.action_stop.setEnabled = Mock()

    return main_window


@pytest.fixture
def execution_controller(mock_main_window):
    """Create an ExecutionController instance."""
    controller = ExecutionController(mock_main_window)
    controller.initialize()
    return controller


class TestExecutionControllerInitialization:
    """Tests for ExecutionController initialization."""

    def test_initialization_success(self, mock_main_window) -> None:
        """Test controller initializes correctly."""
        controller = ExecutionController(mock_main_window)

        assert controller.main_window == mock_main_window
        assert controller._is_running is False
        assert controller._is_paused is False
        assert not controller.is_initialized

    def test_initialize_sets_state(self, mock_main_window) -> None:
        """Test initialize() sets initialized state."""
        controller = ExecutionController(mock_main_window)
        controller.initialize()

        assert controller.is_initialized

    def test_cleanup_resets_state(self, execution_controller) -> None:
        """Test cleanup() resets initialized state."""
        execution_controller.cleanup()

        assert not execution_controller.is_initialized


class TestExecutionControllerProperties:
    """Tests for ExecutionController properties."""

    def test_is_running_property(self, execution_controller) -> None:
        """Test is_running property getter."""
        assert execution_controller.is_running is False

        execution_controller._is_running = True
        assert execution_controller.is_running is True

    def test_is_paused_property(self, execution_controller) -> None:
        """Test is_paused property getter."""
        assert execution_controller.is_paused is False

        execution_controller._is_paused = True
        assert execution_controller.is_paused is True


class TestRunWorkflow:
    """Tests for running workflow."""

    def test_run_workflow_success(self, execution_controller, mock_main_window) -> None:
        """Test running workflow successfully."""
        signal_emitted = []
        execution_controller.execution_started.connect(
            lambda: signal_emitted.append(True)
        )

        execution_controller.run_workflow()

        assert len(signal_emitted) == 1
        assert execution_controller.is_running is True
        assert execution_controller.is_paused is False
        mock_main_window.action_run.setEnabled.assert_called_with(False)
        mock_main_window.action_pause.setEnabled.assert_called_with(True)
        mock_main_window.action_stop.setEnabled.assert_called_with(True)

    def test_run_workflow_validation_blocks(
        self, execution_controller, mock_main_window
    ) -> None:
        """Test run workflow blocked by validation errors."""
        # Mock validation errors
        mock_main_window._bottom_panel.get_validation_errors_blocking.return_value = [
            {"node_id": "node1", "error": "Missing required field"}
        ]

        with patch.object(QMessageBox, "warning") as mock_warning:
            execution_controller.run_workflow()

        mock_warning.assert_called_once()
        mock_main_window._bottom_panel.show_validation_tab.assert_called_once()
        assert execution_controller.is_running is False

    def test_run_workflow_updates_status_bar(
        self, execution_controller, mock_main_window
    ) -> None:
        """Test run workflow updates status bar."""
        execution_controller.run_workflow()

        mock_main_window.show_status.assert_called()
        call_args = mock_main_window.show_status.call_args[0]
        assert "started" in call_args[0].lower()


class TestRunToNode:
    """Tests for run to node functionality."""

    def test_run_to_node_no_graph(self, execution_controller, mock_main_window) -> None:
        """Test run to node when no graph available falls back to full run."""
        mock_main_window.get_graph.return_value = None

        with patch.object(execution_controller, "run_workflow") as mock_run:
            execution_controller.run_to_node()

        mock_run.assert_called_once()

    def test_run_to_node_no_selection_runs_full_workflow(
        self, execution_controller, mock_main_window
    ) -> None:
        """Test run to node with no selection runs full workflow."""
        mock_main_window.get_graph.return_value.selected_nodes.return_value = []

        with patch.object(execution_controller, "run_workflow") as mock_run:
            execution_controller.run_to_node()

        mock_run.assert_called_once()
        mock_main_window.show_status.assert_called()

    def test_run_to_node_no_node_id_runs_full_workflow(
        self, execution_controller, mock_main_window
    ) -> None:
        """Test run to node with node missing ID runs full workflow."""
        mock_node = Mock()
        mock_node.get_property.return_value = None
        mock_main_window.get_graph.return_value.selected_nodes.return_value = [
            mock_node
        ]

        with patch.object(execution_controller, "run_workflow") as mock_run:
            execution_controller.run_to_node()

        mock_run.assert_called_once()

    def test_run_to_node_success(self, execution_controller, mock_main_window) -> None:
        """Test run to node with valid selection."""
        mock_node = Mock()
        mock_node.get_property.return_value = "test_node_id"
        mock_node.name.return_value = "Test Node"
        mock_main_window.get_graph.return_value.selected_nodes.return_value = [
            mock_node
        ]

        signal_emitted = []
        execution_controller.run_to_node_requested.connect(
            lambda node_id: signal_emitted.append(node_id)
        )

        execution_controller.run_to_node()

        assert len(signal_emitted) == 1
        assert signal_emitted[0] == "test_node_id"
        assert execution_controller.is_running is True
        mock_main_window.show_status.assert_called()

    def test_run_to_node_validation_blocks(
        self, execution_controller, mock_main_window
    ) -> None:
        """Test run to node blocked by validation errors."""
        mock_node = Mock()
        mock_node.get_property.return_value = "test_node_id"
        mock_main_window.get_graph.return_value.selected_nodes.return_value = [
            mock_node
        ]

        # Mock validation errors
        mock_main_window._bottom_panel.get_validation_errors_blocking.return_value = [
            {"node_id": "node1", "error": "Error"}
        ]

        with patch.object(QMessageBox, "warning"):
            execution_controller.run_to_node()

        assert execution_controller.is_running is False


class TestRunSingleNode:
    """Tests for run single node functionality."""

    def test_run_single_node_no_graph(
        self, execution_controller, mock_main_window
    ) -> None:
        """Test run single node when no graph available."""
        mock_main_window.get_graph.return_value = None

        execution_controller.run_single_node()

        mock_main_window.show_status.assert_called_with("No graph available", 3000)

    def test_run_single_node_no_selection(
        self, execution_controller, mock_main_window
    ) -> None:
        """Test run single node with no selection."""
        mock_main_window.get_graph.return_value.selected_nodes.return_value = []

        execution_controller.run_single_node()

        mock_main_window.show_status.assert_called()
        call_args = mock_main_window.show_status.call_args[0]
        assert "No node selected" in call_args[0]

    def test_run_single_node_no_id(
        self, execution_controller, mock_main_window
    ) -> None:
        """Test run single node when node has no ID."""
        mock_node = Mock()
        mock_node.get_property.return_value = None
        mock_main_window.get_graph.return_value.selected_nodes.return_value = [
            mock_node
        ]

        execution_controller.run_single_node()

        mock_main_window.show_status.assert_called()
        call_args = mock_main_window.show_status.call_args[0]
        assert "no ID" in call_args[0]

    def test_run_single_node_success(
        self, execution_controller, mock_main_window
    ) -> None:
        """Test run single node successfully."""
        mock_node = Mock()
        mock_node.get_property.return_value = "single_node_id"
        mock_node.name.return_value = "Single Node"
        mock_main_window.get_graph.return_value.selected_nodes.return_value = [
            mock_node
        ]

        signal_emitted = []
        execution_controller.run_single_node_requested.connect(
            lambda node_id: signal_emitted.append(node_id)
        )

        execution_controller.run_single_node()

        assert len(signal_emitted) == 1
        assert signal_emitted[0] == "single_node_id"
        mock_main_window.show_status.assert_called()


class TestPauseResume:
    """Tests for pause and resume functionality."""

    def test_pause_workflow_when_running(
        self, execution_controller, mock_main_window
    ) -> None:
        """Test pausing running workflow."""
        execution_controller._is_running = True

        signal_emitted = []
        execution_controller.execution_paused.connect(
            lambda: signal_emitted.append(True)
        )

        execution_controller.pause_workflow()

        assert len(signal_emitted) == 1
        assert execution_controller.is_paused is True
        mock_main_window.show_status.assert_called()

    def test_pause_workflow_when_not_running(self, execution_controller) -> None:
        """Test pausing when workflow not running logs warning."""
        signal_emitted = []
        execution_controller.execution_paused.connect(
            lambda: signal_emitted.append(True)
        )

        execution_controller.pause_workflow()

        assert len(signal_emitted) == 0
        assert execution_controller.is_paused is False

    def test_resume_workflow_when_paused(
        self, execution_controller, mock_main_window
    ) -> None:
        """Test resuming paused workflow."""
        execution_controller._is_running = True
        execution_controller._is_paused = True

        signal_emitted = []
        execution_controller.execution_resumed.connect(
            lambda: signal_emitted.append(True)
        )

        execution_controller.resume_workflow()

        assert len(signal_emitted) == 1
        assert execution_controller.is_paused is False
        mock_main_window.show_status.assert_called()

    def test_resume_workflow_when_not_paused(self, execution_controller) -> None:
        """Test resuming when workflow not paused logs warning."""
        signal_emitted = []
        execution_controller.execution_resumed.connect(
            lambda: signal_emitted.append(True)
        )

        execution_controller.resume_workflow()

        assert len(signal_emitted) == 0

    def test_toggle_pause_to_paused(self, execution_controller) -> None:
        """Test toggle_pause pauses when checked is True."""
        execution_controller._is_running = True

        with patch.object(execution_controller, "pause_workflow") as mock_pause:
            execution_controller.toggle_pause(True)

        mock_pause.assert_called_once()

    def test_toggle_pause_to_resumed(self, execution_controller) -> None:
        """Test toggle_pause resumes when checked is False."""
        execution_controller._is_paused = True

        with patch.object(execution_controller, "resume_workflow") as mock_resume:
            execution_controller.toggle_pause(False)

        mock_resume.assert_called_once()


class TestStopWorkflow:
    """Tests for stop workflow functionality."""

    def test_stop_workflow_when_running(
        self, execution_controller, mock_main_window
    ) -> None:
        """Test stopping running workflow."""
        execution_controller._is_running = True
        execution_controller._is_paused = False

        signal_emitted = []
        execution_controller.execution_stopped.connect(
            lambda: signal_emitted.append(True)
        )

        execution_controller.stop_workflow()

        assert len(signal_emitted) == 1
        assert execution_controller.is_running is False
        assert execution_controller.is_paused is False
        mock_main_window.action_run.setEnabled.assert_called_with(True)
        mock_main_window.action_pause.setEnabled.assert_called_with(False)
        mock_main_window.action_stop.setEnabled.assert_called_with(False)

    def test_stop_workflow_when_not_running(self, execution_controller) -> None:
        """Test stopping when workflow not running logs warning."""
        signal_emitted = []
        execution_controller.execution_stopped.connect(
            lambda: signal_emitted.append(True)
        )

        execution_controller.stop_workflow()

        assert len(signal_emitted) == 0


class TestExecutionCallbacks:
    """Tests for execution completion and error callbacks."""

    def test_on_execution_completed(
        self, execution_controller, mock_main_window
    ) -> None:
        """Test handling workflow execution completion."""
        execution_controller._is_running = True
        execution_controller._is_paused = False

        signal_emitted = []
        execution_controller.execution_completed.connect(
            lambda: signal_emitted.append(True)
        )

        execution_controller.on_execution_completed()

        assert len(signal_emitted) == 1
        assert execution_controller.is_running is False
        assert execution_controller.is_paused is False
        mock_main_window.action_run.setEnabled.assert_called_with(True)
        mock_main_window.show_status.assert_called()

    def test_on_execution_error(self, execution_controller, mock_main_window) -> None:
        """Test handling workflow execution error."""
        execution_controller._is_running = True

        signal_emitted = []
        execution_controller.execution_error.connect(
            lambda error: signal_emitted.append(error)
        )

        error_message = "Test error message"
        execution_controller.on_execution_error(error_message)

        assert len(signal_emitted) == 1
        assert signal_emitted[0] == error_message
        assert execution_controller.is_running is False
        assert execution_controller.is_paused is False
        mock_main_window.show_status.assert_called()


class TestPrivateMethods:
    """Tests for private helper methods."""

    def test_check_validation_before_run_no_errors(self, execution_controller) -> None:
        """Test validation check passes with no errors."""
        result = execution_controller._check_validation_before_run()

        assert result is True

    def test_check_validation_before_run_with_errors(
        self, execution_controller, mock_main_window
    ) -> None:
        """Test validation check blocks with errors."""
        mock_main_window._bottom_panel.get_validation_errors_blocking.return_value = [
            {"node_id": "node1", "error": "Error 1"},
            {"node_id": "node2", "error": "Error 2"},
        ]

        with patch.object(QMessageBox, "warning") as mock_warning:
            result = execution_controller._check_validation_before_run()

        assert result is False
        mock_warning.assert_called_once()
        mock_main_window._bottom_panel.show_validation_tab.assert_called_once()

    def test_check_validation_before_run_no_panel(
        self, execution_controller, mock_main_window
    ) -> None:
        """Test validation check passes when bottom panel not available."""
        mock_main_window._bottom_panel = None

        result = execution_controller._check_validation_before_run()

        assert result is True

    def test_update_execution_actions_running(
        self, execution_controller, mock_main_window
    ) -> None:
        """Test updating actions when workflow is running."""
        execution_controller._update_execution_actions(running=True)

        mock_main_window.action_run.setEnabled.assert_called_with(False)
        mock_main_window.action_pause.setEnabled.assert_called_with(True)
        mock_main_window.action_stop.setEnabled.assert_called_with(True)

    def test_update_execution_actions_stopped(
        self, execution_controller, mock_main_window
    ) -> None:
        """Test updating actions when workflow is stopped."""
        execution_controller._update_execution_actions(running=False)

        mock_main_window.action_run.setEnabled.assert_called_with(True)
        mock_main_window.action_pause.setEnabled.assert_called_with(False)
        mock_main_window.action_stop.setEnabled.assert_called_with(False)
        mock_main_window.action_pause.setChecked.assert_called_with(False)

    def test_update_execution_actions_no_actions_attribute(
        self, execution_controller, mock_main_window
    ) -> None:
        """Test updating actions when main window has no action_run attribute."""
        del mock_main_window.action_run

        # Should not raise an error
        execution_controller._update_execution_actions(running=True)


class TestExecutionStateTransitions:
    """Tests for execution state transitions."""

    def test_state_transition_idle_to_running(self, execution_controller) -> None:
        """Test state transition from idle to running."""
        assert execution_controller.is_running is False
        assert execution_controller.is_paused is False

        execution_controller.run_workflow()

        assert execution_controller.is_running is True
        assert execution_controller.is_paused is False

    def test_state_transition_running_to_paused(self, execution_controller) -> None:
        """Test state transition from running to paused."""
        execution_controller._is_running = True

        execution_controller.pause_workflow()

        assert execution_controller.is_running is True
        assert execution_controller.is_paused is True

    def test_state_transition_paused_to_running(self, execution_controller) -> None:
        """Test state transition from paused to running."""
        execution_controller._is_running = True
        execution_controller._is_paused = True

        execution_controller.resume_workflow()

        assert execution_controller.is_running is True
        assert execution_controller.is_paused is False

    def test_state_transition_running_to_stopped(self, execution_controller) -> None:
        """Test state transition from running to stopped."""
        execution_controller._is_running = True

        execution_controller.stop_workflow()

        assert execution_controller.is_running is False
        assert execution_controller.is_paused is False

    def test_state_transition_paused_to_stopped(self, execution_controller) -> None:
        """Test state transition from paused to stopped."""
        execution_controller._is_running = True
        execution_controller._is_paused = True

        execution_controller.stop_workflow()

        assert execution_controller.is_running is False
        assert execution_controller.is_paused is False
