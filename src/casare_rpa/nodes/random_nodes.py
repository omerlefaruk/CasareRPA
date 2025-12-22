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
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    NodeStatus,
    DataType,
    ExecutionResult,
)
from casare_rpa.infrastructure.execution import ExecutionContext


@properties(
    PropertyDef(
        "integer_only",
        PropertyType.BOOLEAN,
        default=False,
        label="Integer Only",
        tooltip="Generate integers only (default: False)",
    )
)
@node(category="utility")
class RandomNumberNode(BaseNode):
    """
    Generate a random number within a specified range.

    Config (via @properties):
        integer_only: Generate integers only (default: False)

    Inputs:
        min_value: Minimum value (inclusive)
        max_value: Maximum value (inclusive for int, exclusive for float)

    Outputs:
        result: The random number
    """

    # @category: data
    # @requires: none
    # @ports: min_value, max_value -> result

    def __init__(self, node_id: str, name: str = "Random Number", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "RandomNumberNode"

    def _define_ports(self) -> None:
        # min/max have defaults 0 and 100
        self.add_input_port("min_value", DataType.FLOAT, required=False)
        self.add_input_port("max_value", DataType.FLOAT, required=False)
        self.add_output_port("result", DataType.FLOAT)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            min_val = self.get_parameter("min_value", 0)
            max_val = self.get_parameter("max_value", 100)
            integer_only = self.get_parameter("integer_only", False)

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


@properties(
    PropertyDef(
        "items",
        PropertyType.LIST,
        required=True,
        label="Items",
        tooltip="List of items to choose from",
    ),
    PropertyDef(
        "count",
        PropertyType.INTEGER,
        default=1,
        min_value=1,
        label="Count",
        tooltip="Number of items to select (default: 1)",
    ),
    PropertyDef(
        "allow_duplicates",
        PropertyType.BOOLEAN,
        default=False,
        label="Allow Duplicates",
        tooltip="Allow same item multiple times (default: False)",
    ),
)
@node(category="utility")
class RandomChoiceNode(BaseNode):
    """
    Select a random item from a list.

    Config (via @properties):
        count: Number of items to select (default: 1)
        allow_duplicates: Allow same item multiple times (default: False)

    Inputs:
        items: List of items to choose from

    Outputs:
        result: Selected item(s) - single item if count=1, list otherwise
        index: Index of selected item (only for count=1)
    """

    # @category: data
    # @requires: none
    # @ports: items -> result, index

    def __init__(self, node_id: str, name: str = "Random Choice", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "RandomChoiceNode"

    def _define_ports(self) -> None:
        self.add_input_port("items", DataType.LIST)
        self.add_output_port("result", DataType.ANY)
        self.add_output_port("index", DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            items = self.get_parameter("items", [])
            count = self.get_parameter("count", 1)
            allow_duplicates = self.get_parameter("allow_duplicates", False)

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


@properties(
    PropertyDef(
        "include_uppercase",
        PropertyType.BOOLEAN,
        default=True,
        label="Include Uppercase",
        tooltip="Include A-Z (default: True)",
    ),
    PropertyDef(
        "include_lowercase",
        PropertyType.BOOLEAN,
        default=True,
        label="Include Lowercase",
        tooltip="Include a-z (default: True)",
    ),
    PropertyDef(
        "include_digits",
        PropertyType.BOOLEAN,
        default=True,
        label="Include Digits",
        tooltip="Include 0-9 (default: True)",
    ),
    PropertyDef(
        "include_special",
        PropertyType.BOOLEAN,
        default=False,
        label="Include Special",
        tooltip="Include special characters (default: False)",
    ),
    PropertyDef(
        "custom_chars",
        PropertyType.STRING,
        default="",
        label="Custom Characters",
        tooltip="Custom character set to use (overrides above)",
    ),
)
@node(category="utility")
class RandomStringNode(BaseNode):
    """
    Generate a random string.

    Config (via @properties):
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

    # @category: data
    # @requires: none
    # @ports: length -> result

    def __init__(self, node_id: str, name: str = "Random String", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "RandomStringNode"

    def _define_ports(self) -> None:
        # length has default 8
        self.add_input_port("length", DataType.INTEGER, required=False)
        self.add_output_port("result", DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            length = int(self.get_parameter("length", 8))
            custom_chars = self.get_parameter("custom_chars", "")

            if custom_chars:
                chars = custom_chars
            else:
                chars = ""
                if self.get_parameter("include_uppercase", True):
                    chars += string.ascii_uppercase
                if self.get_parameter("include_lowercase", True):
                    chars += string.ascii_lowercase
                if self.get_parameter("include_digits", True):
                    chars += string.digits
                if self.get_parameter("include_special", False):
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


@properties(
    PropertyDef(
        "version",
        PropertyType.INTEGER,
        default=4,
        choices=[1, 4],
        label="UUID Version",
        tooltip="UUID version (4 for random, 1 for time-based) (default: 4)",
    ),
    PropertyDef(
        "format",
        PropertyType.CHOICE,
        default="standard",
        choices=["standard", "hex", "urn"],
        label="Output Format",
        tooltip="Output format - 'standard', 'hex', 'urn' (default: standard)",
    ),
)
@node(category="utility")
class RandomUUIDNode(BaseNode):
    """
    Generate a random UUID.

    Config (via @properties):
        version: UUID version (4 for random, 1 for time-based) (default: 4)
        format: Output format - 'standard', 'hex', 'urn' (default: standard)

    Outputs:
        result: The UUID string
    """

    # @category: data
    # @requires: none
    # @ports: none -> result

    def __init__(self, node_id: str, name: str = "Random UUID", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "RandomUUIDNode"

    def _define_ports(self) -> None:
        self.add_output_port("result", DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            version = self.get_parameter("version", 4)
            fmt = self.get_parameter("format", "standard")

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


@properties(
    PropertyDef(
        "items",
        PropertyType.LIST,
        required=True,
        label="Items",
        tooltip="List to shuffle",
    ),
)
@node(category="utility")
class ShuffleListNode(BaseNode):
    """
    Shuffle a list randomly.

    Inputs:
        items: List to shuffle

    Outputs:
        result: Shuffled list
    """

    # @category: data
    # @requires: none
    # @ports: items -> result

    def __init__(self, node_id: str, name: str = "Shuffle List", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ShuffleListNode"

    def _define_ports(self) -> None:
        self.add_input_port("items", DataType.LIST)
        self.add_output_port("result", DataType.LIST)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            items = self.get_parameter("items", [])

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
