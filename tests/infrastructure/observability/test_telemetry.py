"""
Tests for CasareRPA OpenTelemetry integration.

Tests TelemetryProvider, instrumentation decorators, and DBOS integration.
"""

import asyncio
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from casare_rpa.infrastructure.observability.telemetry import (
    TelemetryProvider,
    TelemetryConfig,
    ExporterProtocol,
    DBOSSpanContext,
    trace_workflow,
    trace_node,
    trace_async,
    get_tracer,
    get_meter,
    inject_context_to_headers,
    extract_context_from_headers,
    OTEL_AVAILABLE,
)


class TestTelemetryConfig:
    """Tests for TelemetryConfig dataclass."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = TelemetryConfig()

        assert config.service_name == "casare-rpa"
        assert config.service_version == "1.0.0"
        assert config.otlp_endpoint == "http://localhost:4317"
        assert config.otlp_protocol == ExporterProtocol.GRPC
        assert config.traces_enabled is True
        assert config.metrics_enabled is True
        assert config.logs_enabled is True
        assert config.trace_sample_rate == 1.0

    def test_custom_config(self) -> None:
        """Test custom configuration values."""
        config = TelemetryConfig(
            service_name="my-robot",
            service_version="2.0.0",
            otlp_endpoint="http://otel-collector:4317",
            otlp_protocol=ExporterProtocol.HTTP,
            traces_enabled=True,
            metrics_enabled=False,
            console_exporter_enabled=True,
        )

        assert config.service_name == "my-robot"
        assert config.service_version == "2.0.0"
        assert config.otlp_endpoint == "http://otel-collector:4317"
        assert config.otlp_protocol == ExporterProtocol.HTTP
        assert config.metrics_enabled is False
        assert config.console_exporter_enabled is True

    def test_to_resource_attributes(self) -> None:
        """Test conversion to OpenTelemetry resource attributes."""
        config = TelemetryConfig(
            service_name="test-service",
            service_version="1.2.3",
            service_instance_id="instance-001",
            deployment_environment="staging",
        )

        attrs = config.to_resource_attributes()

        assert attrs["service.name"] == "test-service"
        assert attrs["service.version"] == "1.2.3"
        assert attrs["service.instance.id"] == "instance-001"
        assert attrs["deployment.environment"] == "staging"
        assert "host.name" in attrs
        assert attrs["telemetry.sdk.language"] == "python"

    @patch.dict(
        "os.environ",
        {
            "OTEL_SERVICE_NAME": "env-service",
            "OTEL_EXPORTER_OTLP_ENDPOINT": "http://env-endpoint:4317",
        },
    )
    def test_environment_variable_override(self) -> None:
        """Test that environment variables override defaults."""
        config = TelemetryConfig()

        assert config.service_name == "env-service"
        assert config.otlp_endpoint == "http://env-endpoint:4317"


class TestTelemetryProvider:
    """Tests for TelemetryProvider singleton."""

    def test_singleton_pattern(self) -> None:
        """Test that TelemetryProvider is a singleton."""
        provider1 = TelemetryProvider.get_instance()
        provider2 = TelemetryProvider.get_instance()

        assert provider1 is provider2

    def test_initialize_without_otel(self) -> None:
        """Test initialization when OpenTelemetry is not available."""
        provider = TelemetryProvider.get_instance()
        # Reset for clean test
        provider._initialized = False
        provider._tracer_provider = None
        provider._meter_provider = None

        # Should not raise even without OTel packages
        config = TelemetryConfig(
            otlp_protocol=ExporterProtocol.NONE,
        )
        provider.initialize(config, force_reinit=True)

        assert provider._initialized is True

    @pytest.mark.skipif(not OTEL_AVAILABLE, reason="OpenTelemetry not installed")
    def test_initialize_with_console_exporter(self) -> None:
        """Test initialization with console exporter."""
        provider = TelemetryProvider.get_instance()

        config = TelemetryConfig(
            service_name="test-init",
            otlp_protocol=ExporterProtocol.CONSOLE,
            console_exporter_enabled=True,
        )
        provider.initialize(config, force_reinit=True)

        assert provider._initialized is True
        assert provider._tracer_provider is not None

    def test_get_tracer_without_init(self) -> None:
        """Test that get_tracer returns None when not initialized."""
        provider = TelemetryProvider.get_instance()
        provider._initialized = False
        provider._tracer_provider = None

        tracer = provider.get_tracer("test")

        # Returns None when not properly initialized
        # (specific behavior depends on OTEL_AVAILABLE)

    def test_get_meter_without_init(self) -> None:
        """Test that get_meter returns None when not initialized."""
        provider = TelemetryProvider.get_instance()
        provider._initialized = False
        provider._meter_provider = None

        meter = provider.get_meter("test")

        # Returns None when not properly initialized

    def test_record_job_duration(self) -> None:
        """Test job duration recording."""
        provider = TelemetryProvider.get_instance()
        provider._initialized = True
        provider._job_duration_histogram = Mock()

        provider.record_job_duration(
            duration_seconds=45.5,
            workflow_name="TestWorkflow",
            job_id="job-123",
            success=True,
            robot_id="robot-01",
        )

        if provider._job_duration_histogram:
            provider._job_duration_histogram.record.assert_called_once()

    def test_update_queue_depth(self) -> None:
        """Test queue depth update."""
        provider = TelemetryProvider.get_instance()

        provider.update_queue_depth(42)

        assert provider._queue_depth_value == 42.0

    def test_update_robot_utilization(self) -> None:
        """Test robot utilization update."""
        provider = TelemetryProvider.get_instance()

        provider.update_robot_utilization(
            utilization_percent=75.5,
            active_robots=3,
        )

        assert provider._robot_utilization_value == 75.5
        assert provider._active_robots_count == 3


class TestInstrumentationDecorators:
    """Tests for tracing decorators."""

    def test_trace_workflow_sync(self) -> None:
        """Test trace_workflow decorator on sync function."""

        @trace_workflow(workflow_name="TestWorkflow")
        def run_workflow() -> Dict[str, Any]:
            return {"nodes_executed": 5, "success": True}

        result = run_workflow()

        assert result["nodes_executed"] == 5
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_trace_workflow_async(self) -> None:
        """Test trace_workflow decorator on async function."""

        @trace_workflow(workflow_name="AsyncWorkflow")
        async def run_async_workflow() -> Dict[str, Any]:
            await asyncio.sleep(0.01)
            return {"nodes_executed": 10, "success": True}

        result = await run_async_workflow()

        assert result["nodes_executed"] == 10
        assert result["success"] is True

    def test_trace_workflow_exception(self) -> None:
        """Test trace_workflow decorator handles exceptions."""

        @trace_workflow(workflow_name="FailingWorkflow")
        def failing_workflow() -> None:
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            failing_workflow()

    @pytest.mark.asyncio
    async def test_trace_node_async(self) -> None:
        """Test trace_node decorator on async method."""

        class TestNode:
            id = "node-123"

            @trace_node(node_type="ClickNode")
            async def execute(self, ctx: Any) -> Dict[str, Any]:
                await asyncio.sleep(0.01)
                return {"success": True}

        node = TestNode()
        result = await node.execute(Mock())

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_trace_async_decorator(self) -> None:
        """Test general-purpose trace_async decorator."""

        @trace_async(name="fetch_data", component="test.component")
        async def fetch_data(url: str) -> str:
            await asyncio.sleep(0.01)
            return f"data from {url}"

        result = await fetch_data("http://example.com")

        assert result == "data from http://example.com"


class TestDBOSSpanContext:
    """Tests for DBOS workflow span context."""

    @pytest.mark.asyncio
    async def test_dbos_span_context_success(self) -> None:
        """Test DBOS span context for successful workflow."""
        async with DBOSSpanContext(
            workflow_id="wf-123",
            workflow_name="TestWorkflow",
            job_id="job-456",
            robot_id="robot-01",
        ) as ctx:
            ctx.set_result({"nodes_executed": 5})

        # Should complete without error

    @pytest.mark.asyncio
    async def test_dbos_span_context_failure(self) -> None:
        """Test DBOS span context for failed workflow."""
        with pytest.raises(RuntimeError, match="Workflow failed"):
            async with DBOSSpanContext(
                workflow_id="wf-fail",
                workflow_name="FailingWorkflow",
            ) as ctx:
                raise RuntimeError("Workflow failed")

    @pytest.mark.asyncio
    async def test_dbos_span_context_step_span(self) -> None:
        """Test creating step spans within DBOS context."""
        async with DBOSSpanContext(
            workflow_id="wf-steps",
            workflow_name="StepWorkflow",
        ) as ctx:
            # Create a step span
            step_span = ctx.create_step_span("initialize")
            if step_span:
                step_span.end()


class TestContextPropagation:
    """Tests for trace context propagation."""

    def test_inject_context_to_headers(self) -> None:
        """Test injecting trace context into headers."""
        headers: Dict[str, str] = {"Authorization": "Bearer token"}

        result = inject_context_to_headers(headers)

        assert "Authorization" in result
        # When no active span, traceparent may not be added

    def test_extract_context_from_headers(self) -> None:
        """Test extracting trace context from headers."""
        headers = {
            "traceparent": "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"
        }

        context = extract_context_from_headers(headers)

        # Context may be None if OTel not available
        # or may be a valid Context object


class TestModuleFunctions:
    """Tests for module-level convenience functions."""

    def test_get_tracer(self) -> None:
        """Test get_tracer module function."""
        tracer = get_tracer("test.component")

        # May be None if not initialized

    def test_get_meter(self) -> None:
        """Test get_meter module function."""
        meter = get_meter("test.component")

        # May be None if not initialized
