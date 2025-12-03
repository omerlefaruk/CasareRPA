"""
CasareRPA - Google Docs Base Node

Re-exports DocsBaseNode from the unified google_base module.
Provides backward compatibility for existing imports.

New implementations should import directly from:
    from casare_rpa.nodes.google.google_base import DocsBaseNode
"""

from __future__ import annotations

# Re-export the unified base class
from casare_rpa.nodes.google.google_base import (
    DocsBaseNode,
    GoogleAPIClient,
    GoogleAPIError,
    GoogleAuthError,
    GoogleQuotaError,
    GOOGLE_CREDENTIAL_NAME,
    GOOGLE_ACCESS_TOKEN,
    GOOGLE_CREDENTIAL_PROPERTIES,
    get_docs_scopes,
    SCOPES,
)

# For backward compatibility with existing code that uses GoogleDocsClient directly
from casare_rpa.infrastructure.resources.google_docs_client import (
    GoogleDocsClient,
    GoogleDocsConfig,
    GoogleDocsAPIError,
)


__all__ = [
    # Primary export
    "DocsBaseNode",
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
    "get_docs_scopes",
    "SCOPES",
    # Legacy Docs client (for backward compatibility)
    "GoogleDocsClient",
    "GoogleDocsConfig",
    "GoogleDocsAPIError",
]
