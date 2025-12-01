"""
CasareRPA - Bottleneck Detector

Analyzes workflow execution data to identify performance bottlenecks,
error hotspots, and optimization opportunities.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

from loguru import logger


class BottleneckType(Enum):
    """Types of bottlenecks that can be detected."""

    NODE_SLOW = "node_slow"  # Individual node taking too long
    NODE_FAILING = "node_failing"  # Node with high failure rate
    RESOURCE_CPU = "resource_cpu"  # CPU resource constraint
    RESOURCE_MEMORY = "resource_memory"  # Memory resource constraint
    RESOURCE_NETWORK = "resource_network"  # Network latency
    RESOURCE_EXTERNAL = "resource_external"  # External API/service slow
    PATTERN_SEQUENTIAL = "pattern_sequential"  # Sequential when parallel possible
    PATTERN_RETRY_LOOP = "pattern_retry_loop"  # Excessive retries
    PATTERN_WAIT_LONG = "pattern_wait_long"  # Excessive wait times


class Severity(Enum):
    """Bottleneck severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class BottleneckInfo:
    """Information about a detected bottleneck."""

    bottleneck_type: BottleneckType
    severity: Severity
    location: str  # Node ID or workflow location
    description: str
    impact_ms: float  # Estimated time impact
    frequency: float  # How often this occurs (0.0-1.0)
    recommendation: str
    evidence: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.bottleneck_type.value,
            "severity": self.severity.value,
            "location": self.location,
            "description": self.description,
            "impact_ms": self.impact_ms,
            "frequency": round(self.frequency, 3),
            "recommendation": self.recommendation,
            "evidence": self.evidence,
        }


@dataclass
class NodeExecutionStats:
    """Statistics for a single node's executions."""

    node_id: str
    node_type: str
    execution_count: int
    success_count: int
    failure_count: int
    total_duration_ms: float
    avg_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    p95_duration_ms: float
    error_types: Dict[str, int] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.execution_count == 0:
            return 1.0
        return self.success_count / self.execution_count

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate."""
        return 1.0 - self.success_rate


@dataclass
class DetailedBottleneckAnalysis:
    """Complete bottleneck analysis results with detailed node statistics."""

    workflow_id: str
    analysis_time: datetime
    time_range_hours: int
    total_executions: int
    bottlenecks: List[BottleneckInfo] = field(default_factory=list)
    node_stats: List[NodeExecutionStats] = field(default_factory=list)
    optimization_score: float = 0.0  # 0-100
    potential_savings_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "analysis_time": self.analysis_time.isoformat(),
            "time_range_hours": self.time_range_hours,
            "total_executions": self.total_executions,
            "bottlenecks": [b.to_dict() for b in self.bottlenecks],
            "node_stats": [
                {
                    "node_id": s.node_id,
                    "node_type": s.node_type,
                    "executions": s.execution_count,
                    "success_rate": round(s.success_rate, 3),
                    "avg_duration_ms": round(s.avg_duration_ms, 2),
                    "p95_duration_ms": round(s.p95_duration_ms, 2),
                }
                for s in self.node_stats[:10]  # Top 10
            ],
            "optimization_score": round(self.optimization_score, 1),
            "potential_savings_ms": round(self.potential_savings_ms, 2),
            "bottleneck_count": len(self.bottlenecks),
            "severity_breakdown": self._severity_breakdown(),
        }

    def _severity_breakdown(self) -> Dict[str, int]:
        """Count bottlenecks by severity."""
        breakdown = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for b in self.bottlenecks:
            breakdown[b.severity.value] += 1
        return breakdown


class BottleneckDetector:
    """
    Analyzes workflow executions to identify bottlenecks.

    Uses execution history data to find:
    - Slow nodes (performance bottlenecks)
    - Failing nodes (reliability issues)
    - Resource constraints
    - Optimization opportunities
    """

    # Thresholds for bottleneck detection
    SLOW_NODE_THRESHOLD_MS = 5000  # 5 seconds
    SLOW_NODE_P95_MULTIPLIER = 3.0  # P95 > 3x average
    HIGH_FAILURE_RATE = 0.1  # 10% failure rate
    CRITICAL_FAILURE_RATE = 0.25  # 25% failure rate
    RETRY_PATTERN_THRESHOLD = 3  # More than 3 retries
    LONG_WAIT_THRESHOLD_MS = 10000  # 10 seconds

    def __init__(self):
        """Initialize bottleneck detector."""
        logger.debug("BottleneckDetector initialized")

    def analyze(
        self,
        workflow_id: str,
        execution_data: List[Dict[str, Any]],
        time_range_hours: int = 24,
    ) -> DetailedBottleneckAnalysis:
        """
        Analyze workflow executions for bottlenecks.

        Args:
            workflow_id: Workflow to analyze
            execution_data: List of execution records with node timing
            time_range_hours: Time range for analysis

        Returns:
            Complete bottleneck analysis
        """
        if not execution_data:
            return DetailedBottleneckAnalysis(
                workflow_id=workflow_id,
                analysis_time=datetime.now(),
                time_range_hours=time_range_hours,
                total_executions=0,
                optimization_score=100.0,
            )

        # Calculate node statistics
        node_stats = self._calculate_node_stats(execution_data)

        # Detect various bottleneck types
        bottlenecks = []
        bottlenecks.extend(self._detect_slow_nodes(node_stats))
        bottlenecks.extend(self._detect_failing_nodes(node_stats))
        bottlenecks.extend(self._detect_patterns(execution_data, node_stats))

        # Sort by severity and impact
        bottlenecks.sort(
            key=lambda b: (
                -list(Severity).index(b.severity),
                -b.impact_ms,
            )
        )

        # Calculate optimization score and potential savings
        optimization_score = self._calculate_optimization_score(node_stats, bottlenecks)
        potential_savings = sum(b.impact_ms * b.frequency for b in bottlenecks)

        return DetailedBottleneckAnalysis(
            workflow_id=workflow_id,
            analysis_time=datetime.now(),
            time_range_hours=time_range_hours,
            total_executions=len(execution_data),
            bottlenecks=bottlenecks,
            node_stats=node_stats,
            optimization_score=optimization_score,
            potential_savings_ms=potential_savings,
        )

    def _calculate_node_stats(
        self, execution_data: List[Dict[str, Any]]
    ) -> List[NodeExecutionStats]:
        """Calculate per-node execution statistics."""
        node_data: Dict[str, Dict[str, Any]] = {}

        for execution in execution_data:
            node_timings = execution.get("node_timings", {})

            for node_id, timing in node_timings.items():
                if node_id not in node_data:
                    node_data[node_id] = {
                        "node_type": timing.get("node_type", "unknown"),
                        "durations": [],
                        "success_count": 0,
                        "failure_count": 0,
                        "errors": {},
                    }

                duration = timing.get("duration_ms", 0)
                node_data[node_id]["durations"].append(duration)

                if timing.get("success", True):
                    node_data[node_id]["success_count"] += 1
                else:
                    node_data[node_id]["failure_count"] += 1
                    error = timing.get("error_type", "unknown")
                    node_data[node_id]["errors"][error] = (
                        node_data[node_id]["errors"].get(error, 0) + 1
                    )

        # Convert to NodeExecutionStats
        stats = []
        for node_id, data in node_data.items():
            durations = data["durations"]
            if not durations:
                continue

            sorted_durations = sorted(durations)
            p95_idx = int(len(sorted_durations) * 0.95)

            stats.append(
                NodeExecutionStats(
                    node_id=node_id,
                    node_type=data["node_type"],
                    execution_count=len(durations),
                    success_count=data["success_count"],
                    failure_count=data["failure_count"],
                    total_duration_ms=sum(durations),
                    avg_duration_ms=sum(durations) / len(durations),
                    min_duration_ms=min(durations),
                    max_duration_ms=max(durations),
                    p95_duration_ms=sorted_durations[
                        min(p95_idx, len(sorted_durations) - 1)
                    ],
                    error_types=data["errors"],
                )
            )

        # Sort by total duration (most time spent first)
        stats.sort(key=lambda s: -s.total_duration_ms)

        return stats

    def _detect_slow_nodes(
        self, node_stats: List[NodeExecutionStats]
    ) -> List[BottleneckInfo]:
        """Detect slow node bottlenecks."""
        bottlenecks = []

        for stat in node_stats:
            # Check if node is consistently slow
            if stat.avg_duration_ms > self.SLOW_NODE_THRESHOLD_MS:
                severity = (
                    Severity.HIGH
                    if stat.avg_duration_ms > self.SLOW_NODE_THRESHOLD_MS * 2
                    else Severity.MEDIUM
                )

                bottlenecks.append(
                    BottleneckInfo(
                        bottleneck_type=BottleneckType.NODE_SLOW,
                        severity=severity,
                        location=stat.node_id,
                        description=f"Node '{stat.node_id}' averages {stat.avg_duration_ms:.0f}ms",
                        impact_ms=stat.avg_duration_ms - self.SLOW_NODE_THRESHOLD_MS,
                        frequency=1.0,  # Happens every execution
                        recommendation=self._get_slow_node_recommendation(stat),
                        evidence={
                            "avg_duration_ms": stat.avg_duration_ms,
                            "p95_duration_ms": stat.p95_duration_ms,
                            "execution_count": stat.execution_count,
                        },
                    )
                )

            # Check for high variance (P95 >> average)
            elif (
                stat.p95_duration_ms
                > stat.avg_duration_ms * self.SLOW_NODE_P95_MULTIPLIER
            ):
                bottlenecks.append(
                    BottleneckInfo(
                        bottleneck_type=BottleneckType.NODE_SLOW,
                        severity=Severity.LOW,
                        location=stat.node_id,
                        description=f"Node '{stat.node_id}' has high variance (P95: {stat.p95_duration_ms:.0f}ms)",
                        impact_ms=stat.p95_duration_ms - stat.avg_duration_ms,
                        frequency=0.05,  # Affects 5% of executions
                        recommendation="Investigate intermittent slowness, check for resource contention or network issues",
                        evidence={
                            "avg_duration_ms": stat.avg_duration_ms,
                            "p95_duration_ms": stat.p95_duration_ms,
                            "variance_ratio": stat.p95_duration_ms
                            / stat.avg_duration_ms,
                        },
                    )
                )

        return bottlenecks

    def _detect_failing_nodes(
        self, node_stats: List[NodeExecutionStats]
    ) -> List[BottleneckInfo]:
        """Detect nodes with high failure rates."""
        bottlenecks = []

        for stat in node_stats:
            if stat.failure_rate >= self.CRITICAL_FAILURE_RATE:
                severity = Severity.CRITICAL
            elif stat.failure_rate >= self.HIGH_FAILURE_RATE:
                severity = Severity.HIGH
            else:
                continue

            # Find most common error type
            most_common_error = "unknown"
            if stat.error_types:
                most_common_error = max(stat.error_types, key=stat.error_types.get)

            bottlenecks.append(
                BottleneckInfo(
                    bottleneck_type=BottleneckType.NODE_FAILING,
                    severity=severity,
                    location=stat.node_id,
                    description=f"Node '{stat.node_id}' fails {stat.failure_rate*100:.1f}% of the time",
                    impact_ms=stat.avg_duration_ms,  # Time wasted on failures
                    frequency=stat.failure_rate,
                    recommendation=self._get_failing_node_recommendation(
                        stat, most_common_error
                    ),
                    evidence={
                        "failure_rate": stat.failure_rate,
                        "failure_count": stat.failure_count,
                        "error_types": stat.error_types,
                        "most_common_error": most_common_error,
                    },
                )
            )

        return bottlenecks

    def _detect_patterns(
        self,
        execution_data: List[Dict[str, Any]],
        node_stats: List[NodeExecutionStats],
    ) -> List[BottleneckInfo]:
        """Detect execution pattern bottlenecks."""
        bottlenecks = []

        # Detect excessive wait times
        for stat in node_stats:
            if "wait" in stat.node_type.lower():
                if stat.avg_duration_ms > self.LONG_WAIT_THRESHOLD_MS:
                    bottlenecks.append(
                        BottleneckInfo(
                            bottleneck_type=BottleneckType.PATTERN_WAIT_LONG,
                            severity=Severity.LOW,
                            location=stat.node_id,
                            description=f"Wait node '{stat.node_id}' waits {stat.avg_duration_ms:.0f}ms on average",
                            impact_ms=stat.avg_duration_ms
                            - self.LONG_WAIT_THRESHOLD_MS,
                            frequency=1.0,
                            recommendation="Consider reducing wait time or using event-driven waits",
                            evidence={
                                "avg_wait_ms": stat.avg_duration_ms,
                                "max_wait_ms": stat.max_duration_ms,
                            },
                        )
                    )

        # Detect retry patterns
        retry_nodes = [s for s in node_stats if "retry" in s.node_type.lower()]
        for stat in retry_nodes:
            if (
                stat.execution_count
                > len(execution_data) * self.RETRY_PATTERN_THRESHOLD
            ):
                bottlenecks.append(
                    BottleneckInfo(
                        bottleneck_type=BottleneckType.PATTERN_RETRY_LOOP,
                        severity=Severity.MEDIUM,
                        location=stat.node_id,
                        description=f"Excessive retries detected at '{stat.node_id}'",
                        impact_ms=stat.total_duration_ms / len(execution_data),
                        frequency=0.8,
                        recommendation="Fix root cause of failures to reduce retry overhead",
                        evidence={
                            "retry_count": stat.execution_count,
                            "avg_retries_per_execution": stat.execution_count
                            / len(execution_data),
                        },
                    )
                )

        return bottlenecks

    def _calculate_optimization_score(
        self,
        node_stats: List[NodeExecutionStats],
        bottlenecks: List[BottleneckInfo],
    ) -> float:
        """Calculate workflow optimization score (0-100)."""
        if not node_stats:
            return 100.0

        score = 100.0

        # Deduct for bottlenecks
        for b in bottlenecks:
            if b.severity == Severity.CRITICAL:
                score -= 20
            elif b.severity == Severity.HIGH:
                score -= 10
            elif b.severity == Severity.MEDIUM:
                score -= 5
            elif b.severity == Severity.LOW:
                score -= 2

        # Deduct for overall failure rate
        total_failures = sum(s.failure_count for s in node_stats)
        total_executions = sum(s.execution_count for s in node_stats)
        if total_executions > 0:
            failure_rate = total_failures / total_executions
            score -= failure_rate * 50  # Up to 50 points for 100% failures

        return max(0.0, min(100.0, score))

    def _get_slow_node_recommendation(self, stat: NodeExecutionStats) -> str:
        """Get recommendation for slow node."""
        node_type = stat.node_type.lower()

        if "http" in node_type or "api" in node_type:
            return "Consider caching responses, using connection pooling, or optimizing API queries"
        elif "database" in node_type or "query" in node_type:
            return "Optimize database queries, add indexes, or use connection pooling"
        elif "browser" in node_type or "click" in node_type:
            return "Use more specific selectors, reduce page complexity, or add explicit waits"
        elif "file" in node_type:
            return (
                "Use async file operations, batch file processing, or reduce file sizes"
            )
        else:
            return "Profile this node to identify the slow operation, consider async execution"

    def _get_failing_node_recommendation(
        self, stat: NodeExecutionStats, error_type: str
    ) -> str:
        """Get recommendation for failing node."""
        error_lower = error_type.lower()

        if "timeout" in error_lower:
            return "Increase timeout, check network connectivity, or optimize the target operation"
        elif "element" in error_lower or "selector" in error_lower:
            return "Update selectors, enable self-healing, or add explicit waits"
        elif "network" in error_lower or "connection" in error_lower:
            return "Add retry logic with backoff, check network stability"
        elif "permission" in error_lower or "auth" in error_lower:
            return "Verify credentials, check token expiration, update authentication"
        else:
            return f"Investigate '{error_type}' errors, add error handling, enable retry logic"


__all__ = [
    "BottleneckDetector",
    "BottleneckInfo",
    "DetailedBottleneckAnalysis",
    "BottleneckType",
    "Severity",
    "NodeExecutionStats",
]
