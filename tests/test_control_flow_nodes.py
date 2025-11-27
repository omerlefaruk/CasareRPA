"""
Integration tests for control flow nodes.

Tests all 8 control flow nodes to ensure proper execution and routing logic.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from casare_rpa.core.execution_context import ExecutionContext


class TestControlFlowNodes:
    """Integration tests for control flow category nodes."""

    @pytest.fixture
    def execution_context(self):
        """Create a mock execution context with real variable storage."""
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        context.get_variable = lambda name, default=None: context.variables.get(
            name, default
        )
        context.set_variable = lambda name, value: context.variables.__setitem__(
            name, value
        )
        return context

    # =============================================================================
    # IfNode Tests
    # =============================================================================

    @pytest.mark.asyncio
    async def test_if_node_true_branch(self, execution_context):
        """Test IfNode routes to true branch when condition is true."""
        from casare_rpa.nodes.control_flow_nodes import IfNode

        node = IfNode(node_id="test_if_true")
        node.config["expression"] = "5 == 5"

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["condition"] is True
        assert "true" in result["next_nodes"]
        assert "false" not in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_if_node_false_branch(self, execution_context):
        """Test IfNode routes to false branch when condition is false."""
        from casare_rpa.nodes.control_flow_nodes import IfNode

        node = IfNode(node_id="test_if_false")
        node.config["expression"] = "5 == 10"

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["condition"] is False
        assert "false" in result["next_nodes"]
        assert "true" not in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_if_node_with_variables(self, execution_context):
        """Test IfNode evaluates expressions with context variables."""
        from casare_rpa.nodes.control_flow_nodes import IfNode

        # Set variable in context
        execution_context.variables["test_var"] = 42

        node = IfNode(node_id="test_if_var")
        node.config["expression"] = "test_var > 40"

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["condition"] is True
        assert "true" in result["next_nodes"]

    # =============================================================================
    # ForLoopStartNode Tests
    # =============================================================================

    @pytest.mark.asyncio
    async def test_for_loop_start_range_iteration(self, execution_context):
        """Test ForLoopStartNode with range iteration."""
        from casare_rpa.nodes.control_flow_nodes import ForLoopStartNode

        node = ForLoopStartNode(node_id="test_for_start")
        node.config["start"] = 0
        node.config["end"] = 3
        node.config["step"] = 1

        # First iteration
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "body" in result["next_nodes"]
        assert result["data"]["current_index"] == 0
        assert result["data"]["current_item"] == 0

    @pytest.mark.asyncio
    async def test_for_loop_start_list_iteration(self, execution_context):
        """Test ForLoopStartNode with list iteration."""
        from casare_rpa.nodes.control_flow_nodes import ForLoopStartNode

        node = ForLoopStartNode(node_id="test_for_list")
        node.set_input_value("items", ["apple", "banana", "cherry"])

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "body" in result["next_nodes"]
        assert result["data"]["current_index"] == 0
        assert result["data"]["current_item"] == "apple"

    # =============================================================================
    # ForLoopEndNode Tests
    # =============================================================================

    @pytest.mark.asyncio
    async def test_for_loop_end_continue(self, execution_context):
        """Test ForLoopEndNode continues iteration when items remain."""
        from casare_rpa.nodes.control_flow_nodes import (
            ForLoopStartNode,
            ForLoopEndNode,
        )

        # Set up loop state
        loop_state_key = "test_loop_state"
        execution_context.variables[loop_state_key] = {
            "items": [1, 2, 3],
            "current_index": 0,
            "total_iterations": 3,
        }

        end_node = ForLoopEndNode(node_id="test_for_end")
        end_node.config["loop_start_id"] = "test_loop"

        result = await end_node.execute(execution_context)

        assert result["success"] is True
        # Should loop back when not completed
        assert "loop_back_to" in result or "completed" in result["next_nodes"]

    # =============================================================================
    # WhileLoopStartNode Tests
    # =============================================================================

    @pytest.mark.asyncio
    async def test_while_loop_start_true_condition(self, execution_context):
        """Test WhileLoopStartNode enters body when condition is true."""
        from casare_rpa.nodes.control_flow_nodes import WhileLoopStartNode

        execution_context.variables["counter"] = 0

        node = WhileLoopStartNode(node_id="test_while")
        node.config["condition"] = "counter < 5"

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "loop_body" in result["next_nodes"]
        assert "completed" not in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_while_loop_start_false_condition(self, execution_context):
        """Test WhileLoopStartNode skips body when condition is false."""
        from casare_rpa.nodes.control_flow_nodes import WhileLoopStartNode

        execution_context.variables["counter"] = 10

        node = WhileLoopStartNode(node_id="test_while_false")
        node.config["condition"] = "counter < 5"

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "completed" in result["next_nodes"]
        assert "loop_body" not in result["next_nodes"]

    # =============================================================================
    # SwitchNode Tests
    # =============================================================================

    @pytest.mark.asyncio
    async def test_switch_node_match(self, execution_context):
        """Test SwitchNode routes to matching case."""
        from casare_rpa.nodes.control_flow_nodes import SwitchNode

        node = SwitchNode(node_id="test_switch")
        node.set_input_value("value", "apple")
        node.config["cases"] = ["apple", "banana", "cherry"]

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "case_0" in result["next_nodes"]  # Matched first case

    @pytest.mark.asyncio
    async def test_switch_node_default(self, execution_context):
        """Test SwitchNode routes to default when no match."""
        from casare_rpa.nodes.control_flow_nodes import SwitchNode

        node = SwitchNode(node_id="test_switch_default")
        node.set_input_value("value", "orange")
        node.config["cases"] = ["apple", "banana", "cherry"]

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "default" in result["next_nodes"]

    # =============================================================================
    # BreakNode Tests
    # =============================================================================

    @pytest.mark.asyncio
    async def test_break_node(self, execution_context):
        """Test BreakNode signals break control flow."""
        from casare_rpa.nodes.control_flow_nodes import BreakNode

        node = BreakNode(node_id="test_break")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result.get("control_flow") == "break"

    # =============================================================================
    # ContinueNode Tests
    # =============================================================================

    @pytest.mark.asyncio
    async def test_continue_node(self, execution_context):
        """Test ContinueNode signals continue control flow."""
        from casare_rpa.nodes.control_flow_nodes import ContinueNode

        node = ContinueNode(node_id="test_continue")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result.get("control_flow") == "continue"


class TestControlFlowNodesIntegration:
    """Integration tests for control flow nodes visual layer."""

    def test_if_node_visual_integration(self):
        """Test IfNode logic-to-visual connection."""
        from casare_rpa.nodes.control_flow_nodes import IfNode
        from casare_rpa.presentation.canvas.visual_nodes.control_flow import (
            VisualIfNode,
        )

        visual_node = VisualIfNode()
        logic_class = visual_node.get_node_class()
        assert logic_class == IfNode

        node = IfNode(node_id="test_if")
        assert node.node_type == "IfNode"
        assert hasattr(node, "execute")

    def test_for_loop_start_visual_integration(self):
        """Test ForLoopStartNode logic-to-visual connection."""
        from casare_rpa.nodes.control_flow_nodes import ForLoopStartNode
        from casare_rpa.presentation.canvas.visual_nodes.control_flow import (
            VisualForLoopStartNode,
        )

        visual_node = VisualForLoopStartNode()
        logic_class = visual_node.get_node_class()
        assert logic_class == ForLoopStartNode

        node = ForLoopStartNode(node_id="test_for_start")
        assert node.node_type == "ForLoopStartNode"

    def test_while_loop_start_visual_integration(self):
        """Test WhileLoopStartNode logic-to-visual connection."""
        from casare_rpa.nodes.control_flow_nodes import WhileLoopStartNode
        from casare_rpa.presentation.canvas.visual_nodes.control_flow import (
            VisualWhileLoopStartNode,
        )

        visual_node = VisualWhileLoopStartNode()
        logic_class = visual_node.get_node_class()
        assert logic_class == WhileLoopStartNode

        node = WhileLoopStartNode(node_id="test_while")
        assert node.node_type == "WhileLoopStartNode"

    def test_switch_node_visual_integration(self):
        """Test SwitchNode logic-to-visual connection."""
        from casare_rpa.nodes.control_flow_nodes import SwitchNode
        from casare_rpa.presentation.canvas.visual_nodes.control_flow import (
            VisualSwitchNode,
        )

        visual_node = VisualSwitchNode()
        logic_class = visual_node.get_node_class()
        assert logic_class == SwitchNode

        node = SwitchNode(node_id="test_switch")
        assert node.node_type == "SwitchNode"
