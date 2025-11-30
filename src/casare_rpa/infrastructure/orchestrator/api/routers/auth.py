"""
Authentication API endpoints.

Provides:
- POST /auth/login - Login with credentials, get tokens
- POST /auth/refresh - Refresh access token
- POST /auth/logout - Logout (optional token revocation)
- GET /auth/me - Get current user info
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from pydantic import BaseModel, Field

from casare_rpa.infrastructure.orchestrator.api.auth import (
    AuthenticatedUser,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    JWT_DEV_MODE,
)
import jwt


router = APIRouter()


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================


class LoginRequest(BaseModel):
    """Login credentials."""

    username: str = Field(..., min_length=1, description="Username or email")
    password: str = Field(..., min_length=1, description="Password")
    tenant_id: Optional[str] = Field(None, description="Optional tenant ID")


class TokenResponse(BaseModel):
    """Token response with access and refresh tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token expiry in seconds")


class RefreshRequest(BaseModel):
    """Token refresh request."""

    refresh_token: str = Field(..., description="Refresh token")


class UserInfoResponse(BaseModel):
    """Current user information."""

    user_id: str
    roles: list[str]
    tenant_id: Optional[str] = None
    dev_mode: bool = False


class LogoutResponse(BaseModel):
    """Logout response."""

    message: str = "Successfully logged out"


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest) -> TokenResponse:
    """
    Authenticate user and return JWT tokens.

    In production, this should validate against a user database.
    Currently supports dev mode for testing.

    Args:
        request: Login credentials

    Returns:
        Access and refresh tokens
    """
    # In production: validate against database
    # For now: dev mode allows any login
    if JWT_DEV_MODE:
        logger.info(f"Dev mode login for user: {request.username}")

        # Dev mode: accept any credentials, assign admin role
        access_token = create_access_token(
            user_id=request.username,
            roles=["admin", "developer", "operator", "viewer"],
            tenant_id=request.tenant_id,
        )
        refresh_token = create_refresh_token(
            user_id=request.username,
            tenant_id=request.tenant_id,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=3600,  # 1 hour
        )

    # Production: validate credentials against database
    # TODO: Implement actual user validation
    # user = await user_repository.validate_credentials(request.username, request.password)
    # if not user:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Invalid username or password",
    #     )

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Production authentication not yet implemented. Enable JWT_DEV_MODE=true for testing.",
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest) -> TokenResponse:
    """
    Refresh access token using refresh token.

    Args:
        request: Refresh token

    Returns:
        New access and refresh tokens
    """
    try:
        payload = decode_token(request.refresh_token)

        # Verify this is a refresh token
        if payload.type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type. Expected refresh token.",
            )

        # In production: check if refresh token is revoked
        # await token_blacklist.check(request.refresh_token)

        # Generate new tokens
        # In production: fetch user roles from database
        roles = (
            ["admin", "developer", "operator", "viewer"] if JWT_DEV_MODE else ["viewer"]
        )

        access_token = create_access_token(
            user_id=payload.sub,
            roles=roles,
            tenant_id=payload.tenant_id,
        )
        refresh_token = create_refresh_token(
            user_id=payload.sub,
            tenant_id=payload.tenant_id,
        )

        logger.debug(f"Token refreshed for user: {payload.sub}")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=3600,
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired. Please login again.",
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid refresh token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    user: AuthenticatedUser = Depends(get_current_user),
) -> LogoutResponse:
    """
    Logout user (optionally revoke tokens).

    In a full implementation, this would:
    1. Add tokens to a blacklist
    2. Clear server-side sessions
    3. Emit audit log

    Args:
        user: Current authenticated user

    Returns:
        Logout confirmation
    """
    logger.info(f"User logged out: {user.user_id}")

    # In production: revoke tokens
    # await token_blacklist.add(access_token)
    # await token_blacklist.add(refresh_token)

    return LogoutResponse()


@router.get("/me", response_model=UserInfoResponse)
async def get_me(
    user: AuthenticatedUser = Depends(get_current_user),
) -> UserInfoResponse:
    """
    Get current user information.

    Args:
        user: Current authenticated user from JWT

    Returns:
        User info including roles and tenant
    """
    return UserInfoResponse(
        user_id=user.user_id,
        roles=user.roles,
        tenant_id=user.tenant_id,
        dev_mode=user.dev_mode,
    )
