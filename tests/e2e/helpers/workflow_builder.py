"""
CasareRPA - E2E Test Workflow Builder.

Fluent builder for constructing test workflows programmatically.
Automatically handles node IDs, connections, and execution.

Usage:
    result = await (
        WorkflowBuilder()
        .add_start()
        .add_set_variable("counter", 0)
        .add_increment_variable("counter")
        .add_end()
        .execute(initial_vars={"my_var": "initial"})
    )

    assert result["success"]
    assert result["variables"]["counter"] == 1
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, TypedDict, Union

from loguru import logger

from casare_rpa.domain.entities.workflow import WorkflowSchema
from casare_rpa.domain.entities.workflow_metadata import WorkflowMetadata
from casare_rpa.domain.entities.node_connection import NodeConnection
from casare_rpa.domain.value_objects.types import SerializedNode


class WorkflowExecutionResult(TypedDict):
    """Result of workflow execution."""

    success: bool
    variables: Dict[str, Any]
    error: Optional[str]
    executed_nodes: int
    duration_ms: float


@dataclass
class NodeRef:
    """Reference to a node in the workflow being built."""

    node_id: str
    node_type: str
    config: Dict[str, Any] = field(default_factory=dict)
    position: Tuple[float, float] = (0.0, 0.0)

    # Output ports that can be connected from
    exec_out_port: str = "exec_out"
    alt_exec_ports: List[str] = field(default_factory=list)  # e.g., ["true", "false"]


class WorkflowBuilder:
    """
    Fluent builder for creating test workflows.

    Automatically:
    - Generates unique node IDs
    - Connects nodes in sequence (exec_out -> exec_in)
    - Handles control flow branching
    - Manages cleanup after execution

    Example:
        builder = WorkflowBuilder()
        result = await (
            builder
            .add_start()
            .add_set_variable("x", 10)
            .add_if("x > 5")
            .branch_true()
                .add_set_variable("result", "big")
            .branch_false()
                .add_set_variable("result", "small")
            .end_if()
            .add_end()
            .execute()
        )
    """

    def __init__(self, name: str = "E2E Test Workflow") -> None:
        """
        Initialize the workflow builder.

        Args:
            name: Name for the workflow
        """
        self._name = name
        self._nodes: Dict[str, NodeRef] = {}
        self._connections: List[Tuple[str, str, str, str]] = []

        # Tracking for sequential building
        self._node_sequence: List[str] = []  # Order of nodes added
        self._last_node_id: Optional[str] = None
        self._pending_connections: List[
            Tuple[str, str]
        ] = []  # (source_node, source_port)

        # Branch tracking for If/Switch nodes
        self._branch_stack: List[Dict[str, Any]] = []

        # Position tracking for visual layout
        self._next_x = 0.0
        self._next_y = 0.0
        self._y_step = 150.0
        self._x_step = 200.0

        # Loop pairing
        self._loop_stack: List[str] = []  # Stack of loop start node IDs

    def _generate_id(self, prefix: str = "node") -> str:
        """Generate a unique node ID."""
        return f"{prefix}_{uuid.uuid4().hex[:8]}"

    def _add_node(
        self,
        node_type: str,
        config: Dict[str, Any],
        node_id: Optional[str] = None,
        exec_out_port: str = "exec_out",
        alt_exec_ports: Optional[List[str]] = None,
        connect_to_previous: bool = True,
    ) -> "WorkflowBuilder":
        """
        Internal method to add a node.

        Args:
            node_type: Type of node (e.g., "SetVariableNode")
            config: Node configuration
            node_id: Optional specific ID (auto-generated if None)
            exec_out_port: Main execution output port name
            alt_exec_ports: Alternative execution ports (for branching)
            connect_to_previous: Whether to connect from previous node

        Returns:
            Self for chaining
        """
        if node_id is None:
            node_id = self._generate_id(node_type.replace("Node", "").lower())

        ref = NodeRef(
            node_id=node_id,
            node_type=node_type,
            config=config,
            position=(self._next_x, self._next_y),
            exec_out_port=exec_out_port,
            alt_exec_ports=alt_exec_ports or [],
        )

        self._nodes[node_id] = ref
        self._node_sequence.append(node_id)

        # Connect from pending connections
        if connect_to_previous and self._pending_connections:
            for source_node, source_port in self._pending_connections:
                self._connections.append((source_node, source_port, node_id, "exec_in"))
            self._pending_connections.clear()

        # Connect from previous node if no pending and we have a last node
        elif connect_to_previous and self._last_node_id is not None:
            prev_ref = self._nodes[self._last_node_id]
            self._connections.append(
                (self._last_node_id, prev_ref.exec_out_port, node_id, "exec_in")
            )

        # Update tracking
        self._last_node_id = node_id
        self._next_y += self._y_step

        return self

    # =========================================================================
    # BASIC NODES
    # =========================================================================

    def add_start(self, node_id: Optional[str] = None) -> "WorkflowBuilder":
        """
        Add a StartNode.

        Args:
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="StartNode",
            config={},
            node_id=node_id,
            connect_to_previous=False,  # Start has no incoming exec
        )

    def add_end(self, node_id: Optional[str] = None) -> "WorkflowBuilder":
        """
        Add an EndNode.

        Args:
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        # EndNode has no exec_out
        result = self._add_node(
            node_type="EndNode",
            config={},
            node_id=node_id,
            exec_out_port="",  # No output
        )
        # Don't set as last_node since nothing can follow
        self._last_node_id = None
        return result

    # =========================================================================
    # VARIABLE NODES
    # =========================================================================

    def add_set_variable(
        self,
        name: str,
        value: Any,
        variable_type: str = "String",
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a SetVariableNode.

        Args:
            name: Variable name
            value: Value to set
            variable_type: Type hint (String, Boolean, Int32, Float, etc.)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="SetVariableNode",
            config={
                "variable_name": name,
                "default_value": value,
                "variable_type": variable_type,
            },
            node_id=node_id,
        )

    def add_get_variable(
        self,
        name: str,
        output_var: Optional[str] = None,
        default: Any = None,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a GetVariableNode.

        Args:
            name: Variable name to retrieve
            output_var: Variable name to store result (optional)
            default: Default value if variable not found
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="GetVariableNode",
            config={
                "variable_name": name,
                "default_value": default,
            },
            node_id=node_id,
        )

    def add_increment_variable(
        self,
        name: str,
        increment: float = 1.0,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add an IncrementVariableNode.

        Args:
            name: Variable name to increment
            increment: Amount to increment by (default: 1.0)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="IncrementVariableNode",
            config={
                "variable_name": name,
                "increment": increment,
            },
            node_id=node_id,
        )

    # =========================================================================
    # CONTROL FLOW - IF/ELSE
    # =========================================================================

    def add_if(
        self,
        expression: str,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add an IfNode.

        Use branch_true() and branch_false() to add nodes to each branch,
        then end_if() to merge branches.

        Args:
            expression: Boolean expression (uses safe_eval)
            node_id: Optional specific node ID

        Example:
            builder.add_if("counter > 5")
                   .branch_true()
                       .add_set_variable("status", "high")
                   .branch_false()
                       .add_set_variable("status", "low")
                   .end_if()

        Returns:
            Self for chaining
        """
        if_node_id = node_id or self._generate_id("if")

        self._add_node(
            node_type="IfNode",
            config={"expression": expression},
            node_id=if_node_id,
            exec_out_port="true",  # Default to true branch
            alt_exec_ports=["true", "false"],
        )

        # Push branch context onto stack
        self._branch_stack.append(
            {
                "type": "if",
                "node_id": if_node_id,
                "branch_ends": [],  # Will collect end nodes of each branch
                "current_branch": None,
            }
        )

        # Clear pending connections - branches need explicit handling
        self._pending_connections.clear()
        self._last_node_id = None

        return self

    def branch_true(self) -> "WorkflowBuilder":
        """
        Start the true branch of an If node.

        Must be called after add_if().

        Returns:
            Self for chaining
        """
        if not self._branch_stack or self._branch_stack[-1]["type"] != "if":
            raise ValueError("branch_true() must be called after add_if()")

        branch_ctx = self._branch_stack[-1]
        if_node_id = branch_ctx["node_id"]

        # Set up connection from If.true to next node
        self._pending_connections = [(if_node_id, "true")]
        branch_ctx["current_branch"] = "true"

        return self

    def branch_false(self) -> "WorkflowBuilder":
        """
        Start the false branch of an If node.

        Must be called after branch_true().

        Returns:
            Self for chaining
        """
        if not self._branch_stack or self._branch_stack[-1]["type"] != "if":
            raise ValueError("branch_false() must be called after add_if()")

        branch_ctx = self._branch_stack[-1]
        if_node_id = branch_ctx["node_id"]

        # Save current branch end (if any nodes were added)
        # Don't add control flow terminators (Break, Continue, Return) to branch_ends
        if self._last_node_id and self._last_node_id != if_node_id:
            last_node = self._nodes.get(self._last_node_id)
            if last_node and last_node.node_type not in (
                "BreakNode",
                "ContinueNode",
                "ReturnNode",
            ):
                branch_ctx["branch_ends"].append(self._last_node_id)

        # Set up connection from If.false to next node
        self._pending_connections = [(if_node_id, "false")]
        branch_ctx["current_branch"] = "false"
        self._last_node_id = None

        return self

    def end_if(self) -> "WorkflowBuilder":
        """
        End an If block and merge branches.

        Adds a MergeNode to rejoin execution paths.

        Returns:
            Self for chaining
        """
        if not self._branch_stack or self._branch_stack[-1]["type"] != "if":
            raise ValueError(
                "end_if() must be called after branch_true()/branch_false()"
            )

        branch_ctx = self._branch_stack.pop()
        if_node_id = branch_ctx["node_id"]

        # Save current branch end (if any nodes were added to current branch)
        if self._last_node_id and self._last_node_id != if_node_id:
            # Only add to branch_ends if it's not a control flow terminator (Break, Continue, Return)
            last_node = self._nodes.get(self._last_node_id)
            if last_node and last_node.node_type not in (
                "BreakNode",
                "ContinueNode",
                "ReturnNode",
            ):
                branch_ctx["branch_ends"].append(self._last_node_id)

        # Create merge node
        merge_id = self._generate_id("merge")
        merge_ref = NodeRef(
            node_id=merge_id,
            node_type="MergeNode",
            config={},
            position=(self._next_x, self._next_y),
        )
        self._nodes[merge_id] = merge_ref
        self._node_sequence.append(merge_id)
        self._next_y += self._y_step

        # Connect all branch ends to merge
        for end_node_id in branch_ctx["branch_ends"]:
            end_ref = self._nodes[end_node_id]
            self._connections.append(
                (end_node_id, end_ref.exec_out_port, merge_id, "exec_in")
            )

        # Handle empty branches by connecting directly from if node to merge
        # This ensures execution continues when no nodes in the branch
        if branch_ctx["current_branch"] == "false" and not self._last_node_id:
            # Empty false branch - connect If.false directly to merge
            self._connections.append((if_node_id, "false", merge_id, "exec_in"))
        elif branch_ctx["current_branch"] == "true" and not branch_ctx["branch_ends"]:
            # Empty true branch (and possibly no false branch at all)
            if not self._pending_connections:
                # If no pending connections, true branch was empty
                self._connections.append((if_node_id, "true", merge_id, "exec_in"))

        # Continue from merge node
        self._last_node_id = merge_id
        self._pending_connections.clear()

        return self

    # =========================================================================
    # CONTROL FLOW - FOR LOOP
    # =========================================================================

    def add_for_loop(
        self,
        item_var: str = "item",
        list_var: Optional[str] = None,
        items: Optional[List[Any]] = None,
        range_end: Optional[int] = None,
        range_start: int = 0,
        range_step: int = 1,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a ForLoopStartNode.

        Use add_for_loop_end() to close the loop.

        Args:
            item_var: Variable name for current item
            list_var: Variable containing the list to iterate
            items: Direct list of items (if not using list_var)
            range_end: End of range (for counter-based iteration)
            range_start: Start of range (default: 0)
            range_step: Step of range (default: 1)
            node_id: Optional specific node ID

        Example - iterate over items:
            builder.add_set_variable("my_list", [1, 2, 3])
                   .add_for_loop(item_var="num", list_var="my_list")
                   .add_increment_variable("sum", "{{num}}")
                   .add_for_loop_end()

        Example - counter loop:
            builder.add_for_loop(item_var="i", range_end=10)
                   .add_increment_variable("total")
                   .add_for_loop_end()

        Returns:
            Self for chaining
        """
        loop_id = node_id or self._generate_id("for_start")

        # Determine mode and build config
        if range_end is not None:
            mode = "range"
            config = {
                "mode": mode,
                "item_var": item_var,
                "start": range_start,
                "end": range_end,
                "step": range_step,
            }
        else:
            mode = "items"
            config = {
                "mode": mode,
                "item_var": item_var,
                "list_var": list_var or "",
            }

        self._add_node(
            node_type="ForLoopStartNode",
            config=config,
            node_id=loop_id,
            exec_out_port="body",  # Loop body
            alt_exec_ports=["body", "completed"],
        )

        # Track loop for pairing with end
        self._loop_stack.append(loop_id)

        # Set up for body nodes
        self._pending_connections = [(loop_id, "body")]
        self._last_node_id = None

        return self

    def add_for_loop_end(self, node_id: Optional[str] = None) -> "WorkflowBuilder":
        """
        Add a ForLoopEndNode to close a For loop.

        Automatically pairs with the most recent add_for_loop().

        Args:
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        if not self._loop_stack:
            raise ValueError(
                "add_for_loop_end() called without matching add_for_loop()"
            )

        loop_start_id = self._loop_stack.pop()
        end_id = node_id or self._generate_id("for_end")

        # Connect last body node to loop end
        self._add_node(
            node_type="ForLoopEndNode",
            config={"paired_start_id": loop_start_id},
            node_id=end_id,
        )

        # The loop end connects back to start (handled by executor)
        # Continue from the loop start's completed port
        loop_ref = self._nodes[loop_start_id]
        self._pending_connections = [(loop_start_id, "completed")]
        self._last_node_id = None

        return self

    # =========================================================================
    # CONTROL FLOW - WHILE LOOP
    # =========================================================================

    def add_while_loop(
        self,
        expression: str,
        max_iterations: int = 1000,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a WhileLoopStartNode.

        Use add_while_loop_end() to close the loop.

        Args:
            expression: Boolean expression to evaluate each iteration
            max_iterations: Safety limit (default: 1000)
            node_id: Optional specific node ID

        Example:
            builder.add_set_variable("counter", 0)
                   .add_while_loop("counter < 5")
                   .add_increment_variable("counter")
                   .add_while_loop_end()

        Returns:
            Self for chaining
        """
        loop_id = node_id or self._generate_id("while_start")

        self._add_node(
            node_type="WhileLoopStartNode",
            config={
                "expression": expression,
                "max_iterations": max_iterations,
            },
            node_id=loop_id,
            exec_out_port="body",
            alt_exec_ports=["body", "completed"],
        )

        # Track loop for pairing
        self._loop_stack.append(loop_id)

        # Set up for body nodes
        self._pending_connections = [(loop_id, "body")]
        self._last_node_id = None

        return self

    def add_while_loop_end(self, node_id: Optional[str] = None) -> "WorkflowBuilder":
        """
        Add a WhileLoopEndNode to close a While loop.

        Args:
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        if not self._loop_stack:
            raise ValueError(
                "add_while_loop_end() called without matching add_while_loop()"
            )

        loop_start_id = self._loop_stack.pop()
        end_id = node_id or self._generate_id("while_end")

        self._add_node(
            node_type="WhileLoopEndNode",
            config={"paired_start_id": loop_start_id},
            node_id=end_id,
        )

        # Continue from the loop start's completed port
        self._pending_connections = [(loop_start_id, "completed")]
        self._last_node_id = None

        return self

    # =========================================================================
    # DATA OPERATION NODES
    # =========================================================================

    def add_math_operation(
        self,
        output_var: str,
        a: Union[float, str],
        b: Union[float, str] = 0,
        operation: str = "add",
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a MathOperationNode.

        Args:
            output_var: Variable to store result
            a: First operand (number or variable reference)
            b: Second operand
            operation: Operation (add, subtract, multiply, divide, etc.)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="MathOperationNode",
            config={
                "a": a,
                "b": b,
                "operation": operation,
                "output_var": output_var,
            },
            node_id=node_id,
        )

    def add_concat(
        self,
        output_var: str,
        string_1: str,
        string_2: str,
        separator: str = "",
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a ConcatenateNode.

        Args:
            output_var: Variable to store result
            string_1: First string (or variable reference)
            string_2: Second string
            separator: Separator between strings
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="ConcatenateNode",
            config={
                "string_1": string_1,
                "string_2": string_2,
                "separator": separator,
            },
            node_id=node_id,
        )

    # =========================================================================
    # COMPARISON AND DATA OPERATIONS
    # =========================================================================

    def add_comparison(
        self,
        a: Any,
        b: Any,
        operator: str = "==",
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a ComparisonNode.

        Args:
            a: First value to compare (number, string, or variable reference)
            b: Second value to compare
            operator: Comparison operator (==, !=, >, <, >=, <=)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="ComparisonNode",
            config={
                "a": a,
                "b": b,
                "operator": operator,
            },
            node_id=node_id,
        )

    def add_list_append(
        self,
        list_var: str,
        item: Any,
        output_var: Optional[str] = None,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a ListAppendNode.

        Args:
            list_var: Variable name containing the list
            item: Item to append (value or variable reference)
            output_var: Variable to store result (defaults to list_var)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="ListAppendNode",
            config={
                "list": f"{{{{{list_var}}}}}",
                "item": item,
            },
            node_id=node_id,
        )

    # =========================================================================
    # SWITCH/CASE CONTROL FLOW
    # =========================================================================

    def add_switch(
        self,
        expression: str,
        cases: List[str],
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a SwitchNode for multi-way branching.

        Use add_case() and end_switch() to define case branches.

        Args:
            expression: Expression to evaluate (or variable reference)
            cases: List of case values to match
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        switch_node_id = node_id or self._generate_id("switch")

        self._add_node(
            node_type="SwitchNode",
            config={
                "expression": expression,
                "cases": cases,
            },
            node_id=switch_node_id,
            exec_out_port="default",
            alt_exec_ports=[f"case_{c}" for c in cases] + ["default"],
        )

        # Push switch context onto branch stack
        self._branch_stack.append(
            {
                "type": "switch",
                "node_id": switch_node_id,
                "cases": cases,
                "branch_ends": [],
                "current_case": None,
            }
        )

        # Clear pending connections for case handling
        self._pending_connections.clear()
        self._last_node_id = None

        return self

    def add_case(self, case_value: str) -> "WorkflowBuilder":
        """
        Start a case branch in a Switch node.

        Args:
            case_value: The case value to match

        Returns:
            Self for chaining
        """
        if not self._branch_stack or self._branch_stack[-1]["type"] != "switch":
            raise ValueError("add_case() must be called after add_switch()")

        branch_ctx = self._branch_stack[-1]
        switch_node_id = branch_ctx["node_id"]

        # Save previous case end if any
        if self._last_node_id and self._last_node_id != switch_node_id:
            branch_ctx["branch_ends"].append(self._last_node_id)

        # Set up connection from Switch.case_X to next node
        self._pending_connections = [(switch_node_id, f"case_{case_value}")]
        branch_ctx["current_case"] = case_value
        self._last_node_id = None

        return self

    def add_default_case(self) -> "WorkflowBuilder":
        """
        Start the default case branch in a Switch node.

        Returns:
            Self for chaining
        """
        if not self._branch_stack or self._branch_stack[-1]["type"] != "switch":
            raise ValueError("add_default_case() must be called after add_switch()")

        branch_ctx = self._branch_stack[-1]
        switch_node_id = branch_ctx["node_id"]

        # Save previous case end if any
        if self._last_node_id and self._last_node_id != switch_node_id:
            branch_ctx["branch_ends"].append(self._last_node_id)

        # Set up connection from Switch.default to next node
        self._pending_connections = [(switch_node_id, "default")]
        branch_ctx["current_case"] = "default"
        self._last_node_id = None

        return self

    def end_switch(self) -> "WorkflowBuilder":
        """
        End a Switch block and merge branches.

        Returns:
            Self for chaining
        """
        if not self._branch_stack or self._branch_stack[-1]["type"] != "switch":
            raise ValueError("end_switch() must be called after add_case()")

        branch_ctx = self._branch_stack.pop()

        # Save current branch end
        if self._last_node_id:
            branch_ctx["branch_ends"].append(self._last_node_id)

        # Create merge node
        merge_id = self._generate_id("merge")
        merge_ref = NodeRef(
            node_id=merge_id,
            node_type="MergeNode",
            config={},
            position=(self._next_x, self._next_y),
        )
        self._nodes[merge_id] = merge_ref
        self._node_sequence.append(merge_id)
        self._next_y += self._y_step

        # Connect all case ends to merge
        for end_node_id in branch_ctx["branch_ends"]:
            end_ref = self._nodes[end_node_id]
            self._connections.append(
                (end_node_id, end_ref.exec_out_port, merge_id, "exec_in")
            )

        # Continue from merge node
        self._last_node_id = merge_id
        self._pending_connections.clear()

        return self

    # =========================================================================
    # ERROR HANDLING NODES
    # =========================================================================

    def add_throw_error(
        self,
        message: str,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a ThrowErrorNode that intentionally throws an error.

        Args:
            message: Error message to throw
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="ThrowErrorNode",
            config={"error_message": message},
            node_id=node_id,
        )

    def add_assert(
        self,
        condition: Union[bool, str],
        message: str = "Assertion failed",
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add an AssertNode that throws if condition is false.

        Args:
            condition: Boolean condition or expression
            message: Error message if assertion fails
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="AssertNode",
            config={
                "condition": condition,
                "message": message,
            },
            node_id=node_id,
        )

    def add_try(self, node_id: Optional[str] = None) -> "WorkflowBuilder":
        """
        Add a TryNode to begin an error handling block.

        Use add_try_body(), add_catch(), and end_try() to complete the structure.

        Args:
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        try_node_id = node_id or self._generate_id("try")

        self._add_node(
            node_type="TryNode",
            config={},
            node_id=try_node_id,
            exec_out_port="try_body",
            alt_exec_ports=["try_body", "success", "catch"],
        )

        # Push try context onto branch stack
        self._branch_stack.append(
            {
                "type": "try",
                "node_id": try_node_id,
                "try_body_end": None,
                "catch_body_end": None,
                "current_block": None,
            }
        )

        # Clear for try body
        self._pending_connections.clear()
        self._last_node_id = None

        return self

    def try_body(self) -> "WorkflowBuilder":
        """
        Start the try body block.

        Returns:
            Self for chaining
        """
        if not self._branch_stack or self._branch_stack[-1]["type"] != "try":
            raise ValueError("try_body() must be called after add_try()")

        branch_ctx = self._branch_stack[-1]
        try_node_id = branch_ctx["node_id"]

        self._pending_connections = [(try_node_id, "try_body")]
        branch_ctx["current_block"] = "try_body"

        return self

    def catch_block(self) -> "WorkflowBuilder":
        """
        Start the catch block.

        Returns:
            Self for chaining
        """
        if not self._branch_stack or self._branch_stack[-1]["type"] != "try":
            raise ValueError("catch_block() must be called after add_try()")

        branch_ctx = self._branch_stack[-1]
        try_node_id = branch_ctx["node_id"]

        # Save try body end
        if self._last_node_id and self._last_node_id != try_node_id:
            branch_ctx["try_body_end"] = self._last_node_id

        self._pending_connections = [(try_node_id, "catch")]
        branch_ctx["current_block"] = "catch"
        self._last_node_id = None

        return self

    def end_try(self) -> "WorkflowBuilder":
        """
        End a Try/Catch block and merge branches.

        Returns:
            Self for chaining
        """
        if not self._branch_stack or self._branch_stack[-1]["type"] != "try":
            raise ValueError("end_try() must be called after try/catch blocks")

        branch_ctx = self._branch_stack.pop()
        try_node_id = branch_ctx["node_id"]

        # Save current block end
        if self._last_node_id and self._last_node_id != try_node_id:
            if branch_ctx["current_block"] == "try_body":
                branch_ctx["try_body_end"] = self._last_node_id
            elif branch_ctx["current_block"] == "catch":
                branch_ctx["catch_body_end"] = self._last_node_id

        # Create merge node
        merge_id = self._generate_id("merge")
        merge_ref = NodeRef(
            node_id=merge_id,
            node_type="MergeNode",
            config={},
            position=(self._next_x, self._next_y),
        )
        self._nodes[merge_id] = merge_ref
        self._node_sequence.append(merge_id)
        self._next_y += self._y_step

        # Connect try success path to merge
        self._connections.append((try_node_id, "success", merge_id, "exec_in"))

        # Connect try body end to merge (if exists)
        if branch_ctx["try_body_end"]:
            end_ref = self._nodes[branch_ctx["try_body_end"]]
            self._connections.append(
                (branch_ctx["try_body_end"], end_ref.exec_out_port, merge_id, "exec_in")
            )

        # Connect catch body end to merge (if exists)
        if branch_ctx["catch_body_end"]:
            end_ref = self._nodes[branch_ctx["catch_body_end"]]
            self._connections.append(
                (
                    branch_ctx["catch_body_end"],
                    end_ref.exec_out_port,
                    merge_id,
                    "exec_in",
                )
            )

        # Continue from merge node
        self._last_node_id = merge_id
        self._pending_connections.clear()

        return self

    def add_retry(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        backoff_multiplier: float = 2.0,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a RetryNode for automatic retry with backoff.

        Args:
            max_attempts: Maximum number of retry attempts
            initial_delay: Initial delay before first retry (seconds)
            backoff_multiplier: Exponential backoff multiplier
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        retry_node_id = node_id or self._generate_id("retry")

        self._add_node(
            node_type="RetryNode",
            config={
                "max_attempts": max_attempts,
                "initial_delay": initial_delay,
                "backoff_multiplier": backoff_multiplier,
            },
            node_id=retry_node_id,
            exec_out_port="retry_body",
            alt_exec_ports=["retry_body", "success", "failed"],
        )

        # Track retry for pairing
        self._branch_stack.append(
            {
                "type": "retry",
                "node_id": retry_node_id,
                "body_end": None,
            }
        )

        # Set up for retry body
        self._pending_connections = [(retry_node_id, "retry_body")]
        self._last_node_id = None

        return self

    def add_retry_success(self, node_id: Optional[str] = None) -> "WorkflowBuilder":
        """
        Add a RetrySuccessNode to signal retry succeeded.

        Args:
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="RetrySuccessNode",
            config={},
            node_id=node_id,
        )

    def add_retry_fail(
        self,
        error_message: str = "Retry failed",
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a RetryFailNode to signal retry attempt failed.

        Args:
            error_message: Error message for the failure
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="RetryFailNode",
            config={"error_message": error_message},
            node_id=node_id,
        )

    # =========================================================================
    # LOOP CONTROL NODES
    # =========================================================================

    def add_break(self, node_id: Optional[str] = None) -> "WorkflowBuilder":
        """
        Add a BreakNode to exit the current loop.

        Args:
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        # Get current loop start ID if we're inside a loop
        paired_loop_start_id = self._loop_stack[-1] if self._loop_stack else ""

        return self._add_node(
            node_type="BreakNode",
            config={"paired_loop_start_id": paired_loop_start_id},
            node_id=node_id,
        )

    def add_continue(self, node_id: Optional[str] = None) -> "WorkflowBuilder":
        """
        Add a ContinueNode to skip to next loop iteration.

        Args:
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        # Get current loop start ID if we're inside a loop
        paired_loop_start_id = self._loop_stack[-1] if self._loop_stack else ""

        return self._add_node(
            node_type="ContinueNode",
            config={"paired_loop_start_id": paired_loop_start_id},
            node_id=node_id,
        )

    def add_log(
        self,
        message: str,
        level: str = "info",
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a LogNode for debugging.

        Args:
            message: Message to log
            level: Log level (debug, info, warning, error)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="LogNode",
            config={
                "message": message,
                "level": level,
            },
            node_id=node_id,
        )

    def add_decrement_variable(
        self,
        name: str,
        decrement: float = 1.0,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add an IncrementVariableNode with negative increment (decrement).

        Args:
            name: Variable name to decrement
            decrement: Amount to decrement by (default: 1.0)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="IncrementVariableNode",
            config={
                "variable_name": name,
                "increment": -decrement,
            },
            node_id=node_id,
        )

    # =========================================================================
    # STRING OPERATION NODES
    # =========================================================================

    def add_text_split(
        self,
        text: str,
        separator: str = "",
        max_split: int = -1,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a TextSplitNode.

        Args:
            text: Text to split (or variable reference)
            separator: Separator to split on
            max_split: Maximum splits (-1 for unlimited)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="TextSplitNode",
            config={
                "text": text,
                "separator": separator,
                "max_split": max_split,
            },
            node_id=node_id,
        )

    def add_text_replace(
        self,
        text: str,
        old_value: str,
        new_value: str,
        count: int = -1,
        use_regex: bool = False,
        ignore_case: bool = False,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a TextReplaceNode.

        Args:
            text: Text to modify (or variable reference)
            old_value: Value to replace
            new_value: Replacement value
            count: Max replacements (-1 for all)
            use_regex: Use regex matching
            ignore_case: Case-insensitive matching
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="TextReplaceNode",
            config={
                "text": text,
                "old_value": old_value,
                "new_value": new_value,
                "count": count,
                "use_regex": use_regex,
                "ignore_case": ignore_case,
            },
            node_id=node_id,
        )

    def add_text_trim(
        self,
        text: str,
        mode: str = "both",
        characters: str = "",
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a TextTrimNode.

        Args:
            text: Text to trim (or variable reference)
            mode: 'both', 'left', 'right'
            characters: Characters to trim (default: whitespace)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="TextTrimNode",
            config={
                "text": text,
                "mode": mode,
                "characters": characters,
            },
            node_id=node_id,
        )

    def add_text_case(
        self,
        text: str,
        case: str = "lower",
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a TextCaseNode.

        Args:
            text: Text to transform (or variable reference)
            case: 'upper', 'lower', 'title', 'capitalize', 'swapcase'
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="TextCaseNode",
            config={
                "text": text,
                "case": case,
            },
            node_id=node_id,
        )

    def add_text_substring(
        self,
        text: str,
        start: int = 0,
        end: Optional[int] = None,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a TextSubstringNode.

        Args:
            text: Source text (or variable reference)
            start: Start index (inclusive)
            end: End index (exclusive, None for end of string)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        config: Dict[str, Any] = {"text": text, "start": start}
        if end is not None:
            config["end"] = end
        return self._add_node(
            node_type="TextSubstringNode",
            config=config,
            node_id=node_id,
        )

    def add_text_contains(
        self,
        text: str,
        search: str,
        case_sensitive: bool = True,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a TextContainsNode.

        Args:
            text: Text to search in (or variable reference)
            search: Substring to find
            case_sensitive: Case-sensitive search
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="TextContainsNode",
            config={
                "text": text,
                "search": search,
                "case_sensitive": case_sensitive,
            },
            node_id=node_id,
        )

    def add_text_join(
        self,
        items: Union[List[Any], str],
        separator: str = "",
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a TextJoinNode.

        Args:
            items: List to join (or variable reference)
            separator: Separator to use
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="TextJoinNode",
            config={
                "items": items,
                "separator": separator,
            },
            node_id=node_id,
        )

    def add_text_count(
        self,
        text: str,
        mode: str = "characters",
        exclude_whitespace: bool = False,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a TextCountNode.

        Args:
            text: Text to count (or variable reference)
            mode: 'characters', 'words', 'lines'
            exclude_whitespace: Exclude whitespace from char count
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="TextCountNode",
            config={
                "text": text,
                "mode": mode,
                "exclude_whitespace": exclude_whitespace,
            },
            node_id=node_id,
        )

    def add_regex_match(
        self,
        text: str,
        pattern: str,
        ignore_case: bool = False,
        multiline: bool = False,
        dotall: bool = False,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a RegexMatchNode.

        Args:
            text: Text to search (or variable reference)
            pattern: Regex pattern
            ignore_case: Case-insensitive matching
            multiline: ^ and $ match line boundaries
            dotall: . matches newlines
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="RegexMatchNode",
            config={
                "text": text,
                "pattern": pattern,
                "ignore_case": ignore_case,
                "multiline": multiline,
                "dotall": dotall,
            },
            node_id=node_id,
        )

    def add_text_extract(
        self,
        text: str,
        pattern: str,
        all_matches: bool = False,
        ignore_case: bool = False,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a TextExtractNode.

        Args:
            text: Text to search (or variable reference)
            pattern: Regex pattern with capture groups
            all_matches: Return all matches
            ignore_case: Case-insensitive matching
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="TextExtractNode",
            config={
                "text": text,
                "pattern": pattern,
                "all_matches": all_matches,
                "ignore_case": ignore_case,
            },
            node_id=node_id,
        )

    def add_format_string(
        self,
        template: str,
        variables: Union[Dict[str, Any], str],
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a FormatStringNode.

        Args:
            template: Template string with {key} placeholders
            variables: Dict of values (or variable reference)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="FormatStringNode",
            config={
                "template": template,
                "variables": variables,
            },
            node_id=node_id,
        )

    # =========================================================================
    # JSON/DICT OPERATION NODES
    # =========================================================================

    def add_json_parse(
        self,
        json_string: str,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a JsonParseNode.

        Args:
            json_string: JSON string to parse (or variable reference)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="JsonParseNode",
            config={"json_string": json_string},
            node_id=node_id,
        )

    def add_dict_to_json(
        self,
        dict_input: Union[Dict[str, Any], str],
        indent: Optional[int] = None,
        sort_keys: bool = False,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a DictToJsonNode.

        Args:
            dict_input: Dictionary to convert (or variable reference)
            indent: Indentation level (None for compact)
            sort_keys: Sort keys alphabetically
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        config: Dict[str, Any] = {"dict": dict_input, "sort_keys": sort_keys}
        if indent is not None:
            config["indent"] = indent
        return self._add_node(
            node_type="DictToJsonNode",
            config=config,
            node_id=node_id,
        )

    def add_dict_get(
        self,
        dict_input: Union[Dict[str, Any], str],
        key: str,
        default: Any = None,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a DictGetNode.

        Args:
            dict_input: Dictionary (or variable reference)
            key: Key to get
            default: Default if key not found
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="DictGetNode",
            config={
                "dict": dict_input,
                "key": key,
                "default": default,
            },
            node_id=node_id,
        )

    def add_dict_set(
        self,
        dict_input: Union[Dict[str, Any], str],
        key: str,
        value: Any,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a DictSetNode.

        Args:
            dict_input: Dictionary (or variable reference)
            key: Key to set
            value: Value to set
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="DictSetNode",
            config={
                "dict": dict_input,
                "key": key,
                "value": value,
            },
            node_id=node_id,
        )

    def add_dict_remove(
        self,
        dict_input: Union[Dict[str, Any], str],
        key: str,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a DictRemoveNode.

        Args:
            dict_input: Dictionary (or variable reference)
            key: Key to remove
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="DictRemoveNode",
            config={
                "dict": dict_input,
                "key": key,
            },
            node_id=node_id,
        )

    def add_dict_keys(
        self,
        dict_input: Union[Dict[str, Any], str],
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a DictKeysNode.

        Args:
            dict_input: Dictionary (or variable reference)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="DictKeysNode",
            config={"dict": dict_input},
            node_id=node_id,
        )

    def add_dict_values(
        self,
        dict_input: Union[Dict[str, Any], str],
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a DictValuesNode.

        Args:
            dict_input: Dictionary (or variable reference)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="DictValuesNode",
            config={"dict": dict_input},
            node_id=node_id,
        )

    def add_dict_has_key(
        self,
        dict_input: Union[Dict[str, Any], str],
        key: str,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a DictHasKeyNode.

        Args:
            dict_input: Dictionary (or variable reference)
            key: Key to check
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="DictHasKeyNode",
            config={
                "dict": dict_input,
                "key": key,
            },
            node_id=node_id,
        )

    def add_dict_merge(
        self,
        dict_1: Union[Dict[str, Any], str],
        dict_2: Union[Dict[str, Any], str],
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a DictMergeNode.

        Args:
            dict_1: First dictionary (or variable reference)
            dict_2: Second dictionary (or variable reference)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="DictMergeNode",
            config={
                "dict_1": dict_1,
                "dict_2": dict_2,
            },
            node_id=node_id,
        )

    def add_create_dict(
        self,
        key_1: Optional[str] = None,
        value_1: Any = None,
        key_2: Optional[str] = None,
        value_2: Any = None,
        key_3: Optional[str] = None,
        value_3: Any = None,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a CreateDictNode.

        Args:
            key_1: First key
            value_1: First value
            key_2: Second key
            value_2: Second value
            key_3: Third key
            value_3: Third value
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        config: Dict[str, Any] = {}
        if key_1 is not None:
            config["key_1"] = key_1
            config["value_1"] = value_1
        if key_2 is not None:
            config["key_2"] = key_2
            config["value_2"] = value_2
        if key_3 is not None:
            config["key_3"] = key_3
            config["value_3"] = value_3
        return self._add_node(
            node_type="CreateDictNode",
            config=config,
            node_id=node_id,
        )

    def add_get_property(
        self,
        obj: Union[Dict[str, Any], str],
        property_path: str,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a GetPropertyNode for nested property access.

        Args:
            obj: Object/dictionary (or variable reference)
            property_path: Dot-separated path (e.g., "user.name")
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="GetPropertyNode",
            config={
                "object": obj,
                "property_path": property_path,
            },
            node_id=node_id,
        )

    # =========================================================================
    # LIST OPERATION NODES
    # =========================================================================

    def add_create_list(
        self,
        item_1: Any = None,
        item_2: Any = None,
        item_3: Any = None,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a CreateListNode.

        Args:
            item_1: First item
            item_2: Second item
            item_3: Third item
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        config: Dict[str, Any] = {}
        if item_1 is not None:
            config["item_1"] = item_1
        if item_2 is not None:
            config["item_2"] = item_2
        if item_3 is not None:
            config["item_3"] = item_3
        return self._add_node(
            node_type="CreateListNode",
            config=config,
            node_id=node_id,
        )

    def add_list_get_item(
        self,
        list_input: Union[List[Any], str],
        index: int,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a ListGetItemNode.

        Args:
            list_input: List (or variable reference)
            index: Index to get (supports negative)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="ListGetItemNode",
            config={
                "list": list_input,
                "index": index,
            },
            node_id=node_id,
        )

    def add_list_length(
        self,
        list_input: Union[List[Any], str],
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a ListLengthNode.

        Args:
            list_input: List (or variable reference)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="ListLengthNode",
            config={"list": list_input},
            node_id=node_id,
        )

    def add_list_contains(
        self,
        list_input: Union[List[Any], str],
        item: Any,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a ListContainsNode.

        Args:
            list_input: List (or variable reference)
            item: Item to check
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="ListContainsNode",
            config={
                "list": list_input,
                "item": item,
            },
            node_id=node_id,
        )

    def add_list_slice(
        self,
        list_input: Union[List[Any], str],
        start: int = 0,
        end: Optional[int] = None,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a ListSliceNode.

        Args:
            list_input: List (or variable reference)
            start: Start index
            end: End index (None for end of list)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        config: Dict[str, Any] = {"list": list_input, "start": start}
        if end is not None:
            config["end"] = end
        return self._add_node(
            node_type="ListSliceNode",
            config=config,
            node_id=node_id,
        )

    def add_list_sort(
        self,
        list_input: Union[List[Any], str],
        reverse: bool = False,
        key_path: str = "",
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a ListSortNode.

        Args:
            list_input: List (or variable reference)
            reverse: Sort descending
            key_path: Dot path for sorting dict items
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="ListSortNode",
            config={
                "list": list_input,
                "reverse": reverse,
                "key_path": key_path,
            },
            node_id=node_id,
        )

    def add_list_reverse(
        self,
        list_input: Union[List[Any], str],
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a ListReverseNode.

        Args:
            list_input: List (or variable reference)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="ListReverseNode",
            config={"list": list_input},
            node_id=node_id,
        )

    def add_list_unique(
        self,
        list_input: Union[List[Any], str],
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a ListUniqueNode.

        Args:
            list_input: List (or variable reference)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="ListUniqueNode",
            config={"list": list_input},
            node_id=node_id,
        )

    def add_list_filter(
        self,
        list_input: Union[List[Any], str],
        condition: str = "is_not_none",
        value: Any = None,
        key_path: str = "",
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a ListFilterNode.

        Args:
            list_input: List (or variable reference)
            condition: Filter condition
            value: Comparison value
            key_path: Dot path for dict items
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="ListFilterNode",
            config={
                "list": list_input,
                "condition": condition,
                "value": value,
                "key_path": key_path,
            },
            node_id=node_id,
        )

    def add_list_map(
        self,
        list_input: Union[List[Any], str],
        transform: str = "to_string",
        key_path: str = "",
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a ListMapNode.

        Args:
            list_input: List (or variable reference)
            transform: Transformation to apply
            key_path: Dot path for dict items
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="ListMapNode",
            config={
                "list": list_input,
                "transform": transform,
                "key_path": key_path,
            },
            node_id=node_id,
        )

    def add_list_reduce(
        self,
        list_input: Union[List[Any], str],
        operation: str = "sum",
        key_path: str = "",
        initial: Any = None,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a ListReduceNode.

        Args:
            list_input: List (or variable reference)
            operation: Reduction operation
            key_path: Dot path for dict items
            initial: Initial value
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        config: Dict[str, Any] = {
            "list": list_input,
            "operation": operation,
            "key_path": key_path,
        }
        if initial is not None:
            config["initial"] = initial
        return self._add_node(
            node_type="ListReduceNode",
            config=config,
            node_id=node_id,
        )

    def add_list_flatten(
        self,
        list_input: Union[List[Any], str],
        depth: int = 1,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a ListFlattenNode.

        Args:
            list_input: List (or variable reference)
            depth: Levels to flatten
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="ListFlattenNode",
            config={
                "list": list_input,
                "depth": depth,
            },
            node_id=node_id,
        )

    def add_list_join(
        self,
        list_input: Union[List[Any], str],
        separator: str = ", ",
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a ListJoinNode.

        Args:
            list_input: List (or variable reference)
            separator: Separator for joining
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="ListJoinNode",
            config={
                "list": list_input,
                "separator": separator,
            },
            node_id=node_id,
        )

    # =========================================================================
    # FILE OPERATION NODES
    # =========================================================================

    def add_read_file(
        self,
        file_path: str,
        encoding: str = "utf-8",
        binary_mode: bool = False,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a ReadFileNode.

        Args:
            file_path: Path to read (or variable reference)
            encoding: Text encoding (default: utf-8)
            binary_mode: Read as binary (default: False)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="ReadFileNode",
            config={
                "file_path": file_path,
                "encoding": encoding,
                "binary_mode": binary_mode,
                "allow_dangerous_paths": True,
            },
            node_id=node_id,
        )

    def add_write_file(
        self,
        file_path: str,
        content: str,
        encoding: str = "utf-8",
        append_mode: bool = False,
        create_dirs: bool = True,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a WriteFileNode.

        Args:
            file_path: Path to write (or variable reference)
            content: Content to write (or variable reference)
            encoding: Text encoding (default: utf-8)
            append_mode: Append to file (default: False)
            create_dirs: Create parent directories (default: True)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="WriteFileNode",
            config={
                "file_path": file_path,
                "content": content,
                "encoding": encoding,
                "append_mode": append_mode,
                "create_dirs": create_dirs,
                "allow_dangerous_paths": True,
            },
            node_id=node_id,
        )

    def add_append_file(
        self,
        file_path: str,
        content: str,
        encoding: str = "utf-8",
        create_if_missing: bool = True,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add an AppendFileNode.

        Args:
            file_path: Path to append (or variable reference)
            content: Content to append (or variable reference)
            encoding: Text encoding (default: utf-8)
            create_if_missing: Create file if missing (default: True)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="AppendFileNode",
            config={
                "file_path": file_path,
                "content": content,
                "encoding": encoding,
                "create_if_missing": create_if_missing,
                "allow_dangerous_paths": True,
            },
            node_id=node_id,
        )

    def add_file_exists(
        self,
        path: str,
        check_type: str = "any",
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a FileExistsNode.

        Args:
            path: Path to check (or variable reference)
            check_type: "file", "directory", or "any" (default: any)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="FileExistsNode",
            config={
                "path": path,
                "check_type": check_type,
                "allow_dangerous_paths": True,
            },
            node_id=node_id,
        )

    def add_delete_file(
        self,
        file_path: str,
        ignore_missing: bool = False,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a DeleteFileNode.

        Args:
            file_path: Path to delete (or variable reference)
            ignore_missing: Don't error if file missing (default: False)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="DeleteFileNode",
            config={
                "file_path": file_path,
                "ignore_missing": ignore_missing,
                "allow_dangerous_paths": True,
            },
            node_id=node_id,
        )

    def add_copy_file(
        self,
        source_path: str,
        dest_path: str,
        overwrite: bool = False,
        create_dirs: bool = True,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a CopyFileNode.

        Args:
            source_path: Source file path (or variable reference)
            dest_path: Destination file path (or variable reference)
            overwrite: Overwrite if exists (default: False)
            create_dirs: Create destination directories (default: True)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="CopyFileNode",
            config={
                "source_path": source_path,
                "dest_path": dest_path,
                "overwrite": overwrite,
                "create_dirs": create_dirs,
                "allow_dangerous_paths": True,
            },
            node_id=node_id,
        )

    def add_move_file(
        self,
        source_path: str,
        dest_path: str,
        overwrite: bool = False,
        create_dirs: bool = True,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a MoveFileNode.

        Args:
            source_path: Source file path (or variable reference)
            dest_path: Destination file path (or variable reference)
            overwrite: Overwrite if exists (default: False)
            create_dirs: Create destination directories (default: True)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="MoveFileNode",
            config={
                "source_path": source_path,
                "dest_path": dest_path,
                "overwrite": overwrite,
                "create_dirs": create_dirs,
                "allow_dangerous_paths": True,
            },
            node_id=node_id,
        )

    def add_create_directory(
        self,
        directory_path: str,
        parents: bool = True,
        exist_ok: bool = True,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a CreateDirectoryNode.

        Args:
            directory_path: Directory path to create (or variable reference)
            parents: Create parent directories (default: True)
            exist_ok: Don't error if exists (default: True)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="CreateDirectoryNode",
            config={
                "directory_path": directory_path,
                "parents": parents,
                "exist_ok": exist_ok,
                "allow_dangerous_paths": True,
            },
            node_id=node_id,
        )

    def add_list_directory(
        self,
        dir_path: str,
        pattern: str = "*",
        recursive: bool = False,
        files_only: bool = False,
        dirs_only: bool = False,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a ListDirectoryNode.

        Args:
            dir_path: Directory to list (or variable reference)
            pattern: Glob pattern to filter (default: *)
            recursive: Search recursively (default: False)
            files_only: Only return files (default: False)
            dirs_only: Only return directories (default: False)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="ListDirectoryNode",
            config={
                "dir_path": dir_path,
                "pattern": pattern,
                "recursive": recursive,
                "files_only": files_only,
                "dirs_only": dirs_only,
                "allow_dangerous_paths": True,
            },
            node_id=node_id,
        )

    def add_list_files(
        self,
        directory_path: str,
        pattern: str = "*",
        recursive: bool = False,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a ListFilesNode.

        Args:
            directory_path: Directory to list (or variable reference)
            pattern: Glob pattern to filter (default: *)
            recursive: Search recursively (default: False)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="ListFilesNode",
            config={
                "directory_path": directory_path,
                "pattern": pattern,
                "recursive": recursive,
                "allow_dangerous_paths": True,
            },
            node_id=node_id,
        )

    def add_get_file_info(
        self,
        file_path: str,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a GetFileInfoNode.

        Args:
            file_path: File path (or variable reference)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="GetFileInfoNode",
            config={
                "file_path": file_path,
                "allow_dangerous_paths": True,
            },
            node_id=node_id,
        )

    def add_get_file_size(
        self,
        file_path: str,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a GetFileSizeNode.

        Args:
            file_path: File path (or variable reference)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="GetFileSizeNode",
            config={
                "file_path": file_path,
                "allow_dangerous_paths": True,
            },
            node_id=node_id,
        )

    # =========================================================================
    # CSV FILE NODES
    # =========================================================================

    def add_read_csv(
        self,
        file_path: str,
        delimiter: str = ",",
        has_header: bool = True,
        encoding: str = "utf-8",
        skip_rows: int = 0,
        max_rows: int = 0,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a ReadCSVNode.

        Args:
            file_path: Path to CSV file (or variable reference)
            delimiter: Field delimiter (default: ,)
            has_header: First row is header (default: True)
            encoding: Text encoding (default: utf-8)
            skip_rows: Skip N rows after header (default: 0)
            max_rows: Maximum rows to read (0=unlimited)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="ReadCSVNode",
            config={
                "file_path": file_path,
                "delimiter": delimiter,
                "has_header": has_header,
                "encoding": encoding,
                "skip_rows": skip_rows,
                "max_rows": max_rows,
            },
            node_id=node_id,
        )

    def add_write_csv(
        self,
        file_path: str,
        data: Union[List[Any], str],
        headers: Optional[Union[List[str], str]] = None,
        delimiter: str = ",",
        write_header: bool = True,
        encoding: str = "utf-8",
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a WriteCSVNode.

        Args:
            file_path: Path to write CSV (or variable reference)
            data: Data to write - list of dicts or lists (or variable reference)
            headers: Column headers (optional, auto-extracted from dict keys)
            delimiter: Field delimiter (default: ,)
            write_header: Write header row (default: True)
            encoding: Text encoding (default: utf-8)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        config: Dict[str, Any] = {
            "file_path": file_path,
            "data": data,
            "delimiter": delimiter,
            "write_header": write_header,
            "encoding": encoding,
        }
        if headers is not None:
            config["headers"] = headers

        return self._add_node(
            node_type="WriteCSVNode",
            config=config,
            node_id=node_id,
        )

    # =========================================================================
    # JSON FILE NODES
    # =========================================================================

    def add_read_json_file(
        self,
        file_path: str,
        encoding: str = "utf-8",
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a ReadJSONFileNode.

        Args:
            file_path: Path to JSON file (or variable reference)
            encoding: Text encoding (default: utf-8)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="ReadJSONFileNode",
            config={
                "file_path": file_path,
                "encoding": encoding,
            },
            node_id=node_id,
        )

    def add_write_json_file(
        self,
        file_path: str,
        data: Union[Dict[str, Any], List[Any], str],
        indent: int = 2,
        encoding: str = "utf-8",
        ensure_ascii: bool = False,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a WriteJSONFileNode.

        Args:
            file_path: Path to write JSON (or variable reference)
            data: Data to serialize as JSON (or variable reference)
            indent: Indentation level (default: 2)
            encoding: Text encoding (default: utf-8)
            ensure_ascii: Ensure ASCII output (default: False)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="WriteJSONFileNode",
            config={
                "file_path": file_path,
                "data": data,
                "indent": indent,
                "encoding": encoding,
                "ensure_ascii": ensure_ascii,
            },
            node_id=node_id,
        )

    # =========================================================================
    # ZIP FILE NODES
    # =========================================================================

    def add_zip_files(
        self,
        zip_path: str,
        source_path: Optional[str] = None,
        files: Optional[Union[List[str], str]] = None,
        compression: str = "ZIP_DEFLATED",
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a ZipFilesNode.

        Args:
            zip_path: Path to create ZIP file (or variable reference)
            source_path: Source folder or glob pattern (or variable reference)
            files: List of file paths (or variable reference)
            compression: ZIP_STORED or ZIP_DEFLATED (default: ZIP_DEFLATED)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        config: Dict[str, Any] = {
            "zip_path": zip_path,
            "compression": compression,
        }
        if source_path:
            config["source_path"] = source_path
        if files:
            config["files"] = files

        return self._add_node(
            node_type="ZipFilesNode",
            config=config,
            node_id=node_id,
        )

    def add_unzip_files(
        self,
        zip_path: str,
        extract_to: str,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add an UnzipFilesNode.

        Args:
            zip_path: Path to ZIP file (or variable reference)
            extract_to: Directory to extract to (or variable reference)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="UnzipFilesNode",
            config={
                "zip_path": zip_path,
                "extract_to": extract_to,
                "allow_dangerous_paths": True,
            },
            node_id=node_id,
        )

    # =========================================================================
    # HTTP REQUEST NODES
    # =========================================================================

    def add_http_request(
        self,
        method: str = "GET",
        url: str = "",
        headers: Optional[Dict[str, str]] = None,
        body: Optional[str] = None,
        params: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
        verify_ssl: bool = True,
        follow_redirects: bool = True,
        max_redirects: int = 10,
        content_type: str = "application/json",
        retry_count: int = 0,
        retry_delay: float = 1.0,
        headers_from_var: Optional[str] = None,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add an HttpRequestNode.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS)
            url: Target URL
            headers: Request headers as dict
            body: Request body (for POST, PUT, PATCH)
            params: Query parameters as dict
            timeout: Request timeout in seconds
            verify_ssl: Verify SSL certificates
            follow_redirects: Follow HTTP redirects
            max_redirects: Maximum redirects to follow
            content_type: Content-Type header
            retry_count: Number of retries on failure
            retry_delay: Delay between retries in seconds
            headers_from_var: Variable containing headers dict (optional)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        config: Dict[str, Any] = {
            "method": method.upper(),
            "url": url,
            "timeout": timeout,
            "verify_ssl": verify_ssl,
            "follow_redirects": follow_redirects,
            "max_redirects": max_redirects,
            "content_type": content_type,
            "retry_count": retry_count,
            "retry_delay": retry_delay,
        }
        if headers:
            config["headers"] = headers
        if body:
            config["body"] = body
        if params:
            config["params"] = params

        return self._add_node(
            node_type="HttpRequestNode",
            config=config,
            node_id=node_id,
        )

    def add_http_get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add an HttpRequestNode configured for GET.

        Args:
            url: Target URL
            headers: Request headers as dict
            params: Query parameters as dict
            timeout: Request timeout in seconds
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self.add_http_request(
            method="GET",
            url=url,
            headers=headers,
            params=params,
            timeout=timeout,
            node_id=node_id,
        )

    def add_http_post(
        self,
        url: str,
        body: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        content_type: str = "application/json",
        timeout: float = 30.0,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add an HttpRequestNode configured for POST.

        Args:
            url: Target URL
            body: Request body
            headers: Request headers as dict
            content_type: Content-Type header
            timeout: Request timeout in seconds
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self.add_http_request(
            method="POST",
            url=url,
            body=body,
            headers=headers,
            content_type=content_type,
            timeout=timeout,
            node_id=node_id,
        )

    def add_http_put(
        self,
        url: str,
        body: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        content_type: str = "application/json",
        timeout: float = 30.0,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add an HttpRequestNode configured for PUT.

        Args:
            url: Target URL
            body: Request body
            headers: Request headers as dict
            content_type: Content-Type header
            timeout: Request timeout in seconds
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self.add_http_request(
            method="PUT",
            url=url,
            body=body,
            headers=headers,
            content_type=content_type,
            timeout=timeout,
            node_id=node_id,
        )

    def add_http_delete(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add an HttpRequestNode configured for DELETE.

        Args:
            url: Target URL
            headers: Request headers as dict
            timeout: Request timeout in seconds
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self.add_http_request(
            method="DELETE",
            url=url,
            headers=headers,
            timeout=timeout,
            node_id=node_id,
        )

    def add_http_patch(
        self,
        url: str,
        body: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        content_type: str = "application/json",
        timeout: float = 30.0,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add an HttpRequestNode configured for PATCH.

        Args:
            url: Target URL
            body: Request body
            headers: Request headers as dict
            content_type: Content-Type header
            timeout: Request timeout in seconds
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self.add_http_request(
            method="PATCH",
            url=url,
            body=body,
            headers=headers,
            content_type=content_type,
            timeout=timeout,
            node_id=node_id,
        )

    def add_http_auth(
        self,
        auth_type: str = "Bearer",
        token: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        api_key_name: str = "X-API-Key",
        output_var: str = "auth_headers",
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add an HttpAuthNode to configure authentication headers.

        Args:
            auth_type: Authentication type (Bearer, Basic, ApiKey)
            token: Bearer token or API key
            username: Username for Basic auth
            password: Password for Basic auth
            api_key_name: Header name for API key
            output_var: Variable to store auth headers
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        config: Dict[str, Any] = {
            "auth_type": auth_type,
            "api_key_name": api_key_name,
        }
        if token:
            config["token"] = token
        if username:
            config["username"] = username
        if password:
            config["password"] = password

        return self._add_node(
            node_type="HttpAuthNode",
            config=config,
            node_id=node_id,
        )

    def add_set_http_headers(
        self,
        header_name: Optional[str] = None,
        header_value: Optional[str] = None,
        headers_json: Optional[Dict[str, str]] = None,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a SetHttpHeadersNode.

        Args:
            header_name: Single header name
            header_value: Single header value
            headers_json: Multiple headers as dict
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        config: Dict[str, Any] = {}
        if header_name:
            config["header_name"] = header_name
        if header_value:
            config["header_value"] = header_value
        if headers_json:
            config["headers_json"] = headers_json

        return self._add_node(
            node_type="SetHttpHeadersNode",
            config=config,
            node_id=node_id,
        )

    def add_parse_json_response(
        self,
        json_data: str,
        path: str = "",
        default: Optional[Any] = None,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a ParseJsonResponseNode.

        Args:
            json_data: JSON string or variable reference
            path: JSONPath-like path (e.g., "data.users[0].name")
            default: Default value if path not found
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        config: Dict[str, Any] = {
            "path": path,
        }
        if default is not None:
            config["default"] = default

        # The json_data comes in via input port, so we need to set it differently
        result = self._add_node(
            node_type="ParseJsonResponseNode",
            config=config,
            node_id=node_id,
        )
        return result

    def add_build_url(
        self,
        base_url: str,
        path: str = "",
        params: Optional[Dict[str, str]] = None,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a BuildUrlNode.

        Args:
            base_url: Base URL
            path: Path to append
            params: Query parameters as dict
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        config: Dict[str, Any] = {
            "base_url": base_url,
            "path": path,
        }
        if params:
            config["params"] = params

        return self._add_node(
            node_type="BuildUrlNode",
            config=config,
            node_id=node_id,
        )

    def add_http_download_file(
        self,
        url: str,
        save_path: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 300.0,
        overwrite: bool = True,
        retry_count: int = 0,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add an HttpDownloadFileNode.

        Args:
            url: URL to download from
            save_path: Path to save file
            headers: Request headers as dict
            timeout: Download timeout in seconds
            overwrite: Overwrite existing file
            retry_count: Number of retries
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        config: Dict[str, Any] = {
            "url": url,
            "save_path": save_path,
            "timeout": timeout,
            "overwrite": overwrite,
            "retry_count": retry_count,
        }
        if headers:
            config["headers"] = headers

        return self._add_node(
            node_type="HttpDownloadFileNode",
            config=config,
            node_id=node_id,
        )

    def add_http_upload_file(
        self,
        url: str,
        file_path: str,
        field_name: str = "file",
        headers: Optional[Dict[str, str]] = None,
        extra_fields: Optional[Dict[str, Any]] = None,
        timeout: float = 300.0,
        retry_count: int = 0,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add an HttpUploadFileNode.

        Args:
            url: Upload URL
            file_path: Path to file to upload
            field_name: Form field name for file
            headers: Additional headers
            extra_fields: Extra form fields
            timeout: Upload timeout in seconds
            retry_count: Number of retries
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        config: Dict[str, Any] = {
            "url": url,
            "file_path": file_path,
            "field_name": field_name,
            "timeout": timeout,
            "retry_count": retry_count,
        }
        if headers:
            config["headers"] = headers
        if extra_fields:
            config["extra_fields"] = extra_fields

        return self._add_node(
            node_type="HttpUploadFileNode",
            config=config,
            node_id=node_id,
        )

    # =========================================================================
    # BROWSER AUTOMATION NODES
    # =========================================================================

    def add_launch_browser(
        self,
        url: str = "",
        headless: bool = True,
        browser_type: str = "chromium",
        viewport_width: int = 1280,
        viewport_height: int = 720,
        timeout: int = 30000,
        do_not_close: bool = False,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a LaunchBrowserNode.

        Args:
            url: Initial URL to navigate to
            headless: Run in headless mode
            browser_type: Browser type (chromium, firefox, webkit)
            viewport_width: Browser viewport width
            viewport_height: Browser viewport height
            timeout: Launch timeout in milliseconds
            do_not_close: Keep browser open after execution
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="LaunchBrowserNode",
            config={
                "url": url,
                "headless": headless,
                "browser_type": browser_type,
                "viewport_width": viewport_width,
                "viewport_height": viewport_height,
                "do_not_close": do_not_close,
            },
            node_id=node_id,
        )

    def add_close_browser(
        self,
        force_close: bool = False,
        timeout: int = 30000,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a CloseBrowserNode.

        Args:
            force_close: Force close even with unsaved changes
            timeout: Close timeout in milliseconds
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="CloseBrowserNode",
            config={
                "force_close": force_close,
                "timeout": timeout,
            },
            node_id=node_id,
        )

    def add_navigate(
        self,
        url: str,
        timeout: int = 30000,
        wait_until: str = "load",
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a GoToURLNode.

        Args:
            url: URL to navigate to
            timeout: Page load timeout in milliseconds
            wait_until: Navigation event (load, domcontentloaded, networkidle, commit)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="GoToURLNode",
            config={
                "url": url,
                "timeout": timeout,
                "wait_until": wait_until,
            },
            node_id=node_id,
        )

    def add_go_back(
        self,
        timeout: int = 30000,
        wait_until: str = "load",
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a GoBackNode.

        Args:
            timeout: Page load timeout in milliseconds
            wait_until: Navigation event to wait for
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="GoBackNode",
            config={
                "timeout": timeout,
                "wait_until": wait_until,
            },
            node_id=node_id,
        )

    def add_go_forward(
        self,
        timeout: int = 30000,
        wait_until: str = "load",
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a GoForwardNode.

        Args:
            timeout: Page load timeout in milliseconds
            wait_until: Navigation event to wait for
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="GoForwardNode",
            config={
                "timeout": timeout,
                "wait_until": wait_until,
            },
            node_id=node_id,
        )

    def add_refresh(
        self,
        timeout: int = 30000,
        wait_until: str = "load",
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a RefreshPageNode.

        Args:
            timeout: Page load timeout in milliseconds
            wait_until: Navigation event to wait for
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="RefreshPageNode",
            config={
                "timeout": timeout,
                "wait_until": wait_until,
            },
            node_id=node_id,
        )

    def add_click(
        self,
        selector: str,
        timeout: int = 30000,
        button: str = "left",
        click_count: int = 1,
        delay: int = 0,
        force: bool = False,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a ClickElementNode.

        Args:
            selector: CSS or XPath selector for the element
            timeout: Timeout in milliseconds
            button: Mouse button (left, right, middle)
            click_count: Number of clicks (2 for double-click)
            delay: Delay between mousedown and mouseup
            force: Bypass actionability checks
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="ClickElementNode",
            config={
                "selector": selector,
                "timeout": timeout,
                "button": button,
                "click_count": click_count,
                "delay": delay,
                "force": force,
            },
            node_id=node_id,
        )

    def add_double_click(
        self,
        selector: str,
        timeout: int = 30000,
        button: str = "left",
        force: bool = False,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a ClickElementNode configured for double-click.

        Args:
            selector: CSS or XPath selector for the element
            timeout: Timeout in milliseconds
            button: Mouse button
            force: Bypass actionability checks
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="ClickElementNode",
            config={
                "selector": selector,
                "timeout": timeout,
                "button": button,
                "click_count": 2,
                "force": force,
            },
            node_id=node_id,
        )

    def add_right_click(
        self,
        selector: str,
        timeout: int = 30000,
        force: bool = False,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a ClickElementNode configured for right-click.

        Args:
            selector: CSS or XPath selector for the element
            timeout: Timeout in milliseconds
            force: Bypass actionability checks
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="ClickElementNode",
            config={
                "selector": selector,
                "timeout": timeout,
                "button": "right",
                "click_count": 1,
                "force": force,
            },
            node_id=node_id,
        )

    def add_type_text(
        self,
        selector: str,
        text: str,
        timeout: int = 30000,
        clear_first: bool = True,
        delay: int = 0,
        press_enter_after: bool = False,
        press_tab_after: bool = False,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a TypeTextNode.

        Args:
            selector: CSS or XPath selector for the input element
            text: Text to type
            timeout: Timeout in milliseconds
            clear_first: Clear field before typing
            delay: Delay between keystrokes in milliseconds
            press_enter_after: Press Enter after typing
            press_tab_after: Press Tab after typing
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="TypeTextNode",
            config={
                "selector": selector,
                "text": text,
                "timeout": timeout,
                "clear_first": clear_first,
                "delay": delay,
                "press_enter_after": press_enter_after,
                "press_tab_after": press_tab_after,
            },
            node_id=node_id,
        )

    def add_clear_text(
        self,
        selector: str,
        timeout: int = 30000,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a TypeTextNode configured to clear text.

        Args:
            selector: CSS or XPath selector for the input element
            timeout: Timeout in milliseconds
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="TypeTextNode",
            config={
                "selector": selector,
                "text": "",
                "timeout": timeout,
                "clear_first": True,
            },
            node_id=node_id,
        )

    def add_select_dropdown(
        self,
        selector: str,
        value: str,
        select_by: str = "value",
        timeout: int = 30000,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a SelectDropdownNode.

        Args:
            selector: CSS or XPath selector for the select element
            value: Value, label, or index to select
            select_by: Selection method (value, label, index)
            timeout: Timeout in milliseconds
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="SelectDropdownNode",
            config={
                "selector": selector,
                "value": value,
                "select_by": select_by,
                "timeout": timeout,
            },
            node_id=node_id,
        )

    def add_check_checkbox(
        self,
        selector: str,
        timeout: int = 30000,
        force: bool = False,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a ClickElementNode to check a checkbox.

        Uses click to toggle checkbox state.

        Args:
            selector: CSS or XPath selector for the checkbox
            timeout: Timeout in milliseconds
            force: Bypass actionability checks
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="ClickElementNode",
            config={
                "selector": selector,
                "timeout": timeout,
                "force": force,
            },
            node_id=node_id,
        )

    def add_uncheck_checkbox(
        self,
        selector: str,
        timeout: int = 30000,
        force: bool = False,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a ClickElementNode to uncheck a checkbox.

        Uses click to toggle checkbox state.

        Args:
            selector: CSS or XPath selector for the checkbox
            timeout: Timeout in milliseconds
            force: Bypass actionability checks
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="ClickElementNode",
            config={
                "selector": selector,
                "timeout": timeout,
                "force": force,
            },
            node_id=node_id,
        )

    def add_extract_text(
        self,
        selector: str,
        variable_name: str = "extracted_text",
        timeout: int = 30000,
        use_inner_text: bool = False,
        trim_whitespace: bool = True,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add an ExtractTextNode.

        Args:
            selector: CSS or XPath selector for the element
            variable_name: Variable name to store result
            timeout: Timeout in milliseconds
            use_inner_text: Use innerText instead of textContent
            trim_whitespace: Trim leading/trailing whitespace
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="ExtractTextNode",
            config={
                "selector": selector,
                "variable_name": variable_name,
                "timeout": timeout,
                "use_inner_text": use_inner_text,
                "trim_whitespace": trim_whitespace,
            },
            node_id=node_id,
        )

    def add_get_attribute(
        self,
        selector: str,
        attribute: str,
        variable_name: str = "attribute_value",
        timeout: int = 30000,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a GetAttributeNode.

        Args:
            selector: CSS or XPath selector for the element
            attribute: Attribute name to retrieve
            variable_name: Variable name to store result
            timeout: Timeout in milliseconds
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="GetAttributeNode",
            config={
                "selector": selector,
                "attribute": attribute,
                "variable_name": variable_name,
                "timeout": timeout,
            },
            node_id=node_id,
        )

    def add_wait_for_element(
        self,
        selector: str,
        timeout: int = 30000,
        state: str = "visible",
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a WaitForElementNode.

        Args:
            selector: CSS or XPath selector for the element
            timeout: Timeout in milliseconds
            state: Element state (visible, hidden, attached, detached)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="WaitForElementNode",
            config={
                "selector": selector,
                "timeout": timeout,
                "state": state,
            },
            node_id=node_id,
        )

    def add_wait_for_navigation(
        self,
        timeout: int = 30000,
        wait_until: str = "load",
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a WaitForNavigationNode.

        Args:
            timeout: Timeout in milliseconds
            wait_until: Navigation event (load, domcontentloaded, networkidle, commit)
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="WaitForNavigationNode",
            config={
                "timeout": timeout,
                "wait_until": wait_until,
            },
            node_id=node_id,
        )

    def add_wait(
        self,
        duration: float = 1.0,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a WaitNode for static delay.

        Args:
            duration: Wait duration in seconds
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="WaitNode",
            config={
                "duration": duration,
            },
            node_id=node_id,
        )

    def add_screenshot(
        self,
        file_path: str,
        selector: str = "",
        full_page: bool = False,
        image_type: str = "png",
        quality: Optional[int] = None,
        timeout: int = 30000,
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a ScreenshotNode.

        Args:
            file_path: Path to save screenshot
            selector: Optional selector for element screenshot
            full_page: Capture full scrollable page
            image_type: Image format (png or jpeg)
            quality: JPEG quality 0-100 (ignored for PNG)
            timeout: Timeout in milliseconds
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        config: Dict[str, Any] = {
            "file_path": file_path,
            "full_page": full_page,
            "type": image_type,
            "timeout": timeout,
        }
        if selector:
            config["selector"] = selector
        if quality is not None:
            config["quality"] = quality

        return self._add_node(
            node_type="ScreenshotNode",
            config=config,
            node_id=node_id,
        )

    def add_new_tab(
        self,
        tab_name: str = "new_tab",
        url: str = "",
        timeout: int = 30000,
        wait_until: str = "load",
        node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """
        Add a NewTabNode.

        Args:
            tab_name: Name to identify this tab
            url: Optional URL to navigate to
            timeout: Navigation timeout in milliseconds
            wait_until: Navigation event to wait for
            node_id: Optional specific node ID

        Returns:
            Self for chaining
        """
        return self._add_node(
            node_type="NewTabNode",
            config={
                "tab_name": tab_name,
                "url": url,
                "timeout": timeout,
                "wait_until": wait_until,
            },
            node_id=node_id,
        )

    # =========================================================================
    # MANUAL CONNECTION
    # =========================================================================

    def connect(
        self,
        from_node: str,
        from_port: str,
        to_node: str,
        to_port: str,
    ) -> "WorkflowBuilder":
        """
        Manually add a connection between nodes.

        Args:
            from_node: Source node ID
            from_port: Source port name
            to_node: Target node ID
            to_port: Target port name

        Returns:
            Self for chaining
        """
        self._connections.append((from_node, from_port, to_node, to_port))
        return self

    # =========================================================================
    # BUILD & EXECUTE
    # =========================================================================

    def build(self) -> WorkflowSchema:
        """
        Build the WorkflowSchema from the accumulated nodes and connections.

        Returns:
            WorkflowSchema ready for execution
        """
        metadata = WorkflowMetadata(
            name=self._name,
            description="E2E Test Workflow",
            version="1.0.0",
        )

        workflow = WorkflowSchema(metadata)

        # Add all nodes
        for node_id, ref in self._nodes.items():
            node_data: SerializedNode = {
                "node_id": node_id,
                "node_type": ref.node_type,
                "type": ref.node_type,  # Alias
                "config": ref.config,
                "name": ref.node_type.replace("Node", ""),
                "position": {"x": ref.position[0], "y": ref.position[1]},
            }
            workflow.add_node(node_data)

        # Add connections
        for source_node, source_port, target_node, target_port in self._connections:
            # Skip connections to/from empty ports
            if not source_port or not target_port:
                continue

            # Verify nodes exist
            if source_node not in self._nodes:
                logger.warning(f"Connection source node not found: {source_node}")
                continue
            if target_node not in self._nodes:
                logger.warning(f"Connection target node not found: {target_node}")
                continue

            connection = NodeConnection(
                source_node=source_node,
                source_port=source_port,
                target_node=target_node,
                target_port=target_port,
            )
            workflow.connections.append(connection)

        return workflow

    async def execute(
        self,
        initial_vars: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0,
    ) -> WorkflowExecutionResult:
        """
        Build and execute the workflow.

        Args:
            initial_vars: Initial variables to set before execution
            timeout: Maximum execution time in seconds

        Returns:
            WorkflowExecutionResult with success status, variables, error info
        """
        import time

        from casare_rpa.application.use_cases.execute_workflow import (
            ExecuteWorkflowUseCase,
        )
        from casare_rpa.application.use_cases.execution_state_manager import (
            ExecutionSettings,
        )

        workflow = self.build()
        start_time = time.perf_counter()

        # Prepare initial variables
        all_initial_vars = dict(initial_vars or {})

        # Create settings
        settings = ExecutionSettings(
            continue_on_error=False,
            node_timeout=timeout,
        )

        # Create and execute use case
        use_case = ExecuteWorkflowUseCase(
            workflow=workflow,
            event_bus=None,  # Use global event bus
            settings=settings,
            initial_variables=all_initial_vars,
            project_context=None,
        )

        try:
            success = await asyncio.wait_for(
                use_case.execute(),
                timeout=timeout,
            )

            # Extract final variables (excluding internal ones)
            final_variables = {}
            if use_case.context is not None:
                final_variables = {
                    k: v
                    for k, v in use_case.context.variables.items()
                    if not k.startswith("_")
                }

            duration_ms = (time.perf_counter() - start_time) * 1000

            return WorkflowExecutionResult(
                success=success,
                variables=final_variables,
                error=use_case.state_manager.execution_error if not success else None,
                executed_nodes=len(use_case.state_manager.executed_nodes),
                duration_ms=duration_ms,
            )

        except asyncio.TimeoutError:
            duration_ms = (time.perf_counter() - start_time) * 1000
            use_case.stop()

            return WorkflowExecutionResult(
                success=False,
                variables={},
                error=f"Workflow execution timed out after {timeout}s",
                executed_nodes=len(use_case.state_manager.executed_nodes),
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.exception(f"Workflow execution failed: {e}")

            return WorkflowExecutionResult(
                success=False,
                variables={},
                error=str(e),
                executed_nodes=0,
                duration_ms=duration_ms,
            )
