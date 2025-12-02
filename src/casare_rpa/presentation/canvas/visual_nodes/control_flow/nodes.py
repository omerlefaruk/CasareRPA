"""Visual nodes for control_flow category."""

from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode


class VisualIfNode(VisualNode):
    """Visual representation of IfNode."""

    __identifier__ = "casare_rpa.control_flow"
    NODE_NAME = "If"
    NODE_CATEGORY = "control_flow/conditional"

    def __init__(self) -> None:
        """Initialize If node."""
        super().__init__()
        # Note: 'expression' property is auto-created from CasareRPA IfNode schema

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("condition", DataType.BOOLEAN)
        self.add_exec_output("true")
        self.add_exec_output("false")


class VisualForLoopNode(VisualNode):
    """
    Composite For Loop - creates both ForLoopStart and ForLoopEnd nodes.

    This is a marker class that appears in the menu. When selected,
    special handling in node_graph_widget creates both Start and End nodes
    and connects them together.
    """

    __identifier__ = "casare_rpa.control_flow"
    NODE_NAME = "For Loop"
    NODE_CATEGORY = "control_flow/loop"
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

    Supports two modes (configured via properties panel):
        - items: ForEach mode - iterates over collections (lists, dicts, strings)
        - range: Counter mode - iterates over numeric range (start, end, step)

    When iterating over a dict, current_key provides the key for each item.
    """

    __identifier__ = "casare_rpa.control_flow"
    NODE_NAME = "For Loop Start"
    NODE_CATEGORY = "control_flow/loop"
    # Mark as internal - not shown in menu directly
    INTERNAL_NODE = True

    def __init__(self) -> None:
        """Initialize For Loop Start node."""
        super().__init__()
        # Note: 'mode', 'start', 'end', 'step' properties are auto-created from CasareRPA ForLoopStartNode schema
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
        self.add_typed_output("current_key", DataType.ANY)


class VisualForLoopEndNode(VisualNode):
    """
    Visual representation of ForLoopEndNode.
    Note: This is created automatically by VisualForLoopNode composite.
    Hidden from menu - use "For Loop" instead which creates both Start and End.
    """

    __identifier__ = "casare_rpa.control_flow"
    NODE_NAME = "For Loop End"
    NODE_CATEGORY = "control_flow/loop"
    # Mark as internal - not shown in menu directly
    INTERNAL_NODE = True

    def __init__(self) -> None:
        """Initialize For Loop End node."""
        super().__init__()
        # Store paired start node ID (set automatically when created together)
        # This is internal only - not a widget property
        self.paired_start_id: str = ""

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_exec_output()

    def set_paired_start(self, start_node_id: str) -> None:
        """Set the paired ForLoopStart node ID (automatic, not user-configurable)."""
        self.paired_start_id = start_node_id
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
    NODE_CATEGORY = "control_flow/loop"
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
    NODE_CATEGORY = "control_flow/loop"
    INTERNAL_NODE = True

    def __init__(self) -> None:
        """Initialize While Loop Start node."""
        super().__init__()
        # Note: 'expression', 'max_iterations' properties are auto-created from CasareRPA WhileLoopStartNode schema
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
    NODE_CATEGORY = "control_flow/loop"
    INTERNAL_NODE = True

    def __init__(self) -> None:
        """Initialize While Loop End node."""
        super().__init__()
        # Store paired start node ID (set automatically when created together)
        # This is internal only - not a widget property
        self.paired_start_id: str = ""

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_exec_output()

    def set_paired_start(self, start_node_id: str) -> None:
        """Set the paired WhileLoopStart node ID (automatic, not user-configurable)."""
        self.paired_start_id = start_node_id
        # Also update the underlying CasareRPA node if it exists
        casare_node = self.get_casare_node()
        if casare_node and hasattr(casare_node, "set_paired_start"):
            casare_node.set_paired_start(start_node_id)


class VisualBreakNode(VisualNode):
    """Visual representation of BreakNode."""

    __identifier__ = "casare_rpa.control_flow"
    NODE_NAME = "Break"
    NODE_CATEGORY = "control_flow/loop"

    def __init__(self) -> None:
        """Initialize Break node."""
        super().__init__()

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")


class VisualContinueNode(VisualNode):
    """Visual representation of ContinueNode."""

    __identifier__ = "casare_rpa.control_flow"
    NODE_NAME = "Continue"
    NODE_CATEGORY = "control_flow/loop"

    def __init__(self) -> None:
        """Initialize Continue node."""
        super().__init__()

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")


class VisualMergeNode(VisualNode):
    """
    Visual representation of MergeNode.

    Allows multiple execution paths to converge into a single path.
    Connect multiple exec outputs to this node's exec_in, then continue
    from exec_out to the next node.

    Example:
        If ──┬── TRUE ─────────┬──→ Merge ──→ Send Email
             └── FALSE → Zip ──┘
    """

    __identifier__ = "casare_rpa.control_flow"
    NODE_NAME = "Merge"
    NODE_CATEGORY = "control_flow/flow"

    def __init__(self) -> None:
        """Initialize Merge node."""
        super().__init__()

    def setup_ports(self) -> None:
        """Setup ports."""
        # exec_in accepts multiple connections (standard for exec inputs)
        self.add_exec_input()
        self.add_exec_output()


class VisualSwitchNode(VisualNode):
    """Visual representation of SwitchNode."""

    __identifier__ = "casare_rpa.control_flow"
    NODE_NAME = "Switch"
    NODE_CATEGORY = "control_flow/conditional"

    def __init__(self) -> None:
        """Initialize Switch node."""
        super().__init__()
        # Note: 'expression', 'cases' properties are auto-created from CasareRPA SwitchNode schema

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("value", DataType.ANY)

        # Cases will be created dynamically based on config
        # But we need at least the default output
        self.add_exec_output("default")


# =============================================================================
# TRY/CATCH/FINALLY VISUAL NODES
# =============================================================================


class VisualTryCatchFinallyNode(VisualNode):
    """
    Composite Try/Catch/Finally - creates all three nodes together.

    This is a marker class that appears in the menu. When selected,
    special handling creates Try, Catch, and Finally nodes
    placed side-by-side with automatic ID pairing.
    """

    __identifier__ = "casare_rpa.control_flow"
    NODE_NAME = "Try/Catch/Finally"
    NODE_CATEGORY = "control_flow/error_handling"
    # Mark as composite - special handling creates multiple nodes
    COMPOSITE_NODE = True
    COMPOSITE_CREATES = ["TryNode", "CatchNode", "FinallyNode"]

    def __init__(self) -> None:
        """Initialize Try/Catch/Finally composite."""
        super().__init__()

    def setup_ports(self) -> None:
        """Setup ports (not actually used - composite creates real nodes)."""
        pass


class VisualTryNode(VisualNode):
    """
    Visual representation of TryNode.
    Note: This is created automatically by VisualTryCatchFinallyNode composite.
    Hidden from menu - use "Try/Catch/Finally" instead.
    """

    __identifier__ = "casare_rpa.control_flow"
    NODE_NAME = "Try"
    NODE_CATEGORY = "control_flow/error_handling"
    CASARE_NODE_CLASS = "TryNode"
    # Mark as internal - not shown in menu directly
    INTERNAL_NODE = True

    def __init__(self) -> None:
        """Initialize Try node."""
        super().__init__()
        # Paired node IDs - set automatically when created together
        self.paired_catch_id: str = ""
        self.paired_finally_id: str = ""

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_exec_output()  # Main execution flow (top)
        self.add_exec_output("try_body")  # Try body branch (below)


class VisualCatchNode(VisualNode):
    """
    Visual representation of CatchNode.
    Note: This is created automatically by VisualTryCatchFinallyNode composite.
    Hidden from menu - use "Try/Catch/Finally" instead.
    """

    __identifier__ = "casare_rpa.control_flow"
    NODE_NAME = "Catch"
    NODE_CATEGORY = "control_flow/error_handling"
    CASARE_NODE_CLASS = "CatchNode"
    INTERNAL_NODE = True

    def __init__(self) -> None:
        """Initialize Catch node."""
        super().__init__()
        # Paired automatically when created together
        self.paired_try_id: str = ""
        self.paired_finally_id: str = ""

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_exec_output("catch_body")
        self.add_typed_output("error_message", DataType.STRING)
        self.add_typed_output("error_type", DataType.STRING)
        self.add_typed_output("stack_trace", DataType.STRING)

    def set_paired_try(self, try_node_id: str) -> None:
        """Set the paired Try node ID (called automatically)."""
        self.paired_try_id = try_node_id
        casare_node = self.get_casare_node()
        if casare_node and hasattr(casare_node, "set_paired_try"):
            casare_node.set_paired_try(try_node_id)


class VisualFinallyNode(VisualNode):
    """
    Visual representation of FinallyNode.
    Note: This is created automatically by VisualTryCatchFinallyNode composite.
    Hidden from menu - use "Try/Catch/Finally" instead.
    """

    __identifier__ = "casare_rpa.control_flow"
    NODE_NAME = "Finally"
    NODE_CATEGORY = "control_flow/error_handling"
    CASARE_NODE_CLASS = "FinallyNode"
    INTERNAL_NODE = True

    def __init__(self) -> None:
        """Initialize Finally node."""
        super().__init__()
        # Paired automatically when created together
        self.paired_try_id: str = ""

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_exec_output("finally_body")
        self.add_typed_output("had_error", DataType.BOOLEAN)

    def set_paired_try(self, try_node_id: str) -> None:
        """Set the paired Try node ID (called automatically)."""
        self.paired_try_id = try_node_id
        casare_node = self.get_casare_node()
        if casare_node and hasattr(casare_node, "set_paired_try"):
            casare_node.set_paired_try(try_node_id)


# =============================================================================
# PARALLEL EXECUTION VISUAL NODES
# =============================================================================


class VisualForkJoinNode(VisualNode):
    """
    Composite Fork/Join - creates both ForkNode and JoinNode together.

    This is a marker class that appears in the menu. When selected,
    special handling creates Fork and Join nodes placed with space
    between them for adding parallel branch nodes.

    Layout:
        ForkNode ──┬── branch_1 ──→ [space for nodes] ──┬──→ JoinNode
                   ├── branch_2 ──→ [space for nodes] ──┤
                   └── branch_3 ──→ [space for nodes] ──┘
    """

    __identifier__ = "casare_rpa.control_flow"
    NODE_NAME = "Fork/Join"
    NODE_CATEGORY = "control_flow/parallel"
    COMPOSITE_NODE = True
    COMPOSITE_CREATES = ["ForkNode", "JoinNode"]

    def __init__(self) -> None:
        """Initialize Fork/Join composite."""
        super().__init__()

    def setup_ports(self) -> None:
        """Setup ports (not used - composite creates real nodes)."""
        pass


class VisualForkNode(VisualNode):
    """
    Visual representation of ForkNode.

    Splits execution into multiple parallel branches that execute concurrently.
    Use with JoinNode to synchronize branches back together.

    Note: Created automatically by VisualForkJoinNode composite.
    Can also be added independently from menu.
    """

    __identifier__ = "casare_rpa.control_flow"
    NODE_NAME = "Fork"
    NODE_CATEGORY = "control_flow/parallel"
    CASARE_NODE_CLASS = "ForkNode"

    def __init__(self) -> None:
        """Initialize Fork node."""
        super().__init__()
        # Paired JoinNode ID - set automatically when created together
        self.paired_join_id: str = ""

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        # Default to 2 branches - can be changed via properties
        self.add_exec_output("branch_1")
        self.add_exec_output("branch_2")

    def set_paired_join(self, join_node_id: str) -> None:
        """Set the paired JoinNode ID."""
        self.paired_join_id = join_node_id
        casare_node = self.get_casare_node()
        if casare_node and hasattr(casare_node, "set_paired_join"):
            casare_node.set_paired_join(join_node_id)


class VisualJoinNode(VisualNode):
    """
    Visual representation of JoinNode.

    Synchronizes parallel branches from a ForkNode.
    Waits for all branches to complete before continuing execution.

    Note: Created automatically by VisualForkJoinNode composite.
    Can also be added independently from menu.
    """

    __identifier__ = "casare_rpa.control_flow"
    NODE_NAME = "Join"
    NODE_CATEGORY = "control_flow/parallel"
    CASARE_NODE_CLASS = "JoinNode"

    def __init__(self) -> None:
        """Initialize Join node."""
        super().__init__()
        # Paired ForkNode ID - set automatically when created together
        self.paired_fork_id: str = ""

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()  # Multiple connections from branches
        self.add_exec_output()
        self.add_typed_output("results", DataType.DICT)
        self.add_typed_output("branch_count", DataType.INTEGER)

    def set_paired_fork(self, fork_node_id: str) -> None:
        """Set the paired ForkNode ID."""
        self.paired_fork_id = fork_node_id
        casare_node = self.get_casare_node()
        if casare_node and hasattr(casare_node, "set_paired_fork"):
            casare_node.set_paired_fork(fork_node_id)


class VisualParallelForEachNode(VisualNode):
    """
    Visual representation of ParallelForEachNode.

    Processes list items concurrently in batches. Unlike regular ForLoop
    which processes items one-by-one, this node processes multiple items
    at the same time (up to batch_size).

    Example:
        ParallelForEach ──→ ProcessURL ──→ SaveResult
            │
            ├─ items: [url1, url2, url3, ...]
            ├─ batch_size: 5 (process 5 at a time)
            └─ Outputs: current_item, current_index, results
    """

    __identifier__ = "casare_rpa.control_flow"
    NODE_NAME = "Parallel ForEach"
    NODE_CATEGORY = "control_flow/parallel"
    CASARE_NODE_CLASS = "ParallelForEachNode"

    def __init__(self) -> None:
        """Initialize Parallel ForEach node."""
        super().__init__()
        # Note: 'batch_size', 'fail_fast', 'timeout_per_item' properties
        # are auto-created from CasareRPA ParallelForEachNode schema

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("items", DataType.LIST)
        self.add_exec_output("body")
        self.add_exec_output("completed")
        self.add_typed_output("current_item", DataType.ANY)
        self.add_typed_output("current_index", DataType.INTEGER)
        self.add_typed_output("results", DataType.LIST)
