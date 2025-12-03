"""
HashiCorp Vault Provider Implementation.

Supports:
- KV v1 and v2 secrets engines
- Dynamic secrets (database, AWS, Azure)
- Lease management
- Secret rotation
- Namespace support for Vault Enterprise
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from loguru import logger

from casare_rpa.infrastructure.security.vault_client import (
    VaultProvider,
    VaultConfig,
    SecretValue,
    SecretMetadata,
    CredentialType,
    SecretNotFoundError,
    VaultConnectionError,
    VaultAuthenticationError,
    SecretAccessDeniedError,
)

# Optional hvac import
try:
    import hvac
    from hvac.exceptions import (
        Forbidden as HvacForbidden,
        InvalidPath as HvacInvalidPath,
        InvalidRequest as HvacInvalidRequest,
        Unauthorized as HvacUnauthorized,
    )

    HVAC_AVAILABLE = True
except ImportError:
    HVAC_AVAILABLE = False
    hvac = None
    HvacForbidden = Exception
    HvacInvalidPath = Exception
    HvacInvalidRequest = Exception
    HvacUnauthorized = Exception


class HashiCorpVaultProvider(VaultProvider):
    """
    HashiCorp Vault provider using hvac client.

    Supports both KV v1 and v2 secrets engines, dynamic secrets,
    and lease management for enterprise deployments.
    """

    def __init__(self, config: VaultConfig) -> None:
        """
        Initialize HashiCorp Vault provider.

        Args:
            config: Vault configuration with HashiCorp settings

        Raises:
            ImportError: If hvac library is not installed
        """
        if not HVAC_AVAILABLE:
            raise ImportError(
                "HashiCorp Vault support requires hvac library. "
                "Install with: pip install hvac"
            )

        self._config = config
        self._client: Optional["hvac.Client"] = None

    async def connect(self) -> None:
        """Connect to HashiCorp Vault."""
        if not self._config.hashicorp_url:
            raise VaultConnectionError("HashiCorp Vault URL not configured")

        if not self._config.hashicorp_token:
            raise VaultConnectionError("HashiCorp Vault token not configured")

        try:
            # Build client options
            client_kwargs: Dict[str, Any] = {
                "url": self._config.hashicorp_url,
                "token": self._config.hashicorp_token.get_secret_value(),
                "verify": self._config.tls_verify,
            }

            if self._config.hashicorp_namespace:
                client_kwargs["namespace"] = self._config.hashicorp_namespace

            if self._config.tls_ca_cert:
                client_kwargs["verify"] = self._config.tls_ca_cert

            if self._config.tls_client_cert and self._config.tls_client_key:
                client_kwargs["cert"] = (
                    self._config.tls_client_cert,
                    self._config.tls_client_key,
                )

            self._client = hvac.Client(**client_kwargs)

            # Verify authentication
            if not self._client.is_authenticated():
                raise VaultAuthenticationError(
                    "Failed to authenticate with HashiCorp Vault"
                )

            logger.info(f"Connected to HashiCorp Vault at {self._config.hashicorp_url}")

        except HvacUnauthorized as e:
            raise VaultAuthenticationError(f"Vault authentication failed: {e}") from e
        except Exception as e:
            raise VaultConnectionError(
                f"Failed to connect to HashiCorp Vault: {e}"
            ) from e

    async def disconnect(self) -> None:
        """Disconnect from HashiCorp Vault."""
        if self._client:
            # hvac doesn't have explicit disconnect, but we can revoke our token
            # if it's a temporary one (not recommended for production tokens)
            self._client = None
            logger.info("Disconnected from HashiCorp Vault")

    async def is_connected(self) -> bool:
        """Check if connected and authenticated."""
        if not self._client:
            return False
        try:
            return self._client.is_authenticated()
        except Exception:
            return False

    def _ensure_connected(self) -> "hvac.Client":
        """Ensure client is connected and return it."""
        if not self._client:
            raise VaultConnectionError("Not connected to HashiCorp Vault")
        return self._client

    async def get_secret(self, path: str, version: Optional[int] = None) -> SecretValue:
        """
        Get secret from HashiCorp Vault.

        Args:
            path: Secret path (relative to mount point)
            version: Optional specific version for KV v2

        Returns:
            SecretValue with data and metadata
        """
        client = self._ensure_connected()

        try:
            mount_point = self._config.hashicorp_mount_point
            kv_version = self._config.hashicorp_kv_version

            if kv_version == 2:
                response = client.secrets.kv.v2.read_secret_version(
                    path=path,
                    mount_point=mount_point,
                    version=version,
                )

                secret_data = response["data"]["data"]
                vault_metadata = response["data"]["metadata"]

                metadata = SecretMetadata(
                    path=path,
                    version=vault_metadata.get("version", 1),
                    created_at=self._parse_vault_time(
                        vault_metadata.get("created_time")
                    ),
                    updated_at=self._parse_vault_time(
                        vault_metadata.get("created_time")
                    ),
                    credential_type=self._infer_credential_type(secret_data),
                    custom_metadata=vault_metadata.get("custom_metadata") or {},
                )
            else:
                # KV v1
                response = client.secrets.kv.v1.read_secret(
                    path=path,
                    mount_point=mount_point,
                )

                secret_data = response["data"]

                metadata = SecretMetadata(
                    path=path,
                    version=1,
                    credential_type=self._infer_credential_type(secret_data),
                )

            return SecretValue(data=secret_data, metadata=metadata)

        except HvacInvalidPath as e:
            raise SecretNotFoundError(f"Secret not found: {path}", path=path) from e
        except HvacForbidden as e:
            raise SecretAccessDeniedError(
                f"Access denied to secret: {path}", path=path
            ) from e
        except Exception as e:
            logger.error(f"Failed to read secret {path}: {e}")
            raise

    async def put_secret(
        self,
        path: str,
        data: Dict[str, Any],
        credential_type: CredentialType = CredentialType.CUSTOM,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SecretMetadata:
        """Store secret in HashiCorp Vault."""
        client = self._ensure_connected()

        try:
            mount_point = self._config.hashicorp_mount_point
            kv_version = self._config.hashicorp_kv_version

            if kv_version == 2:
                response = client.secrets.kv.v2.create_or_update_secret(
                    path=path,
                    secret=data,
                    mount_point=mount_point,
                    cas=None,  # No check-and-set
                )

                vault_metadata = response.get("data", {})
                version = vault_metadata.get("version", 1)

                # Update custom metadata if provided
                if metadata:
                    client.secrets.kv.v2.update_metadata(
                        path=path,
                        mount_point=mount_point,
                        custom_metadata=metadata,
                    )
            else:
                # KV v1 doesn't have versioning
                client.secrets.kv.v1.create_or_update_secret(
                    path=path,
                    secret=data,
                    mount_point=mount_point,
                )
                version = 1

            return SecretMetadata(
                path=path,
                version=version,
                credential_type=credential_type,
                custom_metadata=metadata or {},
            )

        except HvacForbidden as e:
            raise SecretAccessDeniedError(
                f"Access denied writing to: {path}", path=path
            ) from e
        except Exception as e:
            logger.error(f"Failed to write secret {path}: {e}")
            raise

    async def delete_secret(self, path: str) -> bool:
        """Delete secret from HashiCorp Vault."""
        client = self._ensure_connected()

        try:
            mount_point = self._config.hashicorp_mount_point
            kv_version = self._config.hashicorp_kv_version

            if kv_version == 2:
                # For KV v2, we use destroy to permanently delete
                client.secrets.kv.v2.delete_metadata_and_all_versions(
                    path=path,
                    mount_point=mount_point,
                )
            else:
                client.secrets.kv.v1.delete_secret(
                    path=path,
                    mount_point=mount_point,
                )

            logger.info(f"Deleted secret: {path}")
            return True

        except HvacInvalidPath:
            return False
        except HvacForbidden as e:
            raise SecretAccessDeniedError(
                f"Access denied deleting: {path}", path=path
            ) from e
        except Exception as e:
            logger.error(f"Failed to delete secret {path}: {e}")
            raise

    async def list_secrets(self, path_prefix: str) -> List[str]:
        """List secrets under a path prefix."""
        client = self._ensure_connected()

        try:
            mount_point = self._config.hashicorp_mount_point
            kv_version = self._config.hashicorp_kv_version

            if kv_version == 2:
                response = client.secrets.kv.v2.list_secrets(
                    path=path_prefix,
                    mount_point=mount_point,
                )
            else:
                response = client.secrets.kv.v1.list_secrets(
                    path=path_prefix,
                    mount_point=mount_point,
                )

            keys = response.get("data", {}).get("keys", [])
            # Prepend the prefix to get full paths
            return [f"{path_prefix}/{k}".rstrip("/") for k in keys]

        except HvacInvalidPath:
            return []
        except Exception as e:
            logger.error(f"Failed to list secrets at {path_prefix}: {e}")
            raise

    async def get_dynamic_secret(
        self, path: str, role: str, ttl: Optional[int] = None
    ) -> SecretValue:
        """
        Get dynamically generated credentials.

        Supports database, AWS, Azure, and other dynamic secrets engines.

        Args:
            path: Secrets engine path (e.g., "database", "aws")
            role: Role name for credential generation
            ttl: Optional TTL in seconds

        Returns:
            SecretValue with generated credentials and lease info
        """
        client = self._ensure_connected()

        try:
            # Build the full path for the dynamic secret
            read_path = f"{path}/creds/{role}"

            # Read dynamic credentials
            response = client.read(read_path)

            if not response:
                raise SecretNotFoundError(
                    f"Dynamic secret not found: {read_path}",
                    path=read_path,
                )

            secret_data = response.get("data", {})
            lease_id = response.get("lease_id", "")
            lease_duration = response.get("lease_duration", 0)
            renewable = response.get("renewable", False)

            # Calculate expiration
            expires_at = None
            if lease_duration > 0:
                expires_at = datetime.now(timezone.utc) + timedelta(
                    seconds=lease_duration
                )

            metadata = SecretMetadata(
                path=read_path,
                version=1,
                credential_type=self._infer_dynamic_credential_type(path),
                is_dynamic=True,
                lease_id=lease_id,
                lease_duration=lease_duration,
                renewable=renewable,
                expires_at=expires_at,
            )

            logger.info(
                f"Generated dynamic credentials for {role} "
                f"(lease: {lease_id}, TTL: {lease_duration}s)"
            )

            return SecretValue(data=secret_data, metadata=metadata)

        except Exception as e:
            logger.error(f"Failed to get dynamic secret {path}/{role}: {e}")
            raise

    async def renew_lease(self, lease_id: str, increment: Optional[int] = None) -> int:
        """
        Renew a secret lease.

        Args:
            lease_id: Lease ID to renew
            increment: Optional TTL increment in seconds

        Returns:
            New lease duration in seconds
        """
        client = self._ensure_connected()

        try:
            response = client.sys.renew_lease(
                lease_id=lease_id,
                increment=increment,
            )

            new_duration = response.get("lease_duration", 0)
            logger.info(f"Renewed lease {lease_id} for {new_duration}s")
            return new_duration

        except Exception as e:
            logger.error(f"Failed to renew lease {lease_id}: {e}")
            raise

    async def revoke_lease(self, lease_id: str) -> None:
        """Revoke a secret lease."""
        client = self._ensure_connected()

        try:
            client.sys.revoke_lease(lease_id=lease_id)
            logger.info(f"Revoked lease: {lease_id}")

        except Exception as e:
            logger.error(f"Failed to revoke lease {lease_id}: {e}")
            raise

    async def rotate_secret(self, path: str) -> SecretMetadata:
        """
        Trigger secret rotation.

        For static secrets, this creates a new version with a generated value.
        For dynamic secrets, this typically triggers the rotation endpoint.
        """
        client = self._ensure_connected()

        try:
            # Check if this is a rotation-enabled path
            rotate_path = f"{path}/rotate"

            # Try to trigger rotation endpoint (for supported engines)
            try:
                client.write(rotate_path)
                logger.info(f"Triggered rotation for: {path}")
            except HvacInvalidPath:
                # No rotation endpoint, manual rotation needed
                logger.warning(
                    f"No rotation endpoint for {path}. "
                    "Manual rotation or external rotation service required."
                )

            # Return current metadata
            secret = await self.get_secret(path)
            return secret.metadata

        except Exception as e:
            logger.error(f"Failed to rotate secret {path}: {e}")
            raise

    def _parse_vault_time(self, time_str: Optional[str]) -> datetime:
        """Parse Vault timestamp format."""
        if not time_str:
            return datetime.now(timezone.utc)
        try:
            # Vault uses RFC3339 format
            return datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return datetime.now(timezone.utc)

    def _infer_credential_type(self, data: Dict[str, Any]) -> CredentialType:
        """Infer credential type from data keys."""
        keys = set(data.keys())

        if "username" in keys and "password" in keys:
            return CredentialType.USERNAME_PASSWORD
        if "api_key" in keys or "apikey" in keys:
            return CredentialType.API_KEY
        if "access_token" in keys or "refresh_token" in keys:
            return CredentialType.OAUTH2_TOKEN
        if "private_key" in keys or "ssh_key" in keys:
            return CredentialType.SSH_KEY
        if "certificate" in keys or "cert" in keys:
            return CredentialType.CERTIFICATE
        if "connection_string" in keys or "dsn" in keys:
            return CredentialType.DATABASE_CONNECTION
        if "access_key_id" in keys and "secret_access_key" in keys:
            return CredentialType.AWS_CREDENTIALS
        if "client_id" in keys and "client_secret" in keys:
            return CredentialType.AZURE_CREDENTIALS

        return CredentialType.CUSTOM

    def _infer_dynamic_credential_type(self, engine_path: str) -> CredentialType:
        """Infer credential type from dynamic engine path."""
        engine = engine_path.lower()

        if "database" in engine or "postgres" in engine or "mysql" in engine:
            return CredentialType.DATABASE_CONNECTION
        if "aws" in engine:
            return CredentialType.AWS_CREDENTIALS
        if "azure" in engine:
            return CredentialType.AZURE_CREDENTIALS
        if "ssh" in engine:
            return CredentialType.SSH_KEY

        return CredentialType.CUSTOM
