"""
CasareRPA - Application Use Case: Execute Workflow
Coordinates workflow execution across domain and infrastructure layers.

This use case orchestrates workflow execution by:
- Using ExecutionOrchestrator (domain) for routing decisions
- Using ExecutionContext (infrastructure) for execution and resources
- Using helper services for node execution, state management, and data transfer
- Emitting events via EventBus for progress tracking

Architecture:
- Domain logic: ExecutionOrchestrator makes routing decisions
- Infrastructure: ExecutionContext manages Playwright resources
- Application: This class coordinates them and publishes events

Refactored: Extracted helper services for Single Responsibility:
- ExecutionStateManager: State tracking, progress, pause/resume
- NodeExecutor: Node execution with metrics and lifecycle events
- VariableResolver: Data transfer between nodes, port validation
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from loguru import logger

from casare_rpa.domain.entities.workflow import WorkflowSchema
from casare_rpa.domain.events import EventBus
from casare_rpa.domain.services.execution_orchestrator import ExecutionOrchestrator
from casare_rpa.domain.value_objects.types import EventType, NodeId
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.utils.performance.performance_metrics import get_metrics
from casare_rpa.utils.workflow.workflow_loader import NODE_TYPE_MAP

# Import extracted helper services
from casare_rpa.application.use_cases.execution_state_manager import (
    ExecutionSettings,
    ExecutionStateManager,
)
from casare_rpa.application.use_cases.node_executor import (
    NodeExecutor,
    NodeExecutorWithTryCatch,
)
from casare_rpa.application.use_cases.variable_resolver import (
    VariableResolver,
    TryCatchErrorHandler,
)


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


class ExecuteWorkflowUseCase:
    """
    Application use case for executing workflows.

    Coordinates:
    - Domain: ExecutionOrchestrator for routing logic
    - Domain: Workflow schema for node/connection data
    - Infrastructure: ExecutionContext for resources and variables
    - Infrastructure: EventBus for progress notifications
    - Services: ExecutionStateManager, NodeExecutor, VariableResolver
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

        # Pause/resume support
        self.pause_event = pause_event or asyncio.Event()
        self.pause_event.set()  # Initially not paused

        # State management (extracted service)
        self.state_manager = ExecutionStateManager(
            workflow=workflow,
            orchestrator=self.orchestrator,
            event_bus=event_bus,
            settings=self.settings,
            pause_event=self.pause_event,
        )

        # Infrastructure components (created during execution)
        self.context: Optional[ExecutionContext] = None

        # Node instance cache (for dict-based workflows)
        self._node_instances: Dict[str, Any] = {}

        # Helper services (initialized during execution)
        self._node_executor: Optional[NodeExecutorWithTryCatch] = None
        self._variable_resolver: Optional[VariableResolver] = None
        self._error_handler: Optional[TryCatchErrorHandler] = None

    # ========================================================================
    # BACKWARD COMPATIBILITY - Delegate to state manager
    # ========================================================================

    @property
    def executed_nodes(self) -> Set[NodeId]:
        """Get executed nodes set."""
        return self.state_manager.executed_nodes

    @property
    def current_node_id(self) -> Optional[NodeId]:
        """Get current node ID."""
        return self.state_manager.current_node_id

    @property
    def start_time(self) -> Optional[datetime]:
        """Get start time."""
        return self.state_manager.start_time

    @property
    def end_time(self) -> Optional[datetime]:
        """Get end time."""
        return self.state_manager.end_time

    def stop(self) -> None:
        """Stop workflow execution."""
        self.state_manager.stop()

    # ========================================================================
    # NODE INSTANCE MANAGEMENT
    # ========================================================================

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

    def _store_node_outputs_in_context(self, node_id: str, node: Any) -> None:
        """
        Store node output values in context.variables for {{node_id.output}} resolution.

        This enables the UiPath/Power Automate style variable syntax where
        users can reference node outputs as {{node_id.output_port}} in subsequent nodes.

        Args:
            node_id: ID of the node that just executed
            node: The node instance with output values
        """
        if not self.context or not hasattr(node, "output_ports"):
            return

        # Get all output values from the node's output ports
        output_ports = getattr(node, "output_ports", {})
        if not output_ports:
            return

        # Store in context.variables as {node_id: {port: value, ...}}
        # Filter out exec ports
        data_outputs = {}
        for port_name, port in output_ports.items():
            if port_name.startswith("exec") or port_name.startswith("_exec"):
                continue
            value = port.get_value() if hasattr(port, "get_value") else None
            if value is not None:
                data_outputs[port_name] = value

        if data_outputs:
            self.context.set_variable(node_id, data_outputs)
            logger.debug(f"Stored outputs for {node_id}: {list(data_outputs.keys())}")

    # ========================================================================
    # MAIN EXECUTION
    # ========================================================================

    async def execute(self, run_all: bool = False) -> bool:
        """
        Execute the workflow.

        Args:
            run_all: If True, execute all StartNodes concurrently (Shift+F3).
                     If False, execute only the first StartNode (default F3).

        Returns:
            True if workflow completed successfully, False otherwise
        """
        self.state_manager.start_execution()

        # Create execution context
        self.context = ExecutionContext(
            workflow_name=self.workflow.metadata.name,
            initial_variables=self._initial_variables,
            project_context=self._project_context,
            pause_event=self.pause_event,
        )

        # Initialize helper services
        self._error_handler = TryCatchErrorHandler(self.context)
        self._variable_resolver = VariableResolver(
            workflow=self.workflow,
            node_getter=self._get_node_instance,
        )
        self._node_executor = NodeExecutorWithTryCatch(
            context=self.context,
            event_bus=self.event_bus,
            node_timeout=self.settings.node_timeout,
            progress_calculator=self.state_manager.calculate_progress,
            error_capturer=self._error_handler.capture_error,
        )

        self.state_manager.emit_event(
            EventType.WORKFLOW_STARTED,
            {
                "workflow_name": self.workflow.metadata.name,
                "total_nodes": self.state_manager.total_nodes,
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

            # Handle completion status
            return self._finalize_execution()

        except Exception as e:
            self.state_manager.mark_completed()
            duration = self.state_manager.duration

            self.state_manager.emit_event(
                EventType.WORKFLOW_ERROR,
                {
                    "error": str(e),
                    "executed_nodes": len(self.state_manager.executed_nodes),
                },
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

            self.state_manager.set_current_node(None)

    def _finalize_execution(self) -> bool:
        """
        Finalize execution and emit completion events.

        Returns:
            True if execution completed successfully, False otherwise
        """
        self.state_manager.mark_completed()
        duration = self.state_manager.duration

        # Check for execution failure
        if self.state_manager.is_failed:
            self.state_manager.emit_event(
                EventType.WORKFLOW_ERROR,
                {
                    "error": self.state_manager.execution_error or "Execution failed",
                    "executed_nodes": len(self.state_manager.executed_nodes),
                },
            )
            logger.error(
                f"Workflow execution failed: {self.state_manager.execution_error}"
            )

            get_metrics().record_workflow_complete(
                self.workflow.metadata.name, duration * 1000, success=False
            )
            return False

        # Check if stopped by user
        if self.state_manager.is_stopped:
            self.state_manager.emit_event(
                EventType.WORKFLOW_STOPPED,
                {
                    "executed_nodes": len(self.state_manager.executed_nodes),
                    "total_nodes": len(self.workflow.nodes),
                },
            )
            logger.info("Workflow execution stopped by user")

            get_metrics().record_workflow_complete(
                self.workflow.metadata.name, duration * 1000, success=False
            )
            return False

        # Success
        self.context._state.mark_completed()

        # Export final variables for Output tab display
        final_variables = {
            k: v for k, v in self.context.variables.items() if not k.startswith("_")
        }

        self.state_manager.emit_event(
            EventType.WORKFLOW_COMPLETED,
            {
                "executed_nodes": len(self.state_manager.executed_nodes),
                "total_nodes": len(self.workflow.nodes),
                "duration": duration,
                "variables": final_variables,
            },
        )

        logger.info(
            f"Workflow completed successfully in {duration:.2f}s "
            f"({len(self.state_manager.executed_nodes)} nodes)"
        )

        get_metrics().record_workflow_complete(
            self.workflow.metadata.name, duration * 1000, success=True
        )
        return True

    # ========================================================================
    # SINGLE NODE EXECUTION
    # ========================================================================

    async def _execute_single_node(self, node_id: NodeId) -> None:
        """
        Execute a single node in isolation (F5 mode).

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
            self.state_manager.mark_failed(error_msg)
            return

        # Transfer data from connected input ports
        self._variable_resolver.transfer_inputs_to_node(node_id)

        # Execute the node
        result = await self._node_executor.execute(node)

        if result.success:
            # Store node outputs in context for {{node_id.output}} variable resolution
            self._store_node_outputs_in_context(node_id, node)
        else:
            error_msg = f"Node {node_id} execution failed"
            self.state_manager.mark_failed(
                result.result.get("error", error_msg) if result.result else error_msg
            )

    # ========================================================================
    # SEQUENTIAL EXECUTION
    # ========================================================================

    async def _execute_from_node(self, start_node_id: NodeId) -> None:
        """
        Execute workflow starting from a specific node.

        Args:
            start_node_id: Node ID to start execution from
        """
        nodes_to_execute: List[NodeId] = [start_node_id]

        while nodes_to_execute and not self.state_manager.is_stopped:
            # CHECKPOINT: Wait if paused
            await self.state_manager.pause_checkpoint()

            # Check stop signal after resuming from pause
            if self.state_manager.is_stopped:
                break

            current_node_id = nodes_to_execute.pop(0)

            # Skip if already executed (except for loops)
            is_loop_node = self.orchestrator.is_control_flow_node(current_node_id)
            if (
                current_node_id in self.state_manager.executed_nodes
                and not is_loop_node
            ):
                continue

            # Skip nodes not in subgraph (Run-To-Node filtering)
            if not self.state_manager.should_execute_node(current_node_id):
                logger.debug(f"Skipping node {current_node_id} (not in subgraph)")
                self.state_manager.emit_event(
                    EventType.NODE_SKIPPED,
                    {
                        "node_id": current_node_id,
                        "reason": "not_in_subgraph",
                        "timestamp": datetime.now().isoformat(),
                    },
                )
                continue

            # Get node instance
            try:
                node = self._get_node_instance(current_node_id)
            except ValueError as e:
                error_msg = f"Node {current_node_id} not found in workflow: {e}"
                logger.error(error_msg)
                if not self.settings.continue_on_error:
                    self.state_manager.mark_failed(error_msg)
                    break
                continue

            # Transfer data from connected input ports
            self._variable_resolver.transfer_inputs_to_node(current_node_id)

            # Execute the node
            exec_result = await self._node_executor.execute(node)

            if not exec_result.success:
                # Handle failure with try-catch support
                if self._handle_execution_failure(
                    current_node_id, exec_result.result, nodes_to_execute
                ):
                    continue
                break

            # Mark node as executed
            self.state_manager.mark_node_executed(current_node_id)

            # Store node outputs in context for {{node_id.output}} variable resolution
            self._store_node_outputs_in_context(current_node_id, node)

            # Validate output ports
            if exec_result.result:
                self._variable_resolver.validate_output_ports(node, exec_result.result)

            # Check if target node was reached (Run-To-Node feature)
            if self.state_manager.mark_target_reached(current_node_id):
                break

            # Handle special execution results
            if exec_result.result:
                next_nodes = self._handle_special_results(
                    current_node_id, exec_result, nodes_to_execute
                )
                if next_nodes is not None:
                    continue

            # Get next nodes based on execution result
            next_node_ids = self.orchestrator.get_next_nodes(
                current_node_id, exec_result.result
            )
            nodes_to_execute.extend(next_node_ids)

    def _handle_execution_failure(
        self,
        node_id: NodeId,
        result: Optional[Dict[str, Any]],
        nodes_to_execute: List[NodeId],
    ) -> bool:
        """
        Handle node execution failure with try-catch support.

        Args:
            node_id: Node ID that failed
            result: Execution result
            nodes_to_execute: Queue of nodes to execute

        Returns:
            True if execution should continue (error captured), False to stop
        """
        # Check if error was captured by a try block
        error_captured = self._error_handler.capture_from_result(result, node_id)

        if error_captured:
            # Route to catch node
            catch_id = self._error_handler.find_catch_node_id()
            if catch_id:
                logger.info(
                    f"Node error captured by try block, routing to catch: {catch_id}"
                )
                nodes_to_execute.insert(0, catch_id)
                return True

        if self.settings.continue_on_error:
            logger.warning(f"Node {node_id} failed but continue_on_error is enabled")
            return True

        # Stop execution
        error_msg = result.get("error", "Unknown error") if result else "Unknown error"
        logger.warning(f"Stopping workflow due to node error: {node_id}")
        self.state_manager.mark_failed(error_msg)
        return False

    def _handle_special_results(
        self,
        current_node_id: NodeId,
        exec_result: Any,
        nodes_to_execute: List[NodeId],
    ) -> Optional[bool]:
        """
        Handle special execution result keys.

        Args:
            current_node_id: Current node ID
            exec_result: Execution result
            nodes_to_execute: Queue of nodes to execute

        Returns:
            True if special handling applied (continue loop), None otherwise
        """
        result = exec_result.result
        if not result:
            return None

        # Handle loop_back_to (ForLoop/WhileLoop end nodes)
        if "loop_back_to" in result:
            loop_start_id = result["loop_back_to"]
            logger.debug(f"Loop back to: {loop_start_id}")

            # Clear loop body nodes from executed_nodes so they can re-execute
            # current_node_id is the ForLoopEndNode or WhileLoopEndNode
            body_nodes = self.orchestrator.find_loop_body_nodes(
                loop_start_id, current_node_id
            )
            for body_node_id in body_nodes:
                self.state_manager.executed_nodes.discard(body_node_id)
            logger.debug(f"Cleared {len(body_nodes)} loop body nodes for re-execution")

            nodes_to_execute.insert(0, loop_start_id)
            return True

        # Handle route_to_catch (TryEnd node when error occurred)
        if "route_to_catch" in result:
            catch_id = result["route_to_catch"]
            if catch_id:
                logger.info(f"Routing to catch node: {catch_id}")
                nodes_to_execute.insert(0, catch_id)
                return True

        # Handle error_captured (exception caught by try block)
        if result.get("error_captured") or exec_result.error_captured:
            catch_id = self._error_handler.find_catch_node_id()
            if catch_id:
                logger.info(f"Error captured - routing to catch: {catch_id}")
                nodes_to_execute.insert(0, catch_id)
                return True

        # Handle parallel execution (ForkNode)
        if "parallel_branches" in result:
            asyncio.create_task(
                self._execute_parallel_branches_async(result, nodes_to_execute)
            )
            return True

        # Handle parallel foreach batch (ParallelForEachNode)
        if "parallel_foreach_batch" in result:
            asyncio.create_task(
                self._execute_parallel_foreach_batch_async(
                    result, current_node_id, nodes_to_execute
                )
            )
            return True

        return None

    async def _execute_parallel_branches_async(
        self, fork_result: Dict[str, Any], nodes_to_execute: List[NodeId]
    ) -> None:
        """Execute parallel branches and update queue."""
        await self._execute_parallel_branches(fork_result)
        # After parallel execution, continue to JoinNode
        join_id = fork_result.get("paired_join_id")
        if join_id:
            nodes_to_execute.insert(0, join_id)

    async def _execute_parallel_foreach_batch_async(
        self,
        foreach_result: Dict[str, Any],
        current_node_id: str,
        nodes_to_execute: List[NodeId],
    ) -> None:
        """Execute parallel foreach batch and loop back."""
        await self._execute_parallel_foreach_batch(foreach_result, current_node_id)
        # Loop back to ParallelForEachNode for next batch
        nodes_to_execute.insert(0, current_node_id)

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

        self.state_manager.emit_event(
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

        self.state_manager.emit_event(
            EventType.WORKFLOW_PROGRESS,
            {
                "message": "Parallel workflows completed",
                "success_count": success_count,
                "error_count": error_count,
            },
        )

        # Mark as failed if ALL workflows failed
        if success_count == 0 and error_count > 0:
            self.state_manager.mark_failed(
                f"All {error_count} parallel workflows failed"
            )

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

        # Create temporary node executor for this context
        temp_executor = NodeExecutor(
            context=context,
            event_bus=self.event_bus,
            node_timeout=self.settings.node_timeout,
            progress_calculator=self.state_manager.calculate_progress,
        )

        while nodes_to_execute and not self.state_manager.is_stopped:
            # CHECKPOINT: Wait if paused
            if not self.pause_event.is_set():
                await self.pause_event.wait()

            if self.state_manager.is_stopped:
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
            self._variable_resolver.transfer_inputs_to_node(current_node_id)

            # Execute node with the provided context
            exec_result = await temp_executor.execute(node)

            if not exec_result.success:
                if not self.settings.continue_on_error:
                    break
                continue

            executed_in_workflow.add(current_node_id)

            # Store node outputs in context for {{node_id.output}} variable resolution
            self._store_node_outputs_in_context(current_node_id, node)

            # Handle special result keys
            if exec_result.result and "loop_back_to" in exec_result.result:
                loop_start_id = exec_result.result["loop_back_to"]

                # Clear loop body nodes from executed_in_workflow so they can re-execute
                body_nodes = self.orchestrator.find_loop_body_nodes(
                    loop_start_id, current_node_id
                )
                for body_node_id in body_nodes:
                    executed_in_workflow.discard(body_node_id)
                logger.debug(
                    f"Cleared {len(body_nodes)} loop body nodes for re-execution"
                )

                nodes_to_execute.insert(0, loop_start_id)
                continue

            # Get next nodes
            next_node_ids = self.orchestrator.get_next_nodes(
                current_node_id, exec_result.result
            )
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

        self.state_manager.emit_event(
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
            try:
                tasks = [execute_branch(port) for port in branches]
                results = await asyncio.gather(*tasks)
            except Exception as e:
                logger.error(f"Parallel execution failed (fail_fast): {e}")
                results = [(branches[0], {"_error": str(e)}, False)]
        else:
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

        self.state_manager.emit_event(
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

        # Create temporary executor for branch context
        branch_executor = NodeExecutor(
            context=branch_context,
            event_bus=self.event_bus,
            node_timeout=self.settings.node_timeout,
        )

        while nodes_to_execute and not self.state_manager.is_stopped:
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
            self._variable_resolver.transfer_inputs_to_node(current_node_id)

            # Execute node with branch context
            exec_result = await branch_executor.execute(node)

            if not exec_result.success:
                logger.warning(f"Node {current_node_id} failed in branch")
                break

            executed_in_branch.add(current_node_id)

            # Store node outputs in context for {{node_id.output}} variable resolution
            self._store_node_outputs_in_context(current_node_id, node)

            # Handle loop_back_to
            if exec_result.result and "loop_back_to" in exec_result.result:
                loop_start_id = exec_result.result["loop_back_to"]
                nodes_to_execute.insert(0, loop_start_id)
                continue

            next_node_ids = self.orchestrator.get_next_nodes(
                current_node_id, exec_result.result
            )
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

                # Execute body chain for this item
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

        Args:
            start_node_id: First node in the body chain
            item_context: Isolated context for this item
            foreach_node_id: ParallelForEachNode ID to detect loop-back
        """
        nodes_to_execute = [start_node_id]
        executed: Set[str] = set()
        max_nodes = 100  # Safety limit

        # Create executor for item context
        item_executor = NodeExecutor(
            context=item_context,
            event_bus=self.event_bus,
            node_timeout=self.settings.node_timeout,
        )

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
            self._variable_resolver.transfer_inputs_to_node(current_node_id)

            # Execute
            exec_result = await item_executor.execute(node)

            if not exec_result.success:
                break

            executed.add(current_node_id)

            # Store node outputs in context for {{node_id.output}} variable resolution
            self._store_node_outputs_in_context(current_node_id, node)

            # Handle loop_back_to
            if exec_result.result and "loop_back_to" in exec_result.result:
                loop_id = exec_result.result["loop_back_to"]
                if loop_id != foreach_node_id:
                    nodes_to_execute.insert(0, loop_id)
                continue

            # Get next nodes
            next_ids = self.orchestrator.get_next_nodes(
                current_node_id, exec_result.result
            )
            nodes_to_execute.extend(next_ids)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ExecuteWorkflowUseCase("
            f"workflow='{self.workflow.metadata.name}', "
            f"nodes={len(self.workflow.nodes)})"
        )
