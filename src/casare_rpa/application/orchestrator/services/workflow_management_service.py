"""
Workflow management service.
Handles workflow CRUD operations and file imports.
"""

import os
import asyncio
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from loguru import logger
from dotenv import load_dotenv

from casare_rpa.domain.orchestrator.entities import Workflow, WorkflowStatus
from casare_rpa.domain.orchestrator.repositories import WorkflowRepository

load_dotenv()


class WorkflowManagementService:
    """Service for managing workflows."""

    def __init__(self, workflow_repository: WorkflowRepository):
        """Initialize with injected repository."""
        self._workflow_repository = workflow_repository
        self._supabase_url = os.getenv("SUPABASE_URL")
        self._supabase_key = os.getenv("SUPABASE_KEY")
        self._client = None
        self._connected = False
        self._use_local = True  # Default to local mode

    @property
    def is_cloud_mode(self) -> bool:
        """Check if using cloud (Supabase) mode."""
        return self._connected and not self._use_local

    async def connect(self) -> bool:
        """Connect to Supabase or fall back to local storage."""
        if not self._supabase_url or not self._supabase_key:
            logger.warning("Supabase credentials not found. Using local storage mode.")
            self._use_local = True
            return True

        try:
            from supabase import create_client

            logger.info("Connecting to Supabase...")
            self._client = create_client(self._supabase_url, self._supabase_key)
            self._connected = True
            self._use_local = False
            logger.info("Connected to Supabase successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}. Using local storage.")
            self._use_local = True
            return True

    async def get_workflows(
        self, status: Optional[WorkflowStatus] = None
    ) -> List[Workflow]:
        """Get all workflows."""
        if self._use_local:
            if status:
                return await self._workflow_repository.get_by_status(status)
            return await self._workflow_repository.get_all()
        else:
            try:
                query = self._client.table("workflows").select("*")
                if status:
                    query = query.eq("status", status.value)
                query = query.order("updated_at", desc=True)
                response = await asyncio.to_thread(lambda: query.execute())
                data = response.data
            except Exception as e:
                logger.error(f"Failed to fetch workflows: {e}")
                data = []

        return [Workflow.from_dict(w) for w in data]

    async def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get a specific workflow by ID."""
        workflows = await self.get_workflows()
        for w in workflows:
            if w.id == workflow_id:
                return w
        return None

    async def save_workflow(self, workflow: Workflow) -> bool:
        """Save or update a workflow."""
        now = datetime.now(timezone.utc).isoformat()
        data = {
            "id": workflow.id,
            "name": workflow.name,
            "description": workflow.description,
            "json_definition": workflow.json_definition,
            "version": workflow.version,
            "status": workflow.status.value,
            "created_by": workflow.created_by,
            "created_at": workflow.created_at or now,
            "updated_at": now,
            "tags": workflow.tags,
        }

        if self._use_local:
            workflow_entity = Workflow.from_dict(data)
            await self._workflow_repository.save(workflow_entity)
            return True
        else:
            try:
                await asyncio.to_thread(
                    lambda: self._client.table("workflows").upsert(data).execute()
                )
                return True
            except Exception as e:
                logger.error(f"Failed to save workflow: {e}")
                return False

    async def import_workflow_from_file(self, file_path: Path) -> Optional[Workflow]:
        """Import a workflow from a JSON file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                json_content = f.read()
                workflow_data = json.loads(json_content)

            workflow = Workflow(
                id=str(uuid.uuid4()),
                name=workflow_data.get("name", file_path.stem),
                description=workflow_data.get(
                    "description", f"Imported from {file_path.name}"
                ),
                json_definition=json_content,
                version=1,
                status=WorkflowStatus.DRAFT,
                created_at=datetime.now(timezone.utc).isoformat(),
            )

            if await self.save_workflow(workflow):
                return workflow
        except Exception as e:
            logger.error(f"Failed to import workflow from {file_path}: {e}")
        return None

    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow."""
        if self._use_local:
            await self._workflow_repository.delete(workflow_id)
            return True
        else:
            try:
                await asyncio.to_thread(
                    lambda: self._client.table("workflows")
                    .delete()
                    .eq("id", workflow_id)
                    .execute()
                )
                return True
            except Exception as e:
                logger.error(f"Failed to delete workflow: {e}")
                return False
