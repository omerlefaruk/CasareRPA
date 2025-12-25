"""
CasareRPA - OAuth 2.0 Base Infrastructure

Provides shared OAuth 2.0 functionality for all providers:
- PKCE (RFC 7636) code challenge generation
- Base credential data class with token expiry tracking
- Token refresh with retry logic
- Thread-safe credential caching

Dependencies:
    - loguru (for logging)
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import secrets
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol
from urllib.parse import urlencode

from loguru import logger

# =============================================================================
# Exceptions
# =============================================================================


class OAuth2Error(Exception):
    """Base exception for OAuth 2.0 errors."""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        error_details: dict[str, Any] | None = None,
    ):
        self.error_code = error_code
        self.error_details = error_details or {}
        super().__init__(message)


class TokenRefreshError(OAuth2Error):
    """Exception raised when token refresh fails."""

    pass


class TokenExpiredError(OAuth2Error):
    """Exception raised when token is expired and cannot be refreshed."""

    pass


class InvalidCredentialError(OAuth2Error):
    """Exception raised when credential data is invalid or incomplete."""

    pass


# =============================================================================
# Constants
# =============================================================================

# Standard OAuth endpoints (Google-compatible)
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v2/userinfo"
REVOKE_ENDPOINT = "https://oauth2.googleapis.com/revoke"

# Token expiry buffer (refresh 5 minutes before actual expiry)
TOKEN_EXPIRY_BUFFER_SECONDS = 300

# Default token lifetime (seconds)
DEFAULT_EXPIRES_IN = 3600


# =============================================================================
# PKCE (RFC 7636)
# =============================================================================


@dataclass
class PKCEPair:
    """PKCE code verifier and challenge pair."""

    verifier: str
    challenge: str
    method: str = "S256"


def generate_pkce_pair() -> PKCEPair:
    """
    Generate a PKCE code verifier and challenge.

    Uses SHA-256 as the transformation method (recommended).

    Returns:
        PKCEPair with verifier and challenge.
    """
    verifier = secrets.token_urlsafe(32)
    challenge_bytes = hashlib.sha256(verifier.encode("utf-8")).digest()
    challenge = base64.urlsafe_b64encode(challenge_bytes).rstrip(b"=").decode("utf-8")
    return PKCEPair(verifier=verifier, challenge=challenge, method="S256")


# =============================================================================
# State Encoding/Decoding
# =============================================================================


def encode_state(state_data: dict[str, Any]) -> str:
    """
    Encode state data as a base64 URL-safe string.

    Args:
        state_data: Dictionary of state data to encode.

    Returns:
        Base64-encoded state string.
    """
    json_str = json.dumps(state_data)
    return base64.urlsafe_b64encode(json_str.encode("utf-8")).decode("utf-8")


def decode_state(state_str: str) -> dict[str, Any]:
    """
    Decode a base64-encoded state string.

    Args:
        state_str: Base64-encoded state string.

    Returns:
        Dictionary of state data.

    Raises:
        ValueError: If state string is invalid.
    """
    try:
        normalized = state_str.replace("-", "+").replace("_", "/")
        padding = (4 - len(normalized) % 4) % 4
        padded = normalized + "=" * padding
        json_str = base64.b64decode(padded).decode("utf-8")
        return json.loads(json_str)
    except Exception as e:
        raise ValueError(f"Invalid state string: {e}") from e


# =============================================================================
# Base OAuth Credential Data
# =============================================================================


@dataclass
class OAuth2CredentialData:
    """
    Base OAuth 2.0 credential data.

    Provides common token management for all OAuth providers.
    Subclasses can add provider-specific fields.

    Attributes:
        client_id: OAuth 2.0 client ID
        client_secret: OAuth 2.0 client secret
        access_token: Current access token
        refresh_token: Refresh token (empty for PKCE-only flows)
        token_expiry: UTC datetime when access token expires
        scopes: List of granted OAuth scopes
    """

    client_id: str
    client_secret: str
    access_token: str
    refresh_token: str = ""
    token_expiry: datetime | None = None
    scopes: list[str] = field(default_factory=list)

    def is_expired(self, buffer_seconds: int = TOKEN_EXPIRY_BUFFER_SECONDS) -> bool:
        """
        Check if the access token is expired or about to expire.

        Args:
            buffer_seconds: Seconds before actual expiry to consider token expired.

        Returns:
            True if token is expired or will expire within the buffer period.
        """
        if self.token_expiry is None:
            return True

        now = datetime.now(UTC)
        expiry = self.token_expiry
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=UTC)

        buffer = timedelta(seconds=buffer_seconds)
        return now >= (expiry - buffer)

    def time_until_expiry(self) -> timedelta | None:
        """
        Get time remaining until token expiry.

        Returns:
            timedelta until expiry, or None if expiry not set.
        """
        if self.token_expiry is None:
            return None

        now = datetime.now(UTC)
        expiry = self.token_expiry
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=UTC)

        return expiry - now

    def update_from_token_response(self, token_data: dict[str, Any]) -> None:
        """
        Update credential data from a token response.

        Args:
            token_data: Token response from OAuth provider.
        """
        self.access_token = token_data.get("access_token", self.access_token)

        if "refresh_token" in token_data:
            self.refresh_token = token_data["refresh_token"]

        if "expires_in" in token_data:
            expires_in = token_data["expires_in"]
            self.token_expiry = datetime.now(UTC) + timedelta(seconds=int(expires_in))

    def to_dict(self) -> dict[str, Any]:
        """
        Convert credential data to dictionary for storage.

        Returns:
            Dictionary suitable for JSON serialization.
        """
        data: dict[str, Any] = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "access_token": self.access_token,
            "scopes": self.scopes,
        }

        if self.refresh_token:
            data["refresh_token"] = self.refresh_token

        if self.token_expiry is not None:
            expiry = self.token_expiry
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=UTC)
            data["token_expiry"] = expiry.isoformat()

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OAuth2CredentialData:
        """
        Create credential data from dictionary.

        Args:
            data: Dictionary containing credential fields.

        Returns:
            OAuth2CredentialData instance.

        Raises:
            InvalidCredentialError: If required fields are missing.
        """
        required_fields = ["client_id", "client_secret", "access_token"]
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            raise InvalidCredentialError(
                f"Missing required credential fields: {', '.join(missing)}"
            )

        # Parse token expiry
        token_expiry = None
        if "token_expiry" in data and data["token_expiry"]:
            expiry_str = data["token_expiry"]
            if isinstance(expiry_str, str):
                try:
                    token_expiry = datetime.fromisoformat(expiry_str)
                    if token_expiry.tzinfo is None:
                        token_expiry = token_expiry.replace(tzinfo=UTC)
                except ValueError as e:
                    logger.warning(f"Failed to parse token_expiry '{expiry_str}': {e}")
            elif isinstance(expiry_str, datetime):
                token_expiry = expiry_str

        return cls(
            client_id=data["client_id"],
            client_secret=data["client_secret"],
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", ""),
            token_expiry=token_expiry,
            scopes=data.get("scopes", []),
        )

    def has_scope(self, scope: str) -> bool:
        """Check if credential has a specific scope."""
        return scope in self.scopes

    def has_all_scopes(self, required_scopes: list[str]) -> bool:
        """Check if credential has all required scopes."""
        return all(self.has_scope(scope) for scope in required_scopes)


# =============================================================================
# OAuth URL Builder
# =============================================================================


def build_oauth_url(
    auth_endpoint: str,
    client_id: str,
    redirect_uri: str,
    scopes: list[str],
    pkce_challenge: str | None = None,
    state: str | None = None,
    access_type: str = "offline",
    prompt: str = "consent",
    additional_params: dict[str, str] | None = None,
) -> str:
    """
    Build an OAuth authorization URL.

    Args:
        auth_endpoint: OAuth authorization endpoint URL.
        client_id: OAuth client ID.
        redirect_uri: OAuth redirect URI.
        scopes: List of OAuth scopes to request.
        pkce_challenge: PKCE code challenge (if using PKCE).
        state: OAuth state parameter.
        access_type: Access type (offline for refresh token).
        prompt: Consent prompt behavior.
        additional_params: Additional query parameters.

    Returns:
        Full authorization URL.
    """
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": " ".join(scopes),
        "access_type": access_type,
        "prompt": prompt,
    }

    if pkce_challenge:
        params["code_challenge"] = pkce_challenge
        params["code_challenge_method"] = "S256"

    if state:
        params["state"] = state

    if additional_params:
        params.update(additional_params)

    return f"{auth_endpoint}?{urlencode(params)}"


# =============================================================================
# Base OAuth Manager
# =============================================================================


class TokenRefreshProtocol(Protocol):
    """Protocol for objects that can refresh tokens."""

    async def refresh_token(self, credential_id: str) -> OAuth2CredentialData:
        """Refresh the access token for a credential."""
        ...


class CredentialStoreProtocol(Protocol):
    """Protocol for credential storage."""

    def get_credential(self, credential_id: str) -> dict[str, Any] | None:
        """Get credential data by ID."""
        ...

    def get_credential_info(self, credential_id: str) -> dict[str, Any] | None:
        """Get credential metadata by ID."""
        ...

    def save_credential(
        self,
        name: str,
        credential_type: str,
        category: str,
        data: dict[str, Any],
        description: str,
        tags: list[str],
        credential_id: str | None = None,
    ) -> str:
        """Save credential data."""
        ...


class BaseOAuth2Manager(ABC):
    """
    Base OAuth 2.0 manager with shared functionality.

    Provides:
    - Thread-safe credential caching
    - Per-credential refresh locks
    - Token refresh with retry
    - Credential persistence

    Subclasses must implement:
    - _refresh_token_impl: Provider-specific token refresh logic
    - _persist_credential_impl: Provider-specific persistence logic
    """

    _credential_cache: dict[str, OAuth2CredentialData] = {}
    _refresh_locks: dict[str, threading.Lock] = {}

    def __init__(self) -> None:
        """Initialize the base OAuth manager."""
        self._credential_cache: dict[str, OAuth2CredentialData] = {}
        self._refresh_locks: dict[str, threading.Lock] = {}

    @abstractmethod
    async def _load_credential(self, credential_id: str) -> OAuth2CredentialData:
        """
        Load credential from store.

        Args:
            credential_id: ID of the credential to load.

        Returns:
            OAuth2CredentialData instance.

        Raises:
            InvalidCredentialError: If credential not found or invalid.
        """
        ...

    @abstractmethod
    async def _refresh_token_impl(
        self, credential_data: OAuth2CredentialData
    ) -> OAuth2CredentialData:
        """
        Implement provider-specific token refresh logic.

        Args:
            credential_data: Current credential data with expired token.

        Returns:
            Updated credential data with new access token.

        Raises:
            TokenRefreshError: If refresh fails.
        """
        ...

    @abstractmethod
    async def _persist_credential_impl(
        self, credential_id: str, credential_data: OAuth2CredentialData
    ) -> None:
        """
        Persist updated credential to store.

        Args:
            credential_id: ID of the credential.
            credential_data: Updated credential data.
        """
        ...

    def _get_refresh_lock(self, credential_id: str) -> threading.Lock:
        """Get or create a lock for a specific credential's refresh operation."""
        if credential_id not in self._refresh_locks:
            self._refresh_locks[credential_id] = threading.Lock()
        return self._refresh_locks[credential_id]

    async def get_access_token(self, credential_id: str) -> str:
        """
        Get a valid access token for the given credential.

        Automatically refreshes if expired.

        Args:
            credential_id: ID of the credential.

        Returns:
            Valid access token string.

        Raises:
            InvalidCredentialError: If credential not found or invalid.
            TokenRefreshError: If token refresh fails.
        """
        # Check cache first
        if credential_id in self._credential_cache:
            credential_data = self._credential_cache[credential_id]
            if not credential_data.is_expired():
                return credential_data.access_token

        # Load from store
        credential_data = await self._load_credential(credential_id)
        self._credential_cache[credential_id] = credential_data

        # Check if refresh needed
        if credential_data.is_expired():
            refresh_lock = self._get_refresh_lock(credential_id)
            needs_refresh = False

            # Double-check pattern: minimize lock hold time
            with refresh_lock:
                cached = self._credential_cache.get(credential_id)
                if cached is None or cached.is_expired():
                    needs_refresh = True

            if needs_refresh:
                credential_data = await self._refresh_token(credential_id)

        return credential_data.access_token

    async def _refresh_token(self, credential_id: str) -> OAuth2CredentialData:
        """
        Refresh access token with retry logic.

        Args:
            credential_id: ID of the credential to refresh.

        Returns:
            Updated credential data.

        Raises:
            TokenRefreshError: If refresh fails after retries.
        """
        credential_data = await self._load_credential(credential_id)

        if not credential_data.refresh_token:
            raise TokenRefreshError(
                "No refresh token available",
                error_code="NO_REFRESH_TOKEN",
            )

        logger.debug(f"Refreshing token for credential {credential_id}")

        max_retries = 2
        last_error: Exception | None = None

        for attempt in range(max_retries):
            try:
                updated_data = await self._refresh_token_impl(credential_data)

                # Update cache
                self._credential_cache[credential_id] = updated_data

                # Persist to store
                await self._persist_credential_impl(credential_id, updated_data)

                logger.debug(f"Token refreshed for credential {credential_id}")
                return updated_data

            except TokenRefreshError as e:
                last_error = e
                if attempt < max_retries - 1:
                    logger.warning(f"Token refresh attempt {attempt + 1} failed, retrying: {e}")
                    await asyncio.sleep(1.0 * (2**attempt))  # Exponential backoff
                else:
                    logger.error(f"Token refresh failed after {max_retries} attempts")
                    raise

        raise TokenRefreshError(
            f"Token refresh failed: {last_error}",
            error_code="REFRESH_FAILED",
        ) from last_error

    def invalidate_cache(self, credential_id: str | None = None) -> None:
        """
        Invalidate cached credential data.

        Args:
            credential_id: Specific credential to invalidate, or None for all.
        """
        if credential_id is not None:
            self._credential_cache.pop(credential_id, None)
        else:
            self._credential_cache.clear()

    async def validate_credential(self, credential_id: str) -> tuple[bool, str | None]:
        """
        Validate a credential by checking token validity.

        Args:
            credential_id: ID of the credential to validate.

        Returns:
            Tuple of (is_valid, error_message).
        """
        try:
            await self.get_access_token(credential_id)
            return True, None
        except InvalidCredentialError as e:
            return False, str(e)
        except TokenRefreshError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Validation failed: {e}"


__all__ = [
    # Exceptions
    "OAuth2Error",
    "TokenRefreshError",
    "TokenExpiredError",
    "InvalidCredentialError",
    # Data classes
    "PKCEPair",
    "OAuth2CredentialData",
    # PKCE functions
    "generate_pkce_pair",
    "encode_state",
    "decode_state",
    # URL building
    "build_oauth_url",
    # Base manager
    "BaseOAuth2Manager",
    # Protocols
    "TokenRefreshProtocol",
    "CredentialStoreProtocol",
    # Constants
    "TOKEN_ENDPOINT",
    "USERINFO_ENDPOINT",
    "REVOKE_ENDPOINT",
    "TOKEN_EXPIRY_BUFFER_SECONDS",
    "DEFAULT_EXPIRES_IN",
]
