"""
Tests for ExecutionController EventBus integration.

Tests EventBus-based execution feedback:
- EventBus setup
- Node started/completed/error events
- Workflow completed/error/stopped events
- Visual node status updates
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from PySide6.QtWidgets import QMainWindow

from casare_rpa.presentation.canvas.controllers.execution_controller import (
    ExecutionController,
)


@pytest.fixture
def mock_main_window(qtbot):
    """Create a mock main window."""
    main_window = QMainWindow()
    qtbot.addWidget(main_window)

    # Mock graph
    mock_graph = Mock()
    mock_node1 = Mock()
    mock_node1.get_property = Mock(return_value="node1")
    mock_node1.set_property = Mock()
    mock_graph.all_nodes = Mock(return_value=[mock_node1])

    main_window.get_graph = Mock(return_value=mock_graph)
    main_window.show_status = Mock()
    main_window.get_log_viewer = Mock(return_value=None)

    # Mock signals
    main_window.workflow_run = Mock()
    main_window.action_run = Mock()
    main_window.action_run_to_node = Mock()
    main_window.action_pause = Mock()
    main_window.action_stop = Mock()

    return main_window


@pytest.fixture
def execution_controller(mock_main_window):
    """Create an ExecutionController instance."""
    controller = ExecutionController(mock_main_window)
    return controller


class TestEventBusSetup:
    """Tests for EventBus setup functionality."""

    def test_setup_event_bus_success(
        self, execution_controller, mock_main_window
    ) -> None:
        """Test EventBus setup succeeds when available."""
        # Initialize will set up event bus
        execution_controller.initialize()

        # Verify event bus was setup
        assert execution_controller._event_bus is not None

    def test_setup_event_bus_with_log_viewer(
        self, execution_controller, mock_main_window
    ) -> None:
        """Test EventBus setup subscribes log viewer to all events."""
        mock_log_viewer = Mock()
        mock_log_viewer.log_event = Mock()
        mock_main_window.get_log_viewer.return_value = mock_log_viewer

        execution_controller.initialize()

        # Verify event bus setup completed
        assert execution_controller._event_bus is not None

    def test_setup_event_bus_handles_import_error(self, execution_controller) -> None:
        """Test EventBus setup handles missing EventBus gracefully."""
        # Patch to cause import error
        import sys

        original_modules = sys.modules.copy()
        if "casare_rpa.domain.events" in sys.modules:
            del sys.modules["casare_rpa.domain.events"]

        try:
            execution_controller.initialize()
            # Should not raise exception even if import fails
        finally:
            sys.modules.update(original_modules)


class TestNodeEventHandlers:
    """Tests for node event handlers."""

    def test_on_node_started_updates_visual_status(
        self, execution_controller, mock_main_window
    ) -> None:
        """Test NODE_STARTED event updates visual node status."""
        execution_controller.initialize()

        event_data = {"node_id": "node1"}
        execution_controller._on_node_started(event_data)

        # Verify visual node status updated
        mock_graph = mock_main_window.get_graph()
        mock_node = mock_graph.all_nodes()[0]
        mock_node.set_property.assert_called_with("status", "running")

    def test_on_node_completed_updates_visual_status(
        self, execution_controller, mock_main_window
    ) -> None:
        """Test NODE_COMPLETED event updates visual node status."""
        execution_controller.initialize()

        event_data = {"node_id": "node1"}
        execution_controller._on_node_completed(event_data)

        # Verify visual node status updated
        mock_graph = mock_main_window.get_graph()
        mock_node = mock_graph.all_nodes()[0]
        mock_node.set_property.assert_called_with("status", "completed")

    def test_on_node_error_updates_visual_status(
        self, execution_controller, mock_main_window
    ) -> None:
        """Test NODE_ERROR event updates visual node status."""
        execution_controller.initialize()

        event_data = {"node_id": "node1", "error": "Test error"}
        execution_controller._on_node_error(event_data)

        # Verify visual node status updated
        mock_graph = mock_main_window.get_graph()
        mock_node = mock_graph.all_nodes()[0]
        mock_node.set_property.assert_called_with("status", "error")

    def test_on_node_event_handles_missing_node(
        self, execution_controller, mock_main_window
    ) -> None:
        """Test node event handlers handle missing node gracefully."""
        execution_controller.initialize()

        event_data = {"node_id": "nonexistent"}
        # Should not raise exception
        execution_controller._on_node_started(event_data)
        execution_controller._on_node_completed(event_data)
        execution_controller._on_node_error(event_data)


class TestWorkflowEventHandlers:
    """Tests for workflow event handlers."""

    def test_on_workflow_completed_delegates_to_handler(
        self, execution_controller, mock_main_window
    ) -> None:
        """Test WORKFLOW_COMPLETED event delegates to on_execution_completed."""
        execution_controller.initialize()

        with patch.object(
            execution_controller, "on_execution_completed"
        ) as mock_handler:
            event_data = {}
            execution_controller._on_workflow_completed(event_data)

        mock_handler.assert_called_once()

    def test_on_workflow_error_delegates_to_handler(
        self, execution_controller, mock_main_window
    ) -> None:
        """Test WORKFLOW_ERROR event delegates to on_execution_error."""
        execution_controller.initialize()

        with patch.object(execution_controller, "on_execution_error") as mock_handler:
            event_data = {"error": "Test error"}
            execution_controller._on_workflow_error(event_data)

        mock_handler.assert_called_once_with("Test error")

    def test_on_workflow_stopped_updates_state(
        self, execution_controller, mock_main_window
    ) -> None:
        """Test WORKFLOW_STOPPED event updates execution state."""
        execution_controller.initialize()
        execution_controller._is_running = True
        execution_controller._is_paused = True

        event_data = {}
        execution_controller._on_workflow_stopped(event_data)

        # Verify state updated
        assert not execution_controller._is_running
        assert not execution_controller._is_paused


class TestVisualNodeOperations:
    """Tests for visual node operations."""

    def test_find_visual_node_success(
        self, execution_controller, mock_main_window
    ) -> None:
        """Test _find_visual_node finds node by ID."""
        execution_controller.initialize()

        result = execution_controller._find_visual_node("node1")

        assert result is not None
        assert result.get_property("node_id") == "node1"

    def test_find_visual_node_not_found(
        self, execution_controller, mock_main_window
    ) -> None:
        """Test _find_visual_node returns None for missing node."""
        execution_controller.initialize()

        result = execution_controller._find_visual_node("nonexistent")

        assert result is None

    def test_find_visual_node_handles_no_graph(
        self, execution_controller, mock_main_window
    ) -> None:
        """Test _find_visual_node handles missing graph gracefully."""
        mock_main_window.get_graph.return_value = None
        execution_controller.initialize()

        result = execution_controller._find_visual_node("node1")

        assert result is None

    def test_reset_all_node_visuals(
        self, execution_controller, mock_main_window
    ) -> None:
        """Test _reset_all_node_visuals resets all node statuses."""
        execution_controller.initialize()

        execution_controller._reset_all_node_visuals()

        # Verify all nodes reset to idle
        mock_graph = mock_main_window.get_graph()
        for node in mock_graph.all_nodes():
            node.set_property.assert_called_with("status", "idle")

    def test_run_workflow_resets_visuals(
        self, execution_controller, mock_main_window
    ) -> None:
        """Test run_workflow resets visual node statuses before running."""
        execution_controller.initialize()

        with patch.object(
            execution_controller, "_reset_all_node_visuals"
        ) as mock_reset:
            with patch.object(
                execution_controller, "_check_validation_before_run", return_value=True
            ):
                execution_controller.run_workflow()

        mock_reset.assert_called_once()


class TestCleanup:
    """Tests for cleanup functionality."""

    def test_cleanup_cancels_workflow_task(self, execution_controller) -> None:
        """Test cleanup cancels running workflow task."""
        execution_controller.initialize()

        # Setup mock task
        mock_task = Mock()
        mock_task.done.return_value = False
        mock_task.cancel = Mock()
        execution_controller._workflow_task = mock_task

        execution_controller.cleanup()

        mock_task.cancel.assert_called_once()
        assert execution_controller._workflow_task is None

    def test_cleanup_handles_completed_task(self, execution_controller) -> None:
        """Test cleanup handles already completed task."""
        execution_controller.initialize()

        # Setup completed task
        mock_task = Mock()
        mock_task.done.return_value = True
        execution_controller._workflow_task = mock_task

        execution_controller.cleanup()

        # Should not cancel completed task
        mock_task.cancel.assert_not_called()
