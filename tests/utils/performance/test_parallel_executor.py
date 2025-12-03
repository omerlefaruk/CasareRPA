"""
Tests for parallel executor utilities.

Covers:
- Dependency graph construction
- Ready node detection
- Independent group identification
- Parallel batch creation
- Parallel task execution
- Batch execution with error handling
- Workflow dependency analysis
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock

from casare_rpa.utils.performance.parallel_executor import (
    NodeDependencyInfo,
    DependencyGraph,
    ParallelExecutor,
    analyze_workflow_dependencies,
    identify_parallel_branches,
)
from casare_rpa.domain.value_objects.types import NodeId


class TestNodeDependencyInfo:
    """Tests for NodeDependencyInfo dataclass."""

    def test_initialization_defaults(self):
        """NodeDependencyInfo should initialize with empty sets."""
        node_id = NodeId("node1")
        info = NodeDependencyInfo(node_id=node_id)

        assert info.node_id == node_id
        assert info.dependencies == set()
        assert info.dependents == set()
        assert info.in_degree == 0

    def test_mutable_sets(self):
        """Dependencies and dependents should be mutable."""
        info = NodeDependencyInfo(node_id=NodeId("node1"))

        info.dependencies.add(NodeId("dep1"))
        info.dependents.add(NodeId("dep2"))

        assert NodeId("dep1") in info.dependencies
        assert NodeId("dep2") in info.dependents


class TestDependencyGraph:
    """Tests for DependencyGraph."""

    def test_initialization(self):
        """DependencyGraph should initialize empty."""
        graph = DependencyGraph()

        assert len(graph._nodes) == 0
        assert len(graph._adjacency) == 0

    def test_add_node_creates_dependency_info(self):
        """add_node should create NodeDependencyInfo."""
        graph = DependencyGraph()
        node_id = NodeId("node1")

        graph.add_node(node_id)

        assert node_id in graph._nodes
        assert graph._nodes[node_id].node_id == node_id

    def test_add_node_is_idempotent(self):
        """add_node should not overwrite existing nodes."""
        graph = DependencyGraph()
        node_id = NodeId("node1")

        graph.add_node(node_id)
        graph._nodes[node_id].in_degree = 5  # Modify
        graph.add_node(node_id)  # Re-add

        assert graph._nodes[node_id].in_degree == 5

    def test_add_edge_creates_dependency(self):
        """add_edge should establish dependency relationship."""
        graph = DependencyGraph()
        source = NodeId("source")
        target = NodeId("target")

        graph.add_edge(source, target)

        # Target depends on source
        assert source in graph._nodes[target].dependencies
        assert target in graph._nodes[source].dependents
        assert graph._nodes[target].in_degree == 1

    def test_add_edge_creates_nodes_if_missing(self):
        """add_edge should create nodes if they don't exist."""
        graph = DependencyGraph()
        source = NodeId("source")
        target = NodeId("target")

        graph.add_edge(source, target)

        assert source in graph._nodes
        assert target in graph._nodes

    def test_get_ready_nodes_with_no_dependencies(self):
        """get_ready_nodes should return nodes with all deps satisfied."""
        graph = DependencyGraph()
        node1 = NodeId("node1")
        node2 = NodeId("node2")
        node3 = NodeId("node3")

        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_edge(node1, node3)  # node3 depends on node1

        completed = set()
        ready = graph.get_ready_nodes(completed)

        # node1 and node2 have no dependencies, node3 waits for node1
        assert node1 in ready
        assert node2 in ready
        assert node3 not in ready

    def test_get_ready_nodes_with_completed_dependencies(self):
        """get_ready_nodes should include nodes with completed deps."""
        graph = DependencyGraph()
        node1 = NodeId("node1")
        node2 = NodeId("node2")

        graph.add_edge(node1, node2)  # node2 depends on node1

        completed = {node1}
        ready = graph.get_ready_nodes(completed)

        assert node2 in ready

    def test_get_ready_nodes_excludes_completed(self):
        """get_ready_nodes should exclude already completed nodes."""
        graph = DependencyGraph()
        node1 = NodeId("node1")
        node2 = NodeId("node2")

        graph.add_node(node1)
        graph.add_node(node2)

        completed = {node1}
        ready = graph.get_ready_nodes(completed)

        assert node1 not in ready
        assert node2 in ready

    def test_get_independent_groups_linear_chain(self):
        """get_independent_groups should handle linear dependency chains."""
        graph = DependencyGraph()
        node1 = NodeId("node1")
        node2 = NodeId("node2")
        node3 = NodeId("node3")

        graph.add_edge(node1, node2)
        graph.add_edge(node2, node3)

        groups = graph.get_independent_groups([node1])

        assert len(groups) >= 1
        # First group should be node1 (no deps)
        assert node1 in groups[0]

    def test_get_independent_groups_parallel_branches(self):
        """get_independent_groups should identify parallel branches."""
        graph = DependencyGraph()
        start = NodeId("start")
        branch_a = NodeId("branch_a")
        branch_b = NodeId("branch_b")
        end = NodeId("end")

        # start -> branch_a -> end
        # start -> branch_b -> end
        graph.add_edge(start, branch_a)
        graph.add_edge(start, branch_b)
        graph.add_edge(branch_a, end)
        graph.add_edge(branch_b, end)

        groups = graph.get_independent_groups([start])

        assert len(groups) >= 2
        # First group: start
        # Second group: branch_a and branch_b (parallel)
        # Third group: end

    def test_get_parallel_batches_respects_max_parallel(self):
        """get_parallel_batches should respect max_parallel limit."""
        graph = DependencyGraph()
        nodes = [NodeId(f"node{i}") for i in range(10)]

        for node in nodes:
            graph.add_node(node)

        batches = graph.get_parallel_batches(completed=set(), max_parallel=3)

        # All nodes are independent, should be batched
        for batch in batches:
            assert len(batch) <= 3

        # All nodes should be in batches
        all_nodes = set()
        for batch in batches:
            all_nodes.update(batch)
        assert len(all_nodes) == 10

    def test_get_parallel_batches_empty_when_all_completed(self):
        """get_parallel_batches should return empty when all completed."""
        graph = DependencyGraph()
        node1 = NodeId("node1")
        node2 = NodeId("node2")

        graph.add_node(node1)
        graph.add_node(node2)

        completed = {node1, node2}
        batches = graph.get_parallel_batches(completed, max_parallel=4)

        assert batches == [] or all(len(b) == 0 for b in batches)


class TestParallelExecutor:
    """Tests for ParallelExecutor."""

    def test_initialization_defaults(self):
        """ParallelExecutor should initialize with default settings."""
        executor = ParallelExecutor()

        assert executor._max_concurrency == 4
        assert executor._stop_on_error is True

    def test_initialization_custom_settings(self):
        """ParallelExecutor should accept custom settings."""
        executor = ParallelExecutor(max_concurrency=10, stop_on_error=False)

        assert executor._max_concurrency == 10
        assert executor._stop_on_error is False

    @pytest.mark.asyncio
    async def test_execute_parallel_empty_tasks(self):
        """execute_parallel should handle empty task list."""
        executor = ParallelExecutor()

        results = await executor.execute_parallel([])

        assert results == {}

    @pytest.mark.asyncio
    async def test_execute_parallel_single_task_success(self):
        """execute_parallel should execute single task successfully."""
        executor = ParallelExecutor()

        async def task():
            return "result"

        results = await executor.execute_parallel([("task1", task)])

        assert "task1" in results
        assert results["task1"] == (True, "result")

    @pytest.mark.asyncio
    async def test_execute_parallel_multiple_tasks_success(self):
        """execute_parallel should execute multiple tasks in parallel."""
        executor = ParallelExecutor()

        async def task1():
            await asyncio.sleep(0.05)
            return "result1"

        async def task2():
            await asyncio.sleep(0.05)
            return "result2"

        results = await executor.execute_parallel(
            [
                ("task1", task1),
                ("task2", task2),
            ]
        )

        assert results["task1"] == (True, "result1")
        assert results["task2"] == (True, "result2")

    @pytest.mark.asyncio
    async def test_execute_parallel_task_failure(self):
        """execute_parallel should handle task failures."""
        executor = ParallelExecutor(stop_on_error=False)

        async def failing_task():
            raise ValueError("Task failed")

        async def success_task():
            return "success"

        results = await executor.execute_parallel(
            [
                ("failing", failing_task),
                ("success", success_task),
            ]
        )

        assert results["failing"][0] is False
        assert "Task failed" in results["failing"][1]
        assert results["success"][0] is True

    @pytest.mark.asyncio
    async def test_execute_parallel_stop_on_error(self):
        """execute_parallel should stop other tasks on error when configured."""
        executor = ParallelExecutor(stop_on_error=True, max_concurrency=1)
        executed = []

        async def failing_task():
            executed.append("failing")
            raise ValueError("Task failed")

        async def second_task():
            await asyncio.sleep(0.1)
            executed.append("second")
            return "success"

        results = await executor.execute_parallel(
            [
                ("failing", failing_task),
                ("second", second_task),
            ]
        )

        # Failing task should have failed
        assert results["failing"][0] is False

    @pytest.mark.asyncio
    async def test_execute_parallel_respects_concurrency(self):
        """execute_parallel should respect max_concurrency limit."""
        executor = ParallelExecutor(max_concurrency=2)
        concurrent_count = []
        current = 0
        lock = asyncio.Lock()

        async def task():
            nonlocal current
            async with lock:
                current += 1
                concurrent_count.append(current)
            await asyncio.sleep(0.05)
            async with lock:
                current -= 1
            return "done"

        tasks = [(f"task{i}", task) for i in range(6)]
        await executor.execute_parallel(tasks)

        # Should never exceed max_concurrency
        assert max(concurrent_count) <= 2

    @pytest.mark.asyncio
    async def test_execute_batches_sequential_batches(self):
        """execute_batches should execute batches sequentially."""
        executor = ParallelExecutor()
        execution_order = []

        async def task(name):
            execution_order.append(name)
            return name

        batches = [
            [
                ("batch1_task1", lambda: task("b1t1")),
                ("batch1_task2", lambda: task("b1t2")),
            ],
            [("batch2_task1", lambda: task("b2t1"))],
        ]

        results = await executor.execute_batches(batches)

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_execute_batches_stops_on_error(self):
        """execute_batches should stop on error when configured."""
        executor = ParallelExecutor(stop_on_error=True)

        async def failing_task():
            raise ValueError("Batch 1 failed")

        async def success_task():
            return "success"

        batches = [
            [("failing", failing_task)],
            [("never_runs", success_task)],
        ]

        results = await executor.execute_batches(batches)

        # Should only have results from first batch
        assert len(results) == 1
        assert results[0]["failing"][0] is False


class TestAnalyzeWorkflowDependencies:
    """Tests for analyze_workflow_dependencies function."""

    def test_empty_workflow(self):
        """Should handle empty workflow."""
        graph = analyze_workflow_dependencies(nodes={}, connections=[])

        assert len(graph._nodes) == 0

    def test_nodes_added_to_graph(self):
        """All nodes should be added to graph."""
        nodes = {
            NodeId("node1"): Mock(),
            NodeId("node2"): Mock(),
            NodeId("node3"): Mock(),
        }

        graph = analyze_workflow_dependencies(nodes=nodes, connections=[])

        assert NodeId("node1") in graph._nodes
        assert NodeId("node2") in graph._nodes
        assert NodeId("node3") in graph._nodes

    def test_connections_create_edges(self):
        """Connections should create dependency edges."""
        nodes = {
            NodeId("node1"): Mock(),
            NodeId("node2"): Mock(),
        }

        connection = Mock()
        connection.source_node = NodeId("node1")
        connection.target_node = NodeId("node2")

        graph = analyze_workflow_dependencies(nodes=nodes, connections=[connection])

        # node2 depends on node1
        assert NodeId("node1") in graph._nodes[NodeId("node2")].dependencies


class TestIdentifyParallelBranches:
    """Tests for identify_parallel_branches function."""

    def test_no_successors(self):
        """Should return empty list when no successors."""
        graph = DependencyGraph()
        node = NodeId("node1")
        graph.add_node(node)

        branches = identify_parallel_branches(graph, node, [])

        assert branches == []

    def test_single_successor(self):
        """Should return single branch for single successor."""
        graph = DependencyGraph()
        source = NodeId("source")
        target = NodeId("target")
        graph.add_edge(source, target)

        connection = Mock()
        connection.source_node = source
        connection.target_node = target

        branches = identify_parallel_branches(graph, source, [connection])

        assert len(branches) == 1
        assert target in branches[0]

    def test_multiple_successors(self):
        """Should identify multiple parallel branches."""
        graph = DependencyGraph()
        source = NodeId("source")
        target1 = NodeId("target1")
        target2 = NodeId("target2")

        graph.add_edge(source, target1)
        graph.add_edge(source, target2)

        conn1 = Mock()
        conn1.source_node = source
        conn1.target_node = target1

        conn2 = Mock()
        conn2.source_node = source
        conn2.target_node = target2

        branches = identify_parallel_branches(graph, source, [conn1, conn2])

        assert len(branches) == 2


class TestParallelExecutionScenarios:
    """Integration tests for parallel execution scenarios."""

    @pytest.mark.asyncio
    async def test_diamond_dependency_pattern(self):
        """Test diamond dependency: A -> (B, C) -> D."""
        graph = DependencyGraph()
        a = NodeId("A")
        b = NodeId("B")
        c = NodeId("C")
        d = NodeId("D")

        graph.add_edge(a, b)
        graph.add_edge(a, c)
        graph.add_edge(b, d)
        graph.add_edge(c, d)

        # Initially only A is ready
        ready = graph.get_ready_nodes(set())
        assert a in ready
        assert b not in ready
        assert c not in ready
        assert d not in ready

        # After A completes, B and C are ready
        ready = graph.get_ready_nodes({a})
        assert b in ready
        assert c in ready
        assert d not in ready

        # After B and C complete, D is ready
        ready = graph.get_ready_nodes({a, b, c})
        assert d in ready

    @pytest.mark.asyncio
    async def test_parallel_execution_timing(self):
        """Tasks should actually run in parallel."""
        executor = ParallelExecutor(max_concurrency=10)

        async def slow_task():
            await asyncio.sleep(0.1)
            return "done"

        tasks = [(f"task{i}", slow_task) for i in range(5)]

        import time

        start = time.time()
        await executor.execute_parallel(tasks)
        elapsed = time.time() - start

        # 5 tasks at 0.1s each should take ~0.1s in parallel, not 0.5s
        assert elapsed < 0.3

    @pytest.mark.asyncio
    async def test_error_isolation(self):
        """Errors in one task should not affect others when stop_on_error=False."""
        executor = ParallelExecutor(stop_on_error=False, max_concurrency=10)
        completed = []

        async def failing_task():
            raise ValueError("fail")

        async def success_task(name):
            completed.append(name)
            return name

        tasks = [
            ("fail1", failing_task),
            ("success1", lambda: success_task("s1")),
            ("fail2", failing_task),
            ("success2", lambda: success_task("s2")),
        ]

        results = await executor.execute_parallel(tasks)

        assert results["fail1"][0] is False
        assert results["fail2"][0] is False
        assert results["success1"][0] is True
        assert results["success2"][0] is True
