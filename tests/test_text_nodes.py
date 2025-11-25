"""
Tests for Text operation nodes.

Tests text splitting, replacing, trimming, case conversion, and other text operations.
"""

import pytest

from casare_rpa.nodes.text_nodes import (
    TextSplitNode,
    TextReplaceNode,
    TextTrimNode,
    TextCaseNode,
    TextPadNode,
    TextSubstringNode,
    TextContainsNode,
    TextStartsWithNode,
    TextEndsWithNode,
    TextLinesNode,
    TextReverseNode,
    TextCountNode,
    TextJoinNode,
    TextExtractNode,
)
from casare_rpa.core.types import NodeStatus


class TestTextSplitNode:
    """Tests for TextSplit node."""

    @pytest.mark.asyncio
    async def test_split_basic(self, execution_context):
        """Test basic string splitting."""
        node = TextSplitNode(node_id="split_1")
        node.set_input_value("text", "a,b,c,d")
        node.set_input_value("separator", ",")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == ["a", "b", "c", "d"]
        assert node.get_output_value("count") == 4

    @pytest.mark.asyncio
    async def test_split_with_max(self, execution_context):
        """Test splitting with max splits."""
        node = TextSplitNode(
            node_id="split_1",
            config={"max_split": 2}
        )
        node.set_input_value("text", "a,b,c,d")
        node.set_input_value("separator", ",")

        result = await node.execute(execution_context)

        assert result["success"] is True
        parts = node.get_output_value("result")
        assert len(parts) == 3  # max_split + 1

    @pytest.mark.asyncio
    async def test_split_whitespace(self, execution_context):
        """Test splitting on whitespace."""
        node = TextSplitNode(node_id="split_1")
        node.set_input_value("text", "hello world foo bar")
        node.set_input_value("separator", " ")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == ["hello", "world", "foo", "bar"]

    @pytest.mark.asyncio
    async def test_split_no_separator_found(self, execution_context):
        """Test splitting when separator not in text."""
        node = TextSplitNode(node_id="split_1")
        node.set_input_value("text", "hello")
        node.set_input_value("separator", ",")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == ["hello"]
        assert node.get_output_value("count") == 1


class TestTextReplaceNode:
    """Tests for TextReplace node."""

    @pytest.mark.asyncio
    async def test_replace_basic(self, execution_context):
        """Test basic text replacement."""
        node = TextReplaceNode(node_id="replace_1")
        node.set_input_value("text", "hello world")
        node.set_input_value("old_value", "world")
        node.set_input_value("new_value", "universe")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "hello universe"

    @pytest.mark.asyncio
    async def test_replace_multiple(self, execution_context):
        """Test replacing multiple occurrences."""
        node = TextReplaceNode(node_id="replace_1")
        node.set_input_value("text", "a-b-c-d")
        node.set_input_value("old_value", "-")
        node.set_input_value("new_value", "_")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "a_b_c_d"

    @pytest.mark.asyncio
    async def test_replace_with_regex(self, execution_context):
        """Test regex replacement."""
        node = TextReplaceNode(
            node_id="replace_1",
            config={"use_regex": True}
        )
        node.set_input_value("text", "Hello123World456")
        node.set_input_value("old_value", r"\d+")
        node.set_input_value("new_value", "-")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "Hello-World-"

    @pytest.mark.asyncio
    async def test_replace_with_empty(self, execution_context):
        """Test replacing with empty string (deletion)."""
        node = TextReplaceNode(node_id="replace_1")
        node.set_input_value("text", "hello world")
        node.set_input_value("old_value", " world")
        node.set_input_value("new_value", "")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "hello"


class TestTextTrimNode:
    """Tests for TextTrim node."""

    @pytest.mark.asyncio
    async def test_trim_both(self, execution_context):
        """Test trimming both ends."""
        node = TextTrimNode(node_id="trim_1")
        node.set_input_value("text", "  hello world  ")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "hello world"

    @pytest.mark.asyncio
    async def test_trim_left_only(self, execution_context):
        """Test trimming left side only."""
        node = TextTrimNode(
            node_id="trim_1",
            config={"mode": "left"}
        )
        node.set_input_value("text", "  hello  ")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "hello  "

    @pytest.mark.asyncio
    async def test_trim_right_only(self, execution_context):
        """Test trimming right side only."""
        node = TextTrimNode(
            node_id="trim_1",
            config={"mode": "right"}
        )
        node.set_input_value("text", "  hello  ")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "  hello"

    @pytest.mark.asyncio
    async def test_trim_custom_chars(self, execution_context):
        """Test trimming custom characters."""
        node = TextTrimNode(
            node_id="trim_1",
            config={"characters": "-_"}
        )
        node.set_input_value("text", "---hello___")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "hello"


class TestTextCaseNode:
    """Tests for TextCase node."""

    @pytest.mark.asyncio
    async def test_case_upper(self, execution_context):
        """Test converting to uppercase."""
        node = TextCaseNode(
            node_id="case_1",
            config={"case": "upper"}
        )
        node.set_input_value("text", "hello World")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "HELLO WORLD"

    @pytest.mark.asyncio
    async def test_case_lower(self, execution_context):
        """Test converting to lowercase."""
        node = TextCaseNode(
            node_id="case_1",
            config={"case": "lower"}
        )
        node.set_input_value("text", "HELLO World")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "hello world"

    @pytest.mark.asyncio
    async def test_case_title(self, execution_context):
        """Test converting to title case."""
        node = TextCaseNode(
            node_id="case_1",
            config={"case": "title"}
        )
        node.set_input_value("text", "hello world")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "Hello World"

    @pytest.mark.asyncio
    async def test_case_capitalize(self, execution_context):
        """Test capitalizing first letter."""
        node = TextCaseNode(
            node_id="case_1",
            config={"case": "capitalize"}
        )
        node.set_input_value("text", "hello world")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "Hello world"

    @pytest.mark.asyncio
    async def test_case_swap(self, execution_context):
        """Test swapping case."""
        node = TextCaseNode(
            node_id="case_1",
            config={"case": "swapcase"}
        )
        node.set_input_value("text", "Hello World")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "hELLO wORLD"


class TestTextPadNode:
    """Tests for TextPad node."""

    @pytest.mark.asyncio
    async def test_pad_left(self, execution_context):
        """Test left padding."""
        node = TextPadNode(
            node_id="pad_1",
            config={"mode": "left", "fill_char": "0"}
        )
        node.set_input_value("text", "42")
        node.set_input_value("length", 5)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "00042"

    @pytest.mark.asyncio
    async def test_pad_right(self, execution_context):
        """Test right padding."""
        node = TextPadNode(
            node_id="pad_1",
            config={"mode": "right", "fill_char": "-"}
        )
        node.set_input_value("text", "hello")
        node.set_input_value("length", 10)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "hello-----"

    @pytest.mark.asyncio
    async def test_pad_center(self, execution_context):
        """Test center padding."""
        node = TextPadNode(
            node_id="pad_1",
            config={"mode": "center", "fill_char": "*"}
        )
        node.set_input_value("text", "hi")
        node.set_input_value("length", 6)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "**hi**"


class TestTextSubstringNode:
    """Tests for TextSubstring node."""

    @pytest.mark.asyncio
    async def test_substring_basic(self, execution_context):
        """Test basic substring extraction."""
        node = TextSubstringNode(node_id="sub_1")
        node.set_input_value("text", "hello world")
        node.set_input_value("start", 0)
        node.set_input_value("end", 5)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "hello"

    @pytest.mark.asyncio
    async def test_substring_negative_index(self, execution_context):
        """Test substring with negative index."""
        node = TextSubstringNode(node_id="sub_1")
        node.set_input_value("text", "hello world")
        node.set_input_value("start", -5)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "world"

    @pytest.mark.asyncio
    async def test_substring_no_end(self, execution_context):
        """Test substring without end index."""
        node = TextSubstringNode(node_id="sub_1")
        node.set_input_value("text", "hello world")
        node.set_input_value("start", 6)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "world"


class TestTextContainsNode:
    """Tests for TextContains node."""

    @pytest.mark.asyncio
    async def test_contains_true(self, execution_context):
        """Test text contains substring."""
        node = TextContainsNode(node_id="contains_1")
        node.set_input_value("text", "hello world")
        node.set_input_value("search", "world")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("contains") is True
        assert node.get_output_value("position") == 6

    @pytest.mark.asyncio
    async def test_contains_false(self, execution_context):
        """Test text doesn't contain substring."""
        node = TextContainsNode(node_id="contains_1")
        node.set_input_value("text", "hello world")
        node.set_input_value("search", "foo")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("contains") is False
        assert node.get_output_value("position") == -1

    @pytest.mark.asyncio
    async def test_contains_case_insensitive(self, execution_context):
        """Test case-insensitive contains."""
        node = TextContainsNode(
            node_id="contains_1",
            config={"case_sensitive": False}
        )
        node.set_input_value("text", "Hello World")
        node.set_input_value("search", "WORLD")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("contains") is True


class TestTextStartsWithNode:
    """Tests for TextStartsWith node."""

    @pytest.mark.asyncio
    async def test_starts_with_true(self, execution_context):
        """Test text starts with prefix."""
        node = TextStartsWithNode(node_id="starts_1")
        node.set_input_value("text", "hello world")
        node.set_input_value("prefix", "hello")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") is True

    @pytest.mark.asyncio
    async def test_starts_with_false(self, execution_context):
        """Test text doesn't start with prefix."""
        node = TextStartsWithNode(node_id="starts_1")
        node.set_input_value("text", "hello world")
        node.set_input_value("prefix", "world")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") is False


class TestTextEndsWithNode:
    """Tests for TextEndsWith node."""

    @pytest.mark.asyncio
    async def test_ends_with_true(self, execution_context):
        """Test text ends with suffix."""
        node = TextEndsWithNode(node_id="ends_1")
        node.set_input_value("text", "hello world")
        node.set_input_value("suffix", "world")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") is True

    @pytest.mark.asyncio
    async def test_ends_with_false(self, execution_context):
        """Test text doesn't end with suffix."""
        node = TextEndsWithNode(node_id="ends_1")
        node.set_input_value("text", "hello world")
        node.set_input_value("suffix", "hello")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") is False


class TestTextLinesNode:
    """Tests for TextLines node."""

    @pytest.mark.asyncio
    async def test_lines_basic(self, execution_context):
        """Test splitting text into lines."""
        node = TextLinesNode(node_id="lines_1")
        node.set_input_value("input", "line1\nline2\nline3")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == ["line1", "line2", "line3"]
        assert node.get_output_value("count") == 3

    @pytest.mark.asyncio
    async def test_lines_join(self, execution_context):
        """Test joining lines."""
        node = TextLinesNode(
            node_id="lines_1",
            config={"mode": "join"}
        )
        node.set_input_value("input", ["line1", "line2", "line3"])

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "line1\nline2\nline3"


class TestTextReverseNode:
    """Tests for TextReverse node."""

    @pytest.mark.asyncio
    async def test_reverse_basic(self, execution_context):
        """Test reversing text."""
        node = TextReverseNode(node_id="rev_1")
        node.set_input_value("text", "hello")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "olleh"

    @pytest.mark.asyncio
    async def test_reverse_palindrome(self, execution_context):
        """Test reversing palindrome."""
        node = TextReverseNode(node_id="rev_1")
        node.set_input_value("text", "radar")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "radar"


class TestTextCountNode:
    """Tests for TextCount node."""

    @pytest.mark.asyncio
    async def test_count_characters(self, execution_context):
        """Test counting characters."""
        node = TextCountNode(
            node_id="count_1",
            config={"mode": "characters"}
        )
        node.set_input_value("text", "hello world")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("count") == 11

    @pytest.mark.asyncio
    async def test_count_words(self, execution_context):
        """Test counting words."""
        node = TextCountNode(
            node_id="count_1",
            config={"mode": "words"}
        )
        node.set_input_value("text", "hello world foo")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("count") == 3


class TestTextJoinNode:
    """Tests for TextJoin node."""

    @pytest.mark.asyncio
    async def test_join_basic(self, execution_context):
        """Test joining strings."""
        node = TextJoinNode(node_id="join_1")
        node.set_input_value("items", ["a", "b", "c"])
        node.set_input_value("separator", ", ")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "a, b, c"

    @pytest.mark.asyncio
    async def test_join_no_separator(self, execution_context):
        """Test joining without separator."""
        node = TextJoinNode(node_id="join_1")
        node.set_input_value("items", ["a", "b", "c"])
        node.set_input_value("separator", "")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "abc"

    @pytest.mark.asyncio
    async def test_join_newline(self, execution_context):
        """Test joining with newline."""
        node = TextJoinNode(node_id="join_1")
        node.set_input_value("items", ["line1", "line2", "line3"])
        node.set_input_value("separator", "\n")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "line1\nline2\nline3"


class TestTextExtractNode:
    """Tests for TextExtract node."""

    @pytest.mark.asyncio
    async def test_extract_regex(self, execution_context):
        """Test extracting with regex."""
        node = TextExtractNode(node_id="extract_1")
        node.set_input_value("text", "Email: test@example.com")
        node.set_input_value("pattern", r"\w+@\w+\.\w+")

        result = await node.execute(execution_context)

        assert result["success"] is True
        match = node.get_output_value("match")
        assert match == "test@example.com"
        assert node.get_output_value("found") is True

    @pytest.mark.asyncio
    async def test_extract_multiple(self, execution_context):
        """Test extracting multiple matches."""
        node = TextExtractNode(
            node_id="extract_1",
            config={"all_matches": True}
        )
        node.set_input_value("text", "ID: 123, Code: 456, Ref: 789")
        node.set_input_value("pattern", r"\d+")

        result = await node.execute(execution_context)

        assert result["success"] is True
        matches = node.get_output_value("match")
        assert len(matches) == 3
        assert "123" in matches

    @pytest.mark.asyncio
    async def test_extract_no_match(self, execution_context):
        """Test extracting with no matches."""
        node = TextExtractNode(node_id="extract_1")
        node.set_input_value("text", "hello world")
        node.set_input_value("pattern", r"\d+")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("found") is False
        assert node.get_output_value("match") == ""
