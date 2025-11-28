"""
Integration tests for variable nodes.

Tests all 3 variable nodes to ensure proper variable management.
"""

import pytest
from unittest.mock import Mock

# Uses execution_context fixture from conftest.py - no import needed


class TestVariableNodes:
    """Integration tests for variable category nodes."""

    # Uses execution_context fixture from conftest.py

    # =============================================================================
    # SetVariableNode Tests
    # =============================================================================

    @pytest.mark.asyncio
    async def test_set_variable_node_basic(self, execution_context) -> None:
        """Test SetVariableNode stores a value in context."""
        from casare_rpa.nodes.variable_nodes import SetVariableNode

        node = SetVariableNode(node_id="test_set", variable_name="test_var")
        node.set_input_value("value", "Hello, World!")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert execution_context.variables["test_var"] == "Hello, World!"

    @pytest.mark.asyncio
    async def test_set_variable_node_type_conversion(self, execution_context) -> None:
        """Test SetVariableNode with type conversion."""
        from casare_rpa.nodes.variable_nodes import SetVariableNode

        # Test integer conversion
        node = SetVariableNode(node_id="test_set_int", variable_name="count")
        node.config["variable_type"] = "Int32"
        node.set_input_value("value", "42")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert execution_context.variables["count"] == 42
        assert isinstance(execution_context.variables["count"], int)

    @pytest.mark.asyncio
    async def test_set_variable_node_default_value(self, execution_context) -> None:
        """Test SetVariableNode uses default value when no input."""
        from casare_rpa.nodes.variable_nodes import SetVariableNode

        node = SetVariableNode(
            node_id="test_set_default",
            variable_name="status",
            default_value="pending",
        )

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert execution_context.variables["status"] == "pending"

    # =============================================================================
    # GetVariableNode Tests
    # =============================================================================

    @pytest.mark.asyncio
    async def test_get_variable_node_existing(self, execution_context) -> None:
        """Test GetVariableNode retrieves existing variable."""
        from casare_rpa.nodes.variable_nodes import GetVariableNode

        # Set up variable in context
        execution_context.variables["existing_var"] = "test_value"

        node = GetVariableNode(node_id="test_get", variable_name="existing_var")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["value"] == "test_value"

    @pytest.mark.asyncio
    async def test_get_variable_node_missing(self, execution_context) -> None:
        """Test GetVariableNode handles missing variable."""
        from casare_rpa.nodes.variable_nodes import GetVariableNode

        node = GetVariableNode(
            node_id="test_get_missing", variable_name="nonexistent_var"
        )

        result = await node.execute(execution_context)

        # Should succeed but return None or default
        assert result["success"] is True
        assert result["data"]["value"] is None

    @pytest.mark.asyncio
    async def test_get_variable_node_output_port(self, execution_context) -> None:
        """Test GetVariableNode sets output port value."""
        from casare_rpa.nodes.variable_nodes import GetVariableNode

        execution_context.variables["output_test"] = 123

        node = GetVariableNode(node_id="test_get_output", variable_name="output_test")

        result = await node.execute(execution_context)

        assert result["success"] is True
        # Check output port was set
        output_value = node.get_output_value("value")
        assert output_value == 123

    # =============================================================================
    # IncrementNode Tests
    # =============================================================================

    @pytest.mark.asyncio
    async def test_increment_node_basic(self, execution_context) -> None:
        """Test IncrementNode increments counter."""
        from casare_rpa.nodes.variable_nodes import IncrementNode

        # Initialize counter
        execution_context.variables["counter"] = 0

        node = IncrementNode(node_id="test_increment")
        node.config["variable_name"] = "counter"
        node.config["increment_by"] = 1

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert execution_context.variables["counter"] == 1

    @pytest.mark.asyncio
    async def test_increment_node_custom_step(self, execution_context) -> None:
        """Test IncrementNode with custom increment value."""
        from casare_rpa.nodes.variable_nodes import IncrementNode

        execution_context.variables["counter"] = 10

        node = IncrementNode(node_id="test_increment_custom")
        node.config["variable_name"] = "counter"
        node.config["increment_by"] = 5

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert execution_context.variables["counter"] == 15

    @pytest.mark.asyncio
    async def test_increment_node_decrement(self, execution_context) -> None:
        """Test IncrementNode can decrement with negative value."""
        from casare_rpa.nodes.variable_nodes import IncrementNode

        execution_context.variables["counter"] = 10

        node = IncrementNode(node_id="test_decrement")
        node.config["variable_name"] = "counter"
        node.config["increment_by"] = -2

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert execution_context.variables["counter"] == 8


class TestVariableNodesIntegration:
    """Integration tests for variable nodes visual layer."""

    def test_set_variable_visual_integration(self) -> None:
        """Test SetVariableNode logic-to-visual connection."""
        from casare_rpa.nodes.variable_nodes import SetVariableNode
        from casare_rpa.presentation.canvas.visual_nodes.variables import (
            VisualSetVariableNode,
        )

        visual_node = VisualSetVariableNode()
        logic_class = visual_node.get_node_class()
        assert logic_class == SetVariableNode

        node = SetVariableNode(node_id="test_set", variable_name="test")
        assert node.node_type == "SetVariableNode"
        assert hasattr(node, "execute")

    def test_get_variable_visual_integration(self) -> None:
        """Test GetVariableNode logic-to-visual connection."""
        from casare_rpa.nodes.variable_nodes import GetVariableNode
        from casare_rpa.presentation.canvas.visual_nodes.variables import (
            VisualGetVariableNode,
        )

        visual_node = VisualGetVariableNode()
        logic_class = visual_node.get_node_class()
        assert logic_class == GetVariableNode

        node = GetVariableNode(node_id="test_get", variable_name="test")
        assert node.node_type == "GetVariableNode"

    def test_increment_visual_integration(self) -> None:
        """Test IncrementNode logic-to-visual connection."""
        from casare_rpa.nodes.variable_nodes import IncrementNode
        from casare_rpa.presentation.canvas.visual_nodes.variables import (
            VisualIncrementNode,
        )

        visual_node = VisualIncrementNode()
        logic_class = visual_node.get_node_class()
        assert logic_class == IncrementNode

        node = IncrementNode(node_id="test_increment")
        assert node.node_type == "IncrementNode"
