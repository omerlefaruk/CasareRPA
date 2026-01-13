"""
Compatibility shim for orchestrator API main module.

Re-exports from the server module for backward compatibility with
tests and existing imports.
"""

from casare_rpa.infrastructure.orchestrator.server import app, create_app, main

__all__ = ["app", "create_app", "main"]
