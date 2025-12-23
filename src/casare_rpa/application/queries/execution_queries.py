"""
CQRS Query Service for Execution History.

Read-optimized query service for workflow execution logs.
Provides fast access to execution history without domain model overhead.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from loguru import logger


@dataclass
class ExecutionLogDTO:
    """
    Read-optimized DTO for execution history display.

    Contains summary information about a workflow execution,
    optimized for listing and reporting views.
    """

    execution_id: str
    workflow_id: str
    workflow_name: str
    started_at: datetime
    completed_at: Optional[datetime]
    status: str  # "running", "completed", "failed", "cancelled"
    nodes_executed: int
    error_message: Optional[str] = None


@dataclass
class ExecutionFilter:
    """Filter criteria for execution queries."""

    workflow_id: Optional[str] = None
    status: Optional[str] = None
    started_after: Optional[datetime] = None
    started_before: Optional[datetime] = None
    limit: int = 20
    offset: int = 0


class ExecutionQueryService:
    """
    Read-optimized query service for execution history.

    Provides fast access to execution logs without loading
    full domain entities. Designed for dashboard displays,
    reports, and audit trails.

    Usage:
        service = ExecutionQueryService(Path("./executions"))
        recent = await service.get_recent_executions(limit=10)
    """

    def __init__(self, storage_path: Path) -> None:
        """
        Initialize query service.

        Args:
            storage_path: Path to execution logs storage directory
        """
        self._storage_path = storage_path

    async def get_recent_executions(
        self,
        limit: int = 20,
    ) -> List[ExecutionLogDTO]:
        """
        Get recent workflow executions.

        Returns the most recent executions across all workflows,
        sorted by start time descending.

        Args:
            limit: Maximum number of executions to return

        Returns:
            List of recent execution DTOs
        """
        filter = ExecutionFilter(limit=limit)
        return await self._query_executions(filter)

    async def get_workflow_executions(
        self,
        workflow_id: str,
        limit: int = 10,
    ) -> List[ExecutionLogDTO]:
        """
        Get execution history for a specific workflow.

        Args:
            workflow_id: Workflow identifier
            limit: Maximum number of executions to return

        Returns:
            List of execution DTOs for the workflow
        """
        filter = ExecutionFilter(workflow_id=workflow_id, limit=limit)
        return await self._query_executions(filter)

    async def get_execution_by_id(
        self,
        execution_id: str,
    ) -> Optional[ExecutionLogDTO]:
        """
        Get a specific execution by ID.

        Args:
            execution_id: Execution identifier

        Returns:
            Execution DTO or None if not found
        """
        try:
            execution_file = self._storage_path / f"{execution_id}.json"
            if execution_file.exists():
                return await self._read_execution_log(execution_file)

            # Search by ID in file contents
            return await self._find_execution_by_id(execution_id)

        except Exception as e:
            logger.error(f"Failed to get execution {execution_id}: {e}")
            return None

    async def get_executions_by_status(
        self,
        status: str,
        limit: int = 20,
    ) -> List[ExecutionLogDTO]:
        """
        Get executions filtered by status.

        Args:
            status: Execution status ("running", "completed", "failed", "cancelled")
            limit: Maximum number of executions to return

        Returns:
            List of execution DTOs with the specified status
        """
        filter = ExecutionFilter(status=status, limit=limit)
        return await self._query_executions(filter)

    async def get_running_executions(self) -> List[ExecutionLogDTO]:
        """
        Get all currently running executions.

        Returns:
            List of running execution DTOs
        """
        return await self.get_executions_by_status("running", limit=100)

    async def _query_executions(
        self,
        filter: ExecutionFilter,
    ) -> List[ExecutionLogDTO]:
        """
        Query executions with filter criteria.

        Args:
            filter: Filter criteria

        Returns:
            List of matching execution DTOs
        """
        result: List[ExecutionLogDTO] = []

        try:
            if not self._storage_path.exists():
                logger.debug(f"Storage path does not exist: {self._storage_path}")
                return result

            # Scan execution log files
            execution_files = list(self._storage_path.glob("*.json"))

            for execution_file in execution_files:
                try:
                    dto = await self._read_execution_log(execution_file)
                    if dto and self._matches_filter(dto, filter):
                        result.append(dto)
                except Exception as e:
                    logger.warning(f"Failed to read execution {execution_file}: {e}")
                    continue

            # Sort by started_at descending (most recent first)
            result.sort(
                key=lambda e: e.started_at,
                reverse=True,
            )

            # Apply pagination
            start = filter.offset
            end = filter.offset + filter.limit
            return result[start:end]

        except Exception as e:
            logger.error(f"Failed to query executions: {e}")
            return []

    async def _read_execution_log(
        self,
        execution_file: Path,
    ) -> Optional[ExecutionLogDTO]:
        """
        Read execution log from file.

        Extracts only the fields needed for display.
        """
        try:
            with open(execution_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Extract required fields
            execution_id = data.get("execution_id") or data.get("id", execution_file.stem)
            workflow_id = data.get("workflow_id", "")
            workflow_name = data.get("workflow_name", "Unknown")

            # Parse timestamps
            started_at = self._parse_datetime(data.get("started_at") or data.get("start_time"))
            if started_at is None:
                started_at = datetime.fromtimestamp(execution_file.stat().st_ctime)

            completed_at = self._parse_datetime(data.get("completed_at") or data.get("end_time"))

            # Extract status
            status = data.get("status", "unknown")
            if isinstance(status, dict):
                status = status.get("value", "unknown")

            # Count executed nodes
            nodes_executed = data.get("nodes_executed", 0)
            if isinstance(nodes_executed, list):
                nodes_executed = len(nodes_executed)

            # Extract error message if present
            error_message = data.get("error_message") or data.get("error")

            return ExecutionLogDTO(
                execution_id=execution_id,
                workflow_id=workflow_id,
                workflow_name=workflow_name,
                started_at=started_at,
                completed_at=completed_at,
                status=status,
                nodes_executed=nodes_executed,
                error_message=error_message,
            )

        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in execution file {execution_file}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Failed to read execution file {execution_file}: {e}")
            return None

    async def _find_execution_by_id(
        self,
        execution_id: str,
    ) -> Optional[ExecutionLogDTO]:
        """Find execution by searching ID in file contents."""
        try:
            execution_files = list(self._storage_path.glob("*.json"))

            for execution_file in execution_files:
                try:
                    with open(execution_file, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    file_id = data.get("execution_id") or data.get("id")
                    if file_id == execution_id:
                        return await self._read_execution_log(execution_file)
                except Exception:
                    continue

            return None

        except Exception as e:
            logger.error(f"Failed to find execution by ID {execution_id}: {e}")
            return None

    def _matches_filter(
        self,
        dto: ExecutionLogDTO,
        filter: ExecutionFilter,
    ) -> bool:
        """Check if execution matches filter criteria."""
        # Workflow ID filter
        if filter.workflow_id:
            if dto.workflow_id != filter.workflow_id:
                return False

        # Status filter
        if filter.status:
            if dto.status != filter.status:
                return False

        # Started after filter
        if filter.started_after:
            if dto.started_at < filter.started_after:
                return False

        # Started before filter
        if filter.started_before:
            if dto.started_at > filter.started_before:
                return False

        return True

    def _parse_datetime(
        self,
        value: Optional[str],
    ) -> Optional[datetime]:
        """Parse datetime from string."""
        if not value:
            return None

        try:
            # Handle ISO format with optional timezone
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            pass

        try:
            # Try common formats
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except (ValueError, AttributeError):
            pass

        return None
