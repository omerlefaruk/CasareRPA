"""
Tests for TenantRepository infrastructure layer.

Tests the PostgreSQL persistence for Tenant entities using asyncpg.
All database operations are mocked - no real database required.
"""

import pytest
from unittest.mock import AsyncMock, Mock, MagicMock, patch
from datetime import datetime, timezone
from typing import Dict, Any

import orjson

from casare_rpa.domain.entities.tenant import Tenant, TenantId, TenantSettings
from casare_rpa.infrastructure.persistence.repositories.tenant_repository import (
    TenantRepository,
)


@pytest.fixture
def mock_pool_manager() -> AsyncMock:
    """Create mock database pool manager."""
    manager = AsyncMock()
    pool = AsyncMock()
    manager.get_pool.return_value = pool
    return manager


@pytest.fixture
def mock_connection() -> AsyncMock:
    """Create mock database connection."""
    conn = AsyncMock()
    return conn


@pytest.fixture
def sample_tenant_row() -> Dict[str, Any]:
    """Sample database row for a tenant."""
    return {
        "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Test Tenant",
        "description": "A test tenant",
        "settings": orjson.dumps(
            {
                "max_robots": 10,
                "max_concurrent_jobs": 20,
                "allowed_capabilities": ["browser"],
                "max_api_keys_per_robot": 5,
                "job_retention_days": 30,
                "enable_audit_logging": True,
                "custom_settings": {},
            }
        ).decode(),
        "admin_emails": orjson.dumps(["admin@test.com"]).decode(),
        "contact_email": "contact@test.com",
        "robot_ids": orjson.dumps(["robot-1", "robot-2"]).decode(),
        "is_active": True,
        "created_at": datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2024, 1, 15, 0, 0, 0, tzinfo=timezone.utc),
    }


@pytest.fixture
def sample_tenant() -> Tenant:
    """Sample Tenant entity for testing."""
    return Tenant(
        id=TenantId("550e8400-e29b-41d4-a716-446655440000"),
        name="Test Tenant",
        description="A test tenant",
        settings=TenantSettings(
            max_robots=10,
            allowed_capabilities=["browser"],
        ),
        admin_emails=["admin@test.com"],
        contact_email="contact@test.com",
        robot_ids={"robot-1", "robot-2"},
        is_active=True,
    )


class TestTenantRepositoryRowConversion:
    """Tests for row-to-entity and entity-to-params conversion."""

    def test_row_to_tenant_converts_correctly(
        self, mock_pool_manager: AsyncMock, sample_tenant_row: Dict[str, Any]
    ) -> None:
        """_row_to_tenant creates valid Tenant entity."""
        repo = TenantRepository(pool_manager=mock_pool_manager)

        tenant = repo._row_to_tenant(sample_tenant_row)

        assert str(tenant.id) == "550e8400-e29b-41d4-a716-446655440000"
        assert tenant.name == "Test Tenant"
        assert tenant.description == "A test tenant"
        assert tenant.settings.max_robots == 10
        assert tenant.settings.allowed_capabilities == ["browser"]
        assert tenant.admin_emails == ["admin@test.com"]
        assert tenant.contact_email == "contact@test.com"
        assert tenant.robot_ids == {"robot-1", "robot-2"}
        assert tenant.is_active is True

    def test_row_to_tenant_handles_dict_settings(
        self, mock_pool_manager: AsyncMock
    ) -> None:
        """_row_to_tenant handles settings as dict (already parsed)."""
        repo = TenantRepository(pool_manager=mock_pool_manager)
        row = {
            "tenant_id": "t1",
            "name": "Test",
            "description": "",
            "settings": {"max_robots": 15},  # Dict, not JSON string
            "admin_emails": [],
            "robot_ids": [],
            "is_active": True,
        }

        tenant = repo._row_to_tenant(row)

        assert tenant.settings.max_robots == 15

    def test_row_to_tenant_handles_empty_robot_ids(
        self, mock_pool_manager: AsyncMock
    ) -> None:
        """_row_to_tenant handles empty robot_ids."""
        repo = TenantRepository(pool_manager=mock_pool_manager)
        row = {
            "tenant_id": "t1",
            "name": "Test",
            "description": "",
            "settings": {},
            "admin_emails": [],
            "robot_ids": [],
            "is_active": True,
        }

        tenant = repo._row_to_tenant(row)

        assert tenant.robot_ids == set()

    def test_tenant_to_params_converts_correctly(
        self, mock_pool_manager: AsyncMock, sample_tenant: Tenant
    ) -> None:
        """_tenant_to_params creates valid database parameters."""
        repo = TenantRepository(pool_manager=mock_pool_manager)

        params = repo._tenant_to_params(sample_tenant)

        assert params["tenant_id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert params["name"] == "Test Tenant"
        assert params["description"] == "A test tenant"
        assert params["contact_email"] == "contact@test.com"
        assert params["is_active"] is True

        # Settings should be JSON string
        settings = orjson.loads(params["settings"])
        assert settings["max_robots"] == 10

        # Admin emails should be JSON string
        admin_emails = orjson.loads(params["admin_emails"])
        assert admin_emails == ["admin@test.com"]

        # Robot IDs should be JSON string (list, not set)
        robot_ids = orjson.loads(params["robot_ids"])
        assert set(robot_ids) == {"robot-1", "robot-2"}


class TestTenantRepositorySave:
    """Tests for save() method."""

    @pytest.mark.asyncio
    async def test_save_executes_upsert_query(
        self,
        mock_pool_manager: AsyncMock,
        mock_connection: AsyncMock,
        sample_tenant: Tenant,
    ) -> None:
        """save() executes INSERT ... ON CONFLICT query."""
        mock_pool_manager.get_pool.return_value.acquire.return_value = mock_connection
        repo = TenantRepository(pool_manager=mock_pool_manager)

        await repo.save(sample_tenant)

        mock_connection.execute.assert_awaited_once()
        call_args = mock_connection.execute.call_args
        query = call_args[0][0]
        assert "INSERT INTO tenants" in query
        assert "ON CONFLICT (tenant_id) DO UPDATE" in query

    @pytest.mark.asyncio
    async def test_save_returns_tenant(
        self,
        mock_pool_manager: AsyncMock,
        mock_connection: AsyncMock,
        sample_tenant: Tenant,
    ) -> None:
        """save() returns the saved tenant."""
        mock_pool_manager.get_pool.return_value.acquire.return_value = mock_connection
        repo = TenantRepository(pool_manager=mock_pool_manager)

        result = await repo.save(sample_tenant)

        assert result is sample_tenant

    @pytest.mark.asyncio
    async def test_save_releases_connection(
        self,
        mock_pool_manager: AsyncMock,
        mock_connection: AsyncMock,
        sample_tenant: Tenant,
    ) -> None:
        """save() releases connection after operation."""
        pool = mock_pool_manager.get_pool.return_value
        pool.acquire.return_value = mock_connection
        repo = TenantRepository(pool_manager=mock_pool_manager)

        await repo.save(sample_tenant)

        pool.release.assert_awaited_once_with(mock_connection)

    @pytest.mark.asyncio
    async def test_save_releases_connection_on_error(
        self,
        mock_pool_manager: AsyncMock,
        mock_connection: AsyncMock,
        sample_tenant: Tenant,
    ) -> None:
        """save() releases connection even on error."""
        pool = mock_pool_manager.get_pool.return_value
        pool.acquire.return_value = mock_connection
        mock_connection.execute.side_effect = Exception("DB error")
        repo = TenantRepository(pool_manager=mock_pool_manager)

        with pytest.raises(Exception):
            await repo.save(sample_tenant)

        pool.release.assert_awaited_once_with(mock_connection)


def create_mock_row(data: Dict[str, Any]):
    """Create a mock asyncpg Record that converts to dict properly."""

    class MockRecord:
        def __init__(self, d: Dict[str, Any]):
            self._data = d

        def __iter__(self):
            return iter(self._data.items())

        def keys(self):
            return self._data.keys()

        def get(self, key, default=None):
            return self._data.get(key, default)

        def __getitem__(self, key):
            return self._data[key]

        def items(self):
            return self._data.items()

    return MockRecord(data)


class TestTenantRepositoryGetById:
    """Tests for get_by_id() method."""

    @pytest.mark.asyncio
    async def test_get_by_id_returns_tenant(
        self,
        mock_pool_manager: AsyncMock,
        mock_connection: AsyncMock,
        sample_tenant_row: Dict[str, Any],
    ) -> None:
        """get_by_id() returns Tenant when found."""
        mock_pool_manager.get_pool.return_value.acquire.return_value = mock_connection
        mock_connection.fetchrow.return_value = create_mock_row(sample_tenant_row)
        repo = TenantRepository(pool_manager=mock_pool_manager)

        result = await repo.get_by_id("550e8400-e29b-41d4-a716-446655440000")

        assert result is not None
        assert str(result.id) == "550e8400-e29b-41d4-a716-446655440000"
        assert result.name == "Test Tenant"

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_found(
        self,
        mock_pool_manager: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """get_by_id() returns None when tenant not found."""
        mock_pool_manager.get_pool.return_value.acquire.return_value = mock_connection
        mock_connection.fetchrow.return_value = None
        repo = TenantRepository(pool_manager=mock_pool_manager)

        result = await repo.get_by_id("nonexistent-id")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_queries_correct_column(
        self,
        mock_pool_manager: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """get_by_id() queries by tenant_id column."""
        mock_pool_manager.get_pool.return_value.acquire.return_value = mock_connection
        mock_connection.fetchrow.return_value = None
        repo = TenantRepository(pool_manager=mock_pool_manager)

        await repo.get_by_id("test-id")

        mock_connection.fetchrow.assert_awaited_once()
        call_args = mock_connection.fetchrow.call_args
        query = call_args[0][0]
        assert "tenant_id = $1" in query
        assert call_args[0][1] == "test-id"


class TestTenantRepositoryGetByName:
    """Tests for get_by_name() method."""

    @pytest.mark.asyncio
    async def test_get_by_name_returns_tenant(
        self,
        mock_pool_manager: AsyncMock,
        mock_connection: AsyncMock,
        sample_tenant_row: Dict[str, Any],
    ) -> None:
        """get_by_name() returns Tenant when found."""
        mock_pool_manager.get_pool.return_value.acquire.return_value = mock_connection
        mock_connection.fetchrow.return_value = create_mock_row(sample_tenant_row)
        repo = TenantRepository(pool_manager=mock_pool_manager)

        result = await repo.get_by_name("Test Tenant")

        assert result is not None
        assert result.name == "Test Tenant"

    @pytest.mark.asyncio
    async def test_get_by_name_queries_name_column(
        self,
        mock_pool_manager: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """get_by_name() queries by name column."""
        mock_pool_manager.get_pool.return_value.acquire.return_value = mock_connection
        mock_connection.fetchrow.return_value = None
        repo = TenantRepository(pool_manager=mock_pool_manager)

        await repo.get_by_name("Test Tenant")

        call_args = mock_connection.fetchrow.call_args
        query = call_args[0][0]
        assert "name = $1" in query
        assert call_args[0][1] == "Test Tenant"


class TestTenantRepositoryGetAll:
    """Tests for get_all() method."""

    @pytest.mark.asyncio
    async def test_get_all_returns_tenant_list(
        self,
        mock_pool_manager: AsyncMock,
        mock_connection: AsyncMock,
        sample_tenant_row: Dict[str, Any],
    ) -> None:
        """get_all() returns list of Tenants."""
        mock_pool_manager.get_pool.return_value.acquire.return_value = mock_connection
        mock_row = create_mock_row(sample_tenant_row)
        mock_connection.fetch.return_value = [mock_row]
        repo = TenantRepository(pool_manager=mock_pool_manager)

        result = await repo.get_all()

        assert len(result) == 1
        assert result[0].name == "Test Tenant"

    @pytest.mark.asyncio
    async def test_get_all_filters_inactive_by_default(
        self,
        mock_pool_manager: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """get_all() filters out inactive tenants by default."""
        mock_pool_manager.get_pool.return_value.acquire.return_value = mock_connection
        mock_connection.fetch.return_value = []
        repo = TenantRepository(pool_manager=mock_pool_manager)

        await repo.get_all()

        call_args = mock_connection.fetch.call_args
        query = call_args[0][0]
        assert "is_active = TRUE" in query

    @pytest.mark.asyncio
    async def test_get_all_includes_inactive_when_requested(
        self,
        mock_pool_manager: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """get_all(include_inactive=True) includes inactive tenants."""
        mock_pool_manager.get_pool.return_value.acquire.return_value = mock_connection
        mock_connection.fetch.return_value = []
        repo = TenantRepository(pool_manager=mock_pool_manager)

        await repo.get_all(include_inactive=True)

        call_args = mock_connection.fetch.call_args
        query = call_args[0][0]
        assert "is_active = TRUE" not in query

    @pytest.mark.asyncio
    async def test_get_all_respects_limit_and_offset(
        self,
        mock_pool_manager: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """get_all() uses limit and offset parameters."""
        mock_pool_manager.get_pool.return_value.acquire.return_value = mock_connection
        mock_connection.fetch.return_value = []
        repo = TenantRepository(pool_manager=mock_pool_manager)

        await repo.get_all(limit=50, offset=100)

        call_args = mock_connection.fetch.call_args
        # Limit and offset are positional args after query
        assert call_args[0][1] == 50  # limit
        assert call_args[0][2] == 100  # offset


class TestTenantRepositoryGetByAdminEmail:
    """Tests for get_by_admin_email() method."""

    @pytest.mark.asyncio
    async def test_get_by_admin_email_returns_tenants(
        self,
        mock_pool_manager: AsyncMock,
        mock_connection: AsyncMock,
        sample_tenant_row: Dict[str, Any],
    ) -> None:
        """get_by_admin_email() returns tenants where user is admin."""
        mock_pool_manager.get_pool.return_value.acquire.return_value = mock_connection
        mock_row = create_mock_row(sample_tenant_row)
        mock_connection.fetch.return_value = [mock_row]
        repo = TenantRepository(pool_manager=mock_pool_manager)

        result = await repo.get_by_admin_email("admin@test.com")

        assert len(result) == 1
        assert result[0].name == "Test Tenant"

    @pytest.mark.asyncio
    async def test_get_by_admin_email_normalizes_email(
        self,
        mock_pool_manager: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """get_by_admin_email() normalizes email to lowercase."""
        mock_pool_manager.get_pool.return_value.acquire.return_value = mock_connection
        mock_connection.fetch.return_value = []
        repo = TenantRepository(pool_manager=mock_pool_manager)

        await repo.get_by_admin_email("ADMIN@Test.COM")

        call_args = mock_connection.fetch.call_args
        # The JSON should contain lowercase email
        json_param = call_args[0][1]
        assert "admin@test.com" in json_param.lower()

    @pytest.mark.asyncio
    async def test_get_by_admin_email_uses_jsonb_contains(
        self,
        mock_pool_manager: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """get_by_admin_email() uses JSONB @> operator."""
        mock_pool_manager.get_pool.return_value.acquire.return_value = mock_connection
        mock_connection.fetch.return_value = []
        repo = TenantRepository(pool_manager=mock_pool_manager)

        await repo.get_by_admin_email("admin@test.com")

        call_args = mock_connection.fetch.call_args
        query = call_args[0][0]
        assert "admin_emails @>" in query


class TestTenantRepositoryGetByRobotId:
    """Tests for get_by_robot_id() method."""

    @pytest.mark.asyncio
    async def test_get_by_robot_id_returns_tenant(
        self,
        mock_pool_manager: AsyncMock,
        mock_connection: AsyncMock,
        sample_tenant_row: Dict[str, Any],
    ) -> None:
        """get_by_robot_id() returns tenant owning the robot."""
        mock_pool_manager.get_pool.return_value.acquire.return_value = mock_connection
        mock_connection.fetchrow.return_value = create_mock_row(sample_tenant_row)
        repo = TenantRepository(pool_manager=mock_pool_manager)

        result = await repo.get_by_robot_id("robot-1")

        assert result is not None
        assert "robot-1" in result.robot_ids

    @pytest.mark.asyncio
    async def test_get_by_robot_id_returns_none_when_not_found(
        self,
        mock_pool_manager: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """get_by_robot_id() returns None when robot not in any tenant."""
        mock_pool_manager.get_pool.return_value.acquire.return_value = mock_connection
        mock_connection.fetchrow.return_value = None
        repo = TenantRepository(pool_manager=mock_pool_manager)

        result = await repo.get_by_robot_id("unknown-robot")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_robot_id_uses_jsonb_contains(
        self,
        mock_pool_manager: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """get_by_robot_id() uses JSONB @> operator."""
        mock_pool_manager.get_pool.return_value.acquire.return_value = mock_connection
        mock_connection.fetchrow.return_value = None
        repo = TenantRepository(pool_manager=mock_pool_manager)

        await repo.get_by_robot_id("robot-123")

        call_args = mock_connection.fetchrow.call_args
        query = call_args[0][0]
        assert "robot_ids @>" in query


class TestTenantRepositoryRobotOperations:
    """Tests for add_robot_to_tenant() and remove_robot_from_tenant()."""

    @pytest.mark.asyncio
    async def test_add_robot_to_tenant_success(
        self,
        mock_pool_manager: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """add_robot_to_tenant() returns True on success."""
        mock_pool_manager.get_pool.return_value.acquire.return_value = mock_connection
        mock_connection.execute.return_value = "UPDATE 1"
        repo = TenantRepository(pool_manager=mock_pool_manager)

        result = await repo.add_robot_to_tenant("tenant-1", "robot-new")

        assert result is True

    @pytest.mark.asyncio
    async def test_add_robot_to_tenant_not_found(
        self,
        mock_pool_manager: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """add_robot_to_tenant() returns False when tenant not found."""
        mock_pool_manager.get_pool.return_value.acquire.return_value = mock_connection
        mock_connection.execute.return_value = "UPDATE 0"
        repo = TenantRepository(pool_manager=mock_pool_manager)

        result = await repo.add_robot_to_tenant("nonexistent", "robot-1")

        assert result is False

    @pytest.mark.asyncio
    async def test_add_robot_uses_jsonb_concat(
        self,
        mock_pool_manager: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """add_robot_to_tenant() uses JSONB || operator."""
        mock_pool_manager.get_pool.return_value.acquire.return_value = mock_connection
        mock_connection.execute.return_value = "UPDATE 1"
        repo = TenantRepository(pool_manager=mock_pool_manager)

        await repo.add_robot_to_tenant("tenant-1", "robot-new")

        call_args = mock_connection.execute.call_args
        query = call_args[0][0]
        assert "robot_ids = robot_ids ||" in query
        # Should check NOT already contains
        assert "NOT robot_ids @>" in query

    @pytest.mark.asyncio
    async def test_remove_robot_from_tenant_success(
        self,
        mock_pool_manager: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """remove_robot_from_tenant() returns True on success."""
        mock_pool_manager.get_pool.return_value.acquire.return_value = mock_connection
        mock_connection.execute.return_value = "UPDATE 1"
        repo = TenantRepository(pool_manager=mock_pool_manager)

        result = await repo.remove_robot_from_tenant("tenant-1", "robot-1")

        assert result is True

    @pytest.mark.asyncio
    async def test_remove_robot_uses_jsonb_subtract(
        self,
        mock_pool_manager: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """remove_robot_from_tenant() uses JSONB - operator."""
        mock_pool_manager.get_pool.return_value.acquire.return_value = mock_connection
        mock_connection.execute.return_value = "UPDATE 1"
        repo = TenantRepository(pool_manager=mock_pool_manager)

        await repo.remove_robot_from_tenant("tenant-1", "robot-1")

        call_args = mock_connection.execute.call_args
        query = call_args[0][0]
        assert "robot_ids = robot_ids -" in query


class TestTenantRepositoryDelete:
    """Tests for delete() method."""

    @pytest.mark.asyncio
    async def test_delete_soft_delete_by_default(
        self,
        mock_pool_manager: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """delete() performs soft delete by default."""
        mock_pool_manager.get_pool.return_value.acquire.return_value = mock_connection
        mock_connection.execute.return_value = "UPDATE 1"
        repo = TenantRepository(pool_manager=mock_pool_manager)

        result = await repo.delete("tenant-1")

        assert result is True
        call_args = mock_connection.execute.call_args
        query = call_args[0][0]
        assert "UPDATE tenants" in query
        assert "is_active = FALSE" in query

    @pytest.mark.asyncio
    async def test_delete_hard_delete_when_requested(
        self,
        mock_pool_manager: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """delete(hard_delete=True) permanently deletes."""
        mock_pool_manager.get_pool.return_value.acquire.return_value = mock_connection
        mock_connection.execute.return_value = "DELETE 1"
        repo = TenantRepository(pool_manager=mock_pool_manager)

        result = await repo.delete("tenant-1", hard_delete=True)

        assert result is True
        call_args = mock_connection.execute.call_args
        query = call_args[0][0]
        assert "DELETE FROM tenants" in query

    @pytest.mark.asyncio
    async def test_delete_returns_false_when_not_found(
        self,
        mock_pool_manager: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """delete() returns False when tenant not found."""
        mock_pool_manager.get_pool.return_value.acquire.return_value = mock_connection
        mock_connection.execute.return_value = "UPDATE 0"
        repo = TenantRepository(pool_manager=mock_pool_manager)

        result = await repo.delete("nonexistent")

        assert result is False


class TestTenantRepositoryCount:
    """Tests for count() method."""

    @pytest.mark.asyncio
    async def test_count_returns_active_count_by_default(
        self,
        mock_pool_manager: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """count() returns active tenant count by default."""
        mock_pool_manager.get_pool.return_value.acquire.return_value = mock_connection
        mock_connection.fetchrow.return_value = {"count": 5}
        repo = TenantRepository(pool_manager=mock_pool_manager)

        result = await repo.count()

        assert result == 5
        call_args = mock_connection.fetchrow.call_args
        query = call_args[0][0]
        assert "is_active = TRUE" in query

    @pytest.mark.asyncio
    async def test_count_includes_inactive_when_requested(
        self,
        mock_pool_manager: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """count(include_inactive=True) includes all tenants."""
        mock_pool_manager.get_pool.return_value.acquire.return_value = mock_connection
        mock_connection.fetchrow.return_value = {"count": 10}
        repo = TenantRepository(pool_manager=mock_pool_manager)

        result = await repo.count(include_inactive=True)

        assert result == 10
        call_args = mock_connection.fetchrow.call_args
        query = call_args[0][0]
        assert "is_active" not in query

    @pytest.mark.asyncio
    async def test_count_returns_zero_when_no_result(
        self,
        mock_pool_manager: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """count() returns 0 when no row returned."""
        mock_pool_manager.get_pool.return_value.acquire.return_value = mock_connection
        mock_connection.fetchrow.return_value = None
        repo = TenantRepository(pool_manager=mock_pool_manager)

        result = await repo.count()

        assert result == 0


class TestTenantRepositoryStatistics:
    """Tests for get_statistics() method."""

    @pytest.mark.asyncio
    async def test_get_statistics_returns_all_metrics(
        self,
        mock_pool_manager: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """get_statistics() returns complete statistics."""
        mock_pool_manager.get_pool.return_value.acquire.return_value = mock_connection
        mock_connection.fetchrow.return_value = {
            "total_tenants": 10,
            "active_tenants": 8,
            "inactive_tenants": 2,
            "total_robots": 25,
            "avg_robots_per_tenant": 2.5,
        }
        repo = TenantRepository(pool_manager=mock_pool_manager)

        result = await repo.get_statistics()

        assert result["total_tenants"] == 10
        assert result["active_tenants"] == 8
        assert result["inactive_tenants"] == 2
        assert result["total_robots"] == 25
        assert result["avg_robots_per_tenant"] == 2.5


class TestTenantRepositoryErrorHandling:
    """Tests for error handling in repository operations."""

    @pytest.mark.asyncio
    async def test_save_propagates_database_error(
        self,
        mock_pool_manager: AsyncMock,
        mock_connection: AsyncMock,
        sample_tenant: Tenant,
    ) -> None:
        """save() propagates database errors."""
        mock_pool_manager.get_pool.return_value.acquire.return_value = mock_connection
        mock_connection.execute.side_effect = Exception("Connection lost")
        repo = TenantRepository(pool_manager=mock_pool_manager)

        with pytest.raises(Exception, match="Connection lost"):
            await repo.save(sample_tenant)

    @pytest.mark.asyncio
    async def test_get_by_id_propagates_database_error(
        self,
        mock_pool_manager: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """get_by_id() propagates database errors."""
        mock_pool_manager.get_pool.return_value.acquire.return_value = mock_connection
        mock_connection.fetchrow.side_effect = Exception("Query timeout")
        repo = TenantRepository(pool_manager=mock_pool_manager)

        with pytest.raises(Exception, match="Query timeout"):
            await repo.get_by_id("test-id")

    @pytest.mark.asyncio
    async def test_connection_released_on_fetchrow_error(
        self,
        mock_pool_manager: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """Connection is released even when fetchrow fails."""
        pool = mock_pool_manager.get_pool.return_value
        pool.acquire.return_value = mock_connection
        mock_connection.fetchrow.side_effect = Exception("DB Error")
        repo = TenantRepository(pool_manager=mock_pool_manager)

        with pytest.raises(Exception):
            await repo.get_by_id("test-id")

        pool.release.assert_awaited_once_with(mock_connection)

    @pytest.mark.asyncio
    async def test_connection_released_on_fetch_error(
        self,
        mock_pool_manager: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """Connection is released even when fetch fails."""
        pool = mock_pool_manager.get_pool.return_value
        pool.acquire.return_value = mock_connection
        mock_connection.fetch.side_effect = Exception("DB Error")
        repo = TenantRepository(pool_manager=mock_pool_manager)

        with pytest.raises(Exception):
            await repo.get_all()

        pool.release.assert_awaited_once_with(mock_connection)
