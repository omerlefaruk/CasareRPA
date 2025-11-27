"""
Comprehensive tests for ViewportController.

Tests viewport management including:
- Frame creation
- Minimap management
- Zoom display updates
- Viewport state management
"""

import pytest
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QMainWindow

from casare_rpa.presentation.canvas.controllers.viewport_controller import (
    ViewportController,
)


@pytest.fixture
def mock_main_window(qtbot) -> None:
    """Create a mock MainWindow with viewport-related components."""
    main_window = QMainWindow()
    qtbot.addWidget(main_window)

    # Add mock attributes for minimap
    main_window._minimap = Mock()
    main_window._minimap.setVisible = Mock()
    main_window._minimap.move = Mock()
    main_window._minimap.raise_ = Mock()
    main_window._minimap.height = Mock(return_value=200)

    # Add mock attributes for central widget
    main_window._central_widget = Mock()
    main_window._central_widget.graph = Mock()
    main_window._central_widget.height = Mock(return_value=800)

    # Add mock zoom label
    main_window._zoom_label = Mock()
    main_window._zoom_label.setText = Mock()

    # Mock methods
    main_window.get_minimap = Mock(return_value=main_window._minimap)
    main_window.show_status = Mock()

    # Override centralWidget to return our mock
    main_window.centralWidget = Mock(return_value=main_window._central_widget)

    return main_window


@pytest.fixture
def viewport_controller(mock_main_window) -> None:
    """Create a ViewportController instance."""
    controller = ViewportController(mock_main_window)
    controller.initialize()
    return controller


class TestViewportControllerInitialization:
    """Tests for ViewportController initialization."""

    def test_initialization(self, mock_main_window) -> None:
        """Test controller initializes correctly."""
        controller = ViewportController(mock_main_window)
        assert controller.main_window == mock_main_window
        assert controller._current_zoom == 100.0
        assert controller._minimap_visible is False

    def test_initialize_method(self, mock_main_window) -> None:
        """Test initialize method sets initialized flag."""
        controller = ViewportController(mock_main_window)
        controller.initialize()
        assert controller.is_initialized is True

    def test_cleanup(self, viewport_controller) -> None:
        """Test cleanup method."""
        viewport_controller.cleanup()
        assert viewport_controller.is_initialized is False


class TestMinimapManagement:
    """Tests for minimap management functionality."""

    def test_show_minimap(self, viewport_controller, mock_main_window) -> None:
        """Test showing the minimap."""
        signal_emitted = []
        viewport_controller.minimap_toggled.connect(
            lambda visible: signal_emitted.append(visible)
        )

        viewport_controller.show_minimap()

        mock_main_window._minimap.setVisible.assert_called_with(True)
        assert viewport_controller._minimap_visible is True
        assert len(signal_emitted) == 1
        assert signal_emitted[0] is True

    def test_hide_minimap(self, viewport_controller, mock_main_window) -> None:
        """Test hiding the minimap."""
        viewport_controller._minimap_visible = True

        signal_emitted = []
        viewport_controller.minimap_toggled.connect(
            lambda visible: signal_emitted.append(visible)
        )

        viewport_controller.hide_minimap()

        mock_main_window._minimap.setVisible.assert_called_with(False)
        assert viewport_controller._minimap_visible is False
        assert len(signal_emitted) == 1
        assert signal_emitted[0] is False

    def test_toggle_minimap_on(self, viewport_controller, mock_main_window) -> None:
        """Test toggling minimap on."""
        viewport_controller.toggle_minimap(True)

        mock_main_window._minimap.setVisible.assert_called_with(True)
        assert viewport_controller._minimap_visible is True

    def test_toggle_minimap_off(self, viewport_controller, mock_main_window) -> None:
        """Test toggling minimap off."""
        viewport_controller._minimap_visible = True

        viewport_controller.toggle_minimap(False)

        mock_main_window._minimap.setVisible.assert_called_with(False)
        assert viewport_controller._minimap_visible is False

    def test_position_minimap(self, viewport_controller, mock_main_window) -> None:
        """Test positioning minimap at bottom-left."""
        viewport_controller._position_minimap()

        mock_main_window._minimap.move.assert_called()
        mock_main_window._minimap.raise_.assert_called()

    def test_is_minimap_visible_true(self, viewport_controller) -> None:
        """Test is_minimap_visible returns true when visible."""
        viewport_controller._minimap_visible = True
        assert viewport_controller.is_minimap_visible() is True

    def test_is_minimap_visible_false(self, viewport_controller) -> None:
        """Test is_minimap_visible returns false when hidden."""
        viewport_controller._minimap_visible = False
        assert viewport_controller.is_minimap_visible() is False


class TestZoomManagement:
    """Tests for zoom display functionality."""

    def test_update_zoom_display(self, viewport_controller, mock_main_window) -> None:
        """Test updating zoom display."""
        signal_emitted = []
        viewport_controller.zoom_changed.connect(
            lambda zoom: signal_emitted.append(zoom)
        )

        viewport_controller.update_zoom_display(150.0)

        assert viewport_controller._current_zoom == 150.0
        mock_main_window._zoom_label.setText.assert_called_with("150%")
        assert len(signal_emitted) == 1
        assert signal_emitted[0] == 150.0

    def test_get_current_zoom(self, viewport_controller) -> None:
        """Test getting current zoom level."""
        viewport_controller._current_zoom = 75.0
        assert viewport_controller.get_current_zoom() == 75.0

    def test_get_current_zoom_default(self, viewport_controller) -> None:
        """Test default zoom level is 100%."""
        assert viewport_controller.get_current_zoom() == 100.0

    def test_zoom_changed_signal_emitted(self, viewport_controller) -> None:
        """Test zoom_changed signal is emitted when zoom updates."""
        signal_values = []
        viewport_controller.zoom_changed.connect(
            lambda zoom: signal_values.append(zoom)
        )

        viewport_controller.update_zoom_display(200.0)
        viewport_controller.update_zoom_display(50.0)

        assert signal_values == [200.0, 50.0]


class TestViewportOperations:
    """Tests for viewport operations."""

    def test_reset_viewport(self, viewport_controller, mock_main_window) -> None:
        """Test resetting viewport to default state."""
        mock_graph = Mock()
        mock_main_window._central_widget.graph = mock_graph

        signal_emitted = []
        viewport_controller.viewport_reset.connect(lambda: signal_emitted.append(True))

        viewport_controller._current_zoom = 150.0
        viewport_controller.reset_viewport()

        mock_graph.reset_zoom.assert_called_once()
        assert viewport_controller._current_zoom == 100.0
        assert len(signal_emitted) == 1

    def test_fit_to_view(self, viewport_controller, mock_main_window) -> None:
        """Test fitting viewport to show all nodes."""
        mock_graph = Mock()
        mock_main_window._central_widget.graph = mock_graph

        viewport_controller.fit_to_view()

        mock_graph.fit_to_selection.assert_called_once()

    def test_center_on_node(self, viewport_controller, mock_main_window) -> None:
        """Test centering viewport on a specific node."""
        mock_graph = Mock()
        mock_node = Mock()
        mock_node.id.return_value = "test-node-id"
        mock_graph.all_nodes.return_value = [mock_node]
        mock_graph.clear_selection = Mock()
        mock_graph.fit_to_selection = Mock()
        mock_main_window._central_widget.graph = mock_graph

        viewport_controller.center_on_node("test-node-id")

        mock_graph.clear_selection.assert_called_once()
        mock_node.set_selected.assert_called_once_with(True)
        mock_graph.fit_to_selection.assert_called_once()

    def test_center_on_node_not_found(
        self, viewport_controller, mock_main_window
    ) -> None:
        """Test centering on non-existent node."""
        mock_graph = Mock()
        mock_graph.all_nodes.return_value = []
        mock_main_window._central_widget.graph = mock_graph

        # Should not raise an error
        viewport_controller.center_on_node("non-existent-node")


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_minimap_operations_without_minimap(self, qtbot) -> None:
        """Test minimap operations when minimap is None."""
        main_window = QMainWindow()
        qtbot.addWidget(main_window)
        main_window.get_minimap = Mock(return_value=None)
        main_window.centralWidget = Mock(return_value=None)
        main_window.show_status = Mock()

        controller = ViewportController(main_window)
        controller.initialize()

        # These should not raise errors
        controller.show_minimap()
        controller.hide_minimap()
        controller.toggle_minimap(True)

    def test_zoom_without_label(self, qtbot) -> None:
        """Test zoom display update when label is not available."""
        main_window = QMainWindow()
        qtbot.addWidget(main_window)
        main_window.get_minimap = Mock(return_value=None)
        main_window.centralWidget = Mock(return_value=None)
        main_window.show_status = Mock()
        # No _zoom_label attribute

        controller = ViewportController(main_window)
        controller.initialize()

        # Should not raise error
        controller.update_zoom_display(150.0)

    def test_viewport_operations_no_graph(self, qtbot) -> None:
        """Test viewport operations when graph is not available."""
        main_window = QMainWindow()
        qtbot.addWidget(main_window)
        main_window.get_minimap = Mock(return_value=None)
        main_window.centralWidget = Mock(return_value=None)
        main_window.show_status = Mock()

        controller = ViewportController(main_window)
        controller.initialize()

        # Should not raise errors
        controller.reset_viewport()
        controller.fit_to_view()
        controller.center_on_node("any-node")

    def test_create_frame_no_graph_available(self, qtbot) -> None:
        """Test frame creation when graph is not available."""
        main_window = QMainWindow()
        qtbot.addWidget(main_window)
        main_window.get_minimap = Mock(return_value=None)
        main_window.centralWidget = Mock(return_value=None)
        main_window.show_status = Mock()

        controller = ViewportController(main_window)
        controller.initialize()

        # Should not raise an error
        controller.create_frame()

        main_window.show_status.assert_called_once()
