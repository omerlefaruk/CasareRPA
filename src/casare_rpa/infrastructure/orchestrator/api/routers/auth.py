"""
Authentication API endpoints.

Provides:
- POST /auth/login - Login with credentials, get tokens
- POST /auth/refresh - Refresh access token
- POST /auth/logout - Logout (optional token revocation)
- GET /auth/me - Get current user info

Security:
- Rate limiting on login/refresh to prevent brute force attacks
- IP-based tracking with configurable limits
"""

import time
from collections import defaultdict

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from loguru import logger
from pydantic import BaseModel, Field

from casare_rpa.infrastructure.orchestrator.api.auth import (
    JWT_DEV_MODE,
    AuthenticatedUser,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
)

router = APIRouter()


# =============================================================================
# RATE LIMITING
# =============================================================================

# Rate limit configuration
LOGIN_RATE_LIMIT_MAX_ATTEMPTS = 5  # Max attempts per window
LOGIN_RATE_LIMIT_WINDOW_SECONDS = 300  # 5 minute window
LOGIN_RATE_LIMIT_LOCKOUT_SECONDS = 900  # 15 minute lockout after exceeding

# IP-based rate limit tracking
# Structure: {ip: (attempt_count, window_start_time, lockout_until)}
_login_attempts: dict[str, tuple[int, float, float | None]] = defaultdict(lambda: (0, 0.0, None))


def _get_client_ip(request: Request) -> str:
    """Extract client IP from request, handling proxies."""
    # Check X-Forwarded-For header (from reverse proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP (original client)
        return forwarded_for.split(",")[0].strip()

    # Check X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Fallback to direct client IP
    return request.client.host if request.client else "unknown"


def _check_rate_limit(ip: str) -> tuple[bool, int | None]:
    """
    Check if IP is rate limited.

    Args:
        ip: Client IP address

    Returns:
        Tuple of (is_allowed, retry_after_seconds)
    """
    now = time.time()
    attempts, window_start, lockout_until = _login_attempts[ip]

    # Check if in lockout
    if lockout_until and now < lockout_until:
        retry_after = int(lockout_until - now)
        logger.warning(f"Rate limit lockout for {ip}: {retry_after}s remaining")
        return False, retry_after

    # Check if window has expired
    if now - window_start > LOGIN_RATE_LIMIT_WINDOW_SECONDS:
        # Reset the window
        _login_attempts[ip] = (0, now, None)
        return True, None

    # Check if attempts exceeded
    if attempts >= LOGIN_RATE_LIMIT_MAX_ATTEMPTS:
        # Enter lockout
        lockout_until = now + LOGIN_RATE_LIMIT_LOCKOUT_SECONDS
        _login_attempts[ip] = (attempts, window_start, lockout_until)
        logger.warning(
            f"Rate limit exceeded for {ip}: entering {LOGIN_RATE_LIMIT_LOCKOUT_SECONDS}s lockout"
        )
        return False, LOGIN_RATE_LIMIT_LOCKOUT_SECONDS

    return True, None


def _record_login_attempt(ip: str, success: bool) -> None:
    """
    Record a login attempt for rate limiting.

    Args:
        ip: Client IP address
        success: Whether the login was successful
    """
    now = time.time()
    attempts, window_start, lockout_until = _login_attempts[ip]

    # If successful login, reset attempts
    if success:
        _login_attempts[ip] = (0, now, None)
        return

    # If window expired, start new window
    if now - window_start > LOGIN_RATE_LIMIT_WINDOW_SECONDS:
        _login_attempts[ip] = (1, now, None)
    else:
        # Increment attempts
        _login_attempts[ip] = (attempts + 1, window_start, lockout_until)

    logger.debug(f"Login attempt recorded for {ip}: {_login_attempts[ip][0]} attempts")


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================


class LoginRequest(BaseModel):
    """Login credentials."""

    username: str = Field(..., min_length=1, description="Username or email")
    password: str = Field(..., min_length=1, description="Password")
    tenant_id: str | None = Field(None, description="Optional tenant ID")


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
    tenant_id: str | None = None
    dev_mode: bool = False


class LogoutResponse(BaseModel):
    """Logout response."""

    message: str = "Successfully logged out"


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, http_request: Request) -> TokenResponse:
    """
    Authenticate user and return JWT tokens.

    In production, this should validate against a user database.
    Currently supports dev mode for testing.

    Rate limited: 5 attempts per 5 minutes, then 15 minute lockout.

    Args:
        request: Login credentials
        http_request: FastAPI request for IP extraction

    Returns:
        Access and refresh tokens

    Raises:
        HTTPException 429: Too many login attempts
        HTTPException 401: Invalid credentials
        HTTPException 501: Production auth not implemented
    """
    # Check rate limit
    client_ip = _get_client_ip(http_request)
    is_allowed, retry_after = _check_rate_limit(client_ip)

    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )

    # In production: validate against database
    # For now: dev mode allows any login
    if JWT_DEV_MODE:
        logger.info(f"Dev mode login for user: {request.username} from {client_ip}")

        # Record successful login (resets rate limit)
        _record_login_attempt(client_ip, success=True)

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
    try:
        from casare_rpa.infrastructure.persistence.repositories import UserRepository

        user_repo = UserRepository()
        user = await user_repo.validate_credentials(request.username, request.password)

        if not user:
            _record_login_attempt(client_ip, success=False)
            logger.warning(f"Failed login attempt for user: {request.username} from {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

        # Check if MFA is required (MFA enforcement deferred to future release)
        if user.get("mfa_enabled"):
            logger.info(f"MFA enabled for user {user['user_id']} - enforcement pending")

        # Record successful login
        _record_login_attempt(client_ip, success=True)

        # Create tokens with actual user roles
        access_token = create_access_token(
            user_id=user["user_id"],
            roles=user["roles"],
            tenant_id=user.get("tenant_id") or request.tenant_id,
        )
        refresh_token = create_refresh_token(
            user_id=user["user_id"],
            tenant_id=user.get("tenant_id") or request.tenant_id,
        )

        logger.info(f"User logged in: {user['user_id']} from {client_ip}")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=3600,
        )

    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except ImportError as e:
        logger.error(f"UserRepository import failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service temporarily unavailable. Missing dependencies.",
        )
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        _record_login_attempt(client_ip, success=False)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error. Please try again later.",
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest, http_request: Request) -> TokenResponse:
    """
    Refresh access token using refresh token.

    Rate limited to prevent token refresh abuse.

    Args:
        request: Refresh token
        http_request: FastAPI request for IP extraction

    Returns:
        New access and refresh tokens

    Raises:
        HTTPException 429: Too many refresh attempts
    """
    # Check rate limit (shared with login)
    client_ip = _get_client_ip(http_request)
    is_allowed, retry_after = _check_rate_limit(client_ip)

    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many requests. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )

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
        roles = ["admin", "developer", "operator", "viewer"] if JWT_DEV_MODE else ["viewer"]

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
