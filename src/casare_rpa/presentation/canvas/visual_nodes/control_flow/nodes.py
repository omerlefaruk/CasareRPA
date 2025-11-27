"""Visual nodes for control_flow category."""

from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode


class VisualIfNode(VisualNode):
    """Visual representation of IfNode."""

    __identifier__ = "casare_rpa.control_flow"
    NODE_NAME = "If"
    NODE_CATEGORY = "control_flow"

    def __init__(self) -> None:
        """Initialize If node."""
        super().__init__()
        self.add_text_input("expression", "Expression", tab="properties")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("condition")
        self.add_output("true")
        self.add_output("false")


class VisualForLoopNode(VisualNode):
    """
    Composite For Loop - creates both ForLoopStart and ForLoopEnd nodes.

    This is a marker class that appears in the menu. When selected,
    special handling in node_graph_widget creates both Start and End nodes
    and connects them together.
    """

    __identifier__ = "casare_rpa.control_flow"
    NODE_NAME = "For Loop"
    NODE_CATEGORY = "control_flow"
    # Mark as composite - special handling creates multiple nodes
    COMPOSITE_NODE = True
    COMPOSITE_CREATES = ["ForLoopStartNode", "ForLoopEndNode"]

    def __init__(self) -> None:
        """Initialize For Loop composite (not actually used - see node_graph_widget)."""
        super().__init__()

    def setup_ports(self) -> None:
        """Setup ports (not actually used - composite creates real nodes)."""
        pass


class VisualForLoopStartNode(VisualNode):
    """
    Visual representation of ForLoopStartNode.
    Note: This is created automatically by VisualForLoopNode composite.
    Hidden from menu - use "For Loop" instead which creates both Start and End.
    """

    __identifier__ = "casare_rpa.control_flow"
    NODE_NAME = "For Loop Start"
    NODE_CATEGORY = "control_flow"
    # Mark as internal - not shown in menu directly
    INTERNAL_NODE = True

    def __init__(self) -> None:
        """Initialize For Loop Start node."""
        super().__init__()
        self.add_text_input("start", "Start", text="0", tab="properties")
        self.add_text_input("end", "End", text="10", tab="properties")
        self.add_text_input("step", "Step", text="1", tab="properties")
        # Store paired end node ID
        self.paired_end_id: str = ""

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("items", DataType.LIST)
        self.add_typed_input("end", DataType.INTEGER)
        self.add_exec_output("body")
        self.add_exec_output("completed")
        self.add_typed_output("current_item", DataType.ANY)
        self.add_typed_output("current_index", DataType.INTEGER)


class VisualForLoopEndNode(VisualNode):
    """
    Visual representation of ForLoopEndNode.
    Note: This is created automatically by VisualForLoopNode composite.
    Hidden from menu - use "For Loop" instead which creates both Start and End.
    """

    __identifier__ = "casare_rpa.control_flow"
    NODE_NAME = "For Loop End"
    NODE_CATEGORY = "control_flow"
    # Mark as internal - not shown in menu directly
    INTERNAL_NODE = True

    def __init__(self) -> None:
        """Initialize For Loop End node."""
        super().__init__()
        # Store paired start node ID (set automatically when created together)
        self.paired_start_id: str = ""
        # Create custom property for persistence
        self.create_property("paired_start_id", "", widget_type=None)

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_exec_output()
        # Restore paired_start_id from custom property if available
        stored_id = self.get_property("paired_start_id")
        if stored_id:
            self.paired_start_id = stored_id

    def set_paired_start(self, start_node_id: str) -> None:
        """Set the paired ForLoopStart node ID."""
        self.paired_start_id = start_node_id
        # Save to custom property for persistence
        self.set_property("paired_start_id", start_node_id)
        # Also update the underlying CasareRPA node if it exists
        casare_node = self.get_casare_node()
        if casare_node and hasattr(casare_node, "set_paired_start"):
            casare_node.set_paired_start(start_node_id)


class VisualWhileLoopNode(VisualNode):
    """
    Composite While Loop - creates both WhileLoopStart and WhileLoopEnd nodes.

    This is a marker class that appears in the menu. When selected,
    special handling creates both Start and End nodes connected together.
    """

    __identifier__ = "casare_rpa.control_flow"
    NODE_NAME = "While Loop"
    NODE_CATEGORY = "control_flow"
    COMPOSITE_NODE = True
    COMPOSITE_CREATES = ["WhileLoopStartNode", "WhileLoopEndNode"]

    def __init__(self) -> None:
        """Initialize While Loop composite."""
        super().__init__()

    def setup_ports(self) -> None:
        """Setup ports (not used - composite creates real nodes)."""
        pass


class VisualWhileLoopStartNode(VisualNode):
    """
    Visual representation of WhileLoopStartNode.
    Hidden from menu - use "While Loop" instead.
    """

    __identifier__ = "casare_rpa.control_flow"
    NODE_NAME = "While Loop Start"
    NODE_CATEGORY = "control_flow"
    INTERNAL_NODE = True

    def __init__(self) -> None:
        """Initialize While Loop Start node."""
        super().__init__()
        self.add_text_input("expression", "Expression", tab="properties")
        self.add_text_input(
            "max_iterations", "Max Iterations", text="1000", tab="properties"
        )
        self.paired_end_id: str = ""

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("condition", DataType.BOOLEAN)
        self.add_exec_output("body")
        self.add_exec_output("completed")
        self.add_typed_output("current_iteration", DataType.INTEGER)


class VisualWhileLoopEndNode(VisualNode):
    """
    Visual representation of WhileLoopEndNode.
    Hidden from menu - use "While Loop" instead.
    """

    __identifier__ = "casare_rpa.control_flow"
    NODE_NAME = "While Loop End"
    NODE_CATEGORY = "control_flow"
    INTERNAL_NODE = True

    def __init__(self) -> None:
        """Initialize While Loop End node."""
        super().__init__()
        self.paired_start_id: str = ""
        # Create custom property for persistence
        self.create_property("paired_start_id", "", widget_type=None)

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_exec_output()
        # Restore paired_start_id from custom property if available
        stored_id = self.get_property("paired_start_id")
        if stored_id:
            self.paired_start_id = stored_id

    def set_paired_start(self, start_node_id: str) -> None:
        """Set the paired WhileLoopStart node ID."""
        self.paired_start_id = start_node_id
        # Save to custom property for persistence
        self.set_property("paired_start_id", start_node_id)
        casare_node = self.get_casare_node()
        if casare_node and hasattr(casare_node, "set_paired_start"):
            casare_node.set_paired_start(start_node_id)


class VisualBreakNode(VisualNode):
    """Visual representation of BreakNode."""

    __identifier__ = "casare_rpa.control_flow"
    NODE_NAME = "Break"
    NODE_CATEGORY = "control_flow"

    def __init__(self) -> None:
        """Initialize Break node."""
        super().__init__()

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_output("exec_out")


class VisualContinueNode(VisualNode):
    """Visual representation of ContinueNode."""

    __identifier__ = "casare_rpa.control_flow"
    NODE_NAME = "Continue"
    NODE_CATEGORY = "control_flow"

    def __init__(self) -> None:
        """Initialize Continue node."""
        super().__init__()

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_output("exec_out")


class VisualSwitchNode(VisualNode):
    """Visual representation of SwitchNode."""

    __identifier__ = "casare_rpa.control_flow"
    NODE_NAME = "Switch"
    NODE_CATEGORY = "control_flow"

    def __init__(self) -> None:
        """Initialize Switch node."""
        super().__init__()
        self.add_text_input("expression", "Expression", tab="properties")
        self.add_text_input(
            "cases",
            "Cases (comma-separated)",
            text="success,error,pending",
            tab="properties",
        )

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("value")

        # Cases will be created dynamically based on config
        # But we need at least the default output
        self.add_output("default")
