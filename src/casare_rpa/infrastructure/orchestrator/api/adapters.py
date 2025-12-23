"""
Data adapters for monitoring API.

Maps between infrastructure layer (RPAMetricsCollector, MetricsAggregator)
and API response models (Pydantic).
"""

import json
from datetime import UTC, datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from loguru import logger

if TYPE_CHECKING:
    import asyncpg

from casare_rpa.infrastructure.analytics.metrics_aggregator import MetricsAggregator
from casare_rpa.infrastructure.observability.metrics import (
    RPAMetricsCollector,
)

# Valid job statuses for filtering
VALID_JOB_STATUSES = frozenset({"pending", "claimed", "completed", "failed"})


class MonitoringDataAdapter:
    """
    Adapts infrastructure metrics to monitoring API format.

    Bridges the gap between RPAMetricsCollector (real-time in-memory metrics)
    and the REST API response models expected by the React dashboard.
    """

    def __init__(
        self,
        metrics_collector: RPAMetricsCollector,
        analytics_aggregator: MetricsAggregator,
        db_pool: Optional["asyncpg.Pool"] = None,
    ):
        """
        Initialize the monitoring data adapter.

        Args:
            metrics_collector: RPAMetricsCollector for real-time metrics
            analytics_aggregator: MetricsAggregator for self-healing stats
            db_pool: Optional database connection pool for historical queries
        """
        self.metrics = metrics_collector
        self.analytics = analytics_aggregator
        self._db_pool = db_pool

    @property
    def has_db(self) -> bool:
        """Check if database pool is available for historical queries."""
        return self._db_pool is not None

    async def get_fleet_summary_async(self) -> dict:
        """
        Get fleet-wide metrics summary from database.

        Returns:
            Dict matching FleetMetrics Pydantic model
        """
        if not self._db_pool:
            return self.get_fleet_summary()

        try:
            async with self._db_pool.acquire() as conn:
                # Query robots from database (consider robots seen in last 5 mins as active)
                # Actual Supabase schema uses: 'idle', 'busy', 'offline', 'error', 'maintenance'
                robots_query = """
                    SELECT
                        COUNT(*) AS total,
                        COUNT(*) FILTER (WHERE status = 'busy') AS busy,
                        COUNT(*) FILTER (WHERE status = 'idle' AND last_seen > NOW() - INTERVAL '5 minutes') AS idle,
                        COUNT(*) FILTER (WHERE status = 'offline' OR status = 'error' OR last_seen <= NOW() - INTERVAL '5 minutes') AS offline
                    FROM robots
                """
                robot_stats = await conn.fetchrow(robots_query)

                # Query queue depth
                queue_query = "SELECT COUNT(*) FROM job_queue WHERE status = 'pending'"
                queue_depth = await conn.fetchval(queue_query) or 0

                # Query active jobs
                active_query = "SELECT COUNT(*) FROM job_queue WHERE status = 'claimed'"
                active_jobs = await conn.fetchval(active_query) or 0

                # Query jobs completed today with average duration
                # Use job_queue table (Supabase schema) not pgqueuer_jobs
                jobs_today_query = """
                    SELECT
                        COUNT(*) AS total,
                        AVG(
                            EXTRACT(EPOCH FROM (completed_at - started_at))
                        ) FILTER (
                            WHERE completed_at IS NOT NULL AND started_at IS NOT NULL
                        ) AS avg_duration
                    FROM job_queue
                    WHERE DATE(created_at) = CURRENT_DATE
                """
                jobs_today = await conn.fetchrow(jobs_today_query)

                return {
                    "total_robots": robot_stats["total"] or 0,
                    "active_robots": robot_stats["busy"] or 0,
                    "idle_robots": robot_stats["idle"] or 0,
                    "offline_robots": robot_stats["offline"] or 0,
                    "total_jobs_today": jobs_today["total"] or 0,
                    "active_jobs": active_jobs,
                    "queue_depth": queue_depth,
                    "average_job_duration_seconds": jobs_today["avg_duration"] or 0.0,
                }
        except Exception as e:
            logger.error(f"Database error in get_fleet_summary_async: {e}")
            return self.get_fleet_summary()

    def get_fleet_summary(self) -> dict:
        """
        Get fleet-wide metrics summary (in-memory fallback).

        Returns:
            Dict matching FleetMetrics Pydantic model
        """
        all_robots = self.metrics.get_all_robot_metrics()
        queue_depth = self.metrics.get_queue_depth()
        active_jobs = len(self.metrics.get_active_jobs())

        total_robots = len(all_robots)
        active_robots = sum(1 for r in all_robots.values() if r.status.value == "busy")
        idle_robots = sum(1 for r in all_robots.values() if r.status.value == "idle")
        offline_robots = sum(1 for r in all_robots.values() if r.status.value == "offline")

        # Calculate today's job stats
        job_metrics = self.metrics.get_job_metrics()
        total_jobs_today = job_metrics.total_jobs
        average_duration = (
            job_metrics.total_duration_seconds / total_jobs_today if total_jobs_today > 0 else 0.0
        )

        return {
            "total_robots": total_robots,
            "active_robots": active_robots,
            "idle_robots": idle_robots,
            "offline_robots": offline_robots,
            "total_jobs_today": total_jobs_today,
            "active_jobs": active_jobs,
            "queue_depth": queue_depth,
            "average_job_duration_seconds": average_duration,
        }

    async def get_robot_list_async(self, status: str | None = None) -> list[dict]:
        """
        Get list of all robots from database with optional status filter.

        Args:
            status: Filter by status (idle/busy/offline/failed)

        Returns:
            List of dicts matching RobotSummary Pydantic model
        """
        if not self._db_pool:
            return self.get_robot_list(status)

        try:
            async with self._db_pool.acquire() as conn:
                has_id = await conn.fetchval(
                    """
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'robots' AND column_name = 'id'
                    )
                    """
                )
                robot_id_expr = "COALESCE(robot_id, id)" if has_id else "robot_id"

                # Build query with optional status filter
                # Actual Supabase schema: id, robot_id, name, hostname, status,
                # last_seen, last_heartbeat, metrics, capabilities, environment, etc.
                # NO current_job_ids column exists!
                if status:
                    if status == "idle":
                        query = f"""
                        SELECT
                            {robot_id_expr} AS robot_id,
                            name,
                            hostname,
                            status,
                            NULL AS current_job_id,
                            last_seen,
                            last_heartbeat,
                            metrics
                        FROM robots
                        WHERE status IN ('idle', 'online')
                        ORDER BY last_seen DESC NULLS LAST
                        """
                        rows = await conn.fetch(query)
                    else:
                        query = f"""
                        SELECT
                            {robot_id_expr} AS robot_id,
                            name,
                            hostname,
                            status,
                            NULL AS current_job_id,
                            last_seen,
                            last_heartbeat,
                            metrics
                        FROM robots
                        WHERE status = $1
                        ORDER BY last_seen DESC NULLS LAST
                        """
                        rows = await conn.fetch(query, status)
                else:
                    query = f"""
                        SELECT
                            {robot_id_expr} AS robot_id,
                            name,
                            hostname,
                            status,
                            NULL AS current_job_id,
                            last_seen,
                            last_heartbeat,
                            metrics
                        FROM robots
                        ORDER BY last_seen DESC NULLS LAST
                    """
                    rows = await conn.fetch(query)

                result = []
                for row in rows:
                    # Handle metrics - may be dict, JSON string, or None
                    raw_metrics = row["metrics"]
                    if raw_metrics is None:
                        metrics = {}
                    elif isinstance(raw_metrics, str):
                        try:
                            metrics = json.loads(raw_metrics)
                        except json.JSONDecodeError:
                            metrics = {}
                    else:
                        metrics = raw_metrics

                    # Map Supabase status to API status (online -> idle when not busy)
                    api_status = row["status"]
                    if api_status == "online":
                        api_status = "idle"

                    result.append(
                        {
                            "robot_id": row["robot_id"],
                            "name": row.get("name") or row["hostname"] or row["robot_id"],
                            "hostname": row["hostname"] or row["robot_id"],
                            "status": api_status,
                            "cpu_percent": metrics.get("cpu_percent", 0.0),
                            "memory_mb": metrics.get("memory_mb", 0.0),
                            "current_job_id": str(row["current_job_id"])
                            if row["current_job_id"]
                            else None,
                            "last_heartbeat": row.get("last_heartbeat") or row["last_seen"],
                        }
                    )
                return result

        except Exception as e:
            logger.error(f"Database error in get_robot_list_async: {e}")
            return self.get_robot_list(status)

    def get_robot_list(self, status: str | None = None) -> list[dict]:
        """
        Get list of all robots with optional status filter (in-memory fallback).

        Args:
            status: Filter by status (idle/busy/offline/failed)

        Returns:
            List of dicts matching RobotSummary Pydantic model
        """
        all_robots = self.metrics.get_all_robot_metrics()
        result = []

        for robot_id, robot_metrics in all_robots.items():
            # Filter by status if provided
            if status and robot_metrics.status.value != status:
                continue

            # Map to API format
            # Note: cpu_percent and memory_mb require Robot agent heartbeat (v2.0 feature)
            result.append(
                {
                    "robot_id": robot_id,
                    "hostname": robot_id,  # Hostname populated from Robot agent metadata
                    "status": robot_metrics.status.value,
                    "cpu_percent": 0.0,  # From Robot agent heartbeat
                    "memory_mb": 0.0,  # From Robot agent heartbeat
                    "current_job_id": robot_metrics.current_job_id,
                    "last_heartbeat": robot_metrics.last_job_at or datetime.now(),
                }
            )

        return result

    def get_robot_details(self, robot_id: str) -> dict | None:
        """
        Get detailed metrics for a single robot.

        Args:
            robot_id: Robot identifier

        Returns:
            Dict matching RobotMetrics Pydantic model, or None if not found
        """
        robot_metrics = self.metrics.get_robot_metrics(robot_id)
        if not robot_metrics:
            return None

        # Note: System metrics (cpu/memory) require Robot agent heartbeat (v2.0 feature)
        return {
            "robot_id": robot_id,
            "hostname": robot_id,  # Populated from Robot agent metadata
            "status": robot_metrics.status.value,
            "cpu_percent": 0.0,  # From Robot agent heartbeat
            "memory_mb": 0.0,  # From Robot agent heartbeat
            "memory_percent": 0.0,  # From Robot agent heartbeat
            "current_job_id": robot_metrics.current_job_id,
            "last_heartbeat": robot_metrics.last_job_at or datetime.now(),
            "jobs_completed_today": robot_metrics.jobs_completed,
            "jobs_failed_today": robot_metrics.jobs_failed,
            "average_job_duration_seconds": 0.0,  # Requires job history query
        }

    async def get_job_history(
        self,
        limit: int = 50,
        status: str | None = None,
        workflow_id: str | None = None,
        robot_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get job execution history from pgqueuer_jobs table.

        Args:
            limit: Max jobs to return (1-500, default 50)
            status: Filter by status (pending/claimed/completed/failed)
            workflow_id: Filter by workflow ID
            robot_id: Filter by robot ID (claimed_by column)

        Returns:
            List of dicts matching JobSummary Pydantic model
        """
        if not self._db_pool:
            logger.warning("Database pool not configured - returning empty job history")
            return []

        # Validate and clamp limit
        limit = max(1, min(500, limit))

        # Validate status filter
        if status and status not in VALID_JOB_STATUSES:
            logger.warning(f"Invalid status filter: {status}")
            return []

        try:
            async with self._db_pool.acquire() as conn:
                return await self._query_job_history(conn, limit, status, workflow_id, robot_id)
        except Exception as e:
            logger.error(f"Database error fetching job history: {e}")
            return []

    async def _query_job_history(
        self,
        conn: Any,  # asyncpg.Connection
        limit: int,
        status: str | None,
        workflow_id: str | None,
        robot_id: str | None,
    ) -> list[dict[str, Any]]:
        """
        Execute parameterized query for job history.

        Uses dynamic query building with proper parameterization.
        Extracts workflow_id and workflow_name from payload JSONB.
        """
        # Build query with parameterized filters
        query_parts = [
            """
            SELECT
                id::text AS job_id,
                workflow_id,
                workflow_name,
                robot_id,
                status,
                created_at,
                completed_at,
                CASE
                    WHEN completed_at IS NOT NULL AND started_at IS NOT NULL
                    THEN EXTRACT(EPOCH FROM (completed_at - started_at))::integer * 1000
                    ELSE NULL
                END AS duration_ms
            FROM job_queue
            WHERE 1=1
            """
        ]

        params: list[Any] = []
        param_idx = 1

        if status:
            query_parts.append(f"AND status = ${param_idx}")
            params.append(status)
            param_idx += 1

        if workflow_id:
            query_parts.append(f"AND workflow_id = ${param_idx}")
            params.append(workflow_id)
            param_idx += 1

        if robot_id:
            query_parts.append(f"AND robot_id = ${param_idx}")
            params.append(robot_id)
            param_idx += 1

        query_parts.append(f"ORDER BY created_at DESC LIMIT ${param_idx}")
        params.append(limit)

        query = "\n".join(query_parts)

        logger.debug(f"Executing job history query with {len(params)} params")
        rows = await conn.fetch(query, *params)

        return [self._row_to_job_summary(row) for row in rows]

    def _row_to_job_summary(self, row: Any) -> dict[str, Any]:
        """
        Convert database row to JobSummary dict format.

        Handles NULL values and type conversions.
        """
        return {
            "job_id": row["job_id"],
            "workflow_id": row["workflow_id"] or "",
            "workflow_name": row["workflow_name"],
            "robot_id": row["robot_id"],
            "status": row["status"],
            "created_at": row["created_at"],
            "completed_at": row["completed_at"],
            "duration_ms": row["duration_ms"],
        }

    def get_job_details(self, job_id: str) -> dict | None:
        """
        Get detailed execution information for a single job.

        NOTE: Requires database integration for historical data.

        Args:
            job_id: Job identifier

        Returns:
            Dict matching JobDetails Pydantic model, or None if not found
        """
        # Check active jobs first
        active_jobs = self.metrics.get_active_jobs()
        if job_id in active_jobs:
            job = active_jobs[job_id]
            return {
                "job_id": job_id,
                "workflow_id": job.get("workflow_id", ""),
                "workflow_name": job.get("workflow_name"),
                "robot_id": job.get("robot_id"),
                "status": "running",
                "created_at": job.get("started_at", datetime.now()),
                "claimed_at": job.get("started_at"),
                "completed_at": None,
                "duration_ms": None,
                "error_message": None,
                "error_type": None,
                "retry_count": 0,
                "node_executions": [],
            }

        # For historical jobs, need database - return None from sync method
        # Use get_job_details_async() for database-backed historical queries
        return None

    async def get_job_details_async(self, job_id: str) -> dict[str, Any] | None:
        """
        Get detailed execution information for a single job from database.

        Checks active jobs first, then queries pgqueuer_jobs for historical data.
        Extracts error information and retry count from payload JSONB.

        Args:
            job_id: Job identifier (UUID string)

        Returns:
            Dict matching JobDetails Pydantic model, or None if not found
        """
        # Check active jobs first (in-memory cache)
        active_jobs = self.metrics.get_active_jobs()
        if job_id in active_jobs:
            job = active_jobs[job_id]
            return {
                "job_id": job_id,
                "workflow_id": job.get("workflow_id", ""),
                "workflow_name": job.get("workflow_name"),
                "robot_id": job.get("robot_id"),
                "status": "running",
                "created_at": job.get("started_at", datetime.now(UTC)),
                "claimed_at": job.get("started_at"),
                "completed_at": None,
                "duration_ms": None,
                "error_message": None,
                "error_type": None,
                "retry_count": 0,
                "node_executions": [],
            }

        # Query database for historical job
        if not self._db_pool:
            logger.warning("Database pool not configured - cannot fetch historical job")
            return None

        try:
            async with self._db_pool.acquire() as conn:
                return await self._query_job_details(conn, job_id)
        except Exception as e:
            logger.error(f"Database error fetching job details for {job_id}: {e}")
            return None

    async def _query_job_details(
        self,
        conn: Any,  # asyncpg.Connection
        job_id: str,
    ) -> dict[str, Any] | None:
        """
        Execute parameterized query for single job details.

        Extracts all relevant fields from pgqueuer_jobs table including
        error information stored in payload JSONB.

        Args:
            conn: Database connection
            job_id: Job UUID string

        Returns:
            Dict matching JobDetails model or None if not found
        """
        query = """
            SELECT
                id::text AS job_id,
                workflow_id,
                workflow_name,
                robot_id,
                status,
                created_at,
                started_at AS claimed_at,
                completed_at,
                CASE
                    WHEN completed_at IS NOT NULL AND started_at IS NOT NULL
                    THEN EXTRACT(EPOCH FROM (completed_at - started_at))::integer * 1000
                    ELSE NULL
                END AS duration_ms,
                error_message,
                COALESCE(
                    SUBSTRING(
                        error_message
                        FROM '^([A-Za-z]+Error|[A-Za-z]+Exception)'
                    ),
                    CASE
                        WHEN error_message ILIKE '%%timeout%%'
                            THEN 'TimeoutError'
                        WHEN error_message ILIKE '%%connection%%'
                            THEN 'ConnectionError'
                        WHEN error_message ILIKE '%%not found%%'
                            THEN 'NotFoundError'
                        WHEN error_message ILIKE '%%permission%%'
                            THEN 'PermissionError'
                        WHEN error_message ILIKE '%%validation%%'
                            THEN 'ValidationError'
                        WHEN error_message IS NOT NULL
                            THEN 'UnknownError'
                        ELSE NULL
                    END
                ) AS error_type,
                retry_count,
                result->'node_executions' AS node_executions_json
            FROM job_queue
            WHERE id = $1::uuid
        """

        try:
            row = await conn.fetchrow(query, job_id)
        except Exception as e:
            # Handle invalid UUID format
            logger.warning(f"Invalid job_id format or query error: {e}")
            return None

        if not row:
            logger.debug(f"Job {job_id} not found in database")
            return None

        # Parse node_executions from JSONB if present
        node_executions: list[dict[str, Any]] = []
        if row["node_executions_json"]:
            try:
                raw_executions = row["node_executions_json"]
                if isinstance(raw_executions, str):
                    node_executions = json.loads(raw_executions)
                elif isinstance(raw_executions, list):
                    node_executions = raw_executions
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Failed to parse node_executions for job {job_id}: {e}")

        return {
            "job_id": row["job_id"],
            "workflow_id": row["workflow_id"] or "",
            "workflow_name": row["workflow_name"],
            "robot_id": row["robot_id"],
            "status": row["status"],
            "created_at": row["created_at"],
            "claimed_at": row["claimed_at"],
            "completed_at": row["completed_at"],
            "duration_ms": row["duration_ms"],
            "error_message": row["error_message"],
            "error_type": row["error_type"],
            "retry_count": row["retry_count"],
            "node_executions": node_executions,
        }

    def get_analytics(self) -> dict:
        """
        Get aggregated analytics (sync fallback using in-memory data).

        For database-backed analytics with percentiles, use get_analytics_async().

        Returns:
            Dict matching AnalyticsSummary Pydantic model
        """
        job_metrics = self.metrics.get_job_metrics()

        total_jobs = job_metrics.total_jobs
        success_rate = job_metrics.success_rate
        failure_rate = 100.0 - success_rate if total_jobs > 0 else 0.0

        # Get data from in-memory MetricsAggregator
        error_analysis = self.analytics.get_error_analysis(top_n=10)
        healing_metrics = self.analytics.get_healing_metrics()

        # Build slowest workflows from in-memory cache
        workflow_metrics = self.analytics.get_workflow_metrics()
        slowest_workflows = sorted(
            [
                {
                    "workflow_id": wf.workflow_id,
                    "workflow_name": wf.workflow_name,
                    "average_duration_ms": wf.duration_distribution.mean_ms,
                }
                for wf in workflow_metrics
                if wf.duration_distribution.total_executions > 0
            ],
            key=lambda x: x["average_duration_ms"],
            reverse=True,
        )[:10]

        # Build error distribution
        error_distribution = [
            {"error_type": err["error_type"], "count": err["count"]}
            for err in error_analysis.get("top_errors", [])
        ]

        # Get percentiles from in-memory data if available
        all_durations: list[float] = []
        for wf in workflow_metrics:
            if wf.duration_distribution.total_executions > 0:
                all_durations.extend(
                    [wf.duration_distribution.mean_ms] * wf.duration_distribution.total_executions
                )

        p50_ms = 0.0
        p90_ms = 0.0
        p99_ms = 0.0

        if all_durations:
            from casare_rpa.infrastructure.analytics.metrics_aggregator import (
                ExecutionDistribution,
            )

            dist = ExecutionDistribution.from_durations(all_durations)
            p50_ms = dist.p50_ms
            p90_ms = dist.p90_ms
            p99_ms = dist.p99_ms

        healing_success_rate = healing_metrics.get("overall_success_rate")

        return {
            "total_jobs": total_jobs,
            "success_rate": success_rate,
            "failure_rate": failure_rate,
            "average_duration_ms": job_metrics.average_duration_seconds * 1000,
            "p50_duration_ms": p50_ms,
            "p90_duration_ms": p90_ms,
            "p99_duration_ms": p99_ms,
            "slowest_workflows": slowest_workflows,
            "error_distribution": error_distribution,
            "self_healing_success_rate": healing_success_rate if healing_success_rate else None,
        }

    async def get_analytics_async(
        self,
        days: int = 7,
    ) -> dict[str, Any]:
        """
        Get aggregated analytics with database-backed percentile calculations.

        Queries pgqueuer_jobs table for accurate P50/P90/P99 duration metrics,
        slowest workflows, and error distribution.

        Args:
            days: Number of days to analyze (default: 7)

        Returns:
            Dict matching AnalyticsSummary Pydantic model
        """
        if not self._db_pool:
            logger.warning("No database pool - falling back to in-memory analytics")
            return self.get_analytics()

        try:
            async with self._db_pool.acquire() as conn:
                cutoff = datetime.now(UTC) - timedelta(days=days)

                # Query 1: Basic counts and percentiles using PERCENTILE_CONT
                stats_query = """
                    SELECT
                        COUNT(*) AS total_jobs,
                        COUNT(*) FILTER (WHERE status = 'completed') AS successful_jobs,
                        COUNT(*) FILTER (WHERE status = 'failed') AS failed_jobs,
                        AVG(
                            EXTRACT(EPOCH FROM (completed_at - started_at)) * 1000
                        ) FILTER (
                            WHERE completed_at IS NOT NULL AND started_at IS NOT NULL
                        ) AS avg_duration_ms,
                        PERCENTILE_CONT(0.50) WITHIN GROUP (
                            ORDER BY EXTRACT(EPOCH FROM (completed_at - started_at)) * 1000
                        ) FILTER (
                            WHERE completed_at IS NOT NULL AND started_at IS NOT NULL
                        ) AS p50_duration_ms,
                        PERCENTILE_CONT(0.90) WITHIN GROUP (
                            ORDER BY EXTRACT(EPOCH FROM (completed_at - started_at)) * 1000
                        ) FILTER (
                            WHERE completed_at IS NOT NULL AND started_at IS NOT NULL
                        ) AS p90_duration_ms,
                        PERCENTILE_CONT(0.99) WITHIN GROUP (
                            ORDER BY EXTRACT(EPOCH FROM (completed_at - started_at)) * 1000
                        ) FILTER (
                            WHERE completed_at IS NOT NULL AND started_at IS NOT NULL
                        ) AS p99_duration_ms
                    FROM job_queue
                    WHERE created_at >= $1
                """
                stats_row = await conn.fetchrow(stats_query, cutoff)

                total_jobs = stats_row["total_jobs"] or 0
                successful_jobs = stats_row["successful_jobs"] or 0
                failed_jobs = stats_row["failed_jobs"] or 0

                success_rate = (successful_jobs / total_jobs) * 100 if total_jobs > 0 else 0.0
                failure_rate = (failed_jobs / total_jobs) * 100 if total_jobs > 0 else 0.0

                avg_duration_ms = stats_row["avg_duration_ms"] or 0.0
                p50_duration_ms = stats_row["p50_duration_ms"] or 0.0
                p90_duration_ms = stats_row["p90_duration_ms"] or 0.0
                p99_duration_ms = stats_row["p99_duration_ms"] or 0.0

                # Query 2: Slowest workflows (top 10 by avg duration)
                slowest_query = """
                    SELECT
                        workflow_id,
                        workflow_name,
                        AVG(
                            EXTRACT(EPOCH FROM (completed_at - started_at)) * 1000
                        ) AS average_duration_ms,
                        COUNT(*) AS execution_count
                    FROM job_queue
                    WHERE created_at >= $1
                      AND completed_at IS NOT NULL
                      AND started_at IS NOT NULL
                      AND status IN ('completed', 'failed')
                    GROUP BY workflow_id, workflow_name
                    HAVING COUNT(*) >= 3
                    ORDER BY average_duration_ms DESC
                    LIMIT 10
                """
                slowest_rows = await conn.fetch(slowest_query, cutoff)

                slowest_workflows = [
                    {
                        "workflow_id": row["workflow_id"] or "unknown",
                        "workflow_name": row["workflow_name"] or row["workflow_id"] or "Unknown",
                        "average_duration_ms": round(row["average_duration_ms"], 2),
                    }
                    for row in slowest_rows
                ]

                # Query 3: Error distribution (count by error type pattern)
                error_query = """
                    SELECT
                        COALESCE(
                            SUBSTRING(
                                error_message
                                FROM '^([A-Za-z]+Error|[A-Za-z]+Exception)'
                            ),
                            CASE
                                WHEN error_message ILIKE '%%timeout%%'
                                    THEN 'TimeoutError'
                                WHEN error_message ILIKE '%%connection%%'
                                    THEN 'ConnectionError'
                                WHEN error_message ILIKE '%%not found%%'
                                    THEN 'NotFoundError'
                                WHEN error_message ILIKE '%%permission%%'
                                    THEN 'PermissionError'
                                WHEN error_message ILIKE '%%validation%%'
                                    THEN 'ValidationError'
                                ELSE 'UnknownError'
                            END
                        ) AS error_type,
                        COUNT(*) AS count
                    FROM job_queue
                    WHERE created_at >= $1
                      AND status = 'failed'
                      AND error_message IS NOT NULL
                      AND error_message != ''
                    GROUP BY error_type
                    ORDER BY count DESC
                    LIMIT 20
                """
                error_rows = await conn.fetch(error_query, cutoff)

                error_distribution = [
                    {"error_type": row["error_type"], "count": row["count"]} for row in error_rows
                ]

                # Query 4: Self-healing success rate from payload metadata
                healing_query = """
                    SELECT
                        COALESCE(
                            SUM((metadata->>'healing_attempts')::int), 0
                        ) AS total_attempts,
                        COALESCE(
                            SUM((metadata->>'healing_successes')::int), 0
                        ) AS total_successes
                    FROM job_queue
                    WHERE created_at >= $1
                      AND metadata ? 'healing_attempts'
                """
                healing_row = await conn.fetchrow(healing_query, cutoff)

                healing_attempts = healing_row["total_attempts"] or 0
                healing_successes = healing_row["total_successes"] or 0

                self_healing_success_rate: float | None = None
                if healing_attempts > 0:
                    self_healing_success_rate = round(
                        (healing_successes / healing_attempts) * 100, 2
                    )

                logger.debug(
                    f"Analytics: {total_jobs} jobs, {success_rate:.1f}% success, "
                    f"P50={p50_duration_ms:.0f}ms, P90={p90_duration_ms:.0f}ms"
                )

                return {
                    "total_jobs": total_jobs,
                    "success_rate": round(success_rate, 2),
                    "failure_rate": round(failure_rate, 2),
                    "average_duration_ms": round(avg_duration_ms, 2),
                    "p50_duration_ms": round(p50_duration_ms, 2),
                    "p90_duration_ms": round(p90_duration_ms, 2),
                    "p99_duration_ms": round(p99_duration_ms, 2),
                    "slowest_workflows": slowest_workflows,
                    "error_distribution": error_distribution,
                    "self_healing_success_rate": self_healing_success_rate,
                }

        except Exception as e:
            logger.error(f"Database analytics query failed: {e}")
            return self.get_analytics()

    async def get_activity_events_async(
        self,
        limit: int = 50,
        since: datetime | None = None,
        event_type: str | None = None,
    ) -> dict[str, Any]:
        """
        Get historical activity events for the dashboard.

        Combines job status changes and robot status changes into a unified
        activity feed sorted by timestamp descending.

        Args:
            limit: Max events to return (1-200, default 50)
            since: Only return events after this timestamp
            event_type: Filter by event type (job_started, job_completed, etc.)

        Returns:
            Dict matching ActivityResponse Pydantic model with events and total
        """
        if not self._db_pool:
            logger.warning("No database pool - returning empty activity feed")
            return {"events": [], "total": 0}

        limit = max(1, min(200, limit))

        valid_event_types = frozenset(
            {
                "job_started",
                "job_completed",
                "job_failed",
                "robot_online",
                "robot_offline",
                "schedule_triggered",
            }
        )

        if event_type and event_type not in valid_event_types:
            logger.warning(f"Invalid event_type filter: {event_type}")
            return {"events": [], "total": 0}

        try:
            async with self._db_pool.acquire() as conn:
                events: list[dict[str, Any]] = []

                # Query job events
                job_events = await self._query_job_activity_events(conn, limit, since, event_type)
                events.extend(job_events)

                # Query robot status change events
                robot_events = await self._query_robot_activity_events(
                    conn, limit, since, event_type
                )
                events.extend(robot_events)

                # Sort combined events by timestamp descending
                events.sort(key=lambda e: e["timestamp"], reverse=True)

                # Apply limit after combining
                total = len(events)
                events = events[:limit]

                logger.debug(f"Activity feed: {len(events)} events (total: {total})")

                return {"events": events, "total": total}

        except Exception as e:
            logger.error(f"Failed to fetch activity events: {e}")
            return {"events": [], "total": 0}

    async def _query_job_activity_events(
        self,
        conn: Any,
        limit: int,
        since: datetime | None,
        event_type: str | None,
    ) -> list[dict[str, Any]]:
        """
        Query job-related activity events from pgqueuer_jobs.

        Generates events for job status transitions (started, completed, failed).
        """
        # Map event_type filter to status conditions
        status_filter: str | None = None
        if event_type == "job_started":
            status_filter = "claimed"
        elif event_type == "job_completed":
            status_filter = "completed"
        elif event_type == "job_failed":
            status_filter = "failed"
        elif event_type in ("robot_online", "robot_offline", "schedule_triggered"):
            # These are not job events
            return []

        query_parts = [
            """
            SELECT
                id::text AS job_id,
                workflow_id,
                workflow_name,
                robot_id,
                status,
                created_at,
                started_at AS claimed_at,
                completed_at
            FROM job_queue
            WHERE status IN ('claimed', 'completed', 'failed')
            """
        ]

        params: list[Any] = []
        param_idx = 1

        if status_filter:
            query_parts.append(f"AND status = ${param_idx}")
            params.append(status_filter)
            param_idx += 1

        if since:
            query_parts.append(f"AND created_at >= ${param_idx}")
            params.append(since)
            param_idx += 1

        query_parts.append(f"ORDER BY created_at DESC LIMIT ${param_idx}")
        params.append(limit * 2)  # Fetch extra to account for merging

        query = "\n".join(query_parts)
        rows = await conn.fetch(query, *params)

        events: list[dict[str, Any]] = []

        for row in rows:
            job_id = row["job_id"]
            workflow_name = row["workflow_name"] or row["workflow_id"] or "Unknown Workflow"
            robot_id = row["robot_id"]
            status = row["status"]

            if status == "claimed" and row["claimed_at"]:
                events.append(
                    {
                        "id": f"job_started_{job_id}",
                        "type": "job_started",
                        "timestamp": row["claimed_at"],
                        "title": f"Job started: {workflow_name}",
                        "details": f"Claimed by robot {robot_id}" if robot_id else None,
                        "robot_id": robot_id,
                        "job_id": job_id,
                    }
                )
            elif status == "completed" and row["completed_at"]:
                duration_ms = None
                if row["claimed_at"] and row["completed_at"]:
                    delta = row["completed_at"] - row["claimed_at"]
                    duration_ms = int(delta.total_seconds() * 1000)
                duration_str = f" in {duration_ms}ms" if duration_ms else ""
                events.append(
                    {
                        "id": f"job_completed_{job_id}",
                        "type": "job_completed",
                        "timestamp": row["completed_at"],
                        "title": f"Job completed: {workflow_name}",
                        "details": f"Executed by {robot_id}{duration_str}" if robot_id else None,
                        "robot_id": robot_id,
                        "job_id": job_id,
                    }
                )
            elif status == "failed" and row["completed_at"]:
                events.append(
                    {
                        "id": f"job_failed_{job_id}",
                        "type": "job_failed",
                        "timestamp": row["completed_at"],
                        "title": f"Job failed: {workflow_name}",
                        "details": f"Failed on robot {robot_id}" if robot_id else None,
                        "robot_id": robot_id,
                        "job_id": job_id,
                    }
                )

        return events

    async def _query_robot_activity_events(
        self,
        conn: Any,
        limit: int,
        since: datetime | None,
        event_type: str | None,
    ) -> list[dict[str, Any]]:
        """
        Query robot status change events from robots table.

        Detects online/offline transitions based on status changes.
        """
        if event_type and event_type not in ("robot_online", "robot_offline"):
            return []

        # Check if robots table has status_changed_at column
        # Fall back to using last_seen for status inference
        # Supabase uses: 'offline', 'online', 'busy', 'error', 'maintenance'
        query_parts = [
            """
            SELECT
                robot_id::text AS robot_id,
                hostname,
                status,
                last_seen,
                COALESCE(
                    (metrics->>'status_changed_at')::timestamptz,
                    last_seen
                ) AS status_changed_at
            FROM robots
            WHERE status IN ('online', 'busy', 'offline', 'error')
            """
        ]

        params: list[Any] = []
        param_idx = 1

        if event_type == "robot_online":
            query_parts.append("AND status IN ('online', 'busy')")
        elif event_type == "robot_offline":
            query_parts.append("AND status = 'offline'")

        if since:
            query_parts.append(f"AND last_seen >= ${param_idx}")
            params.append(since)
            param_idx += 1

        query_parts.append(f"ORDER BY last_seen DESC LIMIT ${param_idx}")
        params.append(limit)

        query = "\n".join(query_parts)
        rows = await conn.fetch(query, *params)

        events: list[dict[str, Any]] = []

        for row in rows:
            robot_id = row["robot_id"]
            hostname = row["hostname"] or robot_id
            status = row["status"]
            timestamp = row["status_changed_at"] or row["last_seen"]

            if status == "offline":
                events.append(
                    {
                        "id": f"robot_offline_{robot_id}_{int(timestamp.timestamp())}",
                        "type": "robot_offline",
                        "timestamp": timestamp,
                        "title": f"Robot offline: {hostname}",
                        "details": f"Robot {robot_id} stopped responding",
                        "robot_id": robot_id,
                        "job_id": None,
                    }
                )
            elif status in ("online", "busy"):
                # For online events, we only include if recently seen
                now = datetime.now(UTC)
                if (now - timestamp).total_seconds() < 300:  # Last 5 minutes
                    events.append(
                        {
                            "id": f"robot_online_{robot_id}_{int(timestamp.timestamp())}",
                            "type": "robot_online",
                            "timestamp": timestamp,
                            "title": f"Robot online: {hostname}",
                            "details": f"Robot {robot_id} is now {status}",
                            "robot_id": robot_id,
                            "job_id": None,
                        }
                    )

        return events
