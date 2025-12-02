"""
Tests for ApiKeyRepository.

Tests cover:
- Happy path: CRUD operations, listing, searching
- Sad path: Not found cases, database errors
- Edge cases: Null values, IP address handling, count queries
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from casare_rpa.infrastructure.persistence.repositories.api_key_repository import (
    ApiKeyRepository,
)
from casare_rpa.infrastructure.auth.robot_api_keys import (
    RobotApiKey,
    generate_api_key_raw,
    hash_api_key,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_raw_key() -> str:
    """Generate sample raw API key."""
    return generate_api_key_raw()


@pytest.fixture
def sample_key_hash(sample_raw_key: str) -> str:
    """Generate sample key hash."""
    return hash_api_key(sample_raw_key)


@pytest.fixture
def sample_api_key_record(sample_key_hash: str) -> Dict[str, Any]:
    """Create sample API key database record."""
    return {
        "id": "key-uuid-12345678",
        "robot_id": "robot-uuid-12345678",
        "api_key_hash": sample_key_hash,
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
def sample_api_key_record_with_ip(sample_key_hash: str) -> Dict[str, Any]:
    """Create sample API key record with IP address."""
    return {
        "id": "key-uuid-12345678",
        "robot_id": "robot-uuid-12345678",
        "api_key_hash": sample_key_hash,
        "name": "Test API Key",
        "description": "API key for testing",
        "created_at": datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        "expires_at": None,
        "last_used_at": datetime(2024, 1, 20, 15, 30, 0, tzinfo=timezone.utc),
        "last_used_ip": "192.168.1.100",
        "is_revoked": False,
        "revoked_at": None,
        "revoked_by": None,
        "revoke_reason": None,
        "created_by": "test-user",
    }


@pytest.fixture
def sample_revoked_record(sample_key_hash: str) -> Dict[str, Any]:
    """Create sample revoked API key record."""
    return {
        "id": "key-revoked-12345678",
        "robot_id": "robot-uuid-12345678",
        "api_key_hash": sample_key_hash,
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


@pytest.fixture
def sample_expired_record(sample_key_hash: str) -> Dict[str, Any]:
    """Create sample expired API key record."""
    return {
        "id": "key-expired-12345678",
        "robot_id": "robot-uuid-12345678",
        "api_key_hash": sample_key_hash,
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


# ============================================================================
# Save Tests
# ============================================================================


class TestApiKeyRepositorySave:
    """Test save operation."""

    @pytest.mark.asyncio
    async def test_save_creates_new_key(
        self, mock_pool_manager, mock_connection, sample_key_hash: str
    ):
        """Save creates new API key record."""
        # Configure mock
        new_record = {
            "id": "new-key-uuid",
            "robot_id": "robot-123",
            "api_key_hash": sample_key_hash,
            "name": "New Key",
            "description": "Test description",
            "created_at": datetime.now(timezone.utc),
            "expires_at": None,
            "last_used_at": None,
            "last_used_ip": None,
            "is_revoked": False,
            "revoked_at": None,
            "revoked_by": None,
            "revoke_reason": None,
            "created_by": "test-user",
        }
        mock_connection.fetchrow.return_value = new_record

        repo = ApiKeyRepository(mock_pool_manager)

        result = await repo.save(
            robot_id="robot-123",
            api_key_hash=sample_key_hash,
            name="New Key",
            description="Test description",
            created_by="test-user",
        )

        assert result.id == "new-key-uuid"
        assert result.robot_id == "robot-123"
        assert result.name == "New Key"
        mock_connection.fetchrow.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_with_expiration(
        self, mock_pool_manager, mock_connection, sample_key_hash: str
    ):
        """Save with expiration date."""
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        new_record = {
            "id": "expiring-key-uuid",
            "robot_id": "robot-123",
            "api_key_hash": sample_key_hash,
            "name": "Expiring Key",
            "description": None,
            "created_at": datetime.now(timezone.utc),
            "expires_at": expires_at,
            "last_used_at": None,
            "last_used_ip": None,
            "is_revoked": False,
            "revoked_at": None,
            "revoked_by": None,
            "revoke_reason": None,
            "created_by": "test-user",
        }
        mock_connection.fetchrow.return_value = new_record

        repo = ApiKeyRepository(mock_pool_manager)

        result = await repo.save(
            robot_id="robot-123",
            api_key_hash=sample_key_hash,
            name="Expiring Key",
            expires_at=expires_at,
            created_by="test-user",
        )

        assert result.expires_at == expires_at

    @pytest.mark.asyncio
    async def test_save_database_error_raises(
        self, mock_pool_manager, mock_connection, sample_key_hash: str
    ):
        """Database error during save raises exception."""
        mock_connection.fetchrow.side_effect = Exception("Database connection failed")

        repo = ApiKeyRepository(mock_pool_manager)

        with pytest.raises(Exception, match="Database connection failed"):
            await repo.save(
                robot_id="robot-123",
                api_key_hash=sample_key_hash,
                name="Failed Key",
            )


# ============================================================================
# Get By ID Tests
# ============================================================================


class TestApiKeyRepositoryGetById:
    """Test get_by_id operation."""

    @pytest.mark.asyncio
    async def test_get_by_id_found(
        self, mock_pool_manager, mock_connection, sample_api_key_record: Dict[str, Any]
    ):
        """Get by ID returns key when found."""
        mock_connection.fetchrow.return_value = sample_api_key_record

        repo = ApiKeyRepository(mock_pool_manager)

        result = await repo.get_by_id("key-uuid-12345678")

        assert result is not None
        assert result.id == "key-uuid-12345678"
        assert result.robot_id == "robot-uuid-12345678"
        assert result.name == "Test API Key"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, mock_pool_manager, mock_connection):
        """Get by ID returns None when not found."""
        mock_connection.fetchrow.return_value = None

        repo = ApiKeyRepository(mock_pool_manager)

        result = await repo.get_by_id("nonexistent-key")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_database_error_raises(
        self, mock_pool_manager, mock_connection
    ):
        """Database error during get_by_id raises exception."""
        mock_connection.fetchrow.side_effect = Exception("Query failed")

        repo = ApiKeyRepository(mock_pool_manager)

        with pytest.raises(Exception, match="Query failed"):
            await repo.get_by_id("key-123")


# ============================================================================
# Get By Hash Tests
# ============================================================================


class TestApiKeyRepositoryGetByHash:
    """Test get_by_hash operation."""

    @pytest.mark.asyncio
    async def test_get_by_hash_found(
        self,
        mock_pool_manager,
        mock_connection,
        sample_api_key_record: Dict[str, Any],
        sample_key_hash: str,
    ):
        """Get by hash returns key when found."""
        mock_connection.fetchrow.return_value = sample_api_key_record

        repo = ApiKeyRepository(mock_pool_manager)

        result = await repo.get_by_hash(sample_key_hash)

        assert result is not None
        assert result.api_key_hash == sample_key_hash

    @pytest.mark.asyncio
    async def test_get_by_hash_not_found(
        self, mock_pool_manager, mock_connection, sample_key_hash: str
    ):
        """Get by hash returns None when not found."""
        mock_connection.fetchrow.return_value = None

        repo = ApiKeyRepository(mock_pool_manager)

        result = await repo.get_by_hash(sample_key_hash)

        assert result is None


# ============================================================================
# Get Valid By Hash Tests
# ============================================================================


class TestApiKeyRepositoryGetValidByHash:
    """Test get_valid_by_hash operation."""

    @pytest.mark.asyncio
    async def test_get_valid_by_hash_returns_active_key(
        self,
        mock_pool_manager,
        mock_connection,
        sample_api_key_record: Dict[str, Any],
        sample_key_hash: str,
    ):
        """Get valid by hash returns active key."""
        mock_connection.fetchrow.return_value = sample_api_key_record

        repo = ApiKeyRepository(mock_pool_manager)

        result = await repo.get_valid_by_hash(sample_key_hash)

        assert result is not None
        assert result.is_revoked is False

    @pytest.mark.asyncio
    async def test_get_valid_by_hash_excludes_revoked(
        self, mock_pool_manager, mock_connection, sample_key_hash: str
    ):
        """Get valid by hash excludes revoked keys (database handles this)."""
        # Simulate database returning None for revoked key
        mock_connection.fetchrow.return_value = None

        repo = ApiKeyRepository(mock_pool_manager)

        result = await repo.get_valid_by_hash(sample_key_hash)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_valid_by_hash_excludes_expired(
        self, mock_pool_manager, mock_connection, sample_key_hash: str
    ):
        """Get valid by hash excludes expired keys (database handles this)."""
        # Simulate database returning None for expired key
        mock_connection.fetchrow.return_value = None

        repo = ApiKeyRepository(mock_pool_manager)

        result = await repo.get_valid_by_hash(sample_key_hash)

        assert result is None


# ============================================================================
# List For Robot Tests
# ============================================================================


class TestApiKeyRepositoryListForRobot:
    """Test list_for_robot operation."""

    @pytest.mark.asyncio
    async def test_list_for_robot_returns_keys(
        self,
        mock_pool_manager,
        mock_connection,
        sample_api_key_record: Dict[str, Any],
    ):
        """List for robot returns all active keys."""
        mock_connection.fetch.return_value = [sample_api_key_record]

        repo = ApiKeyRepository(mock_pool_manager)

        result = await repo.list_for_robot("robot-uuid-12345678")

        assert len(result) == 1
        assert result[0].id == "key-uuid-12345678"

    @pytest.mark.asyncio
    async def test_list_for_robot_excludes_revoked_by_default(
        self,
        mock_pool_manager,
        mock_connection,
        sample_api_key_record: Dict[str, Any],
    ):
        """List excludes revoked keys by default."""
        mock_connection.fetch.return_value = [sample_api_key_record]

        repo = ApiKeyRepository(mock_pool_manager)

        await repo.list_for_robot("robot-uuid-12345678", include_revoked=False)

        # Verify the query includes is_revoked = FALSE condition
        call_args = mock_connection.fetch.call_args
        query = call_args[0][0]
        assert "is_revoked = FALSE" in query

    @pytest.mark.asyncio
    async def test_list_for_robot_includes_revoked_when_requested(
        self,
        mock_pool_manager,
        mock_connection,
        sample_api_key_record: Dict[str, Any],
        sample_revoked_record: Dict[str, Any],
    ):
        """List includes revoked keys when requested."""
        mock_connection.fetch.return_value = [
            sample_api_key_record,
            sample_revoked_record,
        ]

        repo = ApiKeyRepository(mock_pool_manager)

        result = await repo.list_for_robot("robot-uuid-12345678", include_revoked=True)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_list_for_robot_empty(self, mock_pool_manager, mock_connection):
        """List returns empty list when no keys exist."""
        mock_connection.fetch.return_value = []

        repo = ApiKeyRepository(mock_pool_manager)

        result = await repo.list_for_robot("robot-with-no-keys")

        assert result == []


# ============================================================================
# List All Tests
# ============================================================================


class TestApiKeyRepositoryListAll:
    """Test list_all operation."""

    @pytest.mark.asyncio
    async def test_list_all_with_pagination(
        self,
        mock_pool_manager,
        mock_connection,
        sample_api_key_record: Dict[str, Any],
    ):
        """List all supports pagination."""
        mock_connection.fetch.return_value = [sample_api_key_record]

        repo = ApiKeyRepository(mock_pool_manager)

        result = await repo.list_all(limit=10, offset=0)

        assert len(result) == 1
        # Verify query includes LIMIT and OFFSET
        call_args = mock_connection.fetch.call_args
        query = call_args[0][0]
        assert "LIMIT" in query
        assert "OFFSET" in query

    @pytest.mark.asyncio
    async def test_list_all_excludes_revoked_by_default(
        self, mock_pool_manager, mock_connection
    ):
        """List all excludes revoked keys by default."""
        mock_connection.fetch.return_value = []

        repo = ApiKeyRepository(mock_pool_manager)

        await repo.list_all(include_revoked=False)

        call_args = mock_connection.fetch.call_args
        query = call_args[0][0]
        assert "is_revoked = FALSE" in query


# ============================================================================
# Update Last Used Tests
# ============================================================================


class TestApiKeyRepositoryUpdateLastUsed:
    """Test update_last_used operation."""

    @pytest.mark.asyncio
    async def test_update_last_used_without_ip(
        self, mock_pool_manager, mock_connection, sample_key_hash: str
    ):
        """Update last_used_at without IP address."""
        mock_connection.execute.return_value = "UPDATE 1"

        repo = ApiKeyRepository(mock_pool_manager)

        await repo.update_last_used(sample_key_hash)

        mock_connection.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_last_used_with_ip(
        self, mock_pool_manager, mock_connection, sample_key_hash: str
    ):
        """Update last_used_at with IP address."""
        mock_connection.execute.return_value = "UPDATE 1"

        repo = ApiKeyRepository(mock_pool_manager)

        await repo.update_last_used(sample_key_hash, client_ip="192.168.1.100")

        mock_connection.execute.assert_called_once()
        # Verify IP was passed to query
        call_args = mock_connection.execute.call_args
        assert "192.168.1.100" in call_args[0]


# ============================================================================
# Revoke Tests
# ============================================================================


class TestApiKeyRepositoryRevoke:
    """Test revoke operation."""

    @pytest.mark.asyncio
    async def test_revoke_success(self, mock_pool_manager, mock_connection):
        """Revoke returns True on success."""
        mock_connection.execute.return_value = "UPDATE 1"

        repo = ApiKeyRepository(mock_pool_manager)

        result = await repo.revoke(
            key_id="key-uuid-12345678",
            revoked_by="admin",
            reason="Security policy",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_revoke_not_found(self, mock_pool_manager, mock_connection):
        """Revoke returns False when key not found."""
        mock_connection.execute.return_value = "UPDATE 0"

        repo = ApiKeyRepository(mock_pool_manager)

        result = await repo.revoke(key_id="nonexistent-key")

        assert result is False

    @pytest.mark.asyncio
    async def test_revoke_already_revoked(self, mock_pool_manager, mock_connection):
        """Revoke returns False for already revoked key."""
        # Query includes is_revoked = FALSE, so already revoked returns 0
        mock_connection.execute.return_value = "UPDATE 0"

        repo = ApiKeyRepository(mock_pool_manager)

        result = await repo.revoke(key_id="already-revoked-key")

        assert result is False


# ============================================================================
# Revoke All For Robot Tests
# ============================================================================


class TestApiKeyRepositoryRevokeAllForRobot:
    """Test revoke_all_for_robot operation."""

    @pytest.mark.asyncio
    async def test_revoke_all_for_robot_success(
        self, mock_pool_manager, mock_connection
    ):
        """Revoke all returns count of revoked keys."""
        mock_connection.execute.return_value = "UPDATE 3"

        repo = ApiKeyRepository(mock_pool_manager)

        result = await repo.revoke_all_for_robot(
            robot_id="robot-uuid-12345678",
            revoked_by="admin",
            reason="Robot decommissioned",
        )

        assert result == 3

    @pytest.mark.asyncio
    async def test_revoke_all_for_robot_no_keys(
        self, mock_pool_manager, mock_connection
    ):
        """Revoke all returns 0 when no active keys exist."""
        mock_connection.execute.return_value = "UPDATE 0"

        repo = ApiKeyRepository(mock_pool_manager)

        result = await repo.revoke_all_for_robot(robot_id="robot-with-no-keys")

        assert result == 0


# ============================================================================
# Delete Tests
# ============================================================================


class TestApiKeyRepositoryDelete:
    """Test delete operation."""

    @pytest.mark.asyncio
    async def test_delete_success(self, mock_pool_manager, mock_connection):
        """Delete returns True on success."""
        mock_connection.execute.return_value = "DELETE 1"

        repo = ApiKeyRepository(mock_pool_manager)

        result = await repo.delete("key-uuid-12345678")

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_not_found(self, mock_pool_manager, mock_connection):
        """Delete returns False when key not found."""
        mock_connection.execute.return_value = "DELETE 0"

        repo = ApiKeyRepository(mock_pool_manager)

        result = await repo.delete("nonexistent-key")

        assert result is False


# ============================================================================
# Delete Expired Tests
# ============================================================================


class TestApiKeyRepositoryDeleteExpired:
    """Test delete_expired operation."""

    @pytest.mark.asyncio
    async def test_delete_expired_success(self, mock_pool_manager, mock_connection):
        """Delete expired returns count of deleted keys."""
        mock_connection.execute.return_value = "DELETE 5"

        repo = ApiKeyRepository(mock_pool_manager)

        result = await repo.delete_expired(days_old=30)

        assert result == 5

    @pytest.mark.asyncio
    async def test_delete_expired_none(self, mock_pool_manager, mock_connection):
        """Delete expired returns 0 when no expired keys exist."""
        mock_connection.execute.return_value = "DELETE 0"

        repo = ApiKeyRepository(mock_pool_manager)

        result = await repo.delete_expired(days_old=30)

        assert result == 0


# ============================================================================
# Count For Robot Tests
# ============================================================================


class TestApiKeyRepositoryCountForRobot:
    """Test count_for_robot operation."""

    @pytest.mark.asyncio
    async def test_count_for_robot_active_only(
        self, mock_pool_manager, mock_connection
    ):
        """Count returns active key count."""
        mock_connection.fetchval.return_value = 3

        repo = ApiKeyRepository(mock_pool_manager)

        result = await repo.count_for_robot("robot-uuid-12345678", active_only=True)

        assert result == 3
        # Verify query includes is_revoked = FALSE
        call_args = mock_connection.fetchval.call_args
        query = call_args[0][0]
        assert "is_revoked = FALSE" in query

    @pytest.mark.asyncio
    async def test_count_for_robot_all(self, mock_pool_manager, mock_connection):
        """Count returns total key count including revoked."""
        mock_connection.fetchval.return_value = 5

        repo = ApiKeyRepository(mock_pool_manager)

        result = await repo.count_for_robot("robot-uuid-12345678", active_only=False)

        assert result == 5


# ============================================================================
# Get Robot ID By Hash Tests
# ============================================================================


class TestApiKeyRepositoryGetRobotIdByHash:
    """Test get_robot_id_by_hash operation."""

    @pytest.mark.asyncio
    async def test_get_robot_id_by_hash_found(
        self, mock_pool_manager, mock_connection, sample_key_hash: str
    ):
        """Get robot ID returns ID when key is valid."""
        mock_connection.fetchval.return_value = "robot-uuid-12345678"

        repo = ApiKeyRepository(mock_pool_manager)

        result = await repo.get_robot_id_by_hash(sample_key_hash)

        assert result == "robot-uuid-12345678"

    @pytest.mark.asyncio
    async def test_get_robot_id_by_hash_not_found(
        self, mock_pool_manager, mock_connection, sample_key_hash: str
    ):
        """Get robot ID returns None for invalid key."""
        mock_connection.fetchval.return_value = None

        repo = ApiKeyRepository(mock_pool_manager)

        result = await repo.get_robot_id_by_hash(sample_key_hash)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_robot_id_by_hash_excludes_invalid(
        self, mock_pool_manager, mock_connection, sample_key_hash: str
    ):
        """Get robot ID query excludes revoked and expired keys."""
        mock_connection.fetchval.return_value = None

        repo = ApiKeyRepository(mock_pool_manager)

        await repo.get_robot_id_by_hash(sample_key_hash)

        # Verify query includes validity checks
        call_args = mock_connection.fetchval.call_args
        query = call_args[0][0]
        assert "is_revoked = FALSE" in query
        assert "expires_at" in query


# ============================================================================
# Row to API Key Conversion Tests
# ============================================================================


class TestApiKeyRepositoryRowConversion:
    """Test row to RobotApiKey conversion."""

    @pytest.mark.asyncio
    async def test_row_with_ip_address(
        self,
        mock_pool_manager,
        mock_connection,
        sample_api_key_record_with_ip: Dict[str, Any],
    ):
        """Row with IP address is converted correctly."""
        mock_connection.fetchrow.return_value = sample_api_key_record_with_ip

        repo = ApiKeyRepository(mock_pool_manager)

        result = await repo.get_by_id("key-uuid-12345678")

        assert result.last_used_ip == "192.168.1.100"
        assert result.last_used_at is not None

    @pytest.mark.asyncio
    async def test_row_with_null_optional_fields(
        self, mock_pool_manager, mock_connection
    ):
        """Row with null optional fields is converted correctly."""
        record = {
            "id": "key-uuid-12345678",
            "robot_id": "robot-uuid-12345678",
            "api_key_hash": "somehash",
            "name": None,
            "description": None,
            "created_at": datetime.now(timezone.utc),
            "expires_at": None,
            "last_used_at": None,
            "last_used_ip": None,
            "is_revoked": False,
            "revoked_at": None,
            "revoked_by": None,
            "revoke_reason": None,
            "created_by": None,
        }
        mock_connection.fetchrow.return_value = record

        repo = ApiKeyRepository(mock_pool_manager)

        result = await repo.get_by_id("key-uuid-12345678")

        assert result is not None
        assert result.name is None
        assert result.description is None
        assert result.last_used_ip is None


# ============================================================================
# Connection Management Tests
# ============================================================================


class TestApiKeyRepositoryConnectionManagement:
    """Test database connection management."""

    @pytest.mark.asyncio
    async def test_connection_released_after_operation(
        self,
        mock_pool_manager,
        mock_pool,
        mock_connection,
        sample_api_key_record: Dict[str, Any],
    ):
        """Connection is released after successful operation."""
        mock_connection.fetchrow.return_value = sample_api_key_record

        repo = ApiKeyRepository(mock_pool_manager)

        await repo.get_by_id("key-uuid-12345678")

        mock_pool.release.assert_called_once_with(mock_connection)

    @pytest.mark.asyncio
    async def test_connection_released_after_error(
        self, mock_pool_manager, mock_pool, mock_connection
    ):
        """Connection is released after error."""
        mock_connection.fetchrow.side_effect = Exception("Database error")

        repo = ApiKeyRepository(mock_pool_manager)

        with pytest.raises(Exception):
            await repo.get_by_id("key-uuid-12345678")

        mock_pool.release.assert_called_once_with(mock_connection)

    @pytest.mark.asyncio
    async def test_get_pool_called_on_operation(
        self, mock_pool_manager, mock_connection, sample_api_key_record: Dict[str, Any]
    ):
        """Pool is retrieved on each operation."""
        mock_connection.fetchrow.return_value = sample_api_key_record

        repo = ApiKeyRepository(mock_pool_manager)

        await repo.get_by_id("key-uuid-12345678")

        mock_pool_manager.get_pool.assert_called_once_with(
            "casare_rpa", db_type="postgresql"
        )


# ============================================================================
# Edge Cases
# ============================================================================


class TestApiKeyRepositoryEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_save_with_all_fields_none(
        self, mock_pool_manager, mock_connection, sample_key_hash: str
    ):
        """Save with all optional fields None."""
        record = {
            "id": "minimal-key-uuid",
            "robot_id": "robot-123",
            "api_key_hash": sample_key_hash,
            "name": None,
            "description": None,
            "created_at": datetime.now(timezone.utc),
            "expires_at": None,
            "last_used_at": None,
            "last_used_ip": None,
            "is_revoked": False,
            "revoked_at": None,
            "revoked_by": None,
            "revoke_reason": None,
            "created_by": None,
        }
        mock_connection.fetchrow.return_value = record

        repo = ApiKeyRepository(mock_pool_manager)

        result = await repo.save(
            robot_id="robot-123",
            api_key_hash=sample_key_hash,
        )

        assert result.id == "minimal-key-uuid"
        assert result.name is None

    @pytest.mark.asyncio
    async def test_list_with_large_offset(self, mock_pool_manager, mock_connection):
        """List with large offset returns empty list."""
        mock_connection.fetch.return_value = []

        repo = ApiKeyRepository(mock_pool_manager)

        result = await repo.list_all(limit=10, offset=10000)

        assert result == []

    @pytest.mark.asyncio
    async def test_count_returns_zero(self, mock_pool_manager, mock_connection):
        """Count returns zero for robot with no keys."""
        mock_connection.fetchval.return_value = 0

        repo = ApiKeyRepository(mock_pool_manager)

        result = await repo.count_for_robot("robot-with-no-keys")

        assert result == 0
