"""
Tests for WorkflowController drag-drop functionality.

Tests drag-drop import operations:
- File drop handling
- JSON data drop handling
- Drag-drop setup
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from PySide6.QtWidgets import QMainWindow

from casare_rpa.presentation.canvas.controllers.workflow_controller import (
    WorkflowController,
)


@pytest.fixture
def mock_main_window(qtbot):
    """Create a mock main window with graph support."""
    main_window = QMainWindow()
    qtbot.addWidget(main_window)

    # Mock graph with drag-drop support
    mock_graph = Mock()
    mock_graph.set_import_file_callback = Mock()
    mock_graph.set_import_callback = Mock()
    mock_graph.setup_drag_drop = Mock()

    main_window.get_graph = Mock(return_value=mock_graph)
    main_window.show_status = Mock()
    main_window.set_modified = Mock()

    return main_window


@pytest.fixture
def workflow_controller(mock_main_window):
    """Create a WorkflowController instance."""
    controller = WorkflowController(mock_main_window)
    return controller


class TestDragDropSetup:
    """Tests for drag-drop setup functionality."""

    def test_setup_drag_drop_import_success(
        self, workflow_controller, mock_main_window
    ) -> None:
        """Test drag-drop import setup succeeds with graph support."""
        workflow_controller.setup_drag_drop_import()

        # Verify callbacks were set
        mock_graph = mock_main_window.get_graph()
        mock_graph.set_import_file_callback.assert_called_once()
        mock_graph.set_import_callback.assert_called_once()
        mock_graph.setup_drag_drop.assert_called_once()

    def test_setup_drag_drop_without_graph(
        self, workflow_controller, mock_main_window
    ) -> None:
        """Test drag-drop setup handles missing graph gracefully."""
        mock_main_window.get_graph.return_value = None

        workflow_controller.setup_drag_drop_import()

        # Should not raise exception

    def test_setup_drag_drop_without_support(
        self, workflow_controller, mock_main_window
    ) -> None:
        """Test drag-drop setup handles graph without drag-drop support."""
        mock_graph = Mock(spec=[])  # Empty spec - no methods
        mock_main_window.get_graph.return_value = mock_graph

        workflow_controller.setup_drag_drop_import()

        # Should not raise exception


class TestFileDropHandling:
    """Tests for file drop callback."""

    @patch("pathlib.Path.read_bytes")
    @patch("orjson.loads")
    def test_file_drop_callback_success(
        self,
        mock_json_loads,
        mock_read_bytes,
        workflow_controller,
        mock_main_window,
        tmp_path,
    ) -> None:
        """Test file drop callback handles valid JSON file."""
        # Setup mocks
        test_file = tmp_path / "workflow.json"
        test_file.touch()

        mock_json_loads.return_value = {
            "nodes": {
                "node1": {"node_type": "BrowserNavigate", "config": {}},
                "node2": {"node_type": "BrowserClick", "config": {}},
            }
        }
        mock_read_bytes.return_value = b'{"nodes": {}}'

        # Setup drag-drop
        workflow_controller.setup_drag_drop_import()

        # Get the callback that was registered
        mock_graph = mock_main_window.get_graph()
        file_callback = mock_graph.set_import_file_callback.call_args[0][0]

        # Trigger file drop
        signal_emitted = []
        workflow_controller.workflow_imported.connect(
            lambda _: signal_emitted.append(True)
        )

        file_callback(str(test_file), (100, 100))

        # Verify signal emitted
        assert len(signal_emitted) == 1
        mock_main_window.set_modified.assert_called_with(True)
        mock_main_window.show_status.assert_called()

    @patch("pathlib.Path.read_bytes")
    def test_file_drop_callback_invalid_json(
        self, mock_read_bytes, workflow_controller, mock_main_window, tmp_path
    ) -> None:
        """Test file drop callback handles invalid JSON gracefully."""
        test_file = tmp_path / "invalid.json"
        test_file.touch()

        mock_read_bytes.side_effect = ValueError("Invalid JSON")

        # Setup drag-drop
        workflow_controller.setup_drag_drop_import()

        # Get the callback
        mock_graph = mock_main_window.get_graph()
        file_callback = mock_graph.set_import_file_callback.call_args[0][0]

        # Trigger file drop
        file_callback(str(test_file), (100, 100))

        # Should show error status
        assert any(
            "Error" in str(call) for call in mock_main_window.show_status.call_args_list
        )


class TestDataDropHandling:
    """Tests for JSON data drop callback."""

    @patch("orjson.dumps")
    def test_data_drop_callback_success(
        self, mock_dumps, workflow_controller, mock_main_window
    ) -> None:
        """Test JSON data drop callback handles valid data."""
        test_data = {
            "nodes": {
                "node1": {"node_type": "BrowserNavigate", "config": {}},
            }
        }
        mock_dumps.return_value = b'{"nodes": {}}'

        # Setup drag-drop
        workflow_controller.setup_drag_drop_import()

        # Get the callback
        mock_graph = mock_main_window.get_graph()
        data_callback = mock_graph.set_import_callback.call_args[0][0]

        # Trigger data drop
        signal_emitted = []
        workflow_controller.workflow_imported_json.connect(
            lambda _: signal_emitted.append(True)
        )

        data_callback(test_data, (200, 200))

        # Verify signal emitted
        assert len(signal_emitted) == 1
        mock_main_window.set_modified.assert_called_with(True)
        mock_main_window.show_status.assert_called()

    def test_data_drop_callback_invalid_data(
        self, workflow_controller, mock_main_window
    ) -> None:
        """Test JSON data drop callback handles invalid data gracefully."""
        # Setup drag-drop
        workflow_controller.setup_drag_drop_import()

        # Get the callback
        mock_graph = mock_main_window.get_graph()
        data_callback = mock_graph.set_import_callback.call_args[0][0]

        # Trigger data drop with invalid data
        with patch("orjson.dumps", side_effect=TypeError("Invalid data")):
            data_callback({"invalid": object()}, (200, 200))

        # Should show error status
        assert any(
            "Error" in str(call) for call in mock_main_window.show_status.call_args_list
        )


class TestInitializeCallsDragDrop:
    """Test that initialize() sets up drag-drop."""

    def test_initialize_calls_setup_drag_drop(
        self, workflow_controller, mock_main_window
    ) -> None:
        """Test that initialize() calls setup_drag_drop_import()."""
        with patch.object(workflow_controller, "setup_drag_drop_import") as mock_setup:
            workflow_controller.initialize()

        mock_setup.assert_called_once()
