"""
Shared fixtures for Cloud Orchestrator Server tests.

Provides:
- FastAPI TestClient setup
- Mock WebSocket connections
- OrchestratorConfig fixtures
- RobotManager fixtures
- Sample robot/job data
"""

import asyncio
import os
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from httpx import ASGITransport, AsyncClient


# ============================================================================
# Environment Fixtures
# ============================================================================


@pytest.fixture
def clean_env():
    """Remove orchestrator-related env vars for clean tests."""
    env_vars = [
        "HOST",
        "PORT",
        "WORKERS",
        "DATABASE_URL",
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "REDIS_URL",
        "API_SECRET",
        "CORS_ORIGINS",
        "ROBOT_HEARTBEAT_TIMEOUT",
        "JOB_TIMEOUT_DEFAULT",
        "WS_PING_INTERVAL",
    ]
    old_values = {}
    for var in env_vars:
        if var in os.environ:
            old_values[var] = os.environ.pop(var)
    yield
    # Restore original values
    for var, value in old_values.items():
        os.environ[var] = value


@pytest.fixture
def env_with_config(clean_env):
    """Set up environment with orchestrator configuration."""
    os.environ["HOST"] = "127.0.0.1"
    os.environ["PORT"] = "9000"
    os.environ["WORKERS"] = "4"
    os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/db"
    os.environ["SUPABASE_URL"] = "https://test.supabase.co"
    os.environ["SUPABASE_KEY"] = "test-key"
    os.environ["REDIS_URL"] = "redis://localhost:6379"
    os.environ["API_SECRET"] = "test-secret-key"
    os.environ["CORS_ORIGINS"] = "http://localhost:3000, https://app.example.com"
    os.environ["ROBOT_HEARTBEAT_TIMEOUT"] = "120"
    os.environ["JOB_TIMEOUT_DEFAULT"] = "7200"
    os.environ["WS_PING_INTERVAL"] = "45"
    yield


@pytest.fixture
def env_with_api_secret(clean_env):
    """Set up environment with API_SECRET for authentication tests."""
    os.environ["API_SECRET"] = "test-api-secret"
    yield


# ============================================================================
# Config Fixtures
# ============================================================================


@pytest.fixture
def orchestrator_config():
    """Create OrchestratorConfig with default values."""
    from casare_rpa.infrastructure.orchestrator.server import OrchestratorConfig

    return OrchestratorConfig()


@pytest.fixture
def orchestrator_config_custom():
    """Create OrchestratorConfig with custom values."""
    from casare_rpa.infrastructure.orchestrator.server import OrchestratorConfig

    return OrchestratorConfig(
        host="192.168.1.100",
        port=9000,
        workers=4,
        database_url="postgresql://test:test@localhost/test",
        supabase_url="https://custom.supabase.co",
        supabase_key="custom-key",
        redis_url="redis://redis:6379",
        api_secret="custom-secret",
        cors_origins=["http://localhost:3000", "https://app.example.com"],
        robot_heartbeat_timeout=120,
        job_timeout_default=7200,
        websocket_ping_interval=45,
    )


# ============================================================================
# Robot Manager Fixtures
# ============================================================================


@pytest.fixture
def robot_manager(orchestrator_config):
    """Create fresh RobotManager instance."""
    from casare_rpa.infrastructure.orchestrator.server import RobotManager

    return RobotManager(orchestrator_config)


# ============================================================================
# WebSocket Mock Fixtures
# ============================================================================


class MockWebSocket:
    """Mock WebSocket for testing."""

    def __init__(self):
        self.accepted = False
        self.closed = False
        self.close_code: Optional[int] = None
        self.sent_messages: List[str] = []
        self.received_messages: List[str] = []
        self._receive_queue: asyncio.Queue = asyncio.Queue()

    async def accept(self):
        """Accept the WebSocket connection."""
        self.accepted = True

    async def close(self, code: int = 1000):
        """Close the WebSocket connection."""
        self.closed = True
        self.close_code = code

    async def send_text(self, data: str):
        """Send text message."""
        self.sent_messages.append(data)

    async def receive_text(self) -> str:
        """Receive text message from queue."""
        return await self._receive_queue.get()

    def queue_message(self, message: str):
        """Queue a message to be received."""
        self._receive_queue.put_nowait(message)

    def get_sent_json(self) -> List[Dict[str, Any]]:
        """Parse all sent messages as JSON."""
        import orjson

        return [orjson.loads(msg) for msg in self.sent_messages]


@pytest.fixture
def mock_websocket():
    """Create mock WebSocket."""
    return MockWebSocket()


@pytest.fixture
def mock_websocket_factory():
    """Factory to create multiple mock WebSockets."""

    def _create():
        return MockWebSocket()

    return _create


# ============================================================================
# Robot Registration Fixtures
# ============================================================================


@pytest.fixture
def sample_robot_registration():
    """Sample robot registration data."""
    from casare_rpa.infrastructure.orchestrator.server import RobotRegistration

    return RobotRegistration(
        robot_id="robot-001",
        robot_name="Test Robot 1",
        capabilities={
            "types": ["browser", "desktop", "http"],
            "max_concurrent_jobs": 3,
        },
        environment="production",
        api_key_hash="abcdef1234567890",
    )


@pytest.fixture
def sample_robot_registration_minimal():
    """Minimal robot registration data."""
    from casare_rpa.infrastructure.orchestrator.server import RobotRegistration

    return RobotRegistration(
        robot_id="robot-minimal",
        robot_name="Minimal Robot",
    )


# ============================================================================
# Job Submission Fixtures
# ============================================================================


@pytest.fixture
def sample_job_submission():
    """Sample job submission data."""
    from casare_rpa.infrastructure.orchestrator.server import JobSubmission

    return JobSubmission(
        workflow_id="workflow-001",
        workflow_data={
            "name": "Test Workflow",
            "nodes": [
                {"id": "start", "type": "start"},
                {
                    "id": "action",
                    "type": "browser.navigate",
                    "url": "https://example.com",
                },
                {"id": "end", "type": "end"},
            ],
            "connections": [
                {"from": "start", "to": "action"},
                {"from": "action", "to": "end"},
            ],
        },
        variables={"url": "https://example.com"},
        priority=7,
        target_robot_id=None,
        required_capabilities=["browser"],
        timeout=1800,
    )


@pytest.fixture
def sample_job_submission_targeted():
    """Job submission targeting specific robot."""
    from casare_rpa.infrastructure.orchestrator.server import JobSubmission

    return JobSubmission(
        workflow_id="workflow-002",
        workflow_data={"name": "Targeted Workflow", "nodes": [], "connections": []},
        variables={},
        priority=10,
        target_robot_id="robot-001",
        required_capabilities=[],
        timeout=None,
    )


@pytest.fixture
def sample_job_submission_minimal():
    """Minimal job submission data."""
    from casare_rpa.infrastructure.orchestrator.server import JobSubmission

    return JobSubmission(
        workflow_id="workflow-minimal",
        workflow_data={"name": "Minimal"},
    )


# ============================================================================
# FastAPI Test Client Fixtures
# ============================================================================


@pytest.fixture
def reset_global_state():
    """Reset global state before each test."""
    import casare_rpa.infrastructure.orchestrator.server as server_module

    # Reset global state
    server_module._config = None
    server_module._robot_manager = None
    server_module._db_pool = None
    yield
    # Cleanup after test
    server_module._config = None
    server_module._robot_manager = None
    server_module._db_pool = None


@pytest.fixture
async def app(reset_global_state, clean_env):
    """Create FastAPI application for testing."""
    # Set API_SECRET for authenticated endpoints
    os.environ["API_SECRET"] = "test-api-secret"
    from casare_rpa.infrastructure.orchestrator.server import create_app

    return create_app()


@pytest.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for testing FastAPI endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ============================================================================
# Connected Robot Fixtures
# ============================================================================


@pytest.fixture
def connected_robot(mock_websocket, sample_robot_registration):
    """Create a ConnectedRobot instance."""
    from casare_rpa.infrastructure.orchestrator.server import ConnectedRobot

    return ConnectedRobot(
        robot_id=sample_robot_registration.robot_id,
        robot_name=sample_robot_registration.robot_name,
        websocket=mock_websocket,
        capabilities=sample_robot_registration.capabilities.get("types", []),
        max_concurrent_jobs=sample_robot_registration.capabilities.get(
            "max_concurrent_jobs", 1
        ),
        environment=sample_robot_registration.environment,
    )


@pytest.fixture
def connected_robot_busy(mock_websocket):
    """Create a busy ConnectedRobot (at max capacity)."""
    from casare_rpa.infrastructure.orchestrator.server import ConnectedRobot

    robot = ConnectedRobot(
        robot_id="robot-busy",
        robot_name="Busy Robot",
        websocket=mock_websocket,
        capabilities=["browser"],
        max_concurrent_jobs=1,
    )
    robot.current_job_ids.add("job-001")
    return robot


# ============================================================================
# Pending Job Fixtures
# ============================================================================


@pytest.fixture
def pending_job():
    """Create a PendingJob instance."""
    from casare_rpa.infrastructure.orchestrator.server import PendingJob

    return PendingJob(
        job_id="job-001",
        workflow_id="workflow-001",
        workflow_data={"name": "Test"},
        variables={"key": "value"},
        priority=5,
        target_robot_id=None,
        required_capabilities=["browser"],
        timeout=3600,
    )


@pytest.fixture
def pending_job_high_priority():
    """Create a high-priority PendingJob."""
    from casare_rpa.infrastructure.orchestrator.server import PendingJob

    return PendingJob(
        job_id="job-high",
        workflow_id="workflow-high",
        workflow_data={"name": "High Priority"},
        variables={},
        priority=10,
        target_robot_id=None,
        required_capabilities=[],
        timeout=3600,
    )


@pytest.fixture
def pending_job_targeted():
    """Create a PendingJob targeting specific robot."""
    from casare_rpa.infrastructure.orchestrator.server import PendingJob

    return PendingJob(
        job_id="job-targeted",
        workflow_id="workflow-targeted",
        workflow_data={"name": "Targeted"},
        variables={},
        priority=5,
        target_robot_id="robot-001",
        required_capabilities=[],
        timeout=3600,
    )


# ============================================================================
# API Key Validation Fixtures
# ============================================================================


@pytest.fixture
def valid_api_key():
    """Generate a valid API key for testing."""
    return "crpa_dGhpcyBpcyBhIHRlc3QgYmFzZTY0IHRva2VuIQ"


@pytest.fixture
def invalid_api_key():
    """Invalid API key for testing."""
    return "invalid-key"


@pytest.fixture
def malformed_api_key():
    """Malformed API key (wrong prefix)."""
    return "wrong_dGhpcyBpcyBhIHRlc3QgYmFzZTY0"


# ============================================================================
# Message Fixtures for WebSocket Tests
# ============================================================================


@pytest.fixture
def register_message():
    """Sample robot registration WebSocket message."""
    import orjson

    return orjson.dumps(
        {
            "type": "register",
            "robot_id": "robot-001",
            "robot_name": "Test Robot 1",
            "capabilities": {"types": ["browser"], "max_concurrent_jobs": 2},
            "environment": "production",
        }
    ).decode()


@pytest.fixture
def heartbeat_message():
    """Sample heartbeat WebSocket message."""
    import orjson

    return orjson.dumps(
        {
            "type": "heartbeat",
            "cpu_percent": 45.5,
            "memory_percent": 62.3,
            "active_jobs": 1,
        }
    ).decode()


@pytest.fixture
def job_complete_message():
    """Sample job completion WebSocket message."""
    import orjson

    return orjson.dumps(
        {
            "type": "job_complete",
            "job_id": "job-001",
            "result": {"success": True, "data": {"extracted": "value"}},
        }
    ).decode()


@pytest.fixture
def job_failed_message():
    """Sample job failure WebSocket message."""
    import orjson

    return orjson.dumps(
        {
            "type": "job_failed",
            "job_id": "job-001",
            "error": "Selector not found: #missing-element",
        }
    ).decode()
