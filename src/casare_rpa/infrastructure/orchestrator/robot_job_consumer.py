from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import urljoin

from loguru import logger

from casare_rpa.infrastructure.http import (
    UnifiedHttpClient,
    UnifiedHttpClientConfig,
)


@dataclass(frozen=True)
class OrchestratorJobConsumerConfig:
    base_url: str
    api_key: str
    environment: str = "default"
    visibility_timeout_seconds: int = 30
    timeout_seconds: float = 30.0


@dataclass(frozen=True)
class ClaimedJob:
    job_id: str
    workflow_id: str
    workflow_name: str
    workflow_json: str
    priority: int
    environment: str
    variables: dict[str, Any]
    created_at: datetime
    claimed_at: datetime
    retry_count: int
    max_retries: int


class OrchestratorJobConsumer:
    """Robot-side consumer that uses Orchestrator REST endpoints (no direct DB)."""

    def __init__(self, config: OrchestratorJobConsumerConfig) -> None:
        self._config = config
        self._client: UnifiedHttpClient | None = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        async with self._lock:
            if self._client is not None:
                return
            http_config = UnifiedHttpClientConfig(
                enable_ssrf_protection=False,  # Internal orchestrator communication
                max_retries=2,
                default_timeout=self._config.timeout_seconds,
                default_headers={"X-Api-Key": self._config.api_key},
            )
            self._client = UnifiedHttpClient(http_config)
            await self._client.start()

    async def stop(self) -> None:
        async with self._lock:
            client = self._client
            self._client = None
        if client is not None:
            try:
                await client.close()
            except Exception as e:
                logger.debug(f"Error closing orchestrator consumer client: {e}")

    async def claim_job(self) -> ClaimedJob | None:
        client = self._client
        if client is None:
            await self.start()
            client = self._client
        if client is None:
            return None

        try:
            url = urljoin(self._config.base_url, "/api/v1/jobs/claim")
            response = await client.post(
                url,
                json={
                    "environment": self._config.environment,
                    "limit": 1,
                    "visibility_timeout_seconds": self._config.visibility_timeout_seconds,
                },
            )
            if response.status == 200:
                data = await response.json()
                if not data:
                    return None

                return ClaimedJob(
                    job_id=data["job_id"],
                    workflow_id=data.get("workflow_id") or "",
                    workflow_name=data.get("workflow_name") or "",
                    workflow_json=data.get("workflow_json") or "",
                    priority=int(data.get("priority") or 0),
                    environment=data.get("environment") or "default",
                    variables=data.get("variables") or {},
                    created_at=datetime.fromisoformat(
                        str(data["created_at"]).replace("Z", "+00:00")
                    ),
                    claimed_at=datetime.fromisoformat(
                        str(data["claimed_at"]).replace("Z", "+00:00")
                    ),
                    retry_count=int(data.get("retry_count") or 0),
                    max_retries=int(data.get("max_retries") or 0),
                )

            text = await response.text()
            logger.warning(f"Orchestrator claim_job failed: {response.status} {text[:200]}")
            return None

        except Exception as e:
            logger.warning(f"Orchestrator claim_job error: {e}")
            return None

    async def complete_job(self, job_id: str, result: dict[str, Any]) -> bool:
        client = self._client
        if client is None:
            await self.start()
            client = self._client
        if client is None:
            return False

        try:
            url = urljoin(self._config.base_url, f"/api/v1/jobs/{job_id}/complete")
            response = await client.post(url, json={"result": result})
            if response.status == 200:
                return True
            text = await response.text()
            logger.warning(
                f"Orchestrator complete_job failed: {response.status} job={job_id} {text[:200]}"
            )
            return False

        except Exception as e:
            logger.warning(f"Orchestrator complete_job error: {e}")
            return False

    async def fail_job(self, job_id: str, error_message: str) -> bool:
        client = self._client
        if client is None:
            await self.start()
            client = self._client
        if client is None:
            return False

        try:
            url = urljoin(self._config.base_url, f"/api/v1/jobs/{job_id}/fail")
            response = await client.post(url, json={"error_message": error_message})
            if response.status == 200:
                return True
            text = await response.text()
            logger.warning(
                f"Orchestrator fail_job failed: {response.status} job={job_id} {text[:200]}"
            )
            return False

        except Exception as e:
            logger.warning(f"Orchestrator fail_job error: {e}")
            return False

    async def release_job(self, job_id: str) -> bool:
        client = self._client
        if client is None:
            await self.start()
            client = self._client
        if client is None:
            return False

        try:
            url = urljoin(self._config.base_url, f"/api/v1/jobs/{job_id}/release")
            response = await client.post(url)
            if response.status == 200:
                return True
            text = await response.text()
            logger.warning(
                f"Orchestrator release_job failed: {response.status} job={job_id} {text[:200]}"
            )
            return False

        except Exception as e:
            logger.warning(f"Orchestrator release_job error: {e}")
            return False

    async def extend_lease(self, job_id: str, extension_seconds: int = 30) -> bool:
        client = self._client
        if client is None:
            await self.start()
            client = self._client
        if client is None:
            return False

        try:
            url = urljoin(self._config.base_url, f"/api/v1/jobs/{job_id}/extend-lease")
            response = await client.post(
                url,
                json={"extension_seconds": int(extension_seconds)},
            )
            if response.status == 200:
                return True
            text = await response.text()
            logger.warning(
                f"Orchestrator extend_lease failed: {response.status} job={job_id} {text[:200]}"
            )
            return False

        except Exception as e:
            logger.warning(f"Orchestrator extend_lease error: {e}")
            return False

    async def update_progress(self, job_id: str, progress: int, current_node: str) -> bool:
        # Progress reporting is optional; keep robot execution robust even if
        # the orchestrator deployment doesn't support progress persistence yet.
        return True
