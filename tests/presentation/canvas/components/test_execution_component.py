"""
Comprehensive tests for ExecutionComponent.

Tests workflow execution management including:
- Running workflows
- Pausing/Resuming
- Stopping execution
- Event handling
- Visual feedback
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio

from casare_rpa.presentation.canvas.components.execution_component import (
    ExecutionComponent,
)


@pytest.fixture
def mock_main_window() -> None:
    """Create a mock MainWindow."""
    mock = Mock()
    mock.workflow_run = Mock()
    mock.workflow_run.connect = Mock()
    mock.workflow_run_to_node = Mock()
    mock.workflow_run_to_node.connect = Mock()
    mock.workflow_run_single_node = Mock()
    mock.workflow_run_single_node.connect = Mock()
    mock.workflow_pause = Mock()
    mock.workflow_pause.connect = Mock()
    mock.workflow_resume = Mock()
    mock.workflow_resume.connect = Mock()
    mock.workflow_stop = Mock()
    mock.workflow_stop.connect = Mock()

    mock.action_run = Mock()
    mock.action_run.setEnabled = Mock()
    mock.action_pause = Mock()
    mock.action_pause.setEnabled = Mock()
    mock.action_stop = Mock()
    mock.action_stop.setEnabled = Mock()

    mock.get_debug_toolbar = Mock(return_value=None)
    mock.get_log_viewer = Mock(return_value=None)
    mock.get_variables_panel = Mock(return_value=None)

    mock_status = Mock()
    mock.statusBar = Mock(return_value=mock_status)

    return mock


@pytest.fixture
def mock_node_graph() -> None:
    """Create a mock node graph."""
    mock = Mock()
    mock.graph = Mock()
    mock.graph.all_nodes = Mock(return_value=[])
    return mock


@pytest.fixture
def execution_component(mock_main_window, mock_node_graph) -> None:
    """Create an ExecutionComponent instance."""
    component = ExecutionComponent(mock_main_window)
    component._node_graph = mock_node_graph
    component.initialize()
    return component


class TestExecutionComponentInitialization:
    """Tests for component initialization."""

    def test_initialization(self, mock_main_window, mock_node_graph) -> None:
        """Test component initializes."""
        component = ExecutionComponent(mock_main_window)
        component._node_graph = mock_node_graph

        component.initialize()

        assert component.is_initialized()
        assert component._workflow_runner is None

    def test_cleanup(self, execution_component) -> None:
        """Test cleanup."""
        execution_component._workflow_task = Mock()
        execution_component._workflow_task.done = Mock(return_value=True)

        execution_component.cleanup()

        # Should not raise errors


class TestRunWorkflow:
    """Tests for running workflow."""

    @patch("casare_rpa.canvas.components.execution_component.WorkflowRunner")
    @patch("casare_rpa.canvas.components.execution_component.get_project_manager")
    @patch("casare_rpa.canvas.components.execution_component.asyncio.ensure_future")
    def test_on_run_workflow(
        self, mock_ensure_future, mock_pm, mock_runner_class, execution_component
    ) -> None:
        """Test running workflow."""
        mock_runner = Mock()
        mock_runner.state = "idle"
        mock_runner_class.return_value = mock_runner

        mock_pm_instance = Mock()
        mock_pm_instance.current_project = None
        mock_pm.return_value = mock_pm_instance

        with patch.object(execution_component, "_reset_all_node_visuals"):
            with patch.object(
                execution_component, "_create_workflow_from_graph", return_value=Mock()
            ):
                with patch.object(
                    execution_component, "_get_initial_variables", return_value={}
                ):
                    execution_component.on_run_workflow()

        # Should create workflow runner
        assert execution_component._workflow_runner is not None
        mock_ensure_future.assert_called_once()


class TestPauseResume:
    """Tests for pause and resume."""

    def test_on_pause_workflow(self, execution_component, mock_main_window) -> None:
        """Test pausing workflow."""
        mock_runner = Mock()
        execution_component._workflow_runner = mock_runner

        execution_component.on_pause_workflow()

        mock_runner.pause.assert_called_once()
        mock_main_window.statusBar().showMessage.assert_called()

    def test_on_pause_workflow_no_runner(self, execution_component) -> None:
        """Test pausing when no runner."""
        execution_component._workflow_runner = None

        # Should not raise error
        execution_component.on_pause_workflow()

    def test_on_resume_workflow(self, execution_component, mock_main_window) -> None:
        """Test resuming workflow."""
        mock_runner = Mock()
        execution_component._workflow_runner = mock_runner

        execution_component.on_resume_workflow()

        mock_runner.resume.assert_called_once()


class TestStopWorkflow:
    """Tests for stopping workflow."""

    def test_on_stop_workflow(self, execution_component, mock_main_window) -> None:
        """Test stopping workflow."""
        mock_runner = Mock()
        mock_task = Mock()
        mock_task.done.return_value = False
        execution_component._workflow_runner = mock_runner
        execution_component._workflow_task = mock_task

        execution_component.on_stop_workflow()

        mock_runner.stop.assert_called_once()
        mock_task.cancel.assert_called_once()


class TestEventHandlers:
    """Tests for event handling."""

    def test_on_node_started(self, execution_component, mock_node_graph) -> None:
        """Test handling node started event."""
        mock_node = Mock()
        mock_node.get_property.return_value = "node1"
        mock_node_graph.graph.all_nodes.return_value = [mock_node]

        execution_component._on_node_started({"node_id": "node1"})

        mock_node.set_property.assert_called_with("status", "running")

    def test_on_node_completed(self, execution_component, mock_node_graph) -> None:
        """Test handling node completed event."""
        mock_node = Mock()
        mock_node.get_property.return_value = "node1"
        mock_node_graph.graph.all_nodes.return_value = [mock_node]

        execution_component._on_node_completed({"node_id": "node1"})

        mock_node.set_property.assert_called_with("status", "completed")

    def test_on_node_error(self, execution_component, mock_node_graph) -> None:
        """Test handling node error event."""
        mock_node = Mock()
        mock_node.get_property.return_value = "node1"
        mock_node_graph.graph.all_nodes.return_value = [mock_node]

        execution_component._on_node_error({"node_id": "node1", "error": "Test error"})

        mock_node.set_property.assert_called_with("status", "error")

    def test_on_workflow_completed(self, execution_component, mock_main_window) -> None:
        """Test handling workflow completed event."""
        execution_component._on_workflow_completed({})

        mock_main_window.statusBar().showMessage.assert_called()

    def test_on_workflow_error(self, execution_component, mock_main_window) -> None:
        """Test handling workflow error event."""
        execution_component._on_workflow_error({"error": "Test error"})

        mock_main_window.statusBar().showMessage.assert_called()


class TestPrivateMethods:
    """Tests for private helper methods."""

    def test_reset_all_node_visuals(self, execution_component, mock_node_graph) -> None:
        """Test resetting node visuals."""
        mock_node = Mock()
        mock_node_graph.graph.all_nodes.return_value = [mock_node]

        execution_component._reset_all_node_visuals()

        mock_node.set_property.assert_called_with("status", "idle")

    def test_find_visual_node(self, execution_component, mock_node_graph) -> None:
        """Test finding visual node by ID."""
        mock_node = Mock()
        mock_node.get_property.return_value = "test_node"
        mock_node_graph.graph.all_nodes.return_value = [mock_node]

        result = execution_component._find_visual_node("test_node")

        assert result == mock_node

    def test_find_visual_node_not_found(
        self, execution_component, mock_node_graph
    ) -> None:
        """Test finding non-existent visual node."""
        mock_node_graph.graph.all_nodes.return_value = []

        result = execution_component._find_visual_node("nonexistent")

        assert result is None

    def test_get_initial_variables(self, execution_component, mock_main_window) -> None:
        """Test getting initial variables."""
        mock_panel = Mock()
        mock_panel.get_all_variables.return_value = {"var1": "value1"}
        mock_main_window.get_variables_panel.return_value = mock_panel

        result = execution_component._get_initial_variables()

        assert result == {"var1": "value1"}

    def test_get_initial_variables_no_panel(
        self, execution_component, mock_main_window
    ) -> None:
        """Test getting initial variables when no panel."""
        mock_main_window.get_variables_panel.return_value = None

        result = execution_component._get_initial_variables()

        assert result == {}
