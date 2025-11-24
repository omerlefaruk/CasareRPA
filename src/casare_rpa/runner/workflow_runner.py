"""
CasareRPA - Workflow Runner
Executes workflows by running nodes in the correct order based on connections.
"""

import asyncio
from typing import Any, Dict, List, Optional, Set
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
    ) -> None:
        """
        Initialize workflow runner.

        Args:
            workflow: The workflow schema to execute
            event_bus: Optional event bus for progress updates
            retry_config: Configuration for automatic retry on transient errors
            node_timeout: Timeout for individual node execution in seconds
            continue_on_error: If True, continue workflow on node errors
        """
        self.workflow = workflow

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

        logger.info(f"WorkflowRunner initialized for workflow: {workflow.metadata.name}")
    
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
            logger.debug(
                f"Data transferred: {connection.source_node}.{connection.source_port} "
                f"-> {connection.target_node}.{connection.target_port} = {value}"
            )
    
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
                    "progress": self.progress
                })

                logger.info(f"Node executed successfully: {node.node_id}")
                return True, result
            else:
                node.status = NodeStatus.ERROR
                error_msg = result.get("error", "Unknown error") if result else str(last_exception or "No result")
                self._emit_event(EventType.NODE_ERROR, {
                    "node_id": node.node_id,
                    "error": error_msg
                })
                logger.error(f"Node execution failed: {node.node_id} - {error_msg}")
                return False, result

        except Exception as e:
            node.status = NodeStatus.ERROR
            error_msg = str(e)

            self._emit_event(EventType.NODE_ERROR, {
                "node_id": node.node_id,
                "error": error_msg
            })

            logger.exception(f"Exception during node execution: {node.node_id}")
            return False, None
    
    async def _execute_workflow(self) -> None:
        """Execute the workflow from start to finish."""
        # Find the start node
        start_node = self._find_start_node()
        if not start_node:
            raise ValueError("No StartNode found in workflow")
        
        # Execute nodes in order, following connections
        nodes_to_execute = [start_node]
        
        while nodes_to_execute and not self._stop_requested:
            # Wait if paused
            await self._pause_event.wait()
            
            current_node = nodes_to_execute.pop(0)
            
            # Skip if already executed (except for loops which need re-execution)
            is_loop_node = current_node.__class__.__name__ in ["ForLoopNode", "WhileLoopNode"]
            if current_node.node_id in self.executed_nodes and not is_loop_node:
                continue
            
            # Transfer data from connected input ports
            for connection in self.workflow.connections:
                if connection.target_node == current_node.node_id:
                    self._transfer_data(connection)
            
            # Execute the node
            success, result = await self._execute_node(current_node)

            if not success:
                if self.continue_on_error:
                    logger.warning(
                        f"Node {current_node.node_id} failed but continue_on_error is enabled. "
                        f"Continuing workflow..."
                    )
                    # Continue to next nodes if available
                else:
                    # Stop on error
                    logger.warning(f"Stopping workflow due to node error: {current_node.node_id}")
                    break
            
            # Check for control flow signals (break/continue)
            control_flow = result.get("control_flow") if result else None
            
            if control_flow == "break":
                # Break from loop - find the loop node and skip to its 'completed' output
                logger.info(f"Break signal received from {current_node.node_id}")
                # Clear any remaining loop body nodes from queue
                # The loop node itself should handle the break by routing to 'completed'
                continue
            elif control_flow == "continue":
                # Continue to next iteration - skip remaining loop body
                logger.info(f"Continue signal received from {current_node.node_id}")
                # The loop node will be re-executed to advance to next iteration
                continue
            
            # Get next nodes based on execution result
            if result and "next_nodes" in result:
                # Dynamic routing - use the next_nodes from result
                next_port_names = result["next_nodes"]
                next_nodes = []
                
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
            else:
                # Fallback to all connected outputs (old behavior)
                next_nodes = self._get_next_nodes(current_node.node_id)
                nodes_to_execute.extend(next_nodes)
    
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
        
        # Create execution context
        self.context = ExecutionContext(
            workflow_name=self.workflow.metadata.name
        )
        
        self._emit_event(EventType.WORKFLOW_STARTED, {
            "workflow_name": self.workflow.metadata.name,
            "total_nodes": self.total_nodes
        })
        
        logger.info(f"Starting workflow execution: {self.workflow.metadata.name}")
        
        try:
            await self._execute_workflow()
            
            # Check if completed successfully
            if self._stop_requested:
                self.state = ExecutionState.STOPPED
                self._emit_event(EventType.WORKFLOW_STOPPED, {
                    "executed_nodes": len(self.executed_nodes),
                    "total_nodes": self.total_nodes
                })
                logger.info("Workflow execution stopped by user")
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
                return True
                
        except Exception as e:
            self.state = ExecutionState.ERROR
            self.end_time = datetime.now()
            
            self._emit_event(EventType.WORKFLOW_ERROR, {
                "error": str(e),
                "executed_nodes": len(self.executed_nodes)
            })
            
            logger.exception("Workflow execution failed with exception")
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
