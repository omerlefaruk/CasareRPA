"""
Shared fixtures for Robot API Key authentication tests.

Provides mocks for:
- Database clients (Supabase, asyncpg)
- API key generation and validation
- Sample API key records
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from casare_rpa.infrastructure.auth.robot_api_keys import (
    API_KEY_PREFIX,
    RobotApiKey,
    generate_api_key_raw,
    hash_api_key,
)


# ============================================================================
# API Key Fixtures
# ============================================================================


@pytest.fixture
def sample_raw_api_key() -> str:
    """Generate a sample raw API key for testing."""
    return generate_api_key_raw()


@pytest.fixture
def sample_api_key_hash(sample_raw_api_key: str) -> str:
    """Generate hash for sample API key."""
    return hash_api_key(sample_raw_api_key)


@pytest.fixture
def sample_robot_api_key(sample_api_key_hash: str) -> RobotApiKey:
    """Create sample RobotApiKey record."""
    return RobotApiKey(
        id="key-uuid-12345678",
        robot_id="robot-uuid-12345678",
        api_key_hash=sample_api_key_hash,
        name="Test API Key",
        description="API key for testing",
        created_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        expires_at=None,
        last_used_at=None,
        last_used_ip=None,
        is_revoked=False,
        revoked_at=None,
        revoked_by=None,
        revoke_reason=None,
        created_by="test-user",
    )


@pytest.fixture
def sample_expired_api_key(sample_api_key_hash: str) -> RobotApiKey:
    """Create expired RobotApiKey record."""
    return RobotApiKey(
        id="key-expired-12345678",
        robot_id="robot-uuid-12345678",
        api_key_hash=sample_api_key_hash,
        name="Expired API Key",
        description="Expired key for testing",
        created_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        expires_at=datetime(2024, 1, 10, 0, 0, 0, tzinfo=timezone.utc),  # Past date
        is_revoked=False,
        created_by="test-user",
    )


@pytest.fixture
def sample_revoked_api_key(sample_api_key_hash: str) -> RobotApiKey:
    """Create revoked RobotApiKey record."""
    return RobotApiKey(
        id="key-revoked-12345678",
        robot_id="robot-uuid-12345678",
        api_key_hash=sample_api_key_hash,
        name="Revoked API Key",
        description="Revoked key for testing",
        created_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        expires_at=None,
        is_revoked=True,
        revoked_at=datetime(2024, 1, 14, 12, 0, 0, tzinfo=timezone.utc),
        revoked_by="admin-user",
        revoke_reason="Security incident",
        created_by="test-user",
    )


@pytest.fixture
def sample_key_with_future_expiry(sample_api_key_hash: str) -> RobotApiKey:
    """Create RobotApiKey with future expiration."""
    future_date = datetime.now(timezone.utc) + timedelta(days=30)
    return RobotApiKey(
        id="key-future-12345678",
        robot_id="robot-uuid-12345678",
        api_key_hash=sample_api_key_hash,
        name="Future Expiry Key",
        description="Key with future expiration",
        created_at=datetime.now(timezone.utc),
        expires_at=future_date,
        is_revoked=False,
        created_by="test-user",
    )


# ============================================================================
# Mock Database Client Fixtures
# ============================================================================


@pytest.fixture
def mock_supabase_client() -> Mock:
    """Create mock Supabase client with chainable methods."""
    client = MagicMock()

    # Create a mock table that supports method chaining
    mock_table = MagicMock()

    # All methods return the table itself for chaining
    mock_table.insert.return_value = mock_table
    mock_table.select.return_value = mock_table
    mock_table.update.return_value = mock_table
    mock_table.delete.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.order.return_value = mock_table

    # execute() returns a response with data
    mock_response = Mock()
    mock_response.data = []
    mock_table.execute.return_value = mock_response

    client.table.return_value = mock_table

    return client


class MockAsyncpgPoolContextManager:
    """Async context manager for mock pool.acquire()."""

    def __init__(self, connection):
        self._connection = connection

    async def __aenter__(self):
        return self._connection

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class MockAsyncpgPool:
    """Mock asyncpg connection pool."""

    def __init__(self):
        self._connection = None

    def acquire(self):
        """Return async context manager for connection."""
        return MockAsyncpgPoolContextManager(self._connection)

    async def release(self, conn):
        """Release connection (no-op)."""
        pass

    def set_connection(self, conn: "MockAsyncpgConnection") -> None:
        """Set the mock connection to use."""
        self._connection = conn


class MockAsyncpgConnection:
    """Mock asyncpg connection."""

    def __init__(self):
        self._fetchrow_result: Dict[str, Any] = {}
        self._fetch_result: List[Dict[str, Any]] = []
        self._fetchval_result: Any = None
        self._execute_result: str = "UPDATE 1"

    async def fetchrow(self, query: str, *args) -> Dict[str, Any]:
        """Return mock row."""
        return self._fetchrow_result

    async def fetch(self, query: str, *args) -> List[Dict[str, Any]]:
        """Return mock rows."""
        return self._fetch_result

    async def fetchval(self, query: str, *args) -> Any:
        """Return mock scalar value."""
        return self._fetchval_result

    async def execute(self, query: str, *args) -> str:
        """Return mock command tag."""
        return self._execute_result

    def set_fetchrow_result(self, data: Dict[str, Any]) -> None:
        """Set result for fetchrow."""
        self._fetchrow_result = data

    def set_fetch_result(self, data: List[Dict[str, Any]]) -> None:
        """Set result for fetch."""
        self._fetch_result = data

    def set_execute_result(self, result: str) -> None:
        """Set result for execute."""
        self._execute_result = result


@pytest.fixture
def mock_asyncpg_connection() -> MockAsyncpgConnection:
    """Create mock asyncpg connection."""
    return MockAsyncpgConnection()


@pytest.fixture
def mock_asyncpg_pool(
    mock_asyncpg_connection: MockAsyncpgConnection,
) -> MockAsyncpgPool:
    """Create mock asyncpg pool."""
    pool = MockAsyncpgPool()
    pool.set_connection(mock_asyncpg_connection)
    return pool


# ============================================================================
# Database Row Fixtures
# ============================================================================


@pytest.fixture
def sample_api_key_row(sample_api_key_hash: str) -> Dict[str, Any]:
    """Create sample API key database row."""
    return {
        "id": "key-uuid-12345678",
        "robot_id": "robot-uuid-12345678",
        "api_key_hash": sample_api_key_hash,
        "name": "Test API Key",
        "description": "API key for testing",
        "created_at": datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        "expires_at": None,
        "last_used_at": None,
        "last_used_ip": None,
        "is_revoked": False,
        "revoked_at": None,
        "revoked_by": None,
        "revoke_reason": None,
        "created_by": "test-user",
    }


@pytest.fixture
def sample_api_key_row_expired(sample_api_key_hash: str) -> Dict[str, Any]:
    """Create expired API key database row."""
    return {
        "id": "key-expired-12345678",
        "robot_id": "robot-uuid-12345678",
        "api_key_hash": sample_api_key_hash,
        "name": "Expired API Key",
        "description": "Expired key",
        "created_at": datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "expires_at": datetime(2024, 1, 10, 0, 0, 0, tzinfo=timezone.utc),
        "last_used_at": None,
        "last_used_ip": None,
        "is_revoked": False,
        "revoked_at": None,
        "revoked_by": None,
        "revoke_reason": None,
        "created_by": "test-user",
    }


@pytest.fixture
def sample_api_key_row_revoked(sample_api_key_hash: str) -> Dict[str, Any]:
    """Create revoked API key database row."""
    return {
        "id": "key-revoked-12345678",
        "robot_id": "robot-uuid-12345678",
        "api_key_hash": sample_api_key_hash,
        "name": "Revoked API Key",
        "description": "Revoked key",
        "created_at": datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "expires_at": None,
        "last_used_at": None,
        "last_used_ip": None,
        "is_revoked": True,
        "revoked_at": datetime(2024, 1, 14, 12, 0, 0, tzinfo=timezone.utc),
        "revoked_by": "admin-user",
        "revoke_reason": "Security incident",
        "created_by": "test-user",
    }
