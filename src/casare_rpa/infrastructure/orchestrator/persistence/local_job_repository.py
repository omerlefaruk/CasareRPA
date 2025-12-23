"""Local job repository implementation."""

from casare_rpa.domain.orchestrator.entities import Job, JobStatus
from casare_rpa.domain.orchestrator.repositories import JobRepository
from casare_rpa.infrastructure.orchestrator.persistence.local_storage_repository import (
    LocalStorageRepository,
)


class LocalJobRepository(JobRepository):
    """Local storage implementation of JobRepository."""

    def __init__(self, storage: LocalStorageRepository):
        self._storage = storage

    async def get_by_id(self, job_id: str) -> Job | None:
        """Get job by ID."""
        jobs = self._storage.get_jobs(limit=1000)
        for j in jobs:
            if j["id"] == job_id:
                return Job.from_dict(j)
        return None

    async def get_all(self) -> list[Job]:
        """Get all jobs."""
        jobs = self._storage.get_jobs(limit=1000)
        return [Job.from_dict(j) for j in jobs]

    async def get_by_status(self, status: JobStatus) -> list[Job]:
        """Get jobs by status."""
        jobs = self._storage.get_jobs(limit=1000, status=status.value)
        return [Job.from_dict(j) for j in jobs]

    async def get_by_robot(self, robot_id: str) -> list[Job]:
        """Get jobs assigned to robot."""
        jobs = self._storage.get_jobs(limit=1000)
        return [Job.from_dict(j) for j in jobs if j.get("robot_id") == robot_id]

    async def get_by_workflow(self, workflow_id: str) -> list[Job]:
        """Get jobs for workflow."""
        jobs = self._storage.get_jobs(limit=1000)
        return [Job.from_dict(j) for j in jobs if j.get("workflow_id") == workflow_id]

    async def save(self, job: Job) -> None:
        """Save or update job."""
        job_dict = job.to_dict()
        self._storage.save_job(job_dict)

    async def delete(self, job_id: str) -> None:
        """Delete job by ID."""
        self._storage.delete_job(job_id)
