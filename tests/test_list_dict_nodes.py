"""
Tests for List and Dict operation nodes.

Tests cover filtering, mapping, sorting, reducing lists,
and dictionary get/set/merge/keys/values operations.
"""

import pytest

from casare_rpa.nodes.data_operation_nodes import (
    # List operations
    ListLengthNode,
    ListAppendNode,
    ListContainsNode,
    ListSliceNode,
    ListJoinNode,
    ListSortNode,
    ListReverseNode,
    ListUniqueNode,
    ListFilterNode,
    ListMapNode,
    ListReduceNode,
    ListFlattenNode,
    # Dict operations
    DictGetNode,
    DictSetNode,
    DictRemoveNode,
    DictMergeNode,
    DictKeysNode,
    DictValuesNode,
    DictHasKeyNode,
    CreateDictNode,
    DictToJsonNode,
    DictItemsNode,
)
from casare_rpa.core.types import NodeStatus


# ==================== LIST OPERATION TESTS ====================

class TestListLengthNode:
    """Tests for ListLength node."""

    @pytest.mark.asyncio
    async def test_list_length_basic(self, execution_context):
        """Test getting length of a list."""
        node = ListLengthNode(node_id="len_1")
        node.set_input_value("list", [1, 2, 3, 4, 5])

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("length") == 5

    @pytest.mark.asyncio
    async def test_list_length_empty(self, execution_context):
        """Test getting length of empty list."""
        node = ListLengthNode(node_id="len_1")
        node.set_input_value("list", [])

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("length") == 0


class TestListAppendNode:
    """Tests for ListAppend node."""

    @pytest.mark.asyncio
    async def test_append_item(self, execution_context):
        """Test appending item to list."""
        node = ListAppendNode(node_id="append_1")
        node.set_input_value("list", [1, 2, 3])
        node.set_input_value("item", 4)

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == [1, 2, 3, 4]

    @pytest.mark.asyncio
    async def test_append_to_empty(self, execution_context):
        """Test appending to empty list."""
        node = ListAppendNode(node_id="append_1")
        node.set_input_value("list", [])
        node.set_input_value("item", "first")

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == ["first"]


class TestListContainsNode:
    """Tests for ListContains node."""

    @pytest.mark.asyncio
    async def test_contains_found(self, execution_context):
        """Test finding item in list."""
        node = ListContainsNode(node_id="contains_1")
        node.set_input_value("list", ["apple", "banana", "cherry"])
        node.set_input_value("item", "banana")

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("contains") is True
        assert node.get_output_value("index") == 1

    @pytest.mark.asyncio
    async def test_contains_not_found(self, execution_context):
        """Test item not in list."""
        node = ListContainsNode(node_id="contains_1")
        node.set_input_value("list", ["apple", "banana", "cherry"])
        node.set_input_value("item", "orange")

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("contains") is False
        assert node.get_output_value("index") == -1


class TestListSliceNode:
    """Tests for ListSlice node."""

    @pytest.mark.asyncio
    async def test_slice_basic(self, execution_context):
        """Test basic list slicing."""
        node = ListSliceNode(node_id="slice_1")
        node.set_input_value("list", [0, 1, 2, 3, 4, 5])
        node.set_input_value("start", 1)
        node.set_input_value("end", 4)

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_slice_from_start(self, execution_context):
        """Test slicing from start."""
        node = ListSliceNode(node_id="slice_1")
        node.set_input_value("list", [0, 1, 2, 3, 4])
        node.set_input_value("start", 0)
        node.set_input_value("end", 3)

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == [0, 1, 2]


class TestListJoinNode:
    """Tests for ListJoin node."""

    @pytest.mark.asyncio
    async def test_join_strings(self, execution_context):
        """Test joining strings."""
        node = ListJoinNode(node_id="join_1")
        node.set_input_value("list", ["a", "b", "c"])
        node.set_input_value("separator", "-")

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == "a-b-c"

    @pytest.mark.asyncio
    async def test_join_with_comma(self, execution_context):
        """Test joining with comma."""
        node = ListJoinNode(node_id="join_1")
        node.set_input_value("list", [1, 2, 3])
        node.set_input_value("separator", ", ")

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == "1, 2, 3"


class TestListSortNode:
    """Tests for ListSort node."""

    @pytest.mark.asyncio
    async def test_sort_numbers(self, execution_context):
        """Test sorting numbers."""
        node = ListSortNode(node_id="sort_1")
        node.set_input_value("list", [3, 1, 4, 1, 5, 9, 2, 6])
        node.set_input_value("reverse", False)

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == [1, 1, 2, 3, 4, 5, 6, 9]

    @pytest.mark.asyncio
    async def test_sort_reverse(self, execution_context):
        """Test sorting in reverse."""
        node = ListSortNode(node_id="sort_1")
        node.set_input_value("list", [1, 2, 3, 4, 5])
        node.set_input_value("reverse", True)

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == [5, 4, 3, 2, 1]

    @pytest.mark.asyncio
    async def test_sort_by_key(self, execution_context):
        """Test sorting by key path."""
        node = ListSortNode(node_id="sort_1")
        node.set_input_value("list", [
            {"name": "Charlie", "age": 30},
            {"name": "Alice", "age": 25},
            {"name": "Bob", "age": 35},
        ])
        node.set_input_value("key_path", "age")

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        sorted_list = node.get_output_value("result")
        assert sorted_list[0]["name"] == "Alice"
        assert sorted_list[2]["name"] == "Bob"


class TestListReverseNode:
    """Tests for ListReverse node."""

    @pytest.mark.asyncio
    async def test_reverse_list(self, execution_context):
        """Test reversing a list."""
        node = ListReverseNode(node_id="reverse_1")
        node.set_input_value("list", [1, 2, 3, 4, 5])

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == [5, 4, 3, 2, 1]


class TestListUniqueNode:
    """Tests for ListUnique node."""

    @pytest.mark.asyncio
    async def test_remove_duplicates(self, execution_context):
        """Test removing duplicates."""
        node = ListUniqueNode(node_id="unique_1")
        node.set_input_value("list", [1, 2, 2, 3, 3, 3, 4])

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == [1, 2, 3, 4]

    @pytest.mark.asyncio
    async def test_unique_strings(self, execution_context):
        """Test unique strings preserving order."""
        node = ListUniqueNode(node_id="unique_1")
        node.set_input_value("list", ["a", "b", "a", "c", "b", "d"])

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == ["a", "b", "c", "d"]


class TestListFilterNode:
    """Tests for ListFilter node."""

    @pytest.mark.asyncio
    async def test_filter_equals(self, execution_context):
        """Test filtering by equality."""
        node = ListFilterNode(node_id="filter_1")
        node.set_input_value("list", [1, 2, 3, 2, 4, 2])
        node.set_input_value("condition", "equals")
        node.set_input_value("value", 2)

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == [2, 2, 2]
        assert node.get_output_value("removed") == [1, 3, 4]

    @pytest.mark.asyncio
    async def test_filter_greater_than(self, execution_context):
        """Test filtering greater than."""
        node = ListFilterNode(node_id="filter_1")
        node.set_input_value("list", [1, 5, 3, 8, 2, 9])
        node.set_input_value("condition", "greater_than")
        node.set_input_value("value", 4)

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == [5, 8, 9]

    @pytest.mark.asyncio
    async def test_filter_by_key_path(self, execution_context):
        """Test filtering by nested property."""
        node = ListFilterNode(node_id="filter_1")
        node.set_input_value("list", [
            {"name": "Alice", "active": True},
            {"name": "Bob", "active": False},
            {"name": "Charlie", "active": True},
        ])
        node.set_input_value("condition", "equals")
        node.set_input_value("value", True)
        node.set_input_value("key_path", "active")

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        filtered = node.get_output_value("result")
        assert len(filtered) == 2
        assert filtered[0]["name"] == "Alice"
        assert filtered[1]["name"] == "Charlie"

    @pytest.mark.asyncio
    async def test_filter_is_not_none(self, execution_context):
        """Test filtering out None values."""
        node = ListFilterNode(node_id="filter_1")
        node.set_input_value("list", [1, None, 2, None, 3])
        node.set_input_value("condition", "is_not_none")

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == [1, 2, 3]


class TestListMapNode:
    """Tests for ListMap node."""

    @pytest.mark.asyncio
    async def test_map_to_string(self, execution_context):
        """Test mapping to strings."""
        node = ListMapNode(node_id="map_1")
        node.set_input_value("list", [1, 2, 3])
        node.set_input_value("transform", "to_string")

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == ["1", "2", "3"]

    @pytest.mark.asyncio
    async def test_map_to_upper(self, execution_context):
        """Test mapping to uppercase."""
        node = ListMapNode(node_id="map_1")
        node.set_input_value("list", ["hello", "world"])
        node.set_input_value("transform", "to_upper")

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == ["HELLO", "WORLD"]

    @pytest.mark.asyncio
    async def test_map_extract_property(self, execution_context):
        """Test extracting property from objects."""
        node = ListMapNode(node_id="map_1")
        node.set_input_value("list", [
            {"name": "Alice", "age": 25},
            {"name": "Bob", "age": 30},
        ])
        node.set_input_value("transform", "get_property")
        node.set_input_value("key_path", "name")

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == ["Alice", "Bob"]


class TestListReduceNode:
    """Tests for ListReduce node."""

    @pytest.mark.asyncio
    async def test_reduce_sum(self, execution_context):
        """Test reducing with sum."""
        node = ListReduceNode(node_id="reduce_1")
        node.set_input_value("list", [1, 2, 3, 4, 5])
        node.set_input_value("operation", "sum")

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == 15.0

    @pytest.mark.asyncio
    async def test_reduce_avg(self, execution_context):
        """Test reducing with average."""
        node = ListReduceNode(node_id="reduce_1")
        node.set_input_value("list", [10, 20, 30])
        node.set_input_value("operation", "avg")

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == 20.0

    @pytest.mark.asyncio
    async def test_reduce_min_max(self, execution_context):
        """Test reducing with min/max."""
        node_min = ListReduceNode(node_id="reduce_min")
        node_min.set_input_value("list", [5, 2, 8, 1, 9])
        node_min.set_input_value("operation", "min")

        node_max = ListReduceNode(node_id="reduce_max")
        node_max.set_input_value("list", [5, 2, 8, 1, 9])
        node_max.set_input_value("operation", "max")

        await node_min.execute(execution_context)
        await node_max.execute(execution_context)

        assert node_min.get_output_value("result") == 1
        assert node_max.get_output_value("result") == 9

    @pytest.mark.asyncio
    async def test_reduce_by_key_path(self, execution_context):
        """Test reducing by nested property."""
        node = ListReduceNode(node_id="reduce_1")
        node.set_input_value("list", [
            {"product": "A", "price": 10},
            {"product": "B", "price": 20},
            {"product": "C", "price": 30},
        ])
        node.set_input_value("operation", "sum")
        node.set_input_value("key_path", "price")

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == 60.0


class TestListFlattenNode:
    """Tests for ListFlatten node."""

    @pytest.mark.asyncio
    async def test_flatten_nested(self, execution_context):
        """Test flattening nested list."""
        node = ListFlattenNode(node_id="flatten_1")
        node.set_input_value("list", [[1, 2], [3, 4], [5, 6]])
        node.set_input_value("depth", 1)

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == [1, 2, 3, 4, 5, 6]

    @pytest.mark.asyncio
    async def test_flatten_deep(self, execution_context):
        """Test deep flattening."""
        node = ListFlattenNode(node_id="flatten_1")
        node.set_input_value("list", [[[1, 2]], [[3, 4]], [[5, 6]]])
        node.set_input_value("depth", 2)

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == [1, 2, 3, 4, 5, 6]


# ==================== DICT OPERATION TESTS ====================

class TestDictGetNode:
    """Tests for DictGet node."""

    @pytest.mark.asyncio
    async def test_get_existing_key(self, execution_context):
        """Test getting existing key."""
        node = DictGetNode(node_id="get_1")
        node.set_input_value("dict", {"name": "Alice", "age": 25})
        node.set_input_value("key", "name")

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("value") == "Alice"
        assert node.get_output_value("found") is True

    @pytest.mark.asyncio
    async def test_get_missing_key_with_default(self, execution_context):
        """Test getting missing key with default."""
        node = DictGetNode(node_id="get_1")
        node.set_input_value("dict", {"name": "Alice"})
        node.set_input_value("key", "age")
        node.set_input_value("default", 0)

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("value") == 0
        assert node.get_output_value("found") is False


class TestDictSetNode:
    """Tests for DictSet node."""

    @pytest.mark.asyncio
    async def test_set_new_key(self, execution_context):
        """Test setting new key."""
        node = DictSetNode(node_id="set_1")
        node.set_input_value("dict", {"name": "Alice"})
        node.set_input_value("key", "age")
        node.set_input_value("value", 25)

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        output = node.get_output_value("result")
        assert output["name"] == "Alice"
        assert output["age"] == 25

    @pytest.mark.asyncio
    async def test_update_existing_key(self, execution_context):
        """Test updating existing key."""
        node = DictSetNode(node_id="set_1")
        node.set_input_value("dict", {"name": "Alice", "age": 25})
        node.set_input_value("key", "age")
        node.set_input_value("value", 26)

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result")["age"] == 26


class TestDictRemoveNode:
    """Tests for DictRemove node."""

    @pytest.mark.asyncio
    async def test_remove_key(self, execution_context):
        """Test removing a key."""
        node = DictRemoveNode(node_id="remove_1")
        node.set_input_value("dict", {"name": "Alice", "age": 25, "city": "NYC"})
        node.set_input_value("key", "city")

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        output = node.get_output_value("result")
        assert "city" not in output
        assert node.get_output_value("removed_value") == "NYC"


class TestDictMergeNode:
    """Tests for DictMerge node."""

    @pytest.mark.asyncio
    async def test_merge_dicts(self, execution_context):
        """Test merging two dicts."""
        node = DictMergeNode(node_id="merge_1")
        node.set_input_value("dict_1", {"a": 1, "b": 2})
        node.set_input_value("dict_2", {"c": 3, "d": 4})

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        output = node.get_output_value("result")
        assert output == {"a": 1, "b": 2, "c": 3, "d": 4}

    @pytest.mark.asyncio
    async def test_merge_with_override(self, execution_context):
        """Test merging with overlapping keys."""
        node = DictMergeNode(node_id="merge_1")
        node.set_input_value("dict_1", {"a": 1, "b": 2})
        node.set_input_value("dict_2", {"b": 99, "c": 3})

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        output = node.get_output_value("result")
        assert output["b"] == 99  # dict_2 value wins


class TestDictKeysNode:
    """Tests for DictKeys node."""

    @pytest.mark.asyncio
    async def test_get_keys(self, execution_context):
        """Test getting all keys."""
        node = DictKeysNode(node_id="keys_1")
        node.set_input_value("dict", {"name": "Alice", "age": 25, "city": "NYC"})

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        keys = node.get_output_value("keys")
        assert set(keys) == {"name", "age", "city"}
        assert node.get_output_value("count") == 3


class TestDictValuesNode:
    """Tests for DictValues node."""

    @pytest.mark.asyncio
    async def test_get_values(self, execution_context):
        """Test getting all values."""
        node = DictValuesNode(node_id="values_1")
        node.set_input_value("dict", {"a": 1, "b": 2, "c": 3})

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        values = node.get_output_value("values")
        assert set(values) == {1, 2, 3}
        assert node.get_output_value("count") == 3


class TestDictHasKeyNode:
    """Tests for DictHasKey node."""

    @pytest.mark.asyncio
    async def test_has_key_true(self, execution_context):
        """Test key exists."""
        node = DictHasKeyNode(node_id="haskey_1")
        node.set_input_value("dict", {"name": "Alice"})
        node.set_input_value("key", "name")

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("has_key") is True

    @pytest.mark.asyncio
    async def test_has_key_false(self, execution_context):
        """Test key doesn't exist."""
        node = DictHasKeyNode(node_id="haskey_1")
        node.set_input_value("dict", {"name": "Alice"})
        node.set_input_value("key", "age")

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("has_key") is False


class TestCreateDictNode:
    """Tests for CreateDict node."""

    @pytest.mark.asyncio
    async def test_create_dict(self, execution_context):
        """Test creating a dict."""
        node = CreateDictNode(node_id="create_1")
        node.set_input_value("key_1", "name")
        node.set_input_value("value_1", "Alice")
        node.set_input_value("key_2", "age")
        node.set_input_value("value_2", 25)

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        output = node.get_output_value("dict")
        assert output == {"name": "Alice", "age": 25}


class TestDictToJsonNode:
    """Tests for DictToJson node."""

    @pytest.mark.asyncio
    async def test_to_json(self, execution_context):
        """Test converting to JSON string."""
        node = DictToJsonNode(node_id="tojson_1")
        node.set_input_value("dict", {"name": "Alice", "age": 25})

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        json_str = node.get_output_value("json_string")
        assert '"name"' in json_str
        assert '"Alice"' in json_str

    @pytest.mark.asyncio
    async def test_to_json_with_indent(self, execution_context):
        """Test converting to formatted JSON."""
        node = DictToJsonNode(node_id="tojson_1")
        node.set_input_value("dict", {"a": 1})
        node.set_input_value("indent", 2)

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        json_str = node.get_output_value("json_string")
        assert "\n" in json_str  # Formatted output has newlines


class TestDictItemsNode:
    """Tests for DictItems node."""

    @pytest.mark.asyncio
    async def test_get_items(self, execution_context):
        """Test getting key-value pairs."""
        node = DictItemsNode(node_id="items_1")
        node.set_input_value("dict", {"a": 1, "b": 2})

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        items = node.get_output_value("items")
        assert len(items) == 2
        assert {"key": "a", "value": 1} in items
        assert {"key": "b", "value": 2} in items
        assert node.get_output_value("count") == 2


# ==================== INTEGRATION TESTS ====================

class TestListDictIntegration:
    """Integration tests combining list and dict operations."""

    @pytest.mark.asyncio
    async def test_filter_map_reduce_pipeline(self, execution_context):
        """Test a pipeline of list operations."""
        data = [
            {"product": "A", "price": 10, "active": True},
            {"product": "B", "price": 20, "active": False},
            {"product": "C", "price": 30, "active": True},
            {"product": "D", "price": 40, "active": True},
        ]

        # Filter: only active products
        filter_node = ListFilterNode(node_id="filter")
        filter_node.set_input_value("list", data)
        filter_node.set_input_value("condition", "equals")
        filter_node.set_input_value("value", True)
        filter_node.set_input_value("key_path", "active")
        await filter_node.execute(execution_context)
        filtered = filter_node.get_output_value("result")

        # Map: extract prices
        map_node = ListMapNode(node_id="map")
        map_node.set_input_value("list", filtered)
        map_node.set_input_value("transform", "get_property")
        map_node.set_input_value("key_path", "price")
        await map_node.execute(execution_context)
        prices = map_node.get_output_value("result")

        # Reduce: sum prices
        reduce_node = ListReduceNode(node_id="reduce")
        reduce_node.set_input_value("list", prices)
        reduce_node.set_input_value("operation", "sum")
        await reduce_node.execute(execution_context)
        total = reduce_node.get_output_value("result")

        # 10 + 30 + 40 = 80 (B is excluded)
        assert total == 80.0

    @pytest.mark.asyncio
    async def test_dict_manipulation_workflow(self, execution_context):
        """Test dict manipulation workflow."""
        # Create initial dict
        create_node = CreateDictNode(node_id="create")
        create_node.set_input_value("key_1", "name")
        create_node.set_input_value("value_1", "Product X")
        create_node.set_input_value("key_2", "price")
        create_node.set_input_value("value_2", 100)
        await create_node.execute(execution_context)
        product = create_node.get_output_value("dict")

        # Add category
        set_node = DictSetNode(node_id="set")
        set_node.set_input_value("dict", product)
        set_node.set_input_value("key", "category")
        set_node.set_input_value("value", "Electronics")
        await set_node.execute(execution_context)
        product = set_node.get_output_value("result")

        # Merge with additional info
        merge_node = DictMergeNode(node_id="merge")
        merge_node.set_input_value("dict_1", product)
        merge_node.set_input_value("dict_2", {"in_stock": True, "quantity": 50})
        await merge_node.execute(execution_context)
        final = merge_node.get_output_value("result")

        assert final["name"] == "Product X"
        assert final["price"] == 100
        assert final["category"] == "Electronics"
        assert final["in_stock"] is True
        assert final["quantity"] == 50
