"""
CasareRPA - Google Calendar Base Node

Re-exports CalendarBaseNode from the unified google_base module.
Provides backward compatibility for existing imports.

New implementations should import directly from:
    from casare_rpa.nodes.google.google_base import CalendarBaseNode
"""

from __future__ import annotations

# Re-export the unified base class
from casare_rpa.nodes.google.google_base import (
    CalendarBaseNode,
    GoogleAPIClient,
    GoogleAPIError,
    GoogleAuthError,
    GoogleQuotaError,
    GOOGLE_CREDENTIAL_NAME,
    GOOGLE_ACCESS_TOKEN,
    GOOGLE_CREDENTIAL_PROPERTIES,
    get_calendar_scopes,
    SCOPES,
)

# For backward compatibility with existing code that uses GoogleCalendarClient directly
from casare_rpa.infrastructure.resources.google_calendar_client import (
    GoogleCalendarClient,
    CalendarConfig,
    GoogleCalendarAPIError,
)


__all__ = [
    # Primary export
    "CalendarBaseNode",
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
    "get_calendar_scopes",
    "SCOPES",
    # Legacy Calendar client (for backward compatibility)
    "GoogleCalendarClient",
    "CalendarConfig",
    "GoogleCalendarAPIError",
]
