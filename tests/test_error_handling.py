"""
Tests for error handling nodes: Try, Retry, Throw.
"""

import pytest
import asyncio
from casare_rpa.core.execution_context import ExecutionContext
from casare_rpa.nodes.error_handling_nodes import (
    TryNode,
    RetryNode,
    RetrySuccessNode,
    RetryFailNode,
    ThrowErrorNode
)
from casare_rpa.nodes.variable_nodes import SetVariableNode


class TestTryNode:
    """Tests for TryNode."""
    
    @pytest.mark.asyncio
    async def test_try_initial_execution(self):
        """Test try node routes to try_body on first execution."""
        context = ExecutionContext("test")
        try_node = TryNode("try1")
        
        result = await try_node.execute(context)
        
        assert result["success"] is True
        assert result["next_nodes"] == ["try_body"]
        assert f"{try_node.node_id}_state" in context.variables
    
    @pytest.mark.asyncio
    async def test_try_success_path(self):
        """Test try node routes to success when no error."""
        context = ExecutionContext("test")
        try_node = TryNode("try1")
        
        # First execution
        await try_node.execute(context)
        
        # Simulate successful try body completion
        try_state = context.variables[f"{try_node.node_id}_state"]
        try_state["error_occurred"] = False
        
        # Second execution (return from try body)
        result = await try_node.execute(context)
        
        assert result["success"] is True
        assert result["next_nodes"] == ["success"]
        assert f"{try_node.node_id}_state" not in context.variables
    
    @pytest.mark.asyncio
    async def test_try_catch_path(self):
        """Test try node routes to catch when error occurs."""
        context = ExecutionContext("test")
        try_node = TryNode("try1")
        
        # First execution
        await try_node.execute(context)
        
        # Simulate error in try body
        try_state = context.variables[f"{try_node.node_id}_state"]
        try_state["error_occurred"] = True
        try_state["error_message"] = "Test error"
        try_state["error_type"] = "TestException"
        
        # Second execution (return from try body with error)
        result = await try_node.execute(context)
        
        assert result["success"] is True
        assert result["next_nodes"] == ["catch"]
        assert result["data"]["error_message"] == "Test error"
        assert result["data"]["error_type"] == "TestException"
        assert try_node.get_output_value("error_message") == "Test error"
        assert try_node.get_output_value("error_type") == "TestException"


class TestRetryNode:
    """Tests for RetryNode."""
    
    @pytest.mark.asyncio
    async def test_retry_first_attempt(self):
        """Test retry node starts with attempt 1."""
        context = ExecutionContext("test")
        retry_node = RetryNode("retry1", {"max_attempts": 3})
        
        result = await retry_node.execute(context)
        
        assert result["success"] is True
        assert result["next_nodes"] == ["retry_body"]
        assert result["data"]["attempt"] == 1
        assert retry_node.get_output_value("attempt") == 1
    
    @pytest.mark.asyncio
    async def test_retry_multiple_attempts(self):
        """Test retry node increments attempts."""
        context = ExecutionContext("test")
        retry_node = RetryNode("retry1", {"max_attempts": 3, "initial_delay": 0.01})
        
        attempts = []
        for i in range(3):
            result = await retry_node.execute(context)
            assert result["success"] is True
            assert result["next_nodes"] == ["retry_body"]
            attempts.append(result["data"]["attempt"])
        
        assert attempts == [1, 2, 3]
    
    @pytest.mark.asyncio
    async def test_retry_max_attempts_exceeded(self):
        """Test retry fails after max attempts."""
        context = ExecutionContext("test")
        retry_node = RetryNode("retry1", {"max_attempts": 2, "initial_delay": 0.01})
        
        # Exhaust attempts
        await retry_node.execute(context)  # Attempt 1
        await retry_node.execute(context)  # Attempt 2
        
        # Store error before final attempt
        retry_state = context.variables[f"{retry_node.node_id}_retry_state"]
        retry_state["last_error"] = "Operation failed"
        
        result = await retry_node.execute(context)  # Attempt 3 - should fail
        
        assert result["success"] is False
        assert result["next_nodes"] == ["failed"]
        assert retry_node.get_output_value("last_error") == "Operation failed"
    
    @pytest.mark.asyncio
    async def test_retry_exponential_backoff(self):
        """Test retry applies exponential backoff delay."""
        context = ExecutionContext("test")
        retry_node = RetryNode("retry1", {
            "max_attempts": 3,
            "initial_delay": 0.1,
            "backoff_multiplier": 2.0
        })
        
        import time
        
        # First attempt - no delay
        start = time.time()
        await retry_node.execute(context)
        duration1 = time.time() - start
        assert duration1 < 0.05  # Should be instant
        
        # Second attempt - 0.1s delay
        start = time.time()
        await retry_node.execute(context)
        duration2 = time.time() - start
        assert 0.08 < duration2 < 0.15
        
        # Third attempt - 0.2s delay (0.1 * 2^1)
        start = time.time()
        await retry_node.execute(context)
        duration3 = time.time() - start
        assert 0.18 < duration3 < 0.25


class TestRetrySuccessNode:
    """Tests for RetrySuccessNode."""
    
    @pytest.mark.asyncio
    async def test_retry_success_execution(self):
        """Test retry success signals completion."""
        context = ExecutionContext("test")
        retry_success = RetrySuccessNode("retry_success1")
        
        result = await retry_success.execute(context)
        
        assert result["success"] is True
        assert result["control_flow"] == "retry_success"
        assert result["next_nodes"] == ["exec_out"]


class TestRetryFailNode:
    """Tests for RetryFailNode."""
    
    @pytest.mark.asyncio
    async def test_retry_fail_execution(self):
        """Test retry fail signals retry needed."""
        context = ExecutionContext("test")
        retry_fail = RetryFailNode("retry_fail1")
        retry_fail.set_input_value("error_message", "Test failure")
        
        result = await retry_fail.execute(context)
        
        assert result["success"] is True
        assert result["control_flow"] == "retry_fail"
        assert result["data"]["error_message"] == "Test failure"
        assert result["next_nodes"] == ["exec_out"]
    
    @pytest.mark.asyncio
    async def test_retry_fail_default_message(self):
        """Test retry fail uses default message if none provided."""
        context = ExecutionContext("test")
        retry_fail = RetryFailNode("retry_fail1")
        
        result = await retry_fail.execute(context)
        
        assert result["success"] is True
        assert result["data"]["error_message"] == "Operation failed"


class TestThrowErrorNode:
    """Tests for ThrowErrorNode."""
    
    @pytest.mark.asyncio
    async def test_throw_error_with_input(self):
        """Test throw error node with input message."""
        context = ExecutionContext("test")
        throw_node = ThrowErrorNode("throw1")
        throw_node.set_input_value("error_message", "Custom test error")
        
        result = await throw_node.execute(context)
        
        assert result["success"] is False
        assert result["error"] == "Custom test error"
        assert result["error_type"] == "CustomError"
    
    @pytest.mark.asyncio
    async def test_throw_error_with_config(self):
        """Test throw error node with config message."""
        context = ExecutionContext("test")
        throw_node = ThrowErrorNode("throw1", {"error_message": "Config error"})
        
        result = await throw_node.execute(context)
        
        assert result["success"] is False
        assert result["error"] == "Config error"
    
    @pytest.mark.asyncio
    async def test_throw_error_default_message(self):
        """Test throw error with default message."""
        context = ExecutionContext("test")
        throw_node = ThrowErrorNode("throw1")
        
        result = await throw_node.execute(context)
        
        assert result["success"] is False
        assert result["error"] == "Custom error"


class TestErrorHandlingIntegration:
    """Integration tests for error handling nodes."""
    
    @pytest.mark.asyncio
    async def test_try_catch_with_throw(self):
        """Test try/catch with throw error."""
        context = ExecutionContext("test")
        
        try_node = TryNode("try1")
        throw_node = ThrowErrorNode("throw1", {"error_message": "Test exception"})
        
        # Enter try block
        result1 = await try_node.execute(context)
        assert result1["next_nodes"] == ["try_body"]
        
        # Execute throw inside try
        throw_result = await throw_node.execute(context)
        assert throw_result["success"] is False
        
        # Simulate error caught
        try_state = context.variables[f"{try_node.node_id}_state"]
        try_state["error_occurred"] = True
        try_state["error_message"] = throw_result["error"]
        try_state["error_type"] = throw_result["error_type"]
        
        # Return from try with error
        result2 = await try_node.execute(context)
        assert result2["next_nodes"] == ["catch"]
        assert result2["data"]["error_message"] == "Test exception"
    
    @pytest.mark.asyncio
    async def test_retry_with_eventual_success(self):
        """Test retry that succeeds on second attempt."""
        context = ExecutionContext("test")
        
        retry_node = RetryNode("retry1", {"max_attempts": 3, "initial_delay": 0.01})
        retry_success = RetrySuccessNode("success1")
        retry_fail = RetryFailNode("fail1")
        
        # First attempt - fail
        result1 = await retry_node.execute(context)
        assert result1["data"]["attempt"] == 1
        
        # Simulate failure
        fail_result = await retry_fail.execute(context)
        assert fail_result["control_flow"] == "retry_fail"
        
        # Store error
        retry_state = context.variables[f"{retry_node.node_id}_retry_state"]
        retry_state["last_error"] = "Temporary failure"
        
        # Second attempt - success
        result2 = await retry_node.execute(context)
        assert result2["data"]["attempt"] == 2
        
        # Simulate success
        success_result = await retry_success.execute(context)
        assert success_result["control_flow"] == "retry_success"
    
    @pytest.mark.asyncio
    async def test_nested_try_catch(self):
        """Test nested try/catch blocks."""
        context = ExecutionContext("test")
        
        outer_try = TryNode("outer_try")
        inner_try = TryNode("inner_try")
        
        # Enter outer try
        result1 = await outer_try.execute(context)
        assert result1["next_nodes"] == ["try_body"]
        
        # Enter inner try
        result2 = await inner_try.execute(context)
        assert result2["next_nodes"] == ["try_body"]
        
        # Both states should exist independently
        assert f"{outer_try.node_id}_state" in context.variables
        assert f"{inner_try.node_id}_state" in context.variables
    
    @pytest.mark.asyncio
    async def test_retry_with_variable_tracking(self):
        """Test retry with variable tracking across attempts."""
        context = ExecutionContext("test")
        
        retry_node = RetryNode("retry1", {"max_attempts": 3, "initial_delay": 0.01})
        
        attempts = []
        for attempt in range(3):
            # Execute retry
            result = await retry_node.execute(context)
            attempt_num = result["data"]["attempt"]
            attempts.append(attempt_num)
            
            # Verify retry state is tracked in context
            retry_state = context.variables[f"{retry_node.node_id}_retry_state"]
            assert retry_state["attempt"] == attempt_num
        
        # Verify all attempts were tracked correctly
        assert attempts == [1, 2, 3]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
