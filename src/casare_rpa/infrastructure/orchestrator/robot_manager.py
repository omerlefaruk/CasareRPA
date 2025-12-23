"""
Robot Manager for Cloud Orchestrator.

Manages connected robots, job queue, and admin WebSocket connections.
Supports optional PostgreSQL persistence for robot state.

Architecture:
- WebSocket connections: Always in-memory (not serializable)
- Robot state: Persisted to PostgreSQL when repository provided
- Job queue: In-memory (Phase 2 will move to PgQueuer)
- Domain events: Published for all state changes
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol, Set

import orjson
from fastapi import WebSocket
from loguru import logger

from casare_rpa.domain.events import get_event_bus
from casare_rpa.domain.orchestrator import Robot, RobotCapability, RobotStatus
from casare_rpa.domain.orchestrator.events import (
    JobAssigned,
    JobCompletedOnOrchestrator,
    JobRequeued,
    JobSubmitted,
    RobotDisconnected,
    RobotHeartbeat,
    RobotRegistered,
)


class RobotRepositoryProtocol(Protocol):
    """Protocol for robot repository (for type hints without circular import)."""

    async def get_by_id(self, robot_id: str) -> Optional[Robot]: ...
    async def get_all_online(self) -> List[Robot]: ...
    async def save(self, robot: Robot) -> None: ...
    async def update_status(self, robot_id: str, status: RobotStatus) -> None: ...
    async def update_heartbeat(
        self, robot_id: str, metrics: Optional[Dict[str, Any]] = None
    ) -> None: ...
    async def add_job_to_robot(self, robot_id: str, job_id: str) -> None: ...
    async def remove_job_from_robot(self, robot_id: str, job_id: str) -> None: ...
    async def mark_offline(self, robot_id: str) -> List[str]: ...


@dataclass
class ConnectedRobot:
    """Represents a connected robot with WebSocket.

    Note: This is a runtime object containing the WebSocket connection.
    Persistent state is stored in the Robot domain entity via repository.
    """

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
    hostname: str = ""

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

    def to_domain_robot(self) -> Robot:
        """Convert to domain Robot entity for persistence."""
        capabilities_set: Set[RobotCapability] = set()
        for cap in self.capabilities:
            try:
                capabilities_set.add(RobotCapability(cap))
            except ValueError:
                pass

        status = RobotStatus.ONLINE
        if len(self.current_job_ids) >= self.max_concurrent_jobs:
            status = RobotStatus.BUSY

        return Robot(
            id=self.robot_id,
            name=self.robot_name,
            status=status,
            environment=self.environment,
            max_concurrent_jobs=self.max_concurrent_jobs,
            last_seen=datetime.now(timezone.utc),
            last_heartbeat=self.last_heartbeat,
            created_at=self.connected_at,
            capabilities=capabilities_set,
            current_job_ids=list(self.current_job_ids),
        )


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
    """Manages connected robots and job queue.

    Supports two modes:
    1. In-memory only (default): Robot state lost on restart
    2. Persistent (with repository): Robot state survives restarts

    WebSocket connections are always in-memory (not serializable).
    """

    def __init__(
        self,
        job_timeout_default: int = 3600,
        robot_repository: Optional[RobotRepositoryProtocol] = None,
        publish_events: bool = True,
    ):
        """Initialize robot manager.

        Args:
            job_timeout_default: Default job timeout in seconds.
            robot_repository: Optional PostgreSQL repository for persistence.
            publish_events: Whether to publish domain events (default True).
        """
        self._job_timeout_default = job_timeout_default
        self._repository = robot_repository
        self._publish_events = publish_events

        # In-memory state (always needed for WebSocket connections)
        self._connections: Dict[str, WebSocket] = {}  # robot_id -> websocket
        self._robots: Dict[str, ConnectedRobot] = {}  # robot_id -> connected robot
        self._jobs: Dict[str, PendingJob] = {}
        self._admin_connections: Set[WebSocket] = set()
        self._api_key_cache: Dict[str, str] = {}  # hash -> robot_id
        self._lock = asyncio.Lock()

        # Event bus for domain events
        self._event_bus = get_event_bus() if publish_events else None

        if robot_repository:
            logger.info("RobotManager initialized with PostgreSQL persistence")
        else:
            logger.info("RobotManager initialized in memory-only mode")

    @property
    def is_persistent(self) -> bool:
        """Check if persistence is enabled."""
        return self._repository is not None

    async def register_robot(
        self,
        websocket: WebSocket,
        robot_id: str,
        robot_name: str,
        capabilities: Dict[str, Any],
        environment: str = "production",
        tenant_id: Optional[str] = None,
        hostname: str = "",
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
                hostname=hostname,
            )

            # Store in-memory (needed for WebSocket)
            self._robots[robot_id] = robot
            self._connections[robot_id] = websocket

            # Persist to database if repository available
            if self._repository:
                try:
                    await self._repository.save(robot.to_domain_robot())
                except Exception as e:
                    logger.error(f"Failed to persist robot {robot_id}: {e}")

            logger.info(
                f"Robot registered: {robot_name} ({robot_id})"
                f"{f' [tenant: {tenant_id}]' if tenant_id else ''}"
                f"{' [persistent]' if self._repository else ''}"
            )

            # Publish domain event
            if self._event_bus:
                self._event_bus.publish(
                    RobotRegistered(
                        robot_id=robot_id,
                        robot_name=robot_name,
                        hostname=hostname,
                        environment=environment,
                        capabilities=tuple(caps),
                        max_concurrent_jobs=max_jobs,
                        tenant_id=tenant_id or "",
                    )
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

    async def unregister_robot(self, robot_id: str, reason: str = "") -> None:
        """Unregister a robot connection."""
        async with self._lock:
            robot = self._robots.pop(robot_id, None)
            self._connections.pop(robot_id, None)

            if robot:
                orphaned_jobs = list(robot.current_job_ids)
                robot_name = robot.robot_name

                logger.info(f"Robot disconnected: {robot_name} ({robot_id})")

                # Requeue any jobs assigned to this robot
                for job_id in orphaned_jobs:
                    if job_id in self._jobs:
                        self._jobs[job_id].status = "pending"
                        self._jobs[job_id].assigned_robot_id = None
                        logger.warning(f"Requeued job {job_id} after robot disconnect")

                # Mark offline in database
                if self._repository:
                    try:
                        await self._repository.mark_offline(robot_id)
                    except Exception as e:
                        logger.error(f"Failed to mark robot {robot_id} offline: {e}")

                # Publish domain event
                if self._event_bus:
                    self._event_bus.publish(
                        RobotDisconnected(
                            robot_id=robot_id,
                            robot_name=robot_name,
                            orphaned_job_ids=tuple(orphaned_jobs),
                            reason=reason,
                        )
                    )

                await self._broadcast_admin(
                    {
                        "type": "robot_disconnected",
                        "robot_id": robot_id,
                        "orphaned_jobs": orphaned_jobs,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )

    async def update_heartbeat(self, robot_id: str, metrics: Dict[str, Any]) -> None:
        """Update robot heartbeat timestamp."""
        if robot_id in self._robots:
            self._robots[robot_id].last_heartbeat = datetime.now(timezone.utc)

            # Persist heartbeat
            if self._repository:
                try:
                    await self._repository.update_heartbeat(robot_id, metrics)
                except Exception as e:
                    logger.error(f"Failed to update heartbeat for {robot_id}: {e}")

            # Publish domain event
            if self._event_bus:
                self._event_bus.publish(
                    RobotHeartbeat(
                        robot_id=robot_id,
                        cpu_percent=metrics.get("cpu_percent", 0.0),
                        memory_mb=metrics.get("memory_mb", 0.0),
                        current_job_count=len(self._robots[robot_id].current_job_ids),
                    )
                )

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

    def get_websocket(self, robot_id: str) -> Optional[WebSocket]:
        """Get WebSocket connection for a robot."""
        return self._connections.get(robot_id)

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

            # Get workflow name for event
            workflow_name = workflow_data.get("name", workflow_id)

            logger.info(
                f"Job submitted: {job_id} (workflow: {workflow_id})"
                f"{f' [tenant: {tenant_id}]' if tenant_id else ''}"
            )

            # Publish domain event
            if self._event_bus:
                self._event_bus.publish(
                    JobSubmitted(
                        job_id=job_id,
                        workflow_id=workflow_id,
                        workflow_name=workflow_name,
                        priority=priority,
                        target_robot_id=target_robot_id or "",
                        tenant_id=tenant_id or "",
                    )
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

        # Persist job assignment
        if self._repository:
            try:
                await self._repository.add_job_to_robot(target_robot.robot_id, job.job_id)
            except Exception as e:
                logger.error(f"Failed to persist job assignment: {e}")

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

            # Publish domain event
            if self._event_bus:
                self._event_bus.publish(
                    JobAssigned(
                        job_id=job.job_id,
                        robot_id=target_robot.robot_id,
                        robot_name=target_robot.robot_name,
                        workflow_id=job.workflow_id,
                    )
                )

            logger.info(f"Job {job.job_id} assigned to robot {target_robot.robot_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to send job to robot: {e}")
            job.status = "pending"
            job.assigned_robot_id = None
            target_robot.current_job_ids.discard(job.job_id)

            # Rollback persistence
            if self._repository:
                try:
                    await self._repository.remove_job_from_robot(target_robot.robot_id, job.job_id)
                except Exception as e2:
                    logger.error(f"Failed to rollback job assignment: {e2}")

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

                # Persist removal
                if self._repository:
                    try:
                        await self._repository.remove_job_from_robot(robot_id, job_id)
                    except Exception as e:
                        logger.error(f"Failed to persist job removal: {e}")

            job = self._jobs.get(job_id)
            if not job:
                logger.warning(f"Cannot requeue unknown job: {job_id}")
                return

            job.rejected_by.add(robot_id)
            job.status = "pending"
            job.assigned_robot_id = None

            logger.info(f"Job {job_id} requeued after rejection by {robot_id}: {reason}")

            # Publish domain event
            if self._event_bus:
                self._event_bus.publish(
                    JobRequeued(
                        job_id=job_id,
                        previous_robot_id=robot_id,
                        reason=reason,
                        rejected_by_count=len(job.rejected_by),
                    )
                )

            # Publish domain event
            if self._event_bus:
                self._event_bus.publish(
                    JobRequeued(
                        job_id=job_id,
                        previous_robot_id=robot_id,
                        reason=reason,
                        rejected_by_count=len(job.rejected_by),
                    )
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

        # Persist job assignment
        if self._repository:
            try:
                await self._repository.add_job_to_robot(target_robot.robot_id, job.job_id)
            except Exception as e:
                logger.error(f"Failed to persist job assignment: {e}")

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

            # Publish domain event
            if self._event_bus:
                self._event_bus.publish(
                    JobAssigned(
                        job_id=job.job_id,
                        robot_id=target_robot.robot_id,
                        robot_name=target_robot.robot_name,
                        workflow_id=job.workflow_id,
                    )
                )

            logger.info(f"Requeued job {job.job_id} assigned to robot {target_robot.robot_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to send requeued job to robot: {e}")
            job.status = "pending"
            job.assigned_robot_id = None
            target_robot.current_job_ids.discard(job.job_id)

            # Rollback persistence
            if self._repository:
                try:
                    await self._repository.remove_job_from_robot(target_robot.robot_id, job.job_id)
                except Exception as e2:
                    logger.error(f"Failed to rollback job assignment: {e2}")

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

                # Persist job removal
                if self._repository:
                    try:
                        await self._repository.remove_job_from_robot(robot_id, job_id)
                    except Exception as e:
                        logger.error(f"Failed to persist job completion: {e}")

            job = self._jobs.get(job_id)
            if job:
                job.status = "completed" if success else "failed"
                logger.info(f"Job {job_id} {job.status}")

                # Publish domain event
                if self._event_bus:
                    self._event_bus.publish(
                        JobCompletedOnOrchestrator(
                            job_id=job_id,
                            robot_id=robot_id,
                            success=success,
                            execution_time_ms=int(
                                (datetime.now(timezone.utc) - job.created_at).total_seconds() * 1000
                            ),
                        )
                    )

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

    async def get_fleet_stats(self) -> Dict[str, Any]:
        """Get fleet statistics.

        Returns summary of all robots and jobs.
        """
        robots = self.get_all_robots()
        jobs = self._jobs

        online_count = sum(1 for r in robots if r.status in ("idle", "working"))
        busy_count = sum(1 for r in robots if r.status == "busy")

        pending_jobs = sum(1 for j in jobs.values() if j.status == "pending")
        assigned_jobs = sum(1 for j in jobs.values() if j.status == "assigned")
        completed_jobs = sum(1 for j in jobs.values() if j.status == "completed")
        failed_jobs = sum(1 for j in jobs.values() if j.status == "failed")

        return {
            "robots": {
                "total": len(robots),
                "online": online_count,
                "busy": busy_count,
            },
            "jobs": {
                "pending": pending_jobs,
                "assigned": assigned_jobs,
                "completed": completed_jobs,
                "failed": failed_jobs,
                "total": len(jobs),
            },
            "persistent": self.is_persistent,
        }
