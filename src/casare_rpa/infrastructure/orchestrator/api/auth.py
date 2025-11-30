"""
Authentication and authorization dependencies for FastAPI.

Provides:
1. JWT token validation and role-based access control (for web dashboard)
2. Robot API token authentication (for robot-to-orchestrator connections)

JWT auth is for browser/dashboard users.
Robot auth is for automated robots connecting over internet.
"""

import os
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger
from pydantic import BaseModel


# =============================================================================
# JWT CONFIGURATION
# =============================================================================

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60")
)
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
JWT_DEV_MODE = os.getenv("JWT_DEV_MODE", "true").lower() in ("true", "1", "yes")


# =============================================================================
# AUTH MODELS
# =============================================================================


class TokenPayload(BaseModel):
    """JWT token payload structure."""

    sub: str  # user_id
    roles: list[str] = []
    tenant_id: Optional[str] = None
    exp: Optional[datetime] = None
    iat: Optional[datetime] = None
    type: str = "access"  # access or refresh


class AuthenticatedUser(BaseModel):
    """Represents an authenticated user from JWT claims."""

    user_id: str
    roles: list[str]
    tenant_id: Optional[str] = None
    dev_mode: bool = False

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return "admin" in self.roles

    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self.roles or "admin" in self.roles


# HTTP Bearer token scheme (for JWT)
security = HTTPBearer(auto_error=False)


def create_access_token(
    user_id: str,
    roles: list[str],
    tenant_id: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        user_id: User identifier
        roles: List of role names
        tenant_id: Optional tenant identifier
        expires_delta: Custom expiration time

    Returns:
        Encoded JWT token string
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    payload = {
        "sub": user_id,
        "roles": roles,
        "tenant_id": tenant_id,
        "exp": expire,
        "iat": now,
        "type": "access",
    }

    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(
    user_id: str,
    tenant_id: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT refresh token.

    Args:
        user_id: User identifier
        tenant_id: Optional tenant identifier
        expires_delta: Custom expiration time

    Returns:
        Encoded JWT refresh token string
    """
    if expires_delta is None:
        expires_delta = timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "exp": expire,
        "iat": now,
        "type": "refresh",
    }

    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> TokenPayload:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string

    Returns:
        TokenPayload with decoded claims

    Raises:
        jwt.ExpiredSignatureError: If token is expired
        jwt.InvalidTokenError: If token is invalid
    """
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    return TokenPayload(**payload)


async def verify_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> AuthenticatedUser:
    """
    Verify JWT token and return authenticated user.

    Args:
        credentials: HTTP Bearer credentials from Authorization header

    Returns:
        AuthenticatedUser with user_id, roles, and tenant_id

    Raises:
        HTTPException: 401 if token invalid or missing
    """
    # Development mode: bypass authentication if no token provided
    if credentials is None:
        if JWT_DEV_MODE:
            logger.debug("JWT dev mode: allowing unauthenticated access as admin")
            return AuthenticatedUser(
                user_id="dev_user",
                roles=["admin"],
                tenant_id=None,
                dev_mode=True,
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        payload = decode_token(token)

        # Verify this is an access token, not a refresh token
        if payload.type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Use access token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return AuthenticatedUser(
            user_id=payload.sub,
            roles=payload.roles,
            tenant_id=payload.tenant_id,
            dev_mode=False,
        )

    except jwt.ExpiredSignatureError:
        logger.warning("Expired JWT token attempted")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_role(required_role: str):
    """
    Dependency factory for role-based access control.

    Args:
        required_role: Required role (viewer, operator, admin, developer)

    Returns:
        Dependency function that validates user has required role

    Example:
        @router.get("/admin-only", dependencies=[Depends(require_role("admin"))])
        async def admin_endpoint():
            ...
    """

    async def role_checker(
        user: AuthenticatedUser = Depends(verify_token),
    ) -> AuthenticatedUser:
        """Check if user has required role."""
        if not user.has_role(required_role):
            logger.warning(
                f"Access denied: user={user.user_id} required={required_role} "
                f"has={user.roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}",
            )

        return user

    return role_checker


# Convenience dependency for getting current user
async def get_current_user(
    user: AuthenticatedUser = Depends(verify_token),
) -> AuthenticatedUser:
    """
    Get the current authenticated user.

    This is an alias for verify_token for clearer semantics in endpoints.

    Example:
        @router.get("/me")
        async def get_profile(user: AuthenticatedUser = Depends(get_current_user)):
            return {"user_id": user.user_id, "roles": user.roles}
    """
    return user


# Convenience dependencies for common roles
require_admin = require_role("admin")
require_developer = require_role("developer")
require_operator = require_role("operator")
require_viewer = require_role("viewer")


# Optional authentication dependency (doesn't fail if no token)
async def optional_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[AuthenticatedUser]:
    """
    Optional authentication - returns None if no token provided.

    Useful for endpoints that provide different data based on authentication status.
    """
    if credentials is None:
        return None

    try:
        return await verify_token(credentials)
    except HTTPException:
        return None


# =============================================================================
# Robot API Token Authentication (for robot-to-orchestrator connections)
# =============================================================================


class RobotAuthenticator:
    """
    Validates robot API tokens against configured hashes.

    Tokens are SHA-256 hashed for secure storage. Supports loading
    from environment variables or database.

    For internet-connected robots, use X-Api-Token header authentication
    instead of JWT (simpler for automated clients).
    """

    def __init__(self):
        self._token_hashes = self._load_token_hashes()
        self._auth_enabled = os.getenv("ROBOT_AUTH_ENABLED", "false").lower() in (
            "true",
            "1",
            "yes",
        )

    def _load_token_hashes(self) -> dict[str, str]:
        """
        Load robot token hashes from environment.

        Format: ROBOT_TOKENS=robot-001:hash1,robot-002:hash2

        Returns:
            Dict mapping token_hash → robot_id
        """
        token_env = os.getenv("ROBOT_TOKENS", "")

        if not token_env:
            logger.warning(
                "ROBOT_TOKENS not configured. Set ROBOT_TOKENS=robot-001:hash1,robot-002:hash2 "
                "or use tools/generate_robot_token.py to create tokens."
            )
            return {}

        token_map = {}
        for entry in token_env.split(","):
            entry = entry.strip()
            if ":" not in entry:
                logger.warning(f"Invalid ROBOT_TOKENS entry (missing ':'): {entry}")
                continue

            robot_id, token_hash = entry.split(":", 1)
            token_map[token_hash.strip()] = robot_id.strip()

        logger.info(f"Loaded {len(token_map)} robot authentication tokens")
        return token_map

    def verify_token(self, token: str) -> Optional[str]:
        """
        Verify robot API token and return robot ID if valid.

        Args:
            token: Raw API token from X-Api-Token header

        Returns:
            robot_id if token is valid, None otherwise
        """
        if not token:
            return None

        # Hash token and check against configured hashes
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return self._token_hashes.get(token_hash)

    @property
    def is_enabled(self) -> bool:
        """Check if robot authentication is enabled."""
        return self._auth_enabled


# Global authenticator instance
_robot_authenticator: Optional[RobotAuthenticator] = None


def get_robot_authenticator() -> RobotAuthenticator:
    """Get or create the global robot authenticator instance."""
    global _robot_authenticator
    if _robot_authenticator is None:
        _robot_authenticator = RobotAuthenticator()
    return _robot_authenticator


async def verify_robot_token(x_api_token: str = Header(...)) -> str:
    """
    FastAPI dependency to verify robot API token.

    Extracts token from X-Api-Token header and validates against
    configured robot tokens.

    Args:
        x_api_token: Token from X-Api-Token HTTP header

    Returns:
        robot_id if authentication successful

    Raises:
        HTTPException 401 if token is invalid or missing

    Example:
        @router.post("/jobs/claim", dependencies=[Depends(verify_robot_token)])
        async def claim_job():
            # Only authenticated robots can reach here
            pass

    Environment:
        ROBOT_AUTH_ENABLED=true  # Enable robot authentication
        ROBOT_TOKENS=robot-001:hash1,robot-002:hash2
    """
    authenticator = get_robot_authenticator()

    # If auth not enabled, allow all (development mode)
    if not authenticator.is_enabled:
        logger.debug("Robot authentication disabled (ROBOT_AUTH_ENABLED=false)")
        return "dev_robot"

    robot_id = authenticator.verify_token(x_api_token)

    if not robot_id:
        logger.warning(
            f"Failed robot authentication attempt with token: {x_api_token[:8]}..."
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.debug(f"Authenticated robot: {robot_id}")
    return robot_id


async def optional_robot_token(
    x_api_token: Optional[str] = Header(None),
) -> Optional[str]:
    """
    Optional robot authentication dependency for endpoints that support both
    authenticated and anonymous access.

    Args:
        x_api_token: Optional token from X-Api-Token header

    Returns:
        robot_id if token provided and valid, None otherwise
    """
    if not x_api_token:
        return None

    authenticator = get_robot_authenticator()

    if not authenticator.is_enabled:
        return None

    return authenticator.verify_token(x_api_token)
