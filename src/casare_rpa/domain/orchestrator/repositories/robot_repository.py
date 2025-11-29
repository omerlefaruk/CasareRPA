"""Robot repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from casare_rpa.domain.orchestrator.entities import Robot, RobotStatus


class RobotRepository(ABC):
    """Repository interface for Robot aggregate."""

    @abstractmethod
    async def get_by_id(self, robot_id: str) -> Optional[Robot]:
        """Get robot by ID."""
        pass

    @abstractmethod
    async def get_all(self) -> List[Robot]:
        """Get all robots."""
        pass

    @abstractmethod
    async def get_all_online(self) -> List[Robot]:
        """Get all online robots."""
        pass

    @abstractmethod
    async def get_by_environment(self, environment: str) -> List[Robot]:
        """Get robots in specific environment."""
        pass

    @abstractmethod
    async def save(self, robot: Robot) -> None:
        """Save or update robot."""
        pass

    @abstractmethod
    async def delete(self, robot_id: str) -> None:
        """Delete robot by ID."""
        pass

    @abstractmethod
    async def update_status(self, robot_id: str, status: RobotStatus) -> None:
        """Update robot status."""
        pass
