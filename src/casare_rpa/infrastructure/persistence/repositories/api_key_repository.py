"""
ApiKeyRepository - PostgreSQL persistence for Robot API Keys.

Provides CRUD operations for robot API key management using asyncpg.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from loguru import logger

from casare_rpa.infrastructure.auth.robot_api_keys import RobotApiKey
from casare_rpa.utils.pooling.database_pool import DatabasePoolManager


class ApiKeyRepository:
    """
    Repository for Robot API Key persistence.

    Uses asyncpg with connection pooling for efficient database operations.
    Maps between RobotApiKey domain model and PostgreSQL robot_api_keys table.
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

    def _row_to_api_key(self, row: Dict[str, Any]) -> RobotApiKey:
        """
        Convert database row to RobotApiKey.

        Args:
            row: asyncpg Record or dict from database query.

        Returns:
            RobotApiKey instance.
        """
        return RobotApiKey(
            id=str(row["id"]),
            robot_id=str(row["robot_id"]),
            api_key_hash=row["api_key_hash"],
            name=row.get("name"),
            description=row.get("description"),
            created_at=row.get("created_at"),
            expires_at=row.get("expires_at"),
            last_used_at=row.get("last_used_at"),
            last_used_ip=str(row["last_used_ip"]) if row.get("last_used_ip") else None,
            is_revoked=row.get("is_revoked", False),
            revoked_at=row.get("revoked_at"),
            revoked_by=row.get("revoked_by"),
            revoke_reason=row.get("revoke_reason"),
            created_by=row.get("created_by"),
        )

    async def save(
        self,
        robot_id: str,
        api_key_hash: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
    ) -> RobotApiKey:
        """
        Save a new API key.

        Args:
            robot_id: UUID of the robot.
            api_key_hash: SHA-256 hash of the API key.
            name: Optional friendly name.
            description: Optional description.
            expires_at: Optional expiration datetime.
            created_by: User who created the key.

        Returns:
            Created RobotApiKey.
        """
        conn = await self._get_connection()
        try:
            row = await conn.fetchrow(
                """
                INSERT INTO robot_api_keys (
                    robot_id, api_key_hash, name, description, expires_at, created_by
                ) VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING *
                """,
                robot_id,
                api_key_hash,
                name,
                description,
                expires_at,
                created_by,
            )
            api_key = self._row_to_api_key(dict(row))
            logger.debug(f"Saved API key: {api_key.id} for robot {robot_id}")
            return api_key
        except Exception as e:
            logger.error(f"Failed to save API key for robot {robot_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def get_by_id(self, key_id: str) -> Optional[RobotApiKey]:
        """
        Get API key by ID.

        Args:
            key_id: UUID of the API key.

        Returns:
            RobotApiKey or None if not found.
        """
        conn = await self._get_connection()
        try:
            row = await conn.fetchrow(
                "SELECT * FROM robot_api_keys WHERE id = $1",
                key_id,
            )
            if row is None:
                return None
            return self._row_to_api_key(dict(row))
        except Exception as e:
            logger.error(f"Failed to get API key {key_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def get_by_hash(self, api_key_hash: str) -> Optional[RobotApiKey]:
        """
        Get API key by hash.

        Args:
            api_key_hash: SHA-256 hash of the API key.

        Returns:
            RobotApiKey or None if not found.
        """
        conn = await self._get_connection()
        try:
            row = await conn.fetchrow(
                "SELECT * FROM robot_api_keys WHERE api_key_hash = $1",
                api_key_hash,
            )
            if row is None:
                return None
            return self._row_to_api_key(dict(row))
        except Exception as e:
            logger.error(f"Failed to get API key by hash: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def get_valid_by_hash(self, api_key_hash: str) -> Optional[RobotApiKey]:
        """
        Get API key by hash if valid (not revoked, not expired).

        Args:
            api_key_hash: SHA-256 hash of the API key.

        Returns:
            RobotApiKey or None if not found or invalid.
        """
        conn = await self._get_connection()
        try:
            row = await conn.fetchrow(
                """
                SELECT * FROM robot_api_keys
                WHERE api_key_hash = $1
                AND is_revoked = FALSE
                AND (expires_at IS NULL OR expires_at > NOW())
                """,
                api_key_hash,
            )
            if row is None:
                return None
            return self._row_to_api_key(dict(row))
        except Exception as e:
            logger.error(f"Failed to get valid API key by hash: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def list_for_robot(
        self,
        robot_id: str,
        include_revoked: bool = False,
    ) -> List[RobotApiKey]:
        """
        List all API keys for a robot.

        Args:
            robot_id: UUID of the robot.
            include_revoked: Whether to include revoked keys.

        Returns:
            List of RobotApiKey.
        """
        conn = await self._get_connection()
        try:
            if include_revoked:
                rows = await conn.fetch(
                    """
                    SELECT * FROM robot_api_keys
                    WHERE robot_id = $1
                    ORDER BY created_at DESC
                    """,
                    robot_id,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT * FROM robot_api_keys
                    WHERE robot_id = $1 AND is_revoked = FALSE
                    ORDER BY created_at DESC
                    """,
                    robot_id,
                )
            return [self._row_to_api_key(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Failed to list API keys for robot {robot_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def list_all(
        self,
        include_revoked: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> List[RobotApiKey]:
        """
        List all API keys.

        Args:
            include_revoked: Whether to include revoked keys.
            limit: Max number of results.
            offset: Result offset.

        Returns:
            List of RobotApiKey.
        """
        conn = await self._get_connection()
        try:
            if include_revoked:
                rows = await conn.fetch(
                    """
                    SELECT * FROM robot_api_keys
                    ORDER BY created_at DESC
                    LIMIT $1 OFFSET $2
                    """,
                    limit,
                    offset,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT * FROM robot_api_keys
                    WHERE is_revoked = FALSE
                    ORDER BY created_at DESC
                    LIMIT $1 OFFSET $2
                    """,
                    limit,
                    offset,
                )
            return [self._row_to_api_key(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Failed to list API keys: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def update_last_used(
        self,
        api_key_hash: str,
        client_ip: Optional[str] = None,
    ) -> None:
        """
        Update last_used_at timestamp for a key.

        Args:
            api_key_hash: SHA-256 hash of the API key.
            client_ip: Client IP address.
        """
        conn = await self._get_connection()
        try:
            await conn.execute(
                """
                UPDATE robot_api_keys
                SET last_used_at = NOW(),
                    last_used_ip = COALESCE($2::inet, last_used_ip)
                WHERE api_key_hash = $1
                """,
                api_key_hash,
                client_ip,
            )
            logger.debug(f"Updated last_used for API key hash: {api_key_hash[:16]}...")
        except Exception as e:
            logger.error(f"Failed to update last_used for API key: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def revoke(
        self,
        key_id: str,
        revoked_by: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> bool:
        """
        Revoke an API key.

        Args:
            key_id: UUID of the API key.
            revoked_by: User who revoked the key.
            reason: Reason for revocation.

        Returns:
            True if key was revoked, False if not found.
        """
        conn = await self._get_connection()
        try:
            result = await conn.execute(
                """
                UPDATE robot_api_keys
                SET is_revoked = TRUE,
                    revoked_at = NOW(),
                    revoked_by = $2,
                    revoke_reason = $3
                WHERE id = $1 AND is_revoked = FALSE
                """,
                key_id,
                revoked_by,
                reason,
            )
            revoked = "UPDATE 1" in result
            if revoked:
                logger.info(f"Revoked API key: {key_id}")
            return revoked
        except Exception as e:
            logger.error(f"Failed to revoke API key {key_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def revoke_all_for_robot(
        self,
        robot_id: str,
        revoked_by: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> int:
        """
        Revoke all API keys for a robot.

        Args:
            robot_id: UUID of the robot.
            revoked_by: User who revoked the keys.
            reason: Reason for revocation.

        Returns:
            Number of keys revoked.
        """
        conn = await self._get_connection()
        try:
            result = await conn.execute(
                """
                UPDATE robot_api_keys
                SET is_revoked = TRUE,
                    revoked_at = NOW(),
                    revoked_by = $2,
                    revoke_reason = $3
                WHERE robot_id = $1 AND is_revoked = FALSE
                """,
                robot_id,
                revoked_by,
                reason,
            )
            count = int(result.split()[-1])
            if count > 0:
                logger.info(f"Revoked {count} API keys for robot {robot_id}")
            return count
        except Exception as e:
            logger.error(f"Failed to revoke API keys for robot {robot_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def delete(self, key_id: str) -> bool:
        """
        Delete an API key (hard delete).

        Args:
            key_id: UUID of the API key.

        Returns:
            True if deleted, False if not found.
        """
        conn = await self._get_connection()
        try:
            result = await conn.execute(
                "DELETE FROM robot_api_keys WHERE id = $1",
                key_id,
            )
            deleted = "DELETE 1" in result
            if deleted:
                logger.info(f"Deleted API key: {key_id}")
            return deleted
        except Exception as e:
            logger.error(f"Failed to delete API key {key_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def delete_expired(self, days_old: int = 30) -> int:
        """
        Delete expired keys older than N days.

        Args:
            days_old: Number of days since expiration.

        Returns:
            Number of keys deleted.
        """
        conn = await self._get_connection()
        try:
            result = await conn.execute(
                """
                DELETE FROM robot_api_keys
                WHERE expires_at IS NOT NULL
                AND expires_at < NOW() - $1 * INTERVAL '1 day'
                """,
                days_old,
            )
            count = int(result.split()[-1])
            if count > 0:
                logger.info(
                    f"Deleted {count} expired API keys older than {days_old} days"
                )
            return count
        except Exception as e:
            logger.error(f"Failed to delete expired API keys: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def count_for_robot(self, robot_id: str, active_only: bool = True) -> int:
        """
        Count API keys for a robot.

        Args:
            robot_id: UUID of the robot.
            active_only: Count only active (non-revoked) keys.

        Returns:
            Number of keys.
        """
        conn = await self._get_connection()
        try:
            if active_only:
                result = await conn.fetchval(
                    """
                    SELECT COUNT(*) FROM robot_api_keys
                    WHERE robot_id = $1 AND is_revoked = FALSE
                    """,
                    robot_id,
                )
            else:
                result = await conn.fetchval(
                    "SELECT COUNT(*) FROM robot_api_keys WHERE robot_id = $1",
                    robot_id,
                )
            return int(result)
        except Exception as e:
            logger.error(f"Failed to count API keys for robot {robot_id}: {e}")
            raise
        finally:
            await self._release_connection(conn)

    async def get_robot_id_by_hash(self, api_key_hash: str) -> Optional[str]:
        """
        Get robot ID associated with an API key hash.

        This is an optimized query for authentication that only fetches
        the robot_id if the key is valid.

        Args:
            api_key_hash: SHA-256 hash of the API key.

        Returns:
            Robot ID or None if key invalid.
        """
        conn = await self._get_connection()
        try:
            result = await conn.fetchval(
                """
                SELECT robot_id FROM robot_api_keys
                WHERE api_key_hash = $1
                AND is_revoked = FALSE
                AND (expires_at IS NULL OR expires_at > NOW())
                """,
                api_key_hash,
            )
            return str(result) if result else None
        except Exception as e:
            logger.error(f"Failed to get robot ID by API key hash: {e}")
            raise
        finally:
            await self._release_connection(conn)


__all__ = ["ApiKeyRepository"]
