"""
CasareRPA - Infrastructure: Unified Observability Facade

Single entry point for all observability functionality.
Auto-configures based on environment (dev=console, prod=telemetry).

Usage:
    from casare_rpa.infrastructure.observability import Observability

    # Initialize once at startup
    Observability.configure()

    # Use throughout application
    Observability.log("info", "Starting workflow", workflow_id="abc123")
    Observability.metric("job_duration", 45.2, {"robot_id": "r1"})

    with Observability.trace("execute_workflow", {"workflow_name": "invoice"}):
        # Traced code block
        pass
"""

from __future__ import annotations

import os
import threading
import time
import warnings
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Generator, Optional, TypeVar

from loguru import logger

# Import underlying components
from casare_rpa.infrastructure.observability.telemetry import (
    TelemetryProvider,
    TelemetryConfig,
    ExporterProtocol,
    OTEL_AVAILABLE,
)
from casare_rpa.infrastructure.observability.metrics import (
    RPAMetricsCollector,
    get_metrics_collector,
)
from casare_rpa.infrastructure.observability.system_metrics import (
    SystemMetricsCollector,
    get_system_metrics_collector,
)
from casare_rpa.infrastructure.observability.logging import (
    configure_logging as _configure_logging,
    SpanLogger,
)
from casare_rpa.infrastructure.observability.stdout_capture import (
    set_output_callbacks,
    remove_output_callbacks,
    capture_output,
)


T = TypeVar("T")


class Environment(str, Enum):
    """Deployment environment."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class ObservabilityConfig:
    """
    Unified configuration for all observability components.

    Auto-detects environment from CASARE_ENV or defaults to development.
    """

    # Environment
    environment: Environment = field(
        default_factory=lambda: Environment(
            os.getenv("CASARE_ENV", "development").lower()
        )
    )

    # Service identification (from env or defaults)
    service_name: str = field(
        default_factory=lambda: os.getenv("OTEL_SERVICE_NAME", "casare-rpa")
    )
    service_version: str = field(
        default_factory=lambda: os.getenv("OTEL_SERVICE_VERSION", "1.0.0")
    )

    # Telemetry (dev=console, prod=OTLP)
    otlp_endpoint: str = field(
        default_factory=lambda: os.getenv(
            "OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"
        )
    )
    enable_telemetry: bool = field(
        default_factory=lambda: os.getenv("ENABLE_TELEMETRY", "true").lower() == "true"
    )

    # Logging
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    enable_console_logs: bool = True
    enable_otel_log_export: bool = field(
        default_factory=lambda: os.getenv("ENABLE_OTEL_LOG_EXPORT", "false").lower()
        == "true"
    )

    # Metrics
    metrics_export_interval_seconds: int = 60
    enable_system_metrics: bool = True

    # Standard labels for all metrics
    robot_id: Optional[str] = field(default_factory=lambda: os.getenv("ROBOT_ID"))
    tenant_id: Optional[str] = field(default_factory=lambda: os.getenv("TENANT_ID"))

    def to_telemetry_config(self) -> TelemetryConfig:
        """Convert to TelemetryConfig for OpenTelemetry initialization."""
        # Determine protocol based on environment
        if self.environment == Environment.DEVELOPMENT:
            protocol = ExporterProtocol.CONSOLE
        else:
            protocol = ExporterProtocol.GRPC

        return TelemetryConfig(
            service_name=self.service_name,
            service_version=self.service_version,
            deployment_environment=self.environment.value,
            otlp_endpoint=self.otlp_endpoint,
            otlp_protocol=protocol,
            traces_enabled=self.enable_telemetry,
            metrics_enabled=self.enable_telemetry,
            logs_enabled=self.enable_otel_log_export,
            console_exporter_enabled=(self.environment == Environment.DEVELOPMENT),
            metrics_export_interval_ms=self.metrics_export_interval_seconds * 1000,
        )


class Observability:
    """
    Unified observability facade providing single entry point for:
    - Logging (via Loguru + OTel export)
    - Metrics (via RPAMetricsCollector + OTel)
    - Tracing (via OpenTelemetry)
    - Stdout capture (for UI terminal)
    - System metrics (CPU/memory via psutil)

    Thread-safe singleton with environment-aware auto-configuration.

    Usage:
        # Initialize at startup (call once)
        Observability.configure()

        # Or with custom config
        Observability.configure(ObservabilityConfig(
            environment=Environment.PRODUCTION,
            robot_id="robot-01",
        ))

        # Logging
        Observability.log("info", "Message", extra_key="value")
        Observability.log("error", "Failed", error=str(e))

        # Metrics
        Observability.metric("job_duration", 45.2, {"workflow": "invoice"})
        Observability.increment("job_count", {"status": "completed"})
        Observability.gauge("queue_depth", 12)

        # Tracing
        with Observability.trace("operation_name", {"attr": "value"}):
            # Code to trace
            pass

        # Shutdown (call at exit)
        Observability.shutdown()
    """

    _instance: Optional["Observability"] = None
    _lock: threading.Lock = threading.Lock()
    _config: Optional[ObservabilityConfig] = None
    _initialized: bool = False

    # Component references
    _telemetry: Optional[TelemetryProvider] = None
    _metrics_collector: Optional[RPAMetricsCollector] = None
    _system_metrics: Optional[SystemMetricsCollector] = None
    _span_logger: Optional[SpanLogger] = None

    @classmethod
    def configure(
        cls,
        config: Optional[ObservabilityConfig] = None,
        force_reinit: bool = False,
    ) -> None:
        """
        Initialize all observability components.

        Idempotent: safe to call multiple times. Will only initialize once
        unless force_reinit=True.

        Args:
            config: Custom configuration. Uses auto-detected defaults if None.
            force_reinit: Force reinitialization even if already configured.
        """
        with cls._lock:
            if cls._initialized and not force_reinit:
                logger.debug("Observability already configured")
                return

            cls._config = config or ObservabilityConfig()

            logger.info(
                f"Configuring observability for {cls._config.environment.value} "
                f"(service={cls._config.service_name})"
            )

            # Initialize telemetry (OpenTelemetry)
            if cls._config.enable_telemetry and OTEL_AVAILABLE:
                cls._telemetry = TelemetryProvider.get_instance()
                cls._telemetry.initialize(
                    cls._config.to_telemetry_config(),
                    force_reinit=force_reinit,
                )
            else:
                logger.info(
                    "Telemetry disabled (OTEL_AVAILABLE=%s, enable_telemetry=%s)",
                    OTEL_AVAILABLE,
                    cls._config.enable_telemetry,
                )

            # Configure logging
            _configure_logging(
                enable_otel_export=cls._config.enable_otel_log_export,
                enable_trace_context=cls._config.enable_telemetry,
                log_level=cls._config.log_level,
            )

            # Initialize metrics collector
            cls._metrics_collector = get_metrics_collector()

            # Initialize system metrics (if enabled)
            if cls._config.enable_system_metrics:
                cls._system_metrics = get_system_metrics_collector()

            # Create span logger for trace-correlated logging
            cls._span_logger = SpanLogger("casare_rpa.facade")

            cls._initialized = True
            logger.info("Observability configured successfully")

    @classmethod
    def is_configured(cls) -> bool:
        """Check if observability has been configured."""
        return cls._initialized

    @classmethod
    def get_config(cls) -> Optional[ObservabilityConfig]:
        """Get current configuration."""
        return cls._config

    # =========================================================================
    # Logging
    # =========================================================================

    @classmethod
    def log(
        cls,
        level: str,
        message: str,
        **attributes: Any,
    ) -> None:
        """
        Log a message with optional structured attributes.

        If tracing is active, the log will be correlated with the current span.

        Args:
            level: Log level (debug, info, warning, error, critical)
            message: Log message
            **attributes: Additional structured attributes
        """
        if not cls._initialized:
            # Fallback to plain loguru
            log_method = getattr(logger, level.lower(), logger.info)
            log_method(message, **attributes)
            return

        # Add standard labels if configured
        if cls._config:
            if cls._config.robot_id and "robot_id" not in attributes:
                attributes["robot_id"] = cls._config.robot_id
            if cls._config.tenant_id and "tenant_id" not in attributes:
                attributes["tenant_id"] = cls._config.tenant_id

        # Use span logger for trace correlation
        if cls._span_logger:
            log_method = getattr(cls._span_logger, level.lower(), cls._span_logger.info)
            log_method(message, **attributes)
        else:
            log_method = getattr(logger, level.lower(), logger.info)
            log_method(message, **attributes)

    @classmethod
    def debug(cls, message: str, **attributes: Any) -> None:
        """Log debug message."""
        cls.log("debug", message, **attributes)

    @classmethod
    def info(cls, message: str, **attributes: Any) -> None:
        """Log info message."""
        cls.log("info", message, **attributes)

    @classmethod
    def warning(cls, message: str, **attributes: Any) -> None:
        """Log warning message."""
        cls.log("warning", message, **attributes)

    @classmethod
    def error(cls, message: str, **attributes: Any) -> None:
        """Log error message."""
        cls.log("error", message, **attributes)

    # =========================================================================
    # Metrics
    # =========================================================================

    @classmethod
    def metric(
        cls,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Record a metric value (histogram/gauge style).

        Args:
            name: Metric name (e.g., "job_duration", "queue_depth")
            value: Metric value
            labels: Optional metric labels/attributes
        """
        if not cls._initialized or not cls._telemetry:
            return

        all_labels = cls._get_standard_labels()
        if labels:
            all_labels.update(labels)

        # Route to appropriate collector method based on metric name
        if name == "job_duration":
            cls._telemetry.record_job_duration(
                duration_seconds=value,
                workflow_name=all_labels.get("workflow_name", "unknown"),
                job_id=all_labels.get("job_id", "unknown"),
                success=all_labels.get("success", "true").lower() == "true",
                robot_id=all_labels.get("robot_id"),
            )
        elif name == "queue_depth":
            cls._telemetry.update_queue_depth(int(value))
        elif name == "robot_utilization":
            cls._telemetry.update_robot_utilization(
                utilization_percent=value,
                active_robots=int(all_labels.get("active_robots", 0)),
            )
        else:
            # Generic metric via OTel meter
            meter = cls._telemetry.get_meter("casare_rpa.facade")
            if meter:
                histogram = meter.create_histogram(
                    name=f"casare_rpa.{name}",
                    description=f"Custom metric: {name}",
                )
                histogram.record(value, all_labels)

    @classmethod
    def increment(
        cls,
        name: str,
        labels: Optional[Dict[str, str]] = None,
        value: int = 1,
    ) -> None:
        """
        Increment a counter metric.

        Args:
            name: Counter name (e.g., "job_count", "error_count")
            labels: Optional metric labels/attributes
            value: Amount to increment (default: 1)
        """
        if not cls._initialized or not cls._telemetry:
            return

        all_labels = cls._get_standard_labels()
        if labels:
            all_labels.update(labels)

        # Route to collector or generic counter
        if name == "node_execution":
            cls._telemetry.record_node_execution(
                node_type=all_labels.get("node_type", "unknown"),
                node_id=all_labels.get("node_id", "unknown"),
                success=all_labels.get("success", "true").lower() == "true",
                duration_ms=float(all_labels.get("duration_ms", 0)),
            )
        elif name == "workflow_execution":
            cls._telemetry.record_workflow_execution(
                workflow_name=all_labels.get("workflow_name", "unknown"),
                success=all_labels.get("success", "true").lower() == "true",
                node_count=int(all_labels.get("node_count", 0)),
                trigger_type=all_labels.get("trigger_type", "manual"),
            )
        elif name == "error":
            cls._telemetry.record_error(
                error_type=all_labels.get("error_type", "unknown"),
                component=all_labels.get("component", "unknown"),
                message=all_labels.get("message", ""),
                recoverable=all_labels.get("recoverable", "false").lower() == "true",
            )
        else:
            # Generic counter via OTel meter
            meter = cls._telemetry.get_meter("casare_rpa.facade")
            if meter:
                counter = meter.create_counter(
                    name=f"casare_rpa.{name}",
                    description=f"Custom counter: {name}",
                )
                counter.add(value, all_labels)

    @classmethod
    def gauge(
        cls, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Set a gauge metric value.

        Args:
            name: Gauge name
            value: Current value
            labels: Optional labels
        """
        # Gauges are typically updated via the underlying collector
        cls.metric(name, value, labels)

    @classmethod
    def _get_standard_labels(cls) -> Dict[str, str]:
        """Get standard labels from config."""
        labels: Dict[str, str] = {}
        if cls._config:
            labels["environment"] = cls._config.environment.value
            if cls._config.robot_id:
                labels["robot_id"] = cls._config.robot_id
            if cls._config.tenant_id:
                labels["tenant_id"] = cls._config.tenant_id
        return labels

    # =========================================================================
    # Tracing
    # =========================================================================

    @classmethod
    @contextmanager
    def trace(
        cls,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        component: str = "casare_rpa",
    ) -> Generator[Optional[Any], None, None]:
        """
        Create a trace span context manager.

        Usage:
            with Observability.trace("execute_workflow", {"workflow_id": "abc"}):
                # Code to trace
                pass

        Args:
            name: Span name
            attributes: Span attributes
            component: Component name for tracer

        Yields:
            Span object or None if tracing disabled
        """
        if not cls._initialized or not cls._telemetry:
            yield None
            return

        # Add standard labels to attributes
        all_attrs = cls._get_standard_labels()
        if attributes:
            all_attrs.update({k: str(v) for k, v in attributes.items()})

        with cls._telemetry.span(
            name, attributes=all_attrs, component=component
        ) as span:
            yield span

    @classmethod
    def get_tracer(cls, name: str = "casare_rpa") -> Optional[Any]:
        """
        Get OpenTelemetry tracer for advanced tracing.

        Args:
            name: Tracer name

        Returns:
            Tracer instance or None if not configured
        """
        if not cls._initialized or not cls._telemetry:
            return None
        return cls._telemetry.get_tracer(name)

    @classmethod
    def get_meter(cls, name: str = "casare_rpa") -> Optional[Any]:
        """
        Get OpenTelemetry meter for advanced metrics.

        Args:
            name: Meter name

        Returns:
            Meter instance or None if not configured
        """
        if not cls._initialized or not cls._telemetry:
            return None
        return cls._telemetry.get_meter(name)

    # =========================================================================
    # Stdout Capture
    # =========================================================================

    @classmethod
    def capture_stdout(
        cls,
        stdout_callback: Optional[Callable[[str], None]] = None,
        stderr_callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        """
        Start capturing stdout/stderr to callbacks.

        Used by UI to display print() output in Terminal tab.

        Args:
            stdout_callback: Function called with each stdout line
            stderr_callback: Function called with each stderr line
        """
        set_output_callbacks(stdout_callback, stderr_callback)

    @classmethod
    def stop_stdout_capture(cls) -> None:
        """Stop capturing stdout/stderr."""
        remove_output_callbacks()

    @classmethod
    @contextmanager
    def captured_output(
        cls,
        stdout_callback: Optional[Callable[[str], None]] = None,
        stderr_callback: Optional[Callable[[str], None]] = None,
    ) -> Generator[None, None, None]:
        """
        Context manager for stdout/stderr capture.

        Usage:
            with Observability.captured_output(on_stdout, on_stderr):
                print("Goes to callback")
        """
        with capture_output(stdout_callback, stderr_callback):
            yield

    # =========================================================================
    # System Metrics
    # =========================================================================

    @classmethod
    def get_system_metrics(cls) -> Dict[str, Any]:
        """
        Get current system metrics (CPU, memory, etc).

        Returns:
            Dict with system metrics
        """
        if not cls._system_metrics:
            return {}

        process = cls._system_metrics.get_process_metrics()
        system = cls._system_metrics.get_system_metrics()

        return {
            "process": {
                "cpu_percent": process.cpu_percent,
                "memory_rss_mb": process.memory_rss_mb,
                "memory_vms_mb": process.memory_vms_mb,
                "memory_percent": process.memory_percent,
                "num_threads": process.num_threads,
            },
            "system": {
                "cpu_percent": system.cpu_percent,
                "cpu_count": system.cpu_count,
                "memory_total_mb": system.memory_total_mb,
                "memory_available_mb": system.memory_available_mb,
                "memory_percent": system.memory_percent,
            },
        }

    # =========================================================================
    # Metrics Collector Access
    # =========================================================================

    @classmethod
    def get_metrics_collector(cls) -> Optional[RPAMetricsCollector]:
        """
        Get the underlying RPA metrics collector for advanced usage.

        Returns:
            RPAMetricsCollector instance or None
        """
        return cls._metrics_collector

    # =========================================================================
    # Shutdown
    # =========================================================================

    @classmethod
    def shutdown(cls) -> None:
        """
        Shutdown all observability components and flush pending data.

        Call at application exit.
        """
        with cls._lock:
            if not cls._initialized:
                return

            logger.info("Shutting down observability")

            # Stop stdout capture
            cls.stop_stdout_capture()

            # Shutdown telemetry
            if cls._telemetry:
                cls._telemetry.shutdown()

            cls._initialized = False
            logger.info("Observability shutdown complete")


# =============================================================================
# Convenience Function for Quick Configuration
# =============================================================================


def configure_observability(
    environment: Optional[str] = None,
    robot_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """
    Quick configuration function for observability.

    Args:
        environment: "development", "staging", or "production"
        robot_id: Robot identifier for metrics
        tenant_id: Tenant identifier for multi-tenancy
        **kwargs: Additional ObservabilityConfig parameters
    """
    config_kwargs: Dict[str, Any] = {}

    if environment:
        config_kwargs["environment"] = Environment(environment.lower())
    if robot_id:
        config_kwargs["robot_id"] = robot_id
    if tenant_id:
        config_kwargs["tenant_id"] = tenant_id

    config_kwargs.update(kwargs)
    config = ObservabilityConfig(**config_kwargs)
    Observability.configure(config)


# =============================================================================
# Deprecation Warnings for Old Direct Imports
# =============================================================================


def _deprecated_import_warning(old_name: str, new_name: str) -> None:
    """Issue deprecation warning for old import patterns."""
    warnings.warn(
        f"Direct import of '{old_name}' is deprecated. "
        f"Use 'from casare_rpa.infrastructure.observability import {new_name}' instead.",
        DeprecationWarning,
        stacklevel=3,
    )
