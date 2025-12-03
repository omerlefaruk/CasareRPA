"""
Workflow execution performance benchmarks.

Tests workflow execution time scaling with node count.
Establishes regression thresholds for 10, 50, and 100 node workflows.

Thresholds:
- 10 nodes: < 500ms
- 50 nodes: < 1.5s
- 100 nodes: < 3s

Run: pytest tests/performance/test_workflow_execution_perf.py -v
Benchmark: pytest tests/performance/test_workflow_execution_perf.py -v --benchmark-compare
"""

import asyncio
import time
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, AsyncMock

import pytest

from casare_rpa.domain.entities.workflow import WorkflowSchema
from casare_rpa.domain.entities.workflow_metadata import WorkflowMetadata
from casare_rpa.domain.entities.node_connection import NodeConnection
from casare_rpa.nodes.basic_nodes import StartNode, EndNode
from casare_rpa.nodes.variable_nodes import SetVariableNode


# --- Performance Thresholds ---
THRESHOLD_10_NODES_MS = 500
THRESHOLD_50_NODES_MS = 1500
THRESHOLD_100_NODES_MS = 3000


def create_workflow_with_n_nodes(n: int) -> Dict[str, Any]:
    """
    Create workflow data with n SetVariable nodes.

    Structure: Start -> [SetVariable * n] -> End
    Total nodes: n + 2 (Start + End)

    Args:
        n: Number of SetVariable nodes

    Returns:
        Workflow dict suitable for WorkflowSchema.from_dict()
    """
    nodes: Dict[str, Any] = {}
    connections: List[Dict[str, str]] = []

    # Start node
    start_id = "start_node"
    nodes[start_id] = {
        "node_id": start_id,
        "node_type": "StartNode",
        "name": "Start",
        "position": [0, 0],
        "config": {},
    }

    prev_id = start_id
    prev_port = "exec_out"

    # n SetVariable nodes
    for i in range(n):
        node_id = f"set_var_{i}"
        nodes[node_id] = {
            "node_id": node_id,
            "node_type": "SetVariableNode",
            "name": f"Set Variable {i}",
            "position": [(i + 1) * 100, 0],
            "config": {
                "variable_name": f"var_{i}",
                "default_value": i,
                "variable_type": "Int32",
            },
        }

        connections.append(
            {
                "source_node": prev_id,
                "source_port": prev_port,
                "target_node": node_id,
                "target_port": "exec_in",
            }
        )

        prev_id = node_id
        prev_port = "exec_out"

    # End node
    end_id = "end_node"
    nodes[end_id] = {
        "node_id": end_id,
        "node_type": "EndNode",
        "name": "End",
        "position": [(n + 1) * 100, 0],
        "config": {},
    }

    connections.append(
        {
            "source_node": prev_id,
            "source_port": prev_port,
            "target_node": end_id,
            "target_port": "exec_in",
        }
    )

    return {
        "metadata": {
            "name": f"Benchmark {n}-Node Workflow",
            "version": "1.0.0",
            "description": f"Performance test workflow with {n} nodes",
        },
        "nodes": nodes,
        "connections": connections,
        "frames": [],
        "variables": {},
        "settings": {"stop_on_error": True, "timeout": 300, "retry_count": 0},
    }


def create_mock_context() -> MagicMock:
    """Create mock execution context with variable storage."""
    context = MagicMock()
    context.variables = {}
    context.get_variable = lambda name, default=None: context.variables.get(
        name, default
    )
    context.set_variable = lambda name, value: context.variables.__setitem__(
        name, value
    )
    context.has_variable = lambda name: name in context.variables
    context.resolve_value = lambda x: x
    context.get_execution_summary = lambda: {
        "workflow_name": "Test Workflow",
        "nodes_executed": len(context.variables),
        "errors": [],
        "duration_ms": 0,
    }
    return context


def instantiate_nodes(workflow_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create node instances from workflow data."""
    nodes = {}
    for node_id, node_data in workflow_data["nodes"].items():
        node_type = node_data["node_type"]
        config = node_data.get("config", {})

        if node_type == "StartNode":
            nodes[node_id] = StartNode(node_id)
        elif node_type == "EndNode":
            nodes[node_id] = EndNode(node_id)
        elif node_type == "SetVariableNode":
            nodes[node_id] = SetVariableNode(node_id, config=config)

    return nodes


def build_execution_order(workflow_data: Dict[str, Any]) -> tuple[str, Dict[str, str]]:
    """
    Build execution order from workflow connections.

    Returns:
        Tuple of (start_node_id, connection_map)
    """
    connection_map = {}
    for conn in workflow_data["connections"]:
        connection_map[conn["source_node"]] = conn["target_node"]

    start_id = None
    for node_id, node_data in workflow_data["nodes"].items():
        if node_data["node_type"] == "StartNode":
            start_id = node_id
            break

    return start_id, connection_map


async def execute_workflow_nodes(
    nodes: Dict[str, Any],
    start_id: str,
    connection_map: Dict[str, str],
    context: MagicMock,
) -> int:
    """
    Execute workflow nodes in order.

    Returns:
        Number of nodes executed
    """
    current_id: Optional[str] = start_id
    executed_count = 0

    while current_id and current_id in nodes:
        node = nodes[current_id]
        await node.execute(context)
        executed_count += 1
        current_id = connection_map.get(current_id)

    return executed_count


class TestWorkflowExecutionPerformance:
    """Performance tests for workflow execution at various scales."""

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_10_node_workflow_under_threshold(self) -> None:
        """10-node workflow execution must complete under 500ms."""
        workflow_data = create_workflow_with_n_nodes(10)
        nodes = instantiate_nodes(workflow_data)
        start_id, connection_map = build_execution_order(workflow_data)
        context = create_mock_context()

        start = time.perf_counter()
        executed = await execute_workflow_nodes(
            nodes, start_id, connection_map, context
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert executed == 12, f"Expected 12 nodes (10 + Start + End), got {executed}"
        assert elapsed_ms < THRESHOLD_10_NODES_MS, (
            f"10-node workflow took {elapsed_ms:.2f}ms "
            f"(threshold: {THRESHOLD_10_NODES_MS}ms)"
        )

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_50_node_workflow_under_threshold(self) -> None:
        """50-node workflow execution must complete under 1.5s."""
        workflow_data = create_workflow_with_n_nodes(50)
        nodes = instantiate_nodes(workflow_data)
        start_id, connection_map = build_execution_order(workflow_data)
        context = create_mock_context()

        start = time.perf_counter()
        executed = await execute_workflow_nodes(
            nodes, start_id, connection_map, context
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert executed == 52, f"Expected 52 nodes, got {executed}"
        assert elapsed_ms < THRESHOLD_50_NODES_MS, (
            f"50-node workflow took {elapsed_ms:.2f}ms "
            f"(threshold: {THRESHOLD_50_NODES_MS}ms)"
        )

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_100_node_workflow_under_threshold(self) -> None:
        """100-node workflow execution must complete under 3s."""
        workflow_data = create_workflow_with_n_nodes(100)
        nodes = instantiate_nodes(workflow_data)
        start_id, connection_map = build_execution_order(workflow_data)
        context = create_mock_context()

        start = time.perf_counter()
        executed = await execute_workflow_nodes(
            nodes, start_id, connection_map, context
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert executed == 102, f"Expected 102 nodes, got {executed}"
        assert elapsed_ms < THRESHOLD_100_NODES_MS, (
            f"100-node workflow took {elapsed_ms:.2f}ms "
            f"(threshold: {THRESHOLD_100_NODES_MS}ms)"
        )

    @pytest.mark.slow
    def test_10_node_workflow_benchmark(self, benchmark) -> None:
        """Benchmark 10-node workflow execution."""
        workflow_data = create_workflow_with_n_nodes(10)

        def run_workflow():
            nodes = instantiate_nodes(workflow_data)
            start_id, connection_map = build_execution_order(workflow_data)
            context = create_mock_context()

            loop = asyncio.new_event_loop()
            try:
                executed = loop.run_until_complete(
                    execute_workflow_nodes(nodes, start_id, connection_map, context)
                )
            finally:
                loop.close()

            return executed

        result = benchmark(run_workflow)
        assert result == 12

        # Verify median under threshold
        median_ms = benchmark.stats.stats.median * 1000
        assert (
            median_ms < THRESHOLD_10_NODES_MS
        ), f"Median {median_ms:.2f}ms exceeds {THRESHOLD_10_NODES_MS}ms"

    @pytest.mark.slow
    def test_50_node_workflow_benchmark(self, benchmark) -> None:
        """Benchmark 50-node workflow execution."""
        workflow_data = create_workflow_with_n_nodes(50)

        def run_workflow():
            nodes = instantiate_nodes(workflow_data)
            start_id, connection_map = build_execution_order(workflow_data)
            context = create_mock_context()

            loop = asyncio.new_event_loop()
            try:
                executed = loop.run_until_complete(
                    execute_workflow_nodes(nodes, start_id, connection_map, context)
                )
            finally:
                loop.close()

            return executed

        result = benchmark(run_workflow)
        assert result == 52

        median_ms = benchmark.stats.stats.median * 1000
        assert (
            median_ms < THRESHOLD_50_NODES_MS
        ), f"Median {median_ms:.2f}ms exceeds {THRESHOLD_50_NODES_MS}ms"

    @pytest.mark.slow
    def test_100_node_workflow_benchmark(self, benchmark) -> None:
        """Benchmark 100-node workflow execution."""
        workflow_data = create_workflow_with_n_nodes(100)

        def run_workflow():
            nodes = instantiate_nodes(workflow_data)
            start_id, connection_map = build_execution_order(workflow_data)
            context = create_mock_context()

            loop = asyncio.new_event_loop()
            try:
                executed = loop.run_until_complete(
                    execute_workflow_nodes(nodes, start_id, connection_map, context)
                )
            finally:
                loop.close()

            return executed

        result = benchmark(run_workflow)
        assert result == 102

        median_ms = benchmark.stats.stats.median * 1000
        assert (
            median_ms < THRESHOLD_100_NODES_MS
        ), f"Median {median_ms:.2f}ms exceeds {THRESHOLD_100_NODES_MS}ms"


class TestWorkflowExecutionScaling:
    """Tests for execution time scaling characteristics."""

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_execution_scales_linearly(self) -> None:
        """Verify execution time scales linearly with node count."""
        sizes = [10, 25, 50, 100]
        timings = []

        for size in sizes:
            workflow_data = create_workflow_with_n_nodes(size)
            nodes = instantiate_nodes(workflow_data)
            start_id, connection_map = build_execution_order(workflow_data)
            context = create_mock_context()

            start = time.perf_counter()
            await execute_workflow_nodes(nodes, start_id, connection_map, context)
            elapsed = time.perf_counter() - start

            timings.append((size, elapsed))

        # Check linear scaling (time ratio close to size ratio)
        for i in range(1, len(timings)):
            prev_size, prev_time = timings[i - 1]
            curr_size, curr_time = timings[i]

            size_ratio = curr_size / prev_size
            time_ratio = curr_time / prev_time if prev_time > 0.001 else 1.0

            # Allow 3x tolerance for system variance
            assert time_ratio < size_ratio * 3, (
                f"Non-linear scaling: size {size_ratio:.1f}x, time {time_ratio:.1f}x "
                f"({prev_size}->{curr_size} nodes)"
            )

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_per_node_overhead_under_1ms(self) -> None:
        """Per-node execution overhead should be under 1ms."""
        iterations = 500
        context = create_mock_context()

        start = time.perf_counter()
        for i in range(iterations):
            node = SetVariableNode(
                f"node_{i}",
                config={"variable_name": f"var_{i}", "default_value": i},
            )
            await node.execute(context)
        elapsed = time.perf_counter() - start

        avg_ms = (elapsed / iterations) * 1000
        assert avg_ms < 1.0, f"Per-node overhead {avg_ms:.3f}ms exceeds 1ms threshold"

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_repeated_execution_stable_timing(self) -> None:
        """Repeated workflow execution should have stable timing."""
        workflow_data = create_workflow_with_n_nodes(50)
        timings = []

        for _ in range(10):
            nodes = instantiate_nodes(workflow_data)
            start_id, connection_map = build_execution_order(workflow_data)
            context = create_mock_context()

            start = time.perf_counter()
            await execute_workflow_nodes(nodes, start_id, connection_map, context)
            elapsed = time.perf_counter() - start
            timings.append(elapsed)

        # Calculate variance
        avg = sum(timings) / len(timings)
        variance = sum((t - avg) ** 2 for t in timings) / len(timings)
        std_dev = variance**0.5

        # Coefficient of variation should be < 50%
        cv = (std_dev / avg) * 100 if avg > 0 else 0
        assert cv < 50, f"Timing too variable: CV={cv:.1f}% (std={std_dev*1000:.2f}ms)"


class TestWorkflowExecutionVariableScaling:
    """Tests for execution scaling with variable operations."""

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_many_variables_no_slowdown(self) -> None:
        """Setting many variables should not cause significant slowdown."""
        # Pre-populate context with 1000 variables
        context = create_mock_context()
        for i in range(1000):
            context.variables[f"existing_var_{i}"] = i

        workflow_data = create_workflow_with_n_nodes(50)
        nodes = instantiate_nodes(workflow_data)
        start_id, connection_map = build_execution_order(workflow_data)

        start = time.perf_counter()
        await execute_workflow_nodes(nodes, start_id, connection_map, context)
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Should still be under threshold despite pre-populated variables
        assert (
            elapsed_ms < THRESHOLD_50_NODES_MS * 1.5
        ), f"Execution with 1000 pre-existing vars took {elapsed_ms:.2f}ms"

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_variable_lookup_performance(self) -> None:
        """Variable lookup should be O(1) in execution context."""
        context = create_mock_context()

        # Add many variables
        for i in range(10000):
            context.variables[f"var_{i}"] = i

        # Time lookups
        iterations = 10000
        start = time.perf_counter()
        for i in range(iterations):
            _ = context.get_variable(f"var_{i % 10000}")
        elapsed = time.perf_counter() - start

        avg_ns = (elapsed / iterations) * 1_000_000_000
        # Dict lookup should be < 1 microsecond
        assert avg_ns < 1000, f"Variable lookup {avg_ns:.0f}ns exceeds 1us threshold"
