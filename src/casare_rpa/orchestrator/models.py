"""
Data models for CasareRPA Orchestrator.
Defines schemas for jobs, schedules, workflows, and robots.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
import uuid


class JobStatus(Enum):
    """Job execution status."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class JobPriority(Enum):
    """Job priority levels."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class RobotStatus(Enum):
    """Robot connection status."""
    OFFLINE = "offline"
    ONLINE = "online"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class WorkflowStatus(Enum):
    """Workflow lifecycle status."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ScheduleFrequency(Enum):
    """Schedule frequency types."""
    ONCE = "once"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CRON = "cron"


@dataclass
class Robot:
    """Robot agent representation."""
    id: str
    name: str
    status: RobotStatus = RobotStatus.OFFLINE
    environment: str = "default"
    max_concurrent_jobs: int = 1
    current_jobs: int = 0
    last_seen: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None
    created_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Robot":
        """Create Robot from dictionary."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", "Unknown"),
            status=RobotStatus(data.get("status", "offline")),
            environment=data.get("environment", "default"),
            max_concurrent_jobs=data.get("max_concurrent_jobs", 1),
            current_jobs=data.get("current_jobs", 0),
            last_seen=data.get("last_seen"),
            last_heartbeat=data.get("last_heartbeat"),
            created_at=data.get("created_at"),
            tags=data.get("tags", []),
            metrics=data.get("metrics", {})
        )

    @property
    def is_available(self) -> bool:
        """Check if robot can accept new jobs."""
        return (
            self.status == RobotStatus.ONLINE and
            self.current_jobs < self.max_concurrent_jobs
        )

    @property
    def utilization(self) -> float:
        """Get robot utilization percentage."""
        if self.max_concurrent_jobs == 0:
            return 0.0
        return (self.current_jobs / self.max_concurrent_jobs) * 100


@dataclass
class Workflow:
    """Workflow definition."""
    id: str
    name: str
    description: str = ""
    json_definition: str = "{}"
    version: int = 1
    status: WorkflowStatus = WorkflowStatus.DRAFT
    created_by: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    execution_count: int = 0
    success_count: int = 0
    avg_duration_ms: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Workflow":
        """Create Workflow from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", "Untitled"),
            description=data.get("description", ""),
            json_definition=data.get("json_definition", "{}"),
            version=data.get("version", 1),
            status=WorkflowStatus(data.get("status", "draft")),
            created_by=data.get("created_by", ""),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            tags=data.get("tags", []),
            execution_count=data.get("execution_count", 0),
            success_count=data.get("success_count", 0),
            avg_duration_ms=data.get("avg_duration_ms", 0)
        )

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.execution_count == 0:
            return 0.0
        return (self.success_count / self.execution_count) * 100


@dataclass
class Job:
    """Job execution record."""
    id: str
    workflow_id: str
    workflow_name: str
    robot_id: str
    robot_name: str = ""
    status: JobStatus = JobStatus.PENDING
    priority: JobPriority = JobPriority.NORMAL
    workflow_json: str = "{}"
    scheduled_time: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: int = 0
    progress: int = 0  # 0-100 percentage
    current_node: str = ""
    result: Dict[str, Any] = field(default_factory=dict)
    logs: str = ""
    error_message: str = ""
    created_at: Optional[datetime] = None
    created_by: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Job":
        """Create Job from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            workflow_id=data.get("workflow_id", ""),
            workflow_name=data.get("workflow_name", "Unknown"),
            robot_id=data.get("robot_id", ""),
            robot_name=data.get("robot_name", ""),
            status=JobStatus(data.get("status", "pending")),
            priority=JobPriority(data.get("priority", 1)),
            workflow_json=data.get("workflow", data.get("workflow_json", "{}")),
            scheduled_time=data.get("scheduled_time"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            duration_ms=data.get("duration_ms", 0),
            progress=data.get("progress", 0),
            current_node=data.get("current_node", ""),
            result=data.get("result", {}),
            logs=data.get("logs", ""),
            error_message=data.get("error_message", ""),
            created_at=data.get("created_at"),
            created_by=data.get("created_by", "")
        )

    @property
    def is_terminal(self) -> bool:
        """Check if job is in a terminal state."""
        return self.status in (
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
            JobStatus.TIMEOUT
        )

    @property
    def duration_formatted(self) -> str:
        """Get formatted duration string."""
        if self.duration_ms == 0:
            return "-"
        seconds = self.duration_ms / 1000
        if seconds < 60:
            return f"{seconds:.1f}s"
        minutes = seconds / 60
        if minutes < 60:
            return f"{minutes:.1f}m"
        hours = minutes / 60
        return f"{hours:.1f}h"


@dataclass
class Schedule:
    """Workflow schedule definition."""
    id: str
    name: str
    workflow_id: str
    workflow_name: str = ""
    robot_id: Optional[str] = None  # None = any available robot
    robot_name: str = ""
    frequency: ScheduleFrequency = ScheduleFrequency.DAILY
    cron_expression: str = ""
    timezone: str = "UTC"
    enabled: bool = True
    priority: JobPriority = JobPriority.NORMAL
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    success_count: int = 0
    created_at: Optional[datetime] = None
    created_by: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Schedule":
        """Create Schedule from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            workflow_id=data.get("workflow_id", ""),
            workflow_name=data.get("workflow_name", ""),
            robot_id=data.get("robot_id"),
            robot_name=data.get("robot_name", ""),
            frequency=ScheduleFrequency(data.get("frequency", "daily")),
            cron_expression=data.get("cron_expression", ""),
            timezone=data.get("timezone", "UTC"),
            enabled=data.get("enabled", True),
            priority=JobPriority(data.get("priority", 1)),
            last_run=data.get("last_run"),
            next_run=data.get("next_run"),
            run_count=data.get("run_count", 0),
            success_count=data.get("success_count", 0),
            created_at=data.get("created_at"),
            created_by=data.get("created_by", "")
        )

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.run_count == 0:
            return 0.0
        return (self.success_count / self.run_count) * 100


@dataclass
class DashboardMetrics:
    """Dashboard KPI metrics."""
    # Job metrics
    total_jobs_today: int = 0
    total_jobs_week: int = 0
    total_jobs_month: int = 0
    jobs_running: int = 0
    jobs_queued: int = 0
    jobs_completed_today: int = 0
    jobs_failed_today: int = 0

    # Success rates
    success_rate_today: float = 0.0
    success_rate_week: float = 0.0
    success_rate_month: float = 0.0

    # Robot metrics
    robots_total: int = 0
    robots_online: int = 0
    robots_busy: int = 0
    robot_utilization: float = 0.0

    # Performance metrics
    avg_execution_time_ms: int = 0
    avg_queue_wait_ms: int = 0
    throughput_per_hour: float = 0.0

    # Workflow metrics
    workflows_total: int = 0
    workflows_published: int = 0
    schedules_active: int = 0

    @property
    def avg_execution_time_formatted(self) -> str:
        """Get formatted average execution time."""
        if self.avg_execution_time_ms == 0:
            return "-"
        seconds = self.avg_execution_time_ms / 1000
        if seconds < 60:
            return f"{seconds:.1f}s"
        minutes = seconds / 60
        return f"{minutes:.1f}m"


@dataclass
class JobHistoryEntry:
    """Entry for job execution history chart."""
    date: str
    total: int = 0
    completed: int = 0
    failed: int = 0

    @property
    def success_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return (self.completed / self.total) * 100
