"""
CasareRPA - OpenAI / Azure OAuth Credential Management

Provides OAuth 2.0 credential handling for OpenAI (Enterprise/Azure) APIs:
- OpenAIOAuthCredentialData: Dataclass for OAuth tokens
- OpenAIOAuthManager: Singleton for token refresh

Integrates with CredentialStore.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from loguru import logger


class OpenAIOAuthError(Exception):
    """Base exception for OpenAI OAuth errors."""

    pass


class TokenRefreshError(OpenAIOAuthError):
    """Exception raised when token refresh fails."""

    pass


class InvalidCredentialError(OpenAIOAuthError):
    """Exception raised when credential data is invalid."""

    pass


# Token expiry buffer
TOKEN_EXPIRY_BUFFER_SECONDS = 300


@dataclass
class OpenAIOAuthCredentialData:
    """
    OAuth 2.0 credential data for OpenAI/Azure.
    """

    client_id: str
    client_secret: str
    authorization_url: str
    token_url: str
    access_token: str
    refresh_token: str
    token_expiry: datetime | None = None
    scopes: list[str] = field(default_factory=list)
    tenant_id: str | None = None  # For Azure

    def is_expired(self, buffer_seconds: int = TOKEN_EXPIRY_BUFFER_SECONDS) -> bool:
        if self.token_expiry is None:
            return True
        now = datetime.now(UTC)
        expiry = self.token_expiry
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=UTC)
        return now >= (expiry - timedelta(seconds=buffer_seconds))

    def to_dict(self) -> dict[str, Any]:
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "authorization_url": self.authorization_url,
            "token_url": self.token_url,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "scopes": self.scopes,
        }
        if self.token_expiry:
            expiry = self.token_expiry
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=UTC)
            data["token_expiry"] = expiry.isoformat()
        if self.tenant_id:
            data["tenant_id"] = self.tenant_id
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OpenAIOAuthCredentialData:
        required = ["client_id", "client_secret", "token_url", "access_token"]
        if not all(k in data for k in required):
            raise InvalidCredentialError(f"Missing fields: {required}")

        token_expiry = None
        if data.get("token_expiry"):
            try:
                token_expiry = datetime.fromisoformat(data["token_expiry"])
                if token_expiry.tzinfo is None:
                    token_expiry = token_expiry.replace(tzinfo=UTC)
            except ValueError:
                pass

        return cls(
            client_id=data["client_id"],
            client_secret=data["client_secret"],
            authorization_url=data.get("authorization_url", ""),
            token_url=data["token_url"],
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", ""),
            token_expiry=token_expiry,
            scopes=data.get("scopes", []),
            tenant_id=data.get("tenant_id"),
        )


class OpenAIOAuthManager:
    """
    Singleton manager for OpenAI/Azure OAuth credentials.
    """

    _instance: OpenAIOAuthManager | None = None
    _lock: asyncio.Lock = asyncio.Lock()

    def __init__(self) -> None:
        self._credential_cache: dict[str, OpenAIOAuthCredentialData] = {}
        self._refresh_locks: dict[str, asyncio.Lock] = {}

    @classmethod
    async def get_instance(cls) -> OpenAIOAuthManager:
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    async def get_access_token(self, credential_id: str) -> str:
        """Get valid access token, refreshing if needed."""
        # Load credential
        if credential_id in self._credential_cache:
            cred = self._credential_cache[credential_id]
        else:
            cred = await self._load_credential(credential_id)

        if cred.is_expired():
            # Refresh
            lock = self._get_refresh_lock(credential_id)
            async with lock:
                # Double check
                if cred.is_expired():
                    cred = await self._refresh_token(credential_id, cred)

        return cred.access_token

    def _get_refresh_lock(self, credential_id: str) -> asyncio.Lock:
        if credential_id not in self._refresh_locks:
            self._refresh_locks[credential_id] = asyncio.Lock()
        return self._refresh_locks[credential_id]

    async def _load_credential(self, credential_id: str) -> OpenAIOAuthCredentialData:
        from casare_rpa.infrastructure.security.credential_store import get_credential_store

        store = get_credential_store()
        raw = store.get_credential(credential_id)
        if not raw:
            raise InvalidCredentialError(f"Credential {credential_id} not found")

        cred = OpenAIOAuthCredentialData.from_dict(raw)
        self._credential_cache[credential_id] = cred
        return cred

    async def _refresh_token(
        self, credential_id: str, cred: OpenAIOAuthCredentialData
    ) -> OpenAIOAuthCredentialData:
        if not cred.refresh_token:
            raise TokenRefreshError("No refresh token available")

        logger.info(f"Refreshing OAuth token for {credential_id}")

        from casare_rpa.infrastructure.http import UnifiedHttpClient, UnifiedHttpClientConfig

        config = UnifiedHttpClientConfig(
            enable_ssrf_protection=True,
            max_retries=2,
            default_timeout=30.0,
        )

        try:
            data = {
                "grant_type": "refresh_token",
                "refresh_token": cred.refresh_token,
                "client_id": cred.client_id,
                "client_secret": cred.client_secret,
            }

            async with UnifiedHttpClient(config) as http_client:
                resp = await http_client.post(
                    cred.token_url,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                result = await resp.json()

                if "error" in result:
                    raise TokenRefreshError(
                        f"Refresh failed: {result.get('error_description', result['error'])}"
                    )

                cred.access_token = result["access_token"]
                if "refresh_token" in result:
                    cred.refresh_token = result["refresh_token"]

                expires_in = result.get("expires_in", 3600)
                cred.token_expiry = datetime.now(UTC) + timedelta(seconds=expires_in)

                self._credential_cache[credential_id] = cred
                await self._persist_credential(credential_id, cred)
                return cred

        except TokenRefreshError:
            raise
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise TokenRefreshError(str(e))

    async def _persist_credential(
        self, credential_id: str, cred: OpenAIOAuthCredentialData
    ) -> None:
        from casare_rpa.infrastructure.security.credential_store import (
            CredentialType,
            get_credential_store,
        )

        store = get_credential_store()
        info = store.get_credential_info(credential_id)
        if info:
            store.save_credential(
                name=info["name"],
                credential_type=CredentialType.OPENAI_OAUTH_KIND,
                category="openai_oauth",
                data=cred.to_dict(),
                description=info.get("description", ""),
                credential_id=credential_id,
            )


async def get_openai_oauth_manager() -> OpenAIOAuthManager:
    return await OpenAIOAuthManager.get_instance()
