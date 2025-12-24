"""
CasareRPA - Google OAuth Credential Management

Provides OAuth 2.0 credential handling for Google Workspace APIs:
- GoogleOAuthCredentialData: Dataclass for OAuth tokens with expiry tracking
- GoogleOAuthManager: Singleton for thread-safe token refresh and caching

Integrates with CredentialStore for secure token persistence.

Dependencies:
    - aiohttp (for async HTTP requests)
    - loguru (for logging)
"""

from __future__ import annotations

import asyncio
import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

import aiohttp
from loguru import logger


class GoogleOAuthError(Exception):
    """Base exception for Google OAuth errors."""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        error_details: dict[str, Any] | None = None,
    ):
        self.error_code = error_code
        self.error_details = error_details or {}
        super().__init__(message)


class TokenRefreshError(GoogleOAuthError):
    """Exception raised when token refresh fails."""

    pass


class TokenExpiredError(GoogleOAuthError):
    """Exception raised when token is expired and cannot be refreshed."""

    pass


class InvalidCredentialError(GoogleOAuthError):
    """Exception raised when credential data is invalid or incomplete."""

    pass


# Google OAuth endpoints
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v3/userinfo"
GOOGLE_REVOKE_ENDPOINT = "https://oauth2.googleapis.com/revoke"

# Token expiry buffer (refresh 5 minutes before actual expiry)
TOKEN_EXPIRY_BUFFER_SECONDS = 300


@dataclass
class GoogleOAuthCredentialData:
    """
    OAuth 2.0 credential data for Google APIs.

    Stores all tokens and metadata needed for Google API authentication,
    with automatic expiry tracking and serialization support.

    Attributes:
        client_id: OAuth 2.0 client ID from Google Cloud Console
        client_secret: OAuth 2.0 client secret from Google Cloud Console
        access_token: Current access token for API requests
        refresh_token: Refresh token for obtaining new access tokens
        token_expiry: UTC datetime when access token expires
        scopes: List of OAuth scopes granted
        user_email: Email of the authenticated user (optional)
        project_id: Google Cloud project ID (optional)
    """

    client_id: str
    client_secret: str
    access_token: str
    refresh_token: str
    token_expiry: datetime | None = None
    scopes: list[str] = field(default_factory=list)
    user_email: str | None = None
    project_id: str | None = None

    def is_expired(self, buffer_seconds: int = TOKEN_EXPIRY_BUFFER_SECONDS) -> bool:
        """
        Check if the access token is expired or about to expire.

        Uses a buffer to refresh tokens before actual expiry, preventing
        failed API calls due to race conditions.

        Args:
            buffer_seconds: Seconds before actual expiry to consider token expired.
                           Defaults to 5 minutes (300 seconds).

        Returns:
            True if token is expired or will expire within the buffer period.
        """
        if self.token_expiry is None:
            # No expiry set - assume expired to be safe
            return True

        # Ensure we're comparing timezone-aware datetimes
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
            Negative timedelta if already expired.
        """
        if self.token_expiry is None:
            return None

        now = datetime.now(UTC)
        expiry = self.token_expiry
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=UTC)

        return expiry - now

    def to_dict(self) -> dict[str, Any]:
        """
        Convert credential data to dictionary for storage.

        Returns:
            Dictionary with all credential fields, suitable for JSON serialization.
        """
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "scopes": self.scopes,
        }

        if self.token_expiry is not None:
            # Store as ISO format string
            expiry = self.token_expiry
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=UTC)
            data["token_expiry"] = expiry.isoformat()

        if self.user_email is not None:
            data["user_email"] = self.user_email

        if self.project_id is not None:
            data["project_id"] = self.project_id

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GoogleOAuthCredentialData:
        """
        Create credential data from dictionary.

        Args:
            data: Dictionary containing credential fields.

        Returns:
            GoogleOAuthCredentialData instance.

        Raises:
            InvalidCredentialError: If required fields are missing.
        """
        required_fields = [
            "client_id",
            "client_secret",
            "access_token",
            "refresh_token",
        ]
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
            refresh_token=data["refresh_token"],
            token_expiry=token_expiry,
            scopes=data.get("scopes", []),
            user_email=data.get("user_email"),
            project_id=data.get("project_id"),
        )

    def has_scope(self, scope: str) -> bool:
        """
        Check if credential has a specific scope.

        Args:
            scope: OAuth scope URL to check.

        Returns:
            True if scope is in the granted scopes list.
        """
        return scope in self.scopes

    def has_all_scopes(self, required_scopes: list[str]) -> bool:
        """
        Check if credential has all required scopes.

        Args:
            required_scopes: List of OAuth scope URLs to check.

        Returns:
            True if all required scopes are granted.
        """
        return all(self.has_scope(scope) for scope in required_scopes)


class GoogleOAuthManager:
    """
    Singleton manager for Google OAuth credentials.

    Provides thread-safe token refresh with caching and automatic
    credential retrieval from the credential store.

    Features:
    - Automatic token refresh before expiry
    - Thread-safe with asyncio.Lock
    - In-memory credential caching
    - User info fetching from Google

    Usage:
        manager = GoogleOAuthManager.get_instance()
        access_token = await manager.get_access_token("my_credential_id")
    """

    _instance: GoogleOAuthManager | None = None
    _instance_lock: threading.Lock = threading.Lock()  # Thread-safe singleton creation

    def __init__(self) -> None:
        """Initialize the manager (use get_instance() instead)."""
        self._credential_cache: dict[str, GoogleOAuthCredentialData] = {}
        self._refresh_locks: dict[str, threading.Lock] = {}  # Thread-safe, works across event loops
        self._session: aiohttp.ClientSession | None = None

    @classmethod
    async def get_instance(cls) -> GoogleOAuthManager:
        """
        Get the singleton instance of GoogleOAuthManager.

        Thread-safe singleton implementation using threading lock,
        which works correctly across different event loops.

        Returns:
            The singleton GoogleOAuthManager instance.
        """
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure HTTP session exists."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30.0)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self) -> None:
        """Close the HTTP session and clear caches."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
        self._credential_cache.clear()
        self._refresh_locks.clear()

    def _get_refresh_lock(self, credential_id: str) -> threading.Lock:
        """Get or create a lock for a specific credential's refresh operation."""
        if credential_id not in self._refresh_locks:
            self._refresh_locks[credential_id] = threading.Lock()
        return self._refresh_locks[credential_id]

    async def get_access_token(self, credential_id: str) -> str:
        """
        Get a valid access token for the given credential.

        Automatically refreshes the token if expired or about to expire.
        Thread-safe - concurrent calls for the same credential will share
        the refresh operation.

        Args:
            credential_id: ID of the credential in the CredentialStore.

        Returns:
            Valid access token string.

        Raises:
            InvalidCredentialError: If credential not found or invalid.
            TokenRefreshError: If token refresh fails.
        """
        # Get or load credential data
        credential_data = await self._get_credential_data(credential_id)

        # Check if token needs refresh
        if credential_data.is_expired():
            # Use per-credential lock to prevent concurrent refresh
            refresh_lock = self._get_refresh_lock(credential_id)
            with refresh_lock:  # Use threading.Lock (not async)
                # Double-check after acquiring lock
                credential_data = self._credential_cache.get(credential_id)
                if credential_data is None or credential_data.is_expired():
                    # Run refresh in sync context since we're holding threading lock
                    credential_data = await self._refresh_token(credential_id)

        return credential_data.access_token

    async def _get_credential_data(self, credential_id: str) -> GoogleOAuthCredentialData:
        """
        Get credential data from cache or load from store.

        Args:
            credential_id: ID of the credential.

        Returns:
            GoogleOAuthCredentialData instance.

        Raises:
            InvalidCredentialError: If credential not found or invalid.
        """
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

            credential_data = GoogleOAuthCredentialData.from_dict(raw_data)
            self._credential_cache[credential_id] = credential_data
            return credential_data

        except InvalidCredentialError:
            raise
        except Exception as e:
            logger.error(f"Failed to load credential {credential_id}: {e}")
            raise InvalidCredentialError(
                f"Failed to load credential: {e}",
                error_code="CREDENTIAL_LOAD_FAILED",
            ) from e

    async def _refresh_token(self, credential_id: str) -> GoogleOAuthCredentialData:
        """
        Refresh the access token using the refresh token.

        Updates both the in-memory cache and the credential store.

        Args:
            credential_id: ID of the credential to refresh.

        Returns:
            Updated GoogleOAuthCredentialData with new access token.

        Raises:
            TokenRefreshError: If refresh fails.
        """
        # Get current credential data
        credential_data = await self._get_credential_data(credential_id)

        if not credential_data.refresh_token:
            raise TokenRefreshError(
                "No refresh token available",
                error_code="NO_REFRESH_TOKEN",
            )

        logger.debug(f"Refreshing access token for credential {credential_id}")

        try:
            session = await self._ensure_session()

            # Prepare token refresh request
            data = {
                "grant_type": "refresh_token",
                "refresh_token": credential_data.refresh_token,
                "client_id": credential_data.client_id,
                "client_secret": credential_data.client_secret,
            }

            async with session.post(GOOGLE_TOKEN_ENDPOINT, data=data) as response:
                result = await response.json()

                if "error" in result:
                    error_desc = result.get("error_description", result["error"])
                    logger.error(f"Token refresh failed: {error_desc}")
                    raise TokenRefreshError(
                        f"Token refresh failed: {error_desc}",
                        error_code=result.get("error"),
                        error_details=result,
                    )

                # Update credential data
                credential_data.access_token = result["access_token"]

                # Google may return a new refresh token
                if "refresh_token" in result:
                    credential_data.refresh_token = result["refresh_token"]

                # Calculate new expiry
                expires_in = result.get("expires_in", 3600)
                credential_data.token_expiry = datetime.now(UTC) + timedelta(seconds=expires_in)

                # Update cache
                self._credential_cache[credential_id] = credential_data

                # Persist updated tokens to credential store
                await self._persist_credential(credential_id, credential_data)

                logger.debug(f"Token refreshed successfully, expires in {expires_in} seconds")
                return credential_data

        except TokenRefreshError:
            raise
        except aiohttp.ClientError as e:
            logger.error(f"Network error during token refresh: {e}")
            raise TokenRefreshError(
                f"Network error during token refresh: {e}",
                error_code="NETWORK_ERROR",
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error during token refresh: {e}")
            raise TokenRefreshError(
                f"Token refresh failed: {e}",
                error_code="REFRESH_FAILED",
            ) from e

    async def _persist_credential(
        self, credential_id: str, credential_data: GoogleOAuthCredentialData
    ) -> None:
        """
        Persist updated credential data to the credential store.

        Args:
            credential_id: ID of the credential.
            credential_data: Updated credential data.
        """
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
                logger.debug(f"Persisted updated credential {credential_id}")

        except Exception as e:
            # Log but don't fail - the in-memory cache has the new token
            logger.warning(f"Failed to persist credential {credential_id}: {e}")

    async def get_user_info(self, access_token: str) -> dict[str, Any]:
        """
        Fetch user information from Google's userinfo endpoint.

        Args:
            access_token: Valid access token with profile scope.

        Returns:
            Dictionary with user info (email, name, picture, etc.).

        Raises:
            GoogleOAuthError: If the request fails.
        """
        try:
            session = await self._ensure_session()
            headers = {"Authorization": f"Bearer {access_token}"}

            async with session.get(GOOGLE_USERINFO_ENDPOINT, headers=headers) as response:
                if response.status == 401:
                    raise TokenExpiredError(
                        "Access token is invalid or expired",
                        error_code="TOKEN_INVALID",
                    )

                if response.status != 200:
                    error_text = await response.text()
                    raise GoogleOAuthError(
                        f"Failed to get user info: {error_text}",
                        error_code=str(response.status),
                    )

                result = await response.json()
                return result

        except (TokenExpiredError, GoogleOAuthError):
            raise
        except aiohttp.ClientError as e:
            logger.error(f"Network error fetching user info: {e}")
            raise GoogleOAuthError(
                f"Network error fetching user info: {e}",
                error_code="NETWORK_ERROR",
            ) from e

    async def revoke_token(self, credential_id: str) -> bool:
        """
        Revoke the access and refresh tokens for a credential.

        Args:
            credential_id: ID of the credential to revoke.

        Returns:
            True if revocation was successful.
        """
        try:
            credential_data = await self._get_credential_data(credential_id)
            session = await self._ensure_session()

            # Revoke refresh token (also invalidates access token)
            data = {"token": credential_data.refresh_token}

            async with session.post(GOOGLE_REVOKE_ENDPOINT, data=data) as response:
                if response.status == 200:
                    # Clear from cache
                    self._credential_cache.pop(credential_id, None)
                    logger.info(f"Revoked token for credential {credential_id}")
                    return True
                else:
                    error_text = await response.text()
                    logger.warning(f"Token revocation failed: {error_text}")
                    return False

        except Exception as e:
            logger.error(f"Error revoking token: {e}")
            return False

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
        Validate a credential by attempting to get a valid token.

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


# Convenience functions for module-level access
async def get_google_oauth_manager() -> GoogleOAuthManager:
    """Get the singleton GoogleOAuthManager instance."""
    return await GoogleOAuthManager.get_instance()


async def get_google_access_token(credential_id: str) -> str:
    """
    Get a valid Google access token for the given credential.

    Convenience function that gets the manager and retrieves the token.

    Args:
        credential_id: ID of the credential in the CredentialStore.

    Returns:
        Valid access token string.
    """
    manager = await get_google_oauth_manager()
    return await manager.get_access_token(credential_id)


async def get_google_user_info(credential_id: str) -> dict[str, Any]:
    """
    Get Google user info for the given credential.

    Convenience function that gets the manager, retrieves a valid token,
    and fetches user info.

    Args:
        credential_id: ID of the credential in the CredentialStore.

    Returns:
        Dictionary with user info (email, name, picture, etc.).
    """
    manager = await get_google_oauth_manager()
    access_token = await manager.get_access_token(credential_id)
    return await manager.get_user_info(access_token)


__all__ = [
    # Exceptions
    "GoogleOAuthError",
    "TokenRefreshError",
    "TokenExpiredError",
    "InvalidCredentialError",
    # Data classes
    "GoogleOAuthCredentialData",
    # Manager
    "GoogleOAuthManager",
    # Constants
    "GOOGLE_TOKEN_ENDPOINT",
    "GOOGLE_USERINFO_ENDPOINT",
    "GOOGLE_REVOKE_ENDPOINT",
    "TOKEN_EXPIRY_BUFFER_SECONDS",
    # Convenience functions
    "get_google_oauth_manager",
    "get_google_access_token",
    "get_google_user_info",
]
