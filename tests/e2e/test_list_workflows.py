"""
CasareRPA - E2E Tests for List Operation Workflows.

Tests list operations including:
- Creation and indexing
- Append and prepend
- Length and contains
- Slicing
- Sorting and reversing
- Filtering and mapping
- Reduce operations
- Unique and flatten
- Joining
"""

import pytest

from .helpers.workflow_builder import WorkflowBuilder


@pytest.mark.asyncio
@pytest.mark.e2e
class TestListCreation:
    """Tests for list creation operations."""

    async def test_create_empty_list(self) -> None:
        """Test creating empty list."""
        result = await (
            WorkflowBuilder("Create Empty List")
            .add_start()
            .add_create_list()
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_create_list_with_items(self) -> None:
        """Test creating list with initial items."""
        result = await (
            WorkflowBuilder("Create List With Items")
            .add_start()
            .add_create_list(item_1=1, item_2=2, item_3=3)
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_create_list_mixed_types(self) -> None:
        """Test creating list with mixed types."""
        result = await (
            WorkflowBuilder("Create List Mixed")
            .add_start()
            .add_create_list(item_1="hello", item_2=42, item_3=True)
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestListAppend:
    """Tests for list append operations."""

    async def test_list_append(self) -> None:
        """Test appending item to list."""
        result = await (
            WorkflowBuilder("List Append")
            .add_start()
            .add_set_variable("items", [1, 2])
            .add_list_append("items", 3)
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_list_append_multiple(self) -> None:
        """Test appending multiple items sequentially."""
        result = await (
            WorkflowBuilder("List Append Multiple")
            .add_start()
            .add_set_variable("items", [])
            .add_list_append("items", "a")
            .add_list_append("items", "b")
            .add_list_append("items", "c")
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestListIndexing:
    """Tests for list indexing operations."""

    async def test_list_get_index(self) -> None:
        """Test getting item by positive index."""
        result = await (
            WorkflowBuilder("List Get Index")
            .add_start()
            .add_set_variable("items", [10, 20, 30])
            .add_list_get_item("{{items}}", index=1)
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_list_get_negative_index(self) -> None:
        """Test getting item by negative index (from end)."""
        result = await (
            WorkflowBuilder("List Get Negative")
            .add_start()
            .add_set_variable("items", [10, 20, 30])
            .add_list_get_item("{{items}}", index=-1)
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_list_get_first(self) -> None:
        """Test getting first item."""
        result = await (
            WorkflowBuilder("List Get First")
            .add_start()
            .add_set_variable("items", ["a", "b", "c"])
            .add_list_get_item("{{items}}", index=0)
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestListLength:
    """Tests for list length operations."""

    async def test_list_length(self) -> None:
        """Test getting list length."""
        result = await (
            WorkflowBuilder("List Length")
            .add_start()
            .add_set_variable("items", [1, 2, 3, 4, 5])
            .add_list_length("{{items}}")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_list_length_empty(self) -> None:
        """Test getting length of empty list."""
        result = await (
            WorkflowBuilder("List Length Empty")
            .add_start()
            .add_set_variable("items", [])
            .add_list_length("{{items}}")
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestListContains:
    """Tests for list contains operations."""

    async def test_list_contains_found(self) -> None:
        """Test checking if list contains item (found)."""
        result = await (
            WorkflowBuilder("List Contains Found")
            .add_start()
            .add_set_variable("items", [1, 2, 3])
            .add_list_contains("{{items}}", item=2)
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_list_contains_not_found(self) -> None:
        """Test checking if list contains item (not found)."""
        result = await (
            WorkflowBuilder("List Contains Not Found")
            .add_start()
            .add_set_variable("items", [1, 2, 3])
            .add_list_contains("{{items}}", item=5)
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_list_contains_string(self) -> None:
        """Test checking if list contains string."""
        result = await (
            WorkflowBuilder("List Contains String")
            .add_start()
            .add_set_variable("items", ["apple", "banana", "cherry"])
            .add_list_contains("{{items}}", item="banana")
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestListSlice:
    """Tests for list slicing operations."""

    async def test_list_slice(self) -> None:
        """Test slicing list with start and end."""
        result = await (
            WorkflowBuilder("List Slice")
            .add_start()
            .add_set_variable("items", [1, 2, 3, 4, 5])
            .add_list_slice("{{items}}", start=1, end=4)
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_list_slice_from_start(self) -> None:
        """Test slicing from start to position."""
        result = await (
            WorkflowBuilder("List Slice From Start")
            .add_start()
            .add_set_variable("items", [1, 2, 3, 4, 5])
            .add_list_slice("{{items}}", start=0, end=3)
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_list_slice_to_end(self) -> None:
        """Test slicing from position to end."""
        result = await (
            WorkflowBuilder("List Slice To End")
            .add_start()
            .add_set_variable("items", [1, 2, 3, 4, 5])
            .add_list_slice("{{items}}", start=2)
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestListReverse:
    """Tests for list reverse operations."""

    async def test_list_reverse(self) -> None:
        """Test reversing list."""
        result = await (
            WorkflowBuilder("List Reverse")
            .add_start()
            .add_set_variable("items", [1, 2, 3])
            .add_list_reverse("{{items}}")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_list_reverse_strings(self) -> None:
        """Test reversing list of strings."""
        result = await (
            WorkflowBuilder("List Reverse Strings")
            .add_start()
            .add_set_variable("items", ["a", "b", "c", "d"])
            .add_list_reverse("{{items}}")
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestListSort:
    """Tests for list sorting operations."""

    async def test_list_sort(self) -> None:
        """Test sorting list ascending."""
        result = await (
            WorkflowBuilder("List Sort")
            .add_start()
            .add_set_variable("items", [3, 1, 4, 1, 5])
            .add_list_sort("{{items}}")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_list_sort_descending(self) -> None:
        """Test sorting list descending."""
        result = await (
            WorkflowBuilder("List Sort Descending")
            .add_start()
            .add_set_variable("items", [3, 1, 4, 1, 5])
            .add_list_sort("{{items}}", reverse=True)
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_list_sort_strings(self) -> None:
        """Test sorting list of strings."""
        result = await (
            WorkflowBuilder("List Sort Strings")
            .add_start()
            .add_set_variable("items", ["cherry", "apple", "banana"])
            .add_list_sort("{{items}}")
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestListFilter:
    """Tests for list filtering operations."""

    async def test_list_filter_greater_than(self) -> None:
        """Test filtering list where items greater than value."""
        result = await (
            WorkflowBuilder("List Filter Greater")
            .add_start()
            .add_set_variable("items", [1, 2, 3, 4, 5])
            .add_list_filter("{{items}}", condition="greater_than", value=2)
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_list_filter_equals(self) -> None:
        """Test filtering list where items equal value."""
        result = await (
            WorkflowBuilder("List Filter Equals")
            .add_start()
            .add_set_variable("items", ["a", "b", "a", "c", "a"])
            .add_list_filter("{{items}}", condition="equals", value="a")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_list_filter_not_none(self) -> None:
        """Test filtering out None values."""
        result = await (
            WorkflowBuilder("List Filter Not None")
            .add_start()
            .add_set_variable("items", [1, None, 2, None, 3])
            .add_list_filter("{{items}}", condition="is_not_none")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_list_filter_contains(self) -> None:
        """Test filtering strings containing substring."""
        result = await (
            WorkflowBuilder("List Filter Contains")
            .add_start()
            .add_set_variable("items", ["hello world", "goodbye", "hello there"])
            .add_list_filter("{{items}}", condition="contains", value="hello")
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestListMap:
    """Tests for list map/transform operations."""

    async def test_list_map_to_string(self) -> None:
        """Test mapping items to strings."""
        result = await (
            WorkflowBuilder("List Map To String")
            .add_start()
            .add_set_variable("items", [1, 2, 3])
            .add_list_map("{{items}}", transform="to_string")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_list_map_to_upper(self) -> None:
        """Test mapping strings to uppercase."""
        result = await (
            WorkflowBuilder("List Map To Upper")
            .add_start()
            .add_set_variable("items", ["hello", "world"])
            .add_list_map("{{items}}", transform="to_upper")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_list_map_to_lower(self) -> None:
        """Test mapping strings to lowercase."""
        result = await (
            WorkflowBuilder("List Map To Lower")
            .add_start()
            .add_set_variable("items", ["HELLO", "WORLD"])
            .add_list_map("{{items}}", transform="to_lower")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_list_map_trim(self) -> None:
        """Test mapping strings to trimmed versions."""
        result = await (
            WorkflowBuilder("List Map Trim")
            .add_start()
            .add_set_variable("items", ["  hello  ", "  world  "])
            .add_list_map("{{items}}", transform="trim")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_list_map_length(self) -> None:
        """Test mapping items to their lengths."""
        result = await (
            WorkflowBuilder("List Map Length")
            .add_start()
            .add_set_variable("items", ["a", "bb", "ccc"])
            .add_list_map("{{items}}", transform="length")
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestListReduce:
    """Tests for list reduce operations."""

    async def test_list_reduce_sum(self) -> None:
        """Test reducing list to sum."""
        result = await (
            WorkflowBuilder("List Reduce Sum")
            .add_start()
            .add_set_variable("items", [1, 2, 3, 4, 5])
            .add_list_reduce("{{items}}", operation="sum")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_list_reduce_product(self) -> None:
        """Test reducing list to product."""
        result = await (
            WorkflowBuilder("List Reduce Product")
            .add_start()
            .add_set_variable("items", [1, 2, 3, 4])
            .add_list_reduce("{{items}}", operation="product")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_list_reduce_avg(self) -> None:
        """Test reducing list to average."""
        result = await (
            WorkflowBuilder("List Reduce Avg")
            .add_start()
            .add_set_variable("items", [10, 20, 30])
            .add_list_reduce("{{items}}", operation="avg")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_list_reduce_first(self) -> None:
        """Test getting first item via reduce."""
        result = await (
            WorkflowBuilder("List Reduce First")
            .add_start()
            .add_set_variable("items", ["first", "second", "third"])
            .add_list_reduce("{{items}}", operation="first")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_list_reduce_last(self) -> None:
        """Test getting last item via reduce."""
        result = await (
            WorkflowBuilder("List Reduce Last")
            .add_start()
            .add_set_variable("items", ["first", "second", "third"])
            .add_list_reduce("{{items}}", operation="last")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_list_reduce_join(self) -> None:
        """Test joining list via reduce."""
        result = await (
            WorkflowBuilder("List Reduce Join")
            .add_start()
            .add_set_variable("items", ["a", "b", "c"])
            .add_list_reduce("{{items}}", operation="join", initial="-")
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestListUnique:
    """Tests for list unique operations."""

    async def test_list_unique(self) -> None:
        """Test removing duplicates from list."""
        result = await (
            WorkflowBuilder("List Unique")
            .add_start()
            .add_set_variable("items", [1, 2, 2, 3, 3, 3])
            .add_list_unique("{{items}}")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_list_unique_strings(self) -> None:
        """Test removing duplicate strings."""
        result = await (
            WorkflowBuilder("List Unique Strings")
            .add_start()
            .add_set_variable("items", ["a", "b", "a", "c", "b"])
            .add_list_unique("{{items}}")
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestListFlatten:
    """Tests for list flatten operations."""

    async def test_list_flatten(self) -> None:
        """Test flattening nested list."""
        result = await (
            WorkflowBuilder("List Flatten")
            .add_start()
            .add_set_variable("items", [[1, 2], [3, 4]])
            .add_list_flatten("{{items}}")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_list_flatten_deep(self) -> None:
        """Test deep flattening nested list."""
        result = await (
            WorkflowBuilder("List Flatten Deep")
            .add_start()
            .add_set_variable("items", [[[1]], [[2, 3]], [[4]]])
            .add_list_flatten("{{items}}", depth=2)
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_list_flatten_mixed(self) -> None:
        """Test flattening mixed nested list."""
        result = await (
            WorkflowBuilder("List Flatten Mixed")
            .add_start()
            .add_set_variable("items", [[1, 2], 3, [4, 5]])
            .add_list_flatten("{{items}}")
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestListJoin:
    """Tests for list join operations."""

    async def test_list_join(self) -> None:
        """Test joining list into string."""
        result = await (
            WorkflowBuilder("List Join")
            .add_start()
            .add_set_variable("items", ["a", "b", "c"])
            .add_list_join("{{items}}", separator="-")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_list_join_comma(self) -> None:
        """Test joining list with comma separator."""
        result = await (
            WorkflowBuilder("List Join Comma")
            .add_start()
            .add_set_variable("items", ["apple", "banana", "cherry"])
            .add_list_join("{{items}}", separator=", ")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_list_join_no_separator(self) -> None:
        """Test joining list with no separator."""
        result = await (
            WorkflowBuilder("List Join No Sep")
            .add_start()
            .add_set_variable("items", ["H", "e", "l", "l", "o"])
            .add_list_join("{{items}}", separator="")
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestListPipeline:
    """Tests for chained list operations."""

    async def test_list_pipeline_filter_sort(self) -> None:
        """Test pipeline: filter -> sort."""
        result = await (
            WorkflowBuilder("List Filter Sort Pipeline")
            .add_start()
            .add_set_variable("items", [5, 2, 8, 1, 9, 3])
            .add_list_filter("{{items}}", condition="greater_than", value=3)
            .add_list_sort("{{items}}")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_list_pipeline_map_join(self) -> None:
        """Test pipeline: map to upper -> join."""
        result = await (
            WorkflowBuilder("List Map Join Pipeline")
            .add_start()
            .add_set_variable("items", ["hello", "world"])
            .add_list_map("{{items}}", transform="to_upper")
            .add_list_join("{{items}}", separator=" ")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_list_pipeline_unique_sort_slice(self) -> None:
        """Test pipeline: unique -> sort -> slice."""
        result = await (
            WorkflowBuilder("List Unique Sort Slice Pipeline")
            .add_start()
            .add_set_variable("items", [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5])
            .add_list_unique("{{items}}")
            .add_list_sort("{{items}}")
            .add_list_slice("{{items}}", start=0, end=5)
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_list_complex_operations(self) -> None:
        """Test complex list operations workflow."""
        result = await (
            WorkflowBuilder("List Complex Ops")
            .add_start()
            .add_set_variable("numbers", [1, 2, 3, 4, 5])
            .add_list_length("{{numbers}}")
            .add_list_reduce("{{numbers}}", operation="sum")
            .add_list_reverse("{{numbers}}")
            .add_list_get_item("{{numbers}}", index=0)
            .add_end()
            .execute()
        )

        assert result["success"] is True
