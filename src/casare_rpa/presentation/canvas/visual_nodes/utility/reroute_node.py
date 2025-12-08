"""
Visual Reroute Node - Houdini-style passthrough dot.

This visual node uses a custom graphics item (RerouteNodeItem) to render
as a small diamond shape instead of a full node with header and widgets.

Used for organizing wire routing in complex workflows.
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QPen, QBrush, QColor
from NodeGraphQt import BaseNode as NodeGraphQtBaseNode

from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.presentation.canvas.graph.reroute_node_item import RerouteNodeItem
from casare_rpa.presentation.canvas.graph.custom_pipe import TYPE_WIRE_COLORS

# Port circle radius
_PORT_RADIUS = 5.0

# Default type color (gray for ANY)
_DEFAULT_TYPE_COLOR = QColor(128, 128, 128)


def _circle_port_painter(painter, rect, info):
    """
    Draw a small circle at the port connection point.

    This draws circles exactly where wires connect, ensuring perfect alignment.
    The rect center is where NodeGraphQt connects wires.
    """
    painter.setRenderHint(painter.RenderHint.Antialiasing)

    # Get center of port rect - this is where wires connect
    center = rect.center()

    # Get color from node if available
    color = _DEFAULT_TYPE_COLOR
    node = info.get("node")
    if node and hasattr(node, "view") and hasattr(node.view, "get_type_color"):
        color = node.view.get_type_color()

    # Draw filled circle with darker border
    painter.setBrush(QBrush(color))
    painter.setPen(QPen(color.darker(120), 1.0))
    painter.drawEllipse(center, _PORT_RADIUS, _PORT_RADIUS)


class VisualRerouteNode(NodeGraphQtBaseNode):
    """
    Visual representation of RerouteNode.

    A minimal diamond-shaped node for wire organization.
    No header, no widgets, just a small clickable dot.
    """

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Reroute"
    NODE_CATEGORY = "utility"

    def __init__(self) -> None:
        """Initialize visual reroute node with custom item."""
        # Use custom RerouteNodeItem for minimal rendering
        super().__init__(qgraphics_item=RerouteNodeItem)

        # Reference to the underlying CasareRPA node
        from casare_rpa.domain.entities.base_node import BaseNode as CasareBaseNode

        self._casare_node: Optional[CasareBaseNode] = None

        # Port type tracking
        self._port_types: dict[str, Optional[DataType]] = {}

        # Configure minimal properties
        self.create_property("node_id", "")
        self.create_property("data_type", "ANY")
        self.create_property("is_exec_reroute", False)

        # Setup ports
        self.setup_ports()

        # Ensure back-reference from view to node
        if hasattr(self, "view") and self.view is not None:
            self.view._node = self

    def set_property(self, name: str, value, push_undo: bool = True) -> None:
        """
        Override to restore _port_types when is_exec_reroute or data_type is set.

        This ensures proper port type detection after deserialization.
        """
        super().set_property(name, value, push_undo)

        # Restore port types from saved properties
        if name == "is_exec_reroute" and value:
            # Exec reroute - set port types to None
            self._port_types["in"] = None
            self._port_types["out"] = None
        elif name == "data_type":
            if value == "EXEC":
                self._port_types["in"] = None
                self._port_types["out"] = None
            elif value and value != "ANY":
                try:
                    data_type = DataType(value)
                    self._port_types["in"] = data_type
                    self._port_types["out"] = data_type
                except (ValueError, KeyError):
                    pass  # Keep existing type

    def setup_ports(self) -> None:
        """Setup single input and output ports."""
        # Single input and output with circle painter
        # Use display_name=False to hide text labels
        # Circle painter draws at exact wire connection point
        self.add_input(
            "in",
            display_name=False,
            painter_func=_circle_port_painter,
        )
        self.add_output(
            "out",
            display_name=False,
            painter_func=_circle_port_painter,
        )

        # Track as ANY type by default
        self._port_types["in"] = DataType.ANY
        self._port_types["out"] = DataType.ANY

    def update_type_from_connection(self, data_type: Optional[DataType]) -> None:
        """
        Update the visual type color when a connection is made.

        Args:
            data_type: DataType from the connected wire, or None for exec
        """
        # Update port types
        self._port_types["in"] = data_type
        self._port_types["out"] = data_type

        # Update visual
        if hasattr(self.view, "set_type_color"):
            if data_type is None:
                # Execution flow - white
                from PySide6.QtGui import QColor

                self.view.set_type_color(QColor(255, 255, 255))
            elif data_type in TYPE_WIRE_COLORS:
                self.view.set_type_color(TYPE_WIRE_COLORS[data_type])
            else:
                # Default gray for unknown types
                from PySide6.QtGui import QColor

                self.view.set_type_color(QColor(128, 128, 128))

        # Update property
        if data_type is None:
            self.set_property("data_type", "EXEC")
            self.set_property("is_exec_reroute", True)
        else:
            self.set_property("data_type", data_type.value)
            self.set_property("is_exec_reroute", False)

    def get_casare_node(self):
        """Get the underlying CasareRPA node instance."""
        return self._casare_node

    def set_casare_node(self, node) -> None:
        """Set the underlying CasareRPA node instance."""
        self._casare_node = node
        if node:
            self.set_property("node_id", node.node_id)

    def get_port_type(self, port_name: str) -> Optional[DataType]:
        """
        Get the DataType for a port.

        Args:
            port_name: Name of the port

        Returns:
            DataType if it's a data port, None if exec
        """
        return self._port_types.get(port_name, DataType.ANY)

    def is_exec_port(self, port_name: str) -> bool:
        """
        Check if a port is an execution flow port.

        Args:
            port_name: Name of the port

        Returns:
            True if this is an execution port
        """
        return self._port_types.get(port_name) is None
