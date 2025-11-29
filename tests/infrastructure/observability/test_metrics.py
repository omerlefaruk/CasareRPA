"""
Tests for CasareRPA RPA-specific metrics collection.

Tests RPAMetricsCollector and its various metric recording functions.
"""

import time
import pytest
from unittest.mock import Mock, patch
from typing import Any

from casare_rpa.infrastructure.observability.metrics import (
    RPAMetricsCollector,
    JobMetrics,
    RobotMetrics,
    JobStatus,
    RobotStatus,
    get_metrics_collector,
)


class TestJobMetrics:
    """Tests for JobMetrics dataclass."""

    def test_default_values(self) -> None:
        """Test default JobMetrics values."""
        metrics = JobMetrics()

        assert metrics.total_jobs == 0
        assert metrics.completed_jobs == 0
        assert metrics.failed_jobs == 0
        assert metrics.cancelled_jobs == 0
        assert metrics.total_duration_seconds == 0.0
        assert metrics.total_queue_wait_seconds == 0.0
        assert metrics.total_nodes_executed == 0

    def test_success_rate_zero_jobs(self) -> None:
        """Test success rate with no jobs."""
        metrics = JobMetrics()

        assert metrics.success_rate == 0.0

    def test_success_rate_calculation(self) -> None:
        """Test success rate calculation."""
        metrics = JobMetrics(
            total_jobs=10,
            completed_jobs=7,
            failed_jobs=3,
        )

        assert metrics.success_rate == 70.0

    def test_average_duration_zero_jobs(self) -> None:
        """Test average duration with no completed jobs."""
        metrics = JobMetrics()

        assert metrics.average_duration_seconds == 0.0

    def test_average_duration_calculation(self) -> None:
        """Test average duration calculation."""
        metrics = JobMetrics(
            completed_jobs=5,
            failed_jobs=5,
            total_duration_seconds=100.0,
        )

        assert metrics.average_duration_seconds == 10.0

    def test_average_queue_wait_calculation(self) -> None:
        """Test average queue wait time calculation."""
        metrics = JobMetrics(
            total_jobs=4,
            total_queue_wait_seconds=20.0,
        )

        assert metrics.average_queue_wait_seconds == 5.0


class TestRobotMetrics:
    """Tests for RobotMetrics dataclass."""

    def test_default_values(self) -> None:
        """Test default RobotMetrics values."""
        metrics = RobotMetrics(robot_id="robot-01")

        assert metrics.robot_id == "robot-01"
        assert metrics.status == RobotStatus.IDLE
        assert metrics.jobs_completed == 0
        assert metrics.jobs_failed == 0
        assert metrics.total_busy_seconds == 0.0
        assert metrics.total_idle_seconds == 0.0
        assert metrics.last_job_at is None
        assert metrics.current_job_id is None

    def test_utilization_zero_time(self) -> None:
        """Test utilization with no tracked time."""
        metrics = RobotMetrics(robot_id="robot-01")

        assert metrics.utilization_percent == 0.0

    def test_utilization_calculation(self) -> None:
        """Test utilization percentage calculation."""
        metrics = RobotMetrics(
            robot_id="robot-01",
            total_busy_seconds=75.0,
            total_idle_seconds=25.0,
        )

        assert metrics.utilization_percent == 75.0

    def test_success_rate_no_jobs(self) -> None:
        """Test success rate with no jobs."""
        metrics = RobotMetrics(robot_id="robot-01")

        assert metrics.success_rate == 0.0

    def test_success_rate_calculation(self) -> None:
        """Test success rate calculation."""
        metrics = RobotMetrics(
            robot_id="robot-01",
            jobs_completed=8,
            jobs_failed=2,
        )

        assert metrics.success_rate == 80.0


class TestRPAMetricsCollector:
    """Tests for RPAMetricsCollector."""

    @pytest.fixture
    def collector(self) -> RPAMetricsCollector:
        """Get a fresh metrics collector instance."""
        collector = RPAMetricsCollector.get_instance()
        collector.reset_metrics()
        return collector

    def test_singleton_pattern(self) -> None:
        """Test that RPAMetricsCollector is a singleton."""
        collector1 = RPAMetricsCollector.get_instance()
        collector2 = get_metrics_collector()

        assert collector1 is collector2

    def test_record_job_enqueue(self, collector: RPAMetricsCollector) -> None:
        """Test recording job enqueue."""
        collector.record_job_enqueue(
            job_id="job-001",
            workflow_name="TestWorkflow",
            priority=10,
        )

        assert collector.get_queue_depth() == 1
        active_jobs = collector.get_active_jobs()
        assert "job-001" in active_jobs
        assert active_jobs["job-001"]["workflow_name"] == "TestWorkflow"
        assert active_jobs["job-001"]["priority"] == 10
        assert active_jobs["job-001"]["status"] == JobStatus.PENDING

    def test_record_job_start(self, collector: RPAMetricsCollector) -> None:
        """Test recording job start."""
        # Enqueue first
        collector.record_job_enqueue("job-001", "TestWorkflow")

        # Then start
        collector.record_job_start("job-001", robot_id="robot-01")

        active_jobs = collector.get_active_jobs()
        assert active_jobs["job-001"]["status"] == JobStatus.RUNNING
        assert active_jobs["job-001"]["robot_id"] == "robot-01"
        assert collector.get_queue_depth() == 0

    def test_record_job_complete_success(self, collector: RPAMetricsCollector) -> None:
        """Test recording successful job completion."""
        collector.record_job_enqueue("job-001", "TestWorkflow")
        collector.record_job_start("job-001", "robot-01")

        collector.record_job_complete(
            job_id="job-001",
            success=True,
            duration_seconds=30.0,
            nodes_executed=15,
        )

        metrics = collector.get_job_metrics()
        assert metrics.total_jobs == 1
        assert metrics.completed_jobs == 1
        assert metrics.failed_jobs == 0
        assert metrics.total_duration_seconds == 30.0
        assert metrics.total_nodes_executed == 15

        # Job should be removed from active jobs
        assert "job-001" not in collector.get_active_jobs()

    def test_record_job_complete_failure(self, collector: RPAMetricsCollector) -> None:
        """Test recording failed job completion."""
        collector.record_job_enqueue("job-001", "TestWorkflow")
        collector.record_job_start("job-001", "robot-01")

        collector.record_job_complete(
            job_id="job-001",
            success=False,
            duration_seconds=5.0,
            error_message="Element not found",
        )

        metrics = collector.get_job_metrics()
        assert metrics.total_jobs == 1
        assert metrics.completed_jobs == 0
        assert metrics.failed_jobs == 1

    def test_record_job_retry(self, collector: RPAMetricsCollector) -> None:
        """Test recording job retry."""
        collector.record_job_enqueue("job-001", "TestWorkflow")
        collector.record_job_start("job-001", "robot-01")

        collector.record_job_retry(
            job_id="job-001",
            attempt_number=2,
            reason="timeout",
        )

        active_jobs = collector.get_active_jobs()
        assert active_jobs["job-001"]["status"] == JobStatus.RETRYING
        assert active_jobs["job-001"]["retry_count"] == 2

    def test_record_job_cancel(self, collector: RPAMetricsCollector) -> None:
        """Test recording job cancellation."""
        collector.record_job_enqueue("job-001", "TestWorkflow")
        collector.record_job_start("job-001", "robot-01")

        collector.record_job_cancel("job-001", reason="user_requested")

        metrics = collector.get_job_metrics()
        assert metrics.cancelled_jobs == 1
        assert "job-001" not in collector.get_active_jobs()


class TestRobotMetricsTracking:
    """Tests for robot metrics tracking."""

    @pytest.fixture
    def collector(self) -> RPAMetricsCollector:
        """Get a fresh metrics collector instance."""
        collector = RPAMetricsCollector.get_instance()
        collector.reset_metrics()
        return collector

    def test_register_robot(self, collector: RPAMetricsCollector) -> None:
        """Test registering a robot."""
        collector.register_robot("robot-01")

        robot_metrics = collector.get_robot_metrics("robot-01")
        assert robot_metrics is not None
        assert robot_metrics.robot_id == "robot-01"
        assert robot_metrics.status == RobotStatus.IDLE

    def test_unregister_robot(self, collector: RPAMetricsCollector) -> None:
        """Test unregistering a robot."""
        collector.register_robot("robot-01")
        collector.unregister_robot("robot-01")

        assert collector.get_robot_metrics("robot-01") is None

    def test_robot_status_changes(self, collector: RPAMetricsCollector) -> None:
        """Test robot status changes during job execution."""
        collector.register_robot("robot-01")
        collector.record_job_enqueue("job-001", "TestWorkflow")
        collector.record_job_start("job-001", "robot-01")

        robot_metrics = collector.get_robot_metrics("robot-01")
        assert robot_metrics is not None
        assert robot_metrics.status == RobotStatus.BUSY
        assert robot_metrics.current_job_id == "job-001"

        collector.record_job_complete("job-001", success=True, duration_seconds=10.0)

        robot_metrics = collector.get_robot_metrics("robot-01")
        assert robot_metrics.status == RobotStatus.IDLE
        assert robot_metrics.current_job_id is None
        assert robot_metrics.jobs_completed == 1

    def test_get_all_robot_metrics(self, collector: RPAMetricsCollector) -> None:
        """Test getting metrics for all robots."""
        collector.register_robot("robot-01")
        collector.register_robot("robot-02")

        all_metrics = collector.get_all_robot_metrics()

        assert len(all_metrics) == 2
        assert "robot-01" in all_metrics
        assert "robot-02" in all_metrics


class TestNodeMetricsTracking:
    """Tests for node execution metrics."""

    @pytest.fixture
    def collector(self) -> RPAMetricsCollector:
        """Get a fresh metrics collector instance."""
        collector = RPAMetricsCollector.get_instance()
        collector.reset_metrics()
        return collector

    def test_track_node_execution_success(self, collector: RPAMetricsCollector) -> None:
        """Test tracking successful node execution."""
        with collector.track_node_execution("ClickNode", "node-001"):
            time.sleep(0.01)  # Simulate work

        node_metrics = collector.get_node_metrics("ClickNode")
        assert node_metrics is not None
        assert node_metrics["total_executions"] == 1
        assert node_metrics["successful"] == 1
        assert node_metrics["failed"] == 0
        assert node_metrics["total_duration_ms"] > 0

    def test_track_node_execution_failure(self, collector: RPAMetricsCollector) -> None:
        """Test tracking failed node execution."""
        with pytest.raises(ValueError):
            with collector.track_node_execution("TypeNode", "node-002"):
                raise ValueError("Element not found")

        node_metrics = collector.get_node_metrics("TypeNode")
        assert node_metrics is not None
        assert node_metrics["total_executions"] == 1
        assert node_metrics["successful"] == 0
        assert node_metrics["failed"] == 1

    def test_multiple_node_executions(self, collector: RPAMetricsCollector) -> None:
        """Test tracking multiple node executions."""
        for i in range(3):
            with collector.track_node_execution("ClickNode", f"node-{i}"):
                pass

        node_metrics = collector.get_node_metrics("ClickNode")
        assert node_metrics["total_executions"] == 3
        assert node_metrics["successful"] == 3

    def test_get_all_node_metrics(self, collector: RPAMetricsCollector) -> None:
        """Test getting metrics for all node types."""
        with collector.track_node_execution("ClickNode", "node-001"):
            pass
        with collector.track_node_execution("TypeNode", "node-002"):
            pass

        all_metrics = collector.get_all_node_metrics()

        assert "ClickNode" in all_metrics
        assert "TypeNode" in all_metrics


class TestSelfHealingMetrics:
    """Tests for self-healing metrics tracking."""

    @pytest.fixture
    def collector(self) -> RPAMetricsCollector:
        """Get a fresh metrics collector instance."""
        collector = RPAMetricsCollector.get_instance()
        collector.reset_metrics()
        return collector

    def test_record_healing_attempt_success(
        self, collector: RPAMetricsCollector
    ) -> None:
        """Test recording successful healing attempt."""
        collector.record_healing_attempt(
            selector="#old-button",
            healing_strategy="attribute_fallback",
            success=True,
            fallback_selector="[data-testid='submit']",
        )

        stats = collector.get_healing_stats()
        assert stats["total_attempts"] == 1
        assert stats["successes"] == 1
        assert stats["failures"] == 0
        assert stats["success_rate"] == 100.0

    def test_record_healing_attempt_failure(
        self, collector: RPAMetricsCollector
    ) -> None:
        """Test recording failed healing attempt."""
        collector.record_healing_attempt(
            selector="#old-button",
            healing_strategy="anchor",
            success=False,
        )

        stats = collector.get_healing_stats()
        assert stats["total_attempts"] == 1
        assert stats["successes"] == 0
        assert stats["failures"] == 1
        assert stats["success_rate"] == 0.0

    def test_multiple_healing_attempts(self, collector: RPAMetricsCollector) -> None:
        """Test multiple healing attempts."""
        collector.record_healing_attempt(
            "#btn1", "attribute_fallback", True, "#btn1-new"
        )
        collector.record_healing_attempt(
            "#btn2", "attribute_fallback", True, "#btn2-new"
        )
        collector.record_healing_attempt("#btn3", "anchor", False)
        collector.record_healing_attempt("#btn4", "anchor", True, "#btn4-new")

        stats = collector.get_healing_stats()
        assert stats["total_attempts"] == 4
        assert stats["successes"] == 3
        assert stats["failures"] == 1
        assert stats["success_rate"] == 75.0


class TestBrowserPoolMetrics:
    """Tests for browser pool metrics."""

    @pytest.fixture
    def collector(self) -> RPAMetricsCollector:
        """Get a fresh metrics collector instance."""
        collector = RPAMetricsCollector.get_instance()
        collector.reset_metrics()
        return collector

    def test_browser_acquired_released(self, collector: RPAMetricsCollector) -> None:
        """Test browser pool acquire/release tracking."""
        # These methods don't maintain internal state,
        # they just record to OTel instruments
        collector.record_browser_acquired()
        collector.record_browser_acquired()
        collector.record_browser_released()

        # No assertion on internal state since it's exported to OTel


class TestMetricsReset:
    """Tests for metrics reset functionality."""

    def test_reset_clears_all_metrics(self) -> None:
        """Test that reset clears all collected metrics."""
        collector = RPAMetricsCollector.get_instance()

        # Add some data
        collector.record_job_enqueue("job-001", "TestWorkflow")
        collector.register_robot("robot-01")
        collector.record_healing_attempt("#btn", "fallback", True)

        # Reset
        collector.reset_metrics()

        # Verify everything is cleared
        assert collector.get_queue_depth() == 0
        assert len(collector.get_active_jobs()) == 0
        assert collector.get_job_metrics().total_jobs == 0
        assert collector.get_healing_stats()["total_attempts"] == 0
