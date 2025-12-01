"""
Job lifecycle service.
Handles job creation, updates, cancellation, and retries.
"""

import os
import asyncio
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Callable
from pathlib import Path

from loguru import logger
from dotenv import load_dotenv

from casare_rpa.domain.orchestrator.entities import Job, JobStatus, JobPriority
from casare_rpa.domain.orchestrator.repositories import JobRepository

load_dotenv()


class JobLifecycleService:
    """
    Service for managing job lifecycle operations.
    Supports both cloud (Supabase) and local storage modes.
    """

    def __init__(self, job_repository: JobRepository):
        """Initialize with injected repository."""
        self._job_repository = job_repository
        self._supabase_url = os.getenv("SUPABASE_URL")
        self._supabase_key = os.getenv("SUPABASE_KEY")
        self._client = None
        self._connected = False
        self._use_local = True  # Default to local mode

        # Event callbacks
        self._on_job_update: Optional[Callable[[Job], None]] = None

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

    # ==================== JOB OPERATIONS ====================

    async def get_jobs(
        self,
        limit: int = 100,
        status: Optional[JobStatus] = None,
        robot_id: Optional[str] = None,
    ) -> List[Job]:
        """Get jobs with optional filtering."""
        if self._use_local:
            if status and robot_id:
                jobs = await self._job_repository.get_by_robot(robot_id)
                return [j for j in jobs if j.status == status][:limit]
            elif status:
                return (await self._job_repository.get_by_status(status))[:limit]
            elif robot_id:
                return (await self._job_repository.get_by_robot(robot_id))[:limit]
            else:
                return (await self._job_repository.get_all())[:limit]
        else:
            try:
                query = self._client.table("jobs").select("*")
                if status:
                    query = query.eq("status", status.value)
                if robot_id:
                    query = query.eq("robot_id", robot_id)
                query = query.order("created_at", desc=True).limit(limit)

                response = await asyncio.to_thread(lambda: query.execute())
                data = response.data
                return [Job.from_dict(j) for j in data]
            except Exception as e:
                logger.error(f"Failed to fetch jobs: {e}")
                return []

    async def get_job(self, job_id: str) -> Optional[Job]:
        """Get a specific job by ID."""
        if self._use_local:
            return await self._job_repository.get_by_id(job_id)
        else:
            try:
                response = await asyncio.to_thread(
                    lambda: self._client.table("jobs")
                    .select("*")
                    .eq("id", job_id)
                    .execute()
                )
                if response.data:
                    return Job.from_dict(response.data[0])
            except Exception as e:
                logger.error(f"Failed to fetch job {job_id}: {e}")
        return None

    async def get_running_jobs(self) -> List[Job]:
        """Get currently running jobs."""
        return await self.get_jobs(status=JobStatus.RUNNING)

    async def get_queued_jobs(self) -> List[Job]:
        """Get jobs waiting in queue."""
        pending = await self.get_jobs(status=JobStatus.PENDING)
        queued = await self.get_jobs(status=JobStatus.QUEUED)
        return pending + queued

    async def create_job(
        self,
        workflow_id: str,
        workflow_name: str,
        workflow_json: str,
        robot_id: str,
        robot_name: str = "",
        priority: JobPriority = JobPriority.NORMAL,
        scheduled_time: Optional[datetime] = None,
    ) -> Optional[Job]:
        """Create a new job."""
        job_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        job_data = {
            "id": job_id,
            "workflow_id": workflow_id,
            "workflow_name": workflow_name,
            "workflow": workflow_json,
            "robot_id": robot_id,
            "robot_name": robot_name,
            "status": JobStatus.PENDING.value,
            "priority": priority.value,
            "scheduled_time": scheduled_time.isoformat() if scheduled_time else None,
            "created_at": now,
            "progress": 0,
            "logs": "",
            "error_message": "",
        }

        if self._use_local:
            job = Job.from_dict(job_data)
            await self._job_repository.save(job)
            logger.info(f"Created job {job_id} for robot {robot_id}")
            return job
        else:
            try:
                await asyncio.to_thread(
                    lambda: self._client.table("jobs").insert(job_data).execute()
                )
                logger.info(f"Created job {job_id} for robot {robot_id}")
                return Job.from_dict(job_data)
            except Exception as e:
                logger.error(f"Failed to create job: {e}")

        return None

    async def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        progress: int = 0,
        current_node: str = "",
        error_message: str = "",
        logs: str = "",
    ) -> bool:
        """Update job status and progress."""
        now = datetime.now(timezone.utc).isoformat()
        data = {
            "status": status.value,
            "progress": progress,
            "current_node": current_node,
            "updated_at": now,
        }

        if status == JobStatus.RUNNING:
            data["started_at"] = now
        elif status in (
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
            JobStatus.TIMEOUT,
        ):
            data["completed_at"] = now
            if error_message:
                data["error_message"] = error_message
            if logs:
                data["logs"] = logs

        if self._use_local:
            job = await self._job_repository.get_by_id(job_id)
            if job:
                # Update job fields
                job.status = status
                job.progress = progress
                job.current_node = current_node
                if error_message:
                    job.error_message = error_message
                if logs:
                    job.logs = logs
                await self._job_repository.save(job)
                return True
            return False
        else:
            try:
                await asyncio.to_thread(
                    lambda: self._client.table("jobs")
                    .update(data)
                    .eq("id", job_id)
                    .execute()
                )
                return True
            except Exception as e:
                logger.error(f"Failed to update job status: {e}")
                return False

    async def cancel_job(self, job_id: str, reason: str = "") -> bool:
        """
        Cancel a pending or running job.

        For running jobs, sets cancel_requested=True which the robot
        will poll for and gracefully stop execution.
        """
        job = await self.get_job(job_id)
        if not job:
            return False

        now = datetime.now(timezone.utc).isoformat()

        if job.status == JobStatus.RUNNING:
            # For running jobs, set cancel_requested flag
            # Robot will poll for this and stop gracefully
            data = {
                "cancel_requested": True,
                "cancel_reason": reason,
                "updated_at": now,
            }

            if self._use_local:
                # Use the injected job_repository instead of undefined _local_storage
                job_obj = await self._job_repository.get_by_id(job_id)
                if job_obj:
                    job_obj.cancel_requested = True
                    job_obj.cancel_reason = reason
                    await self._job_repository.update(job_obj)
                    return True
                return False
            else:
                try:
                    await asyncio.to_thread(
                        lambda: self._client.table("jobs")
                        .update(data)
                        .eq("id", job_id)
                        .execute()
                    )
                    logger.info(f"Cancel requested for running job {job_id}")
                    return True
                except Exception as e:
                    logger.error(f"Failed to request job cancellation: {e}")
                    return False
        else:
            # For pending/queued jobs, cancel immediately
            return await self.update_job_status(
                job_id, JobStatus.CANCELLED, error_message=reason or "Cancelled by user"
            )

    async def retry_job(self, job_id: str) -> Optional[Job]:
        """Retry a failed job by creating a new one with same parameters."""
        original_job = await self.get_job(job_id)
        if not original_job:
            return None

        return await self.create_job(
            workflow_id=original_job.workflow_id,
            workflow_name=original_job.workflow_name,
            workflow_json=original_job.workflow_json,
            robot_id=original_job.robot_id,
            robot_name=original_job.robot_name,
            priority=original_job.priority,
        )

    async def dispatch_workflow_file(
        self, file_path: Path, robot_id: str, priority: JobPriority = JobPriority.NORMAL
    ) -> Optional[Job]:
        """Dispatch a workflow from a file to a robot."""
        try:
            import json

            with open(file_path, "r", encoding="utf-8") as f:
                workflow_json = f.read()
                workflow_data = json.loads(workflow_json)

            # TODO: Get robot from RobotManagementService
            # For now, create job with robot_id
            return await self.create_job(
                workflow_id=str(uuid.uuid4()),
                workflow_name=workflow_data.get("name", file_path.stem),
                workflow_json=workflow_json,
                robot_id=robot_id,
                robot_name="",  # Will be filled by caller
                priority=priority,
            )
        except Exception as e:
            logger.error(f"Failed to dispatch workflow from {file_path}: {e}")
            return None
