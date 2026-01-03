"""Workflow assignment repository interface."""

from abc import ABC, abstractmethod

from casare_rpa.domain.orchestrator.value_objects.robot_assignment import RobotAssignment


class WorkflowAssignmentRepository(ABC):
    """Repository interface for RobotAssignment persistence."""

    @abstractmethod
    async def save(self, assignment: RobotAssignment) -> RobotAssignment:
        """Save or update a workflow assignment."""

    @abstractmethod
    async def get_by_workflow(self, workflow_id: str) -> list[RobotAssignment]:
        """Get all assignments for a workflow."""

    @abstractmethod
    async def get_default_for_workflow(self, workflow_id: str) -> RobotAssignment | None:
        """Get the default assignment for a workflow."""

    @abstractmethod
    async def get_by_robot(self, robot_id: str) -> list[RobotAssignment]:
        """Get all assignments for a robot."""

    @abstractmethod
    async def get_assignment(self, workflow_id: str, robot_id: str) -> RobotAssignment | None:
        """Get a specific assignment by workflow and robot."""

    @abstractmethod
    async def set_default(self, workflow_id: str, robot_id: str) -> None:
        """Mark a specific assignment as default for a workflow."""

    @abstractmethod
    async def delete(self, workflow_id: str, robot_id: str) -> bool:
        """Delete a specific assignment."""

    @abstractmethod
    async def delete_all_for_workflow(self, workflow_id: str) -> int:
        """Delete all assignments for a workflow. Returns deleted count."""

    @abstractmethod
    async def delete_all_for_robot(self, robot_id: str) -> int:
        """Delete all assignments for a robot. Returns deleted count."""

    @abstractmethod
    async def get_workflows_for_robot(self, robot_id: str) -> list[str]:
        """Get workflow IDs that a robot is assigned to."""
