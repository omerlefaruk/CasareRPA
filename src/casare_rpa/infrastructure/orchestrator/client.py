"""
OrchestratorClient - HTTP + WebSocket client for Orchestrator API.

Connects Fleet Dashboard to remote orchestrator for real robot management.
"""

import asyncio
import json
from urllib.parse import quote
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from urllib.parse import urlencode, urljoin

from loguru import logger

from casare_rpa.infrastructure.http import (
    UnifiedHttpClient,
    UnifiedHttpClientConfig,
)
from casare_rpa.infrastructure.http.aiohttp_websocket import (
    AIOHTTP_AVAILABLE,
    AiohttpWebSocketSession,
)


@dataclass
class OrchestratorConfig:
    """Configuration for orchestrator connection."""

    base_url: str = "http://localhost:8000"
    ws_url: str = "ws://localhost:8000"
    api_key: str | None = None
    timeout: float = 30.0
    retry_attempts: int = 3
    retry_delay: float = 1.0


@dataclass
class RobotData:
    """Robot data from orchestrator API."""

    id: str
    name: str
    hostname: str
    status: str
    environment: str = "default"
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    current_job: str | None = None
    current_jobs: int = 0
    max_concurrent_jobs: int = 1
    last_seen: datetime | None = None
    capabilities: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "RobotData":
        """Create from API response."""
        last_seen = data.get("last_seen") or data.get("lastSeen")
        if isinstance(last_seen, str):
            try:
                last_seen = datetime.fromisoformat(last_seen.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                last_seen = None

        return cls(
            id=data.get("robot_id") or data.get("id") or "",
            name=data.get("name") or data.get("robot_id") or "",
            hostname=data.get("hostname") or data.get("name") or "",
            status=data.get("status", "offline"),
            environment=data.get("environment", "default"),
            cpu_percent=data.get("cpu_percent") or data.get("cpuPercent") or 0.0,
            memory_mb=data.get("memory_mb") or data.get("memoryMb") or 0.0,
            current_job=data.get("current_job") or data.get("currentJob"),
            current_jobs=data.get("current_jobs") or data.get("currentJobs") or 0,
            max_concurrent_jobs=data.get("max_concurrent_jobs")
            or data.get("maxConcurrentJobs")
            or 1,
            last_seen=last_seen,
            capabilities=data.get("capabilities", []),
            tags=data.get("tags", []),
        )


@dataclass
class JobData:
    """Job data from orchestrator API."""

    id: str
    workflow_id: str
    workflow_name: str
    robot_id: str | None
    robot_name: str
    status: str
    progress: int = 0
    current_node: str = ""
    created_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int = 0
    error_message: str = ""

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "JobData":
        """Create from API response."""

        def parse_dt(val):
            if isinstance(val, str):
                try:
                    return datetime.fromisoformat(val.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    return None
            return val

        return cls(
            id=data.get("job_id") or data.get("id") or "",
            workflow_id=data.get("workflow_id") or data.get("workflowId") or "",
            workflow_name=data.get("workflow_name") or data.get("workflowName") or "",
            robot_id=data.get("robot_id") or data.get("robotId"),
            robot_name=data.get("robot_name") or data.get("robotName") or "",
            status=data.get("status", "pending"),
            progress=data.get("progress", 0),
            current_node=data.get("current_node") or data.get("currentNode") or "",
            created_at=parse_dt(data.get("created_at") or data.get("createdAt")),
            started_at=parse_dt(data.get("started_at") or data.get("startedAt")),
            completed_at=parse_dt(data.get("completed_at") or data.get("completedAt")),
            duration_ms=data.get("duration_ms") or data.get("durationMs") or 0,
            error_message=data.get("error_message") or data.get("errorMessage") or "",
        )


@dataclass
class RobotApiKeyData:
    """Robot API key metadata (raw key only available on create/rotate)."""

    id: str
    robot_id: str
    robot_name: str = ""
    name: str = ""
    description: str = ""
    status: str = "active"
    created_at: datetime | None = None
    expires_at: datetime | None = None
    last_used_at: datetime | None = None
    last_used_ip: str | None = None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "RobotApiKeyData":
        def parse_dt(val):
            if isinstance(val, str):
                try:
                    return datetime.fromisoformat(val.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    return None
            return val

        return cls(
            id=data.get("id") or data.get("key_id") or "",
            robot_id=data.get("robot_id") or "",
            robot_name=data.get("robot_name") or "",
            name=data.get("key_name") or data.get("name") or "",
            description=data.get("description") or "",
            status=data.get("status") or "active",
            created_at=parse_dt(data.get("created_at")),
            expires_at=parse_dt(data.get("expires_at")),
            last_used_at=parse_dt(data.get("last_used_at")),
            last_used_ip=data.get("last_used_ip"),
        )


class OrchestratorClient:
    """
    Client for communicating with CasareRPA Orchestrator API.

    Provides:
    - HTTP REST API calls for robots, jobs, schedules, analytics
    - WebSocket subscriptions for real-time updates
    - Automatic reconnection and retry logic
    """

    def __init__(self, config: OrchestratorConfig | None = None):
        """Initialize client with configuration."""
        self.config = config or OrchestratorConfig()

        # UnifiedHttpClient for HTTP requests (resilience patterns built-in)
        http_config = UnifiedHttpClientConfig(
            enable_ssrf_protection=False,  # Internal orchestrator
            max_retries=self.config.retry_attempts,
            default_timeout=self.config.timeout,
        )
        self._http_client = UnifiedHttpClient(http_config)

        # WebSocket still uses aiohttp directly (not yet abstracted)
        self._ws_session: AiohttpWebSocketSession | None = None
        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._ws_task: asyncio.Task | None = None
        self._connected = False
        self._last_http_status: int | None = None
        self._callbacks: dict[str, list[Callable]] = {
            "robot_status": [],
            "job_update": [],
            "queue_metrics": [],
            "connected": [],
            "disconnected": [],
            "error": [],
        }

    @property
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._connected and self._http_client._started

    @property
    def last_http_status(self) -> int | None:
        """
        Last HTTP status code returned by the orchestrator API.

        Useful for distinguishing 404 Not Found (e.g. robot deleted) from
        transient network/5xx failures when methods only return bool/None.
        """
        return self._last_http_status

    async def connect(self) -> bool:
        """
        Establish connection to orchestrator.

        Returns:
            True if connected successfully.
        """
        try:
            # Start UnifiedHttpClient
            await self._http_client.start()

            # Build headers for API key
            headers = {}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
                headers["X-Api-Key"] = self.config.api_key

            # Test connection with health check
            health_url = urljoin(self.config.base_url, "/health")
            async with await self._http_client.get(health_url, headers=headers) as resp:
                if resp.status == 200:
                    self._connected = True
                    logger.info(f"Connected to orchestrator at {self.config.base_url}")
                    await self._notify("connected", {"url": self.config.base_url})
                    return True
                else:
                    logger.warning(f"Orchestrator health check failed: {resp.status}")
                    await self._http_client.close()
                    return False

        except Exception as e:
            logger.error(f"Failed to connect to orchestrator: {e}")
            await self._notify("error", {"error": str(e)})
            await self._http_client.close()
            return False

    async def disconnect(self) -> None:
        """Close connection to orchestrator."""
        self._connected = False

        if self._ws_task:
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass
            self._ws_task = None

        if self._ws:
            await self._ws.close()
            self._ws = None

        if self._ws_session:
            await self._ws_session.close()
            self._ws_session = None

        await self._http_client.close()
        await self._notify("disconnected", {})
        logger.info("Disconnected from orchestrator")

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict | None = None,
        json_data: dict | None = None,
    ) -> dict[str, Any] | None:
        """Make HTTP request using UnifiedHttpClient (handles retry internally)."""
        if not self._http_client._started:
            await self.connect()

        if not self._http_client._started:
            return None

        url = urljoin(self.config.base_url, endpoint)

        # Append query parameters to URL (UnifiedHttpClient doesn't have params arg)
        if params:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}{urlencode(params, doseq=True)}"

        # Build headers for API key
        headers = {}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
            headers["X-Api-Key"] = self.config.api_key

        try:
            # UnifiedHttpClient handles retry, circuit breaker, rate limiting
            resp = await self._http_client.request(
                method,
                url,
                json=json_data,
                headers=headers,
                retry_count=self.config.retry_attempts,
                skip_rate_limit=True,  # Orchestrator manages its own rate limiting
                skip_circuit_breaker=True,  # Let orchestrator handle failures
            )

            self._last_http_status = resp.status

            if 200 <= resp.status < 300:
                # Handle 204 No Content
                if resp.status == 204:
                    return {}
                # Try to parse JSON, fallback to empty dict if not JSON
                try:
                    json_resp = await resp.json()
                    return json_resp if json_resp is not None else {}
                except Exception:
                    return {}

            elif resp.status == 404:
                return None
            else:
                resp_text = await resp.text()
                await self._notify(
                    "error",
                    {
                        "status": resp.status,
                        "method": method,
                        "url": url,
                        "body": resp_text[:500],
                    },
                )
                logger.error(f"API request failed: {resp.status} {url} | Body: {resp_text[:200]}")
                return None

        except Exception as e:
            self._last_http_status = None
            logger.error(f"Request error: {e}")
            await self._notify("error", {"error": str(e)})
            return None

    # ==================== ROBOT ENDPOINTS ====================

    async def get_robots(self, status: str | None = None) -> list[RobotData]:
        """
        Get all robots from orchestrator.

        Args:
            status: Optional filter (idle, busy, offline)

        Returns:
            List of RobotData objects.
        """
        params = {}
        if status:
            params["status"] = status

        data = await self._request("GET", "/api/v1/metrics/robots", params=params)
        if not data:
            return []

        return [RobotData.from_api(r) for r in data]

    async def get_robot(self, robot_id: str) -> RobotData | None:
        """Get single robot details."""
        data = await self._request("GET", f"/api/v1/metrics/robots/{robot_id}")
        if not data:
            return None
        return RobotData.from_api(data)

    async def register_robot(
        self,
        robot_id: str,
        name: str,
        hostname: str,
        capabilities: list[str],
        environment: str = "default",
        max_concurrent_jobs: int = 1,
        tags: list[str] | None = None,
    ) -> bool:
        """
        Register a new robot with the orchestrator.

        Args:
            robot_id: Unique robot identifier
            name: Display name
            hostname: Machine hostname
            capabilities: List of capability strings
            environment: Execution environment
            max_concurrent_jobs: Max parallel jobs

        Returns:
            True if registered successfully.
        """
        data = await self._request(
            "POST",
            "/api/v1/robots/register",
            json_data={
                "robot_id": robot_id,
                "name": name,
                "hostname": hostname,
                "capabilities": capabilities,
                "environment": environment,
                "max_concurrent_jobs": max_concurrent_jobs,
                "tags": tags or [],
            },
        )
        return data is not None

    async def update_robot_status(self, robot_id: str, status: str) -> bool:
        """Update robot status."""
        data = await self._request(
            "PUT",
            f"/api/v1/robots/{robot_id}/status",
            json_data={"status": status},
        )
        return data is not None

    async def update_robot(self, robot_id: str, robot_data: dict[str, Any]) -> bool:
        """Update robot metadata (name/environment/capabilities/etc)."""
        data = await self._request(
            "PUT",
            f"/api/v1/robots/{robot_id}",
            json_data=robot_data,
        )
        return data is not None

    async def send_robot_heartbeat(
        self,
        robot_id: str,
        metrics: dict[str, Any] | None = None,
    ) -> bool:
        """Send robot heartbeat with optional metrics payload."""
        data = await self._request(
            "POST",
            f"/api/v1/robots/{robot_id}/heartbeat",
            json_data=metrics or {},
        )
        return data is not None

    async def delete_robot(self, robot_id: str) -> bool:
        """Delete/deregister a robot."""
        if not self._http_client._started:
            await self.connect()
        if not self._http_client._started:
            return False

        url = urljoin(self.config.base_url, f"/api/v1/robots/{robot_id}")

        # Build headers for API key
        headers = {}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
            headers["X-Api-Key"] = self.config.api_key

        try:
            resp = await self._http_client.delete(url, headers=headers)
            if 200 <= resp.status < 300:
                return True
            if resp.status == 404:
                logger.info(
                    f"Robot {robot_id} not found (404) during deletion, treating as success"
                )
                return True

            text = await resp.text()
            logger.warning(f"Delete robot failed: {resp.status} - {text[:200]}")
            return False
        except Exception as e:
            logger.error(f"Error deleting robot: {e}")
            return False

    # ==================== ROBOT API KEY ENDPOINTS ====================

    async def list_robot_api_keys(
        self,
        robot_id: str | None = None,
        status: str | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> list[RobotApiKeyData]:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if robot_id:
            params["robot_id"] = robot_id
        if status:
            params["status"] = status

        data = await self._request("GET", "/api/v1/robot-api-keys", params=params)
        if not data:
            return []

        items = data.get("keys") if isinstance(data, dict) else None
        if not isinstance(items, list):
            return []
        return [RobotApiKeyData.from_api(item) for item in items]

    async def create_robot_api_key(
        self,
        robot_id: str,
        name: str,
        description: str = "",
        expires_at: datetime | None = None,
    ) -> dict[str, Any] | None:
        payload: dict[str, Any] = {
            "robot_id": robot_id,
            "name": name,
            "description": description or None,
            "expires_at": expires_at.isoformat() if expires_at else None,
        }

        data = await self._request("POST", "/api/v1/robot-api-keys", json_data=payload)
        return data if isinstance(data, dict) else None

    async def revoke_robot_api_key(self, key_id: str, reason: str = "") -> bool:
        data = await self._request(
            "POST",
            f"/api/v1/robot-api-keys/{key_id}/revoke",
            json_data={"reason": reason or None},
        )
        return data is not None

    async def rotate_robot_api_key(self, key_id: str) -> dict[str, Any] | None:
        data = await self._request(
            "POST",
            f"/api/v1/robot-api-keys/{key_id}/rotate",
        )
        return data if isinstance(data, dict) else None

    # ==================== JOB ENDPOINTS ====================

    async def get_jobs(
        self,
        limit: int = 50,
        status: str | None = None,
        workflow_id: str | None = None,
        robot_id: str | None = None,
    ) -> list[JobData]:
        """
        Get job history from orchestrator.

        Args:
            limit: Max number of jobs to return
            status: Filter by status (pending, claimed, completed, failed)
            workflow_id: Filter by workflow
            robot_id: Filter by robot

        Returns:
            List of JobData objects.
        """
        params = {"limit": limit}
        if status:
            params["status"] = status
        if workflow_id:
            params["workflow_id"] = workflow_id
        if robot_id:
            params["robot_id"] = robot_id

        data = await self._request("GET", "/api/v1/metrics/jobs", params=params)
        if not data:
            return []

        return [JobData.from_api(j) for j in data]

    async def get_job(self, job_id: str) -> JobData | None:
        """Get single job details."""
        data = await self._request("GET", f"/api/v1/metrics/jobs/{job_id}")
        if not data:
            return None
        return JobData.from_api(data)

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending/running job."""
        data = await self._request("POST", f"/api/v1/jobs/{job_id}/cancel")
        return data is not None

    async def retry_job(self, job_id: str) -> str | None:
        """Retry a failed job. Returns new job ID."""
        data = await self._request("POST", f"/api/v1/jobs/{job_id}/retry")
        if data:
            return data.get("job_id")
        return None

    # ==================== FLEET METRICS ====================

    async def get_fleet_metrics(self) -> dict[str, Any]:
        """Get fleet-wide metrics summary."""
        data = await self._request("GET", "/api/v1/metrics/fleet")
        return data or {}

    async def get_analytics(self, days: int = 7) -> dict[str, Any]:
        """Get aggregated analytics."""
        data = await self._request("GET", "/api/v1/metrics/analytics", params={"days": days})
        return data or {}

    async def get_activity(
        self,
        limit: int = 50,
        since: datetime | None = None,
        event_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get activity feed."""
        params = {"limit": limit}
        if since:
            params["since"] = since.isoformat()
        if event_type:
            params["event_type"] = event_type

        data = await self._request("GET", "/api/v1/metrics/activity", params=params)
        if data:
            return data.get("events", [])
        return []

    # ==================== SCHEDULES ====================

    async def get_schedules(self) -> list[dict[str, Any]]:
        """Get all schedules."""
        data = await self._request("GET", "/api/v1/schedules")
        return data or []

    async def trigger_schedule(self, schedule_id: str) -> bool:
        """Trigger a schedule immediately."""
        data = await self._request("POST", f"/api/v1/schedules/{schedule_id}/run-now")
        return data is not None

    # ==================== WEBSOCKET ====================

    def on(self, event: str, callback: Callable) -> None:
        """
        Register callback for WebSocket events.

        Events:
            - robot_status: Robot status changed
            - job_update: Job progress/status changed
            - queue_metrics: Queue depth changed
            - connected: WebSocket connected
            - disconnected: WebSocket disconnected
            - error: Error occurred
        """
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def off(self, event: str, callback: Callable) -> None:
        """Unregister callback."""
        if event in self._callbacks and callback in self._callbacks[event]:
            self._callbacks[event].remove(callback)

    async def _notify(self, event: str, data: dict[str, Any]) -> None:
        """Notify all callbacks for an event."""
        for callback in self._callbacks.get(event, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            except Exception as e:
                logger.error(f"Callback error for {event}: {e}")

    async def subscribe_live_updates(self) -> None:
        """
        Subscribe to real-time WebSocket updates.

        Starts background task that receives:
        - Robot status changes
        - Job progress updates
        - Queue metrics
        """
        if self._ws_task:
            return  # Already subscribed

        self._ws_task = asyncio.create_task(self._ws_loop())

    async def _ws_loop(self) -> None:
        """WebSocket receive loop with auto-reconnect."""
        if not AIOHTTP_AVAILABLE:
            logger.error("aiohttp is required for WebSocket support")
            return

        while self._connected:
            try:
                ws_url = urljoin(self.config.ws_url, "/ws/monitoring/live-jobs")
                # Add token to query string if configured
                if self.config.api_key:
                    separator = "&" if "?" in ws_url else "?"
                    token = quote(self.config.api_key, safe="")
                    ws_url = f"{ws_url}{separator}token={token}"
                logger.info(f"Connecting to WebSocket: {ws_url.split('?')[0]}")

                # Create a separate session for WebSocket (UnifiedHttpClient doesn't support WS)
                if self._ws_session is None:
                    self._ws_session = AiohttpWebSocketSession(
                        timeout=self.config.timeout
                    )

                # Connect to WebSocket
                async with self._ws_session.ws_connect(ws_url) as ws:
                    self._ws = ws
                    logger.info("WebSocket connected")

                    async for msg in ws:
                        if self._ws_session.is_text(msg):
                            try:
                                data = json.loads(msg.data)
                                event_type = data.get("type", "unknown")

                                if event_type == "robot_status":
                                    await self._notify("robot_status", data)
                                elif event_type == "job_update":
                                    await self._notify("job_update", data)
                                elif event_type == "queue_metrics":
                                    await self._notify("queue_metrics", data)

                            except json.JSONDecodeError:
                                logger.warning(f"Invalid WebSocket message: {msg.data}")

                        elif self._ws_session.is_error(msg):
                            logger.error(f"WebSocket error: {ws.exception()}")
                            break

                        elif self._ws_session.is_closed(msg):
                            logger.info("WebSocket closed")
                            break

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                if self._connected:
                    await asyncio.sleep(5)  # Reconnect delay

        self._ws = None


# Singleton instance
_client: OrchestratorClient | None = None


def get_orchestrator_client() -> OrchestratorClient:
    """Get or create singleton OrchestratorClient."""
    global _client
    if _client is None:
        _client = OrchestratorClient()
    return _client


async def configure_orchestrator(
    base_url: str,
    ws_url: str | None = None,
    api_key: str | None = None,
) -> OrchestratorClient:
    """
    Configure and connect to orchestrator.

    Args:
        base_url: HTTP API base URL (e.g., http://localhost:8000)
        ws_url: WebSocket URL (defaults to base_url with ws:// scheme)
        api_key: Optional API key for authentication

    Returns:
        Connected OrchestratorClient instance.
    """
    global _client

    if ws_url is None:
        ws_url = base_url.replace("http://", "ws://").replace("https://", "wss://")

    config = OrchestratorConfig(
        base_url=base_url,
        ws_url=ws_url,
        api_key=api_key,
    )

    _client = OrchestratorClient(config)
    await _client.connect()
    return _client
