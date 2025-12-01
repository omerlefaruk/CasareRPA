"""
CasareRPA - Error Handlers Package.

Provides error handler base class and implementations.
"""

from .base import ErrorHandler
from .node_handler import NodeErrorHandler

__all__ = [
    "ErrorHandler",
    "NodeErrorHandler",
]
