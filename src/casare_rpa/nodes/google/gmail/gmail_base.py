"""
CasareRPA - Gmail Base Node

Re-exports GmailBaseNode from the unified google_base module.
Provides backward compatibility for existing imports.

New implementations should import directly from:
    from casare_rpa.nodes.google.google_base import GmailBaseNode
"""

from __future__ import annotations

# Re-export the unified base class
from casare_rpa.nodes.google.google_base import (
    GmailBaseNode,
    GoogleAPIClient,
    GoogleAPIError,
    GoogleAuthError,
    GoogleQuotaError,
    GOOGLE_CREDENTIAL_NAME,
    GOOGLE_ACCESS_TOKEN,
    GOOGLE_CREDENTIAL_PROPERTIES,
    get_gmail_scopes,
    SCOPES,
)

# For backward compatibility with existing code that uses GmailClient directly
# Import the infrastructure client
from casare_rpa.infrastructure.resources.gmail_client import (
    GmailClient,
    GmailConfig,
    GmailAPIError,
)


__all__ = [
    # Primary export
    "GmailBaseNode",
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
    "get_gmail_scopes",
    "SCOPES",
    # Legacy Gmail client (for backward compatibility)
    "GmailClient",
    "GmailConfig",
    "GmailAPIError",
]
