"""
Tests for variable nodes.

Tests setting, getting, and incrementing variables in the execution context.
"""

import pytest

from casare_rpa.nodes.variable_nodes import (
    SetVariableNode,
    GetVariableNode,
    IncrementVariableNode,
)
from casare_rpa.core.types import NodeStatus


class TestSetVariableNode:
    """Tests for SetVariable node."""

    @pytest.mark.asyncio
    async def test_set_variable_basic(self, execution_context):
        """Test setting a basic variable."""
        node = SetVariableNode(node_id="set_1", variable_name="my_var")
        node.set_input_value("value", "Hello World")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert execution_context.get_variable("my_var") == "Hello World"
        assert node.get_output_value("value") == "Hello World"

    @pytest.mark.asyncio
    async def test_set_variable_from_input_port(self, execution_context):
        """Test setting variable name from input port."""
        node = SetVariableNode(node_id="set_1")
        node.set_input_value("variable_name", "dynamic_var")
        node.set_input_value("value", 42)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert execution_context.get_variable("dynamic_var") == 42

    @pytest.mark.asyncio
    async def test_set_variable_number(self, execution_context):
        """Test setting a numeric variable."""
        node = SetVariableNode(node_id="set_1", variable_name="count")
        node.set_input_value("value", 100)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert execution_context.get_variable("count") == 100

    @pytest.mark.asyncio
    async def test_set_variable_list(self, execution_context):
        """Test setting a list variable."""
        node = SetVariableNode(node_id="set_1", variable_name="items")
        node.set_input_value("value", ["a", "b", "c"])

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert execution_context.get_variable("items") == ["a", "b", "c"]

    @pytest.mark.asyncio
    async def test_set_variable_dict(self, execution_context):
        """Test setting a dictionary variable."""
        node = SetVariableNode(node_id="set_1", variable_name="config")
        node.set_input_value("value", {"key": "value", "num": 42})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert execution_context.get_variable("config") == {"key": "value", "num": 42}

    @pytest.mark.asyncio
    async def test_set_variable_uses_default(self, execution_context):
        """Test that default value is used when no input provided."""
        node = SetVariableNode(
            node_id="set_1",
            variable_name="status",
            default_value="pending"
        )
        # Don't set input value

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert execution_context.get_variable("status") == "pending"

    @pytest.mark.asyncio
    async def test_set_variable_type_conversion_boolean(self, execution_context):
        """Test boolean type conversion."""
        node = SetVariableNode(
            node_id="set_1",
            config={
                "variable_name": "is_active",
                "variable_type": "Boolean"
            }
        )
        node.set_input_value("value", "true")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert execution_context.get_variable("is_active") is True

    @pytest.mark.asyncio
    async def test_set_variable_type_conversion_int(self, execution_context):
        """Test integer type conversion."""
        node = SetVariableNode(
            node_id="set_1",
            config={
                "variable_name": "count",
                "variable_type": "Int32"
            }
        )
        node.set_input_value("value", "42")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert execution_context.get_variable("count") == 42

    @pytest.mark.asyncio
    async def test_set_variable_no_name_fails(self, execution_context):
        """Test that missing variable name causes error."""
        node = SetVariableNode(node_id="set_1", variable_name="")
        node.set_input_value("value", "test")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_set_variable_overwrite(self, execution_context):
        """Test overwriting an existing variable."""
        # Set initial value
        execution_context.set_variable("counter", 0)

        node = SetVariableNode(node_id="set_1", variable_name="counter")
        node.set_input_value("value", 10)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert execution_context.get_variable("counter") == 10


class TestGetVariableNode:
    """Tests for GetVariable node."""

    @pytest.mark.asyncio
    async def test_get_variable_basic(self, execution_context):
        """Test getting a basic variable."""
        execution_context.set_variable("user_name", "Alice")

        node = GetVariableNode(node_id="get_1", variable_name="user_name")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["value"] == "Alice"
        assert node.get_output_value("value") == "Alice"

    @pytest.mark.asyncio
    async def test_get_variable_from_input_port(self, execution_context):
        """Test getting variable name from input port."""
        execution_context.set_variable("dynamic_key", "secret_value")

        node = GetVariableNode(node_id="get_1")
        node.set_input_value("variable_name", "dynamic_key")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("value") == "secret_value"

    @pytest.mark.asyncio
    async def test_get_variable_number(self, execution_context):
        """Test getting a numeric variable."""
        execution_context.set_variable("score", 95)

        node = GetVariableNode(node_id="get_1", variable_name="score")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("value") == 95

    @pytest.mark.asyncio
    async def test_get_variable_complex_type(self, execution_context):
        """Test getting a complex variable type."""
        data = {"users": [{"name": "Alice"}, {"name": "Bob"}]}
        execution_context.set_variable("api_response", data)

        node = GetVariableNode(node_id="get_1", variable_name="api_response")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("value") == data

    @pytest.mark.asyncio
    async def test_get_variable_not_found_uses_default(self, execution_context):
        """Test that default is used when variable not found."""
        node = GetVariableNode(
            node_id="get_1",
            variable_name="nonexistent",
            default_value="default_value"
        )

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("value") == "default_value"

    @pytest.mark.asyncio
    async def test_get_variable_not_found_no_default(self, execution_context):
        """Test getting nonexistent variable without default returns None."""
        node = GetVariableNode(node_id="get_1", variable_name="nonexistent")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("value") is None

    @pytest.mark.asyncio
    async def test_get_variable_no_name_fails(self, execution_context):
        """Test that missing variable name causes error."""
        node = GetVariableNode(node_id="get_1", variable_name="")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "required" in result["error"].lower()


class TestIncrementVariableNode:
    """Tests for IncrementVariable node."""

    @pytest.mark.asyncio
    async def test_increment_basic(self, execution_context):
        """Test basic increment operation."""
        execution_context.set_variable("counter", 5)

        node = IncrementVariableNode(node_id="inc_1", variable_name="counter")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert execution_context.get_variable("counter") == 6.0
        assert node.get_output_value("value") == 6.0

    @pytest.mark.asyncio
    async def test_increment_custom_amount(self, execution_context):
        """Test increment with custom amount."""
        execution_context.set_variable("score", 100)

        node = IncrementVariableNode(
            node_id="inc_1",
            variable_name="score",
            increment=10
        )

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert execution_context.get_variable("score") == 110.0

    @pytest.mark.asyncio
    async def test_increment_negative(self, execution_context):
        """Test decrement with negative increment."""
        execution_context.set_variable("lives", 3)

        node = IncrementVariableNode(
            node_id="inc_1",
            variable_name="lives",
            increment=-1
        )

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert execution_context.get_variable("lives") == 2.0

    @pytest.mark.asyncio
    async def test_increment_from_zero(self, execution_context):
        """Test incrementing a variable that doesn't exist (starts at 0)."""
        node = IncrementVariableNode(node_id="inc_1", variable_name="new_counter")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert execution_context.get_variable("new_counter") == 1.0

    @pytest.mark.asyncio
    async def test_increment_float(self, execution_context):
        """Test increment with float value."""
        execution_context.set_variable("percentage", 50.5)

        node = IncrementVariableNode(
            node_id="inc_1",
            variable_name="percentage",
            increment=0.5
        )

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert execution_context.get_variable("percentage") == 51.0

    @pytest.mark.asyncio
    async def test_increment_from_input(self, execution_context):
        """Test increment amount from input port."""
        execution_context.set_variable("value", 10)

        node = IncrementVariableNode(node_id="inc_1", variable_name="value")
        node.set_input_value("increment", 5)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert execution_context.get_variable("value") == 15.0

    @pytest.mark.asyncio
    async def test_increment_variable_name_from_input(self, execution_context):
        """Test variable name from input port."""
        execution_context.set_variable("dynamic_var", 20)

        node = IncrementVariableNode(node_id="inc_1")
        node.set_input_value("variable_name", "dynamic_var")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert execution_context.get_variable("dynamic_var") == 21.0

    @pytest.mark.asyncio
    async def test_increment_returns_details(self, execution_context):
        """Test that result includes old and new values."""
        execution_context.set_variable("counter", 10)

        node = IncrementVariableNode(
            node_id="inc_1",
            variable_name="counter",
            increment=5
        )

        result = await node.execute(execution_context)

        assert result["data"]["old_value"] == 10
        assert result["data"]["increment"] == 5
        assert result["data"]["new_value"] == 15.0


class TestVariableNodeScenarios:
    """Integration tests for variable operations."""

    @pytest.mark.asyncio
    async def test_set_then_get_variable(self, execution_context):
        """Test setting and then getting a variable."""
        # Set variable
        set_node = SetVariableNode(node_id="set_1", variable_name="message")
        set_node.set_input_value("value", "Hello from CasareRPA!")

        await set_node.execute(execution_context)

        # Get variable
        get_node = GetVariableNode(node_id="get_1", variable_name="message")

        result = await get_node.execute(execution_context)

        assert result["success"] is True
        assert get_node.get_output_value("value") == "Hello from CasareRPA!"

    @pytest.mark.asyncio
    async def test_increment_in_loop(self, execution_context):
        """Test incrementing a counter in a loop."""
        # Initialize counter
        execution_context.set_variable("loop_counter", 0)

        inc_node = IncrementVariableNode(
            node_id="inc_1",
            variable_name="loop_counter"
        )

        # Simulate 5 loop iterations
        for _ in range(5):
            await inc_node.execute(execution_context)

        assert execution_context.get_variable("loop_counter") == 5.0

    @pytest.mark.asyncio
    async def test_variable_chaining(self, execution_context):
        """Test chaining variable operations."""
        # Set initial value
        set_node = SetVariableNode(node_id="set_1", variable_name="price")
        set_node.set_input_value("value", 100)
        await set_node.execute(execution_context)

        # Get value and use it
        get_node = GetVariableNode(node_id="get_1", variable_name="price")
        await get_node.execute(execution_context)

        price = get_node.get_output_value("value")

        # Calculate tax and set new variable
        tax = price * 0.1
        set_tax = SetVariableNode(node_id="set_2", variable_name="tax")
        set_tax.set_input_value("value", tax)
        await set_tax.execute(execution_context)

        assert execution_context.get_variable("tax") == 10.0

    @pytest.mark.asyncio
    async def test_accumulator_pattern(self, execution_context):
        """Test accumulator pattern with variables."""
        # Initialize accumulator
        execution_context.set_variable("total", 0)

        values = [10, 20, 30, 40]

        for value in values:
            # Get current total
            get_node = GetVariableNode(node_id="get_total", variable_name="total")
            await get_node.execute(execution_context)

            current = get_node.get_output_value("value")

            # Add value and set new total
            set_node = SetVariableNode(node_id="set_total", variable_name="total")
            set_node.set_input_value("value", current + value)
            await set_node.execute(execution_context)

        assert execution_context.get_variable("total") == 100

    @pytest.mark.asyncio
    async def test_multiple_variables(self, execution_context):
        """Test working with multiple variables."""
        # Set multiple variables
        vars_to_set = {
            "first_name": "John",
            "last_name": "Doe",
            "age": 30,
            "is_active": True
        }

        for var_name, var_value in vars_to_set.items():
            set_node = SetVariableNode(node_id=f"set_{var_name}", variable_name=var_name)
            set_node.set_input_value("value", var_value)
            await set_node.execute(execution_context)

        # Verify all variables are set
        for var_name, expected_value in vars_to_set.items():
            get_node = GetVariableNode(node_id=f"get_{var_name}", variable_name=var_name)
            await get_node.execute(execution_context)
            assert get_node.get_output_value("value") == expected_value

    @pytest.mark.asyncio
    async def test_output_chaining(self, execution_context):
        """Test using output of one node as input to another."""
        # Set a value
        set_node = SetVariableNode(node_id="set_1", variable_name="data")
        set_node.set_input_value("value", {"count": 5})
        await set_node.execute(execution_context)

        # The output value from set can be used by another node
        output_value = set_node.get_output_value("value")
        assert output_value == {"count": 5}

        # Another node could use this as input
        set_node2 = SetVariableNode(node_id="set_2", variable_name="data_copy")
        set_node2.set_input_value("value", output_value)
        await set_node2.execute(execution_context)

        assert execution_context.get_variable("data_copy") == {"count": 5}
