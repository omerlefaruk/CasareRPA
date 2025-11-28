"""
PgQueuer Producer for Orchestrator.

Handles job submission to the PgQueuer job queue from the Orchestrator.
"""

import asyncio
from typing import Any, Dict, Optional
from loguru import logger
import asyncpg
from pgqueuer import QueueManager
from pgqueuer.models import Job

from .config import QueueConfig
from .models import JobModel, JobPriority, JobStatus


class PgQueuerProducer:
    """
    Job queue producer using PgQueuer.

    Used by the Orchestrator to enqueue workflow execution jobs.

    Features:
    - Priority-based job submission
    - Async job enqueuing
    - Connection pooling
    - Batch job submission
    - Job status tracking

    Example:
        ```python
        config = QueueConfig.from_env()
        producer = PgQueuerProducer(config)

        await producer.start()
        job_id = await producer.enqueue_job(workflow_json, priority=10)
        await producer.stop()
        ```
    """

    def __init__(self, config: QueueConfig):
        """
        Initialize producer.

        Args:
            config: Queue configuration
        """
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None
        self.queue_manager: Optional[QueueManager] = None
        self._running = False

        logger.info(f"PgQueuer Producer initialized for queue: {config.queue_name}")

    async def start(self) -> None:
        """Start the producer (create connection pool)."""
        if self._running:
            logger.warning("Producer already running")
            return

        try:
            # Create asyncpg connection pool
            self.pool = await asyncpg.create_pool(**self.config.to_connection_kwargs())

            # Initialize queue manager
            self.queue_manager = QueueManager(self.pool)

            self._running = True
            logger.info("PgQueuer Producer started")

        except Exception as e:
            logger.exception(f"Failed to start producer: {e}")
            raise

    async def stop(self) -> None:
        """Stop the producer (close connection pool)."""
        if not self._running:
            return

        self._running = False

        if self.pool:
            await self.pool.close()
            self.pool = None

        self.queue_manager = None
        logger.info("PgQueuer Producer stopped")

    async def enqueue_job(
        self,
        job_id: str,
        workflow_json: str,
        priority: int = JobPriority.NORMAL,
        tenant_id: Optional[str] = None,
        workflow_name: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Enqueue a workflow execution job.

        Args:
            job_id: Unique job identifier
            workflow_json: Serialized workflow JSON
            priority: Job priority (0-20, higher = more urgent)
            tenant_id: Tenant ID for multi-tenancy
            workflow_name: Workflow name for monitoring
            tags: Custom tags

        Returns:
            Job ID

        Raises:
            RuntimeError: If producer not started
        """
        if not self._running or not self.queue_manager:
            raise RuntimeError("Producer not started. Call start() first.")

        # Create job model
        job = JobModel(
            job_id=job_id,
            workflow_json=workflow_json,
            priority=priority,
            tenant_id=tenant_id,
            workflow_name=workflow_name,
            tags=tags or {},
            max_retries=self.config.max_retries,
            visibility_timeout=self.config.visibility_timeout,
        )

        try:
            # Enqueue using PgQueuer
            await self.queue_manager.enqueue(
                queue_name=self.config.queue_name,
                payload=job.to_pgqueuer_payload(),
                priority=priority,
            )

            logger.info(
                f"Job enqueued: {job_id} (priority={priority}, "
                f"workflow={workflow_name or 'unknown'})"
            )

            return job_id

        except Exception as e:
            logger.exception(f"Failed to enqueue job {job_id}: {e}")
            raise

    async def enqueue_batch(
        self,
        jobs: list[tuple[str, str, int]],  # [(job_id, workflow_json, priority)]
    ) -> list[str]:
        """
        Enqueue multiple jobs in batch.

        Args:
            jobs: List of (job_id, workflow_json, priority) tuples

        Returns:
            List of enqueued job IDs

        Raises:
            RuntimeError: If producer not started
        """
        if not self._running or not self.queue_manager:
            raise RuntimeError("Producer not started. Call start() first.")

        job_ids = []

        try:
            for job_id, workflow_json, priority in jobs:
                await self.enqueue_job(job_id, workflow_json, priority)
                job_ids.append(job_id)

            logger.info(f"Batch enqueued: {len(job_ids)} jobs")
            return job_ids

        except Exception as e:
            logger.exception(f"Failed to enqueue batch: {e}")
            raise

    async def get_queue_depth(self) -> int:
        """
        Get current queue depth (number of pending jobs).

        Returns:
            Number of jobs in queue

        Raises:
            RuntimeError: If producer not started
        """
        if not self._running or not self.pool:
            raise RuntimeError("Producer not started")

        query = """
            SELECT COUNT(*)
            FROM pgqueuer.jobs
            WHERE queue_name = $1 AND status = 'pending'
        """

        async with self.pool.acquire() as conn:
            count = await conn.fetchval(query, self.config.queue_name)
            return count or 0

    async def get_job_status(self, job_id: str) -> Optional[JobStatus]:
        """
        Get current status of a job.

        Args:
            job_id: Job identifier

        Returns:
            JobStatus if found, None otherwise

        Raises:
            RuntimeError: If producer not started
        """
        if not self._running or not self.pool:
            raise RuntimeError("Producer not started")

        query = """
            SELECT status
            FROM pgqueuer.jobs
            WHERE payload->>'job_id' = $1
        """

        async with self.pool.acquire() as conn:
            status = await conn.fetchval(query, job_id)
            return JobStatus(status) if status else None

    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a pending or claimed job.

        Args:
            job_id: Job to cancel

        Returns:
            True if job was cancelled, False if not found

        Raises:
            RuntimeError: If producer not started
        """
        if not self._running or not self.pool:
            raise RuntimeError("Producer not started")

        query = """
            UPDATE pgqueuer.jobs
            SET status = 'cancelled'
            WHERE payload->>'job_id' = $1
            AND status IN ('pending', 'claimed')
            RETURNING id
        """

        async with self.pool.acquire() as conn:
            result = await conn.fetchval(query, job_id)
            cancelled = result is not None

            if cancelled:
                logger.info(f"Job cancelled: {job_id}")
            else:
                logger.warning(f"Job not found or cannot be cancelled: {job_id}")

            return cancelled

    async def purge_queue(self) -> int:
        """
        Purge all pending jobs from queue.

        WARNING: This deletes all pending jobs!

        Returns:
            Number of jobs deleted

        Raises:
            RuntimeError: If producer not started
        """
        if not self._running or not self.pool:
            raise RuntimeError("Producer not started")

        query = """
            DELETE FROM pgqueuer.jobs
            WHERE queue_name = $1 AND status = 'pending'
            RETURNING id
        """

        async with self.pool.acquire() as conn:
            result = await conn.fetch(query, self.config.queue_name)
            count = len(result)

            logger.warning(f"Queue purged: {count} jobs deleted")
            return count

    async def health_check(self) -> bool:
        """
        Check if producer is healthy and can connect to database.

        Returns:
            True if healthy, False otherwise
        """
        if not self._running or not self.pool:
            return False

        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Producer health check failed: {e}")
            return False

    def __enter__(self):
        """Context manager support (sync wrapper)."""
        raise RuntimeError("Use 'async with' instead of 'with'")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
