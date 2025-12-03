"""
CasareRPA - Error Handlers Package.

Provides error handler base class and implementations.
"""

from casare_rpa.domain.errors.handlers.base import ErrorHandler
from casare_rpa.domain.errors.handlers.node_handler import NodeErrorHandler

__all__ = [
    "ErrorHandler",
    "NodeErrorHandler",
]
