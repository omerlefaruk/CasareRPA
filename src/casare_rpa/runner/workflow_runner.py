"""
CasareRPA - Workflow Runner
Executes workflows by running nodes in the correct order based on connections.
Supports parallel execution of independent branches for improved performance.
"""

import asyncio
from typing import Any, Dict, List, Optional, Set, Tuple
from datetime import datetime
from loguru import logger

from ..core.base_node import BaseNode
from ..core.workflow_schema import WorkflowSchema, NodeConnection
from ..core.execution_context import ExecutionContext
from ..core.types import NodeId, NodeStatus, EventType
from ..core.events import EventBus, Event
from ..utils.retry import (
    RetryConfig,
    RetryStats,
    classify_error,
    ErrorCategory,
)
from ..utils.parallel_executor import (
    DependencyGraph,
    ParallelExecutor,
    analyze_workflow_dependencies,
)
from ..utils.subgraph_calculator import SubgraphCalculator
from ..utils.performance_metrics import get_metrics

# Default timeout for node execution (in seconds)
DEFAULT_NODE_EXECUTION_TIMEOUT = 120  # 2 minutes


class ExecutionState:
    """Tracks the state of workflow execution."""
    
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    COMPLETED = "completed"
    ERROR = "error"


class WorkflowRunner:
    """
    Executes workflows asynchronously.

    Features:
    - Sequential node execution following connections
    - Parallel execution of independent branches
    - Async support for Playwright operations
    - Real-time progress tracking
    - Pause/Resume/Stop controls
    - Error handling and recovery
    """

    def __init__(
        self,
        workflow: WorkflowSchema,
        event_bus: Optional[EventBus] = None,
        retry_config: Optional[RetryConfig] = None,
        node_timeout: float = DEFAULT_NODE_EXECUTION_TIMEOUT,
        continue_on_error: bool = False,
        parallel_execution: bool = False,
        max_parallel_nodes: int = 4,
        target_node_id: Optional[NodeId] = None,
        initial_variables: Optional[Dict[str, Any]] = None,
        project_context: Optional[Any] = None,
    ) -> None:
        """
        Initialize workflow runner.

        Args:
            workflow: The workflow schema to execute
            event_bus: Optional event bus for progress updates
            retry_config: Configuration for automatic retry on transient errors
            node_timeout: Timeout for individual node execution in seconds
            continue_on_error: If True, continue workflow on node errors
            parallel_execution: If True, execute independent nodes in parallel
            max_parallel_nodes: Maximum number of nodes to run in parallel
            target_node_id: Optional target node for "Run To Node" feature.
                            If set, only nodes in the path to this target will be executed,
                            and execution will pause when the target is reached.
            initial_variables: Optional dict of variables to initialize in context
                               (from Variables Tab in bottom panel)
            project_context: Optional project context for project-scoped variables
        """
        self.workflow = workflow
        self._initial_variables = initial_variables or {}
        self._project_context = project_context

        # Import get_event_bus to get the global instance
        from ..core.events import get_event_bus
        self.event_bus = event_bus or get_event_bus()

        # Retry and timeout configuration
        self.retry_config = retry_config or RetryConfig(
            max_attempts=3,
            initial_delay=1.0,
            max_delay=30.0,
            backoff_multiplier=2.0,
            jitter=True,
        )
        self.node_timeout = node_timeout
        self.continue_on_error = continue_on_error
        self.retry_stats = RetryStats()

        # Parallel execution settings
        self.parallel_execution = parallel_execution
        self.max_parallel_nodes = max_parallel_nodes
        self._dependency_graph: Optional[DependencyGraph] = None
        self._parallel_executor: Optional[ParallelExecutor] = None

        # Execution state
        self.state = ExecutionState.IDLE
        self.context: Optional[ExecutionContext] = None
        self.current_node_id: Optional[NodeId] = None

        # Progress tracking
        self.executed_nodes: Set[NodeId] = set()
        self.total_nodes = len(workflow.nodes)
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

        # Control flags
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # Not paused initially
        self._stop_requested = False

        # Debug mode
        self.debug_mode: bool = False
        self.step_mode: bool = False
        self._step_event = asyncio.Event()
        self._step_event.set()  # Not waiting for step initially
        self.breakpoints: Set[NodeId] = set()
        self.execution_history: List[Dict[str, Any]] = []

        # Build dependency graph if parallel execution is enabled
        if self.parallel_execution:
            self._build_dependency_graph()

        # Run-to-node support (F4 feature)
        self._target_node_id = target_node_id
        self._subgraph_nodes: Optional[Set[NodeId]] = None
        self._target_reached = False

        # Calculate subgraph if target node is specified
        if target_node_id:
            self._calculate_subgraph(target_node_id)

        logger.info(
            f"WorkflowRunner initialized for workflow: {workflow.metadata.name} "
            f"(parallel={parallel_execution}, max_parallel={max_parallel_nodes}"
            f"{f', target={target_node_id}' if target_node_id else ''})"
        )
    
    @property
    def progress(self) -> float:
        """Get execution progress as percentage (0-100)."""
        if self.total_nodes == 0:
            return 0.0
        return (len(self.executed_nodes) / self.total_nodes) * 100
    
    @property
    def is_running(self) -> bool:
        """Check if workflow is currently running."""
        return self.state == ExecutionState.RUNNING
    
    @property
    def is_paused(self) -> bool:
        """Check if workflow is paused."""
        return self.state == ExecutionState.PAUSED
    
    def _emit_event(self, event_type: EventType, data: Dict[str, Any]) -> None:
        """Emit an event to the event bus."""
        if self.event_bus:
            event = Event(
                event_type=event_type,
                data=data,
                node_id=self.current_node_id
            )
            self.event_bus.publish(event)
    
    def _find_start_node(self) -> Optional[BaseNode]:
        """Find the StartNode in the workflow."""
        for node in self.workflow.nodes.values():
            if node.__class__.__name__ == "StartNode":
                return node
        return None

    def _calculate_subgraph(self, target_node_id: NodeId) -> None:
        """
        Calculate the subgraph of nodes required for Run-To-Node execution.

        This finds all nodes on paths from StartNode to the target node.
        Only these nodes will be executed when running to the target.

        Args:
            target_node_id: The target node to run to
        """
        start_node = self._find_start_node()
        if not start_node:
            logger.error("Cannot calculate subgraph: no StartNode found")
            return

        calculator = SubgraphCalculator(
            self.workflow.nodes,
            self.workflow.connections
        )

        # Check if target is reachable
        if not calculator.is_reachable(start_node.node_id, target_node_id):
            logger.error(f"Target node {target_node_id} is not reachable from StartNode")
            return

        # Calculate the subgraph
        self._subgraph_nodes = calculator.calculate_subgraph(
            start_node.node_id,
            target_node_id
        )

        # Update total_nodes to reflect only the subgraph
        self.total_nodes = len(self._subgraph_nodes)
        logger.info(f"Subgraph calculated: {self.total_nodes} nodes to execute")

    def _should_execute_node(self, node_id: NodeId) -> bool:
        """
        Check if a node should be executed based on subgraph filtering.

        If no target is set (full workflow run), all nodes are executed.
        If a target is set, only nodes in the subgraph are executed.

        Args:
            node_id: The node ID to check

        Returns:
            True if the node should be executed
        """
        if self._subgraph_nodes is None:
            return True  # No subgraph filter - execute all nodes
        return node_id in self._subgraph_nodes

    def _check_target_reached(self, node_id: NodeId) -> bool:
        """
        Check if the target node was just executed.

        If so, mark target as reached and pause execution.

        Args:
            node_id: The node that was just executed

        Returns:
            True if this was the target node
        """
        if self._target_node_id and node_id == self._target_node_id:
            self._target_reached = True
            logger.info(f"Target node {node_id} reached - pausing execution")
            return True
        return False

    @property
    def target_reached(self) -> bool:
        """Check if the target node has been reached."""
        return self._target_reached

    @property
    def has_target(self) -> bool:
        """Check if a target node is set for Run-To-Node mode."""
        return self._target_node_id is not None

    @property
    def subgraph_valid(self) -> bool:
        """Check if the subgraph was successfully calculated."""
        return self._subgraph_nodes is not None or self._target_node_id is None

    def _get_next_nodes(self, current_node_id: NodeId) -> List[BaseNode]:
        """
        Get the next nodes to execute based on connections.

        Args:
            current_node_id: ID of the current node

        Returns:
            List of nodes connected to the current node's output
        """
        next_nodes = []

        for connection in self.workflow.connections:
            if connection.source_node == current_node_id:
                # Found a connection from current node
                target_node_id = connection.target_node
                if target_node_id in self.workflow.nodes:
                    next_nodes.append(self.workflow.nodes[target_node_id])

        return next_nodes

    def _build_dependency_graph(self) -> None:
        """Build the dependency graph for parallel execution."""
        self._dependency_graph = analyze_workflow_dependencies(
            self.workflow.nodes, self.workflow.connections
        )
        self._parallel_executor = ParallelExecutor(
            max_concurrency=self.max_parallel_nodes,
            stop_on_error=not self.continue_on_error,
        )
        logger.debug("Dependency graph built for parallel execution")

    def _get_ready_nodes(self) -> List[NodeId]:
        """
        Get nodes that are ready to execute (all dependencies satisfied).

        Returns:
            List of node IDs ready to execute
        """
        if not self._dependency_graph:
            return []
        return self._dependency_graph.get_ready_nodes(self.executed_nodes)

    def _is_parallelizable_node(self, node: BaseNode) -> bool:
        """
        Check if a node can be executed in parallel.

        Some nodes (like control flow, browser operations) should run sequentially.

        Args:
            node: The node to check

        Returns:
            True if node can be parallelized
        """
        # Control flow nodes must run sequentially
        non_parallel_types = {
            "ForLoopStartNode",
            "ForLoopEndNode",
            "WhileLoopStartNode",
            "WhileLoopEndNode",
            "IfNode",
            "SwitchNode",
            "TryNode",
            "RetryNode",
            "BreakNode",
            "ContinueNode",
            # Browser nodes that share state
            "LaunchBrowserNode",
            "CloseBrowserNode",
            "NewTabNode",
        }
        return node.__class__.__name__ not in non_parallel_types

    def _transfer_data(self, connection: NodeConnection) -> None:
        """
        Transfer data from source port to target port.

        Args:
            connection: The connection defining source and target
        """
        source_node = self.workflow.nodes.get(connection.source_node)
        target_node = self.workflow.nodes.get(connection.target_node)

        if not source_node or not target_node:
            return

        # Get value from source output port
        value = source_node.get_output_value(connection.source_port)

        # Set value to target input port
        if value is not None:
            target_node.set_input_value(connection.target_port, value)
            # Log data transfers (non-exec) for debugging
            if "exec" not in connection.source_port.lower():
                logger.info(f"Data: {connection.source_port} -> {connection.target_port} = {repr(value)[:80]}")
    
    async def _execute_node_once(self, node: BaseNode) -> Dict[str, Any]:
        """
        Execute a single node once (internal method for retry wrapper).

        Args:
            node: The node to execute

        Returns:
            Execution result dictionary

        Raises:
            Exception: If execution fails
        """
        # Execute the node with timeout protection
        try:
            result = await asyncio.wait_for(
                node.execute(self.context),
                timeout=self.node_timeout
            )
            return result or {"success": False, "error": "No result returned"}
        except asyncio.TimeoutError:
            raise asyncio.TimeoutError(
                f"Node {node.node_id} timed out after {self.node_timeout}s"
            )

    async def _execute_node(self, node: BaseNode) -> tuple[bool, Optional[Dict[str, Any]]]:
        """
        Execute a single node with retry and timeout support.

        Args:
            node: The node to execute

        Returns:
            Tuple of (success: bool, result: dict) where result contains execution data
        """
        # Check if node is disabled (bypassed)
        if node.config.get("_disabled", False):
            logger.info(f"Node {node.node_id} is disabled - bypassing execution")
            node.status = NodeStatus.COMPLETED

            # Emit a special event for bypassed nodes
            self._emit_event(EventType.NODE_COMPLETED, {
                "node_id": node.node_id,
                "node_type": node.__class__.__name__,
                "bypassed": True,
                "execution_time": 0,
                "progress": self._calculate_progress()
            })

            # Return success so workflow continues, with bypass marker in result
            return True, {"success": True, "bypassed": True}

        self.current_node_id = node.node_id
        node.status = NodeStatus.RUNNING

        # Debug mode: check for breakpoint or step mode
        if self.debug_mode and (self.step_mode or node.node_id in self.breakpoints):
            logger.info(f"Breakpoint hit or step mode at node: {node.node_id}")
            self._emit_event(EventType.NODE_STARTED, {
                "node_id": node.node_id,
                "node_type": node.__class__.__name__,
                "breakpoint": True
            })

            # Wait for step command
            self._step_event.clear()
            await self._step_event.wait()

            # Reset for next step if still in step mode
            if self.step_mode:
                self._step_event.clear()

        self._emit_event(EventType.NODE_STARTED, {
            "node_id": node.node_id,
            "node_type": node.__class__.__name__
        })

        # Record start time for debug info
        import time
        start_time = time.time()

        # Record metrics for performance dashboard
        node_type = node.__class__.__name__
        get_metrics().record_node_start(node_type, node.node_id)

        try:
            # Validate node before execution
            if not node.validate():
                logger.error(f"Node validation failed: {node.node_id}")
                node.status = NodeStatus.ERROR
                self._emit_event(EventType.NODE_ERROR, {
                    "node_id": node.node_id,
                    "error": "Validation failed"
                })
                return False, None

            # Execute with retry logic
            result = None
            last_exception = None

            for attempt in range(1, self.retry_config.max_attempts + 1):
                try:
                    result = await self._execute_node_once(node)

                    # Record successful attempt
                    self.retry_stats.record_attempt(
                        success=result.get("success", False),
                        retry_delay=0 if attempt == 1 else self.retry_config.get_delay(attempt - 1)
                    )

                    if result.get("success", False):
                        break  # Success, exit retry loop

                    # Check if we should retry on failure result
                    error_msg = result.get("error", "Unknown error")
                    if attempt < self.retry_config.max_attempts:
                        # Check if this is a retry-able error
                        # For now, retry on any non-success result
                        delay = self.retry_config.get_delay(attempt)
                        logger.warning(
                            f"Node {node.node_id} attempt {attempt}/{self.retry_config.max_attempts} "
                            f"failed: {error_msg}. Retrying in {delay:.2f}s..."
                        )
                        self._emit_event(EventType.NODE_ERROR, {
                            "node_id": node.node_id,
                            "error": f"Attempt {attempt} failed: {error_msg}",
                            "retrying": True,
                            "attempt": attempt
                        })
                        await asyncio.sleep(delay)
                    else:
                        # Last attempt failed
                        break

                except Exception as e:
                    last_exception = e
                    error_category = classify_error(e)

                    self.retry_stats.record_attempt(
                        success=False,
                        retry_delay=self.retry_config.get_delay(attempt) if attempt > 1 else 0
                    )

                    if self.retry_config.should_retry(e, attempt):
                        delay = self.retry_config.get_delay(attempt)
                        logger.warning(
                            f"Node {node.node_id} attempt {attempt}/{self.retry_config.max_attempts} "
                            f"raised {error_category.value} error: {e}. Retrying in {delay:.2f}s..."
                        )
                        self._emit_event(EventType.NODE_ERROR, {
                            "node_id": node.node_id,
                            "error": f"Attempt {attempt} exception: {str(e)}",
                            "retrying": True,
                            "attempt": attempt,
                            "error_category": error_category.value
                        })
                        await asyncio.sleep(delay)
                    else:
                        # Not retry-able or last attempt
                        logger.error(
                            f"Node {node.node_id} attempt {attempt}/{self.retry_config.max_attempts} "
                            f"failed with {error_category.value} error (not retrying): {e}"
                        )
                        break

            # Update debug info
            execution_time = time.time() - start_time
            node.execution_count += 1
            node.last_execution_time = execution_time
            node.last_output = result

            # Add to execution history if in debug mode
            if self.debug_mode:
                self.execution_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "node_id": node.node_id,
                    "node_type": node.__class__.__name__,
                    "execution_time": execution_time,
                    "status": "success" if result and result.get("success") else "failed",
                    "result": result,
                    "retry_stats": self.retry_stats.to_dict()
                })

            # Handle result
            if result and result.get("success", False):
                node.status = NodeStatus.SUCCESS
                self.executed_nodes.add(node.node_id)

                self._emit_event(EventType.NODE_COMPLETED, {
                    "node_id": node.node_id,
                    "message": result.get("data", {}).get("message", "Completed"),
                    "progress": self.progress,
                    "execution_time": execution_time
                })

                logger.info(f"Node executed successfully: {node.node_id}")
                # Record successful execution in metrics
                get_metrics().record_node_complete(
                    node_type, node.node_id, execution_time * 1000, success=True
                )
                return True, result
            else:
                node.status = NodeStatus.ERROR
                error_msg = result.get("error", "Unknown error") if result else str(last_exception or "No result")
                self._emit_event(EventType.NODE_ERROR, {
                    "node_id": node.node_id,
                    "error": error_msg,
                    "execution_time": execution_time
                })
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

            self._emit_event(EventType.NODE_ERROR, {
                "node_id": node.node_id,
                "error": error_msg,
                "execution_time": execution_time
            })

            logger.exception(f"Exception during node execution: {node.node_id}")
            # Record exception in metrics
            get_metrics().record_node_complete(
                node_type, node.node_id, execution_time * 1000, success=False
            )
            return False, None
    
    async def _execute_workflow(self) -> None:
        """Execute the workflow from start to finish."""
        # Find the start node
        start_node = self._find_start_node()
        if not start_node:
            raise ValueError("No StartNode found in workflow")

        # Use parallel execution if enabled and not in debug/step mode
        if self.parallel_execution and not self.debug_mode and not self.step_mode:
            await self._execute_workflow_parallel(start_node)
        else:
            await self._execute_workflow_sequential(start_node)

    async def _execute_workflow_sequential(self, start_node: BaseNode) -> None:
        """Execute workflow sequentially (original behavior)."""
        # Execute nodes in order, following connections
        nodes_to_execute = [start_node]

        # Track active loops for back-edge routing
        # Each entry: {"loop_node_id": str, "loop_body_nodes": Set[str]}
        active_loops: List[Dict[str, Any]] = []

        # Track active try blocks for error handling
        # Each entry: {"try_node_id": str, "try_body_nodes": Set[str]}
        active_try_blocks: List[Dict[str, Any]] = []

        def _find_try_body_nodes(try_node_id: str) -> Set[str]:
            """Find all nodes reachable from a try node's try_body output."""
            body_nodes: Set[str] = set()
            to_explore: List[str] = []

            # Find nodes connected to try_body port
            for conn in self.workflow.connections:
                if conn.source_node == try_node_id and conn.source_port == "try_body":
                    to_explore.append(conn.target_node)

            # BFS to find all reachable nodes
            while to_explore:
                node_id = to_explore.pop(0)
                if node_id in body_nodes or node_id == try_node_id:
                    continue
                body_nodes.add(node_id)

                # Add connected nodes
                for conn in self.workflow.connections:
                    if conn.source_node == node_id:
                        if conn.target_node != try_node_id:
                            to_explore.append(conn.target_node)

            return body_nodes

        def _handle_try_error(context: ExecutionContext, error_msg: str, error_type: str) -> Optional[str]:
            """Handle error in try block - set error state and return try node id."""
            if not active_try_blocks:
                return None
            try_info = active_try_blocks.pop()
            try_node_id = try_info["try_node_id"]
            # Set error state for TryNode to read
            try_state_key = f"{try_node_id}_state"
            if try_state_key in context.variables:
                context.variables[try_state_key] = {
                    "in_try_block": False,
                    "error_occurred": True,
                    "error_message": error_msg,
                    "error_type": error_type
                }
            return try_node_id

        def _complete_try_block(context: ExecutionContext, try_node_id: str) -> None:
            """Mark try block as successfully completed."""
            try_state_key = f"{try_node_id}_state"
            if try_state_key in context.variables:
                context.variables[try_state_key] = {
                    "in_try_block": False,
                    "error_occurred": False
                }

        def _find_loop_body_nodes(loop_node_id: str) -> Set[str]:
            """Find all nodes reachable from a loop's loop_body output."""
            body_nodes: Set[str] = set()
            to_explore: List[str] = []

            # Find nodes connected to loop body port
            # ForLoopStartNode uses "body", WhileLoopStartNode uses "loop_body"
            for conn in self.workflow.connections:
                if conn.source_node == loop_node_id and conn.source_port in ("loop_body", "body"):
                    to_explore.append(conn.target_node)

            # BFS to find all reachable nodes (until we hit the loop node again or completed)
            while to_explore:
                node_id = to_explore.pop(0)
                if node_id in body_nodes or node_id == loop_node_id:
                    continue
                body_nodes.add(node_id)

                # Add connected nodes (following exec_out connections)
                for conn in self.workflow.connections:
                    if conn.source_node == node_id:
                        # Don't follow back to the same loop's completed port
                        if conn.target_node != loop_node_id:
                            to_explore.append(conn.target_node)

            return body_nodes

        def _handle_break(context: ExecutionContext) -> Optional[str]:
            """Handle break signal - clean up loop state and return loop node id."""
            if not active_loops:
                return None
            loop_info = active_loops.pop()
            loop_node_id = loop_info["loop_node_id"]
            # Clean up loop state in context
            loop_state_key = f"{loop_node_id}_loop_state"
            if loop_state_key in context.variables:
                del context.variables[loop_state_key]
            return loop_node_id

        def _handle_continue() -> Optional[str]:
            """Handle continue signal - return loop node id to re-execute."""
            if not active_loops:
                return None
            return active_loops[-1]["loop_node_id"]

        while nodes_to_execute and not self._stop_requested:
            # Wait if paused
            await self._pause_event.wait()

            current_node = nodes_to_execute.pop(0)

            # Skip if already executed (except for loops and nodes inside active loops)
            is_loop_node = current_node.__class__.__name__ in ["ForLoopStartNode", "WhileLoopStartNode"]
            is_in_active_loop = any(
                current_node.node_id in loop_info["loop_body_nodes"]
                for loop_info in active_loops
            )
            if current_node.node_id in self.executed_nodes and not is_loop_node and not is_in_active_loop:
                continue

            # Skip nodes not in subgraph (Run-To-Node filtering)
            if not self._should_execute_node(current_node.node_id):
                logger.debug(f"Skipping node {current_node.node_id} (not in subgraph)")
                continue

            # Transfer data from connected input ports
            for connection in self.workflow.connections:
                if connection.target_node == current_node.node_id:
                    self._transfer_data(connection)

            # Execute the node
            success, result = await self._execute_node(current_node)

            if not success:
                # Check if we're inside a try block
                in_try_block = False
                for try_info in active_try_blocks:
                    if current_node.node_id in try_info["try_body_nodes"]:
                        in_try_block = True
                        break

                if in_try_block:
                    # Error occurred in try block - route to catch
                    error_msg = result.get("error", "Unknown error") if result else "Unknown error"
                    error_type = type(result.get("error", Exception())).__name__ if result else "Exception"
                    logger.info(f"Error in try block at {current_node.node_id}: {error_msg}")

                    try_node_id = _handle_try_error(self.context, error_msg, error_type)
                    if try_node_id:
                        # Clear remaining try body nodes from queue
                        try_body_nodes = _find_try_body_nodes(try_node_id)
                        nodes_to_execute = [n for n in nodes_to_execute if n.node_id not in try_body_nodes]
                        # Re-add try node to process the error (will route to catch)
                        nodes_to_execute.insert(0, self.workflow.nodes[try_node_id])
                        logger.debug(f"Error caught, re-executing try node {try_node_id} for catch routing")
                    continue

                elif self.continue_on_error:
                    logger.warning(
                        f"Node {current_node.node_id} failed but continue_on_error is enabled. "
                        f"Continuing workflow..."
                    )
                    # Continue to next nodes if available
                else:
                    # Stop on error
                    logger.warning(f"Stopping workflow due to node error: {current_node.node_id}")
                    break

            # Check if target node was reached (Run-To-Node feature)
            if success and self._check_target_reached(current_node.node_id):
                # Emit event indicating target was reached (include execution_time for badge)
                self._emit_event(EventType.NODE_COMPLETED, {
                    "node_id": current_node.node_id,
                    "message": "Target node reached - execution paused",
                    "progress": self.progress,
                    "execution_time": current_node.last_execution_time,
                    "target_reached": True
                })
                # Pause execution at target
                self.pause()
                # Wait for resume or stop
                await self._pause_event.wait()
                # If stop was requested while paused, exit
                if self._stop_requested:
                    break
                # Otherwise, continue execution from here if resumed

            # Check for control flow signals (break/continue)
            control_flow = result.get("control_flow") if result else None

            if control_flow == "break":
                # Break from loop - clean up and route to completed
                logger.info(f"Break signal received from {current_node.node_id}")
                loop_node_id = _handle_break(self.context)
                if loop_node_id:
                    # Clear any loop body nodes from the queue
                    loop_body_nodes = _find_loop_body_nodes(loop_node_id)
                    nodes_to_execute = [n for n in nodes_to_execute if n.node_id not in loop_body_nodes]
                    # Route to completed output of loop node
                    for conn in self.workflow.connections:
                        if conn.source_node == loop_node_id and conn.source_port == "completed":
                            if conn.target_node in self.workflow.nodes:
                                nodes_to_execute.insert(0, self.workflow.nodes[conn.target_node])
                                logger.debug(f"Break: routing to {loop_node_id}.completed -> {conn.target_node}")
                continue

            elif control_flow == "continue":
                # Continue to next iteration - re-add loop node to queue
                logger.info(f"Continue signal received from {current_node.node_id}")
                loop_node_id = _handle_continue()
                if loop_node_id:
                    # Clear remaining loop body nodes from queue
                    loop_body_nodes = active_loops[-1].get("loop_body_nodes", set())
                    nodes_to_execute = [n for n in nodes_to_execute if n.node_id not in loop_body_nodes]
                    # Re-add the loop node to execute next iteration
                    nodes_to_execute.insert(0, self.workflow.nodes[loop_node_id])
                    logger.debug(f"Continue: re-executing loop {loop_node_id}")
                continue

            # Get next nodes based on execution result
            if result and "next_nodes" in result:
                # Handle ForLoopEnd loop_back_to instruction
                if "loop_back_to" in result:
                    loop_start_id = result["loop_back_to"]
                    if loop_start_id in self.workflow.nodes:
                        nodes_to_execute.insert(0, self.workflow.nodes[loop_start_id])
                        logger.debug(f"ForLoopEnd: looping back to {loop_start_id}")
                        continue

                # Dynamic routing - use the next_nodes from result
                next_port_names = result["next_nodes"]
                next_nodes = []

                # Check if this is a loop node entering loop_body (or "body" for ForLoopStartNode)
                if is_loop_node and ("loop_body" in next_port_names or "body" in next_port_names):
                    # Track this loop as active
                    loop_body_nodes = _find_loop_body_nodes(current_node.node_id)
                    active_loops.append({
                        "loop_node_id": current_node.node_id,
                        "loop_body_nodes": loop_body_nodes
                    })
                    logger.debug(f"Entered loop {current_node.node_id}, body nodes: {loop_body_nodes}")

                # Check if loop is completing
                if is_loop_node and "completed" in next_port_names:
                    # Remove this loop from active loops if present
                    active_loops = [l for l in active_loops if l["loop_node_id"] != current_node.node_id]
                    logger.debug(f"Loop {current_node.node_id} completed")

                # Check if this is a TryNode entering try_body
                is_try_node = current_node.__class__.__name__ == "TryNode"
                if is_try_node and "try_body" in next_port_names:
                    # Track this try block as active
                    try_body_nodes = _find_try_body_nodes(current_node.node_id)
                    active_try_blocks.append({
                        "try_node_id": current_node.node_id,
                        "try_body_nodes": try_body_nodes
                    })
                    logger.debug(f"Entered try block {current_node.node_id}, body nodes: {try_body_nodes}")

                # Check if try block is completing (success or catch)
                if is_try_node and ("success" in next_port_names or "catch" in next_port_names):
                    # Remove this try block from active if present
                    active_try_blocks = [t for t in active_try_blocks if t["try_node_id"] != current_node.node_id]
                    logger.debug(f"Try block {current_node.node_id} completed")

                for port_name in next_port_names:
                    # Find connections from current node's specific output port
                    for connection in self.workflow.connections:
                        if (connection.source_node == current_node.node_id and
                            connection.source_port == port_name):
                            target_node_id = connection.target_node
                            if target_node_id in self.workflow.nodes:
                                next_nodes.append(self.workflow.nodes[target_node_id])
                                logger.debug(f"Dynamic routing: {current_node.node_id}.{port_name} -> {target_node_id}")

                nodes_to_execute.extend(next_nodes)

                # Loop back-edge handling: If we're in a loop body and have no more nodes,
                # we need to re-execute the loop node for the next iteration
                if not nodes_to_execute and active_loops:
                    # Check if current node is part of any active loop body
                    for loop_info in reversed(active_loops):
                        if current_node.node_id in loop_info["loop_body_nodes"]:
                            # Check if there are any more loop body nodes pending
                            pending_body_nodes = loop_info["loop_body_nodes"] - self.executed_nodes
                            pending_body_nodes.discard(current_node.node_id)
                            if not pending_body_nodes:
                                # All loop body nodes executed, re-add loop node
                                loop_node = self.workflow.nodes[loop_info["loop_node_id"]]
                                nodes_to_execute.append(loop_node)
                                logger.debug(f"Loop back-edge: returning to {loop_info['loop_node_id']}")
                            break

                # Try block back-edge handling: If try body completes successfully,
                # route back to TryNode for success path
                if not nodes_to_execute and active_try_blocks:
                    # Check if current node is part of any active try body
                    for try_info in reversed(active_try_blocks):
                        if current_node.node_id in try_info["try_body_nodes"]:
                            # Check if there are any more try body nodes pending
                            pending_body_nodes = try_info["try_body_nodes"] - self.executed_nodes
                            pending_body_nodes.discard(current_node.node_id)
                            if not pending_body_nodes:
                                # All try body nodes executed successfully
                                try_node_id = try_info["try_node_id"]
                                _complete_try_block(self.context, try_node_id)
                                # Re-add try node to process success path
                                try_node = self.workflow.nodes[try_node_id]
                                nodes_to_execute.append(try_node)
                                logger.debug(f"Try body completed successfully, routing to {try_node_id} for success")
                            break
            else:
                # Fallback to all connected outputs (old behavior)
                next_nodes = self._get_next_nodes(current_node.node_id)
                nodes_to_execute.extend(next_nodes)

    async def _execute_workflow_parallel(self, start_node: BaseNode) -> None:
        """
        Execute workflow with parallel execution of independent branches.

        Uses dependency analysis to identify nodes that can run concurrently.
        Control flow nodes and browser operations still run sequentially.
        """
        logger.info("Executing workflow with parallel mode enabled")

        # Execute start node first (always sequential)
        await self._pause_event.wait()
        success, result = await self._execute_node(start_node)

        if not success and not self.continue_on_error:
            logger.warning(f"Stopping workflow due to start node error")
            return

        # Process the rest of the workflow using dependency-based scheduling
        while not self._stop_requested:
            await self._pause_event.wait()

            # Get all nodes that are ready to execute
            ready_node_ids = self._get_ready_nodes()

            # Filter out already executed nodes (except loops)
            ready_node_ids = [
                nid for nid in ready_node_ids
                if nid not in self.executed_nodes or
                self.workflow.nodes[nid].__class__.__name__ in ["ForLoopStartNode", "WhileLoopStartNode"]
            ]

            if not ready_node_ids:
                # No more nodes ready - workflow complete
                break

            # Separate parallelizable and sequential nodes
            parallel_nodes: List[BaseNode] = []
            sequential_nodes: List[BaseNode] = []

            for node_id in ready_node_ids:
                node = self.workflow.nodes[node_id]
                if self._is_parallelizable_node(node):
                    parallel_nodes.append(node)
                else:
                    sequential_nodes.append(node)

            # Execute sequential nodes first (one at a time)
            for node in sequential_nodes:
                if self._stop_requested:
                    break

                # Transfer data
                for connection in self.workflow.connections:
                    if connection.target_node == node.node_id:
                        self._transfer_data(connection)

                success, result = await self._execute_node(node)

                if not success and not self.continue_on_error:
                    logger.warning(f"Stopping workflow due to node error: {node.node_id}")
                    return

                # Handle control flow
                control_flow = result.get("control_flow") if result else None
                if control_flow in ("break", "continue"):
                    logger.info(f"{control_flow.capitalize()} signal from {node.node_id}")
                    # Let the loop node handle routing

            # Execute parallelizable nodes concurrently
            if parallel_nodes and not self._stop_requested:
                await self._execute_nodes_parallel(parallel_nodes)

    async def _execute_nodes_parallel(self, nodes: List[BaseNode]) -> None:
        """
        Execute multiple nodes in parallel.

        Args:
            nodes: List of nodes to execute concurrently
        """
        if not nodes:
            return

        logger.info(f"Executing {len(nodes)} nodes in parallel: {[n.node_id for n in nodes]}")

        # Transfer data to all nodes first
        for node in nodes:
            for connection in self.workflow.connections:
                if connection.target_node == node.node_id:
                    self._transfer_data(connection)

        # Create tasks for parallel execution
        async def execute_single(node: BaseNode) -> Tuple[NodeId, bool, Optional[Dict[str, Any]]]:
            """Execute a single node and return results."""
            success, result = await self._execute_node(node)
            return node.node_id, success, result

        # Run all nodes concurrently with semaphore limiting
        semaphore = asyncio.Semaphore(self.max_parallel_nodes)

        async def limited_execute(node: BaseNode) -> Tuple[NodeId, bool, Optional[Dict[str, Any]]]:
            async with semaphore:
                return await execute_single(node)

        # Execute all in parallel
        tasks = [limited_execute(node) for node in nodes]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Parallel node execution error: {result}")
                if not self.continue_on_error:
                    self._stop_requested = True
                    break
            else:
                node_id, success, node_result = result
                if not success and not self.continue_on_error:
                    logger.warning(f"Stopping parallel execution due to node error: {node_id}")
                    self._stop_requested = True
                    break
    
    async def run(self) -> bool:
        """
        Run the workflow asynchronously.
        
        Returns:
            True if workflow completed successfully, False otherwise
        """
        if self.state == ExecutionState.RUNNING:
            logger.warning("Workflow is already running")
            return False
        
        self.state = ExecutionState.RUNNING
        self.start_time = datetime.now()
        self._stop_requested = False
        self.executed_nodes.clear()
        
        # Create execution context with initial variables from Variables Tab
        self.context = ExecutionContext(
            workflow_name=self.workflow.metadata.name,
            initial_variables=self._initial_variables,
            project_context=self._project_context,
        )
        
        self._emit_event(EventType.WORKFLOW_STARTED, {
            "workflow_name": self.workflow.metadata.name,
            "total_nodes": self.total_nodes
        })

        # Record workflow start for performance dashboard
        get_metrics().record_workflow_start(self.workflow.metadata.name)

        logger.info(f"Starting workflow execution: {self.workflow.metadata.name}")
        
        try:
            await self._execute_workflow()
            
            # Check if completed successfully
            if self._stop_requested:
                self.state = ExecutionState.STOPPED
                self.end_time = datetime.now()
                duration = (self.end_time - self.start_time).total_seconds()
                self._emit_event(EventType.WORKFLOW_STOPPED, {
                    "executed_nodes": len(self.executed_nodes),
                    "total_nodes": self.total_nodes
                })
                logger.info("Workflow execution stopped by user")
                # Record stopped workflow as failed for metrics
                get_metrics().record_workflow_complete(
                    self.workflow.metadata.name, duration * 1000, success=False
                )
                return False
            else:
                self.state = ExecutionState.COMPLETED
                self.end_time = datetime.now()
                duration = (self.end_time - self.start_time).total_seconds()
                
                self._emit_event(EventType.WORKFLOW_COMPLETED, {
                    "executed_nodes": len(self.executed_nodes),
                    "total_nodes": self.total_nodes,
                    "duration": duration
                })
                
                logger.info(
                    f"Workflow completed successfully in {duration:.2f}s "
                    f"({len(self.executed_nodes)}/{self.total_nodes} nodes)"
                )
                # Record workflow completion for performance dashboard
                get_metrics().record_workflow_complete(
                    self.workflow.metadata.name, duration * 1000, success=True
                )
                return True

        except Exception as e:
            self.state = ExecutionState.ERROR
            self.end_time = datetime.now()
            duration = (self.end_time - self.start_time).total_seconds()

            self._emit_event(EventType.WORKFLOW_ERROR, {
                "error": str(e),
                "executed_nodes": len(self.executed_nodes)
            })

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
                    await asyncio.wait_for(
                        self.context.cleanup(),
                        timeout=30.0  # 30 second timeout for cleanup
                    )
                except asyncio.TimeoutError:
                    logger.error("Context cleanup timed out after 30 seconds")
                except Exception as cleanup_error:
                    logger.error(f"Error during context cleanup: {cleanup_error}")

            self.current_node_id = None
    
    def pause(self) -> None:
        """Pause workflow execution."""
        if self.state == ExecutionState.RUNNING:
            self.state = ExecutionState.PAUSED
            self._pause_event.clear()
            
            self._emit_event(EventType.WORKFLOW_PAUSED, {
                "executed_nodes": len(self.executed_nodes),
                "total_nodes": self.total_nodes,
                "progress": self.progress
            })
            
            logger.info("Workflow execution paused")
    
    def resume(self) -> None:
        """Resume paused workflow execution."""
        if self.state == ExecutionState.PAUSED:
            self.state = ExecutionState.RUNNING
            self._pause_event.set()
            
            self._emit_event(EventType.WORKFLOW_RESUMED, {
                "executed_nodes": len(self.executed_nodes),
                "total_nodes": self.total_nodes
            })
            
            logger.info("Workflow execution resumed")
    
    def stop(self) -> None:
        """Stop workflow execution."""
        if self.state in (ExecutionState.RUNNING, ExecutionState.PAUSED):
            self._stop_requested = True
            self._pause_event.set()  # Unblock if paused
            
            logger.info("Workflow stop requested")
    
    def reset(self) -> None:
        """Reset the runner to initial state."""
        self.state = ExecutionState.IDLE
        self.context = None
        self.current_node_id = None
        self.executed_nodes.clear()
        self.start_time = None
        self.end_time = None
        self._stop_requested = False
        self._pause_event.set()
        self._step_event.set()
        self.execution_history.clear()
        self._target_reached = False

        # Reset all node statuses
        for node in self.workflow.nodes.values():
            node.reset()

        logger.info("WorkflowRunner reset to initial state")
    
    # Debug Mode Methods
    
    def enable_debug_mode(self, enabled: bool = True) -> None:
        """
        Enable or disable debug mode.
        
        Args:
            enabled: True to enable debug mode, False to disable
        """
        self.debug_mode = enabled
        logger.info(f"Debug mode {'enabled' if enabled else 'disabled'}")
    
    def enable_step_mode(self, enabled: bool = True) -> None:
        """
        Enable or disable step execution mode.
        
        In step mode, execution pauses before each node and waits for step() call.
        
        Args:
            enabled: True to enable step mode, False to disable
        """
        self.step_mode = enabled
        if not enabled:
            self._step_event.set()  # Unblock if disabling
        logger.info(f"Step mode {'enabled' if enabled else 'disabled'}")
    
    def step(self) -> None:
        """Execute one step (one node) in debug mode."""
        if self.step_mode:
            self._step_event.set()
            logger.debug("Step command issued")
    
    def continue_execution(self) -> None:
        """Continue execution without stepping (exit step mode temporarily)."""
        self.step_mode = False
        self._step_event.set()
        logger.info("Continuing execution")
    
    def set_breakpoint(self, node_id: NodeId, enabled: bool = True) -> None:
        """
        Set or remove a breakpoint on a node.
        
        Args:
            node_id: ID of the node to set breakpoint on
            enabled: True to set breakpoint, False to remove
        """
        if enabled:
            self.breakpoints.add(node_id)
            if node_id in self.workflow.nodes:
                self.workflow.nodes[node_id].set_breakpoint(True)
            logger.info(f"Breakpoint set on node: {node_id}")
        else:
            self.breakpoints.discard(node_id)
            if node_id in self.workflow.nodes:
                self.workflow.nodes[node_id].set_breakpoint(False)
            logger.info(f"Breakpoint removed from node: {node_id}")
    
    def clear_all_breakpoints(self) -> None:
        """Clear all breakpoints."""
        for node_id in self.breakpoints:
            if node_id in self.workflow.nodes:
                self.workflow.nodes[node_id].set_breakpoint(False)
        self.breakpoints.clear()
        logger.info("All breakpoints cleared")
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """
        Get the execution history.
        
        Returns:
            List of execution records
        """
        return self.execution_history.copy()
    
    def get_variables(self) -> Dict[str, Any]:
        """
        Get all variables from the execution context.
        
        Returns:
            Dictionary of all variables
        """
        if self.context:
            return self.context.variables.copy()
        return {}
    
    def get_node_debug_info(self, node_id: NodeId) -> Optional[Dict[str, Any]]:
        """
        Get debug information for a specific node.

        Args:
            node_id: ID of the node

        Returns:
            Debug information dictionary or None if node not found
        """
        node = self.workflow.nodes.get(node_id)
        if node:
            return node.get_debug_info()
        return None

    def get_retry_stats(self) -> Dict[str, Any]:
        """
        Get retry statistics for the workflow execution.

        Returns:
            Dictionary with retry statistics
        """
        return self.retry_stats.to_dict()

    def configure_retry(
        self,
        max_attempts: Optional[int] = None,
        initial_delay: Optional[float] = None,
        max_delay: Optional[float] = None,
        backoff_multiplier: Optional[float] = None,
    ) -> None:
        """
        Configure retry behavior.

        Args:
            max_attempts: Maximum retry attempts (including initial)
            initial_delay: Initial delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
            backoff_multiplier: Multiplier for exponential backoff
        """
        if max_attempts is not None:
            self.retry_config.max_attempts = max_attempts
        if initial_delay is not None:
            self.retry_config.initial_delay = initial_delay
        if max_delay is not None:
            self.retry_config.max_delay = max_delay
        if backoff_multiplier is not None:
            self.retry_config.backoff_multiplier = backoff_multiplier

        logger.info(
            f"Retry config updated: max_attempts={self.retry_config.max_attempts}, "
            f"initial_delay={self.retry_config.initial_delay}s, "
            f"max_delay={self.retry_config.max_delay}s, "
            f"backoff={self.retry_config.backoff_multiplier}x"
        )

    def set_node_timeout(self, timeout: float) -> None:
        """
        Set the timeout for node execution.

        Args:
            timeout: Timeout in seconds
        """
        self.node_timeout = timeout
        logger.info(f"Node execution timeout set to {timeout}s")

    # Parallel Execution Methods

    def enable_parallel_execution(self, enabled: bool = True) -> None:
        """
        Enable or disable parallel execution of independent nodes.

        Args:
            enabled: True to enable parallel execution, False to disable
        """
        self.parallel_execution = enabled
        if enabled and not self._dependency_graph:
            self._build_dependency_graph()
        logger.info(f"Parallel execution {'enabled' if enabled else 'disabled'}")

    def set_max_parallel_nodes(self, max_nodes: int) -> None:
        """
        Set the maximum number of nodes to execute in parallel.

        Args:
            max_nodes: Maximum concurrent node executions (1-16)
        """
        self.max_parallel_nodes = max(1, min(16, max_nodes))
        if self._parallel_executor:
            self._parallel_executor._max_concurrency = self.max_parallel_nodes
        logger.info(f"Max parallel nodes set to {self.max_parallel_nodes}")

    def get_parallel_stats(self) -> Dict[str, Any]:
        """
        Get statistics about parallel execution.

        Returns:
            Dictionary with parallel execution stats
        """
        return {
            "enabled": self.parallel_execution,
            "max_parallel_nodes": self.max_parallel_nodes,
            "has_dependency_graph": self._dependency_graph is not None,
        }
