"""
Comprehensive tests for WorkflowLifecycleComponent.

Tests workflow lifecycle operations including:
- New workflow creation
- Opening workflows
- Saving workflows
- Import/export
- Graph serialization/deserialization
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import asyncio

from casare_rpa.presentation.canvas.components.workflow_lifecycle_component import (
    WorkflowLifecycleComponent,
)


@pytest.fixture
def mock_main_window() -> None:
    """Create a mock MainWindow."""
    mock = Mock()
    mock.workflow_new = Mock()
    mock.workflow_new.connect = Mock()
    mock.workflow_new_from_template = Mock()
    mock.workflow_new_from_template.connect = Mock()
    mock.workflow_open = Mock()
    mock.workflow_open.connect = Mock()
    mock.workflow_import = Mock()
    mock.workflow_import.connect = Mock()
    mock.workflow_import_json = Mock()
    mock.workflow_import_json.connect = Mock()
    mock.workflow_export_selected = Mock()
    mock.workflow_export_selected.connect = Mock()
    mock.workflow_save = Mock()
    mock.workflow_save.connect = Mock()
    mock.workflow_save_as = Mock()
    mock.workflow_save_as.connect = Mock()

    mock.set_modified = Mock()
    mock.get_current_file = Mock(return_value=None)

    mock_status = Mock()
    mock.statusBar = Mock(return_value=mock_status)

    mock._central_widget = Mock()
    mock._central_widget.graph = Mock()

    return mock


@pytest.fixture
def mock_node_graph() -> None:
    """Create a mock node graph widget."""
    mock = Mock()
    mock.graph = Mock()
    mock.graph.clear_graph = Mock()
    mock.graph.clear_session = Mock()
    mock.graph.all_nodes = Mock(return_value=[])
    mock.graph.selected_nodes = Mock(return_value=[])
    mock.graph.create_node = Mock()
    return mock


@pytest.fixture
def workflow_component(mock_main_window, mock_node_graph) -> None:
    """Create a WorkflowLifecycleComponent instance."""
    component = WorkflowLifecycleComponent(mock_main_window)
    component._node_graph = mock_node_graph
    component.initialize()
    return component


class TestWorkflowLifecycleComponentInitialization:
    """Tests for component initialization."""

    def test_initialization(self, mock_main_window, mock_node_graph) -> None:
        """Test component initializes."""
        component = WorkflowLifecycleComponent(mock_main_window)
        component._node_graph = mock_node_graph

        component.initialize()

        assert component.is_initialized()
        # Verify signals were connected
        mock_main_window.workflow_new.connect.assert_called_once()

    def test_cleanup(self, workflow_component) -> None:
        """Test cleanup."""
        workflow_component.cleanup()
        # Should not raise errors


class TestNewWorkflow:
    """Tests for new workflow creation."""

    def test_on_new_workflow(
        self, workflow_component, mock_main_window, mock_node_graph
    ) -> None:
        """Test creating new workflow."""
        workflow_component.on_new_workflow()

        mock_node_graph.graph.clear_graph.assert_called_once()
        mock_main_window.set_modified.assert_called_with(False)

    @patch("asyncio.create_task")
    def test_on_new_from_template(self, mock_create_task, workflow_component) -> None:
        """Test creating workflow from template."""
        mock_template = Mock()
        mock_template.name = "Test Template"

        workflow_component.on_new_from_template(mock_template)

        # Should create async task
        mock_create_task.assert_called_once()


class TestOpenWorkflow:
    """Tests for opening workflows."""

    @patch("casare_rpa.canvas.components.workflow_lifecycle_component.WorkflowSchema")
    def test_on_open_workflow_success(
        self, mock_schema_class, workflow_component, mock_main_window, tmp_path
    ) -> None:
        """Test opening workflow successfully."""
        test_file = tmp_path / "test.json"
        test_file.write_text('{"nodes": {}, "connections": []}')

        mock_workflow = Mock()
        mock_schema_class.load_from_file.return_value = mock_workflow

        with patch.object(workflow_component, "_load_workflow_to_graph"):
            workflow_component.on_open_workflow(str(test_file))

        mock_main_window.set_modified.assert_called_with(False)
        mock_main_window.statusBar().showMessage.assert_called()

    @patch("casare_rpa.canvas.components.workflow_lifecycle_component.WorkflowSchema")
    def test_on_open_workflow_error(
        self, mock_schema_class, workflow_component, mock_main_window
    ) -> None:
        """Test opening workflow with error."""
        mock_schema_class.load_from_file.side_effect = Exception("Load error")

        workflow_component.on_open_workflow("/nonexistent/file.json")

        # Should show error message
        mock_main_window.statusBar().showMessage.assert_called()


class TestSaveWorkflow:
    """Tests for saving workflows."""

    @patch("casare_rpa.canvas.components.workflow_lifecycle_component.WorkflowSchema")
    def test_on_save_workflow_success(
        self, mock_schema_class, workflow_component, mock_main_window, tmp_path
    ) -> None:
        """Test saving workflow successfully."""
        test_file = tmp_path / "save.json"
        mock_main_window.get_current_file.return_value = test_file

        mock_workflow = Mock()

        with patch.object(workflow_component, "_ensure_all_nodes_have_casare_nodes"):
            with patch.object(
                workflow_component,
                "_create_workflow_from_graph",
                return_value=mock_workflow,
            ):
                with patch.object(workflow_component, "_save_workflow_to_file"):
                    workflow_component.on_save_workflow()

        mock_main_window.set_modified.assert_called_with(False)
        mock_main_window.statusBar().showMessage.assert_called()

    def test_on_save_workflow_error(
        self, workflow_component, mock_main_window, tmp_path
    ) -> None:
        """Test saving workflow with error."""
        test_file = tmp_path / "error.json"
        mock_main_window.get_current_file.return_value = test_file

        with patch.object(
            workflow_component,
            "_create_workflow_from_graph",
            side_effect=Exception("Save error"),
        ):
            workflow_component.on_save_workflow()

        # Should show error message
        mock_main_window.statusBar().showMessage.assert_called()


class TestSaveAsWorkflow:
    """Tests for save as workflow."""

    @patch("casare_rpa.canvas.components.workflow_lifecycle_component.WorkflowSchema")
    def test_on_save_as_workflow(
        self, mock_schema_class, workflow_component, mock_main_window, tmp_path
    ) -> None:
        """Test save as workflow."""
        test_file = tmp_path / "saveas.json"
        mock_workflow = Mock()

        with patch.object(workflow_component, "_ensure_all_nodes_have_casare_nodes"):
            with patch.object(
                workflow_component,
                "_create_workflow_from_graph",
                return_value=mock_workflow,
            ):
                with patch.object(workflow_component, "_save_workflow_to_file"):
                    workflow_component.on_save_as_workflow(str(test_file))

        mock_main_window.set_modified.assert_called_with(False)


class TestImportWorkflow:
    """Tests for importing workflows."""

    @patch("casare_rpa.canvas.components.workflow_lifecycle_component.WorkflowSchema")
    def test_on_import_workflow(
        self, mock_schema_class, workflow_component, mock_main_window, tmp_path
    ) -> None:
        """Test importing workflow."""
        test_file = tmp_path / "import.json"
        test_file.write_text('{"nodes": {}, "connections": []}')

        mock_workflow = Mock()
        mock_schema_class.load_from_file.return_value = mock_workflow

        with patch.object(workflow_component, "_import_workflow_merge"):
            workflow_component.on_import_workflow(str(test_file))

        mock_main_window.set_modified.assert_called_with(True)

    @patch("casare_rpa.canvas.components.workflow_lifecycle_component.orjson")
    @patch("casare_rpa.canvas.components.workflow_lifecycle_component.WorkflowSchema")
    def test_on_import_workflow_json(
        self, mock_schema_class, mock_orjson, workflow_component, mock_main_window
    ) -> None:
        """Test importing workflow from JSON string."""
        json_str = '{"nodes": {}, "connections": []}'
        mock_workflow = Mock()
        mock_schema_class.from_dict.return_value = mock_workflow
        mock_orjson.loads.return_value = {}

        with patch.object(workflow_component, "_import_workflow_merge"):
            workflow_component.on_import_workflow_json(json_str)

        mock_main_window.set_modified.assert_called_with(True)


class TestExportSelectedNodes:
    """Tests for exporting selected nodes."""

    def test_on_export_selected_no_nodes(
        self, workflow_component, mock_main_window, mock_node_graph
    ) -> None:
        """Test export with no nodes selected."""
        mock_node_graph.graph.selected_nodes.return_value = []

        workflow_component.on_export_selected("/test/export.json")

        mock_main_window.statusBar().showMessage.assert_called_with(
            "No nodes selected", 3000
        )

    @patch("casare_rpa.canvas.components.workflow_lifecycle_component.WorkflowSchema")
    def test_on_export_selected_success(
        self,
        mock_schema_class,
        workflow_component,
        mock_main_window,
        mock_node_graph,
        tmp_path,
    ) -> None:
        """Test exporting selected nodes successfully."""
        mock_node1 = Mock()
        mock_node2 = Mock()
        mock_node_graph.graph.selected_nodes.return_value = [mock_node1, mock_node2]

        test_file = tmp_path / "export.json"

        with patch.object(workflow_component, "_create_workflow_from_selected_nodes"):
            with patch.object(workflow_component, "_save_workflow_to_file"):
                workflow_component.on_export_selected(str(test_file))

        # Should show success message
        mock_main_window.statusBar().showMessage.assert_called()


class TestPrivateMethods:
    """Tests for private helper methods."""

    @patch(
        "casare_rpa.canvas.components.workflow_lifecycle_component.get_identifier_for_type"
    )
    @patch(
        "casare_rpa.canvas.components.workflow_lifecycle_component.get_casare_class_for_type"
    )
    def test_load_workflow_to_graph(
        self, mock_get_class, mock_get_id, workflow_component, mock_node_graph
    ) -> None:
        """Test loading workflow to graph."""
        mock_get_id.return_value = "casare.nodes.StartNode"
        mock_get_class.return_value = Mock

        mock_workflow = Mock()
        mock_workflow.nodes = {
            "node1": {
                "node_type": "StartNode",
                "config": {},
                "position": {"x": 100, "y": 200},
            }
        }
        mock_workflow.connections = []
        mock_workflow.frames = []
        mock_workflow.metadata = Mock()
        mock_workflow.metadata.name = "Test Workflow"

        mock_visual_node = Mock()
        mock_visual_node.widgets.return_value = {}
        mock_visual_node.input_ports.return_value = []
        mock_visual_node.output_ports.return_value = []
        mock_node_graph.graph.create_node.return_value = mock_visual_node

        with patch(
            "casare_rpa.canvas.components.workflow_lifecycle_component.QApplication"
        ):
            workflow_component._load_workflow_to_graph(mock_workflow)

        mock_node_graph.graph.clear_session.assert_called_once()
        mock_node_graph.graph.create_node.assert_called_once()

    def test_create_workflow_from_graph(self, workflow_component) -> None:
        """Test creating workflow from graph."""
        with patch(
            "casare_rpa.canvas.components.workflow_lifecycle_component.get_node_factory"
        ) as mock_factory:
            mock_factory_instance = Mock()
            mock_factory.return_value = mock_factory_instance
            mock_factory_instance.create_workflow_from_graph.return_value = Mock()

            result = workflow_component._create_workflow_from_graph()

            assert result is not None
            mock_factory_instance.create_workflow_from_graph.assert_called_once()

    def test_ensure_all_nodes_have_casare_nodes(
        self, workflow_component, mock_node_graph
    ) -> None:
        """Test ensuring all nodes have casare nodes."""
        mock_visual_node = Mock()
        mock_visual_node.get_casare_node.return_value = None
        mock_visual_node.type_ = "StartNode"
        mock_visual_node.get_property.return_value = "node1"
        mock_node_graph.graph.all_nodes.return_value = [mock_visual_node]

        with patch(
            "casare_rpa.canvas.components.workflow_lifecycle_component.get_casare_class_for_type"
        ) as mock_get_class:
            mock_get_class.return_value = None

            # Should not raise error
            workflow_component._ensure_all_nodes_have_casare_nodes()
