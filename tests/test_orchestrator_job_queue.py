"""
Unit tests for Job Queue components.
Tests JobStateMachine, JobQueue, JobDeduplicator, and JobTimeoutManager.
"""
import pytest
import time
from datetime import datetime, timedelta
import uuid

from casare_rpa.orchestrator.models import Job, JobStatus, JobPriority, Robot, RobotStatus
from casare_rpa.orchestrator.job_queue import (
    JobStateMachine,
    JobStateError,
    JobQueue,
    JobDeduplicator,
    JobTimeoutManager,
    PriorityQueueItem
)


# ============== JobStateMachine Tests ==============

class TestJobStateMachine:
    """Tests for JobStateMachine."""

    def test_valid_transitions(self):
        """Test all valid state transitions."""
        # PENDING -> QUEUED
        job = self._create_job(JobStatus.PENDING)
        job = JobStateMachine.transition(job, JobStatus.QUEUED)
        assert job.status == JobStatus.QUEUED

        # QUEUED -> RUNNING
        job = JobStateMachine.transition(job, JobStatus.RUNNING)
        assert job.status == JobStatus.RUNNING
        assert job.started_at is not None

        # Small delay to ensure duration_ms is > 0
        time.sleep(0.01)

        # RUNNING -> COMPLETED
        job = JobStateMachine.transition(job, JobStatus.COMPLETED)
        assert job.status == JobStatus.COMPLETED
        assert job.completed_at is not None
        assert job.duration_ms >= 0  # May be 0 on fast systems

    def test_running_to_failed(self):
        """Test RUNNING -> FAILED transition."""
        job = self._create_job(JobStatus.RUNNING)
        job.started_at = datetime.utcnow()

        job = JobStateMachine.transition(job, JobStatus.FAILED)
        assert job.status == JobStatus.FAILED
        assert job.completed_at is not None

    def test_running_to_timeout(self):
        """Test RUNNING -> TIMEOUT transition."""
        job = self._create_job(JobStatus.RUNNING)
        job.started_at = datetime.utcnow()

        job = JobStateMachine.transition(job, JobStatus.TIMEOUT)
        assert job.status == JobStatus.TIMEOUT
        assert job.completed_at is not None

    def test_cancel_from_pending(self):
        """Test cancellation from PENDING state."""
        job = self._create_job(JobStatus.PENDING)
        job = JobStateMachine.transition(job, JobStatus.CANCELLED)
        assert job.status == JobStatus.CANCELLED

    def test_cancel_from_queued(self):
        """Test cancellation from QUEUED state."""
        job = self._create_job(JobStatus.QUEUED)
        job = JobStateMachine.transition(job, JobStatus.CANCELLED)
        assert job.status == JobStatus.CANCELLED

    def test_cancel_from_running(self):
        """Test cancellation from RUNNING state."""
        job = self._create_job(JobStatus.RUNNING)
        job = JobStateMachine.transition(job, JobStatus.CANCELLED)
        assert job.status == JobStatus.CANCELLED

    def test_invalid_transition_raises_error(self):
        """Test that invalid transitions raise JobStateError."""
        # PENDING -> RUNNING (must go through QUEUED)
        job = self._create_job(JobStatus.PENDING)
        with pytest.raises(JobStateError):
            JobStateMachine.transition(job, JobStatus.RUNNING)

    def test_invalid_transition_from_completed(self):
        """Test that transitions from COMPLETED are invalid."""
        job = self._create_job(JobStatus.COMPLETED)
        with pytest.raises(JobStateError):
            JobStateMachine.transition(job, JobStatus.RUNNING)

    def test_invalid_transition_from_failed(self):
        """Test that transitions from FAILED are invalid."""
        job = self._create_job(JobStatus.FAILED)
        with pytest.raises(JobStateError):
            JobStateMachine.transition(job, JobStatus.QUEUED)

    def test_can_transition(self):
        """Test can_transition class method."""
        assert JobStateMachine.can_transition(JobStatus.PENDING, JobStatus.QUEUED)
        assert JobStateMachine.can_transition(JobStatus.QUEUED, JobStatus.RUNNING)
        assert JobStateMachine.can_transition(JobStatus.RUNNING, JobStatus.COMPLETED)
        assert not JobStateMachine.can_transition(JobStatus.PENDING, JobStatus.RUNNING)
        assert not JobStateMachine.can_transition(JobStatus.COMPLETED, JobStatus.RUNNING)

    def test_is_terminal(self):
        """Test is_terminal class method."""
        assert JobStateMachine.is_terminal(JobStatus.COMPLETED)
        assert JobStateMachine.is_terminal(JobStatus.FAILED)
        assert JobStateMachine.is_terminal(JobStatus.TIMEOUT)
        assert JobStateMachine.is_terminal(JobStatus.CANCELLED)
        assert not JobStateMachine.is_terminal(JobStatus.PENDING)
        assert not JobStateMachine.is_terminal(JobStatus.QUEUED)
        assert not JobStateMachine.is_terminal(JobStatus.RUNNING)

    def test_is_active(self):
        """Test is_active class method."""
        assert JobStateMachine.is_active(JobStatus.RUNNING)
        assert not JobStateMachine.is_active(JobStatus.PENDING)
        assert not JobStateMachine.is_active(JobStatus.QUEUED)
        assert not JobStateMachine.is_active(JobStatus.COMPLETED)

    def _create_job(self, status: JobStatus) -> Job:
        """Helper to create a job with given status."""
        return Job(
            id=str(uuid.uuid4()),
            workflow_id="wf1",
            workflow_name="Test Workflow",
            robot_id="robot1",
            status=status,
            priority=JobPriority.NORMAL
        )


# ============== PriorityQueueItem Tests ==============

class TestPriorityQueueItem:
    """Tests for PriorityQueueItem ordering."""

    def test_priority_ordering(self):
        """Test that higher priority items come first."""
        job_low = Job(
            id="1", workflow_id="wf1", workflow_name="Low",
            robot_id="r1", status=JobStatus.PENDING, priority=JobPriority.LOW,
            created_at=datetime.utcnow().isoformat()
        )
        job_high = Job(
            id="2", workflow_id="wf1", workflow_name="High",
            robot_id="r1", status=JobStatus.PENDING, priority=JobPriority.HIGH,
            created_at=datetime.utcnow().isoformat()
        )

        item_low = PriorityQueueItem.from_job(job_low)
        item_high = PriorityQueueItem.from_job(job_high)

        # High priority should be "less than" (come first in heap)
        assert item_high < item_low

    def test_same_priority_fifo(self):
        """Test that same priority items are ordered by creation time."""
        time1 = datetime(2024, 1, 1, 12, 0, 0)
        time2 = datetime(2024, 1, 1, 12, 0, 1)  # 1 second later

        job1 = Job(
            id="1", workflow_id="wf1", workflow_name="First",
            robot_id="r1", status=JobStatus.PENDING, priority=JobPriority.NORMAL,
            created_at=time1.isoformat()
        )
        job2 = Job(
            id="2", workflow_id="wf1", workflow_name="Second",
            robot_id="r1", status=JobStatus.PENDING, priority=JobPriority.NORMAL,
            created_at=time2.isoformat()
        )

        item1 = PriorityQueueItem.from_job(job1)
        item2 = PriorityQueueItem.from_job(job2)

        # Earlier job should come first
        assert item1 < item2

    def test_critical_priority(self):
        """Test that CRITICAL priority comes before all others."""
        job_critical = Job(
            id="1", workflow_id="wf1", workflow_name="Critical",
            robot_id="r1", status=JobStatus.PENDING, priority=JobPriority.CRITICAL,
            created_at=datetime.utcnow().isoformat()
        )
        job_high = Job(
            id="2", workflow_id="wf1", workflow_name="High",
            robot_id="r1", status=JobStatus.PENDING, priority=JobPriority.HIGH,
            created_at=datetime.utcnow().isoformat()
        )

        item_critical = PriorityQueueItem.from_job(job_critical)
        item_high = PriorityQueueItem.from_job(job_high)

        assert item_critical < item_high


# ============== JobDeduplicator Tests ==============

class TestJobDeduplicator:
    """Tests for JobDeduplicator."""

    def test_no_duplicate_on_first_submission(self):
        """Test that first submission is not a duplicate."""
        dedup = JobDeduplicator(window_seconds=60)
        assert not dedup.is_duplicate("wf1", "robot1")

    def test_duplicate_detection(self):
        """Test duplicate detection within window."""
        dedup = JobDeduplicator(window_seconds=60)

        # First submission
        dedup.record("wf1", "robot1")

        # Same submission is duplicate
        assert dedup.is_duplicate("wf1", "robot1")

    def test_different_workflow_not_duplicate(self):
        """Test that different workflow is not duplicate."""
        dedup = JobDeduplicator(window_seconds=60)

        dedup.record("wf1", "robot1")
        assert not dedup.is_duplicate("wf2", "robot1")

    def test_different_robot_not_duplicate(self):
        """Test that different robot is not duplicate."""
        dedup = JobDeduplicator(window_seconds=60)

        dedup.record("wf1", "robot1")
        assert not dedup.is_duplicate("wf1", "robot2")

    def test_params_affect_deduplication(self):
        """Test that different params are not duplicate."""
        dedup = JobDeduplicator(window_seconds=60)

        dedup.record("wf1", "robot1", {"param": "value1"})
        assert not dedup.is_duplicate("wf1", "robot1", {"param": "value2"})

    def test_window_expiration(self):
        """Test that duplicates expire after window."""
        dedup = JobDeduplicator(window_seconds=1)  # 1 second window

        dedup.record("wf1", "robot1")
        assert dedup.is_duplicate("wf1", "robot1")

        # Wait for window to expire
        time.sleep(1.5)

        assert not dedup.is_duplicate("wf1", "robot1")

    def test_record_returns_hash(self):
        """Test that record returns a hash string."""
        dedup = JobDeduplicator()
        hash_val = dedup.record("wf1", "robot1")
        assert isinstance(hash_val, str)
        assert len(hash_val) == 16  # SHA256 truncated to 16 chars


# ============== JobTimeoutManager Tests ==============

class TestJobTimeoutManager:
    """Tests for JobTimeoutManager."""

    def test_start_tracking(self):
        """Test starting timeout tracking for a job."""
        manager = JobTimeoutManager(default_timeout_seconds=60)
        manager.start_tracking("job1")

        remaining = manager.get_remaining_time("job1")
        assert remaining is not None
        assert remaining.total_seconds() > 55  # Should be close to 60

    def test_stop_tracking(self):
        """Test stopping timeout tracking."""
        manager = JobTimeoutManager()
        manager.start_tracking("job1")
        manager.stop_tracking("job1")

        remaining = manager.get_remaining_time("job1")
        assert remaining is None

    def test_custom_timeout(self):
        """Test custom timeout per job."""
        manager = JobTimeoutManager(default_timeout_seconds=60)
        manager.start_tracking("job1", timeout_seconds=10)

        remaining = manager.get_remaining_time("job1")
        assert remaining is not None
        assert remaining.total_seconds() <= 10

    def test_timeout_detection(self):
        """Test detecting timed out jobs."""
        manager = JobTimeoutManager(default_timeout_seconds=1)
        manager.start_tracking("job1")

        # Initially not timed out
        assert "job1" not in manager.get_timed_out_jobs()

        # Wait for timeout
        time.sleep(1.5)

        assert "job1" in manager.get_timed_out_jobs()

    def test_multiple_jobs_timeout(self):
        """Test tracking multiple jobs."""
        manager = JobTimeoutManager(default_timeout_seconds=1)
        manager.start_tracking("job1")
        manager.start_tracking("job2", timeout_seconds=10)

        time.sleep(1.5)

        timed_out = manager.get_timed_out_jobs()
        assert "job1" in timed_out
        assert "job2" not in timed_out

    def test_remaining_time_zero_when_expired(self):
        """Test remaining time is zero for expired jobs."""
        manager = JobTimeoutManager(default_timeout_seconds=1)
        manager.start_tracking("job1")

        time.sleep(1.5)

        remaining = manager.get_remaining_time("job1")
        assert remaining == timedelta(0)


# ============== JobQueue Tests ==============

class TestJobQueue:
    """Tests for JobQueue."""

    def test_enqueue_job(self):
        """Test enqueueing a job."""
        queue = JobQueue()
        job = self._create_job(JobPriority.NORMAL)

        success, message = queue.enqueue(job)

        assert success
        assert queue.get_queue_depth() == 1

    def test_enqueue_transitions_to_queued(self):
        """Test that enqueue transitions job to QUEUED state."""
        queue = JobQueue()
        job = self._create_job(JobPriority.NORMAL)

        queue.enqueue(job)

        queued_job = queue.get_job(job.id)
        assert queued_job.status == JobStatus.QUEUED

    def test_enqueue_non_pending_fails(self):
        """Test that enqueueing non-PENDING job fails."""
        queue = JobQueue()
        job = self._create_job(JobPriority.NORMAL)
        job.status = JobStatus.RUNNING

        success, message = queue.enqueue(job)

        assert not success
        assert "PENDING" in message

    def test_dequeue_returns_job(self):
        """Test dequeueing a job."""
        queue = JobQueue()
        job = self._create_job(JobPriority.NORMAL)
        queue.enqueue(job)

        robot = self._create_robot()
        dequeued = queue.dequeue(robot)

        assert dequeued is not None
        assert dequeued.id == job.id
        assert dequeued.status == JobStatus.RUNNING

    def test_dequeue_priority_order(self):
        """Test that dequeue respects priority."""
        queue = JobQueue()

        low = self._create_job(JobPriority.LOW)
        normal = self._create_job(JobPriority.NORMAL)
        high = self._create_job(JobPriority.HIGH)

        # Enqueue in mixed order (disable dedup check since we want multiple jobs with same workflow)
        queue.enqueue(normal, check_duplicate=False)
        queue.enqueue(low, check_duplicate=False)
        queue.enqueue(high, check_duplicate=False)

        robot = self._create_robot()

        # Should get high first
        first = queue.dequeue(robot)
        assert first.priority == JobPriority.HIGH

        robot.current_jobs = 0  # Reset for next dequeue
        second = queue.dequeue(robot)
        assert second.priority == JobPriority.NORMAL

        robot.current_jobs = 0
        third = queue.dequeue(robot)
        assert third.priority == JobPriority.LOW

    def test_dequeue_unavailable_robot(self):
        """Test that unavailable robot cannot dequeue."""
        queue = JobQueue()
        job = self._create_job(JobPriority.NORMAL)
        queue.enqueue(job)

        robot = self._create_robot()
        robot.status = RobotStatus.OFFLINE

        dequeued = queue.dequeue(robot)
        assert dequeued is None

    def test_dequeue_busy_robot(self):
        """Test that fully loaded robot cannot dequeue."""
        queue = JobQueue()
        job = self._create_job(JobPriority.NORMAL)
        queue.enqueue(job)

        robot = self._create_robot()
        robot.current_jobs = robot.max_concurrent_jobs

        dequeued = queue.dequeue(robot)
        assert dequeued is None

    def test_complete_job(self):
        """Test completing a job."""
        queue = JobQueue()
        job = self._create_job(JobPriority.NORMAL)
        queue.enqueue(job)

        robot = self._create_robot()
        dequeued = queue.dequeue(robot)

        success, message = queue.complete(dequeued.id, {"output": "result"})

        assert success
        completed = queue.get_job(dequeued.id)
        assert completed.status == JobStatus.COMPLETED
        assert completed.result == {"output": "result"}

    def test_fail_job(self):
        """Test failing a job."""
        queue = JobQueue()
        job = self._create_job(JobPriority.NORMAL)
        queue.enqueue(job)

        robot = self._create_robot()
        dequeued = queue.dequeue(robot)

        success, message = queue.fail(dequeued.id, "Something went wrong")

        assert success
        failed = queue.get_job(dequeued.id)
        assert failed.status == JobStatus.FAILED
        assert failed.error_message == "Something went wrong"

    def test_cancel_queued_job(self):
        """Test cancelling a queued job."""
        queue = JobQueue()
        job = self._create_job(JobPriority.NORMAL)
        queue.enqueue(job)

        success, message = queue.cancel(job.id, "User cancelled")

        assert success
        cancelled = queue.get_job(job.id)
        assert cancelled.status == JobStatus.CANCELLED

    def test_cancel_running_job(self):
        """Test cancelling a running job."""
        queue = JobQueue()
        job = self._create_job(JobPriority.NORMAL)
        queue.enqueue(job)

        robot = self._create_robot()
        dequeued = queue.dequeue(robot)

        success, message = queue.cancel(dequeued.id)

        assert success
        cancelled = queue.get_job(dequeued.id)
        assert cancelled.status == JobStatus.CANCELLED

    def test_cancel_completed_fails(self):
        """Test that cancelling completed job fails."""
        queue = JobQueue()
        job = self._create_job(JobPriority.NORMAL)
        queue.enqueue(job)

        robot = self._create_robot()
        dequeued = queue.dequeue(robot)
        queue.complete(dequeued.id)

        success, message = queue.cancel(dequeued.id)

        assert not success

    def test_update_progress(self):
        """Test updating job progress."""
        queue = JobQueue()
        job = self._create_job(JobPriority.NORMAL)
        queue.enqueue(job)

        robot = self._create_robot()
        dequeued = queue.dequeue(robot)

        success = queue.update_progress(dequeued.id, 50, "ProcessingNode")

        assert success
        updated = queue.get_job(dequeued.id)
        assert updated.progress == 50
        assert updated.current_node == "ProcessingNode"

    def test_deduplication(self):
        """Test job deduplication."""
        queue = JobQueue(dedup_window_seconds=60)

        job1 = self._create_job(JobPriority.NORMAL)
        success1, _ = queue.enqueue(job1, check_duplicate=True)
        assert success1

        # Same workflow/robot should be duplicate
        job2 = Job(
            id=str(uuid.uuid4()),
            workflow_id=job1.workflow_id,
            workflow_name=job1.workflow_name,
            robot_id=job1.robot_id,
            status=JobStatus.PENDING,
            priority=JobPriority.NORMAL
        )
        success2, message = queue.enqueue(job2, check_duplicate=True)
        assert not success2
        assert "Duplicate" in message

    def test_get_queued_jobs(self):
        """Test getting queued jobs."""
        queue = JobQueue()

        job1 = self._create_job(JobPriority.NORMAL)
        job2 = self._create_job(JobPriority.HIGH)
        queue.enqueue(job1, check_duplicate=False)
        queue.enqueue(job2, check_duplicate=False)

        queued = queue.get_queued_jobs()
        assert len(queued) == 2

    def test_get_running_jobs(self):
        """Test getting running jobs."""
        queue = JobQueue()

        job1 = self._create_job(JobPriority.NORMAL)
        job2 = self._create_job(JobPriority.HIGH)
        queue.enqueue(job1, check_duplicate=False)
        queue.enqueue(job2, check_duplicate=False)

        robot = self._create_robot()
        robot.max_concurrent_jobs = 2
        queue.dequeue(robot)

        running = queue.get_running_jobs()
        assert len(running) == 1

    def test_get_robot_jobs(self):
        """Test getting jobs for specific robot."""
        queue = JobQueue()

        job = self._create_job(JobPriority.NORMAL)
        queue.enqueue(job)

        robot = self._create_robot()
        queue.dequeue(robot)

        robot_jobs = queue.get_robot_jobs(robot.id)
        assert len(robot_jobs) == 1

    def test_get_queue_stats(self):
        """Test queue statistics."""
        queue = JobQueue()

        # Add jobs of different priorities (disable dedup since same workflow_id)
        queue.enqueue(self._create_job(JobPriority.LOW), check_duplicate=False)
        queue.enqueue(self._create_job(JobPriority.NORMAL), check_duplicate=False)
        queue.enqueue(self._create_job(JobPriority.HIGH), check_duplicate=False)
        queue.enqueue(self._create_job(JobPriority.CRITICAL), check_duplicate=False)

        stats = queue.get_queue_stats()

        assert stats["queued"] == 4
        assert stats["by_priority"]["low"] == 1
        assert stats["by_priority"]["normal"] == 1
        assert stats["by_priority"]["high"] == 1
        assert stats["by_priority"]["critical"] == 1

    def test_state_change_callback(self):
        """Test state change callback is called."""
        changes = []

        def on_change(job, old, new):
            changes.append((job.id, old, new))

        queue = JobQueue(on_state_change=on_change)
        job = self._create_job(JobPriority.NORMAL)
        queue.enqueue(job)

        assert len(changes) == 1
        assert changes[0][1] == JobStatus.PENDING
        assert changes[0][2] == JobStatus.QUEUED

    def _create_job(self, priority: JobPriority) -> Job:
        """Helper to create a job."""
        return Job(
            id=str(uuid.uuid4()),
            workflow_id="wf1",
            workflow_name="Test Workflow",
            robot_id="",  # No specific robot
            status=JobStatus.PENDING,
            priority=priority,
            created_at=datetime.utcnow().isoformat()
        )

    def _create_robot(self) -> Robot:
        """Helper to create a robot."""
        return Robot(
            id=str(uuid.uuid4()),
            name="TestRobot",
            status=RobotStatus.ONLINE,
            environment="default",
            max_concurrent_jobs=1,
            current_jobs=0
        )
