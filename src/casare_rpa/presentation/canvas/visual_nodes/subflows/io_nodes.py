"""
Subflow I/O Visual Nodes for CasareRPA.

Provides visual representation for SubflowInputNode and SubflowOutputNode.
These nodes allow users to define the subflow's interface visually.
"""

from typing import Any

from PySide6.QtCore import Slot

from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode


class VisualSubflowInputNode(VisualNode):
    """
    Visual node for defining a subflow input.
    """

    __identifier__ = "casare_rpa.workflow"
    NODE_NAME = "Subflow Input"
    NODE_CATEGORY = "workflow"

    def __init__(self) -> None:
        super().__init__()
        # Set a distinctive color for I/O nodes
        self.set_color(40, 100, 150)
        self.set_property("port_name", "input")

    def setup_ports(self) -> None:
        """Define ports for the input node."""
        self.add_typed_output("value", DataType.ANY)

    @Slot(str, object)
    def on_property_changed(self, name: str, value: Any) -> None:
        """Update node name when port name changes."""
        if name == "port_name":
            self.set_name(f"Input: {value}")
        super().on_property_changed(name, value)


class VisualSubflowOutputNode(VisualNode):
    """
    Visual node for defining a subflow output.
    """

    __identifier__ = "casare_rpa.workflow"
    NODE_NAME = "Subflow Output"
    NODE_CATEGORY = "workflow"

    def __init__(self) -> None:
        super().__init__()
        # Set a distinctive color for I/O nodes
        self.set_color(150, 100, 40)
        self.set_property("port_name", "output")

    def setup_ports(self) -> None:
        """Define ports for the output node."""
        self.add_typed_input("value", DataType.ANY)

    @Slot(str, object)
    def on_property_changed(self, name: str, value: Any) -> None:
        """Update node name when port name changes."""
        if name == "port_name":
            self.set_name(f"Output: {value}")
        super().on_property_changed(name, value)

    @Slot(object, object)
    def on_input_connected(self, in_port, out_port) -> None:
        """
        Notify that an output port should be created in the subflow entity
        matching the source port's name and type.
        """
        # Logic for automatic port creation will be handled in the controller
        # by listening to graph signals, but we can emit a signal here if needed.
        pass
