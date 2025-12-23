"""
Correlation ID middleware for distributed tracing.

Generates or extracts X-Correlation-ID header for request tracing
across robot ↔ orchestrator communication boundaries.

Usage:
    from middleware.correlation import CorrelationIdMiddleware, get_correlation_id

    # Add middleware to app
    app.add_middleware(CorrelationIdMiddleware)

    # Access correlation ID in endpoints
    @router.get("/example")
    async def example(request: Request):
        correlation_id = get_correlation_id(request)
        logger.info("Processing request", correlation_id=correlation_id)
"""

import uuid
from contextvars import ContextVar
from typing import Optional

from fastapi import Request
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Context variable for correlation ID (thread/async-safe)
_correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)

# Header names
CORRELATION_ID_HEADER = "X-Correlation-ID"
REQUEST_ID_HEADER = "X-Request-ID"


def generate_correlation_id() -> str:
    """Generate a new correlation ID with 'corr_' prefix."""
    return f"corr_{uuid.uuid4().hex[:16]}"


def get_correlation_id(request: Optional[Request] = None) -> Optional[str]:
    """
    Get the current correlation ID.

    Args:
        request: Optional FastAPI request (fallback to request.state)

    Returns:
        Correlation ID string or None
    """
    # Try context variable first (works in async context)
    cid = _correlation_id.get()
    if cid:
        return cid

    # Fallback to request.state
    if request is not None:
        return getattr(request.state, "correlation_id", None)

    return None


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID in the current context."""
    _correlation_id.set(correlation_id)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware to propagate correlation IDs across service boundaries.

    Behavior:
    1. If X-Correlation-ID header exists, use it (propagated from robot/upstream)
    2. Otherwise, generate a new correlation ID
    3. Store in request.state.correlation_id
    4. Bind to loguru context for structured logging
    5. Return in X-Correlation-ID response header

    This enables end-to-end request tracing:
    Robot → Orchestrator → Database → Response
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        # Extract or generate correlation ID
        correlation_id = request.headers.get(CORRELATION_ID_HEADER)

        if not correlation_id:
            # Check if we have a request ID we can derive from
            request_id = request.headers.get(REQUEST_ID_HEADER)
            if request_id:
                # Use request ID as correlation ID base
                correlation_id = f"corr_{request_id.replace('req_', '')}"
            else:
                correlation_id = generate_correlation_id()

        # Store in request state
        request.state.correlation_id = correlation_id

        # Set context variable for async access
        set_correlation_id(correlation_id)

        # Bind to loguru context for automatic inclusion in logs
        with logger.contextualize(correlation_id=correlation_id):
            # Log request start
            logger.debug(
                f"Request started: {request.method} {request.url.path}",
                method=request.method,
                path=request.url.path,
                client_ip=request.client.host if request.client else None,
            )

            # Process request
            response = await call_next(request)

            # Add correlation ID to response headers
            response.headers[CORRELATION_ID_HEADER] = correlation_id

            # Log request completion
            logger.debug(
                f"Request completed: {request.method} {request.url.path} -> {response.status_code}",
                status_code=response.status_code,
            )

        # Clear context variable
        _correlation_id.set(None)

        return response


<<<<<<< HEAD
def inject_correlation_header(
    headers: dict, correlation_id: Optional[str] = None
) -> dict:
=======
def inject_correlation_header(headers: dict, correlation_id: Optional[str] = None) -> dict:
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
    """
    Inject correlation ID into outgoing request headers.

    Use this when making HTTP calls to other services to propagate
    the correlation ID for distributed tracing.

    Args:
        headers: Existing headers dict
        correlation_id: Optional correlation ID (uses current context if not provided)

    Returns:
        Headers dict with X-Correlation-ID added

    Example:
        headers = {"Content-Type": "application/json"}
        headers = inject_correlation_header(headers)
        await session.post(url, headers=headers, json=data)
    """
    cid = correlation_id or _correlation_id.get()

    if cid:
        headers = dict(headers)  # Don't mutate original
        headers[CORRELATION_ID_HEADER] = cid

    return headers
