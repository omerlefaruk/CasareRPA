"""
Pydantic models for API request/response schemas.

Type-safe data models matching React dashboard TypeScript interfaces.
"""

from datetime import datetime

from pydantic import BaseModel, Field


# Fleet Metrics Models
class FleetMetrics(BaseModel):
    """Fleet-wide metrics summary."""

    total_robots: int = Field(..., description="Total registered robots")
    active_robots: int = Field(..., description="Robots currently executing jobs")
    idle_robots: int = Field(..., description="Robots available for work")
    offline_robots: int = Field(..., description="Robots not responding to heartbeat")
    total_jobs_today: int = Field(..., description="Total jobs executed today")
    active_jobs: int = Field(..., description="Jobs currently being executed")
    queue_depth: int = Field(..., description="Pending jobs in queue")
    average_job_duration_seconds: float = Field(
        ..., description="Average job duration across fleet"
    )


# Robot Models
class RobotSummary(BaseModel):
    """Robot summary for list view."""

    robot_id: str
    hostname: str
    status: str = Field(..., description="idle | busy | offline | failed")
    cpu_percent: float
    memory_mb: float
    current_job_id: str | None = None
    last_heartbeat: datetime


class RobotMetrics(BaseModel):
    """Detailed robot metrics."""

    robot_id: str
    hostname: str
    status: str
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    current_job_id: str | None = None
    last_heartbeat: datetime
    jobs_completed_today: int
    jobs_failed_today: int
    average_job_duration_seconds: float


# Job Models
class JobSummary(BaseModel):
    """Job summary for history table."""

    job_id: str
    workflow_id: str
    workflow_name: str | None = None
    robot_id: str | None = None
    status: str = Field(..., description="pending | claimed | completed | failed")
    created_at: datetime
    completed_at: datetime | None = None
    duration_ms: int | None = None


class JobDetails(BaseModel):
    """Detailed job execution information."""

    job_id: str
    workflow_id: str
    workflow_name: str | None = None
    robot_id: str | None = None
    status: str
    created_at: datetime
    claimed_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int | None = None
    error_message: str | None = None
    error_type: str | None = None
    retry_count: int = 0
    node_executions: list[dict] = Field(
        default_factory=list, description="Per-node execution breakdown"
    )


# Analytics Models
class WorkflowStats(BaseModel):
    """Statistics for a single workflow."""

    workflow_id: str
    workflow_name: str
    average_duration_ms: float


class ErrorStats(BaseModel):
    """Error distribution statistics."""

    error_type: str
    count: int


class AnalyticsSummary(BaseModel):
    """Aggregated analytics and trends."""

    total_jobs: int
    success_rate: float = Field(..., ge=0, le=100, description="Percentage of successful jobs")
    failure_rate: float = Field(..., ge=0, le=100, description="Percentage of failed jobs")
    average_duration_ms: float
    p50_duration_ms: float = Field(..., description="Median job duration")
    p90_duration_ms: float = Field(..., description="90th percentile")
    p99_duration_ms: float = Field(..., description="99th percentile")
    slowest_workflows: list[WorkflowStats] = Field(
        default_factory=list, description="Top 5 slowest workflows"
    )
    error_distribution: list[ErrorStats] = Field(
        default_factory=list, description="Error types and counts"
    )
    self_healing_success_rate: float | None = Field(None, description="Self-healing recovery rate")


# WebSocket Message Models
class LiveJobUpdate(BaseModel):
    """Real-time job status update."""

    job_id: str
    status: str
    timestamp: datetime


class RobotStatusUpdate(BaseModel):
    """Robot heartbeat update."""

    robot_id: str
    status: str
    cpu_percent: float
    memory_mb: float
    timestamp: datetime


class QueueMetricsUpdate(BaseModel):
    """Queue depth update."""

    depth: int
    timestamp: datetime


# Activity Feed Models
class ActivityEvent(BaseModel):
    """Single activity event for the dashboard feed."""

    id: str = Field(..., description="Unique event identifier")
    type: str = Field(
        ...,
        description="Event type: job_started, job_completed, job_failed, robot_online, robot_offline, schedule_triggered",
    )
    timestamp: datetime = Field(..., description="When the event occurred")
    title: str = Field(..., description="Human-readable event title")
    details: str | None = Field(None, description="Additional event details")
    robot_id: str | None = Field(None, description="Associated robot ID")
    job_id: str | None = Field(None, description="Associated job ID")


class ActivityResponse(BaseModel):
    """Response for activity feed endpoint."""

    events: list[ActivityEvent] = Field(default_factory=list, description="List of activity events")
    total: int = Field(..., description="Total number of events matching filters")
