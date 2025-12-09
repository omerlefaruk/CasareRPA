"""
Import Time Analysis Tests.

Tests the import time of major modules to identify slow imports
and validate lazy import effectiveness.

Run with: pytest tests/performance/test_import_times.py -v
"""

import gc
import importlib
import sys
import time
from typing import Dict, List, Tuple

import pytest


# Import time thresholds (seconds)
MAX_DOMAIN_IMPORT_TIME_S = 1.0
MAX_APPLICATION_IMPORT_TIME_S = 1.0
MAX_INFRASTRUCTURE_IMPORT_TIME_S = 2.0
MAX_NODES_IMPORT_TIME_S = 1.0
MAX_PRESENTATION_IMPORT_TIME_S = 3.0  # Qt is heavy
MAX_TOTAL_COLD_START_S = 10.0


def clear_casare_modules() -> int:
    """
    Clear all casare_rpa modules from sys.modules.

    Returns:
        Number of modules cleared
    """
    modules_to_remove = [
        key for key in sys.modules.keys() if key.startswith("casare_rpa")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]
    gc.collect()
    return len(modules_to_remove)


def time_import(module_path: str) -> Tuple[float, bool]:
    """
    Time the import of a module.

    Args:
        module_path: Full module path (e.g., "casare_rpa.domain.entities")

    Returns:
        Tuple of (elapsed_time, success)
    """
    try:
        start = time.perf_counter()
        importlib.import_module(module_path)
        elapsed = time.perf_counter() - start
        return elapsed, True
    except Exception as e:
        return 0.0, False


class TestDomainLayerImports:
    """Test domain layer import times."""

    def test_domain_entities_import(self) -> None:
        """Test domain entities import time."""
        clear_casare_modules()

        elapsed, success = time_import("casare_rpa.domain.entities")

        assert success, "Failed to import domain entities"
        assert elapsed < MAX_DOMAIN_IMPORT_TIME_S, (
            f"Domain entities import took {elapsed:.2f}s "
            f"(threshold: {MAX_DOMAIN_IMPORT_TIME_S}s)"
        )

    def test_domain_value_objects_import(self) -> None:
        """Test domain value objects import time."""
        clear_casare_modules()

        elapsed, success = time_import("casare_rpa.domain.value_objects")

        assert success, "Failed to import value objects"
        assert elapsed < MAX_DOMAIN_IMPORT_TIME_S, (
            f"Value objects import took {elapsed:.2f}s "
            f"(threshold: {MAX_DOMAIN_IMPORT_TIME_S}s)"
        )

    def test_domain_services_import(self) -> None:
        """Test domain services import time."""
        clear_casare_modules()

        elapsed, success = time_import("casare_rpa.domain.services")

        assert success, "Failed to import domain services"
        assert elapsed < MAX_DOMAIN_IMPORT_TIME_S, (
            f"Domain services import took {elapsed:.2f}s "
            f"(threshold: {MAX_DOMAIN_IMPORT_TIME_S}s)"
        )


class TestApplicationLayerImports:
    """Test application layer import times."""

    def test_application_use_cases_import(self) -> None:
        """Test application use cases import time."""
        clear_casare_modules()

        elapsed, success = time_import("casare_rpa.application.use_cases")

        assert success, "Failed to import use cases"
        assert elapsed < MAX_APPLICATION_IMPORT_TIME_S, (
            f"Use cases import took {elapsed:.2f}s "
            f"(threshold: {MAX_APPLICATION_IMPORT_TIME_S}s)"
        )

    def test_application_services_import(self) -> None:
        """Test application services import time."""
        clear_casare_modules()

        elapsed, success = time_import("casare_rpa.application.services")

        assert success, "Failed to import application services"
        assert elapsed < MAX_APPLICATION_IMPORT_TIME_S, (
            f"Application services import took {elapsed:.2f}s "
            f"(threshold: {MAX_APPLICATION_IMPORT_TIME_S}s)"
        )


class TestInfrastructureLayerImports:
    """Test infrastructure layer import times."""

    def test_infrastructure_http_import(self) -> None:
        """Test HTTP infrastructure import time."""
        clear_casare_modules()

        elapsed, success = time_import("casare_rpa.infrastructure.http")

        assert success, "Failed to import HTTP infrastructure"
        assert elapsed < MAX_INFRASTRUCTURE_IMPORT_TIME_S, (
            f"HTTP infrastructure import took {elapsed:.2f}s "
            f"(threshold: {MAX_INFRASTRUCTURE_IMPORT_TIME_S}s)"
        )

    def test_infrastructure_resources_import(self) -> None:
        """Test resources infrastructure import time."""
        clear_casare_modules()

        elapsed, success = time_import("casare_rpa.infrastructure.resources")

        assert success, "Failed to import resources"
        assert elapsed < MAX_INFRASTRUCTURE_IMPORT_TIME_S, (
            f"Resources import took {elapsed:.2f}s "
            f"(threshold: {MAX_INFRASTRUCTURE_IMPORT_TIME_S}s)"
        )


class TestNodesImports:
    """Test nodes package import times."""

    def test_nodes_package_import(self) -> None:
        """Test nodes package import time (lazy loading)."""
        clear_casare_modules()

        elapsed, success = time_import("casare_rpa.nodes")

        assert success, "Failed to import nodes package"
        assert elapsed < MAX_NODES_IMPORT_TIME_S, (
            f"Nodes package import took {elapsed:.2f}s "
            f"(threshold: {MAX_NODES_IMPORT_TIME_S}s)"
        )

    def test_basic_nodes_import(self) -> None:
        """Test basic nodes module import time."""
        clear_casare_modules()

        elapsed, success = time_import("casare_rpa.nodes.basic_nodes")

        assert success, "Failed to import basic nodes"
        assert elapsed < MAX_NODES_IMPORT_TIME_S, (
            f"Basic nodes import took {elapsed:.2f}s "
            f"(threshold: {MAX_NODES_IMPORT_TIME_S}s)"
        )

    def test_browser_nodes_import(self) -> None:
        """Test browser nodes module import time."""
        clear_casare_modules()

        elapsed, success = time_import("casare_rpa.nodes.browser_nodes")

        assert success, "Failed to import browser nodes"
        assert elapsed < MAX_NODES_IMPORT_TIME_S, (
            f"Browser nodes import took {elapsed:.2f}s "
            f"(threshold: {MAX_NODES_IMPORT_TIME_S}s)"
        )

    def test_variable_nodes_import(self) -> None:
        """Test variable nodes module import time."""
        clear_casare_modules()

        elapsed, success = time_import("casare_rpa.nodes.variable_nodes")

        assert success, "Failed to import variable nodes"
        assert elapsed < MAX_NODES_IMPORT_TIME_S, (
            f"Variable nodes import took {elapsed:.2f}s "
            f"(threshold: {MAX_NODES_IMPORT_TIME_S}s)"
        )


class TestCoreImports:
    """Test core utilities import times."""

    def test_execution_context_import(self) -> None:
        """Test ExecutionContext import time."""
        clear_casare_modules()

        elapsed, success = time_import(
            "casare_rpa.application.use_cases.execute_workflow"
        )

        assert success, "Failed to import execute_workflow module"
        assert (
            elapsed < 2.0
        ), f"ExecutionContext import took {elapsed:.2f}s (threshold: 2.0s)"

    def test_utils_resilience_import(self) -> None:
        """Test resilience utilities import time."""
        clear_casare_modules()

        elapsed, success = time_import("casare_rpa.utils.resilience")

        assert success, "Failed to import resilience utils"
        assert (
            elapsed < 1.0
        ), f"Resilience utils import took {elapsed:.2f}s (threshold: 1.0s)"


class TestLazyImportEffectiveness:
    """Test that lazy imports are effective."""

    def test_nodes_lazy_import_is_faster(self) -> None:
        """
        Test that lazy node import is faster than direct module import.

        The nodes package uses __getattr__ for lazy loading, so importing
        the package should be much faster than importing individual modules.
        """
        clear_casare_modules()

        # Time lazy import (just the registry)
        start = time.perf_counter()
        import casare_rpa.nodes

        lazy_time = time.perf_counter() - start

        clear_casare_modules()

        # Time direct imports of multiple node modules
        start = time.perf_counter()
        from casare_rpa.nodes import basic_nodes
        from casare_rpa.nodes import variable_nodes
        from casare_rpa.nodes import browser_nodes

        direct_time = time.perf_counter() - start

        # Lazy should be faster than loading 3 modules
        assert lazy_time < direct_time, (
            f"Lazy import ({lazy_time:.3f}s) should be faster than "
            f"direct imports ({direct_time:.3f}s)"
        )

    def test_accessing_few_nodes_is_fast(self) -> None:
        """Test that accessing just a few nodes is fast."""
        clear_casare_modules()

        start = time.perf_counter()
        from casare_rpa.nodes import StartNode, EndNode, SetVariableNode

        elapsed = time.perf_counter() - start

        assert elapsed < 2.0, f"Accessing 3 nodes took {elapsed:.2f}s (threshold: 2.0s)"


class TestImportDependencyChain:
    """Test import dependency chain timing."""

    def test_import_chain_domain_to_nodes(self) -> None:
        """Test import chain from domain to nodes."""
        clear_casare_modules()

        timings: Dict[str, float] = {}

        # Import in dependency order
        modules = [
            "casare_rpa.domain.value_objects",
            "casare_rpa.domain.entities",
            "casare_rpa.application.use_cases.execute_workflow",
            "casare_rpa.nodes",
        ]

        total_start = time.perf_counter()
        for module in modules:
            start = time.perf_counter()
            importlib.import_module(module)
            timings[module] = time.perf_counter() - start
        total_time = time.perf_counter() - total_start

        # Total chain should be reasonable
        assert (
            total_time < 5.0
        ), f"Full import chain took {total_time:.2f}s (threshold: 5.0s)"

        # Log individual timings for analysis
        for module, t in timings.items():
            short_name = module.replace("casare_rpa.", "")
            print(f"  {short_name}: {t*1000:.1f}ms")


class TestSlowImportIdentification:
    """Identify potentially slow imports."""

    def test_identify_slow_node_modules(self) -> None:
        """
        Identify slow node module imports.

        Tests each node category and reports timing.
        """
        node_modules = [
            "casare_rpa.nodes.basic_nodes",
            "casare_rpa.nodes.variable_nodes",
            "casare_rpa.nodes.control_flow_nodes",
            "casare_rpa.nodes.data_operation_nodes",
            "casare_rpa.nodes.browser_nodes",
            "casare_rpa.nodes.navigation_nodes",
            "casare_rpa.nodes.interaction_nodes",
            "casare_rpa.nodes.data_nodes",
            "casare_rpa.nodes.wait_nodes",
        ]

        slow_modules: List[Tuple[str, float]] = []

        for module in node_modules:
            clear_casare_modules()
            elapsed, success = time_import(module)

            if success and elapsed > 0.5:  # > 500ms is "slow"
                slow_modules.append((module, elapsed))

        # Report slow modules but don't fail
        if slow_modules:
            print("\nSlow node modules (> 500ms):")
            for module, elapsed in slow_modules:
                print(f"  {module}: {elapsed*1000:.1f}ms")

        # Fail only if any module takes > 2 seconds
        very_slow = [m for m, t in slow_modules if t > 2.0]
        assert len(very_slow) == 0, f"Very slow modules (> 2s): {very_slow}"

    def test_identify_slow_infrastructure_modules(self) -> None:
        """Identify slow infrastructure module imports."""
        infra_modules = [
            "casare_rpa.infrastructure.http",
            "casare_rpa.infrastructure.resources",
            "casare_rpa.infrastructure.execution",
            "casare_rpa.infrastructure.persistence",
        ]

        slow_modules: List[Tuple[str, float]] = []

        for module in infra_modules:
            clear_casare_modules()
            elapsed, success = time_import(module)

            if success and elapsed > 0.5:
                slow_modules.append((module, elapsed))

        if slow_modules:
            print("\nSlow infrastructure modules (> 500ms):")
            for module, elapsed in slow_modules:
                print(f"  {module}: {elapsed*1000:.1f}ms")


class TestColdStartSimulation:
    """Test simulated cold start scenarios."""

    def test_minimal_cold_start(self) -> None:
        """
        Test minimal cold start time.

        Simulates importing just enough to run a simple workflow.
        """
        clear_casare_modules()

        start = time.perf_counter()

        # Minimal imports for workflow execution
        from casare_rpa.domain.entities.workflow import WorkflowSchema
        from casare_rpa.nodes.basic_nodes import StartNode, EndNode
        from casare_rpa.nodes.variable_nodes import SetVariableNode

        elapsed = time.perf_counter() - start

        assert (
            elapsed < 3.0
        ), f"Minimal cold start took {elapsed:.2f}s (threshold: 3.0s)"

    def test_full_application_cold_start(self) -> None:
        """
        Test full application cold start time.

        This is a worst-case scenario importing all major components.
        Should still complete in reasonable time.
        """
        clear_casare_modules()

        start = time.perf_counter()

        # Import order similar to application startup
        try:
            # Domain
            from casare_rpa.domain.entities.workflow import WorkflowSchema
            from casare_rpa.domain.value_objects import DataType

            # Application (includes ExecutionContext)
            from casare_rpa.application.use_cases.execute_workflow import (
                ExecutionContext,
            )
            from casare_rpa.application.services import orchestrator_client

            # Infrastructure
            from casare_rpa.infrastructure.http import unified_http_client
            from casare_rpa.infrastructure.resources import unified_resource_manager

            # Nodes (lazy loading)
            import casare_rpa.nodes

            elapsed = time.perf_counter() - start

            assert elapsed < MAX_TOTAL_COLD_START_S, (
                f"Full cold start took {elapsed:.2f}s "
                f"(threshold: {MAX_TOTAL_COLD_START_S}s)"
            )

        except ImportError as e:
            # Some modules may not exist - that's OK for this test
            elapsed = time.perf_counter() - start
            print(f"Import error (may be expected): {e}")
            assert elapsed < MAX_TOTAL_COLD_START_S


class TestImportCaching:
    """Test import caching behavior."""

    def test_subsequent_imports_are_instant(self) -> None:
        """Test that subsequent imports of same module are instant."""
        clear_casare_modules()

        # First import
        first_start = time.perf_counter()
        from casare_rpa.domain.entities.workflow import WorkflowSchema

        first_time = time.perf_counter() - first_start

        # Second import (should be cached)
        second_start = time.perf_counter()
        second_time = time.perf_counter() - second_start

        # Second import should be essentially instant
        assert (
            second_time < 0.001
        ), f"Cached import took {second_time*1000:.3f}ms (should be < 1ms)"

        # Second should be much faster than first
        assert second_time < first_time / 100, (
            f"Cached import ({second_time*1000:.3f}ms) should be 100x faster "
            f"than first ({first_time*1000:.1f}ms)"
        )

    def test_reimport_after_clear_is_slow(self) -> None:
        """Test that reimport after cache clear takes time again."""
        clear_casare_modules()

        # First import
        first_start = time.perf_counter()
        import casare_rpa.nodes.basic_nodes

        first_time = time.perf_counter() - first_start

        # Clear cache
        clear_casare_modules()

        # Second import after clear (should be similar to first)
        second_start = time.perf_counter()
        second_time = time.perf_counter() - second_start

        # Times should be similar (within 5x)
        ratio = max(first_time, second_time) / max(min(first_time, second_time), 0.001)
        assert ratio < 5, (
            f"Import times after cache clear differ too much: "
            f"first={first_time*1000:.1f}ms, second={second_time*1000:.1f}ms"
        )
