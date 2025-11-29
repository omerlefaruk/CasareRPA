"""
CasareRPA - Dictionary Operation Nodes

Provides nodes for dictionary/object manipulation including:
- Property access and modification
- JSON parsing and serialization
- Dictionary merging and key/value operations
"""

from typing import Any, Dict
import json
from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType, ExecutionResult, PortType
from casare_rpa.infrastructure.execution import ExecutionContext


@executable_node
class JsonParseNode(BaseNode):
    """Node that parses a JSON string."""

    def __init__(self, node_id: str, name: str = "JSON Parse", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "JsonParseNode"

    def _define_ports(self) -> None:
        self.add_input_port("json_string", PortType.INPUT, DataType.STRING)
        self.add_output_port("data", PortType.OUTPUT, DataType.ANY)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            json_str = self.get_parameter("json_string", "")
            if not json_str:
                raise ValueError("Empty JSON string")

            data = json.loads(json_str)
            self.set_output_value("data", data)
            return {"success": True, "data": {"data": data}, "next_nodes": []}
        except Exception as e:
            logger.error(f"JSON parse failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


@executable_node
class GetPropertyNode(BaseNode):
    """Node that gets a property from a dictionary/object."""

    def __init__(self, node_id: str, name: str = "Get Property", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "GetPropertyNode"

    def _define_ports(self) -> None:
        self.add_input_port("object", PortType.INPUT, DataType.DICT)
        self.add_input_port("property_path", PortType.INPUT, DataType.STRING)
        self.add_output_port("value", PortType.OUTPUT, DataType.ANY)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            obj = self.get_parameter("object", {})
            path = self.get_parameter("property_path", "")

            if not isinstance(obj, dict):
                raise ValueError("Input is not a dictionary")

            current: Any = obj
            for part in path.split("."):
                if not part:
                    continue
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    current = None
                    break

            self.set_output_value("value", current)
            return {"success": True, "data": {"value": current}, "next_nodes": []}
        except Exception as e:
            logger.error(f"Get property failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


@executable_node
class DictGetNode(BaseNode):
    """Node that gets a value from a dictionary by key."""

    def __init__(self, node_id: str, name: str = "Dict Get", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "DictGetNode"

    def _define_ports(self) -> None:
        self.add_input_port("dict", PortType.INPUT, DataType.DICT)
        self.add_input_port("key", PortType.INPUT, DataType.STRING)
        self.add_input_port("default", PortType.INPUT, DataType.ANY)
        self.add_output_port("value", PortType.OUTPUT, DataType.ANY)
        self.add_output_port("found", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            d = self.get_parameter("dict", {})
            key = self.get_parameter("key", "")
            default = self.get_parameter("default")

            if not isinstance(d, dict):
                raise ValueError("Input is not a dictionary")

            found = key in d
            value = d.get(key, default)

            self.set_output_value("value", value)
            self.set_output_value("found", found)
            return {
                "success": True,
                "data": {"value": value, "found": found},
                "next_nodes": [],
            }
        except Exception as e:
            logger.error(f"Dict get failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


@executable_node
class DictSetNode(BaseNode):
    """Node that sets a value in a dictionary."""

    def __init__(self, node_id: str, name: str = "Dict Set", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "DictSetNode"

    def _define_ports(self) -> None:
        self.add_input_port("dict", PortType.INPUT, DataType.DICT)
        self.add_input_port("key", PortType.INPUT, DataType.STRING)
        self.add_input_port("value", PortType.INPUT, DataType.ANY)
        self.add_output_port("result", PortType.OUTPUT, DataType.DICT)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            d = self.get_parameter("dict", {})
            key = self.get_parameter("key", "")
            value = self.get_parameter("value")

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


@executable_node
class DictRemoveNode(BaseNode):
    """Node that removes a key from a dictionary."""

    def __init__(self, node_id: str, name: str = "Dict Remove", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "DictRemoveNode"

    def _define_ports(self) -> None:
        self.add_input_port("dict", PortType.INPUT, DataType.DICT)
        self.add_input_port("key", PortType.INPUT, DataType.STRING)
        self.add_output_port("result", PortType.OUTPUT, DataType.DICT)
        self.add_output_port("removed_value", PortType.OUTPUT, DataType.ANY)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            d = self.get_parameter("dict", {})
            key = self.get_parameter("key", "")

            if not isinstance(d, dict):
                raise ValueError("Input is not a dictionary")

            result = d.copy()
            removed_value = result.pop(key, None)

            self.set_output_value("result", result)
            self.set_output_value("removed_value", removed_value)
            return {
                "success": True,
                "data": {"result": result, "removed_value": removed_value},
                "next_nodes": [],
            }
        except Exception as e:
            logger.error(f"Dict remove failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


@executable_node
class DictMergeNode(BaseNode):
    """Node that merges two dictionaries."""

    def __init__(self, node_id: str, name: str = "Dict Merge", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "DictMergeNode"

    def _define_ports(self) -> None:
        self.add_input_port("dict_1", PortType.INPUT, DataType.DICT)
        self.add_input_port("dict_2", PortType.INPUT, DataType.DICT)
        self.add_output_port("result", PortType.OUTPUT, DataType.DICT)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            d1 = self.get_parameter("dict_1", {})
            d2 = self.get_parameter("dict_2", {})

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


@executable_node
class DictKeysNode(BaseNode):
    """Node that gets all keys from a dictionary."""

    def __init__(self, node_id: str, name: str = "Dict Keys", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "DictKeysNode"

    def _define_ports(self) -> None:
        self.add_input_port("dict", PortType.INPUT, DataType.DICT)
        self.add_output_port("keys", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("count", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            d = self.get_parameter("dict", {})

            if not isinstance(d, dict):
                raise ValueError("Input is not a dictionary")

            keys = list(d.keys())
            count = len(keys)

            self.set_output_value("keys", keys)
            self.set_output_value("count", count)
            return {
                "success": True,
                "data": {"keys": keys, "count": count},
                "next_nodes": [],
            }
        except Exception as e:
            logger.error(f"Dict keys failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


@executable_node
class DictValuesNode(BaseNode):
    """Node that gets all values from a dictionary."""

    def __init__(self, node_id: str, name: str = "Dict Values", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "DictValuesNode"

    def _define_ports(self) -> None:
        self.add_input_port("dict", PortType.INPUT, DataType.DICT)
        self.add_output_port("values", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("count", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            d = self.get_parameter("dict", {})

            if not isinstance(d, dict):
                raise ValueError("Input is not a dictionary")

            values = list(d.values())
            count = len(values)

            self.set_output_value("values", values)
            self.set_output_value("count", count)
            return {
                "success": True,
                "data": {"values": values, "count": count},
                "next_nodes": [],
            }
        except Exception as e:
            logger.error(f"Dict values failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


@executable_node
class DictHasKeyNode(BaseNode):
    """Node that checks if a dictionary has a key."""

    def __init__(self, node_id: str, name: str = "Dict Has Key", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "DictHasKeyNode"

    def _define_ports(self) -> None:
        self.add_input_port("dict", PortType.INPUT, DataType.DICT)
        self.add_input_port("key", PortType.INPUT, DataType.STRING)
        self.add_output_port("has_key", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            d = self.get_parameter("dict", {})
            key = self.get_parameter("key", "")

            if not isinstance(d, dict):
                raise ValueError("Input is not a dictionary")

            has_key = key in d

            self.set_output_value("has_key", has_key)
            return {"success": True, "data": {"has_key": has_key}, "next_nodes": []}
        except Exception as e:
            logger.error(f"Dict has key failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


@executable_node
class CreateDictNode(BaseNode):
    """Node that creates a dictionary from key-value pairs."""

    def __init__(self, node_id: str, name: str = "Create Dict", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "CreateDictNode"

    def _define_ports(self) -> None:
        self.add_input_port("key_1", PortType.INPUT, DataType.STRING)
        self.add_input_port("value_1", PortType.INPUT, DataType.ANY)
        self.add_input_port("key_2", PortType.INPUT, DataType.STRING)
        self.add_input_port("value_2", PortType.INPUT, DataType.ANY)
        self.add_input_port("key_3", PortType.INPUT, DataType.STRING)
        self.add_input_port("value_3", PortType.INPUT, DataType.ANY)
        self.add_output_port("dict", PortType.OUTPUT, DataType.DICT)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            result: Dict[str, Any] = {}

            for i in range(1, 4):
                key = self.get_parameter(f"key_{i}")
                value = self.get_parameter(f"value_{i}")
                if key is not None and key != "":
                    result[key] = value

            self.set_output_value("dict", result)
            return {"success": True, "data": {"dict": result}, "next_nodes": []}
        except Exception as e:
            logger.error(f"Create dict failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


@executable_node
@node_schema(
    PropertyDef(
        "indent",
        PropertyType.INTEGER,
        default=None,
        min_value=0,
        label="Indent",
        tooltip="Number of spaces for indentation (None = compact)",
    ),
    PropertyDef(
        "sort_keys",
        PropertyType.BOOLEAN,
        default=False,
        label="Sort Keys",
        tooltip="Sort dictionary keys alphabetically",
    ),
    PropertyDef(
        "ensure_ascii",
        PropertyType.BOOLEAN,
        default=True,
        label="Ensure ASCII",
        tooltip="Escape non-ASCII characters",
    ),
)
class DictToJsonNode(BaseNode):
    """Node that converts a dictionary to a JSON string."""

    def __init__(self, node_id: str, name: str = "Dict to JSON", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "DictToJsonNode"

    def _define_ports(self) -> None:
        self.add_input_port("dict", PortType.INPUT, DataType.DICT)
        self.add_input_port("indent", PortType.INPUT, DataType.INTEGER)
        self.add_output_port("json_string", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            d = self.get_parameter("dict", {})
            indent = self.get_parameter("indent")

            if indent is not None:
                indent = int(indent)

            sort_keys = self.get_parameter("sort_keys", False)
            ensure_ascii = self.get_parameter("ensure_ascii", True)

            json_string = json.dumps(
                d,
                indent=indent,
                sort_keys=sort_keys,
                ensure_ascii=ensure_ascii,
                default=str,
            )

            self.set_output_value("json_string", json_string)
            return {
                "success": True,
                "data": {"json_string": json_string},
                "next_nodes": [],
            }
        except Exception as e:
            logger.error(f"Dict to JSON failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


@executable_node
class DictItemsNode(BaseNode):
    """Node that gets key-value pairs from a dictionary as a list of dicts."""

    def __init__(self, node_id: str, name: str = "Dict Items", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "DictItemsNode"

    def _define_ports(self) -> None:
        self.add_input_port("dict", PortType.INPUT, DataType.DICT)
        self.add_output_port("items", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("count", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            d = self.get_parameter("dict", {})

            if not isinstance(d, dict):
                raise ValueError("Input is not a dictionary")

            items = [{"key": k, "value": v} for k, v in d.items()]
            count = len(items)

            self.set_output_value("items", items)
            self.set_output_value("count", count)
            return {
                "success": True,
                "data": {"items": items, "count": count},
                "next_nodes": [],
            }
        except Exception as e:
            logger.error(f"Dict items failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


__all__ = [
    "JsonParseNode",
    "GetPropertyNode",
    "DictGetNode",
    "DictSetNode",
    "DictRemoveNode",
    "DictMergeNode",
    "DictKeysNode",
    "DictValuesNode",
    "DictHasKeyNode",
    "CreateDictNode",
    "DictToJsonNode",
    "DictItemsNode",
]
