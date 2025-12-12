"""
CasareRPA - User Domain Entity.

Represents a user in the system with authentication and authorization attributes.
Pure domain entity with no external dependencies.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID


class UserStatus(str, Enum):
    """User account status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"
    PENDING_VERIFICATION = "pending_verification"


@dataclass
class User:
    """
    User domain entity.

    Represents an authenticated user in the system with role assignments
    and MFA configuration.
    """

    id: UUID
    email: str
    password_hash: str
    role: str  # SystemRole value from RBAC
    display_name: Optional[str] = None
    tenant_id: Optional[UUID] = None
    status: UserStatus = UserStatus.ACTIVE
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None  # Encrypted TOTP secret
    email_verified: bool = False
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    last_login: Optional[datetime] = None
    last_password_change: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        """Validate user entity on creation."""
        if not self.email:
            raise ValueError("User email cannot be empty")
        if not self.password_hash:
            raise ValueError("Password hash cannot be empty")
        if "@" not in self.email:
            raise ValueError("Invalid email format")

    @property
    def is_active(self) -> bool:
        """Check if user account is active."""
        return self.status == UserStatus.ACTIVE

    @property
    def is_locked(self) -> bool:
        """Check if user account is locked."""
        if self.status == UserStatus.LOCKED:
            return True
        if self.locked_until and datetime.now(timezone.utc) < self.locked_until:
            return True
        return False

    @property
    def requires_mfa(self) -> bool:
        """Check if MFA verification is required for this user."""
        return self.mfa_enabled and self.mfa_secret is not None

    def record_login(self) -> None:
        """Record successful login."""
        self.last_login = datetime.now(timezone.utc)
        self.failed_login_attempts = 0
        self.locked_until = None
        self.updated_at = datetime.now(timezone.utc)

    def record_failed_login(
        self, max_attempts: int = 5, lockout_minutes: int = 30
    ) -> None:
        """
        Record failed login attempt.

        Args:
            max_attempts: Maximum attempts before lockout
            lockout_minutes: Duration of lockout in minutes
        """
        self.failed_login_attempts += 1
        self.updated_at = datetime.now(timezone.utc)

        if self.failed_login_attempts >= max_attempts:
            from datetime import timedelta

            self.locked_until = datetime.now(timezone.utc) + timedelta(
                minutes=lockout_minutes
            )
            self.status = UserStatus.LOCKED

    def unlock(self) -> None:
        """Unlock a locked account."""
        self.status = UserStatus.ACTIVE
        self.locked_until = None
        self.failed_login_attempts = 0
        self.updated_at = datetime.now(timezone.utc)

    def enable_mfa(self, encrypted_secret: str) -> None:
        """
        Enable MFA for this user.

        Args:
            encrypted_secret: Encrypted TOTP secret
        """
        if not encrypted_secret:
            raise ValueError("MFA secret cannot be empty")
        self.mfa_enabled = True
        self.mfa_secret = encrypted_secret
        self.updated_at = datetime.now(timezone.utc)

    def disable_mfa(self) -> None:
        """Disable MFA for this user."""
        self.mfa_enabled = False
        self.mfa_secret = None
        self.updated_at = datetime.now(timezone.utc)

    def change_password(self, new_password_hash: str) -> None:
        """
        Update password hash.

        Args:
            new_password_hash: New bcrypt password hash
        """
        if not new_password_hash:
            raise ValueError("Password hash cannot be empty")
        self.password_hash = new_password_hash
        self.last_password_change = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self, include_sensitive: bool = False) -> dict:
        """
        Convert to dictionary representation.

        Args:
            include_sensitive: Include sensitive fields like password_hash

        Returns:
            Dictionary representation of user
        """
        data = {
            "id": str(self.id),
            "email": self.email,
            "display_name": self.display_name,
            "role": self.role,
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "status": self.status.value,
            "mfa_enabled": self.mfa_enabled,
            "email_verified": self.email_verified,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_sensitive:
            data["password_hash"] = self.password_hash
            data["mfa_secret"] = self.mfa_secret
            data["failed_login_attempts"] = self.failed_login_attempts
            data["locked_until"] = (
                self.locked_until.isoformat() if self.locked_until else None
            )
        return data


__all__ = ["User", "UserStatus"]
