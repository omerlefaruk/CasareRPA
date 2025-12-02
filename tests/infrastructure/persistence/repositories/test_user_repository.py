"""
Tests for UserRepository PostgreSQL implementation.

Tests cover:
- CRUD operations (create_user, get_by_id, get_by_email, update_password)
- Authentication (validate_credentials, password hashing/verification)
- Account security (failed login tracking, account locking)
- Role and tenant membership retrieval
- Error handling (connection failures, not found)

All database operations are mocked using AsyncMock.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from casare_rpa.infrastructure.persistence.repositories.user_repository import (
    UserRepository,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_pool() -> AsyncMock:
    """Create mock connection pool."""
    pool = AsyncMock()
    pool.acquire = AsyncMock()
    pool.release = AsyncMock()
    return pool


@pytest.fixture
def mock_connection() -> AsyncMock:
    """Create mock database connection."""
    conn = AsyncMock()
    conn.fetchrow = AsyncMock()
    conn.fetch = AsyncMock()
    conn.fetchval = AsyncMock()
    conn.execute = AsyncMock()
    return conn


@pytest.fixture
def mock_pool_with_connection(
    mock_pool: AsyncMock, mock_connection: AsyncMock
) -> AsyncMock:
    """Configure pool to return connection."""
    mock_pool.acquire.return_value = mock_connection
    return mock_pool


@pytest.fixture
def sample_user_row() -> Dict[str, Any]:
    """Sample database row for a user."""
    return {
        "id": "user-uuid-12345678",
        "email": "test@example.com",
        "username": "testuser",
        "password_hash": "$2b$12$hashhashhashhashhashhashhashhashhashhashhash",
        "full_name": "Test User",
        "avatar_url": "https://example.com/avatar.png",
        "status": "active",
        "email_verified": True,
        "mfa_enabled": False,
        "timezone": "UTC",
        "locale": "en",
        "failed_login_count": 0,
        "locked_until": None,
        "created_at": datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        "last_login_at": datetime(2024, 1, 20, 15, 30, 0, tzinfo=timezone.utc),
    }


@pytest.fixture
def sample_role_row() -> Dict[str, Any]:
    """Sample tenant membership row with role."""
    return {
        "tenant_id": "tenant-uuid-12345678",
        "role_name": "admin",
    }


@pytest.fixture
def locked_user_row(sample_user_row: Dict[str, Any]) -> Dict[str, Any]:
    """Sample row for locked user account."""
    return {
        **sample_user_row,
        "failed_login_count": 5,
        "locked_until": datetime.now(timezone.utc) + timedelta(minutes=15),
    }


@pytest.fixture
def inactive_user_row(sample_user_row: Dict[str, Any]) -> Dict[str, Any]:
    """Sample row for inactive user."""
    return {
        **sample_user_row,
        "status": "inactive",
    }


# ============================================================================
# Password Hashing Tests
# ============================================================================


class TestUserRepositoryPasswordHashing:
    """Tests for password hashing functionality."""

    def test_hash_password_returns_bcrypt_hash(self) -> None:
        """hash_password returns bcrypt formatted hash."""
        repo = UserRepository()

        # Mock bcrypt if not available
        with patch(
            "casare_rpa.infrastructure.persistence.repositories.user_repository.BCRYPT_AVAILABLE",
            True,
        ):
            with patch(
                "casare_rpa.infrastructure.persistence.repositories.user_repository.bcrypt"
            ) as mock_bcrypt:
                mock_bcrypt.gensalt.return_value = b"$2b$12$testsalt"
                mock_bcrypt.hashpw.return_value = b"$2b$12$testhash"

                result = repo.hash_password("password123")

                assert result == "$2b$12$testhash"
                mock_bcrypt.hashpw.assert_called_once()

    def test_hash_password_raises_when_bcrypt_unavailable(self) -> None:
        """hash_password raises RuntimeError when bcrypt not installed."""
        with patch(
            "casare_rpa.infrastructure.persistence.repositories.user_repository.BCRYPT_AVAILABLE",
            False,
        ):
            repo = UserRepository()

            with pytest.raises(RuntimeError, match="bcrypt not installed"):
                repo.hash_password("password123")

    def test_verify_password_returns_true_for_match(self) -> None:
        """verify_password returns True for correct password."""
        with patch(
            "casare_rpa.infrastructure.persistence.repositories.user_repository.BCRYPT_AVAILABLE",
            True,
        ):
            with patch(
                "casare_rpa.infrastructure.persistence.repositories.user_repository.bcrypt"
            ) as mock_bcrypt:
                mock_bcrypt.checkpw.return_value = True

                result = UserRepository.verify_password("password123", "$2b$12$hash")

                assert result is True

    def test_verify_password_returns_false_for_mismatch(self) -> None:
        """verify_password returns False for incorrect password."""
        with patch(
            "casare_rpa.infrastructure.persistence.repositories.user_repository.BCRYPT_AVAILABLE",
            True,
        ):
            with patch(
                "casare_rpa.infrastructure.persistence.repositories.user_repository.bcrypt"
            ) as mock_bcrypt:
                mock_bcrypt.checkpw.return_value = False

                result = UserRepository.verify_password("wrongpass", "$2b$12$hash")

                assert result is False

    def test_verify_password_returns_false_on_exception(self) -> None:
        """verify_password returns False when bcrypt raises exception."""
        with patch(
            "casare_rpa.infrastructure.persistence.repositories.user_repository.BCRYPT_AVAILABLE",
            True,
        ):
            with patch(
                "casare_rpa.infrastructure.persistence.repositories.user_repository.bcrypt"
            ) as mock_bcrypt:
                mock_bcrypt.checkpw.side_effect = ValueError("Invalid hash")

                result = UserRepository.verify_password("password", "invalid_hash")

                assert result is False

    def test_verify_password_raises_when_bcrypt_unavailable(self) -> None:
        """verify_password raises RuntimeError when bcrypt not installed."""
        with patch(
            "casare_rpa.infrastructure.persistence.repositories.user_repository.BCRYPT_AVAILABLE",
            False,
        ):
            with pytest.raises(RuntimeError, match="bcrypt not installed"):
                UserRepository.verify_password("password", "hash")


# ============================================================================
# Validate Credentials Tests
# ============================================================================


class TestUserRepositoryValidateCredentials:
    """Tests for validate_credentials operation."""

    @pytest.mark.asyncio
    async def test_validate_credentials_success(
        self,
        mock_pool_with_connection: AsyncMock,
        mock_connection: AsyncMock,
        sample_user_row: Dict[str, Any],
        sample_role_row: Dict[str, Any],
    ) -> None:
        """Successful credential validation returns user info."""
        mock_connection.fetchrow.return_value = sample_user_row
        mock_connection.fetch.return_value = [sample_role_row]

        repo = UserRepository(pool=mock_pool_with_connection)

        with patch.object(repo, "verify_password", return_value=True):
            result = await repo.validate_credentials("testuser", "password123")

        assert result is not None
        assert result["user_id"] == "user-uuid-12345678"
        assert result["email"] == "test@example.com"
        assert result["username"] == "testuser"
        assert "admin" in result["roles"]
        assert result["tenant_id"] == "tenant-uuid-12345678"

    @pytest.mark.asyncio
    async def test_validate_credentials_user_not_found(
        self,
        mock_pool_with_connection: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """Validation returns None when user not found."""
        mock_connection.fetchrow.return_value = None

        repo = UserRepository(pool=mock_pool_with_connection)
        result = await repo.validate_credentials("nonexistent", "password")

        assert result is None

    @pytest.mark.asyncio
    async def test_validate_credentials_wrong_password(
        self,
        mock_pool_with_connection: AsyncMock,
        mock_connection: AsyncMock,
        sample_user_row: Dict[str, Any],
    ) -> None:
        """Validation returns None for wrong password."""
        mock_connection.fetchrow.return_value = sample_user_row

        repo = UserRepository(pool=mock_pool_with_connection)

        with patch.object(repo, "verify_password", return_value=False):
            result = await repo.validate_credentials("testuser", "wrongpass")

        assert result is None
        # Should record failed login
        mock_connection.execute.assert_called()

    @pytest.mark.asyncio
    async def test_validate_credentials_account_locked(
        self,
        mock_pool_with_connection: AsyncMock,
        mock_connection: AsyncMock,
        locked_user_row: Dict[str, Any],
    ) -> None:
        """Validation returns None for locked account."""
        mock_connection.fetchrow.return_value = locked_user_row

        repo = UserRepository(pool=mock_pool_with_connection)
        result = await repo.validate_credentials("testuser", "password123")

        assert result is None

    @pytest.mark.asyncio
    async def test_validate_credentials_no_password_hash(
        self,
        mock_pool_with_connection: AsyncMock,
        mock_connection: AsyncMock,
        sample_user_row: Dict[str, Any],
    ) -> None:
        """Validation returns None when user has no password set."""
        sample_user_row["password_hash"] = None
        mock_connection.fetchrow.return_value = sample_user_row

        repo = UserRepository(pool=mock_pool_with_connection)
        result = await repo.validate_credentials("testuser", "password123")

        assert result is None

    @pytest.mark.asyncio
    async def test_validate_credentials_records_successful_login(
        self,
        mock_pool_with_connection: AsyncMock,
        mock_connection: AsyncMock,
        sample_user_row: Dict[str, Any],
        sample_role_row: Dict[str, Any],
    ) -> None:
        """Successful validation clears failed login count."""
        mock_connection.fetchrow.return_value = sample_user_row
        mock_connection.fetch.return_value = [sample_role_row]

        repo = UserRepository(pool=mock_pool_with_connection)

        with patch.object(repo, "verify_password", return_value=True):
            await repo.validate_credentials("testuser", "password123")

        # Check successful login was recorded
        execute_calls = mock_connection.execute.call_args_list
        assert len(execute_calls) > 0
        success_call = execute_calls[-1]
        sql = success_call[0][0]
        assert "failed_login_count = 0" in sql

    @pytest.mark.asyncio
    async def test_validate_credentials_connection_released(
        self,
        mock_pool_with_connection: AsyncMock,
        mock_connection: AsyncMock,
        sample_user_row: Dict[str, Any],
    ) -> None:
        """Connection is released after validation."""
        mock_connection.fetchrow.return_value = sample_user_row

        repo = UserRepository(pool=mock_pool_with_connection)

        with patch.object(repo, "verify_password", return_value=False):
            await repo.validate_credentials("testuser", "wrongpass")

        mock_pool_with_connection.release.assert_awaited_once_with(mock_connection)

    @pytest.mark.asyncio
    async def test_validate_credentials_handles_database_error(
        self,
        mock_pool_with_connection: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """Validation handles database errors gracefully."""
        mock_connection.fetchrow.side_effect = Exception("Database error")

        repo = UserRepository(pool=mock_pool_with_connection)
        result = await repo.validate_credentials("testuser", "password123")

        assert result is None
        mock_pool_with_connection.release.assert_awaited_once_with(mock_connection)


# ============================================================================
# Get User Roles Tests
# ============================================================================


class TestUserRepositoryGetUserRoles:
    """Tests for _get_user_roles internal method."""

    @pytest.mark.asyncio
    async def test_get_user_roles_returns_roles_and_tenant(
        self,
        mock_connection: AsyncMock,
    ) -> None:
        """_get_user_roles returns roles list and tenant_id."""
        mock_connection.fetch.return_value = [
            {"tenant_id": "tenant-1", "role_name": "admin"},
            {"tenant_id": "tenant-1", "role_name": "editor"},
        ]

        repo = UserRepository()
        result = await repo._get_user_roles(mock_connection, "user-123")

        assert "admin" in result["roles"]
        assert "editor" in result["roles"]
        assert result["tenant_id"] == "tenant-1"

    @pytest.mark.asyncio
    async def test_get_user_roles_no_memberships_returns_defaults(
        self,
        mock_connection: AsyncMock,
    ) -> None:
        """_get_user_roles returns default viewer role when no memberships."""
        mock_connection.fetch.return_value = []

        repo = UserRepository()
        result = await repo._get_user_roles(mock_connection, "user-123")

        assert result["roles"] == ["viewer"]
        assert result["tenant_id"] is None

    @pytest.mark.asyncio
    async def test_get_user_roles_deduplicates_roles(
        self,
        mock_connection: AsyncMock,
    ) -> None:
        """_get_user_roles returns unique roles only."""
        mock_connection.fetch.return_value = [
            {"tenant_id": "tenant-1", "role_name": "admin"},
            {
                "tenant_id": "tenant-2",
                "role_name": "admin",
            },  # Same role, different tenant
            {"tenant_id": "tenant-1", "role_name": "editor"},
        ]

        repo = UserRepository()
        result = await repo._get_user_roles(mock_connection, "user-123")

        # Should have 2 unique roles
        assert len(result["roles"]) == 2
        assert "admin" in result["roles"]
        assert "editor" in result["roles"]


# ============================================================================
# Get By ID Tests
# ============================================================================


class TestUserRepositoryGetById:
    """Tests for get_by_id operation."""

    @pytest.mark.asyncio
    async def test_get_by_id_returns_user(
        self,
        mock_pool_with_connection: AsyncMock,
        mock_connection: AsyncMock,
        sample_user_row: Dict[str, Any],
        sample_role_row: Dict[str, Any],
    ) -> None:
        """get_by_id returns user dict when found."""
        mock_connection.fetchrow.return_value = sample_user_row
        mock_connection.fetch.return_value = [sample_role_row]

        repo = UserRepository(pool=mock_pool_with_connection)
        result = await repo.get_by_id("user-uuid-12345678")

        assert result is not None
        assert result["user_id"] == "user-uuid-12345678"
        assert result["email"] == "test@example.com"
        assert result["username"] == "testuser"
        assert result["full_name"] == "Test User"
        assert result["status"] == "active"
        assert "admin" in result["roles"]

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_found(
        self,
        mock_pool_with_connection: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """get_by_id returns None when user not found."""
        mock_connection.fetchrow.return_value = None

        repo = UserRepository(pool=mock_pool_with_connection)
        result = await repo.get_by_id("nonexistent-user")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_handles_database_error(
        self,
        mock_pool_with_connection: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """get_by_id returns None on database error."""
        mock_connection.fetchrow.side_effect = Exception("Database error")

        repo = UserRepository(pool=mock_pool_with_connection)
        result = await repo.get_by_id("user-123")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_releases_connection(
        self,
        mock_pool_with_connection: AsyncMock,
        mock_connection: AsyncMock,
        sample_user_row: Dict[str, Any],
    ) -> None:
        """get_by_id releases connection after operation."""
        mock_connection.fetchrow.return_value = sample_user_row
        mock_connection.fetch.return_value = []

        repo = UserRepository(pool=mock_pool_with_connection)
        await repo.get_by_id("user-uuid-12345678")

        mock_pool_with_connection.release.assert_awaited_once_with(mock_connection)


# ============================================================================
# Get By Email Tests
# ============================================================================


class TestUserRepositoryGetByEmail:
    """Tests for get_by_email operation."""

    @pytest.mark.asyncio
    async def test_get_by_email_returns_user(
        self,
        mock_pool_with_connection: AsyncMock,
        mock_connection: AsyncMock,
        sample_user_row: Dict[str, Any],
        sample_role_row: Dict[str, Any],
    ) -> None:
        """get_by_email returns user dict when found."""
        # First call finds ID, second returns full user
        mock_connection.fetchrow.side_effect = [
            {"id": "user-uuid-12345678"},
            sample_user_row,
        ]
        mock_connection.fetch.return_value = [sample_role_row]

        repo = UserRepository(pool=mock_pool_with_connection)
        result = await repo.get_by_email("test@example.com")

        assert result is not None
        assert result["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_by_email_normalizes_email(
        self,
        mock_pool_with_connection: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """get_by_email normalizes email to lowercase."""
        mock_connection.fetchrow.return_value = None

        repo = UserRepository(pool=mock_pool_with_connection)
        await repo.get_by_email("TEST@EXAMPLE.COM")

        call_args = mock_connection.fetchrow.call_args
        assert "test@example.com" in call_args[0]

    @pytest.mark.asyncio
    async def test_get_by_email_returns_none_when_not_found(
        self,
        mock_pool_with_connection: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """get_by_email returns None when email not found."""
        mock_connection.fetchrow.return_value = None

        repo = UserRepository(pool=mock_pool_with_connection)
        result = await repo.get_by_email("nonexistent@example.com")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_email_handles_database_error(
        self,
        mock_pool_with_connection: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """get_by_email returns None on database error."""
        mock_connection.fetchrow.side_effect = Exception("Database error")

        repo = UserRepository(pool=mock_pool_with_connection)
        result = await repo.get_by_email("test@example.com")

        assert result is None


# ============================================================================
# Create User Tests
# ============================================================================


class TestUserRepositoryCreateUser:
    """Tests for create_user operation."""

    @pytest.mark.asyncio
    async def test_create_user_success(
        self,
        mock_pool_with_connection: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """create_user returns user ID on success."""
        mock_connection.fetchrow.return_value = {"id": "new-user-uuid"}

        repo = UserRepository(pool=mock_pool_with_connection)

        with patch.object(repo, "hash_password", return_value="$2b$12$hashed"):
            result = await repo.create_user(
                email="new@example.com",
                password="password123",
                username="newuser",
                full_name="New User",
            )

        assert result == "new-user-uuid"

    @pytest.mark.asyncio
    async def test_create_user_normalizes_email(
        self,
        mock_pool_with_connection: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """create_user normalizes email to lowercase."""
        mock_connection.fetchrow.return_value = {"id": "new-user-uuid"}

        repo = UserRepository(pool=mock_pool_with_connection)

        with patch.object(repo, "hash_password", return_value="$2b$12$hashed"):
            await repo.create_user(
                email="NEW@EXAMPLE.COM",
                password="password123",
            )

        call_args = mock_connection.fetchrow.call_args
        sql = call_args[0][0]
        params = call_args[0][1:]
        assert params[0] == "new@example.com"

    @pytest.mark.asyncio
    async def test_create_user_hashes_password(
        self,
        mock_pool_with_connection: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """create_user hashes password before storing."""
        mock_connection.fetchrow.return_value = {"id": "new-user-uuid"}

        repo = UserRepository(pool=mock_pool_with_connection)

        with patch.object(
            repo, "hash_password", return_value="$2b$12$hashed"
        ) as mock_hash:
            await repo.create_user(
                email="new@example.com",
                password="password123",
            )

            mock_hash.assert_called_once_with("password123")

    @pytest.mark.asyncio
    async def test_create_user_returns_none_on_error(
        self,
        mock_pool_with_connection: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """create_user returns None on database error."""
        mock_connection.fetchrow.side_effect = Exception("Unique constraint violation")

        repo = UserRepository(pool=mock_pool_with_connection)

        with patch.object(repo, "hash_password", return_value="$2b$12$hashed"):
            result = await repo.create_user(
                email="duplicate@example.com",
                password="password123",
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_create_user_optional_fields(
        self,
        mock_pool_with_connection: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """create_user handles optional fields correctly."""
        mock_connection.fetchrow.return_value = {"id": "new-user-uuid"}

        repo = UserRepository(pool=mock_pool_with_connection)

        with patch.object(repo, "hash_password", return_value="$2b$12$hashed"):
            result = await repo.create_user(
                email="minimal@example.com",
                password="password123",
                # username and full_name omitted
            )

        assert result == "new-user-uuid"

    @pytest.mark.asyncio
    async def test_create_user_releases_connection(
        self,
        mock_pool_with_connection: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """create_user releases connection after operation."""
        mock_connection.fetchrow.return_value = {"id": "new-user-uuid"}

        repo = UserRepository(pool=mock_pool_with_connection)

        with patch.object(repo, "hash_password", return_value="$2b$12$hashed"):
            await repo.create_user(
                email="new@example.com",
                password="password123",
            )

        mock_pool_with_connection.release.assert_awaited_once_with(mock_connection)


# ============================================================================
# Update Password Tests
# ============================================================================


class TestUserRepositoryUpdatePassword:
    """Tests for update_password operation."""

    @pytest.mark.asyncio
    async def test_update_password_success(
        self,
        mock_pool_with_connection: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """update_password returns True on success."""
        mock_connection.execute.return_value = "UPDATE 1"

        repo = UserRepository(pool=mock_pool_with_connection)

        with patch.object(repo, "hash_password", return_value="$2b$12$newhash"):
            result = await repo.update_password("user-123", "newpassword")

        assert result is True

    @pytest.mark.asyncio
    async def test_update_password_hashes_new_password(
        self,
        mock_pool_with_connection: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """update_password hashes new password before storing."""
        mock_connection.execute.return_value = "UPDATE 1"

        repo = UserRepository(pool=mock_pool_with_connection)

        with patch.object(
            repo, "hash_password", return_value="$2b$12$newhash"
        ) as mock_hash:
            await repo.update_password("user-123", "newpassword")

            mock_hash.assert_called_once_with("newpassword")

    @pytest.mark.asyncio
    async def test_update_password_returns_false_when_not_found(
        self,
        mock_pool_with_connection: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """update_password returns False when user not found."""
        mock_connection.execute.return_value = "UPDATE 0"

        repo = UserRepository(pool=mock_pool_with_connection)

        with patch.object(repo, "hash_password", return_value="$2b$12$newhash"):
            result = await repo.update_password("nonexistent", "newpassword")

        assert result is False

    @pytest.mark.asyncio
    async def test_update_password_returns_false_on_error(
        self,
        mock_pool_with_connection: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """update_password returns False on database error."""
        mock_connection.execute.side_effect = Exception("Database error")

        repo = UserRepository(pool=mock_pool_with_connection)

        with patch.object(repo, "hash_password", return_value="$2b$12$newhash"):
            result = await repo.update_password("user-123", "newpassword")

        assert result is False

    @pytest.mark.asyncio
    async def test_update_password_releases_connection(
        self,
        mock_pool_with_connection: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """update_password releases connection after operation."""
        mock_connection.execute.return_value = "UPDATE 1"

        repo = UserRepository(pool=mock_pool_with_connection)

        with patch.object(repo, "hash_password", return_value="$2b$12$newhash"):
            await repo.update_password("user-123", "newpassword")

        mock_pool_with_connection.release.assert_awaited_once_with(mock_connection)


# ============================================================================
# Exists Tests
# ============================================================================


class TestUserRepositoryExists:
    """Tests for exists operation."""

    @pytest.mark.asyncio
    async def test_exists_returns_true_when_found(
        self,
        mock_pool_with_connection: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """exists returns True when user exists."""
        mock_connection.fetchval.return_value = True

        repo = UserRepository(pool=mock_pool_with_connection)
        result = await repo.exists("test@example.com")

        assert result is True

    @pytest.mark.asyncio
    async def test_exists_returns_false_when_not_found(
        self,
        mock_pool_with_connection: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """exists returns False when user does not exist."""
        mock_connection.fetchval.return_value = False

        repo = UserRepository(pool=mock_pool_with_connection)
        result = await repo.exists("nonexistent@example.com")

        assert result is False

    @pytest.mark.asyncio
    async def test_exists_normalizes_email(
        self,
        mock_pool_with_connection: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """exists normalizes email to lowercase."""
        mock_connection.fetchval.return_value = True

        repo = UserRepository(pool=mock_pool_with_connection)
        await repo.exists("TEST@EXAMPLE.COM")

        call_args = mock_connection.fetchval.call_args
        assert "test@example.com" in call_args[0]

    @pytest.mark.asyncio
    async def test_exists_returns_false_on_error(
        self,
        mock_pool_with_connection: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """exists returns False on database error."""
        mock_connection.fetchval.side_effect = Exception("Database error")

        repo = UserRepository(pool=mock_pool_with_connection)
        result = await repo.exists("test@example.com")

        assert result is False

    @pytest.mark.asyncio
    async def test_exists_releases_connection(
        self,
        mock_pool_with_connection: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """exists releases connection after operation."""
        mock_connection.fetchval.return_value = True

        repo = UserRepository(pool=mock_pool_with_connection)
        await repo.exists("test@example.com")

        mock_pool_with_connection.release.assert_awaited_once_with(mock_connection)


# ============================================================================
# Failed Login Tracking Tests
# ============================================================================


class TestUserRepositoryFailedLoginTracking:
    """Tests for failed login tracking and account locking."""

    @pytest.mark.asyncio
    async def test_record_failed_login_increments_count(
        self,
        mock_connection: AsyncMock,
    ) -> None:
        """_record_failed_login increments failed_login_count."""
        repo = UserRepository()

        await repo._record_failed_login(mock_connection, "user-123")

        call_args = mock_connection.execute.call_args
        sql = call_args[0][0]
        assert "failed_login_count = failed_login_count + 1" in sql

    @pytest.mark.asyncio
    async def test_record_failed_login_locks_after_threshold(
        self,
        mock_connection: AsyncMock,
    ) -> None:
        """_record_failed_login locks account after 5 failed attempts."""
        repo = UserRepository()

        await repo._record_failed_login(mock_connection, "user-123")

        call_args = mock_connection.execute.call_args
        sql = call_args[0][0]
        # Should check for 5th failed attempt (count becomes >= 5)
        assert "failed_login_count >= 4" in sql
        assert "INTERVAL '15 minutes'" in sql

    @pytest.mark.asyncio
    async def test_record_successful_login_clears_count(
        self,
        mock_connection: AsyncMock,
    ) -> None:
        """_record_successful_login clears failed_login_count."""
        repo = UserRepository()

        await repo._record_successful_login(mock_connection, "user-123")

        call_args = mock_connection.execute.call_args
        sql = call_args[0][0]
        assert "failed_login_count = 0" in sql
        assert "locked_until = NULL" in sql
        assert "last_login_at = NOW()" in sql


# ============================================================================
# Connection Pool Management Tests
# ============================================================================


class TestUserRepositoryConnectionManagement:
    """Tests for connection pool management."""

    @pytest.mark.asyncio
    async def test_uses_provided_pool(
        self,
        mock_pool_with_connection: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """Repository uses provided pool directly."""
        mock_connection.fetchrow.return_value = None

        repo = UserRepository(pool=mock_pool_with_connection)
        await repo.get_by_id("user-123")

        mock_pool_with_connection.acquire.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_connection_released_on_success(
        self,
        mock_pool_with_connection: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """Connection is released after successful operation."""
        mock_connection.fetchval.return_value = True

        repo = UserRepository(pool=mock_pool_with_connection)
        await repo.exists("test@example.com")

        mock_pool_with_connection.release.assert_awaited_once_with(mock_connection)

    @pytest.mark.asyncio
    async def test_connection_released_on_error(
        self,
        mock_pool_with_connection: AsyncMock,
        mock_connection: AsyncMock,
    ) -> None:
        """Connection is released even after error."""
        mock_connection.fetchval.side_effect = Exception("DB error")

        repo = UserRepository(pool=mock_pool_with_connection)
        await repo.exists("test@example.com")  # Should not raise

        mock_pool_with_connection.release.assert_awaited_once_with(mock_connection)


# ============================================================================
# Edge Cases
# ============================================================================


class TestUserRepositoryEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_validate_credentials_with_email_as_username(
        self,
        mock_pool_with_connection: AsyncMock,
        mock_connection: AsyncMock,
        sample_user_row: Dict[str, Any],
        sample_role_row: Dict[str, Any],
    ) -> None:
        """validate_credentials accepts email as username."""
        mock_connection.fetchrow.return_value = sample_user_row
        mock_connection.fetch.return_value = [sample_role_row]

        repo = UserRepository(pool=mock_pool_with_connection)

        with patch.object(repo, "verify_password", return_value=True):
            result = await repo.validate_credentials(
                "test@example.com",  # Using email
                "password123",
            )

        assert result is not None
        assert result["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_expired_lock_allows_login(
        self,
        mock_pool_with_connection: AsyncMock,
        mock_connection: AsyncMock,
        sample_user_row: Dict[str, Any],
        sample_role_row: Dict[str, Any],
    ) -> None:
        """User with expired lock can log in again."""
        # Lock expired 1 minute ago
        sample_user_row["locked_until"] = datetime.now(timezone.utc) - timedelta(
            minutes=1
        )
        mock_connection.fetchrow.return_value = sample_user_row
        mock_connection.fetch.return_value = [sample_role_row]

        repo = UserRepository(pool=mock_pool_with_connection)

        with patch.object(repo, "verify_password", return_value=True):
            result = await repo.validate_credentials("testuser", "password123")

        assert result is not None

    @pytest.mark.asyncio
    async def test_multiple_tenant_memberships(
        self,
        mock_connection: AsyncMock,
    ) -> None:
        """User with multiple tenant memberships gets first tenant."""
        mock_connection.fetch.return_value = [
            {"tenant_id": "tenant-1", "role_name": "admin"},
            {"tenant_id": "tenant-2", "role_name": "viewer"},
            {"tenant_id": "tenant-3", "role_name": "editor"},
        ]

        repo = UserRepository()
        result = await repo._get_user_roles(mock_connection, "user-123")

        # Should use first tenant (highest priority)
        assert result["tenant_id"] == "tenant-1"
        # Should have all unique roles
        assert len(result["roles"]) == 3

    @pytest.mark.asyncio
    async def test_mfa_enabled_user(
        self,
        mock_pool_with_connection: AsyncMock,
        mock_connection: AsyncMock,
        sample_user_row: Dict[str, Any],
        sample_role_row: Dict[str, Any],
    ) -> None:
        """User with MFA enabled returns mfa_enabled flag."""
        sample_user_row["mfa_enabled"] = True
        mock_connection.fetchrow.return_value = sample_user_row
        mock_connection.fetch.return_value = [sample_role_row]

        repo = UserRepository(pool=mock_pool_with_connection)

        with patch.object(repo, "verify_password", return_value=True):
            result = await repo.validate_credentials("testuser", "password123")

        assert result["mfa_enabled"] is True
