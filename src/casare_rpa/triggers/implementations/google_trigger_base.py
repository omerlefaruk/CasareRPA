"""
CasareRPA - Google Workspace Trigger Base

Base class for Google Workspace triggers (Gmail, Sheets, Drive)
with shared OAuth 2.0 authentication logic.
"""

import asyncio
from abc import abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from loguru import logger

from casare_rpa.infrastructure.http import UnifiedHttpClient, UnifiedHttpClientConfig
from casare_rpa.triggers.base import BaseTrigger, BaseTriggerConfig, TriggerStatus


@dataclass
class GoogleCredentials:
    """
    OAuth 2.0 credentials for Google APIs.

    Attributes:
        access_token: Current access token
        refresh_token: Token for refreshing access
        token_type: Token type (usually 'Bearer')
        expires_at: When the access token expires
        scope: Granted scopes
    """

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_at: datetime | None = None
    scope: str = ""

    @property
    def is_expired(self) -> bool:
        """Check if access token is expired (with 5 min buffer)."""
        if self.expires_at is None:
            return True
        buffer = timedelta(minutes=5)
        return datetime.now(UTC) >= (self.expires_at - buffer)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_type": self.token_type,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "scope": self.scope,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GoogleCredentials":
        """Create from dictionary."""
        expires_at = data.get("expires_at")
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)
        return cls(
            access_token=data.get("access_token", ""),
            refresh_token=data.get("refresh_token", ""),
            token_type=data.get("token_type", "Bearer"),
            expires_at=expires_at,
            scope=data.get("scope", ""),
        )


class GoogleAPIClient:
    """
    Async client for Google APIs with automatic token refresh.

    Handles OAuth 2.0 token management and provides methods for
    making authenticated requests to Google APIs using UnifiedHttpClient.
    """

    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

    def __init__(
        self,
        credentials: GoogleCredentials,
        client_id: str,
        client_secret: str,
    ) -> None:
        """
        Initialize Google API client.

        Args:
            credentials: OAuth credentials
            client_id: Google OAuth client ID
            client_secret: Google OAuth client secret
        """
        self._credentials = credentials
        self._client_id = client_id
        self._client_secret = client_secret
        self._http_client: UnifiedHttpClient | None = None
        self._lock = asyncio.Lock()

    @property
    def credentials(self) -> GoogleCredentials:
        """Get current credentials."""
        return self._credentials

    async def __aenter__(self) -> "GoogleAPIClient":
        """Enter async context."""
        config = UnifiedHttpClientConfig(
            default_timeout=30.0,
            max_retries=2,
            enable_ssrf_protection=False,  # Google APIs are trusted
        )
        self._http_client = UnifiedHttpClient(config)
        await self._http_client.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context."""
        if self._http_client:
            await self._http_client.close()
            self._http_client = None

    async def _ensure_client(self) -> UnifiedHttpClient:
        """Ensure HTTP client is available."""
        if self._http_client is None:
            config = UnifiedHttpClientConfig(
                default_timeout=30.0,
                max_retries=2,
                enable_ssrf_protection=False,
            )
            self._http_client = UnifiedHttpClient(config)
            await self._http_client.start()
        return self._http_client

    async def refresh_token(self) -> bool:
        """
        Refresh the access token using the refresh token.

        Returns:
            True if refresh succeeded, False otherwise
        """
        if not self._credentials.refresh_token:
            logger.error("No refresh token available")
            return False

        client = await self._ensure_client()

        try:
            async with self._lock:
                data = {
                    "grant_type": "refresh_token",
                    "refresh_token": self._credentials.refresh_token,
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                }

                response = await client.post(self.GOOGLE_TOKEN_URL, data=data)

                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Token refresh failed: {error_text}")
                    response.release()
                    return False

                token_data = await response.json()

                # Update credentials
                self._credentials.access_token = token_data["access_token"]
                self._credentials.token_type = token_data.get("token_type", "Bearer")

                # Calculate expiration time
                expires_in = token_data.get("expires_in", 3600)
                self._credentials.expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)

                # Update refresh token if provided
                if "refresh_token" in token_data:
                    self._credentials.refresh_token = token_data["refresh_token"]

                if "scope" in token_data:
                    self._credentials.scope = token_data["scope"]

                logger.debug("Google OAuth token refreshed successfully")
                return True

        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return False

    async def ensure_valid_token(self) -> bool:
        """
        Ensure access token is valid, refreshing if needed.

        Returns:
            True if token is valid, False otherwise
        """
        if not self._credentials.is_expired:
            return True
        return await self.refresh_token()

    async def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Make authenticated GET request.

        Args:
            url: Request URL
            params: Query parameters
            headers: Additional headers

        Returns:
            JSON response data

        Raises:
            Exception: On request failure
            ValueError: On authentication failure
        """
        if not await self.ensure_valid_token():
            raise ValueError("Failed to obtain valid access token")

        client = await self._ensure_client()
        request_headers = headers or {}
        request_headers["Authorization"] = (
            f"{self._credentials.token_type} {self._credentials.access_token}"
        )

        response = await client.get(url, params=params, headers=request_headers)

        try:
            if response.status == 401:
                # Token might have expired, try refresh
                if await self.refresh_token():
                    token = self._credentials.access_token
                    request_headers["Authorization"] = f"{self._credentials.token_type} {token}"
                    retry_response = await client.get(url, params=params, headers=request_headers)
                    try:
                        if retry_response.status != 200:
                            text = await retry_response.text()
                            raise ValueError(f"Google API error: {retry_response.status} - {text}")
                        return await retry_response.json()
                    finally:
                        retry_response.release()
                else:
                    response.release()
                    raise ValueError("Authentication failed after token refresh")

            if response.status != 200:
                text = await response.text()
                response.release()
                raise ValueError(f"Google API error: {response.status} - {text}")

            return await response.json()
        finally:
            if response.status != 401:  # Already released in retry path
                response.release()

    async def post(
        self,
        url: str,
        json_data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Make authenticated POST request.

        Args:
            url: Request URL
            json_data: JSON body data
            headers: Additional headers

        Returns:
            JSON response data

        Raises:
            Exception: On request failure
            ValueError: On authentication failure
        """
        if not await self.ensure_valid_token():
            raise ValueError("Failed to obtain valid access token")

        client = await self._ensure_client()
        request_headers = headers or {}
        request_headers["Authorization"] = (
            f"{self._credentials.token_type} {self._credentials.access_token}"
        )
        request_headers["Content-Type"] = "application/json"

        response = await client.post(url, json=json_data, headers=request_headers)

        try:
            if response.status == 401:
                if await self.refresh_token():
                    token = self._credentials.access_token
                    request_headers["Authorization"] = f"{self._credentials.token_type} {token}"
                    retry_response = await client.post(url, json=json_data, headers=request_headers)
                    try:
                        if retry_response.status not in (200, 201):
                            text = await retry_response.text()
                            raise ValueError(f"Google API error: {retry_response.status} - {text}")
                        return await retry_response.json()
                    finally:
                        retry_response.release()
                else:
                    response.release()
                    raise ValueError("Authentication failed after token refresh")

            if response.status not in (200, 201):
                text = await response.text()
                response.release()
                raise ValueError(f"Google API error: {response.status} - {text}")

            return await response.json()
        finally:
            if response.status != 401:
                response.release()

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._http_client:
            await self._http_client.close()
            self._http_client = None


class GoogleTriggerBase(BaseTrigger):
    """
    Base class for Google Workspace triggers with shared OAuth logic.

    Subclasses must implement:
    - _poll(): Poll for changes (for polling-based triggers)
    - get_required_scopes(): Return required OAuth scopes

    Configuration options (shared):
        client_id: Google OAuth client ID
        client_secret_credential: Credential alias for client secret
        access_token: Initial access token (or from credential)
        refresh_token: Refresh token (or from credential)
        access_token_credential: Credential alias for access token
        refresh_token_credential: Credential alias for refresh token
    """

    # OAuth 2.0 endpoints
    GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

    def __init__(self, config: BaseTriggerConfig, event_callback=None):
        super().__init__(config, event_callback)
        self._client: GoogleAPIClient | None = None
        self._poll_task: asyncio.Task | None = None
        self._running = False

    @abstractmethod
    def get_required_scopes(self) -> list[str]:
        """
        Get required OAuth scopes for this trigger.

        Returns:
            List of required scope URLs
        """
        pass

    def _get_credential_config(self) -> dict[str, Any]:
        """
        Get credential configuration from secrets manager.

        Returns:
            Dictionary with resolved credentials

        Raises:
            ValueError: If required credentials are missing
        """
        config = self.config.config
        result = {}

        # Get client ID
        client_id = config.get("client_id", "")
        if not client_id:
            client_id_credential = config.get("client_id_credential", "")
            if client_id_credential:
                client_id = self._get_secret(client_id_credential)
        if not client_id:
            raise ValueError("Google OAuth client_id is required")
        result["client_id"] = client_id

        # Get client secret
        client_secret = config.get("client_secret", "")
        client_secret_credential = config.get("client_secret_credential", "")
        if client_secret_credential:
            client_secret = self._get_secret(client_secret_credential)
        if not client_secret:
            raise ValueError("Google OAuth client_secret is required")
        result["client_secret"] = client_secret

        # Get access token
        access_token = config.get("access_token", "")
        access_token_credential = config.get("access_token_credential", "")
        if access_token_credential:
            access_token = self._get_secret(access_token_credential)
        result["access_token"] = access_token

        # Get refresh token
        refresh_token = config.get("refresh_token", "")
        refresh_token_credential = config.get("refresh_token_credential", "")
        if refresh_token_credential:
            refresh_token = self._get_secret(refresh_token_credential)
        if not refresh_token and not access_token:
            msg = "Either access_token or refresh_token is required"
            raise ValueError(msg)
        result["refresh_token"] = refresh_token

        return result

    def _get_secret(self, credential_name: str) -> str:
        """
        Get secret from vault or secrets manager.

        Resolution order:
        1. Vault credential provider (async, but run synchronously for compat)
        2. Legacy secrets manager

        Args:
            credential_name: Name of the credential to retrieve

        Returns:
            Secret value or empty string if not found
        """
        # Try vault credential provider first
        try:
            import asyncio

            from casare_rpa.infrastructure.security.credential_provider import (
                VaultCredentialProvider,
            )

            async def _get_from_vault():
                provider = VaultCredentialProvider()
                await provider.initialize()
                try:
                    cred = await provider.get_credential(credential_name)
                    if cred:
                        # Try common field names
                        for field in [
                            "value",
                            "secret",
                            "api_key",
                            "access_token",
                            "client_secret",
                        ]:
                            val = getattr(cred, field, None)
                            if val:
                                return val
                            if hasattr(cred, "data") and cred.data:
                                val = cred.data.get(field)
                                if val:
                                    return val
                    return None
                finally:
                    await provider.shutdown()

            # Try to get event loop, or create one
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Can't run sync in async context, skip vault
                    pass
                else:
                    result = loop.run_until_complete(_get_from_vault())
                    if result:
                        logger.debug(f"Using vault credential: {credential_name}")
                        return result
            except RuntimeError:
                # No event loop, create new one
                result = asyncio.run(_get_from_vault())
                if result:
                    logger.debug(f"Using vault credential: {credential_name}")
                    return result
        except ImportError:
            logger.debug("Vault credential provider not available")
        except Exception as e:
            logger.debug(f"Vault lookup failed: {e}")

        # Fallback to legacy secrets manager
        try:
            from casare_rpa.utils.security.secrets_manager import get_secrets_manager

            secrets = get_secrets_manager()
            value = secrets.get(credential_name, "")
            if not value:
                logger.warning(f"Credential '{credential_name}' not found in secrets manager")
            return value
        except ImportError:
            logger.error("Secrets manager not available")
            return ""

    async def _get_google_client(self) -> GoogleAPIClient:
        """
        Get or create Google API client.

        Returns:
            Authenticated GoogleAPIClient instance

        Raises:
            ValueError: If authentication fails
        """
        if self._client is not None:
            return self._client

        creds = self._get_credential_config()

        credentials = GoogleCredentials(
            access_token=creds["access_token"],
            refresh_token=creds["refresh_token"],
        )

        self._client = GoogleAPIClient(
            credentials=credentials,
            client_id=creds["client_id"],
            client_secret=creds["client_secret"],
        )

        return self._client

    async def _authenticate(self) -> bool:
        """
        Authenticate with Google APIs.

        Returns:
            True if authentication succeeds, False otherwise
        """
        try:
            client = await self._get_google_client()
            return await client.ensure_valid_token()
        except Exception as e:
            logger.error(f"Google authentication failed: {e}")
            self._error_message = str(e)
            return False

    async def start(self) -> bool:
        """Start the Google trigger."""
        valid, error = self.validate_config()
        if not valid:
            self._error_message = error
            self._status = TriggerStatus.ERROR
            return False

        if not await self._authenticate():
            self._status = TriggerStatus.ERROR
            return False

        self._running = True
        self._status = TriggerStatus.ACTIVE

        # Start polling task for polling-based triggers
        self._poll_task = asyncio.create_task(self._poll_loop())

        logger.info(f"Google trigger started: {self.config.name}")
        return True

    async def stop(self) -> bool:
        """Stop the Google trigger."""
        self._running = False

        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
            self._poll_task = None

        if self._client:
            await self._client.close()
            self._client = None

        self._status = TriggerStatus.INACTIVE
        logger.info(f"Google trigger stopped: {self.config.name}")
        return True

    async def _poll_loop(self) -> None:
        """Main polling loop."""
        config = self.config.config
        poll_interval = config.get("poll_interval", 60)

        # Initial delay to allow setup
        await asyncio.sleep(1)

        while self._running:
            try:
                await self._poll()
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error(f"Google trigger poll error: {e}")
                self._error_message = str(e)

            await asyncio.sleep(poll_interval)

    @abstractmethod
    async def _poll(self) -> None:
        """
        Poll for changes.

        Override in subclasses to implement polling logic.
        For webhook-based triggers (like Drive), this can be a no-op.
        """
        pass

    def validate_config(self) -> tuple[bool, str | None]:
        """Validate Google trigger configuration."""
        config = self.config.config

        # Check for credentials
        has_client_id = bool(config.get("client_id") or config.get("client_id_credential"))
        has_client_secret = bool(
            config.get("client_secret") or config.get("client_secret_credential")
        )

        if not has_client_id:
            return False, "client_id or client_id_credential is required"
        if not has_client_secret:
            return False, "client_secret or client_secret_credential is required"

        has_access_token = bool(config.get("access_token") or config.get("access_token_credential"))
        has_refresh_token = bool(
            config.get("refresh_token") or config.get("refresh_token_credential")
        )

        if not has_access_token and not has_refresh_token:
            return False, "access_token or refresh_token is required"

        poll_interval = config.get("poll_interval", 60)
        if poll_interval < 10:
            return False, "poll_interval must be at least 10 seconds"

        return True, None

    @classmethod
    def get_config_schema(cls) -> dict[str, Any]:
        """Get base JSON schema for Google trigger configuration."""
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Trigger name"},
                "enabled": {"type": "boolean", "default": True},
                "priority": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 3,
                    "default": 1,
                },
                "cooldown_seconds": {"type": "integer", "minimum": 0, "default": 0},
                "client_id": {
                    "type": "string",
                    "description": "Google OAuth client ID",
                },
                "client_id_credential": {
                    "type": "string",
                    "description": "Credential alias for Google OAuth client ID",
                },
                "client_secret_credential": {
                    "type": "string",
                    "description": "Credential alias for Google OAuth client secret",
                },
                "access_token_credential": {
                    "type": "string",
                    "description": "Credential alias for access token",
                },
                "refresh_token_credential": {
                    "type": "string",
                    "description": "Credential alias for refresh token",
                },
                "poll_interval": {
                    "type": "integer",
                    "minimum": 10,
                    "default": 60,
                    "description": "Polling interval in seconds",
                },
            },
            "required": ["name"],
        }


__all__ = [
    "GoogleCredentials",
    "GoogleAPIClient",
    "GoogleTriggerBase",
]
