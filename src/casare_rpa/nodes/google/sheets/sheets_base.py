"""
CasareRPA - Google Sheets Base Node

Re-exports SheetsBaseNode from the unified google_base module.
Provides backward compatibility for existing imports.

New implementations should import directly from:
    from casare_rpa.nodes.google.google_base import SheetsBaseNode
"""

from __future__ import annotations

# Re-export the unified base class
from casare_rpa.nodes.google.google_base import (
    SheetsBaseNode,
    GoogleAPIClient,
    GoogleAPIError,
    GoogleAuthError,
    GoogleQuotaError,
    GOOGLE_CREDENTIAL_NAME,
    GOOGLE_ACCESS_TOKEN,
    GOOGLE_CREDENTIAL_PROPERTIES,
    get_sheets_scopes,
    SCOPES,
)

# For backward compatibility with existing code that uses GoogleSheetsClient directly
from casare_rpa.infrastructure.resources.google_sheets_client import (
    GoogleSheetsClient,
    GoogleSheetsConfig,
    GoogleSheetsError,
)


__all__ = [
    # Primary export
    "SheetsBaseNode",
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
    "get_sheets_scopes",
    "SCOPES",
    # Legacy Sheets client (for backward compatibility)
    "GoogleSheetsClient",
    "GoogleSheetsConfig",
    "GoogleSheetsError",
]
