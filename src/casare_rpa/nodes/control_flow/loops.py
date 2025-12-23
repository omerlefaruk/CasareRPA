"""
CasareRPA - Loop Control Flow Nodes

Provides nodes for iteration:
- ForLoopStartNode / ForLoopEndNode: Counter or collection iteration
- WhileLoopStartNode / WhileLoopEndNode: Condition-based iteration
- BreakNode: Exit loop early
- ContinueNode: Skip to next iteration
"""

import re
from typing import Optional

from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeStatus,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.utils.security.safe_eval import is_safe_expression, safe_eval


@properties(
    PropertyDef(
        "mode",
        PropertyType.CHOICE,
        default="items",
        choices=["items", "range"],
        label="Mode",
        tooltip="Iteration mode: 'items' for collection iteration (ForEach), 'range' for counter-based iteration",
    ),
    PropertyDef(
        "list_var",
        PropertyType.STRING,
        default="",
        label="List Variable",
        tooltip="Variable name containing the list to iterate over (for 'items' mode)",
    ),
    PropertyDef(
        "item_var",
        PropertyType.STRING,
        default="item",
        label="Item Variable",
        tooltip="Variable name to store current item in context",
    ),
    PropertyDef(
        "start",
        PropertyType.INTEGER,
        default=0,
        label="Start",
        tooltip="Start value for range iteration (when mode='range')",
    ),
    PropertyDef(
        "end",
        PropertyType.INTEGER,
        default=10,
        label="End",
        tooltip="End value for range iteration (when mode='range')",
    ),
    PropertyDef(
        "step",
        PropertyType.INTEGER,
        default=1,
        min_value=1,
        label="Step",
        tooltip="Step value for range iteration (when mode='range')",
    ),
)
@node(category="control_flow", exec_outputs=["body", "completed"])
class ForLoopStartNode(BaseNode):
    """
    Start node of a For Loop pair (ForLoopStart + ForLoopEnd).

    Use with ForLoopEndNode to create loops with nodes inside.
    The ForLoopEnd connects back to continue iteration.

    Supports two modes:
        - items: ForEach mode - iterates over a collection (list, dict)
        - range: Counter mode - iterates over a numeric range

    Inputs:
        - items: List/dict to iterate over (for 'items' mode)
        - end: End value for range iteration (for 'range' mode)

    Outputs:
        - body: Execution flow for loop body (connect to first node inside loop)
        - current_item: Current item in iteration
        - current_index: Current index (0-based)
        - current_key: Current key (for dict iteration, None otherwise)
        - completed: Fires when all iterations complete
    """

    # @category: control_flow
    # @requires: none
    # @ports: exec_in, items, end -> body, completed, current_item, current_index, current_key

    def __init__(self, node_id: str, config: dict | None = None) -> None:
        """Initialize For Loop Start node."""
        super().__init__(node_id, config)
        self.name = "For Loop Start"
        self.node_type = "ForLoopStartNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        # Note: exec_in/exec_out are added by @node decorator
        self.add_input_port("items", DataType.ANY, required=False)
        self.add_input_port("end", DataType.INTEGER, required=False)
        self.add_exec_output("body")
        self.add_exec_output("completed")
        self.add_output_port("current_item", DataType.ANY)
        self.add_output_port("current_index", DataType.INTEGER)
        self.add_output_port("current_key", DataType.ANY)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute for loop start - handles iteration logic.

        Supports two modes:
        - items: Iterates over input items (list or dict)
        - range: Iterates over numeric range (start, end, step)
        """
        self.status = NodeStatus.RUNNING

        try:
            mode = self.get_parameter("mode", "items")
            loop_state_key = f"{self.node_id}_loop_state"

            # Check if this is first iteration or continuation (from ForLoopEnd)
            if loop_state_key not in context.variables:
                # Initialize loop state based on mode
                if mode == "range":
                    # Range mode - use start, end, step
                    start = self.get_parameter("start", 0)
                    end_input = self.get_input_value("end")
                    end = end_input if end_input is not None else self.get_parameter("end", 10)
                    step = self.get_parameter("step", 1)
                    items = list(range(start, end, step))
                    keys = None  # No keys for range mode
                else:
                    # Items mode - use input items or list_var from context
                    items = self.get_input_value("items")

                    # Try list_var from context if no port connection
                    if items is None:
                        list_var = self.get_parameter("list_var", "")
                        if list_var:
                            items = context.get_variable(list_var)

                    if items is None:
                        # Fallback to range if no items provided
                        start = self.get_parameter("start", 0)
                        end = self.get_parameter("end", 10)
                        step = self.get_parameter("step", 1)
                        items = list(range(start, end, step))
                        keys = None
                    elif isinstance(items, dict):
                        # Dict iteration - store keys separately
                        keys = list(items.keys())
                        items = list(items.values())
                    elif isinstance(items, str):
                        # String - iterate over characters
                        items = list(items)
                        keys = None
                    elif hasattr(items, "__iter__"):
                        items = list(items)
                        keys = None
                    else:
                        # Single item
                        items = [items]
                        keys = None

                context.variables[loop_state_key] = {
                    "items": items,
                    "keys": keys,
                    "index": 0,
                }

            loop_state = context.variables[loop_state_key]
            index = loop_state["index"]
            items_list = loop_state["items"]
            keys_list = loop_state.get("keys")

            # Check if break was requested
            if loop_state.get("break_requested"):
                # Break - clean up and go to completed
                del context.variables[loop_state_key]
                self.status = NodeStatus.SUCCESS
                logger.info(f"For loop exited via break after {index} iterations")

                return {
                    "success": True,
                    "data": {"iterations": index, "break": True},
                    "next_nodes": ["completed"],
                }

            # Check if loop is complete
            if index >= len(items_list):
                # Loop finished - clean up and go to completed
                del context.variables[loop_state_key]
                self.status = NodeStatus.SUCCESS
                logger.info(f"For loop completed after {index} iterations")

                return {
                    "success": True,
                    "data": {"iterations": index},
                    "next_nodes": ["completed"],
                }

            # Get current item and key
            current_item = items_list[index]
            current_key = keys_list[index] if keys_list else None

            # Set output values
            self.set_output_value("current_item", current_item)
            self.set_output_value("current_index", index)
            self.set_output_value("current_key", current_key)

            # Store current item in context variable (item_var)
            item_var = self.get_parameter("item_var", "item")
            if item_var:
                context.set_variable(item_var, current_item)
                if current_key is not None:
                    context.set_variable(f"{item_var}_key", current_key)
                context.set_variable(f"{item_var}_index", index)

            # Increment index for next iteration
            loop_state["index"] = index + 1

            self.status = NodeStatus.RUNNING
            key_str = f", key={repr(current_key)}" if current_key is not None else ""
            logger.info(
                f"For loop iteration {index}/{len(items_list)}: item={repr(current_item)[:100]}{key_str}"
            )

            return {
                "success": True,
                "data": {
                    "item": current_item,
                    "index": index,
                    "remaining": len(items_list) - index - 1,
                },
                "next_nodes": ["body"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"For loop start execution failed: {e}")
            loop_state_key = f"{self.node_id}_loop_state"
            if loop_state_key in context.variables:
                del context.variables[loop_state_key]
            return {"success": False, "error": str(e), "next_nodes": []}


@properties(
    PropertyDef(
        "paired_start_id",
        PropertyType.STRING,
        default="",
        label="Paired Loop Start",
        tooltip="ID of the paired ForLoopStartNode (set automatically)",
    ),
)
@node(category="control_flow")
class ForLoopEndNode(BaseNode):
    """
    End node of a For Loop pair (ForLoopStart + ForLoopEnd).

    Place after all nodes inside the loop body.
    Automatically loops back to the paired ForLoopStartNode.
    The paired_start_id is set automatically when created via "For Loop" menu.

    Outputs:
        - exec_out: Fires after loop completes (connected to ForLoopStart.completed internally)
    """

    # @category: control_flow
    # @requires: none
    # @ports: none -> none

    def __init__(self, node_id: str, config: dict | None = None) -> None:
        """Initialize For Loop End node."""
        super().__init__(node_id, config)
        self.name = "For Loop End"
        self.node_type = "ForLoopEndNode"
        # Paired start node ID - load from config or empty
        self.paired_start_id: str = self.get_parameter("paired_start_id", "")

    def _define_ports(self) -> None:
        """Define node ports."""
        pass  # exec_in and exec_out added by @node decorator

    def set_paired_start(self, start_node_id: str) -> None:
        """Set the paired ForLoopStart node ID."""
        self.paired_start_id = start_node_id
        self.config["paired_start_id"] = start_node_id

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute for loop end - signals to loop back to start.
        """
        self.status = NodeStatus.SUCCESS

        # Get the paired ForLoopStart node ID
        loop_start_id = self.paired_start_id or self.get_parameter("paired_start_id", "")

        if not loop_start_id:
            # Try to find it from context (fallback)
            logger.warning("ForLoopEndNode has no paired ForLoopStartNode - check loop setup")
            return {
                "success": True,
                "data": {},
                "next_nodes": ["exec_out"],  # Just continue to exec_out
            }

        # Check if the loop is complete by looking at loop state
        loop_state_key = f"{loop_start_id}_loop_state"
        if loop_state_key not in context.variables:
            # Loop has completed - go to exec_out
            logger.debug("For loop completed - continuing to exec_out")
            return {"success": True, "data": {}, "next_nodes": ["exec_out"]}

        logger.debug(f"For loop end - looping back to {loop_start_id}")

        # Return special instruction to loop back
        return {
            "success": True,
            "data": {},
            "next_nodes": [],
            "loop_back_to": loop_start_id,  # Special key for workflow runner
        }


@properties(
    PropertyDef(
        "expression",
        PropertyType.STRING,
        default="",
        label="Expression",
        tooltip="Boolean expression to evaluate each iteration (optional if using input port)",
        placeholder="{{counter}} < 100",
    ),
    PropertyDef(
        "max_iterations",
        PropertyType.INTEGER,
        default=1000,
        min_value=1,
        label="Max Iterations",
        tooltip="Maximum iterations to prevent infinite loops",
    ),
)
@node(category="control_flow", exec_outputs=["body", "completed"])
class WhileLoopStartNode(BaseNode):
    """
    Start node of a While Loop pair (WhileLoopStart + WhileLoopEnd).

    Evaluates condition on each iteration and continues until false.
    Includes max iterations safety limit to prevent infinite loops.

    Inputs:
        - condition: Boolean condition to evaluate each iteration

    Outputs:
        - body: Execution flow for loop body
        - current_iteration: Current iteration number (0-based)
        - completed: Fires when condition becomes false
    """

    # @category: control_flow
    # @requires: none
    # @ports: exec_in, condition -> body, completed, current_iteration

    def __init__(self, node_id: str, config: dict | None = None) -> None:
        """Initialize While Loop Start node."""
        super().__init__(node_id, config)
        self.name = "While Loop Start"
        self.node_type = "WhileLoopStartNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        # Note: exec_in/exec_out are added by @node decorator
        self.add_input_port("condition", DataType.BOOLEAN, required=False)
        self.add_exec_output("body")
        self.add_exec_output("completed")
        self.add_output_port("current_iteration", DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute while loop start - evaluates condition and manages iteration."""
        self.status = NodeStatus.RUNNING

        try:
            loop_state_key = f"{self.node_id}_loop_state"
            max_iterations = self.get_parameter("max_iterations", 1000)

            # Initialize or get loop state
            if loop_state_key not in context.variables:
                context.variables[loop_state_key] = {"iteration": 0}

            loop_state = context.variables[loop_state_key]
            iteration = loop_state["iteration"]

            # Check if break was requested
            if loop_state.get("break_requested"):
                # Break - clean up and go to completed
                del context.variables[loop_state_key]
                self.status = NodeStatus.SUCCESS
                logger.info(f"While loop exited via break after {iteration} iterations")

                return {
                    "success": True,
                    "data": {"iterations": iteration, "break": True},
                    "next_nodes": ["completed"],
                }

            # Safety check for infinite loops
            if iteration >= max_iterations:
                del context.variables[loop_state_key]
                logger.warning(f"While loop hit max iterations limit: {max_iterations}")
                self.status = NodeStatus.SUCCESS
                return {
                    "success": True,
                    "data": {"iterations": iteration, "reason": "max_iterations"},
                    "next_nodes": ["completed"],
                }

            # Evaluate condition from input port first
            condition = self.get_input_value("condition")

            # If no input, check config for expression
            if condition is None:
                expression = self.get_parameter("expression", "")
                if expression:
                    try:
                        # Convert {{variable}} syntax to plain variable names
                        resolved_expr = re.sub(r"\{\{(\w+)\}\}", r"\1", expression)
                        if not is_safe_expression(resolved_expr):
                            raise ValueError(f"Unsafe expression detected: {resolved_expr}")
                        condition = safe_eval(resolved_expr, context.variables)
                    except Exception as e:
                        logger.warning(f"Failed to evaluate expression '{expression}': {e}")
                        condition = False
                else:
                    condition = False

            should_continue = bool(condition)

            if not should_continue:
                # Loop finished
                del context.variables[loop_state_key]
                self.status = NodeStatus.SUCCESS
                logger.info(f"While loop completed after {iteration} iterations")
                return {
                    "success": True,
                    "data": {"iterations": iteration},
                    "next_nodes": ["completed"],
                }

            # Continue loop
            self.set_output_value("current_iteration", iteration)
            loop_state["iteration"] = iteration + 1

            self.status = NodeStatus.RUNNING
            logger.debug(f"While loop iteration {iteration}")

            return {
                "success": True,
                "data": {"iteration": iteration},
                "next_nodes": ["body"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"While loop start execution failed: {e}")
            loop_state_key = f"{self.node_id}_loop_state"
            if loop_state_key in context.variables:
                del context.variables[loop_state_key]
            return {"success": False, "error": str(e), "next_nodes": []}


@properties(
    PropertyDef(
        "paired_start_id",
        PropertyType.STRING,
        default="",
        label="Paired Loop Start",
        tooltip="ID of the paired WhileLoopStartNode (set automatically)",
    ),
)
@node(category="control_flow")
class WhileLoopEndNode(BaseNode):
    """
    End node of a While Loop pair (WhileLoopStart + WhileLoopEnd).

    Place after all nodes inside the loop body.
    Automatically loops back to the paired WhileLoopStartNode.

    Outputs:
        - exec_out: Fires after loop completes
    """

    # @category: control_flow
    # @requires: none
    # @ports: none -> none

    def __init__(self, node_id: str, config: dict | None = None) -> None:
        """Initialize While Loop End node."""
        super().__init__(node_id, config)
        self.name = "While Loop End"
        self.node_type = "WhileLoopEndNode"
        # Paired start node ID - load from config or empty
        self.paired_start_id: str = self.get_parameter("paired_start_id", "")

    def _define_ports(self) -> None:
        """Define node ports."""
        pass  # exec_in and exec_out added by @node decorator

    def set_paired_start(self, start_node_id: str) -> None:
        """Set the paired WhileLoopStart node ID."""
        self.paired_start_id = start_node_id
        self.config["paired_start_id"] = start_node_id

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute while loop end - signals to loop back to start."""
        self.status = NodeStatus.SUCCESS

        loop_start_id = self.paired_start_id or self.get_parameter("paired_start_id", "")

        if not loop_start_id:
            logger.warning("WhileLoopEndNode has no paired WhileLoopStartNode")
            return {"success": True, "data": {}, "next_nodes": ["exec_out"]}

        # Check if the loop is complete
        loop_state_key = f"{loop_start_id}_loop_state"
        if loop_state_key not in context.variables:
            logger.debug("While loop completed - continuing to exec_out")
            return {"success": True, "data": {}, "next_nodes": ["exec_out"]}

        logger.debug(f"While loop end - looping back to {loop_start_id}")

        return {
            "success": True,
            "data": {},
            "next_nodes": [],
            "loop_back_to": loop_start_id,
        }


@properties(
    PropertyDef(
        "paired_loop_start_id",
        PropertyType.STRING,
        default="",
        label="Paired Loop Start",
        tooltip="ID of the parent loop's start node (set automatically)",
    ),
)
@node(category="control_flow")
class BreakNode(BaseNode):
    """
    Loop control node that exits from the current loop.

    Signals the parent loop (For/While) to terminate immediately.
    Can only be used inside loop_body execution path.
    """

    # @category: control_flow
    # @requires: none
    # @ports: none -> none

    def __init__(self, node_id: str, config: dict | None = None) -> None:
        """Initialize Break node."""
        super().__init__(node_id, config)
        self.name = "Break"
        self.node_type = "BreakNode"
        # Paired loop start node ID - load from config
        self.paired_loop_start_id: str = self.get_parameter("paired_loop_start_id", "")

    def _define_ports(self) -> None:
        """Define node ports."""
        pass  # exec_in and exec_out added by @node decorator

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute break - signals loop to exit.

        Args:
            context: Execution context

        Returns:
            Result with loop_back_to and break_requested flag
        """
        self.status = NodeStatus.RUNNING

        try:
            # Get the paired loop start node ID
            loop_start_id = self.paired_loop_start_id or self.get_parameter(
                "paired_loop_start_id", ""
            )

            if not loop_start_id:
                logger.warning(
                    "BreakNode has no paired loop - check loop setup. " "Continuing to exec_out."
                )
                self.status = NodeStatus.SUCCESS
                return {
                    "success": True,
                    "control_flow": "break",
                    "next_nodes": ["exec_out"],
                }

            # Set break flag in loop state so ForLoopStart knows to exit
            loop_state_key = f"{loop_start_id}_loop_state"
            if loop_state_key in context.variables:
                context.variables[loop_state_key]["break_requested"] = True

            logger.info(f"Break executed - exiting loop {loop_start_id}")

            self.status = NodeStatus.SUCCESS
            # Return loop_back_to so the loop start can check for break
            return {
                "success": True,
                "data": {},
                "next_nodes": [],
                "loop_back_to": loop_start_id,
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Break execution failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}


@properties(
    PropertyDef(
        "paired_loop_start_id",
        PropertyType.STRING,
        default="",
        label="Paired Loop Start",
        tooltip="ID of the parent loop's start node (set automatically)",
    ),
)
@node(category="control_flow")
class ContinueNode(BaseNode):
    """
    Loop control node that skips to next iteration.

    Signals the parent loop (For/While) to skip remaining loop body
    and proceed to the next iteration.
    Can only be used inside loop_body execution path.
    """

    # @category: control_flow
    # @requires: none
    # @ports: none -> none

    def __init__(self, node_id: str, config: dict | None = None) -> None:
        """Initialize Continue node."""
        super().__init__(node_id, config)
        self.name = "Continue"
        self.node_type = "ContinueNode"
        # Paired loop start node ID - load from config
        self.paired_loop_start_id: str = self.get_parameter("paired_loop_start_id", "")

    def _define_ports(self) -> None:
        """Define node ports."""
        pass  # exec_in and exec_out added by @node decorator

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute continue - signals loop to skip to next iteration.

        Args:
            context: Execution context

        Returns:
            Result with loop_back_to for the paired loop start
        """
        self.status = NodeStatus.RUNNING

        try:
            # Get the paired loop start node ID
            loop_start_id = self.paired_loop_start_id or self.get_parameter(
                "paired_loop_start_id", ""
            )

            if not loop_start_id:
                logger.warning(
                    "ContinueNode has no paired loop - check loop setup. " "Continuing to exec_out."
                )
                self.status = NodeStatus.SUCCESS
                return {
                    "success": True,
                    "control_flow": "continue",
                    "next_nodes": ["exec_out"],
                }

            logger.info(f"Continue executed - looping back to {loop_start_id}")

            self.status = NodeStatus.SUCCESS
            # Return loop_back_to to trigger the next iteration
            # This is the same mechanism used by ForLoopEndNode
            return {
                "success": True,
                "data": {},
                "next_nodes": [],
                "loop_back_to": loop_start_id,
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Continue execution failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}


__all__ = [
    "ForLoopStartNode",
    "ForLoopEndNode",
    "WhileLoopStartNode",
    "WhileLoopEndNode",
    "BreakNode",
    "ContinueNode",
]
