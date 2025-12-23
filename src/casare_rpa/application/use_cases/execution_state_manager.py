"""
CasareRPA - Execution State Manager

Manages execution state including:
- Execution settings (timeout, continue_on_error, target node)
- Progress tracking (executed nodes, current node)
- Subgraph calculation for Run-To-Node feature
- Pause/resume coordination

Extracted from ExecuteWorkflowUseCase for Single Responsibility.
"""

import asyncio
from datetime import datetime
from typing import Any

from loguru import logger

from casare_rpa.domain.entities.workflow import WorkflowSchema
from casare_rpa.domain.events import (
    DomainEvent,
    EventBus,
    WorkflowPaused,
    WorkflowResumed,
)
from casare_rpa.domain.services.execution_orchestrator import ExecutionOrchestrator
from casare_rpa.domain.value_objects.types import NodeId


class ExecutionSettings:
    """Execution settings value object."""

    def __init__(
        self,
        continue_on_error: bool = False,
        node_timeout: float = 120.0,
        target_node_id: NodeId | None = None,
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


class ExecutionStateManager:
    """
    Manages execution state and progress tracking.

    Responsibilities:
    - Track executed nodes and current node
    - Calculate subgraph for Run-To-Node feature
    - Manage pause/resume state
    - Emit progress events
    - Track execution timing
    """

    def __init__(
        self,
        workflow: WorkflowSchema,
        orchestrator: ExecutionOrchestrator,
        event_bus: EventBus | None = None,
        settings: ExecutionSettings | None = None,
        pause_event: asyncio.Event | None = None,
    ) -> None:
        """
        Initialize execution state manager.

        Args:
            workflow: Workflow schema being executed
            orchestrator: Domain orchestrator for routing decisions
            event_bus: Optional event bus for progress updates
            settings: Execution settings
            pause_event: Optional event for pause/resume coordination
        """
        self.workflow = workflow
        self.orchestrator = orchestrator
        self.event_bus = event_bus
        self.settings = settings or ExecutionSettings()

        # Pause/resume support
        self.pause_event = pause_event or asyncio.Event()
        self.pause_event.set()  # Initially not paused

        # Execution tracking
        self.executed_nodes: set[NodeId] = set()
        self.current_node_id: NodeId | None = None
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None
        self._stop_requested = False

        # Run-To-Node support
        self._target_reached = False
        self._subgraph_nodes: set[NodeId] | None = None

        # Execution error tracking
        self._execution_failed = False
        self._execution_error: str | None = None

        # Calculate subgraph if target node is specified
        if self.settings.target_node_id:
            if self.settings.single_node:
                # F5 mode: only execute the target node
                self._subgraph_nodes = {self.settings.target_node_id}
                logger.info(f"Single node mode: executing only {self.settings.target_node_id}")
            else:
                # F4 mode: execute up to target node
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
        if not self.orchestrator.is_reachable(start_node_id, self.settings.target_node_id):
            logger.error(
                f"Target node {self.settings.target_node_id} is not reachable from StartNode"
            )
            return

        # Calculate the subgraph
        self._subgraph_nodes = self.orchestrator.calculate_execution_path(
            start_node_id, self.settings.target_node_id
        )

        logger.info(f"Subgraph calculated: {len(self._subgraph_nodes)} nodes to execute")

    def should_execute_node(self, node_id: NodeId) -> bool:
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

    def start_execution(self) -> None:
        """Mark execution as started."""
        self.start_time = datetime.now()
        self._stop_requested = False
        self.executed_nodes.clear()
        self._execution_failed = False
        self._execution_error = None
        self._target_reached = False

    def mark_node_executed(self, node_id: NodeId) -> None:
        """Mark a node as executed."""
        self.executed_nodes.add(node_id)

    def set_current_node(self, node_id: NodeId | None) -> None:
        """Set the currently executing node."""
        self.current_node_id = node_id

    def mark_target_reached(self, node_id: NodeId) -> bool:
        """
        Check and mark if target node was reached.

        Args:
            node_id: Node ID that just completed

        Returns:
            True if this was the target node
        """
        if self.settings.target_node_id == node_id:
            self._target_reached = True
            logger.info(f"Target node {node_id} reached - execution complete")
            return True
        return False

    def mark_failed(self, error: str) -> None:
        """Mark execution as failed with error."""
        self._execution_failed = True
        self._execution_error = error

    def mark_completed(self) -> None:
        """Mark execution as completed."""
        self.end_time = datetime.now()

    def stop(self) -> None:
        """Request execution stop."""
        self._stop_requested = True
        logger.info("Workflow stop requested")

    @property
    def is_stopped(self) -> bool:
        """Check if stop was requested."""
        return self._stop_requested

    @property
    def is_failed(self) -> bool:
        """Check if execution failed."""
        return self._execution_failed

    @property
    def execution_error(self) -> str | None:
        """Get execution error message."""
        return self._execution_error

    @property
    def target_reached(self) -> bool:
        """Check if target node was reached."""
        return self._target_reached

    @property
    def total_nodes(self) -> int:
        """Get total nodes to execute."""
        if self._subgraph_nodes:
            return len(self._subgraph_nodes)
        return len(self.workflow.nodes)

    @property
    def duration(self) -> float:
        """Get execution duration in seconds."""
        if not self.start_time:
            return 0.0
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()

    def calculate_progress(self) -> float:
        """
        Calculate execution progress as percentage.

        Returns:
            Progress percentage (0-100)
        """
        total = self.total_nodes
        if total == 0:
            return 0.0
        return (len(self.executed_nodes) / total) * 100

    def publish_event(self, event: DomainEvent) -> None:
        """
        Publish a typed domain event to the event bus.

        Args:
            event: Typed DomainEvent to publish
        """
        if self.event_bus:
            self.event_bus.publish(event)

    async def pause_checkpoint(self) -> None:
        """
        Pause checkpoint - wait if pause_event is cleared.

        This method should be called between nodes and optionally
        during long-running node operations to support pause/resume.
        """
        if not self.pause_event.is_set():
            logger.info("Workflow paused at checkpoint")
            self.publish_event(
                WorkflowPaused(
                    workflow_id=self.workflow.metadata.id,
                    paused_at_node_id=self.current_node_id or "",
                    reason="checkpoint",
                )
            )
            await self.pause_event.wait()  # Block until resumed
            logger.info("Workflow resumed from pause")
            self.publish_event(
                WorkflowResumed(
                    workflow_id=self.workflow.metadata.id,
                    resume_from_node_id=self.current_node_id or "",
                )
            )

    def get_execution_summary(self) -> dict[str, Any]:
        """
        Get execution summary.

        Returns:
            Dictionary with execution statistics
        """
        return {
            "workflow_name": self.workflow.metadata.name,
            "executed_nodes": len(self.executed_nodes),
            "total_nodes": self.total_nodes,
            "duration": self.duration,
            "progress": self.calculate_progress(),
            "failed": self._execution_failed,
            "error": self._execution_error,
            "stopped": self._stop_requested,
            "target_reached": self._target_reached,
        }
