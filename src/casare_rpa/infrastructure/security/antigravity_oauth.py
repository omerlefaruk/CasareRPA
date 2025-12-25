"""
Antigravity OAuth 2.0 authentication flow with PKCE.

Provides OAuth authorization and token exchange for accessing
Google's Antigravity API (Cloud Code Assist).
"""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
from dataclasses import dataclass
from typing import TYPE_CHECKING
from urllib.parse import urlencode

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

if TYPE_CHECKING:
    from typing import Any


@dataclass
class PKCEPair:
    verifier: str
    challenge: str


@dataclass
class AntigravityAuthState:
    verifier: str
    project_id: str


@dataclass
class AntigravityAuthorization:
    url: str
    verifier: str
    project_id: str


@dataclass
class AntigravityTokenSuccess:
    refresh_token: str
    access_token: str
    expires_at: int
    email: str | None
    project_id: str


@dataclass
class AntigravityTokenFailure:
    error: str


AntigravityTokenResult = AntigravityTokenSuccess | AntigravityTokenFailure


def generate_pkce_pair() -> PKCEPair:
    verifier = secrets.token_urlsafe(32)
    challenge_bytes = hashlib.sha256(verifier.encode("utf-8")).digest()
    challenge = base64.urlsafe_b64encode(challenge_bytes).rstrip(b"=").decode("utf-8")
    return PKCEPair(verifier=verifier, challenge=challenge)


def encode_state(state: AntigravityAuthState) -> str:
    payload = {"verifier": state.verifier, "projectId": state.project_id}
    return base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")


def decode_state(state_str: str) -> AntigravityAuthState:
    normalized = state_str.replace("-", "+").replace("_", "/")
    padding = (4 - len(normalized) % 4) % 4
    padded = normalized + "=" * padding
    json_str = base64.b64decode(padded).decode("utf-8")
    data = json.loads(json_str)

    if not isinstance(data.get("verifier"), str):
        raise ValueError("Missing PKCE verifier in state")

    return AntigravityAuthState(
        verifier=data["verifier"],
        project_id=data.get("projectId", ""),
    )


def build_antigravity_auth_url(project_id: str = "") -> AntigravityAuthorization:
    pkce = generate_pkce_pair()
    state = encode_state(AntigravityAuthState(verifier=pkce.verifier, project_id=project_id))

    params = {
        "client_id": ANTIGRAVITY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": ANTIGRAVITY_REDIRECT_URI,
        "scope": " ".join(ANTIGRAVITY_SCOPES),
        "code_challenge": pkce.challenge,
        "code_challenge_method": "S256",
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }

    url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

    return AntigravityAuthorization(
        url=url,
        verifier=pkce.verifier,
        project_id=project_id,
    )


async def fetch_project_id(access_token: str) -> str:
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
    import time

    from casare_rpa.infrastructure.http import UnifiedHttpClient, UnifiedHttpClientConfig

    try:
        auth_state = decode_state(state)
    except Exception as e:
        return AntigravityTokenFailure(error=f"Invalid state: {e}")

    config = UnifiedHttpClientConfig(default_timeout=30.0, max_retries=2)

    try:
        async with UnifiedHttpClient(config) as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "client_id": ANTIGRAVITY_CLIENT_ID,
                    "client_secret": ANTIGRAVITY_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": ANTIGRAVITY_REDIRECT_URI,
                    "code_verifier": auth_state.verifier,
                },
            )

            if token_response.status != 200:
                error_text = await token_response.text()
                return AntigravityTokenFailure(error=error_text)

            token_data = await token_response.json()

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

            project_id = auth_state.project_id
            if not project_id:
                project_id = await fetch_project_id(token_data["access_token"])

            expires_in = token_data.get("expires_in", 3600)
            expires_at = int(time.time() * 1000) + (expires_in * 1000)

            stored_refresh = f"{refresh_token}|{project_id or ''}"

            return AntigravityTokenSuccess(
                refresh_token=stored_refresh,
                access_token=token_data["access_token"],
                expires_at=expires_at,
                email=user_email,
                project_id=project_id or "",
            )

    except Exception as e:
        return AntigravityTokenFailure(error=str(e))


def parse_refresh_parts(refresh_token: str) -> tuple[str, str, str | None]:
    parts = refresh_token.split("|")
    token = parts[0] if len(parts) > 0 else ""
    project_id = parts[1] if len(parts) > 1 else ""
    managed_project_id = parts[2] if len(parts) > 2 else None
    return token, project_id, managed_project_id


def format_refresh_parts(token: str, project_id: str, managed_project_id: str | None = None) -> str:
    if managed_project_id:
        return f"{token}|{project_id}|{managed_project_id}"
    if project_id:
        return f"{token}|{project_id}"
    return token


__all__ = [
    "PKCEPair",
    "AntigravityAuthState",
    "AntigravityAuthorization",
    "AntigravityTokenSuccess",
    "AntigravityTokenFailure",
    "AntigravityTokenResult",
    "generate_pkce_pair",
    "encode_state",
    "decode_state",
    "build_antigravity_auth_url",
    "fetch_project_id",
    "exchange_antigravity_token",
    "parse_refresh_parts",
    "format_refresh_parts",
]
