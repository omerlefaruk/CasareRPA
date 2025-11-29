"""
Test fixtures for observability module tests.
"""

import pytest
from unittest.mock import Mock, MagicMock
from typing import Any, Dict

from casare_rpa.infrastructure.observability.telemetry import (
    TelemetryProvider,
    TelemetryConfig,
    ExporterProtocol,
    OTEL_AVAILABLE,
)
from casare_rpa.infrastructure.observability.metrics import RPAMetricsCollector


@pytest.fixture(autouse=True)
def reset_singletons() -> None:
    """Reset singleton state between tests."""
    # Reset TelemetryProvider
    provider = TelemetryProvider.get_instance()
    provider._initialized = False
    provider._tracer_provider = None
    provider._meter_provider = None
    provider._logger_provider = None
    provider._tracers = {}
    provider._meters = {}
    provider._job_duration_histogram = None
    provider._queue_depth_gauge = None
    provider._robot_utilization_gauge = None
    provider._node_execution_counter = None
    provider._workflow_counter = None
    provider._error_counter = None
    provider._queue_depth_value = 0.0
    provider._robot_utilization_value = 0.0
    provider._active_robots_count = 0

    # Reset RPAMetricsCollector - force full reinitialization
    collector = RPAMetricsCollector.get_instance()
    collector._initialized = False
    collector.__init__()  # Reinitialize


@pytest.fixture
def telemetry_config() -> TelemetryConfig:
    """Create a test telemetry configuration."""
    return TelemetryConfig(
        service_name="test-service",
        service_version="1.0.0-test",
        otlp_endpoint="http://localhost:4317",
        otlp_protocol=ExporterProtocol.NONE,  # Disable actual export in tests
        traces_enabled=True,
        metrics_enabled=True,
        logs_enabled=True,
        console_exporter_enabled=False,
    )


@pytest.fixture
def console_config() -> TelemetryConfig:
    """Create a configuration with console exporter for debugging."""
    return TelemetryConfig(
        service_name="test-console",
        otlp_protocol=ExporterProtocol.CONSOLE,
        console_exporter_enabled=True,
    )


@pytest.fixture
def mock_span() -> Mock:
    """Create a mock span for testing."""
    span = Mock()
    span.is_recording.return_value = True
    span.get_span_context.return_value = Mock(
        trace_id=0x0AF7651916CD43DD8448EB211C80319C,
        span_id=0xB7AD6B7169203331,
        trace_flags=1,
    )
    span.set_status = Mock()
    span.set_attribute = Mock()
    span.add_event = Mock()
    span.record_exception = Mock()
    span.end = Mock()
    return span


@pytest.fixture
def mock_tracer(mock_span: Mock) -> Mock:
    """Create a mock tracer for testing."""
    tracer = Mock()
    tracer.start_span.return_value = mock_span
    tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
    tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
    return tracer


@pytest.fixture
def mock_meter() -> Mock:
    """Create a mock meter for testing."""
    meter = Mock()
    meter.create_counter.return_value = Mock()
    meter.create_histogram.return_value = Mock()
    meter.create_up_down_counter.return_value = Mock()
    meter.create_observable_gauge.return_value = Mock()
    return meter
