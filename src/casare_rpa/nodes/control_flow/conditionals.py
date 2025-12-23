"""
CasareRPA - Conditional Control Flow Nodes

Provides nodes for conditional branching:
- IfNode: Binary condition branching (true/false)
- SwitchNode: Multi-way branching based on value matching
- MergeNode: Convergence point for multiple execution paths
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
        "expression",
        PropertyType.STRING,
        default="",
        label="Expression",
        tooltip="Boolean expression to evaluate (optional if using input port)",
        placeholder="{{variable}} > 10",
    ),
)
@node(category="control_flow", exec_outputs=["true", "false"])
class IfNode(BaseNode):
    """
    Conditional node that executes different paths based on condition.

    Evaluates a condition and routes execution to either 'true' or 'false' output.
    Supports boolean inputs or expression evaluation.
    """

    # @category: control_flow
    # @requires: none
    # @ports: exec_in, condition -> true, false

    def __init__(self, node_id: str, config: dict | None = None) -> None:
        """Initialize If node."""
        super().__init__(node_id, config)
        self.name = "If"
        self.node_type = "IfNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        # Note: exec_in/exec_out are added by @node decorator
        self.add_input_port("condition", DataType.ANY, required=False)
        self.add_exec_output("true")
        self.add_exec_output("false")

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
                        # Convert {{variable}} syntax to plain variable names
                        # e.g., "{{x}} > 5" -> "x > 5"
                        resolved_expr = re.sub(r"\{\{(\w+)\}\}", r"\1", expression)

                        if not is_safe_expression(resolved_expr):
                            raise ValueError(f"Unsafe expression detected: {resolved_expr}")
                        condition = safe_eval(resolved_expr, context.variables)
                    except Exception as e:
                        logger.warning(f"Failed to evaluate expression '{expression}': {e}")
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


@properties(
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
@node(category="control_flow", exec_outputs=["exec_out", "default"])
class SwitchNode(BaseNode):
    """
    Multi-way branching node based on value matching.

    Evaluates an input value and routes to matching case output.
    Falls back to 'default' if no case matches.
    """

    # @category: control_flow
    # @requires: none
    # @ports: exec_in, value -> default

    def __init__(self, node_id: str, config: dict | None = None) -> None:
        """Initialize Switch node."""
        super().__init__(node_id, config)
        self.name = "Switch"
        self.node_type = "SwitchNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        # Note: exec_in/exec_out are added by @node decorator
        self.add_input_port("value", DataType.ANY, required=False)

        # Get cases from config (e.g., ["success", "error", "pending"])
        cases = self.get_parameter("cases", [])
        for case in cases:
            self.add_exec_output(f"case_{case}")

        self.add_exec_output("default")

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
                    # Convert {{variable}} syntax to plain variable names
                    resolved_expr = re.sub(r"\{\{(\w+)\}\}", r"\1", expression)
                    # Safely evaluate expression with context variables
                    if not is_safe_expression(resolved_expr):
                        raise ValueError(f"Unsafe expression detected: {resolved_expr}")
                    value = safe_eval(resolved_expr, context.variables)

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


@properties()  # Pass-through node
@node(category="control_flow")
class MergeNode(BaseNode):
    """
    Merge node that allows multiple execution paths to converge.

    This is a pass-through node that accepts multiple incoming exec connections
    and continues to a single output. Use this to join branches from If/Switch
    nodes back into a single execution path.

    Example:
        If --+-- TRUE ----------+---> Merge ---> NextNode
             +-- FALSE -> ... --+
    """

    # @category: control_flow
    # @requires: none
    # @ports: none -> none

    def __init__(self, node_id: str, config: dict | None = None) -> None:
        """Initialize Merge node."""
        super().__init__(node_id, config)
        self.name = "Merge"
        self.node_type = "MergeNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        # exec_in and exec_out added by @node decorator
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


__all__ = [
    "IfNode",
    "SwitchNode",
    "MergeNode",
]
