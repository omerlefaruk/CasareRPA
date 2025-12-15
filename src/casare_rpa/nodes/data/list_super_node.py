"""
Super Node for CasareRPA List Operations.

This module provides a consolidated "List Super Node" that replaces 14
atomic list nodes with action-based dynamic ports and properties.

ListSuperNode (14 operations):
    Create/Access:
        - Create: Create a new list from items
        - Get Item: Get item at index
        - Length: Get list length
        - Contains: Check if list contains item

    Modify:
        - Append: Add item(s) to list
        - Slice: Extract sublist
        - Sort: Sort list
        - Reverse: Reverse list order
        - Unique: Remove duplicates

    Transform:
        - Filter: Filter items by condition
        - Map: Transform each item
        - Reduce: Reduce to single value
        - Flatten: Flatten nested lists
        - Join: Join items to string
"""

from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Awaitable, List

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


class ListAction(str, Enum):
    """Actions available in ListSuperNode."""

    # Create/Access operations
    CREATE = "Create List"
    GET_ITEM = "Get Item"
    LENGTH = "Length"
    CONTAINS = "Contains"

    # Modify operations
    APPEND = "Append"
    SLICE = "Slice"
    SORT = "Sort"
    REVERSE = "Reverse"
    UNIQUE = "Unique"

    # Transform operations
    FILTER = "Filter"
    MAP = "Map"
    REDUCE = "Reduce"
    FLATTEN = "Flatten"
    JOIN = "Join"


# Port schema for dynamic port visibility
LIST_PORT_SCHEMA = DynamicPortSchema()

# Create List ports
LIST_PORT_SCHEMA.register(
    ListAction.CREATE.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("item1", DataType.ANY),
            PortDef("item2", DataType.ANY),
            PortDef("item3", DataType.ANY),
        ],
        outputs=[
            PortDef("list", DataType.LIST),
            PortDef("length", DataType.INTEGER),
        ],
    ),
)

# Get Item ports
LIST_PORT_SCHEMA.register(
    ListAction.GET_ITEM.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("list", DataType.LIST),
            PortDef("index", DataType.INTEGER),
        ],
        outputs=[
            PortDef("item", DataType.ANY),
            PortDef("found", DataType.BOOLEAN),
        ],
    ),
)

# Length ports
LIST_PORT_SCHEMA.register(
    ListAction.LENGTH.value,
    ActionPortConfig.create(
        inputs=[PortDef("list", DataType.LIST)],
        outputs=[
            PortDef("length", DataType.INTEGER),
            PortDef("is_empty", DataType.BOOLEAN),
        ],
    ),
)

# Contains ports
LIST_PORT_SCHEMA.register(
    ListAction.CONTAINS.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("list", DataType.LIST),
            PortDef("item", DataType.ANY),
        ],
        outputs=[
            PortDef("contains", DataType.BOOLEAN),
            PortDef("index", DataType.INTEGER),
            PortDef("count", DataType.INTEGER),
        ],
    ),
)

# Append ports
LIST_PORT_SCHEMA.register(
    ListAction.APPEND.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("list", DataType.LIST),
            PortDef("item", DataType.ANY),
        ],
        outputs=[
            PortDef("list", DataType.LIST),
            PortDef("length", DataType.INTEGER),
        ],
    ),
)

# Slice ports
LIST_PORT_SCHEMA.register(
    ListAction.SLICE.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("list", DataType.LIST),
            PortDef("start", DataType.INTEGER),
            PortDef("end", DataType.INTEGER),
        ],
        outputs=[
            PortDef("slice", DataType.LIST),
            PortDef("length", DataType.INTEGER),
        ],
    ),
)

# Sort ports
LIST_PORT_SCHEMA.register(
    ListAction.SORT.value,
    ActionPortConfig.create(
        inputs=[PortDef("list", DataType.LIST)],
        outputs=[
            PortDef("sorted", DataType.LIST),
            PortDef("length", DataType.INTEGER),
        ],
    ),
)

# Reverse ports
LIST_PORT_SCHEMA.register(
    ListAction.REVERSE.value,
    ActionPortConfig.create(
        inputs=[PortDef("list", DataType.LIST)],
        outputs=[
            PortDef("reversed", DataType.LIST),
            PortDef("length", DataType.INTEGER),
        ],
    ),
)

# Unique ports
LIST_PORT_SCHEMA.register(
    ListAction.UNIQUE.value,
    ActionPortConfig.create(
        inputs=[PortDef("list", DataType.LIST)],
        outputs=[
            PortDef("unique", DataType.LIST),
            PortDef("length", DataType.INTEGER),
            PortDef("duplicates_removed", DataType.INTEGER),
        ],
    ),
)

# Filter ports
LIST_PORT_SCHEMA.register(
    ListAction.FILTER.value,
    ActionPortConfig.create(
        inputs=[PortDef("list", DataType.LIST)],
        outputs=[
            PortDef("filtered", DataType.LIST),
            PortDef("rejected", DataType.LIST),
            PortDef("length", DataType.INTEGER),
        ],
    ),
)

# Map ports
LIST_PORT_SCHEMA.register(
    ListAction.MAP.value,
    ActionPortConfig.create(
        inputs=[PortDef("list", DataType.LIST)],
        outputs=[
            PortDef("mapped", DataType.LIST),
            PortDef("length", DataType.INTEGER),
        ],
    ),
)

# Reduce ports
LIST_PORT_SCHEMA.register(
    ListAction.REDUCE.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("list", DataType.LIST),
            PortDef("initial", DataType.ANY),
        ],
        outputs=[
            PortDef("result", DataType.ANY),
        ],
    ),
)

# Flatten ports
LIST_PORT_SCHEMA.register(
    ListAction.FLATTEN.value,
    ActionPortConfig.create(
        inputs=[PortDef("list", DataType.LIST)],
        outputs=[
            PortDef("flattened", DataType.LIST),
            PortDef("length", DataType.INTEGER),
        ],
    ),
)

# Join ports
LIST_PORT_SCHEMA.register(
    ListAction.JOIN.value,
    ActionPortConfig.create(
        inputs=[PortDef("list", DataType.LIST)],
        outputs=[
            PortDef("result", DataType.STRING),
        ],
    ),
)


# Action groups for display_when
CREATE_ACCESS_ACTIONS = [
    ListAction.CREATE.value,
    ListAction.GET_ITEM.value,
    ListAction.LENGTH.value,
    ListAction.CONTAINS.value,
]

MODIFY_ACTIONS = [
    ListAction.APPEND.value,
    ListAction.SLICE.value,
    ListAction.SORT.value,
    ListAction.REVERSE.value,
    ListAction.UNIQUE.value,
]

TRANSFORM_ACTIONS = [
    ListAction.FILTER.value,
    ListAction.MAP.value,
    ListAction.REDUCE.value,
    ListAction.FLATTEN.value,
    ListAction.JOIN.value,
]

EXPRESSION_ACTIONS = [
    ListAction.FILTER.value,
    ListAction.MAP.value,
    ListAction.REDUCE.value,
]


@properties(
    # === ESSENTIAL: Action selector (always visible) ===
    PropertyDef(
        "action",
        PropertyType.CHOICE,
        default=ListAction.GET_ITEM.value,
        label="Action",
        tooltip="List operation to perform",
        essential=True,
        order=0,
        choices=[a.value for a in ListAction],
    ),
    # === GET ITEM OPTIONS ===
    PropertyDef(
        "default_value",
        PropertyType.STRING,
        default="",
        label="Default Value",
        tooltip="Value to return if index is out of bounds",
        order=10,
        display_when={"action": [ListAction.GET_ITEM.value]},
    ),
    PropertyDef(
        "negative_index",
        PropertyType.BOOLEAN,
        default=True,
        label="Allow Negative Index",
        tooltip="Allow negative indices (e.g., -1 for last item)",
        order=11,
        display_when={"action": [ListAction.GET_ITEM.value]},
    ),
    # === SLICE OPTIONS ===
    PropertyDef(
        "step",
        PropertyType.INTEGER,
        default=1,
        label="Step",
        tooltip="Step value for slice (e.g., 2 for every other item)",
        order=10,
        display_when={"action": [ListAction.SLICE.value]},
    ),
    # === SORT OPTIONS ===
    PropertyDef(
        "descending",
        PropertyType.BOOLEAN,
        default=False,
        label="Descending",
        tooltip="Sort in descending order",
        order=10,
        display_when={"action": [ListAction.SORT.value]},
    ),
    PropertyDef(
        "sort_key",
        PropertyType.STRING,
        default="",
        label="Sort Key",
        tooltip="Property name for sorting objects (leave empty for direct comparison)",
        order=11,
        display_when={"action": [ListAction.SORT.value]},
    ),
    # === UNIQUE OPTIONS ===
    PropertyDef(
        "preserve_order",
        PropertyType.BOOLEAN,
        default=True,
        label="Preserve Order",
        tooltip="Keep original order of items",
        order=10,
        display_when={"action": [ListAction.UNIQUE.value]},
    ),
    # === FILTER/MAP/REDUCE OPTIONS ===
    PropertyDef(
        "expression",
        PropertyType.TEXT,
        default="",
        label="Expression",
        tooltip="Python expression (use 'x' for item, 'i' for index)",
        placeholder="x > 0 or x['status'] == 'active'",
        order=10,
        display_when={"action": EXPRESSION_ACTIONS},
    ),
    PropertyDef(
        "reduce_operation",
        PropertyType.CHOICE,
        default="sum",
        choices=["sum", "product", "min", "max", "concat", "custom"],
        label="Operation",
        tooltip="Built-in reduce operation or 'custom' for expression",
        order=11,
        display_when={"action": [ListAction.REDUCE.value]},
    ),
    # === FLATTEN OPTIONS ===
    PropertyDef(
        "depth",
        PropertyType.INTEGER,
        default=-1,
        label="Depth",
        tooltip="Maximum depth to flatten (-1 for unlimited)",
        order=10,
        display_when={"action": [ListAction.FLATTEN.value]},
    ),
    # === JOIN OPTIONS ===
    PropertyDef(
        "separator",
        PropertyType.STRING,
        default=", ",
        label="Separator",
        tooltip="String to place between items",
        order=10,
        display_when={"action": [ListAction.JOIN.value]},
    ),
    # === APPEND OPTIONS ===
    PropertyDef(
        "extend",
        PropertyType.BOOLEAN,
        default=False,
        label="Extend (Add Multiple)",
        tooltip="If item is a list, add each element separately",
        order=10,
        display_when={"action": [ListAction.APPEND.value]},
    ),
    PropertyDef(
        "position",
        PropertyType.CHOICE,
        default="end",
        choices=["end", "start", "index"],
        label="Position",
        tooltip="Where to insert the item(s)",
        order=11,
        display_when={"action": [ListAction.APPEND.value]},
    ),
    PropertyDef(
        "insert_index",
        PropertyType.INTEGER,
        default=0,
        label="Insert Index",
        tooltip="Index to insert at (when position=index)",
        order=12,
        display_when={"action": [ListAction.APPEND.value]},
    ),
)
@node(category="data")
class ListSuperNode(BaseNode):
    """
    Unified list operations node.

    Consolidates 14 atomic list operations into a single configurable node.
    Select an action from the dropdown to see relevant properties and ports.

    Actions:
        Create/Access:
        - Create List: Create a new list from items
        - Get Item: Get item at index
        - Length: Get list length
        - Contains: Check if list contains item

        Modify:
        - Append: Add item(s) to list
        - Slice: Extract sublist
        - Sort: Sort list items
        - Reverse: Reverse list order
        - Unique: Remove duplicate items

        Transform:
        - Filter: Filter items by expression
        - Map: Transform each item
        - Reduce: Reduce to single value
        - Flatten: Flatten nested lists
        - Join: Join items to string
    """

    def __init__(self, node_id: str, name: str = "List", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ListSuperNode"

    def _define_ports(self) -> None:
        """Define ports based on current action."""
        # Default to Get Item ports
        self.add_input_port("list", DataType.LIST)
        self.add_input_port("index", DataType.INTEGER)
        self.add_output_port("item", DataType.ANY)
        self.add_output_port("found", DataType.BOOLEAN)

    async def execute(self, context: "IExecutionContext") -> ExecutionResult:
        """Execute the selected list action."""
        self.status = NodeStatus.RUNNING

        action = self.get_parameter("action", ListAction.GET_ITEM.value)

        # Map actions to handlers
        handlers: dict[
            str, Callable[["IExecutionContext"], Awaitable[ExecutionResult]]
        ] = {
            ListAction.CREATE.value: self._execute_create,
            ListAction.GET_ITEM.value: self._execute_get_item,
            ListAction.LENGTH.value: self._execute_length,
            ListAction.CONTAINS.value: self._execute_contains,
            ListAction.APPEND.value: self._execute_append,
            ListAction.SLICE.value: self._execute_slice,
            ListAction.SORT.value: self._execute_sort,
            ListAction.REVERSE.value: self._execute_reverse,
            ListAction.UNIQUE.value: self._execute_unique,
            ListAction.FILTER.value: self._execute_filter,
            ListAction.MAP.value: self._execute_map,
            ListAction.REDUCE.value: self._execute_reduce,
            ListAction.FLATTEN.value: self._execute_flatten,
            ListAction.JOIN.value: self._execute_join,
        }

        handler = handlers.get(action)
        if not handler:
            self.status = NodeStatus.ERROR
            return {"success": False, "error": f"Unknown action: {action}"}

        try:
            return await handler(context)
        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Error in ListSuperNode ({action}): {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    # === CREATE/ACCESS ACTION HANDLERS ===

    async def _execute_create(self, context: "IExecutionContext") -> ExecutionResult:
        """Create a new list from items."""
        items = []

        # Collect items from item1, item2, item3 ports
        for port_name in ["item1", "item2", "item3"]:
            value = self.get_input_value(port_name, context)
            if value is not None:
                items.append(value)

        self.set_output_value("list", items)
        self.set_output_value("length", len(items))
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"length": len(items)},
            "next_nodes": ["exec_out"],
        }

    async def _execute_get_item(self, context: "IExecutionContext") -> ExecutionResult:
        """Get item at index."""
        input_list = self.get_input_value("list", context)
        if not isinstance(input_list, list):
            input_list = []

        index = self.get_input_value("index", context)
        if index is None:
            index = 0
        index = int(index)

        default_value = self.get_parameter("default_value", "")
        allow_negative = self.get_parameter("negative_index", True)

        # Handle negative indices
        if index < 0 and not allow_negative:
            self.set_output_value("item", default_value if default_value else None)
            self.set_output_value("found", False)
            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"found": False},
                "next_nodes": ["exec_out"],
            }

        try:
            item = input_list[index]
            found = True
        except IndexError:
            item = default_value if default_value else None
            found = False

        self.set_output_value("item", item)
        self.set_output_value("found", found)
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"found": found},
            "next_nodes": ["exec_out"],
        }

    async def _execute_length(self, context: "IExecutionContext") -> ExecutionResult:
        """Get list length."""
        input_list = self.get_input_value("list", context)
        if not isinstance(input_list, list):
            input_list = []

        length = len(input_list)
        is_empty = length == 0

        self.set_output_value("length", length)
        self.set_output_value("is_empty", is_empty)
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"length": length, "is_empty": is_empty},
            "next_nodes": ["exec_out"],
        }

    async def _execute_contains(self, context: "IExecutionContext") -> ExecutionResult:
        """Check if list contains item."""
        input_list = self.get_input_value("list", context)
        if not isinstance(input_list, list):
            input_list = []

        item = self.get_input_value("item", context)

        contains = item in input_list
        index = input_list.index(item) if contains else -1
        count = input_list.count(item)

        self.set_output_value("contains", contains)
        self.set_output_value("index", index)
        self.set_output_value("count", count)
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"contains": contains, "count": count},
            "next_nodes": ["exec_out"],
        }

    # === MODIFY ACTION HANDLERS ===

    async def _execute_append(self, context: "IExecutionContext") -> ExecutionResult:
        """Add item(s) to list."""
        input_list = self.get_input_value("list", context)
        if not isinstance(input_list, list):
            input_list = []
        else:
            input_list = list(input_list)  # Create a copy

        item = self.get_input_value("item", context)
        extend = self.get_parameter("extend", False)
        position = self.get_parameter("position", "end")
        insert_index = self.get_parameter("insert_index", 0)

        if extend and isinstance(item, list):
            items_to_add = item
        else:
            items_to_add = [item]

        if position == "start":
            input_list = items_to_add + input_list
        elif position == "index":
            for i, it in enumerate(items_to_add):
                input_list.insert(insert_index + i, it)
        else:  # end
            input_list.extend(items_to_add)

        self.set_output_value("list", input_list)
        self.set_output_value("length", len(input_list))
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"length": len(input_list)},
            "next_nodes": ["exec_out"],
        }

    async def _execute_slice(self, context: "IExecutionContext") -> ExecutionResult:
        """Extract sublist."""
        input_list = self.get_input_value("list", context)
        if not isinstance(input_list, list):
            input_list = []

        start = self.get_input_value("start", context)
        end = self.get_input_value("end", context)
        step = self.get_parameter("step", 1)

        start = int(start) if start is not None else None
        end = int(end) if end is not None else None
        step = int(step) if step else 1

        result = input_list[start:end:step]

        self.set_output_value("slice", result)
        self.set_output_value("length", len(result))
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"length": len(result)},
            "next_nodes": ["exec_out"],
        }

    async def _execute_sort(self, context: "IExecutionContext") -> ExecutionResult:
        """Sort list."""
        input_list = self.get_input_value("list", context)
        if not isinstance(input_list, list):
            input_list = []
        else:
            input_list = list(input_list)  # Create a copy

        descending = self.get_parameter("descending", False)
        sort_key = self.get_parameter("sort_key", "")

        if sort_key:
            # Sort by property
            def key_fn(x: Any) -> Any:
                if isinstance(x, dict):
                    return x.get(sort_key, "")
                return getattr(x, sort_key, "")

            try:
                result = sorted(input_list, key=key_fn, reverse=descending)
            except (TypeError, AttributeError):
                result = sorted(input_list, reverse=descending)
        else:
            try:
                result = sorted(input_list, reverse=descending)
            except TypeError:
                # Mixed types - convert to strings
                result = sorted(input_list, key=str, reverse=descending)

        self.set_output_value("sorted", result)
        self.set_output_value("length", len(result))
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"length": len(result)},
            "next_nodes": ["exec_out"],
        }

    async def _execute_reverse(self, context: "IExecutionContext") -> ExecutionResult:
        """Reverse list order."""
        input_list = self.get_input_value("list", context)
        if not isinstance(input_list, list):
            input_list = []

        result = list(reversed(input_list))

        self.set_output_value("reversed", result)
        self.set_output_value("length", len(result))
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"length": len(result)},
            "next_nodes": ["exec_out"],
        }

    async def _execute_unique(self, context: "IExecutionContext") -> ExecutionResult:
        """Remove duplicates."""
        input_list = self.get_input_value("list", context)
        if not isinstance(input_list, list):
            input_list = []

        preserve_order = self.get_parameter("preserve_order", True)
        original_length = len(input_list)

        if preserve_order:
            # Preserve order using dict.fromkeys (Python 3.7+)
            seen: set[Any] = set()
            result = []
            for item in input_list:
                try:
                    key = (
                        item
                        if not isinstance(item, dict)
                        else tuple(sorted(item.items()))
                    )
                    if key not in seen:
                        seen.add(key)
                        result.append(item)
                except TypeError:
                    # Unhashable - use slower approach
                    if item not in result:
                        result.append(item)
        else:
            try:
                result = list(set(input_list))
            except TypeError:
                # Unhashable items - fall back to preserve_order approach
                seen = set()
                result = []
                for item in input_list:
                    if item not in result:
                        result.append(item)

        duplicates_removed = original_length - len(result)

        self.set_output_value("unique", result)
        self.set_output_value("length", len(result))
        self.set_output_value("duplicates_removed", duplicates_removed)
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"length": len(result), "duplicates_removed": duplicates_removed},
            "next_nodes": ["exec_out"],
        }

    # === TRANSFORM ACTION HANDLERS ===

    async def _execute_filter(self, context: "IExecutionContext") -> ExecutionResult:
        """Filter items by expression."""
        input_list = self.get_input_value("list", context)
        if not isinstance(input_list, list):
            input_list = []

        expression = self.get_parameter("expression", "")
        if not expression:
            expression = "True"  # No filter - keep all

        filtered = []
        rejected = []

        for i, x in enumerate(input_list):
            try:
                # Create safe evaluation context
                eval_context = {"x": x, "i": i, "item": x, "index": i}
                result = eval(expression, {"__builtins__": {}}, eval_context)
                if result:
                    filtered.append(x)
                else:
                    rejected.append(x)
            except Exception as e:
                logger.warning(f"Filter expression error on item {i}: {e}")
                rejected.append(x)

        self.set_output_value("filtered", filtered)
        self.set_output_value("rejected", rejected)
        self.set_output_value("length", len(filtered))
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"filtered": len(filtered), "rejected": len(rejected)},
            "next_nodes": ["exec_out"],
        }

    async def _execute_map(self, context: "IExecutionContext") -> ExecutionResult:
        """Transform each item."""
        input_list = self.get_input_value("list", context)
        if not isinstance(input_list, list):
            input_list = []

        expression = self.get_parameter("expression", "")
        if not expression:
            expression = "x"  # Identity function

        result = []
        for i, x in enumerate(input_list):
            try:
                eval_context = {"x": x, "i": i, "item": x, "index": i}
                mapped = eval(expression, {"__builtins__": {}}, eval_context)
                result.append(mapped)
            except Exception as e:
                logger.warning(f"Map expression error on item {i}: {e}")
                result.append(x)  # Keep original on error

        self.set_output_value("mapped", result)
        self.set_output_value("length", len(result))
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"length": len(result)},
            "next_nodes": ["exec_out"],
        }

    async def _execute_reduce(self, context: "IExecutionContext") -> ExecutionResult:
        """Reduce to single value."""
        input_list = self.get_input_value("list", context)
        if not isinstance(input_list, list):
            input_list = []

        initial = self.get_input_value("initial", context)
        operation = self.get_parameter("reduce_operation", "sum")
        expression = self.get_parameter("expression", "")

        if not input_list:
            self.set_output_value("result", initial)
            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"result": initial},
                "next_nodes": ["exec_out"],
            }

        if operation == "sum":
            result = sum(input_list, initial if initial is not None else 0)
        elif operation == "product":
            result = initial if initial is not None else 1
            for item in input_list:
                result *= item
        elif operation == "min":
            result = min(input_list)
        elif operation == "max":
            result = max(input_list)
        elif operation == "concat":
            if isinstance(input_list[0], str):
                result = "".join(input_list)
            else:
                result = []
                for item in input_list:
                    if isinstance(item, list):
                        result.extend(item)
                    else:
                        result.append(item)
        elif operation == "custom" and expression:
            # Custom reduce with expression
            accumulator = initial if initial is not None else input_list[0]
            items = input_list if initial is not None else input_list[1:]
            for i, x in enumerate(items):
                try:
                    eval_context = {
                        "acc": accumulator,
                        "x": x,
                        "i": i,
                        "accumulator": accumulator,
                        "item": x,
                        "index": i,
                    }
                    accumulator = eval(expression, {"__builtins__": {}}, eval_context)
                except Exception as e:
                    logger.warning(f"Reduce expression error: {e}")
            result = accumulator
        else:
            result = input_list

        self.set_output_value("result", result)
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"result": result},
            "next_nodes": ["exec_out"],
        }

    async def _execute_flatten(self, context: "IExecutionContext") -> ExecutionResult:
        """Flatten nested lists."""
        input_list = self.get_input_value("list", context)
        if not isinstance(input_list, list):
            input_list = []

        depth = self.get_parameter("depth", -1)

        def flatten_recursive(lst: list, current_depth: int) -> list:
            result = []
            for item in lst:
                if isinstance(item, list) and (depth < 0 or current_depth < depth):
                    result.extend(flatten_recursive(item, current_depth + 1))
                else:
                    result.append(item)
            return result

        result = flatten_recursive(input_list, 0)

        self.set_output_value("flattened", result)
        self.set_output_value("length", len(result))
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"length": len(result)},
            "next_nodes": ["exec_out"],
        }

    async def _execute_join(self, context: "IExecutionContext") -> ExecutionResult:
        """Join items to string."""
        input_list = self.get_input_value("list", context)
        if not isinstance(input_list, list):
            input_list = []

        separator = self.get_parameter("separator", ", ")
        separator = context.resolve_value(separator)

        result = separator.join(str(item) for item in input_list)

        self.set_output_value("result", result)
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"result": result[:100] + "..." if len(result) > 100 else result},
            "next_nodes": ["exec_out"],
        }

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


__all__ = [
    "ListSuperNode",
    "ListAction",
    "LIST_PORT_SCHEMA",
]
