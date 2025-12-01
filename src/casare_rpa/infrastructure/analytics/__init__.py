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

from casare_rpa.infrastructure.analytics.bottleneck_detector import (
    BottleneckDetector,
    BottleneckInfo,
    DetailedBottleneckAnalysis,
    BottleneckType,
    Severity,
    NodeExecutionStats,
)

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

from casare_rpa.infrastructure.analytics.process_mining import (
    ProcessMiner,
    ProcessEventLog,
    ProcessDiscovery,
    ConformanceChecker,
    ProcessEnhancer,
    ProcessModel,
    ExecutionTrace,
    Activity,
    ActivityStatus,
    ConformanceReport,
    ProcessInsight,
    InsightCategory,
    Deviation,
    DeviationType,
    DirectFollowsEdge,
    get_process_miner,
)

__all__ = [
    # Metrics Aggregator
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
    # Bottleneck Detector
    "BottleneckDetector",
    "BottleneckInfo",
    "DetailedBottleneckAnalysis",
    "BottleneckType",
    "Severity",
    "NodeExecutionStats",
    # Execution Analyzer
    "ExecutionAnalyzer",
    "ExecutionAnalysisResult",
    "ExecutionInsight",
    "InsightType",
    "DurationTrend",
    "SuccessRateTrend",
    "TimeDistribution",
    "TrendDirection",
    # Process Mining
    "ProcessMiner",
    "ProcessEventLog",
    "ProcessDiscovery",
    "ConformanceChecker",
    "ProcessEnhancer",
    "ProcessModel",
    "ExecutionTrace",
    "Activity",
    "ActivityStatus",
    "ConformanceReport",
    "ProcessInsight",
    "InsightCategory",
    "Deviation",
    "DeviationType",
    "DirectFollowsEdge",
    "get_process_miner",
]
