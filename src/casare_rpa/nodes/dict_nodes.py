"""
CasareRPA - Dictionary Operation Nodes

Provides nodes for dictionary/object manipulation including:
- Property access and modification
- JSON parsing and serialization
- Dictionary merging and key/value operations
"""

from typing import Any, Dict, Optional
import json
from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import DataType, ExecutionResult
from casare_rpa.infrastructure.execution import ExecutionContext


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
        self.add_input_port("property_path", DataType.STRING)
        self.add_output_port("value", DataType.ANY)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            obj = self.get_input_value("object", {})
            path = self.get_input_value("property_path", "")

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
            return {
                "success": True,
                "data": {"value": value, "found": found},
                "next_nodes": [],
            }
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
            return {
                "success": True,
                "data": {"result": result, "removed_value": removed_value},
                "next_nodes": [],
            }
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
            return {
                "success": True,
                "data": {"keys": keys, "count": count},
                "next_nodes": [],
            }
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
            return {
                "success": True,
                "data": {"values": values, "count": count},
                "next_nodes": [],
            }
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
            result: Dict[str, Any] = {}

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
            "indent": None,
            "sort_keys": False,
            "ensure_ascii": True,
            "separators": None,
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


class DictItemsNode(BaseNode):
    """Node that gets key-value pairs from a dictionary as a list of dicts."""

    def _define_ports(self) -> None:
        self.add_input_port("dict", DataType.DICT)
        self.add_output_port("items", DataType.LIST)
        self.add_output_port("count", DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            d = self.get_input_value("dict", {})

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
