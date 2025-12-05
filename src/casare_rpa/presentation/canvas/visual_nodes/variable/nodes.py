"""Visual nodes for variable category."""

from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode


class VisualSetVariableNode(VisualNode):
    """Visual representation of SetVariableNode."""

    __identifier__ = "casare_rpa.variable"
    NODE_NAME = "Set Variable"
    NODE_CATEGORY = "variable"

    def __init__(self) -> None:
        """Initialize set variable node."""
        super().__init__()
        # Widgets auto-generated from @node_schema on SetVariableNode
        # Add value widget manually (PropertyType.ANY not auto-generated)
        self.add_text_input("default_value", "Value", tab="properties")
        # Don't collapse - users need to see the value input
        # Must be called after widgets are added
        self._collapsed = True  # Reset to allow set_collapsed to work
        self.set_collapsed(False)

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("value", DataType.ANY)
        self.add_typed_input("variable_name", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("value", DataType.ANY)


class VisualGetVariableNode(VisualNode):
    """Visual representation of GetVariableNode."""

    __identifier__ = "casare_rpa.variable"
    NODE_NAME = "Get Variable"
    NODE_CATEGORY = "variable"

    def __init__(self) -> None:
        """Initialize get variable node."""
        super().__init__()
        # Widgets auto-generated from @node_schema on GetVariableNode

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("variable_name", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("value", DataType.ANY)


class VisualIncrementVariableNode(VisualNode):
    """Visual representation of IncrementVariableNode."""

    __identifier__ = "casare_rpa.variable"
    NODE_NAME = "Increment Variable"
    NODE_CATEGORY = "variable"

    def __init__(self) -> None:
        """Initialize increment variable node."""
        super().__init__()
        # Widgets auto-generated from @node_schema on IncrementVariableNode

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("variable_name", DataType.STRING)
        self.add_typed_input("increment", DataType.FLOAT)
        self.add_exec_output("exec_out")
        self.add_typed_output("value", DataType.FLOAT)


# Control Flow Nodes
