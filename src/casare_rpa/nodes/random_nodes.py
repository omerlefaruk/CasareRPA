"""
Random generation nodes for CasareRPA.

This module provides nodes for random number generation and random selection:
- RandomNumberNode: Generate random integers or floats
- RandomChoiceNode: Select random items from a list
- RandomStringNode: Generate random strings
- RandomUUIDNode: Generate UUIDs
- ShuffleListNode: Shuffle a list randomly
"""

import random
import string
import uuid

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import (
    NodeStatus,
    PortType,
    DataType,
    ExecutionResult,
)
from casare_rpa.infrastructure.execution import ExecutionContext


class RandomNumberNode(BaseNode):
    """
    Generate a random number within a specified range.

    Config:
        integer_only: Generate integers only (default: False)

    Inputs:
        min_value: Minimum value (inclusive)
        max_value: Maximum value (inclusive for int, exclusive for float)

    Outputs:
        result: The random number
    """

    def __init__(self, node_id: str, name: str = "Random Number", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "RandomNumberNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("min_value", PortType.INPUT, DataType.FLOAT)
        self.add_input_port("max_value", PortType.INPUT, DataType.FLOAT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("result", PortType.OUTPUT, DataType.FLOAT)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            min_val = self.get_input_value("min_value", context)
            max_val = self.get_input_value("max_value", context)
            integer_only = self.config.get("integer_only", False)

            # Defaults
            if min_val is None:
                min_val = 0
            if max_val is None:
                max_val = 100

            min_val = float(min_val)
            max_val = float(max_val)

            if min_val > max_val:
                min_val, max_val = max_val, min_val

            if integer_only:
                result = random.randint(int(min_val), int(max_val))
            else:
                result = random.uniform(min_val, max_val)

            self.set_output_value("result", result)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"result": result},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


class RandomChoiceNode(BaseNode):
    """
    Select a random item from a list.

    Config:
        count: Number of items to select (default: 1)
        allow_duplicates: Allow same item multiple times (default: False)

    Inputs:
        items: List of items to choose from

    Outputs:
        result: Selected item(s) - single item if count=1, list otherwise
        index: Index of selected item (only for count=1)
    """

    def __init__(self, node_id: str, name: str = "Random Choice", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "RandomChoiceNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("items", PortType.INPUT, DataType.LIST)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("result", PortType.OUTPUT, DataType.ANY)
        self.add_output_port("index", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            items = self.get_input_value("items", context) or []
            count = self.config.get("count", 1)
            allow_duplicates = self.config.get("allow_duplicates", False)

            if not items:
                raise ValueError("items list cannot be empty")

            if not isinstance(items, (list, tuple)):
                items = list(items)

            count = int(count)

            if count == 1:
                index = random.randint(0, len(items) - 1)
                result = items[index]
                self.set_output_value("index", index)
            else:
                if allow_duplicates:
                    result = random.choices(items, k=count)
                else:
                    if count > len(items):
                        count = len(items)
                    result = random.sample(items, count)
                self.set_output_value("index", -1)

            self.set_output_value("result", result)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"result": result},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


class RandomStringNode(BaseNode):
    """
    Generate a random string.

    Config:
        include_uppercase: Include A-Z (default: True)
        include_lowercase: Include a-z (default: True)
        include_digits: Include 0-9 (default: True)
        include_special: Include special characters (default: False)
        custom_chars: Custom character set to use (overrides above)

    Inputs:
        length: Length of string to generate

    Outputs:
        result: The random string
    """

    def __init__(self, node_id: str, name: str = "Random String", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "RandomStringNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("length", PortType.INPUT, DataType.INTEGER)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("result", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            length = int(self.get_input_value("length", context) or 8)
            custom_chars = self.config.get("custom_chars", "")

            if custom_chars:
                chars = custom_chars
            else:
                chars = ""
                if self.config.get("include_uppercase", True):
                    chars += string.ascii_uppercase
                if self.config.get("include_lowercase", True):
                    chars += string.ascii_lowercase
                if self.config.get("include_digits", True):
                    chars += string.digits
                if self.config.get("include_special", False):
                    chars += string.punctuation

            if not chars:
                chars = string.ascii_letters + string.digits

            result = "".join(random.choice(chars) for _ in range(length))

            self.set_output_value("result", result)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"result": result, "length": length},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


class RandomUUIDNode(BaseNode):
    """
    Generate a random UUID.

    Config:
        version: UUID version (4 for random, 1 for time-based) (default: 4)
        format: Output format - 'standard', 'hex', 'urn' (default: standard)

    Outputs:
        result: The UUID string
    """

    def __init__(self, node_id: str, name: str = "Random UUID", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "RandomUUIDNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("result", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            version = self.config.get("version", 4)
            fmt = self.config.get("format", "standard")

            if version == 1:
                uid = uuid.uuid1()
            else:
                uid = uuid.uuid4()

            if fmt == "hex":
                result = uid.hex
            elif fmt == "urn":
                result = uid.urn
            else:
                result = str(uid)

            self.set_output_value("result", result)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"result": result},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


class ShuffleListNode(BaseNode):
    """
    Shuffle a list randomly.

    Inputs:
        items: List to shuffle

    Outputs:
        result: Shuffled list
    """

    def __init__(self, node_id: str, name: str = "Shuffle List", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ShuffleListNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("items", PortType.INPUT, DataType.LIST)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("result", PortType.OUTPUT, DataType.LIST)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            items = self.get_input_value("items", context) or []

            if not isinstance(items, list):
                items = list(items)

            result = items.copy()
            random.shuffle(result)

            self.set_output_value("result", result)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"count": len(result)},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""
