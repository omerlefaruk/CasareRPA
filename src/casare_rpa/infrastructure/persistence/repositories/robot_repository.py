"""
RobotRepository - PostgreSQL persistence for Robot entities.

Provides CRUD operations for robot registration, status tracking,
and capability-based queries using asyncpg connection pooling.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Set

import orjson
from loguru import logger

from casare_rpa.domain.orchestrator.entities.robot import (
    Robot,
    RobotCapability,
    RobotStatus,
)
from casare_rpa.utils.pooling.database_pool import DatabasePoolManager


class RobotRepository:
    """
    Repository for Robot entity persistence.

    Uses asyncpg with connection pooling for efficient database operations.
    Maps between Robot domain entity and PostgreSQL robots table.
    """

    def __init__(self, pool_manager: Optional[DatabasePoolManager] = None) -> None:
        """
        Initialize repository with optional pool manager.

        Args:
            pool_manager: Database pool manager. If None, will fetch from singleton.
        """
        self._pool_manager = pool_manager
        self._pool_name = "casare_rpa"

    async def _get_pool(self):
        """Get database connection pool."""
        if self._pool_manager is None:
            from casare_rpa.utils.pooling.database_pool import get_pool_manager

            self._pool_manager = await get_pool_manager()
        return await self._pool_manager.get_pool(self._pool_name, db_type="postgresql")

    async def _get_connection(self):
        """Acquire a connection from the pool."""
        pool = await self._get_pool()
        return await pool.acquire()

    async def _release_connection(self, conn) -> None:
        """Release connection back to pool."""
        pool = await self._get_pool()
        await pool.release(conn)

    def _row_to_robot(self, row: Dict[str, Any]) -> Robot:
        """
        Convert database row to Robot domain entity.

        Args:
            row: asyncpg Record or dict from database query.

        Returns:
            Robot domain entity.
        """
        # Parse capabilities from JSONB array
        raw_capabilities = row.get("capabilities", [])
        if isinstance(raw_capabilities, str):
            raw_capabilities = orjson.loads(raw_capabilities)
        capabilities: Set[RobotCapability] = set()
        for cap in raw_capabilities:
            try:
                capabilities.add(RobotCapability(cap))
            except ValueError:
                logger.warning(f"Unknown robot capability: {cap}")

        # Parse current_job_ids from JSONB array
        current_job_ids = row.get("current_job_ids", [])
        if isinstance(current_job_ids, str):
            current_job_ids = orjson.loads(current_job_ids)

        # Parse assigned_workflows from JSONB array
        assigned_workflows = row.get("assigned_workflows", [])
        if isinstance(assigned_workflows, str):
            assigned_workflows = orjson.loads(assigned_workflows)

        # Parse tags from JSONB array
        tags = row.get("tags", [])
        if isinstance(tags, str):
            tags = orjson.loads(tags)

        # Parse metrics from JSONB object
        metrics = row.get("metrics", {})
        if isinstance(metrics, str):
            metrics = orjson.loads(metrics)

        # Parse status enum
        status_str = row.get("status", "offline")
        try:
            status = RobotStatus(status_str)
        except ValueError:
            logger.warning(f"Unknown robot status: {status_str}, defaulting to offline")
            status = RobotStatus.OFFLINE

        return Robot(
            id=str(row["robot_id"]),
            name=row["name"],
            status=status,
            environment=row.get("environment", "default"),
            max_concurrent_jobs=row.get("max_concurrent_jobs", 1),
            last_seen=row.get("last_seen"),
            last_heartbeat=row.get("last_heartbeat"),
            created_at=row.get("created_at"),
            tags=tags,
            metrics=metrics,
            capabilities=capabilities,
            assigned_workflows=assigned_workflows,
            current_job_ids=current_job_ids,
        )

    def _robot_to_params(self, robot: Robot) -> Dict[str, Any]:
        """
        Convert Robot entity to database parameters.

        Args:
            robot: Robot domain entity.

        Returns:
            Dictionary of database column values.
        """
        return {
            "robot_id": robot.id,
            "name": robot.name,
            "hostname": robot.name,  # Use name as hostname if not separate field
            "status": robot.status.value,
            "environment": robot.environment,
            "max_concurrent_jobs": robot.max_concurrent_jobs,
            "last_seen": robot.last_seen,
            "last_heartbeat": robot.last_heartbeat,
            "created_at": robot.created_at or datetime.utcnow(),
            "capabilities": orjson.dumps(
                [cap.value for cap in robot.capabilities]
            ).decode(),
            "tags": orjson.dumps(robot.tags).decode(),
            "metrics": orjson.dumps(robot.metrics).decode(),
            "assigned_workflows": orjson.dumps(robot.assigned_workflows).decode(),
            "current_job_ids": orjson.dumps(robot.current_job_ids).decode(),
        }

    async def save(self, robot: Robot) -> Robot:
        """
        Save or update a robot.

        Uses upsert (INSERT ON CONFLICT UPDATE) for idempotent saves.

        Args:
            robot: Robot entity to save.

        Returns:
            Saved robot entity with any server-generated fields.
        """
        conn = await self._get_connection()
        try:
            params = self._robot_to_params(robot)
            await conn.execute(
                """
                INSERT INTO robots (
                    robot_id, name, hostname, status, environment,
                    max_concurrent_jobs, last_seen, last_heartbeat, created_at,
                    capabilities, tags, metrics, assigned_workflows, current_job_ids
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10::jsonb, $11::jsonb,
                    $12::jsonb, $13::jsonb, $14::jsonb
                )
                ON CONFLICT (robot_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    hostname = EXCLUDED.hostname,
                    status = EXCLUDED.status,
                    environment = EXCLUDED.environment,
                    max_concurrent_jobs = EXCLUDED.max_concurrent_jobs,
                    last_seen = EXCLUDED.last_seen,
                    last_heartbeat = EXCLUDED.last_heartbeat,
                    capabilities = EXCLUDED.capabilities,
                    tags = EXCLUDED.tags,
                    metrics = EXCLUDED.metrics,
                    assigned_workflows = EXCLUDED.assigned_workflows,
                    current_job_ids = EXCLUDED.current_job_ids,
                    updated_at = NOW()
                """,
                params["robot_id"],
                params["name"],
                params["hostname"],
                params["status"],
                params["environment"],
                params["max_concurrent_jobs"],
                params["last_seen"],
                params["last_heartbeat"],
                params["created_at"],
                params["capabilities"],
                params["tags"],
                params["metrics"],
                params["assigned_workflows"],
                params["current_job_ids"],
            )
            logger.debug(f"Saved robot: {robot.id}")
            return robot
        except Exception as e:
            logger.error(f"Failed to save robot {robot.id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def get_by_id(self, robot_id: str) -> Optional[Robot]:
        """
        Get robot by ID.

        Args:
            robot_id: UUID of the robot.

        Returns:
            Robot entity or None if not found.
        """
        conn = await self._get_connection()
        try:
            row = await conn.fetchrow(
                "SELECT * FROM robots WHERE robot_id = $1", robot_id
            )
            if row is None:
                return None
            return self._row_to_robot(dict(row))
        except Exception as e:
            logger.error(f"Failed to get robot {robot_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def get_by_hostname(self, hostname: str) -> Optional[Robot]:
        """
        Get robot by hostname.

        Args:
            hostname: Unique hostname of the robot.

        Returns:
            Robot entity or None if not found.
        """
        conn = await self._get_connection()
        try:
            row = await conn.fetchrow(
                "SELECT * FROM robots WHERE hostname = $1", hostname
            )
            if row is None:
                return None
            return self._row_to_robot(dict(row))
        except Exception as e:
            logger.error(f"Failed to get robot by hostname {hostname}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def get_all(self) -> List[Robot]:
        """
        Get all registered robots.

        Returns:
            List of all Robot entities.
        """
        conn = await self._get_connection()
        try:
            rows = await conn.fetch("SELECT * FROM robots ORDER BY name")
            return [self._row_to_robot(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get all robots: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def get_by_status(self, status: RobotStatus) -> List[Robot]:
        """
        Get robots by status.

        Args:
            status: Robot status to filter by.

        Returns:
            List of robots with matching status.
        """
        conn = await self._get_connection()
        try:
            rows = await conn.fetch(
                "SELECT * FROM robots WHERE status = $1 ORDER BY name",
                status.value,
            )
            return [self._row_to_robot(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get robots by status {status}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def get_available(self) -> List[Robot]:
        """
        Get available robots (online with capacity).

        Returns robots that are online and have room for more jobs.

        Returns:
            List of available Robot entities.
        """
        conn = await self._get_connection()
        try:
            rows = await conn.fetch(
                """
                SELECT * FROM robots
                WHERE status = 'online'
                AND jsonb_array_length(current_job_ids) < max_concurrent_jobs
                ORDER BY jsonb_array_length(current_job_ids) ASC, name
                """
            )
            return [self._row_to_robot(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get available robots: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def get_by_capability(self, capability: RobotCapability) -> List[Robot]:
        """
        Get robots with a specific capability.

        Args:
            capability: Required capability.

        Returns:
            List of robots with the capability.
        """
        conn = await self._get_connection()
        try:
            rows = await conn.fetch(
                """
                SELECT * FROM robots
                WHERE capabilities @> $1::jsonb
                ORDER BY name
                """,
                orjson.dumps([capability.value]).decode(),
            )
            return [self._row_to_robot(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get robots by capability {capability}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def get_by_capabilities(
        self, capabilities: Set[RobotCapability]
    ) -> List[Robot]:
        """
        Get robots with all specified capabilities.

        Args:
            capabilities: Set of required capabilities.

        Returns:
            List of robots with all capabilities.
        """
        if not capabilities:
            return await self.get_all()

        conn = await self._get_connection()
        try:
            caps_json = orjson.dumps([cap.value for cap in capabilities]).decode()
            rows = await conn.fetch(
                """
                SELECT * FROM robots
                WHERE capabilities @> $1::jsonb
                ORDER BY name
                """,
                caps_json,
            )
            return [self._row_to_robot(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get robots by capabilities: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def update_heartbeat(self, robot_id: str) -> None:
        """
        Update robot heartbeat timestamp.

        Also updates last_seen and sets status to online if offline.

        Args:
            robot_id: UUID of the robot.
        """
        conn = await self._get_connection()
        try:
            now = datetime.utcnow()
            await conn.execute(
                """
                UPDATE robots
                SET last_heartbeat = $2,
                    last_seen = $2,
                    status = CASE
                        WHEN status = 'offline' THEN 'online'
                        ELSE status
                    END,
                    updated_at = NOW()
                WHERE robot_id = $1
                """,
                robot_id,
                now,
            )
            logger.debug(f"Updated heartbeat for robot {robot_id}")
        except Exception as e:
            logger.error(f"Failed to update heartbeat for robot {robot_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def update_status(self, robot_id: str, status: RobotStatus) -> None:
        """
        Update robot status.

        Args:
            robot_id: UUID of the robot.
            status: New status.
        """
        conn = await self._get_connection()
        try:
            await conn.execute(
                """
                UPDATE robots
                SET status = $2, updated_at = NOW()
                WHERE robot_id = $1
                """,
                robot_id,
                status.value,
            )
            logger.debug(f"Updated status for robot {robot_id} to {status.value}")
        except Exception as e:
            logger.error(f"Failed to update status for robot {robot_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def update_metrics(self, robot_id: str, metrics: Dict[str, Any]) -> None:
        """
        Update robot metrics.

        Args:
            robot_id: UUID of the robot.
            metrics: New metrics dictionary.
        """
        conn = await self._get_connection()
        try:
            await conn.execute(
                """
                UPDATE robots
                SET metrics = $2::jsonb, updated_at = NOW()
                WHERE robot_id = $1
                """,
                robot_id,
                orjson.dumps(metrics).decode(),
            )
            logger.debug(f"Updated metrics for robot {robot_id}")
        except Exception as e:
            logger.error(f"Failed to update metrics for robot {robot_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def add_current_job(self, robot_id: str, job_id: str) -> None:
        """
        Add a job to robot's current jobs list.

        Args:
            robot_id: UUID of the robot.
            job_id: UUID of the job to add.
        """
        conn = await self._get_connection()
        try:
            await conn.execute(
                """
                UPDATE robots
                SET current_job_ids = current_job_ids || $2::jsonb,
                    status = CASE
                        WHEN jsonb_array_length(current_job_ids || $2::jsonb) >= max_concurrent_jobs
                        THEN 'busy'
                        ELSE status
                    END,
                    updated_at = NOW()
                WHERE robot_id = $1
                AND NOT current_job_ids @> $2::jsonb
                """,
                robot_id,
                orjson.dumps([job_id]).decode(),
            )
            logger.debug(f"Added job {job_id} to robot {robot_id}")
        except Exception as e:
            logger.error(f"Failed to add job {job_id} to robot {robot_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def remove_current_job(self, robot_id: str, job_id: str) -> None:
        """
        Remove a job from robot's current jobs list.

        Args:
            robot_id: UUID of the robot.
            job_id: UUID of the job to remove.
        """
        conn = await self._get_connection()
        try:
            await conn.execute(
                """
                UPDATE robots
                SET current_job_ids = (
                    SELECT jsonb_agg(elem)
                    FROM jsonb_array_elements_text(current_job_ids) elem
                    WHERE elem != $2
                ),
                status = CASE
                    WHEN status = 'busy' THEN 'online'
                    ELSE status
                END,
                updated_at = NOW()
                WHERE robot_id = $1
                """,
                robot_id,
                job_id,
            )
            logger.debug(f"Removed job {job_id} from robot {robot_id}")
        except Exception as e:
            logger.error(f"Failed to remove job {job_id} from robot {robot_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def delete(self, robot_id: str) -> bool:
        """
        Delete a robot.

        Args:
            robot_id: UUID of the robot to delete.

        Returns:
            True if deleted, False if not found.
        """
        conn = await self._get_connection()
        try:
            result = await conn.execute(
                "DELETE FROM robots WHERE robot_id = $1", robot_id
            )
            deleted = result.split()[-1] != "0"
            if deleted:
                logger.info(f"Deleted robot: {robot_id}")
            return deleted
        except Exception as e:
            logger.error(f"Failed to delete robot {robot_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def mark_stale_robots_offline(self, timeout_seconds: int = 60) -> int:
        """
        Mark robots as offline if heartbeat is stale.

        Args:
            timeout_seconds: Seconds since last heartbeat to consider stale.

        Returns:
            Number of robots marked offline.
        """
        conn = await self._get_connection()
        try:
            result = await conn.execute(
                """
                UPDATE robots
                SET status = 'offline', updated_at = NOW()
                WHERE status IN ('online', 'busy')
                AND last_heartbeat < NOW() - $1 * INTERVAL '1 second'
                """,
                timeout_seconds,
            )
            count = int(result.split()[-1])
            if count > 0:
                logger.info(f"Marked {count} stale robots as offline")
            return count
        except Exception as e:
            logger.error(f"Failed to mark stale robots offline: {e}")
            raise
        finally:
            await self._release_connection(conn)


__all__ = ["RobotRepository"]
