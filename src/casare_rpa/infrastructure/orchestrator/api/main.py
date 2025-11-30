"""
FastAPI application for CasareRPA monitoring dashboard.

Provides REST and WebSocket endpoints for fleet monitoring,
job execution tracking, and analytics.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from casare_rpa.infrastructure.events import (
    get_monitoring_event_bus,
    MonitoringEventType,
)
from .routers import auth, metrics, websockets, workflows, schedules
from .routers.websockets import (
    on_job_status_changed,
    on_robot_heartbeat,
    on_queue_depth_changed,
)
from .dependencies import (
    get_metrics_collector,
    get_pool_manager,
    DatabasePoolManager,
)


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
    logger.info("Starting CasareRPA Monitoring API")

    # Initialize database connection pool
    await _init_database_pool(app)

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

    # Shutdown database pool
    await _shutdown_database_pool(app)

    logger.info("Shutting down CasareRPA Monitoring API")


# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI application
app = FastAPI(
    title="CasareRPA Monitoring API",
    description="Multi-robot fleet monitoring and analytics API",
    version="1.0.0",
    lifespan=lifespan,
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:8000",  # Production (served by FastAPI)
    ],
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "DELETE",
    ],  # Extended for workflow/schedule management
    allow_headers=["Content-Type", "Authorization", "X-Api-Token"],  # Robot auth
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(metrics.router, prefix="/api/v1", tags=["metrics"])
app.include_router(websockets.router, prefix="/ws", tags=["websockets"])
app.include_router(workflows.router, prefix="/api/v1", tags=["workflows"])
app.include_router(schedules.router, prefix="/api/v1", tags=["schedules"])


@app.get("/health")
async def health_check():
    """
    Basic health check endpoint for load balancers.

    Returns healthy status if API is running. Does not check dependencies.
    For detailed health info including database status, use /health/detailed.
    """
    return {"status": "healthy", "service": "casare-rpa-monitoring"}


@app.get("/health/detailed")
async def detailed_health_check():
    """
    Detailed health check including all dependencies.

    Returns status of:
    - API service
    - Database connection pool
    - Database connectivity

    Response codes:
    - 200: All systems healthy
    - 200 with degraded=true: API running but some dependencies unavailable
    """
    db_manager: Optional[DatabasePoolManager] = getattr(app.state, "db_manager", None)

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
    all_healthy = db_health.get("healthy", False)

    return {
        "status": "healthy" if all_healthy else "degraded",
        "service": "casare-rpa-monitoring",
        "dependencies": {
            "database": db_health,
        },
    }


@app.get("/health/ready")
async def readiness_check():
    """
    Kubernetes-style readiness probe.

    Returns 200 only if all critical dependencies are available.
    Use this for load balancer health checks that should remove
    unhealthy instances from rotation.
    """
    db_manager: Optional[DatabasePoolManager] = getattr(app.state, "db_manager", None)

    # For readiness, database must be healthy
    if db_manager is None:
        return {"ready": False, "reason": "Database not configured"}

    db_health = await db_manager.check_health()

    if not db_health.get("healthy", False):
        return {
            "ready": False,
            "reason": db_health.get("error", "Database unhealthy"),
        }

    return {"ready": True}


@app.get("/health/live")
async def liveness_check():
    """
    Kubernetes-style liveness probe.

    Returns 200 if the process is alive and can handle requests.
    Does not check dependencies - use /health/ready for that.
    """
    return {"alive": True}


@app.get("/")
async def root():
    """Root endpoint - redirect to docs."""
    return {
        "message": "CasareRPA Monitoring API",
        "docs": "/docs",
        "health": "/health",
        "health_detailed": "/health/detailed",
    }
