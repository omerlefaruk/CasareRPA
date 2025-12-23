"""
Parallel execution utilities for CasareRPA workflow runner.

Provides dependency analysis and parallel execution capabilities
for independent workflow branches.
"""

import asyncio
from collections import defaultdict
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from typing import Any

from loguru import logger

from casare_rpa.domain.value_objects.types import NodeId


@dataclass
class NodeDependencyInfo:
    """Dependency information for a node."""

    node_id: NodeId
    dependencies: set[NodeId] = field(default_factory=set)  # Nodes this depends on
    dependents: set[NodeId] = field(default_factory=set)  # Nodes that depend on this
    in_degree: int = 0  # Number of unresolved dependencies


class DependencyGraph:
    """
    Analyzes workflow structure to determine node dependencies
    and identify independent branches that can run in parallel.
    """

    def __init__(self) -> None:
        """Initialize dependency graph."""
        self._nodes: dict[NodeId, NodeDependencyInfo] = {}
        self._adjacency: dict[NodeId, set[NodeId]] = defaultdict(set)

    def add_node(self, node_id: NodeId) -> None:
        """Add a node to the graph."""
        if node_id not in self._nodes:
            self._nodes[node_id] = NodeDependencyInfo(node_id=node_id)

    def add_edge(self, source: NodeId, target: NodeId) -> None:
        """
        Add a directed edge from source to target.
        This means target depends on source.
        """
        self.add_node(source)
        self.add_node(target)

        self._adjacency[source].add(target)
        self._nodes[target].dependencies.add(source)
        self._nodes[source].dependents.add(target)
        self._nodes[target].in_degree += 1

    def get_ready_nodes(self, completed: set[NodeId]) -> list[NodeId]:
        """
        Get nodes that are ready to execute (all dependencies satisfied).

        Args:
            completed: Set of already completed node IDs

        Returns:
            List of node IDs ready to execute
        """
        ready = []
        for node_id, info in self._nodes.items():
            if node_id in completed:
                continue
            # Check if all dependencies are completed
            if info.dependencies.issubset(completed):
                ready.append(node_id)
        return ready

    def get_independent_groups(self, starting_nodes: list[NodeId]) -> list[list[NodeId]]:
        """
        Find groups of independent nodes that can execute in parallel.

        Uses topological sorting with level detection to group nodes
        that have no dependencies on each other.

        Args:
            starting_nodes: Initial nodes to process

        Returns:
            List of groups, where each group contains independent nodes
        """
        # Build in-degree map for nodes reachable from starting_nodes
        in_degree: dict[NodeId, int] = {}
        reachable: set[NodeId] = set()

        # BFS to find all reachable nodes
        queue = list(starting_nodes)
        while queue:
            node_id = queue.pop(0)
            if node_id in reachable:
                continue
            reachable.add(node_id)
            for neighbor in self._adjacency.get(node_id, set()):
                queue.append(neighbor)

        # Calculate in-degrees for reachable nodes
        for node_id in reachable:
            in_degree[node_id] = 0
        for node_id in reachable:
            for neighbor in self._adjacency.get(node_id, set()):
                if neighbor in reachable:
                    in_degree[neighbor] = in_degree.get(neighbor, 0) + 1

        # Kahn's algorithm with level tracking
        groups: list[list[NodeId]] = []
        current_level = [n for n in starting_nodes if n in reachable and in_degree.get(n, 0) == 0]

        while current_level:
            groups.append(current_level)
            next_level = []

            for node_id in current_level:
                for neighbor in self._adjacency.get(node_id, set()):
                    if neighbor not in reachable:
                        continue
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        next_level.append(neighbor)

            current_level = next_level

        return groups

    def get_parallel_batches(
        self, completed: set[NodeId], max_parallel: int = 4
    ) -> list[list[NodeId]]:
        """
        Get batches of nodes that can be executed in parallel.

        Args:
            completed: Set of completed node IDs
            max_parallel: Maximum nodes to run in parallel

        Returns:
            List of batches, each containing nodes that can run together
        """
        ready = self.get_ready_nodes(completed)

        # Split into batches respecting max_parallel
        batches = []
        for i in range(0, len(ready), max_parallel):
            batches.append(ready[i : i + max_parallel])

        return batches


class ParallelExecutor:
    """
    Executes tasks in parallel with configurable concurrency.

    Features:
    - Configurable max concurrency
    - Error handling and result collection
    - Support for async tasks
    """

    def __init__(
        self,
        max_concurrency: int = 4,
        stop_on_error: bool = True,
    ) -> None:
        """
        Initialize parallel executor.

        Args:
            max_concurrency: Maximum number of concurrent tasks
            stop_on_error: If True, stop all tasks when one fails
        """
        self._max_concurrency = max_concurrency
        self._stop_on_error = stop_on_error
        self._semaphore: asyncio.Semaphore | None = None

    async def execute_parallel(
        self,
        tasks: list[tuple[str, Callable[[], Coroutine[Any, Any, Any]]]],
    ) -> dict[str, tuple[bool, Any]]:
        """
        Execute multiple tasks in parallel.

        Args:
            tasks: List of (task_id, async_callable) tuples

        Returns:
            Dictionary mapping task_id to (success, result) tuples
        """
        if not tasks:
            return {}

        self._semaphore = asyncio.Semaphore(self._max_concurrency)
        results: dict[str, tuple[bool, Any]] = {}
        errors: list[str] = []

        async def run_task(task_id: str, coro_func: Callable) -> None:
            """Run a single task with semaphore control."""
            async with self._semaphore:
                if self._stop_on_error and errors:
                    # Another task already failed
                    results[task_id] = (False, "Cancelled due to other task failure")
                    return

                try:
                    result = await coro_func()
                    results[task_id] = (True, result)
                except Exception as e:
                    logger.error(f"Task {task_id} failed: {e}")
                    results[task_id] = (False, str(e))
                    if self._stop_on_error:
                        errors.append(task_id)

        # Create and run all tasks
        async_tasks = [run_task(task_id, coro_func) for task_id, coro_func in tasks]

        # Wait for all tasks with gather
        await asyncio.gather(*async_tasks, return_exceptions=True)

        return results

    async def execute_batches(
        self,
        batches: list[list[tuple[str, Callable[[], Coroutine[Any, Any, Any]]]]],
    ) -> list[dict[str, tuple[bool, Any]]]:
        """
        Execute batches of tasks sequentially, with tasks within each batch running in parallel.

        Args:
            batches: List of task batches

        Returns:
            List of result dictionaries for each batch
        """
        all_results = []

        for batch in batches:
            batch_results = await self.execute_parallel(batch)
            all_results.append(batch_results)

            # Check for errors if stop_on_error is enabled
            if self._stop_on_error:
                for task_id, (success, _) in batch_results.items():
                    if not success:
                        logger.warning(f"Stopping batch execution due to error in {task_id}")
                        return all_results

        return all_results


def analyze_workflow_dependencies(
    nodes: dict[NodeId, Any],
    connections: list[Any],
) -> DependencyGraph:
    """
    Analyze a workflow to build its dependency graph.

    Args:
        nodes: Dictionary of node_id -> node
        connections: List of NodeConnection objects

    Returns:
        DependencyGraph with all dependencies mapped
    """
    graph = DependencyGraph()

    # Add all nodes
    for node_id in nodes:
        graph.add_node(node_id)

    # Add edges from connections
    for conn in connections:
        # Connection goes source -> target, meaning target depends on source
        graph.add_edge(conn.source_node, conn.target_node)

    return graph


def identify_parallel_branches(
    graph: DependencyGraph,
    from_node: NodeId,
    connections: list[Any],
) -> list[list[NodeId]]:
    """
    Identify branches from a node that can execute in parallel.

    Args:
        graph: The dependency graph
        from_node: Node to find branches from
        connections: All workflow connections

    Returns:
        List of branch paths that are independent
    """
    # Find all direct successors
    successors = []
    for conn in connections:
        if conn.source_node == from_node:
            if conn.target_node not in successors:
                successors.append(conn.target_node)

    if len(successors) <= 1:
        # No parallelism possible
        return [successors] if successors else []

    # Check if successors are truly independent (no shared dependencies)
    branches: list[list[NodeId]] = []

    for successor in successors:
        branches.append([successor])

    return branches
