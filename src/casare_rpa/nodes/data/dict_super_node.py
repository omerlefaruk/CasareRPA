"""
Super Node for CasareRPA Dictionary Operations.

This module provides a consolidated "Dict Super Node" that replaces 12
atomic dict nodes with action-based dynamic ports and properties.

DictSuperNode (12 operations):
    Create/Access:
        - Create: Create dictionary from key-value pairs
        - Get: Get value by key
        - Get Property: Get nested property (dot notation)
        - Has Key: Check if key exists
        - Keys: Get all keys
        - Values: Get all values
        - Items: Get key-value pairs

    Modify:
        - Set: Set value by key
        - Remove: Remove key
        - Merge: Merge dictionaries

    Convert:
        - Parse JSON: Parse JSON string to dict
        - To JSON: Convert dict to JSON string
"""

import json
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Awaitable

from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    NodeStatus,
    DataType,
    ExecutionResult,
)
from casare_rpa.domain.value_objects.dynamic_port_config import (
    PortDef,
    ActionPortConfig,
    DynamicPortSchema,
)

if TYPE_CHECKING:
    from casare_rpa.domain.interfaces import IExecutionContext


class DictAction(str, Enum):
    """Actions available in DictSuperNode."""

    # Create/Access operations
    CREATE = "Create Dict"
    GET = "Get Value"
    GET_PROPERTY = "Get Property"
    HAS_KEY = "Has Key"
    KEYS = "Get Keys"
    VALUES = "Get Values"
    ITEMS = "Get Items"

    # Modify operations
    SET = "Set Value"
    REMOVE = "Remove Key"
    MERGE = "Merge"

    # Convert operations
    PARSE_JSON = "Parse JSON"
    TO_JSON = "To JSON"


# Port schema for dynamic port visibility
DICT_PORT_SCHEMA = DynamicPortSchema()

# Create Dict ports
DICT_PORT_SCHEMA.register(
    DictAction.CREATE.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("key1", DataType.STRING),
            PortDef("value1", DataType.ANY),
            PortDef("key2", DataType.STRING),
            PortDef("value2", DataType.ANY),
            PortDef("key3", DataType.STRING),
            PortDef("value3", DataType.ANY),
        ],
        outputs=[
            PortDef("dict", DataType.DICT),
            PortDef("count", DataType.INTEGER),
        ],
    ),
)

# Get Value ports
DICT_PORT_SCHEMA.register(
    DictAction.GET.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("dict", DataType.DICT),
            PortDef("key", DataType.STRING),
        ],
        outputs=[
            PortDef("value", DataType.ANY),
            PortDef("found", DataType.BOOLEAN),
        ],
    ),
)

# Get Property ports
DICT_PORT_SCHEMA.register(
    DictAction.GET_PROPERTY.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("dict", DataType.DICT),
            PortDef("path", DataType.STRING),
        ],
        outputs=[
            PortDef("value", DataType.ANY),
            PortDef("found", DataType.BOOLEAN),
        ],
    ),
)

# Has Key ports
DICT_PORT_SCHEMA.register(
    DictAction.HAS_KEY.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("dict", DataType.DICT),
            PortDef("key", DataType.STRING),
        ],
        outputs=[
            PortDef("has_key", DataType.BOOLEAN),
        ],
    ),
)

# Get Keys ports
DICT_PORT_SCHEMA.register(
    DictAction.KEYS.value,
    ActionPortConfig.create(
        inputs=[PortDef("dict", DataType.DICT)],
        outputs=[
            PortDef("keys", DataType.LIST),
            PortDef("count", DataType.INTEGER),
        ],
    ),
)

# Get Values ports
DICT_PORT_SCHEMA.register(
    DictAction.VALUES.value,
    ActionPortConfig.create(
        inputs=[PortDef("dict", DataType.DICT)],
        outputs=[
            PortDef("values", DataType.LIST),
            PortDef("count", DataType.INTEGER),
        ],
    ),
)

# Get Items ports
DICT_PORT_SCHEMA.register(
    DictAction.ITEMS.value,
    ActionPortConfig.create(
        inputs=[PortDef("dict", DataType.DICT)],
        outputs=[
            PortDef("items", DataType.LIST),
            PortDef("count", DataType.INTEGER),
        ],
    ),
)

# Set Value ports
DICT_PORT_SCHEMA.register(
    DictAction.SET.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("dict", DataType.DICT),
            PortDef("key", DataType.STRING),
            PortDef("value", DataType.ANY),
        ],
        outputs=[
            PortDef("dict", DataType.DICT),
            PortDef("previous", DataType.ANY),
            PortDef("was_update", DataType.BOOLEAN),
        ],
    ),
)

# Remove Key ports
DICT_PORT_SCHEMA.register(
    DictAction.REMOVE.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("dict", DataType.DICT),
            PortDef("key", DataType.STRING),
        ],
        outputs=[
            PortDef("dict", DataType.DICT),
            PortDef("removed_value", DataType.ANY),
            PortDef("was_removed", DataType.BOOLEAN),
        ],
    ),
)

# Merge ports
DICT_PORT_SCHEMA.register(
    DictAction.MERGE.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("dict1", DataType.DICT),
            PortDef("dict2", DataType.DICT),
        ],
        outputs=[
            PortDef("merged", DataType.DICT),
            PortDef("count", DataType.INTEGER),
        ],
    ),
)

# Parse JSON ports
DICT_PORT_SCHEMA.register(
    DictAction.PARSE_JSON.value,
    ActionPortConfig.create(
        inputs=[PortDef("json_string", DataType.STRING)],
        outputs=[
            PortDef("data", DataType.ANY),
            PortDef("success", DataType.BOOLEAN),
            PortDef("error", DataType.STRING),
        ],
    ),
)

# To JSON ports
DICT_PORT_SCHEMA.register(
    DictAction.TO_JSON.value,
    ActionPortConfig.create(
        inputs=[PortDef("data", DataType.ANY)],
        outputs=[
            PortDef("json_string", DataType.STRING),
            PortDef("success", DataType.BOOLEAN),
        ],
    ),
)


# Action groups for display_when
ACCESS_ACTIONS = [
    DictAction.GET.value,
    DictAction.GET_PROPERTY.value,
    DictAction.HAS_KEY.value,
]

MODIFY_ACTIONS = [
    DictAction.SET.value,
    DictAction.REMOVE.value,
]

JSON_ACTIONS = [
    DictAction.PARSE_JSON.value,
    DictAction.TO_JSON.value,
]


@node(category="data")
@properties(
    # === ESSENTIAL: Action selector (always visible) ===
    PropertyDef(
        "action",
        PropertyType.CHOICE,
        default=DictAction.GET.value,
        label="Action",
        tooltip="Dictionary operation to perform",
        essential=True,
        order=0,
        choices=[a.value for a in DictAction],
    ),
    # === GET VALUE OPTIONS ===
    PropertyDef(
        "default_value",
        PropertyType.STRING,
        default="",
        label="Default Value",
        tooltip="Value to return if key is not found",
        order=10,
        display_when={"action": [DictAction.GET.value, DictAction.GET_PROPERTY.value]},
    ),
    # === GET PROPERTY OPTIONS ===
    PropertyDef(
        "separator",
        PropertyType.STRING,
        default=".",
        label="Path Separator",
        tooltip="Separator for nested property paths",
        order=11,
        display_when={"action": [DictAction.GET_PROPERTY.value]},
    ),
    # === SET VALUE OPTIONS ===
    PropertyDef(
        "create_path",
        PropertyType.BOOLEAN,
        default=True,
        label="Create Path",
        tooltip="Create nested dicts if path doesn't exist",
        order=10,
        display_when={"action": [DictAction.SET.value]},
    ),
    # === REMOVE OPTIONS ===
    PropertyDef(
        "ignore_missing",
        PropertyType.BOOLEAN,
        default=False,
        label="Ignore Missing",
        tooltip="Don't error if key doesn't exist",
        order=10,
        display_when={"action": [DictAction.REMOVE.value]},
    ),
    # === MERGE OPTIONS ===
    PropertyDef(
        "deep_merge",
        PropertyType.BOOLEAN,
        default=False,
        label="Deep Merge",
        tooltip="Recursively merge nested dicts",
        order=10,
        display_when={"action": [DictAction.MERGE.value]},
    ),
    PropertyDef(
        "overwrite",
        PropertyType.BOOLEAN,
        default=True,
        label="Overwrite",
        tooltip="Overwrite values from dict1 with dict2",
        order=11,
        display_when={"action": [DictAction.MERGE.value]},
    ),
    # === TO JSON OPTIONS ===
    PropertyDef(
        "indent",
        PropertyType.INTEGER,
        default=0,
        min_value=0,
        label="Indent",
        tooltip="JSON indentation (0 for compact)",
        order=10,
        display_when={"action": [DictAction.TO_JSON.value]},
    ),
    PropertyDef(
        "sort_keys",
        PropertyType.BOOLEAN,
        default=False,
        label="Sort Keys",
        tooltip="Sort dictionary keys in output",
        order=11,
        display_when={"action": [DictAction.TO_JSON.value]},
    ),
    PropertyDef(
        "ensure_ascii",
        PropertyType.BOOLEAN,
        default=False,
        label="Ensure ASCII",
        tooltip="Escape non-ASCII characters",
        order=12,
        display_when={"action": [DictAction.TO_JSON.value]},
    ),
)
class DictSuperNode(BaseNode):
    """
    Unified dictionary operations node.

    Consolidates 12 atomic dict operations into a single configurable node.
    Select an action from the dropdown to see relevant properties and ports.

    Actions:
        Create/Access:
        - Create Dict: Create dictionary from key-value pairs
        - Get Value: Get value by key
        - Get Property: Get nested property (dot notation)
        - Has Key: Check if key exists
        - Get Keys: Get all keys
        - Get Values: Get all values
        - Get Items: Get key-value pairs

        Modify:
        - Set Value: Set value by key
        - Remove Key: Remove key from dict
        - Merge: Merge two dictionaries

        Convert:
        - Parse JSON: Parse JSON string to dict
        - To JSON: Convert dict to JSON string
    """

    def __init__(self, node_id: str, name: str = "Dict", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "DictSuperNode"

    def _define_ports(self) -> None:
        """Define ports based on current action."""
        # Default to Get Value ports
        self.add_input_port("dict", DataType.DICT)
        self.add_input_port("key", DataType.STRING)
        self.add_output_port("value", DataType.ANY)
        self.add_output_port("found", DataType.BOOLEAN)

    async def execute(self, context: "IExecutionContext") -> ExecutionResult:
        """Execute the selected dict action."""
        self.status = NodeStatus.RUNNING

        action = self.get_parameter("action", DictAction.GET.value)

        # Map actions to handlers
        handlers: dict[
            str, Callable[["IExecutionContext"], Awaitable[ExecutionResult]]
        ] = {
            DictAction.CREATE.value: self._execute_create,
            DictAction.GET.value: self._execute_get,
            DictAction.GET_PROPERTY.value: self._execute_get_property,
            DictAction.HAS_KEY.value: self._execute_has_key,
            DictAction.KEYS.value: self._execute_keys,
            DictAction.VALUES.value: self._execute_values,
            DictAction.ITEMS.value: self._execute_items,
            DictAction.SET.value: self._execute_set,
            DictAction.REMOVE.value: self._execute_remove,
            DictAction.MERGE.value: self._execute_merge,
            DictAction.PARSE_JSON.value: self._execute_parse_json,
            DictAction.TO_JSON.value: self._execute_to_json,
        }

        handler = handlers.get(action)
        if not handler:
            self.status = NodeStatus.ERROR
            return {"success": False, "error": f"Unknown action: {action}"}

        try:
            return await handler(context)
        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Error in DictSuperNode ({action}): {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    # === CREATE/ACCESS ACTION HANDLERS ===

    async def _execute_create(self, context: "IExecutionContext") -> ExecutionResult:
        """Create a new dict from key-value pairs."""
        result = {}

        # Collect key-value pairs
        for i in range(1, 4):
            key = self.get_input_value(f"key{i}", context)
            value = self.get_input_value(f"value{i}", context)
            if key is not None:
                result[str(key)] = value

        self.set_output_value("dict", result)
        self.set_output_value("count", len(result))
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"count": len(result)},
            "next_nodes": ["exec_out"],
        }

    async def _execute_get(self, context: "IExecutionContext") -> ExecutionResult:
        """Get value by key."""
        input_dict = self.get_input_value("dict", context)
        if not isinstance(input_dict, dict):
            input_dict = {}

        key = self.get_input_value("key", context)
        if key is not None:
            key = str(key)

        default_value = self.get_parameter("default_value", "")

        found = key in input_dict
        value = input_dict.get(key, default_value if default_value else None)

        self.set_output_value("value", value)
        self.set_output_value("found", found)
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"found": found},
            "next_nodes": ["exec_out"],
        }

    async def _execute_get_property(
        self, context: "IExecutionContext"
    ) -> ExecutionResult:
        """Get nested property using dot notation."""
        input_dict = self.get_input_value("dict", context)
        if not isinstance(input_dict, dict):
            input_dict = {}

        path = self.get_input_value("path", context)
        if path is None:
            path = ""
        path = str(path)

        separator = self.get_parameter("separator", ".")
        default_value = self.get_parameter("default_value", "")

        # Navigate nested path
        current = input_dict
        found = True
        parts = path.split(separator) if path else []

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            elif isinstance(current, list):
                try:
                    idx = int(part)
                    current = current[idx]
                except (ValueError, IndexError):
                    found = False
                    current = default_value if default_value else None
                    break
            else:
                found = False
                current = default_value if default_value else None
                break

        self.set_output_value("value", current)
        self.set_output_value("found", found)
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"found": found},
            "next_nodes": ["exec_out"],
        }

    async def _execute_has_key(self, context: "IExecutionContext") -> ExecutionResult:
        """Check if key exists."""
        input_dict = self.get_input_value("dict", context)
        if not isinstance(input_dict, dict):
            input_dict = {}

        key = self.get_input_value("key", context)
        if key is not None:
            key = str(key)

        has_key = key in input_dict

        self.set_output_value("has_key", has_key)
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"has_key": has_key},
            "next_nodes": ["exec_out"],
        }

    async def _execute_keys(self, context: "IExecutionContext") -> ExecutionResult:
        """Get all keys."""
        input_dict = self.get_input_value("dict", context)
        if not isinstance(input_dict, dict):
            input_dict = {}

        keys = list(input_dict.keys())

        self.set_output_value("keys", keys)
        self.set_output_value("count", len(keys))
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"count": len(keys)},
            "next_nodes": ["exec_out"],
        }

    async def _execute_values(self, context: "IExecutionContext") -> ExecutionResult:
        """Get all values."""
        input_dict = self.get_input_value("dict", context)
        if not isinstance(input_dict, dict):
            input_dict = {}

        values = list(input_dict.values())

        self.set_output_value("values", values)
        self.set_output_value("count", len(values))
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"count": len(values)},
            "next_nodes": ["exec_out"],
        }

    async def _execute_items(self, context: "IExecutionContext") -> ExecutionResult:
        """Get key-value pairs."""
        input_dict = self.get_input_value("dict", context)
        if not isinstance(input_dict, dict):
            input_dict = {}

        items = [{"key": k, "value": v} for k, v in input_dict.items()]

        self.set_output_value("items", items)
        self.set_output_value("count", len(items))
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"count": len(items)},
            "next_nodes": ["exec_out"],
        }

    # === MODIFY ACTION HANDLERS ===

    async def _execute_set(self, context: "IExecutionContext") -> ExecutionResult:
        """Set value by key."""
        input_dict = self.get_input_value("dict", context)
        if not isinstance(input_dict, dict):
            input_dict = {}
        else:
            input_dict = dict(input_dict)  # Create a copy

        key = self.get_input_value("key", context)
        if key is not None:
            key = str(key)
        value = self.get_input_value("value", context)

        was_update = key in input_dict
        previous = input_dict.get(key)
        input_dict[key] = value

        self.set_output_value("dict", input_dict)
        self.set_output_value("previous", previous)
        self.set_output_value("was_update", was_update)
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"was_update": was_update},
            "next_nodes": ["exec_out"],
        }

    async def _execute_remove(self, context: "IExecutionContext") -> ExecutionResult:
        """Remove key from dict."""
        input_dict = self.get_input_value("dict", context)
        if not isinstance(input_dict, dict):
            input_dict = {}
        else:
            input_dict = dict(input_dict)  # Create a copy

        key = self.get_input_value("key", context)
        if key is not None:
            key = str(key)

        ignore_missing = self.get_parameter("ignore_missing", False)

        was_removed = key in input_dict
        removed_value = None

        if was_removed:
            removed_value = input_dict.pop(key)
        elif not ignore_missing:
            raise KeyError(f"Key not found: {key}")

        self.set_output_value("dict", input_dict)
        self.set_output_value("removed_value", removed_value)
        self.set_output_value("was_removed", was_removed)
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"was_removed": was_removed},
            "next_nodes": ["exec_out"],
        }

    async def _execute_merge(self, context: "IExecutionContext") -> ExecutionResult:
        """Merge two dictionaries."""
        dict1 = self.get_input_value("dict1", context)
        dict2 = self.get_input_value("dict2", context)

        if not isinstance(dict1, dict):
            dict1 = {}
        if not isinstance(dict2, dict):
            dict2 = {}

        deep_merge = self.get_parameter("deep_merge", False)
        overwrite = self.get_parameter("overwrite", True)

        def deep_merge_dicts(d1: dict, d2: dict) -> dict:
            result = dict(d1)
            for key, value in d2.items():
                if (
                    key in result
                    and isinstance(result[key], dict)
                    and isinstance(value, dict)
                ):
                    result[key] = deep_merge_dicts(result[key], value)
                elif key not in result or overwrite:
                    result[key] = value
            return result

        if deep_merge:
            merged = deep_merge_dicts(dict1, dict2)
        else:
            if overwrite:
                merged = {**dict1, **dict2}
            else:
                merged = {**dict2, **dict1}

        self.set_output_value("merged", merged)
        self.set_output_value("count", len(merged))
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"count": len(merged)},
            "next_nodes": ["exec_out"],
        }

    # === CONVERT ACTION HANDLERS ===

    async def _execute_parse_json(
        self, context: "IExecutionContext"
    ) -> ExecutionResult:
        """Parse JSON string to dict."""
        json_string = self.get_input_value("json_string", context)
        if json_string is None:
            json_string = ""

        json_string = str(json_string)

        try:
            data = json.loads(json_string)
            self.set_output_value("data", data)
            self.set_output_value("success", True)
            self.set_output_value("error", "")
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"type": type(data).__name__},
                "next_nodes": ["exec_out"],
            }
        except json.JSONDecodeError as e:
            self.set_output_value("data", None)
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            self.status = NodeStatus.SUCCESS  # Node succeeded, parsing failed

            return {
                "success": True,
                "data": {"error": str(e)},
                "next_nodes": ["exec_out"],
            }

    async def _execute_to_json(self, context: "IExecutionContext") -> ExecutionResult:
        """Convert dict to JSON string."""
        data = self.get_input_value("data", context)

        indent = self.get_parameter("indent", 0)
        sort_keys = self.get_parameter("sort_keys", False)
        ensure_ascii = self.get_parameter("ensure_ascii", False)

        try:
            json_string = json.dumps(
                data,
                indent=indent if indent > 0 else None,
                sort_keys=sort_keys,
                ensure_ascii=ensure_ascii,
            )
            self.set_output_value("json_string", json_string)
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"length": len(json_string)},
                "next_nodes": ["exec_out"],
            }
        except (TypeError, ValueError) as e:
            self.set_output_value("json_string", "")
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR

            return {
                "success": False,
                "error": str(e),
                "next_nodes": [],
            }

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


__all__ = [
    "DictSuperNode",
    "DictAction",
    "DICT_PORT_SCHEMA",
]
