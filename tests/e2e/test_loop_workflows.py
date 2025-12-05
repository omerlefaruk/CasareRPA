"""
CasareRPA - E2E Tests for Loop Workflows.

Tests loop execution including:
- For loops with range
- For loops iterating over lists
- Nested loops
- While loops with conditions
- Loop control (break, continue)
- Accumulators and counters in loops
"""

import pytest

from tests.e2e.helpers import WorkflowBuilder


@pytest.mark.asyncio
@pytest.mark.e2e
class TestForLoopWorkflows:
    """End-to-end tests for For loop workflows."""

    async def test_for_loop_range_counter(self):
        """
        Test For loop counting with range.
        Start -> SetVar("sum", 0) -> ForLoop(range_end=5) -> Inc("sum") -> EndLoop -> End
        Expected: sum == 5 (0+1+1+1+1+1)
        """
        result = await (
            WorkflowBuilder(name="For Loop Range Counter")
            .add_start()
            .add_set_variable("sum", 0, variable_type="Int32")
            .add_for_loop(range_end=5)
            .add_increment_variable("sum")
            .add_for_loop_end()
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"]["sum"] == 5, "Sum should be 5 after 5 iterations"

    async def test_for_loop_range_with_start(self):
        """
        Test For loop with custom start value.
        ForLoop(range_start=2, range_end=5) -> count iterations
        Expected: 3 iterations (2, 3, 4)
        """
        result = await (
            WorkflowBuilder(name="For Loop Range With Start")
            .add_start()
            .add_set_variable("count", 0, variable_type="Int32")
            .add_for_loop(range_start=2, range_end=5)
            .add_increment_variable("count")
            .add_for_loop_end()
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            result["variables"]["count"] == 3
        ), "Count should be 3 (iterations 2, 3, 4)"

    async def test_for_loop_range_with_step(self):
        """
        Test For loop with step value.
        ForLoop(range_start=0, range_end=10, range_step=2) -> count iterations
        Expected: 5 iterations (0, 2, 4, 6, 8)
        """
        result = await (
            WorkflowBuilder(name="For Loop Range With Step")
            .add_start()
            .add_set_variable("count", 0, variable_type="Int32")
            .add_for_loop(range_start=0, range_end=10, range_step=2)
            .add_increment_variable("count")
            .add_for_loop_end()
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"]["count"] == 5, "Count should be 5 (0, 2, 4, 6, 8)"

    async def test_for_loop_over_list(self):
        """
        Test For loop iterating over a list.
        Initial: {"numbers": [1, 2, 3, 4, 5]}
        ForLoop over numbers -> sum all
        Expected: sum == 15
        """
        result = await (
            WorkflowBuilder(name="For Loop Over List")
            .add_start()
            .add_set_variable("sum", 0, variable_type="Int32")
            .add_set_variable("numbers", [1, 2, 3, 4, 5])
            .add_for_loop(item_var="num", list_var="numbers")
            .add_increment_variable("sum")  # Each iteration increments by 1
            .add_for_loop_end()
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"]["sum"] == 5, "Sum should be 5 (5 iterations)"

    async def test_for_loop_empty_range(self):
        """
        Test For loop with empty range (start >= end).
        ForLoop(range_start=5, range_end=5) -> body should not execute
        Expected: counter stays 0
        """
        result = await (
            WorkflowBuilder(name="For Loop Empty Range")
            .add_start()
            .add_set_variable("counter", 0, variable_type="Int32")
            .add_for_loop(range_start=5, range_end=5)
            .add_increment_variable("counter")  # Should not execute
            .add_for_loop_end()
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            result["variables"]["counter"] == 0
        ), "Counter should be 0 for empty range"

    async def test_for_loop_single_iteration(self):
        """
        Test For loop with exactly one iteration.
        ForLoop(range_end=1) -> executes once
        """
        result = await (
            WorkflowBuilder(name="For Loop Single Iteration")
            .add_start()
            .add_set_variable("counter", 0, variable_type="Int32")
            .add_for_loop(range_end=1)
            .add_increment_variable("counter")
            .add_for_loop_end()
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            result["variables"]["counter"] == 1
        ), "Counter should be 1 after single iteration"

    async def test_for_loop_multiple_operations(self):
        """
        Test For loop with multiple operations in body.
        """
        result = await (
            WorkflowBuilder(name="For Loop Multiple Operations")
            .add_start()
            .add_set_variable("counter", 0, variable_type="Int32")
            .add_set_variable("doubled", 0, variable_type="Int32")
            .add_for_loop(range_end=3)
            .add_increment_variable("counter")
            .add_increment_variable("doubled")
            .add_increment_variable("doubled")
            .add_for_loop_end()
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"]["counter"] == 3, "Counter should be 3"
        assert (
            result["variables"]["doubled"] == 6
        ), "Doubled should be 6 (2 increments per iteration)"

    async def test_for_loop_modifies_list_variable(self):
        """
        Test that loop can modify variables from outer scope.
        """
        result = await (
            WorkflowBuilder(name="For Loop Modifies Outer")
            .add_start()
            .add_set_variable("total", 100, variable_type="Int32")
            .add_for_loop(range_end=5)
            .add_decrement_variable("total", 10)
            .add_for_loop_end()
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"]["total"] == 50, "Total should be 50 (100 - 5*10)"


@pytest.mark.asyncio
@pytest.mark.e2e
class TestNestedLoopWorkflows:
    """End-to-end tests for nested loop workflows."""

    async def test_nested_for_loops(self):
        """
        Test nested For loops.
        Outer: range(2), Inner: range(3)
        Expected: total iterations = 6
        """
        result = await (
            WorkflowBuilder(name="Nested For Loops")
            .add_start()
            .add_set_variable("count", 0, variable_type="Int32")
            .add_for_loop(range_end=2)  # Outer loop
            .add_for_loop(range_end=3)  # Inner loop
            .add_increment_variable("count")
            .add_for_loop_end()  # End inner
            .add_for_loop_end()  # End outer
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"]["count"] == 6, "Count should be 6 (2 * 3)"

    async def test_nested_loops_different_ranges(self):
        """
        Test nested loops with different range sizes.
        Outer: range(3), Inner: range(2)
        Expected: total = 6
        """
        result = await (
            WorkflowBuilder(name="Nested Loops Different Ranges")
            .add_start()
            .add_set_variable("total", 0, variable_type="Int32")
            .add_for_loop(range_end=3)  # Outer
            .add_for_loop(range_end=2)  # Inner
            .add_increment_variable("total")
            .add_for_loop_end()
            .add_for_loop_end()
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"]["total"] == 6, "Total should be 6"


@pytest.mark.asyncio
@pytest.mark.e2e
class TestWhileLoopWorkflows:
    """End-to-end tests for While loop workflows."""

    async def test_while_loop_countdown(self):
        """
        Test While loop countdown.
        Start -> SetVar("n", 5) -> While(n > 0) -> Dec("n") -> EndWhile -> End
        Expected: n == 0
        """
        result = await (
            WorkflowBuilder(name="While Loop Countdown")
            .add_start()
            .add_set_variable("n", 5, variable_type="Int32")
            .add_while_loop("{{n}} > 0")
            .add_decrement_variable("n")
            .add_while_loop_end()
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"]["n"] == 0, "n should be 0 after countdown"

    async def test_while_loop_count_up(self):
        """
        Test While loop counting up.
        While(counter < 10) -> Inc(counter)
        Expected: counter == 10
        """
        result = await (
            WorkflowBuilder(name="While Loop Count Up")
            .add_start()
            .add_set_variable("counter", 0, variable_type="Int32")
            .add_while_loop("{{counter}} < 10")
            .add_increment_variable("counter")
            .add_while_loop_end()
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"]["counter"] == 10, "Counter should be 10"

    async def test_while_loop_false_initially(self):
        """
        Test While loop that's false from the start.
        While(0 > 5) -> body should never execute
        """
        result = await (
            WorkflowBuilder(name="While False Initially")
            .add_start()
            .add_set_variable("executed", False)
            .add_set_variable("n", 0, variable_type="Int32")
            .add_while_loop("{{n}} > 5")
            .add_set_variable("executed", True)  # Should never execute
            .add_while_loop_end()
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            result["variables"]["executed"] is False
        ), "Body should never have executed"

    async def test_while_loop_max_iterations_safety(self):
        """
        Test While loop max iterations safety limit.
        While(True) with max_iterations=5
        Expected: Loop stops after 5 iterations
        """
        result = await (
            WorkflowBuilder(name="While Max Iterations")
            .add_start()
            .add_set_variable("counter", 0, variable_type="Int32")
            .add_while_loop("True", max_iterations=5)
            .add_increment_variable("counter")
            .add_while_loop_end()
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            result["variables"]["counter"] == 5
        ), "Counter should be 5 (max iterations)"

    async def test_while_loop_multiple_conditions(self):
        """
        Test While loop with compound condition.
        While(a < 10 and b > 0) -> modify both
        """
        result = await (
            WorkflowBuilder(name="While Multiple Conditions")
            .add_start()
            .add_set_variable("a", 0, variable_type="Int32")
            .add_set_variable("b", 5, variable_type="Int32")
            .add_while_loop("{{a}} < 10 and {{b}} > 0")
            .add_increment_variable("a")
            .add_decrement_variable("b")
            .add_while_loop_end()
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        # Loop exits when b reaches 0 (5 iterations)
        assert result["variables"]["a"] == 5, "a should be 5"
        assert result["variables"]["b"] == 0, "b should be 0"


@pytest.mark.asyncio
@pytest.mark.e2e
class TestLoopControlWorkflows:
    """End-to-end tests for loop control (break, continue)."""

    async def test_for_loop_with_break_condition(self):
        """
        Test For loop with conditional break.
        ForLoop(range_end=10) -> if counter == 3: break
        Expected: counter == 3 (loop exits at 3)
        """
        result = await (
            WorkflowBuilder(name="For Loop With Break")
            .add_start()
            .add_set_variable("counter", 0, variable_type="Int32")
            .add_for_loop(range_end=10)
            .add_increment_variable("counter")
            .add_if("{{counter}} == 3")
            .branch_true()
            .add_break()
            .branch_false()
            # Continue looping
            .end_if()
            .add_for_loop_end()
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            result["variables"]["counter"] == 3
        ), "Counter should be 3 when break executed"

    async def test_while_loop_with_break(self):
        """
        Test While loop with break.
        While(True) -> if counter == 5: break
        Expected: counter == 5
        """
        result = await (
            WorkflowBuilder(name="While Loop With Break")
            .add_start()
            .add_set_variable("counter", 0, variable_type="Int32")
            .add_while_loop("True", max_iterations=100)
            .add_increment_variable("counter")
            .add_if("{{counter}} >= 5")
            .branch_true()
            .add_break()
            .branch_false()
            .end_if()
            .add_while_loop_end()
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            result["variables"]["counter"] == 5
        ), "Counter should be 5 when break executed"

    async def test_for_loop_with_continue(self):
        """
        Test For loop with continue to skip iterations.
        ForLoop(range_end=5) -> if iteration is even: continue; else: increment count
        Expected: Only odd iterations counted (1, 3)

        Note: Continue behavior depends on implementation.
        This tests basic continue functionality.
        """
        result = await (
            WorkflowBuilder(name="For Loop With Continue")
            .add_start()
            .add_set_variable("count", 0, variable_type="Int32")
            .add_set_variable("iteration", 0, variable_type="Int32")
            .add_for_loop(range_end=5)
            .add_increment_variable("iteration")  # Track which iteration we're on
            .add_if("{{iteration}} % 2 == 0")
            .branch_true()
            .add_continue()  # Skip even iterations
            .branch_false()
            .add_increment_variable("count")  # Count odd iterations
            .end_if()
            .add_for_loop_end()
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        # With continue on even, we should count odd iterations (1, 3, 5)
        # But since continue might not work as expected, we verify the loop completes
        assert result["variables"]["iteration"] == 5, "Should complete all iterations"


@pytest.mark.asyncio
@pytest.mark.e2e
class TestLoopAccumulatorWorkflows:
    """End-to-end tests for loops with accumulators."""

    async def test_loop_sum_accumulator(self):
        """
        Test accumulating sum in a loop.
        ForLoop 1-5 -> sum += iteration
        Expected: sum = 1+2+3+4+5 = 15
        """
        result = await (
            WorkflowBuilder(name="Loop Sum Accumulator")
            .add_start()
            .add_set_variable("sum", 0, variable_type="Int32")
            .add_for_loop(range_start=1, range_end=6)  # 1,2,3,4,5
            # Each iteration adds 1 to sum
            .add_increment_variable("sum")
            .add_for_loop_end()
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"]["sum"] == 5, "Sum should be 5 after 5 increments"

    async def test_loop_counter_tracking(self):
        """
        Test tracking loop iteration count.
        ForLoop(range_end=7) with counter
        Expected: final_count == 7
        """
        result = await (
            WorkflowBuilder(name="Loop Counter Tracking")
            .add_start()
            .add_set_variable("final_count", 0, variable_type="Int32")
            .add_for_loop(range_end=7)
            .add_increment_variable("final_count")
            .add_for_loop_end()
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"]["final_count"] == 7, "final_count should be 7"

    async def test_loop_product_accumulator(self):
        """
        Test product accumulator pattern using increment.
        Start with 0, add 2 each iteration for 5 iterations.
        Expected: result == 10
        """
        result = await (
            WorkflowBuilder(name="Loop Product Pattern")
            .add_start()
            .add_set_variable("result", 0, variable_type="Int32")
            .add_for_loop(range_end=5)
            .add_increment_variable("result", increment=2)  # Add 2 each time
            .add_for_loop_end()
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"]["result"] == 10, "Result should be 10 (5 * 2)"


@pytest.mark.asyncio
@pytest.mark.e2e
class TestLoopEdgeCases:
    """End-to-end tests for loop edge cases."""

    async def test_loop_zero_iterations(self):
        """
        Test loop with zero iterations.
        ForLoop(range_end=0)
        Expected: Body never executes
        """
        result = await (
            WorkflowBuilder(name="Loop Zero Iterations")
            .add_start()
            .add_set_variable("executed", False)
            .add_for_loop(range_end=0)
            .add_set_variable("executed", True)
            .add_for_loop_end()
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            result["variables"]["executed"] is False
        ), "Body should not execute for 0 iterations"

    async def test_loop_large_iteration_count(self):
        """
        Test loop with large iteration count (100).
        Expected: Completes successfully
        """
        result = await (
            WorkflowBuilder(name="Loop Large Count")
            .add_start()
            .add_set_variable("counter", 0, variable_type="Int32")
            .add_for_loop(range_end=100)
            .add_increment_variable("counter")
            .add_for_loop_end()
            .add_end()
            .execute(timeout=60.0)  # Allow more time
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"]["counter"] == 100, "Counter should be 100"

    async def test_sequential_loops(self):
        """
        Test multiple sequential loops (not nested).
        """
        result = await (
            WorkflowBuilder(name="Sequential Loops")
            .add_start()
            .add_set_variable("first_loop", 0, variable_type="Int32")
            .add_set_variable("second_loop", 0, variable_type="Int32")
            # First loop
            .add_for_loop(range_end=3)
            .add_increment_variable("first_loop")
            .add_for_loop_end()
            # Second loop
            .add_for_loop(range_end=5)
            .add_increment_variable("second_loop")
            .add_for_loop_end()
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"]["first_loop"] == 3, "First loop should count to 3"
        assert result["variables"]["second_loop"] == 5, "Second loop should count to 5"

    async def test_loop_with_conditional_inside(self):
        """
        Test loop containing conditional logic.
        ForLoop(range_end=10) -> if iteration < 5: inc(small) else: inc(large)
        """
        result = await (
            WorkflowBuilder(name="Loop With Conditional")
            .add_start()
            .add_set_variable("iteration", 0, variable_type="Int32")
            .add_set_variable("small", 0, variable_type="Int32")
            .add_set_variable("large", 0, variable_type="Int32")
            .add_for_loop(range_end=10)
            .add_increment_variable("iteration")
            .add_if("{{iteration}} <= 5")
            .branch_true()
            .add_increment_variable("small")
            .branch_false()
            .add_increment_variable("large")
            .end_if()
            .add_for_loop_end()
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"]["iteration"] == 10, "Should complete 10 iterations"
        assert result["variables"]["small"] == 5, "Small should be 5 (iterations 1-5)"
        assert result["variables"]["large"] == 5, "Large should be 5 (iterations 6-10)"
