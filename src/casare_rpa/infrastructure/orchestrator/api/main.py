"""
FastAPI application for CasareRPA monitoring dashboard.

Provides REST and WebSocket endpoints for fleet monitoring,
job execution tracking, and analytics.

Middleware Order (applied bottom-to-top, executed top-to-bottom):
1. CORS - Cross-origin resource sharing
2. Request ID - Add tracking ID to all requests
3. Rate Limit - Per-tenant/IP rate limiting
4. Auth State - Populate request.state with user info
"""

import os
import time
import uuid
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
# Try project root first, then current directory
project_root = Path(__file__).resolve().parents[5]  # Navigate up to CasareRPA root
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"[API] Loaded .env from: {env_path}")
else:
    load_dotenv()  # Fallback to current directory
    print("[API] Using .env from current directory (fallback)")
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from loguru import logger
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware

from casare_rpa.infrastructure.events import (
    MonitoringEventType,
    get_monitoring_event_bus,
)
from casare_rpa.infrastructure.orchestrator.api.dependencies import (
    DatabasePoolManager,
    get_pool_manager,
)
from casare_rpa.infrastructure.orchestrator.api.rate_limit import (
    limiter,
    setup_rate_limiting,
)
from casare_rpa.infrastructure.orchestrator.api.responses import (
    ErrorCode,
    HealthResponse,
    ReadyResponse,
    error_response,
)
from casare_rpa.infrastructure.orchestrator.api.routers import (
    auth,
    jobs,
    metrics,
    robots,
    schedules,
    websockets,
    workflows,
)
from casare_rpa.infrastructure.orchestrator.api.routers.websockets import (
    on_job_status_changed,
    on_queue_depth_changed,
    on_robot_heartbeat,
)

# API version and startup time for health checks
API_VERSION = "1.1.0"
_startup_time: float = 0.0


async def _init_database_pool(app: FastAPI) -> Optional[DatabasePoolManager]:
    """
    Initialize database connection pool during startup.

    Attempts to create the pool but allows app to start even if database
    is unavailable (degraded mode).

    Args:
        app: FastAPI application instance

    Returns:
        DatabasePoolManager if successful, None otherwise
    """
    # Check if database is enabled
    db_enabled = os.getenv("DB_ENABLED", "true").lower() in ("true", "1", "yes")

    if not db_enabled:
        logger.info("Database disabled via DB_ENABLED=false")
        app.state.db_pool = None
        app.state.db_manager = None
        return None

    pool_manager = get_pool_manager()

    try:
        pool = await pool_manager.create_pool()
        app.state.db_pool = pool
        app.state.db_manager = pool_manager
        logger.info("Database pool initialized and stored in app.state")
        return pool_manager

    except RuntimeError as e:
        # Pool creation failed after retries
        logger.error(
            f"Database initialization failed: {e}. "
            "API will start in degraded mode without database access."
        )
        app.state.db_pool = None
        app.state.db_manager = pool_manager
        return None


async def _shutdown_database_pool(app: FastAPI) -> None:
    """
    Gracefully shutdown database connection pool.

    Args:
        app: FastAPI application instance
    """
    pool_manager: Optional[DatabasePoolManager] = getattr(app.state, "db_manager", None)

    if pool_manager is not None:
        await pool_manager.close()
        app.state.db_pool = None
        app.state.db_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app initialization and cleanup."""
    global _startup_time
    _startup_time = time.time()

    logger.info(f"Starting CasareRPA Monitoring API v{API_VERSION}")

    # Initialize database connection pool
    await _init_database_pool(app)

    # Set database pool for routers that need direct DB access
    if app.state.db_pool:
        from .routers.workflows import set_db_pool as set_workflows_db_pool
        from .routers.schedules import set_db_pool as set_schedules_db_pool
        from .routers.robots import set_db_pool as set_robots_db_pool
        from .routers.jobs import set_db_pool as set_jobs_db_pool

        set_workflows_db_pool(app.state.db_pool)
        set_schedules_db_pool(app.state.db_pool)
        set_robots_db_pool(app.state.db_pool)
        set_jobs_db_pool(app.state.db_pool)
        logger.info(
            "Database pool set for workflows, schedules, robots, and jobs routers"
        )

    # Initialize APScheduler for schedule management
    scheduler_initialized = False
    try:
        from casare_rpa.infrastructure.orchestrator.scheduling import (
            init_global_scheduler,
            shutdown_global_scheduler,
        )
        from .routers.schedules import _execute_scheduled_workflow

        await init_global_scheduler(
            on_schedule_trigger=_execute_scheduled_workflow,
            default_timezone="UTC",
        )
        scheduler_initialized = True
        logger.info("APScheduler initialized for schedule management")
    except ImportError as e:
        logger.warning(
            f"APScheduler not available, schedules will use in-memory only: {e}"
        )
    except Exception as e:
        logger.error(f"Failed to initialize APScheduler: {e}")

    # Store scheduler state in app.state for access in shutdown
    app.state.scheduler_initialized = scheduler_initialized

    # Initialize metrics collectors (get_rpa_metrics initializes the singleton)
    from casare_rpa.infrastructure.observability.metrics import (
        get_metrics_collector as get_rpa_metrics,
    )
    from casare_rpa.infrastructure.analytics.metrics_aggregator import MetricsAggregator

    rpa_metrics = get_rpa_metrics()
    analytics = MetricsAggregator.get_instance()
    logger.info(
        f"Metrics collectors initialized: rpa={rpa_metrics}, analytics={analytics}"
    )

    # Subscribe WebSocket handlers to monitoring events
    event_bus = get_monitoring_event_bus()
    event_bus.subscribe(MonitoringEventType.JOB_STATUS_CHANGED, on_job_status_changed)
    event_bus.subscribe(MonitoringEventType.ROBOT_HEARTBEAT, on_robot_heartbeat)
    event_bus.subscribe(MonitoringEventType.QUEUE_DEPTH_CHANGED, on_queue_depth_changed)
    logger.info("WebSocket event handlers subscribed to monitoring event bus")

    yield

    # Cleanup: unsubscribe handlers
    event_bus.unsubscribe(MonitoringEventType.JOB_STATUS_CHANGED, on_job_status_changed)
    event_bus.unsubscribe(MonitoringEventType.ROBOT_HEARTBEAT, on_robot_heartbeat)
    event_bus.unsubscribe(
        MonitoringEventType.QUEUE_DEPTH_CHANGED, on_queue_depth_changed
    )

    # Shutdown APScheduler
    if getattr(app.state, "scheduler_initialized", False):
        try:
            from casare_rpa.infrastructure.orchestrator.scheduling import (
                shutdown_global_scheduler,
            )

            await shutdown_global_scheduler()
            logger.info("APScheduler shutdown complete")
        except Exception as e:
            logger.error(f"Error shutting down APScheduler: {e}")

    # Shutdown database pool
    await _shutdown_database_pool(app)

    logger.info("Shutting down CasareRPA Monitoring API")


# =============================================================================
# REQUEST ID MIDDLEWARE
# =============================================================================


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add unique request ID to all requests.

    The request ID is:
    1. Taken from X-Request-ID header if provided (for distributed tracing)
    2. Generated as UUID if not provided
    3. Stored in request.state.request_id
    4. Returned in X-Request-ID response header
    """

    async def dispatch(self, request: Request, call_next):
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = f"req_{uuid.uuid4().hex[:16]}"

        # Store in request state for use in endpoints
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response


# =============================================================================
# EXCEPTION HANDLERS
# =============================================================================


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Handle Pydantic validation errors with structured response.

    Converts FastAPI validation errors to our unified error format.
    """
    request_id = getattr(request.state, "request_id", "unknown")

    # Extract validation error details
    errors = exc.errors()
    details = {
        "validation_errors": [
            {
                "field": ".".join(str(loc) for loc in err["loc"]),
                "message": err["msg"],
                "type": err["type"],
            }
            for err in errors
        ]
    }

    logger.warning(f"Validation error: {request.url.path} - {errors}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message="Request validation failed",
            request_id=request_id,
            details=details,
        ),
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Catch-all handler for unhandled exceptions.

    Logs the full error and returns a sanitized response.
    """
    request_id = getattr(request.state, "request_id", "unknown")

    logger.exception(f"Unhandled exception: {request.url.path} - {exc}")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message="An unexpected error occurred",
            request_id=request_id,
            details={"error_type": type(exc).__name__} if os.getenv("DEBUG") else None,
        ),
    )


async def http_exception_handler(
    request: Request,
    exc,
) -> JSONResponse:
    """
    Handle HTTPException with structured response.
    """
    from fastapi import HTTPException

    request_id = getattr(request.state, "request_id", "unknown")

    # Map status codes to error codes
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
        content=error_response(
            code=error_code,
            message=exc.detail,
            request_id=request_id,
        ),
        headers=getattr(exc, "headers", None),
    )


# =============================================================================
# APPLICATION SETUP
# =============================================================================

# Create FastAPI application
app = FastAPI(
    title="CasareRPA Monitoring API",
    description="Multi-robot fleet monitoring and analytics API for CasareRPA orchestrator",
    version=API_VERSION,
    lifespan=lifespan,
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
)

# =============================================================================
# MIDDLEWARE SETUP (order matters - applied bottom-to-top)
# =============================================================================

# Build CORS origins list
_cors_origins = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:8000",  # Local production
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
]

# Add Cloudflare Tunnel URLs if configured
_api_url = os.getenv("CASARE_API_URL", "")
if _api_url and _api_url not in _cors_origins:
    _cors_origins.append(_api_url)

# Add custom CORS origins from environment (comma-separated)
_custom_origins = os.getenv("CORS_ORIGINS", "")
if _custom_origins:
    _cors_origins.extend([o.strip() for o in _custom_origins.split(",") if o.strip()])

# 1. CORS middleware (outermost - runs first on request, last on response)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Api-Key",  # Robot authentication
        "X-Request-ID",  # Distributed tracing
        "X-Tenant-ID",  # Tenant context
    ],
    expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
)

# 2. Request ID middleware (runs second)
app.add_middleware(RequestIdMiddleware)

# 3. Rate limiting (setup in separate module)
setup_rate_limiting(app)

# =============================================================================
# EXCEPTION HANDLERS
# =============================================================================

from fastapi import HTTPException

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# =============================================================================
# ROUTERS
# =============================================================================

# Include routers with /api/v1 prefix
app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["Authentication"],
)
app.include_router(
    metrics.router,
    prefix="/api/v1",
    tags=["Metrics"],
)
app.include_router(
    robots.router,
    prefix="/api/v1",
    tags=["Robots"],
)
app.include_router(
    jobs.router,
    prefix="/api/v1",
    tags=["Jobs"],
)
app.include_router(
    workflows.router,
    prefix="/api/v1",
    tags=["Workflows"],
)
app.include_router(
    schedules.router,
    prefix="/api/v1",
    tags=["Schedules"],
)

# WebSocket router (no version prefix for WS)
app.include_router(
    websockets.router,
    prefix="/ws",
    tags=["WebSockets"],
)


# =============================================================================
# HEALTH CHECK ENDPOINTS
# =============================================================================


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Basic health check",
)
async def health_check():
    """
    Basic health check endpoint for load balancers.

    Returns healthy status if API is running. Does not check dependencies.
    For detailed health info including database status, use /health/detailed.
    """
    db_manager: Optional[DatabasePoolManager] = getattr(app.state, "db_manager", None)
    scheduler_ok = getattr(app.state, "scheduler_initialized", False)

    uptime = time.time() - _startup_time if _startup_time > 0 else 0

    return HealthResponse(
        status="healthy",
        version=API_VERSION,
        database="connected" if db_manager and db_manager._pool else "disconnected",
        scheduler="running" if scheduler_ok else "not_initialized",
        uptime_seconds=round(uptime, 2),
    )


@app.get(
    "/health/detailed",
    tags=["Health"],
    summary="Detailed health check with dependency status",
)
async def detailed_health_check():
    """
    Detailed health check including all dependencies.

    Returns status of:
    - API service
    - Database connection pool
    - Database connectivity
    - Scheduler status

    Response codes:
    - 200: All systems healthy
    - 200 with status=degraded: API running but some dependencies unavailable
    """
    db_manager: Optional[DatabasePoolManager] = getattr(app.state, "db_manager", None)
    scheduler_ok = getattr(app.state, "scheduler_initialized", False)

    uptime = time.time() - _startup_time if _startup_time > 0 else 0

    # Check database health
    if db_manager is not None:
        db_health = await db_manager.check_health()
    else:
        db_health = {
            "healthy": False,
            "error": "Database disabled or not configured",
            "pool_size": 0,
            "pool_free": 0,
        }

    # Determine overall status
    all_healthy = db_health.get("healthy", False) and scheduler_ok

    return {
        "status": "healthy" if all_healthy else "degraded",
        "version": API_VERSION,
        "uptime_seconds": round(uptime, 2),
        "dependencies": {
            "database": db_health,
            "scheduler": {
                "healthy": scheduler_ok,
                "status": "running" if scheduler_ok else "not_initialized",
            },
        },
    }


@app.get(
    "/health/ready",
    response_model=ReadyResponse,
    tags=["Health"],
    summary="Kubernetes readiness probe",
)
async def readiness_check():
    """
    Kubernetes-style readiness probe.

    Returns 200 only if all critical dependencies are available.
    Use this for load balancer health checks that should remove
    unhealthy instances from rotation.
    """
    db_manager: Optional[DatabasePoolManager] = getattr(app.state, "db_manager", None)

    checks = {}

    # Check database
    if db_manager is None:
        checks["database"] = False
    else:
        db_health = await db_manager.check_health()
        checks["database"] = db_health.get("healthy", False)

    # Check scheduler
    checks["scheduler"] = getattr(app.state, "scheduler_initialized", False)

    # Ready if all checks pass
    ready = all(checks.values())

    return ReadyResponse(ready=ready, checks=checks)


@app.get(
    "/health/live",
    tags=["Health"],
    summary="Kubernetes liveness probe",
)
async def liveness_check():
    """
    Kubernetes-style liveness probe.

    Returns 200 if the process is alive and can handle requests.
    Does not check dependencies - use /health/ready for that.
    """
    return {"alive": True}


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "CasareRPA Monitoring API",
        "version": API_VERSION,
        "docs": "/api/v1/docs",
        "redoc": "/api/v1/redoc",
        "openapi": "/api/v1/openapi.json",
        "health": "/health",
        "health_detailed": "/health/detailed",
    }
