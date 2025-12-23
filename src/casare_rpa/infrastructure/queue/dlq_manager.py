"""
CasareRPA Infrastructure Layer - Dead Letter Queue Manager

Implements a Dead Letter Queue (DLQ) strategy with exponential backoff retry.
Failed jobs are retried with increasing delays before being moved to the DLQ.

Features:
- Exponential backoff retry schedule (10s, 1m, 5m, 15m, 1h)
- Jitter (±20%) to prevent thundering herd
- DLQ for jobs that exceed retry limits
- DLQ inspection and manual retry API
- Integration with PgQueuer job queue

Database Schema:
    CREATE TABLE job_queue_dlq (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        original_job_id UUID NOT NULL,
        workflow_id VARCHAR(255) NOT NULL,
        workflow_name VARCHAR(255) NOT NULL,
        workflow_json TEXT NOT NULL,
        variables JSONB DEFAULT '{}',
        error_message TEXT NOT NULL,
        error_details JSONB DEFAULT '{}',
        retry_count INTEGER NOT NULL,
        first_failed_at TIMESTAMPTZ NOT NULL,
        last_failed_at TIMESTAMPTZ NOT NULL,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        reprocessed_at TIMESTAMPTZ,
        reprocessed_by VARCHAR(255),
        CONSTRAINT unique_original_job UNIQUE (original_job_id)
    );

    CREATE INDEX idx_dlq_workflow ON job_queue_dlq(workflow_id);
    CREATE INDEX idx_dlq_created ON job_queue_dlq(created_at DESC);
    CREATE INDEX idx_dlq_reprocessed ON job_queue_dlq(reprocessed_at) WHERE reprocessed_at IS NULL;
"""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timezone
from enum import Enum
from typing import (
    Any,
    AsyncContextManager,
    Dict,
    List,
    Optional,
    Protocol,
    Tuple,
    runtime_checkable,
)

from loguru import logger

# Optional dependency check
try:
    import asyncpg

    HAS_ASYNCPG = True
except ImportError:
    asyncpg = None
    HAS_ASYNCPG = False

# JSON serialization (orjson preferred, stdlib fallback)
try:
    import orjson

    def _json_dumps(data: Any) -> str:
        """Serialize to JSON using orjson."""
        result = orjson.dumps(data)
        return result.decode("utf-8") if isinstance(result, bytes) else str(result)

except ImportError:
    import json

    def _json_dumps(data: Any) -> str:
        """Serialize to JSON using stdlib."""
        return json.dumps(data)


class DatabaseConnection(Protocol):
    """Protocol for async database connection."""

    async def execute(self, query: str, *args: Any) -> str:
        """Execute a query."""
        ...

    async def fetch(self, query: str, *args: Any) -> list[Any]:
        """Fetch multiple rows."""
        ...

    async def fetchrow(self, query: str, *args: Any) -> Any | None:
        """Fetch a single row."""
        ...

    def transaction(self) -> AsyncContextManager[Any]:
        """Start a transaction."""
        ...


@runtime_checkable
class DatabasePool(Protocol):
    """Protocol for async database connection pool."""

    def acquire(self) -> AsyncContextManager[DatabaseConnection]:
        """Acquire a connection from the pool."""
        ...

    async def close(self) -> None:
        """Close the pool and all connections."""
        ...


# Retry schedule: exponential backoff delays in seconds
# Each value represents the delay before the next retry attempt
RETRY_SCHEDULE: list[int] = [
    10,  # Retry 1: 10 seconds after first failure
    60,  # Retry 2: 1 minute after second failure
    300,  # Retry 3: 5 minutes after third failure
    900,  # Retry 4: 15 minutes after fourth failure
    3600,  # Retry 5: 1 hour after fifth failure
]

# Jitter factor: ±20% to prevent thundering herd
JITTER_FACTOR: float = 0.2


class RetryAction(Enum):
    """Action taken after job failure."""

    RETRY = "retry"  # Job will be retried after backoff delay
    MOVE_TO_DLQ = "dlq"  # Job moved to Dead Letter Queue
    ALREADY_IN_DLQ = "already_in_dlq"  # Job was already in DLQ


@dataclass
class FailedJob:
    """
    Represents a job that has failed execution.

    Contains all data needed for retry or DLQ storage.
    """

    job_id: str
    workflow_id: str
    workflow_name: str
    workflow_json: str
    variables: dict[str, Any]
    retry_count: int
    error_message: str
    error_details: dict[str, Any] | None = None
    first_failed_at: datetime | None = None
    last_failed_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "job_id": self.job_id,
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "workflow_json": self.workflow_json,
            "variables": self.variables,
            "retry_count": self.retry_count,
            "error_message": self.error_message,
            "error_details": self.error_details,
            "first_failed_at": self.first_failed_at.isoformat() if self.first_failed_at else None,
            "last_failed_at": self.last_failed_at.isoformat() if self.last_failed_at else None,
        }


@dataclass
class DLQEntry:
    """
    Represents an entry in the Dead Letter Queue.

    Contains the failed job data plus DLQ metadata.
    """

    id: str
    original_job_id: str
    workflow_id: str
    workflow_name: str
    workflow_json: str
    variables: dict[str, Any]
    error_message: str
    error_details: dict[str, Any] | None
    retry_count: int
    first_failed_at: datetime
    last_failed_at: datetime
    created_at: datetime
    reprocessed_at: datetime | None = None
    reprocessed_by: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "original_job_id": self.original_job_id,
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "workflow_json": self.workflow_json,
            "variables": self.variables,
            "error_message": self.error_message,
            "error_details": self.error_details,
            "retry_count": self.retry_count,
            "first_failed_at": self.first_failed_at.isoformat(),
            "last_failed_at": self.last_failed_at.isoformat(),
            "created_at": self.created_at.isoformat(),
            "reprocessed_at": self.reprocessed_at.isoformat() if self.reprocessed_at else None,
            "reprocessed_by": self.reprocessed_by,
        }


@dataclass
class RetryResult:
    """Result of handling a job failure."""

    action: RetryAction
    job_id: str
    retry_count: int
    next_retry_at: datetime | None = None
    delay_seconds: int | None = None
    dlq_entry_id: str | None = None


@dataclass
class DLQManagerConfig:
    """Configuration for the Dead Letter Queue Manager."""

    postgres_url: str
    job_queue_table: str = "job_queue"
    dlq_table: str = "job_queue_dlq"
    retry_schedule: list[int] = field(default_factory=lambda: RETRY_SCHEDULE.copy())
    jitter_factor: float = JITTER_FACTOR
    pool_min_size: int = 1
    pool_max_size: int = 5


class DLQManager:
    """
    Dead Letter Queue Manager with exponential backoff retry.

    Handles job failures by either scheduling retries with exponential
    backoff or moving exhausted jobs to the Dead Letter Queue.

    Usage:
        config = DLQManagerConfig(postgres_url="postgresql://...")
        manager = DLQManager(config)

        await manager.start()

        # Handle a job failure
        result = await manager.handle_job_failure(failed_job)

        if result.action == RetryAction.RETRY:
            print(f"Job scheduled for retry in {result.delay_seconds}s")
        else:
            print(f"Job moved to DLQ: {result.dlq_entry_id}")

        await manager.stop()
    """

    # SQL for requeuing a job with visibility timeout
    SQL_REQUEUE_FOR_RETRY = """
        UPDATE {job_table}
        SET status = 'pending',
            retry_count = $1,
            visible_after = NOW() + $2::INTERVAL,
            robot_id = NULL,
            error_message = $3
        WHERE id = $4
        RETURNING id;
    """

    # SQL for inserting into DLQ
    SQL_INSERT_DLQ = """
        INSERT INTO {dlq_table} (
            original_job_id, workflow_id, workflow_name, workflow_json,
            variables, error_message, error_details, retry_count,
            first_failed_at, last_failed_at
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        ON CONFLICT (original_job_id) DO UPDATE SET
            error_message = EXCLUDED.error_message,
            error_details = EXCLUDED.error_details,
            retry_count = EXCLUDED.retry_count,
            last_failed_at = EXCLUDED.last_failed_at
        RETURNING id;
    """

    # SQL for removing job from queue after DLQ
    SQL_DELETE_JOB = """
        DELETE FROM {job_table}
        WHERE id = $1
        RETURNING id;
    """

    # SQL for listing DLQ entries
    SQL_LIST_DLQ = """
        SELECT id, original_job_id, workflow_id, workflow_name, workflow_json,
               variables, error_message, error_details, retry_count,
               first_failed_at, last_failed_at, created_at,
               reprocessed_at, reprocessed_by
        FROM {dlq_table}
        WHERE ($1::TEXT IS NULL OR workflow_id = $1)
          AND ($2::BOOLEAN IS FALSE OR reprocessed_at IS NULL)
        ORDER BY created_at DESC
        LIMIT $3 OFFSET $4;
    """

    # SQL for getting a single DLQ entry
    SQL_GET_DLQ_ENTRY = """
        SELECT id, original_job_id, workflow_id, workflow_name, workflow_json,
               variables, error_message, error_details, retry_count,
               first_failed_at, last_failed_at, created_at,
               reprocessed_at, reprocessed_by
        FROM {dlq_table}
        WHERE id = $1;
    """

    # SQL for manual retry from DLQ
    SQL_REPROCESS_DLQ = """
        WITH dlq_job AS (
            UPDATE {dlq_table}
            SET reprocessed_at = NOW(),
                reprocessed_by = $2
            WHERE id = $1 AND reprocessed_at IS NULL
            RETURNING original_job_id, workflow_id, workflow_name, workflow_json, variables
        )
        INSERT INTO {job_table} (
            id, workflow_id, workflow_name, workflow_json, variables,
            status, retry_count, priority, visible_after
        )
        SELECT gen_random_uuid(), workflow_id, workflow_name, workflow_json, variables,
               'pending', 0, 1, NOW()
        FROM dlq_job
        RETURNING id;
    """

    # SQL for counting DLQ entries
    SQL_COUNT_DLQ = """
        SELECT COUNT(*) as total,
               COUNT(*) FILTER (WHERE reprocessed_at IS NULL) as pending
        FROM {dlq_table}
        WHERE ($1::TEXT IS NULL OR workflow_id = $1);
    """

    # SQL for purging old DLQ entries
    SQL_PURGE_DLQ = """
        DELETE FROM {dlq_table}
        WHERE reprocessed_at IS NOT NULL
          AND reprocessed_at < NOW() - $1::INTERVAL
        RETURNING id;
    """

    def __init__(self, config: DLQManagerConfig) -> None:
        """
        Initialize the DLQ Manager.

        Args:
            config: Manager configuration

        Raises:
            ImportError: If asyncpg is not installed
        """
        if not HAS_ASYNCPG:
            raise ImportError(
                "asyncpg is required for DLQManager. Install with: pip install asyncpg"
            )

        self._config = config
        self._pool: DatabasePool | None = None
        self._running = False

        # Pre-format SQL with table names
        self._sql_requeue = self.SQL_REQUEUE_FOR_RETRY.format(job_table=config.job_queue_table)
        self._sql_insert_dlq = self.SQL_INSERT_DLQ.format(dlq_table=config.dlq_table)
        self._sql_delete_job = self.SQL_DELETE_JOB.format(job_table=config.job_queue_table)
        self._sql_list_dlq = self.SQL_LIST_DLQ.format(dlq_table=config.dlq_table)
        self._sql_get_entry = self.SQL_GET_DLQ_ENTRY.format(dlq_table=config.dlq_table)
        self._sql_reprocess = self.SQL_REPROCESS_DLQ.format(
            dlq_table=config.dlq_table,
            job_table=config.job_queue_table,
        )
        self._sql_count = self.SQL_COUNT_DLQ.format(dlq_table=config.dlq_table)
        self._sql_purge = self.SQL_PURGE_DLQ.format(dlq_table=config.dlq_table)

        logger.info(
            f"DLQManager initialized (retry_limits={len(config.retry_schedule)}, "
            f"jitter={config.jitter_factor:.0%})"
        )

    @property
    def max_retries(self) -> int:
        """Maximum number of retry attempts before DLQ."""
        return len(self._config.retry_schedule)

    @property
    def is_running(self) -> bool:
        """Check if manager is running."""
        return self._running and self._pool is not None

    def _get_pool(self) -> DatabasePool:
        """
        Get the database pool with type narrowing.

        Returns:
            The database pool

        Raises:
            ConnectionError: If pool is not available
        """
        if self._pool is None:
            raise ConnectionError("DLQManager not connected to database")
        return self._pool

    async def start(self) -> None:
        """
        Start the DLQ Manager and establish database connection.

        Raises:
            RuntimeError: If asyncpg is not available
            Exception: If database connection fails
        """
        if self._running:
            logger.warning("DLQManager already running")
            return

        # Runtime check with type narrowing
        if asyncpg is None:
            raise RuntimeError(
                "asyncpg is required for DLQManager. Install with: pip install asyncpg"
            )

        try:
            self._pool = await asyncpg.create_pool(
                self._config.postgres_url,
                min_size=self._config.pool_min_size,
                max_size=self._config.pool_max_size,
                command_timeout=30,
                statement_cache_size=0,  # Required for pgbouncer/Supabase
            )

            await self._ensure_dlq_table()
            self._running = True
            logger.info("DLQManager started")

        except Exception as e:
            logger.error(f"Failed to start DLQManager: {e}")
            raise

    async def stop(self) -> None:
        """Stop the DLQ Manager and close connections."""
        if not self._running:
            return

        self._running = False

        if self._pool:
            try:
                await self._pool.close()
            except Exception as e:
                logger.warning(f"Error closing DLQManager pool: {e}")
            finally:
                self._pool = None

        logger.info("DLQManager stopped")

    async def _ensure_dlq_table(self) -> None:
        """Create the DLQ table if it doesn't exist."""
        pool = self._get_pool()

        create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {self._config.dlq_table} (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                original_job_id UUID NOT NULL,
                workflow_id VARCHAR(255) NOT NULL,
                workflow_name VARCHAR(255) NOT NULL,
                workflow_json TEXT NOT NULL,
                variables JSONB DEFAULT '{{}}'::jsonb,
                error_message TEXT NOT NULL,
                error_details JSONB DEFAULT '{{}}'::jsonb,
                retry_count INTEGER NOT NULL,
                first_failed_at TIMESTAMPTZ NOT NULL,
                last_failed_at TIMESTAMPTZ NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                reprocessed_at TIMESTAMPTZ,
                reprocessed_by VARCHAR(255),
                CONSTRAINT unique_original_job_{self._config.dlq_table} UNIQUE (original_job_id)
            );

            CREATE INDEX IF NOT EXISTS idx_{self._config.dlq_table}_workflow
            ON {self._config.dlq_table}(workflow_id);

            CREATE INDEX IF NOT EXISTS idx_{self._config.dlq_table}_created
            ON {self._config.dlq_table}(created_at DESC);

            CREATE INDEX IF NOT EXISTS idx_{self._config.dlq_table}_pending
            ON {self._config.dlq_table}(reprocessed_at) WHERE reprocessed_at IS NULL;
        """

        async with pool.acquire() as conn:
            await conn.execute(create_table_sql)

        logger.debug(f"DLQ table '{self._config.dlq_table}' ensured")

    def calculate_backoff_delay(self, retry_count: int) -> tuple[int, int]:
        """
        Calculate the backoff delay with jitter for a retry attempt.

        Args:
            retry_count: Current retry count (0-indexed)

        Returns:
            Tuple of (base_delay, delay_with_jitter) in seconds
        """
        if retry_count >= len(self._config.retry_schedule):
            return 0, 0

        base_delay = self._config.retry_schedule[retry_count]

        # Add jitter: ±JITTER_FACTOR of the base delay
        jitter_range = base_delay * self._config.jitter_factor
        jitter = random.uniform(-jitter_range, jitter_range)
        delay_with_jitter = max(1, int(base_delay + jitter))

        return base_delay, delay_with_jitter

    async def handle_job_failure(
        self,
        job: FailedJob,
    ) -> RetryResult:
        """
        Handle a job failure with retry or DLQ.

        Implements the core DLQ strategy:
        1. If retry_count < max_retries: requeue with exponential backoff
        2. Otherwise: move to Dead Letter Queue

        Args:
            job: The failed job details

        Returns:
            RetryResult indicating the action taken

        Raises:
            ConnectionError: If database connection is not available
            Exception: If database operation fails
        """
        self._get_pool()  # Validate connection is available

        now = datetime.now(UTC)

        # Set failure timestamps
        first_failed = job.first_failed_at or now
        last_failed = now

        if job.retry_count < self.max_retries:
            # Schedule retry with exponential backoff
            return await self._schedule_retry(job, first_failed, last_failed)
        else:
            # Max retries exceeded, move to DLQ
            return await self._move_to_dlq(job, first_failed, last_failed)

    async def _schedule_retry(
        self,
        job: FailedJob,
        first_failed_at: datetime,
        last_failed_at: datetime,
    ) -> RetryResult:
        """
        Schedule a job for retry with exponential backoff.

        Args:
            job: Failed job to retry
            first_failed_at: Time of first failure
            last_failed_at: Time of last failure

        Returns:
            RetryResult with retry details
        """
        pool = self._get_pool()
        base_delay, delay_with_jitter = self.calculate_backoff_delay(job.retry_count)
        next_retry_count = job.retry_count + 1

        try:
            async with pool.acquire() as conn:
                result = await conn.fetchrow(
                    self._sql_requeue,
                    next_retry_count,
                    f"{delay_with_jitter} seconds",
                    job.error_message[:4000],  # Truncate long messages
                    uuid.UUID(job.job_id),
                )

            if result:
                next_retry_at = (
                    last_failed_at.replace(tzinfo=UTC)
                    if last_failed_at.tzinfo is None
                    else last_failed_at
                )

                from datetime import timedelta

                next_retry_at = next_retry_at + timedelta(seconds=delay_with_jitter)

                logger.info(
                    f"Job {job.job_id[:8]}... requeued for retry {next_retry_count}/{self.max_retries} "
                    f"in {delay_with_jitter}s (base: {base_delay}s)"
                )

                return RetryResult(
                    action=RetryAction.RETRY,
                    job_id=job.job_id,
                    retry_count=next_retry_count,
                    next_retry_at=next_retry_at,
                    delay_seconds=delay_with_jitter,
                )
            else:
                logger.warning(
                    f"Job {job.job_id[:8]}... not found for retry, may already be in DLQ"
                )
                return RetryResult(
                    action=RetryAction.ALREADY_IN_DLQ,
                    job_id=job.job_id,
                    retry_count=job.retry_count,
                )

        except Exception as e:
            logger.error(f"Failed to schedule retry for job {job.job_id[:8]}...: {e}")
            raise

    async def _move_to_dlq(
        self,
        job: FailedJob,
        first_failed_at: datetime,
        last_failed_at: datetime,
    ) -> RetryResult:
        """
        Move a job to the Dead Letter Queue.

        Args:
            job: Failed job to move
            first_failed_at: Time of first failure
            last_failed_at: Time of last failure

        Returns:
            RetryResult with DLQ entry ID
        """
        pool = self._get_pool()
        error_details_json = _json_dumps(job.error_details) if job.error_details else "{}"
        variables_json = _json_dumps(job.variables) if job.variables else "{}"

        try:
            async with pool.acquire() as conn:
                async with conn.transaction():
                    # Insert into DLQ
                    dlq_result = await conn.fetchrow(
                        self._sql_insert_dlq,
                        uuid.UUID(job.job_id),
                        job.workflow_id,
                        job.workflow_name,
                        job.workflow_json,
                        variables_json,
                        job.error_message[:4000],
                        error_details_json,
                        job.retry_count,
                        first_failed_at,
                        last_failed_at,
                    )

                    # Delete from job queue
                    await conn.execute(
                        self._sql_delete_job,
                        uuid.UUID(job.job_id),
                    )

            dlq_entry_id = str(dlq_result["id"]) if dlq_result else None

            logger.error(
                f"Job {job.job_id[:8]}... moved to DLQ after {job.retry_count} retries "
                f"(entry_id={dlq_entry_id[:8] if dlq_entry_id else 'unknown'}...): "
                f"{job.error_message[:100]}"
            )

            return RetryResult(
                action=RetryAction.MOVE_TO_DLQ,
                job_id=job.job_id,
                retry_count=job.retry_count,
                dlq_entry_id=dlq_entry_id,
            )

        except Exception as e:
            logger.error(f"Failed to move job {job.job_id[:8]}... to DLQ: {e}")
            raise

    async def list_dlq_entries(
        self,
        workflow_id: str | None = None,
        pending_only: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DLQEntry]:
        """
        List entries in the Dead Letter Queue.

        Args:
            workflow_id: Filter by workflow ID (optional)
            pending_only: Only show entries not yet reprocessed
            limit: Maximum entries to return
            offset: Pagination offset

        Returns:
            List of DLQ entries
        """
        pool = self._get_pool()

        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    self._sql_list_dlq,
                    workflow_id,
                    pending_only,
                    limit,
                    offset,
                )

            entries = []
            for row in rows:
                entries.append(_row_to_dlq_entry(row))

            return entries

        except Exception as e:
            logger.error(f"Failed to list DLQ entries: {e}")
            raise

    async def get_dlq_entry(self, entry_id: str) -> DLQEntry | None:
        """
        Get a specific DLQ entry by ID.

        Args:
            entry_id: DLQ entry UUID

        Returns:
            DLQEntry if found, None otherwise
        """
        pool = self._get_pool()

        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    self._sql_get_entry,
                    uuid.UUID(entry_id),
                )

            if not row:
                return None

            return _row_to_dlq_entry(row)

        except Exception as e:
            logger.error(f"Failed to get DLQ entry {entry_id}: {e}")
            raise

    async def retry_from_dlq(
        self,
        entry_id: str,
        reprocessed_by: str = "manual",
    ) -> str | None:
        """
        Manually retry a job from the Dead Letter Queue.

        Creates a new job in the main queue with reset retry count.
        Marks the DLQ entry as reprocessed.

        Args:
            entry_id: DLQ entry UUID to retry
            reprocessed_by: Identifier of who initiated the retry

        Returns:
            New job ID if successful, None if entry not found or already reprocessed
        """
        pool = self._get_pool()

        try:
            async with pool.acquire() as conn:
                result = await conn.fetchrow(
                    self._sql_reprocess,
                    uuid.UUID(entry_id),
                    reprocessed_by,
                )

            if result:
                new_job_id = str(result["id"])
                logger.info(
                    f"DLQ entry {entry_id[:8]}... reprocessed as new job {new_job_id[:8]}... "
                    f"by '{reprocessed_by}'"
                )
                return new_job_id
            else:
                logger.warning(f"DLQ entry {entry_id[:8]}... not found or already reprocessed")
                return None

        except Exception as e:
            logger.error(f"Failed to retry DLQ entry {entry_id}: {e}")
            raise

    async def get_dlq_stats(
        self,
        workflow_id: str | None = None,
    ) -> dict[str, int]:
        """
        Get DLQ statistics.

        Args:
            workflow_id: Filter by workflow ID (optional)

        Returns:
            Dict with 'total' and 'pending' counts
        """
        pool = self._get_pool()

        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    self._sql_count,
                    workflow_id,
                )

            return {
                "total": row["total"] if row else 0,
                "pending": row["pending"] if row else 0,
            }

        except Exception as e:
            logger.error(f"Failed to get DLQ stats: {e}")
            raise

    async def purge_reprocessed(
        self,
        older_than_days: int = 30,
    ) -> int:
        """
        Purge reprocessed DLQ entries older than specified days.

        Args:
            older_than_days: Delete entries reprocessed more than this many days ago

        Returns:
            Number of entries purged
        """
        pool = self._get_pool()

        try:
            async with pool.acquire() as conn:
                results = await conn.fetch(
                    self._sql_purge,
                    f"{older_than_days} days",
                )

            count = len(results)
            if count > 0:
                logger.info(
                    f"Purged {count} reprocessed DLQ entries older than {older_than_days} days"
                )

            return count

        except Exception as e:
            logger.error(f"Failed to purge DLQ entries: {e}")
            raise

    async def delete_dlq_entry(self, entry_id: str) -> bool:
        """
        Delete a DLQ entry permanently.

        Args:
            entry_id: DLQ entry UUID to delete

        Returns:
            True if entry was deleted, False if not found
        """
        pool = self._get_pool()

        try:
            async with pool.acquire() as conn:
                result = await conn.execute(
                    f"DELETE FROM {self._config.dlq_table} WHERE id = $1",
                    uuid.UUID(entry_id),
                )

            deleted = result != "DELETE 0"
            if deleted:
                logger.info(f"Deleted DLQ entry {entry_id}")
            return deleted

        except Exception as e:
            logger.error(f"Failed to delete DLQ entry {entry_id}: {e}")
            raise

    async def __aenter__(self) -> DLQManager:
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


def _row_to_dlq_entry(row: Any) -> DLQEntry:
    """Convert a database row to DLQEntry."""
    return DLQEntry(
        id=str(row["id"]),
        original_job_id=str(row["original_job_id"]),
        workflow_id=row["workflow_id"],
        workflow_name=row["workflow_name"],
        workflow_json=row["workflow_json"],
        variables=row["variables"] or {},
        error_message=row["error_message"],
        error_details=row["error_details"],
        retry_count=row["retry_count"],
        first_failed_at=row["first_failed_at"],
        last_failed_at=row["last_failed_at"],
        created_at=row["created_at"],
        reprocessed_at=row["reprocessed_at"],
        reprocessed_by=row["reprocessed_by"],
    )
