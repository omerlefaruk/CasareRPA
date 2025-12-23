"""
LogRepository - PostgreSQL persistence for Robot Logs.

Provides efficient storage and retrieval of robot log entries with
30-day retention policy support. Uses asyncpg connection pooling
and leverages PostgreSQL partitioning for efficient cleanup.
"""

from datetime import UTC, datetime, timezone
from typing import Any, Dict, List, Optional

import orjson
from loguru import logger

from casare_rpa.domain.value_objects.log_entry import (
    DEFAULT_LOG_RETENTION_DAYS,
    LogEntry,
    LogLevel,
    LogQuery,
    LogStats,
)
from casare_rpa.utils.pooling.database_pool import DatabasePoolManager


class LogRepository:
    """
    Repository for Robot Log persistence.

    Uses asyncpg with connection pooling for efficient database operations.
    Leverages PostgreSQL partitioning for automatic retention management.
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

    async def save(self, entry: LogEntry) -> LogEntry:
        """
        Save a single log entry.

        Args:
            entry: LogEntry to save.

        Returns:
            Saved LogEntry.
        """
        conn = await self._get_connection()
        try:
            await conn.execute(
                """
                INSERT INTO robot_logs (
                    id, robot_id, tenant_id, timestamp, level,
                    message, source, extra, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9)
                """,
                entry.id,
                entry.robot_id,
                entry.tenant_id,
                entry.timestamp,
                entry.level.value,
                entry.message,
                entry.source,
                orjson.dumps(entry.extra or {}).decode(),
                datetime.now(UTC),
            )
            logger.debug(f"Saved log entry: {entry.id}")
            return entry
        except Exception as e:
            logger.error(f"Failed to save log entry {entry.id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def save_batch(self, entries: list[LogEntry]) -> int:
        """
        Save multiple log entries in a batch.

        Uses COPY for efficient bulk insert.

        Args:
            entries: List of LogEntry objects to save.

        Returns:
            Number of entries saved.
        """
        if not entries:
            return 0

        conn = await self._get_connection()
        try:
            # Prepare records for bulk insert
            records = [
                (
                    entry.id,
                    entry.robot_id,
                    entry.tenant_id,
                    entry.timestamp,
                    entry.level.value,
                    entry.message,
                    entry.source,
                    orjson.dumps(entry.extra or {}).decode(),
                    datetime.now(UTC),
                )
                for entry in entries
            ]

            # Use executemany for batch insert
            await conn.executemany(
                """
                INSERT INTO robot_logs (
                    id, robot_id, tenant_id, timestamp, level,
                    message, source, extra, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9)
                ON CONFLICT (id, timestamp) DO NOTHING
                """,
                records,
            )

            logger.debug(f"Saved batch of {len(entries)} log entries")
            return len(entries)
        except Exception as e:
            logger.error(f"Failed to save log batch: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def query(self, query: LogQuery) -> list[LogEntry]:
        """
        Query log entries with filtering.

        Uses the query_robot_logs PostgreSQL function for efficient filtering.

        Args:
            query: LogQuery with filter parameters.

        Returns:
            List of matching LogEntry objects.
        """
        conn = await self._get_connection()
        try:
            rows = await conn.fetch(
                """
                SELECT * FROM query_robot_logs(
                    $1, $2, $3, $4, $5, $6, $7, $8, $9
                )
                """,
                query.tenant_id,
                query.robot_id,
                query.start_time,
                query.end_time,
                query.min_level.value,
                query.source,
                query.search_text,
                query.limit,
                query.offset,
            )

            return [self._row_to_entry(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Failed to query logs: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def get_by_robot(
        self,
        robot_id: str,
        tenant_id: str,
        limit: int = 100,
        min_level: LogLevel = LogLevel.DEBUG,
    ) -> list[LogEntry]:
        """
        Get recent logs for a specific robot.

        Args:
            robot_id: Robot UUID.
            tenant_id: Tenant UUID.
            limit: Maximum number of logs to return.
            min_level: Minimum log level to include.

        Returns:
            List of LogEntry objects, most recent first.
        """
        query = LogQuery(
            tenant_id=tenant_id,
            robot_id=robot_id,
            min_level=min_level,
            limit=limit,
        )
        return await self.query(query)

    async def get_stats(self, tenant_id: str, robot_id: str | None = None) -> LogStats:
        """
        Get log statistics.

        Args:
            tenant_id: Tenant UUID.
            robot_id: Optional robot UUID for robot-specific stats.

        Returns:
            LogStats with counts and metrics.
        """
        conn = await self._get_connection()
        try:
            row = await conn.fetchrow(
                "SELECT * FROM get_robot_logs_stats($1, $2)",
                tenant_id,
                robot_id,
            )

            if row is None:
                return LogStats(
                    tenant_id=tenant_id,
                    robot_id=robot_id,
                    total_count=0,
                    by_level={},
                    oldest_log=None,
                    newest_log=None,
                    storage_bytes=0,
                )

            return LogStats(
                tenant_id=tenant_id,
                robot_id=robot_id,
                total_count=row["total_count"],
                by_level={
                    "TRACE": row["trace_count"],
                    "DEBUG": row["debug_count"],
                    "INFO": row["info_count"],
                    "WARNING": row["warning_count"],
                    "ERROR": row["error_count"],
                    "CRITICAL": row["critical_count"],
                },
                oldest_log=row["oldest_log"],
                newest_log=row["newest_log"],
                storage_bytes=row["storage_bytes"],
            )
        except Exception as e:
            logger.error(f"Failed to get log stats: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def cleanup_old_logs(
        self, retention_days: int = DEFAULT_LOG_RETENTION_DAYS
    ) -> dict[str, Any]:
        """
        Remove logs older than retention period.

        Uses partition dropping for efficient bulk cleanup.

        Args:
            retention_days: Number of days to retain logs.

        Returns:
            Dictionary with cleanup results.
        """
        conn = await self._get_connection()
        start_time = datetime.now(UTC)
        try:
            # Drop old partitions
            rows = await conn.fetch(
                "SELECT * FROM drop_old_robot_logs_partitions($1)",
                retention_days,
            )

            dropped_partitions = [row["partition_name"] for row in rows]

            # Calculate duration
            duration_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)

            # Record cleanup in history
            await conn.execute(
                """
                INSERT INTO robot_logs_cleanup_history (
                    partitions_dropped, retention_days, duration_ms, status
                ) VALUES ($1, $2, $3, 'completed')
                """,
                dropped_partitions,
                retention_days,
                duration_ms,
            )

            result = {
                "partitions_dropped": dropped_partitions,
                "retention_days": retention_days,
                "duration_ms": duration_ms,
                "status": "completed",
            }

            if dropped_partitions:
                logger.info(
                    f"Log cleanup completed: dropped {len(dropped_partitions)} partitions "
                    f"(retention={retention_days} days, duration={duration_ms}ms)"
                )
            else:
                logger.debug(
                    f"Log cleanup completed: no partitions to drop "
                    f"(retention={retention_days} days)"
                )

            return result
        except Exception as e:
            duration_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
            error_msg = str(e)

            # Record failed cleanup
            try:
                await conn.execute(
                    """
                    INSERT INTO robot_logs_cleanup_history (
                        retention_days, duration_ms, status, error_message
                    ) VALUES ($1, $2, 'failed', $3)
                    """,
                    retention_days,
                    duration_ms,
                    error_msg,
                )
            except Exception:
                pass  # Don't fail if history insert fails

            logger.error(f"Log cleanup failed: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def ensure_partitions(self, months_ahead: int = 2) -> list[dict[str, str]]:
        """
        Ensure future partitions exist.

        Should be called periodically (e.g., daily) to ensure partitions
        are ready for incoming logs.

        Args:
            months_ahead: Number of months to create partitions for.

        Returns:
            List of partition statuses.
        """
        conn = await self._get_connection()
        try:
            rows = await conn.fetch(
                "SELECT * FROM ensure_robot_logs_partitions($1)",
                months_ahead,
            )

            results = [
                {"partition": row["partition_name"], "status": row["status"]} for row in rows
            ]

            logger.debug(f"Ensured {len(results)} log partitions")
            return results
        except Exception as e:
            logger.error(f"Failed to ensure partitions: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def get_cleanup_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get recent cleanup job history.

        Args:
            limit: Maximum number of records to return.

        Returns:
            List of cleanup history records.
        """
        conn = await self._get_connection()
        try:
            rows = await conn.fetch(
                """
                SELECT * FROM robot_logs_cleanup_history
                ORDER BY cleanup_time DESC
                LIMIT $1
                """,
                limit,
            )

            return [
                {
                    "id": str(row["id"]),
                    "cleanup_time": row["cleanup_time"].isoformat()
                    if row["cleanup_time"]
                    else None,
                    "partitions_dropped": row["partitions_dropped"] or [],
                    "rows_deleted": row["rows_deleted"],
                    "retention_days": row["retention_days"],
                    "duration_ms": row["duration_ms"],
                    "status": row["status"],
                    "error_message": row["error_message"],
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Failed to get cleanup history: {e}")
            raise
        finally:
            await self._release_connection(conn)

    def _row_to_entry(self, row: dict[str, Any]) -> LogEntry:
        """
        Convert database row to LogEntry.

        Args:
            row: Database row dictionary.

        Returns:
            LogEntry value object.
        """
        # Parse level
        level_str = row.get("level", "INFO")
        level = LogLevel.from_string(level_str)

        # Parse extra JSONB
        extra = row.get("extra", {})
        if isinstance(extra, str):
            extra = orjson.loads(extra) if extra else {}

        return LogEntry(
            id=str(row["id"]),
            robot_id=str(row["robot_id"]),
            tenant_id=str(row["tenant_id"]),
            timestamp=row["timestamp"],
            level=level,
            message=row["message"],
            source=row.get("source"),
            extra=extra,
        )


__all__ = ["LogRepository"]
