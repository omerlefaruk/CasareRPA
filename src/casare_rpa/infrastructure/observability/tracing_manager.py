"""
Distributed Tracing Manager for CasareRPA.

Provides OpenTelemetry integration for workflow and node execution tracing.
Supports multiple exporters (OTLP, Jaeger, Zipkin) with lazy initialization.

IMPORTANT: OpenTelemetry packages are lazily loaded to avoid startup overhead
when tracing is disabled.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, Optional

from loguru import logger

if TYPE_CHECKING:
    from opentelemetry.trace import Tracer


class TracingExporter(Enum):
    """Supported tracing exporters."""

    NONE = "none"
    CONSOLE = "console"
    OTLP = "otlp"
    JAEGER = "jaeger"
    ZIPKIN = "zipkin"


@dataclass
class TracingConfig:
    """Configuration for distributed tracing."""

    enabled: bool = False
    exporter: TracingExporter = TracingExporter.NONE
    service_name: str = "casare-rpa"
    endpoint: str = "http://localhost:4317"  # Default OTLP gRPC endpoint
    sample_rate: float = 1.0  # 0.0-1.0 (1.0 = trace everything)
    batch_span_processor: bool = True  # Use batch processor for better performance
    max_queue_size: int = 2048
    max_export_batch_size: int = 512
    export_timeout_ms: int = 30000

    # Additional attributes to include in all spans
    extra_attributes: dict[str, str] = field(default_factory=dict)


class NoOpSpan:
    """No-operation span for when tracing is disabled."""

    def __init__(self) -> None:
        self.is_recording_val = False

    def set_attribute(self, key: str, value: Any) -> None:
        pass

    def set_attributes(self, attributes: dict[str, Any]) -> None:
        pass

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        pass

    def set_status(self, status: Any, description: str | None = None) -> None:
        pass

    def record_exception(
        self,
        exception: BaseException,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        pass

    def end(self, end_time: int | None = None) -> None:
        pass

    def is_recording(self) -> bool:
        return False

    def __enter__(self) -> "NoOpSpan":
        return self

    def __exit__(self, *args: Any) -> None:
        pass


class TracingManager:
    """
    Manages distributed tracing for CasareRPA workflows.

    Provides lazy initialization of OpenTelemetry to avoid startup overhead
    when tracing is disabled. Supports multiple exporters and automatic
    span management for workflows and nodes.

    Usage:
        # Initialize with config
        manager = TracingManager(TracingConfig(enabled=True))

        # Start workflow span
        with manager.workflow_span("my-workflow") as workflow:
            # Start node span
            with manager.node_span("node-1", "ClickElementNode") as node:
                # Your node execution code
                pass
    """

    def __init__(self, config: TracingConfig | None = None) -> None:
        """
        Initialize the tracing manager.

        Args:
            config: Tracing configuration (disabled by default)
        """
        self._config = config or TracingConfig()
        self._tracer: Tracer | None = None
        self._initialized = False
        self._provider = None

        # Current workflow span for nested node spans
        self._current_workflow_span: Any | None = None

    def _initialize(self) -> None:
        """
        Lazily initialize OpenTelemetry components.

        Called on first span creation if tracing is enabled.
        """
        if self._initialized or not self._config.enabled:
            return

        try:
            from opentelemetry import trace
            from opentelemetry.sdk.resources import SERVICE_NAME, Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

            # Create resource with service name and extra attributes
            resource_attributes = {SERVICE_NAME: self._config.service_name}
            resource_attributes.update(self._config.extra_attributes)
            resource = Resource.create(resource_attributes)

            # Create sampler based on sample rate
            sampler = TraceIdRatioBased(self._config.sample_rate)

            # Create provider
            self._provider = TracerProvider(resource=resource, sampler=sampler)

            # Configure exporter
            self._configure_exporter()

            # Set as global provider
            trace.set_tracer_provider(self._provider)

            # Get tracer
            self._tracer = trace.get_tracer(
                self._config.service_name,
                schema_url="https://opentelemetry.io/schemas/1.21.0",
            )

            self._initialized = True
            logger.info(
                f"Tracing initialized: exporter={self._config.exporter.value}, "
                f"endpoint={self._config.endpoint}, sample_rate={self._config.sample_rate}"
            )

        except ImportError as e:
            logger.warning(f"OpenTelemetry packages not installed, tracing disabled: {e}")
            self._config.enabled = False

        except Exception as e:
            logger.error(f"Failed to initialize tracing: {e}")
            self._config.enabled = False

    def _configure_exporter(self) -> None:
        """Configure the span exporter based on config."""
        if self._provider is None:
            return

        from opentelemetry.sdk.trace.export import (
            BatchSpanProcessor,
            SimpleSpanProcessor,
        )

        exporter = None

        if self._config.exporter == TracingExporter.CONSOLE:
            from opentelemetry.sdk.trace.export import ConsoleSpanExporter

            exporter = ConsoleSpanExporter()

        elif self._config.exporter == TracingExporter.OTLP:
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                    OTLPSpanExporter,
                )

                exporter = OTLPSpanExporter(
                    endpoint=self._config.endpoint,
                    timeout=self._config.export_timeout_ms // 1000,
                )
            except ImportError:
                logger.warning("OTLP exporter not installed, falling back to console")
                from opentelemetry.sdk.trace.export import ConsoleSpanExporter

                exporter = ConsoleSpanExporter()

        elif self._config.exporter == TracingExporter.JAEGER:
            try:
                from opentelemetry.exporter.jaeger.thrift import JaegerExporter

                # Parse endpoint for Jaeger (expects host:port format)
                if "://" in self._config.endpoint:
                    from urllib.parse import urlparse

                    parsed = urlparse(self._config.endpoint)
                    host = parsed.hostname or "localhost"
                    port = parsed.port or 6831
                else:
                    parts = self._config.endpoint.split(":")
                    host = parts[0] if parts else "localhost"
                    port = int(parts[1]) if len(parts) > 1 else 6831

                exporter = JaegerExporter(agent_host_name=host, agent_port=port)

            except ImportError:
                logger.warning("Jaeger exporter not installed, falling back to console")
                from opentelemetry.sdk.trace.export import ConsoleSpanExporter

                exporter = ConsoleSpanExporter()

        elif self._config.exporter == TracingExporter.ZIPKIN:
            try:
                from opentelemetry.exporter.zipkin.json import ZipkinExporter

                exporter = ZipkinExporter(endpoint=self._config.endpoint)

            except ImportError:
                logger.warning("Zipkin exporter not installed, falling back to console")
                from opentelemetry.sdk.trace.export import ConsoleSpanExporter

                exporter = ConsoleSpanExporter()

        if exporter is not None:
            if self._config.batch_span_processor:
                processor = BatchSpanProcessor(
                    exporter,
                    max_queue_size=self._config.max_queue_size,
                    max_export_batch_size=self._config.max_export_batch_size,
                )
            else:
                processor = SimpleSpanProcessor(exporter)

            self._provider.add_span_processor(processor)

    def _get_tracer(self) -> Optional["Tracer"]:
        """Get tracer, initializing if needed."""
        if not self._config.enabled:
            return None

        if not self._initialized:
            self._initialize()

        return self._tracer

    @contextmanager
    def workflow_span(
        self,
        workflow_id: str,
        workflow_name: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> Iterator[Any]:
        """
        Create a span for workflow execution.

        Args:
            workflow_id: Unique workflow identifier
            workflow_name: Optional human-readable workflow name
            attributes: Additional span attributes

        Yields:
            Span object (NoOpSpan if tracing disabled)
        """
        tracer = self._get_tracer()

        if tracer is None:
            yield NoOpSpan()
            return

        from opentelemetry.trace import StatusCode

        span_attributes = {
            "workflow.id": workflow_id,
            "workflow.name": workflow_name or workflow_id,
            "rpa.component": "workflow",
        }
        if attributes:
            span_attributes.update(attributes)

        with tracer.start_as_current_span(
            f"workflow:{workflow_name or workflow_id}",
            attributes=span_attributes,
        ) as span:
            self._current_workflow_span = span
            try:
                yield span
                span.set_status(StatusCode.OK)
            except Exception as e:
                span.set_status(StatusCode.ERROR, str(e))
                span.record_exception(e)
                raise
            finally:
                self._current_workflow_span = None

    @contextmanager
    def node_span(
        self,
        node_id: str,
        node_type: str,
        node_name: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> Iterator[Any]:
        """
        Create a span for node execution.

        Args:
            node_id: Unique node identifier
            node_type: Node type (e.g., "ClickElementNode")
            node_name: Optional human-readable node name
            attributes: Additional span attributes

        Yields:
            Span object (NoOpSpan if tracing disabled)
        """
        tracer = self._get_tracer()

        if tracer is None:
            yield NoOpSpan()
            return

        from opentelemetry.trace import StatusCode

        span_attributes = {
            "node.id": node_id,
            "node.type": node_type,
            "node.name": node_name or node_id,
            "rpa.component": "node",
        }
        if attributes:
            span_attributes.update(attributes)

        with tracer.start_as_current_span(
            f"node:{node_type}",
            attributes=span_attributes,
        ) as span:
            try:
                yield span
                span.set_status(StatusCode.OK)
            except Exception as e:
                span.set_status(StatusCode.ERROR, str(e))
                span.record_exception(e)
                raise

    @contextmanager
    def custom_span(
        self,
        name: str,
        attributes: dict[str, Any] | None = None,
    ) -> Iterator[Any]:
        """
        Create a custom span for any operation.

        Args:
            name: Span name
            attributes: Span attributes

        Yields:
            Span object (NoOpSpan if tracing disabled)
        """
        tracer = self._get_tracer()

        if tracer is None:
            yield NoOpSpan()
            return

        from opentelemetry.trace import StatusCode

        with tracer.start_as_current_span(name, attributes=attributes) as span:
            try:
                yield span
                span.set_status(StatusCode.OK)
            except Exception as e:
                span.set_status(StatusCode.ERROR, str(e))
                span.record_exception(e)
                raise

    def record_node_result(
        self,
        span: Any,
        success: bool,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        """
        Record node execution result on a span.

        Args:
            span: Span to record on
            success: Whether execution succeeded
            result: Optional result data
            error: Optional error message
        """
        if isinstance(span, NoOpSpan):
            return

        span.set_attribute("node.success", success)

        if error:
            span.set_attribute("node.error", error)

        if result:
            # Only record safe, non-sensitive result attributes
            for key in ["row_count", "bytes_written", "file_count"]:
                if key in result:
                    span.set_attribute(f"node.result.{key}", result[key])

    def add_workflow_event(
        self,
        name: str,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """
        Add an event to the current workflow span.

        Args:
            name: Event name
            attributes: Event attributes
        """
        if self._current_workflow_span is not None:
            self._current_workflow_span.add_event(name, attributes=attributes)

    def shutdown(self) -> None:
        """Shutdown the tracer provider and flush pending spans."""
        if self._provider is not None:
            try:
                self._provider.shutdown()
                logger.debug("Tracing provider shutdown complete")
            except Exception as e:
                logger.warning(f"Error shutting down tracing provider: {e}")
            finally:
                self._provider = None
                self._tracer = None
                self._initialized = False

    @property
    def enabled(self) -> bool:
        """Check if tracing is enabled."""
        return self._config.enabled

    @property
    def config(self) -> TracingConfig:
        """Get current tracing config."""
        return self._config


# Global tracing manager instance (lazy-initialized)
_tracing_manager: TracingManager | None = None


def get_tracing_manager() -> TracingManager:
    """
    Get the global tracing manager instance.

    Creates a disabled manager if not configured.
    """
    global _tracing_manager
    if _tracing_manager is None:
        _tracing_manager = TracingManager()
    return _tracing_manager


def configure_tracing(config: TracingConfig) -> TracingManager:
    """
    Configure and return the global tracing manager.

    Args:
        config: Tracing configuration

    Returns:
        Configured TracingManager instance
    """
    global _tracing_manager
    if _tracing_manager is not None:
        _tracing_manager.shutdown()
    _tracing_manager = TracingManager(config)
    return _tracing_manager
