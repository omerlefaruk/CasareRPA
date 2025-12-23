"""PostgreSQL robot repository implementation.

Provides persistent storage for robot registry, replacing in-memory state
that would be lost on orchestrator restart.

Features:
- Robot registration with UPSERT (handles reconnections)
- Heartbeat-based online detection (configurable timeout)
- Read-through cache for hot paths (optional)
- Tenant isolation support
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set

import orjson
from loguru import logger

from casare_rpa.domain.orchestrator.entities import Robot, RobotCapability, RobotStatus
from casare_rpa.domain.orchestrator.repositories import RobotRepository


class PgRobotRepository(RobotRepository):
    """PostgreSQL-backed robot repository.

    Uses asyncpg for async database access with connection pooling.
    Implements the RobotRepository protocol for DDD compliance.

    Note: WebSocket connections are NOT stored in database (not serializable).
    The repository handles persistent state only - connection objects are
    managed separately in RobotManager._connections dict.
    """

    # SQL Statements
    SQL_UPSERT_ROBOT = """
        INSERT INTO robots (
            robot_id, name, hostname, status, environment,
            capabilities, max_concurrent_jobs, current_job_ids,
            tags, metrics, tenant_id, last_heartbeat, last_seen, created_at
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14
        )
        ON CONFLICT (robot_id) DO UPDATE SET
            name = EXCLUDED.name,
            hostname = EXCLUDED.hostname,
            status = EXCLUDED.status,
            environment = EXCLUDED.environment,
            capabilities = EXCLUDED.capabilities,
            max_concurrent_jobs = EXCLUDED.max_concurrent_jobs,
            current_job_ids = EXCLUDED.current_job_ids,
            tags = EXCLUDED.tags,
            metrics = EXCLUDED.metrics,
            tenant_id = EXCLUDED.tenant_id,
            last_heartbeat = EXCLUDED.last_heartbeat,
            last_seen = EXCLUDED.last_seen
        RETURNING robot_id;
    """

    SQL_GET_BY_ID = """
        SELECT robot_id, name, hostname, status, environment,
               capabilities, max_concurrent_jobs, current_job_ids,
               tags, metrics, tenant_id, last_heartbeat, last_seen, created_at
        FROM robots
        WHERE robot_id = $1;
    """

    SQL_GET_ALL = """
        SELECT robot_id, name, hostname, status, environment,
               capabilities, max_concurrent_jobs, current_job_ids,
               tags, metrics, tenant_id, last_heartbeat, last_seen, created_at
        FROM robots
        ORDER BY name;
    """

    SQL_GET_ALL_ONLINE = """
        SELECT robot_id, name, hostname, status, environment,
               capabilities, max_concurrent_jobs, current_job_ids,
               tags, metrics, tenant_id, last_heartbeat, last_seen, created_at
        FROM robots
        WHERE status != 'offline'
          AND last_heartbeat > $1
        ORDER BY name;
    """

    SQL_GET_BY_ENVIRONMENT = """
        SELECT robot_id, name, hostname, status, environment,
               capabilities, max_concurrent_jobs, current_job_ids,
               tags, metrics, tenant_id, last_heartbeat, last_seen, created_at
        FROM robots
        WHERE environment = $1
        ORDER BY name;
    """

    SQL_GET_BY_TENANT = """
        SELECT robot_id, name, hostname, status, environment,
               capabilities, max_concurrent_jobs, current_job_ids,
               tags, metrics, tenant_id, last_heartbeat, last_seen, created_at
        FROM robots
        WHERE tenant_id = $1
        ORDER BY name;
    """

    SQL_UPDATE_STATUS = """
        UPDATE robots
        SET status = $2, last_seen = $3
        WHERE robot_id = $1;
    """

    SQL_UPDATE_HEARTBEAT = """
        UPDATE robots
        SET last_heartbeat = $2, last_seen = $2, metrics = $3
        WHERE robot_id = $1;
    """

    SQL_UPDATE_CURRENT_JOBS = """
        UPDATE robots
        SET current_job_ids = $2, last_seen = $3
        WHERE robot_id = $1;
    """

    SQL_DELETE = """
        DELETE FROM robots
        WHERE robot_id = $1;
    """

    def __init__(
        self,
        db_pool: Any,
        heartbeat_timeout_seconds: int = 90,
    ):
        """Initialize PostgreSQL robot repository.

        Args:
            db_pool: asyncpg connection pool
            heartbeat_timeout_seconds: Seconds before robot considered offline
        """
        self._pool = db_pool
        self._heartbeat_timeout = timedelta(seconds=heartbeat_timeout_seconds)

    async def get_by_id(self, robot_id: str) -> Optional[Robot]:
        """Get robot by ID."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(self.SQL_GET_BY_ID, robot_id)
            if row:
                return self._row_to_robot(row)
            return None

    async def get_all(self) -> List[Robot]:
        """Get all robots."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(self.SQL_GET_ALL)
            return [self._row_to_robot(row) for row in rows]

    async def get_all_online(self) -> List[Robot]:
        """Get all online robots (based on heartbeat timeout)."""
        cutoff = datetime.now(timezone.utc) - self._heartbeat_timeout
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(self.SQL_GET_ALL_ONLINE, cutoff)
            return [self._row_to_robot(row) for row in rows]

    async def get_by_environment(self, environment: str) -> List[Robot]:
        """Get robots in specific environment."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(self.SQL_GET_BY_ENVIRONMENT, environment)
            return [self._row_to_robot(row) for row in rows]

    async def get_by_tenant(self, tenant_id: str) -> List[Robot]:
        """Get robots belonging to a tenant."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(self.SQL_GET_BY_TENANT, tenant_id)
            return [self._row_to_robot(row) for row in rows]

    async def get_available_robots(
        self,
        required_capabilities: Optional[List[str]] = None,
        tenant_id: Optional[str] = None,
    ) -> List[Robot]:
        """Get robots with available capacity matching capabilities.

        Args:
            required_capabilities: List of required capability strings
            tenant_id: Optional tenant filter

        Returns:
            List of available robots sorted by current job count (least busy first)
        """
        online_robots = await self.get_all_online()

        available = []
        for robot in online_robots:
            # Check tenant
            if tenant_id is not None and getattr(robot, "tenant_id", None) != tenant_id:
                continue

            # Check capacity
            if not robot.is_available:
                continue

            # Check capabilities
            if required_capabilities:
                robot_caps = {cap.value for cap in robot.capabilities}
                if not all(cap in robot_caps for cap in required_capabilities):
                    continue

            available.append(robot)

        # Sort by least busy (fewest current jobs)
        available.sort(key=lambda r: r.current_jobs)
        return available

    async def save(self, robot: Robot) -> None:
        """Save or update robot (UPSERT)."""
        now = datetime.now(timezone.utc)

        # Prepare JSON fields
        capabilities_json = orjson.dumps([cap.value for cap in robot.capabilities]).decode()
        current_jobs_json = orjson.dumps(robot.current_job_ids).decode()
        tags_json = orjson.dumps(robot.tags).decode()
        metrics_json = orjson.dumps(robot.metrics).decode()

        async with self._pool.acquire() as conn:
            await conn.execute(
                self.SQL_UPSERT_ROBOT,
                robot.id,
                robot.name,
                getattr(robot, "hostname", ""),
                robot.status.value,
                robot.environment,
                capabilities_json,
                robot.max_concurrent_jobs,
                current_jobs_json,
                tags_json,
                metrics_json,
                getattr(robot, "tenant_id", None),
                robot.last_heartbeat or now,
                robot.last_seen or now,
                robot.created_at or now,
            )

        logger.debug(f"Saved robot {robot.id} to database")

    async def delete(self, robot_id: str) -> None:
        """Delete robot by ID."""
        async with self._pool.acquire() as conn:
            await conn.execute(self.SQL_DELETE, robot_id)
        logger.debug(f"Deleted robot {robot_id} from database")

    async def update_status(self, robot_id: str, status: RobotStatus) -> None:
        """Update robot status."""
        now = datetime.now(timezone.utc)
        async with self._pool.acquire() as conn:
            await conn.execute(self.SQL_UPDATE_STATUS, robot_id, status.value, now)
        logger.debug(f"Updated robot {robot_id} status to {status.value}")

    async def update_heartbeat(
        self,
        robot_id: str,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update robot heartbeat timestamp and metrics.

        Args:
            robot_id: Robot identifier
            metrics: Optional system metrics (cpu_percent, memory_mb, etc.)
        """
        now = datetime.now(timezone.utc)
        metrics_json = orjson.dumps(metrics or {}).decode()

        async with self._pool.acquire() as conn:
            await conn.execute(self.SQL_UPDATE_HEARTBEAT, robot_id, now, metrics_json)

    async def update_current_jobs(
        self,
        robot_id: str,
        current_job_ids: List[str],
    ) -> None:
        """Update robot's current job IDs.

        Args:
            robot_id: Robot identifier
            current_job_ids: List of currently assigned job IDs
        """
        now = datetime.now(timezone.utc)
        jobs_json = orjson.dumps(current_job_ids).decode()

        async with self._pool.acquire() as conn:
            await conn.execute(self.SQL_UPDATE_CURRENT_JOBS, robot_id, jobs_json, now)

    async def add_job_to_robot(self, robot_id: str, job_id: str) -> None:
        """Add a job to robot's current jobs.

        Args:
            robot_id: Robot identifier
            job_id: Job ID to add
        """
        robot = await self.get_by_id(robot_id)
        if robot:
            current = list(robot.current_job_ids)
            if job_id not in current:
                current.append(job_id)
                await self.update_current_jobs(robot_id, current)

    async def remove_job_from_robot(self, robot_id: str, job_id: str) -> None:
        """Remove a job from robot's current jobs.

        Args:
            robot_id: Robot identifier
            job_id: Job ID to remove
        """
        robot = await self.get_by_id(robot_id)
        if robot:
            current = [j for j in robot.current_job_ids if j != job_id]
            await self.update_current_jobs(robot_id, current)

    async def mark_offline(self, robot_id: str) -> List[str]:
        """Mark robot as offline and return orphaned job IDs.

        Args:
            robot_id: Robot identifier

        Returns:
            List of job IDs that were assigned to this robot
        """
        robot = await self.get_by_id(robot_id)
        orphaned_jobs: List[str] = []

        if robot:
            orphaned_jobs = list(robot.current_job_ids)
            await self.update_status(robot_id, RobotStatus.OFFLINE)
            await self.update_current_jobs(robot_id, [])
            logger.info(f"Marked robot {robot_id} offline with {len(orphaned_jobs)} orphaned jobs")

        return orphaned_jobs

    def _row_to_robot(self, row: Any) -> Robot:
        """Convert database row to Robot domain entity.

        Args:
            row: asyncpg Record

        Returns:
            Robot domain entity
        """
        # Parse JSON fields
        capabilities_raw = row["capabilities"]
        if isinstance(capabilities_raw, str):
            capabilities_raw = orjson.loads(capabilities_raw)

        current_jobs_raw = row["current_job_ids"]
        if isinstance(current_jobs_raw, str):
            current_jobs_raw = orjson.loads(current_jobs_raw)

        tags_raw = row["tags"]
        if isinstance(tags_raw, str):
            tags_raw = orjson.loads(tags_raw)

        metrics_raw = row["metrics"]
        if isinstance(metrics_raw, str):
            metrics_raw = orjson.loads(metrics_raw)

        # Convert capability strings to enums
        capabilities: Set[RobotCapability] = set()
        for cap in capabilities_raw or []:
            try:
                capabilities.add(RobotCapability(cap))
            except ValueError:
                logger.debug(f"Skipping unknown capability: {cap}")

        # Parse status
        status = RobotStatus(row["status"]) if row["status"] else RobotStatus.OFFLINE

        return Robot(
            id=row["robot_id"],
            name=row["name"],
            status=status,
            environment=row["environment"] or "default",
            max_concurrent_jobs=row["max_concurrent_jobs"] or 1,
            last_seen=row["last_seen"],
            last_heartbeat=row["last_heartbeat"],
            created_at=row["created_at"],
            tags=tags_raw or [],
            metrics=metrics_raw or {},
            capabilities=capabilities,
            current_job_ids=current_jobs_raw or [],
        )


# SQL for creating the robots table (for reference/migrations)
CREATE_ROBOTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS robots (
    robot_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    hostname VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'offline',
    environment VARCHAR(100) DEFAULT 'default',
    capabilities JSONB DEFAULT '[]',
    max_concurrent_jobs INTEGER DEFAULT 1,
    current_job_ids JSONB DEFAULT '[]',
    tags JSONB DEFAULT '[]',
    metrics JSONB DEFAULT '{}',
    tenant_id VARCHAR(255),
    registered_at TIMESTAMPTZ,
    last_heartbeat TIMESTAMPTZ,
    last_seen TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Indexes for common queries
    CONSTRAINT robots_status_check CHECK (status IN ('offline', 'online', 'busy', 'error', 'maintenance'))
);

CREATE INDEX IF NOT EXISTS idx_robots_status ON robots(status);
CREATE INDEX IF NOT EXISTS idx_robots_environment ON robots(environment);
CREATE INDEX IF NOT EXISTS idx_robots_tenant_id ON robots(tenant_id);
CREATE INDEX IF NOT EXISTS idx_robots_last_heartbeat ON robots(last_heartbeat);
CREATE INDEX IF NOT EXISTS idx_robots_registered_at ON robots(registered_at);
"""


__all__ = [
    "PgRobotRepository",
    "CREATE_ROBOTS_TABLE_SQL",
]
