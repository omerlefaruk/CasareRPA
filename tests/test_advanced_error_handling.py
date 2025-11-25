"""
Tests for Advanced Error Handling features.

Tests cover:
- Global Error Handler
- Error Analytics
- Error Notification Nodes
- Error Recovery Strategies
- Assert Node
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from casare_rpa.utils.error_handler import (
    GlobalErrorHandler,
    ErrorAnalytics,
    ErrorRecord,
    ErrorPattern,
    RecoveryStrategy,
    ErrorSeverity,
    get_global_error_handler,
    reset_global_error_handler,
)
from casare_rpa.nodes.error_handling_nodes import (
    WebhookNotifyNode,
    OnErrorNode,
    ErrorRecoveryNode,
    LogErrorNode,
    AssertNode,
)
from casare_rpa.core.execution_context import ExecutionContext
from casare_rpa.core.types import NodeStatus


@pytest.fixture
def execution_context():
    """Create an execution context for testing."""
    return ExecutionContext(workflow_name="test_workflow")


@pytest.fixture
def error_analytics():
    """Create a fresh ErrorAnalytics instance."""
    return ErrorAnalytics(max_history=100)


@pytest.fixture
def global_error_handler():
    """Create a fresh GlobalErrorHandler instance."""
    reset_global_error_handler()
    return GlobalErrorHandler()


# =============================================================================
# Error Analytics Tests
# =============================================================================

class TestErrorAnalytics:
    """Tests for ErrorAnalytics class."""

    def test_record_error(self, error_analytics):
        """Test recording an error."""
        error = ErrorRecord(
            timestamp=datetime.now(),
            workflow_id="wf_1",
            workflow_name="Test Workflow",
            node_id="node_1",
            node_type="TestNode",
            error_type="ValueError",
            error_message="Test error",
            stack_trace="",
            severity=ErrorSeverity.ERROR,
        )

        error_analytics.record_error(error)

        assert len(error_analytics._history) == 1
        assert "ValueError" in error_analytics._patterns
        assert error_analytics._patterns["ValueError"].count == 1

    def test_get_top_errors(self, error_analytics):
        """Test getting top errors by frequency."""
        # Record multiple errors of different types
        for i in range(5):
            error_analytics.record_error(ErrorRecord(
                timestamp=datetime.now(),
                workflow_id="wf_1",
                workflow_name="Test",
                node_id="node_1",
                node_type="TestNode",
                error_type="ValueError",
                error_message="Value error",
                stack_trace="",
                severity=ErrorSeverity.ERROR,
            ))

        for i in range(3):
            error_analytics.record_error(ErrorRecord(
                timestamp=datetime.now(),
                workflow_id="wf_1",
                workflow_name="Test",
                node_id="node_2",
                node_type="TestNode",
                error_type="TypeError",
                error_message="Type error",
                stack_trace="",
                severity=ErrorSeverity.ERROR,
            ))

        top_errors = error_analytics.get_top_errors(limit=2)

        assert len(top_errors) == 2
        assert top_errors[0]["error_type"] == "ValueError"
        assert top_errors[0]["count"] == 5
        assert top_errors[1]["error_type"] == "TypeError"
        assert top_errors[1]["count"] == 3

    def test_get_recent_errors(self, error_analytics):
        """Test getting recent errors within time window."""
        # Record an old error
        old_error = ErrorRecord(
            timestamp=datetime.now() - timedelta(hours=48),
            workflow_id="wf_1",
            workflow_name="Test",
            node_id="node_1",
            node_type="TestNode",
            error_type="OldError",
            error_message="Old error",
            stack_trace="",
            severity=ErrorSeverity.ERROR,
        )
        error_analytics.record_error(old_error)

        # Record a recent error
        recent_error = ErrorRecord(
            timestamp=datetime.now(),
            workflow_id="wf_1",
            workflow_name="Test",
            node_id="node_2",
            node_type="TestNode",
            error_type="RecentError",
            error_message="Recent error",
            stack_trace="",
            severity=ErrorSeverity.ERROR,
        )
        error_analytics.record_error(recent_error)

        recent = error_analytics.get_recent_errors(hours=24)

        assert len(recent) == 1
        assert recent[0]["error_type"] == "RecentError"

    def test_get_error_rate(self, error_analytics):
        """Test calculating error rate."""
        # Record 10 errors in the last hour
        for i in range(10):
            error_analytics.record_error(ErrorRecord(
                timestamp=datetime.now(),
                workflow_id="wf_1",
                workflow_name="Test",
                node_id="node_1",
                node_type="TestNode",
                error_type="Error",
                error_message="Error",
                stack_trace="",
                severity=ErrorSeverity.ERROR,
            ))

        rate = error_analytics.get_error_rate(hours=1)

        assert rate == 10.0

    def test_get_summary(self, error_analytics):
        """Test getting analytics summary."""
        error_analytics.record_error(ErrorRecord(
            timestamp=datetime.now(),
            workflow_id="wf_1",
            workflow_name="Test",
            node_id="node_1",
            node_type="TestNode",
            error_type="TestError",
            error_message="Test",
            stack_trace="",
            severity=ErrorSeverity.ERROR,
        ))

        summary = error_analytics.get_summary()

        assert summary["total_errors"] == 1
        assert summary["unique_error_types"] == 1
        assert "error_rate_1h" in summary
        assert "top_errors" in summary

    def test_max_history_limit(self, error_analytics):
        """Test that history is limited to max size."""
        error_analytics._max_history = 10

        for i in range(20):
            error_analytics.record_error(ErrorRecord(
                timestamp=datetime.now(),
                workflow_id="wf_1",
                workflow_name="Test",
                node_id=f"node_{i}",
                node_type="TestNode",
                error_type="Error",
                error_message=f"Error {i}",
                stack_trace="",
                severity=ErrorSeverity.ERROR,
            ))

        assert len(error_analytics._history) == 10

    def test_clear(self, error_analytics):
        """Test clearing analytics data."""
        error_analytics.record_error(ErrorRecord(
            timestamp=datetime.now(),
            workflow_id="wf_1",
            workflow_name="Test",
            node_id="node_1",
            node_type="TestNode",
            error_type="Error",
            error_message="Test",
            stack_trace="",
            severity=ErrorSeverity.ERROR,
        ))

        error_analytics.clear()

        assert len(error_analytics._history) == 0
        assert len(error_analytics._patterns) == 0


# =============================================================================
# Global Error Handler Tests
# =============================================================================

class TestGlobalErrorHandler:
    """Tests for GlobalErrorHandler class."""

    def test_default_strategy(self, global_error_handler):
        """Test default recovery strategy."""
        strategy = global_error_handler.get_strategy("UnknownError")
        assert strategy == RecoveryStrategy.STOP

    def test_set_strategy_for_error(self, global_error_handler):
        """Test setting strategy for specific error type."""
        global_error_handler.set_strategy_for_error("TimeoutError", RecoveryStrategy.RETRY)

        strategy = global_error_handler.get_strategy("TimeoutError")
        assert strategy == RecoveryStrategy.RETRY

    def test_set_fallback_workflow(self, global_error_handler):
        """Test setting fallback workflow for error type."""
        global_error_handler.set_fallback_workflow("CriticalError", "fallback_wf_1")

        strategy = global_error_handler.get_strategy("CriticalError")
        fallback = global_error_handler.get_fallback_workflow("CriticalError")

        assert strategy == RecoveryStrategy.FALLBACK
        assert fallback == "fallback_wf_1"

    @pytest.mark.asyncio
    async def test_handle_error(self, global_error_handler):
        """Test handling an error."""
        exception = ValueError("Test error")

        strategy = await global_error_handler.handle_error(
            exception=exception,
            workflow_id="wf_1",
            workflow_name="Test Workflow",
            node_id="node_1",
            node_type="TestNode",
        )

        assert strategy == RecoveryStrategy.STOP
        assert len(global_error_handler.analytics._history) == 1

    @pytest.mark.asyncio
    async def test_handle_error_with_custom_strategy(self, global_error_handler):
        """Test handling error with custom strategy."""
        global_error_handler.set_strategy_for_error("ValueError", RecoveryStrategy.CONTINUE)

        exception = ValueError("Test error")
        strategy = await global_error_handler.handle_error(
            exception=exception,
            workflow_id="wf_1",
            workflow_name="Test",
            node_id="node_1",
            node_type="TestNode",
        )

        assert strategy == RecoveryStrategy.CONTINUE

    @pytest.mark.asyncio
    async def test_notification_handler(self, global_error_handler):
        """Test notification handler is called on error."""
        notification_received = []

        async def mock_handler(error: ErrorRecord):
            notification_received.append(error)

        global_error_handler.add_notification_handler(mock_handler)

        await global_error_handler.handle_error(
            exception=ValueError("Test"),
            workflow_id="wf_1",
            workflow_name="Test",
            node_id="node_1",
            node_type="TestNode",
        )

        assert len(notification_received) == 1
        assert notification_received[0].error_type == "ValueError"

    def test_enable_disable(self, global_error_handler):
        """Test enabling and disabling handler."""
        global_error_handler.enable(False)
        assert global_error_handler._enabled == False

        global_error_handler.enable(True)
        assert global_error_handler._enabled == True

    def test_get_config(self, global_error_handler):
        """Test getting handler configuration."""
        global_error_handler.set_strategy_for_error("TestError", RecoveryStrategy.RETRY)

        config = global_error_handler.get_config()

        assert config["enabled"] == True
        assert config["default_strategy"] == "stop"
        assert "TestError" in config["strategy_map"]

    def test_singleton(self):
        """Test global error handler singleton."""
        reset_global_error_handler()
        handler1 = get_global_error_handler()
        handler2 = get_global_error_handler()

        assert handler1 is handler2


# =============================================================================
# Error Handling Node Tests
# =============================================================================

class TestWebhookNotifyNode:
    """Tests for WebhookNotifyNode."""

    @pytest.mark.asyncio
    async def test_missing_url(self, execution_context):
        """Test error when webhook URL is missing."""
        node = WebhookNotifyNode(node_id="webhook_1")

        result = await node.execute(execution_context)

        assert result["success"] == False
        assert "No webhook URL" in result["error"]

    @pytest.mark.asyncio
    async def test_build_slack_payload(self, execution_context):
        """Test building Slack-formatted payload."""
        node = WebhookNotifyNode(
            node_id="webhook_1",
            config={"format": "slack"}
        )

        payload = node._build_payload("Test message", {"key": "value"})

        assert payload["text"] == "Test message"
        assert "attachments" in payload

    @pytest.mark.asyncio
    async def test_build_discord_payload(self, execution_context):
        """Test building Discord-formatted payload."""
        node = WebhookNotifyNode(
            node_id="webhook_1",
            config={"format": "discord"}
        )

        payload = node._build_payload("Test message", {"key": "value"})

        assert payload["content"] == "Test message"
        assert "embeds" in payload

    @pytest.mark.asyncio
    async def test_build_teams_payload(self, execution_context):
        """Test building Teams-formatted payload."""
        node = WebhookNotifyNode(
            node_id="webhook_1",
            config={"format": "teams"}
        )

        payload = node._build_payload("Test message", {"key": "value"})

        assert payload["@type"] == "MessageCard"
        assert "sections" in payload


class TestOnErrorNode:
    """Tests for OnErrorNode."""

    @pytest.mark.asyncio
    async def test_enter_protected_block(self, execution_context):
        """Test entering protected block."""
        node = OnErrorNode(node_id="onerror_1")

        result = await node.execute(execution_context)

        assert result["success"] == True
        assert "protected_body" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_error_handling_path(self, execution_context):
        """Test routing to error handler on error."""
        node = OnErrorNode(node_id="onerror_1")

        # Enter protected block
        await node.execute(execution_context)

        # Simulate error
        state_key = f"{node.node_id}_error_state"
        execution_context.variables[state_key]["error_occurred"] = True
        execution_context.variables[state_key]["error_message"] = "Test error"
        execution_context.variables[state_key]["error_type"] = "TestError"

        # Re-execute to handle error
        result = await node.execute(execution_context)

        assert result["success"] == True
        assert "on_error" in result["next_nodes"]
        assert node.get_output_value("error_message") == "Test error"

    @pytest.mark.asyncio
    async def test_finally_execution(self, execution_context):
        """Test finally block execution."""
        node = OnErrorNode(node_id="onerror_1")

        # Enter protected block
        await node.execute(execution_context)

        # Mark as successful (no error)
        state_key = f"{node.node_id}_error_state"

        # Execute again for finally
        result = await node.execute(execution_context)

        assert "finally" in result["next_nodes"]


class TestErrorRecoveryNode:
    """Tests for ErrorRecoveryNode."""

    @pytest.mark.asyncio
    async def test_configure_stop_strategy(self, execution_context):
        """Test configuring stop strategy."""
        node = ErrorRecoveryNode(
            node_id="recovery_1",
            config={"strategy": "stop"}
        )

        result = await node.execute(execution_context)

        assert result["success"] == True
        assert execution_context.variables["_error_recovery_strategy"] == "stop"

    @pytest.mark.asyncio
    async def test_configure_continue_strategy(self, execution_context):
        """Test configuring continue strategy."""
        node = ErrorRecoveryNode(
            node_id="recovery_1",
            config={"strategy": "continue", "max_retries": 5}
        )

        result = await node.execute(execution_context)

        assert result["success"] == True
        assert execution_context.variables["_error_recovery_strategy"] == "continue"
        assert execution_context.variables["_error_recovery_max_retries"] == 5

    @pytest.mark.asyncio
    async def test_invalid_strategy_defaults_to_stop(self, execution_context):
        """Test invalid strategy defaults to stop."""
        node = ErrorRecoveryNode(
            node_id="recovery_1",
            config={"strategy": "invalid_strategy"}
        )

        result = await node.execute(execution_context)

        assert execution_context.variables["_error_recovery_strategy"] == "stop"


class TestLogErrorNode:
    """Tests for LogErrorNode."""

    @pytest.mark.asyncio
    async def test_log_error(self, execution_context):
        """Test logging error details."""
        node = LogErrorNode(
            node_id="log_1",
            config={"level": "error"}
        )
        node.set_input_value("error_message", "Test error message")
        node.set_input_value("error_type", "TestError")

        result = await node.execute(execution_context)

        assert result["success"] == True
        log_entry = node.get_output_value("log_entry")
        assert log_entry["error_message"] == "Test error message"
        assert log_entry["error_type"] == "TestError"
        assert log_entry["level"] == "error"

    @pytest.mark.asyncio
    async def test_log_with_context(self, execution_context):
        """Test logging with additional context."""
        node = LogErrorNode(node_id="log_1")
        node.set_input_value("error_message", "Error")
        node.set_input_value("context", {"user": "test", "action": "save"})

        result = await node.execute(execution_context)

        log_entry = node.get_output_value("log_entry")
        assert log_entry["context"]["user"] == "test"

    @pytest.mark.asyncio
    async def test_different_log_levels(self, execution_context):
        """Test different log levels."""
        for level in ["debug", "info", "warning", "error", "critical"]:
            node = LogErrorNode(
                node_id=f"log_{level}",
                config={"level": level}
            )
            node.set_input_value("error_message", "Test")

            result = await node.execute(execution_context)

            assert result["success"] == True
            assert node.get_output_value("log_entry")["level"] == level


class TestAssertNode:
    """Tests for AssertNode."""

    @pytest.mark.asyncio
    async def test_assertion_passes(self, execution_context):
        """Test assertion that passes."""
        node = AssertNode(node_id="assert_1")
        node.set_input_value("condition", True)
        node.set_input_value("message", "Value should be true")

        result = await node.execute(execution_context)

        assert result["success"] == True
        assert node.get_output_value("passed") == True

    @pytest.mark.asyncio
    async def test_assertion_fails(self, execution_context):
        """Test assertion that fails."""
        node = AssertNode(node_id="assert_1")
        node.set_input_value("condition", False)
        node.set_input_value("message", "Expected true but got false")

        result = await node.execute(execution_context)

        assert result["success"] == False
        assert "Assertion failed" in result["error"]
        assert node.get_output_value("passed") == False

    @pytest.mark.asyncio
    async def test_assertion_with_string_true(self, execution_context):
        """Test assertion with string 'true'."""
        node = AssertNode(node_id="assert_1")
        node.set_input_value("condition", "true")

        result = await node.execute(execution_context)

        assert result["success"] == True

    @pytest.mark.asyncio
    async def test_assertion_with_string_false(self, execution_context):
        """Test assertion with string 'false'."""
        node = AssertNode(node_id="assert_1")
        node.set_input_value("condition", "false")
        node.set_input_value("message", "Should fail")

        result = await node.execute(execution_context)

        assert result["success"] == False


# =============================================================================
# Integration Tests
# =============================================================================

class TestErrorHandlingIntegration:
    """Integration tests for error handling system."""

    @pytest.mark.asyncio
    async def test_error_flow_with_analytics(self, execution_context):
        """Test complete error flow with analytics tracking."""
        handler = GlobalErrorHandler()

        # Configure handler
        handler.set_strategy_for_error("ValueError", RecoveryStrategy.CONTINUE)

        # Handle multiple errors
        for i in range(3):
            await handler.handle_error(
                exception=ValueError(f"Error {i}"),
                workflow_id="wf_1",
                workflow_name="Test",
                node_id=f"node_{i}",
                node_type="TestNode",
            )

        # Check analytics
        summary = handler.analytics.get_summary()
        assert summary["total_errors"] == 3

        top_errors = handler.analytics.get_top_errors(limit=1)
        assert top_errors[0]["count"] == 3

    @pytest.mark.asyncio
    async def test_notification_on_critical_error(self, execution_context):
        """Test notification is sent for critical errors."""
        handler = GlobalErrorHandler()
        notifications = []

        async def capture_notification(error: ErrorRecord):
            notifications.append(error)

        handler.add_notification_handler(capture_notification)

        # Trigger critical error
        await handler.handle_error(
            exception=MemoryError("Out of memory"),
            workflow_id="wf_1",
            workflow_name="Test",
            node_id="node_1",
            node_type="TestNode",
        )

        assert len(notifications) == 1
        assert notifications[0].severity == ErrorSeverity.CRITICAL

    @pytest.mark.asyncio
    async def test_error_recovery_node_integration(self, execution_context):
        """Test ErrorRecoveryNode sets context for workflow."""
        # Configure recovery
        recovery_node = ErrorRecoveryNode(
            node_id="recovery_1",
            config={"strategy": "retry", "max_retries": 5}
        )
        await recovery_node.execute(execution_context)

        # Verify context is set
        assert execution_context.variables["_error_recovery_strategy"] == "retry"
        assert execution_context.variables["_error_recovery_max_retries"] == 5

        # Log error node can use this context
        log_node = LogErrorNode(node_id="log_1")
        log_node.set_input_value("error_message", "Test error")
        log_node.set_input_value("context", {
            "recovery_strategy": execution_context.variables["_error_recovery_strategy"]
        })

        result = await log_node.execute(execution_context)
        log_entry = log_node.get_output_value("log_entry")

        assert log_entry["context"]["recovery_strategy"] == "retry"
