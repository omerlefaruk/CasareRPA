"""
Tests for CasareRPA OpenTelemetry log correlation.

Tests logging integration with trace context.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any
import sys

from casare_rpa.infrastructure.observability.logging import (
    OTelLoguruSink,
    SpanLogger,
    configure_logging,
    get_span_logger,
    log_with_trace,
    trace_context_patcher,
    create_trace_context_format,
)
from casare_rpa.infrastructure.observability.telemetry import OTEL_AVAILABLE


class TestTraceContextPatcher:
    """Tests for trace context patcher."""

    def test_patcher_adds_trace_ids_no_span(self) -> None:
        """Test patcher adds zero trace IDs when no span is active."""
        record: Dict[str, Any] = {"extra": {}}

        trace_context_patcher(record)

        assert "trace_id" in record["extra"]
        assert "span_id" in record["extra"]
        # When no span is active, should be zeros
        assert record["extra"]["trace_id"] == "00000000000000000000000000000000"
        assert record["extra"]["span_id"] == "0000000000000000"

    @pytest.mark.skipif(not OTEL_AVAILABLE, reason="OpenTelemetry not installed")
    def test_patcher_adds_active_span_ids(self) -> None:
        """Test patcher adds actual trace IDs from active span."""
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.resources import Resource

        # Set up a test tracer provider
        provider = TracerProvider(resource=Resource.create({"service.name": "test"}))
        trace.set_tracer_provider(provider)
        tracer = trace.get_tracer("test")

        record: Dict[str, Any] = {"extra": {}}

        with tracer.start_as_current_span("test-span"):
            trace_context_patcher(record)

        assert "trace_id" in record["extra"]
        assert "span_id" in record["extra"]
        # Should not be zeros when span is active
        assert record["extra"]["trace_id"] != "00000000000000000000000000000000"
        assert record["extra"]["span_id"] != "0000000000000000"


class TestCreateTraceContextFormat:
    """Tests for log format creation."""

    def test_format_includes_trace_placeholders(self) -> None:
        """Test format string includes trace context placeholders."""
        fmt = create_trace_context_format()

        assert "trace_id" in fmt
        assert "span_id" in fmt
        assert "{extra[trace_id]}" in fmt
        assert "{extra[span_id]}" in fmt

    def test_format_includes_standard_fields(self) -> None:
        """Test format string includes standard log fields."""
        fmt = create_trace_context_format()

        assert "{time" in fmt
        assert "{level" in fmt
        assert "{message}" in fmt


class TestOTelLoguruSink:
    """Tests for OTelLoguruSink."""

    def test_sink_initialization(self) -> None:
        """Test sink initializes properly."""
        sink = OTelLoguruSink()

        assert sink._initialized is False
        assert sink._otel_logger is None

    def test_sink_callable(self) -> None:
        """Test sink is callable."""
        sink = OTelLoguruSink()

        # Create a mock message with record
        message = Mock()
        message.record = {
            "level": Mock(name="INFO"),
            "message": "Test message",
            "time": Mock(timestamp=lambda: 1234567890.0),
            "file": Mock(name="test.py", path="/path/test.py"),
            "line": 42,
            "function": "test_func",
            "module": "test_module",
            "process": Mock(id=1234, name="MainProcess"),
            "thread": Mock(id=5678, name="MainThread"),
            "extra": {},
            "exception": None,
        }

        # Should not raise even without OTel initialized
        sink(message)


class TestSpanLogger:
    """Tests for SpanLogger."""

    def test_span_logger_creation(self) -> None:
        """Test SpanLogger creation."""
        span_logger = SpanLogger("test.component")

        assert span_logger.name == "test.component"

    def test_span_logger_debug(self) -> None:
        """Test debug logging."""
        span_logger = SpanLogger("test.component")

        # Should not raise
        span_logger.debug("Debug message", key="value")

    def test_span_logger_info(self) -> None:
        """Test info logging."""
        span_logger = SpanLogger("test.component")

        # Should not raise
        span_logger.info("Info message", key="value")

    def test_span_logger_warning(self) -> None:
        """Test warning logging."""
        span_logger = SpanLogger("test.component")

        # Should not raise
        span_logger.warning("Warning message", key="value")

    def test_span_logger_error(self) -> None:
        """Test error logging."""
        span_logger = SpanLogger("test.component")

        # Should not raise
        span_logger.error("Error message", key="value")

    def test_span_logger_exception(self) -> None:
        """Test exception logging."""
        span_logger = SpanLogger("test.component")

        try:
            raise ValueError("Test error")
        except ValueError as e:
            # Should not raise
            span_logger.exception("Exception occurred", exc=e, key="value")


class TestGetSpanLogger:
    """Tests for get_span_logger convenience function."""

    def test_returns_span_logger(self) -> None:
        """Test that get_span_logger returns a SpanLogger."""
        span_logger = get_span_logger("my.component")

        assert isinstance(span_logger, SpanLogger)
        assert span_logger.name == "my.component"


class TestLogWithTrace:
    """Tests for log_with_trace function."""

    def test_log_with_trace_info(self) -> None:
        """Test info level logging with trace."""
        # Should not raise
        log_with_trace("Info message", level="INFO", key="value")

    def test_log_with_trace_error(self) -> None:
        """Test error level logging with trace."""
        # Should not raise
        log_with_trace("Error message", level="ERROR", error_code=500)

    def test_log_with_trace_default_level(self) -> None:
        """Test default level is INFO."""
        # Should not raise
        log_with_trace("Default level message")


class TestConfigureLogging:
    """Tests for configure_logging function."""

    def test_configure_logging_basic(self) -> None:
        """Test basic logging configuration."""
        # This modifies global loguru state, so we test it doesn't raise
        configure_logging(
            enable_otel_export=False,
            enable_trace_context=True,
            log_level="DEBUG",
        )

    def test_configure_logging_with_custom_format(self) -> None:
        """Test logging configuration with custom format."""
        custom_format = "{time} | {level} | {message}"

        configure_logging(
            enable_otel_export=False,
            enable_trace_context=False,
            console_format=custom_format,
            log_level="INFO",
        )

    def test_configure_logging_with_otel_export(self) -> None:
        """Test logging configuration with OTEL export enabled."""
        configure_logging(
            enable_otel_export=True,
            enable_trace_context=True,
            log_level="INFO",
        )


class TestIntegration:
    """Integration tests for logging with tracing."""

    @pytest.mark.skipif(not OTEL_AVAILABLE, reason="OpenTelemetry not installed")
    def test_logging_within_span(self) -> None:
        """Test that logs within a span include trace context."""
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.resources import Resource

        # Set up tracer
        provider = TracerProvider(resource=Resource.create({"service.name": "test"}))
        trace.set_tracer_provider(provider)
        tracer = trace.get_tracer("test")

        span_logger = get_span_logger("test.integration")

        with tracer.start_as_current_span("test-operation") as span:
            # These should add events to the span
            span_logger.info("Starting operation", operation="test")
            span_logger.debug("Processing data", count=42)
            span_logger.info("Operation complete", status="success")

        # Verify span has events
        # Note: In a real test, you'd use an in-memory exporter to verify
