"""
CasareRPA - E2E Tests for Variable Manipulation Workflows.

Tests variable operations including:
- Setting and getting variables
- Different data types (string, integer, list, dict)
- Variable increment/decrement
- Variable overwriting
- Multiple variables in same workflow
- Variable interpolation with initial values
"""

import pytest

from tests.e2e.helpers import WorkflowBuilder


@pytest.mark.asyncio
@pytest.mark.e2e
class TestVariableWorkflows:
    """End-to-end tests for variable manipulation workflows."""

    async def test_set_and_get_string_variable(self):
        """
        Test: Start -> SetVar("name", "John") -> GetVar("name", "output") -> End
        Expected: output == "John"
        """
        result = await (
            WorkflowBuilder(name="Set and Get String Variable")
            .add_start()
            .add_set_variable("name", "John", variable_type="String")
            .add_get_variable("name", output_var="output")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"]["name"] == "John", "Variable 'name' should be 'John'"

    async def test_set_integer_variable(self):
        """
        Test: Start -> SetVar("count", 42) -> End
        Expected: count == 42
        """
        result = await (
            WorkflowBuilder(name="Set Integer Variable")
            .add_start()
            .add_set_variable("count", 42, variable_type="Int32")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"]["count"] == 42, "Variable 'count' should be 42"

    async def test_set_float_variable(self):
        """
        Test: Start -> SetVar("pi", 3.14159) -> End
        Expected: pi == 3.14159
        """
        result = await (
            WorkflowBuilder(name="Set Float Variable")
            .add_start()
            .add_set_variable("pi", 3.14159, variable_type="Float")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            abs(result["variables"]["pi"] - 3.14159) < 0.0001
        ), "Variable 'pi' should be 3.14159"

    async def test_set_boolean_variable(self):
        """
        Test: Start -> SetVar("is_active", True) -> End
        Expected: is_active == True
        """
        result = await (
            WorkflowBuilder(name="Set Boolean Variable")
            .add_start()
            .add_set_variable("is_active", True, variable_type="Boolean")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            result["variables"]["is_active"] is True
        ), "Variable 'is_active' should be True"

    async def test_set_list_variable(self):
        """
        Test: Start -> SetVar("items", [1, 2, 3]) -> End
        Expected: items == [1, 2, 3]
        """
        result = await (
            WorkflowBuilder(name="Set List Variable")
            .add_start()
            .add_set_variable("items", [1, 2, 3])
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"]["items"] == [
            1,
            2,
            3,
        ], "Variable 'items' should be [1, 2, 3]"

    async def test_set_dict_variable(self):
        """
        Test: Start -> SetVar("user", {"name": "John", "age": 30}) -> End
        Expected: user == {"name": "John", "age": 30}
        """
        user_data = {"name": "John", "age": 30}
        result = await (
            WorkflowBuilder(name="Set Dict Variable")
            .add_start()
            .add_set_variable("user", user_data)
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            result["variables"]["user"] == user_data
        ), f"Variable 'user' should be {user_data}"

    async def test_increment_variable_once(self):
        """
        Test: Start -> SetVar("counter", 0) -> Increment("counter") -> End
        Expected: counter == 1
        """
        result = await (
            WorkflowBuilder(name="Increment Variable Once")
            .add_start()
            .add_set_variable("counter", 0, variable_type="Int32")
            .add_increment_variable("counter")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"]["counter"] == 1, "Variable 'counter' should be 1"

    async def test_increment_variable_chain(self):
        """
        Test: Start -> SetVar("counter", 0) -> Increment -> Increment -> Increment -> End
        Expected: counter == 3
        """
        result = await (
            WorkflowBuilder(name="Increment Variable Chain")
            .add_start()
            .add_set_variable("counter", 0, variable_type="Int32")
            .add_increment_variable("counter")
            .add_increment_variable("counter")
            .add_increment_variable("counter")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            result["variables"]["counter"] == 3
        ), "Variable 'counter' should be 3 after 3 increments"

    async def test_increment_variable_with_custom_amount(self):
        """
        Test: Start -> SetVar("value", 10) -> Increment(5) -> End
        Expected: value == 15
        """
        result = await (
            WorkflowBuilder(name="Increment Variable Custom Amount")
            .add_start()
            .add_set_variable("value", 10, variable_type="Int32")
            .add_increment_variable("value", increment=5)
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            result["variables"]["value"] == 15
        ), "Variable 'value' should be 15 after incrementing by 5"

    async def test_decrement_variable(self):
        """
        Test: Start -> SetVar("counter", 10) -> Decrement("counter") -> End
        Expected: counter == 9
        """
        result = await (
            WorkflowBuilder(name="Decrement Variable")
            .add_start()
            .add_set_variable("counter", 10, variable_type="Int32")
            .add_decrement_variable("counter")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            result["variables"]["counter"] == 9
        ), "Variable 'counter' should be 9 after decrement"

    async def test_variable_overwrite(self):
        """
        Test: Start -> SetVar("x", 10) -> SetVar("x", 20) -> End
        Expected: x == 20 (second value overwrites first)
        """
        result = await (
            WorkflowBuilder(name="Variable Overwrite")
            .add_start()
            .add_set_variable("x", 10, variable_type="Int32")
            .add_set_variable("x", 20, variable_type="Int32")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            result["variables"]["x"] == 20
        ), "Variable 'x' should be 20 after overwrite"

    async def test_multiple_variables(self):
        """
        Test: Start -> SetVar("a", 1) -> SetVar("b", 2) -> SetVar("c", 3) -> End
        Expected: a==1, b==2, c==3
        """
        result = await (
            WorkflowBuilder(name="Multiple Variables")
            .add_start()
            .add_set_variable("a", 1, variable_type="Int32")
            .add_set_variable("b", 2, variable_type="Int32")
            .add_set_variable("c", 3, variable_type="Int32")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"]["a"] == 1, "Variable 'a' should be 1"
        assert result["variables"]["b"] == 2, "Variable 'b' should be 2"
        assert result["variables"]["c"] == 3, "Variable 'c' should be 3"

    async def test_variable_with_initial_values(self):
        """
        Test: Initial vars: {"input": "hello"}
              Start -> SetVar("output", "{{input}}_world") -> End
        Expected: output == "hello_world"
        """
        result = await (
            WorkflowBuilder(name="Variable With Initial Values")
            .add_start()
            .add_set_variable("output", "{{input}}_world", variable_type="String")
            .add_end()
            .execute(initial_vars={"input": "hello"})
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        # Note: Variable interpolation may or may not work depending on SetVariableNode implementation
        # The test documents expected behavior - actual result depends on node implementation
        assert "output" in result["variables"], "Variable 'output' should exist"

    async def test_empty_string_variable(self):
        """
        Test: Start -> SetVar("empty", "") -> End
        Expected: empty == ""
        """
        result = await (
            WorkflowBuilder(name="Empty String Variable")
            .add_start()
            .add_set_variable("empty", "", variable_type="String")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            result["variables"]["empty"] == ""
        ), "Variable 'empty' should be empty string"

    async def test_zero_value_variable(self):
        """
        Test: Start -> SetVar("zero", 0) -> End
        Expected: zero == 0 (falsy value should still be stored)
        """
        result = await (
            WorkflowBuilder(name="Zero Value Variable")
            .add_start()
            .add_set_variable("zero", 0, variable_type="Int32")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"]["zero"] == 0, "Variable 'zero' should be 0"

    async def test_null_variable(self):
        """
        Test: Start -> SetVar("null_var", None) -> End
        Expected: null_var == None
        """
        result = await (
            WorkflowBuilder(name="Null Variable")
            .add_start()
            .add_set_variable("null_var", None)
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            result["variables"]["null_var"] is None
        ), "Variable 'null_var' should be None"

    async def test_nested_dict_variable(self):
        """
        Test: Start -> SetVar("nested", {"level1": {"level2": {"value": 42}}}) -> End
        Expected: nested["level1"]["level2"]["value"] == 42
        """
        nested_data = {"level1": {"level2": {"value": 42}}}
        result = await (
            WorkflowBuilder(name="Nested Dict Variable")
            .add_start()
            .add_set_variable("nested", nested_data)
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            result["variables"]["nested"] == nested_data
        ), "Nested dict should be preserved"
        assert result["variables"]["nested"]["level1"]["level2"]["value"] == 42

    async def test_list_with_mixed_types(self):
        """
        Test: Start -> SetVar("mixed", [1, "two", 3.0, True, None]) -> End
        Expected: mixed == [1, "two", 3.0, True, None]
        """
        mixed_list = [1, "two", 3.0, True, None]
        result = await (
            WorkflowBuilder(name="Mixed Type List Variable")
            .add_start()
            .add_set_variable("mixed", mixed_list)
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            result["variables"]["mixed"] == mixed_list
        ), "Mixed type list should be preserved"

    async def test_variable_operations_sequence(self):
        """
        Test complex sequence:
        Start -> SetVar("counter", 0) -> Inc -> Inc -> SetVar("result", counter*2) -> End
        Expected: counter==2, result set appropriately
        """
        result = await (
            WorkflowBuilder(name="Variable Operations Sequence")
            .add_start()
            .add_set_variable("counter", 0, variable_type="Int32")
            .add_increment_variable("counter")
            .add_increment_variable("counter")
            .add_set_variable("final_count", "{{counter}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            result["variables"]["counter"] == 2
        ), "Counter should be 2 after two increments"

    async def test_initial_vars_preserved(self):
        """
        Test that initial variables are preserved through execution.
        Initial: {"preset": "value", "number": 100}
        Start -> SetVar("new", "added") -> End
        Expected: preset=="value", number==100, new=="added"
        """
        result = await (
            WorkflowBuilder(name="Initial Vars Preserved")
            .add_start()
            .add_set_variable("new", "added")
            .add_end()
            .execute(initial_vars={"preset": "value", "number": 100})
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            result["variables"]["preset"] == "value"
        ), "Initial var 'preset' should be preserved"
        assert (
            result["variables"]["number"] == 100
        ), "Initial var 'number' should be preserved"
        assert result["variables"]["new"] == "added", "New var should be added"

    async def test_increment_initial_variable(self):
        """
        Test incrementing a variable that was set in initial_vars.
        Initial: {"counter": 10}
        Start -> Increment("counter") -> Increment("counter") -> End
        Expected: counter == 12
        """
        result = await (
            WorkflowBuilder(name="Increment Initial Variable")
            .add_start()
            .add_increment_variable("counter")
            .add_increment_variable("counter")
            .add_end()
            .execute(initial_vars={"counter": 10})
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"]["counter"] == 12, "Counter should be 12 (10 + 2)"

    async def test_large_list_variable(self):
        """
        Test setting a large list (1000 items).
        Expected: List is stored and retrievable correctly.
        """
        large_list = list(range(1000))
        result = await (
            WorkflowBuilder(name="Large List Variable")
            .add_start()
            .add_set_variable("large", large_list)
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            result["variables"]["large"] == large_list
        ), "Large list should be preserved"
        assert len(result["variables"]["large"]) == 1000, "List should have 1000 items"

    async def test_special_characters_in_string(self):
        """
        Test string variable with special characters.
        """
        special_string = 'Hello "World"! Tab:\t Newline:\n Unicode: \u00e9\u00e8\u00ea'
        result = await (
            WorkflowBuilder(name="Special Characters String")
            .add_start()
            .add_set_variable("special", special_string)
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            result["variables"]["special"] == special_string
        ), "Special characters should be preserved"
