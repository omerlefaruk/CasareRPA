"""
CasareRPA Cloud Orchestrator Server.

FastAPI server that manages robot fleet connections via WebSocket.
Designed for deployment on Railway, Render, or Fly.io.

Features:
- WebSocket endpoint for robot connections
- WebSocket endpoint for admin dashboard
- REST endpoints for job submission and robot management
- Supabase integration for presence sync
- API key authentication for robots

This module serves as the main entry point and composes the following modules:
- robot_manager.py: Robot/job state management
- server_lifecycle.py: Configuration, state, lifespan
- server_auth.py: API key and admin authentication
- websocket_handlers.py: WebSocket endpoints
- health_endpoints.py: Health check endpoints
- rest_endpoints.py: REST API endpoints
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

# Import lifecycle management
from casare_rpa.infrastructure.orchestrator.server_lifecycle import (
    OrchestratorConfig,
    get_config,
    get_robot_manager,
    lifespan,
    reset_orchestrator_state,
)

# Import routers
from casare_rpa.infrastructure.orchestrator import health_endpoints
from casare_rpa.infrastructure.orchestrator import rest_endpoints
from casare_rpa.infrastructure.orchestrator import websocket_handlers

# Re-export for backward compatibility
from casare_rpa.infrastructure.orchestrator.robot_manager import (
    ConnectedRobot,
    PendingJob,
    RobotManager,
)
from casare_rpa.infrastructure.orchestrator.rest_endpoints import (
    JobResponse,
    JobSubmission,
    RobotInfo,
    RobotRegistration,
)
from casare_rpa.infrastructure.orchestrator.server_auth import (
    validate_admin_secret,
    validate_websocket_api_key,
    verify_admin_api_key,
    verify_api_key,
)

__all__ = [
    # Configuration
    "OrchestratorConfig",
    "get_config",
    "get_robot_manager",
    "reset_orchestrator_state",
    # Models
    "ConnectedRobot",
    "PendingJob",
    "RobotManager",
    "JobResponse",
    "JobSubmission",
    "RobotInfo",
    "RobotRegistration",
    # Auth
    "validate_admin_secret",
    "validate_websocket_api_key",
    "verify_admin_api_key",
    "verify_api_key",
    # App
    "create_app",
    "app",
    "main",
]


def create_app() -> FastAPI:
    """Create FastAPI application with composed routers."""
    config = get_config()

    app = FastAPI(
        title="CasareRPA Cloud Orchestrator",
        description="Robot fleet management and job orchestration service",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS - restrictive by default
    origins = config.cors_origins
    if not origins:
        logger.warning(
            "CORS_ORIGINS not configured - using restrictive default. "
            "Set CORS_ORIGINS environment variable for production."
        )
        origins = []

    # Warn if using wildcard with credentials
    if "*" in origins:
        logger.warning(
            "CORS configured with '*' - this is insecure for production! "
            "Set specific origins in CORS_ORIGINS."
        )
        allow_credentials = False
    else:
        allow_credentials = True

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=allow_credentials,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Api-Key", "X-Request-ID"],
    )

    # Include routers
    app.include_router(health_endpoints.router, tags=["Health"])
    app.include_router(rest_endpoints.router, prefix="/api", tags=["API"])
    app.include_router(websocket_handlers.router, prefix="/ws", tags=["WebSocket"])

    return app


# Create application instance
app = create_app()


def main() -> None:
    """Run the orchestrator server."""
    import uvicorn

    config = get_config()
    uvicorn.run(
        "casare_rpa.infrastructure.orchestrator.server:app",
        host=config.host,
        port=config.port,
        workers=config.workers,
        log_level="info",
    )


if __name__ == "__main__":
    main()
