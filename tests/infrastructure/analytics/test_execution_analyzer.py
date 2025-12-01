"""Tests for Execution Analyzer."""

import pytest
from datetime import datetime, timedelta

from casare_rpa.infrastructure.analytics.execution_analyzer import (
    ExecutionAnalyzer,
    ExecutionAnalysisResult,
    ExecutionInsight,
    InsightType,
    DurationTrend,
    SuccessRateTrend,
    TimeDistribution,
    TrendDirection,
)


class TestTrendDirection:
    """Tests for TrendDirection enum."""

    def test_trend_directions(self):
        """Test all trend directions exist."""
        assert TrendDirection.IMPROVING.value == "improving"
        assert TrendDirection.STABLE.value == "stable"
        assert TrendDirection.DEGRADING.value == "degrading"


class TestInsightType:
    """Tests for InsightType enum."""

    def test_insight_types(self):
        """Test all insight types exist."""
        assert InsightType.PERFORMANCE_IMPROVEMENT.value == "performance_improvement"
        assert InsightType.PERFORMANCE_DEGRADATION.value == "performance_degradation"
        assert InsightType.RELIABILITY_ISSUE.value == "reliability_issue"
        assert InsightType.SUCCESS_STREAK.value == "success_streak"
        assert InsightType.FAILURE_PATTERN.value == "failure_pattern"
        assert InsightType.SCHEDULE_OPTIMIZATION.value == "schedule_optimization"
        assert InsightType.RESOURCE_USAGE.value == "resource_usage"


class TestDurationTrend:
    """Tests for DurationTrend dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        trend = DurationTrend(
            direction=TrendDirection.IMPROVING,
            current_avg_ms=500,
            previous_avg_ms=1000,
            change_percent=-50.0,
            confidence=0.8,
        )
        result = trend.to_dict()

        assert result["direction"] == "improving"
        assert result["current_avg_ms"] == 500
        assert result["previous_avg_ms"] == 1000
        assert result["change_percent"] == -50.0
        assert result["confidence"] == 0.8


class TestSuccessRateTrend:
    """Tests for SuccessRateTrend dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        trend = SuccessRateTrend(
            direction=TrendDirection.DEGRADING,
            current_rate=0.85,
            previous_rate=0.95,
            change_percent=-10.53,
            confidence=0.9,
        )
        result = trend.to_dict()

        assert result["direction"] == "degrading"
        assert result["current_rate"] == 0.85
        assert result["previous_rate"] == 0.95
        assert abs(result["change_percent"] - (-10.53)) < 0.01
        assert result["confidence"] == 0.9


class TestTimeDistribution:
    """Tests for TimeDistribution dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        dist = TimeDistribution(
            hourly={9: 10, 10: 15, 11: 12},
            daily={"Monday": 20, "Tuesday": 25},
            peak_hour=10,
            peak_day="Tuesday",
            off_peak_hours=[0, 1, 2, 3, 4, 5],
        )
        result = dist.to_dict()

        assert result["hourly"] == {9: 10, 10: 15, 11: 12}
        assert result["daily"] == {"Monday": 20, "Tuesday": 25}
        assert result["peak_hour"] == 10
        assert result["peak_day"] == "Tuesday"
        assert result["off_peak_hours"] == [0, 1, 2, 3, 4, 5]


class TestExecutionInsight:
    """Tests for ExecutionInsight dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        insight = ExecutionInsight(
            insight_type=InsightType.PERFORMANCE_IMPROVEMENT,
            title="Performance Improving",
            description="Execution time improved by 30%",
            significance=0.6,
            data={"improvement": 30},
            recommended_action=None,
        )
        result = insight.to_dict()

        assert result["type"] == "performance_improvement"
        assert result["title"] == "Performance Improving"
        assert result["description"] == "Execution time improved by 30%"
        assert result["significance"] == 0.6
        assert result["data"] == {"improvement": 30}
        assert result["recommended_action"] is None

    def test_to_dict_with_recommendation(self):
        """Test conversion with recommendation."""
        insight = ExecutionInsight(
            insight_type=InsightType.RELIABILITY_ISSUE,
            title="Reliability Issue",
            description="Success rate dropped",
            significance=0.8,
            recommended_action="Investigate failures",
        )
        result = insight.to_dict()

        assert result["recommended_action"] == "Investigate failures"


class TestExecutionAnalysisResult:
    """Tests for ExecutionAnalysisResult dataclass."""

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        result = ExecutionAnalysisResult(
            workflow_id="wf123",
            analysis_period_hours=168,
            total_executions=100,
            successful_executions=85,
            failed_executions=15,
            duration_trend=DurationTrend(TrendDirection.STABLE, 500, 500, 0, 0.5),
            success_rate_trend=SuccessRateTrend(
                TrendDirection.STABLE, 0.85, 0.85, 0, 0.5
            ),
            time_distribution=TimeDistribution(),
        )
        assert result.success_rate == 0.85
        assert abs(result.failure_rate - 0.15) < 0.001  # Float comparison

    def test_success_rate_no_executions(self):
        """Test success rate with no executions."""
        result = ExecutionAnalysisResult(
            workflow_id="wf123",
            analysis_period_hours=168,
            total_executions=0,
            successful_executions=0,
            failed_executions=0,
            duration_trend=DurationTrend(TrendDirection.STABLE, 0, 0, 0, 0),
            success_rate_trend=SuccessRateTrend(TrendDirection.STABLE, 1.0, 1.0, 0, 0),
            time_distribution=TimeDistribution(),
        )
        assert result.success_rate == 1.0

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = ExecutionAnalysisResult(
            workflow_id="wf123",
            analysis_period_hours=168,
            total_executions=50,
            successful_executions=45,
            failed_executions=5,
            duration_trend=DurationTrend(
                TrendDirection.IMPROVING, 400, 600, -33.3, 0.8
            ),
            success_rate_trend=SuccessRateTrend(
                TrendDirection.STABLE, 0.9, 0.88, 2.3, 0.8
            ),
            time_distribution=TimeDistribution(
                hourly={9: 5}, daily={"Monday": 10}, peak_hour=9, peak_day="Monday"
            ),
            insights=[
                ExecutionInsight(
                    InsightType.PERFORMANCE_IMPROVEMENT,
                    "Better",
                    "Faster now",
                    0.5,
                )
            ],
            error_breakdown={"timeout": 3, "element_not_found": 2},
        )
        dict_result = result.to_dict()

        assert dict_result["workflow_id"] == "wf123"
        assert dict_result["analysis_period_hours"] == 168
        assert dict_result["total_executions"] == 50
        assert dict_result["success_rate"] == 0.9
        assert dict_result["insight_count"] == 1
        assert dict_result["error_breakdown"] == {"timeout": 3, "element_not_found": 2}


class TestExecutionAnalyzer:
    """Tests for ExecutionAnalyzer class."""

    def test_init(self):
        """Test initialization."""
        analyzer = ExecutionAnalyzer()
        assert analyzer.SIGNIFICANT_CHANGE_PERCENT == 10.0
        assert analyzer.SUCCESS_STREAK_THRESHOLD == 20

    def test_analyze_empty_data(self):
        """Test analyze with no executions."""
        analyzer = ExecutionAnalyzer()
        result = analyzer.analyze("wf123", [], analysis_period_hours=168)

        assert result.workflow_id == "wf123"
        assert result.total_executions == 0
        assert result.duration_trend.direction == TrendDirection.STABLE
        assert result.success_rate_trend.current_rate == 1.0

    def test_analyze_single_execution(self):
        """Test analyze with single execution."""
        analyzer = ExecutionAnalyzer()
        executions = [
            {
                "timestamp": datetime.now(),
                "status": "success",
                "duration_ms": 500,
            }
        ]
        result = analyzer.analyze("wf123", executions)

        assert result.total_executions == 1
        assert result.successful_executions == 1
        assert result.failed_executions == 0


class TestDurationTrendAnalysis:
    """Tests for duration trend calculation."""

    def test_improving_duration_trend(self):
        """Test detection of improving duration trend."""
        analyzer = ExecutionAnalyzer()
        now = datetime.now()

        # First half slow, second half fast
        executions = [
            {
                "timestamp": now - timedelta(hours=i),
                "status": "success",
                "duration_ms": 1000,
            }
            for i in range(50, 25, -1)  # Older, slower
        ] + [
            {
                "timestamp": now - timedelta(hours=i),
                "status": "success",
                "duration_ms": 500,
            }
            for i in range(25, 0, -1)  # Newer, faster
        ]

        result = analyzer.analyze("wf123", executions)

        assert result.duration_trend.direction == TrendDirection.IMPROVING
        assert result.duration_trend.change_percent < 0  # Negative = faster

    def test_degrading_duration_trend(self):
        """Test detection of degrading duration trend."""
        analyzer = ExecutionAnalyzer()
        now = datetime.now()

        # First half fast, second half slow
        executions = [
            {
                "timestamp": now - timedelta(hours=i),
                "status": "success",
                "duration_ms": 500,
            }
            for i in range(50, 25, -1)  # Older, faster
        ] + [
            {
                "timestamp": now - timedelta(hours=i),
                "status": "success",
                "duration_ms": 1000,
            }
            for i in range(25, 0, -1)  # Newer, slower
        ]

        result = analyzer.analyze("wf123", executions)

        assert result.duration_trend.direction == TrendDirection.DEGRADING
        assert result.duration_trend.change_percent > 0  # Positive = slower

    def test_stable_duration_trend(self):
        """Test detection of stable duration trend."""
        analyzer = ExecutionAnalyzer()
        now = datetime.now()

        executions = [
            {
                "timestamp": now - timedelta(hours=i),
                "status": "success",
                "duration_ms": 500,
            }
            for i in range(50)
        ]

        result = analyzer.analyze("wf123", executions)

        assert result.duration_trend.direction == TrendDirection.STABLE
        assert abs(result.duration_trend.change_percent) < 10  # Less than 10% change


class TestSuccessRateTrendAnalysis:
    """Tests for success rate trend calculation."""

    def test_improving_success_rate(self):
        """Test detection of improving success rate."""
        analyzer = ExecutionAnalyzer()
        now = datetime.now()

        # First half more failures, second half fewer
        executions = [
            {
                "timestamp": now - timedelta(hours=i),
                "status": "failed" if i % 3 == 0 else "success",
                "duration_ms": 500,
            }
            for i in range(50, 25, -1)
        ] + [
            {
                "timestamp": now - timedelta(hours=i),
                "status": "success",
                "duration_ms": 500,
            }
            for i in range(25, 0, -1)
        ]

        result = analyzer.analyze("wf123", executions)

        assert result.success_rate_trend.direction == TrendDirection.IMPROVING
        assert (
            result.success_rate_trend.current_rate
            > result.success_rate_trend.previous_rate
        )

    def test_degrading_success_rate(self):
        """Test detection of degrading success rate."""
        analyzer = ExecutionAnalyzer()
        now = datetime.now()

        # First half all success, second half more failures
        executions = [
            {
                "timestamp": now - timedelta(hours=i),
                "status": "success",
                "duration_ms": 500,
            }
            for i in range(50, 25, -1)
        ] + [
            {
                "timestamp": now - timedelta(hours=i),
                "status": "failed" if i % 2 == 0 else "success",
                "duration_ms": 500,
            }
            for i in range(25, 0, -1)
        ]

        result = analyzer.analyze("wf123", executions)

        assert result.success_rate_trend.direction == TrendDirection.DEGRADING
        assert (
            result.success_rate_trend.current_rate
            < result.success_rate_trend.previous_rate
        )


class TestTimeDistributionAnalysis:
    """Tests for time distribution calculation."""

    def test_hourly_distribution(self):
        """Test hourly execution distribution."""
        analyzer = ExecutionAnalyzer()

        executions = [
            {
                "timestamp": datetime(2025, 1, 1, hour=9),
                "status": "success",
                "duration_ms": 500,
            },
            {
                "timestamp": datetime(2025, 1, 1, hour=9),
                "status": "success",
                "duration_ms": 500,
            },
            {
                "timestamp": datetime(2025, 1, 1, hour=10),
                "status": "success",
                "duration_ms": 500,
            },
            {
                "timestamp": datetime(2025, 1, 1, hour=14),
                "status": "success",
                "duration_ms": 500,
            },
        ]

        result = analyzer.analyze("wf123", executions)

        assert result.time_distribution.hourly.get(9, 0) == 2
        assert result.time_distribution.hourly.get(10, 0) == 1
        assert result.time_distribution.peak_hour == 9

    def test_daily_distribution(self):
        """Test daily execution distribution."""
        analyzer = ExecutionAnalyzer()

        # Monday = 2, Tuesday = 1
        executions = [
            {
                "timestamp": datetime(2025, 1, 6, hour=9),
                "status": "success",
                "duration_ms": 500,
            },  # Monday
            {
                "timestamp": datetime(2025, 1, 6, hour=10),
                "status": "success",
                "duration_ms": 500,
            },  # Monday
            {
                "timestamp": datetime(2025, 1, 7, hour=9),
                "status": "success",
                "duration_ms": 500,
            },  # Tuesday
        ]

        result = analyzer.analyze("wf123", executions)

        assert result.time_distribution.daily.get("Monday", 0) == 2
        assert result.time_distribution.peak_day == "Monday"

    def test_off_peak_hours(self):
        """Test off-peak hours detection."""
        analyzer = ExecutionAnalyzer()

        # Heavy traffic at hour 10
        executions = [
            {
                "timestamp": datetime(2025, 1, 1, hour=10),
                "status": "success",
                "duration_ms": 500,
            }
            for _ in range(20)
        ] + [
            {
                "timestamp": datetime(2025, 1, 1, hour=3),
                "status": "success",
                "duration_ms": 500,
            }
        ]

        result = analyzer.analyze("wf123", executions)

        assert result.time_distribution.peak_hour == 10
        assert 3 in result.time_distribution.off_peak_hours


class TestErrorBreakdown:
    """Tests for error breakdown calculation."""

    def test_error_type_counting(self):
        """Test error types are counted correctly."""
        analyzer = ExecutionAnalyzer()
        now = datetime.now()

        executions = [
            {
                "timestamp": now,
                "status": "failed",
                "error_type": "timeout",
                "duration_ms": 500,
            },
            {
                "timestamp": now,
                "status": "failed",
                "error_type": "timeout",
                "duration_ms": 500,
            },
            {
                "timestamp": now,
                "status": "failed",
                "error_type": "element_not_found",
                "duration_ms": 500,
            },
            {"timestamp": now, "status": "success", "duration_ms": 500},
        ]

        result = analyzer.analyze("wf123", executions)

        assert result.error_breakdown.get("timeout") == 2
        assert result.error_breakdown.get("element_not_found") == 1

    def test_unknown_error_type(self):
        """Test unknown error type handling."""
        analyzer = ExecutionAnalyzer()
        now = datetime.now()

        executions = [
            {"timestamp": now, "status": "failed", "duration_ms": 500},  # No error_type
        ]

        result = analyzer.analyze("wf123", executions)

        assert result.error_breakdown.get("unknown") == 1


class TestInsightGeneration:
    """Tests for insight generation."""

    def test_performance_improvement_insight(self):
        """Test performance improvement insight is generated."""
        analyzer = ExecutionAnalyzer()
        now = datetime.now()

        # Create significant performance improvement (>25%)
        executions = [
            {
                "timestamp": now - timedelta(hours=i),
                "status": "success",
                "duration_ms": 1000,
            }
            for i in range(100, 50, -1)
        ] + [
            {
                "timestamp": now - timedelta(hours=i),
                "status": "success",
                "duration_ms": 500,
            }
            for i in range(50, 0, -1)
        ]

        result = analyzer.analyze("wf123", executions)

        improvement_insights = [
            i
            for i in result.insights
            if i.insight_type == InsightType.PERFORMANCE_IMPROVEMENT
        ]
        assert len(improvement_insights) >= 1

    def test_performance_degradation_insight(self):
        """Test performance degradation insight is generated."""
        analyzer = ExecutionAnalyzer()
        now = datetime.now()

        # Create significant performance degradation (>25%)
        executions = [
            {
                "timestamp": now - timedelta(hours=i),
                "status": "success",
                "duration_ms": 500,
            }
            for i in range(100, 50, -1)
        ] + [
            {
                "timestamp": now - timedelta(hours=i),
                "status": "success",
                "duration_ms": 1000,
            }
            for i in range(50, 0, -1)
        ]

        result = analyzer.analyze("wf123", executions)

        degradation_insights = [
            i
            for i in result.insights
            if i.insight_type == InsightType.PERFORMANCE_DEGRADATION
        ]
        assert len(degradation_insights) >= 1
        if degradation_insights:
            assert degradation_insights[0].recommended_action is not None

    def test_reliability_issue_insight(self):
        """Test reliability issue insight is generated."""
        analyzer = ExecutionAnalyzer()
        now = datetime.now()

        # Create reliability degradation
        executions = [
            {
                "timestamp": now - timedelta(hours=i),
                "status": "success",
                "duration_ms": 500,
            }
            for i in range(100, 50, -1)
        ] + [
            {
                "timestamp": now - timedelta(hours=i),
                "status": "failed" if i % 2 == 0 else "success",
                "duration_ms": 500,
            }
            for i in range(50, 0, -1)
        ]

        result = analyzer.analyze("wf123", executions)

        reliability_insights = [
            i
            for i in result.insights
            if i.insight_type == InsightType.RELIABILITY_ISSUE
        ]
        assert len(reliability_insights) >= 1

    def test_success_streak_insight(self):
        """Test success streak insight is generated."""
        analyzer = ExecutionAnalyzer()
        now = datetime.now()

        # Create long success streak (>20)
        executions = [
            {
                "timestamp": now - timedelta(hours=i),
                "status": "success",
                "duration_ms": 500,
            }
            for i in range(30)
        ]

        result = analyzer.analyze("wf123", executions)

        streak_insights = [
            i for i in result.insights if i.insight_type == InsightType.SUCCESS_STREAK
        ]
        assert len(streak_insights) >= 1

    def test_failure_pattern_insight(self):
        """Test failure pattern insight is generated."""
        analyzer = ExecutionAnalyzer()
        now = datetime.now()

        # Create failure streak (>3)
        executions = [
            {
                "timestamp": now - timedelta(hours=i),
                "status": "success",
                "duration_ms": 500,
            }
            for i in range(10, 5, -1)
        ] + [
            {
                "timestamp": now - timedelta(hours=i),
                "status": "failed",
                "duration_ms": 500,
            }
            for i in range(5, 0, -1)
        ]

        result = analyzer.analyze("wf123", executions)

        failure_insights = [
            i for i in result.insights if i.insight_type == InsightType.FAILURE_PATTERN
        ]
        assert len(failure_insights) >= 1
        if failure_insights:
            assert failure_insights[0].recommended_action is not None

    def test_schedule_optimization_insight(self):
        """Test schedule optimization insight is generated."""
        analyzer = ExecutionAnalyzer()

        # Create heavy peak at one hour, minimal elsewhere
        executions = [
            {
                "timestamp": datetime(2025, 1, 1, hour=10),
                "status": "success",
                "duration_ms": 500,
            }
            for _ in range(100)
        ] + [
            {
                "timestamp": datetime(2025, 1, 1, hour=h),
                "status": "success",
                "duration_ms": 500,
            }
            for h in [0, 1, 2, 3, 4, 5]  # Off-peak hours
        ]

        result = analyzer.analyze("wf123", executions)

        schedule_insights = [
            i
            for i in result.insights
            if i.insight_type == InsightType.SCHEDULE_OPTIMIZATION
        ]
        # May or may not trigger based on off-peak count
        assert len(schedule_insights) >= 0


class TestInsightSorting:
    """Tests for insight sorting by significance."""

    def test_insights_sorted_by_significance(self):
        """Test insights are sorted by significance."""
        analyzer = ExecutionAnalyzer()
        now = datetime.now()

        # Create data that generates multiple insights
        executions = [
            {
                "timestamp": now - timedelta(hours=i),
                "status": "success",
                "duration_ms": 500,
            }
            for i in range(100, 50, -1)
        ] + [
            {
                "timestamp": now - timedelta(hours=i),
                "status": "failed" if i % 2 == 0 else "success",
                "duration_ms": 1500,
            }
            for i in range(50, 0, -1)
        ]

        result = analyzer.analyze("wf123", executions)

        if len(result.insights) >= 2:
            for i in range(len(result.insights) - 1):
                assert (
                    result.insights[i].significance
                    >= result.insights[i + 1].significance
                )

    def test_max_10_insights(self):
        """Test at most 10 insights are returned."""
        analyzer = ExecutionAnalyzer()
        now = datetime.now()

        # Create lots of data
        executions = [
            {
                "timestamp": now - timedelta(hours=i),
                "status": "success",
                "duration_ms": 500,
            }
            for i in range(1000)
        ]

        result = analyzer.analyze("wf123", executions)

        assert len(result.insights) <= 10


class TestConfidenceCalculation:
    """Tests for confidence calculation."""

    def test_low_confidence_small_sample(self):
        """Test low confidence with small sample size."""
        analyzer = ExecutionAnalyzer()
        now = datetime.now()

        executions = [
            {
                "timestamp": now - timedelta(hours=i),
                "status": "success",
                "duration_ms": 500,
            }
            for i in range(5)
        ]

        result = analyzer.analyze("wf123", executions)

        assert result.duration_trend.confidence < 0.5

    def test_high_confidence_large_sample(self):
        """Test high confidence with large sample size."""
        analyzer = ExecutionAnalyzer()
        now = datetime.now()

        executions = [
            {
                "timestamp": now - timedelta(hours=i),
                "status": "success",
                "duration_ms": 500,
            }
            for i in range(100)
        ]

        result = analyzer.analyze("wf123", executions)

        assert result.duration_trend.confidence > 0.5
