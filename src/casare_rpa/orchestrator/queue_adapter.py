"""
Queue Adapter for Orchestrator Engine.

Provides a unified interface for both in-memory JobQueue and PgQueuer,
allowing gradual migration from in-memory to distributed queue.

This adapter implements the queue interface expected by OrchestratorEngine
while delegating to either JobQueue or PgQueuerProducer based on configuration.
"""

import asyncio
from typing import Optional, Dict, Any, Tuple, Callable
from datetime import datetime
from loguru import logger

from .models import Job, JobStatus, JobPriority
from .job_queue import JobQueue

# Import PgQueuer components (may not be available initially)
try:
    from casare_rpa.infrastructure.queue.producer import PgQueuerProducer
    from casare_rpa.infrastructure.queue.config import QueueConfig
    from casare_rpa.infrastructure.queue.models import (
        JobModel as PgJobModel,
        JobPriority as PgJobPriority,
    )

    PGQUEUER_AVAILABLE = True
except ImportError:
    PGQUEUER_AVAILABLE = False
    logger.warning("PgQueuer not available, using in-memory queue only")


class QueueAdapter:
    """
    Unified queue interface for Orchestrator Engine.

    Supports both:
    - In-memory JobQueue (current, default)
    - PgQueuerProducer (new, distributed)

    The adapter translates between orchestrator Job model and queue-specific models,
    providing a consistent interface regardless of backend.
    """

    def __init__(
        self,
        use_pgqueuer: bool = False,
        pgqueuer_config: Optional[QueueConfig] = None,
        job_queue: Optional[JobQueue] = None,
        on_state_change: Optional[Callable] = None,
    ):
        """
        Initialize queue adapter.

        Args:
            use_pgqueuer: If True, use PgQueuer; otherwise use in-memory JobQueue
            pgqueuer_config: Configuration for PgQueuer (required if use_pgqueuer=True)
            job_queue: Existing JobQueue instance (if not using PgQueuer)
            on_state_change: Callback for job state changes
        """
        self.use_pgqueuer = use_pgqueuer and PGQUEUER_AVAILABLE
        self.on_state_change = on_state_change

        # Initialize queue backend
        if self.use_pgqueuer:
            if not PGQUEUER_AVAILABLE:
                raise RuntimeError(
                    "PgQueuer not available. Install with: pip install pgqueuer"
                )
            if not pgqueuer_config:
                raise ValueError("pgqueuer_config required when use_pgqueuer=True")

            self.pgqueuer_producer = PgQueuerProducer(pgqueuer_config)
            self.job_queue = None
            logger.info("QueueAdapter initialized with PgQueuer backend")
        else:
            self.pgqueuer_producer = None
            self.job_queue = job_queue or JobQueue(
                dedup_window_seconds=300,
                default_timeout_seconds=3600,
                on_state_change=on_state_change,
            )
            logger.info("QueueAdapter initialized with in-memory JobQueue backend")

    async def start(self) -> None:
        """Start the queue backend."""
        if self.use_pgqueuer and self.pgqueuer_producer:
            await self.pgqueuer_producer.start()
            logger.info("PgQueuer producer started")

    async def stop(self) -> None:
        """Stop the queue backend."""
        if self.use_pgqueuer and self.pgqueuer_producer:
            await self.pgqueuer_producer.stop()
            logger.info("PgQueuer producer stopped")

    def enqueue(
        self,
        job: Job,
        check_duplicate: bool = True,
        params: Optional[Dict] = None,
    ) -> Tuple[bool, str]:
        """
        Enqueue a job (sync interface for backward compatibility).

        Args:
            job: Job to enqueue
            check_duplicate: Check for duplicates (in-memory only)
            params: Parameters for deduplication (in-memory only)

        Returns:
            (success, message) tuple
        """
        if self.use_pgqueuer:
            # PgQueuer is async, so we need to run in event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Create task and return immediately
                    asyncio.create_task(self._enqueue_pgqueuer(job))
                    return True, f"Job {job.id} enqueued"
                else:
                    # Run synchronously
                    loop.run_until_complete(self._enqueue_pgqueuer(job))
                    return True, f"Job {job.id} enqueued"
            except Exception as e:
                logger.exception(f"Failed to enqueue job to PgQueuer: {e}")
                return False, str(e)
        else:
            # Use in-memory queue
            return self.job_queue.enqueue(job, check_duplicate, params)

    async def enqueue_async(
        self,
        job: Job,
        check_duplicate: bool = True,
        params: Optional[Dict] = None,
    ) -> Tuple[bool, str]:
        """
        Enqueue a job (async interface).

        Args:
            job: Job to enqueue
            check_duplicate: Check for duplicates (in-memory only)
            params: Parameters for deduplication (in-memory only)

        Returns:
            (success, message) tuple
        """
        if self.use_pgqueuer:
            try:
                await self._enqueue_pgqueuer(job)
                return True, f"Job {job.id} enqueued"
            except Exception as e:
                logger.exception(f"Failed to enqueue job to PgQueuer: {e}")
                return False, str(e)
        else:
            # In-memory queue is sync
            return self.job_queue.enqueue(job, check_duplicate, params)

    async def _enqueue_pgqueuer(self, job: Job) -> None:
        """
        Enqueue job to PgQueuer.

        Converts orchestrator Job to PgQueuer JobModel format.
        """
        if not self.pgqueuer_producer:
            raise RuntimeError("PgQueuer producer not initialized")

        # Convert priority
        priority = self._convert_priority(job.priority)

        # Enqueue
        await self.pgqueuer_producer.enqueue_job(
            job_id=job.id,
            workflow_json=job.workflow_json,
            priority=priority,
            tenant_id=None,  # TODO: Add tenant support
            workflow_name=job.workflow_name,
            tags={
                "robot_id": job.robot_id or "",
                "created_at": job.created_at or "",
            },
        )

        # Trigger state change callback
        if self.on_state_change:
            self.on_state_change(job, JobStatus.QUEUED)

    def dequeue(self) -> Optional[Job]:
        """
        Dequeue next job (in-memory only).

        For PgQueuer, jobs are claimed by consumers directly.

        Returns:
            Next job or None
        """
        if self.use_pgqueuer:
            logger.warning(
                "dequeue() not supported with PgQueuer. "
                "Jobs are claimed by Robot consumers."
            )
            return None
        else:
            return self.job_queue.dequeue()

    def mark_running(self, job_id: str, robot_id: str) -> bool:
        """
        Mark job as running (in-memory only).

        For PgQueuer, status is managed by consumers.
        """
        if self.use_pgqueuer:
            # PgQueuer consumer handles this
            return True
        else:
            return self.job_queue.mark_running(job_id, robot_id)

    def mark_completed(self, job_id: str, result: Optional[Dict] = None) -> bool:
        """
        Mark job as completed (in-memory only).

        For PgQueuer, status is managed by consumers.
        """
        if self.use_pgqueuer:
            # PgQueuer consumer handles this
            return True
        else:
            return self.job_queue.mark_completed(job_id, result)

    def mark_failed(self, job_id: str, error: str) -> bool:
        """
        Mark job as failed (in-memory only).

        For PgQueuer, status is managed by consumers.
        """
        if self.use_pgqueuer:
            # PgQueuer consumer handles this
            return True
        else:
            return self.job_queue.mark_failed(job_id, error)

    def get_pending_count(self) -> int:
        """Get number of pending jobs."""
        if self.use_pgqueuer and self.pgqueuer_producer:
            # Run async method synchronously
            try:
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(self.pgqueuer_producer.get_queue_depth())
            except Exception:
                return 0
        else:
            return self.job_queue.get_pending_count()

    async def get_pending_count_async(self) -> int:
        """Get number of pending jobs (async)."""
        if self.use_pgqueuer and self.pgqueuer_producer:
            return await self.pgqueuer_producer.get_queue_depth()
        else:
            return self.job_queue.get_pending_count()

    def get_status(self) -> Dict[str, Any]:
        """Get queue status."""
        if self.use_pgqueuer:
            return {
                "backend": "pgqueuer",
                "pending_jobs": self.get_pending_count(),
                "healthy": True,  # TODO: Add health check
            }
        else:
            stats = self.job_queue.get_stats()
            return {
                "backend": "in_memory",
                "pending_jobs": stats["queue_depth"],
                "total_jobs": stats["total_jobs"],
                "completed": stats["completed_jobs"],
                "failed": stats["failed_jobs"],
            }

    @staticmethod
    def _convert_priority(priority: JobPriority) -> int:
        """
        Convert orchestrator JobPriority to PgQueuer priority (0-20).

        Mapping:
        - URGENT (3) → 20 (CRITICAL)
        - HIGH (2) → 15 (URGENT)
        - NORMAL (1) → 5 (NORMAL)
        - LOW (0) → 0 (LOW)
        """
        priority_map = {
            JobPriority.URGENT: 20,
            JobPriority.HIGH: 15,
            JobPriority.NORMAL: 5,
            JobPriority.LOW: 0,
        }
        return priority_map.get(priority, 5)
