"""
Viewport controller for canvas view management.

Handles all viewport-related operations:
- Frame creation and management
- Minimap creation and positioning
- Zoom display updates
- Viewport state management
"""

from typing import TYPE_CHECKING

from loguru import logger
from PySide6.QtCore import QEasingCurve, QPointF, QVariantAnimation, Signal
from PySide6.QtWidgets import QMessageBox

from casare_rpa.presentation.canvas.controllers.base_controller import BaseController
from casare_rpa.presentation.canvas.theme_system import TOKENS
from casare_rpa.presentation.canvas.ui.theme import ANIMATIONS

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

    # Zoom limits
    MIN_ZOOM: float = 0.1
    MAX_ZOOM: float = 2.0

    def __init__(self, main_window: "MainWindow"):
        """
        Initialize viewport controller.

        Args:
            main_window: Reference to main window for accessing shared components
        """
        super().__init__(main_window)
        self._current_zoom: float = 100.0
        self._minimap_visible: bool = False
        self._zoom_animation: QVariantAnimation | None = None
        self._zoom_center: QPointF | None = None

    def initialize(self) -> None:
        """Initialize controller resources and connections."""
        super().initialize()

    def cleanup(self) -> None:
        """Clean up controller resources."""
        # Stop any running zoom animation
        if self._zoom_animation and self._zoom_animation.state() == QVariantAnimation.Running:
            self._zoom_animation.stop()
        self._zoom_animation = None
        self._zoom_center = None
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
                NodeFrame,
                create_frame,
                group_selected_nodes,
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
                    size=(TOKENS.sizes.dialog_sm_width, TOKENS.sizes.dialog_height_sm),
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

    def smooth_zoom(self, factor: float, center: QPointF | None = None) -> None:
        """
        Animate zoom with InOutSine easing curve.

        Smoothly interpolates from current zoom to target zoom while
        preserving the point under the cursor (or viewport center).

        Args:
            factor: Zoom multiplier (>1 for zoom in, <1 for zoom out)
            center: Point to zoom toward in scene coordinates.
                   If None, uses viewport center.
        """
        graph = self._get_graph()
        if not graph:
            return

        viewer = graph.viewer()
        if not viewer:
            return

        # Stop any running zoom animation
        if self._zoom_animation and self._zoom_animation.state() == QVariantAnimation.Running:
            self._zoom_animation.stop()

        # Get current scale from transform matrix
        current_scale = viewer.transform().m11()
        target_scale = current_scale * factor

        # Clamp to min/max zoom
        target_scale = max(self.MIN_ZOOM, min(target_scale, self.MAX_ZOOM))

        # Skip if already at limit
        if abs(target_scale - current_scale) < 0.001:
            return

        # Use viewport center if no center provided
        if center is None:
            viewport_center = viewer.viewport().rect().center()
            center = viewer.mapToScene(viewport_center)

        self._zoom_center = center

        # Create and configure animation
        self._zoom_animation = QVariantAnimation()
        self._zoom_animation.setDuration(ANIMATIONS.medium)
        self._zoom_animation.setStartValue(float(current_scale))
        self._zoom_animation.setEndValue(float(target_scale))
        self._zoom_animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._zoom_animation.valueChanged.connect(self._apply_zoom_step)
        self._zoom_animation.start()

    def _apply_zoom_step(self, scale: float) -> None:
        """
        Apply intermediate zoom step during animation.

        Maintains the zoom center point at the same screen position
        throughout the animation.

        Args:
            scale: Current interpolated scale value
        """
        graph = self._get_graph()
        if not graph:
            return

        viewer = graph.viewer()
        if not viewer or self._zoom_center is None:
            return

        try:
            # Get the scene position of the zoom center before transform
            old_pos = viewer.mapFromScene(self._zoom_center)

            # Reset transform and apply new scale
            viewer.resetTransform()
            viewer.scale(scale, scale)

            # Get the new screen position of the zoom center after transform
            new_pos = viewer.mapFromScene(self._zoom_center)

            # Translate to keep the zoom center at the same screen position
            delta = old_pos - new_pos
            viewer.translate(delta.x(), delta.y())

            # Update zoom display
            zoom_percent = scale * 100.0
            self.update_zoom_display(zoom_percent)
        except Exception as e:
            logger.error(f"Failed to apply zoom step: {e}")

    def handle_wheel_zoom(self, delta_y: int, scene_pos: QPointF) -> None:
        """
        Handle mouse wheel zoom with smooth animation.

        Called from event handlers when user scrolls the mouse wheel.
        Zooms in/out centered on the cursor position.

        Args:
            delta_y: Vertical scroll delta (positive = zoom in)
            scene_pos: Cursor position in scene coordinates
        """
        factor = 1.15 if delta_y > 0 else 1 / 1.15
        self.smooth_zoom(factor, scene_pos)

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

    def focus_view(self) -> None:
        """
        Focus/frame selected node(s) - like Nuke/Houdini's F key.

        Frames the selected node(s) in the center of the viewport.
        """
        graph = self._get_graph()
        if not graph:
            return

        try:
            selected_nodes = graph.selected_nodes()
            if not selected_nodes:
                return

            viewer = graph.viewer()
            if not viewer:
                return

            # Calculate bounding rect of all selected nodes
            from PySide6.QtCore import QRectF

            combined_rect = QRectF()
            for node in selected_nodes:
                if hasattr(node, "view") and node.view:
                    node_rect = node.view.sceneBoundingRect()
                    if combined_rect.isNull():
                        combined_rect = node_rect
                    else:
                        combined_rect = combined_rect.united(node_rect)

            if combined_rect.isNull():
                return

            # Add padding around the node(s) for comfortable viewing
            padding = TOKENS.sizes.panel_min_width
            padded_rect = combined_rect.adjusted(-padding, -padding, padding, padding)

            # CRITICAL: Update NodeGraphQt's internal _scene_range to match the new view
            # Without this, panning would restore the old zoom level because
            # viewer.translate() adjusts based on _scene_range
            viewer._scene_range = padded_rect
            viewer._update_scene()

            logger.debug(f"Framed {len(selected_nodes)} node(s) at center")

        except Exception as e:
            logger.error(f"Failed to focus view: {e}")

    def home_all(self) -> None:
        """
        Home all: fit all nodes in view regardless of selection.

        Frames all nodes in the viewport without changing selection.
        """
        graph = self._get_graph()
        if not graph:
            return

        try:
            all_nodes = graph.all_nodes()
            if not all_nodes:
                logger.debug("No nodes to home")
                return

            viewer = graph.viewer()
            if not viewer:
                return

            # Calculate bounding rect of all nodes
            from PySide6.QtCore import QRectF

            combined_rect = QRectF()
            for node in all_nodes:
                if hasattr(node, "view") and node.view:
                    node_rect = node.view.sceneBoundingRect()
                    if combined_rect.isNull():
                        combined_rect = node_rect
                    else:
                        combined_rect = combined_rect.united(node_rect)

            if combined_rect.isNull():
                return

            # Add padding around all nodes for comfortable viewing
            padding = 100
            padded_rect = combined_rect.adjusted(-padding, -padding, padding, padding)

            # CRITICAL: Update NodeGraphQt's internal _scene_range to match the new view
            # Without this, panning would restore the old zoom level because
            # viewer.translate() adjusts based on _scene_range
            viewer._scene_range = padded_rect
            viewer._update_scene()

            logger.debug(f"Home all: fitted {len(all_nodes)} nodes")
        except Exception as e:
            logger.error(f"Failed to home all: {e}")

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
