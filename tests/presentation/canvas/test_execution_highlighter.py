"""
Tests for ExecutionHighlighter.

Tests the visual execution trail functionality including:
- Node state highlighting (running, success, error, breakpoint, skipped)
- Execution path tracking
- Debug controller signal integration
- Fade timers for success state
"""

import pytest
from unittest.mock import MagicMock, patch

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication


class TestHighlightState:
    """Tests for HighlightState enum."""

    def test_highlight_state_values(self):
        """Test that HighlightState has expected values."""
        from casare_rpa.presentation.canvas.graph.execution_highlighter import (
            HighlightState,
        )

        assert HighlightState.IDLE is not None
        assert HighlightState.RUNNING is not None
        assert HighlightState.SUCCESS is not None
        assert HighlightState.ERROR is not None
        assert HighlightState.BREAKPOINT is not None
        assert HighlightState.SKIPPED is not None


class TestExecutionHighlighter:
    """Tests for ExecutionHighlighter class."""

    @pytest.fixture
    def mock_graph(self):
        """Create mock graph widget."""
        graph = MagicMock()
        graph.all_nodes.return_value = []
        return graph

    @pytest.fixture
    def highlighter(self, mock_graph):
        """Create ExecutionHighlighter instance."""
        from casare_rpa.presentation.canvas.graph.execution_highlighter import (
            ExecutionHighlighter,
        )

        return ExecutionHighlighter(mock_graph)

    def test_initialization(self, highlighter):
        """Test highlighter initializes with empty state."""
        assert highlighter._highlights == {}
        assert highlighter._execution_path == []
        assert highlighter._execution_order == {}

    def test_highlight_running(self, highlighter):
        """Test highlighting a node as running."""
        from casare_rpa.presentation.canvas.graph.execution_highlighter import (
            HighlightState,
        )

        highlighter.highlight_running("node_1")

        assert highlighter.get_state("node_1") == HighlightState.RUNNING
        assert "node_1" in highlighter._execution_path
        assert highlighter._execution_order["node_1"] == 0

    def test_highlight_success(self, highlighter):
        """Test highlighting a node as success."""
        from casare_rpa.presentation.canvas.graph.execution_highlighter import (
            HighlightState,
        )

        highlighter.highlight_success("node_1", auto_fade=False)

        assert highlighter.get_state("node_1") == HighlightState.SUCCESS

    def test_highlight_error(self, highlighter):
        """Test highlighting a node as error."""
        from casare_rpa.presentation.canvas.graph.execution_highlighter import (
            HighlightState,
        )

        highlighter.highlight_error("node_1")

        assert highlighter.get_state("node_1") == HighlightState.ERROR

    def test_highlight_breakpoint(self, highlighter):
        """Test highlighting a node as breakpoint."""
        from casare_rpa.presentation.canvas.graph.execution_highlighter import (
            HighlightState,
        )

        highlighter.highlight_breakpoint("node_1")

        assert highlighter.get_state("node_1") == HighlightState.BREAKPOINT

    def test_highlight_skipped(self, highlighter):
        """Test highlighting a node as skipped."""
        from casare_rpa.presentation.canvas.graph.execution_highlighter import (
            HighlightState,
        )

        highlighter.highlight_skipped("node_1")

        assert highlighter.get_state("node_1") == HighlightState.SKIPPED

    def test_clear_highlight(self, highlighter):
        """Test clearing a highlight."""
        from casare_rpa.presentation.canvas.graph.execution_highlighter import (
            HighlightState,
        )

        highlighter.highlight_running("node_1")
        highlighter.clear_highlight("node_1")

        assert highlighter.get_state("node_1") == HighlightState.IDLE
        assert "node_1" not in highlighter._highlights

    def test_clear_all(self, highlighter):
        """Test clearing all highlights."""
        highlighter.highlight_running("node_1")
        highlighter.highlight_success("node_2", auto_fade=False)
        highlighter.highlight_error("node_3")

        highlighter.clear_all()

        assert highlighter._highlights == {}
        assert highlighter._execution_path == []
        assert highlighter._execution_order == {}

    def test_get_execution_path(self, highlighter):
        """Test getting execution path."""
        highlighter.highlight_running("node_1")
        highlighter.highlight_running("node_2")
        highlighter.highlight_running("node_3")

        path = highlighter.get_execution_path()

        assert path == ["node_1", "node_2", "node_3"]

    def test_get_execution_order(self, highlighter):
        """Test getting execution order for a node."""
        highlighter.highlight_running("node_a")
        highlighter.highlight_running("node_b")
        highlighter.highlight_running("node_c")

        assert highlighter.get_execution_order("node_a") == 0
        assert highlighter.get_execution_order("node_b") == 1
        assert highlighter.get_execution_order("node_c") == 2
        assert highlighter.get_execution_order("node_unknown") is None

    def test_highlight_path(self, highlighter):
        """Test setting execution path directly."""
        node_ids = ["node_1", "node_2", "node_3"]

        highlighter.highlight_path(node_ids)

        assert highlighter._execution_path == node_ids
        assert highlighter._execution_order == {
            "node_1": 0,
            "node_2": 1,
            "node_3": 2,
        }

    def test_state_transitions(self, highlighter):
        """Test state transitions (running -> success -> idle)."""
        from casare_rpa.presentation.canvas.graph.execution_highlighter import (
            HighlightState,
        )

        # Start running
        highlighter.highlight_running("node_1")
        assert highlighter.get_state("node_1") == HighlightState.RUNNING

        # Complete successfully
        highlighter.highlight_success("node_1", auto_fade=False)
        assert highlighter.get_state("node_1") == HighlightState.SUCCESS

        # Clear
        highlighter.clear_highlight("node_1")
        assert highlighter.get_state("node_1") == HighlightState.IDLE

    def test_cleanup(self, highlighter):
        """Test cleanup releases resources."""
        highlighter.highlight_running("node_1")
        highlighter.highlight_success("node_2", auto_fade=True)

        highlighter.cleanup()

        assert highlighter._highlights == {}
        assert highlighter._execution_path == []
        assert highlighter._fade_timers == {}


class TestExecutionHighlighterWithDebugController:
    """Tests for ExecutionHighlighter with DebugController integration."""

    @pytest.fixture
    def mock_debug_controller(self):
        """Create mock debug controller with signals."""
        controller = MagicMock()
        controller.breakpoint_hit = MagicMock()
        controller.execution_resumed = MagicMock()
        controller.step_completed = MagicMock()
        return controller

    def test_debug_controller_connection(self, mock_debug_controller):
        """Test that highlighter connects to debug controller signals."""
        from casare_rpa.presentation.canvas.graph.execution_highlighter import (
            ExecutionHighlighter,
        )

        mock_graph = MagicMock()
        mock_graph.all_nodes.return_value = []

        highlighter = ExecutionHighlighter(mock_graph, mock_debug_controller)

        # Verify signals were connected
        mock_debug_controller.breakpoint_hit.connect.assert_called()
        mock_debug_controller.execution_resumed.connect.assert_called()
        mock_debug_controller.step_completed.connect.assert_called()
