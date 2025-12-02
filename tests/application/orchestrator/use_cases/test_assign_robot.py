"""Tests for AssignRobotUseCase.

Tests the robot assignment orchestration with:
- Mock infrastructure (repositories)
- Real domain objects (Robot, RobotAssignment, NodeRobotOverride)
- Three-scenario pattern: SUCCESS, ERROR, EDGE_CASES
"""

import pytest
from unittest.mock import AsyncMock

from casare_rpa.application.orchestrator.use_cases.assign_robot import (
    AssignRobotUseCase,
)
from casare_rpa.domain.orchestrator.entities.robot import RobotCapability
from casare_rpa.domain.orchestrator.value_objects.robot_assignment import (
    RobotAssignment,
)
from casare_rpa.domain.orchestrator.value_objects.node_robot_override import (
    NodeRobotOverride,
)
from casare_rpa.domain.orchestrator.errors import (
    RobotNotFoundError,
    InvalidAssignmentError,
)

from .conftest import create_robot, create_assignment, create_node_override


class TestAssignToWorkflowSuccess:
    """Happy path tests for assign_to_workflow."""

    @pytest.mark.asyncio
    async def test_assign_robot_to_workflow(
        self,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
        available_robot,
    ) -> None:
        """Assign robot to workflow - creates RobotAssignment."""
        # Arrange
        mock_robot_repository.get_by_id.return_value = available_robot

        use_case = AssignRobotUseCase(
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
        )

        # Act
        assignment = await use_case.assign_to_workflow(
            workflow_id="workflow-1",
            robot_id=available_robot.id,
            is_default=True,
            priority=10,
            notes="Primary robot for this workflow",
        )

        # Assert
        assert assignment is not None
        assert assignment.workflow_id == "workflow-1"
        assert assignment.robot_id == available_robot.id
        assert assignment.is_default is True
        assert assignment.priority == 10
        assert assignment.notes == "Primary robot for this workflow"

        # Verify repository was called
        mock_assignment_repository.save.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_assign_robot_as_non_default(
        self,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
        available_robot,
    ) -> None:
        """Assign robot as non-default - creates backup assignment."""
        # Arrange
        mock_robot_repository.get_by_id.return_value = available_robot

        use_case = AssignRobotUseCase(
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
        )

        # Act
        assignment = await use_case.assign_to_workflow(
            workflow_id="workflow-1",
            robot_id=available_robot.id,
            is_default=False,
            priority=5,
        )

        # Assert
        assert assignment.is_default is False
        assert assignment.priority == 5


class TestAssignToWorkflowError:
    """Sad path tests for assign_to_workflow."""

    @pytest.mark.asyncio
    async def test_assign_empty_workflow_id_raises_error(
        self,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
    ) -> None:
        """Assign with empty workflow_id - raises InvalidAssignmentError."""
        use_case = AssignRobotUseCase(
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
        )

        # Act & Assert
        with pytest.raises(InvalidAssignmentError, match="workflow_id cannot be empty"):
            await use_case.assign_to_workflow(
                workflow_id="",
                robot_id="robot-1",
            )

    @pytest.mark.asyncio
    async def test_assign_whitespace_workflow_id_raises_error(
        self,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
    ) -> None:
        """Assign with whitespace workflow_id - raises InvalidAssignmentError."""
        use_case = AssignRobotUseCase(
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
        )

        # Act & Assert
        with pytest.raises(InvalidAssignmentError, match="workflow_id cannot be empty"):
            await use_case.assign_to_workflow(
                workflow_id="   ",
                robot_id="robot-1",
            )

    @pytest.mark.asyncio
    async def test_assign_empty_robot_id_raises_error(
        self,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
    ) -> None:
        """Assign with empty robot_id - raises InvalidAssignmentError."""
        use_case = AssignRobotUseCase(
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
        )

        # Act & Assert
        with pytest.raises(InvalidAssignmentError, match="robot_id cannot be empty"):
            await use_case.assign_to_workflow(
                workflow_id="workflow-1",
                robot_id="",
            )

    @pytest.mark.asyncio
    async def test_assign_nonexistent_robot_raises_error(
        self,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
    ) -> None:
        """Assign non-existent robot - raises RobotNotFoundError."""
        # Arrange
        mock_robot_repository.get_by_id.return_value = None

        use_case = AssignRobotUseCase(
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
        )

        # Act & Assert
        with pytest.raises(RobotNotFoundError, match="Robot nonexistent not found"):
            await use_case.assign_to_workflow(
                workflow_id="workflow-1",
                robot_id="nonexistent",
            )


class TestAssignToNodeSuccess:
    """Happy path tests for assign_to_node."""

    @pytest.mark.asyncio
    async def test_assign_specific_robot_to_node(
        self,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
        available_robot,
    ) -> None:
        """Assign specific robot to node - creates NodeRobotOverride with robot_id."""
        # Arrange
        mock_robot_repository.get_by_id.return_value = available_robot

        use_case = AssignRobotUseCase(
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
        )

        # Act
        override = await use_case.assign_to_node(
            workflow_id="workflow-1",
            node_id="node-gpu-intensive",
            robot_id=available_robot.id,
            reason="Node requires specific robot for GPU processing",
        )

        # Assert
        assert override is not None
        assert override.workflow_id == "workflow-1"
        assert override.node_id == "node-gpu-intensive"
        assert override.robot_id == available_robot.id
        assert override.is_active is True
        assert override.reason == "Node requires specific robot for GPU processing"

        mock_override_repository.save.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_assign_capabilities_to_node(
        self,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
    ) -> None:
        """Assign capability requirements to node - creates capability-based override."""
        use_case = AssignRobotUseCase(
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
        )

        # Act
        override = await use_case.assign_to_node(
            workflow_id="workflow-1",
            node_id="node-ml",
            robot_id=None,  # No specific robot
            required_capabilities=["gpu", "browser"],
            reason="ML node requires GPU",
        )

        # Assert
        assert override is not None
        assert override.robot_id is None
        assert RobotCapability.GPU in override.required_capabilities
        assert RobotCapability.BROWSER in override.required_capabilities
        assert override.is_capability_based is True


class TestAssignToNodeError:
    """Sad path tests for assign_to_node."""

    @pytest.mark.asyncio
    async def test_assign_node_empty_workflow_id_raises_error(
        self,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
    ) -> None:
        """Assign node with empty workflow_id - raises InvalidAssignmentError."""
        use_case = AssignRobotUseCase(
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
        )

        # Act & Assert
        with pytest.raises(InvalidAssignmentError, match="workflow_id cannot be empty"):
            await use_case.assign_to_node(
                workflow_id="",
                node_id="node-1",
                robot_id="robot-1",
            )

    @pytest.mark.asyncio
    async def test_assign_node_empty_node_id_raises_error(
        self,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
    ) -> None:
        """Assign node with empty node_id - raises InvalidAssignmentError."""
        use_case = AssignRobotUseCase(
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
        )

        # Act & Assert
        with pytest.raises(InvalidAssignmentError, match="node_id cannot be empty"):
            await use_case.assign_to_node(
                workflow_id="workflow-1",
                node_id="",
                robot_id="robot-1",
            )

    @pytest.mark.asyncio
    async def test_assign_node_no_robot_or_capabilities_raises_error(
        self,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
    ) -> None:
        """Assign node without robot_id or capabilities - raises InvalidAssignmentError."""
        use_case = AssignRobotUseCase(
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
        )

        # Act & Assert
        with pytest.raises(
            InvalidAssignmentError,
            match="Must specify either robot_id or required_capabilities",
        ):
            await use_case.assign_to_node(
                workflow_id="workflow-1",
                node_id="node-1",
                robot_id=None,
                required_capabilities=None,
            )

    @pytest.mark.asyncio
    async def test_assign_node_nonexistent_robot_raises_error(
        self,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
    ) -> None:
        """Assign node with non-existent robot - raises RobotNotFoundError."""
        # Arrange
        mock_robot_repository.get_by_id.return_value = None

        use_case = AssignRobotUseCase(
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
        )

        # Act & Assert
        with pytest.raises(RobotNotFoundError):
            await use_case.assign_to_node(
                workflow_id="workflow-1",
                node_id="node-1",
                robot_id="nonexistent",
            )


class TestRemoveAssignmentSuccess:
    """Happy path tests for remove operations."""

    @pytest.mark.asyncio
    async def test_remove_workflow_assignment(
        self,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
    ) -> None:
        """Remove workflow assignment - returns True when deleted."""
        # Arrange
        mock_assignment_repository.delete.return_value = True

        use_case = AssignRobotUseCase(
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
        )

        # Act
        result = await use_case.remove_workflow_assignment(
            workflow_id="workflow-1",
            robot_id="robot-1",
        )

        # Assert
        assert result is True
        mock_assignment_repository.delete.assert_awaited_once_with(
            "workflow-1", "robot-1"
        )

    @pytest.mark.asyncio
    async def test_remove_workflow_assignment_not_found(
        self,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
    ) -> None:
        """Remove non-existent assignment - returns False."""
        # Arrange
        mock_assignment_repository.delete.return_value = False

        use_case = AssignRobotUseCase(
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
        )

        # Act
        result = await use_case.remove_workflow_assignment(
            workflow_id="workflow-1",
            robot_id="robot-1",
        )

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_remove_node_override(
        self,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
    ) -> None:
        """Remove node override - returns True when deleted."""
        # Arrange
        mock_override_repository.delete.return_value = True

        use_case = AssignRobotUseCase(
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
        )

        # Act
        result = await use_case.remove_node_override(
            workflow_id="workflow-1",
            node_id="node-1",
        )

        # Assert
        assert result is True
        mock_override_repository.delete.assert_awaited_once_with("workflow-1", "node-1")


class TestDeactivateActivateSuccess:
    """Tests for deactivate/activate operations."""

    @pytest.mark.asyncio
    async def test_deactivate_node_override(
        self,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
    ) -> None:
        """Deactivate node override - soft delete operation."""
        # Arrange
        mock_override_repository.deactivate.return_value = True

        use_case = AssignRobotUseCase(
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
        )

        # Act
        result = await use_case.deactivate_node_override(
            workflow_id="workflow-1",
            node_id="node-1",
        )

        # Assert
        assert result is True
        mock_override_repository.deactivate.assert_awaited_once_with(
            "workflow-1", "node-1"
        )

    @pytest.mark.asyncio
    async def test_activate_node_override(
        self,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
    ) -> None:
        """Activate previously deactivated override - re-enables it."""
        # Arrange
        mock_override_repository.activate.return_value = True

        use_case = AssignRobotUseCase(
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
        )

        # Act
        result = await use_case.activate_node_override(
            workflow_id="workflow-1",
            node_id="node-1",
        )

        # Assert
        assert result is True
        mock_override_repository.activate.assert_awaited_once_with(
            "workflow-1", "node-1"
        )


class TestQueryOperations:
    """Tests for query operations."""

    @pytest.mark.asyncio
    async def test_get_workflow_assignments(
        self,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
    ) -> None:
        """Get all assignments for a workflow."""
        # Arrange
        assignments = [
            create_assignment(workflow_id="workflow-1", robot_id="robot-1"),
            create_assignment(
                workflow_id="workflow-1", robot_id="robot-2", is_default=False
            ),
        ]
        mock_assignment_repository.get_by_workflow.return_value = assignments

        use_case = AssignRobotUseCase(
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
        )

        # Act
        result = await use_case.get_workflow_assignments(workflow_id="workflow-1")

        # Assert
        assert len(result) == 2
        assert result[0].robot_id == "robot-1"
        assert result[1].robot_id == "robot-2"

    @pytest.mark.asyncio
    async def test_get_node_overrides(
        self,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
    ) -> None:
        """Get all node overrides for a workflow."""
        # Arrange
        overrides = [
            create_node_override(
                workflow_id="workflow-1", node_id="node-1", robot_id="robot-1"
            ),
            create_node_override(
                workflow_id="workflow-1", node_id="node-2", robot_id="robot-2"
            ),
        ]
        mock_override_repository.get_by_workflow.return_value = overrides

        use_case = AssignRobotUseCase(
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
        )

        # Act
        result = await use_case.get_node_overrides(workflow_id="workflow-1")

        # Assert
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_active_node_overrides(
        self,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
    ) -> None:
        """Get only active node overrides for a workflow."""
        # Arrange
        active_overrides = [
            create_node_override(
                workflow_id="workflow-1",
                node_id="node-1",
                robot_id="robot-1",
                is_active=True,
            ),
        ]
        mock_override_repository.get_active_for_workflow.return_value = active_overrides

        use_case = AssignRobotUseCase(
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
        )

        # Act
        result = await use_case.get_active_node_overrides(workflow_id="workflow-1")

        # Assert
        assert len(result) == 1
        assert result[0].is_active is True


class TestSetDefaultRobot:
    """Tests for set_default_robot operation."""

    @pytest.mark.asyncio
    async def test_set_default_robot_new_assignment(
        self,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
        available_robot,
    ) -> None:
        """Set default robot when no assignment exists - creates new."""
        # Arrange
        mock_robot_repository.get_by_id.return_value = available_robot
        mock_assignment_repository.get_assignment.return_value = None

        use_case = AssignRobotUseCase(
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
        )

        # Act
        await use_case.set_default_robot(
            workflow_id="workflow-1",
            robot_id=available_robot.id,
        )

        # Assert: New assignment created
        mock_assignment_repository.save.assert_awaited()

    @pytest.mark.asyncio
    async def test_set_default_robot_existing_assignment(
        self,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
        available_robot,
    ) -> None:
        """Set default robot when assignment exists - updates existing."""
        # Arrange
        existing = create_assignment(
            workflow_id="workflow-1",
            robot_id=available_robot.id,
            is_default=False,
        )
        mock_robot_repository.get_by_id.return_value = available_robot
        mock_assignment_repository.get_assignment.return_value = existing

        use_case = AssignRobotUseCase(
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
        )

        # Act
        await use_case.set_default_robot(
            workflow_id="workflow-1",
            robot_id=available_robot.id,
        )

        # Assert: Existing assignment updated
        mock_assignment_repository.set_default.assert_awaited_once_with(
            "workflow-1", available_robot.id
        )

    @pytest.mark.asyncio
    async def test_set_default_robot_nonexistent_raises_error(
        self,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
    ) -> None:
        """Set default with non-existent robot - raises RobotNotFoundError."""
        # Arrange
        mock_robot_repository.get_by_id.return_value = None

        use_case = AssignRobotUseCase(
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
        )

        # Act & Assert
        with pytest.raises(RobotNotFoundError):
            await use_case.set_default_robot(
                workflow_id="workflow-1",
                robot_id="nonexistent",
            )


class TestBulkOperations:
    """Tests for bulk unassign operations."""

    @pytest.mark.asyncio
    async def test_unassign_robot_from_all_workflows(
        self,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
    ) -> None:
        """Unassign robot from all workflows - returns count removed."""
        # Arrange
        mock_assignment_repository.delete_all_for_robot.return_value = 5

        use_case = AssignRobotUseCase(
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
        )

        # Act
        count = await use_case.unassign_robot_from_all_workflows(robot_id="robot-1")

        # Assert
        assert count == 5
        mock_assignment_repository.delete_all_for_robot.assert_awaited_once_with(
            "robot-1"
        )

    @pytest.mark.asyncio
    async def test_remove_all_node_overrides_for_robot(
        self,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
    ) -> None:
        """Remove all node overrides for a robot - returns count removed."""
        # Arrange
        mock_override_repository.delete_all_for_robot.return_value = 3

        use_case = AssignRobotUseCase(
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
        )

        # Act
        count = await use_case.remove_all_node_overrides_for_robot(robot_id="robot-1")

        # Assert
        assert count == 3
        mock_override_repository.delete_all_for_robot.assert_awaited_once_with(
            "robot-1"
        )


class TestEdgeCases:
    """Edge case tests for AssignRobotUseCase."""

    @pytest.mark.asyncio
    async def test_assign_node_with_unknown_capability_ignored(
        self,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
    ) -> None:
        """Assign node with unknown capability - unknown ignored, known kept."""
        use_case = AssignRobotUseCase(
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
        )

        # Act: Include unknown capability
        override = await use_case.assign_to_node(
            workflow_id="workflow-1",
            node_id="node-1",
            robot_id=None,
            required_capabilities=["gpu", "unknown_capability", "browser"],
        )

        # Assert: Unknown ignored, known kept
        assert RobotCapability.GPU in override.required_capabilities
        assert RobotCapability.BROWSER in override.required_capabilities
        # Unknown was logged and skipped

    @pytest.mark.asyncio
    async def test_assign_with_empty_list_capabilities_raises_error(
        self,
        mock_robot_repository: AsyncMock,
        mock_assignment_repository: AsyncMock,
        mock_override_repository: AsyncMock,
    ) -> None:
        """Assign node with empty capabilities list - raises InvalidAssignmentError."""
        use_case = AssignRobotUseCase(
            robot_repository=mock_robot_repository,
            assignment_repository=mock_assignment_repository,
            override_repository=mock_override_repository,
        )

        # Act & Assert
        with pytest.raises(
            InvalidAssignmentError,
            match="Must specify either robot_id or required_capabilities",
        ):
            await use_case.assign_to_node(
                workflow_id="workflow-1",
                node_id="node-1",
                robot_id=None,
                required_capabilities=[],
            )
