"""
Offline Job Queue for Robot Agent.

Provides local SQLite-based job caching for when the robot loses
connection to the backend. Jobs in progress are cached and can
be resumed or synced when connection is restored.

Features:
- Cache in-progress jobs when connection drops
- Queue completed jobs for sync when reconnected
- Persist job state across robot restarts
- Track job execution history locally
"""

import asyncio
import sqlite3
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from loguru import logger
import orjson


class CachedJobStatus(Enum):
    """Status of cached jobs."""

    CACHED = "cached"  # Job cached from backend
    IN_PROGRESS = "in_progress"  # Currently executing
    COMPLETED = "completed"  # Execution completed, pending sync
    FAILED = "failed"  # Execution failed, pending sync
    SYNCED = "synced"  # Successfully synced to backend


class OfflineQueue:
    """
    SQLite-based offline job queue.

    Caches jobs locally when the robot is disconnected from the backend.
    """

    def __init__(
        self,
        db_path: Optional[Path] = None,
        robot_id: Optional[str] = None,
    ):
        """
        Initialize offline queue.

        Args:
            db_path: Path to SQLite database file
            robot_id: Robot identifier for filtering jobs
        """
        if db_path is None:
            db_path = Path.home() / ".casare_rpa" / "offline_queue.db"

        self.db_path = db_path
        self.robot_id = robot_id

        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_db()

        logger.info(f"Offline queue initialized at {self.db_path}")

    @contextmanager
    def _get_connection(self):
        """Get database connection with automatic cleanup."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Jobs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cached_jobs (
                    id TEXT PRIMARY KEY,
                    robot_id TEXT,
                    workflow_json TEXT NOT NULL,
                    original_status TEXT,
                    cached_status TEXT NOT NULL DEFAULT 'cached',
                    cached_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    result TEXT,
                    logs TEXT,
                    error TEXT,
                    sync_attempts INTEGER DEFAULT 0,
                    last_sync_attempt TEXT
                )
            """)

            # Checkpoints table for resumable execution
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS job_checkpoints (
                    job_id TEXT NOT NULL,
                    checkpoint_id TEXT NOT NULL,
                    node_id TEXT NOT NULL,
                    state_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (job_id, checkpoint_id),
                    FOREIGN KEY (job_id) REFERENCES cached_jobs(id)
                )
            """)

            # Execution history for audit
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS execution_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    event_data TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (job_id) REFERENCES cached_jobs(id)
                )
            """)

            # Index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_cached_jobs_status
                ON cached_jobs(cached_status)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_cached_jobs_robot
                ON cached_jobs(robot_id)
            """)

            conn.commit()

    async def cache_job(
        self,
        job_id: str,
        workflow_json: str,
        original_status: str = "pending",
    ) -> bool:
        """
        Cache a job from the backend.

        Args:
            job_id: Job identifier
            workflow_json: Workflow JSON string
            original_status: Status from backend

        Returns:
            True if cached successfully
        """

        def _insert():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO cached_jobs
                    (id, robot_id, workflow_json, original_status, cached_status, cached_at)
                    VALUES (?, ?, ?, ?, 'cached', ?)
                """,
                    (
                        job_id,
                        self.robot_id,
                        workflow_json,
                        original_status,
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )
                conn.commit()

        try:
            await asyncio.to_thread(_insert)
            logger.info(f"Job {job_id} cached locally")
            return True
        except Exception as e:
            logger.error(f"Failed to cache job {job_id}: {e}")
            return False

    async def mark_in_progress(self, job_id: str) -> bool:
        """Mark a cached job as in progress."""

        def _update():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE cached_jobs
                    SET cached_status = 'in_progress', started_at = ?
                    WHERE id = ?
                """,
                    (datetime.now(timezone.utc).isoformat(), job_id),
                )
                conn.commit()
                return cursor.rowcount > 0

        try:
            return await asyncio.to_thread(_update)
        except Exception as e:
            logger.error(f"Failed to mark job {job_id} in progress: {e}")
            return False

    async def mark_completed(
        self,
        job_id: str,
        success: bool,
        result: Optional[Dict] = None,
        logs: Optional[str] = None,
        error: Optional[str] = None,
    ) -> bool:
        """
        Mark a cached job as completed.

        Args:
            job_id: Job identifier
            success: Whether execution succeeded
            result: Execution result data
            logs: Execution logs
            error: Error message if failed
        """

        def _update():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                status = "completed" if success else "failed"
                cursor.execute(
                    """
                    UPDATE cached_jobs
                    SET cached_status = ?,
                        completed_at = ?,
                        result = ?,
                        logs = ?,
                        error = ?
                    WHERE id = ?
                """,
                    (
                        status,
                        datetime.now(timezone.utc).isoformat(),
                        orjson.dumps(result).decode() if result else None,
                        logs,
                        error,
                        job_id,
                    ),
                )
                conn.commit()
                return cursor.rowcount > 0

        try:
            return await asyncio.to_thread(_update)
        except Exception as e:
            logger.error(f"Failed to mark job {job_id} completed: {e}")
            return False

    async def get_jobs_to_sync(self) -> List[Dict]:
        """Get all completed/failed jobs pending sync to backend."""

        def _query():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM cached_jobs
                    WHERE cached_status IN ('completed', 'failed')
                    AND (robot_id = ? OR robot_id IS NULL)
                    ORDER BY completed_at ASC
                """,
                    (self.robot_id,),
                )
                return [dict(row) for row in cursor.fetchall()]

        try:
            return await asyncio.to_thread(_query)
        except Exception as e:
            logger.error(f"Failed to get jobs to sync: {e}")
            return []

    async def mark_synced(self, job_id: str) -> bool:
        """Mark a job as synced to backend."""

        def _update():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE cached_jobs
                    SET cached_status = 'synced', last_sync_attempt = ?
                    WHERE id = ?
                """,
                    (datetime.now(timezone.utc).isoformat(), job_id),
                )
                conn.commit()
                return cursor.rowcount > 0

        try:
            return await asyncio.to_thread(_update)
        except Exception as e:
            logger.error(f"Failed to mark job {job_id} synced: {e}")
            return False

    async def increment_sync_attempts(self, job_id: str) -> bool:
        """Increment sync attempt counter for a job."""

        def _update():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE cached_jobs
                    SET sync_attempts = sync_attempts + 1, last_sync_attempt = ?
                    WHERE id = ?
                """,
                    (datetime.now(timezone.utc).isoformat(), job_id),
                )
                conn.commit()
                return cursor.rowcount > 0

        try:
            return await asyncio.to_thread(_update)
        except Exception as e:
            logger.error(f"Failed to increment sync attempts for {job_id}: {e}")
            return False

    async def get_in_progress_jobs(self) -> List[Dict]:
        """Get jobs that were in progress (for crash recovery)."""

        def _query():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM cached_jobs
                    WHERE cached_status = 'in_progress'
                    AND (robot_id = ? OR robot_id IS NULL)
                """,
                    (self.robot_id,),
                )
                return [dict(row) for row in cursor.fetchall()]

        try:
            return await asyncio.to_thread(_query)
        except Exception as e:
            logger.error(f"Failed to get in-progress jobs: {e}")
            return []

    async def get_cached_jobs(self) -> List[Dict]:
        """Get all cached jobs not yet started."""

        def _query():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM cached_jobs
                    WHERE cached_status = 'cached'
                    AND (robot_id = ? OR robot_id IS NULL)
                    ORDER BY cached_at ASC
                """,
                    (self.robot_id,),
                )
                return [dict(row) for row in cursor.fetchall()]

        try:
            return await asyncio.to_thread(_query)
        except Exception as e:
            logger.error(f"Failed to get cached jobs: {e}")
            return []

    # Checkpoint methods for resumable execution

    async def save_checkpoint(
        self,
        job_id: str,
        checkpoint_id: str,
        node_id: str,
        state: Dict[str, Any],
    ) -> bool:
        """
        Save execution checkpoint for a job.

        Args:
            job_id: Job identifier
            checkpoint_id: Unique checkpoint identifier
            node_id: ID of the node that just completed
            state: Execution state to save
        """

        def _insert():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO job_checkpoints
                    (job_id, checkpoint_id, node_id, state_json, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        job_id,
                        checkpoint_id,
                        node_id,
                        orjson.dumps(state).decode(),
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )
                conn.commit()

        try:
            await asyncio.to_thread(_insert)
            logger.debug(f"Checkpoint saved for job {job_id} at node {node_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save checkpoint for job {job_id}: {e}")
            return False

    async def get_latest_checkpoint(self, job_id: str) -> Optional[Dict]:
        """Get the latest checkpoint for a job."""

        def _query():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM job_checkpoints
                    WHERE job_id = ?
                    ORDER BY created_at DESC
                    LIMIT 1
                """,
                    (job_id,),
                )
                row = cursor.fetchone()
                if row:
                    result = dict(row)
                    result["state"] = orjson.loads(result["state_json"])
                    return result
                return None

        try:
            return await asyncio.to_thread(_query)
        except Exception as e:
            logger.error(f"Failed to get checkpoint for job {job_id}: {e}")
            return None

    async def clear_checkpoints(self, job_id: str) -> bool:
        """Clear all checkpoints for a job."""

        def _delete():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    DELETE FROM job_checkpoints WHERE job_id = ?
                """,
                    (job_id,),
                )
                conn.commit()
                return True

        try:
            return await asyncio.to_thread(_delete)
        except Exception as e:
            logger.error(f"Failed to clear checkpoints for job {job_id}: {e}")
            return False

    # History methods for audit logging

    async def log_event(
        self,
        job_id: str,
        event_type: str,
        event_data: Optional[Dict] = None,
    ) -> bool:
        """Log an event for a job."""

        def _insert():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO execution_history
                    (job_id, event_type, event_data, created_at)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        job_id,
                        event_type,
                        orjson.dumps(event_data).decode() if event_data else None,
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )
                conn.commit()

        try:
            await asyncio.to_thread(_insert)
            return True
        except Exception as e:
            logger.error(f"Failed to log event for job {job_id}: {e}")
            return False

    async def get_job_history(self, job_id: str) -> List[Dict]:
        """Get execution history for a job."""

        def _query():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM execution_history
                    WHERE job_id = ?
                    ORDER BY created_at ASC
                """,
                    (job_id,),
                )
                results = []
                for row in cursor.fetchall():
                    item = dict(row)
                    if item.get("event_data"):
                        item["event_data"] = orjson.loads(item["event_data"])
                    results.append(item)
                return results

        try:
            return await asyncio.to_thread(_query)
        except Exception as e:
            logger.error(f"Failed to get history for job {job_id}: {e}")
            return []

    # Cleanup methods

    async def cleanup_old_synced_jobs(self, days: int = 7) -> int:
        """Remove synced jobs older than specified days."""

        def _delete():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cutoff = datetime.now(timezone.utc).isoformat()
                # Simple approach: delete by number of days
                cursor.execute(
                    """
                    DELETE FROM cached_jobs
                    WHERE cached_status = 'synced'
                    AND julianday(?) - julianday(completed_at) > ?
                """,
                    (cutoff, days),
                )
                deleted = cursor.rowcount
                conn.commit()
                return deleted

        try:
            deleted = await asyncio.to_thread(_delete)
            if deleted > 0:
                logger.info(f"Cleaned up {deleted} old synced jobs")
            return deleted
        except Exception as e:
            logger.error(f"Failed to cleanup old jobs: {e}")
            return 0

    async def get_queue_stats(self) -> Dict[str, int]:
        """Get statistics about the queue."""

        def _query():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT cached_status, COUNT(*) as count
                    FROM cached_jobs
                    WHERE robot_id = ? OR robot_id IS NULL
                    GROUP BY cached_status
                """,
                    (self.robot_id,),
                )
                return {row["cached_status"]: row["count"] for row in cursor.fetchall()}

        try:
            return await asyncio.to_thread(_query)
        except Exception as e:
            logger.error(f"Failed to get queue stats: {e}")
            return {}
