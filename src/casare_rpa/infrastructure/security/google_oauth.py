"""
CasareRPA - Google OAuth Credential Management (Refactored)

Provides OAuth 2.0 credential handling for Google APIs:
- GoogleOAuthCredentialData: Extended dataclass with project/user tracking
- GoogleOAuthManager: Singleton for Vertex AI token management

Integrates with CredentialStore for secure token persistence.

Refactored to use oauth2_base for shared PKCE/token management.

Dependencies:
    - UnifiedHttpClient (for async HTTP requests)
    - loguru (for logging)
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from loguru import logger

from casare_rpa.infrastructure.security.oauth2_base import (
    DEFAULT_EXPIRES_IN,
    REVOKE_ENDPOINT,
    TOKEN_ENDPOINT,
    TOKEN_EXPIRY_BUFFER_SECONDS,
    USERINFO_ENDPOINT,
    BaseOAuth2Manager,
    InvalidCredentialError,
    OAuth2CredentialData,
    TokenExpiredError,
    TokenRefreshError,
)

# Re-export base exceptions for backward compatibility
GoogleOAuthError = TokenRefreshError


# =============================================================================
# Google-specific Credential Data
# =============================================================================


@dataclass
class GoogleOAuthCredentialData(OAuth2CredentialData):
    """
    OAuth 2.0 credential data for Google APIs.

    Extends the base with Google-specific fields:
    - user_email: Email of the authenticated user
    - project_id: Google Cloud project ID (for Vertex AI)

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

    user_email: str | None = None
    project_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        data = super().to_dict()

        if self.user_email is not None:
            data["user_email"] = self.user_email

        if self.project_id is not None:
            data["project_id"] = self.project_id

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GoogleOAuthCredentialData:
        """Create from dictionary."""
        # Extract Google-specific fields before passing to parent
        user_email = data.get("user_email")
        project_id = data.get("project_id")

        # Create base credential first
        base_credential = super().from_dict(data)

        return cls(
            client_id=base_credential.client_id,
            client_secret=base_credential.client_secret,
            access_token=base_credential.access_token,
            refresh_token=base_credential.refresh_token,
            token_expiry=base_credential.token_expiry,
            scopes=base_credential.scopes,
            user_email=user_email,
            project_id=project_id,
        )


# =============================================================================
# Google OAuth Manager
# =============================================================================


class GoogleOAuthManager(BaseOAuth2Manager):
    """
    Singleton manager for Google OAuth credentials.

    Provides thread-safe token refresh for Vertex AI and other Google APIs.

    Features:
    - Automatic token refresh before expiry
    - Thread-safe with threading.Lock (works across event loops)
    - In-memory credential caching
    - User info fetching from Google

    Usage:
        manager = await GoogleOAuthManager.get_instance()
        access_token = await manager.get_access_token("my_credential_id")
    """

    _instance: GoogleOAuthManager | None = None
    _instance_lock: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        """Initialize the manager (use get_instance() instead)."""
        super().__init__()

    @classmethod
    async def get_instance(cls) -> GoogleOAuthManager:
        """
        Get the singleton instance of GoogleOAuthManager.

        Thread-safe singleton implementation using threading lock.

        Returns:
            The singleton GoogleOAuthManager instance.
        """
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    async def close(self) -> None:
        """Clear caches."""
        self._credential_cache.clear()
        self._refresh_locks.clear()

    async def _load_credential(self, credential_id: str) -> GoogleOAuthCredentialData:
        """Load credential from cache or store."""
        # Check cache first
        if credential_id in self._credential_cache:
            return self._credential_cache[credential_id]  # type: ignore

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

    async def _refresh_token_impl(
        self, credential_data: GoogleOAuthCredentialData
    ) -> GoogleOAuthCredentialData:
        """Implement Google token refresh."""
        if not credential_data.refresh_token:
            raise TokenRefreshError(
                "No refresh token available",
                error_code="NO_REFRESH_TOKEN",
            )

        from casare_rpa.infrastructure.http import UnifiedHttpClient, UnifiedHttpClientConfig

        config = UnifiedHttpClientConfig(
            enable_ssrf_protection=True,
            max_retries=2,
            default_timeout=30.0,
        )

        # Prepare token refresh request
        data = {
            "grant_type": "refresh_token",
            "refresh_token": credential_data.refresh_token,
            "client_id": credential_data.client_id,
            "client_secret": credential_data.client_secret,
        }

        async with UnifiedHttpClient(config) as http_client:
            response = await http_client.post(
                TOKEN_ENDPOINT,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            result = await response.json()

            if "error" in result:
                error_desc = result.get("error_description", result["error"])
                logger.error(f"Google token refresh failed: {error_desc}")
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

            return credential_data

    async def _persist_credential_impl(
        self, credential_id: str, credential_data: GoogleOAuthCredentialData
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
                logger.debug(f"Persisted updated credential {credential_id}")

        except Exception as e:
            logger.warning(f"Failed to persist credential {credential_id}: {e}")

    async def get_user_info(self, access_token: str) -> dict[str, Any]:
        """
        Fetch user information from Google's userinfo endpoint.

        Args:
            access_token: Valid access token with profile scope.

        Returns:
            Dictionary with user info (email, name, picture, etc.).
        """
        from casare_rpa.infrastructure.http import UnifiedHttpClient, UnifiedHttpClientConfig

        config = UnifiedHttpClientConfig(
            enable_ssrf_protection=True,
            max_retries=2,
            default_timeout=30.0,
        )

        try:
            headers = {"Authorization": f"Bearer {access_token}"}

            async with UnifiedHttpClient(config) as http_client:
                response = await http_client.get(USERINFO_ENDPOINT, headers=headers)

                if response.status == 401:
                    await response.json()
                    raise TokenExpiredError(
                        "Access token is invalid or expired",
                        error_code="TOKEN_INVALID",
                    )

                if response.status != 200:
                    error_text = await response.text()
                    raise TokenRefreshError(
                        f"Failed to get user info: {error_text}",
                        error_code=str(response.status),
                    )

                return await response.json()

        except (TokenExpiredError, TokenRefreshError):
            raise
        except Exception as e:
            logger.error(f"Network error fetching user info: {e}")
            raise TokenRefreshError(
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
        from casare_rpa.infrastructure.http import UnifiedHttpClient, UnifiedHttpClientConfig

        config = UnifiedHttpClientConfig(
            enable_ssrf_protection=True,
            max_retries=2,
            default_timeout=30.0,
        )

        try:
            credential_data = await self._load_credential(credential_id)

            if not credential_data.refresh_token:
                logger.warning(f"No refresh token to revoke for credential {credential_id}")
                return False

            data = {"token": credential_data.refresh_token}

            async with UnifiedHttpClient(config) as http_client:
                response = await http_client.post(REVOKE_ENDPOINT, data=data)

                if response.status == 200:
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


# =============================================================================
# Convenience Functions
# =============================================================================


async def get_google_oauth_manager() -> GoogleOAuthManager:
    """Get the singleton GoogleOAuthManager instance."""
    return await GoogleOAuthManager.get_instance()


async def get_google_access_token(credential_id: str) -> str:
    """
    Get a valid Google access token for the given credential.

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

    Args:
        credential_id: ID of the credential in the CredentialStore.

    Returns:
        Dictionary with user info (email, name, picture, etc.).
    """
    manager = await get_google_oauth_manager()
    access_token = await manager.get_access_token(credential_id)
    return await manager.get_user_info(access_token)


__all__ = [
    # Exceptions (backward compatibility)
    "GoogleOAuthError",
    "TokenRefreshError",
    "TokenExpiredError",
    "InvalidCredentialError",
    # Data classes
    "GoogleOAuthCredentialData",
    # Manager
    "GoogleOAuthManager",
    # Constants (backward compatibility)
    "GOOGLE_TOKEN_ENDPOINT",
    "GOOGLE_USERINFO_ENDPOINT",
    "GOOGLE_REVOKE_ENDPOINT",
    "TOKEN_EXPIRY_BUFFER_SECONDS",
    # Convenience functions
    "get_google_oauth_manager",
    "get_google_access_token",
    "get_google_user_info",
]

# Export constants from base module
GOOGLE_TOKEN_ENDPOINT = TOKEN_ENDPOINT
GOOGLE_USERINFO_ENDPOINT = USERINFO_ENDPOINT
GOOGLE_REVOKE_ENDPOINT = REVOKE_ENDPOINT
