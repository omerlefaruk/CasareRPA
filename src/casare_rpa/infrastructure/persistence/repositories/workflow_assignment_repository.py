"""
WorkflowAssignmentRepository - PostgreSQL persistence for RobotAssignment value objects.

Provides CRUD operations for workflow-to-robot default assignments
using asyncpg connection pooling.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger

from casare_rpa.domain.orchestrator.value_objects.robot_assignment import (
    RobotAssignment,
)
from casare_rpa.utils.pooling.database_pool import DatabasePoolManager


class WorkflowAssignmentRepository:
    """
    Repository for RobotAssignment value object persistence.

    Uses asyncpg with connection pooling for efficient database operations.
    Maps between RobotAssignment value object and workflow_robot_assignments table.
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

    def _row_to_assignment(self, row: Dict[str, Any]) -> RobotAssignment:
        """
        Convert database row to RobotAssignment value object.

        Args:
            row: asyncpg Record or dict from database query.

        Returns:
            RobotAssignment value object.
        """
        created_at = row.get("created_at")
        if created_at is None:
            created_at = datetime.utcnow()

        return RobotAssignment(
            workflow_id=str(row["workflow_id"]),
            robot_id=str(row["robot_id"]),
            is_default=row.get("is_default", True),
            priority=row.get("priority", 0),
            created_at=created_at,
            created_by=row.get("created_by", "") or "",
            notes=row.get("notes"),
        )

    def _assignment_to_params(self, assignment: RobotAssignment) -> Dict[str, Any]:
        """
        Convert RobotAssignment to database parameters.

        Args:
            assignment: RobotAssignment value object.

        Returns:
            Dictionary of database column values.
        """
        return {
            "workflow_id": assignment.workflow_id,
            "robot_id": assignment.robot_id,
            "is_default": assignment.is_default,
            "priority": assignment.priority,
            "created_at": assignment.created_at or datetime.utcnow(),
            "created_by": assignment.created_by,
            "notes": assignment.notes,
        }

    async def save(self, assignment: RobotAssignment) -> RobotAssignment:
        """
        Save or update a workflow assignment.

        Uses upsert (INSERT ON CONFLICT UPDATE) for idempotent saves.
        If setting is_default=True, unsets other defaults for the workflow.

        Args:
            assignment: RobotAssignment to save.

        Returns:
            Saved assignment.
        """
        conn = await self._get_connection()
        try:
            params = self._assignment_to_params(assignment)

            # If this is the default, unset other defaults first
            if assignment.is_default:
                await conn.execute(
                    """
                    UPDATE workflow_robot_assignments
                    SET is_default = FALSE, updated_at = NOW()
                    WHERE workflow_id = $1 AND robot_id != $2
                    """,
                    params["workflow_id"],
                    params["robot_id"],
                )

            await conn.execute(
                """
                INSERT INTO workflow_robot_assignments (
                    workflow_id, robot_id, is_default, priority,
                    created_at, created_by, notes
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (workflow_id, robot_id) DO UPDATE SET
                    is_default = EXCLUDED.is_default,
                    priority = EXCLUDED.priority,
                    notes = EXCLUDED.notes,
                    updated_at = NOW()
                """,
                params["workflow_id"],
                params["robot_id"],
                params["is_default"],
                params["priority"],
                params["created_at"],
                params["created_by"],
                params["notes"],
            )
            logger.debug(
                f"Saved assignment: workflow={assignment.workflow_id}, "
                f"robot={assignment.robot_id}"
            )
            return assignment
        except Exception as e:
            logger.error(
                f"Failed to save assignment for workflow {assignment.workflow_id}: {e}"
            )
            raise
        finally:
            await self._release_connection(conn)

    async def get_by_workflow(self, workflow_id: str) -> List[RobotAssignment]:
        """
        Get all assignments for a workflow.

        Args:
            workflow_id: UUID of the workflow.

        Returns:
            List of RobotAssignment value objects.
        """
        conn = await self._get_connection()
        try:
            rows = await conn.fetch(
                """
                SELECT * FROM workflow_robot_assignments
                WHERE workflow_id = $1
                ORDER BY is_default DESC, priority DESC
                """,
                workflow_id,
            )
            return [self._row_to_assignment(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get assignments for workflow {workflow_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def get_default_for_workflow(
        self, workflow_id: str
    ) -> Optional[RobotAssignment]:
        """
        Get the default assignment for a workflow.

        Args:
            workflow_id: UUID of the workflow.

        Returns:
            Default RobotAssignment or None if not set.
        """
        conn = await self._get_connection()
        try:
            row = await conn.fetchrow(
                """
                SELECT * FROM workflow_robot_assignments
                WHERE workflow_id = $1 AND is_default = TRUE
                LIMIT 1
                """,
                workflow_id,
            )
            if row is None:
                return None
            return self._row_to_assignment(dict(row))
        except Exception as e:
            logger.error(
                f"Failed to get default assignment for workflow {workflow_id}: {e}"
            )
            raise
        finally:
            await self._release_connection(conn)

    async def get_by_robot(self, robot_id: str) -> List[RobotAssignment]:
        """
        Get all workflow assignments for a robot.

        Args:
            robot_id: UUID of the robot.

        Returns:
            List of RobotAssignment value objects.
        """
        conn = await self._get_connection()
        try:
            rows = await conn.fetch(
                """
                SELECT * FROM workflow_robot_assignments
                WHERE robot_id = $1
                ORDER BY workflow_id
                """,
                robot_id,
            )
            return [self._row_to_assignment(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get assignments for robot {robot_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def get_assignment(
        self, workflow_id: str, robot_id: str
    ) -> Optional[RobotAssignment]:
        """
        Get a specific workflow-robot assignment.

        Args:
            workflow_id: UUID of the workflow.
            robot_id: UUID of the robot.

        Returns:
            RobotAssignment or None if not found.
        """
        conn = await self._get_connection()
        try:
            row = await conn.fetchrow(
                """
                SELECT * FROM workflow_robot_assignments
                WHERE workflow_id = $1 AND robot_id = $2
                """,
                workflow_id,
                robot_id,
            )
            if row is None:
                return None
            return self._row_to_assignment(dict(row))
        except Exception as e:
            logger.error(
                f"Failed to get assignment for workflow={workflow_id}, robot={robot_id}: {e}"
            )
            raise
        finally:
            await self._release_connection(conn)

    async def set_default(self, workflow_id: str, robot_id: str) -> None:
        """
        Set a specific robot as the default for a workflow.

        Args:
            workflow_id: UUID of the workflow.
            robot_id: UUID of the robot to set as default.
        """
        conn = await self._get_connection()
        try:
            async with conn.transaction():
                # Unset all defaults for this workflow
                await conn.execute(
                    """
                    UPDATE workflow_robot_assignments
                    SET is_default = FALSE, updated_at = NOW()
                    WHERE workflow_id = $1
                    """,
                    workflow_id,
                )
                # Set the new default
                await conn.execute(
                    """
                    UPDATE workflow_robot_assignments
                    SET is_default = TRUE, updated_at = NOW()
                    WHERE workflow_id = $1 AND robot_id = $2
                    """,
                    workflow_id,
                    robot_id,
                )
            logger.debug(
                f"Set default assignment: workflow={workflow_id}, robot={robot_id}"
            )
        except Exception as e:
            logger.error(
                f"Failed to set default for workflow={workflow_id}, robot={robot_id}: {e}"
            )
            raise
        finally:
            await self._release_connection(conn)

    async def delete(self, workflow_id: str, robot_id: str) -> bool:
        """
        Delete a workflow-robot assignment.

        Args:
            workflow_id: UUID of the workflow.
            robot_id: UUID of the robot.

        Returns:
            True if deleted, False if not found.
        """
        conn = await self._get_connection()
        try:
            result = await conn.execute(
                """
                DELETE FROM workflow_robot_assignments
                WHERE workflow_id = $1 AND robot_id = $2
                """,
                workflow_id,
                robot_id,
            )
            deleted = result.split()[-1] != "0"
            if deleted:
                logger.info(
                    f"Deleted assignment: workflow={workflow_id}, robot={robot_id}"
                )
            return deleted
        except Exception as e:
            logger.error(
                f"Failed to delete assignment workflow={workflow_id}, robot={robot_id}: {e}"
            )
            raise
        finally:
            await self._release_connection(conn)

    async def delete_all_for_workflow(self, workflow_id: str) -> int:
        """
        Delete all assignments for a workflow.

        Args:
            workflow_id: UUID of the workflow.

        Returns:
            Number of assignments deleted.
        """
        conn = await self._get_connection()
        try:
            result = await conn.execute(
                """
                DELETE FROM workflow_robot_assignments
                WHERE workflow_id = $1
                """,
                workflow_id,
            )
            count = int(result.split()[-1])
            if count > 0:
                logger.info(f"Deleted {count} assignments for workflow {workflow_id}")
            return count
        except Exception as e:
            logger.error(
                f"Failed to delete assignments for workflow {workflow_id}: {e}"
            )
            raise
        finally:
            await self._release_connection(conn)

    async def delete_all_for_robot(self, robot_id: str) -> int:
        """
        Delete all assignments for a robot.

        Useful when decommissioning a robot.

        Args:
            robot_id: UUID of the robot.

        Returns:
            Number of assignments deleted.
        """
        conn = await self._get_connection()
        try:
            result = await conn.execute(
                """
                DELETE FROM workflow_robot_assignments
                WHERE robot_id = $1
                """,
                robot_id,
            )
            count = int(result.split()[-1])
            if count > 0:
                logger.info(f"Deleted {count} assignments for robot {robot_id}")
            return count
        except Exception as e:
            logger.error(f"Failed to delete assignments for robot {robot_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def get_workflows_for_robot(self, robot_id: str) -> List[str]:
        """
        Get workflow IDs assigned to a robot.

        Args:
            robot_id: UUID of the robot.

        Returns:
            List of workflow IDs.
        """
        conn = await self._get_connection()
        try:
            rows = await conn.fetch(
                """
                SELECT workflow_id FROM workflow_robot_assignments
                WHERE robot_id = $1
                ORDER BY workflow_id
                """,
                robot_id,
            )
            return [str(row["workflow_id"]) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get workflows for robot {robot_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)


__all__ = ["WorkflowAssignmentRepository"]
