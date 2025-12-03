"""
CasareRPA - Infrastructure: OpenTelemetry Integration

Provides distributed tracing, metrics collection, and log aggregation for the
CasareRPA platform. Integrates with OTLP-compatible backends (Jaeger, Grafana).

Key Features:
- Distributed tracing with workflow execution spans
- Metrics collection (job duration, queue depth, robot utilization)
- Log aggregation with trace correlation
- Instrumentation decorators for automatic tracing
- DBOS workflow execution integration
"""

from __future__ import annotations

import atexit
import functools
import os
import socket
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Generator,
    List,
    Optional,
    TypeVar,
    ParamSpec,
    cast,
)

from loguru import logger

# OpenTelemetry imports - API
try:
    from opentelemetry import trace, metrics
    from opentelemetry.trace import (
        Span,
        SpanKind,
        Status,
        StatusCode,
        get_current_span,
        set_span_in_context,
    )
    from opentelemetry.trace.propagation.tracecontext import (
        TraceContextTextMapPropagator,
    )
    from opentelemetry.context import Context

    # OpenTelemetry imports - SDK
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
        SpanExporter,
    )
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import (
        PeriodicExportingMetricReader,
        ConsoleMetricExporter,
        MetricReader,
    )
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk._logs import LoggerProvider
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor

    # OTLP exporters
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
        OTLPSpanExporter as OTLPSpanExporterGRPC,
    )
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
        OTLPMetricExporter as OTLPMetricExporterGRPC,
    )
    from opentelemetry.exporter.otlp.proto.grpc._log_exporter import (
        OTLPLogExporter as OTLPLogExporterGRPC,
    )
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
        OTLPSpanExporter as OTLPSpanExporterHTTP,
    )
    from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
        OTLPMetricExporter as OTLPMetricExporterHTTP,
    )
    from opentelemetry.exporter.otlp.proto.http._log_exporter import (
        OTLPLogExporter as OTLPLogExporterHTTP,
    )

    OTEL_AVAILABLE = True
except ImportError as e:
    logger.debug(
        f"OpenTelemetry packages not installed: {e}. "
        "Telemetry disabled. Install with: pip install opentelemetry-api opentelemetry-sdk "
        "opentelemetry-exporter-otlp-proto-grpc opentelemetry-exporter-otlp-proto-http"
    )
    OTEL_AVAILABLE = False

    # When OTel is not installed, create stub implementations for runtime
    # These are needed to avoid NameError at runtime when the library is not installed
    class Span:  # type: ignore[no-redef]
        """Stub Span when OpenTelemetry is not installed."""

        pass

    class SpanKind:  # type: ignore[no-redef]
        """Stub SpanKind when OpenTelemetry is not installed."""

        INTERNAL = None

    class StatusCode:  # type: ignore[no-redef]
        """Stub StatusCode when OpenTelemetry is not installed."""

        OK = None
        ERROR = None

    class Status:  # type: ignore[no-redef]
        """Stub Status when OpenTelemetry is not installed."""

        def __init__(self, code: Any, description: str = "") -> None:
            pass

    # Stub functions for when OTel is not installed
    def get_current_span(context: Any = None) -> Any:  # type: ignore[misc]
        """Stub get_current_span when OpenTelemetry is not installed."""
        return None

    def set_span_in_context(span: Any, context: Any = None) -> Any:  # type: ignore[misc]
        """Stub set_span_in_context when OpenTelemetry is not installed."""
        return None


# Type variables for decorators
P = ParamSpec("P")
T = TypeVar("T")


class ExporterProtocol(str, Enum):
    """OTLP exporter protocol options."""

    GRPC = "grpc"
    HTTP = "http/protobuf"
    CONSOLE = "console"
    NONE = "none"


@dataclass
class TelemetryConfig:
    """
    Configuration for OpenTelemetry integration.

    Supports environment variable overrides following OTel conventions:
    - OTEL_SERVICE_NAME: Service name for resource
    - OTEL_EXPORTER_OTLP_ENDPOINT: OTLP endpoint URL
    - OTEL_EXPORTER_OTLP_PROTOCOL: Protocol (grpc or http/protobuf)
    - OTEL_TRACES_EXPORTER: Trace exporter type
    - OTEL_METRICS_EXPORTER: Metrics exporter type
    - OTEL_LOGS_EXPORTER: Logs exporter type
    """

    # Service identification
    service_name: str = field(
        default_factory=lambda: os.getenv("OTEL_SERVICE_NAME", "casare-rpa")
    )
    service_version: str = field(
        default_factory=lambda: os.getenv("OTEL_SERVICE_VERSION", "1.0.0")
    )
    service_instance_id: str = field(
        default_factory=lambda: os.getenv(
            "OTEL_SERVICE_INSTANCE_ID", socket.gethostname()
        )
    )
    deployment_environment: str = field(
        default_factory=lambda: os.getenv("OTEL_DEPLOYMENT_ENVIRONMENT", "development")
    )

    # OTLP endpoint configuration
    otlp_endpoint: str = field(
        default_factory=lambda: os.getenv(
            "OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"
        )
    )
    otlp_protocol: ExporterProtocol = field(
        default_factory=lambda: ExporterProtocol(
            os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc")
        )
    )
    otlp_headers: Dict[str, str] = field(default_factory=dict)
    otlp_insecure: bool = field(
        default_factory=lambda: os.getenv("OTEL_EXPORTER_OTLP_INSECURE", "true").lower()
        == "true"
    )

    # Feature flags
    traces_enabled: bool = field(
        default_factory=lambda: os.getenv("OTEL_TRACES_EXPORTER", "otlp") != "none"
    )
    metrics_enabled: bool = field(
        default_factory=lambda: os.getenv("OTEL_METRICS_EXPORTER", "otlp") != "none"
    )
    logs_enabled: bool = field(
        default_factory=lambda: os.getenv("OTEL_LOGS_EXPORTER", "otlp") != "none"
    )

    # Sampling and export settings
    trace_sample_rate: float = field(
        default_factory=lambda: float(os.getenv("OTEL_TRACES_SAMPLER_ARG", "1.0"))
    )
    metrics_export_interval_ms: int = field(
        default_factory=lambda: int(os.getenv("OTEL_METRIC_EXPORT_INTERVAL", "60000"))
    )
    batch_export_timeout_ms: int = field(
        default_factory=lambda: int(os.getenv("OTEL_BSP_EXPORT_TIMEOUT", "30000"))
    )

    # Console fallback (useful for development)
    console_exporter_enabled: bool = field(
        default_factory=lambda: os.getenv("OTEL_CONSOLE_EXPORTER", "false").lower()
        == "true"
    )

    def to_resource_attributes(self) -> Dict[str, str]:
        """Convert config to OpenTelemetry resource attributes."""
        return {
            "service.name": self.service_name,
            "service.version": self.service_version,
            "service.instance.id": self.service_instance_id,
            "deployment.environment": self.deployment_environment,
            "host.name": socket.gethostname(),
            "telemetry.sdk.name": "opentelemetry",
            "telemetry.sdk.language": "python",
        }


class TelemetryProvider:
    """
    Singleton provider for OpenTelemetry instrumentation.

    Manages the lifecycle of tracers, meters, and log providers.
    Supports OTLP export to Jaeger, Grafana Tempo, or any OTLP-compatible backend.

    Usage:
        # Initialize at application startup
        provider = TelemetryProvider.get_instance()
        provider.initialize(TelemetryConfig(service_name="my-robot"))

        # Get tracer/meter for instrumentation
        tracer = provider.get_tracer("my.component")
        meter = provider.get_meter("my.component")

        # Shutdown at application exit
        provider.shutdown()
    """

    _instance: Optional["TelemetryProvider"] = None
    _lock: threading.Lock = threading.Lock()
    _initialized: bool

    def __new__(cls) -> "TelemetryProvider":
        """Thread-safe singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    @classmethod
    def get_instance(cls) -> "TelemetryProvider":
        """Get the singleton instance."""
        return cls()

    def __init__(self) -> None:
        """Initialize instance variables (only on first instantiation)."""
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._config: Optional[TelemetryConfig] = None
        self._resource: Optional[Any] = None
        self._tracer_provider: Optional[Any] = None
        self._meter_provider: Optional[Any] = None
        self._logger_provider: Optional[Any] = None
        self._tracers: Dict[str, Any] = {}
        self._meters: Dict[str, Any] = {}
        self._shutdown_registered: bool = False

        # Metrics instruments (cached)
        self._job_duration_histogram: Optional[Any] = None
        self._queue_depth_gauge: Optional[Any] = None
        self._robot_utilization_gauge: Optional[Any] = None
        self._node_execution_counter: Optional[Any] = None
        self._workflow_counter: Optional[Any] = None
        self._error_counter: Optional[Any] = None

        # Observable gauge callbacks data
        self._queue_depth_value: float = 0.0
        self._robot_utilization_value: float = 0.0
        self._active_robots_count: int = 0

        self._initialized = False

    def initialize(
        self,
        config: Optional[TelemetryConfig] = None,
        force_reinit: bool = False,
    ) -> None:
        """
        Initialize OpenTelemetry providers and exporters.

        Args:
            config: Telemetry configuration. Uses defaults if not provided.
            force_reinit: Force reinitialization even if already initialized.

        Raises:
            RuntimeError: If OpenTelemetry packages are not installed.
        """
        if self._initialized and not force_reinit:
            logger.debug("TelemetryProvider already initialized")
            return

        if not OTEL_AVAILABLE:
            logger.warning(
                "OpenTelemetry not available. Telemetry disabled. "
                "Install with: pip install opentelemetry-api opentelemetry-sdk "
                "opentelemetry-exporter-otlp-proto-grpc"
            )
            self._initialized = True
            return

        self._config = config or TelemetryConfig()
        logger.info(
            f"Initializing OpenTelemetry for service '{self._config.service_name}' "
            f"with endpoint '{self._config.otlp_endpoint}'"
        )

        try:
            # Create resource with service attributes
            self._resource = Resource.create(self._config.to_resource_attributes())

            # Initialize providers
            self._init_tracer_provider()
            self._init_meter_provider()
            self._init_logger_provider()

            # Create standard metrics instruments
            self._init_metrics_instruments()

            # Register shutdown hook
            if not self._shutdown_registered:
                atexit.register(self.shutdown)
                self._shutdown_registered = True

            self._initialized = True
            logger.info("OpenTelemetry initialization complete")

        except Exception as e:
            logger.error(f"Failed to initialize OpenTelemetry: {e}")
            self._initialized = True  # Mark as initialized to prevent retry loops

    def _init_tracer_provider(self) -> None:
        """Initialize the tracer provider with configured exporters."""
        if not self._config or not self._config.traces_enabled:
            logger.debug("Traces disabled")
            return

        self._tracer_provider = TracerProvider(resource=self._resource)

        # Add OTLP exporter
        span_exporter = self._create_span_exporter()
        if span_exporter:
            processor = BatchSpanProcessor(
                span_exporter,
                export_timeout_millis=self._config.batch_export_timeout_ms,
            )
            self._tracer_provider.add_span_processor(processor)

        # Add console exporter if enabled
        if self._config.console_exporter_enabled:
            console_processor = BatchSpanProcessor(ConsoleSpanExporter())
            self._tracer_provider.add_span_processor(console_processor)

        # Set as global tracer provider
        trace.set_tracer_provider(self._tracer_provider)
        logger.debug("TracerProvider initialized")

    def _init_meter_provider(self) -> None:
        """Initialize the meter provider with configured exporters."""
        if not self._config or not self._config.metrics_enabled:
            logger.debug("Metrics disabled")
            return

        metric_readers: List[MetricReader] = []

        # Add OTLP metric reader
        metric_exporter = self._create_metric_exporter()
        if metric_exporter:
            reader = PeriodicExportingMetricReader(
                metric_exporter,
                export_interval_millis=self._config.metrics_export_interval_ms,
            )
            metric_readers.append(reader)

        # Add console reader if enabled
        if self._config.console_exporter_enabled:
            console_reader = PeriodicExportingMetricReader(
                ConsoleMetricExporter(),
                export_interval_millis=self._config.metrics_export_interval_ms,
            )
            metric_readers.append(console_reader)

        if metric_readers:
            self._meter_provider = MeterProvider(
                resource=self._resource,
                metric_readers=metric_readers,
            )
            metrics.set_meter_provider(self._meter_provider)
            logger.debug("MeterProvider initialized")

    def _init_logger_provider(self) -> None:
        """Initialize the logger provider for log correlation."""
        if not self._config or not self._config.logs_enabled:
            logger.debug("Logs correlation disabled")
            return

        self._logger_provider = LoggerProvider(resource=self._resource)

        # Add OTLP log exporter
        log_exporter = self._create_log_exporter()
        if log_exporter:
            processor = BatchLogRecordProcessor(log_exporter)
            self._logger_provider.add_log_record_processor(processor)

        logger.debug("LoggerProvider initialized")

    def _create_span_exporter(self) -> Optional[SpanExporter]:
        """Create appropriate span exporter based on config."""
        if not self._config:
            return None

        if self._config.otlp_protocol == ExporterProtocol.NONE:
            return None

        try:
            if self._config.otlp_protocol == ExporterProtocol.GRPC:
                return OTLPSpanExporterGRPC(
                    endpoint=self._config.otlp_endpoint,
                    insecure=self._config.otlp_insecure,
                    headers=self._config.otlp_headers or None,
                )
            elif self._config.otlp_protocol == ExporterProtocol.HTTP:
                endpoint = self._config.otlp_endpoint
                if not endpoint.endswith("/v1/traces"):
                    endpoint = f"{endpoint.rstrip('/')}/v1/traces"
                return OTLPSpanExporterHTTP(
                    endpoint=endpoint,
                    headers=self._config.otlp_headers or None,
                )
            elif self._config.otlp_protocol == ExporterProtocol.CONSOLE:
                return ConsoleSpanExporter()
        except Exception as e:
            logger.warning(f"Failed to create span exporter: {e}")

        return None

    def _create_metric_exporter(self) -> Optional[Any]:
        """Create appropriate metric exporter based on config."""
        if not self._config:
            return None

        if self._config.otlp_protocol == ExporterProtocol.NONE:
            return None

        try:
            if self._config.otlp_protocol == ExporterProtocol.GRPC:
                return OTLPMetricExporterGRPC(
                    endpoint=self._config.otlp_endpoint,
                    insecure=self._config.otlp_insecure,
                    headers=self._config.otlp_headers or None,
                )
            elif self._config.otlp_protocol == ExporterProtocol.HTTP:
                endpoint = self._config.otlp_endpoint
                if not endpoint.endswith("/v1/metrics"):
                    endpoint = f"{endpoint.rstrip('/')}/v1/metrics"
                return OTLPMetricExporterHTTP(
                    endpoint=endpoint,
                    headers=self._config.otlp_headers or None,
                )
            elif self._config.otlp_protocol == ExporterProtocol.CONSOLE:
                return ConsoleMetricExporter()
        except Exception as e:
            logger.warning(f"Failed to create metric exporter: {e}")

        return None

    def _create_log_exporter(self) -> Optional[Any]:
        """Create appropriate log exporter based on config."""
        if not self._config:
            return None

        if self._config.otlp_protocol == ExporterProtocol.NONE:
            return None

        try:
            if self._config.otlp_protocol == ExporterProtocol.GRPC:
                return OTLPLogExporterGRPC(
                    endpoint=self._config.otlp_endpoint,
                    insecure=self._config.otlp_insecure,
                    headers=self._config.otlp_headers or None,
                )
            elif self._config.otlp_protocol == ExporterProtocol.HTTP:
                endpoint = self._config.otlp_endpoint
                if not endpoint.endswith("/v1/logs"):
                    endpoint = f"{endpoint.rstrip('/')}/v1/logs"
                return OTLPLogExporterHTTP(
                    endpoint=endpoint,
                    headers=self._config.otlp_headers or None,
                )
        except Exception as e:
            logger.warning(f"Failed to create log exporter: {e}")

        return None

    def _init_metrics_instruments(self) -> None:
        """Initialize standard metrics instruments for RPA monitoring."""
        meter = self.get_meter("casare_rpa.core")
        if not meter:
            return

        # Job duration histogram (in seconds)
        self._job_duration_histogram = meter.create_histogram(
            name="casare_rpa.job.duration",
            description="Duration of job execution in seconds",
            unit="s",
        )

        # Workflow execution counter
        self._workflow_counter = meter.create_counter(
            name="casare_rpa.workflow.count",
            description="Number of workflow executions",
            unit="1",
        )

        # Node execution counter
        self._node_execution_counter = meter.create_counter(
            name="casare_rpa.node.execution.count",
            description="Number of node executions by type",
            unit="1",
        )

        # Error counter
        self._error_counter = meter.create_counter(
            name="casare_rpa.error.count",
            description="Number of errors by type",
            unit="1",
        )

        # Queue depth gauge (observable)
        def queue_depth_callback(options: Any) -> Generator[Any, None, None]:
            from opentelemetry.metrics import Observation

            yield Observation(value=self._queue_depth_value)

        self._queue_depth_gauge = meter.create_observable_gauge(
            name="casare_rpa.queue.depth",
            description="Current depth of the job queue",
            unit="1",
            callbacks=[queue_depth_callback],
        )

        # Robot utilization gauge (observable)
        def robot_utilization_callback(options: Any) -> Generator[Any, None, None]:
            from opentelemetry.metrics import Observation

            yield Observation(
                value=self._robot_utilization_value,
                attributes={"active_robots": self._active_robots_count},
            )

        self._robot_utilization_gauge = meter.create_observable_gauge(
            name="casare_rpa.robot.utilization",
            description="Robot utilization percentage (0-100)",
            unit="%",
            callbacks=[robot_utilization_callback],
        )

        logger.debug("Metrics instruments initialized")

    def get_tracer(self, name: str, version: str = "1.0.0") -> Optional[Any]:
        """
        Get or create a tracer for the given component.

        Args:
            name: Component name (e.g., "casare_rpa.runner")
            version: Component version

        Returns:
            Tracer instance or None if tracing is disabled
        """
        if not OTEL_AVAILABLE or not self._tracer_provider:
            return None

        cache_key = f"{name}:{version}"
        if cache_key not in self._tracers:
            self._tracers[cache_key] = trace.get_tracer(name, version)

        return self._tracers[cache_key]

    def get_meter(self, name: str, version: str = "1.0.0") -> Optional[Any]:
        """
        Get or create a meter for the given component.

        Args:
            name: Component name (e.g., "casare_rpa.runner")
            version: Component version

        Returns:
            Meter instance or None if metrics are disabled
        """
        if not OTEL_AVAILABLE or not self._meter_provider:
            return None

        cache_key = f"{name}:{version}"
        if cache_key not in self._meters:
            self._meters[cache_key] = metrics.get_meter(name, version)

        return self._meters[cache_key]

    def get_logger_provider(self) -> Optional[Any]:
        """Get the logger provider for log correlation."""
        return self._logger_provider

    def record_job_duration(
        self,
        duration_seconds: float,
        workflow_name: str,
        job_id: str,
        success: bool,
        robot_id: Optional[str] = None,
    ) -> None:
        """
        Record job execution duration.

        Args:
            duration_seconds: Job duration in seconds
            workflow_name: Name of the workflow
            job_id: Unique job identifier
            success: Whether the job completed successfully
            robot_id: ID of the robot that executed the job
        """
        if not self._job_duration_histogram:
            return

        attributes = {
            "workflow.name": workflow_name,
            "job.id": job_id,
            "job.success": str(success).lower(),
        }
        if robot_id:
            attributes["robot.id"] = robot_id

        self._job_duration_histogram.record(duration_seconds, attributes)

    def record_workflow_execution(
        self,
        workflow_name: str,
        success: bool,
        node_count: int,
        trigger_type: str = "manual",
    ) -> None:
        """
        Record a workflow execution event.

        Args:
            workflow_name: Name of the workflow
            success: Whether execution succeeded
            node_count: Number of nodes executed
            trigger_type: How the workflow was triggered
        """
        if not self._workflow_counter:
            return

        attributes = {
            "workflow.name": workflow_name,
            "workflow.success": str(success).lower(),
            "workflow.trigger": trigger_type,
            "workflow.node_count": node_count,
        }
        self._workflow_counter.add(1, attributes)

    def record_node_execution(
        self,
        node_type: str,
        node_id: str,
        success: bool,
        duration_ms: float,
    ) -> None:
        """
        Record a node execution event.

        Args:
            node_type: Type of node (e.g., "ClickNode", "TypeNode")
            node_id: Unique node identifier
            success: Whether execution succeeded
            duration_ms: Execution duration in milliseconds
        """
        if not self._node_execution_counter:
            return

        attributes = {
            "node.type": node_type,
            "node.id": node_id,
            "node.success": str(success).lower(),
        }
        self._node_execution_counter.add(1, attributes)

    def record_error(
        self,
        error_type: str,
        component: str,
        message: str,
        recoverable: bool = False,
    ) -> None:
        """
        Record an error event.

        Args:
            error_type: Type of error (e.g., "ElementNotFound", "Timeout")
            component: Component where error occurred
            message: Error message
            recoverable: Whether the error was recoverable
        """
        if not self._error_counter:
            return

        attributes = {
            "error.type": error_type,
            "error.component": component,
            "error.recoverable": str(recoverable).lower(),
        }
        self._error_counter.add(1, attributes)

    def update_queue_depth(self, depth: int) -> None:
        """
        Update the current queue depth for the observable gauge.

        Args:
            depth: Current number of jobs in queue
        """
        self._queue_depth_value = float(depth)

    def update_robot_utilization(
        self,
        utilization_percent: float,
        active_robots: int,
    ) -> None:
        """
        Update robot utilization metrics.

        Args:
            utilization_percent: Current utilization (0-100)
            active_robots: Number of active robots
        """
        self._robot_utilization_value = utilization_percent
        self._active_robots_count = active_robots

    @contextmanager
    def span(
        self,
        name: str,
        kind: Optional[Any] = None,
        attributes: Optional[Dict[str, Any]] = None,
        component: str = "casare_rpa",
    ) -> Generator[Optional[Span], None, None]:
        """
        Context manager for creating spans.

        Args:
            name: Span name
            kind: Span kind (CLIENT, SERVER, INTERNAL, etc.)
            attributes: Span attributes
            component: Component name for tracer

        Yields:
            Span instance or None if tracing is disabled
        """
        tracer = self.get_tracer(component)
        if not tracer:
            yield None
            return

        span_kind = kind or SpanKind.INTERNAL
        with tracer.start_as_current_span(
            name,
            kind=span_kind,
            attributes=attributes or {},
        ) as span:
            try:
                yield span
            except Exception as e:
                if span:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                raise

    def shutdown(self) -> None:
        """Shutdown all providers and flush pending data."""
        logger.info("Shutting down OpenTelemetry providers")

        if self._tracer_provider:
            try:
                self._tracer_provider.shutdown()
                logger.debug("TracerProvider shutdown complete")
            except Exception as e:
                logger.warning(f"Error shutting down TracerProvider: {e}")

        if self._meter_provider:
            try:
                self._meter_provider.shutdown()
                logger.debug("MeterProvider shutdown complete")
            except Exception as e:
                logger.warning(f"Error shutting down MeterProvider: {e}")

        if self._logger_provider:
            try:
                self._logger_provider.shutdown()
                logger.debug("LoggerProvider shutdown complete")
            except Exception as e:
                logger.warning(f"Error shutting down LoggerProvider: {e}")

        self._initialized = False
        logger.info("OpenTelemetry shutdown complete")


# =============================================================================
# Module-Level Convenience Functions
# =============================================================================


def get_tracer(name: str = "casare_rpa", version: str = "1.0.0") -> Optional[Any]:
    """Get a tracer from the global TelemetryProvider."""
    return TelemetryProvider.get_instance().get_tracer(name, version)


def get_meter(name: str = "casare_rpa", version: str = "1.0.0") -> Optional[Any]:
    """Get a meter from the global TelemetryProvider."""
    return TelemetryProvider.get_instance().get_meter(name, version)


def get_logger_provider() -> Optional[Any]:
    """Get the logger provider from the global TelemetryProvider."""
    return TelemetryProvider.get_instance().get_logger_provider()


def record_job_duration(
    duration_seconds: float,
    workflow_name: str,
    job_id: str,
    success: bool,
    robot_id: Optional[str] = None,
) -> None:
    """Record job duration metric."""
    TelemetryProvider.get_instance().record_job_duration(
        duration_seconds, workflow_name, job_id, success, robot_id
    )


def record_queue_depth(depth: int) -> None:
    """Update queue depth metric."""
    TelemetryProvider.get_instance().update_queue_depth(depth)


def record_robot_utilization(utilization_percent: float, active_robots: int) -> None:
    """Update robot utilization metric."""
    TelemetryProvider.get_instance().update_robot_utilization(
        utilization_percent, active_robots
    )


# =============================================================================
# Instrumentation Decorators
# =============================================================================


def trace_workflow(
    workflow_name: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator for tracing workflow execution.

    Creates a span for the entire workflow with standard RPA attributes.

    Args:
        workflow_name: Override workflow name (default: function name)
        attributes: Additional span attributes

    Usage:
        @trace_workflow(workflow_name="ProcessInvoices")
        async def run_workflow(ctx: ExecutionContext) -> Dict[str, Any]:
            ...
    """
    import asyncio

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            provider = TelemetryProvider.get_instance()
            tracer = provider.get_tracer("casare_rpa.workflow")
            name = workflow_name or func.__name__

            if not tracer:
                return func(*args, **kwargs)

            span_attributes: Dict[str, Any] = {
                "workflow.name": name,
                "workflow.function": func.__qualname__,
            }
            if attributes:
                span_attributes.update(attributes)

            with tracer.start_as_current_span(
                f"workflow:{name}",
                kind=SpanKind.INTERNAL,
                attributes=span_attributes,
            ) as span:
                start_time = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    provider.record_workflow_execution(
                        workflow_name=name,
                        success=True,
                        node_count=_extract_node_count(result),
                        trigger_type="sync",
                    )
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    provider.record_workflow_execution(
                        workflow_name=name,
                        success=False,
                        node_count=0,
                        trigger_type="sync",
                    )
                    provider.record_error(
                        error_type=type(e).__name__,
                        component="workflow",
                        message=str(e),
                        recoverable=False,
                    )
                    raise
                finally:
                    duration = time.perf_counter() - start_time
                    span.set_attribute("workflow.duration_ms", duration * 1000)

        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            provider = TelemetryProvider.get_instance()
            tracer = provider.get_tracer("casare_rpa.workflow")
            name = workflow_name or func.__name__

            if not tracer:
                # Cast is needed because func could be sync or async at runtime
                coro = cast(Callable[P, Awaitable[T]], func)
                return await coro(*args, **kwargs)

            span_attributes: Dict[str, Any] = {
                "workflow.name": name,
                "workflow.function": func.__qualname__,
            }
            if attributes:
                span_attributes.update(attributes)

            with tracer.start_as_current_span(
                f"workflow:{name}",
                kind=SpanKind.INTERNAL,
                attributes=span_attributes,
            ) as span:
                start_time = time.perf_counter()
                try:
                    coro = cast(Callable[P, Awaitable[T]], func)
                    result = await coro(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    provider.record_workflow_execution(
                        workflow_name=name,
                        success=True,
                        node_count=_extract_node_count(result),
                        trigger_type="async",
                    )
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    provider.record_workflow_execution(
                        workflow_name=name,
                        success=False,
                        node_count=0,
                        trigger_type="async",
                    )
                    provider.record_error(
                        error_type=type(e).__name__,
                        component="workflow",
                        message=str(e),
                        recoverable=False,
                    )
                    raise
                finally:
                    duration = time.perf_counter() - start_time
                    span.set_attribute("workflow.duration_ms", duration * 1000)

        if asyncio.iscoroutinefunction(func):
            return cast(Callable[P, T], async_wrapper)
        return cast(Callable[P, T], sync_wrapper)

    return decorator


def trace_node(
    node_type: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator for tracing node execution.

    Creates a span for individual node execution within a workflow.

    Args:
        node_type: Node type name (default: class name)
        attributes: Additional span attributes

    Usage:
        @trace_node(node_type="ClickNode")
        async def execute(self, ctx: ExecutionContext) -> NodeResult:
            ...
    """
    import asyncio

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            provider = TelemetryProvider.get_instance()
            tracer = provider.get_tracer("casare_rpa.node")
            ntype = node_type or _extract_class_name(args)

            if not tracer:
                return func(*args, **kwargs)

            node_id = _extract_node_id(args, kwargs)
            span_attributes: Dict[str, Any] = {
                "node.type": ntype,
                "node.id": node_id or "unknown",
                "node.function": func.__qualname__,
            }
            if attributes:
                span_attributes.update(attributes)

            with tracer.start_as_current_span(
                f"node:{ntype}",
                kind=SpanKind.INTERNAL,
                attributes=span_attributes,
            ) as span:
                start_time = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    provider.record_node_execution(
                        node_type=ntype,
                        node_id=node_id or "unknown",
                        success=True,
                        duration_ms=duration_ms,
                    )
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    provider.record_node_execution(
                        node_type=ntype,
                        node_id=node_id or "unknown",
                        success=False,
                        duration_ms=duration_ms,
                    )
                    raise
                finally:
                    duration = time.perf_counter() - start_time
                    span.set_attribute("node.duration_ms", duration * 1000)

        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            provider = TelemetryProvider.get_instance()
            tracer = provider.get_tracer("casare_rpa.node")
            ntype = node_type or _extract_class_name(args)

            if not tracer:
                coro = cast(Callable[P, Awaitable[T]], func)
                return await coro(*args, **kwargs)

            node_id = _extract_node_id(args, kwargs)
            span_attributes: Dict[str, Any] = {
                "node.type": ntype,
                "node.id": node_id or "unknown",
                "node.function": func.__qualname__,
            }
            if attributes:
                span_attributes.update(attributes)

            with tracer.start_as_current_span(
                f"node:{ntype}",
                kind=SpanKind.INTERNAL,
                attributes=span_attributes,
            ) as span:
                start_time = time.perf_counter()
                try:
                    coro = cast(Callable[P, Awaitable[T]], func)
                    result = await coro(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    provider.record_node_execution(
                        node_type=ntype,
                        node_id=node_id or "unknown",
                        success=True,
                        duration_ms=duration_ms,
                    )
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    provider.record_node_execution(
                        node_type=ntype,
                        node_id=node_id or "unknown",
                        success=False,
                        duration_ms=duration_ms,
                    )
                    raise
                finally:
                    duration = time.perf_counter() - start_time
                    span.set_attribute("node.duration_ms", duration * 1000)

        if asyncio.iscoroutinefunction(func):
            return cast(Callable[P, T], async_wrapper)
        return cast(Callable[P, T], sync_wrapper)

    return decorator


def trace_async(
    name: Optional[str] = None,
    kind: Optional[Any] = None,
    attributes: Optional[Dict[str, Any]] = None,
    component: str = "casare_rpa",
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    General-purpose tracing decorator for async functions.

    Args:
        name: Span name (default: function name)
        kind: Span kind
        attributes: Additional span attributes
        component: Component name for tracer

    Usage:
        @trace_async(name="fetch_data", component="casare_rpa.browser")
        async def fetch_page_data(url: str) -> Dict[str, Any]:
            ...
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            tracer = get_tracer(component)
            span_name = name or func.__name__

            coro = cast(Callable[P, Awaitable[T]], func)
            if not tracer:
                return await coro(*args, **kwargs)

            # Default to INTERNAL span kind when OTel is available
            span_kind = kind if kind is not None else SpanKind.INTERNAL
            span_attributes: Dict[str, Any] = {"function": func.__qualname__}
            if attributes:
                span_attributes.update(attributes)

            with tracer.start_as_current_span(
                span_name,
                kind=span_kind,
                attributes=span_attributes,
            ) as span:
                try:
                    result = await coro(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        return cast(Callable[P, T], wrapper)

    return decorator


# =============================================================================
# DBOS Integration
# =============================================================================


class DBOSSpanContext:
    """
    Context manager for integrating OpenTelemetry with DBOS workflow execution.

    Creates proper span hierarchy for DBOS workflows:
    - Root span: workflow execution
    - Child spans: individual steps (initialize, execute_node, cleanup)

    Usage:
        async with DBOSSpanContext(workflow_id, workflow_name) as ctx:
            # DBOS workflow execution
            result = await run_durable_workflow(...)
            ctx.set_result(result)
    """

    _token: Any  # Context token for detaching

    def __init__(
        self,
        workflow_id: str,
        workflow_name: str,
        job_id: Optional[str] = None,
        robot_id: Optional[str] = None,
    ) -> None:
        """
        Initialize DBOS span context.

        Args:
            workflow_id: DBOS workflow ID (used for trace correlation)
            workflow_name: Human-readable workflow name
            job_id: Job queue job ID (if applicable)
            robot_id: Executing robot ID (if applicable)
        """
        self.workflow_id = workflow_id
        self.workflow_name = workflow_name
        self.job_id = job_id
        self.robot_id = robot_id
        self._span: Optional[Any] = None
        self._tracer: Optional[Any] = None
        self._start_time: float = 0.0
        self._result: Optional[Dict[str, Any]] = None

    async def __aenter__(self) -> "DBOSSpanContext":
        """Enter context and start root span."""
        provider = TelemetryProvider.get_instance()
        self._tracer = provider.get_tracer("casare_rpa.dbos")
        self._start_time = time.perf_counter()

        if self._tracer and OTEL_AVAILABLE:
            attributes: Dict[str, Any] = {
                "dbos.workflow_id": self.workflow_id,
                "workflow.name": self.workflow_name,
            }
            if self.job_id:
                attributes["job.id"] = self.job_id
            if self.robot_id:
                attributes["robot.id"] = self.robot_id

            self._span = self._tracer.start_span(
                f"dbos:workflow:{self.workflow_name}",
                kind=SpanKind.INTERNAL,
                attributes=attributes,
            )
            # Make this span current
            from opentelemetry.context import attach

            self._token = attach(set_span_in_context(self._span))

        return self

    async def __aexit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> bool:
        """Exit context and finalize span."""
        provider = TelemetryProvider.get_instance()
        duration = time.perf_counter() - self._start_time

        if self._span:
            if exc_type and exc_val is not None:
                self._span.set_status(Status(StatusCode.ERROR, str(exc_val)))
                self._span.record_exception(exc_val)
                success = False
            else:
                self._span.set_status(Status(StatusCode.OK))
                success = True

            self._span.set_attribute("workflow.duration_ms", duration * 1000)
            if self._result:
                self._span.set_attribute(
                    "workflow.nodes_executed",
                    self._result.get("nodes_executed", 0),
                )

            self._span.end()

            # Detach context
            if OTEL_AVAILABLE and hasattr(self, "_token"):
                from opentelemetry.context import detach

                detach(self._token)

            # Record metrics
            provider.record_job_duration(
                duration_seconds=duration,
                workflow_name=self.workflow_name,
                job_id=self.job_id or self.workflow_id,
                success=success,
                robot_id=self.robot_id,
            )

        return False  # Don't suppress exceptions

    def set_result(self, result: Dict[str, Any]) -> None:
        """Store workflow result for span attributes."""
        self._result = result

    def create_step_span(self, step_name: str) -> Optional[Any]:
        """
        Create a child span for a DBOS step.

        Args:
            step_name: Name of the DBOS step

        Returns:
            Span instance or None if tracing disabled
        """
        if not self._tracer or not OTEL_AVAILABLE:
            return None

        return self._tracer.start_span(
            f"dbos:step:{step_name}",
            kind=SpanKind.INTERNAL,
            attributes={
                "dbos.step_name": step_name,
                "dbos.workflow_id": self.workflow_id,
            },
        )


# =============================================================================
# Loguru Integration for Log Correlation
# =============================================================================


def setup_loguru_otel_sink() -> None:
    """
    Configure Loguru to include trace context in log messages.

    This enables log correlation with traces in observability backends.
    Adds trace_id and span_id to all log records when a trace is active.
    """
    if not OTEL_AVAILABLE:
        logger.debug("OpenTelemetry not available, skipping loguru integration")
        return

    def otel_context_patcher(record: Any) -> None:
        """Add OpenTelemetry context to log records."""
        span = get_current_span()
        if span and span.is_recording():
            ctx = span.get_span_context()
            record["extra"]["trace_id"] = format(ctx.trace_id, "032x")
            record["extra"]["span_id"] = format(ctx.span_id, "016x")
        else:
            record["extra"]["trace_id"] = "00000000000000000000000000000000"
            record["extra"]["span_id"] = "0000000000000000"

    # Add patcher to include trace context
    logger.configure(patcher=otel_context_patcher)

    logger.debug("Loguru OpenTelemetry integration configured")


# =============================================================================
# Helper Functions
# =============================================================================


def _extract_node_count(result: Any) -> int:
    """Extract node count from workflow result."""
    if isinstance(result, dict):
        count = result.get("nodes_executed", 0)
        return int(count) if count is not None else 0
    return 0


def _extract_class_name(args: tuple[Any, ...]) -> str:
    """Extract class name from method args (self)."""
    if args and hasattr(args[0], "__class__"):
        class_name: str = args[0].__class__.__name__
        return class_name
    return "Unknown"


def _extract_node_id(args: tuple[Any, ...], kwargs: Dict[str, Any]) -> Optional[str]:
    """Extract node ID from method args or kwargs."""
    # Try to get from self.id
    if args and hasattr(args[0], "id"):
        return str(args[0].id)
    # Try to get from kwargs
    node_id = kwargs.get("node_id")
    return str(node_id) if node_id is not None else None


# =============================================================================
# Context Propagation Utilities
# =============================================================================


def inject_context_to_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """
    Inject current trace context into HTTP headers.

    Used for propagating trace context across service boundaries.

    Args:
        headers: Existing headers dict

    Returns:
        Headers with trace context injected
    """
    if not OTEL_AVAILABLE:
        return headers

    propagator = TraceContextTextMapPropagator()
    propagator.inject(headers)
    return headers


def extract_context_from_headers(headers: Dict[str, str]) -> Optional[Context]:
    """
    Extract trace context from HTTP headers.

    Used for continuing traces from upstream services.

    Args:
        headers: HTTP headers containing trace context

    Returns:
        Context object or None if no context found
    """
    if not OTEL_AVAILABLE:
        return None

    propagator = TraceContextTextMapPropagator()
    return propagator.extract(headers)
