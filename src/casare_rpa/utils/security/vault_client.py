"""
HashiCorp Vault Client for CasareRPA

Provides secure credential storage and retrieval using HashiCorp Vault.
Supports multiple authentication methods: AppRole (recommended for Robot/Orchestrator),
Token (for development), and LDAP (for enterprise environments).

Usage:
    config = VaultConfig(
        url="https://vault.company.com",
        auth_method="approle",
        role_id="robot-role-id",
        secret_id="robot-secret-id"
    )
    client = VaultClient(config)
    secret = client.get_secret("database/prod")
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from loguru import logger

# Import hvac conditionally to allow graceful degradation
try:
    import hvac
    from hvac.exceptions import Forbidden, InvalidPath, VaultError

    HVAC_AVAILABLE = True
except ImportError:
    HVAC_AVAILABLE = False
    hvac = None


class VaultConnectionError(Exception):
    """Raised when unable to connect to Vault server."""

    pass


class VaultAuthenticationError(Exception):
    """Raised when authentication to Vault fails."""

    pass


class VaultSecretNotFoundError(Exception):
    """Raised when a secret is not found."""

    pass


class VaultPermissionError(Exception):
    """Raised when access to a secret is denied."""

    pass


@dataclass
class VaultConfig:
    """Configuration for HashiCorp Vault connection.

    Attributes:
        url: Vault server URL (e.g., https://vault.company.com:8200)
        namespace: Optional Vault namespace (for enterprise)
        auth_method: Authentication method (approle, token, ldap, kubernetes)
        role_id: AppRole role ID (for approle auth)
        secret_id: AppRole secret ID (for approle auth)
        token: Direct token (for token auth or development)
        ldap_username: LDAP username (for ldap auth)
        ldap_password: LDAP password (for ldap auth)
        kubernetes_role: Kubernetes role name (for kubernetes auth)
        verify_ssl: Whether to verify SSL certificates
        ca_cert: Path to CA certificate bundle
        timeout: Connection timeout in seconds
        mount_point: KV secrets engine mount point
    """

    url: str
    namespace: str | None = None
    auth_method: str = "approle"
    role_id: str | None = None
    secret_id: str | None = None
    token: str | None = None
    ldap_username: str | None = None
    ldap_password: str | None = None
    kubernetes_role: str | None = None
    verify_ssl: bool = True
    ca_cert: str | None = None
    timeout: int = 30
    mount_point: str = "casarerpa"

    @classmethod
    def from_env(cls) -> VaultConfig:
        """Create VaultConfig from environment variables.

        Environment variables:
            VAULT_ADDR: Vault server URL
            VAULT_NAMESPACE: Vault namespace (optional)
            VAULT_AUTH_METHOD: Auth method (default: approle)
            VAULT_ROLE_ID: AppRole role ID
            VAULT_SECRET_ID: AppRole secret ID
            VAULT_TOKEN: Direct token
            VAULT_CACERT: Path to CA certificate
            VAULT_SKIP_VERIFY: Set to "true" to skip SSL verification
        """
        return cls(
            url=os.environ.get("VAULT_ADDR", "http://localhost:8200"),
            namespace=os.environ.get("VAULT_NAMESPACE"),
            auth_method=os.environ.get("VAULT_AUTH_METHOD", "approle"),
            role_id=os.environ.get("VAULT_ROLE_ID"),
            secret_id=os.environ.get("VAULT_SECRET_ID"),
            token=os.environ.get("VAULT_TOKEN"),
            ca_cert=os.environ.get("VAULT_CACERT"),
            verify_ssl=os.environ.get("VAULT_SKIP_VERIFY", "").lower() != "true",
        )

    @classmethod
    def from_file(cls, config_path: Path) -> VaultConfig:
        """Load VaultConfig from a JSON configuration file."""
        import json

        with open(config_path) as f:
            data = json.load(f)

        vault_config = data.get("vault", data)
        return cls(
            url=vault_config.get("url", "http://localhost:8200"),
            namespace=vault_config.get("namespace"),
            auth_method=vault_config.get("auth_method", "approle"),
            role_id=vault_config.get("role_id"),
            secret_id=vault_config.get("secret_id"),
            token=vault_config.get("token"),
            ca_cert=vault_config.get("ca_cert"),
            verify_ssl=vault_config.get("verify_ssl", True),
            mount_point=vault_config.get("mount_point", "casarerpa"),
        )


class VaultClient:
    """HashiCorp Vault client for CasareRPA.

    Provides methods to securely store and retrieve secrets from Vault.
    Uses the KV v2 secrets engine by default.

    Example:
        >>> config = VaultConfig(url="https://vault.company.com", token="dev-token")
        >>> client = VaultClient(config)
        >>> client.store_secret("myapp/database", {"username": "admin", "password": "secret"})
        >>> creds = client.get_secret("myapp/database")
        >>> print(creds["username"])
        admin
    """

    def __init__(self, config: VaultConfig):
        """Initialize Vault client with configuration.

        Args:
            config: VaultConfig instance with connection details

        Raises:
            VaultConnectionError: If hvac library is not available
            VaultAuthenticationError: If authentication fails
        """
        if not HVAC_AVAILABLE:
            raise VaultConnectionError("hvac library not installed. Install with: pip install hvac")

        self.config = config
        self._client: hvac.Client | None = None
        self._authenticated = False

    @property
    def client(self) -> hvac.Client:
        """Get or create the authenticated Vault client."""
        if self._client is None or not self._authenticated:
            self._connect()
        return self._client

    def _connect(self) -> None:
        """Establish connection to Vault and authenticate."""
        try:
            verify = self.config.ca_cert if self.config.ca_cert else self.config.verify_ssl

            self._client = hvac.Client(
                url=self.config.url,
                namespace=self.config.namespace,
                verify=verify,
                timeout=self.config.timeout,
            )

            self._authenticate()

            if not self._client.is_authenticated():
                raise VaultAuthenticationError("Failed to authenticate to Vault")

            self._authenticated = True
            logger.info(f"Connected to Vault at {self.config.url}")

        except Exception as e:
            if isinstance(e, (VaultConnectionError, VaultAuthenticationError)):
                raise
            raise VaultConnectionError(f"Failed to connect to Vault: {e}")

    def _authenticate(self) -> None:
        """Authenticate to Vault using configured method."""
        method = self.config.auth_method.lower()

        try:
            if method == "approle":
                if not self.config.role_id or not self.config.secret_id:
                    raise VaultAuthenticationError("AppRole auth requires role_id and secret_id")
                self._client.auth.approle.login(
                    role_id=self.config.role_id,
                    secret_id=self.config.secret_id,
                )
                logger.debug("Authenticated via AppRole")

            elif method == "token":
                if not self.config.token:
                    raise VaultAuthenticationError("Token auth requires token")
                self._client.token = self.config.token
                logger.debug("Authenticated via Token")

            elif method == "ldap":
                if not self.config.ldap_username or not self.config.ldap_password:
                    raise VaultAuthenticationError(
                        "LDAP auth requires ldap_username and ldap_password"
                    )
                self._client.auth.ldap.login(
                    username=self.config.ldap_username,
                    password=self.config.ldap_password,
                )
                logger.debug("Authenticated via LDAP")

            elif method == "kubernetes":
                if not self.config.kubernetes_role:
                    raise VaultAuthenticationError("Kubernetes auth requires kubernetes_role")
                # Read JWT from service account
                jwt_path = "/var/run/secrets/kubernetes.io/serviceaccount/token"
                with open(jwt_path) as f:
                    jwt = f.read()
                self._client.auth.kubernetes.login(
                    role=self.config.kubernetes_role,
                    jwt=jwt,
                )
                logger.debug("Authenticated via Kubernetes")

            else:
                raise VaultAuthenticationError(f"Unsupported auth method: {method}")

        except FileNotFoundError as e:
            raise VaultAuthenticationError(f"Kubernetes JWT not found: {e}")
        except Exception as e:
            if isinstance(e, VaultAuthenticationError):
                raise
            raise VaultAuthenticationError(f"Authentication failed: {e}")

    def get_secret(self, path: str) -> dict[str, Any]:
        """Retrieve a secret from Vault KV v2 engine.

        Args:
            path: Secret path (e.g., "database/prod", "api/keys")

        Returns:
            Dictionary containing secret data

        Raises:
            VaultSecretNotFoundError: If secret doesn't exist
            VaultPermissionError: If access is denied
        """
        try:
            response = self.client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=self.config.mount_point,
            )
            return response["data"]["data"]

        except InvalidPath:
            raise VaultSecretNotFoundError(f"Secret not found: {path}")
        except Forbidden:
            raise VaultPermissionError(f"Access denied to secret: {path}")
        except Exception as e:
            logger.error(f"Error retrieving secret {path}: {e}")
            raise

    def store_secret(
        self,
        path: str,
        data: dict[str, Any],
        cas: int | None = None,
    ) -> dict[str, Any]:
        """Store a secret in Vault KV v2 engine.

        Args:
            path: Secret path
            data: Secret data as dictionary
            cas: Check-and-set version (optional, for concurrent write protection)

        Returns:
            Response metadata including version number

        Raises:
            VaultPermissionError: If write access is denied
        """
        try:
            response = self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=data,
                cas=cas,
                mount_point=self.config.mount_point,
            )
            logger.debug(f"Stored secret at {path}")
            return response.get("data", {})

        except Forbidden:
            raise VaultPermissionError(f"Write access denied to: {path}")
        except Exception as e:
            logger.error(f"Error storing secret {path}: {e}")
            raise

    def delete_secret(self, path: str, destroy: bool = False) -> None:
        """Delete a secret from Vault.

        Args:
            path: Secret path
            destroy: If True, permanently destroys all versions.
                    If False, soft-deletes (can be undeleted).
        """
        try:
            if destroy:
                self.client.secrets.kv.v2.delete_metadata_and_all_versions(
                    path=path,
                    mount_point=self.config.mount_point,
                )
                logger.info(f"Permanently destroyed secret: {path}")
            else:
                self.client.secrets.kv.v2.delete_latest_version_of_secret(
                    path=path,
                    mount_point=self.config.mount_point,
                )
                logger.debug(f"Soft-deleted secret: {path}")

        except Forbidden:
            raise VaultPermissionError(f"Delete access denied to: {path}")
        except Exception as e:
            logger.error(f"Error deleting secret {path}: {e}")
            raise

    def list_secrets(self, path: str = "") -> list[str]:
        """List secrets at a given path.

        Args:
            path: Path to list (empty for root of mount point)

        Returns:
            List of secret keys at the path
        """
        try:
            response = self.client.secrets.kv.v2.list_secrets(
                path=path,
                mount_point=self.config.mount_point,
            )
            return response.get("data", {}).get("keys", [])

        except InvalidPath:
            return []
        except Forbidden:
            raise VaultPermissionError(f"List access denied to: {path}")
        except Exception as e:
            logger.error(f"Error listing secrets at {path}: {e}")
            raise

    def get_secret_metadata(self, path: str) -> dict[str, Any]:
        """Get metadata for a secret (versions, creation time, etc.).

        Args:
            path: Secret path

        Returns:
            Metadata dictionary
        """
        try:
            response = self.client.secrets.kv.v2.read_secret_metadata(
                path=path,
                mount_point=self.config.mount_point,
            )
            return response.get("data", {})

        except InvalidPath:
            raise VaultSecretNotFoundError(f"Secret not found: {path}")
        except Forbidden:
            raise VaultPermissionError(f"Metadata access denied to: {path}")

    def is_connected(self) -> bool:
        """Check if the client is connected and authenticated."""
        try:
            return self._client is not None and self._client.is_authenticated()
        except Exception:
            return False

    def renew_token(self) -> None:
        """Renew the current authentication token."""
        try:
            self.client.auth.token.renew_self()
            logger.debug("Token renewed successfully")
        except Exception as e:
            logger.warning(f"Failed to renew token: {e}")
            # Re-authenticate on failure
            self._authenticated = False
            self._connect()


def create_vault_client(
    url: str | None = None,
    token: str | None = None,
    role_id: str | None = None,
    secret_id: str | None = None,
) -> VaultClient:
    """Factory function to create a Vault client.

    Uses provided parameters or falls back to environment variables.

    Args:
        url: Vault server URL
        token: Direct token (for development)
        role_id: AppRole role ID
        secret_id: AppRole secret ID

    Returns:
        Configured VaultClient instance
    """
    if url and token:
        config = VaultConfig(url=url, auth_method="token", token=token)
    elif url and role_id and secret_id:
        config = VaultConfig(
            url=url,
            auth_method="approle",
            role_id=role_id,
            secret_id=secret_id,
        )
    else:
        config = VaultConfig.from_env()

    return VaultClient(config)
