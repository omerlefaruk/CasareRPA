"""
TraceRepository - PostgreSQL persistence for Execution Traces.

Provides efficient storage and retrieval of process mining traces with
configurable retention policies. Uses asyncpg connection pooling
and supports batch operations for high-volume trace ingestion.

Database Schema:
    execution_traces - Main trace records
    trace_activities - Individual activities within traces
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import orjson
from loguru import logger

from casare_rpa.infrastructure.analytics.process_mining import (
    Activity,
    ActivityStatus,
    ExecutionTrace,
)
from casare_rpa.utils.pooling.database_pool import DatabasePoolManager


# =============================================================================
# Constants
# =============================================================================

DEFAULT_RETENTION_DAYS = 90
DEFAULT_QUERY_LIMIT = 1000
BATCH_INSERT_SIZE = 100


# =============================================================================
# Trace Repository
# =============================================================================


class TraceRepository:
    """
    Repository for ExecutionTrace persistence.

    Uses asyncpg with connection pooling for efficient database operations.
    Supports batch inserts, time-range queries, and automatic archival.

    Usage:
        repo = TraceRepository()
        await repo.save_trace(trace)
        traces = await repo.get_traces(workflow_id="wf-123")
    """

    def __init__(self, pool_manager: Optional[DatabasePoolManager] = None) -> None:
        """
        Initialize repository with optional pool manager.

        Args:
            pool_manager: Database pool manager. If None, will fetch from singleton.
        """
        self._pool_manager = pool_manager
        self._pool_name = "casare_rpa"
        self._initialized = False

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

    async def ensure_tables(self) -> None:
        """
        Ensure required tables exist.

        Creates execution_traces and trace_activities tables if they don't exist.
        Should be called during application startup.
        """
        if self._initialized:
            return

        conn = await self._get_connection()
        try:
            # Create execution_traces table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS execution_traces (
                    id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    workflow_name TEXT NOT NULL,
                    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    completed_at TIMESTAMP WITH TIME ZONE,
                    status TEXT NOT NULL DEFAULT 'running',
                    variant_hash TEXT,
                    robot_id TEXT,
                    total_duration_ms INTEGER,
                    activity_count INTEGER DEFAULT 0,
                    success_rate FLOAT DEFAULT 0.0,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)

            # Create trace_activities table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS trace_activities (
                    id SERIAL PRIMARY KEY,
                    trace_id TEXT NOT NULL REFERENCES execution_traces(id) ON DELETE CASCADE,
                    activity_name TEXT NOT NULL,
                    node_id TEXT NOT NULL,
                    node_type TEXT NOT NULL,
                    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    duration_ms INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    inputs JSONB,
                    outputs JSONB,
                    error_message TEXT,
                    sequence_number INTEGER NOT NULL
                )
            """)

            # Create indexes for common queries
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_traces_workflow_id
                ON execution_traces(workflow_id)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_traces_started_at
                ON execution_traces(started_at)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_traces_status
                ON execution_traces(status)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_activities_trace_id
                ON trace_activities(trace_id)
            """)

            self._initialized = True
            logger.info("Trace repository tables initialized")

        except Exception as e:
            logger.error(f"Failed to initialize trace tables: {e}")
            raise
        finally:
            await self._release_connection(conn)

    # =========================================================================
    # Save Operations
    # =========================================================================

    async def save_trace(self, trace: ExecutionTrace) -> ExecutionTrace:
        """
        Save a single execution trace with all activities.

        Args:
            trace: ExecutionTrace to save.

        Returns:
            Saved ExecutionTrace.

        Raises:
            Exception: If database operation fails.
        """
        conn = await self._get_connection()
        try:
            async with conn.transaction():
                # Insert trace record
                await conn.execute(
                    """
                    INSERT INTO execution_traces (
                        id, workflow_id, workflow_name, started_at, completed_at,
                        status, variant_hash, robot_id, total_duration_ms,
                        activity_count, success_rate
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    ON CONFLICT (id) DO UPDATE SET
                        completed_at = EXCLUDED.completed_at,
                        status = EXCLUDED.status,
                        variant_hash = EXCLUDED.variant_hash,
                        total_duration_ms = EXCLUDED.total_duration_ms,
                        activity_count = EXCLUDED.activity_count,
                        success_rate = EXCLUDED.success_rate
                    """,
                    trace.case_id,
                    trace.workflow_id,
                    trace.workflow_name,
                    trace.start_time,
                    trace.end_time,
                    trace.status,
                    trace.variant,
                    trace.robot_id,
                    trace.total_duration_ms,
                    len(trace.activities),
                    trace.success_rate,
                )

                # Delete existing activities and insert new ones
                await conn.execute(
                    "DELETE FROM trace_activities WHERE trace_id = $1",
                    trace.case_id,
                )

                # Insert activities
                for i, activity in enumerate(trace.activities):
                    await conn.execute(
                        """
                        INSERT INTO trace_activities (
                            trace_id, activity_name, node_id, node_type,
                            started_at, duration_ms, status, inputs, outputs,
                            error_message, sequence_number
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9::jsonb, $10, $11)
                        """,
                        trace.case_id,
                        activity.node_type,
                        activity.node_id,
                        activity.node_type,
                        activity.timestamp,
                        activity.duration_ms,
                        activity.status.value,
                        orjson.dumps(activity.inputs or {}).decode(),
                        orjson.dumps(activity.outputs or {}).decode(),
                        activity.error_message,
                        i,
                    )

            logger.debug(
                f"Saved trace {trace.case_id} with {len(trace.activities)} activities"
            )
            return trace

        except Exception as e:
            logger.error(f"Failed to save trace {trace.case_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def save_traces_batch(self, traces: List[ExecutionTrace]) -> int:
        """
        Save multiple traces in a batch.

        Args:
            traces: List of ExecutionTrace objects to save.

        Returns:
            Number of traces saved.
        """
        if not traces:
            return 0

        saved_count = 0
        for i in range(0, len(traces), BATCH_INSERT_SIZE):
            batch = traces[i : i + BATCH_INSERT_SIZE]
            for trace in batch:
                try:
                    await self.save_trace(trace)
                    saved_count += 1
                except Exception as e:
                    logger.error(f"Failed to save trace {trace.case_id} in batch: {e}")

        logger.info(f"Saved batch of {saved_count}/{len(traces)} traces")
        return saved_count

    async def update_trace_status(
        self,
        case_id: str,
        status: str,
        end_time: Optional[datetime] = None,
    ) -> bool:
        """
        Update trace status and completion time.

        Args:
            case_id: Trace ID to update.
            status: New status value.
            end_time: Completion timestamp (defaults to now).

        Returns:
            True if trace was updated, False if not found.
        """
        conn = await self._get_connection()
        try:
            result = await conn.execute(
                """
                UPDATE execution_traces
                SET status = $2, completed_at = $3
                WHERE id = $1
                """,
                case_id,
                status,
                end_time or datetime.now(timezone.utc),
            )
            updated = result.split()[-1] != "0"
            if updated:
                logger.debug(f"Updated trace {case_id} status to {status}")
            return updated

        except Exception as e:
            logger.error(f"Failed to update trace {case_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    # =========================================================================
    # Query Operations
    # =========================================================================

    async def get_trace(self, case_id: str) -> Optional[ExecutionTrace]:
        """
        Get trace by case ID with all activities.

        Args:
            case_id: Trace ID to retrieve.

        Returns:
            ExecutionTrace if found, None otherwise.
        """
        conn = await self._get_connection()
        try:
            # Get trace record
            row = await conn.fetchrow(
                "SELECT * FROM execution_traces WHERE id = $1",
                case_id,
            )
            if row is None:
                return None

            # Get activities
            activity_rows = await conn.fetch(
                """
                SELECT * FROM trace_activities
                WHERE trace_id = $1
                ORDER BY sequence_number
                """,
                case_id,
            )

            return self._rows_to_trace(dict(row), [dict(r) for r in activity_rows])

        except Exception as e:
            logger.error(f"Failed to get trace {case_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def get_traces(
        self,
        workflow_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None,
        robot_id: Optional[str] = None,
        limit: int = DEFAULT_QUERY_LIMIT,
        offset: int = 0,
        include_activities: bool = True,
    ) -> List[ExecutionTrace]:
        """
        Query traces with filters.

        Args:
            workflow_id: Filter by workflow ID.
            start_date: Filter by start time (>= this date).
            end_date: Filter by start time (<= this date).
            status: Filter by status.
            robot_id: Filter by robot ID.
            limit: Maximum number of traces to return.
            offset: Number of traces to skip.
            include_activities: Whether to load activities.

        Returns:
            List of matching ExecutionTrace objects.
        """
        conn = await self._get_connection()
        try:
            # Build query dynamically
            conditions = []
            params = []
            param_idx = 1

            if workflow_id:
                conditions.append(f"workflow_id = ${param_idx}")
                params.append(workflow_id)
                param_idx += 1

            if start_date:
                conditions.append(f"started_at >= ${param_idx}")
                params.append(start_date)
                param_idx += 1

            if end_date:
                conditions.append(f"started_at <= ${param_idx}")
                params.append(end_date)
                param_idx += 1

            if status:
                conditions.append(f"status = ${param_idx}")
                params.append(status)
                param_idx += 1

            if robot_id:
                conditions.append(f"robot_id = ${param_idx}")
                params.append(robot_id)
                param_idx += 1

            where_clause = " AND ".join(conditions) if conditions else "TRUE"

            query = f"""
                SELECT * FROM execution_traces
                WHERE {where_clause}
                ORDER BY started_at DESC
                LIMIT ${param_idx} OFFSET ${param_idx + 1}
            """
            params.extend([limit, offset])

            rows = await conn.fetch(query, *params)

            traces = []
            for row in rows:
                activities = []
                if include_activities:
                    activity_rows = await conn.fetch(
                        """
                        SELECT * FROM trace_activities
                        WHERE trace_id = $1
                        ORDER BY sequence_number
                        """,
                        row["id"],
                    )
                    activities = [dict(r) for r in activity_rows]

                trace = self._rows_to_trace(dict(row), activities)
                traces.append(trace)

            return traces

        except Exception as e:
            logger.error(f"Failed to query traces: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def get_traces_for_workflow(
        self,
        workflow_id: str,
        limit: int = DEFAULT_QUERY_LIMIT,
        status: Optional[str] = None,
    ) -> List[ExecutionTrace]:
        """
        Get traces for a specific workflow.

        Args:
            workflow_id: Workflow ID to filter by.
            limit: Maximum traces to return.
            status: Optional status filter.

        Returns:
            List of ExecutionTrace objects.
        """
        return await self.get_traces(
            workflow_id=workflow_id,
            status=status,
            limit=limit,
        )

    async def get_trace_count(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> int:
        """
        Get count of traces.

        Args:
            workflow_id: Optional workflow filter.
            status: Optional status filter.

        Returns:
            Number of matching traces.
        """
        conn = await self._get_connection()
        try:
            conditions = []
            params = []
            param_idx = 1

            if workflow_id:
                conditions.append(f"workflow_id = ${param_idx}")
                params.append(workflow_id)
                param_idx += 1

            if status:
                conditions.append(f"status = ${param_idx}")
                params.append(status)

            where_clause = " AND ".join(conditions) if conditions else "TRUE"
            query = f"SELECT COUNT(*) FROM execution_traces WHERE {where_clause}"

            row = await conn.fetchrow(query, *params)
            return row["count"] if row else 0

        except Exception as e:
            logger.error(f"Failed to get trace count: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def get_workflow_ids(self) -> List[str]:
        """
        Get list of all distinct workflow IDs with traces.

        Returns:
            List of workflow ID strings.
        """
        conn = await self._get_connection()
        try:
            rows = await conn.fetch(
                "SELECT DISTINCT workflow_id FROM execution_traces ORDER BY workflow_id"
            )
            return [row["workflow_id"] for row in rows]

        except Exception as e:
            logger.error(f"Failed to get workflow IDs: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def get_variant_stats(self, workflow_id: str) -> List[Dict[str, Any]]:
        """
        Get variant statistics for a workflow.

        Args:
            workflow_id: Workflow ID to analyze.

        Returns:
            List of variant statistics dictionaries.
        """
        conn = await self._get_connection()
        try:
            rows = await conn.fetch(
                """
                SELECT
                    variant_hash,
                    COUNT(*) as count,
                    AVG(total_duration_ms) as avg_duration_ms,
                    AVG(success_rate) as avg_success_rate,
                    MIN(started_at) as first_seen,
                    MAX(started_at) as last_seen
                FROM execution_traces
                WHERE workflow_id = $1 AND variant_hash IS NOT NULL
                GROUP BY variant_hash
                ORDER BY count DESC
                """,
                workflow_id,
            )

            return [
                {
                    "variant_hash": row["variant_hash"],
                    "count": row["count"],
                    "avg_duration_ms": float(row["avg_duration_ms"])
                    if row["avg_duration_ms"]
                    else 0,
                    "avg_success_rate": float(row["avg_success_rate"])
                    if row["avg_success_rate"]
                    else 0,
                    "first_seen": row["first_seen"].isoformat()
                    if row["first_seen"]
                    else None,
                    "last_seen": row["last_seen"].isoformat()
                    if row["last_seen"]
                    else None,
                }
                for row in rows
            ]

        except Exception as e:
            logger.error(f"Failed to get variant stats: {e}")
            raise
        finally:
            await self._release_connection(conn)

    # =========================================================================
    # Cleanup Operations
    # =========================================================================

    async def cleanup_old_traces(
        self,
        retention_days: int = DEFAULT_RETENTION_DAYS,
    ) -> Dict[str, Any]:
        """
        Remove traces older than retention period.

        Args:
            retention_days: Number of days to retain traces.

        Returns:
            Dictionary with cleanup results.
        """
        conn = await self._get_connection()
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)

        try:
            # Get count before deletion
            count_row = await conn.fetchrow(
                "SELECT COUNT(*) FROM execution_traces WHERE started_at < $1",
                cutoff_date,
            )
            traces_to_delete = count_row["count"] if count_row else 0

            if traces_to_delete == 0:
                return {
                    "deleted_traces": 0,
                    "retention_days": retention_days,
                    "cutoff_date": cutoff_date.isoformat(),
                }

            # Delete old traces (cascade deletes activities)
            result = await conn.execute(
                "DELETE FROM execution_traces WHERE started_at < $1",
                cutoff_date,
            )

            # Parse deleted count from result
            deleted = int(result.split()[-1]) if result else 0

            logger.info(
                f"Trace cleanup: deleted {deleted} traces older than {retention_days} days"
            )

            return {
                "deleted_traces": deleted,
                "retention_days": retention_days,
                "cutoff_date": cutoff_date.isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to cleanup old traces: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def delete_trace(self, case_id: str) -> bool:
        """
        Delete a specific trace.

        Args:
            case_id: Trace ID to delete.

        Returns:
            True if deleted, False if not found.
        """
        conn = await self._get_connection()
        try:
            result = await conn.execute(
                "DELETE FROM execution_traces WHERE id = $1",
                case_id,
            )
            deleted = result.split()[-1] != "0"
            if deleted:
                logger.debug(f"Deleted trace {case_id}")
            return deleted

        except Exception as e:
            logger.error(f"Failed to delete trace {case_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _rows_to_trace(
        self,
        trace_row: Dict[str, Any],
        activity_rows: List[Dict[str, Any]],
    ) -> ExecutionTrace:
        """
        Convert database rows to ExecutionTrace object.

        Args:
            trace_row: Trace table row.
            activity_rows: Activity table rows.

        Returns:
            ExecutionTrace object.
        """
        activities = []
        for row in activity_rows:
            # Parse inputs/outputs JSONB
            inputs = row.get("inputs", {})
            if isinstance(inputs, str):
                inputs = orjson.loads(inputs) if inputs else {}

            outputs = row.get("outputs", {})
            if isinstance(outputs, str):
                outputs = orjson.loads(outputs) if outputs else {}

            # Parse status
            try:
                status = ActivityStatus(row["status"])
            except ValueError:
                status = ActivityStatus.COMPLETED

            activities.append(
                Activity(
                    node_id=row["node_id"],
                    node_type=row["node_type"],
                    timestamp=row["started_at"],
                    duration_ms=row["duration_ms"],
                    status=status,
                    inputs=inputs,
                    outputs=outputs,
                    error_message=row.get("error_message"),
                )
            )

        return ExecutionTrace(
            case_id=trace_row["id"],
            workflow_id=trace_row["workflow_id"],
            workflow_name=trace_row["workflow_name"],
            activities=activities,
            start_time=trace_row["started_at"],
            end_time=trace_row.get("completed_at"),
            status=trace_row.get("status", "completed"),
            robot_id=trace_row.get("robot_id"),
        )


__all__ = [
    "TraceRepository",
    "DEFAULT_RETENTION_DAYS",
    "DEFAULT_QUERY_LIMIT",
]
