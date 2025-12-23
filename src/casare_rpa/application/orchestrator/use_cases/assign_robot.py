"""AssignRobotUseCase - Assign robots to workflows and nodes.

This use case manages the relationship between robots and workflows:
- Assign default robots to workflows
- Create node-level robot overrides for specific routing
- Remove assignments and overrides
"""

from datetime import datetime

from loguru import logger

from casare_rpa.domain.orchestrator.entities.robot import RobotCapability
from casare_rpa.domain.orchestrator.errors import (
    InvalidAssignmentError,
    RobotNotFoundError,
)
from casare_rpa.domain.orchestrator.value_objects.node_robot_override import (
    NodeRobotOverride,
)
from casare_rpa.domain.orchestrator.value_objects.robot_assignment import (
    RobotAssignment,
)
from casare_rpa.infrastructure.persistence.repositories import (
    NodeOverrideRepository,
    RobotRepository,
    WorkflowAssignmentRepository,
)


class AssignRobotUseCase:
    """Use case for assigning robots to workflows and nodes.

    Provides operations for:
    - Assigning a robot as the default for a workflow
    - Creating node-level robot overrides
    - Removing workflow assignments
    - Removing node overrides

    All operations validate that referenced robots exist before creating
    assignments or overrides.
    """

    def __init__(
        self,
        robot_repository: RobotRepository,
        assignment_repository: WorkflowAssignmentRepository,
        override_repository: NodeOverrideRepository,
    ) -> None:
        """Initialize use case with repositories.

        Args:
            robot_repository: Repository for robot data.
            assignment_repository: Repository for workflow assignments.
            override_repository: Repository for node overrides.
        """
        self._robot_repo = robot_repository
        self._assignment_repo = assignment_repository
        self._override_repo = override_repository

    async def assign_to_workflow(
        self,
        workflow_id: str,
        robot_id: str,
        is_default: bool = True,
        priority: int = 0,
        notes: str | None = None,
        created_by: str = "",
    ) -> RobotAssignment:
        """Assign a robot as the default for a workflow.

        Args:
            workflow_id: ID of the workflow to assign.
            robot_id: ID of the robot to assign.
            is_default: Whether this is the default robot for the workflow.
            priority: Assignment priority (higher = preferred).
            notes: Optional notes about the assignment.
            created_by: User/system making the assignment.

        Returns:
            Created RobotAssignment.

        Raises:
            RobotNotFoundError: If the robot doesn't exist.
            InvalidAssignmentError: If assignment parameters are invalid.
        """
        logger.info(f"Assigning robot {robot_id} to workflow {workflow_id}")

        # Validate inputs
        if not workflow_id or not workflow_id.strip():
            raise InvalidAssignmentError("workflow_id cannot be empty")
        if not robot_id or not robot_id.strip():
            raise InvalidAssignmentError("robot_id cannot be empty")

        # Verify robot exists
        robot = await self._robot_repo.get_by_id(robot_id)
        if not robot:
            raise RobotNotFoundError(f"Robot {robot_id} not found")

        # Create assignment
        assignment = RobotAssignment(
            workflow_id=workflow_id,
            robot_id=robot_id,
            is_default=is_default,
            priority=priority,
            created_at=datetime.utcnow(),
            created_by=created_by,
            notes=notes,
        )

        # Save assignment
        await self._assignment_repo.save(assignment)
        logger.info(
            f"Robot {robot_id} assigned to workflow {workflow_id} "
            f"(default={is_default}, priority={priority})"
        )

        return assignment

    async def assign_to_node(
        self,
        workflow_id: str,
        node_id: str,
        robot_id: str | None = None,
        required_capabilities: list[str] | None = None,
        reason: str | None = None,
        created_by: str = "",
    ) -> NodeRobotOverride:
        """Create a node-level robot override.

        This allows specific nodes within a workflow to run on different
        robots than the workflow's default. Useful for:
        - Nodes requiring specific capabilities (GPU, desktop automation)
        - Load balancing specific heavy operations
        - Routing sensitive operations to secure robots

        Args:
            workflow_id: ID of the workflow containing the node.
            node_id: ID of the node to override.
            robot_id: Specific robot to use (None = use capability matching).
            required_capabilities: Required capabilities if robot_id is None.
            reason: Human-readable explanation for the override.
            created_by: User/system creating the override.

        Returns:
            Created NodeRobotOverride.

        Raises:
            RobotNotFoundError: If specified robot doesn't exist.
            InvalidAssignmentError: If both robot_id and capabilities are None,
                or if parameters are invalid.
        """
        logger.info(f"Creating node override for {workflow_id}/{node_id}")

        # Validate inputs
        if not workflow_id or not workflow_id.strip():
            raise InvalidAssignmentError("workflow_id cannot be empty")
        if not node_id or not node_id.strip():
            raise InvalidAssignmentError("node_id cannot be empty")
        if robot_id is None and not required_capabilities:
            raise InvalidAssignmentError("Must specify either robot_id or required_capabilities")

        # Verify robot exists if specified
        if robot_id:
            robot = await self._robot_repo.get_by_id(robot_id)
            if not robot:
                raise RobotNotFoundError(f"Robot {robot_id} not found")

        # Parse capabilities
        capabilities: set[RobotCapability] = set()
        if required_capabilities:
            for cap_str in required_capabilities:
                try:
                    capabilities.add(RobotCapability(cap_str))
                except ValueError:
                    logger.warning(f"Unknown capability: {cap_str}")

        # Create override
        override = NodeRobotOverride(
            workflow_id=workflow_id,
            node_id=node_id,
            robot_id=robot_id,
            required_capabilities=frozenset(capabilities),
            reason=reason,
            created_at=datetime.utcnow(),
            created_by=created_by,
            is_active=True,
        )

        # Save override
        await self._override_repo.save(override)
        logger.info(f"Node override created for {workflow_id}/{node_id}")

        return override

    async def remove_workflow_assignment(
        self,
        workflow_id: str,
        robot_id: str,
    ) -> bool:
        """Remove a workflow-robot assignment.

        Args:
            workflow_id: ID of the workflow.
            robot_id: ID of the robot to unassign.

        Returns:
            True if assignment was removed, False if not found.
        """
        logger.info(f"Removing assignment: workflow={workflow_id}, robot={robot_id}")

        deleted = await self._assignment_repo.delete(workflow_id, robot_id)

        if deleted:
            logger.info(f"Assignment removed: workflow={workflow_id}, robot={robot_id}")
        else:
            logger.warning(f"Assignment not found: workflow={workflow_id}, robot={robot_id}")

        return deleted

    async def remove_node_override(
        self,
        workflow_id: str,
        node_id: str,
    ) -> bool:
        """Remove a node-level robot override.

        Args:
            workflow_id: ID of the workflow.
            node_id: ID of the node.

        Returns:
            True if override was removed, False if not found.
        """
        logger.info(f"Removing node override: workflow={workflow_id}, node={node_id}")

        deleted = await self._override_repo.delete(workflow_id, node_id)

        if deleted:
            logger.info(f"Override removed: workflow={workflow_id}, node={node_id}")
        else:
            logger.warning(f"Override not found: workflow={workflow_id}, node={node_id}")

        return deleted

    async def deactivate_node_override(
        self,
        workflow_id: str,
        node_id: str,
    ) -> bool:
        """Deactivate a node override (soft delete).

        Unlike remove_node_override, this keeps the override in the database
        but marks it as inactive. Can be reactivated later.

        Args:
            workflow_id: ID of the workflow.
            node_id: ID of the node.

        Returns:
            True if override was deactivated, False if not found.
        """
        logger.info(f"Deactivating node override: workflow={workflow_id}, node={node_id}")

        return await self._override_repo.deactivate(workflow_id, node_id)

    async def activate_node_override(
        self,
        workflow_id: str,
        node_id: str,
    ) -> bool:
        """Reactivate a previously deactivated node override.

        Args:
            workflow_id: ID of the workflow.
            node_id: ID of the node.

        Returns:
            True if override was activated, False if not found.
        """
        logger.info(f"Activating node override: workflow={workflow_id}, node={node_id}")

        return await self._override_repo.activate(workflow_id, node_id)

    async def get_workflow_assignments(
        self,
        workflow_id: str,
    ) -> list[RobotAssignment]:
        """Get all robot assignments for a workflow.

        Args:
            workflow_id: ID of the workflow.

        Returns:
            List of RobotAssignment objects.
        """
        return await self._assignment_repo.get_by_workflow(workflow_id)

    async def get_node_overrides(
        self,
        workflow_id: str,
    ) -> list[NodeRobotOverride]:
        """Get all node overrides for a workflow.

        Args:
            workflow_id: ID of the workflow.

        Returns:
            List of NodeRobotOverride objects.
        """
        return await self._override_repo.get_by_workflow(workflow_id)

    async def get_active_node_overrides(
        self,
        workflow_id: str,
    ) -> list[NodeRobotOverride]:
        """Get only active node overrides for a workflow.

        Args:
            workflow_id: ID of the workflow.

        Returns:
            List of active NodeRobotOverride objects.
        """
        return await self._override_repo.get_active_for_workflow(workflow_id)

    async def set_default_robot(
        self,
        workflow_id: str,
        robot_id: str,
    ) -> None:
        """Set a specific robot as the default for a workflow.

        If an assignment already exists, updates it to be the default.
        Unsets any other default assignments for the workflow.

        Args:
            workflow_id: ID of the workflow.
            robot_id: ID of the robot to set as default.

        Raises:
            RobotNotFoundError: If robot doesn't exist.
        """
        logger.info(f"Setting default robot for workflow {workflow_id}: {robot_id}")

        # Verify robot exists
        robot = await self._robot_repo.get_by_id(robot_id)
        if not robot:
            raise RobotNotFoundError(f"Robot {robot_id} not found")

        # Check if assignment already exists
        existing = await self._assignment_repo.get_assignment(workflow_id, robot_id)

        if existing:
            # Update to make it the default
            await self._assignment_repo.set_default(workflow_id, robot_id)
        else:
            # Create new assignment as default
            await self.assign_to_workflow(
                workflow_id=workflow_id,
                robot_id=robot_id,
                is_default=True,
            )

        logger.info(f"Robot {robot_id} set as default for workflow {workflow_id}")

    async def unassign_robot_from_all_workflows(
        self,
        robot_id: str,
    ) -> int:
        """Remove a robot from all workflow assignments.

        Useful when decommissioning a robot.

        Args:
            robot_id: ID of the robot to unassign.

        Returns:
            Number of assignments removed.
        """
        logger.info(f"Unassigning robot {robot_id} from all workflows")

        count = await self._assignment_repo.delete_all_for_robot(robot_id)
        logger.info(f"Removed {count} workflow assignments for robot {robot_id}")

        return count

    async def remove_all_node_overrides_for_robot(
        self,
        robot_id: str,
    ) -> int:
        """Remove all node overrides targeting a specific robot.

        Useful when decommissioning a robot.

        Args:
            robot_id: ID of the robot.

        Returns:
            Number of overrides removed.
        """
        logger.info(f"Removing all node overrides for robot {robot_id}")

        count = await self._override_repo.delete_all_for_robot(robot_id)
        logger.info(f"Removed {count} node overrides for robot {robot_id}")

        return count


__all__ = ["AssignRobotUseCase"]
