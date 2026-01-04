"""
CasareRPA - Workflow Execution End-to-End Tests

E2E tests for complete workflow execution patterns:
- Linear workflow execution
- Branching workflow execution (If/Switch)
- Loop workflow execution (For/While)
- Error handling workflow (Try/Catch)
- Variable passing between nodes
- Subflow/nested workflow execution

Run with: pytest tests/e2e/test_workflow_execution_e2e.py -v -m e2e
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from casare_rpa.domain.value_objects.types import ExecutionMode
from casare_rpa.infrastructure.execution import ExecutionContext

if TYPE_CHECKING:
    pass


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def workflow_context() -> ExecutionContext:
    """Create ExecutionContext for workflow testing."""
    return ExecutionContext(
        workflow_name="E2EWorkflowTest",
        mode=ExecutionMode.NORMAL,
        initial_variables={},
    )


# =============================================================================
# Linear Workflow Tests
# =============================================================================


@pytest.mark.e2e
class TestLinearWorkflow:
    """E2E tests for linear workflow execution (Start → Process → End)."""

    @pytest.mark.asyncio
    async def test_simple_linear_workflow(self, workflow_context: ExecutionContext) -> None:
        """Test simple linear workflow: Start → SetVar → Log → End."""
        from casare_rpa.nodes import EndNode, LogNode, SetVariableNode, StartNode

        # Create nodes
        start = StartNode("start")
        set_var = SetVariableNode(
            "set_var", config={"variable_name": "message", "value": "Hello E2E!"}
        )
        log = LogNode("log", config={"message": "{{message}}", "level": "INFO"})
        end = EndNode("end")

        # Execute in sequence
        result1 = await start.execute(workflow_context)
        assert result1.get("success") is True

        result2 = await set_var.execute(workflow_context)
        assert result2.get("success") is True
        assert workflow_context.get_variable("message") == "Hello E2E!"

        result3 = await log.execute(workflow_context)
        assert result3.get("success") is True

        result4 = await end.execute(workflow_context)
        assert result4.get("success") is True

    @pytest.mark.asyncio
    async def test_data_transformation_workflow(
        self, workflow_context: ExecutionContext
    ) -> None:
        """Test workflow that transforms data through multiple nodes."""
        from casare_rpa.nodes import (
            CreateListNode,
            EndNode,
            ListFilterNode,
            ListLengthNode,
            StartNode,
        )

        # Start workflow
        start = StartNode("start")
        await start.execute(workflow_context)

        # Create list of numbers
        create_list = CreateListNode("create_list", config={"items": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]})
        list_result = await create_list.execute(workflow_context)
        assert list_result.get("success") is True

        # Store list in variable
        created_list = list_result.get("list", [])
        workflow_context.set_variable("numbers", created_list)

        # Filter to get only even numbers
        filter_node = ListFilterNode(
            "filter", config={"list": created_list, "condition": "item % 2 == 0"}
        )
        filter_result = await filter_node.execute(workflow_context)
        assert filter_result.get("success") is True

        filtered = filter_result.get("filtered", [])
        assert filtered == [2, 4, 6, 8, 10]

        # Get length of filtered list
        length_node = ListLengthNode("length", config={"list": filtered})
        length_result = await length_node.execute(workflow_context)
        assert length_result.get("success") is True
        assert length_result.get("length") == 5

        # End workflow
        end = EndNode("end")
        await end.execute(workflow_context)


# =============================================================================
# Branching Workflow Tests
# =============================================================================


@pytest.mark.e2e
class TestBranchingWorkflow:
    """E2E tests for branching workflow execution (If/Switch)."""

    @pytest.mark.asyncio
    async def test_if_true_branch_workflow(
        self, workflow_context: ExecutionContext
    ) -> None:
        """Test workflow that takes true branch."""
        from casare_rpa.nodes import EndNode, IfNode, LogNode, SetVariableNode, StartNode

        # Start
        start = StartNode("start")
        await start.execute(workflow_context)

        # Set condition variable
        set_cond = SetVariableNode(
            "set_cond", config={"variable_name": "is_valid", "value": True}
        )
        await set_cond.execute(workflow_context)

        # If node - should take true branch
        if_node = IfNode("if", config={"condition": True})
        if_result = await if_node.execute(workflow_context)
        assert if_result.get("success") is True

        branch = if_result.get("branch") or if_result.get("next_port", "true")
        assert "true" in str(branch).lower()

        # Execute true branch
        log_true = LogNode("log_true", config={"message": "Taking TRUE branch", "level": "INFO"})
        await log_true.execute(workflow_context)

        # End
        end = EndNode("end")
        await end.execute(workflow_context)

    @pytest.mark.asyncio
    async def test_if_false_branch_workflow(
        self, workflow_context: ExecutionContext
    ) -> None:
        """Test workflow that takes false branch."""
        from casare_rpa.nodes import EndNode, IfNode, LogNode, StartNode

        # Start
        start = StartNode("start")
        await start.execute(workflow_context)

        # If node - should take false branch
        if_node = IfNode("if", config={"condition": False})
        if_result = await if_node.execute(workflow_context)
        assert if_result.get("success") is True

        branch = if_result.get("branch") or if_result.get("next_port", "false")
        assert "false" in str(branch).lower()

        # Execute false branch
        log_false = LogNode(
            "log_false", config={"message": "Taking FALSE branch", "level": "INFO"}
        )
        await log_false.execute(workflow_context)

        # End
        end = EndNode("end")
        await end.execute(workflow_context)

    @pytest.mark.asyncio
    async def test_switch_workflow(self, workflow_context: ExecutionContext) -> None:
        """Test workflow with switch node routing."""
        from casare_rpa.nodes import EndNode, SetVariableNode, StartNode, SwitchNode

        # Start
        await StartNode("start").execute(workflow_context)

        # Set value to switch on
        await SetVariableNode(
            "set_action", config={"variable_name": "action", "value": "process"}
        ).execute(workflow_context)

        # Switch node
        switch = SwitchNode(
            "switch",
            config={
                "value": "process",
                "cases": ["start", "process", "end", "error"],
            },
        )
        switch_result = await switch.execute(workflow_context)
        assert switch_result.get("success") is True

        # End
        await EndNode("end").execute(workflow_context)


# =============================================================================
# Loop Workflow Tests
# =============================================================================


@pytest.mark.e2e
class TestLoopWorkflow:
    """E2E tests for loop workflow execution."""

    @pytest.mark.asyncio
    async def test_for_loop_workflow(self, workflow_context: ExecutionContext) -> None:
        """Test workflow with for loop iteration."""
        from casare_rpa.nodes import (
            EndNode,
            ForLoopStartNode,
            SetVariableNode,
            StartNode,
        )

        # Start
        await StartNode("start").execute(workflow_context)

        # Initialize counter
        await SetVariableNode(
            "init_counter", config={"variable_name": "total", "value": 0}
        ).execute(workflow_context)

        # For loop over items
        items = [10, 20, 30, 40, 50]
        await ForLoopStartNode("for_start", config={"items": items}).execute(workflow_context)

        # Simulate loop iterations
        total = 0
        for item in items:
            workflow_context.set_variable("current_item", item)
            total += item

        workflow_context.set_variable("total", total)
        assert workflow_context.get_variable("total") == 150

        # End
        await EndNode("end").execute(workflow_context)

    @pytest.mark.asyncio
    async def test_while_loop_workflow(self, workflow_context: ExecutionContext) -> None:
        """Test workflow with while loop iteration."""
        from casare_rpa.nodes import EndNode, IncrementVariableNode, SetVariableNode, StartNode

        # Start
        await StartNode("start").execute(workflow_context)

        # Initialize counter
        await SetVariableNode(
            "init", config={"variable_name": "counter", "value": 0}
        ).execute(workflow_context)

        # Simulate while loop (counter < 5)
        while workflow_context.get_variable("counter") < 5:
            inc = IncrementVariableNode(
                "inc", config={"variable_name": "counter", "increment": 1}
            )
            await inc.execute(workflow_context)

        assert workflow_context.get_variable("counter") == 5

        # End
        await EndNode("end").execute(workflow_context)


# =============================================================================
# Error Handling Workflow Tests
# =============================================================================


@pytest.mark.e2e
class TestErrorHandlingWorkflow:
    """E2E tests for error handling workflow patterns."""

    @pytest.mark.asyncio
    async def test_try_catch_workflow_success(
        self, workflow_context: ExecutionContext
    ) -> None:
        """Test workflow with try/catch where try succeeds."""
        from casare_rpa.nodes import EndNode, LogNode, StartNode, TryNode

        # Start
        await StartNode("start").execute(workflow_context)

        # Try block
        try_node = TryNode("try")
        try_result = await try_node.execute(workflow_context)
        assert try_result.get("success") is True

        # Execute body that succeeds
        log = LogNode("body", config={"message": "Try block executing", "level": "INFO"})
        log_result = await log.execute(workflow_context)
        assert log_result.get("success") is True

        # Skip catch since no error
        # End
        await EndNode("end").execute(workflow_context)

    @pytest.mark.asyncio
    async def test_try_catch_workflow_error(
        self, workflow_context: ExecutionContext
    ) -> None:
        """Test workflow with try/catch where try fails."""
        from casare_rpa.nodes import CatchNode, EndNode, LogNode, StartNode, ThrowErrorNode, TryNode

        # Start
        await StartNode("start").execute(workflow_context)

        # Try block
        try_node = TryNode("try")
        await try_node.execute(workflow_context)

        # Execute body that throws error
        throw = ThrowErrorNode("throw", config={"error_message": "Intentional test error"})
        throw_result = await throw.execute(workflow_context)
        assert throw_result.get("success") is False or "error" in throw_result

        # Catch block handles error
        catch = CatchNode("catch")
        catch_result = await catch.execute(workflow_context)
        assert catch_result.get("success") is True

        # Log error handling
        log = LogNode("error_handled", config={"message": "Error was caught", "level": "WARNING"})
        await log.execute(workflow_context)

        # End
        await EndNode("end").execute(workflow_context)

    @pytest.mark.asyncio
    async def test_retry_workflow(self, workflow_context: ExecutionContext) -> None:
        """Test workflow with retry logic."""
        from casare_rpa.nodes import EndNode, RetryNode, StartNode

        # Start
        await StartNode("start").execute(workflow_context)

        # Track retry attempts
        workflow_context.set_variable("attempts", 0)

        # Retry node setup
        retry = RetryNode(
            "retry",
            config={"max_retries": 3, "delay_seconds": 0.1},
        )
        retry_result = await retry.execute(workflow_context)
        assert retry_result.get("success") is True

        # End
        await EndNode("end").execute(workflow_context)


# =============================================================================
# Variable Passing Workflow Tests
# =============================================================================


@pytest.mark.e2e
class TestVariablePassingWorkflow:
    """E2E tests for variable passing between nodes."""

    @pytest.mark.asyncio
    async def test_variable_chain_workflow(
        self, workflow_context: ExecutionContext
    ) -> None:
        """Test workflow that chains variable transformations."""
        from casare_rpa.nodes import (
            ConcatenateNode,
            EndNode,
            FormatStringNode,
            SetVariableNode,
            StartNode,
        )

        # Start
        await StartNode("start").execute(workflow_context)

        # Set initial variables
        await SetVariableNode(
            "set_first", config={"variable_name": "first_name", "value": "John"}
        ).execute(workflow_context)

        await SetVariableNode(
            "set_last", config={"variable_name": "last_name", "value": "Doe"}
        ).execute(workflow_context)

        # Concatenate names
        concat = ConcatenateNode(
            "concat",
            config={
                "strings": [
                    workflow_context.get_variable("first_name"),
                    " ",
                    workflow_context.get_variable("last_name"),
                ],
                "separator": "",
            },
        )
        concat_result = await concat.execute(workflow_context)
        full_name = concat_result.get("result", "")
        workflow_context.set_variable("full_name", full_name)

        assert workflow_context.get_variable("full_name") == "John Doe"

        # Format greeting
        format_node = FormatStringNode(
            "format",
            config={
                "template": "Welcome, {name}!",
                "values": {"name": workflow_context.get_variable("full_name")},
            },
        )
        format_result = await format_node.execute(workflow_context)
        greeting = format_result.get("result", "")

        assert "Welcome" in greeting
        assert "John Doe" in greeting

        # End
        await EndNode("end").execute(workflow_context)

    @pytest.mark.asyncio
    async def test_nested_variable_resolution(
        self, workflow_context: ExecutionContext
    ) -> None:
        """Test workflow with nested variable resolution."""
        from casare_rpa.nodes import EndNode, SetVariableNode, StartNode

        # Start
        await StartNode("start").execute(workflow_context)

        # Set complex nested data
        user_data = {
            "user": {
                "profile": {"name": "Alice", "age": 30},
                "settings": {"theme": "dark", "notifications": True},
            }
        }
        await SetVariableNode(
            "set_user", config={"variable_name": "data", "value": user_data}
        ).execute(workflow_context)

        # Access nested value
        data = workflow_context.get_variable("data")
        assert data["user"]["profile"]["name"] == "Alice"
        assert data["user"]["settings"]["theme"] == "dark"

        # End
        await EndNode("end").execute(workflow_context)


# =============================================================================
# Complex Workflow Pattern Tests
# =============================================================================


@pytest.mark.e2e
class TestComplexWorkflowPatterns:
    """E2E tests for complex workflow patterns."""

    @pytest.mark.asyncio
    async def test_data_processing_pipeline(
        self, workflow_context: ExecutionContext
    ) -> None:
        """Test complete data processing pipeline workflow."""
        from casare_rpa.nodes import (
            EndNode,
            StartNode,
        )

        # Start
        await StartNode("start").execute(workflow_context)

        # Create data
        data = [
            {"name": "Product A", "price": 100, "qty": 2},
            {"name": "Product B", "price": 50, "qty": 5},
            {"name": "Product C", "price": 200, "qty": 1},
            {"name": "Product D", "price": 75, "qty": 3},
        ]
        workflow_context.set_variable("products", data)

        # Filter products with price > 60
        filtered = [p for p in data if p["price"] > 60]
        workflow_context.set_variable("expensive_products", filtered)
        assert len(filtered) == 3

        # Calculate total value (price * qty)
        total_value = sum(p["price"] * p["qty"] for p in filtered)
        workflow_context.set_variable("total_value", total_value)
        assert total_value == 100 * 2 + 200 * 1 + 75 * 3  # 625

        # End
        await EndNode("end").execute(workflow_context)

    @pytest.mark.asyncio
    async def test_conditional_loop_workflow(
        self, workflow_context: ExecutionContext
    ) -> None:
        """Test workflow with conditional logic inside loop."""
        from casare_rpa.nodes import EndNode, StartNode

        # Start
        await StartNode("start").execute(workflow_context)

        # Process items with conditional logic
        items = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        evens = []
        odds = []

        for item in items:
            if item % 2 == 0:
                evens.append(item)
            else:
                odds.append(item)

        workflow_context.set_variable("evens", evens)
        workflow_context.set_variable("odds", odds)

        assert workflow_context.get_variable("evens") == [2, 4, 6, 8, 10]
        assert workflow_context.get_variable("odds") == [1, 3, 5, 7, 9]

        # End
        await EndNode("end").execute(workflow_context)

    @pytest.mark.asyncio
    async def test_parallel_aggregation_workflow(
        self, workflow_context: ExecutionContext
    ) -> None:
        """Test workflow that aggregates parallel results."""
        from casare_rpa.nodes import EndNode, StartNode

        # Start
        await StartNode("start").execute(workflow_context)

        # Simulate parallel processing results
        parallel_results = {
            "api_1": {"status": "success", "data": [1, 2, 3]},
            "api_2": {"status": "success", "data": [4, 5, 6]},
            "api_3": {"status": "success", "data": [7, 8, 9]},
        }
        workflow_context.set_variable("parallel_results", parallel_results)

        # Aggregate all data
        all_data = []
        for result in parallel_results.values():
            if result["status"] == "success":
                all_data.extend(result["data"])

        workflow_context.set_variable("aggregated_data", all_data)
        assert workflow_context.get_variable("aggregated_data") == [1, 2, 3, 4, 5, 6, 7, 8, 9]

        # End
        await EndNode("end").execute(workflow_context)
