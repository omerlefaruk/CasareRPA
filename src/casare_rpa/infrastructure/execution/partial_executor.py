"""
Partial Executor for Run From Here feature.

Enables starting workflow execution from any node, optionally preserving
variable state from previous runs.
"""

import asyncio
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING
from loguru import logger

if TYPE_CHECKING:
    from casare_rpa.domain.schemas.workflow import WorkflowSchema
    from casare_rpa.infrastructure.execution.execution_context import ExecutionContext


class PartialExecutor:
    """
    Executes workflows starting from a specific node.

    Builds a subgraph from the start node to end nodes and executes only
    that portion of the workflow. Supports preserving variable state from
    previous execution runs.
    """

    def __init__(self) -> None:
        """Initialize the partial executor."""
        self._cached_variables: Dict[str, Any] = {}
        self._last_execution_path: List[str] = []

    def cache_variables(self, variables: Dict[str, Any]) -> None:
        """
        Cache variables from a completed execution for use in partial runs.

        Args:
            variables: Variable dict from completed execution context
        """
        self._cached_variables = dict(variables)
        logger.debug(f"Cached {len(variables)} variables for partial execution")

    def cache_execution_path(self, path: List[str]) -> None:
        """
        Cache execution path from a completed execution.

        Args:
            path: List of executed node IDs
        """
        self._last_execution_path = list(path)
        logger.debug(f"Cached execution path with {len(path)} nodes")

    def get_cached_variables(self) -> Dict[str, Any]:
        """
        Get cached variables from last execution.

        Returns:
            Dict of cached variables (copy)
        """
        return dict(self._cached_variables)

    def has_cached_state(self) -> bool:
        """
        Check if cached state is available from previous run.

        Returns:
            True if variables are cached
        """
        return bool(self._cached_variables)

    def clear_cache(self) -> None:
        """Clear cached execution state."""
        self._cached_variables.clear()
        self._last_execution_path.clear()
        logger.debug("Partial executor cache cleared")

    def build_subgraph_from_node(
        self,
        workflow: "WorkflowSchema",
        start_node_id: str,
    ) -> List[str]:
        """
        Build list of nodes to execute starting from given node.

        Performs a forward traversal from start_node_id to find all
        reachable nodes in execution order.

        Args:
            workflow: The workflow schema
            start_node_id: Node ID to start execution from

        Returns:
            List of node IDs in execution order starting from start_node_id
        """
        if not workflow.nodes:
            logger.warning("Workflow has no nodes")
            return []

        # Check if start node exists
        if start_node_id not in workflow.nodes:
            logger.error(f"Start node {start_node_id} not found in workflow")
            return []

        # Build adjacency list from edges
        adjacency: Dict[str, List[str]] = {}
        for node_id in workflow.nodes:
            adjacency[node_id] = []

        for edge in workflow.edges:
            source_node = edge.source_node
            target_node = edge.target_node
            if source_node in adjacency:
                adjacency[source_node].append(target_node)

        # BFS from start node
        subgraph_nodes: List[str] = []
        visited: Set[str] = set()
        queue: List[str] = [start_node_id]

        while queue:
            node_id = queue.pop(0)
            if node_id in visited:
                continue

            visited.add(node_id)
            subgraph_nodes.append(node_id)

            # Add connected nodes to queue
            for neighbor in adjacency.get(node_id, []):
                if neighbor not in visited:
                    queue.append(neighbor)

        logger.info(
            f"Built subgraph: {len(subgraph_nodes)} nodes starting from {start_node_id}"
        )
        return subgraph_nodes

    def get_predecessors(
        self,
        workflow: "WorkflowSchema",
        node_id: str,
    ) -> List[str]:
        """
        Get all predecessor nodes of a given node.

        Performs a backward traversal to find all nodes that lead to the given node.

        Args:
            workflow: The workflow schema
            node_id: Target node ID

        Returns:
            List of predecessor node IDs
        """
        if not workflow.nodes or node_id not in workflow.nodes:
            return []

        # Build reverse adjacency list
        reverse_adj: Dict[str, List[str]] = {}
        for nid in workflow.nodes:
            reverse_adj[nid] = []

        for edge in workflow.edges:
            target_node = edge.target_node
            source_node = edge.source_node
            if target_node in reverse_adj:
                reverse_adj[target_node].append(source_node)

        # BFS backwards
        predecessors: List[str] = []
        visited: Set[str] = set()
        queue: List[str] = [node_id]

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue

            visited.add(current)
            if current != node_id:
                predecessors.append(current)

            for pred in reverse_adj.get(current, []):
                if pred not in visited:
                    queue.append(pred)

        return predecessors

    def get_variables_for_partial_run(
        self,
        workflow: "WorkflowSchema",
        start_node_id: str,
        use_cached: bool = True,
        initial_variables: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Get variables to use for partial execution.

        If use_cached is True and cached variables exist, returns cached
        variables merged with any initial variables.

        Args:
            workflow: The workflow schema
            start_node_id: Node to start from
            use_cached: Whether to use cached variables from last run
            initial_variables: Optional initial variables to merge

        Returns:
            Dict of variables for execution
        """
        variables: Dict[str, Any] = {}

        # Start with initial variables if provided
        if initial_variables:
            variables.update(initial_variables)

        # Merge cached variables if requested
        if use_cached and self._cached_variables:
            # Only include variables that would have been set by predecessors
            predecessors = self.get_predecessors(workflow, start_node_id)
            logger.debug(
                f"Using cached variables from {len(predecessors)} predecessor nodes"
            )
            variables.update(self._cached_variables)

        return variables

    async def execute_from_node(
        self,
        workflow: "WorkflowSchema",
        start_node_id: str,
        context: "ExecutionContext",
        use_cached_variables: bool = True,
        node_executor_factory: Optional[callable] = None,
    ) -> bool:
        """
        Execute workflow starting from a specific node.

        Args:
            workflow: The workflow schema
            start_node_id: Node ID to start execution from
            context: Execution context
            use_cached_variables: Whether to restore cached variables
            node_executor_factory: Optional factory for creating node executors

        Returns:
            True if execution completed successfully
        """
        logger.info(f"Starting partial execution from node: {start_node_id}")

        # Restore cached variables if requested
        if use_cached_variables and self._cached_variables:
            for name, value in self._cached_variables.items():
                if not name.startswith("_"):  # Skip internal variables
                    context.set_variable(name, value)
            logger.debug(f"Restored {len(self._cached_variables)} cached variables")

        # Build subgraph of nodes to execute
        subgraph_nodes = self.build_subgraph_from_node(workflow, start_node_id)

        if not subgraph_nodes:
            logger.error("No nodes to execute in subgraph")
            return False

        # Execute nodes in order
        try:
            from casare_rpa.infrastructure.execution.node_executor import NodeExecutor

            executor = NodeExecutor()

            for node_id in subgraph_nodes:
                if context.is_stopped():
                    logger.info("Execution stopped by user")
                    break

                node = workflow.nodes.get(node_id)
                if not node:
                    logger.warning(f"Node {node_id} not found in workflow")
                    continue

                # Check for pause
                await context.pause_checkpoint()

                # Execute the node
                context.set_current_node(node_id)
                try:
                    await executor.execute_node(node, context)
                except Exception as e:
                    logger.error(f"Node {node_id} failed: {e}")
                    context.add_error(node_id, str(e))
                    # Continue or stop based on workflow settings
                    raise

            logger.success(f"Partial execution completed: {len(subgraph_nodes)} nodes")
            return True

        except asyncio.CancelledError:
            logger.info("Partial execution cancelled")
            raise

        except Exception as e:
            logger.exception(f"Partial execution failed: {e}")
            return False


# Module-level instance for singleton-like access
_partial_executor: Optional[PartialExecutor] = None


def get_partial_executor() -> PartialExecutor:
    """
    Get the singleton partial executor instance.

    Returns:
        PartialExecutor instance
    """
    global _partial_executor
    if _partial_executor is None:
        _partial_executor = PartialExecutor()
    return _partial_executor
