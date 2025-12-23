"""
Reroute Node Insertion via Alt+LMB on Wire.

Allows inserting a reroute/dot node on an existing connection by Alt+clicking.
This creates a passthrough node that helps organize wire routing.

Usage:
    Alt + Left Mouse Button on wire -> Insert reroute node at click position
"""

import traceback

from loguru import logger
from NodeGraphQt import NodeGraph
from PySide6.QtCore import QObject, QPointF, Qt, Signal
from PySide6.QtGui import QPainterPathStroker

# Import layout constants from reroute_node_item for consistent positioning
from casare_rpa.presentation.canvas.graph.reroute_node_item import (
    _NODE_CENTER_X as REROUTE_CENTER_X,
)
from casare_rpa.presentation.canvas.graph.reroute_node_item import (
    _NODE_CENTER_Y as REROUTE_CENTER_Y,
)


class RerouteInsertManager(QObject):
    """
    Manages inserting reroute nodes on existing connections via Alt+LMB.

    Features:
    - Detects Alt+LMB click on any connection (exec or data)
    - Creates a reroute node at the click position
    - Splits the connection to pass through the reroute
    - Inherits wire type/color from the original connection
    """

    # Signal emitted when a reroute node is successfully inserted
    reroute_inserted = Signal(object, object, object)  # reroute_node, source_node, target_node

    def __init__(self, graph: NodeGraph, parent: QObject | None = None) -> None:
        """
        Initialize the reroute insert manager.

        Args:
            graph: The NodeGraph instance
            parent: Optional parent QObject
        """
        super().__init__(parent)
        self._graph = graph
        self._active = True

        # Install event filter on viewport
        self._setup_event_filter()

    def _setup_event_filter(self) -> None:
        """Install event filter on the graph viewport."""
        try:
            viewer = self._graph.viewer()
            if viewer and hasattr(viewer, "viewport"):
                viewport = viewer.viewport()
                if viewport:
                    viewport.installEventFilter(self)
                    logger.debug("RerouteInsertManager event filter installed")
        except Exception as e:
            logger.warning(f"Could not setup reroute insert event filter: {e}")

    def set_active(self, active: bool) -> None:
        """Enable or disable the reroute insert feature."""
        self._active = active

    def is_active(self) -> bool:
        """Check if reroute insert is active."""
        return self._active

    def eventFilter(self, watched, event) -> bool:
        """
        Filter events to detect Alt+LMB on pipes.

        Args:
            watched: The watched object
            event: The event

        Returns:
            True if event was handled, False otherwise
        """
        if not self._active:
            return False

        # Check for left mouse button press with Alt modifier
        if event.type() == event.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                modifiers = event.modifiers()
                if modifiers & Qt.KeyboardModifier.AltModifier:
                    # Get click position in scene coordinates
                    viewer = self._graph.viewer()
                    if viewer:
                        local_pos = event.position().toPoint()
                        scene_pos = viewer.mapToScene(local_pos)

                        # Check if we clicked on a pipe
                        pipe = self._find_pipe_at_position(scene_pos)
                        if pipe:
                            # Insert reroute node
                            self._insert_reroute_at_pipe(pipe, scene_pos)
                            return True  # Consume the event

        return False

    def _find_pipe_at_position(self, scene_pos: QPointF) -> object | None:
        """
        Find a pipe at the given scene position.

        Args:
            scene_pos: Position in scene coordinates

        Returns:
            The pipe item at that position, or None
        """
        try:
            viewer = self._graph.viewer()
            if not viewer or not viewer.scene():
                return None

            scene = viewer.scene()

            # Hit area for clicking (pixels)
            hit_radius = 15.0

            for item in scene.items():
                class_name = item.__class__.__name__

                # Check if this is a pipe
                if "Pipe" not in class_name:
                    continue

                # Must be a complete connection
                if not hasattr(item, "input_port") or not hasattr(item, "output_port"):
                    continue
                if not item.input_port or not item.output_port:
                    continue

                # Check if click is near the pipe path
                if hasattr(item, "path") and callable(item.path):
                    pipe_path = item.path()
                    if not pipe_path.isEmpty():
                        # Create a stroked path for hit testing
                        stroker = QPainterPathStroker()
                        stroker.setWidth(hit_radius * 2)  # Total width
                        stroked = stroker.createStroke(pipe_path)

                        # Map the stroked path to scene coordinates
                        scene_path = item.mapToScene(stroked)

                        # Check if click point is inside the stroked path
                        if scene_path.contains(scene_pos):
                            return item

            return None

        except Exception as e:
            logger.error(f"Error finding pipe at position: {e}")
            return None

    def _insert_reroute_at_pipe(self, pipe, scene_pos: QPointF) -> None:
        """
        Insert a reroute node at the given position on a pipe.

        Args:
            pipe: The pipe item to split
            scene_pos: Position to insert the reroute node
        """
        try:
            # Get source and target ports from the pipe
            source_port_item = pipe.output_port
            target_port_item = pipe.input_port

            if not source_port_item or not target_port_item:
                logger.warning("Pipe missing ports, cannot insert reroute")
                return

            # Get port names
            source_port_name = self._get_port_name(source_port_item)
            target_port_name = self._get_port_name(target_port_item)

            # Get node items from ports
            source_node_item = source_port_item.parentItem()
            target_node_item = target_port_item.parentItem()

            if not source_node_item or not target_node_item:
                logger.warning("Could not get node items from port items")
                return

            # Get node IDs
            source_node_id = source_node_item.id if hasattr(source_node_item, "id") else None
            target_node_id = target_node_item.id if hasattr(target_node_item, "id") else None

            if not source_node_id or not target_node_id:
                logger.warning("Could not get node IDs")
                return

            # Find model nodes by ID
            source_node = None
            target_node = None
            for model_node in self._graph.all_nodes():
                node_id = model_node.id() if callable(model_node.id) else model_node.id
                if node_id == source_node_id:
                    source_node = model_node
                elif node_id == target_node_id:
                    target_node = model_node
                if source_node and target_node:
                    break

            if not source_node or not target_node:
                logger.warning("Could not find model nodes")
                return

            # Get model ports
            source_port = source_node.get_output(source_port_name)
            target_port = target_node.get_input(target_port_name)

            if not source_port or not target_port:
                logger.warning("Could not get model ports")
                return

            # Determine port data type for reroute
            data_type = self._get_pipe_data_type(pipe)
            is_exec = data_type is None

            # Create the reroute node
            reroute_node = self._create_reroute_node(scene_pos, is_exec)
            if not reroute_node:
                logger.error("Failed to create reroute node")
                return

            # Get reroute ports
            reroute_in = reroute_node.get_input("in")
            reroute_out = reroute_node.get_output("out")

            if not reroute_in or not reroute_out:
                logger.error("Reroute node missing ports")
                # Clean up - delete the node
                try:
                    self._graph.delete_node(reroute_node)
                except Exception:
                    pass
                return

            # CRITICAL: Set port types BEFORE connecting to pass validation
            # The reroute must inherit the data type from the original connection
            if hasattr(reroute_node, "_port_types"):
                reroute_node._port_types["in"] = data_type
                reroute_node._port_types["out"] = data_type

            # Also call update_type_from_connection for visual color
            if hasattr(reroute_node, "update_type_from_connection"):
                reroute_node.update_type_from_connection(data_type)

            # Disconnect original connection
            try:
                source_port.disconnect_from(target_port)
            except Exception:
                try:
                    target_port.disconnect_from(source_port)
                except Exception as e:
                    logger.error(f"Failed to disconnect original pipe: {e}")
                    return

            # Connect through reroute: source -> reroute -> target
            connect_success = True
            try:
                source_port.connect_to(reroute_in)
            except Exception as e:
                logger.error(f"Failed to connect source to reroute: {e}")
                connect_success = False

            try:
                reroute_out.connect_to(target_port)
            except Exception as e:
                logger.error(f"Failed to connect reroute to target: {e}")
                connect_success = False

            if not connect_success:
                # Attempt to restore original connection
                try:
                    source_port.connect_to(target_port)
                    self._graph.delete_node(reroute_node)
                except Exception:
                    pass
                return

            # Note: update_type_from_connection already called before connecting

            logger.info(
                f"Inserted reroute node between "
                f"{self._get_node_name(source_node)} and {self._get_node_name(target_node)}"
            )

            # Emit signal
            self.reroute_inserted.emit(reroute_node, source_node, target_node)

        except Exception as e:
            logger.error(f"Error inserting reroute at pipe: {e}")
            logger.error(traceback.format_exc())

    def _create_reroute_node(self, position: QPointF, is_exec: bool) -> object | None:
        """
        Create a reroute node at the specified position.

        Args:
            position: Scene position for the node
            is_exec: True if this is an execution flow reroute

        Returns:
            The created reroute node, or None on failure
        """
        try:
            # Check if VisualRerouteNode is registered
            # First, try to get the node type from the graph
            node_types = self._graph.registered_nodes()

            # Look for the reroute node type
            reroute_type = None
            for node_type in node_types:
                if "Reroute" in str(node_type):
                    reroute_type = node_type
                    break

            # Offset position to center diamond on click point
            # Uses imported constants from reroute_node_item for consistency
            centered_pos = [
                position.x() - REROUTE_CENTER_X,
                position.y() - REROUTE_CENTER_Y,
            ]

            if reroute_type:
                # Create using the registered type
                reroute_node = self._graph.create_node(
                    reroute_type,
                    pos=centered_pos,
                )
            else:
                # Fallback: Try to register and create
                try:
                    from casare_rpa.presentation.canvas.visual_nodes.utility.reroute_node import (
                        VisualRerouteNode,
                    )

                    self._graph.register_node(VisualRerouteNode)
                    # Use the correct identifier format: __identifier__.VisualClassName
                    # NodeGraphQt uses this format after registration
                    identifier = f"{VisualRerouteNode.__identifier__}.VisualRerouteNode"
                    reroute_node = self._graph.create_node(
                        identifier,
                        pos=centered_pos,
                    )
                except Exception as e:
                    logger.error(f"Could not create reroute node: {e}")
                    return None

            # Set exec mode if needed
            if reroute_node and is_exec:
                if hasattr(reroute_node, "set_property"):
                    reroute_node.set_property("is_exec_reroute", True)

            return reroute_node

        except Exception as e:
            logger.error(f"Error creating reroute node: {e}")
            return None

    def _get_pipe_data_type(self, pipe):
        """
        Get the data type from a pipe's output port.

        Returns None for execution ports, DataType for data ports.
        """
        try:
            output_port = pipe.output_port
            if not output_port:
                return None

            # Get the node from the output port
            node = output_port.node() if hasattr(output_port, "node") else None
            if not node:
                return None

            # Get port type from node's _port_types dict
            port_name = output_port.name() if callable(output_port.name) else str(output_port.name)

            if hasattr(node, "_port_types"):
                data_type = node._port_types.get(port_name)
                return data_type  # None means execution port

            # Check if it's an exec port by name
            if port_name and "exec" in port_name.lower():
                return None  # Execution port

            # Default to ANY type
            from casare_rpa.domain.value_objects.types import DataType

            return DataType.ANY

        except Exception:
            return None

    def _get_port_name(self, port_item) -> str:
        """Get name from a port item."""
        if hasattr(port_item, "name"):
            if callable(port_item.name):
                return port_item.name()
            return str(port_item.name)
        return ""

    def _get_node_name(self, node) -> str:
        """Get name from a node."""
        if hasattr(node, "name"):
            if callable(node.name):
                return node.name()
            return str(node.name)
        return str(node)
