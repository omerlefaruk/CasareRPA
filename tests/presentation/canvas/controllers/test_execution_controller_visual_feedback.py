"""
Tests for ExecutionController node visual feedback changes.

Tests the updated event handlers that use update_status() instead of set_property():
- _on_node_started: Uses update_status("running")
- _on_node_completed: Uses update_status("success") + extracts duration_ms
- _on_node_error: Uses update_status("error")
- _reset_all_node_visuals: Uses update_status("idle") + clears execution time

These tests verify the fix for missing node animations and status icons during
workflow execution.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from PySide6.QtWidgets import QMainWindow

from casare_rpa.presentation.canvas.controllers.execution_controller import (
    ExecutionController,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_visual_node():
    """Create a mock visual node with update_status and update_execution_time methods."""
    node = Mock()
    node.get_property = Mock(return_value="test_node_id")
    node.update_status = Mock()
    node.update_execution_time = Mock()
    return node


@pytest.fixture
def mock_visual_node_without_methods():
    """Create a mock visual node without the new methods (legacy node)."""
    node = Mock()
    node.get_property = Mock(return_value="legacy_node_id")
    # Remove the methods to simulate legacy node
    del node.update_status
    del node.update_execution_time
    return node


@pytest.fixture
def mock_main_window_with_visual_nodes(qtbot, mock_visual_node):
    """Create a mock main window with visual nodes that have update_status method."""
    main_window = QMainWindow()
    qtbot.addWidget(main_window)

    # Mock graph with visual nodes
    mock_graph = Mock()
    mock_graph.all_nodes = Mock(return_value=[mock_visual_node])
    mock_graph.selected_nodes = Mock(return_value=[])

    main_window.get_graph = Mock(return_value=mock_graph)
    main_window.show_status = Mock()
    main_window.get_log_viewer = Mock(return_value=None)
    main_window.get_bottom_panel = Mock(return_value=None)

    # Mock signals
    main_window.workflow_run = Mock()
    main_window.workflow_run.emit = Mock()
    main_window.workflow_pause = Mock()
    main_window.workflow_pause.emit = Mock()
    main_window.workflow_resume = Mock()
    main_window.workflow_resume.emit = Mock()
    main_window.workflow_stop = Mock()
    main_window.workflow_stop.emit = Mock()

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
def execution_controller_with_visual_nodes(
    mock_main_window_with_visual_nodes, mock_visual_node
):
    """Create an ExecutionController with visual nodes indexed."""
    controller = ExecutionController(mock_main_window_with_visual_nodes)
    controller.initialize()
    # Build node index for O(1) lookups
    controller._node_index = {"test_node_id": mock_visual_node}
    return controller


# =============================================================================
# TEST CLASS: Node Started Event Handler
# =============================================================================


class TestOnNodeStartedHandler:
    """Tests for _on_node_started event handler using update_status."""

    def test_on_node_started_calls_update_status_running(
        self, execution_controller_with_visual_nodes, mock_visual_node
    ) -> None:
        """Test NODE_STARTED event calls update_status('running') instead of set_property."""
        controller = execution_controller_with_visual_nodes

        event_data = {"node_id": "test_node_id"}
        controller._on_node_started(event_data)

        mock_visual_node.update_status.assert_called_once_with("running")

    def test_on_node_started_with_event_object(
        self, execution_controller_with_visual_nodes, mock_visual_node
    ) -> None:
        """Test NODE_STARTED handles Event object with data attribute."""
        controller = execution_controller_with_visual_nodes

        # Create Event-like object
        event = Mock()
        event.data = {"node_id": "test_node_id"}
        controller._on_node_started(event)

        mock_visual_node.update_status.assert_called_once_with("running")

    def test_on_node_started_missing_node_id(
        self, execution_controller_with_visual_nodes, mock_visual_node
    ) -> None:
        """Test NODE_STARTED handles missing node_id gracefully."""
        controller = execution_controller_with_visual_nodes

        event_data = {}
        controller._on_node_started(event_data)

        mock_visual_node.update_status.assert_not_called()

    def test_on_node_started_nonexistent_node(
        self, execution_controller_with_visual_nodes, mock_visual_node
    ) -> None:
        """Test NODE_STARTED handles nonexistent node gracefully."""
        controller = execution_controller_with_visual_nodes

        event_data = {"node_id": "nonexistent_node_id"}
        controller._on_node_started(event_data)

        mock_visual_node.update_status.assert_not_called()

    def test_on_node_started_node_without_update_status(
        self, mock_main_window_with_visual_nodes
    ) -> None:
        """Test NODE_STARTED handles node without update_status method."""
        # Create node without update_status
        legacy_node = Mock()
        legacy_node.get_property = Mock(return_value="legacy_id")
        spec_attrs = ["get_property"]  # Only has get_property
        legacy_node.configure_mock(
            **{attr: getattr(legacy_node, attr) for attr in spec_attrs}
        )
        delattr(legacy_node, "update_status")

        controller = ExecutionController(mock_main_window_with_visual_nodes)
        controller.initialize()
        controller._node_index = {"legacy_id": legacy_node}

        event_data = {"node_id": "legacy_id"}
        # Should not raise exception
        controller._on_node_started(event_data)


# =============================================================================
# TEST CLASS: Node Completed Event Handler
# =============================================================================


class TestOnNodeCompletedHandler:
    """Tests for _on_node_completed event handler using update_status('success')."""

    def test_on_node_completed_calls_update_status_success(
        self, execution_controller_with_visual_nodes, mock_visual_node
    ) -> None:
        """Test NODE_COMPLETED event calls update_status('success') not 'completed'."""
        controller = execution_controller_with_visual_nodes

        event_data = {"node_id": "test_node_id"}
        controller._on_node_completed(event_data)

        mock_visual_node.update_status.assert_called_once_with("success")

    def test_on_node_completed_extracts_duration_ms(
        self, execution_controller_with_visual_nodes, mock_visual_node
    ) -> None:
        """Test NODE_COMPLETED extracts and converts duration_ms to seconds."""
        controller = execution_controller_with_visual_nodes

        event_data = {"node_id": "test_node_id", "duration_ms": 1500}
        controller._on_node_completed(event_data)

        mock_visual_node.update_status.assert_called_once_with("success")
        mock_visual_node.update_execution_time.assert_called_once_with(1.5)

    def test_on_node_completed_duration_zero(
        self, execution_controller_with_visual_nodes, mock_visual_node
    ) -> None:
        """Test NODE_COMPLETED handles duration_ms of 0."""
        controller = execution_controller_with_visual_nodes

        event_data = {"node_id": "test_node_id", "duration_ms": 0}
        controller._on_node_completed(event_data)

        mock_visual_node.update_status.assert_called_once_with("success")
        mock_visual_node.update_execution_time.assert_called_once_with(0.0)

    def test_on_node_completed_no_duration(
        self, execution_controller_with_visual_nodes, mock_visual_node
    ) -> None:
        """Test NODE_COMPLETED handles missing duration_ms."""
        controller = execution_controller_with_visual_nodes

        event_data = {"node_id": "test_node_id"}
        controller._on_node_completed(event_data)

        mock_visual_node.update_status.assert_called_once_with("success")
        mock_visual_node.update_execution_time.assert_not_called()

    def test_on_node_completed_with_event_object(
        self, execution_controller_with_visual_nodes, mock_visual_node
    ) -> None:
        """Test NODE_COMPLETED handles Event object with data attribute."""
        controller = execution_controller_with_visual_nodes

        event = Mock()
        event.data = {"node_id": "test_node_id", "duration_ms": 2500}
        controller._on_node_completed(event)

        mock_visual_node.update_status.assert_called_once_with("success")
        mock_visual_node.update_execution_time.assert_called_once_with(2.5)

    def test_on_node_completed_fractional_duration(
        self, execution_controller_with_visual_nodes, mock_visual_node
    ) -> None:
        """Test NODE_COMPLETED handles fractional duration_ms."""
        controller = execution_controller_with_visual_nodes

        event_data = {"node_id": "test_node_id", "duration_ms": 123.456}
        controller._on_node_completed(event_data)

        mock_visual_node.update_execution_time.assert_called_once_with(0.123456)

    def test_on_node_completed_large_duration(
        self, execution_controller_with_visual_nodes, mock_visual_node
    ) -> None:
        """Test NODE_COMPLETED handles large duration values (minutes)."""
        controller = execution_controller_with_visual_nodes

        event_data = {"node_id": "test_node_id", "duration_ms": 120000}  # 2 minutes
        controller._on_node_completed(event_data)

        mock_visual_node.update_execution_time.assert_called_once_with(120.0)

    def test_on_node_completed_node_without_update_execution_time(
        self, mock_main_window_with_visual_nodes
    ) -> None:
        """Test NODE_COMPLETED handles node without update_execution_time method."""
        node = Mock()
        node.get_property = Mock(return_value="test_id")
        node.update_status = Mock()
        # Remove update_execution_time
        if hasattr(node, "update_execution_time"):
            delattr(node, "update_execution_time")

        controller = ExecutionController(mock_main_window_with_visual_nodes)
        controller.initialize()
        controller._node_index = {"test_id": node}

        event_data = {"node_id": "test_id", "duration_ms": 1000}
        # Should not raise exception
        controller._on_node_completed(event_data)
        node.update_status.assert_called_once_with("success")


# =============================================================================
# TEST CLASS: Node Error Event Handler
# =============================================================================


class TestOnNodeErrorHandler:
    """Tests for _on_node_error event handler using update_status('error')."""

    def test_on_node_error_calls_update_status_error(
        self, execution_controller_with_visual_nodes, mock_visual_node
    ) -> None:
        """Test NODE_ERROR event calls update_status('error')."""
        controller = execution_controller_with_visual_nodes

        event_data = {"node_id": "test_node_id", "error": "Test error message"}
        controller._on_node_error(event_data)

        mock_visual_node.update_status.assert_called_once_with("error")

    def test_on_node_error_with_event_object(
        self, execution_controller_with_visual_nodes, mock_visual_node
    ) -> None:
        """Test NODE_ERROR handles Event object with data attribute."""
        controller = execution_controller_with_visual_nodes

        event = Mock()
        event.data = {"node_id": "test_node_id", "error": "Something went wrong"}
        controller._on_node_error(event)

        mock_visual_node.update_status.assert_called_once_with("error")

    def test_on_node_error_without_error_message(
        self, execution_controller_with_visual_nodes, mock_visual_node
    ) -> None:
        """Test NODE_ERROR handles missing error message."""
        controller = execution_controller_with_visual_nodes

        event_data = {"node_id": "test_node_id"}
        controller._on_node_error(event_data)

        mock_visual_node.update_status.assert_called_once_with("error")

    def test_on_node_error_missing_node_id(
        self, execution_controller_with_visual_nodes, mock_visual_node
    ) -> None:
        """Test NODE_ERROR handles missing node_id gracefully."""
        controller = execution_controller_with_visual_nodes

        event_data = {"error": "Error without node"}
        controller._on_node_error(event_data)

        mock_visual_node.update_status.assert_not_called()


# =============================================================================
# TEST CLASS: Reset All Node Visuals
# =============================================================================


class TestResetAllNodeVisuals:
    """Tests for _reset_all_node_visuals using update_status('idle')."""

    def test_reset_all_node_visuals_calls_update_status_idle(
        self, mock_main_window_with_visual_nodes, mock_visual_node
    ) -> None:
        """Test _reset_all_node_visuals calls update_status('idle') on all nodes."""
        controller = ExecutionController(mock_main_window_with_visual_nodes)
        controller.initialize()

        controller._reset_all_node_visuals()

        mock_visual_node.update_status.assert_called_once_with("idle")

    def test_reset_all_node_visuals_clears_execution_time(
        self, mock_main_window_with_visual_nodes, mock_visual_node
    ) -> None:
        """Test _reset_all_node_visuals clears execution time on all nodes."""
        controller = ExecutionController(mock_main_window_with_visual_nodes)
        controller.initialize()

        controller._reset_all_node_visuals()

        mock_visual_node.update_execution_time.assert_called_once_with(None)

    def test_reset_all_node_visuals_multiple_nodes(
        self, mock_main_window_with_visual_nodes
    ) -> None:
        """Test _reset_all_node_visuals resets all nodes in graph."""
        # Create multiple mock nodes
        node1 = Mock()
        node1.get_property = Mock(return_value="node1")
        node1.update_status = Mock()
        node1.update_execution_time = Mock()

        node2 = Mock()
        node2.get_property = Mock(return_value="node2")
        node2.update_status = Mock()
        node2.update_execution_time = Mock()

        node3 = Mock()
        node3.get_property = Mock(return_value="node3")
        node3.update_status = Mock()
        node3.update_execution_time = Mock()

        # Update graph to return multiple nodes
        mock_graph = mock_main_window_with_visual_nodes.get_graph()
        mock_graph.all_nodes.return_value = [node1, node2, node3]

        controller = ExecutionController(mock_main_window_with_visual_nodes)
        controller.initialize()

        controller._reset_all_node_visuals()

        # Verify all nodes were reset
        for node in [node1, node2, node3]:
            node.update_status.assert_called_once_with("idle")
            node.update_execution_time.assert_called_once_with(None)

    def test_reset_all_node_visuals_no_graph(
        self, mock_main_window_with_visual_nodes
    ) -> None:
        """Test _reset_all_node_visuals handles missing graph gracefully."""
        mock_main_window_with_visual_nodes.get_graph.return_value = None

        controller = ExecutionController(mock_main_window_with_visual_nodes)
        controller.initialize()

        # Should not raise exception
        controller._reset_all_node_visuals()

    def test_reset_all_node_visuals_node_without_methods(
        self, mock_main_window_with_visual_nodes
    ) -> None:
        """Test _reset_all_node_visuals handles nodes without new methods."""
        legacy_node = Mock(spec=[])  # Node with no methods
        mock_graph = mock_main_window_with_visual_nodes.get_graph()
        mock_graph.all_nodes.return_value = [legacy_node]

        controller = ExecutionController(mock_main_window_with_visual_nodes)
        controller.initialize()

        # Should not raise exception
        controller._reset_all_node_visuals()


# =============================================================================
# TEST CLASS: Integration Tests
# =============================================================================


class TestVisualFeedbackIntegration:
    """Integration tests for visual feedback during workflow execution."""

    def test_run_workflow_resets_visuals_before_execution(
        self, mock_main_window_with_visual_nodes, mock_visual_node
    ) -> None:
        """Test run_workflow resets visual states before starting execution."""
        # Setup validation to pass
        mock_bottom_panel = Mock()
        mock_bottom_panel.get_validation_errors_blocking = Mock(return_value=[])
        mock_main_window_with_visual_nodes.get_bottom_panel.return_value = (
            mock_bottom_panel
        )

        controller = ExecutionController(mock_main_window_with_visual_nodes)
        controller.initialize()

        # Mock workflow runner
        controller._workflow_runner = Mock()

        # Patch asyncio.create_task to avoid "no running event loop" error
        with patch("asyncio.create_task"):
            controller.run_workflow()

        # Verify visuals were reset before execution
        mock_visual_node.update_status.assert_called_with("idle")
        mock_visual_node.update_execution_time.assert_called_with(None)

    def test_node_lifecycle_happy_path(
        self, execution_controller_with_visual_nodes, mock_visual_node
    ) -> None:
        """Test complete node execution lifecycle: started -> completed."""
        controller = execution_controller_with_visual_nodes

        # Simulate node started
        controller._on_node_started({"node_id": "test_node_id"})
        assert mock_visual_node.update_status.call_args_list[-1] == call("running")

        # Simulate node completed
        controller._on_node_completed({"node_id": "test_node_id", "duration_ms": 500})
        assert mock_visual_node.update_status.call_args_list[-1] == call("success")
        mock_visual_node.update_execution_time.assert_called_with(0.5)

    def test_node_lifecycle_error_path(
        self, execution_controller_with_visual_nodes, mock_visual_node
    ) -> None:
        """Test node execution lifecycle with error: started -> error."""
        controller = execution_controller_with_visual_nodes

        # Simulate node started
        controller._on_node_started({"node_id": "test_node_id"})
        assert mock_visual_node.update_status.call_args_list[-1] == call("running")

        # Simulate node error
        controller._on_node_error({"node_id": "test_node_id", "error": "Timeout"})
        assert mock_visual_node.update_status.call_args_list[-1] == call("error")


# =============================================================================
# TEST CLASS: Edge Cases
# =============================================================================


class TestEdgeCases:
    """Edge case tests for visual feedback handlers."""

    def test_event_data_as_none(
        self, execution_controller_with_visual_nodes, mock_visual_node
    ) -> None:
        """Test handlers handle None event data gracefully."""
        controller = execution_controller_with_visual_nodes

        # These should not raise exceptions
        controller._on_node_started(None)
        controller._on_node_completed(None)
        controller._on_node_error(None)

        mock_visual_node.update_status.assert_not_called()

    def test_event_data_as_non_dict(
        self, execution_controller_with_visual_nodes, mock_visual_node
    ) -> None:
        """Test handlers handle non-dict event data gracefully."""
        controller = execution_controller_with_visual_nodes

        # These should not raise exceptions
        controller._on_node_started("invalid")
        controller._on_node_completed(123)
        controller._on_node_error([])

        mock_visual_node.update_status.assert_not_called()

    def test_duration_ms_none_value(
        self, execution_controller_with_visual_nodes, mock_visual_node
    ) -> None:
        """Test NODE_COMPLETED handles explicit None duration_ms."""
        controller = execution_controller_with_visual_nodes

        event_data = {"node_id": "test_node_id", "duration_ms": None}
        controller._on_node_completed(event_data)

        mock_visual_node.update_status.assert_called_once_with("success")
        mock_visual_node.update_execution_time.assert_not_called()

    def test_empty_node_index(self, mock_main_window_with_visual_nodes) -> None:
        """Test handlers work correctly with empty node index."""
        controller = ExecutionController(mock_main_window_with_visual_nodes)
        controller.initialize()
        controller._node_index = {}

        # Should not raise exceptions
        controller._on_node_started({"node_id": "any_id"})
        controller._on_node_completed({"node_id": "any_id"})
        controller._on_node_error({"node_id": "any_id"})

    def test_build_node_index_populates_correctly(
        self, mock_main_window_with_visual_nodes, mock_visual_node
    ) -> None:
        """Test _build_node_index creates correct node lookup."""
        controller = ExecutionController(mock_main_window_with_visual_nodes)
        controller.initialize()

        controller._build_node_index()

        assert "test_node_id" in controller._node_index
        assert controller._node_index["test_node_id"] == mock_visual_node

    def test_find_visual_node_uses_index(
        self, execution_controller_with_visual_nodes, mock_visual_node
    ) -> None:
        """Test _find_visual_node uses O(1) index lookup."""
        controller = execution_controller_with_visual_nodes

        result = controller._find_visual_node("test_node_id")

        assert result == mock_visual_node
        # Verify it used the index, not graph iteration
        controller.main_window.get_graph().all_nodes.assert_not_called()
