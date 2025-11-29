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
from typing import Optional
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger


# HTTP Bearer token scheme (for JWT)
security = HTTPBearer(auto_error=False)


async def verify_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """
    Verify JWT token and return claims.

    Args:
        credentials: HTTP Bearer credentials from Authorization header

    Returns:
        dict: Token claims (user_id, roles, etc.)

    Raises:
        HTTPException: 401 if token invalid or missing

    TODO: Implement actual JWT validation when PR #33 merges.
    For now, allows unauthenticated access in development.
    """
    # Development mode: bypass authentication
    if credentials is None:
        logger.warning(
            "Authentication bypassed (no token provided) - implement JWT validation"
        )
        return {"user_id": "dev_user", "roles": ["admin"], "dev_mode": True}

    token = credentials.credentials

    # TODO: Implement JWT validation using PR #33's infrastructure
    # from casare_rpa.infrastructure.security.rbac import validate_jwt_token
    # try:
    #     claims = validate_jwt_token(token)
    #     return claims
    # except InvalidTokenError:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Invalid authentication token",
    #         headers={"WWW-Authenticate": "Bearer"},
    #     )

    logger.warning(
        f"Token validation not implemented - accepting token: {token[:20]}..."
    )
    return {"user_id": "authenticated_user", "roles": ["viewer"], "dev_mode": True}


async def require_role(required_role: str):
    """
    Dependency factory for role-based access control.

    Args:
        required_role: Required role (viewer, operator, admin)

    Returns:
        Dependency function that validates user has required role

    Example:
        @router.get("/admin-only", dependencies=[Depends(require_role("admin"))])
        async def admin_endpoint():
            ...
    """

    async def role_checker(claims: dict = Depends(verify_token)) -> dict:
        """Check if user has required role."""
        user_roles = claims.get("roles", [])

        if required_role not in user_roles and "admin" not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}",
            )

        return claims

    return role_checker


# Optional authentication dependency (doesn't fail if no token)
async def optional_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
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
