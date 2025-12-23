"""
Event filters for CasareRPA Canvas.

Contains Qt event filters used by NodeGraphWidget for handling
various mouse and keyboard interactions.

Follows Single Responsibility Principle - each filter handles one interaction type.
"""

from loguru import logger
from PySide6.QtCore import QEvent, QObject, Qt


class TooltipBlocker(QObject):
    """Event filter to block tooltips on the graph canvas."""

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.ToolTip:
            return True
        return False


class OutputPortMMBFilter(QObject):
    """
    Event filter to detect middle mouse button clicks on output ports and node bodies.

    Creates a SetVariable node connected to the clicked output port,
    or shows the output inspector when clicking on a node body.
    Excludes exec ports (exec_in, exec_out, etc.)

    Behavior:
        - LMB: Normal behavior (drag connection)
        - MMB on output port: Create SetVariable node
        - MMB on node body: Show output inspector popup
        - MMB on empty space: Pan viewport (default behavior)
    """

    # Common exec port names to exclude
    EXEC_PORT_NAMES = {
        "exec_in",
        "exec_out",
        "exec",
        "true",
        "false",
        "loop_body",
        "completed",
        "try",
        "catch",
        "finally",
        "on_success",
        "on_failure",
        "on_error",
        "then",
        "else",
    }

    def __init__(self, graph, widget):
        super().__init__()
        self._graph = graph
        self._widget = widget

    def eventFilter(self, obj, event):
        """Handle middle mouse button click."""
        # Only handle MouseButtonPress
        if event.type() != QEvent.Type.MouseButtonPress:
            return False

        if event.button() != Qt.MouseButton.MiddleButton:
            return False

        viewer = self._graph.viewer()
        if not viewer:
            return False

        # Get scene position
        scene_pos = viewer.mapToScene(event.pos())

        # First, check if click is on an output port
        port_item = self._find_port_at_position(viewer, scene_pos)

        if port_item:
            # Check if this is an output port (not input)
            from NodeGraphQt.constants import PortTypeEnum

            if port_item.port_type == PortTypeEnum.OUT.value:
                # Check if this is an exec port - skip those
                if not self._is_exec_port(port_item):
                    # Create SetVariable node
                    try:
                        self._widget._create_set_variable_for_port(port_item)
                    except Exception as e:
                        logger.error(f"Failed to create SetVariable: {e}")
                    return True  # Block the event to prevent panning

        # If not on a port, check if click is on a node body
        node_item = self._find_node_at_position(viewer, scene_pos)
        if node_item:
            # Show output inspector for this node
            try:
                self._show_output_inspector_for_node(node_item, event)
            except Exception as e:
                logger.error(f"Failed to show output inspector: {e}")
            return True  # Block the event to prevent panning

        return False  # Not on a port or node, let panning happen

    def _find_port_at_position(self, viewer, scene_pos):
        """Find a port item at the given scene position."""
        items = viewer.scene().items(scene_pos)

        for item in items:
            class_name = item.__class__.__name__
            if "Port" in class_name or class_name == "PortItem":
                return item
        return None

    def _find_node_at_position(self, viewer, scene_pos):
        """Find a node item at the given scene position."""
        items = viewer.scene().items(scene_pos)

        for item in items:
            class_name = item.__class__.__name__
            # Check for CasareNodeItem, SubflowNodeItem, or generic NodeItem
            if "NodeItem" in class_name and "Reroute" not in class_name:
                return item
        return None

    def _show_output_inspector_for_node(self, node_item, event):
        """Show the output inspector popup for a node."""
        # Get the VisualNode instance
        node = getattr(node_item, "_node", None)
        if not node:
            logger.debug("Cannot show output inspector: no visual node attached")
            return

        # Get output data from the visual node
        output_data = None
        if hasattr(node, "_last_output"):
            output_data = node._last_output

        # Get node ID and name
        node_id = node.get_property("node_id") if hasattr(node, "get_property") else node.id
        node_name = node.name() if callable(node.name) else str(node.name)

        # Calculate popup position (bottom-left of node)
        viewer = self._graph.viewer()
        node_rect = node_item.sceneBoundingRect()
        bottom_left_scene = node_rect.bottomLeft()
        view_pos = viewer.mapFromScene(bottom_left_scene)
        global_pos = viewer.mapToGlobal(view_pos)

        # Show the output inspector
        self._widget.show_output_inspector(node_id, node_name, output_data, global_pos, node_item)
        logger.debug(f"Showing output inspector for {node_name}")

    def _is_exec_port(self, port_item) -> bool:
        """
        Check if a port is an execution flow port.

        Exec ports typically have names like 'exec_in', 'exec_out',
        'true', 'false', 'loop_body', 'completed', etc.
        """
        port_name = port_item.name.lower()

        if port_name in self.EXEC_PORT_NAMES:
            return True

        # Check if port has no data type (exec ports have None data type)
        try:
            node_item = port_item.parentItem()
            if node_item and hasattr(node_item, "node"):
                node = node_item.node
                if hasattr(node, "get_port_type"):
                    port_type = node.get_port_type(port_item.name)
                    if port_type is None:
                        return True
        except Exception as e:
            logger.debug(f"Could not check port type: {e}")

        return False


class ConnectionDropFilter(QObject):
    """
    Event filter to detect when a connection pipe is dropped on empty space.

    Shows a node search menu to create and auto-connect a new node.
    """

    def __init__(self, graph, widget):
        super().__init__()
        self._graph = graph
        self._widget = widget
        self._pending_source_port = None
        self._pending_scene_pos = None

    def eventFilter(self, obj, event):
        # Only handle left mouse button release
        if event.type() != QEvent.Type.MouseButtonRelease:
            return False

        if event.button() != Qt.MouseButton.LeftButton:
            return False

        viewer = self._graph.viewer()
        if not viewer:
            return False

        # Check if there's an active live pipe
        if not hasattr(viewer, "_LIVE_PIPE") or not viewer._LIVE_PIPE.isVisible():
            return False

        # Get the source port before it's cleared
        source_port = getattr(viewer, "_start_port", None)
        if not source_port:
            return False

        # Get scene position
        scene_pos = viewer.mapToScene(event.pos())

        # Check if dropped on a port
        items = viewer.scene().items(scene_pos)

        has_port = False
        for item in items:
            class_name = item.__class__.__name__
            if "Port" in class_name or class_name == "PortItem":
                has_port = True
                logger.debug(f"ConnectionDropFilter: Found port ({class_name}) at drop location")
                break

        if has_port:
            # Let NodeGraphQt handle normal connection
            return False

        # No port found - this is a drop on empty space
        logger.debug(
            f"ConnectionDropFilter: No port found at "
            f"({scene_pos.x():.0f}, {scene_pos.y():.0f}), showing search menu"
        )

        # Save port and schedule search menu
        self._pending_source_port = source_port
        self._pending_scene_pos = scene_pos

        from PySide6.QtCore import QTimer

        QTimer.singleShot(0, self._show_search_after_release)

        # Don't block the event - let NodeGraphQt clean up normally
        return False

    def _show_search_after_release(self):
        """Show search menu after the mouse release event has completed."""
        if not self._pending_source_port:
            return

        source_port = self._pending_source_port
        scene_pos = self._pending_scene_pos
        self._pending_source_port = None
        self._pending_scene_pos = None

        # Double-check: if a connection was made by NodeGraphQt, don't show menu
        try:
            if source_port is None or not hasattr(source_port, "connected_pipes"):
                logger.debug("ConnectionDropFilter: Source port no longer valid, skipping search")
                return
        except Exception as e:
            logger.debug(f"ConnectionDropFilter: Error checking connections: {e}")

        # Show the connection search
        self._widget._show_connection_search(source_port, scene_pos)
