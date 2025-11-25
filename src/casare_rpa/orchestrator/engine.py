"""
Orchestrator Engine - Integrates job queue, scheduler, and dispatcher.
The main orchestration logic for CasareRPA.
"""
import asyncio
from datetime import datetime
from typing import Optional, Dict, List, Any, Callable
import uuid

from loguru import logger

from .models import (
    Job, JobStatus, JobPriority, Robot, RobotStatus,
    Workflow, WorkflowStatus, Schedule, ScheduleFrequency,
    DashboardMetrics
)
from .services import OrchestratorService
from .job_queue import JobQueue, JobStateMachine
from .scheduler import JobScheduler, ScheduleManager, calculate_next_run

try:
    from .dispatcher import JobDispatcher, LoadBalancingStrategy, RobotPool
    HAS_DISPATCHER = True
except ImportError:
    HAS_DISPATCHER = False

try:
    from .server import OrchestratorServer
    HAS_SERVER = True
except ImportError:
    HAS_SERVER = False
    logger.warning("websockets not installed. Server features disabled.")


class OrchestratorEngine:
    """
    Main orchestrator engine that coordinates all components.

    Components:
    - JobQueue: Priority queue with state machine
    - JobScheduler: Cron-based scheduling
    - JobDispatcher: Robot selection and load balancing
    - OrchestratorService: Data persistence

    This is the primary interface for job management.
    """

    def __init__(
        self,
        service: Optional[OrchestratorService] = None,
        load_balancing: str = "least_loaded",
        dispatch_interval: int = 5,
        timeout_check_interval: int = 30,
        default_job_timeout: int = 3600
    ):
        """
        Initialize orchestrator engine.

        Args:
            service: Data persistence service
            load_balancing: Load balancing strategy (round_robin, least_loaded, random, affinity)
            dispatch_interval: Seconds between dispatch attempts
            timeout_check_interval: Seconds between timeout checks
            default_job_timeout: Default job timeout in seconds
        """
        self._service = service or OrchestratorService()

        # Initialize components
        self._job_queue = JobQueue(
            dedup_window_seconds=300,
            default_timeout_seconds=default_job_timeout,
            on_state_change=self._on_job_state_change
        )

        self._scheduler: Optional[JobScheduler] = None
        self._dispatcher: Optional[JobDispatcher] = None

        if HAS_DISPATCHER:
            strategy = LoadBalancingStrategy(load_balancing)
            self._dispatcher = JobDispatcher(
                strategy=strategy,
                dispatch_interval_seconds=dispatch_interval,
                health_check_interval_seconds=30
            )
            self._dispatcher.set_callbacks(
                on_robot_status_change=self._on_robot_status_change,
                on_job_dispatched=self._on_job_dispatched
            )

        # Configuration
        self._dispatch_interval = dispatch_interval
        self._timeout_check_interval = timeout_check_interval

        # Event callbacks
        self._on_job_complete: Optional[Callable[[Job], None]] = None
        self._on_job_failed: Optional[Callable[[Job], None]] = None

        # WebSocket server
        self._server: Optional["OrchestratorServer"] = None
        self._server_host: str = "0.0.0.0"
        self._server_port: int = 8765

        # Running state
        self._running = False
        self._background_tasks: List[asyncio.Task] = []

        logger.info("OrchestratorEngine initialized")

    # ==================== LIFECYCLE ====================

    async def start(self):
        """Start the orchestrator engine."""
        if self._running:
            return

        # Connect to data service
        await self._service.connect()

        # Load existing data
        await self._load_robots()
        await self._load_schedules()

        # Start scheduler
        try:
            self._scheduler = JobScheduler(
                on_schedule_trigger=self._on_schedule_trigger
            )
            await self._scheduler.start()
        except ImportError:
            logger.warning("APScheduler not available, scheduling disabled")

        # Start dispatcher
        if self._dispatcher:
            await self._dispatcher.start(self._job_queue)

        # Start background tasks
        self._running = True
        self._background_tasks.append(
            asyncio.create_task(self._timeout_check_loop())
        )
        self._background_tasks.append(
            asyncio.create_task(self._persist_loop())
        )

        logger.info("OrchestratorEngine started")

    async def stop(self):
        """Stop the orchestrator engine."""
        self._running = False

        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._background_tasks.clear()

        # Stop server
        if self._server:
            await self._server.stop()
            self._server = None

        # Stop scheduler
        if self._scheduler:
            await self._scheduler.stop()

        # Stop dispatcher
        if self._dispatcher:
            await self._dispatcher.stop()

        logger.info("OrchestratorEngine stopped")

    async def start_server(self, host: str = "0.0.0.0", port: int = 8765):
        """
        Start WebSocket server for robot connections.

        Args:
            host: Server bind address
            port: Server port
        """
        if not HAS_SERVER:
            logger.error("Cannot start server: websockets not installed")
            return

        self._server_host = host
        self._server_port = port

        self._server = OrchestratorServer(host=host, port=port)

        # Wire callbacks from server to engine
        self._server.set_callbacks(
            on_robot_connect=self._on_server_robot_connect,
            on_robot_disconnect=self._on_server_robot_disconnect,
            on_job_progress=self._on_server_job_progress,
            on_job_complete=self._on_server_job_complete,
            on_job_failed=self._on_server_job_failed,
        )

        await self._server.start()
        logger.info(f"Orchestrator server started on ws://{host}:{port}")

    async def _on_server_robot_connect(self, robot: Robot):
        """Handle robot connection via WebSocket."""
        logger.info(f"Robot connected via WebSocket: {robot.name} ({robot.id})")

        # Register with dispatcher
        if self._dispatcher:
            self._dispatcher.register_robot(robot, robot.environment)

        # Persist
        await self._service.update_robot_status(robot.id, RobotStatus.ONLINE)

    async def _on_server_robot_disconnect(self, robot_id: str):
        """Handle robot disconnection."""
        logger.info(f"Robot disconnected: {robot_id}")

        if self._dispatcher:
            robot = self._dispatcher.get_robot(robot_id)
            if robot:
                robot.status = RobotStatus.OFFLINE
                self._dispatcher.update_robot(robot)

        await self._service.update_robot_status(robot_id, RobotStatus.OFFLINE)

    async def _on_server_job_progress(self, job_id: str, progress: int, current_node: str):
        """Handle job progress from robot."""
        await self.update_job_progress(job_id, progress, current_node)

    async def _on_server_job_complete(self, job_id: str, result: Dict):
        """Handle job completion from robot."""
        await self.complete_job(job_id, result)

    async def _on_server_job_failed(self, job_id: str, error_message: str):
        """Handle job failure from robot."""
        await self.fail_job(job_id, error_message)

    async def dispatch_job_to_robot(self, job: Job, robot_id: str) -> bool:
        """
        Dispatch a job to a specific robot via WebSocket.

        Args:
            job: Job to dispatch
            robot_id: Target robot ID

        Returns:
            True if dispatched successfully
        """
        if not self._server:
            logger.error("Server not started, cannot dispatch job")
            return False

        # Send job via WebSocket
        result = await self._server.send_job(robot_id, job)

        if result.get("accepted"):
            job.status = JobStatus.RUNNING
            job.robot_id = robot_id
            job.started_at = datetime.utcnow().isoformat()
            await self._persist_job(job)
            logger.info(f"Job {job.id[:8]} dispatched to robot {robot_id}")
            return True
        else:
            reason = result.get("reason", "Unknown")
            logger.warning(f"Job {job.id[:8]} rejected by robot {robot_id}: {reason}")
            return False

    @property
    def server_port(self) -> int:
        """Get the server port."""
        return self._server_port

    @property
    def connected_robots(self) -> List[str]:
        """Get list of connected robot IDs."""
        if self._server:
            return [r.id for r in self._server.get_connected_robots()]
        return []

    @property
    def available_robots(self) -> List[Robot]:
        """Get list of available robots."""
        if self._server:
            return self._server.get_available_robots()
        return []

    async def _load_robots(self):
        """Load robots from persistence."""
        try:
            robots = await self._service.get_robots()
            for robot in robots:
                if self._dispatcher:
                    self._dispatcher.register_robot(robot, robot.environment)
            logger.info(f"Loaded {len(robots)} robots")
        except Exception as e:
            logger.error(f"Failed to load robots: {e}")

    async def _load_schedules(self):
        """Load schedules from persistence."""
        try:
            schedules = await self._service.get_schedules(enabled_only=True)
            for schedule in schedules:
                if self._scheduler:
                    self._scheduler.add_schedule(schedule)
            logger.info(f"Loaded {len(schedules)} schedules")
        except Exception as e:
            logger.error(f"Failed to load schedules: {e}")

    # ==================== JOB MANAGEMENT ====================

    async def submit_job(
        self,
        workflow_id: str,
        workflow_name: str,
        workflow_json: str,
        robot_id: Optional[str] = None,
        priority: JobPriority = JobPriority.NORMAL,
        scheduled_time: Optional[datetime] = None,
        params: Optional[Dict] = None,
        check_duplicate: bool = True
    ) -> Optional[Job]:
        """
        Submit a new job to the queue.

        Args:
            workflow_id: Workflow ID
            workflow_name: Workflow name
            workflow_json: Workflow JSON definition
            robot_id: Target robot ID (optional, any available if not specified)
            priority: Job priority
            scheduled_time: Future execution time (optional)
            params: Job parameters for deduplication
            check_duplicate: Whether to check for duplicates

        Returns:
            Created job or None if failed
        """
        # Create job
        job = Job(
            id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            workflow_json=workflow_json,
            robot_id=robot_id or "",
            robot_name="",
            status=JobStatus.PENDING,
            priority=priority,
            scheduled_time=scheduled_time,
            created_at=datetime.utcnow().isoformat()
        )

        # If scheduled for future, create a one-time schedule
        if scheduled_time and scheduled_time > datetime.utcnow():
            return await self._schedule_future_job(job, scheduled_time)

        # Enqueue immediately
        success, message = self._job_queue.enqueue(job, check_duplicate, params)

        if not success:
            logger.warning(f"Failed to enqueue job: {message}")
            return None

        # Persist to database
        await self._persist_job(job)

        logger.info(f"Job {job.id[:8]} submitted with priority {priority.name}")
        return job

    async def _schedule_future_job(self, job: Job, run_time: datetime) -> Optional[Job]:
        """Schedule a job for future execution."""
        if not self._scheduler:
            logger.error("Scheduler not available for future jobs")
            return None

        # Create a one-time schedule
        schedule = Schedule(
            id=f"onetime_{job.id}",
            name=f"One-time: {job.workflow_name}",
            workflow_id=job.workflow_id,
            workflow_name=job.workflow_name,
            robot_id=job.robot_id if job.robot_id else None,
            frequency=ScheduleFrequency.ONCE,
            priority=job.priority,
            next_run=run_time,
            enabled=True
        )

        self._scheduler.add_schedule(schedule)

        # Store job as pending (not queued yet)
        job.status = JobStatus.PENDING
        await self._persist_job(job)

        logger.info(f"Job {job.id[:8]} scheduled for {run_time}")
        return job

    async def cancel_job(self, job_id: str, reason: str = "Cancelled by user") -> bool:
        """
        Cancel a job.

        Args:
            job_id: Job ID to cancel
            reason: Cancellation reason

        Returns:
            True if cancelled successfully
        """
        success, message = self._job_queue.cancel(job_id, reason)

        if success:
            job = self._job_queue.get_job(job_id)
            if job:
                await self._persist_job(job)
                # Notify robot to cancel (if running)
                if job.robot_id:
                    await self._notify_robot_cancel(job)

        return success

    async def retry_job(self, job_id: str) -> Optional[Job]:
        """
        Retry a failed job.

        Args:
            job_id: Job ID to retry

        Returns:
            New job if created successfully
        """
        # Get original job from persistence
        original = await self._service.get_job(job_id)
        if not original:
            return None

        if original.status not in (JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.TIMEOUT):
            logger.warning(f"Cannot retry job in {original.status.value} state")
            return None

        # Create new job with same parameters
        return await self.submit_job(
            workflow_id=original.workflow_id,
            workflow_name=original.workflow_name,
            workflow_json=original.workflow_json,
            robot_id=original.robot_id if original.robot_id else None,
            priority=original.priority,
            check_duplicate=False  # Allow retry
        )

    async def update_job_progress(
        self,
        job_id: str,
        progress: int,
        current_node: str = ""
    ) -> bool:
        """
        Update job progress (called by robot).

        Args:
            job_id: Job ID
            progress: Progress percentage (0-100)
            current_node: Current node being executed

        Returns:
            True if updated successfully
        """
        success = self._job_queue.update_progress(job_id, progress, current_node)

        if success:
            job = self._job_queue.get_job(job_id)
            if job:
                await self._persist_job(job)

        return success

    async def complete_job(
        self,
        job_id: str,
        result: Optional[Dict] = None
    ) -> bool:
        """
        Mark a job as completed (called by robot).

        Args:
            job_id: Job ID
            result: Job result data

        Returns:
            True if completed successfully
        """
        success, _ = self._job_queue.complete(job_id, result)

        if success:
            job = self._job_queue.get_job(job_id)
            if job:
                await self._persist_job(job)
                await self._release_robot(job)
                if self._dispatcher:
                    self._dispatcher.record_job_result(job, True)
                if self._on_job_complete:
                    self._on_job_complete(job)

        return success

    async def fail_job(
        self,
        job_id: str,
        error_message: str
    ) -> bool:
        """
        Mark a job as failed (called by robot).

        Args:
            job_id: Job ID
            error_message: Error description

        Returns:
            True if marked successfully
        """
        success, _ = self._job_queue.fail(job_id, error_message)

        if success:
            job = self._job_queue.get_job(job_id)
            if job:
                await self._persist_job(job)
                await self._release_robot(job)
                if self._dispatcher:
                    self._dispatcher.record_job_result(job, False)
                if self._on_job_failed:
                    self._on_job_failed(job)

        return success

    # ==================== ROBOT MANAGEMENT ====================

    async def register_robot(
        self,
        robot_id: str,
        name: str,
        environment: str = "default",
        max_concurrent_jobs: int = 1,
        tags: Optional[List[str]] = None
    ) -> Robot:
        """
        Register a robot with the orchestrator.

        Args:
            robot_id: Robot ID
            name: Robot name
            environment: Robot environment/pool
            max_concurrent_jobs: Max concurrent jobs
            tags: Robot tags

        Returns:
            Registered robot
        """
        robot = Robot(
            id=robot_id,
            name=name,
            status=RobotStatus.ONLINE,
            environment=environment,
            max_concurrent_jobs=max_concurrent_jobs,
            current_jobs=0,
            last_seen=datetime.utcnow(),
            last_heartbeat=datetime.utcnow(),
            tags=tags or []
        )

        # Register with dispatcher
        if self._dispatcher:
            self._dispatcher.register_robot(robot, environment)

        # Persist
        await self._service.update_robot_status(robot_id, RobotStatus.ONLINE)

        logger.info(f"Robot '{name}' registered in environment '{environment}'")
        return robot

    async def robot_heartbeat(self, robot_id: str) -> bool:
        """
        Process robot heartbeat.

        Args:
            robot_id: Robot ID

        Returns:
            True if processed
        """
        if self._dispatcher:
            self._dispatcher.update_robot_heartbeat(robot_id)
            return True
        return False

    async def update_robot_status(self, robot_id: str, status: RobotStatus) -> bool:
        """
        Update robot status.

        Args:
            robot_id: Robot ID
            status: New status

        Returns:
            True if updated
        """
        if self._dispatcher:
            robot = self._dispatcher.get_robot(robot_id)
            if robot:
                robot.status = status
                self._dispatcher.update_robot(robot)
                await self._service.update_robot_status(robot_id, status)
                return True
        return False

    async def _release_robot(self, job: Job):
        """Release robot after job completion."""
        if self._dispatcher and job.robot_id:
            robot = self._dispatcher.get_robot(job.robot_id)
            if robot:
                robot.current_jobs = max(0, robot.current_jobs - 1)
                self._dispatcher.update_robot(robot)

    async def _notify_robot_cancel(self, job: Job):
        """Notify robot to cancel a job."""
        # This would send a message to the robot
        # Implementation depends on communication mechanism
        logger.info(f"Notifying robot {job.robot_name} to cancel job {job.id[:8]}")

    # ==================== SCHEDULE MANAGEMENT ====================

    async def create_schedule(
        self,
        name: str,
        workflow_id: str,
        workflow_name: str,
        frequency: ScheduleFrequency,
        cron_expression: str = "",
        robot_id: Optional[str] = None,
        priority: JobPriority = JobPriority.NORMAL,
        timezone: str = "UTC",
        enabled: bool = True
    ) -> Optional[Schedule]:
        """
        Create a new schedule.

        Args:
            name: Schedule name
            workflow_id: Workflow ID to run
            workflow_name: Workflow name
            frequency: Schedule frequency
            cron_expression: Cron expression (for CRON frequency)
            robot_id: Target robot (optional)
            priority: Job priority
            timezone: Timezone
            enabled: Whether schedule is enabled

        Returns:
            Created schedule
        """
        schedule = Schedule(
            id=str(uuid.uuid4()),
            name=name,
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            robot_id=robot_id,
            frequency=frequency,
            cron_expression=cron_expression,
            timezone=timezone,
            enabled=enabled,
            priority=priority,
            created_at=datetime.utcnow().isoformat()
        )

        # Calculate next run
        schedule.next_run = calculate_next_run(
            frequency, cron_expression, timezone
        )

        # Add to scheduler
        if self._scheduler and enabled:
            self._scheduler.add_schedule(schedule)

        # Persist
        await self._service.save_schedule(schedule)

        logger.info(f"Schedule '{name}' created, next run: {schedule.next_run}")
        return schedule

    async def toggle_schedule(self, schedule_id: str, enabled: bool) -> bool:
        """Enable or disable a schedule."""
        if self._scheduler:
            if enabled:
                schedule = await self._service.get_schedule(schedule_id)
                if schedule:
                    self._scheduler.add_schedule(schedule)
            else:
                self._scheduler.remove_schedule(schedule_id)

        return await self._service.toggle_schedule(schedule_id, enabled)

    async def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a schedule."""
        if self._scheduler:
            self._scheduler.remove_schedule(schedule_id)
        return await self._service.delete_schedule(schedule_id)

    # ==================== EVENT HANDLERS ====================

    def _on_job_state_change(self, job: Job, old_status: JobStatus, new_status: JobStatus):
        """Handle job state changes from queue."""
        logger.debug(f"Job {job.id[:8]}: {old_status.value} -> {new_status.value}")

    def _on_robot_status_change(self, robot: Robot, old_status: RobotStatus, new_status: RobotStatus):
        """Handle robot status changes."""
        logger.info(f"Robot '{robot.name}': {old_status.value} -> {new_status.value}")
        # Persist status change
        asyncio.create_task(
            self._service.update_robot_status(robot.id, new_status)
        )

    async def _on_job_dispatched(self, job: Job, robot: Robot):
        """Handle job dispatch."""
        logger.info(f"Job {job.id[:8]} dispatched to robot '{robot.name}'")
        # Persist job update
        await self._persist_job(job)

    async def _on_schedule_trigger(self, schedule: Schedule):
        """Handle schedule trigger."""
        logger.info(f"Schedule '{schedule.name}' triggered")

        # Get workflow
        workflow = await self._service.get_workflow(schedule.workflow_id)
        if not workflow:
            logger.error(f"Workflow {schedule.workflow_id} not found for schedule")
            return

        # Submit job
        await self.submit_job(
            workflow_id=workflow.id,
            workflow_name=workflow.name,
            workflow_json=workflow.json_definition,
            robot_id=schedule.robot_id,
            priority=schedule.priority,
            check_duplicate=True
        )

    # ==================== BACKGROUND TASKS ====================

    async def _timeout_check_loop(self):
        """Periodically check for timed out jobs."""
        while self._running:
            try:
                timed_out = self._job_queue.check_timeouts()
                for job_id in timed_out:
                    job = self._job_queue.get_job(job_id)
                    if job:
                        await self._persist_job(job)
                        await self._release_robot(job)

                await asyncio.sleep(self._timeout_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Timeout check error: {e}")
                await asyncio.sleep(self._timeout_check_interval)

    async def _persist_loop(self):
        """Periodically persist queue state to database."""
        while self._running:
            try:
                await asyncio.sleep(10)  # Persist every 10 seconds

                # Persist running jobs (progress updates)
                for job in self._job_queue.get_running_jobs():
                    await self._persist_job(job)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Persist loop error: {e}")

    async def _persist_job(self, job: Job):
        """Persist job to database."""
        job_data = {
            "id": job.id,
            "workflow_id": job.workflow_id,
            "workflow_name": job.workflow_name,
            "robot_id": job.robot_id,
            "robot_name": job.robot_name,
            "status": job.status.value if isinstance(job.status, JobStatus) else job.status,
            "priority": job.priority.value if isinstance(job.priority, JobPriority) else job.priority,
            "workflow": job.workflow_json,
            "scheduled_time": job.scheduled_time,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "duration_ms": job.duration_ms,
            "progress": job.progress,
            "current_node": job.current_node,
            "result": job.result,
            "logs": job.logs,
            "error_message": job.error_message,
            "created_at": job.created_at,
        }
        self._service._local_storage.save_job(job_data)

    # ==================== STATISTICS ====================

    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        return self._job_queue.get_queue_stats()

    def get_dispatcher_stats(self) -> Dict[str, Any]:
        """Get dispatcher statistics."""
        if self._dispatcher:
            return self._dispatcher.get_stats()
        return {}

    def get_upcoming_schedules(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get upcoming scheduled runs."""
        if self._scheduler:
            return self._scheduler.get_next_runs(limit)
        return []
