"""
CasareRPA - Subgraph Calculator
Calculates the minimal subgraph required for "Run To Node" execution.
"""

from collections import deque
from typing import Any, Dict, List, Optional, Set

from loguru import logger

from ...core.types import NodeId
from ...core.workflow_schema import NodeConnection


class SubgraphCalculator:
    """
    Calculates the minimal subgraph required to execute from start to target node.

    This is used for the "Run To Node" (F4) feature to determine which nodes
    need to be executed to reach a target node from the start node.

    Algorithm:
    1. Find all predecessors of target (nodes that can reach target)
    2. Find all successors of start (nodes reachable from start)
    3. Subgraph = intersection of predecessors and successors

    This gives us exactly the nodes on all paths from start to target.
    """

    def __init__(
        self,
        nodes: Dict[NodeId, Any],
        connections: List[NodeConnection],
    ) -> None:
        """
        Initialize the subgraph calculator.

        Args:
            nodes: Dictionary of node IDs to node data
            connections: List of connections between nodes
        """
        self._nodes = nodes
        self._connections = connections

        # Build adjacency lists for graph traversal
        self._forward_edges: Dict[NodeId, Set[NodeId]] = {}
        self._backward_edges: Dict[NodeId, Set[NodeId]] = {}
        self._build_adjacency_lists()

    def _build_adjacency_lists(self) -> None:
        """Build forward and backward adjacency lists from connections."""
        # Initialize empty sets for all nodes
        for node_id in self._nodes:
            self._forward_edges[node_id] = set()
            self._backward_edges[node_id] = set()

        # Build edges from connections
        for conn in self._connections:
            source = conn.source_node
            target = conn.target_node

            # Only add edges for nodes that exist
            if source in self._nodes and target in self._nodes:
                self._forward_edges[source].add(target)
                self._backward_edges[target].add(source)

        logger.debug(
            f"Built adjacency lists: {len(self._nodes)} nodes, "
            f"{sum(len(edges) for edges in self._forward_edges.values())} edges"
        )

    def get_predecessors(self, node_id: NodeId) -> Set[NodeId]:
        """
        Get all nodes that can reach the given node (backwards BFS).

        This traverses the graph backwards from the target to find all
        nodes that have a path leading to it.

        Args:
            node_id: The target node ID

        Returns:
            Set of all node IDs that can reach the target (including target itself)
        """
        if node_id not in self._nodes:
            logger.warning(f"Node {node_id} not found in graph")
            return set()

        visited: Set[NodeId] = set()
        queue = deque([node_id])

        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)

            # Add all predecessors (nodes with edges TO current)
            for source in self._backward_edges.get(current, set()):
                if source not in visited:
                    queue.append(source)

        return visited

    def get_successors(self, node_id: NodeId) -> Set[NodeId]:
        """
        Get all nodes reachable from the given node (forward BFS).

        This traverses the graph forwards from the start to find all
        nodes that can be reached from it.

        Args:
            node_id: The start node ID

        Returns:
            Set of all node IDs reachable from start (including start itself)
        """
        if node_id not in self._nodes:
            logger.warning(f"Node {node_id} not found in graph")
            return set()

        visited: Set[NodeId] = set()
        queue = deque([node_id])

        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)

            # Add all successors (nodes with edges FROM current)
            for target in self._forward_edges.get(current, set()):
                if target not in visited:
                    queue.append(target)

        return visited

    def calculate_subgraph(
        self,
        start_node_id: NodeId,
        target_node_id: NodeId,
    ) -> Set[NodeId]:
        """
        Calculate the subgraph of nodes required to reach target from start.

        The subgraph contains exactly the nodes that are:
        1. Reachable from the start node, AND
        2. Can reach the target node

        This is the intersection of successors(start) and predecessors(target).

        Args:
            start_node_id: The start node (usually StartNode)
            target_node_id: The target node to run to

        Returns:
            Set of node IDs that form the execution subgraph
        """
        if start_node_id not in self._nodes:
            logger.error(f"Start node {start_node_id} not found in graph")
            return set()

        if target_node_id not in self._nodes:
            logger.error(f"Target node {target_node_id} not found in graph")
            return set()

        # Get all predecessors of target (nodes that can reach target)
        predecessors = self.get_predecessors(target_node_id)

        # Get all successors of start (nodes reachable from start)
        successors = self.get_successors(start_node_id)

        # Subgraph is the intersection
        subgraph = predecessors.intersection(successors)

        # Ensure start and target are included
        subgraph.add(start_node_id)
        subgraph.add(target_node_id)

        logger.info(
            f"Calculated subgraph: {len(subgraph)} nodes "
            f"(from {start_node_id} to {target_node_id})"
        )
        logger.debug(f"Subgraph nodes: {subgraph}")

        return subgraph

    def is_reachable(self, start_node_id: NodeId, target_node_id: NodeId) -> bool:
        """
        Check if target node is reachable from start node.

        Args:
            start_node_id: The start node
            target_node_id: The target node

        Returns:
            True if there is a path from start to target
        """
        if start_node_id not in self._nodes or target_node_id not in self._nodes:
            return False

        successors = self.get_successors(start_node_id)
        return target_node_id in successors

    def get_execution_order(
        self,
        start_node_id: NodeId,
        target_node_id: NodeId,
    ) -> Optional[List[NodeId]]:
        """
        Get a valid topological execution order for the subgraph.

        This provides an ordering where all dependencies are executed
        before the nodes that depend on them.

        Args:
            start_node_id: The start node
            target_node_id: The target node

        Returns:
            List of node IDs in execution order, or None if not reachable
        """
        subgraph = self.calculate_subgraph(start_node_id, target_node_id)
        if not subgraph:
            return None

        # Kahn's algorithm for topological sort within subgraph
        in_degree: Dict[NodeId, int] = {node: 0 for node in subgraph}

        # Calculate in-degrees for subgraph nodes only
        for node_id in subgraph:
            for predecessor in self._backward_edges.get(node_id, set()):
                if predecessor in subgraph:
                    in_degree[node_id] += 1

        # Start with nodes that have no dependencies in the subgraph
        queue = deque([node for node, degree in in_degree.items() if degree == 0])
        result: List[NodeId] = []

        while queue:
            current = queue.popleft()
            result.append(current)

            # Decrease in-degree of successors
            for successor in self._forward_edges.get(current, set()):
                if successor in subgraph:
                    in_degree[successor] -= 1
                    if in_degree[successor] == 0:
                        queue.append(successor)

        # Check for cycles (if result doesn't contain all subgraph nodes)
        if len(result) != len(subgraph):
            logger.warning("Cycle detected in subgraph - using BFS order")
            # Fall back to BFS order from start
            return list(self.get_successors(start_node_id) & subgraph)

        return result
