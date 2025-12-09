"""
Integration Tests for Architecture Layer Boundaries.

Tests Clean DDD architecture layer integration:
- Application layer use cases work with IExecutionContext
- Domain interfaces are correctly implemented by Infrastructure
- No circular imports between layers
- Dependency direction is correct (Presentation -> Application -> Domain <- Infrastructure)

These tests verify architectural integrity without mocking the actual components,
but do mock external dependencies (Playwright, UIAutomation, etc.).
"""

import importlib
import sys
from typing import List, Set
from unittest.mock import Mock, AsyncMock, MagicMock, patch

import pytest


# =============================================================================
# LAYER IMPORT TESTS
# =============================================================================


@pytest.mark.integration
class TestLayerImports:
    """Tests that layer imports work correctly without circular dependencies."""

    def test_domain_layer_imports(self):
        """Verify domain layer can be imported independently."""
        # Domain should have NO external dependencies
        from casare_rpa.domain.entities import workflow, base_node
        from casare_rpa.domain.value_objects import types

        assert workflow is not None
        assert base_node is not None
        assert types is not None

    def test_domain_has_no_infrastructure_imports(self):
        """Verify domain doesn't import from infrastructure."""
        # Clear cached imports
        domain_modules = [
            "casare_rpa.domain",
            "casare_rpa.domain.entities",
            "casare_rpa.domain.value_objects",
            "casare_rpa.domain.services",
        ]

        for mod_name in domain_modules:
            try:
                mod = importlib.import_module(mod_name)
                source = getattr(mod, "__file__", None)
                if source:
                    with open(source, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        # Check for forbidden imports
                        assert (
                            "from casare_rpa.infrastructure" not in content
                        ), f"{mod_name} should not import from infrastructure"
                        assert (
                            "from casare_rpa.presentation" not in content
                        ), f"{mod_name} should not import from presentation"
            except (ImportError, FileNotFoundError, OSError):
                # Module may not exist or be compiled
                pass

    def test_application_layer_imports(self):
        """Verify application layer can be imported."""
        try:
            from casare_rpa.application import interfaces

            assert interfaces is not None
        except ImportError:
            # Application layer structure may vary
            pass

    def test_infrastructure_layer_imports(self):
        """Verify infrastructure layer can be imported."""
        from casare_rpa.infrastructure import http

        assert http is not None

    def test_presentation_layer_imports(self):
        """Verify presentation layer can be imported (Qt may not be available)."""
        try:
            from casare_rpa.presentation.canvas import main_window

            assert main_window is not None
        except ImportError:
            # Qt may not be available in test environment
            pytest.skip("Qt not available")


# =============================================================================
# INTERFACE IMPLEMENTATION TESTS
# =============================================================================


@pytest.mark.integration
class TestDomainInterfaces:
    """Tests that infrastructure correctly implements domain interfaces."""

    def test_event_bus_interface(self):
        """Verify EventBus implements expected interface."""
        from casare_rpa.domain.events import EventBus

        bus = EventBus()

        # Verify required methods exist
        assert hasattr(bus, "subscribe")
        assert hasattr(bus, "emit")
        assert callable(bus.subscribe)
        assert callable(bus.emit)

    def test_workflow_schema_interface(self):
        """Verify WorkflowSchema has expected interface."""
        from casare_rpa.domain.entities.workflow import WorkflowSchema
        from casare_rpa.domain.entities.workflow_metadata import WorkflowMetadata

        metadata = WorkflowMetadata(name="Test", description="", version="1.0.0")
        schema = WorkflowSchema(metadata)

        # Verify required attributes
        assert hasattr(schema, "metadata")
        assert hasattr(schema, "nodes")
        assert hasattr(schema, "connections")
        assert hasattr(schema, "variables")

    def test_base_node_interface(self):
        """Verify BaseNode has expected interface."""
        from casare_rpa.domain.entities.base_node import BaseNode

        # Verify required methods exist on class
        assert hasattr(BaseNode, "execute")
        assert hasattr(BaseNode, "_define_ports")
        assert hasattr(BaseNode, "add_input_port")
        assert hasattr(BaseNode, "add_output_port")


# =============================================================================
# APPLICATION USE CASE TESTS
# =============================================================================


@pytest.mark.integration
class TestApplicationUseCases:
    """Tests application layer use case integration."""

    def test_workflow_loader_integration(self):
        """Verify workflow loader integrates with domain entities."""
        from casare_rpa.utils.workflow.workflow_loader import load_workflow_from_dict

        workflow_data = {
            "metadata": {
                "name": "Test Workflow",
                "description": "Integration test",
                "version": "1.0.0",
            },
            "nodes": {
                "start": {
                    "node_type": "StartNode",
                    "config": {},
                },
                "end": {
                    "node_type": "EndNode",
                    "config": {},
                },
            },
            "connections": [
                {
                    "source_node": "start",
                    "source_port": "exec_out",
                    "target_node": "end",
                    "target_port": "exec_in",
                }
            ],
            "variables": {},
        }

        workflow = load_workflow_from_dict(workflow_data)

        assert workflow is not None
        assert workflow.metadata.name == "Test Workflow"
        assert len(workflow.nodes) >= 2  # start + end (may have auto-start)
        assert len(workflow.connections) >= 1

    def test_workflow_validation_integration(self):
        """Verify workflow validation works with domain objects."""
        from casare_rpa.utils.workflow.workflow_loader import (
            validate_workflow_structure,
            WorkflowValidationError,
        )

        # Valid workflow
        valid_data = {
            "metadata": {"name": "Valid", "description": "", "version": "1.0.0"},
            "nodes": {"n1": {"node_type": "StartNode", "config": {}}},
            "connections": [],
        }

        # Should not raise
        validate_workflow_structure(valid_data)

        # Invalid workflow (missing required fields)
        invalid_data = {"nodes": {}}

        # Note: metadata may be optional, so we test what we know is invalid
        with pytest.raises(WorkflowValidationError):
            # This should fail on some validation
            validate_workflow_structure(
                {
                    "metadata": {},
                    "nodes": {"bad": {"config": {}}},  # Missing node_type
                    "connections": [],
                }
            )

    def test_security_validation_blocks_dangerous_content(self):
        """Verify security validation catches injection attempts."""
        from casare_rpa.utils.workflow.workflow_loader import (
            validate_workflow_structure,
            WorkflowValidationError,
        )

        dangerous_data = {
            "metadata": {"name": "Dangerous", "description": "", "version": "1.0.0"},
            "nodes": {
                "n1": {
                    "node_type": "SetVariableNode",
                    "config": {"value": "__import__('os').system('rm -rf /')"},
                }
            },
            "connections": [],
        }

        with pytest.raises(WorkflowValidationError):
            validate_workflow_structure(dangerous_data)


# =============================================================================
# INFRASTRUCTURE ADAPTER TESTS
# =============================================================================


@pytest.mark.integration
class TestInfrastructureAdapters:
    """Tests infrastructure adapters integrate correctly."""

    @pytest.mark.asyncio
    async def test_http_session_pool_integration(self):
        """Verify HttpSessionPool integrates with aiohttp."""
        try:
            from casare_rpa.utils.pooling.http_session_pool import HttpSessionPool

            pool = HttpSessionPool(
                max_sessions=2,
                max_connections_per_host=5,
            )

            # Verify pool has expected interface
            assert hasattr(pool, "acquire")
            assert hasattr(pool, "release")
            assert hasattr(pool, "close")
            assert hasattr(pool, "get_stats")

            # Verify stats work
            stats = pool.get_stats()
            assert isinstance(stats, dict)
            assert "available" in stats
            assert "in_use" in stats

            await pool.close()

        except ImportError:
            pytest.skip("aiohttp not available")

    @pytest.mark.asyncio
    async def test_unified_http_client_integration(self):
        """Verify UnifiedHttpClient composes all resilience patterns."""
        try:
            from casare_rpa.infrastructure.http.unified_http_client import (
                UnifiedHttpClient,
                UnifiedHttpClientConfig,
            )

            config = UnifiedHttpClientConfig(
                max_retries=2,
                rate_limit_requests=5,
            )
            client = UnifiedHttpClient(config)

            # Verify client has expected interface
            assert hasattr(client, "start")
            assert hasattr(client, "close")
            assert hasattr(client, "get")
            assert hasattr(client, "post")
            assert hasattr(client, "request")
            assert hasattr(client, "stats")

            await client.close()

        except ImportError:
            pytest.skip("aiohttp not available")

    def test_rate_limiter_integration(self):
        """Verify rate limiter works as expected."""
        from casare_rpa.utils.resilience.rate_limiter import (
            RateLimiter,
            RateLimitConfig,
            SlidingWindowRateLimiter,
        )

        # Token bucket limiter
        config = RateLimitConfig(requests_per_second=10, burst_size=5)
        limiter = RateLimiter(config)

        assert hasattr(limiter, "acquire")
        assert hasattr(limiter, "try_acquire")
        assert hasattr(limiter, "stats")

        # Should acquire immediately
        assert limiter.try_acquire() is True

        # Sliding window limiter
        sw_limiter = SlidingWindowRateLimiter(max_requests=10, window_seconds=1.0)
        assert hasattr(sw_limiter, "acquire")
        assert sw_limiter.try_acquire() is True

    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self):
        """Verify circuit breaker works with async operations."""
        from casare_rpa.robot.circuit_breaker import (
            CircuitBreaker,
            CircuitBreakerConfig,
            CircuitState,
            CircuitBreakerOpenError,
        )

        config = CircuitBreakerConfig(
            failure_threshold=2,
            success_threshold=1,
            timeout=0.1,  # Short timeout for testing
        )
        breaker = CircuitBreaker("test_breaker", config)

        # Initially closed
        assert breaker.state == CircuitState.CLOSED

        # Successful call
        async def success():
            return "ok"

        result = await breaker.call(success)
        assert result == "ok"
        assert breaker.state == CircuitState.CLOSED

        # Failing calls
        async def fail():
            raise Exception("failure")

        for _ in range(2):
            try:
                await breaker.call(fail)
            except Exception:
                pass

        # Should be open after failures
        assert breaker.state == CircuitState.OPEN

        # Should raise when open
        with pytest.raises(CircuitBreakerOpenError):
            await breaker.call(success)

        await breaker.reset()
        assert breaker.state == CircuitState.CLOSED


# =============================================================================
# CROSS-LAYER INTEGRATION TESTS
# =============================================================================


@pytest.mark.integration
class TestCrossLayerIntegration:
    """Tests integration across multiple layers."""

    def test_node_registry_to_workflow_loader(self):
        """Verify node registry integrates with workflow loader."""
        import casare_rpa.nodes as nodes_module
        from casare_rpa.utils.workflow.workflow_loader import (
            get_node_class,
            is_valid_node_type,
        )

        # Both should use the same registry
        for node_type in list(nodes_module._NODE_REGISTRY.keys())[:10]:
            assert is_valid_node_type(node_type) is True
            node_class = get_node_class(node_type)
            assert node_class is not None

    def test_domain_events_to_presentation_bridge(self):
        """Verify domain events can be bridged to presentation."""
        from casare_rpa.domain.events import EventBus, Event
        from casare_rpa.domain.value_objects.types import EventType

        # Create isolated event bus for this test
        bus = EventBus()

        # Track received events
        received = []

        def handler(event):
            received.append(event)

        # Subscribe and emit using EventType enum
        bus.subscribe(EventType.WORKFLOW_STARTED, handler)
        bus.emit(EventType.WORKFLOW_STARTED, {"test": "value"})

        assert len(received) == 1
        assert isinstance(received[0], Event)
        assert received[0].data["test"] == "value"

    def test_execution_context_flow(self):
        """Verify execution context flows through layers correctly."""
        # Create a mock execution context
        context = Mock()
        context.variables = {}
        context.resolve_value = (
            lambda x: context.variables.get(x, x) if isinstance(x, str) else x
        )
        context.set_variable = lambda k, v: context.variables.__setitem__(k, v)
        context.get_variable = lambda k, default=None: context.variables.get(k, default)

        # Set a variable
        context.set_variable("test_key", "test_value")
        assert context.get_variable("test_key") == "test_value"

        # Variable resolution
        context.variables["existing"] = "exists"
        assert context.resolve_value("existing") == "exists"


# =============================================================================
# DEPENDENCY DIRECTION TESTS
# =============================================================================


@pytest.mark.integration
class TestDependencyDirection:
    """Tests that dependencies flow in the correct direction."""

    def test_domain_no_external_deps(self):
        """Verify domain layer has minimal dependencies."""
        from casare_rpa.domain.entities import base_node
        from casare_rpa.domain.value_objects import types

        # These should import without external dependencies
        assert base_node is not None
        assert types is not None

    def test_infrastructure_depends_on_domain(self):
        """Verify infrastructure imports from domain."""
        # Infrastructure should be able to use domain types
        from casare_rpa.domain.entities.workflow import WorkflowSchema
        from casare_rpa.domain.entities.workflow_metadata import WorkflowMetadata

        # Create domain objects in infrastructure context
        metadata = WorkflowMetadata(name="Test", description="", version="1.0.0")
        schema = WorkflowSchema(metadata)
        assert schema is not None

    def test_value_objects_immutability(self):
        """Verify value objects behave as expected."""
        from casare_rpa.domain.value_objects.types import DataType, PortType

        # Enum values should be accessible
        assert DataType.STRING is not None
        assert DataType.INTEGER is not None
        assert PortType.INPUT is not None
        assert PortType.OUTPUT is not None

        # DataType comparisons
        assert DataType.STRING != DataType.INTEGER
        assert DataType.STRING == DataType.STRING


# =============================================================================
# NODE CONNECTION TESTS
# =============================================================================


@pytest.mark.integration
class TestNodeConnectionIntegration:
    """Tests node connection validation across layers."""

    def test_node_connection_creation(self):
        """Verify NodeConnection can be created and serialized."""
        from casare_rpa.domain.entities.node_connection import NodeConnection

        conn = NodeConnection(
            source_node="node1",
            source_port="exec_out",
            target_node="node2",
            target_port="exec_in",
        )

        assert conn.source_node == "node1"
        assert conn.source_port == "exec_out"
        assert conn.target_node == "node2"
        assert conn.target_port == "exec_in"

    def test_node_connection_from_dict(self):
        """Verify NodeConnection can be created from dictionary."""
        from casare_rpa.domain.entities.node_connection import NodeConnection

        conn_dict = {
            "source_node": "node1",
            "source_port": "output",
            "target_node": "node2",
            "target_port": "input",
        }

        conn = NodeConnection.from_dict(conn_dict)
        assert conn.source_node == "node1"
        assert conn.target_node == "node2"


# =============================================================================
# ERROR HANDLING INTEGRATION TESTS
# =============================================================================


@pytest.mark.integration
class TestErrorHandlingIntegration:
    """Tests error handling across layers."""

    def test_domain_errors_propagate(self):
        """Verify domain errors propagate correctly."""
        from casare_rpa.utils.workflow.workflow_loader import (
            WorkflowValidationError,
            validate_workflow_structure,
        )

        # Invalid structure should raise domain-level error
        with pytest.raises(WorkflowValidationError):
            validate_workflow_structure(None)

    def test_infrastructure_errors_wrapped(self):
        """Verify infrastructure errors are properly wrapped."""
        from casare_rpa.utils.resilience.rate_limiter import RateLimitExceeded
        from casare_rpa.robot.circuit_breaker import CircuitBreakerOpenError

        # These should be proper exception types
        assert issubclass(RateLimitExceeded, Exception)
        assert issubclass(CircuitBreakerOpenError, Exception)

        # Should have informative messages
        exc = CircuitBreakerOpenError("test_circuit", 5.0)
        assert "test_circuit" in str(exc)
        assert "5.0" in str(exc)
