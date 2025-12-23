from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import aiohttp
from loguru import logger


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
        self._session: aiohttp.ClientSession | None = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        async with self._lock:
            if self._session is not None:
                return
            timeout = aiohttp.ClientTimeout(total=self._config.timeout_seconds)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers={"X-Api-Key": self._config.api_key},
            )

    async def stop(self) -> None:
        async with self._lock:
            session = self._session
            self._session = None
        if session is not None:
            try:
                await session.close()
            except Exception as e:
                logger.debug(f"Error closing orchestrator consumer session: {e}")

    async def claim_job(self) -> ClaimedJob | None:
        session = self._session
        if session is None:
            await self.start()
            session = self._session
        if session is None:
            return None

        try:
            url = urljoin(self._config.base_url, "/api/v1/jobs/claim")
            async with session.post(
                url,
                json={
                    "environment": self._config.environment,
                    "limit": 1,
                    "visibility_timeout_seconds": self._config.visibility_timeout_seconds,
                },
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
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

                text = await resp.text()
                logger.warning(f"Orchestrator claim_job failed: {resp.status} {text[:200]}")
                return None

        except aiohttp.ClientError as e:
            logger.warning(f"Orchestrator claim_job client error: {e}")
            return None
        except Exception as e:
            logger.exception(f"Orchestrator claim_job unexpected error: {e}")
            return None

    async def complete_job(self, job_id: str, result: dict[str, Any]) -> bool:
        session = self._session
        if session is None:
            await self.start()
            session = self._session
        if session is None:
            return False

        try:
            url = urljoin(self._config.base_url, f"/api/v1/jobs/{job_id}/complete")
            async with session.post(url, json={"result": result}) as resp:
                if resp.status == 200:
                    return True
                text = await resp.text()
                logger.warning(
                    f"Orchestrator complete_job failed: {resp.status} job={job_id} {text[:200]}"
                )
                return False

        except aiohttp.ClientError as e:
            logger.warning(f"Orchestrator complete_job client error: {e}")
            return False
        except Exception as e:
            logger.exception(f"Orchestrator complete_job unexpected error: {e}")
            return False

    async def fail_job(self, job_id: str, error_message: str) -> bool:
        session = self._session
        if session is None:
            await self.start()
            session = self._session
        if session is None:
            return False

        try:
            url = urljoin(self._config.base_url, f"/api/v1/jobs/{job_id}/fail")
            async with session.post(url, json={"error_message": error_message}) as resp:
                if resp.status == 200:
                    return True
                text = await resp.text()
                logger.warning(
                    f"Orchestrator fail_job failed: {resp.status} job={job_id} {text[:200]}"
                )
                return False

        except aiohttp.ClientError as e:
            logger.warning(f"Orchestrator fail_job client error: {e}")
            return False
        except Exception as e:
            logger.exception(f"Orchestrator fail_job unexpected error: {e}")
            return False

    async def release_job(self, job_id: str) -> bool:
        session = self._session
        if session is None:
            await self.start()
            session = self._session
        if session is None:
            return False

        try:
            url = urljoin(self._config.base_url, f"/api/v1/jobs/{job_id}/release")
            async with session.post(url) as resp:
                if resp.status == 200:
                    return True
                text = await resp.text()
                logger.warning(
                    f"Orchestrator release_job failed: {resp.status} job={job_id} {text[:200]}"
                )
                return False

        except aiohttp.ClientError as e:
            logger.warning(f"Orchestrator release_job client error: {e}")
            return False
        except Exception as e:
            logger.exception(f"Orchestrator release_job unexpected error: {e}")
            return False

    async def extend_lease(self, job_id: str, extension_seconds: int = 30) -> bool:
        session = self._session
        if session is None:
            await self.start()
            session = self._session
        if session is None:
            return False

        try:
            url = urljoin(self._config.base_url, f"/api/v1/jobs/{job_id}/extend-lease")
            async with session.post(
                url,
                json={"extension_seconds": int(extension_seconds)},
            ) as resp:
                if resp.status == 200:
                    return True
                text = await resp.text()
                logger.warning(
                    f"Orchestrator extend_lease failed: {resp.status} job={job_id} {text[:200]}"
                )
                return False

        except aiohttp.ClientError as e:
            logger.warning(f"Orchestrator extend_lease client error: {e}")
            return False
        except Exception as e:
            logger.exception(f"Orchestrator extend_lease unexpected error: {e}")
            return False

    async def update_progress(self, job_id: str, progress: int, current_node: str) -> bool:
        # Progress reporting is optional; keep robot execution robust even if
        # the orchestrator deployment doesn't support progress persistence yet.
        return True
