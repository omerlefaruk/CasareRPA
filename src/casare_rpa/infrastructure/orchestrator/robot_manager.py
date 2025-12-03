"""
Robot Manager for Cloud Orchestrator.

Manages connected robots, job queue, and admin WebSocket connections.
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

import orjson
from fastapi import WebSocket
from loguru import logger


@dataclass
class ConnectedRobot:
    """Represents a connected robot."""

    robot_id: str
    robot_name: str
    websocket: WebSocket
    capabilities: List[str] = field(default_factory=list)
    max_concurrent_jobs: int = 1
    current_job_ids: Set[str] = field(default_factory=set)
    connected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_heartbeat: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    environment: str = "production"
    tenant_id: Optional[str] = None

    @property
    def status(self) -> str:
        """Get robot status based on job count."""
        if len(self.current_job_ids) >= self.max_concurrent_jobs:
            return "busy"
        if len(self.current_job_ids) > 0:
            return "working"
        return "idle"

    @property
    def available_slots(self) -> int:
        """Get number of available job slots."""
        return max(0, self.max_concurrent_jobs - len(self.current_job_ids))


@dataclass
class PendingJob:
    """Represents a job waiting for assignment."""

    job_id: str
    workflow_id: str
    workflow_data: Dict[str, Any]
    variables: Dict[str, Any]
    priority: int
    target_robot_id: Optional[str]
    required_capabilities: List[str]
    timeout: int
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "pending"
    assigned_robot_id: Optional[str] = None
    tenant_id: Optional[str] = None
    rejected_by: Set[str] = field(default_factory=set)


class RobotManager:
    """Manages connected robots and job queue."""

    def __init__(self, job_timeout_default: int = 3600):
        """Initialize robot manager.

        Args:
            job_timeout_default: Default job timeout in seconds.
        """
        self._job_timeout_default = job_timeout_default
        self._robots: Dict[str, ConnectedRobot] = {}
        self._jobs: Dict[str, PendingJob] = {}
        self._admin_connections: Set[WebSocket] = set()
        self._api_key_cache: Dict[str, str] = {}  # hash -> robot_id
        self._lock = asyncio.Lock()

    async def register_robot(
        self,
        websocket: WebSocket,
        robot_id: str,
        robot_name: str,
        capabilities: Dict[str, Any],
        environment: str = "production",
        tenant_id: Optional[str] = None,
    ) -> ConnectedRobot:
        """Register a new robot connection."""
        async with self._lock:
            caps = capabilities.get("types", [])
            max_jobs = capabilities.get("max_concurrent_jobs", 1)

            robot = ConnectedRobot(
                robot_id=robot_id,
                robot_name=robot_name,
                websocket=websocket,
                capabilities=caps,
                max_concurrent_jobs=max_jobs,
                environment=environment,
                tenant_id=tenant_id,
            )

            self._robots[robot_id] = robot
            logger.info(
                f"Robot registered: {robot_name} ({robot_id})"
                f"{f' [tenant: {tenant_id}]' if tenant_id else ''}"
            )

            await self._broadcast_admin(
                {
                    "type": "robot_connected",
                    "robot_id": robot_id,
                    "robot_name": robot_name,
                    "capabilities": caps,
                    "tenant_id": tenant_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

            return robot

    async def unregister_robot(self, robot_id: str) -> None:
        """Unregister a robot connection."""
        async with self._lock:
            robot = self._robots.pop(robot_id, None)
            if robot:
                logger.info(f"Robot disconnected: {robot.robot_name} ({robot_id})")

                # Requeue any jobs assigned to this robot
                for job_id in robot.current_job_ids:
                    if job_id in self._jobs:
                        self._jobs[job_id].status = "pending"
                        self._jobs[job_id].assigned_robot_id = None
                        logger.warning(f"Requeued job {job_id} after robot disconnect")

                await self._broadcast_admin(
                    {
                        "type": "robot_disconnected",
                        "robot_id": robot_id,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )

    async def update_heartbeat(self, robot_id: str, metrics: Dict[str, Any]) -> None:
        """Update robot heartbeat timestamp."""
        if robot_id in self._robots:
            self._robots[robot_id].last_heartbeat = datetime.now(timezone.utc)

            await self._broadcast_admin(
                {
                    "type": "robot_heartbeat",
                    "robot_id": robot_id,
                    "metrics": metrics,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

    def get_robot(self, robot_id: str) -> Optional[ConnectedRobot]:
        """Get a connected robot by ID."""
        return self._robots.get(robot_id)

    def get_all_robots(
        self,
        tenant_id: Optional[str] = None,
    ) -> List[ConnectedRobot]:
        """Get all connected robots, optionally filtered by tenant."""
        robots = list(self._robots.values())
        if tenant_id is not None:
            robots = [r for r in robots if r.tenant_id == tenant_id]
        return robots

    def get_available_robots(
        self,
        required_capabilities: Optional[List[str]] = None,
        tenant_id: Optional[str] = None,
    ) -> List[ConnectedRobot]:
        """Get robots with available capacity matching capabilities."""
        available = []
        for robot in self._robots.values():
            if robot.available_slots <= 0:
                continue
            if tenant_id is not None and robot.tenant_id != tenant_id:
                continue
            if required_capabilities:
                if not all(cap in robot.capabilities for cap in required_capabilities):
                    continue
            available.append(robot)
        return available

    async def submit_job(
        self,
        workflow_id: str,
        workflow_data: Dict[str, Any],
        variables: Dict[str, Any],
        priority: int = 5,
        target_robot_id: Optional[str] = None,
        required_capabilities: Optional[List[str]] = None,
        timeout: Optional[int] = None,
        tenant_id: Optional[str] = None,
    ) -> PendingJob:
        """Submit a new job to the queue."""
        async with self._lock:
            job_id = str(uuid.uuid4())
            job = PendingJob(
                job_id=job_id,
                workflow_id=workflow_id,
                workflow_data=workflow_data,
                variables=variables,
                priority=priority,
                target_robot_id=target_robot_id,
                required_capabilities=required_capabilities or [],
                timeout=timeout or self._job_timeout_default,
                tenant_id=tenant_id,
            )
            self._jobs[job_id] = job
            logger.info(
                f"Job submitted: {job_id} (workflow: {workflow_id})"
                f"{f' [tenant: {tenant_id}]' if tenant_id else ''}"
            )

            await self._try_assign_job(job)

            return job

    async def _try_assign_job(self, job: PendingJob) -> bool:
        """Try to assign a job to an available robot."""
        if job.status != "pending":
            return False

        target_robot: Optional[ConnectedRobot] = None

        if job.target_robot_id:
            target_robot = self._robots.get(job.target_robot_id)
            if target_robot:
                if job.tenant_id and target_robot.tenant_id != job.tenant_id:
                    logger.warning(
                        f"Job {job.job_id} target robot {job.target_robot_id} "
                        f"belongs to different tenant"
                    )
                    target_robot = None
                elif target_robot.available_slots <= 0:
                    target_robot = None
        else:
            available = self.get_available_robots(
                required_capabilities=job.required_capabilities,
                tenant_id=job.tenant_id,
            )
            if available:
                available.sort(key=lambda r: len(r.current_job_ids))
                target_robot = available[0]

        if target_robot is None:
            return False

        job.status = "assigned"
        job.assigned_robot_id = target_robot.robot_id
        target_robot.current_job_ids.add(job.job_id)

        try:
            await target_robot.websocket.send_text(
                orjson.dumps(
                    {
                        "type": "job_assign",
                        "job_id": job.job_id,
                        "workflow_id": job.workflow_id,
                        "workflow_data": job.workflow_data,
                        "variables": job.variables,
                        "timeout": job.timeout,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ).decode()
            )
            logger.info(f"Job {job.job_id} assigned to robot {target_robot.robot_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to send job to robot: {e}")
            job.status = "pending"
            job.assigned_robot_id = None
            target_robot.current_job_ids.discard(job.job_id)
            return False

    async def requeue_job(
        self,
        robot_id: str,
        job_id: str,
        reason: str,
    ) -> None:
        """Requeue a job that was rejected by a robot."""
        async with self._lock:
            robot = self._robots.get(robot_id)
            if robot:
                robot.current_job_ids.discard(job_id)

            job = self._jobs.get(job_id)
            if not job:
                logger.warning(f"Cannot requeue unknown job: {job_id}")
                return

            job.rejected_by.add(robot_id)
            job.status = "pending"
            job.assigned_robot_id = None

            logger.info(
                f"Job {job_id} requeued after rejection by {robot_id}: {reason}"
            )

            await self._broadcast_admin(
                {
                    "type": "job_requeued",
                    "job_id": job_id,
                    "rejected_by": robot_id,
                    "reason": reason,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

            await self._try_assign_job_excluding(job, job.rejected_by)

    async def _try_assign_job_excluding(
        self,
        job: PendingJob,
        excluded_robots: Set[str],
    ) -> bool:
        """Try to assign a job to an available robot, excluding specified robots."""
        if job.status != "pending":
            return False

        target_robot: Optional[ConnectedRobot] = None

        if job.target_robot_id and job.target_robot_id not in excluded_robots:
            target_robot = self._robots.get(job.target_robot_id)
            if target_robot and target_robot.available_slots <= 0:
                target_robot = None
        else:
            available = [
                r
                for r in self.get_available_robots(job.required_capabilities)
                if r.robot_id not in excluded_robots
            ]
            if available:
                available.sort(key=lambda r: len(r.current_job_ids))
                target_robot = available[0]

        if target_robot is None:
            logger.info(f"No available robots for requeued job {job.job_id}")
            return False

        job.status = "assigned"
        job.assigned_robot_id = target_robot.robot_id
        target_robot.current_job_ids.add(job.job_id)

        try:
            await target_robot.websocket.send_text(
                orjson.dumps(
                    {
                        "type": "job_assign",
                        "job_id": job.job_id,
                        "workflow_id": job.workflow_id,
                        "workflow_data": job.workflow_data,
                        "variables": job.variables,
                        "timeout": job.timeout,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ).decode()
            )
            logger.info(
                f"Requeued job {job.job_id} assigned to robot {target_robot.robot_name}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to send requeued job to robot: {e}")
            job.status = "pending"
            job.assigned_robot_id = None
            target_robot.current_job_ids.discard(job.job_id)
            return False

    async def job_completed(
        self,
        robot_id: str,
        job_id: str,
        success: bool,
        result: Dict[str, Any],
    ) -> None:
        """Handle job completion notification."""
        async with self._lock:
            robot = self._robots.get(robot_id)
            if robot:
                robot.current_job_ids.discard(job_id)

            job = self._jobs.get(job_id)
            if job:
                job.status = "completed" if success else "failed"
                logger.info(f"Job {job_id} {job.status}")

                await self._broadcast_admin(
                    {
                        "type": "job_completed",
                        "job_id": job_id,
                        "robot_id": robot_id,
                        "success": success,
                        "result": result,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )

    def get_job(self, job_id: str) -> Optional[PendingJob]:
        """Get a job by ID."""
        return self._jobs.get(job_id)

    def get_pending_jobs(self) -> List[PendingJob]:
        """Get all pending jobs."""
        return [j for j in self._jobs.values() if j.status == "pending"]

    def get_all_jobs(self) -> Dict[str, PendingJob]:
        """Get all jobs."""
        return self._jobs

    async def add_admin_connection(self, websocket: WebSocket) -> None:
        """Add an admin WebSocket connection."""
        self._admin_connections.add(websocket)
        logger.info(f"Admin connected. Total: {len(self._admin_connections)}")

    def remove_admin_connection(self, websocket: WebSocket) -> None:
        """Remove an admin WebSocket connection."""
        self._admin_connections.discard(websocket)
        logger.info(f"Admin disconnected. Total: {len(self._admin_connections)}")

    async def _broadcast_admin(self, message: Dict[str, Any]) -> None:
        """Broadcast message to all admin connections."""
        disconnected = set()
        for conn in self._admin_connections:
            try:
                await asyncio.wait_for(
                    conn.send_text(orjson.dumps(message).decode()),
                    timeout=1.0,
                )
            except Exception:
                disconnected.add(conn)

        for conn in disconnected:
            self._admin_connections.discard(conn)
