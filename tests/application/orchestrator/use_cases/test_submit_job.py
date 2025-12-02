"""Tests for SubmitJobUseCase.

Tests the job submission orchestration logic with:
- Mock infrastructure (repositories, dispatcher)
- Real domain objects (Job, Robot, RobotAssignment)
- Three-scenario pattern: SUCCESS, ERROR, EDGE_CASES
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

from casare_rpa.application.orchestrator.use_cases.submit_job import SubmitJobUseCase
from casare_rpa.domain.orchestrator.entities.job import Job, JobStatus, JobPriority
from casare_rpa.domain.orchestrator.entities.robot import (
    Robot,
    RobotStatus,
    RobotCapability,
)
from casare_rpa.domain.orchestrator.errors import (
    NoAvailableRobotError,
    RobotNotFoundError,
)
from casare_rpa.domain.orchestrator.services.robot_selection_service import (
    RobotSelectionService,
)

from .conftest import create_robot, create_assignment


class TestSubmitJobSuccess:
    """Happy path tests for SubmitJobUseCase."""

    @pytest.mark.asyncio
    async def test_submit_job_with_explicit_robot(
        self,
        mock_job_repository: AsyncMock,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
        robot_selection_service: RobotSelectionService,
        mock_dispatcher: Mock,
        available_robot: Robot,
        sample_workflow_data: dict,
    ) -> None:
        """Submit job with explicitly specified robot - robot used directly."""
        # Arrange: Robot exists and is available
        mock_robot_repository.get_by_id.return_value = available_robot
        mock_robot_repository.get_all.return_value = [available_robot]

        use_case = SubmitJobUseCase(
            job_repository=mock_job_repository,
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
            robot_selection_service=robot_selection_service,
            dispatcher=mock_dispatcher,
        )

        # Act
        job = await use_case.execute(
            workflow_id="workflow-1",
            workflow_data=sample_workflow_data,
            robot_id=available_robot.id,
            priority=JobPriority.HIGH,
            variables={"test_var": "value"},
        )

        # Assert
        assert job is not None
        assert job.workflow_id == "workflow-1"
        assert job.robot_id == available_robot.id
        assert job.robot_name == available_robot.name
        assert job.priority == JobPriority.HIGH
        assert job.status in (JobStatus.PENDING, JobStatus.QUEUED)

        # Verify job was saved
        mock_job_repository.save.assert_awaited()

    @pytest.mark.asyncio
    async def test_submit_job_with_auto_selection(
        self,
        mock_job_repository: AsyncMock,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
        robot_selection_service: RobotSelectionService,
        mock_dispatcher: Mock,
        sample_workflow_data: dict,
    ) -> None:
        """Submit job without specifying robot - auto-selects least loaded."""
        # Arrange: Multiple available robots with browser capability (required by workflow)
        robots = [
            create_robot(
                robot_id="robot-1",
                name="Robot 1",
                current_job_ids=["job-a", "job-b"],  # 2 jobs
                max_concurrent_jobs=5,
                capabilities={RobotCapability.BROWSER},
            ),
            create_robot(
                robot_id="robot-2",
                name="Robot 2",
                current_job_ids=[],  # 0 jobs - should be selected
                max_concurrent_jobs=5,
                capabilities={RobotCapability.BROWSER},
            ),
        ]
        mock_robot_repository.get_all.return_value = robots
        mock_robot_repository.get_by_id.side_effect = lambda rid: next(
            (r for r in robots if r.id == rid), None
        )

        use_case = SubmitJobUseCase(
            job_repository=mock_job_repository,
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
            robot_selection_service=robot_selection_service,
            dispatcher=mock_dispatcher,
        )

        # Act
        job = await use_case.execute(
            workflow_id="workflow-1",
            workflow_data=sample_workflow_data,
        )

        # Assert: Should select robot-2 (least loaded)
        assert job.robot_id == "robot-2"
        mock_job_repository.save.assert_awaited()

    @pytest.mark.asyncio
    async def test_submit_job_respects_workflow_assignment(
        self,
        mock_job_repository: AsyncMock,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
        robot_selection_service: RobotSelectionService,
        mock_dispatcher: Mock,
        sample_workflow_data: dict,
    ) -> None:
        """Submit job uses assigned robot when no robot_id specified."""
        # Arrange: Workflow has assigned robot with browser capability (required by workflow)
        assigned_robot = create_robot(
            robot_id="assigned-robot",
            name="Assigned Robot",
            capabilities={RobotCapability.BROWSER},
        )
        other_robot = create_robot(
            robot_id="other-robot",
            name="Other Robot",
            current_job_ids=[],
            capabilities={RobotCapability.BROWSER},
        )

        assignment = create_assignment(
            workflow_id="workflow-1", robot_id="assigned-robot"
        )

        mock_robot_repository.get_all.return_value = [assigned_robot, other_robot]
        mock_robot_repository.get_by_id.side_effect = lambda rid: (
            assigned_robot if rid == "assigned-robot" else other_robot
        )
        mock_assignment_repository.get_by_workflow.return_value = [assignment]

        use_case = SubmitJobUseCase(
            job_repository=mock_job_repository,
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
            robot_selection_service=robot_selection_service,
            dispatcher=mock_dispatcher,
        )

        # Act
        job = await use_case.execute(
            workflow_id="workflow-1",
            workflow_data=sample_workflow_data,
        )

        # Assert: Should use assigned robot
        assert job.robot_id == "assigned-robot"

    @pytest.mark.asyncio
    async def test_submit_job_with_variables_injection(
        self,
        mock_job_repository: AsyncMock,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
        robot_selection_service: RobotSelectionService,
        mock_dispatcher: Mock,
        available_robot: Robot,
        sample_workflow_data: dict,
    ) -> None:
        """Submit job with variables - variables injected into workflow JSON."""
        # Arrange
        mock_robot_repository.get_by_id.return_value = available_robot
        mock_robot_repository.get_all.return_value = [available_robot]

        use_case = SubmitJobUseCase(
            job_repository=mock_job_repository,
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
            robot_selection_service=robot_selection_service,
            dispatcher=mock_dispatcher,
        )

        # Act
        job = await use_case.execute(
            workflow_id="workflow-1",
            workflow_data=sample_workflow_data,
            robot_id=available_robot.id,
            variables={"input_url": "https://example.com", "timeout": 30},
        )

        # Assert: Variables should be in workflow JSON
        import orjson

        workflow_json = orjson.loads(job.workflow_json)
        assert workflow_json["variables"]["input_url"] == "https://example.com"
        assert workflow_json["variables"]["timeout"] == 30

    @pytest.mark.asyncio
    async def test_submit_job_with_scheduled_time(
        self,
        mock_job_repository: AsyncMock,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
        robot_selection_service: RobotSelectionService,
        mock_dispatcher: Mock,
        available_robot: Robot,
        sample_workflow_data: dict,
    ) -> None:
        """Submit job with scheduled time - job scheduled for future execution."""
        # Arrange
        mock_robot_repository.get_by_id.return_value = available_robot
        mock_robot_repository.get_all.return_value = [available_robot]
        scheduled = datetime(2025, 12, 31, 12, 0, 0)

        use_case = SubmitJobUseCase(
            job_repository=mock_job_repository,
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
            robot_selection_service=robot_selection_service,
            dispatcher=mock_dispatcher,
        )

        # Act
        job = await use_case.execute(
            workflow_id="workflow-1",
            workflow_data=sample_workflow_data,
            robot_id=available_robot.id,
            scheduled_time=scheduled,
        )

        # Assert
        assert job.scheduled_time == scheduled


class TestSubmitJobError:
    """Sad path tests for SubmitJobUseCase."""

    @pytest.mark.asyncio
    async def test_submit_job_empty_workflow_id_raises_error(
        self,
        mock_job_repository: AsyncMock,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
        robot_selection_service: RobotSelectionService,
        mock_dispatcher: Mock,
        sample_workflow_data: dict,
    ) -> None:
        """Submit job with empty workflow_id - raises ValueError."""
        use_case = SubmitJobUseCase(
            job_repository=mock_job_repository,
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
            robot_selection_service=robot_selection_service,
            dispatcher=mock_dispatcher,
        )

        # Act & Assert
        with pytest.raises(ValueError, match="workflow_id cannot be empty"):
            await use_case.execute(
                workflow_id="",
                workflow_data=sample_workflow_data,
            )

    @pytest.mark.asyncio
    async def test_submit_job_whitespace_workflow_id_raises_error(
        self,
        mock_job_repository: AsyncMock,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
        robot_selection_service: RobotSelectionService,
        mock_dispatcher: Mock,
        sample_workflow_data: dict,
    ) -> None:
        """Submit job with whitespace workflow_id - raises ValueError."""
        use_case = SubmitJobUseCase(
            job_repository=mock_job_repository,
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
            robot_selection_service=robot_selection_service,
            dispatcher=mock_dispatcher,
        )

        # Act & Assert
        with pytest.raises(ValueError, match="workflow_id cannot be empty"):
            await use_case.execute(
                workflow_id="   ",
                workflow_data=sample_workflow_data,
            )

    @pytest.mark.asyncio
    async def test_submit_job_robot_not_found_raises_error(
        self,
        mock_job_repository: AsyncMock,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
        robot_selection_service: RobotSelectionService,
        mock_dispatcher: Mock,
        sample_workflow_data: dict,
    ) -> None:
        """Submit job with non-existent robot_id - raises RobotNotFoundError."""
        # Arrange: Robot does not exist
        mock_robot_repository.get_by_id.return_value = None

        use_case = SubmitJobUseCase(
            job_repository=mock_job_repository,
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
            robot_selection_service=robot_selection_service,
            dispatcher=mock_dispatcher,
        )

        # Act & Assert
        with pytest.raises(RobotNotFoundError, match="Robot nonexistent not found"):
            await use_case.execute(
                workflow_id="workflow-1",
                workflow_data=sample_workflow_data,
                robot_id="nonexistent",
            )

    @pytest.mark.asyncio
    async def test_submit_job_robot_unavailable_raises_error(
        self,
        mock_job_repository: AsyncMock,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
        robot_selection_service: RobotSelectionService,
        mock_dispatcher: Mock,
        busy_robot: Robot,
        sample_workflow_data: dict,
    ) -> None:
        """Submit job to busy robot - raises NoAvailableRobotError."""
        # Arrange: Robot exists but is at capacity
        mock_robot_repository.get_by_id.return_value = busy_robot

        use_case = SubmitJobUseCase(
            job_repository=mock_job_repository,
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
            robot_selection_service=robot_selection_service,
            dispatcher=mock_dispatcher,
        )

        # Act & Assert
        with pytest.raises(NoAvailableRobotError, match="not available"):
            await use_case.execute(
                workflow_id="workflow-1",
                workflow_data=sample_workflow_data,
                robot_id=busy_robot.id,
            )

    @pytest.mark.asyncio
    async def test_submit_job_offline_robot_raises_error(
        self,
        mock_job_repository: AsyncMock,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
        robot_selection_service: RobotSelectionService,
        mock_dispatcher: Mock,
        offline_robot: Robot,
        sample_workflow_data: dict,
    ) -> None:
        """Submit job to offline robot - raises NoAvailableRobotError."""
        # Arrange
        mock_robot_repository.get_by_id.return_value = offline_robot

        use_case = SubmitJobUseCase(
            job_repository=mock_job_repository,
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
            robot_selection_service=robot_selection_service,
            dispatcher=mock_dispatcher,
        )

        # Act & Assert
        with pytest.raises(NoAvailableRobotError):
            await use_case.execute(
                workflow_id="workflow-1",
                workflow_data=sample_workflow_data,
                robot_id=offline_robot.id,
            )

    @pytest.mark.asyncio
    async def test_submit_job_no_robots_available_raises_error(
        self,
        mock_job_repository: AsyncMock,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
        robot_selection_service: RobotSelectionService,
        mock_dispatcher: Mock,
        sample_workflow_data: dict,
    ) -> None:
        """Submit job with no available robots - raises NoAvailableRobotError."""
        # Arrange: No robots available
        mock_robot_repository.get_all.return_value = []

        use_case = SubmitJobUseCase(
            job_repository=mock_job_repository,
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
            robot_selection_service=robot_selection_service,
            dispatcher=mock_dispatcher,
        )

        # Act & Assert
        with pytest.raises(NoAvailableRobotError, match="No available robots"):
            await use_case.execute(
                workflow_id="workflow-1",
                workflow_data=sample_workflow_data,
            )


class TestSubmitJobEdgeCases:
    """Edge case tests for SubmitJobUseCase."""

    @pytest.mark.asyncio
    async def test_submit_job_fallback_when_assigned_robot_unavailable(
        self,
        mock_job_repository: AsyncMock,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
        robot_selection_service: RobotSelectionService,
        mock_dispatcher: Mock,
        sample_workflow_data: dict,
    ) -> None:
        """Assigned robot unavailable - falls back to auto-selection."""
        # Arrange: Assigned robot is busy, but another is available (both with browser cap)
        busy_robot = create_robot(
            robot_id="robot-busy",
            name="Busy Robot",
            status=RobotStatus.ONLINE,
            max_concurrent_jobs=1,
            current_job_ids=["existing-job"],
            capabilities={RobotCapability.BROWSER},
        )
        available_robot = create_robot(
            robot_id="available-robot",
            name="Available Robot",
            current_job_ids=[],
            capabilities={RobotCapability.BROWSER},
        )

        # The busy robot is assigned to workflow
        assignment = create_assignment(workflow_id="workflow-1", robot_id=busy_robot.id)

        mock_robot_repository.get_all.return_value = [busy_robot, available_robot]
        mock_robot_repository.get_by_id.side_effect = lambda rid: (
            busy_robot if rid == busy_robot.id else available_robot
        )
        mock_assignment_repository.get_by_workflow.return_value = [assignment]

        use_case = SubmitJobUseCase(
            job_repository=mock_job_repository,
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
            robot_selection_service=robot_selection_service,
            dispatcher=mock_dispatcher,
        )

        # Act
        job = await use_case.execute(
            workflow_id="workflow-1",
            workflow_data=sample_workflow_data,
        )

        # Assert: Should fall back to available robot
        assert job.robot_id == "available-robot"

    @pytest.mark.asyncio
    async def test_submit_job_analyzes_browser_workflow_capabilities(
        self,
        mock_job_repository: AsyncMock,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
        robot_selection_service: RobotSelectionService,
        mock_dispatcher: Mock,
        sample_workflow_data: dict,
    ) -> None:
        """Workflow with browser nodes - selects robot with browser capability."""
        # Arrange: One robot with browser cap, one without
        browser_robot = create_robot(
            robot_id="browser-robot",
            name="Browser Robot",
            capabilities={RobotCapability.BROWSER},
            current_job_ids=[],
        )
        no_cap_robot = create_robot(
            robot_id="no-cap-robot",
            name="No Cap Robot",
            capabilities=set(),
            current_job_ids=[],
        )

        mock_robot_repository.get_all.return_value = [no_cap_robot, browser_robot]
        mock_robot_repository.get_by_id.side_effect = lambda rid: (
            browser_robot if rid == "browser-robot" else no_cap_robot
        )

        use_case = SubmitJobUseCase(
            job_repository=mock_job_repository,
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
            robot_selection_service=robot_selection_service,
            dispatcher=mock_dispatcher,
        )

        # Act
        job = await use_case.execute(
            workflow_id="workflow-1",
            workflow_data=sample_workflow_data,  # Contains BrowserNavigateNode
        )

        # Assert: Should select browser-capable robot
        assert job.robot_id == "browser-robot"

    @pytest.mark.asyncio
    async def test_submit_job_analyzes_desktop_workflow_capabilities(
        self,
        mock_job_repository: AsyncMock,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
        robot_selection_service: RobotSelectionService,
        mock_dispatcher: Mock,
        sample_workflow_data_with_desktop: dict,
    ) -> None:
        """Workflow with desktop nodes - selects robot with desktop capability."""
        # Arrange: Desktop robot has both browser (for StartNode) and desktop capabilities
        desktop_robot = create_robot(
            robot_id="desktop-robot",
            name="Desktop Robot",
            capabilities={RobotCapability.DESKTOP, RobotCapability.BROWSER},
            current_job_ids=[],
        )
        browser_only = create_robot(
            robot_id="browser-only",
            name="Browser Only",
            capabilities={RobotCapability.BROWSER},  # Missing desktop
            current_job_ids=[],
        )

        mock_robot_repository.get_all.return_value = [browser_only, desktop_robot]
        mock_robot_repository.get_by_id.side_effect = lambda rid: (
            desktop_robot if rid == "desktop-robot" else browser_only
        )

        use_case = SubmitJobUseCase(
            job_repository=mock_job_repository,
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
            robot_selection_service=robot_selection_service,
            dispatcher=mock_dispatcher,
        )

        # Act
        job = await use_case.execute(
            workflow_id="workflow-1",
            workflow_data=sample_workflow_data_with_desktop,
        )

        # Assert
        assert job.robot_id == "desktop-robot"

    @pytest.mark.asyncio
    async def test_submit_job_workflow_name_from_metadata(
        self,
        mock_job_repository: AsyncMock,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
        robot_selection_service: RobotSelectionService,
        mock_dispatcher: Mock,
        available_robot: Robot,
        sample_workflow_data: dict,
    ) -> None:
        """Workflow name extracted from metadata when not explicitly provided."""
        # Arrange
        mock_robot_repository.get_by_id.return_value = available_robot
        mock_robot_repository.get_all.return_value = [available_robot]

        use_case = SubmitJobUseCase(
            job_repository=mock_job_repository,
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
            robot_selection_service=robot_selection_service,
            dispatcher=mock_dispatcher,
        )

        # Act
        job = await use_case.execute(
            workflow_id="workflow-1",
            workflow_data=sample_workflow_data,
            robot_id=available_robot.id,
        )

        # Assert: Should use name from metadata
        assert job.workflow_name == "Test Workflow"

    @pytest.mark.asyncio
    async def test_submit_job_explicit_workflow_name_overrides_metadata(
        self,
        mock_job_repository: AsyncMock,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
        robot_selection_service: RobotSelectionService,
        mock_dispatcher: Mock,
        available_robot: Robot,
        sample_workflow_data: dict,
    ) -> None:
        """Explicit workflow_name parameter takes precedence over metadata."""
        # Arrange
        mock_robot_repository.get_by_id.return_value = available_robot
        mock_robot_repository.get_all.return_value = [available_robot]

        use_case = SubmitJobUseCase(
            job_repository=mock_job_repository,
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
            robot_selection_service=robot_selection_service,
            dispatcher=mock_dispatcher,
        )

        # Act
        job = await use_case.execute(
            workflow_id="workflow-1",
            workflow_data=sample_workflow_data,
            robot_id=available_robot.id,
            workflow_name="Custom Name Override",
        )

        # Assert
        assert job.workflow_name == "Custom Name Override"

    @pytest.mark.asyncio
    async def test_submit_job_dispatch_failure_keeps_job_pending(
        self,
        mock_job_repository: AsyncMock,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
        robot_selection_service: RobotSelectionService,
        available_robot: Robot,
        sample_workflow_data: dict,
    ) -> None:
        """Dispatch failure - job saved but remains PENDING for later pickup."""
        # Arrange: Dispatcher will fail
        mock_dispatcher = Mock()
        mock_dispatcher.get_robot.return_value = available_robot
        mock_dispatcher.register_robot.return_value = None
        mock_dispatcher.select_robot.return_value = None  # Dispatch fails

        mock_robot_repository.get_by_id.return_value = available_robot
        mock_robot_repository.get_all.return_value = [available_robot]

        use_case = SubmitJobUseCase(
            job_repository=mock_job_repository,
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
            robot_selection_service=robot_selection_service,
            dispatcher=mock_dispatcher,
        )

        # Act
        job = await use_case.execute(
            workflow_id="workflow-1",
            workflow_data=sample_workflow_data,
            robot_id=available_robot.id,
        )

        # Assert: Job should be saved even if dispatch fails
        assert job.status == JobStatus.PENDING
        mock_job_repository.save.assert_awaited()

    @pytest.mark.asyncio
    async def test_submit_job_with_nodes_as_list(
        self,
        mock_job_repository: AsyncMock,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
        robot_selection_service: RobotSelectionService,
        mock_dispatcher: Mock,
        available_robot: Robot,
    ) -> None:
        """Workflow with nodes as list instead of dict - handles both formats."""
        # Arrange
        workflow_data = {
            "metadata": {"name": "List Nodes Workflow"},
            "nodes": [
                {"type": "BrowserNavigateNode"},
                {"type": "ClickNode"},
            ],
            "connections": [],
        }

        mock_robot_repository.get_by_id.return_value = available_robot
        mock_robot_repository.get_all.return_value = [available_robot]

        use_case = SubmitJobUseCase(
            job_repository=mock_job_repository,
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
            robot_selection_service=robot_selection_service,
            dispatcher=mock_dispatcher,
        )

        # Act
        job = await use_case.execute(
            workflow_id="workflow-1",
            workflow_data=workflow_data,
            robot_id=available_robot.id,
        )

        # Assert: Should process without error
        assert job is not None
        assert job.workflow_id == "workflow-1"

    @pytest.mark.asyncio
    async def test_submit_job_merges_existing_variables(
        self,
        mock_job_repository: AsyncMock,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
        robot_selection_service: RobotSelectionService,
        mock_dispatcher: Mock,
        available_robot: Robot,
    ) -> None:
        """Variables parameter merges with existing workflow variables."""
        # Arrange
        workflow_data = {
            "metadata": {"name": "Existing Vars Workflow"},
            "nodes": {},
            "connections": [],
            "variables": {"existing_var": "original", "keep_me": "unchanged"},
        }

        mock_robot_repository.get_by_id.return_value = available_robot
        mock_robot_repository.get_all.return_value = [available_robot]

        use_case = SubmitJobUseCase(
            job_repository=mock_job_repository,
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
            robot_selection_service=robot_selection_service,
            dispatcher=mock_dispatcher,
        )

        # Act
        job = await use_case.execute(
            workflow_id="workflow-1",
            workflow_data=workflow_data,
            robot_id=available_robot.id,
            variables={"existing_var": "overwritten", "new_var": "added"},
        )

        # Assert
        import orjson

        workflow_json = orjson.loads(job.workflow_json)
        assert workflow_json["variables"]["existing_var"] == "overwritten"
        assert workflow_json["variables"]["keep_me"] == "unchanged"
        assert workflow_json["variables"]["new_var"] == "added"
