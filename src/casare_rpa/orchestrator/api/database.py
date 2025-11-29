"""
Database connection and query utilities for monitoring API.

Provides async database queries for robot, job, and analytics data.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
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
                FROM pgqueuer_jobs
                WHERE status IN ('claimed', 'running')
                """
            )

            # Get queue depth
            queue_depth = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM pgqueuer_jobs
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

    async def get_robot_list(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of all robots with optional status filter.

        Args:
            status: Filter by robot status (idle/busy/offline)

        Returns:
            List of robot summary dictionaries
        """
        query = """
            SELECT
                robot_id,
                hostname,
                status,
                cpu_percent,
                memory_mb,
                current_job_id,
                last_heartbeat
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
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            job_stats = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) FILTER (WHERE status = 'completed') as completed_today,
                    COUNT(*) FILTER (WHERE status = 'failed') as failed_today,
                    AVG(duration_ms / 1000.0) FILTER (WHERE status IN ('completed', 'failed')) as avg_duration_seconds
                FROM pgqueuer_jobs
                WHERE robot_id = $1 AND created_at >= $2
                """,
                robot_id,
                today_start,
            )

            return {
                **dict(robot),
                "jobs_completed_today": job_stats["completed_today"] or 0,
                "jobs_failed_today": job_stats["failed_today"] or 0,
                "average_job_duration_seconds": float(job_stats["avg_duration_seconds"] or 0),
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
                job_id,
                workflow_id,
                workflow_name,
                robot_id,
                status,
                created_at,
                completed_at,
                duration_ms
            FROM pgqueuer_jobs
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
                    job_id,
                    workflow_id,
                    workflow_name,
                    robot_id,
                    status,
                    created_at,
                    claimed_at,
                    completed_at,
                    duration_ms,
                    error_message,
                    error_type,
                    retry_count
                FROM pgqueuer_jobs
                WHERE job_id = $1
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
                # TODO: Parse node execution breakdown from workflow output
                pass

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
                    AVG(duration_ms) FILTER (WHERE duration_ms IS NOT NULL) as avg_duration,
                    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY duration_ms) as p50,
                    PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY duration_ms) as p90,
                    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY duration_ms) as p99
                FROM pgqueuer_jobs
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
                    AVG(duration_ms) as average_duration_ms
                FROM pgqueuer_jobs
                WHERE status IN ('completed', 'failed')
                  AND duration_ms IS NOT NULL
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
                    COALESCE(error_type, 'UnknownError') as error_type,
                    COUNT(*) as count
                FROM pgqueuer_jobs
                WHERE status = 'failed'
                  AND created_at >= NOW() - INTERVAL '7 days'
                GROUP BY error_type
                ORDER BY count DESC
                LIMIT 10
                """
            )

            # Get self-healing stats (if available)
            # TODO: Implement self-healing tracking
            self_healing_rate = None

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
