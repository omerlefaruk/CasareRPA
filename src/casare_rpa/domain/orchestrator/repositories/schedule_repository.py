"""Schedule repository interface."""

from abc import ABC, abstractmethod

from casare_rpa.domain.orchestrator.entities import Schedule


class ScheduleRepository(ABC):
    """Repository interface for Schedule aggregate."""

    @abstractmethod
    async def get_by_id(self, schedule_id: str) -> Schedule | None:
        """Get schedule by ID."""
        pass

    @abstractmethod
    async def get_all(self) -> list[Schedule]:
        """Get all schedules."""
        pass

    @abstractmethod
    async def get_enabled(self) -> list[Schedule]:
        """Get all enabled schedules."""
        pass

    @abstractmethod
    async def save(self, schedule: Schedule) -> None:
        """Save or update schedule."""
        pass

    @abstractmethod
    async def delete(self, schedule_id: str) -> None:
        """Delete schedule by ID."""
        pass
