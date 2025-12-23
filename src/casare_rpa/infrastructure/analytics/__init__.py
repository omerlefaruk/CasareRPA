"""
CasareRPA Infrastructure: Analytics Module

Provides metrics aggregation, historical analysis, and reporting capabilities
for workflow execution monitoring and optimization.

Architecture:
- metrics_aggregator.py: Facade for analytics API
- aggregation_strategies.py: Strategy pattern for different aggregation types
- metric_calculators.py: Business logic calculators
- metric_storage.py: Storage adapters
- bottleneck_detector.py: Bottleneck analysis
- execution_analyzer.py: Execution pattern analysis
- process_mining.py: Process mining capabilities
"""

# Metrics Aggregator (facade)
# Aggregation Strategies
from casare_rpa.infrastructure.analytics.aggregation_strategies import (
    AggregationPeriod,
    AggregationStrategy,
    AggregationStrategyFactory,
    DimensionalAggregationStrategy,
    DimensionalBucket,
    RollingWindowAggregationStrategy,
    RollingWindowResult,
    StatisticalAggregationStrategy,
    StatisticalResult,
    TimeBasedAggregationStrategy,
    TimeSeriesDataPoint,
)

# Bottleneck Detector
from casare_rpa.infrastructure.analytics.bottleneck_detector import (
    BottleneckDetector,
    BottleneckInfo,
    BottleneckType,
    DetailedBottleneckAnalysis,
    NodeExecutionStats,
    Severity,
)

# Execution Analyzer
from casare_rpa.infrastructure.analytics.execution_analyzer import (
    DurationTrend,
    ExecutionAnalysisResult,
    ExecutionAnalyzer,
    ExecutionInsight,
    InsightType,
    SuccessRateTrend,
    TimeDistribution,
    TrendDirection,
)

# Metric Calculators
from casare_rpa.infrastructure.analytics.metric_calculators import (
    BottleneckAnalysisCalculator,
    BottleneckAnalysisResult,
    CostAnalysisCalculator,
    CostAnalysisResult,
    EfficiencyScoreCalculator,
    EfficiencyScoreResult,
    SLAComplianceCalculator,
    SLAComplianceResult,
    VersionComparisonCalculator,
    VersionComparisonResult,
)

# Metric Models (public API data classes)
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

# Metric Storage
from casare_rpa.infrastructure.analytics.metric_storage import (
    ErrorTrackingStorage,
    HealingMetricsStorage,
    InMemoryJobRecordStorage,
    JobRecord,
    MetricsStorageManager,
    MetricStorage,
    QueueDepthStorage,
    RobotMetricsCache,
    RobotMetricsData,
    WorkflowMetricsCache,
    WorkflowMetricsData,
)
from casare_rpa.infrastructure.analytics.metrics_aggregator import (
    MetricsAggregator,
    get_metrics_aggregator,
)

# PM4Py Integration (lazy loaded)
from casare_rpa.infrastructure.analytics.pm4py_integration import (
    AlignmentResult,
    BPMNResult,
    ConformanceMethod,
    ConformanceSummary,
    DiscoveryAlgorithm,
    PetriNetResult,
    PM4PyIntegration,
    TokenReplayResult,
    get_pm4py_integration,
)

# Process Mining
from casare_rpa.infrastructure.analytics.process_mining import (
    Activity,
    ActivityStatus,
    ConformanceChecker,
    ConformanceReport,
    Deviation,
    DeviationType,
    DirectFollowsEdge,
    ExecutionTrace,
    InsightCategory,
    ProcessDiscovery,
    ProcessEnhancer,
    ProcessEventLog,
    ProcessInsight,
    ProcessMiner,
    ProcessModel,
    get_process_miner,
)

# XES Export
from casare_rpa.infrastructure.analytics.xes_exporter import (
    XESExporter,
    XESImporter,
)

__all__ = [
    # Metrics Aggregator (facade)
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
    # Aggregation Strategies
    "AggregationStrategy",
    "TimeBasedAggregationStrategy",
    "StatisticalAggregationStrategy",
    "DimensionalAggregationStrategy",
    "RollingWindowAggregationStrategy",
    "AggregationStrategyFactory",
    "StatisticalResult",
    "DimensionalBucket",
    "RollingWindowResult",
    # Metric Calculators
    "EfficiencyScoreCalculator",
    "EfficiencyScoreResult",
    "CostAnalysisCalculator",
    "CostAnalysisResult",
    "SLAComplianceCalculator",
    "SLAComplianceResult",
    "BottleneckAnalysisCalculator",
    "BottleneckAnalysisResult",
    "VersionComparisonCalculator",
    "VersionComparisonResult",
    # Metric Storage
    "JobRecord",
    "WorkflowMetricsData",
    "RobotMetricsData",
    "MetricStorage",
    "InMemoryJobRecordStorage",
    "WorkflowMetricsCache",
    "RobotMetricsCache",
    "ErrorTrackingStorage",
    "HealingMetricsStorage",
    "QueueDepthStorage",
    "MetricsStorageManager",
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
    # XES Export
    "XESExporter",
    "XESImporter",
    # PM4Py Integration
    "PM4PyIntegration",
    "DiscoveryAlgorithm",
    "ConformanceMethod",
    "PetriNetResult",
    "BPMNResult",
    "AlignmentResult",
    "TokenReplayResult",
    "ConformanceSummary",
    "get_pm4py_integration",
]
