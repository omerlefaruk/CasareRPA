"""
Phase 6: Advanced Workflow Features Tests

Tests for:
1. Control Flow Nodes (If, For, While, Switch, Break, Continue)
2. Error Handling Nodes (Try/Catch, Retry, Throw)
3. Debugging Tools (Debug toolbar, Variable Inspector, Execution History)
4. Template System (Template loader, categories)
5. Data Operations Nodes (String, Math, List, JSON)
6. UI/UX Enhancements (Minimap, Node Search)
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch
from pathlib import Path

# Mark for GUI tests that require Qt
requires_qt = pytest.mark.skipif(
    not pytest.importorskip("PySide6", reason="PySide6 required for GUI tests"),
    reason="PySide6 not available"
)


class TestControlFlowNodes:
    """Tests for control flow nodes."""

    def test_if_node_creation(self):
        """Test IfNode instantiation."""
        from casare_rpa.nodes import IfNode

        node = IfNode("if_1")

        assert node.node_id == "if_1"
        assert node.name == "If"
        assert "condition" in node.input_ports
        assert "true" in node.output_ports
        assert "false" in node.output_ports

    @pytest.mark.asyncio
    async def test_if_node_true_condition(self):
        """Test IfNode with true condition."""
        from casare_rpa.nodes import IfNode
        from casare_rpa.core.execution_context import ExecutionContext

        context = ExecutionContext(workflow_name="test")
        node = IfNode("if_1")
        node.set_input_value("condition", True)

        result = await node.execute(context)

        assert result["success"] is True
        assert "true" in result.get("next_nodes", [])

    @pytest.mark.asyncio
    async def test_if_node_false_condition(self):
        """Test IfNode with false condition."""
        from casare_rpa.nodes import IfNode
        from casare_rpa.core.execution_context import ExecutionContext

        context = ExecutionContext(workflow_name="test")
        node = IfNode("if_1")
        node.set_input_value("condition", False)

        result = await node.execute(context)

        assert result["success"] is True
        assert "false" in result.get("next_nodes", [])

    @pytest.mark.asyncio
    async def test_if_node_expression_evaluation(self):
        """Test IfNode with expression from config."""
        from casare_rpa.nodes import IfNode
        from casare_rpa.core.execution_context import ExecutionContext

        context = ExecutionContext(workflow_name="test")
        context.set_variable("x", 10)

        node = IfNode("if_1", config={"expression": "x > 5"})

        result = await node.execute(context)

        assert result["success"] is True
        assert "true" in result.get("next_nodes", [])

    def test_for_loop_node_creation(self):
        """Test ForLoopNode instantiation."""
        from casare_rpa.nodes import ForLoopNode

        node = ForLoopNode("for_1")

        assert node.node_id == "for_1"
        assert "items" in node.input_ports
        assert "loop_body" in node.output_ports

    @pytest.mark.asyncio
    async def test_for_loop_iteration(self):
        """Test ForLoopNode iterates over items."""
        from casare_rpa.nodes import ForLoopNode
        from casare_rpa.core.execution_context import ExecutionContext

        context = ExecutionContext(workflow_name="test")
        node = ForLoopNode("for_1")
        node.set_input_value("items", [1, 2, 3])

        result = await node.execute(context)

        assert result["success"] is True
        assert "loop_body" in result.get("next_nodes", [])

    def test_while_loop_node_creation(self):
        """Test WhileLoopNode instantiation."""
        from casare_rpa.nodes import WhileLoopNode

        node = WhileLoopNode("while_1")

        assert node.node_id == "while_1"
        assert "condition" in node.input_ports

    def test_switch_node_creation(self):
        """Test SwitchNode instantiation."""
        from casare_rpa.nodes import SwitchNode

        node = SwitchNode("switch_1")

        assert node.node_id == "switch_1"
        assert "value" in node.input_ports

    def test_break_node_creation(self):
        """Test BreakNode instantiation."""
        from casare_rpa.nodes import BreakNode

        node = BreakNode("break_1")

        assert node.node_id == "break_1"

    @pytest.mark.asyncio
    async def test_break_node_signals_break(self):
        """Test BreakNode signals loop break."""
        from casare_rpa.nodes import BreakNode
        from casare_rpa.core.execution_context import ExecutionContext

        context = ExecutionContext(workflow_name="test")
        node = BreakNode("break_1")

        result = await node.execute(context)

        assert result["success"] is True
        # Break should set a flag or return break signal
        assert result.get("data", {}).get("break") is True or "break" in str(result)

    def test_continue_node_creation(self):
        """Test ContinueNode instantiation."""
        from casare_rpa.nodes import ContinueNode

        node = ContinueNode("continue_1")

        assert node.node_id == "continue_1"

    @pytest.mark.asyncio
    async def test_continue_node_signals_continue(self):
        """Test ContinueNode signals loop continue."""
        from casare_rpa.nodes import ContinueNode
        from casare_rpa.core.execution_context import ExecutionContext

        context = ExecutionContext(workflow_name="test")
        node = ContinueNode("continue_1")

        result = await node.execute(context)

        assert result["success"] is True
        # Continue should set a flag or return continue signal
        assert result.get("data", {}).get("continue") is True or "continue" in str(result)


class TestErrorHandlingNodes:
    """Tests for error handling nodes."""

    def test_try_node_creation(self):
        """Test TryNode instantiation."""
        from casare_rpa.nodes import TryNode

        node = TryNode("try_1")

        assert node.node_id == "try_1"
        assert "try_body" in node.output_ports
        assert "success" in node.output_ports
        assert "catch" in node.output_ports

    @pytest.mark.asyncio
    async def test_try_node_enters_try_block(self):
        """Test TryNode enters try block on first execution."""
        from casare_rpa.nodes import TryNode
        from casare_rpa.core.execution_context import ExecutionContext

        context = ExecutionContext(workflow_name="test")
        node = TryNode("try_1")

        result = await node.execute(context)

        assert result["success"] is True
        assert "try_body" in result.get("next_nodes", [])

    def test_retry_node_creation(self):
        """Test RetryNode instantiation."""
        from casare_rpa.nodes import RetryNode

        node = RetryNode("retry_1")

        assert node.node_id == "retry_1"

    def test_throw_error_node_creation(self):
        """Test ThrowErrorNode instantiation."""
        from casare_rpa.nodes import ThrowErrorNode

        node = ThrowErrorNode("throw_1")

        assert node.node_id == "throw_1"
        assert "error_message" in node.input_ports

    @pytest.mark.asyncio
    async def test_throw_error_raises(self):
        """Test ThrowErrorNode throws an error."""
        from casare_rpa.nodes import ThrowErrorNode
        from casare_rpa.core.execution_context import ExecutionContext

        context = ExecutionContext(workflow_name="test")
        node = ThrowErrorNode("throw_1")
        node.set_input_value("error_message", "Custom error")

        result = await node.execute(context)

        # ThrowErrorNode should fail and report error
        assert result["success"] is False
        assert "error" in result or "Custom error" in str(result)


@pytest.mark.skipif(True, reason="GUI tests require display - skipped in CI")
class TestDebugToolbar:
    """Tests for debug toolbar functionality."""

    def test_debug_toolbar_creation(self, qtbot):
        """Test DebugToolbar instantiation."""
        from casare_rpa.canvas.debug_toolbar import DebugToolbar

        toolbar = DebugToolbar()
        qtbot.addWidget(toolbar)

        assert toolbar is not None
        assert toolbar.objectName() == "DebugToolbar"

    def test_debug_toolbar_has_debug_mode_action(self, qtbot):
        """Test DebugToolbar has debug mode action."""
        from casare_rpa.canvas.debug_toolbar import DebugToolbar

        toolbar = DebugToolbar()
        qtbot.addWidget(toolbar)

        assert hasattr(toolbar, "action_debug_mode")
        assert toolbar.action_debug_mode.isCheckable()

    def test_debug_toolbar_has_step_mode_action(self, qtbot):
        """Test DebugToolbar has step mode action."""
        from casare_rpa.canvas.debug_toolbar import DebugToolbar

        toolbar = DebugToolbar()
        qtbot.addWidget(toolbar)

        assert hasattr(toolbar, "action_step_mode")
        assert toolbar.action_step_mode.isCheckable()

    def test_debug_toolbar_signals_defined(self, qtbot):
        """Test DebugToolbar has required signals."""
        from casare_rpa.canvas.debug_toolbar import DebugToolbar

        toolbar = DebugToolbar()
        qtbot.addWidget(toolbar)

        # Check signals exist
        assert hasattr(toolbar, "debug_mode_toggled")
        assert hasattr(toolbar, "step_mode_toggled")
        assert hasattr(toolbar, "step_requested")
        assert hasattr(toolbar, "continue_requested")
        assert hasattr(toolbar, "stop_requested")


@pytest.mark.skipif(True, reason="GUI tests require display - skipped in CI")
class TestVariableInspector:
    """Tests for variable inspector panel."""

    def test_variable_inspector_creation(self, qtbot):
        """Test VariableInspectorPanel instantiation."""
        from casare_rpa.canvas.variable_inspector import VariableInspectorPanel

        panel = VariableInspectorPanel()
        qtbot.addWidget(panel)

        assert panel is not None
        assert panel.objectName() == "VariableInspectorPanel"

    def test_variable_inspector_has_table(self, qtbot):
        """Test VariableInspectorPanel has variable table."""
        from casare_rpa.canvas.variable_inspector import VariableInspectorPanel

        panel = VariableInspectorPanel()
        qtbot.addWidget(panel)

        assert hasattr(panel, "table")
        assert panel.table.columnCount() == 2  # Name, Value

    def test_variable_inspector_update_variables(self, qtbot):
        """Test updating variables in inspector."""
        from casare_rpa.canvas.variable_inspector import VariableInspectorPanel

        panel = VariableInspectorPanel()
        qtbot.addWidget(panel)

        variables = {"var1": "value1", "var2": 42, "var3": [1, 2, 3]}
        panel.update_variables(variables)

        assert panel.table.rowCount() == 3

    def test_variable_inspector_clear(self, qtbot):
        """Test clearing variables from inspector."""
        from casare_rpa.canvas.variable_inspector import VariableInspectorPanel

        panel = VariableInspectorPanel()
        qtbot.addWidget(panel)

        panel.update_variables({"var1": "value1"})
        panel.clear_variables()

        assert panel.table.rowCount() == 0


@pytest.mark.skipif(True, reason="GUI tests require display - skipped in CI")
class TestMinimap:
    """Tests for minimap widget."""

    def test_minimap_view_creation(self, qtbot):
        """Test MinimapView instantiation."""
        from casare_rpa.canvas.minimap import MinimapView

        view = MinimapView()
        qtbot.addWidget(view)

        assert view is not None

    def test_minimap_widget_creation(self, qtbot):
        """Test MinimapWidget instantiation."""
        from casare_rpa.canvas.minimap import MinimapWidget

        widget = MinimapWidget()
        qtbot.addWidget(widget)

        assert widget is not None

    def test_minimap_has_viewport_clicked_signal(self, qtbot):
        """Test MinimapView has viewport_clicked signal."""
        from casare_rpa.canvas.minimap import MinimapView

        view = MinimapView()
        qtbot.addWidget(view)

        assert hasattr(view, "viewport_clicked")


class TestTemplateLoader:
    """Tests for template loader system."""

    def test_template_loader_creation(self):
        """Test TemplateLoader instantiation."""
        from casare_rpa.utils.template_loader import TemplateLoader

        loader = TemplateLoader()

        assert loader is not None
        assert loader.templates_dir is not None

    def test_template_info_dataclass(self):
        """Test TemplateInfo dataclass."""
        from casare_rpa.utils.template_loader import TemplateInfo

        info = TemplateInfo(
            name="Test Template",
            category="basic",
            description="A test template",
            file_path=Path("/test/path.py"),
            tags=["test", "demo"],
        )

        assert info.name == "Test Template"
        assert info.category == "basic"
        assert info.description == "A test template"
        assert "test" in info.tags

    def test_template_loader_discover(self):
        """Test template discovery."""
        from casare_rpa.utils.template_loader import TemplateLoader

        loader = TemplateLoader()
        templates = loader.discover_templates()

        # Should return a dict (even if empty when no templates dir)
        assert isinstance(templates, dict)

    def test_template_loader_get_categories(self):
        """Test getting template categories."""
        from casare_rpa.utils.template_loader import TemplateLoader

        loader = TemplateLoader()
        loader.discover_templates()

        categories = loader.get_categories()

        assert isinstance(categories, list)


class TestDataOperationNodes:
    """Tests for data operation nodes."""

    def test_concatenate_node_exists(self):
        """Test ConcatenateNode exists and is importable."""
        from casare_rpa.nodes import ConcatenateNode

        node = ConcatenateNode("concat_1")
        assert node.node_id == "concat_1"

    @pytest.mark.asyncio
    async def test_concatenate_strings(self):
        """Test ConcatenateNode joins strings."""
        from casare_rpa.nodes import ConcatenateNode

        node = ConcatenateNode("concat_1")
        node.set_input_value("string_1", "Hello")
        node.set_input_value("string_2", " World")

        result = await node.execute(None)

        assert result["success"] is True
        assert result.get("data", {}).get("result") == "Hello World"

    def test_math_operation_node_exists(self):
        """Test MathOperationNode exists."""
        from casare_rpa.nodes import MathOperationNode

        node = MathOperationNode("math_1")
        assert node.node_id == "math_1"

    @pytest.mark.asyncio
    async def test_math_subtraction(self):
        """Test MathOperationNode subtraction."""
        from casare_rpa.nodes import MathOperationNode

        node = MathOperationNode("math_1", config={"operation": "subtract"})
        node.set_input_value("a", 10)
        node.set_input_value("b", 3)

        result = await node.execute(None)

        assert result["success"] is True
        assert result.get("data", {}).get("result") == 7.0

    @pytest.mark.asyncio
    async def test_math_division(self):
        """Test MathOperationNode division."""
        from casare_rpa.nodes import MathOperationNode

        node = MathOperationNode("math_1", config={"operation": "divide"})
        node.set_input_value("a", 20)
        node.set_input_value("b", 4)

        result = await node.execute(None)

        assert result["success"] is True
        assert result.get("data", {}).get("result") == 5.0

    def test_comparison_node_exists(self):
        """Test ComparisonNode exists."""
        from casare_rpa.nodes import ComparisonNode

        node = ComparisonNode("compare_1")
        assert node.node_id == "compare_1"

    @pytest.mark.asyncio
    async def test_comparison_less_than(self):
        """Test ComparisonNode less than."""
        from casare_rpa.nodes import ComparisonNode

        node = ComparisonNode("compare_1", config={"operator": "<"})
        node.set_input_value("a", 3)
        node.set_input_value("b", 5)

        result = await node.execute(None)

        assert result["success"] is True
        assert result.get("data", {}).get("result") is True

    @pytest.mark.asyncio
    async def test_comparison_not_equal(self):
        """Test ComparisonNode not equal."""
        from casare_rpa.nodes import ComparisonNode

        node = ComparisonNode("compare_1", config={"operator": "!="})
        node.set_input_value("a", 5)
        node.set_input_value("b", 10)

        result = await node.execute(None)

        assert result["success"] is True
        assert result.get("data", {}).get("result") is True

    def test_regex_match_node_exists(self):
        """Test RegexMatchNode exists."""
        from casare_rpa.nodes import RegexMatchNode

        node = RegexMatchNode("regex_1")
        assert node.node_id == "regex_1"

    @pytest.mark.asyncio
    async def test_regex_match_finds_pattern(self):
        """Test RegexMatchNode finds pattern."""
        from casare_rpa.nodes import RegexMatchNode

        node = RegexMatchNode("regex_1")
        node.set_input_value("text", "Contact: user@example.com")
        node.set_input_value("pattern", r"[\w.-]+@[\w.-]+\.\w+")

        result = await node.execute(None)

        assert result["success"] is True
        data = result.get("data", {})
        assert data.get("match_found") is True

    def test_format_string_node_exists(self):
        """Test FormatStringNode exists."""
        from casare_rpa.nodes import FormatStringNode

        node = FormatStringNode("format_1")
        assert node.node_id == "format_1"


@pytest.mark.skipif(True, reason="GUI tests require display - skipped in CI")
class TestExecutionHistory:
    """Tests for execution history viewer."""

    def test_execution_history_viewer_creation(self, qtbot):
        """Test ExecutionHistoryViewer instantiation."""
        from casare_rpa.canvas.execution_history_viewer import ExecutionHistoryViewer

        viewer = ExecutionHistoryViewer()
        qtbot.addWidget(viewer)

        assert viewer is not None

    def test_execution_history_has_table(self, qtbot):
        """Test ExecutionHistoryViewer has history table."""
        from casare_rpa.canvas.execution_history_viewer import ExecutionHistoryViewer

        viewer = ExecutionHistoryViewer()
        qtbot.addWidget(viewer)

        assert hasattr(viewer, "table")

    def test_execution_history_add_entry(self, qtbot):
        """Test adding entry to execution history."""
        from casare_rpa.canvas.execution_history_viewer import ExecutionHistoryViewer

        viewer = ExecutionHistoryViewer()
        qtbot.addWidget(viewer)

        viewer.add_entry("node_1", "completed", "2025-01-01T12:00:00")

        assert viewer.table.rowCount() >= 1

    def test_execution_history_clear(self, qtbot):
        """Test clearing execution history."""
        from casare_rpa.canvas.execution_history_viewer import ExecutionHistoryViewer

        viewer = ExecutionHistoryViewer()
        qtbot.addWidget(viewer)

        viewer.add_entry("node_1", "completed", "2025-01-01T12:00:00")
        viewer.clear_history()

        assert viewer.table.rowCount() == 0


@pytest.mark.skipif(True, reason="GUI tests require display - skipped in CI")
class TestNodeSearch:
    """Tests for node search functionality."""

    def test_node_search_dialog_creation(self, qtbot):
        """Test NodeSearchDialog instantiation."""
        from casare_rpa.canvas.node_search_dialog import NodeSearchDialog

        dialog = NodeSearchDialog()
        qtbot.addWidget(dialog)

        assert dialog is not None


class TestFuzzySearch:
    """Tests for fuzzy search utility."""

    def test_fuzzy_match_exists(self):
        """Test fuzzy_match utility function exists."""
        from casare_rpa.utils.fuzzy_search import fuzzy_match

        matched, score, positions = fuzzy_match("test", "testing")

        assert matched is True
        assert isinstance(score, int)
        assert isinstance(positions, list)

    def test_fuzzy_match_exact(self):
        """Test fuzzy_match with exact substring."""
        from casare_rpa.utils.fuzzy_search import fuzzy_match

        matched, score, positions = fuzzy_match("test", "test")

        assert matched is True
        assert len(positions) == 4  # Matches all 4 chars

    def test_fuzzy_search_with_items(self):
        """Test fuzzy_search with proper item format."""
        from casare_rpa.utils.fuzzy_search import fuzzy_search

        # Items are (category, name, description) tuples
        items = [
            ("Basic", "SetVariable", "Set a variable value"),
            ("Basic", "GetVariable", "Get a variable value"),
            ("Control", "Reset", "Reset workflow"),
        ]

        results = fuzzy_search("set", items)

        assert isinstance(results, list)
        # Should find matches
        assert len(results) > 0

    def test_fuzzy_search_returns_tuples(self):
        """Test fuzzy_search returns proper result format."""
        from casare_rpa.utils.fuzzy_search import fuzzy_search

        items = [("Basic", "StartNode", "Start workflow")]
        results = fuzzy_search("start", items)

        assert len(results) == 1
        # Result should be (category, name, description, score, positions)
        assert len(results[0]) == 5


class TestAutoConnect:
    """Tests for auto-connect feature."""

    def test_auto_connect_module_exists(self):
        """Test auto_connect module exists."""
        from casare_rpa.canvas import auto_connect

        assert auto_connect is not None


@pytest.mark.skipif(True, reason="GUI tests require display - skipped in CI")
class TestNodeRegistry:
    """Tests for node registry."""

    def test_node_registry_exists(self, qtbot):
        """Test node registry module exists."""
        from casare_rpa.canvas.node_registry import NodeRegistry

        registry = NodeRegistry()

        assert registry is not None

    def test_node_registry_get_categories(self, qtbot):
        """Test getting node categories."""
        from casare_rpa.canvas.node_registry import NodeRegistry

        registry = NodeRegistry()
        categories = registry.get_categories()

        assert isinstance(categories, list)
        # Should have multiple categories
        assert len(categories) > 0
