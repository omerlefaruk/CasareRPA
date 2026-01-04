"""
Gemini AI Studio OAuth helper.

Provides a thin wrapper for retrieving an access token for Gemini AI Studio
calls (generativelanguage scope) using the existing Google OAuth credential
store/refresh machinery.
"""

from __future__ import annotations

from casare_rpa.infrastructure.security.google_oauth import GoogleOAuthManager

# Scopes used for Gemini models.
# - Google AI Studio uses generative-language scope.
# - Vertex AI Gemini uses cloud-platform scope.
GEMINI_SCOPES: list[str] = [
    "https://www.googleapis.com/auth/generative-language",
    "https://www.googleapis.com/auth/cloud-platform",
]


async def get_gemini_manager() -> GoogleOAuthManager:
    """Return the shared GoogleOAuthManager instance."""
    return await GoogleOAuthManager.get_instance()


async def get_gemini_access_token(credential_id: str) -> str:
    """Return a valid OAuth access token for Gemini AI Studio/Vertex AI."""
    manager = await get_gemini_manager()
    return await manager.get_access_token(credential_id)


__all__ = ["GEMINI_SCOPES", "get_gemini_access_token", "get_gemini_manager"]
