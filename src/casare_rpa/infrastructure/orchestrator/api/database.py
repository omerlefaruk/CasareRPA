"""
Database connection and query utilities for monitoring API.

Provides async database queries for robot, job, and analytics data.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncpg
from loguru import logger


class MonitoringDatabase:
    """Database interface for monitoring queries."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def get_fleet_summary(self) -> Dict[str, Any]:
        """
        Get fleet-wide summary metrics.

        Returns:
            Dictionary with robot counts, active jobs, queue depth
        """
        async with self.pool.acquire() as conn:
            # Count robots by status
            robot_counts = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) FILTER (WHERE status = 'idle') as idle_robots,
                    COUNT(*) FILTER (WHERE status = 'busy') as active_robots,
                    COUNT(*) FILTER (WHERE status = 'offline') as offline_robots,
                    COUNT(*) as total_robots
                FROM robots
                """
            )

            # Count active jobs
            active_jobs = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM job_queue
                WHERE status = 'running'
                """
            )

            # Get queue depth
            queue_depth = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM job_queue
                WHERE status = 'pending'
                """
            )

            return {
                "total_robots": robot_counts["total_robots"] or 0,
                "active_robots": robot_counts["active_robots"] or 0,
                "idle_robots": robot_counts["idle_robots"] or 0,
                "offline_robots": robot_counts["offline_robots"] or 0,
                "active_jobs": active_jobs or 0,
                "queue_depth": queue_depth or 0,
            }

    async def get_robot_list(
        self, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get list of all robots with optional status filter.

        Args:
            status: Filter by robot status (idle/busy/offline)

        Returns:
            List of robot summary dictionaries
        """
        query = """
            SELECT
                robot_id::text as robot_id,
                name,
                hostname,
                status,
                environment,
                (metrics->>'cpu_percent')::float as cpu_percent,
                (metrics->>'memory_mb')::float as memory_mb,
                current_job_ids->0 as current_job_id,
                last_heartbeat,
                last_seen,
                capabilities,
                tags
            FROM robots
        """

        params = []
        if status:
            query += " WHERE status = $1"
            params.append(status)

        query += " ORDER BY last_heartbeat DESC NULLS LAST"

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]

    async def get_robot_details(self, robot_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed metrics for a single robot.

        Args:
            robot_id: Robot identifier

        Returns:
            Robot metrics dictionary or None if not found
        """
        async with self.pool.acquire() as conn:
            # Get robot base info
            robot = await conn.fetchrow(
                """
                SELECT
                    robot_id,
                    hostname,
                    status,
                    cpu_percent,
                    memory_mb,
                    memory_percent,
                    current_job_id,
                    last_heartbeat
                FROM robots
                WHERE robot_id = $1
                """,
                robot_id,
            )

            if not robot:
                return None

            # Get today's job stats
            today_start = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            job_stats = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) FILTER (WHERE status = 'completed') as completed_today,
                    COUNT(*) FILTER (WHERE status = 'failed') as failed_today,
                    AVG(
                        EXTRACT(EPOCH FROM (completed_at - started_at))
                    ) FILTER (WHERE status IN ('completed', 'failed')) as avg_duration_seconds
                FROM job_queue
                WHERE robot_id = $1 AND created_at >= $2
                """,
                robot_id,
                today_start,
            )

            return {
                **dict(robot),
                "jobs_completed_today": job_stats["completed_today"] or 0,
                "jobs_failed_today": job_stats["failed_today"] or 0,
                "average_job_duration_seconds": float(
                    job_stats["avg_duration_seconds"] or 0
                ),
            }

    async def get_job_history(
        self,
        limit: int = 50,
        status: Optional[str] = None,
        workflow_id: Optional[str] = None,
        robot_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get job execution history with filtering.

        Args:
            limit: Max number of jobs to return
            status: Filter by job status
            workflow_id: Filter by workflow ID
            robot_id: Filter by robot ID

        Returns:
            List of job summary dictionaries
        """
        query = """
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

        params = []
        param_idx = 1

        if status:
            query += f" AND status = ${param_idx}"
            params.append(status)
            param_idx += 1

        if workflow_id:
            query += f" AND workflow_id = ${param_idx}"
            params.append(workflow_id)
            param_idx += 1

        if robot_id:
            query += f" AND robot_id = ${param_idx}"
            params.append(robot_id)
            param_idx += 1

        query += f" ORDER BY created_at DESC LIMIT ${param_idx}"
        params.append(limit)

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]

    async def get_job_details(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed execution information for a single job.

        Args:
            job_id: Job identifier

        Returns:
            Job details dictionary or None if not found
        """
        async with self.pool.acquire() as conn:
            # Get job base info
            job = await conn.fetchrow(
                """
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
                    retry_count
                FROM job_queue
                WHERE id = $1
                """,
                job_id,
            )

            if not job:
                return None

            # Get DBOS workflow status if available
            workflow_status = await conn.fetchrow(
                """
                SELECT
                    status,
                    output,
                    error
                FROM dbos.workflow_status
                WHERE workflow_uuid = $1
                """,
                job_id,
            )

            result = dict(job)
            result["node_executions"] = []

            # Parse workflow output for node executions if available
            if workflow_status and workflow_status["output"]:
                node_executions = self._parse_node_execution_breakdown(
                    workflow_status["output"]
                )
                result["node_executions"] = node_executions

            return result

    async def get_analytics(self) -> Dict[str, Any]:
        """
        Get aggregated analytics and statistics.

        Returns:
            Analytics summary dictionary with success rates, percentiles, etc.
        """
        async with self.pool.acquire() as conn:
            # Get job counts and rates
            job_stats = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) as total_jobs,
                    COUNT(*) FILTER (WHERE status = 'completed') as completed,
                    COUNT(*) FILTER (WHERE status = 'failed') as failed,
                    AVG(
                        EXTRACT(EPOCH FROM (completed_at - started_at)) * 1000
                    ) FILTER (WHERE completed_at IS NOT NULL AND started_at IS NOT NULL) as avg_duration,
                    PERCENTILE_CONT(0.50) WITHIN GROUP (
                        ORDER BY EXTRACT(EPOCH FROM (completed_at - started_at)) * 1000
                    ) as p50,
                    PERCENTILE_CONT(0.90) WITHIN GROUP (
                        ORDER BY EXTRACT(EPOCH FROM (completed_at - started_at)) * 1000
                    ) as p90,
                    PERCENTILE_CONT(0.99) WITHIN GROUP (
                        ORDER BY EXTRACT(EPOCH FROM (completed_at - started_at)) * 1000
                    ) as p99
                FROM job_queue
                WHERE created_at >= NOW() - INTERVAL '7 days'
                """
            )

            total_jobs = job_stats["total_jobs"] or 0
            completed = job_stats["completed"] or 0
            failed = job_stats["failed"] or 0

            success_rate = (completed / total_jobs * 100) if total_jobs > 0 else 0.0
            failure_rate = (failed / total_jobs * 100) if total_jobs > 0 else 0.0

            # Get slowest workflows
            slowest_workflows = await conn.fetch(
                """
                SELECT
                    workflow_id,
                    workflow_name,
                    AVG(
                        EXTRACT(EPOCH FROM (completed_at - started_at)) * 1000
                    ) as average_duration_ms
                FROM job_queue
                WHERE status IN ('completed', 'failed')
                  AND completed_at IS NOT NULL AND started_at IS NOT NULL
                  AND created_at >= NOW() - INTERVAL '7 days'
                GROUP BY workflow_id, workflow_name
                ORDER BY average_duration_ms DESC
                LIMIT 5
                """
            )

            # Get error distribution
            error_distribution = await conn.fetch(
                """
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
                    ) as error_type,
                    COUNT(*) as count
                FROM job_queue
                WHERE status = 'failed'
                  AND created_at >= NOW() - INTERVAL '7 days'
                GROUP BY error_type
                ORDER BY count DESC
                LIMIT 10
                """
            )

            # Get self-healing stats (if available)
            self_healing_stats = await self._get_self_healing_stats(conn)
            self_healing_rate = self_healing_stats.get("healing_success_rate")

            return {
                "total_jobs": total_jobs,
                "success_rate": success_rate,
                "failure_rate": failure_rate,
                "average_duration_ms": float(job_stats["avg_duration"] or 0),
                "p50_duration_ms": float(job_stats["p50"] or 0),
                "p90_duration_ms": float(job_stats["p90"] or 0),
                "p99_duration_ms": float(job_stats["p99"] or 0),
                "slowest_workflows": [dict(row) for row in slowest_workflows],
                "error_distribution": [dict(row) for row in error_distribution],
                "self_healing_success_rate": self_healing_rate,
                "self_healing_stats": self_healing_stats,
            }

    def _parse_node_execution_breakdown(
        self, workflow_output: Any
    ) -> List[Dict[str, Any]]:
        """
        Parse node execution timing breakdown from workflow output.

        Extracts per-node execution data including:
        - Node ID and type
        - Execution duration
        - Success/failure status
        - Error information if failed

        Args:
            workflow_output: Raw workflow output (JSON or dict)

        Returns:
            List of node execution records with timing data
        """
        node_executions: List[Dict[str, Any]] = []

        try:
            # Handle both string and dict output formats
            if isinstance(workflow_output, str):
                import orjson

                output_data = orjson.loads(workflow_output)
            else:
                output_data = workflow_output

            if not isinstance(output_data, dict):
                return node_executions

            # Extract node timings from various possible output formats
            # Format 1: Direct node_timings field (from bottleneck_detector format)
            if "node_timings" in output_data:
                for node_id, timing in output_data["node_timings"].items():
                    node_executions.append(self._normalize_node_timing(node_id, timing))

            # Format 2: step_results from DBOS executor checkpoints
            elif "step_results" in output_data:
                for node_id, result in output_data["step_results"].items():
                    if isinstance(result, dict):
                        node_executions.append(
                            self._normalize_node_timing(node_id, result)
                        )

            # Format 3: nodes array with execution data
            elif "nodes" in output_data and isinstance(output_data["nodes"], list):
                for node in output_data["nodes"]:
                    if isinstance(node, dict) and "id" in node:
                        node_executions.append(
                            self._normalize_node_timing(
                                node["id"],
                                node.get("execution", node),
                            )
                        )

            # Format 4: execution_log with timestamped entries
            elif "execution_log" in output_data:
                for entry in output_data["execution_log"]:
                    if isinstance(entry, dict) and "node_id" in entry:
                        node_executions.append(
                            self._normalize_node_timing(
                                entry["node_id"],
                                entry,
                            )
                        )

            # Sort by start time or execution order if available
            node_executions.sort(
                key=lambda n: (
                    n.get("start_time") or n.get("order") or 0,
                    n.get("node_id", ""),
                )
            )

        except Exception as e:
            logger.warning(f"Failed to parse node execution breakdown: {e}")

        return node_executions

    def _normalize_node_timing(self, node_id: str, timing_data: Any) -> Dict[str, Any]:
        """
        Normalize node timing data to a consistent format.

        Args:
            node_id: Node identifier
            timing_data: Raw timing data (various formats)

        Returns:
            Normalized node execution record
        """
        if not isinstance(timing_data, dict):
            return {
                "node_id": node_id,
                "node_type": "unknown",
                "duration_ms": 0,
                "success": True,
            }

        # Extract duration with fallback field names
        duration_ms = (
            timing_data.get("duration_ms")
            or timing_data.get("duration")
            or timing_data.get("elapsed_ms")
            or 0
        )

        # If duration is in seconds, convert to milliseconds
        if isinstance(duration_ms, float) and duration_ms < 1000:
            duration_key = (
                "duration_seconds" in timing_data or "elapsed_seconds" in timing_data
            )
            if duration_key or (
                "duration" in timing_data and timing_data.get("duration", 0) < 100
            ):
                duration_ms = duration_ms * 1000

        # Extract success status with various field names
        success = timing_data.get(
            "success",
            timing_data.get(
                "succeeded",
                timing_data.get("status") in (None, "completed", "success"),
            ),
        )

        return {
            "node_id": node_id,
            "node_type": timing_data.get(
                "node_type",
                timing_data.get("type", "unknown"),
            ),
            "duration_ms": float(duration_ms),
            "success": bool(success),
            "error_type": timing_data.get(
                "error_type",
                timing_data.get("error", {}).get("type")
                if isinstance(timing_data.get("error"), dict)
                else None,
            ),
            "error_message": timing_data.get(
                "error_message",
                timing_data.get("error")
                if isinstance(timing_data.get("error"), str)
                else timing_data.get("error", {}).get("message")
                if isinstance(timing_data.get("error"), dict)
                else None,
            ),
            "start_time": timing_data.get(
                "start_time",
                timing_data.get("started_at"),
            ),
            "end_time": timing_data.get(
                "end_time",
                timing_data.get("completed_at"),
            ),
            "retry_count": timing_data.get("retry_count", 0),
            "order": timing_data.get("order", timing_data.get("step", 0)),
        }

    async def _get_self_healing_stats(self, conn: asyncpg.Connection) -> Dict[str, Any]:
        """
        Get self-healing selector statistics from telemetry data.

        Queries the healing_events table (if it exists) to calculate:
        - Total healing attempts
        - Success rate by tier
        - Average healing time
        - Problematic selectors

        Args:
            conn: Active database connection

        Returns:
            Dictionary with self-healing statistics
        """
        try:
            # Check if the healing_events table exists
            table_exists = await conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'healing_events'
                )
                """
            )

            if not table_exists:
                return {
                    "available": False,
                    "message": "Self-healing telemetry table not configured",
                }

            # Get aggregate statistics for the last 7 days
            stats = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) as total_attempts,
                    COUNT(*) FILTER (WHERE success = true) as successful_heals,
                    COUNT(*) FILTER (WHERE tier_used = 'original') as original_successes,
                    COUNT(*) FILTER (
                        WHERE success = true AND tier_used != 'original'
                    ) as healed_successes,
                    COUNT(*) FILTER (WHERE success = false) as failures,
                    AVG(healing_time_ms) FILTER (
                        WHERE success = true AND tier_used != 'original'
                    ) as avg_healing_time_ms,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (
                        ORDER BY healing_time_ms
                    ) FILTER (
                        WHERE success = true AND tier_used != 'original'
                    ) as p95_healing_time_ms
                FROM healing_events
                WHERE timestamp >= NOW() - INTERVAL '7 days'
                """
            )

            if not stats or stats["total_attempts"] == 0:
                return {
                    "available": True,
                    "total_attempts": 0,
                    "healing_success_rate": None,
                    "message": "No healing events in the last 7 days",
                }

            total = stats["total_attempts"]
            successful = stats["successful_heals"] or 0
            healed = stats["healed_successes"] or 0
            failures = stats["failures"] or 0

            # Calculate rates
            success_rate = (successful / total * 100) if total > 0 else 0.0
            healing_rate = ((healed + failures) / total * 100) if total > 0 else 0.0
            healing_success_rate = (
                (healed / (healed + failures) * 100) if (healed + failures) > 0 else 0.0
            )

            # Get tier breakdown
            tier_breakdown = await conn.fetch(
                """
                SELECT
                    tier_used,
                    COUNT(*) as count,
                    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
                FROM healing_events
                WHERE timestamp >= NOW() - INTERVAL '7 days'
                  AND success = true
                GROUP BY tier_used
                ORDER BY count DESC
                """
            )

            # Get problematic selectors (frequently need healing or fail)
            problematic = await conn.fetch(
                """
                SELECT
                    selector,
                    COUNT(*) as total_uses,
                    COUNT(*) FILTER (WHERE success = true) as successes,
                    COUNT(*) FILTER (
                        WHERE tier_used != 'original'
                    ) as needed_healing,
                    ROUND(
                        COUNT(*) FILTER (WHERE success = true) * 100.0 / COUNT(*),
                        2
                    ) as success_rate
                FROM healing_events
                WHERE timestamp >= NOW() - INTERVAL '7 days'
                GROUP BY selector
                HAVING COUNT(*) >= 5
                   AND COUNT(*) FILTER (WHERE success = true) * 1.0 / COUNT(*) < 0.9
                ORDER BY success_rate ASC
                LIMIT 5
                """
            )

            return {
                "available": True,
                "total_attempts": total,
                "original_successes": stats["original_successes"] or 0,
                "healed_successes": healed,
                "failures": failures,
                "success_rate": round(success_rate, 2),
                "healing_rate": round(healing_rate, 2),
                "healing_success_rate": round(healing_success_rate, 2),
                "avg_healing_time_ms": round(
                    float(stats["avg_healing_time_ms"] or 0), 2
                ),
                "p95_healing_time_ms": round(
                    float(stats["p95_healing_time_ms"] or 0), 2
                ),
                "tier_breakdown": [
                    {
                        "tier": row["tier_used"],
                        "count": row["count"],
                        "percentage": float(row["percentage"]),
                    }
                    for row in tier_breakdown
                ],
                "problematic_selectors": [
                    {
                        "selector": row["selector"],
                        "total_uses": row["total_uses"],
                        "success_rate": float(row["success_rate"]),
                        "needed_healing": row["needed_healing"],
                    }
                    for row in problematic
                ],
            }

        except Exception as e:
            logger.warning(f"Failed to get self-healing stats: {e}")
            return {
                "available": False,
                "error": str(e),
            }


async def create_db_pool(database_url: str) -> asyncpg.Pool:
    """
    Create async PostgreSQL connection pool.

    Args:
        database_url: PostgreSQL connection string

    Returns:
        asyncpg Pool instance
    """
    logger.info(f"Creating database connection pool: {database_url.split('@')[-1]}")

    pool = await asyncpg.create_pool(
        database_url,
        min_size=2,
        max_size=10,
        command_timeout=60,
        server_settings={"application_name": "casare-rpa-monitoring"},
    )

    logger.info("Database connection pool created successfully")
    return pool
