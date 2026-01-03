"""
Google API Client for CasareRPA

Async Google API client with OAuth 2.0 and credential caching.
Supports Gmail, Sheets, Docs, and Drive APIs.

Dependencies:
    - google-auth
    - google-auth-oauthlib
    - google-api-python-client
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from datetime import UTC
from enum import Enum
from pathlib import Path
from typing import Any

from loguru import logger

from casare_rpa.infrastructure.http import UnifiedHttpClient, UnifiedHttpClientConfig
from casare_rpa.utils.resilience.rate_limiter import (
    RateLimitExceeded,
    SlidingWindowRateLimiter,
)


class GoogleAPIError(Exception):
    """Exception raised for Google API errors."""

    def __init__(
        self,
        message: str,
        error_code: int | None = None,
        error_details: dict[str, Any] | None = None,
    ):
        self.error_code = error_code
        self.error_details = error_details or {}
        super().__init__(message)


class GoogleAuthError(GoogleAPIError):
    """Exception raised for authentication errors."""

    pass


class GoogleQuotaError(GoogleAPIError):
    """Exception raised when API quota is exceeded."""

    def __init__(
        self,
        message: str,
        retry_after: int | None = None,
        error_details: dict[str, Any] | None = None,
    ):
        self.retry_after = retry_after
        super().__init__(message, error_code=429, error_details=error_details)


class GoogleScope(Enum):
    """Google API OAuth2 scopes."""

    # Gmail
    GMAIL_READONLY = "https://www.googleapis.com/auth/gmail.readonly"
    GMAIL_MODIFY = "https://www.googleapis.com/auth/gmail.modify"
    GMAIL_COMPOSE = "https://www.googleapis.com/auth/gmail.compose"
    GMAIL_SEND = "https://www.googleapis.com/auth/gmail.send"

    # Sheets
    SHEETS_READONLY = "https://www.googleapis.com/auth/spreadsheets.readonly"
    SHEETS_FULL = "https://www.googleapis.com/auth/spreadsheets"

    # Docs
    DOCS_READONLY = "https://www.googleapis.com/auth/documents.readonly"
    DOCS_FULL = "https://www.googleapis.com/auth/documents"

    # Drive
    DRIVE_READONLY = "https://www.googleapis.com/auth/drive.readonly"
    DRIVE_FILE = "https://www.googleapis.com/auth/drive.file"
    DRIVE_FULL = "https://www.googleapis.com/auth/drive"

    # Calendar
    CALENDAR_READONLY = "https://www.googleapis.com/auth/calendar.readonly"
    CALENDAR_FULL = "https://www.googleapis.com/auth/calendar"
    CALENDAR_EVENTS = "https://www.googleapis.com/auth/calendar.events"

    # Generative AI (Gemini)
    GENERATIVE_LANGUAGE = "https://www.googleapis.com/auth/generative-language"
    GENERATIVE_LANGUAGE_RETRIEVER = "https://www.googleapis.com/auth/generative-language.retriever"
    CLOUD_PLATFORM = "https://www.googleapis.com/auth/cloud-platform"


# Scope shortcuts for common use cases
SCOPES = {
    "gmail": [GoogleScope.GMAIL_MODIFY.value],
    "gmail_readonly": [GoogleScope.GMAIL_READONLY.value],
    "gmail_send": [GoogleScope.GMAIL_SEND.value],
    "sheets": [GoogleScope.SHEETS_FULL.value],
    "sheets_readonly": [GoogleScope.SHEETS_READONLY.value],
    "docs": [GoogleScope.DOCS_FULL.value],
    "docs_readonly": [GoogleScope.DOCS_READONLY.value],
    "drive": [GoogleScope.DRIVE_FULL.value],
    "drive_readonly": [GoogleScope.DRIVE_READONLY.value],
    "drive_file": [GoogleScope.DRIVE_FILE.value],
    "calendar": [GoogleScope.CALENDAR_FULL.value],
    "calendar_readonly": [GoogleScope.CALENDAR_READONLY.value],
    "calendar_events": [GoogleScope.CALENDAR_EVENTS.value],
}


@dataclass
class GoogleCredentials:
    """OAuth2 credentials for Google APIs."""

    access_token: str
    refresh_token: str | None = None
    token_uri: str = "https://oauth2.googleapis.com/token"
    client_id: str | None = None
    client_secret: str | None = None
    scopes: list[str] = field(default_factory=list)
    expiry: float | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GoogleCredentials:
        """Create credentials from dictionary."""
        return cls(
            access_token=data.get("access_token", ""),
            refresh_token=data.get("refresh_token"),
            token_uri=data.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=data.get("client_id"),
            client_secret=data.get("client_secret"),
            scopes=data.get("scopes", []),
            expiry=data.get("expiry"),
        )

    @classmethod
    def from_service_account(cls, service_account_info: dict[str, Any]) -> GoogleCredentials:
        """Create credentials from service account JSON."""
        try:
            from google.oauth2 import service_account

            creds = service_account.Credentials.from_service_account_info(service_account_info)
            return cls(
                access_token=creds.token or "",
                token_uri=creds._token_uri,
                scopes=list(creds.scopes) if creds.scopes else [],
            )
        except ImportError:
            raise GoogleAuthError(
                "google-auth library not installed. "
                "Install with: pip install google-auth google-auth-oauthlib"
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert credentials to dictionary."""
        data = {
            "access_token": self.access_token,
            "token_uri": self.token_uri,
            "scopes": self.scopes,
        }
        if self.refresh_token:
            data["refresh_token"] = self.refresh_token
        if self.client_id:
            data["client_id"] = self.client_id
        if self.client_secret:
            data["client_secret"] = self.client_secret
        if self.expiry:
            data["expiry"] = self.expiry
        return data

    def is_expired(self) -> bool:
        """Check if the access token is expired."""
        if self.expiry is None:
            return False
        # Add 60 second buffer for token refresh
        return time.time() >= (self.expiry - 60)


@dataclass
class GoogleConfig:
    """Configuration for Google API client."""

    credentials: GoogleCredentials | None = None
    credential_id: str | None = None  # For OAuth auto-refresh via GoogleOAuthManager
    service_account_file: str | None = None
    service_account_info: dict[str, Any] | None = None
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    # Rate limiting: Google quotas vary by API, 10 req/s is conservative default
    rate_limit_requests: int = 10
    rate_limit_window: float = 1.0


class GoogleAPIClient:
    """
    Async Google API client with OAuth 2.0 and credential caching.

    Features:
    - OAuth 2.0 token refresh
    - Rate limiting (Google quotas: 10 req/s per user default)
    - Async HTTP via aiohttp
    - Service caching (reuse authenticated services)
    - Batch request support

    Usage:
        config = GoogleConfig(
            credentials=GoogleCredentials(access_token=os.getenv("GOOGLE_ACCESS_TOKEN", "ACCESS_TOKEN_HERE"))
        )
        client = GoogleAPIClient(config)

        async with client:
            # Execute Gmail API request
            result = await client.gmail.users().messages().list(userId="me")
    """

    BASE_URLS = {
        "gmail": "https://gmail.googleapis.com",
        "sheets": "https://sheets.googleapis.com",
        "docs": "https://docs.googleapis.com",
        "drive": "https://www.googleapis.com",
        "calendar": "https://www.googleapis.com",
    }

    API_VERSIONS = {
        "gmail": "v1",
        "sheets": "v4",
        "docs": "v1",
        "drive": "v3",
        "calendar": "v3",
    }

    def __init__(self, config: GoogleConfig):
        """
        Initialize the Google API client.

        Args:
            config: GoogleConfig with credentials and settings
        """
        self.config = config
        self._credentials: GoogleCredentials | None = config.credentials
        self._http_client: UnifiedHttpClient | None = None
        self._services: dict[str, Any] = {}
        self._rate_limiter = SlidingWindowRateLimiter(
            max_requests=config.rate_limit_requests,
            window_seconds=config.rate_limit_window,
            max_wait_time=60.0,
        )
        self._lock = asyncio.Lock()

    async def __aenter__(self) -> GoogleAPIClient:
        """Enter async context manager."""
        await self._ensure_http_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager."""
        await self.close()

    async def _ensure_http_client(self) -> UnifiedHttpClient:
        """Ensure HTTP client exists."""
        if self._http_client is None:
            http_config = UnifiedHttpClientConfig(
                default_timeout=self.config.timeout,
                max_retries=self.config.max_retries,
                retry_initial_delay=self.config.retry_delay,
                rate_limit_requests=self.config.rate_limit_requests,
                rate_limit_window=self.config.rate_limit_window,
            )
            self._http_client = UnifiedHttpClient(http_config)
            await self._http_client.start()
        return self._http_client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._http_client:
            await self._http_client.close()
            self._http_client = None
        self._services.clear()

    async def authenticate(
        self,
        scopes: list[str] | None = None,
        credentials: dict[str, Any] | None = None,
    ) -> None:
        """
        Authenticate with Google APIs.

        Supports multiple authentication methods:
        1. OAuth2 credentials (access_token, refresh_token)
        2. Service account (JSON file or dict)

        Args:
            scopes: List of OAuth2 scopes to request
            credentials: Credential dictionary override

        Raises:
            GoogleAuthError: If authentication fails
        """
        async with self._lock:
            if credentials:
                self._credentials = GoogleCredentials.from_dict(credentials)
                if scopes:
                    self._credentials.scopes = scopes
                logger.info("Authenticated with provided credentials")
                return

            # Try service account file
            if self.config.service_account_file:
                await self._authenticate_service_account_file(scopes or [])
                return

            # Try service account info dict
            if self.config.service_account_info:
                await self._authenticate_service_account_info(
                    self.config.service_account_info, scopes or []
                )
                return

            # Use existing credentials
            if self._credentials:
                if scopes and not self._credentials.scopes:
                    self._credentials.scopes = scopes
                logger.info("Using existing credentials")
                return

            raise GoogleAuthError(
                "No authentication method configured. "
                "Provide credentials, service_account_file, or service_account_info."
            )

    async def _authenticate_service_account_file(self, scopes: list[str]) -> None:
        """Authenticate using service account JSON file."""
        try:
            from google.oauth2 import service_account

            file_path = Path(self.config.service_account_file)
            if not file_path.exists():
                raise GoogleAuthError(f"Service account file not found: {file_path}")

            with open(file_path) as f:
                info = json.load(f)

            creds = service_account.Credentials.from_service_account_info(info, scopes=scopes)

            # Get access token
            from google.auth.transport.requests import Request

            creds.refresh(Request())

            self._credentials = GoogleCredentials(
                access_token=creds.token,
                token_uri=creds._token_uri,
                scopes=list(creds.scopes) if creds.scopes else scopes,
                expiry=creds.expiry.timestamp() if creds.expiry else None,
            )

            logger.info(
                f"Authenticated with service account: {info.get('client_email', 'unknown')}"
            )

        except ImportError:
            raise GoogleAuthError(
                "google-auth library not installed. "
                "Install with: pip install google-auth google-auth-oauthlib"
            )
        except Exception as e:
            raise GoogleAuthError(f"Service account authentication failed: {e}") from e

    async def _authenticate_service_account_info(
        self, info: dict[str, Any], scopes: list[str]
    ) -> None:
        """Authenticate using service account info dictionary."""
        try:
            from google.auth.transport.requests import Request
            from google.oauth2 import service_account

            creds = service_account.Credentials.from_service_account_info(info, scopes=scopes)

            # Get access token
            creds.refresh(Request())

            self._credentials = GoogleCredentials(
                access_token=creds.token,
                token_uri=creds._token_uri,
                scopes=list(creds.scopes) if creds.scopes else scopes,
                expiry=creds.expiry.timestamp() if creds.expiry else None,
            )

            logger.info(
                f"Authenticated with service account: {info.get('client_email', 'unknown')}"
            )

        except ImportError:
            raise GoogleAuthError(
                "google-auth library not installed. "
                "Install with: pip install google-auth google-auth-oauthlib"
            )
        except Exception as e:
            raise GoogleAuthError(f"Service account authentication failed: {e}") from e

    async def refresh_token(self) -> None:
        """
        Refresh the OAuth2 access token and persist to credential store.

        Uses GoogleOAuthManager if credential_id is available for centralized
        token management. Falls back to direct refresh if needed.

        Raises:
            GoogleAuthError: If token refresh fails or refresh_token not available
        """
        # Try to use GoogleOAuthManager for centralized refresh (recommended path)
        if self.config.credential_id:
            try:
                from casare_rpa.infrastructure.security.google_oauth import (
                    get_google_access_token,
                )

                logger.debug(f"Using GoogleOAuthManager to refresh: {self.config.credential_id}")
                new_token = await get_google_access_token(self.config.credential_id)
                self._credentials.access_token = new_token
                # The OAuth manager already persisted the refreshed tokens
                logger.info("OAuth2 token refreshed via GoogleOAuthManager")
                return
            except ImportError:
                logger.debug("GoogleOAuthManager not available, using direct refresh")
            except Exception as e:
                logger.warning(f"OAuth manager refresh failed, trying direct: {e}")

        # Direct refresh (fallback)
        if not self._credentials:
            raise GoogleAuthError("No credentials available to refresh")

        if not self._credentials.refresh_token:
            raise GoogleAuthError(
                "No refresh_token available. For service accounts, re-authenticate instead."
            )

        if not self._credentials.client_id or not self._credentials.client_secret:
            raise GoogleAuthError("client_id and client_secret required for token refresh")

        async with self._lock:
            try:
                http_client = await self._ensure_http_client()
                data = {
                    "grant_type": "refresh_token",
                    "refresh_token": self._credentials.refresh_token,
                    "client_id": self._credentials.client_id,
                    "client_secret": self._credentials.client_secret,
                }

                response = await http_client.post(
                    self._credentials.token_uri,
                    data=data,
                    skip_rate_limit=True,
                )
                result = await response.json()

                if "error" in result:
                    raise GoogleAuthError(
                        f"Token refresh failed: {result.get('error_description', result['error'])}"
                    )

                self._credentials.access_token = result["access_token"]
                if "refresh_token" in result:
                    self._credentials.refresh_token = result["refresh_token"]

                # Calculate expiry
                expires_in = result.get("expires_in", 3600)
                self._credentials.expiry = time.time() + expires_in

                logger.info("OAuth2 token refreshed successfully (direct)")

                # Persist refreshed tokens to credential store if credential_id available
                if self.config.credential_id:
                    await self._persist_refreshed_token(expires_in)

            except Exception as e:
                raise GoogleAuthError(f"Token refresh network error: {e}") from e

    async def _persist_refreshed_token(self, expires_in: int) -> None:
        """
        Persist refreshed tokens back to the credential store.

        Args:
            expires_in: Token expiry time in seconds
        """
        try:
            from datetime import datetime, timedelta

            from casare_rpa.infrastructure.security.credential_store import (
                CredentialType,
                get_credential_store,
            )

            store = get_credential_store()
            info = store.get_credential_info(self.config.credential_id)

            if info:
                # Build updated credential data
                token_expiry = datetime.now(UTC) + timedelta(seconds=expires_in)
                data = {
                    "client_id": self._credentials.client_id,
                    "client_secret": self._credentials.client_secret,
                    "access_token": self._credentials.access_token,
                    "refresh_token": self._credentials.refresh_token,
                    "token_expiry": token_expiry.isoformat(),
                    "scopes": self._credentials.scopes,
                }

                store.save_credential(
                    name=info["name"],
                    credential_type=CredentialType.GOOGLE_OAUTH_KIND,
                    category=info["category"],
                    data=data,
                    description=info.get("description", ""),
                    tags=info.get("tags", []),
                    credential_id=self.config.credential_id,
                )
                logger.debug(f"Persisted refreshed token: {self.config.credential_id}")

        except Exception as e:
            # Log but don't fail - the in-memory credentials have the new token
            logger.warning(f"Failed to persist refreshed token: {e}")

    async def _ensure_valid_token(self) -> str:
        """Ensure we have a valid access token, refreshing if needed."""
        if not self._credentials:
            raise GoogleAuthError("Not authenticated. Call authenticate() first.")

        if self._credentials.is_expired():
            logger.debug("Access token expired, refreshing...")
            await self.refresh_token()

        return self._credentials.access_token

    async def get_service(self, api: str, version: str | None = None) -> Any:
        """
        Get a Google API service client.

        Uses caching to reuse service instances.

        Args:
            api: API name (gmail, sheets, docs, drive)
            version: API version (defaults to standard version)

        Returns:
            Google API service resource

        Raises:
            GoogleAuthError: If not authenticated
            GoogleAPIError: If service creation fails
        """
        version = version or self.API_VERSIONS.get(api)
        if not version:
            raise GoogleAPIError(f"Unknown API: {api}")

        cache_key = f"{api}_{version}"

        if cache_key in self._services:
            return self._services[cache_key]

        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build

            # Ensure valid token
            await self._ensure_valid_token()

            # Create credentials object
            creds = Credentials(
                token=self._credentials.access_token,
                refresh_token=self._credentials.refresh_token,
                token_uri=self._credentials.token_uri,
                client_id=self._credentials.client_id,
                client_secret=self._credentials.client_secret,
            )

            # Build service
            service = build(api, version, credentials=creds)
            self._services[cache_key] = service

            logger.debug(f"Created {api} {version} service")
            return service

        except ImportError:
            raise GoogleAPIError(
                "google-api-python-client not installed. "
                "Install with: pip install google-api-python-client"
            )
        except Exception as e:
            raise GoogleAPIError(f"Failed to create {api} service: {e}") from e

    async def execute_request(
        self,
        request: Any,
        auto_retry: bool = True,
    ) -> dict[str, Any]:
        """
        Execute a Google API request with rate limiting and retry logic.

        Args:
            request: Google API request object (from service.method().method())
            auto_retry: Whether to retry on transient errors

        Returns:
            API response as dictionary

        Raises:
            GoogleAPIError: If request fails
            GoogleQuotaError: If quota exceeded
        """
        # Apply rate limiting
        try:
            await self._rate_limiter.acquire()
        except RateLimitExceeded as e:
            raise GoogleQuotaError(f"Client-side rate limit exceeded: {e}") from e

        last_error: Exception | None = None

        for attempt in range(self.config.max_retries):
            try:
                # Ensure valid token before each attempt
                await self._ensure_valid_token()

                # Execute request (sync, but runs in thread pool internally)
                result = await asyncio.get_event_loop().run_in_executor(None, request.execute)

                return result

            except Exception as e:
                last_error = e
                error_str = str(e).lower()

                # Check for quota errors
                if "quota" in error_str or "rate" in error_str:
                    retry_after = self._extract_retry_after(e)
                    raise GoogleQuotaError(
                        f"API quota exceeded: {e}",
                        retry_after=retry_after,
                    ) from e

                # Check for auth errors (don't retry)
                if "401" in error_str or "403" in error_str:
                    # Try token refresh once
                    if attempt == 0 and self._credentials and self._credentials.refresh_token:
                        logger.debug("Auth error, attempting token refresh...")
                        try:
                            await self.refresh_token()
                            continue
                        except GoogleAuthError:
                            pass
                    raise GoogleAuthError(f"Authentication failed: {e}") from e

                # Retry on transient errors
                if auto_retry and attempt < self.config.max_retries - 1:
                    wait_time = self.config.retry_delay * (2**attempt)
                    logger.warning(
                        f"Request failed (attempt {attempt + 1}/{self.config.max_retries}): {e}. "
                        f"Retrying in {wait_time:.1f}s..."
                    )
                    await asyncio.sleep(wait_time)
                else:
                    break

        raise GoogleAPIError(
            f"Request failed after {self.config.max_retries} attempts: {last_error}"
        )

    async def execute_batch(
        self,
        requests: list[Any],
        callback: Any | None = None,
    ) -> list[dict[str, Any]]:
        """
        Execute multiple requests as a batch.

        Args:
            requests: List of Google API request objects
            callback: Optional callback for each response

        Returns:
            List of API responses

        Raises:
            GoogleAPIError: If batch execution fails
        """
        if not requests:
            return []

        try:
            from googleapiclient.http import BatchHttpRequest

            results: list[dict[str, Any]] = []
            errors: list[Exception] = []

            def batch_callback(request_id, response, exception):
                if exception:
                    errors.append(exception)
                    results.append({"error": str(exception), "request_id": request_id})
                else:
                    results.append(response if response else {})
                if callback:
                    callback(request_id, response, exception)

            # Create batch request
            batch = BatchHttpRequest(callback=batch_callback)
            for i, request in enumerate(requests):
                batch.add(request, request_id=str(i))

            # Execute batch
            await asyncio.get_event_loop().run_in_executor(None, batch.execute)

            # Check for critical errors
            if len(errors) == len(requests):
                raise GoogleAPIError(f"All batch requests failed. First error: {errors[0]}")

            return results

        except ImportError:
            raise GoogleAPIError(
                "google-api-python-client not installed for batch requests"
            ) from None
        except Exception as e:
            raise GoogleAPIError(f"Batch request failed: {e}") from e

    def _extract_retry_after(self, error: Exception) -> int | None:
        """Extract retry-after value from error if present."""
        error_str = str(error)
        # Try to find retry-after in error message
        if "retry" in error_str.lower():
            import re

            match = re.search(r"(\d+)\s*second", error_str.lower())
            if match:
                return int(match.group(1))
        return None

    # =========================================================================
    # Convenience Properties for API Access
    # =========================================================================

    @property
    def credentials(self) -> GoogleCredentials | None:
        """Get current credentials."""
        return self._credentials

    @property
    def is_authenticated(self) -> bool:
        """Check if client is authenticated."""
        return self._credentials is not None and bool(self._credentials.access_token)

    @property
    def rate_limit_stats(self) -> dict[str, Any]:
        """Get rate limiting statistics."""
        return self._rate_limiter.stats.to_dict()


# Factory function for easy client creation
async def create_google_client(
    credentials: dict[str, Any] | None = None,
    service_account_file: str | None = None,
    service_account_info: dict[str, Any] | None = None,
    scopes: list[str] | None = None,
) -> GoogleAPIClient:
    """
    Factory function to create and authenticate a Google API client.

    Args:
        credentials: OAuth2 credentials dictionary
        service_account_file: Path to service account JSON file
        service_account_info: Service account info as dictionary
        scopes: List of OAuth2 scopes

    Returns:
        Authenticated GoogleAPIClient

    Example:
        client = await create_google_client(
            service_account_file="service-account.json",
            scopes=SCOPES["gmail"]
        )
    """
    config = GoogleConfig(
        credentials=GoogleCredentials.from_dict(credentials) if credentials else None,
        service_account_file=service_account_file,
        service_account_info=service_account_info,
    )

    client = GoogleAPIClient(config)
    await client.authenticate(scopes=scopes)
    return client


__all__ = [
    "GoogleAPIClient",
    "GoogleConfig",
    "GoogleCredentials",
    "GoogleScope",
    "GoogleAPIError",
    "GoogleAuthError",
    "GoogleQuotaError",
    "SCOPES",
    "create_google_client",
]
