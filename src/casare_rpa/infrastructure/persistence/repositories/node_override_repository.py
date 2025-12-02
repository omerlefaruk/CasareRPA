"""
NodeOverrideRepository - PostgreSQL persistence for NodeRobotOverride value objects.

Provides CRUD operations for node-level robot routing overrides
using asyncpg connection pooling.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Set

import orjson
from loguru import logger

from casare_rpa.domain.orchestrator.entities.robot import RobotCapability
from casare_rpa.domain.orchestrator.value_objects.node_robot_override import (
    NodeRobotOverride,
)
from casare_rpa.utils.pooling.database_pool import DatabasePoolManager


class NodeOverrideRepository:
    """
    Repository for NodeRobotOverride value object persistence.

    Uses asyncpg with connection pooling for efficient database operations.
    Maps between NodeRobotOverride value object and node_robot_overrides table.
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

    def _row_to_override(self, row: Dict[str, Any]) -> NodeRobotOverride:
        """
        Convert database row to NodeRobotOverride value object.

        Args:
            row: asyncpg Record or dict from database query.

        Returns:
            NodeRobotOverride value object.
        """
        # Parse required_capabilities from JSONB array
        raw_capabilities = row.get("required_capabilities", [])
        if isinstance(raw_capabilities, str):
            raw_capabilities = (
                orjson.loads(raw_capabilities) if raw_capabilities else []
            )
        capabilities: Set[RobotCapability] = set()
        for cap in raw_capabilities:
            try:
                capabilities.add(RobotCapability(cap))
            except ValueError:
                logger.warning(f"Unknown robot capability in override: {cap}")

        created_at = row.get("created_at")
        if created_at is None:
            created_at = datetime.utcnow()

        robot_id = row.get("robot_id")
        if robot_id is not None:
            robot_id = str(robot_id)

        return NodeRobotOverride(
            workflow_id=str(row["workflow_id"]),
            node_id=row["node_id"],
            robot_id=robot_id,
            required_capabilities=frozenset(capabilities),
            reason=row.get("reason"),
            created_at=created_at,
            created_by=row.get("created_by", "") or "",
            is_active=row.get("is_active", True),
        )

    def _override_to_params(self, override: NodeRobotOverride) -> Dict[str, Any]:
        """
        Convert NodeRobotOverride to database parameters.

        Args:
            override: NodeRobotOverride value object.

        Returns:
            Dictionary of database column values.
        """
        # Convert frozenset of capabilities to JSON array
        capabilities_list = [cap.value for cap in override.required_capabilities]

        return {
            "workflow_id": override.workflow_id,
            "node_id": override.node_id,
            "robot_id": override.robot_id,
            "required_capabilities": orjson.dumps(capabilities_list).decode(),
            "reason": override.reason,
            "created_at": override.created_at or datetime.utcnow(),
            "created_by": override.created_by,
            "is_active": override.is_active,
        }

    async def save(self, override: NodeRobotOverride) -> NodeRobotOverride:
        """
        Save or update a node override.

        Uses upsert (INSERT ON CONFLICT UPDATE) for idempotent saves.

        Args:
            override: NodeRobotOverride to save.

        Returns:
            Saved override.
        """
        conn = await self._get_connection()
        try:
            params = self._override_to_params(override)
            await conn.execute(
                """
                INSERT INTO node_robot_overrides (
                    workflow_id, node_id, robot_id, required_capabilities,
                    reason, created_at, created_by, is_active
                ) VALUES ($1, $2, $3, $4::jsonb, $5, $6, $7, $8)
                ON CONFLICT (workflow_id, node_id) DO UPDATE SET
                    robot_id = EXCLUDED.robot_id,
                    required_capabilities = EXCLUDED.required_capabilities,
                    reason = EXCLUDED.reason,
                    is_active = EXCLUDED.is_active,
                    updated_at = NOW()
                """,
                params["workflow_id"],
                params["node_id"],
                params["robot_id"],
                params["required_capabilities"],
                params["reason"],
                params["created_at"],
                params["created_by"],
                params["is_active"],
            )
            logger.debug(
                f"Saved override: workflow={override.workflow_id}, "
                f"node={override.node_id}"
            )
            return override
        except Exception as e:
            logger.error(
                f"Failed to save override for workflow={override.workflow_id}, "
                f"node={override.node_id}: {e}"
            )
            raise
        finally:
            await self._release_connection(conn)

    async def get_by_workflow(self, workflow_id: str) -> List[NodeRobotOverride]:
        """
        Get all overrides for a workflow.

        Args:
            workflow_id: UUID of the workflow.

        Returns:
            List of NodeRobotOverride value objects.
        """
        conn = await self._get_connection()
        try:
            rows = await conn.fetch(
                """
                SELECT * FROM node_robot_overrides
                WHERE workflow_id = $1
                ORDER BY node_id
                """,
                workflow_id,
            )
            return [self._row_to_override(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get overrides for workflow {workflow_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def get_by_node(
        self, workflow_id: str, node_id: str
    ) -> Optional[NodeRobotOverride]:
        """
        Get override for a specific node.

        Args:
            workflow_id: UUID of the workflow.
            node_id: ID of the node.

        Returns:
            NodeRobotOverride or None if not found.
        """
        conn = await self._get_connection()
        try:
            row = await conn.fetchrow(
                """
                SELECT * FROM node_robot_overrides
                WHERE workflow_id = $1 AND node_id = $2
                """,
                workflow_id,
                node_id,
            )
            if row is None:
                return None
            return self._row_to_override(dict(row))
        except Exception as e:
            logger.error(
                f"Failed to get override for workflow={workflow_id}, node={node_id}: {e}"
            )
            raise
        finally:
            await self._release_connection(conn)

    async def get_active_for_workflow(
        self, workflow_id: str
    ) -> List[NodeRobotOverride]:
        """
        Get active overrides for a workflow.

        Args:
            workflow_id: UUID of the workflow.

        Returns:
            List of active NodeRobotOverride value objects.
        """
        conn = await self._get_connection()
        try:
            rows = await conn.fetch(
                """
                SELECT * FROM node_robot_overrides
                WHERE workflow_id = $1 AND is_active = TRUE
                ORDER BY node_id
                """,
                workflow_id,
            )
            return [self._row_to_override(dict(row)) for row in rows]
        except Exception as e:
            logger.error(
                f"Failed to get active overrides for workflow {workflow_id}: {e}"
            )
            raise
        finally:
            await self._release_connection(conn)

    async def get_by_robot(self, robot_id: str) -> List[NodeRobotOverride]:
        """
        Get all overrides targeting a specific robot.

        Args:
            robot_id: UUID of the robot.

        Returns:
            List of NodeRobotOverride value objects.
        """
        conn = await self._get_connection()
        try:
            rows = await conn.fetch(
                """
                SELECT * FROM node_robot_overrides
                WHERE robot_id = $1
                ORDER BY workflow_id, node_id
                """,
                robot_id,
            )
            return [self._row_to_override(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get overrides for robot {robot_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def get_by_capability(
        self, capability: RobotCapability
    ) -> List[NodeRobotOverride]:
        """
        Get all overrides requiring a specific capability.

        Args:
            capability: Required capability.

        Returns:
            List of NodeRobotOverride value objects.
        """
        conn = await self._get_connection()
        try:
            rows = await conn.fetch(
                """
                SELECT * FROM node_robot_overrides
                WHERE required_capabilities @> $1::jsonb
                ORDER BY workflow_id, node_id
                """,
                orjson.dumps([capability.value]).decode(),
            )
            return [self._row_to_override(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get overrides by capability {capability}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def delete(self, workflow_id: str, node_id: str) -> bool:
        """
        Delete a node override.

        Args:
            workflow_id: UUID of the workflow.
            node_id: ID of the node.

        Returns:
            True if deleted, False if not found.
        """
        conn = await self._get_connection()
        try:
            result = await conn.execute(
                """
                DELETE FROM node_robot_overrides
                WHERE workflow_id = $1 AND node_id = $2
                """,
                workflow_id,
                node_id,
            )
            deleted = result.split()[-1] != "0"
            if deleted:
                logger.info(f"Deleted override: workflow={workflow_id}, node={node_id}")
            return deleted
        except Exception as e:
            logger.error(
                f"Failed to delete override workflow={workflow_id}, node={node_id}: {e}"
            )
            raise
        finally:
            await self._release_connection(conn)

    async def deactivate(self, workflow_id: str, node_id: str) -> bool:
        """
        Deactivate a node override (soft delete).

        Args:
            workflow_id: UUID of the workflow.
            node_id: ID of the node.

        Returns:
            True if deactivated, False if not found.
        """
        conn = await self._get_connection()
        try:
            result = await conn.execute(
                """
                UPDATE node_robot_overrides
                SET is_active = FALSE, updated_at = NOW()
                WHERE workflow_id = $1 AND node_id = $2
                """,
                workflow_id,
                node_id,
            )
            updated = result.split()[-1] != "0"
            if updated:
                logger.debug(
                    f"Deactivated override: workflow={workflow_id}, node={node_id}"
                )
            return updated
        except Exception as e:
            logger.error(
                f"Failed to deactivate override workflow={workflow_id}, node={node_id}: {e}"
            )
            raise
        finally:
            await self._release_connection(conn)

    async def activate(self, workflow_id: str, node_id: str) -> bool:
        """
        Activate a node override.

        Args:
            workflow_id: UUID of the workflow.
            node_id: ID of the node.

        Returns:
            True if activated, False if not found.
        """
        conn = await self._get_connection()
        try:
            result = await conn.execute(
                """
                UPDATE node_robot_overrides
                SET is_active = TRUE, updated_at = NOW()
                WHERE workflow_id = $1 AND node_id = $2
                """,
                workflow_id,
                node_id,
            )
            updated = result.split()[-1] != "0"
            if updated:
                logger.debug(
                    f"Activated override: workflow={workflow_id}, node={node_id}"
                )
            return updated
        except Exception as e:
            logger.error(
                f"Failed to activate override workflow={workflow_id}, node={node_id}: {e}"
            )
            raise
        finally:
            await self._release_connection(conn)

    async def delete_all_for_workflow(self, workflow_id: str) -> int:
        """
        Delete all overrides for a workflow.

        Args:
            workflow_id: UUID of the workflow.

        Returns:
            Number of overrides deleted.
        """
        conn = await self._get_connection()
        try:
            result = await conn.execute(
                """
                DELETE FROM node_robot_overrides
                WHERE workflow_id = $1
                """,
                workflow_id,
            )
            count = int(result.split()[-1])
            if count > 0:
                logger.info(f"Deleted {count} overrides for workflow {workflow_id}")
            return count
        except Exception as e:
            logger.error(f"Failed to delete overrides for workflow {workflow_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def delete_all_for_robot(self, robot_id: str) -> int:
        """
        Delete all overrides targeting a specific robot.

        Useful when decommissioning a robot.

        Args:
            robot_id: UUID of the robot.

        Returns:
            Number of overrides deleted.
        """
        conn = await self._get_connection()
        try:
            result = await conn.execute(
                """
                DELETE FROM node_robot_overrides
                WHERE robot_id = $1
                """,
                robot_id,
            )
            count = int(result.split()[-1])
            if count > 0:
                logger.info(f"Deleted {count} overrides for robot {robot_id}")
            return count
        except Exception as e:
            logger.error(f"Failed to delete overrides for robot {robot_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def get_override_map(self, workflow_id: str) -> Dict[str, NodeRobotOverride]:
        """
        Get a map of node_id to override for a workflow.

        Useful for quick lookup during workflow execution.

        Args:
            workflow_id: UUID of the workflow.

        Returns:
            Dictionary mapping node_id to NodeRobotOverride.
        """
        overrides = await self.get_active_for_workflow(workflow_id)
        return {override.node_id: override for override in overrides}


__all__ = ["NodeOverrideRepository"]
