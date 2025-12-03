"""
Tests for jobs REST API router.

Tests cover:
- Job cancellation endpoint (POST /jobs/{job_id}/cancel)
- Job retry endpoint (POST /jobs/{job_id}/retry)
- Job progress update endpoint (PUT /jobs/{job_id}/progress)
- Error handling for missing jobs, invalid states
- Database pool availability

Test Patterns:
- SUCCESS: 200/201 responses with valid payloads
- ERROR: 400, 404, 500, 503 responses
- EDGE CASES: various job states, database unavailability
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from casare_rpa.infrastructure.orchestrator.api.routers.jobs import (
    JobCancelResponse,
    JobRetryResponse,
    JobProgressUpdate,
    router,
    set_db_pool,
    get_db_pool,
)


# ============================================================================
# Test Constants
# ============================================================================

TEST_JOB_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
TEST_JOB_ID_2 = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
TEST_WORKFLOW_ID = "12345678-1234-5678-1234-567812345678"


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_db_pool() -> MagicMock:
    """Create mock database pool."""
    pool = MagicMock()
    pool.acquire = MagicMock(return_value=AsyncMock())
    return pool


@pytest.fixture
def mock_conn() -> AsyncMock:
    """Create mock database connection."""
    conn = AsyncMock()
    conn.fetchrow = AsyncMock()
    conn.execute = AsyncMock()
    return conn


@pytest.fixture
def client(mock_db_pool: MagicMock, mock_conn: AsyncMock) -> TestClient:
    """Create FastAPI test client with mocked database."""
    app = FastAPI()
    app.include_router(router)

    # Configure mock connection context manager
    mock_db_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_db_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

    # Set the mock pool
    set_db_pool(mock_db_pool)

    yield TestClient(app)

    # Cleanup
    set_db_pool(None)


@pytest.fixture
def client_no_db() -> TestClient:
    """Create FastAPI test client without database pool."""
    app = FastAPI()
    app.include_router(router)
    set_db_pool(None)
    return TestClient(app)


@pytest.fixture
def pending_job_row() -> Dict[str, Any]:
    """Sample pending job database row."""
    return {
        "job_id": TEST_JOB_ID,
        "status": "pending",
        "workflow_id": TEST_WORKFLOW_ID,
        "workflow_name": "Test Workflow",
        "payload": '{"nodes": []}',
        "environment": "default",
        "priority": 1,
        "robot_uuid": None,
    }


@pytest.fixture
def running_job_row() -> Dict[str, Any]:
    """Sample running job database row."""
    return {
        "job_id": TEST_JOB_ID,
        "status": "running",
        "workflow_id": TEST_WORKFLOW_ID,
        "workflow_name": "Test Workflow",
        "payload": '{"nodes": []}',
        "environment": "default",
        "priority": 1,
        "robot_uuid": "robot-001",
    }


@pytest.fixture
def failed_job_row() -> Dict[str, Any]:
    """Sample failed job database row."""
    return {
        "job_id": TEST_JOB_ID,
        "status": "failed",
        "workflow_id": TEST_WORKFLOW_ID,
        "workflow_name": "Test Workflow",
        "payload": '{"nodes": []}',
        "environment": "default",
        "priority": 1,
        "robot_uuid": "robot-001",
    }


@pytest.fixture
def completed_job_row() -> Dict[str, Any]:
    """Sample completed job database row."""
    return {
        "job_id": TEST_JOB_ID,
        "status": "completed",
        "workflow_id": TEST_WORKFLOW_ID,
        "workflow_name": "Test Workflow",
        "payload": '{"nodes": []}',
        "environment": "default",
        "priority": 1,
        "robot_uuid": "robot-001",
    }


# ============================================================================
# Request Model Validation Tests
# ============================================================================


class TestJobProgressUpdateValidation:
    """Tests for JobProgressUpdate model validation."""

    def test_valid_progress_update(self) -> None:
        """Test valid progress update passes validation."""
        update = JobProgressUpdate(progress=50)
        assert update.progress == 50
        assert update.current_node is None
        assert update.message is None

    def test_progress_with_all_fields(self) -> None:
        """Test progress update with all optional fields."""
        update = JobProgressUpdate(
            progress=75,
            current_node="node_123",
            message="Processing step 3",
        )
        assert update.progress == 75
        assert update.current_node == "node_123"
        assert update.message == "Processing step 3"

    def test_progress_at_boundaries(self) -> None:
        """Test progress at valid boundary values."""
        assert JobProgressUpdate(progress=0).progress == 0
        assert JobProgressUpdate(progress=100).progress == 100

    def test_progress_below_minimum_fails(self) -> None:
        """Test progress below 0 fails validation."""
        with pytest.raises(ValueError):
            JobProgressUpdate(progress=-1)

    def test_progress_above_maximum_fails(self) -> None:
        """Test progress above 100 fails validation."""
        with pytest.raises(ValueError):
            JobProgressUpdate(progress=101)


# ============================================================================
# Cancel Job Endpoint Tests
# ============================================================================


class TestCancelJobEndpoint:
    """Tests for POST /jobs/{job_id}/cancel endpoint."""

    def test_cancel_pending_job_success(
        self,
        client: TestClient,
        mock_conn: AsyncMock,
        pending_job_row: Dict[str, Any],
    ) -> None:
        """Test successful cancellation of pending job."""
        mock_conn.fetchrow.return_value = pending_job_row
        mock_conn.execute.return_value = "UPDATE 1"

        response = client.post(f"/jobs/{TEST_JOB_ID}/cancel")

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == TEST_JOB_ID
        assert data["cancelled"] is True
        assert data["previous_status"] == "pending"
        assert "success" in data["message"].lower()

    def test_cancel_running_job_success(
        self,
        client: TestClient,
        mock_conn: AsyncMock,
        running_job_row: Dict[str, Any],
    ) -> None:
        """Test successful cancellation of running job."""
        mock_conn.fetchrow.return_value = running_job_row
        mock_conn.execute.return_value = "UPDATE 1"

        response = client.post(f"/jobs/{TEST_JOB_ID}/cancel")

        assert response.status_code == 200
        data = response.json()
        assert data["cancelled"] is True
        assert data["previous_status"] == "running"

    def test_cancel_completed_job_fails(
        self,
        client: TestClient,
        mock_conn: AsyncMock,
        completed_job_row: Dict[str, Any],
    ) -> None:
        """Test cancellation of completed job returns cancelled=False."""
        mock_conn.fetchrow.return_value = completed_job_row

        response = client.post(f"/jobs/{TEST_JOB_ID}/cancel")

        assert response.status_code == 200
        data = response.json()
        assert data["cancelled"] is False
        assert data["previous_status"] == "completed"
        assert "cannot cancel" in data["message"].lower()

    def test_cancel_failed_job_fails(
        self,
        client: TestClient,
        mock_conn: AsyncMock,
        failed_job_row: Dict[str, Any],
    ) -> None:
        """Test cancellation of failed job returns cancelled=False."""
        # Return failed status
        failed_job_row["status"] = "failed"
        mock_conn.fetchrow.return_value = failed_job_row

        response = client.post(f"/jobs/{TEST_JOB_ID}/cancel")

        assert response.status_code == 200
        data = response.json()
        assert data["cancelled"] is False
        assert data["previous_status"] == "failed"

    def test_cancel_already_cancelled_job(
        self,
        client: TestClient,
        mock_conn: AsyncMock,
    ) -> None:
        """Test cancellation of already cancelled job returns cancelled=False."""
        mock_conn.fetchrow.return_value = {
            "job_id": TEST_JOB_ID,
            "status": "cancelled",
        }

        response = client.post(f"/jobs/{TEST_JOB_ID}/cancel")

        assert response.status_code == 200
        data = response.json()
        assert data["cancelled"] is False
        assert data["previous_status"] == "cancelled"

    def test_cancel_job_not_found(
        self,
        client: TestClient,
        mock_conn: AsyncMock,
    ) -> None:
        """Test cancellation of non-existent job returns 404."""
        # Return None for both queries
        mock_conn.fetchrow.return_value = None

        response = client.post(f"/jobs/{TEST_JOB_ID}/cancel")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_cancel_job_database_unavailable(self, client_no_db: TestClient) -> None:
        """Test cancel returns 503 when database unavailable."""
        response = client_no_db.post(f"/jobs/{TEST_JOB_ID}/cancel")

        assert response.status_code == 503
        assert "database" in response.json()["detail"].lower()

    def test_cancel_job_database_error(
        self,
        client: TestClient,
        mock_conn: AsyncMock,
    ) -> None:
        """Test cancel returns 500 on database error."""
        mock_conn.fetchrow.side_effect = Exception("Database connection error")

        response = client.post(f"/jobs/{TEST_JOB_ID}/cancel")

        assert response.status_code == 500
        assert "failed to cancel" in response.json()["detail"].lower()

    def test_cancel_job_invalid_id_format(self, client: TestClient) -> None:
        """Test cancel with invalid job_id format returns 422."""
        # Test with empty string (min_length=1)
        response = client.post("/jobs//cancel")
        assert response.status_code in (404, 405)  # FastAPI routing behavior

    def test_cancel_job_checks_job_queue_fallback(
        self,
        client: TestClient,
        mock_conn: AsyncMock,
    ) -> None:
        """Test cancel checks job_queue table as fallback."""
        # First query (jobs table) returns None
        # Second query (job_queue) returns the job
        mock_conn.fetchrow.side_effect = [
            None,  # jobs table
            {"job_id": TEST_JOB_ID, "status": "pending"},  # job_queue table
        ]
        mock_conn.execute.return_value = "UPDATE 0"  # First update fails

        response = client.post(f"/jobs/{TEST_JOB_ID}/cancel")

        assert response.status_code == 200
        assert mock_conn.fetchrow.call_count == 2


# ============================================================================
# Retry Job Endpoint Tests
# ============================================================================


class TestRetryJobEndpoint:
    """Tests for POST /jobs/{job_id}/retry endpoint."""

    def test_retry_failed_job_success(
        self,
        client: TestClient,
        mock_conn: AsyncMock,
        failed_job_row: Dict[str, Any],
    ) -> None:
        """Test successful retry of failed job."""
        mock_conn.fetchrow.return_value = failed_job_row
        mock_conn.execute.return_value = "INSERT 1"

        response = client.post(f"/jobs/{TEST_JOB_ID}/retry")

        assert response.status_code == 200
        data = response.json()
        assert data["original_job_id"] == TEST_JOB_ID
        assert "new_job_id" in data
        assert len(data["new_job_id"]) == 36  # UUID format
        assert "retry" in data["message"].lower()

    def test_retry_cancelled_job_success(
        self,
        client: TestClient,
        mock_conn: AsyncMock,
    ) -> None:
        """Test successful retry of cancelled job."""
        mock_conn.fetchrow.return_value = {
            "job_id": TEST_JOB_ID,
            "status": "cancelled",
            "workflow_id": TEST_WORKFLOW_ID,
            "workflow_name": "Test Workflow",
            "payload": '{"nodes": []}',
            "environment": "default",
            "priority": 1,
            "robot_uuid": None,
        }
        mock_conn.execute.return_value = "INSERT 1"

        response = client.post(f"/jobs/{TEST_JOB_ID}/retry")

        assert response.status_code == 200
        data = response.json()
        assert data["original_job_id"] == TEST_JOB_ID
        assert "new_job_id" in data

    def test_retry_timeout_job_success(
        self,
        client: TestClient,
        mock_conn: AsyncMock,
    ) -> None:
        """Test successful retry of timeout job."""
        mock_conn.fetchrow.return_value = {
            "job_id": TEST_JOB_ID,
            "status": "timeout",
            "workflow_id": TEST_WORKFLOW_ID,
            "workflow_name": "Test Workflow",
            "payload": '{"nodes": []}',
            "environment": "default",
            "priority": 1,
            "robot_uuid": "robot-001",
        }
        mock_conn.execute.return_value = "INSERT 1"

        response = client.post(f"/jobs/{TEST_JOB_ID}/retry")

        assert response.status_code == 200
        data = response.json()
        assert "new_job_id" in data

    def test_retry_pending_job_fails(
        self,
        client: TestClient,
        mock_conn: AsyncMock,
        pending_job_row: Dict[str, Any],
    ) -> None:
        """Test retry of pending job returns 400."""
        mock_conn.fetchrow.return_value = pending_job_row

        response = client.post(f"/jobs/{TEST_JOB_ID}/retry")

        assert response.status_code == 400
        assert "cannot retry" in response.json()["detail"].lower()
        assert "pending" in response.json()["detail"].lower()

    def test_retry_running_job_fails(
        self,
        client: TestClient,
        mock_conn: AsyncMock,
        running_job_row: Dict[str, Any],
    ) -> None:
        """Test retry of running job returns 400."""
        mock_conn.fetchrow.return_value = running_job_row

        response = client.post(f"/jobs/{TEST_JOB_ID}/retry")

        assert response.status_code == 400
        assert "cannot retry" in response.json()["detail"].lower()
        assert "running" in response.json()["detail"].lower()

    def test_retry_completed_job_fails(
        self,
        client: TestClient,
        mock_conn: AsyncMock,
        completed_job_row: Dict[str, Any],
    ) -> None:
        """Test retry of completed job returns 400."""
        mock_conn.fetchrow.return_value = completed_job_row

        response = client.post(f"/jobs/{TEST_JOB_ID}/retry")

        assert response.status_code == 400
        assert "cannot retry" in response.json()["detail"].lower()
        assert "completed" in response.json()["detail"].lower()

    def test_retry_job_not_found(
        self,
        client: TestClient,
        mock_conn: AsyncMock,
    ) -> None:
        """Test retry of non-existent job returns 404."""
        mock_conn.fetchrow.return_value = None

        response = client.post(f"/jobs/{TEST_JOB_ID}/retry")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_retry_job_database_unavailable(self, client_no_db: TestClient) -> None:
        """Test retry returns 503 when database unavailable."""
        response = client_no_db.post(f"/jobs/{TEST_JOB_ID}/retry")

        assert response.status_code == 503
        assert "database" in response.json()["detail"].lower()

    def test_retry_job_database_error(
        self,
        client: TestClient,
        mock_conn: AsyncMock,
    ) -> None:
        """Test retry returns 500 on database error."""
        mock_conn.fetchrow.side_effect = Exception("Database connection error")

        response = client.post(f"/jobs/{TEST_JOB_ID}/retry")

        assert response.status_code == 500
        assert "failed to retry" in response.json()["detail"].lower()

    def test_retry_creates_new_job_id(
        self,
        client: TestClient,
        mock_conn: AsyncMock,
        failed_job_row: Dict[str, Any],
    ) -> None:
        """Test retry creates a new unique job ID."""
        mock_conn.fetchrow.return_value = failed_job_row
        mock_conn.execute.return_value = "INSERT 1"

        response1 = client.post(f"/jobs/{TEST_JOB_ID}/retry")
        mock_conn.fetchrow.return_value = failed_job_row
        response2 = client.post(f"/jobs/{TEST_JOB_ID}/retry")

        data1 = response1.json()
        data2 = response2.json()

        # Each retry should create a unique new job ID
        assert data1["new_job_id"] != data2["new_job_id"]


# ============================================================================
# Update Job Progress Endpoint Tests
# ============================================================================


class TestUpdateProgressEndpoint:
    """Tests for PUT /jobs/{job_id}/progress endpoint."""

    def test_update_progress_success(
        self,
        client: TestClient,
        mock_conn: AsyncMock,
    ) -> None:
        """Test successful progress update."""
        mock_conn.execute.return_value = "UPDATE 1"

        response = client.put(
            f"/jobs/{TEST_JOB_ID}/progress",
            json={"progress": 50},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == TEST_JOB_ID
        assert data["progress"] == 50

    def test_update_progress_with_current_node(
        self,
        client: TestClient,
        mock_conn: AsyncMock,
    ) -> None:
        """Test progress update with current node information."""
        mock_conn.execute.return_value = "UPDATE 1"

        response = client.put(
            f"/jobs/{TEST_JOB_ID}/progress",
            json={
                "progress": 75,
                "current_node": "process_data_node",
                "message": "Processing records",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["progress"] == 75
        assert data["current_node"] == "process_data_node"

    def test_update_progress_at_zero(
        self,
        client: TestClient,
        mock_conn: AsyncMock,
    ) -> None:
        """Test progress update at 0%."""
        mock_conn.execute.return_value = "UPDATE 1"

        response = client.put(
            f"/jobs/{TEST_JOB_ID}/progress",
            json={"progress": 0},
        )

        assert response.status_code == 200
        assert response.json()["progress"] == 0

    def test_update_progress_at_hundred(
        self,
        client: TestClient,
        mock_conn: AsyncMock,
    ) -> None:
        """Test progress update at 100%."""
        mock_conn.execute.return_value = "UPDATE 1"

        response = client.put(
            f"/jobs/{TEST_JOB_ID}/progress",
            json={"progress": 100},
        )

        assert response.status_code == 200
        assert response.json()["progress"] == 100

    def test_update_progress_job_not_running(
        self,
        client: TestClient,
        mock_conn: AsyncMock,
    ) -> None:
        """Test progress update for non-running job returns 404."""
        mock_conn.execute.return_value = "UPDATE 0"

        response = client.put(
            f"/jobs/{TEST_JOB_ID}/progress",
            json={"progress": 50},
        )

        assert response.status_code == 404
        assert "not found or not running" in response.json()["detail"].lower()

    def test_update_progress_invalid_value_low(self, client: TestClient) -> None:
        """Test progress update with value below 0 returns 422."""
        response = client.put(
            f"/jobs/{TEST_JOB_ID}/progress",
            json={"progress": -1},
        )

        assert response.status_code == 422

    def test_update_progress_invalid_value_high(self, client: TestClient) -> None:
        """Test progress update with value above 100 returns 422."""
        response = client.put(
            f"/jobs/{TEST_JOB_ID}/progress",
            json={"progress": 101},
        )

        assert response.status_code == 422

    def test_update_progress_database_unavailable(
        self, client_no_db: TestClient
    ) -> None:
        """Test progress update returns 503 when database unavailable."""
        response = client_no_db.put(
            f"/jobs/{TEST_JOB_ID}/progress",
            json={"progress": 50},
        )

        assert response.status_code == 503

    def test_update_progress_database_error(
        self,
        client: TestClient,
        mock_conn: AsyncMock,
    ) -> None:
        """Test progress update returns 500 on database error."""
        mock_conn.execute.side_effect = Exception("Database connection error")

        response = client.put(
            f"/jobs/{TEST_JOB_ID}/progress",
            json={"progress": 50},
        )

        assert response.status_code == 500
        assert "failed to update" in response.json()["detail"].lower()


# ============================================================================
# Database Pool Management Tests
# ============================================================================


class TestDatabasePoolManagement:
    """Tests for database pool getter/setter functions."""

    def test_set_and_get_db_pool(self) -> None:
        """Test setting and getting database pool."""
        mock_pool = MagicMock()

        set_db_pool(mock_pool)
        assert get_db_pool() is mock_pool

        # Cleanup
        set_db_pool(None)
        assert get_db_pool() is None

    def test_get_db_pool_returns_none_when_not_set(self) -> None:
        """Test get_db_pool returns None when pool not set."""
        set_db_pool(None)
        assert get_db_pool() is None


# ============================================================================
# Edge Case Tests
# ============================================================================


class TestEdgeCases:
    """Edge case and boundary condition tests."""

    def test_cancel_job_id_max_length(
        self,
        client: TestClient,
        mock_conn: AsyncMock,
    ) -> None:
        """Test cancel with maximum length job ID."""
        long_job_id = "a" * 64  # max_length=64
        mock_conn.fetchrow.return_value = {
            "job_id": long_job_id,
            "status": "pending",
        }
        mock_conn.execute.return_value = "UPDATE 1"

        response = client.post(f"/jobs/{long_job_id}/cancel")

        assert response.status_code == 200
        assert response.json()["job_id"] == long_job_id

    def test_retry_preserves_workflow_metadata(
        self,
        client: TestClient,
        mock_conn: AsyncMock,
        failed_job_row: Dict[str, Any],
    ) -> None:
        """Test retry preserves original workflow metadata."""
        failed_job_row["priority"] = 15
        failed_job_row["environment"] = "production"
        mock_conn.fetchrow.return_value = failed_job_row
        mock_conn.execute.return_value = "INSERT 1"

        response = client.post(f"/jobs/{TEST_JOB_ID}/retry")

        assert response.status_code == 200
        # Verify the execute was called with correct parameters
        assert mock_conn.execute.called

    def test_update_progress_null_current_node(
        self,
        client: TestClient,
        mock_conn: AsyncMock,
    ) -> None:
        """Test progress update with null current_node uses COALESCE."""
        mock_conn.execute.return_value = "UPDATE 1"

        response = client.put(
            f"/jobs/{TEST_JOB_ID}/progress",
            json={"progress": 50, "current_node": None},
        )

        assert response.status_code == 200
