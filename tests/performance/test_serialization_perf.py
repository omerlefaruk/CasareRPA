"""
Workflow serialization performance benchmarks.

Tests serialization and deserialization performance for workflows
of various sizes (small, medium, large).

Thresholds:
- Small workflow (10 nodes): < 5ms serialize, < 10ms deserialize
- Medium workflow (50 nodes): < 20ms serialize, < 40ms deserialize
- Large workflow (200 nodes): < 100ms serialize, < 200ms deserialize

Run: pytest tests/performance/test_serialization_perf.py -v
"""

import time
from typing import Any, Dict, List

import pytest

try:
    import orjson

    ORJSON_AVAILABLE = True
except ImportError:
    ORJSON_AVAILABLE = False
    import json

from casare_rpa.domain.entities.workflow import WorkflowSchema
from casare_rpa.domain.entities.workflow_metadata import WorkflowMetadata
from casare_rpa.domain.entities.node_connection import NodeConnection
from casare_rpa.nodes.basic_nodes import StartNode, EndNode
from casare_rpa.nodes.variable_nodes import SetVariableNode


# --- Performance Thresholds (milliseconds) ---
THRESHOLD_SMALL_SERIALIZE_MS = 5
THRESHOLD_SMALL_DESERIALIZE_MS = 10
THRESHOLD_MEDIUM_SERIALIZE_MS = 20
THRESHOLD_MEDIUM_DESERIALIZE_MS = 40
THRESHOLD_LARGE_SERIALIZE_MS = 100
THRESHOLD_LARGE_DESERIALIZE_MS = 200


def create_workflow_dict(n_nodes: int) -> Dict[str, Any]:
    """
    Create workflow dictionary with n SetVariable nodes.

    Structure: Start -> [SetVariable * n] -> End
    Total nodes: n + 2 (Start + End)

    Args:
        n_nodes: Number of SetVariable nodes

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
    for i in range(n_nodes):
        node_id = f"set_var_{i}"
        nodes[node_id] = {
            "node_id": node_id,
            "node_type": "SetVariableNode",
            "name": f"Set Variable {i}",
            "position": [(i + 1) * 100, 0],
            "config": {
                "variable_name": f"var_{i}",
                "default_value": f"value_{i}",
                "variable_type": "String",
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
        "position": [(n_nodes + 1) * 100, 0],
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
            "name": f"Serialization Test ({n_nodes} nodes)",
            "version": "1.0.0",
            "description": f"Performance test workflow with {n_nodes} nodes",
        },
        "nodes": nodes,
        "connections": connections,
        "frames": [],
        "variables": {
            f"global_var_{i}": {"type": "String", "default_value": f"global_{i}"}
            for i in range(10)
        },
        "settings": {"stop_on_error": True, "timeout": 300, "retry_count": 0},
    }


def create_workflow_schema(n_nodes: int) -> WorkflowSchema:
    """Create WorkflowSchema with n nodes."""
    return WorkflowSchema.from_dict(create_workflow_dict(n_nodes))


class TestWorkflowSerializationPerformance:
    """Performance tests for workflow serialization (to_dict)."""

    @pytest.mark.slow
    def test_small_workflow_serialize_under_threshold(self) -> None:
        """Small workflow (10 nodes) serialization must complete under 5ms."""
        workflow = create_workflow_schema(10)

        iterations = 100
        start = time.perf_counter()

        for _ in range(iterations):
            _ = workflow.to_dict()

        elapsed_ms = (time.perf_counter() - start) * 1000
        avg_ms = elapsed_ms / iterations

        assert avg_ms < THRESHOLD_SMALL_SERIALIZE_MS, (
            f"Small workflow serialization took {avg_ms:.3f}ms avg "
            f"(threshold: {THRESHOLD_SMALL_SERIALIZE_MS}ms)"
        )

    @pytest.mark.slow
    def test_medium_workflow_serialize_under_threshold(self) -> None:
        """Medium workflow (50 nodes) serialization must complete under 20ms."""
        workflow = create_workflow_schema(50)

        iterations = 50
        start = time.perf_counter()

        for _ in range(iterations):
            _ = workflow.to_dict()

        elapsed_ms = (time.perf_counter() - start) * 1000
        avg_ms = elapsed_ms / iterations

        assert avg_ms < THRESHOLD_MEDIUM_SERIALIZE_MS, (
            f"Medium workflow serialization took {avg_ms:.3f}ms avg "
            f"(threshold: {THRESHOLD_MEDIUM_SERIALIZE_MS}ms)"
        )

    @pytest.mark.slow
    def test_large_workflow_serialize_under_threshold(self) -> None:
        """Large workflow (200 nodes) serialization must complete under 100ms."""
        workflow = create_workflow_schema(200)

        iterations = 20
        start = time.perf_counter()

        for _ in range(iterations):
            _ = workflow.to_dict()

        elapsed_ms = (time.perf_counter() - start) * 1000
        avg_ms = elapsed_ms / iterations

        assert avg_ms < THRESHOLD_LARGE_SERIALIZE_MS, (
            f"Large workflow serialization took {avg_ms:.3f}ms avg "
            f"(threshold: {THRESHOLD_LARGE_SERIALIZE_MS}ms)"
        )

    @pytest.mark.slow
    def test_serialize_benchmark(self, benchmark) -> None:
        """Benchmark workflow serialization."""
        workflow = create_workflow_schema(50)

        def serialize():
            return workflow.to_dict()

        result = benchmark(serialize)
        assert "nodes" in result
        assert len(result["nodes"]) == 52  # 50 + Start + End


class TestWorkflowDeserializationPerformance:
    """Performance tests for workflow deserialization (from_dict)."""

    @pytest.mark.slow
    def test_small_workflow_deserialize_under_threshold(self) -> None:
        """Small workflow (10 nodes) deserialization must complete under 10ms."""
        workflow_dict = create_workflow_dict(10)

        iterations = 100
        start = time.perf_counter()

        for _ in range(iterations):
            _ = WorkflowSchema.from_dict(workflow_dict)

        elapsed_ms = (time.perf_counter() - start) * 1000
        avg_ms = elapsed_ms / iterations

        assert avg_ms < THRESHOLD_SMALL_DESERIALIZE_MS, (
            f"Small workflow deserialization took {avg_ms:.3f}ms avg "
            f"(threshold: {THRESHOLD_SMALL_DESERIALIZE_MS}ms)"
        )

    @pytest.mark.slow
    def test_medium_workflow_deserialize_under_threshold(self) -> None:
        """Medium workflow (50 nodes) deserialization must complete under 40ms."""
        workflow_dict = create_workflow_dict(50)

        iterations = 50
        start = time.perf_counter()

        for _ in range(iterations):
            _ = WorkflowSchema.from_dict(workflow_dict)

        elapsed_ms = (time.perf_counter() - start) * 1000
        avg_ms = elapsed_ms / iterations

        assert avg_ms < THRESHOLD_MEDIUM_DESERIALIZE_MS, (
            f"Medium workflow deserialization took {avg_ms:.3f}ms avg "
            f"(threshold: {THRESHOLD_MEDIUM_DESERIALIZE_MS}ms)"
        )

    @pytest.mark.slow
    def test_large_workflow_deserialize_under_threshold(self) -> None:
        """Large workflow (200 nodes) deserialization must complete under 200ms."""
        workflow_dict = create_workflow_dict(200)

        iterations = 20
        start = time.perf_counter()

        for _ in range(iterations):
            _ = WorkflowSchema.from_dict(workflow_dict)

        elapsed_ms = (time.perf_counter() - start) * 1000
        avg_ms = elapsed_ms / iterations

        assert avg_ms < THRESHOLD_LARGE_DESERIALIZE_MS, (
            f"Large workflow deserialization took {avg_ms:.3f}ms avg "
            f"(threshold: {THRESHOLD_LARGE_DESERIALIZE_MS}ms)"
        )

    @pytest.mark.slow
    def test_deserialize_benchmark(self, benchmark) -> None:
        """Benchmark workflow deserialization."""
        workflow_dict = create_workflow_dict(50)

        def deserialize():
            return WorkflowSchema.from_dict(workflow_dict)

        result = benchmark(deserialize)
        assert len(result.nodes) == 52  # 50 + Start + End


class TestJSONSerializationPerformance:
    """Performance tests for JSON encoding/decoding."""

    @pytest.mark.slow
    def test_json_encode_small_workflow(self) -> None:
        """JSON encoding small workflow should be fast."""
        workflow = create_workflow_schema(10)
        workflow_dict = workflow.to_dict()

        iterations = 100
        start = time.perf_counter()

        for _ in range(iterations):
            if ORJSON_AVAILABLE:
                _ = orjson.dumps(workflow_dict)
            else:
                _ = json.dumps(workflow_dict)

        elapsed_ms = (time.perf_counter() - start) * 1000
        avg_ms = elapsed_ms / iterations

        # JSON encoding should add < 5ms overhead
        assert avg_ms < 5, f"JSON encode took {avg_ms:.3f}ms avg"

    @pytest.mark.slow
    def test_json_encode_large_workflow(self) -> None:
        """JSON encoding large workflow should still be reasonable."""
        workflow = create_workflow_schema(200)
        workflow_dict = workflow.to_dict()

        iterations = 20
        start = time.perf_counter()

        for _ in range(iterations):
            if ORJSON_AVAILABLE:
                _ = orjson.dumps(workflow_dict)
            else:
                _ = json.dumps(workflow_dict)

        elapsed_ms = (time.perf_counter() - start) * 1000
        avg_ms = elapsed_ms / iterations

        # JSON encoding large workflow should be < 50ms
        assert avg_ms < 50, f"JSON encode took {avg_ms:.3f}ms avg"

    @pytest.mark.slow
    def test_json_decode_small_workflow(self) -> None:
        """JSON decoding small workflow should be fast."""
        workflow_dict = create_workflow_dict(10)
        if ORJSON_AVAILABLE:
            json_bytes = orjson.dumps(workflow_dict)
        else:
            json_str = json.dumps(workflow_dict)

        iterations = 100
        start = time.perf_counter()

        for _ in range(iterations):
            if ORJSON_AVAILABLE:
                _ = orjson.loads(json_bytes)
            else:
                _ = json.loads(json_str)

        elapsed_ms = (time.perf_counter() - start) * 1000
        avg_ms = elapsed_ms / iterations

        # JSON decoding should be < 2ms
        assert avg_ms < 2, f"JSON decode took {avg_ms:.3f}ms avg"

    @pytest.mark.slow
    def test_full_roundtrip_small_workflow(self) -> None:
        """Full serialize + JSON encode + JSON decode + deserialize cycle."""
        workflow = create_workflow_schema(10)

        iterations = 100
        start = time.perf_counter()

        for _ in range(iterations):
            # Serialize
            workflow_dict = workflow.to_dict()
            # JSON encode
            if ORJSON_AVAILABLE:
                json_bytes = orjson.dumps(workflow_dict)
                # JSON decode
                decoded = orjson.loads(json_bytes)
            else:
                json_str = json.dumps(workflow_dict)
                decoded = json.loads(json_str)
            # Deserialize
            _ = WorkflowSchema.from_dict(decoded)

        elapsed_ms = (time.perf_counter() - start) * 1000
        avg_ms = elapsed_ms / iterations

        # Full roundtrip should be < 20ms for small workflow
        assert avg_ms < 20, f"Full roundtrip took {avg_ms:.3f}ms avg"

    @pytest.mark.slow
    def test_full_roundtrip_large_workflow(self) -> None:
        """Full roundtrip for large workflow."""
        workflow = create_workflow_schema(200)

        iterations = 10
        start = time.perf_counter()

        for _ in range(iterations):
            workflow_dict = workflow.to_dict()
            if ORJSON_AVAILABLE:
                json_bytes = orjson.dumps(workflow_dict)
                decoded = orjson.loads(json_bytes)
            else:
                json_str = json.dumps(workflow_dict)
                decoded = json.loads(json_str)
            _ = WorkflowSchema.from_dict(decoded)

        elapsed_ms = (time.perf_counter() - start) * 1000
        avg_ms = elapsed_ms / iterations

        # Full roundtrip should be < 500ms for large workflow
        assert avg_ms < 500, f"Full roundtrip took {avg_ms:.3f}ms avg"


class TestSerializationScaling:
    """Tests for serialization time scaling characteristics."""

    @pytest.mark.slow
    def test_serialization_scales_linearly(self) -> None:
        """Serialization time should scale linearly with workflow size."""
        sizes = [10, 25, 50, 100]
        serialize_timings = []
        deserialize_timings = []

        for size in sizes:
            workflow = create_workflow_schema(size)
            workflow_dict = create_workflow_dict(size)

            # Time serialization
            iterations = 20
            start = time.perf_counter()
            for _ in range(iterations):
                _ = workflow.to_dict()
            serialize_time = (time.perf_counter() - start) / iterations
            serialize_timings.append((size, serialize_time))

            # Time deserialization
            start = time.perf_counter()
            for _ in range(iterations):
                _ = WorkflowSchema.from_dict(workflow_dict)
            deserialize_time = (time.perf_counter() - start) / iterations
            deserialize_timings.append((size, deserialize_time))

        # Check linear scaling for serialization
        for i in range(1, len(serialize_timings)):
            prev_size, prev_time = serialize_timings[i - 1]
            curr_size, curr_time = serialize_timings[i]

            size_ratio = curr_size / prev_size
            time_ratio = curr_time / prev_time if prev_time > 0.0001 else 1.0

            # Allow 3x tolerance for system variance
            assert (
                time_ratio < size_ratio * 3
            ), f"Serialization non-linear: size {size_ratio:.1f}x, time {time_ratio:.1f}x"

        # Check linear scaling for deserialization
        for i in range(1, len(deserialize_timings)):
            prev_size, prev_time = deserialize_timings[i - 1]
            curr_size, curr_time = deserialize_timings[i]

            size_ratio = curr_size / prev_size
            time_ratio = curr_time / prev_time if prev_time > 0.0001 else 1.0

            assert (
                time_ratio < size_ratio * 3
            ), f"Deserialization non-linear: size {size_ratio:.1f}x, time {time_ratio:.1f}x"

    @pytest.mark.slow
    def test_serialized_size_scales_linearly(self) -> None:
        """Serialized data size should scale linearly with node count."""
        sizes = [10, 50, 100, 200]
        data_sizes = []

        for size in sizes:
            workflow_dict = create_workflow_dict(size)
            if ORJSON_AVAILABLE:
                json_bytes = orjson.dumps(workflow_dict)
                byte_size = len(json_bytes)
            else:
                json_str = json.dumps(workflow_dict)
                byte_size = len(json_str.encode("utf-8"))
            data_sizes.append((size, byte_size))

        # Check approximately linear growth
        for i in range(1, len(data_sizes)):
            prev_size, prev_bytes = data_sizes[i - 1]
            curr_size, curr_bytes = data_sizes[i]

            size_ratio = curr_size / prev_size
            bytes_ratio = curr_bytes / prev_bytes if prev_bytes > 0 else 1.0

            # Allow 1.5x tolerance (some overhead doesn't scale linearly)
            assert (
                bytes_ratio < size_ratio * 1.5
            ), f"Data size non-linear: nodes {size_ratio:.1f}x, bytes {bytes_ratio:.1f}x"


class TestConnectionSerializationPerformance:
    """Performance tests for connection-heavy workflows."""

    @pytest.mark.slow
    def test_many_connections_serialize(self) -> None:
        """Workflow with many connections should serialize quickly."""
        # Create workflow with many inter-node connections (not just linear chain)
        metadata = WorkflowMetadata(name="Connection Test")
        workflow = WorkflowSchema(metadata)

        # Add start node
        workflow.add_node(
            {
                "node_id": "start",
                "node_type": "StartNode",
                "name": "Start",
                "position": [0, 0],
                "config": {},
            }
        )

        # Add 50 nodes and connect each to next
        for i in range(50):
            workflow.add_node(
                {
                    "node_id": f"node_{i}",
                    "node_type": "SetVariableNode",
                    "name": f"Node {i}",
                    "position": [i * 100, 0],
                    "config": {"variable_name": f"var_{i}"},
                }
            )

        # Add connections
        workflow.add_connection(
            NodeConnection(
                source_node="start",
                source_port="exec_out",
                target_node="node_0",
                target_port="exec_in",
            )
        )

        for i in range(49):
            workflow.add_connection(
                NodeConnection(
                    source_node=f"node_{i}",
                    source_port="exec_out",
                    target_node=f"node_{i+1}",
                    target_port="exec_in",
                )
            )

        iterations = 50
        start = time.perf_counter()

        for _ in range(iterations):
            _ = workflow.to_dict()

        elapsed_ms = (time.perf_counter() - start) * 1000
        avg_ms = elapsed_ms / iterations

        # Should be under 30ms
        assert avg_ms < 30, f"Connection-heavy serialize took {avg_ms:.3f}ms avg"


class TestSerializationBenchmarks:
    """Benchmark tests using pytest-benchmark."""

    @pytest.mark.slow
    def test_benchmark_small_serialize(self, benchmark) -> None:
        """Benchmark small workflow serialization."""
        workflow = create_workflow_schema(10)

        result = benchmark(workflow.to_dict)
        assert len(result["nodes"]) == 12

        median_ms = benchmark.stats.stats.median * 1000
        assert median_ms < THRESHOLD_SMALL_SERIALIZE_MS

    @pytest.mark.slow
    def test_benchmark_medium_serialize(self, benchmark) -> None:
        """Benchmark medium workflow serialization."""
        workflow = create_workflow_schema(50)

        result = benchmark(workflow.to_dict)
        assert len(result["nodes"]) == 52

        median_ms = benchmark.stats.stats.median * 1000
        assert median_ms < THRESHOLD_MEDIUM_SERIALIZE_MS

    @pytest.mark.slow
    def test_benchmark_large_serialize(self, benchmark) -> None:
        """Benchmark large workflow serialization."""
        workflow = create_workflow_schema(200)

        result = benchmark(workflow.to_dict)
        assert len(result["nodes"]) == 202

        median_ms = benchmark.stats.stats.median * 1000
        assert median_ms < THRESHOLD_LARGE_SERIALIZE_MS

    @pytest.mark.slow
    def test_benchmark_small_deserialize(self, benchmark) -> None:
        """Benchmark small workflow deserialization."""
        workflow_dict = create_workflow_dict(10)

        def deserialize():
            return WorkflowSchema.from_dict(workflow_dict)

        result = benchmark(deserialize)
        assert len(result.nodes) == 12

        median_ms = benchmark.stats.stats.median * 1000
        assert median_ms < THRESHOLD_SMALL_DESERIALIZE_MS

    @pytest.mark.slow
    def test_benchmark_medium_deserialize(self, benchmark) -> None:
        """Benchmark medium workflow deserialization."""
        workflow_dict = create_workflow_dict(50)

        def deserialize():
            return WorkflowSchema.from_dict(workflow_dict)

        result = benchmark(deserialize)
        assert len(result.nodes) == 52

        median_ms = benchmark.stats.stats.median * 1000
        assert median_ms < THRESHOLD_MEDIUM_DESERIALIZE_MS

    @pytest.mark.slow
    def test_benchmark_large_deserialize(self, benchmark) -> None:
        """Benchmark large workflow deserialization."""
        workflow_dict = create_workflow_dict(200)

        def deserialize():
            return WorkflowSchema.from_dict(workflow_dict)

        result = benchmark(deserialize)
        assert len(result.nodes) == 202

        median_ms = benchmark.stats.stats.median * 1000
        assert median_ms < THRESHOLD_LARGE_DESERIALIZE_MS
