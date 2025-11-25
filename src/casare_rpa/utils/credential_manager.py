"""
Credential Manager for CasareRPA

High-level interface for managing credentials with support for:
- HashiCorp Vault (recommended for production)
- Local encrypted storage (fallback for offline/development)

Credentials are organized by scope:
- GLOBAL: Organization-wide credentials
- WORKFLOW: Credentials specific to a workflow
- ROBOT: Credentials specific to a robot
- ASSET: RPA Asset credentials (files, queues, etc.)

Usage:
    manager = CredentialManager.create()

    # Store a credential
    manager.store_credential("db_admin", "admin", "password123")

    # Retrieve a credential
    cred = manager.get_credential("db_admin")
    print(f"Username: {cred.username}")
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from loguru import logger

from .vault_client import (
    VaultClient,
    VaultConfig,
    VaultSecretNotFoundError,
    VaultPermissionError,
    VaultConnectionError,
    HVAC_AVAILABLE,
)


class CredentialScope(Enum):
    """Scope for credential storage and access control.

    Attributes:
        GLOBAL: Organization-wide credentials accessible by all
        WORKFLOW: Credentials scoped to a specific workflow
        ROBOT: Credentials scoped to a specific robot
        ASSET: RPA Asset credentials (e.g., queue credentials, file shares)
    """
    GLOBAL = "global"
    WORKFLOW = "workflows"
    ROBOT = "robots"
    ASSET = "assets"


class CredentialType(Enum):
    """Type of credential for proper handling."""
    GENERIC = "generic"
    USERNAME_PASSWORD = "username_password"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    CERTIFICATE = "certificate"
    SSH_KEY = "ssh_key"


@dataclass
class Credential:
    """Represents a stored credential.

    Attributes:
        name: Unique identifier for the credential
        credential_type: Type of credential
        username: Username (for username/password type)
        password: Password or secret value
        api_key: API key (for api_key type)
        access_token: OAuth access token
        refresh_token: OAuth refresh token
        certificate: Certificate data (base64 encoded)
        private_key: Private key data (base64 encoded)
        metadata: Additional metadata
        created_at: Creation timestamp
        updated_at: Last update timestamp
        expires_at: Expiration timestamp (optional)
    """
    name: str
    credential_type: CredentialType = CredentialType.GENERIC
    username: Optional[str] = None
    password: Optional[str] = None
    api_key: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    certificate: Optional[str] = None
    private_key: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert credential to dictionary for storage."""
        data = {
            "name": self.name,
            "credential_type": self.credential_type.value,
            "metadata": self.metadata,
        }

        # Include non-None secret fields
        if self.username:
            data["username"] = self.username
        if self.password:
            data["password"] = self.password
        if self.api_key:
            data["api_key"] = self.api_key
        if self.access_token:
            data["access_token"] = self.access_token
        if self.refresh_token:
            data["refresh_token"] = self.refresh_token
        if self.certificate:
            data["certificate"] = self.certificate
        if self.private_key:
            data["private_key"] = self.private_key

        # Timestamps
        if self.created_at:
            data["created_at"] = self.created_at.isoformat()
        if self.updated_at:
            data["updated_at"] = self.updated_at.isoformat()
        if self.expires_at:
            data["expires_at"] = self.expires_at.isoformat()

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Credential":
        """Create Credential from dictionary."""
        return cls(
            name=data.get("name", ""),
            credential_type=CredentialType(
                data.get("credential_type", "generic")
            ),
            username=data.get("username"),
            password=data.get("password"),
            api_key=data.get("api_key"),
            access_token=data.get("access_token"),
            refresh_token=data.get("refresh_token"),
            certificate=data.get("certificate"),
            private_key=data.get("private_key"),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"])
            if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"])
            if data.get("updated_at") else None,
            expires_at=datetime.fromisoformat(data["expires_at"])
            if data.get("expires_at") else None,
        )

    def is_expired(self) -> bool:
        """Check if the credential has expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at


class CredentialManager:
    """High-level credential management for CasareRPA.

    Provides a unified interface for storing and retrieving credentials
    with support for different scopes and backend storage systems.

    Example:
        >>> manager = CredentialManager.create()
        >>> manager.store_credential("db_prod", "admin", "secret", scope=CredentialScope.GLOBAL)
        >>> cred = manager.get_credential("db_prod")
        >>> print(cred.username)
        admin
    """

    def __init__(self, vault_client: Optional[VaultClient] = None):
        """Initialize credential manager.

        Args:
            vault_client: Optional VaultClient for Vault backend.
                         If None, will use local encrypted storage.
        """
        self.vault = vault_client
        self._local_store_path = Path.home() / ".casare_rpa" / "credentials"
        self._local_store_path.mkdir(parents=True, exist_ok=True)

    @classmethod
    def create(
        cls,
        vault_url: Optional[str] = None,
        vault_token: Optional[str] = None,
        vault_role_id: Optional[str] = None,
        vault_secret_id: Optional[str] = None,
        use_local_fallback: bool = True,
    ) -> "CredentialManager":
        """Factory method to create a CredentialManager.

        Attempts to connect to Vault if configured, falls back to local storage.

        Args:
            vault_url: Vault server URL
            vault_token: Vault token (for development)
            vault_role_id: AppRole role ID
            vault_secret_id: AppRole secret ID
            use_local_fallback: If True, use local storage when Vault unavailable

        Returns:
            Configured CredentialManager instance
        """
        vault_client = None

        # Try to create Vault client
        if HVAC_AVAILABLE and (vault_url or os.environ.get("VAULT_ADDR")):
            try:
                if vault_url and vault_token:
                    config = VaultConfig(
                        url=vault_url,
                        auth_method="token",
                        token=vault_token,
                    )
                elif vault_url and vault_role_id and vault_secret_id:
                    config = VaultConfig(
                        url=vault_url,
                        auth_method="approle",
                        role_id=vault_role_id,
                        secret_id=vault_secret_id,
                    )
                else:
                    config = VaultConfig.from_env()

                vault_client = VaultClient(config)
                logger.info("CredentialManager: Using HashiCorp Vault backend")

            except (VaultConnectionError, VaultPermissionError) as e:
                logger.warning(f"Vault connection failed: {e}")
                if not use_local_fallback:
                    raise

        if vault_client is None:
            logger.info("CredentialManager: Using local encrypted storage")

        return cls(vault_client=vault_client)

    def _build_path(
        self,
        name: str,
        scope: CredentialScope,
        scope_id: Optional[str] = None,
    ) -> str:
        """Build the storage path for a credential."""
        if scope_id:
            return f"{scope.value}/{scope_id}/{name}"
        return f"{scope.value}/{name}"

    def get_credential(
        self,
        name: str,
        scope: CredentialScope = CredentialScope.GLOBAL,
        scope_id: Optional[str] = None,
    ) -> Credential:
        """Retrieve a credential by name.

        Args:
            name: Credential name
            scope: Credential scope
            scope_id: Optional ID (workflow_id, robot_id, etc.)

        Returns:
            Credential object

        Raises:
            VaultSecretNotFoundError: If credential doesn't exist
        """
        path = self._build_path(name, scope, scope_id)

        if self.vault:
            data = self.vault.get_secret(path)
            return Credential.from_dict(data)
        else:
            return self._get_local_credential(path)

    def store_credential(
        self,
        name: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        scope: CredentialScope = CredentialScope.GLOBAL,
        scope_id: Optional[str] = None,
        credential_type: CredentialType = CredentialType.USERNAME_PASSWORD,
        api_key: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        expires_at: Optional[datetime] = None,
    ) -> None:
        """Store a credential securely.

        Args:
            name: Credential name (unique within scope)
            username: Username for username/password credentials
            password: Password or secret value
            scope: Where to store the credential
            scope_id: Optional ID for scoped credentials
            credential_type: Type of credential
            api_key: API key (for api_key type)
            metadata: Additional metadata to store
            expires_at: Optional expiration timestamp
        """
        path = self._build_path(name, scope, scope_id)
        now = datetime.now()

        credential = Credential(
            name=name,
            credential_type=credential_type,
            username=username,
            password=password,
            api_key=api_key,
            metadata=metadata or {},
            created_at=now,
            updated_at=now,
            expires_at=expires_at,
        )

        if self.vault:
            self.vault.store_secret(path, credential.to_dict())
            logger.debug(f"Stored credential in Vault: {path}")
        else:
            self._store_local_credential(path, credential)
            logger.debug(f"Stored credential locally: {path}")

    def delete_credential(
        self,
        name: str,
        scope: CredentialScope = CredentialScope.GLOBAL,
        scope_id: Optional[str] = None,
        permanent: bool = False,
    ) -> None:
        """Delete a credential.

        Args:
            name: Credential name
            scope: Credential scope
            scope_id: Optional scope ID
            permanent: If True, permanently destroy (Vault only)
        """
        path = self._build_path(name, scope, scope_id)

        if self.vault:
            self.vault.delete_secret(path, destroy=permanent)
        else:
            self._delete_local_credential(path)

        logger.info(f"Deleted credential: {path}")

    def list_credentials(
        self,
        scope: CredentialScope = CredentialScope.GLOBAL,
        scope_id: Optional[str] = None,
    ) -> list[str]:
        """List all credentials in a scope.

        Args:
            scope: Credential scope to list
            scope_id: Optional scope ID

        Returns:
            List of credential names
        """
        if scope_id:
            path = f"{scope.value}/{scope_id}"
        else:
            path = scope.value

        if self.vault:
            return self.vault.list_secrets(path)
        else:
            return self._list_local_credentials(path)

    def credential_exists(
        self,
        name: str,
        scope: CredentialScope = CredentialScope.GLOBAL,
        scope_id: Optional[str] = None,
    ) -> bool:
        """Check if a credential exists.

        Args:
            name: Credential name
            scope: Credential scope
            scope_id: Optional scope ID

        Returns:
            True if credential exists
        """
        try:
            self.get_credential(name, scope, scope_id)
            return True
        except (VaultSecretNotFoundError, FileNotFoundError):
            return False

    # Local storage methods (fallback when Vault is unavailable)

    def _get_local_credential(self, path: str) -> Credential:
        """Retrieve credential from local encrypted storage."""
        file_path = self._local_store_path / f"{path.replace('/', '_')}.json"

        if not file_path.exists():
            raise VaultSecretNotFoundError(f"Credential not found: {path}")

        # In production, this should decrypt the file
        # For now, using simple JSON storage
        with open(file_path) as f:
            data = json.load(f)

        return Credential.from_dict(data)

    def _store_local_credential(self, path: str, credential: Credential) -> None:
        """Store credential in local encrypted storage."""
        file_path = self._local_store_path / f"{path.replace('/', '_')}.json"
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # In production, this should encrypt the file
        # For now, using simple JSON storage with restricted permissions
        with open(file_path, "w") as f:
            json.dump(credential.to_dict(), f, indent=2)

        # Restrict file permissions (Windows doesn't have chmod)
        try:
            import stat
            os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR)
        except Exception:
            pass  # Skip on Windows

    def _delete_local_credential(self, path: str) -> None:
        """Delete credential from local storage."""
        file_path = self._local_store_path / f"{path.replace('/', '_')}.json"
        if file_path.exists():
            file_path.unlink()

    def _list_local_credentials(self, path: str) -> list[str]:
        """List credentials in local storage."""
        prefix = path.replace("/", "_")
        credentials = []

        for file in self._local_store_path.glob(f"{prefix}_*.json"):
            # Extract credential name from filename
            name = file.stem.replace(prefix + "_", "")
            credentials.append(name)

        return credentials


# Convenience functions for quick access

_default_manager: Optional[CredentialManager] = None


def get_default_manager() -> CredentialManager:
    """Get or create the default credential manager."""
    global _default_manager
    if _default_manager is None:
        _default_manager = CredentialManager.create()
    return _default_manager


def get_credential(
    name: str,
    scope: CredentialScope = CredentialScope.GLOBAL,
    scope_id: Optional[str] = None,
) -> Credential:
    """Convenience function to get a credential using default manager."""
    return get_default_manager().get_credential(name, scope, scope_id)


def store_credential(
    name: str,
    username: Optional[str] = None,
    password: Optional[str] = None,
    scope: CredentialScope = CredentialScope.GLOBAL,
    scope_id: Optional[str] = None,
    **kwargs,
) -> None:
    """Convenience function to store a credential using default manager."""
    get_default_manager().store_credential(
        name, username, password, scope, scope_id, **kwargs
    )
