"""
CQRS Query Service for Workflows.

Read-optimized query service that bypasses domain model for performance.
This is the Query side of CQRS - returns DTOs directly from storage.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from loguru import logger


@dataclass
class WorkflowListItemDTO:
    """
    Read-optimized DTO for workflow list display.

    Contains only the fields needed for listing workflows,
    avoiding the overhead of loading full domain entities.
    """

    id: str
    name: str
    node_count: int
    last_modified: Optional[datetime]
    description: str = ""


@dataclass
class WorkflowFilter:
    """Filter criteria for workflow queries."""

    name_contains: Optional[str] = None
    modified_after: Optional[datetime] = None
    modified_before: Optional[datetime] = None
    limit: int = 100
    offset: int = 0


class WorkflowQueryService:
    """
    Read-optimized query service for workflows.

    Bypasses domain model for performance on read operations.
    This is the Query side of CQRS - designed for fast reads
    without domain validation or business rules.

    Usage:
        service = WorkflowQueryService(Path("./workflows"))
        workflows = await service.list_workflows(WorkflowFilter(limit=10))
    """

    def __init__(self, storage_path: Path) -> None:
        """
        Initialize query service.

        Args:
            storage_path: Path to workflow storage directory
        """
        self._storage_path = storage_path

    async def list_workflows(
        self,
        filter: Optional[WorkflowFilter] = None,
    ) -> List[WorkflowListItemDTO]:
        """
        List workflows with optional filtering.

        Reads workflow metadata directly from storage without
        loading full domain entities for better performance.

        Args:
            filter: Optional filter criteria

        Returns:
            List of workflow DTOs matching the filter
        """
        filter = filter or WorkflowFilter()
        result: List[WorkflowListItemDTO] = []

        try:
            if not self._storage_path.exists():
                logger.debug(f"Storage path does not exist: {self._storage_path}")
                return result

            # Scan workflow files
            workflow_files = list(self._storage_path.glob("*.json"))

            for workflow_file in workflow_files:
                try:
                    dto = await self._read_workflow_summary(workflow_file)
                    if dto and self._matches_filter(dto, filter):
                        result.append(dto)
                except Exception as e:
                    logger.warning(f"Failed to read workflow {workflow_file}: {e}")
                    continue

            # Sort by last_modified descending (most recent first)
            result.sort(
                key=lambda w: w.last_modified or datetime.min,
                reverse=True,
            )

            # Apply pagination
            start = filter.offset
            end = filter.offset + filter.limit
            return result[start:end]

        except Exception as e:
            logger.error(f"Failed to list workflows: {e}")
            return []

    async def get_workflow_summary(
        self,
        workflow_id: str,
    ) -> Optional[WorkflowListItemDTO]:
        """
        Get summary info for a single workflow.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Workflow DTO or None if not found
        """
        try:
            workflow_file = self._storage_path / f"{workflow_id}.json"
            if not workflow_file.exists():
                # Try searching by ID in file content
                return await self._find_workflow_by_id(workflow_id)

            return await self._read_workflow_summary(workflow_file)

        except Exception as e:
            logger.error(f"Failed to get workflow summary {workflow_id}: {e}")
            return None

    async def search_workflows(
        self,
        query: str,
    ) -> List[WorkflowListItemDTO]:
        """
        Full-text search across workflow names and descriptions.

        Args:
            query: Search query string

        Returns:
            List of matching workflow DTOs
        """
        if not query or not query.strip():
            return await self.list_workflows()

        query_lower = query.lower().strip()
        result: List[WorkflowListItemDTO] = []

        try:
            if not self._storage_path.exists():
                return result

            workflow_files = list(self._storage_path.glob("*.json"))

            for workflow_file in workflow_files:
                try:
                    dto = await self._read_workflow_summary(workflow_file)
                    if dto and self._matches_search(dto, query_lower):
                        result.append(dto)
                except Exception as e:
                    logger.warning(f"Failed to search workflow {workflow_file}: {e}")
                    continue

            # Sort by relevance (name match first, then description)
            result.sort(
                key=lambda w: (
                    0 if query_lower in w.name.lower() else 1,
                    w.name.lower(),
                ),
            )

            return result

        except Exception as e:
            logger.error(f"Failed to search workflows: {e}")
            return []

    async def _read_workflow_summary(
        self,
        workflow_file: Path,
    ) -> Optional[WorkflowListItemDTO]:
        """
        Read workflow summary from file.

        Extracts only the fields needed for display,
        without parsing the full workflow structure.
        """
        try:
            with open(workflow_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            metadata = data.get("metadata", {})
            if not isinstance(metadata, dict):
                metadata = {}

            # Extract workflow ID
            workflow_id = workflow_file.stem

            # Extract name (with fallback to filename)
            name = metadata.get("name", workflow_file.stem)

            # Count nodes
            nodes = data.get("nodes", {})
            node_count = len(nodes) if isinstance(nodes, dict) else 0

            # Parse last modified
            last_modified = None
            modified_str = metadata.get("modified_at")
            if modified_str:
                try:
                    last_modified = datetime.fromisoformat(modified_str.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    pass

            # Fallback to file modification time
            if last_modified is None:
                last_modified = datetime.fromtimestamp(workflow_file.stat().st_mtime)

            # Extract description
            description = metadata.get("description", "")

            return WorkflowListItemDTO(
                id=workflow_id,
                name=name,
                node_count=node_count,
                last_modified=last_modified,
                description=description,
            )

        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in workflow file {workflow_file}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Failed to read workflow file {workflow_file}: {e}")
            return None

    async def _find_workflow_by_id(
        self,
        workflow_id: str,
    ) -> Optional[WorkflowListItemDTO]:
        """Find workflow by searching ID in file contents."""
        try:
            workflow_files = list(self._storage_path.glob("*.json"))

            for workflow_file in workflow_files:
                try:
                    with open(workflow_file, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    if data.get("id") == workflow_id:
                        return await self._read_workflow_summary(workflow_file)
                except Exception:
                    continue

            return None

        except Exception as e:
            logger.error(f"Failed to find workflow by ID {workflow_id}: {e}")
            return None

    def _matches_filter(
        self,
        dto: WorkflowListItemDTO,
        filter: WorkflowFilter,
    ) -> bool:
        """Check if workflow matches filter criteria."""
        # Name contains filter
        if filter.name_contains:
            if filter.name_contains.lower() not in dto.name.lower():
                return False

        # Modified after filter
        if filter.modified_after and dto.last_modified:
            if dto.last_modified < filter.modified_after:
                return False

        # Modified before filter
        if filter.modified_before and dto.last_modified:
            if dto.last_modified > filter.modified_before:
                return False

        return True

    def _matches_search(
        self,
        dto: WorkflowListItemDTO,
        query_lower: str,
    ) -> bool:
        """Check if workflow matches search query."""
        if query_lower in dto.name.lower():
            return True
        if query_lower in dto.description.lower():
            return True
        return False
