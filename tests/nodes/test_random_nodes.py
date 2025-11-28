"""
Tests for Random generation nodes.

Tests 5 random nodes:
- RandomNumberNode, RandomChoiceNode, RandomStringNode
- RandomUUIDNode, ShuffleListNode
"""

import pytest
import re
import uuid
from unittest.mock import Mock

# Uses execution_context fixture from conftest.py - no import needed


class TestRandomNumberNode:
    """Tests for RandomNumberNode."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_random_number_default_range(self, execution_context) -> None:
        """Test random number in default range (0-100)."""
        from casare_rpa.nodes.random_nodes import RandomNumberNode

        node = RandomNumberNode(node_id="test_rand_default")

        result = await node.execute(execution_context)

        assert result["success"] is True
        num = node.get_output_value("result")
        assert 0 <= num <= 100

    @pytest.mark.asyncio
    async def test_random_number_custom_range(self, execution_context) -> None:
        """Test random number in custom range."""
        from casare_rpa.nodes.random_nodes import RandomNumberNode

        node = RandomNumberNode(node_id="test_rand_custom")
        node.set_input_value("min_value", 50)
        node.set_input_value("max_value", 60)

        result = await node.execute(execution_context)

        assert result["success"] is True
        num = node.get_output_value("result")
        assert 50 <= num <= 60

    @pytest.mark.asyncio
    async def test_random_number_integer_only(self, execution_context) -> None:
        """Test random integer generation."""
        from casare_rpa.nodes.random_nodes import RandomNumberNode

        node = RandomNumberNode(node_id="test_rand_int", config={"integer_only": True})
        node.set_input_value("min_value", 1)
        node.set_input_value("max_value", 10)

        result = await node.execute(execution_context)

        assert result["success"] is True
        num = node.get_output_value("result")
        assert isinstance(num, int)
        assert 1 <= num <= 10

    @pytest.mark.asyncio
    async def test_random_number_swapped_range(self, execution_context) -> None:
        """Test random number handles swapped min/max."""
        from casare_rpa.nodes.random_nodes import RandomNumberNode

        node = RandomNumberNode(node_id="test_rand_swap")
        node.set_input_value("min_value", 100)
        node.set_input_value("max_value", 50)

        result = await node.execute(execution_context)

        assert result["success"] is True
        num = node.get_output_value("result")
        assert 50 <= num <= 100

    @pytest.mark.asyncio
    async def test_random_number_distribution(self, execution_context) -> None:
        """Test random numbers have reasonable distribution."""
        from casare_rpa.nodes.random_nodes import RandomNumberNode

        numbers = []
        for i in range(100):
            node = RandomNumberNode(
                node_id=f"test_dist_{i}", config={"integer_only": True}
            )
            node.set_input_value("min_value", 1)
            node.set_input_value("max_value", 10)
            await node.execute(execution_context)
            numbers.append(node.get_output_value("result"))

        # All numbers should be in range
        assert all(1 <= n <= 10 for n in numbers)
        # Should have some variety (not all same number)
        assert len(set(numbers)) > 1


class TestRandomChoiceNode:
    """Tests for RandomChoiceNode."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_random_choice_single(self, execution_context) -> None:
        """Test selecting single random item."""
        from casare_rpa.nodes.random_nodes import RandomChoiceNode

        items = ["apple", "banana", "cherry", "date"]
        node = RandomChoiceNode(node_id="test_choice_single")
        node.set_input_value("items", items)

        result = await node.execute(execution_context)

        assert result["success"] is True
        chosen = node.get_output_value("result")
        assert chosen in items
        index = node.get_output_value("index")
        assert 0 <= index < len(items)

    @pytest.mark.asyncio
    async def test_random_choice_multiple_no_duplicates(
        self, execution_context
    ) -> None:
        """Test selecting multiple items without duplicates."""
        from casare_rpa.nodes.random_nodes import RandomChoiceNode

        items = ["a", "b", "c", "d", "e"]
        node = RandomChoiceNode(
            node_id="test_choice_multi", config={"count": 3, "allow_duplicates": False}
        )
        node.set_input_value("items", items)

        result = await node.execute(execution_context)

        assert result["success"] is True
        chosen = node.get_output_value("result")
        assert len(chosen) == 3
        assert len(set(chosen)) == 3  # No duplicates
        assert all(item in items for item in chosen)

    @pytest.mark.asyncio
    async def test_random_choice_multiple_with_duplicates(
        self, execution_context
    ) -> None:
        """Test selecting multiple items with duplicates allowed."""
        from casare_rpa.nodes.random_nodes import RandomChoiceNode

        items = ["a", "b"]
        node = RandomChoiceNode(
            node_id="test_choice_dup", config={"count": 5, "allow_duplicates": True}
        )
        node.set_input_value("items", items)

        result = await node.execute(execution_context)

        assert result["success"] is True
        chosen = node.get_output_value("result")
        assert len(chosen) == 5
        assert all(item in items for item in chosen)

    @pytest.mark.asyncio
    async def test_random_choice_count_exceeds_items(self, execution_context) -> None:
        """Test when count exceeds available items (no duplicates)."""
        from casare_rpa.nodes.random_nodes import RandomChoiceNode

        items = ["a", "b", "c"]
        node = RandomChoiceNode(
            node_id="test_choice_exceed",
            config={"count": 10, "allow_duplicates": False},
        )
        node.set_input_value("items", items)

        result = await node.execute(execution_context)

        assert result["success"] is True
        chosen = node.get_output_value("result")
        # Should cap at available items
        assert len(chosen) <= len(items)

    @pytest.mark.asyncio
    async def test_random_choice_empty_list(self, execution_context) -> None:
        """Test random choice with empty list fails."""
        from casare_rpa.nodes.random_nodes import RandomChoiceNode

        node = RandomChoiceNode(node_id="test_choice_empty")
        node.set_input_value("items", [])

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "error" in result


class TestRandomStringNode:
    """Tests for RandomStringNode."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_random_string_default(self, execution_context) -> None:
        """Test random string with default settings."""
        from casare_rpa.nodes.random_nodes import RandomStringNode

        node = RandomStringNode(node_id="test_str_default")
        node.set_input_value("length", 10)

        result = await node.execute(execution_context)

        assert result["success"] is True
        string = node.get_output_value("result")
        assert len(string) == 10
        # Default includes uppercase, lowercase, digits
        assert re.match(r"^[A-Za-z0-9]+$", string)

    @pytest.mark.asyncio
    async def test_random_string_uppercase_only(self, execution_context) -> None:
        """Test random string with uppercase only."""
        from casare_rpa.nodes.random_nodes import RandomStringNode

        node = RandomStringNode(
            node_id="test_str_upper",
            config={
                "include_uppercase": True,
                "include_lowercase": False,
                "include_digits": False,
            },
        )
        node.set_input_value("length", 10)

        result = await node.execute(execution_context)

        assert result["success"] is True
        string = node.get_output_value("result")
        assert len(string) == 10
        assert string.isupper()

    @pytest.mark.asyncio
    async def test_random_string_digits_only(self, execution_context) -> None:
        """Test random string with digits only."""
        from casare_rpa.nodes.random_nodes import RandomStringNode

        node = RandomStringNode(
            node_id="test_str_digits",
            config={
                "include_uppercase": False,
                "include_lowercase": False,
                "include_digits": True,
            },
        )
        node.set_input_value("length", 8)

        result = await node.execute(execution_context)

        assert result["success"] is True
        string = node.get_output_value("result")
        assert len(string) == 8
        assert string.isdigit()

    @pytest.mark.asyncio
    async def test_random_string_with_special(self, execution_context) -> None:
        """Test random string with special characters."""
        from casare_rpa.nodes.random_nodes import RandomStringNode

        node = RandomStringNode(
            node_id="test_str_special",
            config={
                "include_uppercase": False,
                "include_lowercase": False,
                "include_digits": False,
                "include_special": True,
            },
        )
        node.set_input_value("length", 10)

        result = await node.execute(execution_context)

        assert result["success"] is True
        string = node.get_output_value("result")
        assert len(string) == 10
        # Should only contain punctuation
        import string as string_module

        assert all(c in string_module.punctuation for c in string)

    @pytest.mark.asyncio
    async def test_random_string_custom_chars(self, execution_context) -> None:
        """Test random string with custom character set."""
        from casare_rpa.nodes.random_nodes import RandomStringNode

        node = RandomStringNode(
            node_id="test_str_custom", config={"custom_chars": "ABC123"}
        )
        node.set_input_value("length", 20)

        result = await node.execute(execution_context)

        assert result["success"] is True
        string = node.get_output_value("result")
        assert len(string) == 20
        assert all(c in "ABC123" for c in string)

    @pytest.mark.asyncio
    async def test_random_string_default_length(self, execution_context) -> None:
        """Test random string uses default length 8 when length is 0 or None."""
        from casare_rpa.nodes.random_nodes import RandomStringNode

        # When length is 0 or None, it defaults to 8
        node = RandomStringNode(node_id="test_str_default_len")
        node.set_input_value("length", None)

        result = await node.execute(execution_context)

        assert result["success"] is True
        string = node.get_output_value("result")
        assert len(string) == 8  # Default length


class TestRandomUUIDNode:
    """Tests for RandomUUIDNode."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_uuid_standard_format(self, execution_context) -> None:
        """Test UUID generation in standard format."""
        from casare_rpa.nodes.random_nodes import RandomUUIDNode

        node = RandomUUIDNode(node_id="test_uuid_std")

        result = await node.execute(execution_context)

        assert result["success"] is True
        uid = node.get_output_value("result")
        # Validate UUID format: 8-4-4-4-12 hex chars
        assert re.match(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", uid
        )

    @pytest.mark.asyncio
    async def test_uuid_hex_format(self, execution_context) -> None:
        """Test UUID generation in hex format."""
        from casare_rpa.nodes.random_nodes import RandomUUIDNode

        node = RandomUUIDNode(node_id="test_uuid_hex", config={"format": "hex"})

        result = await node.execute(execution_context)

        assert result["success"] is True
        uid = node.get_output_value("result")
        # Hex format: 32 hex chars, no dashes
        assert re.match(r"^[0-9a-f]{32}$", uid)

    @pytest.mark.asyncio
    async def test_uuid_urn_format(self, execution_context) -> None:
        """Test UUID generation in URN format."""
        from casare_rpa.nodes.random_nodes import RandomUUIDNode

        node = RandomUUIDNode(node_id="test_uuid_urn", config={"format": "urn"})

        result = await node.execute(execution_context)

        assert result["success"] is True
        uid = node.get_output_value("result")
        # URN format starts with urn:uuid:
        assert uid.startswith("urn:uuid:")

    @pytest.mark.asyncio
    async def test_uuid_uniqueness(self, execution_context) -> None:
        """Test UUIDs are unique."""
        from casare_rpa.nodes.random_nodes import RandomUUIDNode

        uuids = []
        for i in range(10):
            node = RandomUUIDNode(node_id=f"test_uuid_uniq_{i}")
            await node.execute(execution_context)
            uuids.append(node.get_output_value("result"))

        # All should be unique
        assert len(uuids) == len(set(uuids))

    @pytest.mark.asyncio
    async def test_uuid_version_4(self, execution_context) -> None:
        """Test UUID version 4 (random) is generated by default."""
        from casare_rpa.nodes.random_nodes import RandomUUIDNode

        node = RandomUUIDNode(node_id="test_uuid_v4", config={"version": 4})

        result = await node.execute(execution_context)

        assert result["success"] is True
        uid_str = node.get_output_value("result")
        # Validate by parsing
        parsed = uuid.UUID(uid_str)
        assert parsed.version == 4


class TestShuffleListNode:
    """Tests for ShuffleListNode."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_shuffle_list(self, execution_context) -> None:
        """Test shuffling a list."""
        from casare_rpa.nodes.random_nodes import ShuffleListNode

        original = [1, 2, 3, 4, 5]
        node = ShuffleListNode(node_id="test_shuffle")
        node.set_input_value("items", original.copy())

        result = await node.execute(execution_context)

        assert result["success"] is True
        shuffled = node.get_output_value("result")
        # Same length
        assert len(shuffled) == len(original)
        # Same elements
        assert sorted(shuffled) == sorted(original)

    @pytest.mark.asyncio
    async def test_shuffle_preserves_original(self, execution_context) -> None:
        """Test shuffling does not modify original list."""
        from casare_rpa.nodes.random_nodes import ShuffleListNode

        original = [1, 2, 3, 4, 5]
        node = ShuffleListNode(node_id="test_shuffle_orig")
        node.set_input_value("items", original)

        await node.execute(execution_context)

        # Original should be unchanged
        assert original == [1, 2, 3, 4, 5]

    @pytest.mark.asyncio
    async def test_shuffle_empty_list(self, execution_context) -> None:
        """Test shuffling empty list."""
        from casare_rpa.nodes.random_nodes import ShuffleListNode

        node = ShuffleListNode(node_id="test_shuffle_empty")
        node.set_input_value("items", [])

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == []

    @pytest.mark.asyncio
    async def test_shuffle_single_item(self, execution_context) -> None:
        """Test shuffling single item list."""
        from casare_rpa.nodes.random_nodes import ShuffleListNode

        node = ShuffleListNode(node_id="test_shuffle_single")
        node.set_input_value("items", ["only"])

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == ["only"]

    @pytest.mark.asyncio
    async def test_shuffle_tuple_input(self, execution_context) -> None:
        """Test shuffling tuple input (converts to list)."""
        from casare_rpa.nodes.random_nodes import ShuffleListNode

        node = ShuffleListNode(node_id="test_shuffle_tuple")
        node.set_input_value("items", (1, 2, 3))

        result = await node.execute(execution_context)

        assert result["success"] is True
        shuffled = node.get_output_value("result")
        assert isinstance(shuffled, list)
        assert sorted(shuffled) == [1, 2, 3]


class TestRandomEdgeCases:
    """Edge case tests for random nodes."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_random_number_same_min_max(self, execution_context) -> None:
        """Test random number when min equals max."""
        from casare_rpa.nodes.random_nodes import RandomNumberNode

        node = RandomNumberNode(node_id="test_same", config={"integer_only": True})
        node.set_input_value("min_value", 5)
        node.set_input_value("max_value", 5)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 5

    @pytest.mark.asyncio
    async def test_random_string_no_chars_fallback(self, execution_context) -> None:
        """Test random string falls back when all char options disabled."""
        from casare_rpa.nodes.random_nodes import RandomStringNode

        node = RandomStringNode(
            node_id="test_fallback",
            config={
                "include_uppercase": False,
                "include_lowercase": False,
                "include_digits": False,
                "include_special": False,
            },
        )
        node.set_input_value("length", 10)

        result = await node.execute(execution_context)

        assert result["success"] is True
        string = node.get_output_value("result")
        # Should fall back to alphanumeric
        assert len(string) == 10

    @pytest.mark.asyncio
    async def test_execution_result_pattern(self, execution_context) -> None:
        """Test all random nodes follow ExecutionResult pattern."""
        from casare_rpa.nodes.random_nodes import (
            RandomNumberNode,
            RandomChoiceNode,
            RandomStringNode,
            RandomUUIDNode,
            ShuffleListNode,
        )

        # Test RandomNumberNode
        node1 = RandomNumberNode(node_id="test_pattern1")
        result1 = await node1.execute(execution_context)
        assert "success" in result1
        assert "data" in result1
        assert "next_nodes" in result1
        assert "exec_out" in result1["next_nodes"]

        # Test RandomChoiceNode
        node2 = RandomChoiceNode(node_id="test_pattern2")
        node2.set_input_value("items", ["a", "b", "c"])
        result2 = await node2.execute(execution_context)
        assert result2["success"] is True

        # Test RandomStringNode
        node3 = RandomStringNode(node_id="test_pattern3")
        node3.set_input_value("length", 5)
        result3 = await node3.execute(execution_context)
        assert result3["success"] is True

        # Test RandomUUIDNode
        node4 = RandomUUIDNode(node_id="test_pattern4")
        result4 = await node4.execute(execution_context)
        assert result4["success"] is True

        # Test ShuffleListNode
        node5 = ShuffleListNode(node_id="test_pattern5")
        node5.set_input_value("items", [1, 2, 3])
        result5 = await node5.execute(execution_context)
        assert result5["success"] is True
