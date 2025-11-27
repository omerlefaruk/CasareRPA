"""
Comprehensive tests for NodeController.

Tests node operations including:
- Node selection
- Node enable/disable
- Node navigation
- Node search
- Property updates
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from PySide6.QtCore import QPointF
from PySide6.QtGui import QCursor

from casare_rpa.presentation.canvas.controllers.node_controller import NodeController


@pytest.fixture
def mock_main_window():
    """Create a mock MainWindow with all required attributes."""
    mock = Mock()
    mock._central_widget = Mock()
    mock._central_widget.graph = Mock()
    mock_status = Mock()
    mock.statusBar = Mock(return_value=mock_status)
    return mock


@pytest.fixture
def node_controller(mock_main_window):
    """Create a NodeController instance."""
    controller = NodeController(mock_main_window)
    controller.initialize()
    return controller


@pytest.fixture
def mock_node():
    """Create a mock visual node."""
    node = Mock()
    node.get_property = Mock(return_value="test_node_id")
    node.name = Mock(return_value="Test Node")
    node.pos = Mock(return_value=(100, 200))
    node.set_selected = Mock()
    node.get_casare_node = Mock()
    node.view = Mock()
    node.view.setOpacity = Mock()
    return node


class TestNodeControllerInitialization:
    """Tests for NodeController initialization."""

    def test_initialization_success(self, mock_main_window):
        """Test controller initializes correctly."""
        controller = NodeController(mock_main_window)
        assert controller.main_window == mock_main_window

    def test_initialize_sets_state(self, node_controller):
        """Test initialize() sets initialized state."""
        assert node_controller.is_initialized()

    def test_cleanup_resets_state(self, node_controller):
        """Test cleanup() resets initialized state."""
        node_controller.cleanup()
        assert not node_controller.is_initialized()


class TestSelectNearestNode:
    """Tests for selecting nearest node to mouse."""

    def test_select_nearest_node_no_graph(self, node_controller, mock_main_window):
        """Test select nearest node when no graph available."""
        mock_main_window._central_widget.graph = None

        node_controller.select_nearest_node()

        # Should return early without error

    def test_select_nearest_node_no_nodes(self, node_controller, mock_main_window):
        """Test select nearest node when no nodes in graph."""
        mock_graph = mock_main_window._central_widget.graph
        mock_graph.all_nodes.return_value = []
        mock_graph.viewer.return_value = Mock()

        node_controller.select_nearest_node()

        mock_main_window.statusBar().showMessage.assert_called_with(
            "No nodes in graph", 2000
        )

    @patch("casare_rpa.presentation.canvas.controllers.node_controller.QCursor")
    def test_select_nearest_node_success(
        self, mock_cursor, node_controller, mock_main_window, mock_node
    ):
        """Test selecting nearest node successfully."""
        mock_graph = mock_main_window._central_widget.graph
        mock_viewer = Mock()
        mock_graph.viewer.return_value = mock_viewer
        mock_graph.all_nodes.return_value = [mock_node]
        mock_graph.clear_selection = Mock()

        # Mock cursor and viewer positioning
        mock_cursor.pos.return_value = Mock()
        mock_viewer.mapFromGlobal.return_value = Mock()
        scene_pos = Mock()
        scene_pos.x.return_value = 100
        scene_pos.y.return_value = 200
        mock_viewer.mapToScene.return_value = scene_pos

        signal_emitted = []
        node_controller.node_selected.connect(lambda nid: signal_emitted.append(nid))

        node_controller.select_nearest_node()

        mock_graph.clear_selection.assert_called_once()
        mock_node.set_selected.assert_called_once_with(True)
        assert len(signal_emitted) == 1
        assert signal_emitted[0] == "test_node_id"


class TestToggleDisableNode:
    """Tests for toggling node disable state."""

    def test_toggle_disable_no_graph(self, node_controller, mock_main_window):
        """Test toggle disable when no graph available."""
        mock_main_window._central_widget.graph = None

        node_controller.toggle_disable_node()

        # Should return early without error

    def test_toggle_disable_no_nodes(self, node_controller, mock_main_window):
        """Test toggle disable when no nodes in graph."""
        mock_graph = mock_main_window._central_widget.graph
        mock_graph.all_nodes.return_value = []
        mock_graph.viewer.return_value = Mock()

        node_controller.toggle_disable_node()

        mock_main_window.statusBar().showMessage.assert_called()

    @patch("casare_rpa.presentation.canvas.controllers.node_controller.QCursor")
    def test_toggle_disable_to_disabled(
        self, mock_cursor, node_controller, mock_main_window, mock_node
    ):
        """Test toggling node from enabled to disabled."""
        mock_casare_node = Mock()
        mock_casare_node.config = {"_disabled": False}
        mock_node.get_casare_node.return_value = mock_casare_node

        mock_graph = mock_main_window._central_widget.graph
        mock_viewer = Mock()
        mock_graph.viewer.return_value = mock_viewer
        mock_graph.all_nodes.return_value = [mock_node]
        mock_graph.clear_selection = Mock()

        # Mock cursor positioning
        mock_cursor.pos.return_value = Mock()
        mock_viewer.mapFromGlobal.return_value = Mock()
        scene_pos = Mock()
        scene_pos.x.return_value = 100
        scene_pos.y.return_value = 200
        mock_viewer.mapToScene.return_value = scene_pos

        signal_emitted = []
        node_controller.node_disabled.connect(lambda nid: signal_emitted.append(nid))

        node_controller.toggle_disable_node()

        assert mock_casare_node.config["_disabled"] is True
        mock_node.view.setOpacity.assert_called_with(0.4)
        assert len(signal_emitted) == 1

    @patch("casare_rpa.presentation.canvas.controllers.node_controller.QCursor")
    def test_toggle_disable_to_enabled(
        self, mock_cursor, node_controller, mock_main_window, mock_node
    ):
        """Test toggling node from disabled to enabled."""
        mock_casare_node = Mock()
        mock_casare_node.config = {"_disabled": True}
        mock_node.get_casare_node.return_value = mock_casare_node

        mock_graph = mock_main_window._central_widget.graph
        mock_viewer = Mock()
        mock_graph.viewer.return_value = mock_viewer
        mock_graph.all_nodes.return_value = [mock_node]
        mock_graph.clear_selection = Mock()

        # Mock cursor positioning
        mock_cursor.pos.return_value = Mock()
        mock_viewer.mapFromGlobal.return_value = Mock()
        scene_pos = Mock()
        scene_pos.x.return_value = 100
        scene_pos.y.return_value = 200
        mock_viewer.mapToScene.return_value = scene_pos

        signal_emitted = []
        node_controller.node_enabled.connect(lambda nid: signal_emitted.append(nid))

        node_controller.toggle_disable_node()

        assert mock_casare_node.config["_disabled"] is False
        mock_node.view.setOpacity.assert_called_with(1.0)
        assert len(signal_emitted) == 1


class TestNavigateToNode:
    """Tests for navigating to specific node."""

    def test_navigate_to_node_no_graph(self, node_controller, mock_main_window):
        """Test navigate to node when no graph available."""
        mock_main_window._central_widget.graph = None

        node_controller.navigate_to_node("test_id")

        # Should return early without error

    def test_navigate_to_node_not_found(self, node_controller, mock_main_window):
        """Test navigate to node when node doesn't exist."""
        mock_graph = mock_main_window._central_widget.graph
        mock_graph.all_nodes.return_value = []

        node_controller.navigate_to_node("nonexistent_id")

        # Should log warning but not crash

    def test_navigate_to_node_success(
        self, node_controller, mock_main_window, mock_node
    ):
        """Test navigating to node successfully."""
        mock_graph = mock_main_window._central_widget.graph
        mock_viewer = Mock()
        mock_viewer.center_on = Mock()
        mock_graph.viewer.return_value = mock_viewer
        mock_graph.all_nodes.return_value = [mock_node]
        mock_graph.clear_selection = Mock()

        signal_emitted = []
        node_controller.node_navigated.connect(lambda nid: signal_emitted.append(nid))

        node_controller.navigate_to_node("test_node_id")

        mock_graph.clear_selection.assert_called_once()
        mock_node.set_selected.assert_called_once_with(True)
        mock_viewer.center_on.assert_called_once_with([mock_node])
        assert len(signal_emitted) == 1
        assert signal_emitted[0] == "test_node_id"


class TestFindNode:
    """Tests for node search dialog."""

    @patch(
        "casare_rpa.presentation.canvas.controllers.node_controller.NodeSearchDialog"
    )
    def test_find_node_success(
        self, mock_dialog_class, node_controller, mock_main_window
    ):
        """Test opening node search dialog."""
        mock_graph = mock_main_window._central_widget.graph
        mock_dialog = Mock()
        mock_dialog_class.return_value = mock_dialog

        node_controller.find_node()

        mock_dialog_class.assert_called_once_with(mock_graph, mock_main_window)
        mock_dialog.show_search.assert_called_once()

    def test_find_node_no_graph(self, node_controller, mock_main_window):
        """Test find node when no graph available."""
        mock_main_window._central_widget.graph = None

        node_controller.find_node()

        mock_main_window.statusBar().showMessage.assert_called_with(
            "No graph available", 3000
        )


class TestUpdateNodeProperty:
    """Tests for updating node properties."""

    def test_update_node_property_success(
        self, node_controller, mock_main_window, mock_node
    ):
        """Test updating node property successfully."""
        mock_node.set_property = Mock()
        mock_graph = mock_main_window._central_widget.graph
        mock_graph.all_nodes.return_value = [mock_node]

        signal_emitted = []
        node_controller.node_property_changed.connect(
            lambda nid, prop, val: signal_emitted.append((nid, prop, val))
        )

        node_controller.update_node_property("test_node_id", "test_prop", "test_value")

        mock_node.set_property.assert_called_once_with("test_prop", "test_value")
        assert len(signal_emitted) == 1
        assert signal_emitted[0] == ("test_node_id", "test_prop", "test_value")

    def test_update_node_property_not_found(self, node_controller, mock_main_window):
        """Test updating property on non-existent node."""
        mock_graph = mock_main_window._central_widget.graph
        mock_graph.all_nodes.return_value = []

        node_controller.update_node_property("nonexistent_id", "prop", "value")

        # Should log warning but not crash

    def test_update_node_property_no_graph(self, node_controller, mock_main_window):
        """Test updating property when no graph available."""
        mock_main_window._central_widget.graph = None

        node_controller.update_node_property("node_id", "prop", "value")

        # Should return early without error


class TestPrivateMethods:
    """Tests for private helper methods."""

    def test_get_graph_success(self, node_controller, mock_main_window):
        """Test _get_graph returns graph successfully."""
        expected_graph = mock_main_window._central_widget.graph

        result = node_controller._get_graph()

        assert result == expected_graph

    def test_get_graph_no_central_widget(self, node_controller, mock_main_window):
        """Test _get_graph returns None when no central widget."""
        mock_main_window._central_widget = None

        result = node_controller._get_graph()

        assert result is None

    def test_get_graph_no_graph_attribute(self, node_controller, mock_main_window):
        """Test _get_graph returns None when central widget has no graph."""
        del mock_main_window._central_widget.graph

        result = node_controller._get_graph()

        assert result is None
