"""
Node creation performance benchmarks.

Tests node instantiation and port creation performance.
Establishes regression thresholds for node factory operations.

Thresholds:
- Single node creation: < 5ms
- Port creation: < 1ms per port
- Batch node creation (100 nodes): < 100ms

Run: pytest tests/performance/test_node_creation_perf.py -v
"""

import time
from typing import List, Type

import pytest

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects import Port
from casare_rpa.domain.value_objects.types import DataType, PortType
from casare_rpa.nodes.basic_nodes import StartNode, EndNode, CommentNode
from casare_rpa.nodes.variable_nodes import SetVariableNode, GetVariableNode
from casare_rpa.nodes.control_flow_nodes import IfNode


# --- Performance Thresholds ---
THRESHOLD_SINGLE_NODE_MS = 5
THRESHOLD_PORT_CREATION_MS = 1
THRESHOLD_BATCH_100_NODES_MS = 100
THRESHOLD_BATCH_1000_NODES_MS = 1000


class TestNodeInstantiationPerformance:
    """Performance tests for node instantiation."""

    @pytest.mark.slow
    def test_start_node_creation_under_threshold(self) -> None:
        """StartNode creation must complete under 5ms."""
        iterations = 100
        start = time.perf_counter()

        for i in range(iterations):
            node = StartNode(f"start_{i}")

        elapsed_ms = (time.perf_counter() - start) * 1000
        avg_ms = elapsed_ms / iterations

        assert avg_ms < THRESHOLD_SINGLE_NODE_MS, (
            f"StartNode creation took {avg_ms:.3f}ms avg "
            f"(threshold: {THRESHOLD_SINGLE_NODE_MS}ms)"
        )

    @pytest.mark.slow
    def test_end_node_creation_under_threshold(self) -> None:
        """EndNode creation must complete under 5ms."""
        iterations = 100
        start = time.perf_counter()

        for i in range(iterations):
            node = EndNode(f"end_{i}")

        elapsed_ms = (time.perf_counter() - start) * 1000
        avg_ms = elapsed_ms / iterations

        assert avg_ms < THRESHOLD_SINGLE_NODE_MS, (
            f"EndNode creation took {avg_ms:.3f}ms avg "
            f"(threshold: {THRESHOLD_SINGLE_NODE_MS}ms)"
        )

    @pytest.mark.slow
    def test_set_variable_node_creation_under_threshold(self) -> None:
        """SetVariableNode creation must complete under 5ms."""
        iterations = 100
        start = time.perf_counter()

        for i in range(iterations):
            node = SetVariableNode(
                f"set_var_{i}",
                config={"variable_name": f"var_{i}", "default_value": i},
            )

        elapsed_ms = (time.perf_counter() - start) * 1000
        avg_ms = elapsed_ms / iterations

        assert avg_ms < THRESHOLD_SINGLE_NODE_MS, (
            f"SetVariableNode creation took {avg_ms:.3f}ms avg "
            f"(threshold: {THRESHOLD_SINGLE_NODE_MS}ms)"
        )

    @pytest.mark.slow
    def test_if_node_creation_under_threshold(self) -> None:
        """IfNode creation must complete under 5ms."""
        iterations = 100
        start = time.perf_counter()

        for i in range(iterations):
            node = IfNode(f"if_{i}", config={"expression": "true"})

        elapsed_ms = (time.perf_counter() - start) * 1000
        avg_ms = elapsed_ms / iterations

        assert avg_ms < THRESHOLD_SINGLE_NODE_MS, (
            f"IfNode creation took {avg_ms:.3f}ms avg "
            f"(threshold: {THRESHOLD_SINGLE_NODE_MS}ms)"
        )

    @pytest.mark.slow
    def test_node_creation_benchmark(self, benchmark) -> None:
        """Benchmark node creation across multiple types."""
        node_types: List[tuple[Type, str, dict]] = [
            (StartNode, "start", {}),
            (EndNode, "end", {}),
            (SetVariableNode, "set_var", {"variable_name": "x", "default_value": 1}),
            (CommentNode, "comment", {"comment": "Test"}),
        ]

        counter = [0]

        def create_nodes():
            results = []
            for node_cls, prefix, config in node_types:
                counter[0] += 1
                node = node_cls(f"{prefix}_{counter[0]}", config=config)
                results.append(node)
            return results

        result = benchmark(create_nodes)
        assert len(result) == len(node_types)


class TestPortCreationPerformance:
    """Performance tests for port creation."""

    @pytest.mark.slow
    def test_port_creation_under_threshold(self) -> None:
        """Port creation must complete under 1ms."""
        iterations = 1000
        start = time.perf_counter()

        ports = []
        for i in range(iterations):
            port = Port(
                name=f"port_{i}",
                port_type=PortType.INPUT,
                data_type=DataType.STRING,
                label=f"Port {i}",
            )
            ports.append(port)

        elapsed_ms = (time.perf_counter() - start) * 1000
        avg_ms = elapsed_ms / iterations

        assert avg_ms < THRESHOLD_PORT_CREATION_MS, (
            f"Port creation took {avg_ms:.4f}ms avg "
            f"(threshold: {THRESHOLD_PORT_CREATION_MS}ms)"
        )

    @pytest.mark.slow
    def test_port_creation_all_types(self) -> None:
        """Port creation with all data types should be fast."""
        data_types = [
            DataType.STRING,
            DataType.INTEGER,
            DataType.FLOAT,
            DataType.BOOLEAN,
            DataType.OBJECT,
            DataType.ARRAY,
            DataType.ANY,
        ]

        iterations = 100
        start = time.perf_counter()

        ports = []
        for _ in range(iterations):
            for i, dt in enumerate(data_types):
                port = Port(
                    name=f"port_{i}",
                    port_type=PortType.INPUT,
                    data_type=dt,
                )
                ports.append(port)

        elapsed_ms = (time.perf_counter() - start) * 1000
        total_ports = iterations * len(data_types)
        avg_ms = elapsed_ms / total_ports

        assert (
            avg_ms < THRESHOLD_PORT_CREATION_MS
        ), f"Port creation for all types took {avg_ms:.4f}ms avg"

    @pytest.mark.slow
    def test_port_value_operations(self) -> None:
        """Port value get/set operations should be fast."""
        port = Port("test_port", PortType.INPUT, DataType.STRING)

        iterations = 10000
        start = time.perf_counter()

        for i in range(iterations):
            port.set_value(f"value_{i}")
            _ = port.get_value()

        elapsed_ms = (time.perf_counter() - start) * 1000
        avg_us = (elapsed_ms / iterations) * 1000  # microseconds

        # Port operations should be < 10 microseconds
        assert avg_us < 10, f"Port value operations took {avg_us:.2f}us avg"


class TestBatchNodeCreation:
    """Performance tests for batch node creation."""

    @pytest.mark.slow
    def test_create_100_nodes_under_threshold(self) -> None:
        """Creating 100 nodes must complete under 100ms."""
        start = time.perf_counter()

        nodes = []
        for i in range(100):
            node = SetVariableNode(
                f"node_{i}",
                config={"variable_name": f"var_{i}", "default_value": i},
            )
            nodes.append(node)

        elapsed_ms = (time.perf_counter() - start) * 1000

        assert len(nodes) == 100
        assert elapsed_ms < THRESHOLD_BATCH_100_NODES_MS, (
            f"Creating 100 nodes took {elapsed_ms:.2f}ms "
            f"(threshold: {THRESHOLD_BATCH_100_NODES_MS}ms)"
        )

    @pytest.mark.slow
    def test_create_1000_nodes_under_threshold(self) -> None:
        """Creating 1000 nodes must complete under 1s."""
        start = time.perf_counter()

        nodes = []
        for i in range(1000):
            node = SetVariableNode(
                f"node_{i}",
                config={"variable_name": f"var_{i}", "default_value": i},
            )
            nodes.append(node)

        elapsed_ms = (time.perf_counter() - start) * 1000

        assert len(nodes) == 1000
        assert elapsed_ms < THRESHOLD_BATCH_1000_NODES_MS, (
            f"Creating 1000 nodes took {elapsed_ms:.2f}ms "
            f"(threshold: {THRESHOLD_BATCH_1000_NODES_MS}ms)"
        )

    @pytest.mark.slow
    def test_batch_creation_benchmark(self, benchmark) -> None:
        """Benchmark batch node creation."""
        batch_size = 100

        def create_batch():
            nodes = []
            for i in range(batch_size):
                node = SetVariableNode(
                    f"batch_node_{i}",
                    config={"variable_name": f"var_{i}", "default_value": i},
                )
                nodes.append(node)
            return nodes

        result = benchmark(create_batch)
        assert len(result) == batch_size

        # Verify median under threshold
        median_ms = benchmark.stats.stats.median * 1000
        assert (
            median_ms < THRESHOLD_BATCH_100_NODES_MS
        ), f"Batch median {median_ms:.2f}ms exceeds {THRESHOLD_BATCH_100_NODES_MS}ms"


class TestNodeScalingCharacteristics:
    """Tests for node creation scaling behavior."""

    @pytest.mark.slow
    def test_node_creation_scales_linearly(self) -> None:
        """Node creation time should scale linearly with count."""
        sizes = [10, 50, 100, 500]
        timings = []

        for size in sizes:
            start = time.perf_counter()
            nodes = [
                SetVariableNode(f"node_{i}", config={"variable_name": f"v{i}"})
                for i in range(size)
            ]
            elapsed = time.perf_counter() - start
            timings.append((size, elapsed))

        # Check linear scaling
        for i in range(1, len(timings)):
            prev_size, prev_time = timings[i - 1]
            curr_size, curr_time = timings[i]

            size_ratio = curr_size / prev_size
            time_ratio = curr_time / prev_time if prev_time > 0.0001 else 1.0

            # Allow 2.5x tolerance for system variance
            assert (
                time_ratio < size_ratio * 2.5
            ), f"Non-linear scaling: size {size_ratio:.1f}x, time {time_ratio:.1f}x"

    @pytest.mark.slow
    def test_node_memory_footprint(self) -> None:
        """Node instances should have reasonable memory footprint."""
        import sys

        node = SetVariableNode(
            "test_node",
            config={"variable_name": "test", "default_value": 42},
        )

        # Basic size check (not including referenced objects)
        base_size = sys.getsizeof(node)

        # Node should be under 2KB base size
        assert base_size < 2048, f"Node base size {base_size} bytes exceeds 2KB"

    @pytest.mark.slow
    def test_port_count_scaling(self) -> None:
        """Nodes with many ports should still be fast to create."""

        # Create a node with many ports by directly adding ports
        class ManyPortsNode(BaseNode):
            def __init__(self, node_id: str, num_ports: int = 10, **kwargs):
                self._num_ports = num_ports
                config = kwargs.get("config", {})
                super().__init__(node_id, config)
                self.node_type = "ManyPortsNode"

            def _define_ports(self):
                for i in range(self._num_ports):
                    self.add_input_port(f"input_{i}", DataType.STRING)
                    self.add_output_port(f"output_{i}", DataType.STRING)

            async def execute(self, context):
                return {"success": True}

        # Test with increasing port counts
        port_counts = [5, 10, 20, 50]
        timings = []

        for num_ports in port_counts:
            iterations = 50
            start = time.perf_counter()
            for i in range(iterations):
                node = ManyPortsNode(f"node_{i}", num_ports=num_ports)
            elapsed = time.perf_counter() - start
            avg_ms = (elapsed / iterations) * 1000
            timings.append((num_ports, avg_ms))

        # Even 50-port nodes should be under 10ms
        for num_ports, avg_ms in timings:
            assert avg_ms < 10, (
                f"Node with {num_ports} ports took {avg_ms:.2f}ms " f"(threshold: 10ms)"
            )


class TestNodeSerializationPerformance:
    """Performance tests for node serialization."""

    @pytest.mark.slow
    def test_node_serialize_under_threshold(self) -> None:
        """Node serialization should be fast."""
        node = SetVariableNode(
            "test_node",
            config={"variable_name": "test", "default_value": 42},
        )

        iterations = 1000
        start = time.perf_counter()

        for _ in range(iterations):
            _ = node.serialize()

        elapsed_ms = (time.perf_counter() - start) * 1000
        avg_ms = elapsed_ms / iterations

        # Serialization should be < 0.5ms per node
        assert avg_ms < 0.5, f"Node serialization took {avg_ms:.4f}ms avg"

    @pytest.mark.slow
    def test_batch_serialization_benchmark(self, benchmark) -> None:
        """Benchmark batch node serialization."""
        nodes = [
            SetVariableNode(f"node_{i}", config={"variable_name": f"v{i}"})
            for i in range(100)
        ]

        def serialize_batch():
            return [node.serialize() for node in nodes]

        result = benchmark(serialize_batch)
        assert len(result) == 100


class TestNodeValidationPerformance:
    """Performance tests for node validation."""

    @pytest.mark.slow
    def test_node_validation_under_threshold(self) -> None:
        """Node validation should be fast."""
        node = SetVariableNode(
            "test_node",
            config={"variable_name": "test", "default_value": 42},
        )

        iterations = 1000
        start = time.perf_counter()

        for _ in range(iterations):
            is_valid, error = node.validate()

        elapsed_ms = (time.perf_counter() - start) * 1000
        avg_ms = elapsed_ms / iterations

        # Validation should be < 0.1ms per node
        assert avg_ms < 0.1, f"Node validation took {avg_ms:.4f}ms avg"

    @pytest.mark.slow
    def test_batch_validation_benchmark(self, benchmark) -> None:
        """Benchmark batch node validation."""
        nodes = [
            SetVariableNode(f"node_{i}", config={"variable_name": f"v{i}"})
            for i in range(100)
        ]

        def validate_batch():
            results = []
            for node in nodes:
                results.append(node.validate())
            return results

        result = benchmark(validate_batch)
        assert len(result) == 100
