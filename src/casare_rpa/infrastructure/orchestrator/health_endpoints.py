"""
Health Check Endpoints for Cloud Orchestrator.

Provides health, liveness, and readiness endpoints for Kubernetes/load balancers.
"""

from fastapi import APIRouter

from casare_rpa.infrastructure.orchestrator.server_lifecycle import get_robot_manager


router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check."""
    return {"status": "healthy", "service": "casare-orchestrator"}


@router.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe."""
    return {"alive": True}


@router.get("/health/ready")
async def readiness_check():
    """Kubernetes readiness probe."""
    manager = get_robot_manager()
    return {
        "ready": True,
        "connected_robots": len(manager.get_all_robots()),
        "pending_jobs": len(manager.get_pending_jobs()),
    }
