"""
PgQueuer Consumer for Robot Agent.

Handles job consumption and execution tracking for Robot agents.
"""

import asyncio
from typing import AsyncIterator, Callable, Optional, Awaitable
from loguru import logger
import asyncpg
from pgqueuer import QueueManager
from pgqueuer.models import Job

from .config import QueueConfig
from .models import JobModel, JobStatus


class PgQueuerConsumer:
    """
    Job queue consumer using PgQueuer.

    Used by Robot agents to claim and execute workflow jobs.

    Features:
    - Priority-based job claiming
    - Visibility timeout pattern
    - Heartbeat mechanism
    - Dead Letter Queue integration
    - Concurrent job execution

    Example:
        ```python
        config = QueueConfig.from_env()
        consumer = PgQueuerConsumer(config, robot_id="robot-001")

        async def handle_job(job: JobModel):
            # Execute workflow
            return True

        await consumer.start(handle_job)
        ```
    """

    def __init__(self, config: QueueConfig, robot_id: str):
        """
        Initialize consumer.

        Args:
            config: Queue configuration
            robot_id: Unique robot identifier
        """
        self.config = config
        self.robot_id = robot_id
        self.pool: Optional[asyncpg.Pool] = None
        self.queue_manager: Optional[QueueManager] = None
        self._running = False
        self._consumer_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._claimed_jobs: dict[str, JobModel] = {}

        logger.info(
            f"PgQueuer Consumer initialized: robot={robot_id}, "
            f"queue={config.queue_name}"
        )

    async def start(
        self,
        job_handler: Callable[[JobModel], Awaitable[bool]],
    ) -> None:
        """
        Start the consumer.

        Args:
            job_handler: Async function to handle jobs
                        Returns True if job succeeded, False otherwise
        """
        if self._running:
            logger.warning("Consumer already running")
            return

        try:
            # Create connection pool
            self.pool = await asyncpg.create_pool(**self.config.to_connection_kwargs())

            # Initialize queue manager
            self.queue_manager = QueueManager(self.pool)

            self._running = True

            # Start consumer task
            self._consumer_task = asyncio.create_task(self._consume_loop(job_handler))

            # Start heartbeat task
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

            logger.info(f"PgQueuer Consumer started: {self.robot_id}")

        except Exception as e:
            logger.exception(f"Failed to start consumer: {e}")
            raise

    async def stop(self) -> None:
        """Stop the consumer."""
        if not self._running:
            return

        self._running = False

        # Cancel tasks
        if self._consumer_task:
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                pass

        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        # Release claimed jobs
        for job_id in list(self._claimed_jobs.keys()):
            await self.release_job(job_id)

        # Close pool
        if self.pool:
            await self.pool.close()
            self.pool = None

        self.queue_manager = None
        logger.info(f"PgQueuer Consumer stopped: {self.robot_id}")

    async def _consume_loop(
        self,
        job_handler: Callable[[JobModel], Awaitable[bool]],
    ) -> None:
        """
        Main consumer loop.

        Args:
            job_handler: Job handler function
        """
        logger.info("Consumer loop started")

        while self._running:
            try:
                # Check if at capacity
                if len(self._claimed_jobs) >= self.config.max_concurrent_jobs:
                    await asyncio.sleep(self.config.poll_interval)
                    continue

                # Claim next job
                job = await self.claim_job()

                if job:
                    # Execute job in background
                    asyncio.create_task(self._execute_job(job, job_handler))
                else:
                    # No jobs available, wait before polling again
                    await asyncio.sleep(self.config.poll_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Consumer loop error: {e}")
                await asyncio.sleep(self.config.poll_interval)

        logger.info("Consumer loop stopped")

    async def claim_job(self) -> Optional[JobModel]:
        """
        Claim next available job from queue.

        Returns:
            JobModel if job claimed, None if queue empty
        """
        if not self._running or not self.queue_manager or not self.pool:
            return None

        try:
            # Claim job using PgQueuer with visibility timeout
            async with self.pool.acquire() as conn:
                query = """
                    UPDATE pgqueuer.jobs
                    SET status = 'claimed',
                        claimed_at = NOW(),
                        claimed_by = $1
                    WHERE id = (
                        SELECT id
                        FROM pgqueuer.jobs
                        WHERE queue_name = $2
                        AND status = 'pending'
                        ORDER BY priority DESC, created_at ASC
                        LIMIT 1
                        FOR UPDATE SKIP LOCKED
                    )
                    RETURNING payload
                """

                payload = await conn.fetchval(
                    query,
                    self.robot_id,
                    self.config.queue_name,
                )

                if not payload:
                    return None

                # Create JobModel from payload
                job = JobModel.from_pgqueuer_payload(payload)
                job.mark_claimed(self.robot_id)

                # Track claimed job
                self._claimed_jobs[job.job_id] = job

                logger.info(f"Job claimed: {job.job_id} (priority={job.priority})")

                return job

        except Exception as e:
            logger.exception(f"Failed to claim job: {e}")
            return None

    async def _execute_job(
        self,
        job: JobModel,
        job_handler: Callable[[JobModel], Awaitable[bool]],
    ) -> None:
        """
        Execute a claimed job.

        Args:
            job: Job to execute
            job_handler: Handler function
        """
        try:
            # Mark as running
            job.mark_running()
            logger.info(f"Job started: {job.job_id}")

            # Execute job
            success = await job_handler(job)

            if success:
                await self.complete_job(job.job_id)
            else:
                await self.fail_job(job.job_id, "Job handler returned False")

        except Exception as e:
            logger.exception(f"Job execution error: {job.job_id}")
            await self.fail_job(job.job_id, str(e))

        finally:
            # Remove from claimed jobs
            self._claimed_jobs.pop(job.job_id, None)

    async def complete_job(self, job_id: str) -> None:
        """
        Mark job as successfully completed.

        Args:
            job_id: Job identifier
        """
        if not self.pool:
            return

        try:
            query = """
                UPDATE pgqueuer.jobs
                SET status = 'completed',
                    completed_at = NOW()
                WHERE payload->>'job_id' = $1
            """

            async with self.pool.acquire() as conn:
                await conn.execute(query, job_id)

            logger.info(f"Job completed: {job_id}")

        except Exception as e:
            logger.exception(f"Failed to complete job {job_id}: {e}")

    async def fail_job(self, job_id: str, error: str) -> None:
        """
        Mark job as failed.

        Args:
            job_id: Job identifier
            error: Error message
        """
        if not self.pool:
            return

        try:
            job = self._claimed_jobs.get(job_id)
            if not job:
                logger.warning(f"Job not in claimed jobs: {job_id}")
                return

            job.mark_failed(error)

            # Check if should retry or move to DLQ
            if job.should_retry():
                # Reset to pending for retry
                query = """
                    UPDATE pgqueuer.jobs
                    SET status = 'pending',
                        retry_count = retry_count + 1,
                        last_error = $2
                    WHERE payload->>'job_id' = $1
                """
                status_msg = f"retry {job.retry_count}/{job.max_retries}"
            else:
                # Move to DLQ
                query = """
                    UPDATE pgqueuer.jobs
                    SET status = 'failed',
                        completed_at = NOW(),
                        error_message = $2
                    WHERE payload->>'job_id' = $1
                """
                status_msg = "moved to DLQ"

            async with self.pool.acquire() as conn:
                await conn.execute(query, job_id, error)

            logger.warning(f"Job failed: {job_id} ({status_msg})")

        except Exception as e:
            logger.exception(f"Failed to fail job {job_id}: {e}")

    async def release_job(self, job_id: str) -> None:
        """
        Release a claimed job back to queue.

        Used when consumer stops or job needs to be re-queued.

        Args:
            job_id: Job identifier
        """
        if not self.pool:
            return

        try:
            query = """
                UPDATE pgqueuer.jobs
                SET status = 'pending',
                    claimed_at = NULL,
                    claimed_by = NULL
                WHERE payload->>'job_id' = $1
                AND status = 'claimed'
            """

            async with self.pool.acquire() as conn:
                await conn.execute(query, job_id)

            logger.info(f"Job released: {job_id}")

        except Exception as e:
            logger.exception(f"Failed to release job {job_id}: {e}")

    async def _heartbeat_loop(self) -> None:
        """
        Heartbeat loop to extend visibility timeout for claimed jobs.
        """
        logger.info("Heartbeat loop started")

        while self._running:
            try:
                await asyncio.sleep(self.config.visibility_timeout / 2)

                if not self._claimed_jobs or not self.pool:
                    continue

                # Extend visibility timeout for claimed jobs
                job_ids = list(self._claimed_jobs.keys())

                query = """
                    UPDATE pgqueuer.jobs
                    SET claimed_at = NOW()
                    WHERE payload->>'job_id' = ANY($1)
                    AND status IN ('claimed', 'running')
                """

                async with self.pool.acquire() as conn:
                    await conn.execute(query, job_ids)

                logger.debug(f"Heartbeat sent for {len(job_ids)} jobs")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Heartbeat error: {e}")

        logger.info("Heartbeat loop stopped")

    async def health_check(self) -> bool:
        """
        Check if consumer is healthy.

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
            logger.error(f"Consumer health check failed: {e}")
            return False

    def get_claimed_job_count(self) -> int:
        """
        Get number of currently claimed jobs.

        Returns:
            Number of claimed jobs
        """
        return len(self._claimed_jobs)

    async def __aenter__(self):
        """Async context manager entry."""
        raise RuntimeError("Use start() method instead of async context manager")

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
