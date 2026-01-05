"""
FastAPI backend for monitoring dashboard.
Provides REST and WebSocket endpoints for multi-robot fleet monitoring.
"""

# Avoid importing the orchestrator app at module import time to prevent
# circular imports during startup.


def __getattr__(name: str):
    if name == "app":
        from casare_rpa.infrastructure.orchestrator.server import app

        return app
    raise AttributeError(name)


__all__ = ["app"]
