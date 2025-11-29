"""
CasareRPA Infrastructure: Analytics Module

Provides metrics aggregation, historical analysis, and reporting capabilities
for workflow execution monitoring and optimization.
"""

from casare_rpa.infrastructure.analytics.metrics_aggregator import (
    MetricsAggregator,
    AggregationPeriod,
    TimeSeriesDataPoint,
    WorkflowMetrics,
    RobotPerformanceMetrics,
    ExecutionDistribution,
    BottleneckAnalysis,
    EfficiencyScore,
    CostAnalysis,
    SLACompliance,
    ComparativeAnalysis,
    AnalyticsReport,
    get_metrics_aggregator,
)

__all__ = [
    "MetricsAggregator",
    "AggregationPeriod",
    "TimeSeriesDataPoint",
    "WorkflowMetrics",
    "RobotPerformanceMetrics",
    "ExecutionDistribution",
    "BottleneckAnalysis",
    "EfficiencyScore",
    "CostAnalysis",
    "SLACompliance",
    "ComparativeAnalysis",
    "AnalyticsReport",
    "get_metrics_aggregator",
]
