"""
Comprehensive tests for error handling nodes.

Tests all 10 error handling nodes:
- TryNode, ThrowErrorNode, RetryNode, AssertNode
- LogErrorNode, OnErrorNode, ErrorRecoveryNode
- RetrySuccessNode, RetryFailNode, WebhookNotifyNode
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncio
import json

# Uses execution_context fixture from conftest.py - no import needed
from casare_rpa.domain.value_objects.types import NodeStatus


class TestTryNode:
    """Tests for TryNode error handling."""

    @pytest.fixture
    def execution_context(self) -> None:
        """Create mock execution context."""
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        context.workflow_name = "test_workflow"
        return context

    @pytest.mark.asyncio
    async def test_try_node_initial_execution(self, execution_context) -> None:
        """Test TryNode routes to try_body on first execution."""
        from casare_rpa.nodes.error_handling_nodes import TryNode

        node = TryNode(node_id="test_try")
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "try_body" in result["next_nodes"]
        assert f"{node.node_id}_state" in execution_context.variables
        assert (
            execution_context.variables[f"{node.node_id}_state"]["in_try_block"] is True
        )

    @pytest.mark.asyncio
    async def test_try_node_success_path(self, execution_context) -> None:
        """Test TryNode routes to success when no error occurred."""
        from casare_rpa.nodes.error_handling_nodes import TryNode

        node = TryNode(node_id="test_try_success")

        # First execution enters try block
        await node.execute(execution_context)

        # Simulate successful execution by setting state without error
        execution_context.variables[f"{node.node_id}_state"]["error_occurred"] = False

        # Second execution should route to success
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "success" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_try_node_catch_path(self, execution_context) -> None:
        """Test TryNode routes to catch when error occurred."""
        from casare_rpa.nodes.error_handling_nodes import TryNode

        node = TryNode(node_id="test_try_catch")

        # First execution enters try block
        await node.execute(execution_context)

        # Simulate error by setting state with error
        execution_context.variables[f"{node.node_id}_state"]["error_occurred"] = True
        execution_context.variables[f"{node.node_id}_state"]["error_message"] = (
            "Test error"
        )
        execution_context.variables[f"{node.node_id}_state"]["error_type"] = (
            "TestException"
        )

        # Second execution should route to catch
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "catch" in result["next_nodes"]
        assert result["data"]["error_message"] == "Test error"
        assert result["data"]["error_type"] == "TestException"

    @pytest.mark.asyncio
    async def test_try_node_outputs_error_info(self, execution_context) -> None:
        """Test TryNode sets output ports with error info."""
        from casare_rpa.nodes.error_handling_nodes import TryNode

        node = TryNode(node_id="test_try_outputs")

        await node.execute(execution_context)
        execution_context.variables[f"{node.node_id}_state"]["error_occurred"] = True
        execution_context.variables[f"{node.node_id}_state"]["error_message"] = (
            "Output test"
        )
        execution_context.variables[f"{node.node_id}_state"]["error_type"] = (
            "OutputException"
        )

        await node.execute(execution_context)

        assert node.get_output_value("error_message") == "Output test"
        assert node.get_output_value("error_type") == "OutputException"


class TestThrowErrorNode:
    """Tests for ThrowErrorNode."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_throw_error_with_config_message(self, execution_context) -> None:
        """Test ThrowErrorNode with message from config."""
        from casare_rpa.nodes.error_handling_nodes import ThrowErrorNode

        node = ThrowErrorNode(
            node_id="test_throw", config={"error_message": "Custom error"}
        )
        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "Custom error" in result["error"]
        assert result["error_type"] == "CustomError"
        assert node.status == NodeStatus.ERROR

    @pytest.mark.asyncio
    async def test_throw_error_with_input_message(self, execution_context) -> None:
        """Test ThrowErrorNode with message from input port."""
        from casare_rpa.nodes.error_handling_nodes import ThrowErrorNode

        node = ThrowErrorNode(node_id="test_throw_input")
        node.set_input_value("error_message", "Input error message")
        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "Input error message" in result["error"]

    @pytest.mark.asyncio
    async def test_throw_error_default_message(self, execution_context) -> None:
        """Test ThrowErrorNode with default message."""
        from casare_rpa.nodes.error_handling_nodes import ThrowErrorNode

        node = ThrowErrorNode(node_id="test_throw_default")
        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "Custom error" in result["error"]  # Default message


class TestRetryNode:
    """Tests for RetryNode automatic retry logic."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_retry_first_attempt(self, execution_context) -> None:
        """Test RetryNode first attempt routes to retry_body."""
        from casare_rpa.nodes.error_handling_nodes import RetryNode

        node = RetryNode(node_id="test_retry", config={"max_attempts": 3})
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "retry_body" in result["next_nodes"]
        assert result["data"]["attempt"] == 1

    @pytest.mark.asyncio
    async def test_retry_increments_attempt(self, execution_context) -> None:
        """Test RetryNode increments attempt count."""
        from casare_rpa.nodes.error_handling_nodes import RetryNode

        node = RetryNode(
            node_id="test_retry_inc", config={"max_attempts": 3, "initial_delay": 0.01}
        )

        # First attempt
        await node.execute(execution_context)

        # Second attempt (simulating failure and retry)
        result = await node.execute(execution_context)

        assert result["data"]["attempt"] == 2

    @pytest.mark.asyncio
    async def test_retry_max_attempts_exceeded(self, execution_context) -> None:
        """Test RetryNode fails when max attempts exceeded."""
        from casare_rpa.nodes.error_handling_nodes import RetryNode

        node = RetryNode(
            node_id="test_retry_max", config={"max_attempts": 2, "initial_delay": 0.01}
        )

        # Execute 3 times to exceed max_attempts of 2
        await node.execute(execution_context)  # Attempt 1
        await node.execute(execution_context)  # Attempt 2
        result = await node.execute(execution_context)  # Attempt 3 - should fail

        assert result["success"] is False
        assert "failed" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_retry_outputs_attempt_number(self, execution_context) -> None:
        """Test RetryNode sets attempt output port."""
        from casare_rpa.nodes.error_handling_nodes import RetryNode

        node = RetryNode(node_id="test_retry_output", config={"max_attempts": 3})
        await node.execute(execution_context)

        assert node.get_output_value("attempt") == 1

    @pytest.mark.asyncio
    async def test_retry_exponential_backoff(self, execution_context) -> None:
        """Test RetryNode applies exponential backoff delay."""
        from casare_rpa.nodes.error_handling_nodes import RetryNode

        node = RetryNode(
            node_id="test_retry_backoff",
            config={
                "max_attempts": 3,
                "initial_delay": 0.01,
                "backoff_multiplier": 2.0,
            },
        )

        # First attempt - no delay
        start = asyncio.get_event_loop().time()
        await node.execute(execution_context)
        first_duration = asyncio.get_event_loop().time() - start

        # Second attempt - should have delay
        start = asyncio.get_event_loop().time()
        await node.execute(execution_context)
        second_duration = asyncio.get_event_loop().time() - start

        # Second attempt should take longer due to delay
        assert second_duration >= 0.01  # At least initial delay


class TestRetrySuccessNode:
    """Tests for RetrySuccessNode."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        return context

    @pytest.mark.asyncio
    async def test_retry_success_signals_completion(self, execution_context) -> None:
        """Test RetrySuccessNode signals successful retry completion."""
        from casare_rpa.nodes.error_handling_nodes import RetrySuccessNode

        node = RetrySuccessNode(node_id="test_retry_success")
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["control_flow"] == "retry_success"
        assert "exec_out" in result["next_nodes"]


class TestRetryFailNode:
    """Tests for RetryFailNode."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        return context

    @pytest.mark.asyncio
    async def test_retry_fail_signals_failure(self, execution_context) -> None:
        """Test RetryFailNode signals retry failure."""
        from casare_rpa.nodes.error_handling_nodes import RetryFailNode

        node = RetryFailNode(node_id="test_retry_fail")
        node.set_input_value("error_message", "Operation timed out")
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["control_flow"] == "retry_fail"
        assert result["data"]["error_message"] == "Operation timed out"

    @pytest.mark.asyncio
    async def test_retry_fail_default_message(self, execution_context) -> None:
        """Test RetryFailNode with default error message."""
        from casare_rpa.nodes.error_handling_nodes import RetryFailNode

        node = RetryFailNode(node_id="test_retry_fail_default")
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["error_message"] == "Operation failed"


class TestAssertNode:
    """Tests for AssertNode condition validation."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_assert_passes_on_true(self, execution_context) -> None:
        """Test AssertNode passes when condition is true."""
        from casare_rpa.nodes.error_handling_nodes import AssertNode

        node = AssertNode(node_id="test_assert_true", config={"condition": True})
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["passed"] is True
        assert "exec_out" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_assert_fails_on_false(self, execution_context) -> None:
        """Test AssertNode fails when condition is false."""
        from casare_rpa.nodes.error_handling_nodes import AssertNode

        node = AssertNode(
            node_id="test_assert_false",
            config={"condition": False, "message": "Expected value to be true"},
        )
        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "Assertion failed" in result["error"]
        assert result["error_type"] == "AssertionError"

    @pytest.mark.asyncio
    async def test_assert_with_input_condition(self, execution_context) -> None:
        """Test AssertNode with condition from input port."""
        from casare_rpa.nodes.error_handling_nodes import AssertNode

        node = AssertNode(node_id="test_assert_input")
        node.set_input_value("condition", True)
        node.set_input_value("message", "Custom assertion message")
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("passed") is True

    @pytest.mark.asyncio
    async def test_assert_string_condition_parsing(self, execution_context) -> None:
        """Test AssertNode parses string conditions correctly."""
        from casare_rpa.nodes.error_handling_nodes import AssertNode

        # Test "true" string
        node = AssertNode(node_id="test_assert_string")
        node.set_input_value("condition", "true")
        result = await node.execute(execution_context)
        assert result["success"] is True

        # Test "false" string
        node2 = AssertNode(node_id="test_assert_string_false")
        node2.set_input_value("condition", "false")
        result2 = await node2.execute(execution_context)
        assert result2["success"] is False


class TestLogErrorNode:
    """Tests for LogErrorNode error logging."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.workflow_name = "test_workflow"
        return context

    @pytest.mark.asyncio
    async def test_log_error_basic(self, execution_context) -> None:
        """Test LogErrorNode logs error with basic info."""
        from casare_rpa.nodes.error_handling_nodes import LogErrorNode

        node = LogErrorNode(node_id="test_log_error")
        node.set_input_value("error_message", "Test error occurred")
        node.set_input_value("error_type", "TestError")
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "exec_out" in result["next_nodes"]

        log_entry = node.get_output_value("log_entry")
        assert log_entry["error_message"] == "Test error occurred"
        assert log_entry["error_type"] == "TestError"
        assert log_entry["workflow"] == "test_workflow"

    @pytest.mark.asyncio
    async def test_log_error_with_context(self, execution_context) -> None:
        """Test LogErrorNode logs with additional context."""
        from casare_rpa.nodes.error_handling_nodes import LogErrorNode

        node = LogErrorNode(node_id="test_log_context")
        node.set_input_value("error_message", "Error with context")
        node.set_input_value("context", {"node_id": "failed_node", "step": 5})
        result = await node.execute(execution_context)

        log_entry = node.get_output_value("log_entry")
        assert log_entry["context"]["node_id"] == "failed_node"
        assert log_entry["context"]["step"] == 5

    @pytest.mark.asyncio
    async def test_log_error_levels(self, execution_context) -> None:
        """Test LogErrorNode respects log level configuration."""
        from casare_rpa.nodes.error_handling_nodes import LogErrorNode

        for level in ["debug", "info", "warning", "error", "critical"]:
            node = LogErrorNode(node_id=f"test_log_{level}", config={"level": level})
            node.set_input_value("error_message", f"Test {level} message")
            result = await node.execute(execution_context)

            assert result["success"] is True
            log_entry = node.get_output_value("log_entry")
            assert log_entry["level"] == level


class TestOnErrorNode:
    """Tests for OnErrorNode global error handling."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        return context

    @pytest.mark.asyncio
    async def test_on_error_initial_execution(self, execution_context) -> None:
        """Test OnErrorNode enters protected block on first execution."""
        from casare_rpa.nodes.error_handling_nodes import OnErrorNode

        node = OnErrorNode(node_id="test_on_error")
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "protected_body" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_on_error_catches_error(self, execution_context) -> None:
        """Test OnErrorNode routes to error handler when error occurred."""
        from casare_rpa.nodes.error_handling_nodes import OnErrorNode

        node = OnErrorNode(node_id="test_on_error_catch")

        # First execution enters protected block
        await node.execute(execution_context)

        # Simulate error
        state_key = f"{node.node_id}_error_state"
        execution_context.variables[state_key]["error_occurred"] = True
        execution_context.variables[state_key]["error_message"] = "Caught error"
        execution_context.variables[state_key]["error_type"] = "CaughtException"
        execution_context.variables[state_key]["error_node"] = "failing_node"

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "on_error" in result["next_nodes"]
        assert node.get_output_value("error_message") == "Caught error"

    @pytest.mark.asyncio
    async def test_on_error_finally_block(self, execution_context) -> None:
        """Test OnErrorNode executes finally block after error handling."""
        from casare_rpa.nodes.error_handling_nodes import OnErrorNode

        node = OnErrorNode(node_id="test_on_error_finally")

        # Enter protected block
        await node.execute(execution_context)

        # Set error state with error already handled
        state_key = f"{node.node_id}_error_state"
        execution_context.variables[state_key]["error_occurred"] = True
        execution_context.variables[state_key]["error_handled"] = True
        execution_context.variables[state_key]["finally_executed"] = False

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "finally" in result["next_nodes"]


class TestErrorRecoveryNode:
    """Tests for ErrorRecoveryNode strategy configuration."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        return context

    @pytest.mark.asyncio
    async def test_recovery_stop_strategy(self, execution_context) -> None:
        """Test ErrorRecoveryNode configures stop strategy."""
        from casare_rpa.nodes.error_handling_nodes import ErrorRecoveryNode

        node = ErrorRecoveryNode(
            node_id="test_recovery_stop", config={"strategy": "stop"}
        )
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["strategy"] == "stop"
        assert execution_context.variables["_error_recovery_strategy"] == "stop"

    @pytest.mark.asyncio
    async def test_recovery_continue_strategy(self, execution_context) -> None:
        """Test ErrorRecoveryNode configures continue strategy."""
        from casare_rpa.nodes.error_handling_nodes import ErrorRecoveryNode

        node = ErrorRecoveryNode(
            node_id="test_recovery_continue", config={"strategy": "continue"}
        )
        result = await node.execute(execution_context)

        assert result["data"]["strategy"] == "continue"
        assert execution_context.variables["_error_recovery_strategy"] == "continue"

    @pytest.mark.asyncio
    async def test_recovery_retry_strategy(self, execution_context) -> None:
        """Test ErrorRecoveryNode configures retry strategy with max_retries."""
        from casare_rpa.nodes.error_handling_nodes import ErrorRecoveryNode

        node = ErrorRecoveryNode(
            node_id="test_recovery_retry",
            config={"strategy": "retry", "max_retries": 5},
        )
        result = await node.execute(execution_context)

        assert result["data"]["strategy"] == "retry"
        assert result["data"]["max_retries"] == 5
        assert execution_context.variables["_error_recovery_max_retries"] == 5

    @pytest.mark.asyncio
    async def test_recovery_invalid_strategy_defaults_to_stop(
        self, execution_context
    ) -> None:
        """Test ErrorRecoveryNode defaults to stop for invalid strategy."""
        from casare_rpa.nodes.error_handling_nodes import ErrorRecoveryNode

        node = ErrorRecoveryNode(
            node_id="test_recovery_invalid", config={"strategy": "invalid"}
        )
        result = await node.execute(execution_context)

        assert result["data"]["strategy"] == "stop"

    @pytest.mark.asyncio
    async def test_recovery_with_input_ports(self, execution_context) -> None:
        """Test ErrorRecoveryNode accepts strategy from input port."""
        from casare_rpa.nodes.error_handling_nodes import ErrorRecoveryNode

        node = ErrorRecoveryNode(node_id="test_recovery_input")
        node.set_input_value("strategy", "fallback")
        node.set_input_value("max_retries", 10)
        result = await node.execute(execution_context)

        assert result["data"]["strategy"] == "fallback"
        assert result["data"]["max_retries"] == 10


class TestWebhookNotifyNode:
    """Tests for WebhookNotifyNode notification sending."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        return context

    @pytest.mark.asyncio
    async def test_webhook_missing_url(self, execution_context) -> None:
        """Test WebhookNotifyNode fails without URL."""
        from casare_rpa.nodes.error_handling_nodes import WebhookNotifyNode

        node = WebhookNotifyNode(node_id="test_webhook_no_url")
        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "No webhook URL provided" in result["error"]

    @pytest.mark.asyncio
    async def test_webhook_success(self, execution_context) -> None:
        """Test WebhookNotifyNode sends notification successfully."""
        from casare_rpa.nodes.error_handling_nodes import WebhookNotifyNode

        node = WebhookNotifyNode(
            node_id="test_webhook_success",
            config={"webhook_url": "https://example.com/webhook", "timeout": 5},
        )
        node.set_input_value("message", "Test notification")

        # Mock aiohttp
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='{"status": "ok"}')

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.post = MagicMock(
            return_value=MagicMock(
                __aenter__=AsyncMock(return_value=mock_response),
                __aexit__=AsyncMock(return_value=None),
            )
        )

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("success") is True

    @pytest.mark.asyncio
    async def test_webhook_slack_format(self, execution_context) -> None:
        """Test WebhookNotifyNode builds Slack format payload."""
        from casare_rpa.nodes.error_handling_nodes import WebhookNotifyNode

        node = WebhookNotifyNode(
            node_id="test_webhook_slack", config={"format": "slack"}
        )

        payload = node._build_payload("Test message", {"key": "value"})

        assert "text" in payload
        assert payload["text"] == "Test message"
        assert "attachments" in payload

    @pytest.mark.asyncio
    async def test_webhook_discord_format(self, execution_context) -> None:
        """Test WebhookNotifyNode builds Discord format payload."""
        from casare_rpa.nodes.error_handling_nodes import WebhookNotifyNode

        node = WebhookNotifyNode(
            node_id="test_webhook_discord", config={"format": "discord"}
        )

        payload = node._build_payload("Test message", {"key": "value"})

        assert "content" in payload
        assert payload["content"] == "Test message"
        assert "embeds" in payload

    @pytest.mark.asyncio
    async def test_webhook_teams_format(self, execution_context) -> None:
        """Test WebhookNotifyNode builds Teams format payload."""
        from casare_rpa.nodes.error_handling_nodes import WebhookNotifyNode

        node = WebhookNotifyNode(
            node_id="test_webhook_teams", config={"format": "teams"}
        )

        payload = node._build_payload("Test message", {"key": "value"})

        assert "@type" in payload
        assert payload["@type"] == "MessageCard"
        assert "sections" in payload


class TestErrorHandlingNodesIntegration:
    """Integration tests for error handling nodes with ExecutionResult pattern."""

    def test_all_nodes_have_execute_method(self) -> None:
        """Test all error handling nodes implement execute method."""
        from casare_rpa.nodes.error_handling_nodes import (
            TryNode,
            ThrowErrorNode,
            RetryNode,
            AssertNode,
            LogErrorNode,
            OnErrorNode,
            ErrorRecoveryNode,
            RetrySuccessNode,
            RetryFailNode,
            WebhookNotifyNode,
        )

        node_classes = [
            TryNode,
            ThrowErrorNode,
            RetryNode,
            AssertNode,
            LogErrorNode,
            OnErrorNode,
            ErrorRecoveryNode,
            RetrySuccessNode,
            RetryFailNode,
            WebhookNotifyNode,
        ]

        for cls in node_classes:
            node = cls(node_id=f"test_{cls.__name__}")
            assert hasattr(node, "execute")
            assert callable(node.execute)

    def test_all_nodes_have_define_ports(self) -> None:
        """Test all error handling nodes define ports correctly."""
        from casare_rpa.nodes.error_handling_nodes import (
            TryNode,
            ThrowErrorNode,
            RetryNode,
            AssertNode,
            LogErrorNode,
            OnErrorNode,
            ErrorRecoveryNode,
            RetrySuccessNode,
            RetryFailNode,
            WebhookNotifyNode,
        )

        node_classes = [
            TryNode,
            ThrowErrorNode,
            RetryNode,
            AssertNode,
            LogErrorNode,
            OnErrorNode,
            ErrorRecoveryNode,
            RetrySuccessNode,
            RetryFailNode,
            WebhookNotifyNode,
        ]

        for cls in node_classes:
            node = cls(node_id=f"test_{cls.__name__}")
            # All nodes should have exec_in input port
            assert "exec_in" in node.input_ports

    def test_execution_result_pattern_compliance(self) -> None:
        """Test ExecutionResult contains required keys."""
        from casare_rpa.nodes.error_handling_nodes import AssertNode

        node = AssertNode(node_id="test_result_pattern", config={"condition": True})

        # ExecutionResult should be a TypedDict with success, data, next_nodes, error
        import asyncio

        context = Mock(spec=ExecutionContext)
        context.variables = {}

        result = asyncio.get_event_loop().run_until_complete(node.execute(context))

        assert "success" in result
        assert isinstance(result["success"], bool)
        # next_nodes is optional but commonly used
        if result["success"]:
            assert "next_nodes" in result
