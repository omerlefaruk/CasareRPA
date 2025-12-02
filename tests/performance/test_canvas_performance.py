"""Performance tests for Canvas-related operations.

Tests node creation and data structure operations
performance without requiring full Qt GUI setup.
"""

import time
import pytest


class TestNodeCreationPerformance:
    """Tests for node instantiation performance."""

    def test_casare_node_instantiation_time(self):
        """Test CasareNode instantiation performance (without visual)."""
        from casare_rpa.nodes.basic_nodes import StartNode, EndNode
        from casare_rpa.nodes.utility_nodes import LogNode
        from casare_rpa.nodes.variable_nodes import SetVariableNode
        from casare_rpa.nodes.control_flow_nodes import IfNode

        node_classes = [StartNode, EndNode, SetVariableNode, IfNode]

        start = time.perf_counter()
        nodes = []
        for i in range(100):
            for cls in node_classes:
                nodes.append(cls(node_id=f"node_{i}_{cls.__name__}"))
        elapsed = time.perf_counter() - start

        # 400 node instantiations should be fast
        assert (
            elapsed < 1.0
        ), f"Node instantiation too slow: {elapsed:.3f}s for 400 nodes"
        assert len(nodes) == 400

    def test_node_instantiation_with_config(self):
        """Test node instantiation with configuration."""
        from casare_rpa.nodes.variable_nodes import SetVariableNode

        start = time.perf_counter()
        nodes = []
        for i in range(100):
            node = SetVariableNode(
                node_id=f"set_var_{i}",
                variable_name=f"var_{i}",
                value=f"value_{i}",
            )
            nodes.append(node)
        elapsed = time.perf_counter() - start

        assert elapsed < 0.5, f"Config node creation too slow: {elapsed:.3f}s"


class TestNodeSchemaPerformance:
    """Tests for node schema generation performance."""

    def test_node_attribute_access_time(self):
        """Test node attribute access performance."""
        from casare_rpa.nodes.variable_nodes import SetVariableNode
        from casare_rpa.nodes.control_flow_nodes import IfNode

        nodes = []
        # Pre-create nodes
        for i in range(100):
            nodes.append(
                SetVariableNode(
                    node_id=f"schema_{i}_set",
                    variable_name=f"var_{i}",
                )
            )
            nodes.append(IfNode(node_id=f"schema_{i}_if"))

        # Time attribute access
        start = time.perf_counter()
        for node in nodes:
            _ = node.node_id
            _ = node.node_type
            _ = hasattr(node, "execute")
        elapsed = time.perf_counter() - start

        assert elapsed < 0.1, f"Attribute access too slow: {elapsed:.3f}s"


class TestNodeConnectionPerformance:
    """Tests for node connection data structure performance."""

    def test_connection_data_creation(self):
        """Test connection data structure creation."""
        connections = []
        start = time.perf_counter()

        for i in range(1000):
            conn = {
                "source_id": f"node_{i}",
                "source_port": "exec_out",
                "target_id": f"node_{i+1}",
                "target_port": "exec_in",
            }
            connections.append(conn)

        elapsed = time.perf_counter() - start
        assert elapsed < 0.05, f"Connection creation too slow: {elapsed:.3f}s"
        assert len(connections) == 1000

    def test_connection_lookup_by_source(self):
        """Test connection lookup performance."""
        # Build connections
        connections = []
        for i in range(1000):
            connections.append(
                {
                    "source_id": f"node_{i % 100}",  # 100 unique sources
                    "source_port": "exec_out",
                    "target_id": f"node_{i+100}",
                    "target_port": "exec_in",
                }
            )

        # Build lookup index
        by_source = {}
        for conn in connections:
            src = conn["source_id"]
            if src not in by_source:
                by_source[src] = []
            by_source[src].append(conn)

        # Time lookups
        start = time.perf_counter()
        for _ in range(100):
            for i in range(100):
                _ = by_source.get(f"node_{i}", [])
        elapsed = time.perf_counter() - start

        assert elapsed < 0.02, f"Connection lookup too slow: {elapsed:.3f}s"


class TestWorkflowDataPerformance:
    """Tests for workflow data structure operations."""

    def test_workflow_dict_serialization(self):
        """Test workflow serialization to dict."""
        import json

        # Create large workflow data
        workflow = {
            "metadata": {
                "name": "Performance Test Workflow",
                "version": "3.0",
            },
            "nodes": {},
            "connections": [],
        }

        for i in range(500):
            workflow["nodes"][f"node_{i}"] = {
                "id": f"node_{i}",
                "type": "LogNode" if i % 5 else "SetVariableNode",
                "position": [i * 200, (i % 10) * 100],
                "properties": {
                    "message": f"Log message {i}",
                },
            }

        for i in range(499):
            workflow["connections"].append(
                {
                    "source": f"node_{i}.exec_out",
                    "target": f"node_{i+1}.exec_in",
                }
            )

        start = time.perf_counter()
        for _ in range(10):
            json_str = json.dumps(workflow)
            _ = json.loads(json_str)
        elapsed = time.perf_counter() - start

        assert elapsed < 0.5, f"JSON serialization too slow: {elapsed:.3f}s"

    def test_workflow_node_lookup(self):
        """Test node lookup in workflow dict."""
        workflow_nodes = {}
        for i in range(500):
            workflow_nodes[f"node_{i}"] = {
                "id": f"node_{i}",
                "type": "LogNode",
            }

        start = time.perf_counter()
        for _ in range(100):
            for i in range(500):
                _ = workflow_nodes.get(f"node_{i}")
        elapsed = time.perf_counter() - start

        # 50000 lookups should be very fast
        assert elapsed < 0.1, f"Node lookup too slow: {elapsed:.3f}s"


class TestGraphAlgorithmPerformance:
    """Tests for graph algorithm performance."""

    def test_adjacency_list_building(self):
        """Test adjacency list construction from connections."""
        connections = []
        for i in range(1000):
            connections.append(
                {
                    "source": f"node_{i}.exec_out",
                    "target": f"node_{i+1}.exec_in",
                }
            )

        start = time.perf_counter()
        for _ in range(100):
            adj = {}
            for conn in connections:
                src = conn["source"].split(".")[0]
                tgt = conn["target"].split(".")[0]
                if src not in adj:
                    adj[src] = []
                adj[src].append(tgt)
        elapsed = time.perf_counter() - start

        assert elapsed < 0.5, f"Adjacency building too slow: {elapsed:.3f}s"

    def test_bfs_traversal_performance(self):
        """Test BFS traversal on large graph."""
        # Build adjacency list for 1000-node linear graph
        adj = {}
        for i in range(999):
            adj[f"node_{i}"] = [f"node_{i+1}"]
        adj["node_999"] = []

        from collections import deque

        start = time.perf_counter()
        for _ in range(100):
            visited = set()
            queue = deque(["node_0"])
            while queue:
                node = queue.popleft()
                if node not in visited:
                    visited.add(node)
                    queue.extend(adj.get(node, []))
        elapsed = time.perf_counter() - start

        assert elapsed < 0.5, f"BFS traversal too slow: {elapsed:.3f}s"

    def test_cycle_detection_performance(self):
        """Test cycle detection on large acyclic graph."""
        from casare_rpa.domain.validation.rules import has_circular_dependency

        # Build 500-node linear workflow
        nodes = {
            f"node_{i}": {"id": f"node_{i}", "type": "LogNode"} for i in range(500)
        }
        connections = [
            {
                "source": f"node_{i}.exec_out",
                "target": f"node_{i+1}.exec_in",
            }
            for i in range(499)
        ]

        start = time.perf_counter()
        for _ in range(10):
            result = has_circular_dependency(nodes, connections)
        elapsed = time.perf_counter() - start

        assert result is False, "Linear graph should have no cycles"
        assert elapsed < 0.5, f"Cycle detection too slow: {elapsed:.3f}s"


class TestMemoryScaling:
    """Tests for memory usage scaling with node count."""

    @pytest.mark.skipif(
        True,
        reason="Requires psutil - run manually with psutil installed",
    )
    def test_node_memory_scaling(self):
        """Test memory usage scales linearly with node count."""
        try:
            import psutil

            process = psutil.Process()
        except ImportError:
            pytest.skip("psutil not installed")

        from casare_rpa.nodes.utility_nodes import LogNode

        # Baseline memory
        baseline = process.memory_info().rss

        # Create nodes
        nodes = []
        measurements = []
        for count in [100, 200, 300, 400, 500]:
            while len(nodes) < count:
                nodes.append(LogNode(node_id=f"mem_node_{len(nodes)}"))
            mem = process.memory_info().rss - baseline
            measurements.append((count, mem))

        # Check approximately linear scaling
        mem_100 = measurements[0][1]
        mem_500 = measurements[4][1]

        ratio = mem_500 / max(mem_100, 1)
        assert ratio < 10, f"Memory scaling suspicious: ratio={ratio:.1f}x"
