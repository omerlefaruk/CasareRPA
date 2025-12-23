"""
UserRepository - PostgreSQL persistence for User authentication.

Provides user lookup and credential validation for production authentication.
Uses asyncpg with connection pooling and bcrypt for secure password hashing.
"""

from datetime import UTC, datetime
from typing import Any

from loguru import logger

try:
    import bcrypt

    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False
    logger.debug("bcrypt not available. Password hashing disabled.")


class UserRepository:
    """
    Repository for user authentication and management.

    Uses asyncpg with connection pooling for efficient database operations.
    Supports both the users table (RBAC migration 016) and tenant_members for roles.
    """

    def __init__(self, pool=None) -> None:
        """
        Initialize repository with optional connection pool.

        Args:
            pool: asyncpg connection pool. If None, will use pool manager.
        """
        self._pool = pool
        self._pool_manager = None

    async def _get_pool(self):
        """Get database connection pool."""
        if self._pool is not None:
            return self._pool

        if self._pool_manager is None:
            from casare_rpa.utils.pooling.database_pool import get_pool_manager

            self._pool_manager = await get_pool_manager()
        return await self._pool_manager.get_pool("casare_rpa", db_type="postgresql")

    async def _get_connection(self):
        """Acquire a connection from the pool."""
        pool = await self._get_pool()
        return await pool.acquire()

    async def _release_connection(self, conn) -> None:
        """Release connection back to pool."""
        pool = await self._get_pool()
        await pool.release(conn)

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password: Plain text password.

        Returns:
            Bcrypt hash string.
        """
        if not BCRYPT_AVAILABLE:
            raise RuntimeError("bcrypt not installed. Run: pip install bcrypt")
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            password: Plain text password to verify.
            password_hash: Bcrypt hash to check against.

        Returns:
            True if password matches hash.
        """
        if not BCRYPT_AVAILABLE:
            raise RuntimeError("bcrypt not installed. Run: pip install bcrypt")
        try:
            return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
        except Exception as e:
            logger.warning(f"Password verification failed: {e}")
            return False

    async def validate_credentials(self, username: str, password: str) -> dict[str, Any] | None:
        """
        Validate user credentials and return user info if valid.

        Checks both username and email fields for matching user,
        then verifies password against stored hash.

        Args:
            username: Username or email address.
            password: Plain text password.

        Returns:
            Dict with user_id, roles, tenant_id if valid, None otherwise.
        """
        conn = await self._get_connection()
        try:
            # Look up user by username or email
            row = await conn.fetchrow(
                """
                SELECT
                    u.id,
                    u.email,
                    u.username,
                    u.password_hash,
                    u.status,
                    u.failed_login_count,
                    u.locked_until,
                    u.mfa_enabled
                FROM users u
                WHERE (u.username = $1 OR u.email = $1)
                  AND u.status = 'active'
                """,
                username,
            )

            if not row:
                logger.debug(f"User not found: {username}")
                return None

            # Check if account is locked
            if row["locked_until"] and row["locked_until"] > datetime.now(UTC):
                logger.warning(f"Account locked: {username}")
                return None

            # Verify password
            if not row["password_hash"]:
                logger.warning(f"No password set for user: {username}")
                return None

            if not self.verify_password(password, row["password_hash"]):
                # Record failed attempt
                await self._record_failed_login(conn, row["id"])
                logger.debug(f"Invalid password for user: {username}")
                return None

            # Get user roles and tenant membership
            user_id = str(row["id"])
            roles_data = await self._get_user_roles(conn, user_id)

            # Clear failed login count on successful login
            await self._record_successful_login(conn, row["id"])

            return {
                "user_id": user_id,
                "email": row["email"],
                "username": row["username"],
                "roles": roles_data["roles"],
                "tenant_id": roles_data["tenant_id"],
                "mfa_enabled": row["mfa_enabled"],
            }

        except Exception as e:
            logger.error(f"Credential validation failed: {e}")
            return None
        finally:
            await self._release_connection(conn)

    async def _get_user_roles(self, conn, user_id: str) -> dict[str, Any]:
        """
        Get user roles and primary tenant from tenant_members table.

        Args:
            conn: Database connection.
            user_id: User UUID.

        Returns:
            Dict with roles list and tenant_id.
        """
        # Get tenant memberships with role info
        rows = await conn.fetch(
            """
            SELECT
                tm.tenant_id,
                r.name as role_name
            FROM tenant_members tm
            JOIN roles r ON r.id = tm.role_id
            WHERE tm.user_id = $1::uuid
              AND tm.status = 'active'
            ORDER BY r.priority DESC
            """,
            user_id,
        )

        if not rows:
            # User has no tenant memberships, return default role
            return {"roles": ["viewer"], "tenant_id": None}

        # Collect unique roles from all memberships
        roles = list(set(row["role_name"] for row in rows))

        # Use first (highest priority) tenant as primary
        tenant_id = str(rows[0]["tenant_id"]) if rows else None

        return {"roles": roles, "tenant_id": tenant_id}

    async def _record_failed_login(self, conn, user_id) -> None:
        """Record failed login attempt and potentially lock account."""
        await conn.execute(
            """
            UPDATE users
            SET failed_login_count = failed_login_count + 1,
                locked_until = CASE
                    WHEN failed_login_count >= 4 THEN NOW() + INTERVAL '15 minutes'
                    ELSE locked_until
                END
            WHERE id = $1
            """,
            user_id,
        )

    async def _record_successful_login(self, conn, user_id) -> None:
        """Clear failed login count on successful authentication."""
        await conn.execute(
            """
            UPDATE users
            SET failed_login_count = 0,
                locked_until = NULL,
                last_login_at = NOW()
            WHERE id = $1
            """,
            user_id,
        )

    async def get_by_id(self, user_id: str) -> dict[str, Any] | None:
        """
        Get user by ID.

        Args:
            user_id: User UUID.

        Returns:
            User dict or None if not found.
        """
        conn = await self._get_connection()
        try:
            row = await conn.fetchrow(
                """
                SELECT
                    id, email, username, full_name, avatar_url,
                    status, email_verified, mfa_enabled,
                    timezone, locale, created_at, last_login_at
                FROM users
                WHERE id = $1::uuid
                """,
                user_id,
            )
            if not row:
                return None

            # Get roles
            roles_data = await self._get_user_roles(conn, user_id)

            return {
                "user_id": str(row["id"]),
                "email": row["email"],
                "username": row["username"],
                "full_name": row["full_name"],
                "avatar_url": row["avatar_url"],
                "status": row["status"],
                "email_verified": row["email_verified"],
                "mfa_enabled": row["mfa_enabled"],
                "timezone": row["timezone"],
                "locale": row["locale"],
                "created_at": row["created_at"],
                "last_login_at": row["last_login_at"],
                "roles": roles_data["roles"],
                "tenant_id": roles_data["tenant_id"],
            }
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            return None
        finally:
            await self._release_connection(conn)

    async def get_by_email(self, email: str) -> dict[str, Any] | None:
        """
        Get user by email address.

        Args:
            email: Email address.

        Returns:
            User dict or None if not found.
        """
        conn = await self._get_connection()
        try:
            row = await conn.fetchrow(
                "SELECT id FROM users WHERE email = $1",
                email.lower(),
            )
            if not row:
                return None
            return await self.get_by_id(str(row["id"]))
        except Exception as e:
            logger.error(f"Failed to get user by email {email}: {e}")
            return None
        finally:
            await self._release_connection(conn)

    async def create_user(
        self,
        email: str,
        password: str,
        username: str | None = None,
        full_name: str | None = None,
    ) -> str | None:
        """
        Create a new user.

        Args:
            email: Email address (required).
            password: Plain text password.
            username: Optional username.
            full_name: Optional display name.

        Returns:
            User ID if created, None on error.
        """
        conn = await self._get_connection()
        try:
            password_hash = self.hash_password(password)

            row = await conn.fetchrow(
                """
                INSERT INTO users (email, username, full_name, password_hash, status)
                VALUES ($1, $2, $3, $4, 'active')
                RETURNING id
                """,
                email.lower(),
                username,
                full_name,
                password_hash,
            )

            if row:
                logger.info(f"Created user: {email}")
                return str(row["id"])
            return None

        except Exception as e:
            logger.error(f"Failed to create user {email}: {e}")
            return None
        finally:
            await self._release_connection(conn)

    async def update_password(self, user_id: str, new_password: str) -> bool:
        """
        Update user password.

        Args:
            user_id: User UUID.
            new_password: New plain text password.

        Returns:
            True if updated successfully.
        """
        conn = await self._get_connection()
        try:
            password_hash = self.hash_password(new_password)
            result = await conn.execute(
                """
                UPDATE users
                SET password_hash = $1, updated_at = NOW()
                WHERE id = $2::uuid
                """,
                password_hash,
                user_id,
            )
            success = "UPDATE 1" in result
            if success:
                logger.info(f"Password updated for user: {user_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to update password for {user_id}: {e}")
            return False
        finally:
            await self._release_connection(conn)

    async def exists(self, email: str) -> bool:
        """
        Check if user with email exists.

        Args:
            email: Email address.

        Returns:
            True if user exists.
        """
        conn = await self._get_connection()
        try:
            result = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM users WHERE email = $1)",
                email.lower(),
            )
            return result
        except Exception as e:
            logger.error(f"Failed to check user exists {email}: {e}")
            return False
        finally:
            await self._release_connection(conn)


__all__ = ["UserRepository"]
