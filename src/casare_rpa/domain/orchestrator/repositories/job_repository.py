"""Job repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from casare_rpa.domain.orchestrator.entities import Job, JobStatus


class JobRepository(ABC):
    """Repository interface for Job aggregate."""

    @abstractmethod
    async def get_by_id(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        pass

    @abstractmethod
    async def get_all(self) -> List[Job]:
        """Get all jobs."""
        pass

    @abstractmethod
    async def get_by_status(self, status: JobStatus) -> List[Job]:
        """Get jobs by status."""
        pass

    @abstractmethod
    async def get_by_robot(self, robot_id: str) -> List[Job]:
        """Get jobs assigned to robot."""
        pass

    @abstractmethod
    async def get_by_workflow(self, workflow_id: str) -> List[Job]:
        """Get jobs for workflow."""
        pass

    @abstractmethod
    async def save(self, job: Job) -> None:
        """Save or update job."""
        pass

    @abstractmethod
    async def delete(self, job_id: str) -> None:
        """Delete job by ID."""
        pass
