"""
Tests for REST API metrics endpoints.

Tests the /api/v1/metrics/* endpoints with mocked metrics collector.
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from casare_rpa.orchestrator.api.main import app


@pytest.fixture
def mock_collector():
    """Create mock metrics collector."""
    collector = Mock()

    # Mock fleet summary
    collector.get_fleet_summary.return_value = {
        "total_robots": 5,
        "active_robots": 2,
        "idle_robots": 2,
        "offline_robots": 1,
        "active_jobs": 3,
        "queue_depth": 10,
    }

    # Mock robot list
    collector.get_robot_list.return_value = [
        {
            "robot_id": "robot-001",
            "hostname": "robot-01.local",
            "status": "busy",
            "cpu_percent": 45.2,
            "memory_mb": 1024.5,
            "current_job_id": "job-123",
            "last_heartbeat": datetime(2025, 11, 29, 10, 30, 0),
        },
        {
            "robot_id": "robot-002",
            "hostname": "robot-02.local",
            "status": "idle",
            "cpu_percent": 12.5,
            "memory_mb": 512.0,
            "current_job_id": None,
            "last_heartbeat": datetime(2025, 11, 29, 10, 29, 0),
        },
    ]

    # Mock robot details
    collector.get_robot_details.return_value = {
        "robot_id": "robot-001",
        "hostname": "robot-01.local",
        "status": "busy",
        "cpu_percent": 45.2,
        "memory_mb": 1024.5,
        "memory_percent": 68.3,
        "current_job_id": "job-123",
        "last_heartbeat": datetime(2025, 11, 29, 10, 30, 0),
        "jobs_completed_today": 15,
        "jobs_failed_today": 2,
        "average_job_duration_seconds": 120.5,
    }

    # Mock job history
    collector.get_job_history.return_value = [
        {
            "job_id": "job-123",
            "workflow_id": "workflow-001",
            "workflow_name": "Data Extraction",
            "robot_id": "robot-001",
            "status": "completed",
            "created_at": datetime(2025, 11, 29, 10, 0, 0),
            "completed_at": datetime(2025, 11, 29, 10, 2, 30),
            "duration_ms": 150000,
        },
    ]

    # Mock job details
    collector.get_job_details.return_value = {
        "job_id": "job-123",
        "workflow_id": "workflow-001",
        "workflow_name": "Data Extraction",
        "robot_id": "robot-001",
        "status": "completed",
        "created_at": datetime(2025, 11, 29, 10, 0, 0),
        "claimed_at": datetime(2025, 11, 29, 10, 0, 5),
        "completed_at": datetime(2025, 11, 29, 10, 2, 30),
        "duration_ms": 150000,
        "error_message": None,
        "error_type": None,
        "retry_count": 0,
        "node_executions": [],
    }

    # Mock analytics
    collector.get_analytics.return_value = {
        "total_jobs": 100,
        "success_rate": 95.0,
        "failure_rate": 5.0,
        "average_duration_ms": 120000.0,
        "p50_duration_ms": 100000.0,
        "p90_duration_ms": 200000.0,
        "p99_duration_ms": 300000.0,
        "slowest_workflows": [
            {
                "workflow_id": "workflow-001",
                "workflow_name": "Data Extraction",
                "average_duration_ms": 180000.0,
            }
        ],
        "error_distribution": [
            {"error_type": "TimeoutError", "count": 3},
            {"error_type": "NetworkError", "count": 2},
        ],
        "self_healing_success_rate": 80.0,
    }

    return collector


@pytest.fixture
def client(mock_collector):
    """Create test client with mocked dependencies."""
    from casare_rpa.orchestrator.api.dependencies import get_metrics_collector

    # Override dependency
    app.dependency_overrides[get_metrics_collector] = lambda: mock_collector

    yield TestClient(app)

    # Clean up
    app.dependency_overrides.clear()


class TestFleetMetrics:
    """Tests for /metrics/fleet endpoint."""

    def test_get_fleet_metrics_success(self, client):
        """Test successful fleet metrics retrieval."""
        response = client.get("/api/v1/metrics/fleet")

        assert response.status_code == 200
        data = response.json()
        assert data["total_robots"] == 5
        assert data["active_robots"] == 2
        assert data["idle_robots"] == 2
        assert data["offline_robots"] == 1
        assert data["active_jobs"] == 3
        assert data["queue_depth"] == 10

    def test_get_fleet_metrics_collector_error(self, client, mock_collector):
        """Test error handling when collector fails."""
        mock_collector.get_fleet_summary.side_effect = Exception("Database error")

        response = client.get("/api/v1/metrics/fleet")

        assert response.status_code == 500
        assert "Failed to fetch fleet metrics" in response.json()["detail"]


class TestRobotEndpoints:
    """Tests for /metrics/robots/* endpoints."""

    def test_get_robots_all(self, client):
        """Test getting all robots without filter."""
        response = client.get("/api/v1/metrics/robots")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["robot_id"] == "robot-001"
        assert data[0]["status"] == "busy"
        assert data[1]["robot_id"] == "robot-002"
        assert data[1]["status"] == "idle"

    def test_get_robots_filtered(self, client, mock_collector):
        """Test getting robots with status filter."""
        response = client.get("/api/v1/metrics/robots?status=busy")

        assert response.status_code == 200
        # Verify collector was called with filter
        mock_collector.get_robot_list.assert_called_with(status="busy")

    def test_get_robot_details_success(self, client):
        """Test getting detailed robot metrics."""
        response = client.get("/api/v1/metrics/robots/robot-001")

        assert response.status_code == 200
        data = response.json()
        assert data["robot_id"] == "robot-001"
        assert data["hostname"] == "robot-01.local"
        assert data["status"] == "busy"
        assert data["jobs_completed_today"] == 15
        assert data["jobs_failed_today"] == 2

    def test_get_robot_details_not_found(self, client, mock_collector):
        """Test 404 when robot not found."""
        mock_collector.get_robot_details.return_value = None

        response = client.get("/api/v1/metrics/robots/nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_get_robot_details_invalid_id(self, client):
        """Test validation of robot ID format."""
        # Test with invalid characters
        response = client.get("/api/v1/metrics/robots/robot@invalid!")

        assert response.status_code == 422  # Validation error

    def test_get_robot_details_id_too_long(self, client):
        """Test validation of robot ID length."""
        long_id = "a" * 100  # Exceeds 64 char limit
        response = client.get(f"/api/v1/metrics/robots/{long_id}")

        assert response.status_code == 422


class TestJobEndpoints:
    """Tests for /metrics/jobs/* endpoints."""

    def test_get_jobs_default(self, client):
        """Test getting jobs with default parameters."""
        response = client.get("/api/v1/metrics/jobs")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["job_id"] == "job-123"
        assert data[0]["status"] == "completed"

    def test_get_jobs_with_filters(self, client, mock_collector):
        """Test getting jobs with multiple filters."""
        response = client.get(
            "/api/v1/metrics/jobs?limit=10&status=completed&workflow_id=workflow-001&robot_id=robot-001"
        )

        assert response.status_code == 200
        # Verify collector was called with all filters
        mock_collector.get_job_history.assert_called_with(
            limit=10,
            status="completed",
            workflow_id="workflow-001",
            robot_id="robot-001",
        )

    def test_get_jobs_limit_validation(self, client):
        """Test limit parameter validation."""
        # Test below minimum
        response = client.get("/api/v1/metrics/jobs?limit=0")
        assert response.status_code == 422

        # Test above maximum
        response = client.get("/api/v1/metrics/jobs?limit=1000")
        assert response.status_code == 422

        # Test valid limit
        response = client.get("/api/v1/metrics/jobs?limit=50")
        assert response.status_code == 200

    def test_get_job_details_success(self, client):
        """Test getting detailed job information."""
        response = client.get("/api/v1/metrics/jobs/job-123")

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "job-123"
        assert data["workflow_name"] == "Data Extraction"
        assert data["status"] == "completed"
        assert data["duration_ms"] == 150000

    def test_get_job_details_not_found(self, client, mock_collector):
        """Test 404 when job not found."""
        mock_collector.get_job_details.return_value = None

        response = client.get("/api/v1/metrics/jobs/nonexistent")

        assert response.status_code == 404

    def test_get_job_details_invalid_id(self, client):
        """Test validation of job ID format."""
        response = client.get("/api/v1/metrics/jobs/invalid@job!")

        assert response.status_code == 422


class TestAnalyticsEndpoint:
    """Tests for /metrics/analytics endpoint."""

    def test_get_analytics_success(self, client):
        """Test getting aggregated analytics."""
        response = client.get("/api/v1/metrics/analytics")

        assert response.status_code == 200
        data = response.json()
        assert data["total_jobs"] == 100
        assert data["success_rate"] == 95.0
        assert data["failure_rate"] == 5.0
        assert data["p50_duration_ms"] == 100000.0
        assert data["p90_duration_ms"] == 200000.0
        assert data["p99_duration_ms"] == 300000.0
        assert len(data["slowest_workflows"]) == 1
        assert len(data["error_distribution"]) == 2
        assert data["self_healing_success_rate"] == 80.0

    def test_get_analytics_collector_error(self, client, mock_collector):
        """Test error handling when analytics collection fails."""
        mock_collector.get_analytics.side_effect = Exception("Aggregation error")

        response = client.get("/api/v1/metrics/analytics")

        assert response.status_code == 500
