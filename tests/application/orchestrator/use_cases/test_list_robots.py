"""Tests for ListRobotsUseCase.

Tests the robot listing and filtering with:
- Mock infrastructure (repositories)
- Real domain objects (Robot, RobotAssignment)
- Three-scenario pattern: SUCCESS, ERROR, EDGE_CASES
"""

import pytest
from unittest.mock import AsyncMock

from casare_rpa.application.orchestrator.use_cases.list_robots import ListRobotsUseCase
from casare_rpa.domain.orchestrator.entities.robot import (
    Robot,
    RobotStatus,
    RobotCapability,
)

from .conftest import create_robot, create_assignment


class TestGetAllSuccess:
    """Happy path tests for get_all."""

    @pytest.mark.asyncio
    async def test_get_all_robots(
        self,
        mock_robot_repository: AsyncMock,
    ) -> None:
        """Get all robots - returns complete list."""
        # Arrange
        robots = [
            create_robot(robot_id="robot-1", name="Robot 1"),
            create_robot(robot_id="robot-2", name="Robot 2"),
            create_robot(robot_id="robot-3", name="Robot 3"),
        ]
        mock_robot_repository.get_all.return_value = robots

        use_case = ListRobotsUseCase(robot_repository=mock_robot_repository)

        # Act
        result = await use_case.get_all()

        # Assert
        assert len(result) == 3
        assert result[0].id == "robot-1"
        assert result[1].id == "robot-2"
        assert result[2].id == "robot-3"

    @pytest.mark.asyncio
    async def test_get_all_empty_list(
        self,
        mock_robot_repository: AsyncMock,
    ) -> None:
        """Get all when no robots exist - returns empty list."""
        # Arrange
        mock_robot_repository.get_all.return_value = []

        use_case = ListRobotsUseCase(robot_repository=mock_robot_repository)

        # Act
        result = await use_case.get_all()

        # Assert
        assert result == []


class TestGetAvailableSuccess:
    """Happy path tests for get_available."""

    @pytest.mark.asyncio
    async def test_get_available_robots(
        self,
        mock_robot_repository: AsyncMock,
        available_robot: Robot,
        busy_robot: Robot,
        offline_robot: Robot,
    ) -> None:
        """Get available robots - returns only robots that can accept jobs."""
        # Arrange
        mock_robot_repository.get_available.return_value = [available_robot]

        use_case = ListRobotsUseCase(robot_repository=mock_robot_repository)

        # Act
        result = await use_case.get_available()

        # Assert
        assert len(result) == 1
        assert result[0].id == available_robot.id

    @pytest.mark.asyncio
    async def test_get_available_none_available(
        self,
        mock_robot_repository: AsyncMock,
    ) -> None:
        """Get available when none available - returns empty list."""
        # Arrange
        mock_robot_repository.get_available.return_value = []

        use_case = ListRobotsUseCase(robot_repository=mock_robot_repository)

        # Act
        result = await use_case.get_available()

        # Assert
        assert result == []


class TestGetByCapabilitySuccess:
    """Happy path tests for capability filtering."""

    @pytest.mark.asyncio
    async def test_get_by_capability_single(
        self,
        mock_robot_repository: AsyncMock,
        robot_with_gpu: Robot,
    ) -> None:
        """Get robots with single capability - filters correctly."""
        # Arrange
        mock_robot_repository.get_by_capability.return_value = [robot_with_gpu]

        use_case = ListRobotsUseCase(robot_repository=mock_robot_repository)

        # Act
        result = await use_case.get_by_capability(RobotCapability.GPU)

        # Assert
        assert len(result) == 1
        assert RobotCapability.GPU in result[0].capabilities

    @pytest.mark.asyncio
    async def test_get_by_capabilities_multiple(
        self,
        mock_robot_repository: AsyncMock,
    ) -> None:
        """Get robots with multiple capabilities - all must match."""
        # Arrange
        multi_cap_robot = create_robot(
            robot_id="multi-cap",
            name="Multi Cap Robot",
            capabilities={
                RobotCapability.BROWSER,
                RobotCapability.DESKTOP,
                RobotCapability.GPU,
            },
        )
        mock_robot_repository.get_by_capabilities.return_value = [multi_cap_robot]

        use_case = ListRobotsUseCase(robot_repository=mock_robot_repository)

        # Act
        result = await use_case.get_by_capabilities(
            [RobotCapability.BROWSER, RobotCapability.DESKTOP]
        )

        # Assert
        assert len(result) == 1
        assert result[0].has_all_capabilities(
            {RobotCapability.BROWSER, RobotCapability.DESKTOP}
        )


class TestGetForWorkflowSuccess:
    """Happy path tests for workflow-based filtering."""

    @pytest.mark.asyncio
    async def test_get_for_workflow(
        self,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
    ) -> None:
        """Get robots assigned to workflow - returns assigned robots."""
        # Arrange
        robot1 = create_robot(robot_id="robot-1", name="Robot 1")
        robot2 = create_robot(robot_id="robot-2", name="Robot 2")

        assignments = [
            create_assignment(workflow_id="workflow-1", robot_id="robot-1"),
            create_assignment(
                workflow_id="workflow-1", robot_id="robot-2", is_default=False
            ),
        ]
        mock_assignment_repository.get_by_workflow.return_value = assignments
        mock_robot_repository.get_by_id.side_effect = lambda rid: (
            robot1 if rid == "robot-1" else robot2
        )

        use_case = ListRobotsUseCase(
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
        )

        # Act
        result = await use_case.get_for_workflow("workflow-1")

        # Assert
        assert len(result) == 2
        robot_ids = {r.id for r in result}
        assert "robot-1" in robot_ids
        assert "robot-2" in robot_ids

    @pytest.mark.asyncio
    async def test_get_for_workflow_no_assignments(
        self,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
    ) -> None:
        """Get robots for workflow with no assignments - returns empty list."""
        # Arrange
        mock_assignment_repository.get_by_workflow.return_value = []

        use_case = ListRobotsUseCase(
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
        )

        # Act
        result = await use_case.get_for_workflow("workflow-1")

        # Assert
        assert result == []

    @pytest.mark.asyncio
    async def test_get_default_for_workflow(
        self,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        available_robot: Robot,
    ) -> None:
        """Get default robot for workflow - returns default robot."""
        # Arrange
        default_assignment = create_assignment(
            workflow_id="workflow-1",
            robot_id=available_robot.id,
            is_default=True,
        )
        mock_assignment_repository.get_default_for_workflow.return_value = (
            default_assignment
        )
        mock_robot_repository.get_by_id.return_value = available_robot

        use_case = ListRobotsUseCase(
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
        )

        # Act
        result = await use_case.get_default_for_workflow("workflow-1")

        # Assert
        assert result is not None
        assert result.id == available_robot.id

    @pytest.mark.asyncio
    async def test_get_default_for_workflow_none(
        self,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
    ) -> None:
        """Get default for workflow with no default - returns None."""
        # Arrange
        mock_assignment_repository.get_default_for_workflow.return_value = None

        use_case = ListRobotsUseCase(
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
        )

        # Act
        result = await use_case.get_default_for_workflow("workflow-1")

        # Assert
        assert result is None


class TestGetForWorkflowError:
    """Sad path tests for workflow-based filtering."""

    @pytest.mark.asyncio
    async def test_get_for_workflow_without_assignment_repo_raises_error(
        self,
        mock_robot_repository: AsyncMock,
    ) -> None:
        """Get for workflow without assignment repo - raises ValueError."""
        use_case = ListRobotsUseCase(
            robot_repository=mock_robot_repository,
            assignment_repository=None,  # No assignment repo
        )

        # Act & Assert
        with pytest.raises(
            ValueError, match="assignment_repository required for get_for_workflow"
        ):
            await use_case.get_for_workflow("workflow-1")

    @pytest.mark.asyncio
    async def test_get_default_for_workflow_without_assignment_repo_raises_error(
        self,
        mock_robot_repository: AsyncMock,
    ) -> None:
        """Get default for workflow without assignment repo - raises ValueError."""
        use_case = ListRobotsUseCase(
            robot_repository=mock_robot_repository,
            assignment_repository=None,
        )

        # Act & Assert
        with pytest.raises(
            ValueError,
            match="assignment_repository required for get_default_for_workflow",
        ):
            await use_case.get_default_for_workflow("workflow-1")


class TestGetByIdAndNameSuccess:
    """Happy path tests for get_by_id and get_by_name."""

    @pytest.mark.asyncio
    async def test_get_by_id(
        self,
        mock_robot_repository: AsyncMock,
        available_robot: Robot,
    ) -> None:
        """Get robot by ID - returns robot."""
        # Arrange
        mock_robot_repository.get_by_id.return_value = available_robot

        use_case = ListRobotsUseCase(robot_repository=mock_robot_repository)

        # Act
        result = await use_case.get_by_id(available_robot.id)

        # Assert
        assert result is not None
        assert result.id == available_robot.id

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(
        self,
        mock_robot_repository: AsyncMock,
    ) -> None:
        """Get robot by ID when not found - returns None."""
        # Arrange
        mock_robot_repository.get_by_id.return_value = None

        use_case = ListRobotsUseCase(robot_repository=mock_robot_repository)

        # Act
        result = await use_case.get_by_id("nonexistent")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_name(
        self,
        mock_robot_repository: AsyncMock,
        available_robot: Robot,
    ) -> None:
        """Get robot by name - returns robot."""
        # Arrange
        mock_robot_repository.get_by_hostname.return_value = available_robot

        use_case = ListRobotsUseCase(robot_repository=mock_robot_repository)

        # Act
        result = await use_case.get_by_name(available_robot.name)

        # Assert
        assert result is not None
        assert result.name == available_robot.name


class TestGetByStatusSuccess:
    """Happy path tests for status-based filtering."""

    @pytest.mark.asyncio
    async def test_get_online_robots(
        self,
        mock_robot_repository: AsyncMock,
    ) -> None:
        """Get online robots - returns only ONLINE status."""
        # Arrange
        online_robots = [
            create_robot(robot_id="r1", name="R1", status=RobotStatus.ONLINE),
            create_robot(robot_id="r2", name="R2", status=RobotStatus.ONLINE),
        ]
        mock_robot_repository.get_by_status.return_value = online_robots

        use_case = ListRobotsUseCase(robot_repository=mock_robot_repository)

        # Act
        result = await use_case.get_online()

        # Assert
        assert len(result) == 2
        for robot in result:
            assert robot.status == RobotStatus.ONLINE

    @pytest.mark.asyncio
    async def test_get_offline_robots(
        self,
        mock_robot_repository: AsyncMock,
    ) -> None:
        """Get offline robots - returns only OFFLINE status."""
        # Arrange
        offline_robots = [
            create_robot(robot_id="r1", name="R1", status=RobotStatus.OFFLINE),
        ]
        mock_robot_repository.get_by_status.return_value = offline_robots

        use_case = ListRobotsUseCase(robot_repository=mock_robot_repository)

        # Act
        result = await use_case.get_offline()

        # Assert
        assert len(result) == 1
        assert result[0].status == RobotStatus.OFFLINE

    @pytest.mark.asyncio
    async def test_get_busy_robots(
        self,
        mock_robot_repository: AsyncMock,
    ) -> None:
        """Get busy robots - returns only BUSY status."""
        # Arrange
        busy_robots = [
            create_robot(robot_id="r1", name="R1", status=RobotStatus.BUSY),
        ]
        mock_robot_repository.get_by_status.return_value = busy_robots

        use_case = ListRobotsUseCase(robot_repository=mock_robot_repository)

        # Act
        result = await use_case.get_busy()

        # Assert
        assert len(result) == 1
        assert result[0].status == RobotStatus.BUSY


class TestGetWithCapacitySuccess:
    """Happy path tests for capacity filtering."""

    @pytest.mark.asyncio
    async def test_get_with_available_capacity(
        self,
        mock_robot_repository: AsyncMock,
    ) -> None:
        """Get robots with available capacity - filters by min capacity."""
        # Arrange
        high_cap = create_robot(
            robot_id="high",
            name="High Cap",
            max_concurrent_jobs=10,
            current_job_ids=["j1", "j2"],  # 8 available
        )
        low_cap = create_robot(
            robot_id="low",
            name="Low Cap",
            max_concurrent_jobs=3,
            current_job_ids=["j1", "j2"],  # 1 available
        )
        mock_robot_repository.get_available.return_value = [high_cap, low_cap]

        use_case = ListRobotsUseCase(robot_repository=mock_robot_repository)

        # Act
        result = await use_case.get_with_available_capacity(min_capacity=5)

        # Assert
        assert len(result) == 1
        assert result[0].id == "high"


class TestSearchSuccess:
    """Happy path tests for search functionality."""

    @pytest.mark.asyncio
    async def test_search_by_name(
        self,
        mock_robot_repository: AsyncMock,
    ) -> None:
        """Search robots by name - matches partial name."""
        # Arrange
        robots = [
            create_robot(robot_id="r1", name="Production Robot", tags=[]),
            create_robot(robot_id="r2", name="Test Robot", tags=[]),
            create_robot(robot_id="r3", name="Dev Robot", tags=[]),
        ]
        mock_robot_repository.get_all.return_value = robots

        use_case = ListRobotsUseCase(robot_repository=mock_robot_repository)

        # Act
        result = await use_case.search("prod")

        # Assert
        assert len(result) == 1
        assert result[0].name == "Production Robot"

    @pytest.mark.asyncio
    async def test_search_by_tag(
        self,
        mock_robot_repository: AsyncMock,
    ) -> None:
        """Search robots by tag - matches tags."""
        # Arrange
        robots = [
            create_robot(robot_id="r1", name="Robot 1", tags=["production", "gpu"]),
            create_robot(robot_id="r2", name="Robot 2", tags=["staging"]),
        ]
        mock_robot_repository.get_all.return_value = robots

        use_case = ListRobotsUseCase(robot_repository=mock_robot_repository)

        # Act
        result = await use_case.search("gpu")

        # Assert
        assert len(result) == 1
        assert "gpu" in result[0].tags

    @pytest.mark.asyncio
    async def test_search_case_insensitive(
        self,
        mock_robot_repository: AsyncMock,
    ) -> None:
        """Search is case insensitive."""
        # Arrange
        robots = [
            create_robot(robot_id="r1", name="Production Robot"),
        ]
        mock_robot_repository.get_all.return_value = robots

        use_case = ListRobotsUseCase(robot_repository=mock_robot_repository)

        # Act
        result = await use_case.search("PRODUCTION")

        # Assert
        assert len(result) == 1


class TestGetStatisticsSuccess:
    """Happy path tests for statistics."""

    @pytest.mark.asyncio
    async def test_get_statistics(
        self,
        mock_robot_repository: AsyncMock,
    ) -> None:
        """Get robot fleet statistics - calculates all metrics."""
        # Arrange
        robots = [
            create_robot(
                robot_id="r1",
                name="R1",
                status=RobotStatus.ONLINE,
                max_concurrent_jobs=5,
                current_job_ids=["j1"],
                capabilities={RobotCapability.BROWSER},
            ),
            create_robot(
                robot_id="r2",
                name="R2",
                status=RobotStatus.ONLINE,
                max_concurrent_jobs=5,
                current_job_ids=["j1", "j2"],
                capabilities={RobotCapability.BROWSER, RobotCapability.GPU},
            ),
            create_robot(
                robot_id="r3",
                name="R3",
                status=RobotStatus.OFFLINE,
                max_concurrent_jobs=5,
                current_job_ids=[],
                capabilities={RobotCapability.DESKTOP},
            ),
            create_robot(
                robot_id="r4",
                name="R4",
                status=RobotStatus.BUSY,
                max_concurrent_jobs=1,
                current_job_ids=["j1"],
                capabilities={RobotCapability.BROWSER},
            ),
        ]
        mock_robot_repository.get_all.return_value = robots

        use_case = ListRobotsUseCase(robot_repository=mock_robot_repository)

        # Act
        stats = await use_case.get_statistics()

        # Assert
        assert stats["total"] == 4

        # Status counts
        assert stats["by_status"]["online"] == 2
        assert stats["by_status"]["offline"] == 1
        assert stats["by_status"]["busy"] == 1
        assert stats["by_status"]["error"] == 0
        assert stats["by_status"]["maintenance"] == 0

        # Capacity
        assert stats["capacity"]["total"] == 16  # 5+5+5+1
        assert stats["capacity"]["current_load"] == 4  # 1+2+0+1
        assert stats["capacity"]["available"] == 12  # 16-4

        # Capabilities
        assert stats["capabilities"]["browser"] == 3
        assert stats["capabilities"]["gpu"] == 1
        assert stats["capabilities"]["desktop"] == 1

    @pytest.mark.asyncio
    async def test_get_statistics_empty_fleet(
        self,
        mock_robot_repository: AsyncMock,
    ) -> None:
        """Get statistics with no robots - handles empty fleet."""
        # Arrange
        mock_robot_repository.get_all.return_value = []

        use_case = ListRobotsUseCase(robot_repository=mock_robot_repository)

        # Act
        stats = await use_case.get_statistics()

        # Assert
        assert stats["total"] == 0
        assert stats["capacity"]["total"] == 0
        assert stats["capacity"]["utilization_percent"] == 0


class TestEdgeCases:
    """Edge case tests for ListRobotsUseCase."""

    @pytest.mark.asyncio
    async def test_get_for_workflow_robot_deleted(
        self,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
    ) -> None:
        """Get for workflow when assigned robot deleted - skips missing robots."""
        # Arrange
        assignments = [
            create_assignment(workflow_id="workflow-1", robot_id="robot-1"),
            create_assignment(
                workflow_id="workflow-1", robot_id="deleted-robot", is_default=False
            ),
        ]
        mock_assignment_repository.get_by_workflow.return_value = assignments

        existing_robot = create_robot(robot_id="robot-1", name="Robot 1")
        mock_robot_repository.get_by_id.side_effect = lambda rid: (
            existing_robot if rid == "robot-1" else None
        )

        use_case = ListRobotsUseCase(
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
        )

        # Act
        result = await use_case.get_for_workflow("workflow-1")

        # Assert: Only existing robot returned
        assert len(result) == 1
        assert result[0].id == "robot-1"

    @pytest.mark.asyncio
    async def test_search_empty_query(
        self,
        mock_robot_repository: AsyncMock,
    ) -> None:
        """Search with empty query - matches all robots."""
        # Arrange
        robots = [
            create_robot(robot_id="r1", name="Robot 1"),
            create_robot(robot_id="r2", name="Robot 2"),
        ]
        mock_robot_repository.get_all.return_value = robots

        use_case = ListRobotsUseCase(robot_repository=mock_robot_repository)

        # Act
        result = await use_case.search("")

        # Assert: Empty string matches all
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_statistics_utilization_calculation(
        self,
        mock_robot_repository: AsyncMock,
    ) -> None:
        """Statistics utilization - calculates percentage correctly."""
        # Arrange: 50% utilization
        robots = [
            create_robot(
                robot_id="r1",
                name="R1",
                status=RobotStatus.ONLINE,
                max_concurrent_jobs=4,
                current_job_ids=["j1", "j2"],  # 2 of 4
            ),
        ]
        mock_robot_repository.get_all.return_value = robots

        use_case = ListRobotsUseCase(robot_repository=mock_robot_repository)

        # Act
        stats = await use_case.get_statistics()

        # Assert: 2/4 = 50%
        assert stats["capacity"]["utilization_percent"] == 50.0
