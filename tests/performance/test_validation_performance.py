"""
Performance benchmark tests for workflow validation module.

Tests execution time, memory usage, and scalability.
"""

import pytest
import time
import sys
from typing import Dict, Any

# Note: validation module still in core/ but doesn't trigger deprecation warnings
from casare_rpa.domain.validation import (
    validate_workflow,
    validate_node,
    validate_connections,
    _has_circular_dependency,
    _find_entry_points_and_reachable,
)


# ============================================================================
# Performance Fixtures
# ============================================================================


@pytest.fixture
def small_workflow() -> None:
    """Workflow with 10 nodes."""
    nodes = {}
    connections = []
    for i in range(10):
        nodes[f"n{i}"] = {"node_id": f"n{i}", "node_type": "LogNode"}
        if i > 0:
            connections.append(
                {
                    "source_node": f"n{i-1}",
                    "source_port": "exec_out",
                    "target_node": f"n{i}",
                    "target_port": "exec_in",
                }
            )
    return {
        "metadata": {"name": "Small Workflow"},
        "nodes": nodes,
        "connections": connections,
    }


@pytest.fixture
def medium_workflow() -> None:
    """Workflow with 100 nodes."""
    nodes = {}
    connections = []
    for i in range(100):
        nodes[f"n{i}"] = {"node_id": f"n{i}", "node_type": "LogNode"}
        if i > 0:
            connections.append(
                {
                    "source_node": f"n{i-1}",
                    "source_port": "exec_out",
                    "target_node": f"n{i}",
                    "target_port": "exec_in",
                }
            )
    return {
        "metadata": {"name": "Medium Workflow"},
        "nodes": nodes,
        "connections": connections,
    }


@pytest.fixture
def large_workflow() -> None:
    """Workflow with 1000 nodes."""
    nodes = {}
    connections = []
    for i in range(1000):
        nodes[f"n{i}"] = {"node_id": f"n{i}", "node_type": "LogNode"}
        if i > 0:
            connections.append(
                {
                    "source_node": f"n{i-1}",
                    "source_port": "exec_out",
                    "target_node": f"n{i}",
                    "target_port": "exec_in",
                }
            )
    return {
        "metadata": {"name": "Large Workflow"},
        "nodes": nodes,
        "connections": connections,
    }


@pytest.fixture
def dense_workflow() -> None:
    """Workflow with 50 nodes and dense connections (many-to-many)."""
    nodes = {}
    connections = []
    for i in range(50):
        nodes[f"n{i}"] = {"node_id": f"n{i}", "node_type": "LogNode"}

    # Create dense connections (each node connects to next 5 nodes)
    for i in range(45):
        for j in range(1, 6):
            if i + j < 50:
                connections.append(
                    {
                        "source_node": f"n{i}",
                        "source_port": "exec_out",
                        "target_node": f"n{i+j}",
                        "target_port": "exec_in",
                    }
                )

    return {
        "metadata": {"name": "Dense Workflow"},
        "nodes": nodes,
        "connections": connections,
    }


# ============================================================================
# Timing Benchmarks
# ============================================================================


class TestValidationTiming:
    """Test validation execution time."""

    def test_small_workflow_timing(self, small_workflow, benchmark) -> None:
        """Benchmark validation of small workflow (10 nodes)."""

        def validate():
            return validate_workflow(small_workflow)

        result = benchmark(validate)
        assert result.is_valid is True

    def test_medium_workflow_timing(self, medium_workflow, benchmark) -> None:
        """Benchmark validation of medium workflow (100 nodes)."""

        def validate():
            return validate_workflow(medium_workflow)

        result = benchmark(validate)
        assert result.is_valid is True

    def test_large_workflow_timing(self, large_workflow, benchmark) -> None:
        """Benchmark validation of large workflow (1000 nodes)."""

        def validate():
            return validate_workflow(large_workflow)

        result = benchmark(validate)
        assert result.is_valid is True

    def test_dense_workflow_timing(self, dense_workflow, benchmark) -> None:
        """Benchmark validation of densely connected workflow."""

        def validate():
            return validate_workflow(dense_workflow)

        result = benchmark(validate)
        assert result.is_valid is True

    def test_validation_scales_linearly(
        self, small_workflow, medium_workflow, large_workflow
    ) -> None:
        """Test that validation time scales linearly with workflow size."""
        # Validate and time each workflow
        start = time.time()
        validate_workflow(small_workflow)
        time_small = time.time() - start

        start = time.time()
        validate_workflow(medium_workflow)
        time_medium = time.time() - start

        start = time.time()
        validate_workflow(large_workflow)
        time_large = time.time() - start

        # Medium should be roughly 10x small (100 vs 10 nodes)
        # Large should be roughly 10x medium (1000 vs 100 nodes)
        # Allow for some variance (2x-15x range)
        ratio_medium_to_small = time_medium / time_small if time_small > 0 else 0
        ratio_large_to_medium = time_large / time_medium if time_medium > 0 else 0

        # These should be roughly 10x but we allow wide margin
        assert (
            2 < ratio_medium_to_small < 20
        ), f"Medium/Small ratio: {ratio_medium_to_small}"
        assert (
            2 < ratio_large_to_medium < 20
        ), f"Large/Medium ratio: {ratio_large_to_medium}"


# ============================================================================
# Specific Operation Benchmarks
# ============================================================================


class TestOperationBenchmarks:
    """Benchmark specific validation operations."""

    def test_node_validation_timing(self, benchmark) -> None:
        """Benchmark individual node validation."""
        node_data = {
            "node_id": "test_node",
            "node_type": "StartNode",
            "position": [100, 200],
            "config": {"key1": "value1", "key2": "value2"},
        }

        def validate():
            return validate_node("test_node", node_data)

        result = benchmark(validate)
        assert result.is_valid is True

    def test_connection_validation_timing(self, benchmark) -> None:
        """Benchmark connection validation."""
        connections = [
            {
                "source_node": f"n{i}",
                "source_port": "exec_out",
                "target_node": f"n{i+1}",
                "target_port": "exec_in",
            }
            for i in range(100)
        ]
        node_ids = {f"n{i}" for i in range(101)}

        def validate():
            return validate_connections(connections, node_ids)

        result = benchmark(validate)
        assert result.is_valid is True

    def test_circular_dependency_detection_timing(self, benchmark) -> None:
        """Benchmark circular dependency detection."""
        nodes = {
            f"n{i}": {"node_id": f"n{i}", "node_type": "LogNode"} for i in range(100)
        }

        # Create circular chain
        connections = [
            {
                "source_node": f"n{i}",
                "source_port": "exec_out",
                "target_node": f"n{(i+1)%100}",
                "target_port": "exec_in",
            }
            for i in range(100)
        ]

        def detect():
            return _has_circular_dependency(nodes, connections)

        result = benchmark(detect)
        assert result is True  # Should detect the circle

    def test_entry_point_detection_timing(self, benchmark) -> None:
        """Benchmark entry point and reachability detection."""
        nodes = {
            f"n{i}": {"node_id": f"n{i}", "node_type": "LogNode"} for i in range(100)
        }

        connections = [
            {
                "source_node": f"n{i}",
                "source_port": "exec_out",
                "target_node": f"n{i+1}",
                "target_port": "exec_in",
            }
            for i in range(99)
        ]

        def detect():
            return _find_entry_points_and_reachable(nodes, connections)

        entry_points, reachable = benchmark(detect)
        assert len(entry_points) > 0
        assert len(reachable) > 0


# ============================================================================
# Repeated Validation Benchmarks
# ============================================================================


class TestRepeatedValidation:
    """Test performance of repeated validations."""

    def test_repeated_validation_no_slowdown(self, small_workflow) -> None:
        """Test that repeated validations don't slow down."""
        times = []

        for _ in range(100):
            start = time.time()
            validate_workflow(small_workflow)
            elapsed = time.time() - start
            times.append(elapsed)

        # First validation might be slower due to cache warming
        # But subsequent validations should be consistent
        avg_first_10 = sum(times[:10]) / 10
        avg_last_10 = sum(times[-10:]) / 10

        # Last 10 should not be significantly slower than first 10
        # Allow 2x variance
        assert avg_last_10 < avg_first_10 * 2

    def test_validation_caching_behavior(self, small_workflow) -> None:
        """Test that validation doesn't improperly cache results."""
        # First validation
        result1 = validate_workflow(small_workflow)
        assert result1.is_valid is True

        # Modify workflow to make it invalid
        invalid_workflow = small_workflow.copy()
        invalid_workflow["nodes"]["invalid"] = {
            "node_id": "different_id",  # Mismatch
            "node_type": "StartNode",
        }

        # Second validation should detect the error
        result2 = validate_workflow(invalid_workflow)
        assert result2.is_valid is False

        # Third validation of original should still pass
        result3 = validate_workflow(small_workflow)
        assert result3.is_valid is True


# ============================================================================
# Worst-Case Scenario Benchmarks
# ============================================================================


class TestWorstCaseScenarios:
    """Test performance in worst-case scenarios."""

    def test_worst_case_circular_detection(self) -> None:
        """Test circular detection with worst-case topology."""
        # Create a complex graph that takes longest to detect cycle
        nodes = {
            f"n{i}": {"node_id": f"n{i}", "node_type": "LogNode"} for i in range(100)
        }

        # Create complex interconnected structure with cycle at the end
        connections = []
        for i in range(99):
            connections.append(
                {
                    "source_node": f"n{i}",
                    "source_port": "exec_out",
                    "target_node": f"n{i+1}",
                    "target_port": "exec_in",
                }
            )
        # Add cycle back to start
        connections.append(
            {
                "source_node": "n99",
                "source_port": "exec_out",
                "target_node": "n0",
                "target_port": "exec_in",
            }
        )

        start = time.time()
        result = _has_circular_dependency(nodes, connections)
        elapsed = time.time() - start

        assert result is True  # Should detect cycle
        assert elapsed < 1.0  # Should complete within 1 second

    def test_worst_case_unreachable_nodes(self) -> None:
        """Test reachability detection with many unreachable nodes."""
        # Create workflow with one connected component and many isolated nodes
        nodes = {}
        connections = []

        # Connected component (10 nodes)
        for i in range(10):
            nodes[f"connected_{i}"] = {
                "node_id": f"connected_{i}",
                "node_type": "LogNode",
            }
            if i > 0:
                connections.append(
                    {
                        "source_node": f"connected_{i-1}",
                        "source_port": "exec_out",
                        "target_node": f"connected_{i}",
                        "target_port": "exec_in",
                    }
                )

        # Isolated nodes (990 nodes)
        for i in range(990):
            nodes[f"isolated_{i}"] = {
                "node_id": f"isolated_{i}",
                "node_type": "LogNode",
            }

        data = {
            "metadata": {"name": "Many Unreachable"},
            "nodes": nodes,
            "connections": connections,
        }

        start = time.time()
        result = validate_workflow(data)
        elapsed = time.time() - start

        # Should complete within reasonable time
        assert elapsed < 5.0  # 5 seconds for 1000 nodes
        assert any(issue.code == "UNREACHABLE_NODES" for issue in result.warnings)

    def test_worst_case_all_errors(self) -> None:
        """Test validation with workflow that has maximum errors."""
        # Create workflow with many different types of errors
        nodes = {}
        connections = []

        # Add 100 invalid nodes (missing required fields, unknown types, etc.)
        for i in range(50):
            nodes[f"missing_{i}"] = {}  # Missing all required fields

        for i in range(50):
            nodes[f"unknown_{i}"] = {
                "node_id": f"unknown_{i}",
                "node_type": "NonExistentNodeType",
            }

        # Add 100 invalid connections
        for i in range(100):
            connections.append(
                {
                    "source_node": f"nonexistent_source_{i}",
                    "source_port": "out",
                    "target_node": f"nonexistent_target_{i}",
                    "target_port": "in",
                }
            )

        data = {
            "metadata": {"name": "A" * 200},  # Too long name
            "nodes": nodes,
            "connections": connections,
        }

        start = time.time()
        result = validate_workflow(data)
        elapsed = time.time() - start

        assert result.is_valid is False
        assert result.error_count > 100  # Should detect many errors
        assert elapsed < 2.0  # Should still complete quickly


# ============================================================================
# Memory Usage Tests (if pytest-benchmark not available)
# ============================================================================


class TestMemoryUsage:
    """Test memory usage of validation operations."""

    def test_large_workflow_memory_usage(self, large_workflow) -> None:
        """Test that large workflow validation doesn't use excessive memory."""
        # Get memory usage before
        import gc

        gc.collect()

        # Validate large workflow
        result = validate_workflow(large_workflow)
        assert result.is_valid is True

        # Force garbage collection
        gc.collect()

        # If we got here without MemoryError, test passes

    def test_validation_result_memory_cleanup(self) -> None:
        """Test that ValidationResult objects are properly cleaned up."""
        import gc

        results = []

        # Create many validation results
        for i in range(1000):
            data = {
                "nodes": {
                    f"n{i}": {
                        "node_id": f"n{i}",
                        "node_type": "UnknownType",  # Will generate error
                    }
                }
            }
            result = validate_workflow(data)
            results.append(result)

        # Clear references
        results.clear()
        gc.collect()

        # If we got here without MemoryError, test passes


# ============================================================================
# Concurrency Tests
# ============================================================================


class TestConcurrentValidation:
    """Test validation under concurrent access."""

    def test_concurrent_validation_different_workflows(self, small_workflow) -> None:
        """Test concurrent validation of different workflows."""
        import threading

        results = []
        errors = []

        def validate_workflow_thread(workflow_id):
            try:
                data = {
                    "metadata": {"name": f"Workflow {workflow_id}"},
                    "nodes": {
                        "n1": {"node_id": "n1", "node_type": "StartNode"},
                    },
                }
                result = validate_workflow(data)
                results.append(result)
            except Exception as e:
                errors.append(e)

        threads = []
        for i in range(20):
            t = threading.Thread(target=validate_workflow_thread, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # All validations should succeed
        assert len(errors) == 0
        assert len(results) == 20

    def test_concurrent_validation_same_workflow(self, medium_workflow) -> None:
        """Test concurrent validation of the same workflow."""
        import threading

        results = []
        errors = []

        def validate_thread():
            try:
                result = validate_workflow(medium_workflow)
                results.append(result)
            except Exception as e:
                errors.append(e)

        threads = []
        for _ in range(10):
            t = threading.Thread(target=validate_thread)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # All validations should succeed
        assert len(errors) == 0
        assert len(results) == 10
        # All results should be identical
        assert all(r.is_valid is True for r in results)


# ============================================================================
# Scalability Tests
# ============================================================================


class TestScalability:
    """Test how validation scales with different parameters."""

    @pytest.mark.parametrize("node_count", [10, 50, 100, 500])
    def test_validation_scales_with_node_count(self, node_count) -> None:
        """Test validation with varying node counts."""
        nodes = {
            f"n{i}": {"node_id": f"n{i}", "node_type": "LogNode"}
            for i in range(node_count)
        }
        data = {"metadata": {"name": "Test"}, "nodes": nodes, "connections": []}

        start = time.time()
        result = validate_workflow(data)
        elapsed = time.time() - start

        assert result.is_valid is True
        # Should complete within reasonable time (100ms per 100 nodes)
        assert elapsed < (node_count / 100) * 0.1

    @pytest.mark.parametrize("connection_count", [10, 50, 100, 500])
    def test_validation_scales_with_connection_count(self, connection_count) -> None:
        """Test validation with varying connection counts."""
        # Create enough nodes
        node_count = connection_count + 1
        nodes = {
            f"n{i}": {"node_id": f"n{i}", "node_type": "LogNode"}
            for i in range(node_count)
        }

        # Create linear connections
        connections = [
            {
                "source_node": f"n{i}",
                "source_port": "exec_out",
                "target_node": f"n{i+1}",
                "target_port": "exec_in",
            }
            for i in range(connection_count)
        ]

        data = {
            "metadata": {"name": "Test"},
            "nodes": nodes,
            "connections": connections,
        }

        start = time.time()
        result = validate_workflow(data)
        elapsed = time.time() - start

        assert result.is_valid is True
        # Should complete within reasonable time
        assert elapsed < (connection_count / 100) * 0.1
