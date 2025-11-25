"""Tests for orchestrator result collection system."""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock

from casare_rpa.orchestrator.results import (
    JobResult,
    ExecutionStatistics,
    ResultCollector,
    ResultExporter,
)
from casare_rpa.orchestrator.models import Job, JobStatus, JobPriority


@pytest.fixture
def sample_job():
    """Create a sample job for testing."""
    job = Job(
        id="job-001",
        workflow_id="wf-001",
        workflow_name="Test Workflow",
        workflow_json="{}",
        robot_id="robot-001",
        robot_name="Test Robot",
        status=JobStatus.RUNNING,
        started_at=datetime.utcnow() - timedelta(seconds=60),
    )
    return job


@pytest.fixture
def sample_results():
    """Create sample results for testing."""
    now = datetime.utcnow()
    results = []

    for i in range(10):
        status = JobStatus.COMPLETED if i % 3 != 0 else JobStatus.FAILED
        result = JobResult(
            job_id=f"job-{i:03d}",
            workflow_id=f"wf-{i % 3:03d}",
            workflow_name=f"Workflow {i % 3}",
            robot_id=f"robot-{i % 2:03d}",
            robot_name=f"Robot {i % 2}",
            status=status,
            started_at=now - timedelta(minutes=i+10),
            completed_at=now - timedelta(minutes=i),
            duration_ms=5000 + i * 1000,
            error_message="Test error" if status == JobStatus.FAILED else "",
        )
        results.append(result)

    return results


class TestJobResult:
    """Tests for JobResult dataclass."""

    def test_job_result_creation(self):
        """Test creating a job result."""
        result = JobResult(
            job_id="j1",
            workflow_id="wf1",
            workflow_name="Test Workflow",
            robot_id="r1",
            robot_name="Robot 1",
            status=JobStatus.COMPLETED,
            started_at=datetime(2024, 1, 1, 12, 0, 0),
            completed_at=datetime(2024, 1, 1, 12, 1, 0),
            duration_ms=60000,
            progress=100,
            result_data={"output": "success"},
        )

        assert result.job_id == "j1"
        assert result.status == JobStatus.COMPLETED
        assert result.duration_ms == 60000
        assert result.is_success is True
        assert result.duration_seconds == 60.0

    def test_job_result_failed(self):
        """Test failed job result."""
        result = JobResult(
            job_id="j1",
            workflow_id="wf1",
            workflow_name="Test",
            robot_id="r1",
            robot_name="Robot 1",
            status=JobStatus.FAILED,
            error_message="Connection timeout",
            error_type="NetworkError",
            stack_trace="Traceback...",
            failed_node="node-5",
        )

        assert result.is_success is False
        assert result.error_message == "Connection timeout"
        assert result.error_type == "NetworkError"

    def test_job_result_to_dict(self):
        """Test conversion to dictionary."""
        result = JobResult(
            job_id="j1",
            workflow_id="wf1",
            workflow_name="Test",
            robot_id="r1",
            robot_name="Robot 1",
            status=JobStatus.COMPLETED,
            duration_ms=5000,
        )

        data = result.to_dict()

        assert data["job_id"] == "j1"
        assert data["status"] == "completed"
        assert data["duration_ms"] == 5000

    def test_job_result_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "job_id": "j1",
            "workflow_id": "wf1",
            "workflow_name": "Test",
            "robot_id": "r1",
            "robot_name": "Robot 1",
            "status": "failed",
            "duration_ms": 3000,
            "error_message": "Test error",
        }

        result = JobResult.from_dict(data)

        assert result.job_id == "j1"
        assert result.status == JobStatus.FAILED
        assert result.error_message == "Test error"

    def test_job_result_roundtrip(self):
        """Test dict serialization roundtrip."""
        original = JobResult(
            job_id="j1",
            workflow_id="wf1",
            workflow_name="Test",
            robot_id="r1",
            robot_name="Robot 1",
            status=JobStatus.COMPLETED,
            started_at=datetime(2024, 1, 1, 12, 0, 0),
            completed_at=datetime(2024, 1, 1, 12, 5, 0),
            duration_ms=300000,
            result_data={"key": "value"},
        )

        data = original.to_dict()
        restored = JobResult.from_dict(data)

        assert restored.job_id == original.job_id
        assert restored.status == original.status
        assert restored.duration_ms == original.duration_ms
        assert restored.result_data == original.result_data


class TestExecutionStatistics:
    """Tests for ExecutionStatistics dataclass."""

    def test_statistics_defaults(self):
        """Test default statistics values."""
        stats = ExecutionStatistics()

        assert stats.total_executions == 0
        assert stats.successful == 0
        assert stats.failed == 0
        assert stats.success_rate == 0.0

    def test_statistics_to_dict(self):
        """Test conversion to dictionary."""
        stats = ExecutionStatistics(
            total_executions=100,
            successful=90,
            failed=10,
            success_rate=90.0,
            avg_duration_ms=5000.0,
        )

        data = stats.to_dict()

        assert data["total_executions"] == 100
        assert data["successful"] == 90
        assert data["success_rate"] == 90.0


class TestResultCollector:
    """Tests for ResultCollector class."""

    def test_collector_initialization(self):
        """Test collector initialization."""
        collector = ResultCollector(
            max_results=1000,
            max_logs_per_job=500,
        )

        assert collector._max_results == 1000
        assert collector._max_logs_per_job == 500
        assert collector.result_count == 0

    @pytest.mark.asyncio
    async def test_collect_result_success(self, sample_job):
        """Test collecting successful result."""
        collector = ResultCollector()

        result = await collector.collect_result(
            job=sample_job,
            result_data={"output": "success"},
            duration_ms=5000,
        )

        assert result.job_id == sample_job.id
        assert result.status == JobStatus.COMPLETED
        assert result.result_data == {"output": "success"}
        assert collector.result_count == 1

    @pytest.mark.asyncio
    async def test_collect_failure(self, sample_job):
        """Test collecting failed result."""
        collector = ResultCollector()

        result = await collector.collect_failure(
            job=sample_job,
            error_message="Connection timeout",
            error_type="NetworkError",
            stack_trace="Traceback...",
            failed_node="node-5",
        )

        assert result.status == JobStatus.FAILED
        assert result.error_message == "Connection timeout"
        assert result.error_type == "NetworkError"
        assert result.failed_node == "node-5"

    @pytest.mark.asyncio
    async def test_collect_cancellation(self, sample_job):
        """Test collecting cancelled result."""
        collector = ResultCollector()

        result = await collector.collect_cancellation(
            job=sample_job,
            reason="User cancelled",
        )

        assert result.status == JobStatus.CANCELLED
        assert result.error_message == "User cancelled"

    @pytest.mark.asyncio
    async def test_collect_timeout(self, sample_job):
        """Test collecting timeout result."""
        collector = ResultCollector()

        result = await collector.collect_timeout(job=sample_job)

        assert result.status == JobStatus.TIMEOUT
        assert "timed out" in result.error_message.lower()

    def test_add_log(self):
        """Test adding log entries."""
        collector = ResultCollector()

        collector.add_log(
            job_id="j1",
            level="INFO",
            message="Starting execution",
            node_id="node-1",
        )

        collector.add_log(
            job_id="j1",
            level="DEBUG",
            message="Processing data",
        )

        assert len(collector._pending_logs["j1"]) == 2
        assert collector._pending_logs["j1"][0]["level"] == "INFO"
        assert collector._pending_logs["j1"][1]["level"] == "DEBUG"

    def test_add_log_batch(self):
        """Test adding batch log entries."""
        collector = ResultCollector()

        entries = [
            {"level": "INFO", "message": "Step 1"},
            {"level": "DEBUG", "message": "Step 2"},
            {"level": "WARNING", "message": "Step 3"},
        ]

        collector.add_log_batch("j1", entries)

        assert len(collector._pending_logs["j1"]) == 3

    def test_add_log_max_limit(self):
        """Test log limit enforcement."""
        collector = ResultCollector(max_logs_per_job=5)

        for i in range(10):
            collector.add_log("j1", "INFO", f"Log {i}")

        assert len(collector._pending_logs["j1"]) == 5
        # Should keep most recent
        assert "Log 9" in collector._pending_logs["j1"][-1]["message"]

    @pytest.mark.asyncio
    async def test_logs_attached_to_result(self, sample_job):
        """Test logs are attached to result on completion."""
        collector = ResultCollector()

        collector.add_log(sample_job.id, "INFO", "Starting")
        collector.add_log(sample_job.id, "DEBUG", "Processing")

        result = await collector.collect_result(sample_job)

        assert len(result.logs) == 2
        assert sample_job.id not in collector._pending_logs

    @pytest.mark.asyncio
    async def test_max_results_eviction(self):
        """Test old results are evicted when max reached."""
        collector = ResultCollector(max_results=5)

        for i in range(10):
            job = Job(
                id=f"j{i}",
                workflow_id="wf1",
                workflow_name="Test",
                robot_id="r1",
            )
            await collector.collect_result(job)

        assert collector.result_count == 5
        # Oldest should be evicted
        assert collector.get_result("j0") is None
        assert collector.get_result("j9") is not None

    def test_get_result(self, sample_results):
        """Test getting result by ID."""
        collector = ResultCollector()
        collector._results = {r.job_id: r for r in sample_results}
        collector._results_order = [r.job_id for r in sample_results]

        result = collector.get_result("job-005")
        assert result is not None
        assert result.job_id == "job-005"

        none_result = collector.get_result("nonexistent")
        assert none_result is None

    def test_get_results_by_workflow(self, sample_results):
        """Test getting results filtered by workflow."""
        collector = ResultCollector()
        collector._results = {r.job_id: r for r in sample_results}
        collector._results_order = [r.job_id for r in sample_results]

        results = collector.get_results_by_workflow("wf-000")
        assert len(results) > 0
        assert all(r.workflow_id == "wf-000" for r in results)

    def test_get_results_by_robot(self, sample_results):
        """Test getting results filtered by robot."""
        collector = ResultCollector()
        collector._results = {r.job_id: r for r in sample_results}
        collector._results_order = [r.job_id for r in sample_results]

        results = collector.get_results_by_robot("robot-000")
        assert len(results) > 0
        assert all(r.robot_id == "robot-000" for r in results)

    def test_get_recent_results(self, sample_results):
        """Test getting recent results."""
        collector = ResultCollector()
        collector._results = {r.job_id: r for r in sample_results}
        collector._results_order = [r.job_id for r in sample_results]

        recent = collector.get_recent_results(3)
        assert len(recent) == 3

    def test_get_failed_results(self, sample_results):
        """Test getting failed results."""
        collector = ResultCollector()
        collector._results = {r.job_id: r for r in sample_results}
        collector._results_order = [r.job_id for r in sample_results]

        failed = collector.get_failed_results()
        assert len(failed) > 0
        assert all(r.status == JobStatus.FAILED for r in failed)

    def test_get_statistics(self, sample_results):
        """Test getting statistics."""
        collector = ResultCollector()
        collector._results = {r.job_id: r for r in sample_results}
        collector._results_order = [r.job_id for r in sample_results]

        stats = collector.get_statistics()

        assert stats.total_executions == 10
        assert stats.successful > 0
        assert stats.failed > 0
        assert stats.success_rate > 0.0

    def test_get_statistics_filtered(self, sample_results):
        """Test getting filtered statistics."""
        collector = ResultCollector()
        collector._results = {r.job_id: r for r in sample_results}
        collector._results_order = [r.job_id for r in sample_results]

        stats = collector.get_statistics(workflow_id="wf-000")

        assert stats.total_executions > 0
        assert stats.total_executions < 10

    def test_get_workflow_stats(self, sample_results):
        """Test getting per-workflow statistics."""
        collector = ResultCollector()
        collector._results = {r.job_id: r for r in sample_results}
        collector._results_order = [r.job_id for r in sample_results]

        stats_map = collector.get_workflow_stats()

        assert len(stats_map) > 0
        assert "wf-000" in stats_map

    def test_get_robot_stats(self, sample_results):
        """Test getting per-robot statistics."""
        collector = ResultCollector()
        collector._results = {r.job_id: r for r in sample_results}
        collector._results_order = [r.job_id for r in sample_results]

        stats_map = collector.get_robot_stats()

        assert len(stats_map) > 0
        assert "robot-000" in stats_map

    def test_get_hourly_stats(self, sample_results):
        """Test getting hourly statistics."""
        collector = ResultCollector()
        collector._results = {r.job_id: r for r in sample_results}
        collector._results_order = [r.job_id for r in sample_results]

        hourly = collector.get_hourly_stats(hours=24)

        assert len(hourly) == 24
        assert all("hour" in h for h in hourly)

    def test_clear(self, sample_results):
        """Test clearing all results."""
        collector = ResultCollector()
        collector._results = {r.job_id: r for r in sample_results}
        collector._results_order = [r.job_id for r in sample_results]
        collector._pending_logs["j1"] = [{"level": "INFO", "message": "test"}]

        collector.clear()

        assert collector.result_count == 0
        assert collector.pending_log_count == 0

    @pytest.mark.asyncio
    async def test_callbacks(self, sample_job):
        """Test result callbacks."""
        collector = ResultCollector()

        on_received = MagicMock()
        on_stored = MagicMock()

        collector.set_callbacks(
            on_result_received=on_received,
            on_result_stored=on_stored,
        )

        await collector.collect_result(sample_job)

        on_received.assert_called_once()
        on_stored.assert_called_once()


class TestResultExporter:
    """Tests for ResultExporter class."""

    def test_to_json(self, sample_results):
        """Test exporting to JSON."""
        json_str = ResultExporter.to_json(sample_results)

        assert json_str is not None
        assert "job-000" in json_str
        assert "completed" in json_str or "failed" in json_str

    def test_to_json_pretty(self, sample_results):
        """Test exporting to pretty JSON."""
        json_str = ResultExporter.to_json(sample_results, pretty=True)

        assert "\n" in json_str
        assert "  " in json_str  # indentation

    def test_to_csv(self, sample_results):
        """Test exporting to CSV."""
        csv_str = ResultExporter.to_csv(sample_results)

        lines = csv_str.split("\n")
        assert len(lines) > 1  # Header + data

        # Check header
        assert "job_id" in lines[0]
        assert "workflow_id" in lines[0]
        assert "status" in lines[0]

    def test_to_csv_empty(self):
        """Test exporting empty results to CSV."""
        csv_str = ResultExporter.to_csv([])
        assert csv_str == ""

    def test_to_summary(self, sample_results):
        """Test generating summary."""
        summary = ResultExporter.to_summary(sample_results)

        assert summary["total"] == 10
        assert summary["successful"] > 0
        assert summary["failed"] > 0
        assert "success_rate" in summary
        assert "unique_workflows" in summary
        assert "unique_robots" in summary

    def test_to_summary_empty(self):
        """Test summary for empty results."""
        summary = ResultExporter.to_summary([])
        assert summary["total"] == 0


class TestResultCollectorEdgeCases:
    """Tests for edge cases in result collection."""

    @pytest.mark.asyncio
    async def test_update_existing_result(self):
        """Test updating an existing result."""
        collector = ResultCollector()

        job = Job(
            id="j1",
            workflow_id="wf1",
            workflow_name="Test",
            robot_id="r1",
        )

        # First result
        await collector.collect_result(job, result_data={"v": 1})

        # Update with new result
        await collector.collect_result(job, result_data={"v": 2})

        assert collector.result_count == 1
        result = collector.get_result("j1")
        assert result.result_data == {"v": 2}

    def test_statistics_cache(self, sample_results):
        """Test statistics caching."""
        collector = ResultCollector()
        collector._results = {r.job_id: r for r in sample_results}
        collector._results_order = [r.job_id for r in sample_results]

        # First call computes stats
        stats1 = collector.get_statistics()
        assert collector._stats_cache is not None

        # Second call uses cache
        stats2 = collector.get_statistics()
        assert stats1.total_executions == stats2.total_executions

    @pytest.mark.asyncio
    async def test_statistics_cache_invalidation(self, sample_job):
        """Test statistics cache invalidation on new result."""
        collector = ResultCollector()

        await collector.collect_result(sample_job)

        # Get stats to populate cache
        collector.get_statistics()
        assert collector._stats_cache is not None

        # Add new result
        job2 = Job(
            id="j2",
            workflow_id="wf1",
            workflow_name="Test",
            robot_id="r1",
        )
        await collector.collect_result(job2)

        # Cache should be invalidated
        assert collector._stats_cache is None
