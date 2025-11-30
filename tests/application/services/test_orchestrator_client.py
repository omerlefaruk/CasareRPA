"""
Tests for OrchestratorClient application service.

Tests the Application layer service that abstracts HTTP communication
with the Orchestrator API.
"""

import pytest
from unittest.mock import Mock, AsyncMock

from casare_rpa.application.services.orchestrator_client import (
    OrchestratorClient,
    WorkflowSubmissionResult,
    AiohttpClient,
)


class TestWorkflowSubmissionResult:
    """Tests for WorkflowSubmissionResult dataclass."""

    def test_success_result(self):
        """Test creating a successful result."""
        result = WorkflowSubmissionResult(
            success=True,
            workflow_id="wf-123",
            job_id="job-456",
            message="Submitted",
        )

        assert result.success is True
        assert result.workflow_id == "wf-123"
        assert result.job_id == "job-456"
        assert result.error is None

    def test_failure_result(self):
        """Test creating a failure result."""
        result = WorkflowSubmissionResult(
            success=False,
            message="Failed",
            error="Connection refused",
        )

        assert result.success is False
        assert result.workflow_id is None
        assert result.job_id is None
        assert result.error == "Connection refused"


class TestOrchestratorClient:
    """Tests for OrchestratorClient."""

    def test_initialization_default_url(self):
        """Test client initializes with default URL."""
        client = OrchestratorClient()

        assert client._base_url == "http://localhost:8000"

    def test_initialization_custom_url(self):
        """Test client initializes with custom URL."""
        client = OrchestratorClient(orchestrator_url="http://custom:9000")

        assert client._base_url == "http://custom:9000"

    def test_initialization_strips_trailing_slash(self):
        """Test client strips trailing slash from URL."""
        client = OrchestratorClient(orchestrator_url="http://localhost:8000/")

        assert client._base_url == "http://localhost:8000"

    @pytest.mark.asyncio
    async def test_submit_workflow_success(self):
        """Test successful workflow submission."""
        # Create mock HTTP client
        mock_http = Mock()
        mock_http.post = AsyncMock(
            return_value=(
                200,
                {"workflow_id": "wf-123", "job_id": "job-456", "message": "OK"},
                "",
            )
        )

        client = OrchestratorClient(http_client=mock_http)

        result = await client.submit_workflow(
            workflow_name="Test Workflow",
            workflow_json={"nodes": []},
            execution_mode="lan",
        )

        assert result.success is True
        assert result.workflow_id == "wf-123"
        assert result.job_id == "job-456"

        # Verify HTTP call
        mock_http.post.assert_awaited_once()
        call_args = mock_http.post.call_args
        assert "http://localhost:8000/api/v1/workflows" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_submit_workflow_with_all_params(self):
        """Test workflow submission with all parameters."""
        mock_http = Mock()
        mock_http.post = AsyncMock(
            return_value=(
                200,
                {"workflow_id": "wf-abc", "schedule_id": "sched-123"},
                "",
            )
        )

        client = OrchestratorClient(
            orchestrator_url="http://orchestrator:8080",
            http_client=mock_http,
        )

        result = await client.submit_workflow(
            workflow_name="Scheduled Workflow",
            workflow_json={"nodes": [{"id": "1"}]},
            execution_mode="internet",
            trigger_type="scheduled",
            priority=5,
            metadata={"cron": "0 9 * * *"},
        )

        assert result.success is True
        assert result.workflow_id == "wf-abc"
        assert result.schedule_id == "sched-123"

        # Verify payload
        call_args = mock_http.post.call_args
        payload = call_args[1]["json"]
        assert payload["workflow_name"] == "Scheduled Workflow"
        assert payload["execution_mode"] == "internet"
        assert payload["trigger_type"] == "scheduled"
        assert payload["priority"] == 5
        assert payload["metadata"]["cron"] == "0 9 * * *"

    @pytest.mark.asyncio
    async def test_submit_workflow_api_error(self):
        """Test handling of API error response."""
        mock_http = Mock()
        mock_http.post = AsyncMock(
            return_value=(
                500,
                {},
                "Internal Server Error: Database connection failed",
            )
        )

        client = OrchestratorClient(http_client=mock_http)

        result = await client.submit_workflow(
            workflow_name="Test",
            workflow_json={"nodes": []},
        )

        assert result.success is False
        assert "500" in result.message
        assert "Database connection failed" in result.error

    @pytest.mark.asyncio
    async def test_submit_workflow_validation_error(self):
        """Test handling of validation error (400 status)."""
        mock_http = Mock()
        mock_http.post = AsyncMock(
            return_value=(
                400,
                {},
                "workflow_json must contain 'nodes' key",
            )
        )

        client = OrchestratorClient(http_client=mock_http)

        result = await client.submit_workflow(
            workflow_name="Invalid",
            workflow_json={},  # Missing nodes
        )

        assert result.success is False
        assert "400" in result.message

    @pytest.mark.asyncio
    async def test_submit_workflow_connection_error(self):
        """Test handling of connection error."""
        mock_http = Mock()
        mock_http.post = AsyncMock(side_effect=ConnectionError("Connection refused"))

        client = OrchestratorClient(http_client=mock_http)

        result = await client.submit_workflow(
            workflow_name="Test",
            workflow_json={"nodes": []},
        )

        assert result.success is False
        assert "connect" in result.message.lower()
        assert "Connection refused" in result.error

    @pytest.mark.asyncio
    async def test_submit_workflow_unexpected_error(self):
        """Test handling of unexpected exception."""
        mock_http = Mock()
        mock_http.post = AsyncMock(side_effect=RuntimeError("Unexpected error"))

        client = OrchestratorClient(http_client=mock_http)

        result = await client.submit_workflow(
            workflow_name="Test",
            workflow_json={"nodes": []},
        )

        assert result.success is False
        assert "Unexpected" in result.message
        assert "Unexpected error" in result.error

    @pytest.mark.asyncio
    async def test_close_client(self):
        """Test closing the client."""
        mock_http = Mock()
        mock_http.close = AsyncMock()

        client = OrchestratorClient(http_client=mock_http)

        await client.close()

        mock_http.close.assert_awaited_once()


class TestAiohttpClient:
    """Tests for AiohttpClient implementation."""

    def test_initialization(self):
        """Test client initializes with no session."""
        client = AiohttpClient()

        assert client._session is None

    @pytest.mark.asyncio
    async def test_post_creates_session(self):
        """Test POST creates a session on first call."""
        # Note: This test requires actual aiohttp, so we mock at a lower level
        from unittest.mock import patch, MagicMock

        client = AiohttpClient()

        # Mock the session creation with proper async context manager
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"id": "123"})
        mock_response.text = AsyncMock(return_value="")

        # Create async context manager mock
        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_context)
        mock_session.closed = False

        with patch.object(client, "_get_session", AsyncMock(return_value=mock_session)):
            status, json_resp, error = await client.post(
                "http://test.com/api",
                json={"data": "test"},
            )

        assert status == 200
        assert json_resp == {"id": "123"}
        assert error == ""

    @pytest.mark.asyncio
    async def test_close_session(self):
        """Test closing the HTTP session."""
        client = AiohttpClient()

        # Create a mock session
        mock_session = AsyncMock()
        mock_session.closed = False
        mock_session.close = AsyncMock()
        client._session = mock_session

        await client.close()

        mock_session.close.assert_awaited_once()
        assert client._session is None

    @pytest.mark.asyncio
    async def test_close_no_session(self):
        """Test closing when no session exists."""
        client = AiohttpClient()

        # Should not raise
        await client.close()


class TestIntegrationScenarios:
    """Integration-style tests for common scenarios."""

    @pytest.mark.asyncio
    async def test_submit_lan_workflow_scenario(self):
        """Test typical LAN workflow submission scenario."""
        mock_http = Mock()
        mock_http.post = AsyncMock(
            return_value=(
                200,
                {
                    "workflow_id": "wf-lan-001",
                    "job_id": "job-lan-001",
                    "status": "success",
                    "message": "Workflow submitted for LAN execution",
                },
                "",
            )
        )

        client = OrchestratorClient(
            orchestrator_url="http://192.168.1.100:8000",
            http_client=mock_http,
        )

        result = await client.submit_workflow(
            workflow_name="Scrape Product Prices",
            workflow_json={
                "nodes": [
                    {"id": "1", "type": "browser.navigate"},
                    {"id": "2", "type": "browser.extract"},
                ],
                "connections": [{"from": "1", "to": "2"}],
            },
            execution_mode="lan",
            metadata={"submitted_from": "canvas", "user": "admin"},
        )

        assert result.success is True
        assert result.workflow_id == "wf-lan-001"
        assert result.job_id == "job-lan-001"

    @pytest.mark.asyncio
    async def test_submit_internet_workflow_scenario(self):
        """Test typical internet robot workflow submission."""
        mock_http = Mock()
        mock_http.post = AsyncMock(
            return_value=(
                200,
                {
                    "workflow_id": "wf-inet-001",
                    "job_id": "job-inet-001",
                    "message": "Queued for internet robots",
                },
                "",
            )
        )

        client = OrchestratorClient(http_client=mock_http)

        result = await client.submit_workflow(
            workflow_name="Remote Data Processing",
            workflow_json={"nodes": [], "connections": []},
            execution_mode="internet",
            priority=5,  # Higher priority
        )

        assert result.success is True

        # Verify execution_mode was passed correctly
        call_args = mock_http.post.call_args
        payload = call_args[1]["json"]
        assert payload["execution_mode"] == "internet"
        assert payload["priority"] == 5

    @pytest.mark.asyncio
    async def test_orchestrator_unavailable_scenario(self):
        """Test handling when orchestrator is down."""
        mock_http = Mock()
        mock_http.post = AsyncMock(
            side_effect=ConnectionError("Cannot connect to host localhost:8000")
        )

        client = OrchestratorClient(http_client=mock_http)

        result = await client.submit_workflow(
            workflow_name="Test",
            workflow_json={"nodes": []},
        )

        assert result.success is False
        assert "connect" in result.message.lower()
        # Error message should help user troubleshoot
        assert "localhost:8000" in result.error
