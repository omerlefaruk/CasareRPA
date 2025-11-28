"""
Control flow nodes for CasareRPA.

This module implements conditional and loop nodes for workflow control flow.
"""

from typing import Optional
from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import executable_node
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.domain.value_objects.types import (
    PortType,
    DataType,
    NodeStatus,
    ExecutionResult,
)
from ..utils.security.safe_eval import safe_eval, is_safe_expression


class IfNode(BaseNode):
    """
    Conditional node that executes different paths based on condition.

    Evaluates a condition and routes execution to either 'true' or 'false' output.
    Supports boolean inputs or expression evaluation.
    """

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize If node."""
        super().__init__(node_id, config)
        self.name = "If"
        self.node_type = "IfNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("condition", PortType.INPUT, DataType.ANY, required=False)
        self.add_output_port("true", PortType.EXEC_OUTPUT)
        self.add_output_port("false", PortType.EXEC_OUTPUT)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute conditional logic.

        Args:
            context: Execution context

        Returns:
            Result with next node based on condition
        """
        self.status = NodeStatus.RUNNING

        try:
            # Get condition value
            condition = self.get_input_value("condition")

            # If no input, check config for expression
            if condition is None:
                expression = self.config.get("expression", "")
                if expression:
                    # Safely evaluate expression with context variables
                    try:
                        if not is_safe_expression(expression):
                            raise ValueError(
                                f"Unsafe expression detected: {expression}"
                            )
                        condition = safe_eval(expression, context.variables)
                    except Exception as e:
                        logger.warning(
                            f"Failed to evaluate expression '{expression}': {e}"
                        )
                        condition = False
                else:
                    condition = False

            # Convert to boolean
            result = bool(condition)

            # Determine next node
            next_port = "true" if result else "false"

            self.status = NodeStatus.SUCCESS
            logger.info(f"If condition evaluated to: {result} -> {next_port}")

            return {
                "success": True,
                "data": {"condition": result},
                "next_nodes": [next_port],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"If node execution failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}


class ForLoopStartNode(BaseNode):
    """
    Start node of a For Loop pair (ForLoopStart + ForLoopEnd).

    Use with ForLoopEndNode to create loops with nodes inside.
    The ForLoopEnd connects back to continue iteration.

    Inputs:
        - items: List to iterate over (optional, uses range if not provided)
        - end: End value for range iteration

    Outputs:
        - body: Execution flow for loop body (connect to first node inside loop)
        - current_item: Current item in iteration
        - current_index: Current index (0-based)
        - completed: Fires when all iterations complete
    """

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize For Loop Start node."""
        super().__init__(node_id, config)
        self.name = "For Loop Start"
        self.node_type = "ForLoopStartNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("items", PortType.INPUT, DataType.LIST, required=False)
        self.add_input_port("end", PortType.INPUT, DataType.INTEGER, required=False)
        self.add_output_port("body", PortType.EXEC_OUTPUT)
        self.add_output_port("completed", PortType.EXEC_OUTPUT)
        self.add_output_port("current_item", PortType.OUTPUT, DataType.ANY)
        self.add_output_port("current_index", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute for loop start - handles iteration logic.
        """
        self.status = NodeStatus.RUNNING

        try:
            # Get items to iterate
            items = self.get_input_value("items")

            # If no input, create range from config/inputs
            if items is None:
                start = int(self.config.get("start", 0))
                end_input = self.get_input_value("end")
                end = (
                    int(end_input)
                    if end_input is not None
                    else int(self.config.get("end", 10))
                )
                step = int(self.config.get("step", 1))
                items = list(range(start, end, step))

            # Ensure items is iterable
            if not hasattr(items, "__iter__") or isinstance(items, str):
                items = [items]

            # Store loop state in context
            loop_state_key = f"{self.node_id}_loop_state"

            # Check if this is first iteration or continuation (from ForLoopEnd)
            if loop_state_key not in context.variables:
                # Initialize loop state
                context.variables[loop_state_key] = {"items": list(items), "index": 0}

            loop_state = context.variables[loop_state_key]
            index = loop_state["index"]
            items_list = loop_state["items"]

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

            # Get current item
            current_item = items_list[index]

            # Set output values
            self.set_output_value("current_item", current_item)
            self.set_output_value("current_index", index)

            # Increment index for next iteration
            loop_state["index"] = index + 1

            self.status = NodeStatus.RUNNING
            logger.info(
                f"For loop iteration {index}/{len(items_list)}: current_item={repr(current_item)[:100]}"
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


@executable_node
class ForLoopEndNode(BaseNode):
    """
    End node of a For Loop pair (ForLoopStart + ForLoopEnd).

    Place after all nodes inside the loop body.
    Automatically loops back to the paired ForLoopStartNode.
    The paired_start_id is set automatically when created via "For Loop" menu.

    Outputs:
        - exec_out: Fires after loop completes (connected to ForLoopStart.completed internally)
    """

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize For Loop End node."""
        super().__init__(node_id, config)
        self.name = "For Loop End"
        self.node_type = "ForLoopEndNode"
        # Paired start node ID - set when created together
        self.paired_start_id: str = config.get("paired_start_id", "") if config else ""

    def _define_ports(self) -> None:
        """Define node ports."""
        pass  # exec_in and exec_out added by @executable_node decorator

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
        loop_start_id = self.paired_start_id or self.config.get("paired_start_id", "")

        if not loop_start_id:
            # Try to find it from context (fallback)
            logger.warning(
                "ForLoopEndNode has no paired ForLoopStartNode - check loop setup"
            )
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

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize While Loop Start node."""
        super().__init__(node_id, config)
        self.name = "While Loop Start"
        self.node_type = "WhileLoopStartNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port(
            "condition", PortType.INPUT, DataType.BOOLEAN, required=False
        )
        self.add_output_port("body", PortType.EXEC_OUTPUT)
        self.add_output_port("completed", PortType.EXEC_OUTPUT)
        self.add_output_port("current_iteration", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute while loop start - evaluates condition and manages iteration."""
        self.status = NodeStatus.RUNNING

        try:
            loop_state_key = f"{self.node_id}_loop_state"
            max_iterations = int(self.config.get("max_iterations") or 1000)

            # Initialize or get loop state
            if loop_state_key not in context.variables:
                context.variables[loop_state_key] = {"iteration": 0}

            loop_state = context.variables[loop_state_key]
            iteration = loop_state["iteration"]

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

            # Evaluate condition
            condition = self.get_input_value("condition")

            # If no input, check config for expression
            if condition is None:
                expression = self.config.get("expression", "")
                if expression:
                    try:
                        if not is_safe_expression(expression):
                            raise ValueError(
                                f"Unsafe expression detected: {expression}"
                            )
                        condition = safe_eval(expression, context.variables)
                    except Exception as e:
                        logger.warning(
                            f"Failed to evaluate expression '{expression}': {e}"
                        )
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


@executable_node
class WhileLoopEndNode(BaseNode):
    """
    End node of a While Loop pair (WhileLoopStart + WhileLoopEnd).

    Place after all nodes inside the loop body.
    Automatically loops back to the paired WhileLoopStartNode.

    Outputs:
        - exec_out: Fires after loop completes
    """

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize While Loop End node."""
        super().__init__(node_id, config)
        self.name = "While Loop End"
        self.node_type = "WhileLoopEndNode"
        self.paired_start_id: str = config.get("paired_start_id", "") if config else ""

    def _define_ports(self) -> None:
        """Define node ports."""
        pass  # exec_in and exec_out added by @executable_node decorator

    def set_paired_start(self, start_node_id: str) -> None:
        """Set the paired WhileLoopStart node ID."""
        self.paired_start_id = start_node_id
        self.config["paired_start_id"] = start_node_id

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute while loop end - signals to loop back to start."""
        self.status = NodeStatus.SUCCESS

        loop_start_id = self.paired_start_id or self.config.get("paired_start_id", "")

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


@executable_node
class BreakNode(BaseNode):
    """
    Loop control node that exits from the current loop.

    Signals the parent loop (For/While) to terminate immediately.
    Can only be used inside loop_body execution path.
    """

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize Break node."""
        super().__init__(node_id, config)
        self.name = "Break"
        self.node_type = "BreakNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        pass  # exec_in and exec_out added by @executable_node decorator

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute break - signals loop to exit.

        Args:
            context: Execution context

        Returns:
            Result with break signal
        """
        self.status = NodeStatus.RUNNING

        try:
            logger.info("Break executed - loop will exit")

            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "control_flow": "break",
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Break execution failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}


@executable_node
class ContinueNode(BaseNode):
    """
    Loop control node that skips to next iteration.

    Signals the parent loop (For/While) to skip remaining loop body
    and proceed to the next iteration.
    Can only be used inside loop_body execution path.
    """

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize Continue node."""
        super().__init__(node_id, config)
        self.name = "Continue"
        self.node_type = "ContinueNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        pass  # exec_in and exec_out added by @executable_node decorator

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute continue - signals loop to skip to next iteration.

        Args:
            context: Execution context

        Returns:
            Result with continue signal
        """
        self.status = NodeStatus.RUNNING

        try:
            logger.info("Continue executed - skipping to next iteration")

            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "control_flow": "continue",
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Continue execution failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}


class SwitchNode(BaseNode):
    """
    Multi-way branching node based on value matching.

    Evaluates an input value and routes to matching case output.
    Falls back to 'default' if no case matches.
    """

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize Switch node."""
        super().__init__(node_id, config)
        self.name = "Switch"
        self.node_type = "SwitchNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("value", PortType.INPUT, DataType.ANY, required=False)

        # Get cases from config (e.g., ["success", "error", "pending"])
        cases = self.config.get("cases", [])
        for case in cases:
            self.add_output_port(f"case_{case}", PortType.EXEC_OUTPUT)

        self.add_output_port("default", PortType.EXEC_OUTPUT)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute switch logic - match value to case.

        Args:
            context: Execution context

        Returns:
            Result with matched case or default
        """
        self.status = NodeStatus.RUNNING

        try:
            # Get value to match
            value = self.get_input_value("value")

            # If no value input, try expression
            if value is None:
                expression = self.config.get("expression", "")
                if expression:
                    # Safely evaluate expression with context variables
                    if not is_safe_expression(expression):
                        raise ValueError(f"Unsafe expression detected: {expression}")
                    value = safe_eval(expression, context.variables)

            # Convert to string for matching
            value_str = str(value) if value is not None else ""

            # Check each case
            cases = self.config.get("cases", [])
            for case in cases:
                if str(case) == value_str:
                    next_port = f"case_{case}"
                    logger.info(f"Switch matched case: {case} -> {next_port}")

                    self.status = NodeStatus.SUCCESS
                    return {
                        "success": True,
                        "data": {"matched_case": case, "value": value},
                        "next_nodes": [next_port],
                    }

            # No match - use default
            logger.info(f"Switch no match for '{value}' -> default")

            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"matched_case": "default", "value": value},
                "next_nodes": ["default"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Switch execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "next_nodes": ["default"],  # Fallback on error
            }
