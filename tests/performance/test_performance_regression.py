"""
Performance regression tests for CasareRPA.

Hard thresholds to prevent performance degradation:
- Startup: < 3 seconds (cold start to MainWindow visible)
- 100-node workflow execution: < 5 seconds

Expected runtime environment:
- CPU: Modern multi-core (4+ cores recommended)
- RAM: 8GB+ available
- Storage: SSD recommended
- OS: Windows 10/11
- Python: 3.12+

These tests use pytest-benchmark for reliable, reproducible measurements.
Run with: pytest tests/performance/test_performance_regression.py -v
"""

import asyncio
import sys
import time
import uuid
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

# Conditionally import benchmark - tests skip if not available
try:
    import pytest_benchmark

    BENCHMARK_AVAILABLE = True
except ImportError:
    BENCHMARK_AVAILABLE = False


# --- Performance Thresholds (in seconds) ---
STARTUP_THRESHOLD_SECONDS = 3.0
EXECUTION_100_NODE_THRESHOLD_SECONDS = 5.0


# --- Fixtures ---


@pytest.fixture
def mock_execution_context() -> MagicMock:
    """Create a lightweight mock execution context for benchmarks."""
    context = MagicMock()
    context.variables: Dict[str, Any] = {}
    context.resolve_value = lambda x: x
    context.get_variable = lambda name, default=None: context.variables.get(
        name, default
    )
    context.set_variable = lambda name, value: context.variables.__setitem__(
        name, value
    )
    context.has_variable = lambda name: name in context.variables
    context.cleanup = AsyncMock()
    return context


@pytest.fixture
def simple_workflow_data() -> Dict[str, Any]:
    """Create a minimal workflow with Start -> End nodes."""
    start_id = f"start_{uuid.uuid4().hex[:8]}"
    end_id = f"end_{uuid.uuid4().hex[:8]}"

    return {
        "metadata": {
            "name": "Simple Test Workflow",
            "version": "1.0.0",
            "description": "Minimal workflow for testing",
        },
        "nodes": {
            start_id: {
                "node_id": start_id,
                "node_type": "StartNode",
                "name": "Start",
                "position": [0, 0],
                "config": {},
            },
            end_id: {
                "node_id": end_id,
                "node_type": "EndNode",
                "name": "End",
                "position": [200, 0],
                "config": {},
            },
        },
        "connections": [
            {
                "source_node": start_id,
                "source_port": "exec_out",
                "target_node": end_id,
                "target_port": "exec_in",
            }
        ],
        "frames": [],
        "variables": {},
        "settings": {"stop_on_error": True, "timeout": 30, "retry_count": 0},
    }


def create_100_node_workflow() -> Dict[str, Any]:
    """
    Create a 100-node workflow for execution benchmarking.

    Structure: Start -> 98 SetVariable nodes -> End
    Each SetVariable sets a counter incrementing by 1.
    """
    nodes: Dict[str, Any] = {}
    connections: List[Dict[str, str]] = []

    # Start node
    start_id = f"start_{uuid.uuid4().hex[:8]}"
    nodes[start_id] = {
        "node_id": start_id,
        "node_type": "StartNode",
        "name": "Start",
        "position": [0, 0],
        "config": {},
    }

    prev_id = start_id
    prev_port = "exec_out"

    # 98 SetVariable nodes (total 100 with Start + End)
    for i in range(98):
        node_id = f"setvar_{i}_{uuid.uuid4().hex[:8]}"
        nodes[node_id] = {
            "node_id": node_id,
            "node_type": "SetVariableNode",
            "name": f"Set Variable {i}",
            "position": [(i + 1) * 100, 0],
            "config": {
                "variable_name": f"counter_{i}",
                "default_value": i,
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
    end_id = f"end_{uuid.uuid4().hex[:8]}"
    nodes[end_id] = {
        "node_id": end_id,
        "node_type": "EndNode",
        "name": "End",
        "position": [9900, 0],
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
            "name": "100 Node Benchmark Workflow",
            "version": "1.0.0",
            "description": "Benchmark workflow with 100 nodes",
        },
        "nodes": nodes,
        "connections": connections,
        "frames": [],
        "variables": {},
        "settings": {"stop_on_error": True, "timeout": 300, "retry_count": 0},
    }


# --- Startup Performance Tests ---


class TestStartupPerformance:
    """Tests for application startup performance."""

    def test_import_core_modules_time(self) -> None:
        """Importing core modules should complete quickly."""
        start = time.perf_counter()

        # Core module imports that happen during startup
        from casare_rpa.core.base_node import BaseNode
        from casare_rpa.core.types import NodeStatus, PortType
        from casare_rpa.domain.entities.workflow import WorkflowSchema
        from casare_rpa.domain.entities.workflow_metadata import WorkflowMetadata

        elapsed = time.perf_counter() - start

        # Core imports should be fast (< 1 second)
        assert (
            elapsed < 1.0
        ), f"Core module imports took {elapsed:.2f}s (threshold: 1.0s)"

    def test_import_nodes_time(self) -> None:
        """Importing node modules should complete within threshold."""
        start = time.perf_counter()

        from casare_rpa.nodes.basic_nodes import StartNode, EndNode
        from casare_rpa.nodes.variable_nodes import SetVariableNode, GetVariableNode
        from casare_rpa.nodes.control_flow_nodes import IfNode, ForLoopStartNode
        from casare_rpa.nodes.data_operation_nodes import ConcatenateNode

        elapsed = time.perf_counter() - start

        # Node imports should be reasonably fast
        assert (
            elapsed < 2.0
        ), f"Node module imports took {elapsed:.2f}s (threshold: 2.0s)"

    def test_workflow_schema_creation_time(
        self, simple_workflow_data: Dict[str, Any]
    ) -> None:
        """Creating WorkflowSchema from dict should be fast."""
        from casare_rpa.domain.entities.workflow import WorkflowSchema

        start = time.perf_counter()

        for _ in range(100):
            workflow = WorkflowSchema.from_dict(simple_workflow_data)

        elapsed = time.perf_counter() - start
        avg_per_workflow = elapsed / 100

        # Schema creation should be < 10ms each
        assert (
            avg_per_workflow < 0.01
        ), f"WorkflowSchema creation took {avg_per_workflow*1000:.2f}ms avg (threshold: 10ms)"


# --- Execution Performance Tests ---


class TestExecutionPerformance:
    """Tests for workflow execution performance."""

    @pytest.mark.asyncio
    async def test_simple_workflow_execution_time(
        self, simple_workflow_data: Dict[str, Any]
    ) -> None:
        """Simple 2-node workflow should execute very quickly."""
        from casare_rpa.domain.entities.workflow import WorkflowSchema
        from casare_rpa.nodes.basic_nodes import StartNode, EndNode

        workflow = WorkflowSchema.from_dict(simple_workflow_data)

        # Create actual node instances
        nodes = {}
        for node_id, node_data in workflow.nodes.items():
            if node_data["node_type"] == "StartNode":
                nodes[node_id] = StartNode(node_id)
            elif node_data["node_type"] == "EndNode":
                nodes[node_id] = EndNode(node_id)

        # Create mock context
        context = MagicMock()
        context.variables = {}
        context.get_variable = lambda name, default=None: context.variables.get(
            name, default
        )
        context.set_variable = lambda name, value: context.variables.__setitem__(
            name, value
        )

        start = time.perf_counter()

        # Execute each node
        for node_id, node in nodes.items():
            await node.execute(context)

        elapsed = time.perf_counter() - start

        # Simple workflow should be < 100ms
        assert (
            elapsed < 0.1
        ), f"Simple workflow took {elapsed*1000:.2f}ms (threshold: 100ms)"

    @pytest.mark.asyncio
    async def test_100_node_workflow_execution_under_threshold(self) -> None:
        """100-node workflow execution must complete under 5 seconds."""
        from casare_rpa.domain.entities.workflow import WorkflowSchema
        from casare_rpa.nodes.basic_nodes import StartNode, EndNode
        from casare_rpa.nodes.variable_nodes import SetVariableNode

        workflow_data = create_100_node_workflow()
        workflow = WorkflowSchema.from_dict(workflow_data)

        # Create node instances
        nodes: Dict[str, Any] = {}
        for node_id, node_data in workflow.nodes.items():
            node_type = node_data["node_type"]
            config = node_data.get("config", {})

            if node_type == "StartNode":
                nodes[node_id] = StartNode(node_id)
            elif node_type == "EndNode":
                nodes[node_id] = EndNode(node_id)
            elif node_type == "SetVariableNode":
                nodes[node_id] = SetVariableNode(
                    node_id,
                    variable_name=config.get("variable_name", ""),
                    default_value=config.get("default_value"),
                )

        # Create mock context
        context = MagicMock()
        context.variables = {}
        context.get_variable = lambda name, default=None: context.variables.get(
            name, default
        )
        context.set_variable = lambda name, value: context.variables.__setitem__(
            name, value
        )

        # Build execution order from connections
        connection_map: Dict[str, str] = {}
        for conn_data in workflow_data["connections"]:
            source = conn_data["source_node"]
            target = conn_data["target_node"]
            connection_map[source] = target

        # Find start node
        start_node_id = None
        for node_id, node_data in workflow_data["nodes"].items():
            if node_data["node_type"] == "StartNode":
                start_node_id = node_id
                break

        assert start_node_id is not None, "No StartNode found"

        # Execute in order
        start = time.perf_counter()

        current_id: Optional[str] = start_node_id
        executed_count = 0

        while current_id and current_id in nodes:
            node = nodes[current_id]
            result = await node.execute(context)
            executed_count += 1

            # Move to next node
            current_id = connection_map.get(current_id)

        elapsed = time.perf_counter() - start

        # Verify all nodes executed
        assert executed_count == 100, f"Expected 100 nodes, executed {executed_count}"

        # Performance assertion
        assert elapsed < EXECUTION_100_NODE_THRESHOLD_SECONDS, (
            f"100-node workflow took {elapsed:.2f}s "
            f"(threshold: {EXECUTION_100_NODE_THRESHOLD_SECONDS}s)"
        )

    @pytest.mark.asyncio
    async def test_node_execution_overhead(self) -> None:
        """Per-node execution overhead should be minimal (< 1ms avg)."""
        from casare_rpa.nodes.variable_nodes import SetVariableNode

        context = MagicMock()
        context.variables = {}
        context.get_variable = lambda name, default=None: context.variables.get(
            name, default
        )
        context.set_variable = lambda name, value: context.variables.__setitem__(
            name, value
        )

        iterations = 1000
        start = time.perf_counter()

        for i in range(iterations):
            node = SetVariableNode(
                f"node_{i}",
                variable_name=f"var_{i}",
                default_value=i,
            )
            await node.execute(context)

        elapsed = time.perf_counter() - start
        avg_per_node = (elapsed / iterations) * 1000  # Convert to ms

        # Average per-node overhead should be < 1ms
        assert (
            avg_per_node < 1.0
        ), f"Per-node overhead: {avg_per_node:.3f}ms avg (threshold: 1.0ms)"


# --- Benchmark Tests (require pytest-benchmark) ---


@pytest.mark.skipif(not BENCHMARK_AVAILABLE, reason="pytest-benchmark not installed")
class TestBenchmarkStartup:
    """Benchmark tests for startup using pytest-benchmark."""

    @pytest.mark.benchmark(group="startup")
    def test_startup_time_under_threshold(self, benchmark) -> None:
        """
        Benchmark application startup time.

        This measures the time to import core modules and create
        a WorkflowSchema - simulating cold start initialization.

        Threshold: < 3 seconds
        """

        def startup_simulation():
            # Simulate core startup imports
            import importlib

            # Reimport to simulate fresh load (modules cached after first)
            from casare_rpa.domain.entities.workflow import WorkflowSchema
            from casare_rpa.domain.entities.workflow_metadata import WorkflowMetadata
            from casare_rpa.core.base_node import BaseNode
            from casare_rpa.core.types import NodeStatus

            # Create a workflow schema
            schema = WorkflowSchema()
            schema.metadata.name = "Benchmark Workflow"

            return schema

        result = benchmark(startup_simulation)

        # Get benchmark statistics
        mean_time = benchmark.stats.stats.mean

        assert (
            mean_time < STARTUP_THRESHOLD_SECONDS
        ), f"Startup time {mean_time:.2f}s exceeds {STARTUP_THRESHOLD_SECONDS}s threshold"


@pytest.mark.skipif(not BENCHMARK_AVAILABLE, reason="pytest-benchmark not installed")
class TestBenchmarkExecution:
    """Benchmark tests for workflow execution using pytest-benchmark."""

    @pytest.mark.benchmark(group="execution")
    def test_100_node_workflow_under_threshold(self, benchmark) -> None:
        """
        Benchmark 100-node workflow execution.

        Threshold: < 5 seconds
        """
        from casare_rpa.domain.entities.workflow import WorkflowSchema
        from casare_rpa.nodes.basic_nodes import StartNode, EndNode
        from casare_rpa.nodes.variable_nodes import SetVariableNode

        # Setup outside benchmark
        workflow_data = create_100_node_workflow()
        workflow = WorkflowSchema.from_dict(workflow_data)

        def execute_workflow():
            # Create fresh nodes and context for each run
            nodes = {}
            for node_id, node_data in workflow.nodes.items():
                node_type = node_data["node_type"]
                config = node_data.get("config", {})

                if node_type == "StartNode":
                    nodes[node_id] = StartNode(node_id)
                elif node_type == "EndNode":
                    nodes[node_id] = EndNode(node_id)
                elif node_type == "SetVariableNode":
                    nodes[node_id] = SetVariableNode(
                        node_id,
                        variable_name=config.get("variable_name", ""),
                        default_value=config.get("default_value"),
                    )

            context = MagicMock()
            context.variables = {}
            context.get_variable = lambda name, default=None: context.variables.get(
                name, default
            )
            context.set_variable = lambda name, value: context.variables.__setitem__(
                name, value
            )

            # Build execution order
            connection_map = {}
            for conn_data in workflow_data["connections"]:
                connection_map[conn_data["source_node"]] = conn_data["target_node"]

            # Find start
            start_id = None
            for nid, ndata in workflow_data["nodes"].items():
                if ndata["node_type"] == "StartNode":
                    start_id = nid
                    break

            # Execute synchronously for benchmark
            current_id = start_id
            executed = 0

            loop = asyncio.new_event_loop()
            try:
                while current_id and current_id in nodes:
                    loop.run_until_complete(nodes[current_id].execute(context))
                    executed += 1
                    current_id = connection_map.get(current_id)
            finally:
                loop.close()

            return executed

        result = benchmark(execute_workflow)

        mean_time = benchmark.stats.stats.mean

        assert (
            mean_time < EXECUTION_100_NODE_THRESHOLD_SECONDS
        ), f"Execution time {mean_time:.2f}s exceeds {EXECUTION_100_NODE_THRESHOLD_SECONDS}s threshold"


# --- Memory Tests ---


class TestMemoryPerformance:
    """Tests for memory usage during operations."""

    def test_workflow_memory_footprint(self) -> None:
        """100-node workflow should have reasonable memory footprint."""
        from casare_rpa.domain.entities.workflow import WorkflowSchema

        workflow_data = create_100_node_workflow()

        # Get size of workflow data dict
        data_size = sys.getsizeof(workflow_data)

        # Create schema
        workflow = WorkflowSchema.from_dict(workflow_data)

        # Workflow schema should not be excessively large
        # 100 nodes ~ 100KB is reasonable upper bound
        assert (
            data_size < 100_000
        ), f"Workflow data size {data_size} bytes exceeds 100KB threshold"

    def test_node_instance_memory(self) -> None:
        """Individual node instances should be lightweight."""
        from casare_rpa.nodes.variable_nodes import SetVariableNode

        node = SetVariableNode("test_node", variable_name="test", default_value=42)

        # Get approximate size (not including referenced objects)
        node_size = sys.getsizeof(node)

        # Node instance should be < 1KB
        assert node_size < 1024, f"Node instance size {node_size} bytes exceeds 1KB"


# --- Regression Guard Tests ---


class TestPerformanceRegressionGuards:
    """
    Guard tests to catch performance regressions.

    These are simple, fast tests that run on every CI build
    to detect obvious performance degradation.
    """

    def test_workflow_serialization_speed(self) -> None:
        """Workflow serialization should be fast."""
        from casare_rpa.domain.entities.workflow import WorkflowSchema
        import orjson

        workflow_data = create_100_node_workflow()
        workflow = WorkflowSchema.from_dict(workflow_data)

        start = time.perf_counter()

        for _ in range(100):
            serialized = workflow.to_dict()
            _ = orjson.dumps(serialized)

        elapsed = time.perf_counter() - start
        avg = elapsed / 100

        # 100-node workflow serialization should be < 10ms
        assert avg < 0.01, f"Serialization took {avg*1000:.2f}ms avg (threshold: 10ms)"

    def test_workflow_deserialization_speed(self) -> None:
        """Workflow deserialization should be fast."""
        from casare_rpa.domain.entities.workflow import WorkflowSchema
        import orjson

        workflow_data = create_100_node_workflow()
        json_bytes = orjson.dumps(workflow_data)

        start = time.perf_counter()

        for _ in range(100):
            data = orjson.loads(json_bytes)
            _ = WorkflowSchema.from_dict(data)

        elapsed = time.perf_counter() - start
        avg = elapsed / 100

        # Deserialization should be < 10ms
        assert (
            avg < 0.01
        ), f"Deserialization took {avg*1000:.2f}ms avg (threshold: 10ms)"

    def test_node_creation_speed(self) -> None:
        """Creating node instances should be fast."""
        from casare_rpa.nodes.variable_nodes import SetVariableNode

        start = time.perf_counter()

        nodes = []
        for i in range(1000):
            node = SetVariableNode(f"node_{i}", variable_name=f"var_{i}")
            nodes.append(node)

        elapsed = time.perf_counter() - start

        # Creating 1000 nodes should be < 1 second
        assert (
            elapsed < 1.0
        ), f"Creating 1000 nodes took {elapsed:.2f}s (threshold: 1.0s)"
