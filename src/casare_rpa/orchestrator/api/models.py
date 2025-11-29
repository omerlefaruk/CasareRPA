"""
Pydantic models for API request/response schemas.

Type-safe data models matching React dashboard TypeScript interfaces.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# Fleet Metrics Models
class FleetMetrics(BaseModel):
    """Fleet-wide metrics summary."""

    total_robots: int = Field(..., description="Total registered robots")
    active_robots: int = Field(..., description="Robots currently executing jobs")
    idle_robots: int = Field(..., description="Robots available for work")
    offline_robots: int = Field(..., description="Robots not responding to heartbeat")
    active_jobs: int = Field(..., description="Jobs currently being executed")
    queue_depth: int = Field(..., description="Pending jobs in queue")


# Robot Models
class RobotSummary(BaseModel):
    """Robot summary for list view."""

    robot_id: str
    hostname: str
    status: str = Field(..., description="idle | busy | offline | failed")
    cpu_percent: float
    memory_mb: float
    current_job_id: Optional[str] = None
    last_heartbeat: datetime


class RobotMetrics(BaseModel):
    """Detailed robot metrics."""

    robot_id: str
    hostname: str
    status: str
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    current_job_id: Optional[str] = None
    last_heartbeat: datetime
    jobs_completed_today: int
    jobs_failed_today: int
    average_job_duration_seconds: float


# Job Models
class JobSummary(BaseModel):
    """Job summary for history table."""

    job_id: str
    workflow_id: str
    workflow_name: Optional[str] = None
    robot_id: Optional[str] = None
    status: str = Field(..., description="pending | claimed | completed | failed")
    created_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None


class JobDetails(BaseModel):
    """Detailed job execution information."""

    job_id: str
    workflow_id: str
    workflow_name: Optional[str] = None
    robot_id: Optional[str] = None
    status: str
    created_at: datetime
    claimed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    retry_count: int = 0
    node_executions: List[dict] = Field(
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
    success_rate: float = Field(
        ..., ge=0, le=100, description="Percentage of successful jobs"
    )
    failure_rate: float = Field(
        ..., ge=0, le=100, description="Percentage of failed jobs"
    )
    average_duration_ms: float
    p50_duration_ms: float = Field(..., description="Median job duration")
    p90_duration_ms: float = Field(..., description="90th percentile")
    p99_duration_ms: float = Field(..., description="99th percentile")
    slowest_workflows: List[WorkflowStats] = Field(
        default_factory=list, description="Top 5 slowest workflows"
    )
    error_distribution: List[ErrorStats] = Field(
        default_factory=list, description="Error types and counts"
    )
    self_healing_success_rate: Optional[float] = Field(
        None, description="Self-healing recovery rate"
    )


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
