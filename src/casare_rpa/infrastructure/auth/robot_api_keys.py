"""
Robot API Key Service.

Manages secure API key authentication for robots connecting to the orchestrator.
API keys are SHA-256 hashed before storage - raw keys are shown once and never stored.

Key Format: crpa_<base64url_token> (44 chars total, easily identifiable)
"""

import hashlib
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from loguru import logger

# =============================================================================
# CONSTANTS
# =============================================================================

API_KEY_PREFIX = "crpa"
API_KEY_TOKEN_BYTES = 32  # 256 bits of entropy


# =============================================================================
# EXCEPTIONS
# =============================================================================


class RobotApiKeyError(Exception):
    """Base exception for robot API key operations."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(message)


class ApiKeyNotFoundError(RobotApiKeyError):
    """Raised when API key is not found."""

    def __init__(self, key_hint: str = "") -> None:
        hint = f" (prefix: {key_hint})" if key_hint else ""
        super().__init__(f"API key not found{hint}")


class ApiKeyRevokedError(RobotApiKeyError):
    """Raised when API key has been revoked."""

    def __init__(self, key_id: str) -> None:
        super().__init__(f"API key has been revoked: {key_id}")
        self.key_id = key_id


class ApiKeyExpiredError(RobotApiKeyError):
    """Raised when API key has expired."""

    def __init__(self, key_id: str, expired_at: datetime) -> None:
        super().__init__(f"API key expired at {expired_at}: {key_id}")
        self.key_id = key_id
        self.expired_at = expired_at


# =============================================================================
# ENUMS
# =============================================================================


class ApiKeyValidationResult(str, Enum):
    """Result of API key validation."""

    VALID = "valid"
    NOT_FOUND = "not_found"
    REVOKED = "revoked"
    EXPIRED = "expired"
    INVALID_FORMAT = "invalid_format"


# =============================================================================
# DATA MODELS
# =============================================================================


@dataclass
class RobotApiKey:
    """
    Represents a robot API key record.

    Note: The raw API key is never stored. Only the SHA-256 hash is persisted.
    """

    id: str
    robot_id: str
    api_key_hash: str
    name: str | None = None
    description: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None
    last_used_at: datetime | None = None
    last_used_ip: str | None = None
    is_revoked: bool = False
    revoked_at: datetime | None = None
    revoked_by: str | None = None
    revoke_reason: str | None = None
    created_by: str | None = None

    @property
    def is_expired(self) -> bool:
        """Check if key has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(UTC) > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if key is currently valid (not revoked, not expired)."""
        return not self.is_revoked and not self.is_expired

    @property
    def status(self) -> ApiKeyValidationResult:
        """Get current status of the key."""
        if self.is_revoked:
            return ApiKeyValidationResult.REVOKED
        if self.is_expired:
            return ApiKeyValidationResult.EXPIRED
        return ApiKeyValidationResult.VALID

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "robot_id": self.robot_id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "last_used_ip": self.last_used_ip,
            "is_revoked": self.is_revoked,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "revoked_by": self.revoked_by,
            "revoke_reason": self.revoke_reason,
            "created_by": self.created_by,
            "status": self.status.value,
        }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def generate_api_key_raw() -> str:
    """
    Generate a new raw API key.

    Format: crpa_<base64url_token>
    Example: crpa_dGhpcyBpcyBhIHRlc3QgYmFzZTY0IHRva2VuIQ

    Returns:
        Raw API key string (44 chars)
    """
    token = secrets.token_urlsafe(API_KEY_TOKEN_BYTES)
    return f"{API_KEY_PREFIX}_{token}"


def hash_api_key(raw_key: str) -> str:
    """
    Hash an API key using SHA-256.

    Args:
        raw_key: Raw API key string

    Returns:
        64-character hex digest
    """
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def validate_api_key_format(raw_key: str) -> bool:
    """
    Validate API key format.

    Args:
        raw_key: Raw API key string

    Returns:
        True if format is valid
    """
    if not raw_key:
        return False
    if not raw_key.startswith(f"{API_KEY_PREFIX}_"):
        return False
    # Expected length: "crpa_" (5) + base64url token (43) = 48
    if len(raw_key) < 40:
        return False
    return True


def extract_key_prefix(raw_key: str, length: int = 12) -> str:
    """
    Extract prefix from API key for logging/identification.

    Args:
        raw_key: Raw API key
        length: Number of characters to include

    Returns:
        Key prefix (e.g., "crpa_dGhpcy...")
    """
    if not raw_key:
        return ""
    return raw_key[:length]


# =============================================================================
# SERVICE
# =============================================================================


class RobotApiKeyService:
    """
    Service for managing robot API keys.

    Handles generation, validation, and revocation of API keys.
    Works with Supabase or any database client that supports the
    robot_api_keys table.
    """

    def __init__(self, db_client: Any) -> None:
        """
        Initialize the service.

        Args:
            db_client: Database client (Supabase client or connection pool)
        """
        self._client = db_client
        self._table_name = "robot_api_keys"

    async def generate_api_key(
        self,
        robot_id: str,
        name: str | None = None,
        description: str | None = None,
        expires_at: datetime | None = None,
        created_by: str | None = None,
    ) -> tuple[str, RobotApiKey]:
        """
        Generate a new API key for a robot.

        The raw key is returned ONCE and should be displayed to the user.
        It cannot be recovered after this call.

        Args:
            robot_id: UUID of the robot
            name: Optional friendly name for the key
            description: Optional description
            expires_at: Optional expiration datetime
            created_by: User who created the key

        Returns:
            Tuple of (raw_key, key_record)

        Raises:
            RobotApiKeyError: If key generation fails
        """
        raw_key = generate_api_key_raw()
        key_hash = hash_api_key(raw_key)

        try:
            # Insert into database
            result = await self._insert_key(
                robot_id=robot_id,
                api_key_hash=key_hash,
                name=name,
                description=description,
                expires_at=expires_at,
                created_by=created_by,
            )

            key_record = RobotApiKey(
                id=result["id"],
                robot_id=robot_id,
                api_key_hash=key_hash,
                name=name,
                description=description,
                expires_at=expires_at,
                created_by=created_by,
            )

            logger.info(
                f"Generated API key for robot {robot_id}: " f"id={key_record.id}, name={name}"
            )

            return raw_key, key_record

        except Exception as e:
            logger.error(f"Failed to generate API key for robot {robot_id}: {e}")
            raise RobotApiKeyError(
                f"Failed to generate API key: {e}",
                {"robot_id": robot_id},
            ) from e

    async def validate_api_key(
        self,
        raw_key: str,
        update_last_used: bool = True,
        client_ip: str | None = None,
    ) -> RobotApiKey | None:
        """
        Validate an API key and return the associated key record.

        Args:
            raw_key: Raw API key string
            update_last_used: Whether to update last_used_at timestamp
            client_ip: Client IP address for audit

        Returns:
            RobotApiKey if valid, None if invalid

        Raises:
            ApiKeyRevokedError: If key was revoked
            ApiKeyExpiredError: If key has expired
        """
        if not validate_api_key_format(raw_key):
            logger.warning(f"Invalid API key format: {extract_key_prefix(raw_key)}...")
            return None

        key_hash = hash_api_key(raw_key)

        try:
            key_record = await self._get_key_by_hash(key_hash)

            if key_record is None:
                logger.warning(f"API key not found: {extract_key_prefix(raw_key)}...")
                return None

            if key_record.is_revoked:
                logger.warning(f"Attempted use of revoked API key: {key_record.id}")
                raise ApiKeyRevokedError(key_record.id)

            if key_record.is_expired:
                logger.warning(f"Attempted use of expired API key: {key_record.id}")
                raise ApiKeyExpiredError(key_record.id, key_record.expires_at)

            if update_last_used:
                await self._update_last_used(key_hash, client_ip)

            logger.debug(f"Validated API key: id={key_record.id}, robot={key_record.robot_id}")
            return key_record

        except (ApiKeyRevokedError, ApiKeyExpiredError):
            raise
        except Exception as e:
            logger.error(f"Failed to validate API key: {e}")
            return None

    async def revoke_api_key(
        self,
        key_id: str,
        revoked_by: str | None = None,
        reason: str | None = None,
    ) -> bool:
        """
        Revoke an API key.

        Args:
            key_id: UUID of the API key to revoke
            revoked_by: User who revoked the key
            reason: Reason for revocation

        Returns:
            True if key was revoked, False if not found
        """
        try:
            success = await self._revoke_key(key_id, revoked_by, reason)

            if success:
                logger.info(f"Revoked API key {key_id}: by={revoked_by}, reason={reason}")
            else:
                logger.warning(f"API key not found for revocation: {key_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to revoke API key {key_id}: {e}")
            raise RobotApiKeyError(
                f"Failed to revoke API key: {e}",
                {"key_id": key_id},
            ) from e

    async def list_keys_for_robot(
        self,
        robot_id: str,
        include_revoked: bool = False,
    ) -> list[RobotApiKey]:
        """
        List all API keys for a robot.

        Args:
            robot_id: UUID of the robot
            include_revoked: Whether to include revoked keys

        Returns:
            List of RobotApiKey records
        """
        try:
            keys = await self._list_keys_for_robot(robot_id, include_revoked)
            logger.debug(f"Listed {len(keys)} API keys for robot {robot_id}")
            return keys

        except Exception as e:
            logger.error(f"Failed to list API keys for robot {robot_id}: {e}")
            raise RobotApiKeyError(
                f"Failed to list API keys: {e}",
                {"robot_id": robot_id},
            ) from e

    async def get_key_by_id(self, key_id: str) -> RobotApiKey | None:
        """
        Get an API key by its ID.

        Args:
            key_id: UUID of the API key

        Returns:
            RobotApiKey if found, None otherwise
        """
        try:
            return await self._get_key_by_id(key_id)
        except Exception as e:
            logger.error(f"Failed to get API key {key_id}: {e}")
            return None

    async def rotate_key(
        self,
        key_id: str,
        rotated_by: str | None = None,
    ) -> tuple[str, RobotApiKey]:
        """
        Rotate an API key (revoke old, create new).

        Args:
            key_id: UUID of the key to rotate
            rotated_by: User performing rotation

        Returns:
            Tuple of (new_raw_key, new_key_record)

        Raises:
            ApiKeyNotFoundError: If key doesn't exist
            RobotApiKeyError: If rotation fails
        """
        old_key = await self.get_key_by_id(key_id)
        if old_key is None:
            raise ApiKeyNotFoundError(key_id)

        # Revoke old key
        await self.revoke_api_key(
            key_id=key_id,
            revoked_by=rotated_by,
            reason="Rotated - replaced by new key",
        )

        # Generate new key
        raw_key, new_key = await self.generate_api_key(
            robot_id=old_key.robot_id,
            name=f"{old_key.name or 'Key'} (rotated)",
            description=old_key.description,
            expires_at=old_key.expires_at,
            created_by=rotated_by,
        )

        logger.info(
            f"Rotated API key: old={key_id}, new={new_key.id}, " f"robot={old_key.robot_id}"
        )

        return raw_key, new_key

    async def delete_expired_keys(self, days_old: int = 30) -> int:
        """
        Delete keys that have been expired for more than N days.

        Args:
            days_old: Days since expiration to delete

        Returns:
            Number of keys deleted
        """
        try:
            count = await self._delete_expired_keys(days_old)
            logger.info(f"Deleted {count} expired API keys (older than {days_old} days)")
            return count
        except Exception as e:
            logger.error(f"Failed to delete expired API keys: {e}")
            return 0

    # =========================================================================
    # DATABASE OPERATIONS (to be overridden for different backends)
    # =========================================================================

    async def _insert_key(
        self,
        robot_id: str,
        api_key_hash: str,
        name: str | None,
        description: str | None,
        expires_at: datetime | None,
        created_by: str | None,
    ) -> dict[str, Any]:
        """Insert a new API key into the database."""
        # Supabase client implementation
        if hasattr(self._client, "table"):
            response = (
                self._client.table(self._table_name)
                .insert(
                    {
                        "robot_id": robot_id,
                        "api_key_hash": api_key_hash,
                        "name": name,
                        "description": description,
                        "expires_at": expires_at.isoformat() if expires_at else None,
                        "created_by": created_by,
                    }
                )
                .execute()
            )
            return response.data[0]

        # asyncpg pool implementation
        if hasattr(self._client, "acquire"):
            async with self._client.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO robot_api_keys (
                        robot_id, api_key_hash, name, description, expires_at, created_by
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING id, robot_id, api_key_hash, name, description,
                              created_at, expires_at, created_by
                    """,
                    robot_id,
                    api_key_hash,
                    name,
                    description,
                    expires_at,
                    created_by,
                )
                return dict(row)

        raise RobotApiKeyError("Unsupported database client type")

    async def _get_key_by_hash(self, api_key_hash: str) -> RobotApiKey | None:
        """Get an API key by its hash."""
        # Supabase client implementation
        if hasattr(self._client, "table"):
            response = (
                self._client.table(self._table_name)
                .select("*")
                .eq("api_key_hash", api_key_hash)
                .execute()
            )
            if not response.data:
                return None
            return self._row_to_key(response.data[0])

        # asyncpg pool implementation
        if hasattr(self._client, "acquire"):
            async with self._client.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM robot_api_keys WHERE api_key_hash = $1",
                    api_key_hash,
                )
                if row is None:
                    return None
                return self._row_to_key(dict(row))

        raise RobotApiKeyError("Unsupported database client type")

    async def _get_key_by_id(self, key_id: str) -> RobotApiKey | None:
        """Get an API key by its ID."""
        # Supabase client implementation
        if hasattr(self._client, "table"):
            response = self._client.table(self._table_name).select("*").eq("id", key_id).execute()
            if not response.data:
                return None
            return self._row_to_key(response.data[0])

        # asyncpg pool implementation
        if hasattr(self._client, "acquire"):
            async with self._client.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM robot_api_keys WHERE id = $1",
                    key_id,
                )
                if row is None:
                    return None
                return self._row_to_key(dict(row))

        raise RobotApiKeyError("Unsupported database client type")

    async def _update_last_used(
        self,
        api_key_hash: str,
        client_ip: str | None,
    ) -> None:
        """Update last_used_at timestamp for a key."""
        now = datetime.now(UTC)

        # Supabase client implementation
        if hasattr(self._client, "table"):
            update_data = {"last_used_at": now.isoformat()}
            if client_ip:
                update_data["last_used_ip"] = client_ip

            self._client.table(self._table_name).update(update_data).eq(
                "api_key_hash", api_key_hash
            ).execute()
            return

        # asyncpg pool implementation
        if hasattr(self._client, "acquire"):
            async with self._client.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE robot_api_keys
                    SET last_used_at = $1, last_used_ip = COALESCE($2, last_used_ip)
                    WHERE api_key_hash = $3
                    """,
                    now,
                    client_ip,
                    api_key_hash,
                )
            return

        raise RobotApiKeyError("Unsupported database client type")

    async def _revoke_key(
        self,
        key_id: str,
        revoked_by: str | None,
        reason: str | None,
    ) -> bool:
        """Revoke an API key."""
        now = datetime.now(UTC)

        # Supabase client implementation
        if hasattr(self._client, "table"):
            response = (
                self._client.table(self._table_name)
                .update(
                    {
                        "is_revoked": True,
                        "revoked_at": now.isoformat(),
                        "revoked_by": revoked_by,
                        "revoke_reason": reason,
                    }
                )
                .eq("id", key_id)
                .execute()
            )
            return len(response.data) > 0

        # asyncpg pool implementation
        if hasattr(self._client, "acquire"):
            async with self._client.acquire() as conn:
                result = await conn.execute(
                    """
                    UPDATE robot_api_keys
                    SET is_revoked = TRUE, revoked_at = $1, revoked_by = $2, revoke_reason = $3
                    WHERE id = $4
                    """,
                    now,
                    revoked_by,
                    reason,
                    key_id,
                )
                return "UPDATE 1" in result

        raise RobotApiKeyError("Unsupported database client type")

    async def _list_keys_for_robot(
        self,
        robot_id: str,
        include_revoked: bool,
    ) -> list[RobotApiKey]:
        """List all API keys for a robot."""
        # Supabase client implementation
        if hasattr(self._client, "table"):
            query = self._client.table(self._table_name).select("*").eq("robot_id", robot_id)
            if not include_revoked:
                query = query.eq("is_revoked", False)
            response = query.order("created_at", desc=True).execute()
            return [self._row_to_key(row) for row in response.data]

        # asyncpg pool implementation
        if hasattr(self._client, "acquire"):
            async with self._client.acquire() as conn:
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
                return [self._row_to_key(dict(row)) for row in rows]

        raise RobotApiKeyError("Unsupported database client type")

    async def _delete_expired_keys(self, days_old: int) -> int:
        """Delete expired keys older than N days."""
        # asyncpg pool implementation
        if hasattr(self._client, "acquire"):
            async with self._client.acquire() as conn:
                result = await conn.execute(
                    """
                    DELETE FROM robot_api_keys
                    WHERE expires_at IS NOT NULL
                    AND expires_at < NOW() - $1 * INTERVAL '1 day'
                    """,
                    days_old,
                )
                return int(result.split()[-1])

        # Supabase doesn't support complex DELETE with intervals easily
        # Would need to compute the cutoff date and use RPC
        return 0

    def _row_to_key(self, row: dict[str, Any]) -> RobotApiKey:
        """Convert a database row to a RobotApiKey."""
        return RobotApiKey(
            id=str(row["id"]),
            robot_id=str(row["robot_id"]),
            api_key_hash=row["api_key_hash"],
            name=row.get("name"),
            description=row.get("description"),
            created_at=self._parse_datetime(row.get("created_at")),
            expires_at=self._parse_datetime(row.get("expires_at")),
            last_used_at=self._parse_datetime(row.get("last_used_at")),
            last_used_ip=row.get("last_used_ip"),
            is_revoked=row.get("is_revoked", False),
            revoked_at=self._parse_datetime(row.get("revoked_at")),
            revoked_by=row.get("revoked_by"),
            revoke_reason=row.get("revoke_reason"),
            created_by=row.get("created_by"),
        )

    def _parse_datetime(self, value: Any) -> datetime | None:
        """Parse datetime from various formats."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            # Handle ISO format with or without timezone
            try:
                if value.endswith("Z"):
                    value = value[:-1] + "+00:00"
                return datetime.fromisoformat(value)
            except ValueError:
                logger.warning(f"Failed to parse datetime: {value}")
                return None
        return None


__all__ = [
    "RobotApiKey",
    "RobotApiKeyService",
    "RobotApiKeyError",
    "ApiKeyNotFoundError",
    "ApiKeyRevokedError",
    "ApiKeyExpiredError",
    "ApiKeyValidationResult",
    "generate_api_key_raw",
    "hash_api_key",
    "validate_api_key_format",
    "extract_key_prefix",
]
