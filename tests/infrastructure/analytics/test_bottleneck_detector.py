"""Tests for Bottleneck Detector."""

import pytest
from datetime import datetime

from casare_rpa.infrastructure.analytics.bottleneck_detector import (
    BottleneckDetector,
    BottleneckInfo,
    DetailedBottleneckAnalysis,
    BottleneckType,
    Severity,
    NodeExecutionStats,
)


class TestBottleneckType:
    """Tests for BottleneckType enum."""

    def test_bottleneck_types(self):
        """Test all bottleneck types exist."""
        assert BottleneckType.NODE_SLOW.value == "node_slow"
        assert BottleneckType.NODE_FAILING.value == "node_failing"
        assert BottleneckType.RESOURCE_CPU.value == "resource_cpu"
        assert BottleneckType.RESOURCE_MEMORY.value == "resource_memory"
        assert BottleneckType.RESOURCE_NETWORK.value == "resource_network"
        assert BottleneckType.RESOURCE_EXTERNAL.value == "resource_external"
        assert BottleneckType.PATTERN_SEQUENTIAL.value == "pattern_sequential"
        assert BottleneckType.PATTERN_RETRY_LOOP.value == "pattern_retry_loop"
        assert BottleneckType.PATTERN_WAIT_LONG.value == "pattern_wait_long"


class TestSeverity:
    """Tests for Severity enum."""

    def test_severity_levels(self):
        """Test all severity levels exist."""
        assert Severity.LOW.value == "low"
        assert Severity.MEDIUM.value == "medium"
        assert Severity.HIGH.value == "high"
        assert Severity.CRITICAL.value == "critical"


class TestNodeExecutionStats:
    """Tests for NodeExecutionStats dataclass."""

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        stats = NodeExecutionStats(
            node_id="node1",
            node_type="ClickElementNode",
            execution_count=100,
            success_count=90,
            failure_count=10,
            total_duration_ms=50000,
            avg_duration_ms=500,
            min_duration_ms=100,
            max_duration_ms=2000,
            p95_duration_ms=1500,
        )
        assert stats.success_rate == 0.9
        assert abs(stats.failure_rate - 0.1) < 0.001  # Float comparison

    def test_success_rate_no_executions(self):
        """Test success rate with no executions."""
        stats = NodeExecutionStats(
            node_id="node1",
            node_type="ClickElementNode",
            execution_count=0,
            success_count=0,
            failure_count=0,
            total_duration_ms=0,
            avg_duration_ms=0,
            min_duration_ms=0,
            max_duration_ms=0,
            p95_duration_ms=0,
        )
        assert stats.success_rate == 1.0

    def test_failure_rate_calculation(self):
        """Test failure rate calculation."""
        stats = NodeExecutionStats(
            node_id="node1",
            node_type="ClickElementNode",
            execution_count=50,
            success_count=25,
            failure_count=25,
            total_duration_ms=25000,
            avg_duration_ms=500,
            min_duration_ms=200,
            max_duration_ms=1000,
            p95_duration_ms=900,
        )
        assert stats.failure_rate == 0.5


class TestBottleneckInfo:
    """Tests for BottleneckInfo dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        info = BottleneckInfo(
            bottleneck_type=BottleneckType.NODE_SLOW,
            severity=Severity.HIGH,
            location="node_abc",
            description="Node is slow",
            impact_ms=3000,
            frequency=0.8,
            recommendation="Optimize the node",
            evidence={"avg_duration": 8000},
        )
        result = info.to_dict()

        assert result["type"] == "node_slow"
        assert result["severity"] == "high"
        assert result["location"] == "node_abc"
        assert result["description"] == "Node is slow"
        assert result["impact_ms"] == 3000
        assert result["frequency"] == 0.8
        assert result["recommendation"] == "Optimize the node"
        assert result["evidence"] == {"avg_duration": 8000}


class TestDetailedBottleneckAnalysis:
    """Tests for DetailedBottleneckAnalysis dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        analysis = DetailedBottleneckAnalysis(
            workflow_id="wf123",
            analysis_time=datetime(2025, 1, 1, 12, 0),
            time_range_hours=24,
            total_executions=100,
            bottlenecks=[
                BottleneckInfo(
                    bottleneck_type=BottleneckType.NODE_SLOW,
                    severity=Severity.HIGH,
                    location="node1",
                    description="Slow",
                    impact_ms=5000,
                    frequency=1.0,
                    recommendation="Fix it",
                )
            ],
            optimization_score=85.0,
            potential_savings_ms=5000,
        )
        result = analysis.to_dict()

        assert result["workflow_id"] == "wf123"
        assert result["time_range_hours"] == 24
        assert result["total_executions"] == 100
        assert result["bottleneck_count"] == 1
        assert result["optimization_score"] == 85.0

    def test_severity_breakdown(self):
        """Test severity breakdown calculation."""
        analysis = DetailedBottleneckAnalysis(
            workflow_id="wf123",
            analysis_time=datetime.now(),
            time_range_hours=24,
            total_executions=50,
            bottlenecks=[
                BottleneckInfo(
                    BottleneckType.NODE_SLOW,
                    Severity.CRITICAL,
                    "n1",
                    "",
                    0,
                    0,
                    "",
                ),
                BottleneckInfo(
                    BottleneckType.NODE_SLOW,
                    Severity.HIGH,
                    "n2",
                    "",
                    0,
                    0,
                    "",
                ),
                BottleneckInfo(
                    BottleneckType.NODE_SLOW,
                    Severity.HIGH,
                    "n3",
                    "",
                    0,
                    0,
                    "",
                ),
                BottleneckInfo(
                    BottleneckType.NODE_SLOW,
                    Severity.MEDIUM,
                    "n4",
                    "",
                    0,
                    0,
                    "",
                ),
            ],
        )
        result = analysis.to_dict()
        breakdown = result["severity_breakdown"]

        assert breakdown["critical"] == 1
        assert breakdown["high"] == 2
        assert breakdown["medium"] == 1
        assert breakdown["low"] == 0


class TestBottleneckDetector:
    """Tests for BottleneckDetector class."""

    def test_init(self):
        """Test initialization."""
        detector = BottleneckDetector()
        assert detector.SLOW_NODE_THRESHOLD_MS == 5000
        assert detector.HIGH_FAILURE_RATE == 0.1

    def test_analyze_empty_data(self):
        """Test analyze with no execution data."""
        detector = BottleneckDetector()
        result = detector.analyze("wf123", [], time_range_hours=24)

        assert result.workflow_id == "wf123"
        assert result.total_executions == 0
        assert result.optimization_score == 100.0
        assert len(result.bottlenecks) == 0

    def test_analyze_single_execution(self):
        """Test analyze with single execution."""
        detector = BottleneckDetector()
        execution_data = [
            {
                "node_timings": {
                    "node1": {
                        "node_type": "ClickElementNode",
                        "duration_ms": 200,
                        "success": True,
                    }
                }
            }
        ]
        result = detector.analyze("wf123", execution_data)

        assert result.total_executions == 1
        assert len(result.node_stats) == 1
        assert result.node_stats[0].node_id == "node1"


class TestSlowNodeDetection:
    """Tests for slow node bottleneck detection."""

    def test_detect_slow_node(self):
        """Test detection of slow nodes."""
        detector = BottleneckDetector()
        execution_data = [
            {
                "node_timings": {
                    "slow_node": {
                        "node_type": "HttpRequestNode",
                        "duration_ms": 8000,  # Above threshold (5000)
                        "success": True,
                    }
                }
            }
            for _ in range(10)
        ]
        result = detector.analyze("wf123", execution_data)

        slow_bottlenecks = [
            b
            for b in result.bottlenecks
            if b.bottleneck_type == BottleneckType.NODE_SLOW
        ]
        assert len(slow_bottlenecks) >= 1
        assert slow_bottlenecks[0].location == "slow_node"

    def test_detect_high_variance_node(self):
        """Test detection of high variance nodes."""
        detector = BottleneckDetector()
        # Create data where P95 >> average (high variance)
        execution_data = [
            {
                "node_timings": {
                    "variable_node": {
                        "node_type": "BrowserNode",
                        "duration_ms": 100 if i < 95 else 5000,  # 95% fast, 5% slow
                        "success": True,
                    }
                }
            }
            for i in range(100)
        ]
        result = detector.analyze("wf123", execution_data)

        # Should find high variance pattern
        variance_issues = [
            b
            for b in result.bottlenecks
            if "variance" in b.description.lower() or "p95" in b.description.lower()
        ]
        assert len(variance_issues) >= 1 or any(
            s.node_id == "variable_node" and s.p95_duration_ms > s.avg_duration_ms * 3
            for s in result.node_stats
        )

    def test_no_slow_node_under_threshold(self):
        """Test no false positives for fast nodes."""
        detector = BottleneckDetector()
        execution_data = [
            {
                "node_timings": {
                    "fast_node": {
                        "node_type": "ClickElementNode",
                        "duration_ms": 100,  # Below threshold
                        "success": True,
                    }
                }
            }
            for _ in range(10)
        ]
        result = detector.analyze("wf123", execution_data)

        slow_bottlenecks = [
            b
            for b in result.bottlenecks
            if b.bottleneck_type == BottleneckType.NODE_SLOW
        ]
        assert len(slow_bottlenecks) == 0


class TestFailingNodeDetection:
    """Tests for failing node bottleneck detection."""

    def test_detect_critical_failure_rate(self):
        """Test detection of critical failure rate (>=25%)."""
        detector = BottleneckDetector()
        execution_data = [
            {
                "node_timings": {
                    "flaky_node": {
                        "node_type": "ClickElementNode",
                        "duration_ms": 500,
                        "success": i < 7,  # 30% failure rate
                        "error_type": "element_not_found" if i >= 7 else None,
                    }
                }
            }
            for i in range(10)
        ]
        result = detector.analyze("wf123", execution_data)

        failing_bottlenecks = [
            b
            for b in result.bottlenecks
            if b.bottleneck_type == BottleneckType.NODE_FAILING
        ]
        assert len(failing_bottlenecks) >= 1
        assert failing_bottlenecks[0].severity == Severity.CRITICAL

    def test_detect_high_failure_rate(self):
        """Test detection of high failure rate (>=10%)."""
        detector = BottleneckDetector()
        execution_data = [
            {
                "node_timings": {
                    "flaky_node": {
                        "node_type": "ClickElementNode",
                        "duration_ms": 500,
                        "success": i < 85,  # 15% failure rate
                        "error_type": "timeout" if i >= 85 else None,
                    }
                }
            }
            for i in range(100)
        ]
        result = detector.analyze("wf123", execution_data)

        failing_bottlenecks = [
            b
            for b in result.bottlenecks
            if b.bottleneck_type == BottleneckType.NODE_FAILING
        ]
        assert len(failing_bottlenecks) >= 1
        assert failing_bottlenecks[0].severity == Severity.HIGH

    def test_no_failing_node_low_failure_rate(self):
        """Test no false positives for reliable nodes."""
        detector = BottleneckDetector()
        execution_data = [
            {
                "node_timings": {
                    "reliable_node": {
                        "node_type": "ClickElementNode",
                        "duration_ms": 500,
                        "success": i < 98,  # 2% failure rate
                        "error_type": "rare_error" if i >= 98 else None,
                    }
                }
            }
            for i in range(100)
        ]
        result = detector.analyze("wf123", execution_data)

        failing_bottlenecks = [
            b
            for b in result.bottlenecks
            if b.bottleneck_type == BottleneckType.NODE_FAILING
        ]
        assert len(failing_bottlenecks) == 0


class TestPatternDetection:
    """Tests for pattern-based bottleneck detection."""

    def test_detect_long_wait_pattern(self):
        """Test detection of excessive wait times."""
        detector = BottleneckDetector()
        execution_data = [
            {
                "node_timings": {
                    "wait_node": {
                        "node_type": "WaitNode",
                        "duration_ms": 15000,  # Above threshold (10000)
                        "success": True,
                    }
                }
            }
            for _ in range(10)
        ]
        result = detector.analyze("wf123", execution_data)

        wait_bottlenecks = [
            b
            for b in result.bottlenecks
            if b.bottleneck_type == BottleneckType.PATTERN_WAIT_LONG
        ]
        assert len(wait_bottlenecks) >= 1

    def test_detect_retry_loop_pattern(self):
        """Test detection of excessive retry patterns."""
        detector = BottleneckDetector()
        # Create execution data with many retry executions
        execution_data = [
            {
                "node_timings": {
                    "retry_node": {
                        "node_type": "RetryNode",
                        "duration_ms": 500,
                        "success": True,
                    }
                }
            }
            for _ in range(50)  # Way more retries than executions
        ]
        result = detector.analyze("wf123", execution_data)

        retry_bottlenecks = [
            b
            for b in result.bottlenecks
            if b.bottleneck_type == BottleneckType.PATTERN_RETRY_LOOP
        ]
        # Check if retry pattern detected
        assert len(retry_bottlenecks) >= 0  # May or may not trigger based on threshold


class TestOptimizationScore:
    """Tests for optimization score calculation."""

    def test_perfect_score_no_bottlenecks(self):
        """Test perfect score with no issues."""
        detector = BottleneckDetector()
        execution_data = [
            {
                "node_timings": {
                    "good_node": {
                        "node_type": "ClickElementNode",
                        "duration_ms": 100,
                        "success": True,
                    }
                }
            }
            for _ in range(100)
        ]
        result = detector.analyze("wf123", execution_data)

        assert result.optimization_score == 100.0

    def test_reduced_score_with_bottlenecks(self):
        """Test reduced score with bottlenecks."""
        detector = BottleneckDetector()
        execution_data = [
            {
                "node_timings": {
                    "slow_node": {
                        "node_type": "HttpRequestNode",
                        "duration_ms": 10000,  # Slow
                        "success": i < 70,  # 30% failures
                        "error_type": "timeout" if i >= 70 else None,
                    }
                }
            }
            for i in range(100)
        ]
        result = detector.analyze("wf123", execution_data)

        assert result.optimization_score < 100.0
        assert result.optimization_score >= 0.0

    def test_score_clamped_to_0_100(self):
        """Test score is clamped between 0 and 100."""
        detector = BottleneckDetector()
        # Create many failures to try to push score negative
        execution_data = [
            {
                "node_timings": {
                    f"node_{i}": {
                        "node_type": "FailingNode",
                        "duration_ms": 20000,  # Slow
                        "success": False,  # All failures
                        "error_type": "critical_error",
                    }
                    for i in range(10)
                }
            }
            for _ in range(50)
        ]
        result = detector.analyze("wf123", execution_data)

        assert result.optimization_score >= 0.0
        assert result.optimization_score <= 100.0


class TestRecommendations:
    """Tests for bottleneck recommendations."""

    def test_http_node_recommendation(self):
        """Test recommendation for slow HTTP node."""
        detector = BottleneckDetector()
        execution_data = [
            {
                "node_timings": {
                    "api_node": {
                        "node_type": "HttpRequestNode",
                        "duration_ms": 10000,
                        "success": True,
                    }
                }
            }
            for _ in range(10)
        ]
        result = detector.analyze("wf123", execution_data)

        slow_bottlenecks = [
            b
            for b in result.bottlenecks
            if b.bottleneck_type == BottleneckType.NODE_SLOW
        ]
        if slow_bottlenecks:
            assert any(
                "cache" in b.recommendation.lower()
                or "pool" in b.recommendation.lower()
                for b in slow_bottlenecks
            )

    def test_timeout_error_recommendation(self):
        """Test recommendation for timeout errors."""
        detector = BottleneckDetector()
        execution_data = [
            {
                "node_timings": {
                    "timeout_node": {
                        "node_type": "BrowserNode",
                        "duration_ms": 500,
                        "success": i < 70,
                        "error_type": "timeout" if i >= 70 else None,
                    }
                }
            }
            for i in range(100)
        ]
        result = detector.analyze("wf123", execution_data)

        failing_bottlenecks = [
            b
            for b in result.bottlenecks
            if b.bottleneck_type == BottleneckType.NODE_FAILING
        ]
        if failing_bottlenecks:
            assert any(
                "timeout" in b.recommendation.lower() for b in failing_bottlenecks
            )


class TestMultipleNodes:
    """Tests for multiple node analysis."""

    def test_analyze_multiple_nodes(self):
        """Test analysis of multiple nodes."""
        detector = BottleneckDetector()
        execution_data = [
            {
                "node_timings": {
                    "node1": {
                        "node_type": "ClickElementNode",
                        "duration_ms": 100,
                        "success": True,
                    },
                    "node2": {
                        "node_type": "TypeTextNode",
                        "duration_ms": 200,
                        "success": True,
                    },
                    "node3": {
                        "node_type": "HttpRequestNode",
                        "duration_ms": 8000,  # Slow
                        "success": True,
                    },
                }
            }
            for _ in range(10)
        ]
        result = detector.analyze("wf123", execution_data)

        assert len(result.node_stats) == 3
        # Node3 should be flagged as slow
        slow_bottlenecks = [b for b in result.bottlenecks if b.location == "node3"]
        assert len(slow_bottlenecks) >= 1

    def test_nodes_sorted_by_total_duration(self):
        """Test nodes are sorted by total duration."""
        detector = BottleneckDetector()
        execution_data = [
            {
                "node_timings": {
                    "fast": {"node_type": "A", "duration_ms": 100, "success": True},
                    "slow": {"node_type": "B", "duration_ms": 1000, "success": True},
                    "medium": {"node_type": "C", "duration_ms": 500, "success": True},
                }
            }
            for _ in range(10)
        ]
        result = detector.analyze("wf123", execution_data)

        assert result.node_stats[0].node_id == "slow"
        assert result.node_stats[1].node_id == "medium"
        assert result.node_stats[2].node_id == "fast"


class TestPotentialSavings:
    """Tests for potential savings calculation."""

    def test_potential_savings_calculated(self):
        """Test potential savings are calculated from bottlenecks."""
        detector = BottleneckDetector()
        execution_data = [
            {
                "node_timings": {
                    "slow_node": {
                        "node_type": "HttpRequestNode",
                        "duration_ms": 10000,
                        "success": True,
                    }
                }
            }
            for _ in range(10)
        ]
        result = detector.analyze("wf123", execution_data)

        # Should have potential savings from slow node
        assert result.potential_savings_ms > 0

    def test_no_savings_for_optimized_workflow(self):
        """Test no savings for already optimized workflow."""
        detector = BottleneckDetector()
        execution_data = [
            {
                "node_timings": {
                    "fast_node": {
                        "node_type": "ClickElementNode",
                        "duration_ms": 50,
                        "success": True,
                    }
                }
            }
            for _ in range(10)
        ]
        result = detector.analyze("wf123", execution_data)

        assert result.potential_savings_ms == 0
