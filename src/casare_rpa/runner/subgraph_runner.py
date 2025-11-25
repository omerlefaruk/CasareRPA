"""
CasareRPA - Subgraph Runner
Executes snippet subgraphs with entry/exit point handling and context isolation.
"""

import asyncio
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass
from loguru import logger

from ..core.base_node import BaseNode
from ..core.workflow_schema import NodeConnection
from ..core.execution_context import ExecutionContext
from ..core.types import NodeId, NodeStatus


@dataclass
class SubgraphExecutionResult:
    """
    Result of subgraph execution.

    Attributes:
        success: Whether execution completed successfully
        executed_nodes: Set of node IDs that were executed
        node_results: Dict mapping node_id to execution result
        exit_node_results: Results from exit nodes (for output)
        error: Optional error message
    """

    success: bool
    executed_nodes: Set[NodeId]
    node_results: Dict[NodeId, Dict[str, Any]]
    exit_node_results: Dict[NodeId, Any]
    error: Optional[str] = None


class SubgraphRunner:
    """
    Executes a subgraph of nodes with entry and exit points.

    This is used by SnippetNode to execute internal node networks.
    Unlike WorkflowRunner, SubgraphRunner:
    - Starts from specified entry nodes (not StartNode)
    - Stops at specified exit nodes (not workflow end)
    - Uses provided ExecutionContext (child context)
    - Simpler execution model (no retry, parallel, debug features)
    """

    def __init__(
        self,
        nodes: Dict[NodeId, BaseNode],
        connections: List[NodeConnection],
        entry_nodes: List[NodeId],
        exit_nodes: List[NodeId],
    ):
        """
        Initialize subgraph runner.

        Args:
            nodes: Dictionary of node instances in subgraph
            connections: List of connections between nodes
            entry_nodes: Node IDs to start execution from
            exit_nodes: Node IDs where execution terminates
        """
        self.nodes = nodes
        self.connections = connections
        self.entry_nodes = entry_nodes
        self.exit_nodes = exit_nodes

        # Build connection lookup for fast traversal
        self._build_connection_map()

        logger.debug(
            f"SubgraphRunner initialized: {len(nodes)} nodes, "
            f"{len(entry_nodes)} entry points, {len(exit_nodes)} exit points"
        )

    def _build_connection_map(self):
        """Build fast lookup maps for connections."""
        # Map node_id -> list of connections FROM this node
        self.outgoing_connections: Dict[NodeId, List[NodeConnection]] = {}

        # Map node_id -> list of connections TO this node
        self.incoming_connections: Dict[NodeId, List[NodeConnection]] = {}

        for conn in self.connections:
            # Outgoing
            if conn.source_node not in self.outgoing_connections:
                self.outgoing_connections[conn.source_node] = []
            self.outgoing_connections[conn.source_node].append(conn)

            # Incoming
            if conn.target_node not in self.incoming_connections:
                self.incoming_connections[conn.target_node] = []
            self.incoming_connections[conn.target_node].append(conn)

    async def execute(self, context: ExecutionContext) -> SubgraphExecutionResult:
        """
        Execute the subgraph from entry to exit nodes.

        Args:
            context: Execution context (usually child context)

        Returns:
            SubgraphExecutionResult with execution data
        """
        executed_nodes: Set[NodeId] = set()
        node_results: Dict[NodeId, Dict[str, Any]] = {}
        exit_node_results: Dict[NodeId, Any] = {}
        error_message: Optional[str] = None

        logger.info(
            f"Starting subgraph execution with {len(self.entry_nodes)} entry points"
        )

        try:
            # Execute from each entry point
            for entry_id in self.entry_nodes:
                if entry_id not in self.nodes:
                    logger.warning(f"Entry node {entry_id} not found in subgraph")
                    continue

                await self._execute_from_node(
                    entry_id, context, executed_nodes, node_results, exit_node_results
                )

            # Check if all entry nodes were processed
            success = len(executed_nodes) > 0 and error_message is None

            logger.info(
                f"Subgraph execution completed: {len(executed_nodes)} nodes executed, "
                f"success={success}"
            )

            return SubgraphExecutionResult(
                success=success,
                executed_nodes=executed_nodes,
                node_results=node_results,
                exit_node_results=exit_node_results,
                error=error_message,
            )

        except Exception as e:
            logger.error(f"Subgraph execution failed: {e}")
            return SubgraphExecutionResult(
                success=False,
                executed_nodes=executed_nodes,
                node_results=node_results,
                exit_node_results=exit_node_results,
                error=str(e),
            )

    async def _execute_from_node(
        self,
        node_id: NodeId,
        context: ExecutionContext,
        executed_nodes: Set[NodeId],
        node_results: Dict[NodeId, Dict[str, Any]],
        exit_node_results: Dict[NodeId, Any],
    ):
        """
        Recursively execute nodes starting from a given node.

        Args:
            node_id: Current node ID to execute
            context: Execution context
            executed_nodes: Set of already executed nodes (to avoid cycles)
            node_results: Dict to store node execution results
            exit_node_results: Dict to store exit node results
        """
        # Skip if already executed (avoid infinite loops)
        if node_id in executed_nodes:
            return

        # Skip if node not in subgraph
        if node_id not in self.nodes:
            logger.warning(f"Node {node_id} not found in subgraph")
            return

        # Get node
        node = self.nodes[node_id]

        # Mark as executed
        executed_nodes.add(node_id)

        # Execute node
        try:
            logger.debug(f"Executing subgraph node: {node_id} ({node.__class__.__name__})")

            # Set node status
            node.status = NodeStatus.RUNNING

            # Validate node
            if not node.validate():
                logger.error(f"Node validation failed: {node_id}")
                node.status = NodeStatus.ERROR
                node_results[node_id] = {"success": False, "error": "Validation failed"}
                return

            # Execute node
            result = await node.execute(context)
            if result is None:
                result = {"success": True}

            # Record result
            node_results[node_id] = result

            # Update node status
            if result.get("success", False):
                node.status = NodeStatus.SUCCESS
            else:
                node.status = NodeStatus.ERROR

            # If this is an exit node, store its result
            if node_id in self.exit_nodes:
                exit_node_results[node_id] = result.get("data", None)
                logger.debug(f"Exit node reached: {node_id}")
                # Don't continue execution past exit nodes
                return

            # Transfer data to connected nodes
            outgoing = self.outgoing_connections.get(node_id, [])
            for conn in outgoing:
                self._transfer_data(conn)

            # Continue execution to connected nodes
            # Execute only if this is an execution flow connection
            for conn in outgoing:
                # Check if this is an execution connection (exec_out port)
                if conn.source_port in ["exec_out", "loop_body", "completed", "then", "else"]:
                    # Recursively execute target node
                    await self._execute_from_node(
                        conn.target_node,
                        context,
                        executed_nodes,
                        node_results,
                        exit_node_results,
                    )

        except Exception as e:
            logger.error(f"Error executing subgraph node {node_id}: {e}")
            node.status = NodeStatus.ERROR
            node_results[node_id] = {"success": False, "error": str(e)}

    def _transfer_data(self, connection: NodeConnection):
        """
        Transfer data from source port to target port.

        Args:
            connection: The connection defining source and target
        """
        source_node = self.nodes.get(connection.source_node)
        target_node = self.nodes.get(connection.target_node)

        if not source_node or not target_node:
            return

        # Get value from source output port
        value = source_node.get_output_value(connection.source_port)

        # Set value to target input port
        if value is not None:
            target_node.set_input_value(connection.target_port, value)
            logger.debug(
                f"Subgraph data transfer: {connection.source_node}.{connection.source_port} "
                f"-> {connection.target_node}.{connection.target_port}"
            )
