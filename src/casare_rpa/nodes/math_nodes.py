"""
CasareRPA - Math Operation Nodes

Provides nodes for mathematical operations including:
- Arithmetic operations (add, subtract, multiply, divide, etc.)
- Trigonometric functions
- Comparison operations
"""

import math
from loguru import logger

from typing import Any, Union
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType, ExecutionResult
from casare_rpa.infrastructure.execution import ExecutionContext


def _strip_var_wrapper(value: str) -> str:
    """Strip {{}} wrapper from variable reference if present."""
    value = value.strip()
    if value.startswith("{{") and value.endswith("}}"):
        return value[2:-2].strip()
    return value


def _resolve_numeric_param(
    node: BaseNode, context: ExecutionContext, param_name: str, default: float = 0
) -> float:
    """Resolve a numeric parameter from input port, parameter, or variable reference."""
    # Try input port first
    value = node.get_input_value(param_name)
    if value is not None:
        return float(value)

    # Try parameter
    param = node.get_parameter(param_name, default)

    # If it's a string, try to resolve as variable reference
    if isinstance(param, str):
        var_name = _strip_var_wrapper(param)
        resolved = context.get_variable(var_name)
        if resolved is not None:
            return float(resolved)
        # Try parsing as literal number
        try:
            return float(param)
        except ValueError:
            return default

    return float(param) if param is not None else default


@node_schema(
    PropertyDef(
        "operation",
        PropertyType.CHOICE,
        default="add",
        choices=[
            "add",
            "subtract",
            "multiply",
            "divide",
            "floor_divide",
            "power",
            "modulo",
            "min",
            "max",
            "abs",
            "sqrt",
            "floor",
            "ceil",
            "round",
            "sin",
            "cos",
            "tan",
            "log",
            "log10",
            "exp",
            "negate",
        ],
        label="Operation",
        tooltip="Mathematical operation to perform",
    ),
    PropertyDef(
        "round_digits",
        PropertyType.INTEGER,
        default=None,
        min_value=0,
        label="Round Digits",
        tooltip="Number of decimal places to round result (optional)",
    ),
)
@executable_node
class MathOperationNode(BaseNode):
    """Node that performs math operations."""

    def __init__(self, node_id: str, name: str = "Math Operation", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "MathOperationNode"

    def _define_ports(self) -> None:
        self.add_input_port("a", DataType.FLOAT)
        self.add_input_port("b", DataType.FLOAT)
        self.add_output_port("result", DataType.FLOAT)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            a = _resolve_numeric_param(self, context, "a", 0)
            b = _resolve_numeric_param(self, context, "b", 0)
            operation = self.get_parameter("operation", "add").lower()
            output_var = self.get_parameter("output_var")

            result = 0.0

            # Two-operand operations
            if operation == "add":
                result = a + b
            elif operation == "subtract":
                result = a - b
            elif operation == "multiply":
                result = a * b
            elif operation == "divide":
                if b == 0:
                    raise ValueError("Division by zero")
                result = a / b
            elif operation == "floor_divide":
                if b == 0:
                    raise ValueError("Division by zero")
                result = a // b
            elif operation == "power":
                result = math.pow(a, b)
            elif operation == "modulo":
                result = a % b
            elif operation == "min":
                result = min(a, b)
            elif operation == "max":
                result = max(a, b)
            # Single-operand operations (use 'a' only)
            elif operation == "abs":
                result = abs(a)
            elif operation == "sqrt":
                result = math.sqrt(a)
            elif operation == "floor":
                result = math.floor(a)
            elif operation == "ceil":
                result = math.ceil(a)
            elif operation == "round":
                result = round(a)
            elif operation == "sin":
                result = math.sin(a)
            elif operation == "cos":
                result = math.cos(a)
            elif operation == "tan":
                result = math.tan(a)
            elif operation == "log":
                result = math.log(a) if b == 0 else math.log(a, b)
            elif operation == "log10":
                result = math.log10(a)
            elif operation == "exp":
                result = math.exp(a)
            elif operation == "negate":
                result = -a
            else:
                raise ValueError(f"Unknown operation: {operation}")

            # Apply rounding if configured
            round_digits = self.get_parameter("round_digits")
            if round_digits is not None:
                result = round(result, int(round_digits))

            # Store in context if output_var specified
            if output_var:
                context.set_variable(output_var, result)
                logger.info(f"Math result stored in '{output_var}' = {result}")

            self.set_output_value("result", result)
            return {"success": True, "data": {"result": result}, "next_nodes": []}
        except Exception as e:
            logger.error(f"Math operation failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


@node_schema(
    PropertyDef(
        "operator",
        PropertyType.CHOICE,
        default="==",
        choices=[
            "==",
            "equals (==)",
            "!=",
            "not equals (!=)",
            ">",
            "greater than (>)",
            "<",
            "less than (<)",
            ">=",
            "greater or equal (>=)",
            "<=",
            "less or equal (<=)",
        ],
        label="Operator",
        tooltip="Comparison operator to use",
    ),
)
@executable_node
class ComparisonNode(BaseNode):
    """Node that compares two values."""

    def __init__(self, node_id: str, name: str = "Comparison", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ComparisonNode"

    def _define_ports(self) -> None:
        self.add_input_port("a", DataType.ANY)
        self.add_input_port("b", DataType.ANY)
        self.add_output_port("result", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            a = self.get_parameter("a")
            b = self.get_parameter("b")
            operator = self.get_parameter("operator", "==")

            result = False

            # Handle both symbol and descriptive formats
            op_map = {
                "==": "==",
                "equals (==)": "==",
                "!=": "!=",
                "not equals (!=)": "!=",
                ">": ">",
                "greater than (>)": ">",
                "<": "<",
                "less than (<)": "<",
                ">=": ">=",
                "greater or equal (>=)": ">=",
                "<=": "<=",
                "less or equal (<=)": "<=",
            }
            op = op_map.get(operator, operator)

            if op == "==":
                result = a == b
            elif op == "!=":
                result = a != b
            elif op == ">":
                result = a > b
            elif op == "<":
                result = a < b
            elif op == ">=":
                result = a >= b
            elif op == "<=":
                result = a <= b
            else:
                raise ValueError(f"Unknown operator: {op}")

            self.set_output_value("result", result)
            return {"success": True, "data": {"result": result}, "next_nodes": []}
        except Exception as e:
            logger.error(f"Comparison failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


__all__ = [
    "MathOperationNode",
    "ComparisonNode",
]
