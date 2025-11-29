"""Local workflow repository implementation."""

from typing import List, Optional

from casare_rpa.domain.orchestrator.entities import Workflow, WorkflowStatus
from casare_rpa.domain.orchestrator.repositories import WorkflowRepository
from .local_storage_repository import LocalStorageRepository


class LocalWorkflowRepository(WorkflowRepository):
    """Local storage implementation of WorkflowRepository."""

    def __init__(self, storage: LocalStorageRepository):
        self._storage = storage

    async def get_by_id(self, workflow_id: str) -> Optional[Workflow]:
        """Get workflow by ID."""
        workflows = self._storage.get_workflows()
        for w in workflows:
            if w["id"] == workflow_id:
                return Workflow.from_dict(w)
        return None

    async def get_all(self) -> List[Workflow]:
        """Get all workflows."""
        workflows = self._storage.get_workflows()
        return [Workflow.from_dict(w) for w in workflows]

    async def get_by_status(self, status: WorkflowStatus) -> List[Workflow]:
        """Get workflows by status."""
        workflows = self._storage.get_workflows()
        return [
            Workflow.from_dict(w) for w in workflows if w.get("status") == status.value
        ]

    async def save(self, workflow: Workflow) -> None:
        """Save or update workflow."""
        workflow_dict = workflow.to_dict()
        self._storage.save_workflow(workflow_dict)

    async def delete(self, workflow_id: str) -> None:
        """Delete workflow by ID."""
        self._storage.delete_workflow(workflow_id)
