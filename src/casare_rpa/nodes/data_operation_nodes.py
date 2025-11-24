"""
Data operation nodes for CasareRPA.

This module provides nodes for string manipulation, regex operations,
math operations, list handling, and JSON processing.
"""

from typing import Any, Dict, List, Optional, Union
import re
import orjson
import math
import random
from loguru import logger

from casare_rpa.core.base_node import BaseNode
from casare_rpa.core.types import PortType, DataType, NodeStatus, ExecutionResult


class ConcatenateNode(BaseNode):
    """Node that concatenates multiple strings."""

    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        # Configurable separator
        self.separator = self.config.get("separator", "")
        self.name = "Concatenate"
        self.node_type = "ConcatenateNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("string_1", PortType.INPUT, DataType.STRING)
        self.add_input_port("string_2", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("result", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context) -> ExecutionResult:
        self.status = NodeStatus.RUNNING
        try:
            s1 = str(self.get_input_value("string_1") or "")
            s2 = str(self.get_input_value("string_2") or "")

            result = f"{s1}{self.separator}{s2}"

            self.set_output_value("result", result)
            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"result": result},
                "next_nodes": ["exec_out"]
            }
        except Exception as e:
            logger.error(f"Concatenate failed: {e}")
            self.status = NodeStatus.ERROR
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }


class FormatStringNode(BaseNode):
    """Node that formats a string using python's format() method."""

    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        self.name = "Format String"
        self.node_type = "FormatStringNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("template", PortType.INPUT, DataType.STRING)
        self.add_input_port("variables", PortType.INPUT, DataType.DICT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("result", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context) -> ExecutionResult:
        self.status = NodeStatus.RUNNING
        try:
            template = self.get_input_value("template") or ""
            variables = self.get_input_value("variables") or {}

            if not isinstance(variables, dict):
                raise ValueError("Variables input must be a dictionary")

            result = template.format(**variables)

            self.set_output_value("result", result)
            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"result": result},
                "next_nodes": ["exec_out"]
            }
        except Exception as e:
            logger.error(f"Format string failed: {e}")
            self.status = NodeStatus.ERROR
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }


class RegexMatchNode(BaseNode):
    """Node that searches for a regex pattern in a string."""

    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        self.name = "Regex Match"
        self.node_type = "RegexMatchNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("text", PortType.INPUT, DataType.STRING)
        self.add_input_port("pattern", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("match_found", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("first_match", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("all_matches", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("groups", PortType.OUTPUT, DataType.LIST)

    async def execute(self, context) -> ExecutionResult:
        self.status = NodeStatus.RUNNING
        try:
            text = self.get_input_value("text") or ""
            pattern = self.get_input_value("pattern") or ""

            matches = list(re.finditer(pattern, text))

            match_found = len(matches) > 0
            first_match = matches[0].group(0) if match_found else ""
            all_matches = [m.group(0) for m in matches]

            # Collect groups from the first match if available
            groups = list(matches[0].groups()) if match_found else []

            self.set_output_value("match_found", match_found)
            self.set_output_value("first_match", first_match)
            self.set_output_value("all_matches", all_matches)
            self.set_output_value("groups", groups)

            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {
                    "match_found": match_found,
                    "first_match": first_match,
                    "all_matches": all_matches,
                    "groups": groups
                },
                "next_nodes": ["exec_out"]
            }
        except Exception as e:
            logger.error(f"Regex match failed: {e}")
            self.status = NodeStatus.ERROR
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }


class RegexReplaceNode(BaseNode):
    """Node that replaces text using regex."""

    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        self.name = "Regex Replace"
        self.node_type = "RegexReplaceNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("text", PortType.INPUT, DataType.STRING)
        self.add_input_port("pattern", PortType.INPUT, DataType.STRING)
        self.add_input_port("replacement", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("result", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("count", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context) -> ExecutionResult:
        self.status = NodeStatus.RUNNING
        try:
            text = self.get_input_value("text") or ""
            pattern = self.get_input_value("pattern") or ""
            replacement = self.get_input_value("replacement") or ""

            result, count = re.subn(pattern, replacement, text)

            self.set_output_value("result", result)
            self.set_output_value("count", count)
            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"result": result, "count": count},
                "next_nodes": ["exec_out"]
            }
        except Exception as e:
            logger.error(f"Regex replace failed: {e}")
            self.status = NodeStatus.ERROR
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }


class MathOperationNode(BaseNode):
    """Node that performs basic math operations."""

    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        # Operation: add, subtract, multiply, divide, power, modulo
        self.operation = self.config.get("operation", "add")
        self.name = "Math Operation"
        self.node_type = "MathOperationNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("a", PortType.INPUT, DataType.FLOAT)
        self.add_input_port("b", PortType.INPUT, DataType.FLOAT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("result", PortType.OUTPUT, DataType.FLOAT)

    async def execute(self, context) -> ExecutionResult:
        self.status = NodeStatus.RUNNING
        try:
            a = float(self.get_input_value("a") or 0)
            b = float(self.get_input_value("b") or 0)

            result = 0.0
            op = self.operation.lower()

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
            elif op == "power":
                result = math.pow(a, b)
            elif op == "modulo":
                result = a % b
            else:
                raise ValueError(f"Unknown operation: {op}")

            self.set_output_value("result", result)
            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"result": result, "operation": op},
                "next_nodes": ["exec_out"]
            }
        except Exception as e:
            logger.error(f"Math operation failed: {e}")
            self.status = NodeStatus.ERROR
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }


class ComparisonNode(BaseNode):
    """Node that compares two values.

    Supports operators: ==, !=, >, <, >=, <=, and, or, in, not in, is, is not
    """

    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        # Operator from dropdown or custom_operator text field
        self.operator = self.config.get("operator", "==")
        # Allow custom operator to override dropdown
        custom_op = self.config.get("custom_operator", "").strip()
        if custom_op:
            self.operator = custom_op
        self.name = "Comparison"
        self.node_type = "ComparisonNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("a", PortType.INPUT, DataType.ANY)
        self.add_input_port("b", PortType.INPUT, DataType.ANY)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("result", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context) -> ExecutionResult:
        self.status = NodeStatus.RUNNING
        try:
            a = self.get_input_value("a")
            b = self.get_input_value("b")

            result = False
            op = self.operator

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
            elif op == "and":
                result = bool(a) and bool(b)
            elif op == "or":
                result = bool(a) or bool(b)
            elif op == "in":
                result = a in b
            elif op == "not in":
                result = a not in b
            elif op == "is":
                result = a is b
            elif op == "is not":
                result = a is not b
            else:
                raise ValueError(f"Unknown operator: {op}")

            self.set_output_value("result", result)
            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"result": result, "operator": op},
                "next_nodes": ["exec_out"]
            }
        except Exception as e:
            logger.error(f"Comparison failed: {e}")
            self.status = NodeStatus.ERROR
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }


class CreateListNode(BaseNode):
    """Node that creates a list from inputs."""

    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        self.name = "Create List"
        self.node_type = "CreateListNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("item_1", PortType.INPUT, DataType.ANY)
        self.add_input_port("item_2", PortType.INPUT, DataType.ANY)
        self.add_input_port("item_3", PortType.INPUT, DataType.ANY)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("list", PortType.OUTPUT, DataType.LIST)

    async def execute(self, context) -> ExecutionResult:
        self.status = NodeStatus.RUNNING
        try:
            result = []

            for i in range(1, 4):
                key = f"item_{i}"
                val = self.get_input_value(key)
                if val is not None:
                    result.append(val)

            self.set_output_value("list", result)
            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"list": result, "count": len(result)},
                "next_nodes": ["exec_out"]
            }
        except Exception as e:
            logger.error(f"Create list failed: {e}")
            self.status = NodeStatus.ERROR
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }


class ListGetItemNode(BaseNode):
    """Node that gets an item from a list by index."""

    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        self.name = "List Get Item"
        self.node_type = "ListGetItemNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("list", PortType.INPUT, DataType.LIST)
        self.add_input_port("index", PortType.INPUT, DataType.INTEGER)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("item", PortType.OUTPUT, DataType.ANY)

    async def execute(self, context) -> ExecutionResult:
        self.status = NodeStatus.RUNNING
        try:
            lst = self.get_input_value("list") or []
            idx = int(self.get_input_value("index") or 0)

            if not isinstance(lst, (list, tuple)):
                raise ValueError("Input is not a list")

            if idx < 0:
                idx += len(lst)

            if idx < 0 or idx >= len(lst):
                raise IndexError(f"List index out of range: {idx}")

            item = lst[idx]
            self.set_output_value("item", item)
            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"item": item, "index": idx},
                "next_nodes": ["exec_out"]
            }
        except Exception as e:
            logger.error(f"List get item failed: {e}")
            self.status = NodeStatus.ERROR
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }


class JsonParseNode(BaseNode):
    """Node that parses a JSON string."""

    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        self.name = "JSON Parse"
        self.node_type = "JsonParseNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("json_string", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("data", PortType.OUTPUT, DataType.ANY)

    async def execute(self, context) -> ExecutionResult:
        self.status = NodeStatus.RUNNING
        try:
            json_str = self.get_input_value("json_string") or ""
            if not json_str:
                raise ValueError("Empty JSON string")

            data = orjson.loads(json_str)
            self.set_output_value("data", data)
            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"parsed_data": data},
                "next_nodes": ["exec_out"]
            }
        except Exception as e:
            logger.error(f"JSON parse failed: {e}")
            self.status = NodeStatus.ERROR
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }


class GetPropertyNode(BaseNode):
    """Node that gets a property from a dictionary/object."""

    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        self.name = "Get Property"
        self.node_type = "GetPropertyNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("object", PortType.INPUT, DataType.DICT)
        self.add_input_port("property_path", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("value", PortType.OUTPUT, DataType.ANY)

    async def execute(self, context) -> ExecutionResult:
        self.status = NodeStatus.RUNNING
        try:
            obj = self.get_input_value("object") or {}
            path = self.get_input_value("property_path") or ""

            if not isinstance(obj, dict):
                raise ValueError("Input is not a dictionary")

            current = obj
            for part in path.split('.'):
                if not part:
                    continue
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    # Property not found - return None
                    current = None
                    break

            self.set_output_value("value", current)
            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"value": current, "path": path},
                "next_nodes": ["exec_out"]
            }
        except Exception as e:
            logger.error(f"Get property failed: {e}")
            self.status = NodeStatus.ERROR
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }
