"""API routers for monitoring endpoints."""

from casare_rpa.infrastructure.orchestrator.api.routers import (
    analytics,
    auth,
    dlq,
    jobs,
    metrics,
    robot_api_keys,
    robots,
    schedules,
    websockets,
    workflows,
)

__all__ = [
    "analytics",
    "auth",
    "dlq",
    "jobs",
    "metrics",
    "robot_api_keys",
    "robots",
    "schedules",
    "websockets",
    "workflows",
    "health",
]
