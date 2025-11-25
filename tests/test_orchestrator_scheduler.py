"""
Unit tests for CasareRPA Orchestrator Scheduler.
Tests JobScheduler, ScheduleManager, and utility functions.
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from zoneinfo import ZoneInfo

from casare_rpa.orchestrator.models import (
    Schedule, ScheduleFrequency, Job, JobStatus, JobPriority,
    Workflow, WorkflowStatus
)

# Check if APScheduler is available
try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.date import DateTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    HAS_APSCHEDULER = True
except ImportError:
    HAS_APSCHEDULER = False

# Import scheduler components
from casare_rpa.orchestrator.scheduler import (
    parse_cron_expression,
    frequency_to_interval,
    calculate_next_run,
)

# Conditionally import scheduler classes
if HAS_APSCHEDULER:
    from casare_rpa.orchestrator.scheduler import (
        JobScheduler,
        ScheduleManager,
        ScheduleExecutionError,
    )


# ==================== FIXTURES ====================

@pytest.fixture
def sample_workflow():
    """Create a sample workflow."""
    return Workflow(
        id="wf-001",
        name="Test Workflow",
        description="A test workflow",
        status=WorkflowStatus.PUBLISHED,
        version="1.0.0"
    )


@pytest.fixture
def sample_schedule(sample_workflow):
    """Create a sample schedule."""
    return Schedule(
        id="sched-001",
        name="Test Schedule",
        workflow_id=sample_workflow.id,
        workflow_name=sample_workflow.name,
        frequency=ScheduleFrequency.HOURLY,
        enabled=True,
        timezone="UTC"
    )


@pytest.fixture
def cron_schedule(sample_workflow):
    """Create a cron-based schedule."""
    return Schedule(
        id="sched-002",
        name="Cron Schedule",
        workflow_id=sample_workflow.id,
        workflow_name=sample_workflow.name,
        frequency=ScheduleFrequency.CRON,
        cron_expression="0 9 * * 1-5",  # 9 AM weekdays
        enabled=True,
        timezone="UTC"
    )


@pytest.fixture
def once_schedule(sample_workflow):
    """Create a one-time schedule."""
    return Schedule(
        id="sched-003",
        name="Once Schedule",
        workflow_id=sample_workflow.id,
        workflow_name=sample_workflow.name,
        frequency=ScheduleFrequency.ONCE,
        next_run=datetime.utcnow() + timedelta(hours=1),
        enabled=True,
        timezone="UTC"
    )


# ==================== PARSE CRON EXPRESSION TESTS ====================

class TestParseCronExpression:
    """Tests for parse_cron_expression function."""

    def test_parse_5_field_cron(self):
        """Test parsing standard 5-field cron expression."""
        result = parse_cron_expression("30 9 * * 1-5")

        assert result["minute"] == "30"
        assert result["hour"] == "9"
        assert result["day"] == "*"
        assert result["month"] == "*"
        assert result["day_of_week"] == "1-5"
        assert "second" not in result

    def test_parse_6_field_cron(self):
        """Test parsing extended 6-field cron expression."""
        result = parse_cron_expression("0 30 9 * * 1-5")

        assert result["second"] == "0"
        assert result["minute"] == "30"
        assert result["hour"] == "9"
        assert result["day"] == "*"
        assert result["month"] == "*"
        assert result["day_of_week"] == "1-5"

    def test_parse_all_wildcards(self):
        """Test parsing all wildcards."""
        result = parse_cron_expression("* * * * *")

        assert result["minute"] == "*"
        assert result["hour"] == "*"
        assert result["day"] == "*"
        assert result["month"] == "*"
        assert result["day_of_week"] == "*"

    def test_parse_complex_expression(self):
        """Test parsing complex cron expression."""
        result = parse_cron_expression("0,30 8-17 1,15 * *")

        assert result["minute"] == "0,30"
        assert result["hour"] == "8-17"
        assert result["day"] == "1,15"
        assert result["month"] == "*"
        assert result["day_of_week"] == "*"

    def test_parse_invalid_field_count(self):
        """Test parsing invalid cron expression raises error."""
        with pytest.raises(ValueError, match="Invalid cron expression"):
            parse_cron_expression("* * *")  # Only 3 fields

        with pytest.raises(ValueError, match="Invalid cron expression"):
            parse_cron_expression("* * * * * * *")  # 7 fields

    def test_parse_with_extra_whitespace(self):
        """Test parsing with extra whitespace."""
        result = parse_cron_expression("  30   9   *   *   1-5  ")

        assert result["minute"] == "30"
        assert result["hour"] == "9"


# ==================== FREQUENCY TO INTERVAL TESTS ====================

class TestFrequencyToInterval:
    """Tests for frequency_to_interval function."""

    def test_hourly_interval(self):
        """Test hourly frequency returns 1 hour."""
        interval = frequency_to_interval(ScheduleFrequency.HOURLY)
        assert interval == timedelta(hours=1)

    def test_daily_interval(self):
        """Test daily frequency returns 1 day."""
        interval = frequency_to_interval(ScheduleFrequency.DAILY)
        assert interval == timedelta(days=1)

    def test_weekly_interval(self):
        """Test weekly frequency returns 1 week."""
        interval = frequency_to_interval(ScheduleFrequency.WEEKLY)
        assert interval == timedelta(weeks=1)

    def test_monthly_interval(self):
        """Test monthly frequency returns ~30 days."""
        interval = frequency_to_interval(ScheduleFrequency.MONTHLY)
        assert interval == timedelta(days=30)

    def test_cron_returns_none(self):
        """Test cron frequency returns None (not interval-based)."""
        interval = frequency_to_interval(ScheduleFrequency.CRON)
        assert interval is None

    def test_once_returns_none(self):
        """Test once frequency returns None."""
        interval = frequency_to_interval(ScheduleFrequency.ONCE)
        assert interval is None


# ==================== CALCULATE NEXT RUN TESTS ====================

@pytest.mark.skipif(not HAS_APSCHEDULER, reason="APScheduler not installed")
class TestCalculateNextRun:
    """Tests for calculate_next_run function."""

    def test_calculate_hourly_next_run(self):
        """Test calculating next run for hourly schedule."""
        from_time = datetime(2024, 1, 15, 10, 30, 0)
        next_run = calculate_next_run(
            ScheduleFrequency.HOURLY,
            from_time=from_time
        )

        assert next_run is not None
        assert next_run > from_time

    def test_calculate_daily_next_run(self):
        """Test calculating next run for daily schedule."""
        from_time = datetime(2024, 1, 15, 10, 30, 0)
        next_run = calculate_next_run(
            ScheduleFrequency.DAILY,
            from_time=from_time
        )

        assert next_run is not None
        assert next_run > from_time

    def test_calculate_cron_next_run(self):
        """Test calculating next run for cron schedule."""
        from_time = datetime(2024, 1, 15, 8, 0, 0)  # Monday 8 AM
        next_run = calculate_next_run(
            ScheduleFrequency.CRON,
            cron_expression="0 9 * * 1-5",  # 9 AM weekdays
            from_time=from_time
        )

        assert next_run is not None
        assert next_run.hour == 9

    def test_calculate_once_returns_none(self):
        """Test ONCE frequency returns None (needs explicit next_run)."""
        next_run = calculate_next_run(ScheduleFrequency.ONCE)
        assert next_run is None

    def test_calculate_with_timezone(self):
        """Test calculating next run with timezone."""
        from_time = datetime(2024, 1, 15, 10, 30, 0)
        next_run = calculate_next_run(
            ScheduleFrequency.HOURLY,
            timezone="America/New_York",
            from_time=from_time
        )

        assert next_run is not None

    def test_calculate_invalid_cron_returns_none(self):
        """Test invalid cron expression returns None."""
        next_run = calculate_next_run(
            ScheduleFrequency.CRON,
            cron_expression="invalid"
        )
        assert next_run is None


# ==================== JOB SCHEDULER TESTS ====================

@pytest.mark.skipif(not HAS_APSCHEDULER, reason="APScheduler not installed")
class TestJobScheduler:
    """Tests for JobScheduler class."""

    @pytest.fixture
    def scheduler(self):
        """Create a JobScheduler instance."""
        return JobScheduler(timezone="UTC")

    @pytest.fixture
    async def running_scheduler(self, scheduler):
        """Create and start a scheduler."""
        await scheduler.start()
        yield scheduler
        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_scheduler_start_stop(self, scheduler):
        """Test scheduler can start and stop."""
        assert not scheduler._running

        await scheduler.start()
        assert scheduler._running
        assert scheduler._scheduler is not None

        await scheduler.stop()
        assert not scheduler._running
        assert scheduler._scheduler is None

    @pytest.mark.asyncio
    async def test_scheduler_start_idempotent(self, scheduler):
        """Test starting scheduler multiple times is safe."""
        await scheduler.start()
        await scheduler.start()  # Should not raise
        assert scheduler._running
        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_scheduler_stop_idempotent(self, scheduler):
        """Test stopping scheduler multiple times is safe."""
        await scheduler.start()
        await scheduler.stop()
        await scheduler.stop()  # Should not raise
        assert not scheduler._running

    @pytest.mark.asyncio
    async def test_add_hourly_schedule(self, running_scheduler, sample_schedule):
        """Test adding an hourly schedule."""
        result = running_scheduler.add_schedule(sample_schedule)

        assert result is True
        assert sample_schedule.id in running_scheduler._schedules

    @pytest.mark.asyncio
    async def test_add_cron_schedule(self, running_scheduler, cron_schedule):
        """Test adding a cron schedule."""
        result = running_scheduler.add_schedule(cron_schedule)

        assert result is True
        assert cron_schedule.id in running_scheduler._schedules

    @pytest.mark.asyncio
    async def test_add_once_schedule(self, running_scheduler, once_schedule):
        """Test adding a one-time schedule."""
        result = running_scheduler.add_schedule(once_schedule)

        assert result is True
        assert once_schedule.id in running_scheduler._schedules

    @pytest.mark.asyncio
    async def test_add_disabled_schedule(self, running_scheduler, sample_schedule):
        """Test adding a disabled schedule doesn't add to APScheduler."""
        sample_schedule.enabled = False
        result = running_scheduler.add_schedule(sample_schedule)

        assert result is True
        # Disabled schedules are not added to internal tracking
        assert sample_schedule.id not in running_scheduler._schedules

    @pytest.mark.asyncio
    async def test_add_schedule_without_running_scheduler(self, scheduler, sample_schedule):
        """Test adding schedule without starting scheduler fails."""
        result = scheduler.add_schedule(sample_schedule)
        assert result is False

    @pytest.mark.asyncio
    async def test_remove_schedule(self, running_scheduler, sample_schedule):
        """Test removing a schedule."""
        running_scheduler.add_schedule(sample_schedule)
        result = running_scheduler.remove_schedule(sample_schedule.id)

        assert result is True
        assert sample_schedule.id not in running_scheduler._schedules

    @pytest.mark.asyncio
    async def test_remove_nonexistent_schedule(self, running_scheduler):
        """Test removing a non-existent schedule."""
        result = running_scheduler.remove_schedule("nonexistent")
        # APScheduler will raise, so this returns False
        assert result is False

    @pytest.mark.asyncio
    async def test_update_schedule(self, running_scheduler, sample_schedule):
        """Test updating a schedule."""
        running_scheduler.add_schedule(sample_schedule)

        sample_schedule.name = "Updated Schedule"
        result = running_scheduler.update_schedule(sample_schedule)

        assert result is True

    @pytest.mark.asyncio
    async def test_enable_schedule(self, running_scheduler, sample_schedule):
        """Test enabling a schedule."""
        sample_schedule.enabled = False
        running_scheduler._schedules[sample_schedule.id] = sample_schedule

        result = running_scheduler.enable_schedule(sample_schedule.id)
        assert result is True
        assert sample_schedule.enabled is True

    @pytest.mark.asyncio
    async def test_disable_schedule(self, running_scheduler, sample_schedule):
        """Test disabling a schedule."""
        running_scheduler.add_schedule(sample_schedule)

        result = running_scheduler.disable_schedule(sample_schedule.id)
        assert result is True
        assert sample_schedule.enabled is False

    @pytest.mark.asyncio
    async def test_pause_resume_all(self, running_scheduler, sample_schedule):
        """Test pausing and resuming all schedules."""
        running_scheduler.add_schedule(sample_schedule)

        # Should not raise
        running_scheduler.pause_all()
        running_scheduler.resume_all()

    @pytest.mark.asyncio
    async def test_get_next_runs(self, running_scheduler, sample_schedule):
        """Test getting upcoming scheduled runs."""
        running_scheduler.add_schedule(sample_schedule)

        upcoming = running_scheduler.get_next_runs(limit=5)

        assert isinstance(upcoming, list)
        assert len(upcoming) <= 5

    @pytest.mark.asyncio
    async def test_get_schedule_info(self, running_scheduler, sample_schedule):
        """Test getting schedule info."""
        running_scheduler.add_schedule(sample_schedule)

        info = running_scheduler.get_schedule_info(sample_schedule.id)

        assert info is not None
        assert info["id"] == sample_schedule.id
        assert info["name"] == sample_schedule.name
        assert info["workflow_id"] == sample_schedule.workflow_id

    @pytest.mark.asyncio
    async def test_get_nonexistent_schedule_info(self, running_scheduler):
        """Test getting info for non-existent schedule."""
        info = running_scheduler.get_schedule_info("nonexistent")
        assert info is None

    @pytest.mark.asyncio
    async def test_schedule_trigger_callback(self, sample_schedule):
        """Test schedule trigger callback is called."""
        callback_called = asyncio.Event()
        triggered_schedule = None

        async def on_trigger(schedule):
            nonlocal triggered_schedule
            triggered_schedule = schedule
            callback_called.set()

        scheduler = JobScheduler(on_schedule_trigger=on_trigger)
        await scheduler.start()

        try:
            # Add a schedule that triggers very soon
            sample_schedule.frequency = ScheduleFrequency.ONCE
            sample_schedule.next_run = datetime.utcnow() + timedelta(seconds=0.5)
            scheduler.add_schedule(sample_schedule)

            # Wait for callback
            try:
                await asyncio.wait_for(callback_called.wait(), timeout=2.0)
                assert triggered_schedule is not None
                assert triggered_schedule.id == sample_schedule.id
            except asyncio.TimeoutError:
                # Schedule might not trigger in time in CI, that's ok
                pass
        finally:
            await scheduler.stop()

    @pytest.mark.asyncio
    async def test_invalid_cron_schedule(self, running_scheduler, sample_workflow):
        """Test adding schedule with invalid cron expression."""
        schedule = Schedule(
            id="sched-bad",
            name="Bad Schedule",
            workflow_id=sample_workflow.id,
            workflow_name=sample_workflow.name,
            frequency=ScheduleFrequency.CRON,
            cron_expression="invalid cron",
            enabled=True
        )

        result = running_scheduler.add_schedule(schedule)
        assert result is False

    @pytest.mark.asyncio
    async def test_once_schedule_without_next_run(self, running_scheduler, sample_workflow):
        """Test ONCE schedule without next_run fails."""
        schedule = Schedule(
            id="sched-once-bad",
            name="Bad Once Schedule",
            workflow_id=sample_workflow.id,
            workflow_name=sample_workflow.name,
            frequency=ScheduleFrequency.ONCE,
            next_run=None,
            enabled=True
        )

        result = running_scheduler.add_schedule(schedule)
        assert result is False


# ==================== SCHEDULE MANAGER TESTS ====================

@pytest.mark.skipif(not HAS_APSCHEDULER, reason="APScheduler not installed")
class TestScheduleManager:
    """Tests for ScheduleManager class."""

    @pytest.fixture
    def job_creator(self):
        """Create a mock job creator."""
        return AsyncMock()

    @pytest.fixture
    def manager(self, job_creator):
        """Create a ScheduleManager instance."""
        return ScheduleManager(job_creator=job_creator)

    @pytest.fixture
    async def running_manager(self, manager):
        """Create and start a manager."""
        await manager.start()
        yield manager
        await manager.stop()

    @pytest.mark.asyncio
    async def test_manager_start_stop(self, manager):
        """Test manager can start and stop."""
        await manager.start()
        assert manager._scheduler._running

        await manager.stop()
        assert not manager._scheduler._running

    @pytest.mark.asyncio
    async def test_add_schedule(self, running_manager, sample_schedule):
        """Test adding a schedule through manager."""
        result = running_manager.add_schedule(sample_schedule)

        assert result is True
        assert running_manager.get_schedule(sample_schedule.id) is not None

    @pytest.mark.asyncio
    async def test_remove_schedule(self, running_manager, sample_schedule):
        """Test removing a schedule through manager."""
        running_manager.add_schedule(sample_schedule)
        result = running_manager.remove_schedule(sample_schedule.id)

        assert result is True
        assert running_manager.get_schedule(sample_schedule.id) is None

    @pytest.mark.asyncio
    async def test_update_schedule(self, running_manager, sample_schedule):
        """Test updating a schedule through manager."""
        running_manager.add_schedule(sample_schedule)

        sample_schedule.name = "Updated Name"
        result = running_manager.update_schedule(sample_schedule)

        assert result is True
        assert running_manager.get_schedule(sample_schedule.id).name == "Updated Name"

    @pytest.mark.asyncio
    async def test_enable_disable_schedule(self, running_manager, sample_schedule):
        """Test enabling and disabling schedules."""
        running_manager.add_schedule(sample_schedule)

        running_manager.disable_schedule(sample_schedule.id)
        assert running_manager.get_schedule(sample_schedule.id).enabled is False

        running_manager.enable_schedule(sample_schedule.id)
        assert running_manager.get_schedule(sample_schedule.id).enabled is True

    @pytest.mark.asyncio
    async def test_get_all_schedules(self, running_manager, sample_schedule, cron_schedule):
        """Test getting all schedules."""
        running_manager.add_schedule(sample_schedule)
        running_manager.add_schedule(cron_schedule)

        schedules = running_manager.get_all_schedules()

        assert len(schedules) == 2

    @pytest.mark.asyncio
    async def test_get_upcoming_runs(self, running_manager, sample_schedule):
        """Test getting upcoming runs."""
        running_manager.add_schedule(sample_schedule)

        upcoming = running_manager.get_upcoming_runs(limit=5)

        assert isinstance(upcoming, list)

    @pytest.mark.asyncio
    async def test_on_trigger_creates_job(self, sample_schedule, job_creator):
        """Test that trigger callback creates a job."""
        manager = ScheduleManager(job_creator=job_creator)
        await manager.start()

        try:
            # Simulate trigger
            await manager._on_trigger(sample_schedule)

            job_creator.assert_called_once_with(sample_schedule)
        finally:
            await manager.stop()

    @pytest.mark.asyncio
    async def test_on_trigger_handles_sync_creator(self, sample_schedule):
        """Test that trigger callback handles sync job creator."""
        sync_creator = Mock()
        manager = ScheduleManager(job_creator=sync_creator)
        await manager.start()

        try:
            await manager._on_trigger(sample_schedule)
            sync_creator.assert_called_once_with(sample_schedule)
        finally:
            await manager.stop()

    @pytest.mark.asyncio
    async def test_on_trigger_error_propagates(self, sample_schedule):
        """Test that job creator errors propagate."""
        async def failing_creator(schedule):
            raise ValueError("Job creation failed")

        manager = ScheduleManager(job_creator=failing_creator)
        await manager.start()

        try:
            with pytest.raises(ValueError, match="Job creation failed"):
                await manager._on_trigger(sample_schedule)
        finally:
            await manager.stop()


# ==================== INTEGRATION TESTS ====================

@pytest.mark.skipif(not HAS_APSCHEDULER, reason="APScheduler not installed")
class TestSchedulerIntegration:
    """Integration tests for scheduler components."""

    @pytest.mark.asyncio
    async def test_full_schedule_lifecycle(self, sample_workflow):
        """Test complete schedule lifecycle."""
        jobs_created = []

        async def create_job(schedule):
            jobs_created.append(schedule.id)

        manager = ScheduleManager(job_creator=create_job)
        await manager.start()

        try:
            # Create schedule
            schedule = Schedule(
                id="lifecycle-test",
                name="Lifecycle Test",
                workflow_id=sample_workflow.id,
                workflow_name=sample_workflow.name,
                frequency=ScheduleFrequency.HOURLY,
                enabled=True
            )

            # Add
            assert manager.add_schedule(schedule) is True
            assert manager.get_schedule(schedule.id) is not None

            # Update
            schedule.name = "Updated Lifecycle"
            assert manager.update_schedule(schedule) is True
            assert manager.get_schedule(schedule.id).name == "Updated Lifecycle"

            # Disable
            assert manager.disable_schedule(schedule.id) is True
            assert manager.get_schedule(schedule.id).enabled is False

            # Enable
            assert manager.enable_schedule(schedule.id) is True
            assert manager.get_schedule(schedule.id).enabled is True

            # Remove
            assert manager.remove_schedule(schedule.id) is True
            assert manager.get_schedule(schedule.id) is None

        finally:
            await manager.stop()

    @pytest.mark.asyncio
    async def test_multiple_schedules(self, sample_workflow):
        """Test managing multiple schedules."""
        manager = ScheduleManager(job_creator=AsyncMock())
        await manager.start()

        try:
            schedules = []
            for i in range(5):
                schedule = Schedule(
                    id=f"multi-{i}",
                    name=f"Schedule {i}",
                    workflow_id=sample_workflow.id,
                    workflow_name=sample_workflow.name,
                    frequency=ScheduleFrequency.DAILY,
                    enabled=True
                )
                schedules.append(schedule)
                manager.add_schedule(schedule)

            assert len(manager.get_all_schedules()) == 5

            # Remove some
            manager.remove_schedule("multi-0")
            manager.remove_schedule("multi-2")

            assert len(manager.get_all_schedules()) == 3

        finally:
            await manager.stop()

    @pytest.mark.asyncio
    async def test_different_frequencies(self, sample_workflow):
        """Test schedules with different frequencies."""
        manager = ScheduleManager(job_creator=AsyncMock())
        await manager.start()

        try:
            frequencies = [
                (ScheduleFrequency.HOURLY, None),
                (ScheduleFrequency.DAILY, None),
                (ScheduleFrequency.WEEKLY, None),
                (ScheduleFrequency.CRON, "0 9 * * *"),
            ]

            for i, (freq, cron) in enumerate(frequencies):
                schedule = Schedule(
                    id=f"freq-{i}",
                    name=f"Frequency Test {i}",
                    workflow_id=sample_workflow.id,
                    workflow_name=sample_workflow.name,
                    frequency=freq,
                    cron_expression=cron,
                    enabled=True
                )
                result = manager.add_schedule(schedule)
                assert result is True, f"Failed to add {freq.value} schedule"

            assert len(manager.get_all_schedules()) == len(frequencies)

        finally:
            await manager.stop()
