"""
Service layer for CasareRPA Orchestrator.
Handles business logic for jobs, schedules, workflows, and robots.
"""

import os
import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
import uuid

from loguru import logger
from dotenv import load_dotenv

from .models import (
    Robot,
    RobotStatus,
    Workflow,
    WorkflowStatus,
    Job,
    JobStatus,
    JobPriority,
    Schedule,
    DashboardMetrics,
    JobHistoryEntry,
)

load_dotenv()


class LocalStorageService:
    """
    Local storage service for offline/development mode.
    Stores data in JSON files when Supabase is not available.
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or Path.home() / ".casare_rpa" / "orchestrator"
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self._robots_file = self.storage_dir / "robots.json"
        self._jobs_file = self.storage_dir / "jobs.json"
        self._workflows_file = self.storage_dir / "workflows.json"
        self._schedules_file = self.storage_dir / "schedules.json"

        # Initialize files if they don't exist
        for file_path in [
            self._robots_file,
            self._jobs_file,
            self._workflows_file,
            self._schedules_file,
        ]:
            if not file_path.exists():
                file_path.write_text("[]")

    def _load_json(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load JSON data from file."""
        try:
            return json.loads(file_path.read_text())
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            return []

    def _save_json(self, file_path: Path, data: List[Dict[str, Any]]) -> bool:
        """Save JSON data to file."""
        try:
            file_path.write_text(json.dumps(data, indent=2, default=str))
            return True
        except Exception as e:
            logger.error(f"Failed to save {file_path}: {e}")
            return False

    # Robots
    def get_robots(self) -> List[Dict[str, Any]]:
        return self._load_json(self._robots_file)

    def save_robot(self, robot: Dict[str, Any]) -> bool:
        robots = self.get_robots()
        # Update existing or add new
        for i, r in enumerate(robots):
            if r["id"] == robot["id"]:
                robots[i] = robot
                return self._save_json(self._robots_file, robots)
        robots.append(robot)
        return self._save_json(self._robots_file, robots)

    def delete_robot(self, robot_id: str) -> bool:
        robots = [r for r in self.get_robots() if r["id"] != robot_id]
        return self._save_json(self._robots_file, robots)

    # Jobs
    def get_jobs(
        self, limit: int = 100, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        jobs = self._load_json(self._jobs_file)
        if status:
            jobs = [j for j in jobs if j.get("status") == status]
        # Sort by created_at descending
        jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return jobs[:limit]

    def save_job(self, job: Dict[str, Any]) -> bool:
        jobs = self._load_json(self._jobs_file)
        for i, j in enumerate(jobs):
            if j["id"] == job["id"]:
                jobs[i] = job
                return self._save_json(self._jobs_file, jobs)
        jobs.append(job)
        return self._save_json(self._jobs_file, jobs)

    def delete_job(self, job_id: str) -> bool:
        jobs = [j for j in self._load_json(self._jobs_file) if j["id"] != job_id]
        return self._save_json(self._jobs_file, jobs)

    # Workflows
    def get_workflows(self) -> List[Dict[str, Any]]:
        return self._load_json(self._workflows_file)

    def save_workflow(self, workflow: Dict[str, Any]) -> bool:
        workflows = self.get_workflows()
        for i, w in enumerate(workflows):
            if w["id"] == workflow["id"]:
                workflows[i] = workflow
                return self._save_json(self._workflows_file, workflows)
        workflows.append(workflow)
        return self._save_json(self._workflows_file, workflows)

    def delete_workflow(self, workflow_id: str) -> bool:
        workflows = [w for w in self.get_workflows() if w["id"] != workflow_id]
        return self._save_json(self._workflows_file, workflows)

    # Schedules
    def get_schedules(self) -> List[Dict[str, Any]]:
        return self._load_json(self._schedules_file)

    def save_schedule(self, schedule: Dict[str, Any]) -> bool:
        schedules = self.get_schedules()
        for i, s in enumerate(schedules):
            if s["id"] == schedule["id"]:
                schedules[i] = schedule
                return self._save_json(self._schedules_file, schedules)
        schedules.append(schedule)
        return self._save_json(self._schedules_file, schedules)

    def delete_schedule(self, schedule_id: str) -> bool:
        schedules = [s for s in self.get_schedules() if s["id"] != schedule_id]
        return self._save_json(self._schedules_file, schedules)


class OrchestratorService:
    """
    Main orchestrator service.
    Handles all business logic and data operations.
    Supports both Supabase (cloud) and local storage modes.
    """

    def __init__(self):
        self._supabase_url = os.getenv("SUPABASE_URL")
        self._supabase_key = os.getenv("SUPABASE_KEY")
        self._client = None
        self._connected = False
        self._use_local = False
        self._local_storage = LocalStorageService()

        # Event callbacks
        self._on_job_update: Optional[Callable[[Job], None]] = None
        self._on_robot_update: Optional[Callable[[Robot], None]] = None

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

    # ==================== ROBOTS ====================

    async def get_robots(self) -> List[Robot]:
        """Get all registered robots."""
        if self._use_local:
            data = self._local_storage.get_robots()
        else:
            try:
                response = await asyncio.to_thread(
                    lambda: self._client.table("robots")
                    .select("*")
                    .order("last_seen", desc=True)
                    .execute()
                )
                data = response.data
            except Exception as e:
                logger.error(f"Failed to fetch robots: {e}")
                data = []

        return [Robot.from_dict(r) for r in data]

    async def get_robot(self, robot_id: str) -> Optional[Robot]:
        """Get a specific robot by ID."""
        robots = await self.get_robots()
        for robot in robots:
            if robot.id == robot_id:
                return robot
        return None

    async def get_available_robots(self) -> List[Robot]:
        """Get robots that can accept new jobs."""
        robots = await self.get_robots()
        return [r for r in robots if r.is_available]

    async def update_robot_status(self, robot_id: str, status: RobotStatus) -> bool:
        """Update robot status."""
        data = {"status": status.value, "last_seen": datetime.utcnow().isoformat()}

        if self._use_local:
            robots = self._local_storage.get_robots()
            for r in robots:
                if r["id"] == robot_id:
                    r.update(data)
                    return self._local_storage.save_robot(r)
            return False
        else:
            try:
                await asyncio.to_thread(
                    lambda: self._client.table("robots")
                    .update(data)
                    .eq("id", robot_id)
                    .execute()
                )
                return True
            except Exception as e:
                logger.error(f"Failed to update robot status: {e}")
                return False

    # ==================== JOBS ====================

    async def get_jobs(
        self,
        limit: int = 100,
        status: Optional[JobStatus] = None,
        robot_id: Optional[str] = None,
    ) -> List[Job]:
        """Get jobs with optional filtering."""
        if self._use_local:
            data = self._local_storage.get_jobs(limit, status.value if status else None)
            if robot_id:
                data = [j for j in data if j.get("robot_id") == robot_id]
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
            except Exception as e:
                logger.error(f"Failed to fetch jobs: {e}")
                data = []

        return [Job.from_dict(j) for j in data]

    async def get_job(self, job_id: str) -> Optional[Job]:
        """Get a specific job by ID."""
        if self._use_local:
            jobs = self._local_storage.get_jobs(limit=1000)
            for j in jobs:
                if j["id"] == job_id:
                    return Job.from_dict(j)
            return None
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
        now = datetime.utcnow().isoformat()

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
            if self._local_storage.save_job(job_data):
                logger.info(f"Created job {job_id} for robot {robot_id}")
                return Job.from_dict(job_data)
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
        now = datetime.utcnow().isoformat()
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
            jobs = self._local_storage.get_jobs(limit=1000)
            for j in jobs:
                if j["id"] == job_id:
                    j.update(data)
                    return self._local_storage.save_job(j)
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

        For running jobs, this sets cancel_requested=True which the robot
        will poll for and gracefully stop execution.
        """
        job = await self.get_job(job_id)
        if not job:
            return False

        now = datetime.utcnow().isoformat()

        if job.status == JobStatus.RUNNING:
            # For running jobs, set cancel_requested flag
            # Robot will poll for this and stop gracefully
            data = {
                "cancel_requested": True,
                "cancel_reason": reason,
                "updated_at": now,
            }

            if self._use_local:
                jobs = self._local_storage.get_jobs(limit=1000)
                for j in jobs:
                    if j["id"] == job_id:
                        j.update(data)
                        return self._local_storage.save_job(j)
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

    # ==================== WORKFLOWS ====================

    async def get_workflows(
        self, status: Optional[WorkflowStatus] = None
    ) -> List[Workflow]:
        """Get all workflows."""
        if self._use_local:
            data = self._local_storage.get_workflows()
            if status:
                data = [w for w in data if w.get("status") == status.value]
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
        now = datetime.utcnow().isoformat()
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
            return self._local_storage.save_workflow(data)
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
                created_at=datetime.utcnow().isoformat(),
            )

            if await self.save_workflow(workflow):
                return workflow
        except Exception as e:
            logger.error(f"Failed to import workflow from {file_path}: {e}")
        return None

    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow."""
        if self._use_local:
            return self._local_storage.delete_workflow(workflow_id)
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

    # ==================== SCHEDULES ====================

    async def get_schedules(self, enabled_only: bool = False) -> List[Schedule]:
        """Get all schedules."""
        if self._use_local:
            data = self._local_storage.get_schedules()
            if enabled_only:
                data = [s for s in data if s.get("enabled", True)]
        else:
            try:
                query = self._client.table("schedules").select("*")
                if enabled_only:
                    query = query.eq("enabled", True)
                query = query.order("next_run", desc=False)
                response = await asyncio.to_thread(lambda: query.execute())
                data = response.data
            except Exception as e:
                logger.error(f"Failed to fetch schedules: {e}")
                data = []

        return [Schedule.from_dict(s) for s in data]

    async def get_schedule(self, schedule_id: str) -> Optional[Schedule]:
        """Get a specific schedule by ID."""
        schedules = await self.get_schedules()
        for s in schedules:
            if s.id == schedule_id:
                return s
        return None

    async def save_schedule(self, schedule: Schedule) -> bool:
        """Save or update a schedule."""
        now = datetime.utcnow().isoformat()
        data = {
            "id": schedule.id,
            "name": schedule.name,
            "workflow_id": schedule.workflow_id,
            "workflow_name": schedule.workflow_name,
            "robot_id": schedule.robot_id,
            "robot_name": schedule.robot_name,
            "frequency": schedule.frequency.value,
            "cron_expression": schedule.cron_expression,
            "timezone": schedule.timezone,
            "enabled": schedule.enabled,
            "priority": schedule.priority.value,
            "last_run": schedule.last_run,
            "next_run": schedule.next_run,
            "run_count": schedule.run_count,
            "success_count": schedule.success_count,
            "created_at": schedule.created_at or now,
            "created_by": schedule.created_by,
        }

        if self._use_local:
            return self._local_storage.save_schedule(data)
        else:
            try:
                await asyncio.to_thread(
                    lambda: self._client.table("schedules").upsert(data).execute()
                )
                return True
            except Exception as e:
                logger.error(f"Failed to save schedule: {e}")
                return False

    async def toggle_schedule(self, schedule_id: str, enabled: bool) -> bool:
        """Enable or disable a schedule."""
        schedule = await self.get_schedule(schedule_id)
        if schedule:
            schedule.enabled = enabled
            return await self.save_schedule(schedule)
        return False

    async def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a schedule."""
        if self._use_local:
            return self._local_storage.delete_schedule(schedule_id)
        else:
            try:
                await asyncio.to_thread(
                    lambda: self._client.table("schedules")
                    .delete()
                    .eq("id", schedule_id)
                    .execute()
                )
                return True
            except Exception as e:
                logger.error(f"Failed to delete schedule: {e}")
                return False

    # ==================== DASHBOARD METRICS ====================

    async def get_dashboard_metrics(self) -> DashboardMetrics:
        """Get dashboard KPI metrics."""
        metrics = DashboardMetrics()

        # Get all data
        robots = await self.get_robots()
        jobs = await self.get_jobs(limit=1000)
        workflows = await self.get_workflows()
        schedules = await self.get_schedules()

        # Robot metrics
        metrics.robots_total = len(robots)
        metrics.robots_online = len(
            [r for r in robots if r.status == RobotStatus.ONLINE]
        )
        metrics.robots_busy = len([r for r in robots if r.status == RobotStatus.BUSY])

        if metrics.robots_total > 0:
            total_utilization = sum(r.utilization for r in robots)
            metrics.robot_utilization = total_utilization / metrics.robots_total

        # Job metrics - time-based filtering
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)
        month_start = today_start - timedelta(days=30)

        def parse_date(date_str: str) -> Optional[datetime]:
            if not date_str:
                return None
            try:
                return datetime.fromisoformat(
                    date_str.replace("Z", "+00:00").replace("+00:00", "")
                )
            except (ValueError, TypeError):
                return None

        jobs_today = []
        jobs_week = []
        jobs_month = []

        for job in jobs:
            created = (
                parse_date(job.created_at)
                if isinstance(job.created_at, str)
                else job.created_at
            )
            if created:
                if created >= today_start:
                    jobs_today.append(job)
                if created >= week_start:
                    jobs_week.append(job)
                if created >= month_start:
                    jobs_month.append(job)

        metrics.total_jobs_today = len(jobs_today)
        metrics.total_jobs_week = len(jobs_week)
        metrics.total_jobs_month = len(jobs_month)

        metrics.jobs_running = len([j for j in jobs if j.status == JobStatus.RUNNING])
        metrics.jobs_queued = len(
            [j for j in jobs if j.status in (JobStatus.PENDING, JobStatus.QUEUED)]
        )

        completed_today = [j for j in jobs_today if j.status == JobStatus.COMPLETED]
        failed_today = [j for j in jobs_today if j.status == JobStatus.FAILED]
        metrics.jobs_completed_today = len(completed_today)
        metrics.jobs_failed_today = len(failed_today)

        # Success rates
        if metrics.total_jobs_today > 0:
            metrics.success_rate_today = (
                metrics.jobs_completed_today / metrics.total_jobs_today
            ) * 100
        if metrics.total_jobs_week > 0:
            completed_week = len(
                [j for j in jobs_week if j.status == JobStatus.COMPLETED]
            )
            metrics.success_rate_week = (completed_week / metrics.total_jobs_week) * 100
        if metrics.total_jobs_month > 0:
            completed_month = len(
                [j for j in jobs_month if j.status == JobStatus.COMPLETED]
            )
            metrics.success_rate_month = (
                completed_month / metrics.total_jobs_month
            ) * 100

        # Performance metrics
        completed_jobs = [
            j for j in jobs if j.status == JobStatus.COMPLETED and j.duration_ms > 0
        ]
        if completed_jobs:
            metrics.avg_execution_time_ms = sum(
                j.duration_ms for j in completed_jobs
            ) // len(completed_jobs)

        # Throughput (jobs per hour in last 24h)
        if jobs_today:
            hours_elapsed = max(1, (now - today_start).total_seconds() / 3600)
            metrics.throughput_per_hour = len(jobs_today) / hours_elapsed

        # Workflow metrics
        metrics.workflows_total = len(workflows)
        metrics.workflows_published = len(
            [w for w in workflows if w.status == WorkflowStatus.PUBLISHED]
        )

        # Schedule metrics
        metrics.schedules_active = len([s for s in schedules if s.enabled])

        return metrics

    async def get_job_history(self, days: int = 7) -> List[JobHistoryEntry]:
        """Get job execution history for charting."""
        jobs = await self.get_jobs(limit=1000)
        now = datetime.utcnow()

        history: Dict[str, JobHistoryEntry] = {}

        for i in range(days):
            date = (now - timedelta(days=i)).strftime("%Y-%m-%d")
            history[date] = JobHistoryEntry(date=date)

        for job in jobs:
            created = job.created_at
            if isinstance(created, str):
                try:
                    created = datetime.fromisoformat(
                        created.replace("Z", "+00:00").replace("+00:00", "")
                    )
                except (ValueError, TypeError):
                    continue

            if created:
                date_key = created.strftime("%Y-%m-%d")
                if date_key in history:
                    history[date_key].total += 1
                    if job.status == JobStatus.COMPLETED:
                        history[date_key].completed += 1
                    elif job.status == JobStatus.FAILED:
                        history[date_key].failed += 1

        # Return sorted by date ascending
        return sorted(history.values(), key=lambda x: x.date)

    # ==================== DISPATCH ====================

    async def dispatch_workflow(
        self,
        workflow_id: str,
        robot_id: str,
        priority: JobPriority = JobPriority.NORMAL,
    ) -> Optional[Job]:
        """Dispatch a workflow to a robot for execution."""
        workflow = await self.get_workflow(workflow_id)
        robot = await self.get_robot(robot_id)

        if not workflow:
            logger.error(f"Workflow {workflow_id} not found")
            return None
        if not robot:
            logger.error(f"Robot {robot_id} not found")
            return None

        return await self.create_job(
            workflow_id=workflow.id,
            workflow_name=workflow.name,
            workflow_json=workflow.json_definition,
            robot_id=robot.id,
            robot_name=robot.name,
            priority=priority,
        )

    async def dispatch_workflow_file(
        self, file_path: Path, robot_id: str, priority: JobPriority = JobPriority.NORMAL
    ) -> Optional[Job]:
        """Dispatch a workflow from a file to a robot."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                workflow_json = f.read()
                workflow_data = json.loads(workflow_json)

            robot = await self.get_robot(robot_id)
            if not robot:
                logger.error(f"Robot {robot_id} not found")
                return None

            return await self.create_job(
                workflow_id=str(uuid.uuid4()),
                workflow_name=workflow_data.get("name", file_path.stem),
                workflow_json=workflow_json,
                robot_id=robot.id,
                robot_name=robot.name,
                priority=priority,
            )
        except Exception as e:
            logger.error(f"Failed to dispatch workflow from {file_path}: {e}")
            return None
