"""Trigger repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from casare_rpa.triggers.base import BaseTriggerConfig, TriggerType


class TriggerRepository(ABC):
    """Repository interface for Trigger aggregate."""

    @abstractmethod
    async def get_by_id(self, trigger_id: str) -> Optional[BaseTriggerConfig]:
        """Get trigger by ID."""
        pass

    @abstractmethod
    async def get_all(self) -> List[BaseTriggerConfig]:
        """Get all triggers."""
        pass

    @abstractmethod
    async def get_enabled(self) -> List[BaseTriggerConfig]:
        """Get all enabled triggers."""
        pass

    @abstractmethod
    async def get_by_scenario(self, scenario_id: str) -> List[BaseTriggerConfig]:
        """Get all triggers for a scenario."""
        pass

    @abstractmethod
    async def get_by_workflow(self, workflow_id: str) -> List[BaseTriggerConfig]:
        """Get all triggers for a workflow."""
        pass

    @abstractmethod
    async def get_by_type(self, trigger_type: TriggerType) -> List[BaseTriggerConfig]:
        """Get all triggers of a specific type."""
        pass

    @abstractmethod
    async def save(self, trigger: BaseTriggerConfig) -> None:
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
