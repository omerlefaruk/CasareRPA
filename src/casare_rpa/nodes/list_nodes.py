"""
CasareRPA - List Operation Nodes

Provides nodes for list/array manipulation including:
- Creation and indexing
- Slicing and filtering
- Sorting and transformation
- Reduction operations
"""

from typing import Any, Dict
from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType, ExecutionResult, PortType
from casare_rpa.infrastructure.execution import ExecutionContext


@executable_node
class CreateListNode(BaseNode):
    """Node that creates a list from inputs."""

    def __init__(self, node_id: str, name: str = "Create List", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "CreateListNode"

    def _define_ports(self) -> None:
        self.add_input_port("item_1", PortType.INPUT, DataType.ANY)
        self.add_input_port("item_2", PortType.INPUT, DataType.ANY)
        self.add_input_port("item_3", PortType.INPUT, DataType.ANY)
        self.add_output_port("list", PortType.OUTPUT, DataType.LIST)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            result = []

            for i in range(1, 4):
                key = f"item_{i}"
                val = self.get_parameter(key)
                if val is not None:
                    result.append(val)

            self.set_output_value("list", result)
            return {"success": True, "data": {"list": result}, "next_nodes": []}
        except Exception as e:
            logger.error(f"Create list failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


@executable_node
class ListGetItemNode(BaseNode):
    """Node that gets an item from a list by index."""

    def __init__(self, node_id: str, name: str = "List Get Item", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ListGetItemNode"

    def _define_ports(self) -> None:
        self.add_input_port("list", PortType.INPUT, DataType.LIST)
        self.add_input_port("index", PortType.INPUT, DataType.INTEGER)
        self.add_output_port("item", PortType.OUTPUT, DataType.ANY)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            lst = self.get_parameter("list", [])
            idx = int(self.get_parameter("index", 0))

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


@executable_node
class ListLengthNode(BaseNode):
    """Node that returns the length of a list."""

    def __init__(self, node_id: str, name: str = "List Length", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ListLengthNode"

    def _define_ports(self) -> None:
        self.add_input_port("list", PortType.INPUT, DataType.LIST)
        self.add_output_port("length", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            lst = self.get_parameter("list", [])
            if not isinstance(lst, (list, tuple)):
                raise ValueError("Input is not a list")

            length = len(lst)
            self.set_output_value("length", length)
            return {"success": True, "data": {"length": length}, "next_nodes": []}
        except Exception as e:
            logger.error(f"List length failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


@executable_node
class ListAppendNode(BaseNode):
    """Node that appends an item to a list."""

    def __init__(self, node_id: str, name: str = "List Append", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ListAppendNode"

    def _define_ports(self) -> None:
        self.add_input_port("list", PortType.INPUT, DataType.LIST)
        self.add_input_port("item", PortType.INPUT, DataType.ANY)
        self.add_output_port("result", PortType.OUTPUT, DataType.LIST)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            lst = self.get_parameter("list", [])
            item = self.get_parameter("item")

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


@executable_node
class ListContainsNode(BaseNode):
    """Node that checks if a list contains an item."""

    def __init__(self, node_id: str, name: str = "List Contains", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ListContainsNode"

    def _define_ports(self) -> None:
        self.add_input_port("list", PortType.INPUT, DataType.LIST)
        self.add_input_port("item", PortType.INPUT, DataType.ANY)
        self.add_output_port("contains", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("index", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            lst = self.get_parameter("list", [])
            item = self.get_parameter("item")

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


@executable_node
class ListSliceNode(BaseNode):
    """Node that gets a slice of a list."""

    def __init__(self, node_id: str, name: str = "List Slice", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ListSliceNode"

    def _define_ports(self) -> None:
        self.add_input_port("list", PortType.INPUT, DataType.LIST)
        self.add_input_port("start", PortType.INPUT, DataType.INTEGER)
        self.add_input_port("end", PortType.INPUT, DataType.INTEGER)
        self.add_output_port("result", PortType.OUTPUT, DataType.LIST)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            lst = self.get_parameter("list", [])
            start = self.get_parameter("start", 0)
            end = self.get_parameter("end")

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


@executable_node
@node_schema(
    PropertyDef(
        "separator",
        PropertyType.STRING,
        default=", ",
        label="Separator",
        tooltip="Separator to use when joining items",
    ),
)
class ListJoinNode(BaseNode):
    """Node that joins a list into a string."""

    def __init__(self, node_id: str, name: str = "List Join", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ListJoinNode"

    def _define_ports(self) -> None:
        self.add_input_port("list", PortType.INPUT, DataType.LIST)
        self.add_input_port("separator", PortType.INPUT, DataType.STRING)
        self.add_output_port("result", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            lst = self.get_parameter("list", [])
            separator = self.get_parameter("separator", ", ")

            if not isinstance(lst, (list, tuple)):
                raise ValueError("Input is not a list")

            result = separator.join(str(item) for item in lst)

            self.set_output_value("result", result)
            return {"success": True, "data": {"result": result}, "next_nodes": []}
        except Exception as e:
            logger.error(f"List join failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


@executable_node
@node_schema(
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
class ListSortNode(BaseNode):
    """Node that sorts a list."""

    def __init__(self, node_id: str, name: str = "List Sort", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ListSortNode"

    def _define_ports(self) -> None:
        self.add_input_port("list", PortType.INPUT, DataType.LIST)
        self.add_input_port("reverse", PortType.INPUT, DataType.BOOLEAN)
        self.add_input_port("key_path", PortType.INPUT, DataType.STRING)
        self.add_output_port("result", PortType.OUTPUT, DataType.LIST)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            lst = self.get_parameter("list", [])
            reverse = self.get_parameter("reverse", False)
            key_path = self.get_parameter("key_path", "")

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


@executable_node
class ListReverseNode(BaseNode):
    """Node that reverses a list."""

    def __init__(self, node_id: str, name: str = "List Reverse", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ListReverseNode"

    def _define_ports(self) -> None:
        self.add_input_port("list", PortType.INPUT, DataType.LIST)
        self.add_output_port("result", PortType.OUTPUT, DataType.LIST)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            lst = self.get_parameter("list", [])

            if not isinstance(lst, (list, tuple)):
                raise ValueError("Input is not a list")

            result = list(reversed(lst))

            self.set_output_value("result", result)
            return {"success": True, "data": {"result": result}, "next_nodes": []}
        except Exception as e:
            logger.error(f"List reverse failed: {e}")
            self.error_message = str(e)
            return {"success": False, "error": str(e), "next_nodes": []}


@executable_node
class ListUniqueNode(BaseNode):
    """Node that removes duplicates from a list."""

    def __init__(self, node_id: str, name: str = "List Unique", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ListUniqueNode"

    def _define_ports(self) -> None:
        self.add_input_port("list", PortType.INPUT, DataType.LIST)
        self.add_output_port("result", PortType.OUTPUT, DataType.LIST)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            lst = self.get_parameter("list", [])

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


@executable_node
@node_schema(
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
@executable_node
class ListFilterNode(BaseNode):
    """Node that filters a list based on a condition."""

    def __init__(self, node_id: str, name: str = "List Filter", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ListFilterNode"

    def _define_ports(self) -> None:
        self.add_input_port("list", PortType.INPUT, DataType.LIST)
        self.add_input_port("condition", PortType.INPUT, DataType.STRING)
        self.add_input_port("value", PortType.INPUT, DataType.ANY)
        self.add_input_port("key_path", PortType.INPUT, DataType.STRING)
        self.add_output_port("result", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("removed", PortType.OUTPUT, DataType.LIST)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            lst = self.get_parameter("list", [])
            condition = self.get_parameter("condition", "is_not_none")
            compare_value = self.get_parameter("value")
            key_path = self.get_parameter("key_path", "")

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


@executable_node
@node_schema(
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
@executable_node
class ListMapNode(BaseNode):
    """Node that transforms each item in a list."""

    def __init__(self, node_id: str, name: str = "List Map", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ListMapNode"

    def _define_ports(self) -> None:
        self.add_input_port("list", PortType.INPUT, DataType.LIST)
        self.add_input_port("transform", PortType.INPUT, DataType.STRING)
        self.add_input_port("key_path", PortType.INPUT, DataType.STRING)
        self.add_output_port("result", PortType.OUTPUT, DataType.LIST)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            lst = self.get_parameter("list", [])
            transform = self.get_parameter("transform", "to_string")
            key_path = self.get_parameter("key_path", "")

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


@executable_node
@node_schema(
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
@executable_node
class ListReduceNode(BaseNode):
    """Node that reduces a list to a single value."""

    def __init__(self, node_id: str, name: str = "List Reduce", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ListReduceNode"

    def _define_ports(self) -> None:
        self.add_input_port("list", PortType.INPUT, DataType.LIST)
        self.add_input_port("operation", PortType.INPUT, DataType.STRING)
        self.add_input_port("key_path", PortType.INPUT, DataType.STRING)
        self.add_input_port("initial", PortType.INPUT, DataType.ANY)
        self.add_output_port("result", PortType.OUTPUT, DataType.ANY)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            lst = self.get_parameter("list", [])
            operation = self.get_parameter("operation", "sum")
            key_path = self.get_parameter("key_path", "")
            initial = self.get_parameter("initial")

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


@executable_node
@node_schema(
    PropertyDef(
        "depth",
        PropertyType.INTEGER,
        default=1,
        min_value=1,
        label="Depth",
        tooltip="How many levels to flatten",
    ),
)
class ListFlattenNode(BaseNode):
    """Node that flattens a nested list."""

    def __init__(self, node_id: str, name: str = "List Flatten", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ListFlattenNode"

    def _define_ports(self) -> None:
        self.add_input_port("list", PortType.INPUT, DataType.LIST)
        self.add_input_port("depth", PortType.INPUT, DataType.INTEGER)
        self.add_output_port("result", PortType.OUTPUT, DataType.LIST)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            lst = self.get_parameter("list", [])
            depth = int(self.get_parameter("depth", 1))

            if not isinstance(lst, (list, tuple)):
                raise ValueError("Input is not a list")

            def flatten(items: Any, current_depth: int) -> list:
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
