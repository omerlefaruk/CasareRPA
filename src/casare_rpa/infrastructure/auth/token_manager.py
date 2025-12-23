"""
CasareRPA - JWT Token Manager.

Manages JWT tokens for user authentication:
- Access token generation and validation
- Refresh token handling
- Token payload extraction

Usage:
    from casare_rpa.infrastructure.auth import TokenManager

    manager = TokenManager(secret_key="your-secret")

    # Generate tokens
    access_token = manager.generate_access_token(user)
    refresh_token = manager.generate_refresh_token(user)

    # Validate and extract
    payload = manager.validate_token(access_token)
    user_id = payload["sub"]
"""

import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID

import jwt
from loguru import logger

from casare_rpa.domain.entities.user import User

# =============================================================================
# CONSTANTS
# =============================================================================

DEFAULT_ACCESS_TOKEN_MINUTES = 60  # 1 hour
DEFAULT_REFRESH_TOKEN_DAYS = 30
JWT_ALGORITHM = "HS256"
TOKEN_TYPE_CLAIM = "type"


# =============================================================================
# ENUMS
# =============================================================================


class TokenType(str, Enum):
    """JWT token types."""

    ACCESS = "access"
    REFRESH = "refresh"
    MFA_PENDING = "mfa_pending"  # Temporary token waiting for MFA


# =============================================================================
# EXCEPTIONS
# =============================================================================


class TokenError(Exception):
    """Base exception for token operations."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(message)


class TokenExpiredError(TokenError):
    """Raised when token has expired."""

    pass


class TokenInvalidError(TokenError):
    """Raised when token is invalid or malformed."""

    pass


class TokenRevokedError(TokenError):
    """Raised when token has been revoked."""

    pass


# =============================================================================
# DATA MODELS
# =============================================================================


@dataclass
class TokenConfig:
    """Token generation configuration."""

    access_token_minutes: int = DEFAULT_ACCESS_TOKEN_MINUTES
    refresh_token_days: int = DEFAULT_REFRESH_TOKEN_DAYS
    include_roles: bool = True
    include_tenant: bool = True


@dataclass
class TokenPayload:
    """Parsed JWT token payload."""

    sub: str  # User ID
    email: str
    role: str
    token_type: TokenType
    tenant_id: str | None = None
    exp: datetime | None = None
    iat: datetime | None = None
    jti: str | None = None  # JWT ID for revocation tracking
    mfa_verified: bool = True
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def user_id(self) -> UUID:
        """Get user ID as UUID."""
        return UUID(self.sub)

    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        if self.exp is None:
            return False
        return datetime.now(UTC) > self.exp

    @property
    def is_access_token(self) -> bool:
        """Check if this is an access token."""
        return self.token_type == TokenType.ACCESS

    @property
    def is_refresh_token(self) -> bool:
        """Check if this is a refresh token."""
        return self.token_type == TokenType.REFRESH

    @property
    def requires_mfa(self) -> bool:
        """Check if MFA verification is still required."""
        return self.token_type == TokenType.MFA_PENDING


# =============================================================================
# TOKEN MANAGER
# =============================================================================


class TokenManager:
    """
    Manager for JWT token operations.

    Handles generation, validation, and refresh of JWT tokens.
    """

    def __init__(
        self,
        secret_key: str,
        config: TokenConfig | None = None,
        algorithm: str = JWT_ALGORITHM,
    ) -> None:
        """
        Initialize token manager.

        Args:
            secret_key: Secret key for signing tokens
            config: Token configuration options
            algorithm: JWT algorithm (default HS256)
        """
        if not secret_key or len(secret_key) < 32:
            raise TokenError("Secret key must be at least 32 characters")

        self._secret_key = secret_key
        self._config = config or TokenConfig()
        self._algorithm = algorithm
        self._revoked_tokens: set[str] = set()  # JTI tracking

    def generate_access_token(
        self,
        user: User,
        mfa_verified: bool = True,
        extra_claims: dict[str, Any] | None = None,
    ) -> str:
        """
        Generate an access token for a user.

        Args:
            user: User entity
            mfa_verified: Whether MFA has been verified
            extra_claims: Additional claims to include

        Returns:
            JWT access token string
        """
        now = datetime.now(UTC)
        expires = now + timedelta(minutes=self._config.access_token_minutes)

        # Determine token type based on MFA status
        if user.requires_mfa and not mfa_verified:
            token_type = TokenType.MFA_PENDING
        else:
            token_type = TokenType.ACCESS

        payload = self._build_payload(
            user=user,
            token_type=token_type,
            expires=expires,
            issued_at=now,
            mfa_verified=mfa_verified,
            extra_claims=extra_claims,
        )

        token = jwt.encode(payload, self._secret_key, algorithm=self._algorithm)
        logger.debug(
            f"Generated {token_type.value} token for user {user.id}, "
            f"expires {expires.isoformat()}"
        )
        return token

    def generate_refresh_token(
        self,
        user: User,
        extra_claims: dict[str, Any] | None = None,
    ) -> str:
        """
        Generate a refresh token for a user.

        Args:
            user: User entity
            extra_claims: Additional claims to include

        Returns:
            JWT refresh token string
        """
        now = datetime.now(UTC)
        expires = now + timedelta(days=self._config.refresh_token_days)

        payload = self._build_payload(
            user=user,
            token_type=TokenType.REFRESH,
            expires=expires,
            issued_at=now,
            mfa_verified=True,  # Refresh tokens always assume MFA was done
            extra_claims=extra_claims,
        )

        token = jwt.encode(payload, self._secret_key, algorithm=self._algorithm)
        logger.debug(
            f"Generated refresh token for user {user.id}, " f"expires {expires.isoformat()}"
        )
        return token

    def validate_token(
        self,
        token: str,
        expected_type: TokenType | None = None,
        verify_expiration: bool = True,
    ) -> TokenPayload:
        """
        Validate a JWT token and return its payload.

        Args:
            token: JWT token string
            expected_type: Expected token type (None = any)
            verify_expiration: Whether to verify expiration

        Returns:
            TokenPayload with parsed claims

        Raises:
            TokenExpiredError: If token has expired
            TokenInvalidError: If token is invalid
            TokenRevokedError: If token has been revoked
        """
        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],
                options={"verify_exp": verify_expiration},
            )
        except jwt.ExpiredSignatureError as e:
            raise TokenExpiredError("Token has expired") from e
        except jwt.InvalidTokenError as e:
            raise TokenInvalidError(f"Invalid token: {e}") from e

        # Check if revoked
        jti = payload.get("jti")
        if jti and jti in self._revoked_tokens:
            raise TokenRevokedError("Token has been revoked")

        # Parse token type
        raw_type = payload.get(TOKEN_TYPE_CLAIM, TokenType.ACCESS.value)
        try:
            token_type = TokenType(raw_type)
        except ValueError:
            token_type = TokenType.ACCESS

        # Verify expected type
        if expected_type and token_type != expected_type:
            raise TokenInvalidError(f"Expected {expected_type.value} token, got {token_type.value}")

        # Parse expiration
        exp = None
        if "exp" in payload:
            exp = datetime.fromtimestamp(payload["exp"], tz=UTC)

        iat = None
        if "iat" in payload:
            iat = datetime.fromtimestamp(payload["iat"], tz=UTC)

        return TokenPayload(
            sub=payload["sub"],
            email=payload.get("email", ""),
            role=payload.get("role", ""),
            token_type=token_type,
            tenant_id=payload.get("tenant_id"),
            exp=exp,
            iat=iat,
            jti=jti,
            mfa_verified=payload.get("mfa_verified", True),
            extra={
                k: v
                for k, v in payload.items()
                if k
                not in {
                    "sub",
                    "email",
                    "role",
                    "type",
                    "tenant_id",
                    "exp",
                    "iat",
                    "jti",
                    "mfa_verified",
                }
            },
        )

    def refresh_access_token(
        self,
        refresh_token: str,
        user: User,
    ) -> str:
        """
        Generate a new access token using a refresh token.

        Args:
            refresh_token: Valid refresh token
            user: User entity (must match token)

        Returns:
            New access token

        Raises:
            TokenError: If refresh token is invalid or user mismatch
        """
        payload = self.validate_token(refresh_token, expected_type=TokenType.REFRESH)

        if str(user.id) != payload.sub:
            raise TokenInvalidError("Token user ID does not match")

        return self.generate_access_token(user, mfa_verified=True)

    def revoke_token(self, token: str) -> bool:
        """
        Revoke a token by adding its JTI to the revoked set.

        Args:
            token: Token to revoke

        Returns:
            True if revoked, False if no JTI present
        """
        try:
            payload = self.validate_token(token, verify_expiration=False)
            if payload.jti:
                self._revoked_tokens.add(payload.jti)
                logger.info(f"Revoked token: {payload.jti}")
                return True
            return False
        except TokenError:
            return False

    def decode_without_verification(self, token: str) -> dict[str, Any]:
        """
        Decode token without verifying signature.

        Args:
            token: JWT token

        Returns:
            Raw payload dictionary

        Note:
            Use only for debugging/logging. Never trust unverified tokens.
        """
        return jwt.decode(
            token,
            options={"verify_signature": False},
        )

    def _build_payload(
        self,
        user: User,
        token_type: TokenType,
        expires: datetime,
        issued_at: datetime,
        mfa_verified: bool,
        extra_claims: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build JWT payload dictionary."""
        payload = {
            "sub": str(user.id),
            "email": user.email,
            TOKEN_TYPE_CLAIM: token_type.value,
            "exp": expires,
            "iat": issued_at,
            "jti": secrets.token_urlsafe(16),
            "mfa_verified": mfa_verified,
        }

        if self._config.include_roles:
            payload["role"] = user.role

        if self._config.include_tenant and user.tenant_id:
            payload["tenant_id"] = str(user.tenant_id)

        if extra_claims:
            payload.update(extra_claims)

        return payload


def generate_secret_key(length: int = 64) -> str:
    """
    Generate a secure secret key for token signing.

    Args:
        length: Key length in bytes

    Returns:
        URL-safe base64 encoded secret key
    """
    return secrets.token_urlsafe(length)


__all__ = [
    "TokenManager",
    "TokenConfig",
    "TokenPayload",
    "TokenType",
    "TokenError",
    "TokenExpiredError",
    "TokenInvalidError",
    "TokenRevokedError",
    "generate_secret_key",
]
