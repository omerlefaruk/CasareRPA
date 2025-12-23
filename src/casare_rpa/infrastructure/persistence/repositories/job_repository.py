"""
JobRepository - PostgreSQL persistence for Job entities.

Provides CRUD operations for job execution tracking, status management,
and workflow-based queries using asyncpg connection pooling.
"""

from datetime import datetime
from typing import Any

import orjson
from loguru import logger

from casare_rpa.domain.orchestrator.entities.job import (
    Job,
    JobPriority,
    JobStatus,
)
from casare_rpa.utils.pooling.database_pool import DatabasePoolManager


class JobRepository:
    """
    Repository for Job entity persistence.

    Uses asyncpg with connection pooling for efficient database operations.
    Maps between Job domain entity and PostgreSQL jobs table.
    """

    def __init__(self, pool_manager: DatabasePoolManager | None = None) -> None:
        """
        Initialize repository with optional pool manager.

        Args:
            pool_manager: Database pool manager. If None, will fetch from singleton.
        """
        self._pool_manager = pool_manager
        self._pool_name = "casare_rpa"

    async def _get_pool(self):
        """Get database connection pool."""
        if self._pool_manager is None:
            from casare_rpa.utils.pooling.database_pool import get_pool_manager

            self._pool_manager = await get_pool_manager()
        return await self._pool_manager.get_pool(self._pool_name, db_type="postgresql")

    async def _get_connection(self):
        """Acquire a connection from the pool."""
        pool = await self._get_pool()
        return await pool.acquire()

    async def _release_connection(self, conn) -> None:
        """Release connection back to pool."""
        pool = await self._get_pool()
        await pool.release(conn)

    def _row_to_job(self, row: dict[str, Any]) -> Job:
        """
        Convert database row to Job domain entity.

        Args:
            row: asyncpg Record or dict from database query.

        Returns:
            Job domain entity.
        """
        # Parse status enum
        status_str = row.get("status", "pending")
        try:
            status = JobStatus(status_str)
        except ValueError:
            logger.warning(f"Unknown job status: {status_str}, defaulting to pending")
            status = JobStatus.PENDING

        # Parse priority enum
        priority_val = row.get("priority", 1)
        try:
            if isinstance(priority_val, int):
                priority = JobPriority(priority_val)
            elif isinstance(priority_val, str):
                priority = JobPriority[priority_val.upper()]
            else:
                priority = JobPriority.NORMAL
        except (ValueError, KeyError):
            priority = JobPriority.NORMAL

        # Parse result from JSONB
        result = row.get("result", {})
        if isinstance(result, str):
            result = orjson.loads(result) if result else {}

        # Parse payload from JSONB (maps to workflow_json in domain)
        payload = row.get("payload", {})
        if isinstance(payload, str):
            payload = orjson.loads(payload) if payload else {}
        workflow_json = orjson.dumps(payload).decode() if payload else "{}"

        return Job(
            id=str(row["job_id"]),
            workflow_id=str(row["workflow_id"]) if row.get("workflow_id") else "",
            workflow_name=row.get("workflow_name", ""),
            robot_id=str(row["robot_uuid"]) if row.get("robot_uuid") else "",
            robot_name=row.get("robot_name", ""),
            status=status,
            priority=priority,
            environment=row.get("environment", "default"),
            workflow_json=workflow_json,
            scheduled_time=row.get("scheduled_time"),
            started_at=row.get("started_at"),
            completed_at=row.get("completed_at"),
            duration_ms=row.get("duration_ms", 0) or 0,
            progress=row.get("progress", 0) or 0,
            current_node=row.get("current_node", "") or "",
            result=result,
            logs=row.get("logs", "") or "",
            error_message=row.get("error_message", "") or "",
            created_at=row.get("created_at"),
            created_by=row.get("created_by", "") or "",
        )

    def _job_to_params(self, job: Job) -> dict[str, Any]:
        """
        Convert Job entity to database parameters.

        Args:
            job: Job domain entity.

        Returns:
            Dictionary of database column values.
        """
        # Convert workflow_json to payload JSONB
        try:
            payload = orjson.loads(job.workflow_json) if job.workflow_json else {}
        except (orjson.JSONDecodeError, TypeError):
            payload = {}

        return {
            "job_id": job.id,
            "workflow_id": job.workflow_id if job.workflow_id else None,
            "workflow_name": job.workflow_name,
            "robot_uuid": job.robot_id if job.robot_id else None,
            "status": job.status.value,
            "priority": job.priority.value,
            "environment": job.environment,
            "payload": orjson.dumps(payload).decode(),
            "scheduled_time": job.scheduled_time,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "duration_ms": job.duration_ms,
            "progress": job.progress,
            "current_node": job.current_node,
            "result": orjson.dumps(job.result).decode(),
            "logs": job.logs,
            "error_message": job.error_message,
            "created_at": job.created_at or datetime.utcnow(),
            "created_by": job.created_by,
        }

    async def save(self, job: Job) -> Job:
        """
        Save or update a job.

        Uses upsert (INSERT ON CONFLICT UPDATE) for idempotent saves.

        Args:
            job: Job entity to save.

        Returns:
            Saved job entity with any server-generated fields.
        """
        conn = await self._get_connection()
        try:
            params = self._job_to_params(job)
            await conn.execute(
                """
                INSERT INTO jobs (
                    job_id, workflow_id, workflow_name, robot_uuid, status,
                    priority, environment, payload, scheduled_time,
                    started_at, completed_at, duration_ms, progress,
                    current_node, result, logs, error_message, created_at, created_by
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9,
                    $10, $11, $12, $13, $14, $15::jsonb, $16, $17, $18, $19
                )
                ON CONFLICT (job_id) DO UPDATE SET
                    workflow_id = EXCLUDED.workflow_id,
                    workflow_name = EXCLUDED.workflow_name,
                    robot_uuid = EXCLUDED.robot_uuid,
                    status = EXCLUDED.status,
                    priority = EXCLUDED.priority,
                    environment = EXCLUDED.environment,
                    payload = EXCLUDED.payload,
                    scheduled_time = EXCLUDED.scheduled_time,
                    started_at = EXCLUDED.started_at,
                    completed_at = EXCLUDED.completed_at,
                    duration_ms = EXCLUDED.duration_ms,
                    progress = EXCLUDED.progress,
                    current_node = EXCLUDED.current_node,
                    result = EXCLUDED.result,
                    logs = EXCLUDED.logs,
                    error_message = EXCLUDED.error_message,
                    updated_at = NOW()
                """,
                params["job_id"],
                params["workflow_id"],
                params["workflow_name"],
                params["robot_uuid"],
                params["status"],
                params["priority"],
                params["environment"],
                params["payload"],
                params["scheduled_time"],
                params["started_at"],
                params["completed_at"],
                params["duration_ms"],
                params["progress"],
                params["current_node"],
                params["result"],
                params["logs"],
                params["error_message"],
                params["created_at"],
                params["created_by"],
            )
            logger.debug(f"Saved job: {job.id}")
            return job
        except Exception as e:
            logger.error(f"Failed to save job {job.id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def get_by_id(self, job_id: str) -> Job | None:
        """
        Get job by ID.

        Args:
            job_id: UUID of the job.

        Returns:
            Job entity or None if not found.
        """
        conn = await self._get_connection()
        try:
            row = await conn.fetchrow("SELECT * FROM jobs WHERE job_id = $1", job_id)
            if row is None:
                return None
            return self._row_to_job(dict(row))
        except Exception as e:
            logger.error(f"Failed to get job {job_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def get_by_robot(self, robot_id: str) -> list[Job]:
        """
        Get jobs assigned to a robot.

        Args:
            robot_id: UUID of the robot.

        Returns:
            List of jobs for the robot.
        """
        conn = await self._get_connection()
        try:
            rows = await conn.fetch(
                """
                SELECT * FROM jobs
                WHERE robot_uuid = $1
                ORDER BY created_at DESC
                """,
                robot_id,
            )
            return [self._row_to_job(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get jobs for robot {robot_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def get_by_workflow(self, workflow_id: str) -> list[Job]:
        """
        Get jobs for a workflow.

        Args:
            workflow_id: UUID of the workflow.

        Returns:
            List of jobs for the workflow.
        """
        conn = await self._get_connection()
        try:
            rows = await conn.fetch(
                """
                SELECT * FROM jobs
                WHERE workflow_id = $1
                ORDER BY created_at DESC
                """,
                workflow_id,
            )
            return [self._row_to_job(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get jobs for workflow {workflow_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def get_by_status(self, status: JobStatus) -> list[Job]:
        """
        Get jobs by status.

        Args:
            status: Job status to filter by.

        Returns:
            List of jobs with matching status.
        """
        conn = await self._get_connection()
        try:
            rows = await conn.fetch(
                """
                SELECT * FROM jobs
                WHERE status = $1
                ORDER BY priority DESC, created_at ASC
                """,
                status.value,
            )
            return [self._row_to_job(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get jobs by status {status}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def get_pending(self) -> list[Job]:
        """
        Get pending jobs ordered by priority and creation time.

        Returns:
            List of pending Job entities.
        """
        return await self.get_by_status(JobStatus.PENDING)

    async def get_queued(self) -> list[Job]:
        """
        Get queued jobs ordered by priority and creation time.

        Returns:
            List of queued Job entities.
        """
        return await self.get_by_status(JobStatus.QUEUED)

    async def get_running(self) -> list[Job]:
        """
        Get running jobs.

        Returns:
            List of running Job entities.
        """
        return await self.get_by_status(JobStatus.RUNNING)

    async def get_pending_for_robot(self, robot_id: str) -> list[Job]:
        """
        Get pending jobs assigned to a specific robot.

        Args:
            robot_id: UUID of the robot.

        Returns:
            List of pending jobs for the robot.
        """
        conn = await self._get_connection()
        try:
            rows = await conn.fetch(
                """
                SELECT * FROM jobs
                WHERE robot_uuid = $1
                AND status IN ('pending', 'queued')
                ORDER BY priority DESC, created_at ASC
                """,
                robot_id,
            )
            return [self._row_to_job(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get pending jobs for robot {robot_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def update_status(
        self,
        job_id: str,
        status: JobStatus,
        result: dict[str, Any] | None = None,
        error_message: str | None = None,
    ) -> None:
        """
        Update job status with optional result/error.

        Args:
            job_id: UUID of the job.
            status: New status.
            result: Optional result dictionary for completed jobs.
            error_message: Optional error message for failed jobs.
        """
        conn = await self._get_connection()
        try:
            now = datetime.utcnow()

            # Build dynamic update
            updates = ["status = $2", "updated_at = NOW()"]
            params: list[Any] = [job_id, status.value]
            param_idx = 3

            if status == JobStatus.RUNNING:
                updates.append(f"started_at = ${param_idx}")
                params.append(now)
                param_idx += 1

            if status in (
                JobStatus.COMPLETED,
                JobStatus.FAILED,
                JobStatus.CANCELLED,
                JobStatus.TIMEOUT,
            ):
                updates.append(f"completed_at = ${param_idx}")
                params.append(now)
                param_idx += 1

            if result is not None:
                updates.append(f"result = ${param_idx}::jsonb")
                params.append(orjson.dumps(result).decode())
                param_idx += 1

            if error_message is not None:
                updates.append(f"error_message = ${param_idx}")
                params.append(error_message)
                param_idx += 1

            query = f"UPDATE jobs SET {', '.join(updates)} WHERE job_id = $1"
            await conn.execute(query, *params)
            logger.debug(f"Updated job {job_id} status to {status.value}")
        except Exception as e:
            logger.error(f"Failed to update status for job {job_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def update_progress(self, job_id: str, progress: int, current_node: str = "") -> None:
        """
        Update job progress.

        Args:
            job_id: UUID of the job.
            progress: Progress percentage (0-100).
            current_node: Currently executing node ID.
        """
        conn = await self._get_connection()
        try:
            await conn.execute(
                """
                UPDATE jobs
                SET progress = $2, current_node = $3, updated_at = NOW()
                WHERE job_id = $1
                """,
                job_id,
                max(0, min(100, progress)),
                current_node,
            )
            logger.debug(f"Updated job {job_id} progress to {progress}%")
        except Exception as e:
            logger.error(f"Failed to update progress for job {job_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def append_logs(self, job_id: str, log_entry: str) -> None:
        """
        Append to job logs.

        Args:
            job_id: UUID of the job.
            log_entry: Log text to append.
        """
        conn = await self._get_connection()
        try:
            await conn.execute(
                """
                UPDATE jobs
                SET logs = logs || $2, updated_at = NOW()
                WHERE job_id = $1
                """,
                job_id,
                log_entry + "\n",
            )
        except Exception as e:
            logger.error(f"Failed to append logs for job {job_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def calculate_duration(self, job_id: str) -> None:
        """
        Calculate and update job duration based on started_at and completed_at.

        Args:
            job_id: UUID of the job.
        """
        conn = await self._get_connection()
        try:
            await conn.execute(
                """
                UPDATE jobs
                SET duration_ms = EXTRACT(EPOCH FROM (completed_at - started_at)) * 1000
                WHERE job_id = $1
                AND started_at IS NOT NULL
                AND completed_at IS NOT NULL
                """,
                job_id,
            )
        except Exception as e:
            logger.error(f"Failed to calculate duration for job {job_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def delete(self, job_id: str) -> bool:
        """
        Delete a job.

        Args:
            job_id: UUID of the job to delete.

        Returns:
            True if deleted, False if not found.
        """
        conn = await self._get_connection()
        try:
            result = await conn.execute("DELETE FROM jobs WHERE job_id = $1", job_id)
            deleted = result.split()[-1] != "0"
            if deleted:
                logger.info(f"Deleted job: {job_id}")
            return deleted
        except Exception as e:
            logger.error(f"Failed to delete job {job_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def delete_old_jobs(self, days: int = 30) -> int:
        """
        Delete completed/failed jobs older than specified days.

        Args:
            days: Age threshold in days.

        Returns:
            Number of jobs deleted.
        """
        conn = await self._get_connection()
        try:
            result = await conn.execute(
                """
                DELETE FROM jobs
                WHERE status IN ('completed', 'failed', 'cancelled', 'timeout')
                AND created_at < NOW() - $1 * INTERVAL '1 day'
                """,
                days,
            )
            count = int(result.split()[-1])
            if count > 0:
                logger.info(f"Deleted {count} old jobs (older than {days} days)")
            return count
        except Exception as e:
            logger.error(f"Failed to delete old jobs: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def claim_next_job(self, robot_id: str) -> Job | None:
        """
        Atomically claim the next pending job for a robot.

        Uses SELECT FOR UPDATE SKIP LOCKED for safe concurrent access.

        Args:
            robot_id: UUID of the claiming robot.

        Returns:
            Claimed job or None if no jobs available.
        """
        conn = await self._get_connection()
        try:
            # Use transaction with row locking
            async with conn.transaction():
                row = await conn.fetchrow(
                    """
                    SELECT * FROM jobs
                    WHERE status = 'pending'
                    AND (robot_uuid IS NULL OR robot_uuid = $1)
                    ORDER BY priority DESC, created_at ASC
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED
                    """,
                    robot_id,
                )
                if row is None:
                    return None

                job_id = str(row["job_id"])
                await conn.execute(
                    """
                    UPDATE jobs
                    SET status = 'queued',
                        robot_uuid = $2,
                        updated_at = NOW()
                    WHERE job_id = $1
                    """,
                    job_id,
                    robot_id,
                )

                # Fetch updated job
                updated_row = await conn.fetchrow("SELECT * FROM jobs WHERE job_id = $1", job_id)
                return self._row_to_job(dict(updated_row))
        except Exception as e:
            logger.error(f"Failed to claim job for robot {robot_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)


__all__ = ["JobRepository"]
