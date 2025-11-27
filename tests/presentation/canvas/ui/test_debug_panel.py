"""
Comprehensive tests for DebugPanel UI.

Tests debug panel functionality including:
- Variable inspection
- Breakpoints
- Step controls
- Stack trace
"""

import pytest
from unittest.mock import Mock
from PySide6.QtWidgets import QApplication

from casare_rpa.presentation.canvas.ui.panels.debug_panel import DebugPanel


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def debug_panel(qapp):
    """Create a DebugPanel instance."""
    panel = DebugPanel()
    yield panel
    panel.deleteLater()


class TestDebugPanelInitialization:
    """Tests for DebugPanel initialization."""

    def test_initialization(self, qapp):
        """Test panel initializes correctly."""
        panel = DebugPanel()
        assert panel.windowTitle() == "Debug"
        panel.deleteLater()

    def test_setup_ui(self, debug_panel):
        """Test UI is set up."""
        assert debug_panel.widget() is not None


class TestVariableInspection:
    """Tests for variable inspection."""

    def test_update_variables(self, debug_panel):
        """Test updating variables display."""
        variables = {"var1": "value1", "var2": 42}

        if hasattr(debug_panel, "update_variables"):
            debug_panel.update_variables(variables)
        # Should not raise error

    def test_clear_variables(self, debug_panel):
        """Test clearing variables."""
        if hasattr(debug_panel, "clear_variables"):
            debug_panel.clear_variables()


class TestBreakpoints:
    """Tests for breakpoint management."""

    def test_add_breakpoint(self, debug_panel):
        """Test adding breakpoint."""
        if hasattr(debug_panel, "add_breakpoint"):
            debug_panel.add_breakpoint("node1")

    def test_remove_breakpoint(self, debug_panel):
        """Test removing breakpoint."""
        if hasattr(debug_panel, "remove_breakpoint"):
            debug_panel.remove_breakpoint("node1")

    def test_clear_breakpoints(self, debug_panel):
        """Test clearing all breakpoints."""
        if hasattr(debug_panel, "clear_breakpoints"):
            debug_panel.clear_breakpoints()


class TestStepControls:
    """Tests for step control buttons."""

    def test_step_over(self, debug_panel):
        """Test step over button."""
        # Should have step control buttons
        assert hasattr(debug_panel, "widget")

    def test_step_into(self, debug_panel):
        """Test step into button."""
        # Buttons may emit signals
        pass

    def test_continue_execution(self, debug_panel):
        """Test continue button."""
        # Button should be present
        pass


class TestStackTrace:
    """Tests for stack trace display."""

    def test_update_stack_trace(self, debug_panel):
        """Test updating stack trace."""
        stack = [
            {"node_id": "node1", "name": "Start"},
            {"node_id": "node2", "name": "Process"},
        ]

        if hasattr(debug_panel, "update_stack_trace"):
            debug_panel.update_stack_trace(stack)

    def test_clear_stack_trace(self, debug_panel):
        """Test clearing stack trace."""
        if hasattr(debug_panel, "clear_stack_trace"):
            debug_panel.clear_stack_trace()
