"""
CasareRPA Infrastructure Layer - PgQueuer Consumer

Implements a PostgreSQL-based distributed queue consumer for robot job claiming.
Uses SKIP LOCKED for concurrent, non-blocking job acquisition.

Features:
- Job claiming with SKIP LOCKED (no blocking, high concurrency)
- Visibility timeout management (jobs return to queue if not completed)
- Heartbeat/lease extension for long-running jobs
- Job completion/failure reporting
- Batch claiming support for throughput optimization
- Automatic reconnection with exponential backoff

Architecture:
- Robots poll for jobs via claim_job() or claim_batch()
- Jobs become invisible for visibility_timeout_seconds after claiming
- Heartbeats extend the lease to prevent timeout during long execution
- Jobs are marked complete/failed when finished

Database Schema (expected):
    CREATE TABLE job_queue (
        id UUID PRIMARY KEY,
        workflow_id VARCHAR(255) NOT NULL,
        workflow_name VARCHAR(255) NOT NULL,
        workflow_json TEXT NOT NULL,
        priority INTEGER DEFAULT 1,
        status VARCHAR(50) DEFAULT 'pending',
        robot_id VARCHAR(255),
        environment VARCHAR(100) DEFAULT 'default',
        visible_after TIMESTAMPTZ DEFAULT NOW(),
        created_at TIMESTAMPTZ DEFAULT NOW(),
        started_at TIMESTAMPTZ,
        completed_at TIMESTAMPTZ,
        error_message TEXT,
        result JSONB,
        retry_count INTEGER DEFAULT 0,
        max_retries INTEGER DEFAULT 3,
        variables JSONB DEFAULT '{}'
    );

    CREATE INDEX idx_job_queue_claiming ON job_queue (status, visible_after, priority DESC)
        WHERE status = 'pending';
"""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import uuid

from loguru import logger

try:
    import asyncpg
    from asyncpg import Pool
    from asyncpg.exceptions import PostgresError

    HAS_ASYNCPG = True
except ImportError:
    HAS_ASYNCPG = False
    asyncpg = None
    Pool = None
    PostgresError = Exception


class ConnectionState(Enum):
    """Consumer connection state."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


@dataclass
class ClaimedJob:
    """
    Represents a job claimed by a robot consumer.

    Contains all data needed to execute the workflow and report back.
    """

    job_id: str
    workflow_id: str
    workflow_name: str
    workflow_json: str
    priority: int
    environment: str
    variables: Dict[str, Any]
    created_at: datetime
    claimed_at: datetime
    retry_count: int
    max_retries: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "job_id": self.job_id,
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "workflow_json": self.workflow_json,
            "priority": self.priority,
            "environment": self.environment,
            "variables": self.variables,
            "created_at": self.created_at.isoformat(),
            "claimed_at": self.claimed_at.isoformat(),
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
        }


@dataclass
class ConsumerConfig:
    """Configuration for PgQueuerConsumer."""

    postgres_url: str
    robot_id: str
    environment: str = "default"
    batch_size: int = 1
    visibility_timeout_seconds: int = 30
    heartbeat_interval_seconds: int = 10
    max_reconnect_attempts: int = 10
    reconnect_base_delay_seconds: float = 1.0
    reconnect_max_delay_seconds: float = 60.0
    pool_min_size: int = 2
    pool_max_size: int = 10
    claim_poll_interval_seconds: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert config to dictionary with credential masking.

        SECURITY: Masks postgres_url to prevent credential leakage in logs.
        """
        from casare_rpa.infrastructure.security.validators import sanitize_log_value

        return {
            "postgres_url": sanitize_log_value(self.postgres_url),
            "robot_id": self.robot_id,
            "environment": self.environment,
            "batch_size": self.batch_size,
            "visibility_timeout_seconds": self.visibility_timeout_seconds,
            "heartbeat_interval_seconds": self.heartbeat_interval_seconds,
            "max_reconnect_attempts": self.max_reconnect_attempts,
            "reconnect_base_delay_seconds": self.reconnect_base_delay_seconds,
            "reconnect_max_delay_seconds": self.reconnect_max_delay_seconds,
            "pool_min_size": self.pool_min_size,
            "pool_max_size": self.pool_max_size,
            "claim_poll_interval_seconds": self.claim_poll_interval_seconds,
        }


class PgQueuerConsumer:
    """
    PostgreSQL-based distributed queue consumer for robot job claiming.

    Uses SKIP LOCKED for high-concurrency, non-blocking job acquisition.
    Supports visibility timeout, heartbeats, and automatic reconnection.

    Usage:
        config = ConsumerConfig(
            postgres_url="postgresql://user:pass@host:5432/db",
            robot_id="robot-001",
            environment="production"
        )
        consumer = PgQueuerConsumer(config)

        await consumer.start()

        # Claim and process jobs
        job = await consumer.claim_job()
        if job:
            try:
                result = await execute_workflow(job)
                await consumer.complete_job(job.job_id, result)
            except Exception as e:
                await consumer.fail_job(job.job_id, str(e))

        await consumer.stop()
    """

    # SQL queries as class constants for clarity and maintainability
    # SECURITY: Atomic UPDATE with subquery to prevent TOCTOU race condition
    # The FOR UPDATE SKIP LOCKED is inside the UPDATE's WHERE clause subquery,
    # ensuring no time gap between SELECT and UPDATE
    SQL_CLAIM_JOB = """
        UPDATE job_queue
        SET status = 'running',
            robot_id = $3,
            started_at = NOW(),
            visible_after = NOW() + INTERVAL '1 second' * $4
        WHERE id IN (
            SELECT id
            FROM job_queue
            WHERE status = 'pending'
              AND visible_after <= NOW()
              AND (environment = $1 OR environment = 'default' OR $1 = 'default')
            ORDER BY priority DESC, created_at ASC
            LIMIT $2
            FOR UPDATE SKIP LOCKED
        )
        RETURNING id,
                  workflow_id,
                  workflow_name,
                  workflow_json,
                  priority,
                  environment,
                  variables,
                  created_at,
                  retry_count,
                  max_retries;
    """

    SQL_EXTEND_LEASE = """
        UPDATE job_queue
        SET visible_after = NOW() + INTERVAL '1 second' * $2
        WHERE id = $1
          AND status = 'running'
          AND robot_id = $3
        RETURNING id;
    """

    SQL_COMPLETE_JOB = """
        UPDATE job_queue
        SET status = 'completed',
            completed_at = NOW(),
            result = $2::jsonb
        WHERE id = $1
          AND status = 'running'
          AND robot_id = $3
        RETURNING id;
    """

    SQL_FAIL_JOB = """
        UPDATE job_queue
        SET status = CASE
                WHEN retry_count < max_retries THEN 'pending'
                ELSE 'failed'
            END,
            error_message = $2,
            retry_count = retry_count + 1,
            robot_id = CASE
                WHEN retry_count < max_retries THEN NULL
                ELSE robot_id
            END,
            visible_after = CASE
                WHEN retry_count < max_retries THEN NOW() + INTERVAL '1 second' * (retry_count + 1) * 5
                ELSE visible_after
            END,
            completed_at = CASE
                WHEN retry_count >= max_retries THEN NOW()
                ELSE NULL
            END
        WHERE id = $1
          AND status = 'running'
          AND robot_id = $3
        RETURNING id, status, retry_count;
    """

    SQL_RELEASE_JOB = """
        UPDATE job_queue
        SET status = 'pending',
            robot_id = NULL,
            started_at = NULL,
            visible_after = NOW()
        WHERE id = $1
          AND status = 'running'
          AND robot_id = $2
        RETURNING id;
    """

    SQL_REQUEUE_TIMED_OUT = """
        UPDATE job_queue
        SET status = CASE
                WHEN retry_count < max_retries THEN 'pending'
                ELSE 'failed'
            END,
            robot_id = NULL,
            error_message = COALESCE(error_message, '') || ' [Visibility timeout exceeded]',
            retry_count = retry_count + 1,
            visible_after = NOW()
        WHERE status = 'running'
          AND visible_after < NOW()
          AND robot_id = $1
        RETURNING id, status;
    """

    SQL_GET_JOB_STATUS = """
        SELECT id, status, robot_id, visible_after
        FROM job_queue
        WHERE id = $1;
    """

    def __init__(self, config: ConsumerConfig) -> None:
        """
        Initialize the consumer.

        Args:
            config: Consumer configuration

        Raises:
            ImportError: If asyncpg is not installed
            ValidationError: If robot_id is invalid
        """
        if not HAS_ASYNCPG:
            raise ImportError(
                "asyncpg is required for PgQueuerConsumer. "
                "Install with: pip install asyncpg"
            )

        # SECURITY: Validate robot_id to prevent SQL injection and impersonation attacks
        from casare_rpa.infrastructure.security.validators import validate_robot_id

        validate_robot_id(config.robot_id)

        self._config = config
        self._pool: Optional[Pool] = None
        self._state = ConnectionState.DISCONNECTED
        self._running = False
        self._reconnect_attempts = 0
        self._active_jobs: Dict[str, ClaimedJob] = {}
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._state_callbacks: List[Callable[[ConnectionState], None]] = []
        self._lock = asyncio.Lock()

        logger.info(
            f"PgQueuerConsumer initialized for robot '{config.robot_id}' "
            f"in environment '{config.environment}'"
        )

    @property
    def state(self) -> ConnectionState:
        """Get current connection state."""
        return self._state

    @property
    def robot_id(self) -> str:
        """Get robot ID."""
        return self._config.robot_id

    @property
    def active_job_count(self) -> int:
        """Get count of currently active (claimed) jobs."""
        return len(self._active_jobs)

    @property
    def is_connected(self) -> bool:
        """Check if consumer is connected and ready."""
        return self._state == ConnectionState.CONNECTED and self._pool is not None

    def add_state_callback(self, callback: Callable[[ConnectionState], None]) -> None:
        """
        Add a callback for connection state changes.

        Args:
            callback: Function to call when state changes
        """
        self._state_callbacks.append(callback)

    def remove_state_callback(
        self, callback: Callable[[ConnectionState], None]
    ) -> None:
        """
        Remove a state change callback.

        Args:
            callback: Callback to remove
        """
        if callback in self._state_callbacks:
            self._state_callbacks.remove(callback)

    def _set_state(self, new_state: ConnectionState) -> None:
        """Update state and notify callbacks."""
        if self._state != new_state:
            old_state = self._state
            self._state = new_state
            logger.debug(f"Consumer state: {old_state.value} -> {new_state.value}")
            for callback in self._state_callbacks:
                try:
                    callback(new_state)
                except Exception as e:
                    logger.warning(f"State callback error: {e}")

    async def start(self) -> bool:
        """
        Start the consumer and establish database connection.

        Returns:
            True if started successfully, False otherwise
        """
        if self._running:
            logger.warning("Consumer already running")
            return True

        self._running = True
        success = await self._connect()

        if success:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            logger.info(f"PgQueuerConsumer started for robot '{self._config.robot_id}'")

        return success

    async def stop(self) -> None:
        """
        Stop the consumer gracefully.

        Releases any active jobs back to the queue and closes connections.
        """
        logger.info("Stopping PgQueuerConsumer...")
        self._running = False

        # Cancel heartbeat task
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None

        # Release active jobs back to queue
        await self._release_all_active_jobs()

        # Close pool
        if self._pool:
            try:
                await self._pool.close()
            except Exception as e:
                logger.warning(f"Error closing connection pool: {e}")
            self._pool = None

        self._set_state(ConnectionState.DISCONNECTED)
        logger.info("PgQueuerConsumer stopped")

    async def _connect(self) -> bool:
        """
        Establish database connection with retry logic.

        Returns:
            True if connected successfully
        """
        self._set_state(ConnectionState.CONNECTING)

        try:
            self._pool = await asyncpg.create_pool(
                self._config.postgres_url,
                min_size=self._config.pool_min_size,
                max_size=self._config.pool_max_size,
                command_timeout=30,
            )

            # Test connection
            async with self._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")

            self._set_state(ConnectionState.CONNECTED)
            self._reconnect_attempts = 0
            logger.info("Database connection established")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            self._set_state(ConnectionState.FAILED)
            return False

    async def _reconnect(self) -> bool:
        """
        Attempt to reconnect with exponential backoff.

        Returns:
            True if reconnected successfully
        """
        if not self._running:
            return False

        self._set_state(ConnectionState.RECONNECTING)
        self._reconnect_attempts += 1

        if self._reconnect_attempts > self._config.max_reconnect_attempts:
            logger.error(
                f"Max reconnect attempts ({self._config.max_reconnect_attempts}) exceeded"
            )
            self._set_state(ConnectionState.FAILED)
            return False

        # Exponential backoff with jitter
        delay = min(
            self._config.reconnect_base_delay_seconds
            * (2 ** (self._reconnect_attempts - 1)),
            self._config.reconnect_max_delay_seconds,
        )
        # Add jitter (10-30% of delay)
        jitter = delay * random.uniform(0.1, 0.3)
        delay += jitter

        logger.info(
            f"Reconnect attempt {self._reconnect_attempts}/{self._config.max_reconnect_attempts} "
            f"in {delay:.1f}s"
        )
        await asyncio.sleep(delay)

        # Close existing pool if any
        if self._pool:
            try:
                await self._pool.close()
            except Exception:
                pass
            self._pool = None

        return await self._connect()

    async def _ensure_connection(self) -> bool:
        """
        Ensure we have a valid connection, reconnecting if needed.

        Returns:
            True if connection is available
        """
        if self.is_connected:
            return True

        if self._state in (ConnectionState.CONNECTING, ConnectionState.RECONNECTING):
            # Already trying to connect
            await asyncio.sleep(0.5)
            return self.is_connected

        return await self._reconnect()

    async def _execute_with_retry(
        self,
        query: str,
        *args: Any,
        max_retries: int = 3,
    ) -> Any:
        """
        Execute a query with automatic retry on connection failure.

        Args:
            query: SQL query to execute
            *args: Query arguments
            max_retries: Maximum retry attempts

        Returns:
            Query result

        Raises:
            PostgresError: If query fails after all retries
            ConnectionError: If connection cannot be established
        """
        last_error: Optional[Exception] = None

        for attempt in range(max_retries):
            if not await self._ensure_connection():
                raise ConnectionError("Unable to establish database connection")

            try:
                async with self._pool.acquire() as conn:
                    return await conn.fetch(query, *args)
            except asyncpg.exceptions.ConnectionDoesNotExistError:
                logger.warning(
                    f"Connection lost, attempting reconnect (attempt {attempt + 1})"
                )
                last_error = ConnectionError("Connection lost")
                await self._reconnect()
            except asyncpg.exceptions.InterfaceError as e:
                logger.warning(f"Interface error: {e}, attempting reconnect")
                last_error = e
                await self._reconnect()
            except PostgresError:
                # Non-connection errors should not trigger reconnect
                raise

        raise last_error or ConnectionError("Query failed after retries")

    async def claim_job(self) -> Optional[ClaimedJob]:
        """
        Claim a single job from the queue.

        Uses SKIP LOCKED for non-blocking concurrent access.

        Returns:
            ClaimedJob if one was claimed, None if queue is empty

        Raises:
            ConnectionError: If database connection fails
        """
        jobs = await self.claim_batch(limit=1)
        return jobs[0] if jobs else None

    async def claim_batch(self, limit: Optional[int] = None) -> List[ClaimedJob]:
        """
        Claim multiple jobs from the queue.

        Args:
            limit: Maximum jobs to claim (defaults to config.batch_size)

        Returns:
            List of claimed jobs (may be empty)

        Raises:
            ConnectionError: If database connection fails
        """
        batch_size = limit or self._config.batch_size

        try:
            rows = await self._execute_with_retry(
                self.SQL_CLAIM_JOB,
                self._config.environment,
                batch_size,
                self._config.robot_id,
                self._config.visibility_timeout_seconds,
            )
        except Exception as e:
            logger.error(f"Failed to claim jobs: {e}")
            raise

        claimed_jobs: List[ClaimedJob] = []
        now = datetime.now(timezone.utc)

        for row in rows:
            job = ClaimedJob(
                job_id=str(row["id"]),
                workflow_id=row["workflow_id"],
                workflow_name=row["workflow_name"],
                workflow_json=row["workflow_json"],
                priority=row["priority"],
                environment=row["environment"],
                variables=row["variables"] or {},
                created_at=row["created_at"],
                claimed_at=now,
                retry_count=row["retry_count"],
                max_retries=row["max_retries"],
            )
            claimed_jobs.append(job)

            # Track active job for heartbeat
            async with self._lock:
                self._active_jobs[job.job_id] = job

            logger.info(
                f"Claimed job {job.job_id[:8]}... workflow='{job.workflow_name}' "
                f"priority={job.priority} retry={job.retry_count}"
            )

        return claimed_jobs

    async def extend_lease(
        self,
        job_id: str,
        extension_seconds: Optional[int] = None,
    ) -> bool:
        """
        Extend the visibility timeout (lease) for a job.

        Should be called periodically during long-running job execution.

        Args:
            job_id: Job ID to extend
            extension_seconds: Seconds to extend (defaults to visibility_timeout_seconds)

        Returns:
            True if lease was extended, False if job not found or not owned

        Raises:
            ConnectionError: If database connection fails
        """
        extension = extension_seconds or self._config.visibility_timeout_seconds

        try:
            rows = await self._execute_with_retry(
                self.SQL_EXTEND_LEASE,
                uuid.UUID(job_id),
                extension,
                self._config.robot_id,
            )

            success = len(rows) > 0
            if success:
                logger.debug(f"Extended lease for job {job_id[:8]}... by {extension}s")
            else:
                logger.warning(
                    f"Failed to extend lease for job {job_id[:8]}... "
                    "(job not found or not owned by this robot)"
                )
            return success

        except Exception as e:
            logger.error(f"Failed to extend lease for job {job_id[:8]}...: {e}")
            raise

    async def complete_job(
        self,
        job_id: str,
        result: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Mark a job as completed.

        Args:
            job_id: Job ID to complete
            result: Optional result data to store

        Returns:
            True if job was completed, False if not found or not owned

        Raises:
            ConnectionError: If database connection fails
        """
        import orjson

        result_json = orjson.dumps(result or {}).decode("utf-8")

        try:
            rows = await self._execute_with_retry(
                self.SQL_COMPLETE_JOB,
                uuid.UUID(job_id),
                result_json,
                self._config.robot_id,
            )

            success = len(rows) > 0

            async with self._lock:
                self._active_jobs.pop(job_id, None)

            if success:
                logger.info(f"Completed job {job_id[:8]}...")
            else:
                logger.warning(
                    f"Failed to complete job {job_id[:8]}... "
                    "(job not found or not owned by this robot)"
                )

            return success

        except Exception as e:
            logger.error(f"Failed to complete job {job_id[:8]}...: {e}")
            raise

    async def fail_job(
        self,
        job_id: str,
        error_message: str,
    ) -> tuple[bool, bool]:
        """
        Mark a job as failed.

        If retries remain, the job is re-queued with exponential backoff.
        Otherwise, it's marked as permanently failed.

        Args:
            job_id: Job ID to fail
            error_message: Error description

        Returns:
            Tuple of (success, will_retry) - success indicates update worked,
            will_retry indicates if job was re-queued for retry

        Raises:
            ConnectionError: If database connection fails
        """
        try:
            rows = await self._execute_with_retry(
                self.SQL_FAIL_JOB,
                uuid.UUID(job_id),
                error_message[:4000],  # Truncate long messages
                self._config.robot_id,
            )

            async with self._lock:
                self._active_jobs.pop(job_id, None)

            if not rows:
                logger.warning(
                    f"Failed to update job {job_id[:8]}... "
                    "(job not found or not owned by this robot)"
                )
                return False, False

            row = rows[0]
            new_status = row["status"]
            retry_count = row["retry_count"]
            will_retry = new_status == "pending"

            if will_retry:
                logger.info(
                    f"Job {job_id[:8]}... failed, re-queued for retry "
                    f"({retry_count} retries): {error_message[:100]}"
                )
            else:
                logger.warning(
                    f"Job {job_id[:8]}... permanently failed after "
                    f"{retry_count} retries: {error_message[:100]}"
                )

            return True, will_retry

        except Exception as e:
            logger.error(f"Failed to mark job {job_id[:8]}... as failed: {e}")
            raise

    async def release_job(self, job_id: str) -> bool:
        """
        Release a job back to the queue without completing or failing it.

        Useful for graceful shutdown or when a job should be retried immediately.

        Args:
            job_id: Job ID to release

        Returns:
            True if job was released, False if not found or not owned

        Raises:
            ConnectionError: If database connection fails
        """
        try:
            rows = await self._execute_with_retry(
                self.SQL_RELEASE_JOB,
                uuid.UUID(job_id),
                self._config.robot_id,
            )

            async with self._lock:
                self._active_jobs.pop(job_id, None)

            success = len(rows) > 0
            if success:
                logger.info(f"Released job {job_id[:8]}... back to queue")
            else:
                logger.warning(
                    f"Failed to release job {job_id[:8]}... "
                    "(job not found or not owned by this robot)"
                )

            return success

        except Exception as e:
            logger.error(f"Failed to release job {job_id[:8]}...: {e}")
            raise

    async def _release_all_active_jobs(self) -> None:
        """Release all currently active jobs back to the queue."""
        async with self._lock:
            job_ids = list(self._active_jobs.keys())

        for job_id in job_ids:
            try:
                await self.release_job(job_id)
            except Exception as e:
                logger.warning(
                    f"Failed to release job {job_id[:8]}... during shutdown: {e}"
                )

    async def requeue_timed_out_jobs(self) -> int:
        """
        Requeue jobs that exceeded their visibility timeout.

        This is typically called by a background task to recover jobs
        from crashed robots.

        Returns:
            Number of jobs requeued

        Raises:
            ConnectionError: If database connection fails
        """
        try:
            rows = await self._execute_with_retry(
                self.SQL_REQUEUE_TIMED_OUT,
                self._config.robot_id,
            )

            count = len(rows)
            if count > 0:
                logger.info(f"Requeued {count} timed-out jobs")

            return count

        except Exception as e:
            logger.error(f"Failed to requeue timed-out jobs: {e}")
            raise

    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current status of a job.

        Args:
            job_id: Job ID to check

        Returns:
            Dict with status info, or None if not found
        """
        try:
            rows = await self._execute_with_retry(
                self.SQL_GET_JOB_STATUS,
                uuid.UUID(job_id),
            )

            if not rows:
                return None

            row = rows[0]
            return {
                "id": str(row["id"]),
                "status": row["status"],
                "robot_id": row["robot_id"],
                "visible_after": row["visible_after"].isoformat()
                if row["visible_after"]
                else None,
            }

        except Exception as e:
            logger.error(f"Failed to get job status: {e}")
            return None

    async def _heartbeat_loop(self) -> None:
        """
        Background task to extend leases for all active jobs.

        Runs periodically to prevent visibility timeout during long executions.
        """
        logger.debug("Heartbeat loop started")

        while self._running:
            try:
                await asyncio.sleep(self._config.heartbeat_interval_seconds)

                if not self._running:
                    break

                async with self._lock:
                    job_ids = list(self._active_jobs.keys())

                for job_id in job_ids:
                    try:
                        await self.extend_lease(job_id)
                    except Exception as e:
                        logger.warning(f"Heartbeat failed for job {job_id[:8]}...: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat loop error: {e}")
                await asyncio.sleep(1)

        logger.debug("Heartbeat loop stopped")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get consumer statistics.

        Returns:
            Dict with consumer stats
        """
        return {
            "robot_id": self._config.robot_id,
            "environment": self._config.environment,
            "state": self._state.value,
            "is_connected": self.is_connected,
            "active_jobs": self.active_job_count,
            "active_job_ids": list(self._active_jobs.keys()),
            "reconnect_attempts": self._reconnect_attempts,
            "config": {
                "batch_size": self._config.batch_size,
                "visibility_timeout_seconds": self._config.visibility_timeout_seconds,
                "heartbeat_interval_seconds": self._config.heartbeat_interval_seconds,
            },
        }

    async def __aenter__(self) -> "PgQueuerConsumer":
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: Any,
        exc_val: Any,
        exc_tb: Any,
    ) -> bool:
        """Async context manager exit."""
        await self.stop()
        return False
