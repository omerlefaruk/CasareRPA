"""
Tests for CasareRPA Scheduler System.
Tests schedule creation, storage, execution, and history tracking.
"""
import json
import pytest
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ============== Schedule Dialog Tests ==============

class TestWorkflowSchedule:
    """Tests for WorkflowSchedule data class."""

    def test_create_schedule(self):
        """Test creating a basic schedule."""
        from casare_rpa.canvas.schedule_dialog import WorkflowSchedule, ScheduleFrequency

        schedule = WorkflowSchedule(
            name="Test Schedule",
            workflow_path="/path/to/workflow.json",
            workflow_name="Test Workflow",
            frequency=ScheduleFrequency.DAILY,
            time_hour=9,
            time_minute=30
        )

        assert schedule.name == "Test Schedule"
        assert schedule.workflow_name == "Test Workflow"
        assert schedule.frequency == ScheduleFrequency.DAILY
        assert schedule.time_hour == 9
        assert schedule.time_minute == 30
        assert schedule.enabled is True
        assert schedule.id  # Should have auto-generated ID

    def test_schedule_to_dict(self):
        """Test schedule serialization to dictionary."""
        from casare_rpa.canvas.schedule_dialog import WorkflowSchedule, ScheduleFrequency

        schedule = WorkflowSchedule(
            id="test-id",
            name="Test Schedule",
            workflow_path="/path/to/workflow.json",
            workflow_name="Test Workflow",
            frequency=ScheduleFrequency.WEEKLY,
            day_of_week=2  # Wednesday
        )

        data = schedule.to_dict()

        assert data["id"] == "test-id"
        assert data["name"] == "Test Schedule"
        assert data["frequency"] == "weekly"
        assert data["day_of_week"] == 2

    def test_schedule_from_dict(self):
        """Test schedule deserialization from dictionary."""
        from casare_rpa.canvas.schedule_dialog import WorkflowSchedule, ScheduleFrequency

        data = {
            "id": "test-id",
            "name": "Loaded Schedule",
            "workflow_path": "/path/to/workflow.json",
            "workflow_name": "Workflow",
            "frequency": "monthly",
            "day_of_month": 15,
            "time_hour": 14,
            "time_minute": 0,
            "enabled": True,
            "run_count": 5,
            "success_count": 4
        }

        schedule = WorkflowSchedule.from_dict(data)

        assert schedule.id == "test-id"
        assert schedule.name == "Loaded Schedule"
        assert schedule.frequency == ScheduleFrequency.MONTHLY
        assert schedule.day_of_month == 15
        assert schedule.run_count == 5
        assert schedule.success_count == 4

    def test_calculate_next_run_daily(self):
        """Test next run calculation for daily schedule."""
        from casare_rpa.canvas.schedule_dialog import WorkflowSchedule, ScheduleFrequency

        now = datetime(2025, 1, 15, 10, 0, 0)  # 10:00 AM

        # Schedule for 9:00 AM - should be tomorrow
        schedule = WorkflowSchedule(
            name="Daily 9AM",
            workflow_path="test.json",
            frequency=ScheduleFrequency.DAILY,
            time_hour=9,
            time_minute=0
        )

        next_run = schedule.calculate_next_run(from_time=now)

        assert next_run is not None
        assert next_run.day == 16  # Next day
        assert next_run.hour == 9
        assert next_run.minute == 0

    def test_calculate_next_run_hourly(self):
        """Test next run calculation for hourly schedule."""
        from casare_rpa.canvas.schedule_dialog import WorkflowSchedule, ScheduleFrequency

        now = datetime(2025, 1, 15, 10, 45, 0)  # 10:45

        schedule = WorkflowSchedule(
            name="Hourly at :30",
            workflow_path="test.json",
            frequency=ScheduleFrequency.HOURLY,
            time_minute=30
        )

        next_run = schedule.calculate_next_run(from_time=now)

        assert next_run is not None
        assert next_run.hour == 11  # Next hour
        assert next_run.minute == 30

    def test_calculate_next_run_weekly(self):
        """Test next run calculation for weekly schedule."""
        from casare_rpa.canvas.schedule_dialog import WorkflowSchedule, ScheduleFrequency

        # Wednesday, Jan 15, 2025
        now = datetime(2025, 1, 15, 10, 0, 0)

        # Schedule for Monday (day_of_week=0)
        schedule = WorkflowSchedule(
            name="Weekly Monday",
            workflow_path="test.json",
            frequency=ScheduleFrequency.WEEKLY,
            day_of_week=0,  # Monday
            time_hour=9,
            time_minute=0
        )

        next_run = schedule.calculate_next_run(from_time=now)

        assert next_run is not None
        assert next_run.weekday() == 0  # Monday
        assert next_run > now

    def test_calculate_next_run_monthly(self):
        """Test next run calculation for monthly schedule."""
        from casare_rpa.canvas.schedule_dialog import WorkflowSchedule, ScheduleFrequency

        now = datetime(2025, 1, 20, 10, 0, 0)  # Jan 20

        # Schedule for day 15 - should be Feb 15
        schedule = WorkflowSchedule(
            name="Monthly 15th",
            workflow_path="test.json",
            frequency=ScheduleFrequency.MONTHLY,
            day_of_month=15,
            time_hour=9,
            time_minute=0
        )

        next_run = schedule.calculate_next_run(from_time=now)

        assert next_run is not None
        assert next_run.month == 2
        assert next_run.day == 15

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        from casare_rpa.canvas.schedule_dialog import WorkflowSchedule

        schedule = WorkflowSchedule(
            name="Test",
            workflow_path="test.json",
            run_count=10,
            success_count=8
        )

        assert schedule.success_rate == 80.0

    def test_success_rate_zero_runs(self):
        """Test success rate with no runs."""
        from casare_rpa.canvas.schedule_dialog import WorkflowSchedule

        schedule = WorkflowSchedule(name="Test", workflow_path="test.json")

        assert schedule.success_rate == 0.0

    def test_frequency_display(self):
        """Test human-readable frequency display."""
        from casare_rpa.canvas.schedule_dialog import WorkflowSchedule, ScheduleFrequency

        daily = WorkflowSchedule(
            name="Test",
            workflow_path="test.json",
            frequency=ScheduleFrequency.DAILY,
            time_hour=14,
            time_minute=30
        )
        assert "14:30" in daily.frequency_display

        weekly = WorkflowSchedule(
            name="Test",
            workflow_path="test.json",
            frequency=ScheduleFrequency.WEEKLY,
            day_of_week=4,  # Friday
            time_hour=9,
            time_minute=0
        )
        assert "Fri" in weekly.frequency_display

        cron = WorkflowSchedule(
            name="Test",
            workflow_path="test.json",
            frequency=ScheduleFrequency.CRON,
            cron_expression="0 9 * * MON-FRI"
        )
        assert "0 9 * * MON-FRI" in cron.frequency_display


# ============== Schedule Storage Tests ==============

class TestScheduleStorage:
    """Tests for ScheduleStorage class."""

    def test_storage_initialization(self):
        """Test storage initialization creates file."""
        from casare_rpa.canvas.schedule_storage import ScheduleStorage

        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "schedules.json"
            storage = ScheduleStorage(storage_path)

            assert storage_path.exists()
            content = json.loads(storage_path.read_text())
            assert content == []

    def test_save_and_get_schedule(self):
        """Test saving and retrieving a schedule."""
        from casare_rpa.canvas.schedule_storage import ScheduleStorage
        from casare_rpa.canvas.schedule_dialog import WorkflowSchedule, ScheduleFrequency

        with tempfile.TemporaryDirectory() as tmpdir:
            storage = ScheduleStorage(Path(tmpdir) / "schedules.json")

            schedule = WorkflowSchedule(
                id="test-123",
                name="Test Schedule",
                workflow_path="/path/to/workflow.json",
                workflow_name="Test Workflow",
                frequency=ScheduleFrequency.DAILY
            )

            # Save
            assert storage.save_schedule(schedule) is True

            # Retrieve
            retrieved = storage.get_schedule("test-123")
            assert retrieved is not None
            assert retrieved.name == "Test Schedule"
            assert retrieved.id == "test-123"

    def test_get_all_schedules(self):
        """Test getting all schedules."""
        from casare_rpa.canvas.schedule_storage import ScheduleStorage
        from casare_rpa.canvas.schedule_dialog import WorkflowSchedule

        with tempfile.TemporaryDirectory() as tmpdir:
            storage = ScheduleStorage(Path(tmpdir) / "schedules.json")

            # Save multiple schedules
            for i in range(5):
                schedule = WorkflowSchedule(
                    id=f"schedule-{i}",
                    name=f"Schedule {i}",
                    workflow_path=f"/path/workflow{i}.json"
                )
                storage.save_schedule(schedule)

            # Get all
            schedules = storage.get_all_schedules()
            assert len(schedules) == 5

    def test_update_schedule(self):
        """Test updating an existing schedule."""
        from casare_rpa.canvas.schedule_storage import ScheduleStorage
        from casare_rpa.canvas.schedule_dialog import WorkflowSchedule

        with tempfile.TemporaryDirectory() as tmpdir:
            storage = ScheduleStorage(Path(tmpdir) / "schedules.json")

            # Create
            schedule = WorkflowSchedule(
                id="test-123",
                name="Original Name",
                workflow_path="/path/workflow.json"
            )
            storage.save_schedule(schedule)

            # Update
            schedule.name = "Updated Name"
            storage.save_schedule(schedule)

            # Verify
            retrieved = storage.get_schedule("test-123")
            assert retrieved.name == "Updated Name"

            # Should still be only one schedule
            assert len(storage.get_all_schedules()) == 1

    def test_delete_schedule(self):
        """Test deleting a schedule."""
        from casare_rpa.canvas.schedule_storage import ScheduleStorage
        from casare_rpa.canvas.schedule_dialog import WorkflowSchedule

        with tempfile.TemporaryDirectory() as tmpdir:
            storage = ScheduleStorage(Path(tmpdir) / "schedules.json")

            schedule = WorkflowSchedule(
                id="to-delete",
                name="Will Delete",
                workflow_path="/path/workflow.json"
            )
            storage.save_schedule(schedule)
            assert len(storage.get_all_schedules()) == 1

            # Delete
            assert storage.delete_schedule("to-delete") is True
            assert len(storage.get_all_schedules()) == 0
            assert storage.get_schedule("to-delete") is None

    def test_get_enabled_schedules(self):
        """Test filtering enabled schedules."""
        from casare_rpa.canvas.schedule_storage import ScheduleStorage
        from casare_rpa.canvas.schedule_dialog import WorkflowSchedule

        with tempfile.TemporaryDirectory() as tmpdir:
            storage = ScheduleStorage(Path(tmpdir) / "schedules.json")

            # Mix of enabled/disabled
            for i in range(4):
                schedule = WorkflowSchedule(
                    id=f"schedule-{i}",
                    name=f"Schedule {i}",
                    workflow_path=f"/path/workflow{i}.json",
                    enabled=(i % 2 == 0)  # Even = enabled
                )
                storage.save_schedule(schedule)

            enabled = storage.get_enabled_schedules()
            assert len(enabled) == 2

    def test_get_due_schedules(self):
        """Test getting schedules due to run."""
        from casare_rpa.canvas.schedule_storage import ScheduleStorage
        from casare_rpa.canvas.schedule_dialog import WorkflowSchedule

        with tempfile.TemporaryDirectory() as tmpdir:
            storage = ScheduleStorage(Path(tmpdir) / "schedules.json")

            # Past due
            past_due = WorkflowSchedule(
                id="past-due",
                name="Past Due",
                workflow_path="/path/workflow.json",
                enabled=True,
                next_run=datetime.now() - timedelta(hours=1)
            )
            storage.save_schedule(past_due)

            # Future
            future = WorkflowSchedule(
                id="future",
                name="Future",
                workflow_path="/path/workflow.json",
                enabled=True,
                next_run=datetime.now() + timedelta(hours=1)
            )
            storage.save_schedule(future)

            due = storage.get_due_schedules()
            assert len(due) == 1
            assert due[0].id == "past-due"

    def test_mark_schedule_run(self):
        """Test marking a schedule as run."""
        from casare_rpa.canvas.schedule_storage import ScheduleStorage
        from casare_rpa.canvas.schedule_dialog import WorkflowSchedule, ScheduleFrequency

        with tempfile.TemporaryDirectory() as tmpdir:
            storage = ScheduleStorage(Path(tmpdir) / "schedules.json")

            schedule = WorkflowSchedule(
                id="test-run",
                name="Test Run",
                workflow_path="/path/workflow.json",
                frequency=ScheduleFrequency.DAILY,
                run_count=0,
                success_count=0
            )
            storage.save_schedule(schedule)

            # Mark as run (success)
            storage.mark_schedule_run("test-run", success=True)

            updated = storage.get_schedule("test-run")
            assert updated.run_count == 1
            assert updated.success_count == 1
            assert updated.last_run is not None

    def test_mark_schedule_run_failure(self):
        """Test marking a schedule run as failed."""
        from casare_rpa.canvas.schedule_storage import ScheduleStorage
        from casare_rpa.canvas.schedule_dialog import WorkflowSchedule

        with tempfile.TemporaryDirectory() as tmpdir:
            storage = ScheduleStorage(Path(tmpdir) / "schedules.json")

            schedule = WorkflowSchedule(
                id="test-fail",
                name="Test Fail",
                workflow_path="/path/workflow.json"
            )
            storage.save_schedule(schedule)

            # Mark as failed
            storage.mark_schedule_run("test-fail", success=False, error_message="Test error")

            updated = storage.get_schedule("test-fail")
            assert updated.run_count == 1
            assert updated.success_count == 0
            assert updated.failure_count == 1
            assert updated.last_error == "Test error"

    def test_save_all_schedules(self):
        """Test saving all schedules at once."""
        from casare_rpa.canvas.schedule_storage import ScheduleStorage
        from casare_rpa.canvas.schedule_dialog import WorkflowSchedule

        with tempfile.TemporaryDirectory() as tmpdir:
            storage = ScheduleStorage(Path(tmpdir) / "schedules.json")

            schedules = [
                WorkflowSchedule(id=f"s-{i}", name=f"Schedule {i}", workflow_path=f"/path/{i}.json")
                for i in range(3)
            ]

            assert storage.save_all_schedules(schedules) is True
            assert len(storage.get_all_schedules()) == 3


# ============== Execution History Tests ==============

class TestExecutionHistory:
    """Tests for ExecutionHistory class."""

    def test_history_initialization(self):
        """Test history initialization creates file."""
        from casare_rpa.scheduler.execution_history import ExecutionHistory

        with tempfile.TemporaryDirectory() as tmpdir:
            history_path = Path(tmpdir) / "history.json"
            history = ExecutionHistory(storage_path=history_path)

            assert history_path.exists()

    def test_add_entry(self):
        """Test adding an entry to history."""
        from casare_rpa.scheduler.execution_history import ExecutionHistory, ExecutionHistoryEntry

        with tempfile.TemporaryDirectory() as tmpdir:
            history = ExecutionHistory(storage_path=Path(tmpdir) / "history.json")

            entry = ExecutionHistoryEntry(
                id="entry-1",
                schedule_id="schedule-1",
                schedule_name="Test Schedule",
                workflow_path="/path/workflow.json",
                workflow_name="Test Workflow",
                status="completed",
                started_at=datetime.now(),
                completed_at=datetime.now(),
                success=True,
                duration_ms=5000
            )

            assert history.add_entry(entry) is True

            entries = history.get_entries()
            assert len(entries) == 1
            assert entries[0].schedule_name == "Test Schedule"

    def test_get_entries_with_filter(self):
        """Test getting entries with filters."""
        from casare_rpa.scheduler.execution_history import ExecutionHistory, ExecutionHistoryEntry

        with tempfile.TemporaryDirectory() as tmpdir:
            history = ExecutionHistory(storage_path=Path(tmpdir) / "history.json")

            # Add mixed entries
            for i in range(10):
                entry = ExecutionHistoryEntry(
                    id=f"entry-{i}",
                    schedule_id=f"schedule-{i % 2}",  # Two schedules
                    schedule_name=f"Schedule {i % 2}",
                    workflow_path="/path/workflow.json",
                    workflow_name="Workflow",
                    status="completed" if i % 3 != 0 else "failed",
                    started_at=datetime.now() - timedelta(hours=i),
                    success=i % 3 != 0
                )
                history.add_entry(entry)

            # Filter by schedule
            schedule_0 = history.get_entries(schedule_id="schedule-0")
            assert all(e.schedule_id == "schedule-0" for e in schedule_0)

            # Filter by status
            failures = history.get_entries(status="failed")
            assert all(e.status == "failed" for e in failures)

    def test_get_for_schedule(self):
        """Test getting entries for specific schedule."""
        from casare_rpa.scheduler.execution_history import ExecutionHistory, ExecutionHistoryEntry

        with tempfile.TemporaryDirectory() as tmpdir:
            history = ExecutionHistory(storage_path=Path(tmpdir) / "history.json")

            for i in range(5):
                entry = ExecutionHistoryEntry(
                    id=f"entry-{i}",
                    schedule_id="target-schedule" if i < 3 else "other",
                    schedule_name="Target",
                    workflow_path="/path/workflow.json",
                    workflow_name="Workflow",
                    status="completed",
                    started_at=datetime.now()
                )
                history.add_entry(entry)

            target_entries = history.get_for_schedule("target-schedule")
            assert len(target_entries) == 3

    def test_get_failures(self):
        """Test getting failed executions."""
        from casare_rpa.scheduler.execution_history import ExecutionHistory, ExecutionHistoryEntry

        with tempfile.TemporaryDirectory() as tmpdir:
            history = ExecutionHistory(storage_path=Path(tmpdir) / "history.json")

            for i in range(6):
                entry = ExecutionHistoryEntry(
                    id=f"entry-{i}",
                    schedule_id="schedule",
                    schedule_name="Schedule",
                    workflow_path="/path/workflow.json",
                    workflow_name="Workflow",
                    status="failed" if i < 2 else "completed",
                    started_at=datetime.now(),
                    success=i >= 2
                )
                history.add_entry(entry)

            failures = history.get_failures()
            assert len(failures) == 2

    def test_get_statistics(self):
        """Test getting execution statistics."""
        from casare_rpa.scheduler.execution_history import ExecutionHistory, ExecutionHistoryEntry

        with tempfile.TemporaryDirectory() as tmpdir:
            history = ExecutionHistory(storage_path=Path(tmpdir) / "history.json")

            # Add 10 entries: 7 success, 3 failed
            for i in range(10):
                entry = ExecutionHistoryEntry(
                    id=f"entry-{i}",
                    schedule_id=f"schedule-{i % 2}",
                    schedule_name=f"Schedule {i % 2}",
                    workflow_path="/path/workflow.json",
                    workflow_name="Workflow",
                    status="completed" if i < 7 else "failed",
                    started_at=datetime.now(),
                    success=i < 7,
                    duration_ms=1000 + i * 100
                )
                history.add_entry(entry)

            stats = history.get_statistics(days=7)

            assert stats["total_executions"] == 10
            assert stats["successful"] == 7
            assert stats["failed"] == 3
            assert stats["success_rate"] == 70.0
            assert stats["avg_duration_ms"] > 0
            assert len(stats["by_schedule"]) == 2

    def test_cleanup_old_entries(self):
        """Test automatic cleanup of old entries."""
        from casare_rpa.scheduler.execution_history import ExecutionHistory, ExecutionHistoryEntry

        with tempfile.TemporaryDirectory() as tmpdir:
            # Short retention for testing
            history = ExecutionHistory(
                storage_path=Path(tmpdir) / "history.json",
                retention_days=7
            )

            # Add old entry
            old_entry = ExecutionHistoryEntry(
                id="old-entry",
                schedule_id="old-schedule",
                schedule_name="Old Schedule",
                workflow_path="/path/workflow.json",
                workflow_name="Workflow",
                status="completed",
                started_at=datetime.now() - timedelta(days=30)  # 30 days old
            )
            history.add_entry(old_entry)

            # Add new entry
            new_entry = ExecutionHistoryEntry(
                id="new-entry",
                schedule_id="new-schedule",
                schedule_name="New Schedule",
                workflow_path="/path/workflow.json",
                workflow_name="Workflow",
                status="completed",
                started_at=datetime.now()
            )
            history.add_entry(new_entry)

            # Old entry should be cleaned up
            entries = history.get_entries(limit=100)
            assert len(entries) == 1
            # Verify it's the new entry by checking schedule_id (id is auto-generated)
            assert entries[0].schedule_id == "new-schedule"

    def test_clear_history(self):
        """Test clearing all history."""
        from casare_rpa.scheduler.execution_history import ExecutionHistory, ExecutionHistoryEntry

        with tempfile.TemporaryDirectory() as tmpdir:
            history = ExecutionHistory(storage_path=Path(tmpdir) / "history.json")

            for i in range(5):
                entry = ExecutionHistoryEntry(
                    id=f"entry-{i}",
                    schedule_id="schedule",
                    schedule_name="Schedule",
                    workflow_path="/path/workflow.json",
                    workflow_name="Workflow",
                    status="completed",
                    started_at=datetime.now()
                )
                history.add_entry(entry)

            assert len(history.get_entries()) == 5

            history.clear_history()
            assert len(history.get_entries()) == 0

    def test_delete_for_schedule(self):
        """Test deleting history for specific schedule."""
        from casare_rpa.scheduler.execution_history import ExecutionHistory, ExecutionHistoryEntry

        with tempfile.TemporaryDirectory() as tmpdir:
            history = ExecutionHistory(storage_path=Path(tmpdir) / "history.json")

            for i in range(6):
                entry = ExecutionHistoryEntry(
                    id=f"entry-{i}",
                    schedule_id="to-delete" if i < 4 else "keep",
                    schedule_name="Schedule",
                    workflow_path="/path/workflow.json",
                    workflow_name="Workflow",
                    status="completed",
                    started_at=datetime.now()
                )
                history.add_entry(entry)

            assert history.delete_for_schedule("to-delete") is True

            entries = history.get_entries()
            assert len(entries) == 2
            assert all(e.schedule_id == "keep" for e in entries)

    def test_duration_formatted(self):
        """Test duration formatting."""
        from casare_rpa.scheduler.execution_history import ExecutionHistoryEntry

        # Seconds
        entry1 = ExecutionHistoryEntry(
            id="1", schedule_id="s", schedule_name="S",
            workflow_path="", workflow_name="",
            status="completed", started_at=datetime.now(),
            duration_ms=45000  # 45 seconds
        )
        assert "s" in entry1.duration_formatted

        # Minutes
        entry2 = ExecutionHistoryEntry(
            id="2", schedule_id="s", schedule_name="S",
            workflow_path="", workflow_name="",
            status="completed", started_at=datetime.now(),
            duration_ms=180000  # 3 minutes
        )
        assert "m" in entry2.duration_formatted

        # Hours
        entry3 = ExecutionHistoryEntry(
            id="3", schedule_id="s", schedule_name="S",
            workflow_path="", workflow_name="",
            status="completed", started_at=datetime.now(),
            duration_ms=7200000  # 2 hours
        )
        assert "h" in entry3.duration_formatted


# ============== Scheduler Service Tests ==============

class TestSchedulerConfig:
    """Tests for SchedulerConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        from casare_rpa.scheduler.workflow_scheduler import SchedulerConfig

        config = SchedulerConfig()

        assert config.check_interval_seconds == 60
        assert config.max_concurrent_executions == 3
        assert config.execution_timeout_seconds == 3600
        assert config.retry_failed is False

    def test_custom_config(self):
        """Test custom configuration."""
        from casare_rpa.scheduler.workflow_scheduler import SchedulerConfig

        config = SchedulerConfig(
            check_interval_seconds=30,
            max_concurrent_executions=5,
            retry_failed=True,
            max_retries=5
        )

        assert config.check_interval_seconds == 30
        assert config.max_concurrent_executions == 5
        assert config.retry_failed is True
        assert config.max_retries == 5


class TestScheduleExecutionResult:
    """Tests for ScheduleExecutionResult."""

    def test_create_result(self):
        """Test creating an execution result."""
        from casare_rpa.scheduler.workflow_scheduler import (
            ScheduleExecutionResult, ScheduleStatus
        )

        result = ScheduleExecutionResult(
            schedule_id="test-id",
            schedule_name="Test Schedule",
            workflow_path="/path/workflow.json",
            workflow_name="Test Workflow",
            status=ScheduleStatus.COMPLETED,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            success=True,
            duration_ms=5000
        )

        assert result.schedule_id == "test-id"
        assert result.status == ScheduleStatus.COMPLETED
        assert result.success is True

    def test_result_to_dict(self):
        """Test result serialization."""
        from casare_rpa.scheduler.workflow_scheduler import (
            ScheduleExecutionResult, ScheduleStatus
        )

        result = ScheduleExecutionResult(
            schedule_id="test-id",
            schedule_name="Test",
            workflow_path="/path/workflow.json",
            workflow_name="Workflow",
            status=ScheduleStatus.FAILED,
            started_at=datetime.now(),
            success=False,
            error_message="Test error"
        )

        data = result.to_dict()

        assert data["schedule_id"] == "test-id"
        assert data["status"] == "failed"
        assert data["error_message"] == "Test error"


@pytest.mark.asyncio
class TestWorkflowSchedulerService:
    """Tests for WorkflowSchedulerService."""

    async def test_scheduler_start_stop(self):
        """Test starting and stopping scheduler."""
        pytest.importorskip("apscheduler")
        from casare_rpa.scheduler.workflow_scheduler import WorkflowSchedulerService

        scheduler = WorkflowSchedulerService()

        # Mock schedule storage
        with patch("casare_rpa.scheduler.workflow_scheduler.WorkflowSchedulerService._load_schedules"):
            started = await scheduler.start()
            assert started is True
            assert scheduler.is_running is True

            await scheduler.stop()
            assert scheduler.is_running is False

    async def test_scheduler_get_next_runs(self):
        """Test getting next scheduled runs."""
        pytest.importorskip("apscheduler")
        from casare_rpa.scheduler.workflow_scheduler import WorkflowSchedulerService

        scheduler = WorkflowSchedulerService()

        # Not running - should return empty
        runs = scheduler.get_next_runs()
        assert runs == []

    async def test_scheduler_callbacks(self):
        """Test scheduler callbacks."""
        pytest.importorskip("apscheduler")
        from casare_rpa.scheduler.workflow_scheduler import WorkflowSchedulerService

        start_called = []
        complete_called = []
        error_called = []

        scheduler = WorkflowSchedulerService(
            on_execution_start=lambda r: start_called.append(r),
            on_execution_complete=lambda r: complete_called.append(r),
            on_execution_error=lambda r: error_called.append(r)
        )

        # Verify callbacks are set
        assert scheduler._on_execution_start is not None
        assert scheduler._on_execution_complete is not None
        assert scheduler._on_execution_error is not None


# ============== Integration Tests ==============

class TestSchedulerIntegration:
    """Integration tests for the scheduler system."""

    def test_schedule_roundtrip(self):
        """Test creating, saving, and loading a schedule."""
        from casare_rpa.canvas.schedule_dialog import WorkflowSchedule, ScheduleFrequency
        from casare_rpa.canvas.schedule_storage import ScheduleStorage

        with tempfile.TemporaryDirectory() as tmpdir:
            storage = ScheduleStorage(Path(tmpdir) / "schedules.json")

            # Create schedule
            original = WorkflowSchedule(
                name="Integration Test",
                workflow_path="/path/to/workflow.json",
                workflow_name="Test Workflow",
                frequency=ScheduleFrequency.DAILY,
                time_hour=10,
                time_minute=30,
                enabled=True
            )

            # Calculate next run
            original.next_run = original.calculate_next_run()

            # Save
            storage.save_schedule(original)

            # Load
            loaded = storage.get_schedule(original.id)

            # Verify
            assert loaded is not None
            assert loaded.name == original.name
            assert loaded.frequency == original.frequency
            assert loaded.time_hour == original.time_hour
            assert loaded.enabled == original.enabled

    def test_execution_history_roundtrip(self):
        """Test recording and retrieving execution history."""
        from casare_rpa.scheduler.execution_history import (
            ExecutionHistory, ExecutionHistoryEntry
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            history = ExecutionHistory(Path(tmpdir) / "history.json")

            # Record execution
            entry = ExecutionHistoryEntry(
                id="exec-1",
                schedule_id="schedule-1",
                schedule_name="Test Schedule",
                workflow_path="/path/workflow.json",
                workflow_name="Test Workflow",
                status="completed",
                started_at=datetime.now() - timedelta(seconds=30),
                completed_at=datetime.now(),
                success=True,
                duration_ms=30000
            )

            history.add_entry(entry)

            # Retrieve
            entries = history.get_for_schedule("schedule-1")
            assert len(entries) == 1

            # Get stats
            stats = history.get_statistics(days=1)
            assert stats["total_executions"] == 1
            assert stats["success_rate"] == 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
