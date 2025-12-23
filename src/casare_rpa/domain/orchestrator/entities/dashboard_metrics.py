"""Dashboard metrics value object."""

from dataclasses import dataclass, field


@dataclass
class JobHistoryEntry:
    """Single job history entry for charts."""

    timestamp: str
    completed: int = 0
    failed: int = 0
    cancelled: int = 0


@dataclass
class DashboardMetrics:
    """Dashboard KPI metrics value object."""

    # Robot metrics
    robots_total: int = 0
    robots_online: int = 0
    robots_busy: int = 0
    robots_offline: int = 0
    robot_utilization: float = 0.0

    # Job metrics - today
    total_jobs_today: int = 0
    jobs_completed_today: int = 0
    jobs_failed_today: int = 0
    jobs_running: int = 0
    jobs_queued: int = 0

    # Job metrics - week/month
    total_jobs_week: int = 0
    total_jobs_month: int = 0

    # Success rates
    success_rate_today: float = 0.0
    success_rate_week: float = 0.0
    success_rate_month: float = 0.0

    # Performance metrics
    avg_duration_ms: float = 0.0
    min_duration_ms: float = 0.0
    max_duration_ms: float = 0.0

    # Workflow metrics
    workflows_total: int = 0
    workflows_published: int = 0

    # Schedule metrics
    schedules_total: int = 0
    schedules_enabled: int = 0

    # Job history for charts
    job_history: list[JobHistoryEntry] = field(default_factory=list)
