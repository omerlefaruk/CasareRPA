"""
CasareRPA - Infrastructure: Observability Module

OpenTelemetry integration for distributed tracing, metrics, and log aggregation.
Provides production-grade monitoring for the CasareRPA platform.

Key Components:
- Observability: Unified facade for all observability functionality (RECOMMENDED)
- TelemetryProvider: Singleton for initializing and managing OpenTelemetry SDK
- RPAMetricsCollector: Job duration, queue depth, robot utilization metrics
- MetricsExporter: Multi-backend metrics export (JSON, Prometheus, OTLP)
- MetricsSnapshot: Point-in-time metrics for streaming/REST
- SystemMetricsCollector: CPU, memory, disk, network monitoring
- Log correlation: Automatic trace context injection into logs

Recommended Usage (via unified facade):
    from casare_rpa.infrastructure.observability import (
        Observability,
        configure_observability,
    )

    # Quick setup (auto-detects environment)
    configure_observability(robot_id="robot-01")

    # Or with full config
    Observability.configure()

    # Use throughout application
    Observability.log("info", "Starting workflow", workflow_id="abc123")
    Observability.metric("job_duration", 45.2, {"robot_id": "r1"})

    with Observability.trace("execute_workflow", {"workflow_name": "invoice"}):
        # Traced code block
        pass

    # Shutdown at exit
    Observability.shutdown()

Legacy Usage (direct components):
    from casare_rpa.infrastructure.observability import (
        TelemetryProvider,
        TelemetryConfig,
        configure_logging,
        get_metrics_collector,
    )

    config = TelemetryConfig(
        service_name="casare-robot",
        otlp_endpoint="http://localhost:4317",
    )
    TelemetryProvider.get_instance().initialize(config)
    configure_logging(enable_otel_export=True)

    collector = get_metrics_collector()
    collector.record_job_start("job-123", "robot-01")
"""

# =============================================================================
# Unified Facade (RECOMMENDED)
# =============================================================================

from casare_rpa.infrastructure.observability.facade import (
    Observability,
    ObservabilityConfig,
    Environment,
    configure_observability,
)

# =============================================================================
# Telemetry (OpenTelemetry)
# =============================================================================

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

# =============================================================================
# Metrics Collection
# =============================================================================

from casare_rpa.infrastructure.observability.metrics import (
    # Core collector
    RPAMetricsCollector,
    get_metrics_collector,
    # Data classes
    JobMetrics,
    RobotMetrics,
    JobStatus,
    RobotStatus,
    # Multi-backend export
    MetricsExporter,
    MetricsSnapshot,
    get_metrics_exporter,
)

# =============================================================================
# System Metrics
# =============================================================================

from casare_rpa.infrastructure.observability.system_metrics import (
    SystemMetricsCollector,
    ProcessMetrics,
    SystemMetrics,
    get_system_metrics_collector,
    get_cpu_percent,
    get_memory_mb,
)

# =============================================================================
# Logging
# =============================================================================

from casare_rpa.infrastructure.observability.logging import (
    OTelLoguruSink,
    UILoguruSink,
    SpanLogger,
    configure_logging,
    get_span_logger,
    log_with_trace,
    trace_context_patcher,
    create_trace_context_format,
    set_ui_log_callback,
    remove_ui_log_callback,
)

# =============================================================================
# Stdout Capture
# =============================================================================

from casare_rpa.infrastructure.observability.stdout_capture import (
    OutputCapture,
    set_output_callbacks,
    remove_output_callbacks,
    capture_output,
)


__all__ = [
    # =========================================================================
    # Unified Facade (RECOMMENDED)
    # =========================================================================
    "Observability",
    "ObservabilityConfig",
    "Environment",
    "configure_observability",
    # =========================================================================
    # Telemetry core
    # =========================================================================
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
    "setup_loguru_otel_sink",
    # =========================================================================
    # Metrics collector
    # =========================================================================
    "RPAMetricsCollector",
    "JobMetrics",
    "RobotMetrics",
    "JobStatus",
    "RobotStatus",
    "get_metrics_collector",
    # Multi-backend export
    "MetricsExporter",
    "MetricsSnapshot",
    "get_metrics_exporter",
    # =========================================================================
    # System Metrics
    # =========================================================================
    "SystemMetricsCollector",
    "ProcessMetrics",
    "SystemMetrics",
    "get_system_metrics_collector",
    "get_cpu_percent",
    "get_memory_mb",
    # =========================================================================
    # Logging
    # =========================================================================
    "OTelLoguruSink",
    "UILoguruSink",
    "SpanLogger",
    "configure_logging",
    "get_span_logger",
    "log_with_trace",
    "trace_context_patcher",
    "create_trace_context_format",
    "set_ui_log_callback",
    "remove_ui_log_callback",
    # =========================================================================
    # Stdout Capture
    # =========================================================================
    "OutputCapture",
    "set_output_callbacks",
    "remove_output_callbacks",
    "capture_output",
]
