"""
Job Executor for Robot Agent.

Handles concurrent job execution with:
- Configurable concurrency limits
- Job queue management
- Execution lifecycle management
- Integration with checkpointing and metrics
"""

import asyncio
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from loguru import logger
import orjson

from casare_rpa.utils.workflow_loader import load_workflow_from_dict
from casare_rpa.runner.workflow_runner import WorkflowRunner

from .checkpoint import CheckpointManager
from .metrics import MetricsCollector, get_metrics_collector
from .audit import AuditLogger
from .progress_reporter import ProgressReporter, CancellationChecker, JobLocker
from .offline_queue import OfflineQueue


class JobStatus(Enum):
    """Status of a job in the executor."""
    QUEUED = "queued"
    STARTING = "starting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class JobInfo:
    """Information about a job being executed."""
    job_id: str
    workflow_json: str
    status: JobStatus = JobStatus.QUEUED
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    task: Optional[asyncio.Task] = None
    error: Optional[str] = None
    result: Optional[Dict] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
        }


class JobExecutor:
    """
    Manages concurrent job execution.

    Features:
    - Configurable maximum concurrent jobs
    - Job queue for pending jobs
    - Automatic checkpoint saving
    - Progress reporting
    - Cancellation support
    """

    def __init__(
        self,
        max_concurrent_jobs: int = 3,
        checkpoint_manager: Optional[CheckpointManager] = None,
        metrics_collector: Optional[MetricsCollector] = None,
        audit_logger: Optional[AuditLogger] = None,
        progress_reporter: Optional[ProgressReporter] = None,
        offline_queue: Optional[OfflineQueue] = None,
        job_locker: Optional[JobLocker] = None,
        on_job_complete: Optional[Callable[[str, bool, Optional[str]], Any]] = None,
    ):
        """
        Initialize job executor.

        Args:
            max_concurrent_jobs: Maximum jobs to run concurrently
            checkpoint_manager: For saving/restoring checkpoints
            metrics_collector: For tracking metrics
            audit_logger: For audit logging
            progress_reporter: For reporting progress to Orchestrator
            offline_queue: For offline job caching
            job_locker: For job locking
            on_job_complete: Callback when job completes (job_id, success, error)
        """
        self.max_concurrent_jobs = max_concurrent_jobs
        self.checkpoint_manager = checkpoint_manager
        self.metrics = metrics_collector or get_metrics_collector()
        self.audit = audit_logger
        self.progress_reporter = progress_reporter
        self.offline_queue = offline_queue
        self.job_locker = job_locker
        self.on_job_complete = on_job_complete

        # Concurrency control
        self._semaphore = asyncio.Semaphore(max_concurrent_jobs)
        self._running_jobs: Dict[str, JobInfo] = {}
        self._pending_queue: asyncio.Queue = asyncio.Queue()

        # Cancellation tokens
        self._cancellation_checkers: Dict[str, CancellationChecker] = {}

        # State
        self._running = False
        self._processor_task: Optional[asyncio.Task] = None

        logger.info(f"Job executor initialized (max_concurrent={max_concurrent_jobs})")

    @property
    def running_count(self) -> int:
        """Get number of currently running jobs."""
        return len(self._running_jobs)

    @property
    def is_at_capacity(self) -> bool:
        """Check if at maximum capacity."""
        return self.running_count >= self.max_concurrent_jobs

    async def start(self):
        """Start the job executor."""
        self._running = True
        self._processor_task = asyncio.create_task(self._process_queue())
        logger.info("Job executor started")

    async def stop(self, cancel_running: bool = False):
        """
        Stop the job executor.

        Args:
            cancel_running: Whether to cancel running jobs
        """
        self._running = False

        if cancel_running:
            # Cancel all running jobs
            for job_id, job_info in list(self._running_jobs.items()):
                await self.cancel_job(job_id, "Executor stopping")

        # Wait for queue processor to stop
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass

        logger.info("Job executor stopped")

    async def submit_job(
        self,
        job_id: str,
        workflow_json: str,
        priority: int = 0,
    ) -> bool:
        """
        Submit a job for execution.

        Args:
            job_id: Job identifier
            workflow_json: Workflow JSON string
            priority: Job priority (higher = sooner)

        Returns:
            True if job was accepted
        """
        if job_id in self._running_jobs:
            logger.warning(f"Job {job_id} already running")
            return False

        job_info = JobInfo(
            job_id=job_id,
            workflow_json=workflow_json,
            status=JobStatus.QUEUED,
        )

        # Add to queue (priority ignored for now - FIFO)
        await self._pending_queue.put(job_info)

        if self.audit:
            self.audit.job_received(job_id, "submitted")

        logger.info(f"Job {job_id} submitted to executor")
        return True

    async def cancel_job(
        self,
        job_id: str,
        reason: Optional[str] = None,
    ) -> bool:
        """
        Cancel a running or queued job.

        Args:
            job_id: Job to cancel
            reason: Cancellation reason

        Returns:
            True if job was cancelled
        """
        job_info = self._running_jobs.get(job_id)
        if not job_info:
            logger.warning(f"Job {job_id} not found for cancellation")
            return False

        if job_info.status not in (JobStatus.RUNNING, JobStatus.STARTING):
            logger.warning(f"Job {job_id} not in cancellable state: {job_info.status}")
            return False

        # Cancel the task
        if job_info.task and not job_info.task.done():
            job_info.task.cancel()

        job_info.status = JobStatus.CANCELLED
        job_info.error = reason or "Cancelled by request"

        if self.progress_reporter:
            await self.progress_reporter.report_cancelled(reason)

        if self.audit:
            self.audit.job_cancelled(job_id, reason)

        logger.info(f"Job {job_id} cancelled: {reason}")
        return True

    async def _process_queue(self):
        """Background task to process job queue."""
        while self._running:
            try:
                # Get next job from queue (with timeout)
                try:
                    job_info = await asyncio.wait_for(
                        self._pending_queue.get(),
                        timeout=1.0,
                    )
                except asyncio.TimeoutError:
                    continue

                # Wait for available slot
                async with self._semaphore:
                    # Start job execution
                    job_info.task = asyncio.create_task(
                        self._execute_job(job_info)
                    )
                    self._running_jobs[job_info.job_id] = job_info

                    # Wait for job to complete (but don't block queue processing)
                    # The task will remove itself from _running_jobs when done

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Queue processor error: {e}")
                await asyncio.sleep(1)

    async def _execute_job(self, job_info: JobInfo):
        """
        Execute a single job.

        Args:
            job_info: Job information
        """
        job_id = job_info.job_id
        job_info.status = JobStatus.STARTING
        job_info.started_at = datetime.now(timezone.utc)

        success = False
        error_message = None

        try:
            # Parse workflow
            if isinstance(job_info.workflow_json, str):
                workflow_data = orjson.loads(job_info.workflow_json)
            else:
                workflow_data = job_info.workflow_json

            # Load workflow
            workflow = load_workflow_from_dict(workflow_data)
            total_nodes = len(workflow.nodes)
            workflow_name = workflow.metadata.name if workflow.metadata else "unknown"

            # Start metrics tracking
            self.metrics.start_job(job_id, workflow_name, total_nodes)

            # Start progress reporting
            if self.progress_reporter:
                await self.progress_reporter.start_job(job_id, workflow_name, total_nodes)

            # Setup cancellation checker
            if self.progress_reporter and hasattr(self.progress_reporter, 'connection'):
                checker = CancellationChecker(self.progress_reporter.connection)
                checker.start(job_id)
                self._cancellation_checkers[job_id] = checker

            if self.audit:
                self.audit.job_started(job_id, total_nodes)

            job_info.status = JobStatus.RUNNING

            # Create and run workflow
            runner = WorkflowRunner(workflow)

            # Setup checkpoint hook if available
            if self.checkpoint_manager:
                self.checkpoint_manager.start_job(job_id, workflow_name)
                # Hook into node completion for checkpoints
                self._setup_checkpoint_hook(runner, job_id)

            # Execute workflow
            success = await self._run_with_cancellation_check(runner, job_id)

            # Check if cancelled during execution
            checker = self._cancellation_checkers.get(job_id)
            if checker and checker.is_cancelled:
                success = False
                error_message = "Job was cancelled"
                job_info.status = JobStatus.CANCELLED
            else:
                job_info.status = JobStatus.COMPLETED if success else JobStatus.FAILED

                if not success:
                    # Get error from runner context
                    if hasattr(runner, 'context') and runner.context.errors:
                        error_message = str(runner.context.errors[-1])
                    else:
                        error_message = "Workflow execution failed"

        except asyncio.CancelledError:
            job_info.status = JobStatus.CANCELLED
            error_message = "Job was cancelled"
            logger.info(f"Job {job_id} was cancelled")

        except Exception as e:
            job_info.status = JobStatus.FAILED
            error_message = str(e)
            logger.exception(f"Job {job_id} failed with error: {e}")

        finally:
            job_info.completed_at = datetime.now(timezone.utc)
            job_info.error = error_message

            duration_ms = (
                (job_info.completed_at - job_info.started_at).total_seconds() * 1000
                if job_info.started_at else 0
            )

            # End metrics tracking
            self.metrics.end_job(success, error_message)

            # End progress reporting
            if self.progress_reporter:
                await self.progress_reporter.end_job(
                    success,
                    error_message,
                )

            # Audit logging
            if self.audit:
                if success:
                    self.audit.job_completed(job_id, duration_ms)
                elif job_info.status == JobStatus.CANCELLED:
                    pass  # Already logged in cancel_job
                else:
                    self.audit.job_failed(job_id, error_message or "Unknown error", duration_ms)

            # Stop cancellation checker
            checker = self._cancellation_checkers.pop(job_id, None)
            if checker:
                checker.stop()

            # Checkpoint cleanup
            if self.checkpoint_manager:
                if success:
                    await self.checkpoint_manager.clear_checkpoints(job_id)
                self.checkpoint_manager.end_job()

            # Remove from running jobs
            self._running_jobs.pop(job_id, None)

            # Callback
            if self.on_job_complete:
                try:
                    result = self.on_job_complete(job_id, success, error_message)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    logger.error(f"Job complete callback error: {e}")

    async def _run_with_cancellation_check(
        self,
        runner: WorkflowRunner,
        job_id: str,
    ) -> bool:
        """
        Run workflow with periodic cancellation checks.

        Args:
            runner: WorkflowRunner instance
            job_id: Job identifier

        Returns:
            True if completed successfully
        """
        # Start the workflow run
        run_task = asyncio.create_task(runner.run())

        checker = self._cancellation_checkers.get(job_id)

        while not run_task.done():
            # Check for cancellation
            if checker and checker.is_cancelled:
                run_task.cancel()
                try:
                    await run_task
                except asyncio.CancelledError:
                    pass
                return False

            # Wait a bit before next check
            try:
                await asyncio.wait_for(asyncio.shield(run_task), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                run_task.cancel()
                return False

        return run_task.result()

    def _setup_checkpoint_hook(self, runner: WorkflowRunner, job_id: str):
        """Setup checkpoint saving hook on workflow runner."""
        if not self.checkpoint_manager:
            return

        # Subscribe to node completion events
        if hasattr(runner, 'event_bus') and runner.event_bus:
            from casare_rpa.core.events import EventType

            def on_node_complete(event):
                if event.node_id and hasattr(runner, 'context'):
                    asyncio.create_task(
                        self.checkpoint_manager.save_checkpoint(
                            event.node_id,
                            runner.context,
                        )
                    )

            runner.event_bus.subscribe(EventType.NODE_COMPLETED, on_node_complete)

    def get_status(self) -> Dict[str, Any]:
        """Get executor status."""
        return {
            "max_concurrent_jobs": self.max_concurrent_jobs,
            "running_count": self.running_count,
            "pending_count": self._pending_queue.qsize(),
            "is_at_capacity": self.is_at_capacity,
            "running_jobs": [
                job.to_dict() for job in self._running_jobs.values()
            ],
        }

    def set_max_concurrent(self, max_jobs: int):
        """
        Update maximum concurrent jobs.

        Note: Takes effect for new jobs only.
        """
        if max_jobs < 1:
            raise ValueError("max_concurrent_jobs must be at least 1")

        self.max_concurrent_jobs = max_jobs
        self._semaphore = asyncio.Semaphore(max_jobs)
        logger.info(f"Max concurrent jobs updated to {max_jobs}")


class JobExecutorConfig:
    """Configuration for job executor."""

    def __init__(
        self,
        max_concurrent_jobs: int = 3,
        checkpoint_enabled: bool = True,
        progress_reporting_enabled: bool = True,
        cancellation_check_interval: float = 2.0,
    ):
        self.max_concurrent_jobs = max_concurrent_jobs
        self.checkpoint_enabled = checkpoint_enabled
        self.progress_reporting_enabled = progress_reporting_enabled
        self.cancellation_check_interval = cancellation_check_interval

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JobExecutorConfig":
        """Create from dictionary."""
        return cls(
            max_concurrent_jobs=data.get("max_concurrent_jobs", 3),
            checkpoint_enabled=data.get("checkpoint_enabled", True),
            progress_reporting_enabled=data.get("progress_reporting_enabled", True),
            cancellation_check_interval=data.get("cancellation_check_interval", 2.0),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "max_concurrent_jobs": self.max_concurrent_jobs,
            "checkpoint_enabled": self.checkpoint_enabled,
            "progress_reporting_enabled": self.progress_reporting_enabled,
            "cancellation_check_interval": self.cancellation_check_interval,
        }
