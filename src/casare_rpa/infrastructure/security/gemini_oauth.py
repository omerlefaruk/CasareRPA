"""
CasareRPA - Gemini AI Studio OAuth Credential Management

Provides OAuth 2.0 credential handling for Gemini AI Studio (generativelanguage.googleapis.com).
This uses the generative-language scope which works with Gemini subscription without needing GCP billing.

Key differences from google_oauth.py:
- Scope: generative-language (works with Gemini subscription)
- Endpoint: generativelanguage.googleapis.com (not Vertex AI)
- Model prefix: gemini/ (not vertex_ai/)
- No GCP project required

Based on opencode-gemini-auth: https://github.com/jenslys/opencode-gemini-auth

Dependencies:
    - UnifiedHttpClient (for resilient async HTTP requests)
    - loguru (for logging)
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import threading
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

from loguru import logger

from casare_rpa.infrastructure.http import (
    UnifiedHttpClient,
    UnifiedHttpClientConfig,
)

# =============================================================================
# Gemini AI Studio OAuth Configuration
# =============================================================================


# Gemini CLI OAuth 2.0 Client (from opencode-gemini-auth)
# These are public OAuth client credentials - safe to expose
# Source: https://github.com/jenslys/opencode-gemini-auth
# The client secret is public knowledge for OAuth flows (not a private secret)
def _get_gemini_client_id() -> str:
    """Get Gemini OAuth client ID from environment or use default."""
    return os.getenv(
        "GEMINI_OAUTH_CLIENT_ID",
        "681255809395-oo8ft2oprdrnp9e3aqf6av3hmdib135j.apps.googleusercontent.com",
    )


def _get_gemini_client_secret() -> str:
    """Get Gemini OAuth client secret from environment or use default."""
    return os.getenv(
        "GEMINI_OAUTH_CLIENT_SECRET",
        "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",
    )


GEMINI_REDIRECT_URI = "http://localhost:8085/oauth2callback"

# OAuth endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v1/userinfo"

# Gemini AI Studio API endpoint
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"

# Scopes (cloud-platform is used, but we route to Gemini AI Studio endpoint, not Vertex AI)
GEMINI_SCOPES = [
    "https://www.googleapis.com/auth/cloud-platform",
]

# Default token expiry (Google tokens usually expire in 1 hour)
DEFAULT_EXPIRES_IN = 3600
TOKEN_EXPIRY_BUFFER_SECONDS = 60


# =============================================================================
# Exceptions
# =============================================================================


class GeminiOAuthError(Exception):
    """Base exception for Gemini OAuth errors."""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        error_details: dict[str, Any] | None = None,
    ):
        self.error_code = error_code
        self.error_details = error_details or {}
        super().__init__(message)


class TokenExpiredError(GeminiOAuthError):
    """Raised when access token is expired."""

    pass


class InvalidCredentialError(GeminiOAuthError):
    """Raised when credential is invalid or not found."""

    pass


class TokenRefreshError(GeminiOAuthError):
    """Raised when token refresh fails."""

    pass


# =============================================================================
# PKCE Helper Functions
# =============================================================================


def generate_code_verifier() -> str:
    """Generate a secure random code verifier for PKCE."""
    return secrets.token_urlsafe(32)


def generate_code_challenge(verifier: str) -> str:
    """Generate the code challenge from the verifier using SHA256."""
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


def encode_state(payload: dict[str, Any]) -> str:
    """Encode a dict into a URL-safe base64 string for OAuth state."""
    json_str = json.dumps(payload)
    return base64.urlsafe_b64encode(json_str.encode()).rstrip(b"=").decode()


def decode_state(state: str) -> dict[str, Any]:
    """Decode an OAuth state parameter back into its dict representation."""
    # Add padding if needed
    padded = state + "=" * (4 - len(state) % 4)
    json_bytes = base64.urlsafe_b64decode(padded.encode())
    return json.loads(json_bytes.decode())


# =============================================================================
# Gemini OAuth Credential Data
# =============================================================================


@dataclass
class GeminiOAuthCredentialData:
    """
    OAuth 2.0 credential data for Gemini AI Studio.

    Uses the Gemini CLI OAuth client which requires only the
    generative-language scope (no GCP project or billing needed).

    Attributes:
        client_id: OAuth 2.0 client ID (Gemini CLI client)
        client_secret: OAuth 2.0 client secret (Gemini CLI client)
        access_token: Current access token for API requests
        refresh_token: Refresh token for obtaining new access tokens
        token_expiry: UTC datetime when access token expires
        scopes: List of OAuth scopes granted
        user_email: Email of the authenticated user
    """

    client_id: str
    client_secret: str
    access_token: str
    refresh_token: str
    token_expiry: datetime
    scopes: list[str]
    user_email: str | None = None

    def is_expired(self) -> bool:
        """Check if the access token is expired (or close to expiry)."""
        if self.token_expiry is None:
            return False
        buffer = timedelta(seconds=TOKEN_EXPIRY_BUFFER_SECONDS)
        return datetime.now(UTC) >= (self.token_expiry - buffer)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_expiry": self.token_expiry.isoformat(),
            "scopes": self.scopes,
        }
        if self.user_email:
            data["user_email"] = self.user_email
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GeminiOAuthCredentialData:
        """Create from dictionary."""
        token_expiry = data.get("token_expiry")
        if isinstance(token_expiry, str):
            token_expiry = datetime.fromisoformat(token_expiry)

        return cls(
            client_id=data["client_id"],
            client_secret=data["client_secret"],
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            token_expiry=token_expiry or datetime.now(UTC) + timedelta(seconds=DEFAULT_EXPIRES_IN),
            scopes=data.get("scopes", []),
            user_email=data.get("user_email"),
        )


# =============================================================================
# Gemini OAuth Manager
# =============================================================================


class GeminiOAuthManager:
    """
    Manager for Gemini AI Studio OAuth credentials.

    Provides thread-safe token refresh and credential management
    for the Gemini AI Studio API (generativelanguage.googleapis.com).

    Features:
    - Automatic token refresh before expiry
    - Thread-safe with threading.Lock
    - In-memory credential caching
    - PKCE OAuth flow support

    Usage:
        manager = await GeminiOAuthManager.get_instance()
        access_token = await manager.get_access_token("my_credential_id")
    """

    _instance: GeminiOAuthManager | None = None
    _instance_lock: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        """Initialize the manager (use get_instance() instead)."""
        self._credential_cache: dict[str, GeminiOAuthCredentialData] = {}
        self._refresh_locks: dict[str, threading.Lock] = {}
        self._global_lock = threading.Lock()

    @classmethod
    async def get_instance(cls) -> GeminiOAuthManager:
        """Get the singleton instance."""
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    async def close(self) -> None:
        """Clear caches (HTTP client is managed by UnifiedHttpClient singleton)."""
        self._credential_cache.clear()
        self._refresh_locks.clear()

    def _get_refresh_lock(self, credential_id: str) -> threading.Lock:
        """Get or create a refresh lock for a specific credential."""
        with self._global_lock:
            if credential_id not in self._refresh_locks:
                self._refresh_locks[credential_id] = threading.Lock()
            return self._refresh_locks[credential_id]

    async def _load_credential(self, credential_id: str) -> GeminiOAuthCredentialData:
        """Load credential from cache or store."""
        # Check cache first
        if credential_id in self._credential_cache:
            return self._credential_cache[credential_id]

        # Load from credential store
        try:
            from casare_rpa.infrastructure.security.credential_store import (
                get_credential_store,
            )

            store = get_credential_store()
            raw_data = store.get_credential(credential_id)

            if raw_data is None:
                raise InvalidCredentialError(
                    f"Credential not found: {credential_id}",
                    error_code="CREDENTIAL_NOT_FOUND",
                )

            # Load credential data (uses cloud-platform scope, routes to Gemini AI Studio)
            credential_data = GeminiOAuthCredentialData.from_dict(raw_data)
            self._credential_cache[credential_id] = credential_data
            return credential_data

        except InvalidCredentialError:
            raise
        except Exception as e:
            logger.error(f"Failed to load Gemini credential {credential_id}: {e}")
            raise InvalidCredentialError(
                f"Failed to load credential: {e}",
                error_code="CREDENTIAL_LOAD_FAILED",
            ) from e

    async def _refresh_token(
        self, credential_id: str, credential_data: GeminiOAuthCredentialData
    ) -> GeminiOAuthCredentialData:
        """Refresh the access token."""
        if not credential_data.refresh_token:
            raise TokenRefreshError(
                "No refresh token available",
                error_code="NO_REFRESH_TOKEN",
            )

        config = UnifiedHttpClientConfig(
            enable_ssrf_protection=True,
            max_retries=2,
            default_timeout=30.0,
        )

        async with UnifiedHttpClient(config) as http_client:
            data = {
                "grant_type": "refresh_token",
                "refresh_token": credential_data.refresh_token,
                "client_id": credential_data.client_id,
                "client_secret": credential_data.client_secret,
            }

            response = await http_client.post(GOOGLE_TOKEN_URL, data=data)
            result = await response.json()

            if "error" in result:
                error_desc = result.get("error_description", result["error"])
                logger.error(f"Gemini token refresh failed: {error_desc}")
                raise TokenRefreshError(
                    f"Token refresh failed: {error_desc}",
                    error_code=result.get("error"),
                    error_details=result,
                )

            # Update credential data
            credential_data.access_token = result["access_token"]

            if "refresh_token" in result:
                credential_data.refresh_token = result["refresh_token"]

            expires_in = result.get("expires_in", DEFAULT_EXPIRES_IN)
            credential_data.token_expiry = datetime.now(UTC) + timedelta(seconds=expires_in)

            logger.debug(f"Refreshed Gemini token for {credential_id}")

            return credential_data

    async def _persist_credential(
        self, credential_id: str, credential_data: GeminiOAuthCredentialData
    ) -> None:
        """Persist updated credential to store."""
        try:
            from casare_rpa.infrastructure.security.credential_store import (
                CredentialType,
                get_credential_store,
            )

            store = get_credential_store()
            info = store.get_credential_info(credential_id)

            if info:
                store.save_credential(
                    name=info["name"],
                    credential_type=CredentialType.GOOGLE_OAUTH_KIND,
                    category=info["category"],
                    data=credential_data.to_dict(),
                    description=info.get("description", ""),
                    tags=info.get("tags", []),
                    credential_id=credential_id,
                )
                logger.debug(f"Persisted refreshed Gemini credential: {credential_id}")

        except Exception as e:
            logger.warning(f"Failed to persist refreshed Gemini credential: {e}")

    async def get_access_token(self, credential_id: str) -> str:
        """
        Get a valid access token for the credential.

        Automatically refreshes if expired.

        Args:
            credential_id: The credential ID

        Returns:
            Valid access token
        """
        # Get credential-specific lock
        refresh_lock = self._get_refresh_lock(credential_id)

        # Check if another thread is already refreshing
        if refresh_lock.locked():
            # Wait for refresh to complete
            with refresh_lock:
                pass
            # Return from cache
            if credential_id in self._credential_cache:
                return self._credential_cache[credential_id].access_token

        # Load credential
        credential_data = await self._load_credential(credential_id)

        # Check if refresh is needed
        if credential_data.is_expired():
            with refresh_lock:
                # Double-check after acquiring lock
                if credential_id in self._credential_cache:
                    cached = self._credential_cache[credential_id]
                    if not cached.is_expired():
                        return cached.access_token

                # Refresh token
                credential_data = await self._refresh_token(credential_id, credential_data)

                # Update cache
                self._credential_cache[credential_id] = credential_data

                # Persist to store
                await self._persist_credential(credential_id, credential_data)

        return credential_data.access_token

    def clear_cache(self, credential_id: str | None = None) -> None:
        """Clear credential cache."""
        if credential_id:
            self._credential_cache.pop(credential_id, None)
        else:
            self._credential_cache.clear()


# =============================================================================
# OAuth Flow Helper Functions
# =============================================================================


@dataclass
class GeminiAuthorizationRequest:
    """Result of initiating OAuth flow."""

    auth_url: str
    code_verifier: str
    state: str


@dataclass
class GeminiTokenExchangeResult:
    """Result of exchanging auth code for tokens."""

    success: bool
    access_token: str | None = None
    refresh_token: str | None = None
    user_email: str | None = None
    error: str | None = None


def initiate_gemini_oauth() -> GeminiAuthorizationRequest:
    """
    Initiate the Gemini AI Studio OAuth flow.

    Generates the authorization URL with PKCE.

    Returns:
        GeminiAuthorizationRequest with auth URL, verifier, and state
    """
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)

    state_payload = {"verifier": code_verifier}
    state = encode_state(state_payload)

    params = {
        "client_id": _get_gemini_client_id(),
        "response_type": "code",
        "redirect_uri": GEMINI_REDIRECT_URI,
        "scope": " ".join(GEMINI_SCOPES),
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }

    auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    return GeminiAuthorizationRequest(
        auth_url=auth_url,
        code_verifier=code_verifier,
        state=state,
    )


async def exchange_gemini_code(
    code: str, state: str, session: Any = None
) -> GeminiTokenExchangeResult:
    """
    Exchange the authorization code for access/refresh tokens.

    Args:
        code: Authorization code from callback
        state: State parameter from callback (contains verifier)
        session: Ignored for backward compatibility (uses UnifiedHttpClient internally)

    Returns:
        GeminiTokenExchangeResult with tokens or error
    """
    try:
        # Decode state to get verifier
        state_data = decode_state(state)
        code_verifier = state_data.get("verifier")

        if not code_verifier:
            return GeminiTokenExchangeResult(success=False, error="Missing code verifier in state")

        config = UnifiedHttpClientConfig(
            enable_ssrf_protection=True,
            max_retries=2,
            default_timeout=30.0,
        )

        async with UnifiedHttpClient(config) as http_client:
            # Exchange code for tokens
            data = {
                "client_id": _get_gemini_client_id(),
                "client_secret": _get_gemini_client_secret(),
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": GEMINI_REDIRECT_URI,
                "code_verifier": code_verifier,
            }

            response = await http_client.post(GOOGLE_TOKEN_URL, data=data)
            result = await response.json()

            if "error" in result:
                error_desc = result.get("error_description", result["error"])
                return GeminiTokenExchangeResult(success=False, error=error_desc)

            access_token = result.get("access_token")
            refresh_token = result.get("refresh_token")

            if not refresh_token:
                return GeminiTokenExchangeResult(
                    success=False, error="Missing refresh token in response"
                )

            # Get user email
            user_email = None
            if access_token:
                userinfo_response = await http_client.get(
                    GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"}
                )
                if userinfo_response.status == 200:
                    userinfo = await userinfo_response.json()
                    user_email = userinfo.get("email")

            return GeminiTokenExchangeResult(
                success=True,
                access_token=access_token,
                refresh_token=refresh_token,
                user_email=user_email,
            )

    except Exception as e:
        logger.error(f"Gemini token exchange failed: {e}")
        return GeminiTokenExchangeResult(success=False, error=str(e))


# =============================================================================
# Direct API Client (for making requests without LiteLLM)
# =============================================================================


async def call_gemini_api(
    credential_id: str,
    model: str,
    prompt: str,
    *,
    generation_config: dict[str, Any] | None = None,
    manager: GeminiOAuthManager | None = None,
) -> dict[str, Any]:
    """
    Call the Gemini AI Studio API directly with OAuth.

    This bypasses LiteLLM and makes a direct HTTP request to
    generativelanguage.googleapis.com.

    Args:
        credential_id: OAuth credential ID
        model: Model name (e.g., "gemini-flash-lite-latest")
        prompt: User prompt
        generation_config: Optional generation config
        manager: Optional GeminiOAuthManager instance

    Returns:
        API response as dict
    """
    manager = manager or await GeminiOAuthManager.get_instance()
    access_token = await manager.get_access_token(credential_id)

    # Clean model name (remove prefixes)
    clean_model = model
    for prefix in ["gemini/", "models/", "vertex_ai/"]:
        if clean_model.startswith(prefix):
            clean_model = clean_model[len(prefix) :]
            break

    # Build API URL
    url = f"{GEMINI_API_BASE}/models/{clean_model}:generateContent"

    # Build request body
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": generation_config
        or {
            "temperature": 0.7,
            "maxOutputTokens": 8192,
        },
    }

    config = UnifiedHttpClientConfig(
        enable_ssrf_protection=True,
        max_retries=2,
        default_timeout=30.0,
    )

    async with UnifiedHttpClient(config) as http_client:
        response = await http_client.post(
            url,
            json=body,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            timeout=60.0,  # Longer timeout for generation
        )
        result = await response.json()

        if response.status != 200:
            error_msg = result.get("error", {}).get("message", "Unknown error")
            raise GeminiOAuthError(
                f"Gemini API error: {error_msg}",
                error_code=str(response.status),
                error_details=result,
            )

        return result


# =============================================================================
# Convenience functions
# =============================================================================


async def get_gemini_manager() -> GeminiOAuthManager:
    """Get the singleton GeminiOAuthManager instance."""
    return await GeminiOAuthManager.get_instance()


async def get_gemini_access_token(credential_id: str) -> str:
    """
    Get a valid Gemini AI Studio access token.

    Args:
        credential_id: The credential ID

    Returns:
        Valid access token
    """
    manager = await get_gemini_manager()
    return await manager.get_access_token(credential_id)


__all__ = [
    "GeminiOAuthManager",
    "GeminiOAuthCredentialData",
    "GeminiOAuthError",
    "TokenExpiredError",
    "InvalidCredentialError",
    "TokenRefreshError",
    "GeminiAuthorizationRequest",
    "GeminiTokenExchangeResult",
    "initiate_gemini_oauth",
    "exchange_gemini_code",
    "call_gemini_api",
    "get_gemini_manager",
    "get_gemini_access_token",
]
