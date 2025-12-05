"""
CasareRPA - E2E Tests for String Manipulation Workflows.

Tests string operations including:
- Concatenation
- String formatting
- Case transformations
- Trim operations
- Split and join
- Replace operations
- Regex matching and extraction
- Substring operations
"""

import pytest

from .helpers.workflow_builder import WorkflowBuilder


@pytest.mark.asyncio
@pytest.mark.e2e
class TestConcatenation:
    """Tests for string concatenation operations."""

    async def test_concat_two_strings(self) -> None:
        """Test concatenating two simple strings."""
        result = await (
            WorkflowBuilder("Concat Two Strings")
            .add_start()
            .add_set_variable("a", "Hello")
            .add_set_variable("b", "World")
            .add_concat("result", "{{a}}", "{{b}}")
            .add_end()
            .execute()
        )

        assert result["success"] is True
        assert result["variables"].get("a") == "Hello"
        assert result["variables"].get("b") == "World"

    async def test_concat_with_separator(self) -> None:
        """Test concatenating strings with a separator."""
        result = await (
            WorkflowBuilder("Concat With Separator")
            .add_start()
            .add_set_variable("first", "Hello")
            .add_set_variable("second", "World")
            .add_concat("result", "{{first}}", "{{second}}", separator=" ")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_concat_empty_strings(self) -> None:
        """Test concatenating empty strings."""
        result = await (
            WorkflowBuilder("Concat Empty")
            .add_start()
            .add_set_variable("a", "")
            .add_set_variable("b", "test")
            .add_concat("result", "{{a}}", "{{b}}")
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestFormatString:
    """Tests for string formatting operations."""

    async def test_format_string_with_variables(self) -> None:
        """Test formatting string with dictionary variables."""
        result = await (
            WorkflowBuilder("Format String")
            .add_start()
            .add_set_variable("format_vars", {"name": "John", "age": 30})
            .add_format_string(
                template="Hello, {name}! You are {age} years old.",
                variables="{{format_vars}}",
            )
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_format_string_with_dict_literal(self) -> None:
        """Test formatting string with inline dictionary."""
        result = await (
            WorkflowBuilder("Format With Dict")
            .add_start()
            .add_format_string(
                template="Item: {item}, Price: ${price}",
                variables={"item": "Widget", "price": "9.99"},
            )
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestCaseTransforms:
    """Tests for string case transformations."""

    async def test_string_to_uppercase(self) -> None:
        """Test converting string to uppercase."""
        result = await (
            WorkflowBuilder("Uppercase")
            .add_start()
            .add_set_variable("input", "hello world")
            .add_text_case("{{input}}", case="upper")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_string_to_lowercase(self) -> None:
        """Test converting string to lowercase."""
        result = await (
            WorkflowBuilder("Lowercase")
            .add_start()
            .add_set_variable("input", "HELLO WORLD")
            .add_text_case("{{input}}", case="lower")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_string_to_title_case(self) -> None:
        """Test converting string to title case."""
        result = await (
            WorkflowBuilder("Title Case")
            .add_start()
            .add_set_variable("input", "hello world example")
            .add_text_case("{{input}}", case="title")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_string_capitalize(self) -> None:
        """Test capitalizing first character."""
        result = await (
            WorkflowBuilder("Capitalize")
            .add_start()
            .add_set_variable("input", "hello world")
            .add_text_case("{{input}}", case="capitalize")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_string_swapcase(self) -> None:
        """Test swapping case of characters."""
        result = await (
            WorkflowBuilder("Swapcase")
            .add_start()
            .add_set_variable("input", "Hello World")
            .add_text_case("{{input}}", case="swapcase")
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestTrimOperations:
    """Tests for string trim operations."""

    async def test_string_trim_both(self) -> None:
        """Test trimming whitespace from both sides."""
        result = await (
            WorkflowBuilder("Trim Both")
            .add_start()
            .add_set_variable("input", "  hello  ")
            .add_text_trim("{{input}}", mode="both")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_string_trim_left(self) -> None:
        """Test trimming whitespace from left side."""
        result = await (
            WorkflowBuilder("Trim Left")
            .add_start()
            .add_set_variable("input", "  hello  ")
            .add_text_trim("{{input}}", mode="left")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_string_trim_right(self) -> None:
        """Test trimming whitespace from right side."""
        result = await (
            WorkflowBuilder("Trim Right")
            .add_start()
            .add_set_variable("input", "  hello  ")
            .add_text_trim("{{input}}", mode="right")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_string_trim_custom_characters(self) -> None:
        """Test trimming custom characters."""
        result = await (
            WorkflowBuilder("Trim Custom")
            .add_start()
            .add_set_variable("input", "###hello###")
            .add_text_trim("{{input}}", mode="both", characters="#")
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestSplitJoin:
    """Tests for string split and join operations."""

    async def test_string_split(self) -> None:
        """Test splitting string by separator."""
        result = await (
            WorkflowBuilder("Split String")
            .add_start()
            .add_set_variable("input", "a,b,c")
            .add_text_split("{{input}}", separator=",")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_string_split_whitespace(self) -> None:
        """Test splitting string by whitespace."""
        result = await (
            WorkflowBuilder("Split Whitespace")
            .add_start()
            .add_set_variable("input", "one two three")
            .add_text_split("{{input}}")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_string_split_max(self) -> None:
        """Test splitting string with max splits."""
        result = await (
            WorkflowBuilder("Split Max")
            .add_start()
            .add_set_variable("input", "a,b,c,d,e")
            .add_text_split("{{input}}", separator=",", max_split=2)
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_string_join(self) -> None:
        """Test joining list into string."""
        result = await (
            WorkflowBuilder("Join String")
            .add_start()
            .add_set_variable("items", ["a", "b", "c"])
            .add_text_join("{{items}}", separator="-")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_list_join_node(self) -> None:
        """Test ListJoinNode for joining lists."""
        result = await (
            WorkflowBuilder("List Join")
            .add_start()
            .add_set_variable("items", ["apple", "banana", "cherry"])
            .add_list_join("{{items}}", separator=", ")
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestReplaceOperations:
    """Tests for string replace operations."""

    async def test_string_replace(self) -> None:
        """Test basic string replacement."""
        result = await (
            WorkflowBuilder("Replace String")
            .add_start()
            .add_set_variable("input", "hello world")
            .add_text_replace("{{input}}", old_value="world", new_value="there")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_string_replace_multiple(self) -> None:
        """Test replacing multiple occurrences."""
        result = await (
            WorkflowBuilder("Replace Multiple")
            .add_start()
            .add_set_variable("input", "cat cat cat")
            .add_text_replace("{{input}}", old_value="cat", new_value="dog")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_string_replace_limited(self) -> None:
        """Test replacing with count limit."""
        result = await (
            WorkflowBuilder("Replace Limited")
            .add_start()
            .add_set_variable("input", "aaa")
            .add_text_replace("{{input}}", old_value="a", new_value="b", count=2)
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_string_replace_case_insensitive(self) -> None:
        """Test case-insensitive replacement."""
        result = await (
            WorkflowBuilder("Replace Case Insensitive")
            .add_start()
            .add_set_variable("input", "Hello HELLO hello")
            .add_text_replace(
                "{{input}}",
                old_value="hello",
                new_value="hi",
                use_regex=True,
                ignore_case=True,
            )
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestSubstringOperations:
    """Tests for substring operations."""

    async def test_string_substring(self) -> None:
        """Test extracting substring."""
        result = await (
            WorkflowBuilder("Substring")
            .add_start()
            .add_set_variable("input", "hello world")
            .add_text_substring("{{input}}", start=0, end=5)
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_string_substring_from_end(self) -> None:
        """Test extracting substring from specific position to end."""
        result = await (
            WorkflowBuilder("Substring To End")
            .add_start()
            .add_set_variable("input", "hello world")
            .add_text_substring("{{input}}", start=6)
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_string_length(self) -> None:
        """Test getting string length."""
        result = await (
            WorkflowBuilder("String Length")
            .add_start()
            .add_set_variable("input", "hello")
            .add_text_count("{{input}}", mode="characters")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_string_word_count(self) -> None:
        """Test counting words in string."""
        result = await (
            WorkflowBuilder("Word Count")
            .add_start()
            .add_set_variable("input", "one two three four five")
            .add_text_count("{{input}}", mode="words")
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestRegexOperations:
    """Tests for regex matching and extraction."""

    async def test_regex_match_found(self) -> None:
        """Test regex matching when pattern is found."""
        result = await (
            WorkflowBuilder("Regex Match Found")
            .add_start()
            .add_set_variable("input", "email@test.com")
            .add_regex_match("{{input}}", pattern=r"[a-z]+@[a-z]+\.[a-z]+")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_regex_match_not_found(self) -> None:
        """Test regex matching when pattern is not found."""
        result = await (
            WorkflowBuilder("Regex Match Not Found")
            .add_start()
            .add_set_variable("input", "invalid")
            .add_regex_match("{{input}}", pattern=r"[a-z]+@[a-z]+\.[a-z]+")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_regex_extract_groups(self) -> None:
        """Test regex extraction with capture groups."""
        result = await (
            WorkflowBuilder("Regex Extract")
            .add_start()
            .add_set_variable("input", "John is 30 years old")
            .add_text_extract("{{input}}", pattern=r"(\w+) is (\d+)")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_regex_match_case_insensitive(self) -> None:
        """Test case-insensitive regex matching."""
        result = await (
            WorkflowBuilder("Regex Case Insensitive")
            .add_start()
            .add_set_variable("input", "HELLO world")
            .add_regex_match("{{input}}", pattern=r"hello", ignore_case=True)
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_regex_extract_all_matches(self) -> None:
        """Test extracting all regex matches."""
        result = await (
            WorkflowBuilder("Regex All Matches")
            .add_start()
            .add_set_variable("input", "cat dog cat bird cat")
            .add_text_extract("{{input}}", pattern=r"cat", all_matches=True)
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestContainsOperations:
    """Tests for string contains operations."""

    async def test_text_contains(self) -> None:
        """Test checking if text contains substring."""
        result = await (
            WorkflowBuilder("Text Contains")
            .add_start()
            .add_set_variable("input", "hello world")
            .add_text_contains("{{input}}", search="world")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_text_contains_not_found(self) -> None:
        """Test checking if text contains substring (not found)."""
        result = await (
            WorkflowBuilder("Text Not Contains")
            .add_start()
            .add_set_variable("input", "hello world")
            .add_text_contains("{{input}}", search="xyz")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_text_contains_case_insensitive(self) -> None:
        """Test case-insensitive contains check."""
        result = await (
            WorkflowBuilder("Text Contains Case Insensitive")
            .add_start()
            .add_set_variable("input", "Hello World")
            .add_text_contains("{{input}}", search="hello", case_sensitive=False)
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestStringPipeline:
    """Tests for chained string operations."""

    async def test_string_pipeline(self) -> None:
        """Test pipeline: trim -> lowercase -> replace -> split."""
        result = await (
            WorkflowBuilder("String Pipeline")
            .add_start()
            .add_set_variable("input", "  Hello World Example  ")
            .add_text_trim("{{input}}")
            .add_text_case("{{input}}", case="lower")
            .add_text_replace("{{input}}", old_value="world", new_value="there")
            .add_text_split("{{input}}", separator=" ")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_format_and_concat(self) -> None:
        """Test combining format string and concatenation."""
        result = await (
            WorkflowBuilder("Format and Concat")
            .add_start()
            .add_set_variable("user", {"first": "John", "last": "Doe"})
            .add_format_string("Name: {first} {last}", "{{user}}")
            .add_set_variable("greeting", "Hello!")
            .add_concat("final", "{{greeting}}", " Your name is recorded.")
            .add_end()
            .execute()
        )

        assert result["success"] is True
