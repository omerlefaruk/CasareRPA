"""
Metrics service.
Calculates dashboard KPIs and job history for visualization.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional


from casare_rpa.domain.orchestrator.entities import (
    Robot,
    Job,
    Workflow,
    Schedule,
    RobotStatus,
    JobStatus,
    WorkflowStatus,
    DashboardMetrics,
    JobHistoryEntry,
)


class MetricsService:
    """Service for calculating orchestrator metrics and KPIs."""

    async def calculate_dashboard_metrics(
        self,
        robots: List[Robot],
        jobs: List[Job],
        workflows: List[Workflow],
        schedules: List[Schedule],
    ) -> DashboardMetrics:
        """Calculate dashboard KPI metrics."""
        metrics = DashboardMetrics()

        # Robot metrics
        metrics.robots_total = len(robots)
        metrics.robots_online = len(
            [r for r in robots if r.status == RobotStatus.ONLINE]
        )
        metrics.robots_busy = len([r for r in robots if r.status == RobotStatus.BUSY])

        if metrics.robots_total > 0:
            total_utilization = sum(r.utilization for r in robots)
            metrics.robot_utilization = total_utilization / metrics.robots_total

        # Job metrics - time-based filtering
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)
        month_start = today_start - timedelta(days=30)

        jobs_today = []
        jobs_week = []
        jobs_month = []

        for job in jobs:
            created = self._parse_date(job.created_at)
            if created:
                if created >= today_start:
                    jobs_today.append(job)
                if created >= week_start:
                    jobs_week.append(job)
                if created >= month_start:
                    jobs_month.append(job)

        metrics.total_jobs_today = len(jobs_today)
        metrics.total_jobs_week = len(jobs_week)
        metrics.total_jobs_month = len(jobs_month)

        metrics.jobs_running = len([j for j in jobs if j.status == JobStatus.RUNNING])
        metrics.jobs_queued = len(
            [j for j in jobs if j.status in (JobStatus.PENDING, JobStatus.QUEUED)]
        )

        completed_today = [j for j in jobs_today if j.status == JobStatus.COMPLETED]
        failed_today = [j for j in jobs_today if j.status == JobStatus.FAILED]
        metrics.jobs_completed_today = len(completed_today)
        metrics.jobs_failed_today = len(failed_today)

        # Success rates
        if metrics.total_jobs_today > 0:
            metrics.success_rate_today = (
                metrics.jobs_completed_today / metrics.total_jobs_today
            ) * 100
        if metrics.total_jobs_week > 0:
            completed_week = len(
                [j for j in jobs_week if j.status == JobStatus.COMPLETED]
            )
            metrics.success_rate_week = (completed_week / metrics.total_jobs_week) * 100
        if metrics.total_jobs_month > 0:
            completed_month = len(
                [j for j in jobs_month if j.status == JobStatus.COMPLETED]
            )
            metrics.success_rate_month = (
                completed_month / metrics.total_jobs_month
            ) * 100

        # Performance metrics
        completed_jobs = [
            j for j in jobs if j.status == JobStatus.COMPLETED and j.duration_ms > 0
        ]
        if completed_jobs:
            metrics.avg_execution_time_ms = sum(
                j.duration_ms for j in completed_jobs
            ) // len(completed_jobs)

        # Throughput (jobs per hour in last 24h)
        if jobs_today:
            hours_elapsed = max(1, (now - today_start).total_seconds() / 3600)
            metrics.throughput_per_hour = len(jobs_today) / hours_elapsed

        # Workflow metrics
        metrics.workflows_total = len(workflows)
        metrics.workflows_published = len(
            [w for w in workflows if w.status == WorkflowStatus.PUBLISHED]
        )

        # Schedule metrics
        metrics.schedules_active = len([s for s in schedules if s.enabled])

        return metrics

    async def calculate_job_history(
        self, jobs: List[Job], days: int = 7
    ) -> List[JobHistoryEntry]:
        """Get job execution history for charting."""
        now = datetime.now(timezone.utc)

        history: Dict[str, JobHistoryEntry] = {}

        for i in range(days):
            date = (now - timedelta(days=i)).strftime("%Y-%m-%d")
            history[date] = JobHistoryEntry(date=date)

        for job in jobs:
            created = self._parse_date(job.created_at)
            if created:
                date_key = created.strftime("%Y-%m-%d")
                if date_key in history:
                    history[date_key].total += 1
                    if job.status == JobStatus.COMPLETED:
                        history[date_key].completed += 1
                    elif job.status == JobStatus.FAILED:
                        history[date_key].failed += 1

        # Return sorted by date ascending
        return sorted(history.values(), key=lambda x: x.date)

    def _parse_date(self, date_str) -> Optional[datetime]:
        """Parse date string to datetime."""
        if not date_str:
            return None
        if isinstance(date_str, datetime):
            return date_str
        try:
            return datetime.fromisoformat(
                date_str.replace("Z", "+00:00").replace("+00:00", "")
            )
        except (ValueError, TypeError):
            return None
