"""
Control flow nodes for CasareRPA.

This module implements conditional and loop nodes for workflow control flow.
"""

from typing import Optional
from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.domain.value_objects.types import (
    PortType,
    DataType,
    NodeStatus,
    ExecutionResult,
)
from casare_rpa.utils.security.safe_eval import safe_eval, is_safe_expression


@node_schema(
    PropertyDef(
        "expression",
        PropertyType.STRING,
        default="",
        label="Expression",
        tooltip="Boolean expression to evaluate (optional if using input port)",
        placeholder="{{variable}} > 10",
    ),
)
@executable_node
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
            # Get condition value from input port first
            condition = self.get_input_value("condition")

            # If no input, check config for expression
            if condition is None:
                expression = self.get_parameter("expression", "")
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


@node_schema(
    PropertyDef(
        "mode",
        PropertyType.CHOICE,
        default="items",
        choices=["items", "range"],
        label="Mode",
        tooltip="Iteration mode: 'items' for collection iteration (ForEach), 'range' for counter-based iteration",
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
@executable_node
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

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize For Loop Start node."""
        super().__init__(node_id, config)
        self.name = "For Loop Start"
        self.node_type = "ForLoopStartNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("items", PortType.INPUT, DataType.ANY, required=False)
        self.add_input_port("end", PortType.INPUT, DataType.INTEGER, required=False)
        self.add_output_port("body", PortType.EXEC_OUTPUT)
        self.add_output_port("completed", PortType.EXEC_OUTPUT)
        self.add_output_port("current_item", PortType.OUTPUT, DataType.ANY)
        self.add_output_port("current_index", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("current_key", PortType.OUTPUT, DataType.ANY)

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
                    end = (
                        end_input
                        if end_input is not None
                        else self.get_parameter("end", 10)
                    )
                    step = self.get_parameter("step", 1)
                    items = list(range(start, end, step))
                    keys = None  # No keys for range mode
                else:
                    # Items mode - use input items
                    items = self.get_input_value("items")

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
        # Paired start node ID - set automatically, not user-configurable
        self.paired_start_id: str = ""

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
        loop_start_id = self.paired_start_id or self.get_parameter(
            "paired_start_id", ""
        )

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


@node_schema(
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
@executable_node
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
            max_iterations = self.get_parameter("max_iterations", 1000)

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

            # Evaluate condition from input port first
            condition = self.get_input_value("condition")

            # If no input, check config for expression
            if condition is None:
                expression = self.get_parameter("expression", "")
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
        # Paired start node ID - set automatically, not user-configurable
        self.paired_start_id: str = ""

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

        loop_start_id = self.paired_start_id or self.get_parameter(
            "paired_start_id", ""
        )

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


@executable_node
class MergeNode(BaseNode):
    """
    Merge node that allows multiple execution paths to converge.

    This is a pass-through node that accepts multiple incoming exec connections
    and continues to a single output. Use this to join branches from If/Switch
    nodes back into a single execution path.

    Example:
        If ──┬── TRUE ─────────┬──→ Merge ──→ NextNode
             └── FALSE → ... ──┘
    """

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize Merge node."""
        super().__init__(node_id, config)
        self.name = "Merge"
        self.node_type = "MergeNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        # exec_in and exec_out added by @executable_node decorator
        pass

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute merge - simply passes execution through.

        Args:
            context: Execution context

        Returns:
            Result continuing to exec_out
        """
        self.status = NodeStatus.RUNNING

        try:
            logger.debug("Merge node - passing execution through")
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Merge node execution failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}


@node_schema(
    PropertyDef(
        "cases",
        PropertyType.LIST,
        default=[],
        label="Cases",
        tooltip="List of case values to match (e.g., ['success', 'error', 'pending'])",
    ),
    PropertyDef(
        "expression",
        PropertyType.STRING,
        default="",
        label="Expression",
        tooltip="Expression to evaluate for value (optional if using input port)",
        placeholder="{{status}}",
    ),
)
@executable_node
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
        cases = self.get_parameter("cases", [])
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
            # Get value to match from input port first
            value = self.get_input_value("value")

            # If no value input, try expression
            if value is None:
                expression = self.get_parameter("expression", "")
                if expression:
                    # Safely evaluate expression with context variables
                    if not is_safe_expression(expression):
                        raise ValueError(f"Unsafe expression detected: {expression}")
                    value = safe_eval(expression, context.variables)

            # Convert to string for matching
            value_str = str(value) if value is not None else ""

            # Check each case
            cases = self.get_parameter("cases", [])
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


# =============================================================================
# TRY/CATCH/FINALLY NODES
# =============================================================================


@executable_node
class TryNode(BaseNode):
    """
    Try block for error handling.

    Use with CatchNode and FinallyNode to create try/catch/finally blocks.
    When an error occurs in any node within the try body, execution routes
    to the CatchNode instead of failing the workflow.

    Layout: Try, Catch, Finally are placed side-by-side automatically.

    Outputs:
        - try_body: Execution flow for the try block (connect nodes here)
        - exec_out: Continues after try body completes (no error)
    """

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize Try node."""
        super().__init__(node_id, config)
        self.name = "Try"
        self.node_type = "TryNode"
        # Paired nodes - set automatically when created together
        self.paired_catch_id: str = ""
        self.paired_finally_id: str = ""

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)  # Main flow (top)
        self.add_output_port("try_body", PortType.EXEC_OUTPUT)  # Try body (below)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute try - initializes error capture state."""
        self.status = NodeStatus.RUNNING

        try:
            # Initialize try state for error capture
            try_state_key = f"{self.node_id}_try_state"
            context.variables[try_state_key] = {
                "error": False,
                "error_type": None,
                "error_message": None,
                "stack_trace": None,
                "catch_id": self.paired_catch_id,
                "finally_id": self.paired_finally_id,
            }

            logger.debug(f"Try block started: {self.node_id}")
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"try_state_key": try_state_key},
                "next_nodes": ["try_body"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Try execution failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}


@node_schema(
    PropertyDef(
        "error_types",
        PropertyType.STRING,
        default="",
        label="Error Types",
        tooltip="Comma-separated error types to catch (empty = catch all). E.g., 'ValueError,KeyError'",
    ),
)
@executable_node
class CatchNode(BaseNode):
    """
    Catch block for handling errors from the Try block.

    Receives errors from the paired Try block and provides error details
    as output ports. Can filter by error type.

    Paired automatically with Try and Finally nodes when created together.

    Outputs:
        - catch_body: Execution flow for error handling
        - error_message: The error message string
        - error_type: The error type/class name
        - stack_trace: Full stack trace (if available)
    """

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize Catch node."""
        super().__init__(node_id, config)
        self.name = "Catch"
        self.node_type = "CatchNode"
        # Paired automatically when created together
        self.paired_try_id: str = ""
        self.paired_finally_id: str = ""

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("catch_body", PortType.EXEC_OUTPUT)
        self.add_output_port("error_message", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("error_type", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("stack_trace", PortType.OUTPUT, DataType.STRING)

    def set_paired_try(self, try_node_id: str) -> None:
        """Set the paired Try node ID (called automatically)."""
        self.paired_try_id = try_node_id

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute catch - provides error details and executes catch body."""
        self.status = NodeStatus.RUNNING

        try:
            try_id = self.paired_try_id or self.get_parameter("paired_try_id", "")
            try_state_key = f"{try_id}_try_state"
            try_state = context.variables.get(try_state_key, {})

            if not try_state.get("error"):
                # No error - skip catch body (shouldn't normally happen)
                logger.debug("Catch node reached but no error in try state - skipping")
                self.status = NodeStatus.SKIPPED

                return {
                    "success": True,
                    "data": {},
                    "next_nodes": [],  # Skip catch body
                }

            # Check error type filter
            error_types_str = self.get_parameter("error_types", "")
            if error_types_str:
                allowed_types = [
                    t.strip() for t in error_types_str.split(",") if t.strip()
                ]
                error_type = try_state.get("error_type", "")
                if allowed_types and error_type not in allowed_types:
                    # Error type not in filter - re-raise
                    logger.info(
                        f"Catch filter {allowed_types} doesn't match {error_type} - re-raising"
                    )
                    return {
                        "success": False,
                        "error": try_state.get("error_message", "Unhandled error"),
                        "next_nodes": [],
                    }

            # Set output values for error handling
            self.set_output_value("error_message", try_state.get("error_message", ""))
            self.set_output_value("error_type", try_state.get("error_type", ""))
            self.set_output_value("stack_trace", try_state.get("stack_trace", ""))

            logger.info(f"Catch block handling error: {try_state.get('error_type')}")
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {
                    "error_message": try_state.get("error_message", ""),
                    "error_type": try_state.get("error_type", ""),
                },
                "next_nodes": ["catch_body"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Catch execution failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}


@executable_node
class FinallyNode(BaseNode):
    """
    Finally block - always executes after Try/Catch regardless of errors.

    Cleans up try state and provides a guaranteed execution path for cleanup code.
    Paired automatically with Try and Catch nodes when created together.

    Outputs:
        - finally_body: Execution flow for cleanup code
        - had_error: Boolean indicating if an error occurred in try block
    """

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize Finally node."""
        super().__init__(node_id, config)
        self.name = "Finally"
        self.node_type = "FinallyNode"
        # Paired automatically when created together
        self.paired_try_id: str = ""

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("finally_body", PortType.EXEC_OUTPUT)
        self.add_output_port("had_error", PortType.OUTPUT, DataType.BOOLEAN)

    def set_paired_try(self, try_node_id: str) -> None:
        """Set the paired Try node ID (called automatically)."""
        self.paired_try_id = try_node_id

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute finally - always runs, cleans up try state."""
        self.status = NodeStatus.RUNNING

        try:
            try_id = self.paired_try_id or self.get_parameter("paired_try_id", "")
            try_state_key = f"{try_id}_try_state"
            try_state = context.variables.get(try_state_key, {})

            had_error = try_state.get("error", False)

            # Clean up try state
            if try_state_key in context.variables:
                del context.variables[try_state_key]

            # Set output
            self.set_output_value("had_error", had_error)

            logger.info(f"Finally block executing (had_error={had_error})")
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"had_error": had_error},
                "next_nodes": ["finally_body"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Finally execution failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}
