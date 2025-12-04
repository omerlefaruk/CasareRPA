# Infrastructure Layer Functions

**Total:** 2637 functions

## casare_rpa.infrastructure.agent.heartbeat_service

**File:** `src\casare_rpa\infrastructure\agent\heartbeat_service.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | HeartbeatService | `self, interval: int, on_heartbeat: Optional[Callable[[Dict[str, Any]], None]], ...` | `-` | DUNDER |
| `_get_system_info` | HeartbeatService | `self` | `Dict[str, Any]` | INTERNAL |
| `async _heartbeat_loop` | HeartbeatService | `self` | `None` | INTERNAL |
| `async _send_heartbeat` | HeartbeatService | `self` | `None` | INTERNAL |
| `consecutive_failures` | HeartbeatService | `self` | `int` | UNUSED |
| `get_health_status` | HeartbeatService | `self` | `str` | USED |
| `get_status` | HeartbeatService | `self` | `Dict[str, Any]` | USED |
| `get_system_metrics` | HeartbeatService | `self` | `Dict[str, Any]` | USED |
| `is_running` | HeartbeatService | `self` | `bool` | USED |
| `last_heartbeat` | HeartbeatService | `self` | `Optional[datetime]` | UNUSED |
| `async send_immediate` | HeartbeatService | `self` | `None` | UNUSED |
| `async start` | HeartbeatService | `self` | `None` | USED |
| `async stop` | HeartbeatService | `self` | `None` | USED |
| `total_heartbeats` | HeartbeatService | `self` | `int` | UNUSED |


## casare_rpa.infrastructure.agent.job_executor

**File:** `src\casare_rpa\infrastructure\agent\job_executor.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | JobExecutor | `self, progress_callback: Optional[Callable[[str, int, str], None]], continue_on_error: bool, ...` | `-` | DUNDER |
| `async _report_progress` | JobExecutor | `self, job_id: str, progress: int, ...` | `None` | INTERNAL |
| `active_job_count` | JobExecutor | `self` | `int` | UNUSED |
| `cancel_job` | JobExecutor | `self, job_id: str` | `bool` | UNUSED |
| `clear_result` | JobExecutor | `self, job_id: str` | `None` | UNUSED |
| `async execute` | JobExecutor | `self, job_data: Dict[str, Any], initial_variables: Optional[Dict[str, Any]]` | `Dict[str, Any]` | USED |
| `get_result` | JobExecutor | `self, job_id: str` | `Optional[Dict[str, Any]]` | USED |
| `__init__` | _ProgressTracker | `self, job_id: str, callback: Optional[Callable[[str, int, str], None]]` | `-` | DUNDER |
| `on_node_completed` | _ProgressTracker | `self, event: Any` | `None` | UNUSED |
| `on_node_error` | _ProgressTracker | `self, event: Any` | `None` | UNUSED |
| `on_node_started` | _ProgressTracker | `self, event: Any` | `None` | UNUSED |


## casare_rpa.infrastructure.agent.log_handler

**File:** `src\casare_rpa\infrastructure\agent\log_handler.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `create_robot_log_handler` | - | `robot_id: str, send_callback: Optional[Callable[[str], Any]], min_level: str` | `tuple` | UNUSED |
| `__init__` | RobotLogHandler | `self, robot_id: str, send_callback: Optional[Callable[[str], Any]], ...` | `None` | DUNDER |
| `async _flush_loop` | RobotLogHandler | `self` | `None` | INTERNAL |
| `async flush` | RobotLogHandler | `self` | `int` | USED |
| `get_metrics` | RobotLogHandler | `self` | `Dict[str, Any]` | USED |
| `min_level` | RobotLogHandler | `self` | `LogLevel` | UNUSED |
| `min_level` | RobotLogHandler | `self, level: LogLevel` | `None` | UNUSED |
| `set_connected` | RobotLogHandler | `self, connected: bool` | `None` | USED |
| `set_send_callback` | RobotLogHandler | `self, callback: Callable[[str], Any]` | `None` | UNUSED |
| `sink` | RobotLogHandler | `self, message: Any` | `None` | UNUSED |
| `async start` | RobotLogHandler | `self` | `None` | USED |
| `async stop` | RobotLogHandler | `self` | `None` | USED |


## casare_rpa.infrastructure.agent.robot_agent

**File:** `src\casare_rpa\infrastructure\agent\robot_agent.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | RobotAgent | `self, config: RobotConfig` | `-` | DUNDER |
| `async _connect_and_run` | RobotAgent | `self` | `None` | INTERNAL |
| `async _execute_job` | RobotAgent | `self, job_data: Dict[str, Any]` | `None` | INTERNAL |
| `async _handle_error` | RobotAgent | `self, message: Dict[str, Any]` | `None` | INTERNAL |
| `async _handle_heartbeat_ack` | RobotAgent | `self, message: Dict[str, Any]` | `None` | INTERNAL |
| `async _handle_job_assign` | RobotAgent | `self, message: Dict[str, Any]` | `None` | INTERNAL |
| `async _handle_job_cancel` | RobotAgent | `self, message: Dict[str, Any]` | `None` | INTERNAL |
| `async _handle_message` | RobotAgent | `self, message: Dict[str, Any]` | `None` | INTERNAL |
| `async _handle_ping` | RobotAgent | `self, message: Dict[str, Any]` | `None` | INTERNAL |
| `async _handle_register_ack` | RobotAgent | `self, message: Dict[str, Any]` | `None` | INTERNAL |
| `async _message_loop` | RobotAgent | `self` | `None` | INTERNAL |
| `_on_heartbeat_failure` | RobotAgent | `self, error: Exception` | `None` | INTERNAL |
| `async _on_job_progress` | RobotAgent | `self, job_id: str, progress: int, ...` | `None` | INTERNAL |
| `async _register` | RobotAgent | `self` | `None` | INTERNAL |
| `async _send` | RobotAgent | `self, message: Dict[str, Any]` | `None` | INTERNAL |
| `async _send_heartbeat` | RobotAgent | `self, heartbeat_data: Dict[str, Any]` | `None` | INTERNAL |
| `_setup_signal_handlers` | RobotAgent | `self` | `None` | INTERNAL |
| `_signal_handler` | RobotAgent | `self, signum: int, frame: Any` | `None` | INTERNAL |
| `active_job_count` | RobotAgent | `self` | `int` | UNUSED |
| `active_job_ids` | RobotAgent | `self` | `List[str]` | UNUSED |
| `get_status` | RobotAgent | `self` | `Dict[str, Any]` | USED |
| `is_connected` | RobotAgent | `self` | `bool` | USED |
| `is_registered` | RobotAgent | `self` | `bool` | UNUSED |
| `is_running` | RobotAgent | `self` | `bool` | USED |
| `async start` | RobotAgent | `self` | `None` | USED |
| `async stop` | RobotAgent | `self, wait_for_jobs: bool` | `None` | USED |


## casare_rpa.infrastructure.agent.robot_config

**File:** `src\casare_rpa\infrastructure\agent\robot_config.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__post_init__` | RobotConfig | `self` | `None` | DUNDER |
| `_detect_capabilities` | RobotConfig | `self` | `List[str]` | INTERNAL |
| `_validate` | RobotConfig | `self` | `None` | INTERNAL |
| `from_env` | RobotConfig | `cls` | `'RobotConfig'` | USED |
| `from_file` | RobotConfig | `cls, config_path: Path` | `'RobotConfig'` | USED |
| `hostname` | RobotConfig | `self` | `str` | UNUSED |
| `os_info` | RobotConfig | `self` | `str` | UNUSED |
| `to_dict` | RobotConfig | `self` | `dict` | USED |
| `uses_api_key` | RobotConfig | `self` | `bool` | UNUSED |
| `uses_mtls` | RobotConfig | `self` | `bool` | UNUSED |


## casare_rpa.infrastructure.analytics.aggregation_strategies

**File:** `src\casare_rpa\infrastructure\analytics\aggregation_strategies.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `aggregate` | AggregationStrategy | `self, data: List[T]` | `V` | USED |
| `reset` | AggregationStrategy | `self` | `None` | USED |
| `create_dimensional` | AggregationStrategyFactory | `dimension_field: str, value_field: str, name_field: Optional[str]` | `DimensionalAggregationStrategy` | UNUSED |
| `create_rolling_window` | AggregationStrategyFactory | `window_size: int, trend_threshold: float` | `RollingWindowAggregationStrategy` | UNUSED |
| `create_statistical` | AggregationStrategyFactory | `max_samples: int` | `StatisticalAggregationStrategy` | UNUSED |
| `create_time_based` | AggregationStrategyFactory | `period: AggregationPeriod, value_field: str, timestamp_field: str` | `TimeBasedAggregationStrategy` | UNUSED |
| `__init__` | DimensionalAggregationStrategy | `self, dimension_field: str, value_field: str, ...` | `-` | DUNDER |
| `add_record` | DimensionalAggregationStrategy | `self, record: Dict[str, Any]` | `None` | USED |
| `aggregate` | DimensionalAggregationStrategy | `self, data: List[Dict[str, Any]]` | `Dict[str, DimensionalBucket]` | USED |
| `get_avg` | DimensionalAggregationStrategy | `b: DimensionalBucket` | `float` | UNUSED |
| `get_count` | DimensionalAggregationStrategy | `b: DimensionalBucket` | `float` | USED |
| `get_sum` | DimensionalAggregationStrategy | `b: DimensionalBucket` | `float` | UNUSED |
| `get_top_dimensions` | DimensionalAggregationStrategy | `self, n: int, by: str` | `List[DimensionalBucket]` | UNUSED |
| `reset` | DimensionalAggregationStrategy | `self` | `None` | USED |
| `add` | DimensionalBucket | `self, value: float` | `None` | USED |
| `avg_value` | DimensionalBucket | `self` | `float` | UNUSED |
| `to_dict` | DimensionalBucket | `self` | `Dict[str, Any]` | USED |
| `__init__` | RollingWindowAggregationStrategy | `self, window_size: int, trend_threshold: float` | `-` | DUNDER |
| `add_value` | RollingWindowAggregationStrategy | `self, value: float` | `None` | USED |
| `aggregate` | RollingWindowAggregationStrategy | `self, data: List[float]` | `RollingWindowResult` | USED |
| `get_result` | RollingWindowAggregationStrategy | `self` | `RollingWindowResult` | USED |
| `reset` | RollingWindowAggregationStrategy | `self` | `None` | USED |
| `to_dict` | RollingWindowResult | `self` | `Dict[str, Any]` | USED |
| `__init__` | StatisticalAggregationStrategy | `self, max_samples: int` | `-` | DUNDER |
| `add_value` | StatisticalAggregationStrategy | `self, value: float` | `None` | USED |
| `aggregate` | StatisticalAggregationStrategy | `self, data: List[float]` | `StatisticalResult` | USED |
| `get_statistics` | StatisticalAggregationStrategy | `self` | `StatisticalResult` | USED |
| `percentile` | StatisticalAggregationStrategy | `sorted_data: List[float], p: float` | `float` | USED |
| `reset` | StatisticalAggregationStrategy | `self` | `None` | USED |
| `to_dict` | StatisticalResult | `self` | `Dict[str, Any]` | USED |
| `__init__` | TimeBasedAggregationStrategy | `self, period: AggregationPeriod, value_field: str, ...` | `-` | DUNDER |
| `_truncate_to_period` | TimeBasedAggregationStrategy | `self, dt: datetime` | `datetime` | INTERNAL |
| `add_data_point` | TimeBasedAggregationStrategy | `self, record: Dict[str, Any]` | `None` | USED |
| `aggregate` | TimeBasedAggregationStrategy | `self, data: List[Dict[str, Any]]` | `List[TimeSeriesDataPoint]` | USED |
| `get_time_series` | TimeBasedAggregationStrategy | `self, start_time: Optional[datetime], end_time: Optional[datetime], ...` | `List[TimeSeriesDataPoint]` | USED |
| `reset` | TimeBasedAggregationStrategy | `self` | `None` | USED |
| `to_dict` | TimeSeriesDataPoint | `self` | `Dict[str, Any]` | USED |


## casare_rpa.infrastructure.analytics.bottleneck_detector

**File:** `src\casare_rpa\infrastructure\analytics\bottleneck_detector.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | BottleneckDetector | `self` | `-` | DUNDER |
| `_calculate_node_stats` | BottleneckDetector | `self, execution_data: List[Dict[str, Any]]` | `List[NodeExecutionStats]` | INTERNAL |
| `_calculate_optimization_score` | BottleneckDetector | `self, node_stats: List[NodeExecutionStats], bottlenecks: List[BottleneckInfo]` | `float` | INTERNAL |
| `_detect_failing_nodes` | BottleneckDetector | `self, node_stats: List[NodeExecutionStats]` | `List[BottleneckInfo]` | INTERNAL |
| `_detect_patterns` | BottleneckDetector | `self, execution_data: List[Dict[str, Any]], node_stats: List[NodeExecutionStats]` | `List[BottleneckInfo]` | INTERNAL |
| `_detect_slow_nodes` | BottleneckDetector | `self, node_stats: List[NodeExecutionStats]` | `List[BottleneckInfo]` | INTERNAL |
| `_get_failing_node_recommendation` | BottleneckDetector | `self, stat: NodeExecutionStats, error_type: str` | `str` | INTERNAL |
| `_get_slow_node_recommendation` | BottleneckDetector | `self, stat: NodeExecutionStats` | `str` | INTERNAL |
| `analyze` | BottleneckDetector | `self, workflow_id: str, execution_data: List[Dict[str, Any]], ...` | `DetailedBottleneckAnalysis` | USED |
| `to_dict` | BottleneckInfo | `self` | `Dict[str, Any]` | USED |
| `_severity_breakdown` | DetailedBottleneckAnalysis | `self` | `Dict[str, int]` | INTERNAL |
| `to_dict` | DetailedBottleneckAnalysis | `self` | `Dict[str, Any]` | USED |
| `failure_rate` | NodeExecutionStats | `self` | `float` | UNUSED |
| `success_rate` | NodeExecutionStats | `self` | `float` | UNUSED |


## casare_rpa.infrastructure.analytics.execution_analyzer

**File:** `src\casare_rpa\infrastructure\analytics\execution_analyzer.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `to_dict` | DurationTrend | `self` | `Dict[str, Any]` | USED |
| `failure_rate` | ExecutionAnalysisResult | `self` | `float` | UNUSED |
| `success_rate` | ExecutionAnalysisResult | `self` | `float` | UNUSED |
| `to_dict` | ExecutionAnalysisResult | `self` | `Dict[str, Any]` | USED |
| `__init__` | ExecutionAnalyzer | `self` | `-` | DUNDER |
| `_calculate_duration_trend` | ExecutionAnalyzer | `self, current: List[Dict[str, Any]], previous: List[Dict[str, Any]]` | `DurationTrend` | INTERNAL |
| `_calculate_error_breakdown` | ExecutionAnalyzer | `self, executions: List[Dict[str, Any]]` | `Dict[str, int]` | INTERNAL |
| `_calculate_success_rate_trend` | ExecutionAnalyzer | `self, current: List[Dict[str, Any]], previous: List[Dict[str, Any]]` | `SuccessRateTrend` | INTERNAL |
| `_calculate_time_distribution` | ExecutionAnalyzer | `self, executions: List[Dict[str, Any]]` | `TimeDistribution` | INTERNAL |
| `_detect_streaks` | ExecutionAnalyzer | `self, executions: List[Dict[str, Any]]` | `Optional[ExecutionInsight]` | INTERNAL |
| `_empty_result` | ExecutionAnalyzer | `self, workflow_id: str, analysis_period_hours: int` | `ExecutionAnalysisResult` | INTERNAL |
| `_generate_insights` | ExecutionAnalyzer | `self, executions: List[Dict[str, Any]], duration_trend: DurationTrend, ...` | `List[ExecutionInsight]` | INTERNAL |
| `analyze` | ExecutionAnalyzer | `self, workflow_id: str, executions: List[Dict[str, Any]], ...` | `ExecutionAnalysisResult` | USED |
| `to_dict` | ExecutionInsight | `self` | `Dict[str, Any]` | USED |
| `to_dict` | SuccessRateTrend | `self` | `Dict[str, Any]` | USED |
| `to_dict` | TimeDistribution | `self` | `Dict[str, Any]` | USED |


## casare_rpa.infrastructure.analytics.metric_calculators

**File:** `src\casare_rpa\infrastructure\analytics\metric_calculators.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `analyze` | BottleneckAnalysisCalculator | `self, workflow_id: str, records: List[Dict[str, Any]], ...` | `BottleneckAnalysisResult` | USED |
| `to_dict` | BottleneckAnalysisResult | `self` | `Dict[str, Any]` | USED |
| `__init__` | CostAnalysisCalculator | `self, robot_cost_per_hour: float, cloud_cost_per_hour: float, ...` | `-` | DUNDER |
| `calculate` | CostAnalysisCalculator | `self, records: List[Dict[str, Any]], period_start: datetime, ...` | `CostAnalysisResult` | USED |
| `to_dict` | CostAnalysisResult | `self` | `Dict[str, Any]` | USED |
| `__init__` | EfficiencyScoreCalculator | `self, reliability_weight: float, performance_weight: float, ...` | `-` | DUNDER |
| `_calculate_maintainability_score` | EfficiencyScoreCalculator | `self, error_type_count: int` | `float` | INTERNAL |
| `_calculate_performance_score` | EfficiencyScoreCalculator | `self, p95_ms: float` | `float` | INTERNAL |
| `_calculate_resource_score` | EfficiencyScoreCalculator | `self, healing_attempts: int, total_executions: int` | `float` | INTERNAL |
| `calculate` | EfficiencyScoreCalculator | `self, workflow_id: str, workflow_name: str, ...` | `EfficiencyScoreResult` | USED |
| `to_dict` | EfficiencyScoreResult | `self` | `Dict[str, Any]` | USED |
| `get_error_data` | MetricsDataSource | `self, workflow_id: Optional[str]` | `Dict[str, int]` | UNUSED |
| `get_healing_data` | MetricsDataSource | `self, workflow_id: Optional[str]` | `Dict[str, Any]` | UNUSED |
| `get_job_records` | MetricsDataSource | `self, workflow_id: Optional[str], start_time: Optional[datetime], ...` | `List[Dict[str, Any]]` | UNUSED |
| `get_workflow_data` | MetricsDataSource | `self, workflow_id: str` | `Dict[str, Any]` | USED |
| `__init__` | SLAComplianceCalculator | `self, default_success_rate: float, default_p95_ms: float, ...` | `-` | DUNDER |
| `check` | SLAComplianceCalculator | `self, workflow_id: str, workflow_name: str, ...` | `SLAComplianceResult` | USED |
| `to_dict` | SLAComplianceResult | `self` | `Dict[str, Any]` | USED |
| `_calculate_percentile` | VersionComparisonCalculator | `values: List[float], percentile: float` | `float` | INTERNAL |
| `compare` | VersionComparisonCalculator | `self, workflow_id: str, version_a: str, ...` | `VersionComparisonResult` | USED |
| `to_dict` | VersionComparisonResult | `self` | `Dict[str, Any]` | USED |


## casare_rpa.infrastructure.analytics.metric_models

**File:** `src\casare_rpa\infrastructure\analytics\metric_models.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `to_dict` | AnalyticsReport | `self` | `Dict[str, Any]` | USED |
| `from_durations` | ExecutionDistribution | `cls, durations: List[float]` | `'ExecutionDistribution'` | USED |
| `to_dict` | ExecutionDistribution | `self` | `Dict[str, Any]` | USED |
| `availability_percent` | RobotPerformanceMetrics | `self` | `float` | UNUSED |
| `from_cache` | RobotPerformanceMetrics | `cls, data: RobotMetricsData` | `'RobotPerformanceMetrics'` | USED |
| `success_rate` | RobotPerformanceMetrics | `self` | `float` | UNUSED |
| `to_dict` | RobotPerformanceMetrics | `self` | `Dict[str, Any]` | USED |
| `utilization_percent` | RobotPerformanceMetrics | `self` | `float` | UNUSED |
| `failure_rate` | WorkflowMetrics | `self` | `float` | UNUSED |
| `from_cache` | WorkflowMetrics | `cls, data: WorkflowMetricsData, durations: List[float], ...` | `'WorkflowMetrics'` | USED |
| `success_rate` | WorkflowMetrics | `self` | `float` | UNUSED |
| `to_dict` | WorkflowMetrics | `self` | `Dict[str, Any]` | USED |


## casare_rpa.infrastructure.analytics.metric_storage

**File:** `src\casare_rpa\infrastructure\analytics\metric_storage.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ErrorTrackingStorage | `self` | `-` | DUNDER |
| `clear` | ErrorTrackingStorage | `self` | `None` | USED |
| `get_global_counts` | ErrorTrackingStorage | `self` | `Dict[str, int]` | USED |
| `get_top_errors` | ErrorTrackingStorage | `self, n: int, workflow_id: Optional[str]` | `List[Dict[str, Any]]` | USED |
| `get_workflow_counts` | ErrorTrackingStorage | `self, workflow_id: str` | `Dict[str, int]` | USED |
| `record_error` | ErrorTrackingStorage | `self, workflow_id: str, error_type: str` | `None` | USED |
| `__init__` | HealingMetricsStorage | `self` | `-` | DUNDER |
| `clear` | HealingMetricsStorage | `self` | `None` | USED |
| `get_by_tier` | HealingMetricsStorage | `self` | `Dict[str, Dict[str, Any]]` | USED |
| `get_by_workflow` | HealingMetricsStorage | `self, workflow_id: Optional[str]` | `Dict[str, Any]` | USED |
| `record_from_record` | HealingMetricsStorage | `self, record: JobRecord` | `None` | USED |
| `record_healing` | HealingMetricsStorage | `self, workflow_id: str, tier: str, ...` | `None` | USED |
| `__init__` | InMemoryJobRecordStorage | `self, max_records: int` | `-` | DUNDER |
| `add` | InMemoryJobRecordStorage | `self, record: JobRecord` | `None` | USED |
| `clear` | InMemoryJobRecordStorage | `self` | `None` | USED |
| `get_all` | InMemoryJobRecordStorage | `self` | `List[JobRecord]` | USED |
| `get_by_robot` | InMemoryJobRecordStorage | `self, robot_id: str, start_time: Optional[datetime], ...` | `List[JobRecord]` | USED |
| `get_by_time_range` | InMemoryJobRecordStorage | `self, start_time: Optional[datetime], end_time: Optional[datetime]` | `List[JobRecord]` | USED |
| `get_by_version` | InMemoryJobRecordStorage | `self, workflow_id: str, version: str` | `List[JobRecord]` | USED |
| `get_by_workflow` | InMemoryJobRecordStorage | `self, workflow_id: str, start_time: Optional[datetime], ...` | `List[JobRecord]` | USED |
| `get_filtered` | InMemoryJobRecordStorage | `self, filter_func: Callable[[JobRecord], bool]` | `List[JobRecord]` | USED |
| `to_dict` | JobRecord | `self` | `Dict[str, Any]` | USED |
| `add` | MetricStorage | `self, item: T` | `None` | USED |
| `clear` | MetricStorage | `self` | `None` | USED |
| `get_all` | MetricStorage | `self` | `List[T]` | USED |
| `get_filtered` | MetricStorage | `self, filter_func: Callable[[T], bool]` | `List[T]` | USED |
| `__init__` | MetricsStorageManager | `self, max_job_records: int, max_duration_samples: int, ...` | `-` | DUNDER |
| `record_job` | MetricsStorageManager | `self, record: JobRecord` | `None` | USED |
| `reset` | MetricsStorageManager | `self` | `None` | USED |
| `__init__` | QueueDepthStorage | `self, max_points: int` | `-` | DUNDER |
| `clear` | QueueDepthStorage | `self` | `None` | USED |
| `get_history` | QueueDepthStorage | `self, hours: int, limit: int` | `List[TimeSeriesDataPoint]` | USED |
| `get_statistics` | QueueDepthStorage | `self, hours: int` | `Dict[str, Any]` | USED |
| `record` | QueueDepthStorage | `self, depth: int` | `None` | USED |
| `__init__` | RobotMetricsCache | `self` | `-` | DUNDER |
| `clear` | RobotMetricsCache | `self` | `None` | USED |
| `get` | RobotMetricsCache | `self, robot_id: str` | `Optional[RobotMetricsData]` | USED |
| `get_all` | RobotMetricsCache | `self` | `List[RobotMetricsData]` | USED |
| `update` | RobotMetricsCache | `self, record: JobRecord` | `None` | USED |
| `update_status` | RobotMetricsCache | `self, robot_id: str, status: str` | `None` | USED |
| `availability_percent` | RobotMetricsData | `self` | `float` | UNUSED |
| `success_rate` | RobotMetricsData | `self` | `float` | UNUSED |
| `update_from_record` | RobotMetricsData | `self, record: JobRecord` | `None` | USED |
| `utilization_percent` | RobotMetricsData | `self` | `float` | UNUSED |
| `__init__` | WorkflowMetricsCache | `self, max_duration_samples: int` | `-` | DUNDER |
| `_update_hourly` | WorkflowMetricsCache | `self, workflow_id: str, record: JobRecord` | `None` | INTERNAL |
| `clear` | WorkflowMetricsCache | `self` | `None` | USED |
| `get` | WorkflowMetricsCache | `self, workflow_id: str` | `Optional[WorkflowMetricsData]` | USED |
| `get_all` | WorkflowMetricsCache | `self` | `List[WorkflowMetricsData]` | USED |
| `get_durations` | WorkflowMetricsCache | `self, workflow_id: str` | `List[float]` | USED |
| `get_hourly_data` | WorkflowMetricsCache | `self, workflow_id: str, limit: int` | `List[TimeSeriesDataPoint]` | USED |
| `update` | WorkflowMetricsCache | `self, record: JobRecord` | `None` | USED |
| `failure_rate` | WorkflowMetricsData | `self` | `float` | UNUSED |
| `success_rate` | WorkflowMetricsData | `self` | `float` | UNUSED |
| `update_from_record` | WorkflowMetricsData | `self, record: JobRecord` | `None` | USED |


## casare_rpa.infrastructure.analytics.metrics_aggregator

**File:** `src\casare_rpa\infrastructure\analytics\metrics_aggregator.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `get_metrics_aggregator` | - | `` | `MetricsAggregator` | UNUSED |
| `__init__` | MetricsAggregator | `self` | `None` | DUNDER |
| `__new__` | MetricsAggregator | `cls` | `'MetricsAggregator'` | DUNDER |
| `analyze_bottlenecks` | MetricsAggregator | `self, workflow_id: str` | `BottleneckAnalysis` | USED |
| `calculate_cost_analysis` | MetricsAggregator | `self, start_time: datetime, end_time: datetime` | `CostAnalysis` | USED |
| `calculate_efficiency_score` | MetricsAggregator | `self, workflow_id: str` | `EfficiencyScore` | USED |
| `check_sla_compliance` | MetricsAggregator | `self, workflow_id: str, start_time: Optional[datetime], ...` | `SLACompliance` | USED |
| `compare_versions` | MetricsAggregator | `self, workflow_id: str, version_a: str, ...` | `ComparativeAnalysis` | UNUSED |
| `configure_costs` | MetricsAggregator | `self, robot_cost_per_hour: float, cloud_cost_per_hour: float, ...` | `None` | UNUSED |
| `configure_sla` | MetricsAggregator | `self, workflow_id: str, target_success_rate: float, ...` | `None` | UNUSED |
| `export_csv` | MetricsAggregator | `self, start_time: Optional[datetime], end_time: Optional[datetime]` | `str` | UNUSED |
| `generate_report` | MetricsAggregator | `self, period: AggregationPeriod, start_time: Optional[datetime], ...` | `AnalyticsReport` | UNUSED |
| `get_duration_statistics` | MetricsAggregator | `self, workflow_id: str, start_time: Optional[datetime], ...` | `ExecutionDistribution` | USED |
| `get_error_analysis` | MetricsAggregator | `self, workflow_id: Optional[str], top_n: int` | `Dict[str, Any]` | USED |
| `get_execution_summary` | MetricsAggregator | `self, start_time: Optional[datetime], end_time: Optional[datetime]` | `Dict[str, Any]` | USED |
| `get_healing_metrics` | MetricsAggregator | `self, workflow_id: Optional[str]` | `Dict[str, Any]` | USED |
| `get_instance` | MetricsAggregator | `cls` | `'MetricsAggregator'` | USED |
| `get_queue_metrics` | MetricsAggregator | `self, hours: int` | `Dict[str, Any]` | USED |
| `get_robot_metrics` | MetricsAggregator | `self, robot_id: Optional[str]` | `List[RobotPerformanceMetrics]` | USED |
| `get_time_series` | MetricsAggregator | `self, workflow_id: str, metric: str, ...` | `List[TimeSeriesDataPoint]` | USED |
| `get_workflow_metrics` | MetricsAggregator | `self, workflow_id: Optional[str], start_time: Optional[datetime], ...` | `List[WorkflowMetrics]` | USED |
| `record_healing_result` | MetricsAggregator | `self, workflow_id: str, tier: str, ...` | `None` | UNUSED |
| `record_job_execution` | MetricsAggregator | `self, job_id: str, workflow_id: str, ...` | `None` | UNUSED |
| `record_queue_depth` | MetricsAggregator | `self, depth: int` | `None` | UNUSED |
| `reset` | MetricsAggregator | `self` | `None` | USED |
| `reset_instance` | MetricsAggregator | `cls` | `None` | UNUSED |


## casare_rpa.infrastructure.analytics.process_mining

**File:** `src\casare_rpa\infrastructure\analytics\process_mining.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `get_process_miner` | - | `` | `ProcessMiner` | USED |
| `from_dict` | Activity | `cls, data: Dict[str, Any]` | `Activity` | USED |
| `to_dict` | Activity | `self` | `Dict[str, Any]` | USED |
| `batch_check` | ConformanceChecker | `self, traces: List[ExecutionTrace], model: ProcessModel` | `Dict[str, Any]` | USED |
| `check_conformance` | ConformanceChecker | `self, trace: ExecutionTrace, model: ProcessModel` | `ConformanceReport` | USED |
| `to_dict` | ConformanceReport | `self` | `Dict[str, Any]` | USED |
| `activity_sequence` | ExecutionTrace | `self` | `List[str]` | UNUSED |
| `success_rate` | ExecutionTrace | `self` | `float` | UNUSED |
| `to_dict` | ExecutionTrace | `self` | `Dict[str, Any]` | USED |
| `total_duration_ms` | ExecutionTrace | `self` | `int` | UNUSED |
| `variant` | ExecutionTrace | `self` | `str` | UNUSED |
| `__init__` | ProcessDiscovery | `self` | `None` | DUNDER |
| `_calculate_edge_stats` | ProcessDiscovery | `self, model: ProcessModel` | `None` | INTERNAL |
| `_detect_loops` | ProcessDiscovery | `self, model: ProcessModel` | `Set[str]` | INTERNAL |
| `_detect_parallelism` | ProcessDiscovery | `self, traces: List[ExecutionTrace], model: ProcessModel` | `List[Tuple[str, str]]` | INTERNAL |
| `_process_trace` | ProcessDiscovery | `self, trace: ExecutionTrace, model: ProcessModel` | `None` | INTERNAL |
| `discover` | ProcessDiscovery | `self, traces: List[ExecutionTrace]` | `ProcessModel` | USED |
| `discover_variants` | ProcessDiscovery | `self, traces: List[ExecutionTrace]` | `Dict[str, List[ExecutionTrace]]` | USED |
| `__init__` | ProcessEnhancer | `self` | `None` | DUNDER |
| `_find_error_patterns` | ProcessEnhancer | `self, model: ProcessModel, traces: List[ExecutionTrace]` | `List[ProcessInsight]` | INTERNAL |
| `_find_parallelization_opportunities` | ProcessEnhancer | `self, model: ProcessModel` | `List[ProcessInsight]` | INTERNAL |
| `_find_simplification_opportunities` | ProcessEnhancer | `self, model: ProcessModel, traces: List[ExecutionTrace]` | `List[ProcessInsight]` | INTERNAL |
| `_find_slow_paths` | ProcessEnhancer | `self, model: ProcessModel, traces: List[ExecutionTrace]` | `List[ProcessInsight]` | INTERNAL |
| `analyze` | ProcessEnhancer | `self, model: ProcessModel, traces: List[ExecutionTrace]` | `List[ProcessInsight]` | USED |
| `__init__` | ProcessEventLog | `self, max_traces: int` | `None` | DUNDER |
| `add_trace` | ProcessEventLog | `self, trace: ExecutionTrace` | `None` | USED |
| `clear` | ProcessEventLog | `self, workflow_id: Optional[str]` | `None` | USED |
| `get_all_workflows` | ProcessEventLog | `self` | `List[str]` | USED |
| `get_trace` | ProcessEventLog | `self, case_id: str` | `Optional[ExecutionTrace]` | USED |
| `get_trace_count` | ProcessEventLog | `self, workflow_id: Optional[str]` | `int` | USED |
| `get_traces_for_workflow` | ProcessEventLog | `self, workflow_id: str, limit: Optional[int], ...` | `List[ExecutionTrace]` | USED |
| `get_traces_in_timerange` | ProcessEventLog | `self, start_time: datetime, end_time: datetime, ...` | `List[ExecutionTrace]` | USED |
| `to_dict` | ProcessInsight | `self` | `Dict[str, Any]` | USED |
| `__init__` | ProcessMiner | `self, max_traces: int` | `None` | DUNDER |
| `check_conformance` | ProcessMiner | `self, trace: ExecutionTrace, workflow_id: Optional[str]` | `Optional[ConformanceReport]` | USED |
| `complete_trace` | ProcessMiner | `self, case_id: str, status: str` | `None` | USED |
| `discover_process` | ProcessMiner | `self, workflow_id: str, min_traces: int` | `Optional[ProcessModel]` | USED |
| `get_insights` | ProcessMiner | `self, workflow_id: str` | `List[ProcessInsight]` | USED |
| `get_process_summary` | ProcessMiner | `self, workflow_id: str` | `Dict[str, Any]` | USED |
| `get_variants` | ProcessMiner | `self, workflow_id: str` | `Dict[str, Any]` | USED |
| `record_activity` | ProcessMiner | `self, case_id: str, workflow_id: str, ...` | `None` | USED |
| `record_trace` | ProcessMiner | `self, trace: ExecutionTrace` | `None` | UNUSED |
| `_reconstruct_path_from_edges` | ProcessModel | `self` | `List[str]` | INTERNAL |
| `_select_best_entry_node` | ProcessModel | `self` | `Optional[str]` | INTERNAL |
| `_select_next_node` | ProcessModel | `self, current: str, visited: Set[str]` | `Optional[str]` | INTERNAL |
| `get_all_variant_paths` | ProcessModel | `self` | `Dict[str, Tuple[List[str], int]]` | UNUSED |
| `get_edge_frequency` | ProcessModel | `self, source: str, target: str` | `int` | UNUSED |
| `get_most_common_path` | ProcessModel | `self` | `List[str]` | USED |
| `get_variant_path` | ProcessModel | `self, variant_hash: str` | `List[str]` | UNUSED |
| `to_dict` | ProcessModel | `self` | `Dict[str, Any]` | USED |
| `to_mermaid` | ProcessModel | `self` | `str` | USED |


## casare_rpa.infrastructure.auth.robot_api_keys

**File:** `src\casare_rpa\infrastructure\auth\robot_api_keys.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `extract_key_prefix` | - | `raw_key: str, length: int` | `str` | USED |
| `generate_api_key_raw` | - | `` | `str` | USED |
| `hash_api_key` | - | `raw_key: str` | `str` | USED |
| `validate_api_key_format` | - | `raw_key: str` | `bool` | USED |
| `__init__` | ApiKeyExpiredError | `self, key_id: str, expired_at: datetime` | `None` | DUNDER |
| `__init__` | ApiKeyNotFoundError | `self, key_hint: str` | `None` | DUNDER |
| `__init__` | ApiKeyRevokedError | `self, key_id: str` | `None` | DUNDER |
| `is_expired` | RobotApiKey | `self` | `bool` | USED |
| `is_valid` | RobotApiKey | `self` | `bool` | UNUSED |
| `status` | RobotApiKey | `self` | `ApiKeyValidationResult` | UNUSED |
| `to_dict` | RobotApiKey | `self` | `Dict[str, Any]` | USED |
| `__init__` | RobotApiKeyError | `self, message: str, details: Optional[Dict[str, Any]]` | `None` | DUNDER |
| `__init__` | RobotApiKeyService | `self, db_client: Any` | `None` | DUNDER |
| `async _delete_expired_keys` | RobotApiKeyService | `self, days_old: int` | `int` | INTERNAL |
| `async _get_key_by_hash` | RobotApiKeyService | `self, api_key_hash: str` | `Optional[RobotApiKey]` | INTERNAL |
| `async _get_key_by_id` | RobotApiKeyService | `self, key_id: str` | `Optional[RobotApiKey]` | INTERNAL |
| `async _insert_key` | RobotApiKeyService | `self, robot_id: str, api_key_hash: str, ...` | `Dict[str, Any]` | INTERNAL |
| `async _list_keys_for_robot` | RobotApiKeyService | `self, robot_id: str, include_revoked: bool` | `List[RobotApiKey]` | INTERNAL |
| `_parse_datetime` | RobotApiKeyService | `self, value: Any` | `Optional[datetime]` | INTERNAL |
| `async _revoke_key` | RobotApiKeyService | `self, key_id: str, revoked_by: Optional[str], ...` | `bool` | INTERNAL |
| `_row_to_key` | RobotApiKeyService | `self, row: Dict[str, Any]` | `RobotApiKey` | INTERNAL |
| `async _update_last_used` | RobotApiKeyService | `self, api_key_hash: str, client_ip: Optional[str]` | `None` | INTERNAL |
| `async delete_expired_keys` | RobotApiKeyService | `self, days_old: int` | `int` | UNUSED |
| `async generate_api_key` | RobotApiKeyService | `self, robot_id: str, name: Optional[str], ...` | `tuple[str, RobotApiKey]` | USED |
| `async get_key_by_id` | RobotApiKeyService | `self, key_id: str` | `Optional[RobotApiKey]` | USED |
| `async list_keys_for_robot` | RobotApiKeyService | `self, robot_id: str, include_revoked: bool` | `List[RobotApiKey]` | UNUSED |
| `async revoke_api_key` | RobotApiKeyService | `self, key_id: str, revoked_by: Optional[str], ...` | `bool` | USED |
| `async rotate_key` | RobotApiKeyService | `self, key_id: str, rotated_by: Optional[str]` | `tuple[str, RobotApiKey]` | UNUSED |
| `async validate_api_key` | RobotApiKeyService | `self, raw_key: str, update_last_used: bool, ...` | `Optional[RobotApiKey]` | USED |


## casare_rpa.infrastructure.browser.healing.anchor_healer

**File:** `src\casare_rpa\infrastructure\browser\healing\anchor_healer.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | AnchorHealer | `self, near_threshold: float, min_confidence: float` | `None` | DUNDER |
| `_build_anchor_selector` | AnchorHealer | `self, anchor_data: Dict[str, Any]` | `Optional[str]` | INTERNAL |
| `_calculate_anchor_stability` | AnchorHealer | `self, anchor_data: Dict[str, Any]` | `float` | INTERNAL |
| `_determine_spatial_relation` | AnchorHealer | `self, target: BoundingRect, anchor: BoundingRect` | `SpatialRelation` | INTERNAL |
| `_generate_relative_selectors` | AnchorHealer | `self, anchor: AnchorElement, relation: SpatialRelation, ...` | `List[Tuple[str, float]]` | INTERNAL |
| `async capture_spatial_context` | AnchorHealer | `self, page: Page, selector: str` | `Optional[SpatialContext]` | USED |
| `async find_nearby_elements` | AnchorHealer | `self, page: Page, anchor_selector: str, ...` | `List[Dict[str, Any]]` | UNUSED |
| `get_context` | AnchorHealer | `self, selector: str` | `Optional[SpatialContext]` | USED |
| `async heal` | AnchorHealer | `self, page: Page, selector: str, ...` | `AnchorHealingResult` | USED |
| `store_context` | AnchorHealer | `self, selector: str, context: SpatialContext` | `None` | USED |


## casare_rpa.infrastructure.browser.healing.cv_healer

**File:** `src\casare_rpa\infrastructure\browser\healing\cv_healer.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_ensure_cv_imports` | - | `` | `bool` | INTERNAL |
| `to_dict` | CVContext | `self` | `Dict[str, Any]` | USED |
| `__init__` | CVHealer | `self, ocr_confidence_threshold: float, template_similarity_threshold: float, ...` | `None` | DUNDER |
| `_bytes_to_cv_image` | CVHealer | `self, image_bytes: bytes` | `Any` | INTERNAL |
| `_create_pixel_fallback_result` | CVHealer | `self, context: CVContext, selector: str, ...` | `CVHealingResult` | INTERNAL |
| `_dedupe_matches` | CVHealer | `self, matches: List[TemplateMatch], distance_threshold: int` | `List[TemplateMatch]` | INTERNAL |
| `_detect_visual_elements` | CVHealer | `self, screenshot: Any, expected_size: Tuple[int, int], ...` | `List[Dict[str, Any]]` | INTERNAL |
| `_find_multiword_matches` | CVHealer | `self, ocr_data: Dict[str, Any], search_text: str` | `List[OCRMatch]` | INTERNAL |
| `_perform_ocr` | CVHealer | `self, screenshot: Any, search_text: str` | `List[OCRMatch]` | INTERNAL |
| `_perform_template_matching` | CVHealer | `self, screenshot: Any, template: Any` | `List[TemplateMatch]` | INTERNAL |
| `_preprocess_for_ocr` | CVHealer | `self, gray_image: Any` | `Any` | INTERNAL |
| `async _try_ocr_healing` | CVHealer | `self, screenshot: Any, search_text: str, ...` | `CVHealingResult` | INTERNAL |
| `async _try_template_healing` | CVHealer | `self, screenshot: Any, template_bytes: bytes, ...` | `CVHealingResult` | INTERNAL |
| `async _try_visual_detection` | CVHealer | `self, screenshot: Any, context: CVContext, ...` | `CVHealingResult` | INTERNAL |
| `async capture_cv_context` | CVHealer | `self, page: Page, selector: str` | `Optional[CVContext]` | USED |
| `async find_template_on_page` | CVHealer | `self, page: Page, template_path: Path` | `List[TemplateMatch]` | UNUSED |
| `async find_text_on_page` | CVHealer | `self, page: Page, text: str, ...` | `List[OCRMatch]` | UNUSED |
| `get_context` | CVHealer | `self, selector: str` | `Optional[CVContext]` | USED |
| `async heal` | CVHealer | `self, page: Page, selector: str, ...` | `CVHealingResult` | USED |
| `is_available` | CVHealer | `self` | `bool` | UNUSED |
| `store_context` | CVHealer | `self, selector: str, context: CVContext` | `None` | USED |
| `to_dict` | CVHealingResult | `self` | `Dict[str, Any]` | USED |
| `center_x` | OCRMatch | `self` | `int` | UNUSED |
| `center_y` | OCRMatch | `self` | `int` | UNUSED |
| `to_dict` | OCRMatch | `self` | `Dict[str, Any]` | USED |
| `center_x` | TemplateMatch | `self` | `int` | UNUSED |
| `center_y` | TemplateMatch | `self` | `int` | UNUSED |
| `to_dict` | TemplateMatch | `self` | `Dict[str, Any]` | USED |


## casare_rpa.infrastructure.browser.healing.healing_chain

**File:** `src\casare_rpa\infrastructure\browser\healing\healing_chain.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `create_healing_chain` | - | `healing_budget_ms: float, cv_budget_ms: float, enable_cv: bool` | `SelectorHealingChain` | UNUSED |
| `cv_click_coordinates` | HealingChainResult | `self` | `Optional[Tuple[int, int]]` | UNUSED |
| `is_cv_result` | HealingChainResult | `self` | `bool` | UNUSED |
| `async heal` | HealingStrategy | `self, page: Any, selector: str` | `Any` | USED |
| `__init__` | SelectorHealingChain | `self, heuristic_healer: Optional[SelectorHealer], anchor_healer: Optional[AnchorHealer], ...` | `None` | DUNDER |
| `_record_telemetry` | SelectorHealingChain | `self, selector: str, page_url: str, ...` | `None` | INTERNAL |
| `async _try_anchor_healing` | SelectorHealingChain | `self, page: Page, selector: str, ...` | `AnchorHealingResult` | INTERNAL |
| `async _try_cv_healing` | SelectorHealingChain | `self, page: Page, selector: str, ...` | `CVHealingResult` | INTERNAL |
| `async _try_heuristic_healing` | SelectorHealingChain | `self, page: Page, selector: str, ...` | `Dict[str, Any]` | INTERNAL |
| `async _try_selector` | SelectorHealingChain | `self, page: Page, selector: str` | `Optional[Any]` | INTERNAL |
| `async capture_element_context` | SelectorHealingChain | `self, page: Page, selector: str` | `bool` | UNUSED |
| `export_report` | SelectorHealingChain | `self` | `Dict[str, Any]` | USED |
| `get_problematic_selectors` | SelectorHealingChain | `self, min_uses: int, max_success_rate: float` | `List[Any]` | USED |
| `get_stats` | SelectorHealingChain | `self` | `Dict[str, Any]` | USED |
| `get_tier_stats` | SelectorHealingChain | `self` | `Dict[str, Dict[str, Any]]` | USED |
| `healing_budget_ms` | SelectorHealingChain | `self` | `float` | UNUSED |
| `healing_budget_ms` | SelectorHealingChain | `self, value: float` | `None` | UNUSED |
| `async locate_element` | SelectorHealingChain | `self, page: Page, selector: str, ...` | `HealingChainResult` | UNUSED |


## casare_rpa.infrastructure.browser.healing.models

**File:** `src\casare_rpa\infrastructure\browser\healing\models.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `from_dict` | AnchorElement | `cls, data: Dict[str, Any]` | `AnchorElement` | USED |
| `is_stable` | AnchorElement | `self` | `bool` | UNUSED |
| `to_dict` | AnchorElement | `self` | `Dict[str, Any]` | USED |
| `to_dict` | AnchorHealingResult | `self` | `Dict[str, Any]` | USED |
| `bottom` | BoundingRect | `self` | `float` | USED |
| `center_x` | BoundingRect | `self` | `float` | UNUSED |
| `center_y` | BoundingRect | `self` | `float` | UNUSED |
| `distance_to` | BoundingRect | `self, other: BoundingRect` | `float` | UNUSED |
| `edge_distance_to` | BoundingRect | `self, other: BoundingRect` | `float` | UNUSED |
| `from_dict` | BoundingRect | `cls, data: Dict[str, float]` | `BoundingRect` | USED |
| `right` | BoundingRect | `self` | `float` | USED |
| `to_dict` | BoundingRect | `self` | `Dict[str, float]` | USED |
| `from_dict` | SpatialContext | `cls, data: Dict[str, Any]` | `SpatialContext` | USED |
| `get_best_anchor` | SpatialContext | `self` | `Optional[Tuple[AnchorElement, SpatialRelation, float]]` | UNUSED |
| `to_dict` | SpatialContext | `self` | `Dict[str, Any]` | USED |


## casare_rpa.infrastructure.browser.healing.telemetry

**File:** `src\casare_rpa\infrastructure\browser\healing\telemetry.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `get_healing_telemetry` | - | `storage_path: Optional[Path]` | `HealingTelemetry` | USED |
| `reset_healing_telemetry` | - | `` | `None` | UNUSED |
| `to_dict` | HealingEvent | `self` | `Dict[str, Any]` | USED |
| `__init__` | HealingTelemetry | `self, storage_path: Optional[Path], max_events: int, ...` | `None` | DUNDER |
| `_load` | HealingTelemetry | `self` | `None` | INTERNAL |
| `_update_stats` | HealingTelemetry | `self, event: HealingEvent` | `None` | INTERNAL |
| `cleanup_old_events` | HealingTelemetry | `self` | `int` | UNUSED |
| `export_report` | HealingTelemetry | `self` | `Dict[str, Any]` | USED |
| `get_overall_stats` | HealingTelemetry | `self` | `Dict[str, Any]` | USED |
| `get_problematic_selectors` | HealingTelemetry | `self, min_uses: int, max_success_rate: float` | `List[SelectorStats]` | USED |
| `get_recent_events` | HealingTelemetry | `self, limit: int, selector: Optional[str], ...` | `List[HealingEvent]` | USED |
| `get_selector_stats` | HealingTelemetry | `self, selector: str` | `Optional[SelectorStats]` | UNUSED |
| `get_tier_stats` | HealingTelemetry | `self` | `Dict[str, Dict[str, Any]]` | USED |
| `record_event` | HealingTelemetry | `self, selector: str, page_url: str, ...` | `HealingEvent` | USED |
| `reset` | HealingTelemetry | `self` | `None` | USED |
| `save` | HealingTelemetry | `self` | `None` | USED |
| `healing_rate` | SelectorStats | `self` | `float` | UNUSED |
| `healing_success_rate` | SelectorStats | `self` | `float` | UNUSED |
| `success_rate` | SelectorStats | `self` | `float` | UNUSED |
| `to_dict` | SelectorStats | `self` | `Dict[str, Any]` | USED |


## casare_rpa.infrastructure.config.cloudflare_config

**File:** `src\casare_rpa\infrastructure\config\cloudflare_config.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `from_env` | CloudflareConfig | `cls` | `'CloudflareConfig'` | USED |
| `is_production` | CloudflareConfig | `self` | `bool` | UNUSED |
| `is_secure` | CloudflareConfig | `self` | `bool` | UNUSED |
| `local` | CloudflareConfig | `cls` | `'CloudflareConfig'` | UNUSED |
| `production` | CloudflareConfig | `cls` | `'CloudflareConfig'` | UNUSED |


## casare_rpa.infrastructure.events.monitoring_events

**File:** `src\casare_rpa\infrastructure\events\monitoring_events.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `get_monitoring_event_bus` | - | `` | `MonitoringEventBus` | USED |
| `to_dict` | MonitoringEvent | `self` | `Dict` | USED |
| `__init__` | MonitoringEventBus | `self, max_history: int` | `-` | DUNDER |
| `__new__` | MonitoringEventBus | `cls` | `'MonitoringEventBus'` | DUNDER |
| `clear_all` | MonitoringEventBus | `self` | `None` | UNUSED |
| `get_history` | MonitoringEventBus | `self, limit: int` | `List[MonitoringEvent]` | USED |
| `get_instance` | MonitoringEventBus | `cls` | `'MonitoringEventBus'` | USED |
| `get_statistics` | MonitoringEventBus | `self` | `Dict` | USED |
| `async publish` | MonitoringEventBus | `self, event_type: MonitoringEventType, payload: Dict, ...` | `None` | USED |
| `subscribe` | MonitoringEventBus | `self, event_type: MonitoringEventType, handler: EventHandler` | `None` | USED |
| `unsubscribe` | MonitoringEventBus | `self, event_type: MonitoringEventType, handler: EventHandler` | `None` | USED |
| `async wrapped` | MonitoringEventBus | `h, e` | `-` | USED |


## casare_rpa.infrastructure.execution.dbos_executor

**File:** `src\casare_rpa\infrastructure\execution\dbos_executor.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `async start_durable_workflow` | - | `workflow: Any, workflow_id: str, initial_variables: Optional[Dict[str, Any]], ...` | `Dict[str, Any]` | UNUSED |
| `to_dict` | DBOSExecutorConfig | `self` | `Dict[str, Any]` | USED |
| `__init__` | DBOSWorkflowExecutor | `self, config: Optional[DBOSExecutorConfig], event_bus: Optional[EventBus]` | `None` | DUNDER |
| `_emit_event` | DBOSWorkflowExecutor | `self, event_type: EventType, data: Dict[str, Any]` | `None` | INTERNAL |
| `async _ensure_checkpoint_table` | DBOSWorkflowExecutor | `self` | `None` | INTERNAL |
| `async _load_checkpoint` | DBOSWorkflowExecutor | `self, workflow_id: str` | `Optional[ExecutionCheckpoint]` | INTERNAL |
| `async _save_checkpoint` | DBOSWorkflowExecutor | `self, checkpoint: ExecutionCheckpoint` | `None` | INTERNAL |
| `async clear_checkpoint` | DBOSWorkflowExecutor | `self, workflow_id: str` | `bool` | UNUSED |
| `async execute_workflow` | DBOSWorkflowExecutor | `self, workflow_json: str, workflow_id: str, ...` | `DurableExecutionResult` | USED |
| `on_node_complete` | DBOSWorkflowExecutor | `event: Event` | `None` | USED |
| `async start` | DBOSWorkflowExecutor | `self` | `None` | USED |
| `async stop` | DBOSWorkflowExecutor | `self` | `None` | USED |
| `from_dict` | ExecutionCheckpoint | `cls, data: Dict[str, Any]` | `'ExecutionCheckpoint'` | USED |
| `to_dict` | ExecutionCheckpoint | `self` | `Dict[str, Any]` | USED |


## casare_rpa.infrastructure.execution.debug_executor

**File:** `src\casare_rpa\infrastructure\execution\debug_executor.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | DebugExecutor | `self, workflow: 'WorkflowSchema', context: 'ExecutionContext', ...` | `None` | DUNDER |
| `async _execute_from_node` | DebugExecutor | `self, start_node_id: NodeId` | `None` | INTERNAL |
| `async _execute_node` | DebugExecutor | `self, node: Any, node_id: NodeId` | `tuple[bool, Optional[Dict[str, Any]]]` | INTERNAL |
| `_find_start_node` | DebugExecutor | `self` | `Optional[NodeId]` | INTERNAL |
| `async _pause_checkpoint` | DebugExecutor | `self` | `None` | INTERNAL |
| `_transfer_input_data` | DebugExecutor | `self, node_id: NodeId, orchestrator: Any` | `None` | INTERNAL |
| `cleanup` | DebugExecutor | `self` | `None` | USED |
| `async execute` | DebugExecutor | `self` | `bool` | USED |
| `get_current_record` | DebugExecutor | `self` | `Optional[NodeExecutionRecord]` | UNUSED |
| `get_execution_records` | DebugExecutor | `self` | `List[NodeExecutionRecord]` | UNUSED |
| `get_execution_summary` | DebugExecutor | `self` | `Dict[str, Any]` | USED |
| `get_node_execution_info` | DebugExecutor | `self, node_id: str` | `Optional[NodeExecutionRecord]` | UNUSED |
| `get_variable_history` | DebugExecutor | `self, variable_name: str` | `List[tuple[str, Any]]` | UNUSED |
| `pause` | DebugExecutor | `self` | `None` | USED |
| `resume` | DebugExecutor | `self` | `None` | USED |
| `session` | DebugExecutor | `self` | `Optional[DebugSession]` | UNUSED |
| `state` | DebugExecutor | `self` | `DebugState` | UNUSED |
| `stop` | DebugExecutor | `self` | `None` | USED |


## casare_rpa.infrastructure.execution.execution_context

**File:** `src\casare_rpa\infrastructure\execution\execution_context.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `async __aenter__` | ExecutionContext | `self` | `'ExecutionContext'` | DUNDER |
| `async __aexit__` | ExecutionContext | `self, exc_type: Any, exc_val: Any, ...` | `bool` | DUNDER |
| `__enter__` | ExecutionContext | `self` | `'ExecutionContext'` | DUNDER |
| `__exit__` | ExecutionContext | `self, exc_type: Any, exc_val: Any, ...` | `bool` | DUNDER |
| `__init__` | ExecutionContext | `self, workflow_name: str, mode: ExecutionMode, ...` | `None` | DUNDER |
| `__repr__` | ExecutionContext | `self` | `str` | DUNDER |
| `active_page` | ExecutionContext | `self` | `Optional['Page']` | UNUSED |
| `active_page` | ExecutionContext | `self, value: Optional['Page']` | `None` | UNUSED |
| `add_browser_context` | ExecutionContext | `self, context: 'BrowserContext'` | `None` | USED |
| `add_error` | ExecutionContext | `self, node_id: NodeId, error_message: str` | `None` | USED |
| `add_page` | ExecutionContext | `self, page: 'Page', name: str` | `None` | USED |
| `browser` | ExecutionContext | `self` | `Optional['Browser']` | UNUSED |
| `browser` | ExecutionContext | `self, value: Optional['Browser']` | `None` | UNUSED |
| `browser_contexts` | ExecutionContext | `self` | `List['BrowserContext']` | UNUSED |
| `async cleanup` | ExecutionContext | `self` | `None` | USED |
| `clear_pages` | ExecutionContext | `self` | `None` | USED |
| `clear_variables` | ExecutionContext | `self` | `None` | USED |
| `clone_for_branch` | ExecutionContext | `self, branch_name: str` | `'ExecutionContext'` | USED |
| `close_page` | ExecutionContext | `self, name: str` | `None` | USED |
| `completed_at` | ExecutionContext | `self` | `Optional[datetime]` | UNUSED |
| `create_workflow_context` | ExecutionContext | `self, workflow_name: str` | `'ExecutionContext'` | USED |
| `current_node_id` | ExecutionContext | `self` | `Optional[NodeId]` | UNUSED |
| `delete_variable` | ExecutionContext | `self, name: str` | `None` | USED |
| `errors` | ExecutionContext | `self` | `List[tuple[NodeId, str]]` | USED |
| `execution_path` | ExecutionContext | `self` | `List[NodeId]` | UNUSED |
| `get_active_page` | ExecutionContext | `self` | `Optional['Page']` | USED |
| `get_browser` | ExecutionContext | `self` | `Optional['Browser']` | USED |
| `async get_credential_provider` | ExecutionContext | `self` | `Optional['VaultCredentialProvider']` | USED |
| `get_execution_summary` | ExecutionContext | `self` | `Dict[str, Any]` | USED |
| `get_page` | ExecutionContext | `self, name: str` | `Optional['Page']` | USED |
| `get_variable` | ExecutionContext | `self, name: str, default: Any` | `Any` | USED |
| `has_project_context` | ExecutionContext | `self` | `bool` | UNUSED |
| `has_variable` | ExecutionContext | `self, name: str` | `bool` | USED |
| `is_stopped` | ExecutionContext | `self` | `bool` | USED |
| `mark_completed` | ExecutionContext | `self` | `None` | USED |
| `merge_branch_results` | ExecutionContext | `self, branch_name: str, branch_variables: Dict[str, Any]` | `None` | USED |
| `mode` | ExecutionContext | `self` | `ExecutionMode` | UNUSED |
| `pages` | ExecutionContext | `self` | `Dict[str, 'Page']` | UNUSED |
| `async pause_checkpoint` | ExecutionContext | `self` | `None` | USED |
| `project_context` | ExecutionContext | `self` | `Optional['ProjectContext']` | UNUSED |
| `async resolve_credential` | ExecutionContext | `self, alias: str, required: bool` | `Optional[Any]` | USED |
| `resolve_credential_path` | ExecutionContext | `self, alias: str` | `Optional[str]` | USED |
| `resolve_value` | ExecutionContext | `self, value: Any` | `Any` | USED |
| `set_active_page` | ExecutionContext | `self, page: 'Page', name: str` | `None` | USED |
| `set_browser` | ExecutionContext | `self, browser: 'Browser'` | `None` | USED |
| `set_current_node` | ExecutionContext | `self, node_id: NodeId` | `None` | USED |
| `set_variable` | ExecutionContext | `self, name: str, value: Any` | `None` | USED |
| `started_at` | ExecutionContext | `self` | `datetime` | UNUSED |
| `stop_execution` | ExecutionContext | `self` | `None` | USED |
| `stopped` | ExecutionContext | `self` | `bool` | UNUSED |
| `variables` | ExecutionContext | `self` | `Dict[str, Any]` | UNUSED |
| `workflow_name` | ExecutionContext | `self` | `str` | UNUSED |


## casare_rpa.infrastructure.execution.recovery_strategies

**File:** `src\casare_rpa\infrastructure\execution\recovery_strategies.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_on_create_registry` | - | `instance: RecoveryStrategyRegistry` | `None` | INTERNAL |
| `get_recovery_strategy_registry` | - | `` | `RecoveryStrategyRegistry` | USED |
| `reset_recovery_strategy_registry` | - | `` | `None` | UNUSED |
| `action` | AbortStrategy | `self` | `RecoveryAction` | USED |
| `async execute` | AbortStrategy | `self, context: ErrorContext, decision: RecoveryDecision, ...` | `bool` | USED |
| `__init__` | CircuitBreaker | `self, name: str, config: Optional[CircuitBreakerConfig]` | `None` | DUNDER |
| `_transition_to_closed` | CircuitBreaker | `self` | `None` | INTERNAL |
| `_transition_to_half_open` | CircuitBreaker | `self` | `None` | INTERNAL |
| `_transition_to_open` | CircuitBreaker | `self` | `None` | INTERNAL |
| `get_state` | CircuitBreaker | `self` | `Dict[str, Any]` | USED |
| `is_half_open` | CircuitBreaker | `self` | `bool` | UNUSED |
| `is_open` | CircuitBreaker | `self` | `bool` | UNUSED |
| `record_failure` | CircuitBreaker | `self, error_type: Optional[str]` | `None` | USED |
| `record_success` | CircuitBreaker | `self` | `None` | USED |
| `reset` | CircuitBreaker | `self` | `None` | USED |
| `__init__` | CompensateStrategy | `self, config: Optional[CompensateConfig], compensator_func: Optional[Callable[..., Any]]` | `None` | DUNDER |
| `action` | CompensateStrategy | `self` | `RecoveryAction` | USED |
| `async execute` | CompensateStrategy | `self, context: ErrorContext, decision: RecoveryDecision, ...` | `bool` | USED |
| `__init__` | EscalateStrategy | `self, config: Optional[EscalateConfig]` | `None` | DUNDER |
| `action` | EscalateStrategy | `self` | `RecoveryAction` | USED |
| `async execute` | EscalateStrategy | `self, context: ErrorContext, decision: RecoveryDecision, ...` | `bool` | USED |
| `resolve_escalation` | EscalateStrategy | `self, escalation_id: str, action: RecoveryAction` | `bool` | UNUSED |
| `__init__` | FallbackStrategy | `self, config: Optional[FallbackConfig]` | `None` | DUNDER |
| `action` | FallbackStrategy | `self` | `RecoveryAction` | USED |
| `async execute` | FallbackStrategy | `self, context: ErrorContext, decision: RecoveryDecision, ...` | `bool` | USED |
| `action` | RecoveryStrategy | `self` | `RecoveryAction` | USED |
| `async execute` | RecoveryStrategy | `self, context: ErrorContext, decision: RecoveryDecision, ...` | `bool` | USED |
| `__init__` | RecoveryStrategyRegistry | `self` | `None` | DUNDER |
| `_register_defaults` | RecoveryStrategyRegistry | `self` | `None` | INTERNAL |
| `async execute_recovery` | RecoveryStrategyRegistry | `self, context: ErrorContext, decision: RecoveryDecision, ...` | `bool` | USED |
| `get_circuit_breaker` | RecoveryStrategyRegistry | `self, name: str` | `Optional[CircuitBreaker]` | UNUSED |
| `get_or_create_circuit_breaker` | RecoveryStrategyRegistry | `self, name: str, config: Optional[CircuitBreakerConfig]` | `CircuitBreaker` | UNUSED |
| `get_strategy` | RecoveryStrategyRegistry | `self, action: RecoveryAction` | `Optional[RecoveryStrategy]` | USED |
| `register_strategy` | RecoveryStrategyRegistry | `self, action: RecoveryAction, strategy: RecoveryStrategy` | `None` | UNUSED |
| `screenshot_capture` | RecoveryStrategyRegistry | `self` | `ScreenshotCapture` | UNUSED |
| `__init__` | RetryStrategy | `self, config: Optional[RetryConfig], circuit_breaker: Optional[CircuitBreaker]` | `None` | DUNDER |
| `_calculate_delay` | RetryStrategy | `self, retry_count: int` | `int` | INTERNAL |
| `action` | RetryStrategy | `self` | `RecoveryAction` | USED |
| `async execute` | RetryStrategy | `self, context: ErrorContext, decision: RecoveryDecision, ...` | `bool` | USED |
| `__init__` | ScreenshotCapture | `self, output_dir: Optional[Path], max_screenshots: int` | `None` | DUNDER |
| `_cleanup_old_screenshots` | ScreenshotCapture | `self` | `None` | INTERNAL |
| `async capture_browser_screenshot` | ScreenshotCapture | `self, context: ErrorContext, execution_context: 'ExecutionContext'` | `Optional[str]` | USED |
| `capture_desktop_screenshot` | ScreenshotCapture | `self, context: ErrorContext` | `Optional[str]` | USED |
| `async capture_for_context` | ScreenshotCapture | `self, context: ErrorContext, execution_context: 'ExecutionContext'` | `Optional[str]` | USED |
| `action` | SkipStrategy | `self` | `RecoveryAction` | USED |
| `async execute` | SkipStrategy | `self, context: ErrorContext, decision: RecoveryDecision, ...` | `bool` | USED |


## casare_rpa.infrastructure.logging.log_cleanup

**File:** `src\casare_rpa\infrastructure\logging\log_cleanup.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `get_log_cleanup_job` | - | `` | `LogCleanupJob` | USED |
| `async init_log_cleanup_job` | - | `retention_days: int, auto_start: bool` | `LogCleanupJob` | UNUSED |
| `__init__` | LogCleanupJob | `self, log_repository: Optional[LogRepository], retention_days: int, ...` | `None` | DUNDER |
| `async _scheduler_loop` | LogCleanupJob | `self` | `None` | INTERNAL |
| `get_status` | LogCleanupJob | `self` | `Dict[str, Any]` | USED |
| `retention_days` | LogCleanupJob | `self` | `int` | UNUSED |
| `retention_days` | LogCleanupJob | `self, value: int` | `None` | UNUSED |
| `async run_cleanup` | LogCleanupJob | `self` | `Dict[str, Any]` | USED |
| `async start` | LogCleanupJob | `self` | `None` | USED |
| `async stop` | LogCleanupJob | `self` | `None` | USED |


## casare_rpa.infrastructure.logging.log_streaming_service

**File:** `src\casare_rpa\infrastructure\logging\log_streaming_service.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_create_log_streaming_service` | - | `` | `LogStreamingService` | INTERNAL |
| `get_log_streaming_service` | - | `` | `LogStreamingService` | USED |
| `async init_log_streaming_service` | - | `log_repository: Optional[LogRepository]` | `LogStreamingService` | UNUSED |
| `reset_log_streaming_service` | - | `` | `None` | UNUSED |
| `__init__` | LogStreamingService | `self, log_repository: Optional[LogRepository], persist_logs: bool, ...` | `None` | DUNDER |
| `async _broadcast_logs` | LogStreamingService | `self, robot_id: str, tenant_id: str, ...` | `None` | INTERNAL |
| `async _flush_persist_queue` | LogStreamingService | `self` | `None` | INTERNAL |
| `async _persist_batch` | LogStreamingService | `self, entries: List[LogEntry]` | `None` | INTERNAL |
| `async _persist_worker` | LogStreamingService | `self` | `None` | INTERNAL |
| `async _send_to_subscriber` | LogStreamingService | `self, websocket: Any, robot_id: str, ...` | `None` | INTERNAL |
| `buffer_log` | LogStreamingService | `self, robot_id: str, entry: LogEntry` | `None` | UNUSED |
| `get_buffered_logs` | LogStreamingService | `self, robot_id: str` | `List[LogEntry]` | UNUSED |
| `get_metrics` | LogStreamingService | `self` | `Dict[str, Any]` | USED |
| `get_subscriber_count` | LogStreamingService | `self` | `int` | UNUSED |
| `async receive_log_batch` | LogStreamingService | `self, robot_id: str, batch_data: Dict[str, Any], ...` | `int` | USED |
| `async receive_single_log` | LogStreamingService | `self, robot_id: str, tenant_id: str, ...` | `None` | UNUSED |
| `async start` | LogStreamingService | `self` | `None` | USED |
| `async stop` | LogStreamingService | `self` | `None` | USED |
| `async subscribe` | LogStreamingService | `self, websocket: Any, robot_ids: Optional[List[str]], ...` | `None` | USED |
| `async unsubscribe` | LogStreamingService | `self, websocket: Any` | `None` | USED |


## casare_rpa.infrastructure.observability.facade

**File:** `src\casare_rpa\infrastructure\observability\facade.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_deprecated_import_warning` | - | `old_name: str, new_name: str` | `None` | INTERNAL |
| `configure_observability` | - | `environment: Optional[str], robot_id: Optional[str], tenant_id: Optional[str]` | `None` | UNUSED |
| `_get_standard_labels` | Observability | `cls` | `Dict[str, str]` | INTERNAL |
| `capture_stdout` | Observability | `cls, stdout_callback: Optional[Callable[[str], None]], stderr_callback: Optional[Callable[[str], None]]` | `None` | UNUSED |
| `captured_output` | Observability | `cls, stdout_callback: Optional[Callable[[str], None]], stderr_callback: Optional[Callable[[str], None]]` | `Generator[None, None, None]` | UNUSED |
| `configure` | Observability | `cls, config: Optional[ObservabilityConfig], force_reinit: bool` | `None` | USED |
| `debug` | Observability | `cls, message: str` | `None` | USED |
| `error` | Observability | `cls, message: str` | `None` | USED |
| `gauge` | Observability | `cls, name: str, value: float, ...` | `None` | UNUSED |
| `get_config` | Observability | `cls` | `Optional[ObservabilityConfig]` | USED |
| `get_meter` | Observability | `cls, name: str` | `Optional[Any]` | USED |
| `get_metrics_collector` | Observability | `cls` | `Optional[RPAMetricsCollector]` | USED |
| `get_system_metrics` | Observability | `cls` | `Dict[str, Any]` | USED |
| `get_tracer` | Observability | `cls, name: str` | `Optional[Any]` | USED |
| `increment` | Observability | `cls, name: str, labels: Optional[Dict[str, str]], ...` | `None` | USED |
| `info` | Observability | `cls, message: str` | `None` | USED |
| `is_configured` | Observability | `cls` | `bool` | UNUSED |
| `log` | Observability | `cls, level: str, message: str` | `None` | USED |
| `metric` | Observability | `cls, name: str, value: float, ...` | `None` | USED |
| `shutdown` | Observability | `cls` | `None` | USED |
| `stop_stdout_capture` | Observability | `cls` | `None` | USED |
| `trace` | Observability | `cls, name: str, attributes: Optional[Dict[str, Any]], ...` | `Generator[Optional[Any], None, None]` | UNUSED |
| `warning` | Observability | `cls, message: str` | `None` | USED |
| `to_telemetry_config` | ObservabilityConfig | `self` | `TelemetryConfig` | USED |


## casare_rpa.infrastructure.observability.logging

**File:** `src\casare_rpa\infrastructure\observability\logging.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_cleanup_on_exit` | - | `` | `None` | INTERNAL |
| `configure_logging` | - | `enable_otel_export: bool, enable_trace_context: bool, console_format: Optional[str], ...` | `None` | USED |
| `create_trace_context_format` | - | `` | `str` | USED |
| `get_span_logger` | - | `name: str` | `SpanLogger` | UNUSED |
| `get_ui_log_sink` | - | `` | `Optional[UILoguruSink]` | UNUSED |
| `log_with_trace` | - | `message: str, level: str` | `None` | UNUSED |
| `remove_ui_log_callback` | - | `` | `None` | USED |
| `set_ui_log_callback` | - | `callback: Callable[[str, str, str, str], None], min_level: str` | `None` | USED |
| `trace_context_patcher` | - | `record: Dict[str, Any]` | `None` | UNUSED |
| `__call__` | OTelLoguruSink | `self, message: Any` | `None` | DUNDER |
| `__init__` | OTelLoguruSink | `self` | `None` | DUNDER |
| `_ensure_initialized` | OTelLoguruSink | `self` | `bool` | INTERNAL |
| `__init__` | SpanLogger | `self, name: str` | `None` | DUNDER |
| `_log_with_span` | SpanLogger | `self, level: str, message: str` | `None` | INTERNAL |
| `debug` | SpanLogger | `self, message: str` | `None` | USED |
| `error` | SpanLogger | `self, message: str` | `None` | USED |
| `exception` | SpanLogger | `self, message: str, exc: Optional[Exception]` | `None` | USED |
| `info` | SpanLogger | `self, message: str` | `None` | USED |
| `warning` | SpanLogger | `self, message: str` | `None` | USED |
| `__call__` | UILoguruSink | `self, message: Any` | `None` | DUNDER |
| `__init__` | UILoguruSink | `self, callback: Callable[[str, str, str, str], None], min_level: str` | `None` | DUNDER |


## casare_rpa.infrastructure.observability.metrics

**File:** `src\casare_rpa\infrastructure\observability\metrics.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `get_metrics_collector` | - | `` | `RPAMetricsCollector` | USED |
| `get_metrics_exporter` | - | `interval_seconds: float, environment: str` | `MetricsExporter` | USED |
| `average_duration_seconds` | JobMetrics | `self` | `float` | UNUSED |
| `average_queue_wait_seconds` | JobMetrics | `self` | `float` | UNUSED |
| `success_rate` | JobMetrics | `self` | `float` | UNUSED |
| `__init__` | MetricsExporter | `self, interval_seconds: float, environment: str` | `None` | DUNDER |
| `async _export_loop` | MetricsExporter | `self` | `None` | INTERNAL |
| `async _export_once` | MetricsExporter | `self` | `None` | INTERNAL |
| `add_dict_callback` | MetricsExporter | `self, callback: Callable[[Dict[str, Any]], None]` | `None` | UNUSED |
| `add_json_callback` | MetricsExporter | `self, callback: Callable[[str], None]` | `None` | UNUSED |
| `add_prometheus_callback` | MetricsExporter | `self, callback: Callable[[str], None]` | `None` | UNUSED |
| `get_last_snapshot` | MetricsExporter | `self` | `Optional[MetricsSnapshot]` | UNUSED |
| `get_prometheus_format` | MetricsExporter | `self` | `str` | USED |
| `get_snapshot_dict` | MetricsExporter | `self` | `Dict[str, Any]` | UNUSED |
| `get_snapshot_json` | MetricsExporter | `self` | `str` | UNUSED |
| `remove_callback` | MetricsExporter | `self, callback: Callable` | `None` | USED |
| `async start` | MetricsExporter | `self` | `None` | USED |
| `async stop` | MetricsExporter | `self` | `None` | USED |
| `from_collector` | MetricsSnapshot | `cls, collector: RPAMetricsCollector, environment: str` | `'MetricsSnapshot'` | USED |
| `to_dict` | MetricsSnapshot | `self` | `Dict[str, Any]` | USED |
| `to_json` | MetricsSnapshot | `self` | `str` | USED |
| `__init__` | RPAMetricsCollector | `self, emit_events: bool` | `None` | DUNDER |
| `__new__` | RPAMetricsCollector | `cls` | `'RPAMetricsCollector'` | DUNDER |
| `_emit_monitoring_event` | RPAMetricsCollector | `self, event_type: MonitoringEventType, payload: Dict[str, Any]` | `None` | INTERNAL |
| `_init_instruments` | RPAMetricsCollector | `self` | `None` | INTERNAL |
| `_record_node_metrics` | RPAMetricsCollector | `self, node_type: str, node_id: str, ...` | `None` | INTERNAL |
| `_update_global_utilization` | RPAMetricsCollector | `self` | `None` | INTERNAL |
| `_update_robot_status` | RPAMetricsCollector | `self, robot_id: str, status: RobotStatus, ...` | `None` | INTERNAL |
| `active_jobs_callback` | RPAMetricsCollector | `options: Any` | `Generator[Any, None, None]` | UNUSED |
| `get_active_jobs` | RPAMetricsCollector | `self` | `Dict[str, Dict[str, Any]]` | USED |
| `get_all_node_metrics` | RPAMetricsCollector | `self` | `Dict[str, Dict[str, Any]]` | USED |
| `get_all_robot_metrics` | RPAMetricsCollector | `self` | `Dict[str, RobotMetrics]` | USED |
| `get_healing_stats` | RPAMetricsCollector | `self` | `Dict[str, Any]` | USED |
| `get_instance` | RPAMetricsCollector | `cls` | `'RPAMetricsCollector'` | USED |
| `get_job_metrics` | RPAMetricsCollector | `self` | `JobMetrics` | USED |
| `get_node_metrics` | RPAMetricsCollector | `self, node_type: str` | `Optional[Dict[str, Any]]` | UNUSED |
| `get_queue_depth` | RPAMetricsCollector | `self` | `int` | USED |
| `get_robot_metrics` | RPAMetricsCollector | `self, robot_id: str` | `Optional[RobotMetrics]` | USED |
| `queue_throughput_callback` | RPAMetricsCollector | `options: Any` | `Generator[Any, None, None]` | UNUSED |
| `record_browser_acquired` | RPAMetricsCollector | `self` | `None` | UNUSED |
| `record_browser_released` | RPAMetricsCollector | `self` | `None` | UNUSED |
| `record_healing_attempt` | RPAMetricsCollector | `self, selector: str, healing_strategy: str, ...` | `None` | UNUSED |
| `record_job_cancel` | RPAMetricsCollector | `self, job_id: str, reason: str` | `None` | UNUSED |
| `record_job_complete` | RPAMetricsCollector | `self, job_id: str, success: bool, ...` | `None` | UNUSED |
| `record_job_enqueue` | RPAMetricsCollector | `self, job_id: str, workflow_name: str, ...` | `None` | UNUSED |
| `record_job_retry` | RPAMetricsCollector | `self, job_id: str, attempt_number: int, ...` | `None` | UNUSED |
| `record_job_start` | RPAMetricsCollector | `self, job_id: str, robot_id: Optional[str]` | `None` | UNUSED |
| `register_robot` | RPAMetricsCollector | `self, robot_id: str` | `None` | USED |
| `reset_metrics` | RPAMetricsCollector | `self` | `None` | UNUSED |
| `track_node_execution` | RPAMetricsCollector | `self, node_type: str, node_id: str` | `Generator[None, None, None]` | UNUSED |
| `unregister_robot` | RPAMetricsCollector | `self, robot_id: str` | `None` | USED |
| `success_rate` | RobotMetrics | `self` | `float` | UNUSED |
| `utilization_percent` | RobotMetrics | `self` | `float` | UNUSED |


## casare_rpa.infrastructure.observability.stdout_capture

**File:** `src\casare_rpa\infrastructure\observability\stdout_capture.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_cleanup_on_exit` | - | `` | `None` | INTERNAL |
| `capture_output` | - | `stdout_callback: Optional[Callable[[str], None]], stderr_callback: Optional[Callable[[str], None]]` | `-` | USED |
| `get_output_capture` | - | `` | `Optional[OutputCapture]` | UNUSED |
| `remove_output_callbacks` | - | `` | `None` | USED |
| `set_output_callbacks` | - | `stdout_callback: Optional[Callable[[str], None]], stderr_callback: Optional[Callable[[str], None]]` | `None` | USED |
| `__enter__` | OutputCapture | `self` | `'OutputCapture'` | DUNDER |
| `__exit__` | OutputCapture | `self, exc_type, exc_val, ...` | `None` | DUNDER |
| `__init__` | OutputCapture | `self, stdout_callback: Optional[Callable[[str], None]], stderr_callback: Optional[Callable[[str], None]]` | `-` | DUNDER |
| `start` | OutputCapture | `self` | `None` | USED |
| `stop` | OutputCapture | `self` | `None` | USED |
| `__init__` | _CallbackWriter | `self, original: TextIO, callback: Optional[Callable[[str], None]]` | `-` | DUNDER |
| `encoding` | _CallbackWriter | `self` | `str` | UNUSED |
| `errors` | _CallbackWriter | `self` | `Optional[str]` | USED |
| `fileno` | _CallbackWriter | `self` | `int` | USED |
| `flush` | _CallbackWriter | `self` | `None` | USED |
| `isatty` | _CallbackWriter | `self` | `bool` | USED |
| `write` | _CallbackWriter | `self, text: str` | `int` | USED |


## casare_rpa.infrastructure.observability.system_metrics

**File:** `src\casare_rpa\infrastructure\observability\system_metrics.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `get_cpu_percent` | - | `` | `float` | USED |
| `get_memory_mb` | - | `` | `float` | USED |
| `get_system_metrics_collector` | - | `` | `SystemMetricsCollector` | USED |
| `__init__` | SystemMetricsCollector | `self` | `None` | DUNDER |
| `__new__` | SystemMetricsCollector | `cls` | `'SystemMetricsCollector'` | DUNDER |
| `get_cpu_percent` | SystemMetricsCollector | `self` | `float` | USED |
| `get_instance` | SystemMetricsCollector | `cls` | `'SystemMetricsCollector'` | USED |
| `get_memory_mb` | SystemMetricsCollector | `self` | `float` | USED |
| `get_process_metrics` | SystemMetricsCollector | `self` | `ProcessMetrics` | USED |
| `get_system_metrics` | SystemMetricsCollector | `self` | `SystemMetrics` | USED |


## casare_rpa.infrastructure.observability.telemetry

**File:** `src\casare_rpa\infrastructure\observability\telemetry.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_extract_class_name` | - | `args: tuple[Any, ...]` | `str` | INTERNAL |
| `_extract_node_count` | - | `result: Any` | `int` | INTERNAL |
| `_extract_node_id` | - | `args: tuple[Any, ...], kwargs: Dict[str, Any]` | `Optional[str]` | INTERNAL |
| `async async_wrapper` | - | `` | `T` | UNUSED |
| `async async_wrapper` | - | `` | `T` | UNUSED |
| `decorator` | - | `func: Callable[P, T]` | `Callable[P, T]` | UNUSED |
| `decorator` | - | `func: Callable[P, T]` | `Callable[P, T]` | UNUSED |
| `decorator` | - | `func: Callable[P, T]` | `Callable[P, T]` | UNUSED |
| `extract_context_from_headers` | - | `headers: Dict[str, str]` | `Optional[Context]` | UNUSED |
| `get_current_span` | - | `context: Any` | `Any` | USED |
| `get_logger_provider` | - | `` | `Optional[Any]` | USED |
| `get_meter` | - | `name: str, version: str` | `Optional[Any]` | USED |
| `get_tracer` | - | `name: str, version: str` | `Optional[Any]` | USED |
| `inject_context_to_headers` | - | `headers: Dict[str, str]` | `Dict[str, str]` | UNUSED |
| `otel_context_patcher` | - | `record: Any` | `None` | UNUSED |
| `record_job_duration` | - | `duration_seconds: float, workflow_name: str, job_id: str, ...` | `None` | USED |
| `record_queue_depth` | - | `depth: int` | `None` | UNUSED |
| `record_robot_utilization` | - | `utilization_percent: float, active_robots: int` | `None` | UNUSED |
| `set_span_in_context` | - | `span: Any, context: Any` | `Any` | USED |
| `setup_loguru_otel_sink` | - | `` | `None` | UNUSED |
| `sync_wrapper` | - | `` | `T` | UNUSED |
| `sync_wrapper` | - | `` | `T` | UNUSED |
| `trace_async` | - | `name: Optional[str], kind: Optional[Any], attributes: Optional[Dict[str, Any]], ...` | `Callable[[Callable[P, T]], Callable[P, T]]` | UNUSED |
| `trace_node` | - | `node_type: Optional[str], attributes: Optional[Dict[str, Any]]` | `Callable[[Callable[P, T]], Callable[P, T]]` | UNUSED |
| `trace_workflow` | - | `workflow_name: Optional[str], attributes: Optional[Dict[str, Any]]` | `Callable[[Callable[P, T]], Callable[P, T]]` | UNUSED |
| `async wrapper` | - | `` | `T` | UNUSED |
| `async __aenter__` | DBOSSpanContext | `self` | `'DBOSSpanContext'` | DUNDER |
| `async __aexit__` | DBOSSpanContext | `self, exc_type: Optional[type], exc_val: Optional[BaseException], ...` | `bool` | DUNDER |
| `__init__` | DBOSSpanContext | `self, workflow_id: str, workflow_name: str, ...` | `None` | DUNDER |
| `create_step_span` | DBOSSpanContext | `self, step_name: str` | `Optional[Any]` | UNUSED |
| `set_result` | DBOSSpanContext | `self, result: Dict[str, Any]` | `None` | USED |
| `__init__` | Status | `self, code: Any, description: str` | `None` | DUNDER |
| `to_resource_attributes` | TelemetryConfig | `self` | `Dict[str, str]` | USED |
| `__init__` | TelemetryProvider | `self` | `None` | DUNDER |
| `__new__` | TelemetryProvider | `cls` | `'TelemetryProvider'` | DUNDER |
| `_create_log_exporter` | TelemetryProvider | `self` | `Optional[Any]` | INTERNAL |
| `_create_metric_exporter` | TelemetryProvider | `self` | `Optional[Any]` | INTERNAL |
| `_create_span_exporter` | TelemetryProvider | `self` | `Optional[SpanExporter]` | INTERNAL |
| `_init_logger_provider` | TelemetryProvider | `self` | `None` | INTERNAL |
| `_init_meter_provider` | TelemetryProvider | `self` | `None` | INTERNAL |
| `_init_metrics_instruments` | TelemetryProvider | `self` | `None` | INTERNAL |
| `_init_tracer_provider` | TelemetryProvider | `self` | `None` | INTERNAL |
| `get_instance` | TelemetryProvider | `cls` | `'TelemetryProvider'` | USED |
| `get_logger_provider` | TelemetryProvider | `self` | `Optional[Any]` | USED |
| `get_meter` | TelemetryProvider | `self, name: str, version: str` | `Optional[Any]` | USED |
| `get_tracer` | TelemetryProvider | `self, name: str, version: str` | `Optional[Any]` | USED |
| `initialize` | TelemetryProvider | `self, config: Optional[TelemetryConfig], force_reinit: bool` | `None` | USED |
| `queue_depth_callback` | TelemetryProvider | `options: Any` | `Generator[Any, None, None]` | UNUSED |
| `record_error` | TelemetryProvider | `self, error_type: str, component: str, ...` | `None` | USED |
| `record_job_duration` | TelemetryProvider | `self, duration_seconds: float, workflow_name: str, ...` | `None` | USED |
| `record_node_execution` | TelemetryProvider | `self, node_type: str, node_id: str, ...` | `None` | USED |
| `record_workflow_execution` | TelemetryProvider | `self, workflow_name: str, success: bool, ...` | `None` | USED |
| `robot_utilization_callback` | TelemetryProvider | `options: Any` | `Generator[Any, None, None]` | UNUSED |
| `shutdown` | TelemetryProvider | `self` | `None` | USED |
| `span` | TelemetryProvider | `self, name: str, kind: Optional[Any], ...` | `Generator[Optional[Span], None, None]` | USED |
| `update_queue_depth` | TelemetryProvider | `self, depth: int` | `None` | USED |
| `update_robot_utilization` | TelemetryProvider | `self, utilization_percent: float, active_robots: int` | `None` | USED |


## casare_rpa.infrastructure.orchestrator.api.adapters

**File:** `src\casare_rpa\infrastructure\orchestrator\api\adapters.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | MonitoringDataAdapter | `self, metrics_collector: RPAMetricsCollector, analytics_aggregator: MetricsAggregator, ...` | `-` | DUNDER |
| `async _query_job_activity_events` | MonitoringDataAdapter | `self, conn: Any, limit: int, ...` | `List[Dict[str, Any]]` | INTERNAL |
| `async _query_job_details` | MonitoringDataAdapter | `self, conn: Any, job_id: str` | `Optional[Dict[str, Any]]` | INTERNAL |
| `async _query_job_history` | MonitoringDataAdapter | `self, conn: Any, limit: int, ...` | `List[Dict[str, Any]]` | INTERNAL |
| `async _query_robot_activity_events` | MonitoringDataAdapter | `self, conn: Any, limit: int, ...` | `List[Dict[str, Any]]` | INTERNAL |
| `_row_to_job_summary` | MonitoringDataAdapter | `self, row: Any` | `Dict[str, Any]` | INTERNAL |
| `async get_activity_events_async` | MonitoringDataAdapter | `self, limit: int, since: Optional[datetime], ...` | `Dict[str, Any]` | USED |
| `get_analytics` | MonitoringDataAdapter | `self` | `Dict` | USED |
| `async get_analytics_async` | MonitoringDataAdapter | `self, days: int` | `Dict[str, Any]` | USED |
| `get_fleet_summary` | MonitoringDataAdapter | `self` | `Dict` | USED |
| `async get_fleet_summary_async` | MonitoringDataAdapter | `self` | `Dict` | USED |
| `get_job_details` | MonitoringDataAdapter | `self, job_id: str` | `Optional[Dict]` | UNUSED |
| `async get_job_details_async` | MonitoringDataAdapter | `self, job_id: str` | `Optional[Dict[str, Any]]` | USED |
| `async get_job_history` | MonitoringDataAdapter | `self, limit: int, status: Optional[str], ...` | `List[Dict[str, Any]]` | USED |
| `get_robot_details` | MonitoringDataAdapter | `self, robot_id: str` | `Optional[Dict]` | USED |
| `get_robot_list` | MonitoringDataAdapter | `self, status: Optional[str]` | `List[Dict]` | USED |
| `async get_robot_list_async` | MonitoringDataAdapter | `self, status: Optional[str]` | `List[Dict]` | USED |
| `has_db` | MonitoringDataAdapter | `self` | `bool` | UNUSED |


## casare_rpa.infrastructure.orchestrator.api.auth

**File:** `src\casare_rpa\infrastructure\orchestrator\api\auth.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_check_tenant` | - | `user: AuthenticatedUser` | `None` | INTERNAL |
| `_require_tenant` | - | `user: AuthenticatedUser` | `str` | INTERNAL |
| `configure_robot_authenticator` | - | `use_database: bool, db_pool` | `RobotAuthenticator` | UNUSED |
| `create_access_token` | - | `user_id: str, roles: list[str], tenant_id: Optional[str], ...` | `str` | USED |
| `create_refresh_token` | - | `user_id: str, tenant_id: Optional[str], expires_delta: Optional[timedelta]` | `str` | USED |
| `decode_token` | - | `token: str` | `TokenPayload` | USED |
| `async get_current_user` | - | `user: AuthenticatedUser` | `AuthenticatedUser` | UNUSED |
| `async get_current_user_or_robot` | - | `credentials: Optional[HTTPAuthorizationCredentials], x_api_key: Optional[str]` | `AuthenticatedUser` | UNUSED |
| `get_robot_authenticator` | - | `` | `RobotAuthenticator` | USED |
| `get_tenant_id` | - | `user: AuthenticatedUser` | `Optional[str]` | UNUSED |
| `async optional_auth` | - | `credentials: Optional[HTTPAuthorizationCredentials]` | `Optional[AuthenticatedUser]` | UNUSED |
| `async optional_robot_token` | - | `x_api_key: Optional[str]` | `Optional[str]` | UNUSED |
| `require_role` | - | `required_role: str` | `-` | UNUSED |
| `require_same_tenant` | - | `resource_tenant_id: str` | `-` | UNUSED |
| `require_tenant` | - | `` | `str` | UNUSED |
| `async role_checker` | - | `user: AuthenticatedUser` | `AuthenticatedUser` | UNUSED |
| `async verify_robot_token` | - | `x_api_key: str` | `str` | UNUSED |
| `async verify_token` | - | `credentials: Optional[HTTPAuthorizationCredentials]` | `AuthenticatedUser` | USED |
| `has_role` | AuthenticatedUser | `self, role: str` | `bool` | USED |
| `is_admin` | AuthenticatedUser | `self` | `bool` | UNUSED |
| `__init__` | RobotAuthenticator | `self, use_database: bool, db_pool` | `-` | DUNDER |
| `_load_token_hashes` | RobotAuthenticator | `self` | `dict[str, str]` | INTERNAL |
| `is_enabled` | RobotAuthenticator | `self` | `bool` | USED |
| `verify_token` | RobotAuthenticator | `self, token: str` | `Optional[str]` | USED |
| `async verify_token_async` | RobotAuthenticator | `self, token: str, client_ip: Optional[str]` | `Optional[str]` | USED |


## casare_rpa.infrastructure.orchestrator.api.database

**File:** `src\casare_rpa\infrastructure\orchestrator\api\database.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `async create_db_pool` | - | `database_url: str` | `asyncpg.Pool` | UNUSED |
| `__init__` | MonitoringDatabase | `self, pool: asyncpg.Pool` | `-` | DUNDER |
| `async _get_self_healing_stats` | MonitoringDatabase | `self, conn: asyncpg.Connection` | `Dict[str, Any]` | INTERNAL |
| `_normalize_node_timing` | MonitoringDatabase | `self, node_id: str, timing_data: Any` | `Dict[str, Any]` | INTERNAL |
| `_parse_node_execution_breakdown` | MonitoringDatabase | `self, workflow_output: Any` | `List[Dict[str, Any]]` | INTERNAL |
| `async get_analytics` | MonitoringDatabase | `self` | `Dict[str, Any]` | USED |
| `async get_fleet_summary` | MonitoringDatabase | `self` | `Dict[str, Any]` | USED |
| `async get_job_details` | MonitoringDatabase | `self, job_id: str` | `Optional[Dict[str, Any]]` | UNUSED |
| `async get_job_history` | MonitoringDatabase | `self, limit: int, status: Optional[str], ...` | `List[Dict[str, Any]]` | USED |
| `async get_robot_details` | MonitoringDatabase | `self, robot_id: str` | `Optional[Dict[str, Any]]` | USED |
| `async get_robot_list` | MonitoringDatabase | `self, status: Optional[str]` | `List[Dict[str, Any]]` | USED |


## casare_rpa.infrastructure.orchestrator.api.dependencies

**File:** `src\casare_rpa\infrastructure\orchestrator\api\dependencies.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `async get_db_connection` | - | `request: Request` | `AsyncGenerator[asyncpg.Connection, None]` | USED |
| `async get_db_pool` | - | `request: Request` | `asyncpg.Pool` | USED |
| `get_metrics_collector` | - | `request: Request` | `-` | USED |
| `get_pool_manager` | - | `` | `DatabasePoolManager` | USED |
| `from_env` | DatabaseConfig | `cls` | `'DatabaseConfig'` | USED |
| `__init__` | DatabasePoolManager | `self, config: Optional[DatabaseConfig]` | `-` | DUNDER |
| `async _verify_connection` | DatabasePoolManager | `self` | `None` | INTERNAL |
| `async check_health` | DatabasePoolManager | `self` | `dict` | USED |
| `async close` | DatabasePoolManager | `self` | `None` | USED |
| `async create_pool` | DatabasePoolManager | `self` | `asyncpg.Pool` | USED |
| `is_healthy` | DatabasePoolManager | `self` | `bool` | UNUSED |
| `pool` | DatabasePoolManager | `self` | `Optional[asyncpg.Pool]` | UNUSED |


## casare_rpa.infrastructure.orchestrator.api.main

**File:** `src\casare_rpa\infrastructure\orchestrator\api\main.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `async _init_database_pool` | - | `app: FastAPI` | `Optional[DatabasePoolManager]` | INTERNAL |
| `async _shutdown_database_pool` | - | `app: FastAPI` | `None` | INTERNAL |
| `async detailed_health_check` | - | `` | `-` | UNUSED |
| `async generic_exception_handler` | - | `request: Request, exc: Exception` | `JSONResponse` | UNUSED |
| `async health_check` | - | `` | `-` | UNUSED |
| `async http_exception_handler` | - | `request: Request, exc` | `JSONResponse` | UNUSED |
| `async lifespan` | - | `app: FastAPI` | `-` | UNUSED |
| `async liveness_check` | - | `` | `-` | UNUSED |
| `async readiness_check` | - | `` | `-` | UNUSED |
| `async root` | - | `` | `-` | UNUSED |
| `async validation_exception_handler` | - | `request: Request, exc: RequestValidationError` | `JSONResponse` | UNUSED |
| `async dispatch` | RequestIdMiddleware | `self, request: Request, call_next` | `-` | UNUSED |


## casare_rpa.infrastructure.orchestrator.api.rate_limit

**File:** `src\casare_rpa\infrastructure\orchestrator\api\rate_limit.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `decorator` | - | `func: Callable` | `Callable` | UNUSED |
| `get_ip_only` | - | `request: Request` | `str` | UNUSED |
| `get_rate_limit_info` | - | `request: Request` | `dict` | UNUSED |
| `get_tenant_or_ip` | - | `request: Request` | `str` | USED |
| `get_user_or_ip` | - | `request: Request` | `str` | UNUSED |
| `limit_auth` | - | `func: Callable` | `Callable` | UNUSED |
| `limit_custom` | - | `limit: str, key_func: Optional[Callable]` | `Callable` | UNUSED |
| `limit_high` | - | `func: Callable` | `Callable` | UNUSED |
| `limit_low` | - | `func: Callable` | `Callable` | UNUSED |
| `limit_progress` | - | `func: Callable` | `Callable` | UNUSED |
| `limit_standard` | - | `func: Callable` | `Callable` | UNUSED |
| `async rate_limit_exceeded_handler` | - | `request: Request, exc: RateLimitExceeded` | `JSONResponse` | UNUSED |
| `setup_rate_limiting` | - | `app` | `None` | UNUSED |


## casare_rpa.infrastructure.orchestrator.api.responses

**File:** `src\casare_rpa\infrastructure\orchestrator\api\responses.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `error_response` | - | `code: ErrorCode, message: str, request_id: str, ...` | `dict` | USED |
| `success_response` | - | `data: Any, request_id: str, page: Optional[int], ...` | `dict` | UNUSED |
| `serialize_timestamp` | ResponseMeta | `self, v: datetime` | `str` | UNUSED |


## casare_rpa.infrastructure.orchestrator.api.routers.analytics

**File:** `src\casare_rpa\infrastructure\orchestrator\api\routers\analytics.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `async add_trace` | - | `request: Request, trace_data: Dict[str, Any]` | `Dict[str, str]` | USED |
| `async analyze_bottlenecks` | - | `request: Request, workflow_id: str, days: int` | `BottleneckAnalysisResponse` | USED |
| `async analyze_execution` | - | `request: Request, workflow_id: str, days: int` | `ExecutionAnalysisResponse` | UNUSED |
| `async check_conformance` | - | `request: Request, workflow_id: str, limit: int` | `ConformanceSummaryResponse` | USED |
| `async clear_traces` | - | `request: Request, workflow_id: str` | `Dict[str, str]` | UNUSED |
| `async discover_process` | - | `request: Request, workflow_id: str, limit: int` | `ProcessModelResponse` | USED |
| `get_bottleneck_detector` | - | `` | `BottleneckDetector` | USED |
| `get_execution_analyzer` | - | `` | `ExecutionAnalyzer` | USED |
| `async get_execution_timeline` | - | `request: Request, workflow_id: str, days: int, ...` | `Dict[str, Any]` | USED |
| `async get_node_performance` | - | `request: Request, workflow_id: str, node_id: str, ...` | `NodeStatsResponse` | UNUSED |
| `async get_process_insights` | - | `request: Request, workflow_id: str, limit: int` | `List[ProcessInsightResponse]` | UNUSED |
| `async get_traces` | - | `request: Request, workflow_id: str, limit: int, ...` | `List[Dict[str, Any]]` | UNUSED |
| `async get_variants` | - | `request: Request, workflow_id: str, limit: int` | `VariantsResponse` | USED |
| `async list_workflows_with_traces` | - | `request: Request` | `List[Dict[str, Any]]` | UNUSED |


## casare_rpa.infrastructure.orchestrator.api.routers.auth

**File:** `src\casare_rpa\infrastructure\orchestrator\api\routers\auth.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_check_rate_limit` | - | `ip: str` | `Tuple[bool, Optional[int]]` | INTERNAL |
| `_get_client_ip` | - | `request: Request` | `str` | INTERNAL |
| `_record_login_attempt` | - | `ip: str, success: bool` | `None` | INTERNAL |
| `async get_me` | - | `user: AuthenticatedUser` | `UserInfoResponse` | USED |
| `async login` | - | `request: LoginRequest, http_request: Request` | `TokenResponse` | USED |
| `async logout` | - | `user: AuthenticatedUser` | `LogoutResponse` | USED |
| `async refresh_token` | - | `request: RefreshRequest, http_request: Request` | `TokenResponse` | USED |


## casare_rpa.infrastructure.orchestrator.api.routers.jobs

**File:** `src\casare_rpa\infrastructure\orchestrator\api\routers\jobs.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `async cancel_job` | - | `request: Request, job_id: str` | `-` | UNUSED |
| `get_db_pool` | - | `` | `-` | USED |
| `async retry_job` | - | `request: Request, job_id: str` | `-` | UNUSED |
| `set_db_pool` | - | `pool` | `None` | UNUSED |
| `async update_job_progress` | - | `request: Request, job_id: str, update: JobProgressUpdate` | `-` | USED |


## casare_rpa.infrastructure.orchestrator.api.routers.metrics

**File:** `src\casare_rpa\infrastructure\orchestrator\api\routers\metrics.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `async broadcast_metrics_to_websockets` | - | `data: Dict[str, Any]` | `None` | UNUSED |
| `async get_activity` | - | `request: Request, limit: int, since: Optional[datetime], ...` | `-` | UNUSED |
| `async get_analytics` | - | `request: Request, days: int` | `-` | USED |
| `async get_fleet_metrics` | - | `request: Request, collector` | `-` | USED |
| `async get_job_details` | - | `request: Request, job_id: str, collector` | `-` | UNUSED |
| `async get_jobs` | - | `request: Request, limit: int, status: Optional[str], ...` | `-` | USED |
| `async get_metrics_snapshot` | - | `request: Request, environment: str` | `-` | UNUSED |
| `async get_prometheus_metrics` | - | `request: Request, environment: str` | `-` | UNUSED |
| `async get_robot_details` | - | `request: Request, robot_id: str, collector` | `-` | USED |
| `async get_robots` | - | `request: Request, status: Optional[str], collector` | `-` | USED |
| `get_websocket_connection_count` | - | `` | `int` | UNUSED |
| `async metrics_websocket_stream` | - | `websocket: WebSocket, interval: int, environment: str` | `-` | UNUSED |


## casare_rpa.infrastructure.orchestrator.api.routers.robots

**File:** `src\casare_rpa\infrastructure\orchestrator\api\routers\robots.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_row_to_response` | - | `row: Dict[str, Any]` | `RobotResponse` | INTERNAL |
| `async delete_robot` | - | `request: Request, robot_id: str` | `-` | USED |
| `get_db_pool` | - | `` | `-` | USED |
| `async get_robot` | - | `request: Request, robot_id: str` | `-` | USED |
| `async list_robots` | - | `request: Request, status: Optional[str], environment: Optional[str], ...` | `-` | UNUSED |
| `parse_jsonb` | - | `val` | `-` | USED |
| `async register_robot` | - | `request: Request, registration: RobotRegistration` | `-` | USED |
| `async robot_heartbeat` | - | `request: Request, robot_id: str, metrics: Optional[Dict[str, Any]]` | `-` | UNUSED |
| `set_db_pool` | - | `pool` | `None` | UNUSED |
| `async update_robot` | - | `request: Request, robot_id: str, update: RobotUpdate` | `-` | USED |
| `async update_robot_status` | - | `request: Request, robot_id: str, status_update: RobotStatusUpdate` | `-` | USED |


## casare_rpa.infrastructure.orchestrator.api.routers.schedules

**File:** `src\casare_rpa\infrastructure\orchestrator\api\routers\schedules.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_convert_to_advanced_schedule` | - | `schedule_id: str, request: ScheduleRequest, now: datetime, ...` | `AdvancedSchedule` | INTERNAL |
| `async _execute_scheduled_workflow` | - | `schedule: AdvancedSchedule` | `None` | INTERNAL |
| `async _get_workflow_data` | - | `schedule: AdvancedSchedule` | `Optional[Dict[str, Any]]` | INTERNAL |
| `async _publish_fallback_job_event` | - | `job_id: str, schedule: AdvancedSchedule` | `None` | INTERNAL |
| `_schedule_to_response` | - | `schedule: AdvancedSchedule` | `Dict[str, Any]` | INTERNAL |
| `calculate_next_run` | - | `cron_expression: str, base_time: Optional[datetime]` | `datetime` | USED |
| `async create_schedule` | - | `request: ScheduleRequest, current_user: AuthenticatedUser` | `ScheduleResponse` | UNUSED |
| `async delete_schedule` | - | `schedule_id: str, current_user: AuthenticatedUser` | `dict` | USED |
| `async disable_schedule` | - | `schedule_id: str, current_user: AuthenticatedUser` | `ScheduleResponse` | USED |
| `async enable_schedule` | - | `schedule_id: str, current_user: AuthenticatedUser` | `ScheduleResponse` | USED |
| `get_db_pool` | - | `` | `-` | USED |
| `async get_schedule` | - | `schedule_id: str, current_user: AuthenticatedUser` | `ScheduleResponse` | USED |
| `async get_upcoming_schedules` | - | `limit: int, workflow_id: Optional[str], current_user: AuthenticatedUser` | `List[dict]` | UNUSED |
| `async list_schedules` | - | `workflow_id: Optional[str], enabled: Optional[bool], limit: int, ...` | `List[ScheduleResponse]` | UNUSED |
| `set_db_pool` | - | `pool` | `None` | UNUSED |
| `async trigger_schedule_now` | - | `schedule_id: str, current_user: AuthenticatedUser` | `dict` | UNUSED |
| `validate_uuid_format` | - | `value: str, field_name: str` | `str` | USED |
| `validate_cron` | ScheduleRequest | `cls, v` | `-` | UNUSED |
| `validate_execution_mode` | ScheduleRequest | `cls, v` | `-` | UNUSED |


## casare_rpa.infrastructure.orchestrator.api.routers.websockets

**File:** `src\casare_rpa\infrastructure\orchestrator\api\routers\websockets.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `async broadcast_job_update` | - | `job_id: str, status: str` | `-` | USED |
| `async broadcast_queue_metrics` | - | `depth: int` | `-` | USED |
| `async broadcast_robot_status` | - | `robot_id: str, status: str, cpu_percent: float, ...` | `-` | USED |
| `async on_job_status_changed` | - | `event: MonitoringEvent` | `None` | UNUSED |
| `async on_queue_depth_changed` | - | `event: MonitoringEvent` | `None` | UNUSED |
| `async on_robot_heartbeat` | - | `event: MonitoringEvent` | `None` | UNUSED |
| `async verify_websocket_token` | - | `websocket: WebSocket, token: Optional[str]` | `Optional[str]` | USED |
| `async websocket_live_jobs` | - | `websocket: WebSocket, token: Optional[str]` | `-` | UNUSED |
| `async websocket_queue_metrics` | - | `websocket: WebSocket, token: Optional[str]` | `-` | UNUSED |
| `async websocket_robot_status` | - | `websocket: WebSocket, token: Optional[str]` | `-` | UNUSED |
| `__init__` | ConnectionManager | `self` | `-` | DUNDER |
| `async broadcast` | ConnectionManager | `self, message: dict` | `-` | USED |
| `async connect` | ConnectionManager | `self, websocket: WebSocket` | `-` | USED |
| `disconnect` | ConnectionManager | `self, websocket: WebSocket` | `-` | USED |


## casare_rpa.infrastructure.orchestrator.api.routers.workflows

**File:** `src\casare_rpa\infrastructure\orchestrator\api\routers\workflows.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_get_trigger_manager` | - | `` | `Optional['TriggerManager']` | INTERNAL |
| `async delete_workflow` | - | `workflow_id: str, current_user: AuthenticatedUser` | `Dict[str, str]` | USED |
| `async enqueue_job` | - | `workflow_id: str, workflow_json: Dict[str, Any], priority: int, ...` | `str` | USED |
| `get_db_pool` | - | `` | `Optional[asyncpg.Pool]` | USED |
| `async get_workflow` | - | `workflow_id: str, current_user: AuthenticatedUser` | `WorkflowDetailsResponse` | USED |
| `get_workflows_dir` | - | `` | `Path` | USED |
| `set_db_pool` | - | `pool: asyncpg.Pool` | `None` | UNUSED |
| `set_trigger_manager` | - | `manager: 'TriggerManager'` | `None` | UNUSED |
| `async store_workflow_database` | - | `workflow_id: str, workflow_name: str, workflow_json: Dict[str, Any], ...` | `bool` | USED |
| `async store_workflow_filesystem` | - | `workflow_id: str, workflow_name: str, workflow_json: Dict[str, Any]` | `Path` | USED |
| `async submit_workflow` | - | `request: WorkflowSubmissionRequest, current_user: AuthenticatedUser` | `WorkflowSubmissionResponse` | USED |
| `async upload_workflow` | - | `file: UploadFile, trigger_type: str, execution_mode: str, ...` | `WorkflowSubmissionResponse` | UNUSED |
| `validate_uuid_format` | - | `value: str, field_name: str` | `str` | USED |
| `validate_execution_mode` | WorkflowSubmissionRequest | `cls, v` | `-` | UNUSED |
| `validate_trigger_type` | WorkflowSubmissionRequest | `cls, v` | `-` | UNUSED |
| `validate_workflow_json` | WorkflowSubmissionRequest | `cls, v` | `-` | USED |


## casare_rpa.infrastructure.orchestrator.client

**File:** `src\casare_rpa\infrastructure\orchestrator\client.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `async configure_orchestrator` | - | `base_url: str, ws_url: Optional[str], api_key: Optional[str]` | `OrchestratorClient` | UNUSED |
| `get_orchestrator_client` | - | `` | `OrchestratorClient` | UNUSED |
| `from_api` | JobData | `cls, data: Dict[str, Any]` | `'JobData'` | USED |
| `parse_dt` | JobData | `val` | `-` | USED |
| `__init__` | OrchestratorClient | `self, config: Optional[OrchestratorConfig]` | `-` | DUNDER |
| `async _notify` | OrchestratorClient | `self, event: str, data: Dict[str, Any]` | `None` | INTERNAL |
| `async _request` | OrchestratorClient | `self, method: str, endpoint: str, ...` | `Optional[Dict[str, Any]]` | INTERNAL |
| `async _ws_loop` | OrchestratorClient | `self` | `None` | INTERNAL |
| `async cancel_job` | OrchestratorClient | `self, job_id: str` | `bool` | UNUSED |
| `async connect` | OrchestratorClient | `self` | `bool` | USED |
| `async delete_robot` | OrchestratorClient | `self, robot_id: str` | `bool` | USED |
| `async disconnect` | OrchestratorClient | `self` | `None` | USED |
| `async get_activity` | OrchestratorClient | `self, limit: int, since: Optional[datetime], ...` | `List[Dict[str, Any]]` | UNUSED |
| `async get_analytics` | OrchestratorClient | `self, days: int` | `Dict[str, Any]` | USED |
| `async get_fleet_metrics` | OrchestratorClient | `self` | `Dict[str, Any]` | USED |
| `async get_job` | OrchestratorClient | `self, job_id: str` | `Optional[JobData]` | USED |
| `async get_jobs` | OrchestratorClient | `self, limit: int, status: Optional[str], ...` | `List[JobData]` | USED |
| `async get_robot` | OrchestratorClient | `self, robot_id: str` | `Optional[RobotData]` | USED |
| `async get_robots` | OrchestratorClient | `self, status: Optional[str]` | `List[RobotData]` | USED |
| `async get_schedules` | OrchestratorClient | `self` | `List[Dict[str, Any]]` | USED |
| `is_connected` | OrchestratorClient | `self` | `bool` | USED |
| `off` | OrchestratorClient | `self, event: str, callback: Callable` | `None` | USED |
| `on` | OrchestratorClient | `self, event: str, callback: Callable` | `None` | USED |
| `async register_robot` | OrchestratorClient | `self, robot_id: str, name: str, ...` | `bool` | USED |
| `async retry_job` | OrchestratorClient | `self, job_id: str` | `Optional[str]` | UNUSED |
| `async subscribe_live_updates` | OrchestratorClient | `self` | `None` | USED |
| `async trigger_schedule` | OrchestratorClient | `self, schedule_id: str` | `bool` | UNUSED |
| `async update_robot_status` | OrchestratorClient | `self, robot_id: str, status: str` | `bool` | USED |
| `from_api` | RobotData | `cls, data: Dict[str, Any]` | `'RobotData'` | USED |


## casare_rpa.infrastructure.orchestrator.communication.cloud_service

**File:** `src\casare_rpa\infrastructure\orchestrator\communication\cloud_service.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | CloudService | `self` | `-` | DUNDER |
| `async connect` | CloudService | `self` | `-` | USED |
| `async dispatch_job` | CloudService | `self, robot_id: str, workflow_json: str` | `-` | UNUSED |
| `async get_jobs` | CloudService | `self` | `List[Dict[str, Any]]` | USED |
| `async get_robots` | CloudService | `self` | `List[Dict[str, Any]]` | USED |


## casare_rpa.infrastructure.orchestrator.communication.delegates

**File:** `src\casare_rpa\infrastructure\orchestrator\communication\delegates.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | DurationDelegate | `self, parent` | `-` | DUNDER |
| `paint` | DurationDelegate | `self, painter: QPainter, option: QStyleOptionViewItem, ...` | `-` | USED |
| `sizeHint` | DurationDelegate | `self, option: QStyleOptionViewItem, index: QModelIndex` | `QSize` | USED |
| `__init__` | IconTextDelegate | `self, icon_map: Optional[dict], parent` | `-` | DUNDER |
| `paint` | IconTextDelegate | `self, painter: QPainter, option: QStyleOptionViewItem, ...` | `-` | USED |
| `sizeHint` | IconTextDelegate | `self, option: QStyleOptionViewItem, index: QModelIndex` | `QSize` | USED |
| `__init__` | PriorityDelegate | `self, parent` | `-` | DUNDER |
| `paint` | PriorityDelegate | `self, painter: QPainter, option: QStyleOptionViewItem, ...` | `-` | USED |
| `sizeHint` | PriorityDelegate | `self, option: QStyleOptionViewItem, index: QModelIndex` | `QSize` | USED |
| `__init__` | ProgressBarDelegate | `self, parent` | `-` | DUNDER |
| `paint` | ProgressBarDelegate | `self, painter: QPainter, option: QStyleOptionViewItem, ...` | `-` | USED |
| `sizeHint` | ProgressBarDelegate | `self, option: QStyleOptionViewItem, index: QModelIndex` | `QSize` | USED |
| `__init__` | RobotStatusDelegate | `self, parent` | `-` | DUNDER |
| `paint` | RobotStatusDelegate | `self, painter: QPainter, option: QStyleOptionViewItem, ...` | `-` | USED |
| `sizeHint` | RobotStatusDelegate | `self, option: QStyleOptionViewItem, index: QModelIndex` | `QSize` | USED |
| `__init__` | StatusDelegate | `self, parent` | `-` | DUNDER |
| `paint` | StatusDelegate | `self, painter: QPainter, option: QStyleOptionViewItem, ...` | `-` | USED |
| `sizeHint` | StatusDelegate | `self, option: QStyleOptionViewItem, index: QModelIndex` | `QSize` | USED |
| `__init__` | TimeDelegate | `self, parent` | `-` | DUNDER |
| `paint` | TimeDelegate | `self, painter: QPainter, option: QStyleOptionViewItem, ...` | `-` | USED |
| `sizeHint` | TimeDelegate | `self, option: QStyleOptionViewItem, index: QModelIndex` | `QSize` | USED |


## casare_rpa.infrastructure.orchestrator.communication.realtime_service

**File:** `src\casare_rpa\infrastructure\orchestrator\communication\realtime_service.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | JobProgressTracker | `self, realtime_service: RealtimeService` | `-` | DUNDER |
| `on_progress` | JobProgressTracker | `self, job_id: str, progress: Dict` | `-` | USED |
| `subscribe` | JobProgressTracker | `self, job_id: str, callback: Callable[[Dict], None]` | `-` | USED |
| `unsubscribe` | JobProgressTracker | `self, job_id: str, callback: Callable[[Dict], None]` | `-` | USED |
| `__init__` | RealtimeService | `self, url: str, key: str, ...` | `-` | DUNDER |
| `async _poll_jobs` | RealtimeService | `self` | `-` | INTERNAL |
| `async _poll_loop` | RealtimeService | `self` | `-` | INTERNAL |
| `async _poll_robots` | RealtimeService | `self` | `-` | INTERNAL |
| `async _start_polling` | RealtimeService | `self` | `bool` | INTERNAL |
| `async _subscribe_to_jobs` | RealtimeService | `self` | `-` | INTERNAL |
| `async _subscribe_to_robots` | RealtimeService | `self` | `-` | INTERNAL |
| `async connect` | RealtimeService | `self` | `bool` | USED |
| `async disconnect` | RealtimeService | `self` | `-` | USED |
| `track_job` | RealtimeService | `self, job_id: str` | `-` | USED |
| `untrack_job` | RealtimeService | `self, job_id: str` | `-` | USED |
| `__init__` | RobotStatusTracker | `self, realtime_service: RealtimeService` | `-` | DUNDER |
| `get_all_robots` | RobotStatusTracker | `self` | `List[Dict]` | USED |
| `get_robot_status` | RobotStatusTracker | `self, robot_id: str` | `Optional[Dict]` | UNUSED |
| `on_robot_update` | RobotStatusTracker | `self, robot: Dict` | `-` | UNUSED |
| `subscribe` | RobotStatusTracker | `self, callback: Callable[[Dict], None]` | `-` | USED |
| `unsubscribe` | RobotStatusTracker | `self, callback: Callable[[Dict], None]` | `-` | USED |


## casare_rpa.infrastructure.orchestrator.communication.websocket_client

**File:** `src\casare_rpa\infrastructure\orchestrator\communication\websocket_client.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | RobotClient | `self, robot_id: str, robot_name: str, ...` | `-` | DUNDER |
| `_get_capabilities` | RobotClient | `self` | `Dict[str, Any]` | INTERNAL |
| `async _handle_error` | RobotClient | `self, msg: Message` | `-` | INTERNAL |
| `async _handle_heartbeat_ack` | RobotClient | `self, msg: Message` | `-` | INTERNAL |
| `async _handle_job_assign` | RobotClient | `self, msg: Message` | `-` | INTERNAL |
| `async _handle_job_cancel` | RobotClient | `self, msg: Message` | `-` | INTERNAL |
| `async _handle_pause` | RobotClient | `self, msg: Message` | `-` | INTERNAL |
| `async _handle_register_ack` | RobotClient | `self, msg: Message` | `-` | INTERNAL |
| `async _handle_resume` | RobotClient | `self, msg: Message` | `-` | INTERNAL |
| `async _handle_shutdown` | RobotClient | `self, msg: Message` | `-` | INTERNAL |
| `async _handle_status_request` | RobotClient | `self, msg: Message` | `-` | INTERNAL |
| `async _heartbeat_loop` | RobotClient | `self` | `-` | INTERNAL |
| `async _receive_loop` | RobotClient | `self` | `-` | INTERNAL |
| `async _reconnect` | RobotClient | `self` | `-` | INTERNAL |
| `async _register` | RobotClient | `self` | `-` | INTERNAL |
| `async _send` | RobotClient | `self, msg: Message` | `-` | INTERNAL |
| `async _send_heartbeat` | RobotClient | `self` | `-` | INTERNAL |
| `_setup_handlers` | RobotClient | `self` | `-` | INTERNAL |
| `active_job_count` | RobotClient | `self` | `int` | UNUSED |
| `async connect` | RobotClient | `self` | `bool` | USED |
| `async disconnect` | RobotClient | `self, reason: str` | `-` | USED |
| `get_active_jobs` | RobotClient | `self` | `List[str]` | USED |
| `is_available` | RobotClient | `self` | `bool` | UNUSED |
| `is_connected` | RobotClient | `self` | `bool` | USED |
| `is_paused` | RobotClient | `self` | `bool` | UNUSED |
| `async report_job_complete` | RobotClient | `self, job_id: str, result: Optional[Dict[str, Any]]` | `-` | UNUSED |
| `async report_job_failed` | RobotClient | `self, job_id: str, error_message: str, ...` | `-` | USED |
| `async report_progress` | RobotClient | `self, job_id: str, progress: int, ...` | `-` | UNUSED |
| `async send_log` | RobotClient | `self, job_id: str, level: str, ...` | `-` | UNUSED |
| `async send_log_batch` | RobotClient | `self, job_id: str, entries: List[Dict[str, Any]]` | `-` | UNUSED |
| `set_callbacks` | RobotClient | `self, on_job_received: Optional[Callable[[Dict], Any]], on_job_cancel: Optional[Callable[[str], Any]], ...` | `-` | USED |


## casare_rpa.infrastructure.orchestrator.communication.websocket_server

**File:** `src\casare_rpa\infrastructure\orchestrator\communication\websocket_server.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | OrchestratorServer | `self, host: str, port: int, ...` | `-` | DUNDER |
| `async _check_robot_health` | OrchestratorServer | `self` | `-` | INTERNAL |
| `async _handle_connection` | OrchestratorServer | `self, websocket: 'WebSocketServerProtocol'` | `-` | INTERNAL |
| `async _handle_disconnect` | OrchestratorServer | `self, websocket: WebSocketServerProtocol, msg: Message` | `-` | INTERNAL |
| `async _handle_heartbeat` | OrchestratorServer | `self, websocket: WebSocketServerProtocol, msg: Message` | `-` | INTERNAL |
| `async _handle_job_accept` | OrchestratorServer | `self, websocket: WebSocketServerProtocol, msg: Message` | `-` | INTERNAL |
| `async _handle_job_cancelled` | OrchestratorServer | `self, websocket: WebSocketServerProtocol, msg: Message` | `-` | INTERNAL |
| `async _handle_job_complete` | OrchestratorServer | `self, websocket: WebSocketServerProtocol, msg: Message` | `-` | INTERNAL |
| `async _handle_job_failed` | OrchestratorServer | `self, websocket: WebSocketServerProtocol, msg: Message` | `-` | INTERNAL |
| `async _handle_job_progress` | OrchestratorServer | `self, websocket: WebSocketServerProtocol, msg: Message` | `-` | INTERNAL |
| `async _handle_job_reject` | OrchestratorServer | `self, websocket: WebSocketServerProtocol, msg: Message` | `-` | INTERNAL |
| `async _handle_log_batch` | OrchestratorServer | `self, websocket: WebSocketServerProtocol, msg: Message` | `-` | INTERNAL |
| `async _handle_log_entry` | OrchestratorServer | `self, websocket: WebSocketServerProtocol, msg: Message` | `-` | INTERNAL |
| `async _handle_register` | OrchestratorServer | `self, websocket: WebSocketServerProtocol, msg: Message` | `-` | INTERNAL |
| `async _handle_status_response` | OrchestratorServer | `self, websocket: WebSocketServerProtocol, msg: Message` | `-` | INTERNAL |
| `async _health_check_loop` | OrchestratorServer | `self` | `-` | INTERNAL |
| `async _remove_connection` | OrchestratorServer | `self, robot_id: str` | `-` | INTERNAL |
| `_resolve_response` | OrchestratorServer | `self, correlation_id: Optional[str], result: Any` | `-` | INTERNAL |
| `async _send` | OrchestratorServer | `self, websocket: WebSocketServerProtocol, msg: Message` | `-` | INTERNAL |
| `async _send_error` | OrchestratorServer | `self, websocket: WebSocketServerProtocol, error_code: str, ...` | `-` | INTERNAL |
| `_setup_handlers` | OrchestratorServer | `self` | `-` | INTERNAL |
| `available_count` | OrchestratorServer | `self` | `int` | UNUSED |
| `async broadcast` | OrchestratorServer | `self, msg: Message, environment: Optional[str]` | `-` | USED |
| `async cancel_job` | OrchestratorServer | `self, robot_id: str, job_id: str, ...` | `bool` | UNUSED |
| `connected_count` | OrchestratorServer | `self` | `int` | UNUSED |
| `get_available_robots` | OrchestratorServer | `self` | `List[Robot]` | USED |
| `get_connected_robots` | OrchestratorServer | `self` | `List[Robot]` | USED |
| `get_robot` | OrchestratorServer | `self, robot_id: str` | `Optional[Robot]` | USED |
| `is_robot_connected` | OrchestratorServer | `self, robot_id: str` | `bool` | UNUSED |
| `async request_status` | OrchestratorServer | `self, robot_id: str, timeout: float` | `Optional[Dict]` | UNUSED |
| `async send_job` | OrchestratorServer | `self, robot_id: str, job: Job, ...` | `Dict[str, Any]` | USED |
| `set_callbacks` | OrchestratorServer | `self, on_robot_connect: Optional[Callable[[Robot], Any]], on_robot_disconnect: Optional[Callable[[str], Any]], ...` | `-` | USED |
| `async start` | OrchestratorServer | `self` | `-` | USED |
| `async stop` | OrchestratorServer | `self` | `-` | USED |
| `__init__` | RobotConnection | `self, websocket: 'WebSocketServerProtocol', robot_id: str, ...` | `-` | DUNDER |
| `is_available` | RobotConnection | `self` | `bool` | UNUSED |
| `to_robot` | RobotConnection | `self` | `Robot` | USED |


## casare_rpa.infrastructure.orchestrator.health_endpoints

**File:** `src\casare_rpa\infrastructure\orchestrator\health_endpoints.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `async health_check` | - | `` | `-` | UNUSED |
| `async liveness_check` | - | `` | `-` | UNUSED |
| `async readiness_check` | - | `` | `-` | UNUSED |


## casare_rpa.infrastructure.orchestrator.persistence.local_job_repository

**File:** `src\casare_rpa\infrastructure\orchestrator\persistence\local_job_repository.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | LocalJobRepository | `self, storage: LocalStorageRepository` | `-` | DUNDER |
| `async delete` | LocalJobRepository | `self, job_id: str` | `None` | USED |
| `async get_all` | LocalJobRepository | `self` | `List[Job]` | USED |
| `async get_by_id` | LocalJobRepository | `self, job_id: str` | `Optional[Job]` | USED |
| `async get_by_robot` | LocalJobRepository | `self, robot_id: str` | `List[Job]` | USED |
| `async get_by_status` | LocalJobRepository | `self, status: JobStatus` | `List[Job]` | USED |
| `async get_by_workflow` | LocalJobRepository | `self, workflow_id: str` | `List[Job]` | USED |
| `async save` | LocalJobRepository | `self, job: Job` | `None` | USED |


## casare_rpa.infrastructure.orchestrator.persistence.local_robot_repository

**File:** `src\casare_rpa\infrastructure\orchestrator\persistence\local_robot_repository.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | LocalRobotRepository | `self, storage: LocalStorageRepository` | `-` | DUNDER |
| `async delete` | LocalRobotRepository | `self, robot_id: str` | `None` | USED |
| `async get_all` | LocalRobotRepository | `self` | `List[Robot]` | USED |
| `async get_all_online` | LocalRobotRepository | `self` | `List[Robot]` | UNUSED |
| `async get_by_environment` | LocalRobotRepository | `self, environment: str` | `List[Robot]` | UNUSED |
| `async get_by_id` | LocalRobotRepository | `self, robot_id: str` | `Optional[Robot]` | USED |
| `async save` | LocalRobotRepository | `self, robot: Robot` | `None` | USED |
| `async update_status` | LocalRobotRepository | `self, robot_id: str, status: RobotStatus` | `None` | USED |


## casare_rpa.infrastructure.orchestrator.persistence.local_schedule_repository

**File:** `src\casare_rpa\infrastructure\orchestrator\persistence\local_schedule_repository.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | LocalScheduleRepository | `self, storage: LocalStorageRepository` | `-` | DUNDER |
| `async delete` | LocalScheduleRepository | `self, schedule_id: str` | `None` | USED |
| `async get_all` | LocalScheduleRepository | `self` | `List[Schedule]` | USED |
| `async get_by_id` | LocalScheduleRepository | `self, schedule_id: str` | `Optional[Schedule]` | USED |
| `async get_enabled` | LocalScheduleRepository | `self` | `List[Schedule]` | USED |
| `async save` | LocalScheduleRepository | `self, schedule: Schedule` | `None` | USED |


## casare_rpa.infrastructure.orchestrator.persistence.local_storage_repository

**File:** `src\casare_rpa\infrastructure\orchestrator\persistence\local_storage_repository.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | LocalStorageRepository | `self, storage_dir: Optional[Path]` | `-` | DUNDER |
| `_load_json` | LocalStorageRepository | `self, file_path: Path` | `List[Dict[str, Any]]` | INTERNAL |
| `_save_json` | LocalStorageRepository | `self, file_path: Path, data: List[Dict[str, Any]]` | `bool` | INTERNAL |
| `delete_job` | LocalStorageRepository | `self, job_id: str` | `bool` | USED |
| `delete_robot` | LocalStorageRepository | `self, robot_id: str` | `bool` | USED |
| `delete_schedule` | LocalStorageRepository | `self, schedule_id: str` | `bool` | USED |
| `delete_trigger` | LocalStorageRepository | `self, trigger_id: str` | `bool` | USED |
| `delete_triggers_by_scenario` | LocalStorageRepository | `self, scenario_id: str` | `int` | USED |
| `delete_workflow` | LocalStorageRepository | `self, workflow_id: str` | `bool` | USED |
| `get_jobs` | LocalStorageRepository | `self, limit: int, status: Optional[str]` | `List[Dict[str, Any]]` | USED |
| `get_robots` | LocalStorageRepository | `self` | `List[Dict[str, Any]]` | USED |
| `get_schedules` | LocalStorageRepository | `self` | `List[Dict[str, Any]]` | USED |
| `get_triggers` | LocalStorageRepository | `self` | `List[Dict[str, Any]]` | USED |
| `get_workflows` | LocalStorageRepository | `self` | `List[Dict[str, Any]]` | USED |
| `save_job` | LocalStorageRepository | `self, job: Dict[str, Any]` | `bool` | USED |
| `save_robot` | LocalStorageRepository | `self, robot: Dict[str, Any]` | `bool` | USED |
| `save_schedule` | LocalStorageRepository | `self, schedule: Dict[str, Any]` | `bool` | USED |
| `save_trigger` | LocalStorageRepository | `self, trigger: Dict[str, Any]` | `bool` | USED |
| `save_workflow` | LocalStorageRepository | `self, workflow: Dict[str, Any]` | `bool` | USED |


## casare_rpa.infrastructure.orchestrator.persistence.local_trigger_repository

**File:** `src\casare_rpa\infrastructure\orchestrator\persistence\local_trigger_repository.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | LocalTriggerRepository | `self, storage: LocalStorageRepository` | `-` | DUNDER |
| `async delete` | LocalTriggerRepository | `self, trigger_id: str` | `None` | USED |
| `async delete_by_scenario` | LocalTriggerRepository | `self, scenario_id: str` | `int` | UNUSED |
| `async get_all` | LocalTriggerRepository | `self` | `List[BaseTriggerConfig]` | USED |
| `async get_by_id` | LocalTriggerRepository | `self, trigger_id: str` | `Optional[BaseTriggerConfig]` | USED |
| `async get_by_scenario` | LocalTriggerRepository | `self, scenario_id: str` | `List[BaseTriggerConfig]` | UNUSED |
| `async get_by_type` | LocalTriggerRepository | `self, trigger_type: TriggerType` | `List[BaseTriggerConfig]` | UNUSED |
| `async get_by_workflow` | LocalTriggerRepository | `self, workflow_id: str` | `List[BaseTriggerConfig]` | USED |
| `async get_enabled` | LocalTriggerRepository | `self` | `List[BaseTriggerConfig]` | USED |
| `async save` | LocalTriggerRepository | `self, trigger: BaseTriggerConfig` | `None` | USED |


## casare_rpa.infrastructure.orchestrator.persistence.local_workflow_repository

**File:** `src\casare_rpa\infrastructure\orchestrator\persistence\local_workflow_repository.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | LocalWorkflowRepository | `self, storage: LocalStorageRepository` | `-` | DUNDER |
| `async delete` | LocalWorkflowRepository | `self, workflow_id: str` | `None` | USED |
| `async get_all` | LocalWorkflowRepository | `self` | `List[Workflow]` | USED |
| `async get_by_id` | LocalWorkflowRepository | `self, workflow_id: str` | `Optional[Workflow]` | USED |
| `async get_by_status` | LocalWorkflowRepository | `self, status: WorkflowStatus` | `List[Workflow]` | USED |
| `async save` | LocalWorkflowRepository | `self, workflow: Workflow` | `None` | USED |


## casare_rpa.infrastructure.orchestrator.resilience.error_recovery

**File:** `src\casare_rpa\infrastructure\orchestrator\resilience\error_recovery.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `is_expired` | AuthToken | `self` | `bool` | USED |
| `__init__` | ErrorRecoveryManager | `self, retry_policy: Optional[RetryPolicy], max_history: int` | `-` | DUNDER |
| `_record_action` | ErrorRecoveryManager | `self, error_type: str, strategy: RecoveryStrategy, ...` | `-` | INTERNAL |
| `get_recent_actions` | ErrorRecoveryManager | `self, limit: int` | `List[RecoveryAction]` | UNUSED |
| `get_statistics` | ErrorRecoveryManager | `self` | `Dict[str, Any]` | USED |
| `async handle_connection_error` | ErrorRecoveryManager | `self, robot_id: str, error: Exception, ...` | `bool` | USED |
| `async handle_job_error` | ErrorRecoveryManager | `self, job_id: str, robot_id: str, ...` | `bool` | UNUSED |
| `async handle_robot_crash` | ErrorRecoveryManager | `self, robot_id: str, active_jobs: List[str], ...` | `Dict[str, bool]` | UNUSED |
| `set_callbacks` | ErrorRecoveryManager | `self, on_success: Optional[Callable], on_failure: Optional[Callable], ...` | `-` | USED |
| `is_healthy` | HealthMetrics | `self` | `bool` | UNUSED |
| `to_dict` | HealthMetrics | `self` | `Dict[str, Any]` | USED |
| `__init__` | HealthMonitor | `self, thresholds: Optional[HealthThresholds], check_interval: float` | `-` | DUNDER |
| `_calculate_status` | HealthMonitor | `self, metrics: HealthMetrics` | `HealthStatus` | INTERNAL |
| `async _check_all_robots` | HealthMonitor | `self` | `-` | INTERNAL |
| `async _check_loop` | HealthMonitor | `self` | `-` | INTERNAL |
| `_notify_health_change` | HealthMonitor | `self, robot_id: str, old_status: HealthStatus, ...` | `-` | INTERNAL |
| `get_all_health` | HealthMonitor | `self` | `Dict[str, HealthMetrics]` | UNUSED |
| `get_overall_health` | HealthMonitor | `self` | `Dict[str, Any]` | UNUSED |
| `get_robot_health` | HealthMonitor | `self, robot_id: str` | `Optional[HealthMetrics]` | UNUSED |
| `get_unhealthy_robots` | HealthMonitor | `self` | `List[str]` | UNUSED |
| `record_error` | HealthMonitor | `self, robot_id: str` | `-` | USED |
| `record_request` | HealthMonitor | `self, robot_id: str, response_time_ms: float` | `-` | UNUSED |
| `remove_robot` | HealthMonitor | `self, robot_id: str` | `-` | USED |
| `set_callbacks` | HealthMonitor | `self, on_health_change: Optional[Callable], on_robot_unhealthy: Optional[Callable]` | `-` | USED |
| `async start` | HealthMonitor | `self` | `-` | USED |
| `async stop` | HealthMonitor | `self` | `-` | USED |
| `update_heartbeat` | HealthMonitor | `self, robot_id: str, cpu_percent: float, ...` | `-` | USED |
| `calculate_delay` | RetryPolicy | `self, attempt: int` | `float` | USED |
| `should_retry` | RetryPolicy | `self, error_type: str, attempt: int` | `bool` | USED |
| `__init__` | SecurityManager | `self, secret_key: Optional[str], token_ttl_hours: int, ...` | `-` | DUNDER |
| `active_token_count` | SecurityManager | `self` | `int` | UNUSED |
| `check_rate_limit` | SecurityManager | `self, identifier: str` | `bool` | UNUSED |
| `cleanup_expired_tokens` | SecurityManager | `self` | `int` | UNUSED |
| `cleanup_stale_rate_limits` | SecurityManager | `self` | `int` | UNUSED |
| `generate_token` | SecurityManager | `self, robot_id: str, scopes: Optional[List[str]]` | `AuthToken` | UNUSED |
| `get_rate_limit_remaining` | SecurityManager | `self, identifier: str` | `int` | UNUSED |
| `get_statistics` | SecurityManager | `self` | `Dict[str, Any]` | USED |
| `revoke_robot_tokens` | SecurityManager | `self, robot_id: str` | `int` | UNUSED |
| `revoke_token` | SecurityManager | `self, token_str: str` | `bool` | UNUSED |
| `sign_message` | SecurityManager | `self, message: str` | `str` | USED |
| `validate_token` | SecurityManager | `self, token_str: str` | `Optional[AuthToken]` | UNUSED |
| `verify_signature` | SecurityManager | `self, message: str, signature: str` | `bool` | USED |


## casare_rpa.infrastructure.orchestrator.resilience.robot_recovery

**File:** `src\casare_rpa\infrastructure\orchestrator\resilience\robot_recovery.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `async get_workflow_status` | DBOSClientProtocol | `self, workflow_id: str` | `Optional[Dict[str, Any]]` | USED |
| `async __aenter__` | RobotRecoveryManager | `self` | `'RobotRecoveryManager'` | DUNDER |
| `async __aexit__` | RobotRecoveryManager | `self, exc_type: Any, exc_val: Any, ...` | `bool` | DUNDER |
| `__init__` | RobotRecoveryManager | `self, config: RobotRecoveryConfig, dbos_client: Optional[DBOSClientProtocol], ...` | `None` | DUNDER |
| `_calculate_retry_delay` | RobotRecoveryManager | `self, retry_count: int` | `int` | INTERNAL |
| `async _check_for_stale_robots` | RobotRecoveryManager | `self` | `None` | INTERNAL |
| `async _find_claimed_jobs` | RobotRecoveryManager | `self, robot_id: str` | `List[FailedJobInfo]` | INTERNAL |
| `async _get_checkpoint_status` | RobotRecoveryManager | `self, job_id: str` | `Optional[WorkflowCheckpointStatus]` | INTERNAL |
| `async _health_monitor_loop` | RobotRecoveryManager | `self` | `None` | INTERNAL |
| `async _mark_robot_failed` | RobotRecoveryManager | `self, robot_id: str` | `bool` | INTERNAL |
| `async _move_job_to_dlq` | RobotRecoveryManager | `self, job_id: str, error_message: str, ...` | `bool` | INTERNAL |
| `_record_recovery_event` | RobotRecoveryManager | `self, event: RobotFailureEvent, results: List[RecoveryResult]` | `None` | INTERNAL |
| `async _recover_job` | RobotRecoveryManager | `self, job: FailedJobInfo, robot_id: str, ...` | `RecoveryResult` | INTERNAL |
| `async _release_job_for_resumption` | RobotRecoveryManager | `self, job_id: str, delay_seconds: int, ...` | `bool` | INTERNAL |
| `async _requeue_job_for_retry` | RobotRecoveryManager | `self, job_id: str, delay_seconds: int, ...` | `bool` | INTERNAL |
| `get_statistics` | RobotRecoveryManager | `self` | `Dict[str, Any]` | USED |
| `async handle_robot_failure` | RobotRecoveryManager | `self, event: RobotFailureEvent` | `List[RecoveryResult]` | USED |
| `is_running` | RobotRecoveryManager | `self` | `bool` | USED |
| `async manually_recover_robot` | RobotRecoveryManager | `self, robot_id: str, reason: str` | `List[RecoveryResult]` | UNUSED |
| `recovery_history` | RobotRecoveryManager | `self` | `List[Dict[str, Any]]` | UNUSED |
| `async start` | RobotRecoveryManager | `self` | `bool` | USED |
| `async stop` | RobotRecoveryManager | `self` | `None` | USED |


## casare_rpa.infrastructure.orchestrator.rest_endpoints

**File:** `src\casare_rpa\infrastructure\orchestrator\rest_endpoints.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `async get_job` | - | `job_id: str, _: str` | `-` | USED |
| `async get_log_cleanup_status` | - | `_: str` | `-` | UNUSED |
| `async get_log_stats` | - | `_: str, tenant_id: str, robot_id: Optional[str]` | `-` | UNUSED |
| `async get_log_streaming_metrics` | - | `_: str` | `-` | UNUSED |
| `async get_robot` | - | `robot_id: str, _: str` | `-` | USED |
| `async list_jobs` | - | `_: str, status: Optional[str], tenant_id: Optional[str], ...` | `-` | UNUSED |
| `async list_robots` | - | `_: str, tenant_id: Optional[str]` | `-` | UNUSED |
| `async query_logs` | - | `_: str, tenant_id: str, robot_id: Optional[str], ...` | `-` | UNUSED |
| `async submit_job` | - | `submission: JobSubmission, _: str` | `-` | USED |
| `async trigger_log_cleanup` | - | `_: str` | `-` | UNUSED |


## casare_rpa.infrastructure.orchestrator.robot_manager

**File:** `src\casare_rpa\infrastructure\orchestrator\robot_manager.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `available_slots` | ConnectedRobot | `self` | `int` | UNUSED |
| `status` | ConnectedRobot | `self` | `str` | UNUSED |
| `__init__` | RobotManager | `self, job_timeout_default: int` | `-` | DUNDER |
| `async _broadcast_admin` | RobotManager | `self, message: Dict[str, Any]` | `None` | INTERNAL |
| `async _try_assign_job` | RobotManager | `self, job: PendingJob` | `bool` | INTERNAL |
| `async _try_assign_job_excluding` | RobotManager | `self, job: PendingJob, excluded_robots: Set[str]` | `bool` | INTERNAL |
| `async add_admin_connection` | RobotManager | `self, websocket: WebSocket` | `None` | USED |
| `get_all_jobs` | RobotManager | `self` | `Dict[str, PendingJob]` | USED |
| `get_all_robots` | RobotManager | `self, tenant_id: Optional[str]` | `List[ConnectedRobot]` | USED |
| `get_available_robots` | RobotManager | `self, required_capabilities: Optional[List[str]], tenant_id: Optional[str]` | `List[ConnectedRobot]` | USED |
| `get_job` | RobotManager | `self, job_id: str` | `Optional[PendingJob]` | USED |
| `get_pending_jobs` | RobotManager | `self` | `List[PendingJob]` | USED |
| `get_robot` | RobotManager | `self, robot_id: str` | `Optional[ConnectedRobot]` | USED |
| `async job_completed` | RobotManager | `self, robot_id: str, job_id: str, ...` | `None` | USED |
| `async register_robot` | RobotManager | `self, websocket: WebSocket, robot_id: str, ...` | `ConnectedRobot` | USED |
| `remove_admin_connection` | RobotManager | `self, websocket: WebSocket` | `None` | USED |
| `async requeue_job` | RobotManager | `self, robot_id: str, job_id: str, ...` | `None` | USED |
| `async submit_job` | RobotManager | `self, workflow_id: str, workflow_data: Dict[str, Any], ...` | `PendingJob` | USED |
| `async unregister_robot` | RobotManager | `self, robot_id: str` | `None` | USED |
| `async update_heartbeat` | RobotManager | `self, robot_id: str, metrics: Dict[str, Any]` | `None` | USED |


## casare_rpa.infrastructure.orchestrator.scheduling

**File:** `src\casare_rpa\infrastructure\orchestrator\scheduling\__init__.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_get_scheduler_state_setter` | - | `` | `-` | INTERNAL |
| `get_global_scheduler` | - | `` | `Optional[AdvancedScheduler]` | USED |
| `async init_global_scheduler` | - | `on_schedule_trigger, default_timezone: str` | `AdvancedScheduler` | USED |
| `is_scheduler_initialized` | - | `` | `bool` | USED |
| `reset_scheduler_state` | - | `` | `None` | UNUSED |
| `set_state` | - | `instance: Optional[AdvancedScheduler], initialized: bool` | `None` | UNUSED |
| `async shutdown_global_scheduler` | - | `` | `None` | USED |


## casare_rpa.infrastructure.orchestrator.scheduling.advanced_scheduler

**File:** `src\casare_rpa\infrastructure\orchestrator\scheduling\advanced_scheduler.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | AdvancedScheduler | `self, on_schedule_trigger: Optional[Callable[[AdvancedSchedule], Any]], default_timezone: str` | `-` | DUNDER |
| `async _check_condition` | AdvancedScheduler | `self, schedule: AdvancedSchedule` | `bool` | INTERNAL |
| `_create_trigger` | AdvancedScheduler | `self, schedule: AdvancedSchedule` | `-` | INTERNAL |
| `async _execute_schedule` | AdvancedScheduler | `self, schedule_id: str, event_data: Optional[Dict[str, Any]], ...` | `None` | INTERNAL |
| `_matches_filter` | AdvancedScheduler | `self, event_data: Dict[str, Any], filter_spec: Dict[str, Any]` | `bool` | INTERNAL |
| `add_schedule` | AdvancedScheduler | `self, schedule: AdvancedSchedule` | `bool` | USED |
| `check_missed_runs` | AdvancedScheduler | `self` | `List[AdvancedSchedule]` | UNUSED |
| `dependency_tracker` | AdvancedScheduler | `self` | `DependencyTracker` | UNUSED |
| `async execute_catch_up` | AdvancedScheduler | `self, schedule_id: str` | `int` | UNUSED |
| `get_all_schedules` | AdvancedScheduler | `self` | `List[AdvancedSchedule]` | USED |
| `get_calendar` | AdvancedScheduler | `self, calendar_id: str` | `Optional[BusinessCalendar]` | USED |
| `get_dependency_graph` | AdvancedScheduler | `self` | `Dict[str, List[str]]` | UNUSED |
| `get_schedule` | AdvancedScheduler | `self, schedule_id: str` | `Optional[AdvancedSchedule]` | USED |
| `get_schedules_by_status` | AdvancedScheduler | `self, status: ScheduleStatus` | `List[AdvancedSchedule]` | UNUSED |
| `get_sla_report` | AdvancedScheduler | `self, schedule_id: Optional[str], window_hours: int` | `Dict[str, Any]` | UNUSED |
| `get_upcoming_runs` | AdvancedScheduler | `self, limit: int, workflow_id: Optional[str]` | `List[Dict[str, Any]]` | USED |
| `is_running` | AdvancedScheduler | `self` | `bool` | USED |
| `notify_completion` | AdvancedScheduler | `self, schedule_id: str, success: bool, ...` | `None` | USED |
| `pause_schedule` | AdvancedScheduler | `self, schedule_id: str` | `bool` | USED |
| `register_calendar` | AdvancedScheduler | `self, calendar_id: str, calendar: BusinessCalendar` | `None` | UNUSED |
| `remove_schedule` | AdvancedScheduler | `self, schedule_id: str` | `bool` | USED |
| `resume_schedule` | AdvancedScheduler | `self, schedule_id: str` | `bool` | USED |
| `sla_monitor` | AdvancedScheduler | `self` | `SLAMonitor` | UNUSED |
| `async start` | AdvancedScheduler | `self` | `None` | USED |
| `async stop` | AdvancedScheduler | `self, wait: bool` | `None` | USED |
| `trigger_event` | AdvancedScheduler | `self, event_type: EventType, event_source: str, ...` | `List[str]` | UNUSED |
| `update_schedule` | AdvancedScheduler | `self, schedule: AdvancedSchedule` | `bool` | USED |
| `validate_dependency_graph` | AdvancedScheduler | `self` | `Tuple[bool, List[str]]` | UNUSED |


## casare_rpa.infrastructure.orchestrator.scheduling.calendar

**File:** `src\casare_rpa\infrastructure\orchestrator\scheduling\calendar.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `is_active` | BlackoutPeriod | `self, check_time: datetime, workflow_id: Optional[str]` | `bool` | USED |
| `overlaps` | BlackoutPeriod | `self, start: datetime, end: datetime` | `bool` | UNUSED |
| `__init__` | BusinessCalendar | `self, config: Optional[CalendarConfig]` | `-` | DUNDER |
| `_get_holiday_dates` | BusinessCalendar | `self, year: int` | `Set[date]` | INTERNAL |
| `add_blackout` | BusinessCalendar | `self, blackout: BlackoutPeriod` | `None` | UNUSED |
| `add_custom_date` | BusinessCalendar | `self, d: date` | `None` | USED |
| `add_holiday` | BusinessCalendar | `self, holiday: Holiday` | `None` | UNUSED |
| `add_working_days` | BusinessCalendar | `self, start: date, days: int` | `date` | UNUSED |
| `adjust_to_working_time` | BusinessCalendar | `self, dt: datetime, workflow_id: Optional[str]` | `datetime` | USED |
| `can_execute` | BusinessCalendar | `self, dt: datetime, workflow_id: Optional[str], ...` | `Tuple[bool, Optional[str]]` | USED |
| `config` | BusinessCalendar | `self` | `CalendarConfig` | UNUSED |
| `count_working_days` | BusinessCalendar | `self, start: date, end: date` | `int` | UNUSED |
| `create_24_7_calendar` | BusinessCalendar | `cls, timezone: str, holidays: Optional[List[Holiday]]` | `'BusinessCalendar'` | UNUSED |
| `create_uk_calendar` | BusinessCalendar | `cls, timezone: str, include_bank_holidays: bool` | `'BusinessCalendar'` | UNUSED |
| `create_us_calendar` | BusinessCalendar | `cls, timezone: str, include_federal_holidays: bool` | `'BusinessCalendar'` | UNUSED |
| `from_dict` | BusinessCalendar | `cls, data: Dict[str, Any]` | `'BusinessCalendar'` | USED |
| `get_holidays_for_year` | BusinessCalendar | `self, year: int` | `List[Tuple[date, str]]` | UNUSED |
| `get_next_working_time` | BusinessCalendar | `self, from_time: Optional[datetime], workflow_id: Optional[str], ...` | `Optional[datetime]` | USED |
| `get_working_hours_remaining` | BusinessCalendar | `self, dt: datetime` | `int` | UNUSED |
| `is_custom_non_working` | BusinessCalendar | `self, d: date` | `bool` | USED |
| `is_holiday` | BusinessCalendar | `self, d: date` | `bool` | USED |
| `is_in_blackout` | BusinessCalendar | `self, dt: datetime, workflow_id: Optional[str]` | `Tuple[bool, Optional[str]]` | USED |
| `is_weekend` | BusinessCalendar | `self, d: date` | `bool` | USED |
| `is_within_working_hours` | BusinessCalendar | `self, dt: datetime` | `bool` | USED |
| `is_working_day` | BusinessCalendar | `self, d: date` | `bool` | USED |
| `remove_blackout` | BusinessCalendar | `self, name: str` | `bool` | UNUSED |
| `remove_custom_date` | BusinessCalendar | `self, d: date` | `bool` | UNUSED |
| `remove_holiday` | BusinessCalendar | `self, name: str` | `bool` | UNUSED |
| `set_working_hours` | BusinessCalendar | `self, day: DayOfWeek, hours: WorkingHours` | `None` | UNUSED |
| `timezone` | BusinessCalendar | `self` | `str` | UNUSED |
| `to_dict` | BusinessCalendar | `self` | `Dict[str, Any]` | USED |
| `__post_init__` | CalendarConfig | `self` | `-` | DUNDER |
| `from_date` | DayOfWeek | `cls, d: date` | `'DayOfWeek'` | USED |
| `_apply_observance` | Holiday | `self, d: date` | `date` | INTERNAL |
| `_calculate_floating_date` | Holiday | `self, year: int` | `Optional[date]` | INTERNAL |
| `get_date` | Holiday | `self, year: int` | `Optional[date]` | USED |
| `contains` | WorkingHours | `self, t: time` | `bool` | USED |
| `minutes_remaining` | WorkingHours | `self, from_time: time` | `int` | USED |


## casare_rpa.infrastructure.orchestrator.scheduling.job_assignment

**File:** `src\casare_rpa\infrastructure\orchestrator\scheduling\job_assignment.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `async assign_job_to_robot` | - | `job_requirements: JobRequirements, available_robots: List[RobotInfo], engine: Optional[JobAssignmentEngine], ...` | `AssignmentResult` | UNUSED |
| `__init__` | JobAssignmentEngine | `self, weights: Optional[ScoringWeights], state_ttl_seconds: int, ...` | `-` | DUNDER |
| `_calculate_cpu_penalty` | JobAssignmentEngine | `self, cpu_percent: float` | `float` | INTERNAL |
| `_calculate_job_count_penalty` | JobAssignmentEngine | `self, robot: RobotInfo` | `float` | INTERNAL |
| `_calculate_memory_penalty` | JobAssignmentEngine | `self, memory_percent: float` | `float` | INTERNAL |
| `_calculate_proximity_bonus` | JobAssignmentEngine | `self, robot: RobotInfo, orchestrator_zone: str` | `float` | INTERNAL |
| `_calculate_state_affinity_bonus` | JobAssignmentEngine | `self, requirements: JobRequirements, robot: RobotInfo` | `float` | INTERNAL |
| `_calculate_tag_bonus` | JobAssignmentEngine | `self, requirements: JobRequirements, robot: RobotInfo` | `float` | INTERNAL |
| `_filter_by_hard_constraints` | JobAssignmentEngine | `self, requirements: JobRequirements, robots: List[RobotInfo]` | `List[RobotInfo]` | INTERNAL |
| `_matches_capabilities` | JobAssignmentEngine | `self, requirements: JobRequirements, robot: RobotInfo` | `bool` | INTERNAL |
| `_meets_resource_requirements` | JobAssignmentEngine | `self, requirements: JobRequirements, robot: RobotInfo` | `bool` | INTERNAL |
| `_score_robots` | JobAssignmentEngine | `self, requirements: JobRequirements, robots: List[RobotInfo], ...` | `List[Tuple[RobotInfo, float, Dict[str, float]]]` | INTERNAL |
| `assign_job` | JobAssignmentEngine | `self, requirements: JobRequirements, available_robots: List[RobotInfo], ...` | `AssignmentResult` | USED |
| `cleanup_expired_state` | JobAssignmentEngine | `self` | `int` | UNUSED |
| `clear_state_affinity` | JobAssignmentEngine | `self, workflow_id: str, robot_id: Optional[str]` | `None` | UNUSED |
| `get_assignment_stats` | JobAssignmentEngine | `self` | `Dict[str, Any]` | UNUSED |
| `record_job_completion` | JobAssignmentEngine | `self, workflow_id: str, robot_id: str, ...` | `None` | UNUSED |
| `weights` | JobAssignmentEngine | `self` | `ScoringWeights` | UNUSED |
| `weights` | JobAssignmentEngine | `self, value: ScoringWeights` | `None` | UNUSED |
| `__init__` | NoCapableRobotError | `self, job_name: str, required_capabilities: Optional[List[str]]` | `-` | DUNDER |
| `_version_satisfies` | RobotCapability | `self, have: str, need: str` | `bool` | INTERNAL |
| `matches` | RobotCapability | `self, required: 'RobotCapability'` | `bool` | USED |
| `_parse_capabilities` | RobotInfo | `self` | `List[RobotCapability]` | INTERNAL |
| `has_capability` | RobotInfo | `self, capability: RobotCapability` | `bool` | USED |
| `is_available` | RobotInfo | `self` | `bool` | UNUSED |
| `utilization` | RobotInfo | `self` | `float` | UNUSED |
| `capabilities` | RobotPresenceProtocol | `self` | `Dict[str, Any]` | UNUSED |
| `cpu_percent` | RobotPresenceProtocol | `self` | `float` | USED |
| `current_jobs` | RobotPresenceProtocol | `self` | `int` | UNUSED |
| `environment` | RobotPresenceProtocol | `self` | `str` | UNUSED |
| `max_concurrent_jobs` | RobotPresenceProtocol | `self` | `int` | UNUSED |
| `memory_percent` | RobotPresenceProtocol | `self` | `float` | USED |
| `name` | RobotPresenceProtocol | `self` | `str` | USED |
| `robot_id` | RobotPresenceProtocol | `self` | `str` | UNUSED |
| `status` | RobotPresenceProtocol | `self` | `str` | UNUSED |
| `tags` | RobotPresenceProtocol | `self` | `List[str]` | UNUSED |
| `__init__` | StateAffinityTracker | `self, state_ttl_seconds: int` | `-` | DUNDER |
| `cleanup_expired` | StateAffinityTracker | `self` | `int` | USED |
| `clear_state` | StateAffinityTracker | `self, workflow_id: str, robot_id: Optional[str]` | `None` | USED |
| `get_robots_with_state` | StateAffinityTracker | `self, workflow_id: str` | `List[str]` | USED |
| `has_state` | StateAffinityTracker | `self, workflow_id: str, robot_id: str` | `bool` | USED |
| `record_state` | StateAffinityTracker | `self, workflow_id: str, robot_id: str` | `None` | USED |


## casare_rpa.infrastructure.orchestrator.scheduling.schedule_conflict_resolver

**File:** `src\casare_rpa\infrastructure\orchestrator\scheduling\schedule_conflict_resolver.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ConflictResolver | `self` | `-` | DUNDER |
| `acquire_resource` | ConflictResolver | `self, schedule_id: str, resource_id: str, ...` | `bool` | UNUSED |
| `get_resource_holders` | ConflictResolver | `self, resource_id: str` | `Set[str]` | UNUSED |
| `has_conflict` | ConflictResolver | `self, schedule_id: str, required_resources: List[str], ...` | `Tuple[bool, List[str]]` | UNUSED |
| `release_all_resources` | ConflictResolver | `self, schedule_id: str` | `None` | UNUSED |
| `release_resource` | ConflictResolver | `self, schedule_id: str, resource_id: str` | `None` | UNUSED |
| `__init__` | DependencyGraphValidator | `self` | `-` | DUNDER |
| `build_graph_from_dependencies` | DependencyGraphValidator | `self, dependencies: Dict[str, DependencyConfig]` | `None` | UNUSED |
| `get_all_downstream` | DependencyGraphValidator | `self, schedule_id: str` | `Set[str]` | UNUSED |
| `get_all_upstream` | DependencyGraphValidator | `self, schedule_id: str` | `Set[str]` | UNUSED |
| `get_dependents` | DependencyGraphValidator | `self, schedule_id: str` | `List[str]` | USED |
| `get_execution_order` | DependencyGraphValidator | `self` | `List[str]` | UNUSED |
| `has_cycle` | DependencyGraphValidator | `node: str, path: List[str]` | `bool` | USED |
| `set_graph` | DependencyGraphValidator | `self, graph: Dict[str, List[str]]` | `None` | USED |
| `validate` | DependencyGraphValidator | `self` | `Tuple[bool, List[str]]` | USED |
| `__init__` | DependencyTracker | `self, ttl_seconds: int` | `-` | DUNDER |
| `_cleanup_old` | DependencyTracker | `self, schedule_id: str` | `None` | INTERNAL |
| `are_dependencies_satisfied` | DependencyTracker | `self, dependency_ids: List[str], wait_for_all: bool, ...` | `Tuple[bool, List[str]]` | USED |
| `clear_history` | DependencyTracker | `self, schedule_id: Optional[str]` | `None` | USED |
| `get_completion_history` | DependencyTracker | `self, schedule_id: str, limit: int, ...` | `List[CompletionRecord]` | UNUSED |
| `get_latest_completion` | DependencyTracker | `self, schedule_id: str` | `Optional[CompletionRecord]` | UNUSED |
| `is_dependency_satisfied` | DependencyTracker | `self, dependency_id: str, since: Optional[datetime], ...` | `bool` | USED |
| `record_completion` | DependencyTracker | `self, schedule_id: str, success: bool, ...` | `None` | USED |
| `async wait_for_dependencies` | DependencyTracker | `self, dependency_ids: List[str], wait_for_all: bool, ...` | `Tuple[bool, List[str]]` | UNUSED |
| `async wait_for_dependency` | DependencyTracker | `self, dependency_id: str, timeout_seconds: int` | `bool` | USED |


## casare_rpa.infrastructure.orchestrator.scheduling.schedule_models

**File:** `src\casare_rpa\infrastructure\orchestrator\scheduling\schedule_models.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `sla_status` | AdvancedSchedule | `self` | `SLAStatus` | UNUSED |
| `success_rate` | AdvancedSchedule | `self` | `float` | UNUSED |


## casare_rpa.infrastructure.orchestrator.scheduling.schedule_optimizer

**File:** `src\casare_rpa\infrastructure\orchestrator\scheduling\schedule_optimizer.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ExecutionOptimizer | `self, coalesce_window_ms: int, max_concurrent_executions: int` | `-` | DUNDER |
| `active_count` | ExecutionOptimizer | `self` | `int` | UNUSED |
| `can_start_execution` | ExecutionOptimizer | `self` | `bool` | UNUSED |
| `get_active_executions` | ExecutionOptimizer | `self` | `List[Dict[str, datetime]]` | UNUSED |
| `get_execution_duration` | ExecutionOptimizer | `self, schedule_id: str` | `Optional[timedelta]` | UNUSED |
| `mark_completed` | ExecutionOptimizer | `self, schedule_id: str` | `None` | USED |
| `mark_pending` | ExecutionOptimizer | `self, schedule_id: str` | `None` | UNUSED |
| `mark_started` | ExecutionOptimizer | `self, schedule_id: str` | `bool` | UNUSED |
| `should_coalesce` | ExecutionOptimizer | `self, schedule_id: str` | `bool` | UNUSED |
| `__init__` | PriorityQueue | `self` | `-` | DUNDER |
| `clear` | PriorityQueue | `self` | `None` | USED |
| `dequeue` | PriorityQueue | `self` | `Optional[str]` | USED |
| `enqueue` | PriorityQueue | `self, schedule_id: str, priority: int` | `None` | USED |
| `peek` | PriorityQueue | `self` | `Optional[str]` | UNUSED |
| `remove` | PriorityQueue | `self, schedule_id: str` | `bool` | USED |
| `size` | PriorityQueue | `self` | `int` | USED |
| `size_by_priority` | PriorityQueue | `self` | `Dict[int, int]` | UNUSED |
| `__init__` | SlidingWindowRateLimiter | `self, max_executions: int, window_seconds: int` | `-` | DUNDER |
| `_cleanup_old_entries` | SlidingWindowRateLimiter | `self, schedule_id: str` | `None` | INTERNAL |
| `can_execute` | SlidingWindowRateLimiter | `self, schedule_id: str` | `bool` | USED |
| `get_execution_count` | SlidingWindowRateLimiter | `self, schedule_id: str` | `int` | USED |
| `get_remaining_capacity` | SlidingWindowRateLimiter | `self, schedule_id: str` | `int` | UNUSED |
| `get_wait_time` | SlidingWindowRateLimiter | `self, schedule_id: str` | `int` | USED |
| `max_executions` | SlidingWindowRateLimiter | `self` | `int` | UNUSED |
| `record_execution` | SlidingWindowRateLimiter | `self, schedule_id: str` | `None` | USED |
| `reset` | SlidingWindowRateLimiter | `self, schedule_id: Optional[str]` | `None` | USED |
| `window_seconds` | SlidingWindowRateLimiter | `self` | `int` | UNUSED |


## casare_rpa.infrastructure.orchestrator.scheduling.scheduling_strategies

**File:** `src\casare_rpa\infrastructure\orchestrator\scheduling\scheduling_strategies.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_alias_to_description` | CronExpressionParser | `cls, alias: str` | `str` | INTERNAL |
| `_build_description` | CronExpressionParser | `cls, parts: Dict[str, str]` | `str` | INTERNAL |
| `get_available_aliases` | CronExpressionParser | `cls` | `Dict[str, str]` | UNUSED |
| `parse` | CronExpressionParser | `cls, expression: str` | `Dict[str, str]` | USED |
| `to_human_readable` | CronExpressionParser | `cls, expression: str` | `str` | USED |
| `validate` | CronExpressionParser | `cls, expression: str` | `Tuple[bool, Optional[str]]` | USED |
| `__init__` | CronSchedulingStrategy | `self, cron_expression: str, timezone: str` | `-` | DUNDER |
| `expression` | CronSchedulingStrategy | `self` | `str` | UNUSED |
| `get_next_run_time` | CronSchedulingStrategy | `self, current_time: datetime, last_run: Optional[datetime]` | `Optional[datetime]` | UNUSED |
| `get_parsed` | CronSchedulingStrategy | `self` | `Dict[str, str]` | UNUSED |
| `timezone` | CronSchedulingStrategy | `self` | `str` | UNUSED |
| `to_human_readable` | CronSchedulingStrategy | `self` | `str` | USED |
| `validate` | CronSchedulingStrategy | `self` | `Tuple[bool, Optional[str]]` | USED |
| `__init__` | DependencySchedulingStrategy | `self, depends_on: list, wait_for_all: bool, ...` | `-` | DUNDER |
| `depends_on` | DependencySchedulingStrategy | `self` | `list` | UNUSED |
| `get_next_run_time` | DependencySchedulingStrategy | `self, current_time: datetime, last_run: Optional[datetime]` | `Optional[datetime]` | UNUSED |
| `to_human_readable` | DependencySchedulingStrategy | `self` | `str` | USED |
| `trigger_on_success_only` | DependencySchedulingStrategy | `self` | `bool` | UNUSED |
| `validate` | DependencySchedulingStrategy | `self` | `Tuple[bool, Optional[str]]` | USED |
| `wait_for_all` | DependencySchedulingStrategy | `self` | `bool` | UNUSED |
| `__init__` | EventDrivenStrategy | `self, event_type: str, event_source: str, ...` | `-` | DUNDER |
| `event_filter` | EventDrivenStrategy | `self` | `Dict[str, Any]` | UNUSED |
| `event_source` | EventDrivenStrategy | `self` | `str` | UNUSED |
| `event_type` | EventDrivenStrategy | `self` | `str` | UNUSED |
| `get_next_run_time` | EventDrivenStrategy | `self, current_time: datetime, last_run: Optional[datetime]` | `Optional[datetime]` | UNUSED |
| `to_human_readable` | EventDrivenStrategy | `self` | `str` | USED |
| `validate` | EventDrivenStrategy | `self` | `Tuple[bool, Optional[str]]` | USED |
| `__init__` | IntervalSchedulingStrategy | `self, interval_seconds: int, timezone: str` | `-` | DUNDER |
| `get_next_run_time` | IntervalSchedulingStrategy | `self, current_time: datetime, last_run: Optional[datetime]` | `Optional[datetime]` | UNUSED |
| `interval_seconds` | IntervalSchedulingStrategy | `self` | `int` | UNUSED |
| `timezone` | IntervalSchedulingStrategy | `self` | `str` | UNUSED |
| `to_human_readable` | IntervalSchedulingStrategy | `self` | `str` | USED |
| `validate` | IntervalSchedulingStrategy | `self` | `Tuple[bool, Optional[str]]` | USED |
| `__init__` | OneTimeSchedulingStrategy | `self, run_at: datetime, timezone: str` | `-` | DUNDER |
| `get_next_run_time` | OneTimeSchedulingStrategy | `self, current_time: datetime, last_run: Optional[datetime]` | `Optional[datetime]` | UNUSED |
| `mark_executed` | OneTimeSchedulingStrategy | `self` | `None` | UNUSED |
| `run_at` | OneTimeSchedulingStrategy | `self` | `datetime` | UNUSED |
| `timezone` | OneTimeSchedulingStrategy | `self` | `str` | UNUSED |
| `to_human_readable` | OneTimeSchedulingStrategy | `self` | `str` | USED |
| `validate` | OneTimeSchedulingStrategy | `self` | `Tuple[bool, Optional[str]]` | USED |
| `get_next_run_time` | SchedulingStrategy | `self, current_time: datetime, last_run: Optional[datetime]` | `Optional[datetime]` | UNUSED |
| `validate` | SchedulingStrategy | `self` | `Tuple[bool, Optional[str]]` | USED |


## casare_rpa.infrastructure.orchestrator.scheduling.sla_monitor

**File:** `src\casare_rpa\infrastructure\orchestrator\scheduling\sla_monitor.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | SLAAggregator | `self, sla_monitor: SLAMonitor` | `-` | DUNDER |
| `get_fleet_status_summary` | SLAAggregator | `self, schedule_configs: Dict[str, SLAConfig], window_hours: int` | `Dict[SLAStatus, int]` | UNUSED |
| `get_fleet_success_rate` | SLAAggregator | `self, schedule_ids: List[str], window_hours: int` | `float` | UNUSED |
| `get_slowest_performers` | SLAAggregator | `self, schedule_ids: List[str], limit: int, ...` | `List[Dict[str, Any]]` | UNUSED |
| `get_worst_performers` | SLAAggregator | `self, schedule_ids: List[str], limit: int, ...` | `List[Dict[str, Any]]` | UNUSED |
| `__init__` | SLAMonitor | `self, metrics_retention_limit: int` | `-` | DUNDER |
| `_check_sla` | SLAMonitor | `self, metrics: ExecutionMetrics, sla: SLAConfig` | `None` | INTERNAL |
| `add_alert_callback` | SLAMonitor | `self, callback: Callable[[str, SLAStatus, str], None]` | `None` | UNUSED |
| `clear_metrics` | SLAMonitor | `self, schedule_id: Optional[str]` | `None` | UNUSED |
| `generate_report` | SLAMonitor | `self, schedule_id: str, schedule_name: str, ...` | `SLAReport` | UNUSED |
| `get_active_executions` | SLAMonitor | `self` | `Dict[str, ExecutionMetrics]` | UNUSED |
| `get_average_duration` | SLAMonitor | `self, schedule_id: str, window_hours: int` | `int` | USED |
| `get_execution_count` | SLAMonitor | `self, schedule_id: str, window_hours: int` | `int` | USED |
| `get_failure_rate` | SLAMonitor | `self, schedule_id: str, window_hours: int` | `float` | UNUSED |
| `get_metrics` | SLAMonitor | `self, schedule_id: str, since: Optional[datetime], ...` | `List[ExecutionMetrics]` | USED |
| `get_percentile_duration` | SLAMonitor | `self, schedule_id: str, percentile: float, ...` | `int` | UNUSED |
| `get_sla_status` | SLAMonitor | `self, schedule_id: str, sla_config: SLAConfig, ...` | `SLAStatus` | USED |
| `get_success_rate` | SLAMonitor | `self, schedule_id: str, window_hours: int` | `float` | USED |
| `record_completion` | SLAMonitor | `self, execution_id: str, success: bool, ...` | `Optional[ExecutionMetrics]` | USED |
| `record_error` | SLAMonitor | `self, execution_id: str, error_message: str, ...` | `Optional[ExecutionMetrics]` | USED |
| `record_start` | SLAMonitor | `self, schedule_id: str, scheduled_time: Optional[datetime], ...` | `str` | USED |
| `remove_alert_callback` | SLAMonitor | `self, callback: Callable[[str, SLAStatus, str], None]` | `bool` | UNUSED |


## casare_rpa.infrastructure.orchestrator.scheduling.state_affinity

**File:** `src\casare_rpa\infrastructure\orchestrator\scheduling\state_affinity.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `age_seconds` | RobotState | `self` | `float` | UNUSED |
| `idle_seconds` | RobotState | `self` | `float` | UNUSED |
| `is_expired` | RobotState | `self` | `bool` | USED |
| `to_dict` | RobotState | `self` | `Dict[str, Any]` | USED |
| `touch` | RobotState | `self` | `None` | USED |
| `__init__` | SessionAffinityError | `self, message: str, workflow_id: str, ...` | `-` | DUNDER |
| `__init__` | StateAffinityManager | `self, default_state_ttl_seconds: float, session_timeout_seconds: float, ...` | `-` | DUNDER |
| `_cleanup_expired` | StateAffinityManager | `self` | `Tuple[int, int]` | INTERNAL |
| `async _cleanup_loop` | StateAffinityManager | `self` | `None` | INTERNAL |
| `_score_and_select` | StateAffinityManager | `self, candidates: List[str], robot_scorer: Optional[Callable[[str], float]]` | `Optional[str]` | INTERNAL |
| `_select_hard_affinity` | StateAffinityManager | `self, workflow_id: str, available_robots: List[str], ...` | `StateAffinityDecision` | INTERNAL |
| `_select_no_affinity` | StateAffinityManager | `self, available_robots: List[str], robots_with_state: List[str], ...` | `StateAffinityDecision` | INTERNAL |
| `_select_session_affinity` | StateAffinityManager | `self, workflow_id: str, available_robots: List[str], ...` | `StateAffinityDecision` | INTERNAL |
| `_select_soft_affinity` | StateAffinityManager | `self, workflow_id: str, available_robots: List[str], ...` | `StateAffinityDecision` | INTERNAL |
| `clear_queue_attempts` | StateAffinityManager | `self, job_id: str` | `None` | UNUSED |
| `create_session` | StateAffinityManager | `self, session_id: str, workflow_id: str, ...` | `WorkflowSession` | UNUSED |
| `end_session` | StateAffinityManager | `self, workflow_id: str` | `bool` | UNUSED |
| `get_all_state_for_workflow` | StateAffinityManager | `self, workflow_id: str` | `Dict[str, List[RobotState]]` | UNUSED |
| `get_robots_with_state` | StateAffinityManager | `self, workflow_id: str` | `List[str]` | USED |
| `get_session` | StateAffinityManager | `self, workflow_id: str` | `Optional[WorkflowSession]` | USED |
| `get_session_robot` | StateAffinityManager | `self, workflow_id: str` | `Optional[str]` | UNUSED |
| `get_state_for_robot` | StateAffinityManager | `self, robot_id: str, workflow_id: str` | `List[RobotState]` | USED |
| `get_statistics` | StateAffinityManager | `self` | `Dict[str, Any]` | USED |
| `get_workflow_state_summary` | StateAffinityManager | `self, workflow_id: str` | `Dict[str, Any]` | UNUSED |
| `has_state_for` | StateAffinityManager | `self, robot_id: str, workflow_id: str` | `bool` | USED |
| `async migrate_state` | StateAffinityManager | `self, workflow_id: str, source_robot: str, ...` | `Tuple[int, int]` | UNUSED |
| `record_session_job` | StateAffinityManager | `self, workflow_id: str` | `None` | UNUSED |
| `register_migration_handler` | StateAffinityManager | `self, state_type: str, handler: Callable[[str, str, RobotState], Any]` | `None` | UNUSED |
| `register_state` | StateAffinityManager | `self, robot_id: str, workflow_id: str, ...` | `RobotState` | USED |
| `select_robot` | StateAffinityManager | `self, workflow_id: str, affinity_level: StateAffinityLevel, ...` | `StateAffinityDecision` | USED |
| `async start` | StateAffinityManager | `self` | `None` | USED |
| `async stop` | StateAffinityManager | `self` | `None` | USED |
| `touch_state` | StateAffinityManager | `self, robot_id: str, workflow_id: str` | `None` | UNUSED |
| `unregister_state` | StateAffinityManager | `self, robot_id: str, workflow_id: str, ...` | `int` | USED |
| `is_expired` | WorkflowSession | `self` | `bool` | USED |
| `record_job` | WorkflowSession | `self` | `None` | USED |


## casare_rpa.infrastructure.orchestrator.server

**File:** `src\casare_rpa\infrastructure\orchestrator\server.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `create_app` | - | `` | `FastAPI` | UNUSED |
| `main` | - | `` | `None` | USED |


## casare_rpa.infrastructure.orchestrator.server_auth

**File:** `src\casare_rpa\infrastructure\orchestrator\server_auth.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `async validate_admin_secret` | - | `secret: Optional[str]` | `bool` | USED |
| `async validate_websocket_api_key` | - | `api_key: Optional[str]` | `Optional[str]` | USED |
| `async verify_admin_api_key` | - | `x_api_key: str` | `str` | UNUSED |
| `async verify_api_key` | - | `x_api_key: str` | `str` | UNUSED |


## casare_rpa.infrastructure.orchestrator.server_lifecycle

**File:** `src\casare_rpa\infrastructure\orchestrator\server_lifecycle.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `async _cleanup_services` | - | `` | `None` | INTERNAL |
| `_get_state` | - | `` | `OrchestratorState` | INTERNAL |
| `async _init_database` | - | `config: OrchestratorConfig` | `None` | INTERNAL |
| `async _init_log_services` | - | `db_pool: Any` | `None` | INTERNAL |
| `_set_state_field` | - | `field_name: str, value: Any` | `None` | INTERNAL |
| `get_config` | - | `` | `OrchestratorConfig` | USED |
| `get_db_pool` | - | `` | `Any` | USED |
| `get_log_cleanup_job` | - | `` | `Any` | USED |
| `get_log_repository` | - | `` | `Any` | USED |
| `get_log_streaming_service` | - | `` | `Any` | USED |
| `get_robot_manager` | - | `` | `RobotManager` | USED |
| `async lifespan` | - | `app: FastAPI` | `-` | UNUSED |
| `reset_orchestrator_state` | - | `` | `None` | UNUSED |
| `from_env` | OrchestratorConfig | `cls` | `'OrchestratorConfig'` | USED |


## casare_rpa.infrastructure.orchestrator.websocket_handlers

**File:** `src\casare_rpa\infrastructure\orchestrator\websocket_handlers.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `async admin_websocket` | - | `websocket: WebSocket, api_secret: Optional[str]` | `-` | UNUSED |
| `async all_logs_stream_websocket` | - | `websocket: WebSocket, api_secret: Optional[str], tenant_id: Optional[str], ...` | `-` | UNUSED |
| `async log_stream_websocket` | - | `websocket: WebSocket, robot_id: str, api_secret: Optional[str], ...` | `-` | UNUSED |
| `async robot_websocket` | - | `websocket: WebSocket, robot_id: str, api_key: Optional[str]` | `-` | UNUSED |


## casare_rpa.infrastructure.persistence.file_system_project_repository

**File:** `src\casare_rpa\infrastructure\persistence\file_system_project_repository.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | FileSystemProjectRepository | `self` | `None` | DUNDER |
| `_invalidate_cache` | FileSystemProjectRepository | `self` | `None` | INTERNAL |
| `async delete` | FileSystemProjectRepository | `self, project_id: str, remove_files: bool` | `None` | USED |
| `async delete_scenario` | FileSystemProjectRepository | `self, project_id: str, scenario_id: str` | `None` | USED |
| `async exists` | FileSystemProjectRepository | `self, project_id: str` | `bool` | USED |
| `async get_all` | FileSystemProjectRepository | `self` | `List[Project]` | USED |
| `async get_by_id` | FileSystemProjectRepository | `self, project_id: str` | `Optional[Project]` | USED |
| `async get_by_path` | FileSystemProjectRepository | `self, path: Path` | `Optional[Project]` | USED |
| `async get_global_credentials` | FileSystemProjectRepository | `self` | `CredentialBindingsFile` | UNUSED |
| `async get_global_variables` | FileSystemProjectRepository | `self` | `VariablesFile` | USED |
| `async get_project_credentials` | FileSystemProjectRepository | `self, project_id: str` | `CredentialBindingsFile` | UNUSED |
| `async get_project_variables` | FileSystemProjectRepository | `self, project_id: str` | `VariablesFile` | USED |
| `async get_projects_index` | FileSystemProjectRepository | `self` | `ProjectsIndex` | USED |
| `async get_scenario` | FileSystemProjectRepository | `self, project_id: str, scenario_id: str` | `Optional[Scenario]` | USED |
| `async get_scenarios` | FileSystemProjectRepository | `self, project_id: str` | `List[Scenario]` | USED |
| `async save` | FileSystemProjectRepository | `self, project: Project` | `None` | USED |
| `async save_global_credentials` | FileSystemProjectRepository | `self, credentials: CredentialBindingsFile` | `None` | USED |
| `async save_global_variables` | FileSystemProjectRepository | `self, variables: VariablesFile` | `None` | USED |
| `async save_project_credentials` | FileSystemProjectRepository | `self, project_id: str, credentials: CredentialBindingsFile` | `None` | USED |
| `async save_project_variables` | FileSystemProjectRepository | `self, project_id: str, variables: VariablesFile` | `None` | USED |
| `async save_projects_index` | FileSystemProjectRepository | `self, index: ProjectsIndex` | `None` | USED |
| `async save_scenario` | FileSystemProjectRepository | `self, project_id: str, scenario: Scenario` | `None` | USED |
| `async update_project_opened` | FileSystemProjectRepository | `self, project_id: str` | `None` | USED |


## casare_rpa.infrastructure.persistence.project_storage

**File:** `src\casare_rpa\infrastructure\persistence\project_storage.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `create_project_structure` | ProjectStorage | `path: Path` | `None` | USED |
| `delete_project` | ProjectStorage | `project: Project, remove_files: bool` | `None` | USED |
| `is_project_folder` | ProjectStorage | `path: Path` | `bool` | USED |
| `list_scenario_files` | ProjectStorage | `project: Project` | `List[Path]` | USED |
| `load_global_credentials` | ProjectStorage | `` | `CredentialBindingsFile` | USED |
| `load_global_variables` | ProjectStorage | `` | `VariablesFile` | USED |
| `load_project` | ProjectStorage | `path: Path` | `Project` | USED |
| `load_project_credentials` | ProjectStorage | `project: Project` | `CredentialBindingsFile` | USED |
| `load_project_variables` | ProjectStorage | `project: Project` | `VariablesFile` | USED |
| `load_projects_index` | ProjectStorage | `` | `ProjectsIndex` | USED |
| `load_workflow` | ProjectStorage | `file_path: Path, validate_on_load: bool, strict: bool` | `'WorkflowSchema'` | UNUSED |
| `save_global_credentials` | ProjectStorage | `credentials: CredentialBindingsFile` | `None` | USED |
| `save_global_variables` | ProjectStorage | `variables: VariablesFile` | `None` | USED |
| `save_project` | ProjectStorage | `project: Project` | `None` | USED |
| `save_project_credentials` | ProjectStorage | `project: Project, credentials: CredentialBindingsFile` | `None` | USED |
| `save_project_variables` | ProjectStorage | `project: Project, variables: VariablesFile` | `None` | USED |
| `save_projects_index` | ProjectStorage | `index: ProjectsIndex` | `None` | USED |
| `save_workflow` | ProjectStorage | `workflow: 'WorkflowSchema', file_path: Path, validate_before_save: bool` | `None` | USED |


## casare_rpa.infrastructure.persistence.repositories.api_key_repository

**File:** `src\casare_rpa\infrastructure\persistence\repositories\api_key_repository.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ApiKeyRepository | `self, pool_manager: Optional[DatabasePoolManager]` | `None` | DUNDER |
| `async _get_connection` | ApiKeyRepository | `self` | `-` | INTERNAL |
| `async _get_pool` | ApiKeyRepository | `self` | `-` | INTERNAL |
| `async _release_connection` | ApiKeyRepository | `self, conn` | `None` | INTERNAL |
| `_row_to_api_key` | ApiKeyRepository | `self, row: Dict[str, Any]` | `RobotApiKey` | INTERNAL |
| `async count_for_robot` | ApiKeyRepository | `self, robot_id: str, active_only: bool` | `int` | UNUSED |
| `async delete` | ApiKeyRepository | `self, key_id: str` | `bool` | USED |
| `async delete_expired` | ApiKeyRepository | `self, days_old: int` | `int` | UNUSED |
| `async get_by_hash` | ApiKeyRepository | `self, api_key_hash: str` | `Optional[RobotApiKey]` | UNUSED |
| `async get_by_id` | ApiKeyRepository | `self, key_id: str` | `Optional[RobotApiKey]` | USED |
| `async get_robot_id_by_hash` | ApiKeyRepository | `self, api_key_hash: str` | `Optional[str]` | UNUSED |
| `async get_valid_by_hash` | ApiKeyRepository | `self, api_key_hash: str` | `Optional[RobotApiKey]` | UNUSED |
| `async list_all` | ApiKeyRepository | `self, include_revoked: bool, limit: int, ...` | `List[RobotApiKey]` | UNUSED |
| `async list_for_robot` | ApiKeyRepository | `self, robot_id: str, include_revoked: bool` | `List[RobotApiKey]` | UNUSED |
| `async revoke` | ApiKeyRepository | `self, key_id: str, revoked_by: Optional[str], ...` | `bool` | UNUSED |
| `async revoke_all_for_robot` | ApiKeyRepository | `self, robot_id: str, revoked_by: Optional[str], ...` | `int` | UNUSED |
| `async save` | ApiKeyRepository | `self, robot_id: str, api_key_hash: str, ...` | `RobotApiKey` | USED |
| `async update_last_used` | ApiKeyRepository | `self, api_key_hash: str, client_ip: Optional[str]` | `None` | UNUSED |


## casare_rpa.infrastructure.persistence.repositories.job_repository

**File:** `src\casare_rpa\infrastructure\persistence\repositories\job_repository.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | JobRepository | `self, pool_manager: Optional[DatabasePoolManager]` | `None` | DUNDER |
| `async _get_connection` | JobRepository | `self` | `-` | INTERNAL |
| `async _get_pool` | JobRepository | `self` | `-` | INTERNAL |
| `_job_to_params` | JobRepository | `self, job: Job` | `Dict[str, Any]` | INTERNAL |
| `async _release_connection` | JobRepository | `self, conn` | `None` | INTERNAL |
| `_row_to_job` | JobRepository | `self, row: Dict[str, Any]` | `Job` | INTERNAL |
| `async append_logs` | JobRepository | `self, job_id: str, log_entry: str` | `None` | UNUSED |
| `async calculate_duration` | JobRepository | `self, job_id: str` | `None` | UNUSED |
| `async claim_next_job` | JobRepository | `self, robot_id: str` | `Optional[Job]` | UNUSED |
| `async delete` | JobRepository | `self, job_id: str` | `bool` | USED |
| `async delete_old_jobs` | JobRepository | `self, days: int` | `int` | UNUSED |
| `async get_by_id` | JobRepository | `self, job_id: str` | `Optional[Job]` | USED |
| `async get_by_robot` | JobRepository | `self, robot_id: str` | `List[Job]` | USED |
| `async get_by_status` | JobRepository | `self, status: JobStatus` | `List[Job]` | USED |
| `async get_by_workflow` | JobRepository | `self, workflow_id: str` | `List[Job]` | USED |
| `async get_pending` | JobRepository | `self` | `List[Job]` | UNUSED |
| `async get_pending_for_robot` | JobRepository | `self, robot_id: str` | `List[Job]` | UNUSED |
| `async get_queued` | JobRepository | `self` | `List[Job]` | UNUSED |
| `async get_running` | JobRepository | `self` | `List[Job]` | UNUSED |
| `async save` | JobRepository | `self, job: Job` | `Job` | USED |
| `async update_progress` | JobRepository | `self, job_id: str, progress: int, ...` | `None` | USED |
| `async update_status` | JobRepository | `self, job_id: str, status: JobStatus, ...` | `None` | USED |


## casare_rpa.infrastructure.persistence.repositories.log_repository

**File:** `src\casare_rpa\infrastructure\persistence\repositories\log_repository.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | LogRepository | `self, pool_manager: Optional[DatabasePoolManager]` | `None` | DUNDER |
| `async _get_connection` | LogRepository | `self` | `-` | INTERNAL |
| `async _get_pool` | LogRepository | `self` | `-` | INTERNAL |
| `async _release_connection` | LogRepository | `self, conn` | `None` | INTERNAL |
| `_row_to_entry` | LogRepository | `self, row: Dict[str, Any]` | `LogEntry` | INTERNAL |
| `async cleanup_old_logs` | LogRepository | `self, retention_days: int` | `Dict[str, Any]` | USED |
| `async ensure_partitions` | LogRepository | `self, months_ahead: int` | `List[Dict[str, str]]` | USED |
| `async get_by_robot` | LogRepository | `self, robot_id: str, tenant_id: str, ...` | `List[LogEntry]` | USED |
| `async get_cleanup_history` | LogRepository | `self, limit: int` | `List[Dict[str, Any]]` | UNUSED |
| `async get_stats` | LogRepository | `self, tenant_id: str, robot_id: Optional[str]` | `LogStats` | USED |
| `async query` | LogRepository | `self, query: LogQuery` | `List[LogEntry]` | USED |
| `async save` | LogRepository | `self, entry: LogEntry` | `LogEntry` | USED |
| `async save_batch` | LogRepository | `self, entries: List[LogEntry]` | `int` | USED |


## casare_rpa.infrastructure.persistence.repositories.node_override_repository

**File:** `src\casare_rpa\infrastructure\persistence\repositories\node_override_repository.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | NodeOverrideRepository | `self, pool_manager: Optional[DatabasePoolManager]` | `None` | DUNDER |
| `async _get_connection` | NodeOverrideRepository | `self` | `-` | INTERNAL |
| `async _get_pool` | NodeOverrideRepository | `self` | `-` | INTERNAL |
| `_override_to_params` | NodeOverrideRepository | `self, override: NodeRobotOverride` | `Dict[str, Any]` | INTERNAL |
| `async _release_connection` | NodeOverrideRepository | `self, conn` | `None` | INTERNAL |
| `_row_to_override` | NodeOverrideRepository | `self, row: Dict[str, Any]` | `NodeRobotOverride` | INTERNAL |
| `async activate` | NodeOverrideRepository | `self, workflow_id: str, node_id: str` | `bool` | USED |
| `async deactivate` | NodeOverrideRepository | `self, workflow_id: str, node_id: str` | `bool` | USED |
| `async delete` | NodeOverrideRepository | `self, workflow_id: str, node_id: str` | `bool` | USED |
| `async delete_all_for_robot` | NodeOverrideRepository | `self, robot_id: str` | `int` | USED |
| `async delete_all_for_workflow` | NodeOverrideRepository | `self, workflow_id: str` | `int` | UNUSED |
| `async get_active_for_workflow` | NodeOverrideRepository | `self, workflow_id: str` | `List[NodeRobotOverride]` | USED |
| `async get_by_capability` | NodeOverrideRepository | `self, capability: RobotCapability` | `List[NodeRobotOverride]` | USED |
| `async get_by_node` | NodeOverrideRepository | `self, workflow_id: str, node_id: str` | `Optional[NodeRobotOverride]` | UNUSED |
| `async get_by_robot` | NodeOverrideRepository | `self, robot_id: str` | `List[NodeRobotOverride]` | USED |
| `async get_by_workflow` | NodeOverrideRepository | `self, workflow_id: str` | `List[NodeRobotOverride]` | USED |
| `async get_override_map` | NodeOverrideRepository | `self, workflow_id: str` | `Dict[str, NodeRobotOverride]` | UNUSED |
| `async save` | NodeOverrideRepository | `self, override: NodeRobotOverride` | `NodeRobotOverride` | USED |


## casare_rpa.infrastructure.persistence.repositories.robot_repository

**File:** `src\casare_rpa\infrastructure\persistence\repositories\robot_repository.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | RobotRepository | `self, pool_manager: Optional[DatabasePoolManager]` | `None` | DUNDER |
| `async _get_connection` | RobotRepository | `self` | `-` | INTERNAL |
| `async _get_pool` | RobotRepository | `self` | `-` | INTERNAL |
| `async _release_connection` | RobotRepository | `self, conn` | `None` | INTERNAL |
| `_robot_to_params` | RobotRepository | `self, robot: Robot` | `Dict[str, Any]` | INTERNAL |
| `_row_to_robot` | RobotRepository | `self, row: Dict[str, Any]` | `Robot` | INTERNAL |
| `async add_current_job` | RobotRepository | `self, robot_id: str, job_id: str` | `None` | UNUSED |
| `async delete` | RobotRepository | `self, robot_id: str` | `bool` | USED |
| `async get_all` | RobotRepository | `self` | `List[Robot]` | USED |
| `async get_available` | RobotRepository | `self` | `List[Robot]` | USED |
| `async get_by_capabilities` | RobotRepository | `self, capabilities: Set[RobotCapability]` | `List[Robot]` | USED |
| `async get_by_capability` | RobotRepository | `self, capability: RobotCapability` | `List[Robot]` | USED |
| `async get_by_hostname` | RobotRepository | `self, hostname: str` | `Optional[Robot]` | USED |
| `async get_by_id` | RobotRepository | `self, robot_id: str` | `Optional[Robot]` | USED |
| `async get_by_status` | RobotRepository | `self, status: RobotStatus` | `List[Robot]` | USED |
| `async mark_stale_robots_offline` | RobotRepository | `self, timeout_seconds: int` | `int` | UNUSED |
| `async remove_current_job` | RobotRepository | `self, robot_id: str, job_id: str` | `None` | UNUSED |
| `async save` | RobotRepository | `self, robot: Robot` | `Robot` | USED |
| `async update_heartbeat` | RobotRepository | `self, robot_id: str` | `None` | USED |
| `async update_metrics` | RobotRepository | `self, robot_id: str, metrics: Dict[str, Any]` | `None` | USED |
| `async update_status` | RobotRepository | `self, robot_id: str, status: RobotStatus` | `None` | USED |


## casare_rpa.infrastructure.persistence.repositories.tenant_repository

**File:** `src\casare_rpa\infrastructure\persistence\repositories\tenant_repository.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | TenantRepository | `self, pool_manager: Optional[DatabasePoolManager]` | `None` | DUNDER |
| `async _get_connection` | TenantRepository | `self` | `-` | INTERNAL |
| `async _get_pool` | TenantRepository | `self` | `-` | INTERNAL |
| `async _release_connection` | TenantRepository | `self, conn` | `None` | INTERNAL |
| `_row_to_tenant` | TenantRepository | `self, row: Dict[str, Any]` | `Tenant` | INTERNAL |
| `_tenant_to_params` | TenantRepository | `self, tenant: Tenant` | `Dict[str, Any]` | INTERNAL |
| `async add_robot_to_tenant` | TenantRepository | `self, tenant_id: str, robot_id: str` | `bool` | UNUSED |
| `async count` | TenantRepository | `self, include_inactive: bool` | `int` | USED |
| `async delete` | TenantRepository | `self, tenant_id: str, hard_delete: bool` | `bool` | USED |
| `async get_all` | TenantRepository | `self, include_inactive: bool, limit: int, ...` | `List[Tenant]` | USED |
| `async get_by_admin_email` | TenantRepository | `self, email: str` | `List[Tenant]` | UNUSED |
| `async get_by_id` | TenantRepository | `self, tenant_id: str` | `Optional[Tenant]` | USED |
| `async get_by_name` | TenantRepository | `self, name: str` | `Optional[Tenant]` | UNUSED |
| `async get_by_robot_id` | TenantRepository | `self, robot_id: str` | `Optional[Tenant]` | UNUSED |
| `async get_statistics` | TenantRepository | `self` | `Dict[str, Any]` | USED |
| `async remove_robot_from_tenant` | TenantRepository | `self, tenant_id: str, robot_id: str` | `bool` | UNUSED |
| `async save` | TenantRepository | `self, tenant: Tenant` | `Tenant` | USED |


## casare_rpa.infrastructure.persistence.repositories.user_repository

**File:** `src\casare_rpa\infrastructure\persistence\repositories\user_repository.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | UserRepository | `self, pool` | `None` | DUNDER |
| `async _get_connection` | UserRepository | `self` | `-` | INTERNAL |
| `async _get_pool` | UserRepository | `self` | `-` | INTERNAL |
| `async _get_user_roles` | UserRepository | `self, conn, user_id: str` | `Dict[str, Any]` | INTERNAL |
| `async _record_failed_login` | UserRepository | `self, conn, user_id` | `None` | INTERNAL |
| `async _record_successful_login` | UserRepository | `self, conn, user_id` | `None` | INTERNAL |
| `async _release_connection` | UserRepository | `self, conn` | `None` | INTERNAL |
| `async create_user` | UserRepository | `self, email: str, password: str, ...` | `Optional[str]` | UNUSED |
| `async exists` | UserRepository | `self, email: str` | `bool` | USED |
| `async get_by_email` | UserRepository | `self, email: str` | `Optional[Dict[str, Any]]` | UNUSED |
| `async get_by_id` | UserRepository | `self, user_id: str` | `Optional[Dict[str, Any]]` | USED |
| `hash_password` | UserRepository | `password: str` | `str` | USED |
| `async update_password` | UserRepository | `self, user_id: str, new_password: str` | `bool` | UNUSED |
| `async validate_credentials` | UserRepository | `self, username: str, password: str` | `Optional[Dict[str, Any]]` | USED |
| `verify_password` | UserRepository | `password: str, password_hash: str` | `bool` | USED |


## casare_rpa.infrastructure.persistence.repositories.workflow_assignment_repository

**File:** `src\casare_rpa\infrastructure\persistence\repositories\workflow_assignment_repository.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | WorkflowAssignmentRepository | `self, pool_manager: Optional[DatabasePoolManager]` | `None` | DUNDER |
| `_assignment_to_params` | WorkflowAssignmentRepository | `self, assignment: RobotAssignment` | `Dict[str, Any]` | INTERNAL |
| `async _get_connection` | WorkflowAssignmentRepository | `self` | `-` | INTERNAL |
| `async _get_pool` | WorkflowAssignmentRepository | `self` | `-` | INTERNAL |
| `async _release_connection` | WorkflowAssignmentRepository | `self, conn` | `None` | INTERNAL |
| `_row_to_assignment` | WorkflowAssignmentRepository | `self, row: Dict[str, Any]` | `RobotAssignment` | INTERNAL |
| `async delete` | WorkflowAssignmentRepository | `self, workflow_id: str, robot_id: str` | `bool` | USED |
| `async delete_all_for_robot` | WorkflowAssignmentRepository | `self, robot_id: str` | `int` | USED |
| `async delete_all_for_workflow` | WorkflowAssignmentRepository | `self, workflow_id: str` | `int` | UNUSED |
| `async get_assignment` | WorkflowAssignmentRepository | `self, workflow_id: str, robot_id: str` | `Optional[RobotAssignment]` | USED |
| `async get_by_robot` | WorkflowAssignmentRepository | `self, robot_id: str` | `List[RobotAssignment]` | USED |
| `async get_by_workflow` | WorkflowAssignmentRepository | `self, workflow_id: str` | `List[RobotAssignment]` | USED |
| `async get_default_for_workflow` | WorkflowAssignmentRepository | `self, workflow_id: str` | `Optional[RobotAssignment]` | USED |
| `async get_workflows_for_robot` | WorkflowAssignmentRepository | `self, robot_id: str` | `List[str]` | UNUSED |
| `async save` | WorkflowAssignmentRepository | `self, assignment: RobotAssignment` | `RobotAssignment` | USED |
| `async set_default` | WorkflowAssignmentRepository | `self, workflow_id: str, robot_id: str` | `None` | USED |


## casare_rpa.infrastructure.persistence.setup_db

**File:** `src\casare_rpa\infrastructure\persistence\setup_db.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `async apply_migration` | - | `conn: asyncpg.Connection, migration_file: Path` | `bool` | USED |
| `async get_db_connection` | - | `` | `-` | USED |
| `main` | - | `` | `-` | USED |
| `async setup_database` | - | `` | `-` | USED |
| `async verify_setup` | - | `` | `-` | USED |


## casare_rpa.infrastructure.persistence.template_storage

**File:** `src\casare_rpa\infrastructure\persistence\template_storage.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | TemplateStorage | `self, builtin_dir: Path, user_dir: Path` | `None` | DUNDER |
| `_ensure_directories` | TemplateStorage | `self` | `None` | INTERNAL |
| `_invalidate_cache` | TemplateStorage | `self` | `None` | INTERNAL |
| `_load_all_templates` | TemplateStorage | `self` | `None` | INTERNAL |
| `_load_template_file` | TemplateStorage | `self, file_path: Path` | `Optional[WorkflowTemplate]` | INTERNAL |
| `_scan_directory` | TemplateStorage | `self, directory: Path, is_builtin: bool` | `List[WorkflowTemplate]` | INTERNAL |
| `async delete` | TemplateStorage | `self, template_id: str` | `bool` | USED |
| `async exists` | TemplateStorage | `self, template_id: str` | `bool` | USED |
| `async export_template` | TemplateStorage | `self, template_id: str` | `Optional[bytes]` | UNUSED |
| `async get_all` | TemplateStorage | `self` | `List[WorkflowTemplate]` | USED |
| `async get_builtin` | TemplateStorage | `self` | `List[WorkflowTemplate]` | UNUSED |
| `async get_by_category` | TemplateStorage | `self, category: TemplateCategory` | `List[WorkflowTemplate]` | USED |
| `async get_by_id` | TemplateStorage | `self, template_id: str` | `Optional[WorkflowTemplate]` | USED |
| `async get_category_counts` | TemplateStorage | `self` | `Dict[str, int]` | UNUSED |
| `async get_user_templates` | TemplateStorage | `self` | `List[WorkflowTemplate]` | UNUSED |
| `async import_template` | TemplateStorage | `self, json_data: bytes, overwrite: bool` | `WorkflowTemplate` | UNUSED |
| `reload` | TemplateStorage | `self` | `None` | USED |
| `async save` | TemplateStorage | `self, template: WorkflowTemplate` | `None` | USED |
| `async search` | TemplateStorage | `self, query: str, category: Optional[TemplateCategory], ...` | `List[WorkflowTemplate]` | USED |
| `create_default` | TemplateStorageFactory | `` | `TemplateStorage` | USED |
| `create_for_project` | TemplateStorageFactory | `project_path: Path` | `TemplateStorage` | UNUSED |


## casare_rpa.infrastructure.queue.dlq_manager

**File:** `src\casare_rpa\infrastructure\queue\dlq_manager.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_json_dumps` | - | `data: Any` | `str` | INTERNAL |
| `_json_dumps` | - | `data: Any` | `str` | INTERNAL |
| `_row_to_dlq_entry` | - | `row: Any` | `DLQEntry` | INTERNAL |
| `to_dict` | DLQEntry | `self` | `Dict[str, Any]` | USED |
| `async __aenter__` | DLQManager | `self` | `'DLQManager'` | DUNDER |
| `async __aexit__` | DLQManager | `self, exc_type: Any, exc_val: Any, ...` | `bool` | DUNDER |
| `__init__` | DLQManager | `self, config: DLQManagerConfig` | `None` | DUNDER |
| `async _ensure_dlq_table` | DLQManager | `self` | `None` | INTERNAL |
| `_get_pool` | DLQManager | `self` | `DatabasePool` | INTERNAL |
| `async _move_to_dlq` | DLQManager | `self, job: FailedJob, first_failed_at: datetime, ...` | `RetryResult` | INTERNAL |
| `async _schedule_retry` | DLQManager | `self, job: FailedJob, first_failed_at: datetime, ...` | `RetryResult` | INTERNAL |
| `calculate_backoff_delay` | DLQManager | `self, retry_count: int` | `Tuple[int, int]` | USED |
| `async get_dlq_entry` | DLQManager | `self, entry_id: str` | `Optional[DLQEntry]` | UNUSED |
| `async get_dlq_stats` | DLQManager | `self, workflow_id: Optional[str]` | `Dict[str, int]` | UNUSED |
| `async handle_job_failure` | DLQManager | `self, job: FailedJob` | `RetryResult` | UNUSED |
| `is_running` | DLQManager | `self` | `bool` | USED |
| `async list_dlq_entries` | DLQManager | `self, workflow_id: Optional[str], pending_only: bool, ...` | `List[DLQEntry]` | UNUSED |
| `max_retries` | DLQManager | `self` | `int` | UNUSED |
| `async purge_reprocessed` | DLQManager | `self, older_than_days: int` | `int` | UNUSED |
| `async retry_from_dlq` | DLQManager | `self, entry_id: str, reprocessed_by: str` | `Optional[str]` | UNUSED |
| `async start` | DLQManager | `self` | `None` | USED |
| `async stop` | DLQManager | `self` | `None` | USED |
| `async execute` | DatabaseConnection | `self, query: str` | `str` | USED |
| `async fetch` | DatabaseConnection | `self, query: str` | `List[Any]` | USED |
| `async fetchrow` | DatabaseConnection | `self, query: str` | `Optional[Any]` | USED |
| `transaction` | DatabaseConnection | `self` | `AsyncContextManager[Any]` | USED |
| `acquire` | DatabasePool | `self` | `AsyncContextManager[DatabaseConnection]` | USED |
| `async close` | DatabasePool | `self` | `None` | USED |
| `to_dict` | FailedJob | `self` | `Dict[str, Any]` | USED |


## casare_rpa.infrastructure.queue.memory_queue

**File:** `src\casare_rpa\infrastructure\queue\memory_queue.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `get_memory_queue` | - | `visibility_timeout: int` | `MemoryQueue` | USED |
| `async initialize_memory_queue` | - | `` | `MemoryQueue` | UNUSED |
| `async shutdown_memory_queue` | - | `` | `None` | UNUSED |
| `to_dict` | MemoryJob | `self` | `Dict[str, Any]` | USED |
| `__init__` | MemoryQueue | `self, visibility_timeout: int` | `-` | DUNDER |
| `async _cleanup_expired_claims` | MemoryQueue | `self` | `None` | INTERNAL |
| `async claim` | MemoryQueue | `self, robot_id: str, execution_mode: Optional[str]` | `Optional[MemoryJob]` | UNUSED |
| `async enqueue` | MemoryQueue | `self, workflow_id: str, workflow_json: Dict[str, Any], ...` | `str` | USED |
| `async extend_claim` | MemoryQueue | `self, job_id: str` | `bool` | UNUSED |
| `async get_job` | MemoryQueue | `self, job_id: str` | `Optional[MemoryJob]` | USED |
| `async get_jobs_by_robot` | MemoryQueue | `self, robot_id: str, limit: int` | `List[MemoryJob]` | UNUSED |
| `async get_jobs_by_status` | MemoryQueue | `self, status: JobStatus, limit: int` | `List[MemoryJob]` | UNUSED |
| `async get_queue_depth` | MemoryQueue | `self, execution_mode: Optional[str]` | `int` | USED |
| `async start` | MemoryQueue | `self` | `None` | USED |
| `async stop` | MemoryQueue | `self` | `None` | USED |
| `async update_status` | MemoryQueue | `self, job_id: str, status: JobStatus, ...` | `bool` | USED |


## casare_rpa.infrastructure.queue.pgqueuer_consumer

**File:** `src\casare_rpa\infrastructure\queue\pgqueuer_consumer.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `to_dict` | ClaimedJob | `self` | `Dict[str, Any]` | USED |
| `to_dict` | ConsumerConfig | `self` | `Dict[str, Any]` | USED |
| `async __aenter__` | PgQueuerConsumer | `self` | `'PgQueuerConsumer'` | DUNDER |
| `async __aexit__` | PgQueuerConsumer | `self, exc_type: Optional[type[BaseException]], exc_val: Optional[BaseException], ...` | `bool` | DUNDER |
| `__init__` | PgQueuerConsumer | `self, config: ConsumerConfig` | `None` | DUNDER |
| `async _connect` | PgQueuerConsumer | `self` | `bool` | INTERNAL |
| `async _ensure_connection` | PgQueuerConsumer | `self` | `bool` | INTERNAL |
| `async _execute_with_retry` | PgQueuerConsumer | `self, query: str` | `DatabaseRecordList` | INTERNAL |
| `async _heartbeat_loop` | PgQueuerConsumer | `self` | `None` | INTERNAL |
| `async _reconnect` | PgQueuerConsumer | `self` | `bool` | INTERNAL |
| `async _release_all_active_jobs` | PgQueuerConsumer | `self` | `None` | INTERNAL |
| `_set_state` | PgQueuerConsumer | `self, new_state: ConnectionState` | `None` | INTERNAL |
| `active_job_count` | PgQueuerConsumer | `self` | `int` | UNUSED |
| `add_state_callback` | PgQueuerConsumer | `self, callback: StateChangeCallback` | `None` | UNUSED |
| `async claim_batch` | PgQueuerConsumer | `self, limit: Optional[int]` | `List[ClaimedJob]` | USED |
| `async claim_job` | PgQueuerConsumer | `self` | `Optional[ClaimedJob]` | USED |
| `async complete_job` | PgQueuerConsumer | `self, job_id: JobId, result: Optional[Dict[str, Any]]` | `bool` | USED |
| `async extend_lease` | PgQueuerConsumer | `self, job_id: JobId, extension_seconds: Optional[int]` | `bool` | USED |
| `async fail_job` | PgQueuerConsumer | `self, job_id: JobId, error_message: str` | `tuple[bool, bool]` | USED |
| `async get_job_status` | PgQueuerConsumer | `self, job_id: JobId` | `Optional[JobStatusInfo]` | UNUSED |
| `get_stats` | PgQueuerConsumer | `self` | `ConsumerStats` | USED |
| `is_connected` | PgQueuerConsumer | `self` | `bool` | USED |
| `async release_job` | PgQueuerConsumer | `self, job_id: JobId` | `bool` | USED |
| `remove_state_callback` | PgQueuerConsumer | `self, callback: StateChangeCallback` | `None` | UNUSED |
| `async requeue_timed_out_jobs` | PgQueuerConsumer | `self` | `int` | UNUSED |
| `robot_id` | PgQueuerConsumer | `self` | `str` | UNUSED |
| `async start` | PgQueuerConsumer | `self` | `bool` | USED |
| `state` | PgQueuerConsumer | `self` | `ConnectionState` | UNUSED |
| `async stop` | PgQueuerConsumer | `self` | `None` | USED |


## casare_rpa.infrastructure.queue.pgqueuer_producer

**File:** `src\casare_rpa\infrastructure\queue\pgqueuer_producer.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `to_dict` | EnqueuedJob | `self` | `Dict[str, Any]` | USED |
| `__post_init__` | JobSubmission | `self` | `None` | DUNDER |
| `async __aenter__` | PgQueuerProducer | `self` | `'PgQueuerProducer'` | DUNDER |
| `async __aexit__` | PgQueuerProducer | `self, exc_type: Optional[type[BaseException]], exc_val: Optional[BaseException], ...` | `bool` | DUNDER |
| `__init__` | PgQueuerProducer | `self, config: ProducerConfig` | `None` | DUNDER |
| `async _connect` | PgQueuerProducer | `self` | `bool` | INTERNAL |
| `async _ensure_connection` | PgQueuerProducer | `self` | `bool` | INTERNAL |
| `async _execute_with_retry` | PgQueuerProducer | `self, query: str` | `DatabaseRecordList` | INTERNAL |
| `async _reconnect` | PgQueuerProducer | `self` | `bool` | INTERNAL |
| `_set_state` | PgQueuerProducer | `self, new_state: ProducerConnectionState` | `None` | INTERNAL |
| `add_state_callback` | PgQueuerProducer | `self, callback: StateChangeCallback` | `None` | UNUSED |
| `async cancel_job` | PgQueuerProducer | `self, job_id: JobId, reason: str` | `bool` | UNUSED |
| `async enqueue_batch` | PgQueuerProducer | `self, submissions: List[JobSubmission]` | `List[EnqueuedJob]` | UNUSED |
| `async enqueue_job` | PgQueuerProducer | `self, workflow_id: WorkflowId, workflow_name: str, ...` | `EnqueuedJob` | USED |
| `async get_job_status` | PgQueuerProducer | `self, job_id: JobId` | `Optional[JobDetailedStatus]` | UNUSED |
| `async get_queue_depth_by_priority` | PgQueuerProducer | `self` | `Dict[int, int]` | UNUSED |
| `async get_queue_stats` | PgQueuerProducer | `self` | `QueueStats` | USED |
| `get_stats` | PgQueuerProducer | `self` | `ProducerStats` | USED |
| `is_connected` | PgQueuerProducer | `self` | `bool` | USED |
| `async purge_old_jobs` | PgQueuerProducer | `self, days_old: int` | `int` | UNUSED |
| `remove_state_callback` | PgQueuerProducer | `self, callback: StateChangeCallback` | `None` | UNUSED |
| `async start` | PgQueuerProducer | `self` | `bool` | USED |
| `state` | PgQueuerProducer | `self` | `ProducerConnectionState` | UNUSED |
| `async stop` | PgQueuerProducer | `self` | `None` | USED |
| `total_cancelled` | PgQueuerProducer | `self` | `int` | UNUSED |
| `total_enqueued` | PgQueuerProducer | `self` | `int` | UNUSED |
| `to_dict` | ProducerConfig | `self` | `Dict[str, Any]` | USED |


## casare_rpa.infrastructure.queue.types

**File:** `src\casare_rpa\infrastructure\queue\types.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__call__` | HeartbeatCallback | `self, job_ids: List[str]` | `None` | DUNDER |
| `__call__` | JobClaimedCallback | `self, job: ClaimedJobPayload` | `None` | DUNDER |
| `__call__` | JobCompletedCallback | `self, job_id: str, result: JobResult` | `None` | DUNDER |
| `__call__` | JobFailedCallback | `self, job_id: str, error: str, ...` | `None` | DUNDER |
| `__call__` | StateChangeCallback | `self, new_state: Any` | `None` | DUNDER |


## casare_rpa.infrastructure.realtime.supabase_realtime

**File:** `src\casare_rpa\infrastructure\realtime\supabase_realtime.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `from_broadcast` | ControlCommandPayload | `cls, payload: Dict[str, Any]` | `'ControlCommandPayload'` | USED |
| `from_postgres_change` | JobInsertedPayload | `cls, payload: Dict[str, Any]` | `'JobInsertedPayload'` | USED |
| `get_busy_robots` | PresenceState | `self` | `List[RobotPresenceInfo]` | USED |
| `get_idle_robots` | PresenceState | `self` | `List[RobotPresenceInfo]` | USED |
| `get_robot_by_id` | PresenceState | `self, robot_id: str` | `Optional[RobotPresenceInfo]` | UNUSED |
| `async __aenter__` | RealtimeClient | `self` | `'RealtimeClient'` | DUNDER |
| `async __aexit__` | RealtimeClient | `self, exc_type: Any, exc_val: Any, ...` | `bool` | DUNDER |
| `__init__` | RealtimeClient | `self, config: RealtimeConfig` | `None` | DUNDER |
| `_handle_cancel_job_broadcast` | RealtimeClient | `self, payload: Dict[str, Any]` | `None` | INTERNAL |
| `_handle_control_command` | RealtimeClient | `self, command: str, payload: Dict[str, Any]` | `None` | INTERNAL |
| `_handle_job_inserted` | RealtimeClient | `self, payload: Dict[str, Any]` | `None` | INTERNAL |
| `_handle_pause_broadcast` | RealtimeClient | `self, payload: Dict[str, Any]` | `None` | INTERNAL |
| `_handle_presence_join` | RealtimeClient | `self, new_presences: Dict[str, Any]` | `None` | INTERNAL |
| `_handle_presence_leave` | RealtimeClient | `self, left_presences: Dict[str, Any]` | `None` | INTERNAL |
| `_handle_presence_sync` | RealtimeClient | `self` | `None` | INTERNAL |
| `_handle_resume_broadcast` | RealtimeClient | `self, payload: Dict[str, Any]` | `None` | INTERNAL |
| `_handle_shutdown_broadcast` | RealtimeClient | `self, payload: Dict[str, Any]` | `None` | INTERNAL |
| `_parse_presence_list` | RealtimeClient | `self, presences: Dict[str, Any]` | `List[RobotPresenceInfo]` | INTERNAL |
| `async _presence_update_loop` | RealtimeClient | `self` | `None` | INTERNAL |
| `async _reconnect` | RealtimeClient | `self` | `bool` | INTERNAL |
| `async _safe_callback` | RealtimeClient | `self, callback: Callable[[T], Awaitable[None]], payload: T` | `None` | INTERNAL |
| `_set_state` | RealtimeClient | `self, new_state: RealtimeConnectionState` | `None` | INTERNAL |
| `async _setup_control_channel` | RealtimeClient | `self` | `bool` | INTERNAL |
| `async _setup_jobs_channel` | RealtimeClient | `self` | `bool` | INTERNAL |
| `async _setup_presence_channel` | RealtimeClient | `self` | `bool` | INTERNAL |
| `async _start_reconnect_monitor` | RealtimeClient | `self` | `None` | INTERNAL |
| `_update_presence_state` | RealtimeClient | `self, raw_state: Dict[str, Any]` | `None` | INTERNAL |
| `async connect` | RealtimeClient | `self` | `bool` | USED |
| `async disconnect` | RealtimeClient | `self` | `None` | USED |
| `get_status` | RealtimeClient | `self` | `Dict[str, Any]` | USED |
| `is_connected` | RealtimeClient | `self` | `bool` | USED |
| `on_connection_state` | RealtimeClient | `self, callback: ConnectionStateCallback` | `None` | UNUSED |
| `on_control_command` | RealtimeClient | `self, callback: ControlCommandCallback` | `None` | UNUSED |
| `on_job_inserted` | RealtimeClient | `self, callback: JobInsertCallback` | `None` | UNUSED |
| `on_presence_join` | RealtimeClient | `self, callback: PresenceJoinCallback` | `None` | USED |
| `on_presence_leave` | RealtimeClient | `self, callback: PresenceLeaveCallback` | `None` | USED |
| `on_presence_sync` | RealtimeClient | `self, callback: PresenceSyncCallback` | `None` | USED |
| `presence_state` | RealtimeClient | `self` | `PresenceState` | USED |
| `async send_broadcast` | RealtimeClient | `self, event: str, payload: Dict[str, Any], ...` | `bool` | USED |
| `async send_heartbeat` | RealtimeClient | `self, job_id: str, progress_percent: int, ...` | `bool` | USED |
| `state` | RealtimeClient | `self` | `RealtimeConnectionState` | UNUSED |
| `async subscribe_all` | RealtimeClient | `self` | `bool` | USED |
| `subscription_manager` | RealtimeClient | `self` | `SubscriptionManager` | UNUSED |
| `async track_presence` | RealtimeClient | `self, info: RobotPresenceInfo` | `bool` | USED |
| `async wait_for_job_notification` | RealtimeClient | `self, timeout: float` | `bool` | USED |
| `get_realtime_url` | RealtimeConfig | `self` | `str` | USED |
| `to_dict` | RobotPresenceInfo | `self` | `Dict[str, Any]` | USED |
| `__init__` | SubscriptionManager | `self` | `None` | DUNDER |
| `get_all_states` | SubscriptionManager | `self` | `Dict[str, ChannelState]` | USED |
| `get_state` | SubscriptionManager | `self, name: str` | `ChannelState` | USED |
| `is_subscribed` | SubscriptionManager | `self, name: str` | `bool` | USED |
| `on_subscribe` | SubscriptionManager | `status: Any, err: Optional[Exception]` | `None` | UNUSED |
| `register_channel` | SubscriptionManager | `self, name: str, channel: Any, ...` | `None` | USED |
| `async subscribe_channel` | SubscriptionManager | `self, name: str` | `bool` | USED |
| `async unsubscribe_all` | SubscriptionManager | `self` | `None` | USED |
| `async unsubscribe_channel` | SubscriptionManager | `self, name: str` | `bool` | USED |


## casare_rpa.infrastructure.resources.browser_resource_manager

**File:** `src\casare_rpa\infrastructure\resources\browser_resource_manager.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | BrowserResourceManager | `self` | `None` | DUNDER |
| `__repr__` | BrowserResourceManager | `self` | `str` | DUNDER |
| `add_browser_context` | BrowserResourceManager | `self, context: 'BrowserContext'` | `None` | USED |
| `add_page` | BrowserResourceManager | `self, page: 'Page', name: str` | `None` | USED |
| `async cleanup` | BrowserResourceManager | `self, skip_browser: bool` | `None` | USED |
| `clear_pages` | BrowserResourceManager | `self` | `None` | USED |
| `close_page` | BrowserResourceManager | `self, name: str` | `None` | USED |
| `get_active_page` | BrowserResourceManager | `self` | `Optional['Page']` | USED |
| `get_browser` | BrowserResourceManager | `self` | `Optional['Browser']` | USED |
| `get_browser_contexts` | BrowserResourceManager | `self` | `List['BrowserContext']` | UNUSED |
| `get_page` | BrowserResourceManager | `self, name: str` | `Optional['Page']` | USED |
| `set_active_page` | BrowserResourceManager | `self, page: 'Page', name: str` | `None` | USED |
| `set_browser` | BrowserResourceManager | `self, browser: 'Browser'` | `None` | USED |
| `set_page` | BrowserResourceManager | `self, page: 'Page', name: str, ...` | `None` | UNUSED |


## casare_rpa.infrastructure.resources.document_ai_manager

**File:** `src\casare_rpa\infrastructure\resources\document_ai_manager.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | DocumentAIManager | `self` | `None` | DUNDER |
| `__repr__` | DocumentAIManager | `self` | `str` | DUNDER |
| `async _encode_document` | DocumentAIManager | `self, document: str | bytes` | `Tuple[str, str]` | INTERNAL |
| `_get_llm_manager` | DocumentAIManager | `self` | `LLMResourceManager` | INTERNAL |
| `async classify_document` | DocumentAIManager | `self, document: str | bytes, categories: Optional[List[str]], ...` | `DocumentClassification` | USED |
| `async cleanup` | DocumentAIManager | `self` | `None` | USED |
| `configure` | DocumentAIManager | `self, config: LLMConfig` | `None` | USED |
| `async extract_form` | DocumentAIManager | `self, document: str | bytes, field_schema: Dict[str, str], ...` | `ExtractionResult` | USED |
| `async extract_invoice` | DocumentAIManager | `self, document: str | bytes, custom_fields: Optional[List[str]], ...` | `ExtractionResult` | USED |
| `async extract_table` | DocumentAIManager | `self, document: str | bytes, table_hint: Optional[str], ...` | `TableExtractionResult` | USED |
| `validate_extraction` | DocumentAIManager | `self, extraction: Dict[str, Any], required_fields: List[str], ...` | `ValidationResult` | USED |


## casare_rpa.infrastructure.resources.gmail_client

**File:** `src\casare_rpa\infrastructure\resources\gmail_client.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | GmailAPIError | `self, message: str, error_code: Optional[int], ...` | `-` | DUNDER |
| `async __aenter__` | GmailClient | `self` | `'GmailClient'` | DUNDER |
| `async __aexit__` | GmailClient | `self, exc_type, exc_val, ...` | `None` | DUNDER |
| `__init__` | GmailClient | `self, config: GmailConfig` | `-` | DUNDER |
| `async _create_attachment_part` | GmailClient | `self, attachment: Union[str, Path, dict]` | `Optional[MIMEBase]` | INTERNAL |
| `async _create_message` | GmailClient | `self, to: list[str], subject: str, ...` | `str` | INTERNAL |
| `async _ensure_session` | GmailClient | `self` | `aiohttp.ClientSession` | INTERNAL |
| `_guess_mime_type` | GmailClient | `self, path: Path` | `str` | INTERNAL |
| `async _request` | GmailClient | `self, method: str, endpoint: str, ...` | `dict` | INTERNAL |
| `async close` | GmailClient | `self` | `None` | USED |
| `async create_draft` | GmailClient | `self, to: list[str], subject: str, ...` | `GmailDraft` | USED |
| `async delete_message` | GmailClient | `self, message_id: str` | `None` | USED |
| `async forward_message` | GmailClient | `self, message_id: str, to: list[str], ...` | `GmailMessage` | USED |
| `async get_attachment` | GmailClient | `self, message_id: str, attachment_id: str` | `bytes` | USED |
| `async get_labels` | GmailClient | `self` | `list[dict]` | UNUSED |
| `async get_message` | GmailClient | `self, message_id: str, format_type: str` | `GmailMessage` | USED |
| `async get_thread` | GmailClient | `self, thread_id: str, format_type: str` | `GmailThread` | USED |
| `async modify_labels` | GmailClient | `self, message_id: str, add_labels: Optional[list[str]], ...` | `GmailMessage` | UNUSED |
| `async reply_to_message` | GmailClient | `self, message_id: str, thread_id: str, ...` | `GmailMessage` | USED |
| `async search_messages` | GmailClient | `self, query: str, max_results: int, ...` | `tuple[list[GmailMessage], Optional[str]]` | USED |
| `async send_message` | GmailClient | `self, to: list[str], subject: str, ...` | `GmailMessage` | USED |
| `async trash_message` | GmailClient | `self, message_id: str` | `GmailMessage` | UNUSED |
| `async untrash_message` | GmailClient | `self, message_id: str` | `GmailMessage` | UNUSED |
| `users_url` | GmailConfig | `self` | `str` | UNUSED |
| `from_response` | GmailDraft | `cls, data: dict` | `'GmailDraft'` | USED |
| `_parse_addresses` | GmailMessage | `addr_string: str` | `list[str]` | INTERNAL |
| `_parse_payload` | GmailMessage | `payload: dict` | `tuple[str, str, list[dict]]` | INTERNAL |
| `from_response` | GmailMessage | `cls, data: dict` | `'GmailMessage'` | USED |
| `from_response` | GmailThread | `cls, data: dict` | `'GmailThread'` | USED |


## casare_rpa.infrastructure.resources.google_calendar_client

**File:** `src\casare_rpa\infrastructure\resources\google_calendar_client.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `from_response` | Calendar | `cls, data: dict` | `'Calendar'` | USED |
| `to_dict` | Calendar | `self` | `dict` | USED |
| `from_response` | CalendarEvent | `cls, data: dict, calendar_id: str` | `'CalendarEvent'` | USED |
| `to_dict` | CalendarEvent | `self` | `dict` | USED |
| `from_response` | FreeBusyInfo | `cls, calendar_id: str, data: dict` | `'FreeBusyInfo'` | USED |
| `__init__` | GoogleCalendarAPIError | `self, message: str, error_code: Optional[int], ...` | `-` | DUNDER |
| `async __aenter__` | GoogleCalendarClient | `self` | `'GoogleCalendarClient'` | DUNDER |
| `async __aexit__` | GoogleCalendarClient | `self, exc_type, exc_val, ...` | `None` | DUNDER |
| `__init__` | GoogleCalendarClient | `self, config: CalendarConfig` | `-` | DUNDER |
| `async _ensure_session` | GoogleCalendarClient | `self` | `aiohttp.ClientSession` | INTERNAL |
| `_format_datetime` | GoogleCalendarClient | `self, dt: datetime` | `str` | INTERNAL |
| `async _request` | GoogleCalendarClient | `self, method: str, endpoint: str, ...` | `dict` | INTERNAL |
| `async close` | GoogleCalendarClient | `self` | `None` | USED |
| `async create_calendar` | GoogleCalendarClient | `self, summary: str, description: Optional[str], ...` | `Calendar` | USED |
| `async create_event` | GoogleCalendarClient | `self, calendar_id: str, summary: str, ...` | `CalendarEvent` | USED |
| `async delete_calendar` | GoogleCalendarClient | `self, calendar_id: str` | `bool` | USED |
| `async delete_event` | GoogleCalendarClient | `self, calendar_id: str, event_id: str, ...` | `bool` | USED |
| `async get_calendar` | GoogleCalendarClient | `self, calendar_id: str` | `Calendar` | USED |
| `async get_event` | GoogleCalendarClient | `self, calendar_id: str, event_id: str` | `CalendarEvent` | USED |
| `async get_free_busy` | GoogleCalendarClient | `self, calendar_ids: List[str], time_min: datetime, ...` | `dict[str, FreeBusyInfo]` | USED |
| `async list_calendars` | GoogleCalendarClient | `self, min_access_role: Optional[str], show_deleted: bool, ...` | `List[Calendar]` | USED |
| `async list_events` | GoogleCalendarClient | `self, calendar_id: str, time_min: Optional[datetime], ...` | `tuple[List[CalendarEvent], Optional[str]]` | USED |
| `async move_event` | GoogleCalendarClient | `self, calendar_id: str, event_id: str, ...` | `CalendarEvent` | USED |
| `async quick_add_event` | GoogleCalendarClient | `self, calendar_id: str, text: str, ...` | `CalendarEvent` | USED |
| `async update_event` | GoogleCalendarClient | `self, calendar_id: str, event_id: str, ...` | `CalendarEvent` | USED |


## casare_rpa.infrastructure.resources.google_client

**File:** `src\casare_rpa\infrastructure\resources\google_client.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `async create_google_client` | - | `credentials: Optional[Dict[str, Any]], service_account_file: Optional[str], service_account_info: Optional[Dict[str, Any]], ...` | `GoogleAPIClient` | UNUSED |
| `async __aenter__` | GoogleAPIClient | `self` | `'GoogleAPIClient'` | DUNDER |
| `async __aexit__` | GoogleAPIClient | `self, exc_type, exc_val, ...` | `None` | DUNDER |
| `__init__` | GoogleAPIClient | `self, config: GoogleConfig` | `-` | DUNDER |
| `async _authenticate_service_account_file` | GoogleAPIClient | `self, scopes: List[str]` | `None` | INTERNAL |
| `async _authenticate_service_account_info` | GoogleAPIClient | `self, info: Dict[str, Any], scopes: List[str]` | `None` | INTERNAL |
| `async _ensure_session` | GoogleAPIClient | `self` | `aiohttp.ClientSession` | INTERNAL |
| `async _ensure_valid_token` | GoogleAPIClient | `self` | `str` | INTERNAL |
| `_extract_retry_after` | GoogleAPIClient | `self, error: Exception` | `Optional[int]` | INTERNAL |
| `async authenticate` | GoogleAPIClient | `self, scopes: Optional[List[str]], credentials: Optional[Dict[str, Any]]` | `None` | USED |
| `batch_callback` | GoogleAPIClient | `request_id, response, exception` | `-` | UNUSED |
| `async close` | GoogleAPIClient | `self` | `None` | USED |
| `credentials` | GoogleAPIClient | `self` | `Optional[GoogleCredentials]` | UNUSED |
| `async execute_batch` | GoogleAPIClient | `self, requests: List[Any], callback: Optional[Any]` | `List[Dict[str, Any]]` | UNUSED |
| `async execute_request` | GoogleAPIClient | `self, request: Any, auto_retry: bool` | `Dict[str, Any]` | UNUSED |
| `async get_service` | GoogleAPIClient | `self, api: str, version: Optional[str]` | `Any` | USED |
| `is_authenticated` | GoogleAPIClient | `self` | `bool` | USED |
| `rate_limit_stats` | GoogleAPIClient | `self` | `Dict[str, Any]` | UNUSED |
| `async refresh_token` | GoogleAPIClient | `self` | `None` | USED |
| `__init__` | GoogleAPIError | `self, message: str, error_code: Optional[int], ...` | `-` | DUNDER |
| `from_dict` | GoogleCredentials | `cls, data: Dict[str, Any]` | `'GoogleCredentials'` | USED |
| `from_service_account` | GoogleCredentials | `cls, service_account_info: Dict[str, Any]` | `'GoogleCredentials'` | USED |
| `is_expired` | GoogleCredentials | `self` | `bool` | USED |
| `to_dict` | GoogleCredentials | `self` | `Dict[str, Any]` | USED |
| `__init__` | GoogleQuotaError | `self, message: str, retry_after: Optional[int], ...` | `-` | DUNDER |


## casare_rpa.infrastructure.resources.google_docs_client

**File:** `src\casare_rpa\infrastructure\resources\google_docs_client.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `to_api_format` | DocumentStyle | `self` | `Dict[str, Any]` | USED |
| `__init__` | GoogleDocsAPIError | `self, message: str, error_code: Optional[int], ...` | `-` | DUNDER |
| `async __aenter__` | GoogleDocsClient | `self` | `'GoogleDocsClient'` | DUNDER |
| `async __aexit__` | GoogleDocsClient | `self, exc_type, exc_val, ...` | `None` | DUNDER |
| `__init__` | GoogleDocsClient | `self, config: GoogleDocsConfig` | `-` | DUNDER |
| `async _ensure_session` | GoogleDocsClient | `self` | `aiohttp.ClientSession` | INTERNAL |
| `async _request` | GoogleDocsClient | `self, method: str, url: str, ...` | `Dict[str, Any]` | INTERNAL |
| `async append_text` | GoogleDocsClient | `self, document_id: str, text: str` | `Dict[str, Any]` | USED |
| `async apply_style` | GoogleDocsClient | `self, document_id: str, start_index: int, ...` | `Dict[str, Any]` | USED |
| `async batch_update` | GoogleDocsClient | `self, document_id: str, requests: List[Dict[str, Any]]` | `Dict[str, Any]` | USED |
| `async close` | GoogleDocsClient | `self` | `None` | USED |
| `async create_document` | GoogleDocsClient | `self, title: str, content: Optional[str]` | `GoogleDocument` | USED |
| `async delete_content` | GoogleDocsClient | `self, document_id: str, start_index: int, ...` | `Dict[str, Any]` | UNUSED |
| `async export_document` | GoogleDocsClient | `self, document_id: str, export_format: ExportFormat, ...` | `Union[bytes, str]` | USED |
| `async get_document` | GoogleDocsClient | `self, document_id: str` | `GoogleDocument` | USED |
| `async get_text` | GoogleDocsClient | `self, document_id: str` | `str` | USED |
| `async insert_image` | GoogleDocsClient | `self, document_id: str, image_url: str, ...` | `Dict[str, Any]` | USED |
| `async insert_table` | GoogleDocsClient | `self, document_id: str, rows: int, ...` | `Dict[str, Any]` | USED |
| `async insert_text` | GoogleDocsClient | `self, document_id: str, text: str, ...` | `Dict[str, Any]` | USED |
| `async replace_text` | GoogleDocsClient | `self, document_id: str, search_text: str, ...` | `Dict[str, Any]` | USED |
| `extract_text` | GoogleDocument | `self` | `str` | USED |
| `from_response` | GoogleDocument | `cls, data: Dict[str, Any]` | `'GoogleDocument'` | USED |


## casare_rpa.infrastructure.resources.google_drive_client

**File:** `src\casare_rpa\infrastructure\resources\google_drive_client.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | DriveAPIError | `self, message: str, error_code: Optional[int], ...` | `-` | DUNDER |
| `from_response` | DriveFile | `cls, data: dict` | `'DriveFile'` | USED |
| `is_folder` | DriveFile | `self` | `bool` | UNUSED |
| `is_google_doc` | DriveFile | `self` | `bool` | UNUSED |
| `from_extension` | DriveMimeType | `cls, ext: str` | `str` | USED |
| `async __aenter__` | GoogleDriveClient | `self` | `'GoogleDriveClient'` | DUNDER |
| `async __aexit__` | GoogleDriveClient | `self, exc_type, exc_val, ...` | `None` | DUNDER |
| `__init__` | GoogleDriveClient | `self, config: DriveConfig` | `-` | DUNDER |
| `async _ensure_session` | GoogleDriveClient | `self` | `aiohttp.ClientSession` | INTERNAL |
| `async _request` | GoogleDriveClient | `self, method: str, url: str, ...` | `dict` | INTERNAL |
| `async _resumable_upload` | GoogleDriveClient | `self, file_path: Path, metadata: dict, ...` | `DriveFile` | INTERNAL |
| `async _simple_upload` | GoogleDriveClient | `self, file_path: Path, metadata: dict, ...` | `DriveFile` | INTERNAL |
| `async close` | GoogleDriveClient | `self` | `None` | USED |
| `async copy_file` | GoogleDriveClient | `self, file_id: str, new_name: Optional[str], ...` | `DriveFile` | USED |
| `async create_folder` | GoogleDriveClient | `self, name: str, parent_id: Optional[str], ...` | `DriveFile` | USED |
| `async delete_file` | GoogleDriveClient | `self, file_id: str, permanent: bool` | `bool` | USED |
| `async download_file` | GoogleDriveClient | `self, file_id: str, destination_path: Union[str, Path]` | `Path` | USED |
| `async empty_trash` | GoogleDriveClient | `self` | `bool` | UNUSED |
| `async export_file` | GoogleDriveClient | `self, file_id: str, destination_path: Union[str, Path], ...` | `Path` | UNUSED |
| `async get_about` | GoogleDriveClient | `self` | `dict` | UNUSED |
| `async get_file` | GoogleDriveClient | `self, file_id: str, fields: Optional[str]` | `DriveFile` | USED |
| `async list_files` | GoogleDriveClient | `self, folder_id: Optional[str], query: Optional[str], ...` | `tuple[list[DriveFile], Optional[str]]` | USED |
| `async move_file` | GoogleDriveClient | `self, file_id: str, new_folder_id: str` | `DriveFile` | USED |
| `async rename_file` | GoogleDriveClient | `self, file_id: str, new_name: str` | `DriveFile` | USED |
| `async search_files` | GoogleDriveClient | `self, query: str, mime_type: Optional[str], ...` | `list[DriveFile]` | USED |
| `async update_file` | GoogleDriveClient | `self, file_id: str, name: Optional[str], ...` | `DriveFile` | UNUSED |
| `async upload_file` | GoogleDriveClient | `self, file_path: Union[str, Path], folder_id: Optional[str], ...` | `DriveFile` | USED |


## casare_rpa.infrastructure.resources.google_sheets_client

**File:** `src\casare_rpa\infrastructure\resources\google_sheets_client.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `async __aenter__` | GoogleSheetsClient | `self` | `GoogleSheetsClient` | DUNDER |
| `async __aexit__` | GoogleSheetsClient | `self, exc_type, exc_val, ...` | `None` | DUNDER |
| `__init__` | GoogleSheetsClient | `self, config: GoogleSheetsConfig` | `None` | DUNDER |
| `async _authenticate_service_account` | GoogleSheetsClient | `self` | `None` | INTERNAL |
| `_get_headers` | GoogleSheetsClient | `self` | `Dict[str, str]` | INTERNAL |
| `_get_url` | GoogleSheetsClient | `self, endpoint: str, use_api_key: bool` | `str` | INTERNAL |
| `async _request` | GoogleSheetsClient | `self, method: str, endpoint: str, ...` | `Dict[str, Any]` | INTERNAL |
| `async add_sheet` | GoogleSheetsClient | `self, spreadsheet_id: str, sheet_name: str, ...` | `SheetProperties` | USED |
| `async append_values` | GoogleSheetsClient | `self, spreadsheet_id: str, range_notation: str, ...` | `Dict[str, Any]` | USED |
| `async batch_clear_values` | GoogleSheetsClient | `self, spreadsheet_id: str, ranges: List[str]` | `Dict[str, Any]` | USED |
| `async batch_get_values` | GoogleSheetsClient | `self, spreadsheet_id: str, ranges: List[str], ...` | `Dict[str, List[List[Any]]]` | USED |
| `async batch_update` | GoogleSheetsClient | `self, spreadsheet_id: str, requests: List[Dict[str, Any]]` | `Dict[str, Any]` | USED |
| `async batch_update_values` | GoogleSheetsClient | `self, spreadsheet_id: str, data: List[Dict[str, Any]], ...` | `Dict[str, Any]` | USED |
| `async clear_values` | GoogleSheetsClient | `self, spreadsheet_id: str, range_notation: str` | `Dict[str, Any]` | USED |
| `async copy_sheet` | GoogleSheetsClient | `self, source_spreadsheet_id: str, source_sheet_id: int, ...` | `SheetProperties` | USED |
| `async create_spreadsheet` | GoogleSheetsClient | `self, title: str, sheets: Optional[List[str]], ...` | `SpreadsheetProperties` | USED |
| `async delete_sheet` | GoogleSheetsClient | `self, spreadsheet_id: str, sheet_id: int` | `bool` | USED |
| `async get_sheet_by_name` | GoogleSheetsClient | `self, spreadsheet_id: str, sheet_name: str` | `Optional[SheetProperties]` | USED |
| `async get_sheet_row_count` | GoogleSheetsClient | `self, spreadsheet_id: str, sheet_name: str` | `int` | UNUSED |
| `async get_spreadsheet` | GoogleSheetsClient | `self, spreadsheet_id: str, include_grid_data: bool` | `SpreadsheetProperties` | USED |
| `async get_values` | GoogleSheetsClient | `self, spreadsheet_id: str, range_notation: str, ...` | `List[List[Any]]` | USED |
| `async update_values` | GoogleSheetsClient | `self, spreadsheet_id: str, range_notation: str, ...` | `Dict[str, Any]` | USED |
| `get_auth_method` | GoogleSheetsConfig | `self` | `str` | USED |
| `__init__` | GoogleSheetsError | `self, message: str, status_code: int, ...` | `-` | DUNDER |


## casare_rpa.infrastructure.resources.llm_model_provider

**File:** `src\casare_rpa\infrastructure\resources\llm_model_provider.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `get_all_models` | - | `` | `List[str]` | USED |
| `get_model_provider` | - | `` | `LLMModelProvider` | USED |
| `get_models_for_credential` | - | `credential_name: str` | `List[str]` | USED |
| `get_provider_for_credential` | - | `credential_name: str` | `Optional[str]` | USED |
| `__init__` | LLMModelProvider | `self` | `None` | DUNDER |
| `__new__` | LLMModelProvider | `cls` | `'LLMModelProvider'` | DUNDER |
| `_fetch_models` | LLMModelProvider | `self, provider: str, api_key: str` | `List[str]` | INTERNAL |
| `_get_provider_from_credential` | LLMModelProvider | `self, credential_name: str` | `Tuple[Optional[str], Optional[str]]` | INTERNAL |
| `_parse_cohere_models` | LLMModelProvider | `self, data: Dict[str, Any]` | `List[str]` | INTERNAL |
| `_parse_google_models` | LLMModelProvider | `self, data: Dict[str, Any]` | `List[str]` | INTERNAL |
| `_parse_openai_models` | LLMModelProvider | `self, data: Dict[str, Any]` | `List[str]` | INTERNAL |
| `_parse_together_models` | LLMModelProvider | `self, data: Dict[str, Any]` | `List[str]` | INTERNAL |
| `get_all_models` | LLMModelProvider | `self` | `List[str]` | USED |
| `get_models_for_credential` | LLMModelProvider | `self, credential_name: str` | `List[str]` | USED |
| `get_models_for_provider` | LLMModelProvider | `self, provider: str, api_key: Optional[str], ...` | `List[str]` | USED |
| `get_provider_for_credential` | LLMModelProvider | `self, credential_name: str` | `Optional[str]` | USED |
| `refresh_cache` | LLMModelProvider | `self, provider: Optional[str]` | `None` | UNUSED |


## casare_rpa.infrastructure.resources.llm_resource_manager

**File:** `src\casare_rpa\infrastructure\resources\llm_resource_manager.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `to_dict` | ChatMessage | `self` | `Dict[str, Any]` | USED |
| `add_message` | ConversationHistory | `self, role: str, content: str` | `None` | USED |
| `clear` | ConversationHistory | `self` | `None` | USED |
| `get_messages` | ConversationHistory | `self` | `List[Dict[str, str]]` | USED |
| `to_dict` | ImageContent | `self` | `Dict[str, Any]` | USED |
| `__init__` | LLMResourceManager | `self` | `None` | DUNDER |
| `__repr__` | LLMResourceManager | `self` | `str` | DUNDER |
| `_calculate_cost` | LLMResourceManager | `self, model: str, prompt_tokens: int, ...` | `float` | INTERNAL |
| `_detect_provider_from_model` | LLMResourceManager | `self, model: str` | `Optional[str]` | INTERNAL |
| `_ensure_initialized` | LLMResourceManager | `self` | `Any` | INTERNAL |
| `_get_api_key_for_model` | LLMResourceManager | `self, model: str` | `Optional[str]` | INTERNAL |
| `_get_api_key_for_provider` | LLMResourceManager | `self, provider: LLMProvider` | `Optional[str]` | INTERNAL |
| `_get_api_key_store` | LLMResourceManager | `self` | `Any` | INTERNAL |
| `_get_model_string` | LLMResourceManager | `self, model: Optional[str]` | `str` | INTERNAL |
| `async chat` | LLMResourceManager | `self, message: str, conversation_id: Optional[str], ...` | `tuple[LLMResponse, str]` | USED |
| `async cleanup` | LLMResourceManager | `self` | `None` | USED |
| `clear_conversation` | LLMResourceManager | `self, conversation_id: str` | `bool` | UNUSED |
| `async completion` | LLMResourceManager | `self, prompt: str, model: Optional[str], ...` | `LLMResponse` | USED |
| `config` | LLMResourceManager | `self` | `Optional[LLMConfig]` | UNUSED |
| `configure` | LLMResourceManager | `self, config: LLMConfig` | `None` | USED |
| `delete_conversation` | LLMResourceManager | `self, conversation_id: str` | `bool` | UNUSED |
| `async extract_structured` | LLMResourceManager | `self, text: str, schema: Dict[str, Any], ...` | `Dict[str, Any]` | USED |
| `get_conversation` | LLMResourceManager | `self, conversation_id: str` | `Optional[ConversationHistory]` | UNUSED |
| `metrics` | LLMResourceManager | `self` | `LLMUsageMetrics` | UNUSED |
| `async vision_completion` | LLMResourceManager | `self, prompt: str, images: List[ImageContent], ...` | `LLMResponse` | USED |
| `add_usage` | LLMUsageMetrics | `self, prompt_tokens: int, completion_tokens: int, ...` | `None` | USED |
| `record_error` | LLMUsageMetrics | `self` | `None` | USED |


## casare_rpa.infrastructure.resources.telegram_client

**File:** `src\casare_rpa\infrastructure\resources\telegram_client.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | TelegramAPIError | `self, message: str, error_code: Optional[int], ...` | `-` | DUNDER |
| `async __aenter__` | TelegramClient | `self` | `'TelegramClient'` | DUNDER |
| `async __aexit__` | TelegramClient | `self, exc_type, exc_val, ...` | `None` | DUNDER |
| `__init__` | TelegramClient | `self, config: TelegramConfig` | `-` | DUNDER |
| `async _ensure_session` | TelegramClient | `self` | `aiohttp.ClientSession` | INTERNAL |
| `_guess_content_type` | TelegramClient | `self, path: Path` | `str` | INTERNAL |
| `async _request` | TelegramClient | `self, method: str, data: Optional[dict], ...` | `dict` | INTERNAL |
| `async answer_callback_query` | TelegramClient | `self, callback_query_id: str, text: Optional[str], ...` | `bool` | USED |
| `async close` | TelegramClient | `self` | `None` | USED |
| `async delete_message` | TelegramClient | `self, chat_id: Union[int, str], message_id: int` | `bool` | USED |
| `async delete_webhook` | TelegramClient | `self, drop_pending_updates: bool` | `bool` | USED |
| `async edit_message_caption` | TelegramClient | `self, chat_id: Union[int, str], message_id: int, ...` | `TelegramMessage` | UNUSED |
| `async edit_message_text` | TelegramClient | `self, chat_id: Union[int, str], message_id: int, ...` | `TelegramMessage` | USED |
| `async get_me` | TelegramClient | `self` | `dict` | USED |
| `async get_updates` | TelegramClient | `self, offset: Optional[int], limit: int, ...` | `list[dict]` | USED |
| `async send_document` | TelegramClient | `self, chat_id: Union[int, str], document: Union[str, Path, bytes], ...` | `TelegramMessage` | USED |
| `async send_location` | TelegramClient | `self, chat_id: Union[int, str], latitude: float, ...` | `TelegramMessage` | USED |
| `async send_media_group` | TelegramClient | `self, chat_id: Union[int, str], media: list[dict], ...` | `list[TelegramMessage]` | USED |
| `async send_message` | TelegramClient | `self, chat_id: Union[int, str], text: str, ...` | `TelegramMessage` | USED |
| `async send_photo` | TelegramClient | `self, chat_id: Union[int, str], photo: Union[str, Path, bytes], ...` | `TelegramMessage` | USED |
| `async set_webhook` | TelegramClient | `self, url: str, allowed_updates: Optional[list[str]], ...` | `bool` | USED |
| `api_url` | TelegramConfig | `self` | `str` | UNUSED |
| `from_response` | TelegramMessage | `cls, data: dict` | `'TelegramMessage'` | USED |


## casare_rpa.infrastructure.resources.unified_resource_manager

**File:** `src\casare_rpa\infrastructure\resources\unified_resource_manager.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | BrowserPool | `self, max_size: int, headless: bool` | `None` | DUNDER |
| `async acquire` | BrowserPool | `self, job_id: str, timeout: float` | `Optional['BrowserContext']` | USED |
| `get_stats` | BrowserPool | `self` | `Dict[str, Any]` | USED |
| `async release` | BrowserPool | `self, job_id: str` | `bool` | USED |
| `async start` | BrowserPool | `self` | `None` | USED |
| `async stop` | BrowserPool | `self` | `None` | USED |
| `__init__` | DatabasePool | `self, max_size: int` | `None` | DUNDER |
| `async acquire` | DatabasePool | `self, job_id: str, timeout: float` | `Optional[Any]` | USED |
| `get_stats` | DatabasePool | `self` | `Dict[str, Any]` | USED |
| `async release` | DatabasePool | `self, job_id: str` | `bool` | USED |
| `async start` | DatabasePool | `self, postgres_url: str` | `None` | USED |
| `async stop` | DatabasePool | `self` | `None` | USED |
| `__init__` | HTTPPool | `self, max_size: int` | `None` | DUNDER |
| `async acquire` | HTTPPool | `self, job_id: str, timeout: float` | `Optional[Any]` | USED |
| `get_stats` | HTTPPool | `self` | `Dict[str, Any]` | USED |
| `async release` | HTTPPool | `self, job_id: str` | `bool` | USED |
| `async start` | HTTPPool | `self` | `None` | USED |
| `async stop` | HTTPPool | `self` | `None` | USED |
| `count_by_type` | JobResources | `self, resource_type: ResourceType` | `int` | UNUSED |
| `get_lease` | JobResources | `self, resource_type: ResourceType` | `Optional[ResourceLease]` | UNUSED |
| `to_dict` | JobResources | `self` | `Dict[str, Any]` | USED |
| `__init__` | LRUResourceCache | `self, max_size: int` | `None` | DUNDER |
| `async clear` | LRUResourceCache | `self` | `List[T]` | USED |
| `async evict_lru` | LRUResourceCache | `self` | `Optional[tuple[str, T]]` | USED |
| `async get` | LRUResourceCache | `self, key: str` | `Optional[T]` | USED |
| `async keys` | LRUResourceCache | `self` | `List[str]` | USED |
| `max_size` | LRUResourceCache | `self` | `int` | UNUSED |
| `async peek_lru` | LRUResourceCache | `self` | `Optional[tuple[str, T]]` | UNUSED |
| `async put` | LRUResourceCache | `self, key: str, resource: T` | `Optional[T]` | USED |
| `async remove` | LRUResourceCache | `self, key: str` | `Optional[T]` | USED |
| `size` | LRUResourceCache | `self` | `int` | USED |
| `to_dict` | PoolStatistics | `self` | `Dict[str, int]` | USED |
| `idle_time` | ResourceLease | `self` | `timedelta` | UNUSED |
| `is_expired` | ResourceLease | `self` | `bool` | USED |
| `time_remaining` | ResourceLease | `self` | `timedelta` | UNUSED |
| `touch` | ResourceLease | `self` | `None` | USED |
| `async __aenter__` | UnifiedResourceManager | `self` | `'UnifiedResourceManager'` | DUNDER |
| `async __aexit__` | UnifiedResourceManager | `self, exc_type: Any, exc_val: Any, ...` | `bool` | DUNDER |
| `__init__` | UnifiedResourceManager | `self, browser_pool_size: int, db_pool_size: int, ...` | `None` | DUNDER |
| `_check_quota` | UnifiedResourceManager | `self, job_id: str, resource_type: ResourceType` | `bool` | INTERNAL |
| `async _cleanup_expired_leases` | UnifiedResourceManager | `self` | `None` | INTERNAL |
| `async _release_single_lease` | UnifiedResourceManager | `self, lease: ResourceLease` | `None` | INTERNAL |
| `async _run_cleanup_cycle` | UnifiedResourceManager | `self` | `None` | INTERNAL |
| `async acquire_resources_for_job` | UnifiedResourceManager | `self, job_id: str, workflow_json: Union[str, Dict], ...` | `JobResources` | USED |
| `analyze_workflow_needs` | UnifiedResourceManager | `self, workflow_json: Union[str, Dict]` | `Dict[str, bool]` | USED |
| `get_job_leases` | UnifiedResourceManager | `self, job_id: str` | `List[ResourceLease]` | UNUSED |
| `get_stats` | UnifiedResourceManager | `self` | `Dict[str, Any]` | USED |
| `async release_all_job_resources` | UnifiedResourceManager | `self, job_id: str` | `None` | UNUSED |
| `async release_resources` | UnifiedResourceManager | `self, resources: JobResources` | `None` | USED |
| `async start` | UnifiedResourceManager | `self` | `None` | USED |
| `async stop` | UnifiedResourceManager | `self` | `None` | USED |


## casare_rpa.infrastructure.resources.whatsapp_client

**File:** `src\casare_rpa\infrastructure\resources\whatsapp_client.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | WhatsAppAPIError | `self, message: str, error_code: Optional[int], ...` | `-` | DUNDER |
| `async __aenter__` | WhatsAppClient | `self` | `'WhatsAppClient'` | DUNDER |
| `async __aexit__` | WhatsAppClient | `self, exc_type, exc_val, ...` | `None` | DUNDER |
| `__init__` | WhatsAppClient | `self, config: WhatsAppConfig` | `-` | DUNDER |
| `async _ensure_session` | WhatsAppClient | `self` | `aiohttp.ClientSession` | INTERNAL |
| `async _request` | WhatsAppClient | `self, method: str, url: str, ...` | `dict` | INTERNAL |
| `async close` | WhatsAppClient | `self` | `None` | USED |
| `async get_media_url` | WhatsAppClient | `self, media_id: str` | `str` | UNUSED |
| `async list_templates` | WhatsAppClient | `self, limit: int` | `list[WhatsAppTemplate]` | UNUSED |
| `async mark_as_read` | WhatsAppClient | `self, message_id: str` | `bool` | UNUSED |
| `async send_audio` | WhatsAppClient | `self, to: str, audio: Union[str, Path]` | `WhatsAppMessage` | UNUSED |
| `async send_contacts` | WhatsAppClient | `self, to: str, contacts: list[dict]` | `WhatsAppMessage` | UNUSED |
| `async send_document` | WhatsAppClient | `self, to: str, document: Union[str, Path], ...` | `WhatsAppMessage` | USED |
| `async send_image` | WhatsAppClient | `self, to: str, image: Union[str, Path], ...` | `WhatsAppMessage` | USED |
| `async send_interactive` | WhatsAppClient | `self, to: str, interactive_type: str, ...` | `WhatsAppMessage` | USED |
| `async send_location` | WhatsAppClient | `self, to: str, latitude: float, ...` | `WhatsAppMessage` | USED |
| `async send_message` | WhatsAppClient | `self, to: str, text: str, ...` | `WhatsAppMessage` | USED |
| `async send_template` | WhatsAppClient | `self, to: str, template_name: str, ...` | `WhatsAppMessage` | USED |
| `async send_video` | WhatsAppClient | `self, to: str, video: Union[str, Path], ...` | `WhatsAppMessage` | USED |
| `async upload_media` | WhatsAppClient | `self, file_path: Path, content_type: str` | `str` | UNUSED |
| `api_url` | WhatsAppConfig | `self` | `str` | UNUSED |
| `media_url` | WhatsAppConfig | `self` | `str` | UNUSED |
| `templates_url` | WhatsAppConfig | `self` | `str` | UNUSED |
| `from_response` | WhatsAppMessage | `cls, data: dict, phone_number: str` | `'WhatsAppMessage'` | USED |
| `from_response` | WhatsAppTemplate | `cls, data: dict` | `'WhatsAppTemplate'` | USED |


## casare_rpa.infrastructure.security.api_key_store

**File:** `src\casare_rpa\infrastructure\security\api_key_store.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `get_api_key` | - | `provider: str` | `Optional[str]` | USED |
| `get_api_key_store` | - | `` | `APIKeyStore` | USED |
| `set_api_key` | - | `provider: str, api_key: str` | `None` | UNUSED |
| `__init__` | APIKeyStore | `self, store_path: Optional[Path]` | `None` | DUNDER |
| `_ensure_initialized` | APIKeyStore | `self` | `None` | INTERNAL |
| `_get_default_store_path` | APIKeyStore | `self` | `Path` | INTERNAL |
| `_get_machine_identifier` | APIKeyStore | `self` | `str` | INTERNAL |
| `_get_master_key` | APIKeyStore | `self` | `bytes` | INTERNAL |
| `_load_store` | APIKeyStore | `self` | `None` | INTERNAL |
| `_protect_key` | APIKeyStore | `self, key: bytes` | `bytes` | INTERNAL |
| `_save_store` | APIKeyStore | `self` | `None` | INTERNAL |
| `_unprotect_key` | APIKeyStore | `self, protected_key: bytes` | `bytes` | INTERNAL |
| `clear_cache` | APIKeyStore | `self` | `None` | USED |
| `delete_key` | APIKeyStore | `self, provider: str` | `bool` | UNUSED |
| `get_key` | APIKeyStore | `self, provider: str, check_env: bool` | `Optional[str]` | USED |
| `get_key_info` | APIKeyStore | `self, provider: str` | `Optional[Dict]` | UNUSED |
| `has_key` | APIKeyStore | `self, provider: str, check_env: bool` | `bool` | UNUSED |
| `list_providers` | APIKeyStore | `self` | `List[str]` | UNUSED |
| `set_key` | APIKeyStore | `self, provider: str, api_key: str, ...` | `None` | USED |


## casare_rpa.infrastructure.security.credential_provider

**File:** `src\casare_rpa\infrastructure\security\credential_provider.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `create_credential_resolver` | - | `config: Optional[VaultConfig]` | `VaultCredentialProvider` | UNUSED |
| `async resolve_credentials_for_node` | - | `provider: VaultCredentialProvider, credential_requirements: Dict[str, Dict[str, Any]]` | `Dict[str, ResolvedCredential]` | UNUSED |
| `async __aenter__` | VaultCredentialProvider | `self` | `'VaultCredentialProvider'` | DUNDER |
| `async __aexit__` | VaultCredentialProvider | `self, exc_type: Any, exc_val: Any, ...` | `bool` | DUNDER |
| `__init__` | VaultCredentialProvider | `self, config: Optional[VaultConfig], vault_client: Optional[VaultClient]` | `None` | DUNDER |
| `_build_resolved_credential` | VaultCredentialProvider | `self, secret: SecretValue, alias: str, ...` | `ResolvedCredential` | INTERNAL |
| `async _check_leases` | VaultCredentialProvider | `self` | `None` | INTERNAL |
| `async _lease_monitor_loop` | VaultCredentialProvider | `self` | `None` | INTERNAL |
| `async _renew_lease` | VaultCredentialProvider | `self, lease: CredentialLease` | `None` | INTERNAL |
| `async _revoke_lease` | VaultCredentialProvider | `self, lease: CredentialLease` | `None` | INTERNAL |
| `get_active_leases` | VaultCredentialProvider | `self` | `List[Dict[str, Any]]` | UNUSED |
| `async get_credential` | VaultCredentialProvider | `self, alias: str, required: bool` | `Optional[ResolvedCredential]` | USED |
| `async get_credential_by_path` | VaultCredentialProvider | `self, vault_path: str, alias: Optional[str]` | `ResolvedCredential` | USED |
| `async get_dynamic_credential` | VaultCredentialProvider | `self, engine_path: str, role: str, ...` | `ResolvedCredential` | UNUSED |
| `get_registered_aliases` | VaultCredentialProvider | `self` | `Dict[str, str]` | UNUSED |
| `async initialize` | VaultCredentialProvider | `self` | `None` | USED |
| `async invalidate_credential` | VaultCredentialProvider | `self, alias_or_path: str` | `bool` | UNUSED |
| `register_alias` | VaultCredentialProvider | `self, alias: str, vault_path: str` | `None` | UNUSED |
| `register_bindings` | VaultCredentialProvider | `self, bindings: Dict[str, str]` | `None` | USED |
| `set_execution_context` | VaultCredentialProvider | `self, workflow_id: Optional[str], robot_id: Optional[str]` | `None` | USED |
| `async shutdown` | VaultCredentialProvider | `self` | `None` | USED |


## casare_rpa.infrastructure.security.credential_store

**File:** `src\casare_rpa\infrastructure\security\credential_store.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `get_credential_store` | - | `` | `CredentialStore` | USED |
| `from_dict` | Credential | `cls, data: Dict[str, Any]` | `'Credential'` | USED |
| `to_dict` | Credential | `self` | `Dict[str, Any]` | USED |
| `__init__` | CredentialStore | `self, store_path: Optional[Path]` | `None` | DUNDER |
| `_decrypt_data` | CredentialStore | `self, encrypted_data: str` | `Dict[str, Any]` | INTERNAL |
| `_encrypt_data` | CredentialStore | `self, data: Dict[str, Any]` | `str` | INTERNAL |
| `_ensure_initialized` | CredentialStore | `self` | `None` | INTERNAL |
| `_generate_id` | CredentialStore | `self` | `str` | INTERNAL |
| `_get_default_store_path` | CredentialStore | `self` | `Path` | INTERNAL |
| `_get_machine_identifier` | CredentialStore | `self` | `str` | INTERNAL |
| `_get_master_key` | CredentialStore | `self` | `bytes` | INTERNAL |
| `_load_store` | CredentialStore | `self` | `None` | INTERNAL |
| `_protect_key` | CredentialStore | `self, key: bytes` | `bytes` | INTERNAL |
| `_save_store` | CredentialStore | `self` | `None` | INTERNAL |
| `_unprotect_key` | CredentialStore | `self, protected_key: bytes` | `bytes` | INTERNAL |
| `clear_cache` | CredentialStore | `self` | `None` | USED |
| `delete_credential` | CredentialStore | `self, credential_id: str` | `bool` | USED |
| `get_api_key` | CredentialStore | `self, credential_id: str` | `Optional[str]` | USED |
| `get_api_key_by_provider` | CredentialStore | `self, provider: str` | `Optional[str]` | USED |
| `get_credential` | CredentialStore | `self, credential_id: str` | `Optional[Dict[str, Any]]` | USED |
| `get_credential_info` | CredentialStore | `self, credential_id: str` | `Optional[Dict[str, Any]]` | USED |
| `get_credentials_for_dropdown` | CredentialStore | `self, category: Optional[str]` | `List[tuple[str, str]]` | UNUSED |
| `list_credentials` | CredentialStore | `self, category: Optional[str], credential_type: Optional[CredentialType]` | `List[Dict[str, Any]]` | USED |
| `rename_credential` | CredentialStore | `self, credential_id: str, new_name: str` | `bool` | UNUSED |
| `save_api_key` | CredentialStore | `self, name: str, provider: str, ...` | `str` | UNUSED |
| `save_credential` | CredentialStore | `self, name: str, credential_type: CredentialType, ...` | `str` | USED |
| `save_username_password` | CredentialStore | `self, name: str, category: str, ...` | `str` | UNUSED |
| `search_credentials` | CredentialStore | `self, query: str` | `List[Dict[str, Any]]` | USED |


## casare_rpa.infrastructure.security.merkle_audit

**File:** `src\casare_rpa\infrastructure\security\merkle_audit.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `get_audit_service` | - | `db_pool` | `MerkleAuditService` | USED |
| `async log_audit_event` | - | `action: AuditAction, actor_id: UUID, resource_type: ResourceType, ...` | `AuditEntry` | UNUSED |
| `__init__` | MerkleAuditService | `self, db_pool` | `-` | DUNDER |
| `async _get_entries_range` | MerkleAuditService | `self, start_id: Optional[int], end_id: Optional[int]` | `List[AuditEntry]` | INTERNAL |
| `async _get_last_hash` | MerkleAuditService | `self` | `bytes` | INTERNAL |
| `async _persist_entry` | MerkleAuditService | `self, entry: AuditEntry` | `None` | INTERNAL |
| `_row_to_entry` | MerkleAuditService | `self, row` | `AuditEntry` | INTERNAL |
| `async append_entry` | MerkleAuditService | `self, entry: AuditEntry` | `AuditEntry` | USED |
| `build_merkle_tree` | MerkleAuditService | `self, entry_hashes: List[bytes]` | `bytes` | USED |
| `compute_entry_hash` | MerkleAuditService | `self, entry: AuditEntry` | `bytes` | USED |
| `async compute_merkle_root` | MerkleAuditService | `self, start_id: Optional[int], end_id: Optional[int]` | `bytes` | UNUSED |
| `async export_audit_log` | MerkleAuditService | `self, start_date: Optional[datetime], end_date: Optional[datetime], ...` | `Dict[str, Any]` | UNUSED |
| `generate_merkle_proof` | MerkleAuditService | `self, entry_hash: bytes, all_hashes: List[bytes]` | `List[Tuple[bytes, str]]` | UNUSED |
| `async verify_chain` | MerkleAuditService | `self, start_id: Optional[int], end_id: Optional[int]` | `ChainVerificationResult` | UNUSED |
| `verify_merkle_proof` | MerkleAuditService | `self, entry_hash: bytes, merkle_root: bytes, ...` | `bool` | UNUSED |


## casare_rpa.infrastructure.security.providers.factory

**File:** `src\casare_rpa\infrastructure\security\providers\factory.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `create_vault_provider` | - | `config: VaultConfig, fallback_to_sqlite: bool` | `VaultProvider` | USED |
| `get_available_backends` | - | `` | `dict[VaultBackend, bool]` | USED |
| `get_recommended_backend` | - | `` | `VaultBackend` | UNUSED |


## casare_rpa.infrastructure.security.providers.hashicorp

**File:** `src\casare_rpa\infrastructure\security\providers\hashicorp.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | HashiCorpVaultProvider | `self, config: VaultConfig` | `None` | DUNDER |
| `_ensure_connected` | HashiCorpVaultProvider | `self` | `'hvac.Client'` | INTERNAL |
| `_infer_credential_type` | HashiCorpVaultProvider | `self, data: Dict[str, Any]` | `CredentialType` | INTERNAL |
| `_infer_dynamic_credential_type` | HashiCorpVaultProvider | `self, engine_path: str` | `CredentialType` | INTERNAL |
| `_parse_vault_time` | HashiCorpVaultProvider | `self, time_str: Optional[str]` | `datetime` | INTERNAL |
| `async connect` | HashiCorpVaultProvider | `self` | `None` | USED |
| `async delete_secret` | HashiCorpVaultProvider | `self, path: str` | `bool` | USED |
| `async disconnect` | HashiCorpVaultProvider | `self` | `None` | USED |
| `async get_dynamic_secret` | HashiCorpVaultProvider | `self, path: str, role: str, ...` | `SecretValue` | USED |
| `async get_secret` | HashiCorpVaultProvider | `self, path: str, version: Optional[int]` | `SecretValue` | USED |
| `async is_connected` | HashiCorpVaultProvider | `self` | `bool` | USED |
| `async list_secrets` | HashiCorpVaultProvider | `self, path_prefix: str` | `List[str]` | USED |
| `async put_secret` | HashiCorpVaultProvider | `self, path: str, data: Dict[str, Any], ...` | `SecretMetadata` | USED |
| `async renew_lease` | HashiCorpVaultProvider | `self, lease_id: str, increment: Optional[int]` | `int` | USED |
| `async revoke_lease` | HashiCorpVaultProvider | `self, lease_id: str` | `None` | USED |
| `async rotate_secret` | HashiCorpVaultProvider | `self, path: str` | `SecretMetadata` | USED |


## casare_rpa.infrastructure.security.providers.sqlite_vault

**File:** `src\casare_rpa\infrastructure\security\providers\sqlite_vault.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `async create_development_vault` | - | `path: str, encryption_key: Optional[str]` | `EncryptedSQLiteProvider` | UNUSED |
| `__init__` | EncryptedSQLiteProvider | `self, config: VaultConfig` | `None` | DUNDER |
| `_create_fernet` | EncryptedSQLiteProvider | `self` | `'Fernet'` | INTERNAL |
| `async _create_schema` | EncryptedSQLiteProvider | `self` | `None` | INTERNAL |
| `_decrypt` | EncryptedSQLiteProvider | `self, encrypted: bytes` | `Dict[str, Any]` | INTERNAL |
| `_encrypt` | EncryptedSQLiteProvider | `self, data: Dict[str, Any]` | `bytes` | INTERNAL |
| `_ensure_connected` | EncryptedSQLiteProvider | `self` | `tuple['aiosqlite.Connection', 'Fernet']` | INTERNAL |
| `_generate_api_key` | EncryptedSQLiteProvider | `self, length: int` | `str` | INTERNAL |
| `_generate_password` | EncryptedSQLiteProvider | `self, length: int` | `str` | INTERNAL |
| `_generate_rotated_values` | EncryptedSQLiteProvider | `self, current_data: Dict[str, Any], cred_type: CredentialType` | `Dict[str, Any]` | INTERNAL |
| `_get_machine_id` | EncryptedSQLiteProvider | `self` | `str` | INTERNAL |
| `async connect` | EncryptedSQLiteProvider | `self` | `None` | USED |
| `async delete_secret` | EncryptedSQLiteProvider | `self, path: str` | `bool` | USED |
| `async disconnect` | EncryptedSQLiteProvider | `self` | `None` | USED |
| `async get_secret` | EncryptedSQLiteProvider | `self, path: str, version: Optional[int]` | `SecretValue` | USED |
| `async is_connected` | EncryptedSQLiteProvider | `self` | `bool` | USED |
| `async list_secrets` | EncryptedSQLiteProvider | `self, path_prefix: str` | `List[str]` | USED |
| `async put_secret` | EncryptedSQLiteProvider | `self, path: str, data: Dict[str, Any], ...` | `SecretMetadata` | USED |
| `async rotate_secret` | EncryptedSQLiteProvider | `self, path: str` | `SecretMetadata` | USED |


## casare_rpa.infrastructure.security.providers.supabase_vault

**File:** `src\casare_rpa\infrastructure\security\providers\supabase_vault.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | SupabaseVaultProvider | `self, config: VaultConfig` | `None` | DUNDER |
| `_build_postgres_url` | SupabaseVaultProvider | `self` | `str` | INTERNAL |
| `async _ensure_fallback_tables` | SupabaseVaultProvider | `self, conn: 'asyncpg.Connection'` | `None` | INTERNAL |
| `_ensure_pool` | SupabaseVaultProvider | `self` | `'asyncpg.Pool'` | INTERNAL |
| `_generate_password` | SupabaseVaultProvider | `self, length: int` | `str` | INTERNAL |
| `_generate_rotated_values` | SupabaseVaultProvider | `self, current_data: Dict[str, Any], cred_type: CredentialType` | `Dict[str, Any]` | INTERNAL |
| `_infer_credential_type` | SupabaseVaultProvider | `self, data: Dict[str, Any]` | `CredentialType` | INTERNAL |
| `async connect` | SupabaseVaultProvider | `self` | `None` | USED |
| `async delete_secret` | SupabaseVaultProvider | `self, path: str` | `bool` | USED |
| `async disconnect` | SupabaseVaultProvider | `self` | `None` | USED |
| `async get_secret` | SupabaseVaultProvider | `self, path: str, version: Optional[int]` | `SecretValue` | USED |
| `async is_connected` | SupabaseVaultProvider | `self` | `bool` | USED |
| `async list_secrets` | SupabaseVaultProvider | `self, path_prefix: str` | `List[str]` | USED |
| `async put_secret` | SupabaseVaultProvider | `self, path: str, data: Dict[str, Any], ...` | `SecretMetadata` | USED |
| `async rotate_secret` | SupabaseVaultProvider | `self, path: str` | `SecretMetadata` | USED |


## casare_rpa.infrastructure.security.rbac

**File:** `src\casare_rpa\infrastructure\security\rbac.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `async create_authorization_service` | - | `permission_registry: Optional[PermissionRegistry]` | `AuthorizationService` | UNUSED |
| `create_permission_registry` | - | `` | `PermissionRegistry` | USED |
| `decorator` | - | `func: Callable[..., T]` | `Callable[..., T]` | UNUSED |
| `get_default_permissions` | - | `` | `List[Permission]` | UNUSED |
| `require_permission` | - | `resource: ResourceType, action: ActionType, get_context: Optional[Callable[..., Dict[str, Any]]]` | `Callable[[Callable[..., T]], Callable[..., T]]` | UNUSED |
| `async wrapper` | - | `` | `T` | UNUSED |
| `__init__` | AuthorizationService | `self, role_manager: RoleManager, permission_registry: PermissionRegistry` | `None` | DUNDER |
| `async check_all_permissions` | AuthorizationService | `self, user_id: UUID, tenant_id: UUID, ...` | `bool` | UNUSED |
| `async check_any_permission` | AuthorizationService | `self, user_id: UUID, tenant_id: UUID, ...` | `bool` | UNUSED |
| `async check_permission` | AuthorizationService | `self, user_id: UUID, tenant_id: UUID, ...` | `bool` | USED |
| `get_available_permissions` | AuthorizationService | `self, resource: Optional[ResourceType], category: Optional[str]` | `List[Permission]` | UNUSED |
| `async get_user_permissions` | AuthorizationService | `self, user_id: UUID, tenant_id: UUID, ...` | `UserPermissions` | USED |
| `async invalidate_user_cache` | AuthorizationService | `self, user_id: Optional[UUID], tenant_id: Optional[UUID]` | `int` | UNUSED |
| `__eq__` | Permission | `self, other: object` | `bool` | DUNDER |
| `__hash__` | Permission | `self` | `int` | DUNDER |
| `permission_key` | Permission | `self` | `str` | UNUSED |
| `evaluate` | PermissionCondition | `self, context: Dict[str, Any]` | `bool` | USED |
| `__init__` | PermissionDeniedError | `self, user_id: UUID, resource: ResourceType, ...` | `None` | DUNDER |
| `__init__` | PermissionRegistry | `self` | `None` | DUNDER |
| `exists` | PermissionRegistry | `self, resource: ResourceType, action: ActionType` | `bool` | USED |
| `get` | PermissionRegistry | `self, resource: ResourceType, action: ActionType` | `Optional[Permission]` | USED |
| `get_all` | PermissionRegistry | `self` | `List[Permission]` | USED |
| `get_by_category` | PermissionRegistry | `self, category: str` | `List[Permission]` | USED |
| `get_by_key` | PermissionRegistry | `self, key: str` | `Optional[Permission]` | USED |
| `get_by_resource` | PermissionRegistry | `self, resource: ResourceType` | `List[Permission]` | USED |
| `async register` | PermissionRegistry | `self, permission: Permission` | `None` | USED |
| `async register_many` | PermissionRegistry | `self, permissions: List[Permission]` | `None` | UNUSED |
| `__init__` | RBACError | `self, message: str, details: Optional[Dict[str, Any]]` | `None` | DUNDER |
| `__hash__` | Role | `self` | `int` | DUNDER |
| `get_permission_keys` | Role | `self` | `Set[str]` | USED |
| `has_permission` | Role | `self, resource: ResourceType, action: ActionType, ...` | `bool` | USED |
| `__init__` | RoleManager | `self, permission_registry: PermissionRegistry` | `None` | DUNDER |
| `async create_custom_role` | RoleManager | `self, tenant_id: UUID, name: str, ...` | `Role` | UNUSED |
| `async delete_custom_role` | RoleManager | `self, role_id: UUID, tenant_id: UUID` | `bool` | UNUSED |
| `get_all_system_roles` | RoleManager | `self` | `List[Role]` | UNUSED |
| `get_available_roles` | RoleManager | `self, tenant_id: UUID` | `List[Role]` | UNUSED |
| `get_role` | RoleManager | `self, role_id: UUID, tenant_id: Optional[UUID]` | `Optional[Role]` | USED |
| `get_system_role` | RoleManager | `self, role_id: UUID` | `Optional[Role]` | UNUSED |
| `get_system_role_by_name` | RoleManager | `self, name: str` | `Optional[Role]` | UNUSED |
| `get_tenant_role` | RoleManager | `self, tenant_id: UUID, role_id: UUID` | `Optional[Role]` | USED |
| `get_tenant_roles` | RoleManager | `self, tenant_id: UUID` | `List[Role]` | USED |
| `async load_system_roles` | RoleManager | `self, roles: List[Role]` | `None` | UNUSED |
| `async load_tenant_roles` | RoleManager | `self, tenant_id: UUID, roles: List[Role]` | `None` | UNUSED |
| `async update_role_permissions` | RoleManager | `self, role_id: UUID, tenant_id: UUID, ...` | `Role` | UNUSED |
| `__init__` | RoleNotFoundError | `self, role_id: UUID` | `None` | DUNDER |
| `is_granted` | RolePermission | `self, context: Optional[Dict[str, Any]]` | `bool` | USED |
| `has_all_permissions` | UserPermissions | `self, permissions: List[tuple[ResourceType, ActionType]], context: Optional[Dict[str, Any]]` | `bool` | USED |
| `has_any_permission` | UserPermissions | `self, permissions: List[tuple[ResourceType, ActionType]], context: Optional[Dict[str, Any]]` | `bool` | USED |
| `has_permission` | UserPermissions | `self, resource: ResourceType, action: ActionType, ...` | `bool` | USED |
| `highest_priority_role` | UserPermissions | `self` | `Optional[Role]` | UNUSED |
| `is_cache_valid` | UserPermissions | `self` | `bool` | UNUSED |


## casare_rpa.infrastructure.security.rotation

**File:** `src\casare_rpa\infrastructure\security\rotation.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `async setup_rotation_for_credentials` | - | `rotation_manager: SecretRotationManager, credential_bindings: Dict[str, str], frequency: RotationFrequency` | `int` | UNUSED |
| `async execute` | LoggingRotationHook | `self, path: str, old_data: Optional[Dict[str, Any]], ...` | `bool` | USED |
| `async execute` | RotationHook | `self, path: str, old_data: Optional[Dict[str, Any]], ...` | `bool` | USED |
| `calculate_next_rotation` | RotationPolicy | `self` | `datetime` | USED |
| `get_interval` | RotationPolicy | `self` | `timedelta` | USED |
| `__init__` | SecretRotationManager | `self, vault_client: VaultClient, check_interval_seconds: int` | `None` | DUNDER |
| `_add_to_history` | SecretRotationManager | `self, record: RotationRecord` | `None` | INTERNAL |
| `async _check_and_rotate` | SecretRotationManager | `self` | `None` | INTERNAL |
| `async _scheduler_loop` | SecretRotationManager | `self` | `None` | INTERNAL |
| `get_due_rotations` | SecretRotationManager | `self` | `List[RotationPolicy]` | UNUSED |
| `get_policies` | SecretRotationManager | `self` | `List[RotationPolicy]` | UNUSED |
| `get_rotation_history` | SecretRotationManager | `self, path: Optional[str], limit: int` | `List[RotationRecord]` | UNUSED |
| `register_hook` | SecretRotationManager | `self, name: str, hook: RotationHook` | `None` | USED |
| `register_policy` | SecretRotationManager | `self, policy: RotationPolicy` | `None` | USED |
| `async rotate_secret` | SecretRotationManager | `self, path: str, force: bool` | `RotationRecord` | USED |
| `async start` | SecretRotationManager | `self` | `None` | USED |
| `async stop` | SecretRotationManager | `self` | `None` | USED |
| `unregister_policy` | SecretRotationManager | `self, path: str` | `bool` | UNUSED |


## casare_rpa.infrastructure.security.tenancy

**File:** `src\casare_rpa\infrastructure\security\tenancy.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `create_api_key_service` | - | `tenant_service: TenantService` | `APIKeyService` | UNUSED |
| `create_audit_service` | - | `context_manager: Optional[TenantContextManager], merkle_enabled: bool` | `AuditService` | UNUSED |
| `create_tenant_context_manager` | - | `` | `TenantContextManager` | USED |
| `create_tenant_service` | - | `context_manager: Optional[TenantContextManager]` | `TenantService` | UNUSED |
| `generate` | APIKey | `cls, tenant_id: UUID, name: str, ...` | `tuple['APIKey', str]` | USED |
| `is_valid` | APIKey | `self` | `bool` | UNUSED |
| `verify` | APIKey | `self, raw_key: str` | `bool` | USED |
| `__init__` | APIKeyService | `self, tenant_service: TenantService` | `None` | DUNDER |
| `async create_key` | APIKeyService | `self, tenant_id: UUID, name: str, ...` | `tuple[APIKey, str]` | UNUSED |
| `async get_key` | APIKeyService | `self, key_id: UUID` | `Optional[APIKey]` | USED |
| `async list_keys` | APIKeyService | `self, tenant_id: UUID` | `List[APIKey]` | UNUSED |
| `async revoke_key` | APIKeyService | `self, key_id: UUID, revoked_by: Optional[UUID]` | `APIKey` | UNUSED |
| `async validate_key` | APIKeyService | `self, raw_key: str` | `APIKey` | UNUSED |
| `__init__` | AuditService | `self, context_manager: TenantContextManager, merkle_enabled: bool` | `None` | DUNDER |
| `async _append_to_merkle_log` | AuditService | `self, entry: AuditLogEntry` | `None` | INTERNAL |
| `_map_to_merkle_action` | AuditService | `self, action: AuditAction` | `MerkleAuditAction` | INTERNAL |
| `async flush` | AuditService | `self` | `int` | USED |
| `async log` | AuditService | `self, tenant_id: UUID, action: AuditAction, ...` | `AuditLogEntry` | USED |
| `async query` | AuditService | `self, tenant_id: UUID, action: Optional[AuditAction], ...` | `List[AuditLogEntry]` | USED |
| `__init__` | InvalidAPIKeyError | `self, reason: str` | `None` | DUNDER |
| `__init__` | QuotaExceededError | `self, tenant_id: UUID, resource_type: str, ...` | `None` | DUNDER |
| `__init__` | RateLimitExceededError | `self, tenant_id: UUID, limit_type: str, ...` | `None` | DUNDER |
| `for_tier` | ResourceQuotas | `cls, tier: SubscriptionTier` | `'ResourceQuotas'` | USED |
| `validate_config` | SSOConfig | `self` | `List[str]` | USED |
| `__init__` | TenancyError | `self, message: str, details: Optional[Dict[str, Any]]` | `None` | DUNDER |
| `check_quota` | Tenant | `self, resource_type: str` | `bool` | USED |
| `get_quota_remaining` | Tenant | `self, resource_type: str` | `int` | UNUSED |
| `is_active` | Tenant | `self` | `bool` | USED |
| `is_subscription_valid` | Tenant | `self` | `bool` | UNUSED |
| `validate_slug` | Tenant | `cls, v: str` | `str` | UNUSED |
| `__post_init__` | TenantContext | `self` | `None` | DUNDER |
| `__init__` | TenantContextManager | `self` | `None` | DUNDER |
| `async clear_context` | TenantContextManager | `self` | `None` | USED |
| `current` | TenantContextManager | `self` | `Optional[TenantContext]` | UNUSED |
| `get_rls_parameters` | TenantContextManager | `self` | `Dict[str, str]` | UNUSED |
| `async set_context` | TenantContextManager | `self, context: TenantContext` | `None` | USED |
| `async with_context` | TenantContextManager | `self, context: TenantContext` | `AsyncGenerator[TenantContext, None]` | USED |
| `async with_tenant` | TenantContextManager | `self, tenant_id: UUID, user_id: Optional[UUID]` | `AsyncGenerator[TenantContext, None]` | UNUSED |
| `__init__` | TenantNotFoundError | `self, tenant_id: UUID` | `None` | DUNDER |
| `__init__` | TenantService | `self, context_manager: TenantContextManager` | `None` | DUNDER |
| `async activate_tenant` | TenantService | `self, tenant_id: UUID` | `Tenant` | UNUSED |
| `async check_and_enforce_quota` | TenantService | `self, tenant_id: UUID, resource_type: str, ...` | `bool` | USED |
| `async configure_sso` | TenantService | `self, tenant_id: UUID, config: SSOConfig` | `Tenant` | UNUSED |
| `async create_tenant` | TenantService | `self, name: str, slug: str, ...` | `Tenant` | UNUSED |
| `async decrement_usage` | TenantService | `self, tenant_id: UUID, resource_type: str, ...` | `None` | USED |
| `async get_tenant` | TenantService | `self, tenant_id: UUID` | `Tenant` | USED |
| `async get_tenant_by_slug` | TenantService | `self, slug: str` | `Tenant` | UNUSED |
| `async increment_usage` | TenantService | `self, tenant_id: UUID, resource_type: str, ...` | `None` | USED |
| `async suspend_tenant` | TenantService | `self, tenant_id: UUID, reason: Optional[str]` | `Tenant` | UNUSED |
| `async update_subscription` | TenantService | `self, tenant_id: UUID, tier: SubscriptionTier, ...` | `Tenant` | UNUSED |
| `async update_tenant` | TenantService | `self, tenant_id: UUID` | `Tenant` | UNUSED |
| `__init__` | TenantSuspendedError | `self, tenant_id: UUID` | `None` | DUNDER |


## casare_rpa.infrastructure.security.validators

**File:** `src\casare_rpa\infrastructure\security\validators.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `sanitize_log_value` | - | `value: Any, mask_patterns: list[str]` | `str` | USED |
| `validate_robot_id` | - | `value: str` | `str` | USED |
| `validate_sql_identifier` | - | `value: str, name: str` | `str` | USED |
| `validate_workflow_id` | - | `value: str` | `str` | USED |


## casare_rpa.infrastructure.security.vault_client

**File:** `src\casare_rpa\infrastructure\security\vault_client.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `to_log_string` | AuditEvent | `self` | `str` | USED |
| `__init__` | AuditLogger | `self, enabled: bool, log_reads: bool` | `None` | DUNDER |
| `async flush` | AuditLogger | `self` | `None` | USED |
| `get_recent_events` | AuditLogger | `self, count: int` | `List[AuditEvent]` | USED |
| `log` | AuditLogger | `self, event: AuditEvent` | `None` | USED |
| `log_cache_event` | AuditLogger | `self, path: str, hit: bool` | `None` | USED |
| `log_read` | AuditLogger | `self, path: str, success: bool, ...` | `None` | USED |
| `log_write` | AuditLogger | `self, path: str, success: bool, ...` | `None` | USED |
| `is_expired` | CacheEntry | `self` | `bool` | USED |
| `__init__` | SecretCache | `self, max_size: int, default_ttl: int` | `None` | DUNDER |
| `async _evict_lru` | SecretCache | `self` | `None` | INTERNAL |
| `async clear` | SecretCache | `self` | `None` | USED |
| `async get` | SecretCache | `self, path: str` | `Optional[SecretValue]` | USED |
| `get_stats` | SecretCache | `self` | `Dict[str, Any]` | USED |
| `async invalidate` | SecretCache | `self, path: str` | `bool` | USED |
| `async invalidate_prefix` | SecretCache | `self, prefix: str` | `int` | USED |
| `async set` | SecretCache | `self, path: str, value: SecretValue, ...` | `None` | USED |
| `is_expired` | SecretMetadata | `self` | `bool` | USED |
| `time_until_expiry` | SecretMetadata | `self` | `Optional[timedelta]` | UNUSED |
| `get` | SecretValue | `self, key: str, default: Any` | `Any` | USED |
| `get_api_key` | SecretValue | `self` | `Optional[str]` | USED |
| `get_password` | SecretValue | `self` | `Optional[str]` | USED |
| `get_username` | SecretValue | `self` | `Optional[str]` | USED |
| `async __aenter__` | VaultClient | `self` | `'VaultClient'` | DUNDER |
| `async __aexit__` | VaultClient | `self, exc_type: Any, exc_val: Any, ...` | `bool` | DUNDER |
| `__init__` | VaultClient | `self, config: VaultConfig, provider: Optional[VaultProvider]` | `None` | DUNDER |
| `async connect` | VaultClient | `self` | `None` | USED |
| `async delete_secret` | VaultClient | `self, path: str` | `bool` | USED |
| `async disconnect` | VaultClient | `self` | `None` | USED |
| `get_audit_events` | VaultClient | `self, count: int` | `List[AuditEvent]` | UNUSED |
| `get_cache_stats` | VaultClient | `self` | `Dict[str, Any]` | UNUSED |
| `async get_dynamic_secret` | VaultClient | `self, path: str, role: str, ...` | `SecretValue` | USED |
| `async get_secret` | VaultClient | `self, path: str, version: Optional[int], ...` | `SecretValue` | USED |
| `async invalidate_cache` | VaultClient | `self, path: Optional[str]` | `int` | USED |
| `async is_connected` | VaultClient | `self` | `bool` | USED |
| `async list_secrets` | VaultClient | `self, path_prefix: str` | `List[str]` | USED |
| `async put_secret` | VaultClient | `self, path: str, data: Dict[str, Any], ...` | `SecretMetadata` | USED |
| `async renew_lease` | VaultClient | `self, lease_id: str, increment: Optional[int]` | `int` | USED |
| `async revoke_lease` | VaultClient | `self, lease_id: str` | `None` | USED |
| `async rotate_secret` | VaultClient | `self, path: str` | `SecretMetadata` | USED |
| `set_context` | VaultClient | `self, workflow_id: Optional[str], robot_id: Optional[str]` | `None` | USED |
| `get_backend_display_name` | VaultConfig | `self` | `str` | USED |
| `validate_hashicorp_url` | VaultConfig | `cls, v: Optional[str]` | `Optional[str]` | UNUSED |
| `__init__` | VaultError | `self, message: str, path: Optional[str]` | `None` | DUNDER |
| `async connect` | VaultProvider | `self` | `None` | USED |
| `async delete_secret` | VaultProvider | `self, path: str` | `bool` | USED |
| `async disconnect` | VaultProvider | `self` | `None` | USED |
| `async get_dynamic_secret` | VaultProvider | `self, path: str, role: str, ...` | `SecretValue` | USED |
| `async get_secret` | VaultProvider | `self, path: str, version: Optional[int]` | `SecretValue` | USED |
| `async is_connected` | VaultProvider | `self` | `bool` | USED |
| `async list_secrets` | VaultProvider | `self, path_prefix: str` | `List[str]` | USED |
| `async put_secret` | VaultProvider | `self, path: str, data: Dict[str, Any], ...` | `SecretMetadata` | USED |
| `async renew_lease` | VaultProvider | `self, lease_id: str, increment: Optional[int]` | `int` | USED |
| `async revoke_lease` | VaultProvider | `self, lease_id: str` | `None` | USED |
| `async rotate_secret` | VaultProvider | `self, path: str` | `SecretMetadata` | USED |


## casare_rpa.infrastructure.security.workflow_schema

**File:** `src\casare_rpa\infrastructure\security\workflow_schema.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `validate_workflow_json` | - | `workflow_data: Dict[str, Any]` | `WorkflowSchema` | USED |
| `validate_config` | WorkflowNodeSchema | `cls, v: Dict[str, Any]` | `Dict[str, Any]` | USED |
| `validate_node_type` | WorkflowNodeSchema | `cls, v: str` | `str` | UNUSED |
| `validate_nodes_not_empty` | WorkflowSchema | `cls, v: Dict[str, WorkflowNodeSchema]` | `Dict[str, WorkflowNodeSchema]` | UNUSED |


## casare_rpa.infrastructure.tunnel.agent_tunnel

**File:** `src\casare_rpa\infrastructure\tunnel\agent_tunnel.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | AgentTunnel | `self, config: TunnelConfig` | `-` | DUNDER |
| `async _handle_job_assignment` | AgentTunnel | `self, message: Dict[str, Any]` | `None` | INTERNAL |
| `async _handle_message` | AgentTunnel | `self, message: Dict[str, Any]` | `None` | INTERNAL |
| `async _heartbeat_loop` | AgentTunnel | `self` | `None` | INTERNAL |
| `async _receive_loop` | AgentTunnel | `self` | `None` | INTERNAL |
| `async _register` | AgentTunnel | `self` | `None` | INTERNAL |
| `async _send` | AgentTunnel | `self, message: Dict[str, Any]` | `None` | INTERNAL |
| `_set_state` | AgentTunnel | `self, new_state: TunnelState` | `None` | INTERNAL |
| `async connect` | AgentTunnel | `self` | `bool` | USED |
| `async disconnect` | AgentTunnel | `self` | `None` | USED |
| `get_metrics` | AgentTunnel | `self` | `Dict[str, Any]` | USED |
| `is_connected` | AgentTunnel | `self` | `bool` | USED |
| `async report_job_complete` | AgentTunnel | `self, job_id: str, result: Optional[Dict[str, Any]]` | `None` | UNUSED |
| `async report_job_failed` | AgentTunnel | `self, job_id: str, error: str, ...` | `None` | USED |
| `async report_job_progress` | AgentTunnel | `self, job_id: str, progress: float, ...` | `None` | UNUSED |
| `async run_forever` | AgentTunnel | `self` | `None` | USED |
| `state` | AgentTunnel | `self` | `TunnelState` | UNUSED |
| `async update_status` | AgentTunnel | `self, status: str, metadata: Optional[Dict[str, Any]]` | `None` | USED |
| `__post_init__` | TunnelConfig | `self` | `-` | DUNDER |


## casare_rpa.infrastructure.tunnel.mtls

**File:** `src\casare_rpa\infrastructure\tunnel\mtls.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | CertificateManager | `self, certs_dir: Path` | `-` | DUNDER |
| `check_expiration` | CertificateManager | `self, cert_path: Path, warn_days: int` | `tuple[bool, int]` | UNUSED |
| `generate_ca` | CertificateManager | `self, common_name: str, organization: str, ...` | `tuple[Path, Path]` | UNUSED |
| `generate_certificate` | CertificateManager | `self, cert_type: CertificateType, common_name: str, ...` | `tuple[Path, Path]` | UNUSED |
| `get_certificate_info` | CertificateManager | `self, cert_path: Path` | `CertificateInfo` | USED |
| `name_to_dict` | CertificateManager | `name: x509.Name` | `Dict[str, str]` | USED |
| `create_ssl_context` | MTLSConfig | `self` | `ssl.SSLContext` | USED |


## casare_rpa.infrastructure.updater.tuf_updater

**File:** `src\casare_rpa\infrastructure\updater\tuf_updater.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `from_root_json` | TUFRootConfig | `cls, root_data: Dict[str, Any]` | `'TUFRootConfig'` | USED |
| `__init__` | TUFUpdater | `self, repo_url: str, local_cache_dir: Path, ...` | `-` | DUNDER |
| `_check_metadata_expiration` | TUFUpdater | `self, metadata: Dict[str, Any], filename: str` | `None` | INTERNAL |
| `_extract_version` | TUFUpdater | `self, filename: str` | `Optional[str]` | INTERNAL |
| `async _fetch_metadata` | TUFUpdater | `self, session: aiohttp.ClientSession, filename: str` | `Dict[str, Any]` | INTERNAL |
| `_find_latest_target` | TUFUpdater | `self` | `Optional[tuple]` | INTERNAL |
| `_is_newer_version` | TUFUpdater | `self, new_version: str, current_version: str` | `bool` | INTERNAL |
| `_load_trusted_root` | TUFUpdater | `self, root_path: Path` | `None` | INTERNAL |
| `async _refresh_metadata` | TUFUpdater | `self` | `None` | INTERNAL |
| `_verify_metadata_signatures` | TUFUpdater | `self, metadata: Dict[str, Any], filename: str` | `None` | INTERNAL |
| `_verify_single_signature` | TUFUpdater | `self, data: bytes, signature_hex: str, ...` | `bool` | INTERNAL |
| `async apply_update` | TUFUpdater | `self, update_path: Path, restart_app: bool` | `bool` | USED |
| `async check_for_updates` | TUFUpdater | `self` | `Optional[UpdateInfo]` | USED |
| `cleanup_old_versions` | TUFUpdater | `self, keep_count: int` | `int` | USED |
| `async download_update` | TUFUpdater | `self, update_info: UpdateInfo, progress_callback: Optional[Callable[[DownloadProgress], None]]` | `Path` | USED |
| `parse_version` | TUFUpdater | `v: str` | `tuple` | USED |
| `version_key` | TUFUpdater | `item` | `-` | UNUSED |


## casare_rpa.infrastructure.updater.update_manager

**File:** `src\casare_rpa\infrastructure\updater\update_manager.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `get_update_manager` | - | `current_version: Optional[str]` | `UpdateManager` | UNUSED |
| `reset_update_manager` | - | `` | `None` | UNUSED |
| `__init__` | UpdateManager | `self, current_version: str, repo_url: Optional[str], ...` | `-` | DUNDER |
| `async _background_check_loop` | UpdateManager | `self` | `None` | INTERNAL |
| `_set_state` | UpdateManager | `self, state: UpdateState` | `None` | INTERNAL |
| `async apply_update` | UpdateManager | `self, restart: bool` | `bool` | USED |
| `async check_for_updates` | UpdateManager | `self` | `Optional[UpdateInfo]` | USED |
| `cleanup` | UpdateManager | `self` | `int` | USED |
| `clear_skipped_versions` | UpdateManager | `self` | `None` | UNUSED |
| `async download_update` | UpdateManager | `self` | `Optional[Path]` | USED |
| `is_ready_to_install` | UpdateManager | `self` | `bool` | UNUSED |
| `is_update_available` | UpdateManager | `self` | `bool` | UNUSED |
| `is_version_skipped` | UpdateManager | `self, version: str` | `bool` | UNUSED |
| `skip_version` | UpdateManager | `self, version: str` | `None` | USED |
| `async start` | UpdateManager | `self` | `None` | USED |
| `state` | UpdateManager | `self` | `UpdateState` | UNUSED |
| `async stop` | UpdateManager | `self` | `None` | USED |
| `update_info` | UpdateManager | `self` | `Optional[UpdateInfo]` | UNUSED |
