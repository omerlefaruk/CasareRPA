"""
CasareRPA Infrastructure: Metrics Aggregation Engine

Facade for comprehensive analytics and reporting:
- Real-time execution metrics
- Historical trend analysis
- Percentile-based duration statistics (p50, p95, p99)
- Resource utilization tracking
- Cost analysis (robot-hours, cloud costs)
- Bottleneck identification
- Workflow efficiency scoring
- Comparative analysis (version A vs B)

This module serves as a facade, delegating to:
- aggregation_strategies.py: Strategy pattern for aggregations
- metric_calculators.py: Business logic calculators
- metric_storage.py: Storage adapters
- metric_models.py: Data models for public API
"""

from __future__ import annotations

import statistics
from datetime import UTC, datetime, timedelta, timezone
from threading import Lock
from typing import Any, Dict, List, Optional

from loguru import logger

from casare_rpa.infrastructure.analytics.aggregation_strategies import (
    AggregationPeriod,
    TimeSeriesDataPoint,
)
from casare_rpa.infrastructure.analytics.metric_calculators import (
    BottleneckAnalysisCalculator,
    CostAnalysisCalculator,
    EfficiencyScoreCalculator,
    EfficiencyScoreResult,
    SLAComplianceCalculator,
    SLAComplianceResult,
    VersionComparisonCalculator,
)
from casare_rpa.infrastructure.analytics.metric_models import (
    AnalyticsReport,
    BottleneckAnalysis,
    ComparativeAnalysis,
    CostAnalysis,
    EfficiencyScore,
    ExecutionDistribution,
    RobotPerformanceMetrics,
    SLACompliance,
    WorkflowMetrics,
)
from casare_rpa.infrastructure.analytics.metric_storage import (
    JobRecord,
    MetricsStorageManager,
)


class MetricsAggregator:
    """
    Central metrics aggregation facade.

    Provides a unified API for analytics while delegating to specialized
    strategies, calculators, and storage adapters.

    Thread-safe singleton pattern for global access.
    """

    _instance: MetricsAggregator | None = None
    _lock: Lock = Lock()

    def __new__(cls) -> MetricsAggregator:
        """Thread-safe singleton."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    @classmethod
    def get_instance(cls) -> MetricsAggregator:
        """Get singleton instance."""
        return cls()

    def __init__(self) -> None:
        """Initialize aggregator."""
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._lock = Lock()
        self._storage = MetricsStorageManager()
        self._efficiency_calc = EfficiencyScoreCalculator()
        self._cost_calc = CostAnalysisCalculator()
        self._sla_calc = SLAComplianceCalculator()
        self._bottleneck_calc = BottleneckAnalysisCalculator()
        self._version_calc = VersionComparisonCalculator()
        self._sla_configs: dict[str, dict[str, float]] = {}

        self._initialized = True
        logger.info("MetricsAggregator initialized")

    def configure_costs(
        self,
        robot_cost_per_hour: float = 5.0,
        cloud_cost_per_hour: float = 0.10,
        manual_cost_per_hour: float = 25.0,
    ) -> None:
        """Configure cost parameters for analysis."""
        self._cost_calc = CostAnalysisCalculator(
            robot_cost_per_hour=robot_cost_per_hour,
            cloud_cost_per_hour=cloud_cost_per_hour,
            manual_cost_per_hour=manual_cost_per_hour,
        )

    def configure_sla(
        self,
        workflow_id: str,
        target_success_rate: float = 99.0,
        target_p95_ms: float = 60000.0,
        target_availability: float = 99.5,
    ) -> None:
        """Configure SLA targets for a workflow."""
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
        completed_at: datetime | None = None,
        error_type: str | None = None,
        error_message: str | None = None,
        nodes_executed: int = 0,
        healing_attempts: int = 0,
        healing_successes: int = 0,
    ) -> None:
        """Record a job execution for analytics."""
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
            completed_at=completed_at or datetime.now(UTC),
            error_type=error_type,
            error_message=error_message,
            nodes_executed=nodes_executed,
            healing_attempts=healing_attempts,
            healing_successes=healing_successes,
        )

        with self._lock:
            self._storage.record_job(record)

        logger.debug(
            f"Recorded job execution: {job_id} workflow={workflow_id} "
            f"status={status} duration={duration_ms}ms"
        )

    def record_queue_depth(self, depth: int) -> None:
        """Record current queue depth for trending."""
        self._storage.queue_depth.record(depth)

    def record_healing_result(self, workflow_id: str, tier: str, success: bool) -> None:
        """Record a healing attempt result."""
        with self._lock:
            self._storage.healing_metrics.record_healing(workflow_id, tier, success)

    def get_execution_summary(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> dict[str, Any]:
        """Get execution summary for a time period."""
        end_time = end_time or datetime.now(UTC)
        start_time = start_time or (end_time - timedelta(hours=24))

        records = self._storage.job_records.get_by_time_range(start_time, end_time)

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
            "avg_duration_ms": round(statistics.mean(durations), 2) if durations else 0.0,
            "avg_queue_wait_ms": round(statistics.mean(queue_waits), 2) if queue_waits else 0.0,
            "throughput_per_hour": round(throughput, 2),
        }

    def get_workflow_metrics(
        self,
        workflow_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[WorkflowMetrics]:
        """Get metrics for workflows."""
        if workflow_id:
            data = self._storage.workflow_metrics.get(workflow_id)
            if not data:
                return []
            durations = self._storage.workflow_metrics.get_durations(workflow_id)
            hourly = self._storage.workflow_metrics.get_hourly_data(workflow_id)
            return [WorkflowMetrics.from_cache(data, durations, hourly)]

        result = []
        for data in self._storage.workflow_metrics.get_all():
            durations = self._storage.workflow_metrics.get_durations(data.workflow_id)
            hourly = self._storage.workflow_metrics.get_hourly_data(data.workflow_id)
            result.append(WorkflowMetrics.from_cache(data, durations, hourly))
        return result

    def get_robot_metrics(self, robot_id: str | None = None) -> list[RobotPerformanceMetrics]:
        """Get metrics for robots."""
        if robot_id:
            data = self._storage.robot_metrics.get(robot_id)
            return [RobotPerformanceMetrics.from_cache(data)] if data else []

        return [
            RobotPerformanceMetrics.from_cache(data)
            for data in self._storage.robot_metrics.get_all()
        ]

    def get_duration_statistics(
        self,
        workflow_id: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> ExecutionDistribution:
        """Get execution duration statistics for a workflow."""
        if start_time or end_time:
            records = self._storage.job_records.get_by_workflow(workflow_id, start_time, end_time)
            durations = [r.duration_ms for r in records]
        else:
            durations = self._storage.workflow_metrics.get_durations(workflow_id)
        return ExecutionDistribution.from_durations(durations)

    def get_error_analysis(self, workflow_id: str | None = None, top_n: int = 10) -> dict[str, Any]:
        """Get error analysis and breakdown."""
        top_errors = self._storage.error_tracking.get_top_errors(top_n, workflow_id)
        counts = (
            self._storage.error_tracking.get_workflow_counts(workflow_id)
            if workflow_id
            else self._storage.error_tracking.get_global_counts()
        )
        return {
            "total_errors": sum(counts.values()),
            "unique_error_types": len(counts),
            "top_errors": top_errors,
        }

    def get_healing_metrics(self, workflow_id: str | None = None) -> dict[str, Any]:
        """Get self-healing metrics and success rates."""
        data = self._storage.healing_metrics.get_by_workflow(workflow_id)
        tier_data = self._storage.healing_metrics.get_by_tier()
        return {**data, "tier_breakdown": tier_data}

    def get_queue_metrics(self, hours: int = 24) -> dict[str, Any]:
        """Get queue depth and throughput metrics."""
        stats = self._storage.queue_depth.get_statistics(hours)
        history = self._storage.queue_depth.get_history(hours, limit=100)
        return {**stats, "time_series": [dp.to_dict() for dp in history]}

    def get_time_series(
        self,
        workflow_id: str,
        metric: str = "executions",
        period: AggregationPeriod = AggregationPeriod.HOUR,
        limit: int = 24,
    ) -> list[TimeSeriesDataPoint]:
        """Get time series data for a workflow."""
        return self._storage.workflow_metrics.get_hourly_data(workflow_id, limit)

    def calculate_efficiency_score(self, workflow_id: str) -> EfficiencyScore:
        """Calculate efficiency score for a workflow."""
        data = self._storage.workflow_metrics.get(workflow_id)
        if not data:
            return EfficiencyScoreResult(workflow_id=workflow_id, workflow_name="Unknown")

        durations = self._storage.workflow_metrics.get_durations(workflow_id)
        dist = ExecutionDistribution.from_durations(durations)
        healing = self._storage.healing_metrics.get_by_workflow(workflow_id)
        error_count = len(self._storage.error_tracking.get_workflow_counts(workflow_id))

        return self._efficiency_calc.calculate(
            workflow_id=workflow_id,
            workflow_name=data.workflow_name,
            success_rate=data.success_rate,
            p95_duration_ms=dist.p95_ms,
            total_executions=data.total_executions,
            healing_attempts=healing.get("total_attempts", 0),
            error_type_count=error_count,
        )

    def calculate_cost_analysis(self, start_time: datetime, end_time: datetime) -> CostAnalysis:
        """Calculate cost analysis for a time period."""
        records = self._storage.job_records.get_by_time_range(start_time, end_time)
        return self._cost_calc.calculate([r.to_dict() for r in records], start_time, end_time)

    def check_sla_compliance(
        self,
        workflow_id: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> SLACompliance:
        """Check SLA compliance for a workflow."""
        data = self._storage.workflow_metrics.get(workflow_id)
        if not data:
            return SLAComplianceResult(workflow_id=workflow_id, workflow_name="Unknown")

        dist = self.get_duration_statistics(workflow_id, start_time, end_time)
        sla_config = self._sla_configs.get(workflow_id, {})

        return self._sla_calc.check(
            workflow_id=workflow_id,
            workflow_name=data.workflow_name,
            actual_success_rate=data.success_rate,
            actual_p95_ms=dist.p95_ms,
            actual_availability=100.0,
            target_success_rate=sla_config.get("success_rate"),
            target_p95_ms=sla_config.get("p95_ms"),
            target_availability=sla_config.get("availability"),
        )

    def analyze_bottlenecks(self, workflow_id: str) -> BottleneckAnalysis:
        """Analyze performance bottlenecks for a workflow."""
        records = self._storage.job_records.get_by_workflow(workflow_id)
        data = self._storage.workflow_metrics.get(workflow_id)
        healing = self._storage.healing_metrics.get_by_workflow(workflow_id)

        return self._bottleneck_calc.analyze(
            workflow_id=workflow_id,
            records=[r.to_dict() for r in records],
            failure_rate=data.failure_rate if data else 0.0,
            healing_attempts=healing.get("total_attempts", 0),
        )

    def compare_versions(
        self, workflow_id: str, version_a: str, version_b: str
    ) -> ComparativeAnalysis:
        """Compare two versions of a workflow."""
        records_a = self._storage.job_records.get_by_version(workflow_id, version_a)
        records_b = self._storage.job_records.get_by_version(workflow_id, version_b)

        return self._version_calc.compare(
            workflow_id=workflow_id,
            version_a=version_a,
            version_b=version_b,
            records_a=[r.to_dict() for r in records_a],
            records_b=[r.to_dict() for r in records_b],
        )

    def generate_report(
        self,
        period: AggregationPeriod = AggregationPeriod.DAY,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> AnalyticsReport:
        """Generate comprehensive analytics report."""
        end_time = end_time or datetime.now(UTC)
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

        return AnalyticsReport(
            generated_at=datetime.now(UTC),
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
            queue_metrics=self.get_queue_metrics(),
            error_analysis=self.get_error_analysis(),
            healing_metrics=self.get_healing_metrics(),
            cost_analysis=self.calculate_cost_analysis(start_time, end_time),
            sla_compliance=[
                self.check_sla_compliance(wf.workflow_id, start_time, end_time) for wf in workflows
            ],
            bottlenecks=[self.analyze_bottlenecks(wf.workflow_id) for wf in workflows],
            efficiency_scores=[self.calculate_efficiency_score(wf.workflow_id) for wf in workflows],
        )

    def export_csv(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> str:
        """Export job execution data as CSV."""
        end_time = end_time or datetime.now(UTC)
        start_time = start_time or (end_time - timedelta(days=7))
        records = self._storage.job_records.get_by_time_range(start_time, end_time)

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
            self._storage.reset()
        logger.info("MetricsAggregator reset")

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance (for testing)."""
        with cls._lock:
            if cls._instance is not None:
                cls._instance.reset()
                cls._instance = None


def get_metrics_aggregator() -> MetricsAggregator:
    """Get singleton metrics aggregator instance."""
    return MetricsAggregator.get_instance()
