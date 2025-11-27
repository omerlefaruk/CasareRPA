"""
CasareRPA - Project Storage (DEPRECATED)

DEPRECATED: This module is a compatibility wrapper.
The implementation has been moved to infrastructure.persistence.project_storage

For new code, import from:
- casare_rpa.infrastructure.persistence.project_storage

This module will be removed in v3.0.
"""

import warnings

# Re-export everything from infrastructure layer for backward compatibility
from ..infrastructure.persistence.project_storage import (
    ProjectStorage,
    PROJECT_MARKER_FILE,
)


# Emit deprecation warning when module is imported
warnings.warn(
    "casare_rpa.project.project_storage is deprecated. "
    "Use casare_rpa.infrastructure.persistence.project_storage instead. "
    "This module will be removed in v3.0.",
    DeprecationWarning,
    stacklevel=2
)


__all__ = [
    "ProjectStorage",
    "PROJECT_MARKER_FILE",
]
