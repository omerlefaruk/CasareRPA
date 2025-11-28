"""
Comprehensive tests for control flow nodes.

Tests 8 control flow nodes:
- IfNode: Conditional branching
- ForLoopStartNode/ForLoopEndNode: For loop iteration
- WhileLoopStartNode/WhileLoopEndNode: While loop iteration
- SwitchNode: Multi-way branching
- BreakNode: Exit loop
- ContinueNode: Skip to next iteration

All tests verify ExecutionResult pattern compliance.
"""

import pytest
from unittest.mock import Mock

from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.nodes.control_flow_nodes import (
    IfNode,
    ForLoopStartNode,
    ForLoopEndNode,
    WhileLoopStartNode,
    WhileLoopEndNode,
    SwitchNode,
    BreakNode,
    ContinueNode,
)


@pytest.fixture
def execution_context():
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


class TestIfNode:
    """Tests for IfNode conditional branching."""

    @pytest.mark.asyncio
    async def test_if_true_branch_with_input(self, execution_context):
        """Test IfNode routes to true branch when input condition is True."""
        node = IfNode(node_id="test_if_true")
        node.set_input_value("condition", True)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["condition"] is True
        assert "true" in result["next_nodes"]
        assert "false" not in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_if_false_branch_with_input(self, execution_context):
        """Test IfNode routes to false branch when input condition is False."""
        node = IfNode(node_id="test_if_false")
        node.set_input_value("condition", False)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["condition"] is False
        assert "false" in result["next_nodes"]
        assert "true" not in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_if_true_branch_with_expression(self, execution_context):
        """Test IfNode routes to true branch when expression evaluates to True."""
        node = IfNode(node_id="test_if_expr_true")
        node.config["expression"] = "5 > 3"

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["condition"] is True
        assert "true" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_if_false_branch_with_expression(self, execution_context):
        """Test IfNode routes to false branch when expression evaluates to False."""
        node = IfNode(node_id="test_if_expr_false")
        node.config["expression"] = "5 < 3"

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["condition"] is False
        assert "false" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_if_with_context_variables(self, execution_context):
        """Test IfNode evaluates expressions with context variables."""
        execution_context.variables["test_var"] = 42

        node = IfNode(node_id="test_if_var")
        node.config["expression"] = "test_var > 40"

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["condition"] is True
        assert "true" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_if_no_condition_defaults_false(self, execution_context):
        """Test IfNode defaults to false when no condition provided."""
        node = IfNode(node_id="test_if_no_cond")
        # No input or expression set

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["condition"] is False
        assert "false" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_if_truthy_values(self, execution_context):
        """Test IfNode handles truthy values correctly."""
        for truthy in [1, "hello", [1], {"a": 1}, 1.5]:
            node = IfNode(node_id=f"test_if_truthy_{type(truthy).__name__}")
            node.set_input_value("condition", truthy)

            result = await node.execute(execution_context)

            assert result["success"] is True
            assert result["data"]["condition"] is True
            assert "true" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_if_falsy_values(self, execution_context):
        """Test IfNode handles falsy values correctly."""
        for falsy in [0, "", [], {}, None, 0.0]:
            node = IfNode(node_id=f"test_if_falsy_{type(falsy).__name__}")
            node.set_input_value("condition", falsy)

            result = await node.execute(execution_context)

            assert result["success"] is True
            assert result["data"]["condition"] is False
            assert "false" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_if_invalid_expression_defaults_false(self, execution_context):
        """Test IfNode handles invalid expressions gracefully."""
        node = IfNode(node_id="test_if_invalid")
        node.config["expression"] = "undefined_var > 5"

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["condition"] is False
        assert "false" in result["next_nodes"]

    def test_if_node_ports(self):
        """Test IfNode has correct ports defined."""
        node = IfNode(node_id="test_ports")
        assert "exec_in" in [p.name for p in node.input_ports.values()]
        assert "condition" in [p.name for p in node.input_ports.values()]
        assert "true" in [p.name for p in node.output_ports.values()]
        assert "false" in [p.name for p in node.output_ports.values()]

    def test_if_node_type(self):
        """Test IfNode has correct type."""
        node = IfNode(node_id="test_type")
        assert node.node_type == "IfNode"
        assert node.name == "If"


# =============================================================================
# ForLoopStartNode Tests
# =============================================================================


class TestForLoopStartNode:
    """Tests for ForLoopStartNode iteration control."""

    @pytest.mark.asyncio
    async def test_for_range_iteration_first(self, execution_context):
        """Test ForLoopStartNode first iteration with range."""
        node = ForLoopStartNode(node_id="test_for_range")
        node.config["start"] = 0
        node.config["end"] = 3
        node.config["step"] = 1

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "body" in result["next_nodes"]
        assert result["data"]["index"] == 0
        assert result["data"]["item"] == 0

    @pytest.mark.asyncio
    async def test_for_range_custom_step(self, execution_context):
        """Test ForLoopStartNode with custom step."""
        node = ForLoopStartNode(node_id="test_for_step")
        node.config["start"] = 0
        node.config["end"] = 10
        node.config["step"] = 2

        # First iteration
        result = await node.execute(execution_context)
        assert result["data"]["item"] == 0

        # Second iteration
        result = await node.execute(execution_context)
        assert result["data"]["item"] == 2

    @pytest.mark.asyncio
    async def test_for_list_iteration(self, execution_context):
        """Test ForLoopStartNode with list input."""
        node = ForLoopStartNode(node_id="test_for_list")
        node.set_input_value("items", ["apple", "banana", "cherry"])

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "body" in result["next_nodes"]
        assert result["data"]["index"] == 0
        assert result["data"]["item"] == "apple"

    @pytest.mark.asyncio
    async def test_for_loop_completion(self, execution_context):
        """Test ForLoopStartNode completes after all iterations."""
        node = ForLoopStartNode(node_id="test_for_complete")
        node.set_input_value("items", [1, 2])

        # First iteration
        result = await node.execute(execution_context)
        assert "body" in result["next_nodes"]

        # Second iteration
        result = await node.execute(execution_context)
        assert "body" in result["next_nodes"]

        # Completion
        result = await node.execute(execution_context)
        assert "completed" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_for_empty_list(self, execution_context):
        """Test ForLoopStartNode with empty list."""
        node = ForLoopStartNode(node_id="test_for_empty")
        node.set_input_value("items", [])

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "completed" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_for_single_item(self, execution_context):
        """Test ForLoopStartNode with single item."""
        node = ForLoopStartNode(node_id="test_for_single")
        node.set_input_value("items", ["only"])

        # First iteration
        result = await node.execute(execution_context)
        assert result["data"]["item"] == "only"
        assert "body" in result["next_nodes"]

        # Completion
        result = await node.execute(execution_context)
        assert "completed" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_for_string_converted_to_list(self, execution_context):
        """Test ForLoopStartNode with string input (treated as single item)."""
        node = ForLoopStartNode(node_id="test_for_string")
        node.set_input_value("items", "hello")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["item"] == "hello"

    @pytest.mark.asyncio
    async def test_for_output_values(self, execution_context):
        """Test ForLoopStartNode sets output values correctly."""
        node = ForLoopStartNode(node_id="test_for_outputs")
        node.set_input_value("items", [10, 20, 30])

        await node.execute(execution_context)

        assert node.get_output_value("current_item") == 10
        assert node.get_output_value("current_index") == 0

    @pytest.mark.asyncio
    async def test_for_with_end_input(self, execution_context):
        """Test ForLoopStartNode with end value from input."""
        node = ForLoopStartNode(node_id="test_for_end_input")
        node.set_input_value("end", 5)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["remaining"] == 4  # 5 items total, first done

    def test_for_node_ports(self):
        """Test ForLoopStartNode has correct ports."""
        node = ForLoopStartNode(node_id="test_ports")
        input_ports = [p.name for p in node.input_ports.values()]
        output_ports = [p.name for p in node.output_ports.values()]

        assert "exec_in" in input_ports
        assert "items" in input_ports
        assert "end" in input_ports
        assert "body" in output_ports
        assert "completed" in output_ports
        assert "current_item" in output_ports
        assert "current_index" in output_ports

    def test_for_node_type(self):
        """Test ForLoopStartNode has correct type."""
        node = ForLoopStartNode(node_id="test_type")
        assert node.node_type == "ForLoopStartNode"
        assert node.name == "For Loop Start"


# =============================================================================
# ForLoopEndNode Tests
# =============================================================================


class TestForLoopEndNode:
    """Tests for ForLoopEndNode loop control."""

    @pytest.mark.asyncio
    async def test_for_end_loops_back(self, execution_context):
        """Test ForLoopEndNode loops back when items remain."""
        # Set up loop state
        loop_state_key = "test_loop_start_loop_state"
        execution_context.variables[loop_state_key] = {
            "items": [1, 2, 3],
            "index": 1,
        }

        end_node = ForLoopEndNode(node_id="test_for_end")
        end_node.set_paired_start("test_loop_start")

        result = await end_node.execute(execution_context)

        assert result["success"] is True
        assert result.get("loop_back_to") == "test_loop_start"

    @pytest.mark.asyncio
    async def test_for_end_completes(self, execution_context):
        """Test ForLoopEndNode goes to exec_out when loop completes."""
        # No loop state means loop completed
        end_node = ForLoopEndNode(node_id="test_for_end_done")
        end_node.set_paired_start("test_loop_start")

        result = await end_node.execute(execution_context)

        assert result["success"] is True
        assert "exec_out" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_for_end_no_paired_start(self, execution_context):
        """Test ForLoopEndNode handles missing paired start."""
        end_node = ForLoopEndNode(node_id="test_for_end_orphan")
        # No paired_start_id set

        result = await end_node.execute(execution_context)

        assert result["success"] is True
        assert "exec_out" in result["next_nodes"]

    def test_for_end_set_paired_start(self):
        """Test ForLoopEndNode.set_paired_start method."""
        end_node = ForLoopEndNode(node_id="test_end")
        end_node.set_paired_start("my_start_node")

        assert end_node.paired_start_id == "my_start_node"
        assert end_node.config["paired_start_id"] == "my_start_node"

    def test_for_end_node_type(self):
        """Test ForLoopEndNode has correct type."""
        node = ForLoopEndNode(node_id="test_type")
        assert node.node_type == "ForLoopEndNode"
        assert node.name == "For Loop End"


# =============================================================================
# WhileLoopStartNode Tests
# =============================================================================


class TestWhileLoopStartNode:
    """Tests for WhileLoopStartNode iteration control."""

    @pytest.mark.asyncio
    async def test_while_enters_body_true(self, execution_context):
        """Test WhileLoopStartNode enters body when condition is true."""
        node = WhileLoopStartNode(node_id="test_while")
        node.set_input_value("condition", True)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "body" in result["next_nodes"]
        assert "completed" not in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_while_skips_body_false(self, execution_context):
        """Test WhileLoopStartNode skips body when condition is false."""
        node = WhileLoopStartNode(node_id="test_while_false")
        node.set_input_value("condition", False)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "completed" in result["next_nodes"]
        assert "body" not in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_while_with_expression(self, execution_context):
        """Test WhileLoopStartNode with expression condition."""
        execution_context.variables["counter"] = 0

        node = WhileLoopStartNode(node_id="test_while_expr")
        node.config["expression"] = "counter < 5"

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "body" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_while_max_iterations(self, execution_context):
        """Test WhileLoopStartNode respects max_iterations."""
        node = WhileLoopStartNode(node_id="test_while_max")
        node.set_input_value("condition", True)
        node.config["max_iterations"] = 3

        # Run iterations until max
        for i in range(3):
            result = await node.execute(execution_context)
            assert "body" in result["next_nodes"]

        # Next should be completed due to max iterations
        result = await node.execute(execution_context)
        assert "completed" in result["next_nodes"]
        assert result["data"]["reason"] == "max_iterations"

    @pytest.mark.asyncio
    async def test_while_iteration_output(self, execution_context):
        """Test WhileLoopStartNode sets current_iteration output."""
        node = WhileLoopStartNode(node_id="test_while_iter")
        node.set_input_value("condition", True)

        await node.execute(execution_context)
        assert node.get_output_value("current_iteration") == 0

        await node.execute(execution_context)
        assert node.get_output_value("current_iteration") == 1

    @pytest.mark.asyncio
    async def test_while_no_condition_defaults_false(self, execution_context):
        """Test WhileLoopStartNode defaults to false without condition."""
        node = WhileLoopStartNode(node_id="test_while_no_cond")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "completed" in result["next_nodes"]

    def test_while_node_ports(self):
        """Test WhileLoopStartNode has correct ports."""
        node = WhileLoopStartNode(node_id="test_ports")
        input_ports = [p.name for p in node.input_ports.values()]
        output_ports = [p.name for p in node.output_ports.values()]

        assert "exec_in" in input_ports
        assert "condition" in input_ports
        assert "body" in output_ports
        assert "completed" in output_ports
        assert "current_iteration" in output_ports

    def test_while_node_type(self):
        """Test WhileLoopStartNode has correct type."""
        node = WhileLoopStartNode(node_id="test_type")
        assert node.node_type == "WhileLoopStartNode"
        assert node.name == "While Loop Start"


# =============================================================================
# WhileLoopEndNode Tests
# =============================================================================


class TestWhileLoopEndNode:
    """Tests for WhileLoopEndNode loop control."""

    @pytest.mark.asyncio
    async def test_while_end_loops_back(self, execution_context):
        """Test WhileLoopEndNode loops back when not completed."""
        # Set up loop state
        loop_state_key = "test_while_start_loop_state"
        execution_context.variables[loop_state_key] = {"iteration": 1}

        end_node = WhileLoopEndNode(node_id="test_while_end")
        end_node.set_paired_start("test_while_start")

        result = await end_node.execute(execution_context)

        assert result["success"] is True
        assert result.get("loop_back_to") == "test_while_start"

    @pytest.mark.asyncio
    async def test_while_end_completes(self, execution_context):
        """Test WhileLoopEndNode goes to exec_out when loop completes."""
        # No loop state means loop completed
        end_node = WhileLoopEndNode(node_id="test_while_end_done")
        end_node.set_paired_start("test_while_start")

        result = await end_node.execute(execution_context)

        assert result["success"] is True
        assert "exec_out" in result["next_nodes"]

    def test_while_end_set_paired_start(self):
        """Test WhileLoopEndNode.set_paired_start method."""
        end_node = WhileLoopEndNode(node_id="test_end")
        end_node.set_paired_start("my_while_start")

        assert end_node.paired_start_id == "my_while_start"
        assert end_node.config["paired_start_id"] == "my_while_start"

    def test_while_end_node_type(self):
        """Test WhileLoopEndNode has correct type."""
        node = WhileLoopEndNode(node_id="test_type")
        assert node.node_type == "WhileLoopEndNode"
        assert node.name == "While Loop End"


# =============================================================================
# SwitchNode Tests
# =============================================================================


class TestSwitchNode:
    """Tests for SwitchNode multi-way branching."""

    @pytest.mark.asyncio
    async def test_switch_matches_first_case(self, execution_context):
        """Test SwitchNode routes to first matching case."""
        node = SwitchNode(
            node_id="test_switch", config={"cases": ["apple", "banana", "cherry"]}
        )
        node.set_input_value("value", "apple")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "case_apple" in result["next_nodes"]
        assert result["data"]["matched_case"] == "apple"

    @pytest.mark.asyncio
    async def test_switch_matches_middle_case(self, execution_context):
        """Test SwitchNode routes to middle case."""
        node = SwitchNode(node_id="test_switch", config={"cases": ["a", "b", "c"]})
        node.set_input_value("value", "b")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "case_b" in result["next_nodes"]
        assert result["data"]["matched_case"] == "b"

    @pytest.mark.asyncio
    async def test_switch_default_no_match(self, execution_context):
        """Test SwitchNode routes to default when no match."""
        node = SwitchNode(node_id="test_switch", config={"cases": ["apple", "banana"]})
        node.set_input_value("value", "orange")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "default" in result["next_nodes"]
        assert result["data"]["matched_case"] == "default"

    @pytest.mark.asyncio
    async def test_switch_numeric_cases(self, execution_context):
        """Test SwitchNode with numeric case values."""
        node = SwitchNode(node_id="test_switch", config={"cases": [1, 2, 3]})
        node.set_input_value("value", 2)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "case_2" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_switch_empty_cases(self, execution_context):
        """Test SwitchNode with no cases defined."""
        node = SwitchNode(node_id="test_switch", config={"cases": []})
        node.set_input_value("value", "anything")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "default" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_switch_none_value(self, execution_context):
        """Test SwitchNode with None value."""
        node = SwitchNode(node_id="test_switch", config={"cases": ["a", "b"]})
        node.set_input_value("value", None)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "default" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_switch_with_expression(self, execution_context):
        """Test SwitchNode evaluates expression for value."""
        execution_context.variables["status"] = "success"

        node = SwitchNode(
            node_id="test_switch", config={"cases": ["success", "error", "pending"]}
        )
        node.config["expression"] = "status"

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "case_success" in result["next_nodes"]

    def test_switch_node_ports(self):
        """Test SwitchNode has correct ports."""
        node = SwitchNode(node_id="test_ports", config={"cases": ["a", "b"]})
        output_ports = [p.name for p in node.output_ports.values()]

        assert "case_a" in output_ports
        assert "case_b" in output_ports
        assert "default" in output_ports

    def test_switch_node_type(self):
        """Test SwitchNode has correct type."""
        node = SwitchNode(node_id="test_type")
        assert node.node_type == "SwitchNode"
        assert node.name == "Switch"


# =============================================================================
# BreakNode Tests
# =============================================================================


class TestBreakNode:
    """Tests for BreakNode loop exit control."""

    @pytest.mark.asyncio
    async def test_break_signals_break(self, execution_context):
        """Test BreakNode signals break control flow."""
        node = BreakNode(node_id="test_break")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["control_flow"] == "break"
        assert "exec_out" in result["next_nodes"]

    def test_break_node_ports(self):
        """Test BreakNode has correct ports."""
        node = BreakNode(node_id="test_ports")
        input_ports = [p.name for p in node.input_ports.values()]
        output_ports = [p.name for p in node.output_ports.values()]

        assert "exec_in" in input_ports
        assert "exec_out" in output_ports

    def test_break_node_type(self):
        """Test BreakNode has correct type."""
        node = BreakNode(node_id="test_type")
        assert node.node_type == "BreakNode"
        assert node.name == "Break"


# =============================================================================
# ContinueNode Tests
# =============================================================================


class TestContinueNode:
    """Tests for ContinueNode iteration skip control."""

    @pytest.mark.asyncio
    async def test_continue_signals_continue(self, execution_context):
        """Test ContinueNode signals continue control flow."""
        node = ContinueNode(node_id="test_continue")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["control_flow"] == "continue"
        assert "exec_out" in result["next_nodes"]

    def test_continue_node_ports(self):
        """Test ContinueNode has correct ports."""
        node = ContinueNode(node_id="test_ports")
        input_ports = [p.name for p in node.input_ports.values()]
        output_ports = [p.name for p in node.output_ports.values()]

        assert "exec_in" in input_ports
        assert "exec_out" in output_ports

    def test_continue_node_type(self):
        """Test ContinueNode has correct type."""
        node = ContinueNode(node_id="test_type")
        assert node.node_type == "ContinueNode"
        assert node.name == "Continue"


# =============================================================================
# Integration Tests
# =============================================================================


class TestControlFlowIntegration:
    """Integration tests for control flow node patterns."""

    @pytest.mark.asyncio
    async def test_for_loop_complete_cycle(self, execution_context):
        """Test complete For Loop cycle with start and end nodes."""
        start_node = ForLoopStartNode(node_id="loop_start")
        end_node = ForLoopEndNode(node_id="loop_end")
        end_node.set_paired_start("loop_start")

        start_node.set_input_value("items", ["a", "b"])

        # First iteration
        result = await start_node.execute(execution_context)
        assert result["data"]["item"] == "a"

        result = await end_node.execute(execution_context)
        assert result.get("loop_back_to") == "loop_start"

        # Second iteration
        result = await start_node.execute(execution_context)
        assert result["data"]["item"] == "b"

        result = await end_node.execute(execution_context)
        assert result.get("loop_back_to") == "loop_start"

        # Completion
        result = await start_node.execute(execution_context)
        assert "completed" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_while_loop_with_condition_change(self, execution_context):
        """Test While Loop with condition change during iteration."""
        execution_context.variables["count"] = 0

        start_node = WhileLoopStartNode(node_id="while_start")
        start_node.config["expression"] = "count < 2"

        # First iteration - count=0
        result = await start_node.execute(execution_context)
        assert "body" in result["next_nodes"]

        # Simulate body execution
        execution_context.variables["count"] = 1

        # Second iteration - count=1
        result = await start_node.execute(execution_context)
        assert "body" in result["next_nodes"]

        # Simulate body execution
        execution_context.variables["count"] = 2

        # Third iteration - count=2, condition false
        result = await start_node.execute(execution_context)
        assert "completed" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_nested_if_conditions(self, execution_context):
        """Test nested If conditions."""
        execution_context.variables["a"] = 5
        execution_context.variables["b"] = 10

        outer_if = IfNode(node_id="outer_if")
        outer_if.config["expression"] = "a > 0"

        inner_if = IfNode(node_id="inner_if")
        inner_if.config["expression"] = "b > a"

        outer_result = await outer_if.execute(execution_context)
        assert "true" in outer_result["next_nodes"]

        inner_result = await inner_if.execute(execution_context)
        assert "true" in inner_result["next_nodes"]

    @pytest.mark.asyncio
    async def test_switch_in_for_loop(self, execution_context):
        """Test Switch node inside a For loop."""
        start_node = ForLoopStartNode(node_id="loop_start")
        start_node.set_input_value("items", ["success", "error", "pending"])

        switch_node = SwitchNode(
            node_id="switch_in_loop", config={"cases": ["success", "error"]}
        )

        # First iteration - success
        result = await start_node.execute(execution_context)
        switch_node.set_input_value("value", result["data"]["item"])
        switch_result = await switch_node.execute(execution_context)
        assert "case_success" in switch_result["next_nodes"]

        # Second iteration - error
        result = await start_node.execute(execution_context)
        switch_node.set_input_value("value", result["data"]["item"])
        switch_result = await switch_node.execute(execution_context)
        assert "case_error" in switch_result["next_nodes"]

        # Third iteration - pending (default)
        result = await start_node.execute(execution_context)
        switch_node.set_input_value("value", result["data"]["item"])
        switch_result = await switch_node.execute(execution_context)
        assert "default" in switch_result["next_nodes"]

    @pytest.mark.asyncio
    async def test_while_loop_complete_cycle(self, execution_context):
        """Test complete While Loop cycle with start and end nodes."""
        execution_context.variables["counter"] = 0

        start_node = WhileLoopStartNode(node_id="while_start")
        start_node.config["expression"] = "counter < 2"

        end_node = WhileLoopEndNode(node_id="while_end")
        end_node.set_paired_start("while_start")

        # First iteration
        result = await start_node.execute(execution_context)
        assert "body" in result["next_nodes"]

        execution_context.variables["counter"] = 1
        result = await end_node.execute(execution_context)
        assert result.get("loop_back_to") == "while_start"

        # Second iteration
        result = await start_node.execute(execution_context)
        assert "body" in result["next_nodes"]

        execution_context.variables["counter"] = 2
        result = await end_node.execute(execution_context)
        assert result.get("loop_back_to") == "while_start"

        # Completion
        result = await start_node.execute(execution_context)
        assert "completed" in result["next_nodes"]


# =============================================================================
# Additional Edge Case Tests
# =============================================================================


class TestControlFlowEdgeCases:
    """Additional edge case tests for control flow nodes."""

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

    @pytest.mark.asyncio
    async def test_if_complex_expression(self, execution_context):
        """Test IfNode with complex expression."""
        execution_context.variables["x"] = 10
        execution_context.variables["y"] = 20

        node = IfNode(node_id="test_complex")
        node.config["expression"] = "(x + y) > 25 and x < y"

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["condition"] is True
        assert "true" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_if_unsafe_expression_rejected(self, execution_context):
        """Test IfNode rejects unsafe expressions."""
        node = IfNode(node_id="test_unsafe")
        node.config["expression"] = "__import__('os').system('echo bad')"

        result = await node.execute(execution_context)

        # Should fail safely and default to false
        assert result["success"] is True
        assert result["data"]["condition"] is False
        assert "false" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_for_loop_negative_step(self, execution_context):
        """Test ForLoopStartNode with negative step (countdown)."""
        node = ForLoopStartNode(node_id="test_countdown")
        node.config["start"] = 5
        node.config["end"] = 0
        node.config["step"] = -1

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["item"] == 5
        assert "body" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_for_loop_dict_items(self, execution_context):
        """Test ForLoopStartNode with dictionary (iterates keys)."""
        node = ForLoopStartNode(node_id="test_dict")
        node.set_input_value("items", {"a": 1, "b": 2, "c": 3})

        result = await node.execute(execution_context)

        assert result["success"] is True
        # Dict iteration gives keys
        assert result["data"]["item"] in ["a", "b", "c"]

    @pytest.mark.asyncio
    async def test_for_loop_tuple_items(self, execution_context):
        """Test ForLoopStartNode with tuple input."""
        node = ForLoopStartNode(node_id="test_tuple")
        node.set_input_value("items", (100, 200, 300))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["item"] == 100

    @pytest.mark.asyncio
    async def test_for_loop_set_items(self, execution_context):
        """Test ForLoopStartNode with set input."""
        node = ForLoopStartNode(node_id="test_set")
        node.set_input_value("items", {1, 2, 3})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["item"] in [1, 2, 3]

    @pytest.mark.asyncio
    async def test_for_loop_generator(self, execution_context):
        """Test ForLoopStartNode with generator input."""
        node = ForLoopStartNode(node_id="test_gen")

        def gen():
            yield 10
            yield 20

        node.set_input_value("items", gen())

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["item"] == 10

    @pytest.mark.asyncio
    async def test_while_loop_invalid_expression(self, execution_context):
        """Test WhileLoopStartNode with invalid expression."""
        node = WhileLoopStartNode(node_id="test_invalid")
        node.config["expression"] = "undefined_var > 5"

        result = await node.execute(execution_context)

        assert result["success"] is True
        # Invalid expression defaults to false
        assert "completed" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_while_loop_expression_with_list(self, execution_context):
        """Test WhileLoopStartNode with list length expression."""
        execution_context.variables["items"] = [1, 2, 3]

        node = WhileLoopStartNode(node_id="test_list_expr")
        node.config["expression"] = "len(items) > 0"

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "body" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_switch_boolean_cases(self, execution_context):
        """Test SwitchNode with boolean case values."""
        node = SwitchNode(node_id="test_bool", config={"cases": [True, False]})
        node.set_input_value("value", True)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "case_True" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_switch_case_sensitive(self, execution_context):
        """Test SwitchNode is case sensitive."""
        node = SwitchNode(node_id="test_case", config={"cases": ["Apple", "apple"]})
        node.set_input_value("value", "apple")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "case_apple" in result["next_nodes"]
        assert result["data"]["matched_case"] == "apple"

    @pytest.mark.asyncio
    async def test_switch_whitespace_value(self, execution_context):
        """Test SwitchNode handles whitespace values."""
        node = SwitchNode(node_id="test_ws", config={"cases": ["  ", "a"]})
        node.set_input_value("value", "  ")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "case_  " in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_break_node_status(self, execution_context):
        """Test BreakNode sets correct node status."""
        from casare_rpa.domain.value_objects.types import NodeStatus

        node = BreakNode(node_id="test_break_status")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_continue_node_status(self, execution_context):
        """Test ContinueNode sets correct node status."""
        from casare_rpa.domain.value_objects.types import NodeStatus

        node = ContinueNode(node_id="test_continue_status")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_for_loop_large_iteration(self, execution_context):
        """Test ForLoopStartNode with large iteration count."""
        node = ForLoopStartNode(node_id="test_large")
        node.config["start"] = 0
        node.config["end"] = 1000
        node.config["step"] = 1

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["remaining"] == 999

    @pytest.mark.asyncio
    async def test_while_loop_max_iterations_one(self, execution_context):
        """Test WhileLoopStartNode with max_iterations=1 runs once then completes."""
        node = WhileLoopStartNode(node_id="test_one_max")
        node.set_input_value("condition", True)
        node.config["max_iterations"] = 1

        # First execution enters body (iteration 0)
        result = await node.execute(execution_context)
        assert result["success"] is True
        assert "body" in result["next_nodes"]

        # Second execution hits max (iteration 1 >= max_iterations 1)
        result = await node.execute(execution_context)
        assert result["success"] is True
        assert "completed" in result["next_nodes"]
        assert result["data"]["reason"] == "max_iterations"

    @pytest.mark.asyncio
    async def test_for_end_with_config_paired_id(self, execution_context):
        """Test ForLoopEndNode reads paired_start_id from config."""
        # Set up loop state
        loop_state_key = "config_start_loop_state"
        execution_context.variables[loop_state_key] = {"items": [1], "index": 0}

        end_node = ForLoopEndNode(
            node_id="test_config_end", config={"paired_start_id": "config_start"}
        )

        result = await end_node.execute(execution_context)

        assert result["success"] is True
        assert result.get("loop_back_to") == "config_start"

    @pytest.mark.asyncio
    async def test_while_end_no_paired_start(self, execution_context):
        """Test WhileLoopEndNode handles missing paired start."""
        end_node = WhileLoopEndNode(node_id="test_orphan_while")
        # No paired_start_id set

        result = await end_node.execute(execution_context)

        assert result["success"] is True
        assert "exec_out" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_if_with_none_input(self, execution_context):
        """Test IfNode with explicit None input."""
        node = IfNode(node_id="test_none")
        node.set_input_value("condition", None)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["condition"] is False
        assert "false" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_switch_zero_value(self, execution_context):
        """Test SwitchNode with 0 value matching."""
        node = SwitchNode(node_id="test_zero", config={"cases": [0, 1, 2]})
        node.set_input_value("value", 0)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "case_0" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_for_loop_state_cleanup_on_error(self, execution_context):
        """Test ForLoopStartNode cleans up state on error."""
        node = ForLoopStartNode(node_id="test_error_cleanup")
        # Provide invalid end value that will cause error during range()
        node.config["start"] = 0
        node.config["end"] = "not_a_number"  # Will cause int() error

        result = await node.execute(execution_context)

        assert result["success"] is False
        # Loop state should be cleaned up
        loop_state_key = f"{node.node_id}_loop_state"
        assert loop_state_key not in execution_context.variables

    @pytest.mark.asyncio
    async def test_if_node_execution_result_pattern(self, execution_context):
        """Test IfNode returns proper ExecutionResult structure."""
        node = IfNode(node_id="test_pattern")
        node.set_input_value("condition", True)

        result = await node.execute(execution_context)

        # Verify ExecutionResult structure
        assert "success" in result
        assert "data" in result
        assert "next_nodes" in result
        assert isinstance(result["success"], bool)
        assert isinstance(result["data"], dict)
        assert isinstance(result["next_nodes"], list)

    @pytest.mark.asyncio
    async def test_for_loop_execution_result_pattern(self, execution_context):
        """Test ForLoopStartNode returns proper ExecutionResult structure."""
        node = ForLoopStartNode(node_id="test_for_pattern")
        node.set_input_value("items", [1, 2, 3])

        result = await node.execute(execution_context)

        # Verify ExecutionResult structure
        assert "success" in result
        assert "data" in result
        assert "next_nodes" in result
        assert "item" in result["data"]
        assert "index" in result["data"]
        assert "remaining" in result["data"]

    @pytest.mark.asyncio
    async def test_while_loop_execution_result_pattern(self, execution_context):
        """Test WhileLoopStartNode returns proper ExecutionResult structure."""
        node = WhileLoopStartNode(node_id="test_while_pattern")
        node.set_input_value("condition", True)

        result = await node.execute(execution_context)

        # Verify ExecutionResult structure
        assert "success" in result
        assert "data" in result
        assert "next_nodes" in result
        assert "iteration" in result["data"]

    @pytest.mark.asyncio
    async def test_switch_execution_result_pattern(self, execution_context):
        """Test SwitchNode returns proper ExecutionResult structure."""
        node = SwitchNode(node_id="test_switch_pattern", config={"cases": ["a", "b"]})
        node.set_input_value("value", "a")

        result = await node.execute(execution_context)

        # Verify ExecutionResult structure
        assert "success" in result
        assert "data" in result
        assert "next_nodes" in result
        assert "matched_case" in result["data"]
        assert "value" in result["data"]

    @pytest.mark.asyncio
    async def test_break_execution_result_pattern(self, execution_context):
        """Test BreakNode returns proper ExecutionResult structure."""
        node = BreakNode(node_id="test_break_pattern")

        result = await node.execute(execution_context)

        # Verify ExecutionResult structure
        assert "success" in result
        assert "control_flow" in result
        assert "next_nodes" in result
        assert result["control_flow"] == "break"

    @pytest.mark.asyncio
    async def test_continue_execution_result_pattern(self, execution_context):
        """Test ContinueNode returns proper ExecutionResult structure."""
        node = ContinueNode(node_id="test_continue_pattern")

        result = await node.execute(execution_context)

        # Verify ExecutionResult structure
        assert "success" in result
        assert "control_flow" in result
        assert "next_nodes" in result
        assert result["control_flow"] == "continue"
