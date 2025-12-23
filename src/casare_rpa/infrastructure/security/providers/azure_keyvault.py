"""
Azure Key Vault Provider Implementation.

Supports:
- DefaultAzureCredential (auto-detect: env vars, managed identity, CLI)
- Service Principal authentication (client_id, client_secret, tenant_id)
- Managed Identity (for Azure-hosted workloads)
- Secret versioning
- Soft-delete recovery
"""

from datetime import UTC, datetime
from typing import Any

from loguru import logger

from casare_rpa.infrastructure.security.vault_client import (
    CredentialType,
    SecretAccessDeniedError,
    SecretMetadata,
    SecretNotFoundError,
    SecretValue,
    VaultAuthenticationError,
    VaultConfig,
    VaultConnectionError,
    VaultProvider,
)

# Lazy load Azure SDK
_AZURE_AVAILABLE: bool | None = None
_SecretClient = None
_DefaultAzureCredential = None
_ClientSecretCredential = None
_ManagedIdentityCredential = None
_ResourceNotFoundError = None
_HttpResponseError = None


def _check_azure_available() -> bool:
    """Check if Azure SDK is available and import modules."""
    global _AZURE_AVAILABLE, _SecretClient, _DefaultAzureCredential
    global _ClientSecretCredential, _ManagedIdentityCredential
    global _ResourceNotFoundError, _HttpResponseError

    if _AZURE_AVAILABLE is not None:
        return _AZURE_AVAILABLE

    try:
        from azure.core.exceptions import HttpResponseError, ResourceNotFoundError
        from azure.identity import (
            ClientSecretCredential,
            DefaultAzureCredential,
            ManagedIdentityCredential,
        )
        from azure.keyvault.secrets import SecretClient

        _SecretClient = SecretClient
        _DefaultAzureCredential = DefaultAzureCredential
        _ClientSecretCredential = ClientSecretCredential
        _ManagedIdentityCredential = ManagedIdentityCredential
        _ResourceNotFoundError = ResourceNotFoundError
        _HttpResponseError = HttpResponseError

        _AZURE_AVAILABLE = True
    except ImportError:
        _AZURE_AVAILABLE = False

    return _AZURE_AVAILABLE


class AzureKeyVaultProvider(VaultProvider):
    """
    Azure Key Vault provider using azure-keyvault-secrets client.

    Supports multiple authentication methods:
    - DefaultAzureCredential: Auto-detects available credentials
    - Service Principal: Uses client_id, client_secret, tenant_id
    - Managed Identity: For Azure-hosted applications

    Usage:
        config = VaultConfig(
            backend=VaultBackend.AZURE_KEYVAULT,
            azure_vault_url="https://my-vault.vault.azure.net/",
        )
        provider = AzureKeyVaultProvider(config)
        await provider.connect()
    """

    def __init__(self, config: VaultConfig) -> None:
        """
        Initialize Azure Key Vault provider.

        Args:
            config: Vault configuration with Azure settings

        Raises:
            ImportError: If Azure SDK libraries are not installed
        """
        if not _check_azure_available():
            raise ImportError(
                "Azure Key Vault support requires azure-identity and "
                "azure-keyvault-secrets libraries. "
                "Install with: pip install azure-identity azure-keyvault-secrets"
            )

        self._config = config
        self._client: _SecretClient | None = None
        self._credential = None

    async def connect(self) -> None:
        """Connect to Azure Key Vault."""
        if not self._config.azure_vault_url:
            raise VaultConnectionError("Azure Key Vault URL not configured")

        try:
            # Determine credential type
            self._credential = self._create_credential()

            # Create secret client
            self._client = _SecretClient(
                vault_url=self._config.azure_vault_url,
                credential=self._credential,
            )

            # Verify connection by listing secrets (limited)
            try:
                # Just iterate once to verify access
                secrets_iter = self._client.list_properties_of_secrets()
                next(iter(secrets_iter), None)
            except StopIteration:
                pass  # Empty vault is valid

            logger.info(f"Connected to Azure Key Vault at {self._config.azure_vault_url}")

        except _HttpResponseError as e:
            if e.status_code == 401 or e.status_code == 403:
                raise VaultAuthenticationError(
                    f"Azure Key Vault authentication failed: {e.message}"
                ) from e
            raise VaultConnectionError(f"Failed to connect to Azure Key Vault: {e.message}") from e
        except Exception as e:
            raise VaultConnectionError(f"Failed to connect to Azure Key Vault: {e}") from e

    def _create_credential(self) -> Any:
        """Create appropriate Azure credential based on config."""
        # Service Principal authentication
        if (
            self._config.azure_tenant_id
            and self._config.azure_client_id
            and self._config.azure_client_secret
        ):
            logger.debug("Using Service Principal credential for Azure Key Vault")
            return _ClientSecretCredential(
                tenant_id=self._config.azure_tenant_id,
                client_id=self._config.azure_client_id,
                client_secret=self._config.azure_client_secret.get_secret_value(),
            )

        # Managed Identity (explicit)
        if self._config.azure_use_managed_identity:
            logger.debug("Using Managed Identity credential for Azure Key Vault")
            client_id = self._config.azure_managed_identity_client_id
            return (
                _ManagedIdentityCredential(client_id=client_id)
                if client_id
                else _ManagedIdentityCredential()
            )

        # Default credential chain (auto-detect)
        logger.debug("Using DefaultAzureCredential for Azure Key Vault")
        return _DefaultAzureCredential()

    async def disconnect(self) -> None:
        """Disconnect from Azure Key Vault."""
        if self._client:
            self._client.close()
            self._client = None
        if self._credential:
            # Close credential if it has a close method
            if hasattr(self._credential, "close"):
                self._credential.close()
            self._credential = None
        logger.info("Disconnected from Azure Key Vault")

    async def is_connected(self) -> bool:
        """Check if connected to Azure Key Vault."""
        if not self._client:
            return False
        try:
            # Try to list one secret to verify connection
            secrets_iter = self._client.list_properties_of_secrets()
            next(iter(secrets_iter), None)
            return True
        except Exception:
            return False

    def _ensure_connected(self) -> "_SecretClient":
        """Ensure client is connected and return it."""
        if not self._client:
            raise VaultConnectionError("Not connected to Azure Key Vault")
        return self._client

    async def get_secret(self, path: str, version: int | None = None) -> SecretValue:
        """
        Get secret from Azure Key Vault.

        Args:
            path: Secret name in Key Vault
            version: Optional specific version (as string version ID in Azure)

        Returns:
            SecretValue with data and metadata
        """
        client = self._ensure_connected()

        try:
            # Azure uses version as string, not int
            version_str = str(version) if version else None
            secret = client.get_secret(path, version=version_str)

            # Azure secrets are single values, wrap in dict
            data = {"value": secret.value}

            # Parse content type for credential type hints
            credential_type = self._infer_credential_type(secret.properties.content_type or "")

            # Build metadata
            metadata = SecretMetadata(
                path=path,
                version=1,  # Azure versions are strings, use 1 for compatibility
                created_at=secret.properties.created_on or datetime.now(UTC),
                updated_at=secret.properties.updated_on or datetime.now(UTC),
                expires_at=secret.properties.expires_on,
                credential_type=credential_type,
                custom_metadata={
                    "azure_version": secret.properties.version,
                    "enabled": secret.properties.enabled,
                    "content_type": secret.properties.content_type,
                    "tags": secret.properties.tags or {},
                },
            )

            return SecretValue(data=data, metadata=metadata)

        except _ResourceNotFoundError as e:
            raise SecretNotFoundError(f"Secret not found: {path}", path=path) from e
        except _HttpResponseError as e:
            if e.status_code == 403:
                raise SecretAccessDeniedError(f"Access denied to secret: {path}", path=path) from e
            logger.error(f"Failed to read secret {path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to read secret {path}: {e}")
            raise

    async def put_secret(
        self,
        path: str,
        data: dict[str, Any],
        credential_type: CredentialType = CredentialType.CUSTOM_KIND,
        metadata: dict[str, Any] | None = None,
    ) -> SecretMetadata:
        """Store secret in Azure Key Vault."""
        client = self._ensure_connected()

        try:
            # Azure Key Vault stores single values
            # If data has 'value' key, use that; otherwise serialize as JSON
            if "value" in data and len(data) == 1:
                secret_value = str(data["value"])
            else:
                import json

                secret_value = json.dumps(data)

            # Set content type based on credential type
            content_type = self._credential_type_to_content_type(credential_type)

            # Extract tags from metadata
            tags = (metadata or {}).get("tags", {})

            # Set secret
            secret = client.set_secret(
                name=path,
                value=secret_value,
                content_type=content_type,
                tags=tags,
            )

            return SecretMetadata(
                path=path,
                version=1,
                created_at=secret.properties.created_on or datetime.now(UTC),
                updated_at=secret.properties.updated_on or datetime.now(UTC),
                credential_type=credential_type,
                custom_metadata={
                    "azure_version": secret.properties.version,
                    "tags": tags,
                },
            )

        except _HttpResponseError as e:
            if e.status_code == 403:
                raise SecretAccessDeniedError(f"Access denied writing to: {path}", path=path) from e
            logger.error(f"Failed to write secret {path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to write secret {path}: {e}")
            raise

    async def delete_secret(self, path: str) -> bool:
        """Delete secret from Azure Key Vault (soft-delete)."""
        client = self._ensure_connected()

        try:
            # Start delete operation (soft-delete by default in Azure)
            poller = client.begin_delete_secret(path)
            # Wait for deletion to complete
            poller.wait()

            logger.info(f"Deleted secret: {path}")
            return True

        except _ResourceNotFoundError:
            return False
        except _HttpResponseError as e:
            if e.status_code == 403:
                raise SecretAccessDeniedError(f"Access denied deleting: {path}", path=path) from e
            logger.error(f"Failed to delete secret {path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to delete secret {path}: {e}")
            raise

    async def list_secrets(self, path_prefix: str) -> list[str]:
        """List secrets in Azure Key Vault."""
        client = self._ensure_connected()

        try:
            secrets = []
            for secret_properties in client.list_properties_of_secrets():
                name = secret_properties.name
                # Filter by prefix if provided
                if not path_prefix or name.startswith(path_prefix):
                    secrets.append(name)

            return sorted(secrets)

        except _HttpResponseError as e:
            if e.status_code == 403:
                raise SecretAccessDeniedError(
                    "Access denied listing secrets", path=path_prefix
                ) from e
            logger.error(f"Failed to list secrets: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to list secrets at {path_prefix}: {e}")
            raise

    async def rotate_secret(self, path: str) -> SecretMetadata:
        """
        Rotate a secret by generating new random values.

        Note: Azure Key Vault doesn't have built-in rotation.
        This generates a new version with new random values.
        """
        # Get current secret
        current = await self.get_secret(path)

        # Generate new values based on credential type
        new_data = self._generate_rotated_values(current.data, current.metadata.credential_type)

        # Store new version
        return await self.put_secret(
            path=path,
            data=new_data,
            credential_type=current.metadata.credential_type,
            metadata=current.metadata.custom_metadata,
        )

    def _generate_rotated_values(
        self, current_data: dict[str, Any], cred_type: CredentialType
    ) -> dict[str, Any]:
        """Generate new secret values based on type."""
        import secrets as secrets_module

        new_data = current_data.copy()

        if cred_type == CredentialType.USER_PASS_KIND:
            return self._build_username_password_data(secret_data)
        elif cred_type == CredentialType.API_KEY_KIND:
            for key in ["api_key", "apikey", "key", "token", "value"]:
                if key in new_data:
                    new_data[key] = secrets_module.token_urlsafe(32)
                    break
            else:
                new_data["value"] = secrets_module.token_urlsafe(32)
        else:
            # For other types, try common password fields
            for key in ["password", "secret", "key", "value"]:
                if key in new_data:
                    new_data[key] = self._generate_password()
                    break

        return new_data

    def _generate_password(self, length: int = 32) -> str:
        """Generate a secure random password."""
        import secrets as secrets_module

        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        return "".join(secrets_module.choice(alphabet) for _ in range(length))

    def _infer_credential_type(self, content_type: str) -> CredentialType:
        """Infer credential type from Azure content type."""
        content_type_lower = content_type.lower()

        if "password" in content_type_lower:
            return CredentialType.USER_PASS_KIND
        if "api" in content_type_lower or "key" in content_type_lower:
            return CredentialType.API_KEY_KIND
        if "oauth" in content_type_lower or "token" in content_type_lower:
            return CredentialType.OAUTH2_TOKEN_KIND
        if "ssh" in content_type_lower:
            return CredentialType.SSH_KEY
        if "cert" in content_type_lower:
            return CredentialType.CERTIFICATE
        if "connection" in content_type_lower or "database" in content_type_lower:
            return CredentialType.DATABASE_CONNECTION
        if "aws" in content_type_lower:
            return CredentialType.AWS_CREDENTIALS
        if "azure" in content_type_lower:
            return CredentialType.AZURE_CREDENTIALS

        return CredentialType.CUSTOM_KIND

    def _credential_type_to_content_type(self, cred_type: CredentialType) -> str:
        """Convert credential type to Azure content type."""
        mapping = {
            CredentialType.USER_PASS_KIND: "application/x-password",
            CredentialType.API_KEY_KIND: "application/x-api-key",
            CredentialType.OAUTH2_TOKEN_KIND: "application/x-oauth-token",
            CredentialType.SSH_KEY: "application/x-ssh-key",
            CredentialType.CERTIFICATE: "application/x-pem-file",
            CredentialType.DATABASE_CONNECTION: "application/x-connection-string",
            CredentialType.AWS_CREDENTIALS: "application/x-aws-credentials",
            CredentialType.AZURE_CREDENTIALS: "application/x-azure-credentials",
            CredentialType.CUSTOM_KIND: "text/plain",
        }
        return mapping.get(cred_type, "text/plain")

    async def recover_deleted_secret(self, path: str) -> SecretMetadata:
        """
        Recover a soft-deleted secret in Azure Key Vault.

        Args:
            path: Secret name to recover

        Returns:
            SecretMetadata for recovered secret
        """
        client = self._ensure_connected()

        try:
            poller = client.begin_recover_deleted_secret(path)
            recovered = poller.result()

            logger.info(f"Recovered deleted secret: {path}")

            return SecretMetadata(
                path=path,
                version=1,
                created_at=recovered.properties.created_on or datetime.now(UTC),
                updated_at=recovered.properties.updated_on or datetime.now(UTC),
                credential_type=self._infer_credential_type(
                    recovered.properties.content_type or ""
                ),
            )

        except _ResourceNotFoundError as e:
            raise SecretNotFoundError(f"Deleted secret not found: {path}", path=path) from e
        except Exception as e:
            logger.error(f"Failed to recover secret {path}: {e}")
            raise

    async def purge_deleted_secret(self, path: str) -> bool:
        """
        Permanently delete a soft-deleted secret.

        Args:
            path: Secret name to purge

        Returns:
            True if purged successfully
        """
        client = self._ensure_connected()

        try:
            client.purge_deleted_secret(path)
            logger.info(f"Purged deleted secret: {path}")
            return True

        except _ResourceNotFoundError:
            return False
        except Exception as e:
            logger.error(f"Failed to purge secret {path}: {e}")
            raise
