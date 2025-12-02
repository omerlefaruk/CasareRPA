"""
Tests for CasareRPA Cloud Orchestrator Server.

Test coverage:
- OrchestratorConfig: Environment loading, defaults, CORS parsing
- RobotManager: Robot registration, job management, state tracking
- Health endpoints: /health, /health/live, /health/ready
- Robot API: GET /api/robots, GET /api/robots/{id}
- Job API: POST /api/jobs, GET /api/jobs, GET /api/jobs/{id}
- WebSocket: Robot connections, admin connections, message handling
"""

import asyncio
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import orjson
import pytest

from casare_rpa.infrastructure.orchestrator.server import (
    ConnectedRobot,
    JobSubmission,
    OrchestratorConfig,
    PendingJob,
    RobotManager,
    RobotRegistration,
)


# =============================================================================
# OrchestratorConfig Tests
# =============================================================================


class TestOrchestratorConfig:
    """Tests for OrchestratorConfig dataclass."""

    def test_default_values(self, orchestrator_config):
        """Verify default configuration values."""
        assert orchestrator_config.host == "0.0.0.0"
        assert orchestrator_config.port == 8000
        assert orchestrator_config.workers == 1
        assert orchestrator_config.database_url is None
        assert orchestrator_config.supabase_url is None
        assert orchestrator_config.supabase_key is None
        assert orchestrator_config.redis_url is None
        assert orchestrator_config.api_secret == ""
        assert orchestrator_config.cors_origins == []
        assert orchestrator_config.robot_heartbeat_timeout == 90
        assert orchestrator_config.job_timeout_default == 3600
        assert orchestrator_config.websocket_ping_interval == 30

    def test_custom_values(self, orchestrator_config_custom):
        """Verify custom configuration values."""
        assert orchestrator_config_custom.host == "192.168.1.100"
        assert orchestrator_config_custom.port == 9000
        assert orchestrator_config_custom.workers == 4
        assert (
            orchestrator_config_custom.database_url
            == "postgresql://test:test@localhost/test"
        )
        assert orchestrator_config_custom.supabase_url == "https://custom.supabase.co"
        assert orchestrator_config_custom.supabase_key == "custom-key"
        assert orchestrator_config_custom.redis_url == "redis://redis:6379"
        assert orchestrator_config_custom.api_secret == "custom-secret"
        assert len(orchestrator_config_custom.cors_origins) == 2
        assert orchestrator_config_custom.robot_heartbeat_timeout == 120
        assert orchestrator_config_custom.job_timeout_default == 7200
        assert orchestrator_config_custom.websocket_ping_interval == 45

    def test_from_env_defaults(self, clean_env):
        """from_env() returns defaults when env vars missing."""
        config = OrchestratorConfig.from_env()

        assert config.host == "0.0.0.0"
        assert config.port == 8000
        assert config.workers == 1
        assert config.database_url is None
        assert config.cors_origins == []

    def test_from_env_loads_all_variables(self, env_with_config):
        """from_env() loads all environment variables correctly."""
        config = OrchestratorConfig.from_env()

        assert config.host == "127.0.0.1"
        assert config.port == 9000
        assert config.workers == 4
        assert config.database_url == "postgresql://user:pass@localhost:5432/db"
        assert config.supabase_url == "https://test.supabase.co"
        assert config.supabase_key == "test-key"
        assert config.redis_url == "redis://localhost:6379"
        assert config.api_secret == "test-secret-key"
        assert config.robot_heartbeat_timeout == 120
        assert config.job_timeout_default == 7200
        assert config.websocket_ping_interval == 45

    def test_cors_origins_list_parses_comma_separated(self, env_with_config):
        """CORS_ORIGINS parses comma-separated values."""
        config = OrchestratorConfig.from_env()

        assert len(config.cors_origins) == 2
        assert "http://localhost:3000" in config.cors_origins
        assert "https://app.example.com" in config.cors_origins

    def test_cors_origins_handles_whitespace(self, clean_env):
        """CORS_ORIGINS trims whitespace from values."""
        os.environ["CORS_ORIGINS"] = "  http://a.com  ,  http://b.com  ,  "
        config = OrchestratorConfig.from_env()

        assert config.cors_origins == ["http://a.com", "http://b.com"]

    def test_cors_origins_empty_string(self, clean_env):
        """CORS_ORIGINS handles empty string."""
        os.environ["CORS_ORIGINS"] = ""
        config = OrchestratorConfig.from_env()

        assert config.cors_origins == []


# =============================================================================
# ConnectedRobot Tests
# =============================================================================


class TestConnectedRobot:
    """Tests for ConnectedRobot dataclass."""

    def test_status_idle_when_no_jobs(self, connected_robot):
        """Robot status is 'idle' when no jobs assigned."""
        assert connected_robot.status == "idle"
        assert connected_robot.available_slots == 3

    def test_status_working_when_has_jobs(self, connected_robot):
        """Robot status is 'working' when has some jobs but not at capacity."""
        connected_robot.current_job_ids.add("job-001")

        assert connected_robot.status == "working"
        assert connected_robot.available_slots == 2

    def test_status_busy_when_at_capacity(self, connected_robot_busy):
        """Robot status is 'busy' when at max concurrent jobs."""
        assert connected_robot_busy.status == "busy"
        assert connected_robot_busy.available_slots == 0

    def test_available_slots_calculation(self, mock_websocket):
        """Available slots calculated correctly."""
        robot = ConnectedRobot(
            robot_id="robot-test",
            robot_name="Test",
            websocket=mock_websocket,
            max_concurrent_jobs=5,
        )
        robot.current_job_ids.add("job-1")
        robot.current_job_ids.add("job-2")

        assert robot.available_slots == 3

    def test_available_slots_never_negative(self, mock_websocket):
        """Available slots never goes negative."""
        robot = ConnectedRobot(
            robot_id="robot-test",
            robot_name="Test",
            websocket=mock_websocket,
            max_concurrent_jobs=1,
        )
        robot.current_job_ids.add("job-1")
        robot.current_job_ids.add("job-2")  # Over capacity

        assert robot.available_slots == 0


# =============================================================================
# RobotManager Tests
# =============================================================================


class TestRobotManager:
    """Tests for RobotManager class."""

    @pytest.mark.asyncio
    async def test_register_robot_adds_to_registry(
        self,
        robot_manager,
        mock_websocket,
        sample_robot_registration,
    ):
        """register_robot adds robot to internal registry."""
        robot = await robot_manager.register_robot(
            mock_websocket, sample_robot_registration
        )

        assert robot.robot_id == sample_robot_registration.robot_id
        assert robot.robot_name == sample_robot_registration.robot_name
        assert robot_manager.get_robot(sample_robot_registration.robot_id) is robot

    @pytest.mark.asyncio
    async def test_register_robot_extracts_capabilities(
        self,
        robot_manager,
        mock_websocket,
        sample_robot_registration,
    ):
        """register_robot extracts capabilities from registration."""
        robot = await robot_manager.register_robot(
            mock_websocket, sample_robot_registration
        )

        assert "browser" in robot.capabilities
        assert "desktop" in robot.capabilities
        assert robot.max_concurrent_jobs == 3

    @pytest.mark.asyncio
    async def test_register_robot_broadcasts_to_admins(
        self,
        robot_manager,
        mock_websocket,
        mock_websocket_factory,
        sample_robot_registration,
    ):
        """register_robot broadcasts to admin connections."""
        admin_ws = mock_websocket_factory()
        await robot_manager.add_admin_connection(admin_ws)

        await robot_manager.register_robot(mock_websocket, sample_robot_registration)

        assert len(admin_ws.sent_messages) == 1
        msg = orjson.loads(admin_ws.sent_messages[0])
        assert msg["type"] == "robot_connected"
        assert msg["robot_id"] == sample_robot_registration.robot_id

    @pytest.mark.asyncio
    async def test_unregister_robot_removes_from_registry(
        self,
        robot_manager,
        mock_websocket,
        sample_robot_registration,
    ):
        """unregister_robot removes robot from registry."""
        await robot_manager.register_robot(mock_websocket, sample_robot_registration)

        await robot_manager.unregister_robot(sample_robot_registration.robot_id)

        assert robot_manager.get_robot(sample_robot_registration.robot_id) is None

    @pytest.mark.asyncio
    async def test_unregister_robot_requeues_jobs(
        self,
        robot_manager,
        mock_websocket,
        sample_robot_registration,
        sample_job_submission,
    ):
        """unregister_robot requeues assigned jobs."""
        robot = await robot_manager.register_robot(
            mock_websocket, sample_robot_registration
        )
        job = await robot_manager.submit_job(sample_job_submission)

        # Job should be assigned
        assert job.status == "assigned"
        assert robot.robot_id in str(job.assigned_robot_id)

        # Disconnect robot
        await robot_manager.unregister_robot(robot.robot_id)

        # Job should be requeued
        assert job.status == "pending"
        assert job.assigned_robot_id is None

    @pytest.mark.asyncio
    async def test_unregister_nonexistent_robot_no_error(self, robot_manager):
        """unregister_robot handles nonexistent robot gracefully."""
        await robot_manager.unregister_robot("nonexistent-robot")
        # Should not raise

    def test_get_robot_returns_robot_by_id(
        self,
        robot_manager,
        mock_websocket,
    ):
        """get_robot returns robot by ID."""
        from casare_rpa.infrastructure.orchestrator.server import ConnectedRobot

        robot = ConnectedRobot(
            robot_id="robot-test",
            robot_name="Test Robot",
            websocket=mock_websocket,
        )
        robot_manager._robots["robot-test"] = robot

        result = robot_manager.get_robot("robot-test")

        assert result is robot

    def test_get_robot_returns_none_for_unknown(self, robot_manager):
        """get_robot returns None for unknown ID."""
        result = robot_manager.get_robot("unknown-robot")

        assert result is None

    def test_get_all_robots_returns_list(self, robot_manager, mock_websocket_factory):
        """get_all_robots returns all connected robots."""
        from casare_rpa.infrastructure.orchestrator.server import ConnectedRobot

        robot1 = ConnectedRobot(
            robot_id="robot-1",
            robot_name="Robot 1",
            websocket=mock_websocket_factory(),
        )
        robot2 = ConnectedRobot(
            robot_id="robot-2",
            robot_name="Robot 2",
            websocket=mock_websocket_factory(),
        )
        robot_manager._robots["robot-1"] = robot1
        robot_manager._robots["robot-2"] = robot2

        result = robot_manager.get_all_robots()

        assert len(result) == 2
        assert robot1 in result
        assert robot2 in result

    def test_get_all_robots_empty_when_none_connected(self, robot_manager):
        """get_all_robots returns empty list when no robots connected."""
        result = robot_manager.get_all_robots()

        assert result == []

    @pytest.mark.asyncio
    async def test_submit_job_adds_to_queue(
        self,
        robot_manager,
        sample_job_submission_minimal,
    ):
        """submit_job adds job to internal queue."""
        job = await robot_manager.submit_job(sample_job_submission_minimal)

        assert job.job_id is not None
        assert job.workflow_id == sample_job_submission_minimal.workflow_id
        assert robot_manager.get_job(job.job_id) is job

    @pytest.mark.asyncio
    async def test_submit_job_uses_default_timeout(
        self,
        robot_manager,
        sample_job_submission_minimal,
    ):
        """submit_job uses config default timeout when not specified."""
        job = await robot_manager.submit_job(sample_job_submission_minimal)

        assert job.timeout == robot_manager.config.job_timeout_default

    @pytest.mark.asyncio
    async def test_submit_job_uses_custom_timeout(
        self,
        robot_manager,
        sample_job_submission,
    ):
        """submit_job uses provided timeout when specified."""
        job = await robot_manager.submit_job(sample_job_submission)

        assert job.timeout == 1800

    @pytest.mark.asyncio
    async def test_submit_job_assigns_to_available_robot(
        self,
        robot_manager,
        mock_websocket,
        sample_robot_registration,
        sample_job_submission,
    ):
        """submit_job assigns to available robot immediately."""
        await robot_manager.register_robot(mock_websocket, sample_robot_registration)

        job = await robot_manager.submit_job(sample_job_submission)

        assert job.status == "assigned"
        assert job.assigned_robot_id == sample_robot_registration.robot_id

    @pytest.mark.asyncio
    async def test_submit_job_pending_when_no_robots(
        self,
        robot_manager,
        sample_job_submission,
    ):
        """submit_job stays pending when no robots available."""
        job = await robot_manager.submit_job(sample_job_submission)

        assert job.status == "pending"
        assert job.assigned_robot_id is None

    @pytest.mark.asyncio
    async def test_submit_job_sends_to_robot_websocket(
        self,
        robot_manager,
        mock_websocket,
        sample_robot_registration,
        sample_job_submission,
    ):
        """submit_job sends job assignment via WebSocket."""
        await robot_manager.register_robot(mock_websocket, sample_robot_registration)

        await robot_manager.submit_job(sample_job_submission)

        assert len(mock_websocket.sent_messages) >= 1
        # First message is admin broadcast, last should be job assignment
        job_msg = orjson.loads(mock_websocket.sent_messages[-1])
        assert job_msg["type"] == "job_assign"
        assert job_msg["workflow_id"] == sample_job_submission.workflow_id

    @pytest.mark.asyncio
    async def test_job_completed_marks_job_done(
        self,
        robot_manager,
        mock_websocket,
        sample_robot_registration,
        sample_job_submission,
    ):
        """job_completed marks job as completed."""
        await robot_manager.register_robot(mock_websocket, sample_robot_registration)
        job = await robot_manager.submit_job(sample_job_submission)

        await robot_manager.job_completed(
            sample_robot_registration.robot_id,
            job.job_id,
            success=True,
            result={"data": "extracted"},
        )

        assert job.status == "completed"

    @pytest.mark.asyncio
    async def test_job_completed_marks_job_failed(
        self,
        robot_manager,
        mock_websocket,
        sample_robot_registration,
        sample_job_submission,
    ):
        """job_completed marks job as failed when success=False."""
        await robot_manager.register_robot(mock_websocket, sample_robot_registration)
        job = await robot_manager.submit_job(sample_job_submission)

        await robot_manager.job_completed(
            sample_robot_registration.robot_id,
            job.job_id,
            success=False,
            result={"error": "Timeout"},
        )

        assert job.status == "failed"

    @pytest.mark.asyncio
    async def test_job_completed_frees_robot_slot(
        self,
        robot_manager,
        mock_websocket,
        sample_robot_registration,
        sample_job_submission,
    ):
        """job_completed removes job from robot's current jobs."""
        robot = await robot_manager.register_robot(
            mock_websocket, sample_robot_registration
        )
        job = await robot_manager.submit_job(sample_job_submission)

        assert job.job_id in robot.current_job_ids

        await robot_manager.job_completed(
            robot.robot_id,
            job.job_id,
            success=True,
            result={},
        )

        assert job.job_id not in robot.current_job_ids

    def test_get_job_returns_job_by_id(self, robot_manager, pending_job):
        """get_job returns job by ID."""
        robot_manager._jobs[pending_job.job_id] = pending_job

        result = robot_manager.get_job(pending_job.job_id)

        assert result is pending_job

    def test_get_job_returns_none_for_unknown(self, robot_manager):
        """get_job returns None for unknown ID."""
        result = robot_manager.get_job("unknown-job")

        assert result is None

    def test_get_pending_jobs_filters_correctly(self, robot_manager):
        """get_pending_jobs returns only pending jobs."""
        pending = PendingJob(
            job_id="pending-1",
            workflow_id="wf-1",
            workflow_data={},
            variables={},
            priority=5,
            target_robot_id=None,
            required_capabilities=[],
            timeout=3600,
            status="pending",
        )
        assigned = PendingJob(
            job_id="assigned-1",
            workflow_id="wf-2",
            workflow_data={},
            variables={},
            priority=5,
            target_robot_id=None,
            required_capabilities=[],
            timeout=3600,
            status="assigned",
        )
        completed = PendingJob(
            job_id="completed-1",
            workflow_id="wf-3",
            workflow_data={},
            variables={},
            priority=5,
            target_robot_id=None,
            required_capabilities=[],
            timeout=3600,
            status="completed",
        )

        robot_manager._jobs["pending-1"] = pending
        robot_manager._jobs["assigned-1"] = assigned
        robot_manager._jobs["completed-1"] = completed

        result = robot_manager.get_pending_jobs()

        assert len(result) == 1
        assert result[0] is pending

    @pytest.mark.asyncio
    async def test_update_heartbeat_updates_timestamp(
        self,
        robot_manager,
        mock_websocket,
        sample_robot_registration,
    ):
        """update_heartbeat updates robot's last_heartbeat."""
        robot = await robot_manager.register_robot(
            mock_websocket, sample_robot_registration
        )
        original_heartbeat = robot.last_heartbeat

        await asyncio.sleep(0.01)  # Small delay
        await robot_manager.update_heartbeat(robot.robot_id, {"cpu": 50})

        assert robot.last_heartbeat > original_heartbeat

    @pytest.mark.asyncio
    async def test_get_available_robots_filters_by_capacity(
        self,
        robot_manager,
        mock_websocket_factory,
    ):
        """get_available_robots filters out robots at capacity."""
        from casare_rpa.infrastructure.orchestrator.server import ConnectedRobot

        available = ConnectedRobot(
            robot_id="available",
            robot_name="Available",
            websocket=mock_websocket_factory(),
            max_concurrent_jobs=2,
        )
        busy = ConnectedRobot(
            robot_id="busy",
            robot_name="Busy",
            websocket=mock_websocket_factory(),
            max_concurrent_jobs=1,
        )
        busy.current_job_ids.add("job-1")

        robot_manager._robots["available"] = available
        robot_manager._robots["busy"] = busy

        result = robot_manager.get_available_robots()

        assert len(result) == 1
        assert result[0] is available

    @pytest.mark.asyncio
    async def test_get_available_robots_filters_by_capabilities(
        self,
        robot_manager,
        mock_websocket_factory,
    ):
        """get_available_robots filters by required capabilities."""
        from casare_rpa.infrastructure.orchestrator.server import ConnectedRobot

        browser_robot = ConnectedRobot(
            robot_id="browser",
            robot_name="Browser Robot",
            websocket=mock_websocket_factory(),
            capabilities=["browser"],
        )
        desktop_robot = ConnectedRobot(
            robot_id="desktop",
            robot_name="Desktop Robot",
            websocket=mock_websocket_factory(),
            capabilities=["desktop"],
        )

        robot_manager._robots["browser"] = browser_robot
        robot_manager._robots["desktop"] = desktop_robot

        result = robot_manager.get_available_robots(required_capabilities=["browser"])

        assert len(result) == 1
        assert result[0] is browser_robot


# =============================================================================
# Health Endpoint Tests
# =============================================================================


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    @pytest.mark.asyncio
    async def test_health_returns_healthy(self, client):
        """GET /health returns 200 with healthy status."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "casare-orchestrator"

    @pytest.mark.asyncio
    async def test_health_live_returns_alive(self, client):
        """GET /health/live returns 200 with alive=True."""
        response = await client.get("/health/live")

        assert response.status_code == 200
        data = response.json()
        assert data["alive"] is True

    @pytest.mark.asyncio
    async def test_health_ready_returns_ready(self, client):
        """GET /health/ready returns 200 with ready status."""
        response = await client.get("/health/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is True
        assert "connected_robots" in data
        assert "pending_jobs" in data


# =============================================================================
# Robot API Endpoint Tests
# =============================================================================


class TestRobotApiEndpoints:
    """Tests for robot management API endpoints."""

    @pytest.mark.asyncio
    async def test_list_robots_empty(self, client):
        """GET /api/robots returns empty list when no robots connected."""
        response = await client.get(
            "/api/robots",
            headers={"X-Api-Key": "test-api-secret"},
        )

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_robots_returns_connected(self, app, client, mock_websocket):
        """GET /api/robots returns list of connected robots."""
        from casare_rpa.infrastructure.orchestrator.server import (
            ConnectedRobot,
            get_robot_manager,
        )

        manager = get_robot_manager()
        robot = ConnectedRobot(
            robot_id="test-robot",
            robot_name="Test Robot",
            websocket=mock_websocket,
            capabilities=["browser"],
            max_concurrent_jobs=2,
        )
        manager._robots["test-robot"] = robot

        response = await client.get(
            "/api/robots",
            headers={"X-Api-Key": "test-api-secret"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["robot_id"] == "test-robot"
        assert data[0]["robot_name"] == "Test Robot"
        assert data[0]["status"] == "idle"
        assert "browser" in data[0]["capabilities"]

    @pytest.mark.asyncio
    async def test_get_robot_by_id_success(self, app, client, mock_websocket):
        """GET /api/robots/{id} returns specific robot."""
        from casare_rpa.infrastructure.orchestrator.server import (
            ConnectedRobot,
            get_robot_manager,
        )

        manager = get_robot_manager()
        robot = ConnectedRobot(
            robot_id="robot-123",
            robot_name="Robot 123",
            websocket=mock_websocket,
            capabilities=["desktop"],
        )
        manager._robots["robot-123"] = robot

        response = await client.get(
            "/api/robots/robot-123",
            headers={"X-Api-Key": "test-api-secret"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["robot_id"] == "robot-123"
        assert data["robot_name"] == "Robot 123"

    @pytest.mark.asyncio
    async def test_get_robot_by_id_not_found(self, client):
        """GET /api/robots/{id} returns 404 for unknown robot."""
        response = await client.get(
            "/api/robots/unknown-robot",
            headers={"X-Api-Key": "test-api-secret"},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


# =============================================================================
# Job API Endpoint Tests
# =============================================================================


class TestJobApiEndpoints:
    """Tests for job management API endpoints."""

    @pytest.mark.asyncio
    async def test_submit_job_success(self, client):
        """POST /api/jobs creates new job."""
        response = await client.post(
            "/api/jobs",
            json={
                "workflow_id": "wf-001",
                "workflow_data": {"name": "Test"},
                "variables": {},
                "priority": 5,
            },
            headers={"X-Api-Key": "test-api-secret"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["workflow_id"] == "wf-001"
        assert data["status"] in ["pending", "assigned"]

    @pytest.mark.asyncio
    async def test_submit_job_validates_required_fields(self, client):
        """POST /api/jobs validates required fields."""
        response = await client.post(
            "/api/jobs",
            json={
                "variables": {},
            },
            headers={"X-Api-Key": "test-api-secret"},
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_submit_job_with_priority(self, client):
        """POST /api/jobs accepts priority."""
        response = await client.post(
            "/api/jobs",
            json={
                "workflow_id": "wf-priority",
                "workflow_data": {},
                "priority": 10,
            },
            headers={"X-Api-Key": "test-api-secret"},
        )

        assert response.status_code == 200
        # Priority should be between 1-10

    @pytest.mark.asyncio
    async def test_list_jobs_empty(self, client):
        """GET /api/jobs returns empty list when no jobs."""
        response = await client.get(
            "/api/jobs",
            headers={"X-Api-Key": "test-api-secret"},
        )

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_jobs_returns_all(self, app, client):
        """GET /api/jobs returns list of jobs."""
        from casare_rpa.infrastructure.orchestrator.server import (
            PendingJob,
            get_robot_manager,
        )

        manager = get_robot_manager()
        job = PendingJob(
            job_id="job-list-test",
            workflow_id="wf-test",
            workflow_data={"name": "Test"},
            variables={},
            priority=5,
            target_robot_id=None,
            required_capabilities=[],
            timeout=3600,
        )
        manager._jobs["job-list-test"] = job

        response = await client.get(
            "/api/jobs",
            headers={"X-Api-Key": "test-api-secret"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["job_id"] == "job-list-test"

    @pytest.mark.asyncio
    async def test_list_jobs_filters_by_status(self, app, client):
        """GET /api/jobs filters by status parameter."""
        from casare_rpa.infrastructure.orchestrator.server import (
            PendingJob,
            get_robot_manager,
        )

        manager = get_robot_manager()
        pending = PendingJob(
            job_id="job-pending",
            workflow_id="wf-1",
            workflow_data={},
            variables={},
            priority=5,
            target_robot_id=None,
            required_capabilities=[],
            timeout=3600,
            status="pending",
        )
        completed = PendingJob(
            job_id="job-completed",
            workflow_id="wf-2",
            workflow_data={},
            variables={},
            priority=5,
            target_robot_id=None,
            required_capabilities=[],
            timeout=3600,
            status="completed",
        )
        manager._jobs["job-pending"] = pending
        manager._jobs["job-completed"] = completed

        response = await client.get(
            "/api/jobs?status=pending",
            headers={"X-Api-Key": "test-api-secret"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["job_id"] == "job-pending"

    @pytest.mark.asyncio
    async def test_get_job_by_id_success(self, app, client):
        """GET /api/jobs/{id} returns job status."""
        from casare_rpa.infrastructure.orchestrator.server import (
            PendingJob,
            get_robot_manager,
        )

        manager = get_robot_manager()
        job = PendingJob(
            job_id="job-get-test",
            workflow_id="wf-test",
            workflow_data={"name": "Test"},
            variables={"key": "value"},
            priority=7,
            target_robot_id=None,
            required_capabilities=[],
            timeout=1800,
        )
        manager._jobs["job-get-test"] = job

        response = await client.get(
            "/api/jobs/job-get-test",
            headers={"X-Api-Key": "test-api-secret"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "job-get-test"
        assert data["workflow_id"] == "wf-test"
        assert data["priority"] == 7

    @pytest.mark.asyncio
    async def test_get_job_by_id_not_found(self, client):
        """GET /api/jobs/{id} returns 404 for unknown job."""
        response = await client.get(
            "/api/jobs/unknown-job",
            headers={"X-Api-Key": "test-api-secret"},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


# =============================================================================
# WebSocket Robot Connection Tests
# =============================================================================

# Note: MockWebSocket is defined in conftest.py - use the fixture


class TestWebSocketRobotConnection:
    """Tests for robot WebSocket connections."""

    @pytest.mark.asyncio
    async def test_robot_connects_and_registers(
        self,
        robot_manager,
        mock_websocket,
        register_message,
    ):
        """Robot connects and registers successfully."""

        registration = RobotRegistration(
            robot_id="robot-ws-test",
            robot_name="WebSocket Test Robot",
            capabilities={"types": ["browser"]},
        )

        robot = await robot_manager.register_robot(mock_websocket, registration)

        assert robot is not None
        assert robot.robot_id == "robot-ws-test"
        assert robot_manager.get_robot("robot-ws-test") is robot

    @pytest.mark.asyncio
    async def test_robot_receives_job_assignment(
        self,
        robot_manager,
        mock_websocket,
        sample_robot_registration,
        sample_job_submission,
    ):
        """Robot receives job assignment via WebSocket."""
        await robot_manager.register_robot(mock_websocket, sample_robot_registration)

        await robot_manager.submit_job(sample_job_submission)

        # Should have received job_assign message
        sent_json = [orjson.loads(m) for m in mock_websocket.sent_messages]
        job_assigns = [m for m in sent_json if m.get("type") == "job_assign"]

        assert len(job_assigns) == 1
        assert job_assigns[0]["workflow_id"] == sample_job_submission.workflow_id

    @pytest.mark.asyncio
    async def test_robot_heartbeat_updates_timestamp(
        self,
        robot_manager,
        mock_websocket,
        sample_robot_registration,
    ):
        """Robot heartbeat updates last_heartbeat timestamp."""
        robot = await robot_manager.register_robot(
            mock_websocket, sample_robot_registration
        )
        original = robot.last_heartbeat

        await asyncio.sleep(0.01)
        await robot_manager.update_heartbeat(
            robot.robot_id,
            {"cpu": 45, "memory": 60},
        )

        assert robot.last_heartbeat > original


# =============================================================================
# WebSocket Admin Connection Tests
# =============================================================================


class TestWebSocketAdminConnection:
    """Tests for admin WebSocket connections."""

    @pytest.mark.asyncio
    async def test_admin_connects_successfully(self, robot_manager, mock_websocket):
        """Admin WebSocket connects successfully."""
        await robot_manager.add_admin_connection(mock_websocket)

        assert mock_websocket in robot_manager._admin_connections

    @pytest.mark.asyncio
    async def test_admin_receives_robot_updates(
        self,
        robot_manager,
        mock_websocket,
        mock_websocket_factory,
        sample_robot_registration,
    ):
        """Admin receives robot connection updates."""
        admin_ws = mock_websocket_factory()
        await robot_manager.add_admin_connection(admin_ws)

        robot_ws = mock_websocket_factory()
        await robot_manager.register_robot(robot_ws, sample_robot_registration)

        # Admin should receive robot_connected event
        sent_json = [orjson.loads(m) for m in admin_ws.sent_messages]
        robot_events = [m for m in sent_json if m.get("type") == "robot_connected"]

        assert len(robot_events) == 1
        assert robot_events[0]["robot_id"] == sample_robot_registration.robot_id

    @pytest.mark.asyncio
    async def test_admin_receives_job_updates(
        self,
        robot_manager,
        mock_websocket,
        mock_websocket_factory,
        sample_robot_registration,
        sample_job_submission,
    ):
        """Admin receives job completion updates."""
        admin_ws = mock_websocket_factory()
        await robot_manager.add_admin_connection(admin_ws)

        robot_ws = mock_websocket_factory()
        await robot_manager.register_robot(robot_ws, sample_robot_registration)

        job = await robot_manager.submit_job(sample_job_submission)
        await robot_manager.job_completed(
            sample_robot_registration.robot_id,
            job.job_id,
            success=True,
            result={"data": "test"},
        )

        # Admin should receive job_completed event
        sent_json = [orjson.loads(m) for m in admin_ws.sent_messages]
        job_events = [m for m in sent_json if m.get("type") == "job_completed"]

        assert len(job_events) == 1
        assert job_events[0]["job_id"] == job.job_id
        assert job_events[0]["success"] is True

    @pytest.mark.asyncio
    async def test_admin_disconnect_removes_from_list(
        self,
        robot_manager,
        mock_websocket,
    ):
        """Disconnected admin is removed from admin connections."""
        await robot_manager.add_admin_connection(mock_websocket)
        assert mock_websocket in robot_manager._admin_connections

        robot_manager.remove_admin_connection(mock_websocket)

        assert mock_websocket not in robot_manager._admin_connections

    @pytest.mark.asyncio
    async def test_broadcast_handles_failed_connections(
        self,
        robot_manager,
        mock_websocket_factory,
    ):
        """Broadcast removes failed admin connections."""
        good_ws = mock_websocket_factory()
        bad_ws = mock_websocket_factory()

        # Make bad_ws fail on send
        async def fail_send(data):
            raise Exception("Connection closed")

        bad_ws.send_text = fail_send

        await robot_manager.add_admin_connection(good_ws)
        await robot_manager.add_admin_connection(bad_ws)

        # Broadcast should handle the failure
        await robot_manager._broadcast_admin({"type": "test"})

        # Bad connection should be removed
        assert bad_ws not in robot_manager._admin_connections
        assert good_ws in robot_manager._admin_connections


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_job_assignment_fails_gracefully(
        self,
        robot_manager,
        mock_websocket,
        sample_robot_registration,
    ):
        """Job assignment handles WebSocket send failure."""
        await robot_manager.register_robot(mock_websocket, sample_robot_registration)

        # Make send fail
        async def fail_send(data):
            raise Exception("Send failed")

        mock_websocket.send_text = fail_send

        job = await robot_manager.submit_job(
            JobSubmission(
                workflow_id="fail-test",
                workflow_data={},
            )
        )

        # Job should be requeued as pending
        assert job.status == "pending"
        assert job.assigned_robot_id is None

    @pytest.mark.asyncio
    async def test_concurrent_job_submissions(
        self, robot_manager, mock_websocket_factory
    ):
        """Handles concurrent job submissions correctly."""

        # Register a robot
        reg = RobotRegistration(
            robot_id="concurrent-robot",
            robot_name="Concurrent Robot",
            capabilities={"types": [], "max_concurrent_jobs": 3},
        )
        await robot_manager.register_robot(mock_websocket_factory(), reg)

        # Submit multiple jobs concurrently
        submissions = [
            JobSubmission(workflow_id=f"wf-{i}", workflow_data={}) for i in range(5)
        ]

        jobs = await asyncio.gather(
            *[robot_manager.submit_job(sub) for sub in submissions]
        )

        # All jobs should be created
        assert len(jobs) == 5

        # At most 3 should be assigned (robot capacity)
        assigned = [j for j in jobs if j.status == "assigned"]
        assert len(assigned) <= 3

    @pytest.mark.asyncio
    async def test_targeted_job_waits_for_specific_robot(
        self,
        robot_manager,
        mock_websocket_factory,
    ):
        """Targeted job stays pending if target robot unavailable."""

        # Register a different robot
        reg = RobotRegistration(
            robot_id="other-robot",
            robot_name="Other Robot",
            capabilities={"types": ["browser"]},
        )
        await robot_manager.register_robot(mock_websocket_factory(), reg)

        # Submit job targeting nonexistent robot
        job = await robot_manager.submit_job(
            JobSubmission(
                workflow_id="targeted-wf",
                workflow_data={},
                target_robot_id="specific-robot",  # Not registered
            )
        )

        # Job should stay pending
        assert job.status == "pending"
        assert job.target_robot_id == "specific-robot"

    @pytest.mark.asyncio
    async def test_capability_matching_all_required(
        self,
        robot_manager,
        mock_websocket_factory,
    ):
        """Job requiring capabilities only assigned to matching robot."""

        # Robot with only browser capability
        browser_reg = RobotRegistration(
            robot_id="browser-only",
            robot_name="Browser Only",
            capabilities={"types": ["browser"]},
        )
        await robot_manager.register_robot(mock_websocket_factory(), browser_reg)

        # Job requiring both browser and desktop
        job = await robot_manager.submit_job(
            JobSubmission(
                workflow_id="multi-cap-wf",
                workflow_data={},
                required_capabilities=["browser", "desktop"],
            )
        )

        # Should not be assigned (robot lacks desktop)
        assert job.status == "pending"
