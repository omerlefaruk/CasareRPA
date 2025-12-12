"""
Tests for Azure Key Vault Provider.

These tests mock the Azure SDK to avoid requiring actual Azure credentials.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, PropertyMock

from casare_rpa.infrastructure.security.vault_client import (
    VaultConfig,
    VaultBackend,
    SecretNotFoundError,
    VaultConnectionError,
    VaultAuthenticationError,
    SecretAccessDeniedError,
    CredentialType,
)


# Skip all tests if Azure SDK not available
pytest.importorskip("azure.keyvault.secrets")
pytest.importorskip("azure.identity")


from casare_rpa.infrastructure.security.providers.azure_keyvault import (
    AzureKeyVaultProvider,
    _check_azure_available,
)


@pytest.fixture
def mock_azure_secret():
    """Create a mock Azure KeyVault secret."""
    secret = MagicMock()
    secret.value = '{"username": "testuser", "password": "testpass"}'
    secret.properties = MagicMock()
    secret.properties.version = "abc123"
    secret.properties.enabled = True
    secret.properties.created_on = datetime(2024, 1, 1, tzinfo=timezone.utc)
    secret.properties.updated_on = datetime(2024, 6, 1, tzinfo=timezone.utc)
    secret.properties.expires_on = None
    secret.properties.content_type = "application/x-password"
    secret.properties.tags = {"env": "test"}
    return secret


@pytest.fixture
def mock_secret_properties():
    """Create mock secret properties for listing."""
    props = MagicMock()
    props.name = "test-secret"
    props.enabled = True
    return props


@pytest.fixture
def azure_config():
    """Create Azure Key Vault configuration."""
    return VaultConfig(
        backend=VaultBackend.AZURE_KEYVAULT,
        azure_vault_url="https://test-vault.vault.azure.net/",
    )


@pytest.fixture
def azure_service_principal_config():
    """Create Azure config with Service Principal auth."""
    from pydantic import SecretStr

    return VaultConfig(
        backend=VaultBackend.AZURE_KEYVAULT,
        azure_vault_url="https://test-vault.vault.azure.net/",
        azure_tenant_id="test-tenant-id",
        azure_client_id="test-client-id",
        azure_client_secret=SecretStr("test-client-secret"),
    )


class TestAzureKeyVaultProvider:
    """Test Azure Key Vault provider."""

    def test_init_requires_azure_sdk(self, azure_config):
        """Provider initializes when SDK is available."""
        provider = AzureKeyVaultProvider(azure_config)
        assert provider._config == azure_config
        assert provider._client is None

    @pytest.mark.asyncio
    async def test_connect_requires_vault_url(self):
        """Connect fails without vault URL."""
        config = VaultConfig(backend=VaultBackend.AZURE_KEYVAULT)
        provider = AzureKeyVaultProvider(config)

        with pytest.raises(VaultConnectionError, match="URL not configured"):
            await provider.connect()

    @pytest.mark.asyncio
    async def test_connect_with_default_credential(self, azure_config):
        """Connect uses DefaultAzureCredential by default."""
        provider = AzureKeyVaultProvider(azure_config)

        with (
            patch(
                "casare_rpa.infrastructure.security.providers.azure_keyvault._SecretClient"
            ) as mock_client_cls,
            patch(
                "casare_rpa.infrastructure.security.providers.azure_keyvault._DefaultAzureCredential"
            ) as mock_cred_cls,
        ):
            mock_client = MagicMock()
            mock_client.list_properties_of_secrets.return_value = iter([])
            mock_client_cls.return_value = mock_client

            await provider.connect()

            mock_cred_cls.assert_called_once()
            mock_client_cls.assert_called_once()
            assert provider._client is not None

    @pytest.mark.asyncio
    async def test_connect_with_service_principal(self, azure_service_principal_config):
        """Connect uses ClientSecretCredential with SP config."""
        provider = AzureKeyVaultProvider(azure_service_principal_config)

        with (
            patch(
                "casare_rpa.infrastructure.security.providers.azure_keyvault._SecretClient"
            ) as mock_client_cls,
            patch(
                "casare_rpa.infrastructure.security.providers.azure_keyvault._ClientSecretCredential"
            ) as mock_cred_cls,
        ):
            mock_client = MagicMock()
            mock_client.list_properties_of_secrets.return_value = iter([])
            mock_client_cls.return_value = mock_client

            await provider.connect()

            mock_cred_cls.assert_called_once_with(
                tenant_id="test-tenant-id",
                client_id="test-client-id",
                client_secret="test-client-secret",
            )

    @pytest.mark.asyncio
    async def test_disconnect(self, azure_config):
        """Disconnect closes client."""
        provider = AzureKeyVaultProvider(azure_config)
        provider._client = MagicMock()
        provider._credential = MagicMock()

        await provider.disconnect()

        provider._client.close.assert_called_once()
        assert provider._client is None
        assert provider._credential is None

    @pytest.mark.asyncio
    async def test_is_connected_false_when_no_client(self, azure_config):
        """is_connected returns False when not connected."""
        provider = AzureKeyVaultProvider(azure_config)
        assert await provider.is_connected() is False

    @pytest.mark.asyncio
    async def test_get_secret_success(self, azure_config, mock_azure_secret):
        """Get secret returns data and metadata."""
        provider = AzureKeyVaultProvider(azure_config)
        provider._client = MagicMock()
        provider._client.get_secret.return_value = mock_azure_secret

        result = await provider.get_secret("test-secret")

        assert result.data == {"username": "testuser", "password": "testpass"}
        assert result.metadata.path == "test-secret"
        assert result.metadata.custom_metadata["azure_version"] == "abc123"
        provider._client.get_secret.assert_called_once_with("test-secret", version=None)

    @pytest.mark.asyncio
    async def test_get_secret_plain_text(self, azure_config):
        """Get secret handles plain text values."""
        provider = AzureKeyVaultProvider(azure_config)
        provider._client = MagicMock()

        mock_secret = MagicMock()
        mock_secret.value = "plain-text-secret"
        mock_secret.properties = MagicMock()
        mock_secret.properties.version = "v1"
        mock_secret.properties.enabled = True
        mock_secret.properties.created_on = datetime.now(timezone.utc)
        mock_secret.properties.updated_on = datetime.now(timezone.utc)
        mock_secret.properties.expires_on = None
        mock_secret.properties.content_type = None
        mock_secret.properties.tags = {}

        provider._client.get_secret.return_value = mock_secret

        result = await provider.get_secret("plain-secret")

        assert result.data == {"value": "plain-text-secret"}

    @pytest.mark.asyncio
    async def test_get_secret_not_found(self, azure_config):
        """Get secret raises SecretNotFoundError when not found."""
        provider = AzureKeyVaultProvider(azure_config)
        provider._client = MagicMock()

        from azure.core.exceptions import ResourceNotFoundError

        provider._client.get_secret.side_effect = ResourceNotFoundError("Not found")

        with pytest.raises(SecretNotFoundError, match="not found"):
            await provider.get_secret("missing-secret")

    @pytest.mark.asyncio
    async def test_get_secret_access_denied(self, azure_config):
        """Get secret raises SecretAccessDeniedError on 403."""
        provider = AzureKeyVaultProvider(azure_config)
        provider._client = MagicMock()

        from azure.core.exceptions import HttpResponseError

        error = HttpResponseError("Forbidden")
        error.status_code = 403
        provider._client.get_secret.side_effect = error

        with pytest.raises(SecretAccessDeniedError):
            await provider.get_secret("forbidden-secret")

    @pytest.mark.asyncio
    async def test_put_secret_success(self, azure_config):
        """Put secret stores and returns metadata."""
        provider = AzureKeyVaultProvider(azure_config)
        provider._client = MagicMock()

        mock_result = MagicMock()
        mock_result.properties.version = "new-version"
        mock_result.properties.created_on = datetime.now(timezone.utc)
        mock_result.properties.updated_on = datetime.now(timezone.utc)
        provider._client.set_secret.return_value = mock_result

        result = await provider.put_secret(
            "new-secret",
            {"username": "user", "password": "pass"},
            CredentialType.USERNAME_PASSWORD,
        )

        assert result.path == "new-secret"
        assert result.credential_type == CredentialType.USERNAME_PASSWORD
        provider._client.set_secret.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_secret_success(self, azure_config):
        """Delete secret completes successfully."""
        provider = AzureKeyVaultProvider(azure_config)
        provider._client = MagicMock()

        mock_poller = MagicMock()
        mock_poller.wait.return_value = None
        provider._client.begin_delete_secret.return_value = mock_poller

        result = await provider.delete_secret("to-delete")

        assert result is True
        provider._client.begin_delete_secret.assert_called_once_with("to-delete")

    @pytest.mark.asyncio
    async def test_delete_secret_not_found(self, azure_config):
        """Delete secret returns False when not found."""
        provider = AzureKeyVaultProvider(azure_config)
        provider._client = MagicMock()

        from azure.core.exceptions import ResourceNotFoundError

        provider._client.begin_delete_secret.side_effect = ResourceNotFoundError(
            "Not found"
        )

        result = await provider.delete_secret("missing")

        assert result is False

    @pytest.mark.asyncio
    async def test_list_secrets(self, azure_config, mock_secret_properties):
        """List secrets returns secret names."""
        provider = AzureKeyVaultProvider(azure_config)
        provider._client = MagicMock()

        props1 = MagicMock()
        props1.name = "secret-1"
        props2 = MagicMock()
        props2.name = "secret-2"

        provider._client.list_properties_of_secrets.return_value = iter(
            [props1, props2]
        )

        result = await provider.list_secrets("")

        assert result == ["secret-1", "secret-2"]

    @pytest.mark.asyncio
    async def test_list_secrets_with_prefix(self, azure_config):
        """List secrets filters by prefix."""
        provider = AzureKeyVaultProvider(azure_config)
        provider._client = MagicMock()

        props1 = MagicMock()
        props1.name = "app-secret-1"
        props2 = MagicMock()
        props2.name = "app-secret-2"
        props3 = MagicMock()
        props3.name = "other-secret"

        provider._client.list_properties_of_secrets.return_value = iter(
            [props1, props2, props3]
        )

        result = await provider.list_secrets("app-")

        assert result == ["app-secret-1", "app-secret-2"]

    @pytest.mark.asyncio
    async def test_rotate_secret(self, azure_config, mock_azure_secret):
        """Rotate secret generates new values."""
        provider = AzureKeyVaultProvider(azure_config)
        provider._client = MagicMock()
        provider._client.get_secret.return_value = mock_azure_secret

        mock_result = MagicMock()
        mock_result.properties.version = "rotated"
        mock_result.properties.created_on = datetime.now(timezone.utc)
        mock_result.properties.updated_on = datetime.now(timezone.utc)
        provider._client.set_secret.return_value = mock_result

        result = await provider.rotate_secret("test-secret")

        assert result.path == "test-secret"
        # Verify set_secret was called with new password
        call_args = provider._client.set_secret.call_args
        assert call_args is not None

    def test_infer_credential_type_from_content_type(self, azure_config):
        """Credential type inference from content type."""
        provider = AzureKeyVaultProvider(azure_config)

        assert provider._infer_credential_type("application/x-password") == (
            CredentialType.USERNAME_PASSWORD
        )
        assert provider._infer_credential_type("application/x-api-key") == (
            CredentialType.API_KEY
        )
        assert provider._infer_credential_type("text/plain") == CredentialType.CUSTOM

    @pytest.mark.asyncio
    async def test_recover_deleted_secret(self, azure_config):
        """Recover deleted secret restores it."""
        provider = AzureKeyVaultProvider(azure_config)
        provider._client = MagicMock()

        mock_recovered = MagicMock()
        mock_recovered.properties.created_on = datetime.now(timezone.utc)
        mock_recovered.properties.updated_on = datetime.now(timezone.utc)
        mock_recovered.properties.content_type = None

        mock_poller = MagicMock()
        mock_poller.result.return_value = mock_recovered
        provider._client.begin_recover_deleted_secret.return_value = mock_poller

        result = await provider.recover_deleted_secret("deleted-secret")

        assert result.path == "deleted-secret"

    @pytest.mark.asyncio
    async def test_purge_deleted_secret(self, azure_config):
        """Purge permanently deletes a secret."""
        provider = AzureKeyVaultProvider(azure_config)
        provider._client = MagicMock()

        result = await provider.purge_deleted_secret("to-purge")

        assert result is True
        provider._client.purge_deleted_secret.assert_called_once_with("to-purge")


class TestAzureKeyVaultProviderEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_not_connected_raises_error(self, azure_config):
        """Operations fail when not connected."""
        provider = AzureKeyVaultProvider(azure_config)

        with pytest.raises(VaultConnectionError, match="Not connected"):
            await provider.get_secret("any")

    @pytest.mark.asyncio
    async def test_managed_identity_config(self):
        """Managed Identity credential is used when configured."""
        from pydantic import SecretStr

        config = VaultConfig(
            backend=VaultBackend.AZURE_KEYVAULT,
            azure_vault_url="https://test.vault.azure.net/",
            azure_use_managed_identity=True,
            azure_managed_identity_client_id="mi-client-id",
        )

        provider = AzureKeyVaultProvider(config)

        with (
            patch(
                "casare_rpa.infrastructure.security.providers.azure_keyvault._SecretClient"
            ),
            patch(
                "casare_rpa.infrastructure.security.providers.azure_keyvault._ManagedIdentityCredential"
            ) as mock_mi_cred,
        ):
            mock_client = MagicMock()
            mock_client.list_properties_of_secrets.return_value = iter([])

            with patch(
                "casare_rpa.infrastructure.security.providers.azure_keyvault._SecretClient",
                return_value=mock_client,
            ):
                await provider.connect()

            mock_mi_cred.assert_called_once_with(client_id="mi-client-id")

    def test_azure_availability_check(self):
        """Azure availability check returns bool."""
        result = _check_azure_available()
        assert isinstance(result, bool)
        assert result is True  # We imported it, so it's available
