"""
Tests for Text operation nodes.

Tests 14 text nodes:
- TextSplitNode, TextJoinNode, TextReplaceNode, TextTrimNode
- TextCaseNode (upper, lower, title), TextExtractNode (regex match)
- TextSubstringNode, TextContainsNode, TextStartsWithNode, TextEndsWithNode
- TextLinesNode, TextReverseNode, TextCountNode, TextPadNode
"""

import pytest
from unittest.mock import Mock

# Uses execution_context fixture from conftest.py - no import needed


class TestTextSplitNode:
    """Tests for TextSplitNode."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_split_by_separator(self, execution_context) -> None:
        """Test splitting text by custom separator."""
        from casare_rpa.nodes.text_nodes import TextSplitNode

        node = TextSplitNode(node_id="test_split")
        node.set_input_value("text", "apple,banana,cherry")
        node.set_input_value("separator", ",")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == ["apple", "banana", "cherry"]
        assert node.get_output_value("count") == 3

    @pytest.mark.asyncio
    async def test_split_by_whitespace(self, execution_context) -> None:
        """Test splitting text by whitespace (default)."""
        from casare_rpa.nodes.text_nodes import TextSplitNode

        node = TextSplitNode(node_id="test_split_ws")
        node.set_input_value("text", "hello world  test")
        node.set_input_value("separator", None)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == ["hello", "world", "test"]

    @pytest.mark.asyncio
    async def test_split_with_max_split(self, execution_context) -> None:
        """Test splitting with max_split limit."""
        from casare_rpa.nodes.text_nodes import TextSplitNode

        node = TextSplitNode(node_id="test_split_max", config={"max_split": 2})
        node.set_input_value("text", "a,b,c,d")
        node.set_input_value("separator", ",")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == ["a", "b", "c,d"]

    @pytest.mark.asyncio
    async def test_split_empty_string(self, execution_context) -> None:
        """Test splitting empty string."""
        from casare_rpa.nodes.text_nodes import TextSplitNode

        node = TextSplitNode(node_id="test_split_empty")
        node.set_input_value("text", "")
        node.set_input_value("separator", ",")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == [""]


class TestTextJoinNode:
    """Tests for TextJoinNode."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_join_with_separator(self, execution_context) -> None:
        """Test joining list with separator."""
        from casare_rpa.nodes.text_nodes import TextJoinNode

        node = TextJoinNode(node_id="test_join")
        node.set_input_value("items", ["apple", "banana", "cherry"])
        node.set_input_value("separator", ", ")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "apple, banana, cherry"

    @pytest.mark.asyncio
    async def test_join_without_separator(self, execution_context) -> None:
        """Test joining list without separator."""
        from casare_rpa.nodes.text_nodes import TextJoinNode

        node = TextJoinNode(node_id="test_join_no_sep")
        node.set_input_value("items", ["a", "b", "c"])
        node.set_input_value("separator", "")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "abc"

    @pytest.mark.asyncio
    async def test_join_mixed_types(self, execution_context) -> None:
        """Test joining list with mixed types."""
        from casare_rpa.nodes.text_nodes import TextJoinNode

        node = TextJoinNode(node_id="test_join_mixed")
        node.set_input_value("items", [1, "two", 3.0])
        node.set_input_value("separator", "-")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "1-two-3.0"


class TestTextReplaceNode:
    """Tests for TextReplaceNode."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_replace_simple(self, execution_context) -> None:
        """Test simple text replacement."""
        from casare_rpa.nodes.text_nodes import TextReplaceNode

        node = TextReplaceNode(node_id="test_replace")
        node.set_input_value("text", "Hello World")
        node.set_input_value("old_value", "World")
        node.set_input_value("new_value", "Python")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "Hello Python"
        assert node.get_output_value("replacements") == 1

    @pytest.mark.asyncio
    async def test_replace_multiple(self, execution_context) -> None:
        """Test multiple replacements."""
        from casare_rpa.nodes.text_nodes import TextReplaceNode

        node = TextReplaceNode(node_id="test_replace_multi")
        node.set_input_value("text", "aa bb aa cc aa")
        node.set_input_value("old_value", "aa")
        node.set_input_value("new_value", "XX")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "XX bb XX cc XX"
        assert node.get_output_value("replacements") == 3

    @pytest.mark.asyncio
    async def test_replace_with_count_limit(self, execution_context) -> None:
        """Test replacement with count limit."""
        from casare_rpa.nodes.text_nodes import TextReplaceNode

        node = TextReplaceNode(node_id="test_replace_limit", config={"count": 2})
        node.set_input_value("text", "a a a a a")
        node.set_input_value("old_value", "a")
        node.set_input_value("new_value", "X")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "X X a a a"
        assert node.get_output_value("replacements") == 2

    @pytest.mark.asyncio
    async def test_replace_regex(self, execution_context) -> None:
        """Test regex replacement."""
        from casare_rpa.nodes.text_nodes import TextReplaceNode

        node = TextReplaceNode(node_id="test_replace_regex", config={"use_regex": True})
        node.set_input_value("text", "Price: $100.50")
        node.set_input_value("old_value", r"\$(\d+\.\d+)")
        node.set_input_value("new_value", r"USD \1")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "Price: USD 100.50"

    @pytest.mark.asyncio
    async def test_replace_case_insensitive(self, execution_context) -> None:
        """Test case-insensitive regex replacement."""
        from casare_rpa.nodes.text_nodes import TextReplaceNode

        node = TextReplaceNode(
            node_id="test_replace_ci", config={"use_regex": True, "ignore_case": True}
        )
        node.set_input_value("text", "Hello HELLO hello")
        node.set_input_value("old_value", "hello")
        node.set_input_value("new_value", "HI")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "HI HI HI"


class TestTextTrimNode:
    """Tests for TextTrimNode."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_trim_both(self, execution_context) -> None:
        """Test trimming both sides."""
        from casare_rpa.nodes.text_nodes import TextTrimNode

        node = TextTrimNode(node_id="test_trim")
        node.set_input_value("text", "  hello world  ")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "hello world"

    @pytest.mark.asyncio
    async def test_trim_left(self, execution_context) -> None:
        """Test trimming left side only."""
        from casare_rpa.nodes.text_nodes import TextTrimNode

        node = TextTrimNode(node_id="test_trim_left", config={"mode": "left"})
        node.set_input_value("text", "  hello  ")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "hello  "

    @pytest.mark.asyncio
    async def test_trim_right(self, execution_context) -> None:
        """Test trimming right side only."""
        from casare_rpa.nodes.text_nodes import TextTrimNode

        node = TextTrimNode(node_id="test_trim_right", config={"mode": "right"})
        node.set_input_value("text", "  hello  ")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "  hello"

    @pytest.mark.asyncio
    async def test_trim_custom_chars(self, execution_context) -> None:
        """Test trimming custom characters."""
        from casare_rpa.nodes.text_nodes import TextTrimNode

        node = TextTrimNode(node_id="test_trim_custom", config={"characters": "-_"})
        node.set_input_value("text", "--_hello_--")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "hello"


class TestTextCaseNode:
    """Tests for TextCaseNode."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_case_upper(self, execution_context) -> None:
        """Test uppercase conversion."""
        from casare_rpa.nodes.text_nodes import TextCaseNode

        node = TextCaseNode(node_id="test_upper", config={"case": "upper"})
        node.set_input_value("text", "Hello World")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "HELLO WORLD"

    @pytest.mark.asyncio
    async def test_case_lower(self, execution_context) -> None:
        """Test lowercase conversion."""
        from casare_rpa.nodes.text_nodes import TextCaseNode

        node = TextCaseNode(node_id="test_lower", config={"case": "lower"})
        node.set_input_value("text", "Hello World")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "hello world"

    @pytest.mark.asyncio
    async def test_case_title(self, execution_context) -> None:
        """Test title case conversion."""
        from casare_rpa.nodes.text_nodes import TextCaseNode

        node = TextCaseNode(node_id="test_title", config={"case": "title"})
        node.set_input_value("text", "hello world")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "Hello World"

    @pytest.mark.asyncio
    async def test_case_capitalize(self, execution_context) -> None:
        """Test capitalize conversion."""
        from casare_rpa.nodes.text_nodes import TextCaseNode

        node = TextCaseNode(node_id="test_cap", config={"case": "capitalize"})
        node.set_input_value("text", "hello WORLD")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "Hello world"

    @pytest.mark.asyncio
    async def test_case_swapcase(self, execution_context) -> None:
        """Test swapcase conversion."""
        from casare_rpa.nodes.text_nodes import TextCaseNode

        node = TextCaseNode(node_id="test_swap", config={"case": "swapcase"})
        node.set_input_value("text", "Hello World")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "hELLO wORLD"


class TestTextExtractNode:
    """Tests for TextExtractNode (regex matching)."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_extract_single_match(self, execution_context) -> None:
        """Test extracting single regex match."""
        from casare_rpa.nodes.text_nodes import TextExtractNode

        node = TextExtractNode(node_id="test_extract")
        node.set_input_value("text", "Email: test@example.com")
        node.set_input_value("pattern", r"[\w.-]+@[\w.-]+")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("found") is True
        assert node.get_output_value("match") == "test@example.com"
        assert node.get_output_value("match_count") == 1

    @pytest.mark.asyncio
    async def test_extract_all_matches(self, execution_context) -> None:
        """Test extracting all regex matches."""
        from casare_rpa.nodes.text_nodes import TextExtractNode

        node = TextExtractNode(node_id="test_extract_all", config={"all_matches": True})
        node.set_input_value("text", "a1 b2 c3 d4")
        node.set_input_value("pattern", r"\w\d")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("found") is True
        assert node.get_output_value("match") == ["a1", "b2", "c3", "d4"]
        assert node.get_output_value("match_count") == 4

    @pytest.mark.asyncio
    async def test_extract_with_groups(self, execution_context) -> None:
        """Test extracting regex with capture groups."""
        from casare_rpa.nodes.text_nodes import TextExtractNode

        node = TextExtractNode(node_id="test_extract_groups")
        node.set_input_value("text", "Name: John, Age: 30")
        node.set_input_value("pattern", r"Name: (\w+), Age: (\d+)")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("found") is True
        assert node.get_output_value("groups") == ["John", "30"]

    @pytest.mark.asyncio
    async def test_extract_no_match(self, execution_context) -> None:
        """Test when pattern does not match."""
        from casare_rpa.nodes.text_nodes import TextExtractNode

        node = TextExtractNode(node_id="test_extract_none")
        node.set_input_value("text", "no numbers here")
        node.set_input_value("pattern", r"\d+")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("found") is False
        assert node.get_output_value("match_count") == 0


class TestTextSubstringNode:
    """Tests for TextSubstringNode."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_substring_start_end(self, execution_context) -> None:
        """Test substring with start and end indices."""
        from casare_rpa.nodes.text_nodes import TextSubstringNode

        node = TextSubstringNode(node_id="test_substr")
        node.set_input_value("text", "Hello World")
        node.set_input_value("start", 0)
        node.set_input_value("end", 5)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "Hello"
        assert node.get_output_value("length") == 5

    @pytest.mark.asyncio
    async def test_substring_start_only(self, execution_context) -> None:
        """Test substring with start only."""
        from casare_rpa.nodes.text_nodes import TextSubstringNode

        node = TextSubstringNode(node_id="test_substr_start")
        node.set_input_value("text", "Hello World")
        node.set_input_value("start", 6)
        node.set_input_value("end", None)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "World"

    @pytest.mark.asyncio
    async def test_substring_negative_index(self, execution_context) -> None:
        """Test substring with negative index."""
        from casare_rpa.nodes.text_nodes import TextSubstringNode

        node = TextSubstringNode(node_id="test_substr_neg")
        node.set_input_value("text", "Hello World")
        node.set_input_value("start", -5)
        node.set_input_value("end", None)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "World"


class TestTextContainsNode:
    """Tests for TextContainsNode."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_contains_found(self, execution_context) -> None:
        """Test when substring is found."""
        from casare_rpa.nodes.text_nodes import TextContainsNode

        node = TextContainsNode(node_id="test_contains")
        node.set_input_value("text", "Hello World")
        node.set_input_value("search", "World")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("contains") is True
        assert node.get_output_value("position") == 6
        assert node.get_output_value("count") == 1

    @pytest.mark.asyncio
    async def test_contains_not_found(self, execution_context) -> None:
        """Test when substring is not found."""
        from casare_rpa.nodes.text_nodes import TextContainsNode

        node = TextContainsNode(node_id="test_contains_none")
        node.set_input_value("text", "Hello World")
        node.set_input_value("search", "Python")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("contains") is False
        assert node.get_output_value("position") == -1
        assert node.get_output_value("count") == 0

    @pytest.mark.asyncio
    async def test_contains_case_insensitive(self, execution_context) -> None:
        """Test case-insensitive search."""
        from casare_rpa.nodes.text_nodes import TextContainsNode

        node = TextContainsNode(
            node_id="test_contains_ci", config={"case_sensitive": False}
        )
        node.set_input_value("text", "Hello World")
        node.set_input_value("search", "WORLD")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("contains") is True

    @pytest.mark.asyncio
    async def test_contains_multiple(self, execution_context) -> None:
        """Test counting multiple occurrences."""
        from casare_rpa.nodes.text_nodes import TextContainsNode

        node = TextContainsNode(node_id="test_contains_multi")
        node.set_input_value("text", "aa bb aa cc aa")
        node.set_input_value("search", "aa")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("count") == 3


class TestTextStartsWithNode:
    """Tests for TextStartsWithNode."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_starts_with_true(self, execution_context) -> None:
        """Test when text starts with prefix."""
        from casare_rpa.nodes.text_nodes import TextStartsWithNode

        node = TextStartsWithNode(node_id="test_starts")
        node.set_input_value("text", "Hello World")
        node.set_input_value("prefix", "Hello")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") is True

    @pytest.mark.asyncio
    async def test_starts_with_false(self, execution_context) -> None:
        """Test when text does not start with prefix."""
        from casare_rpa.nodes.text_nodes import TextStartsWithNode

        node = TextStartsWithNode(node_id="test_starts_false")
        node.set_input_value("text", "Hello World")
        node.set_input_value("prefix", "World")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") is False

    @pytest.mark.asyncio
    async def test_starts_with_case_insensitive(self, execution_context) -> None:
        """Test case-insensitive prefix check."""
        from casare_rpa.nodes.text_nodes import TextStartsWithNode

        node = TextStartsWithNode(
            node_id="test_starts_ci", config={"case_sensitive": False}
        )
        node.set_input_value("text", "Hello World")
        node.set_input_value("prefix", "HELLO")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") is True


class TestTextEndsWithNode:
    """Tests for TextEndsWithNode."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_ends_with_true(self, execution_context) -> None:
        """Test when text ends with suffix."""
        from casare_rpa.nodes.text_nodes import TextEndsWithNode

        node = TextEndsWithNode(node_id="test_ends")
        node.set_input_value("text", "Hello World")
        node.set_input_value("suffix", "World")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") is True

    @pytest.mark.asyncio
    async def test_ends_with_false(self, execution_context) -> None:
        """Test when text does not end with suffix."""
        from casare_rpa.nodes.text_nodes import TextEndsWithNode

        node = TextEndsWithNode(node_id="test_ends_false")
        node.set_input_value("text", "Hello World")
        node.set_input_value("suffix", "Hello")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") is False

    @pytest.mark.asyncio
    async def test_ends_with_case_insensitive(self, execution_context) -> None:
        """Test case-insensitive suffix check."""
        from casare_rpa.nodes.text_nodes import TextEndsWithNode

        node = TextEndsWithNode(
            node_id="test_ends_ci", config={"case_sensitive": False}
        )
        node.set_input_value("text", "Hello World")
        node.set_input_value("suffix", "WORLD")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") is True


class TestTextLinesNode:
    """Tests for TextLinesNode."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_lines_split(self, execution_context) -> None:
        """Test splitting text into lines."""
        from casare_rpa.nodes.text_nodes import TextLinesNode

        node = TextLinesNode(node_id="test_lines_split")
        node.set_input_value("input", "line1\nline2\nline3")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == ["line1", "line2", "line3"]
        assert node.get_output_value("count") == 3

    @pytest.mark.asyncio
    async def test_lines_join(self, execution_context) -> None:
        """Test joining lines into text."""
        from casare_rpa.nodes.text_nodes import TextLinesNode

        node = TextLinesNode(node_id="test_lines_join", config={"mode": "join"})
        node.set_input_value("input", ["line1", "line2", "line3"])

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "line1\nline2\nline3"

    @pytest.mark.asyncio
    async def test_lines_split_keep_ends(self, execution_context) -> None:
        """Test splitting lines keeping line endings."""
        from casare_rpa.nodes.text_nodes import TextLinesNode

        node = TextLinesNode(node_id="test_lines_keep", config={"keep_ends": True})
        node.set_input_value("input", "a\nb\n")

        result = await node.execute(execution_context)

        assert result["success"] is True
        lines = node.get_output_value("result")
        assert lines[0] == "a\n"
        assert lines[1] == "b\n"


class TestTextReverseNode:
    """Tests for TextReverseNode."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_reverse_text(self, execution_context) -> None:
        """Test reversing text."""
        from casare_rpa.nodes.text_nodes import TextReverseNode

        node = TextReverseNode(node_id="test_reverse")
        node.set_input_value("text", "Hello")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "olleH"

    @pytest.mark.asyncio
    async def test_reverse_empty(self, execution_context) -> None:
        """Test reversing empty string."""
        from casare_rpa.nodes.text_nodes import TextReverseNode

        node = TextReverseNode(node_id="test_reverse_empty")
        node.set_input_value("text", "")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == ""

    @pytest.mark.asyncio
    async def test_reverse_palindrome(self, execution_context) -> None:
        """Test reversing palindrome."""
        from casare_rpa.nodes.text_nodes import TextReverseNode

        node = TextReverseNode(node_id="test_reverse_pal")
        node.set_input_value("text", "radar")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "radar"


class TestTextCountNode:
    """Tests for TextCountNode."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_count_characters(self, execution_context) -> None:
        """Test counting characters."""
        from casare_rpa.nodes.text_nodes import TextCountNode

        node = TextCountNode(node_id="test_count_chars", config={"mode": "characters"})
        node.set_input_value("text", "Hello World")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("characters") == 11
        assert node.get_output_value("count") == 11

    @pytest.mark.asyncio
    async def test_count_words(self, execution_context) -> None:
        """Test counting words."""
        from casare_rpa.nodes.text_nodes import TextCountNode

        node = TextCountNode(node_id="test_count_words", config={"mode": "words"})
        node.set_input_value("text", "Hello World Test")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("words") == 3
        assert node.get_output_value("count") == 3

    @pytest.mark.asyncio
    async def test_count_lines(self, execution_context) -> None:
        """Test counting lines."""
        from casare_rpa.nodes.text_nodes import TextCountNode

        node = TextCountNode(node_id="test_count_lines", config={"mode": "lines"})
        node.set_input_value("text", "line1\nline2\nline3")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("lines") == 3
        assert node.get_output_value("count") == 3

    @pytest.mark.asyncio
    async def test_count_exclude_whitespace(self, execution_context) -> None:
        """Test counting characters excluding whitespace."""
        from casare_rpa.nodes.text_nodes import TextCountNode

        node = TextCountNode(
            node_id="test_count_no_ws",
            config={"mode": "characters", "exclude_whitespace": True},
        )
        node.set_input_value("text", "Hello World")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("characters") == 10  # No space


class TestTextPadNode:
    """Tests for TextPadNode."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_pad_left(self, execution_context) -> None:
        """Test left padding (right-justify)."""
        from casare_rpa.nodes.text_nodes import TextPadNode

        node = TextPadNode(
            node_id="test_pad_left", config={"mode": "left", "fill_char": "0"}
        )
        node.set_input_value("text", "42")
        node.set_input_value("length", 5)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "00042"

    @pytest.mark.asyncio
    async def test_pad_right(self, execution_context) -> None:
        """Test right padding (left-justify)."""
        from casare_rpa.nodes.text_nodes import TextPadNode

        node = TextPadNode(
            node_id="test_pad_right", config={"mode": "right", "fill_char": "-"}
        )
        node.set_input_value("text", "hi")
        node.set_input_value("length", 5)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "hi---"

    @pytest.mark.asyncio
    async def test_pad_center(self, execution_context) -> None:
        """Test center padding."""
        from casare_rpa.nodes.text_nodes import TextPadNode

        node = TextPadNode(
            node_id="test_pad_center", config={"mode": "center", "fill_char": "*"}
        )
        node.set_input_value("text", "hi")
        node.set_input_value("length", 6)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "**hi**"


class TestTextEdgeCases:
    """Edge case tests for text nodes."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_empty_string_handling(self, execution_context) -> None:
        """Test various nodes handle empty strings."""
        from casare_rpa.nodes.text_nodes import (
            TextSplitNode,
            TextTrimNode,
            TextCaseNode,
            TextReverseNode,
        )

        # Split empty
        node1 = TextSplitNode(node_id="test_empty1")
        node1.set_input_value("text", "")
        result1 = await node1.execute(execution_context)
        assert result1["success"] is True

        # Trim empty
        node2 = TextTrimNode(node_id="test_empty2")
        node2.set_input_value("text", "")
        result2 = await node2.execute(execution_context)
        assert result2["success"] is True

        # Case empty
        node3 = TextCaseNode(node_id="test_empty3", config={"case": "upper"})
        node3.set_input_value("text", "")
        result3 = await node3.execute(execution_context)
        assert result3["success"] is True

        # Reverse empty
        node4 = TextReverseNode(node_id="test_empty4")
        node4.set_input_value("text", "")
        result4 = await node4.execute(execution_context)
        assert result4["success"] is True

    @pytest.mark.asyncio
    async def test_unicode_handling(self, execution_context) -> None:
        """Test text nodes handle unicode properly."""
        from casare_rpa.nodes.text_nodes import (
            TextReverseNode,
            TextCaseNode,
            TextCountNode,
        )

        # Reverse unicode
        node1 = TextReverseNode(node_id="test_unicode1")
        node1.set_input_value("text", "cafe")
        result1 = await node1.execute(execution_context)
        assert result1["success"] is True
        assert node1.get_output_value("result") == "efac"

        # Case unicode
        node2 = TextCaseNode(node_id="test_unicode2", config={"case": "upper"})
        node2.set_input_value("text", "cafe")
        result2 = await node2.execute(execution_context)
        assert result2["success"] is True
        assert node2.get_output_value("result") == "CAFE"

        # Count unicode
        node3 = TextCountNode(node_id="test_unicode3", config={"mode": "characters"})
        node3.set_input_value("text", "cafe")
        result3 = await node3.execute(execution_context)
        assert result3["success"] is True
        assert node3.get_output_value("characters") == 4

    @pytest.mark.asyncio
    async def test_execution_result_pattern(self, execution_context) -> None:
        """Test all text nodes follow ExecutionResult pattern."""
        from casare_rpa.nodes.text_nodes import TextSplitNode

        node = TextSplitNode(node_id="test_pattern")
        node.set_input_value("text", "a,b,c")
        node.set_input_value("separator", ",")

        result = await node.execute(execution_context)

        # Verify ExecutionResult structure
        assert "success" in result
        assert "data" in result
        assert "next_nodes" in result
        assert result["success"] is True
        assert "exec_out" in result["next_nodes"]
