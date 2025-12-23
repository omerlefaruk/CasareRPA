"""
CasareRPA - User Manager.

Manages user authentication including:
- User creation with password hashing
- Password verification
- User lookup and management
- MFA enrollment

Usage:
    from casare_rpa.infrastructure.auth import UserManager

    manager = UserManager(db_client)

    # Create user
    user = await manager.create_user(
        email="user@example.com",
        password="YOUR_SECURE_PASSWORD",
        role=SystemRole.DEVELOPER
    )

    # Authenticate
    auth_result = await manager.authenticate(email, password)
    if auth_result.success:
        user = auth_result.user
"""

import asyncio
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

import bcrypt
from loguru import logger

from casare_rpa.domain.entities.user import User, UserStatus
from casare_rpa.infrastructure.security.rbac import SystemRole

# =============================================================================
# CONSTANTS
# =============================================================================

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
BCRYPT_ROUNDS = 12
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


# =============================================================================
# EXCEPTIONS
# =============================================================================


class UserManagerError(Exception):
    """Base exception for user manager operations."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(message)


class UserNotFoundError(UserManagerError):
    """Raised when user is not found."""

    def __init__(self, identifier: str) -> None:
        super().__init__(f"User not found: {identifier}")
        self.identifier = identifier


class UserExistsError(UserManagerError):
    """Raised when user already exists."""

    def __init__(self, email: str) -> None:
        super().__init__(f"User with email already exists: {email}")
        self.email = email


class InvalidPasswordError(UserManagerError):
    """Raised when password does not meet requirements."""

    pass


class InvalidEmailError(UserManagerError):
    """Raised when email format is invalid."""

    pass


class AccountLockedError(UserManagerError):
    """Raised when account is locked."""

    def __init__(self, user_id: UUID, locked_until: datetime | None = None) -> None:
        msg = f"Account is locked: {user_id}"
        if locked_until:
            msg += f" until {locked_until.isoformat()}"
        super().__init__(msg)
        self.user_id = user_id
        self.locked_until = locked_until


# =============================================================================
# DATA MODELS
# =============================================================================


class AuthResult(str, Enum):
    """Authentication result status."""

    SUCCESS = "success"
    INVALID_CREDENTIALS = "invalid_credentials"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_INACTIVE = "account_inactive"
    MFA_REQUIRED = "mfa_required"


@dataclass
class AuthenticationResult:
    """Result of authentication attempt."""

    status: AuthResult
    user: User | None = None
    message: str | None = None
    requires_mfa: bool = False

    @property
    def success(self) -> bool:
        """Check if authentication succeeded."""
        return self.status == AuthResult.SUCCESS

    @property
    def needs_mfa(self) -> bool:
        """Check if MFA verification is needed."""
        return self.status == AuthResult.MFA_REQUIRED or self.requires_mfa


@dataclass
class PasswordPolicy:
    """Password strength requirements."""

    min_length: int = MIN_PASSWORD_LENGTH
    max_length: int = MAX_PASSWORD_LENGTH
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digit: bool = True
    require_special: bool = False
    special_chars: str = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    def validate(self, password: str) -> tuple[bool, str]:
        """
        Validate password against policy.

        Args:
            password: Password to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < self.min_length:
            return False, f"Password must be at least {self.min_length} characters"
        if len(password) > self.max_length:
            return False, f"Password must be at most {self.max_length} characters"
        if self.require_uppercase and not any(c.isupper() for c in password):
            return False, "Password must contain uppercase letter"
        if self.require_lowercase and not any(c.islower() for c in password):
            return False, "Password must contain lowercase letter"
        if self.require_digit and not any(c.isdigit() for c in password):
            return False, "Password must contain digit"
        if self.require_special and not any(c in self.special_chars for c in password):
            return (
                False,
                f"Password must contain special character: {self.special_chars}",
            )
        return True, ""


# =============================================================================
# USER MANAGER
# =============================================================================


class UserManager:
    """
    Manager for user authentication and management.

    Handles user CRUD, password hashing, and authentication.
    """

    def __init__(
        self,
        db_client: Any,
        password_policy: PasswordPolicy | None = None,
        max_login_attempts: int = 5,
        lockout_minutes: int = 30,
    ) -> None:
        """
        Initialize user manager.

        Args:
            db_client: Database client (Supabase or asyncpg pool)
            password_policy: Password strength requirements
            max_login_attempts: Max failed logins before lockout
            lockout_minutes: Lockout duration in minutes
        """
        self._client = db_client
        self._password_policy = password_policy or PasswordPolicy()
        self._max_login_attempts = max_login_attempts
        self._lockout_minutes = lockout_minutes
        self._table_name = "users"
        self._lock = asyncio.Lock()

    async def create_user(
        self,
        email: str,
        password: str,
        role: SystemRole = SystemRole.DEVELOPER,
        display_name: str | None = None,
        tenant_id: UUID | None = None,
        created_by: UUID | None = None,
    ) -> User:
        """
        Create a new user account.

        Args:
            email: User email address
            password: Plain text password
            role: User role (default DEVELOPER)
            display_name: Optional display name
            tenant_id: Optional tenant ID
            created_by: Optional ID of user creating this account

        Returns:
            Created User entity

        Raises:
            UserExistsError: If email already registered
            InvalidEmailError: If email format invalid
            InvalidPasswordError: If password doesn't meet policy
        """
        # Validate email
        email = email.strip().lower()
        if not EMAIL_REGEX.match(email):
            raise InvalidEmailError(f"Invalid email format: {email}")

        # Validate password
        is_valid, error_msg = self._password_policy.validate(password)
        if not is_valid:
            raise InvalidPasswordError(error_msg)

        # Check if user exists
        existing = await self._get_user_by_email(email)
        if existing:
            raise UserExistsError(email)

        # Hash password
        password_hash = self._hash_password(password)

        # Create user
        user_id = uuid4()
        now = datetime.now(UTC)

        user = User(
            id=user_id,
            email=email,
            password_hash=password_hash,
            role=role.value,
            display_name=display_name or email.split("@")[0],
            tenant_id=tenant_id,
            status=UserStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )

        try:
            await self._insert_user(user)
            logger.info(f"Created user: {email} with role {role.value}")
            return user
        except Exception as e:
            logger.error(f"Failed to create user {email}: {e}")
            raise UserManagerError(f"Failed to create user: {e}") from e

    async def authenticate(
        self,
        email: str,
        password: str,
    ) -> AuthenticationResult:
        """
        Authenticate user with email and password.

        Args:
            email: User email
            password: Plain text password

        Returns:
            AuthenticationResult with status and user if successful
        """
        email = email.strip().lower()

        try:
            user = await self._get_user_by_email(email)
        except Exception as e:
            logger.error(f"Database error during authentication: {e}")
            return AuthenticationResult(
                status=AuthResult.INVALID_CREDENTIALS,
                message="Authentication failed",
            )

        if not user:
            logger.debug(f"Authentication failed: user not found {email}")
            return AuthenticationResult(
                status=AuthResult.INVALID_CREDENTIALS,
                message="Invalid email or password",
            )

        # Check account status
        if user.is_locked:
            logger.warning(f"Authentication blocked: account locked {email}")
            return AuthenticationResult(
                status=AuthResult.ACCOUNT_LOCKED,
                message="Account is locked. Try again later.",
            )

        if not user.is_active:
            logger.warning(f"Authentication blocked: account inactive {email}")
            return AuthenticationResult(
                status=AuthResult.ACCOUNT_INACTIVE,
                message="Account is not active",
            )

        # Verify password
        if not self._verify_password(password, user.password_hash):
            user.record_failed_login(self._max_login_attempts, self._lockout_minutes)
            await self._update_user(user)
            logger.debug(f"Authentication failed: invalid password for {email}")
            return AuthenticationResult(
                status=AuthResult.INVALID_CREDENTIALS,
                message="Invalid email or password",
            )

        # Check if MFA required
        if user.requires_mfa:
            logger.debug(f"MFA required for user {email}")
            return AuthenticationResult(
                status=AuthResult.MFA_REQUIRED,
                user=user,
                requires_mfa=True,
                message="MFA verification required",
            )

        # Success - update last login
        user.record_login()
        await self._update_user(user)
        logger.info(f"User authenticated: {email}")

        return AuthenticationResult(
            status=AuthResult.SUCCESS,
            user=user,
        )

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        """Get user by ID."""
        return await self._get_user_by_id(user_id)

    async def get_user_by_email(self, email: str) -> User | None:
        """Get user by email."""
        return await self._get_user_by_email(email.strip().lower())

    async def update_password(
        self,
        user_id: UUID,
        current_password: str,
        new_password: str,
    ) -> bool:
        """
        Update user password.

        Args:
            user_id: User ID
            current_password: Current password for verification
            new_password: New password

        Returns:
            True if password updated

        Raises:
            UserNotFoundError: If user not found
            InvalidPasswordError: If current password wrong or new invalid
        """
        user = await self._get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError(str(user_id))

        if not self._verify_password(current_password, user.password_hash):
            raise InvalidPasswordError("Current password is incorrect")

        is_valid, error_msg = self._password_policy.validate(new_password)
        if not is_valid:
            raise InvalidPasswordError(error_msg)

        new_hash = self._hash_password(new_password)
        user.change_password(new_hash)
        await self._update_user(user)
        logger.info(f"Password updated for user {user_id}")
        return True

    async def reset_password(
        self,
        user_id: UUID,
        new_password: str,
    ) -> bool:
        """
        Reset user password (admin operation).

        Args:
            user_id: User ID
            new_password: New password

        Returns:
            True if password reset
        """
        user = await self._get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError(str(user_id))

        is_valid, error_msg = self._password_policy.validate(new_password)
        if not is_valid:
            raise InvalidPasswordError(error_msg)

        new_hash = self._hash_password(new_password)
        user.change_password(new_hash)
        await self._update_user(user)
        logger.info(f"Password reset for user {user_id}")
        return True

    async def unlock_account(self, user_id: UUID) -> bool:
        """
        Unlock a locked user account.

        Args:
            user_id: User ID to unlock

        Returns:
            True if unlocked
        """
        user = await self._get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError(str(user_id))

        user.unlock()
        await self._update_user(user)
        logger.info(f"Account unlocked: {user_id}")
        return True

    async def deactivate_user(self, user_id: UUID) -> bool:
        """
        Deactivate a user account.

        Args:
            user_id: User ID to deactivate

        Returns:
            True if deactivated
        """
        user = await self._get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError(str(user_id))

        user.status = UserStatus.INACTIVE
        user.updated_at = datetime.now(UTC)
        await self._update_user(user)
        logger.info(f"User deactivated: {user_id}")
        return True

    async def enable_mfa(
        self,
        user_id: UUID,
        encrypted_secret: str,
    ) -> bool:
        """
        Enable MFA for a user.

        Args:
            user_id: User ID
            encrypted_secret: Encrypted TOTP secret

        Returns:
            True if MFA enabled
        """
        user = await self._get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError(str(user_id))

        user.enable_mfa(encrypted_secret)
        await self._update_user(user)
        logger.info(f"MFA enabled for user {user_id}")
        return True

    async def disable_mfa(self, user_id: UUID) -> bool:
        """
        Disable MFA for a user.

        Args:
            user_id: User ID

        Returns:
            True if MFA disabled
        """
        user = await self._get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError(str(user_id))

        user.disable_mfa()
        await self._update_user(user)
        logger.info(f"MFA disabled for user {user_id}")
        return True

    async def list_users(
        self,
        tenant_id: UUID | None = None,
        include_inactive: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[User]:
        """
        List users with optional filtering.

        Args:
            tenant_id: Filter by tenant
            include_inactive: Include inactive users
            limit: Maximum users to return
            offset: Pagination offset

        Returns:
            List of User entities
        """
        return await self._list_users(tenant_id, include_inactive, limit, offset)

    def _hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash."""
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"),
                password_hash.encode("utf-8"),
            )
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    # =========================================================================
    # DATABASE OPERATIONS
    # =========================================================================

    async def _insert_user(self, user: User) -> None:
        """Insert a new user into the database."""
        data = {
            "id": str(user.id),
            "email": user.email,
            "password_hash": user.password_hash,
            "role": user.role,
            "display_name": user.display_name,
            "tenant_id": str(user.tenant_id) if user.tenant_id else None,
            "status": user.status.value,
            "mfa_enabled": user.mfa_enabled,
            "mfa_secret": user.mfa_secret,
            "email_verified": user.email_verified,
            "failed_login_attempts": user.failed_login_attempts,
            "locked_until": user.locked_until.isoformat() if user.locked_until else None,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat(),
        }

        if hasattr(self._client, "table"):
            self._client.table(self._table_name).insert(data).execute()
        elif hasattr(self._client, "acquire"):
            async with self._client.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO users (
                        id, email, password_hash, role, display_name, tenant_id,
                        status, mfa_enabled, mfa_secret, email_verified,
                        failed_login_attempts, locked_until, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                    """,
                    user.id,
                    user.email,
                    user.password_hash,
                    user.role,
                    user.display_name,
                    user.tenant_id,
                    user.status.value,
                    user.mfa_enabled,
                    user.mfa_secret,
                    user.email_verified,
                    user.failed_login_attempts,
                    user.locked_until,
                    user.created_at,
                    user.updated_at,
                )
        else:
            raise UserManagerError("Unsupported database client type")

    async def _update_user(self, user: User) -> None:
        """Update an existing user in the database."""
        data = {
            "email": user.email,
            "password_hash": user.password_hash,
            "role": user.role,
            "display_name": user.display_name,
            "status": user.status.value,
            "mfa_enabled": user.mfa_enabled,
            "mfa_secret": user.mfa_secret,
            "email_verified": user.email_verified,
            "failed_login_attempts": user.failed_login_attempts,
            "locked_until": user.locked_until.isoformat() if user.locked_until else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "last_password_change": (
                user.last_password_change.isoformat() if user.last_password_change else None
            ),
            "updated_at": user.updated_at.isoformat(),
        }

        if hasattr(self._client, "table"):
            self._client.table(self._table_name).update(data).eq("id", str(user.id)).execute()
        elif hasattr(self._client, "acquire"):
            async with self._client.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE users SET
                        email = $1, password_hash = $2, role = $3, display_name = $4,
                        status = $5, mfa_enabled = $6, mfa_secret = $7, email_verified = $8,
                        failed_login_attempts = $9, locked_until = $10, last_login = $11,
                        last_password_change = $12, updated_at = $13
                    WHERE id = $14
                    """,
                    user.email,
                    user.password_hash,
                    user.role,
                    user.display_name,
                    user.status.value,
                    user.mfa_enabled,
                    user.mfa_secret,
                    user.email_verified,
                    user.failed_login_attempts,
                    user.locked_until,
                    user.last_login,
                    user.last_password_change,
                    user.updated_at,
                    user.id,
                )
        else:
            raise UserManagerError("Unsupported database client type")

    async def _get_user_by_id(self, user_id: UUID) -> User | None:
        """Get user by ID from database."""
        if hasattr(self._client, "table"):
            response = (
                self._client.table(self._table_name).select("*").eq("id", str(user_id)).execute()
            )
            if not response.data:
                return None
            return self._row_to_user(response.data[0])

        if hasattr(self._client, "acquire"):
            async with self._client.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM users WHERE id = $1",
                    user_id,
                )
                if row is None:
                    return None
                return self._row_to_user(dict(row))

        raise UserManagerError("Unsupported database client type")

    async def _get_user_by_email(self, email: str) -> User | None:
        """Get user by email from database."""
        if hasattr(self._client, "table"):
            response = self._client.table(self._table_name).select("*").eq("email", email).execute()
            if not response.data:
                return None
            return self._row_to_user(response.data[0])

        if hasattr(self._client, "acquire"):
            async with self._client.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM users WHERE email = $1",
                    email,
                )
                if row is None:
                    return None
                return self._row_to_user(dict(row))

        raise UserManagerError("Unsupported database client type")

    async def _list_users(
        self,
        tenant_id: UUID | None,
        include_inactive: bool,
        limit: int,
        offset: int,
    ) -> list[User]:
        """List users from database."""
        if hasattr(self._client, "table"):
            query = self._client.table(self._table_name).select("*")
            if tenant_id:
                query = query.eq("tenant_id", str(tenant_id))
            if not include_inactive:
                query = query.eq("status", UserStatus.ACTIVE.value)
            response = query.range(offset, offset + limit - 1).execute()
            return [self._row_to_user(row) for row in response.data]

        if hasattr(self._client, "acquire"):
            async with self._client.acquire() as conn:
                conditions = []
                params = []
                param_idx = 1

                if tenant_id:
                    conditions.append(f"tenant_id = ${param_idx}")
                    params.append(tenant_id)
                    param_idx += 1

                if not include_inactive:
                    conditions.append(f"status = ${param_idx}")
                    params.append(UserStatus.ACTIVE.value)
                    param_idx += 1

                where_clause = " AND ".join(conditions) if conditions else "TRUE"
                params.extend([limit, offset])

                rows = await conn.fetch(
                    f"""
                    SELECT * FROM users
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                    LIMIT ${param_idx} OFFSET ${param_idx + 1}
                    """,
                    *params,
                )
                return [self._row_to_user(dict(row)) for row in rows]

        raise UserManagerError("Unsupported database client type")

    def _row_to_user(self, row: dict[str, Any]) -> User:
        """Convert a database row to User entity."""
        return User(
            id=UUID(str(row["id"])),
            email=row["email"],
            password_hash=row["password_hash"],
            role=row["role"],
            display_name=row.get("display_name"),
            tenant_id=UUID(str(row["tenant_id"])) if row.get("tenant_id") else None,
            status=UserStatus(row.get("status", "active")),
            mfa_enabled=row.get("mfa_enabled", False),
            mfa_secret=row.get("mfa_secret"),
            email_verified=row.get("email_verified", False),
            failed_login_attempts=row.get("failed_login_attempts", 0),
            locked_until=self._parse_datetime(row.get("locked_until")),
            last_login=self._parse_datetime(row.get("last_login")),
            last_password_change=self._parse_datetime(row.get("last_password_change")),
            created_at=self._parse_datetime(row.get("created_at")) or datetime.now(UTC),
            updated_at=self._parse_datetime(row.get("updated_at")) or datetime.now(UTC),
        )

    def _parse_datetime(self, value: Any) -> datetime | None:
        """Parse datetime from various formats."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                if value.endswith("Z"):
                    value = value[:-1] + "+00:00"
                return datetime.fromisoformat(value)
            except ValueError:
                return None
        return None


__all__ = [
    "UserManager",
    "UserManagerError",
    "UserNotFoundError",
    "UserExistsError",
    "InvalidPasswordError",
    "InvalidEmailError",
    "AccountLockedError",
    "AuthenticationResult",
    "AuthResult",
    "PasswordPolicy",
]
