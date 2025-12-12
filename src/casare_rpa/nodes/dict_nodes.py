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
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType, ExecutionResult
from casare_rpa.infrastructure.execution import ExecutionContext


@node(category="data")
@properties(
    PropertyDef(
        "json_string",
        PropertyType.TEXT,
        default="",
        label="JSON String",
        placeholder='{"key": "value"}',
        tooltip="JSON string to parse",
        essential=True,
    ),
)
class JsonParseNode(BaseNode):
    """Node that parses a JSON string."""

    # @category: data
    # @requires: none
    # @ports: json_string -> data

    def __init__(self, node_id: str, name: str = "JSON Parse", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "JsonParseNode"

    def _define_ports(self) -> None:
        self.add_input_port("json_string", DataType.STRING, required=False)
        self.add_output_port("data", DataType.ANY)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            json_str = self.get_parameter("json_string", "")
            # Resolve {{variable}} patterns
            json_str = context.resolve_value(json_str) if json_str else ""
            if not json_str:
                raise ValueError("Empty JSON string")

            data = json.loads(json_str)
            self.set_output_value("data", data)
            return {"success": True, "data": {"data": data}, "next_nodes": []}
        except Exception as e:
            logger.error(f"JSON parse failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


@node(category="data")
@properties(
    PropertyDef(
        "property_path",
        PropertyType.STRING,
        default="",
        label="Property Path",
        placeholder="key.nested.value",
        tooltip="Dot-separated path to property (e.g., user.name)",
        essential=True,
    ),
)
class GetPropertyNode(BaseNode):
    """Node that gets a property from a dictionary/object."""

    # @category: data
    # @requires: none
    # @ports: object, property_path -> value

    def __init__(self, node_id: str, name: str = "Get Property", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "GetPropertyNode"

    def _define_ports(self) -> None:
        self.add_input_port("object", DataType.DICT, required=False)
        self.add_input_port("property_path", DataType.STRING, required=False)
        self.add_output_port("value", DataType.ANY)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            obj = self.get_parameter("object", {})
            path = self.get_parameter("property_path", "")
            # Resolve {{variable}} patterns
            obj = context.resolve_value(obj) if obj else {}
            path = context.resolve_value(path) if path else ""

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


@node(category="data")
@properties(
    PropertyDef(
        "key",
        PropertyType.STRING,
        default="",
        label="Key",
        placeholder="key_name",
        tooltip="Dictionary key to get",
        essential=True,
    ),
)
class DictGetNode(BaseNode):
    """Node that gets a value from a dictionary by key."""

    # @category: data
    # @requires: none
    # @ports: dict, key, default -> value, found

    def __init__(self, node_id: str, name: str = "Dict Get", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "DictGetNode"

    def _define_ports(self) -> None:
        self.add_input_port("dict", DataType.DICT, required=False)
        self.add_input_port("key", DataType.STRING, required=False)
        self.add_input_port("default", DataType.ANY, required=False)
        self.add_output_port("value", DataType.ANY)
        self.add_output_port("found", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            d = self.get_parameter("dict", {})
            key = self.get_parameter("key", "")
            default = self.get_parameter("default")
            # Resolve {{variable}} patterns
            d = context.resolve_value(d) if d else {}
            key = context.resolve_value(key) if key else ""
            default = context.resolve_value(default) if default is not None else None

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


@node(category="data")
@properties(
    PropertyDef(
        "key",
        PropertyType.STRING,
        default="",
        label="Key",
        placeholder="key_name",
        tooltip="Dictionary key to set",
        essential=True,
    ),
)
class DictSetNode(BaseNode):
    """Node that sets a value in a dictionary."""

    # @category: data
    # @requires: none
    # @ports: dict, key, value -> result

    def __init__(self, node_id: str, name: str = "Dict Set", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "DictSetNode"

    def _define_ports(self) -> None:
        self.add_input_port("dict", DataType.DICT, required=False)
        self.add_input_port("key", DataType.STRING, required=False)
        self.add_input_port("value", DataType.ANY, required=False)
        self.add_output_port("result", DataType.DICT)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            d = self.get_parameter("dict", {})
            key = self.get_parameter("key", "")
            value = self.get_parameter("value")
            # Resolve {{variable}} patterns
            d = context.resolve_value(d) if d else {}
            key = context.resolve_value(key) if key else ""
            value = context.resolve_value(value)

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


@node(category="data")
@properties(
    PropertyDef(
        "key",
        PropertyType.STRING,
        default="",
        label="Key",
        placeholder="key_name",
        tooltip="Dictionary key to remove",
        essential=True,
    ),
)
class DictRemoveNode(BaseNode):
    """Node that removes a key from a dictionary."""

    # @category: data
    # @requires: none
    # @ports: dict, key -> result, removed_value

    def __init__(self, node_id: str, name: str = "Dict Remove", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "DictRemoveNode"

    def _define_ports(self) -> None:
        self.add_input_port("dict", DataType.DICT, required=False)
        self.add_input_port("key", DataType.STRING, required=False)
        self.add_output_port("result", DataType.DICT)
        self.add_output_port("removed_value", DataType.ANY)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            d = self.get_parameter("dict", {})
            key = self.get_parameter("key", "")
            # Resolve {{variable}} patterns
            d = context.resolve_value(d) if d else {}
            key = context.resolve_value(key) if key else ""

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


@node(category="data")
@properties()  # Input port driven
class DictMergeNode(BaseNode):
    """Node that merges two dictionaries."""

    # @category: data
    # @requires: none
    # @ports: dict_1, dict_2 -> result

    def __init__(self, node_id: str, name: str = "Dict Merge", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "DictMergeNode"

    def _define_ports(self) -> None:
        self.add_input_port("dict_1", DataType.DICT, required=False)
        self.add_input_port("dict_2", DataType.DICT, required=False)
        self.add_output_port("result", DataType.DICT)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            d1 = self.get_parameter("dict_1", {})
            d2 = self.get_parameter("dict_2", {})
            # Resolve {{variable}} patterns
            d1 = context.resolve_value(d1) if d1 else {}
            d2 = context.resolve_value(d2) if d2 else {}

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


@node(category="data")
@properties()  # Input port driven
class DictKeysNode(BaseNode):
    """Node that gets all keys from a dictionary."""

    # @category: data
    # @requires: none
    # @ports: dict -> keys, count

    def __init__(self, node_id: str, name: str = "Dict Keys", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "DictKeysNode"

    def _define_ports(self) -> None:
        self.add_input_port("dict", DataType.DICT, required=False)
        self.add_output_port("keys", DataType.LIST)
        self.add_output_port("count", DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            d = self.get_parameter("dict", {})
            # Resolve {{variable}} patterns
            d = context.resolve_value(d) if d else {}

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


@node(category="data")
@properties()  # Input port driven
class DictValuesNode(BaseNode):
    """Node that gets all values from a dictionary."""

    # @category: data
    # @requires: none
    # @ports: dict -> values, count

    def __init__(self, node_id: str, name: str = "Dict Values", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "DictValuesNode"

    def _define_ports(self) -> None:
        self.add_input_port("dict", DataType.DICT, required=False)
        self.add_output_port("values", DataType.LIST)
        self.add_output_port("count", DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            d = self.get_parameter("dict", {})
            # Resolve {{variable}} patterns
            d = context.resolve_value(d) if d else {}

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


@node(category="data")
@properties()  # Input port driven
class DictHasKeyNode(BaseNode):
    """Node that checks if a dictionary has a key."""

    # @category: data
    # @requires: none
    # @ports: dict, key -> has_key

    def __init__(self, node_id: str, name: str = "Dict Has Key", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "DictHasKeyNode"

    def _define_ports(self) -> None:
        self.add_input_port("dict", DataType.DICT, required=False)
        self.add_input_port("key", DataType.STRING, required=False)
        self.add_output_port("has_key", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            d = self.get_parameter("dict", {})
            key = self.get_parameter("key", "")
            # Resolve {{variable}} patterns
            d = context.resolve_value(d) if d else {}
            key = context.resolve_value(key) if key else ""

            if not isinstance(d, dict):
                raise ValueError("Input is not a dictionary")

            has_key = key in d

            self.set_output_value("has_key", has_key)
            return {"success": True, "data": {"has_key": has_key}, "next_nodes": []}
        except Exception as e:
            logger.error(f"Dict has key failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


@node(category="data")
@properties()  # Input port driven
class CreateDictNode(BaseNode):
    """Node that creates a dictionary from key-value pairs."""

    # @category: data
    # @requires: none
    # @ports: key_1, value_1, key_2, value_2, key_3, value_3 -> dict

    def __init__(self, node_id: str, name: str = "Create Dict", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "CreateDictNode"

    def _define_ports(self) -> None:
        # All keys/values are optional - can create empty or partial dicts
        self.add_input_port("key_1", DataType.STRING, required=False)
        self.add_input_port("value_1", DataType.ANY, required=False)
        self.add_input_port("key_2", DataType.STRING, required=False)
        self.add_input_port("value_2", DataType.ANY, required=False)
        self.add_input_port("key_3", DataType.STRING, required=False)
        self.add_input_port("value_3", DataType.ANY, required=False)
        self.add_output_port("dict", DataType.DICT)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            result: Dict[str, Any] = {}

            for i in range(1, 4):
                key = self.get_parameter(f"key_{i}")
                value = self.get_parameter(f"value_{i}")
                # Resolve {{variable}} patterns
                key = context.resolve_value(key) if key else None
                value = context.resolve_value(value) if value is not None else None
                if key is not None and key != "":
                    result[key] = value

            self.set_output_value("dict", result)
            return {"success": True, "data": {"dict": result}, "next_nodes": []}
        except Exception as e:
            logger.error(f"Create dict failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


@node(category="data")
@properties(
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

    # @category: data
    # @requires: none
    # @ports: dict, indent -> json_string

    def __init__(self, node_id: str, name: str = "Dict to JSON", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "DictToJsonNode"

    def _define_ports(self) -> None:
        self.add_input_port("dict", DataType.DICT, required=False)
        self.add_input_port("indent", DataType.INTEGER, required=False)
        self.add_output_port("json_string", DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            d = self.get_parameter("dict", {})
            indent = self.get_parameter("indent")
            # Resolve {{variable}} patterns
            d = context.resolve_value(d) if d else {}

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


@node(category="data")
@properties()  # Input port driven
class DictItemsNode(BaseNode):
    """Node that gets key-value pairs from a dictionary as a list of dicts."""

    # @category: data
    # @requires: none
    # @ports: dict -> items, count

    def __init__(self, node_id: str, name: str = "Dict Items", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "DictItemsNode"

    def _define_ports(self) -> None:
        self.add_input_port("dict", DataType.DICT, required=False)
        self.add_output_port("items", DataType.LIST)
        self.add_output_port("count", DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            d = self.get_parameter("dict", {})
            # Resolve {{variable}} patterns
            d = context.resolve_value(d) if d else {}

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
