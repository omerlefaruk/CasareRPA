"""
Integration tests for script nodes.

Tests all 5 script nodes to ensure proper logic-to-visual layer connections
and basic functionality.
"""

import pytest
from unittest.mock import Mock

# Uses execution_context fixture from conftest.py - no import needed


class TestScriptNodesIntegration:
    """Integration tests for scripts category nodes."""

    # Uses execution_context fixture from conftest.py

    # =============================================================================
    # Python Script Nodes
    # =============================================================================

    def test_run_python_script_node_integration(self, execution_context) -> None:
        """Test RunPythonScriptNode logic-to-visual connection."""
        from casare_rpa.nodes.script_nodes import RunPythonScriptNode
        from casare_rpa.presentation.canvas.visual_nodes.scripts import (
            VisualRunPythonScriptNode,
        )

        # Test visual node returns correct logic class
        visual_node = VisualRunPythonScriptNode()
        logic_class = visual_node.get_node_class()
        assert logic_class == RunPythonScriptNode

        # Test node instantiation
        node = RunPythonScriptNode(node_id="test_python_script")
        assert node.node_type == "RunPythonScriptNode"
        assert hasattr(node, "execute")

    @pytest.mark.asyncio
    async def test_run_python_script_execution(self, execution_context) -> None:
        """Test RunPythonScriptNode basic execution."""
        from casare_rpa.nodes.script_nodes import RunPythonScriptNode

        node = RunPythonScriptNode(node_id="test_python_script")
        node.set_input_value("code", "result = 2 + 2")
        node.set_input_value("variables", {})

        result = await node.execute(execution_context)
        assert result["success"] is True
        assert node.get_output_value("result") == 4

    def test_run_python_file_node_integration(self, execution_context) -> None:
        """Test RunPythonFileNode logic-to-visual connection."""
        from casare_rpa.nodes.script_nodes import RunPythonFileNode
        from casare_rpa.presentation.canvas.visual_nodes.scripts import (
            VisualRunPythonFileNode,
        )

        visual_node = VisualRunPythonFileNode()
        logic_class = visual_node.get_node_class()
        assert logic_class == RunPythonFileNode

        node = RunPythonFileNode(node_id="test_python_file", config={"timeout": 300})
        assert node.node_type == "RunPythonFileNode"

    # =============================================================================
    # Expression Eval Node
    # =============================================================================

    def test_eval_expression_node_integration(self, execution_context) -> None:
        """Test EvalExpressionNode logic-to-visual connection."""
        from casare_rpa.nodes.script_nodes import EvalExpressionNode
        from casare_rpa.presentation.canvas.visual_nodes.scripts import (
            VisualEvalExpressionNode,
        )

        visual_node = VisualEvalExpressionNode()
        logic_class = visual_node.get_node_class()
        assert logic_class == EvalExpressionNode

        node = EvalExpressionNode(node_id="test_eval_expression")
        assert node.node_type == "EvalExpressionNode"

    @pytest.mark.asyncio
    async def test_eval_expression_execution(self, execution_context) -> None:
        """Test EvalExpressionNode basic execution."""
        from casare_rpa.nodes.script_nodes import EvalExpressionNode

        node = EvalExpressionNode(node_id="test_eval")
        node.set_input_value("expression", "5 * 10")
        node.set_input_value("variables", {})

        result = await node.execute(execution_context)
        assert result["success"] is True
        assert node.get_output_value("result") == 50
        assert node.get_output_value("type") == "int"

    # =============================================================================
    # Batch Script Node
    # =============================================================================

    def test_run_batch_script_node_integration(self, execution_context) -> None:
        """Test RunBatchScriptNode logic-to-visual connection."""
        from casare_rpa.nodes.script_nodes import RunBatchScriptNode
        from casare_rpa.presentation.canvas.visual_nodes.scripts import (
            VisualRunBatchScriptNode,
        )

        visual_node = VisualRunBatchScriptNode()
        logic_class = visual_node.get_node_class()
        assert logic_class == RunBatchScriptNode

        node = RunBatchScriptNode(node_id="test_batch_script", config={"timeout": 300})
        assert node.node_type == "RunBatchScriptNode"

    @pytest.mark.asyncio
    async def test_run_batch_script_execution(self, execution_context) -> None:
        """Test RunBatchScriptNode basic execution."""
        from casare_rpa.nodes.script_nodes import RunBatchScriptNode

        node = RunBatchScriptNode(node_id="test_batch", config={"timeout": 5})
        node.set_input_value("script", "echo test")

        result = await node.execute(execution_context)
        assert result["success"] is True
        assert "test" in node.get_output_value("stdout")

    # =============================================================================
    # JavaScript Node
    # =============================================================================

    def test_run_javascript_node_integration(self, execution_context) -> None:
        """Test RunJavaScriptNode logic-to-visual connection."""
        from casare_rpa.nodes.script_nodes import RunJavaScriptNode
        from casare_rpa.presentation.canvas.visual_nodes.scripts import (
            VisualRunJavaScriptNode,
        )

        visual_node = VisualRunJavaScriptNode()
        logic_class = visual_node.get_node_class()
        assert logic_class == RunJavaScriptNode

        node = RunJavaScriptNode(node_id="test_javascript")
        assert node.node_type == "RunJavaScriptNode"

    @pytest.mark.asyncio
    async def test_run_javascript_execution(self, execution_context) -> None:
        """Test RunJavaScriptNode basic execution."""
        from casare_rpa.nodes.script_nodes import RunJavaScriptNode

        node = RunJavaScriptNode(node_id="test_js")
        node.set_input_value("code", "2 + 2")
        node.set_input_value("variables", {})

        result = await node.execute(execution_context)
        assert result["success"] is True
        # JavaScript execution returns the evaluated expression
        assert node.get_output_value("result") == 4

    # =============================================================================
    # Port Configuration Tests
    # =============================================================================

    def test_all_visual_nodes_have_proper_ports(self) -> None:
        """Test that all script visual nodes have setup_ports method."""
        from casare_rpa.presentation.canvas.visual_nodes.scripts import (
            VisualRunPythonScriptNode,
            VisualRunPythonFileNode,
            VisualEvalExpressionNode,
            VisualRunBatchScriptNode,
            VisualRunJavaScriptNode,
        )

        visual_nodes = [
            VisualRunPythonScriptNode(),
            VisualRunPythonFileNode(),
            VisualEvalExpressionNode(),
            VisualRunBatchScriptNode(),
            VisualRunJavaScriptNode(),
        ]

        for visual_node in visual_nodes:
            assert hasattr(
                visual_node, "setup_ports"
            ), f"{visual_node.__class__.__name__} missing setup_ports method"
            assert hasattr(
                visual_node, "get_node_class"
            ), f"{visual_node.__class__.__name__} missing get_node_class method"

    def test_all_visual_nodes_have_correct_category(self) -> None:
        """Test that all script visual nodes have correct NODE_CATEGORY."""
        from casare_rpa.presentation.canvas.visual_nodes.scripts import (
            VisualRunPythonScriptNode,
            VisualRunPythonFileNode,
            VisualEvalExpressionNode,
            VisualRunBatchScriptNode,
            VisualRunJavaScriptNode,
        )

        visual_nodes = [
            VisualRunPythonScriptNode(),
            VisualRunPythonFileNode(),
            VisualEvalExpressionNode(),
            VisualRunBatchScriptNode(),
            VisualRunJavaScriptNode(),
        ]

        for visual_node in visual_nodes:
            assert (
                visual_node.NODE_CATEGORY == "scripts"
            ), f"{visual_node.__class__.__name__} has wrong NODE_CATEGORY"


class TestScriptNodesNodeRegistry:
    """Test that all script nodes are properly registered."""

    def test_all_script_nodes_in_registry(self) -> None:
        """Test that all 5 script nodes are in the node registry."""
        from casare_rpa.nodes import _NODE_REGISTRY

        script_nodes = [
            "RunPythonScriptNode",
            "RunPythonFileNode",
            "EvalExpressionNode",
            "RunBatchScriptNode",
            "RunJavaScriptNode",
        ]

        for node_name in script_nodes:
            assert node_name in _NODE_REGISTRY, f"{node_name} not in node registry"
            assert (
                _NODE_REGISTRY[node_name] == "script_nodes"
            ), f"{node_name} registered to wrong module"

    def test_can_instantiate_all_script_nodes_from_registry(self) -> None:
        """Test that all script nodes can be instantiated via registry."""
        from casare_rpa.nodes import get_node_class

        script_nodes = [
            "RunPythonScriptNode",
            "RunPythonFileNode",
            "EvalExpressionNode",
            "RunBatchScriptNode",
            "RunJavaScriptNode",
        ]

        for node_name in script_nodes:
            node_class = get_node_class(node_name)
            assert node_class is not None, f"Could not get class for {node_name}"

            # Test instantiation
            node = node_class(node_id=f"test_{node_name.lower()}")
            assert node.node_type == node_name
            assert hasattr(node, "execute")
