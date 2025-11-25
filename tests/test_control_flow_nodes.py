"""
Tests for control flow nodes.

Tests conditional logic (If), loops (For, While), and control statements (Break, Continue, Switch).
"""

import pytest

from casare_rpa.nodes.control_flow_nodes import (
    IfNode,
    ForLoopNode,
    WhileLoopNode,
    BreakNode,
    ContinueNode,
    SwitchNode,
)
from casare_rpa.core.types import NodeStatus


class TestIfNode:
    """Tests for conditional If node."""

    @pytest.mark.asyncio
    async def test_if_true_condition(self, execution_context):
        """Test If node with true condition."""
        node = IfNode(node_id="if_1")
        node.set_input_value("condition", True)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["condition"] is True
        assert "true" in result["next_nodes"]
        assert "false" not in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_if_false_condition(self, execution_context):
        """Test If node with false condition."""
        node = IfNode(node_id="if_1")
        node.set_input_value("condition", False)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["condition"] is False
        assert "false" in result["next_nodes"]
        assert "true" not in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_if_truthy_values(self, execution_context):
        """Test If node with truthy values."""
        truthy_values = [1, "text", [1, 2], {"key": "value"}, 0.1]

        for value in truthy_values:
            node = IfNode(node_id=f"if_{id(value)}")
            node.set_input_value("condition", value)

            result = await node.execute(execution_context)

            assert result["data"]["condition"] is True, f"Expected {value} to be truthy"
            assert "true" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_if_falsy_values(self, execution_context):
        """Test If node with falsy values."""
        falsy_values = [0, "", [], {}, None]

        for value in falsy_values:
            node = IfNode(node_id=f"if_{id(value)}")
            node.set_input_value("condition", value)

            result = await node.execute(execution_context)

            assert result["data"]["condition"] is False, f"Expected {value} to be falsy"
            assert "false" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_if_expression_evaluation(self, execution_context):
        """Test If node with expression from config."""
        execution_context.set_variable("age", 25)

        node = IfNode(node_id="if_1", config={"expression": "age >= 18"})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["condition"] is True

    @pytest.mark.asyncio
    async def test_if_expression_false(self, execution_context):
        """Test If node with expression evaluating to false."""
        execution_context.set_variable("score", 50)

        node = IfNode(node_id="if_1", config={"expression": "score >= 70"})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["condition"] is False

    @pytest.mark.asyncio
    async def test_if_no_condition_defaults_false(self, execution_context):
        """Test If node with no condition defaults to false."""
        node = IfNode(node_id="if_1")
        # No condition set

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["condition"] is False
        assert "false" in result["next_nodes"]


class TestForLoopNode:
    """Tests for For Loop node."""

    @pytest.mark.asyncio
    async def test_for_loop_with_list(self, execution_context):
        """Test For loop iterating over a list."""
        node = ForLoopNode(node_id="for_1")
        node.set_input_value("items", ["a", "b", "c"])

        # First iteration
        result1 = await node.execute(execution_context)
        assert result1["success"] is True
        assert "loop_body" in result1["next_nodes"]
        assert node.get_output_value("item") == "a"
        assert node.get_output_value("index") == 0

        # Second iteration
        result2 = await node.execute(execution_context)
        assert node.get_output_value("item") == "b"
        assert node.get_output_value("index") == 1

        # Third iteration
        result3 = await node.execute(execution_context)
        assert node.get_output_value("item") == "c"
        assert node.get_output_value("index") == 2

        # Loop completed
        result4 = await node.execute(execution_context)
        assert "completed" in result4["next_nodes"]
        assert result4["data"]["iterations"] == 3

    @pytest.mark.asyncio
    async def test_for_loop_with_range_config(self, execution_context):
        """Test For loop with range from config."""
        node = ForLoopNode(node_id="for_1", config={
            "start": 0,
            "end": 5,
            "step": 1
        })

        items_collected = []
        for _ in range(6):  # 5 iterations + 1 completion
            result = await node.execute(execution_context)
            if "loop_body" in result["next_nodes"]:
                items_collected.append(node.get_output_value("item"))
            else:
                break

        assert items_collected == [0, 1, 2, 3, 4]

    @pytest.mark.asyncio
    async def test_for_loop_with_step(self, execution_context):
        """Test For loop with custom step."""
        node = ForLoopNode(node_id="for_1", config={
            "start": 0,
            "end": 10,
            "step": 2
        })

        items_collected = []
        for _ in range(10):
            result = await node.execute(execution_context)
            if "loop_body" in result["next_nodes"]:
                items_collected.append(node.get_output_value("item"))
            else:
                break

        assert items_collected == [0, 2, 4, 6, 8]

    @pytest.mark.asyncio
    async def test_for_loop_empty_list(self, execution_context):
        """Test For loop with empty list completes immediately."""
        node = ForLoopNode(node_id="for_1")
        node.set_input_value("items", [])

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "completed" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_for_loop_single_item(self, execution_context):
        """Test For loop with single item."""
        node = ForLoopNode(node_id="for_1")
        node.set_input_value("items", ["only"])

        # Single iteration
        result1 = await node.execute(execution_context)
        assert "loop_body" in result1["next_nodes"]
        assert node.get_output_value("item") == "only"

        # Completion
        result2 = await node.execute(execution_context)
        assert "completed" in result2["next_nodes"]


class TestWhileLoopNode:
    """Tests for While Loop node."""

    @pytest.mark.asyncio
    async def test_while_loop_basic(self, execution_context):
        """Test While loop with counter."""
        execution_context.set_variable("counter", 3)

        iterations = 0
        for _ in range(10):  # Safety limit
            # Simulate counter decrement
            node = WhileLoopNode(node_id="while_1", config={
                "expression": "counter > 0"
            })
            result = await node.execute(execution_context)

            if "loop_body" in result["next_nodes"]:
                iterations += 1
                counter = execution_context.get_variable("counter")
                execution_context.set_variable("counter", counter - 1)
            else:
                break

        assert iterations == 3

    @pytest.mark.asyncio
    async def test_while_loop_false_condition(self, execution_context):
        """Test While loop with initially false condition."""
        node = WhileLoopNode(node_id="while_1")
        node.set_input_value("condition", False)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "completed" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_while_loop_max_iterations(self, execution_context):
        """Test While loop respects max iterations limit."""
        node = WhileLoopNode(node_id="while_1", config={
            "max_iterations": 5
        })
        node.set_input_value("condition", True)

        iterations = 0
        for _ in range(10):
            result = await node.execute(execution_context)
            if "loop_body" in result["next_nodes"]:
                iterations += 1
            else:
                break

        assert iterations == 5
        assert result["data"]["reason"] == "max_iterations"

    @pytest.mark.asyncio
    async def test_while_loop_outputs_iteration(self, execution_context):
        """Test While loop outputs iteration count."""
        node = WhileLoopNode(node_id="while_1", config={
            "max_iterations": 3
        })
        node.set_input_value("condition", True)

        # First iteration
        result = await node.execute(execution_context)
        assert node.get_output_value("iteration") == 0

        # Second iteration
        result = await node.execute(execution_context)
        assert node.get_output_value("iteration") == 1


class TestBreakNode:
    """Tests for Break node."""

    @pytest.mark.asyncio
    async def test_break_signals_loop_exit(self, execution_context):
        """Test Break node signals loop exit."""
        node = BreakNode(node_id="break_1")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["control_flow"] == "break"
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_break_has_exec_output(self, execution_context):
        """Test Break node has exec output."""
        node = BreakNode(node_id="break_1")

        result = await node.execute(execution_context)

        assert "exec_out" in result["next_nodes"]


class TestContinueNode:
    """Tests for Continue node."""

    @pytest.mark.asyncio
    async def test_continue_signals_skip(self, execution_context):
        """Test Continue node signals skip to next iteration."""
        node = ContinueNode(node_id="continue_1")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["control_flow"] == "continue"
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_continue_has_exec_output(self, execution_context):
        """Test Continue node has exec output."""
        node = ContinueNode(node_id="continue_1")

        result = await node.execute(execution_context)

        assert "exec_out" in result["next_nodes"]


class TestSwitchNode:
    """Tests for Switch node."""

    @pytest.mark.asyncio
    async def test_switch_matches_case(self, execution_context):
        """Test Switch node matches a case."""
        node = SwitchNode(node_id="switch_1", config={
            "cases": ["success", "error", "pending"]
        })
        node.set_input_value("value", "success")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["matched_case"] == "success"
        assert "case_success" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_switch_no_match_uses_default(self, execution_context):
        """Test Switch node uses default when no match."""
        node = SwitchNode(node_id="switch_1", config={
            "cases": ["success", "error"]
        })
        node.set_input_value("value", "unknown")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["matched_case"] == "default"
        assert "default" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_switch_with_numeric_cases(self, execution_context):
        """Test Switch node with numeric values."""
        node = SwitchNode(node_id="switch_1", config={
            "cases": ["1", "2", "3"]
        })
        node.set_input_value("value", 2)

        result = await node.execute(execution_context)

        assert result["data"]["matched_case"] == "2"
        assert "case_2" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_switch_empty_cases(self, execution_context):
        """Test Switch with no cases always uses default."""
        node = SwitchNode(node_id="switch_1", config={"cases": []})
        node.set_input_value("value", "anything")

        result = await node.execute(execution_context)

        assert "default" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_switch_null_value(self, execution_context):
        """Test Switch node with None value."""
        node = SwitchNode(node_id="switch_1", config={
            "cases": ["null", "empty"]
        })
        node.set_input_value("value", None)

        result = await node.execute(execution_context)

        # None converts to empty string, may match "None" or default
        assert result["success"] is True


class TestControlFlowScenarios:
    """Integration tests for control flow patterns."""

    @pytest.mark.asyncio
    async def test_if_else_branching(self, execution_context):
        """Test if-else style branching."""
        # Check if age >= 18
        execution_context.set_variable("age", 21)

        if_node = IfNode(node_id="if_age", config={
            "expression": "age >= 18"
        })

        result = await if_node.execute(execution_context)

        assert result["data"]["condition"] is True
        assert "true" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_for_loop_collect_items(self, execution_context):
        """Test for loop collecting and processing items."""
        data = ["apple", "banana", "cherry"]

        for_node = ForLoopNode(node_id="for_collect")
        for_node.set_input_value("items", data)

        processed = []
        for _ in range(10):  # Safety limit
            result = await for_node.execute(execution_context)

            if "loop_body" in result["next_nodes"]:
                item = for_node.get_output_value("item")
                processed.append(item.upper())
            else:
                break

        assert processed == ["APPLE", "BANANA", "CHERRY"]

    @pytest.mark.asyncio
    async def test_nested_conditions(self, execution_context):
        """Test nested if conditions."""
        execution_context.set_variable("temperature", 75)
        execution_context.set_variable("raining", False)

        # Check temperature
        temp_check = IfNode(node_id="if_temp", config={
            "expression": "temperature > 70"
        })
        temp_result = await temp_check.execute(execution_context)

        if temp_result["data"]["condition"]:
            # Check rain
            rain_check = IfNode(node_id="if_rain", config={
                "expression": "not raining"
            })
            rain_result = await rain_check.execute(execution_context)

            # Good weather: warm and not raining
            assert rain_result["data"]["condition"] is True

    @pytest.mark.asyncio
    async def test_switch_status_handling(self, execution_context):
        """Test switch for status handling pattern."""
        statuses = ["pending", "processing", "success", "error", "unknown"]
        expected_cases = ["pending", "processing", "success", "error", "default"]

        for status, expected in zip(statuses, expected_cases):
            switch_node = SwitchNode(node_id="switch_status", config={
                "cases": ["pending", "processing", "success", "error"]
            })
            switch_node.set_input_value("value", status)

            result = await switch_node.execute(execution_context)

            if expected == "default":
                assert result["data"]["matched_case"] == "default"
            else:
                assert result["data"]["matched_case"] == expected

    @pytest.mark.asyncio
    async def test_loop_with_break_pattern(self, execution_context):
        """Test pattern of loop with conditional break."""
        # Search for first even number
        numbers = [1, 3, 5, 4, 7, 9]

        for_node = ForLoopNode(node_id="for_search")
        for_node.set_input_value("items", numbers)

        found_number = None
        for _ in range(10):
            result = await for_node.execute(execution_context)

            if "loop_body" in result["next_nodes"]:
                current = for_node.get_output_value("item")
                if current % 2 == 0:
                    found_number = current
                    # Would execute break here
                    break
            else:
                break

        assert found_number == 4

    @pytest.mark.asyncio
    async def test_loop_with_continue_pattern(self, execution_context):
        """Test pattern of loop with conditional continue."""
        # Sum only even numbers
        numbers = [1, 2, 3, 4, 5, 6]

        for_node = ForLoopNode(node_id="for_sum")
        for_node.set_input_value("items", numbers)

        total = 0
        for _ in range(10):
            result = await for_node.execute(execution_context)

            if "loop_body" in result["next_nodes"]:
                current = for_node.get_output_value("item")
                if current % 2 != 0:
                    # Would execute continue here
                    continue
                total += current
            else:
                break

        assert total == 12  # 2 + 4 + 6

    @pytest.mark.asyncio
    async def test_complex_workflow_pattern(self, execution_context):
        """Test complex workflow with multiple control flow nodes."""
        # Process users and categorize by age
        users = [
            {"name": "Alice", "age": 25},
            {"name": "Bob", "age": 17},
            {"name": "Charlie", "age": 30},
        ]

        for_node = ForLoopNode(node_id="for_users")
        for_node.set_input_value("items", users)

        adults = []
        minors = []

        for _ in range(10):
            result = await for_node.execute(execution_context)

            if "loop_body" in result["next_nodes"]:
                user = for_node.get_output_value("item")
                execution_context.set_variable("user_age", user["age"])

                # Check if adult
                if_adult = IfNode(node_id="if_adult", config={
                    "expression": "user_age >= 18"
                })
                if_result = await if_adult.execute(execution_context)

                if if_result["data"]["condition"]:
                    adults.append(user["name"])
                else:
                    minors.append(user["name"])
            else:
                break

        assert adults == ["Alice", "Charlie"]
        assert minors == ["Bob"]
