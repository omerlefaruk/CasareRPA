"""
FastAPI backend for monitoring dashboard.

Provides REST and WebSocket endpoints for multi-robot fleet monitoring.
"""

from casare_rpa.infrastructure.orchestrator.api.main import app

__all__ = ["app"]
