"""
CasareRPA - Node Decorators Package

Provides decorators for common node patterns:
- @node: Unified decorator for node metadata and exec ports
- @properties: Property schema decorator
- @error_handler: Standardized error handling for execute methods
- @handle_errors: Legacy error handling with retry support
- @validate_required: Parameter validation decorator
- @with_timeout: Timeout handling decorator

Usage:
    from casare_rpa.domain.decorators import (
        node,
        properties,
        error_handler,
        handle_errors,
        validate_required,
        with_timeout,
    )
"""

# Import error_handler from its module
from casare_rpa.domain.decorators.error_handler import error_handler

# Re-export everything from the main decorators module
# This file (decorators/__init__.py) shadows decorators.py, so we need to
# import from _decorators_core.py which contains the actual implementations

# NOTE: The main decorators (node, properties, etc.) are defined in the
# decorators.py file at the same level. Since Python prioritizes packages
# over modules, we need to move those decorators here.

# For now, import from _decorators_core which we'll create
# Actually, the cleanest solution is to rename decorators.py to _decorators_core.py
# and import from there. Let's do a simpler approach - just move the critical
# imports here by reimporting from the internal module.

# Import core decorators - we'll create a _core module with the original content
try:
    from casare_rpa.domain._decorators_core import (
        node,
        properties,
        handle_errors,
        validate_required,
        with_timeout,
        get_node_metadata,
        get_node_schema,
        has_exec_ports,
    )
except ImportError:
    # Fallback: decorators.py hasn't been renamed yet
    # This shouldn't happen after the migration is complete
    raise ImportError(
        "Cannot import decorators. Please ensure _decorators_core.py exists. "
        "Run: mv domain/decorators.py domain/_decorators_core.py"
    )

__all__ = [
    # Class decorators
    "node",
    "properties",
    # Method decorators
    "error_handler",
    "handle_errors",
    "validate_required",
    "with_timeout",
    # Utility functions
    "get_node_metadata",
    "get_node_schema",
    "has_exec_ports",
]
