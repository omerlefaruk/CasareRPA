"""
Tests for Robot Agent Metrics Collection.

Tests metrics collection functionality:
- Counter increment (total jobs, successful/failed)
- Gauge set (current resource usage)
- Histogram record (node execution times)
- Job and node metrics tracking
- Resource monitoring
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from casare_rpa.robot.metrics import (
    MetricsCollector,
    JobMetrics,
    NodeMetrics,
    ResourceSnapshot,
    get_metrics_collector,
)


# --- Fixtures ---


@pytest.fixture
def metrics_collector() -> MetricsCollector:
    """Provide fresh metrics collector for testing."""
    collector = MetricsCollector(
        history_limit=100,
        resource_sample_interval=1.0,
    )
    return collector


@pytest.fixture
def collector_with_job(metrics_collector: MetricsCollector) -> MetricsCollector:
    """Provide metrics collector with an active job."""
    metrics_collector.start_job("job-001", "Test Workflow", total_nodes=5)
    return metrics_collector


# --- JobMetrics Tests ---


class TestJobMetrics:
    """Tests for JobMetrics dataclass."""

    def test_create_job_metrics(self):
        """Creating JobMetrics with required fields."""
        metrics = JobMetrics(
            job_id="job-001",
            workflow_name="Test Workflow",
            started_at=datetime.now(timezone.utc),
        )

        assert metrics.job_id == "job-001"
        assert metrics.workflow_name == "Test Workflow"
        assert metrics.success is False
        assert metrics.duration_ms == 0
        assert metrics.total_nodes == 0
        assert metrics.completed_nodes == 0

    def test_to_dict_serialization(self):
        """JobMetrics.to_dict() produces valid dictionary."""
        started = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        completed = datetime(2024, 1, 1, 12, 1, 0, tzinfo=timezone.utc)

        metrics = JobMetrics(
            job_id="job-001",
            workflow_name="Test Workflow",
            started_at=started,
            completed_at=completed,
            duration_ms=60000,
            success=True,
            total_nodes=10,
            completed_nodes=10,
            failed_nodes=0,
            skipped_nodes=0,
            retry_count=2,
            error_message=None,
        )

        result = metrics.to_dict()

        assert result["job_id"] == "job-001"
        assert result["workflow_name"] == "Test Workflow"
        assert result["started_at"] == "2024-01-01T12:00:00+00:00"
        assert result["completed_at"] == "2024-01-01T12:01:00+00:00"
        assert result["duration_ms"] == 60000
        assert result["success"] is True
        assert result["total_nodes"] == 10
        assert result["retry_count"] == 2


class TestNodeMetrics:
    """Tests for NodeMetrics dataclass."""

    def test_create_node_metrics(self):
        """Creating NodeMetrics with required fields."""
        metrics = NodeMetrics(
            node_id="node-001",
            node_type="ClickElementNode",
            duration_ms=150.5,
            success=True,
        )

        assert metrics.node_id == "node-001"
        assert metrics.node_type == "ClickElementNode"
        assert metrics.duration_ms == 150.5
        assert metrics.success is True
        assert metrics.error_type is None
        assert metrics.retry_count == 0

    def test_failed_node_metrics(self):
        """NodeMetrics with error information."""
        metrics = NodeMetrics(
            node_id="node-002",
            node_type="TypeTextNode",
            duration_ms=5000,
            success=False,
            error_type="TimeoutError",
            retry_count=3,
        )

        assert metrics.success is False
        assert metrics.error_type == "TimeoutError"
        assert metrics.retry_count == 3


class TestResourceSnapshot:
    """Tests for ResourceSnapshot dataclass."""

    def test_create_resource_snapshot(self):
        """Creating ResourceSnapshot with all fields."""
        snapshot = ResourceSnapshot(
            timestamp=datetime.now(timezone.utc),
            cpu_percent=45.5,
            memory_percent=62.3,
            memory_mb=512.0,
            disk_percent=75.0,
            network_bytes_sent=1024,
            network_bytes_recv=2048,
        )

        assert snapshot.cpu_percent == 45.5
        assert snapshot.memory_percent == 62.3
        assert snapshot.memory_mb == 512.0
        assert snapshot.disk_percent == 75.0


# --- MetricsCollector Job Tracking Tests ---


class TestMetricsCollectorJobTracking:
    """Tests for job-level metrics tracking."""

    def test_start_job_creates_metrics(self, metrics_collector: MetricsCollector):
        """start_job() creates JobMetrics instance."""
        result = metrics_collector.start_job("job-001", "Test Workflow", total_nodes=5)

        assert result is not None
        assert isinstance(result, JobMetrics)
        assert result.job_id == "job-001"
        assert result.workflow_name == "Test Workflow"
        assert result.total_nodes == 5
        assert metrics_collector._current_job is not None

    def test_end_job_success(self, collector_with_job: MetricsCollector):
        """end_job() marks job as successful."""
        collector_with_job.end_job(success=True)

        assert collector_with_job._current_job is None
        assert collector_with_job._total_jobs == 1
        assert collector_with_job._successful_jobs == 1
        assert collector_with_job._failed_jobs == 0

    def test_end_job_failure(self, collector_with_job: MetricsCollector):
        """end_job() marks job as failed with error message."""
        collector_with_job.end_job(success=False, error_message="Connection timeout")

        assert collector_with_job._failed_jobs == 1
        assert collector_with_job._successful_jobs == 0
        assert "Connection timeout" in collector_with_job._error_counts

    def test_end_job_calculates_duration(self, collector_with_job: MetricsCollector):
        """end_job() calculates job duration."""
        # Small delay to ensure duration > 0
        import time

        time.sleep(0.01)

        collector_with_job.end_job(success=True)

        assert collector_with_job._total_duration_ms > 0

    def test_end_job_stores_in_history(self, collector_with_job: MetricsCollector):
        """end_job() stores job in history."""
        collector_with_job.end_job(success=True)

        assert len(collector_with_job._job_metrics) == 1
        assert collector_with_job._job_metrics[0].job_id == "job-001"

    def test_history_limit_enforced(self, metrics_collector: MetricsCollector):
        """History limit is enforced when exceeded."""
        metrics_collector.history_limit = 5

        for i in range(10):
            metrics_collector.start_job(f"job-{i:03d}", "Workflow", total_nodes=1)
            metrics_collector.end_job(success=True)

        assert len(metrics_collector._job_metrics) == 5
        # Oldest jobs should be removed
        assert metrics_collector._job_metrics[0].job_id == "job-005"

    def test_end_job_without_active_job(self, metrics_collector: MetricsCollector):
        """end_job() handles no active job gracefully."""
        # Should not raise
        metrics_collector.end_job(success=True)

        assert metrics_collector._total_jobs == 0


# --- MetricsCollector Node Tracking Tests ---


class TestMetricsCollectorNodeTracking:
    """Tests for node-level metrics tracking."""

    def test_record_node_success(self, collector_with_job: MetricsCollector):
        """record_node() tracks successful node execution."""
        collector_with_job.record_node(
            node_id="node-001",
            node_type="ClickElementNode",
            duration_ms=150.0,
            success=True,
        )

        assert collector_with_job._current_job.completed_nodes == 1
        assert len(collector_with_job._current_job.node_metrics) == 1

    def test_record_node_failure(self, collector_with_job: MetricsCollector):
        """record_node() tracks failed node execution."""
        collector_with_job.record_node(
            node_id="node-002",
            node_type="TypeTextNode",
            duration_ms=5000.0,
            success=False,
            error_type="TimeoutError",
        )

        assert collector_with_job._current_job.failed_nodes == 1
        assert "TypeTextNode:TimeoutError" in collector_with_job._error_counts

    def test_record_node_with_retries(self, collector_with_job: MetricsCollector):
        """record_node() tracks retry counts."""
        collector_with_job.record_node(
            node_id="node-001",
            node_type="NavigateNode",
            duration_ms=3000.0,
            success=True,
            retry_count=2,
        )

        assert collector_with_job._current_job.retry_count == 2

    def test_record_node_updates_node_stats(self, metrics_collector: MetricsCollector):
        """record_node() updates aggregated node type statistics."""
        metrics_collector.start_job("job-001", "Workflow", total_nodes=3)

        metrics_collector.record_node("n1", "ClickNode", 100.0, True)
        metrics_collector.record_node("n2", "ClickNode", 200.0, True)
        metrics_collector.record_node("n3", "ClickNode", 300.0, False, "Error")

        stats = metrics_collector._node_stats["ClickNode"]
        assert stats["total_executions"] == 3
        assert stats["successful"] == 2
        assert stats["failed"] == 1
        assert stats["total_duration_ms"] == 600.0

    def test_record_node_skipped(self, collector_with_job: MetricsCollector):
        """record_node_skipped() increments skipped count."""
        collector_with_job.record_node_skipped("node-001", "ClickNode")

        assert collector_with_job._current_job.skipped_nodes == 1


# --- MetricsCollector Summary Tests ---


class TestMetricsCollectorSummary:
    """Tests for metrics summary and reporting."""

    def test_get_summary_empty(self, metrics_collector: MetricsCollector):
        """get_summary() handles no data gracefully."""
        summary = metrics_collector.get_summary()

        assert summary["total_jobs"] == 0
        assert summary["success_rate_percent"] == 0
        assert summary["average_duration_ms"] == 0

    def test_get_summary_with_data(self, metrics_collector: MetricsCollector):
        """get_summary() returns correct aggregations."""
        # Complete 3 jobs (2 success, 1 fail)
        for i, success in enumerate([True, True, False]):
            metrics_collector.start_job(f"job-{i}", "Workflow", total_nodes=1)
            metrics_collector.end_job(success=success)

        summary = metrics_collector.get_summary()

        assert summary["total_jobs"] == 3
        assert summary["successful_jobs"] == 2
        assert summary["failed_jobs"] == 1
        assert summary["success_rate_percent"] == pytest.approx(66.67, rel=0.1)

    def test_get_summary_shows_current_job(
        self,
        collector_with_job: MetricsCollector,
    ):
        """get_summary() shows current job ID."""
        summary = collector_with_job.get_summary()

        assert summary["current_job"] == "job-001"

    def test_get_node_stats(self, metrics_collector: MetricsCollector):
        """get_node_stats() returns per-node-type statistics."""
        metrics_collector.start_job("job", "Workflow", total_nodes=4)

        metrics_collector.record_node("n1", "ClickNode", 100.0, True)
        metrics_collector.record_node("n2", "ClickNode", 100.0, True)
        metrics_collector.record_node("n3", "TypeNode", 200.0, True)
        metrics_collector.record_node("n4", "TypeNode", 200.0, False)

        stats = metrics_collector.get_node_stats()

        assert "ClickNode" in stats
        assert stats["ClickNode"]["total_executions"] == 2
        assert stats["ClickNode"]["success_rate_percent"] == 100.0
        assert stats["ClickNode"]["average_duration_ms"] == 100.0

        assert "TypeNode" in stats
        assert stats["TypeNode"]["total_executions"] == 2
        assert stats["TypeNode"]["success_rate_percent"] == 50.0

    def test_get_error_summary(self, metrics_collector: MetricsCollector):
        """get_error_summary() returns top errors."""
        metrics_collector.start_job("job", "Workflow", total_nodes=5)

        # Record various errors
        for i in range(5):
            metrics_collector.record_node(
                f"n{i}",
                "Node",
                100.0,
                False,
                "TimeoutError",
            )
        for i in range(3):
            metrics_collector.record_node(
                f"n{i+5}",
                "Node",
                100.0,
                False,
                "NetworkError",
            )

        errors = metrics_collector.get_error_summary(limit=2)

        assert len(errors) == 2
        assert errors[0]["count"] == 5  # Most common first
        assert "TimeoutError" in errors[0]["error"]

    def test_get_recent_jobs(self, metrics_collector: MetricsCollector):
        """get_recent_jobs() returns recent job metrics."""
        for i in range(5):
            metrics_collector.start_job(f"job-{i:03d}", f"Workflow-{i}", 1)
            metrics_collector.end_job(success=True)

        recent = metrics_collector.get_recent_jobs(limit=3)

        assert len(recent) == 3
        # Most recent first
        assert recent[0]["job_id"] == "job-004"
        assert recent[1]["job_id"] == "job-003"
        assert recent[2]["job_id"] == "job-002"


# --- MetricsCollector Resource Monitoring Tests ---


class TestMetricsCollectorResourceMonitoring:
    """Tests for resource monitoring functionality."""

    @pytest.mark.asyncio
    async def test_start_resource_monitoring(
        self,
        metrics_collector: MetricsCollector,
    ):
        """start_resource_monitoring() starts background task."""
        with patch("casare_rpa.robot.metrics.PSUTIL_AVAILABLE", True):
            with patch.object(
                metrics_collector,
                "_sample_resources",
                return_value=ResourceSnapshot(
                    timestamp=datetime.now(timezone.utc),
                    cpu_percent=10.0,
                    memory_percent=50.0,
                    memory_mb=512.0,
                ),
            ):
                await metrics_collector.start_resource_monitoring()

                try:
                    assert metrics_collector._monitoring is True
                    assert metrics_collector._resource_task is not None

                    # Let it sample once
                    await asyncio.sleep(0.1)
                finally:
                    await metrics_collector.stop_resource_monitoring()

    @pytest.mark.asyncio
    async def test_stop_resource_monitoring(
        self,
        metrics_collector: MetricsCollector,
    ):
        """stop_resource_monitoring() stops background task."""
        with patch("casare_rpa.robot.metrics.PSUTIL_AVAILABLE", True):
            metrics_collector._monitoring = True
            metrics_collector._resource_task = asyncio.create_task(asyncio.sleep(10))

            await metrics_collector.stop_resource_monitoring()

            assert metrics_collector._monitoring is False
            assert metrics_collector._resource_task is None

    @pytest.mark.asyncio
    async def test_resource_monitoring_without_psutil(
        self,
        metrics_collector: MetricsCollector,
    ):
        """Resource monitoring handles missing psutil."""
        with patch("casare_rpa.robot.metrics.PSUTIL_AVAILABLE", False):
            await metrics_collector.start_resource_monitoring()

            # Should not start monitoring
            assert metrics_collector._monitoring is False

    def test_get_current_resources_without_psutil(
        self,
        metrics_collector: MetricsCollector,
    ):
        """get_current_resources() returns None without psutil."""
        with patch("casare_rpa.robot.metrics.PSUTIL_AVAILABLE", False):
            result = metrics_collector.get_current_resources()

            assert result is None

    def test_get_resource_history(self, metrics_collector: MetricsCollector):
        """get_resource_history() returns recent samples."""
        now = datetime.now(timezone.utc)

        # Add some history
        for i in range(5):
            metrics_collector._resource_history.append(
                ResourceSnapshot(
                    timestamp=now - timedelta(minutes=i),
                    cpu_percent=float(10 * i),
                    memory_percent=50.0,
                    memory_mb=512.0,
                )
            )

        history = metrics_collector.get_resource_history(minutes=3)

        # Should include samples within last 3 minutes
        assert len(history) >= 3


# --- MetricsCollector Full Report Tests ---


class TestMetricsCollectorFullReport:
    """Tests for comprehensive report generation."""

    def test_get_full_report(self, metrics_collector: MetricsCollector):
        """get_full_report() returns all metrics."""
        metrics_collector.start_job("job-001", "Workflow", 2)
        metrics_collector.record_node("n1", "ClickNode", 100.0, True)
        metrics_collector.end_job(success=True)

        report = metrics_collector.get_full_report()

        assert "summary" in report
        assert "node_stats" in report
        assert "top_errors" in report
        assert "recent_jobs" in report
        assert "current_resources" in report
        assert "resource_history" in report
        assert "generated_at" in report

    def test_full_report_summary_accurate(self, metrics_collector: MetricsCollector):
        """Full report summary reflects actual data."""
        metrics_collector.start_job("job-001", "Workflow", 2)
        metrics_collector.end_job(success=True)

        report = metrics_collector.get_full_report()

        assert report["summary"]["total_jobs"] == 1
        assert report["summary"]["successful_jobs"] == 1


# --- MetricsCollector Reset Tests ---


class TestMetricsCollectorReset:
    """Tests for metrics reset functionality."""

    def test_reset_clears_all_metrics(self, metrics_collector: MetricsCollector):
        """reset() clears all tracked metrics."""
        # Add some data
        metrics_collector.start_job("job-001", "Workflow", 1)
        metrics_collector.record_node("n1", "Node", 100.0, True)
        metrics_collector.end_job(success=True)
        metrics_collector._resource_history.append(
            ResourceSnapshot(
                timestamp=datetime.now(timezone.utc),
                cpu_percent=10.0,
                memory_percent=50.0,
                memory_mb=512.0,
            )
        )

        metrics_collector.reset()

        assert len(metrics_collector._job_metrics) == 0
        assert metrics_collector._current_job is None
        assert metrics_collector._total_jobs == 0
        assert metrics_collector._successful_jobs == 0
        assert metrics_collector._failed_jobs == 0
        assert len(metrics_collector._node_stats) == 0
        assert len(metrics_collector._resource_history) == 0
        assert len(metrics_collector._error_counts) == 0


# --- Global Metrics Instance Tests ---


class TestGlobalMetricsInstance:
    """Tests for global metrics collector singleton."""

    def test_get_metrics_collector_returns_instance(self):
        """get_metrics_collector() returns MetricsCollector."""
        collector = get_metrics_collector()

        assert collector is not None
        assert isinstance(collector, MetricsCollector)

    def test_get_metrics_collector_singleton(self):
        """get_metrics_collector() returns same instance."""
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()

        assert collector1 is collector2


# --- Counter Increment Tests ---


class TestCounterIncrement:
    """Tests for counter-like metrics (job counts, node executions)."""

    def test_increment_total_jobs(self, metrics_collector: MetricsCollector):
        """Total jobs counter increments correctly."""
        for i in range(5):
            metrics_collector.start_job(f"job-{i}", "Workflow", 1)
            metrics_collector.end_job(success=True)

        assert metrics_collector._total_jobs == 5

    def test_increment_successful_jobs(self, metrics_collector: MetricsCollector):
        """Successful jobs counter increments correctly."""
        for i in range(3):
            metrics_collector.start_job(f"job-{i}", "Workflow", 1)
            metrics_collector.end_job(success=True)

        for i in range(2):
            metrics_collector.start_job(f"fail-{i}", "Workflow", 1)
            metrics_collector.end_job(success=False)

        assert metrics_collector._successful_jobs == 3
        assert metrics_collector._failed_jobs == 2

    def test_increment_node_executions(self, metrics_collector: MetricsCollector):
        """Node execution counter increments correctly."""
        metrics_collector.start_job("job", "Workflow", 10)

        for i in range(10):
            metrics_collector.record_node(f"n{i}", "TestNode", 100.0, True)

        stats = metrics_collector._node_stats["TestNode"]
        assert stats["total_executions"] == 10

    def test_increment_error_counts(self, metrics_collector: MetricsCollector):
        """Error counts increment for each occurrence."""
        metrics_collector.start_job("job", "Workflow", 5)

        for i in range(3):
            metrics_collector.record_node(
                f"n{i}",
                "Node",
                100.0,
                False,
                "SameError",
            )

        assert metrics_collector._error_counts["Node:SameError"] == 3


# --- Gauge Set Tests (Current Values) ---


class TestGaugeSet:
    """Tests for gauge-like metrics (current values)."""

    def test_current_job_tracking(self, metrics_collector: MetricsCollector):
        """Current job is tracked as gauge."""
        assert metrics_collector._current_job is None

        metrics_collector.start_job("job-001", "Workflow", 1)
        assert metrics_collector._current_job is not None
        assert metrics_collector._current_job.job_id == "job-001"

        metrics_collector.end_job(success=True)
        assert metrics_collector._current_job is None

    def test_completed_nodes_count(self, collector_with_job: MetricsCollector):
        """Completed nodes count updates in real-time."""
        assert collector_with_job._current_job.completed_nodes == 0

        collector_with_job.record_node("n1", "Node", 100.0, True)
        assert collector_with_job._current_job.completed_nodes == 1

        collector_with_job.record_node("n2", "Node", 100.0, True)
        assert collector_with_job._current_job.completed_nodes == 2


# --- Histogram Record Tests (Duration Tracking) ---


class TestHistogramRecord:
    """Tests for histogram-like metrics (duration distributions)."""

    def test_total_duration_accumulates(self, metrics_collector: MetricsCollector):
        """Total duration accumulates across jobs."""
        for i in range(3):
            metrics_collector.start_job(f"job-{i}", "Workflow", 1)
            metrics_collector.end_job(success=True)

        assert metrics_collector._total_duration_ms > 0

    def test_node_duration_accumulates(self, metrics_collector: MetricsCollector):
        """Node type duration accumulates."""
        metrics_collector.start_job("job", "Workflow", 3)

        metrics_collector.record_node("n1", "SlowNode", 1000.0, True)
        metrics_collector.record_node("n2", "SlowNode", 2000.0, True)
        metrics_collector.record_node("n3", "SlowNode", 3000.0, True)

        stats = metrics_collector._node_stats["SlowNode"]
        assert stats["total_duration_ms"] == 6000.0

    def test_average_duration_calculated(self, metrics_collector: MetricsCollector):
        """Average duration is calculated correctly."""
        metrics_collector.start_job("job", "Workflow", 4)

        metrics_collector.record_node("n1", "Node", 100.0, True)
        metrics_collector.record_node("n2", "Node", 200.0, True)
        metrics_collector.record_node("n3", "Node", 300.0, True)
        metrics_collector.record_node("n4", "Node", 400.0, True)

        stats = metrics_collector.get_node_stats()
        assert stats["Node"]["average_duration_ms"] == 250.0


# --- Edge Cases ---


class TestMetricsCollectorEdgeCases:
    """Edge case tests for metrics collector."""

    def test_record_node_without_current_job(
        self,
        metrics_collector: MetricsCollector,
    ):
        """record_node() works even without active job."""
        # Should not raise
        metrics_collector.record_node("n1", "Node", 100.0, True)

        # Stats should still be updated
        assert metrics_collector._node_stats["Node"]["total_executions"] == 1

    def test_error_message_truncation(self, metrics_collector: MetricsCollector):
        """Long error messages are truncated in counts."""
        long_error = "A" * 200

        metrics_collector.start_job("job", "Workflow", 1)
        metrics_collector.end_job(success=False, error_message=long_error)

        # Error key should be truncated
        error_keys = list(metrics_collector._error_counts.keys())
        assert len(error_keys) == 1
        assert len(error_keys[0]) == 100

    def test_multiple_concurrent_jobs(self, metrics_collector: MetricsCollector):
        """Only one job can be active at a time."""
        metrics_collector.start_job("job-001", "Workflow 1", 1)
        metrics_collector.start_job("job-002", "Workflow 2", 1)

        # Second start should replace first
        assert metrics_collector._current_job.job_id == "job-002"

    def test_zero_duration_jobs(self, metrics_collector: MetricsCollector):
        """Handles zero duration jobs."""
        metrics_collector.start_job("fast-job", "Workflow", 1)
        # Immediately end
        metrics_collector._current_job.started_at = datetime.now(timezone.utc)
        metrics_collector.end_job(success=True)

        # Should not cause division errors
        summary = metrics_collector.get_summary()
        assert summary["average_duration_ms"] >= 0
