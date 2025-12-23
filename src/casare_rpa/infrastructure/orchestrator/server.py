import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

# Core Routers
from casare_rpa.infrastructure.orchestrator import websocket_handlers
from casare_rpa.infrastructure.orchestrator.api.rate_limit import setup_rate_limiting
from casare_rpa.infrastructure.orchestrator.api.responses import ErrorCode, error_response

# Monitoring Routers
from casare_rpa.infrastructure.orchestrator.api.routers import (
    analytics,
    auth,
    dlq,
    health,
    jobs,
    metrics,
    robot_api_keys,
    robots,
    schedules,
    websockets,
    workflows,
)
from casare_rpa.infrastructure.orchestrator.server_lifecycle import (
    get_config,
    lifespan,
)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Add unique request ID to all requests/responses."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:16]}"
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


from fastapi import HTTPException


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", "unknown")
    details = {
        "validation_errors": [
            {"field": ".".join(str(loc) for loc in err["loc"]), "message": err["msg"]}
            for err in exc.errors()
        ]
    }
    return JSONResponse(
        status_code=422,
        content=error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message="Request validation failed",
            request_id=request_id,
            details=details,
        ),
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, "request_id", "unknown")
    status_to_code = {
        401: ErrorCode.AUTH_TOKEN_INVALID,
        403: ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
        404: ErrorCode.RESOURCE_NOT_FOUND,
        409: ErrorCode.RESOURCE_CONFLICT,
        429: ErrorCode.RATE_LIMIT_EXCEEDED,
        503: ErrorCode.SERVICE_UNAVAILABLE,
    }
    error_code = status_to_code.get(exc.status_code, ErrorCode.INTERNAL_ERROR)
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(code=error_code, message=exc.detail, request_id=request_id),
        headers=exc.headers,
    )


async def generic_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.exception(f"Unhandled exception: {request.url.path} - {exc}")
    return JSONResponse(
        status_code=500,
        content=error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message="An unexpected error occurred",
            request_id=request_id,
        ),
    )


def create_app() -> FastAPI:
    """Create the unified CasareRPA Orchestrator FastAPI application."""
    config = get_config()

    app = FastAPI(
        title="CasareRPA Orchestrator",
        description="Unified fleet management, job orchestration, and monitoring analytics",
        version=config.api_version,
        lifespan=lifespan,
    )

    # 1. Middleware
    origins = config.cors_origins or ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True if "*" not in origins else False,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
    )
    app.add_middleware(RequestIdMiddleware)

    if config.rate_limit_enabled:
        setup_rate_limiting(app)

    # 2. Exception Handlers
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # 3. Core Fleet Routers
    app.include_router(health.router)
    app.include_router(websocket_handlers.router, prefix="/ws", tags=["Robot WebSocket"])

    # 4. Monitoring Dashboard Routers (v1)
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
    app.include_router(metrics.router, prefix="/api/v1", tags=["Metrics"])
    app.include_router(robots.router, prefix="/api/v1", tags=["Robots Manager"])
    app.include_router(robot_api_keys.router, prefix="/api/v1", tags=["API Keys"])
    app.include_router(jobs.router, prefix="/api/v1", tags=["Jobs Manager"])
    app.include_router(workflows.router, prefix="/api/v1", tags=["Workflows"])
    app.include_router(schedules.router, prefix="/api/v1", tags=["Schedules"])
    app.include_router(analytics.router, prefix="/api/v1", tags=["Analytics"])
    app.include_router(dlq.router, prefix="/api/v1", tags=["DLQ"])
    app.include_router(websockets.router, prefix="/ws/monitoring", tags=["Dashboard WebSocket"])

    return app


app = create_app()


def main() -> None:
    """Run the orchestrator server."""
    import uvicorn

    config = get_config()
    logger.info(f"Starting unified orchestrator on {config.host}:{config.port}")
    uvicorn.run(
        "casare_rpa.infrastructure.orchestrator.server:app",
        host=config.host,
        port=config.port,
        workers=config.workers,
    )


if __name__ == "__main__":
    main()
