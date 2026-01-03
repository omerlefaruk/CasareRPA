"""Node override repository interface."""

from abc import ABC, abstractmethod

from casare_rpa.domain.orchestrator.entities.robot import RobotCapability
from casare_rpa.domain.orchestrator.value_objects.node_robot_override import (
    NodeRobotOverride,
)


class NodeOverrideRepository(ABC):
    """Repository interface for NodeRobotOverride persistence."""

    @abstractmethod
    async def save(self, override: NodeRobotOverride) -> NodeRobotOverride:
        """Save or update a node override."""

    @abstractmethod
    async def get_by_workflow(self, workflow_id: str) -> list[NodeRobotOverride]:
        """Get all overrides for a workflow."""

    @abstractmethod
    async def get_by_node(self, workflow_id: str, node_id: str) -> NodeRobotOverride | None:
        """Get override for a specific workflow node."""

    @abstractmethod
    async def get_active_for_workflow(self, workflow_id: str) -> list[NodeRobotOverride]:
        """Get active overrides for a workflow."""

    @abstractmethod
    async def get_by_robot(self, robot_id: str) -> list[NodeRobotOverride]:
        """Get overrides that reference a given robot."""

    @abstractmethod
    async def get_by_capability(self, capability: RobotCapability) -> list[NodeRobotOverride]:
        """Get overrides filtered by robot capability."""

    @abstractmethod
    async def delete(self, workflow_id: str, node_id: str) -> bool:
        """Delete a specific override."""

    @abstractmethod
    async def deactivate(self, workflow_id: str, node_id: str) -> bool:
        """Deactivate a specific override."""

    @abstractmethod
    async def activate(self, workflow_id: str, node_id: str) -> bool:
        """Activate a specific override."""

    @abstractmethod
    async def delete_all_for_workflow(self, workflow_id: str) -> int:
        """Delete all overrides for a workflow. Returns deleted count."""

    @abstractmethod
    async def delete_all_for_robot(self, robot_id: str) -> int:
        """Delete all overrides that reference a robot. Returns deleted count."""

    @abstractmethod
    async def get_override_map(self, workflow_id: str) -> dict[str, NodeRobotOverride]:
        """Get node_id -> override mapping for quick lookup."""
