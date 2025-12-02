"""
Shared fixtures for PostgreSQL repository tests.

Provides AsyncMock patterns for asyncpg connection pools and connections
to test repository implementations without actual database access.
"""

from datetime import datetime
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock
import pytest


class MockAsyncpgRecord(dict):
    """Mock asyncpg Record that behaves like both dict and has __getitem__ access."""

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'MockAsyncpgRecord' has no attribute '{name}'")


def create_mock_record(data: Dict[str, Any]) -> MockAsyncpgRecord:
    """Create a mock asyncpg Record from a dictionary."""
    return MockAsyncpgRecord(data)


@pytest.fixture
def mock_pool():
    """
    Create a mock asyncpg connection pool.

    Returns:
        AsyncMock configured to return mock connections.
    """
    pool = AsyncMock()
    return pool


class MockAsyncContextManager:
    """Mock async context manager for transactions."""

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None


@pytest.fixture
def mock_connection():
    """
    Create a mock asyncpg connection with common methods.

    The connection provides:
    - fetchrow: Returns single row or None
    - fetch: Returns list of rows
    - execute: Returns command tag string
    - transaction: Async context manager for transactions

    Returns:
        AsyncMock configured for database operations.
    """
    conn = AsyncMock()

    # Default behaviors - tests can override
    conn.fetchrow.return_value = None
    conn.fetch.return_value = []
    conn.execute.return_value = "DELETE 0"

    # Transaction context manager - asyncpg's transaction() returns a sync object
    # that is an async context manager (not a coroutine)
    conn.transaction = Mock(return_value=MockAsyncContextManager())

    return conn


@pytest.fixture
def mock_pool_manager(mock_pool, mock_connection):
    """
    Create a mock DatabasePoolManager.

    Wires together pool and connection mocks so that:
    - get_pool() returns mock_pool
    - pool.acquire() returns mock_connection
    - pool.release() is a no-op

    Args:
        mock_pool: Pool fixture
        mock_connection: Connection fixture

    Returns:
        AsyncMock configured as DatabasePoolManager.
    """
    manager = AsyncMock()
    manager.get_pool.return_value = mock_pool
    mock_pool.acquire.return_value = mock_connection
    mock_pool.release = AsyncMock()
    return manager


@pytest.fixture
def sample_robot_row() -> MockAsyncpgRecord:
    """Create sample robot database row."""
    return create_mock_record(
        {
            "robot_id": "robot-uuid-1234",
            "name": "Test Robot",
            "hostname": "test-host",
            "status": "online",
            "environment": "production",
            "max_concurrent_jobs": 3,
            "last_seen": datetime(2024, 1, 15, 10, 30, 0),
            "last_heartbeat": datetime(2024, 1, 15, 10, 29, 55),
            "created_at": datetime(2024, 1, 1, 0, 0, 0),
            "capabilities": '["browser", "desktop"]',
            "tags": '["tag1", "tag2"]',
            "metrics": '{"cpu": 45, "memory": 60}',
            "assigned_workflows": '["wf-1", "wf-2"]',
            "current_job_ids": '["job-1"]',
        }
    )


@pytest.fixture
def sample_job_row() -> MockAsyncpgRecord:
    """Create sample job database row."""
    return create_mock_record(
        {
            "job_id": "job-uuid-1234",
            "workflow_id": "wf-uuid-5678",
            "workflow_name": "Test Workflow",
            "robot_uuid": "robot-uuid-1234",
            "robot_name": "Test Robot",
            "status": "pending",
            "priority": 1,
            "environment": "production",
            "payload": '{"nodes": []}',
            "scheduled_time": None,
            "started_at": None,
            "completed_at": None,
            "duration_ms": 0,
            "progress": 0,
            "current_node": "",
            "result": "{}",
            "logs": "",
            "error_message": "",
            "created_at": datetime(2024, 1, 15, 10, 0, 0),
            "created_by": "test-user",
        }
    )


@pytest.fixture
def sample_assignment_row() -> MockAsyncpgRecord:
    """Create sample workflow assignment database row."""
    return create_mock_record(
        {
            "workflow_id": "wf-uuid-5678",
            "robot_id": "robot-uuid-1234",
            "is_default": True,
            "priority": 10,
            "created_at": datetime(2024, 1, 10, 8, 0, 0),
            "created_by": "admin",
            "notes": "Primary assignment for production workflow",
        }
    )


@pytest.fixture
def sample_override_row() -> MockAsyncpgRecord:
    """Create sample node override database row."""
    return create_mock_record(
        {
            "workflow_id": "wf-uuid-5678",
            "node_id": "node-gpu-processing",
            "robot_id": "robot-gpu-1234",
            "required_capabilities": '["gpu", "high_memory"]',
            "reason": "Node requires GPU for ML inference",
            "created_at": datetime(2024, 1, 12, 14, 0, 0),
            "created_by": "ml-team",
            "is_active": True,
        }
    )
