"""
Robot Failover and Crash Recovery Module.

Implements fault-tolerant job recovery when robots crash or disconnect.
Integrates with DBOS checkpointing for exactly-once execution semantics.

Key Features:
- Automatic robot failure detection via heartbeat timeout
- Job recovery from DBOS checkpoints when available
- Graceful job requeuing with configurable delays
- Dead Letter Queue (DLQ) for permanently failed jobs
- Health monitoring integration for proactive failure detection

Architecture:
- RobotRecoveryManager coordinates all recovery operations
- Integrates with PostgreSQL job queue (pgqueuer pattern)
- Uses DBOS workflow checkpoints for resumable execution
- Visibility timeout prevents duplicate job processing
"""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Protocol

from loguru import logger

try:
    import asyncpg
    from asyncpg import Pool

    HAS_ASYNCPG = True
except ImportError:
    HAS_ASYNCPG = False
    asyncpg = None
    Pool = None


class RecoveryAction(Enum):
    """Actions taken during job recovery."""

    RESUMED_FROM_CHECKPOINT = "resumed_from_checkpoint"
    REQUEUED_FOR_RETRY = "requeued_for_retry"
    MOVED_TO_DLQ = "moved_to_dlq"
    NO_ACTION_NEEDED = "no_action_needed"
    RECOVERY_FAILED = "recovery_failed"


class RobotStatus(Enum):
    """Robot status values for database operations."""

    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    FAILED = "failed"
    MAINTENANCE = "maintenance"


class WorkflowCheckpointStatus(Enum):
    """DBOS workflow checkpoint status values."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class RobotFailureEvent:
    """
    Event representing a robot failure detection.

    Attributes:
        robot_id: Unique identifier of the failed robot
        detected_at: Timestamp when failure was detected
        last_heartbeat: Last known heartbeat timestamp
        failure_reason: Human-readable failure description
        active_job_ids: List of job IDs that were being processed
    """

    robot_id: str
    detected_at: datetime
    last_heartbeat: Optional[datetime]
    failure_reason: str
    active_job_ids: List[str] = field(default_factory=list)


@dataclass
class RecoveryResult:
    """
    Result of a job recovery operation.

    Attributes:
        job_id: ID of the job that was recovered
        action: Recovery action that was taken
        success: Whether recovery was successful
        error: Error message if recovery failed
        delay_seconds: Delay before job becomes visible again
        checkpoint_used: Whether DBOS checkpoint was used for recovery
    """

    job_id: str
    action: RecoveryAction
    success: bool
    error: Optional[str] = None
    delay_seconds: int = 0
    checkpoint_used: bool = False


@dataclass
class FailedJobInfo:
    """Information about a job that failed due to robot crash."""

    job_id: str
    workflow_id: str
    workflow_name: str
    workflow_json: str
    priority: int
    environment: str
    variables: Dict[str, Any]
    retry_count: int
    max_retries: int
    created_at: datetime
    claimed_at: Optional[datetime]


@dataclass
class RobotRecoveryConfig:
    """
    Configuration for robot recovery behavior.

    Attributes:
        postgres_url: PostgreSQL connection string
        job_table: Table name for job queue (default: job_queue)
        robot_table: Table name for robots (default: robots)
        checkpoint_table: Table name for DBOS checkpoints
        dlq_table: Table name for dead letter queue
        heartbeat_timeout_seconds: Time after which robot is considered dead
        default_requeue_delay_seconds: Default delay for requeued jobs
        max_retries: Maximum retry attempts before moving to DLQ
        retry_delays: List of delays for exponential backoff retries
        enable_checkpoint_recovery: Enable DBOS checkpoint-based recovery
        monitor_interval_seconds: Interval for health monitoring loop
        pool_min_size: Minimum database pool connections
        pool_max_size: Maximum database pool connections
    """

    postgres_url: str
    job_table: str = "job_queue"
    robot_table: str = "robots"
    checkpoint_table: str = "workflow_checkpoints"
    dlq_table: str = "job_dlq"
    heartbeat_timeout_seconds: int = 60
    default_requeue_delay_seconds: int = 10
    max_retries: int = 5
    retry_delays: List[int] = field(default_factory=lambda: [10, 60, 300, 900, 3600])
    enable_checkpoint_recovery: bool = True
    monitor_interval_seconds: float = 30.0
    pool_min_size: int = 2
    pool_max_size: int = 5


class DBOSClientProtocol(Protocol):
    """Protocol for DBOS workflow status API integration."""

    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a DBOS workflow.

        Returns dict with 'status' key containing WorkflowCheckpointStatus value.
        """
        ...


class RobotRecoveryManager:
    """
    Manages robot failure detection and job recovery.

    Monitors robot health via heartbeat timeouts and recovers jobs
    from failed robots using DBOS checkpoints when available.

    Usage:
        config = RobotRecoveryConfig(
            postgres_url="postgresql://user:pass@host:5432/db",
            heartbeat_timeout_seconds=60,
        )
        manager = RobotRecoveryManager(config)

        await manager.start()

        # Manual failure handling
        event = RobotFailureEvent(
            robot_id="robot-001",
            detected_at=datetime.now(timezone.utc),
            last_heartbeat=...,
            failure_reason="Heartbeat timeout"
        )
        results = await manager.handle_robot_failure(event)

        await manager.stop()
    """

    # SQL queries for robot and job management
    SQL_MARK_ROBOT_FAILED = """
        UPDATE {robot_table}
        SET status = 'failed', updated_at = NOW()
        WHERE id = $1
        RETURNING id, name, status;
    """

    SQL_FIND_CLAIMED_JOBS = """
        SELECT id, workflow_id, workflow_name, workflow_json, priority,
               environment, variables, retry_count, max_retries, created_at, started_at
        FROM {job_table}
        WHERE robot_id = $1 AND status = 'running'
        ORDER BY priority DESC, created_at ASC;
    """

    SQL_RELEASE_JOB_TO_QUEUE = """
        UPDATE {job_table}
        SET status = 'pending',
            robot_id = NULL,
            started_at = NULL,
            visible_after = NOW() + INTERVAL '1 second' * $2,
            error_message = COALESCE(error_message, '') || $3
        WHERE id = $1 AND status = 'running'
        RETURNING id;
    """

    SQL_REQUEUE_WITH_RETRY = """
        UPDATE {job_table}
        SET status = CASE
                WHEN retry_count < max_retries THEN 'pending'
                ELSE 'failed'
            END,
            robot_id = NULL,
            started_at = NULL,
            retry_count = retry_count + 1,
            visible_after = CASE
                WHEN retry_count < max_retries
                THEN NOW() + INTERVAL '1 second' * $2
                ELSE visible_after
            END,
            error_message = $3,
            completed_at = CASE
                WHEN retry_count >= max_retries THEN NOW()
                ELSE NULL
            END
        WHERE id = $1 AND status = 'running'
        RETURNING id, status, retry_count;
    """

    SQL_MOVE_TO_DLQ = """
        INSERT INTO {dlq_table} (
            job_id, workflow_id, workflow_name, workflow_json,
            variables, error_message, retry_count, failed_at,
            original_created_at, robot_id
        )
        SELECT id, workflow_id, workflow_name, workflow_json,
               variables, $2, retry_count, NOW(), created_at, $3
        FROM {job_table}
        WHERE id = $1
        RETURNING job_id;
    """

    SQL_DELETE_FAILED_JOB = """
        DELETE FROM {job_table}
        WHERE id = $1 AND status = 'failed'
        RETURNING id;
    """

    SQL_GET_CHECKPOINT_STATUS = """
        SELECT workflow_id, state, current_step, executed_nodes, updated_at
        FROM {checkpoint_table}
        WHERE workflow_id = $1;
    """

    SQL_FIND_STALE_ROBOTS = """
        SELECT id, name, last_heartbeat
        FROM {robot_table}
        WHERE status IN ('online', 'busy')
          AND last_heartbeat < NOW() - INTERVAL '1 second' * $1;
    """

    SQL_GET_ROBOT_ACTIVE_JOBS = """
        SELECT id
        FROM {job_table}
        WHERE robot_id = $1 AND status = 'running';
    """

    def __init__(
        self,
        config: RobotRecoveryConfig,
        dbos_client: Optional[DBOSClientProtocol] = None,
        on_failure_detected: Optional[Callable[[RobotFailureEvent], None]] = None,
        on_recovery_complete: Optional[Callable[[str, List[RecoveryResult]], None]] = None,
    ) -> None:
        """
        Initialize the robot recovery manager.

        Args:
            config: Recovery configuration
            dbos_client: Optional DBOS client for checkpoint status queries
            on_failure_detected: Callback when robot failure is detected
            on_recovery_complete: Callback when recovery completes for a robot

        Raises:
            ImportError: If asyncpg is not installed
        """
        if not HAS_ASYNCPG:
            raise ImportError(
                "asyncpg is required for RobotRecoveryManager. " "Install with: pip install asyncpg"
            )

        self._config = config
        self._dbos_client = dbos_client
        self._on_failure_detected = on_failure_detected
        self._on_recovery_complete = on_recovery_complete

        self._pool: Optional[Pool] = None
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._recovery_history: List[Dict[str, Any]] = []
        self._max_history = 1000

        # Format SQL queries with table names
        self._sql_mark_robot_failed = self.SQL_MARK_ROBOT_FAILED.format(
            robot_table=config.robot_table
        )
        self._sql_find_claimed_jobs = self.SQL_FIND_CLAIMED_JOBS.format(job_table=config.job_table)
        self._sql_release_job = self.SQL_RELEASE_JOB_TO_QUEUE.format(job_table=config.job_table)
        self._sql_requeue_with_retry = self.SQL_REQUEUE_WITH_RETRY.format(
            job_table=config.job_table
        )
        self._sql_move_to_dlq = self.SQL_MOVE_TO_DLQ.format(
            dlq_table=config.dlq_table,
            job_table=config.job_table,
        )
        self._sql_delete_failed = self.SQL_DELETE_FAILED_JOB.format(job_table=config.job_table)
        self._sql_get_checkpoint = self.SQL_GET_CHECKPOINT_STATUS.format(
            checkpoint_table=config.checkpoint_table
        )
        self._sql_find_stale_robots = self.SQL_FIND_STALE_ROBOTS.format(
            robot_table=config.robot_table
        )
        self._sql_get_robot_jobs = self.SQL_GET_ROBOT_ACTIVE_JOBS.format(job_table=config.job_table)

        logger.info(
            f"RobotRecoveryManager initialized "
            f"(heartbeat_timeout={config.heartbeat_timeout_seconds}s, "
            f"checkpoint_recovery={'enabled' if config.enable_checkpoint_recovery else 'disabled'})"
        )

    @property
    def is_running(self) -> bool:
        """Check if recovery manager is running."""
        return self._running

    @property
    def recovery_history(self) -> List[Dict[str, Any]]:
        """Get recent recovery history."""
        return list(self._recovery_history)

    async def start(self) -> bool:
        """
        Start the recovery manager and health monitoring.

        Returns:
            True if started successfully, False otherwise
        """
        if self._running:
            logger.warning("RobotRecoveryManager already running")
            return True

        try:
            self._pool = await asyncpg.create_pool(
                self._config.postgres_url,
                min_size=self._config.pool_min_size,
                max_size=self._config.pool_max_size,
                command_timeout=30,
            )

            # Verify connection
            async with self._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")

            self._running = True
            self._monitor_task = asyncio.create_task(self._health_monitor_loop())

            logger.info("RobotRecoveryManager started")
            return True

        except Exception as e:
            logger.error(f"Failed to start RobotRecoveryManager: {e}")
            return False

    async def stop(self) -> None:
        """Stop the recovery manager and close connections."""
        logger.info("Stopping RobotRecoveryManager...")
        self._running = False

        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None

        if self._pool:
            try:
                await self._pool.close()
            except Exception as e:
                logger.warning(f"Error closing connection pool: {e}")
            self._pool = None

        logger.info("RobotRecoveryManager stopped")

    async def handle_robot_failure(self, event: RobotFailureEvent) -> List[RecoveryResult]:
        """
        Handle a robot failure event.

        Recovery algorithm:
        1. Mark robot as failed in database
        2. Find all jobs claimed by the robot
        3. For each job:
           a. Check DBOS checkpoint status
           b. If checkpoint exists and is PENDING, release job for resumption
           c. Otherwise, requeue job with retry delay or move to DLQ

        Args:
            event: Robot failure event with details

        Returns:
            List of recovery results for each affected job
        """
        if not self._pool:
            logger.error("Recovery manager not started - cannot handle failure")
            return []

        logger.warning(
            f"Handling robot failure: robot_id={event.robot_id}, "
            f"reason={event.failure_reason}, detected_at={event.detected_at.isoformat()}"
        )

        results: List[RecoveryResult] = []

        try:
            # Step 1: Mark robot as failed
            await self._mark_robot_failed(event.robot_id)

            # Step 2: Find all claimed jobs
            failed_jobs = await self._find_claimed_jobs(event.robot_id)

            if not failed_jobs:
                logger.info(f"No active jobs found for failed robot {event.robot_id}")
                return results

            logger.info(f"Found {len(failed_jobs)} jobs to recover from robot {event.robot_id}")

            # Step 3: Recover each job
            for job in failed_jobs:
                result = await self._recover_job(job, event.robot_id, event.failure_reason)
                results.append(result)

            # Record recovery event in history
            self._record_recovery_event(event, results)

            # Notify callback
            if self._on_recovery_complete:
                try:
                    self._on_recovery_complete(event.robot_id, results)
                except Exception as e:
                    logger.warning(f"Recovery complete callback error: {e}")

        except Exception as e:
            logger.exception(f"Error handling robot failure for {event.robot_id}: {e}")
            results.append(
                RecoveryResult(
                    job_id="*",
                    action=RecoveryAction.RECOVERY_FAILED,
                    success=False,
                    error=str(e),
                )
            )

        return results

    async def _mark_robot_failed(self, robot_id: str) -> bool:
        """
        Mark a robot as failed in the database.

        Args:
            robot_id: ID of the robot to mark as failed

        Returns:
            True if robot was marked, False if not found
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(self._sql_mark_robot_failed, robot_id)

            if row:
                logger.info(f"Marked robot {robot_id} as failed (name={row['name']})")
                return True
            else:
                logger.warning(f"Robot {robot_id} not found in database")
                return False

        except Exception as e:
            logger.error(f"Failed to mark robot {robot_id} as failed: {e}")
            raise

    async def _find_claimed_jobs(self, robot_id: str) -> List[FailedJobInfo]:
        """
        Find all jobs currently claimed by a robot.

        Args:
            robot_id: ID of the robot

        Returns:
            List of job information for claimed jobs
        """
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(self._sql_find_claimed_jobs, robot_id)

            jobs = []
            for row in rows:
                jobs.append(
                    FailedJobInfo(
                        job_id=str(row["id"]),
                        workflow_id=row["workflow_id"],
                        workflow_name=row["workflow_name"],
                        workflow_json=row["workflow_json"],
                        priority=row["priority"],
                        environment=row["environment"],
                        variables=row["variables"] or {},
                        retry_count=row["retry_count"],
                        max_retries=row["max_retries"],
                        created_at=row["created_at"],
                        claimed_at=row["started_at"],
                    )
                )

            return jobs

        except Exception as e:
            logger.error(f"Failed to find claimed jobs for robot {robot_id}: {e}")
            raise

    async def _recover_job(
        self,
        job: FailedJobInfo,
        robot_id: str,
        failure_reason: str,
    ) -> RecoveryResult:
        """
        Recover a single job from a failed robot.

        Recovery decision:
        - If DBOS checkpoint exists with PENDING status -> release for resumption
        - If retries remain -> requeue with exponential backoff delay
        - If max retries exceeded -> move to DLQ

        Args:
            job: Job information
            robot_id: ID of the failed robot
            failure_reason: Reason for the robot failure

        Returns:
            RecoveryResult with action taken
        """
        error_message = f"[Robot failure: {failure_reason}]"

        try:
            # Check DBOS checkpoint if enabled
            if self._config.enable_checkpoint_recovery:
                checkpoint_status = await self._get_checkpoint_status(job.job_id)

                if checkpoint_status and checkpoint_status == WorkflowCheckpointStatus.PENDING:
                    # Checkpoint exists and workflow can be resumed
                    result = await self._release_job_for_resumption(
                        job.job_id,
                        delay_seconds=self._config.default_requeue_delay_seconds,
                        error_message=f"{error_message} Resuming from checkpoint.",
                    )

                    if result:
                        logger.info(f"Job {job.job_id[:8]}... can resume from DBOS checkpoint")
                        return RecoveryResult(
                            job_id=job.job_id,
                            action=RecoveryAction.RESUMED_FROM_CHECKPOINT,
                            success=True,
                            delay_seconds=self._config.default_requeue_delay_seconds,
                            checkpoint_used=True,
                        )

            # No checkpoint or checkpoint not usable - use retry logic
            if job.retry_count < job.max_retries:
                delay = self._calculate_retry_delay(job.retry_count)
                full_error = f"{error_message} Retry {job.retry_count + 1}/{job.max_retries}."

                result = await self._requeue_job_for_retry(
                    job.job_id,
                    delay_seconds=delay,
                    error_message=full_error,
                )

                if result:
                    logger.info(
                        f"Job {job.job_id[:8]}... requeued for retry "
                        f"(attempt {job.retry_count + 1}, delay={delay}s)"
                    )
                    return RecoveryResult(
                        job_id=job.job_id,
                        action=RecoveryAction.REQUEUED_FOR_RETRY,
                        success=True,
                        delay_seconds=delay,
                    )

            # Max retries exceeded - move to DLQ
            full_error = f"{error_message} Max retries ({job.max_retries}) exceeded."
            dlq_result = await self._move_job_to_dlq(
                job.job_id,
                error_message=full_error,
                robot_id=robot_id,
            )

            if dlq_result:
                logger.warning(
                    f"Job {job.job_id[:8]}... moved to DLQ after " f"{job.retry_count} retries"
                )
                return RecoveryResult(
                    job_id=job.job_id,
                    action=RecoveryAction.MOVED_TO_DLQ,
                    success=True,
                )

            # Recovery failed
            return RecoveryResult(
                job_id=job.job_id,
                action=RecoveryAction.RECOVERY_FAILED,
                success=False,
                error="Failed to requeue or move to DLQ",
            )

        except Exception as e:
            logger.error(f"Error recovering job {job.job_id[:8]}...: {e}")
            return RecoveryResult(
                job_id=job.job_id,
                action=RecoveryAction.RECOVERY_FAILED,
                success=False,
                error=str(e),
            )

    async def _get_checkpoint_status(self, job_id: str) -> Optional[WorkflowCheckpointStatus]:
        """
        Get DBOS checkpoint status for a job.

        First tries the injected DBOS client, falls back to direct database query.

        Args:
            job_id: Job/workflow ID to check

        Returns:
            Checkpoint status if found, None otherwise
        """
        # Try DBOS client first
        if self._dbos_client:
            try:
                status_data = await self._dbos_client.get_workflow_status(job_id)
                if status_data and "status" in status_data:
                    status_str = status_data["status"].lower()
                    return WorkflowCheckpointStatus(status_str)
            except Exception as e:
                logger.debug(f"DBOS client query failed: {e}")

        # Fall back to direct database query
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(self._sql_get_checkpoint, job_id)

            if row and row["state"]:
                state_str = row["state"].lower()
                return WorkflowCheckpointStatus(state_str)

            return None

        except Exception as e:
            logger.debug(f"Checkpoint status query failed for {job_id}: {e}")
            return None

    async def _release_job_for_resumption(
        self,
        job_id: str,
        delay_seconds: int,
        error_message: str,
    ) -> bool:
        """
        Release a job back to the queue for checkpoint-based resumption.

        Args:
            job_id: Job ID to release
            delay_seconds: Delay before job becomes visible
            error_message: Message to append to job

        Returns:
            True if job was released, False otherwise
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    self._sql_release_job,
                    job_id,
                    delay_seconds,
                    f" {error_message}",
                )

            return row is not None

        except Exception as e:
            logger.error(f"Failed to release job {job_id} for resumption: {e}")
            return False

    async def _requeue_job_for_retry(
        self,
        job_id: str,
        delay_seconds: int,
        error_message: str,
    ) -> bool:
        """
        Requeue a job for retry with delay.

        Args:
            job_id: Job ID to requeue
            delay_seconds: Delay before job becomes visible
            error_message: Error message to record

        Returns:
            True if job was requeued, False otherwise
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    self._sql_requeue_with_retry,
                    job_id,
                    delay_seconds,
                    error_message,
                )

            if row:
                new_status = row["status"]
                return new_status == "pending"

            return False

        except Exception as e:
            logger.error(f"Failed to requeue job {job_id}: {e}")
            return False

    async def _move_job_to_dlq(
        self,
        job_id: str,
        error_message: str,
        robot_id: str,
    ) -> bool:
        """
        Move a job to the dead letter queue.

        Args:
            job_id: Job ID to move
            error_message: Final error message
            robot_id: ID of the robot that failed

        Returns:
            True if job was moved to DLQ, False otherwise
        """
        try:
            async with self._pool.acquire() as conn:
                async with conn.transaction():
                    # Insert into DLQ
                    dlq_row = await conn.fetchrow(
                        self._sql_move_to_dlq,
                        job_id,
                        error_message,
                        robot_id,
                    )

                    if dlq_row:
                        # Delete from job queue
                        await conn.execute(self._sql_delete_failed, job_id)
                        return True

            return False

        except Exception as e:
            logger.error(f"Failed to move job {job_id} to DLQ: {e}")
            return False

    def _calculate_retry_delay(self, retry_count: int) -> int:
        """
        Calculate retry delay with exponential backoff and jitter.

        Args:
            retry_count: Current retry count (0-based)

        Returns:
            Delay in seconds
        """
        delays = self._config.retry_delays

        if retry_count < len(delays):
            base_delay = delays[retry_count]
        else:
            # Use last delay for additional retries
            base_delay = delays[-1] if delays else self._config.default_requeue_delay_seconds

        # Add jitter (+/- 20%)
        jitter_factor = random.uniform(0.8, 1.2)
        delay = int(base_delay * jitter_factor)

        return max(1, delay)  # Minimum 1 second delay

    async def _health_monitor_loop(self) -> None:
        """
        Background loop for detecting robot failures via heartbeat timeout.

        Periodically checks for robots that have exceeded the heartbeat timeout
        and initiates recovery for their jobs.
        """
        logger.debug("Health monitor loop started")

        while self._running:
            try:
                await asyncio.sleep(self._config.monitor_interval_seconds)

                if not self._running:
                    break

                await self._check_for_stale_robots()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor loop error: {e}")
                await asyncio.sleep(5)

        logger.debug("Health monitor loop stopped")

    async def _check_for_stale_robots(self) -> None:
        """
        Check for robots that have exceeded heartbeat timeout.

        Automatically initiates recovery for any stale robots found.
        """
        if not self._pool:
            return

        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(
                    self._sql_find_stale_robots,
                    self._config.heartbeat_timeout_seconds,
                )

            for row in rows:
                robot_id = str(row["id"])
                robot_name = row["name"]
                last_heartbeat = row["last_heartbeat"]

                logger.warning(
                    f"Detected stale robot: {robot_name} ({robot_id}) "
                    f"last_heartbeat={last_heartbeat}"
                )

                # Get active jobs for this robot
                async with self._pool.acquire() as conn:
                    job_rows = await conn.fetch(self._sql_get_robot_jobs, robot_id)

                active_job_ids = [str(r["id"]) for r in job_rows]

                # Create failure event
                event = RobotFailureEvent(
                    robot_id=robot_id,
                    detected_at=datetime.now(timezone.utc),
                    last_heartbeat=last_heartbeat,
                    failure_reason=f"Heartbeat timeout (>{self._config.heartbeat_timeout_seconds}s)",
                    active_job_ids=active_job_ids,
                )

                # Notify callback
                if self._on_failure_detected:
                    try:
                        self._on_failure_detected(event)
                    except Exception as e:
                        logger.warning(f"Failure detected callback error: {e}")

                # Handle recovery
                await self.handle_robot_failure(event)

        except Exception as e:
            logger.error(f"Error checking for stale robots: {e}")

    def _record_recovery_event(
        self,
        event: RobotFailureEvent,
        results: List[RecoveryResult],
    ) -> None:
        """Record a recovery event in history."""
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "robot_id": event.robot_id,
            "failure_reason": event.failure_reason,
            "jobs_recovered": len(results),
            "jobs_succeeded": sum(1 for r in results if r.success),
            "jobs_failed": sum(1 for r in results if not r.success),
            "actions": {
                action.value: sum(1 for r in results if r.action == action)
                for action in RecoveryAction
            },
        }

        self._recovery_history.append(record)

        # Trim history
        if len(self._recovery_history) > self._max_history:
            self._recovery_history = self._recovery_history[-self._max_history :]

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get recovery manager statistics.

        Returns:
            Dict with recovery statistics
        """
        total_recoveries = len(self._recovery_history)
        total_jobs = sum(r["jobs_recovered"] for r in self._recovery_history)
        successful_jobs = sum(r["jobs_succeeded"] for r in self._recovery_history)

        action_counts: Dict[str, int] = {}
        for record in self._recovery_history:
            for action, count in record["actions"].items():
                action_counts[action] = action_counts.get(action, 0) + count

        return {
            "is_running": self._running,
            "total_recovery_events": total_recoveries,
            "total_jobs_processed": total_jobs,
            "successful_recoveries": successful_jobs,
            "failed_recoveries": total_jobs - successful_jobs,
            "success_rate": (successful_jobs / total_jobs * 100) if total_jobs > 0 else 0.0,
            "action_breakdown": action_counts,
            "config": {
                "heartbeat_timeout_seconds": self._config.heartbeat_timeout_seconds,
                "max_retries": self._config.max_retries,
                "checkpoint_recovery_enabled": self._config.enable_checkpoint_recovery,
                "monitor_interval_seconds": self._config.monitor_interval_seconds,
            },
        }

    async def manually_recover_robot(
        self, robot_id: str, reason: str = "Manual recovery"
    ) -> List[RecoveryResult]:
        """
        Manually trigger recovery for a specific robot.

        Useful for administrative actions or testing.

        Args:
            robot_id: ID of the robot to recover
            reason: Reason for the manual recovery

        Returns:
            List of recovery results
        """
        event = RobotFailureEvent(
            robot_id=robot_id,
            detected_at=datetime.now(timezone.utc),
            last_heartbeat=None,
            failure_reason=reason,
        )

        return await self.handle_robot_failure(event)

    async def __aenter__(self) -> "RobotRecoveryManager":
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
