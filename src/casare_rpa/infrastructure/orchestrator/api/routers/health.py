"""
Unified Health Check Router for Orchestrator.

Provides health, liveness, and readiness probes with dependency checks.
"""

import time
from typing import Dict, Any
from fastapi import APIRouter, Depends

from casare_rpa.infrastructure.orchestrator.server_lifecycle import (
    get_state,
    get_robot_manager,
    get_db_manager,
)
from casare_rpa.infrastructure.orchestrator.api.auth import optional_auth, AuthenticatedUser

router = APIRouter()


@router.get("/health", tags=["Health"])
@router.get("/health/live", tags=["Health"])
async def health_check():
    """Basic liveness probe."""
    return {"status": "healthy", "service": "casare-rpa-orchestrator", "timestamp": time.time()}


@router.get("/health/ready", tags=["Health"])
async def readiness_check(user: AuthenticatedUser = Depends(optional_auth)):
    """
    Readiness probe with dependency status.

    Admins see detailed status, others see boolean ready.
    """
    state = get_state()
    robot_manager = get_robot_manager()
    db_manager = get_db_manager()

    # Core availability requirements
    db_ok = True
    if state.config and state.config.db_enabled:
        db_ok = db_manager.is_healthy if db_manager else False

    is_ready = db_ok and robot_manager is not None

    response: Dict[str, Any] = {"ready": is_ready, "status": "up" if is_ready else "degraded"}

    # Detailed info for authenticated admins
    if user and user.is_admin:
        response.update(
            {
                "database": "connected" if db_ok else "disconnected",
                "robots_connected": len(robot_manager.get_all_robots()) if robot_manager else 0,
                "pending_jobs": len(robot_manager.get_pending_jobs()) if robot_manager else 0,
                "uptime_seconds": round(time.time() - state.startup_time, 1)
                if state.startup_time
                else 0,
                "version": state.config.api_version if state.config else "unknown",
            }
        )

    return response
