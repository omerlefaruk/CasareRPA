"""
Tests for robots REST API router.

Tests cover:
- Robot registration (success, upsert, validation)
- Robot listing (with filters, pagination)
- Robot retrieval (success, not found)
- Robot update (partial, full, not found)
- Robot status update (valid statuses, heartbeat)
- Robot deletion (success, not found)
- Robot heartbeat (with/without metrics)
- Database unavailability handling

Note: Tests use TestClient integration tests because endpoints use slowapi
rate limiting which requires real Starlette Request objects.
"""

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from casare_rpa.infrastructure.orchestrator.api.routers.robots import (
    RobotRegistration,
    RobotUpdate,
    RobotStatusUpdate,
    RobotResponse,
    RobotListResponse,
    router,
    set_db_pool,
    get_db_pool,
    _row_to_response,
)


# ============================================================================
# Test Data
# ============================================================================

TEST_ROBOT_ID = "robot-test-001"
TEST_ROBOT_ID_2 = "robot-test-002"


def create_sample_robot_row(
    robot_id: str = TEST_ROBOT_ID,
    name: str = "Test Robot",
    hostname: str = "test-host",
    status: str = "idle",
    environment: str = "production",
    max_concurrent_jobs: int = 3,
    capabilities: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    current_job_ids: Optional[List[str]] = None,
    metrics: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a sample robot database row."""
    now = datetime.now(timezone.utc)
    return {
        "robot_id": robot_id,
        "name": name,
        "hostname": hostname,
        "status": status,
        "environment": environment,
        "max_concurrent_jobs": max_concurrent_jobs,
        "capabilities": capabilities or ["browser", "desktop"],
        "tags": tags or ["production", "tier1"],
        "current_job_ids": current_job_ids or [],
        "last_seen": now,
        "last_heartbeat": now,
        "created_at": now,
        "metrics": metrics or {"cpu_percent": 25.5, "memory_mb": 1024},
    }


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_registration() -> RobotRegistration:
    """Sample robot registration request."""
    return RobotRegistration(
        robot_id=TEST_ROBOT_ID,
        name="Test Robot",
        hostname="test-host.local",
        capabilities=["browser", "desktop", "http"],
        environment="production",
        max_concurrent_jobs=3,
        tags=["tier1", "high-priority"],
    )


@pytest.fixture
def sample_registration_minimal() -> RobotRegistration:
    """Minimal robot registration request."""
    return RobotRegistration(
        robot_id="robot-minimal",
        name="Minimal Robot",
        hostname="minimal-host",
    )


@pytest.fixture
def sample_update() -> RobotUpdate:
    """Sample robot update request."""
    return RobotUpdate(
        name="Updated Robot Name",
        hostname="new-hostname.local",
        capabilities=["browser", "http"],
        environment="staging",
        max_concurrent_jobs=5,
        tags=["updated", "tier2"],
    )


@pytest.fixture
def sample_update_partial() -> RobotUpdate:
    """Partial robot update request (only name)."""
    return RobotUpdate(name="Renamed Robot")


@pytest.fixture
def sample_status_update() -> RobotStatusUpdate:
    """Sample status update request."""
    return RobotStatusUpdate(status="busy")


@pytest.fixture
def mock_db_pool():
    """Create mock database pool with async context manager."""
    pool = MagicMock()
    conn = AsyncMock()

    # Set up async context manager properly
    context_manager = AsyncMock()
    context_manager.__aenter__.return_value = conn
    context_manager.__aexit__.return_value = None
    pool.acquire.return_value = context_manager

    return pool, conn


@pytest.fixture
def client() -> TestClient:
    """Create FastAPI test client."""
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_db_pool():
    """Ensure db pool is reset after each test."""
    yield
    set_db_pool(None)


# ============================================================================
# RobotRegistration Validation Tests
# ============================================================================


class TestRobotRegistrationValidation:
    """Tests for RobotRegistration model validation."""

    def test_valid_registration(self, sample_registration: RobotRegistration) -> None:
        """Test valid registration passes validation."""
        assert sample_registration.robot_id == TEST_ROBOT_ID
        assert sample_registration.name == "Test Robot"
        assert "browser" in sample_registration.capabilities

    def test_valid_minimal_registration(
        self, sample_registration_minimal: RobotRegistration
    ) -> None:
        """Test minimal registration with defaults."""
        assert sample_registration_minimal.robot_id == "robot-minimal"
        assert sample_registration_minimal.capabilities == []
        assert sample_registration_minimal.environment == "default"
        assert sample_registration_minimal.max_concurrent_jobs == 1

    def test_robot_id_empty_raises_error(self) -> None:
        """Test empty robot_id raises validation error."""
        with pytest.raises(ValueError):
            RobotRegistration(robot_id="", name="Test", hostname="host")

    def test_robot_id_too_long_raises_error(self) -> None:
        """Test robot_id exceeding max length raises error."""
        with pytest.raises(ValueError):
            RobotRegistration(robot_id="x" * 65, name="Test", hostname="host")

    def test_name_empty_raises_error(self) -> None:
        """Test empty name raises validation error."""
        with pytest.raises(ValueError):
            RobotRegistration(robot_id="robot-1", name="", hostname="host")

    def test_max_concurrent_jobs_invalid_range(self) -> None:
        """Test max_concurrent_jobs outside valid range raises error."""
        with pytest.raises(ValueError):
            RobotRegistration(
                robot_id="robot-1",
                name="Test",
                hostname="host",
                max_concurrent_jobs=0,
            )
        with pytest.raises(ValueError):
            RobotRegistration(
                robot_id="robot-1",
                name="Test",
                hostname="host",
                max_concurrent_jobs=101,
            )


# ============================================================================
# RobotStatusUpdate Validation Tests
# ============================================================================


class TestRobotStatusUpdateValidation:
    """Tests for RobotStatusUpdate model validation."""

    @pytest.mark.parametrize(
        "status", ["idle", "busy", "offline", "error", "maintenance"]
    )
    def test_valid_statuses(self, status: str) -> None:
        """Test all valid status values."""
        update = RobotStatusUpdate(status=status)
        assert update.status == status

    def test_invalid_status_raises_error(self) -> None:
        """Test invalid status raises validation error."""
        with pytest.raises(ValueError):
            RobotStatusUpdate(status="invalid")

    def test_status_case_sensitive(self) -> None:
        """Test status is case-sensitive."""
        with pytest.raises(ValueError):
            RobotStatusUpdate(status="IDLE")


# ============================================================================
# Helper Function Tests
# ============================================================================


class TestRowToResponse:
    """Tests for _row_to_response helper function."""

    def test_converts_row_to_response(self) -> None:
        """Test converting database row to response model."""
        row = create_sample_robot_row()
        response = _row_to_response(row)

        assert response.robot_id == TEST_ROBOT_ID
        assert response.name == "Test Robot"
        assert response.hostname == "test-host"
        assert response.status == "idle"
        assert response.environment == "production"
        assert response.max_concurrent_jobs == 3
        assert "browser" in response.capabilities
        assert "production" in response.tags

    def test_handles_string_jsonb_fields(self) -> None:
        """Test parsing JSONB fields stored as strings."""
        row = create_sample_robot_row()
        row["capabilities"] = '["browser", "desktop"]'
        row["tags"] = '["tag1"]'
        row["current_job_ids"] = '["job-1"]'
        row["metrics"] = '{"cpu": 50}'

        response = _row_to_response(row)

        assert response.capabilities == ["browser", "desktop"]
        assert response.tags == ["tag1"]
        assert response.current_job_ids == ["job-1"]
        assert response.metrics == {"cpu": 50}

    def test_handles_none_values(self) -> None:
        """Test handling None values for optional fields."""
        row = {
            "robot_id": TEST_ROBOT_ID,
            "name": "Test",
            "hostname": "host",
            "status": "idle",
            "environment": "default",
            "max_concurrent_jobs": 1,
            "capabilities": None,
            "tags": None,
            "current_job_ids": None,
            "metrics": None,
            "last_seen": None,
            "last_heartbeat": None,
            "created_at": None,
        }

        response = _row_to_response(row)

        assert response.capabilities == []
        assert response.tags == []
        assert response.current_job_ids == []
        assert response.metrics == {}
        assert response.last_seen is None

    def test_handles_missing_keys(self) -> None:
        """Test handling missing keys with defaults."""
        row = {}
        response = _row_to_response(row)

        assert response.robot_id == ""
        assert response.name == ""
        assert response.status == "offline"
        assert response.environment == "default"


# ============================================================================
# Database Pool Tests
# ============================================================================


class TestDatabasePoolManagement:
    """Tests for database pool set/get functions."""

    def test_set_and_get_db_pool(self) -> None:
        """Test setting and getting database pool."""
        mock_pool = MagicMock()
        set_db_pool(mock_pool)
        assert get_db_pool() is mock_pool
        set_db_pool(None)

    def test_get_db_pool_returns_none_when_not_set(self) -> None:
        """Test get_db_pool returns None when not set."""
        set_db_pool(None)
        assert get_db_pool() is None


# ============================================================================
# Register Robot Endpoint Tests (Integration)
# ============================================================================


class TestRegisterRobotEndpoint:
    """Tests for POST /robots/register endpoint."""

    def test_register_robot_database_unavailable(
        self,
        client: TestClient,
    ) -> None:
        """Test registration fails when database unavailable."""
        set_db_pool(None)

        response = client.post(
            "/robots/register",
            json={
                "robot_id": TEST_ROBOT_ID,
                "name": "Test Robot",
                "hostname": "test-host",
            },
        )

        assert response.status_code == 503
        assert "Database not available" in response.json()["detail"]

    def test_register_robot_success(
        self,
        client: TestClient,
        mock_db_pool,
    ) -> None:
        """Test successful robot registration."""
        pool, conn = mock_db_pool
        robot_row = create_sample_robot_row()
        conn.fetchrow.return_value = robot_row

        set_db_pool(pool)

        response = client.post(
            "/robots/register",
            json={
                "robot_id": TEST_ROBOT_ID,
                "name": "Test Robot",
                "hostname": "test-host.local",
                "capabilities": ["browser", "desktop"],
                "environment": "production",
                "max_concurrent_jobs": 3,
                "tags": ["tier1"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["robot_id"] == TEST_ROBOT_ID
        assert data["name"] == "Test Robot"
        conn.execute.assert_awaited_once()
        conn.fetchrow.assert_awaited_once()

    def test_register_robot_fetch_fails(
        self,
        client: TestClient,
        mock_db_pool,
    ) -> None:
        """Test registration fails if fetch returns None."""
        pool, conn = mock_db_pool
        conn.fetchrow.return_value = None

        set_db_pool(pool)

        response = client.post(
            "/robots/register",
            json={
                "robot_id": TEST_ROBOT_ID,
                "name": "Test Robot",
                "hostname": "test-host",
            },
        )

        assert response.status_code == 500
        assert "Failed to fetch registered robot" in response.json()["detail"]

    def test_register_robot_database_error(
        self,
        client: TestClient,
        mock_db_pool,
    ) -> None:
        """Test registration handles database errors."""
        pool, conn = mock_db_pool
        conn.execute.side_effect = Exception("Connection lost")

        set_db_pool(pool)

        response = client.post(
            "/robots/register",
            json={
                "robot_id": TEST_ROBOT_ID,
                "name": "Test Robot",
                "hostname": "test-host",
            },
        )

        assert response.status_code == 500
        assert "Registration failed" in response.json()["detail"]

    def test_register_robot_validation_error(
        self,
        client: TestClient,
    ) -> None:
        """Test registration validation errors."""
        set_db_pool(MagicMock())

        # Empty robot_id
        response = client.post(
            "/robots/register",
            json={
                "robot_id": "",
                "name": "Test Robot",
                "hostname": "test-host",
            },
        )

        assert response.status_code == 422  # Validation error


# ============================================================================
# List Robots Endpoint Tests (Integration)
# ============================================================================


class TestListRobotsEndpoint:
    """Tests for GET /robots endpoint."""

    def test_list_robots_database_unavailable(
        self,
        client: TestClient,
    ) -> None:
        """Test listing fails when database unavailable."""
        set_db_pool(None)

        response = client.get("/robots")

        assert response.status_code == 503

    def test_list_robots_success(
        self,
        client: TestClient,
        mock_db_pool,
    ) -> None:
        """Test successful robot listing."""
        pool, conn = mock_db_pool
        robot_rows = [
            create_sample_robot_row(robot_id="robot-1", name="Robot 1"),
            create_sample_robot_row(robot_id="robot-2", name="Robot 2"),
        ]
        conn.fetchval.return_value = 2
        conn.fetch.return_value = robot_rows

        set_db_pool(pool)

        response = client.get("/robots")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["robots"]) == 2
        assert data["robots"][0]["robot_id"] == "robot-1"

    def test_list_robots_with_status_filter(
        self,
        client: TestClient,
        mock_db_pool,
    ) -> None:
        """Test listing robots with status filter."""
        pool, conn = mock_db_pool
        robot_rows = [create_sample_robot_row(status="idle")]
        conn.fetchval.return_value = 1
        conn.fetch.return_value = robot_rows

        set_db_pool(pool)

        response = client.get("/robots?status=idle")

        assert response.status_code == 200
        # Verify filter was applied in query
        call_args = conn.fetch.call_args[0][0]
        assert "status = $" in call_args

    def test_list_robots_with_environment_filter(
        self,
        client: TestClient,
        mock_db_pool,
    ) -> None:
        """Test listing robots with environment filter."""
        pool, conn = mock_db_pool
        robot_rows = [create_sample_robot_row(environment="production")]
        conn.fetchval.return_value = 1
        conn.fetch.return_value = robot_rows

        set_db_pool(pool)

        response = client.get("/robots?environment=production")

        assert response.status_code == 200
        call_args = conn.fetch.call_args[0][0]
        assert "environment = $" in call_args

    def test_list_robots_with_pagination(
        self,
        client: TestClient,
        mock_db_pool,
    ) -> None:
        """Test listing robots with pagination."""
        pool, conn = mock_db_pool
        conn.fetchval.return_value = 100
        conn.fetch.return_value = [create_sample_robot_row()]

        set_db_pool(pool)

        response = client.get("/robots?limit=10&offset=20")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 100

    def test_list_robots_empty(
        self,
        client: TestClient,
        mock_db_pool,
    ) -> None:
        """Test listing when no robots exist."""
        pool, conn = mock_db_pool
        conn.fetchval.return_value = 0
        conn.fetch.return_value = []

        set_db_pool(pool)

        response = client.get("/robots")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["robots"]) == 0

    def test_list_robots_database_error(
        self,
        client: TestClient,
        mock_db_pool,
    ) -> None:
        """Test list robots handles database errors."""
        pool, conn = mock_db_pool
        conn.fetchval.side_effect = Exception("Query timeout")

        set_db_pool(pool)

        response = client.get("/robots")

        assert response.status_code == 500
        assert "Failed to list robots" in response.json()["detail"]


# ============================================================================
# Get Robot Endpoint Tests (Integration)
# ============================================================================


class TestGetRobotEndpoint:
    """Tests for GET /robots/{robot_id} endpoint."""

    def test_get_robot_database_unavailable(
        self,
        client: TestClient,
    ) -> None:
        """Test retrieval fails when database unavailable."""
        set_db_pool(None)

        response = client.get(f"/robots/{TEST_ROBOT_ID}")

        assert response.status_code == 503

    def test_get_robot_success(
        self,
        client: TestClient,
        mock_db_pool,
    ) -> None:
        """Test successful robot retrieval."""
        pool, conn = mock_db_pool
        robot_row = create_sample_robot_row()
        conn.fetchrow.return_value = robot_row

        set_db_pool(pool)

        response = client.get(f"/robots/{TEST_ROBOT_ID}")

        assert response.status_code == 200
        data = response.json()
        assert data["robot_id"] == TEST_ROBOT_ID
        assert data["name"] == "Test Robot"

    def test_get_robot_not_found(
        self,
        client: TestClient,
        mock_db_pool,
    ) -> None:
        """Test 404 when robot not found."""
        pool, conn = mock_db_pool
        conn.fetchrow.return_value = None

        set_db_pool(pool)

        response = client.get("/robots/nonexistent-robot")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


# ============================================================================
# Update Robot Endpoint Tests (Integration)
# ============================================================================


class TestUpdateRobotEndpoint:
    """Tests for PUT /robots/{robot_id} endpoint."""

    def test_update_robot_database_unavailable(
        self,
        client: TestClient,
    ) -> None:
        """Test update fails when database unavailable."""
        set_db_pool(None)

        response = client.put(
            f"/robots/{TEST_ROBOT_ID}",
            json={"name": "Updated Name"},
        )

        assert response.status_code == 503

    def test_update_robot_success(
        self,
        client: TestClient,
        mock_db_pool,
    ) -> None:
        """Test successful robot update."""
        pool, conn = mock_db_pool
        conn.fetchrow.side_effect = [
            {"robot_id": TEST_ROBOT_ID},  # exists check
            create_sample_robot_row(name="Updated Robot Name"),  # updated row
        ]

        set_db_pool(pool)

        response = client.put(
            f"/robots/{TEST_ROBOT_ID}",
            json={
                "name": "Updated Robot Name",
                "hostname": "new-host.local",
                "capabilities": ["browser"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["robot_id"] == TEST_ROBOT_ID
        conn.execute.assert_awaited_once()

    def test_update_robot_partial(
        self,
        client: TestClient,
        mock_db_pool,
    ) -> None:
        """Test partial robot update (only name)."""
        pool, conn = mock_db_pool
        conn.fetchrow.side_effect = [
            {"robot_id": TEST_ROBOT_ID},
            create_sample_robot_row(name="Renamed Robot"),
        ]

        set_db_pool(pool)

        response = client.put(
            f"/robots/{TEST_ROBOT_ID}",
            json={"name": "Renamed Robot"},
        )

        assert response.status_code == 200
        # Verify only name is in the update query
        update_call = conn.execute.call_args[0][0]
        assert "name = $" in update_call

    def test_update_robot_not_found(
        self,
        client: TestClient,
        mock_db_pool,
    ) -> None:
        """Test 404 when updating nonexistent robot."""
        pool, conn = mock_db_pool
        conn.fetchrow.return_value = None

        set_db_pool(pool)

        response = client.put(
            "/robots/nonexistent",
            json={"name": "Updated Name"},
        )

        assert response.status_code == 404


# ============================================================================
# Update Robot Status Endpoint Tests (Integration)
# ============================================================================


class TestUpdateRobotStatusEndpoint:
    """Tests for PUT /robots/{robot_id}/status endpoint."""

    def test_update_status_database_unavailable(
        self,
        client: TestClient,
    ) -> None:
        """Test status update fails when database unavailable."""
        set_db_pool(None)

        response = client.put(
            f"/robots/{TEST_ROBOT_ID}/status",
            json={"status": "busy"},
        )

        assert response.status_code == 503

    def test_update_status_success(
        self,
        client: TestClient,
        mock_db_pool,
    ) -> None:
        """Test successful status update."""
        pool, conn = mock_db_pool
        conn.execute.return_value = "UPDATE 1"
        conn.fetchrow.return_value = create_sample_robot_row(status="busy")

        set_db_pool(pool)

        response = client.put(
            f"/robots/{TEST_ROBOT_ID}/status",
            json={"status": "busy"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "busy"

    def test_update_status_not_found(
        self,
        client: TestClient,
        mock_db_pool,
    ) -> None:
        """Test 404 when updating status of nonexistent robot."""
        pool, conn = mock_db_pool
        conn.execute.return_value = "UPDATE 0"

        set_db_pool(pool)

        response = client.put(
            "/robots/nonexistent/status",
            json={"status": "busy"},
        )

        assert response.status_code == 404

    @pytest.mark.parametrize(
        "status", ["idle", "busy", "offline", "error", "maintenance"]
    )
    def test_update_status_all_valid_values(
        self,
        client: TestClient,
        mock_db_pool,
        status: str,
    ) -> None:
        """Test all valid status values can be set."""
        pool, conn = mock_db_pool
        conn.execute.return_value = "UPDATE 1"
        conn.fetchrow.return_value = create_sample_robot_row(status=status)

        set_db_pool(pool)

        response = client.put(
            f"/robots/{TEST_ROBOT_ID}/status",
            json={"status": status},
        )

        assert response.status_code == 200
        assert response.json()["status"] == status

    def test_update_status_invalid_value(
        self,
        client: TestClient,
        mock_db_pool,
    ) -> None:
        """Test invalid status value returns validation error."""
        pool, _ = mock_db_pool
        set_db_pool(pool)

        response = client.put(
            f"/robots/{TEST_ROBOT_ID}/status",
            json={"status": "invalid_status"},
        )

        assert response.status_code == 422  # Validation error


# ============================================================================
# Delete Robot Endpoint Tests (Integration)
# ============================================================================


class TestDeleteRobotEndpoint:
    """Tests for DELETE /robots/{robot_id} endpoint."""

    def test_delete_robot_database_unavailable(
        self,
        client: TestClient,
    ) -> None:
        """Test deletion fails when database unavailable."""
        set_db_pool(None)

        response = client.delete(f"/robots/{TEST_ROBOT_ID}")

        assert response.status_code == 503

    def test_delete_robot_success(
        self,
        client: TestClient,
        mock_db_pool,
    ) -> None:
        """Test successful robot deletion."""
        pool, conn = mock_db_pool
        conn.execute.return_value = "DELETE 1"

        set_db_pool(pool)

        response = client.delete(f"/robots/{TEST_ROBOT_ID}")

        assert response.status_code == 200
        data = response.json()
        assert data["deleted"] is True
        assert data["robot_id"] == TEST_ROBOT_ID

    def test_delete_robot_not_found(
        self,
        client: TestClient,
        mock_db_pool,
    ) -> None:
        """Test 404 when deleting nonexistent robot."""
        pool, conn = mock_db_pool
        conn.execute.return_value = "DELETE 0"

        set_db_pool(pool)

        response = client.delete("/robots/nonexistent")

        assert response.status_code == 404


# ============================================================================
# Robot Heartbeat Endpoint Tests (Integration)
# ============================================================================


class TestRobotHeartbeatEndpoint:
    """Tests for POST /robots/{robot_id}/heartbeat endpoint."""

    def test_heartbeat_database_unavailable(
        self,
        client: TestClient,
    ) -> None:
        """Test heartbeat fails when database unavailable."""
        set_db_pool(None)

        response = client.post(f"/robots/{TEST_ROBOT_ID}/heartbeat")

        assert response.status_code == 503

    def test_heartbeat_success_without_metrics(
        self,
        client: TestClient,
        mock_db_pool,
    ) -> None:
        """Test successful heartbeat without metrics."""
        pool, conn = mock_db_pool
        conn.execute.return_value = "UPDATE 1"

        set_db_pool(pool)

        response = client.post(f"/robots/{TEST_ROBOT_ID}/heartbeat")

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "timestamp" in data

    def test_heartbeat_success_with_metrics(
        self,
        client: TestClient,
        mock_db_pool,
    ) -> None:
        """Test successful heartbeat with metrics."""
        pool, conn = mock_db_pool
        conn.execute.return_value = "UPDATE 1"

        set_db_pool(pool)

        response = client.post(
            f"/robots/{TEST_ROBOT_ID}/heartbeat",
            json={
                "cpu_percent": 45.5,
                "memory_mb": 2048,
                "active_jobs": 2,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        # Verify metrics query was used
        call_args = conn.execute.call_args[0][0]
        assert "metrics = $" in call_args

    def test_heartbeat_not_found(
        self,
        client: TestClient,
        mock_db_pool,
    ) -> None:
        """Test 404 when heartbeat for nonexistent robot."""
        pool, conn = mock_db_pool
        conn.execute.return_value = "UPDATE 0"

        set_db_pool(pool)

        response = client.post("/robots/nonexistent/heartbeat")

        assert response.status_code == 404

    def test_heartbeat_revives_offline_robot(
        self,
        client: TestClient,
        mock_db_pool,
    ) -> None:
        """Test heartbeat changes status from offline to idle."""
        pool, conn = mock_db_pool
        conn.execute.return_value = "UPDATE 1"

        set_db_pool(pool)

        response = client.post(f"/robots/{TEST_ROBOT_ID}/heartbeat")

        assert response.status_code == 200
        # Verify CASE statement in query for status update
        call_args = conn.execute.call_args[0][0]
        assert "CASE WHEN status = 'offline' THEN 'idle'" in call_args


# ============================================================================
# Edge Case Tests
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_robot_id_max_length(self) -> None:
        """Test robot_id at max length (64 chars)."""
        max_id = "x" * 64
        registration = RobotRegistration(
            robot_id=max_id,
            name="Test",
            hostname="host",
        )
        assert len(registration.robot_id) == 64

    def test_capabilities_empty_list(self) -> None:
        """Test registration with empty capabilities."""
        registration = RobotRegistration(
            robot_id="robot-1",
            name="Test",
            hostname="host",
            capabilities=[],
        )
        assert registration.capabilities == []

    def test_tags_empty_list(self) -> None:
        """Test registration with empty tags."""
        registration = RobotRegistration(
            robot_id="robot-1",
            name="Test",
            hostname="host",
            tags=[],
        )
        assert registration.tags == []

    def test_max_concurrent_jobs_boundary_values(self) -> None:
        """Test max_concurrent_jobs at boundaries (1 and 100)."""
        reg_min = RobotRegistration(
            robot_id="robot-1",
            name="Test",
            hostname="host",
            max_concurrent_jobs=1,
        )
        reg_max = RobotRegistration(
            robot_id="robot-2",
            name="Test",
            hostname="host",
            max_concurrent_jobs=100,
        )
        assert reg_min.max_concurrent_jobs == 1
        assert reg_max.max_concurrent_jobs == 100

    def test_update_with_empty_body(
        self,
        client: TestClient,
        mock_db_pool,
    ) -> None:
        """Test update with empty JSON body."""
        pool, conn = mock_db_pool
        conn.fetchrow.side_effect = [
            {"robot_id": TEST_ROBOT_ID},
            create_sample_robot_row(),
        ]

        set_db_pool(pool)

        response = client.put(
            f"/robots/{TEST_ROBOT_ID}",
            json={},
        )

        # Should still execute (with just updated_at)
        assert response.status_code == 200
        assert response.json()["robot_id"] == TEST_ROBOT_ID

    def test_registration_with_special_characters(
        self,
        client: TestClient,
        mock_db_pool,
    ) -> None:
        """Test registration with special characters in name."""
        pool, conn = mock_db_pool
        robot_row = create_sample_robot_row(name="Robot with 'quotes' & <symbols>")
        conn.fetchrow.return_value = robot_row

        set_db_pool(pool)

        response = client.post(
            "/robots/register",
            json={
                "robot_id": "robot-special",
                "name": "Robot with 'quotes' & <symbols>",
                "hostname": "test-host",
            },
        )

        assert response.status_code == 200

    def test_list_robots_both_filters(
        self,
        client: TestClient,
        mock_db_pool,
    ) -> None:
        """Test listing with both status and environment filters."""
        pool, conn = mock_db_pool
        conn.fetchval.return_value = 1
        conn.fetch.return_value = [
            create_sample_robot_row(status="idle", environment="production")
        ]

        set_db_pool(pool)

        response = client.get("/robots?status=idle&environment=production")

        assert response.status_code == 200
        call_args = conn.fetch.call_args[0][0]
        assert "status = $" in call_args
        assert "environment = $" in call_args
