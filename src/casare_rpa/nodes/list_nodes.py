"""
CasareRPA - List Operation Nodes

Provides nodes for list/array manipulation including:
- Creation and indexing
- Slicing and filtering
- Sorting and transformation
- Reduction operations
"""

from typing import Any
from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType, ExecutionResult
from casare_rpa.infrastructure.execution import ExecutionContext

# Maximum recursion depth for flatten operation to prevent stack overflow
MAX_FLATTEN_DEPTH = 100


def _strip_var_wrapper(value: str) -> str:
    """Strip {{}} wrapper from variable reference if present."""
    value = value.strip()
    if value.startswith("{{") and value.endswith("}}"):
        return value[2:-2].strip()
    return value


def _resolve_list_param(
    node: BaseNode,
    context: ExecutionContext,
    port_name: str = "list",
    param_name: str = "list",
) -> Any:
    """Resolve a list parameter from input port, parameter, or variable reference.

    Priority:
    1. Input port value (from connection)
    2. Parameter value (direct list)
    3. Variable reference (string -> context.get_variable)
    """
    # Try input port first
    value = node.get_input_value(port_name)
    if value is not None:
        return value

    # Try parameter
    param = node.get_parameter(param_name, [])

    # If it's a string, treat as variable reference
    if isinstance(param, str) and param:
        var_name = _strip_var_wrapper(param)
        resolved = context.get_variable(var_name)
        if resolved is not None:
            return resolved
        # Return empty list if variable not found
        return []

    return param


@properties()  # Input port driven
@node(category="data")
class CreateListNode(BaseNode):
    """Node that creates a list from inputs."""

    # @category: data
    # @requires: none
    # @ports: item_1, item_2, item_3 -> list

    def __init__(self, node_id: str, name: str = "Create List", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "CreateListNode"

    def _define_ports(self) -> None:
        self.add_input_port("item_1", DataType.ANY, required=False)
        self.add_input_port("item_2", DataType.ANY, required=False)
        self.add_input_port("item_3", DataType.ANY, required=False)
        self.add_output_port("list", DataType.LIST)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            result = []

            for i in range(1, 4):
                key = f"item_{i}"
                # Try input port first, then parameter
                val = self.get_input_value(key)
                if val is None:
                    param = self.get_parameter(key)
                    # If string, resolve as variable reference
                    if isinstance(param, str) and param:
                        val = context.get_variable(param)
                        if val is None:
                            val = param  # Use literal string if not a variable
                    else:
                        val = param

                if val is not None:
                    result.append(val)

            self.set_output_value("list", result)
            return {"success": True, "data": {"list": result}, "next_nodes": []}
        except Exception as e:
            logger.error(f"Create list failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


@properties()  # Input port driven
@node(category="data")
class ListGetItemNode(BaseNode):
    """Node that gets an item from a list by index."""

    # @category: data
    # @requires: none
    # @ports: list, index -> item

    def __init__(self, node_id: str, name: str = "List Get Item", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ListGetItemNode"

    def _define_ports(self) -> None:
        self.add_input_port("list", DataType.LIST, required=False)
        self.add_input_port("index", DataType.INTEGER, required=False)
        self.add_output_port("item", DataType.ANY)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            lst = _resolve_list_param(self, context)

            # Resolve index from port or parameter
            idx = self.get_input_value("index")
            if idx is None:
                idx_param = self.get_parameter("index", 0)
                if isinstance(idx_param, str) and idx_param:
                    resolved = context.get_variable(idx_param)
                    idx = int(resolved) if resolved is not None else 0
                else:
                    idx = int(idx_param) if idx_param is not None else 0
            else:
                idx = int(idx)

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


@properties()  # Input port driven
@node(category="data")
class ListLengthNode(BaseNode):
    """Node that returns the length of a list."""

    # @category: data
    # @requires: none
    # @ports: list -> length

    def __init__(self, node_id: str, name: str = "List Length", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ListLengthNode"

    def _define_ports(self) -> None:
        self.add_input_port("list", DataType.LIST, required=False)
        self.add_output_port("length", DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            lst = _resolve_list_param(self, context)

            if not isinstance(lst, (list, tuple)):
                raise ValueError("Input is not a list")

            length = len(lst)
            self.set_output_value("length", length)
            return {"success": True, "data": {"length": length}, "next_nodes": []}
        except Exception as e:
            logger.error(f"List length failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


@properties()  # Input port driven
@node(category="data")
class ListAppendNode(BaseNode):
    """Node that appends an item to a list."""

    # @category: data
    # @requires: none
    # @ports: list, item -> result

    def __init__(self, node_id: str, name: str = "List Append", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ListAppendNode"

    def _define_ports(self) -> None:
        self.add_input_port("list", DataType.LIST, required=False)
        self.add_input_port("item", DataType.ANY, required=False)
        self.add_output_port("result", DataType.LIST)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            lst = _resolve_list_param(self, context)

            # Resolve item from port or parameter
            item = self.get_input_value("item")
            if item is None:
                item_param = self.get_parameter("item")
                if isinstance(item_param, str) and item_param:
                    resolved = context.get_variable(item_param)
                    item = resolved if resolved is not None else item_param
                else:
                    item = item_param

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


@properties()  # Input port driven
@node(category="data")
class ListContainsNode(BaseNode):
    """Node that checks if a list contains an item."""

    # @category: data
    # @requires: none
    # @ports: list, item -> contains, index

    def __init__(self, node_id: str, name: str = "List Contains", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ListContainsNode"

    def _define_ports(self) -> None:
        self.add_input_port("list", DataType.LIST, required=False)
        self.add_input_port("item", DataType.ANY, required=False)
        self.add_output_port("contains", DataType.BOOLEAN)
        self.add_output_port("index", DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            lst = _resolve_list_param(self, context)

            # Resolve item from port or parameter
            item = self.get_input_value("item")
            if item is None:
                item_param = self.get_parameter("item")
                if isinstance(item_param, str) and item_param:
                    resolved = context.get_variable(item_param)
                    item = resolved if resolved is not None else item_param
                else:
                    item = item_param

            if not isinstance(lst, (list, tuple)):
                raise ValueError("Input is not a list")

            contains = item in lst
            index = lst.index(item) if contains else -1

            self.set_output_value("contains", contains)
            self.set_output_value("index", index)
            return {
                "success": True,
                "data": {"contains": contains, "index": index},
                "next_nodes": [],
            }
        except Exception as e:
            logger.error(f"List contains failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


@properties()  # Input port driven
@node(category="data")
class ListSliceNode(BaseNode):
    """Node that gets a slice of a list."""

    # @category: data
    # @requires: none
    # @ports: list, start, end -> result

    def __init__(self, node_id: str, name: str = "List Slice", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ListSliceNode"

    def _define_ports(self) -> None:
        self.add_input_port("list", DataType.LIST, required=False)
        # start defaults to 0, end defaults to None (end of list)
        self.add_input_port("start", DataType.INTEGER, required=False)
        self.add_input_port("end", DataType.INTEGER, required=False)
        self.add_output_port("result", DataType.LIST)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            lst = _resolve_list_param(self, context)

            # Resolve start from port or parameter
            start = self.get_input_value("start")
            if start is None:
                start_param = self.get_parameter("start", 0)
                if isinstance(start_param, str) and start_param:
                    resolved = context.get_variable(start_param)
                    start = int(resolved) if resolved is not None else 0
                else:
                    start = start_param

            # Resolve end from port or parameter
            end = self.get_input_value("end")
            if end is None:
                end_param = self.get_parameter("end")
                if isinstance(end_param, str) and end_param:
                    resolved = context.get_variable(end_param)
                    end = int(resolved) if resolved is not None else None
                else:
                    end = end_param

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


@properties(
    PropertyDef(
        "separator",
        PropertyType.STRING,
        default=", ",
        label="Separator",
        tooltip="Separator to use when joining items",
    ),
)
@node(category="data")
class ListJoinNode(BaseNode):
    """Node that joins a list into a string."""

    # @category: data
    # @requires: none
    # @ports: list, separator -> result

    def __init__(self, node_id: str, name: str = "List Join", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ListJoinNode"

    def _define_ports(self) -> None:
        self.add_input_port("list", DataType.LIST, required=False)
        # separator defaults to ", "
        self.add_input_port("separator", DataType.STRING, required=False)
        self.add_output_port("result", DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            lst = _resolve_list_param(self, context)

            # Resolve separator from port or parameter
            separator = self.get_input_value("separator")
            if separator is None:
                sep_param = self.get_parameter("separator", ", ")
                if isinstance(sep_param, str):
                    # Check if it's a variable reference (no literal commas/spaces)
                    resolved = context.get_variable(sep_param)
                    separator = str(resolved) if resolved is not None else sep_param
                else:
                    separator = str(sep_param) if sep_param else ", "

            if not isinstance(lst, (list, tuple)):
                raise ValueError("Input is not a list")

            result = separator.join(str(item) for item in lst)

            self.set_output_value("result", result)
            return {"success": True, "data": {"result": result}, "next_nodes": []}
        except Exception as e:
            logger.error(f"List join failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


@properties(
    PropertyDef(
        "reverse",
        PropertyType.BOOLEAN,
        default=False,
        label="Reverse",
        tooltip="Sort in descending order",
    ),
    PropertyDef(
        "key_path",
        PropertyType.STRING,
        default="",
        label="Key Path",
        tooltip="Dot-separated path to sort by (for dict items)",
    ),
)
@node(category="data")
class ListSortNode(BaseNode):
    """Node that sorts a list."""

    # @category: data
    # @requires: none
    # @ports: list, reverse, key_path -> result

    def __init__(self, node_id: str, name: str = "List Sort", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ListSortNode"

    def _define_ports(self) -> None:
        self.add_input_port("list", DataType.LIST, required=False)
        # reverse defaults to False, key_path defaults to ""
        self.add_input_port("reverse", DataType.BOOLEAN, required=False)
        self.add_input_port("key_path", DataType.STRING, required=False)
        self.add_output_port("result", DataType.LIST)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            lst = _resolve_list_param(self, context)

            # Resolve reverse from port or parameter
            reverse = self.get_input_value("reverse")
            if reverse is None:
                rev_param = self.get_parameter("reverse", False)
                if isinstance(rev_param, str) and rev_param:
                    resolved = context.get_variable(rev_param)
                    reverse = bool(resolved) if resolved is not None else False
                else:
                    reverse = bool(rev_param) if rev_param is not None else False

            # Resolve key_path from port or parameter
            key_path = self.get_input_value("key_path")
            if key_path is None:
                kp_param = self.get_parameter("key_path", "")
                if isinstance(kp_param, str) and kp_param:
                    resolved = context.get_variable(kp_param)
                    key_path = str(resolved) if resolved is not None else kp_param
                else:
                    key_path = str(kp_param) if kp_param else ""

            if not isinstance(lst, (list, tuple)):
                raise ValueError("Input is not a list")

            result = list(lst)

            if key_path:

                def get_key(item: Any) -> Any:
                    current = item
                    for part in key_path.split("."):
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


@properties()  # Input port driven
@node(category="data")
class ListReverseNode(BaseNode):
    """Node that reverses a list."""

    # @category: data
    # @requires: none
    # @ports: list -> result

    def __init__(self, node_id: str, name: str = "List Reverse", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ListReverseNode"

    def _define_ports(self) -> None:
        self.add_input_port("list", DataType.LIST, required=False)
        self.add_output_port("result", DataType.LIST)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            lst = _resolve_list_param(self, context)

            if not isinstance(lst, (list, tuple)):
                raise ValueError("Input is not a list")

            result = list(reversed(lst))

            self.set_output_value("result", result)
            return {"success": True, "data": {"result": result}, "next_nodes": []}
        except Exception as e:
            logger.error(f"List reverse failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


@properties()  # Input port driven
@node(category="data")
class ListUniqueNode(BaseNode):
    """Node that removes duplicates from a list."""

    # @category: data
    # @requires: none
    # @ports: list -> result

    def __init__(self, node_id: str, name: str = "List Unique", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ListUniqueNode"

    def _define_ports(self) -> None:
        self.add_input_port("list", DataType.LIST, required=False)
        self.add_output_port("result", DataType.LIST)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            lst = _resolve_list_param(self, context)

            if not isinstance(lst, (list, tuple)):
                raise ValueError("Input is not a list")

            # Preserve order while removing duplicates
            seen: set = set()
            result = []
            for item in lst:
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


@properties(
    PropertyDef(
        "condition",
        PropertyType.CHOICE,
        default="is_not_none",
        choices=[
            "equals",
            "not_equals",
            "contains",
            "starts_with",
            "ends_with",
            "greater_than",
            "less_than",
            "is_not_none",
            "is_none",
            "is_truthy",
            "is_falsy",
        ],
        label="Condition",
        tooltip="Condition to filter by",
    ),
    PropertyDef(
        "key_path",
        PropertyType.STRING,
        default="",
        label="Key Path",
        tooltip="Dot-separated path to compare (for dict items)",
    ),
)
@node(category="data")
class ListFilterNode(BaseNode):
    """Node that filters a list based on a condition."""

    # @category: data
    # @requires: none
    # @ports: list, condition, value, key_path -> result, removed

    def __init__(self, node_id: str, name: str = "List Filter", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ListFilterNode"

    def _define_ports(self) -> None:
        self.add_input_port("list", DataType.LIST, required=False)
        # condition defaults to "is_not_none", value is optional, key_path defaults to ""
        self.add_input_port("condition", DataType.STRING, required=False)
        self.add_input_port("value", DataType.ANY, required=False)
        self.add_input_port("key_path", DataType.STRING, required=False)
        self.add_output_port("result", DataType.LIST)
        self.add_output_port("removed", DataType.LIST)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            lst = _resolve_list_param(self, context)

            # Resolve condition from port or parameter
            condition = self.get_input_value("condition")
            if condition is None:
                cond_param = self.get_parameter("condition", "is_not_none")
                if isinstance(cond_param, str) and cond_param:
                    resolved = context.get_variable(cond_param)
                    condition = str(resolved) if resolved is not None else cond_param
                else:
                    condition = "is_not_none"

            # Resolve compare value from port or parameter
            compare_value = self.get_input_value("value")
            if compare_value is None:
                val_param = self.get_parameter("value")
                if isinstance(val_param, str) and val_param:
                    resolved = context.get_variable(val_param)
                    compare_value = resolved if resolved is not None else val_param
                else:
                    compare_value = val_param

            # Resolve key_path from port or parameter
            key_path = self.get_input_value("key_path")
            if key_path is None:
                kp_param = self.get_parameter("key_path", "")
                if isinstance(kp_param, str) and kp_param:
                    resolved = context.get_variable(kp_param)
                    key_path = str(resolved) if resolved is not None else kp_param
                else:
                    key_path = ""

            if not isinstance(lst, (list, tuple)):
                raise ValueError("Input is not a list")

            def get_item_value(item: Any) -> Any:
                if not key_path:
                    return item
                current = item
                for part in key_path.split("."):
                    if isinstance(current, dict) and part in current:
                        current = current[part]
                    else:
                        return None
                return current

            def matches(item: Any) -> bool:
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
            return {
                "success": True,
                "data": {"result": result, "removed": removed},
                "next_nodes": [],
            }
        except Exception as e:
            logger.error(f"List filter failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


@properties(
    PropertyDef(
        "transform",
        PropertyType.CHOICE,
        default="to_string",
        choices=[
            "get_property",
            "to_string",
            "to_int",
            "to_float",
            "to_upper",
            "to_lower",
            "trim",
            "length",
        ],
        label="Transform",
        tooltip="Transformation to apply to each item",
    ),
    PropertyDef(
        "key_path",
        PropertyType.STRING,
        default="",
        label="Key Path",
        tooltip="Dot-separated path to extract (for dict items)",
    ),
)
@node(category="data")
class ListMapNode(BaseNode):
    """Node that transforms each item in a list."""

    # @category: data
    # @requires: none
    # @ports: list, transform, key_path -> result

    def __init__(self, node_id: str, name: str = "List Map", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ListMapNode"

    def _define_ports(self) -> None:
        self.add_input_port("list", DataType.LIST, required=False)
        # transform defaults to "to_string", key_path defaults to ""
        self.add_input_port("transform", DataType.STRING, required=False)
        self.add_input_port("key_path", DataType.STRING, required=False)
        self.add_output_port("result", DataType.LIST)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            lst = _resolve_list_param(self, context)

            # Resolve transform from port or parameter
            transform = self.get_input_value("transform")
            if transform is None:
                tf_param = self.get_parameter("transform", "to_string")
                if isinstance(tf_param, str) and tf_param:
                    resolved = context.get_variable(tf_param)
                    transform = str(resolved) if resolved is not None else tf_param
                else:
                    transform = "to_string"

            # Resolve key_path from port or parameter
            key_path = self.get_input_value("key_path")
            if key_path is None:
                kp_param = self.get_parameter("key_path", "")
                if isinstance(kp_param, str) and kp_param:
                    resolved = context.get_variable(kp_param)
                    key_path = str(resolved) if resolved is not None else kp_param
                else:
                    key_path = ""

            if not isinstance(lst, (list, tuple)):
                raise ValueError("Input is not a list")

            def apply_transform(item: Any) -> Any:
                val = item
                if key_path:
                    for part in key_path.split("."):
                        if isinstance(val, dict) and part in val:
                            val = val[part]
                        else:
                            val = None
                            break

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


@properties(
    PropertyDef(
        "operation",
        PropertyType.CHOICE,
        default="sum",
        choices=[
            "sum",
            "product",
            "min",
            "max",
            "avg",
            "count",
            "first",
            "last",
            "join",
        ],
        label="Operation",
        tooltip="Reduction operation to perform",
    ),
    PropertyDef(
        "key_path",
        PropertyType.STRING,
        default="",
        label="Key Path",
        tooltip="Dot-separated path to values (for dict items)",
    ),
)
@node(category="data")
class ListReduceNode(BaseNode):
    """Node that reduces a list to a single value."""

    # @category: data
    # @requires: none
    # @ports: list, operation, key_path, initial -> result

    def __init__(self, node_id: str, name: str = "List Reduce", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ListReduceNode"

    def _define_ports(self) -> None:
        self.add_input_port("list", DataType.LIST, required=False)
        # operation defaults to "sum", key_path defaults to "", initial is optional
        self.add_input_port("operation", DataType.STRING, required=False)
        self.add_input_port("key_path", DataType.STRING, required=False)
        self.add_input_port("initial", DataType.ANY, required=False)
        self.add_output_port("result", DataType.ANY)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            lst = _resolve_list_param(self, context)

            # Resolve operation from port or parameter
            operation = self.get_input_value("operation")
            if operation is None:
                op_param = self.get_parameter("operation", "sum")
                if isinstance(op_param, str) and op_param:
                    resolved = context.get_variable(op_param)
                    operation = str(resolved) if resolved is not None else op_param
                else:
                    operation = "sum"

            # Resolve key_path from port or parameter
            key_path = self.get_input_value("key_path")
            if key_path is None:
                kp_param = self.get_parameter("key_path", "")
                if isinstance(kp_param, str) and kp_param:
                    resolved = context.get_variable(kp_param)
                    key_path = str(resolved) if resolved is not None else kp_param
                else:
                    key_path = ""

            # Resolve initial from port or parameter
            initial = self.get_input_value("initial")
            if initial is None:
                init_param = self.get_parameter("initial")
                if isinstance(init_param, str) and init_param:
                    resolved = context.get_variable(init_param)
                    initial = resolved if resolved is not None else init_param
                else:
                    initial = init_param

            if not isinstance(lst, (list, tuple)):
                raise ValueError("Input is not a list")

            # Extract values if key_path specified
            if key_path:
                values = []
                for item in lst:
                    val = item
                    for part in key_path.split("."):
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
                result = (
                    initial
                    if initial is not None
                    else (
                        0 if operation in ["sum", "product", "avg", "count"] else None
                    )
                )
            elif operation == "sum":
                result = sum(float(v) for v in values)
            elif operation == "product":
                result = 1.0
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


@properties(
    PropertyDef(
        "depth",
        PropertyType.INTEGER,
        default=1,
        min_value=1,
        label="Depth",
        tooltip="How many levels to flatten",
    ),
)
@node(category="data")
class ListFlattenNode(BaseNode):
    """Node that flattens a nested list."""

    # @category: data
    # @requires: none
    # @ports: list, depth -> result

    def __init__(self, node_id: str, name: str = "List Flatten", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ListFlattenNode"

    def _define_ports(self) -> None:
        self.add_input_port("list", DataType.LIST, required=False)
        self.add_input_port("depth", DataType.INTEGER, required=False)
        self.add_output_port("result", DataType.LIST)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            lst = _resolve_list_param(self, context)

            # Resolve depth from port or parameter
            depth = self.get_input_value("depth")
            if depth is None:
                depth_param = self.get_parameter("depth", 1)
                if isinstance(depth_param, str) and depth_param:
                    resolved = context.get_variable(depth_param)
                    depth = int(resolved) if resolved is not None else 1
                else:
                    depth = int(depth_param) if depth_param is not None else 1
            else:
                depth = int(depth)

            if not isinstance(lst, (list, tuple)):
                raise ValueError("Input is not a list")

            def flatten(
                items: Any, current_depth: int, max_depth: int = MAX_FLATTEN_DEPTH
            ) -> list:
                if current_depth > max_depth:
                    raise ValueError(
                        f"Flatten depth {current_depth} exceeds maximum {max_depth}. "
                        "Possible circular reference."
                    )
                result = []
                for item in items:
                    if isinstance(item, (list, tuple)) and current_depth > 0:
                        result.extend(flatten(item, current_depth - 1, max_depth))
                    else:
                        result.append(item)
                return result

            result = flatten(lst, depth, MAX_FLATTEN_DEPTH)

            self.set_output_value("result", result)
            return {"success": True, "data": {"result": result}, "next_nodes": []}
        except Exception as e:
            logger.error(f"List flatten failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


__all__ = [
    "CreateListNode",
    "ListGetItemNode",
    "ListLengthNode",
    "ListAppendNode",
    "ListContainsNode",
    "ListSliceNode",
    "ListJoinNode",
    "ListSortNode",
    "ListReverseNode",
    "ListUniqueNode",
    "ListFilterNode",
    "ListMapNode",
    "ListReduceNode",
    "ListFlattenNode",
]
