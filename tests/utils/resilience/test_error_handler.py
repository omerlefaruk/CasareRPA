"""Tests for error_handler module."""

from datetime import datetime, timedelta
import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch

from casare_rpa.utils.resilience.error_handler import (
    RecoveryStrategy,
    ErrorSeverity,
    ErrorRecord,
    ErrorPattern,
    ErrorAnalytics,
    GlobalErrorHandler,
    get_global_error_handler,
    reset_global_error_handler,
)


class TestRecoveryStrategy:
    """Tests for RecoveryStrategy enum."""

    def test_enum_values(self):
        """Test that enum values are correct."""
        assert RecoveryStrategy.STOP.value == "stop"
        assert RecoveryStrategy.CONTINUE.value == "continue"
        assert RecoveryStrategy.RETRY.value == "retry"
        assert RecoveryStrategy.RESTART.value == "restart"
        assert RecoveryStrategy.FALLBACK.value == "fallback"
        assert RecoveryStrategy.NOTIFY_AND_STOP.value == "notify_and_stop"


class TestErrorSeverity:
    """Tests for ErrorSeverity enum."""

    def test_enum_values(self):
        """Test that enum values are correct."""
        assert ErrorSeverity.DEBUG.value == "debug"
        assert ErrorSeverity.INFO.value == "info"
        assert ErrorSeverity.WARNING.value == "warning"
        assert ErrorSeverity.ERROR.value == "error"
        assert ErrorSeverity.CRITICAL.value == "critical"


class TestErrorRecord:
    """Tests for ErrorRecord dataclass."""

    def test_default_values(self):
        """Test ErrorRecord with required fields."""
        timestamp = datetime.now()
        record = ErrorRecord(
            timestamp=timestamp,
            workflow_id="wf_123",
            workflow_name="Test Workflow",
            node_id="node_456",
            node_type="ClickNode",
            error_type="ElementNotFoundError",
            error_message="Element not found",
            stack_trace="traceback...",
            severity=ErrorSeverity.ERROR,
        )

        assert record.timestamp == timestamp
        assert record.workflow_id == "wf_123"
        assert record.workflow_name == "Test Workflow"
        assert record.node_id == "node_456"
        assert record.node_type == "ClickNode"
        assert record.error_type == "ElementNotFoundError"
        assert record.error_message == "Element not found"
        assert record.context == {}
        assert record.recovered is False
        assert record.recovery_strategy is None

    def test_to_dict(self):
        """Test ErrorRecord serialization."""
        timestamp = datetime(2024, 1, 15, 10, 30, 0)
        record = ErrorRecord(
            timestamp=timestamp,
            workflow_id="wf_123",
            workflow_name="Test Workflow",
            node_id="node_456",
            node_type="ClickNode",
            error_type="TimeoutError",
            error_message="Operation timed out",
            stack_trace="stack...",
            severity=ErrorSeverity.WARNING,
            context={"url": "https://example.com"},
            recovered=True,
            recovery_strategy=RecoveryStrategy.RETRY,
        )

        data = record.to_dict()

        assert data["timestamp"] == "2024-01-15T10:30:00"
        assert data["workflow_id"] == "wf_123"
        assert data["workflow_name"] == "Test Workflow"
        assert data["node_id"] == "node_456"
        assert data["node_type"] == "ClickNode"
        assert data["error_type"] == "TimeoutError"
        assert data["error_message"] == "Operation timed out"
        assert data["stack_trace"] == "stack..."
        assert data["severity"] == "warning"
        assert data["context"] == {"url": "https://example.com"}
        assert data["recovered"] is True
        assert data["recovery_strategy"] == "retry"


class TestErrorPattern:
    """Tests for ErrorPattern dataclass."""

    def test_default_values(self):
        """Test ErrorPattern with required fields."""
        now = datetime.now()
        pattern = ErrorPattern(
            error_type="ValueError",
            first_seen=now,
            last_seen=now,
        )

        assert pattern.error_type == "ValueError"
        assert pattern.first_seen == now
        assert pattern.last_seen == now
        assert pattern.count == 0
        assert pattern.affected_nodes == set()
        assert pattern.affected_workflows == set()

    def test_to_dict(self):
        """Test ErrorPattern serialization."""
        first = datetime(2024, 1, 1, 0, 0, 0)
        last = datetime(2024, 1, 15, 12, 0, 0)
        pattern = ErrorPattern(
            error_type="ConnectionError",
            first_seen=first,
            last_seen=last,
            count=15,
            affected_nodes={"node_1", "node_2"},
            affected_workflows={"workflow_a"},
        )

        data = pattern.to_dict()

        assert data["error_type"] == "ConnectionError"
        assert data["first_seen"] == "2024-01-01T00:00:00"
        assert data["last_seen"] == "2024-01-15T12:00:00"
        assert data["count"] == 15
        assert set(data["affected_nodes"]) == {"node_1", "node_2"}
        assert data["affected_workflows"] == ["workflow_a"]


class TestErrorAnalytics:
    """Tests for ErrorAnalytics class."""

    def test_initialization(self):
        """Test ErrorAnalytics initialization."""
        analytics = ErrorAnalytics(max_history=500)

        assert analytics._max_history == 500
        assert len(analytics._history) == 0
        assert len(analytics._patterns) == 0

    def test_record_error_first_occurrence(self):
        """Test recording first error of a type."""
        analytics = ErrorAnalytics()
        record = ErrorRecord(
            timestamp=datetime.now(),
            workflow_id="wf_1",
            workflow_name="Workflow 1",
            node_id="node_1",
            node_type="TypeNode",
            error_type="NewError",
            error_message="First occurrence",
            stack_trace="stack...",
            severity=ErrorSeverity.ERROR,
        )

        analytics.record_error(record)

        assert len(analytics._history) == 1
        assert "NewError" in analytics._patterns
        assert analytics._patterns["NewError"].count == 1

    def test_record_error_multiple_occurrences(self):
        """Test recording multiple errors of same type."""
        analytics = ErrorAnalytics()

        for i in range(5):
            record = ErrorRecord(
                timestamp=datetime.now(),
                workflow_id=f"wf_{i}",
                workflow_name=f"Workflow {i}",
                node_id=f"node_{i}",
                node_type="TypeNode",
                error_type="RepeatedError",
                error_message=f"Occurrence {i}",
                stack_trace="stack...",
                severity=ErrorSeverity.ERROR,
            )
            analytics.record_error(record)

        assert len(analytics._history) == 5
        assert analytics._patterns["RepeatedError"].count == 5
        assert len(analytics._patterns["RepeatedError"].affected_nodes) == 5

    def test_record_error_respects_max_history(self):
        """Test that history is limited by max_history."""
        analytics = ErrorAnalytics(max_history=3)

        for i in range(5):
            record = ErrorRecord(
                timestamp=datetime.now(),
                workflow_id=f"wf_{i}",
                workflow_name="Test",
                node_id=f"node_{i}",
                node_type="TypeNode",
                error_type="Error",
                error_message=f"Error {i}",
                stack_trace="stack...",
                severity=ErrorSeverity.ERROR,
            )
            analytics.record_error(record)

        assert len(analytics._history) == 3
        assert analytics._history[0].error_message == "Error 2"

    def test_get_top_errors(self):
        """Test getting top errors by frequency."""
        analytics = ErrorAnalytics()

        # Add errors with different frequencies
        for i in range(10):
            analytics.record_error(self._make_error("CommonError"))
        for i in range(5):
            analytics.record_error(self._make_error("MediumError"))
        for i in range(2):
            analytics.record_error(self._make_error("RareError"))

        top = analytics.get_top_errors(limit=2)

        assert len(top) == 2
        assert top[0]["error_type"] == "CommonError"
        assert top[0]["count"] == 10
        assert top[1]["error_type"] == "MediumError"
        assert top[1]["count"] == 5

    def test_get_recent_errors(self):
        """Test getting recent errors within time window."""
        analytics = ErrorAnalytics()

        # Add old error
        old_record = ErrorRecord(
            timestamp=datetime.now() - timedelta(hours=48),
            workflow_id="wf_old",
            workflow_name="Old",
            node_id="node_old",
            node_type="TypeNode",
            error_type="OldError",
            error_message="Old error",
            stack_trace="stack...",
            severity=ErrorSeverity.ERROR,
        )
        analytics.record_error(old_record)

        # Add recent error
        recent_record = ErrorRecord(
            timestamp=datetime.now(),
            workflow_id="wf_new",
            workflow_name="New",
            node_id="node_new",
            node_type="TypeNode",
            error_type="NewError",
            error_message="New error",
            stack_trace="stack...",
            severity=ErrorSeverity.ERROR,
        )
        analytics.record_error(recent_record)

        recent = analytics.get_recent_errors(hours=24)

        assert len(recent) == 1
        assert recent[0]["error_type"] == "NewError"

    def test_get_error_rate(self):
        """Test error rate calculation."""
        analytics = ErrorAnalytics()

        # Add 10 errors in the last hour
        for i in range(10):
            analytics.record_error(self._make_error("Error"))

        rate = analytics.get_error_rate(hours=1)

        assert rate == 10.0

    def test_get_summary(self):
        """Test getting analytics summary."""
        analytics = ErrorAnalytics()

        for i in range(3):
            analytics.record_error(self._make_error("Error1"))
        for i in range(2):
            analytics.record_error(self._make_error("Error2"))

        summary = analytics.get_summary()

        assert summary["total_errors"] == 5
        assert summary["unique_error_types"] == 2
        assert "error_rate_1h" in summary
        assert "error_rate_24h" in summary
        assert len(summary["top_errors"]) <= 5

    def test_clear(self):
        """Test clearing all analytics data."""
        analytics = ErrorAnalytics()

        for i in range(5):
            analytics.record_error(self._make_error("Error"))

        analytics.clear()

        assert len(analytics._history) == 0
        assert len(analytics._patterns) == 0
        assert len(analytics._error_counts) == 0

    def _make_error(self, error_type: str) -> ErrorRecord:
        """Helper to create error records."""
        return ErrorRecord(
            timestamp=datetime.now(),
            workflow_id="wf_test",
            workflow_name="Test Workflow",
            node_id="node_test",
            node_type="TestNode",
            error_type=error_type,
            error_message="Test error",
            stack_trace="stack...",
            severity=ErrorSeverity.ERROR,
        )


class TestGlobalErrorHandler:
    """Tests for GlobalErrorHandler class."""

    def test_initialization_default(self):
        """Test default initialization."""
        handler = GlobalErrorHandler()

        assert handler._default_strategy == RecoveryStrategy.STOP
        assert handler._enabled is True
        assert len(handler._strategy_map) == 0
        assert len(handler._notification_handlers) == 0

    def test_initialization_custom_strategy(self):
        """Test initialization with custom default strategy."""
        handler = GlobalErrorHandler(default_strategy=RecoveryStrategy.CONTINUE)

        assert handler._default_strategy == RecoveryStrategy.CONTINUE

    def test_set_default_strategy(self):
        """Test setting default strategy."""
        handler = GlobalErrorHandler()

        handler.set_default_strategy(RecoveryStrategy.RETRY)

        assert handler._default_strategy == RecoveryStrategy.RETRY

    def test_set_strategy_for_error(self):
        """Test setting strategy for specific error type."""
        handler = GlobalErrorHandler()

        handler.set_strategy_for_error("TimeoutError", RecoveryStrategy.RETRY)

        assert handler._strategy_map["TimeoutError"] == RecoveryStrategy.RETRY

    def test_set_fallback_workflow(self):
        """Test setting fallback workflow."""
        handler = GlobalErrorHandler()

        handler.set_fallback_workflow("CriticalError", "fallback_wf_123")

        assert handler._fallback_workflows["CriticalError"] == "fallback_wf_123"
        assert handler._strategy_map["CriticalError"] == RecoveryStrategy.FALLBACK

    def test_add_notification_handler(self):
        """Test adding notification handler."""
        handler = GlobalErrorHandler()
        mock_handler = AsyncMock()

        handler.add_notification_handler(mock_handler)

        assert mock_handler in handler._notification_handlers

    def test_remove_notification_handler(self):
        """Test removing notification handler."""
        handler = GlobalErrorHandler()
        mock_handler = AsyncMock()
        handler.add_notification_handler(mock_handler)

        handler.remove_notification_handler(mock_handler)

        assert mock_handler not in handler._notification_handlers

    def test_enable_disable(self):
        """Test enable/disable functionality."""
        handler = GlobalErrorHandler()

        handler.enable(False)
        assert handler._enabled is False

        handler.enable(True)
        assert handler._enabled is True

    def test_get_strategy_configured(self):
        """Test get_strategy returns configured strategy."""
        handler = GlobalErrorHandler()
        handler.set_strategy_for_error("ValueError", RecoveryStrategy.CONTINUE)

        result = handler.get_strategy("ValueError")

        assert result == RecoveryStrategy.CONTINUE

    def test_get_strategy_default(self):
        """Test get_strategy returns default for unconfigured."""
        handler = GlobalErrorHandler(default_strategy=RecoveryStrategy.STOP)

        result = handler.get_strategy("UnknownError")

        assert result == RecoveryStrategy.STOP

    def test_get_fallback_workflow_exists(self):
        """Test get_fallback_workflow returns configured workflow."""
        handler = GlobalErrorHandler()
        handler.set_fallback_workflow("Error", "fallback_123")

        result = handler.get_fallback_workflow("Error")

        assert result == "fallback_123"

    def test_get_fallback_workflow_none(self):
        """Test get_fallback_workflow returns None when not configured."""
        handler = GlobalErrorHandler()

        result = handler.get_fallback_workflow("UnknownError")

        assert result is None

    @pytest.mark.asyncio
    async def test_handle_error_returns_strategy(self):
        """Test handle_error returns appropriate strategy."""
        handler = GlobalErrorHandler()
        handler.set_strategy_for_error("ValueError", RecoveryStrategy.CONTINUE)

        result = await handler.handle_error(
            exception=ValueError("test"),
            workflow_id="wf_1",
            workflow_name="Test",
            node_id="node_1",
            node_type="TestNode",
        )

        assert result == RecoveryStrategy.CONTINUE

    @pytest.mark.asyncio
    async def test_handle_error_records_analytics(self):
        """Test handle_error records to analytics."""
        handler = GlobalErrorHandler()

        await handler.handle_error(
            exception=RuntimeError("test error"),
            workflow_id="wf_1",
            workflow_name="Test Workflow",
            node_id="node_1",
            node_type="TestNode",
        )

        assert len(handler.analytics._history) == 1
        assert handler.analytics._history[0].error_type == "RuntimeError"

    @pytest.mark.asyncio
    async def test_handle_error_sends_notifications(self):
        """Test handle_error sends notifications."""
        handler = GlobalErrorHandler()
        mock_handler = AsyncMock()
        handler.add_notification_handler(mock_handler)

        await handler.handle_error(
            exception=RuntimeError("test"),
            workflow_id="wf_1",
            workflow_name="Test",
            node_id="node_1",
            node_type="TestNode",
        )

        mock_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_error_disabled_returns_default(self):
        """Test handle_error returns default when disabled."""
        handler = GlobalErrorHandler(default_strategy=RecoveryStrategy.STOP)
        handler.set_strategy_for_error("ValueError", RecoveryStrategy.RETRY)
        handler.enable(False)

        result = await handler.handle_error(
            exception=ValueError("test"),
            workflow_id="wf_1",
            workflow_name="Test",
            node_id="node_1",
            node_type="TestNode",
        )

        assert result == RecoveryStrategy.STOP

    @pytest.mark.asyncio
    async def test_classify_severity_critical(self):
        """Test critical errors are classified correctly."""
        handler = GlobalErrorHandler()

        result = await handler.handle_error(
            exception=MemoryError("out of memory"),
            workflow_id="wf_1",
            workflow_name="Test",
            node_id="node_1",
            node_type="TestNode",
        )

        assert handler.analytics._history[0].severity == ErrorSeverity.CRITICAL

    @pytest.mark.asyncio
    async def test_classify_severity_warning(self):
        """Test timeout errors are classified as warning."""
        handler = GlobalErrorHandler()

        await handler.handle_error(
            exception=TimeoutError("timed out"),
            workflow_id="wf_1",
            workflow_name="Test",
            node_id="node_1",
            node_type="TestNode",
        )

        assert handler.analytics._history[0].severity == ErrorSeverity.WARNING

    def test_get_config(self):
        """Test getting error handler configuration."""
        handler = GlobalErrorHandler(default_strategy=RecoveryStrategy.CONTINUE)
        handler.set_strategy_for_error("Error1", RecoveryStrategy.RETRY)
        handler.set_fallback_workflow("Error2", "fallback_wf")

        config = handler.get_config()

        assert config["enabled"] is True
        assert config["default_strategy"] == "continue"
        assert config["strategy_map"]["Error1"] == "retry"
        assert config["strategy_map"]["Error2"] == "fallback"
        assert config["fallback_workflows"]["Error2"] == "fallback_wf"


class TestGlobalSingleton:
    """Tests for global error handler singleton."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_global_error_handler()

    def teardown_method(self):
        """Reset singleton after each test."""
        reset_global_error_handler()

    def test_get_global_error_handler_creates_instance(self):
        """Test that get_global_error_handler creates instance."""
        handler = get_global_error_handler()

        assert handler is not None
        assert isinstance(handler, GlobalErrorHandler)

    def test_get_global_error_handler_returns_same_instance(self):
        """Test that get_global_error_handler returns same instance."""
        handler1 = get_global_error_handler()
        handler2 = get_global_error_handler()

        assert handler1 is handler2

    def test_reset_global_error_handler(self):
        """Test that reset creates new instance."""
        handler1 = get_global_error_handler()
        reset_global_error_handler()
        handler2 = get_global_error_handler()

        assert handler1 is not handler2
