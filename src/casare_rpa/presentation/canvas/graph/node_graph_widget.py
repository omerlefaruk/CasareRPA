"""
Node graph widget wrapper for NodeGraphQt integration.

This module provides a wrapper around NodeGraphQt's NodeGraph
to integrate it with the PySide6 application.

The NodeGraphQt library has several bugs and limitations that are fixed
via wrapper classes in node_widgets.py. All fixes are applied at module
load time by calling apply_all_node_widget_fixes().
"""

from typing import Optional

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtWidgets import QApplication, QLineEdit, QTextEdit, QVBoxLayout, QWidget

from loguru import logger
from NodeGraphQt import NodeGraph

from casare_rpa.presentation.canvas.connections.auto_connect import AutoConnectManager
from casare_rpa.presentation.canvas.connections.connection_cutter import (
    ConnectionCutter,
)
from casare_rpa.presentation.canvas.connections.node_insert import NodeInsertManager
from casare_rpa.presentation.canvas.graph.composite_node_creator import (
    CompositeNodeCreator,
)
from casare_rpa.presentation.canvas.graph.custom_pipe import CasarePipe
from casare_rpa.presentation.canvas.graph.event_filters import (
    ConnectionDropFilter,
    OutputPortMMBFilter,
    TooltipBlocker,
)
from casare_rpa.presentation.canvas.graph.node_creation_helper import (
    NodeCreationHelper,
)
from casare_rpa.presentation.canvas.graph.node_quick_actions import NodeQuickActions
from casare_rpa.presentation.canvas.graph.node_widgets import (
    apply_all_node_widget_fixes,
)
from casare_rpa.presentation.canvas.graph.selection_manager import SelectionManager

# ============================================================================
# CRITICAL: Disable NodeGraphQt item caching to prevent zoom/pan glitches
# ============================================================================
# NodeGraphQt uses DeviceCoordinateCache which causes rendering artifacts
# when zooming/panning because cached images become stale. We patch the
# constant to NoCache (value 0) before any items are created.
from PySide6.QtWidgets import QGraphicsItem

_NO_CACHE = QGraphicsItem.CacheMode.NoCache

# Patch all NodeGraphQt modules that use ITEM_CACHE_MODE
try:
    import NodeGraphQt.qgraphics.node_abstract as _node_abstract
    import NodeGraphQt.qgraphics.node_base as _node_base
    import NodeGraphQt.qgraphics.pipe as _pipe
    import NodeGraphQt.qgraphics.port as _port

    _node_abstract.ITEM_CACHE_MODE = _NO_CACHE
    _node_base.ITEM_CACHE_MODE = _NO_CACHE
    _pipe.ITEM_CACHE_MODE = _NO_CACHE
    _port.ITEM_CACHE_MODE = _NO_CACHE
    logger.debug("Disabled NodeGraphQt item caching to prevent zoom/pan glitches")
except Exception as e:
    logger.warning(f"Failed to patch NodeGraphQt cache mode: {e}")

# Import connection validator for strict type checking
try:
    from casare_rpa.presentation.canvas.connections.connection_validator import (
        ConnectionValidator,
        get_connection_validator,
    )

    HAS_CONNECTION_VALIDATOR = True
except ImportError:
    HAS_CONNECTION_VALIDATOR = False
    logger.warning("ConnectionValidator not available - connection validation disabled")


# ============================================================================
# Apply all NodeGraphQt fixes via wrapper classes
# ============================================================================
# This replaces the inline monkey-patches that were previously scattered
# throughout this module. The fixes are now encapsulated in node_widgets.py:
#   - CasareComboBox: Fixes combo dropdown z-order issue
#   - CasareCheckBox: Adds dark blue checkbox styling
#   - CasareLivePipe: Fixes draw_index_pointer text_pos bug
#   - CasarePipeItemFix: Fixes draw_path viewer None crash

apply_all_node_widget_fixes()


class NodeGraphWidget(QWidget):
    """
    Widget wrapper for NodeGraphQt's NodeGraph.

    Provides a Qt widget container for the node graph editor
    with custom styling and configuration.

    Now includes connection validation with strict type checking.
    """

    # Signal emitted when an invalid connection is blocked
    connection_blocked = Signal(str)  # Error message

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the node graph widget.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        # Create node graph
        self._graph = NodeGraph()

        # Configure graph
        self._setup_graph()

        # Enable viewport culling for smooth 60 FPS panning with 100+ nodes
        from casare_rpa.presentation.canvas.graph.viewport_culling import (
            ViewportCullingManager,
        )

        self._culler = ViewportCullingManager(cell_size=500, margin=200)
        self._culler.set_enabled(True)
        self._setup_viewport_culling()

        # Create selection manager
        self._selection = SelectionManager(self._graph, self)

        # Create composite node creator (For Loop, While Loop, Try/Catch)
        self._composite_creator = CompositeNodeCreator(self._graph, self)

        # Create node creation helper (SetVariable, drag-drop, auto-connect)
        self._creation_helper = NodeCreationHelper(self._graph, self)

        # Create auto-connect manager
        self._auto_connect = AutoConnectManager(self._graph, self)

        # Create connection cutter (Y + LMB drag to cut connections)
        self._connection_cutter = ConnectionCutter(self._graph, self)

        # Create node insert manager (drag node onto connection to insert)
        self._node_insert = NodeInsertManager(self._graph, self)

        # Create quick actions for node context menu
        self._quick_actions = NodeQuickActions(self._graph, self)

        # Wire up auto-connect reference so quick actions can check drag state
        # This allows RMB to confirm auto-connect while dragging
        self._quick_actions.set_auto_connect_manager(self._auto_connect)

        # Setup connection validator for strict type checking
        self._validator = (
            get_connection_validator() if HAS_CONNECTION_VALIDATOR else None
        )
        if self._validator:
            self._setup_connection_validation()

        # Setup paste hook for duplicate ID detection
        self._setup_paste_hook()

        # Import callbacks (set by app.py)
        self._import_callback = None
        self._import_file_callback = None

        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._graph.widget)

        self.setLayout(layout)

        # Install event filter on graph viewer to capture Tab key for context menu
        self._graph.viewer().installEventFilter(self)
        # Also install on viewport to capture mouse events (right-click)
        self._graph.viewer().viewport().installEventFilter(self)
        # Install on scene to capture connection drags
        self._graph.viewer().scene().installEventFilter(self)

        # Install tooltip blocker
        self._tooltip_blocker = TooltipBlocker()
        self._graph.viewer().installEventFilter(self._tooltip_blocker)
        self._graph.viewer().viewport().installEventFilter(self._tooltip_blocker)

        # Monkey-patch viewer to detect connection drops
        self._patch_viewer_for_connection_search()

        # Fix MMB panning over items
        self._fix_mmb_panning()

    def _patch_viewer_for_connection_search(self):
        """
        Install an event filter to detect when a connection is dropped on empty space.
        Uses Qt event filter pattern instead of monkey-patching for stability.
        """
        self._connection_drop_filter = ConnectionDropFilter(self._graph, self)
        self._graph.viewer().viewport().installEventFilter(self._connection_drop_filter)

        # Install output port MMB filter (for quick SetVariable creation)
        self._output_port_mmb_filter = OutputPortMMBFilter(self._graph, self)
        self._graph.viewer().viewport().installEventFilter(self._output_port_mmb_filter)

    def _fix_mmb_panning(self):
        """
        No-op - removed MMB panning patch as it was causing stability issues.
        NodeGraphQt's default MMB behavior is used instead.
        """
        pass

    def _setup_viewport_culling(self) -> None:
        """
        Wire up viewport culling to graph events for automatic node/pipe culling.

        This connects to:
        - node_created: Register new nodes with culler
        - nodes_deleted: Unregister deleted nodes
        - port_connected: Register new pipes
        - port_disconnected: Unregister deleted pipes
        - Viewport scroll/zoom events via event filter
        """
        try:
            # Connect to node creation/deletion signals
            if hasattr(self._graph, "node_created"):
                self._graph.node_created.connect(self._on_culling_node_created)
            if hasattr(self._graph, "nodes_deleted"):
                self._graph.nodes_deleted.connect(self._on_culling_nodes_deleted)

            # Connect to pipe creation/deletion signals
            if hasattr(self._graph, "port_connected"):
                self._graph.port_connected.connect(self._on_culling_pipe_created)
            if hasattr(self._graph, "port_disconnected"):
                self._graph.port_disconnected.connect(self._on_culling_pipe_deleted)

            # Connect to session_changed signal to clear culler when graph is reset
            if hasattr(self._graph, "session_changed"):
                self._graph.session_changed.connect(self._on_session_changed)

            # Install viewport update timer for smooth culling during pan/zoom
            # Use 33ms (~30 FPS) instead of 16ms (~60 FPS) to reduce CPU overhead
            # while still providing smooth visual updates
            from PySide6.QtCore import QTimer

            self._viewport_update_timer = QTimer(self)
            self._viewport_update_timer.setInterval(33)  # ~30 FPS (reduced from 60 FPS)
            self._viewport_update_timer.timeout.connect(self._update_viewport_culling)
            self._viewport_update_timer.start()

            logger.debug("Viewport culling signals connected")
        except Exception as e:
            logger.warning(f"Could not setup viewport culling: {e}")

    def _on_culling_node_created(self, node) -> None:
        """Register newly created node with culler and update variable picker context."""
        try:
            if hasattr(node, "view") and node.view:
                rect = node.view.sceneBoundingRect()
                self._culler.register_node(node.id, node.view, rect)
        except Exception as e:
            logger.debug(f"Could not register node for culling: {e}")

        # Update variable picker context for all widgets in the node
        self._update_variable_picker_context(node)

    def _update_variable_picker_context(self, node) -> None:
        """
        Update variable picker context for all VariableAwareLineEdit widgets in a node.

        This enables upstream variable detection in the variable picker popup.
        """
        try:
            from casare_rpa.presentation.canvas.graph.node_widgets import (
                update_node_context_for_widgets,
            )

            update_node_context_for_widgets(node)
        except Exception as e:
            logger.debug(f"Could not update variable picker context: {e}")

    def _on_culling_nodes_deleted(self, node_ids) -> None:
        """Unregister deleted nodes from culler."""
        try:
            for node_id in node_ids:
                self._culler.unregister_node(node_id)
        except Exception as e:
            logger.debug(f"Could not unregister nodes from culling: {e}")

    def _on_session_changed(self, *args) -> None:
        """Clear culler when graph session is reset (clear_session called)."""
        try:
            self._culler.clear()
            logger.debug("Viewport culler cleared on session change")
        except Exception as e:
            logger.debug(f"Could not clear culler on session change: {e}")

    def _on_culling_pipe_created(self, input_port, output_port) -> None:
        """Register newly created pipe with culler and propagate control flow frames."""
        try:
            # Get the pipe item from the connection
            # NodeGraphQt stores pipes in the output port
            source_node = None
            target_node = None
            if hasattr(output_port, "connected_pipes"):
                for pipe in output_port.connected_pipes():
                    if (
                        pipe
                        and hasattr(pipe, "input_port")
                        and pipe.input_port() == input_port
                    ):
                        source_node = output_port.node()
                        target_node = input_port.node()
                        if source_node and target_node:
                            pipe_id = f"{source_node.id}:{output_port.name()}>{target_node.id}:{input_port.name()}"
                            self._culler.register_pipe(
                                pipe_id, source_node.id, target_node.id, pipe
                            )
                        break

            # Propagate control flow frame to connected nodes
            if source_node and target_node:
                self._propagate_control_flow_frame(source_node, target_node)

        except Exception as e:
            logger.debug(f"Could not register pipe for culling: {e}")

    def _propagate_control_flow_frame(self, source_node, target_node) -> None:
        """
        Propagate control flow frame membership when nodes are connected.

        If one node is in a control flow frame (For Loop, While Loop, Try/Catch/Finally),
        add the other node to the same frame and trigger auto-resize.
        """
        try:
            # Get control flow frame from either node
            source_frame = getattr(source_node, "control_flow_frame", None)
            target_frame = getattr(target_node, "control_flow_frame", None)

            frame = source_frame or target_frame
            if not frame:
                return  # No control flow frame involved

            # Check if frame is still valid (in scene)
            if not frame.scene():
                return

            # Add nodes to frame if not already members
            if source_frame and not target_frame:
                # Target node is joining the frame
                frame.add_node(target_node)
                target_node.control_flow_frame = frame
                logger.debug(
                    f"Added {target_node.name()} to control flow frame '{frame.frame_title}'"
                )

            elif target_frame and not source_frame:
                # Source node is joining the frame
                frame.add_node(source_node)
                source_node.control_flow_frame = frame
                logger.debug(
                    f"Added {source_node.name()} to control flow frame '{frame.frame_title}'"
                )

            # Trigger frame bounds update (auto-resize)
            if hasattr(frame, "_check_node_bounds"):
                frame._check_node_bounds()

        except Exception as e:
            logger.debug(f"Could not propagate control flow frame: {e}")

    def _on_culling_pipe_deleted(self, input_port, output_port) -> None:
        """Unregister deleted pipe from culler."""
        try:
            source_node = output_port.node() if output_port else None
            target_node = input_port.node() if input_port else None
            if source_node and target_node:
                pipe_id = f"{source_node.id}:{output_port.name()}>{target_node.id}:{input_port.name()}"
                self._culler.unregister_pipe(pipe_id)
        except Exception as e:
            logger.debug(f"Could not unregister pipe from culling: {e}")

    def _update_viewport_culling(self) -> None:
        """Update culling based on current viewport (called by timer)."""
        try:
            viewer = self._graph.viewer()
            if viewer and viewer.viewport():
                # Get visible viewport rect in scene coordinates
                viewport_rect = viewer.mapToScene(
                    viewer.viewport().rect()
                ).boundingRect()
                self._culler.update_viewport(viewport_rect)
        except Exception:
            # Suppress errors during startup
            pass

    def _setup_graph(self) -> None:
        """Configure the node graph settings and appearance."""
        # Set graph background color to VSCode Dark+ editor background
        self._graph.set_background_color(
            30, 30, 30
        )  # #1E1E1E (VSCode editor background)

        # Set grid styling
        self._graph.set_grid_mode(1)  # Show grid

        # Set graph properties
        self._graph.set_pipe_style(1)  # Curved pipes (CURVED = 1, not 2)

        # Configure selection and connection colors
        # Get the viewer to apply custom colors
        viewer = self._graph.viewer()

        # Register custom pipe class for connection labels and output preview
        try:
            # Always set - don't check hasattr, just assign directly
            viewer._PIPE_ITEM = CasarePipe
        except Exception as e:
            logger.warning(f"Could not register custom pipe: {e}")

        # Set selection colors - transparent overlay, thick yellow border
        if hasattr(viewer, "_node_sel_color"):
            viewer._node_sel_color = (0, 0, 0, 0)  # Transparent selection overlay
        if hasattr(viewer, "_node_sel_border_color"):
            viewer._node_sel_border_color = (255, 215, 0, 255)  # Bright yellow border

        # Set pipe colors - light gray curved lines
        if hasattr(viewer, "_pipe_color"):
            viewer._pipe_color = (100, 100, 100, 255)  # Gray pipes
        if hasattr(viewer, "_live_pipe_color"):
            viewer._live_pipe_color = (100, 100, 100, 255)  # Gray when dragging

        # Configure port colors to differentiate input/output
        # Input ports (left side) - cyan/teal color
        # Output ports (right side) - orange/amber color
        # Override the default port colors through the viewer
        if hasattr(viewer, "_port_color"):
            viewer._port_color = (100, 181, 246, 255)  # Light blue for ports
        if hasattr(viewer, "_port_border_color"):
            viewer._port_border_color = (66, 165, 245, 255)  # Darker blue border

        # ==================== PERFORMANCE OPTIMIZATIONS ====================

        # Qt rendering optimizations for high FPS (60/120/144 Hz support)
        from PySide6.QtWidgets import QGraphicsView
        from PySide6.QtCore import Qt

        # Enable optimization flags
        viewer.setOptimizationFlag(
            QGraphicsView.OptimizationFlag.DontSavePainterState, True
        )
        viewer.setOptimizationFlag(
            QGraphicsView.OptimizationFlag.DontAdjustForAntialiasing, True
        )
        viewer.setOptimizationFlag(
            QGraphicsView.OptimizationFlag.IndirectPainting, True
        )

        # Full viewport updates - prevents glitches during zoom/pan
        # Note: SmartViewportUpdate/MinimalViewportUpdate + CacheBackground causes
        # rendering artifacts because cached content doesn't invalidate on transforms
        viewer.setViewportUpdateMode(
            QGraphicsView.ViewportUpdateMode.FullViewportUpdate
        )

        # Disable background caching - incompatible with zoom/pan transforms
        viewer.setCacheMode(QGraphicsView.CacheModeFlag(0))

        # High refresh rate optimizations
        viewer.viewport().setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        viewer.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)

        # GPU-accelerated rendering (with automatic fallback to CPU)
        try:
            from PySide6.QtOpenGLWidgets import QOpenGLWidget
            from PySide6.QtGui import QSurfaceFormat

            # Configure OpenGL format for high performance
            gl_format = QSurfaceFormat()
            gl_format.setVersion(3, 3)  # OpenGL 3.3+ for modern features
            gl_format.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
            gl_format.setSwapBehavior(QSurfaceFormat.SwapBehavior.DoubleBuffer)
            gl_format.setSwapInterval(
                0
            )  # Disable vsync for maximum FPS (120/144/240 Hz support)
            gl_format.setSamples(4)  # 4x MSAA antialiasing

            # Create OpenGL viewport
            gl_widget = QOpenGLWidget()
            gl_widget.setFormat(gl_format)

            viewer.setViewport(gl_widget)

            # Set as default format for future widgets
            QSurfaceFormat.setDefaultFormat(gl_format)
        except Exception as e:
            logger.warning(f"GPU rendering unavailable, using CPU rendering: {e}")
            # Continue with default CPU-based QPainter rendering

    @property
    def graph(self) -> NodeGraph:
        """
        Get the underlying NodeGraph instance.

        Returns:
            NodeGraph instance
        """
        return self._graph

    def clear_graph(self) -> None:
        """Clear all nodes and connections from the graph."""
        self._graph.clear_session()

    def fit_to_selection(self) -> None:
        """Fit the view to the selected nodes."""
        self._graph.fit_to_selection()

    def reset_zoom(self) -> None:
        """Reset zoom to 100%."""
        self._graph.reset_zoom()

    def zoom_in(self) -> None:
        """Zoom in the graph view."""
        current_zoom = self._graph.get_zoom()
        self._graph.set_zoom(current_zoom + 0.1)

    def zoom_out(self) -> None:
        """Zoom out the graph view."""
        current_zoom = self._graph.get_zoom()
        self._graph.set_zoom(current_zoom - 0.1)

    def center_on_nodes(self) -> None:
        """Center the view on all nodes."""
        nodes = self._graph.all_nodes()
        if nodes:
            self._graph.center_on(nodes)

    @property
    def selection(self) -> SelectionManager:
        """
        Get the selection manager.

        Returns:
            SelectionManager instance
        """
        return self._selection

    def get_selected_nodes(self) -> list:
        """
        Get the currently selected nodes.

        Returns:
            List of selected node objects
        """
        return self._selection.get_selected_nodes()

    def clear_selection(self) -> None:
        """Clear node selection."""
        self._selection.clear_selection()

    @property
    def auto_connect(self) -> AutoConnectManager:
        """
        Get the auto-connect manager.

        Returns:
            AutoConnectManager instance
        """
        return self._auto_connect

    @property
    def node_insert(self) -> NodeInsertManager:
        """
        Get the node insert manager.

        Returns:
            NodeInsertManager instance
        """
        return self._node_insert

    def set_auto_connect_enabled(self, enabled: bool) -> None:
        """
        Enable or disable the auto-connect feature.

        Args:
            enabled: Whether to enable auto-connect
        """
        self._auto_connect.set_active(enabled)

    def is_auto_connect_enabled(self) -> bool:
        """
        Check if auto-connect is enabled.

        Returns:
            True if auto-connect is enabled
        """
        return self._auto_connect.is_active()

    def set_auto_connect_distance(self, distance: float) -> None:
        """
        Set the maximum distance for auto-connect suggestions.

        Args:
            distance: Maximum distance in pixels
        """
        self._auto_connect.set_max_distance(distance)

    @property
    def quick_actions(self) -> NodeQuickActions:
        """
        Get the quick actions manager.

        Returns:
            NodeQuickActions instance
        """
        return self._quick_actions

    def eventFilter(self, obj, event):
        """
        Event filter to capture Tab key press and right-click for context menu.

        Args:
            obj: Object that received the event
            event: The event

        Returns:
            True if event was handled, False otherwise
        """
        # Clear focus from text widgets when mouse enters canvas
        # This prevents numpad shortcuts (1-6) from typing into focused widgets
        if event.type() == QEvent.Type.Enter:
            focus_widget = QApplication.focusWidget()
            if isinstance(focus_widget, (QLineEdit, QTextEdit)):
                # Check if focus widget is inside a node (embedded in graphics scene)
                # We only clear focus for widgets embedded in the canvas, not the properties panel
                parent = focus_widget.parent()
                while parent:
                    if hasattr(parent, "scene") and callable(parent.scene):
                        # Widget is in a QGraphicsProxyWidget - clear focus
                        focus_widget.clearFocus()
                        break
                    parent = getattr(parent, "parent", lambda: None)()

        # Capture right-click position BEFORE context menu is shown
        # We intercept MouseButtonPress with RightButton to capture position early
        if event.type() == event.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.RightButton:
                viewer = self._graph.viewer()

                # Cancel live connection on right-click
                if hasattr(viewer, "_LIVE_PIPE") and viewer._LIVE_PIPE.isVisible():
                    viewer.end_live_connection()
                    logger.debug("Right-click - cancelled live connection")
                    return True

                # Capture the position where right-click occurred
                if hasattr(event, "globalPos"):
                    global_pos = event.globalPos()
                else:
                    global_pos = event.globalPosition().toPoint()
                scene_pos = viewer.mapToScene(viewer.mapFromGlobal(global_pos))

                # Store position on the context menu for node creation
                context_menu = self._graph.get_context_menu("graph")
                if context_menu and context_menu.qmenu:
                    context_menu.qmenu._initial_scene_pos = scene_pos

                # Let the event propagate to show the menu
                return False

        if event.type() == event.Type.KeyPress:
            key_event = event
            if key_event.key() == Qt.Key.Key_Tab:
                # Show context menu at cursor position
                viewer = self._graph.viewer()
                cursor_pos = viewer.cursor().pos()

                # Check if we're dragging a connection
                source_port = None
                live_pipe_was_visible = False
                if hasattr(viewer, "_LIVE_PIPE") and viewer._LIVE_PIPE.isVisible():
                    # Save the source port for auto-connection
                    source_port = (
                        viewer._start_port if hasattr(viewer, "_start_port") else None
                    )
                    if source_port:
                        live_pipe_was_visible = True
                        # Hide the connection line while menu is open
                        viewer._LIVE_PIPE.setVisible(False)
                        logger.debug(
                            "Tab pressed during connection drag - hiding live pipe"
                        )

                # Get the context menu and show it
                context_menu = self._graph.get_context_menu("graph")
                if context_menu and context_menu.qmenu:
                    # Capture initial scene position BEFORE showing the menu
                    # This is stored so nodes are created at the original position
                    scene_pos = viewer.mapToScene(viewer.mapFromGlobal(cursor_pos))
                    context_menu.qmenu._initial_scene_pos = scene_pos

                    # If dragging a connection, setup auto-connect
                    tab_handler_executed = [False]
                    tab_on_node_created = None

                    if source_port:

                        def tab_on_node_created(node):
                            """Auto-connect newly created node to source port."""
                            if tab_handler_executed[0]:
                                return
                            tab_handler_executed[0] = True
                            try:
                                self._auto_connect_new_node(node, source_port)
                                # End the live connection since we've completed it
                                viewer.end_live_connection()
                                logger.info("Auto-connected node from Tab search")
                            except Exception as e:
                                logger.error(f"Failed to auto-connect node: {e}")

                        # Connect temporary handler for this node creation
                        if hasattr(self._graph, "node_created"):
                            self._graph.node_created.connect(tab_on_node_created)

                    try:
                        context_menu.qmenu.exec(cursor_pos)
                    finally:
                        # ALWAYS disconnect handler after menu closes
                        if tab_on_node_created and hasattr(self._graph, "node_created"):
                            try:
                                self._graph.node_created.disconnect(tab_on_node_created)
                            except (RuntimeError, TypeError):
                                pass

                    # If menu was cancelled and we were dragging, end the connection
                    if live_pipe_was_visible and not tab_handler_executed[0]:
                        viewer.end_live_connection()
                        logger.debug("Tab menu cancelled - ending live connection")

                return True  # Event handled

            # Handle Escape key to cancel live connection
            if key_event.key() == Qt.Key.Key_Escape:
                viewer = self._graph.viewer()
                if hasattr(viewer, "_LIVE_PIPE") and viewer._LIVE_PIPE.isVisible():
                    viewer.end_live_connection()
                    logger.debug("ESC pressed - cancelled live connection")
                    return True

            # Handle X key or Delete key to delete selected frames
            # Note: X key (88) and Delete key
            if key_event.key() == Qt.Key.Key_X or key_event.key() == Qt.Key.Key_Delete:
                logger.debug(f"Frame delete key pressed: {key_event.key()}")
                if self._delete_selected_frames():
                    return True  # Event handled if frames were deleted

            # Also handle lowercase 'x' (key code 88)
            if key_event.text().lower() == "x":
                logger.debug("X key text detected")
                if self._delete_selected_frames():
                    return True

        return super().eventFilter(obj, event)

    def _delete_selected_frames(self) -> bool:
        """
        Delete any selected frames in the scene.

        Returns:
            True if any frames were deleted, False otherwise
        """
        return self._selection.delete_selected_frames()

    # =========================================================================
    # CONNECTION VALIDATION
    # =========================================================================

    def _setup_connection_validation(self) -> None:
        """
        Setup connection validation hooks.

        Connects to the port_connected signal to validate connections
        and block invalid ones.
        """
        try:
            # Connect to the port_connected signal if available
            if hasattr(self._graph, "port_connected"):
                self._graph.port_connected.connect(self._on_port_connected)
                logger.debug("Connection validation enabled")
        except Exception as e:
            logger.warning(f"Could not setup connection validation: {e}")

    def _on_port_connected(self, input_port, output_port) -> None:
        """
        Handle port connection event.

        Validates the connection and disconnects if types are incompatible.

        Args:
            input_port: The input (target) port
            output_port: The output (source) port
        """
        if not self._validator:
            return

        try:
            # Get the node objects
            source_node = output_port.node()
            target_node = input_port.node()

            # Check if nodes support typed ports
            if not hasattr(source_node, "get_port_type") or not hasattr(
                target_node, "get_port_type"
            ):
                return  # Can't validate, allow connection

            # Validate the connection
            validation = self._validator.validate_connection(
                source_node, output_port.name(), target_node, input_port.name()
            )

            if not validation.is_valid:
                # Block the connection - disconnect immediately
                logger.warning(f"Connection blocked: {validation.message}")

                try:
                    # CRITICAL: Use push_undo=False and emit_signal=False
                    # We're inside a signal handler from the same connection event.
                    # Pushing to undo stack here corrupts NodeGraphQt's internal state
                    # and prevents future connections from the same port.
                    output_port.disconnect_from(
                        input_port, push_undo=False, emit_signal=False
                    )
                except Exception as e:
                    logger.error(f"Failed to disconnect invalid connection: {e}")

                # Emit signal for UI feedback
                self.connection_blocked.emit(validation.message)

        except Exception as e:
            logger.debug(f"Connection validation error: {e}")

    # =========================================================================
    # PASTE HOOK FOR DUPLICATE ID DETECTION
    # =========================================================================

    def _setup_paste_hook(self) -> None:
        """
        Setup hooks to regenerate node IDs after paste operations.

        NodeGraphQt emits node_created for each pasted node.
        We intercept this to detect and fix duplicate IDs.

        IMPORTANT: We use a deferred check (QTimer.singleShot) because NodeGraphQt
        restores properties AFTER the node_created signal fires. The deferred check
        runs after the current event loop iteration, ensuring properties are restored.
        """
        try:
            if hasattr(self._graph, "node_created"):
                self._graph.node_created.connect(self._on_node_created_check_duplicate)
                logger.debug("Paste hook for duplicate ID detection enabled")
        except Exception as e:
            logger.warning(f"Could not setup paste hook: {e}")

    def _on_node_created_check_duplicate(self, node) -> None:
        """
        Handle node creation/paste events.

        - Handles composite nodes (e.g., For Loop creates Start + End)
        - Schedules deferred duplicate ID check after properties are restored
        - Syncs visual node properties to casare_node.config after paste
        This prevents self-connection errors from copy/paste operations.
        """
        from PySide6.QtCore import QTimer

        # Check if this is a composite node that creates multiple nodes
        visual_class = node.__class__
        if getattr(visual_class, "COMPOSITE_NODE", False):
            logger.info(
                f"Detected composite node: {visual_class.__name__}, handling creation of multiple nodes"
            )
            self._handle_composite_node_creation(node)
            return

        # CRITICAL: Use deferred check because NodeGraphQt restores properties
        # AFTER the node_created signal fires during paste/duplicate operations.
        # QTimer.singleShot(0, ...) runs after the current event loop iteration,
        # ensuring all properties have been restored from the clipboard/serialization.
        QTimer.singleShot(0, lambda: self._deferred_duplicate_check(node))

    def _deferred_duplicate_check(self, node) -> None:
        """
        Deferred duplicate ID check after properties are fully restored.

        This runs after the event loop iteration, ensuring NodeGraphQt has
        finished restoring properties from paste/duplicate operations.

        Args:
            node: The newly created/pasted visual node
        """
        from casare_rpa.utils.id_generator import generate_node_id

        # Verify node still exists (might have been deleted)
        if node not in self._graph.all_nodes():
            return

        # Get current node_id property (now should be restored if pasted)
        current_id = node.get_property("node_id")

        # Get or create casare_node
        casare_node = self._ensure_casare_node(node)

        if not casare_node:
            logger.warning(
                f"Could not get/create casare_node for {node.name()} - "
                f"node may not execute correctly"
            )
            return

        # If current_id is empty, this is a fresh node creation - ensure ID is set
        if not current_id:
            # Sync casare_node's ID to the visual property
            node.set_property("node_id", casare_node.node_id)
            logger.debug(f"Set node_id for new node: {casare_node.node_id}")
        else:
            # Check if this ID is a duplicate (from paste/duplicate operation)
            is_duplicate = self._check_for_duplicate_id(node, current_id)

            if is_duplicate:
                # Generate new unique ID
                node_type = (
                    getattr(casare_node, "node_type", None)
                    or type(casare_node).__name__
                )
                new_id = generate_node_id(node_type)

                # Update both locations synchronously
                casare_node.node_id = new_id
                node.set_property("node_id", new_id)

                logger.info(f"Regenerated duplicate node ID: {current_id} -> {new_id}")
            else:
                # Not a duplicate, but ensure casare_node has the same ID as visual property
                if casare_node.node_id != current_id:
                    casare_node.node_id = current_id
                    logger.debug(
                        f"Synced casare_node ID to visual property: {current_id}"
                    )

        # CRITICAL: Always sync visual node properties to casare_node.config
        # This ensures pasted nodes retain their configured values for:
        # - Same-canvas paste (duplicate ID detected)
        # - Cross-canvas paste (no duplicate, but config needs sync)
        # - Workflow load (deserializer sets properties, need sync to config)
        self._sync_visual_properties_to_casare_node(node, casare_node)

    def _ensure_casare_node(self, node):
        """
        Ensure the visual node has a linked casare_node, creating one if needed.

        Args:
            node: The visual node

        Returns:
            The casare_node instance or None if creation failed
        """
        # Try to get existing casare_node
        casare_node = (
            node.get_casare_node() if hasattr(node, "get_casare_node") else None
        )

        if casare_node:
            return casare_node

        # No casare_node - try to create one
        try:
            from casare_rpa.presentation.canvas.graph.node_registry import (
                get_node_factory,
                get_casare_node_mapping,
            )

            # Check if this visual node type has a casare_node mapping
            mapping = get_casare_node_mapping()
            if type(node) not in mapping:
                # Visual-only node (e.g., comment, sticky note) - no casare_node needed
                logger.debug(
                    f"Visual-only node {type(node).__name__} - no casare_node needed"
                )
                return None

            factory = get_node_factory()
            casare_node = factory.create_casare_node(node)

            if casare_node:
                logger.info(
                    f"Created missing casare_node for {node.name()}: {casare_node.node_id}"
                )
            else:
                logger.error(f"Failed to create casare_node for {node.name()}")

            return casare_node

        except Exception as e:
            logger.error(f"Error creating casare_node for {node.name()}: {e}")
            return None

    def _check_for_duplicate_id(self, node, node_id: str) -> bool:
        """
        Check if another node already has the same node_id.

        Args:
            node: The node to check
            node_id: The node_id to check for duplicates

        Returns:
            True if another node has the same ID, False otherwise
        """
        for other_node in self._graph.all_nodes():
            if other_node is node:
                continue

            other_id = other_node.get_property("node_id")
            if other_id == node_id:
                return True

        return False

    def _sync_visual_properties_to_casare_node(self, visual_node, casare_node) -> None:
        """
        Sync visual node properties to casare_node.config after paste.

        When pasting, NodeGraphQt restores visual properties but the casare_node
        is newly created with empty config. This syncs the values.

        Args:
            visual_node: The pasted visual node with restored properties
            casare_node: The newly created casare_node needing config sync
        """
        try:
            # Get all custom properties from visual node model
            if not hasattr(visual_node, "model"):
                return

            model = visual_node.model
            custom_props = list(model.custom_properties.keys()) if model else []

            synced_count = 0
            for prop_name in custom_props:
                # Skip internal/meta properties
                if prop_name.startswith("_") or prop_name in (
                    "node_id",
                    "name",
                    "color",
                    "pos",
                    "disabled",
                    "selected",
                    "visible",
                    "width",
                    "height",
                ):
                    continue

                try:
                    prop_value = visual_node.get_property(prop_name)
                    if prop_value is not None:
                        # Sync to casare_node config
                        casare_node.config[prop_name] = prop_value
                        synced_count += 1
                except Exception:
                    pass  # Property access failed, skip

            if synced_count > 0:
                logger.debug(
                    f"Synced {synced_count} properties to pasted node "
                    f"{casare_node.node_id}"
                )

        except Exception as e:
            logger.warning(f"Failed to sync properties for pasted node: {e}")

    def _handle_composite_node_creation(self, composite_node) -> None:
        """
        Handle creation of composite nodes (e.g., For Loop creates Start + End).

        Delegates to CompositeNodeCreator for the actual node creation and pairing.

        Args:
            composite_node: The composite marker node that was created
        """
        self._composite_creator.handle_composite_node(composite_node)

    # =========================================================================
    # IMPORT CALLBACKS
    # =========================================================================

    def set_import_callback(self, callback) -> None:
        """
        Set callback for importing workflow data.

        Args:
            callback: Function(data: dict, position: tuple) -> ImportResult
        """
        self._import_callback = callback

    def set_import_file_callback(self, callback) -> None:
        """
        Set callback for importing workflow from file.

        Args:
            callback: Function(file_path: str, position: tuple) -> None
        """
        self._import_file_callback = callback

    # =========================================================================
    # DRAG AND DROP SUPPORT
    # =========================================================================

    def setup_drag_drop(self) -> None:
        """
        Enable drag and drop support for importing workflow JSON files.

        Must be called after widget is initialized. Enables dropping
        .json files directly onto the canvas to import nodes.
        """
        # Enable drops on the graph viewer widget
        viewer = self._graph.viewer()
        viewer.setAcceptDrops(True)

        # Override drag/drop events on the viewer
        viewer.dragEnterEvent = self._handle_drag_enter
        viewer.dragMoveEvent = self._handle_drag_move
        viewer.dropEvent = self._handle_drop

        logger.debug("Drag-drop support enabled for workflow import")

    def _handle_drag_enter(self, event) -> None:
        """Handle drag enter event - accept JSON files and node library drags."""
        mime_data = event.mimeData()

        # Accept node library drags
        if mime_data.hasFormat("application/x-casare-node"):
            event.acceptProposedAction()
            return

        # Accept casare_node: text format from node library
        if mime_data.hasText():
            text = mime_data.text()
            if text.startswith("casare_node:"):
                event.acceptProposedAction()
                return

        if mime_data.hasUrls():
            for url in mime_data.urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if file_path.lower().endswith(".json"):
                        event.acceptProposedAction()
                        return

        # Also accept plain text (for JSON text drops)
        if mime_data.hasText():
            text = mime_data.text()
            if text.strip().startswith("{") and '"nodes"' in text:
                event.acceptProposedAction()
                return

        event.ignore()

    def _handle_drag_move(self, event) -> None:
        """Handle drag move event."""
        # Same logic as drag enter
        self._handle_drag_enter(event)

    def _handle_drop(self, event) -> None:
        """Handle drop event - import workflow file, JSON text, or node library node."""

        mime_data = event.mimeData()
        drop_pos = event.position() if hasattr(event, "position") else event.posF()

        # Convert to scene coordinates for node positioning
        viewer = self._graph.viewer()
        scene_pos = viewer.mapToScene(drop_pos.toPoint())
        position = (scene_pos.x(), scene_pos.y())

        # Handle node library drops (application/x-casare-node)
        if mime_data.hasFormat("application/x-casare-node"):
            data = mime_data.data("application/x-casare-node").data().decode()
            parts = data.split("|")
            if len(parts) >= 1:
                node_type = parts[0]
                identifier = parts[1] if len(parts) > 1 else ""
                self._create_node_at_position(node_type, identifier, position)
                event.acceptProposedAction()
                return

        # Handle casare_node: text format from node library
        if mime_data.hasText():
            text = mime_data.text()
            if text.startswith("casare_node:"):
                parts = text.split(":")
                if len(parts) >= 2:
                    node_type = parts[1]
                    identifier = parts[2] if len(parts) > 2 else ""
                    self._create_node_at_position(node_type, identifier, position)
                    event.acceptProposedAction()
                    return

        # Handle file drops
        if mime_data.hasUrls():
            for url in mime_data.urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if file_path.lower().endswith(".json"):
                        if self._import_file_callback:
                            self._import_file_callback(file_path, position)
                        event.acceptProposedAction()
                        return

        # Handle JSON text drops
        if mime_data.hasText():
            text = mime_data.text()
            if text.strip().startswith("{"):
                try:
                    import orjson

                    data = orjson.loads(text)
                    if "nodes" in data:
                        if self._import_callback:
                            self._import_callback(data, position)
                        event.acceptProposedAction()
                        return
                except Exception as e:
                    logger.warning(f"Dropped text is not valid JSON: {e}")

        event.ignore()

    def _create_node_at_position(
        self, node_type: str, identifier: str, position: tuple
    ) -> None:
        """Create a node at the specified position from a drag-drop operation."""
        self._creation_helper.create_node_at_position(node_type, identifier, position)

    def _show_connection_search(self, source_port, scene_pos):
        """
        Show node context menu (same as Tab search) and auto-connect created node.

        Args:
            source_port: The port that was dragged from
            scene_pos: Scene position where connection was released
        """
        # Get the context menu (same as Tab search)
        context_menu = self._graph.get_context_menu("graph")
        if not context_menu or not context_menu.qmenu:
            logger.warning("Context menu not available")
            return

        # Store scene position for node creation
        context_menu.qmenu._initial_scene_pos = scene_pos

        # Store source port for auto-connection after node is created
        # Use a flag to track if handler already executed
        handler_executed = [False]  # Use list to allow mutation in nested function

        def on_node_created(node):
            """Auto-connect newly created node to source port."""
            if handler_executed[0]:
                return  # Already ran, skip
            handler_executed[0] = True
            try:
                self._auto_connect_new_node(node, source_port)
            except Exception as e:
                logger.error(f"Failed to auto-connect node: {e}")

        # Connect temporary handler for this node creation
        if hasattr(self._graph, "node_created"):
            self._graph.node_created.connect(on_node_created)

        # Show context menu at the release position (map scene to global coordinates)
        viewer = self._graph.viewer()
        view_pos = viewer.mapFromScene(scene_pos)
        global_pos = viewer.mapToGlobal(view_pos)

        try:
            context_menu.qmenu.exec(global_pos)
        finally:
            # ALWAYS disconnect handler after menu closes (whether node created or cancelled)
            try:
                self._graph.node_created.disconnect(on_node_created)
            except (RuntimeError, TypeError):
                pass  # Already disconnected or never connected

    def _auto_connect_new_node(self, new_node, source_port_item):
        """
        Auto-connect a newly created node to the source port.

        Args:
            new_node: The newly created node
            source_port_item: The port item that was dragged from (PortItem from viewer)
        """
        self._creation_helper.auto_connect_new_node(new_node, source_port_item)

    def _create_set_variable_for_port(self, source_port_item):
        """
        Create a SetVariable node connected to the clicked output port.

        Args:
            source_port_item: The output port item that was clicked (PortItem from viewer)
        """
        # Update helper offsets if they've been set on this widget
        if hasattr(self, "_set_variable_y_offset"):
            self._creation_helper.y_offset = self._set_variable_y_offset
        if hasattr(self, "_set_variable_x_gap"):
            self._creation_helper.x_gap = self._set_variable_x_gap

        self._creation_helper.create_set_variable_for_port(source_port_item)
