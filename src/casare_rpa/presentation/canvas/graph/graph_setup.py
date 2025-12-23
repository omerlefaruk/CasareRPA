"""
Graph initialization and configuration module.

Extracts graph setup logic from NodeGraphWidget for better maintainability.
Handles:
- Graph configuration (colors, styles, optimization flags)
- OpenGL viewport setup
- Signal connections for viewport culling
- Connection validation setup
- Port legend and breadcrumb navigation setup
"""

from typing import TYPE_CHECKING

from loguru import logger
from PySide6.QtCore import QRectF, QTimer
from PySide6.QtWidgets import QGraphicsView

if TYPE_CHECKING:
    from NodeGraphQt import NodeGraph

    from casare_rpa.presentation.canvas.graph.viewport_culling import (
        ViewportCullingManager,
    )


class GraphSetup:
    """
    Handles graph initialization, configuration, and signal setup.

    Extracted from NodeGraphWidget to reduce class size and improve cohesion.
    """

    def __init__(self, graph: "NodeGraph", culler: "ViewportCullingManager"):
        """
        Initialize graph setup handler.

        Args:
            graph: The NodeGraph instance to configure
            culler: The viewport culling manager
        """
        self._graph = graph
        self._culler = culler
        self._viewport_update_timer: QTimer | None = None
        self._last_viewport_rect: QRectF = QRectF()
        self._last_transform_m11: float = 0.01
        self._last_transform_dx: float = 0.0
        self._last_transform_dy: float = 0.0

    def configure_graph(self) -> None:
        """Configure the node graph settings and appearance."""
        # Set graph background color to VSCode Dark+ editor background
        self._graph.set_background_color(30, 30, 30)

        # Set grid styling
        self._graph.set_grid_mode(1)

        # Set graph properties
        self._graph.set_pipe_style(1)  # Curved pipes

        # Configure viewer settings
        self._configure_viewer()

    def _configure_viewer(self) -> None:
        """Configure viewer colors and optimization settings."""
        from casare_rpa.presentation.canvas.graph.custom_pipe import (
            CasareLivePipe,
            CasarePipe,
        )

        viewer = self._graph.viewer()

        # Register custom pipe class
        try:
            viewer._PIPE_ITEM = CasarePipe
            viewer._LIVE_PIPE_ITEM = CasareLivePipe

            # If viewer already has a live pipe instance, we must REPLACE it
            if hasattr(viewer, "_LIVE_PIPE"):
                # Clean up old instance if it exists
                old_live_pipe = viewer._LIVE_PIPE
                if old_live_pipe and hasattr(old_live_pipe, "scene") and old_live_pipe.scene():
                    old_live_pipe.scene().removeItem(old_live_pipe)

                # Instantiate our custom class
                viewer._LIVE_PIPE = CasareLivePipe()
                viewer._LIVE_PIPE.setVisible(False)
                viewer.scene().addItem(viewer._LIVE_PIPE)
                logger.debug("Replaced default live pipe with CasareLivePipe")
        except Exception as e:
            logger.warning(f"Could not register custom pipe: {e}")

        # Set selection colors
        if hasattr(viewer, "_node_sel_color"):
            viewer._node_sel_color = (0, 0, 0, 0)
        if hasattr(viewer, "_node_sel_border_color"):
            viewer._node_sel_border_color = (255, 215, 0, 255)

        # Set pipe colors
        if hasattr(viewer, "_pipe_color"):
            viewer._pipe_color = (100, 100, 100, 255)
        if hasattr(viewer, "_live_pipe_color"):
            viewer._live_pipe_color = (100, 100, 100, 255)

        # Configure port colors
        if hasattr(viewer, "_port_color"):
            viewer._port_color = (100, 181, 246, 255)
        if hasattr(viewer, "_port_border_color"):
            viewer._port_border_color = (66, 165, 245, 255)

        # Enable optimization flags
        self._configure_optimization_flags(viewer)

        # Setup OpenGL viewport
        self._setup_opengl_viewport(viewer)

    def _configure_optimization_flags(self, viewer: QGraphicsView) -> None:
        """Configure QGraphicsView optimization flags for performance."""
        from PySide6.QtCore import Qt

        viewer.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontSavePainterState, True)
        viewer.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontAdjustForAntialiasing, True)
        viewer.setOptimizationFlag(QGraphicsView.OptimizationFlag.IndirectPainting, True)

        # Minimal viewport updates
        viewer.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.MinimalViewportUpdate)

        # Disable Qt caching (use custom LOD-based caching)
        viewer.setCacheMode(QGraphicsView.CacheModeFlag(0))

        # High refresh rate optimizations
        viewer.viewport().setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        viewer.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)

    def _setup_opengl_viewport(self, viewer: QGraphicsView) -> None:
        """Setup GPU-accelerated OpenGL viewport."""
        try:
            from PySide6.QtGui import QSurfaceFormat
            from PySide6.QtOpenGLWidgets import QOpenGLWidget

            gl_format = QSurfaceFormat()
            gl_format.setVersion(3, 3)
            gl_format.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
            gl_format.setSwapBehavior(QSurfaceFormat.SwapBehavior.DoubleBuffer)
            gl_format.setSwapInterval(0)
            gl_format.setSamples(4)

            gl_widget = QOpenGLWidget()
            gl_widget.setFormat(gl_format)
            viewer.setViewport(gl_widget)

            QSurfaceFormat.setDefaultFormat(gl_format)
            logger.debug("GPU rendering enabled (OpenGL 3.3)")
        except Exception as e:
            logger.warning(f"GPU rendering unavailable, using CPU: {e}")

    def setup_viewport_culling(
        self,
        on_node_created_callback,
        on_nodes_deleted_callback,
        on_pipe_created_callback,
        on_pipe_deleted_callback,
        on_session_changed_callback,
        update_culling_callback,
    ) -> None:
        """
        Wire up viewport culling to graph events.

        Args:
            on_node_created_callback: Callback for node creation
            on_nodes_deleted_callback: Callback for node deletion
            on_pipe_created_callback: Callback for pipe creation
            on_pipe_deleted_callback: Callback for pipe deletion
            on_session_changed_callback: Callback for session changes
            update_culling_callback: Callback for viewport updates
        """
        try:
            if hasattr(self._graph, "node_created"):
                self._graph.node_created.connect(on_node_created_callback)
            if hasattr(self._graph, "nodes_deleted"):
                self._graph.nodes_deleted.connect(on_nodes_deleted_callback)
            if hasattr(self._graph, "port_connected"):
                self._graph.port_connected.connect(on_pipe_created_callback)
            if hasattr(self._graph, "port_disconnected"):
                self._graph.port_disconnected.connect(on_pipe_deleted_callback)
            if hasattr(self._graph, "session_changed"):
                self._graph.session_changed.connect(on_session_changed_callback)

            # Start viewport update timer
            self._start_viewport_timer(update_culling_callback)

            logger.debug("Viewport culling signals connected")
        except Exception as e:
            logger.warning(f"Could not setup viewport culling: {e}")

    def _start_viewport_timer(self, update_callback) -> None:
        """Start the viewport update timer for smooth culling."""
        from PySide6.QtCore import QTimer

        self._viewport_update_timer = QTimer()
        self._viewport_update_timer.setInterval(8)  # ~120 FPS
        self._viewport_update_timer.timeout.connect(update_callback)
        self._viewport_update_timer.start()

    @staticmethod
    def _is_viewport_changed(current: QRectF, last: QRectF, tol: float = 0.5) -> bool:
        """
        Check if viewport rect changed beyond a small tolerance.

        This avoids missing updates due to minor floating-point jitter while
        still skipping truly idle frames.
        """
        if last.isNull():
            return True
        return (
            abs(current.x() - last.x()) > tol
            or abs(current.y() - last.y()) > tol
            or abs(current.width() - last.width()) > tol
            or abs(current.height() - last.height()) > tol
        )

    def update_viewport_culling(self) -> None:
        """Update culling and LOD based on current viewport."""
        from casare_rpa.presentation.canvas.graph.custom_node_item import (
            get_high_performance_mode,
        )
        from casare_rpa.presentation.canvas.graph.lod_manager import (
            LODLevel,
            get_lod_manager,
        )

        try:
            viewer = self._graph.viewer()
            if not viewer or not viewer.viewport():
                return

            viewport_rect = viewer.mapToScene(viewer.viewport().rect()).boundingRect()

            # Check transform changes
            transform = viewer.transform()
            m11 = transform.m11()
            dx = transform.dx()
            dy = transform.dy()

            zoom_pct_change = abs(m11 - self._last_transform_m11) / max(
                self._last_transform_m11, 0.01
            )
            transform_changed = (
                zoom_pct_change > 0.02
                or abs(dx - self._last_transform_dx) > 0.5
                or abs(dy - self._last_transform_dy) > 0.5
            )

            viewport_changed = self._is_viewport_changed(viewport_rect, self._last_viewport_rect)

            # Skip if neither viewport nor transform changed (idle detection)
            if not viewport_changed and not transform_changed:
                return

            if viewport_changed:
                self._last_viewport_rect = viewport_rect
                self._culler.update_viewport(viewport_rect)

            if transform_changed:
                self._last_transform_m11 = m11
                self._last_transform_dx = dx
                self._last_transform_dy = dy
                viewer.resetCachedContent()

            # Update LOD manager
            lod_manager = get_lod_manager()
            lod_manager.update_from_view(viewer)

            if get_high_performance_mode():
                lod_manager.force_lod(LODLevel.LOW)

        except Exception:
            pass  # Suppress errors during startup

    def cleanup(self) -> None:
        """Clean up timers and resources."""
        if self._viewport_update_timer:
            self._viewport_update_timer.stop()
            self._viewport_update_timer.deleteLater()
            self._viewport_update_timer = None

    @property
    def viewport_update_timer(self) -> QTimer | None:
        """Get the viewport update timer."""
        return self._viewport_update_timer
