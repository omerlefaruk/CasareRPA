"""
CasareRPA - Google Drive Base Node

Re-exports DriveBaseNode from the unified google_base module.
Provides backward compatibility for existing imports.

New implementations should import directly from:
    from casare_rpa.nodes.google.google_base import DriveBaseNode
"""

from __future__ import annotations

# Re-export the unified base class
from casare_rpa.nodes.google.google_base import (
    DriveBaseNode,
    GoogleAPIClient,
    GoogleAPIError,
    GoogleAuthError,
    GoogleQuotaError,
    GOOGLE_CREDENTIAL_NAME,
    GOOGLE_ACCESS_TOKEN,
    GOOGLE_CREDENTIAL_PROPERTIES,
    get_drive_scopes,
    SCOPES,
)

# For backward compatibility with existing code that uses GoogleDriveClient directly
from casare_rpa.infrastructure.resources.google_drive_client import (
    GoogleDriveClient,
    DriveConfig,
    DriveAPIError,
    DriveMimeType,
)


__all__ = [
    # Primary export
    "DriveBaseNode",
    # Google client/credentials
    "GoogleAPIClient",
    "GoogleAPIError",
    "GoogleAuthError",
    "GoogleQuotaError",
    # PropertyDef constants
    "GOOGLE_CREDENTIAL_NAME",
    "GOOGLE_ACCESS_TOKEN",
    "GOOGLE_CREDENTIAL_PROPERTIES",
    # Scope helpers
    "get_drive_scopes",
    "SCOPES",
    # Legacy Drive client (for backward compatibility)
    "GoogleDriveClient",
    "DriveConfig",
    "DriveAPIError",
    "DriveMimeType",
]
