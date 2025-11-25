"""
Tests for Random and DateTime nodes.

Tests random number generation, string generation, UUIDs, and datetime operations.
"""

import pytest
import re
import uuid
from datetime import datetime, timedelta

from casare_rpa.nodes.random_nodes import (
    RandomNumberNode,
    RandomChoiceNode,
    RandomStringNode,
    RandomUUIDNode,
    ShuffleListNode,
)
from casare_rpa.nodes.datetime_nodes import (
    GetCurrentDateTimeNode,
    FormatDateTimeNode,
    ParseDateTimeNode,
    DateTimeAddNode,
    DateTimeDiffNode,
    DateTimeCompareNode,
    GetTimestampNode,
)
from casare_rpa.core.types import NodeStatus


class TestRandomNumberNode:
    """Tests for RandomNumber node."""

    @pytest.mark.asyncio
    async def test_random_number_basic(self, execution_context):
        """Test basic random number generation."""
        node = RandomNumberNode(node_id="rand_1")
        node.set_input_value("min_value", 0)
        node.set_input_value("max_value", 100)

        result = await node.execute(execution_context)

        assert result["success"] is True
        random_val = node.get_output_value("result")
        assert 0 <= random_val <= 100

    @pytest.mark.asyncio
    async def test_random_number_integer_only(self, execution_context):
        """Test integer-only random number generation."""
        node = RandomNumberNode(
            node_id="rand_1",
            config={"integer_only": True}
        )
        node.set_input_value("min_value", 1)
        node.set_input_value("max_value", 10)

        result = await node.execute(execution_context)

        assert result["success"] is True
        random_val = node.get_output_value("result")
        assert isinstance(random_val, int)
        assert 1 <= random_val <= 10

    @pytest.mark.asyncio
    async def test_random_number_defaults(self, execution_context):
        """Test default min/max values."""
        node = RandomNumberNode(node_id="rand_1")

        result = await node.execute(execution_context)

        assert result["success"] is True
        random_val = node.get_output_value("result")
        assert 0 <= random_val <= 100

    @pytest.mark.asyncio
    async def test_random_number_swapped_range(self, execution_context):
        """Test that swapped min/max are handled correctly."""
        node = RandomNumberNode(node_id="rand_1")
        node.set_input_value("min_value", 100)
        node.set_input_value("max_value", 0)

        result = await node.execute(execution_context)

        assert result["success"] is True
        random_val = node.get_output_value("result")
        assert 0 <= random_val <= 100


class TestRandomChoiceNode:
    """Tests for RandomChoice node."""

    @pytest.mark.asyncio
    async def test_random_choice_single(self, execution_context):
        """Test selecting a single random item."""
        node = RandomChoiceNode(node_id="choice_1")
        node.set_input_value("items", ["a", "b", "c", "d"])

        result = await node.execute(execution_context)

        assert result["success"] is True
        choice = node.get_output_value("result")
        assert choice in ["a", "b", "c", "d"]
        assert node.get_output_value("index") >= 0

    @pytest.mark.asyncio
    async def test_random_choice_multiple(self, execution_context):
        """Test selecting multiple random items."""
        node = RandomChoiceNode(
            node_id="choice_1",
            config={"count": 3, "allow_duplicates": False}
        )
        node.set_input_value("items", ["a", "b", "c", "d", "e"])

        result = await node.execute(execution_context)

        assert result["success"] is True
        choices = node.get_output_value("result")
        assert len(choices) == 3
        assert len(set(choices)) == 3  # No duplicates

    @pytest.mark.asyncio
    async def test_random_choice_empty_list_fails(self, execution_context):
        """Test that empty list raises error."""
        node = RandomChoiceNode(node_id="choice_1")
        node.set_input_value("items", [])

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "empty" in result["error"].lower()


class TestRandomStringNode:
    """Tests for RandomString node."""

    @pytest.mark.asyncio
    async def test_random_string_basic(self, execution_context):
        """Test basic random string generation."""
        node = RandomStringNode(node_id="str_1")
        node.set_input_value("length", 10)

        result = await node.execute(execution_context)

        assert result["success"] is True
        random_str = node.get_output_value("result")
        assert len(random_str) == 10

    @pytest.mark.asyncio
    async def test_random_string_digits_only(self, execution_context):
        """Test digit-only random string."""
        node = RandomStringNode(
            node_id="str_1",
            config={
                "include_uppercase": False,
                "include_lowercase": False,
                "include_digits": True,
                "include_special": False
            }
        )
        node.set_input_value("length", 8)

        result = await node.execute(execution_context)

        assert result["success"] is True
        random_str = node.get_output_value("result")
        assert random_str.isdigit()

    @pytest.mark.asyncio
    async def test_random_string_custom_chars(self, execution_context):
        """Test custom character set."""
        node = RandomStringNode(
            node_id="str_1",
            config={"custom_chars": "ABC123"}
        )
        node.set_input_value("length", 20)

        result = await node.execute(execution_context)

        assert result["success"] is True
        random_str = node.get_output_value("result")
        assert all(c in "ABC123" for c in random_str)


class TestRandomUUIDNode:
    """Tests for RandomUUID node."""

    @pytest.mark.asyncio
    async def test_uuid_generation(self, execution_context):
        """Test UUID generation."""
        node = RandomUUIDNode(node_id="uuid_1")

        result = await node.execute(execution_context)

        assert result["success"] is True
        uid = node.get_output_value("result")
        # Verify it's a valid UUID format
        uuid.UUID(uid)

    @pytest.mark.asyncio
    async def test_uuid_hex_format(self, execution_context):
        """Test UUID hex format."""
        node = RandomUUIDNode(
            node_id="uuid_1",
            config={"format": "hex"}
        )

        result = await node.execute(execution_context)

        assert result["success"] is True
        uid = node.get_output_value("result")
        assert len(uid) == 32  # Hex format has no dashes
        assert "-" not in uid


class TestShuffleListNode:
    """Tests for ShuffleList node."""

    @pytest.mark.asyncio
    async def test_shuffle_list(self, execution_context):
        """Test list shuffling."""
        original = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        node = ShuffleListNode(node_id="shuffle_1")
        node.set_input_value("items", original.copy())

        result = await node.execute(execution_context)

        assert result["success"] is True
        shuffled = node.get_output_value("result")
        assert len(shuffled) == len(original)
        assert sorted(shuffled) == sorted(original)

    @pytest.mark.asyncio
    async def test_shuffle_preserves_elements(self, execution_context):
        """Test that shuffle preserves all elements."""
        original = ["a", "b", "c"]
        node = ShuffleListNode(node_id="shuffle_1")
        node.set_input_value("items", original.copy())

        result = await node.execute(execution_context)

        shuffled = node.get_output_value("result")
        assert set(shuffled) == set(original)


class TestGetCurrentDateTimeNode:
    """Tests for GetCurrentDateTime node."""

    @pytest.mark.asyncio
    async def test_get_current_datetime(self, execution_context):
        """Test getting current datetime."""
        node = GetCurrentDateTimeNode(node_id="dt_1")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("year") == datetime.now().year
        assert node.get_output_value("month") == datetime.now().month
        assert node.get_output_value("day") == datetime.now().day

    @pytest.mark.asyncio
    async def test_get_datetime_with_format(self, execution_context):
        """Test formatted datetime output."""
        node = GetCurrentDateTimeNode(
            node_id="dt_1",
            config={"format": "%Y-%m-%d"}
        )

        result = await node.execute(execution_context)

        assert result["success"] is True
        dt_str = node.get_output_value("datetime")
        assert re.match(r"\d{4}-\d{2}-\d{2}", dt_str)

    @pytest.mark.asyncio
    async def test_get_datetime_components(self, execution_context):
        """Test datetime components are available."""
        node = GetCurrentDateTimeNode(node_id="dt_1")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("timestamp") > 0
        assert 1 <= node.get_output_value("month") <= 12
        assert 1 <= node.get_output_value("day") <= 31
        assert 0 <= node.get_output_value("hour") <= 23
        assert 0 <= node.get_output_value("minute") <= 59
        assert 0 <= node.get_output_value("second") <= 59
        assert node.get_output_value("day_of_week") in [
            "Monday", "Tuesday", "Wednesday", "Thursday",
            "Friday", "Saturday", "Sunday"
        ]


class TestFormatDateTimeNode:
    """Tests for FormatDateTime node."""

    @pytest.mark.asyncio
    async def test_format_datetime_string(self, execution_context):
        """Test formatting datetime from string."""
        node = FormatDateTimeNode(
            node_id="fmt_1",
            config={"format": "%d/%m/%Y"}
        )
        node.set_input_value("datetime", "2024-01-15 10:30:00")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "15/01/2024"

    @pytest.mark.asyncio
    async def test_format_datetime_timestamp(self, execution_context):
        """Test formatting datetime from timestamp."""
        node = FormatDateTimeNode(
            node_id="fmt_1",
            config={"format": "%Y-%m-%d"}
        )
        # Use a known timestamp
        node.set_input_value("datetime", 1704067200)  # 2024-01-01 00:00:00 UTC

        result = await node.execute(execution_context)

        assert result["success"] is True
        # Result depends on local timezone


class TestParseDateTimeNode:
    """Tests for ParseDateTime node."""

    @pytest.mark.asyncio
    async def test_parse_datetime_basic(self, execution_context):
        """Test basic datetime parsing."""
        node = ParseDateTimeNode(node_id="parse_1")
        node.set_input_value("datetime_string", "2024-03-15 14:30:00")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("year") == 2024
        assert node.get_output_value("month") == 3
        assert node.get_output_value("day") == 15
        assert node.get_output_value("hour") == 14
        assert node.get_output_value("minute") == 30
        assert node.get_output_value("success") is True

    @pytest.mark.asyncio
    async def test_parse_datetime_with_format(self, execution_context):
        """Test parsing with explicit format."""
        node = ParseDateTimeNode(
            node_id="parse_1",
            config={"format": "%d/%m/%Y"}
        )
        node.set_input_value("datetime_string", "25/12/2024")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("year") == 2024
        assert node.get_output_value("month") == 12
        assert node.get_output_value("day") == 25


class TestDateTimeAddNode:
    """Tests for DateTimeAdd node."""

    @pytest.mark.asyncio
    async def test_add_days(self, execution_context):
        """Test adding days to datetime."""
        node = DateTimeAddNode(node_id="add_1")
        node.set_input_value("datetime", "2024-01-01T00:00:00")
        node.set_input_value("days", 10)

        result = await node.execute(execution_context)

        assert result["success"] is True
        result_dt = node.get_output_value("result")
        assert "2024-01-11" in result_dt

    @pytest.mark.asyncio
    async def test_add_negative_days(self, execution_context):
        """Test subtracting days from datetime."""
        node = DateTimeAddNode(node_id="add_1")
        node.set_input_value("datetime", "2024-01-15T00:00:00")
        node.set_input_value("days", -5)

        result = await node.execute(execution_context)

        assert result["success"] is True
        result_dt = node.get_output_value("result")
        assert "2024-01-10" in result_dt

    @pytest.mark.asyncio
    async def test_add_multiple_units(self, execution_context):
        """Test adding multiple time units."""
        node = DateTimeAddNode(node_id="add_1")
        node.set_input_value("datetime", "2024-01-01T10:00:00")
        node.set_input_value("hours", 2)
        node.set_input_value("minutes", 30)

        result = await node.execute(execution_context)

        assert result["success"] is True
        result_dt = node.get_output_value("result")
        assert "12:30" in result_dt


class TestDateTimeDiffNode:
    """Tests for DateTimeDiff node."""

    @pytest.mark.asyncio
    async def test_datetime_diff_days(self, execution_context):
        """Test calculating difference in days."""
        node = DateTimeDiffNode(node_id="diff_1")
        node.set_input_value("datetime_1", "2024-01-01T00:00:00")
        node.set_input_value("datetime_2", "2024-01-11T00:00:00")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("total_days") == 10.0
        assert node.get_output_value("days") == 10

    @pytest.mark.asyncio
    async def test_datetime_diff_negative(self, execution_context):
        """Test negative difference."""
        node = DateTimeDiffNode(node_id="diff_1")
        node.set_input_value("datetime_1", "2024-01-11T00:00:00")
        node.set_input_value("datetime_2", "2024-01-01T00:00:00")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("total_days") == -10.0


class TestDateTimeCompareNode:
    """Tests for DateTimeCompare node."""

    @pytest.mark.asyncio
    async def test_datetime_before(self, execution_context):
        """Test comparing earlier datetime."""
        node = DateTimeCompareNode(node_id="cmp_1")
        node.set_input_value("datetime_1", "2024-01-01T00:00:00")
        node.set_input_value("datetime_2", "2024-01-02T00:00:00")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("is_before") is True
        assert node.get_output_value("is_after") is False
        assert node.get_output_value("is_equal") is False
        assert node.get_output_value("comparison") == -1

    @pytest.mark.asyncio
    async def test_datetime_equal(self, execution_context):
        """Test comparing equal datetimes."""
        node = DateTimeCompareNode(node_id="cmp_1")
        node.set_input_value("datetime_1", "2024-01-01T12:00:00")
        node.set_input_value("datetime_2", "2024-01-01T12:00:00")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("is_equal") is True
        assert node.get_output_value("comparison") == 0


class TestGetTimestampNode:
    """Tests for GetTimestamp node."""

    @pytest.mark.asyncio
    async def test_get_timestamp_seconds(self, execution_context):
        """Test getting timestamp in seconds."""
        node = GetTimestampNode(node_id="ts_1")

        result = await node.execute(execution_context)

        assert result["success"] is True
        ts = node.get_output_value("timestamp")
        now_ts = datetime.now().timestamp()
        assert abs(ts - now_ts) < 2  # Within 2 seconds

    @pytest.mark.asyncio
    async def test_get_timestamp_milliseconds(self, execution_context):
        """Test getting timestamp in milliseconds."""
        node = GetTimestampNode(
            node_id="ts_1",
            config={"milliseconds": True}
        )

        result = await node.execute(execution_context)

        assert result["success"] is True
        ts = node.get_output_value("timestamp")
        assert ts > 1000000000000  # Should be in milliseconds
