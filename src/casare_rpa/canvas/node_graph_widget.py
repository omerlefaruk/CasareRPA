"""
Node graph widget wrapper for NodeGraphQt integration.

This module provides a wrapper around NodeGraphQt's NodeGraph
to integrate it with the PySide6 application.
"""

from typing import Optional

from PySide6.QtWidgets import QWidget, QVBoxLayout, QComboBox
from PySide6.QtGui import QPen, QPainter, QPainterPath, QColor, QKeyEvent
from PySide6.QtCore import Qt, QObject, QEvent, Signal
from NodeGraphQt import NodeGraph
from NodeGraphQt.qgraphics.node_base import NodeItem

from loguru import logger

from ..utils.config import GUI_THEME
from .auto_connect import AutoConnectManager
from .connection_cutter import ConnectionCutter
from .node_quick_actions import NodeQuickActions
from .custom_pipe import CasarePipe
from .snippet_breadcrumb_bar import SnippetBreadcrumbBar
from .snippet_navigation import SnippetNavigationManager, set_navigation_manager
from .parameter_drop_zone import ParameterDropZone
from .parameter_naming_dialog import ParameterNamingDialog
from .property_drag_enabler import enable_property_dragging

# Import connection validator for strict type checking
try:
    from .connection_validator import ConnectionValidator, get_connection_validator
    HAS_CONNECTION_VALIDATOR = True
except ImportError:
    HAS_CONNECTION_VALIDATOR = False
    logger.warning("ConnectionValidator not available - connection validation disabled")


# ============================================================================
# FIX: Combo box dropdown z-order issue in QGraphicsProxyWidget
# ============================================================================
# When QComboBox is embedded in a QGraphicsProxyWidget, the dropdown popup
# can get clipped by other widgets in the same node. This fix ensures the
# popup appears as a top-level window above all graphics items.

try:
    from NodeGraphQt.widgets.node_widgets import NodeComboBox
    from NodeGraphQt.constants import Z_VAL_NODE_WIDGET

    # Store original z-value for restoration
    COMBO_RAISED_Z = 10000  # Very high z-value when popup is open

    _original_node_combo_init = NodeComboBox.__init__

    def _patched_node_combo_init(self, parent=None, name='', label='', items=None):
        """Patched init to fix combo dropdown z-order."""
        _original_node_combo_init(self, parent, name, label, items)
        self._original_z = self.zValue()

        # Get the combo widget and patch showPopup/hidePopup
        combo = self.get_custom_widget()
        if combo and isinstance(combo, QComboBox):
            node_widget = self  # Capture reference for closures

            # Store original methods
            _original_show_popup = combo.showPopup
            _original_hide_popup = combo.hidePopup

            def patched_show_popup():
                # Raise z-value when popup opens
                node_widget.setZValue(COMBO_RAISED_Z)
                _original_show_popup()

            def patched_hide_popup():
                _original_hide_popup()
                # Restore original z-value when popup closes
                node_widget.setZValue(node_widget._original_z)

            combo.showPopup = patched_show_popup
            combo.hidePopup = patched_hide_popup

    NodeComboBox.__init__ = _patched_node_combo_init
    logger.debug("Patched NodeComboBox for proper dropdown z-order")

except Exception as e:
    logger.warning(f"Could not patch NodeComboBox: {e}")


# ============================================================================
# FIX: Checkbox styling in nodes - dark blue with white checkmark
# ============================================================================
try:
    from NodeGraphQt.widgets.node_widgets import NodeCheckBox
    from pathlib import Path

    # Get checkmark asset path
    CHECKMARK_PATH = (Path(__file__).parent / "assets" / "checkmark.svg").as_posix()

    _original_node_checkbox_init = NodeCheckBox.__init__

    def _patched_node_checkbox_init(self, parent=None, name='', label='', text='', state=False):
        """Patched init to add dark blue styling with white checkmark."""
        _original_node_checkbox_init(self, parent, name, label, text, state)

        # Get the checkbox widget and add custom styling
        checkbox = self.get_custom_widget()
        if checkbox:
            # Apply dark blue checkbox styling with white checkmark
            checkbox_style = f"""
                QCheckBox::indicator {{
                    width: 18px;
                    height: 18px;
                    border: 2px solid #3E3E42;
                    border-radius: 3px;
                    background-color: #252526;
                }}

                QCheckBox::indicator:unchecked:hover {{
                    border-color: #0063B1;
                }}

                QCheckBox::indicator:checked {{
                    background-color: #0063B1;
                    border-color: #0063B1;
                    image: url({CHECKMARK_PATH});
                }}

                QCheckBox::indicator:checked:hover {{
                    background-color: #005A9E;
                    border-color: #005A9E;
                }}
            """
            # Append to existing stylesheet
            existing_style = checkbox.styleSheet()
            checkbox.setStyleSheet(existing_style + checkbox_style)

    NodeCheckBox.__init__ = _patched_node_checkbox_init
    logger.debug("Patched NodeCheckBox for dark blue styling with white checkmark")

except Exception as e:
    logger.warning(f"Could not patch NodeCheckBox: {e}")


class TooltipBlocker(QObject):
    """Event filter to block tooltips."""
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.ToolTip:
            return True
        return False


# Monkey-patch NodeItem to use thicker selection border and rounded corners
_original_paint = NodeItem.paint

def _patched_paint(self, painter, option, widget):
    """Custom paint with thicker yellow border and rounded corners."""
    # Temporarily clear selection for child items to prevent dotted boxes
    option_copy = option.__class__(option)
    option_copy.state &= ~option_copy.state.State_Selected
    
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    
    # Get bounding rect
    rect = self.boundingRect()
    
    # Determine colors
    bg_color = QColor(*self.color)
    border_color = QColor(*self.border_color)
    
    if self.selected:
        # VSCode-style selection: 3px blue border
        border_width = 3.0
        border_color = QColor(0, 122, 204, 255)  # VSCode focus border (#007ACC)
        # Keep background the same (no overlay)
    else:
        border_width = 1.0
    
    # Create rounded rectangle path with 8px radius
    radius = 8.0
    path = QPainterPath()
    path.addRoundedRect(rect, radius, radius)
    
    # Fill background
    painter.fillPath(path, bg_color)
    
    # Draw border
    pen = QPen(border_color, border_width)
    pen.setCosmetic(self.viewer().get_zoom() < 0.0)
    painter.strokePath(path, pen)
    
    painter.restore()
    
    # Draw child items (ports, text, widgets) without selection indicators
    for child in self.childItems():
        if child.isVisible():
            painter.save()
            painter.translate(child.pos())
            child.paint(painter, option_copy, widget)  # Use option without selection state
            painter.restore()

NodeItem.paint = _patched_paint





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
        from .viewport_culling import ViewportCullingManager
        self._culler = ViewportCullingManager(
            cell_size=500,
            margin=200
        )
        self._culler.set_enabled(True)
        logger.info("Viewport culling enabled for performance optimization")

        # Create auto-connect manager
        self._auto_connect = AutoConnectManager(self._graph, self)

        # Create connection cutter (Y + LMB drag to cut connections)
        self._connection_cutter = ConnectionCutter(self._graph, self)

        # Create quick actions for node context menu
        self._quick_actions = NodeQuickActions(self._graph, self)

        # Wire up auto-connect reference so quick actions can check drag state
        # This allows RMB to confirm auto-connect while dragging
        self._quick_actions.set_auto_connect_manager(self._auto_connect)

        # Setup connection validator for strict type checking
        self._validator = get_connection_validator() if HAS_CONNECTION_VALIDATOR else None
        if self._validator:
            self._setup_connection_validation()

        # Setup paste hook for duplicate ID detection
        self._setup_paste_hook()

        # Enable property dragging for snippet parameter creation
        enable_property_dragging()

        # Import callbacks (set by app.py)
        self._import_callback = None
        self._import_file_callback = None

        # Create snippet navigation system
        self._snippet_breadcrumb = SnippetBreadcrumbBar(self)
        self._navigation_manager = SnippetNavigationManager(self)

        # Set as global navigation manager
        set_navigation_manager(self._navigation_manager)

        # Create parameter drop zone (shown only when inside snippet)
        self._parameter_drop_zone = ParameterDropZone(self)
        self._parameter_drop_zone.setVisible(False)  # Hidden by default

        # Connect navigation signals
        self._navigation_manager.navigation_changed.connect(self._on_navigation_changed)
        self._snippet_breadcrumb.level_clicked.connect(self._on_breadcrumb_clicked)

        # Connect drop zone signal
        self._parameter_drop_zone.parameter_requested.connect(self._on_parameter_requested)

        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._snippet_breadcrumb)  # Breadcrumb at top
        layout.addWidget(self._parameter_drop_zone)  # Drop zone below breadcrumb
        layout.addWidget(self._graph.widget)  # Graph below

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
        Monkey-patch the viewer's mouseReleaseEvent to detect connection drops.
        """
        viewer = self._graph.viewer()
        original_mouse_release = viewer.mouseReleaseEvent

        def patched_mouse_release(event):
            # Check if LMB release with live pipe (MUST check BEFORE calling original)
            if event.button() == Qt.MouseButton.LeftButton:
                # Check for _LIVE_PIPE (uppercase!) visibility
                if hasattr(viewer, '_LIVE_PIPE') and viewer._LIVE_PIPE.isVisible():
                    logger.debug("Live pipe detected during mouse release")

                    # Get scene position where mouse was released
                    scene_pos = viewer.mapToScene(event.pos())
                    logger.debug(f"Release position: ({scene_pos.x()}, {scene_pos.y()})")

                    # Check if released on empty space (no port underneath)
                    items = viewer.scene().items(scene_pos)
                    has_port = any(hasattr(item, 'port') and item.port for item in items)

                    logger.debug(f"Has port at release: {has_port}")

                    if not has_port:
                        # Save source port BEFORE calling original (which will clear it)
                        source_port = viewer._start_port if hasattr(viewer, '_start_port') else None

                        logger.debug(f"Source port: {source_port}")

                        if source_port:
                            logger.info(f"Connection dropped in empty space, showing search")
                            # Call original first to clean up the pipe
                            original_mouse_release(event)
                            # Then show search
                            self._show_connection_search(source_port, scene_pos)
                            return

            # Call original handler
            original_mouse_release(event)

        viewer.mouseReleaseEvent = patched_mouse_release
        logger.debug("Patched viewer mouseReleaseEvent for connection search")

    def _fix_mmb_panning(self):
        """
        Monkey-patch the viewer's mousePressEvent to allow panning with MMB
        even when hovering over items (nodes, ports, etc).
        Also prevents MMB from starting port connections.
        """
        viewer = self._graph.viewer()
        ViewerClass = viewer.__class__
        
        # Only patch once
        if getattr(ViewerClass, '_patched_mmb', False):
            return
            
        original_mouse_press = ViewerClass.mousePressEvent
        original_start_live = ViewerClass.start_live_connection
        
        def patched_mouse_press(viewer_self, event):
            # Call the original method first
            original_mouse_press(viewer_self, event)
            
            # If MMB was pressed, force MMB_state to True.
            # The original method sets MMB_state = False if it detects nodes under the cursor,
            # preventing panning. We override this behavior here to ensure MMB always pans.
            if event.button() == Qt.MouseButton.MiddleButton:
                viewer_self.MMB_state = True
                
                # Also cancel any live connection that may have been started by MMB
                if viewer_self._LIVE_PIPE.isVisible():
                    viewer_self.end_live_connection()
        
        def patched_start_live(viewer_self, selected_port):
            # Only allow starting connections with LMB, not MMB
            if viewer_self.MMB_state:
                return
            original_start_live(viewer_self, selected_port)
        
        ViewerClass.mousePressEvent = patched_mouse_press
        ViewerClass.start_live_connection = patched_start_live
        ViewerClass._patched_mmb = True

    def _setup_graph(self) -> None:
        """Configure the node graph settings and appearance."""
        # Set graph background color to VSCode Dark+ editor background
        self._graph.set_background_color(30, 30, 30)  # #1E1E1E (VSCode editor background)

        # Set grid styling
        self._graph.set_grid_mode(1)  # Show grid

        # Set graph properties
        self._graph.set_pipe_style(1)  # Curved pipes (CURVED = 1, not 2)

        # Configure selection and connection colors
        # Get the viewer to apply custom colors
        viewer = self._graph.viewer()

        # Register custom pipe class for connection labels and output preview
        try:
            if hasattr(viewer, '_PIPE_ITEM'):
                viewer._PIPE_ITEM = CasarePipe
                logger.debug("Custom pipe class registered for connection labels")
        except Exception as e:
            logger.debug(f"Could not register custom pipe: {e}")
        
        # Set selection colors - transparent overlay, thick yellow border
        if hasattr(viewer, '_node_sel_color'):
            viewer._node_sel_color = (0, 0, 0, 0)  # Transparent selection overlay
        if hasattr(viewer, '_node_sel_border_color'):
            viewer._node_sel_border_color = (255, 215, 0, 255)  # Bright yellow border
        
        # Set pipe colors - light gray curved lines
        if hasattr(viewer, '_pipe_color'):
            viewer._pipe_color = (100, 100, 100, 255)  # Gray pipes
        if hasattr(viewer, '_live_pipe_color'):
            viewer._live_pipe_color = (100, 100, 100, 255)  # Gray when dragging
        
        # Configure port colors to differentiate input/output
        # Input ports (left side) - cyan/teal color
        # Output ports (right side) - orange/amber color
        from NodeGraphQt.constants import PortEnum
        # Override the default port colors through the viewer
        if hasattr(viewer, '_port_color'):
            viewer._port_color = (100, 181, 246, 255)  # Light blue for ports
        if hasattr(viewer, '_port_border_color'):
            viewer._port_border_color = (66, 165, 245, 255)  # Darker blue border

        # ==================== PERFORMANCE OPTIMIZATIONS ====================

        # Qt rendering optimizations for high FPS (60/120/144 Hz support)
        from PySide6.QtWidgets import QGraphicsView
        from PySide6.QtCore import Qt

        # Enable optimization flags
        viewer.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontSavePainterState, True)
        viewer.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontAdjustForAntialiasing, True)
        viewer.setOptimizationFlag(QGraphicsView.OptimizationFlag.IndirectPainting, True)

        # Smart viewport updates (only redraw changed regions)
        viewer.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.SmartViewportUpdate)

        # Enable caching for static content
        viewer.setCacheMode(QGraphicsView.CacheMode.CacheBackground)

        # High refresh rate optimizations
        viewer.viewport().setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        viewer.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)

        # Detect and adapt to screen refresh rate
        screen = viewer.screen() if hasattr(viewer, 'screen') else viewer.window().screen()
        refresh_rate = screen.refreshRate()
        logger.info(f"Display refresh rate detected: {refresh_rate}Hz")

        # Configure frame timing based on refresh rate
        if refresh_rate >= 120:
            # High refresh rate display - prioritize low latency
            viewer.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.MinimalViewportUpdate)
            logger.info("Optimized for high refresh rate (120+ Hz)")
        elif refresh_rate >= 60:
            # Standard display - balance quality and performance
            viewer.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.SmartViewportUpdate)
            logger.info("Optimized for standard refresh rate (60 Hz)")

        # GPU-accelerated rendering (with automatic fallback to CPU)
        try:
            from PySide6.QtOpenGLWidgets import QOpenGLWidget
            from PySide6.QtGui import QSurfaceFormat

            # Configure OpenGL format for high performance
            gl_format = QSurfaceFormat()
            gl_format.setVersion(3, 3)  # OpenGL 3.3+ for modern features
            gl_format.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
            gl_format.setSwapBehavior(QSurfaceFormat.SwapBehavior.DoubleBuffer)
            gl_format.setSwapInterval(0)  # Disable vsync for maximum FPS (120/144/240 Hz support)
            gl_format.setSamples(4)  # 4x MSAA antialiasing

            # Create OpenGL viewport
            gl_widget = QOpenGLWidget()
            gl_widget.setFormat(gl_format)

            viewer.setViewport(gl_widget)

            # Set as default format for future widgets
            QSurfaceFormat.setDefaultFormat(gl_format)

            logger.info(f"GPU-accelerated rendering enabled (vsync disabled for {refresh_rate}Hz)")
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
    
    def get_selected_nodes(self) -> list:
        """
        Get the currently selected nodes.
        
        Returns:
            List of selected node objects
        """
        return self._graph.selected_nodes()
    
    def clear_selection(self) -> None:
        """Clear node selection."""
        self._graph.clear_selection()
    
    @property
    def auto_connect(self) -> AutoConnectManager:
        """
        Get the auto-connect manager.
        
        Returns:
            AutoConnectManager instance
        """
        return self._auto_connect
    
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
        # Capture right-click position BEFORE context menu is shown
        # We intercept MouseButtonPress with RightButton to capture position early
        if event.type() == event.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.RightButton:
                viewer = self._graph.viewer()
                # Capture the position where right-click occurred
                if hasattr(event, 'globalPos'):
                    global_pos = event.globalPos()
                else:
                    global_pos = event.globalPosition().toPoint()
                scene_pos = viewer.mapToScene(viewer.mapFromGlobal(global_pos))

                # Store position on the context menu for node creation
                context_menu = self._graph.get_context_menu('graph')
                if context_menu and context_menu.qmenu:
                    context_menu.qmenu._initial_scene_pos = scene_pos
                    logger.info(f"Right-click captured at scene position: ({scene_pos.x()}, {scene_pos.y()})")

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
                if hasattr(viewer, '_LIVE_PIPE') and viewer._LIVE_PIPE.isVisible():
                    # Save the source port for auto-connection
                    source_port = viewer._start_port if hasattr(viewer, '_start_port') else None
                    if source_port:
                        live_pipe_was_visible = True
                        # Hide the connection line while menu is open
                        viewer._LIVE_PIPE.setVisible(False)
                        logger.debug("Tab pressed during connection drag - hiding live pipe")

                # Get the context menu and show it
                context_menu = self._graph.get_context_menu('graph')
                if context_menu and context_menu.qmenu:
                    # Capture initial scene position BEFORE showing the menu
                    # This is stored so nodes are created at the original position
                    scene_pos = viewer.mapToScene(viewer.mapFromGlobal(cursor_pos))
                    context_menu.qmenu._initial_scene_pos = scene_pos

                    # If dragging a connection, setup auto-connect
                    if source_port:
                        def on_node_created(node):
                            """Auto-connect newly created node to source port."""
                            try:
                                self._auto_connect_new_node(node, source_port)
                                # End the live connection since we've completed it
                                viewer.end_live_connection()
                                logger.info(f"Auto-connected node from Tab search")
                            except Exception as e:
                                logger.error(f"Failed to auto-connect node: {e}")
                            finally:
                                # Disconnect this one-time handler
                                try:
                                    self._graph.node_created.disconnect(on_node_created)
                                except:
                                    pass

                        # Connect temporary handler for this node creation
                        if hasattr(self._graph, 'node_created'):
                            self._graph.node_created.connect(on_node_created)

                    context_menu.qmenu.exec(cursor_pos)

                    # If menu was cancelled and we were dragging, end the connection
                    if live_pipe_was_visible and hasattr(viewer, '_start_port') and viewer._start_port:
                        viewer.end_live_connection()
                        logger.debug("Tab menu cancelled - ending live connection")

                return True  # Event handled

            # Handle X key or Delete key to delete selected frames
            # Note: X key (88) and Delete key
            if key_event.key() == Qt.Key.Key_X or key_event.key() == Qt.Key.Key_Delete:
                logger.debug(f"Frame delete key pressed: {key_event.key()}")
                if self._delete_selected_frames():
                    return True  # Event handled if frames were deleted

            # Also handle lowercase 'x' (key code 88)
            if key_event.text().lower() == 'x':
                logger.debug(f"X key text detected")
                if self._delete_selected_frames():
                    return True

        return super().eventFilter(obj, event)

    def _delete_selected_frames(self) -> bool:
        """
        Delete any selected frames in the scene.

        Returns:
            True if any frames were deleted, False otherwise
        """
        from .node_frame import NodeFrame

        viewer = self._graph.viewer()
        scene = viewer.scene()
        deleted_any = False

        # Find and delete selected frames
        for item in scene.selectedItems():
            if isinstance(item, NodeFrame):
                logger.info(f"Deleting selected frame: {item.frame_title}")
                item._delete_frame()
                deleted_any = True

        return deleted_any

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
            if hasattr(self._graph, 'port_connected'):
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
            if not hasattr(source_node, 'get_port_type') or not hasattr(target_node, 'get_port_type'):
                return  # Can't validate, allow connection

            # Validate the connection
            validation = self._validator.validate_connection(
                source_node, output_port.name(),
                target_node, input_port.name()
            )

            if not validation.is_valid:
                # Block the connection - disconnect immediately
                logger.warning(f"Connection blocked: {validation.message}")

                try:
                    output_port.disconnect_from(input_port)
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
        """
        try:
            if hasattr(self._graph, 'node_created'):
                self._graph.node_created.connect(self._on_node_created_check_duplicate)
                logger.debug("Paste hook for duplicate ID detection enabled")
        except Exception as e:
            logger.warning(f"Could not setup paste hook: {e}")

    def _on_node_created_check_duplicate(self, node) -> None:
        """
        Handle node creation/paste events.

        Detects pasted nodes with duplicate IDs and regenerates them.
        This prevents self-connection errors from copy/paste operations.
        """
        from ..utils.id_generator import generate_node_id

        # Get current node_id property
        current_id = node.get_property("node_id")
        if not current_id:
            return  # New node creation handled by factory

        # Check if another node already has this ID (duplicate from paste)
        for other_node in self._graph.all_nodes():
            if other_node is not node and other_node.get_property("node_id") == current_id:
                # Duplicate detected - regenerate ID
                casare_node = node.get_casare_node() if hasattr(node, 'get_casare_node') else None

                if casare_node:
                    # Get node type for ID generation
                    node_type = casare_node.node_type if hasattr(casare_node, 'node_type') else "Node"
                    new_id = generate_node_id(node_type)

                    # Update both locations synchronously
                    casare_node.node_id = new_id
                    node.set_property("node_id", new_id)

                    # Verify sync succeeded
                    verify_id = node.get_property("node_id")
                    if verify_id != new_id:
                        logger.error(
                            f"Property update failed for {node.name()}: "
                            f"expected {new_id}, got {verify_id}"
                        )
                    else:
                        logger.info(f"Regenerated duplicate node ID: {current_id} -> {new_id}")
                break

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
        """Handle drag enter event - accept JSON files."""
        mime_data = event.mimeData()

        if mime_data.hasUrls():
            for url in mime_data.urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if file_path.lower().endswith('.json'):
                        event.acceptProposedAction()
                        return

        # Also accept plain text (for JSON text drops)
        if mime_data.hasText():
            text = mime_data.text()
            if text.strip().startswith('{') and '"nodes"' in text:
                event.acceptProposedAction()
                return

        event.ignore()

    def _handle_drag_move(self, event) -> None:
        """Handle drag move event."""
        # Same logic as drag enter
        self._handle_drag_enter(event)

    def _handle_drop(self, event) -> None:
        """Handle drop event - import workflow file or JSON text."""
        from PySide6.QtCore import QPointF

        mime_data = event.mimeData()
        drop_pos = event.position() if hasattr(event, 'position') else event.posF()

        # Convert to scene coordinates for node positioning
        viewer = self._graph.viewer()
        scene_pos = viewer.mapToScene(drop_pos.toPoint())
        position = (scene_pos.x(), scene_pos.y())

        # Handle file drops
        if mime_data.hasUrls():
            for url in mime_data.urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if file_path.lower().endswith('.json'):
                        logger.info(f"Dropped workflow file: {file_path}")
                        if self._import_file_callback:
                            self._import_file_callback(file_path, position)
                        event.acceptProposedAction()
                        return

        # Handle JSON text drops
        if mime_data.hasText():
            text = mime_data.text()
            if text.strip().startswith('{'):
                try:
                    import orjson
                    data = orjson.loads(text)
                    if "nodes" in data:
                        logger.info("Dropped workflow JSON text")
                        if self._import_callback:
                            self._import_callback(data, position)
                        event.acceptProposedAction()
                        return
                except Exception as e:
                    logger.warning(f"Dropped text is not valid JSON: {e}")

        event.ignore()

    def _on_navigation_changed(self) -> None:
        """Handle navigation stack changes - update breadcrumb display and drop zone visibility."""
        path = self._navigation_manager.get_breadcrumb_path()
        self._snippet_breadcrumb.set_path(path)

        # Show drop zone only when inside a snippet (depth > 0)
        depth = self._navigation_manager.get_depth()
        is_inside_snippet = depth > 0
        self._parameter_drop_zone.setVisible(is_inside_snippet)

        logger.debug(f"Navigation changed, depth: {depth}, drop zone visible: {is_inside_snippet}")

    def _on_breadcrumb_clicked(self, level_index: int) -> None:
        """
        Handle breadcrumb level click - navigate back to that level.

        Args:
            level_index: Index of level clicked (0 = root workflow)
        """
        logger.info(f"Navigating back to level {level_index}")
        self._navigation_manager.navigate_back_to_level(level_index)

    def get_navigation_manager(self):
        """Get the snippet navigation manager."""
        return self._navigation_manager

    def _show_connection_search(self, source_port, scene_pos):
        """
        Show node context menu (same as Tab search) and auto-connect created node.

        Args:
            source_port: The port that was dragged from
            scene_pos: Scene position where connection was released
        """
        # Get the context menu (same as Tab search)
        context_menu = self._graph.get_context_menu('graph')
        if not context_menu or not context_menu.qmenu:
            logger.warning("Context menu not available")
            return

        # Store scene position for node creation
        context_menu.qmenu._initial_scene_pos = scene_pos

        # Store source port for auto-connection after node is created
        # We'll connect to node_created signal temporarily
        def on_node_created(node):
            """Auto-connect newly created node to source port."""
            try:
                self._auto_connect_new_node(node, source_port)
            except Exception as e:
                logger.error(f"Failed to auto-connect node: {e}")
            finally:
                # Disconnect this one-time handler
                try:
                    self._graph.node_created.disconnect(on_node_created)
                except:
                    pass

        # Connect temporary handler for this node creation
        if hasattr(self._graph, 'node_created'):
            self._graph.node_created.connect(on_node_created)

        # Show context menu at the release position (map scene to global coordinates)
        viewer = self._graph.viewer()
        view_pos = viewer.mapFromScene(scene_pos)
        global_pos = viewer.mapToGlobal(view_pos)
        context_menu.qmenu.exec(global_pos)

        logger.debug(f"Context menu shown at scene position: ({scene_pos.x()}, {scene_pos.y()})")

    def _auto_connect_new_node(self, new_node, source_port_item):
        """
        Auto-connect a newly created node to the source port.

        Args:
            new_node: The newly created node
            source_port_item: The port item that was dragged from (PortItem from viewer)
        """
        try:
            # Import port type enum
            from NodeGraphQt.constants import PortTypeEnum

            # Determine if source is input or output
            # PortItem has .port_type property: IN=2, OUT=1
            is_source_output = source_port_item.port_type == PortTypeEnum.OUT.value

            logger.debug(f"Auto-connecting from {'output' if is_source_output else 'input'} port: {source_port_item.name}")

            # Find compatible port on new node and connect using PortItem.connect_to()
            if is_source_output:
                # Source is output, find input on new node
                for port in new_node.input_ports():
                    # Get the PortItem view from the Port object
                    target_port_item = port.view
                    # Try to connect at the PortItem level
                    try:
                        source_port_item.connect_to(target_port_item)
                        logger.info(f"Auto-connected {source_port_item.name} -> {target_port_item.name}")
                        break
                    except Exception as e:
                        logger.debug(f"Could not connect to {target_port_item.name}: {e}")
                        continue
            else:
                # Source is input, find output on new node
                for port in new_node.output_ports():
                    # Get the PortItem view from the Port object
                    target_port_item = port.view
                    # Try to connect at the PortItem level
                    try:
                        target_port_item.connect_to(source_port_item)
                        logger.info(f"Auto-connected {target_port_item.name} -> {source_port_item.name}")
                        break
                    except Exception as e:
                        logger.debug(f"Could not connect to {target_port_item.name}: {e}")
                        continue

        except Exception as e:
            logger.error(f"Failed to auto-connect new node: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def _on_parameter_requested(self, node_id: str, property_key: str, data_type: str, current_value) -> None:
        """
        Handle parameter creation request from drop zone.

        Args:
            node_id: ID of node containing the property
            property_key: Key of the property being exposed
            data_type: Data type of the property
            current_value: Current value of the property
        """
        from PySide6.QtWidgets import QMessageBox
        from ..core.snippet_definition import ParameterMapping

        logger.info(f"Parameter requested: {node_id}.{property_key} (type: {data_type})")

        # Show parameter naming dialog
        dialog = ParameterNamingDialog(node_id, property_key, data_type, current_value, self)
        if dialog.exec() != ParameterNamingDialog.DialogCode.Accepted:
            logger.debug("Parameter creation cancelled by user")
            return

        # Get dialog results
        param_name = dialog.get_parameter_name()
        description = dialog.get_description()
        required = dialog.is_required()
        default_value = dialog.get_default_value()

        logger.info(f"Creating parameter: {param_name} -> {node_id}.{property_key}")

        # Get current snippet definition from navigation manager
        current_level = self._navigation_manager.get_current_level()
        if not current_level or not current_level.snippet_definition:
            QMessageBox.critical(
                self,
                "Navigation Error",
                "Cannot create parameter: not currently inside a snippet"
            )
            return

        snippet_def = current_level.snippet_definition

        # Check if parameter name already exists
        if any(p.name == param_name for p in snippet_def.parameters):
            QMessageBox.warning(
                self,
                "Duplicate Parameter",
                f"Parameter '{param_name}' already exists in this snippet.\n\n"
                f"Please choose a different name."
            )
            return

        # Create parameter mapping
        param_mapping = ParameterMapping(
            name=param_name,
            target_node_id=node_id,
            target_property=property_key,
            data_type=data_type,
            default_value=default_value,
            required=required,
            description=description
        )

        # Add to snippet definition
        snippet_def.parameters.append(param_mapping)

        logger.info(f"Parameter '{param_name}' created successfully")

        # TODO: Update the VisualSnippetNode in the parent level to show the new parameter port
        # This requires finding the snippet node at the parent level and dynamically adding a port

        QMessageBox.information(
            self,
            "Parameter Created",
            f"Parameter '{param_name}' has been created.\n\n"
            f"Maps to: {node_id}.{property_key}\n"
            f"Type: {data_type}\n"
            f"Required: {required}"
        )
