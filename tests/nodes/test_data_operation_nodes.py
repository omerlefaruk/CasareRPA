"""
Comprehensive tests for data operation nodes.

Tests 30+ data operation nodes across categories:
- String operations: Concatenate, FormatString, RegexMatch, RegexReplace
- Math operations: MathOperation, Comparison
- List operations: CreateList, ListGetItem, ListLength, ListAppend, ListContains,
                   ListSlice, ListJoin, ListSort, ListReverse, ListUnique,
                   ListFilter, ListMap, ListReduce, ListFlatten
- Dict operations: CreateDict, DictGet, DictSet, DictRemove, DictMerge,
                   DictKeys, DictValues, DictHasKey, DictItems, DictToJson
- JSON operations: JsonParse, GetProperty

Target: 100+ tests covering success scenarios, error handling, edge cases,
type coercion, and ExecutionResult compliance.
"""

import pytest
from unittest.mock import Mock
from casare_rpa.core.execution_context import ExecutionContext
from casare_rpa.nodes.data_operation_nodes import (
    ConcatenateNode,
    FormatStringNode,
    RegexMatchNode,
    RegexReplaceNode,
    MathOperationNode,
    ComparisonNode,
    CreateListNode,
    ListGetItemNode,
    JsonParseNode,
    GetPropertyNode,
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


@pytest.fixture
def execution_context():
    """Create a mock execution context."""
    context = Mock(spec=ExecutionContext)
    context.variables = {}
    context.resolve_value = lambda x: x
    return context


# =============================================================================
# String Operations
# =============================================================================


class TestConcatenateNode:
    """Tests for ConcatenateNode string joining."""

    @pytest.mark.asyncio
    async def test_concatenate_two_strings(self, execution_context):
        """Test concatenating two strings."""
        node = ConcatenateNode(node_id="test_concat")
        node.set_input_value("string_1", "Hello")
        node.set_input_value("string_2", "World")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "HelloWorld"

    @pytest.mark.asyncio
    async def test_concatenate_with_separator(self, execution_context):
        """Test concatenating with separator."""
        node = ConcatenateNode(node_id="test_concat_sep", config={"separator": " "})
        node.set_input_value("string_1", "Hello")
        node.set_input_value("string_2", "World")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "Hello World"

    @pytest.mark.asyncio
    async def test_concatenate_empty_strings(self, execution_context):
        """Test concatenating empty strings."""
        node = ConcatenateNode(node_id="test_concat_empty")
        node.set_input_value("string_1", "")
        node.set_input_value("string_2", "")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == ""

    @pytest.mark.asyncio
    async def test_concatenate_numbers_converted(self, execution_context):
        """Test concatenating numbers (converted to strings)."""
        node = ConcatenateNode(node_id="test_concat_num")
        node.set_input_value("string_1", 123)
        node.set_input_value("string_2", 456)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "123456"


class TestFormatStringNode:
    """Tests for FormatStringNode template formatting."""

    @pytest.mark.asyncio
    async def test_format_simple(self, execution_context):
        """Test simple string formatting."""
        node = FormatStringNode(node_id="test_format")
        node.set_input_value("template", "Hello, {name}!")
        node.set_input_value("variables", {"name": "World"})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "Hello, World!"

    @pytest.mark.asyncio
    async def test_format_multiple_vars(self, execution_context):
        """Test formatting with multiple variables."""
        node = FormatStringNode(node_id="test_format_multi")
        node.set_input_value("template", "{first} {last} is {age} years old")
        node.set_input_value("variables", {"first": "John", "last": "Doe", "age": 30})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "John Doe is 30 years old"

    @pytest.mark.asyncio
    async def test_format_invalid_variables_type(self, execution_context):
        """Test error when variables is not a dict."""
        node = FormatStringNode(node_id="test_format_err")
        node.set_input_value("template", "{name}")
        node.set_input_value("variables", "not a dict")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "dictionary" in result["error"].lower()


class TestRegexMatchNode:
    """Tests for RegexMatchNode pattern matching."""

    @pytest.mark.asyncio
    async def test_regex_match_found(self, execution_context):
        """Test regex match found."""
        node = RegexMatchNode(node_id="test_regex")
        node.set_input_value("text", "Hello World")
        node.set_input_value("pattern", r"\w+")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("match_found") is True
        assert node.get_output_value("first_match") == "Hello"
        assert node.get_output_value("match_count") == 2

    @pytest.mark.asyncio
    async def test_regex_no_match(self, execution_context):
        """Test regex no match."""
        node = RegexMatchNode(node_id="test_regex_no")
        node.set_input_value("text", "Hello World")
        node.set_input_value("pattern", r"\d+")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("match_found") is False
        assert node.get_output_value("first_match") == ""
        assert node.get_output_value("match_count") == 0

    @pytest.mark.asyncio
    async def test_regex_with_groups(self, execution_context):
        """Test regex with capture groups."""
        node = RegexMatchNode(node_id="test_regex_groups")
        node.set_input_value("text", "john@example.com")
        node.set_input_value("pattern", r"(\w+)@(\w+)\.(\w+)")

        result = await node.execute(execution_context)

        assert result["success"] is True
        groups = node.get_output_value("groups")
        assert groups[0] == "john"
        assert groups[1] == "example"
        assert groups[2] == "com"

    @pytest.mark.asyncio
    async def test_regex_case_insensitive(self, execution_context):
        """Test case insensitive regex."""
        node = RegexMatchNode(node_id="test_regex_ci", config={"ignore_case": True})
        node.set_input_value("text", "Hello WORLD")
        node.set_input_value("pattern", r"world")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("match_found") is True
        assert node.get_output_value("first_match") == "WORLD"


class TestRegexReplaceNode:
    """Tests for RegexReplaceNode pattern replacement."""

    @pytest.mark.asyncio
    async def test_regex_replace_all(self, execution_context):
        """Test replacing all matches."""
        node = RegexReplaceNode(node_id="test_replace")
        node.set_input_value("text", "cat dog cat")
        node.set_input_value("pattern", r"cat")
        node.set_input_value("replacement", "bird")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "bird dog bird"
        assert node.get_output_value("count") == 2

    @pytest.mark.asyncio
    async def test_regex_replace_limited(self, execution_context):
        """Test replacing limited number of matches."""
        node = RegexReplaceNode(node_id="test_replace_lim", config={"max_count": 1})
        node.set_input_value("text", "cat dog cat")
        node.set_input_value("pattern", r"cat")
        node.set_input_value("replacement", "bird")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "bird dog cat"
        assert node.get_output_value("count") == 1

    @pytest.mark.asyncio
    async def test_regex_replace_with_backreference(self, execution_context):
        """Test replacing with backreferences."""
        node = RegexReplaceNode(node_id="test_replace_back")
        node.set_input_value("text", "John Smith")
        node.set_input_value("pattern", r"(\w+) (\w+)")
        node.set_input_value("replacement", r"\2, \1")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "Smith, John"


# =============================================================================
# Math Operations
# =============================================================================


class TestMathOperationNode:
    """Tests for MathOperationNode calculations."""

    @pytest.mark.asyncio
    async def test_math_add(self, execution_context):
        """Test addition."""
        node = MathOperationNode(node_id="test_add", config={"operation": "add"})
        node.set_input_value("a", 5)
        node.set_input_value("b", 3)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 8.0

    @pytest.mark.asyncio
    async def test_math_subtract(self, execution_context):
        """Test subtraction."""
        node = MathOperationNode(node_id="test_sub", config={"operation": "subtract"})
        node.set_input_value("a", 10)
        node.set_input_value("b", 4)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 6.0

    @pytest.mark.asyncio
    async def test_math_multiply(self, execution_context):
        """Test multiplication."""
        node = MathOperationNode(node_id="test_mul", config={"operation": "multiply"})
        node.set_input_value("a", 6)
        node.set_input_value("b", 7)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 42.0

    @pytest.mark.asyncio
    async def test_math_divide(self, execution_context):
        """Test division."""
        node = MathOperationNode(node_id="test_div", config={"operation": "divide"})
        node.set_input_value("a", 20)
        node.set_input_value("b", 4)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 5.0

    @pytest.mark.asyncio
    async def test_math_divide_by_zero(self, execution_context):
        """Test division by zero."""
        node = MathOperationNode(
            node_id="test_div_zero", config={"operation": "divide"}
        )
        node.set_input_value("a", 10)
        node.set_input_value("b", 0)

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "zero" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_math_power(self, execution_context):
        """Test power operation."""
        node = MathOperationNode(node_id="test_pow", config={"operation": "power"})
        node.set_input_value("a", 2)
        node.set_input_value("b", 10)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 1024.0

    @pytest.mark.asyncio
    async def test_math_modulo(self, execution_context):
        """Test modulo operation."""
        node = MathOperationNode(node_id="test_mod", config={"operation": "modulo"})
        node.set_input_value("a", 17)
        node.set_input_value("b", 5)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 2.0

    @pytest.mark.asyncio
    async def test_math_abs(self, execution_context):
        """Test absolute value."""
        node = MathOperationNode(node_id="test_abs", config={"operation": "abs"})
        node.set_input_value("a", -42)
        node.set_input_value("b", 0)  # Not used but required

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 42.0

    @pytest.mark.asyncio
    async def test_math_sqrt(self, execution_context):
        """Test square root."""
        node = MathOperationNode(node_id="test_sqrt", config={"operation": "sqrt"})
        node.set_input_value("a", 16)
        node.set_input_value("b", 0)  # Not used but required

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 4.0

    @pytest.mark.asyncio
    async def test_math_floor(self, execution_context):
        """Test floor operation."""
        node = MathOperationNode(node_id="test_floor", config={"operation": "floor"})
        node.set_input_value("a", 3.7)
        node.set_input_value("b", 0)  # Not used but required

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 3.0

    @pytest.mark.asyncio
    async def test_math_ceil(self, execution_context):
        """Test ceiling operation."""
        node = MathOperationNode(node_id="test_ceil", config={"operation": "ceil"})
        node.set_input_value("a", 3.1)
        node.set_input_value("b", 0)  # Not used but required

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 4.0

    @pytest.mark.asyncio
    async def test_math_min(self, execution_context):
        """Test minimum."""
        node = MathOperationNode(node_id="test_min", config={"operation": "min"})
        node.set_input_value("a", 5)
        node.set_input_value("b", 3)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 3.0

    @pytest.mark.asyncio
    async def test_math_max(self, execution_context):
        """Test maximum."""
        node = MathOperationNode(node_id="test_max", config={"operation": "max"})
        node.set_input_value("a", 5)
        node.set_input_value("b", 8)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 8.0

    @pytest.mark.asyncio
    async def test_math_round_digits(self, execution_context):
        """Test rounding with specific digits."""
        node = MathOperationNode(
            node_id="test_round", config={"operation": "divide", "round_digits": 2}
        )
        node.set_input_value("a", 10)
        node.set_input_value("b", 3)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 3.33


class TestComparisonNode:
    """Tests for ComparisonNode value comparisons."""

    @pytest.mark.asyncio
    async def test_comparison_equal(self, execution_context):
        """Test equality comparison."""
        node = ComparisonNode(node_id="test_eq", config={"operator": "=="})
        node.set_input_value("a", 5)
        node.set_input_value("b", 5)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") is True

    @pytest.mark.asyncio
    async def test_comparison_not_equal(self, execution_context):
        """Test inequality comparison."""
        node = ComparisonNode(node_id="test_neq", config={"operator": "!="})
        node.set_input_value("a", 5)
        node.set_input_value("b", 10)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") is True

    @pytest.mark.asyncio
    async def test_comparison_greater(self, execution_context):
        """Test greater than comparison."""
        node = ComparisonNode(node_id="test_gt", config={"operator": ">"})
        node.set_input_value("a", 10)
        node.set_input_value("b", 5)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") is True

    @pytest.mark.asyncio
    async def test_comparison_less(self, execution_context):
        """Test less than comparison."""
        node = ComparisonNode(node_id="test_lt", config={"operator": "<"})
        node.set_input_value("a", 3)
        node.set_input_value("b", 10)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") is True

    @pytest.mark.asyncio
    async def test_comparison_greater_equal(self, execution_context):
        """Test greater than or equal comparison."""
        node = ComparisonNode(node_id="test_gte", config={"operator": ">="})
        node.set_input_value("a", 5)
        node.set_input_value("b", 5)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") is True

    @pytest.mark.asyncio
    async def test_comparison_less_equal(self, execution_context):
        """Test less than or equal comparison."""
        node = ComparisonNode(node_id="test_lte", config={"operator": "<="})
        node.set_input_value("a", 3)
        node.set_input_value("b", 3)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") is True

    @pytest.mark.asyncio
    async def test_comparison_string(self, execution_context):
        """Test string comparison."""
        node = ComparisonNode(node_id="test_str", config={"operator": "=="})
        node.set_input_value("a", "hello")
        node.set_input_value("b", "hello")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") is True


# =============================================================================
# List Operations
# =============================================================================


class TestCreateListNode:
    """Tests for CreateListNode list creation."""

    @pytest.mark.asyncio
    async def test_create_list(self, execution_context):
        """Test creating a list from items."""
        node = CreateListNode(node_id="test_create_list")
        node.set_input_value("item_1", "a")
        node.set_input_value("item_2", "b")
        node.set_input_value("item_3", "c")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("list") == ["a", "b", "c"]

    @pytest.mark.asyncio
    async def test_create_list_partial(self, execution_context):
        """Test creating list with partial items."""
        node = CreateListNode(node_id="test_create_partial")
        node.set_input_value("item_1", "only")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("list") == ["only"]


class TestListGetItemNode:
    """Tests for ListGetItemNode element access."""

    @pytest.mark.asyncio
    async def test_list_get_item(self, execution_context):
        """Test getting item by index."""
        node = ListGetItemNode(node_id="test_get")
        node.set_input_value("list", ["a", "b", "c"])
        node.set_input_value("index", 1)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("item") == "b"

    @pytest.mark.asyncio
    async def test_list_get_negative_index(self, execution_context):
        """Test getting item with negative index."""
        node = ListGetItemNode(node_id="test_get_neg")
        node.set_input_value("list", ["a", "b", "c"])
        node.set_input_value("index", -1)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("item") == "c"

    @pytest.mark.asyncio
    async def test_list_get_out_of_range(self, execution_context):
        """Test error on out of range index."""
        node = ListGetItemNode(node_id="test_get_oor")
        node.set_input_value("list", ["a", "b"])
        node.set_input_value("index", 10)

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "out of range" in result["error"].lower()


class TestListLengthNode:
    """Tests for ListLengthNode list size."""

    @pytest.mark.asyncio
    async def test_list_length(self, execution_context):
        """Test getting list length."""
        node = ListLengthNode(node_id="test_len")
        node.set_input_value("list", [1, 2, 3, 4, 5])

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("length") == 5

    @pytest.mark.asyncio
    async def test_list_length_empty(self, execution_context):
        """Test length of empty list."""
        node = ListLengthNode(node_id="test_len_empty")
        node.set_input_value("list", [])

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("length") == 0


class TestListAppendNode:
    """Tests for ListAppendNode element addition."""

    @pytest.mark.asyncio
    async def test_list_append(self, execution_context):
        """Test appending to list."""
        node = ListAppendNode(node_id="test_append")
        node.set_input_value("list", [1, 2])
        node.set_input_value("item", 3)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_list_append_to_empty(self, execution_context):
        """Test appending to empty list."""
        node = ListAppendNode(node_id="test_append_empty")
        node.set_input_value("list", [])
        node.set_input_value("item", "first")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == ["first"]


class TestListContainsNode:
    """Tests for ListContainsNode membership check."""

    @pytest.mark.asyncio
    async def test_list_contains_true(self, execution_context):
        """Test item found in list."""
        node = ListContainsNode(node_id="test_contains")
        node.set_input_value("list", ["apple", "banana", "cherry"])
        node.set_input_value("item", "banana")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("contains") is True
        assert node.get_output_value("index") == 1

    @pytest.mark.asyncio
    async def test_list_contains_false(self, execution_context):
        """Test item not found in list."""
        node = ListContainsNode(node_id="test_contains_no")
        node.set_input_value("list", ["apple", "banana"])
        node.set_input_value("item", "orange")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("contains") is False
        assert node.get_output_value("index") == -1


class TestListSliceNode:
    """Tests for ListSliceNode list slicing."""

    @pytest.mark.asyncio
    async def test_list_slice(self, execution_context):
        """Test slicing list."""
        node = ListSliceNode(node_id="test_slice")
        node.set_input_value("list", [0, 1, 2, 3, 4])
        node.set_input_value("start", 1)
        node.set_input_value("end", 4)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_list_slice_no_end(self, execution_context):
        """Test slicing without end."""
        node = ListSliceNode(node_id="test_slice_no_end")
        node.set_input_value("list", [0, 1, 2, 3, 4])
        node.set_input_value("start", 2)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == [2, 3, 4]


class TestListJoinNode:
    """Tests for ListJoinNode list to string."""

    @pytest.mark.asyncio
    async def test_list_join(self, execution_context):
        """Test joining list to string."""
        node = ListJoinNode(node_id="test_join")
        node.set_input_value("list", ["a", "b", "c"])
        node.set_input_value("separator", ", ")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "a, b, c"

    @pytest.mark.asyncio
    async def test_list_join_numbers(self, execution_context):
        """Test joining numbers."""
        node = ListJoinNode(node_id="test_join_num")
        node.set_input_value("list", [1, 2, 3])
        node.set_input_value("separator", "-")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "1-2-3"


class TestListSortNode:
    """Tests for ListSortNode list sorting."""

    @pytest.mark.asyncio
    async def test_list_sort_ascending(self, execution_context):
        """Test ascending sort."""
        node = ListSortNode(node_id="test_sort")
        node.set_input_value("list", [3, 1, 4, 1, 5])

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == [1, 1, 3, 4, 5]

    @pytest.mark.asyncio
    async def test_list_sort_descending(self, execution_context):
        """Test descending sort."""
        node = ListSortNode(node_id="test_sort_desc")
        node.set_input_value("list", [3, 1, 4])
        node.set_input_value("reverse", True)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == [4, 3, 1]

    @pytest.mark.asyncio
    async def test_list_sort_by_key(self, execution_context):
        """Test sorting by key path."""
        node = ListSortNode(node_id="test_sort_key")
        node.set_input_value(
            "list", [{"name": "Bob"}, {"name": "Alice"}, {"name": "Charlie"}]
        )
        node.set_input_value("key_path", "name")

        result = await node.execute(execution_context)

        assert result["success"] is True
        sorted_list = node.get_output_value("result")
        assert sorted_list[0]["name"] == "Alice"
        assert sorted_list[1]["name"] == "Bob"


class TestListReverseNode:
    """Tests for ListReverseNode list reversal."""

    @pytest.mark.asyncio
    async def test_list_reverse(self, execution_context):
        """Test reversing list."""
        node = ListReverseNode(node_id="test_reverse")
        node.set_input_value("list", [1, 2, 3])

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == [3, 2, 1]


class TestListUniqueNode:
    """Tests for ListUniqueNode duplicate removal."""

    @pytest.mark.asyncio
    async def test_list_unique(self, execution_context):
        """Test removing duplicates."""
        node = ListUniqueNode(node_id="test_unique")
        node.set_input_value("list", [1, 2, 2, 3, 3, 3])

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_list_unique_preserves_order(self, execution_context):
        """Test unique preserves first occurrence order."""
        node = ListUniqueNode(node_id="test_unique_order")
        node.set_input_value("list", ["b", "a", "b", "c", "a"])

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == ["b", "a", "c"]


class TestListFilterNode:
    """Tests for ListFilterNode filtering."""

    @pytest.mark.asyncio
    async def test_list_filter_equals(self, execution_context):
        """Test filtering by equality."""
        node = ListFilterNode(node_id="test_filter_eq")
        node.set_input_value(
            "list", [{"status": "active"}, {"status": "inactive"}, {"status": "active"}]
        )
        node.set_input_value("condition", "equals")
        node.set_input_value("value", "active")
        node.set_input_value("key_path", "status")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert len(node.get_output_value("result")) == 2

    @pytest.mark.asyncio
    async def test_list_filter_greater_than(self, execution_context):
        """Test filtering by greater than."""
        node = ListFilterNode(node_id="test_filter_gt")
        node.set_input_value("list", [1, 5, 10, 15, 20])
        node.set_input_value("condition", "greater_than")
        node.set_input_value("value", 10)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == [15, 20]

    @pytest.mark.asyncio
    async def test_list_filter_is_not_none(self, execution_context):
        """Test filtering non-null values."""
        node = ListFilterNode(node_id="test_filter_none")
        node.set_input_value("list", [1, None, 2, None, 3])
        node.set_input_value("condition", "is_not_none")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == [1, 2, 3]


class TestListMapNode:
    """Tests for ListMapNode transformation."""

    @pytest.mark.asyncio
    async def test_list_map_to_upper(self, execution_context):
        """Test mapping to uppercase."""
        node = ListMapNode(node_id="test_map")
        node.set_input_value("list", ["hello", "world"])
        node.set_input_value("transform", "to_upper")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == ["HELLO", "WORLD"]

    @pytest.mark.asyncio
    async def test_list_map_get_property(self, execution_context):
        """Test extracting property from objects."""
        node = ListMapNode(node_id="test_map_prop")
        node.set_input_value("list", [{"name": "Alice"}, {"name": "Bob"}])
        node.set_input_value("transform", "get_property")
        node.set_input_value("key_path", "name")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == ["Alice", "Bob"]


class TestListReduceNode:
    """Tests for ListReduceNode aggregation."""

    @pytest.mark.asyncio
    async def test_list_reduce_sum(self, execution_context):
        """Test summing list."""
        node = ListReduceNode(node_id="test_reduce_sum")
        node.set_input_value("list", [1, 2, 3, 4, 5])
        node.set_input_value("operation", "sum")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 15.0

    @pytest.mark.asyncio
    async def test_list_reduce_avg(self, execution_context):
        """Test averaging list."""
        node = ListReduceNode(node_id="test_reduce_avg")
        node.set_input_value("list", [10, 20, 30])
        node.set_input_value("operation", "avg")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 20.0

    @pytest.mark.asyncio
    async def test_list_reduce_min(self, execution_context):
        """Test finding minimum."""
        node = ListReduceNode(node_id="test_reduce_min")
        node.set_input_value("list", [5, 2, 8, 1])
        node.set_input_value("operation", "min")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 1

    @pytest.mark.asyncio
    async def test_list_reduce_max(self, execution_context):
        """Test finding maximum."""
        node = ListReduceNode(node_id="test_reduce_max")
        node.set_input_value("list", [5, 2, 8, 1])
        node.set_input_value("operation", "max")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 8

    @pytest.mark.asyncio
    async def test_list_reduce_count(self, execution_context):
        """Test counting items."""
        node = ListReduceNode(node_id="test_reduce_count")
        node.set_input_value("list", [1, 2, 3])
        node.set_input_value("operation", "count")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 3


class TestListFlattenNode:
    """Tests for ListFlattenNode nested list flattening."""

    @pytest.mark.asyncio
    async def test_list_flatten_one_level(self, execution_context):
        """Test flattening one level."""
        node = ListFlattenNode(node_id="test_flatten")
        node.set_input_value("list", [[1, 2], [3, 4], [5]])
        node.set_input_value("depth", 1)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == [1, 2, 3, 4, 5]

    @pytest.mark.asyncio
    async def test_list_flatten_deep(self, execution_context):
        """Test flattening multiple levels."""
        node = ListFlattenNode(node_id="test_flatten_deep")
        node.set_input_value("list", [[[1, 2]], [[3, 4]]])
        node.set_input_value("depth", 2)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == [1, 2, 3, 4]


# =============================================================================
# Dictionary Operations
# =============================================================================


class TestDictGetNode:
    """Tests for DictGetNode value retrieval."""

    @pytest.mark.asyncio
    async def test_dict_get(self, execution_context):
        """Test getting dict value."""
        node = DictGetNode(node_id="test_dict_get")
        node.set_input_value("dict", {"name": "John", "age": 30})
        node.set_input_value("key", "name")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("value") == "John"
        assert node.get_output_value("found") is True

    @pytest.mark.asyncio
    async def test_dict_get_missing_with_default(self, execution_context):
        """Test getting missing key with default."""
        node = DictGetNode(node_id="test_dict_get_default")
        node.set_input_value("dict", {"name": "John"})
        node.set_input_value("key", "age")
        node.set_input_value("default", 0)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("value") == 0
        assert node.get_output_value("found") is False


class TestDictSetNode:
    """Tests for DictSetNode value setting."""

    @pytest.mark.asyncio
    async def test_dict_set(self, execution_context):
        """Test setting dict value."""
        node = DictSetNode(node_id="test_dict_set")
        node.set_input_value("dict", {"name": "John"})
        node.set_input_value("key", "age")
        node.set_input_value("value", 30)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == {"name": "John", "age": 30}

    @pytest.mark.asyncio
    async def test_dict_set_overwrite(self, execution_context):
        """Test overwriting existing key."""
        node = DictSetNode(node_id="test_dict_set_ow")
        node.set_input_value("dict", {"name": "John"})
        node.set_input_value("key", "name")
        node.set_input_value("value", "Jane")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == {"name": "Jane"}


class TestDictRemoveNode:
    """Tests for DictRemoveNode key removal."""

    @pytest.mark.asyncio
    async def test_dict_remove(self, execution_context):
        """Test removing dict key."""
        node = DictRemoveNode(node_id="test_dict_remove")
        node.set_input_value("dict", {"name": "John", "age": 30})
        node.set_input_value("key", "age")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == {"name": "John"}
        assert node.get_output_value("removed_value") == 30

    @pytest.mark.asyncio
    async def test_dict_remove_missing(self, execution_context):
        """Test removing non-existent key."""
        node = DictRemoveNode(node_id="test_dict_remove_miss")
        node.set_input_value("dict", {"name": "John"})
        node.set_input_value("key", "age")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("removed_value") is None


class TestDictMergeNode:
    """Tests for DictMergeNode dictionary merging."""

    @pytest.mark.asyncio
    async def test_dict_merge(self, execution_context):
        """Test merging two dicts."""
        node = DictMergeNode(node_id="test_dict_merge")
        node.set_input_value("dict_1", {"a": 1, "b": 2})
        node.set_input_value("dict_2", {"c": 3, "d": 4})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == {"a": 1, "b": 2, "c": 3, "d": 4}

    @pytest.mark.asyncio
    async def test_dict_merge_overlap(self, execution_context):
        """Test merging with overlapping keys (second wins)."""
        node = DictMergeNode(node_id="test_dict_merge_ov")
        node.set_input_value("dict_1", {"a": 1, "b": 2})
        node.set_input_value("dict_2", {"b": 20, "c": 3})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == {"a": 1, "b": 20, "c": 3}


class TestDictKeysNode:
    """Tests for DictKeysNode key extraction."""

    @pytest.mark.asyncio
    async def test_dict_keys(self, execution_context):
        """Test getting dict keys."""
        node = DictKeysNode(node_id="test_dict_keys")
        node.set_input_value("dict", {"a": 1, "b": 2, "c": 3})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert set(node.get_output_value("keys")) == {"a", "b", "c"}
        assert node.get_output_value("count") == 3


class TestDictValuesNode:
    """Tests for DictValuesNode value extraction."""

    @pytest.mark.asyncio
    async def test_dict_values(self, execution_context):
        """Test getting dict values."""
        node = DictValuesNode(node_id="test_dict_values")
        node.set_input_value("dict", {"a": 1, "b": 2, "c": 3})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert set(node.get_output_value("values")) == {1, 2, 3}
        assert node.get_output_value("count") == 3


class TestDictHasKeyNode:
    """Tests for DictHasKeyNode key check."""

    @pytest.mark.asyncio
    async def test_dict_has_key_true(self, execution_context):
        """Test key exists."""
        node = DictHasKeyNode(node_id="test_has_key")
        node.set_input_value("dict", {"name": "John"})
        node.set_input_value("key", "name")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("has_key") is True

    @pytest.mark.asyncio
    async def test_dict_has_key_false(self, execution_context):
        """Test key does not exist."""
        node = DictHasKeyNode(node_id="test_has_key_no")
        node.set_input_value("dict", {"name": "John"})
        node.set_input_value("key", "age")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("has_key") is False


class TestCreateDictNode:
    """Tests for CreateDictNode dictionary creation."""

    @pytest.mark.asyncio
    async def test_create_dict(self, execution_context):
        """Test creating dict from key-value pairs."""
        node = CreateDictNode(node_id="test_create_dict")
        node.set_input_value("key_1", "name")
        node.set_input_value("value_1", "John")
        node.set_input_value("key_2", "age")
        node.set_input_value("value_2", 30)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("dict") == {"name": "John", "age": 30}


class TestDictToJsonNode:
    """Tests for DictToJsonNode JSON conversion."""

    @pytest.mark.asyncio
    async def test_dict_to_json(self, execution_context):
        """Test converting dict to JSON string."""
        node = DictToJsonNode(node_id="test_to_json")
        node.set_input_value("dict", {"name": "John", "age": 30})

        result = await node.execute(execution_context)

        assert result["success"] is True
        json_str = node.get_output_value("json_string")
        assert "name" in json_str
        assert "John" in json_str

    @pytest.mark.asyncio
    async def test_dict_to_json_pretty(self, execution_context):
        """Test converting dict to pretty JSON."""
        node = DictToJsonNode(node_id="test_to_json_pretty")
        node.set_input_value("dict", {"name": "John"})
        node.set_input_value("indent", 2)

        result = await node.execute(execution_context)

        assert result["success"] is True
        json_str = node.get_output_value("json_string")
        assert "\n" in json_str


class TestDictItemsNode:
    """Tests for DictItemsNode item extraction."""

    @pytest.mark.asyncio
    async def test_dict_items(self, execution_context):
        """Test getting dict items as list."""
        node = DictItemsNode(node_id="test_items")
        node.set_input_value("dict", {"a": 1, "b": 2})

        result = await node.execute(execution_context)

        assert result["success"] is True
        items = node.get_output_value("items")
        assert len(items) == 2
        assert {"key": "a", "value": 1} in items
        assert {"key": "b", "value": 2} in items


# =============================================================================
# JSON Operations
# =============================================================================


class TestJsonParseNode:
    """Tests for JsonParseNode JSON parsing."""

    @pytest.mark.asyncio
    async def test_json_parse(self, execution_context):
        """Test parsing JSON string."""
        node = JsonParseNode(node_id="test_json_parse")
        node.set_input_value("json_string", '{"name": "John", "age": 30}')

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("data") == {"name": "John", "age": 30}

    @pytest.mark.asyncio
    async def test_json_parse_array(self, execution_context):
        """Test parsing JSON array."""
        node = JsonParseNode(node_id="test_json_array")
        node.set_input_value("json_string", "[1, 2, 3]")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("data") == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_json_parse_invalid(self, execution_context):
        """Test parsing invalid JSON."""
        node = JsonParseNode(node_id="test_json_invalid")
        node.set_input_value("json_string", "not json")

        result = await node.execute(execution_context)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_json_parse_empty(self, execution_context):
        """Test parsing empty string."""
        node = JsonParseNode(node_id="test_json_empty")
        node.set_input_value("json_string", "")

        result = await node.execute(execution_context)

        assert result["success"] is False


class TestGetPropertyNode:
    """Tests for GetPropertyNode nested property access."""

    @pytest.mark.asyncio
    async def test_get_property_simple(self, execution_context):
        """Test getting simple property."""
        node = GetPropertyNode(node_id="test_get_prop")
        node.set_input_value("object", {"name": "John"})
        node.set_input_value("property_path", "name")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("value") == "John"

    @pytest.mark.asyncio
    async def test_get_property_nested(self, execution_context):
        """Test getting nested property."""
        node = GetPropertyNode(node_id="test_get_nested")
        node.set_input_value("object", {"user": {"address": {"city": "NYC"}}})
        node.set_input_value("property_path", "user.address.city")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("value") == "NYC"

    @pytest.mark.asyncio
    async def test_get_property_missing(self, execution_context):
        """Test getting missing property returns None."""
        node = GetPropertyNode(node_id="test_get_missing")
        node.set_input_value("object", {"name": "John"})
        node.set_input_value("property_path", "age")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("value") is None


# =============================================================================
# Additional List Operations Tests
# =============================================================================


class TestListAppendNodeExtended:
    """Extended tests for ListAppendNode."""

    @pytest.mark.asyncio
    async def test_append_none_item(self, execution_context):
        """Test appending None to list."""
        node = ListAppendNode(node_id="test_append_none")
        node.set_input_value("list", [1, 2])
        node.set_input_value("item", None)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == [1, 2, None]

    @pytest.mark.asyncio
    async def test_append_list_as_item(self, execution_context):
        """Test appending a list as single item."""
        node = ListAppendNode(node_id="test_append_list")
        node.set_input_value("list", [1, 2])
        node.set_input_value("item", [3, 4])

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == [1, 2, [3, 4]]

    @pytest.mark.asyncio
    async def test_append_from_tuple(self, execution_context):
        """Test appending to tuple (converted to list)."""
        node = ListAppendNode(node_id="test_append_tuple")
        node.set_input_value("list", (1, 2))
        node.set_input_value("item", 3)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == [1, 2, 3]


class TestListSliceNodeExtended:
    """Extended tests for ListSliceNode."""

    @pytest.mark.asyncio
    async def test_slice_negative_indices(self, execution_context):
        """Test slicing with negative indices."""
        node = ListSliceNode(node_id="test_slice_neg")
        node.set_input_value("list", [0, 1, 2, 3, 4])
        node.set_input_value("start", -3)
        node.set_input_value("end", -1)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == [2, 3]

    @pytest.mark.asyncio
    async def test_slice_empty_result(self, execution_context):
        """Test slice resulting in empty list."""
        node = ListSliceNode(node_id="test_slice_empty")
        node.set_input_value("list", [1, 2, 3])
        node.set_input_value("start", 5)
        node.set_input_value("end", 10)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == []

    @pytest.mark.asyncio
    async def test_slice_invalid_input(self, execution_context):
        """Test slice with invalid input type."""
        node = ListSliceNode(node_id="test_slice_invalid")
        node.set_input_value("list", "not a list")
        node.set_input_value("start", 0)
        node.set_input_value("end", 2)

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "not a list" in result["error"].lower()


class TestListFilterNodeExtended:
    """Extended tests for ListFilterNode."""

    @pytest.mark.asyncio
    async def test_filter_contains(self, execution_context):
        """Test filtering by contains condition."""
        node = ListFilterNode(node_id="test_filter_contains")
        node.set_input_value("list", ["apple", "banana", "apricot", "cherry"])
        node.set_input_value("condition", "contains")
        node.set_input_value("value", "ap")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == ["apple", "apricot"]
        assert node.get_output_value("removed") == ["banana", "cherry"]

    @pytest.mark.asyncio
    async def test_filter_starts_with(self, execution_context):
        """Test filtering by starts_with condition."""
        node = ListFilterNode(node_id="test_filter_starts")
        node.set_input_value("list", ["apple", "banana", "apricot"])
        node.set_input_value("condition", "starts_with")
        node.set_input_value("value", "a")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == ["apple", "apricot"]

    @pytest.mark.asyncio
    async def test_filter_ends_with(self, execution_context):
        """Test filtering by ends_with condition."""
        node = ListFilterNode(node_id="test_filter_ends")
        node.set_input_value("list", ["cat", "dog", "bat", "rat"])
        node.set_input_value("condition", "ends_with")
        node.set_input_value("value", "at")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == ["cat", "bat", "rat"]

    @pytest.mark.asyncio
    async def test_filter_less_than(self, execution_context):
        """Test filtering by less_than condition."""
        node = ListFilterNode(node_id="test_filter_lt")
        node.set_input_value("list", [1, 5, 10, 15, 20])
        node.set_input_value("condition", "less_than")
        node.set_input_value("value", 10)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == [1, 5]

    @pytest.mark.asyncio
    async def test_filter_is_none(self, execution_context):
        """Test filtering for None values."""
        node = ListFilterNode(node_id="test_filter_is_none")
        node.set_input_value("list", [1, None, 2, None, 3])
        node.set_input_value("condition", "is_none")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == [None, None]

    @pytest.mark.asyncio
    async def test_filter_is_truthy(self, execution_context):
        """Test filtering for truthy values."""
        node = ListFilterNode(node_id="test_filter_truthy")
        node.set_input_value("list", [0, 1, "", "a", None, [], [1]])
        node.set_input_value("condition", "is_truthy")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == [1, "a", [1]]

    @pytest.mark.asyncio
    async def test_filter_is_falsy(self, execution_context):
        """Test filtering for falsy values."""
        node = ListFilterNode(node_id="test_filter_falsy")
        node.set_input_value("list", [0, 1, "", "a", None, [], [1]])
        node.set_input_value("condition", "is_falsy")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == [0, "", None, []]

    @pytest.mark.asyncio
    async def test_filter_not_equals(self, execution_context):
        """Test filtering by not_equals condition."""
        node = ListFilterNode(node_id="test_filter_neq")
        node.set_input_value(
            "list", [{"status": "ok"}, {"status": "error"}, {"status": "ok"}]
        )
        node.set_input_value("condition", "not_equals")
        node.set_input_value("value", "error")
        node.set_input_value("key_path", "status")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert len(node.get_output_value("result")) == 2


class TestListMapNodeExtended:
    """Extended tests for ListMapNode."""

    @pytest.mark.asyncio
    async def test_map_to_lower(self, execution_context):
        """Test mapping to lowercase."""
        node = ListMapNode(node_id="test_map_lower")
        node.set_input_value("list", ["HELLO", "WORLD"])
        node.set_input_value("transform", "to_lower")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == ["hello", "world"]

    @pytest.mark.asyncio
    async def test_map_to_int(self, execution_context):
        """Test mapping to integers."""
        node = ListMapNode(node_id="test_map_int")
        node.set_input_value("list", ["1", "2", "3"])
        node.set_input_value("transform", "to_int")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_map_to_float(self, execution_context):
        """Test mapping to floats."""
        node = ListMapNode(node_id="test_map_float")
        node.set_input_value("list", ["1.5", "2.5", "3.5"])
        node.set_input_value("transform", "to_float")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == [1.5, 2.5, 3.5]

    @pytest.mark.asyncio
    async def test_map_trim(self, execution_context):
        """Test mapping with trim."""
        node = ListMapNode(node_id="test_map_trim")
        node.set_input_value("list", ["  hello  ", "  world  "])
        node.set_input_value("transform", "trim")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == ["hello", "world"]

    @pytest.mark.asyncio
    async def test_map_length(self, execution_context):
        """Test mapping to lengths."""
        node = ListMapNode(node_id="test_map_len")
        node.set_input_value("list", ["a", "ab", "abc"])
        node.set_input_value("transform", "length")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_map_nested_key_path(self, execution_context):
        """Test extracting nested property."""
        node = ListMapNode(node_id="test_map_nested")
        node.set_input_value(
            "list", [{"user": {"name": "Alice"}}, {"user": {"name": "Bob"}}]
        )
        node.set_input_value("transform", "get_property")
        node.set_input_value("key_path", "user.name")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == ["Alice", "Bob"]

    @pytest.mark.asyncio
    async def test_map_invalid_type(self, execution_context):
        """Test map with invalid input type."""
        node = ListMapNode(node_id="test_map_invalid")
        node.set_input_value("list", "not a list")
        node.set_input_value("transform", "to_upper")

        result = await node.execute(execution_context)

        assert result["success"] is False


class TestListReduceNodeExtended:
    """Extended tests for ListReduceNode."""

    @pytest.mark.asyncio
    async def test_reduce_product(self, execution_context):
        """Test product reduction."""
        node = ListReduceNode(node_id="test_reduce_product")
        node.set_input_value("list", [2, 3, 4])
        node.set_input_value("operation", "product")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 24.0

    @pytest.mark.asyncio
    async def test_reduce_first(self, execution_context):
        """Test first element reduction."""
        node = ListReduceNode(node_id="test_reduce_first")
        node.set_input_value("list", ["a", "b", "c"])
        node.set_input_value("operation", "first")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "a"

    @pytest.mark.asyncio
    async def test_reduce_last(self, execution_context):
        """Test last element reduction."""
        node = ListReduceNode(node_id="test_reduce_last")
        node.set_input_value("list", ["a", "b", "c"])
        node.set_input_value("operation", "last")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "c"

    @pytest.mark.asyncio
    async def test_reduce_join(self, execution_context):
        """Test join reduction."""
        node = ListReduceNode(node_id="test_reduce_join")
        node.set_input_value("list", ["a", "b", "c"])
        node.set_input_value("operation", "join")
        node.set_input_value("initial", "-")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "a-b-c"

    @pytest.mark.asyncio
    async def test_reduce_empty_list(self, execution_context):
        """Test reduction of empty list."""
        node = ListReduceNode(node_id="test_reduce_empty")
        node.set_input_value("list", [])
        node.set_input_value("operation", "sum")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 0

    @pytest.mark.asyncio
    async def test_reduce_with_key_path(self, execution_context):
        """Test reduction with key path extraction."""
        node = ListReduceNode(node_id="test_reduce_key")
        node.set_input_value("list", [{"value": 10}, {"value": 20}, {"value": 30}])
        node.set_input_value("operation", "sum")
        node.set_input_value("key_path", "value")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 60.0

    @pytest.mark.asyncio
    async def test_reduce_unknown_operation(self, execution_context):
        """Test error on unknown operation."""
        node = ListReduceNode(node_id="test_reduce_unknown")
        node.set_input_value("list", [1, 2, 3])
        node.set_input_value("operation", "unknown_op")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "unknown" in result["error"].lower()


class TestListFlattenNodeExtended:
    """Extended tests for ListFlattenNode."""

    @pytest.mark.asyncio
    async def test_flatten_mixed_types(self, execution_context):
        """Test flattening with mixed types."""
        node = ListFlattenNode(node_id="test_flatten_mixed")
        node.set_input_value("list", [[1, "a"], [2, "b"]])
        node.set_input_value("depth", 1)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == [1, "a", 2, "b"]

    @pytest.mark.asyncio
    async def test_flatten_zero_depth(self, execution_context):
        """Test flatten with zero depth (no flattening)."""
        node = ListFlattenNode(node_id="test_flatten_zero")
        node.set_input_value("list", [[1, 2], [3, 4]])
        node.set_input_value("depth", 0)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == [[1, 2], [3, 4]]

    @pytest.mark.asyncio
    async def test_flatten_invalid_input(self, execution_context):
        """Test flatten with invalid input."""
        node = ListFlattenNode(node_id="test_flatten_invalid")
        node.set_input_value("list", "not a list")
        node.set_input_value("depth", 1)

        result = await node.execute(execution_context)

        assert result["success"] is False


class TestListUniqueNodeExtended:
    """Extended tests for ListUniqueNode."""

    @pytest.mark.asyncio
    async def test_unique_with_dicts(self, execution_context):
        """Test unique with unhashable items (dicts)."""
        node = ListUniqueNode(node_id="test_unique_dicts")
        node.set_input_value("list", [{"a": 1}, {"a": 1}, {"a": 2}])

        result = await node.execute(execution_context)

        assert result["success"] is True
        # Uses string representation for comparison
        assert len(node.get_output_value("result")) == 2

    @pytest.mark.asyncio
    async def test_unique_empty_list(self, execution_context):
        """Test unique on empty list."""
        node = ListUniqueNode(node_id="test_unique_empty")
        node.set_input_value("list", [])

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == []


# =============================================================================
# Additional Dictionary Operations Tests
# =============================================================================


class TestDictGetNodeExtended:
    """Extended tests for DictGetNode."""

    @pytest.mark.asyncio
    async def test_dict_get_none_value(self, execution_context):
        """Test getting key with None value."""
        node = DictGetNode(node_id="test_dict_get_none")
        node.set_input_value("dict", {"key": None})
        node.set_input_value("key", "key")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("value") is None
        assert node.get_output_value("found") is True

    @pytest.mark.asyncio
    async def test_dict_get_invalid_type(self, execution_context):
        """Test get with invalid input type."""
        node = DictGetNode(node_id="test_dict_get_invalid")
        node.set_input_value("dict", "not a dict")
        node.set_input_value("key", "key")

        result = await node.execute(execution_context)

        assert result["success"] is False


class TestDictSetNodeExtended:
    """Extended tests for DictSetNode."""

    @pytest.mark.asyncio
    async def test_dict_set_empty_key_error(self, execution_context):
        """Test setting with empty key raises error."""
        node = DictSetNode(node_id="test_dict_set_empty")
        node.set_input_value("dict", {"name": "John"})
        node.set_input_value("key", "")
        node.set_input_value("value", "test")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_dict_set_to_empty_dict(self, execution_context):
        """Test setting value in empty dict."""
        node = DictSetNode(node_id="test_dict_set_new")
        node.set_input_value("dict", {})
        node.set_input_value("key", "name")
        node.set_input_value("value", "John")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == {"name": "John"}

    @pytest.mark.asyncio
    async def test_dict_set_none_value(self, execution_context):
        """Test setting None as value."""
        node = DictSetNode(node_id="test_dict_set_none")
        node.set_input_value("dict", {"a": 1})
        node.set_input_value("key", "b")
        node.set_input_value("value", None)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == {"a": 1, "b": None}


class TestDictMergeNodeExtended:
    """Extended tests for DictMergeNode."""

    @pytest.mark.asyncio
    async def test_dict_merge_empty_first(self, execution_context):
        """Test merging when first dict is empty."""
        node = DictMergeNode(node_id="test_merge_empty_1")
        node.set_input_value("dict_1", {})
        node.set_input_value("dict_2", {"a": 1})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == {"a": 1}

    @pytest.mark.asyncio
    async def test_dict_merge_empty_second(self, execution_context):
        """Test merging when second dict is empty."""
        node = DictMergeNode(node_id="test_merge_empty_2")
        node.set_input_value("dict_1", {"a": 1})
        node.set_input_value("dict_2", {})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == {"a": 1}

    @pytest.mark.asyncio
    async def test_dict_merge_nested(self, execution_context):
        """Test merging dicts with nested values."""
        node = DictMergeNode(node_id="test_merge_nested")
        node.set_input_value("dict_1", {"user": {"name": "John"}})
        node.set_input_value("dict_2", {"user": {"age": 30}})

        result = await node.execute(execution_context)

        assert result["success"] is True
        # Shallow merge - second dict's user overwrites first
        assert node.get_output_value("result") == {"user": {"age": 30}}


class TestDictKeysValuesExtended:
    """Extended tests for DictKeysNode and DictValuesNode."""

    @pytest.mark.asyncio
    async def test_dict_keys_empty(self, execution_context):
        """Test getting keys from empty dict."""
        node = DictKeysNode(node_id="test_keys_empty")
        node.set_input_value("dict", {})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("keys") == []
        assert node.get_output_value("count") == 0

    @pytest.mark.asyncio
    async def test_dict_values_empty(self, execution_context):
        """Test getting values from empty dict."""
        node = DictValuesNode(node_id="test_values_empty")
        node.set_input_value("dict", {})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("values") == []
        assert node.get_output_value("count") == 0

    @pytest.mark.asyncio
    async def test_dict_keys_invalid(self, execution_context):
        """Test keys with invalid input."""
        node = DictKeysNode(node_id="test_keys_invalid")
        node.set_input_value("dict", [1, 2, 3])

        result = await node.execute(execution_context)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_dict_values_invalid(self, execution_context):
        """Test values with invalid input."""
        node = DictValuesNode(node_id="test_values_invalid")
        node.set_input_value("dict", "not a dict")

        result = await node.execute(execution_context)

        assert result["success"] is False


class TestDictRemoveNodeExtended:
    """Extended tests for DictRemoveNode."""

    @pytest.mark.asyncio
    async def test_dict_remove_last_key(self, execution_context):
        """Test removing the only key."""
        node = DictRemoveNode(node_id="test_remove_last")
        node.set_input_value("dict", {"only": "key"})
        node.set_input_value("key", "only")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == {}
        assert node.get_output_value("removed_value") == "key"

    @pytest.mark.asyncio
    async def test_dict_remove_invalid(self, execution_context):
        """Test remove with invalid input type."""
        node = DictRemoveNode(node_id="test_remove_invalid")
        node.set_input_value("dict", [1, 2])
        node.set_input_value("key", "key")

        result = await node.execute(execution_context)

        assert result["success"] is False


class TestDictItemsNodeExtended:
    """Extended tests for DictItemsNode."""

    @pytest.mark.asyncio
    async def test_dict_items_empty(self, execution_context):
        """Test items from empty dict."""
        node = DictItemsNode(node_id="test_items_empty")
        node.set_input_value("dict", {})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("items") == []
        assert node.get_output_value("count") == 0

    @pytest.mark.asyncio
    async def test_dict_items_invalid(self, execution_context):
        """Test items with invalid input."""
        node = DictItemsNode(node_id="test_items_invalid")
        node.set_input_value("dict", "not a dict")

        result = await node.execute(execution_context)

        assert result["success"] is False


class TestDictHasKeyNodeExtended:
    """Extended tests for DictHasKeyNode."""

    @pytest.mark.asyncio
    async def test_has_key_empty_string(self, execution_context):
        """Test checking for empty string key."""
        node = DictHasKeyNode(node_id="test_has_empty")
        node.set_input_value("dict", {"": "empty key"})
        node.set_input_value("key", "")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("has_key") is True

    @pytest.mark.asyncio
    async def test_has_key_invalid(self, execution_context):
        """Test has_key with invalid input."""
        node = DictHasKeyNode(node_id="test_has_invalid")
        node.set_input_value("dict", 123)
        node.set_input_value("key", "key")

        result = await node.execute(execution_context)

        assert result["success"] is False


class TestCreateDictNodeExtended:
    """Extended tests for CreateDictNode."""

    @pytest.mark.asyncio
    async def test_create_dict_partial_keys(self, execution_context):
        """Test creating dict with some null keys."""
        node = CreateDictNode(node_id="test_create_partial")
        node.set_input_value("key_1", "name")
        node.set_input_value("value_1", "John")
        # key_2 not set
        node.set_input_value("key_3", "age")
        node.set_input_value("value_3", 30)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("dict") == {"name": "John", "age": 30}

    @pytest.mark.asyncio
    async def test_create_dict_empty(self, execution_context):
        """Test creating empty dict."""
        node = CreateDictNode(node_id="test_create_empty")
        # No keys set

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("dict") == {}


class TestDictToJsonNodeExtended:
    """Extended tests for DictToJsonNode."""

    @pytest.mark.asyncio
    async def test_to_json_sorted_keys(self, execution_context):
        """Test JSON with sorted keys."""
        node = DictToJsonNode(node_id="test_json_sorted", config={"sort_keys": True})
        node.set_input_value("dict", {"c": 3, "a": 1, "b": 2})

        result = await node.execute(execution_context)

        assert result["success"] is True
        json_str = node.get_output_value("json_string")
        # Keys should be sorted
        assert json_str.index('"a"') < json_str.index('"b"') < json_str.index('"c"')

    @pytest.mark.asyncio
    async def test_to_json_nested(self, execution_context):
        """Test JSON with nested structures."""
        node = DictToJsonNode(node_id="test_json_nested")
        node.set_input_value("dict", {"list": [1, 2], "nested": {"a": 1}})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "[1, 2]" in node.get_output_value(
            "json_string"
        ) or "[1,2]" in node.get_output_value("json_string")


# =============================================================================
# Additional Math Operations Tests
# =============================================================================


class TestMathOperationNodeExtended:
    """Extended tests for MathOperationNode."""

    @pytest.mark.asyncio
    async def test_math_floor_divide(self, execution_context):
        """Test floor division."""
        node = MathOperationNode(
            node_id="test_floor_div", config={"operation": "floor_divide"}
        )
        node.set_input_value("a", 17)
        node.set_input_value("b", 5)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 3.0

    @pytest.mark.asyncio
    async def test_math_floor_divide_by_zero(self, execution_context):
        """Test floor division by zero."""
        node = MathOperationNode(
            node_id="test_floor_div_zero", config={"operation": "floor_divide"}
        )
        node.set_input_value("a", 10)
        node.set_input_value("b", 0)

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "zero" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_math_sin(self, execution_context):
        """Test sine function."""
        import math

        node = MathOperationNode(node_id="test_sin", config={"operation": "sin"})
        node.set_input_value("a", 0)
        node.set_input_value("b", 0)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 0.0

    @pytest.mark.asyncio
    async def test_math_cos(self, execution_context):
        """Test cosine function."""
        node = MathOperationNode(node_id="test_cos", config={"operation": "cos"})
        node.set_input_value("a", 0)
        node.set_input_value("b", 0)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 1.0

    @pytest.mark.asyncio
    async def test_math_tan(self, execution_context):
        """Test tangent function."""
        node = MathOperationNode(node_id="test_tan", config={"operation": "tan"})
        node.set_input_value("a", 0)
        node.set_input_value("b", 0)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 0.0

    @pytest.mark.asyncio
    async def test_math_log(self, execution_context):
        """Test natural logarithm."""
        import math

        node = MathOperationNode(node_id="test_log", config={"operation": "log"})
        node.set_input_value("a", math.e)
        node.set_input_value("b", 0)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert abs(node.get_output_value("result") - 1.0) < 0.0001

    @pytest.mark.asyncio
    async def test_math_log_with_base(self, execution_context):
        """Test logarithm with custom base."""
        node = MathOperationNode(node_id="test_log_base", config={"operation": "log"})
        node.set_input_value("a", 8)
        node.set_input_value("b", 2)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 3.0

    @pytest.mark.asyncio
    async def test_math_log10(self, execution_context):
        """Test base-10 logarithm."""
        node = MathOperationNode(node_id="test_log10", config={"operation": "log10"})
        node.set_input_value("a", 100)
        node.set_input_value("b", 0)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 2.0

    @pytest.mark.asyncio
    async def test_math_exp(self, execution_context):
        """Test exponential function."""
        node = MathOperationNode(node_id="test_exp", config={"operation": "exp"})
        node.set_input_value("a", 0)
        node.set_input_value("b", 0)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 1.0

    @pytest.mark.asyncio
    async def test_math_negate(self, execution_context):
        """Test negation."""
        node = MathOperationNode(node_id="test_negate", config={"operation": "negate"})
        node.set_input_value("a", 42)
        node.set_input_value("b", 0)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == -42.0

    @pytest.mark.asyncio
    async def test_math_round_operation(self, execution_context):
        """Test round operation."""
        node = MathOperationNode(node_id="test_round_op", config={"operation": "round"})
        node.set_input_value("a", 3.7)
        node.set_input_value("b", 0)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 4.0

    @pytest.mark.asyncio
    async def test_math_unknown_operation(self, execution_context):
        """Test error on unknown operation."""
        node = MathOperationNode(
            node_id="test_unknown", config={"operation": "unknown"}
        )
        node.set_input_value("a", 1)
        node.set_input_value("b", 1)

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "unknown" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_math_negative_sqrt(self, execution_context):
        """Test sqrt of negative number."""
        node = MathOperationNode(node_id="test_neg_sqrt", config={"operation": "sqrt"})
        node.set_input_value("a", -1)
        node.set_input_value("b", 0)

        result = await node.execute(execution_context)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_math_type_coercion(self, execution_context):
        """Test type coercion from strings."""
        node = MathOperationNode(node_id="test_coerce", config={"operation": "add"})
        node.set_input_value("a", "5")
        node.set_input_value("b", "3")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 8.0


class TestComparisonNodeExtended:
    """Extended tests for ComparisonNode."""

    @pytest.mark.asyncio
    async def test_comparison_descriptive_equals(self, execution_context):
        """Test descriptive format for equality."""
        node = ComparisonNode(
            node_id="test_desc_eq", config={"operator": "equals (==)"}
        )
        node.set_input_value("a", 5)
        node.set_input_value("b", 5)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") is True

    @pytest.mark.asyncio
    async def test_comparison_descriptive_not_equals(self, execution_context):
        """Test descriptive format for not equals."""
        node = ComparisonNode(
            node_id="test_desc_neq", config={"operator": "not equals (!=)"}
        )
        node.set_input_value("a", 5)
        node.set_input_value("b", 10)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") is True

    @pytest.mark.asyncio
    async def test_comparison_descriptive_greater(self, execution_context):
        """Test descriptive format for greater than."""
        node = ComparisonNode(
            node_id="test_desc_gt", config={"operator": "greater than (>)"}
        )
        node.set_input_value("a", 10)
        node.set_input_value("b", 5)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") is True

    @pytest.mark.asyncio
    async def test_comparison_descriptive_less(self, execution_context):
        """Test descriptive format for less than."""
        node = ComparisonNode(
            node_id="test_desc_lt", config={"operator": "less than (<)"}
        )
        node.set_input_value("a", 3)
        node.set_input_value("b", 10)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") is True

    @pytest.mark.asyncio
    async def test_comparison_unknown_operator(self, execution_context):
        """Test error on unknown operator."""
        node = ComparisonNode(node_id="test_unknown_op", config={"operator": "???"})
        node.set_input_value("a", 5)
        node.set_input_value("b", 5)

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "unknown" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_comparison_none_values(self, execution_context):
        """Test comparing None values."""
        node = ComparisonNode(node_id="test_none", config={"operator": "=="})
        node.set_input_value("a", None)
        node.set_input_value("b", None)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") is True


# =============================================================================
# Regex Extended Tests
# =============================================================================


class TestRegexMatchNodeExtended:
    """Extended tests for RegexMatchNode."""

    @pytest.mark.asyncio
    async def test_regex_multiline(self, execution_context):
        """Test multiline regex mode."""
        node = RegexMatchNode(node_id="test_regex_ml", config={"multiline": True})
        node.set_input_value("text", "line1\nline2\nline3")
        node.set_input_value("pattern", r"^line")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("match_count") == 3

    @pytest.mark.asyncio
    async def test_regex_dotall(self, execution_context):
        """Test dotall regex mode."""
        node = RegexMatchNode(node_id="test_regex_dotall", config={"dotall": True})
        node.set_input_value("text", "start\nend")
        node.set_input_value("pattern", r"start.end")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("match_found") is True

    @pytest.mark.asyncio
    async def test_regex_invalid_pattern(self, execution_context):
        """Test invalid regex pattern."""
        node = RegexMatchNode(node_id="test_regex_invalid")
        node.set_input_value("text", "test")
        node.set_input_value("pattern", r"[invalid")

        result = await node.execute(execution_context)

        assert result["success"] is False


class TestRegexReplaceNodeExtended:
    """Extended tests for RegexReplaceNode."""

    @pytest.mark.asyncio
    async def test_regex_replace_case_insensitive(self, execution_context):
        """Test case-insensitive replacement."""
        node = RegexReplaceNode(node_id="test_replace_ci", config={"ignore_case": True})
        node.set_input_value("text", "Hello HELLO hello")
        node.set_input_value("pattern", r"hello")
        node.set_input_value("replacement", "hi")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "hi hi hi"
        assert node.get_output_value("count") == 3

    @pytest.mark.asyncio
    async def test_regex_replace_invalid_pattern(self, execution_context):
        """Test replacement with invalid pattern."""
        node = RegexReplaceNode(node_id="test_replace_invalid")
        node.set_input_value("text", "test")
        node.set_input_value("pattern", r"[invalid")
        node.set_input_value("replacement", "x")

        result = await node.execute(execution_context)

        assert result["success"] is False


# =============================================================================
# ExecutionResult Compliance Tests
# =============================================================================


class TestExecutionResultCompliance:
    """Tests verifying ExecutionResult pattern compliance."""

    @pytest.mark.asyncio
    async def test_list_node_result_structure(self, execution_context):
        """Test list node returns proper ExecutionResult."""
        node = ListAppendNode(node_id="test_result")
        node.set_input_value("list", [1, 2])
        node.set_input_value("item", 3)

        result = await node.execute(execution_context)

        assert "success" in result
        assert "next_nodes" in result
        assert isinstance(result["success"], bool)
        assert isinstance(result["next_nodes"], list)

    @pytest.mark.asyncio
    async def test_dict_node_result_structure(self, execution_context):
        """Test dict node returns proper ExecutionResult."""
        node = DictSetNode(node_id="test_result")
        node.set_input_value("dict", {})
        node.set_input_value("key", "test")
        node.set_input_value("value", 123)

        result = await node.execute(execution_context)

        assert "success" in result
        assert "data" in result
        assert "next_nodes" in result

    @pytest.mark.asyncio
    async def test_math_node_result_structure(self, execution_context):
        """Test math node returns proper ExecutionResult."""
        node = MathOperationNode(node_id="test_result", config={"operation": "add"})
        node.set_input_value("a", 1)
        node.set_input_value("b", 2)

        result = await node.execute(execution_context)

        assert "success" in result
        assert result["success"] is True
        assert "data" in result
        assert "result" in result["data"]

    @pytest.mark.asyncio
    async def test_error_result_structure(self, execution_context):
        """Test error returns proper ExecutionResult."""
        node = ListGetItemNode(node_id="test_error")
        node.set_input_value("list", [1, 2])
        node.set_input_value("index", 100)

        result = await node.execute(execution_context)

        assert "success" in result
        assert result["success"] is False
        assert "error" in result
        assert isinstance(result["error"], str)
