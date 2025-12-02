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
from typing import Any, Dict, List, Optional, Set, Tuple
from loguru import logger

from ...domain.entities.workflow import WorkflowSchema
from ...domain.services.execution_orchestrator import ExecutionOrchestrator
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.domain.events import EventBus, Event
from casare_rpa.domain.value_objects.types import EventType, NodeId, NodeStatus
from ...utils.performance.performance_metrics import get_metrics
from ...utils.workflow.workflow_loader import NODE_TYPE_MAP


def _create_node_from_dict(node_data: dict) -> Any:
    """
    Create a node instance from a dict definition.

    Args:
        node_data: Dict with node_id, type, and optional config

    Returns:
        Node instance

    Raises:
        ValueError: If node type is unknown
    """
    node_type = node_data.get("type") or node_data.get("node_type")
    node_id = node_data.get("node_id")
    config = node_data.get("config", {})

    node_class = NODE_TYPE_MAP.get(node_type)
    if not node_class:
        raise ValueError(f"Unknown node type: {node_type}")

    return node_class(node_id=node_id, config=config)


class ExecutionSettings:
    """Execution settings value object."""

    def __init__(
        self,
        continue_on_error: bool = False,
        node_timeout: float = 120.0,
        target_node_id: Optional[NodeId] = None,
        single_node: bool = False,
    ) -> None:
        """
        Initialize execution settings.

        Args:
            continue_on_error: If True, continue workflow on node errors
            node_timeout: Timeout for individual node execution in seconds
            target_node_id: Optional target node for Run-To-Node (F4) or Run-Single-Node (F5)
            single_node: If True, execute only target_node_id (F5 mode)
        """
        self.continue_on_error = continue_on_error
        self.node_timeout = node_timeout
        self.target_node_id = target_node_id
        self.single_node = single_node


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
        pause_event: Optional[asyncio.Event] = None,
    ) -> None:
        """
        Initialize execute workflow use case.

        Args:
            workflow: Workflow schema to execute
            event_bus: Optional event bus for progress updates
            settings: Execution settings
            initial_variables: Optional dict of variables to initialize
            project_context: Optional project context for scoped variables
            pause_event: Optional event for pause/resume coordination
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

        # Pause/resume support
        self.pause_event = pause_event or asyncio.Event()
        self.pause_event.set()  # Initially not paused

        # Execution tracking
        self.executed_nodes: Set[NodeId] = set()
        self.current_node_id: Optional[NodeId] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self._stop_requested = False

        # Run-To-Node support
        self._target_reached = False
        self._subgraph_nodes: Optional[Set[NodeId]] = None

        # Node instance cache (for dict-based workflows)
        self._node_instances: Dict[str, Any] = {}

        # Execution error tracking
        self._execution_failed = False
        self._execution_error: Optional[str] = None

        # Calculate subgraph if target node is specified
        if self.settings.target_node_id:
            if self.settings.single_node:
                # F5 mode: only execute the target node
                self._subgraph_nodes = {self.settings.target_node_id}
                logger.info(
                    f"Single node mode: executing only {self.settings.target_node_id}"
                )
            else:
                # F4 mode: execute up to target node
                self._calculate_subgraph()

    def _get_node_instance(self, node_id: str) -> Any:
        """
        Get or create a node instance from workflow nodes.

        Handles both actual node objects and dict-based node definitions.
        Uses caching to maintain node state across executions.

        Args:
            node_id: ID of the node to get

        Returns:
            Node instance (either existing or created from dict)

        Raises:
            ValueError: If node not found or cannot be created
        """
        # Return cached instance if available
        if node_id in self._node_instances:
            return self._node_instances[node_id]

        # Get node data from workflow
        node_data = self.workflow.nodes.get(node_id)
        if not node_data:
            raise ValueError(f"Node {node_id} not found in workflow")

        # If already a node object, cache and return
        if not isinstance(node_data, dict):
            self._node_instances[node_id] = node_data
            return node_data

        # Convert dict to node instance
        node = _create_node_from_dict(node_data)
        self._node_instances[node_id] = node
        return node

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
            node: The node instance to execute

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

        # Track execution path in context state
        self.context.set_current_node(node.node_id)

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
            # validate() returns tuple (is_valid: bool, error_message: Optional[str])
            is_valid, validation_error = node.validate()
            if not is_valid:
                error_msg = validation_error or "Validation failed"
                logger.error(f"Node validation failed: {node.node_id} - {error_msg}")
                node.status = NodeStatus.ERROR
                self._emit_event(
                    EventType.NODE_ERROR,
                    {"node_id": node.node_id, "error": error_msg},
                )
                return False, None

            # Execute the node
            result = await self._execute_node_once(node)

            # Update debug info
            execution_time = time.time() - start_time
            node.execution_count += 1
            node.last_execution_time = execution_time
            node.last_output = result

            # Handle None result explicitly
            if result is None:
                result = {
                    "success": False,
                    "error": f"Node {node.node_id} ({node_type}) returned None instead of result dict",
                }
                logger.error(result["error"])

            # Handle result
            if result.get("success", False):
                node.status = NodeStatus.SUCCESS
                self.executed_nodes.add(node.node_id)

                # Validate output ports have values after successful execution
                self._validate_output_ports(node, result)

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
                error_msg = result.get("error", "Unknown error")
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

            # Check if we're inside a try block - capture error for catch
            error_captured = self._capture_try_block_error(
                error_msg, type(e).__name__, e
            )

            if not error_captured:
                self._emit_event(
                    EventType.NODE_ERROR,
                    {
                        "node_id": node.node_id,
                        "error": error_msg,
                        "execution_time": execution_time,
                    },
                )
                logger.exception(f"Exception during node execution: {node.node_id}")
            else:
                logger.info(
                    f"Exception captured by try block: {node.node_id} - {error_msg}"
                )

            # Record exception in metrics
            get_metrics().record_node_complete(
                node_type, node.node_id, execution_time * 1000, success=False
            )

            # If error was captured by try block, return success with special marker
            if error_captured:
                return True, {"success": True, "error_captured": True}
            return False, None

    def _transfer_data(self, connection: Any) -> None:
        """
        Transfer data from source port to target port.

        Args:
            connection: The connection defining source and target
        """
        try:
            source_node = self._get_node_instance(connection.source_node)
            target_node = self._get_node_instance(connection.target_node)
        except ValueError:
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
        else:
            # Log warning when data transfer fails due to missing output value
            if "exec" not in connection.source_port.lower():
                logger.warning(
                    f"Data transfer skipped: source node {source_node.node_id} "
                    f"({type(source_node).__name__}) port '{connection.source_port}' has no value"
                )

    def _validate_output_ports(self, node: Any, result: dict) -> bool:
        """
        Validate that required output ports have values after execution.

        Logs warnings for output ports that have no value after successful execution.
        This helps detect silent failures where nodes succeed but don't produce expected data.

        Args:
            node: The executed node instance
            result: The execution result dictionary

        Returns:
            True (validation is informational, doesn't block execution)
        """
        # Skip validation for control flow nodes (only have exec ports)
        control_flow_nodes = (
            "IfNode",
            "ForLoopStartNode",
            "ForLoopEndNode",
            "WhileLoopNode",
            "WhileEndNode",
            "TryCatchNode",
            "TryEndNode",
            "CatchNode",
            "CatchEndNode",
            "FinallyNode",
            "FinallyEndNode",
            "ForkNode",
            "JoinNode",
            "StartNode",
            "EndNode",
            "ParallelForEachNode",
        )
        node_type_name = type(node).__name__
        if node_type_name in control_flow_nodes:
            return True

        # Check if node has output_ports attribute
        if not hasattr(node, "output_ports"):
            return True

        # Filter to data output ports (exclude exec ports)
        # node.output_ports is a Dict[str, Port], so iterate over values()
        output_ports = [
            p
            for p in node.output_ports.values()
            if not p.name.startswith("exec") and not p.name.startswith("_exec")
        ]

        if not output_ports:
            return True  # No data ports to validate

        # Validate each output port has a value
        for port in output_ports:
            value = node.get_output_value(port.name)
            if value is None:
                logger.warning(
                    f"Node {node.node_id} ({node_type_name}) output port "
                    f"'{port.name}' has no value after successful execution"
                )

        return True

    def _capture_try_block_error(
        self, error_msg: str, error_type: str, exception: Exception
    ) -> bool:
        """
        Check if we're inside a try block and capture the error if so.

        Args:
            error_msg: Error message
            error_type: Error type/class name
            exception: The original exception

        Returns:
            True if error was captured by a try block, False otherwise
        """
        if not self.context:
            return False

        # Find active try state(s) in context variables
        import traceback

        stack_trace = "".join(
            traceback.format_exception(
                type(exception), exception, exception.__traceback__
            )
        )

        for key, value in list(self.context.variables.items()):
            if key.endswith("_try_state") and isinstance(value, dict):
                # Found an active try block - capture the error
                value["error"] = True
                value["error_type"] = error_type
                value["error_message"] = error_msg
                value["stack_trace"] = stack_trace
                logger.debug(f"Error captured in try block: {key}")
                return True

        return False

    def _find_active_try_catch_id(self) -> Optional[str]:
        """
        Find the catch node ID for the most recent active try block.

        Returns:
            Catch node ID if found, None otherwise
        """
        if not self.context:
            return None

        for key, value in self.context.variables.items():
            if key.endswith("_try_state") and isinstance(value, dict):
                if value.get("error") and value.get("catch_id"):
                    return value.get("catch_id")

        return None

    async def execute(self, run_all: bool = False) -> bool:
        """
        Execute the workflow.

        Args:
            run_all: If True, execute all StartNodes concurrently (Shift+F3).
                     If False, execute only the first StartNode (default F3).

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
            pause_event=self.pause_event,
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
            # Single node mode (F5): Execute only the target node
            if self.settings.single_node and self.settings.target_node_id:
                logger.info(
                    f"Single node execution mode: {self.settings.target_node_id}"
                )
                await self._execute_single_node(self.settings.target_node_id)
            elif run_all:
                # Run All mode (Shift+F3): Execute all StartNodes concurrently
                start_nodes = self.orchestrator.find_all_start_nodes()
                if len(start_nodes) > 1:
                    logger.info(
                        f"Run All mode: executing {len(start_nodes)} workflows concurrently"
                    )
                    await self._execute_parallel_workflows(start_nodes)
                elif start_nodes:
                    # Only one StartNode - run normally
                    await self._execute_from_node(start_nodes[0])
                else:
                    raise ValueError("No StartNode found in workflow")
            else:
                # Normal or Run-To-Node mode: Start from StartNode
                start_node_id = self.orchestrator.find_start_node()
                if not start_node_id:
                    raise ValueError("No StartNode found in workflow")

                # Execute workflow sequentially
                await self._execute_from_node(start_node_id)

            # Check for execution failure
            if self._execution_failed:
                self.end_time = datetime.now()
                duration = (self.end_time - self.start_time).total_seconds()

                self._emit_event(
                    EventType.WORKFLOW_ERROR,
                    {
                        "error": self._execution_error or "Execution failed",
                        "executed_nodes": len(self.executed_nodes),
                    },
                )

                logger.error(f"Workflow execution failed: {self._execution_error}")

                # Record workflow failure for performance dashboard
                get_metrics().record_workflow_complete(
                    self.workflow.metadata.name, duration * 1000, success=False
                )
                return False

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

                # Mark execution state as completed
                self.context._state.mark_completed()

                # Export final variables for Output tab display
                # Filter out internal variables (starting with _)
                final_variables = {
                    k: v
                    for k, v in self.context.variables.items()
                    if not k.startswith("_")
                }

                self._emit_event(
                    EventType.WORKFLOW_COMPLETED,
                    {
                        "executed_nodes": len(self.executed_nodes),
                        "total_nodes": len(self.workflow.nodes),
                        "duration": duration,
                        "variables": final_variables,
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

    async def _execute_single_node(self, node_id: NodeId) -> None:
        """
        Execute a single node in isolation (F5 mode).

        This method executes only the specified node, using any existing
        data from previous executions stored in the context. Useful for
        re-running a node with the same inputs.

        Args:
            node_id: Node ID to execute
        """
        logger.info(f"Executing single node: {node_id}")

        # Get node instance
        try:
            node = self._get_node_instance(node_id)
        except ValueError as e:
            error_msg = f"Node {node_id} not found in workflow: {e}"
            logger.error(error_msg)
            self._execution_failed = True
            self._execution_error = error_msg
            return

        # Transfer data from connected input ports (use existing data if available)
        for connection in self.workflow.connections:
            if connection.target_node == node_id:
                self._transfer_data(connection)

        # Execute the node
        success, result = await self._execute_node(node)

        if not success:
            error_msg = f"Node {node_id} execution failed"
            self._execution_failed = True
            self._execution_error = (
                result.get("error", error_msg) if result else error_msg
            )

    async def _execute_from_node(self, start_node_id: NodeId) -> None:
        """
        Execute workflow starting from a specific node.

        Args:
            start_node_id: Node ID to start execution from
        """
        # Queue of nodes to execute
        nodes_to_execute: List[NodeId] = [start_node_id]

        while nodes_to_execute and not self._stop_requested:
            # CHECKPOINT: Wait if paused
            await self._pause_checkpoint()

            # Check stop signal after resuming from pause
            if self._stop_requested:
                break

            current_node_id = nodes_to_execute.pop(0)

            # Skip if already executed (except for loops)
            is_loop_node = self.orchestrator.is_control_flow_node(current_node_id)
            if current_node_id in self.executed_nodes and not is_loop_node:
                continue

            # Skip nodes not in subgraph (Run-To-Node filtering)
            if not self._should_execute_node(current_node_id):
                logger.debug(f"Skipping node {current_node_id} (not in subgraph)")
                # Emit NODE_SKIPPED event for nodes filtered by subgraph
                self._emit_event(
                    EventType.NODE_SKIPPED,
                    {
                        "node_id": current_node_id,
                        "reason": "not_in_subgraph",
                        "timestamp": datetime.now().isoformat(),
                    },
                )
                continue

            # Get node instance (handles both dict and object nodes)
            try:
                node = self._get_node_instance(current_node_id)
            except ValueError as e:
                error_msg = f"Node {current_node_id} not found in workflow: {e}"
                logger.error(error_msg)
                if not self.settings.continue_on_error:
                    self._execution_failed = True
                    self._execution_error = error_msg
                    break
                continue

            # Transfer data from connected input ports
            for connection in self.workflow.connections:
                if connection.target_node == current_node_id:
                    self._transfer_data(connection)

            # Execute the node
            success, result = await self._execute_node(node)

            if not success:
                # Check if error was captured by a try block (non-exception error)
                error_msg = (
                    result.get("error", "Unknown error") if result else "Unknown error"
                )
                error_captured = self._capture_try_block_error(
                    error_msg, "ExecutionError", Exception(error_msg)
                )

                if error_captured:
                    # Route to catch node
                    catch_id = self._find_active_try_catch_id()
                    if catch_id:
                        logger.info(
                            f"Node error captured by try block, routing to catch: {catch_id}"
                        )
                        nodes_to_execute.insert(0, catch_id)
                        continue
                elif self.settings.continue_on_error:
                    logger.warning(
                        f"Node {current_node_id} failed but continue_on_error is enabled"
                    )
                else:
                    error_msg = f"Node {current_node_id} execution failed"
                    logger.warning(
                        f"Stopping workflow due to node error: {current_node_id}"
                    )
                    self._execution_failed = True
                    self._execution_error = (
                        result.get("error", error_msg) if result else error_msg
                    )
                    break

            # Check if target node was reached (Run-To-Node feature)
            if success and self.settings.target_node_id == current_node_id:
                self._target_reached = True
                logger.info(
                    f"Target node {current_node_id} reached - execution complete"
                )
                break

            # Handle special execution result keys
            if result:
                # Handle loop_back_to (ForLoop/WhileLoop end nodes)
                if "loop_back_to" in result:
                    loop_start_id = result["loop_back_to"]
                    logger.debug(f"Loop back to: {loop_start_id}")
                    nodes_to_execute.insert(0, loop_start_id)
                    continue

                # Handle route_to_catch (TryEnd node when error occurred)
                if "route_to_catch" in result:
                    catch_id = result["route_to_catch"]
                    if catch_id:
                        logger.info(f"Routing to catch node: {catch_id}")
                        nodes_to_execute.insert(0, catch_id)
                        continue

                # Handle error_captured (exception caught by try block)
                if result.get("error_captured"):
                    catch_id = self._find_active_try_catch_id()
                    if catch_id:
                        logger.info(f"Error captured - routing to catch: {catch_id}")
                        nodes_to_execute.insert(0, catch_id)
                        continue

            # Handle parallel execution (ForkNode)
            if result and "parallel_branches" in result:
                await self._execute_parallel_branches(result)
                # After parallel execution, continue to JoinNode
                join_id = result.get("paired_join_id")
                if join_id:
                    nodes_to_execute.insert(0, join_id)
                continue

            # Handle parallel foreach batch (ParallelForEachNode)
            if result and "parallel_foreach_batch" in result:
                await self._execute_parallel_foreach_batch(result, current_node_id)
                # Loop back to ParallelForEachNode for next batch
                nodes_to_execute.insert(0, current_node_id)
                continue

            # Get next nodes based on execution result
            next_node_ids = self.orchestrator.get_next_nodes(current_node_id, result)

            # Add next nodes to queue
            nodes_to_execute.extend(next_node_ids)

    # ========================================================================
    # PARALLEL EXECUTION SUPPORT
    # ========================================================================

    async def _execute_parallel_workflows(self, start_nodes: List[NodeId]) -> None:
        """
        Execute multiple workflows concurrently from different StartNodes.

        Used for "Run All" (Shift+F3) feature where multiple independent
        workflows on the same canvas execute in parallel.

        Design:
        - Variables are SHARED between workflows (same dict reference)
        - Browsers are SEPARATE (each workflow gets its own BrowserResourceManager)
        - Failures are isolated (one workflow failing doesn't stop others)

        Args:
            start_nodes: List of StartNode IDs to execute concurrently
        """
        logger.info(f"Starting {len(start_nodes)} parallel workflows")

        self._emit_event(
            EventType.WORKFLOW_PROGRESS,
            {"message": f"Starting {len(start_nodes)} parallel workflows"},
        )

        async def execute_single_workflow(
            start_id: NodeId, index: int
        ) -> Tuple[str, bool]:
            """Execute one workflow from its StartNode."""
            workflow_name = f"workflow_{index}"
            try:
                # Create context with SHARED variables but SEPARATE browser
                workflow_context = self.context.create_workflow_context(workflow_name)

                # Execute from this start node using the workflow context
                await self._execute_from_node_with_context(start_id, workflow_context)

                # Cleanup this workflow's browser resources
                try:
                    await workflow_context._resources.cleanup()
                except Exception as cleanup_err:
                    logger.warning(f"{workflow_name} cleanup error: {cleanup_err}")

                return workflow_name, True

            except Exception as e:
                logger.error(f"{workflow_name} failed: {e}")
                return workflow_name, False

        # Execute all workflows concurrently (continue on failure)
        tasks = [
            execute_single_workflow(start_id, i)
            for i, start_id in enumerate(start_nodes)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successes/failures
        success_count = 0
        error_count = 0
        for r in results:
            if isinstance(r, Exception):
                error_count += 1
            elif r[1]:  # r is (workflow_name, success)
                success_count += 1
            else:
                error_count += 1

        logger.info(
            f"Parallel workflows completed: {success_count} success, {error_count} errors"
        )

        self._emit_event(
            EventType.WORKFLOW_PROGRESS,
            {
                "message": "Parallel workflows completed",
                "success_count": success_count,
                "error_count": error_count,
            },
        )

        # Mark as failed if ALL workflows failed
        if success_count == 0 and error_count > 0:
            self._execution_failed = True
            self._execution_error = f"All {error_count} parallel workflows failed"

    async def _execute_from_node_with_context(
        self, start_node_id: NodeId, context: ExecutionContext
    ) -> None:
        """
        Execute workflow from a node using a specified context.

        Similar to _execute_from_node but uses provided context instead of
        self.context. Used for parallel workflow execution where each
        workflow needs its own context (for separate browser).

        Args:
            start_node_id: Node ID to start execution from
            context: ExecutionContext to use for this execution
        """
        nodes_to_execute: List[NodeId] = [start_node_id]
        executed_in_workflow: Set[NodeId] = set()

        while nodes_to_execute and not self._stop_requested:
            # CHECKPOINT: Wait if paused
            if not self.pause_event.is_set():
                await self.pause_event.wait()

            if self._stop_requested:
                break

            current_node_id = nodes_to_execute.pop(0)

            # Skip if already executed (except for loops)
            is_loop_node = self.orchestrator.is_control_flow_node(current_node_id)
            if current_node_id in executed_in_workflow and not is_loop_node:
                continue

            # Get node instance
            try:
                node = self._get_node_instance(current_node_id)
            except ValueError as e:
                logger.error(f"Node {current_node_id} not found: {e}")
                break

            # Transfer data from connected input ports
            for connection in self.workflow.connections:
                if connection.target_node == current_node_id:
                    self._transfer_data(connection)

            # Execute node with the provided context
            try:
                context.set_current_node(current_node_id)
                result = await asyncio.wait_for(
                    node.execute(context), timeout=self.settings.node_timeout
                )
            except asyncio.TimeoutError:
                logger.error(
                    f"Node {current_node_id} timed out after {self.settings.node_timeout}s"
                )
                break
            except Exception as e:
                logger.error(f"Node {current_node_id} failed: {e}")
                if not self.settings.continue_on_error:
                    break
                continue

            if not result or not result.get("success", False):
                if not self.settings.continue_on_error:
                    break
                continue

            executed_in_workflow.add(current_node_id)

            # Handle special result keys
            if result:
                if "loop_back_to" in result:
                    loop_start_id = result["loop_back_to"]
                    nodes_to_execute.insert(0, loop_start_id)
                    continue

            # Get next nodes
            next_node_ids = self.orchestrator.get_next_nodes(current_node_id, result)
            nodes_to_execute.extend(next_node_ids)

    async def _execute_parallel_branches(self, fork_result: Dict[str, Any]) -> None:
        """
        Execute parallel branches from a ForkNode concurrently.

        Creates isolated contexts for each branch, executes them with
        asyncio.gather, and stores results for the JoinNode.

        Args:
            fork_result: Result dict from ForkNode containing:
                - parallel_branches: List of branch port names
                - fork_id: ForkNode ID for result storage
                - paired_join_id: Target JoinNode ID
                - fail_fast: Whether to cancel on first failure
        """
        branches = fork_result.get("parallel_branches", [])
        fork_id = fork_result.get("fork_id", "")
        fail_fast = fork_result.get("fail_fast", False)

        if not branches:
            logger.warning("ForkNode returned no branches to execute")
            return

        logger.info(
            f"Executing {len(branches)} parallel branches (fail_fast={fail_fast})"
        )

        self._emit_event(
            EventType.WORKFLOW_PROGRESS,
            {
                "message": f"Starting {len(branches)} parallel branches",
                "fork_id": fork_id,
                "branches": branches,
            },
        )

        async def execute_branch(branch_port: str) -> Tuple[str, Dict[str, Any], bool]:
            """Execute a single branch and return its results."""
            try:
                # Get target node for this branch
                target_node_id = None
                for connection in self.workflow.connections:
                    if (
                        connection.source_node == fork_id
                        and connection.source_port == branch_port
                    ):
                        target_node_id = connection.target_node
                        break

                if not target_node_id:
                    logger.warning(f"No target node found for branch {branch_port}")
                    return branch_port, {}, True

                # Create isolated context for this branch
                branch_context = self.context.clone_for_branch(branch_port)

                # Execute branch nodes until we hit JoinNode or terminal
                await self._execute_branch_to_join(
                    target_node_id, branch_context, fork_result.get("paired_join_id")
                )

                # Return branch results (variables)
                return branch_port, branch_context.variables, True

            except Exception as e:
                logger.error(f"Branch {branch_port} failed: {e}")
                return branch_port, {"_error": str(e)}, False

        # Execute all branches concurrently
        if fail_fast:
            # With fail_fast, we use gather with return_exceptions=False
            # so first exception cancels others
            try:
                tasks = [execute_branch(port) for port in branches]
                results = await asyncio.gather(*tasks)
            except Exception as e:
                logger.error(f"Parallel execution failed (fail_fast): {e}")
                results = [(branches[0], {"_error": str(e)}, False)]
        else:
            # Without fail_fast, capture all results including errors
            tasks = [execute_branch(port) for port in branches]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        branch_results: Dict[str, Any] = {}
        success_count = 0
        error_count = 0

        for result in results:
            if isinstance(result, Exception):
                error_count += 1
                branch_results[f"error_{error_count}"] = {"_error": str(result)}
            else:
                branch_port, variables, success = result
                branch_results[branch_port] = variables
                if success:
                    success_count += 1
                else:
                    error_count += 1

        # Store results for JoinNode
        results_key = f"{fork_id}_branch_results"
        self.context.set_variable(results_key, branch_results)

        logger.info(
            f"Parallel branches completed: {success_count} success, {error_count} errors"
        )

        self._emit_event(
            EventType.WORKFLOW_PROGRESS,
            {
                "message": "Parallel branches completed",
                "fork_id": fork_id,
                "success_count": success_count,
                "error_count": error_count,
            },
        )

    async def _execute_branch_to_join(
        self,
        start_node_id: str,
        branch_context: ExecutionContext,
        join_node_id: Optional[str],
    ) -> None:
        """
        Execute a branch from start_node until reaching JoinNode or terminal.

        Args:
            start_node_id: Node ID to start execution from
            branch_context: Isolated context for this branch
            join_node_id: JoinNode ID where branch should stop
        """
        nodes_to_execute = [start_node_id]
        executed_in_branch: Set[str] = set()

        while nodes_to_execute and not self._stop_requested:
            current_node_id = nodes_to_execute.pop(0)

            # Stop at JoinNode - don't execute it in branch
            if current_node_id == join_node_id:
                break

            # Skip if already executed in this branch
            if current_node_id in executed_in_branch:
                continue

            # Get node instance
            try:
                node = self._get_node_instance(current_node_id)
            except ValueError as e:
                logger.error(f"Node {current_node_id} not found in branch: {e}")
                break

            # Transfer data from connected input ports
            for connection in self.workflow.connections:
                if connection.target_node == current_node_id:
                    self._transfer_data(connection)

            # Execute node with branch context
            try:
                result = await asyncio.wait_for(
                    node.execute(branch_context), timeout=self.settings.node_timeout
                )
            except asyncio.TimeoutError:
                logger.error(f"Node {current_node_id} timed out in branch")
                break
            except Exception as e:
                logger.error(f"Node {current_node_id} failed in branch: {e}")
                break

            executed_in_branch.add(current_node_id)

            # Handle result
            if not result or not result.get("success", False):
                logger.warning(f"Node {current_node_id} failed in branch")
                break

            # Get next nodes (don't handle special parallel keys in branches)
            if "loop_back_to" in result:
                loop_start_id = result["loop_back_to"]
                nodes_to_execute.insert(0, loop_start_id)
                continue

            next_node_ids = self.orchestrator.get_next_nodes(current_node_id, result)
            nodes_to_execute.extend(next_node_ids)

    async def _execute_parallel_foreach_batch(
        self, foreach_result: Dict[str, Any], foreach_node_id: str
    ) -> None:
        """
        Execute a batch of items from ParallelForEachNode concurrently.

        Args:
            foreach_result: Result dict from ParallelForEachNode containing:
                - parallel_foreach_batch: Batch info (items, indices, body_port)
                - foreach_id: ParallelForEachNode ID
                - fail_fast: Whether to stop on first failure
                - timeout_per_item: Timeout per item
        """
        batch_info = foreach_result.get("parallel_foreach_batch", {})
        items = batch_info.get("items", [])
        indices = batch_info.get("indices", [])
        body_port = batch_info.get("body_port", "body")
        state_key = batch_info.get("state_key", "")
        fail_fast = foreach_result.get("fail_fast", False)
        timeout_per_item = foreach_result.get("timeout_per_item", 60)

        if not items:
            return

        logger.info(f"Processing parallel batch: {len(items)} items")

        # Get target node for body port
        body_node_id = None
        for connection in self.workflow.connections:
            if (
                connection.source_node == foreach_node_id
                and connection.source_port == body_port
            ):
                body_node_id = connection.target_node
                break

        if not body_node_id:
            logger.warning(
                f"No body node connected to ParallelForEach {foreach_node_id}"
            )
            return

        async def process_item(item: Any, index: int) -> Tuple[int, Any, bool]:
            """Process a single item and return result."""
            try:
                # Create isolated context for this item
                item_context = self.context.clone_for_branch(f"item_{index}")
                item_context.set_variable("current_item", item)
                item_context.set_variable("current_index", index)

                # Set output values on the ParallelForEachNode for this context
                foreach_node = self._get_node_instance(foreach_node_id)
                foreach_node.set_output_value("current_item", item)
                foreach_node.set_output_value("current_index", index)

                # Execute body chain for this item (until we loop back or hit terminal)
                await asyncio.wait_for(
                    self._execute_item_body(
                        body_node_id, item_context, foreach_node_id
                    ),
                    timeout=timeout_per_item,
                )

                # Get result from context
                result = item_context.get_variable("_item_result", item)
                return index, result, True

            except asyncio.TimeoutError:
                logger.error(f"Item {index} timed out after {timeout_per_item}s")
                return index, None, False
            except Exception as e:
                logger.error(f"Item {index} failed: {e}")
                return index, None, False

        # Execute all items in batch concurrently
        tasks = [process_item(item, idx) for item, idx in zip(items, indices)]

        if fail_fast:
            try:
                results = await asyncio.gather(*tasks)
            except Exception as e:
                logger.error(f"Batch processing failed (fail_fast): {e}")
                results = []
        else:
            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect results and update state
        state = self.context.get_variable(state_key, {})
        batch_results = state.get("results", [])
        batch_errors = state.get("errors", [])

        for result in results:
            if isinstance(result, Exception):
                batch_errors.append(str(result))
            else:
                idx, value, success = result
                if success:
                    batch_results.append(value)
                else:
                    batch_errors.append(f"Item {idx} failed")

        # Update state
        state["results"] = batch_results
        state["errors"] = batch_errors
        self.context.set_variable(state_key, state)

        logger.info(
            f"Batch completed: {len(batch_results)} results, {len(batch_errors)} errors"
        )

    async def _execute_item_body(
        self, start_node_id: str, item_context: ExecutionContext, foreach_node_id: str
    ) -> None:
        """
        Execute the body chain for a single item in ParallelForEach.

        Executes until reaching a terminal node or looping back to foreach.

        Args:
            start_node_id: First node in the body chain
            item_context: Isolated context for this item
            foreach_node_id: ParallelForEachNode ID to detect loop-back
        """
        nodes_to_execute = [start_node_id]
        executed: Set[str] = set()
        max_nodes = 100  # Safety limit

        while nodes_to_execute and len(executed) < max_nodes:
            current_node_id = nodes_to_execute.pop(0)

            # Stop if we'd loop back to the foreach node
            if current_node_id == foreach_node_id:
                break

            if current_node_id in executed:
                continue

            try:
                node = self._get_node_instance(current_node_id)
            except ValueError:
                break

            # Transfer data
            for connection in self.workflow.connections:
                if connection.target_node == current_node_id:
                    self._transfer_data(connection)

            # Execute
            try:
                result = await node.execute(item_context)
            except Exception as e:
                logger.error(f"Item body node {current_node_id} failed: {e}")
                break

            executed.add(current_node_id)

            if not result or not result.get("success", False):
                break

            # Handle loop_back_to
            if "loop_back_to" in result:
                loop_id = result["loop_back_to"]
                if loop_id != foreach_node_id:
                    nodes_to_execute.insert(0, loop_id)
                continue

            # Get next nodes
            next_ids = self.orchestrator.get_next_nodes(current_node_id, result)
            nodes_to_execute.extend(next_ids)

    def stop(self) -> None:
        """Stop workflow execution."""
        self._stop_requested = True
        logger.info("Workflow stop requested")

    async def _pause_checkpoint(self) -> None:
        """
        Pause checkpoint - wait if pause_event is cleared.

        This method should be called between nodes and optionally
        during long-running node operations to support pause/resume.
        """
        if not self.pause_event.is_set():
            logger.info("Workflow paused at checkpoint")
            self._emit_event(
                EventType.WORKFLOW_PAUSED, {"current_node": self.current_node_id}
            )
            await self.pause_event.wait()  # Block until resumed
            logger.info("Workflow resumed from pause")
            self._emit_event(
                EventType.WORKFLOW_RESUMED, {"current_node": self.current_node_id}
            )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ExecuteWorkflowUseCase("
            f"workflow='{self.workflow.metadata.name}', "
            f"nodes={len(self.workflow.nodes)})"
        )
