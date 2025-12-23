"""
Checkpoint System for Robot Agent.

Provides per-node checkpointing for crash recovery:
- Save execution state after each node completes
- Resume execution from last checkpoint after crash
- Track variables, executed nodes, and browser state
"""

import asyncio
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

import orjson
from loguru import logger

from casare_rpa.robot.offline_queue import OfflineQueue


@dataclass
class CheckpointState:
    """State captured at a checkpoint."""

    checkpoint_id: str
    job_id: str
    workflow_name: str
    created_at: str

    # Execution progress
    current_node_id: str
    executed_nodes: list[str]
    execution_path: list[str]

    # Variable state (serializable values only)
    variables: dict[str, Any]

    # Error tracking
    errors: list[dict[str, str]]

    # Browser state hints (can't fully restore, but helps)
    has_browser: bool = False
    active_page_name: str | None = None
    page_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CheckpointState":
        """Create from dictionary."""
        return cls(**data)


class CheckpointManager:
    """
    Manages per-node checkpointing for job execution.

    Saves execution state after each node completes, allowing
    recovery from crashes or interruptions.
    """

    def __init__(
        self,
        offline_queue: OfflineQueue,
        auto_save: bool = True,
    ):
        """
        Initialize checkpoint manager.

        Args:
            offline_queue: OfflineQueue instance for persistence
            auto_save: Whether to auto-save after each node
        """
        self.offline_queue = offline_queue
        self.auto_save = auto_save

        # Current state
        self._current_job_id: str | None = None
        self._current_workflow_name: str | None = None
        self._executed_nodes: set[str] = set()
        self._execution_path: list[str] = []
        self._variables: dict[str, Any] = {}
        self._errors: list[dict[str, str]] = []
        self._browser_state: dict[str, Any] = {}

        logger.info("Checkpoint manager initialized")

    def start_job(self, job_id: str, workflow_name: str):
        """
        Start tracking a new job.

        Args:
            job_id: Job identifier
            workflow_name: Name of the workflow
        """
        self._current_job_id = job_id
        self._current_workflow_name = workflow_name
        self._executed_nodes.clear()
        self._execution_path.clear()
        self._variables.clear()
        self._errors.clear()
        self._browser_state.clear()

        logger.debug(f"Checkpoint tracking started for job {job_id}")

    def end_job(self):
        """End tracking for current job."""
        self._current_job_id = None
        self._current_workflow_name = None

    async def save_checkpoint(
        self,
        node_id: str,
        context: Any,  # ExecutionContext
    ) -> str | None:
        """
        Save checkpoint after node execution.

        Args:
            node_id: ID of the node that just completed
            context: ExecutionContext with current state

        Returns:
            Checkpoint ID if saved successfully
        """
        if not self._current_job_id:
            return None

        # Update tracking
        self._executed_nodes.add(node_id)
        self._execution_path.append(node_id)

        # Capture serializable variables
        serializable_vars = self._extract_serializable_variables(context)

        # Capture browser state hints
        browser_state = self._capture_browser_state(context)

        # Create checkpoint
        checkpoint_id = str(uuid.uuid4())[:8]
        state = CheckpointState(
            checkpoint_id=checkpoint_id,
            job_id=self._current_job_id,
            workflow_name=self._current_workflow_name or "unknown",
            created_at=datetime.now(UTC).isoformat(),
            current_node_id=node_id,
            executed_nodes=list(self._executed_nodes),
            execution_path=self._execution_path.copy(),
            variables=serializable_vars,
            errors=self._errors.copy(),
            has_browser=browser_state.get("has_browser", False),
            active_page_name=browser_state.get("active_page_name"),
            page_count=browser_state.get("page_count", 0),
        )

        # Save to offline queue
        success = await self.offline_queue.save_checkpoint(
            job_id=self._current_job_id,
            checkpoint_id=checkpoint_id,
            node_id=node_id,
            state=state.to_dict(),
        )

        if success:
            logger.debug(f"Checkpoint {checkpoint_id} saved at node {node_id}")
            return checkpoint_id
        else:
            logger.warning(f"Failed to save checkpoint at node {node_id}")
            return None

    def _extract_serializable_variables(
        self,
        context: Any,
    ) -> dict[str, Any]:
        """Extract only JSON-serializable variables from context."""
        result = {}

        if not hasattr(context, "variables"):
            return result

        # PERFORMANCE: Fast-path for common serializable types (avoid test serialization)
        _SAFE_TYPES = (str, int, float, bool, type(None))

        for key, value in context.variables.items():
            # Fast path: primitives are always serializable
            if isinstance(value, _SAFE_TYPES):
                result[key] = value
            elif isinstance(value, (list, dict)):
                # Lists and dicts need full check (may contain non-serializable items)
                try:
                    orjson.dumps(value)
                    result[key] = value
                except (TypeError, ValueError):
                    logger.debug(f"Skipping non-serializable variable: {key}")
                    result[key] = f"<non-serializable: {type(value).__name__}>"
            else:
                # Other types: test serializability
                try:
                    orjson.dumps(value)
                    result[key] = value
                except (TypeError, ValueError):
                    logger.debug(f"Skipping non-serializable variable: {key}")
                    result[key] = f"<non-serializable: {type(value).__name__}>"

        return result

    def _capture_browser_state(self, context: Any) -> dict[str, Any]:
        """Capture browser state hints from context."""
        state = {
            "has_browser": False,
            "active_page_name": None,
            "page_count": 0,
        }

        if hasattr(context, "browser") and context.browser:
            state["has_browser"] = True

        if hasattr(context, "active_page") and context.active_page:
            state["active_page_name"] = getattr(context, "_active_page_name", None)

        if hasattr(context, "pages"):
            state["page_count"] = len(context.pages)

        return state

    async def get_checkpoint(
        self,
        job_id: str,
    ) -> CheckpointState | None:
        """
        Get the latest checkpoint for a job.

        Args:
            job_id: Job identifier

        Returns:
            CheckpointState if found
        """
        checkpoint_data = await self.offline_queue.get_latest_checkpoint(job_id)
        if checkpoint_data and "state" in checkpoint_data:
            try:
                return CheckpointState.from_dict(checkpoint_data["state"])
            except Exception as e:
                logger.error(f"Failed to parse checkpoint: {e}")
        return None

    async def restore_from_checkpoint(
        self,
        checkpoint: CheckpointState,
        context: Any,  # ExecutionContext
    ) -> bool:
        """
        Restore execution state from checkpoint.

        Args:
            checkpoint: CheckpointState to restore from
            context: ExecutionContext to restore into

        Returns:
            True if restored successfully
        """
        try:
            # Restore variables
            for key, value in checkpoint.variables.items():
                if not value.startswith("<non-serializable"):
                    context.variables[key] = value

            # Restore tracking state
            self._current_job_id = checkpoint.job_id
            self._current_workflow_name = checkpoint.workflow_name
            self._executed_nodes = set(checkpoint.executed_nodes)
            self._execution_path = checkpoint.execution_path.copy()
            self._errors = checkpoint.errors.copy()

            logger.info(
                f"Restored checkpoint {checkpoint.checkpoint_id} "
                f"at node {checkpoint.current_node_id} "
                f"({len(checkpoint.executed_nodes)} nodes completed)"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to restore checkpoint: {e}")
            return False

    def record_error(self, node_id: str, error_message: str):
        """Record an error for the current job."""
        self._errors.append(
            {
                "node_id": node_id,
                "error": error_message,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )

    def get_executed_nodes(self) -> set[str]:
        """Get set of executed node IDs."""
        return self._executed_nodes.copy()

    def is_node_executed(self, node_id: str) -> bool:
        """Check if a node has been executed."""
        return node_id in self._executed_nodes

    async def clear_checkpoints(self, job_id: str):
        """Clear all checkpoints for a job."""
        await self.offline_queue.clear_checkpoints(job_id)
        logger.debug(f"Cleared checkpoints for job {job_id}")

    def update_variable(self, key: str, value: Any):
        """Update a tracked variable."""
        self._variables[key] = value


class ResumableRunner:
    """
    Helper for running workflows with checkpoint support.

    Wraps WorkflowRunner to add checkpoint save/restore.
    """

    def __init__(
        self,
        checkpoint_manager: CheckpointManager,
        runner: Any,  # WorkflowRunner
    ):
        """
        Initialize resumable runner.

        Args:
            checkpoint_manager: CheckpointManager instance
            runner: WorkflowRunner instance
        """
        self.checkpoint_manager = checkpoint_manager
        self.runner = runner
        self._checkpoint_callback = None

    async def run(
        self,
        job_id: str,
        resume_from_checkpoint: bool = True,
    ) -> bool:
        """
        Run workflow with checkpoint support.

        Args:
            job_id: Job identifier
            resume_from_checkpoint: Whether to resume from existing checkpoint

        Returns:
            True if workflow completed successfully
        """
        workflow_name = (
            self.runner.workflow.metadata.name if self.runner.workflow.metadata else "unknown"
        )

        # Check for existing checkpoint
        checkpoint = None
        if resume_from_checkpoint:
            checkpoint = await self.checkpoint_manager.get_checkpoint(job_id)

        # Start tracking
        self.checkpoint_manager.start_job(job_id, workflow_name)

        try:
            if checkpoint:
                # Resume from checkpoint
                logger.info(
                    f"Resuming job {job_id} from checkpoint "
                    f"{checkpoint.checkpoint_id} at node {checkpoint.current_node_id}"
                )

                # Restore state
                await self.checkpoint_manager.restore_from_checkpoint(
                    checkpoint,
                    self.runner.context if hasattr(self.runner, "context") else None,
                )

                # Skip already executed nodes
                executed = self.checkpoint_manager.get_executed_nodes()
                self.runner.set_skip_nodes(executed) if hasattr(
                    self.runner, "set_skip_nodes"
                ) else None

            # Setup checkpoint callback
            self._setup_checkpoint_hook()

            # Run workflow
            success = await self.runner.run()

            # Clear checkpoints on success
            if success:
                await self.checkpoint_manager.clear_checkpoints(job_id)

            return success

        finally:
            self.checkpoint_manager.end_job()

    def _setup_checkpoint_hook(self):
        """Setup hook to save checkpoints after each node."""
        if not self.checkpoint_manager.auto_save:
            return

        # Subscribe to node completion events
        if hasattr(self.runner, "event_bus") and self.runner.event_bus:
            from casare_rpa.domain.events import NodeCompleted

            async def on_node_complete(event: NodeCompleted):
                if event.node_id and hasattr(self.runner, "context"):
                    await self.checkpoint_manager.save_checkpoint(
                        event.node_id,
                        self.runner.context,
                    )

            self.runner.event_bus.subscribe(
                NodeCompleted,
                lambda e: asyncio.create_task(on_node_complete(e)),
            )


def create_checkpoint_state(
    job_id: str,
    workflow_name: str,
    node_id: str,
    executed_nodes: list[str],
    variables: dict[str, Any],
) -> CheckpointState:
    """
    Factory function to create a checkpoint state.

    Args:
        job_id: Job identifier
        workflow_name: Name of the workflow
        node_id: Current node ID
        executed_nodes: List of executed node IDs
        variables: Current variables

    Returns:
        CheckpointState instance
    """
    return CheckpointState(
        checkpoint_id=str(uuid.uuid4())[:8],
        job_id=job_id,
        workflow_name=workflow_name,
        created_at=datetime.now(UTC).isoformat(),
        current_node_id=node_id,
        executed_nodes=executed_nodes,
        execution_path=executed_nodes.copy(),
        variables=variables,
        errors=[],
    )
