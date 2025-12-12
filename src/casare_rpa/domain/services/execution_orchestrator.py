"""
CasareRPA - Domain Service: Execution Orchestrator
Pure business logic for workflow execution orchestration.

This is a PURE domain service with NO infrastructure dependencies:
- NO async/await
- NO Playwright
- NO EventBus
- NO resource management

Handles:
- Connection traversal logic
- Control flow decisions (if/else, loops, branches)
- Execution path calculation (Run-To-Node feature)
- Dependency analysis
"""

from collections import deque
from typing import Any, Dict, List, Optional, Set

import logging

logger = logging.getLogger(__name__)

from casare_rpa.domain.entities.workflow import WorkflowSchema
from casare_rpa.domain.value_objects.types import NodeId


# Pre-computed set of control flow node types (module-level constant for O(1) lookup)
CONTROL_FLOW_TYPES = frozenset(
    {
        "IfNode",
        "SwitchNode",
        "ForLoopStartNode",
        "ForLoopEndNode",
        "WhileLoopStartNode",
        "WhileLoopEndNode",
        "BreakNode",
        "ContinueNode",
        "TryNode",
        "CatchNode",
        "RetryNode",
    }
)


class ExecutionOrchestrator:
    """
    Domain service for workflow execution logic.

    Responsibilities:
    - Determine execution order based on connections
    - Handle control flow (loops, branches, try/catch)
    - Track execution path
    - Calculate subgraphs for Run-To-Node

    Does NOT:
    - Execute nodes (that's infrastructure)
    - Manage resources (that's infrastructure)
    - Emit events (that's application layer)
    """

    def __init__(self, workflow: WorkflowSchema) -> None:
        """
        Initialize execution orchestrator.

        Args:
            workflow: Workflow schema with nodes and connections
        """
        self.workflow = workflow
        self._execution_graph: Optional[Dict[NodeId, List[NodeId]]] = None

        # PERFORMANCE: Build connection index maps for O(1) lookups
        # Instead of O(n) scans through all connections for every node execution
        self._outgoing_connections: Dict[NodeId, List] = {}
        self._incoming_connections: Dict[NodeId, List] = {}
        self._port_connections: Dict[
            tuple, List
        ] = {}  # (node_id, port_name) -> connections
        self._build_connection_indexes()

    def _build_connection_indexes(self) -> None:
        """
        Build connection index maps for O(1) lookups.

        Replaces O(n) scans through all connections with dict lookups.
        """
        self._outgoing_connections.clear()
        self._incoming_connections.clear()
        self._port_connections.clear()

        for conn in self.workflow.connections:
            # Index by source node (outgoing)
            if conn.source_node not in self._outgoing_connections:
                self._outgoing_connections[conn.source_node] = []
            self._outgoing_connections[conn.source_node].append(conn)

            # Index by target node (incoming)
            if conn.target_node not in self._incoming_connections:
                self._incoming_connections[conn.target_node] = []
            self._incoming_connections[conn.target_node].append(conn)

            # Index by (source_node, source_port) for port-specific lookups
            port_key = (conn.source_node, conn.source_port)
            if port_key not in self._port_connections:
                self._port_connections[port_key] = []
            self._port_connections[port_key].append(conn)

    def find_start_node(self) -> Optional[NodeId]:
        """
        Find the workflow entry point (StartNode or TriggerNode).

        Trigger nodes are also valid entry points as they start workflows.

        Returns:
            Node ID of entry point, or None if not found
        """
        trigger_node_id = None

        for node_id, node_data in self.workflow.nodes.items():
            # Handle both dict (serialized) and node instance formats
            if isinstance(node_data, dict):
                # Support both "node_type" and "type" keys for compatibility
                node_type = node_data.get("node_type") or node_data.get("type", "")
            else:
                # Node instance - check node_type attribute
                node_type = getattr(node_data, "node_type", "")

            # Prefer StartNode if present
            if node_type == "StartNode":
                logger.debug(f"Found StartNode: {node_id}")
                return node_id

            # Track trigger nodes as alternative entry points
            if node_type.endswith("TriggerNode"):
                trigger_node_id = node_id
                logger.debug(f"Found trigger node: {node_id} ({node_type})")

        # If no StartNode, use trigger node
        if trigger_node_id:
            logger.debug(f"Using trigger node as entry point: {trigger_node_id}")
            return trigger_node_id

        logger.warning("No StartNode or TriggerNode found in workflow")
        return None

    def find_all_start_nodes(self) -> List[NodeId]:
        """
        Find all StartNodes in workflow for parallel execution.

        Unlike find_start_node() which returns the first one, this returns
        all StartNodes to enable multi-workflow parallel execution.

        Returns:
            List of all StartNode IDs in the workflow
        """
        start_nodes: List[NodeId] = []

        for node_id, node_data in self.workflow.nodes.items():
            # Handle both dict (serialized) and node instance formats
            if isinstance(node_data, dict):
                node_type = node_data.get("node_type") or node_data.get("type", "")
            else:
                node_type = getattr(node_data, "node_type", "")

            if node_type == "StartNode":
                start_nodes.append(node_id)

        logger.debug(f"Found {len(start_nodes)} StartNodes in workflow")
        return start_nodes

    def find_trigger_node(self) -> Optional[NodeId]:
        """
        Find the trigger node in workflow (if any).

        Returns:
            Node ID of trigger node, or None if not found
        """
        for node_id, node_data in self.workflow.nodes.items():
            if isinstance(node_data, dict):
                node_type = node_data.get("node_type") or node_data.get("type", "")
            else:
                node_type = getattr(node_data, "node_type", "")

            if node_type.endswith("TriggerNode"):
                logger.debug(f"Found trigger node: {node_id} ({node_type})")
                return node_id

        return None

    def is_trigger_node(self, node_id: NodeId) -> bool:
        """
        Check if a node is a trigger node.

        Args:
            node_id: Node ID to check

        Returns:
            True if the node is a trigger node
        """
        node_type = self.get_node_type(node_id)
        return node_type.endswith("TriggerNode")

    def get_next_nodes(
        self, current_node_id: NodeId, execution_result: Optional[Dict[str, Any]] = None
    ) -> List[NodeId]:
        """
        Determine next nodes to execute based on connections and result.

        Validates that specified ports have connections and logs warnings if not.

        Handles:
        - Dynamic routing (next_nodes in result)
        - Control flow (break, continue)
        - Default routing (all exec_out connections)

        Args:
            current_node_id: ID of current node
            execution_result: Result from node execution

        Returns:
            List of next node IDs to execute
        """
        next_nodes: List[NodeId] = []

        # Check for dynamic routing (control flow nodes return next_nodes)
        if execution_result and "next_nodes" in execution_result:
            next_port_names = execution_result["next_nodes"]
            logger.debug(
                f"Dynamic routing from {current_node_id}: ports={next_port_names}"
            )

            # Find connections from specified ports with validation
            for port_name in next_port_names:
                connections = self._get_connections_from_port(
                    current_node_id, port_name
                )

                if not connections:
                    # Log warning for missing connections
                    if port_name == "exec_out":
                        logger.debug(
                            f"Node {current_node_id} exec_out has no connections - "
                            f"execution path ends here"
                        )
                    else:
                        logger.warning(
                            f"Node {current_node_id} specified next port '{port_name}' "
                            f"but no connections found. Workflow may have incomplete connections."
                        )
                    continue

                # Add connected node IDs
                for connection in connections:
                    if connection.target_node not in next_nodes:
                        next_nodes.append(connection.target_node)
                        logger.debug(
                            f"  Route: {current_node_id}.{port_name} -> {connection.target_node}"
                        )

            if not next_nodes and next_port_names:
                logger.info(
                    f"Node {current_node_id} completed with no next nodes to execute "
                    f"(end of branch)"
                )

            return next_nodes

        # Default routing: follow all exec_out connections (using pre-built index)
        for connection in self._outgoing_connections.get(current_node_id, []):
            # Only follow execution connections (not data connections)
            if "exec" in connection.source_port.lower():
                next_nodes.append(connection.target_node)
                logger.debug(
                    f"Exec connection: {current_node_id} -> {connection.target_node}"
                )

        return next_nodes

    def _get_connections_from_port(self, node_id: NodeId, port_name: str) -> List:
        """
        Get all connections originating from a specific port.

        Uses pre-built index for O(1) lookup instead of O(n) scan.

        Args:
            node_id: Source node ID
            port_name: Source port name

        Returns:
            List of connections from the specified port
        """
        return self._port_connections.get((node_id, port_name), [])

    def calculate_execution_path(
        self, start_node_id: NodeId, target_node_id: Optional[NodeId] = None
    ) -> Set[NodeId]:
        """
        Calculate the execution path from start to target (or all nodes).

        Uses BFS to find all nodes reachable from start.
        If target is specified, finds all nodes on paths to target (subgraph).

        Args:
            start_node_id: Starting node ID
            target_node_id: Optional target node ID (Run-To-Node)

        Returns:
            Set of node IDs in the execution path
        """
        if target_node_id:
            # Calculate subgraph: nodes on paths from start to target
            return self._calculate_subgraph(start_node_id, target_node_id)

        # Calculate full reachable graph (using pre-built index)
        reachable: Set[NodeId] = set()
        queue: deque[NodeId] = deque([start_node_id])
        reachable.add(start_node_id)

        while queue:
            current = queue.popleft()

            # Find all connected nodes (O(1) lookup instead of O(n) scan)
            for connection in self._outgoing_connections.get(current, []):
                target = connection.target_node
                if target not in reachable:
                    reachable.add(target)
                    queue.append(target)

        logger.info(f"Calculated execution path: {len(reachable)} nodes reachable")
        return reachable

    def _calculate_subgraph(
        self, start_node_id: NodeId, target_node_id: NodeId
    ) -> Set[NodeId]:
        """
        Calculate subgraph of nodes required to reach target from start.

        Uses BFS from start, tracking all nodes until target is reached.
        Then backtraces to find all nodes on paths to target.

        Args:
            start_node_id: Starting node ID
            target_node_id: Target node ID

        Returns:
            Set of node IDs on paths from start to target
        """
        # First, check if target is reachable
        if not self.is_reachable(start_node_id, target_node_id):
            logger.error(
                f"Target {target_node_id} is not reachable from {start_node_id}"
            )
            return set()

        # Build reverse graph for backtracking (using pre-built index)
        predecessors: Dict[NodeId, Set[NodeId]] = {}
        queue: deque[NodeId] = deque([start_node_id])
        visited: Set[NodeId] = {start_node_id}

        # BFS to build predecessor map (O(1) lookup per node)
        while queue:
            current = queue.popleft()

            for connection in self._outgoing_connections.get(current, []):
                target = connection.target_node

                # Track predecessors
                if target not in predecessors:
                    predecessors[target] = set()
                predecessors[target].add(current)

                if target not in visited:
                    visited.add(target)
                    queue.append(target)

        # Backtrace from target to start to find all nodes on paths
        subgraph: Set[NodeId] = {target_node_id}
        backtrack_queue: deque[NodeId] = deque([target_node_id])

        while backtrack_queue:
            current = backtrack_queue.popleft()

            if current in predecessors:
                for pred in predecessors[current]:
                    if pred not in subgraph:
                        subgraph.add(pred)
                        backtrack_queue.append(pred)

        logger.info(
            f"Subgraph calculated: {len(subgraph)} nodes from {start_node_id} to {target_node_id}"
        )
        return subgraph

    def is_reachable(self, start_node_id: NodeId, target_node_id: NodeId) -> bool:
        """
        Check if target node is reachable from start node.

        Uses BFS to determine reachability.

        Args:
            start_node_id: Starting node ID
            target_node_id: Target node ID

        Returns:
            True if target is reachable from start
        """
        if start_node_id == target_node_id:
            return True

        visited: Set[NodeId] = {start_node_id}
        queue: deque[NodeId] = deque([start_node_id])

        while queue:
            current = queue.popleft()

            # O(1) lookup instead of O(n) scan
            for connection in self._outgoing_connections.get(current, []):
                target = connection.target_node

                if target == target_node_id:
                    return True

                if target not in visited:
                    visited.add(target)
                    queue.append(target)

        return False

    def should_stop_on_error(self, error: Exception, settings: Dict[str, Any]) -> bool:
        """
        Decide if error should halt execution.

        Business logic for error handling:
        - Check continue_on_error setting
        - Check error severity
        - Check if error is in try block

        Args:
            error: Exception that occurred
            settings: Workflow settings

        Returns:
            True if execution should stop
        """
        continue_on_error = settings.get("continue_on_error", False)

        if continue_on_error:
            logger.warning(f"Error occurred but continue_on_error is enabled: {error}")
            return False

        # In future, could check error severity/type
        # For now, stop on all errors unless continue_on_error is set
        return True

    def handle_control_flow(
        self, node_id: NodeId, result: Dict[str, Any]
    ) -> Optional[str]:
        """
        Process control flow signals (break/continue/return).

        Args:
            node_id: ID of node that returned result
            result: Execution result

        Returns:
            Control flow signal name or None
        """
        control_flow = result.get("control_flow")

        if control_flow in ("break", "continue", "return"):
            logger.debug(f"Control flow signal from {node_id}: {control_flow}")
            return control_flow

        return None

    def build_dependency_graph(self) -> Dict[NodeId, Set[NodeId]]:
        """
        Build execution dependency graph.

        Creates a directed graph where each node maps to its dependencies
        (nodes that must execute before it).

        Returns:
            Dictionary mapping node_id -> set of dependency node_ids
        """
        if self._execution_graph is not None:
            return self._execution_graph

        dependencies: Dict[NodeId, Set[NodeId]] = {}

        # Initialize all nodes with empty dependencies
        for node_id in self.workflow.nodes:
            dependencies[node_id] = set()

        # Build dependencies from connections
        for connection in self.workflow.connections:
            target = connection.target_node
            source = connection.source_node

            # Target depends on source
            dependencies[target].add(source)

        self._execution_graph = dependencies
        logger.debug(f"Dependency graph built: {len(dependencies)} nodes")

        return dependencies

    def validate_execution_order(self) -> tuple[bool, List[str]]:
        """
        Ensure no circular dependencies in workflow.

        Uses topological sort to detect cycles.

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors: List[str] = []

        # Build dependency graph
        dependencies = self.build_dependency_graph()

        # Try topological sort
        in_degree: Dict[NodeId, int] = {
            node_id: len(deps) for node_id, deps in dependencies.items()
        }

        queue: deque[NodeId] = deque(
            [node_id for node_id, degree in in_degree.items() if degree == 0]
        )

        sorted_count = 0

        while queue:
            current = queue.popleft()
            sorted_count += 1

            # Find nodes that depend on current
            for node_id, deps in dependencies.items():
                if current in deps:
                    in_degree[node_id] -= 1
                    if in_degree[node_id] == 0:
                        queue.append(node_id)

        # If not all nodes were sorted, there's a cycle
        if sorted_count != len(self.workflow.nodes):
            errors.append(
                f"Circular dependency detected: {len(self.workflow.nodes) - sorted_count} nodes in cycle"
            )
            logger.error("Workflow has circular dependencies")
            return False, errors

        logger.debug("Workflow execution order validated: no circular dependencies")
        return True, []

    def find_try_body_nodes(self, try_node_id: NodeId) -> Set[NodeId]:
        """
        Find all nodes reachable from a try node's try_body output.

        Used to track which nodes are inside a try block for error routing.

        Args:
            try_node_id: ID of try node

        Returns:
            Set of node IDs in try body
        """
        body_nodes: Set[NodeId] = set()
        queue: deque[NodeId] = deque()

        # Find nodes connected to try_body port (O(1) lookup)
        for connection in self._port_connections.get((try_node_id, "try_body"), []):
            queue.append(connection.target_node)

        # BFS to find all reachable nodes
        while queue:
            node_id = queue.popleft()

            if node_id == try_node_id or node_id in body_nodes:
                continue

            body_nodes.add(node_id)

            # Add connected nodes (O(1) lookup)
            for connection in self._outgoing_connections.get(node_id, []):
                if connection.target_node != try_node_id:
                    queue.append(connection.target_node)

        logger.debug(f"Try {try_node_id} body: {len(body_nodes)} nodes")
        return body_nodes

    def get_node_type(self, node_id: NodeId) -> str:
        """
        Get the type of a node.

        Args:
            node_id: Node ID

        Returns:
            Node type name, or empty string if not found
        """
        node_data = self.workflow.nodes.get(node_id)
        if node_data:
            # Handle both dict (serialized) and node instance formats
            if isinstance(node_data, dict):
                # Support both "node_type" and "type" keys for compatibility
                return node_data.get("node_type") or node_data.get("type", "")
            else:
                # Node instance - check node_type attribute
                return getattr(node_data, "node_type", "")
        return ""

    def is_control_flow_node(self, node_id: NodeId) -> bool:
        """
        Check if a node is a control flow node.

        Control flow nodes affect execution routing:
        - IfNode, SwitchNode
        - ForLoopStartNode, WhileLoopStartNode
        - BreakNode, ContinueNode
        - TryNode, CatchNode

        Uses module-level CONTROL_FLOW_TYPES frozenset for O(1) lookup
        without recreating the set on every call.

        Args:
            node_id: Node ID

        Returns:
            True if node is a control flow node
        """
        node_type = self.get_node_type(node_id)
        return node_type in CONTROL_FLOW_TYPES

    def find_loop_body_nodes(
        self, loop_start_id: NodeId, loop_end_id: NodeId
    ) -> Set[NodeId]:
        """
        Find all nodes in a loop body between start and end nodes.

        Used to clear executed_nodes when looping back so body nodes
        can re-execute on each iteration.

        Args:
            loop_start_id: ForLoopStartNode or WhileLoopStartNode ID
            loop_end_id: ForLoopEndNode or WhileLoopEndNode ID

        Returns:
            Set of node IDs that are inside the loop body
        """
        body_nodes: Set[NodeId] = set()

        # BFS from loop start's body port to find all reachable nodes
        # until we hit the loop end
        queue: deque[NodeId] = deque()

        # Find the first node connected to loop_start's body port (O(1) lookup)
        # Note: ForLoopStartNode and WhileLoopStartNode use "body" as port name
        for connection in self._port_connections.get((loop_start_id, "body"), []):
            queue.append(connection.target_node)
            body_nodes.add(connection.target_node)

        # BFS to find all body nodes
        while queue:
            current = queue.popleft()

            # Don't traverse past loop end
            if current == loop_end_id:
                continue

            # Find all nodes connected from this node (O(1) lookup)
            for connection in self._outgoing_connections.get(current, []):
                target = connection.target_node

                if target not in body_nodes:
                    body_nodes.add(target)
                    queue.append(target)

        # Remove loop end from body nodes (it's a control flow node, handled separately)
        body_nodes.discard(loop_end_id)

        logger.debug(
            f"Found {len(body_nodes)} loop body nodes between "
            f"{loop_start_id} and {loop_end_id}"
        )
        return body_nodes

    def get_all_nodes(self) -> List[NodeId]:
        """
        Get all node IDs in the workflow.

        Returns:
            List of all node IDs
        """
        return list(self.workflow.nodes.keys())

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ExecutionOrchestrator("
            f"workflow='{self.workflow.metadata.name}', "
            f"nodes={len(self.workflow.nodes)}, "
            f"connections={len(self.workflow.connections)})"
        )
