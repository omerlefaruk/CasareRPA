"""Orchestrator HTTP client adapter.

Implements the `HttpClient` protocol expected by
`casare_rpa.application.services.orchestrator_client.OrchestratorClient`
using the unified infrastructure HTTP client.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from casare_rpa.infrastructure.http.unified_http_client import (
    UnifiedHttpClient,
    UnifiedHttpClientConfig,
)


class OrchestratorHttpClientAdapter:
    """Adapter for UnifiedHttpClient (local Orchestrator API communication)."""

    def __init__(self) -> None:
        config = UnifiedHttpClientConfig(
            default_timeout=30.0,
            connect_timeout=10.0,
            max_retries=3,
            enable_ssrf_protection=True,
            allow_private_ips=True,
        )
        self._client = UnifiedHttpClient(config)

    async def post(self, url: str, json: dict[str, Any]) -> tuple[int, dict[str, Any], str]:
        try:
            response = await self._client.post(url, json=json)
            status = response.status
            try:
                json_response = await response.json()
            except Exception:
                json_response = {}
            error_text = await response.text() if status != 200 else ""
            return status, json_response, error_text
        except Exception as e:
            logger.error(f"HTTP request failed: {e}")
            raise ConnectionError(f"HTTP request failed: {e}") from e

    async def close(self) -> None:
        await self._client.close()
