"""
CasareRPA Infrastructure Layer - PgQueuer Producer

Implements a PostgreSQL-based distributed queue producer for orchestrator job enqueuing.
Counterpart to PgQueuerConsumer - the orchestrator uses this to submit jobs.

Features:
- Job submission with priority and environment routing
- Batch job enqueuing for bulk operations
- Job cancellation and status queries
- Automatic reconnection with exponential backoff
- Connection pooling for high throughput

Architecture:
- Orchestrator submits jobs via enqueue_job() or enqueue_batch()
- Jobs are inserted with pending status and become visible immediately
- Priority-based ordering (higher priority = claimed first)
- Environment filtering for multi-tenant deployments

Database Schema (same as consumer):
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
"""

from __future__ import annotations

import asyncio
import random
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from loguru import logger

from casare_rpa.infrastructure.queue.types import (
    DatabaseRecord,
    DatabaseRecordList,
    JobDetailedStatus,
    JobId,
    ProducerConfigStats,
    ProducerStats,
    QueueStats,
    StateChangeCallback,
    WorkflowId,
)

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


class ProducerConnectionState(Enum):
    """Producer connection state."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


@dataclass
class EnqueuedJob:
    """
    Represents a job that has been enqueued by the producer.

    Contains confirmation data after successful submission.
    """

    job_id: str
    workflow_id: str
    workflow_name: str
    priority: int
    environment: str
    created_at: datetime
    visible_after: datetime

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "job_id": self.job_id,
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "priority": self.priority,
            "environment": self.environment,
            "created_at": self.created_at.isoformat(),
            "visible_after": self.visible_after.isoformat(),
        }


@dataclass
class JobSubmission:
    """
    Job submission request for batch enqueuing.

    Use this when submitting multiple jobs at once.
    """

    workflow_id: str
    workflow_name: str
    workflow_json: str
    priority: int = 10
    environment: str = "default"
    variables: dict[str, Any] | None = None
    max_retries: int = 3
    delay_seconds: int = 0  # Delay before job becomes visible

    def __post_init__(self) -> None:
        """Validate submission data."""
        if not self.workflow_id:
            raise ValueError("workflow_id is required")
        if not self.workflow_name:
            raise ValueError("workflow_name is required")
        if not self.workflow_json:
            raise ValueError("workflow_json is required")
        if self.priority < 0 or self.priority > 100:
            raise ValueError("priority must be between 0 and 100")
        if self.max_retries < 0 or self.max_retries > 10:
            raise ValueError("max_retries must be between 0 and 10")
        if self.delay_seconds < 0:
            raise ValueError("delay_seconds cannot be negative")


@dataclass
class ProducerConfig:
    """Configuration for PgQueuerProducer."""

    postgres_url: str
    default_environment: str = "default"
    default_priority: int = 10
    default_max_retries: int = 3
    max_reconnect_attempts: int = 10
    reconnect_base_delay_seconds: float = 1.0
    reconnect_max_delay_seconds: float = 60.0
    pool_min_size: int = 2
    pool_max_size: int = 10

    def to_dict(self) -> dict[str, Any]:
        """
        Convert config to dictionary with credential masking.

        SECURITY: Masks postgres_url to prevent credential leakage in logs.
        """
        from casare_rpa.infrastructure.security.validators import sanitize_log_value

        return {
            "postgres_url": sanitize_log_value(self.postgres_url),
            "default_environment": self.default_environment,
            "default_priority": self.default_priority,
            "default_max_retries": self.default_max_retries,
            "max_reconnect_attempts": self.max_reconnect_attempts,
            "reconnect_base_delay_seconds": self.reconnect_base_delay_seconds,
            "reconnect_max_delay_seconds": self.reconnect_max_delay_seconds,
            "pool_min_size": self.pool_min_size,
            "pool_max_size": self.pool_max_size,
        }


class PgQueuerProducer:
    """
    PostgreSQL-based distributed queue producer for orchestrator job enqueuing.

    Provides high-throughput job submission with connection pooling and
    automatic reconnection.

    Usage:
        config = ProducerConfig(
            postgres_url="postgresql://user:pass@host:5432/db",
            default_environment="production"
        )
        producer = PgQueuerProducer(config)

        await producer.start()

        # Submit a single job
        job = await producer.enqueue_job(
            workflow_id="wf-001",
            workflow_name="Data Processing",
            workflow_json='{"nodes": [...]}',
            priority=20,
        )
        print(f"Submitted job {job.job_id}")

        # Submit batch of jobs
        submissions = [
            JobSubmission(workflow_id="wf-001", workflow_name="Job A", workflow_json="..."),
            JobSubmission(workflow_id="wf-002", workflow_name="Job B", workflow_json="..."),
        ]
        jobs = await producer.enqueue_batch(submissions)

        await producer.stop()
    """

    # SQL queries as class constants for clarity and maintainability
    SQL_ENQUEUE_JOB = """
        INSERT INTO job_queue (
            id, workflow_id, workflow_name, workflow_json,
            priority, status, environment, visible_after,
            created_at, max_retries, variables
        ) VALUES (
            $1, $2, $3, $4, $5, 'pending', $6,
            NOW() + INTERVAL '1 second' * $7,
            NOW(), $8, $9::jsonb
        )
        RETURNING id, workflow_id, workflow_name, priority, environment,
                  created_at, visible_after;
    """

    SQL_CANCEL_JOB = """
        UPDATE job_queue
        SET status = 'cancelled',
            completed_at = NOW(),
            error_message = $2
        WHERE id = $1
          AND status IN ('pending', 'running')
        RETURNING id, status;
    """

    SQL_GET_JOB_STATUS = """
        SELECT id, status, robot_id, priority, environment,
               created_at, started_at, completed_at,
               error_message, retry_count, max_retries
        FROM job_queue
        WHERE id = $1;
    """

    SQL_GET_QUEUE_STATS = """
        SELECT
            COUNT(*) FILTER (WHERE status = 'pending') as pending_count,
            COUNT(*) FILTER (WHERE status = 'running') as running_count,
            COUNT(*) FILTER (WHERE status = 'completed') as completed_count,
            COUNT(*) FILTER (WHERE status = 'failed') as failed_count,
            COUNT(*) FILTER (WHERE status = 'cancelled') as cancelled_count,
            AVG(EXTRACT(EPOCH FROM (started_at - created_at)))
                FILTER (WHERE started_at IS NOT NULL) as avg_queue_wait_seconds,
            AVG(EXTRACT(EPOCH FROM (completed_at - started_at)))
                FILTER (WHERE completed_at IS NOT NULL AND status = 'completed')
                as avg_execution_seconds
        FROM job_queue
        WHERE created_at > NOW() - INTERVAL '1 hour';
    """

    SQL_GET_QUEUE_DEPTH_BY_PRIORITY = """
        SELECT priority, COUNT(*) as count
        FROM job_queue
        WHERE status = 'pending'
          AND visible_after <= NOW()
        GROUP BY priority
        ORDER BY priority DESC;
    """

    SQL_PURGE_OLD_JOBS = """
        DELETE FROM job_queue
        WHERE status IN ('completed', 'failed', 'cancelled')
          AND completed_at < NOW() - INTERVAL '1 day' * $1
        RETURNING id;
    """

    def __init__(self, config: ProducerConfig) -> None:
        """
        Initialize the producer.

        Args:
            config: Producer configuration

        Raises:
            ImportError: If asyncpg is not installed
        """
        if not HAS_ASYNCPG:
            raise ImportError(
                "asyncpg is required for PgQueuerProducer. " "Install with: pip install asyncpg"
            )

        self._config: ProducerConfig = config
        self._pool: Pool | None = None
        self._state: ProducerConnectionState = ProducerConnectionState.DISCONNECTED
        self._running: bool = False
        self._reconnect_attempts: int = 0
        self._state_callbacks: list[StateChangeCallback] = []
        self._lock: asyncio.Lock = asyncio.Lock()

        # Statistics
        self._total_enqueued: int = 0
        self._total_cancelled: int = 0

        logger.info(
            f"PgQueuerProducer initialized with default environment "
            f"'{config.default_environment}'"
        )

    @property
    def state(self) -> ProducerConnectionState:
        """Get current connection state."""
        return self._state

    @property
    def is_connected(self) -> bool:
        """Check if producer is connected and ready."""
        return self._state == ProducerConnectionState.CONNECTED and self._pool is not None

    @property
    def total_enqueued(self) -> int:
        """Get total number of jobs enqueued since startup."""
        return self._total_enqueued

    @property
    def total_cancelled(self) -> int:
        """Get total number of jobs cancelled since startup."""
        return self._total_cancelled

    def add_state_callback(self, callback: StateChangeCallback) -> None:
        """
        Add a callback for connection state changes.

        Args:
            callback: Function to call when state changes (must accept ProducerConnectionState)
        """
        self._state_callbacks.append(callback)

    def remove_state_callback(self, callback: StateChangeCallback) -> None:
        """
        Remove a state change callback.

        Args:
            callback: Callback to remove
        """
        if callback in self._state_callbacks:
            self._state_callbacks.remove(callback)

    def _set_state(self, new_state: ProducerConnectionState) -> None:
        """Update state and notify callbacks."""
        if self._state != new_state:
            old_state = self._state
            self._state = new_state
            logger.debug(f"Producer state: {old_state.value} -> {new_state.value}")
            for callback in self._state_callbacks:
                try:
                    callback(new_state)
                except Exception as e:
                    logger.warning(f"State callback error: {e}")

    async def start(self) -> bool:
        """
        Start the producer and establish database connection.

        Returns:
            True if started successfully, False otherwise
        """
        if self._running:
            logger.warning("Producer already running")
            return True

        self._running = True
        success = await self._connect()

        if success:
            logger.info("PgQueuerProducer started")

        return success

    async def stop(self) -> None:
        """
        Stop the producer gracefully.

        Closes all database connections.
        """
        logger.info("Stopping PgQueuerProducer...")
        self._running = False

        # Close pool
        if self._pool:
            try:
                await self._pool.close()
            except Exception as e:
                logger.warning(f"Error closing connection pool: {e}")
            self._pool = None

        self._set_state(ProducerConnectionState.DISCONNECTED)
        logger.info(
            f"PgQueuerProducer stopped (enqueued={self._total_enqueued}, "
            f"cancelled={self._total_cancelled})"
        )

    async def _connect(self) -> bool:
        """
        Establish database connection with retry logic.

        Returns:
            True if connected successfully
        """
        self._set_state(ProducerConnectionState.CONNECTING)

        try:
            self._pool = await asyncpg.create_pool(
                self._config.postgres_url,
                min_size=self._config.pool_min_size,
                max_size=self._config.pool_max_size,
                command_timeout=30,
                statement_cache_size=0,  # Required for pgbouncer/Supabase
            )

            # Test connection
            async with self._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")

            self._set_state(ProducerConnectionState.CONNECTED)
            self._reconnect_attempts = 0
            logger.info("Database connection established")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            self._set_state(ProducerConnectionState.FAILED)
            return False

    async def _reconnect(self) -> bool:
        """
        Attempt to reconnect with exponential backoff.

        Returns:
            True if reconnected successfully
        """
        if not self._running:
            return False

        self._set_state(ProducerConnectionState.RECONNECTING)
        self._reconnect_attempts += 1

        if self._reconnect_attempts > self._config.max_reconnect_attempts:
            logger.error(f"Max reconnect attempts ({self._config.max_reconnect_attempts}) exceeded")
            self._set_state(ProducerConnectionState.FAILED)
            return False

        # Exponential backoff with jitter
        delay = min(
            self._config.reconnect_base_delay_seconds * (2 ** (self._reconnect_attempts - 1)),
            self._config.reconnect_max_delay_seconds,
        )
        # Add jitter (10-30% of delay)
        jitter = delay * random.uniform(0.1, 0.3)
        delay += jitter

        logger.info(
            f"Reconnect attempt {self._reconnect_attempts}/"
            f"{self._config.max_reconnect_attempts} in {delay:.1f}s"
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

        if self._state in (
            ProducerConnectionState.CONNECTING,
            ProducerConnectionState.RECONNECTING,
        ):
            # Already trying to connect
            await asyncio.sleep(0.5)
            return self.is_connected

        return await self._reconnect()

    async def _execute_with_retry(
        self,
        query: str,
        *args: Any,
        max_retries: int = 3,
    ) -> DatabaseRecordList:
        """
        Execute a query with automatic retry on connection failure.

        Args:
            query: SQL query to execute
            *args: Query arguments
            max_retries: Maximum retry attempts

        Returns:
            List of database records from the query

        Raises:
            PostgresError: If query fails after all retries
            ConnectionError: If connection cannot be established
        """
        last_error: Exception | None = None

        for attempt in range(max_retries):
            if not await self._ensure_connection():
                raise ConnectionError("Unable to establish database connection")

            try:
                assert self._pool is not None  # Guaranteed by _ensure_connection()
                async with self._pool.acquire() as conn:
                    result: Sequence[DatabaseRecord] = await conn.fetch(query, *args)
                    return list(result)
            except asyncpg.exceptions.ConnectionDoesNotExistError:
                logger.warning(f"Connection lost, attempting reconnect (attempt {attempt + 1})")
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

    async def enqueue_job(
        self,
        workflow_id: WorkflowId,
        workflow_name: str,
        workflow_json: str,
        priority: int | None = None,
        environment: str | None = None,
        variables: dict[str, Any] | None = None,
        max_retries: int | None = None,
        delay_seconds: int = 0,
    ) -> EnqueuedJob:
        """
        Enqueue a single job to the queue.

        Args:
            workflow_id: Unique workflow identifier
            workflow_name: Human-readable workflow name
            workflow_json: Serialized workflow definition
            priority: Job priority (0-100, higher = more urgent)
            environment: Target environment for robot filtering
            variables: Initial workflow variables
            max_retries: Maximum retry attempts on failure
            delay_seconds: Delay before job becomes visible

        Returns:
            EnqueuedJob with confirmation data

        Raises:
            ValueError: If arguments are invalid
            ConnectionError: If database connection fails
        """
        import orjson

        # Validate workflow_id
        from casare_rpa.infrastructure.security.validators import validate_workflow_id

        validate_workflow_id(workflow_id)

        # Apply defaults
        priority = priority if priority is not None else self._config.default_priority
        environment = environment or self._config.default_environment
        max_retries = max_retries if max_retries is not None else self._config.default_max_retries
        variables = variables or {}

        # Validate ranges
        if priority < 0 or priority > 100:
            raise ValueError("priority must be between 0 and 100")
        if max_retries < 0 or max_retries > 10:
            raise ValueError("max_retries must be between 0 and 10")
        if delay_seconds < 0:
            raise ValueError("delay_seconds cannot be negative")

        job_id = uuid.uuid4()
        variables_json = orjson.dumps(variables).decode("utf-8")

        try:
            rows = await self._execute_with_retry(
                self.SQL_ENQUEUE_JOB,
                job_id,
                workflow_id,
                workflow_name,
                workflow_json,
                priority,
                environment,
                delay_seconds,
                max_retries,
                variables_json,
            )

            if not rows:
                raise RuntimeError("Failed to enqueue job - no row returned")

            row = rows[0]
            enqueued_job = EnqueuedJob(
                job_id=str(row["id"]),
                workflow_id=row["workflow_id"],
                workflow_name=row["workflow_name"],
                priority=row["priority"],
                environment=row["environment"],
                created_at=row["created_at"],
                visible_after=row["visible_after"],
            )

            async with self._lock:
                self._total_enqueued += 1

            logger.info(
                f"Enqueued job {enqueued_job.job_id[:8]}... "
                f"workflow='{workflow_name}' priority={priority} env='{environment}'"
            )

            return enqueued_job

        except Exception as e:
            logger.error(f"Failed to enqueue job: {e}")
            raise

    async def enqueue_batch(self, submissions: list[JobSubmission]) -> list[EnqueuedJob]:
        """
        Enqueue multiple jobs in a single transaction.

        More efficient than calling enqueue_job() multiple times.

        Args:
            submissions: List of JobSubmission objects

        Returns:
            List of EnqueuedJob confirmations

        Raises:
            ValueError: If any submission is invalid
            ConnectionError: If database connection fails
        """
        if not submissions:
            return []

        import orjson

        from casare_rpa.infrastructure.security.validators import validate_workflow_id

        # Validate all submissions first
        for sub in submissions:
            validate_workflow_id(sub.workflow_id)

        if not await self._ensure_connection():
            raise ConnectionError("Unable to establish database connection")

        enqueued_jobs: list[EnqueuedJob] = []

        try:
            assert self._pool is not None  # Guaranteed by _ensure_connection()
            async with self._pool.acquire() as conn:
                async with conn.transaction():
                    for sub in submissions:
                        job_id = uuid.uuid4()
                        variables = sub.variables or {}
                        variables_json = orjson.dumps(variables).decode("utf-8")

                        rows = await conn.fetch(
                            self.SQL_ENQUEUE_JOB,
                            job_id,
                            sub.workflow_id,
                            sub.workflow_name,
                            sub.workflow_json,
                            sub.priority,
                            sub.environment,
                            sub.delay_seconds,
                            sub.max_retries,
                            variables_json,
                        )

                        if rows:
                            row = rows[0]
                            enqueued_jobs.append(
                                EnqueuedJob(
                                    job_id=str(row["id"]),
                                    workflow_id=row["workflow_id"],
                                    workflow_name=row["workflow_name"],
                                    priority=row["priority"],
                                    environment=row["environment"],
                                    created_at=row["created_at"],
                                    visible_after=row["visible_after"],
                                )
                            )

            async with self._lock:
                self._total_enqueued += len(enqueued_jobs)

            logger.info(f"Batch enqueued {len(enqueued_jobs)} jobs")
            return enqueued_jobs

        except Exception as e:
            logger.error(f"Failed to batch enqueue jobs: {e}")
            raise

    async def cancel_job(
        self,
        job_id: JobId,
        reason: str = "Cancelled by orchestrator",
    ) -> bool:
        """
        Cancel a pending or running job.

        Jobs that are already completed, failed, or cancelled cannot be cancelled.

        Args:
            job_id: Job ID to cancel
            reason: Cancellation reason

        Returns:
            True if job was cancelled, False if not found or already finished

        Raises:
            ConnectionError: If database connection fails
        """
        try:
            rows = await self._execute_with_retry(
                self.SQL_CANCEL_JOB,
                uuid.UUID(job_id),
                reason[:4000],
            )

            success = len(rows) > 0

            if success:
                async with self._lock:
                    self._total_cancelled += 1
                logger.info(f"Cancelled job {job_id[:8]}...: {reason}")
            else:
                logger.warning(
                    f"Failed to cancel job {job_id[:8]}... " "(not found or already finished)"
                )

            return success

        except Exception as e:
            logger.error(f"Failed to cancel job {job_id[:8]}...: {e}")
            raise

    async def get_job_status(self, job_id: JobId) -> JobDetailedStatus | None:
        """
        Get detailed status of a job.

        Args:
            job_id: Job ID to query

        Returns:
            Dict with job status info, or None if not found
        """
        try:
            rows = await self._execute_with_retry(
                self.SQL_GET_JOB_STATUS,
                uuid.UUID(job_id),
            )

            if not rows:
                return None

            row = rows[0]
            status: JobDetailedStatus = {
                "job_id": str(row["id"]),
                "status": row["status"],
                "robot_id": row["robot_id"],
                "priority": row["priority"],
                "environment": row["environment"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                "started_at": row["started_at"].isoformat() if row["started_at"] else None,
                "completed_at": row["completed_at"].isoformat() if row["completed_at"] else None,
                "error_message": row["error_message"],
                "retry_count": row["retry_count"],
                "max_retries": row["max_retries"],
            }
            return status

        except Exception as e:
            logger.error(f"Failed to get job status: {e}")
            return None

    async def get_queue_stats(self) -> QueueStats:
        """
        Get queue statistics for the last hour.

        Returns:
            Typed queue statistics dictionary
        """
        empty_stats: QueueStats = {
            "pending_count": 0,
            "running_count": 0,
            "completed_count": 0,
            "failed_count": 0,
            "cancelled_count": 0,
            "avg_queue_wait_seconds": 0.0,
            "avg_execution_seconds": 0.0,
        }

        try:
            rows = await self._execute_with_retry(self.SQL_GET_QUEUE_STATS)

            if not rows:
                return empty_stats

            row = rows[0]
            stats: QueueStats = {
                "pending_count": row["pending_count"] or 0,
                "running_count": row["running_count"] or 0,
                "completed_count": row["completed_count"] or 0,
                "failed_count": row["failed_count"] or 0,
                "cancelled_count": row["cancelled_count"] or 0,
                "avg_queue_wait_seconds": float(row["avg_queue_wait_seconds"] or 0),
                "avg_execution_seconds": float(row["avg_execution_seconds"] or 0),
            }
            return stats

        except Exception as e:
            logger.error(f"Failed to get queue stats: {e}")
            return empty_stats

    async def get_queue_depth_by_priority(self) -> dict[int, int]:
        """
        Get queue depth grouped by priority.

        Returns:
            Dict mapping priority to count of pending jobs
        """
        try:
            rows = await self._execute_with_retry(self.SQL_GET_QUEUE_DEPTH_BY_PRIORITY)
            return {row["priority"]: row["count"] for row in rows}

        except Exception as e:
            logger.error(f"Failed to get queue depth by priority: {e}")
            return {}

    async def purge_old_jobs(self, days_old: int = 30) -> int:
        """
        Purge completed/failed/cancelled jobs older than specified days.

        Args:
            days_old: Delete jobs older than this many days

        Returns:
            Number of jobs deleted

        Raises:
            ValueError: If days_old is invalid
            ConnectionError: If database connection fails
        """
        if days_old < 1:
            raise ValueError("days_old must be at least 1")

        try:
            rows = await self._execute_with_retry(self.SQL_PURGE_OLD_JOBS, days_old)
            count = len(rows)

            if count > 0:
                logger.info(f"Purged {count} jobs older than {days_old} days")

            return count

        except Exception as e:
            logger.error(f"Failed to purge old jobs: {e}")
            raise

    def get_stats(self) -> ProducerStats:
        """
        Get producer statistics.

        Returns:
            Typed producer statistics dictionary
        """
        config_stats: ProducerConfigStats = {
            "default_environment": self._config.default_environment,
            "default_priority": self._config.default_priority,
            "default_max_retries": self._config.default_max_retries,
        }
        stats: ProducerStats = {
            "state": self._state.value,
            "is_connected": self.is_connected,
            "total_enqueued": self._total_enqueued,
            "total_cancelled": self._total_cancelled,
            "reconnect_attempts": self._reconnect_attempts,
            "config": config_stats,
        }
        return stats

    async def __aenter__(self) -> PgQueuerProducer:
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any | None,
    ) -> bool:
        """Async context manager exit."""
        await self.stop()
        return False
