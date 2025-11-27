from typing import Any, Dict, List, Optional, Union
import re
import json
import math
import random
from loguru import logger

from ..core.base_node import BaseNode
from ..core.types import PortType, DataType, NodeStatus, ExecutionResult
from ..core.execution_context import ExecutionContext

class ConcatenateNode(BaseNode):
    """Node that concatenates multiple strings."""

    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        # Configurable separator
        self.separator = self.config.get("separator", "")

    def _define_ports(self) -> None:
        self.add_input_port("string_1", DataType.STRING)
        self.add_input_port("string_2", DataType.STRING)
        self.add_output_port("result", DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            # Get inputs (support dynamic number of inputs in future, for now just 2 fixed + optional extras from config if we were to expand)
            # Actually, let's stick to the ports defined.
            s1 = str(self.get_input_value("string_1", ""))
            s2 = str(self.get_input_value("string_2", ""))

            result = f"{s1}{self.separator}{s2}"

            self.set_output_value("result", result)
            return {"success": True, "data": {"result": result}, "next_nodes": []}
        except Exception as e:
            logger.error(f"Concatenate failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}

class FormatStringNode(BaseNode):
    """Node that formats a string using python's format() method."""

    def _define_ports(self) -> None:
        self.add_input_port("template", DataType.STRING)
        self.add_input_port("variables", DataType.DICT) # Dict of variables to format with
        self.add_output_port("result", DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            template = self.get_input_value("template", "")
            variables = self.get_input_value("variables", {})

            if not isinstance(variables, dict):
                raise ValueError("Variables input must be a dictionary")

            result = template.format(**variables)

            self.set_output_value("result", result)
            return {"success": True, "data": {"result": result}, "next_nodes": []}
        except Exception as e:
            logger.error(f"Format string failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}

class RegexMatchNode(BaseNode):
    """Node that searches for a regex pattern in a string."""

    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        default_config = {
            "ignore_case": False,  # Case insensitive matching
            "multiline": False,  # ^ and $ match line boundaries
            "dotall": False,  # . matches newlines
        }
        if config is None:
            config = {}
        for key, value in default_config.items():
            if key not in config:
                config[key] = value
        super().__init__(node_id, config)

    def _define_ports(self) -> None:
        self.add_input_port("text", DataType.STRING)
        self.add_input_port("pattern", DataType.STRING)
        self.add_output_port("match_found", DataType.BOOLEAN)
        self.add_output_port("first_match", DataType.STRING)
        self.add_output_port("all_matches", DataType.LIST)
        self.add_output_port("groups", DataType.LIST)
        self.add_output_port("match_count", DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            text = self.get_input_value("text", "")
            pattern = self.get_input_value("pattern", "")

            # Build regex flags
            flags = 0
            if self.config.get("ignore_case", False):
                flags |= re.IGNORECASE
            if self.config.get("multiline", False):
                flags |= re.MULTILINE
            if self.config.get("dotall", False):
                flags |= re.DOTALL

            matches = list(re.finditer(pattern, text, flags=flags))

            match_found = len(matches) > 0
            first_match = matches[0].group(0) if match_found else ""
            all_matches = [m.group(0) for m in matches]

            # Collect groups from the first match if available
            groups = list(matches[0].groups()) if match_found else []

            self.set_output_value("match_found", match_found)
            self.set_output_value("first_match", first_match)
            self.set_output_value("all_matches", all_matches)
            self.set_output_value("groups", groups)
            self.set_output_value("match_count", len(matches))

            return {"success": True, "data": {"match_found": match_found, "first_match": first_match, "all_matches": all_matches, "groups": groups, "match_count": len(matches)}, "next_nodes": []}
        except Exception as e:
            logger.error(f"Regex match failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}

class RegexReplaceNode(BaseNode):
    """Node that replaces text using regex."""

    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        default_config = {
            "ignore_case": False,  # Case insensitive matching
            "multiline": False,  # ^ and $ match line boundaries
            "dotall": False,  # . matches newlines
            "max_count": 0,  # Max replacements (0 = unlimited)
        }
        if config is None:
            config = {}
        for key, value in default_config.items():
            if key not in config:
                config[key] = value
        super().__init__(node_id, config)

    def _define_ports(self) -> None:
        self.add_input_port("text", DataType.STRING)
        self.add_input_port("pattern", DataType.STRING)
        self.add_input_port("replacement", DataType.STRING)
        self.add_output_port("result", DataType.STRING)
        self.add_output_port("count", DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            text = self.get_input_value("text", "")
            pattern = self.get_input_value("pattern", "")
            replacement = self.get_input_value("replacement", "")

            # Build regex flags
            flags = 0
            if self.config.get("ignore_case", False):
                flags |= re.IGNORECASE
            if self.config.get("multiline", False):
                flags |= re.MULTILINE
            if self.config.get("dotall", False):
                flags |= re.DOTALL

            max_count = int(self.config.get("max_count", 0))
            if max_count > 0:
                result, count = re.subn(pattern, replacement, text, count=max_count, flags=flags)
            else:
                result, count = re.subn(pattern, replacement, text, flags=flags)

            self.set_output_value("result", result)
            self.set_output_value("count", count)
            return {"success": True, "data": {"result": result, "count": count}, "next_nodes": []}
        except Exception as e:
            logger.error(f"Regex replace failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}

class MathOperationNode(BaseNode):
    """Node that performs math operations."""

    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        default_config = {
            "operation": "add",  # Operation to perform
            "round_digits": None,  # Decimal places to round to (None = no rounding)
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
        # Operator: ==, !=, >, <, >=, <=
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
            # e.g., "==" or "equals (==)"
            op_map = {
                "==": "==", "equals (==)": "==",
                "!=": "!=", "not equals (!=)": "!=",
                ">": ">", "greater than (>)": ">",
                "<": "<", "less than (<)": "<",
                ">=": ">=", "greater or equal (>=)": ">=",
                "<=": "<=", "less or equal (<=)": "<=",
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

class CreateListNode(BaseNode):
    """Node that creates a list from inputs."""

    def _define_ports(self) -> None:
        # Dynamic inputs would be better, but for now let's support up to 5 items
        # or take a single input that is already a list/tuple to convert
        self.add_input_port("item_1", DataType.ANY)
        self.add_input_port("item_2", DataType.ANY)
        self.add_input_port("item_3", DataType.ANY)
        self.add_output_port("list", DataType.LIST)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            result = []
            # Check for connected inputs
            # In a real implementation, we might check which ports are actually connected
            # For now, we'll just take non-None values or values that were explicitly set

            # Note: get_input_value returns None if not set and no default provided.
            # But we might want to allow None in the list.
            # A better way is to check if the port has a connection or value.
            # BaseNode doesn't expose 'is_connected' easily without checking the graph,
            # but we can check if the value is in self.inputs

            for i in range(1, 4):
                key = f"item_{i}"
                val = self.get_input_value(key)
                if val is not None:
                    result.append(val)

            self.set_output_value("list", result)
            return {"success": True, "data": {"list": result}, "next_nodes": []}
        except Exception as e:
            logger.error(f"Create list failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}

class ListGetItemNode(BaseNode):
    """Node that gets an item from a list by index."""

    def _define_ports(self) -> None:
        self.add_input_port("list", DataType.LIST)
        self.add_input_port("index", DataType.INTEGER)
        self.add_output_port("item", DataType.ANY)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            lst = self.get_input_value("list", [])
            idx = int(self.get_input_value("index", 0))

            if not isinstance(lst, (list, tuple)):
                raise ValueError("Input is not a list")

            if idx < 0:
                idx += len(lst)

            if idx < 0 or idx >= len(lst):
                raise IndexError(f"List index out of range: {idx}")

            item = lst[idx]
            self.set_output_value("item", item)
            return {"success": True, "data": {"item": item}, "next_nodes": []}
        except Exception as e:
            logger.error(f"List get item failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}

class JsonParseNode(BaseNode):
    """Node that parses a JSON string."""

    def _define_ports(self) -> None:
        self.add_input_port("json_string", DataType.STRING)
        self.add_output_port("data", DataType.ANY)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            json_str = self.get_input_value("json_string", "")
            if not json_str:
                raise ValueError("Empty JSON string")

            data = json.loads(json_str)
            self.set_output_value("data", data)
            return {"success": True, "data": {"data": data}, "next_nodes": []}
        except Exception as e:
            logger.error(f"JSON parse failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}

class GetPropertyNode(BaseNode):
    """Node that gets a property from a dictionary/object."""

    def _define_ports(self) -> None:
        self.add_input_port("object", DataType.DICT)
        self.add_input_port("property_path", DataType.STRING) # dot notation supported e.g. "user.address.city"
        self.add_output_port("value", DataType.ANY)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            obj = self.get_input_value("object", {})
            path = self.get_input_value("property_path", "")

            if not isinstance(obj, dict):
                raise ValueError("Input is not a dictionary")

            current = obj
            for part in path.split('.'):
                if not part:
                    continue
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    # Property not found
                    # We could return None or raise error. Let's return None for now.
                    current = None
                    break

            self.set_output_value("value", current)
            return {"success": True, "data": {"value": current}, "next_nodes": []}
        except Exception as e:
            logger.error(f"Get property failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


# ==================== LIST OPERATIONS ====================

class ListLengthNode(BaseNode):
    """Node that returns the length of a list."""

    def _define_ports(self) -> None:
        self.add_input_port("list", DataType.LIST)
        self.add_output_port("length", DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            lst = self.get_input_value("list", [])
            if not isinstance(lst, (list, tuple)):
                raise ValueError("Input is not a list")

            length = len(lst)
            self.set_output_value("length", length)
            return {"success": True, "data": {"length": length}, "next_nodes": []}
        except Exception as e:
            logger.error(f"List length failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


class ListAppendNode(BaseNode):
    """Node that appends an item to a list."""

    def _define_ports(self) -> None:
        self.add_input_port("list", DataType.LIST)
        self.add_input_port("item", DataType.ANY)
        self.add_output_port("result", DataType.LIST)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            lst = self.get_input_value("list", [])
            item = self.get_input_value("item")

            if not isinstance(lst, list):
                lst = list(lst) if isinstance(lst, tuple) else [lst]

            result = lst.copy()
            result.append(item)

            self.set_output_value("result", result)
            return {"success": True, "data": {"result": result}, "next_nodes": []}
        except Exception as e:
            logger.error(f"List append failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


class ListContainsNode(BaseNode):
    """Node that checks if a list contains an item."""

    def _define_ports(self) -> None:
        self.add_input_port("list", DataType.LIST)
        self.add_input_port("item", DataType.ANY)
        self.add_output_port("contains", DataType.BOOLEAN)
        self.add_output_port("index", DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            lst = self.get_input_value("list", [])
            item = self.get_input_value("item")

            if not isinstance(lst, (list, tuple)):
                raise ValueError("Input is not a list")

            contains = item in lst
            index = lst.index(item) if contains else -1

            self.set_output_value("contains", contains)
            self.set_output_value("index", index)
            return {"success": True, "data": {"contains": contains, "index": index}, "next_nodes": []}
        except Exception as e:
            logger.error(f"List contains failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


class ListSliceNode(BaseNode):
    """Node that gets a slice of a list."""

    def _define_ports(self) -> None:
        self.add_input_port("list", DataType.LIST)
        self.add_input_port("start", DataType.INTEGER)
        self.add_input_port("end", DataType.INTEGER)
        self.add_output_port("result", DataType.LIST)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            lst = self.get_input_value("list", [])
            start = self.get_input_value("start", 0)
            end = self.get_input_value("end")

            if not isinstance(lst, (list, tuple)):
                raise ValueError("Input is not a list")

            start = int(start) if start is not None else None
            end = int(end) if end is not None else None

            result = list(lst[start:end])

            self.set_output_value("result", result)
            return {"success": True, "data": {"result": result}, "next_nodes": []}
        except Exception as e:
            logger.error(f"List slice failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


class ListJoinNode(BaseNode):
    """Node that joins a list into a string."""

    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        self.separator = self.config.get("separator", ", ")

    def _define_ports(self) -> None:
        self.add_input_port("list", DataType.LIST)
        self.add_input_port("separator", DataType.STRING)
        self.add_output_port("result", DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            lst = self.get_input_value("list", [])
            separator = self.get_input_value("separator", self.separator)

            if not isinstance(lst, (list, tuple)):
                raise ValueError("Input is not a list")

            result = separator.join(str(item) for item in lst)

            self.set_output_value("result", result)
            return {"success": True, "data": {"result": result}, "next_nodes": []}
        except Exception as e:
            logger.error(f"List join failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


class ListSortNode(BaseNode):
    """Node that sorts a list."""

    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        self.reverse = self.config.get("reverse", False)
        self.key_path = self.config.get("key_path", "")

    def _define_ports(self) -> None:
        self.add_input_port("list", DataType.LIST)
        self.add_input_port("reverse", DataType.BOOLEAN)
        self.add_input_port("key_path", DataType.STRING)
        self.add_output_port("result", DataType.LIST)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            lst = self.get_input_value("list", [])
            reverse = self.get_input_value("reverse", self.reverse)
            key_path = self.get_input_value("key_path", self.key_path)

            if not isinstance(lst, (list, tuple)):
                raise ValueError("Input is not a list")

            result = list(lst)

            if key_path:
                # Sort by nested key (e.g., "name" or "user.age")
                def get_key(item):
                    current = item
                    for part in key_path.split('.'):
                        if isinstance(current, dict) and part in current:
                            current = current[part]
                        else:
                            return None
                    return current
                result.sort(key=get_key, reverse=bool(reverse))
            else:
                result.sort(reverse=bool(reverse))

            self.set_output_value("result", result)
            return {"success": True, "data": {"result": result}, "next_nodes": []}
        except Exception as e:
            logger.error(f"List sort failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


class ListReverseNode(BaseNode):
    """Node that reverses a list."""

    def _define_ports(self) -> None:
        self.add_input_port("list", DataType.LIST)
        self.add_output_port("result", DataType.LIST)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            lst = self.get_input_value("list", [])

            if not isinstance(lst, (list, tuple)):
                raise ValueError("Input is not a list")

            result = list(reversed(lst))

            self.set_output_value("result", result)
            return {"success": True, "data": {"result": result}, "next_nodes": []}
        except Exception as e:
            logger.error(f"List reverse failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


class ListUniqueNode(BaseNode):
    """Node that removes duplicates from a list."""

    def _define_ports(self) -> None:
        self.add_input_port("list", DataType.LIST)
        self.add_output_port("result", DataType.LIST)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            lst = self.get_input_value("list", [])

            if not isinstance(lst, (list, tuple)):
                raise ValueError("Input is not a list")

            # Preserve order while removing duplicates
            seen = set()
            result = []
            for item in lst:
                # For unhashable items, use string representation
                try:
                    key = item
                    if key not in seen:
                        seen.add(key)
                        result.append(item)
                except TypeError:
                    key = str(item)
                    if key not in seen:
                        seen.add(key)
                        result.append(item)

            self.set_output_value("result", result)
            return {"success": True, "data": {"result": result}, "next_nodes": []}
        except Exception as e:
            logger.error(f"List unique failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


class ListFilterNode(BaseNode):
    """Node that filters a list based on a condition."""

    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        # Condition: "equals", "not_equals", "contains", "starts_with", "ends_with",
        # "greater_than", "less_than", "is_not_none", "is_none"
        self.condition = self.config.get("condition", "is_not_none")
        self.key_path = self.config.get("key_path", "")

    def _define_ports(self) -> None:
        self.add_input_port("list", DataType.LIST)
        self.add_input_port("condition", DataType.STRING)
        self.add_input_port("value", DataType.ANY)
        self.add_input_port("key_path", DataType.STRING)
        self.add_output_port("result", DataType.LIST)
        self.add_output_port("removed", DataType.LIST)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            lst = self.get_input_value("list", [])
            condition = self.get_input_value("condition", self.condition)
            compare_value = self.get_input_value("value")
            key_path = self.get_input_value("key_path", self.key_path)

            if not isinstance(lst, (list, tuple)):
                raise ValueError("Input is not a list")

            def get_item_value(item):
                if not key_path:
                    return item
                current = item
                for part in key_path.split('.'):
                    if isinstance(current, dict) and part in current:
                        current = current[part]
                    else:
                        return None
                return current

            def matches(item):
                val = get_item_value(item)
                if condition == "equals":
                    return val == compare_value
                elif condition == "not_equals":
                    return val != compare_value
                elif condition == "contains":
                    return compare_value in str(val) if val else False
                elif condition == "starts_with":
                    return str(val).startswith(str(compare_value)) if val else False
                elif condition == "ends_with":
                    return str(val).endswith(str(compare_value)) if val else False
                elif condition == "greater_than":
                    return val > compare_value if val is not None else False
                elif condition == "less_than":
                    return val < compare_value if val is not None else False
                elif condition == "is_not_none":
                    return val is not None
                elif condition == "is_none":
                    return val is None
                elif condition == "is_truthy":
                    return bool(val)
                elif condition == "is_falsy":
                    return not bool(val)
                else:
                    return True

            result = [item for item in lst if matches(item)]
            removed = [item for item in lst if not matches(item)]

            self.set_output_value("result", result)
            self.set_output_value("removed", removed)
            return {"success": True, "data": {"result": result, "removed": removed}, "next_nodes": []}
        except Exception as e:
            logger.error(f"List filter failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


class ListMapNode(BaseNode):
    """Node that transforms each item in a list."""

    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        # Transform: "get_property", "to_string", "to_int", "to_float", "to_upper", "to_lower", "trim"
        self.transform = self.config.get("transform", "to_string")
        self.key_path = self.config.get("key_path", "")

    def _define_ports(self) -> None:
        self.add_input_port("list", DataType.LIST)
        self.add_input_port("transform", DataType.STRING)
        self.add_input_port("key_path", DataType.STRING)
        self.add_output_port("result", DataType.LIST)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            lst = self.get_input_value("list", [])
            transform = self.get_input_value("transform", self.transform)
            key_path = self.get_input_value("key_path", self.key_path)

            if not isinstance(lst, (list, tuple)):
                raise ValueError("Input is not a list")

            def apply_transform(item):
                # First, optionally extract property
                val = item
                if key_path:
                    for part in key_path.split('.'):
                        if isinstance(val, dict) and part in val:
                            val = val[part]
                        else:
                            val = None
                            break

                # Then apply transform
                if transform == "get_property":
                    return val
                elif transform == "to_string":
                    return str(val) if val is not None else ""
                elif transform == "to_int":
                    return int(val) if val is not None else 0
                elif transform == "to_float":
                    return float(val) if val is not None else 0.0
                elif transform == "to_upper":
                    return str(val).upper() if val else ""
                elif transform == "to_lower":
                    return str(val).lower() if val else ""
                elif transform == "trim":
                    return str(val).strip() if val else ""
                elif transform == "length":
                    return len(val) if val else 0
                else:
                    return val

            result = [apply_transform(item) for item in lst]

            self.set_output_value("result", result)
            return {"success": True, "data": {"result": result}, "next_nodes": []}
        except Exception as e:
            logger.error(f"List map failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


class ListReduceNode(BaseNode):
    """Node that reduces a list to a single value."""

    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        # Operation: "sum", "product", "min", "max", "avg", "count", "first", "last", "join"
        self.operation = self.config.get("operation", "sum")
        self.key_path = self.config.get("key_path", "")

    def _define_ports(self) -> None:
        self.add_input_port("list", DataType.LIST)
        self.add_input_port("operation", DataType.STRING)
        self.add_input_port("key_path", DataType.STRING)
        self.add_input_port("initial", DataType.ANY)
        self.add_output_port("result", DataType.ANY)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            lst = self.get_input_value("list", [])
            operation = self.get_input_value("operation", self.operation)
            key_path = self.get_input_value("key_path", self.key_path)
            initial = self.get_input_value("initial")

            if not isinstance(lst, (list, tuple)):
                raise ValueError("Input is not a list")

            # Extract values if key_path specified
            if key_path:
                values = []
                for item in lst:
                    val = item
                    for part in key_path.split('.'):
                        if isinstance(val, dict) and part in val:
                            val = val[part]
                        else:
                            val = None
                            break
                    if val is not None:
                        values.append(val)
            else:
                values = [v for v in lst if v is not None]

            if len(values) == 0:
                result = initial if initial is not None else (0 if operation in ["sum", "product", "avg", "count"] else None)
            elif operation == "sum":
                result = sum(float(v) for v in values)
            elif operation == "product":
                result = 1
                for v in values:
                    result *= float(v)
            elif operation == "min":
                result = min(values)
            elif operation == "max":
                result = max(values)
            elif operation == "avg":
                result = sum(float(v) for v in values) / len(values)
            elif operation == "count":
                result = len(values)
            elif operation == "first":
                result = values[0] if values else None
            elif operation == "last":
                result = values[-1] if values else None
            elif operation == "join":
                separator = str(initial) if initial else ""
                result = separator.join(str(v) for v in values)
            else:
                raise ValueError(f"Unknown operation: {operation}")

            self.set_output_value("result", result)
            return {"success": True, "data": {"result": result}, "next_nodes": []}
        except Exception as e:
            logger.error(f"List reduce failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


class ListFlattenNode(BaseNode):
    """Node that flattens a nested list."""

    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        self.depth = self.config.get("depth", 1)

    def _define_ports(self) -> None:
        self.add_input_port("list", DataType.LIST)
        self.add_input_port("depth", DataType.INTEGER)
        self.add_output_port("result", DataType.LIST)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            lst = self.get_input_value("list", [])
            depth = int(self.get_input_value("depth", self.depth))

            if not isinstance(lst, (list, tuple)):
                raise ValueError("Input is not a list")

            def flatten(items, current_depth):
                result = []
                for item in items:
                    if isinstance(item, (list, tuple)) and current_depth > 0:
                        result.extend(flatten(item, current_depth - 1))
                    else:
                        result.append(item)
                return result

            result = flatten(lst, depth)

            self.set_output_value("result", result)
            return {"success": True, "data": {"result": result}, "next_nodes": []}
        except Exception as e:
            logger.error(f"List flatten failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


# ==================== DICTIONARY OPERATIONS ====================

class DictGetNode(BaseNode):
    """Node that gets a value from a dictionary by key."""

    def _define_ports(self) -> None:
        self.add_input_port("dict", DataType.DICT)
        self.add_input_port("key", DataType.STRING)
        self.add_input_port("default", DataType.ANY)
        self.add_output_port("value", DataType.ANY)
        self.add_output_port("found", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            d = self.get_input_value("dict", {})
            key = self.get_input_value("key", "")
            default = self.get_input_value("default")

            if not isinstance(d, dict):
                raise ValueError("Input is not a dictionary")

            found = key in d
            value = d.get(key, default)

            self.set_output_value("value", value)
            self.set_output_value("found", found)
            return {"success": True, "data": {"value": value, "found": found}, "next_nodes": []}
        except Exception as e:
            logger.error(f"Dict get failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


class DictSetNode(BaseNode):
    """Node that sets a value in a dictionary."""

    def _define_ports(self) -> None:
        self.add_input_port("dict", DataType.DICT)
        self.add_input_port("key", DataType.STRING)
        self.add_input_port("value", DataType.ANY)
        self.add_output_port("result", DataType.DICT)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            d = self.get_input_value("dict", {})
            key = self.get_input_value("key", "")
            value = self.get_input_value("value")

            if not isinstance(d, dict):
                d = {}

            if not key:
                raise ValueError("Key is required")

            result = d.copy()
            result[key] = value

            self.set_output_value("result", result)
            return {"success": True, "data": {"result": result}, "next_nodes": []}
        except Exception as e:
            logger.error(f"Dict set failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


class DictRemoveNode(BaseNode):
    """Node that removes a key from a dictionary."""

    def _define_ports(self) -> None:
        self.add_input_port("dict", DataType.DICT)
        self.add_input_port("key", DataType.STRING)
        self.add_output_port("result", DataType.DICT)
        self.add_output_port("removed_value", DataType.ANY)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            d = self.get_input_value("dict", {})
            key = self.get_input_value("key", "")

            if not isinstance(d, dict):
                raise ValueError("Input is not a dictionary")

            result = d.copy()
            removed_value = result.pop(key, None)

            self.set_output_value("result", result)
            self.set_output_value("removed_value", removed_value)
            return {"success": True, "data": {"result": result, "removed_value": removed_value}, "next_nodes": []}
        except Exception as e:
            logger.error(f"Dict remove failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


class DictMergeNode(BaseNode):
    """Node that merges two dictionaries."""

    def _define_ports(self) -> None:
        self.add_input_port("dict_1", DataType.DICT)
        self.add_input_port("dict_2", DataType.DICT)
        self.add_output_port("result", DataType.DICT)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            d1 = self.get_input_value("dict_1", {})
            d2 = self.get_input_value("dict_2", {})

            if not isinstance(d1, dict):
                d1 = {}
            if not isinstance(d2, dict):
                d2 = {}

            result = {**d1, **d2}

            self.set_output_value("result", result)
            return {"success": True, "data": {"result": result}, "next_nodes": []}
        except Exception as e:
            logger.error(f"Dict merge failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


class DictKeysNode(BaseNode):
    """Node that gets all keys from a dictionary."""

    def _define_ports(self) -> None:
        self.add_input_port("dict", DataType.DICT)
        self.add_output_port("keys", DataType.LIST)
        self.add_output_port("count", DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            d = self.get_input_value("dict", {})

            if not isinstance(d, dict):
                raise ValueError("Input is not a dictionary")

            keys = list(d.keys())
            count = len(keys)

            self.set_output_value("keys", keys)
            self.set_output_value("count", count)
            return {"success": True, "data": {"keys": keys, "count": count}, "next_nodes": []}
        except Exception as e:
            logger.error(f"Dict keys failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


class DictValuesNode(BaseNode):
    """Node that gets all values from a dictionary."""

    def _define_ports(self) -> None:
        self.add_input_port("dict", DataType.DICT)
        self.add_output_port("values", DataType.LIST)
        self.add_output_port("count", DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            d = self.get_input_value("dict", {})

            if not isinstance(d, dict):
                raise ValueError("Input is not a dictionary")

            values = list(d.values())
            count = len(values)

            self.set_output_value("values", values)
            self.set_output_value("count", count)
            return {"success": True, "data": {"values": values, "count": count}, "next_nodes": []}
        except Exception as e:
            logger.error(f"Dict values failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


class DictHasKeyNode(BaseNode):
    """Node that checks if a dictionary has a key."""

    def _define_ports(self) -> None:
        self.add_input_port("dict", DataType.DICT)
        self.add_input_port("key", DataType.STRING)
        self.add_output_port("has_key", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            d = self.get_input_value("dict", {})
            key = self.get_input_value("key", "")

            if not isinstance(d, dict):
                raise ValueError("Input is not a dictionary")

            has_key = key in d

            self.set_output_value("has_key", has_key)
            return {"success": True, "data": {"has_key": has_key}, "next_nodes": []}
        except Exception as e:
            logger.error(f"Dict has key failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


class CreateDictNode(BaseNode):
    """Node that creates a dictionary from key-value pairs."""

    def _define_ports(self) -> None:
        self.add_input_port("key_1", DataType.STRING)
        self.add_input_port("value_1", DataType.ANY)
        self.add_input_port("key_2", DataType.STRING)
        self.add_input_port("value_2", DataType.ANY)
        self.add_input_port("key_3", DataType.STRING)
        self.add_input_port("value_3", DataType.ANY)
        self.add_output_port("dict", DataType.DICT)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            result = {}

            for i in range(1, 4):
                key = self.get_input_value(f"key_{i}")
                value = self.get_input_value(f"value_{i}")
                if key is not None and key != "":
                    result[key] = value

            self.set_output_value("dict", result)
            return {"success": True, "data": {"dict": result}, "next_nodes": []}
        except Exception as e:
            logger.error(f"Create dict failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


class DictToJsonNode(BaseNode):
    """Node that converts a dictionary to a JSON string."""

    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        default_config = {
            "indent": None,  # Indentation level (None = compact)
            "sort_keys": False,  # Sort keys alphabetically
            "ensure_ascii": True,  # Escape non-ASCII characters
            "separators": None,  # Custom separators (item, key) - None = default
        }
        if config is None:
            config = {}
        for key, value in default_config.items():
            if key not in config:
                config[key] = value
        super().__init__(node_id, config)
        self.indent = self.config.get("indent", None)

    def _define_ports(self) -> None:
        self.add_input_port("dict", DataType.DICT)
        self.add_input_port("indent", DataType.INTEGER)
        self.add_output_port("json_string", DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            d = self.get_input_value("dict", {})
            indent = self.get_input_value("indent", self.indent)

            if indent is not None:
                indent = int(indent)

            sort_keys = self.config.get("sort_keys", False)
            ensure_ascii = self.config.get("ensure_ascii", True)

            json_string = json.dumps(
                d,
                indent=indent,
                sort_keys=sort_keys,
                ensure_ascii=ensure_ascii,
                default=str
            )

            self.set_output_value("json_string", json_string)
            return {"success": True, "data": {"json_string": json_string}, "next_nodes": []}
        except Exception as e:
            logger.error(f"Dict to JSON failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


class DictItemsNode(BaseNode):
    """Node that gets key-value pairs from a dictionary as a list of tuples."""

    def _define_ports(self) -> None:
        self.add_input_port("dict", DataType.DICT)
        self.add_output_port("items", DataType.LIST)
        self.add_output_port("count", DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            d = self.get_input_value("dict", {})

            if not isinstance(d, dict):
                raise ValueError("Input is not a dictionary")

            # Return as list of dicts for easier use in workflows
            items = [{"key": k, "value": v} for k, v in d.items()]
            count = len(items)

            self.set_output_value("items", items)
            self.set_output_value("count", count)
            return {"success": True, "data": {"items": items, "count": count}, "next_nodes": []}
        except Exception as e:
            logger.error(f"Dict items failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}
