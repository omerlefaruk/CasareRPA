"""
Viewport controller for canvas view management.

Handles all viewport-related operations:
- Frame creation and management
- Minimap creation and positioning
- Zoom display updates
- Viewport state management
"""

from typing import TYPE_CHECKING
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMessageBox
from loguru import logger

from casare_rpa.presentation.canvas.controllers.base_controller import BaseController

if TYPE_CHECKING:
    from casare_rpa.presentation.canvas.main_window import MainWindow


class ViewportController(BaseController):
    """
    Manages canvas viewport operations.

    Single Responsibility: Viewport display and frame management.

    Signals:
        frame_created: Emitted when a frame is created (NodeFrame)
        zoom_changed: Emitted when zoom level changes (float: zoom_percent)
        minimap_toggled: Emitted when minimap visibility changes (bool: visible)
        viewport_reset: Emitted when viewport is reset to default
    """

    # Signals
    frame_created = Signal(object)  # NodeFrame
    zoom_changed = Signal(float)  # zoom_percent
    minimap_toggled = Signal(bool)  # visible
    viewport_reset = Signal()

    def __init__(self, main_window: "MainWindow"):
        """
        Initialize viewport controller.

        Args:
            main_window: Reference to main window for accessing shared components
        """
        super().__init__(main_window)
        self._current_zoom: float = 100.0
        self._minimap_visible: bool = False

    def initialize(self) -> None:
        """Initialize controller resources and connections."""
        super().initialize()
        logger.info("ViewportController initialized")

    def cleanup(self) -> None:
        """Clean up controller resources."""
        super().cleanup()
        logger.info("ViewportController cleanup")

    def create_frame(self) -> None:
        """
        Create a frame around selected nodes or an empty frame.

        If nodes are selected, creates a frame containing them.
        Otherwise, creates an empty frame at the canvas center.
        """
        try:
            from ..graph.node_frame import (
                group_selected_nodes,
                create_frame,
                NodeFrame,
            )

            graph = self._get_graph()
            if not graph:
                logger.warning("Cannot create frame: Node graph not available")
                self.main_window.show_status("Node graph not available", 3000)
                return

            viewer = graph.viewer()
            selected_nodes = graph.selected_nodes()

            # Set graph reference for all frames
            NodeFrame.set_graph(graph)

            if selected_nodes:
                frame = group_selected_nodes(viewer, "Group", selected_nodes)
                if frame:
                    logger.info(f"Created frame around {len(selected_nodes)} nodes")
                    self.main_window.show_status(
                        f"Created frame with {len(selected_nodes)} nodes", 3000
                    )
                    self.frame_created.emit(frame)
            else:
                frame = create_frame(
                    viewer,
                    title="Frame",
                    color_name="blue",
                    position=(0, 0),
                    size=(400, 300),
                    graph=graph,
                )
                logger.info("Created empty frame at canvas center")
                self.main_window.show_status("Created empty frame", 3000)
                if frame:
                    self.frame_created.emit(frame)

        except ImportError as e:
            logger.error(f"Failed to import frame module: {e}")
            self._show_frame_error(f"Frame module not available: {e}")
        except Exception as e:
            logger.error(f"Failed to create frame: {e}")
            self._show_frame_error(str(e))

    def create_minimap(self, node_graph) -> None:
        """
        Create minimap overlay widget for the node graph.

        Args:
            node_graph: The NodeGraph instance to create minimap for
        """
        try:
            from ..graph.minimap import Minimap

            central_widget = self.main_window.centralWidget()
            if central_widget:
                minimap = Minimap(node_graph, central_widget)
                minimap.setVisible(False)  # Initially hidden
                self.main_window._minimap = minimap
                self._position_minimap()
                logger.debug("Minimap created successfully")
        except ImportError as e:
            logger.error(f"Failed to import Minimap: {e}")
        except Exception as e:
            logger.error(f"Failed to create minimap: {e}")

    def position_minimap(self) -> None:
        """Position minimap at bottom-left of central widget."""
        self._position_minimap()

    def _position_minimap(self) -> None:
        """Internal method to position minimap at bottom-left of central widget."""
        minimap = self.main_window.get_minimap()
        central_widget = self.main_window.centralWidget()

        if minimap and central_widget:
            margin = 10
            x = margin
            y = central_widget.height() - minimap.height() - margin
            minimap.move(x, y)
            minimap.raise_()  # Ensure it's on top

    def show_minimap(self) -> None:
        """Show the minimap overlay."""
        minimap = self.main_window.get_minimap()
        if minimap:
            minimap.setVisible(True)
            self._position_minimap()
            self._minimap_visible = True
            self.minimap_toggled.emit(True)
            logger.debug("Minimap shown")

    def hide_minimap(self) -> None:
        """Hide the minimap overlay."""
        minimap = self.main_window.get_minimap()
        if minimap:
            minimap.setVisible(False)
            self._minimap_visible = False
            self.minimap_toggled.emit(False)
            logger.debug("Minimap hidden")

    def toggle_minimap(self, checked: bool) -> None:
        """
        Toggle minimap visibility.

        Args:
            checked: True to show, False to hide
        """
        if checked:
            self.show_minimap()
        else:
            self.hide_minimap()

    def update_zoom_display(self, zoom_percent: float) -> None:
        """
        Update zoom level display and emit signal.

        Args:
            zoom_percent: Current zoom level as percentage
        """
        self._current_zoom = zoom_percent
        self.zoom_changed.emit(zoom_percent)

        # Update main window's zoom label if available
        if hasattr(self.main_window, "_zoom_label"):
            self.main_window._zoom_label.setText(f"{int(zoom_percent)}%")

    def get_current_zoom(self) -> float:
        """
        Get current zoom level.

        Returns:
            Current zoom level as percentage
        """
        return self._current_zoom

    def is_minimap_visible(self) -> bool:
        """
        Check if minimap is currently visible.

        Returns:
            True if minimap is visible
        """
        return self._minimap_visible

    def reset_viewport(self) -> None:
        """Reset viewport to default state (100% zoom, centered)."""
        graph = self._get_graph()
        if graph:
            try:
                graph.reset_zoom()
                self._current_zoom = 100.0
                self.zoom_changed.emit(100.0)
                self.viewport_reset.emit()
                logger.debug("Viewport reset to default")
            except Exception as e:
                logger.error(f"Failed to reset viewport: {e}")

    def fit_to_view(self) -> None:
        """Fit all nodes in the current view."""
        graph = self._get_graph()
        if graph:
            try:
                graph.fit_to_selection()
                logger.debug("Viewport fitted to selection")
            except Exception as e:
                logger.error(f"Failed to fit viewport: {e}")

    def center_on_node(self, node_id: str) -> None:
        """
        Center viewport on a specific node.

        Args:
            node_id: ID of the node to center on
        """
        graph = self._get_graph()
        if not graph:
            return

        try:
            for node in graph.all_nodes():
                if node.id() == node_id or getattr(node, "node_id", None) == node_id:
                    graph.clear_selection()
                    node.set_selected(True)
                    graph.fit_to_selection()
                    logger.debug(f"Centered viewport on node: {node_id}")
                    return
            logger.warning(f"Node not found for centering: {node_id}")
        except Exception as e:
            logger.error(f"Failed to center on node {node_id}: {e}")

    def _get_graph(self):
        """
        Get the node graph from the central widget.

        Returns:
            NodeGraph instance or None if not available
        """
        central_widget = self.main_window.centralWidget()
        if central_widget and hasattr(central_widget, "graph"):
            return central_widget.graph
        return None

    def _show_frame_error(self, error_message: str) -> None:
        """
        Display frame creation error to user.

        Args:
            error_message: Error message to display
        """
        QMessageBox.warning(
            self.main_window,
            "Create Frame",
            f"Failed to create frame:\n{error_message}",
        )
