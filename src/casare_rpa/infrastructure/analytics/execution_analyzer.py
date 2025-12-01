"""
CasareRPA - Execution Analyzer

Analyzes workflow execution patterns, trends, and provides insights
for workflow optimization.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from collections import defaultdict

from loguru import logger


class TrendDirection(Enum):
    """Direction of a trend."""

    IMPROVING = "improving"
    STABLE = "stable"
    DEGRADING = "degrading"


class InsightType(Enum):
    """Types of insights generated."""

    PERFORMANCE_IMPROVEMENT = "performance_improvement"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    RELIABILITY_ISSUE = "reliability_issue"
    SUCCESS_STREAK = "success_streak"
    FAILURE_PATTERN = "failure_pattern"
    SCHEDULE_OPTIMIZATION = "schedule_optimization"
    RESOURCE_USAGE = "resource_usage"


@dataclass
class ExecutionInsight:
    """An insight generated from execution analysis."""

    insight_type: InsightType
    title: str
    description: str
    significance: float  # 0.0-1.0
    data: Dict[str, Any] = field(default_factory=dict)
    recommended_action: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.insight_type.value,
            "title": self.title,
            "description": self.description,
            "significance": round(self.significance, 3),
            "data": self.data,
            "recommended_action": self.recommended_action,
        }


@dataclass
class DurationTrend:
    """Trend analysis for execution duration."""

    direction: TrendDirection
    current_avg_ms: float
    previous_avg_ms: float
    change_percent: float
    confidence: float  # 0.0-1.0 based on sample size

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "direction": self.direction.value,
            "current_avg_ms": round(self.current_avg_ms, 2),
            "previous_avg_ms": round(self.previous_avg_ms, 2),
            "change_percent": round(self.change_percent, 2),
            "confidence": round(self.confidence, 3),
        }


@dataclass
class SuccessRateTrend:
    """Trend analysis for success rate."""

    direction: TrendDirection
    current_rate: float
    previous_rate: float
    change_percent: float
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "direction": self.direction.value,
            "current_rate": round(self.current_rate, 3),
            "previous_rate": round(self.previous_rate, 3),
            "change_percent": round(self.change_percent, 2),
            "confidence": round(self.confidence, 3),
        }


@dataclass
class TimeDistribution:
    """Distribution of executions over time."""

    hourly: Dict[int, int] = field(default_factory=dict)  # hour -> count
    daily: Dict[str, int] = field(default_factory=dict)  # day name -> count
    peak_hour: int = 0
    peak_day: str = ""
    off_peak_hours: List[int] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "hourly": self.hourly,
            "daily": self.daily,
            "peak_hour": self.peak_hour,
            "peak_day": self.peak_day,
            "off_peak_hours": self.off_peak_hours,
        }


@dataclass
class ExecutionAnalysisResult:
    """Complete execution analysis results."""

    workflow_id: str
    analysis_period_hours: int
    total_executions: int
    successful_executions: int
    failed_executions: int
    duration_trend: DurationTrend
    success_rate_trend: SuccessRateTrend
    time_distribution: TimeDistribution
    insights: List[ExecutionInsight] = field(default_factory=list)
    error_breakdown: Dict[str, int] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        """Calculate overall success rate."""
        if self.total_executions == 0:
            return 1.0
        return self.successful_executions / self.total_executions

    @property
    def failure_rate(self) -> float:
        """Calculate overall failure rate."""
        return 1.0 - self.success_rate

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "analysis_period_hours": self.analysis_period_hours,
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "success_rate": round(self.success_rate, 3),
            "duration_trend": self.duration_trend.to_dict(),
            "success_rate_trend": self.success_rate_trend.to_dict(),
            "time_distribution": self.time_distribution.to_dict(),
            "insights": [i.to_dict() for i in self.insights],
            "error_breakdown": self.error_breakdown,
            "insight_count": len(self.insights),
        }


class ExecutionAnalyzer:
    """
    Analyzes workflow execution patterns and generates insights.

    Provides:
    - Duration trend analysis
    - Success rate trend analysis
    - Time-of-day patterns
    - Actionable insights
    """

    # Thresholds for trend detection
    SIGNIFICANT_CHANGE_PERCENT = 10.0  # 10% change is significant
    MIN_SAMPLES_FOR_CONFIDENCE = 10
    HIGH_CONFIDENCE_SAMPLES = 50

    # Thresholds for insights
    SUCCESS_STREAK_THRESHOLD = 20  # 20 consecutive successes
    FAILURE_STREAK_THRESHOLD = 3  # 3 consecutive failures is concerning
    PERFORMANCE_CHANGE_THRESHOLD = 25.0  # 25% change triggers insight

    def __init__(self):
        """Initialize execution analyzer."""
        logger.debug("ExecutionAnalyzer initialized")

    def analyze(
        self,
        workflow_id: str,
        executions: List[Dict[str, Any]],
        analysis_period_hours: int = 168,  # 1 week default
    ) -> ExecutionAnalysisResult:
        """
        Analyze workflow executions.

        Args:
            workflow_id: Workflow to analyze
            executions: List of execution records
            analysis_period_hours: Time period to analyze

        Returns:
            Complete execution analysis
        """
        if not executions:
            return self._empty_result(workflow_id, analysis_period_hours)

        # Sort by timestamp
        sorted_executions = sorted(
            executions, key=lambda e: e.get("timestamp", datetime.min)
        )

        # Split into current and previous period for trend analysis
        midpoint = len(sorted_executions) // 2
        current_period = sorted_executions[midpoint:]
        previous_period = sorted_executions[:midpoint]

        # Calculate trends
        duration_trend = self._calculate_duration_trend(current_period, previous_period)
        success_rate_trend = self._calculate_success_rate_trend(
            current_period, previous_period
        )

        # Calculate time distribution
        time_distribution = self._calculate_time_distribution(sorted_executions)

        # Calculate error breakdown
        error_breakdown = self._calculate_error_breakdown(sorted_executions)

        # Count successes and failures
        successful = sum(1 for e in sorted_executions if e.get("status") == "success")
        failed = len(sorted_executions) - successful

        # Generate insights
        insights = self._generate_insights(
            sorted_executions,
            duration_trend,
            success_rate_trend,
            time_distribution,
        )

        return ExecutionAnalysisResult(
            workflow_id=workflow_id,
            analysis_period_hours=analysis_period_hours,
            total_executions=len(sorted_executions),
            successful_executions=successful,
            failed_executions=failed,
            duration_trend=duration_trend,
            success_rate_trend=success_rate_trend,
            time_distribution=time_distribution,
            insights=insights,
            error_breakdown=error_breakdown,
        )

    def _empty_result(
        self, workflow_id: str, analysis_period_hours: int
    ) -> ExecutionAnalysisResult:
        """Create empty result when no executions."""
        return ExecutionAnalysisResult(
            workflow_id=workflow_id,
            analysis_period_hours=analysis_period_hours,
            total_executions=0,
            successful_executions=0,
            failed_executions=0,
            duration_trend=DurationTrend(
                direction=TrendDirection.STABLE,
                current_avg_ms=0,
                previous_avg_ms=0,
                change_percent=0,
                confidence=0,
            ),
            success_rate_trend=SuccessRateTrend(
                direction=TrendDirection.STABLE,
                current_rate=1.0,
                previous_rate=1.0,
                change_percent=0,
                confidence=0,
            ),
            time_distribution=TimeDistribution(),
        )

    def _calculate_duration_trend(
        self,
        current: List[Dict[str, Any]],
        previous: List[Dict[str, Any]],
    ) -> DurationTrend:
        """Calculate duration trend between periods."""
        current_durations = [
            e.get("duration_ms", 0) for e in current if e.get("duration_ms")
        ]
        previous_durations = [
            e.get("duration_ms", 0) for e in previous if e.get("duration_ms")
        ]

        current_avg = (
            sum(current_durations) / len(current_durations) if current_durations else 0
        )
        previous_avg = (
            sum(previous_durations) / len(previous_durations)
            if previous_durations
            else 0
        )

        if previous_avg > 0:
            change_percent = ((current_avg - previous_avg) / previous_avg) * 100
        else:
            change_percent = 0

        # Determine direction
        if abs(change_percent) < self.SIGNIFICANT_CHANGE_PERCENT:
            direction = TrendDirection.STABLE
        elif change_percent < 0:
            direction = TrendDirection.IMPROVING  # Faster is better
        else:
            direction = TrendDirection.DEGRADING

        # Calculate confidence based on sample size
        total_samples = len(current_durations) + len(previous_durations)
        confidence = min(1.0, total_samples / self.HIGH_CONFIDENCE_SAMPLES)

        return DurationTrend(
            direction=direction,
            current_avg_ms=current_avg,
            previous_avg_ms=previous_avg,
            change_percent=change_percent,
            confidence=confidence,
        )

    def _calculate_success_rate_trend(
        self,
        current: List[Dict[str, Any]],
        previous: List[Dict[str, Any]],
    ) -> SuccessRateTrend:
        """Calculate success rate trend between periods."""
        current_successes = sum(1 for e in current if e.get("status") == "success")
        previous_successes = sum(1 for e in previous if e.get("status") == "success")

        current_rate = current_successes / len(current) if current else 1.0
        previous_rate = previous_successes / len(previous) if previous else 1.0

        if previous_rate > 0:
            change_percent = ((current_rate - previous_rate) / previous_rate) * 100
        else:
            change_percent = 0 if current_rate == 1.0 else -100

        # Determine direction
        if abs(change_percent) < self.SIGNIFICANT_CHANGE_PERCENT:
            direction = TrendDirection.STABLE
        elif change_percent > 0:
            direction = TrendDirection.IMPROVING  # Higher success rate is better
        else:
            direction = TrendDirection.DEGRADING

        # Calculate confidence
        total_samples = len(current) + len(previous)
        confidence = min(1.0, total_samples / self.HIGH_CONFIDENCE_SAMPLES)

        return SuccessRateTrend(
            direction=direction,
            current_rate=current_rate,
            previous_rate=previous_rate,
            change_percent=change_percent,
            confidence=confidence,
        )

    def _calculate_time_distribution(
        self, executions: List[Dict[str, Any]]
    ) -> TimeDistribution:
        """Calculate execution time distribution."""
        hourly: Dict[int, int] = defaultdict(int)
        daily: Dict[str, int] = defaultdict(int)

        for execution in executions:
            timestamp = execution.get("timestamp")
            if isinstance(timestamp, datetime):
                hourly[timestamp.hour] += 1
                daily[timestamp.strftime("%A")] += 1

        # Find peak times
        peak_hour = max(hourly, key=hourly.get) if hourly else 0
        peak_day = max(daily, key=daily.get) if daily else ""

        # Find off-peak hours (less than 25% of peak)
        off_peak = []
        if hourly:
            peak_count = hourly[peak_hour]
            for hour, count in hourly.items():
                if count < peak_count * 0.25:
                    off_peak.append(hour)

        return TimeDistribution(
            hourly=dict(hourly),
            daily=dict(daily),
            peak_hour=peak_hour,
            peak_day=peak_day,
            off_peak_hours=sorted(off_peak),
        )

    def _calculate_error_breakdown(
        self, executions: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Calculate error type breakdown."""
        errors: Dict[str, int] = defaultdict(int)

        for execution in executions:
            if execution.get("status") == "failed":
                error_type = execution.get("error_type", "unknown")
                errors[error_type] += 1

        return dict(errors)

    def _generate_insights(
        self,
        executions: List[Dict[str, Any]],
        duration_trend: DurationTrend,
        success_rate_trend: SuccessRateTrend,
        time_distribution: TimeDistribution,
    ) -> List[ExecutionInsight]:
        """Generate actionable insights from analysis."""
        insights = []

        # Performance trend insights
        if (
            duration_trend.direction == TrendDirection.IMPROVING
            and duration_trend.confidence > 0.5
        ):
            if abs(duration_trend.change_percent) >= self.PERFORMANCE_CHANGE_THRESHOLD:
                insights.append(
                    ExecutionInsight(
                        insight_type=InsightType.PERFORMANCE_IMPROVEMENT,
                        title="Performance Improving",
                        description=f"Execution time has improved by {abs(duration_trend.change_percent):.1f}%",
                        significance=min(1.0, abs(duration_trend.change_percent) / 50),
                        data={
                            "improvement_percent": abs(duration_trend.change_percent),
                            "current_avg_ms": duration_trend.current_avg_ms,
                            "previous_avg_ms": duration_trend.previous_avg_ms,
                        },
                    )
                )

        elif (
            duration_trend.direction == TrendDirection.DEGRADING
            and duration_trend.confidence > 0.5
        ):
            if abs(duration_trend.change_percent) >= self.PERFORMANCE_CHANGE_THRESHOLD:
                insights.append(
                    ExecutionInsight(
                        insight_type=InsightType.PERFORMANCE_DEGRADATION,
                        title="Performance Degrading",
                        description=f"Execution time has increased by {duration_trend.change_percent:.1f}%",
                        significance=min(1.0, duration_trend.change_percent / 50),
                        data={
                            "degradation_percent": duration_trend.change_percent,
                            "current_avg_ms": duration_trend.current_avg_ms,
                            "previous_avg_ms": duration_trend.previous_avg_ms,
                        },
                        recommended_action="Investigate recent changes and check for new bottlenecks",
                    )
                )

        # Reliability insights
        if (
            success_rate_trend.direction == TrendDirection.DEGRADING
            and success_rate_trend.confidence > 0.5
        ):
            insights.append(
                ExecutionInsight(
                    insight_type=InsightType.RELIABILITY_ISSUE,
                    title="Reliability Declining",
                    description=f"Success rate dropped from {success_rate_trend.previous_rate*100:.1f}% to {success_rate_trend.current_rate*100:.1f}%",
                    significance=abs(success_rate_trend.change_percent) / 100,
                    data={
                        "current_rate": success_rate_trend.current_rate,
                        "previous_rate": success_rate_trend.previous_rate,
                    },
                    recommended_action="Review recent failures and enable self-healing",
                )
            )

        # Check for success/failure streaks
        streak_insight = self._detect_streaks(executions)
        if streak_insight:
            insights.append(streak_insight)

        # Schedule optimization insight
        if (
            time_distribution.off_peak_hours
            and len(time_distribution.off_peak_hours) >= 4
        ):
            insights.append(
                ExecutionInsight(
                    insight_type=InsightType.SCHEDULE_OPTIMIZATION,
                    title="Schedule Optimization Available",
                    description=f"Consider scheduling during off-peak hours: {time_distribution.off_peak_hours[:5]}",
                    significance=0.3,
                    data={
                        "peak_hour": time_distribution.peak_hour,
                        "off_peak_hours": time_distribution.off_peak_hours,
                    },
                    recommended_action=f"Move non-critical executions to hours {time_distribution.off_peak_hours[:3]}",
                )
            )

        # Sort by significance
        insights.sort(key=lambda i: -i.significance)

        return insights[:10]  # Return top 10 insights

    def _detect_streaks(
        self, executions: List[Dict[str, Any]]
    ) -> Optional[ExecutionInsight]:
        """Detect success or failure streaks."""
        if not executions:
            return None

        current_streak = 0
        streak_type = None

        for execution in reversed(executions):  # Start from most recent
            status = execution.get("status")

            if streak_type is None:
                streak_type = status
                current_streak = 1
            elif status == streak_type:
                current_streak += 1
            else:
                break

        if streak_type == "success" and current_streak >= self.SUCCESS_STREAK_THRESHOLD:
            return ExecutionInsight(
                insight_type=InsightType.SUCCESS_STREAK,
                title="Excellent Reliability",
                description=f"Last {current_streak} executions were successful",
                significance=min(1.0, current_streak / 50),
                data={"streak_length": current_streak},
            )

        elif (
            streak_type == "failed" and current_streak >= self.FAILURE_STREAK_THRESHOLD
        ):
            return ExecutionInsight(
                insight_type=InsightType.FAILURE_PATTERN,
                title="Consecutive Failures Detected",
                description=f"Last {current_streak} executions failed",
                significance=min(1.0, current_streak / 5),
                data={"streak_length": current_streak},
                recommended_action="Investigate immediately - workflow may need repair",
            )

        return None


__all__ = [
    "ExecutionAnalyzer",
    "ExecutionAnalysisResult",
    "ExecutionInsight",
    "InsightType",
    "DurationTrend",
    "SuccessRateTrend",
    "TimeDistribution",
    "TrendDirection",
]
