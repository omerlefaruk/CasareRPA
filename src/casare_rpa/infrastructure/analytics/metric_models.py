"""
CasareRPA Infrastructure: Metric Data Models

Data classes for analytics results and reports.
Provides backward-compatible public API classes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from casare_rpa.infrastructure.analytics.aggregation_strategies import (
    AggregationPeriod,
    StatisticalAggregationStrategy,
    TimeSeriesDataPoint,
)
from casare_rpa.infrastructure.analytics.metric_calculators import (
    BottleneckAnalysisResult,
    CostAnalysisResult,
    EfficiencyScoreResult,
    SLAComplianceResult,
    VersionComparisonResult,
)
from casare_rpa.infrastructure.analytics.metric_storage import (
    RobotMetricsData,
    WorkflowMetricsData,
)


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
        """Create from a list of durations using StatisticalAggregationStrategy."""
        if not durations:
            return cls()

        strategy = StatisticalAggregationStrategy()
        result = strategy.aggregate(durations)

        return cls(
            total_executions=result.count,
            min_ms=result.min_value,
            max_ms=result.max_value,
            mean_ms=result.mean,
            median_ms=result.median,
            std_dev_ms=result.std_dev,
            p50_ms=result.p50,
            p75_ms=result.p75,
            p90_ms=result.p90,
            p95_ms=result.p95,
            p99_ms=result.p99,
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

    @classmethod
    def from_cache(
        cls,
        data: WorkflowMetricsData,
        durations: List[float],
        hourly: List[TimeSeriesDataPoint],
    ) -> "WorkflowMetrics":
        """Create from cached data."""
        return cls(
            workflow_id=data.workflow_id,
            workflow_name=data.workflow_name,
            total_executions=data.total_executions,
            successful_executions=data.successful_executions,
            failed_executions=data.failed_executions,
            cancelled_executions=data.cancelled_executions,
            timeout_executions=data.timeout_executions,
            duration_distribution=ExecutionDistribution.from_durations(durations),
            error_breakdown=data.error_breakdown,
            last_execution=data.last_execution,
            first_execution=data.first_execution,
            hourly_trend=hourly,
        )

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
        """Calculate availability percentage."""
        total = (
            self.total_busy_seconds
            + self.total_idle_seconds
            + self.total_offline_seconds
        )
        if total == 0:
            return 0.0
        online = self.total_busy_seconds + self.total_idle_seconds
        return (online / total) * 100

    @classmethod
    def from_cache(cls, data: RobotMetricsData) -> "RobotPerformanceMetrics":
        """Create from cached data."""
        return cls(
            robot_id=data.robot_id,
            robot_name=data.robot_name,
            total_jobs=data.total_jobs,
            successful_jobs=data.successful_jobs,
            failed_jobs=data.failed_jobs,
            total_busy_seconds=data.total_busy_seconds,
            total_idle_seconds=data.total_idle_seconds,
            total_offline_seconds=data.total_offline_seconds,
            avg_job_duration_ms=data.avg_job_duration_ms,
            jobs_per_hour=data.jobs_per_hour,
            current_status=data.current_status,
            last_active=data.last_active,
        )

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


# Backward compatibility aliases
BottleneckAnalysis = BottleneckAnalysisResult
EfficiencyScore = EfficiencyScoreResult
CostAnalysis = CostAnalysisResult
SLACompliance = SLAComplianceResult
ComparativeAnalysis = VersionComparisonResult


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


__all__ = [
    "ExecutionDistribution",
    "WorkflowMetrics",
    "RobotPerformanceMetrics",
    "AnalyticsReport",
    # Backward compatibility aliases
    "BottleneckAnalysis",
    "EfficiencyScore",
    "CostAnalysis",
    "SLACompliance",
    "ComparativeAnalysis",
]
