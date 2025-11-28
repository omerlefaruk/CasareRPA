"""
CasareRPA - Math Operation Nodes

Provides nodes for mathematical operations including:
- Arithmetic operations (add, subtract, multiply, divide, etc.)
- Trigonometric functions
- Comparison operations
"""

from typing import Any, Dict, Optional
import math
from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import DataType, ExecutionResult
from casare_rpa.infrastructure.execution import ExecutionContext


class MathOperationNode(BaseNode):
    """Node that performs math operations."""

    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        default_config = {
            "operation": "add",
            "round_digits": None,
        }
        if config is None:
            config = {}
        for key, value in default_config.items():
            if key not in config:
                config[key] = value
        super().__init__(node_id, config)
        self.operation = self.config.get("operation", "add")

    def _define_ports(self) -> None:
        self.add_input_port("a", DataType.FLOAT)
        self.add_input_port("b", DataType.FLOAT)
        self.add_output_port("result", DataType.FLOAT)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            a = float(self.get_input_value("a", 0))
            b = float(self.get_input_value("b", 0))

            result = 0.0
            op = self.operation.lower()

            # Two-operand operations
            if op == "add":
                result = a + b
            elif op == "subtract":
                result = a - b
            elif op == "multiply":
                result = a * b
            elif op == "divide":
                if b == 0:
                    raise ValueError("Division by zero")
                result = a / b
            elif op == "floor_divide":
                if b == 0:
                    raise ValueError("Division by zero")
                result = a // b
            elif op == "power":
                result = math.pow(a, b)
            elif op == "modulo":
                result = a % b
            elif op == "min":
                result = min(a, b)
            elif op == "max":
                result = max(a, b)
            # Single-operand operations (use 'a' only)
            elif op == "abs":
                result = abs(a)
            elif op == "sqrt":
                result = math.sqrt(a)
            elif op == "floor":
                result = math.floor(a)
            elif op == "ceil":
                result = math.ceil(a)
            elif op == "round":
                result = round(a)
            elif op == "sin":
                result = math.sin(a)
            elif op == "cos":
                result = math.cos(a)
            elif op == "tan":
                result = math.tan(a)
            elif op == "log":
                result = math.log(a) if b == 0 else math.log(a, b)
            elif op == "log10":
                result = math.log10(a)
            elif op == "exp":
                result = math.exp(a)
            elif op == "negate":
                result = -a
            else:
                raise ValueError(f"Unknown operation: {op}")

            # Apply rounding if configured
            round_digits = self.config.get("round_digits")
            if round_digits is not None:
                result = round(result, int(round_digits))

            self.set_output_value("result", result)
            return {"success": True, "data": {"result": result}, "next_nodes": []}
        except Exception as e:
            logger.error(f"Math operation failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


class ComparisonNode(BaseNode):
    """Node that compares two values."""

    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        self.operator = self.config.get("operator", "==")

    def _define_ports(self) -> None:
        self.add_input_port("a", DataType.ANY)
        self.add_input_port("b", DataType.ANY)
        self.add_output_port("result", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            a = self.get_input_value("a")
            b = self.get_input_value("b")

            result = False
            op = self.operator

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
            op = op_map.get(op, op)

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
