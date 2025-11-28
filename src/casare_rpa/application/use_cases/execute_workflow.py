"""
CasareRPA - Application Use Case: Execute Workflow
Coordinates workflow execution across domain and infrastructure layers.

This use case orchestrates workflow execution by:
- Using ExecutionOrchestrator (domain) for routing decisions
- Using ExecutionContext (infrastructure) for execution and resources
- Emitting events via EventBus for progress tracking
- Handling async execution and errors

Architecture:
- Domain logic: ExecutionOrchestrator makes routing decisions
- Infrastructure: ExecutionContext manages Playwright resources
- Application: This class coordinates them and publishes events
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from loguru import logger

from ...domain.entities.workflow import WorkflowSchema
from ...domain.services.execution_orchestrator import ExecutionOrchestrator
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.domain.events import EventBus, Event
from casare_rpa.domain.value_objects.types import EventType, NodeId, NodeStatus
from ...utils.performance.performance_metrics import get_metrics


class ExecutionSettings:
    """Execution settings value object."""

    def __init__(
        self,
        continue_on_error: bool = False,
        node_timeout: float = 120.0,
        target_node_id: Optional[NodeId] = None,
    ) -> None:
        """
        Initialize execution settings.

        Args:
            continue_on_error: If True, continue workflow on node errors
            node_timeout: Timeout for individual node execution in seconds
            target_node_id: Optional target node for Run-To-Node feature
        """
        self.continue_on_error = continue_on_error
        self.node_timeout = node_timeout
        self.target_node_id = target_node_id


class ExecuteWorkflowUseCase:
    """
    Application use case for executing workflows.

    Coordinates:
    - Domain: ExecutionOrchestrator for routing logic
    - Domain: Workflow schema for node/connection data
    - Infrastructure: ExecutionContext for resources and variables
    - Infrastructure: EventBus for progress notifications
    """

    def __init__(
        self,
        workflow: WorkflowSchema,
        event_bus: Optional[EventBus] = None,
        settings: Optional[ExecutionSettings] = None,
        initial_variables: Optional[Dict[str, Any]] = None,
        project_context: Optional[Any] = None,
    ) -> None:
        """
        Initialize execute workflow use case.

        Args:
            workflow: Workflow schema to execute
            event_bus: Optional event bus for progress updates
            settings: Execution settings
            initial_variables: Optional dict of variables to initialize
            project_context: Optional project context for scoped variables
        """
        self.workflow = workflow
        self.settings = settings or ExecutionSettings()
        self._initial_variables = initial_variables or {}
        self._project_context = project_context

        # Get global event bus if not provided
        if event_bus is None:
            from casare_rpa.domain.events import get_event_bus

            event_bus = get_event_bus()

        self.event_bus = event_bus

        # Domain services
        self.orchestrator = ExecutionOrchestrator(workflow)

        # Infrastructure components (created during execution)
        self.context: Optional[ExecutionContext] = None

        # Execution tracking
        self.executed_nodes: Set[NodeId] = set()
        self.current_node_id: Optional[NodeId] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self._stop_requested = False

        # Run-To-Node support
        self._target_reached = False
        self._subgraph_nodes: Optional[Set[NodeId]] = None

        # Calculate subgraph if target node is specified
        if self.settings.target_node_id:
            self._calculate_subgraph()

    def _calculate_subgraph(self) -> None:
        """Calculate subgraph for Run-To-Node execution."""
        if not self.settings.target_node_id:
            return

        start_node_id = self.orchestrator.find_start_node()
        if not start_node_id:
            logger.error("Cannot calculate subgraph: no StartNode found")
            return

        # Check if target is reachable
        if not self.orchestrator.is_reachable(
            start_node_id, self.settings.target_node_id
        ):
            logger.error(
                f"Target node {self.settings.target_node_id} is not reachable from StartNode"
            )
            return

        # Calculate the subgraph
        self._subgraph_nodes = self.orchestrator.calculate_execution_path(
            start_node_id, self.settings.target_node_id
        )

        logger.info(
            f"Subgraph calculated: {len(self._subgraph_nodes)} nodes to execute"
        )

    def _should_execute_node(self, node_id: NodeId) -> bool:
        """
        Check if a node should be executed based on subgraph filtering.

        Args:
            node_id: Node ID to check

        Returns:
            True if node should be executed
        """
        if self._subgraph_nodes is None:
            return True  # No subgraph filter - execute all nodes

        return node_id in self._subgraph_nodes

    def _emit_event(self, event_type: EventType, data: Dict[str, Any]) -> None:
        """
        Emit an event to the event bus.

        Args:
            event_type: Type of event
            data: Event data payload
        """
        if self.event_bus:
            event = Event(
                event_type=event_type,
                data=data,
                node_id=self.current_node_id,
            )
            self.event_bus.publish(event)

    def _calculate_progress(self) -> float:
        """
        Calculate execution progress as percentage.

        Returns:
            Progress percentage (0-100)
        """
        total = (
            len(self._subgraph_nodes)
            if self._subgraph_nodes
            else len(self.workflow.nodes)
        )
        if total == 0:
            return 0.0
        return (len(self.executed_nodes) / total) * 100

    async def _execute_node_once(self, node: Any) -> Dict[str, Any]:
        """
        Execute a single node once (internal method for retry wrapper).

        Args:
            node: The node to execute

        Returns:
            Execution result dictionary

        Raises:
            Exception: If execution fails
        """
        try:
            result = await asyncio.wait_for(
                node.execute(self.context), timeout=self.settings.node_timeout
            )
            return result or {"success": False, "error": "No result returned"}
        except asyncio.TimeoutError:
            raise asyncio.TimeoutError(
                f"Node {node.node_id} timed out after {self.settings.node_timeout}s"
            )

    async def _execute_node(self, node: Any) -> tuple[bool, Optional[Dict[str, Any]]]:
        """
        Execute a single node with error handling.

        Args:
            node: The node to execute

        Returns:
            Tuple of (success: bool, result: dict)
        """
        # Check if node is disabled (bypassed)
        if node.config.get("_disabled", False):
            logger.info(f"Node {node.node_id} is disabled - bypassing execution")
            node.status = NodeStatus.SUCCESS

            self._emit_event(
                EventType.NODE_COMPLETED,
                {
                    "node_id": node.node_id,
                    "node_type": node.__class__.__name__,
                    "bypassed": True,
                    "execution_time": 0,
                    "progress": self._calculate_progress(),
                },
            )

            return True, {"success": True, "bypassed": True}

        self.current_node_id = node.node_id
        node.status = NodeStatus.RUNNING

        self._emit_event(
            EventType.NODE_STARTED,
            {"node_id": node.node_id, "node_type": node.__class__.__name__},
        )

        # Record start time
        import time

        start_time = time.time()

        # Record metrics
        node_type = node.__class__.__name__
        get_metrics().record_node_start(node_type, node.node_id)

        try:
            # Validate node before execution
            if not node.validate():
                logger.error(f"Node validation failed: {node.node_id}")
                node.status = NodeStatus.ERROR
                self._emit_event(
                    EventType.NODE_ERROR,
                    {"node_id": node.node_id, "error": "Validation failed"},
                )
                return False, None

            # Execute the node
            result = await self._execute_node_once(node)

            # Update debug info
            execution_time = time.time() - start_time
            node.execution_count += 1
            node.last_execution_time = execution_time
            node.last_output = result

            # Handle result
            if result and result.get("success", False):
                node.status = NodeStatus.SUCCESS
                self.executed_nodes.add(node.node_id)

                self._emit_event(
                    EventType.NODE_COMPLETED,
                    {
                        "node_id": node.node_id,
                        "message": result.get("data", {}).get("message", "Completed"),
                        "progress": self._calculate_progress(),
                        "execution_time": execution_time,
                    },
                )

                # Record successful execution in metrics
                get_metrics().record_node_complete(
                    node_type, node.node_id, execution_time * 1000, success=True
                )
                return True, result
            else:
                node.status = NodeStatus.ERROR
                error_msg = (
                    result.get("error", "Unknown error") if result else "No result"
                )
                self._emit_event(
                    EventType.NODE_ERROR,
                    {
                        "node_id": node.node_id,
                        "error": error_msg,
                        "execution_time": execution_time,
                    },
                )
                logger.error(f"Node execution failed: {node.node_id} - {error_msg}")

                # Record failed execution in metrics
                get_metrics().record_node_complete(
                    node_type, node.node_id, execution_time * 1000, success=False
                )
                return False, result

        except Exception as e:
            node.status = NodeStatus.ERROR
            error_msg = str(e)
            execution_time = time.time() - start_time

            self._emit_event(
                EventType.NODE_ERROR,
                {
                    "node_id": node.node_id,
                    "error": error_msg,
                    "execution_time": execution_time,
                },
            )

            logger.exception(f"Exception during node execution: {node.node_id}")

            # Record exception in metrics
            get_metrics().record_node_complete(
                node_type, node.node_id, execution_time * 1000, success=False
            )
            return False, None

    def _transfer_data(self, connection: Any, nodes: Dict[NodeId, Any]) -> None:
        """
        Transfer data from source port to target port.

        Args:
            connection: The connection defining source and target
            nodes: Dictionary of node instances
        """
        source_node = nodes.get(connection.source_node)
        target_node = nodes.get(connection.target_node)

        if not source_node or not target_node:
            return

        # Get value from source output port
        value = source_node.get_output_value(connection.source_port)

        # Set value to target input port
        if value is not None:
            target_node.set_input_value(connection.target_port, value)

            # Log data transfers (non-exec) for debugging
            if "exec" not in connection.source_port.lower():
                logger.info(
                    f"Data: {connection.source_port} -> {connection.target_port} = {repr(value)[:80]}"
                )

    async def execute(self) -> bool:
        """
        Execute the workflow.

        Returns:
            True if workflow completed successfully, False otherwise
        """
        self.start_time = datetime.now()
        self._stop_requested = False
        self.executed_nodes.clear()

        # Create execution context
        self.context = ExecutionContext(
            workflow_name=self.workflow.metadata.name,
            initial_variables=self._initial_variables,
            project_context=self._project_context,
        )

        self._emit_event(
            EventType.WORKFLOW_STARTED,
            {
                "workflow_name": self.workflow.metadata.name,
                "total_nodes": len(self._subgraph_nodes)
                if self._subgraph_nodes
                else len(self.workflow.nodes),
            },
        )

        # Record workflow start for performance dashboard
        get_metrics().record_workflow_start(self.workflow.metadata.name)

        logger.info(f"Starting workflow execution: {self.workflow.metadata.name}")

        try:
            # Find start node
            start_node_id = self.orchestrator.find_start_node()
            if not start_node_id:
                raise ValueError("No StartNode found in workflow")

            # Execute workflow sequentially
            await self._execute_from_node(start_node_id)

            # Check if completed successfully
            if self._stop_requested:
                self.end_time = datetime.now()
                duration = (self.end_time - self.start_time).total_seconds()

                self._emit_event(
                    EventType.WORKFLOW_STOPPED,
                    {
                        "executed_nodes": len(self.executed_nodes),
                        "total_nodes": len(self.workflow.nodes),
                    },
                )

                logger.info("Workflow execution stopped by user")

                # Record stopped workflow as failed for metrics
                get_metrics().record_workflow_complete(
                    self.workflow.metadata.name, duration * 1000, success=False
                )
                return False
            else:
                self.end_time = datetime.now()
                duration = (self.end_time - self.start_time).total_seconds()

                self._emit_event(
                    EventType.WORKFLOW_COMPLETED,
                    {
                        "executed_nodes": len(self.executed_nodes),
                        "total_nodes": len(self.workflow.nodes),
                        "duration": duration,
                    },
                )

                logger.info(
                    f"Workflow completed successfully in {duration:.2f}s "
                    f"({len(self.executed_nodes)} nodes)"
                )

                # Record workflow completion for performance dashboard
                get_metrics().record_workflow_complete(
                    self.workflow.metadata.name, duration * 1000, success=True
                )
                return True

        except Exception as e:
            self.end_time = datetime.now()
            duration = (self.end_time - self.start_time).total_seconds()

            self._emit_event(
                EventType.WORKFLOW_ERROR,
                {"error": str(e), "executed_nodes": len(self.executed_nodes)},
            )

            logger.exception("Workflow execution failed with exception")

            # Record workflow failure for performance dashboard
            get_metrics().record_workflow_complete(
                self.workflow.metadata.name, duration * 1000, success=False
            )
            return False

        finally:
            # Cleanup context resources
            if self.context:
                try:
                    await asyncio.wait_for(self.context.cleanup(), timeout=30.0)
                except asyncio.TimeoutError:
                    logger.error("Context cleanup timed out after 30 seconds")
                except Exception as cleanup_error:
                    logger.error(f"Error during context cleanup: {cleanup_error}")

            self.current_node_id = None

    async def _execute_from_node(self, start_node_id: NodeId) -> None:
        """
        Execute workflow starting from a specific node.

        Args:
            start_node_id: Node ID to start execution from
        """
        # Queue of nodes to execute
        nodes_to_execute: List[NodeId] = [start_node_id]

        while nodes_to_execute and not self._stop_requested:
            current_node_id = nodes_to_execute.pop(0)

            # Skip if already executed (except for loops)
            is_loop_node = self.orchestrator.is_control_flow_node(current_node_id)
            if current_node_id in self.executed_nodes and not is_loop_node:
                continue

            # Skip nodes not in subgraph (Run-To-Node filtering)
            if not self._should_execute_node(current_node_id):
                logger.debug(f"Skipping node {current_node_id} (not in subgraph)")
                continue

            # Get node instance
            node = self.workflow.nodes.get(current_node_id)
            if not node:
                logger.error(f"Node {current_node_id} not found in workflow")
                continue

            # Transfer data from connected input ports
            for connection in self.workflow.connections:
                if connection.target_node == current_node_id:
                    self._transfer_data(connection, self.workflow.nodes)

            # Execute the node
            success, result = await self._execute_node(node)

            if not success:
                if self.settings.continue_on_error:
                    logger.warning(
                        f"Node {current_node_id} failed but continue_on_error is enabled"
                    )
                else:
                    logger.warning(
                        f"Stopping workflow due to node error: {current_node_id}"
                    )
                    break

            # Check if target node was reached (Run-To-Node feature)
            if success and self.settings.target_node_id == current_node_id:
                self._target_reached = True
                logger.info(
                    f"Target node {current_node_id} reached - execution complete"
                )
                break

            # Get next nodes based on execution result
            next_node_ids = self.orchestrator.get_next_nodes(current_node_id, result)

            # Add next nodes to queue
            nodes_to_execute.extend(next_node_ids)

    def stop(self) -> None:
        """Stop workflow execution."""
        self._stop_requested = True
        logger.info("Workflow stop requested")

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ExecuteWorkflowUseCase("
            f"workflow='{self.workflow.metadata.name}', "
            f"nodes={len(self.workflow.nodes)})"
        )
