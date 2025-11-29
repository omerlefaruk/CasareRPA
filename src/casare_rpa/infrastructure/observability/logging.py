"""
CasareRPA - Infrastructure: OpenTelemetry Log Correlation

Integrates Loguru with OpenTelemetry for log correlation with traces.
Enables viewing logs in context with distributed traces in observability backends.

Features:
- Automatic trace_id/span_id injection into log records
- OTLP log export to Grafana Loki, Jaeger, or any OTLP backend
- Structured logging with semantic attributes
- Context-aware logging helpers
"""

from __future__ import annotations

import logging
import sys
from typing import Any, Callable, Dict, Optional

from loguru import logger

from casare_rpa.infrastructure.observability.telemetry import (
    TelemetryProvider,
    OTEL_AVAILABLE,
)

if OTEL_AVAILABLE:
    from opentelemetry.trace import get_current_span, Span
    from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor


class OTelLoguruSink:
    """
    Custom Loguru sink that exports logs via OpenTelemetry.

    Converts Loguru log records to OpenTelemetry LogRecords and
    exports them through the configured OTLP exporter.

    Usage:
        sink = OTelLoguruSink()
        logger.add(sink, format="{message}")
    """

    def __init__(self) -> None:
        """Initialize the sink."""
        self._otel_logger: Optional[Any] = None
        self._initialized = False

    def _ensure_initialized(self) -> bool:
        """Ensure OpenTelemetry logger is initialized."""
        if self._initialized:
            return self._otel_logger is not None

        if not OTEL_AVAILABLE:
            self._initialized = True
            return False

        provider = TelemetryProvider.get_instance()
        logger_provider = provider.get_logger_provider()

        if logger_provider:
            try:
                from opentelemetry.sdk._logs import LoggerProvider

                if isinstance(logger_provider, LoggerProvider):
                    self._otel_logger = logger_provider.get_logger(
                        "casare_rpa.loguru",
                        version="1.0.0",
                    )
            except Exception as e:
                logger.warning(f"Failed to get OTel logger: {e}")

        self._initialized = True
        return self._otel_logger is not None

    def __call__(self, message: Any) -> None:
        """
        Process a Loguru log record and export via OpenTelemetry.

        Args:
            message: Loguru message dict containing log record data
        """
        if not self._ensure_initialized():
            return

        if not OTEL_AVAILABLE:
            return

        try:
            record = message.record
            level = record["level"].name
            text = record["message"]

            # Map Loguru levels to OTel severity
            severity_map = {
                "TRACE": 1,
                "DEBUG": 5,
                "INFO": 9,
                "SUCCESS": 9,
                "WARNING": 13,
                "ERROR": 17,
                "CRITICAL": 21,
            }
            severity_number = severity_map.get(level, 9)

            # Build attributes from record
            attributes: Dict[str, Any] = {
                "log.file.name": record["file"].name if record["file"] else "unknown",
                "log.file.path": str(record["file"].path) if record["file"] else "",
                "log.line.number": record["line"],
                "log.function": record["function"],
                "log.module": record["module"],
                "log.process.id": record["process"].id,
                "log.process.name": record["process"].name,
                "log.thread.id": record["thread"].id,
                "log.thread.name": record["thread"].name,
            }

            # Add extra fields
            if record["extra"]:
                for key, value in record["extra"].items():
                    if isinstance(value, (str, int, float, bool)):
                        attributes[f"log.extra.{key}"] = value

            # Add exception info if present
            if record["exception"]:
                exc = record["exception"]
                if exc.type:
                    attributes["exception.type"] = exc.type.__name__
                if exc.value:
                    attributes["exception.message"] = str(exc.value)
                if exc.traceback:
                    import traceback

                    attributes["exception.stacktrace"] = "".join(
                        traceback.format_exception(exc.type, exc.value, exc.traceback)
                    )

            # Emit log via OTel
            if self._otel_logger:
                from opentelemetry.sdk._logs import LogRecord
                from opentelemetry.trace import get_current_span
                from time import time_ns

                span = get_current_span()
                span_context = span.get_span_context() if span else None

                log_record = LogRecord(
                    timestamp=int(record["time"].timestamp() * 1e9),
                    observed_timestamp=time_ns(),
                    body=text,
                    severity_number=severity_number,
                    severity_text=level,
                    attributes=attributes,
                    trace_id=span_context.trace_id if span_context else 0,
                    span_id=span_context.span_id if span_context else 0,
                    trace_flags=span_context.trace_flags if span_context else 0,
                )
                self._otel_logger.emit(log_record)

        except Exception as e:
            # Don't let logging errors break the application
            sys.stderr.write(f"OTel log export error: {e}\n")


def create_trace_context_format() -> str:
    """
    Create a Loguru format string that includes trace context.

    Returns:
        Format string with trace_id and span_id placeholders
    """
    return (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<dim>trace_id={extra[trace_id]}</dim> | "
        "<dim>span_id={extra[span_id]}</dim> | "
        "<level>{message}</level>"
    )


def trace_context_patcher(record: Dict[str, Any]) -> None:
    """
    Loguru patcher that adds trace context to log records.

    Injects trace_id and span_id into the record's extra dict
    for inclusion in formatted log output.

    Args:
        record: Loguru log record dict
    """
    if not OTEL_AVAILABLE:
        record["extra"]["trace_id"] = "00000000000000000000000000000000"
        record["extra"]["span_id"] = "0000000000000000"
        return

    try:
        span = get_current_span()
        if span and span.is_recording():
            ctx = span.get_span_context()
            record["extra"]["trace_id"] = format(ctx.trace_id, "032x")
            record["extra"]["span_id"] = format(ctx.span_id, "016x")
        else:
            record["extra"]["trace_id"] = "00000000000000000000000000000000"
            record["extra"]["span_id"] = "0000000000000000"
    except Exception:
        record["extra"]["trace_id"] = "00000000000000000000000000000000"
        record["extra"]["span_id"] = "0000000000000000"


def configure_logging(
    enable_otel_export: bool = True,
    enable_trace_context: bool = True,
    console_format: Optional[str] = None,
    log_level: str = "INFO",
) -> None:
    """
    Configure Loguru for OpenTelemetry integration.

    Sets up:
    - Trace context injection into log records
    - OTLP log export (if enabled)
    - Console output with trace context

    Args:
        enable_otel_export: Export logs via OTLP
        enable_trace_context: Include trace_id/span_id in logs
        console_format: Custom format for console output
        log_level: Minimum log level
    """
    # Remove default handler
    logger.remove()

    # Add patcher for trace context
    if enable_trace_context:
        logger.configure(patcher=trace_context_patcher)

    # Console handler with trace context
    fmt = console_format or create_trace_context_format()
    logger.add(
        sys.stderr,
        format=fmt,
        level=log_level,
        colorize=True,
    )

    # OTLP export handler
    if enable_otel_export and OTEL_AVAILABLE:
        otel_sink = OTelLoguruSink()
        logger.add(
            otel_sink,
            format="{message}",
            level=log_level,
            serialize=False,
        )

    logger.info("Logging configured with OpenTelemetry integration")


class SpanLogger:
    """
    Context-aware logger that automatically includes span information.

    Provides structured logging methods that record to both Loguru
    and the current OpenTelemetry span.

    Usage:
        span_logger = SpanLogger("workflow_runner")
        span_logger.info("Starting execution", workflow_id="abc123")
    """

    def __init__(self, name: str) -> None:
        """
        Initialize span logger.

        Args:
            name: Logger name for identification
        """
        self.name = name
        self._logger = logger.bind(component=name)

    def _log_with_span(
        self,
        level: str,
        message: str,
        **attributes: Any,
    ) -> None:
        """Log to both Loguru and current span."""
        # Log to Loguru
        log_method = getattr(self._logger, level.lower())
        log_method(message, **attributes)

        # Add event to current span
        if OTEL_AVAILABLE:
            span = get_current_span()
            if span and span.is_recording():
                span.add_event(
                    message,
                    attributes={
                        "log.level": level,
                        "log.component": self.name,
                        **{
                            k: str(v)
                            if not isinstance(v, (str, int, float, bool))
                            else v
                            for k, v in attributes.items()
                        },
                    },
                )

    def debug(self, message: str, **attributes: Any) -> None:
        """Log debug message."""
        self._log_with_span("DEBUG", message, **attributes)

    def info(self, message: str, **attributes: Any) -> None:
        """Log info message."""
        self._log_with_span("INFO", message, **attributes)

    def warning(self, message: str, **attributes: Any) -> None:
        """Log warning message."""
        self._log_with_span("WARNING", message, **attributes)

    def error(self, message: str, **attributes: Any) -> None:
        """Log error message."""
        self._log_with_span("ERROR", message, **attributes)

    def exception(
        self, message: str, exc: Optional[Exception] = None, **attributes: Any
    ) -> None:
        """Log exception with traceback."""
        self._logger.exception(message)

        if OTEL_AVAILABLE and exc:
            span = get_current_span()
            if span and span.is_recording():
                span.record_exception(exc)
                span.add_event(
                    f"Exception: {message}",
                    attributes={
                        "log.level": "ERROR",
                        "log.component": self.name,
                        "exception.type": type(exc).__name__,
                        "exception.message": str(exc),
                        **{
                            k: str(v)
                            if not isinstance(v, (str, int, float, bool))
                            else v
                            for k, v in attributes.items()
                        },
                    },
                )


# =============================================================================
# Convenience Functions
# =============================================================================


def get_span_logger(name: str) -> SpanLogger:
    """
    Get a span-aware logger instance.

    Args:
        name: Logger name

    Returns:
        SpanLogger instance
    """
    return SpanLogger(name)


def log_with_trace(
    message: str,
    level: str = "INFO",
    **attributes: Any,
) -> None:
    """
    Log a message with automatic trace context inclusion.

    Args:
        message: Log message
        level: Log level
        **attributes: Additional attributes to include
    """
    log_method = getattr(logger, level.lower())
    log_method(message, **attributes)

    if OTEL_AVAILABLE:
        span = get_current_span()
        if span and span.is_recording():
            span.add_event(message, attributes=attributes)
