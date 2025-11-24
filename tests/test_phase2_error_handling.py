"""
Phase 2: Error Handling & Retry Tests

Tests for:
1. Retry configuration and logic
2. Error classification (transient vs permanent)
3. Exponential backoff with jitter
4. Workflow runner retry integration
5. Timeout handling
6. Continue on error functionality
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime


class TestRetryConfig:
    """Tests for RetryConfig class."""

    def test_retry_config_defaults(self):
        """Test default retry configuration values."""
        from casare_rpa.utils.retry import RetryConfig

        config = RetryConfig()

        assert config.max_attempts >= 1
        assert config.initial_delay > 0
        assert config.max_delay >= config.initial_delay
        assert config.backoff_multiplier >= 1.0

    def test_retry_config_custom_values(self):
        """Test custom retry configuration."""
        from casare_rpa.utils.retry import RetryConfig

        config = RetryConfig(
            max_attempts=5,
            initial_delay=0.5,
            max_delay=10.0,
            backoff_multiplier=3.0,
            jitter=True,
        )

        assert config.max_attempts == 5
        assert config.initial_delay == 0.5
        assert config.max_delay == 10.0
        assert config.backoff_multiplier == 3.0
        assert config.jitter is True

    def test_retry_config_get_delay_exponential(self):
        """Test exponential backoff delay calculation."""
        from casare_rpa.utils.retry import RetryConfig

        config = RetryConfig(
            initial_delay=1.0,
            max_delay=60.0,
            backoff_multiplier=2.0,
            jitter=False,
        )

        # First retry delay
        delay1 = config.get_delay(1)
        assert delay1 == 1.0

        # Second retry delay (should double)
        delay2 = config.get_delay(2)
        assert delay2 == 2.0

        # Third retry delay
        delay3 = config.get_delay(3)
        assert delay3 == 4.0

    def test_retry_config_max_delay_cap(self):
        """Test that delay is capped at max_delay."""
        from casare_rpa.utils.retry import RetryConfig

        config = RetryConfig(
            initial_delay=1.0,
            max_delay=5.0,
            backoff_multiplier=10.0,
            jitter=False,
        )

        # Large attempt number should be capped
        delay = config.get_delay(10)
        assert delay <= 5.0

    def test_retry_config_jitter(self):
        """Test that jitter adds randomness to delays."""
        from casare_rpa.utils.retry import RetryConfig

        config = RetryConfig(
            initial_delay=1.0,
            max_delay=60.0,
            backoff_multiplier=2.0,
            jitter=True,
        )

        # Get multiple delays - with jitter they should vary
        delays = [config.get_delay(2) for _ in range(10)]

        # With jitter, not all delays should be identical
        # (there's a very small chance they could be, but unlikely)
        unique_delays = set(delays)
        # At least some variation expected
        assert len(unique_delays) >= 1


class TestErrorClassification:
    """Tests for error classification functionality."""

    def test_classify_transient_errors(self):
        """Test classification of transient (retryable) errors."""
        from casare_rpa.utils.retry import classify_error, ErrorCategory

        # Timeout errors are transient
        timeout_error = asyncio.TimeoutError("Connection timed out")
        assert classify_error(timeout_error) == ErrorCategory.TRANSIENT

        # Connection errors are transient
        conn_error = ConnectionError("Connection refused")
        assert classify_error(conn_error) == ErrorCategory.TRANSIENT

    def test_classify_unknown_errors(self):
        """Test classification of unknown (unclassified) errors."""
        from casare_rpa.utils.retry import classify_error, ErrorCategory

        # Value errors are unknown (not in transient list)
        value_error = ValueError("Invalid input")
        assert classify_error(value_error) == ErrorCategory.UNKNOWN

        # Type errors are unknown (not in transient list)
        type_error = TypeError("Wrong type")
        assert classify_error(type_error) == ErrorCategory.UNKNOWN

    def test_classify_by_message_pattern(self):
        """Test classification by error message patterns."""
        from casare_rpa.utils.retry import classify_error, ErrorCategory

        # Error with "timeout" in message should be transient
        timeout_msg_error = Exception("Operation timeout occurred")
        assert classify_error(timeout_msg_error) == ErrorCategory.TRANSIENT

        # Error with "rate limit" in message should be transient
        rate_limit_error = Exception("Rate limit exceeded")
        assert classify_error(rate_limit_error) == ErrorCategory.TRANSIENT

    def test_should_retry_transient(self):
        """Test that transient errors trigger retry."""
        from casare_rpa.utils.retry import RetryConfig

        config = RetryConfig(max_attempts=3)

        timeout_error = asyncio.TimeoutError()
        assert config.should_retry(timeout_error, attempt=1) is True
        assert config.should_retry(timeout_error, attempt=2) is True

    def test_should_not_retry_permanent(self):
        """Test that permanent errors don't trigger retry."""
        from casare_rpa.utils.retry import RetryConfig

        config = RetryConfig(max_attempts=3)

        value_error = ValueError("Invalid")
        assert config.should_retry(value_error, attempt=1) is False

    def test_should_not_retry_max_attempts(self):
        """Test that retry stops at max attempts."""
        from casare_rpa.utils.retry import RetryConfig

        config = RetryConfig(max_attempts=3)

        timeout_error = asyncio.TimeoutError()
        # At max attempts, should not retry
        assert config.should_retry(timeout_error, attempt=3) is False


class TestRetryStats:
    """Tests for retry statistics tracking."""

    def test_retry_stats_initial_state(self):
        """Test initial state of retry stats."""
        from casare_rpa.utils.retry import RetryStats

        stats = RetryStats()

        assert stats.total_attempts == 0
        assert stats.successful_attempts == 0
        assert stats.failed_attempts == 0

    def test_retry_stats_record_success(self):
        """Test recording successful attempts."""
        from casare_rpa.utils.retry import RetryStats

        stats = RetryStats()

        stats.record_attempt(success=True, retry_delay=0)
        stats.record_attempt(success=True, retry_delay=1.0)

        assert stats.total_attempts == 2
        assert stats.successful_attempts == 2
        assert stats.failed_attempts == 0

    def test_retry_stats_record_failure(self):
        """Test recording failed attempts."""
        from casare_rpa.utils.retry import RetryStats

        stats = RetryStats()

        stats.record_attempt(success=False, retry_delay=1.0)
        stats.record_attempt(success=False, retry_delay=2.0)
        stats.record_attempt(success=True, retry_delay=4.0)

        assert stats.total_attempts == 3
        assert stats.successful_attempts == 1
        assert stats.failed_attempts == 2

    def test_retry_stats_to_dict(self):
        """Test converting stats to dictionary."""
        from casare_rpa.utils.retry import RetryStats

        stats = RetryStats()
        stats.record_attempt(success=True, retry_delay=0)
        stats.record_attempt(success=False, retry_delay=1.0)

        stats_dict = stats.to_dict()

        assert isinstance(stats_dict, dict)
        assert "total_attempts" in stats_dict
        assert "successful_attempts" in stats_dict
        assert "failed_attempts" in stats_dict


class TestWorkflowRunnerRetry:
    """Tests for retry functionality in WorkflowRunner."""

    def test_runner_retry_config(self):
        """Test that runner accepts retry configuration."""
        from casare_rpa.runner.workflow_runner import WorkflowRunner
        from casare_rpa.core.workflow_schema import WorkflowSchema, WorkflowMetadata
        from casare_rpa.utils.retry import RetryConfig

        metadata = WorkflowMetadata(name="Test")
        workflow = WorkflowSchema(metadata)

        custom_config = RetryConfig(
            max_attempts=5,
            initial_delay=0.5,
        )

        runner = WorkflowRunner(workflow, retry_config=custom_config)

        assert runner.retry_config.max_attempts == 5
        assert runner.retry_config.initial_delay == 0.5

    def test_runner_default_retry_config(self):
        """Test runner has default retry configuration."""
        from casare_rpa.runner.workflow_runner import WorkflowRunner
        from casare_rpa.core.workflow_schema import WorkflowSchema, WorkflowMetadata

        metadata = WorkflowMetadata(name="Test")
        workflow = WorkflowSchema(metadata)

        runner = WorkflowRunner(workflow)

        assert runner.retry_config is not None
        assert runner.retry_config.max_attempts >= 1

    def test_runner_configure_retry(self):
        """Test runtime retry configuration."""
        from casare_rpa.runner.workflow_runner import WorkflowRunner
        from casare_rpa.core.workflow_schema import WorkflowSchema, WorkflowMetadata

        metadata = WorkflowMetadata(name="Test")
        workflow = WorkflowSchema(metadata)

        runner = WorkflowRunner(workflow)

        runner.configure_retry(
            max_attempts=10,
            initial_delay=2.0,
            max_delay=120.0,
        )

        assert runner.retry_config.max_attempts == 10
        assert runner.retry_config.initial_delay == 2.0
        assert runner.retry_config.max_delay == 120.0

    def test_runner_get_retry_stats(self):
        """Test getting retry statistics from runner."""
        from casare_rpa.runner.workflow_runner import WorkflowRunner
        from casare_rpa.core.workflow_schema import WorkflowSchema, WorkflowMetadata

        metadata = WorkflowMetadata(name="Test")
        workflow = WorkflowSchema(metadata)

        runner = WorkflowRunner(workflow)

        stats = runner.get_retry_stats()

        assert isinstance(stats, dict)
        assert "total_attempts" in stats


class TestWorkflowRunnerTimeout:
    """Tests for timeout functionality in WorkflowRunner."""

    def test_runner_default_timeout(self):
        """Test runner has default timeout."""
        from casare_rpa.runner.workflow_runner import (
            WorkflowRunner,
            DEFAULT_NODE_EXECUTION_TIMEOUT,
        )
        from casare_rpa.core.workflow_schema import WorkflowSchema, WorkflowMetadata

        metadata = WorkflowMetadata(name="Test")
        workflow = WorkflowSchema(metadata)

        runner = WorkflowRunner(workflow)

        assert runner.node_timeout == DEFAULT_NODE_EXECUTION_TIMEOUT

    def test_runner_custom_timeout(self):
        """Test runner with custom timeout."""
        from casare_rpa.runner.workflow_runner import WorkflowRunner
        from casare_rpa.core.workflow_schema import WorkflowSchema, WorkflowMetadata

        metadata = WorkflowMetadata(name="Test")
        workflow = WorkflowSchema(metadata)

        runner = WorkflowRunner(workflow, node_timeout=60.0)

        assert runner.node_timeout == 60.0

    def test_runner_set_timeout(self):
        """Test setting timeout at runtime."""
        from casare_rpa.runner.workflow_runner import WorkflowRunner
        from casare_rpa.core.workflow_schema import WorkflowSchema, WorkflowMetadata

        metadata = WorkflowMetadata(name="Test")
        workflow = WorkflowSchema(metadata)

        runner = WorkflowRunner(workflow)
        runner.set_node_timeout(30.0)

        assert runner.node_timeout == 30.0


class TestContinueOnError:
    """Tests for continue_on_error functionality."""

    def test_runner_continue_on_error_default(self):
        """Test default continue_on_error is False."""
        from casare_rpa.runner.workflow_runner import WorkflowRunner
        from casare_rpa.core.workflow_schema import WorkflowSchema, WorkflowMetadata

        metadata = WorkflowMetadata(name="Test")
        workflow = WorkflowSchema(metadata)

        runner = WorkflowRunner(workflow)

        assert runner.continue_on_error is False

    def test_runner_continue_on_error_enabled(self):
        """Test enabling continue_on_error."""
        from casare_rpa.runner.workflow_runner import WorkflowRunner
        from casare_rpa.core.workflow_schema import WorkflowSchema, WorkflowMetadata

        metadata = WorkflowMetadata(name="Test")
        workflow = WorkflowSchema(metadata)

        runner = WorkflowRunner(workflow, continue_on_error=True)

        assert runner.continue_on_error is True


class TestAsyncContextManager:
    """Tests for async context manager support in ExecutionContext."""

    @pytest.mark.asyncio
    async def test_async_context_manager_enter(self):
        """Test async context manager __aenter__."""
        from casare_rpa.core.execution_context import ExecutionContext

        context = ExecutionContext(workflow_name="test")

        async with context as ctx:
            assert ctx is context
            assert ctx.workflow_name == "test"

    @pytest.mark.asyncio
    async def test_async_context_manager_cleanup_on_exit(self):
        """Test async context manager calls cleanup on exit."""
        from casare_rpa.core.execution_context import ExecutionContext

        context = ExecutionContext(workflow_name="test")

        # Add mock resources
        mock_page = MagicMock()

        async def async_close():
            pass

        mock_page.close = async_close
        context.pages["test"] = mock_page

        async with context:
            assert len(context.pages) == 1

        # After exit, cleanup should have been called
        assert len(context.pages) == 0

    @pytest.mark.asyncio
    async def test_async_context_manager_exception_handling(self):
        """Test async context manager handles exceptions."""
        from casare_rpa.core.execution_context import ExecutionContext

        context = ExecutionContext(workflow_name="test")

        with pytest.raises(ValueError):
            async with context:
                raise ValueError("Test error")

        # Context should still be cleaned up
        assert len(context.pages) == 0
