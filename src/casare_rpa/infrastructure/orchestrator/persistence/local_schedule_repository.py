"""Local schedule repository implementation."""

from typing import List, Optional

from casare_rpa.domain.orchestrator.entities import Schedule
from casare_rpa.domain.orchestrator.repositories import ScheduleRepository
from .local_storage_repository import LocalStorageRepository


class LocalScheduleRepository(ScheduleRepository):
    """Local storage implementation of ScheduleRepository."""

    def __init__(self, storage: LocalStorageRepository):
        self._storage = storage

    async def get_by_id(self, schedule_id: str) -> Optional[Schedule]:
        """Get schedule by ID."""
        schedules = self._storage.get_schedules()
        for s in schedules:
            if s["id"] == schedule_id:
                return Schedule.from_dict(s)
        return None

    async def get_all(self) -> List[Schedule]:
        """Get all schedules."""
        schedules = self._storage.get_schedules()
        return [Schedule.from_dict(s) for s in schedules]

    async def get_enabled(self) -> List[Schedule]:
        """Get all enabled schedules."""
        schedules = self._storage.get_schedules()
        return [Schedule.from_dict(s) for s in schedules if s.get("enabled", True)]

    async def save(self, schedule: Schedule) -> None:
        """Save or update schedule."""
        schedule_dict = schedule.to_dict()
        self._storage.save_schedule(schedule_dict)

    async def delete(self, schedule_id: str) -> None:
        """Delete schedule by ID."""
        self._storage.delete_schedule(schedule_id)
