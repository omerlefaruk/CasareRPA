"""
Tests for error handling nodes.

Tests try/catch, retry with backoff, and custom error throwing.
"""

import pytest

from casare_rpa.nodes.error_handling_nodes import (
    TryNode,
    RetryNode,
    RetrySuccessNode,
    RetryFailNode,
    ThrowErrorNode,
)
from casare_rpa.core.types import NodeStatus


class TestTryNode:
    """Tests for Try block node."""

    @pytest.mark.asyncio
    async def test_try_enters_try_body(self, execution_context):
        """Test Try node enters try body on first execution."""
        node = TryNode(node_id="try_1")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "try_body" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_try_success_path(self, execution_context):
        """Test Try node routes to success after successful try body."""
        node = TryNode(node_id="try_1")

        # First execution - enter try block
        result1 = await node.execute(execution_context)
        assert "try_body" in result1["next_nodes"]

        # Set success state (simulating try body completed without error)
        execution_context.variables[f"{node.node_id}_state"]["in_try_block"] = False
        execution_context.variables[f"{node.node_id}_state"]["error_occurred"] = False

        # Second execution - return from try block
        result2 = await node.execute(execution_context)
        assert "success" in result2["next_nodes"]

    @pytest.mark.asyncio
    async def test_try_catch_path(self, execution_context):
        """Test Try node routes to catch when error occurs."""
        node = TryNode(node_id="try_1")

        # First execution - enter try block
        await node.execute(execution_context)

        # Set error state (simulating error in try body)
        execution_context.variables[f"{node.node_id}_state"]["error_occurred"] = True
        execution_context.variables[f"{node.node_id}_state"]["error_message"] = "Test error"
        execution_context.variables[f"{node.node_id}_state"]["error_type"] = "ValueError"

        # Second execution - return from try block with error
        result = await node.execute(execution_context)

        assert "catch" in result["next_nodes"]
        assert node.get_output_value("error_message") == "Test error"
        assert node.get_output_value("error_type") == "ValueError"

    @pytest.mark.asyncio
    async def test_try_cleans_up_state(self, execution_context):
        """Test Try node cleans up state after completion."""
        node = TryNode(node_id="try_1")

        # First execution
        await node.execute(execution_context)
        state_key = f"{node.node_id}_state"
        assert state_key in execution_context.variables

        # Second execution (success)
        execution_context.variables[state_key]["error_occurred"] = False
        await node.execute(execution_context)

        # State should be cleaned up
        assert state_key not in execution_context.variables


class TestRetryNode:
    """Tests for Retry node."""

    @pytest.mark.asyncio
    async def test_retry_first_attempt(self, execution_context):
        """Test Retry node starts first attempt."""
        node = RetryNode(node_id="retry_1", config={"max_attempts": 3})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "retry_body" in result["next_nodes"]
        assert node.get_output_value("attempt") == 1

    @pytest.mark.asyncio
    async def test_retry_multiple_attempts(self, execution_context):
        """Test Retry node tracks multiple attempts."""
        node = RetryNode(node_id="retry_1", config={
            "max_attempts": 3,
            "initial_delay": 0.01  # Short delay for testing
        })

        # First attempt
        result1 = await node.execute(execution_context)
        assert node.get_output_value("attempt") == 1
        assert "retry_body" in result1["next_nodes"]

        # Second attempt
        result2 = await node.execute(execution_context)
        assert node.get_output_value("attempt") == 2
        assert "retry_body" in result2["next_nodes"]

        # Third attempt
        result3 = await node.execute(execution_context)
        assert node.get_output_value("attempt") == 3
        assert "retry_body" in result3["next_nodes"]

    @pytest.mark.asyncio
    async def test_retry_max_attempts_exceeded(self, execution_context):
        """Test Retry node fails after max attempts."""
        node = RetryNode(node_id="retry_1", config={
            "max_attempts": 2,
            "initial_delay": 0.01
        })

        # First attempt
        await node.execute(execution_context)
        # Second attempt
        await node.execute(execution_context)
        # Third attempt - exceeds max
        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "failed" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_retry_default_config(self, execution_context):
        """Test Retry node with default configuration."""
        node = RetryNode(node_id="retry_1")

        result = await node.execute(execution_context)

        assert result["success"] is True
        # Default max_attempts is 3
        assert "retry_body" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_retry_outputs_attempt_number(self, execution_context):
        """Test Retry node outputs correct attempt numbers."""
        node = RetryNode(node_id="retry_1", config={
            "max_attempts": 5,
            "initial_delay": 0.01
        })

        attempts = []
        for _ in range(5):
            await node.execute(execution_context)
            attempts.append(node.get_output_value("attempt"))

        assert attempts == [1, 2, 3, 4, 5]


class TestRetrySuccessNode:
    """Tests for Retry Success signal node."""

    @pytest.mark.asyncio
    async def test_retry_success_signal(self, execution_context):
        """Test RetrySuccess node signals success."""
        node = RetrySuccessNode(node_id="retry_success_1")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["control_flow"] == "retry_success"
        assert "exec_out" in result["next_nodes"]
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_retry_success_has_exec_output(self, execution_context):
        """Test RetrySuccess node has execution output."""
        node = RetrySuccessNode(node_id="retry_success_1")

        result = await node.execute(execution_context)

        assert "exec_out" in result["next_nodes"]


class TestRetryFailNode:
    """Tests for Retry Fail signal node."""

    @pytest.mark.asyncio
    async def test_retry_fail_signal(self, execution_context):
        """Test RetryFail node signals failure."""
        node = RetryFailNode(node_id="retry_fail_1")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["control_flow"] == "retry_fail"

    @pytest.mark.asyncio
    async def test_retry_fail_with_message(self, execution_context):
        """Test RetryFail node captures error message."""
        node = RetryFailNode(node_id="retry_fail_1")
        node.set_input_value("error_message", "Connection timeout")

        result = await node.execute(execution_context)

        assert result["data"]["error_message"] == "Connection timeout"

    @pytest.mark.asyncio
    async def test_retry_fail_default_message(self, execution_context):
        """Test RetryFail node has default message."""
        node = RetryFailNode(node_id="retry_fail_1")

        result = await node.execute(execution_context)

        assert result["data"]["error_message"] == "Operation failed"


class TestThrowErrorNode:
    """Tests for Throw Error node."""

    @pytest.mark.asyncio
    async def test_throw_error_basic(self, execution_context):
        """Test ThrowError node throws error."""
        node = ThrowErrorNode(node_id="throw_1")
        node.set_input_value("error_message", "Something went wrong")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert result["error"] == "Something went wrong"
        assert result["error_type"] == "CustomError"
        assert node.status == NodeStatus.ERROR

    @pytest.mark.asyncio
    async def test_throw_error_from_config(self, execution_context):
        """Test ThrowError with message from config."""
        node = ThrowErrorNode(node_id="throw_1", config={
            "error_message": "Config error message"
        })

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert result["error"] == "Config error message"

    @pytest.mark.asyncio
    async def test_throw_error_default_message(self, execution_context):
        """Test ThrowError with default message."""
        node = ThrowErrorNode(node_id="throw_1")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert result["error"] == "Custom error"

    @pytest.mark.asyncio
    async def test_throw_error_no_next_nodes(self, execution_context):
        """Test ThrowError stops execution flow."""
        node = ThrowErrorNode(node_id="throw_1")
        node.set_input_value("error_message", "Stop here")

        result = await node.execute(execution_context)

        assert result["next_nodes"] == []


class TestErrorHandlingScenarios:
    """Integration tests for error handling patterns."""

    @pytest.mark.asyncio
    async def test_try_success_scenario(self, execution_context):
        """Test successful try block scenario."""
        try_node = TryNode(node_id="try_1")

        # Enter try block
        result1 = await try_node.execute(execution_context)
        assert "try_body" in result1["next_nodes"]

        # Simulate successful execution (no error)
        state = execution_context.variables[f"{try_node.node_id}_state"]
        state["error_occurred"] = False

        # Exit try block
        result2 = await try_node.execute(execution_context)
        assert "success" in result2["next_nodes"]

    @pytest.mark.asyncio
    async def test_try_catch_scenario(self, execution_context):
        """Test try block catching error scenario."""
        try_node = TryNode(node_id="try_1")

        # Enter try block
        await try_node.execute(execution_context)

        # Simulate error in try body
        state = execution_context.variables[f"{try_node.node_id}_state"]
        state["error_occurred"] = True
        state["error_message"] = "Database connection failed"
        state["error_type"] = "ConnectionError"

        # Exit try block - should go to catch
        result = await try_node.execute(execution_context)

        assert "catch" in result["next_nodes"]
        assert try_node.get_output_value("error_message") == "Database connection failed"

    @pytest.mark.asyncio
    async def test_retry_until_success(self, execution_context):
        """Test retry pattern until success."""
        retry_node = RetryNode(node_id="retry_1", config={
            "max_attempts": 5,
            "initial_delay": 0.01
        })

        # Simulate 2 failures then success
        failures = 2
        attempts = 0

        for _ in range(10):  # Safety limit
            result = await retry_node.execute(execution_context)
            attempts += 1

            if "retry_body" in result["next_nodes"]:
                if attempts <= failures:
                    # Simulate failure - would continue retrying
                    continue
                else:
                    # Simulate success
                    break
            elif "failed" in result["next_nodes"]:
                # Max retries exceeded
                break

        # Should have succeeded after 3 attempts (2 failures + 1 success)
        assert attempts == 3

    @pytest.mark.asyncio
    async def test_conditional_throw_error(self, execution_context):
        """Test conditional error throwing."""
        # Simulate validation failure
        is_valid = False

        if not is_valid:
            throw_node = ThrowErrorNode(node_id="throw_validation")
            throw_node.set_input_value("error_message", "Validation failed: Invalid input")

            result = await throw_node.execute(execution_context)

            assert result["success"] is False
            assert "Validation failed" in result["error"]

    @pytest.mark.asyncio
    async def test_error_recovery_pattern(self, execution_context):
        """Test error recovery using try/catch."""
        try_node = TryNode(node_id="try_1")

        # Enter try block
        await try_node.execute(execution_context)

        # Simulate error
        state = execution_context.variables[f"{try_node.node_id}_state"]
        state["error_occurred"] = True
        state["error_message"] = "Network error"
        state["error_type"] = "NetworkError"

        # Exit to catch block
        catch_result = await try_node.execute(execution_context)
        assert "catch" in catch_result["next_nodes"]

        # In catch block, get error details
        error_msg = try_node.get_output_value("error_message")
        error_type = try_node.get_output_value("error_type")

        assert error_msg == "Network error"
        assert error_type == "NetworkError"

        # Recovery could happen here (e.g., log error, use fallback value)

    @pytest.mark.asyncio
    async def test_nested_retry_in_try(self, execution_context):
        """Test retry inside a try block pattern."""
        try_node = TryNode(node_id="try_1")
        retry_node = RetryNode(node_id="retry_1", config={
            "max_attempts": 2,
            "initial_delay": 0.01
        })

        # Enter try block
        try_result = await try_node.execute(execution_context)
        assert "try_body" in try_result["next_nodes"]

        # In try body, start retry
        retry_result = await retry_node.execute(execution_context)
        assert "retry_body" in retry_result["next_nodes"]
        assert retry_node.get_output_value("attempt") == 1

    @pytest.mark.asyncio
    async def test_multiple_throw_error_messages(self, execution_context):
        """Test throwing different errors for different conditions."""
        conditions = [
            ("empty_input", "Input cannot be empty"),
            ("invalid_format", "Invalid data format"),
            ("auth_failed", "Authentication required"),
        ]

        for error_code, error_message in conditions:
            throw_node = ThrowErrorNode(node_id=f"throw_{error_code}")
            throw_node.set_input_value("error_message", error_message)

            result = await throw_node.execute(execution_context)

            assert result["success"] is False
            assert result["error"] == error_message
            assert throw_node.status == NodeStatus.ERROR

    @pytest.mark.asyncio
    async def test_retry_preserves_context(self, execution_context):
        """Test that retry preserves execution context between attempts."""
        execution_context.set_variable("attempt_data", [])

        retry_node = RetryNode(node_id="retry_1", config={
            "max_attempts": 3,
            "initial_delay": 0.01
        })

        for _ in range(3):
            result = await retry_node.execute(execution_context)
            if "retry_body" in result["next_nodes"]:
                # Record this attempt's data
                data = execution_context.get_variable("attempt_data")
                data.append(retry_node.get_output_value("attempt"))
                execution_context.set_variable("attempt_data", data)

        # All attempts should be recorded
        assert execution_context.get_variable("attempt_data") == [1, 2, 3]
