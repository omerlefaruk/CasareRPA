"""
REST API endpoints for advanced analytics.

Provides process mining, bottleneck detection, and execution analysis
for workflow optimization and monitoring.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from loguru import logger
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from casare_rpa.infrastructure.analytics import (
    # Process Mining
    get_process_miner,
    ExecutionTrace,
    Activity,
    ActivityStatus,
    BottleneckDetector,
    ExecutionAnalyzer,
)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Singleton instances
_bottleneck_detector: Optional[BottleneckDetector] = None
_execution_analyzer: Optional[ExecutionAnalyzer] = None


def get_bottleneck_detector() -> BottleneckDetector:
    """Get or create bottleneck detector singleton."""
    global _bottleneck_detector
    if _bottleneck_detector is None:
        _bottleneck_detector = BottleneckDetector()
    return _bottleneck_detector


def get_execution_analyzer() -> ExecutionAnalyzer:
    """Get or create execution analyzer singleton."""
    global _execution_analyzer
    if _execution_analyzer is None:
        _execution_analyzer = ExecutionAnalyzer()
    return _execution_analyzer


# =============================================================================
# Pydantic Models for API Responses
# =============================================================================


class ProcessModelResponse(BaseModel):
    """Response model for discovered process."""

    workflow_id: str
    nodes: List[str]
    node_types: Dict[str, str]
    edges: Dict[str, Dict[str, Dict[str, Any]]]
    variants: Dict[str, int]
    variant_paths: Dict[str, List[str]]
    entry_nodes: List[str]
    exit_nodes: List[str]
    loop_nodes: List[str]
    parallel_pairs: List[List[str]]
    trace_count: int
    most_common_path: List[str]
    mermaid_diagram: str


class VariantInfo(BaseModel):
    """Information about a process variant."""

    variant_hash: str
    path: List[str]
    count: int
    percentage: float


class VariantsResponse(BaseModel):
    """Response for variant analysis."""

    workflow_id: str
    total_traces: int
    variant_count: int
    variants: List[VariantInfo]


class ConformanceCheckRequest(BaseModel):
    """Request to check conformance of a trace."""

    workflow_id: str
    trace_activities: List[Dict[str, Any]]


class ConformanceSummaryResponse(BaseModel):
    """Summary of conformance checking."""

    workflow_id: str
    total_traces: int
    conformant_traces: int
    conformance_rate: float
    average_fitness: float
    average_precision: float
    deviation_summary: Dict[str, int]


class ProcessInsightResponse(BaseModel):
    """Response model for process insights."""

    category: str
    title: str
    description: str
    impact: str
    affected_nodes: List[str]
    recommendation: str
    data: Dict[str, Any]


class BottleneckResponse(BaseModel):
    """Response model for a bottleneck."""

    type: str
    severity: str
    location: str
    description: str
    impact_ms: float
    frequency: float
    recommendation: str
    evidence: Dict[str, Any]


class NodeStatsResponse(BaseModel):
    """Response model for node execution statistics."""

    node_id: str
    node_type: str
    execution_count: int
    success_count: int
    failure_count: int
    success_rate: float
    avg_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    p95_duration_ms: float
    error_types: Dict[str, int]


class BottleneckAnalysisResponse(BaseModel):
    """Complete bottleneck analysis response."""

    workflow_id: str
    analysis_period_days: int
    total_executions: int
    bottlenecks: List[BottleneckResponse]
    node_stats: List[NodeStatsResponse]
    slowest_nodes: List[str]
    failing_nodes: List[str]
    recommendations: List[str]


class TrendResponse(BaseModel):
    """Response model for a trend."""

    direction: str
    current_value: float
    previous_value: float
    change_percent: float
    confidence: float


class InsightResponse(BaseModel):
    """Response model for an execution insight."""

    type: str
    title: str
    description: str
    significance: float
    data: Dict[str, Any]
    recommended_action: Optional[str]


class TimeDistributionResponse(BaseModel):
    """Response for execution time distribution."""

    hour_distribution: Dict[int, int]
    day_of_week_distribution: Dict[int, int]
    peak_hour: int
    peak_day: int


class ExecutionAnalysisResponse(BaseModel):
    """Complete execution analysis response."""

    workflow_id: str
    analysis_period_days: int
    total_executions: int
    duration_trend: TrendResponse
    success_rate_trend: TrendResponse
    time_distribution: TimeDistributionResponse
    insights: List[InsightResponse]
    summary: Dict[str, Any]


# =============================================================================
# Process Mining Endpoints
# =============================================================================


@router.get("/analytics/process-mining/discover/{workflow_id}")
@limiter.limit("30/minute")
async def discover_process(
    request: Request,
    workflow_id: str,
    limit: int = Query(100, ge=10, le=1000, description="Max traces to analyze"),
) -> ProcessModelResponse:
    """
    Discover process model from workflow execution traces.

    Uses Direct-Follows Graph (DFG) algorithm to build a process model
    from historical execution data.

    Returns:
        - Node graph with frequencies and durations
        - Execution variants and their counts
        - Entry/exit nodes
        - Loop and parallel activity detection
        - Mermaid diagram for visualization
    """
    logger.info(f"Discovering process for workflow: {workflow_id}")

    try:
        miner = get_process_miner()
        traces = miner.event_log.get_traces_for_workflow(workflow_id, limit=limit)

        if not traces:
            raise HTTPException(
                status_code=404,
                detail=f"No execution traces found for workflow {workflow_id}",
            )

        model = miner.discover_process(workflow_id, limit=limit)

        return ProcessModelResponse(
            workflow_id=model.workflow_id,
            nodes=list(model.nodes),
            node_types=model.node_types,
            edges={
                src: {
                    tgt: {
                        "frequency": edge.frequency,
                        "avg_duration_ms": edge.avg_duration_ms,
                        "error_rate": edge.error_rate,
                    }
                    for tgt, edge in targets.items()
                }
                for src, targets in model.edges.items()
            },
            variants=model.variants,
            variant_paths=model.variant_paths,
            entry_nodes=list(model.entry_nodes),
            exit_nodes=list(model.exit_nodes),
            loop_nodes=list(model.loop_nodes),
            parallel_pairs=[list(pair) for pair in model.parallel_pairs],
            trace_count=model.trace_count,
            most_common_path=model.get_most_common_path(),
            mermaid_diagram=model.to_mermaid(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Process discovery failed: {e}")
        raise HTTPException(status_code=500, detail=f"Process discovery failed: {e}")


@router.get("/analytics/process-mining/variants/{workflow_id}")
@limiter.limit("30/minute")
async def get_variants(
    request: Request,
    workflow_id: str,
    limit: int = Query(100, ge=10, le=1000, description="Max traces to analyze"),
) -> VariantsResponse:
    """
    Get all execution variants for a workflow.

    Variants are unique execution paths through the workflow.
    Returns variant paths sorted by frequency.
    """
    logger.info(f"Getting variants for workflow: {workflow_id}")

    try:
        miner = get_process_miner()
        traces = miner.event_log.get_traces_for_workflow(workflow_id, limit=limit)

        if not traces:
            raise HTTPException(
                status_code=404,
                detail=f"No execution traces found for workflow {workflow_id}",
            )

        model = miner.discover_process(workflow_id, limit=limit)

        # Build variant info list
        total_count = sum(model.variants.values())
        variants = []
        for variant_hash, count in sorted(model.variants.items(), key=lambda x: x[1], reverse=True):
            path = model.variant_paths.get(variant_hash, [])
            variants.append(
                VariantInfo(
                    variant_hash=variant_hash,
                    path=path,
                    count=count,
                    percentage=round(count / total_count * 100, 2) if total_count else 0,
                )
            )

        return VariantsResponse(
            workflow_id=workflow_id,
            total_traces=total_count,
            variant_count=len(variants),
            variants=variants,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Variant analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Variant analysis failed: {e}")


@router.get("/analytics/process-mining/conformance/{workflow_id}")
@limiter.limit("20/minute")
async def check_conformance(
    request: Request,
    workflow_id: str,
    limit: int = Query(50, ge=10, le=500, description="Max traces to check"),
) -> ConformanceSummaryResponse:
    """
    Check conformance of recent executions against discovered model.

    Compares actual execution traces to the expected process model
    and identifies deviations.

    Returns:
        - Conformance rate
        - Fitness and precision scores
        - Deviation summary by type
    """
    logger.info(f"Checking conformance for workflow: {workflow_id}")

    try:
        miner = get_process_miner()
        traces = miner.event_log.get_traces_for_workflow(workflow_id, limit=limit)

        if not traces:
            raise HTTPException(
                status_code=404,
                detail=f"No execution traces found for workflow {workflow_id}",
            )

        # First discover the model, then check conformance
        miner.discover_process(workflow_id, limit=limit)
        result = miner.check_conformance_batch(workflow_id, limit=limit)

        return ConformanceSummaryResponse(
            workflow_id=workflow_id,
            total_traces=result["total_traces"],
            conformant_traces=result["conformant_traces"],
            conformance_rate=round(result["conformance_rate"], 3),
            average_fitness=round(result["average_fitness"], 3),
            average_precision=round(result["average_precision"], 3),
            deviation_summary=result["deviation_summary"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Conformance checking failed: {e}")
        raise HTTPException(status_code=500, detail=f"Conformance checking failed: {e}")


@router.get("/analytics/process-mining/insights/{workflow_id}")
@limiter.limit("20/minute")
async def get_process_insights(
    request: Request,
    workflow_id: str,
    limit: int = Query(100, ge=10, le=1000, description="Max traces to analyze"),
) -> List[ProcessInsightResponse]:
    """
    Get AI-generated insights for process optimization.

    Analyzes the process model and execution traces to identify:
    - Bottleneck nodes
    - Parallelization opportunities
    - Simplification suggestions
    - Error patterns
    """
    logger.info(f"Generating insights for workflow: {workflow_id}")

    try:
        miner = get_process_miner()
        traces = miner.event_log.get_traces_for_workflow(workflow_id, limit=limit)

        if not traces:
            raise HTTPException(
                status_code=404,
                detail=f"No execution traces found for workflow {workflow_id}",
            )

        insights = miner.get_insights(workflow_id, limit=limit)

        return [
            ProcessInsightResponse(
                category=insight.category.value,
                title=insight.title,
                description=insight.description,
                impact=insight.impact,
                affected_nodes=insight.affected_nodes,
                recommendation=insight.recommendation,
                data=insight.data,
            )
            for insight in insights
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Insight generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Insight generation failed: {e}")


@router.get("/analytics/process-mining/workflows")
@limiter.limit("60/minute")
async def list_workflows_with_traces(request: Request) -> List[Dict[str, Any]]:
    """
    List all workflows that have execution traces.

    Returns workflow IDs and their trace counts.
    """
    try:
        miner = get_process_miner()
        workflow_ids = miner.event_log.get_all_workflows()

        result = []
        for wf_id in workflow_ids:
            trace_count = miner.event_log.get_trace_count(wf_id)
            result.append({"workflow_id": wf_id, "trace_count": trace_count})

        return sorted(result, key=lambda x: x["trace_count"], reverse=True)

    except Exception as e:
        logger.error(f"Failed to list workflows: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list workflows: {e}")


# =============================================================================
# Bottleneck Detection Endpoints
# =============================================================================


@router.get("/analytics/bottlenecks/{workflow_id}")
@limiter.limit("20/minute")
async def analyze_bottlenecks(
    request: Request,
    workflow_id: str,
    days: int = Query(7, ge=1, le=90, description="Analysis period in days"),
) -> BottleneckAnalysisResponse:
    """
    Analyze workflow for performance bottlenecks.

    Identifies:
    - Slow nodes (duration outliers)
    - Failing nodes (high error rates)
    - Resource constraints (CPU, memory, network)
    - Pattern issues (sequential when parallel possible, retry loops)

    Returns bottlenecks sorted by severity and impact.
    """
    logger.info(f"Analyzing bottlenecks for workflow: {workflow_id}, days={days}")

    try:
        miner = get_process_miner()
        detector = get_bottleneck_detector()

        # Get traces for the analysis period
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days)
        traces = miner.event_log.get_traces_in_timerange(start_time, end_time, workflow_id)

        if not traces:
            raise HTTPException(
                status_code=404,
                detail=f"No execution traces found for workflow {workflow_id} in the last {days} days",
            )

        # Run bottleneck analysis
        analysis = detector.analyze(traces)

        # Build response
        bottlenecks = [
            BottleneckResponse(
                type=b.bottleneck_type.value,
                severity=b.severity.value,
                location=b.location,
                description=b.description,
                impact_ms=b.impact_ms,
                frequency=b.frequency,
                recommendation=b.recommendation,
                evidence=b.evidence,
            )
            for b in analysis.bottlenecks
        ]

        node_stats = [
            NodeStatsResponse(
                node_id=ns.node_id,
                node_type=ns.node_type,
                execution_count=ns.execution_count,
                success_count=ns.success_count,
                failure_count=ns.failure_count,
                success_rate=round(ns.success_rate, 3),
                avg_duration_ms=round(ns.avg_duration_ms, 2),
                min_duration_ms=round(ns.min_duration_ms, 2),
                max_duration_ms=round(ns.max_duration_ms, 2),
                p95_duration_ms=round(ns.p95_duration_ms, 2),
                error_types=ns.error_types,
            )
            for ns in analysis.node_stats
        ]

        return BottleneckAnalysisResponse(
            workflow_id=workflow_id,
            analysis_period_days=days,
            total_executions=len(traces),
            bottlenecks=bottlenecks,
            node_stats=node_stats,
            slowest_nodes=analysis.slowest_nodes[:5],
            failing_nodes=analysis.failing_nodes[:5],
            recommendations=analysis.recommendations,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bottleneck analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Bottleneck analysis failed: {e}")


@router.get("/analytics/bottlenecks/{workflow_id}/nodes/{node_id}")
@limiter.limit("30/minute")
async def get_node_performance(
    request: Request,
    workflow_id: str,
    node_id: str,
    days: int = Query(7, ge=1, le=90, description="Analysis period in days"),
) -> NodeStatsResponse:
    """
    Get detailed performance statistics for a specific node.

    Returns execution counts, duration statistics, and error breakdown.
    """
    logger.info(f"Getting node performance: {workflow_id}/{node_id}")

    try:
        miner = get_process_miner()
        detector = get_bottleneck_detector()

        # Get traces
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days)
        traces = miner.event_log.get_traces_in_timerange(start_time, end_time, workflow_id)

        if not traces:
            raise HTTPException(
                status_code=404,
                detail=f"No execution traces found for workflow {workflow_id}",
            )

        # Analyze and find the specific node
        analysis = detector.analyze(traces)

        for ns in analysis.node_stats:
            if ns.node_id == node_id:
                return NodeStatsResponse(
                    node_id=ns.node_id,
                    node_type=ns.node_type,
                    execution_count=ns.execution_count,
                    success_count=ns.success_count,
                    failure_count=ns.failure_count,
                    success_rate=round(ns.success_rate, 3),
                    avg_duration_ms=round(ns.avg_duration_ms, 2),
                    min_duration_ms=round(ns.min_duration_ms, 2),
                    max_duration_ms=round(ns.max_duration_ms, 2),
                    p95_duration_ms=round(ns.p95_duration_ms, 2),
                    error_types=ns.error_types,
                )

        raise HTTPException(
            status_code=404,
            detail=f"Node {node_id} not found in workflow {workflow_id}",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Node performance query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Node performance query failed: {e}")


# =============================================================================
# Execution Analysis Endpoints
# =============================================================================


@router.get("/analytics/execution/{workflow_id}")
@limiter.limit("20/minute")
async def analyze_execution(
    request: Request,
    workflow_id: str,
    days: int = Query(14, ge=1, le=90, description="Analysis period in days"),
) -> ExecutionAnalysisResponse:
    """
    Analyze execution patterns and trends for a workflow.

    Provides:
    - Duration trends (improving/degrading/stable)
    - Success rate trends
    - Time distribution (peak hours, days)
    - AI-generated insights and recommendations
    """
    logger.info(f"Analyzing execution for workflow: {workflow_id}, days={days}")

    try:
        miner = get_process_miner()
        analyzer = get_execution_analyzer()

        # Get traces for analysis
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days)
        traces = miner.event_log.get_traces_in_timerange(start_time, end_time, workflow_id)

        if not traces:
            raise HTTPException(
                status_code=404,
                detail=f"No execution traces found for workflow {workflow_id} in the last {days} days",
            )

        # Run analysis
        result = analyzer.analyze(traces, days=days)

        # Build response
        duration_trend = TrendResponse(
            direction=result.duration_trend.direction.value,
            current_value=result.duration_trend.current_avg_ms,
            previous_value=result.duration_trend.previous_avg_ms,
            change_percent=result.duration_trend.change_percent,
            confidence=result.duration_trend.confidence,
        )

        success_trend = TrendResponse(
            direction=result.success_rate_trend.direction.value,
            current_value=result.success_rate_trend.current_rate,
            previous_value=result.success_rate_trend.previous_rate,
            change_percent=result.success_rate_trend.change_percent,
            confidence=result.success_rate_trend.confidence,
        )

        time_dist = TimeDistributionResponse(
            hour_distribution=result.time_distribution.hour_distribution,
            day_of_week_distribution=result.time_distribution.day_of_week_distribution,
            peak_hour=result.time_distribution.peak_hour,
            peak_day=result.time_distribution.peak_day,
        )

        insights = [
            InsightResponse(
                type=i.insight_type.value,
                title=i.title,
                description=i.description,
                significance=i.significance,
                data=i.data,
                recommended_action=i.recommended_action,
            )
            for i in result.insights
        ]

        return ExecutionAnalysisResponse(
            workflow_id=workflow_id,
            analysis_period_days=days,
            total_executions=len(traces),
            duration_trend=duration_trend,
            success_rate_trend=success_trend,
            time_distribution=time_dist,
            insights=insights,
            summary=result.summary,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Execution analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Execution analysis failed: {e}")


@router.get("/analytics/execution/{workflow_id}/timeline")
@limiter.limit("30/minute")
async def get_execution_timeline(
    request: Request,
    workflow_id: str,
    days: int = Query(7, ge=1, le=30, description="Timeline period in days"),
    granularity: str = Query("hour", description="Granularity: hour, day"),
) -> Dict[str, Any]:
    """
    Get execution timeline data for visualization.

    Returns time-series data suitable for charts:
    - Execution counts over time
    - Success/failure rates over time
    - Average duration over time
    """
    logger.info(
        f"Getting execution timeline: {workflow_id}, days={days}, granularity={granularity}"
    )

    try:
        miner = get_process_miner()

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days)
        traces = miner.event_log.get_traces_in_timerange(start_time, end_time, workflow_id)

        if not traces:
            raise HTTPException(
                status_code=404,
                detail=f"No execution traces found for workflow {workflow_id}",
            )

        # Aggregate by time bucket
        timeline: Dict[str, Dict[str, Any]] = {}

        for trace in traces:
            if granularity == "hour":
                bucket = trace.start_time.strftime("%Y-%m-%d %H:00")
            else:  # day
                bucket = trace.start_time.strftime("%Y-%m-%d")

            if bucket not in timeline:
                timeline[bucket] = {
                    "timestamp": bucket,
                    "executions": 0,
                    "successes": 0,
                    "failures": 0,
                    "total_duration_ms": 0,
                }

            timeline[bucket]["executions"] += 1
            if trace.status == "completed":
                timeline[bucket]["successes"] += 1
            elif trace.status == "failed":
                timeline[bucket]["failures"] += 1
            timeline[bucket]["total_duration_ms"] += trace.total_duration_ms

        # Calculate averages and sort
        data_points = []
        for bucket, data in sorted(timeline.items()):
            data_points.append(
                {
                    "timestamp": data["timestamp"],
                    "executions": data["executions"],
                    "successes": data["successes"],
                    "failures": data["failures"],
                    "success_rate": round(data["successes"] / data["executions"], 3)
                    if data["executions"]
                    else 0,
                    "avg_duration_ms": round(data["total_duration_ms"] / data["executions"], 2)
                    if data["executions"]
                    else 0,
                }
            )

        return {
            "workflow_id": workflow_id,
            "period_days": days,
            "granularity": granularity,
            "data_points": data_points,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Timeline query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Timeline query failed: {e}")


# =============================================================================
# Event Log Management Endpoints
# =============================================================================


@router.post("/analytics/traces")
@limiter.limit("100/minute")
async def add_trace(request: Request, trace_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Add an execution trace to the event log.

    Used by robots and the execution engine to record workflow executions.

    Required fields:
    - case_id: Unique execution ID
    - workflow_id: Workflow being executed
    - workflow_name: Human-readable name
    - activities: List of activity records
    - start_time: ISO timestamp
    """
    try:
        miner = get_process_miner()

        # Parse activities
        activities = []
        for act_data in trace_data.get("activities", []):
            activities.append(
                Activity(
                    node_id=act_data["node_id"],
                    node_type=act_data.get("node_type", "unknown"),
                    timestamp=datetime.fromisoformat(act_data["timestamp"]),
                    duration_ms=act_data.get("duration_ms", 0),
                    status=ActivityStatus(act_data.get("status", "completed")),
                    inputs=act_data.get("inputs", {}),
                    outputs=act_data.get("outputs", {}),
                    error_message=act_data.get("error_message"),
                )
            )

        # Create trace
        trace = ExecutionTrace(
            case_id=trace_data["case_id"],
            workflow_id=trace_data["workflow_id"],
            workflow_name=trace_data.get("workflow_name", trace_data["workflow_id"]),
            activities=activities,
            start_time=datetime.fromisoformat(trace_data["start_time"]),
            end_time=datetime.fromisoformat(trace_data["end_time"])
            if trace_data.get("end_time")
            else None,
            status=trace_data.get("status", "running"),
            robot_id=trace_data.get("robot_id"),
        )

        miner.event_log.add_trace(trace)

        return {"status": "ok", "case_id": trace.case_id, "variant": trace.variant}

    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing required field: {e}")
    except Exception as e:
        logger.error(f"Failed to add trace: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add trace: {e}")


@router.get("/analytics/traces/{workflow_id}")
@limiter.limit("60/minute")
async def get_traces(
    request: Request,
    workflow_id: str,
    limit: int = Query(50, ge=1, le=500),
    status: Optional[str] = Query(None, description="Filter by status"),
) -> List[Dict[str, Any]]:
    """
    Get execution traces for a workflow.

    Returns trace details including activities, duration, and status.
    """
    try:
        miner = get_process_miner()
        traces = miner.event_log.get_traces_for_workflow(workflow_id, limit=limit, status=status)

        return [trace.to_dict() for trace in traces]

    except Exception as e:
        logger.error(f"Failed to get traces: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get traces: {e}")


@router.delete("/analytics/traces/{workflow_id}")
@limiter.limit("10/minute")
async def clear_traces(request: Request, workflow_id: str) -> Dict[str, str]:
    """
    Clear all traces for a workflow.

    Use with caution - this removes all historical execution data.
    """
    try:
        miner = get_process_miner()
        count = miner.event_log.get_trace_count(workflow_id)
        miner.event_log.clear(workflow_id)

        logger.info(f"Cleared {count} traces for workflow {workflow_id}")
        return {"status": "ok", "cleared_count": str(count)}

    except Exception as e:
        logger.error(f"Failed to clear traces: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear traces: {e}")
