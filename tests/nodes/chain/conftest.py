"""
Chain testing infrastructure for CasareRPA.

Provides fluent APIs for building and executing multi-node workflows
in integration tests. Uses real node implementations with mocked
external I/O (browser, desktop, HTTP, file system).

Classes:
    WorkflowBuilder: Fluent API for constructing test workflows
    ChainExecutor: Executes node chains with proper data flow

Fixtures:
    workflow_builder: Returns WorkflowBuilder instance
    chain_executor: Returns ChainExecutor instance
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import pytest
from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.entities.node_connection import NodeConnection
from casare_rpa.domain.entities.workflow import WorkflowSchema
from casare_rpa.domain.entities.workflow_metadata import WorkflowMetadata
from casare_rpa.domain.services.execution_orchestrator import ExecutionOrchestrator
from casare_rpa.domain.value_objects.types import (
    NodeId,
    NodeStatus,
    EXEC_IN_PORT,
    EXEC_OUT_PORT,
)
from casare_rpa.infrastructure.execution import ExecutionContext


@dataclass
class ChainExecutionResult:
    """
    Result of a chain execution.

    Attributes:
        success: Whether all nodes executed successfully
        nodes_executed: List of node IDs in execution order
        final_variables: Variables after execution completes
        errors: List of (node_id, error_message) tuples
        node_results: Map of node_id to execution result
    """

    success: bool
    nodes_executed: List[NodeId] = field(default_factory=list)
    final_variables: Dict[str, Any] = field(default_factory=dict)
    errors: List[Tuple[NodeId, str]] = field(default_factory=list)
    node_results: Dict[NodeId, Dict[str, Any]] = field(default_factory=dict)


class WorkflowBuilder:
    """
    Fluent API for building test workflows.

    Provides a clean, chainable interface for constructing workflows
    with nodes and connections. Designed for integration tests that
    need to verify node chains work together correctly.

    Usage:
        builder = WorkflowBuilder()
        workflow = (
            builder
            .add(StartNode("start"), id="start")
            .add(SetVariableNode("set_x", config={"name": "x", "value": 10}), id="set_x")
            .add(EndNode("end"), id="end")
            .connect("start", "set_x")
            .connect("set_x", "end")
            .build()
        )

    Sequential shorthand:
        workflow = (
            builder
            .add(StartNode("start"))
            .add(SetVariableNode("set_x", config={"name": "x", "value": 10}))
            .add(EndNode("end"))
            .connect_sequential()
            .build()
        )
    """

    def __init__(self, name: str = "Test Workflow") -> None:
        """
        Initialize workflow builder.

        Args:
            name: Workflow name for metadata
        """
        self._name = name
        self._nodes: Dict[NodeId, BaseNode] = {}
        self._node_order: List[NodeId] = []
        self._connections: List[NodeConnection] = []
        self._auto_id_counter = 0

    def add(
        self,
        node: BaseNode,
        id: Optional[str] = None,
    ) -> WorkflowBuilder:
        """
        Add a node to the workflow.

        If no ID is provided, uses the node's existing node_id.
        Nodes are tracked in insertion order for connect_sequential().

        Args:
            node: Node instance to add
            id: Optional override for node ID (updates node.node_id)

        Returns:
            Self for method chaining

        Raises:
            ValueError: If node ID already exists in workflow
        """
        node_id = id if id is not None else node.node_id

        if node_id in self._nodes:
            raise ValueError(f"Node ID '{node_id}' already exists in workflow")

        if id is not None:
            node.node_id = id

        self._nodes[node_id] = node
        self._node_order.append(node_id)

        logger.debug(f"WorkflowBuilder: Added node '{node_id}' ({node.node_type})")
        return self

    def connect(
        self,
        source: str,
        target: str,
    ) -> WorkflowBuilder:
        """
        Connect two nodes.

        Supports two formats:
        - "node_id" - connects exec_out -> exec_in
        - "node_id.port_name" - connects specific ports

        Args:
            source: Source node ID or "node_id.port_name"
            target: Target node ID or "node_id.port_name"

        Returns:
            Self for method chaining

        Raises:
            ValueError: If source or target node not found
        """
        source_node_id, source_port = self._parse_port_spec(source, is_source=True)
        target_node_id, target_port = self._parse_port_spec(target, is_source=False)

        if source_node_id not in self._nodes:
            raise ValueError(f"Source node '{source_node_id}' not found in workflow")
        if target_node_id not in self._nodes:
            raise ValueError(f"Target node '{target_node_id}' not found in workflow")

        connection = NodeConnection(
            source_node=source_node_id,
            source_port=source_port,
            target_node=target_node_id,
            target_port=target_port,
        )
        self._connections.append(connection)

        logger.debug(
            f"WorkflowBuilder: Connected {source_node_id}.{source_port} -> "
            f"{target_node_id}.{target_port}"
        )
        return self

    def connect_sequential(self) -> WorkflowBuilder:
        """
        Auto-connect all nodes in insertion order via exec ports.

        Connects each node to the next using exec_out -> exec_in.
        Useful for simple linear workflows where explicit connections
        are tedious.

        Returns:
            Self for method chaining

        Raises:
            ValueError: If fewer than 2 nodes exist
        """
        if len(self._node_order) < 2:
            raise ValueError("Cannot connect sequentially with fewer than 2 nodes")

        for i in range(len(self._node_order) - 1):
            source_id = self._node_order[i]
            target_id = self._node_order[i + 1]

            connection = NodeConnection(
                source_node=source_id,
                source_port=EXEC_OUT_PORT,
                target_node=target_id,
                target_port=EXEC_IN_PORT,
            )
            self._connections.append(connection)

            logger.debug(
                f"WorkflowBuilder: Sequential connect {source_id} -> {target_id}"
            )

        return self

    def build(self) -> WorkflowSchema:
        """
        Build and return the workflow.

        Creates a WorkflowSchema with all added nodes and connections.
        Nodes are stored as instances (not serialized) for direct execution.

        Returns:
            WorkflowSchema ready for execution

        Raises:
            ValueError: If workflow has no nodes
        """
        if not self._nodes:
            raise ValueError("Cannot build workflow with no nodes")

        metadata = WorkflowMetadata(name=self._name)
        workflow = WorkflowSchema(metadata=metadata)

        for node_id, node in self._nodes.items():
            workflow.nodes[node_id] = node

        for connection in self._connections:
            workflow.connections.append(connection)

        logger.info(
            f"WorkflowBuilder: Built workflow '{self._name}' with "
            f"{len(self._nodes)} nodes, {len(self._connections)} connections"
        )

        return workflow

    def reset(self) -> WorkflowBuilder:
        """
        Reset builder state for reuse.

        Clears all nodes and connections, allowing the builder
        to be reused for another workflow.

        Returns:
            Self for method chaining
        """
        self._nodes.clear()
        self._node_order.clear()
        self._connections.clear()
        self._auto_id_counter = 0
        return self

    def _parse_port_spec(
        self,
        spec: str,
        is_source: bool,
    ) -> Tuple[str, str]:
        """
        Parse a port specification into node_id and port_name.

        Args:
            spec: Port spec in format "node_id" or "node_id.port_name"
            is_source: True if parsing source port, False for target

        Returns:
            Tuple of (node_id, port_name)
        """
        if "." in spec:
            parts = spec.split(".", 1)
            return parts[0], parts[1]

        default_port = EXEC_OUT_PORT if is_source else EXEC_IN_PORT
        return spec, default_port


class ChainExecutor:
    """
    Executes node chains with proper data flow.

    Uses real node implementations and tracks execution flow.
    Designed for integration tests that verify multi-node
    behavior without needing a full workflow runner.

    Key features:
    - Real node execution (not mocked)
    - Proper data transfer between connected ports
    - Execution path tracking
    - Error capture and reporting

    Usage:
        executor = ChainExecutor()
        result = await executor.execute(workflow, variables={"x": 10})

        assert result.success
        assert result.final_variables["output"] == expected_value
    """

    def __init__(
        self,
        timeout_per_node: float = 30.0,
        stop_on_error: bool = True,
    ) -> None:
        """
        Initialize chain executor.

        Args:
            timeout_per_node: Timeout in seconds for each node
            stop_on_error: Stop execution on first error
        """
        self._timeout_per_node = timeout_per_node
        self._stop_on_error = stop_on_error

    async def execute(
        self,
        workflow: WorkflowSchema,
        variables: Optional[Dict[str, Any]] = None,
    ) -> ChainExecutionResult:
        """
        Execute the workflow and return results.

        Creates an ExecutionContext, finds the start node,
        and executes nodes following the connection graph.
        Data flows through port connections automatically.

        Args:
            workflow: Workflow to execute
            variables: Initial variables to set in context

        Returns:
            ChainExecutionResult with execution details

        Raises:
            ValueError: If no StartNode found
        """
        result = ChainExecutionResult(success=True)

        async with ExecutionContext(
            workflow_name=workflow.metadata.name,
            initial_variables=variables,
        ) as context:
            orchestrator = ExecutionOrchestrator(workflow)
            start_node_id = orchestrator.find_start_node()

            if not start_node_id:
                result.success = False
                result.errors.append(("workflow", "No StartNode found in workflow"))
                return result

            try:
                await self._execute_from_node(
                    workflow=workflow,
                    orchestrator=orchestrator,
                    context=context,
                    start_node_id=start_node_id,
                    result=result,
                )
            except Exception as e:
                result.success = False
                result.errors.append(("executor", str(e)))
                logger.exception(f"ChainExecutor: Execution failed: {e}")

            result.final_variables = dict(context.variables)

        return result

    async def _execute_from_node(
        self,
        workflow: WorkflowSchema,
        orchestrator: ExecutionOrchestrator,
        context: ExecutionContext,
        start_node_id: NodeId,
        result: ChainExecutionResult,
    ) -> None:
        """
        Execute workflow starting from a specific node.

        Uses BFS to traverse the connection graph, executing
        nodes in order and transferring data between ports.

        Args:
            workflow: Workflow being executed
            orchestrator: Orchestrator for navigation
            context: Execution context
            start_node_id: Node to start from
            result: Result object to populate
        """
        executed: set[NodeId] = set()
        nodes_to_execute: List[NodeId] = [start_node_id]

        while nodes_to_execute:
            current_node_id = nodes_to_execute.pop(0)

            if current_node_id in executed:
                if not orchestrator.is_control_flow_node(current_node_id):
                    continue

            node = workflow.nodes.get(current_node_id)
            if node is None:
                logger.error(f"ChainExecutor: Node '{current_node_id}' not found")
                continue

            if not isinstance(node, BaseNode):
                logger.error(
                    f"ChainExecutor: Node '{current_node_id}' is not a BaseNode instance"
                )
                continue

            self._transfer_input_data(workflow, current_node_id)

            try:
                node_result = await asyncio.wait_for(
                    node.execute(context),
                    timeout=self._timeout_per_node,
                )

                result.nodes_executed.append(current_node_id)
                result.node_results[current_node_id] = node_result or {}
                executed.add(current_node_id)

                success = node_result.get("success", False) if node_result else False

                if not success:
                    error_msg = (
                        node_result.get("error", "Unknown error")
                        if node_result
                        else "No result returned"
                    )
                    result.errors.append((current_node_id, error_msg))

                    if self._stop_on_error:
                        result.success = False
                        logger.warning(
                            f"ChainExecutor: Stopping on error at '{current_node_id}'"
                        )
                        return

                next_node_ids = orchestrator.get_next_nodes(
                    current_node_id, node_result
                )
                nodes_to_execute.extend(next_node_ids)

            except asyncio.TimeoutError:
                result.errors.append(
                    (current_node_id, f"Timeout after {self._timeout_per_node}s")
                )
                result.success = False
                logger.error(f"ChainExecutor: Node '{current_node_id}' timed out")
                if self._stop_on_error:
                    return

            except Exception as e:
                result.errors.append((current_node_id, str(e)))
                result.success = False
                logger.exception(
                    f"ChainExecutor: Node '{current_node_id}' raised exception"
                )
                if self._stop_on_error:
                    return

    def _transfer_input_data(
        self,
        workflow: WorkflowSchema,
        target_node_id: NodeId,
    ) -> None:
        """
        Transfer data from connected source ports to target input ports.

        Finds all connections targeting this node and copies
        output values from source nodes to input ports.

        Args:
            workflow: Workflow containing nodes and connections
            target_node_id: ID of node receiving data
        """
        target_node = workflow.nodes.get(target_node_id)
        if not isinstance(target_node, BaseNode):
            return

        for connection in workflow.connections:
            if connection.target_node != target_node_id:
                continue

            source_node = workflow.nodes.get(connection.source_node)
            if not isinstance(source_node, BaseNode):
                continue

            source_port = connection.source_port
            target_port = connection.target_port

            if source_port.startswith("exec"):
                continue

            value = source_node.get_output_value(source_port)
            if value is not None:
                try:
                    target_node.set_input_value(target_port, value)
                    logger.debug(
                        f"ChainExecutor: Data transfer "
                        f"{connection.source_node}.{source_port} -> "
                        f"{target_node_id}.{target_port}"
                    )
                except ValueError as e:
                    logger.warning(f"ChainExecutor: Failed to set input value: {e}")


@pytest.fixture
def workflow_builder() -> WorkflowBuilder:
    """
    Provide a fresh WorkflowBuilder instance for tests.

    Returns:
        WorkflowBuilder ready for use

    Usage:
        def test_my_chain(workflow_builder):
            workflow = (
                workflow_builder
                .add(StartNode("start"))
                .add(MyNode("my_node"))
                .add(EndNode("end"))
                .connect_sequential()
                .build()
            )
    """
    return WorkflowBuilder()


@pytest.fixture
def chain_executor() -> ChainExecutor:
    """
    Provide a ChainExecutor instance for tests.

    Returns:
        ChainExecutor ready for workflow execution

    Usage:
        @pytest.mark.asyncio
        async def test_my_chain(workflow_builder, chain_executor):
            workflow = workflow_builder.add(...).build()
            result = await chain_executor.execute(workflow)
            assert result.success
    """
    return ChainExecutor()
