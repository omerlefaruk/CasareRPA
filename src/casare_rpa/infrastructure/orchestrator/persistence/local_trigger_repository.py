"""Local trigger repository implementation."""

from typing import List, Optional

from casare_rpa.domain.orchestrator.repositories import TriggerRepository
from casare_rpa.infrastructure.orchestrator.persistence.local_storage_repository import (
    LocalStorageRepository,
)
from casare_rpa.triggers.base import BaseTriggerConfig, TriggerType


class LocalTriggerRepository(TriggerRepository):
    """Local storage implementation of TriggerRepository."""

    def __init__(self, storage: LocalStorageRepository):
        self._storage = storage

    async def get_by_id(self, trigger_id: str) -> Optional[BaseTriggerConfig]:
        """Get trigger by ID."""
        triggers = self._storage.get_triggers()
        for t in triggers:
            if t["id"] == trigger_id:
                return BaseTriggerConfig.from_dict(t)
        return None

    async def get_all(self) -> List[BaseTriggerConfig]:
        """Get all triggers."""
        triggers = self._storage.get_triggers()
        return [BaseTriggerConfig.from_dict(t) for t in triggers]

    async def get_enabled(self) -> List[BaseTriggerConfig]:
        """Get all enabled triggers."""
        triggers = self._storage.get_triggers()
        return [BaseTriggerConfig.from_dict(t) for t in triggers if t.get("enabled", True)]

    async def get_by_scenario(self, scenario_id: str) -> List[BaseTriggerConfig]:
        """Get all triggers for a scenario."""
        triggers = self._storage.get_triggers()
        return [
            BaseTriggerConfig.from_dict(t) for t in triggers if t.get("scenario_id") == scenario_id
        ]

    async def get_by_workflow(self, workflow_id: str) -> List[BaseTriggerConfig]:
        """Get all triggers for a workflow."""
        triggers = self._storage.get_triggers()
        return [
            BaseTriggerConfig.from_dict(t) for t in triggers if t.get("workflow_id") == workflow_id
        ]

    async def get_by_type(self, trigger_type: TriggerType) -> List[BaseTriggerConfig]:
        """Get all triggers of a specific type."""
        triggers = self._storage.get_triggers()
        return [
            BaseTriggerConfig.from_dict(t)
            for t in triggers
            if t.get("trigger_type") == trigger_type.value
        ]

    async def save(self, trigger: BaseTriggerConfig) -> None:
        """Save or update trigger."""
        trigger_dict = trigger.to_dict()
        self._storage.save_trigger(trigger_dict)

    async def delete(self, trigger_id: str) -> None:
        """Delete trigger by ID."""
        self._storage.delete_trigger(trigger_id)

    async def delete_by_scenario(self, scenario_id: str) -> int:
        """Delete all triggers for a scenario. Returns count deleted."""
        return self._storage.delete_triggers_by_scenario(scenario_id)
