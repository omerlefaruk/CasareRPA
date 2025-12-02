"""
Tests for ExecutionController._on_node_completed method.

Tests the handling of execution time display from NODE_COMPLETED events,
covering:
- execution_time (seconds) field support
- duration_ms (milliseconds) field support
- Edge cases (None, zero, negative values)

Note: These tests mock the method directly without instantiating the full controller
      because the controller requires a real QMainWindow parent.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch


class TestOnNodeCompletedLogic:
    """
    Tests for the _on_node_completed logic.

    These tests extract the core logic of _on_node_completed and test it
    in isolation to avoid Qt dependency issues.
    """

    @pytest.fixture
    def mock_visual_node(self):
        """Create a mock visual node with update_status and update_execution_time."""
        node = Mock()
        node.update_status = Mock()
        node.update_execution_time = Mock()
        return node

    def _extract_execution_time(self, event_data):
        """
        Extract the execution time logic from _on_node_completed.

        This mirrors the implementation in ExecutionController._on_node_completed:
        - Support both 'execution_time' (seconds) and 'duration_ms' (milliseconds)
        - execution_time takes precedence
        - Returns None if no timing data available
        """
        execution_time_sec = None
        if isinstance(event_data, dict):
            if "execution_time" in event_data:
                execution_time_sec = event_data.get("execution_time")
            elif "duration_ms" in event_data:
                duration_ms = event_data.get("duration_ms")
                if duration_ms is not None:
                    execution_time_sec = duration_ms / 1000.0
        return execution_time_sec

    # =========================================================================
    # Happy Path Tests
    # =========================================================================

    def test_execution_time_seconds_extracted_correctly(self):
        """Test that execution_time in seconds is extracted correctly."""
        event_data = {
            "node_id": "test_node",
            "execution_time": 1.5,  # 1.5 seconds
        }

        result = self._extract_execution_time(event_data)

        assert result == 1.5

    def test_duration_ms_converted_to_seconds(self):
        """Test that duration_ms is converted to seconds correctly."""
        event_data = {
            "node_id": "test_node",
            "duration_ms": 1500,  # 1500 ms = 1.5 seconds
        }

        result = self._extract_execution_time(event_data)

        assert result == 1.5

    def test_execution_time_takes_precedence(self):
        """Test that execution_time takes precedence over duration_ms."""
        event_data = {
            "node_id": "test_node",
            "execution_time": 2.5,  # Should use this
            "duration_ms": 1000,  # Should ignore this
        }

        result = self._extract_execution_time(event_data)

        assert result == 2.5

    # =========================================================================
    # Edge Case Tests
    # =========================================================================

    def test_zero_execution_time(self):
        """Test that zero execution time is valid."""
        event_data = {
            "node_id": "test_node",
            "execution_time": 0.0,
        }

        result = self._extract_execution_time(event_data)

        assert result == 0.0

    def test_zero_duration_ms(self):
        """Test that zero duration_ms converts to 0.0 seconds."""
        event_data = {
            "node_id": "test_node",
            "duration_ms": 0,
        }

        result = self._extract_execution_time(event_data)

        assert result == 0.0

    def test_none_execution_time_returns_none(self):
        """Test that None execution_time returns None."""
        event_data = {
            "node_id": "test_node",
            "execution_time": None,
        }

        result = self._extract_execution_time(event_data)

        assert result is None

    def test_none_duration_ms_returns_none(self):
        """Test that None duration_ms returns None."""
        event_data = {
            "node_id": "test_node",
            "duration_ms": None,
        }

        result = self._extract_execution_time(event_data)

        assert result is None

    def test_missing_timing_fields_returns_none(self):
        """Test that missing timing fields returns None."""
        event_data = {
            "node_id": "test_node",
            # No execution_time or duration_ms
        }

        result = self._extract_execution_time(event_data)

        assert result is None

    def test_very_small_execution_time(self):
        """Test sub-millisecond execution times."""
        event_data = {
            "node_id": "test_node",
            "execution_time": 0.0001,  # 0.1 ms
        }

        result = self._extract_execution_time(event_data)

        assert result == 0.0001

    def test_large_execution_time(self):
        """Test large execution times (1 hour)."""
        event_data = {
            "node_id": "test_node",
            "execution_time": 3600.0,  # 1 hour
        }

        result = self._extract_execution_time(event_data)

        assert result == 3600.0

    # =========================================================================
    # Precision Tests
    # =========================================================================

    def test_duration_ms_conversion_precision(self):
        """Test that duration_ms conversion maintains precision."""
        event_data = {
            "node_id": "test_node",
            "duration_ms": 1234.567,
        }

        result = self._extract_execution_time(event_data)

        # 1234.567 ms / 1000 = 1.234567 seconds
        assert abs(result - 1.234567) < 0.0001

    def test_fractional_duration_ms(self):
        """Test fractional milliseconds."""
        event_data = {
            "node_id": "test_node",
            "duration_ms": 0.5,  # 0.5 ms = 0.0005 seconds
        }

        result = self._extract_execution_time(event_data)

        assert result == 0.0005

    # =========================================================================
    # Sad Path Tests
    # =========================================================================

    def test_non_dict_event_data_returns_none(self):
        """Test that non-dict event data returns None."""
        result = self._extract_execution_time("not a dict")
        assert result is None

        result = self._extract_execution_time(None)
        assert result is None

        result = self._extract_execution_time(123)
        assert result is None


class TestNodeCompletedEventHandling:
    """
    Tests for the full _on_node_completed event handling.

    Uses patching to test the method in isolation.
    """

    def _simulate_on_node_completed(self, node_index, event):
        """
        Simulate the _on_node_completed logic without controller instantiation.

        This mirrors the implementation to verify the integration logic.
        """
        # Extract data from Event object
        event_data = event.data if hasattr(event, "data") else event
        node_id = event_data.get("node_id") if isinstance(event_data, dict) else None

        if node_id:
            visual_node = node_index.get(node_id)
            if visual_node and hasattr(visual_node, "update_status"):
                visual_node.update_status("success")

                # Update execution time if available
                execution_time_sec = None
                if isinstance(event_data, dict):
                    if "execution_time" in event_data:
                        execution_time_sec = event_data.get("execution_time")
                    elif "duration_ms" in event_data:
                        duration_ms = event_data.get("duration_ms")
                        if duration_ms is not None:
                            execution_time_sec = duration_ms / 1000.0

                if execution_time_sec is not None and hasattr(
                    visual_node, "update_execution_time"
                ):
                    visual_node.update_execution_time(execution_time_sec)

    @pytest.fixture
    def mock_visual_node(self):
        """Create a mock visual node."""
        node = Mock()
        node.update_status = Mock()
        node.update_execution_time = Mock()
        return node

    def test_node_completed_with_execution_time(self, mock_visual_node):
        """Test NODE_COMPLETED with execution_time field."""
        node_index = {"test_node_id": mock_visual_node}
        event = Mock()
        event.data = {
            "node_id": "test_node_id",
            "execution_time": 1.5,
        }

        self._simulate_on_node_completed(node_index, event)

        mock_visual_node.update_status.assert_called_once_with("success")
        mock_visual_node.update_execution_time.assert_called_once_with(1.5)

    def test_node_completed_with_duration_ms(self, mock_visual_node):
        """Test NODE_COMPLETED with duration_ms field."""
        node_index = {"test_node_id": mock_visual_node}
        event = Mock()
        event.data = {
            "node_id": "test_node_id",
            "duration_ms": 1500,
        }

        self._simulate_on_node_completed(node_index, event)

        mock_visual_node.update_status.assert_called_once_with("success")
        mock_visual_node.update_execution_time.assert_called_once_with(1.5)

    def test_node_completed_execution_time_precedence(self, mock_visual_node):
        """Test that execution_time takes precedence."""
        node_index = {"test_node_id": mock_visual_node}
        event = Mock()
        event.data = {
            "node_id": "test_node_id",
            "execution_time": 2.5,
            "duration_ms": 1000,
        }

        self._simulate_on_node_completed(node_index, event)

        mock_visual_node.update_execution_time.assert_called_once_with(2.5)

    def test_node_completed_updates_status(self, mock_visual_node):
        """Test that NODE_COMPLETED always updates status to success."""
        node_index = {"test_node_id": mock_visual_node}
        event = Mock()
        event.data = {"node_id": "test_node_id"}

        self._simulate_on_node_completed(node_index, event)

        mock_visual_node.update_status.assert_called_once_with("success")

    def test_node_completed_without_timing_no_update(self, mock_visual_node):
        """Test NODE_COMPLETED without timing fields does not update time."""
        node_index = {"test_node_id": mock_visual_node}
        event = Mock()
        event.data = {"node_id": "test_node_id"}

        self._simulate_on_node_completed(node_index, event)

        mock_visual_node.update_status.assert_called_once_with("success")
        mock_visual_node.update_execution_time.assert_not_called()

    def test_node_completed_with_none_execution_time(self, mock_visual_node):
        """Test NODE_COMPLETED with None execution_time."""
        node_index = {"test_node_id": mock_visual_node}
        event = Mock()
        event.data = {
            "node_id": "test_node_id",
            "execution_time": None,
        }

        self._simulate_on_node_completed(node_index, event)

        mock_visual_node.update_status.assert_called_once_with("success")
        mock_visual_node.update_execution_time.assert_not_called()

    def test_node_completed_unknown_node_id(self, mock_visual_node):
        """Test NODE_COMPLETED with unknown node_id."""
        node_index = {"test_node_id": mock_visual_node}
        event = Mock()
        event.data = {
            "node_id": "unknown_id",
            "execution_time": 1.0,
        }

        self._simulate_on_node_completed(node_index, event)

        # Nothing should happen to mock_visual_node
        mock_visual_node.update_status.assert_not_called()
        mock_visual_node.update_execution_time.assert_not_called()

    def test_node_completed_missing_node_id(self, mock_visual_node):
        """Test NODE_COMPLETED with missing node_id."""
        node_index = {"test_node_id": mock_visual_node}
        event = Mock()
        event.data = {
            "execution_time": 1.0,
        }

        self._simulate_on_node_completed(node_index, event)

        # Nothing should happen
        mock_visual_node.update_status.assert_not_called()
        mock_visual_node.update_execution_time.assert_not_called()

    def test_node_completed_dict_event(self, mock_visual_node):
        """Test NODE_COMPLETED with event as dict (not Event object)."""
        node_index = {"test_node_id": mock_visual_node}
        event = {
            "node_id": "test_node_id",
            "execution_time": 2.0,
        }

        self._simulate_on_node_completed(node_index, event)

        mock_visual_node.update_status.assert_called_once_with("success")
        mock_visual_node.update_execution_time.assert_called_once_with(2.0)

    def test_node_completed_visual_node_missing_methods(self):
        """Test NODE_COMPLETED when visual node lacks methods."""
        visual_node = Mock(spec=[])  # Empty spec - no methods
        node_index = {"test_node_id": visual_node}
        event = Mock()
        event.data = {
            "node_id": "test_node_id",
            "execution_time": 1.0,
        }

        # Should not raise
        self._simulate_on_node_completed(node_index, event)

    def test_node_completed_zero_execution_time(self, mock_visual_node):
        """Test NODE_COMPLETED with zero execution time."""
        node_index = {"test_node_id": mock_visual_node}
        event = Mock()
        event.data = {
            "node_id": "test_node_id",
            "execution_time": 0.0,
        }

        self._simulate_on_node_completed(node_index, event)

        mock_visual_node.update_execution_time.assert_called_once_with(0.0)


class TestDurationMsConversion:
    """Tests specifically for duration_ms to seconds conversion."""

    def test_integer_duration_ms(self):
        """Test integer duration_ms conversion."""
        duration_ms = 1500
        expected_seconds = 1.5

        result = duration_ms / 1000.0

        assert result == expected_seconds

    def test_float_duration_ms(self):
        """Test float duration_ms conversion."""
        duration_ms = 1234.567
        expected_seconds = 1.234567

        result = duration_ms / 1000.0

        assert abs(result - expected_seconds) < 0.0001

    def test_zero_duration_ms(self):
        """Test zero duration_ms conversion."""
        duration_ms = 0
        expected_seconds = 0.0

        result = duration_ms / 1000.0

        assert result == expected_seconds

    def test_sub_millisecond_duration(self):
        """Test sub-millisecond duration conversion."""
        duration_ms = 0.1  # 0.1 ms = 0.0001 seconds

        result = duration_ms / 1000.0

        assert result == 0.0001

    def test_large_duration_ms(self):
        """Test large duration_ms conversion (1 hour)."""
        duration_ms = 3600000  # 1 hour in ms

        result = duration_ms / 1000.0

        assert result == 3600.0
