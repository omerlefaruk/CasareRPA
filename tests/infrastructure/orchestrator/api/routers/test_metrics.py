"""
Tests for metrics REST API router.

Tests cover:
- Fleet metrics endpoint (GET /metrics/fleet)
- Robots list endpoint (GET /metrics/robots)
- Robot details endpoint (GET /metrics/robots/{robot_id})
- Jobs history endpoint (GET /metrics/jobs)
- Job details endpoint (GET /metrics/jobs/{job_id})
- Analytics endpoint (GET /metrics/analytics)
- Activity feed endpoint (GET /metrics/activity)
- Metrics snapshot endpoint (GET /metrics/snapshot)
- Prometheus metrics endpoint (GET /metrics/prometheus)
- WebSocket connection tracking

Test Patterns:
- SUCCESS: 200 responses with valid payloads
- ERROR: 404, 500 responses
- EDGE CASES: filtering, pagination, invalid parameters
"""

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from casare_rpa.infrastructure.orchestrator.api.routers.metrics import (
    router,
    get_websocket_connection_count,
    _metrics_ws_connections,
)
from casare_rpa.infrastructure.orchestrator.api.dependencies import (
    get_metrics_collector,
)
from casare_rpa.infrastructure.orchestrator.api.models import (
    FleetMetrics,
    RobotSummary,
    RobotMetrics,
    JobSummary,
    JobDetails,
    AnalyticsSummary,
    ActivityEvent,
    ActivityResponse,
)


# ============================================================================
# Test Constants
# ============================================================================

TEST_ROBOT_ID = "robot-001"
TEST_ROBOT_ID_2 = "robot-002"
TEST_JOB_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
TEST_WORKFLOW_ID = "12345678-1234-5678-1234-567812345678"


# ============================================================================
# Sample Response Data
# ============================================================================


def sample_fleet_metrics() -> Dict[str, Any]:
    """Sample fleet metrics data."""
    return {
        "total_robots": 5,
        "active_robots": 2,
        "idle_robots": 2,
        "offline_robots": 1,
        "total_jobs_today": 150,
        "active_jobs": 3,
        "queue_depth": 12,
        "average_job_duration_seconds": 45.5,
    }


def sample_robot_summary(robot_id: str = TEST_ROBOT_ID) -> Dict[str, Any]:
    """Sample robot summary data."""
    return {
        "robot_id": robot_id,
        "hostname": f"host-{robot_id}",
        "status": "idle",
        "cpu_percent": 25.5,
        "memory_mb": 1024.0,
        "current_job_id": None,
        "last_heartbeat": datetime.now(timezone.utc).isoformat(),
    }


def sample_robot_metrics(robot_id: str = TEST_ROBOT_ID) -> Dict[str, Any]:
    """Sample detailed robot metrics data."""
    return {
        "robot_id": robot_id,
        "hostname": f"host-{robot_id}",
        "status": "busy",
        "cpu_percent": 65.0,
        "memory_mb": 2048.0,
        "memory_percent": 50.0,
        "current_job_id": TEST_JOB_ID,
        "last_heartbeat": datetime.now(timezone.utc).isoformat(),
        "jobs_completed_today": 25,
        "jobs_failed_today": 2,
        "average_job_duration_seconds": 38.7,
    }


def sample_job_summary(job_id: str = TEST_JOB_ID) -> Dict[str, Any]:
    """Sample job summary data."""
    return {
        "job_id": job_id,
        "workflow_id": TEST_WORKFLOW_ID,
        "workflow_name": "Test Workflow",
        "robot_id": TEST_ROBOT_ID,
        "status": "completed",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "duration_ms": 5000,
    }


def sample_job_details(job_id: str = TEST_JOB_ID) -> Dict[str, Any]:
    """Sample detailed job data."""
    return {
        "job_id": job_id,
        "workflow_id": TEST_WORKFLOW_ID,
        "workflow_name": "Test Workflow",
        "robot_id": TEST_ROBOT_ID,
        "status": "completed",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "claimed_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "duration_ms": 5000,
        "error_message": None,
        "error_type": None,
        "retry_count": 0,
        "node_executions": [
            {"node_id": "node1", "status": "completed", "duration_ms": 1000},
            {"node_id": "node2", "status": "completed", "duration_ms": 2000},
        ],
    }


def sample_analytics() -> Dict[str, Any]:
    """Sample analytics data."""
    return {
        "total_jobs": 1500,
        "success_rate": 95.5,
        "failure_rate": 4.5,
        "average_duration_ms": 4500.0,
        "p50_duration_ms": 3200.0,
        "p90_duration_ms": 8500.0,
        "p99_duration_ms": 15000.0,
        "slowest_workflows": [
            {
                "workflow_id": "wf-001",
                "workflow_name": "Data Migration",
                "average_duration_ms": 25000.0,
            },
            {
                "workflow_id": "wf-002",
                "workflow_name": "Report Generation",
                "average_duration_ms": 18000.0,
            },
        ],
        "error_distribution": [
            {"error_type": "timeout", "count": 35},
            {"error_type": "selector_not_found", "count": 22},
        ],
        "self_healing_success_rate": 85.0,
    }


def sample_activity_event(event_id: str = "evt-001") -> Dict[str, Any]:
    """Sample activity event data."""
    return {
        "id": event_id,
        "type": "job_completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "title": "Job completed successfully",
        "details": "Workflow 'Test Workflow' finished in 5.0s",
        "robot_id": TEST_ROBOT_ID,
        "job_id": TEST_JOB_ID,
    }


# ============================================================================
# Mock Collector Factory
# ============================================================================


def create_mock_collector() -> MagicMock:
    """Create a fresh mock metrics collector."""
    collector = MagicMock()
    collector.get_fleet_summary_async = AsyncMock(return_value=sample_fleet_metrics())
    collector.get_robot_list_async = AsyncMock(
        return_value=[sample_robot_summary(TEST_ROBOT_ID)]
    )
    collector.get_robot_details = MagicMock(
        return_value=sample_robot_metrics(TEST_ROBOT_ID)
    )
    collector.get_job_history = AsyncMock(
        return_value=[sample_job_summary(TEST_JOB_ID)]
    )
    collector.get_job_details_async = AsyncMock(
        return_value=sample_job_details(TEST_JOB_ID)
    )
    collector.get_analytics_async = AsyncMock(return_value=sample_analytics())
    collector.get_activity_events_async = AsyncMock(
        return_value={"events": [sample_activity_event()], "total": 1}
    )
    return collector


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_collector() -> MagicMock:
    """Create mock metrics collector."""
    return create_mock_collector()


@pytest.fixture
def app(mock_collector: MagicMock) -> FastAPI:
    """Create FastAPI app with mocked dependencies."""
    app = FastAPI()
    app.include_router(router)
    app.state.db_pool = MagicMock()

    # Override dependency
    app.dependency_overrides[get_metrics_collector] = lambda: mock_collector

    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create FastAPI test client."""
    return TestClient(app)


# ============================================================================
# Fleet Metrics Endpoint Tests
# ============================================================================


class TestFleetMetricsEndpoint:
    """Tests for GET /metrics/fleet endpoint."""

    def test_get_fleet_metrics_success(self, mock_collector: MagicMock) -> None:
        """Test successful fleet metrics retrieval."""
        app = FastAPI()
        app.include_router(router)
        app.state.db_pool = MagicMock()
        app.dependency_overrides[get_metrics_collector] = lambda: mock_collector

        client = TestClient(app)
        response = client.get("/metrics/fleet")

        assert response.status_code == 200
        data = response.json()
        assert data["total_robots"] == 5
        assert data["active_robots"] == 2
        assert data["idle_robots"] == 2
        assert data["offline_robots"] == 1
        assert data["total_jobs_today"] == 150
        assert data["active_jobs"] == 3
        assert data["queue_depth"] == 12
        assert data["average_job_duration_seconds"] == 45.5

    def test_get_fleet_metrics_error(self, mock_collector: MagicMock) -> None:
        """Test fleet metrics error handling."""
        mock_collector.get_fleet_summary_async.side_effect = Exception("Database error")

        app = FastAPI()
        app.include_router(router)
        app.state.db_pool = MagicMock()
        app.dependency_overrides[get_metrics_collector] = lambda: mock_collector

        client = TestClient(app)
        response = client.get("/metrics/fleet")

        assert response.status_code == 500
        assert "failed to fetch" in response.json()["detail"].lower()


# ============================================================================
# Robots List Endpoint Tests
# ============================================================================


class TestRobotsListEndpoint:
    """Tests for GET /metrics/robots endpoint."""

    def test_get_robots_success(self, mock_collector: MagicMock) -> None:
        """Test successful robots list retrieval."""
        app = FastAPI()
        app.include_router(router)
        app.state.db_pool = MagicMock()
        app.dependency_overrides[get_metrics_collector] = lambda: mock_collector

        client = TestClient(app)
        response = client.get("/metrics/robots")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["robot_id"] == TEST_ROBOT_ID

    def test_get_robots_with_status_filter(self, mock_collector: MagicMock) -> None:
        """Test robots list with status filter."""
        app = FastAPI()
        app.include_router(router)
        app.state.db_pool = MagicMock()
        app.dependency_overrides[get_metrics_collector] = lambda: mock_collector

        client = TestClient(app)
        response = client.get("/metrics/robots?status=idle")

        assert response.status_code == 200
        mock_collector.get_robot_list_async.assert_called()

    def test_get_robots_with_busy_filter(self, mock_collector: MagicMock) -> None:
        """Test robots list with busy status filter."""
        mock_collector.get_robot_list_async.return_value = [
            {
                **sample_robot_summary(TEST_ROBOT_ID),
                "status": "busy",
                "current_job_id": TEST_JOB_ID,
            }
        ]

        app = FastAPI()
        app.include_router(router)
        app.state.db_pool = MagicMock()
        app.dependency_overrides[get_metrics_collector] = lambda: mock_collector

        client = TestClient(app)
        response = client.get("/metrics/robots?status=busy")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "busy"

    def test_get_robots_empty_list(self, mock_collector: MagicMock) -> None:
        """Test robots list when no robots registered."""
        mock_collector.get_robot_list_async.return_value = []

        app = FastAPI()
        app.include_router(router)
        app.state.db_pool = MagicMock()
        app.dependency_overrides[get_metrics_collector] = lambda: mock_collector

        client = TestClient(app)
        response = client.get("/metrics/robots?status=offline")

        assert response.status_code == 200
        assert response.json() == []

    def test_get_robots_error(self, mock_collector: MagicMock) -> None:
        """Test robots list error handling."""
        mock_collector.get_robot_list_async.side_effect = Exception("Database error")

        app = FastAPI()
        app.include_router(router)
        app.state.db_pool = MagicMock()
        app.dependency_overrides[get_metrics_collector] = lambda: mock_collector

        client = TestClient(app)
        response = client.get("/metrics/robots")

        assert response.status_code == 500


# ============================================================================
# Robot Details Endpoint Tests
# ============================================================================


class TestRobotDetailsEndpoint:
    """Tests for GET /metrics/robots/{robot_id} endpoint."""

    def test_get_robot_details_success(self, mock_collector: MagicMock) -> None:
        """Test successful robot details retrieval."""
        app = FastAPI()
        app.include_router(router)
        app.state.db_pool = MagicMock()
        app.dependency_overrides[get_metrics_collector] = lambda: mock_collector

        client = TestClient(app)
        response = client.get(f"/metrics/robots/{TEST_ROBOT_ID}")

        assert response.status_code == 200
        data = response.json()
        assert data["robot_id"] == TEST_ROBOT_ID
        assert data["hostname"] == f"host-{TEST_ROBOT_ID}"
        assert data["jobs_completed_today"] == 25
        assert data["jobs_failed_today"] == 2

    def test_get_robot_details_not_found(self, mock_collector: MagicMock) -> None:
        """Test robot details for non-existent robot."""
        mock_collector.get_robot_details.return_value = None

        app = FastAPI()
        app.include_router(router)
        app.state.db_pool = MagicMock()
        app.dependency_overrides[get_metrics_collector] = lambda: mock_collector

        client = TestClient(app)
        response = client.get("/metrics/robots/nonexistent-robot")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_robot_details_invalid_id_pattern(self) -> None:
        """Test robot details with invalid ID pattern."""
        app = FastAPI()
        app.include_router(router)

        client = TestClient(app)
        # ID with special characters (should fail pattern validation)
        response = client.get("/metrics/robots/robot$$$invalid")

        assert response.status_code == 422  # Validation error

    def test_get_robot_details_error(self, mock_collector: MagicMock) -> None:
        """Test robot details error handling."""
        mock_collector.get_robot_details.side_effect = Exception("Database error")

        app = FastAPI()
        app.include_router(router)
        app.state.db_pool = MagicMock()
        app.dependency_overrides[get_metrics_collector] = lambda: mock_collector

        client = TestClient(app)
        response = client.get(f"/metrics/robots/{TEST_ROBOT_ID}")

        assert response.status_code == 500


# ============================================================================
# Jobs History Endpoint Tests
# ============================================================================


class TestJobsHistoryEndpoint:
    """Tests for GET /metrics/jobs endpoint."""

    def test_get_jobs_success(self, mock_collector: MagicMock) -> None:
        """Test successful jobs list retrieval."""
        app = FastAPI()
        app.include_router(router)
        app.state.db_pool = MagicMock()
        app.dependency_overrides[get_metrics_collector] = lambda: mock_collector

        client = TestClient(app)
        response = client.get("/metrics/jobs")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["job_id"] == TEST_JOB_ID

    def test_get_jobs_with_limit(self, mock_collector: MagicMock) -> None:
        """Test jobs list with limit parameter."""
        app = FastAPI()
        app.include_router(router)
        app.state.db_pool = MagicMock()
        app.dependency_overrides[get_metrics_collector] = lambda: mock_collector

        client = TestClient(app)
        response = client.get("/metrics/jobs?limit=10")

        assert response.status_code == 200

    def test_get_jobs_with_status_filter(self, mock_collector: MagicMock) -> None:
        """Test jobs list with status filter."""
        app = FastAPI()
        app.include_router(router)
        app.state.db_pool = MagicMock()
        app.dependency_overrides[get_metrics_collector] = lambda: mock_collector

        client = TestClient(app)
        response = client.get("/metrics/jobs?status=completed")

        assert response.status_code == 200

    def test_get_jobs_with_workflow_filter(self, mock_collector: MagicMock) -> None:
        """Test jobs list with workflow_id filter."""
        app = FastAPI()
        app.include_router(router)
        app.state.db_pool = MagicMock()
        app.dependency_overrides[get_metrics_collector] = lambda: mock_collector

        client = TestClient(app)
        response = client.get(f"/metrics/jobs?workflow_id={TEST_WORKFLOW_ID}")

        assert response.status_code == 200

    def test_get_jobs_with_robot_filter(self, mock_collector: MagicMock) -> None:
        """Test jobs list with robot_id filter."""
        app = FastAPI()
        app.include_router(router)
        app.state.db_pool = MagicMock()
        app.dependency_overrides[get_metrics_collector] = lambda: mock_collector

        client = TestClient(app)
        response = client.get(f"/metrics/jobs?robot_id={TEST_ROBOT_ID}")

        assert response.status_code == 200

    def test_get_jobs_with_all_filters(self, mock_collector: MagicMock) -> None:
        """Test jobs list with all filters combined."""
        app = FastAPI()
        app.include_router(router)
        app.state.db_pool = MagicMock()
        app.dependency_overrides[get_metrics_collector] = lambda: mock_collector

        client = TestClient(app)
        response = client.get(
            f"/metrics/jobs?limit=25&status=failed&workflow_id={TEST_WORKFLOW_ID}&robot_id={TEST_ROBOT_ID}"
        )

        assert response.status_code == 200

    def test_get_jobs_limit_boundary_min(self) -> None:
        """Test jobs list with minimum limit value."""
        app = FastAPI()
        app.include_router(router)
        app.state.db_pool = MagicMock()
        mock_coll = create_mock_collector()
        app.dependency_overrides[get_metrics_collector] = lambda: mock_coll

        client = TestClient(app)
        response = client.get("/metrics/jobs?limit=1")
        assert response.status_code == 200

    def test_get_jobs_limit_boundary_max(self) -> None:
        """Test jobs list with maximum limit value."""
        app = FastAPI()
        app.include_router(router)
        app.state.db_pool = MagicMock()
        mock_coll = create_mock_collector()
        app.dependency_overrides[get_metrics_collector] = lambda: mock_coll

        client = TestClient(app)
        response = client.get("/metrics/jobs?limit=500")
        assert response.status_code == 200

    def test_get_jobs_limit_below_min(self) -> None:
        """Test jobs list with limit below minimum."""
        app = FastAPI()
        app.include_router(router)

        client = TestClient(app)
        response = client.get("/metrics/jobs?limit=0")
        assert response.status_code == 422

    def test_get_jobs_limit_above_max(self) -> None:
        """Test jobs list with limit above maximum."""
        app = FastAPI()
        app.include_router(router)

        client = TestClient(app)
        response = client.get("/metrics/jobs?limit=501")
        assert response.status_code == 422

    def test_get_jobs_error(self, mock_collector: MagicMock) -> None:
        """Test jobs list error handling."""
        mock_collector.get_job_history.side_effect = Exception("Database error")

        app = FastAPI()
        app.include_router(router)
        app.state.db_pool = MagicMock()
        app.dependency_overrides[get_metrics_collector] = lambda: mock_collector

        client = TestClient(app)
        response = client.get("/metrics/jobs")

        assert response.status_code == 500


# ============================================================================
# Job Details Endpoint Tests
# ============================================================================


class TestJobDetailsEndpoint:
    """Tests for GET /metrics/jobs/{job_id} endpoint."""

    def test_get_job_details_success(self, mock_collector: MagicMock) -> None:
        """Test successful job details retrieval."""
        app = FastAPI()
        app.include_router(router)
        app.state.db_pool = MagicMock()
        app.dependency_overrides[get_metrics_collector] = lambda: mock_collector

        client = TestClient(app)
        response = client.get(f"/metrics/jobs/{TEST_JOB_ID}")

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == TEST_JOB_ID
        assert data["workflow_id"] == TEST_WORKFLOW_ID
        assert data["status"] == "completed"
        assert len(data["node_executions"]) == 2

    def test_get_job_details_not_found(self, mock_collector: MagicMock) -> None:
        """Test job details for non-existent job."""
        mock_collector.get_job_details_async.return_value = None

        app = FastAPI()
        app.include_router(router)
        app.state.db_pool = MagicMock()
        app.dependency_overrides[get_metrics_collector] = lambda: mock_collector

        client = TestClient(app)
        response = client.get("/metrics/jobs/nonexistent-job-id")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_job_details_with_error_info(self, mock_collector: MagicMock) -> None:
        """Test job details with error information."""
        failed_job = sample_job_details(TEST_JOB_ID)
        failed_job["status"] = "failed"
        failed_job["error_message"] = "Element not found: #submit-btn"
        failed_job["error_type"] = "selector_not_found"
        failed_job["retry_count"] = 2
        mock_collector.get_job_details_async.return_value = failed_job

        app = FastAPI()
        app.include_router(router)
        app.state.db_pool = MagicMock()
        app.dependency_overrides[get_metrics_collector] = lambda: mock_collector

        client = TestClient(app)
        response = client.get(f"/metrics/jobs/{TEST_JOB_ID}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert data["error_message"] == "Element not found: #submit-btn"
        assert data["error_type"] == "selector_not_found"
        assert data["retry_count"] == 2

    def test_get_job_details_error(self, mock_collector: MagicMock) -> None:
        """Test job details error handling."""
        mock_collector.get_job_details_async.side_effect = Exception("Database error")

        app = FastAPI()
        app.include_router(router)
        app.state.db_pool = MagicMock()
        app.dependency_overrides[get_metrics_collector] = lambda: mock_collector

        client = TestClient(app)
        response = client.get(f"/metrics/jobs/{TEST_JOB_ID}")

        assert response.status_code == 500


# ============================================================================
# Analytics Endpoint Tests
# ============================================================================


class TestAnalyticsEndpoint:
    """Tests for GET /metrics/analytics endpoint."""

    def test_get_analytics_success(self, mock_collector: MagicMock) -> None:
        """Test successful analytics retrieval."""
        app = FastAPI()
        app.include_router(router)
        app.state.db_pool = MagicMock()
        app.dependency_overrides[get_metrics_collector] = lambda: mock_collector

        client = TestClient(app)
        response = client.get("/metrics/analytics")

        assert response.status_code == 200
        data = response.json()
        assert data["total_jobs"] == 1500
        assert data["success_rate"] == 95.5
        assert data["failure_rate"] == 4.5
        assert data["p50_duration_ms"] == 3200.0
        assert data["p90_duration_ms"] == 8500.0
        assert data["p99_duration_ms"] == 15000.0
        assert len(data["slowest_workflows"]) == 2
        assert len(data["error_distribution"]) == 2
        assert data["self_healing_success_rate"] == 85.0

    def test_get_analytics_with_days_param(self, mock_collector: MagicMock) -> None:
        """Test analytics with custom days parameter."""
        app = FastAPI()
        app.include_router(router)
        app.state.db_pool = MagicMock()
        app.dependency_overrides[get_metrics_collector] = lambda: mock_collector

        client = TestClient(app)
        response = client.get("/metrics/analytics?days=30")

        assert response.status_code == 200

    def test_get_analytics_days_boundary_min(self) -> None:
        """Test analytics with minimum days value."""
        app = FastAPI()
        app.include_router(router)
        app.state.db_pool = MagicMock()
        mock_coll = create_mock_collector()
        app.dependency_overrides[get_metrics_collector] = lambda: mock_coll

        client = TestClient(app)
        response = client.get("/metrics/analytics?days=1")
        assert response.status_code == 200

    def test_get_analytics_days_boundary_max(self) -> None:
        """Test analytics with maximum days value."""
        app = FastAPI()
        app.include_router(router)
        app.state.db_pool = MagicMock()
        mock_coll = create_mock_collector()
        app.dependency_overrides[get_metrics_collector] = lambda: mock_coll

        client = TestClient(app)
        response = client.get("/metrics/analytics?days=90")
        assert response.status_code == 200

    def test_get_analytics_days_below_min(self) -> None:
        """Test analytics with days below minimum."""
        app = FastAPI()
        app.include_router(router)

        client = TestClient(app)
        response = client.get("/metrics/analytics?days=0")
        assert response.status_code == 422

    def test_get_analytics_days_above_max(self) -> None:
        """Test analytics with days above maximum."""
        app = FastAPI()
        app.include_router(router)

        client = TestClient(app)
        response = client.get("/metrics/analytics?days=91")
        assert response.status_code == 422

    def test_get_analytics_error(self, mock_collector: MagicMock) -> None:
        """Test analytics error handling."""
        mock_collector.get_analytics_async.side_effect = Exception("Database error")

        app = FastAPI()
        app.include_router(router)
        app.state.db_pool = MagicMock()
        app.dependency_overrides[get_metrics_collector] = lambda: mock_collector

        client = TestClient(app)
        response = client.get("/metrics/analytics")

        assert response.status_code == 500


# ============================================================================
# Activity Feed Endpoint Tests
# ============================================================================


class TestActivityEndpoint:
    """Tests for GET /metrics/activity endpoint."""

    def test_get_activity_success(self, mock_collector: MagicMock) -> None:
        """Test successful activity feed retrieval."""
        app = FastAPI()
        app.include_router(router)
        app.state.db_pool = MagicMock()
        app.dependency_overrides[get_metrics_collector] = lambda: mock_collector

        client = TestClient(app)
        response = client.get("/metrics/activity")

        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        assert "total" in data
        assert len(data["events"]) == 1
        assert data["events"][0]["type"] == "job_completed"

    def test_get_activity_with_limit(self, mock_collector: MagicMock) -> None:
        """Test activity feed with limit parameter."""
        app = FastAPI()
        app.include_router(router)
        app.state.db_pool = MagicMock()
        app.dependency_overrides[get_metrics_collector] = lambda: mock_collector

        client = TestClient(app)
        response = client.get("/metrics/activity?limit=100")

        assert response.status_code == 200

    def test_get_activity_with_event_type(self, mock_collector: MagicMock) -> None:
        """Test activity feed with event type filter."""
        app = FastAPI()
        app.include_router(router)
        app.state.db_pool = MagicMock()
        app.dependency_overrides[get_metrics_collector] = lambda: mock_collector

        client = TestClient(app)
        response = client.get("/metrics/activity?event_type=job_started")

        assert response.status_code == 200

    def test_get_activity_limit_boundaries(self) -> None:
        """Test activity feed limit boundaries."""
        app = FastAPI()
        app.include_router(router)
        app.state.db_pool = MagicMock()
        mock_coll = create_mock_collector()
        app.dependency_overrides[get_metrics_collector] = lambda: mock_coll

        client = TestClient(app)

        # Minimum
        response = client.get("/metrics/activity?limit=1")
        assert response.status_code == 200

        # Maximum
        response = client.get("/metrics/activity?limit=200")
        assert response.status_code == 200

    def test_get_activity_limit_below_min(self) -> None:
        """Test activity feed limit below minimum."""
        app = FastAPI()
        app.include_router(router)

        client = TestClient(app)
        response = client.get("/metrics/activity?limit=0")
        assert response.status_code == 422

    def test_get_activity_limit_above_max(self) -> None:
        """Test activity feed limit above maximum."""
        app = FastAPI()
        app.include_router(router)

        client = TestClient(app)
        response = client.get("/metrics/activity?limit=201")
        assert response.status_code == 422

    def test_get_activity_error(self, mock_collector: MagicMock) -> None:
        """Test activity feed error handling."""
        mock_collector.get_activity_events_async.side_effect = Exception(
            "Database error"
        )

        app = FastAPI()
        app.include_router(router)
        app.state.db_pool = MagicMock()
        app.dependency_overrides[get_metrics_collector] = lambda: mock_collector

        client = TestClient(app)
        response = client.get("/metrics/activity")

        assert response.status_code == 500


# ============================================================================
# Metrics Snapshot Endpoint Tests
# ============================================================================


class TestMetricsSnapshotEndpoint:
    """Tests for GET /metrics/snapshot endpoint."""

    def test_get_snapshot_success(self) -> None:
        """Test successful metrics snapshot retrieval."""
        app = FastAPI()
        app.include_router(router)

        mock_collector = MagicMock()
        mock_snapshot = MagicMock()
        mock_snapshot.to_dict.return_value = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "counters": {},
            "gauges": {},
        }

        with (
            patch(
                "casare_rpa.infrastructure.orchestrator.api.routers.metrics.get_rpa_metrics_collector",
                return_value=mock_collector,
            ),
            patch(
                "casare_rpa.infrastructure.orchestrator.api.routers.metrics.MetricsSnapshot.from_collector",
                return_value=mock_snapshot,
            ),
        ):
            client = TestClient(app)
            response = client.get("/metrics/snapshot")

        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data

    def test_get_snapshot_with_environment(self) -> None:
        """Test metrics snapshot with environment parameter."""
        app = FastAPI()
        app.include_router(router)

        mock_collector = MagicMock()
        mock_snapshot = MagicMock()
        mock_snapshot.to_dict.return_value = {"timestamp": "2024-01-01T00:00:00Z"}

        with (
            patch(
                "casare_rpa.infrastructure.orchestrator.api.routers.metrics.get_rpa_metrics_collector",
                return_value=mock_collector,
            ),
            patch(
                "casare_rpa.infrastructure.orchestrator.api.routers.metrics.MetricsSnapshot.from_collector",
                return_value=mock_snapshot,
            ),
        ):
            client = TestClient(app)
            response = client.get("/metrics/snapshot?environment=production")

        assert response.status_code == 200

    def test_get_snapshot_error(self) -> None:
        """Test metrics snapshot error handling."""
        app = FastAPI()
        app.include_router(router)

        with patch(
            "casare_rpa.infrastructure.orchestrator.api.routers.metrics.get_rpa_metrics_collector",
            side_effect=Exception("Metrics collector error"),
        ):
            client = TestClient(app)
            response = client.get("/metrics/snapshot")

        assert response.status_code == 500


# ============================================================================
# Prometheus Metrics Endpoint Tests
# ============================================================================


class TestPrometheusEndpoint:
    """Tests for GET /metrics/prometheus endpoint."""

    def test_get_prometheus_success(self) -> None:
        """Test successful Prometheus metrics retrieval."""
        app = FastAPI()
        app.include_router(router)

        mock_exporter = MagicMock()
        mock_exporter.get_prometheus_format.return_value = (
            "# HELP casare_jobs_total Total jobs\n"
            "# TYPE casare_jobs_total counter\n"
            "casare_jobs_total 100\n"
        )

        with patch(
            "casare_rpa.infrastructure.orchestrator.api.routers.metrics.get_metrics_exporter",
            return_value=mock_exporter,
        ):
            client = TestClient(app)
            response = client.get("/metrics/prometheus")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        assert "casare_jobs_total" in response.text

    def test_get_prometheus_with_environment(self) -> None:
        """Test Prometheus metrics with environment parameter."""
        app = FastAPI()
        app.include_router(router)

        mock_exporter = MagicMock()
        mock_exporter.get_prometheus_format.return_value = "# Empty metrics\n"

        with patch(
            "casare_rpa.infrastructure.orchestrator.api.routers.metrics.get_metrics_exporter",
            return_value=mock_exporter,
        ) as mock_get:
            client = TestClient(app)
            response = client.get("/metrics/prometheus?environment=staging")

        assert response.status_code == 200
        mock_get.assert_called_once_with(environment="staging")

    def test_get_prometheus_error(self) -> None:
        """Test Prometheus metrics error handling."""
        app = FastAPI()
        app.include_router(router)

        with patch(
            "casare_rpa.infrastructure.orchestrator.api.routers.metrics.get_metrics_exporter",
            side_effect=Exception("Exporter error"),
        ):
            client = TestClient(app)
            response = client.get("/metrics/prometheus")

        assert response.status_code == 500


# ============================================================================
# WebSocket Connection Tracking Tests
# ============================================================================


class TestWebSocketConnectionTracking:
    """Tests for WebSocket connection tracking."""

    def test_get_websocket_connection_count_empty(self) -> None:
        """Test connection count when no connections."""
        _metrics_ws_connections.clear()
        assert get_websocket_connection_count() == 0

    def test_get_websocket_connection_count_with_connections(self) -> None:
        """Test connection count with active connections."""
        _metrics_ws_connections.clear()

        # Add mock connections
        mock_ws1 = MagicMock()
        mock_ws2 = MagicMock()
        _metrics_ws_connections.add(mock_ws1)
        _metrics_ws_connections.add(mock_ws2)

        assert get_websocket_connection_count() == 2

        # Cleanup
        _metrics_ws_connections.clear()


# ============================================================================
# Edge Case Tests
# ============================================================================


class TestEdgeCases:
    """Edge case and boundary condition tests."""

    def test_fleet_metrics_all_zeros(self) -> None:
        """Test fleet metrics with all zero values."""
        mock_collector = create_mock_collector()
        mock_collector.get_fleet_summary_async.return_value = {
            "total_robots": 0,
            "active_robots": 0,
            "idle_robots": 0,
            "offline_robots": 0,
            "total_jobs_today": 0,
            "active_jobs": 0,
            "queue_depth": 0,
            "average_job_duration_seconds": 0.0,
        }

        app = FastAPI()
        app.include_router(router)
        app.state.db_pool = MagicMock()
        app.dependency_overrides[get_metrics_collector] = lambda: mock_collector

        client = TestClient(app)
        response = client.get("/metrics/fleet")

        assert response.status_code == 200
        data = response.json()
        assert data["total_robots"] == 0

    def test_robots_list_empty(self) -> None:
        """Test robots list when no robots registered."""
        mock_collector = create_mock_collector()
        mock_collector.get_robot_list_async.return_value = []

        app = FastAPI()
        app.include_router(router)
        app.state.db_pool = MagicMock()
        app.dependency_overrides[get_metrics_collector] = lambda: mock_collector

        client = TestClient(app)
        response = client.get("/metrics/robots")

        assert response.status_code == 200
        assert response.json() == []

    def test_jobs_list_empty(self) -> None:
        """Test jobs list when no jobs exist."""
        mock_collector = create_mock_collector()
        mock_collector.get_job_history.return_value = []

        app = FastAPI()
        app.include_router(router)
        app.state.db_pool = MagicMock()
        app.dependency_overrides[get_metrics_collector] = lambda: mock_collector

        client = TestClient(app)
        response = client.get("/metrics/jobs")

        assert response.status_code == 200
        assert response.json() == []

    def test_activity_feed_empty(self) -> None:
        """Test activity feed when no events exist."""
        mock_collector = create_mock_collector()
        mock_collector.get_activity_events_async.return_value = {
            "events": [],
            "total": 0,
        }

        app = FastAPI()
        app.include_router(router)
        app.state.db_pool = MagicMock()
        app.dependency_overrides[get_metrics_collector] = lambda: mock_collector

        client = TestClient(app)
        response = client.get("/metrics/activity")

        assert response.status_code == 200
        data = response.json()
        assert data["events"] == []
        assert data["total"] == 0

    def test_robot_id_with_hyphens(self) -> None:
        """Test robot ID with hyphens (valid pattern)."""
        robot_id = "robot-with-hyphens-123"
        mock_collector = create_mock_collector()
        mock_collector.get_robot_details.return_value = sample_robot_metrics(robot_id)

        app = FastAPI()
        app.include_router(router)
        app.state.db_pool = MagicMock()
        app.dependency_overrides[get_metrics_collector] = lambda: mock_collector

        client = TestClient(app)
        response = client.get(f"/metrics/robots/{robot_id}")

        assert response.status_code == 200
        assert response.json()["robot_id"] == robot_id

    def test_robot_id_with_underscores(self) -> None:
        """Test robot ID with underscores (valid pattern)."""
        robot_id = "robot_with_underscores_123"
        mock_collector = create_mock_collector()
        mock_collector.get_robot_details.return_value = sample_robot_metrics(robot_id)

        app = FastAPI()
        app.include_router(router)
        app.state.db_pool = MagicMock()
        app.dependency_overrides[get_metrics_collector] = lambda: mock_collector

        client = TestClient(app)
        response = client.get(f"/metrics/robots/{robot_id}")

        assert response.status_code == 200
        assert response.json()["robot_id"] == robot_id
