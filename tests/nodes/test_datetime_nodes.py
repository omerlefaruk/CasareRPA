"""
Tests for DateTime nodes.

Tests 7 datetime nodes:
- GetCurrentDateTimeNode, FormatDateTimeNode, ParseDateTimeNode
- DateTimeAddNode, DateTimeDiffNode, DateTimeCompareNode, GetTimestampNode
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock

from casare_rpa.infrastructure.execution import ExecutionContext


class TestDateTimeNodes:
    """Tests for datetime category nodes."""

    @pytest.fixture
    def execution_context(self) -> None:
        """Create a mock execution context."""
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    # =========================================================================
    # GetCurrentDateTimeNode Tests (4 tests)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_get_current_datetime_basic(self, execution_context) -> None:
        """Test GetCurrentDateTimeNode returns current datetime."""
        from casare_rpa.nodes.datetime_nodes import GetCurrentDateTimeNode

        node = GetCurrentDateTimeNode(node_id="test_now")
        before = datetime.now()
        result = await node.execute(execution_context)
        after = datetime.now()

        assert result["success"] is True
        assert "exec_out" in result["next_nodes"]
        # Verify timestamp is between before and after
        ts = node.get_output_value("timestamp")
        assert before.timestamp() <= ts <= after.timestamp()

    @pytest.mark.asyncio
    async def test_get_current_datetime_components(self, execution_context) -> None:
        """Test GetCurrentDateTimeNode outputs all components."""
        from casare_rpa.nodes.datetime_nodes import GetCurrentDateTimeNode

        node = GetCurrentDateTimeNode(node_id="test_components")
        result = await node.execute(execution_context)

        assert result["success"] is True
        # Verify all component outputs exist
        assert isinstance(node.get_output_value("year"), int)
        assert isinstance(node.get_output_value("month"), int)
        assert isinstance(node.get_output_value("day"), int)
        assert isinstance(node.get_output_value("hour"), int)
        assert isinstance(node.get_output_value("minute"), int)
        assert isinstance(node.get_output_value("second"), int)
        assert node.get_output_value("day_of_week") in [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]

    @pytest.mark.asyncio
    async def test_get_current_datetime_custom_format(self, execution_context) -> None:
        """Test GetCurrentDateTimeNode with custom format."""
        from casare_rpa.nodes.datetime_nodes import GetCurrentDateTimeNode

        node = GetCurrentDateTimeNode(
            node_id="test_format", config={"format": "%Y-%m-%d"}
        )
        result = await node.execute(execution_context)

        assert result["success"] is True
        dt_str = node.get_output_value("datetime")
        # Validate format: YYYY-MM-DD
        assert len(dt_str) == 10
        assert dt_str[4] == "-" and dt_str[7] == "-"

    @pytest.mark.asyncio
    async def test_get_current_datetime_with_timezone(self, execution_context) -> None:
        """Test GetCurrentDateTimeNode with timezone."""
        from casare_rpa.nodes.datetime_nodes import GetCurrentDateTimeNode

        node = GetCurrentDateTimeNode(node_id="test_tz", config={"timezone": "UTC"})
        result = await node.execute(execution_context)

        # Should succeed (may fall back to local if ZoneInfo not available)
        assert result["success"] is True
        assert node.get_output_value("datetime") is not None

    # =========================================================================
    # FormatDateTimeNode Tests (4 tests)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_format_datetime_from_string(self, execution_context) -> None:
        """Test FormatDateTimeNode formats string input."""
        from casare_rpa.nodes.datetime_nodes import FormatDateTimeNode

        node = FormatDateTimeNode(
            node_id="test_format_str", config={"format": "%d/%m/%Y"}
        )
        node.set_input_value("datetime", "2024-01-15")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "15/01/2024"

    @pytest.mark.asyncio
    async def test_format_datetime_from_timestamp(self, execution_context) -> None:
        """Test FormatDateTimeNode formats timestamp input."""
        from casare_rpa.nodes.datetime_nodes import FormatDateTimeNode

        # Use a known timestamp: 2024-01-01 00:00:00 UTC
        ts = datetime(2024, 1, 1, 12, 30, 45).timestamp()

        node = FormatDateTimeNode(
            node_id="test_format_ts", config={"format": "%H:%M:%S"}
        )
        node.set_input_value("datetime", ts)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "12:30:45"

    @pytest.mark.asyncio
    async def test_format_datetime_with_input_format(self, execution_context) -> None:
        """Test FormatDateTimeNode with explicit input format."""
        from casare_rpa.nodes.datetime_nodes import FormatDateTimeNode

        node = FormatDateTimeNode(
            node_id="test_format_input", config={"format": "%Y-%m-%d"}
        )
        node.set_input_value("datetime", "15/01/2024")
        node.set_input_value("input_format", "%d/%m/%Y")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "2024-01-15"

    @pytest.mark.asyncio
    async def test_format_datetime_invalid_input(self, execution_context) -> None:
        """Test FormatDateTimeNode handles invalid input."""
        from casare_rpa.nodes.datetime_nodes import FormatDateTimeNode

        node = FormatDateTimeNode(node_id="test_format_invalid")
        node.set_input_value("datetime", "not-a-date")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "error" in result

    # =========================================================================
    # ParseDateTimeNode Tests (4 tests)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_parse_datetime_iso_format(self, execution_context) -> None:
        """Test ParseDateTimeNode parses ISO format."""
        from casare_rpa.nodes.datetime_nodes import ParseDateTimeNode

        node = ParseDateTimeNode(node_id="test_parse_iso")
        node.set_input_value("datetime_string", "2024-06-15T14:30:00")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("year") == 2024
        assert node.get_output_value("month") == 6
        assert node.get_output_value("day") == 15
        assert node.get_output_value("hour") == 14
        assert node.get_output_value("minute") == 30
        assert node.get_output_value("success") is True

    @pytest.mark.asyncio
    async def test_parse_datetime_common_formats(self, execution_context) -> None:
        """Test ParseDateTimeNode auto-detects common formats."""
        from casare_rpa.nodes.datetime_nodes import ParseDateTimeNode

        # Test DD/MM/YYYY format
        node = ParseDateTimeNode(node_id="test_parse_dmy")
        node.set_input_value("datetime_string", "15/06/2024")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("day") == 15
        assert node.get_output_value("month") == 6
        assert node.get_output_value("year") == 2024

    @pytest.mark.asyncio
    async def test_parse_datetime_with_format(self, execution_context) -> None:
        """Test ParseDateTimeNode with explicit format."""
        from casare_rpa.nodes.datetime_nodes import ParseDateTimeNode

        node = ParseDateTimeNode(
            node_id="test_parse_explicit", config={"format": "%B %d, %Y"}
        )
        node.set_input_value("datetime_string", "January 15, 2024")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("year") == 2024
        assert node.get_output_value("month") == 1
        assert node.get_output_value("day") == 15

    @pytest.mark.asyncio
    async def test_parse_datetime_empty_string(self, execution_context) -> None:
        """Test ParseDateTimeNode handles empty string."""
        from casare_rpa.nodes.datetime_nodes import ParseDateTimeNode

        node = ParseDateTimeNode(node_id="test_parse_empty")
        node.set_input_value("datetime_string", "")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert node.get_output_value("success") is False

    # =========================================================================
    # DateTimeAddNode Tests (4 tests)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_datetime_add_days(self, execution_context) -> None:
        """Test DateTimeAddNode adds days."""
        from casare_rpa.nodes.datetime_nodes import DateTimeAddNode

        node = DateTimeAddNode(node_id="test_add_days")
        node.set_input_value("datetime", "2024-01-15T00:00:00")
        node.set_input_value("days", 10)

        result = await node.execute(execution_context)

        assert result["success"] is True
        result_dt = node.get_output_value("result")
        assert "2024-01-25" in result_dt

    @pytest.mark.asyncio
    async def test_datetime_add_hours_minutes(self, execution_context) -> None:
        """Test DateTimeAddNode adds hours and minutes."""
        from casare_rpa.nodes.datetime_nodes import DateTimeAddNode

        node = DateTimeAddNode(node_id="test_add_time")
        node.set_input_value("datetime", "2024-01-15T10:00:00")
        node.set_input_value("hours", 2)
        node.set_input_value("minutes", 30)

        result = await node.execute(execution_context)

        assert result["success"] is True
        result_dt = node.get_output_value("result")
        assert "12:30:00" in result_dt

    @pytest.mark.asyncio
    async def test_datetime_subtract_days(self, execution_context) -> None:
        """Test DateTimeAddNode subtracts with negative values."""
        from casare_rpa.nodes.datetime_nodes import DateTimeAddNode

        node = DateTimeAddNode(node_id="test_subtract_days")
        node.set_input_value("datetime", "2024-01-15T00:00:00")
        node.set_input_value("days", -5)

        result = await node.execute(execution_context)

        assert result["success"] is True
        result_dt = node.get_output_value("result")
        assert "2024-01-10" in result_dt

    @pytest.mark.asyncio
    async def test_datetime_add_uses_current_if_null(self, execution_context) -> None:
        """Test DateTimeAddNode uses current datetime if input is None."""
        from casare_rpa.nodes.datetime_nodes import DateTimeAddNode

        before = datetime.now()
        node = DateTimeAddNode(node_id="test_add_null")
        node.set_input_value("datetime", None)
        node.set_input_value("seconds", 0)

        result = await node.execute(execution_context)
        after = datetime.now()

        assert result["success"] is True
        ts = node.get_output_value("timestamp")
        assert before.timestamp() <= ts <= after.timestamp()

    # =========================================================================
    # DateTimeDiffNode Tests (4 tests)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_datetime_diff_positive(self, execution_context) -> None:
        """Test DateTimeDiffNode calculates positive difference."""
        from casare_rpa.nodes.datetime_nodes import DateTimeDiffNode

        node = DateTimeDiffNode(node_id="test_diff_pos")
        node.set_input_value("datetime_1", "2024-01-01T00:00:00")
        node.set_input_value("datetime_2", "2024-01-02T00:00:00")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("total_days") == 1.0
        assert node.get_output_value("total_hours") == 24.0
        assert node.get_output_value("days") == 1

    @pytest.mark.asyncio
    async def test_datetime_diff_negative(self, execution_context) -> None:
        """Test DateTimeDiffNode calculates negative difference."""
        from casare_rpa.nodes.datetime_nodes import DateTimeDiffNode

        node = DateTimeDiffNode(node_id="test_diff_neg")
        node.set_input_value("datetime_1", "2024-01-02T00:00:00")
        node.set_input_value("datetime_2", "2024-01-01T00:00:00")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("total_days") == -1.0
        assert node.get_output_value("days") == -1

    @pytest.mark.asyncio
    async def test_datetime_diff_hours_minutes(self, execution_context) -> None:
        """Test DateTimeDiffNode calculates hours and minutes."""
        from casare_rpa.nodes.datetime_nodes import DateTimeDiffNode

        node = DateTimeDiffNode(node_id="test_diff_hm")
        node.set_input_value("datetime_1", "2024-01-01T10:00:00")
        node.set_input_value("datetime_2", "2024-01-01T12:30:45")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("hours") == 2
        assert node.get_output_value("minutes") == 30
        assert node.get_output_value("seconds") == 45

    @pytest.mark.asyncio
    async def test_datetime_diff_from_timestamps(self, execution_context) -> None:
        """Test DateTimeDiffNode works with timestamps."""
        from casare_rpa.nodes.datetime_nodes import DateTimeDiffNode

        ts1 = datetime(2024, 1, 1).timestamp()
        ts2 = datetime(2024, 1, 3).timestamp()

        node = DateTimeDiffNode(node_id="test_diff_ts")
        node.set_input_value("datetime_1", ts1)
        node.set_input_value("datetime_2", ts2)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("total_days") == 2.0

    # =========================================================================
    # DateTimeCompareNode Tests (4 tests)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_datetime_compare_before(self, execution_context) -> None:
        """Test DateTimeCompareNode detects before."""
        from casare_rpa.nodes.datetime_nodes import DateTimeCompareNode

        node = DateTimeCompareNode(node_id="test_compare_before")
        node.set_input_value("datetime_1", "2024-01-01")
        node.set_input_value("datetime_2", "2024-01-02")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("is_before") is True
        assert node.get_output_value("is_after") is False
        assert node.get_output_value("is_equal") is False
        assert node.get_output_value("comparison") == -1

    @pytest.mark.asyncio
    async def test_datetime_compare_after(self, execution_context) -> None:
        """Test DateTimeCompareNode detects after."""
        from casare_rpa.nodes.datetime_nodes import DateTimeCompareNode

        node = DateTimeCompareNode(node_id="test_compare_after")
        node.set_input_value("datetime_1", "2024-01-02")
        node.set_input_value("datetime_2", "2024-01-01")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("is_before") is False
        assert node.get_output_value("is_after") is True
        assert node.get_output_value("comparison") == 1

    @pytest.mark.asyncio
    async def test_datetime_compare_equal(self, execution_context) -> None:
        """Test DateTimeCompareNode detects equal."""
        from casare_rpa.nodes.datetime_nodes import DateTimeCompareNode

        node = DateTimeCompareNode(node_id="test_compare_equal")
        node.set_input_value("datetime_1", "2024-01-15T10:30:00")
        node.set_input_value("datetime_2", "2024-01-15T10:30:00")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("is_equal") is True
        assert node.get_output_value("comparison") == 0

    @pytest.mark.asyncio
    async def test_datetime_compare_invalid(self, execution_context) -> None:
        """Test DateTimeCompareNode handles invalid input."""
        from casare_rpa.nodes.datetime_nodes import DateTimeCompareNode

        node = DateTimeCompareNode(node_id="test_compare_invalid")
        node.set_input_value("datetime_1", "not-a-date")
        node.set_input_value("datetime_2", "2024-01-01")

        result = await node.execute(execution_context)

        assert result["success"] is False

    # =========================================================================
    # GetTimestampNode Tests (3 tests)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_get_timestamp_seconds(self, execution_context) -> None:
        """Test GetTimestampNode returns seconds."""
        from casare_rpa.nodes.datetime_nodes import GetTimestampNode

        before = datetime.now().timestamp()
        node = GetTimestampNode(node_id="test_ts_sec")
        result = await node.execute(execution_context)
        after = datetime.now().timestamp()

        assert result["success"] is True
        ts = node.get_output_value("timestamp")
        assert before <= ts <= after

    @pytest.mark.asyncio
    async def test_get_timestamp_milliseconds(self, execution_context) -> None:
        """Test GetTimestampNode returns milliseconds."""
        from casare_rpa.nodes.datetime_nodes import GetTimestampNode

        before = datetime.now().timestamp() * 1000
        node = GetTimestampNode(node_id="test_ts_ms", config={"milliseconds": True})
        result = await node.execute(execution_context)
        after = datetime.now().timestamp() * 1000

        assert result["success"] is True
        ts = node.get_output_value("timestamp")
        assert before <= ts <= after
        # Milliseconds should be much larger than seconds
        assert ts > 1000000000000

    @pytest.mark.asyncio
    async def test_get_timestamp_execution_result_pattern(
        self, execution_context
    ) -> None:
        """Test GetTimestampNode follows ExecutionResult pattern."""
        from casare_rpa.nodes.datetime_nodes import GetTimestampNode

        node = GetTimestampNode(node_id="test_ts_pattern")
        result = await node.execute(execution_context)

        # Verify ExecutionResult structure
        assert "success" in result
        assert "data" in result
        assert "next_nodes" in result
        assert result["success"] is True
        assert "timestamp" in result["data"]
        assert "exec_out" in result["next_nodes"]


class TestDateTimeEdgeCases:
    """Edge case tests for datetime nodes."""

    @pytest.fixture
    def execution_context(self) -> None:
        """Create a mock execution context."""
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_leap_year_handling(self, execution_context) -> None:
        """Test datetime nodes handle leap years."""
        from casare_rpa.nodes.datetime_nodes import DateTimeAddNode

        node = DateTimeAddNode(node_id="test_leap")
        node.set_input_value("datetime", "2024-02-28T00:00:00")
        node.set_input_value("days", 1)

        result = await node.execute(execution_context)

        assert result["success"] is True
        result_dt = node.get_output_value("result")
        assert "2024-02-29" in result_dt  # 2024 is leap year

    @pytest.mark.asyncio
    async def test_year_boundary_crossing(self, execution_context) -> None:
        """Test datetime addition across year boundary."""
        from casare_rpa.nodes.datetime_nodes import DateTimeAddNode

        node = DateTimeAddNode(node_id="test_year_boundary")
        node.set_input_value("datetime", "2024-12-31T23:00:00")
        node.set_input_value("hours", 2)

        result = await node.execute(execution_context)

        assert result["success"] is True
        result_dt = node.get_output_value("result")
        assert "2025-01-01" in result_dt

    @pytest.mark.asyncio
    async def test_iso_format_with_timezone(self, execution_context) -> None:
        """Test parsing ISO format with timezone Z suffix."""
        from casare_rpa.nodes.datetime_nodes import ParseDateTimeNode

        node = ParseDateTimeNode(node_id="test_iso_tz")
        node.set_input_value("datetime_string", "2024-06-15T14:30:00Z")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("year") == 2024
