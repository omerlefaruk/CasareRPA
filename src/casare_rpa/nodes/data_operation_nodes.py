from typing import Any, Dict, List, Optional, Union
import re
import json
import math
import random
from loguru import logger

from ..core.base_node import BaseNode
from ..core.types import PortType, DataType, NodeStatus

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

    async def execute(self, context) -> NodeStatus:
        try:
            # Get inputs (support dynamic number of inputs in future, for now just 2 fixed + optional extras from config if we were to expand)
            # Actually, let's stick to the ports defined.
            s1 = str(self.get_input_value("string_1", ""))
            s2 = str(self.get_input_value("string_2", ""))
            
            result = f"{s1}{self.separator}{s2}"
            
            self.set_output_value("result", result)
            return NodeStatus.SUCCESS
        except Exception as e:
            logger.error(f"Concatenate failed: {e}")
            self.error_message = str(e)
            return NodeStatus.ERROR

class FormatStringNode(BaseNode):
    """Node that formats a string using python's format() method."""
    
    def _define_ports(self) -> None:
        self.add_input_port("template", DataType.STRING)
        self.add_input_port("variables", DataType.DICT) # Dict of variables to format with
        self.add_output_port("result", DataType.STRING)

    async def execute(self, context) -> NodeStatus:
        try:
            template = self.get_input_value("template", "")
            variables = self.get_input_value("variables", {})
            
            if not isinstance(variables, dict):
                raise ValueError("Variables input must be a dictionary")
                
            result = template.format(**variables)
            
            self.set_output_value("result", result)
            return NodeStatus.SUCCESS
        except Exception as e:
            logger.error(f"Format string failed: {e}")
            self.error_message = str(e)
            return NodeStatus.ERROR

class RegexMatchNode(BaseNode):
    """Node that searches for a regex pattern in a string."""
    
    def _define_ports(self) -> None:
        self.add_input_port("text", DataType.STRING)
        self.add_input_port("pattern", DataType.STRING)
        self.add_output_port("match_found", DataType.BOOLEAN)
        self.add_output_port("first_match", DataType.STRING)
        self.add_output_port("all_matches", DataType.LIST)
        self.add_output_port("groups", DataType.LIST)

    async def execute(self, context) -> NodeStatus:
        try:
            text = self.get_input_value("text", "")
            pattern = self.get_input_value("pattern", "")
            
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
            
            return NodeStatus.SUCCESS
        except Exception as e:
            logger.error(f"Regex match failed: {e}")
            self.error_message = str(e)
            return NodeStatus.ERROR

class RegexReplaceNode(BaseNode):
    """Node that replaces text using regex."""
    
    def _define_ports(self) -> None:
        self.add_input_port("text", DataType.STRING)
        self.add_input_port("pattern", DataType.STRING)
        self.add_input_port("replacement", DataType.STRING)
        self.add_output_port("result", DataType.STRING)
        self.add_output_port("count", DataType.INTEGER)

    async def execute(self, context) -> NodeStatus:
        try:
            text = self.get_input_value("text", "")
            pattern = self.get_input_value("pattern", "")
            replacement = self.get_input_value("replacement", "")
            
            result, count = re.subn(pattern, replacement, text)
            
            self.set_output_value("result", result)
            self.set_output_value("count", count)
            return NodeStatus.SUCCESS
        except Exception as e:
            logger.error(f"Regex replace failed: {e}")
            self.error_message = str(e)
            return NodeStatus.ERROR

class MathOperationNode(BaseNode):
    """Node that performs basic math operations."""
    
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
        # Operation: add, subtract, multiply, divide, power, modulo
        self.operation = self.config.get("operation", "add")

    def _define_ports(self) -> None:
        self.add_input_port("a", DataType.FLOAT)
        self.add_input_port("b", DataType.FLOAT)
        self.add_output_port("result", DataType.FLOAT)

    async def execute(self, context) -> NodeStatus:
        try:
            a = float(self.get_input_value("a", 0))
            b = float(self.get_input_value("b", 0))
            
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
            return NodeStatus.SUCCESS
        except Exception as e:
            logger.error(f"Math operation failed: {e}")
            self.error_message = str(e)
            return NodeStatus.ERROR

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

    async def execute(self, context) -> NodeStatus:
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
            else:
                raise ValueError(f"Unknown operator: {op}")
            
            self.set_output_value("result", result)
            return NodeStatus.SUCCESS
        except Exception as e:
            logger.error(f"Comparison failed: {e}")
            self.error_message = str(e)
            return NodeStatus.ERROR

class CreateListNode(BaseNode):
    """Node that creates a list from inputs."""
    
    def _define_ports(self) -> None:
        # Dynamic inputs would be better, but for now let's support up to 5 items
        # or take a single input that is already a list/tuple to convert
        self.add_input_port("item_1", DataType.ANY)
        self.add_input_port("item_2", DataType.ANY)
        self.add_input_port("item_3", DataType.ANY)
        self.add_output_port("list", DataType.LIST)

    async def execute(self, context) -> NodeStatus:
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
            return NodeStatus.SUCCESS
        except Exception as e:
            logger.error(f"Create list failed: {e}")
            self.error_message = str(e)
            return NodeStatus.ERROR

class ListGetItemNode(BaseNode):
    """Node that gets an item from a list by index."""
    
    def _define_ports(self) -> None:
        self.add_input_port("list", DataType.LIST)
        self.add_input_port("index", DataType.INTEGER)
        self.add_output_port("item", DataType.ANY)

    async def execute(self, context) -> NodeStatus:
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
            return NodeStatus.SUCCESS
        except Exception as e:
            logger.error(f"List get item failed: {e}")
            self.error_message = str(e)
            return NodeStatus.ERROR

class JsonParseNode(BaseNode):
    """Node that parses a JSON string."""
    
    def _define_ports(self) -> None:
        self.add_input_port("json_string", DataType.STRING)
        self.add_output_port("data", DataType.ANY)

    async def execute(self, context) -> NodeStatus:
        try:
            json_str = self.get_input_value("json_string", "")
            if not json_str:
                raise ValueError("Empty JSON string")
                
            data = json.loads(json_str)
            self.set_output_value("data", data)
            return NodeStatus.SUCCESS
        except Exception as e:
            logger.error(f"JSON parse failed: {e}")
            self.error_message = str(e)
            return NodeStatus.ERROR

class GetPropertyNode(BaseNode):
    """Node that gets a property from a dictionary/object."""
    
    def _define_ports(self) -> None:
        self.add_input_port("object", DataType.DICT)
        self.add_input_port("property_path", DataType.STRING) # dot notation supported e.g. "user.address.city"
        self.add_output_port("value", DataType.ANY)

    async def execute(self, context) -> NodeStatus:
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
            return NodeStatus.SUCCESS
        except Exception as e:
            logger.error(f"Get property failed: {e}")
            self.error_message = str(e)
            return NodeStatus.ERROR
