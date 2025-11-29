"""
CasareRPA Infrastructure: Metrics Aggregation Engine

Provides comprehensive analytics and reporting for workflow monitoring:
- Real-time execution metrics
- Historical trend analysis
- Percentile-based duration statistics (p50, p95, p99)
- Resource utilization tracking
- Cost analysis (robot-hours, cloud costs)
- Bottleneck identification
- Workflow efficiency scoring
- Comparative analysis (version A vs B)
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from threading import Lock
from typing import Any, Callable, Dict, List, Optional, Tuple

from loguru import logger


class AggregationPeriod(str, Enum):
    """Time period for metrics aggregation."""

    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


@dataclass
class TimeSeriesDataPoint:
    """Single data point in a time series."""

    timestamp: datetime
    value: float
    count: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": round(self.value, 2),
            "count": self.count,
            "metadata": self.metadata,
        }


@dataclass
class ExecutionDistribution:
    """Statistical distribution of execution times."""

    total_executions: int = 0
    min_ms: float = 0.0
    max_ms: float = 0.0
    mean_ms: float = 0.0
    median_ms: float = 0.0
    std_dev_ms: float = 0.0
    p50_ms: float = 0.0
    p75_ms: float = 0.0
    p90_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0

    @classmethod
    def from_durations(cls, durations: List[float]) -> "ExecutionDistribution":
        """
        Calculate distribution from a list of durations.

        Args:
            durations: List of execution durations in milliseconds.

        Returns:
            Populated ExecutionDistribution.
        """
        if not durations:
            return cls()

        sorted_durations = sorted(durations)
        n = len(sorted_durations)

        def percentile(data: List[float], p: float) -> float:
            """Calculate percentile value."""
            if not data:
                return 0.0
            k = (n - 1) * (p / 100.0)
            f = int(k)
            c = f + 1 if f + 1 < n else f
            d = k - f
            return data[f] + d * (data[c] - data[f]) if c != f else data[f]

        mean = statistics.mean(sorted_durations)
        std_dev = statistics.stdev(sorted_durations) if n > 1 else 0.0

        return cls(
            total_executions=n,
            min_ms=sorted_durations[0],
            max_ms=sorted_durations[-1],
            mean_ms=mean,
            median_ms=statistics.median(sorted_durations),
            std_dev_ms=std_dev,
            p50_ms=percentile(sorted_durations, 50),
            p75_ms=percentile(sorted_durations, 75),
            p90_ms=percentile(sorted_durations, 90),
            p95_ms=percentile(sorted_durations, 95),
            p99_ms=percentile(sorted_durations, 99),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_executions": self.total_executions,
            "min_ms": round(self.min_ms, 2),
            "max_ms": round(self.max_ms, 2),
            "mean_ms": round(self.mean_ms, 2),
            "median_ms": round(self.median_ms, 2),
            "std_dev_ms": round(self.std_dev_ms, 2),
            "p50_ms": round(self.p50_ms, 2),
            "p75_ms": round(self.p75_ms, 2),
            "p90_ms": round(self.p90_ms, 2),
            "p95_ms": round(self.p95_ms, 2),
            "p99_ms": round(self.p99_ms, 2),
        }


@dataclass
class WorkflowMetrics:
    """Comprehensive metrics for a single workflow."""

    workflow_id: str
    workflow_name: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    cancelled_executions: int = 0
    timeout_executions: int = 0
    duration_distribution: ExecutionDistribution = field(
        default_factory=ExecutionDistribution
    )
    error_breakdown: Dict[str, int] = field(default_factory=dict)
    last_execution: Optional[datetime] = None
    first_execution: Optional[datetime] = None
    hourly_trend: List[TimeSeriesDataPoint] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_executions == 0:
            return 0.0
        return (self.successful_executions / self.total_executions) * 100

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate percentage."""
        if self.total_executions == 0:
            return 0.0
        return (self.failed_executions / self.total_executions) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "cancelled_executions": self.cancelled_executions,
            "timeout_executions": self.timeout_executions,
            "success_rate": round(self.success_rate, 2),
            "failure_rate": round(self.failure_rate, 2),
            "duration_distribution": self.duration_distribution.to_dict(),
            "error_breakdown": self.error_breakdown,
            "last_execution": (
                self.last_execution.isoformat() if self.last_execution else None
            ),
            "first_execution": (
                self.first_execution.isoformat() if self.first_execution else None
            ),
            "hourly_trend": [dp.to_dict() for dp in self.hourly_trend[-24:]],
        }


@dataclass
class RobotPerformanceMetrics:
    """Performance metrics for a single robot."""

    robot_id: str
    robot_name: str
    total_jobs: int = 0
    successful_jobs: int = 0
    failed_jobs: int = 0
    total_busy_seconds: float = 0.0
    total_idle_seconds: float = 0.0
    total_offline_seconds: float = 0.0
    avg_job_duration_ms: float = 0.0
    jobs_per_hour: float = 0.0
    current_status: str = "offline"
    last_active: Optional[datetime] = None

    @property
    def utilization_percent(self) -> float:
        """Calculate utilization percentage."""
        total = self.total_busy_seconds + self.total_idle_seconds
        if total == 0:
            return 0.0
        return (self.total_busy_seconds / total) * 100

    @property
    def success_rate(self) -> float:
        """Calculate job success rate."""
        if self.total_jobs == 0:
            return 0.0
        return (self.successful_jobs / self.total_jobs) * 100

    @property
    def availability_percent(self) -> float:
        """Calculate availability percentage (online time)."""
        total = (
            self.total_busy_seconds
            + self.total_idle_seconds
            + self.total_offline_seconds
        )
        if total == 0:
            return 0.0
        online = self.total_busy_seconds + self.total_idle_seconds
        return (online / total) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "robot_id": self.robot_id,
            "robot_name": self.robot_name,
            "total_jobs": self.total_jobs,
            "successful_jobs": self.successful_jobs,
            "failed_jobs": self.failed_jobs,
            "success_rate": round(self.success_rate, 2),
            "utilization_percent": round(self.utilization_percent, 2),
            "availability_percent": round(self.availability_percent, 2),
            "total_busy_seconds": round(self.total_busy_seconds, 2),
            "total_idle_seconds": round(self.total_idle_seconds, 2),
            "avg_job_duration_ms": round(self.avg_job_duration_ms, 2),
            "jobs_per_hour": round(self.jobs_per_hour, 2),
            "current_status": self.current_status,
            "last_active": self.last_active.isoformat() if self.last_active else None,
        }


@dataclass
class BottleneckAnalysis:
    """Identifies performance bottlenecks in workflow execution."""

    workflow_id: str
    bottleneck_nodes: List[Dict[str, Any]] = field(default_factory=list)
    queue_wait_time_avg_ms: float = 0.0
    queue_depth_avg: float = 0.0
    robot_contention_rate: float = 0.0
    resource_bottlenecks: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "bottleneck_nodes": self.bottleneck_nodes,
            "queue_wait_time_avg_ms": round(self.queue_wait_time_avg_ms, 2),
            "queue_depth_avg": round(self.queue_depth_avg, 2),
            "robot_contention_rate": round(self.robot_contention_rate, 2),
            "resource_bottlenecks": self.resource_bottlenecks,
            "recommendations": self.recommendations,
        }


@dataclass
class EfficiencyScore:
    """Workflow efficiency scoring and analysis."""

    workflow_id: str
    workflow_name: str
    overall_score: float = 0.0  # 0-100
    reliability_score: float = 0.0  # Based on success rate
    performance_score: float = 0.0  # Based on execution time vs baseline
    resource_score: float = 0.0  # Based on resource utilization
    maintainability_score: float = 0.0  # Based on healing rate, error diversity
    trend: str = "stable"  # improving, stable, degrading
    factors: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "overall_score": round(self.overall_score, 2),
            "reliability_score": round(self.reliability_score, 2),
            "performance_score": round(self.performance_score, 2),
            "resource_score": round(self.resource_score, 2),
            "maintainability_score": round(self.maintainability_score, 2),
            "trend": self.trend,
            "factors": self.factors,
        }


@dataclass
class CostAnalysis:
    """Cost analysis for RPA operations."""

    period_start: datetime
    period_end: datetime
    total_robot_hours: float = 0.0
    robot_cost_per_hour: float = 0.0  # Configurable
    total_robot_cost: float = 0.0
    cloud_compute_hours: float = 0.0
    cloud_cost_per_hour: float = 0.0  # Configurable
    total_cloud_cost: float = 0.0
    total_cost: float = 0.0
    cost_per_execution: float = 0.0
    cost_per_successful_execution: float = 0.0
    workflow_cost_breakdown: Dict[str, float] = field(default_factory=dict)
    savings_vs_manual: float = 0.0  # Estimated savings

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "total_robot_hours": round(self.total_robot_hours, 2),
            "robot_cost_per_hour": round(self.robot_cost_per_hour, 2),
            "total_robot_cost": round(self.total_robot_cost, 2),
            "cloud_compute_hours": round(self.cloud_compute_hours, 2),
            "cloud_cost_per_hour": round(self.cloud_cost_per_hour, 2),
            "total_cloud_cost": round(self.total_cloud_cost, 2),
            "total_cost": round(self.total_cost, 2),
            "cost_per_execution": round(self.cost_per_execution, 2),
            "cost_per_successful_execution": round(
                self.cost_per_successful_execution, 2
            ),
            "workflow_cost_breakdown": {
                k: round(v, 2) for k, v in self.workflow_cost_breakdown.items()
            },
            "savings_vs_manual": round(self.savings_vs_manual, 2),
        }


@dataclass
class SLACompliance:
    """SLA compliance tracking and reporting."""

    workflow_id: str
    workflow_name: str
    sla_target_success_rate: float = 99.0
    sla_target_p95_ms: float = 60000.0
    sla_target_availability: float = 99.5
    actual_success_rate: float = 0.0
    actual_p95_ms: float = 0.0
    actual_availability: float = 0.0
    success_rate_compliant: bool = False
    latency_compliant: bool = False
    availability_compliant: bool = False
    overall_compliant: bool = False
    compliance_percentage: float = 0.0
    violations: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "sla_targets": {
                "success_rate": self.sla_target_success_rate,
                "p95_ms": self.sla_target_p95_ms,
                "availability": self.sla_target_availability,
            },
            "actual_metrics": {
                "success_rate": round(self.actual_success_rate, 2),
                "p95_ms": round(self.actual_p95_ms, 2),
                "availability": round(self.actual_availability, 2),
            },
            "compliance": {
                "success_rate": self.success_rate_compliant,
                "latency": self.latency_compliant,
                "availability": self.availability_compliant,
                "overall": self.overall_compliant,
                "percentage": round(self.compliance_percentage, 2),
            },
            "violations": self.violations[-50:],
        }


@dataclass
class ComparativeAnalysis:
    """A/B comparison between workflow versions."""

    workflow_id: str
    version_a: str
    version_b: str
    version_a_metrics: WorkflowMetrics = field(
        default_factory=lambda: WorkflowMetrics(workflow_id="", workflow_name="")
    )
    version_b_metrics: WorkflowMetrics = field(
        default_factory=lambda: WorkflowMetrics(workflow_id="", workflow_name="")
    )
    success_rate_diff: float = 0.0
    avg_duration_diff_ms: float = 0.0
    p95_duration_diff_ms: float = 0.0
    recommendation: str = ""
    confidence: float = 0.0  # Statistical confidence
    sample_size_sufficient: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "version_a": self.version_a,
            "version_b": self.version_b,
            "version_a_metrics": {
                "total_executions": self.version_a_metrics.total_executions,
                "success_rate": round(self.version_a_metrics.success_rate, 2),
                "avg_duration_ms": round(
                    self.version_a_metrics.duration_distribution.mean_ms, 2
                ),
                "p95_duration_ms": round(
                    self.version_a_metrics.duration_distribution.p95_ms, 2
                ),
            },
            "version_b_metrics": {
                "total_executions": self.version_b_metrics.total_executions,
                "success_rate": round(self.version_b_metrics.success_rate, 2),
                "avg_duration_ms": round(
                    self.version_b_metrics.duration_distribution.mean_ms, 2
                ),
                "p95_duration_ms": round(
                    self.version_b_metrics.duration_distribution.p95_ms, 2
                ),
            },
            "differences": {
                "success_rate_diff": round(self.success_rate_diff, 2),
                "avg_duration_diff_ms": round(self.avg_duration_diff_ms, 2),
                "p95_duration_diff_ms": round(self.p95_duration_diff_ms, 2),
            },
            "recommendation": self.recommendation,
            "confidence": round(self.confidence, 2),
            "sample_size_sufficient": self.sample_size_sufficient,
        }


@dataclass
class AnalyticsReport:
    """Comprehensive analytics report."""

    generated_at: datetime
    period_start: datetime
    period_end: datetime
    period: AggregationPeriod
    summary: Dict[str, Any] = field(default_factory=dict)
    execution_metrics: Dict[str, Any] = field(default_factory=dict)
    workflow_metrics: List[WorkflowMetrics] = field(default_factory=list)
    robot_metrics: List[RobotPerformanceMetrics] = field(default_factory=list)
    queue_metrics: Dict[str, Any] = field(default_factory=dict)
    error_analysis: Dict[str, Any] = field(default_factory=dict)
    healing_metrics: Dict[str, Any] = field(default_factory=dict)
    cost_analysis: Optional[CostAnalysis] = None
    sla_compliance: List[SLACompliance] = field(default_factory=list)
    bottlenecks: List[BottleneckAnalysis] = field(default_factory=list)
    efficiency_scores: List[EfficiencyScore] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "generated_at": self.generated_at.isoformat(),
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "period": self.period.value,
            "summary": self.summary,
            "execution_metrics": self.execution_metrics,
            "workflow_metrics": [w.to_dict() for w in self.workflow_metrics],
            "robot_metrics": [r.to_dict() for r in self.robot_metrics],
            "queue_metrics": self.queue_metrics,
            "error_analysis": self.error_analysis,
            "healing_metrics": self.healing_metrics,
            "cost_analysis": self.cost_analysis.to_dict()
            if self.cost_analysis
            else None,
            "sla_compliance": [s.to_dict() for s in self.sla_compliance],
            "bottlenecks": [b.to_dict() for b in self.bottlenecks],
            "efficiency_scores": [e.to_dict() for e in self.efficiency_scores],
        }


@dataclass
class JobRecord:
    """Internal record of job execution for analytics."""

    job_id: str
    workflow_id: str
    workflow_name: str
    workflow_version: str
    robot_id: str
    status: str
    duration_ms: float
    queue_wait_ms: float
    started_at: datetime
    completed_at: Optional[datetime]
    error_type: Optional[str]
    error_message: Optional[str]
    nodes_executed: int
    healing_attempts: int
    healing_successes: int


class MetricsAggregator:
    """
    Central metrics aggregation engine for analytics and reporting.

    Collects execution data, computes statistics, generates reports,
    and provides query APIs for the analytics dashboard.

    Thread-safe singleton pattern for global access.
    """

    _instance: Optional["MetricsAggregator"] = None
    _lock: Lock = Lock()

    def __new__(cls) -> "MetricsAggregator":
        """Thread-safe singleton."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    @classmethod
    def get_instance(cls) -> "MetricsAggregator":
        """Get singleton instance."""
        return cls()

    def __init__(self) -> None:
        """Initialize aggregator."""
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._lock = Lock()

        # Job records storage (in-memory, production should use DB)
        self._job_records: List[JobRecord] = []
        self._max_records: int = 100000

        # Workflow metrics cache
        self._workflow_cache: Dict[str, WorkflowMetrics] = {}
        self._workflow_durations: Dict[str, List[float]] = defaultdict(list)

        # Robot metrics
        self._robot_cache: Dict[str, RobotPerformanceMetrics] = {}

        # Time series data
        self._hourly_executions: Dict[str, List[TimeSeriesDataPoint]] = defaultdict(
            list
        )
        self._queue_depth_history: List[TimeSeriesDataPoint] = []

        # Error tracking
        self._error_counts: Dict[str, int] = defaultdict(int)
        self._error_by_workflow: Dict[str, Dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )

        # Healing metrics
        self._healing_by_tier: Dict[str, int] = defaultdict(int)
        self._healing_by_workflow: Dict[str, Dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )

        # Cost configuration
        self._robot_cost_per_hour: float = 5.0
        self._cloud_cost_per_hour: float = 0.10
        self._manual_cost_per_hour: float = 25.0

        # SLA configuration
        self._sla_configs: Dict[str, Dict[str, float]] = {}

        self._initialized = True
        logger.info("MetricsAggregator initialized")

    def configure_costs(
        self,
        robot_cost_per_hour: float = 5.0,
        cloud_cost_per_hour: float = 0.10,
        manual_cost_per_hour: float = 25.0,
    ) -> None:
        """
        Configure cost parameters for analysis.

        Args:
            robot_cost_per_hour: Cost per robot-hour.
            cloud_cost_per_hour: Cloud compute cost per hour.
            manual_cost_per_hour: Estimated manual labor cost per hour.
        """
        self._robot_cost_per_hour = robot_cost_per_hour
        self._cloud_cost_per_hour = cloud_cost_per_hour
        self._manual_cost_per_hour = manual_cost_per_hour

    def configure_sla(
        self,
        workflow_id: str,
        target_success_rate: float = 99.0,
        target_p95_ms: float = 60000.0,
        target_availability: float = 99.5,
    ) -> None:
        """
        Configure SLA targets for a workflow.

        Args:
            workflow_id: Workflow identifier.
            target_success_rate: Target success rate percentage.
            target_p95_ms: Target P95 latency in milliseconds.
            target_availability: Target availability percentage.
        """
        self._sla_configs[workflow_id] = {
            "success_rate": target_success_rate,
            "p95_ms": target_p95_ms,
            "availability": target_availability,
        }

    def record_job_execution(
        self,
        job_id: str,
        workflow_id: str,
        workflow_name: str,
        workflow_version: str,
        robot_id: str,
        status: str,
        duration_ms: float,
        queue_wait_ms: float,
        started_at: datetime,
        completed_at: Optional[datetime] = None,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None,
        nodes_executed: int = 0,
        healing_attempts: int = 0,
        healing_successes: int = 0,
    ) -> None:
        """
        Record a job execution for analytics.

        Args:
            job_id: Unique job identifier.
            workflow_id: Workflow identifier.
            workflow_name: Workflow display name.
            workflow_version: Workflow version.
            robot_id: Executing robot identifier.
            status: Job status (completed, failed, cancelled, timeout).
            duration_ms: Execution duration in milliseconds.
            queue_wait_ms: Time spent waiting in queue.
            started_at: Execution start time.
            completed_at: Execution end time.
            error_type: Error type if failed.
            error_message: Error message if failed.
            nodes_executed: Number of nodes executed.
            healing_attempts: Number of healing attempts.
            healing_successes: Number of successful healings.
        """
        record = JobRecord(
            job_id=job_id,
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            workflow_version=workflow_version,
            robot_id=robot_id,
            status=status,
            duration_ms=duration_ms,
            queue_wait_ms=queue_wait_ms,
            started_at=started_at,
            completed_at=completed_at or datetime.now(timezone.utc),
            error_type=error_type,
            error_message=error_message,
            nodes_executed=nodes_executed,
            healing_attempts=healing_attempts,
            healing_successes=healing_successes,
        )

        with self._lock:
            self._job_records.append(record)
            if len(self._job_records) > self._max_records:
                self._job_records = self._job_records[-self._max_records :]

            self._update_workflow_cache(record)
            self._update_robot_cache(record)
            self._update_error_tracking(record)
            self._update_healing_tracking(record)
            self._update_time_series(record)

        logger.debug(
            f"Recorded job execution: {job_id} workflow={workflow_id} "
            f"status={status} duration={duration_ms}ms"
        )

    def _update_workflow_cache(self, record: JobRecord) -> None:
        """Update workflow metrics cache."""
        wf_id = record.workflow_id

        if wf_id not in self._workflow_cache:
            self._workflow_cache[wf_id] = WorkflowMetrics(
                workflow_id=wf_id,
                workflow_name=record.workflow_name,
            )

        wf = self._workflow_cache[wf_id]
        wf.total_executions += 1

        if record.status == "completed":
            wf.successful_executions += 1
        elif record.status == "failed":
            wf.failed_executions += 1
        elif record.status == "cancelled":
            wf.cancelled_executions += 1
        elif record.status == "timeout":
            wf.timeout_executions += 1

        self._workflow_durations[wf_id].append(record.duration_ms)
        if len(self._workflow_durations[wf_id]) > 10000:
            self._workflow_durations[wf_id] = self._workflow_durations[wf_id][-10000:]

        wf.duration_distribution = ExecutionDistribution.from_durations(
            self._workflow_durations[wf_id]
        )

        wf.last_execution = record.completed_at
        if wf.first_execution is None:
            wf.first_execution = record.started_at

    def _update_robot_cache(self, record: JobRecord) -> None:
        """Update robot metrics cache."""
        robot_id = record.robot_id
        if not robot_id:
            return

        if robot_id not in self._robot_cache:
            self._robot_cache[robot_id] = RobotPerformanceMetrics(
                robot_id=robot_id,
                robot_name=robot_id,
            )

        robot = self._robot_cache[robot_id]
        robot.total_jobs += 1

        if record.status == "completed":
            robot.successful_jobs += 1
        elif record.status == "failed":
            robot.failed_jobs += 1

        robot.total_busy_seconds += record.duration_ms / 1000
        robot.last_active = record.completed_at

        # Calculate running average
        robot.avg_job_duration_ms = (
            robot.avg_job_duration_ms * (robot.total_jobs - 1) + record.duration_ms
        ) / robot.total_jobs

    def _update_error_tracking(self, record: JobRecord) -> None:
        """Update error tracking."""
        if record.status == "failed" and record.error_type:
            self._error_counts[record.error_type] += 1
            self._error_by_workflow[record.workflow_id][record.error_type] += 1

    def _update_healing_tracking(self, record: JobRecord) -> None:
        """Update healing metrics."""
        if record.healing_attempts > 0:
            self._healing_by_workflow[record.workflow_id]["attempts"] += (
                record.healing_attempts
            )
            self._healing_by_workflow[record.workflow_id]["successes"] += (
                record.healing_successes
            )

    def _update_time_series(self, record: JobRecord) -> None:
        """Update time series data."""
        hour = record.started_at.replace(minute=0, second=0, microsecond=0)

        hourly = self._hourly_executions[record.workflow_id]
        if hourly and hourly[-1].timestamp == hour:
            hourly[-1].count += 1
            hourly[-1].value = (
                hourly[-1].value * (hourly[-1].count - 1) + record.duration_ms
            ) / hourly[-1].count
        else:
            hourly.append(
                TimeSeriesDataPoint(
                    timestamp=hour,
                    value=record.duration_ms,
                    count=1,
                )
            )

        if len(hourly) > 168:  # Keep 7 days of hourly data
            self._hourly_executions[record.workflow_id] = hourly[-168:]

    def record_queue_depth(self, depth: int) -> None:
        """Record current queue depth for trending."""
        now = datetime.now(timezone.utc)
        with self._lock:
            self._queue_depth_history.append(
                TimeSeriesDataPoint(
                    timestamp=now,
                    value=float(depth),
                )
            )
            if len(self._queue_depth_history) > 1440:  # 24 hours at 1-min intervals
                self._queue_depth_history = self._queue_depth_history[-1440:]

    def record_healing_result(
        self,
        workflow_id: str,
        tier: str,
        success: bool,
    ) -> None:
        """Record a healing attempt result."""
        with self._lock:
            self._healing_by_tier[tier] += 1
            if success:
                self._healing_by_tier[f"{tier}_success"] += 1

    def get_execution_summary(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get execution summary for a time period.

        Args:
            start_time: Period start (default: 24 hours ago).
            end_time: Period end (default: now).

        Returns:
            Summary dictionary with execution metrics.
        """
        end_time = end_time or datetime.now(timezone.utc)
        start_time = start_time or (end_time - timedelta(hours=24))

        with self._lock:
            records = [
                r for r in self._job_records if start_time <= r.started_at <= end_time
            ]

        if not records:
            return {
                "total_executions": 0,
                "successful": 0,
                "failed": 0,
                "cancelled": 0,
                "timeout": 0,
                "success_rate": 0.0,
                "avg_duration_ms": 0.0,
                "avg_queue_wait_ms": 0.0,
                "throughput_per_hour": 0.0,
            }

        total = len(records)
        successful = sum(1 for r in records if r.status == "completed")
        failed = sum(1 for r in records if r.status == "failed")
        cancelled = sum(1 for r in records if r.status == "cancelled")
        timeout = sum(1 for r in records if r.status == "timeout")

        durations = [r.duration_ms for r in records]
        queue_waits = [r.queue_wait_ms for r in records]

        hours = (end_time - start_time).total_seconds() / 3600
        throughput = total / hours if hours > 0 else 0

        return {
            "total_executions": total,
            "successful": successful,
            "failed": failed,
            "cancelled": cancelled,
            "timeout": timeout,
            "success_rate": round((successful / total) * 100, 2) if total > 0 else 0.0,
            "avg_duration_ms": round(statistics.mean(durations), 2)
            if durations
            else 0.0,
            "avg_queue_wait_ms": round(statistics.mean(queue_waits), 2)
            if queue_waits
            else 0.0,
            "throughput_per_hour": round(throughput, 2),
        }

    def get_workflow_metrics(
        self,
        workflow_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[WorkflowMetrics]:
        """
        Get metrics for workflows.

        Args:
            workflow_id: Specific workflow (optional, all if None).
            start_time: Period start filter.
            end_time: Period end filter.

        Returns:
            List of WorkflowMetrics.
        """
        with self._lock:
            if workflow_id:
                wf = self._workflow_cache.get(workflow_id)
                return [wf] if wf else []

            return list(self._workflow_cache.values())

    def get_robot_metrics(
        self,
        robot_id: Optional[str] = None,
    ) -> List[RobotPerformanceMetrics]:
        """
        Get metrics for robots.

        Args:
            robot_id: Specific robot (optional, all if None).

        Returns:
            List of RobotPerformanceMetrics.
        """
        with self._lock:
            if robot_id:
                robot = self._robot_cache.get(robot_id)
                return [robot] if robot else []

            return list(self._robot_cache.values())

    def get_duration_statistics(
        self,
        workflow_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> ExecutionDistribution:
        """
        Get execution duration statistics for a workflow.

        Args:
            workflow_id: Workflow identifier.
            start_time: Period start filter.
            end_time: Period end filter.

        Returns:
            ExecutionDistribution with percentiles.
        """
        with self._lock:
            durations = self._workflow_durations.get(workflow_id, [])

        if not durations:
            return ExecutionDistribution()

        if start_time or end_time:
            end_time = end_time or datetime.now(timezone.utc)
            start_time = start_time or (end_time - timedelta(days=30))

            with self._lock:
                records = [
                    r
                    for r in self._job_records
                    if r.workflow_id == workflow_id
                    and start_time <= r.started_at <= end_time
                ]
                durations = [r.duration_ms for r in records]

        return ExecutionDistribution.from_durations(durations)

    def get_error_analysis(
        self,
        workflow_id: Optional[str] = None,
        top_n: int = 10,
    ) -> Dict[str, Any]:
        """
        Get error analysis and breakdown.

        Args:
            workflow_id: Filter by workflow (optional).
            top_n: Number of top errors to include.

        Returns:
            Error analysis dictionary.
        """
        with self._lock:
            if workflow_id:
                errors = dict(self._error_by_workflow.get(workflow_id, {}))
            else:
                errors = dict(self._error_counts)

        sorted_errors = sorted(errors.items(), key=lambda x: x[1], reverse=True)[:top_n]
        total = sum(errors.values())

        return {
            "total_errors": total,
            "unique_error_types": len(errors),
            "top_errors": [
                {
                    "error_type": err_type,
                    "count": count,
                    "percentage": round((count / total) * 100, 2) if total > 0 else 0,
                }
                for err_type, count in sorted_errors
            ],
        }

    def get_healing_metrics(
        self,
        workflow_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get self-healing metrics and success rates.

        Args:
            workflow_id: Filter by workflow (optional).

        Returns:
            Healing metrics dictionary.
        """
        with self._lock:
            if workflow_id:
                data = dict(self._healing_by_workflow.get(workflow_id, {}))
            else:
                data = {
                    "attempts": sum(
                        v.get("attempts", 0) for v in self._healing_by_workflow.values()
                    ),
                    "successes": sum(
                        v.get("successes", 0)
                        for v in self._healing_by_workflow.values()
                    ),
                }

            tier_data = dict(self._healing_by_tier)

        attempts = data.get("attempts", 0)
        successes = data.get("successes", 0)

        tiers = ["heuristic", "anchor", "cv"]
        tier_breakdown = {}
        for tier in tiers:
            tier_attempts = tier_data.get(tier, 0)
            tier_successes = tier_data.get(f"{tier}_success", 0)
            tier_breakdown[tier] = {
                "attempts": tier_attempts,
                "successes": tier_successes,
                "success_rate": round((tier_successes / tier_attempts) * 100, 2)
                if tier_attempts > 0
                else 0.0,
            }

        return {
            "total_attempts": attempts,
            "total_successes": successes,
            "overall_success_rate": round((successes / attempts) * 100, 2)
            if attempts > 0
            else 0.0,
            "tier_breakdown": tier_breakdown,
        }

    def get_queue_metrics(
        self,
        hours: int = 24,
    ) -> Dict[str, Any]:
        """
        Get queue depth and throughput metrics.

        Args:
            hours: Number of hours to analyze.

        Returns:
            Queue metrics dictionary.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        with self._lock:
            history = [dp for dp in self._queue_depth_history if dp.timestamp >= cutoff]

        if not history:
            return {
                "current_depth": 0,
                "avg_depth": 0.0,
                "max_depth": 0,
                "time_series": [],
            }

        depths = [dp.value for dp in history]

        return {
            "current_depth": int(history[-1].value) if history else 0,
            "avg_depth": round(statistics.mean(depths), 2),
            "max_depth": int(max(depths)),
            "min_depth": int(min(depths)),
            "time_series": [dp.to_dict() for dp in history[-100:]],
        }

    def get_time_series(
        self,
        workflow_id: str,
        metric: str = "executions",
        period: AggregationPeriod = AggregationPeriod.HOUR,
        limit: int = 24,
    ) -> List[TimeSeriesDataPoint]:
        """
        Get time series data for a workflow.

        Args:
            workflow_id: Workflow identifier.
            metric: Metric type (executions, duration, success_rate).
            period: Aggregation period.
            limit: Number of data points.

        Returns:
            List of TimeSeriesDataPoint.
        """
        with self._lock:
            hourly = self._hourly_executions.get(workflow_id, [])

        return hourly[-limit:]

    def calculate_efficiency_score(
        self,
        workflow_id: str,
    ) -> EfficiencyScore:
        """
        Calculate efficiency score for a workflow.

        Args:
            workflow_id: Workflow identifier.

        Returns:
            EfficiencyScore with breakdown.
        """
        with self._lock:
            wf = self._workflow_cache.get(workflow_id)
            healing = dict(self._healing_by_workflow.get(workflow_id, {}))

        if not wf:
            return EfficiencyScore(workflow_id=workflow_id, workflow_name="Unknown")

        # Reliability: based on success rate
        reliability = min(wf.success_rate, 100.0)

        # Performance: based on P95 vs baseline (60s = 100%, 300s = 0%)
        p95 = wf.duration_distribution.p95_ms
        baseline_excellent = 60000  # 1 min
        baseline_poor = 300000  # 5 min
        if p95 <= baseline_excellent:
            performance = 100.0
        elif p95 >= baseline_poor:
            performance = 0.0
        else:
            performance = 100 * (
                1 - (p95 - baseline_excellent) / (baseline_poor - baseline_excellent)
            )

        # Resource: inverse of healing rate
        attempts = healing.get("attempts", 0)
        successes = healing.get("successes", 0)
        if attempts == 0:
            resource = 100.0
        else:
            healing_rate = (
                (attempts / wf.total_executions) if wf.total_executions > 0 else 0
            )
            resource = max(0, 100 - (healing_rate * 100))

        # Maintainability: low error diversity is good
        error_types = len(self._error_by_workflow.get(workflow_id, {}))
        if error_types == 0:
            maintainability = 100.0
        elif error_types <= 2:
            maintainability = 80.0
        elif error_types <= 5:
            maintainability = 50.0
        else:
            maintainability = 20.0

        overall = (
            reliability * 0.4
            + performance * 0.3
            + resource * 0.15
            + maintainability * 0.15
        )

        return EfficiencyScore(
            workflow_id=workflow_id,
            workflow_name=wf.workflow_name,
            overall_score=overall,
            reliability_score=reliability,
            performance_score=performance,
            resource_score=resource,
            maintainability_score=maintainability,
            trend="stable",
            factors={
                "success_rate": wf.success_rate,
                "p95_ms": p95,
                "healing_rate": (attempts / wf.total_executions * 100)
                if wf.total_executions > 0
                else 0,
                "error_diversity": error_types,
            },
        )

    def calculate_cost_analysis(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> CostAnalysis:
        """
        Calculate cost analysis for a time period.

        Args:
            start_time: Period start.
            end_time: Period end.

        Returns:
            CostAnalysis with cost breakdown.
        """
        with self._lock:
            records = [
                r for r in self._job_records if start_time <= r.started_at <= end_time
            ]

        if not records:
            return CostAnalysis(
                period_start=start_time,
                period_end=end_time,
            )

        total_duration_ms = sum(r.duration_ms for r in records)
        total_robot_hours = total_duration_ms / 1000 / 3600

        total_robot_cost = total_robot_hours * self._robot_cost_per_hour
        total_cloud_cost = total_robot_hours * self._cloud_cost_per_hour
        total_cost = total_robot_cost + total_cloud_cost

        total_executions = len(records)
        successful = sum(1 for r in records if r.status == "completed")

        cost_per_execution = (
            total_cost / total_executions if total_executions > 0 else 0
        )
        cost_per_successful = total_cost / successful if successful > 0 else 0

        # Estimate savings vs manual
        estimated_manual_hours = total_robot_hours * 3  # Assume automation is 3x faster
        savings = (estimated_manual_hours * self._manual_cost_per_hour) - total_cost

        # Workflow breakdown
        workflow_costs: Dict[str, float] = defaultdict(float)
        for r in records:
            wf_hours = r.duration_ms / 1000 / 3600
            workflow_costs[r.workflow_id] += wf_hours * (
                self._robot_cost_per_hour + self._cloud_cost_per_hour
            )

        return CostAnalysis(
            period_start=start_time,
            period_end=end_time,
            total_robot_hours=total_robot_hours,
            robot_cost_per_hour=self._robot_cost_per_hour,
            total_robot_cost=total_robot_cost,
            cloud_compute_hours=total_robot_hours,
            cloud_cost_per_hour=self._cloud_cost_per_hour,
            total_cloud_cost=total_cloud_cost,
            total_cost=total_cost,
            cost_per_execution=cost_per_execution,
            cost_per_successful_execution=cost_per_successful,
            workflow_cost_breakdown=dict(workflow_costs),
            savings_vs_manual=savings,
        )

    def check_sla_compliance(
        self,
        workflow_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> SLACompliance:
        """
        Check SLA compliance for a workflow.

        Args:
            workflow_id: Workflow identifier.
            start_time: Period start.
            end_time: Period end.

        Returns:
            SLACompliance with status and violations.
        """
        sla_config = self._sla_configs.get(
            workflow_id,
            {
                "success_rate": 99.0,
                "p95_ms": 60000.0,
                "availability": 99.5,
            },
        )

        with self._lock:
            wf = self._workflow_cache.get(workflow_id)

        if not wf:
            return SLACompliance(
                workflow_id=workflow_id,
                workflow_name="Unknown",
            )

        dist = self.get_duration_statistics(workflow_id, start_time, end_time)

        success_rate_compliant = wf.success_rate >= sla_config["success_rate"]
        latency_compliant = dist.p95_ms <= sla_config["p95_ms"]
        availability_compliant = True  # Would need uptime data

        compliant_count = sum(
            [success_rate_compliant, latency_compliant, availability_compliant]
        )
        compliance_percentage = (compliant_count / 3) * 100

        violations = []
        if not success_rate_compliant:
            violations.append(
                {
                    "type": "success_rate",
                    "target": sla_config["success_rate"],
                    "actual": wf.success_rate,
                    "gap": sla_config["success_rate"] - wf.success_rate,
                }
            )
        if not latency_compliant:
            violations.append(
                {
                    "type": "p95_latency",
                    "target": sla_config["p95_ms"],
                    "actual": dist.p95_ms,
                    "gap": dist.p95_ms - sla_config["p95_ms"],
                }
            )

        return SLACompliance(
            workflow_id=workflow_id,
            workflow_name=wf.workflow_name,
            sla_target_success_rate=sla_config["success_rate"],
            sla_target_p95_ms=sla_config["p95_ms"],
            sla_target_availability=sla_config["availability"],
            actual_success_rate=wf.success_rate,
            actual_p95_ms=dist.p95_ms,
            actual_availability=100.0,
            success_rate_compliant=success_rate_compliant,
            latency_compliant=latency_compliant,
            availability_compliant=availability_compliant,
            overall_compliant=all(
                [success_rate_compliant, latency_compliant, availability_compliant]
            ),
            compliance_percentage=compliance_percentage,
            violations=violations,
        )

    def analyze_bottlenecks(
        self,
        workflow_id: str,
    ) -> BottleneckAnalysis:
        """
        Analyze performance bottlenecks for a workflow.

        Args:
            workflow_id: Workflow identifier.

        Returns:
            BottleneckAnalysis with recommendations.
        """
        with self._lock:
            records = [r for r in self._job_records if r.workflow_id == workflow_id]
            wf = self._workflow_cache.get(workflow_id)

        if not records:
            return BottleneckAnalysis(workflow_id=workflow_id)

        queue_waits = [r.queue_wait_ms for r in records]
        avg_queue_wait = statistics.mean(queue_waits) if queue_waits else 0

        recommendations = []

        if avg_queue_wait > 30000:
            recommendations.append(
                "High queue wait time detected. Consider adding more robots or "
                "optimizing workflow scheduling."
            )

        if wf and wf.failure_rate > 10:
            recommendations.append(
                f"High failure rate ({wf.failure_rate:.1f}%). Review error logs "
                "and consider implementing retry logic."
            )

        healing = self._healing_by_workflow.get(workflow_id, {})
        if healing.get("attempts", 0) > 0:
            healing_rate = (healing.get("attempts", 0) / len(records)) * 100
            if healing_rate > 20:
                recommendations.append(
                    f"High healing rate ({healing_rate:.1f}%). Update selectors "
                    "to reduce dependency on self-healing."
                )

        return BottleneckAnalysis(
            workflow_id=workflow_id,
            queue_wait_time_avg_ms=avg_queue_wait,
            recommendations=recommendations,
        )

    def compare_versions(
        self,
        workflow_id: str,
        version_a: str,
        version_b: str,
    ) -> ComparativeAnalysis:
        """
        Compare two versions of a workflow.

        Args:
            workflow_id: Workflow identifier.
            version_a: First version to compare.
            version_b: Second version to compare.

        Returns:
            ComparativeAnalysis with differences and recommendation.
        """
        with self._lock:
            records_a = [
                r
                for r in self._job_records
                if r.workflow_id == workflow_id and r.workflow_version == version_a
            ]
            records_b = [
                r
                for r in self._job_records
                if r.workflow_id == workflow_id and r.workflow_version == version_b
            ]

        def build_metrics(records: List[JobRecord], version: str) -> WorkflowMetrics:
            wf = WorkflowMetrics(workflow_id=workflow_id, workflow_name=version)
            wf.total_executions = len(records)
            wf.successful_executions = sum(
                1 for r in records if r.status == "completed"
            )
            wf.failed_executions = sum(1 for r in records if r.status == "failed")
            durations = [r.duration_ms for r in records]
            wf.duration_distribution = ExecutionDistribution.from_durations(durations)
            return wf

        metrics_a = build_metrics(records_a, version_a)
        metrics_b = build_metrics(records_b, version_b)

        success_diff = metrics_b.success_rate - metrics_a.success_rate
        avg_diff = (
            metrics_b.duration_distribution.mean_ms
            - metrics_a.duration_distribution.mean_ms
        )
        p95_diff = (
            metrics_b.duration_distribution.p95_ms
            - metrics_a.duration_distribution.p95_ms
        )

        min_sample = 30
        sample_sufficient = (
            metrics_a.total_executions >= min_sample
            and metrics_b.total_executions >= min_sample
        )

        if not sample_sufficient:
            recommendation = "Insufficient data for reliable comparison."
            confidence = 0.0
        elif success_diff > 5 and avg_diff < 0:
            recommendation = f"Version {version_b} is significantly better."
            confidence = 0.9
        elif (
            success_diff < -5
            or avg_diff > metrics_a.duration_distribution.mean_ms * 0.2
        ):
            recommendation = f"Version {version_a} performs better. Consider reverting."
            confidence = 0.85
        else:
            recommendation = "No significant difference between versions."
            confidence = 0.7

        return ComparativeAnalysis(
            workflow_id=workflow_id,
            version_a=version_a,
            version_b=version_b,
            version_a_metrics=metrics_a,
            version_b_metrics=metrics_b,
            success_rate_diff=success_diff,
            avg_duration_diff_ms=avg_diff,
            p95_duration_diff_ms=p95_diff,
            recommendation=recommendation,
            confidence=confidence,
            sample_size_sufficient=sample_sufficient,
        )

    def generate_report(
        self,
        period: AggregationPeriod = AggregationPeriod.DAY,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> AnalyticsReport:
        """
        Generate comprehensive analytics report.

        Args:
            period: Aggregation period.
            start_time: Report start time.
            end_time: Report end time.

        Returns:
            AnalyticsReport with all metrics.
        """
        end_time = end_time or datetime.now(timezone.utc)

        period_deltas = {
            AggregationPeriod.HOUR: timedelta(hours=1),
            AggregationPeriod.DAY: timedelta(days=1),
            AggregationPeriod.WEEK: timedelta(weeks=1),
            AggregationPeriod.MONTH: timedelta(days=30),
            AggregationPeriod.QUARTER: timedelta(days=90),
            AggregationPeriod.YEAR: timedelta(days=365),
        }
        start_time = start_time or (end_time - period_deltas[period])

        summary = self.get_execution_summary(start_time, end_time)
        workflows = self.get_workflow_metrics()
        robots = self.get_robot_metrics()
        queue = self.get_queue_metrics()
        errors = self.get_error_analysis()
        healing = self.get_healing_metrics()
        cost = self.calculate_cost_analysis(start_time, end_time)

        sla_list = []
        efficiency_list = []
        bottleneck_list = []

        for wf in workflows:
            sla_list.append(
                self.check_sla_compliance(wf.workflow_id, start_time, end_time)
            )
            efficiency_list.append(self.calculate_efficiency_score(wf.workflow_id))
            bottleneck_list.append(self.analyze_bottlenecks(wf.workflow_id))

        return AnalyticsReport(
            generated_at=datetime.now(timezone.utc),
            period_start=start_time,
            period_end=end_time,
            period=period,
            summary=summary,
            execution_metrics={
                "total": summary["total_executions"],
                "by_status": {
                    "successful": summary["successful"],
                    "failed": summary["failed"],
                    "cancelled": summary["cancelled"],
                    "timeout": summary["timeout"],
                },
            },
            workflow_metrics=workflows,
            robot_metrics=robots,
            queue_metrics=queue,
            error_analysis=errors,
            healing_metrics=healing,
            cost_analysis=cost,
            sla_compliance=sla_list,
            bottlenecks=bottleneck_list,
            efficiency_scores=efficiency_list,
        )

    def export_csv(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> str:
        """
        Export job execution data as CSV.

        Args:
            start_time: Period start.
            end_time: Period end.

        Returns:
            CSV string.
        """
        end_time = end_time or datetime.now(timezone.utc)
        start_time = start_time or (end_time - timedelta(days=7))

        with self._lock:
            records = [
                r for r in self._job_records if start_time <= r.started_at <= end_time
            ]

        lines = [
            "job_id,workflow_id,workflow_name,workflow_version,robot_id,status,"
            "duration_ms,queue_wait_ms,started_at,completed_at,error_type,"
            "nodes_executed,healing_attempts,healing_successes"
        ]

        for r in records:
            lines.append(
                f"{r.job_id},{r.workflow_id},{r.workflow_name},{r.workflow_version},"
                f"{r.robot_id},{r.status},{r.duration_ms},{r.queue_wait_ms},"
                f"{r.started_at.isoformat()},{r.completed_at.isoformat() if r.completed_at else ''},"
                f"{r.error_type or ''},{r.nodes_executed},{r.healing_attempts},{r.healing_successes}"
            )

        return "\n".join(lines)

    def reset(self) -> None:
        """Reset all collected data."""
        with self._lock:
            self._job_records.clear()
            self._workflow_cache.clear()
            self._workflow_durations.clear()
            self._robot_cache.clear()
            self._hourly_executions.clear()
            self._queue_depth_history.clear()
            self._error_counts.clear()
            self._error_by_workflow.clear()
            self._healing_by_tier.clear()
            self._healing_by_workflow.clear()

        logger.info("MetricsAggregator reset")


def get_metrics_aggregator() -> MetricsAggregator:
    """Get singleton metrics aggregator instance."""
    return MetricsAggregator.get_instance()
