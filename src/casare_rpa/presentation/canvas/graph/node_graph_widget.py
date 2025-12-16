"""
Node graph widget wrapper for NodeGraphQt integration.

This module provides a wrapper around NodeGraphQt's NodeGraph
to integrate it with the PySide6 application.

The NodeGraphQt library has several bugs and limitations that are fixed
via wrapper classes in node_widgets.py. All fixes are applied at module
load time by calling apply_all_node_widget_fixes().

REFACTORED: Logic extracted into delegate classes:
- GraphSetup: Graph configuration, optimization, signals
- ConnectionHandler: Connection validation, pipe management
- NodeSelectionHandler: Selection operations, delete, duplicate
- GraphEventHandler: Event filtering, keyboard/mouse handling
"""

from typing import Optional

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsScene,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from loguru import logger
from NodeGraphQt import NodeGraph

from casare_rpa.presentation.canvas.connections.auto_connect import AutoConnectManager
from casare_rpa.presentation.canvas.connections.connection_cutter import (
    ConnectionCutter,
)
from casare_rpa.presentation.canvas.connections.node_insert import NodeInsertManager
from casare_rpa.presentation.canvas.connections.reroute_insert import (
    RerouteInsertManager,
)
from casare_rpa.presentation.canvas.connections.shake_to_detach import (
    ShakeToDetachManager,
    set_shake_manager,
)
from casare_rpa.presentation.canvas.connections.smart_routing import (
    SmartRoutingManager,
    set_routing_manager,
)
from casare_rpa.presentation.canvas.connections.wire_bundler import (
    WireBundler,
    set_wire_bundler,
)
from casare_rpa.presentation.canvas.graph.composite_node_creator import (
    CompositeNodeCreator,
)
from casare_rpa.presentation.canvas.graph.custom_node_item import (
    get_high_performance_mode,
    set_high_performance_mode,
    get_high_perf_node_threshold,
)
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
from casare_rpa.presentation.canvas.ui.panels.port_legend_panel import PortLegendPanel
from casare_rpa.presentation.canvas.ui.widgets.breadcrumb_nav import (
    BreadcrumbNavWidget,
    SubflowNavigationController,
)

# Extracted delegate classes
from casare_rpa.presentation.canvas.graph.graph_setup import GraphSetup
from casare_rpa.presentation.canvas.graph.connection_handler import ConnectionHandler
from casare_rpa.presentation.canvas.graph.node_selection_handler import (
    NodeSelectionHandler,
)
from casare_rpa.presentation.canvas.graph.graph_event_handler import GraphEventHandler

# Keyboard navigation
from casare_rpa.presentation.canvas.graph.keyboard_navigator import KeyboardNavigator
from casare_rpa.presentation.canvas.graph.focus_ring import FocusRingManager

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


# Apply all NodeGraphQt fixes via wrapper classes
apply_all_node_widget_fixes()


class NodeGraphWidget(QWidget):
    """
    Widget wrapper for NodeGraphQt's NodeGraph.

    Provides a Qt widget container for the node graph editor
    with custom styling and configuration.

    Now includes connection validation with strict type checking.

    REFACTORED: Uses delegate classes for better maintainability:
    - GraphSetup: Configuration and initialization
    - ConnectionHandler: Connection management
    - NodeSelectionHandler: Selection operations
    - GraphEventHandler: Event filtering
    """

    # Signal emitted when an invalid connection is blocked
    connection_blocked = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the node graph widget.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        # Create node graph
        self._graph = NodeGraph()

        # Enable viewport culling for smooth 60 FPS panning with 100+ nodes
        from casare_rpa.presentation.canvas.graph.viewport_culling import (
            ViewportCullingManager,
        )

        self._culler = ViewportCullingManager(cell_size=500, margin=200)
        self._culler.set_enabled(True)

        # Create delegate classes for extracted functionality
        self._graph_setup = GraphSetup(self._graph, self._culler)
        self._graph_setup.configure_graph()

        # Create selection manager first (needed by other handlers)
        self._selection = SelectionManager(self._graph, self)

        # Create selection handler delegate
        self._selection_handler = NodeSelectionHandler(self._graph, self._selection)

        # Create connection handler delegate
        validator = get_connection_validator() if HAS_CONNECTION_VALIDATOR else None
        self._connection_handler = ConnectionHandler(
            self._graph, self._culler, validator
        )
        self._connection_handler.connection_blocked.connect(
            self.connection_blocked.emit
        )
        self._connection_handler.setup_validation()

        # Create event handler delegate
        self._event_handler = GraphEventHandler(
            self._graph, self._selection_handler, self
        )

        # Setup viewport culling signals (uses methods from this class and delegates)
        self._setup_viewport_culling()

        # PERFORMANCE: O(1) node ID tracking instead of O(n) scans
        self._node_ids_in_use: set[str] = set()
        self._node_count: int = 0

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

        # Create reroute insert manager (Alt+LMB on wire to insert reroute node)
        self._reroute_insert = RerouteInsertManager(self._graph, self)

        # Create shake-to-detach manager (shake node to disconnect all wires)
        self._shake_to_detach = ShakeToDetachManager(self._graph, self)
        set_shake_manager(self._shake_to_detach)

        # Create wire bundler for grouping parallel connections
        self._wire_bundler = WireBundler(self._graph, self)
        set_wire_bundler(self._wire_bundler)

        # Create smart routing manager for obstacle avoidance
        self._smart_routing = SmartRoutingManager(self._graph)
        set_routing_manager(self._smart_routing)

        # Create quick actions for node context menu
        self._quick_actions = NodeQuickActions(self._graph, self)
        self._quick_actions.set_auto_connect_manager(self._auto_connect)

        # Create keyboard navigator for arrow key navigation
        self._keyboard_navigator = KeyboardNavigator(self._graph)
        self._focus_ring_manager: Optional[FocusRingManager] = None

        # Track mouse press for popup close
        self._popup_close_press_pos = None

        # Connect create subflow action
        self._quick_actions.create_subflow_requested.connect(
            self._create_subflow_from_selection
        )

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

        # Install event filters
        self._setup_event_filters()

        # Setup port legend panel (F1 help overlay)
        self._setup_port_legend()

        # Setup breadcrumb navigation for subflows
        self._setup_breadcrumb_nav()

        # Configure event handler callbacks
        self._setup_event_handler_callbacks()

    def _setup_event_filters(self) -> None:
        """Install event filters on graph viewer and related widgets."""
        self._graph.viewer().installEventFilter(self)
        self._graph.viewer().viewport().installEventFilter(self)
        self._graph.viewer().scene().installEventFilter(self)

        # Install tooltip blocker
        self._tooltip_blocker = TooltipBlocker()
        self._graph.viewer().installEventFilter(self._tooltip_blocker)
        self._graph.viewer().viewport().installEventFilter(self._tooltip_blocker)

        # Install connection drop filter
        self._connection_drop_filter = ConnectionDropFilter(self._graph, self)
        self._graph.viewer().viewport().installEventFilter(self._connection_drop_filter)

        # Install output port MMB filter
        self._output_port_mmb_filter = OutputPortMMBFilter(self._graph, self)
        self._graph.viewer().viewport().installEventFilter(self._output_port_mmb_filter)

    def _setup_event_handler_callbacks(self) -> None:
        """Configure callbacks for the event handler delegate."""
        self._event_handler.set_callbacks(
            on_tab=self._handle_tab_key,
            on_escape=self._handle_escape_key,
            on_delete_frames=self._delete_selected_frames,
            on_toggle_port_legend=self._toggle_port_legend,
            on_subflow_dive_in=self._on_subflow_dive_in,
            on_subflow_go_back=self._on_subflow_go_back,
            on_close_output_popup=self._check_close_output_popup,
        )

    def _handle_tab_key(self) -> bool:
        """Handle Tab key to show context menu."""
        viewer = self._graph.viewer()

        cursor_pos = viewer.cursor().pos()

        source_port = None
        live_pipe_was_visible = False
        if hasattr(viewer, "_LIVE_PIPE") and viewer._LIVE_PIPE.isVisible():
            source_port = viewer._start_port if hasattr(viewer, "_start_port") else None
            if source_port:
                live_pipe_was_visible = True
                viewer._LIVE_PIPE.setVisible(False)

        context_menu = self._graph.get_context_menu("graph")
        if context_menu and context_menu.qmenu:
            scene_pos = viewer.mapToScene(viewer.mapFromGlobal(cursor_pos))
            context_menu.qmenu._initial_scene_pos = scene_pos

            tab_handler_executed = [False]
            tab_on_node_created = None

            if source_port:

                def tab_on_node_created(node):
                    if tab_handler_executed[0]:
                        return
                    tab_handler_executed[0] = True
                    try:
                        self._auto_connect_new_node(node, source_port)
                        viewer.end_live_connection()
                    except Exception as e:
                        logger.error(f"Failed to auto-connect node: {e}")

                if hasattr(self._graph, "node_created"):
                    self._graph.node_created.connect(tab_on_node_created)

            try:
                context_menu.qmenu.exec(cursor_pos)
            finally:
                if tab_on_node_created and hasattr(self._graph, "node_created"):
                    try:
                        self._graph.node_created.disconnect(tab_on_node_created)
                    except (RuntimeError, TypeError):
                        pass

            if live_pipe_was_visible and not tab_handler_executed[0]:
                viewer.end_live_connection()

        return True

    def _handle_escape_key(self) -> bool:
        """Handle Escape key to cancel live connection."""
        viewer = self._graph.viewer()
        if hasattr(viewer, "_LIVE_PIPE") and viewer._LIVE_PIPE.isVisible():
            viewer.end_live_connection()
            logger.debug("ESC pressed - cancelled live connection")
            return True
        return False

    def _check_close_output_popup(self) -> None:
        """Check if output popup should be closed on click."""
        if (
            hasattr(self, "_output_popup")
            and self._output_popup
            and self._output_popup.isVisible()
            and not self._output_popup.is_pinned
        ):
            self.close_output_popup()

    def _setup_viewport_culling(self) -> None:
        """Wire up viewport culling to graph events."""
        self._graph_setup.setup_viewport_culling(
            on_node_created_callback=self._on_culling_node_created,
            on_nodes_deleted_callback=self._on_culling_nodes_deleted,
            on_pipe_created_callback=self._connection_handler.on_pipe_created,
            on_pipe_deleted_callback=self._connection_handler.on_pipe_deleted,
            on_session_changed_callback=self._on_session_changed,
            update_culling_callback=self._graph_setup.update_viewport_culling,
        )

    def _on_culling_node_created(self, node) -> None:
        """Register newly created node with culler and update variable picker context."""
        try:
            if hasattr(node, "view") and node.view:
                rect = node.view.sceneBoundingRect()
                self._culler.register_node(node.id, node.view, rect)

                view = node.view
                if hasattr(view, "set_position_callback"):
                    node_id = node.id
                    widget_ref = self

                    def on_position_changed(item, nid=node_id):
                        try:
                            widget_ref._culler.update_node_position(
                                nid, item.sceneBoundingRect()
                            )
                            if (
                                hasattr(widget_ref, "_smart_routing")
                                and widget_ref._smart_routing.is_enabled()
                            ):
                                widget_ref._smart_routing.update_obstacles()
                        except Exception:
                            pass

                    view.set_position_callback(on_position_changed)
        except Exception as e:
            logger.debug(f"Could not register node for culling: {e}")

        self._node_count += 1
        self._update_variable_picker_context(node)
        self._check_performance_mode_incremental()

    def _update_variable_picker_context(self, node) -> None:
        """Update variable picker context for all VariableAwareLineEdit widgets in a node."""
        try:
            from casare_rpa.presentation.canvas.graph.node_widgets import (
                update_node_context_for_widgets,
            )

            update_node_context_for_widgets(node)
        except Exception as e:
            logger.debug(f"Could not update variable picker context: {e}")

    def _on_culling_nodes_deleted(self, node_ids) -> None:
        """Unregister deleted nodes from culler and update tracking."""
        try:
            for node_id in node_ids:
                self._culler.unregister_node(node_id)
                self._node_ids_in_use.discard(node_id)
            self._node_count = max(0, self._node_count - len(node_ids))
        except Exception as e:
            logger.debug(f"Could not unregister nodes from culling: {e}")

        self._connection_handler.cleanup_orphaned_pipes(node_ids)

    def _on_session_changed(self, *args) -> None:
        """Clear culler when graph session is reset."""
        try:
            self._culler.clear()
            self._node_ids_in_use.clear()
            self._node_count = 0
            logger.debug("Viewport culler cleared on session change")
        except Exception as e:
            logger.debug(f"Could not clear culler on session change: {e}")

    def _setup_port_legend(self) -> None:
        """Create and configure the port legend panel."""
        self._port_legend = PortLegendPanel(self)
        self._port_legend.show_first_time_hint()

    def _setup_breadcrumb_nav(self) -> None:
        """Create and configure the breadcrumb navigation for subflows."""
        self._breadcrumb = BreadcrumbNavWidget(self)
        self._breadcrumb.setParent(self)
        self._breadcrumb.move(10, 10)

        main_window = self.window()
        self._subflow_nav = SubflowNavigationController(
            self._graph, self._breadcrumb, main_window
        )

        self._breadcrumb.navigate_back.connect(self._on_subflow_go_back)
        self._breadcrumb.navigate_to.connect(self._on_subflow_navigate_to)
        self._subflow_nav.initialize("root", "main")

    def _on_subflow_dive_in(self) -> bool:
        """Handle V key - dive into selected subflow."""
        if not hasattr(self, "_subflow_nav"):
            return False

        selected = self._graph.selected_nodes()
        if len(selected) != 1:
            return False

        node = selected[0]
        node_type = node.__class__.__name__.lower()
        identifier = getattr(node, "__identifier__", "").lower()
        if "subflow" not in node_type and "subflow" not in identifier:
            return False

        success = self._subflow_nav.dive_in()
        if success:
            logger.info("Dived into subflow")
        return success

    def _on_subflow_go_back(self) -> bool:
        """Handle C key or back button - go back to parent workflow."""
        if not hasattr(self, "_subflow_nav"):
            return False

        success = self._subflow_nav.go_back()
        if success:
            logger.info("Went back to parent workflow")
        return success

    def _on_subflow_navigate_to(self, item_id: str, level_index: int) -> None:
        """Handle clicking a breadcrumb to navigate to that level."""
        if not hasattr(self, "_subflow_nav"):
            return
        self._subflow_nav.navigate_to_level(level_index)

    @property
    def breadcrumb(self) -> BreadcrumbNavWidget:
        """Get the breadcrumb navigation widget."""
        return self._breadcrumb

    @property
    def subflow_navigation(self) -> SubflowNavigationController:
        """Get the subflow navigation controller."""
        return self._subflow_nav

    @property
    def graph(self) -> NodeGraph:
        """Get the underlying NodeGraph instance."""
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
        """Get the selection manager."""
        return self._selection

    def get_selected_nodes(self) -> list:
        """Get the currently selected nodes."""
        return self._selection_handler.get_selected_nodes()

    def clear_selection(self) -> None:
        """Clear node selection."""
        self._selection_handler.clear_selection()

    @property
    def auto_connect(self) -> AutoConnectManager:
        """Get the auto-connect manager."""
        return self._auto_connect

    @property
    def node_insert(self) -> NodeInsertManager:
        """Get the node insert manager."""
        return self._node_insert

    @property
    def reroute_insert(self) -> RerouteInsertManager:
        """Get the reroute insert manager."""
        return self._reroute_insert

    @property
    def wire_bundler(self) -> WireBundler:
        """Get the wire bundler manager."""
        return self._wire_bundler

    def set_wire_bundling_enabled(self, enabled: bool) -> None:
        """Enable or disable wire bundling."""
        self._wire_bundler.set_enabled(enabled)
        logger.info(f"Wire bundling {'enabled' if enabled else 'disabled'}")

    def is_wire_bundling_enabled(self) -> bool:
        """Check if wire bundling is enabled."""
        return self._wire_bundler.is_enabled()

    def set_auto_connect_enabled(self, enabled: bool) -> None:
        """Enable or disable the auto-connect feature."""
        self._auto_connect.set_active(enabled)

    def is_auto_connect_enabled(self) -> bool:
        """Check if auto-connect is enabled."""
        return self._auto_connect.is_active()

    def set_auto_connect_distance(self, distance: float) -> None:
        """Set the maximum distance for auto-connect suggestions."""
        self._auto_connect.set_max_distance(distance)

    @property
    def shake_to_detach(self) -> ShakeToDetachManager:
        """Get the shake-to-detach manager."""
        return self._shake_to_detach

    def set_shake_to_detach_enabled(self, enabled: bool) -> None:
        """Enable or disable shake-to-detach gesture."""
        self._shake_to_detach.set_active(enabled)
        logger.info(f"Shake-to-detach {'enabled' if enabled else 'disabled'}")

    def is_shake_to_detach_enabled(self) -> bool:
        """Check if shake-to-detach is enabled."""
        return self._shake_to_detach.is_active()

    def set_shake_sensitivity(
        self,
        shake_threshold: int = 4,
        time_window_ms: int = 400,
        min_movement_px: int = 15,
    ) -> None:
        """
        Configure shake-to-detach sensitivity.

        Args:
            shake_threshold: Direction changes needed to trigger (default 4)
            time_window_ms: Time window for shake detection (default 400ms)
            min_movement_px: Minimum horizontal movement per swing (default 15px)
        """
        self._shake_to_detach.set_sensitivity(
            shake_threshold, time_window_ms, min_movement_px
        )

    # =========================================================================
    # HIGH PERFORMANCE MODE
    # =========================================================================

    def _check_performance_mode(self) -> None:
        """Check if high performance mode should be auto-enabled based on node count."""
        node_count = len(self._graph.all_nodes())
        threshold = get_high_perf_node_threshold()

        if node_count >= threshold and not get_high_performance_mode():
            set_high_performance_mode(True)
            logger.info(
                f"Auto-enabled High Performance Mode ({node_count} nodes >= {threshold})"
            )

    def _check_performance_mode_incremental(self) -> None:
        """O(1) performance mode check using tracked node count."""
        threshold = get_high_perf_node_threshold()
        if self._node_count == threshold and not get_high_performance_mode():
            set_high_performance_mode(True)
            logger.info(
                f"Auto-enabled High Performance Mode ({self._node_count} nodes >= {threshold})"
            )

    def set_high_performance_mode(self, enabled: bool) -> None:
        """Enable or disable high performance mode."""
        set_high_performance_mode(enabled)
        self._graph.viewer().viewport().update()
        logger.info(f"High Performance Mode {'enabled' if enabled else 'disabled'}")

    def enable_animation_mode(self) -> None:
        """Disable BSP tree indexing during workflow execution."""
        try:
            scene = self._graph.viewer().scene()
            if scene:
                scene.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.NoIndex)
                logger.debug("Scene indexing disabled for animation mode")
        except Exception as e:
            logger.debug(f"Could not enable animation mode: {e}")

    def enable_editing_mode(self) -> None:
        """Re-enable BSP tree indexing after workflow execution."""
        try:
            scene = self._graph.viewer().scene()
            if scene:
                scene.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.BspTreeIndex)
                logger.debug("Scene indexing re-enabled for editing mode")
        except Exception as e:
            logger.debug(f"Could not enable editing mode: {e}")

    def is_high_performance_mode(self) -> bool:
        """Check if high performance mode is enabled."""
        return get_high_performance_mode()

    # =========================================================================
    # SMART WIRE ROUTING
    # =========================================================================

    @property
    def smart_routing(self) -> SmartRoutingManager:
        """Get the smart routing manager."""
        return self._smart_routing

    def set_smart_routing_enabled(self, enabled: bool) -> None:
        """Enable or disable smart wire routing."""
        from casare_rpa.presentation.canvas.graph.custom_pipe import (
            set_smart_routing_enabled,
        )

        self._smart_routing.set_enabled(enabled)
        set_smart_routing_enabled(enabled)

        if enabled:
            self._smart_routing.mark_dirty()
            self._smart_routing.update_obstacles()

        self._graph.viewer().viewport().update()
        logger.info(f"Smart Wire Routing {'enabled' if enabled else 'disabled'}")

    def is_smart_routing_enabled(self) -> bool:
        """Check if smart wire routing is enabled."""
        return self._smart_routing.is_enabled()

    @property
    def quick_actions(self) -> NodeQuickActions:
        """Get the quick actions manager."""
        return self._quick_actions

    # =========================================================================
    # EVENT FILTER (delegates to GraphEventHandler)
    # =========================================================================

    def eventFilter(self, obj, event):
        """Event filter to capture Tab key press and right-click for context menu."""
        event_type = event.type()

        # Handle drag events
        if event_type == QEvent.Type.DragEnter:
            self._handle_drag_enter(event)
            return event.isAccepted()
        elif event_type == QEvent.Type.DragMove:
            self._handle_drag_move(event)
            return event.isAccepted()
        elif event_type == QEvent.Type.Drop:
            self._handle_drop(event)
            return event.isAccepted()

        # Clear focus from text widgets when mouse enters canvas
        if event.type() == QEvent.Type.Enter:
            focus_widget = QApplication.focusWidget()
            if isinstance(focus_widget, (QLineEdit, QTextEdit)):
                parent = focus_widget.parent()
                while parent:
                    if hasattr(parent, "scene") and callable(parent.scene):
                        focus_widget.clearFocus()
                        break
                    parent = getattr(parent, "parent", lambda: None)()

        # Handle mouse press for output popup and Alt+drag
        if event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                self._check_close_output_popup()
                modifiers = event.modifiers()

                # Alt+LMB: drag duplicate
                if modifiers & Qt.KeyboardModifier.AltModifier:
                    if self._alt_drag_duplicate(event):
                        return True

            if event.button() == Qt.MouseButton.RightButton:
                viewer = self._graph.viewer()
                if hasattr(viewer, "_LIVE_PIPE") and viewer._LIVE_PIPE.isVisible():
                    viewer.end_live_connection()
                    return True

                if hasattr(event, "globalPos"):
                    global_pos = event.globalPos()
                else:
                    global_pos = event.globalPosition().toPoint()
                scene_pos = viewer.mapToScene(viewer.mapFromGlobal(global_pos))

                context_menu = self._graph.get_context_menu("graph")
                if context_menu and context_menu.qmenu:
                    context_menu.qmenu._initial_scene_pos = scene_pos

                return False

        # Handle mouse release for Alt+drag cleanup
        if event.type() == QEvent.Type.MouseButtonRelease:
            if (
                event.button() == Qt.MouseButton.LeftButton
                and self._event_handler.alt_drag_node
            ):
                self._event_handler.alt_drag_node = None

        # Handle mouse move for Alt+drag
        if event.type() == QEvent.Type.MouseMove:
            if self._event_handler.alt_drag_node:
                self._alt_drag_move(event)
                return True

        # Handle key press events
        if event.type() == QEvent.Type.KeyPress:
            key_event = event
            if key_event.key() == Qt.Key.Key_Tab:
                self._handle_tab_key()
                return True

            if key_event.key() == Qt.Key.Key_Escape:
                if self._handle_escape_key():
                    return True

            if key_event.key() == Qt.Key.Key_Delete:
                if self._delete_selected_frames():
                    return True
                if self._selection_handler.delete_selected_nodes():
                    return True

            # Check if text widget has focus - don't delete nodes when typing
            focus_widget = QApplication.focusWidget()
            if isinstance(focus_widget, (QLineEdit, QTextEdit)):
                pass  # Let the text widget handle the key
            elif key_event.key() == Qt.Key.Key_X or key_event.text().lower() == "x":
                if self._delete_selected_frames():
                    return True
                if self._selection_handler.delete_selected_nodes():
                    return True

            if (
                key_event.key() == Qt.Key.Key_D
                and key_event.modifiers() == Qt.KeyboardModifier.ControlModifier
            ):
                if self._selection_handler.duplicate_selected_nodes():
                    return True

            if (
                key_event.key() == Qt.Key.Key_E
                and key_event.modifiers() == Qt.KeyboardModifier.ControlModifier
            ):
                if self._selection_handler.toggle_selected_nodes_enabled():
                    return True

            if key_event.key() == Qt.Key.Key_F2:
                if self._selection_handler.rename_selected_node():
                    return True

            if key_event.key() == Qt.Key.Key_F1:
                self._toggle_port_legend()
                return True

            if (
                key_event.key() == Qt.Key.Key_G
                and key_event.modifiers() == Qt.KeyboardModifier.ControlModifier
            ):
                if self._create_subflow_from_selection():
                    return True

            if key_event.key() == Qt.Key.Key_V and not key_event.modifiers():
                if self._on_subflow_dive_in():
                    return True

            if key_event.key() == Qt.Key.Key_C and not key_event.modifiers():
                if self._on_subflow_go_back():
                    return True

            # Keyboard navigation (arrow keys)
            if key_event.key() == Qt.Key.Key_Right:
                if self._handle_keyboard_nav("right"):
                    return True

            if key_event.key() == Qt.Key.Key_Left:
                if self._handle_keyboard_nav("left"):
                    return True

            if key_event.key() == Qt.Key.Key_Up:
                if self._handle_keyboard_nav("up"):
                    return True

            if key_event.key() == Qt.Key.Key_Down:
                if self._handle_keyboard_nav("down"):
                    return True

            if key_event.key() == Qt.Key.Key_Home:
                if self._keyboard_navigator.navigate_home():
                    self._update_focus_ring()
                    return True

            if key_event.key() == Qt.Key.Key_End:
                if self._keyboard_navigator.navigate_end():
                    self._update_focus_ring()
                    return True

            # Zoom shortcuts
            if (
                key_event.key() == Qt.Key.Key_0
                and key_event.modifiers() & Qt.KeyboardModifier.ControlModifier
            ):
                self.reset_zoom()
                return True

            if (
                key_event.key() == Qt.Key.Key_Plus
                and key_event.modifiers() & Qt.KeyboardModifier.ControlModifier
            ):
                self.zoom_in()
                return True

            if (
                key_event.key() == Qt.Key.Key_Minus
                and key_event.modifiers() & Qt.KeyboardModifier.ControlModifier
            ):
                self.zoom_out()
                return True

            if (
                key_event.key() == Qt.Key.Key_1
                and key_event.modifiers() & Qt.KeyboardModifier.ControlModifier
            ):
                self.fit_to_all()
                return True

        return super().eventFilter(obj, event)

    def _delete_selected_frames(self) -> bool:
        """Delete any selected frames in the scene."""
        return self._selection.delete_selected_frames()

    # =========================================================================
    # KEYBOARD NAVIGATION
    # =========================================================================

    def _handle_keyboard_nav(self, direction: str) -> bool:
        """
        Handle keyboard navigation in the specified direction.

        Args:
            direction: One of "up", "down", "left", "right"

        Returns:
            True if navigation was handled
        """
        # Sync current selection to navigator
        selected = self._graph.selected_nodes()
        if selected:
            self._keyboard_navigator.set_current_node(selected[0].id)

        result = self._keyboard_navigator.navigate(direction)
        if result:
            self._update_focus_ring()

        return result

    def _update_focus_ring(self) -> None:
        """Update focus ring to surround current keyboard-navigated node."""
        node_id = self._keyboard_navigator.current_node_id
        if not node_id:
            self._hide_focus_ring()
            return

        # Find the node's view item
        for node in self._graph.all_nodes():
            if node.id == node_id:
                if hasattr(node, "view") and node.view:
                    self._show_focus_ring(node.view)
                return

        self._hide_focus_ring()

    def _show_focus_ring(self, node_item) -> None:
        """Show focus ring around a node item."""
        if self._focus_ring_manager is None:
            scene = self._graph.viewer().scene()
            if scene:
                self._focus_ring_manager = FocusRingManager(scene)

        if self._focus_ring_manager:
            self._focus_ring_manager.show_focus(node_item)

    def _hide_focus_ring(self) -> None:
        """Hide the focus ring."""
        if self._focus_ring_manager:
            self._focus_ring_manager.hide_focus()

    @property
    def keyboard_navigator(self) -> KeyboardNavigator:
        """Get the keyboard navigator."""
        return self._keyboard_navigator

    def fit_to_all(self) -> None:
        """Fit view to all nodes (Ctrl+1)."""
        nodes = self._graph.all_nodes()
        if nodes:
            self._graph.fit_to_selection()

    def _alt_drag_duplicate(self, event) -> bool:
        """Handle Alt+LMB drag to duplicate node under cursor."""
        try:
            viewer = self._graph.viewer()
            view_pos = viewer.mapFromGlobal(event.globalPosition().toPoint())
            node = self._selection_handler.get_node_at_view_pos(view_pos)

            if not node:
                return False

            scene_pos = viewer.mapToScene(view_pos)
            orig_x, orig_y = node.pos()

            self._graph.copy_nodes([node])
            self._graph.paste_nodes()

            selected = self._graph.selected_nodes()
            new_node = None
            for n in selected:
                if n != node:
                    new_node = n
                    break

            if not new_node:
                for n in self._graph.all_nodes():
                    if n != node and hasattr(n, "view"):
                        nx, ny = n.pos()
                        if abs(nx - orig_x) < 150 and abs(ny - orig_y) < 150:
                            new_node = n
                            break

            if not new_node:
                return False

            self._event_handler._alt_drag_offset_x = scene_pos.x() - orig_x
            self._event_handler._alt_drag_offset_y = scene_pos.y() - orig_y
            self._event_handler._alt_drag_node = new_node

            new_node.set_pos(
                scene_pos.x() - self._event_handler._alt_drag_offset_x,
                scene_pos.y() - self._event_handler._alt_drag_offset_y,
            )

            view_item = new_node.view
            if view_item:
                view_item.setZValue(view_item.zValue() + 1000)
                view_item.prepareGeometryChange()
                view_item.update()

            self._graph.clear_selection()
            new_node.set_selected(True)
            if view_item:
                view_item.setSelected(True)

            logger.debug(
                f"Alt+drag duplicated node: {node.name()} -> {new_node.name()}"
            )
            return True

        except Exception as e:
            logger.error(f"Alt+drag duplicate failed: {e}")
            return False

    def _alt_drag_move(self, event) -> bool:
        """Update position of Alt+drag duplicate node during mouse move."""
        if not self._event_handler.alt_drag_node:
            return False

        try:
            viewer = self._graph.viewer()
            view_pos = viewer.mapFromGlobal(event.globalPosition().toPoint())
            scene_pos = viewer.mapToScene(view_pos)

            self._event_handler.alt_drag_node.set_pos(
                scene_pos.x() - self._event_handler._alt_drag_offset_x,
                scene_pos.y() - self._event_handler._alt_drag_offset_y,
            )
            return True
        except Exception as e:
            logger.debug(f"Alt+drag move error: {e}")
            return False

    def _create_subflow_from_selection(self) -> bool:
        """Create a subflow from the currently selected nodes."""
        return self._selection_handler.create_subflow_from_selection(self)

    # =========================================================================
    # PORT LEGEND
    # =========================================================================

    def _toggle_port_legend(self) -> None:
        """Toggle the port legend panel visibility."""
        if hasattr(self, "_port_legend") and self._port_legend:
            self._port_legend.toggle_legend()

    def show_port_legend(self) -> None:
        """Show the port legend panel."""
        if hasattr(self, "_port_legend") and self._port_legend:
            self._port_legend.show_legend()

    def hide_port_legend(self) -> None:
        """Hide the port legend panel."""
        if hasattr(self, "_port_legend") and self._port_legend:
            self._port_legend.hide_legend()

    @property
    def port_legend(self) -> "PortLegendPanel":
        """Get the port legend panel."""
        return self._port_legend

    # =========================================================================
    # PASTE HOOK FOR DUPLICATE ID DETECTION
    # =========================================================================

    def _setup_paste_hook(self) -> None:
        """Setup hooks to regenerate node IDs after paste operations."""
        try:
            if hasattr(self._graph, "node_created"):
                self._graph.node_created.connect(self._on_node_created_check_duplicate)
                logger.debug("Paste hook for duplicate ID detection enabled")
        except Exception as e:
            logger.warning(f"Could not setup paste hook: {e}")

    def _on_node_created_check_duplicate(self, node) -> None:
        """Handle node creation/paste events."""
        from PySide6.QtCore import QTimer

        visual_class = node.__class__
        if getattr(visual_class, "COMPOSITE_NODE", False):
            self._handle_composite_node_creation(node)
            return

        QTimer.singleShot(0, lambda: self._deferred_duplicate_check(node))

    def _deferred_duplicate_check(self, node) -> None:
        """Deferred duplicate ID check after properties are fully restored."""
        from casare_rpa.utils.id_generator import generate_node_id

        if node not in self._graph.all_nodes():
            return

        node_class_name = type(node).__name__
        if "Reroute" in node_class_name:
            return

        current_id = node.get_property("node_id")
        casare_node = self._ensure_casare_node(node)

        if not casare_node:
            logger.warning(f"Could not get/create casare_node for {node.name()}")
            return

        if not current_id:
            node.set_property("node_id", casare_node.node_id)
            self._register_node_id(casare_node.node_id)
        else:
            is_duplicate = self._check_for_duplicate_id(node, current_id)

            if is_duplicate:
                node_type = (
                    getattr(casare_node, "node_type", None)
                    or type(casare_node).__name__
                )
                new_id = generate_node_id(node_type)
                casare_node.node_id = new_id
                node.set_property("node_id", new_id)
                self._register_node_id(new_id)
                logger.info(f"Regenerated duplicate node ID: {current_id} -> {new_id}")
            else:
                if casare_node.node_id != current_id:
                    casare_node.node_id = current_id
                self._register_node_id(current_id)

        self._sync_visual_properties_to_casare_node(node, casare_node)

    def _ensure_casare_node(self, node):
        """Ensure the visual node has a linked casare_node."""
        casare_node = (
            node.get_casare_node() if hasattr(node, "get_casare_node") else None
        )

        if casare_node:
            return casare_node

        try:
            from casare_rpa.presentation.canvas.graph.node_registry import (
                get_node_factory,
                get_casare_node_mapping,
            )

            mapping = get_casare_node_mapping()
            if type(node) not in mapping:
                return None

            factory = get_node_factory()
            casare_node = factory.create_casare_node(node)

            if casare_node:
                logger.info(f"Created missing casare_node for {node.name()}")

            return casare_node

        except Exception as e:
            logger.error(f"Error creating casare_node for {node.name()}: {e}")
            return None

    def _check_for_duplicate_id(self, node, node_id: str) -> bool:
        """Check if another node already has the same node_id."""
        return node_id in self._node_ids_in_use

    def _register_node_id(self, node_id: str) -> None:
        """Register a node ID in the tracking set."""
        if node_id:
            self._node_ids_in_use.add(node_id)

    def _sync_visual_properties_to_casare_node(self, visual_node, casare_node) -> None:
        """Sync visual node properties to casare_node.config after paste."""
        try:
            if not hasattr(visual_node, "model"):
                return

            model = visual_node.model
            custom_props = list(model.custom_properties.keys()) if model else []

            synced_count = 0
            for prop_name in custom_props:
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
                        casare_node.config[prop_name] = prop_value
                        synced_count += 1
                except Exception:
                    pass

            if synced_count > 0:
                logger.debug(f"Synced {synced_count} properties to pasted node")

        except Exception as e:
            logger.warning(f"Failed to sync properties for pasted node: {e}")

    def _handle_composite_node_creation(self, composite_node) -> None:
        """Handle creation of composite nodes."""
        self._composite_creator.handle_composite_node(composite_node)

    # =========================================================================
    # IMPORT CALLBACKS
    # =========================================================================

    def set_import_callback(self, callback) -> None:
        """Set callback for importing workflow data."""
        self._import_callback = callback

    def set_import_file_callback(self, callback) -> None:
        """Set callback for importing workflow from file."""
        self._import_file_callback = callback

    # =========================================================================
    # DRAG AND DROP SUPPORT
    # =========================================================================

    def setup_drag_drop(self) -> None:
        """Enable drag and drop support for importing workflow JSON files."""
        viewer = self._graph.viewer()
        viewer.setAcceptDrops(True)

        viewport = viewer.viewport()
        if viewport:
            viewport.setAcceptDrops(True)

        viewer.dragEnterEvent = self._handle_drag_enter
        viewer.dragMoveEvent = self._handle_drag_move
        viewer.dropEvent = self._handle_drop

        viewer.installEventFilter(self)
        if viewport:
            viewport.installEventFilter(self)

        self.setAcceptDrops(True)
        if hasattr(self._graph, "setAcceptDrops"):
            self._graph.setAcceptDrops(True)

        logger.info("Drag-drop support enabled for workflow import")

    def dragEnterEvent(self, event) -> None:
        """Handle drag enter at widget level."""
        self._handle_drag_enter(event)

    def dragMoveEvent(self, event) -> None:
        """Handle drag move at widget level."""
        self._handle_drag_move(event)

    def dropEvent(self, event) -> None:
        """Handle drop at widget level."""
        self._handle_drop(event)

    def _handle_drag_enter(self, event) -> None:
        """Handle drag enter event."""
        mime_data = event.mimeData()

        if mime_data.hasFormat("application/x-casare-node"):
            event.acceptProposedAction()
            return

        if mime_data.hasFormat("application/x-casare-variable"):
            event.acceptProposedAction()
            return

        if mime_data.hasText():
            text = mime_data.text()
            if text.startswith("casare_node:"):
                event.acceptProposedAction()
                return
            if text.startswith("{{") and text.endswith("}}"):
                event.acceptProposedAction()
                return

        if mime_data.hasUrls():
            for url in mime_data.urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if file_path.lower().endswith(".json"):
                        event.acceptProposedAction()
                        return

        if mime_data.hasText():
            text = mime_data.text()
            if text.strip().startswith("{") and '"nodes"' in text:
                event.acceptProposedAction()
                return

        event.ignore()

    def _handle_drag_move(self, event) -> None:
        """Handle drag move event."""
        self._handle_drag_enter(event)

    def _handle_drop(self, event) -> None:
        """Handle drop event."""

        mime_data = event.mimeData()
        drop_pos = event.position() if hasattr(event, "position") else event.posF()

        viewer = self._graph.viewer()
        scene_pos = viewer.mapToScene(drop_pos.toPoint())
        position = (scene_pos.x(), scene_pos.y())

        # Handle variable drops
        if mime_data.hasFormat("application/x-casare-variable"):
            self._handle_variable_drop(event, mime_data, viewer, scene_pos)
            return

        # Handle node library drops
        if mime_data.hasFormat("application/x-casare-node"):
            data = mime_data.data("application/x-casare-node").data().decode()
            parts = data.split("|")
            if len(parts) >= 1:
                node_type = parts[0]
                identifier = parts[1] if len(parts) > 1 else ""
                self._create_node_at_position(node_type, identifier, position)
                event.acceptProposedAction()
                return

        # Handle casare_node: text format
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

    def _handle_variable_drop(self, event, mime_data, viewer, scene_pos) -> None:
        """Handle variable drops from Output Inspector."""
        import json as json_module
        from PySide6.QtWidgets import QLineEdit, QTextEdit, QGraphicsProxyWidget

        variable_text = None
        try:
            data_bytes = mime_data.data("application/x-casare-variable")
            data_str = bytes(data_bytes).decode("utf-8")
            data = json_module.loads(data_str)
            variable_text = data.get("variable", "")
        except Exception:
            pass

        if not variable_text and mime_data.hasText():
            text = mime_data.text()
            if text.startswith("{{") and text.endswith("}}"):
                variable_text = text

        if not variable_text:
            event.ignore()
            return

        drop_pos = event.position() if hasattr(event, "position") else event.posF()
        items = viewer.items(drop_pos.toPoint())

        for item in items:
            if isinstance(item, QGraphicsProxyWidget):
                widget = item.widget()
                if not widget:
                    continue

                widget_pos = item.mapFromScene(scene_pos).toPoint()
                target = widget.childAt(widget_pos) or widget

                while target:
                    if isinstance(target, QLineEdit):
                        cursor_pos = target.cursorPosition()
                        current_text = target.text()
                        new_text = (
                            current_text[:cursor_pos]
                            + variable_text
                            + current_text[cursor_pos:]
                        )
                        target.setText(new_text)
                        target.setCursorPosition(cursor_pos + len(variable_text))
                        target.setFocus()
                        event.acceptProposedAction()
                        return

                    if isinstance(target, QTextEdit):
                        target.insertPlainText(variable_text)
                        target.setFocus()
                        event.acceptProposedAction()
                        return

                    target = target.parent() if hasattr(target, "parent") else None

        event.ignore()

    def _create_node_at_position(
        self, node_type: str, identifier: str, position: tuple
    ) -> None:
        """Create a node at the specified position."""
        self._creation_helper.create_node_at_position(node_type, identifier, position)

    def _show_connection_search(self, source_port, scene_pos):
        """Show node context menu and auto-connect created node."""

        def node_created_handler(node, port):
            self._auto_connect_new_node(node, port)

        self._connection_handler.show_connection_search(
            source_port, scene_pos, node_created_handler
        )

    def _auto_connect_new_node(self, new_node, source_port_item):
        """Auto-connect a newly created node to the source port."""
        self._creation_helper.auto_connect_new_node(new_node, source_port_item)

    def _create_set_variable_for_port(self, source_port_item):
        """Create a SetVariable node connected to the clicked output port."""
        if hasattr(self, "_set_variable_y_offset"):
            self._creation_helper.y_offset = self._set_variable_y_offset
        if hasattr(self, "_set_variable_x_gap"):
            self._creation_helper.x_gap = self._set_variable_x_gap

        self._creation_helper.create_set_variable_for_port(source_port_item)

    # =========================================================================
    # OUTPUT INSPECTOR POPUP
    # =========================================================================

    def show_output_inspector(
        self,
        node_id: str,
        node_name: str,
        output_data,
        global_pos,
        node_item=None,
    ) -> None:
        """Show the Node Output Inspector popup for a node."""
        from casare_rpa.presentation.canvas.ui.widgets.node_output_popup import (
            NodeOutputPopup,
        )
        from PySide6.QtCore import QPoint

        if not hasattr(self, "_output_popup") or self._output_popup is None:
            self._output_popup = NodeOutputPopup(self)
            self._output_popup.closed.connect(self._on_output_popup_closed)

            # Set main_window reference on variables view for VariableProvider access
            if hasattr(self._output_popup, "_variables_view"):
                # Find main window from parent hierarchy
                main_window = self._find_main_window()
                if main_window:
                    self._output_popup._variables_view.set_main_window(main_window)

        popup = self._output_popup
        popup.set_node(node_id, node_name)

        if output_data:
            popup.set_data(output_data)
        else:
            popup.set_data({})

        if isinstance(global_pos, QPoint):
            adjusted_pos = QPoint(global_pos.x(), global_pos.y() + 5)
        else:
            adjusted_pos = QPoint(int(global_pos.x()), int(global_pos.y()) + 5)

        popup.show_at_position(adjusted_pos)

        if node_item is not None:
            view = self._graph.viewer()
            if view:
                popup.start_tracking_node(node_item, view)

    def _find_main_window(self):
        """Find the MainWindow in the parent hierarchy."""
        from casare_rpa.presentation.canvas.main_window import MainWindow

        parent = self.parent()
        while parent is not None:
            if isinstance(parent, MainWindow):
                return parent
            parent = parent.parent() if hasattr(parent, "parent") else None
        return None

    def _on_output_popup_closed(self) -> None:
        """Handle output popup close event."""
        if hasattr(self, "_output_popup") and self._output_popup:
            if not self._output_popup.is_pinned:
                self._output_popup = None

    def close_output_popup(self) -> None:
        """Close the output inspector popup if open and not pinned."""
        if hasattr(self, "_output_popup") and self._output_popup:
            if not self._output_popup.is_pinned:
                self._output_popup.close()
                self._output_popup = None

    def update_output_inspector(self, node_id: str, output_data) -> None:
        """Update the output inspector if it's showing for the specified node."""
        if not hasattr(self, "_output_popup") or self._output_popup is None:
            return

        if self._output_popup.node_id == node_id:
            if output_data:
                self._output_popup.set_data(output_data)
            else:
                self._output_popup.set_data({})

    def cleanup(self) -> None:
        """Clean up resources to prevent memory leaks."""
        self._graph_setup.cleanup()

        if hasattr(self, "_output_popup") and self._output_popup:
            self._output_popup.close()
            self._output_popup = None

        if hasattr(self, "_culler") and self._culler:
            self._culler.clear()

        # Clean up focus ring manager
        if hasattr(self, "_focus_ring_manager") and self._focus_ring_manager:
            self._focus_ring_manager.remove()
            self._focus_ring_manager = None

        logger.debug("NodeGraphWidget cleanup completed")

    def closeEvent(self, event) -> None:
        """Handle widget close event."""
        self.cleanup()
        super().closeEvent(event)
