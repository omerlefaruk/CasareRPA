"""
Data adapters for monitoring API.

Maps between infrastructure layer (RPAMetricsCollector, MetricsAggregator)
and API response models (Pydantic).
"""

from datetime import datetime
from typing import List, Dict, Optional

from loguru import logger

from casare_rpa.infrastructure.observability.metrics import (
    RPAMetricsCollector,
    RobotMetrics as InfraRobotMetrics,
    JobMetrics as InfraJobMetrics,
)
from casare_rpa.infrastructure.analytics.metrics_aggregator import MetricsAggregator


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
    ):
        self.metrics = metrics_collector
        self.analytics = analytics_aggregator

    def get_fleet_summary(self) -> Dict:
        """
        Get fleet-wide metrics summary.

        Returns:
            Dict matching FleetMetrics Pydantic model
        """
        all_robots = self.metrics.get_all_robot_metrics()
        queue_depth = self.metrics.get_queue_depth()
        active_jobs = len(self.metrics.get_active_jobs())

        total_robots = len(all_robots)
        active_robots = sum(1 for r in all_robots.values() if r.status.value == "busy")
        idle_robots = sum(1 for r in all_robots.values() if r.status.value == "idle")
        offline_robots = sum(
            1 for r in all_robots.values() if r.status.value == "offline"
        )

        return {
            "total_robots": total_robots,
            "active_robots": active_robots,
            "idle_robots": idle_robots,
            "offline_robots": offline_robots,
            "active_jobs": active_jobs,
            "queue_depth": queue_depth,
        }

    def get_robot_list(self, status: Optional[str] = None) -> List[Dict]:
        """
        Get list of all robots with optional status filter.

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
            result.append(
                {
                    "robot_id": robot_id,
                    "hostname": robot_id,  # TODO: Get actual hostname from metadata
                    "status": robot_metrics.status.value,
                    "cpu_percent": 0.0,  # TODO: Get from system metrics
                    "memory_mb": 0.0,  # TODO: Get from system metrics
                    "current_job_id": robot_metrics.current_job_id,
                    "last_heartbeat": robot_metrics.last_job_at or datetime.now(),
                }
            )

        return result

    def get_robot_details(self, robot_id: str) -> Optional[Dict]:
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

        return {
            "robot_id": robot_id,
            "hostname": robot_id,  # TODO: Get actual hostname
            "status": robot_metrics.status.value,
            "cpu_percent": 0.0,  # TODO: System metrics
            "memory_mb": 0.0,  # TODO: System metrics
            "memory_percent": 0.0,  # TODO: System metrics
            "current_job_id": robot_metrics.current_job_id,
            "last_heartbeat": robot_metrics.last_job_at or datetime.now(),
            "jobs_completed_today": robot_metrics.jobs_completed,
            "jobs_failed_today": robot_metrics.jobs_failed,
            "average_job_duration_seconds": 0.0,  # TODO: Calculate from history
        }

    def get_job_history(
        self,
        limit: int = 50,
        status: Optional[str] = None,
        workflow_id: Optional[str] = None,
        robot_id: Optional[str] = None,
    ) -> List[Dict]:
        """
        Get job execution history.

        NOTE: PR #33 metrics collector doesn't store job history,
        so this needs database integration. Returning empty for now.

        Args:
            limit: Max jobs to return
            status: Filter by status
            workflow_id: Filter by workflow
            robot_id: Filter by robot

        Returns:
            List of dicts matching JobSummary Pydantic model
        """
        logger.warning(
            "Job history requires database queries - implement in next phase"
        )
        # TODO: Query database (pgqueuer_jobs table) using asyncpg
        return []

    def get_job_details(self, job_id: str) -> Optional[Dict]:
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

        # For historical jobs, need database
        logger.warning(
            "Historical job details require database queries - implement in next phase"
        )
        # TODO: Query database (pgqueuer_jobs + dbos tables)
        return None

    def get_analytics(self) -> Dict:
        """
        Get aggregated analytics and statistics.

        Uses MetricsAggregator for advanced calculations (percentiles, trends).

        Returns:
            Dict matching AnalyticsSummary Pydantic model
        """
        job_metrics = self.metrics.get_job_metrics()

        # Basic metrics from RPAMetricsCollector
        total_jobs = job_metrics.total_jobs
        success_rate = job_metrics.success_rate
        failure_rate = 100.0 - success_rate if total_jobs > 0 else 0.0

        # For advanced analytics, would use MetricsAggregator
        # but it requires database records. Return basic metrics for now.
        logger.warning(
            "Advanced analytics require database integration - basic stats only"
        )

        return {
            "total_jobs": total_jobs,
            "success_rate": success_rate,
            "failure_rate": failure_rate,
            "average_duration_ms": job_metrics.average_duration_seconds * 1000,
            "p50_duration_ms": 0.0,  # TODO: Calculate from database
            "p90_duration_ms": 0.0,  # TODO: Calculate from database
            "p99_duration_ms": 0.0,  # TODO: Calculate from database
            "slowest_workflows": [],  # TODO: Query from MetricsAggregator
            "error_distribution": [],  # TODO: Query from MetricsAggregator
            "self_healing_success_rate": None,  # TODO: Get from healing stats
        }
