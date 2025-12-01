"""Tests for credential_manager module."""

from datetime import datetime, timedelta
import pytest
from unittest.mock import Mock, patch

from casare_rpa.utils.security.credential_manager import (
    CredentialScope,
    CredentialType,
    Credential,
    CredentialManager,
    VaultRequiredError,
)


class TestCredentialScope:
    """Tests for CredentialScope enum."""

    def test_enum_values(self):
        """Test that enum values are correct."""
        assert CredentialScope.GLOBAL.value == "global"
        assert CredentialScope.PROJECT.value == "projects"
        assert CredentialScope.WORKFLOW.value == "workflows"
        assert CredentialScope.ROBOT.value == "robots"
        assert CredentialScope.ASSET.value == "assets"


class TestCredentialType:
    """Tests for CredentialType enum."""

    def test_enum_values(self):
        """Test that enum values are correct."""
        assert CredentialType.GENERIC.value == "generic"
        assert CredentialType.USERNAME_PASSWORD.value == "username_password"
        assert CredentialType.API_KEY.value == "api_key"
        assert CredentialType.OAUTH2.value == "oauth2"
        assert CredentialType.CERTIFICATE.value == "certificate"
        assert CredentialType.SSH_KEY.value == "ssh_key"


class TestCredential:
    """Tests for Credential dataclass."""

    def test_default_values(self):
        """Test default credential values."""
        cred = Credential(name="test_cred")

        assert cred.name == "test_cred"
        assert cred.credential_type == CredentialType.GENERIC
        assert cred.username is None
        assert cred.password is None
        assert cred.api_key is None
        assert cred.access_token is None
        assert cred.refresh_token is None
        assert cred.certificate is None
        assert cred.private_key is None
        assert cred.metadata == {}
        assert cred.created_at is None
        assert cred.expires_at is None

    def test_username_password_credential(self):
        """Test username/password credential."""
        cred = Credential(
            name="db_admin",
            credential_type=CredentialType.USERNAME_PASSWORD,
            username="admin",
            password="secret123",
        )

        assert cred.name == "db_admin"
        assert cred.credential_type == CredentialType.USERNAME_PASSWORD
        assert cred.username == "admin"
        assert cred.password == "secret123"

    def test_api_key_credential(self):
        """Test API key credential."""
        cred = Credential(
            name="service_api",
            credential_type=CredentialType.API_KEY,
            api_key="sk-abc123xyz",
        )

        assert cred.name == "service_api"
        assert cred.credential_type == CredentialType.API_KEY
        assert cred.api_key == "sk-abc123xyz"

    def test_oauth2_credential(self):
        """Test OAuth2 credential."""
        cred = Credential(
            name="google_auth",
            credential_type=CredentialType.OAUTH2,
            access_token="access_token_value",
            refresh_token="refresh_token_value",
        )

        assert cred.name == "google_auth"
        assert cred.credential_type == CredentialType.OAUTH2
        assert cred.access_token == "access_token_value"
        assert cred.refresh_token == "refresh_token_value"

    def test_to_dict_minimal(self):
        """Test to_dict with minimal data."""
        cred = Credential(name="minimal")

        data = cred.to_dict()

        assert data["name"] == "minimal"
        assert data["credential_type"] == "generic"
        assert data["metadata"] == {}
        assert "username" not in data
        assert "password" not in data

    def test_to_dict_full(self):
        """Test to_dict with all fields."""
        now = datetime(2024, 1, 15, 10, 30, 0)
        expires = datetime(2024, 12, 31, 23, 59, 59)

        cred = Credential(
            name="full_cred",
            credential_type=CredentialType.USERNAME_PASSWORD,
            username="admin",
            password="secret",
            metadata={"env": "production"},
            created_at=now,
            updated_at=now,
            expires_at=expires,
        )

        data = cred.to_dict()

        assert data["name"] == "full_cred"
        assert data["credential_type"] == "username_password"
        assert data["username"] == "admin"
        assert data["password"] == "secret"
        assert data["metadata"] == {"env": "production"}
        assert data["created_at"] == "2024-01-15T10:30:00"
        assert data["updated_at"] == "2024-01-15T10:30:00"
        assert data["expires_at"] == "2024-12-31T23:59:59"

    def test_from_dict_minimal(self):
        """Test from_dict with minimal data."""
        data = {
            "name": "from_dict_cred",
        }

        cred = Credential.from_dict(data)

        assert cred.name == "from_dict_cred"
        assert cred.credential_type == CredentialType.GENERIC
        assert cred.username is None

    def test_from_dict_full(self):
        """Test from_dict with all fields."""
        data = {
            "name": "full_cred",
            "credential_type": "username_password",
            "username": "admin",
            "password": "secret",
            "api_key": "key123",
            "access_token": "access",
            "refresh_token": "refresh",
            "metadata": {"env": "staging"},
            "created_at": "2024-03-01T12:00:00",
            "updated_at": "2024-03-02T12:00:00",
            "expires_at": "2024-06-01T00:00:00",
        }

        cred = Credential.from_dict(data)

        assert cred.name == "full_cred"
        assert cred.credential_type == CredentialType.USERNAME_PASSWORD
        assert cred.username == "admin"
        assert cred.password == "secret"
        assert cred.api_key == "key123"
        assert cred.access_token == "access"
        assert cred.refresh_token == "refresh"
        assert cred.metadata == {"env": "staging"}
        assert cred.created_at == datetime(2024, 3, 1, 12, 0, 0)
        assert cred.updated_at == datetime(2024, 3, 2, 12, 0, 0)
        assert cred.expires_at == datetime(2024, 6, 1, 0, 0, 0)

    def test_is_expired_not_expired(self):
        """Test is_expired with future expiration."""
        future = datetime.now() + timedelta(days=30)
        cred = Credential(name="future_cred", expires_at=future)

        assert cred.is_expired() is False

    def test_is_expired_expired(self):
        """Test is_expired with past expiration."""
        past = datetime.now() - timedelta(days=1)
        cred = Credential(name="expired_cred", expires_at=past)

        assert cred.is_expired() is True

    def test_is_expired_no_expiration(self):
        """Test is_expired with no expiration set."""
        cred = Credential(name="no_expiry")

        assert cred.is_expired() is False


class TestCredentialManager:
    """Tests for CredentialManager class."""

    def test_init_requires_vault_client(self):
        """Test that __init__ requires a vault client."""
        with pytest.raises(VaultRequiredError) as exc_info:
            CredentialManager(vault_client=None)

        assert "REQUIRED" in str(exc_info.value)

    def test_init_with_vault_client(self):
        """Test successful initialization with vault client."""
        mock_vault = Mock()

        manager = CredentialManager(vault_client=mock_vault)

        assert manager.vault == mock_vault

    def test_build_path_global(self):
        """Test _build_path for global scope."""
        mock_vault = Mock()
        manager = CredentialManager(vault_client=mock_vault)

        path = manager._build_path("test_cred", CredentialScope.GLOBAL)

        assert path == "global/test_cred"

    def test_build_path_with_scope_id(self):
        """Test _build_path with scope ID."""
        mock_vault = Mock()
        manager = CredentialManager(vault_client=mock_vault)

        path = manager._build_path("db_cred", CredentialScope.WORKFLOW, "wf_123")

        assert path == "workflows/wf_123/db_cred"

    def test_build_path_robot(self):
        """Test _build_path for robot scope."""
        mock_vault = Mock()
        manager = CredentialManager(vault_client=mock_vault)

        path = manager._build_path("api_key", CredentialScope.ROBOT, "robot_456")

        assert path == "robots/robot_456/api_key"

    def test_get_credential(self):
        """Test get_credential retrieves from vault."""
        mock_vault = Mock()
        mock_vault.get_secret.return_value = {
            "name": "test_cred",
            "credential_type": "username_password",
            "username": "admin",
            "password": "secret",
        }
        manager = CredentialManager(vault_client=mock_vault)

        cred = manager.get_credential("test_cred")

        assert cred.name == "test_cred"
        assert cred.username == "admin"
        assert cred.password == "secret"
        mock_vault.get_secret.assert_called_once_with("global/test_cred")

    def test_store_credential(self):
        """Test store_credential saves to vault."""
        mock_vault = Mock()
        manager = CredentialManager(vault_client=mock_vault)

        manager.store_credential(
            name="new_cred",
            username="user",
            password="pass",
            scope=CredentialScope.PROJECT,
            scope_id="proj_123",
        )

        mock_vault.store_secret.assert_called_once()
        call_args = mock_vault.store_secret.call_args
        assert call_args[0][0] == "projects/proj_123/new_cred"
        assert call_args[0][1]["name"] == "new_cred"
        assert call_args[0][1]["username"] == "user"
        assert call_args[0][1]["password"] == "pass"

    def test_delete_credential(self):
        """Test delete_credential removes from vault."""
        mock_vault = Mock()
        manager = CredentialManager(vault_client=mock_vault)

        manager.delete_credential("old_cred", CredentialScope.GLOBAL)

        mock_vault.delete_secret.assert_called_once_with(
            "global/old_cred", destroy=False
        )

    def test_delete_credential_permanent(self):
        """Test delete_credential with permanent flag."""
        mock_vault = Mock()
        manager = CredentialManager(vault_client=mock_vault)

        manager.delete_credential("old_cred", permanent=True)

        mock_vault.delete_secret.assert_called_once_with(
            "global/old_cred", destroy=True
        )

    def test_list_credentials(self):
        """Test list_credentials returns vault list."""
        mock_vault = Mock()
        mock_vault.list_secrets.return_value = ["cred1", "cred2", "cred3"]
        manager = CredentialManager(vault_client=mock_vault)

        result = manager.list_credentials(CredentialScope.ASSET, "asset_1")

        assert result == ["cred1", "cred2", "cred3"]
        mock_vault.list_secrets.assert_called_once_with("assets/asset_1")

    def test_credential_exists_true(self):
        """Test credential_exists returns True when exists."""
        mock_vault = Mock()
        mock_vault.get_secret.return_value = {"name": "existing"}
        manager = CredentialManager(vault_client=mock_vault)

        result = manager.credential_exists("existing")

        assert result is True

    def test_credential_exists_false(self):
        """Test credential_exists returns False when not found."""
        from casare_rpa.utils.security.vault_client import VaultSecretNotFoundError

        mock_vault = Mock()
        mock_vault.get_secret.side_effect = VaultSecretNotFoundError("not found")
        manager = CredentialManager(vault_client=mock_vault)

        result = manager.credential_exists("nonexistent")

        assert result is False


class TestCredentialManagerCreate:
    """Tests for CredentialManager.create factory method."""

    def test_create_no_vault_addr_raises(self):
        """Test create raises when VAULT_ADDR not set."""
        with patch.dict("os.environ", {}, clear=True):
            with patch(
                "casare_rpa.utils.security.credential_manager.HVAC_AVAILABLE", True
            ):
                with pytest.raises(VaultRequiredError) as exc_info:
                    CredentialManager.create()

                assert "VAULT_ADDR" in str(exc_info.value)

    def test_create_no_hvac_raises(self):
        """Test create raises when hvac not installed."""
        with patch(
            "casare_rpa.utils.security.credential_manager.HVAC_AVAILABLE", False
        ):
            with pytest.raises(VaultRequiredError) as exc_info:
                CredentialManager.create()

            assert "hvac" in str(exc_info.value)
