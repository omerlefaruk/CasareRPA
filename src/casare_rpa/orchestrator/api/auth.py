"""
Authentication and authorization dependencies for FastAPI.

Provides JWT token validation and role-based access control.
Currently stubbed - full implementation requires PR #33 infrastructure.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger


# HTTP Bearer token scheme
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
