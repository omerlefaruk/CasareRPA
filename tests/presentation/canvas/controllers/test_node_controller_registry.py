"""
Tests for NodeController registry initialization.

Tests node registry management:
- Node registry setup
- Node type registration
- Node mapping cache
- Cleanup
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from PySide6.QtWidgets import QMainWindow

from casare_rpa.presentation.canvas.controllers.node_controller import (
    NodeController,
)


@pytest.fixture
def mock_main_window(qtbot):
    """Create a mock main window."""
    main_window = QMainWindow()
    qtbot.addWidget(main_window)

    # Mock graph
    mock_graph = Mock()
    main_window.get_graph = Mock(return_value=mock_graph)
    main_window.show_status = Mock()

    return main_window


@pytest.fixture
def node_controller(mock_main_window):
    """Create a NodeController instance."""
    controller = NodeController(mock_main_window)
    return controller


class TestNodeRegistrySetup:
    """Tests for node registry setup functionality."""

    @patch(
        "casare_rpa.presentation.canvas.controllers.node_controller.get_node_registry"
    )
    @patch(
        "casare_rpa.presentation.canvas.controllers.node_controller.get_casare_node_mapping"
    )
    def test_initialize_node_registry_success(
        self, mock_get_mapping, mock_get_registry, node_controller, mock_main_window
    ) -> None:
        """Test node registry initialization succeeds."""
        mock_registry = Mock()
        mock_registry.register_all_nodes = Mock()
        mock_get_registry.return_value = mock_registry

        node_controller.initialize()

        # Verify registry operations
        mock_registry.register_all_nodes.assert_called_once()
        mock_get_mapping.assert_called_once()

    @patch(
        "casare_rpa.presentation.canvas.controllers.node_controller.get_node_registry"
    )
    @patch(
        "casare_rpa.presentation.canvas.controllers.node_controller.get_casare_node_mapping"
    )
    def test_initialize_node_registry_with_graph(
        self, mock_get_mapping, mock_get_registry, node_controller, mock_main_window
    ) -> None:
        """Test node registry initialization uses graph from main window."""
        mock_registry = Mock()
        mock_registry.register_all_nodes = Mock()
        mock_get_registry.return_value = mock_registry

        mock_graph = mock_main_window.get_graph()

        node_controller.initialize()

        # Verify graph passed to register_all_nodes
        mock_registry.register_all_nodes.assert_called_once_with(mock_graph)

    def test_initialize_node_registry_without_graph(
        self, node_controller, mock_main_window
    ) -> None:
        """Test node registry initialization handles missing graph gracefully."""
        mock_main_window.get_graph.return_value = None

        with patch(
            "casare_rpa.presentation.canvas.controllers.node_controller.get_node_registry"
        ):
            node_controller.initialize()

        # Should not raise exception

    @patch(
        "casare_rpa.presentation.canvas.controllers.node_controller.get_node_registry"
    )
    def test_initialize_node_registry_handles_import_error(
        self, mock_get_registry, node_controller
    ) -> None:
        """Test node registry initialization handles import error gracefully."""
        mock_get_registry.side_effect = ImportError("Node registry not available")

        node_controller.initialize()

        # Should not raise exception

    @patch(
        "casare_rpa.presentation.canvas.controllers.node_controller.get_node_registry"
    )
    def test_initialize_node_registry_handles_exception(
        self, mock_get_registry, node_controller
    ) -> None:
        """Test node registry initialization handles general exception gracefully."""
        mock_registry = Mock()
        mock_registry.register_all_nodes.side_effect = Exception("Registration failed")
        mock_get_registry.return_value = mock_registry

        node_controller.initialize()

        # Should not raise exception


class TestNodeRegistration:
    """Tests for node type registration."""

    @patch(
        "casare_rpa.presentation.canvas.controllers.node_controller.get_node_registry"
    )
    @patch(
        "casare_rpa.presentation.canvas.controllers.node_controller.get_casare_node_mapping"
    )
    def test_register_all_nodes_called(
        self, mock_get_mapping, mock_get_registry, node_controller, mock_main_window
    ) -> None:
        """Test register_all_nodes is called during initialization."""
        mock_registry = Mock()
        mock_registry.register_all_nodes = Mock()
        mock_get_registry.return_value = mock_registry

        node_controller.initialize()

        # Verify all nodes registered
        assert mock_registry.register_all_nodes.call_count == 1

    @patch(
        "casare_rpa.presentation.canvas.controllers.node_controller.get_node_registry"
    )
    @patch(
        "casare_rpa.presentation.canvas.controllers.node_controller.get_casare_node_mapping"
    )
    def test_node_mapping_cache_built(
        self, mock_get_mapping, mock_get_registry, node_controller
    ) -> None:
        """Test node mapping cache is pre-built during initialization."""
        mock_registry = Mock()
        mock_registry.register_all_nodes = Mock()
        mock_get_registry.return_value = mock_registry

        node_controller.initialize()

        # Verify mapping cache built
        mock_get_mapping.assert_called_once()


class TestInitializeCallsRegistry:
    """Test that initialize() sets up node registry."""

    @patch(
        "casare_rpa.presentation.canvas.controllers.node_controller.get_node_registry"
    )
    @patch(
        "casare_rpa.presentation.canvas.controllers.node_controller.get_casare_node_mapping"
    )
    def test_initialize_calls_initialize_node_registry(
        self, mock_get_mapping, mock_get_registry, node_controller
    ) -> None:
        """Test that initialize() calls _initialize_node_registry()."""
        mock_registry = Mock()
        mock_registry.register_all_nodes = Mock()
        mock_get_registry.return_value = mock_registry

        with patch.object(
            node_controller,
            "_initialize_node_registry",
            wraps=node_controller._initialize_node_registry,
        ) as mock_init:
            node_controller.initialize()

        mock_init.assert_called_once()


class TestGetGraph:
    """Tests for _get_graph method."""

    def test_get_graph_success(self, node_controller, mock_main_window) -> None:
        """Test _get_graph returns graph from main window."""
        mock_graph = mock_main_window.get_graph()

        result = node_controller._get_graph()

        assert result == mock_graph

    def test_get_graph_handles_none(self, node_controller, mock_main_window) -> None:
        """Test _get_graph handles missing graph gracefully."""
        mock_main_window.get_graph.return_value = None

        result = node_controller._get_graph()

        assert result is None


class TestControllerState:
    """Tests for controller state management."""

    @patch(
        "casare_rpa.presentation.canvas.controllers.node_controller.get_node_registry"
    )
    @patch(
        "casare_rpa.presentation.canvas.controllers.node_controller.get_casare_node_mapping"
    )
    def test_controller_initialized_after_setup(
        self, mock_get_mapping, mock_get_registry, node_controller
    ) -> None:
        """Test controller is marked as initialized after setup."""
        mock_registry = Mock()
        mock_registry.register_all_nodes = Mock()
        mock_get_registry.return_value = mock_registry

        assert not node_controller.is_initialized

        node_controller.initialize()

        assert node_controller.is_initialized

    def test_cleanup_resets_initialized_state(self, node_controller) -> None:
        """Test cleanup resets initialized state."""
        with patch(
            "casare_rpa.presentation.canvas.controllers.node_controller.get_node_registry"
        ):
            node_controller.initialize()
            assert node_controller.is_initialized

            node_controller.cleanup()

            assert not node_controller.is_initialized
