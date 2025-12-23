"""Trigger repository interface."""

from abc import ABC, abstractmethod

from casare_rpa.domain.entities.trigger_config import TriggerConfig
from casare_rpa.domain.value_objects.trigger_types import TriggerType


class TriggerRepository(ABC):
    """Repository interface for Trigger aggregate."""

    @abstractmethod
    async def get_by_id(self, trigger_id: str) -> TriggerConfig | None:
        """Get trigger by ID."""
        pass

    @abstractmethod
    async def get_all(self) -> list[TriggerConfig]:
        """Get all triggers."""
        pass

    @abstractmethod
    async def get_enabled(self) -> list[TriggerConfig]:
        """Get all enabled triggers."""
        pass

    @abstractmethod
    async def get_by_scenario(self, scenario_id: str) -> list[TriggerConfig]:
        """Get all triggers for a scenario."""
        pass

    @abstractmethod
    async def get_by_workflow(self, workflow_id: str) -> list[TriggerConfig]:
        """Get all triggers for a workflow."""
        pass

    @abstractmethod
    async def get_by_type(self, trigger_type: TriggerType) -> list[TriggerConfig]:
        """Get all triggers of a specific type."""
        pass

    @abstractmethod
    async def save(self, trigger: TriggerConfig) -> None:
        """Save or update trigger."""
        pass

    @abstractmethod
    async def delete(self, trigger_id: str) -> None:
        """Delete trigger by ID."""
        pass

    @abstractmethod
    async def delete_by_scenario(self, scenario_id: str) -> int:
        """Delete all triggers for a scenario. Returns count deleted."""
        pass
