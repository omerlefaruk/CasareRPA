"""Tests for Execute Job use case."""

import pytest
from unittest.mock import AsyncMock

from casare_rpa.application.orchestrator.use_cases import ExecuteJobUseCase
from casare_rpa.domain.orchestrator.entities import Job, JobStatus, Robot, RobotStatus
from casare_rpa.domain.orchestrator.errors import JobTransitionError


class TestExecuteJobUseCase:
    """Test ExecuteJobUseCase."""

    @pytest.mark.asyncio
    async def test_execute_job_success(self):
        """Execute job transitions to RUNNING when robot available."""
        # Arrange
        job_repo = AsyncMock()
        robot_repo = AsyncMock()

        job = Job(
            id="job1",
            workflow_id="wf1",
            workflow_name="Test",
            robot_id="robot1",
            status=JobStatus.QUEUED,
        )
        robot = Robot(
            id="robot1",
            name="Test Robot",
            status=RobotStatus.ONLINE,
            max_concurrent_jobs=3,
            current_job_ids=[],
        )

        job_repo.get_by_id.return_value = job
        robot_repo.get_by_id.return_value = robot

        use_case = ExecuteJobUseCase(job_repo, robot_repo)

        # Act
        result = await use_case.execute("job1")

        # Assert
        assert result.status == JobStatus.RUNNING
        assert robot.current_jobs == 1
        job_repo.save.assert_called_once_with(job)
        robot_repo.save.assert_called_once_with(robot)

    @pytest.mark.asyncio
    async def test_execute_job_not_found(self):
        """Execute raises ValueError when job not found."""
        # Arrange
        job_repo = AsyncMock()
        robot_repo = AsyncMock()
        job_repo.get_by_id.return_value = None

        use_case = ExecuteJobUseCase(job_repo, robot_repo)

        # Act & Assert
        with pytest.raises(ValueError, match="Job job1 not found"):
            await use_case.execute("job1")

    @pytest.mark.asyncio
    async def test_execute_job_robot_not_found(self):
        """Execute raises ValueError when robot not found."""
        # Arrange
        job_repo = AsyncMock()
        robot_repo = AsyncMock()

        job = Job(
            id="job1",
            workflow_id="wf1",
            workflow_name="Test",
            robot_id="robot1",
            status=JobStatus.QUEUED,
        )
        job_repo.get_by_id.return_value = job
        robot_repo.get_by_id.return_value = None

        use_case = ExecuteJobUseCase(job_repo, robot_repo)

        # Act & Assert
        with pytest.raises(ValueError, match="Robot robot1 not found"):
            await use_case.execute("job1")

    @pytest.mark.asyncio
    async def test_execute_job_robot_unavailable(self):
        """Execute raises ValueError when robot unavailable."""
        # Arrange
        job_repo = AsyncMock()
        robot_repo = AsyncMock()

        job = Job(
            id="job1",
            workflow_id="wf1",
            workflow_name="Test",
            robot_id="robot1",
            status=JobStatus.QUEUED,
        )
        robot = Robot(
            id="robot1",
            name="Test",
            status=RobotStatus.OFFLINE,  # Offline
        )

        job_repo.get_by_id.return_value = job
        robot_repo.get_by_id.return_value = robot

        use_case = ExecuteJobUseCase(job_repo, robot_repo)

        # Act & Assert
        with pytest.raises(ValueError, match="Robot robot1 is not available"):
            await use_case.execute("job1")

    @pytest.mark.asyncio
    async def test_execute_job_invalid_transition(self):
        """Execute raises JobTransitionError for invalid state transition."""
        # Arrange
        job_repo = AsyncMock()
        robot_repo = AsyncMock()

        job = Job(
            id="job1",
            workflow_id="wf1",
            workflow_name="Test",
            robot_id="robot1",
            status=JobStatus.COMPLETED,  # Terminal state
        )
        robot = Robot(id="robot1", name="Test", status=RobotStatus.ONLINE)

        job_repo.get_by_id.return_value = job
        robot_repo.get_by_id.return_value = robot

        use_case = ExecuteJobUseCase(job_repo, robot_repo)

        # Act & Assert
        with pytest.raises(JobTransitionError):
            await use_case.execute("job1")
