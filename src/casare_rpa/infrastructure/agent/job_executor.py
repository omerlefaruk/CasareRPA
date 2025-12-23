"""
Job Executor for Robot Agent.

Executes workflow jobs by loading workflow definitions and running them
through the ExecuteWorkflowUseCase. Handles progress reporting and result
collection for the robot agent.
"""

import asyncio
import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timezone
from typing import Any, Dict, Optional

from loguru import logger


class JobExecutionError(Exception):
    """Raised when job execution fails."""

    pass


@dataclass
class JobExecutionResult:
    """
    Result of a job execution with DBOS-like semantics.

    Used by RobotAgent to get structured execution results.
    """

    workflow_id: str
    success: bool
    error: str | None = None
    executed_nodes: int = 0
    total_nodes: int = 0
    duration_ms: int = 0
    recovered: bool = False  # True if resumed from checkpoint


class JobExecutor:
    """
    Executes jobs by loading and running workflows.

    Provides a bridge between the robot agent's job management
    and the workflow execution infrastructure.

    Attributes:
        progress_callback: Optional callback for reporting progress
        continue_on_error: Whether to continue workflow on node errors
        job_timeout: Maximum execution time per job in seconds
    """

    def __init__(
        self,
        progress_callback: Callable[[str, int, str], None] | None = None,
        continue_on_error: bool = False,
        job_timeout: float = 3600.0,
        node_timeout: float = 120.0,
    ):
        """
        Initialize job executor.

        Args:
            progress_callback: Async callback(job_id, progress, message) for progress updates
            continue_on_error: Continue workflow execution on node errors
            job_timeout: Maximum execution time in seconds (default: 1 hour)
            node_timeout: Maximum execution time per node in seconds (default: 2 minutes)
        """
        self.progress_callback = progress_callback
        self.continue_on_error = continue_on_error
        self.job_timeout = job_timeout
        self.node_timeout = node_timeout

        # Track active executions
        self._active_jobs: dict[str, asyncio.Task] = {}
        self._job_results: dict[str, dict[str, Any]] = {}

    async def execute(
        self,
        job_data: dict[str, Any],
        initial_variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Execute a job and return the result.

        Args:
            job_data: Job data containing:
                - job_id: Unique job identifier
                - workflow_json: Serialized workflow definition (str or dict)
                - workflow_name: Name of the workflow
                - priority: Job priority (optional)
                - payload: Additional job payload (optional)
            initial_variables: Variables to inject into workflow execution

        Returns:
            Execution result dictionary containing:
                - success: Boolean indicating success/failure
                - job_id: Job identifier
                - started_at: Execution start timestamp
                - completed_at: Execution end timestamp
                - duration_ms: Execution duration in milliseconds
                - nodes_executed: Number of nodes executed
                - error: Error message (if failed)
                - result_data: Any output data from workflow
        """
        job_id = job_data.get("job_id", "unknown")
        workflow_name = job_data.get("workflow_name", "Unknown Workflow")

        logger.info(f"Starting job execution: {job_id} ({workflow_name})")

        started_at = datetime.now(UTC)
        result: dict[str, Any] = {
            "success": False,
            "job_id": job_id,
            "started_at": started_at.isoformat(),
            "completed_at": None,
            "duration_ms": 0,
            "nodes_executed": 0,
            "error": None,
            "result_data": {},
        }

        try:
            # Parse workflow JSON
            workflow_json = job_data.get("workflow_json", "{}")
            if isinstance(workflow_json, str):
                try:
                    workflow_dict = json.loads(workflow_json)
                except json.JSONDecodeError as e:
                    raise JobExecutionError(f"Invalid workflow JSON: {e}")
            elif isinstance(workflow_json, dict):
                workflow_dict = workflow_json
            else:
                raise JobExecutionError(
                    f"workflow_json must be str or dict, got {type(workflow_json)}"
                )

            # Report initial progress
            await self._report_progress(job_id, 0, "Loading workflow...")

            # Load workflow using workflow loader
            from casare_rpa.utils.workflow.workflow_loader import (
                load_workflow_from_dict,
            )

            workflow = load_workflow_from_dict(workflow_dict)

            await self._report_progress(job_id, 5, "Workflow loaded, starting execution...")

            # Merge job payload into initial variables
            combined_variables = dict(initial_variables or {})
            if job_data.get("payload"):
                combined_variables["_job_payload"] = job_data["payload"]
            combined_variables["_job_id"] = job_id
            combined_variables["_job_priority"] = job_data.get("priority", "normal")

            # Create execution use case with progress tracking
            from casare_rpa.application.use_cases.execute_workflow import (
                ExecuteWorkflowUseCase,
                ExecutionSettings,
            )
            from casare_rpa.domain.events import (
                EventBus,
                NodeCompleted,
                NodeFailed,
                NodeStarted,
            )

            # Create a local event bus for this execution
            event_bus = EventBus()

            # Track progress through events
            progress_tracker = _ProgressTracker(job_id, self.progress_callback)
            event_bus.subscribe(NodeStarted, progress_tracker.on_node_started)
            event_bus.subscribe(NodeCompleted, progress_tracker.on_node_completed)
            event_bus.subscribe(NodeFailed, progress_tracker.on_node_error)

            settings = ExecutionSettings(
                continue_on_error=self.continue_on_error,
                node_timeout=self.node_timeout,
            )

            use_case = ExecuteWorkflowUseCase(
                workflow=workflow,
                event_bus=event_bus,
                settings=settings,
                initial_variables=combined_variables,
            )

            # Execute with timeout
            try:
                success = await asyncio.wait_for(
                    use_case.execute(),
                    timeout=self.job_timeout,
                )
            except TimeoutError:
                raise JobExecutionError(f"Job execution timed out after {self.job_timeout}s")

            # Collect results
            completed_at = datetime.now(UTC)
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)

            result["success"] = success
            result["completed_at"] = completed_at.isoformat()
            result["duration_ms"] = duration_ms
            result["nodes_executed"] = len(use_case.executed_nodes)

            # Extract output variables
            if use_case.context:
                result["result_data"] = {
                    "variables": dict(use_case.context.variables),
                    "execution_path": list(use_case.context.execution_path),
                }

            if success:
                await self._report_progress(job_id, 100, "Job completed successfully")
                logger.info(
                    f"Job {job_id} completed successfully in {duration_ms}ms "
                    f"({result['nodes_executed']} nodes)"
                )
            else:
                result["error"] = "Workflow execution failed"
                if use_case.context and use_case.context.errors:
                    result["error"] = "; ".join(
                        [f"{node}: {msg}" for node, msg in use_case.context.errors]
                    )
                await self._report_progress(job_id, 100, f"Job failed: {result['error']}")
                logger.error(f"Job {job_id} failed: {result['error']}")

        except JobExecutionError as e:
            result["error"] = str(e)
            result["completed_at"] = datetime.now(UTC).isoformat()
            result["duration_ms"] = int((datetime.now(UTC) - started_at).total_seconds() * 1000)
            await self._report_progress(job_id, 100, f"Job error: {e}")
            logger.error(f"Job {job_id} execution error: {e}")

        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"
            result["completed_at"] = datetime.now(UTC).isoformat()
            result["duration_ms"] = int((datetime.now(UTC) - started_at).total_seconds() * 1000)
            await self._report_progress(job_id, 100, f"Job error: {e}")
            logger.exception(f"Job {job_id} unexpected error")

        finally:
            # Store result for later retrieval
            self._job_results[job_id] = result

        return result

    async def _report_progress(self, job_id: str, progress: int, message: str) -> None:
        """Report job progress through callback."""
        if self.progress_callback:
            try:
                result = self.progress_callback(job_id, progress, message)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.warning(f"Progress callback error for job {job_id}: {e}")

    async def execute_workflow(
        self,
        workflow_json: str,
        workflow_id: str,
        initial_variables: dict[str, Any] | None = None,
        wait_for_result: bool = True,
        on_progress: Callable[[int, str], Awaitable[None]] | None = None,
    ) -> JobExecutionResult:
        """
        Execute a workflow with DBOS-like semantics.

        This is the canonical execution entry point for RobotAgent.
        Wraps the execute() method and returns a structured result.

        Args:
            workflow_json: Serialized workflow definition (JSON string or dict)
            workflow_id: Unique identifier for this execution
            initial_variables: Initial execution variables
            wait_for_result: Wait for execution to complete (always True for now)
            on_progress: Optional callback for progress updates (progress%, node_id)

        Returns:
            JobExecutionResult with execution outcome
        """
        # Set up progress tracking if callback provided
        original_callback = self.progress_callback
        if on_progress:

            async def wrapped_progress(job_id: str, progress: int, message: str) -> None:
                # Extract node_id from message (format: "Executing: node_id" or "Completed: node_id")
                node_id = message.split(": ", 1)[1] if ": " in message else message
                try:
                    await on_progress(progress, node_id)
                except Exception as e:
                    logger.debug(f"Progress callback error: {e}")
                # Also call original callback if present
                if original_callback:
                    try:
                        result = original_callback(job_id, progress, message)
                        if asyncio.iscoroutine(result):
                            await result
                    except Exception:
                        pass

            self.progress_callback = wrapped_progress

        try:
            # Build job_data for execute()
            job_data = {
                "job_id": workflow_id,
                "workflow_json": workflow_json,
                "workflow_name": f"Job-{workflow_id[:8]}",
            }

            result = await self.execute(job_data, initial_variables)

            return JobExecutionResult(
                workflow_id=workflow_id,
                success=result.get("success", False),
                error=result.get("error"),
                executed_nodes=result.get("nodes_executed", 0),
                total_nodes=result.get("nodes_executed", 0),  # Not tracked separately
                duration_ms=result.get("duration_ms", 0),
                recovered=False,  # Checkpointing not implemented in JobExecutor
            )
        finally:
            # Restore original callback
            self.progress_callback = original_callback

    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running job.

        Args:
            job_id: Job to cancel

        Returns:
            True if job was cancelled, False if not found
        """
        if job_id in self._active_jobs:
            task = self._active_jobs[job_id]
            task.cancel()
            logger.info(f"Cancelled job: {job_id}")
            return True
        return False

    def get_result(self, job_id: str) -> dict[str, Any] | None:
        """
        Get the result of a completed job.

        Args:
            job_id: Job identifier

        Returns:
            Job result dictionary or None if not found
        """
        return self._job_results.get(job_id)

    def clear_result(self, job_id: str) -> None:
        """Remove a job result from memory."""
        self._job_results.pop(job_id, None)

    @property
    def active_job_count(self) -> int:
        """Get count of currently executing jobs."""
        return len(self._active_jobs)


class _ProgressTracker:
    """Internal helper for tracking execution progress through events."""

    def __init__(
        self,
        job_id: str,
        callback: Callable[[str, int, str], None] | None,
    ):
        self.job_id = job_id
        self.callback = callback
        self.nodes_started = 0
        self.nodes_completed = 0
        self.total_nodes = 0
        self.current_node = ""

    def on_node_started(self, event: Any) -> None:
        """Handle node started event."""
        self.nodes_started += 1
        self.current_node = event.node_id if hasattr(event, "node_id") else "unknown"

        if self.callback:
            progress = min(95, 5 + int((self.nodes_completed / max(1, self.nodes_started)) * 90))
            try:
                result = self.callback(
                    self.job_id,
                    progress,
                    f"Executing: {self.current_node}",
                )
                if asyncio.iscoroutine(result):
                    asyncio.create_task(result)
            except Exception:
                pass

    def on_node_completed(self, event: Any) -> None:
        """Handle node completed event."""
        self.nodes_completed += 1
        node_id = event.node_id if hasattr(event, "node_id") else "unknown"

        if self.callback:
            progress = min(95, 5 + int((self.nodes_completed / max(1, self.nodes_started)) * 90))
            try:
                result = self.callback(
                    self.job_id,
                    progress,
                    f"Completed: {node_id}",
                )
                if asyncio.iscoroutine(result):
                    asyncio.create_task(result)
            except Exception:
                pass

    def on_node_error(self, event: Any) -> None:
        """Handle node error event."""
        node_id = event.node_id if hasattr(event, "node_id") else "unknown"
        error = event.error_message if hasattr(event, "error_message") else "Unknown error"

        if self.callback:
            try:
                result = self.callback(
                    self.job_id,
                    -1,  # Negative indicates error
                    f"Error in {node_id}: {error}",
                )
                if asyncio.iscoroutine(result):
                    asyncio.create_task(result)
            except Exception:
                pass
