"""
Node Creation Helper for CasareRPA Canvas.

Handles node creation operations including:
- Drag-and-drop node creation
- SetVariable node creation from port MMB click
- Auto-connect after node creation

Follows Single Responsibility Principle - handles node creation assistance only.
"""

from typing import Optional, Tuple, TYPE_CHECKING

from loguru import logger
from PySide6.QtCore import QObject, QPointF, QRectF

if TYPE_CHECKING:
    from NodeGraphQt import NodeGraph


class NodeCreationHelper(QObject):
    """
    Assists with node creation operations on the canvas.

    Handles:
    - Creating nodes from drag-drop
    - Creating SetVariable nodes from port MMB click
    - Auto-connecting newly created nodes

    Usage:
        helper = NodeCreationHelper(graph)
        helper.create_set_variable_for_port(port_item)
    """

    # Default offsets for SetVariable positioning
    DEFAULT_Y_OFFSET = 150
    DEFAULT_X_GAP = 150

    def __init__(
        self,
        graph: "NodeGraph",
        parent: Optional[QObject] = None,
        y_offset: float = DEFAULT_Y_OFFSET,
        x_gap: float = DEFAULT_X_GAP,
    ) -> None:
        """
        Initialize node creation helper.

        Args:
            graph: The NodeGraphQt NodeGraph instance
            parent: Optional parent QObject
            y_offset: Vertical offset for SetVariable nodes
            x_gap: Horizontal gap for SetVariable nodes
        """
        super().__init__(parent)
        self._graph = graph
        self._y_offset = y_offset
        self._x_gap = x_gap

    @property
    def graph(self) -> "NodeGraph":
        """Get the underlying graph."""
        return self._graph

    @property
    def y_offset(self) -> float:
        """Get vertical offset for SetVariable nodes."""
        return self._y_offset

    @y_offset.setter
    def y_offset(self, value: float) -> None:
        """Set vertical offset for SetVariable nodes."""
        self._y_offset = value

    @property
    def x_gap(self) -> float:
        """Get horizontal gap for SetVariable nodes."""
        return self._x_gap

    @x_gap.setter
    def x_gap(self, value: float) -> None:
        """Set horizontal gap for SetVariable nodes."""
        self._x_gap = value

    def create_node_at_position(
        self, node_type: str, identifier: str, position: Tuple[float, float]
    ) -> Optional[object]:
        """
        Create a node at the specified position from a drag-drop operation.

        Args:
            node_type: The node class name
            identifier: The node identifier prefix
            position: Tuple of (x, y) scene coordinates

        Returns:
            The created node or None if creation failed
        """
        try:
            from .node_registry import get_node_registry

            registry = get_node_registry()

            # Find the visual node class by __name__
            visual_class = None
            for category in registry.get_categories():
                for node_class in registry.get_nodes_by_category(category):
                    if node_class.__name__ == node_type:
                        visual_class = node_class
                        break
                if visual_class:
                    break

            if visual_class:
                # Build the full node identifier for NodeGraphQt
                node_identifier = getattr(visual_class, "__identifier__", identifier)
                node_name = getattr(visual_class, "NODE_NAME", node_type)

                full_type = (
                    f"{node_identifier}.{node_name}" if node_identifier else node_name
                )
                logger.debug(f"Creating node with type: {full_type}")

                # Create the node
                node = self._graph.create_node(full_type)
                if node:
                    node.set_pos(position[0], position[1])
                    logger.info(f"Created node {node_name} at {position}")
                    return node
                else:
                    logger.warning(f"create_node returned None for: {full_type}")
            else:
                logger.warning(
                    f"Could not find visual class for node type: {node_type}"
                )

            return None

        except Exception as e:
            logger.error(f"Failed to create node from drop: {e}", exc_info=True)
            return None

    def auto_connect_new_node(self, new_node, source_port_item) -> bool:
        """
        Auto-connect a newly created node to the source port.

        Args:
            new_node: The newly created node
            source_port_item: The port item that was dragged from (PortItem from viewer)

        Returns:
            True if connection was made, False otherwise
        """
        try:
            from NodeGraphQt.constants import PortTypeEnum

            # Determine if source is input or output
            is_source_output = source_port_item.port_type == PortTypeEnum.OUT.value

            logger.debug(
                f"Auto-connecting from {'output' if is_source_output else 'input'} "
                f"port: {source_port_item.name}"
            )

            # Find compatible port on new node and connect
            if is_source_output:
                # Source is output, find input on new node
                for port in new_node.input_ports():
                    target_port_item = port.view
                    try:
                        source_port_item.connect_to(target_port_item)
                        logger.info(
                            f"Auto-connected {source_port_item.name} -> {target_port_item.name}"
                        )
                        return True
                    except Exception as e:
                        logger.debug(
                            f"Could not connect to {target_port_item.name}: {e}"
                        )
                        continue
            else:
                # Source is input, find output on new node
                for port in new_node.output_ports():
                    target_port_item = port.view
                    try:
                        target_port_item.connect_to(source_port_item)
                        logger.info(
                            f"Auto-connected {target_port_item.name} -> {source_port_item.name}"
                        )
                        return True
                    except Exception as e:
                        logger.debug(
                            f"Could not connect to {target_port_item.name}: {e}"
                        )
                        continue

            return False

        except Exception as e:
            logger.error(f"Failed to auto-connect new node: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return False

    def create_set_variable_for_port(self, source_port_item) -> Optional[object]:
        """
        Create a SetVariable node connected to the clicked output port.

        Args:
            source_port_item: The output port item that was clicked (PortItem from viewer)

        Returns:
            The created SetVariable node or None if creation failed
        """
        try:
            # Get the source node from the port item
            source_node = self._get_node_from_port_item(source_port_item)
            if not source_node:
                logger.warning("Could not find source node from port item")
                return None

            port_name = source_port_item.name

            # Get node name for logging
            node_name = self._get_node_name(source_node)
            logger.info(f"Creating SetVariable for port: {node_name}.{port_name}")

            # Calculate position
            source_scene_pos, source_width = self._get_node_position_and_width(
                source_node
            )
            port_scene_pos = source_port_item.scenePos()
            port_y = port_scene_pos.y()

            # Initial position: right of source node + gap, with y offset
            initial_x = source_scene_pos.x() + source_width + self._x_gap
            initial_y = port_y + self._y_offset

            # Create the SetVariable node
            set_var_node = self._graph.create_node(
                "casare_rpa.variable.VisualSetVariableNode",
                pos=[initial_x, initial_y],
            )

            if not set_var_node:
                logger.error("Failed to create SetVariable node")
                return None

            # Set the variable name to the output port's name
            set_var_node.set_property("variable_name", port_name)

            # Set default_value from source port's last output (if available)
            # source_node may be NodeItem (graphics) or VisualNode - handle both
            visual_node = source_node
            if not hasattr(visual_node, "get_last_output") and hasattr(
                source_node, "node"
            ):
                visual_node = source_node.node

            if hasattr(visual_node, "get_last_output"):
                last_output = visual_node.get_last_output()
                if last_output and port_name in last_output:
                    port_value = last_output[port_name]
                    value_str = str(port_value) if port_value is not None else ""
                    set_var_node.set_property("default_value", value_str)
                    logger.debug(
                        f"Set default_value from port output: {value_str[:100]}"
                    )

            logger.debug(
                f"SetVariable node created at ({initial_x}, {initial_y}) "
                f"with name '{port_name}'"
            )

            # Refine position to avoid overlaps
            self._refine_node_position(
                set_var_node, source_scene_pos, source_width, port_y
            )

            # Connect the source output port to the "value" input
            self._connect_to_set_variable(source_port_item, set_var_node)

            return set_var_node

        except Exception as e:
            logger.error(f"Failed to create SetVariable for port: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return None

    def _get_node_from_port_item(self, port_item):
        """Get the node object from a port item."""
        node_item = port_item.parentItem()

        # Try different ways to get the node
        if node_item and hasattr(node_item, "node"):
            return node_item.node

        if hasattr(port_item, "node"):
            return port_item.node

        # Walk up parent chain
        parent = node_item
        while parent:
            if hasattr(parent, "node"):
                return parent.node
            parent = parent.parentItem() if hasattr(parent, "parentItem") else None

        return None

    def _get_node_name(self, node) -> str:
        """Get the display name of a node."""
        if callable(getattr(node, "name", None)):
            return node.name()
        return getattr(node, "name", str(node))

    def _get_node_position_and_width(self, node) -> Tuple[QPointF, float]:
        """Get node scene position and width."""
        source_view = getattr(node, "view", None)
        if source_view is not None:
            source_scene_pos = source_view.scenePos()
            try:
                source_width = source_view.boundingRect().width()
            except Exception:
                source_width = 200
            return source_scene_pos, source_width

        # Fallback to node.pos property
        raw_pos = (
            node.pos()
            if callable(getattr(node, "pos", None))
            else getattr(node, "pos", (0, 0))
        )
        if isinstance(raw_pos, (list, tuple)):
            return QPointF(raw_pos[0], raw_pos[1]), 200
        elif raw_pos is not None:
            return QPointF(raw_pos.x(), raw_pos.y()), 200
        return QPointF(0, 0), 200

    def _refine_node_position(
        self,
        set_var_node,
        source_scene_pos: QPointF,
        source_width: float,
        port_y: float,
    ) -> None:
        """Refine SetVariable node position to avoid overlaps."""
        try:
            new_view = getattr(set_var_node, "view", None)
            if new_view is None:
                new_view = set_var_node.view if hasattr(set_var_node, "view") else None

            # Compute dimensions
            new_width = new_view.boundingRect().width() if new_view else 150
            new_height = new_view.boundingRect().height() if new_view else 120

            # Target position
            target_x = source_scene_pos.x() + source_width + self._x_gap
            target_y = port_y - (new_height / 2) + self._y_offset

            # Set initial position
            self._set_node_position(set_var_node, new_view, target_x, target_y)

            # Avoid overlaps
            viewer = self._graph.viewer()
            scene = viewer.scene()

            for attempt in range(6):
                if new_view is None:
                    break

                new_rect: QRectF = new_view.sceneBoundingRect()
                colliding_items = [
                    it
                    for it in scene.items(new_rect)
                    if it is not new_view
                    and it.__class__.__name__ == new_view.__class__.__name__
                ]
                colliding_nodes = [it for it in colliding_items if hasattr(it, "node")]

                if not colliding_nodes:
                    break

                # Bump to the right
                target_x += new_width + 50
                self._set_node_position(set_var_node, new_view, target_x, target_y)
                logger.debug(
                    f"Adjusted SetVariable position: attempt {attempt + 1}, x={target_x}"
                )

            # Select the new node
            self._graph.clear_selection()
            set_var_node.set_selected(True)

        except Exception as e:
            logger.debug(f"Could not refine SetVariable position: {e}")

    def _set_node_position(self, node, view, x: float, y: float) -> None:
        """Set node position using node API or view fallback."""
        try:
            if hasattr(node, "set_pos"):
                try:
                    node.set_pos(x, y)
                except TypeError:
                    node.set_pos([x, y])
                return
        except Exception:
            pass

        if view is not None:
            view.setPos(QPointF(x, y))

    def _connect_to_set_variable(self, source_port_item, set_var_node) -> bool:
        """Connect source port to SetVariable's value input."""
        value_port = None
        for port in set_var_node.input_ports():
            pname = (
                port.name()
                if callable(getattr(port, "name", None))
                else getattr(port, "name", None)
            )
            if pname == "value":
                value_port = port
                break

        if value_port:
            target_port_item = getattr(value_port, "view", None)
            try:
                source_port_item.connect_to(target_port_item)
                logger.info(f"Connected {source_port_item.name} -> value")
                return True
            except Exception as e:
                logger.warning(f"Could not connect ports: {e}")
        else:
            logger.warning("Could not find 'value' input port on SetVariable node")

        return False
