"""
Integration Test Fixtures for CasareRPA Robot Orchestration.

Provides shared fixtures for integration testing across:
- Orchestrator components
- PgQueuer distributed queue
- Robot Agent
- DBOS Executor
- Coordination/Load Balancing

These fixtures enable comprehensive testing of the complete robot
orchestration system without requiring actual PostgreSQL or Supabase.
"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from casare_rpa.domain.events import EventBus, get_event_bus


# =============================================================================
# EVENT BUS FIXTURES
# =============================================================================


@pytest.fixture
def event_bus() -> EventBus:
    """Provide a real event bus for integration testing."""
    return get_event_bus()


@pytest.fixture
def isolated_event_bus() -> EventBus:
    """Provide an isolated event bus (not the global singleton)."""
    return EventBus()


# =============================================================================
# SAMPLE WORKFLOW FIXTURES
# =============================================================================


@pytest.fixture
def sample_workflow_json() -> str:
    """Provide sample workflow JSON for testing."""
    return """
    {
        "metadata": {
            "name": "Integration Test Workflow",
            "version": "1.0.0",
            "description": "Workflow for integration testing"
        },
        "nodes": [
            {
                "id": "start-node",
                "type": "StartNode",
                "position": {"x": 100, "y": 100},
                "properties": {}
            },
            {
                "id": "set-var-node",
                "type": "SetVariableNode",
                "position": {"x": 200, "y": 100},
                "properties": {
                    "variable_name": "test_output",
                    "value": "executed"
                }
            },
            {
                "id": "log-node",
                "type": "LogNode",
                "position": {"x": 300, "y": 100},
                "properties": {
                    "message": "Test workflow executed"
                }
            },
            {
                "id": "end-node",
                "type": "EndNode",
                "position": {"x": 400, "y": 100},
                "properties": {}
            }
        ],
        "connections": [
            {"from_node": "start-node", "from_port": "output", "to_node": "set-var-node", "to_port": "input"},
            {"from_node": "set-var-node", "from_port": "output", "to_node": "log-node", "to_port": "input"},
            {"from_node": "log-node", "from_port": "output", "to_node": "end-node", "to_port": "input"}
        ]
    }
    """


@pytest.fixture
def minimal_workflow_json() -> str:
    """Provide minimal workflow JSON for quick tests."""
    return '{"metadata": {"name": "Minimal"}, "nodes": [], "connections": []}'


@pytest.fixture
def failing_workflow_json() -> str:
    """Provide workflow JSON that should fail during execution."""
    return """
    {
        "metadata": {"name": "Failing Workflow"},
        "nodes": [
            {"id": "start", "type": "StartNode", "properties": {}},
            {"id": "error", "type": "ErrorNode", "properties": {"error_message": "Intentional failure"}},
            {"id": "end", "type": "EndNode", "properties": {}}
        ],
        "connections": [
            {"from_node": "start", "from_port": "output", "to_node": "error", "to_port": "input"},
            {"from_node": "error", "from_port": "output", "to_node": "end", "to_port": "input"}
        ]
    }
    """


# =============================================================================
# MOCK DATABASE FIXTURES
# =============================================================================


@pytest.fixture
def mock_postgres_pool() -> AsyncMock:
    """Provide mock asyncpg connection pool."""
    pool = AsyncMock()
    pool.acquire.return_value.__aenter__ = AsyncMock(return_value=AsyncMock())
    pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
    pool.close = AsyncMock()
    return pool


@pytest.fixture
def mock_supabase_client() -> MagicMock:
    """Provide mock Supabase client."""
    client = MagicMock()
    client.table.return_value.select.return_value.execute = AsyncMock(
        return_value=MagicMock(data=[])
    )
    client.table.return_value.insert.return_value.execute = AsyncMock(
        return_value=MagicMock(data=[])
    )
    client.table.return_value.update.return_value.eq.return_value.execute = AsyncMock(
        return_value=MagicMock(data=[])
    )
    return client


# =============================================================================
# REALTIME MOCK FIXTURES
# =============================================================================


class MockRealtimeChannel:
    """Mock Supabase Realtime channel."""

    def __init__(self, name: str):
        self.name = name
        self._subscribed = False
        self._handlers: Dict[str, List] = {}

    def on(self, event_type: str, handler) -> "MockRealtimeChannel":
        """Subscribe to an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        return self

    def subscribe(self) -> "MockRealtimeChannel":
        """Subscribe to the channel."""
        self._subscribed = True
        return self

    def unsubscribe(self) -> None:
        """Unsubscribe from the channel."""
        self._subscribed = False

    def trigger(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Trigger handlers for testing."""
        for handler in self._handlers.get(event_type, []):
            handler(payload)


class MockRealtimeClient:
    """Mock Supabase Realtime client."""

    def __init__(self):
        self._channels: Dict[str, MockRealtimeChannel] = {}
        self._connected = False

    def channel(self, name: str) -> MockRealtimeChannel:
        """Get or create a channel."""
        if name not in self._channels:
            self._channels[name] = MockRealtimeChannel(name)
        return self._channels[name]

    def connect(self) -> None:
        """Connect to realtime."""
        self._connected = True

    def disconnect(self) -> None:
        """Disconnect from realtime."""
        self._connected = False

    def trigger_job_notification(self, job_id: str) -> None:
        """Trigger a job notification for testing."""
        channel = self._channels.get("job_queue")
        if channel:
            channel.trigger("INSERT", {"record": {"id": job_id}})


@pytest.fixture
def mock_realtime_client() -> MockRealtimeClient:
    """Provide mock Supabase Realtime client."""
    return MockRealtimeClient()


# =============================================================================
# HELPER FIXTURES
# =============================================================================


@pytest.fixture
def generate_job_id():
    """Factory for generating unique job IDs."""
    counter = 0

    def _generate(prefix: str = "job") -> str:
        nonlocal counter
        counter += 1
        return f"{prefix}-{counter:04d}-{uuid.uuid4().hex[:8]}"

    return _generate


@pytest.fixture
def generate_workflow_id():
    """Factory for generating unique workflow IDs."""
    counter = 0

    def _generate(prefix: str = "workflow") -> str:
        nonlocal counter
        counter += 1
        return f"{prefix}-{counter:04d}"

    return _generate


@pytest.fixture
def generate_robot_id():
    """Factory for generating unique robot IDs."""
    counter = 0

    def _generate(prefix: str = "robot") -> str:
        nonlocal counter
        counter += 1
        return f"{prefix}-{counter:03d}"

    return _generate


# =============================================================================
# TIMING HELPERS
# =============================================================================


@pytest.fixture
def async_timeout():
    """Provide async timeout helper."""

    async def _timeout(coro, timeout_seconds: float = 5.0):
        """Execute coroutine with timeout."""
        try:
            return await asyncio.wait_for(coro, timeout=timeout_seconds)
        except asyncio.TimeoutError:
            pytest.fail(f"Operation timed out after {timeout_seconds}s")

    return _timeout


@pytest.fixture
def wait_until():
    """Provide polling wait helper."""

    async def _wait_until(
        condition,
        timeout_seconds: float = 5.0,
        poll_interval: float = 0.1,
        message: str = "Condition not met",
    ) -> None:
        """Wait until condition is true or timeout."""
        start = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start < timeout_seconds:
            if condition():
                return
            await asyncio.sleep(poll_interval)
        pytest.fail(f"{message} (timeout after {timeout_seconds}s)")

    return _wait_until


# =============================================================================
# PYTEST CONFIGURATION
# =============================================================================


def pytest_configure(config):
    """Configure pytest markers for integration tests."""
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running (may take >1s)")
    config.addinivalue_line(
        "markers", "requires_postgres: mark test as requiring PostgreSQL"
    )
    config.addinivalue_line(
        "markers", "requires_supabase: mark test as requiring Supabase"
    )


# Configure pytest-asyncio to use function scope by default
@pytest.fixture(scope="function")
def event_loop():
    """Create event loop for each test function."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
