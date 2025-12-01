"""
Tests for Variable operation nodes.

Tests 3 variable nodes (16 tests total):
- SetVariableNode: store values in execution context (6 tests)
- GetVariableNode: retrieve values from execution context (5 tests)
- IncrementVariableNode: increment numeric variables (5 tests)
"""

import pytest
from unittest.mock import Mock
from casare_rpa.domain.value_objects.types import NodeStatus

# Note: execution_context fixture is provided by tests/conftest.py


class TestSetVariableNode:
    """Tests for SetVariableNode - storing values in context."""

    @pytest.mark.asyncio
    async def test_set_variable_basic(self, execution_context) -> None:
        """Test setting a basic string variable."""
        from casare_rpa.nodes.variable_nodes import SetVariableNode

        node = SetVariableNode(node_id="set_1", variable_name="my_var")
        node.set_input_value("value", "test_value")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["variable_name"] == "my_var"
        assert result["data"]["value"] == "test_value"
        assert execution_context.variables["my_var"] == "test_value"
        assert node.get_output_value("value") == "test_value"
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_set_variable_from_input_port(self, execution_context) -> None:
        """Test setting variable name from input port."""
        from casare_rpa.nodes.variable_nodes import SetVariableNode

        node = SetVariableNode(node_id="set_2")
        node.set_input_value("variable_name", "dynamic_var")
        node.set_input_value("value", 42)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert execution_context.variables["dynamic_var"] == 42

    @pytest.mark.asyncio
    async def test_set_variable_with_default_value(self, execution_context) -> None:
        """Test using default value when no input provided."""
        from casare_rpa.nodes.variable_nodes import SetVariableNode

        node = SetVariableNode(
            node_id="set_3", variable_name="default_var", default_value="default"
        )
        # Don't set input value - should use default

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert execution_context.variables["default_var"] == "default"

    @pytest.mark.asyncio
    async def test_set_variable_type_coercion_boolean(self, execution_context) -> None:
        """Test type coercion to boolean."""
        from casare_rpa.nodes.variable_nodes import SetVariableNode

        node = SetVariableNode(
            node_id="set_4",
            variable_name="bool_var",
            config={"variable_name": "bool_var", "variable_type": "Boolean"},
        )
        node.set_input_value("value", "true")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert execution_context.variables["bool_var"] is True

    @pytest.mark.asyncio
    async def test_set_variable_type_coercion_int(self, execution_context) -> None:
        """Test type coercion to integer."""
        from casare_rpa.nodes.variable_nodes import SetVariableNode

        node = SetVariableNode(
            node_id="set_5",
            variable_name="int_var",
            config={"variable_name": "int_var", "variable_type": "Int32"},
        )
        node.set_input_value("value", "42")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert execution_context.variables["int_var"] == 42
        assert isinstance(execution_context.variables["int_var"], int)

    @pytest.mark.asyncio
    async def test_set_variable_missing_name_fails(self, execution_context) -> None:
        """Test that missing variable name causes failure."""
        from casare_rpa.nodes.variable_nodes import SetVariableNode

        node = SetVariableNode(node_id="set_6", variable_name="")
        node.set_input_value("value", "test")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "Variable name is required" in result["error"]
        assert node.status == NodeStatus.ERROR


class TestGetVariableNode:
    """Tests for GetVariableNode - retrieving values from context."""

    @pytest.fixture
    def execution_context(self) -> Mock:
        """Override fixture with pre-populated variables for get tests."""
        context = Mock()
        context.variables = {
            "existing_var": "existing_value",
            "num_var": 100,
            "list_var": [1, 2, 3],
        }
        context.resolve_value = lambda x: x
        context.get_variable = lambda name, default=None: context.variables.get(
            name, default
        )
        context.set_variable = lambda name, value: context.variables.__setitem__(
            name, value
        )
        return context

    @pytest.mark.asyncio
    async def test_get_variable_existing(self, execution_context) -> None:
        """Test getting an existing variable."""
        from casare_rpa.nodes.variable_nodes import GetVariableNode

        node = GetVariableNode(node_id="get_1", variable_name="existing_var")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["variable_name"] == "existing_var"
        assert result["data"]["value"] == "existing_value"
        assert node.get_output_value("value") == "existing_value"
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_get_variable_with_default(self, execution_context) -> None:
        """Test getting undefined variable returns default."""
        from casare_rpa.nodes.variable_nodes import GetVariableNode

        node = GetVariableNode(
            node_id="get_2", variable_name="undefined_var", default_value="fallback"
        )

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["value"] == "fallback"
        assert node.get_output_value("value") == "fallback"

    @pytest.mark.asyncio
    async def test_get_variable_undefined_no_default(self, execution_context) -> None:
        """Test getting undefined variable with no default returns None."""
        from casare_rpa.nodes.variable_nodes import GetVariableNode

        node = GetVariableNode(node_id="get_3", variable_name="undefined_var")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["value"] is None
        assert node.get_output_value("value") is None

    @pytest.mark.asyncio
    async def test_get_variable_from_input_port(self, execution_context) -> None:
        """Test getting variable name from input port."""
        from casare_rpa.nodes.variable_nodes import GetVariableNode

        node = GetVariableNode(node_id="get_4")
        node.set_input_value("variable_name", "num_var")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["value"] == 100

    @pytest.mark.asyncio
    async def test_get_variable_missing_name_fails(self, execution_context) -> None:
        """Test that missing variable name causes failure."""
        from casare_rpa.nodes.variable_nodes import GetVariableNode

        node = GetVariableNode(node_id="get_5", variable_name="")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "Variable name is required" in result["error"]
        assert node.status == NodeStatus.ERROR


class TestIncrementVariableNode:
    """Tests for IncrementVariableNode - incrementing numeric variables."""

    @pytest.fixture
    def execution_context(self) -> Mock:
        """Override fixture with counter variables for increment tests."""
        context = Mock()
        context.variables = {"counter": 10, "float_counter": 5.5}
        context.resolve_value = lambda x: x
        context.get_variable = lambda name, default=None: context.variables.get(
            name, default
        )
        context.set_variable = lambda name, value: context.variables.__setitem__(
            name, value
        )
        return context

    @pytest.mark.asyncio
    async def test_increment_existing_variable(self, execution_context) -> None:
        """Test incrementing an existing variable by default 1."""
        from casare_rpa.nodes.variable_nodes import IncrementVariableNode

        node = IncrementVariableNode(node_id="inc_1", variable_name="counter")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["old_value"] == 10
        assert result["data"]["increment"] == 1.0
        assert result["data"]["new_value"] == 11.0
        assert execution_context.variables["counter"] == 11.0
        assert node.get_output_value("value") == 11.0
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_increment_custom_amount(self, execution_context) -> None:
        """Test incrementing by custom amount."""
        from casare_rpa.nodes.variable_nodes import IncrementVariableNode

        node = IncrementVariableNode(
            node_id="inc_2", variable_name="counter", increment=5.0
        )

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["new_value"] == 15.0
        assert execution_context.variables["counter"] == 15.0

    @pytest.mark.asyncio
    async def test_increment_undefined_variable_starts_at_zero(
        self, execution_context
    ) -> None:
        """Test incrementing undefined variable initializes to 0."""
        from casare_rpa.nodes.variable_nodes import IncrementVariableNode

        node = IncrementVariableNode(
            node_id="inc_3", variable_name="new_counter", increment=3.0
        )

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["old_value"] == 0
        assert result["data"]["new_value"] == 3.0
        assert execution_context.variables["new_counter"] == 3.0

    @pytest.mark.asyncio
    async def test_increment_from_input_port(self, execution_context) -> None:
        """Test increment value from input port."""
        from casare_rpa.nodes.variable_nodes import IncrementVariableNode

        node = IncrementVariableNode(node_id="inc_4", variable_name="counter")
        node.set_input_value("increment", 10.0)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["new_value"] == 20.0

    @pytest.mark.asyncio
    async def test_increment_negative_decrement(self, execution_context) -> None:
        """Test negative increment (decrement)."""
        from casare_rpa.nodes.variable_nodes import IncrementVariableNode

        node = IncrementVariableNode(
            node_id="inc_5", variable_name="counter", increment=-3.0
        )

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["new_value"] == 7.0
        assert execution_context.variables["counter"] == 7.0


class TestVariableNodesValidation:
    """Validation tests for variable nodes.

    Note: Schema validation now happens in @node_schema decorator during __init__.
    These tests verify nodes can be created and schema is attached.
    """

    def test_set_variable_has_schema(self) -> None:
        """Test SetVariableNode has schema attached."""
        from casare_rpa.nodes.variable_nodes import SetVariableNode

        node = SetVariableNode(node_id="val_1", variable_name="test")

        # Node should have schema attached by @node_schema decorator
        assert hasattr(SetVariableNode, "__node_schema__")
        assert node.config.get("variable_name") == "test"

    def test_set_variable_with_valid_name(self) -> None:
        """Test SetVariableNode with valid name stores it in config."""
        from casare_rpa.nodes.variable_nodes import SetVariableNode

        node = SetVariableNode(node_id="val_2", variable_name="valid_name")

        assert node.config.get("variable_name") == "valid_name"

    def test_get_variable_has_schema(self) -> None:
        """Test GetVariableNode has schema attached."""
        from casare_rpa.nodes.variable_nodes import GetVariableNode

        node = GetVariableNode(node_id="val_3", variable_name="test")

        assert hasattr(GetVariableNode, "__node_schema__")
        assert node.config.get("variable_name") == "test"

    def test_increment_variable_has_schema(self) -> None:
        """Test IncrementVariableNode has schema attached."""
        from casare_rpa.nodes.variable_nodes import IncrementVariableNode

        node = IncrementVariableNode(node_id="val_4", variable_name="counter")

        assert hasattr(IncrementVariableNode, "__node_schema__")
        assert node.config.get("variable_name") == "counter"


class TestVariableNodesIntegration:
    """Integration tests for variable nodes."""

    # Uses the global execution_context fixture from conftest.py

    @pytest.mark.asyncio
    async def test_set_then_get_variable(self, execution_context) -> None:
        """Test setting then getting a variable."""
        from casare_rpa.nodes.variable_nodes import SetVariableNode, GetVariableNode

        # Set the variable
        set_node = SetVariableNode(node_id="set", variable_name="test_var")
        set_node.set_input_value("value", "hello world")
        await set_node.execute(execution_context)

        # Get the variable
        get_node = GetVariableNode(node_id="get", variable_name="test_var")
        result = await get_node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["value"] == "hello world"

    @pytest.mark.asyncio
    async def test_increment_loop_simulation(self, execution_context) -> None:
        """Test incrementing a counter multiple times (loop simulation)."""
        from casare_rpa.nodes.variable_nodes import (
            SetVariableNode,
            IncrementVariableNode,
        )

        # Initialize counter
        set_node = SetVariableNode(node_id="init", variable_name="loop_counter")
        set_node.set_input_value("value", 0)
        await set_node.execute(execution_context)

        # Increment 5 times
        inc_node = IncrementVariableNode(
            node_id="inc", variable_name="loop_counter", increment=1.0
        )
        for _ in range(5):
            await inc_node.execute(execution_context)

        assert execution_context.variables["loop_counter"] == 5.0

    @pytest.mark.asyncio
    async def test_execution_result_pattern(self, execution_context) -> None:
        """Test all variable nodes follow ExecutionResult pattern."""
        from casare_rpa.nodes.variable_nodes import (
            SetVariableNode,
            GetVariableNode,
            IncrementVariableNode,
        )

        nodes = [
            SetVariableNode(node_id="n1", variable_name="v1"),
            GetVariableNode(node_id="n2", variable_name="v1"),
            IncrementVariableNode(node_id="n3", variable_name="v1"),
        ]

        nodes[0].set_input_value("value", 10)

        for node in nodes:
            result = await node.execute(execution_context)

            # Verify ExecutionResult structure
            assert "success" in result
            assert "data" in result or "error" in result
            assert "next_nodes" in result
            if result["success"]:
                assert "exec_out" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_node_type_attribute(self, execution_context) -> None:
        """Test all variable nodes have correct node_type attribute."""
        from casare_rpa.nodes.variable_nodes import (
            SetVariableNode,
            GetVariableNode,
            IncrementVariableNode,
        )

        set_node = SetVariableNode(node_id="s1", variable_name="v")
        get_node = GetVariableNode(node_id="g1", variable_name="v")
        inc_node = IncrementVariableNode(node_id="i1", variable_name="v")

        assert set_node.node_type == "SetVariableNode"
        assert get_node.node_type == "GetVariableNode"
        assert inc_node.node_type == "IncrementVariableNode"
