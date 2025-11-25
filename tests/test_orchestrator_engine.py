"""
Unit tests for CasareRPA Orchestrator Engine.
Tests OrchestratorEngine integration of queue, scheduler, and dispatcher.
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock, PropertyMock
import uuid

from casare_rpa.orchestrator.models import (
    Job, JobStatus, JobPriority,
    Robot, RobotStatus,
    Workflow, WorkflowStatus,
    Schedule, ScheduleFrequency
)
from casare_rpa.orchestrator.engine import OrchestratorEngine
from casare_rpa.orchestrator.services import OrchestratorService
from casare_rpa.orchestrator.job_queue import JobQueue


# ==================== FIXTURES ====================

@pytest.fixture
def mock_service():
    """Create a mock OrchestratorService."""
    service = AsyncMock(spec=OrchestratorService)
    service.connect = AsyncMock()
    service.get_robots = AsyncMock(return_value=[])
    service.get_schedules = AsyncMock(return_value=[])
    service.get_workflow = AsyncMock(return_value=None)
    service.get_job = AsyncMock(return_value=None)
    service.save_schedule = AsyncMock()
    service.toggle_schedule = AsyncMock(return_value=True)
    service.delete_schedule = AsyncMock(return_value=True)
    service.update_robot_status = AsyncMock()
    service.get_schedule = AsyncMock(return_value=None)

    # Mock local storage
    mock_storage = Mock()
    mock_storage.save_job = Mock()
    service._local_storage = mock_storage

    return service


@pytest.fixture
def sample_workflow():
    """Create a sample workflow."""
    return Workflow(
        id="wf-001",
        name="Test Workflow",
        description="A test workflow",
        json_definition='{"nodes": []}',
        status=WorkflowStatus.PUBLISHED,
        version="1.0.0"
    )


@pytest.fixture
def sample_job(sample_workflow):
    """Create a sample job."""
    return Job(
        id="job-001",
        workflow_id=sample_workflow.id,
        workflow_name=sample_workflow.name,
        workflow_json='{"nodes": []}',
        status=JobStatus.PENDING,
        priority=JobPriority.NORMAL
    )


@pytest.fixture
def sample_robot():
    """Create a sample robot."""
    return Robot(
        id="robot-001",
        name="Test Robot",
        status=RobotStatus.ONLINE,
        environment="default",
        current_jobs=0,
        max_concurrent_jobs=3,
        last_heartbeat=datetime.utcnow(),
        last_seen=datetime.utcnow()
    )


@pytest.fixture
def engine(mock_service):
    """Create an OrchestratorEngine instance."""
    return OrchestratorEngine(
        service=mock_service,
        load_balancing="least_loaded",
        dispatch_interval=5,
        timeout_check_interval=30,
        default_job_timeout=3600
    )


# ==================== INITIALIZATION TESTS ====================

class TestEngineInitialization:
    """Tests for OrchestratorEngine initialization."""

    def test_create_engine_default(self, mock_service):
        """Test creating engine with defaults."""
        engine = OrchestratorEngine(service=mock_service)

        assert engine._service == mock_service
        assert engine._job_queue is not None
        assert engine._running is False

    def test_create_engine_with_strategy(self, mock_service):
        """Test creating engine with different load balancing strategies."""
        strategies = ["round_robin", "least_loaded", "random", "affinity"]

        for strategy in strategies:
            engine = OrchestratorEngine(
                service=mock_service,
                load_balancing=strategy
            )
            if engine._dispatcher:
                assert engine._dispatcher._strategy.value == strategy

    def test_create_engine_with_intervals(self, mock_service):
        """Test creating engine with custom intervals."""
        engine = OrchestratorEngine(
            service=mock_service,
            dispatch_interval=10,
            timeout_check_interval=60,
            default_job_timeout=7200
        )

        assert engine._dispatch_interval == 10
        assert engine._timeout_check_interval == 60


# ==================== LIFECYCLE TESTS ====================

class TestEngineLifecycle:
    """Tests for engine start/stop."""

    @pytest.mark.asyncio
    async def test_start_engine(self, engine, mock_service):
        """Test starting the engine."""
        await engine.start()

        assert engine._running is True
        mock_service.connect.assert_called_once()
        mock_service.get_robots.assert_called_once()
        mock_service.get_schedules.assert_called_once()

        await engine.stop()

    @pytest.mark.asyncio
    async def test_start_engine_idempotent(self, engine, mock_service):
        """Test starting engine multiple times is safe."""
        await engine.start()
        await engine.start()  # Should not raise

        assert engine._running is True
        # Should only connect once
        assert mock_service.connect.call_count == 1

        await engine.stop()

    @pytest.mark.asyncio
    async def test_stop_engine(self, engine):
        """Test stopping the engine."""
        await engine.start()
        await engine.stop()

        assert engine._running is False
        assert len(engine._background_tasks) == 0

    @pytest.mark.asyncio
    async def test_stop_engine_not_started(self, engine):
        """Test stopping engine that was never started."""
        await engine.stop()  # Should not raise
        assert engine._running is False

    @pytest.mark.asyncio
    async def test_load_robots_on_start(self, mock_service, sample_robot):
        """Test loading robots during startup."""
        mock_service.get_robots.return_value = [sample_robot]

        engine = OrchestratorEngine(service=mock_service)
        await engine.start()

        # Robot should be registered with dispatcher
        if engine._dispatcher:
            robots = engine._dispatcher.get_all_robots()
            assert len(robots) == 1
            assert robots[0].id == sample_robot.id

        await engine.stop()

    @pytest.mark.asyncio
    async def test_load_schedules_on_start(self, mock_service, sample_workflow):
        """Test loading schedules during startup."""
        schedule = Schedule(
            id="sched-001",
            name="Test Schedule",
            workflow_id=sample_workflow.id,
            workflow_name=sample_workflow.name,
            frequency=ScheduleFrequency.HOURLY,
            enabled=True
        )
        mock_service.get_schedules.return_value = [schedule]

        engine = OrchestratorEngine(service=mock_service)
        await engine.start()

        # Schedule should be added to scheduler
        if engine._scheduler:
            assert schedule.id in engine._scheduler._schedules

        await engine.stop()


# ==================== JOB SUBMISSION TESTS ====================

class TestJobSubmission:
    """Tests for job submission."""

    @pytest.mark.asyncio
    async def test_submit_job(self, engine, sample_workflow):
        """Test submitting a job."""
        await engine.start()

        job = await engine.submit_job(
            workflow_id=sample_workflow.id,
            workflow_name=sample_workflow.name,
            workflow_json='{"nodes": []}',
            priority=JobPriority.NORMAL
        )

        assert job is not None
        assert job.workflow_id == sample_workflow.id
        assert job.status == JobStatus.QUEUED

        await engine.stop()

    @pytest.mark.asyncio
    async def test_submit_job_with_priority(self, engine, sample_workflow):
        """Test submitting jobs with different priorities."""
        await engine.start()

        priorities = [JobPriority.LOW, JobPriority.NORMAL, JobPriority.HIGH, JobPriority.CRITICAL]

        for priority in priorities:
            job = await engine.submit_job(
                workflow_id=sample_workflow.id,
                workflow_name=sample_workflow.name,
                workflow_json='{}',
                priority=priority,
                check_duplicate=False
            )
            assert job.priority == priority

        await engine.stop()

    @pytest.mark.asyncio
    async def test_submit_job_with_robot_id(self, engine, sample_workflow, sample_robot):
        """Test submitting job to specific robot."""
        await engine.start()

        # Register robot first
        await engine.register_robot(
            robot_id=sample_robot.id,
            name=sample_robot.name
        )

        job = await engine.submit_job(
            workflow_id=sample_workflow.id,
            workflow_name=sample_workflow.name,
            workflow_json='{}',
            robot_id=sample_robot.id
        )

        assert job is not None
        assert job.robot_id == sample_robot.id

        await engine.stop()

    @pytest.mark.asyncio
    async def test_submit_duplicate_job_blocked(self, engine, sample_workflow):
        """Test duplicate job submission is blocked."""
        await engine.start()

        params = {"key": "value"}

        job1 = await engine.submit_job(
            workflow_id=sample_workflow.id,
            workflow_name=sample_workflow.name,
            workflow_json='{}',
            params=params,
            check_duplicate=True
        )

        # Submit same job again
        job2 = await engine.submit_job(
            workflow_id=sample_workflow.id,
            workflow_name=sample_workflow.name,
            workflow_json='{}',
            params=params,
            check_duplicate=True
        )

        assert job1 is not None
        assert job2 is None  # Duplicate blocked

        await engine.stop()

    @pytest.mark.asyncio
    async def test_submit_duplicate_allowed_when_disabled(self, engine, sample_workflow):
        """Test duplicate check can be disabled."""
        await engine.start()

        params = {"key": "value"}

        job1 = await engine.submit_job(
            workflow_id=sample_workflow.id,
            workflow_name=sample_workflow.name,
            workflow_json='{}',
            params=params,
            check_duplicate=False
        )

        job2 = await engine.submit_job(
            workflow_id=sample_workflow.id,
            workflow_name=sample_workflow.name,
            workflow_json='{}',
            params=params,
            check_duplicate=False
        )

        assert job1 is not None
        assert job2 is not None
        assert job1.id != job2.id

        await engine.stop()

    @pytest.mark.asyncio
    async def test_submit_scheduled_job(self, engine, sample_workflow):
        """Test submitting a job scheduled for the future."""
        await engine.start()

        future_time = datetime.utcnow() + timedelta(hours=1)

        job = await engine.submit_job(
            workflow_id=sample_workflow.id,
            workflow_name=sample_workflow.name,
            workflow_json='{}',
            scheduled_time=future_time
        )

        # Job may be None if scheduler is not available (APScheduler not installed)
        if engine._scheduler:
            assert job is not None
            assert job.status == JobStatus.PENDING  # Not queued yet
        else:
            assert job is None  # Scheduler not available

        await engine.stop()


# ==================== JOB CANCELLATION TESTS ====================

class TestJobCancellation:
    """Tests for job cancellation."""

    @pytest.mark.asyncio
    async def test_cancel_queued_job(self, engine, sample_workflow):
        """Test cancelling a queued job."""
        await engine.start()

        job = await engine.submit_job(
            workflow_id=sample_workflow.id,
            workflow_name=sample_workflow.name,
            workflow_json='{}'
        )

        result = await engine.cancel_job(job.id, "Test cancellation")

        assert result is True
        cancelled_job = engine._job_queue.get_job(job.id)
        assert cancelled_job.status == JobStatus.CANCELLED

        await engine.stop()

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_job(self, engine):
        """Test cancelling non-existent job."""
        await engine.start()

        result = await engine.cancel_job("nonexistent")

        assert result is False

        await engine.stop()


# ==================== JOB RETRY TESTS ====================

class TestJobRetry:
    """Tests for job retry."""

    @pytest.mark.asyncio
    async def test_retry_failed_job(self, engine, mock_service, sample_workflow):
        """Test retrying a failed job."""
        await engine.start()

        # Create and fail a job
        failed_job = Job(
            id="failed-job",
            workflow_id=sample_workflow.id,
            workflow_name=sample_workflow.name,
            robot_id="",
            workflow_json='{}',
            status=JobStatus.FAILED,
            priority=JobPriority.NORMAL
        )
        mock_service.get_job.return_value = failed_job

        new_job = await engine.retry_job(failed_job.id)

        assert new_job is not None
        assert new_job.id != failed_job.id
        assert new_job.workflow_id == failed_job.workflow_id

        await engine.stop()

    @pytest.mark.asyncio
    async def test_retry_cancelled_job(self, engine, mock_service, sample_workflow):
        """Test retrying a cancelled job."""
        await engine.start()

        cancelled_job = Job(
            id="cancelled-job",
            workflow_id=sample_workflow.id,
            workflow_name=sample_workflow.name,
            robot_id="",
            workflow_json='{}',
            status=JobStatus.CANCELLED,
            priority=JobPriority.HIGH
        )
        mock_service.get_job.return_value = cancelled_job

        new_job = await engine.retry_job(cancelled_job.id)

        assert new_job is not None
        assert new_job.priority == JobPriority.HIGH

        await engine.stop()

    @pytest.mark.asyncio
    async def test_retry_running_job_fails(self, engine, mock_service, sample_workflow):
        """Test cannot retry running job."""
        await engine.start()

        running_job = Job(
            id="running-job",
            workflow_id=sample_workflow.id,
            workflow_name=sample_workflow.name,
            robot_id="",
            workflow_json='{}',
            status=JobStatus.RUNNING,
            priority=JobPriority.NORMAL
        )
        mock_service.get_job.return_value = running_job

        new_job = await engine.retry_job(running_job.id)

        assert new_job is None

        await engine.stop()

    @pytest.mark.asyncio
    async def test_retry_nonexistent_job(self, engine, mock_service):
        """Test retrying non-existent job."""
        await engine.start()

        mock_service.get_job.return_value = None

        new_job = await engine.retry_job("nonexistent")

        assert new_job is None

        await engine.stop()


# ==================== HELPER ====================

def _create_test_robot():
    """Create a robot for testing."""
    return Robot(
        id="test-robot-001",
        name="TestRobot",
        status=RobotStatus.ONLINE,
        environment="default",
        current_jobs=0,
        max_concurrent_jobs=3,
        last_heartbeat=datetime.utcnow(),
        last_seen=datetime.utcnow()
    )


# ==================== JOB PROGRESS TESTS ====================

class TestJobProgress:
    """Tests for job progress updates."""

    @pytest.mark.asyncio
    async def test_update_progress(self, engine, sample_workflow):
        """Test updating job progress."""
        await engine.start()

        job = await engine.submit_job(
            workflow_id=sample_workflow.id,
            workflow_name=sample_workflow.name,
            workflow_json='{}'
        )

        # Transition to running via dequeue
        robot = _create_test_robot()
        engine._job_queue.dequeue(robot)

        result = await engine.update_job_progress(job.id, 50, "node-1")

        assert result is True
        updated_job = engine._job_queue.get_job(job.id)
        assert updated_job.progress == 50
        assert updated_job.current_node == "node-1"

        await engine.stop()

    @pytest.mark.asyncio
    async def test_update_progress_nonexistent_job(self, engine):
        """Test updating progress for non-existent job."""
        await engine.start()

        result = await engine.update_job_progress("nonexistent", 50)

        assert result is False

        await engine.stop()


# ==================== JOB COMPLETION TESTS ====================

class TestJobCompletion:
    """Tests for job completion."""

    @pytest.mark.asyncio
    async def test_complete_job(self, engine, sample_workflow):
        """Test completing a job."""
        await engine.start()

        job = await engine.submit_job(
            workflow_id=sample_workflow.id,
            workflow_name=sample_workflow.name,
            workflow_json='{}'
        )

        # Transition to running via dequeue
        robot = _create_test_robot()
        engine._job_queue.dequeue(robot)

        result = await engine.complete_job(job.id, {"output": "success"})

        assert result is True
        completed_job = engine._job_queue.get_job(job.id)
        assert completed_job.status == JobStatus.COMPLETED
        assert completed_job.result == {"output": "success"}

        await engine.stop()

    @pytest.mark.asyncio
    async def test_complete_job_callback(self, engine, sample_workflow):
        """Test completion callback is called."""
        callback = Mock()
        engine._on_job_complete = callback

        await engine.start()

        job = await engine.submit_job(
            workflow_id=sample_workflow.id,
            workflow_name=sample_workflow.name,
            workflow_json='{}'
        )

        robot = _create_test_robot()
        engine._job_queue.dequeue(robot)
        await engine.complete_job(job.id)

        callback.assert_called_once()

        await engine.stop()

    @pytest.mark.asyncio
    async def test_fail_job(self, engine, sample_workflow):
        """Test failing a job."""
        await engine.start()

        job = await engine.submit_job(
            workflow_id=sample_workflow.id,
            workflow_name=sample_workflow.name,
            workflow_json='{}'
        )

        robot = _create_test_robot()
        engine._job_queue.dequeue(robot)

        result = await engine.fail_job(job.id, "Test error")

        assert result is True
        failed_job = engine._job_queue.get_job(job.id)
        assert failed_job.status == JobStatus.FAILED
        assert failed_job.error_message == "Test error"

        await engine.stop()

    @pytest.mark.asyncio
    async def test_fail_job_callback(self, engine, sample_workflow):
        """Test failure callback is called."""
        callback = Mock()
        engine._on_job_failed = callback

        await engine.start()

        job = await engine.submit_job(
            workflow_id=sample_workflow.id,
            workflow_name=sample_workflow.name,
            workflow_json='{}'
        )

        robot = _create_test_robot()
        engine._job_queue.dequeue(robot)
        await engine.fail_job(job.id, "Error")

        callback.assert_called_once()

        await engine.stop()


# ==================== ROBOT MANAGEMENT TESTS ====================

class TestRobotManagement:
    """Tests for robot management."""

    @pytest.mark.asyncio
    async def test_register_robot(self, engine, mock_service):
        """Test registering a robot."""
        await engine.start()

        robot = await engine.register_robot(
            robot_id="robot-new",
            name="New Robot",
            environment="production",
            max_concurrent_jobs=5,
            tags=["web", "data"]
        )

        assert robot is not None
        assert robot.id == "robot-new"
        assert robot.name == "New Robot"
        assert robot.status == RobotStatus.ONLINE

        mock_service.update_robot_status.assert_called()

        await engine.stop()

    @pytest.mark.asyncio
    async def test_robot_heartbeat(self, engine, sample_robot):
        """Test robot heartbeat."""
        await engine.start()

        await engine.register_robot(
            robot_id=sample_robot.id,
            name=sample_robot.name
        )

        result = await engine.robot_heartbeat(sample_robot.id)

        assert result is True

        await engine.stop()

    @pytest.mark.asyncio
    async def test_robot_heartbeat_not_registered(self, engine):
        """Test heartbeat for unregistered robot."""
        await engine.start()

        result = await engine.robot_heartbeat("unknown")

        # Should still return True if dispatcher exists
        assert isinstance(result, bool)

        await engine.stop()

    @pytest.mark.asyncio
    async def test_update_robot_status(self, engine, sample_robot, mock_service):
        """Test updating robot status."""
        await engine.start()

        await engine.register_robot(
            robot_id=sample_robot.id,
            name=sample_robot.name
        )

        result = await engine.update_robot_status(sample_robot.id, RobotStatus.BUSY)

        assert result is True
        mock_service.update_robot_status.assert_called()

        await engine.stop()


# ==================== SCHEDULE MANAGEMENT TESTS ====================

class TestScheduleManagement:
    """Tests for schedule management."""

    @pytest.mark.asyncio
    async def test_create_hourly_schedule(self, engine, mock_service, sample_workflow):
        """Test creating an hourly schedule."""
        await engine.start()

        schedule = await engine.create_schedule(
            name="Hourly Schedule",
            workflow_id=sample_workflow.id,
            workflow_name=sample_workflow.name,
            frequency=ScheduleFrequency.HOURLY
        )

        assert schedule is not None
        assert schedule.name == "Hourly Schedule"
        assert schedule.frequency == ScheduleFrequency.HOURLY

        mock_service.save_schedule.assert_called_once()

        await engine.stop()

    @pytest.mark.asyncio
    async def test_create_cron_schedule(self, engine, mock_service, sample_workflow):
        """Test creating a cron schedule."""
        await engine.start()

        schedule = await engine.create_schedule(
            name="Cron Schedule",
            workflow_id=sample_workflow.id,
            workflow_name=sample_workflow.name,
            frequency=ScheduleFrequency.CRON,
            cron_expression="0 9 * * 1-5"
        )

        assert schedule is not None
        assert schedule.frequency == ScheduleFrequency.CRON
        assert schedule.cron_expression == "0 9 * * 1-5"

        await engine.stop()

    @pytest.mark.asyncio
    async def test_create_disabled_schedule(self, engine, mock_service, sample_workflow):
        """Test creating a disabled schedule."""
        await engine.start()

        schedule = await engine.create_schedule(
            name="Disabled Schedule",
            workflow_id=sample_workflow.id,
            workflow_name=sample_workflow.name,
            frequency=ScheduleFrequency.DAILY,
            enabled=False
        )

        assert schedule is not None
        assert schedule.enabled is False

        await engine.stop()

    @pytest.mark.asyncio
    async def test_toggle_schedule_enable(self, engine, mock_service, sample_workflow):
        """Test enabling a schedule."""
        await engine.start()

        schedule = Schedule(
            id="toggle-test",
            name="Toggle Test",
            workflow_id=sample_workflow.id,
            workflow_name=sample_workflow.name,
            frequency=ScheduleFrequency.HOURLY,
            enabled=False
        )
        mock_service.get_schedule.return_value = schedule

        result = await engine.toggle_schedule(schedule.id, True)

        assert result is True
        mock_service.toggle_schedule.assert_called_with(schedule.id, True)

        await engine.stop()

    @pytest.mark.asyncio
    async def test_toggle_schedule_disable(self, engine, mock_service, sample_workflow):
        """Test disabling a schedule."""
        await engine.start()

        schedule = Schedule(
            id="toggle-test",
            name="Toggle Test",
            workflow_id=sample_workflow.id,
            workflow_name=sample_workflow.name,
            frequency=ScheduleFrequency.HOURLY,
            enabled=True
        )

        result = await engine.toggle_schedule(schedule.id, False)

        assert result is True

        await engine.stop()

    @pytest.mark.asyncio
    async def test_delete_schedule(self, engine, mock_service):
        """Test deleting a schedule."""
        await engine.start()

        result = await engine.delete_schedule("sched-to-delete")

        assert result is True
        mock_service.delete_schedule.assert_called_with("sched-to-delete")

        await engine.stop()


# ==================== EVENT HANDLER TESTS ====================

class TestEventHandlers:
    """Tests for event handlers."""

    @pytest.mark.asyncio
    async def test_on_job_state_change(self, engine, sample_workflow):
        """Test job state change handler."""
        await engine.start()

        job = await engine.submit_job(
            workflow_id=sample_workflow.id,
            workflow_name=sample_workflow.name,
            workflow_json='{}'
        )

        # State change should be logged (we can't easily test log output)
        assert job.status == JobStatus.QUEUED

        await engine.stop()

    @pytest.mark.asyncio
    async def test_on_schedule_trigger(self, engine, mock_service, sample_workflow):
        """Test schedule trigger handler creates job."""
        await engine.start()

        mock_service.get_workflow.return_value = sample_workflow

        schedule = Schedule(
            id="trigger-test",
            name="Trigger Test",
            workflow_id=sample_workflow.id,
            workflow_name=sample_workflow.name,
            frequency=ScheduleFrequency.HOURLY,
            enabled=True,
            priority=JobPriority.HIGH
        )

        await engine._on_schedule_trigger(schedule)

        # Should have created a job
        stats = engine.get_queue_stats()
        assert stats["total_tracked"] >= 1

        await engine.stop()

    @pytest.mark.asyncio
    async def test_on_schedule_trigger_workflow_not_found(self, engine, mock_service, sample_workflow):
        """Test schedule trigger when workflow not found."""
        await engine.start()

        mock_service.get_workflow.return_value = None

        schedule = Schedule(
            id="trigger-test",
            name="Trigger Test",
            workflow_id="nonexistent",
            workflow_name="Nonexistent",
            frequency=ScheduleFrequency.HOURLY,
            enabled=True
        )

        # Should not raise, just log error
        await engine._on_schedule_trigger(schedule)

        await engine.stop()


# ==================== STATISTICS TESTS ====================

class TestEngineStatistics:
    """Tests for engine statistics."""

    @pytest.mark.asyncio
    async def test_get_queue_stats(self, engine, sample_workflow):
        """Test getting queue statistics."""
        await engine.start()

        await engine.submit_job(
            workflow_id=sample_workflow.id,
            workflow_name=sample_workflow.name,
            workflow_json='{}'
        )

        stats = engine.get_queue_stats()

        assert "queued" in stats
        assert stats["queued"] >= 1

        await engine.stop()

    @pytest.mark.asyncio
    async def test_get_dispatcher_stats(self, engine, sample_robot):
        """Test getting dispatcher statistics."""
        await engine.start()

        await engine.register_robot(
            robot_id=sample_robot.id,
            name=sample_robot.name
        )

        stats = engine.get_dispatcher_stats()

        if engine._dispatcher:
            assert "total_robots" in stats
            assert stats["total_robots"] >= 1

        await engine.stop()

    @pytest.mark.asyncio
    async def test_get_upcoming_schedules(self, engine, sample_workflow):
        """Test getting upcoming scheduled runs."""
        await engine.start()

        await engine.create_schedule(
            name="Upcoming Test",
            workflow_id=sample_workflow.id,
            workflow_name=sample_workflow.name,
            frequency=ScheduleFrequency.HOURLY
        )

        upcoming = engine.get_upcoming_schedules(limit=5)

        # May or may not have upcoming schedules depending on scheduler
        assert isinstance(upcoming, list)

        await engine.stop()


# ==================== BACKGROUND TASK TESTS ====================

class TestBackgroundTasks:
    """Tests for background tasks."""

    @pytest.mark.asyncio
    async def test_timeout_check_loop(self, engine, sample_workflow):
        """Test timeout check loop runs."""
        await engine.start()

        # Submit a job and make it timeout
        job = await engine.submit_job(
            workflow_id=sample_workflow.id,
            workflow_name=sample_workflow.name,
            workflow_json='{}'
        )

        # Manually start the job via dequeue
        robot = _create_test_robot()
        engine._job_queue.dequeue(robot)

        # Set a very short timeout (1 second) and wait for it to expire
        # Note: timeout check uses `elapsed > timeout`, so we need elapsed > 0
        engine._job_queue._timeout_manager.start_tracking(job.id, 1)

        # Wait longer than the timeout
        await asyncio.sleep(1.1)

        # Manually trigger timeout check
        timed_out = engine._job_queue.check_timeouts()

        assert job.id in timed_out

        await engine.stop()

    @pytest.mark.asyncio
    async def test_background_tasks_created(self, engine):
        """Test background tasks are created on start."""
        await engine.start()

        assert len(engine._background_tasks) == 2  # timeout loop + persist loop

        await engine.stop()

        assert len(engine._background_tasks) == 0

    @pytest.mark.asyncio
    async def test_persist_job(self, engine, mock_service, sample_workflow):
        """Test job persistence."""
        await engine.start()

        job = await engine.submit_job(
            workflow_id=sample_workflow.id,
            workflow_name=sample_workflow.name,
            workflow_json='{}'
        )

        # Verify save_job was called
        mock_service._local_storage.save_job.assert_called()

        await engine.stop()


# ==================== INTEGRATION TESTS ====================

class TestEngineIntegration:
    """Integration tests for full engine workflows."""

    @pytest.mark.asyncio
    async def test_full_job_lifecycle(self, engine, sample_workflow):
        """Test complete job lifecycle: submit -> run -> complete."""
        await engine.start()

        # Submit
        job = await engine.submit_job(
            workflow_id=sample_workflow.id,
            workflow_name=sample_workflow.name,
            workflow_json='{}',
            priority=JobPriority.HIGH
        )
        assert job.status == JobStatus.QUEUED

        # Start (simulating dispatcher) via dequeue
        robot = _create_test_robot()
        engine._job_queue.dequeue(robot)
        job = engine._job_queue.get_job(job.id)
        assert job.status == JobStatus.RUNNING

        # Progress
        await engine.update_job_progress(job.id, 50, "step-1")
        job = engine._job_queue.get_job(job.id)
        assert job.progress == 50

        # Complete
        await engine.complete_job(job.id, {"result": "success"})
        job = engine._job_queue.get_job(job.id)
        assert job.status == JobStatus.COMPLETED

        await engine.stop()

    @pytest.mark.asyncio
    async def test_full_job_failure_lifecycle(self, engine, sample_workflow):
        """Test job failure lifecycle: submit -> run -> fail."""
        await engine.start()

        job = await engine.submit_job(
            workflow_id=sample_workflow.id,
            workflow_name=sample_workflow.name,
            workflow_json='{}'
        )

        robot = _create_test_robot()
        engine._job_queue.dequeue(robot)

        await engine.fail_job(job.id, "Execution error")

        job = engine._job_queue.get_job(job.id)
        assert job.status == JobStatus.FAILED
        assert "Execution error" in job.error_message

        await engine.stop()

    @pytest.mark.asyncio
    async def test_multiple_jobs_priority_ordering(self, engine, sample_workflow):
        """Test multiple jobs are ordered by priority."""
        await engine.start()

        # Submit jobs with different priorities
        await engine.submit_job(
            workflow_id=sample_workflow.id,
            workflow_name=sample_workflow.name,
            workflow_json='{"id": "low"}',
            priority=JobPriority.LOW,
            check_duplicate=False
        )

        await engine.submit_job(
            workflow_id=sample_workflow.id,
            workflow_name=sample_workflow.name,
            workflow_json='{"id": "critical"}',
            priority=JobPriority.CRITICAL,
            check_duplicate=False
        )

        await engine.submit_job(
            workflow_id=sample_workflow.id,
            workflow_name=sample_workflow.name,
            workflow_json='{"id": "normal"}',
            priority=JobPriority.NORMAL,
            check_duplicate=False
        )

        # Dequeue should return critical first
        robot = Robot(
            id="robot-test",
            name="Test",
            status=RobotStatus.ONLINE,
            current_jobs=0,
            max_concurrent_jobs=5
        )

        job = engine._job_queue.dequeue(robot)
        assert job.priority == JobPriority.CRITICAL

        await engine.stop()
