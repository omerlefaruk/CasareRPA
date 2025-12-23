"""
CasareRPA Infrastructure: Metric Calculators

Calculation helpers for various analytics metrics:
- Efficiency score calculation
- Cost analysis calculation
- SLA compliance checking
- Bottleneck analysis
- Version comparison
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol


class MetricsDataSource(Protocol):
    """Protocol for metrics data sources."""

    def get_workflow_data(self, workflow_id: str) -> dict[str, Any]:
        """Get workflow metrics data."""
        ...

    def get_job_records(
        self,
        workflow_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Get job execution records."""
        ...

    def get_healing_data(self, workflow_id: str | None = None) -> dict[str, Any]:
        """Get healing metrics data."""
        ...

    def get_error_data(self, workflow_id: str | None = None) -> dict[str, int]:
        """Get error count data."""
        ...


@dataclass
class EfficiencyScoreResult:
    """Result of efficiency score calculation."""

    workflow_id: str
    workflow_name: str
    overall_score: float = 0.0
    reliability_score: float = 0.0
    performance_score: float = 0.0
    resource_score: float = 0.0
    maintainability_score: float = 0.0
    trend: str = "stable"
    factors: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
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


class EfficiencyScoreCalculator:
    """
    Calculates workflow efficiency scores.

    Considers reliability, performance, resource usage, and maintainability.
    """

    # Weight configuration
    RELIABILITY_WEIGHT = 0.4
    PERFORMANCE_WEIGHT = 0.3
    RESOURCE_WEIGHT = 0.15
    MAINTAINABILITY_WEIGHT = 0.15

    # Performance baselines (in ms)
    BASELINE_EXCELLENT = 60000  # 1 minute
    BASELINE_POOR = 300000  # 5 minutes

    def __init__(
        self,
        reliability_weight: float = 0.4,
        performance_weight: float = 0.3,
        resource_weight: float = 0.15,
        maintainability_weight: float = 0.15,
    ):
        """
        Initialize calculator with custom weights.

        Args:
            reliability_weight: Weight for reliability score.
            performance_weight: Weight for performance score.
            resource_weight: Weight for resource score.
            maintainability_weight: Weight for maintainability score.
        """
        self.reliability_weight = reliability_weight
        self.performance_weight = performance_weight
        self.resource_weight = resource_weight
        self.maintainability_weight = maintainability_weight

    def calculate(
        self,
        workflow_id: str,
        workflow_name: str,
        success_rate: float,
        p95_duration_ms: float,
        total_executions: int,
        healing_attempts: int,
        error_type_count: int,
    ) -> EfficiencyScoreResult:
        """
        Calculate efficiency score for a workflow.

        Args:
            workflow_id: Workflow identifier.
            workflow_name: Workflow display name.
            success_rate: Success rate percentage (0-100).
            p95_duration_ms: 95th percentile duration in ms.
            total_executions: Total number of executions.
            healing_attempts: Number of healing attempts.
            error_type_count: Number of distinct error types.

        Returns:
            EfficiencyScoreResult with breakdown.
        """
        # Reliability: based on success rate (0-100)
        reliability = min(success_rate, 100.0)

        # Performance: based on P95 vs baseline
        performance = self._calculate_performance_score(p95_duration_ms)

        # Resource: inverse of healing rate
        resource = self._calculate_resource_score(healing_attempts, total_executions)

        # Maintainability: low error diversity is good
        maintainability = self._calculate_maintainability_score(error_type_count)

        # Calculate weighted overall score
        overall = (
            reliability * self.reliability_weight
            + performance * self.performance_weight
            + resource * self.resource_weight
            + maintainability * self.maintainability_weight
        )

        # Calculate healing rate for factors
        healing_rate = (healing_attempts / total_executions * 100) if total_executions > 0 else 0

        return EfficiencyScoreResult(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            overall_score=overall,
            reliability_score=reliability,
            performance_score=performance,
            resource_score=resource,
            maintainability_score=maintainability,
            trend="stable",
            factors={
                "success_rate": success_rate,
                "p95_ms": p95_duration_ms,
                "healing_rate": healing_rate,
                "error_diversity": error_type_count,
            },
        )

    def _calculate_performance_score(self, p95_ms: float) -> float:
        """Calculate performance score from P95 duration."""
        if p95_ms <= self.BASELINE_EXCELLENT:
            return 100.0
        elif p95_ms >= self.BASELINE_POOR:
            return 0.0
        else:
            return 100 * (
                1
                - (p95_ms - self.BASELINE_EXCELLENT)
                / (self.BASELINE_POOR - self.BASELINE_EXCELLENT)
            )

    def _calculate_resource_score(
        self,
        healing_attempts: int,
        total_executions: int,
    ) -> float:
        """Calculate resource score from healing rate."""
        if healing_attempts == 0:
            return 100.0

        healing_rate = (healing_attempts / total_executions) if total_executions > 0 else 0
        return max(0, 100 - (healing_rate * 100))

    def _calculate_maintainability_score(self, error_type_count: int) -> float:
        """Calculate maintainability score from error diversity."""
        if error_type_count == 0:
            return 100.0
        elif error_type_count <= 2:
            return 80.0
        elif error_type_count <= 5:
            return 50.0
        else:
            return 20.0


@dataclass
class CostAnalysisResult:
    """Result of cost analysis calculation."""

    period_start: datetime
    period_end: datetime
    total_robot_hours: float = 0.0
    robot_cost_per_hour: float = 0.0
    total_robot_cost: float = 0.0
    cloud_compute_hours: float = 0.0
    cloud_cost_per_hour: float = 0.0
    total_cloud_cost: float = 0.0
    total_cost: float = 0.0
    cost_per_execution: float = 0.0
    cost_per_successful_execution: float = 0.0
    workflow_cost_breakdown: dict[str, float] = field(default_factory=dict)
    savings_vs_manual: float = 0.0

    def to_dict(self) -> dict[str, Any]:
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
            "cost_per_successful_execution": round(self.cost_per_successful_execution, 2),
            "workflow_cost_breakdown": {
                k: round(v, 2) for k, v in self.workflow_cost_breakdown.items()
            },
            "savings_vs_manual": round(self.savings_vs_manual, 2),
        }


class CostAnalysisCalculator:
    """
    Calculates cost analysis for RPA operations.

    Tracks robot hours, cloud costs, and estimates savings.
    """

    # Automation efficiency multiplier (how much faster than manual)
    AUTOMATION_SPEED_MULTIPLIER = 3.0

    def __init__(
        self,
        robot_cost_per_hour: float = 5.0,
        cloud_cost_per_hour: float = 0.10,
        manual_cost_per_hour: float = 25.0,
    ):
        """
        Initialize cost calculator.

        Args:
            robot_cost_per_hour: Cost per robot-hour.
            cloud_cost_per_hour: Cloud compute cost per hour.
            manual_cost_per_hour: Estimated manual labor cost per hour.
        """
        self.robot_cost_per_hour = robot_cost_per_hour
        self.cloud_cost_per_hour = cloud_cost_per_hour
        self.manual_cost_per_hour = manual_cost_per_hour

    def calculate(
        self,
        records: list[dict[str, Any]],
        period_start: datetime,
        period_end: datetime,
    ) -> CostAnalysisResult:
        """
        Calculate cost analysis from job records.

        Args:
            records: List of job execution records.
            period_start: Analysis period start.
            period_end: Analysis period end.

        Returns:
            CostAnalysisResult with cost breakdown.
        """
        if not records:
            return CostAnalysisResult(
                period_start=period_start,
                period_end=period_end,
            )

        # Calculate total duration
        total_duration_ms = sum(r.get("duration_ms", 0) for r in records)
        total_robot_hours = total_duration_ms / 1000 / 3600

        # Calculate costs
        total_robot_cost = total_robot_hours * self.robot_cost_per_hour
        total_cloud_cost = total_robot_hours * self.cloud_cost_per_hour
        total_cost = total_robot_cost + total_cloud_cost

        # Count executions
        total_executions = len(records)
        successful = sum(1 for r in records if r.get("status") == "completed")

        # Per-execution costs
        cost_per_execution = total_cost / total_executions if total_executions > 0 else 0
        cost_per_successful = total_cost / successful if successful > 0 else 0

        # Estimate savings vs manual
        estimated_manual_hours = total_robot_hours * self.AUTOMATION_SPEED_MULTIPLIER
        savings = (estimated_manual_hours * self.manual_cost_per_hour) - total_cost

        # Workflow breakdown
        workflow_costs: dict[str, float] = {}
        for r in records:
            wf_id = r.get("workflow_id", "unknown")
            wf_hours = r.get("duration_ms", 0) / 1000 / 3600
            wf_cost = wf_hours * (self.robot_cost_per_hour + self.cloud_cost_per_hour)
            workflow_costs[wf_id] = workflow_costs.get(wf_id, 0) + wf_cost

        return CostAnalysisResult(
            period_start=period_start,
            period_end=period_end,
            total_robot_hours=total_robot_hours,
            robot_cost_per_hour=self.robot_cost_per_hour,
            total_robot_cost=total_robot_cost,
            cloud_compute_hours=total_robot_hours,
            cloud_cost_per_hour=self.cloud_cost_per_hour,
            total_cloud_cost=total_cloud_cost,
            total_cost=total_cost,
            cost_per_execution=cost_per_execution,
            cost_per_successful_execution=cost_per_successful,
            workflow_cost_breakdown=workflow_costs,
            savings_vs_manual=savings,
        )


@dataclass
class SLAComplianceResult:
    """Result of SLA compliance check."""

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
    violations: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
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


class SLAComplianceCalculator:
    """
    Checks SLA compliance for workflows.

    Monitors success rate, latency, and availability targets.
    """

    def __init__(
        self,
        default_success_rate: float = 99.0,
        default_p95_ms: float = 60000.0,
        default_availability: float = 99.5,
    ):
        """
        Initialize SLA calculator with defaults.

        Args:
            default_success_rate: Default success rate target.
            default_p95_ms: Default P95 latency target.
            default_availability: Default availability target.
        """
        self.default_success_rate = default_success_rate
        self.default_p95_ms = default_p95_ms
        self.default_availability = default_availability

    def check(
        self,
        workflow_id: str,
        workflow_name: str,
        actual_success_rate: float,
        actual_p95_ms: float,
        actual_availability: float = 100.0,
        target_success_rate: float | None = None,
        target_p95_ms: float | None = None,
        target_availability: float | None = None,
    ) -> SLAComplianceResult:
        """
        Check SLA compliance for a workflow.

        Args:
            workflow_id: Workflow identifier.
            workflow_name: Workflow display name.
            actual_success_rate: Actual success rate.
            actual_p95_ms: Actual P95 latency.
            actual_availability: Actual availability.
            target_success_rate: Target success rate (or default).
            target_p95_ms: Target P95 latency (or default).
            target_availability: Target availability (or default).

        Returns:
            SLAComplianceResult with status.
        """
        # Use defaults if not specified
        target_success = target_success_rate or self.default_success_rate
        target_p95 = target_p95_ms or self.default_p95_ms
        target_avail = target_availability or self.default_availability

        # Check compliance
        success_rate_compliant = actual_success_rate >= target_success
        latency_compliant = actual_p95_ms <= target_p95
        availability_compliant = actual_availability >= target_avail

        # Calculate overall compliance
        compliant_count = sum(
            [
                success_rate_compliant,
                latency_compliant,
                availability_compliant,
            ]
        )
        compliance_percentage = (compliant_count / 3) * 100

        # Build violations list
        violations = []
        if not success_rate_compliant:
            violations.append(
                {
                    "type": "success_rate",
                    "target": target_success,
                    "actual": actual_success_rate,
                    "gap": target_success - actual_success_rate,
                }
            )
        if not latency_compliant:
            violations.append(
                {
                    "type": "p95_latency",
                    "target": target_p95,
                    "actual": actual_p95_ms,
                    "gap": actual_p95_ms - target_p95,
                }
            )
        if not availability_compliant:
            violations.append(
                {
                    "type": "availability",
                    "target": target_avail,
                    "actual": actual_availability,
                    "gap": target_avail - actual_availability,
                }
            )

        return SLAComplianceResult(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            sla_target_success_rate=target_success,
            sla_target_p95_ms=target_p95,
            sla_target_availability=target_avail,
            actual_success_rate=actual_success_rate,
            actual_p95_ms=actual_p95_ms,
            actual_availability=actual_availability,
            success_rate_compliant=success_rate_compliant,
            latency_compliant=latency_compliant,
            availability_compliant=availability_compliant,
            overall_compliant=all(
                [
                    success_rate_compliant,
                    latency_compliant,
                    availability_compliant,
                ]
            ),
            compliance_percentage=compliance_percentage,
            violations=violations,
        )


@dataclass
class BottleneckAnalysisResult:
    """Result of bottleneck analysis."""

    workflow_id: str
    bottleneck_nodes: list[dict[str, Any]] = field(default_factory=list)
    queue_wait_time_avg_ms: float = 0.0
    queue_depth_avg: float = 0.0
    robot_contention_rate: float = 0.0
    resource_bottlenecks: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
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


class BottleneckAnalysisCalculator:
    """
    Analyzes performance bottlenecks in workflow execution.

    Identifies queue issues, resource contention, and provides recommendations.
    """

    # Thresholds
    HIGH_QUEUE_WAIT_MS = 30000  # 30 seconds
    HIGH_FAILURE_RATE = 10.0  # 10%
    HIGH_HEALING_RATE = 20.0  # 20%

    def analyze(
        self,
        workflow_id: str,
        records: list[dict[str, Any]],
        failure_rate: float = 0.0,
        healing_attempts: int = 0,
    ) -> BottleneckAnalysisResult:
        """
        Analyze bottlenecks for a workflow.

        Args:
            workflow_id: Workflow identifier.
            records: Job execution records.
            failure_rate: Current failure rate.
            healing_attempts: Total healing attempts.

        Returns:
            BottleneckAnalysisResult with recommendations.
        """
        if not records:
            return BottleneckAnalysisResult(workflow_id=workflow_id)

        # Calculate queue wait statistics
        queue_waits = [r.get("queue_wait_ms", 0) for r in records]
        avg_queue_wait = statistics.mean(queue_waits) if queue_waits else 0

        # Generate recommendations
        recommendations = []

        if avg_queue_wait > self.HIGH_QUEUE_WAIT_MS:
            recommendations.append(
                "High queue wait time detected. Consider adding more robots or "
                "optimizing workflow scheduling."
            )

        if failure_rate > self.HIGH_FAILURE_RATE:
            recommendations.append(
                f"High failure rate ({failure_rate:.1f}%). Review error logs "
                "and consider implementing retry logic."
            )

        if healing_attempts > 0 and len(records) > 0:
            healing_rate = (healing_attempts / len(records)) * 100
            if healing_rate > self.HIGH_HEALING_RATE:
                recommendations.append(
                    f"High healing rate ({healing_rate:.1f}%). Update selectors "
                    "to reduce dependency on self-healing."
                )

        return BottleneckAnalysisResult(
            workflow_id=workflow_id,
            queue_wait_time_avg_ms=avg_queue_wait,
            recommendations=recommendations,
        )


@dataclass
class VersionComparisonResult:
    """Result of version comparison."""

    workflow_id: str
    version_a: str
    version_b: str
    version_a_executions: int = 0
    version_a_success_rate: float = 0.0
    version_a_avg_duration_ms: float = 0.0
    version_a_p95_duration_ms: float = 0.0
    version_b_executions: int = 0
    version_b_success_rate: float = 0.0
    version_b_avg_duration_ms: float = 0.0
    version_b_p95_duration_ms: float = 0.0
    success_rate_diff: float = 0.0
    avg_duration_diff_ms: float = 0.0
    p95_duration_diff_ms: float = 0.0
    recommendation: str = ""
    confidence: float = 0.0
    sample_size_sufficient: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "version_a": self.version_a,
            "version_b": self.version_b,
            "version_a_metrics": {
                "total_executions": self.version_a_executions,
                "success_rate": round(self.version_a_success_rate, 2),
                "avg_duration_ms": round(self.version_a_avg_duration_ms, 2),
                "p95_duration_ms": round(self.version_a_p95_duration_ms, 2),
            },
            "version_b_metrics": {
                "total_executions": self.version_b_executions,
                "success_rate": round(self.version_b_success_rate, 2),
                "avg_duration_ms": round(self.version_b_avg_duration_ms, 2),
                "p95_duration_ms": round(self.version_b_p95_duration_ms, 2),
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


class VersionComparisonCalculator:
    """
    Compares two versions of a workflow.

    Provides A/B comparison with statistical analysis.
    """

    MIN_SAMPLE_SIZE = 30  # Minimum samples for reliable comparison
    SIGNIFICANT_SUCCESS_DIFF = 5.0  # 5% difference is significant
    SIGNIFICANT_DURATION_DIFF = 0.2  # 20% difference is significant

    @staticmethod
    def _calculate_percentile(values: list[float], percentile: float) -> float:
        """Calculate percentile from sorted values."""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        n = len(sorted_values)
        k = (n - 1) * (percentile / 100.0)
        f = int(k)
        c = f + 1 if f + 1 < n else f
        d = k - f

        return (
            sorted_values[f] + d * (sorted_values[c] - sorted_values[f])
            if c != f
            else sorted_values[f]
        )

    def compare(
        self,
        workflow_id: str,
        version_a: str,
        version_b: str,
        records_a: list[dict[str, Any]],
        records_b: list[dict[str, Any]],
    ) -> VersionComparisonResult:
        """
        Compare two workflow versions.

        Args:
            workflow_id: Workflow identifier.
            version_a: First version identifier.
            version_b: Second version identifier.
            records_a: Execution records for version A.
            records_b: Execution records for version B.

        Returns:
            VersionComparisonResult with analysis.
        """
        # Calculate metrics for version A
        a_executions = len(records_a)
        a_successful = sum(1 for r in records_a if r.get("status") == "completed")
        a_success_rate = (a_successful / a_executions * 100) if a_executions > 0 else 0
        a_durations = [r.get("duration_ms", 0) for r in records_a]
        a_avg = statistics.mean(a_durations) if a_durations else 0
        a_p95 = self._calculate_percentile(a_durations, 95)

        # Calculate metrics for version B
        b_executions = len(records_b)
        b_successful = sum(1 for r in records_b if r.get("status") == "completed")
        b_success_rate = (b_successful / b_executions * 100) if b_executions > 0 else 0
        b_durations = [r.get("duration_ms", 0) for r in records_b]
        b_avg = statistics.mean(b_durations) if b_durations else 0
        b_p95 = self._calculate_percentile(b_durations, 95)

        # Calculate differences (B - A, positive means B is higher)
        success_diff = b_success_rate - a_success_rate
        avg_diff = b_avg - a_avg
        p95_diff = b_p95 - a_p95

        # Check sample size
        sample_sufficient = (
            a_executions >= self.MIN_SAMPLE_SIZE and b_executions >= self.MIN_SAMPLE_SIZE
        )

        # Generate recommendation
        if not sample_sufficient:
            recommendation = "Insufficient data for reliable comparison."
            confidence = 0.0
        elif success_diff > self.SIGNIFICANT_SUCCESS_DIFF and avg_diff < 0:
            recommendation = f"Version {version_b} is significantly better."
            confidence = 0.9
        elif success_diff < -self.SIGNIFICANT_SUCCESS_DIFF or (
            a_avg > 0 and avg_diff > a_avg * self.SIGNIFICANT_DURATION_DIFF
        ):
            recommendation = f"Version {version_a} performs better. Consider reverting."
            confidence = 0.85
        else:
            recommendation = "No significant difference between versions."
            confidence = 0.7

        return VersionComparisonResult(
            workflow_id=workflow_id,
            version_a=version_a,
            version_b=version_b,
            version_a_executions=a_executions,
            version_a_success_rate=a_success_rate,
            version_a_avg_duration_ms=a_avg,
            version_a_p95_duration_ms=a_p95,
            version_b_executions=b_executions,
            version_b_success_rate=b_success_rate,
            version_b_avg_duration_ms=b_avg,
            version_b_p95_duration_ms=b_p95,
            success_rate_diff=success_diff,
            avg_duration_diff_ms=avg_diff,
            p95_duration_diff_ms=p95_diff,
            recommendation=recommendation,
            confidence=confidence,
            sample_size_sufficient=sample_sufficient,
        )


__all__ = [
    # Result classes
    "EfficiencyScoreResult",
    "CostAnalysisResult",
    "SLAComplianceResult",
    "BottleneckAnalysisResult",
    "VersionComparisonResult",
    # Calculator classes
    "EfficiencyScoreCalculator",
    "CostAnalysisCalculator",
    "SLAComplianceCalculator",
    "BottleneckAnalysisCalculator",
    "VersionComparisonCalculator",
    # Protocols
    "MetricsDataSource",
]
