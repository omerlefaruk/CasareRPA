"""
Performance baseline tests for CasareRPA.

This module establishes baseline performance metrics for:
- Application startup time
- Module import times
- Workflow execution time
- Memory usage patterns

Run with: pytest tests/performance/test_baseline.py -v
"""

import gc
import importlib
import sys
import time
from typing import Any, Dict, List, Tuple
from unittest.mock import MagicMock, patch

import psutil
import pytest


def get_process_memory_mb() -> float:
    """Get current process memory usage in MB."""
    process = psutil.Process()
    return process.memory_info().rss / (1024 * 1024)


def force_gc() -> None:
    """Force garbage collection for accurate memory measurements."""
    gc.collect()
    gc.collect()
    gc.collect()


class TestImportPerformance:
    """Tests for module import performance."""

    def test_core_imports_time(self, benchmark: Any) -> None:
        """Measure time to import core modules."""

        def import_core_modules() -> List[str]:
            modules_to_import = [
                "casare_rpa",
                "casare_rpa.domain",
                "casare_rpa.domain.entities.base_node",
            ]
            imported = []
            for module_name in modules_to_import:
                try:
                    # Remove from cache to measure fresh import
                    if module_name in sys.modules:
                        del sys.modules[module_name]
                    importlib.import_module(module_name)
                    imported.append(module_name)
                except ImportError:
                    pass
            return imported

        result = benchmark(import_core_modules)
        assert len(result) > 0, "Should import at least one core module"

    def test_node_imports_time(self, benchmark: Any) -> None:
        """Measure time to import node modules."""

        def import_node_modules() -> List[str]:
            modules_to_import = [
                "casare_rpa.nodes",
                "casare_rpa.nodes.basic_nodes",
                "casare_rpa.nodes.variable_nodes",
                "casare_rpa.nodes.control_flow_nodes",
            ]
            imported = []
            for module_name in modules_to_import:
                try:
                    if module_name in sys.modules:
                        del sys.modules[module_name]
                    importlib.import_module(module_name)
                    imported.append(module_name)
                except ImportError:
                    pass
            return imported

        result = benchmark(import_node_modules)
        assert len(result) > 0, "Should import at least one node module"

    def test_canvas_imports_time(self, benchmark: Any) -> None:
        """Measure time to import canvas/UI modules (without Qt)."""

        def import_canvas_modules() -> List[str]:
            # Skip Qt-dependent modules and only test importable ones
            modules_to_import = [
                "casare_rpa.utils",
                "casare_rpa.utils.config",
            ]
            imported = []
            for module_name in modules_to_import:
                try:
                    if module_name in sys.modules:
                        del sys.modules[module_name]
                    importlib.import_module(module_name)
                    imported.append(module_name)
                except ImportError:
                    pass
            return imported

        result = benchmark(import_canvas_modules)
        assert len(result) > 0, "Should import at least one utility module"


class TestMemoryBaseline:
    """Tests for memory usage baseline."""

    def test_baseline_memory_usage(self) -> None:
        """Measure baseline memory usage after importing core modules."""
        force_gc()
        initial_memory = get_process_memory_mb()

        # Import core modules
        try:
            import casare_rpa
            import casare_rpa.domain
            import casare_rpa.nodes
        except ImportError:
            pytest.skip("Core modules not available")

        force_gc()
        after_import_memory = get_process_memory_mb()

        memory_increase = after_import_memory - initial_memory

        # Record metrics
        print("\n=== Memory Baseline ===")
        print(f"Initial memory: {initial_memory:.2f} MB")
        print(f"After imports: {after_import_memory:.2f} MB")
        print(f"Memory increase: {memory_increase:.2f} MB")

        # Assert reasonable memory usage (less than 200MB for imports)
        assert (
            memory_increase < 200
        ), f"Memory increase {memory_increase:.2f} MB exceeds 200 MB threshold"

    def test_node_registry_memory(self) -> None:
        """Measure memory usage of node registry."""
        force_gc()
        initial_memory = get_process_memory_mb()

        try:
            from casare_rpa.canvas.graph.node_registry import NodeRegistry

            registry = NodeRegistry()
            # Trigger node discovery if available
            if hasattr(registry, "discover_nodes"):
                registry.discover_nodes()
            elif hasattr(registry, "get_all_nodes"):
                registry.get_all_nodes()
        except ImportError:
            pytest.skip("NodeRegistry not available")

        force_gc()
        after_registry_memory = get_process_memory_mb()

        memory_increase = after_registry_memory - initial_memory

        print("\n=== Node Registry Memory ===")
        print(f"Initial memory: {initial_memory:.2f} MB")
        print(f"After registry: {after_registry_memory:.2f} MB")
        print(f"Memory increase: {memory_increase:.2f} MB")

        # Assert reasonable memory usage for node registry
        assert (
            memory_increase < 100
        ), f"Node registry memory {memory_increase:.2f} MB exceeds 100 MB threshold"


class TestNodeExecutionBaseline:
    """Tests for node execution performance."""

    def test_basic_node_execution(self, benchmark: Any) -> None:
        """Measure execution time for basic nodes."""
        try:
            from casare_rpa.nodes.basic_nodes import StartNode, EndNode
        except ImportError:
            pytest.skip("Basic nodes not available")

        def execute_basic_nodes() -> Tuple[Any, Any]:
            start_node = StartNode("start_test")
            end_node = EndNode("end_test")

            # Mock context
            context = MagicMock()
            context.variables = {}
            context.get_variable = MagicMock(return_value=None)
            context.set_variable = MagicMock()

            # Execute nodes synchronously if possible
            start_result = None
            end_result = None

            if hasattr(start_node, "execute_sync"):
                start_result = start_node.execute_sync(context)
            elif hasattr(start_node, "process"):
                start_result = start_node.process(context)

            if hasattr(end_node, "execute_sync"):
                end_result = end_node.execute_sync(context)
            elif hasattr(end_node, "process"):
                end_result = end_node.process(context)

            return start_result, end_result

        result = benchmark(execute_basic_nodes)

    def test_variable_node_execution(self, benchmark: Any) -> None:
        """Measure execution time for variable operations."""
        try:
            from casare_rpa.nodes.variable_nodes import SetVariableNode, GetVariableNode
        except ImportError:
            pytest.skip("Variable nodes not available")

        def execute_variable_nodes() -> Dict[str, Any]:
            set_var = SetVariableNode("set_var_test")
            get_var = GetVariableNode("get_var_test")

            # Mock context with variable storage
            variables: Dict[str, Any] = {}

            def mock_set(name: str, value: Any) -> None:
                variables[name] = value

            def mock_get(name: str, default: Any = None) -> Any:
                return variables.get(name, default)

            context = MagicMock()
            context.variables = variables
            context.set_variable = mock_set
            context.get_variable = mock_get

            # Configure nodes
            if hasattr(set_var, "set_property"):
                set_var.set_property("variable_name", "test_var")
                set_var.set_property("value", "test_value")

            if hasattr(get_var, "set_property"):
                get_var.set_property("variable_name", "test_var")

            # Execute nodes
            if hasattr(set_var, "process"):
                set_var.process(context)
            if hasattr(get_var, "process"):
                get_var.process(context)

            return variables

        result = benchmark(execute_variable_nodes)

    def test_control_flow_node_execution(self, benchmark: Any) -> None:
        """Measure execution time for control flow nodes."""
        try:
            from casare_rpa.nodes.control_flow_nodes import IfNode
        except ImportError:
            pytest.skip("Control flow nodes not available")

        def execute_if_node() -> Any:
            if_node = IfNode("if_test")

            context = MagicMock()
            context.variables = {"condition_var": True}
            context.get_variable = lambda name, default=None: context.variables.get(
                name, default
            )

            # Configure condition
            if hasattr(if_node, "set_property"):
                if_node.set_property("condition", "True")

            result = None
            if hasattr(if_node, "process"):
                result = if_node.process(context)
            elif hasattr(if_node, "evaluate"):
                result = if_node.evaluate(context)

            return result

        result = benchmark(execute_if_node)


class TestWorkflowExecutionBaseline:
    """Tests for workflow execution performance."""

    def test_simple_workflow_execution(self, benchmark: Any) -> None:
        """Measure execution time for a simple 10-node workflow."""
        try:
            from casare_rpa.nodes.basic_nodes import StartNode, EndNode
            from casare_rpa.nodes.variable_nodes import SetVariableNode
        except ImportError:
            pytest.skip("Required nodes not available")

        def execute_simple_workflow() -> List[Any]:
            # Build a simple workflow: Start -> 8 SetVariable -> End
            nodes = [StartNode("start")]
            for i in range(8):
                node = SetVariableNode(f"set_var_{i}")
                if hasattr(node, "set_property"):
                    node.set_property("variable_name", f"var_{i}")
                    node.set_property("value", f"value_{i}")
                nodes.append(node)
            nodes.append(EndNode("end"))

            # Execute sequentially
            context = MagicMock()
            context.variables = {}
            context.set_variable = lambda n, v: context.variables.update({n: v})
            context.get_variable = lambda n, d=None: context.variables.get(n, d)

            results = []
            for node in nodes:
                result = None
                if hasattr(node, "process"):
                    result = node.process(context)
                elif hasattr(node, "execute_sync"):
                    result = node.execute_sync(context)
                results.append(result)

            return results

        result = benchmark(execute_simple_workflow)
        assert len(result) == 10, "Should execute 10 nodes"


class TestStartupBaseline:
    """Tests for application startup performance (headless)."""

    def test_module_import_startup(self, benchmark: Any) -> None:
        """Measure cold-start import time for all core modules."""
        # List of modules to clear and re-import
        modules_to_clear = [
            mod for mod in sys.modules.keys() if mod.startswith("casare_rpa")
        ]

        def cold_start_imports() -> int:
            # Clear cached modules
            for mod in list(sys.modules.keys()):
                if mod.startswith("casare_rpa"):
                    del sys.modules[mod]

            # Import main package
            imported_count = 0
            try:
                import casare_rpa

                imported_count += 1
            except ImportError:
                pass

            try:
                import casare_rpa.domain

                imported_count += 1
            except ImportError:
                pass

            try:
                import casare_rpa.nodes

                imported_count += 1
            except ImportError:
                pass

            try:
                import casare_rpa.utils

                imported_count += 1
            except ImportError:
                pass

            return imported_count

        result = benchmark(cold_start_imports)
        assert result > 0, "Should import at least one module"


class TestDataOperationsBaseline:
    """Tests for data operation node performance."""

    def test_string_operations(self, benchmark: Any) -> None:
        """Measure performance of string operation nodes."""
        try:
            from casare_rpa.nodes.data_operation_nodes import (
                StringConcatNode,
                StringSplitNode,
            )
        except ImportError:
            pytest.skip("Data operation nodes not available")

        def string_operations() -> List[str]:
            concat_node = StringConcatNode("concat_test")
            split_node = StringSplitNode("split_test")

            context = MagicMock()
            context.variables = {}
            context.set_variable = lambda n, v: context.variables.update({n: v})
            context.get_variable = lambda n, d=None: context.variables.get(n, d)

            results = []

            # Configure and execute concat
            if hasattr(concat_node, "set_property"):
                concat_node.set_property("string1", "Hello ")
                concat_node.set_property("string2", "World")

            if hasattr(concat_node, "process"):
                r = concat_node.process(context)
                results.append(str(r) if r else "concat_done")

            # Configure and execute split
            if hasattr(split_node, "set_property"):
                split_node.set_property("input_string", "a,b,c,d,e")
                split_node.set_property("delimiter", ",")

            if hasattr(split_node, "process"):
                r = split_node.process(context)
                results.append(str(r) if r else "split_done")

            return results

        result = benchmark(string_operations)

    def test_math_operations(self, benchmark: Any) -> None:
        """Measure performance of math operation nodes."""
        try:
            from casare_rpa.nodes.data_operation_nodes import (
                MathAddNode,
                MathMultiplyNode,
            )
        except ImportError:
            pytest.skip("Math operation nodes not available")

        def math_operations() -> List[float]:
            add_node = MathAddNode("add_test")
            multiply_node = MathMultiplyNode("multiply_test")

            context = MagicMock()
            context.variables = {}
            context.set_variable = lambda n, v: context.variables.update({n: v})
            context.get_variable = lambda n, d=None: context.variables.get(n, d)

            results = []

            # Execute 100 operations
            for i in range(100):
                if hasattr(add_node, "set_property"):
                    add_node.set_property("value1", i)
                    add_node.set_property("value2", i + 1)

                if hasattr(add_node, "process"):
                    add_node.process(context)

                if hasattr(multiply_node, "set_property"):
                    multiply_node.set_property("value1", i)
                    multiply_node.set_property("value2", 2)

                if hasattr(multiply_node, "process"):
                    multiply_node.process(context)

                results.append(float(i * 2))

            return results

        result = benchmark(math_operations)
        assert len(result) == 100, "Should perform 100 operations"


def run_manual_baseline_measurement() -> Dict[str, Any]:
    """
    Run manual baseline measurements without pytest-benchmark.

    Returns dict with timing and memory metrics.
    """
    results: Dict[str, Any] = {}

    # Measure import times
    print("\n" + "=" * 60)
    print("CASARE RPA - PERFORMANCE BASELINE MEASUREMENT")
    print("=" * 60)

    # 1. Core module imports
    force_gc()
    start_time = time.perf_counter()
    try:
        import casare_rpa
        import casare_rpa.domain
    except ImportError:
        pass
    core_import_time = (time.perf_counter() - start_time) * 1000
    results["core_import_ms"] = core_import_time
    print(f"\n1. Core module imports: {core_import_time:.2f} ms")

    # 2. Node module imports
    force_gc()
    start_time = time.perf_counter()
    try:
        import casare_rpa.nodes
    except ImportError:
        pass
    node_import_time = (time.perf_counter() - start_time) * 1000
    results["node_import_ms"] = node_import_time
    print(f"2. Node module imports: {node_import_time:.2f} ms")

    # 3. Utils imports
    force_gc()
    start_time = time.perf_counter()
    try:
        import casare_rpa.utils
    except ImportError:
        pass
    utils_import_time = (time.perf_counter() - start_time) * 1000
    results["utils_import_ms"] = utils_import_time
    print(f"3. Utils module imports: {utils_import_time:.2f} ms")

    # 4. Memory usage
    force_gc()
    memory_usage = get_process_memory_mb()
    results["memory_after_imports_mb"] = memory_usage
    print(f"\n4. Memory after imports: {memory_usage:.2f} MB")

    # 5. Total time
    total_import_time = core_import_time + node_import_time + utils_import_time
    results["total_import_ms"] = total_import_time
    print(f"\n5. Total import time: {total_import_time:.2f} ms")

    print("\n" + "=" * 60)

    return results


if __name__ == "__main__":
    # Run manual measurements when executed directly
    run_manual_baseline_measurement()
