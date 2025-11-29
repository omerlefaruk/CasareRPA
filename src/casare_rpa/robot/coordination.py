"""
Multi-Robot Coordination System for CasareRPA.

Provides distributed coordination for robot fleet management:
- Robot registration with capabilities/tags
- Heartbeat-based health monitoring
- Load balancing strategies (round-robin, least-busy, capability-based)
- Job affinity routing
- Distributed locks for exclusive resources
- Auto-scaling triggers
- PostgreSQL-backed coordination state
"""

from __future__ import annotations

import asyncio
import hashlib
import time
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    TypeVar,
)

from loguru import logger
from pydantic import BaseModel, Field, field_validator

try:
    import asyncpg

    HAS_ASYNCPG = True
except ImportError:
    HAS_ASYNCPG = False
    asyncpg = None  # type: ignore

try:
    from pgqueuer import PgQueuer

    HAS_PGQUEUER = True
except ImportError:
    HAS_PGQUEUER = False


# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================


class RobotHealthStatus(str, Enum):
    """Health status of a robot."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class LoadBalancingStrategy(str, Enum):
    """Strategies for distributing jobs across robots."""

    ROUND_ROBIN = "round_robin"
    LEAST_BUSY = "least_busy"
    CAPABILITY_BASED = "capability_based"
    RANDOM = "random"
    WEIGHTED = "weighted"
    AFFINITY = "affinity"


class ScalingAction(str, Enum):
    """Auto-scaling action types."""

    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    NO_ACTION = "no_action"


# Default timeouts and intervals
DEFAULT_HEARTBEAT_INTERVAL_SEC = 10
DEFAULT_HEARTBEAT_TIMEOUT_SEC = 30
DEFAULT_LOCK_TIMEOUT_SEC = 300
DEFAULT_HEALTH_CHECK_INTERVAL_SEC = 15


# ============================================================================
# PYDANTIC MODELS
# ============================================================================


class RobotCapabilities(BaseModel):
    """Capabilities and resource specifications of a robot."""

    tags: List[str] = Field(
        default_factory=list,
        description="Capability tags (e.g., 'gpu', 'browser', 'ocr')",
    )
    max_concurrent_jobs: int = Field(
        default=1, ge=1, le=100, description="Maximum concurrent jobs"
    )
    memory_mb: int = Field(default=0, ge=0, description="Available memory in MB")
    cpu_cores: int = Field(default=0, ge=0, description="Available CPU cores")
    has_gpu: bool = Field(default=False, description="GPU availability")
    has_browser: bool = Field(default=True, description="Browser automation support")
    has_desktop: bool = Field(default=True, description="Desktop automation support")
    custom_capabilities: Dict[str, Any] = Field(
        default_factory=dict, description="Custom capability flags"
    )

    def matches_requirements(self, requirements: JobRequirements) -> bool:
        """Check if robot capabilities satisfy job requirements."""
        # Check required tags
        if requirements.required_tags:
            if not all(tag in self.tags for tag in requirements.required_tags):
                return False

        # Check GPU requirement
        if requirements.requires_gpu and not self.has_gpu:
            return False

        # Check browser requirement
        if requirements.requires_browser and not self.has_browser:
            return False

        # Check desktop requirement
        if requirements.requires_desktop and not self.has_desktop:
            return False

        # Check memory requirement
        if (
            requirements.min_memory_mb > 0
            and self.memory_mb < requirements.min_memory_mb
        ):
            return False

        return True


class JobRequirements(BaseModel):
    """Requirements for job execution."""

    required_tags: List[str] = Field(
        default_factory=list, description="Required capability tags"
    )
    preferred_tags: List[str] = Field(
        default_factory=list, description="Preferred but not required tags"
    )
    requires_gpu: bool = Field(default=False, description="Requires GPU")
    requires_browser: bool = Field(
        default=False, description="Requires browser automation"
    )
    requires_desktop: bool = Field(
        default=False, description="Requires desktop automation"
    )
    min_memory_mb: int = Field(
        default=0, ge=0, description="Minimum memory requirement"
    )
    affinity_robot_id: Optional[str] = Field(
        default=None, description="Preferred robot ID for affinity routing"
    )
    environment: str = Field(default="default", description="Target environment")


class RobotMetrics(BaseModel):
    """Runtime metrics from a robot."""

    cpu_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    memory_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    disk_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    current_jobs: int = Field(default=0, ge=0)
    jobs_completed: int = Field(default=0, ge=0)
    jobs_failed: int = Field(default=0, ge=0)
    avg_job_duration_ms: float = Field(default=0.0, ge=0.0)
    uptime_seconds: float = Field(default=0.0, ge=0.0)
    last_job_completed_at: Optional[datetime] = None


class RobotRegistration(BaseModel):
    """Robot registration data for the coordination system."""

    robot_id: str = Field(
        ..., min_length=1, max_length=128, description="Unique robot identifier"
    )
    name: str = Field(
        ..., min_length=1, max_length=256, description="Human-readable robot name"
    )
    environment: str = Field(
        default="default", max_length=64, description="Deployment environment"
    )
    version: str = Field(
        default="1.0.0", max_length=32, description="Robot agent version"
    )
    hostname: str = Field(default="", max_length=256, description="Host machine name")
    ip_address: str = Field(default="", max_length=45, description="Robot IP address")
    capabilities: RobotCapabilities = Field(default_factory=RobotCapabilities)
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @field_validator("robot_id")
    @classmethod
    def validate_robot_id(cls, v: str) -> str:
        """Validate robot_id contains only safe characters."""
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError(
                "robot_id must contain only alphanumeric characters, hyphens, and underscores"
            )
        return v


class RobotState(BaseModel):
    """Current state of a registered robot."""

    robot_id: str
    name: str
    environment: str
    version: str
    hostname: str
    ip_address: str
    capabilities: RobotCapabilities
    metrics: RobotMetrics = Field(default_factory=RobotMetrics)
    health_status: RobotHealthStatus = RobotHealthStatus.UNKNOWN
    is_online: bool = False
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_heartbeat: Optional[datetime] = None
    last_job_assigned_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def is_available(self) -> bool:
        """Check if robot can accept new jobs."""
        return (
            self.is_online
            and self.health_status
            in (RobotHealthStatus.HEALTHY, RobotHealthStatus.DEGRADED)
            and self.metrics.current_jobs < self.capabilities.max_concurrent_jobs
        )

    @property
    def available_slots(self) -> int:
        """Get number of available job slots."""
        return max(0, self.capabilities.max_concurrent_jobs - self.metrics.current_jobs)

    @property
    def load_factor(self) -> float:
        """Get load factor (0.0 to 1.0)."""
        if self.capabilities.max_concurrent_jobs == 0:
            return 1.0
        return self.metrics.current_jobs / self.capabilities.max_concurrent_jobs


class DistributedLock(BaseModel):
    """Distributed lock for exclusive resource access."""

    lock_id: str = Field(..., description="Unique lock identifier")
    resource_id: str = Field(..., description="Resource being locked")
    holder_id: str = Field(..., description="Robot/process holding the lock")
    acquired_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field(..., description="Lock expiration time")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """Check if lock has expired."""
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def ttl_seconds(self) -> float:
        """Get remaining time-to-live in seconds."""
        delta = self.expires_at - datetime.now(timezone.utc)
        return max(0.0, delta.total_seconds())


class ScalingMetrics(BaseModel):
    """Metrics used for auto-scaling decisions."""

    total_robots: int = 0
    online_robots: int = 0
    healthy_robots: int = 0
    total_capacity: int = 0
    current_load: int = 0
    queue_depth: int = 0
    avg_wait_time_ms: float = 0.0
    avg_utilization: float = 0.0


class ScalingDecision(BaseModel):
    """Result of auto-scaling evaluation."""

    action: ScalingAction
    reason: str
    recommended_count: int = 0
    current_count: int = 0
    metrics: ScalingMetrics = Field(default_factory=ScalingMetrics)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ============================================================================
# COORDINATION REPOSITORY INTERFACE
# ============================================================================


class CoordinationRepository(ABC):
    """Abstract interface for coordination state persistence."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to storage backend."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to storage backend."""
        pass

    @abstractmethod
    async def register_robot(self, registration: RobotRegistration) -> RobotState:
        """Register a new robot or update existing registration."""
        pass

    @abstractmethod
    async def unregister_robot(self, robot_id: str) -> bool:
        """Remove a robot from the registry."""
        pass

    @abstractmethod
    async def update_heartbeat(self, robot_id: str, metrics: RobotMetrics) -> bool:
        """Update robot heartbeat and metrics."""
        pass

    @abstractmethod
    async def get_robot(self, robot_id: str) -> Optional[RobotState]:
        """Get robot state by ID."""
        pass

    @abstractmethod
    async def get_all_robots(
        self, environment: Optional[str] = None
    ) -> List[RobotState]:
        """Get all registered robots, optionally filtered by environment."""
        pass

    @abstractmethod
    async def get_available_robots(
        self,
        requirements: Optional[JobRequirements] = None,
        environment: Optional[str] = None,
    ) -> List[RobotState]:
        """Get robots available for job assignment."""
        pass

    @abstractmethod
    async def update_robot_health(
        self, robot_id: str, status: RobotHealthStatus
    ) -> bool:
        """Update robot health status."""
        pass

    @abstractmethod
    async def acquire_lock(
        self,
        resource_id: str,
        holder_id: str,
        timeout_seconds: int = DEFAULT_LOCK_TIMEOUT_SEC,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[DistributedLock]:
        """Attempt to acquire a distributed lock."""
        pass

    @abstractmethod
    async def release_lock(self, resource_id: str, holder_id: str) -> bool:
        """Release a distributed lock."""
        pass

    @abstractmethod
    async def extend_lock(
        self, resource_id: str, holder_id: str, extension_seconds: int
    ) -> bool:
        """Extend a lock's expiration time."""
        pass

    @abstractmethod
    async def get_lock(self, resource_id: str) -> Optional[DistributedLock]:
        """Get current lock state for a resource."""
        pass

    @abstractmethod
    async def cleanup_expired_locks(self) -> int:
        """Remove expired locks. Returns count of locks cleaned."""
        pass

    @abstractmethod
    async def mark_stale_robots_offline(self, timeout_seconds: int) -> int:
        """Mark robots without recent heartbeat as offline. Returns count updated."""
        pass


# ============================================================================
# POSTGRESQL COORDINATION REPOSITORY
# ============================================================================


class PostgresCoordinationRepository(CoordinationRepository):
    """PostgreSQL-backed coordination repository using asyncpg."""

    # SQL statements for table creation
    CREATE_ROBOTS_TABLE = """
        CREATE TABLE IF NOT EXISTS coordination_robots (
            robot_id VARCHAR(128) PRIMARY KEY,
            name VARCHAR(256) NOT NULL,
            environment VARCHAR(64) NOT NULL DEFAULT 'default',
            version VARCHAR(32) NOT NULL DEFAULT '1.0.0',
            hostname VARCHAR(256) DEFAULT '',
            ip_address VARCHAR(45) DEFAULT '',
            capabilities JSONB NOT NULL DEFAULT '{}',
            metrics JSONB NOT NULL DEFAULT '{}',
            health_status VARCHAR(32) NOT NULL DEFAULT 'unknown',
            is_online BOOLEAN NOT NULL DEFAULT FALSE,
            registered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            last_heartbeat TIMESTAMPTZ,
            last_job_assigned_at TIMESTAMPTZ,
            metadata JSONB NOT NULL DEFAULT '{}'
        );
        CREATE INDEX IF NOT EXISTS idx_robots_environment ON coordination_robots(environment);
        CREATE INDEX IF NOT EXISTS idx_robots_is_online ON coordination_robots(is_online);
        CREATE INDEX IF NOT EXISTS idx_robots_health_status ON coordination_robots(health_status);
    """

    CREATE_LOCKS_TABLE = """
        CREATE TABLE IF NOT EXISTS coordination_locks (
            resource_id VARCHAR(256) PRIMARY KEY,
            lock_id VARCHAR(64) NOT NULL,
            holder_id VARCHAR(128) NOT NULL,
            acquired_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            expires_at TIMESTAMPTZ NOT NULL,
            metadata JSONB NOT NULL DEFAULT '{}'
        );
        CREATE INDEX IF NOT EXISTS idx_locks_holder ON coordination_locks(holder_id);
        CREATE INDEX IF NOT EXISTS idx_locks_expires ON coordination_locks(expires_at);
    """

    def __init__(
        self,
        dsn: Optional[str] = None,
        host: str = "localhost",
        port: int = 5432,
        database: str = "casare_rpa",
        user: str = "postgres",
        password: str = "",
        min_pool_size: int = 2,
        max_pool_size: int = 10,
    ):
        """
        Initialize PostgreSQL coordination repository.

        Args:
            dsn: Full connection string (overrides individual params)
            host: Database host
            port: Database port
            database: Database name
            user: Database user
            password: Database password
            min_pool_size: Minimum connection pool size
            max_pool_size: Maximum connection pool size
        """
        if not HAS_ASYNCPG:
            raise ImportError(
                "asyncpg is required for PostgreSQL coordination. Install with: pip install asyncpg"
            )

        self._dsn = dsn
        self._host = host
        self._port = port
        self._database = database
        self._user = user
        self._password = password
        self._min_pool_size = min_pool_size
        self._max_pool_size = max_pool_size

        self._pool: Optional[asyncpg.Pool] = None
        self._connected = False

    async def connect(self) -> None:
        """Establish connection pool and create tables."""
        if self._connected:
            return

        try:
            if self._dsn:
                self._pool = await asyncpg.create_pool(
                    self._dsn,
                    min_size=self._min_pool_size,
                    max_size=self._max_pool_size,
                )
            else:
                self._pool = await asyncpg.create_pool(
                    host=self._host,
                    port=self._port,
                    database=self._database,
                    user=self._user,
                    password=self._password,
                    min_size=self._min_pool_size,
                    max_size=self._max_pool_size,
                )

            # Create tables
            async with self._pool.acquire() as conn:
                await conn.execute(self.CREATE_ROBOTS_TABLE)
                await conn.execute(self.CREATE_LOCKS_TABLE)

            self._connected = True
            logger.info("PostgreSQL coordination repository connected")

        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise

    async def disconnect(self) -> None:
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            self._connected = False
            logger.info("PostgreSQL coordination repository disconnected")

    def _ensure_connected(self) -> None:
        """Raise error if not connected."""
        if not self._connected or not self._pool:
            raise RuntimeError("Repository not connected. Call connect() first.")

    async def register_robot(self, registration: RobotRegistration) -> RobotState:
        """Register or update a robot."""
        self._ensure_connected()

        now = datetime.now(timezone.utc)

        query = """
            INSERT INTO coordination_robots (
                robot_id, name, environment, version, hostname, ip_address,
                capabilities, metrics, health_status, is_online,
                registered_at, last_heartbeat, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            ON CONFLICT (robot_id) DO UPDATE SET
                name = EXCLUDED.name,
                environment = EXCLUDED.environment,
                version = EXCLUDED.version,
                hostname = EXCLUDED.hostname,
                ip_address = EXCLUDED.ip_address,
                capabilities = EXCLUDED.capabilities,
                is_online = EXCLUDED.is_online,
                last_heartbeat = EXCLUDED.last_heartbeat,
                metadata = EXCLUDED.metadata
            RETURNING *
        """

        import json

        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                registration.robot_id,
                registration.name,
                registration.environment,
                registration.version,
                registration.hostname,
                registration.ip_address,
                json.dumps(registration.capabilities.model_dump()),
                json.dumps({}),  # Empty metrics on registration
                RobotHealthStatus.UNKNOWN.value,
                True,
                now,
                now,
                json.dumps(registration.metadata),
            )

        state = self._row_to_robot_state(row)
        logger.info(f"Robot registered: {registration.robot_id} ({registration.name})")
        return state

    async def unregister_robot(self, robot_id: str) -> bool:
        """Remove a robot from the registry."""
        self._ensure_connected()

        query = "DELETE FROM coordination_robots WHERE robot_id = $1"

        async with self._pool.acquire() as conn:
            result = await conn.execute(query, robot_id)

        deleted = result.endswith("1")
        if deleted:
            logger.info(f"Robot unregistered: {robot_id}")
        return deleted

    async def update_heartbeat(self, robot_id: str, metrics: RobotMetrics) -> bool:
        """Update robot heartbeat and metrics."""
        self._ensure_connected()

        import json

        query = """
            UPDATE coordination_robots
            SET last_heartbeat = NOW(),
                is_online = TRUE,
                metrics = $2,
                health_status = CASE
                    WHEN ($2::jsonb->>'cpu_percent')::float > 90 OR
                         ($2::jsonb->>'memory_percent')::float > 95
                    THEN 'degraded'
                    ELSE 'healthy'
                END
            WHERE robot_id = $1
            RETURNING robot_id
        """

        async with self._pool.acquire() as conn:
            result = await conn.fetchval(
                query, robot_id, json.dumps(metrics.model_dump())
            )

        return result is not None

    async def get_robot(self, robot_id: str) -> Optional[RobotState]:
        """Get robot state by ID."""
        self._ensure_connected()

        query = "SELECT * FROM coordination_robots WHERE robot_id = $1"

        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, robot_id)

        if row:
            return self._row_to_robot_state(row)
        return None

    async def get_all_robots(
        self, environment: Optional[str] = None
    ) -> List[RobotState]:
        """Get all registered robots."""
        self._ensure_connected()

        if environment:
            query = (
                "SELECT * FROM coordination_robots WHERE environment = $1 ORDER BY name"
            )
            params = (environment,)
        else:
            query = "SELECT * FROM coordination_robots ORDER BY name"
            params = ()

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

        return [self._row_to_robot_state(row) for row in rows]

    async def get_available_robots(
        self,
        requirements: Optional[JobRequirements] = None,
        environment: Optional[str] = None,
    ) -> List[RobotState]:
        """Get robots available for job assignment."""
        self._ensure_connected()

        query = """
            SELECT * FROM coordination_robots
            WHERE is_online = TRUE
            AND health_status IN ('healthy', 'degraded')
            AND (capabilities->>'max_concurrent_jobs')::int > COALESCE((metrics->>'current_jobs')::int, 0)
        """
        params: List[Any] = []

        if environment:
            query += f" AND environment = ${len(params) + 1}"
            params.append(environment)

        query += " ORDER BY (metrics->>'current_jobs')::int ASC"

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

        robots = [self._row_to_robot_state(row) for row in rows]

        # Apply capability filtering in Python for complex requirements
        if requirements:
            robots = [
                r for r in robots if r.capabilities.matches_requirements(requirements)
            ]

        return robots

    async def update_robot_health(
        self, robot_id: str, status: RobotHealthStatus
    ) -> bool:
        """Update robot health status."""
        self._ensure_connected()

        query = "UPDATE coordination_robots SET health_status = $2 WHERE robot_id = $1 RETURNING robot_id"

        async with self._pool.acquire() as conn:
            result = await conn.fetchval(query, robot_id, status.value)

        return result is not None

    async def acquire_lock(
        self,
        resource_id: str,
        holder_id: str,
        timeout_seconds: int = DEFAULT_LOCK_TIMEOUT_SEC,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[DistributedLock]:
        """Attempt to acquire a distributed lock using PostgreSQL advisory locks."""
        self._ensure_connected()

        import json
        import uuid

        now = datetime.now(timezone.utc)
        expires_at = datetime.fromtimestamp(
            now.timestamp() + timeout_seconds, tz=timezone.utc
        )
        lock_id = str(uuid.uuid4())[:8]

        # Use INSERT with ON CONFLICT to atomically acquire or fail
        query = """
            INSERT INTO coordination_locks (resource_id, lock_id, holder_id, acquired_at, expires_at, metadata)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (resource_id) DO UPDATE SET
                lock_id = EXCLUDED.lock_id,
                holder_id = EXCLUDED.holder_id,
                acquired_at = EXCLUDED.acquired_at,
                expires_at = EXCLUDED.expires_at,
                metadata = EXCLUDED.metadata
            WHERE coordination_locks.expires_at < NOW()
               OR coordination_locks.holder_id = EXCLUDED.holder_id
            RETURNING *
        """

        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    resource_id,
                    lock_id,
                    holder_id,
                    now,
                    expires_at,
                    json.dumps(metadata or {}),
                )

            if row and row["holder_id"] == holder_id:
                lock = DistributedLock(
                    lock_id=row["lock_id"],
                    resource_id=resource_id,
                    holder_id=holder_id,
                    acquired_at=row["acquired_at"],
                    expires_at=row["expires_at"],
                    metadata=metadata or {},
                )
                logger.debug(f"Lock acquired: {resource_id} by {holder_id}")
                return lock

            return None

        except Exception as e:
            logger.error(f"Failed to acquire lock {resource_id}: {e}")
            return None

    async def release_lock(self, resource_id: str, holder_id: str) -> bool:
        """Release a distributed lock."""
        self._ensure_connected()

        query = (
            "DELETE FROM coordination_locks WHERE resource_id = $1 AND holder_id = $2"
        )

        async with self._pool.acquire() as conn:
            result = await conn.execute(query, resource_id, holder_id)

        released = result.endswith("1")
        if released:
            logger.debug(f"Lock released: {resource_id} by {holder_id}")
        return released

    async def extend_lock(
        self, resource_id: str, holder_id: str, extension_seconds: int
    ) -> bool:
        """Extend a lock's expiration time."""
        self._ensure_connected()

        query = """
            UPDATE coordination_locks
            SET expires_at = NOW() + INTERVAL '1 second' * $3
            WHERE resource_id = $1 AND holder_id = $2 AND expires_at > NOW()
            RETURNING resource_id
        """

        async with self._pool.acquire() as conn:
            result = await conn.fetchval(
                query, resource_id, holder_id, extension_seconds
            )

        return result is not None

    async def get_lock(self, resource_id: str) -> Optional[DistributedLock]:
        """Get current lock state for a resource."""
        self._ensure_connected()

        query = "SELECT * FROM coordination_locks WHERE resource_id = $1 AND expires_at > NOW()"

        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, resource_id)

        if row:
            return DistributedLock(
                lock_id=row["lock_id"],
                resource_id=row["resource_id"],
                holder_id=row["holder_id"],
                acquired_at=row["acquired_at"],
                expires_at=row["expires_at"],
                metadata=row["metadata"] if isinstance(row["metadata"], dict) else {},
            )
        return None

    async def cleanup_expired_locks(self) -> int:
        """Remove expired locks."""
        self._ensure_connected()

        query = "DELETE FROM coordination_locks WHERE expires_at < NOW()"

        async with self._pool.acquire() as conn:
            result = await conn.execute(query)

        # Extract count from "DELETE N"
        try:
            count = int(result.split()[-1])
            if count > 0:
                logger.debug(f"Cleaned up {count} expired locks")
            return count
        except (ValueError, IndexError):
            return 0

    async def mark_stale_robots_offline(self, timeout_seconds: int) -> int:
        """Mark robots without recent heartbeat as offline."""
        self._ensure_connected()

        query = """
            UPDATE coordination_robots
            SET is_online = FALSE, health_status = 'unhealthy'
            WHERE is_online = TRUE
            AND last_heartbeat < NOW() - INTERVAL '1 second' * $1
        """

        async with self._pool.acquire() as conn:
            result = await conn.execute(query, timeout_seconds)

        try:
            count = int(result.split()[-1])
            if count > 0:
                logger.warning(f"Marked {count} stale robots as offline")
            return count
        except (ValueError, IndexError):
            return 0

    def _row_to_robot_state(self, row: asyncpg.Record) -> RobotState:
        """Convert database row to RobotState model."""
        import json

        capabilities_data = row["capabilities"]
        if isinstance(capabilities_data, str):
            capabilities_data = json.loads(capabilities_data)

        metrics_data = row["metrics"]
        if isinstance(metrics_data, str):
            metrics_data = json.loads(metrics_data)

        metadata = row["metadata"]
        if isinstance(metadata, str):
            metadata = json.loads(metadata)

        return RobotState(
            robot_id=row["robot_id"],
            name=row["name"],
            environment=row["environment"],
            version=row["version"],
            hostname=row["hostname"],
            ip_address=row["ip_address"],
            capabilities=RobotCapabilities(**capabilities_data),
            metrics=RobotMetrics(**metrics_data),
            health_status=RobotHealthStatus(row["health_status"]),
            is_online=row["is_online"],
            registered_at=row["registered_at"],
            last_heartbeat=row["last_heartbeat"],
            last_job_assigned_at=row.get("last_job_assigned_at"),
            metadata=metadata,
        )


# ============================================================================
# IN-MEMORY COORDINATION REPOSITORY (for testing/development)
# ============================================================================


class InMemoryCoordinationRepository(CoordinationRepository):
    """In-memory coordination repository for testing and development."""

    def __init__(self):
        self._robots: Dict[str, RobotState] = {}
        self._locks: Dict[str, DistributedLock] = {}
        self._connected = False

    async def connect(self) -> None:
        self._connected = True
        logger.info("In-memory coordination repository connected")

    async def disconnect(self) -> None:
        self._connected = False
        self._robots.clear()
        self._locks.clear()
        logger.info("In-memory coordination repository disconnected")

    async def register_robot(self, registration: RobotRegistration) -> RobotState:
        now = datetime.now(timezone.utc)

        existing = self._robots.get(registration.robot_id)

        state = RobotState(
            robot_id=registration.robot_id,
            name=registration.name,
            environment=registration.environment,
            version=registration.version,
            hostname=registration.hostname,
            ip_address=registration.ip_address,
            capabilities=registration.capabilities,
            metrics=existing.metrics if existing else RobotMetrics(),
            health_status=RobotHealthStatus.HEALTHY,
            is_online=True,
            registered_at=existing.registered_at if existing else now,
            last_heartbeat=now,
            metadata=registration.metadata,
        )

        self._robots[registration.robot_id] = state
        logger.info(f"Robot registered: {registration.robot_id}")
        return state

    async def unregister_robot(self, robot_id: str) -> bool:
        if robot_id in self._robots:
            del self._robots[robot_id]
            logger.info(f"Robot unregistered: {robot_id}")
            return True
        return False

    async def update_heartbeat(self, robot_id: str, metrics: RobotMetrics) -> bool:
        if robot_id not in self._robots:
            return False

        robot = self._robots[robot_id]
        robot.last_heartbeat = datetime.now(timezone.utc)
        robot.metrics = metrics
        robot.is_online = True

        # Auto-detect health status
        if metrics.cpu_percent > 90 or metrics.memory_percent > 95:
            robot.health_status = RobotHealthStatus.DEGRADED
        else:
            robot.health_status = RobotHealthStatus.HEALTHY

        return True

    async def get_robot(self, robot_id: str) -> Optional[RobotState]:
        return self._robots.get(robot_id)

    async def get_all_robots(
        self, environment: Optional[str] = None
    ) -> List[RobotState]:
        robots = list(self._robots.values())
        if environment:
            robots = [r for r in robots if r.environment == environment]
        return sorted(robots, key=lambda r: r.name)

    async def get_available_robots(
        self,
        requirements: Optional[JobRequirements] = None,
        environment: Optional[str] = None,
    ) -> List[RobotState]:
        robots = [r for r in self._robots.values() if r.is_available]

        if environment:
            robots = [r for r in robots if r.environment == environment]

        if requirements:
            robots = [
                r for r in robots if r.capabilities.matches_requirements(requirements)
            ]

        return sorted(robots, key=lambda r: r.metrics.current_jobs)

    async def update_robot_health(
        self, robot_id: str, status: RobotHealthStatus
    ) -> bool:
        if robot_id not in self._robots:
            return False
        self._robots[robot_id].health_status = status
        return True

    async def acquire_lock(
        self,
        resource_id: str,
        holder_id: str,
        timeout_seconds: int = DEFAULT_LOCK_TIMEOUT_SEC,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[DistributedLock]:
        now = datetime.now(timezone.utc)

        # Check existing lock
        existing = self._locks.get(resource_id)
        if existing and not existing.is_expired and existing.holder_id != holder_id:
            return None  # Lock held by another holder

        import uuid

        expires_at = datetime.fromtimestamp(
            now.timestamp() + timeout_seconds, tz=timezone.utc
        )

        lock = DistributedLock(
            lock_id=str(uuid.uuid4())[:8],
            resource_id=resource_id,
            holder_id=holder_id,
            acquired_at=now,
            expires_at=expires_at,
            metadata=metadata or {},
        )

        self._locks[resource_id] = lock
        logger.debug(f"Lock acquired: {resource_id} by {holder_id}")
        return lock

    async def release_lock(self, resource_id: str, holder_id: str) -> bool:
        lock = self._locks.get(resource_id)
        if lock and lock.holder_id == holder_id:
            del self._locks[resource_id]
            logger.debug(f"Lock released: {resource_id}")
            return True
        return False

    async def extend_lock(
        self, resource_id: str, holder_id: str, extension_seconds: int
    ) -> bool:
        lock = self._locks.get(resource_id)
        if lock and lock.holder_id == holder_id and not lock.is_expired:
            new_expires = datetime.fromtimestamp(
                datetime.now(timezone.utc).timestamp() + extension_seconds,
                tz=timezone.utc,
            )
            self._locks[resource_id] = DistributedLock(
                lock_id=lock.lock_id,
                resource_id=lock.resource_id,
                holder_id=lock.holder_id,
                acquired_at=lock.acquired_at,
                expires_at=new_expires,
                metadata=lock.metadata,
            )
            return True
        return False

    async def get_lock(self, resource_id: str) -> Optional[DistributedLock]:
        lock = self._locks.get(resource_id)
        if lock and not lock.is_expired:
            return lock
        return None

    async def cleanup_expired_locks(self) -> int:
        expired = [rid for rid, lock in self._locks.items() if lock.is_expired]
        for rid in expired:
            del self._locks[rid]
        return len(expired)

    async def mark_stale_robots_offline(self, timeout_seconds: int) -> int:
        now = datetime.now(timezone.utc)
        count = 0

        for robot in self._robots.values():
            if robot.is_online and robot.last_heartbeat:
                if (now - robot.last_heartbeat).total_seconds() > timeout_seconds:
                    robot.is_online = False
                    robot.health_status = RobotHealthStatus.UNHEALTHY
                    count += 1

        if count > 0:
            logger.warning(f"Marked {count} stale robots as offline")
        return count


# ============================================================================
# LOAD BALANCER
# ============================================================================


class LoadBalancer:
    """Implements multiple load balancing strategies for robot selection."""

    def __init__(
        self, default_strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEAST_BUSY
    ):
        self._default_strategy = default_strategy
        self._round_robin_index: Dict[str, int] = {}  # environment -> index
        self._affinity_map: Dict[str, str] = {}  # workflow_id -> robot_id

    def select_robot(
        self,
        available_robots: List[RobotState],
        strategy: Optional[LoadBalancingStrategy] = None,
        requirements: Optional[JobRequirements] = None,
    ) -> Optional[RobotState]:
        """
        Select the best robot for a job using the specified strategy.

        Args:
            available_robots: List of available robots
            strategy: Load balancing strategy (uses default if not specified)
            requirements: Optional job requirements for capability matching

        Returns:
            Selected robot or None if no suitable robot available
        """
        if not available_robots:
            return None

        strategy = strategy or self._default_strategy

        # Filter by requirements first
        if requirements:
            available_robots = [
                r
                for r in available_robots
                if r.capabilities.matches_requirements(requirements)
            ]
            if not available_robots:
                return None

        # Check for affinity
        if requirements and requirements.affinity_robot_id:
            affinity_match = next(
                (
                    r
                    for r in available_robots
                    if r.robot_id == requirements.affinity_robot_id
                ),
                None,
            )
            if affinity_match:
                return affinity_match

        # Apply strategy
        if strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._select_round_robin(available_robots)
        elif strategy == LoadBalancingStrategy.LEAST_BUSY:
            return self._select_least_busy(available_robots)
        elif strategy == LoadBalancingStrategy.CAPABILITY_BASED:
            return self._select_by_capability(available_robots, requirements)
        elif strategy == LoadBalancingStrategy.RANDOM:
            return self._select_random(available_robots)
        elif strategy == LoadBalancingStrategy.WEIGHTED:
            return self._select_weighted(available_robots)
        elif strategy == LoadBalancingStrategy.AFFINITY:
            return self._select_least_busy(
                available_robots
            )  # Fallback for affinity without match
        else:
            return self._select_least_busy(available_robots)

    def _select_round_robin(self, robots: List[RobotState]) -> RobotState:
        """Round-robin selection across robots."""
        if not robots:
            raise ValueError("No robots available")

        # Group by environment for round-robin within environment
        env = robots[0].environment
        idx = self._round_robin_index.get(env, 0)
        idx = idx % len(robots)
        self._round_robin_index[env] = idx + 1
        return robots[idx]

    def _select_least_busy(self, robots: List[RobotState]) -> RobotState:
        """Select robot with lowest load factor."""
        return min(robots, key=lambda r: (r.load_factor, r.metrics.current_jobs))

    def _select_by_capability(
        self,
        robots: List[RobotState],
        requirements: Optional[JobRequirements] = None,
    ) -> RobotState:
        """Select robot with best capability match."""
        if not requirements or not requirements.preferred_tags:
            return self._select_least_busy(robots)

        def capability_score(robot: RobotState) -> Tuple[int, float]:
            # Count matching preferred tags (negative for max-heap effect with min)
            matched = sum(
                1
                for tag in requirements.preferred_tags
                if tag in robot.capabilities.tags
            )
            return (-matched, robot.load_factor)

        return min(robots, key=capability_score)

    def _select_random(self, robots: List[RobotState]) -> RobotState:
        """Random selection."""
        import random

        return random.choice(robots)

    def _select_weighted(self, robots: List[RobotState]) -> RobotState:
        """Weighted selection based on available capacity."""
        import random

        # Weight by available slots
        weights = [r.available_slots for r in robots]
        total_weight = sum(weights)

        if total_weight == 0:
            return self._select_random(robots)

        rand = random.uniform(0, total_weight)
        cumulative = 0.0
        for robot, weight in zip(robots, weights):
            cumulative += weight
            if rand <= cumulative:
                return robot

        return robots[-1]

    def set_affinity(self, workflow_id: str, robot_id: str) -> None:
        """Set workflow affinity to a specific robot."""
        self._affinity_map[workflow_id] = robot_id

    def clear_affinity(self, workflow_id: str) -> None:
        """Clear workflow affinity."""
        self._affinity_map.pop(workflow_id, None)

    def get_affinity(self, workflow_id: str) -> Optional[str]:
        """Get affinity robot for a workflow."""
        return self._affinity_map.get(workflow_id)


# ============================================================================
# AUTO-SCALING EVALUATOR
# ============================================================================


@dataclass
class ScalingConfig:
    """Configuration for auto-scaling behavior."""

    min_robots: int = 1
    max_robots: int = 10
    scale_up_threshold: float = 0.8  # Scale up when avg utilization > 80%
    scale_down_threshold: float = 0.3  # Scale down when avg utilization < 30%
    queue_depth_scale_up: int = 10  # Scale up when queue depth > 10
    cooldown_seconds: int = 300  # Minimum time between scaling actions
    evaluation_window_seconds: int = 60  # Window for averaging metrics


class AutoScalingEvaluator:
    """Evaluates metrics and recommends scaling actions."""

    def __init__(self, config: Optional[ScalingConfig] = None):
        self._config = config or ScalingConfig()
        self._last_scale_action: Optional[datetime] = None

    def evaluate(
        self,
        robots: List[RobotState],
        queue_depth: int = 0,
        avg_wait_time_ms: float = 0.0,
    ) -> ScalingDecision:
        """
        Evaluate current metrics and recommend scaling action.

        Args:
            robots: Current robot states
            queue_depth: Number of jobs waiting in queue
            avg_wait_time_ms: Average queue wait time

        Returns:
            Scaling decision with recommended action
        """
        now = datetime.now(timezone.utc)

        # Check cooldown
        if self._last_scale_action:
            elapsed = (now - self._last_scale_action).total_seconds()
            if elapsed < self._config.cooldown_seconds:
                return ScalingDecision(
                    action=ScalingAction.NO_ACTION,
                    reason=f"In cooldown period ({int(self._config.cooldown_seconds - elapsed)}s remaining)",
                    current_count=len(robots),
                    metrics=self._compute_metrics(
                        robots, queue_depth, avg_wait_time_ms
                    ),
                )

        metrics = self._compute_metrics(robots, queue_depth, avg_wait_time_ms)
        online_count = metrics.online_robots

        # Check for scale up conditions
        if self._should_scale_up(metrics):
            new_count = min(online_count + 1, self._config.max_robots)
            if new_count > online_count:
                return ScalingDecision(
                    action=ScalingAction.SCALE_UP,
                    reason=self._get_scale_up_reason(metrics),
                    recommended_count=new_count,
                    current_count=online_count,
                    metrics=metrics,
                )

        # Check for scale down conditions
        if self._should_scale_down(metrics):
            new_count = max(online_count - 1, self._config.min_robots)
            if new_count < online_count:
                return ScalingDecision(
                    action=ScalingAction.SCALE_DOWN,
                    reason=self._get_scale_down_reason(metrics),
                    recommended_count=new_count,
                    current_count=online_count,
                    metrics=metrics,
                )

        return ScalingDecision(
            action=ScalingAction.NO_ACTION,
            reason="Metrics within acceptable range",
            current_count=online_count,
            metrics=metrics,
        )

    def record_scaling_action(self) -> None:
        """Record that a scaling action was taken (resets cooldown)."""
        self._last_scale_action = datetime.now(timezone.utc)

    def _compute_metrics(
        self,
        robots: List[RobotState],
        queue_depth: int,
        avg_wait_time_ms: float,
    ) -> ScalingMetrics:
        """Compute scaling metrics from robot states."""
        online_robots = [r for r in robots if r.is_online]
        healthy_robots = [
            r for r in online_robots if r.health_status == RobotHealthStatus.HEALTHY
        ]

        total_capacity = sum(r.capabilities.max_concurrent_jobs for r in online_robots)
        current_load = sum(r.metrics.current_jobs for r in online_robots)

        avg_utilization = (current_load / total_capacity) if total_capacity > 0 else 0.0

        return ScalingMetrics(
            total_robots=len(robots),
            online_robots=len(online_robots),
            healthy_robots=len(healthy_robots),
            total_capacity=total_capacity,
            current_load=current_load,
            queue_depth=queue_depth,
            avg_wait_time_ms=avg_wait_time_ms,
            avg_utilization=avg_utilization,
        )

    def _should_scale_up(self, metrics: ScalingMetrics) -> bool:
        """Check if we should scale up."""
        if metrics.online_robots >= self._config.max_robots:
            return False

        # High utilization
        if metrics.avg_utilization > self._config.scale_up_threshold:
            return True

        # Large queue
        if metrics.queue_depth > self._config.queue_depth_scale_up:
            return True

        # No healthy robots
        if metrics.healthy_robots == 0 and metrics.online_robots > 0:
            return True

        return False

    def _should_scale_down(self, metrics: ScalingMetrics) -> bool:
        """Check if we should scale down."""
        if metrics.online_robots <= self._config.min_robots:
            return False

        # Low utilization and empty queue
        if (
            metrics.avg_utilization < self._config.scale_down_threshold
            and metrics.queue_depth == 0
        ):
            return True

        return False

    def _get_scale_up_reason(self, metrics: ScalingMetrics) -> str:
        """Get human-readable reason for scale up."""
        reasons = []
        if metrics.avg_utilization > self._config.scale_up_threshold:
            reasons.append(f"High utilization ({metrics.avg_utilization:.1%})")
        if metrics.queue_depth > self._config.queue_depth_scale_up:
            reasons.append(f"Large queue depth ({metrics.queue_depth})")
        if metrics.healthy_robots == 0:
            reasons.append("No healthy robots")
        return "; ".join(reasons) if reasons else "Scale up recommended"

    def _get_scale_down_reason(self, metrics: ScalingMetrics) -> str:
        """Get human-readable reason for scale down."""
        return f"Low utilization ({metrics.avg_utilization:.1%}) with empty queue"


# ============================================================================
# ROBOT COORDINATOR - MAIN ORCHESTRATION CLASS
# ============================================================================


class RobotCoordinator:
    """
    Central coordinator for multi-robot fleet management.

    Integrates:
    - Robot registration and heartbeat monitoring
    - Load balancing across robots
    - Job affinity routing
    - Distributed locking
    - Health monitoring
    - Auto-scaling triggers

    Usage:
        coordinator = RobotCoordinator(
            repository=PostgresCoordinationRepository(dsn="postgresql://..."),
            load_balancing_strategy=LoadBalancingStrategy.LEAST_BUSY,
        )
        await coordinator.start()

        # Register robots
        state = await coordinator.register_robot(RobotRegistration(...))

        # Get best robot for a job
        robot = await coordinator.select_robot_for_job(JobRequirements(...))

        # Use distributed locks
        async with coordinator.lock("resource-123", "robot-1"):
            # Exclusive access to resource
            pass

        await coordinator.stop()
    """

    def __init__(
        self,
        repository: Optional[CoordinationRepository] = None,
        load_balancing_strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEAST_BUSY,
        heartbeat_timeout_seconds: int = DEFAULT_HEARTBEAT_TIMEOUT_SEC,
        health_check_interval_seconds: int = DEFAULT_HEALTH_CHECK_INTERVAL_SEC,
        scaling_config: Optional[ScalingConfig] = None,
        on_robot_online: Optional[Callable[[RobotState], None]] = None,
        on_robot_offline: Optional[Callable[[str], None]] = None,
        on_scaling_recommendation: Optional[Callable[[ScalingDecision], None]] = None,
    ):
        """
        Initialize the robot coordinator.

        Args:
            repository: Coordination state repository (defaults to in-memory)
            load_balancing_strategy: Default load balancing strategy
            heartbeat_timeout_seconds: Time before marking robot offline
            health_check_interval_seconds: Interval between health checks
            scaling_config: Auto-scaling configuration
            on_robot_online: Callback when robot comes online
            on_robot_offline: Callback when robot goes offline
            on_scaling_recommendation: Callback for scaling recommendations
        """
        self._repository = repository or InMemoryCoordinationRepository()
        self._load_balancer = LoadBalancer(load_balancing_strategy)
        self._scaling_evaluator = AutoScalingEvaluator(scaling_config)

        self._heartbeat_timeout = heartbeat_timeout_seconds
        self._health_check_interval = health_check_interval_seconds

        self._on_robot_online = on_robot_online
        self._on_robot_offline = on_robot_offline
        self._on_scaling_recommendation = on_scaling_recommendation

        self._running = False
        self._health_check_task: Optional[asyncio.Task] = None
        self._lock_cleanup_task: Optional[asyncio.Task] = None

        logger.info("RobotCoordinator initialized")

    async def start(self) -> None:
        """Start the coordinator and background tasks."""
        if self._running:
            return

        await self._repository.connect()
        self._running = True

        # Start background tasks
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        self._lock_cleanup_task = asyncio.create_task(self._lock_cleanup_loop())

        logger.info("RobotCoordinator started")

    async def stop(self) -> None:
        """Stop the coordinator and cleanup."""
        self._running = False

        # Cancel background tasks
        for task in [self._health_check_task, self._lock_cleanup_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        await self._repository.disconnect()
        logger.info("RobotCoordinator stopped")

    # ==================== ROBOT MANAGEMENT ====================

    async def register_robot(self, registration: RobotRegistration) -> RobotState:
        """
        Register a new robot or update existing registration.

        Args:
            registration: Robot registration data

        Returns:
            Current robot state after registration
        """
        state = await self._repository.register_robot(registration)

        if self._on_robot_online:
            try:
                self._on_robot_online(state)
            except Exception as e:
                logger.error(f"Error in on_robot_online callback: {e}")

        return state

    async def unregister_robot(self, robot_id: str) -> bool:
        """
        Unregister a robot from the fleet.

        Args:
            robot_id: Robot ID to unregister

        Returns:
            True if robot was unregistered
        """
        success = await self._repository.unregister_robot(robot_id)

        if success and self._on_robot_offline:
            try:
                self._on_robot_offline(robot_id)
            except Exception as e:
                logger.error(f"Error in on_robot_offline callback: {e}")

        return success

    async def heartbeat(self, robot_id: str, metrics: RobotMetrics) -> bool:
        """
        Process robot heartbeat with metrics update.

        Args:
            robot_id: Robot ID
            metrics: Current robot metrics

        Returns:
            True if heartbeat was processed successfully
        """
        return await self._repository.update_heartbeat(robot_id, metrics)

    async def get_robot(self, robot_id: str) -> Optional[RobotState]:
        """Get robot state by ID."""
        return await self._repository.get_robot(robot_id)

    async def get_all_robots(
        self, environment: Optional[str] = None
    ) -> List[RobotState]:
        """Get all registered robots."""
        return await self._repository.get_all_robots(environment)

    async def get_available_robots(
        self,
        requirements: Optional[JobRequirements] = None,
        environment: Optional[str] = None,
    ) -> List[RobotState]:
        """Get robots available for job assignment."""
        return await self._repository.get_available_robots(requirements, environment)

    # ==================== LOAD BALANCING ====================

    async def select_robot_for_job(
        self,
        requirements: Optional[JobRequirements] = None,
        strategy: Optional[LoadBalancingStrategy] = None,
        environment: Optional[str] = None,
    ) -> Optional[RobotState]:
        """
        Select the best robot for a job using load balancing.

        Args:
            requirements: Job requirements for capability matching
            strategy: Load balancing strategy override
            environment: Target environment filter

        Returns:
            Selected robot or None if no suitable robot available
        """
        env = environment or (requirements.environment if requirements else None)
        available = await self._repository.get_available_robots(requirements, env)

        if not available:
            logger.warning(f"No available robots for requirements: {requirements}")
            return None

        selected = self._load_balancer.select_robot(available, strategy, requirements)

        if selected:
            logger.debug(
                f"Selected robot {selected.robot_id} for job (strategy={strategy})"
            )

        return selected

    def set_job_affinity(self, workflow_id: str, robot_id: str) -> None:
        """Set workflow affinity to a specific robot."""
        self._load_balancer.set_affinity(workflow_id, robot_id)
        logger.debug(f"Set affinity: workflow {workflow_id} -> robot {robot_id}")

    def clear_job_affinity(self, workflow_id: str) -> None:
        """Clear workflow affinity."""
        self._load_balancer.clear_affinity(workflow_id)

    # ==================== DISTRIBUTED LOCKING ====================

    async def acquire_lock(
        self,
        resource_id: str,
        holder_id: str,
        timeout_seconds: int = DEFAULT_LOCK_TIMEOUT_SEC,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[DistributedLock]:
        """
        Acquire a distributed lock for exclusive resource access.

        Args:
            resource_id: Unique identifier for the resource to lock
            holder_id: ID of the robot/process acquiring the lock
            timeout_seconds: Lock timeout
            metadata: Optional metadata to store with lock

        Returns:
            Lock object if acquired, None if resource already locked
        """
        return await self._repository.acquire_lock(
            resource_id, holder_id, timeout_seconds, metadata
        )

    async def release_lock(self, resource_id: str, holder_id: str) -> bool:
        """Release a distributed lock."""
        return await self._repository.release_lock(resource_id, holder_id)

    async def extend_lock(
        self, resource_id: str, holder_id: str, extension_seconds: int
    ) -> bool:
        """Extend a lock's expiration time."""
        return await self._repository.extend_lock(
            resource_id, holder_id, extension_seconds
        )

    async def get_lock(self, resource_id: str) -> Optional[DistributedLock]:
        """Get current lock state for a resource."""
        return await self._repository.get_lock(resource_id)

    @asynccontextmanager
    async def lock(
        self,
        resource_id: str,
        holder_id: str,
        timeout_seconds: int = DEFAULT_LOCK_TIMEOUT_SEC,
        retry_interval: float = 0.5,
        max_retries: int = 10,
    ) -> AsyncIterator[DistributedLock]:
        """
        Context manager for distributed locking with automatic retry and release.

        Usage:
            async with coordinator.lock("resource-id", "robot-id") as lock:
                # Exclusive access to resource
                pass
            # Lock automatically released

        Args:
            resource_id: Resource to lock
            holder_id: ID of holder
            timeout_seconds: Lock timeout
            retry_interval: Seconds between retries
            max_retries: Maximum acquisition attempts

        Yields:
            Acquired lock

        Raises:
            RuntimeError: If lock cannot be acquired after max_retries
        """
        lock_obj: Optional[DistributedLock] = None

        for attempt in range(max_retries):
            lock_obj = await self.acquire_lock(resource_id, holder_id, timeout_seconds)
            if lock_obj:
                break
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_interval)

        if not lock_obj:
            raise RuntimeError(
                f"Failed to acquire lock on {resource_id} after {max_retries} attempts"
            )

        try:
            yield lock_obj
        finally:
            await self.release_lock(resource_id, holder_id)

    # ==================== HEALTH MONITORING ====================

    async def update_robot_health(
        self, robot_id: str, status: RobotHealthStatus
    ) -> bool:
        """Manually update robot health status."""
        return await self._repository.update_robot_health(robot_id, status)

    async def check_fleet_health(self) -> Dict[str, Any]:
        """
        Get comprehensive fleet health report.

        Returns:
            Dictionary with health metrics and robot states
        """
        robots = await self._repository.get_all_robots()

        total = len(robots)
        online = sum(1 for r in robots if r.is_online)
        healthy = sum(1 for r in robots if r.health_status == RobotHealthStatus.HEALTHY)
        degraded = sum(
            1 for r in robots if r.health_status == RobotHealthStatus.DEGRADED
        )
        unhealthy = sum(
            1 for r in robots if r.health_status == RobotHealthStatus.UNHEALTHY
        )

        total_capacity = sum(
            r.capabilities.max_concurrent_jobs for r in robots if r.is_online
        )
        current_load = sum(r.metrics.current_jobs for r in robots if r.is_online)

        return {
            "total_robots": total,
            "online_robots": online,
            "offline_robots": total - online,
            "healthy_robots": healthy,
            "degraded_robots": degraded,
            "unhealthy_robots": unhealthy,
            "total_capacity": total_capacity,
            "current_load": current_load,
            "utilization": (current_load / total_capacity)
            if total_capacity > 0
            else 0.0,
            "robots": [
                {
                    "robot_id": r.robot_id,
                    "name": r.name,
                    "environment": r.environment,
                    "is_online": r.is_online,
                    "health_status": r.health_status.value,
                    "load": f"{r.metrics.current_jobs}/{r.capabilities.max_concurrent_jobs}",
                }
                for r in robots
            ],
        }

    # ==================== AUTO-SCALING ====================

    async def evaluate_scaling(
        self, queue_depth: int = 0, avg_wait_time_ms: float = 0.0
    ) -> ScalingDecision:
        """
        Evaluate current metrics and get scaling recommendation.

        Args:
            queue_depth: Number of jobs waiting in queue
            avg_wait_time_ms: Average queue wait time

        Returns:
            Scaling decision with recommended action
        """
        robots = await self._repository.get_all_robots()
        decision = self._scaling_evaluator.evaluate(
            robots, queue_depth, avg_wait_time_ms
        )

        if (
            decision.action != ScalingAction.NO_ACTION
            and self._on_scaling_recommendation
        ):
            try:
                self._on_scaling_recommendation(decision)
            except Exception as e:
                logger.error(f"Error in scaling recommendation callback: {e}")

        return decision

    def record_scaling_action(self) -> None:
        """Record that a scaling action was taken (resets cooldown)."""
        self._scaling_evaluator.record_scaling_action()

    # ==================== BACKGROUND TASKS ====================

    async def _health_check_loop(self) -> None:
        """Background task for health monitoring."""
        while self._running:
            try:
                # Mark stale robots as offline
                stale_count = await self._repository.mark_stale_robots_offline(
                    self._heartbeat_timeout
                )

                if stale_count > 0 and self._on_robot_offline:
                    # Get offline robots to notify
                    all_robots = await self._repository.get_all_robots()
                    offline = [r for r in all_robots if not r.is_online]
                    for robot in offline:
                        try:
                            self._on_robot_offline(robot.robot_id)
                        except Exception as e:
                            logger.error(f"Error in on_robot_offline callback: {e}")

                await asyncio.sleep(self._health_check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(self._health_check_interval)

    async def _lock_cleanup_loop(self) -> None:
        """Background task for cleaning up expired locks."""
        while self._running:
            try:
                await self._repository.cleanup_expired_locks()
                await asyncio.sleep(60)  # Cleanup every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Lock cleanup error: {e}")
                await asyncio.sleep(60)

    # ==================== STATISTICS ====================

    def get_load_balancer_stats(self) -> Dict[str, Any]:
        """Get load balancer statistics."""
        return {
            "default_strategy": self._load_balancer._default_strategy.value,
            "affinity_count": len(self._load_balancer._affinity_map),
        }


# ============================================================================
# PGQUEUER INTEGRATION
# ============================================================================


class PgQueuerJobDistributor:
    """
    Integrates RobotCoordinator with PgQueuer for distributed job distribution.

    This class bridges the coordination system with PgQueuer to:
    - Route jobs to capable robots based on requirements
    - Use load balancing for robot selection
    - Support job affinity
    - Handle exclusive resource locking for jobs
    """

    def __init__(
        self,
        coordinator: RobotCoordinator,
        pgqueuer_dsn: Optional[str] = None,
    ):
        """
        Initialize PgQueuer job distributor.

        Args:
            coordinator: Robot coordinator instance
            pgqueuer_dsn: PostgreSQL connection string for PgQueuer
        """
        if not HAS_PGQUEUER:
            logger.warning(
                "PgQueuer not installed. Job distribution via PgQueuer disabled."
            )

        self._coordinator = coordinator
        self._pgqueuer_dsn = pgqueuer_dsn
        self._pgqueuer: Optional[PgQueuer] = None

    async def start(self) -> None:
        """Start the job distributor."""
        if HAS_PGQUEUER and self._pgqueuer_dsn:
            # PgQueuer initialization would go here
            # This is a placeholder for actual PgQueuer integration
            logger.info("PgQueuer job distributor started")

    async def stop(self) -> None:
        """Stop the job distributor."""
        if self._pgqueuer:
            # PgQueuer cleanup would go here
            pass
        logger.info("PgQueuer job distributor stopped")

    async def route_job(
        self,
        job_id: str,
        workflow_id: str,
        requirements: Optional[JobRequirements] = None,
        strategy: Optional[LoadBalancingStrategy] = None,
    ) -> Optional[str]:
        """
        Route a job to the best available robot.

        Args:
            job_id: Job ID
            workflow_id: Workflow ID (for affinity)
            requirements: Job requirements
            strategy: Load balancing strategy override

        Returns:
            Selected robot_id or None if no robot available
        """
        # Check for workflow affinity
        affinity_robot = self._coordinator._load_balancer.get_affinity(workflow_id)
        if affinity_robot and requirements:
            requirements = JobRequirements(
                **requirements.model_dump(),
                affinity_robot_id=affinity_robot,
            )

        robot = await self._coordinator.select_robot_for_job(requirements, strategy)

        if robot:
            logger.info(f"Job {job_id} routed to robot {robot.robot_id}")
            return robot.robot_id

        logger.warning(f"No robot available for job {job_id}")
        return None

    async def claim_job_for_robot(
        self,
        robot_id: str,
        job_id: str,
        lock_resource: Optional[str] = None,
        lock_timeout: int = DEFAULT_LOCK_TIMEOUT_SEC,
    ) -> bool:
        """
        Claim a job for a robot, optionally acquiring an exclusive lock.

        Args:
            robot_id: Robot claiming the job
            job_id: Job to claim
            lock_resource: Optional resource to lock exclusively
            lock_timeout: Lock timeout in seconds

        Returns:
            True if job was claimed successfully
        """
        # Acquire lock if needed
        if lock_resource:
            lock = await self._coordinator.acquire_lock(
                lock_resource, robot_id, lock_timeout
            )
            if not lock:
                logger.warning(
                    f"Robot {robot_id} failed to acquire lock on {lock_resource} for job {job_id}"
                )
                return False

        logger.debug(f"Robot {robot_id} claimed job {job_id}")
        return True

    async def release_job(
        self,
        robot_id: str,
        job_id: str,
        lock_resource: Optional[str] = None,
    ) -> None:
        """
        Release a job and any associated locks.

        Args:
            robot_id: Robot releasing the job
            job_id: Job being released
            lock_resource: Optional resource lock to release
        """
        if lock_resource:
            await self._coordinator.release_lock(lock_resource, robot_id)

        logger.debug(f"Robot {robot_id} released job {job_id}")
