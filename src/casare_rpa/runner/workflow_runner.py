"""
CasareRPA - Workflow Runner (LEGACY COMPATIBILITY WRAPPER)

IMPORTANT: This class is DEPRECATED and maintained only for backward compatibility.

New code should use ExecuteWorkflowUseCase directly from application.use_cases.

This wrapper maintains the existing API while delegating to the new clean architecture.
"""

import asyncio
import warnings
from typing import Any, Dict, List, Optional, Set
from datetime import datetime
from loguru import logger

from ..core.base_node import BaseNode
from ..core.workflow_schema import WorkflowSchema, NodeConnection
from ..core.execution_context import ExecutionContext
from ..core.types import NodeId, NodeStatus, EventType
from ..core.events import EventBus, Event
from ..application.use_cases.execute_workflow import (
    ExecuteWorkflowUseCase,
    ExecutionSettings,
)
from ..utils.resilience.retry import RetryConfig, RetryStats
from ..utils.performance.parallel_executor import DependencyGraph, ParallelExecutor
from ..utils.performance.performance_metrics import get_metrics

# Default timeout for node execution (in seconds)
DEFAULT_NODE_EXECUTION_TIMEOUT = 120  # 2 minutes


class ExecutionState:
    """Tracks the state of workflow execution (for backward compatibility)."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    COMPLETED = "completed"
    ERROR = "error"


class WorkflowRunner:
    """
    LEGACY: Workflow runner compatibility wrapper.

    This class is DEPRECATED. New code should use ExecuteWorkflowUseCase directly.

    Maintains backward compatibility by wrapping the new clean architecture
    implementation while preserving the original API.
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

        DEPRECATED: Use ExecuteWorkflowUseCase instead.

        Args:
            workflow: The workflow schema to execute
            event_bus: Optional event bus for progress updates
            retry_config: Configuration for automatic retry (not implemented in new architecture)
            node_timeout: Timeout for individual node execution in seconds
            continue_on_error: If True, continue workflow on node errors
            parallel_execution: If True, execute independent nodes in parallel (not implemented)
            max_parallel_nodes: Maximum number of nodes to run in parallel (not implemented)
            target_node_id: Optional target node for "Run To Node" feature
            initial_variables: Optional dict of variables to initialize
            project_context: Optional project context for project-scoped variables
        """
        # Emit deprecation warning
        warnings.warn(
            "WorkflowRunner is deprecated. Use ExecuteWorkflowUseCase instead. "
            "This compatibility wrapper will be removed in a future version.",
            DeprecationWarning,
            stacklevel=2,
        )

        # Store parameters for compatibility
        self.workflow = workflow
        self._initial_variables = initial_variables or {}
        self._project_context = project_context

        # Import get_event_bus to get the global instance
        from ..core.events import get_event_bus

        self.event_bus = event_bus or get_event_bus()

        # Retry and timeout configuration (for compatibility)
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

        # Parallel execution settings (not implemented in new architecture yet)
        self.parallel_execution = parallel_execution
        self.max_parallel_nodes = max_parallel_nodes
        self._dependency_graph: Optional[DependencyGraph] = None
        self._parallel_executor: Optional[ParallelExecutor] = None

        if parallel_execution:
            logger.warning(
                "Parallel execution is not yet implemented in the new architecture. "
                "Falling back to sequential execution."
            )

        # Execution state (for compatibility)
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

        # Debug mode (not fully implemented in new architecture)
        self.debug_mode: bool = False
        self.step_mode: bool = False
        self._step_event = asyncio.Event()
        self._step_event.set()
        self.breakpoints: Set[NodeId] = set()
        self.execution_history: List[Dict[str, Any]] = []

        # Create execution settings for use case
        self._execution_settings = ExecutionSettings(
            continue_on_error=continue_on_error,
            node_timeout=node_timeout,
            target_node_id=target_node_id,
        )

        # Create the use case (will be recreated on each run)
        self._use_case: Optional[ExecuteWorkflowUseCase] = None

    @property
    def progress(self) -> float:
        """Get execution progress as percentage (0-100)."""
        if self._use_case:
            return self._use_case._calculate_progress()
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

    @property
    def target_reached(self) -> bool:
        """Check if the target node has been reached."""
        if self._use_case:
            return self._use_case._target_reached
        return False

    @property
    def has_target(self) -> bool:
        """Check if a target node is set for Run-To-Node mode."""
        return self._execution_settings.target_node_id is not None

    @property
    def subgraph_valid(self) -> bool:
        """Check if the subgraph was successfully calculated."""
        if self._use_case:
            return (
                self._use_case._subgraph_nodes is not None
                or self._execution_settings.target_node_id is None
            )
        return True

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

        # Create the use case for this execution
        self._use_case = ExecuteWorkflowUseCase(
            workflow=self.workflow,
            event_bus=self.event_bus,
            settings=self._execution_settings,
            initial_variables=self._initial_variables,
            project_context=self._project_context,
        )

        # Store reference to context for compatibility
        self.context = self._use_case.context

        logger.info(f"Starting workflow execution: {self.workflow.metadata.name}")

        try:
            # Execute the workflow
            success = await self._use_case.execute()

            # Update state based on result
            if success:
                self.state = ExecutionState.COMPLETED
            else:
                if self._stop_requested:
                    self.state = ExecutionState.STOPPED
                else:
                    self.state = ExecutionState.ERROR

            # Update tracking
            self.executed_nodes = self._use_case.executed_nodes
            self.end_time = datetime.now()

            return success

        except Exception as e:
            self.state = ExecutionState.ERROR
            self.end_time = datetime.now()
            logger.exception("Workflow execution failed with exception")
            return False

        finally:
            self.current_node_id = None

    def pause(self) -> None:
        """
        Pause workflow execution.

        NOTE: Pause/resume is not fully implemented in the new architecture.
        This method is kept for compatibility but may not work as expected.
        """
        if self.state == ExecutionState.RUNNING:
            self.state = ExecutionState.PAUSED
            self._pause_event.clear()

            self._emit_event(
                EventType.WORKFLOW_PAUSED,
                {
                    "executed_nodes": len(self.executed_nodes),
                    "total_nodes": self.total_nodes,
                    "progress": self.progress,
                },
            )

            logger.warning(
                "Pause requested but not fully implemented in new architecture"
            )

    def resume(self) -> None:
        """
        Resume paused workflow execution.

        NOTE: Pause/resume is not fully implemented in the new architecture.
        """
        if self.state == ExecutionState.PAUSED:
            self.state = ExecutionState.RUNNING
            self._pause_event.set()

            self._emit_event(
                EventType.WORKFLOW_RESUMED,
                {
                    "executed_nodes": len(self.executed_nodes),
                    "total_nodes": self.total_nodes,
                },
            )

            logger.warning(
                "Resume requested but not fully implemented in new architecture"
            )

    def stop(self) -> None:
        """Stop workflow execution."""
        if self.state in (ExecutionState.RUNNING, ExecutionState.PAUSED):
            self._stop_requested = True
            self._pause_event.set()  # Unblock if paused

            if self._use_case:
                self._use_case.stop()

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
        self._use_case = None

        # Reset all node statuses
        for node in self.workflow.nodes.values():
            node.reset()

        logger.info("WorkflowRunner reset to initial state")

    def _emit_event(self, event_type: EventType, data: Dict[str, Any]) -> None:
        """Emit an event to the event bus."""
        if self.event_bus:
            event = Event(
                event_type=event_type, data=data, node_id=self.current_node_id
            )
            self.event_bus.publish(event)

    # ========================================================================
    # Debug Mode Methods (Limited compatibility)
    # ========================================================================

    def enable_debug_mode(self, enabled: bool = True) -> None:
        """
        Enable or disable debug mode.

        NOTE: Debug mode is not fully implemented in the new architecture.
        """
        self.debug_mode = enabled
        logger.warning(
            f"Debug mode {'enabled' if enabled else 'disabled'} "
            "(limited functionality in new architecture)"
        )

    def enable_step_mode(self, enabled: bool = True) -> None:
        """
        Enable or disable step execution mode.

        NOTE: Step mode is not implemented in the new architecture.
        """
        self.step_mode = enabled
        if not enabled:
            self._step_event.set()
        logger.warning(
            f"Step mode {'enabled' if enabled else 'disabled'} "
            "(not implemented in new architecture)"
        )

    def step(self) -> None:
        """
        Execute one step (one node) in debug mode.

        NOTE: Not implemented in new architecture.
        """
        if self.step_mode:
            self._step_event.set()
            logger.warning("Step command not implemented in new architecture")

    def continue_execution(self) -> None:
        """
        Continue execution without stepping.

        NOTE: Not implemented in new architecture.
        """
        self.step_mode = False
        self._step_event.set()
        logger.warning("Continue execution not implemented in new architecture")

    def set_breakpoint(self, node_id: NodeId, enabled: bool = True) -> None:
        """
        Set or remove a breakpoint on a node.

        NOTE: Breakpoints are not implemented in the new architecture.
        """
        if enabled:
            self.breakpoints.add(node_id)
            if node_id in self.workflow.nodes:
                self.workflow.nodes[node_id].set_breakpoint(True)
            logger.warning(
                f"Breakpoint set on {node_id} (not implemented in new architecture)"
            )
        else:
            self.breakpoints.discard(node_id)
            if node_id in self.workflow.nodes:
                self.workflow.nodes[node_id].set_breakpoint(False)
            logger.warning(
                f"Breakpoint removed from {node_id}"
            )

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

        NOTE: Limited in new architecture.
        """
        return self.execution_history.copy()

    def get_variables(self) -> Dict[str, Any]:
        """Get all variables from the execution context."""
        if self._use_case and self._use_case.context:
            return self._use_case.context._state.variables.copy()
        if self.context:
            return self.context._state.variables.copy()
        return {}

    def get_node_debug_info(self, node_id: NodeId) -> Optional[Dict[str, Any]]:
        """Get debug information for a specific node."""
        node = self.workflow.nodes.get(node_id)
        if node:
            return node.get_debug_info()
        return None

    def get_retry_stats(self) -> Dict[str, Any]:
        """Get retry statistics (for compatibility)."""
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

        NOTE: Retry logic is not implemented in the new architecture.
        """
        if max_attempts is not None:
            self.retry_config.max_attempts = max_attempts
        if initial_delay is not None:
            self.retry_config.initial_delay = initial_delay
        if max_delay is not None:
            self.retry_config.max_delay = max_delay
        if backoff_multiplier is not None:
            self.retry_config.backoff_multiplier = backoff_multiplier

        logger.warning(
            f"Retry config updated but not implemented in new architecture: "
            f"max_attempts={self.retry_config.max_attempts}, "
            f"initial_delay={self.retry_config.initial_delay}s"
        )

    def set_node_timeout(self, timeout: float) -> None:
        """Set the timeout for node execution."""
        self.node_timeout = timeout
        self._execution_settings.node_timeout = timeout
        logger.info(f"Node execution timeout set to {timeout}s")

    # ========================================================================
    # Parallel Execution Methods (Not implemented in new architecture)
    # ========================================================================

    def enable_parallel_execution(self, enabled: bool = True) -> None:
        """
        Enable or disable parallel execution.

        NOTE: Not implemented in new architecture.
        """
        self.parallel_execution = enabled
        logger.warning(
            f"Parallel execution {'enabled' if enabled else 'disabled'} "
            "(not implemented in new architecture)"
        )

    def set_max_parallel_nodes(self, max_nodes: int) -> None:
        """
        Set the maximum number of nodes to execute in parallel.

        NOTE: Not implemented in new architecture.
        """
        self.max_parallel_nodes = max(1, min(16, max_nodes))
        logger.warning(
            f"Max parallel nodes set to {self.max_parallel_nodes} "
            "(not implemented in new architecture)"
        )

    def get_parallel_stats(self) -> Dict[str, Any]:
        """Get statistics about parallel execution."""
        return {
            "enabled": self.parallel_execution,
            "max_parallel_nodes": self.max_parallel_nodes,
            "has_dependency_graph": False,  # Not implemented
        }
