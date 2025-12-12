"""
Tests for UserManager - User authentication and management.

Tests cover:
- User creation with validation
- Password hashing and verification
- Authentication flow
- Account lockout
- MFA enable/disable
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from casare_rpa.infrastructure.auth.user_manager import (
    UserManager,
    AuthResult,
    AuthenticationResult,
    PasswordPolicy,
    UserExistsError,
    InvalidPasswordError,
    InvalidEmailError,
    UserNotFoundError,
)
from casare_rpa.infrastructure.security.rbac import SystemRole
from casare_rpa.domain.entities.user import User, UserStatus


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_db_client():
    """Create a mock database client."""
    client = MagicMock()
    client.table = MagicMock(return_value=client)
    client.select = MagicMock(return_value=client)
    client.insert = MagicMock(return_value=client)
    client.update = MagicMock(return_value=client)
    client.eq = MagicMock(return_value=client)
    client.execute = MagicMock(return_value=MagicMock(data=[]))
    return client


@pytest.fixture
def user_manager(mock_db_client):
    """Create UserManager with mock client."""
    return UserManager(
        db_client=mock_db_client,
        max_login_attempts=3,
        lockout_minutes=15,
    )


@pytest.fixture
def password_policy():
    """Create a test password policy."""
    return PasswordPolicy(
        min_length=8,
        max_length=128,
        require_uppercase=True,
        require_lowercase=True,
        require_digit=True,
        require_special=False,
    )


@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    return User(
        id=uuid4(),
        email="test@example.com",
        password_hash="$2b$12$hashedpassword",
        role=SystemRole.DEVELOPER.value,
        display_name="Test User",
        status=UserStatus.ACTIVE,
    )


# =============================================================================
# PASSWORD POLICY TESTS
# =============================================================================


class TestPasswordPolicy:
    """Tests for PasswordPolicy validation."""

    def test_validate_valid_password(self, password_policy):
        """Valid password passes validation."""
        is_valid, error = password_policy.validate("SecurePass123")
        assert is_valid is True
        assert error == ""

    def test_validate_too_short(self, password_policy):
        """Password shorter than minimum fails."""
        is_valid, error = password_policy.validate("Short1")
        assert is_valid is False
        assert "at least 8" in error

    def test_validate_too_long(self, password_policy):
        """Password longer than maximum fails."""
        is_valid, error = password_policy.validate("A" * 129 + "a1")
        assert is_valid is False
        assert "at most 128" in error

    def test_validate_no_uppercase(self, password_policy):
        """Password without uppercase fails."""
        is_valid, error = password_policy.validate("nouppercase123")
        assert is_valid is False
        assert "uppercase" in error

    def test_validate_no_lowercase(self, password_policy):
        """Password without lowercase fails."""
        is_valid, error = password_policy.validate("NOLOWERCASE123")
        assert is_valid is False
        assert "lowercase" in error

    def test_validate_no_digit(self, password_policy):
        """Password without digit fails."""
        is_valid, error = password_policy.validate("NoDigitHere")
        assert is_valid is False
        assert "digit" in error

    def test_validate_special_char_required(self):
        """Password without special char fails when required."""
        policy = PasswordPolicy(require_special=True)
        is_valid, error = policy.validate("NoSpecial123")
        assert is_valid is False
        assert "special character" in error


# =============================================================================
# USER MANAGER TESTS
# =============================================================================


class TestUserManagerCreate:
    """Tests for user creation."""

    @pytest.mark.asyncio
    async def test_create_user_success(self, user_manager, mock_db_client):
        """Successfully create a new user."""
        mock_db_client.execute.return_value = MagicMock(data=[])

        user = await user_manager.create_user(
            email="newuser@example.com",
            password="SecurePass123",
            role=SystemRole.DEVELOPER,
            display_name="New User",
        )

        assert user.email == "newuser@example.com"
        assert user.role == SystemRole.DEVELOPER.value
        assert user.display_name == "New User"
        assert user.status == UserStatus.ACTIVE
        mock_db_client.table.assert_called()

    @pytest.mark.asyncio
    async def test_create_user_invalid_email(self, user_manager):
        """Invalid email format raises error."""
        with pytest.raises(InvalidEmailError):
            await user_manager.create_user(
                email="invalid-email",
                password="SecurePass123",
            )

    @pytest.mark.asyncio
    async def test_create_user_weak_password(self, user_manager):
        """Weak password raises error."""
        with pytest.raises(InvalidPasswordError):
            await user_manager.create_user(
                email="user@example.com",
                password="weak",
            )

    @pytest.mark.asyncio
    async def test_create_user_already_exists(
        self, user_manager, mock_db_client, sample_user
    ):
        """Duplicate email raises error."""
        # Mock existing user found
        mock_db_client.execute.return_value = MagicMock(
            data=[{"id": str(sample_user.id), "email": sample_user.email}]
        )

        with pytest.raises(UserExistsError):
            await user_manager.create_user(
                email=sample_user.email,
                password="SecurePass123",
            )


class TestUserManagerAuthenticate:
    """Tests for user authentication."""

    @pytest.mark.asyncio
    async def test_authenticate_success(self, user_manager, mock_db_client):
        """Successful authentication returns user."""
        import bcrypt

        password = "SecurePass123"
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        mock_db_client.execute.return_value = MagicMock(
            data=[
                {
                    "id": str(uuid4()),
                    "email": "user@example.com",
                    "password_hash": password_hash,
                    "role": "developer",
                    "status": "active",
                    "mfa_enabled": False,
                }
            ]
        )

        result = await user_manager.authenticate("user@example.com", password)

        assert result.status == AuthResult.SUCCESS
        assert result.user is not None
        assert result.user.email == "user@example.com"

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, user_manager, mock_db_client):
        """Non-existent user returns invalid credentials."""
        mock_db_client.execute.return_value = MagicMock(data=[])

        result = await user_manager.authenticate(
            "nonexistent@example.com",
            "SomePassword123",
        )

        assert result.status == AuthResult.INVALID_CREDENTIALS
        assert result.user is None

    @pytest.mark.asyncio
    async def test_authenticate_wrong_password(self, user_manager, mock_db_client):
        """Wrong password returns invalid credentials."""
        import bcrypt

        correct_hash = bcrypt.hashpw(b"CorrectPassword123", bcrypt.gensalt()).decode()

        mock_db_client.execute.return_value = MagicMock(
            data=[
                {
                    "id": str(uuid4()),
                    "email": "user@example.com",
                    "password_hash": correct_hash,
                    "role": "developer",
                    "status": "active",
                    "failed_login_attempts": 0,
                }
            ]
        )

        result = await user_manager.authenticate(
            "user@example.com",
            "WrongPassword123",
        )

        assert result.status == AuthResult.INVALID_CREDENTIALS

    @pytest.mark.asyncio
    async def test_authenticate_account_locked(self, user_manager, mock_db_client):
        """Locked account returns account locked status."""
        mock_db_client.execute.return_value = MagicMock(
            data=[
                {
                    "id": str(uuid4()),
                    "email": "user@example.com",
                    "password_hash": "hash",
                    "role": "developer",
                    "status": "locked",
                }
            ]
        )

        result = await user_manager.authenticate(
            "user@example.com",
            "SomePassword123",
        )

        assert result.status == AuthResult.ACCOUNT_LOCKED

    @pytest.mark.asyncio
    async def test_authenticate_mfa_required(self, user_manager, mock_db_client):
        """MFA-enabled user requires MFA verification."""
        import bcrypt

        password = "SecurePass123"
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        mock_db_client.execute.return_value = MagicMock(
            data=[
                {
                    "id": str(uuid4()),
                    "email": "user@example.com",
                    "password_hash": password_hash,
                    "role": "developer",
                    "status": "active",
                    "mfa_enabled": True,
                    "mfa_secret": "JBSWY3DPEHPK3PXP",
                }
            ]
        )

        result = await user_manager.authenticate("user@example.com", password)

        assert result.status == AuthResult.MFA_REQUIRED
        assert result.requires_mfa is True
        assert result.user is not None


class TestUserManagerMFA:
    """Tests for MFA management."""

    @pytest.mark.asyncio
    async def test_enable_mfa(self, user_manager, mock_db_client):
        """Enable MFA for a user."""
        user_id = uuid4()
        mock_db_client.execute.return_value = MagicMock(
            data=[
                {
                    "id": str(user_id),
                    "email": "user@example.com",
                    "password_hash": "hash",
                    "role": "developer",
                    "status": "active",
                    "mfa_enabled": False,
                }
            ]
        )

        result = await user_manager.enable_mfa(user_id, "encrypted_secret")

        assert result is True

    @pytest.mark.asyncio
    async def test_disable_mfa(self, user_manager, mock_db_client):
        """Disable MFA for a user."""
        user_id = uuid4()
        mock_db_client.execute.return_value = MagicMock(
            data=[
                {
                    "id": str(user_id),
                    "email": "user@example.com",
                    "password_hash": "hash",
                    "role": "developer",
                    "status": "active",
                    "mfa_enabled": True,
                    "mfa_secret": "secret",
                }
            ]
        )

        result = await user_manager.disable_mfa(user_id)

        assert result is True


class TestUserManagerAccountManagement:
    """Tests for account management operations."""

    @pytest.mark.asyncio
    async def test_unlock_account(self, user_manager, mock_db_client):
        """Unlock a locked account."""
        user_id = uuid4()
        mock_db_client.execute.return_value = MagicMock(
            data=[
                {
                    "id": str(user_id),
                    "email": "user@example.com",
                    "password_hash": "hash",
                    "role": "developer",
                    "status": "locked",
                    "failed_login_attempts": 5,
                }
            ]
        )

        result = await user_manager.unlock_account(user_id)

        assert result is True

    @pytest.mark.asyncio
    async def test_deactivate_user(self, user_manager, mock_db_client):
        """Deactivate a user account."""
        user_id = uuid4()
        mock_db_client.execute.return_value = MagicMock(
            data=[
                {
                    "id": str(user_id),
                    "email": "user@example.com",
                    "password_hash": "hash",
                    "role": "developer",
                    "status": "active",
                }
            ]
        )

        result = await user_manager.deactivate_user(user_id)

        assert result is True

    @pytest.mark.asyncio
    async def test_user_not_found_operations(self, user_manager, mock_db_client):
        """Operations on non-existent user raise error."""
        mock_db_client.execute.return_value = MagicMock(data=[])
        user_id = uuid4()

        with pytest.raises(UserNotFoundError):
            await user_manager.unlock_account(user_id)

        with pytest.raises(UserNotFoundError):
            await user_manager.enable_mfa(user_id, "secret")


__all__ = [
    "TestPasswordPolicy",
    "TestUserManagerCreate",
    "TestUserManagerAuthenticate",
    "TestUserManagerMFA",
    "TestUserManagerAccountManagement",
]
