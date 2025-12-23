"""
TenantRepository - PostgreSQL persistence for Tenant entities.

Provides CRUD operations for tenant management in multi-tenant deployments
using asyncpg connection pooling.
"""

from datetime import UTC, datetime
from typing import Any

import orjson
from loguru import logger

from casare_rpa.domain.entities.tenant import Tenant, TenantId, TenantSettings
from casare_rpa.utils.pooling.database_pool import DatabasePoolManager


class TenantRepository:
    """
    Repository for Tenant entity persistence.

    Uses asyncpg with connection pooling for efficient database operations.
    Maps between Tenant domain entity and PostgreSQL tenants table.
    """

    def __init__(self, pool_manager: DatabasePoolManager | None = None) -> None:
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

    def _row_to_tenant(self, row: dict[str, Any]) -> Tenant:
        """
        Convert database row to Tenant domain entity.

        Args:
            row: asyncpg Record or dict from database query.

        Returns:
            Tenant domain entity.
        """
        # Parse settings from JSONB
        settings_data = row.get("settings", {})
        if isinstance(settings_data, str):
            settings_data = orjson.loads(settings_data)
        settings = TenantSettings.from_dict(settings_data)

        # Parse admin_emails from JSONB array
        admin_emails = row.get("admin_emails", [])
        if isinstance(admin_emails, str):
            admin_emails = orjson.loads(admin_emails)

        # Parse robot_ids from JSONB array
        robot_ids = row.get("robot_ids", [])
        if isinstance(robot_ids, str):
            robot_ids = orjson.loads(robot_ids)
        robot_ids = set(robot_ids)

        return Tenant(
            id=TenantId(str(row["tenant_id"])),
            name=row["name"],
            description=row.get("description", ""),
            settings=settings,
            admin_emails=admin_emails,
            contact_email=row.get("contact_email"),
            robot_ids=robot_ids,
            is_active=row.get("is_active", True),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    def _tenant_to_params(self, tenant: Tenant) -> dict[str, Any]:
        """
        Convert Tenant entity to database parameters.

        Args:
            tenant: Tenant domain entity.

        Returns:
            Dictionary of database column values.
        """
        now = datetime.now(UTC)
        return {
            "tenant_id": str(tenant.id),
            "name": tenant.name,
            "description": tenant.description,
            "settings": orjson.dumps(tenant.settings.to_dict()).decode(),
            "admin_emails": orjson.dumps(tenant.admin_emails).decode(),
            "contact_email": tenant.contact_email,
            "robot_ids": orjson.dumps(list(tenant.robot_ids)).decode(),
            "is_active": tenant.is_active,
            "created_at": tenant.created_at or now,
            "updated_at": now,
        }

    async def save(self, tenant: Tenant) -> Tenant:
        """
        Save a tenant (insert or update).

        Args:
            tenant: Tenant to save.

        Returns:
            Saved Tenant with updated timestamps.
        """
        params = self._tenant_to_params(tenant)
        conn = await self._get_connection()

        try:
            await conn.execute(
                """
                INSERT INTO tenants (
                    tenant_id, name, description, settings, admin_emails,
                    contact_email, robot_ids, is_active, created_at, updated_at
                ) VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, $6, $7::jsonb, $8, $9, $10)
                ON CONFLICT (tenant_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    settings = EXCLUDED.settings,
                    admin_emails = EXCLUDED.admin_emails,
                    contact_email = EXCLUDED.contact_email,
                    robot_ids = EXCLUDED.robot_ids,
                    is_active = EXCLUDED.is_active,
                    updated_at = EXCLUDED.updated_at
                """,
                params["tenant_id"],
                params["name"],
                params["description"],
                params["settings"],
                params["admin_emails"],
                params["contact_email"],
                params["robot_ids"],
                params["is_active"],
                params["created_at"],
                params["updated_at"],
            )
            logger.debug(f"Saved tenant: {tenant.id}")
            return tenant
        except Exception as e:
            logger.error(f"Failed to save tenant {tenant.id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def get_by_id(self, tenant_id: str) -> Tenant | None:
        """
        Get tenant by ID.

        Args:
            tenant_id: Tenant UUID.

        Returns:
            Tenant if found, None otherwise.
        """
        conn = await self._get_connection()
        try:
            row = await conn.fetchrow(
                "SELECT * FROM tenants WHERE tenant_id = $1",
                tenant_id,
            )
            if row is None:
                return None
            return self._row_to_tenant(dict(row))
        except Exception as e:
            logger.error(f"Failed to get tenant {tenant_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def get_by_name(self, name: str) -> Tenant | None:
        """
        Get tenant by name.

        Args:
            name: Tenant name.

        Returns:
            Tenant if found, None otherwise.
        """
        conn = await self._get_connection()
        try:
            row = await conn.fetchrow(
                "SELECT * FROM tenants WHERE name = $1",
                name,
            )
            if row is None:
                return None
            return self._row_to_tenant(dict(row))
        except Exception as e:
            logger.error(f"Failed to get tenant by name {name}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def get_all(
        self,
        include_inactive: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Tenant]:
        """
        Get all tenants.

        Args:
            include_inactive: Include inactive tenants.
            limit: Maximum results.
            offset: Pagination offset.

        Returns:
            List of tenants.
        """
        conn = await self._get_connection()
        try:
            if include_inactive:
                rows = await conn.fetch(
                    """
                    SELECT * FROM tenants
                    ORDER BY name ASC
                    LIMIT $1 OFFSET $2
                    """,
                    limit,
                    offset,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT * FROM tenants
                    WHERE is_active = TRUE
                    ORDER BY name ASC
                    LIMIT $1 OFFSET $2
                    """,
                    limit,
                    offset,
                )
            return [self._row_to_tenant(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get all tenants: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def get_by_admin_email(self, email: str) -> list[Tenant]:
        """
        Get all tenants where user is an admin.

        Args:
            email: Admin email address.

        Returns:
            List of tenants where user is admin.
        """
        conn = await self._get_connection()
        try:
            rows = await conn.fetch(
                """
                SELECT * FROM tenants
                WHERE admin_emails @> $1::jsonb
                AND is_active = TRUE
                ORDER BY name ASC
                """,
                orjson.dumps([email.lower()]).decode(),
            )
            return [self._row_to_tenant(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get tenants for admin {email}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def get_by_robot_id(self, robot_id: str) -> Tenant | None:
        """
        Get tenant that owns a specific robot.

        Args:
            robot_id: Robot ID.

        Returns:
            Tenant if found, None otherwise.
        """
        conn = await self._get_connection()
        try:
            row = await conn.fetchrow(
                """
                SELECT * FROM tenants
                WHERE robot_ids @> $1::jsonb
                AND is_active = TRUE
                """,
                orjson.dumps([robot_id]).decode(),
            )
            if row is None:
                return None
            return self._row_to_tenant(dict(row))
        except Exception as e:
            logger.error(f"Failed to get tenant for robot {robot_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def add_robot_to_tenant(self, tenant_id: str, robot_id: str) -> bool:
        """
        Add a robot to a tenant.

        Args:
            tenant_id: Tenant UUID.
            robot_id: Robot ID to add.

        Returns:
            True if successful.
        """
        conn = await self._get_connection()
        try:
            result = await conn.execute(
                """
                UPDATE tenants
                SET robot_ids = robot_ids || $1::jsonb,
                    updated_at = NOW()
                WHERE tenant_id = $2
                AND NOT robot_ids @> $1::jsonb
                """,
                orjson.dumps([robot_id]).decode(),
                tenant_id,
            )
            success = "UPDATE 1" in result
            if success:
                logger.debug(f"Added robot {robot_id} to tenant {tenant_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to add robot {robot_id} to tenant {tenant_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def remove_robot_from_tenant(self, tenant_id: str, robot_id: str) -> bool:
        """
        Remove a robot from a tenant.

        Args:
            tenant_id: Tenant UUID.
            robot_id: Robot ID to remove.

        Returns:
            True if successful.
        """
        conn = await self._get_connection()
        try:
            result = await conn.execute(
                """
                UPDATE tenants
                SET robot_ids = robot_ids - $1,
                    updated_at = NOW()
                WHERE tenant_id = $2
                """,
                robot_id,
                tenant_id,
            )
            success = "UPDATE 1" in result
            if success:
                logger.debug(f"Removed robot {robot_id} from tenant {tenant_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to remove robot {robot_id} from tenant {tenant_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def delete(self, tenant_id: str, hard_delete: bool = False) -> bool:
        """
        Delete a tenant.

        Args:
            tenant_id: Tenant UUID to delete.
            hard_delete: If True, permanently delete. If False, soft delete.

        Returns:
            True if tenant was deleted.
        """
        conn = await self._get_connection()
        try:
            if hard_delete:
                result = await conn.execute(
                    "DELETE FROM tenants WHERE tenant_id = $1",
                    tenant_id,
                )
                success = "DELETE 1" in result
            else:
                result = await conn.execute(
                    """
                    UPDATE tenants
                    SET is_active = FALSE, updated_at = NOW()
                    WHERE tenant_id = $1
                    """,
                    tenant_id,
                )
                success = "UPDATE 1" in result

            if success:
                action = "deleted" if hard_delete else "deactivated"
                logger.info(f"Tenant {tenant_id} {action}")
            return success
        except Exception as e:
            logger.error(f"Failed to delete tenant {tenant_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def count(self, include_inactive: bool = False) -> int:
        """
        Count total tenants.

        Args:
            include_inactive: Include inactive tenants.

        Returns:
            Total tenant count.
        """
        conn = await self._get_connection()
        try:
            if include_inactive:
                row = await conn.fetchrow("SELECT COUNT(*) as count FROM tenants")
            else:
                row = await conn.fetchrow(
                    "SELECT COUNT(*) as count FROM tenants WHERE is_active = TRUE"
                )
            return row["count"] if row else 0
        except Exception as e:
            logger.error(f"Failed to count tenants: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def get_statistics(self) -> dict[str, Any]:
        """
        Get tenant statistics.

        Returns:
            Statistics dictionary with counts and aggregations.
        """
        conn = await self._get_connection()
        try:
            row = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) as total_tenants,
                    COUNT(*) FILTER (WHERE is_active = TRUE) as active_tenants,
                    COUNT(*) FILTER (WHERE is_active = FALSE) as inactive_tenants,
                    COALESCE(SUM(jsonb_array_length(robot_ids)), 0) as total_robots,
                    COALESCE(AVG(jsonb_array_length(robot_ids)), 0) as avg_robots_per_tenant
                FROM tenants
                """
            )
            return {
                "total_tenants": row["total_tenants"],
                "active_tenants": row["active_tenants"],
                "inactive_tenants": row["inactive_tenants"],
                "total_robots": row["total_robots"],
                "avg_robots_per_tenant": round(row["avg_robots_per_tenant"], 2),
            }
        except Exception as e:
            logger.error(f"Failed to get tenant statistics: {e}")
            raise
        finally:
            await self._release_connection(conn)


__all__ = ["TenantRepository"]
