"""Local robot repository implementation."""

from typing import List, Optional

from casare_rpa.domain.orchestrator.entities import Robot, RobotStatus
from casare_rpa.domain.orchestrator.repositories import RobotRepository
from .local_storage_repository import LocalStorageRepository


class LocalRobotRepository(RobotRepository):
    """Local storage implementation of RobotRepository."""

    def __init__(self, storage: LocalStorageRepository):
        self._storage = storage

    async def get_by_id(self, robot_id: str) -> Optional[Robot]:
        """Get robot by ID."""
        robots = self._storage.get_robots()
        for r in robots:
            if r["id"] == robot_id:
                return Robot.from_dict(r)
        return None

    async def get_all(self) -> List[Robot]:
        """Get all robots."""
        robots = self._storage.get_robots()
        return [Robot.from_dict(r) for r in robots]

    async def get_all_online(self) -> List[Robot]:
        """Get all online robots."""
        robots = self._storage.get_robots()
        return [
            Robot.from_dict(r)
            for r in robots
            if r.get("status") == RobotStatus.ONLINE.value
        ]

    async def get_by_environment(self, environment: str) -> List[Robot]:
        """Get robots in specific environment."""
        robots = self._storage.get_robots()
        return [
            Robot.from_dict(r) for r in robots if r.get("environment") == environment
        ]

    async def save(self, robot: Robot) -> None:
        """Save or update robot."""
        robot_dict = robot.to_dict()
        self._storage.save_robot(robot_dict)

    async def delete(self, robot_id: str) -> None:
        """Delete robot by ID."""
        self._storage.delete_robot(robot_id)

    async def update_status(self, robot_id: str, status: RobotStatus) -> None:
        """Update robot status."""
        robot = await self.get_by_id(robot_id)
        if robot:
            robot.status = status
            await self.save(robot)
