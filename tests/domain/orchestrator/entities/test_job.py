"""Tests for Job domain entity."""

import pytest
from datetime import datetime


class TestJobEntity:
    """Test Job entity behavior and invariants."""

    def test_job_creation_with_required_fields(self):
        """Job can be created with minimal required fields."""
        from casare_rpa.domain.orchestrator.entities import Job, JobStatus

        job = Job(
            id="job1",
            workflow_id="wf1",
            workflow_name="Test Workflow",
            robot_id="robot1",
        )

        assert job.id == "job1"
        assert job.workflow_id == "wf1"
        assert job.robot_id == "robot1"
        assert job.status == JobStatus.PENDING  # Default

    def test_job_is_terminal_when_completed(self):
        """Job is terminal when in COMPLETED status."""
        from casare_rpa.domain.orchestrator.entities import Job, JobStatus

        job = Job(
            id="job1",
            workflow_id="wf1",
            workflow_name="Test",
            robot_id="robot1",
            status=JobStatus.COMPLETED,
        )

        assert job.is_terminal() is True

    def test_job_is_terminal_when_failed(self):
        """Job is terminal when in FAILED status."""
        from casare_rpa.domain.orchestrator.entities import Job, JobStatus

        job = Job(
            id="job1",
            workflow_id="wf1",
            workflow_name="Test",
            robot_id="robot1",
            status=JobStatus.FAILED,
        )

        assert job.is_terminal() is True

    def test_job_is_not_terminal_when_running(self):
        """Job is not terminal when running."""
        from casare_rpa.domain.orchestrator.entities import Job, JobStatus

        job = Job(
            id="job1",
            workflow_id="wf1",
            workflow_name="Test",
            robot_id="robot1",
            status=JobStatus.RUNNING,
        )

        assert job.is_terminal() is False

    def test_job_can_transition_from_pending_to_queued(self):
        """Job can transition from PENDING to QUEUED."""
        from casare_rpa.domain.orchestrator.entities import Job, JobStatus

        job = Job(
            id="job1",
            workflow_id="wf1",
            workflow_name="Test",
            robot_id="robot1",
            status=JobStatus.PENDING,
        )

        assert job.can_transition_to(JobStatus.QUEUED) is True

    def test_job_cannot_transition_from_completed_to_running(self):
        """Job cannot transition from terminal status."""
        from casare_rpa.domain.orchestrator.entities import Job, JobStatus

        job = Job(
            id="job1",
            workflow_id="wf1",
            workflow_name="Test",
            robot_id="robot1",
            status=JobStatus.COMPLETED,
        )

        assert job.can_transition_to(JobStatus.RUNNING) is False

    def test_job_transition_updates_status(self):
        """Job transition updates status when valid."""
        from casare_rpa.domain.orchestrator.entities import Job, JobStatus

        job = Job(
            id="job1",
            workflow_id="wf1",
            workflow_name="Test",
            robot_id="robot1",
            status=JobStatus.PENDING,
        )

        job.transition_to(JobStatus.QUEUED)

        assert job.status == JobStatus.QUEUED

    def test_job_transition_raises_error_on_invalid_transition(self):
        """Job raises error on invalid transition."""
        from casare_rpa.domain.orchestrator.entities import Job, JobStatus
        from casare_rpa.domain.orchestrator.errors import JobTransitionError

        job = Job(
            id="job1",
            workflow_id="wf1",
            workflow_name="Test",
            robot_id="robot1",
            status=JobStatus.COMPLETED,
        )

        with pytest.raises(JobTransitionError):
            job.transition_to(JobStatus.RUNNING)
