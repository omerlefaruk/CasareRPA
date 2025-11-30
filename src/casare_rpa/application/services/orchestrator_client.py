"""
Orchestrator API client service.

Application layer service that abstracts HTTP communication with the Orchestrator API.
This prevents Presentation layer from directly depending on Infrastructure (aiohttp).

Architecture: Presentation → Application (this) → Infrastructure (aiohttp)
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol
from loguru import logger


@dataclass
class WorkflowSubmissionResult:
    """Result of workflow submission to Orchestrator."""

    success: bool
    workflow_id: Optional[str] = None
    job_id: Optional[str] = None
    schedule_id: Optional[str] = None
    message: str = ""
    error: Optional[str] = None


class HttpClient(Protocol):
    """Protocol for HTTP client abstraction (for testing)."""

    async def post(
        self, url: str, json: Dict[str, Any]
    ) -> tuple[int, Dict[str, Any], str]:
        """
        POST request to URL with JSON payload.

        Returns:
            Tuple of (status_code, json_response, error_text)
        """
        ...

    async def close(self) -> None:
        """Close the client and release resources."""
        ...


class AiohttpClient:
    """Default HTTP client implementation using aiohttp."""

    def __init__(self) -> None:
        self._session = None

    async def _get_session(self):
        """Get or create aiohttp session with connection pooling."""
        if self._session is None or self._session.closed:
            import aiohttp

            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            connector = aiohttp.TCPConnector(
                limit=10,
                limit_per_host=5,
                keepalive_timeout=30,
            )
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
            )
        return self._session

    async def post(
        self, url: str, json: Dict[str, Any]
    ) -> tuple[int, Dict[str, Any], str]:
        """POST request with JSON payload."""
        import aiohttp

        session = await self._get_session()
        try:
            async with session.post(url, json=json) as resp:
                status = resp.status
                try:
                    json_response = await resp.json()
                except Exception:
                    json_response = {}
                error_text = await resp.text() if status != 200 else ""
                return status, json_response, error_text
        except aiohttp.ClientError as e:
            raise ConnectionError(f"HTTP request failed: {e}") from e

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None


class OrchestratorClient:
    """
    Application layer client for Orchestrator API.

    Encapsulates all HTTP communication with the Orchestrator,
    providing a clean interface for the Presentation layer.

    Usage:
        client = OrchestratorClient(orchestrator_url="http://localhost:8000")
        result = await client.submit_workflow(
            workflow_name="My Workflow",
            workflow_json={"nodes": [...]},
            execution_mode="lan",
        )
        if result.success:
            print(f"Job ID: {result.job_id}")
    """

    def __init__(
        self,
        orchestrator_url: str = "http://localhost:8000",
        http_client: Optional[HttpClient] = None,
    ) -> None:
        """
        Initialize Orchestrator client.

        Args:
            orchestrator_url: Base URL for Orchestrator API
            http_client: Optional HTTP client (for testing). Uses AiohttpClient by default.
        """
        self._base_url = orchestrator_url.rstrip("/")
        self._http_client = http_client or AiohttpClient()

    async def submit_workflow(
        self,
        workflow_name: str,
        workflow_json: Dict[str, Any],
        execution_mode: str = "lan",
        trigger_type: str = "manual",
        priority: int = 10,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WorkflowSubmissionResult:
        """
        Submit a workflow to the Orchestrator for execution.

        Args:
            workflow_name: Name of the workflow
            workflow_json: Serialized workflow definition
            execution_mode: "lan" for local robots, "internet" for remote robots
            trigger_type: "manual", "scheduled", or "webhook"
            priority: Job priority (0=highest, 20=lowest)
            metadata: Additional metadata for the job

        Returns:
            WorkflowSubmissionResult with success status and IDs
        """
        logger.info(
            "Submitting workflow '{}' to Orchestrator (mode={})",
            workflow_name,
            execution_mode,
        )

        payload = {
            "workflow_name": workflow_name,
            "workflow_json": workflow_json,
            "trigger_type": trigger_type,
            "execution_mode": execution_mode,
            "priority": priority,
            "metadata": metadata or {},
        }

        try:
            url = f"{self._base_url}/api/v1/workflows"
            status, json_response, error_text = await self._http_client.post(
                url, json=payload
            )

            if status == 200:
                workflow_id = json_response.get("workflow_id", "unknown")
                job_id = json_response.get("job_id")
                schedule_id = json_response.get("schedule_id")

                logger.info(
                    "Workflow submitted: workflow={}, job={}, schedule={}",
                    workflow_id,
                    job_id,
                    schedule_id,
                )

                return WorkflowSubmissionResult(
                    success=True,
                    workflow_id=workflow_id,
                    job_id=job_id,
                    schedule_id=schedule_id,
                    message=json_response.get("message", "Workflow submitted"),
                )
            else:
                logger.error(
                    "Workflow submission failed: {} - {}", status, error_text[:200]
                )
                return WorkflowSubmissionResult(
                    success=False,
                    message=f"Submission failed with status {status}",
                    error=error_text[:500],
                )

        except ConnectionError as e:
            logger.error("Connection error: {}", e)
            return WorkflowSubmissionResult(
                success=False,
                message="Could not connect to Orchestrator",
                error=str(e),
            )

        except Exception as e:
            logger.error("Unexpected error submitting workflow: {}", e)
            return WorkflowSubmissionResult(
                success=False,
                message="Unexpected error",
                error=str(e),
            )

    async def close(self) -> None:
        """Close the client and release resources."""
        await self._http_client.close()
        logger.debug("OrchestratorClient closed")
