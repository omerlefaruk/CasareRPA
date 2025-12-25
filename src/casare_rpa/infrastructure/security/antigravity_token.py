"""
Antigravity OAuth token refresh management.

Handles access token refresh using stored refresh tokens.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from loguru import logger

from casare_rpa.infrastructure.security.antigravity_constants import (
    ANTIGRAVITY_CLIENT_ID,
    ANTIGRAVITY_CLIENT_SECRET,
)
from casare_rpa.infrastructure.security.antigravity_oauth import (
    format_refresh_parts,
    parse_refresh_parts,
)


class AntigravityTokenRefreshError(Exception):
    def __init__(
        self,
        message: str,
        code: str | None = None,
        description: str | None = None,
        status: int = 0,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.description = description
        self.status = status


@dataclass
class AntigravityAuthDetails:
    refresh_token: str
    access_token: str | None = None
    expires_at: int | None = None

    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return True
        buffer_ms = 60_000
        return time.time() * 1000 >= (self.expires_at - buffer_ms)


def parse_oauth_error_payload(text: str | None) -> tuple[str | None, str | None]:
    if not text:
        return None, None

    try:
        import json

        payload = json.loads(text)
        if not isinstance(payload, dict):
            return None, text

        code: str | None = None
        error = payload.get("error")
        if isinstance(error, str):
            code = error
        elif isinstance(error, dict):
            code = error.get("status") or error.get("code")
            if not payload.get("error_description") and error.get("message"):
                return code, error.get("message")

        description = payload.get("error_description")
        if description:
            return code, description

        if isinstance(error, dict) and error.get("message"):
            return code, error.get("message")

        return code, None
    except Exception:
        return None, text


async def refresh_antigravity_token(auth: AntigravityAuthDetails) -> AntigravityAuthDetails | None:
    from casare_rpa.infrastructure.http import UnifiedHttpClient, UnifiedHttpClientConfig

    refresh_token, project_id, managed_project_id = parse_refresh_parts(auth.refresh_token)
    if not refresh_token:
        return None

    config = UnifiedHttpClientConfig(default_timeout=30.0, max_retries=2)

    try:
        async with UnifiedHttpClient(config) as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": ANTIGRAVITY_CLIENT_ID,
                    "client_secret": ANTIGRAVITY_CLIENT_SECRET,
                },
            )

            if response.status != 200:
                error_text = await response.text()
                code, description = parse_oauth_error_payload(error_text)
                details = ": ".join(filter(None, [code, description or error_text]))
                message = f"Antigravity token refresh failed ({response.status})"
                if details:
                    message = f"{message} - {details}"

                logger.warning(f"[Antigravity OAuth] {message}")

                if code == "invalid_grant":
                    logger.warning(
                        "[Antigravity OAuth] Google revoked the stored refresh token. "
                        "Reauthenticate via the settings dialog."
                    )

                raise AntigravityTokenRefreshError(
                    message=message,
                    code=code,
                    description=description or error_text,
                    status=response.status,
                )

            payload = await response.json()
            new_refresh = payload.get("refresh_token", refresh_token)
            expires_in = payload.get("expires_in", 3600)
            expires_at = int(time.time() * 1000) + (expires_in * 1000)

            return AntigravityAuthDetails(
                refresh_token=format_refresh_parts(new_refresh, project_id, managed_project_id),
                access_token=payload["access_token"],
                expires_at=expires_at,
            )

    except AntigravityTokenRefreshError:
        raise
    except Exception as e:
        logger.error(f"Failed to refresh Antigravity access token: {e}")
        return None


async def ensure_valid_token(auth: AntigravityAuthDetails) -> AntigravityAuthDetails:
    if not auth.is_expired and auth.access_token:
        return auth
    refreshed = await refresh_antigravity_token(auth)
    if not refreshed:
        raise AntigravityTokenRefreshError(
            message="Failed to refresh token",
            status=401,
        )
    return refreshed


__all__ = [
    "AntigravityTokenRefreshError",
    "AntigravityAuthDetails",
    "parse_oauth_error_payload",
    "refresh_antigravity_token",
    "ensure_valid_token",
]
