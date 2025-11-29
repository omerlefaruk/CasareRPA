"""
CasareRPA - Infrastructure: Observability Module

OpenTelemetry integration for distributed tracing, metrics, and log aggregation.
Provides production-grade monitoring for the CasareRPA platform.

Key Components:
- TelemetryProvider: Singleton for initializing and managing OpenTelemetry SDK
- Instrumentation decorators: For automatic tracing of functions and methods
- RPAMetricsCollector: Job duration, queue depth, robot utilization metrics
- Log correlation: Automatic trace context injection into logs

Example Usage:
    # Initialize at application startup
    from casare_rpa.infrastructure.observability import (
        TelemetryProvider,
        TelemetryConfig,
        configure_logging,
    )

    config = TelemetryConfig(
        service_name="casare-robot",
        otlp_endpoint="http://localhost:4317",
    )
    TelemetryProvider.get_instance().initialize(config)
    configure_logging(enable_otel_export=True)

    # Use decorators for automatic tracing
    from casare_rpa.infrastructure.observability import trace_workflow, trace_node

    @trace_workflow(workflow_name="InvoiceProcessor")
    async def process_invoices(ctx):
        ...

    # Record metrics
    from casare_rpa.infrastructure.observability import get_metrics_collector

    collector = get_metrics_collector()
    collector.record_job_start("job-123", "robot-01")
"""

from casare_rpa.infrastructure.observability.telemetry import (
    TelemetryProvider,
    TelemetryConfig,
    ExporterProtocol,
    DBOSSpanContext,
    get_tracer,
    get_meter,
    get_logger_provider,
    trace_workflow,
    trace_node,
    trace_async,
    record_job_duration,
    record_queue_depth,
    record_robot_utilization,
    inject_context_to_headers,
    extract_context_from_headers,
    setup_loguru_otel_sink,
    OTEL_AVAILABLE,
)

from casare_rpa.infrastructure.observability.metrics import (
    RPAMetricsCollector,
    JobMetrics,
    RobotMetrics,
    JobStatus,
    RobotStatus,
    get_metrics_collector,
)

from casare_rpa.infrastructure.observability.logging import (
    OTelLoguruSink,
    SpanLogger,
    configure_logging,
    get_span_logger,
    log_with_trace,
    trace_context_patcher,
    create_trace_context_format,
)

__all__ = [
    # Telemetry core
    "TelemetryProvider",
    "TelemetryConfig",
    "ExporterProtocol",
    "DBOSSpanContext",
    "OTEL_AVAILABLE",
    # Tracer/Meter access
    "get_tracer",
    "get_meter",
    "get_logger_provider",
    # Instrumentation decorators
    "trace_workflow",
    "trace_node",
    "trace_async",
    # Metric recording
    "record_job_duration",
    "record_queue_depth",
    "record_robot_utilization",
    # Context propagation
    "inject_context_to_headers",
    "extract_context_from_headers",
    # Metrics collector
    "RPAMetricsCollector",
    "JobMetrics",
    "RobotMetrics",
    "JobStatus",
    "RobotStatus",
    "get_metrics_collector",
    # Logging
    "OTelLoguruSink",
    "SpanLogger",
    "configure_logging",
    "get_span_logger",
    "log_with_trace",
    "trace_context_patcher",
    "create_trace_context_format",
    "setup_loguru_otel_sink",
]
