"""
Tests for workflows REST API router.

Tests cover:
- Workflow submission (manual, scheduled, webhook triggers)
- File upload endpoint
- Workflow retrieval
- Workflow deletion
- Validation errors
- Error handling
"""

import os
import tempfile
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from casare_rpa.infrastructure.orchestrator.api.routers.workflows import (
    WorkflowSubmissionRequest,
    WorkflowSubmissionResponse,
    WorkflowDetailsResponse,
    get_workflows_dir,
    store_workflow_filesystem,
    store_workflow_database,
    enqueue_job,
    submit_workflow,
    upload_workflow,
    get_workflow,
    delete_workflow,
    router,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_workflow_json() -> Dict[str, Any]:
    """Sample valid workflow JSON."""
    return {
        "nodes": [
            {"id": "node1", "type": "start", "name": "Start"},
            {"id": "node2", "type": "end", "name": "End"},
        ],
        "connections": [{"from": "node1", "to": "node2"}],
        "metadata": {"version": "1.0"},
    }


@pytest.fixture
def sample_submission_request(
    sample_workflow_json: Dict[str, Any],
) -> WorkflowSubmissionRequest:
    """Sample workflow submission request."""
    return WorkflowSubmissionRequest(
        workflow_name="Test Workflow",
        workflow_json=sample_workflow_json,
        trigger_type="manual",
        execution_mode="lan",
        priority=10,
        metadata={"author": "test"},
    )


@pytest.fixture
def temp_workflows_dir(tmp_path: Path) -> Path:
    """Temporary workflows directory for testing."""
    workflows_dir = tmp_path / "workflows"
    workflows_dir.mkdir()
    return workflows_dir


# ============================================================================
# WorkflowSubmissionRequest Validation Tests
# ============================================================================


class TestWorkflowSubmissionRequestValidation:
    """Tests for request model validation."""

    def test_valid_request(self, sample_workflow_json: Dict[str, Any]) -> None:
        """Test valid request passes validation."""
        request = WorkflowSubmissionRequest(
            workflow_name="Test Workflow",
            workflow_json=sample_workflow_json,
        )
        assert request.workflow_name == "Test Workflow"
        assert request.trigger_type == "manual"
        assert request.execution_mode == "lan"
        assert request.priority == 10

    def test_invalid_trigger_type(self, sample_workflow_json: Dict[str, Any]) -> None:
        """Test invalid trigger_type raises error."""
        with pytest.raises(ValueError, match="trigger_type must be one of"):
            WorkflowSubmissionRequest(
                workflow_name="Test",
                workflow_json=sample_workflow_json,
                trigger_type="invalid",
            )

    def test_invalid_execution_mode(self, sample_workflow_json: Dict[str, Any]) -> None:
        """Test invalid execution_mode raises error."""
        with pytest.raises(ValueError, match="execution_mode must be one of"):
            WorkflowSubmissionRequest(
                workflow_name="Test",
                workflow_json=sample_workflow_json,
                execution_mode="cloud",
            )

    def test_workflow_json_missing_nodes(self) -> None:
        """Test workflow_json without nodes key raises error."""
        with pytest.raises(ValueError, match="must contain 'nodes' key"):
            WorkflowSubmissionRequest(
                workflow_name="Test",
                workflow_json={"connections": []},
            )

    def test_workflow_json_nodes_not_list(self) -> None:
        """Test workflow_json.nodes must be list."""
        with pytest.raises(ValueError, match="nodes must be a list"):
            WorkflowSubmissionRequest(
                workflow_name="Test",
                workflow_json={"nodes": "not a list"},
            )

    def test_workflow_name_empty(self, sample_workflow_json: Dict[str, Any]) -> None:
        """Test empty workflow_name raises error."""
        with pytest.raises(ValueError):
            WorkflowSubmissionRequest(
                workflow_name="",
                workflow_json=sample_workflow_json,
            )

    def test_workflow_name_too_long(self, sample_workflow_json: Dict[str, Any]) -> None:
        """Test workflow_name exceeding max length raises error."""
        with pytest.raises(ValueError):
            WorkflowSubmissionRequest(
                workflow_name="x" * 256,
                workflow_json=sample_workflow_json,
            )

    def test_priority_out_of_range(self, sample_workflow_json: Dict[str, Any]) -> None:
        """Test priority outside valid range raises error."""
        with pytest.raises(ValueError):
            WorkflowSubmissionRequest(
                workflow_name="Test",
                workflow_json=sample_workflow_json,
                priority=25,  # Max is 20
            )


# ============================================================================
# Utility Function Tests
# ============================================================================


class TestGetWorkflowsDir:
    """Tests for get_workflows_dir function."""

    def test_creates_directory_if_not_exists(self, tmp_path: Path) -> None:
        """Test creates workflows directory if missing."""
        workflows_path = tmp_path / "new_workflows"
        with patch.dict(os.environ, {"WORKFLOWS_DIR": str(workflows_path)}):
            result = get_workflows_dir()
            assert result.exists()
            assert result.is_dir()

    def test_uses_default_if_env_not_set(self, monkeypatch) -> None:
        """Test uses default path if WORKFLOWS_DIR not set."""
        monkeypatch.delenv("WORKFLOWS_DIR", raising=False)
        result = get_workflows_dir()
        assert result == Path("./workflows")


class TestStoreWorkflowFilesystem:
    """Tests for store_workflow_filesystem function."""

    @pytest.mark.asyncio
    async def test_stores_workflow_file(
        self, temp_workflows_dir: Path, sample_workflow_json: Dict[str, Any]
    ) -> None:
        """Test workflow is stored to filesystem."""
        with patch.dict(os.environ, {"WORKFLOWS_DIR": str(temp_workflows_dir)}):
            result = await store_workflow_filesystem(
                workflow_id="wf-123",
                workflow_name="Test Workflow",
                workflow_json=sample_workflow_json,
            )

            assert result.exists()
            assert result.name == "wf-123.json"

    @pytest.mark.asyncio
    async def test_stores_correct_content(
        self, temp_workflows_dir: Path, sample_workflow_json: Dict[str, Any]
    ) -> None:
        """Test stored content is correct."""
        import orjson

        with patch.dict(os.environ, {"WORKFLOWS_DIR": str(temp_workflows_dir)}):
            file_path = await store_workflow_filesystem(
                workflow_id="wf-123",
                workflow_name="Test Workflow",
                workflow_json=sample_workflow_json,
            )

            content = orjson.loads(file_path.read_bytes())
            assert content["workflow_id"] == "wf-123"
            assert content["workflow_name"] == "Test Workflow"
            assert content["workflow_json"] == sample_workflow_json


class TestStoreWorkflowDatabase:
    """Tests for store_workflow_database function."""

    @pytest.mark.asyncio
    async def test_returns_true_stub(
        self, sample_workflow_json: Dict[str, Any]
    ) -> None:
        """Test database storage returns True (stub behavior)."""
        result = await store_workflow_database(
            workflow_id="wf-123",
            workflow_name="Test",
            workflow_json=sample_workflow_json,
        )
        assert result is True


class TestEnqueueJob:
    """Tests for enqueue_job function."""

    @pytest.mark.asyncio
    async def test_uses_memory_queue_when_enabled(
        self, sample_workflow_json: Dict[str, Any]
    ) -> None:
        """Test enqueue uses memory queue when USE_MEMORY_QUEUE=true."""
        mock_queue = AsyncMock()
        mock_queue.enqueue.return_value = "job-123"

        with patch.dict(os.environ, {"USE_MEMORY_QUEUE": "true"}):
            with patch(
                "casare_rpa.infrastructure.orchestrator.api.routers.workflows.get_memory_queue",
                return_value=mock_queue,
            ):
                job_id = await enqueue_job(
                    workflow_id="wf-001",
                    workflow_json=sample_workflow_json,
                    priority=10,
                    execution_mode="lan",
                    metadata={"key": "value"},
                )

        assert job_id == "job-123"
        mock_queue.enqueue.assert_awaited_once_with(
            workflow_id="wf-001",
            workflow_json=sample_workflow_json,
            priority=10,
            execution_mode="lan",
            metadata={"key": "value"},
        )

    @pytest.mark.asyncio
    async def test_returns_placeholder_when_pgqueuer_not_ready(
        self, sample_workflow_json: Dict[str, Any]
    ) -> None:
        """Test returns placeholder job_id when PgQueuer not implemented."""
        with patch.dict(os.environ, {"USE_MEMORY_QUEUE": "false"}):
            job_id = await enqueue_job(
                workflow_id="wf-001",
                workflow_json=sample_workflow_json,
                priority=10,
                execution_mode="lan",
                metadata={},
            )

        assert job_id is not None
        assert len(job_id) == 36  # UUID format


# ============================================================================
# submit_workflow Endpoint Tests
# ============================================================================


class TestSubmitWorkflowEndpoint:
    """Tests for POST /workflows endpoint."""

    @pytest.mark.asyncio
    async def test_submit_manual_trigger_success(
        self,
        sample_submission_request: WorkflowSubmissionRequest,
        temp_workflows_dir: Path,
    ) -> None:
        """Test successful manual trigger submission."""
        with patch.dict(
            os.environ,
            {
                "WORKFLOWS_DIR": str(temp_workflows_dir),
                "WORKFLOW_BACKUP_ENABLED": "true",
            },
        ):
            with patch(
                "casare_rpa.infrastructure.orchestrator.api.routers.workflows.enqueue_job",
                new_callable=AsyncMock,
                return_value="job-123",
            ):
                response = await submit_workflow(sample_submission_request)

        assert response.status == "success"
        assert response.workflow_id is not None
        assert response.job_id == "job-123"
        assert response.schedule_id is None

    @pytest.mark.asyncio
    async def test_submit_scheduled_trigger(
        self, sample_workflow_json: Dict[str, Any], temp_workflows_dir: Path
    ) -> None:
        """Test scheduled trigger returns schedule_id."""
        request = WorkflowSubmissionRequest(
            workflow_name="Scheduled Workflow",
            workflow_json=sample_workflow_json,
            trigger_type="scheduled",
            schedule_cron="0 * * * *",
        )

        with patch.dict(
            os.environ,
            {
                "WORKFLOWS_DIR": str(temp_workflows_dir),
                "WORKFLOW_BACKUP_ENABLED": "true",
            },
        ):
            response = await submit_workflow(request)

        assert response.status == "success"
        assert response.job_id is None
        assert response.schedule_id is not None

    @pytest.mark.asyncio
    async def test_submit_webhook_trigger(
        self, sample_workflow_json: Dict[str, Any], temp_workflows_dir: Path
    ) -> None:
        """Test webhook trigger submission."""
        request = WorkflowSubmissionRequest(
            workflow_name="Webhook Workflow",
            workflow_json=sample_workflow_json,
            trigger_type="webhook",
        )

        with patch.dict(
            os.environ,
            {
                "WORKFLOWS_DIR": str(temp_workflows_dir),
                "WORKFLOW_BACKUP_ENABLED": "true",
            },
        ):
            response = await submit_workflow(request)

        assert response.status == "success"
        assert response.job_id is None
        assert response.schedule_id is None

    @pytest.mark.asyncio
    async def test_submit_stores_filesystem_backup(
        self,
        sample_submission_request: WorkflowSubmissionRequest,
        temp_workflows_dir: Path,
    ) -> None:
        """Test filesystem backup is created."""
        with patch.dict(
            os.environ,
            {
                "WORKFLOWS_DIR": str(temp_workflows_dir),
                "WORKFLOW_BACKUP_ENABLED": "true",
            },
        ):
            with patch(
                "casare_rpa.infrastructure.orchestrator.api.routers.workflows.enqueue_job",
                new_callable=AsyncMock,
                return_value="job-123",
            ):
                response = await submit_workflow(sample_submission_request)

        # Check file was created
        workflow_file = temp_workflows_dir / f"{response.workflow_id}.json"
        assert workflow_file.exists()

    @pytest.mark.asyncio
    async def test_submit_skips_backup_when_disabled(
        self,
        sample_submission_request: WorkflowSubmissionRequest,
        temp_workflows_dir: Path,
    ) -> None:
        """Test filesystem backup is skipped when disabled."""
        with patch.dict(
            os.environ,
            {
                "WORKFLOWS_DIR": str(temp_workflows_dir),
                "WORKFLOW_BACKUP_ENABLED": "false",
            },
        ):
            with patch(
                "casare_rpa.infrastructure.orchestrator.api.routers.workflows.enqueue_job",
                new_callable=AsyncMock,
                return_value="job-123",
            ):
                response = await submit_workflow(sample_submission_request)

        # Check file was NOT created
        workflow_files = list(temp_workflows_dir.glob("*.json"))
        assert len(workflow_files) == 0

    @pytest.mark.asyncio
    async def test_submit_error_handling(
        self, sample_submission_request: WorkflowSubmissionRequest
    ) -> None:
        """Test error handling during submission."""
        with patch(
            "casare_rpa.infrastructure.orchestrator.api.routers.workflows.store_workflow_database",
            side_effect=Exception("Database error"),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await submit_workflow(sample_submission_request)

        assert exc_info.value.status_code == 500
        assert "Workflow submission failed" in str(exc_info.value.detail)


# ============================================================================
# get_workflow Endpoint Tests
# ============================================================================


class TestGetWorkflowEndpoint:
    """Tests for GET /workflows/{workflow_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_workflow_success(
        self, temp_workflows_dir: Path, sample_workflow_json: Dict[str, Any]
    ) -> None:
        """Test successful workflow retrieval."""
        import orjson

        # Create workflow file
        workflow_id = "wf-test-123"
        workflow_data = {
            "workflow_id": workflow_id,
            "workflow_name": "Test Workflow",
            "workflow_json": sample_workflow_json,
            "version": 1,
            "description": "Test description",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        file_path = temp_workflows_dir / f"{workflow_id}.json"
        file_path.write_bytes(orjson.dumps(workflow_data))

        with patch.dict(os.environ, {"WORKFLOWS_DIR": str(temp_workflows_dir)}):
            response = await get_workflow(workflow_id)

        assert response.workflow_id == workflow_id
        assert response.workflow_name == "Test Workflow"
        assert response.version == 1

    @pytest.mark.asyncio
    async def test_get_workflow_not_found(self, temp_workflows_dir: Path) -> None:
        """Test 404 when workflow not found (wrapped in 500 by error handler)."""
        with patch.dict(os.environ, {"WORKFLOWS_DIR": str(temp_workflows_dir)}):
            with pytest.raises(HTTPException) as exc_info:
                await get_workflow("non-existent-id")

        # Error handler wraps 404 in 500, check the detail message
        assert "Workflow not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_workflow_corrupted_file(self, temp_workflows_dir: Path) -> None:
        """Test error handling for corrupted workflow file."""
        workflow_id = "wf-corrupted"
        file_path = temp_workflows_dir / f"{workflow_id}.json"
        file_path.write_text("not valid json {")

        with patch.dict(os.environ, {"WORKFLOWS_DIR": str(temp_workflows_dir)}):
            with pytest.raises(HTTPException) as exc_info:
                await get_workflow(workflow_id)

        assert exc_info.value.status_code == 500


# ============================================================================
# delete_workflow Endpoint Tests
# ============================================================================


class TestDeleteWorkflowEndpoint:
    """Tests for DELETE /workflows/{workflow_id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_workflow_success(
        self, temp_workflows_dir: Path, sample_workflow_json: Dict[str, Any]
    ) -> None:
        """Test successful workflow deletion."""
        import orjson

        # Create workflow file
        workflow_id = "wf-to-delete"
        workflow_data = {
            "workflow_id": workflow_id,
            "workflow_json": sample_workflow_json,
        }
        file_path = temp_workflows_dir / f"{workflow_id}.json"
        file_path.write_bytes(orjson.dumps(workflow_data))

        with patch.dict(os.environ, {"WORKFLOWS_DIR": str(temp_workflows_dir)}):
            response = await delete_workflow(workflow_id)

        assert response["status"] == "success"
        assert not file_path.exists()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_workflow(self, temp_workflows_dir: Path) -> None:
        """Test deleting non-existent workflow succeeds silently."""
        with patch.dict(os.environ, {"WORKFLOWS_DIR": str(temp_workflows_dir)}):
            response = await delete_workflow("non-existent-id")

        assert response["status"] == "success"


# ============================================================================
# upload_workflow Endpoint Tests
# ============================================================================


class TestUploadWorkflowEndpoint:
    """Tests for POST /workflows/upload endpoint."""

    @pytest.mark.asyncio
    async def test_upload_valid_json_file(
        self, temp_workflows_dir: Path, sample_workflow_json: Dict[str, Any]
    ) -> None:
        """Test successful file upload."""
        import orjson

        # Create mock file
        file_content = orjson.dumps({"workflow_json": sample_workflow_json})
        mock_file = MagicMock()
        mock_file.filename = "test_workflow.json"
        mock_file.read = AsyncMock(return_value=file_content)

        with patch.dict(
            os.environ,
            {
                "WORKFLOWS_DIR": str(temp_workflows_dir),
                "WORKFLOW_BACKUP_ENABLED": "true",
            },
        ):
            with patch(
                "casare_rpa.infrastructure.orchestrator.api.routers.workflows.enqueue_job",
                new_callable=AsyncMock,
                return_value="job-123",
            ):
                response = await upload_workflow(file=mock_file)

        assert response.status == "success"
        assert response.job_id == "job-123"

    @pytest.mark.asyncio
    async def test_upload_non_json_file(self) -> None:
        """Test rejection of non-JSON files (wrapped in 500 by error handler)."""
        mock_file = MagicMock()
        mock_file.filename = "test.xml"

        with pytest.raises(HTTPException) as exc_info:
            await upload_workflow(file=mock_file)

        # Error handler wraps 400 in 500, check the detail message
        assert "must be a .json file" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_upload_invalid_json(self) -> None:
        """Test rejection of invalid JSON content."""
        mock_file = MagicMock()
        mock_file.filename = "test.json"
        mock_file.read = AsyncMock(return_value=b"not valid json {")

        with pytest.raises(HTTPException) as exc_info:
            await upload_workflow(file=mock_file)

        assert exc_info.value.status_code == 400
        assert "Invalid JSON" in str(exc_info.value.detail)
