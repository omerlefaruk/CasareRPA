"""
Tests for data operation nodes.

Tests string manipulation, regex operations, math, comparisons, lists, and JSON parsing.
"""

import pytest

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
)
from casare_rpa.core.types import NodeStatus, DataType


class TestConcatenateNode:
    """Tests for string concatenation."""

    @pytest.mark.asyncio
    async def test_concatenate_two_strings(self, execution_context):
        """Test basic string concatenation."""
        node = ConcatenateNode(node_id="concat_1")
        node.set_input_value("string_1", "Hello")
        node.set_input_value("string_2", "World")

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == "HelloWorld"

    @pytest.mark.asyncio
    async def test_concatenate_with_separator(self, execution_context):
        """Test concatenation with custom separator."""
        node = ConcatenateNode(node_id="concat_1", config={"separator": " "})
        node.set_input_value("string_1", "Hello")
        node.set_input_value("string_2", "World")

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == "Hello World"

    @pytest.mark.asyncio
    async def test_concatenate_with_comma_separator(self, execution_context):
        """Test concatenation with comma separator."""
        node = ConcatenateNode(node_id="concat_1", config={"separator": ", "})
        node.set_input_value("string_1", "apple")
        node.set_input_value("string_2", "banana")

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == "apple, banana"

    @pytest.mark.asyncio
    async def test_concatenate_empty_strings(self, execution_context):
        """Test concatenation with empty strings."""
        node = ConcatenateNode(node_id="concat_1")
        node.set_input_value("string_1", "")
        node.set_input_value("string_2", "")

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == ""

    @pytest.mark.asyncio
    async def test_concatenate_converts_numbers(self, execution_context):
        """Test that numbers are converted to strings."""
        node = ConcatenateNode(node_id="concat_1")
        node.set_input_value("string_1", 123)
        node.set_input_value("string_2", 456)

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == "123456"


class TestFormatStringNode:
    """Tests for string formatting."""

    @pytest.mark.asyncio
    async def test_format_simple_template(self, execution_context):
        """Test formatting a simple template."""
        node = FormatStringNode(node_id="format_1")
        node.set_input_value("template", "Hello, {name}!")
        node.set_input_value("variables", {"name": "Alice"})

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == "Hello, Alice!"

    @pytest.mark.asyncio
    async def test_format_multiple_variables(self, execution_context):
        """Test formatting with multiple variables."""
        node = FormatStringNode(node_id="format_1")
        node.set_input_value("template", "{greeting} {name}, you have {count} messages.")
        node.set_input_value("variables", {
            "greeting": "Hi",
            "name": "Bob",
            "count": 5
        })

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == "Hi Bob, you have 5 messages."

    @pytest.mark.asyncio
    async def test_format_with_number_formatting(self, execution_context):
        """Test formatting numbers with format specifiers."""
        node = FormatStringNode(node_id="format_1")
        node.set_input_value("template", "Price: ${price:.2f}")
        node.set_input_value("variables", {"price": 19.999})

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == "Price: $20.00"

    @pytest.mark.asyncio
    async def test_format_invalid_variables_type(self, execution_context):
        """Test that non-dict variables cause error."""
        node = FormatStringNode(node_id="format_1")
        node.set_input_value("template", "Hello {name}")
        node.set_input_value("variables", "not a dict")

        result = await node.execute(execution_context)

        assert result == NodeStatus.ERROR
        assert "dictionary" in node.error_message.lower()


class TestRegexMatchNode:
    """Tests for regex pattern matching."""

    @pytest.mark.asyncio
    async def test_regex_simple_match(self, execution_context):
        """Test simple regex match."""
        node = RegexMatchNode(node_id="regex_1")
        node.set_input_value("text", "The quick brown fox")
        node.set_input_value("pattern", r"quick")

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("match_found") is True
        assert node.get_output_value("first_match") == "quick"

    @pytest.mark.asyncio
    async def test_regex_no_match(self, execution_context):
        """Test regex with no match."""
        node = RegexMatchNode(node_id="regex_1")
        node.set_input_value("text", "Hello World")
        node.set_input_value("pattern", r"xyz")

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("match_found") is False
        assert node.get_output_value("first_match") == ""
        assert node.get_output_value("all_matches") == []

    @pytest.mark.asyncio
    async def test_regex_multiple_matches(self, execution_context):
        """Test finding multiple matches."""
        node = RegexMatchNode(node_id="regex_1")
        node.set_input_value("text", "abc123def456ghi789")
        node.set_input_value("pattern", r"\d+")

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("match_found") is True
        assert node.get_output_value("first_match") == "123"
        assert node.get_output_value("all_matches") == ["123", "456", "789"]

    @pytest.mark.asyncio
    async def test_regex_with_groups(self, execution_context):
        """Test regex with capture groups."""
        node = RegexMatchNode(node_id="regex_1")
        node.set_input_value("text", "John Doe, age 30")
        node.set_input_value("pattern", r"(\w+) (\w+), age (\d+)")

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("match_found") is True
        groups = node.get_output_value("groups")
        assert groups == ["John", "Doe", "30"]

    @pytest.mark.asyncio
    async def test_regex_email_pattern(self, execution_context):
        """Test extracting emails with regex."""
        node = RegexMatchNode(node_id="regex_1")
        node.set_input_value("text", "Contact us at support@example.com or sales@company.org")
        node.set_input_value("pattern", r"[\w.-]+@[\w.-]+\.\w+")

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("match_found") is True
        assert "support@example.com" in node.get_output_value("all_matches")
        assert "sales@company.org" in node.get_output_value("all_matches")


class TestRegexReplaceNode:
    """Tests for regex replacement."""

    @pytest.mark.asyncio
    async def test_regex_simple_replace(self, execution_context):
        """Test simple replacement."""
        node = RegexReplaceNode(node_id="regex_replace_1")
        node.set_input_value("text", "Hello World")
        node.set_input_value("pattern", r"World")
        node.set_input_value("replacement", "Universe")

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == "Hello Universe"
        assert node.get_output_value("count") == 1

    @pytest.mark.asyncio
    async def test_regex_replace_all_occurrences(self, execution_context):
        """Test replacing all occurrences."""
        node = RegexReplaceNode(node_id="regex_replace_1")
        node.set_input_value("text", "cat and cat and cat")
        node.set_input_value("pattern", r"cat")
        node.set_input_value("replacement", "dog")

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == "dog and dog and dog"
        assert node.get_output_value("count") == 3

    @pytest.mark.asyncio
    async def test_regex_replace_with_groups(self, execution_context):
        """Test replacement using captured groups."""
        node = RegexReplaceNode(node_id="regex_replace_1")
        node.set_input_value("text", "2023-12-25")
        node.set_input_value("pattern", r"(\d{4})-(\d{2})-(\d{2})")
        node.set_input_value("replacement", r"\3/\2/\1")

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == "25/12/2023"

    @pytest.mark.asyncio
    async def test_regex_remove_whitespace(self, execution_context):
        """Test removing extra whitespace."""
        node = RegexReplaceNode(node_id="regex_replace_1")
        node.set_input_value("text", "Hello    World    Test")
        node.set_input_value("pattern", r"\s+")
        node.set_input_value("replacement", " ")

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == "Hello World Test"


class TestMathOperationNode:
    """Tests for math operations."""

    @pytest.mark.asyncio
    async def test_math_addition(self, execution_context):
        """Test addition."""
        node = MathOperationNode(node_id="math_1", config={"operation": "add"})
        node.set_input_value("a", 10)
        node.set_input_value("b", 5)

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == 15.0

    @pytest.mark.asyncio
    async def test_math_subtraction(self, execution_context):
        """Test subtraction."""
        node = MathOperationNode(node_id="math_1", config={"operation": "subtract"})
        node.set_input_value("a", 10)
        node.set_input_value("b", 3)

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == 7.0

    @pytest.mark.asyncio
    async def test_math_multiplication(self, execution_context):
        """Test multiplication."""
        node = MathOperationNode(node_id="math_1", config={"operation": "multiply"})
        node.set_input_value("a", 7)
        node.set_input_value("b", 6)

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == 42.0

    @pytest.mark.asyncio
    async def test_math_division(self, execution_context):
        """Test division."""
        node = MathOperationNode(node_id="math_1", config={"operation": "divide"})
        node.set_input_value("a", 20)
        node.set_input_value("b", 4)

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == 5.0

    @pytest.mark.asyncio
    async def test_math_division_by_zero(self, execution_context):
        """Test division by zero raises error."""
        node = MathOperationNode(node_id="math_1", config={"operation": "divide"})
        node.set_input_value("a", 10)
        node.set_input_value("b", 0)

        result = await node.execute(execution_context)

        assert result == NodeStatus.ERROR
        assert "zero" in node.error_message.lower()

    @pytest.mark.asyncio
    async def test_math_power(self, execution_context):
        """Test power operation."""
        node = MathOperationNode(node_id="math_1", config={"operation": "power"})
        node.set_input_value("a", 2)
        node.set_input_value("b", 10)

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == 1024.0

    @pytest.mark.asyncio
    async def test_math_modulo(self, execution_context):
        """Test modulo operation."""
        node = MathOperationNode(node_id="math_1", config={"operation": "modulo"})
        node.set_input_value("a", 17)
        node.set_input_value("b", 5)

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") == 2.0

    @pytest.mark.asyncio
    async def test_math_with_floats(self, execution_context):
        """Test math with floating point numbers."""
        node = MathOperationNode(node_id="math_1", config={"operation": "add"})
        node.set_input_value("a", 3.14)
        node.set_input_value("b", 2.86)

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert abs(node.get_output_value("result") - 6.0) < 0.0001

    @pytest.mark.asyncio
    async def test_math_unknown_operation(self, execution_context):
        """Test unknown operation raises error."""
        node = MathOperationNode(node_id="math_1", config={"operation": "invalid"})
        node.set_input_value("a", 1)
        node.set_input_value("b", 1)

        result = await node.execute(execution_context)

        assert result == NodeStatus.ERROR
        assert "unknown" in node.error_message.lower()


class TestComparisonNode:
    """Tests for comparison operations."""

    @pytest.mark.asyncio
    async def test_comparison_equals_true(self, execution_context):
        """Test equality comparison - true case."""
        node = ComparisonNode(node_id="cmp_1", config={"operator": "=="})
        node.set_input_value("a", 5)
        node.set_input_value("b", 5)

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") is True

    @pytest.mark.asyncio
    async def test_comparison_equals_false(self, execution_context):
        """Test equality comparison - false case."""
        node = ComparisonNode(node_id="cmp_1", config={"operator": "=="})
        node.set_input_value("a", 5)
        node.set_input_value("b", 10)

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") is False

    @pytest.mark.asyncio
    async def test_comparison_not_equals(self, execution_context):
        """Test not equals comparison."""
        node = ComparisonNode(node_id="cmp_1", config={"operator": "!="})
        node.set_input_value("a", "hello")
        node.set_input_value("b", "world")

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") is True

    @pytest.mark.asyncio
    async def test_comparison_greater_than(self, execution_context):
        """Test greater than comparison."""
        node = ComparisonNode(node_id="cmp_1", config={"operator": ">"})
        node.set_input_value("a", 10)
        node.set_input_value("b", 5)

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") is True

    @pytest.mark.asyncio
    async def test_comparison_less_than(self, execution_context):
        """Test less than comparison."""
        node = ComparisonNode(node_id="cmp_1", config={"operator": "<"})
        node.set_input_value("a", 3)
        node.set_input_value("b", 7)

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") is True

    @pytest.mark.asyncio
    async def test_comparison_greater_or_equal(self, execution_context):
        """Test greater or equal comparison."""
        node = ComparisonNode(node_id="cmp_1", config={"operator": ">="})
        node.set_input_value("a", 5)
        node.set_input_value("b", 5)

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") is True

    @pytest.mark.asyncio
    async def test_comparison_less_or_equal(self, execution_context):
        """Test less or equal comparison."""
        node = ComparisonNode(node_id="cmp_1", config={"operator": "<="})
        node.set_input_value("a", 3)
        node.set_input_value("b", 3)

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") is True

    @pytest.mark.asyncio
    async def test_comparison_descriptive_operator(self, execution_context):
        """Test comparison with descriptive operator format."""
        node = ComparisonNode(node_id="cmp_1", config={"operator": "equals (==)"})
        node.set_input_value("a", "test")
        node.set_input_value("b", "test")

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") is True

    @pytest.mark.asyncio
    async def test_comparison_string_values(self, execution_context):
        """Test comparison with string values."""
        node = ComparisonNode(node_id="cmp_1", config={"operator": ">"})
        node.set_input_value("a", "banana")
        node.set_input_value("b", "apple")

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("result") is True  # 'banana' > 'apple' alphabetically


class TestCreateListNode:
    """Tests for list creation."""

    @pytest.mark.asyncio
    async def test_create_list_with_items(self, execution_context):
        """Test creating a list with items."""
        node = CreateListNode(node_id="list_1")
        node.set_input_value("item_1", "apple")
        node.set_input_value("item_2", "banana")
        node.set_input_value("item_3", "cherry")

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("list") == ["apple", "banana", "cherry"]

    @pytest.mark.asyncio
    async def test_create_list_partial_items(self, execution_context):
        """Test creating a list with some items."""
        node = CreateListNode(node_id="list_1")
        node.set_input_value("item_1", "one")
        node.set_input_value("item_2", "two")
        # item_3 not set

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("list") == ["one", "two"]

    @pytest.mark.asyncio
    async def test_create_list_mixed_types(self, execution_context):
        """Test creating a list with mixed types."""
        node = CreateListNode(node_id="list_1")
        node.set_input_value("item_1", 42)
        node.set_input_value("item_2", "text")
        node.set_input_value("item_3", True)

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("list") == [42, "text", True]


class TestListGetItemNode:
    """Tests for getting items from lists."""

    @pytest.mark.asyncio
    async def test_get_first_item(self, execution_context):
        """Test getting the first item."""
        node = ListGetItemNode(node_id="get_1")
        node.set_input_value("list", ["a", "b", "c"])
        node.set_input_value("index", 0)

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("item") == "a"

    @pytest.mark.asyncio
    async def test_get_last_item(self, execution_context):
        """Test getting the last item with negative index."""
        node = ListGetItemNode(node_id="get_1")
        node.set_input_value("list", ["a", "b", "c"])
        node.set_input_value("index", -1)

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("item") == "c"

    @pytest.mark.asyncio
    async def test_get_middle_item(self, execution_context):
        """Test getting a middle item."""
        node = ListGetItemNode(node_id="get_1")
        node.set_input_value("list", [10, 20, 30, 40, 50])
        node.set_input_value("index", 2)

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("item") == 30

    @pytest.mark.asyncio
    async def test_get_out_of_range(self, execution_context):
        """Test getting an index out of range."""
        node = ListGetItemNode(node_id="get_1")
        node.set_input_value("list", ["a", "b"])
        node.set_input_value("index", 5)

        result = await node.execute(execution_context)

        assert result == NodeStatus.ERROR
        assert "out of range" in node.error_message.lower()

    @pytest.mark.asyncio
    async def test_get_from_tuple(self, execution_context):
        """Test getting item from a tuple."""
        node = ListGetItemNode(node_id="get_1")
        node.set_input_value("list", (1, 2, 3))
        node.set_input_value("index", 1)

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("item") == 2


class TestJsonParseNode:
    """Tests for JSON parsing."""

    @pytest.mark.asyncio
    async def test_parse_simple_object(self, execution_context):
        """Test parsing a simple JSON object."""
        node = JsonParseNode(node_id="json_1")
        node.set_input_value("json_string", '{"name": "John", "age": 30}')

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        data = node.get_output_value("data")
        assert data == {"name": "John", "age": 30}

    @pytest.mark.asyncio
    async def test_parse_array(self, execution_context):
        """Test parsing a JSON array."""
        node = JsonParseNode(node_id="json_1")
        node.set_input_value("json_string", '[1, 2, 3, "four", true]')

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        data = node.get_output_value("data")
        assert data == [1, 2, 3, "four", True]

    @pytest.mark.asyncio
    async def test_parse_nested_object(self, execution_context):
        """Test parsing a nested JSON object."""
        node = JsonParseNode(node_id="json_1")
        json_str = '{"user": {"name": "Alice", "address": {"city": "NYC"}}}'
        node.set_input_value("json_string", json_str)

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        data = node.get_output_value("data")
        assert data["user"]["address"]["city"] == "NYC"

    @pytest.mark.asyncio
    async def test_parse_invalid_json(self, execution_context):
        """Test parsing invalid JSON raises error."""
        node = JsonParseNode(node_id="json_1")
        node.set_input_value("json_string", "not valid json {")

        result = await node.execute(execution_context)

        assert result == NodeStatus.ERROR

    @pytest.mark.asyncio
    async def test_parse_empty_string(self, execution_context):
        """Test parsing empty string raises error."""
        node = JsonParseNode(node_id="json_1")
        node.set_input_value("json_string", "")

        result = await node.execute(execution_context)

        assert result == NodeStatus.ERROR


class TestGetPropertyNode:
    """Tests for getting properties from objects."""

    @pytest.mark.asyncio
    async def test_get_simple_property(self, execution_context):
        """Test getting a simple property."""
        node = GetPropertyNode(node_id="prop_1")
        node.set_input_value("object", {"name": "John", "age": 30})
        node.set_input_value("property_path", "name")

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("value") == "John"

    @pytest.mark.asyncio
    async def test_get_nested_property(self, execution_context):
        """Test getting a nested property with dot notation."""
        node = GetPropertyNode(node_id="prop_1")
        node.set_input_value("object", {
            "user": {
                "profile": {
                    "email": "john@example.com"
                }
            }
        })
        node.set_input_value("property_path", "user.profile.email")

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("value") == "john@example.com"

    @pytest.mark.asyncio
    async def test_get_missing_property(self, execution_context):
        """Test getting a missing property returns None."""
        node = GetPropertyNode(node_id="prop_1")
        node.set_input_value("object", {"name": "John"})
        node.set_input_value("property_path", "address")

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("value") is None

    @pytest.mark.asyncio
    async def test_get_deeply_nested_missing(self, execution_context):
        """Test getting a deeply nested missing property."""
        node = GetPropertyNode(node_id="prop_1")
        node.set_input_value("object", {"level1": {"level2": {}}})
        node.set_input_value("property_path", "level1.level2.level3.level4")

        result = await node.execute(execution_context)

        assert result == NodeStatus.SUCCESS
        assert node.get_output_value("value") is None


class TestDataOperationScenarios:
    """Integration tests combining multiple data operation nodes."""

    @pytest.mark.asyncio
    async def test_parse_json_and_get_property(self, execution_context):
        """Test parsing JSON and extracting a property."""
        # Parse JSON
        json_node = JsonParseNode(node_id="json_1")
        json_node.set_input_value("json_string", '{"user": {"name": "Alice", "score": 95}}')
        await json_node.execute(execution_context)

        # Get property
        prop_node = GetPropertyNode(node_id="prop_1")
        prop_node.set_input_value("object", json_node.get_output_value("data"))
        prop_node.set_input_value("property_path", "user.name")
        await prop_node.execute(execution_context)

        assert prop_node.get_output_value("value") == "Alice"

    @pytest.mark.asyncio
    async def test_extract_email_and_format_greeting(self, execution_context):
        """Test extracting email and creating a greeting."""
        # Extract email
        regex_node = RegexMatchNode(node_id="regex_1")
        regex_node.set_input_value("text", "Contact: alice@example.com for info")
        regex_node.set_input_value("pattern", r"([\w.]+)@")
        await regex_node.execute(execution_context)

        # Get username from email
        username = regex_node.get_output_value("groups")[0]

        # Format greeting
        format_node = FormatStringNode(node_id="format_1")
        format_node.set_input_value("template", "Hello, {name}! Welcome back.")
        format_node.set_input_value("variables", {"name": username.capitalize()})
        await format_node.execute(execution_context)

        assert format_node.get_output_value("result") == "Hello, Alice! Welcome back."

    @pytest.mark.asyncio
    async def test_calculate_and_compare(self, execution_context):
        """Test calculating a value and comparing it."""
        # Calculate: 5 * 10 = 50
        math_node = MathOperationNode(node_id="math_1", config={"operation": "multiply"})
        math_node.set_input_value("a", 5)
        math_node.set_input_value("b", 10)
        await math_node.execute(execution_context)

        # Compare if result >= 50
        cmp_node = ComparisonNode(node_id="cmp_1", config={"operator": ">="})
        cmp_node.set_input_value("a", math_node.get_output_value("result"))
        cmp_node.set_input_value("b", 50)
        await cmp_node.execute(execution_context)

        assert cmp_node.get_output_value("result") is True

    @pytest.mark.asyncio
    async def test_build_url_from_parts(self, execution_context):
        """Test building a URL from parts using concatenation."""
        # Concatenate base URL
        concat1 = ConcatenateNode(node_id="concat_1")
        concat1.set_input_value("string_1", "https://api.example.com")
        concat1.set_input_value("string_2", "/users/")
        await concat1.execute(execution_context)

        # Add user ID
        concat2 = ConcatenateNode(node_id="concat_2")
        concat2.set_input_value("string_1", concat1.get_output_value("result"))
        concat2.set_input_value("string_2", "12345")
        await concat2.execute(execution_context)

        assert concat2.get_output_value("result") == "https://api.example.com/users/12345"
