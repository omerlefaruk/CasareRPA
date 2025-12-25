"""
Antigravity OAuth 2.0 authentication flow with PKCE (Refactored).

Provides OAuth authorization and token exchange for accessing
Google's Antigravity API (Cloud Code Assist).

Refactored to use oauth2_base for shared PKCE/token management.

Gemini Subscription Support:
- Routes to Antigravity API for Gemini models (gemini-antigravity quota)
- Supports both GEMINI_ANTIGRAVITY and GEMINI_CLI quota pools
- Auto-detects project ID for Vertex AI integration
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from loguru import logger

from casare_rpa.infrastructure.security.antigravity_constants import (
    ANTIGRAVITY_CLIENT_ID,
    ANTIGRAVITY_CLIENT_SECRET,
    ANTIGRAVITY_ENDPOINT_FALLBACKS,
    ANTIGRAVITY_HEADERS,
    ANTIGRAVITY_LOAD_ENDPOINTS,
    ANTIGRAVITY_REDIRECT_URI,
    ANTIGRAVITY_SCOPES,
)
from casare_rpa.infrastructure.security.oauth2_base import (
    DEFAULT_EXPIRES_IN,
    TOKEN_ENDPOINT,
    decode_state,
    encode_state,
    generate_pkce_pair,
)

if TYPE_CHECKING:
    pass


# =============================================================================
# Antigravity-specific Data Classes
# =============================================================================


@dataclass
class AntigravityAuthState:
    """OAuth state for Antigravity flow."""

    verifier: str
    project_id: str


@dataclass
class AntigravityAuthorization:
    """Authorization URL and state for Antigravity OAuth."""

    url: str
    verifier: str
    project_id: str


@dataclass
class AntigravityTokenSuccess:
    """Successful token exchange result."""

    refresh_token: str
    access_token: str
    expires_at: int
    email: str | None
    project_id: str


@dataclass
class AntigravityTokenFailure:
    """Failed token exchange result."""

    error: str


AntigravityTokenResult = AntigravityTokenSuccess | AntigravityTokenFailure


# =============================================================================
# Antigravity OAuth Flow Functions
# =============================================================================


def build_antigravity_auth_url(project_id: str = "") -> AntigravityAuthorization:
    """
    Build Antigravity OAuth authorization URL with PKCE.

    Args:
        project_id: Optional Google Cloud project ID.

    Returns:
        AntigravityAuthorization with auth URL, verifier, and project ID.
    """
    pkce = generate_pkce_pair()
    state = encode_state({"verifier": pkce.verifier, "projectId": project_id})

    from casare_rpa.infrastructure.security.oauth2_base import build_oauth_url

    url = build_oauth_url(
        auth_endpoint="https://accounts.google.com/o/oauth2/v2/auth",
        client_id=ANTIGRAVITY_CLIENT_ID,
        redirect_uri=ANTIGRAVITY_REDIRECT_URI,
        scopes=list(ANTIGRAVITY_SCOPES),
        pkce_challenge=pkce.challenge,
        state=state,
        access_type="offline",
        prompt="consent",
    )

    return AntigravityAuthorization(
        url=url,
        verifier=pkce.verifier,
        project_id=project_id,
    )


async def fetch_project_id(access_token: str) -> str:
    """
    Fetch the Google Cloud project ID from Antigravity API.

    Uses the loadCodeAssist endpoint to discover the project ID
    associated with the authenticated Google account.

    Args:
        access_token: Valid OAuth access token.

    Returns:
        Project ID string, or empty string if not found.
    """
    from casare_rpa.infrastructure.http import UnifiedHttpClient, UnifiedHttpClientConfig

    config = UnifiedHttpClientConfig(default_timeout=30.0, max_retries=2)
    errors: list[str] = []

    load_headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "User-Agent": "google-api-nodejs-client/9.15.1",
        "X-Goog-Api-Client": "google-cloud-sdk vscode_cloudshelleditor/0.1",
        "Client-Metadata": ANTIGRAVITY_HEADERS["Client-Metadata"],
    }

    # Combine load and fallback endpoints, removing duplicates
    all_endpoints = list(
        dict.fromkeys([*ANTIGRAVITY_LOAD_ENDPOINTS, *ANTIGRAVITY_ENDPOINT_FALLBACKS])
    )

    async with UnifiedHttpClient(config) as client:
        for base_endpoint in all_endpoints:
            try:
                url = f"{base_endpoint}/v1internal:loadCodeAssist"
                response = await client.post(
                    url,
                    headers=load_headers,
                    json={
                        "metadata": {
                            "ideType": "IDE_UNSPECIFIED",
                            "platform": "PLATFORM_UNSPECIFIED",
                            "pluginType": "GEMINI",
                        }
                    },
                )

                if response.status != 200:
                    message = await response.text()
                    errors.append(
                        f"loadCodeAssist {response.status} at {base_endpoint}: {message[:200]}"
                    )
                    continue

                data = await response.json()
                project = data.get("cloudaicompanionProject")

                if isinstance(project, str) and project:
                    return project
                if isinstance(project, dict) and project.get("id"):
                    return project["id"]

                errors.append(f"loadCodeAssist missing project id at {base_endpoint}")

            except Exception as e:
                errors.append(f"loadCodeAssist error at {base_endpoint}: {e}")

    if errors:
        logger.warning(
            f"Failed to resolve Antigravity project via loadCodeAssist: {'; '.join(errors)}"
        )

    return ""


async def exchange_antigravity_token(code: str, state: str) -> AntigravityTokenResult:
    """
    Exchange OAuth authorization code for access/refresh tokens.

    Args:
        code: OAuth authorization code from callback.
        state: OAuth state parameter (contains PKCE verifier).

    Returns:
        AntigravityTokenSuccess with tokens, or AntigravityTokenFailure.
    """
    try:
        state_data = decode_state(state)
        verifier = state_data.get("verifier")
        project_id = state_data.get("projectId", "")

        if not verifier:
            return AntigravityTokenFailure(error="Missing PKCE verifier in state")

    except Exception as e:
        return AntigravityTokenFailure(error=f"Invalid state: {e}")

    from casare_rpa.infrastructure.http import UnifiedHttpClient, UnifiedHttpClientConfig

    config = UnifiedHttpClientConfig(default_timeout=30.0, max_retries=2)

    try:
        async with UnifiedHttpClient(config) as client:
            token_response = await client.post(
                TOKEN_ENDPOINT,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "client_id": ANTIGRAVITY_CLIENT_ID,
                    "client_secret": ANTIGRAVITY_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": ANTIGRAVITY_REDIRECT_URI,
                    "code_verifier": verifier,
                },
            )

            if token_response.status != 200:
                error_text = await token_response.text()
                return AntigravityTokenFailure(error=error_text)

            token_data = await token_response.json()

            # Fetch user email
            user_email: str | None = None
            try:
                user_response = await client.get(
                    "https://www.googleapis.com/oauth2/v1/userinfo?alt=json",
                    headers={"Authorization": f"Bearer {token_data['access_token']}"},
                )
                if user_response.status == 200:
                    user_info = await user_response.json()
                    user_email = user_info.get("email")
            except Exception as e:
                logger.debug(f"Could not fetch user info: {e}")

            refresh_token = token_data.get("refresh_token")
            if not refresh_token:
                return AntigravityTokenFailure(error="Missing refresh token in response")

            # Fetch project ID if not provided
            if not project_id:
                project_id = await fetch_project_id(token_data["access_token"])

            expires_in = token_data.get("expires_in", DEFAULT_EXPIRES_IN)
            expires_at = int(time.time() * 1000) + (expires_in * 1000)

            # Store refresh token with project ID for later use
            stored_refresh = f"{refresh_token}|{project_id or ''}"

            return AntigravityTokenSuccess(
                refresh_token=stored_refresh,
                access_token=token_data["access_token"],
                expires_at=expires_at,
                email=user_email,
                project_id=project_id or "",
            )

    except Exception as e:
        logger.error(f"Token exchange failed: {e}")
        return AntigravityTokenFailure(error=str(e))


# =============================================================================
# Refresh Token Parsing (for Account Management)
# =============================================================================


def parse_refresh_parts(refresh_token: str) -> tuple[str, str, str | None]:
    """
    Parse the stored refresh token format.

    Format: token|project_id|managed_project_id

    Args:
        refresh_token: Stored refresh token string.

    Returns:
        Tuple of (token, project_id, managed_project_id).
    """
    parts = refresh_token.split("|")
    token = parts[0] if len(parts) > 0 else ""
    project_id = parts[1] if len(parts) > 1 else ""
    managed_project_id = parts[2] if len(parts) > 2 else None
    return token, project_id, managed_project_id


def format_refresh_parts(token: str, project_id: str, managed_project_id: str | None = None) -> str:
    """
    Format refresh token with project IDs.

    Args:
        token: OAuth refresh token.
        project_id: Google Cloud project ID.
        managed_project_id: Optional managed project ID.

    Returns:
        Formatted refresh token string.
    """
    if managed_project_id:
        return f"{token}|{project_id}|{managed_project_id}"
    if project_id:
        return f"{token}|{project_id}"
    return token


__all__ = [
    # Data classes
    "AntigravityAuthState",
    "AntigravityAuthorization",
    "AntigravityTokenSuccess",
    "AntigravityTokenFailure",
    "AntigravityTokenResult",
    # OAuth flow functions
    "build_antigravity_auth_url",
    "fetch_project_id",
    "exchange_antigravity_token",
    # Refresh token utilities
    "parse_refresh_parts",
    "format_refresh_parts",
]
