"""
In-memory job queue fallback for development without PostgreSQL.

Provides a simple asyncio.Queue-based implementation of the job queue
interface. Jobs are stored in memory only and will be lost on restart.

Use when:
- DB_ENABLED=false
- USE_MEMORY_QUEUE=true
- PostgreSQL unavailable
- Local development/testing

Production deployments should use PgQueuer for persistence and
distributed coordination.
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from loguru import logger


class JobStatus(Enum):
    """Job status enumeration."""

    PENDING = "pending"
    QUEUED = "queued"
    CLAIMED = "claimed"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class MemoryJob:
    """
    In-memory job representation.

    Mimics PgQueuer's Job interface for compatibility.
    """

    job_id: str
    workflow_id: str
    workflow_json: dict[str, Any]
    priority: int = 10
    status: JobStatus = JobStatus.PENDING
    robot_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    claimed_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    retry_count: int = 0
    max_retries: int = 3
    visibility_timeout: int = 30  # seconds
    execution_mode: str = "lan"  # lan or internet
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert job to dictionary."""
        return {
            "job_id": self.job_id,
            "workflow_id": self.workflow_id,
            "workflow_json": self.workflow_json,
            "priority": self.priority,
            "status": self.status.value,
            "robot_id": self.robot_id,
            "created_at": self.created_at.isoformat(),
            "claimed_at": self.claimed_at.isoformat() if self.claimed_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "execution_mode": self.execution_mode,
            "metadata": self.metadata,
        }


class MemoryQueue:
    """
    In-memory job queue implementation.

    Thread-safe, async-compatible queue for local development.
    Stores jobs in memory with priority support and visibility timeout.

    NOT suitable for production:
    - Jobs lost on restart
    - No distributed coordination
    - No persistence
    - Single-process only

    For production, use PgQueuer.
    """

    def __init__(self, visibility_timeout: int = 30):
        """
        Initialize memory queue.

        Args:
            visibility_timeout: Seconds before claimed job returns to queue
        """
        self._jobs: dict[str, MemoryJob] = {}  # job_id -> Job
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._claimed_jobs: dict[str, MemoryJob] = {}  # job_id -> Job
        self._lock = asyncio.Lock()
        self._visibility_timeout = visibility_timeout
        self._running = False
        self._cleanup_task: asyncio.Task | None = None

        logger.info("MemoryQueue initialized (in-memory fallback active)")

    async def start(self) -> None:
        """Start the queue and cleanup task."""
        if self._running:
            return

        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_claims())
        logger.info("MemoryQueue started with visibility timeout {}", self._visibility_timeout)

    async def stop(self) -> None:
        """Stop the queue and cleanup task."""
        if not self._running:
            return

        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        logger.info("MemoryQueue stopped")

    async def enqueue(
        self,
        workflow_id: str,
        workflow_json: dict[str, Any],
        priority: int = 10,
        execution_mode: str = "lan",
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Add job to queue.

        Args:
            workflow_id: Workflow identifier
            workflow_json: Workflow definition
            priority: Job priority (0=highest, 20=lowest)
            execution_mode: "lan" or "internet"
            metadata: Additional job metadata

        Returns:
            job_id: Unique job identifier
        """
        async with self._lock:
            job_id = str(uuid.uuid4())
            job = MemoryJob(
                job_id=job_id,
                workflow_id=workflow_id,
                workflow_json=workflow_json,
                priority=priority,
                status=JobStatus.QUEUED,
                execution_mode=execution_mode,
                metadata=metadata or {},
            )

            self._jobs[job_id] = job
            # PriorityQueue: (priority, insertion_order, job_id)
            await self._queue.put((priority, datetime.now(UTC), job_id))

            logger.info(
                "Job enqueued: {} (workflow={}, priority={}, mode={})",
                job_id,
                workflow_id,
                priority,
                execution_mode,
            )

            return job_id

    async def claim(self, robot_id: str, execution_mode: str | None = None) -> MemoryJob | None:
        """
        Claim next available job from queue.

        Args:
            robot_id: Robot identifier claiming the job
            execution_mode: Filter by execution mode (None = any)

        Returns:
            MemoryJob if available, None otherwise
        """
        async with self._lock:
            # Try to find matching job in queue
            temp_items = []
            claimed_job = None

            try:
                while not self._queue.empty():
                    priority, timestamp, job_id = await self._queue.get()

                    job = self._jobs.get(job_id)
                    if not job:
                        continue  # Job was deleted

                    # Check execution mode filter
                    if execution_mode and job.execution_mode != execution_mode:
                        temp_items.append((priority, timestamp, job_id))
                        continue

                    # Found matching job - claim it
                    job.status = JobStatus.CLAIMED
                    job.robot_id = robot_id
                    job.claimed_at = datetime.now(UTC)

                    self._claimed_jobs[job_id] = job
                    claimed_job = job

                    logger.info(
                        "Job claimed: {} by robot {} (workflow={}, mode={})",
                        job_id,
                        robot_id,
                        job.workflow_id,
                        job.execution_mode,
                    )
                    break

            finally:
                # Return non-matching jobs to queue
                for item in temp_items:
                    await self._queue.put(item)

            return claimed_job

    async def update_status(
        self,
        job_id: str,
        status: JobStatus,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> bool:
        """
        Update job status.

        Args:
            job_id: Job identifier
            status: New status
            result: Job result (if completed)
            error: Error message (if failed)

        Returns:
            True if updated, False if job not found
        """
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                logger.warning("Cannot update status - job not found: {}", job_id)
                return False

            old_status = job.status
            job.status = status

            if status == JobStatus.RUNNING and not job.started_at:
                job.started_at = datetime.now(UTC)

            if status in (
                JobStatus.COMPLETED,
                JobStatus.FAILED,
                JobStatus.CANCELLED,
                JobStatus.TIMEOUT,
            ):
                job.completed_at = datetime.now(UTC)
                # Remove from claimed jobs
                self._claimed_jobs.pop(job_id, None)

            if result:
                job.result = result

            if error:
                job.error = error

            logger.info(
                "Job status updated: {} {} -> {} (workflow={})",
                job_id,
                old_status.value,
                status.value,
                job.workflow_id,
            )

            return True

    async def extend_claim(self, job_id: str) -> bool:
        """
        Extend visibility timeout for claimed job (heartbeat).

        Args:
            job_id: Job identifier

        Returns:
            True if extended, False if job not found or not claimed
        """
        async with self._lock:
            job = self._claimed_jobs.get(job_id)
            if not job:
                return False

            job.claimed_at = datetime.now(UTC)
            logger.debug("Job claim extended: {}", job_id)
            return True

    async def get_job(self, job_id: str) -> MemoryJob | None:
        """
        Get job by ID.

        Args:
            job_id: Job identifier

        Returns:
            MemoryJob if found, None otherwise
        """
        async with self._lock:
            return self._jobs.get(job_id)

    async def get_jobs_by_status(self, status: JobStatus, limit: int = 100) -> list[MemoryJob]:
        """
        Get jobs by status.

        Args:
            status: Job status filter
            limit: Maximum number of jobs to return

        Returns:
            List of matching jobs
        """
        async with self._lock:
            jobs = [job for job in self._jobs.values() if job.status == status]
            jobs.sort(key=lambda j: j.created_at, reverse=True)
            return jobs[:limit]

    async def get_jobs_by_robot(self, robot_id: str, limit: int = 100) -> list[MemoryJob]:
        """
        Get jobs assigned to robot.

        Args:
            robot_id: Robot identifier
            limit: Maximum number of jobs to return

        Returns:
            List of matching jobs
        """
        async with self._lock:
            jobs = [job for job in self._jobs.values() if job.robot_id == robot_id]
            jobs.sort(key=lambda j: j.created_at, reverse=True)
            return jobs[:limit]

    async def get_queue_depth(self, execution_mode: str | None = None) -> int:
        """
        Get number of queued jobs.

        Args:
            execution_mode: Filter by execution mode (None = all)

        Returns:
            Number of jobs in queue
        """
        async with self._lock:
            if execution_mode:
                return sum(
                    1
                    for job in self._jobs.values()
                    if job.status == JobStatus.QUEUED and job.execution_mode == execution_mode
                )
            else:
                return sum(1 for job in self._jobs.values() if job.status == JobStatus.QUEUED)

    async def _cleanup_expired_claims(self) -> None:
        """Background task to return expired claims to queue."""
        while self._running:
            try:
                await asyncio.sleep(5)  # Check every 5 seconds

                async with self._lock:
                    now = datetime.now(UTC)
                    expired_jobs = []

                    for job_id, job in list(self._claimed_jobs.items()):
                        if not job.claimed_at:
                            continue

                        elapsed = (now - job.claimed_at).total_seconds()
                        if elapsed > self._visibility_timeout:
                            expired_jobs.append(job)

                    # Return expired jobs to queue
                    for job in expired_jobs:
                        job.status = JobStatus.QUEUED
                        job.robot_id = None
                        job.claimed_at = None
                        self._claimed_jobs.pop(job.job_id, None)

                        await self._queue.put((job.priority, datetime.now(UTC), job.job_id))

                        logger.warning(
                            "Job claim expired, returned to queue: {} (workflow={})",
                            job.job_id,
                            job.workflow_id,
                        )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in cleanup task: {}", e)


# Global singleton instance
_memory_queue: MemoryQueue | None = None


def get_memory_queue(visibility_timeout: int = 30) -> MemoryQueue:
    """
    Get or create global MemoryQueue instance.

    Args:
        visibility_timeout: Seconds before claimed job returns to queue

    Returns:
        MemoryQueue singleton
    """
    global _memory_queue

    if _memory_queue is None:
        _memory_queue = MemoryQueue(visibility_timeout=visibility_timeout)

    return _memory_queue


async def initialize_memory_queue() -> MemoryQueue:
    """
    Initialize and start the memory queue.

    Returns:
        Started MemoryQueue instance
    """
    queue = get_memory_queue()
    await queue.start()
    return queue


async def shutdown_memory_queue() -> None:
    """Shutdown the memory queue."""
    global _memory_queue

    if _memory_queue:
        await _memory_queue.stop()
        _memory_queue = None
