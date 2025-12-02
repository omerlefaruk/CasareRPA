"""
Shared fixtures for robot agent tests.

Provides mocked components for:
- WebSocket connections (websockets library)
- System metrics (psutil)
- ExecuteWorkflowUseCase
- File I/O for config loading
"""

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest


# ============================================================================
# Robot Configuration Fixtures
# ============================================================================


@pytest.fixture
def valid_config_dict() -> Dict[str, Any]:
    """Provide valid configuration dictionary."""
    return {
        "robot_name": "Test Robot",
        "control_plane_url": "wss://orchestrator.example.com/ws/robot",
        "robot_id": "robot-test-12345678",
        "heartbeat_interval": 30,
        "max_concurrent_jobs": 2,
        "capabilities": ["browser", "desktop"],
        "tags": ["test", "unit"],
        "environment": "test",
        "log_level": "DEBUG",
    }


@pytest.fixture
def minimal_config_dict() -> Dict[str, Any]:
    """Provide minimal valid configuration (required fields only)."""
    return {
        "robot_name": "Minimal Robot",
        "control_plane_url": "ws://localhost:8080/ws",
    }


@pytest.fixture
def config_json_file(tmp_path: Path, valid_config_dict: Dict[str, Any]) -> Path:
    """Create a temporary config JSON file."""
    config_file = tmp_path / "robot_config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(valid_config_dict, f)
    return config_file


@pytest.fixture
def invalid_json_file(tmp_path: Path) -> Path:
    """Create a temporary file with invalid JSON."""
    config_file = tmp_path / "invalid_config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        f.write("{invalid json content")
    return config_file


# ============================================================================
# Mock psutil Module
# ============================================================================


class MockVirtualMemory:
    """Mock psutil virtual_memory result."""

    def __init__(
        self,
        total: int = 16 * 1024**3,  # 16 GB
        available: int = 8 * 1024**3,  # 8 GB
        percent: float = 50.0,
        used: int = 8 * 1024**3,
    ):
        self.total = total
        self.available = available
        self.percent = percent
        self.used = used


class MockDiskUsage:
    """Mock psutil disk_usage result."""

    def __init__(
        self,
        total: int = 500 * 1024**3,  # 500 GB
        used: int = 250 * 1024**3,  # 250 GB
        free: int = 250 * 1024**3,
        percent: float = 50.0,
    ):
        self.total = total
        self.used = used
        self.free = free
        self.percent = percent


class MockNetIOCounters:
    """Mock psutil net_io_counters result."""

    def __init__(
        self,
        bytes_sent: int = 1000000,
        bytes_recv: int = 2000000,
    ):
        self.bytes_sent = bytes_sent
        self.bytes_recv = bytes_recv


@pytest.fixture
def mock_psutil():
    """
    Provide mocked psutil module for system metrics tests.

    Returns a mock that simulates psutil behavior for:
    - cpu_percent
    - virtual_memory
    - disk_usage
    - net_io_counters
    - cpu_count
    - boot_time
    - pids
    """
    mock = MagicMock()
    mock.cpu_percent.return_value = 25.0
    mock.virtual_memory.return_value = MockVirtualMemory()
    mock.disk_usage.return_value = MockDiskUsage()
    mock.net_io_counters.return_value = MockNetIOCounters()
    mock.cpu_count.side_effect = lambda logical=True: 8 if logical else 4
    mock.boot_time.return_value = (
        datetime.now(timezone.utc).timestamp() - 3600  # 1 hour uptime
    )
    mock.pids.return_value = list(range(100))  # 100 processes

    return mock


@pytest.fixture
def mock_psutil_high_load():
    """Provide mocked psutil with high system load (critical state)."""
    mock = MagicMock()
    mock.cpu_percent.return_value = 95.0  # Critical CPU
    mock.virtual_memory.return_value = MockVirtualMemory(
        percent=92.0
    )  # Critical memory
    mock.disk_usage.return_value = MockDiskUsage(percent=85.0)
    mock.net_io_counters.return_value = MockNetIOCounters()
    mock.cpu_count.side_effect = lambda logical=True: 8 if logical else 4
    mock.boot_time.return_value = datetime.now(timezone.utc).timestamp() - 3600
    mock.pids.return_value = list(range(100))

    return mock


# ============================================================================
# WebSocket Connection Mocks
# ============================================================================


class MockWebSocket:
    """
    Mock WebSocket connection for testing RobotAgent.

    Simulates websockets library behavior including:
    - send/recv methods (async)
    - Connection states
    - Close behavior
    - Message queue for testing sequences
    """

    def __init__(self):
        self.sent_messages: List[str] = []
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.closed = False
        self.close_code: Optional[int] = None
        self.close_reason: Optional[str] = None

    async def send(self, message: str) -> None:
        """Record sent message."""
        if self.closed:
            raise Exception("Connection closed")
        self.sent_messages.append(message)

    async def recv(self) -> str:
        """Return next message from queue."""
        if self.closed:
            raise Exception("Connection closed")
        try:
            return await asyncio.wait_for(self.message_queue.get(), timeout=5.0)
        except asyncio.TimeoutError:
            raise Exception("Receive timeout")

    async def close(self, code: int = 1000, reason: str = "") -> None:
        """Close connection."""
        self.closed = True
        self.close_code = code
        self.close_reason = reason

    def queue_message(self, message: Dict[str, Any]) -> None:
        """Add a message to the receive queue."""
        self.message_queue.put_nowait(json.dumps(message))

    def get_sent_messages(self) -> List[Dict[str, Any]]:
        """Get all sent messages as parsed JSON."""
        return [json.loads(msg) for msg in self.sent_messages]

    def get_last_sent(self) -> Optional[Dict[str, Any]]:
        """Get the last sent message as parsed JSON."""
        if self.sent_messages:
            return json.loads(self.sent_messages[-1])
        return None


@pytest.fixture
def mock_websocket() -> MockWebSocket:
    """Provide mock WebSocket connection."""
    return MockWebSocket()


@pytest.fixture
def mock_websockets_connect(mock_websocket: MockWebSocket):
    """
    Patch websockets.connect to return mock WebSocket.

    Usage in tests:
        async with mock_websockets_connect:
            # websockets.connect will return mock_websocket
            pass
    """
    with patch("websockets.connect", new_callable=AsyncMock) as mock_connect:
        mock_connect.return_value = mock_websocket
        yield mock_connect


# ============================================================================
# Job Execution Mocks
# ============================================================================


@pytest.fixture
def sample_workflow_json() -> str:
    """Provide sample workflow JSON for job execution tests."""
    workflow = {
        "name": "Test Workflow",
        "version": "1.0",
        "nodes": [
            {
                "id": "start",
                "type": "StartNode",
                "position": {"x": 0, "y": 0},
            },
            {
                "id": "end",
                "type": "EndNode",
                "position": {"x": 200, "y": 0},
            },
        ],
        "connections": [
            {"from": "start", "to": "end"},
        ],
    }
    return json.dumps(workflow)


@pytest.fixture
def sample_job_data(sample_workflow_json: str) -> Dict[str, Any]:
    """Provide sample job data for execution tests."""
    return {
        "job_id": "job-test-001",
        "workflow_name": "Test Workflow",
        "workflow_json": sample_workflow_json,
        "priority": "normal",
        "payload": {"input_var": "test_value"},
    }


@pytest.fixture
def mock_execute_workflow_use_case():
    """
    Provide mocked ExecuteWorkflowUseCase.

    Simulates successful workflow execution with:
    - execute() returning True
    - executed_nodes property
    - context with variables
    """
    mock_use_case = MagicMock()
    mock_use_case.execute = AsyncMock(return_value=True)
    mock_use_case.executed_nodes = ["start", "end"]

    mock_context = MagicMock()
    mock_context.variables = {"_job_id": "job-test-001", "result": "success"}
    mock_context.execution_path = ["start", "end"]
    mock_context.errors = []
    mock_use_case.context = mock_context

    return mock_use_case


@pytest.fixture
def mock_execute_workflow_use_case_failure():
    """Provide mocked ExecuteWorkflowUseCase that simulates failure."""
    mock_use_case = MagicMock()
    mock_use_case.execute = AsyncMock(return_value=False)
    mock_use_case.executed_nodes = ["start"]

    mock_context = MagicMock()
    mock_context.variables = {"_job_id": "job-test-001"}
    mock_context.execution_path = ["start"]
    mock_context.errors = [("node1", "Test error occurred")]
    mock_use_case.context = mock_context

    return mock_use_case


# ============================================================================
# Heartbeat Service Fixtures
# ============================================================================


@pytest.fixture
def heartbeat_callback():
    """Provide a tracking callback for heartbeat tests."""
    calls: List[Dict[str, Any]] = []

    async def callback(data: Dict[str, Any]) -> None:
        calls.append(data)

    callback.calls = calls
    return callback


@pytest.fixture
def heartbeat_failure_callback():
    """Provide a tracking callback for heartbeat failure tests."""
    calls: List[Exception] = []

    def callback(error: Exception) -> None:
        calls.append(error)

    callback.calls = calls
    return callback


# ============================================================================
# Progress Callback Fixtures
# ============================================================================


@pytest.fixture
def progress_callback():
    """Provide a tracking callback for progress reporting tests."""
    calls: List[tuple] = []

    async def callback(job_id: str, progress: int, message: str) -> None:
        calls.append((job_id, progress, message))

    callback.calls = calls
    return callback


# ============================================================================
# Environment Variable Fixtures
# ============================================================================


@pytest.fixture
def env_config_vars(monkeypatch):
    """Set up environment variables for config loading tests."""
    env_vars = {
        "CASARE_ROBOT_NAME": "Env Robot",
        "CASARE_CONTROL_PLANE_URL": "wss://test.example.com/ws",
        "CASARE_ROBOT_ID": "robot-env-12345678",
        "CASARE_HEARTBEAT_INTERVAL": "60",
        "CASARE_MAX_CONCURRENT_JOBS": "3",
        "CASARE_CAPABILITIES": "browser,desktop,gpu",
        "CASARE_TAGS": "production,team-a",
        "CASARE_ENVIRONMENT": "production",
        "CASARE_LOG_LEVEL": "WARNING",
    }

    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    return env_vars


@pytest.fixture
def minimal_env_config_vars(monkeypatch):
    """Set up minimal environment variables for config loading tests."""
    env_vars = {
        "CASARE_ROBOT_NAME": "Minimal Env Robot",
        "CASARE_CONTROL_PLANE_URL": "ws://localhost:9090/ws",
    }

    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    return env_vars
