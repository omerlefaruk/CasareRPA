"""
Rate limiting configuration for CasareRPA Orchestrator API.

Provides per-tenant rate limiting using slowapi with configurable limits
for different endpoint categories. Limits are applied per-tenant when
available, otherwise per-IP.

Rate Limit Categories:
- High: Health checks, metrics polling (200/min)
- Standard: Most CRUD operations (60/min)
- Low: Expensive operations like job submission, analytics (20/min)
- Auth: Login/refresh endpoints (5/min per IP to prevent brute force)
"""

import os
from collections.abc import Callable

from fastapi import Request
from loguru import logger
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse

from casare_rpa.infrastructure.orchestrator.api.responses import (
    ErrorCode,
    error_response,
)

# =============================================================================
# CONFIGURATION
# =============================================================================

# Rate limit defaults (can be overridden via environment)
RATE_LIMIT_HIGH = os.getenv("RATE_LIMIT_HIGH", "200/minute")
RATE_LIMIT_STANDARD = os.getenv("RATE_LIMIT_STANDARD", "60/minute")
RATE_LIMIT_LOW = os.getenv("RATE_LIMIT_LOW", "20/minute")
RATE_LIMIT_AUTH = os.getenv("RATE_LIMIT_AUTH", "5/minute")
RATE_LIMIT_PROGRESS = os.getenv("RATE_LIMIT_PROGRESS", "600/minute")

# Enable/disable rate limiting globally
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() in (
    "true",
    "1",
    "yes",
)


# =============================================================================
# KEY FUNCTIONS
# =============================================================================


def get_tenant_or_ip(request: Request) -> str:
    """
    Get rate limit key based on tenant ID or IP address.

    Priority:
    1. Tenant ID from JWT claims (if authenticated)
    2. Remote IP address (fallback)

    This ensures fair rate limiting per-tenant while still protecting
    against unauthenticated abuse.

    Args:
        request: FastAPI request object

    Returns:
        Rate limit key string (tenant:xxx or ip:xxx)
    """
    # Try to get tenant from request state (set by auth middleware)
    tenant_id = getattr(request.state, "tenant_id", None)
    if tenant_id:
        return f"tenant:{tenant_id}"

    # Try to get user from request state
    user = getattr(request.state, "user", None)
    if user and hasattr(user, "tenant_id") and user.tenant_id:
        return f"tenant:{user.tenant_id}"

    # Fallback to IP address
    return f"ip:{get_remote_address(request)}"


def get_user_or_ip(request: Request) -> str:
    """
    Get rate limit key based on user ID or IP address.

    Used for per-user rate limiting (stricter than per-tenant).

    Args:
        request: FastAPI request object

    Returns:
        Rate limit key string (user:xxx or ip:xxx)
    """
    user = getattr(request.state, "user", None)
    if user and hasattr(user, "user_id"):
        return f"user:{user.user_id}"

    return f"ip:{get_remote_address(request)}"


def get_ip_only(request: Request) -> str:
    """
    Get rate limit key based on IP address only.

    Used for auth endpoints to prevent brute force attacks
    regardless of tenant/user.

    Args:
        request: FastAPI request object

    Returns:
        Rate limit key string (ip:xxx)
    """
    return f"ip:{get_remote_address(request)}"


# =============================================================================
# LIMITER INSTANCE
# =============================================================================

# Create main limiter with tenant-based key function
limiter = Limiter(
    key_func=get_tenant_or_ip,
    enabled=RATE_LIMIT_ENABLED,
    default_limits=[RATE_LIMIT_STANDARD],
    headers_enabled=True,  # Add X-RateLimit-* headers
    strategy="fixed-window",  # Options: fixed-window, moving-window
)

# Create separate limiter for auth endpoints (always IP-based)
auth_limiter = Limiter(
    key_func=get_ip_only,
    enabled=RATE_LIMIT_ENABLED,
    default_limits=[RATE_LIMIT_AUTH],
    headers_enabled=True,
)


# =============================================================================
# RATE LIMIT DECORATORS
# =============================================================================


def limit_high(func: Callable) -> Callable:
    """
    Apply high rate limit (200/min) for frequently polled endpoints.

    Use for: Health checks, metrics polling, WebSocket upgrades.
    """
    return limiter.limit(RATE_LIMIT_HIGH)(func)


def limit_standard(func: Callable) -> Callable:
    """
    Apply standard rate limit (60/min) for typical CRUD operations.

    Use for: List/get/create/update operations.
    """
    return limiter.limit(RATE_LIMIT_STANDARD)(func)


def limit_low(func: Callable) -> Callable:
    """
    Apply low rate limit (20/min) for expensive operations.

    Use for: Job submission, analytics queries, bulk operations.
    """
    return limiter.limit(RATE_LIMIT_LOW)(func)


def limit_auth(func: Callable) -> Callable:
    """
    Apply auth rate limit (5/min per IP) for login/refresh.

    Use for: Login, token refresh, password reset.
    """
    return auth_limiter.limit(RATE_LIMIT_AUTH)(func)


def limit_progress(func: Callable) -> Callable:
    """
    Apply high rate limit for progress updates (600/min).

    Use for: Job progress updates from robots (frequent polling).
    """
    return limiter.limit(RATE_LIMIT_PROGRESS)(func)


def limit_custom(limit: str, key_func: Callable | None = None) -> Callable:
    """
    Apply custom rate limit.

    Args:
        limit: Rate limit string (e.g., "100/minute", "10/second")
        key_func: Optional custom key function

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        if key_func:
            custom_limiter = Limiter(
                key_func=key_func,
                enabled=RATE_LIMIT_ENABLED,
            )
            return custom_limiter.limit(limit)(func)
        return limiter.limit(limit)(func)

    return decorator


# =============================================================================
# EXCEPTION HANDLER
# =============================================================================


async def rate_limit_exceeded_handler(
    request: Request,
    exc: RateLimitExceeded,
) -> JSONResponse:
    """
    Custom handler for rate limit exceeded errors.

    Returns a structured error response with retry information.

    Args:
        request: FastAPI request object
        exc: RateLimitExceeded exception

    Returns:
        JSONResponse with 429 status and retry headers
    """
    # Get request ID from state or generate one
    request_id = getattr(request.state, "request_id", "unknown")

    # Parse retry-after from exception
    retry_after = getattr(exc, "retry_after", 60)

    logger.warning(
        f"Rate limit exceeded: path={request.url.path} key={exc.detail} retry_after={retry_after}s"
    )

    response_body = error_response(
        code=ErrorCode.RATE_LIMIT_EXCEEDED,
        message=f"Rate limit exceeded. Try again in {retry_after} seconds.",
        request_id=request_id,
        details={
            "limit": str(exc.detail) if hasattr(exc, "detail") else None,
            "retry_after_seconds": retry_after,
        },
    )

    return JSONResponse(
        status_code=429,
        content=response_body,
        headers={
            "Retry-After": str(retry_after),
            "X-RateLimit-Reset": str(retry_after),
        },
    )


# =============================================================================
# MIDDLEWARE SETUP
# =============================================================================


def setup_rate_limiting(app) -> None:
    """
    Configure rate limiting for a FastAPI application.

    Attaches the limiter to the app state and registers the
    rate limit exceeded exception handler.

    Args:
        app: FastAPI application instance
    """
    if not RATE_LIMIT_ENABLED:
        logger.info("Rate limiting disabled (RATE_LIMIT_ENABLED=false)")
        return

    # Attach limiter to app state
    app.state.limiter = limiter

    # Register exception handler
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

    logger.info(
        f"Rate limiting enabled: high={RATE_LIMIT_HIGH}, "
        f"standard={RATE_LIMIT_STANDARD}, low={RATE_LIMIT_LOW}, "
        f"auth={RATE_LIMIT_AUTH}"
    )


# =============================================================================
# RATE LIMIT INFO ENDPOINT
# =============================================================================


def get_rate_limit_info(request: Request) -> dict:
    """
    Get current rate limit information for a request.

    Useful for debugging and monitoring.

    Args:
        request: FastAPI request object

    Returns:
        Dict with rate limit key and configuration
    """
    return {
        "key": get_tenant_or_ip(request),
        "enabled": RATE_LIMIT_ENABLED,
        "limits": {
            "high": RATE_LIMIT_HIGH,
            "standard": RATE_LIMIT_STANDARD,
            "low": RATE_LIMIT_LOW,
            "auth": RATE_LIMIT_AUTH,
            "progress": RATE_LIMIT_PROGRESS,
        },
    }
