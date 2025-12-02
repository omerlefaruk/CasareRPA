"""
CasareRPA Cloud Orchestrator Server.

FastAPI server that manages robot fleet connections via WebSocket.
Designed for deployment on Railway, Render, or Fly.io.

Features:
- WebSocket endpoint for robot connections
- WebSocket endpoint for admin dashboard
- REST endpoints for job submission and robot management
- Supabase integration for presence sync
- API key authentication for robots
"""

import asyncio
import os
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

import orjson
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Header,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from pydantic import BaseModel, Field

from casare_rpa.infrastructure.auth.robot_api_keys import (
    hash_api_key,
    validate_api_key_format,
)
from casare_rpa.domain.value_objects.log_entry import (
    LogLevel,
    LogQuery,
    DEFAULT_LOG_RETENTION_DAYS,
)


# =============================================================================
# CONFIGURATION
# =============================================================================


@dataclass
class OrchestratorConfig:
    """Orchestrator configuration loaded from environment."""

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1

    # Database
    database_url: Optional[str] = None
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None

    # Redis (optional queue backend)
    redis_url: Optional[str] = None

    # Security
    api_secret: str = ""
    cors_origins: List[str] = field(default_factory=list)

    # Timeouts
    robot_heartbeat_timeout: int = 90  # seconds
    job_timeout_default: int = 3600  # 1 hour
    websocket_ping_interval: int = 30

    @classmethod
    def from_env(cls) -> "OrchestratorConfig":
        """Load configuration from environment variables."""
        cors_origins_str = os.getenv("CORS_ORIGINS", "")
        cors_origins = [o.strip() for o in cors_origins_str.split(",") if o.strip()]

        return cls(
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8000")),
            workers=int(os.getenv("WORKERS", "1")),
            database_url=os.getenv("DATABASE_URL"),
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key=os.getenv("SUPABASE_KEY"),
            redis_url=os.getenv("REDIS_URL"),
            api_secret=os.getenv("API_SECRET", ""),
            cors_origins=cors_origins,
            robot_heartbeat_timeout=int(os.getenv("ROBOT_HEARTBEAT_TIMEOUT", "90")),
            job_timeout_default=int(os.getenv("JOB_TIMEOUT_DEFAULT", "3600")),
            websocket_ping_interval=int(os.getenv("WS_PING_INTERVAL", "30")),
        )


# =============================================================================
# MODELS
# =============================================================================


class RobotRegistration(BaseModel):
    """Robot registration message from WebSocket."""

    robot_id: str
    robot_name: str
    capabilities: Dict[str, Any] = Field(default_factory=dict)
    environment: str = "production"
    api_key_hash: Optional[str] = None
    tenant_id: Optional[str] = None  # Multi-tenant support


class JobSubmission(BaseModel):
    """Job submission request."""

    workflow_id: str
    workflow_data: Dict[str, Any]
    variables: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=5, ge=1, le=10)
    target_robot_id: Optional[str] = None
    required_capabilities: List[str] = Field(default_factory=list)
    timeout: Optional[int] = None
    tenant_id: Optional[str] = None  # Multi-tenant support


class JobResponse(BaseModel):
    """Job response after submission."""

    job_id: str
    status: str
    workflow_id: str
    robot_id: Optional[str] = None
    created_at: datetime


class RobotInfo(BaseModel):
    """Robot information for API response."""

    robot_id: str
    robot_name: str
    status: str
    capabilities: List[str] = Field(default_factory=list)
    current_jobs: int = 0
    max_concurrent_jobs: int = 1
    last_heartbeat: Optional[datetime] = None
    connected_at: Optional[datetime] = None
    tenant_id: Optional[str] = None  # Multi-tenant support


class LogQueryRequest(BaseModel):
    """Log query parameters."""

    robot_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    min_level: str = "DEBUG"
    source: Optional[str] = None
    search_text: Optional[str] = None
    limit: int = Field(default=100, ge=1, le=10000)
    offset: int = Field(default=0, ge=0)


class LogEntryResponse(BaseModel):
    """Log entry response."""

    id: str
    robot_id: str
    timestamp: datetime
    level: str
    message: str
    source: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None


class LogStatsResponse(BaseModel):
    """Log statistics response."""

    total_count: int
    by_level: Dict[str, int]
    oldest_log: Optional[datetime] = None
    newest_log: Optional[datetime] = None
    storage_bytes: int


# =============================================================================
# IN-MEMORY STATE (for serverless-friendly operation)
# =============================================================================


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
    tenant_id: Optional[str] = None  # Multi-tenant support

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
    tenant_id: Optional[str] = None  # Multi-tenant support


class RobotManager:
    """Manages connected robots and job queue."""

    def __init__(self, config: OrchestratorConfig):
        self.config = config
        self._robots: Dict[str, ConnectedRobot] = {}
        self._jobs: Dict[str, PendingJob] = {}
        self._admin_connections: Set[WebSocket] = set()
        self._api_key_cache: Dict[str, str] = {}  # hash -> robot_id
        self._lock = asyncio.Lock()

    async def register_robot(
        self,
        websocket: WebSocket,
        registration: RobotRegistration,
    ) -> ConnectedRobot:
        """Register a new robot connection."""
        async with self._lock:
            # Extract capabilities
            caps = registration.capabilities.get("types", [])
            max_jobs = registration.capabilities.get("max_concurrent_jobs", 1)

            robot = ConnectedRobot(
                robot_id=registration.robot_id,
                robot_name=registration.robot_name,
                websocket=websocket,
                capabilities=caps,
                max_concurrent_jobs=max_jobs,
                environment=registration.environment,
                tenant_id=registration.tenant_id,
            )

            self._robots[registration.robot_id] = robot
            logger.info(
                f"Robot registered: {registration.robot_name} ({registration.robot_id})"
                f"{f' [tenant: {registration.tenant_id}]' if registration.tenant_id else ''}"
            )

            # Broadcast to admin connections
            await self._broadcast_admin(
                {
                    "type": "robot_connected",
                    "robot_id": registration.robot_id,
                    "robot_name": registration.robot_name,
                    "capabilities": caps,
                    "tenant_id": registration.tenant_id,
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

                # Broadcast to admin connections
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

            # Broadcast to admin connections
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
        """Get all connected robots, optionally filtered by tenant.

        Args:
            tenant_id: If provided, only return robots for this tenant.
                       If None, return all robots.
        """
        robots = list(self._robots.values())
        if tenant_id is not None:
            robots = [r for r in robots if r.tenant_id == tenant_id]
        return robots

    def get_available_robots(
        self,
        required_capabilities: Optional[List[str]] = None,
        tenant_id: Optional[str] = None,
    ) -> List[ConnectedRobot]:
        """Get robots with available capacity matching capabilities.

        Args:
            required_capabilities: List of capabilities the robot must have.
            tenant_id: If provided, only return robots for this tenant.
        """
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

    async def submit_job(self, submission: JobSubmission) -> PendingJob:
        """Submit a new job to the queue."""
        async with self._lock:
            job_id = str(uuid.uuid4())
            job = PendingJob(
                job_id=job_id,
                workflow_id=submission.workflow_id,
                workflow_data=submission.workflow_data,
                variables=submission.variables,
                priority=submission.priority,
                target_robot_id=submission.target_robot_id,
                required_capabilities=submission.required_capabilities,
                timeout=submission.timeout or self.config.job_timeout_default,
                tenant_id=submission.tenant_id,
            )
            self._jobs[job_id] = job
            logger.info(
                f"Job submitted: {job_id} (workflow: {submission.workflow_id})"
                f"{f' [tenant: {submission.tenant_id}]' if submission.tenant_id else ''}"
            )

            # Try to assign immediately
            await self._try_assign_job(job)

            return job

    async def _try_assign_job(self, job: PendingJob) -> bool:
        """Try to assign a job to an available robot.

        Respects tenant isolation - jobs can only be assigned to robots
        belonging to the same tenant.
        """
        if job.status != "pending":
            return False

        # Find matching robot
        target_robot: Optional[ConnectedRobot] = None

        if job.target_robot_id:
            # Specific robot requested
            target_robot = self._robots.get(job.target_robot_id)
            if target_robot:
                # Verify tenant isolation
                if job.tenant_id and target_robot.tenant_id != job.tenant_id:
                    logger.warning(
                        f"Job {job.job_id} target robot {job.target_robot_id} "
                        f"belongs to different tenant"
                    )
                    target_robot = None
                elif target_robot.available_slots <= 0:
                    target_robot = None
        else:
            # Find best available robot (tenant-scoped)
            available = self.get_available_robots(
                required_capabilities=job.required_capabilities,
                tenant_id=job.tenant_id,
            )
            if available:
                # Sort by priority: least loaded first
                available.sort(key=lambda r: len(r.current_job_ids))
                target_robot = available[0]

        if target_robot is None:
            return False

        # Assign job
        job.status = "assigned"
        job.assigned_robot_id = target_robot.robot_id
        target_robot.current_job_ids.add(job.job_id)

        # Send job to robot
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
        """Requeue a job that was rejected by a robot.

        Removes the job from the rejecting robot and attempts to assign
        to another available robot. If no robot is available, the job
        stays pending in the queue.
        """
        async with self._lock:
            # Remove job from the rejecting robot
            robot = self._robots.get(robot_id)
            if robot:
                robot.current_job_ids.discard(job_id)

            job = self._jobs.get(job_id)
            if not job:
                logger.warning(f"Cannot requeue unknown job: {job_id}")
                return

            # Track rejection to avoid reassigning to same robot
            if not hasattr(job, "rejected_by"):
                job.rejected_by = set()
            job.rejected_by.add(robot_id)

            # Reset job to pending
            job.status = "pending"
            job.assigned_robot_id = None

            logger.info(
                f"Job {job_id} requeued after rejection by {robot_id}: {reason}"
            )

            # Broadcast to admin
            await self._broadcast_admin(
                {
                    "type": "job_requeued",
                    "job_id": job_id,
                    "rejected_by": robot_id,
                    "reason": reason,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

            # Try to assign to another robot (excluding the one that rejected)
            await self._try_assign_job_excluding(job, job.rejected_by)

    async def _try_assign_job_excluding(
        self,
        job: "PendingJob",
        excluded_robots: Set[str],
    ) -> bool:
        """Try to assign a job to an available robot, excluding specified robots."""
        if job.status != "pending":
            return False

        # Find matching robot excluding rejected ones
        target_robot: Optional[ConnectedRobot] = None

        if job.target_robot_id and job.target_robot_id not in excluded_robots:
            # Specific robot requested and not excluded
            target_robot = self._robots.get(job.target_robot_id)
            if target_robot and target_robot.available_slots <= 0:
                target_robot = None
        else:
            # Find best available robot not in excluded list
            available = [
                r
                for r in self.get_available_robots(job.required_capabilities)
                if r.robot_id not in excluded_robots
            ]
            if available:
                # Sort by priority: least loaded first
                available.sort(key=lambda r: len(r.current_job_ids))
                target_robot = available[0]

        if target_robot is None:
            logger.info(f"No available robots for requeued job {job.job_id}")
            return False

        # Assign job
        job.status = "assigned"
        job.assigned_robot_id = target_robot.robot_id
        target_robot.current_job_ids.add(job.job_id)

        # Send job to robot
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

                # Broadcast to admin
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


# =============================================================================
# APPLICATION FACTORY
# =============================================================================


# Global state
_config: Optional[OrchestratorConfig] = None
_robot_manager: Optional[RobotManager] = None
_db_pool = None
_log_streaming_service = None
_log_repository = None
_log_cleanup_job = None


def get_config() -> OrchestratorConfig:
    """Get orchestrator configuration."""
    global _config
    if _config is None:
        _config = OrchestratorConfig.from_env()
    return _config


def get_robot_manager() -> RobotManager:
    """Get robot manager instance."""
    global _robot_manager
    if _robot_manager is None:
        _robot_manager = RobotManager(get_config())
    return _robot_manager


async def verify_api_key(
    x_api_key: str = Header(..., alias="X-Api-Key"),
) -> str:
    """Verify robot API key and return robot_id.

    Validates API key format and verifies against database when configured.
    Returns robot_id on success, raises HTTPException on failure.
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
        )

    if not validate_api_key_format(x_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format",
        )

    key_hash = hash_api_key(x_api_key)

    # Validate against database when configured
    global _db_pool
    if _db_pool is not None:
        try:
            async with _db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT robot_id, is_revoked, expires_at
                    FROM robot_api_keys
                    WHERE key_hash = $1
                    """,
                    key_hash,
                )
                if row is None:
                    logger.warning(
                        f"API key not found in database (hash: {key_hash[:16]}...)"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid API key",
                    )
                if row["is_revoked"]:
                    logger.warning(f"API key revoked (robot: {row['robot_id']})")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="API key has been revoked",
                    )
                if row["expires_at"] is not None:
                    if row["expires_at"] < datetime.now(timezone.utc):
                        logger.warning(f"API key expired (robot: {row['robot_id']})")
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="API key has expired",
                        )

                # Update last used timestamp (fire-and-forget)
                await conn.execute(
                    """
                    UPDATE robot_api_keys SET last_used_at = NOW()
                    WHERE key_hash = $1
                    """,
                    key_hash,
                )

                logger.debug(f"API key validated for robot: {row['robot_id']}")
                return row["robot_id"]

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Database error validating API key: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service unavailable",
            )

    # Fallback: no database configured, accept valid format with warning
    logger.warning("API key validation skipped - no database configured")
    return "unverified"


async def validate_websocket_api_key(api_key: Optional[str]) -> Optional[str]:
    """Validate API key for WebSocket connections.

    Returns robot_id on success, None on failure.
    Does not raise exceptions - caller should handle None appropriately.
    """
    if not api_key:
        return None

    if not validate_api_key_format(api_key):
        return None

    key_hash = hash_api_key(api_key)

    global _db_pool
    if _db_pool is not None:
        try:
            async with _db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT robot_id, is_revoked, expires_at
                    FROM robot_api_keys
                    WHERE key_hash = $1
                    """,
                    key_hash,
                )
                if row is None:
                    logger.warning(
                        f"WebSocket API key not found (hash: {key_hash[:16]}...)"
                    )
                    return None
                if row["is_revoked"]:
                    logger.warning(
                        f"WebSocket API key revoked (robot: {row['robot_id']})"
                    )
                    return None
                if row["expires_at"] is not None:
                    if row["expires_at"] < datetime.now(timezone.utc):
                        logger.warning(
                            f"WebSocket API key expired (robot: {row['robot_id']})"
                        )
                        return None

                logger.debug(
                    f"WebSocket API key validated for robot: {row['robot_id']}"
                )
                return row["robot_id"]

        except Exception as e:
            logger.error(f"Database error validating WebSocket API key: {e}")
            return None

    # Fallback: no database configured, accept valid format with warning
    logger.warning("WebSocket API key validation skipped - no database configured")
    return "unverified"


async def validate_admin_secret(secret: Optional[str]) -> bool:
    """Validate admin API secret for WebSocket connections.

    Returns True if secret matches configured API_SECRET, False otherwise.
    """
    if not secret:
        return False

    config = get_config()
    if not config.api_secret:
        logger.warning("Admin authentication attempted but API_SECRET not configured")
        return False

    # Use constant-time comparison to prevent timing attacks
    import hmac

    return hmac.compare_digest(secret, config.api_secret)


async def verify_admin_api_key(
    x_api_key: str = Header(..., alias="X-Api-Key"),
) -> str:
    """Verify admin API key for REST endpoints.

    This is for admin/management endpoints that require the API_SECRET.
    """
    config = get_config()

    if not config.api_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API_SECRET not configured",
        )

    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
        )

    # Use constant-time comparison to prevent timing attacks
    import hmac

    if not hmac.compare_digest(x_api_key, config.api_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return "admin"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    config = get_config()
    logger.info("Starting CasareRPA Cloud Orchestrator")
    logger.info(f"Host: {config.host}:{config.port}")

    # Initialize database pool if configured
    global _db_pool, _log_streaming_service, _log_repository, _log_cleanup_job
    if config.database_url:
        try:
            import asyncpg

            _db_pool = await asyncpg.create_pool(
                config.database_url,
                min_size=2,
                max_size=10,
            )
            logger.info("Database pool initialized")

            # Initialize log repository and streaming service
            try:
                from casare_rpa.infrastructure.persistence.repositories.log_repository import (
                    LogRepository,
                )
                from casare_rpa.infrastructure.logging.log_streaming_service import (
                    LogStreamingService,
                )
                from casare_rpa.infrastructure.logging.log_cleanup import (
                    LogCleanupJob,
                )

                _log_repository = LogRepository()
                _log_streaming_service = LogStreamingService(_log_repository)
                await _log_streaming_service.start()
                logger.info("Log streaming service started")

                # Start log cleanup job
                _log_cleanup_job = LogCleanupJob(
                    log_repository=_log_repository,
                    retention_days=DEFAULT_LOG_RETENTION_DAYS,
                )
                await _log_cleanup_job.start()
                logger.info("Log cleanup job started")

            except Exception as e:
                logger.warning(f"Log streaming initialization failed: {e}")

        except Exception as e:
            logger.warning(f"Database connection failed: {e}")

    # Initialize Supabase if configured
    if config.supabase_url and config.supabase_key:
        logger.info("Supabase integration enabled")

    yield

    # Cleanup
    if _log_cleanup_job:
        await _log_cleanup_job.stop()
        logger.info("Log cleanup job stopped")

    if _log_streaming_service:
        await _log_streaming_service.stop()
        logger.info("Log streaming service stopped")

    if _db_pool:
        await _db_pool.close()
        logger.info("Database pool closed")

    logger.info("Shutting down orchestrator")


def create_app() -> FastAPI:
    """Create FastAPI application."""
    config = get_config()

    app = FastAPI(
        title="CasareRPA Cloud Orchestrator",
        description="Robot fleet management and job orchestration service",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS - restrictive by default
    # Production deployments MUST set CORS_ORIGINS explicitly
    origins = config.cors_origins
    if not origins:
        # Default to restrictive: only same-origin allowed
        logger.warning(
            "CORS_ORIGINS not configured - using restrictive default. "
            "Set CORS_ORIGINS environment variable for production."
        )
        origins = []  # Empty list = no cross-origin requests allowed

    # Warn if using wildcard with credentials
    if "*" in origins:
        logger.warning(
            "CORS configured with '*' - this is insecure for production! "
            "Set specific origins in CORS_ORIGINS."
        )
        # Disable credentials when using wildcard (browser security requirement)
        allow_credentials = False
    else:
        allow_credentials = True

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=allow_credentials,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Api-Key", "X-Request-ID"],
    )

    # Health endpoints
    @app.get("/health")
    async def health_check():
        """Basic health check."""
        return {"status": "healthy", "service": "casare-orchestrator"}

    @app.get("/health/live")
    async def liveness_check():
        """Kubernetes liveness probe."""
        return {"alive": True}

    @app.get("/health/ready")
    async def readiness_check():
        """Kubernetes readiness probe."""
        manager = get_robot_manager()
        return {
            "ready": True,
            "connected_robots": len(manager.get_all_robots()),
            "pending_jobs": len(manager.get_pending_jobs()),
        }

    # Robot management endpoints (require admin authentication)
    @app.get("/api/robots", response_model=List[RobotInfo])
    async def list_robots(
        _: str = Depends(verify_admin_api_key),
        tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    ):
        """List all connected robots, optionally filtered by tenant. Requires admin API key."""
        manager = get_robot_manager()
        robots = manager.get_all_robots(tenant_id=tenant_id)
        return [
            RobotInfo(
                robot_id=r.robot_id,
                robot_name=r.robot_name,
                status=r.status,
                capabilities=r.capabilities,
                current_jobs=len(r.current_job_ids),
                max_concurrent_jobs=r.max_concurrent_jobs,
                last_heartbeat=r.last_heartbeat,
                connected_at=r.connected_at,
                tenant_id=r.tenant_id,
            )
            for r in robots
        ]

    @app.get("/api/robots/{robot_id}", response_model=RobotInfo)
    async def get_robot(robot_id: str, _: str = Depends(verify_admin_api_key)):
        """Get a specific robot by ID. Requires admin API key."""
        manager = get_robot_manager()
        robot = manager.get_robot(robot_id)
        if not robot:
            raise HTTPException(status_code=404, detail="Robot not found")
        return RobotInfo(
            robot_id=robot.robot_id,
            robot_name=robot.robot_name,
            status=robot.status,
            capabilities=robot.capabilities,
            current_jobs=len(robot.current_job_ids),
            max_concurrent_jobs=robot.max_concurrent_jobs,
            last_heartbeat=robot.last_heartbeat,
            connected_at=robot.connected_at,
            tenant_id=robot.tenant_id,
        )

    # Job endpoints (require admin authentication)
    @app.post("/api/jobs", response_model=JobResponse)
    async def submit_job(
        submission: JobSubmission,
        _: str = Depends(verify_admin_api_key),
    ):
        """Submit a job for execution. Requires admin API key."""
        manager = get_robot_manager()
        job = await manager.submit_job(submission)
        return JobResponse(
            job_id=job.job_id,
            status=job.status,
            workflow_id=job.workflow_id,
            robot_id=job.assigned_robot_id,
            created_at=job.created_at,
        )

    @app.get("/api/jobs/{job_id}")
    async def get_job(job_id: str, _: str = Depends(verify_admin_api_key)):
        """Get job status by ID. Requires admin API key."""
        manager = get_robot_manager()
        job = manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return {
            "job_id": job.job_id,
            "workflow_id": job.workflow_id,
            "status": job.status,
            "priority": job.priority,
            "assigned_robot_id": job.assigned_robot_id,
            "created_at": job.created_at.isoformat(),
        }

    @app.get("/api/jobs")
    async def list_jobs(
        _: str = Depends(verify_admin_api_key),
        status: Optional[str] = Query(None),
        tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
        limit: int = Query(100, ge=1, le=1000),
    ):
        """List jobs with optional status and tenant filter. Requires admin API key."""
        manager = get_robot_manager()
        jobs = list(manager._jobs.values())

        if status:
            jobs = [j for j in jobs if j.status == status]

        if tenant_id:
            jobs = [j for j in jobs if j.tenant_id == tenant_id]

        # Sort by priority (higher first) then created_at (older first)
        jobs.sort(key=lambda j: (-j.priority, j.created_at))

        return [
            {
                "job_id": j.job_id,
                "workflow_id": j.workflow_id,
                "status": j.status,
                "priority": j.priority,
                "assigned_robot_id": j.assigned_robot_id,
                "tenant_id": j.tenant_id,
                "created_at": j.created_at.isoformat(),
            }
            for j in jobs[:limit]
        ]

    # =========================================================================
    # LOG ENDPOINTS
    # =========================================================================

    @app.get("/api/logs", response_model=List[LogEntryResponse])
    async def query_logs(
        _: str = Depends(verify_admin_api_key),
        tenant_id: str = Query(..., description="Tenant ID (required)"),
        robot_id: Optional[str] = Query(None, description="Filter by robot ID"),
        start_time: Optional[datetime] = Query(None, description="Start of time range"),
        end_time: Optional[datetime] = Query(None, description="End of time range"),
        min_level: str = Query("DEBUG", description="Minimum log level"),
        source: Optional[str] = Query(None, description="Filter by source"),
        search_text: Optional[str] = Query(None, description="Search in message"),
        limit: int = Query(100, ge=1, le=10000),
        offset: int = Query(0, ge=0),
    ):
        """Query historical logs with filtering. Requires admin API key."""
        if _log_repository is None:
            raise HTTPException(
                status_code=503,
                detail="Log service not available",
            )

        try:
            query = LogQuery(
                tenant_id=tenant_id,
                robot_id=robot_id,
                start_time=start_time,
                end_time=end_time,
                min_level=LogLevel.from_string(min_level),
                source=source,
                search_text=search_text,
                limit=limit,
                offset=offset,
            )
            entries = await _log_repository.query(query)
            return [
                LogEntryResponse(
                    id=e.id,
                    robot_id=e.robot_id,
                    timestamp=e.timestamp,
                    level=e.level.value,
                    message=e.message,
                    source=e.source,
                    extra=e.extra,
                )
                for e in entries
            ]
        except Exception as e:
            logger.error(f"Log query failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/logs/stats", response_model=LogStatsResponse)
    async def get_log_stats(
        _: str = Depends(verify_admin_api_key),
        tenant_id: str = Query(..., description="Tenant ID (required)"),
        robot_id: Optional[str] = Query(None, description="Filter by robot ID"),
    ):
        """Get log statistics. Requires admin API key."""
        if _log_repository is None:
            raise HTTPException(
                status_code=503,
                detail="Log service not available",
            )

        try:
            stats = await _log_repository.get_stats(tenant_id, robot_id)
            return LogStatsResponse(
                total_count=stats.total_count,
                by_level=stats.by_level,
                oldest_log=stats.oldest_log,
                newest_log=stats.newest_log,
                storage_bytes=stats.storage_bytes,
            )
        except Exception as e:
            logger.error(f"Log stats query failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/logs/streaming/metrics")
    async def get_log_streaming_metrics(_: str = Depends(verify_admin_api_key)):
        """Get log streaming service metrics. Requires admin API key."""
        if _log_streaming_service is None:
            raise HTTPException(
                status_code=503,
                detail="Log streaming service not available",
            )

        return _log_streaming_service.get_metrics()

    @app.get("/api/logs/cleanup/status")
    async def get_log_cleanup_status(_: str = Depends(verify_admin_api_key)):
        """Get log cleanup job status. Requires admin API key."""
        if _log_cleanup_job is None:
            raise HTTPException(
                status_code=503,
                detail="Log cleanup job not available",
            )

        return _log_cleanup_job.get_status()

    @app.post("/api/logs/cleanup/run")
    async def trigger_log_cleanup(_: str = Depends(verify_admin_api_key)):
        """Manually trigger log cleanup. Requires admin API key."""
        if _log_cleanup_job is None:
            raise HTTPException(
                status_code=503,
                detail="Log cleanup job not available",
            )

        result = await _log_cleanup_job.run_cleanup()
        return result

    # Log streaming WebSocket endpoint
    @app.websocket("/ws/logs/{robot_id}")
    async def log_stream_websocket(
        websocket: WebSocket,
        robot_id: str,
        api_secret: Optional[str] = Query(None, alias="api_secret"),
        min_level: str = Query("DEBUG", alias="min_level"),
    ):
        """WebSocket endpoint for streaming logs from a specific robot.

        Requires admin API secret authentication.
        Example: ws://host/ws/logs/robot-123?api_secret=your-secret&min_level=INFO
        """
        # Validate admin secret
        if not await validate_admin_secret(api_secret):
            logger.warning(f"Log stream auth failed for robot_id={robot_id}")
            await websocket.close(code=4001)
            return

        if _log_streaming_service is None:
            await websocket.close(code=4503)  # Service unavailable
            return

        await websocket.accept()
        logger.info(f"Log stream connected for robot: {robot_id}")

        try:
            # Subscribe to logs for this robot
            level = LogLevel.from_string(min_level)
            await _log_streaming_service.subscribe(
                websocket,
                robot_ids=[robot_id],
                min_level=level,
            )

            # Keep connection alive
            while True:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")

        except WebSocketDisconnect:
            logger.info(f"Log stream disconnected for robot: {robot_id}")
        except Exception as e:
            logger.error(f"Log stream error: {e}")
        finally:
            await _log_streaming_service.unsubscribe(websocket)

    @app.websocket("/ws/logs")
    async def all_logs_stream_websocket(
        websocket: WebSocket,
        api_secret: Optional[str] = Query(None, alias="api_secret"),
        tenant_id: Optional[str] = Query(None, alias="tenant_id"),
        min_level: str = Query("DEBUG", alias="min_level"),
    ):
        """WebSocket endpoint for streaming all logs (admin view).

        Requires admin API secret authentication.
        Example: ws://host/ws/logs?api_secret=your-secret&tenant_id=xxx&min_level=INFO
        """
        # Validate admin secret
        if not await validate_admin_secret(api_secret):
            logger.warning("All logs stream auth failed")
            await websocket.close(code=4001)
            return

        if _log_streaming_service is None:
            await websocket.close(code=4503)
            return

        await websocket.accept()
        logger.info(f"All logs stream connected (tenant={tenant_id})")

        try:
            # Subscribe to all logs for tenant
            level = LogLevel.from_string(min_level)
            await _log_streaming_service.subscribe(
                websocket,
                robot_ids=None,  # All robots
                tenant_id=tenant_id,
                min_level=level,
            )

            # Keep connection alive
            while True:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")

        except WebSocketDisconnect:
            logger.info("All logs stream disconnected")
        except Exception as e:
            logger.error(f"All logs stream error: {e}")
        finally:
            await _log_streaming_service.unsubscribe(websocket)

    # Robot WebSocket endpoint
    @app.websocket("/ws/robot/{robot_id}")
    async def robot_websocket(
        websocket: WebSocket,
        robot_id: str,
        api_key: Optional[str] = Query(None, alias="api_key"),
    ):
        """WebSocket endpoint for robot connections.

        Requires API key authentication via query parameter.
        Example: ws://host/ws/robot/robot-123?api_key=crpa_xxxxx
        """
        # Validate API key before accepting connection
        validated_robot_id = await validate_websocket_api_key(api_key)
        if validated_robot_id is None:
            logger.warning(f"Robot WebSocket auth failed for robot_id={robot_id}")
            await websocket.close(code=4001)  # 4001 = Unauthorized
            return

        # Verify robot_id matches the API key's robot (if database validation succeeded)
        if validated_robot_id != "unverified" and validated_robot_id != robot_id:
            logger.warning(
                f"Robot ID mismatch: URL={robot_id}, API key={validated_robot_id}"
            )
            await websocket.close(code=4003)  # 4003 = Forbidden
            return

        await websocket.accept()
        logger.info(f"Robot WebSocket connected: {robot_id}")

        manager = get_robot_manager()
        registered_robot: Optional[ConnectedRobot] = None

        try:
            while True:
                raw_message = await websocket.receive_text()
                message = orjson.loads(raw_message)
                msg_type = message.get("type", "")

                if msg_type == "register":
                    registration = RobotRegistration(
                        robot_id=message.get("robot_id", robot_id),
                        robot_name=message.get("robot_name", robot_id),
                        capabilities=message.get("capabilities", {}),
                        environment=message.get("environment", "production"),
                        api_key_hash=message.get("api_key_hash"),
                    )
                    registered_robot = await manager.register_robot(
                        websocket, registration
                    )

                    # Send acknowledgement
                    await websocket.send_text(
                        orjson.dumps(
                            {
                                "type": "register_ack",
                                "robot_id": registration.robot_id,
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            }
                        ).decode()
                    )

                elif msg_type == "heartbeat":
                    await manager.update_heartbeat(robot_id, message)
                    await websocket.send_text(
                        orjson.dumps(
                            {
                                "type": "heartbeat_ack",
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            }
                        ).decode()
                    )

                elif msg_type == "job_accept":
                    job_id = message.get("job_id")
                    logger.debug(f"Robot {robot_id} accepted job {job_id}")

                elif msg_type == "job_reject":
                    job_id = message.get("job_id")
                    reason = message.get("reason", "Unknown")
                    logger.warning(f"Robot {robot_id} rejected job {job_id}: {reason}")

                    # Requeue the job for another robot
                    await manager.requeue_job(robot_id, job_id, reason)

                elif msg_type == "job_progress":
                    job_id = message.get("job_id")
                    progress = message.get("progress", 0)
                    logger.debug(f"Job {job_id} progress: {progress}%")

                elif msg_type == "job_complete":
                    job_id = message.get("job_id")
                    result = message.get("result", {})
                    await manager.job_completed(robot_id, job_id, True, result)

                elif msg_type == "job_failed":
                    job_id = message.get("job_id")
                    error = message.get("error", "Unknown error")
                    await manager.job_completed(
                        robot_id, job_id, False, {"error": error}
                    )

                elif msg_type == "pong":
                    logger.debug(f"Pong from {robot_id}")

                elif msg_type == "log_batch":
                    # Handle log batch from robot
                    if (
                        _log_streaming_service is not None
                        and registered_robot is not None
                    ):
                        tenant_id = registered_robot.tenant_id or "default"
                        try:
                            count = await _log_streaming_service.receive_log_batch(
                                robot_id, message, tenant_id
                            )
                            logger.debug(f"Received {count} logs from {robot_id}")
                        except Exception as e:
                            logger.warning(
                                f"Failed to process log batch from {robot_id}: {e}"
                            )

                else:
                    logger.warning(f"Unknown message type from {robot_id}: {msg_type}")

        except WebSocketDisconnect:
            logger.info(f"Robot WebSocket disconnected: {robot_id}")
        except Exception as e:
            logger.error(f"Robot WebSocket error: {e}")
        finally:
            await manager.unregister_robot(robot_id)

    # Admin WebSocket endpoint
    @app.websocket("/ws/admin")
    async def admin_websocket(
        websocket: WebSocket,
        api_secret: Optional[str] = Query(None, alias="api_secret"),
    ):
        """WebSocket endpoint for admin dashboard.

        Requires API secret authentication via query parameter.
        Example: ws://host/ws/admin?api_secret=your-secret-key
        """
        # Validate API secret before accepting connection
        if not await validate_admin_secret(api_secret):
            logger.warning(
                "Admin WebSocket auth failed - invalid or missing api_secret"
            )
            await websocket.close(code=4001)  # 4001 = Unauthorized
            return

        await websocket.accept()
        logger.info("Admin WebSocket connected")

        manager = get_robot_manager()
        await manager.add_admin_connection(websocket)

        try:
            # Send initial state
            robots = manager.get_all_robots()
            await websocket.send_text(
                orjson.dumps(
                    {
                        "type": "initial_state",
                        "robots": [
                            {
                                "robot_id": r.robot_id,
                                "robot_name": r.robot_name,
                                "status": r.status,
                                "capabilities": r.capabilities,
                            }
                            for r in robots
                        ],
                        "pending_jobs": len(manager.get_pending_jobs()),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ).decode()
            )

            # Keep connection alive
            while True:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")

        except WebSocketDisconnect:
            logger.info("Admin WebSocket disconnected")
        except Exception as e:
            logger.error(f"Admin WebSocket error: {e}")
        finally:
            manager.remove_admin_connection(websocket)

    return app


# Create application instance
app = create_app()


# =============================================================================
# ENTRY POINT
# =============================================================================


def main() -> None:
    """Run the orchestrator server."""
    import uvicorn

    config = get_config()
    uvicorn.run(
        "casare_rpa.infrastructure.orchestrator.server:app",
        host=config.host,
        port=config.port,
        workers=config.workers,
        log_level="info",
    )


if __name__ == "__main__":
    main()
