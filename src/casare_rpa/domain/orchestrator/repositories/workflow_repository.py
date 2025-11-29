"""Workflow repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from casare_rpa.domain.orchestrator.entities import Workflow, WorkflowStatus


class WorkflowRepository(ABC):
    """Repository interface for Workflow aggregate."""

    @abstractmethod
    async def get_by_id(self, workflow_id: str) -> Optional[Workflow]:
        """Get workflow by ID."""
        pass

    @abstractmethod
    async def get_all(self) -> List[Workflow]:
        """Get all workflows."""
        pass

    @abstractmethod
    async def get_by_status(self, status: WorkflowStatus) -> List[Workflow]:
        """Get workflows by status."""
        pass

    @abstractmethod
    async def save(self, workflow: Workflow) -> None:
        """Save or update workflow."""
        pass

    @abstractmethod
    async def delete(self, workflow_id: str) -> None:
        """Delete workflow by ID."""
        pass
