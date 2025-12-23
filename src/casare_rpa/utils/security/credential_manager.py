"""
Credential Manager for CasareRPA

SECURITY: This module enforces HashiCorp Vault for ALL credential storage.
Local storage has been disabled for security reasons.

Credentials are organized by scope:
- GLOBAL: Organization-wide credentials
- WORKFLOW: Credentials specific to a workflow
- ROBOT: Credentials specific to a robot
- ASSET: RPA Asset credentials (files, queues, etc.)

Setup Requirements:
    1. Install HashiCorp Vault: https://www.vaultproject.io/downloads
    2. Configure environment variables:
       - VAULT_ADDR: Vault server URL (e.g., http://127.0.0.1:8200)
       - VAULT_TOKEN: Authentication token
       Or use AppRole auth:
       - VAULT_ROLE_ID: AppRole role ID
       - VAULT_SECRET_ID: AppRole secret ID

Usage:
    manager = CredentialManager.create()

    # Store a credential
    manager.store_credential("db_admin", "admin", "password123")

    # Retrieve a credential
    cred = manager.get_credential("db_admin")
    print(f"Username: {cred.username}")
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from loguru import logger

from casare_rpa.utils.security.vault_client import (
    HVAC_AVAILABLE,
    VaultClient,
    VaultConfig,
    VaultConnectionError,
    VaultPermissionError,
    VaultSecretNotFoundError,
)


class CredentialScope(Enum):
    """Scope for credential storage and access control.

    Attributes:
        GLOBAL: Organization-wide credentials accessible by all
        PROJECT: Credentials scoped to a specific project
        WORKFLOW: Credentials scoped to a specific workflow/scenario
        ROBOT: Credentials scoped to a specific robot
        ASSET: RPA Asset credentials (e.g., queue credentials, file shares)
    """

    GLOBAL = "global"
    PROJECT = "projects"
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
    # Messaging integrations
    TELEGRAM_BOT = "telegram_bot"
    WHATSAPP_BUSINESS = "whatsapp_business"


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
        bot_token: Telegram bot token (from @BotFather)
        phone_number_id: WhatsApp Business phone number ID
        business_account_id: WhatsApp Business account ID
        verify_token: Webhook verification token (for Meta webhooks)
        metadata: Additional metadata
        created_at: Creation timestamp
        updated_at: Last update timestamp
        expires_at: Expiration timestamp (optional)
    """

    name: str
    credential_type: CredentialType = CredentialType.GENERIC
    username: str | None = None
    password: str | None = None
    api_key: str | None = None
    access_token: str | None = None
    refresh_token: str | None = None
    certificate: str | None = None
    private_key: str | None = None
    # Messaging integrations
    bot_token: str | None = None
    phone_number_id: str | None = None
    business_account_id: str | None = None
    verify_token: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    expires_at: datetime | None = None

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
        # Messaging integration fields
        if self.bot_token:
            data["bot_token"] = self.bot_token
        if self.phone_number_id:
            data["phone_number_id"] = self.phone_number_id
        if self.business_account_id:
            data["business_account_id"] = self.business_account_id
        if self.verify_token:
            data["verify_token"] = self.verify_token

        # Timestamps
        if self.created_at:
            data["created_at"] = self.created_at.isoformat()
        if self.updated_at:
            data["updated_at"] = self.updated_at.isoformat()
        if self.expires_at:
            data["expires_at"] = self.expires_at.isoformat()

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Credential:
        """Create Credential from dictionary."""
        return cls(
            name=data.get("name", ""),
            credential_type=CredentialType(data.get("credential_type", "generic")),
            username=data.get("username"),
            password=data.get("password"),
            api_key=data.get("api_key"),
            access_token=data.get("access_token"),
            refresh_token=data.get("refresh_token"),
            certificate=data.get("certificate"),
            private_key=data.get("private_key"),
            # Messaging integration fields
            bot_token=data.get("bot_token"),
            phone_number_id=data.get("phone_number_id"),
            business_account_id=data.get("business_account_id"),
            verify_token=data.get("verify_token"),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else None,
            updated_at=datetime.fromisoformat(data["updated_at"])
            if data.get("updated_at")
            else None,
            expires_at=datetime.fromisoformat(data["expires_at"])
            if data.get("expires_at")
            else None,
        )

    def is_expired(self) -> bool:
        """Check if the credential has expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at


class VaultRequiredError(Exception):
    """Raised when Vault is required but not available."""

    pass


class CredentialManager:
    """High-level credential management for CasareRPA.

    SECURITY: This manager REQUIRES HashiCorp Vault for all credential operations.
    Local storage has been disabled for security reasons.

    Provides a unified interface for storing and retrieving credentials
    with support for different scopes.

    Example:
        >>> manager = CredentialManager.create()
        >>> manager.store_credential("db_prod", "admin", "secret", scope=CredentialScope.GLOBAL)
        >>> cred = manager.get_credential("db_prod")
        >>> print(cred.username)
        admin
    """

    def __init__(self, vault_client: VaultClient):
        """Initialize credential manager.

        Args:
            vault_client: VaultClient for Vault backend (REQUIRED).

        Raises:
            VaultRequiredError: If vault_client is None.
        """
        if vault_client is None:
            raise VaultRequiredError(
                "HashiCorp Vault is REQUIRED for credential management. "
                "Local storage has been disabled for security reasons. "
                "Please configure Vault by setting VAULT_ADDR and VAULT_TOKEN "
                "(or VAULT_ROLE_ID and VAULT_SECRET_ID for AppRole auth) "
                "environment variables."
            )
        self.vault = vault_client
        logger.info("CredentialManager initialized with Vault backend")

    @classmethod
    def create(
        cls,
        vault_url: str | None = None,
        vault_token: str | None = None,
        vault_role_id: str | None = None,
        vault_secret_id: str | None = None,
    ) -> CredentialManager:
        """Factory method to create a CredentialManager.

        SECURITY: This method REQUIRES HashiCorp Vault. Local storage is disabled.

        Args:
            vault_url: Vault server URL (or set VAULT_ADDR env var)
            vault_token: Vault token (or set VAULT_TOKEN env var)
            vault_role_id: AppRole role ID (or set VAULT_ROLE_ID env var)
            vault_secret_id: AppRole secret ID (or set VAULT_SECRET_ID env var)

        Returns:
            Configured CredentialManager instance

        Raises:
            VaultRequiredError: If Vault is not configured or unavailable
            VaultConnectionError: If connection to Vault fails
        """
        # SECURITY: Check if hvac library is available
        if not HVAC_AVAILABLE:
            raise VaultRequiredError(
                "HashiCorp Vault client library (hvac) is not installed. "
                "Install it with: pip install hvac"
            )

        # Check for Vault configuration
        vault_addr = vault_url or os.environ.get("VAULT_ADDR")
        if not vault_addr:
            raise VaultRequiredError(
                "Vault is REQUIRED but not configured. "
                "Set VAULT_ADDR environment variable or pass vault_url parameter. "
                "Example: VAULT_ADDR=http://127.0.0.1:8200"
            )

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
            logger.info(f"CredentialManager: Connected to Vault at {vault_addr}")

            return cls(vault_client=vault_client)

        except VaultConnectionError as e:
            raise VaultRequiredError(
                f"Failed to connect to Vault at {vault_addr}: {e}. "
                "Ensure Vault is running and accessible."
            ) from e
        except VaultPermissionError as e:
            raise VaultRequiredError(
                f"Vault authentication failed: {e}. "
                "Check your VAULT_TOKEN or AppRole credentials."
            ) from e

    def _build_path(
        self,
        name: str,
        scope: CredentialScope,
        scope_id: str | None = None,
    ) -> str:
        """Build the storage path for a credential."""
        if scope_id:
            return f"{scope.value}/{scope_id}/{name}"
        return f"{scope.value}/{name}"

    def get_credential(
        self,
        name: str,
        scope: CredentialScope = CredentialScope.GLOBAL,
        scope_id: str | None = None,
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

        # SECURITY: Audit log credential access
        logger.info(f"Credential access: {path}")

        data = self.vault.get_secret(path)
        credential = Credential.from_dict(data)

        # Check for expiration
        if credential.is_expired():
            logger.warning(f"Credential '{name}' has expired")

        return credential

    def store_credential(
        self,
        name: str,
        username: str | None = None,
        password: str | None = None,
        scope: CredentialScope = CredentialScope.GLOBAL,
        scope_id: str | None = None,
        credential_type: CredentialType = CredentialType.USERNAME_PASSWORD,
        api_key: str | None = None,
        metadata: dict[str, Any] | None = None,
        expires_at: datetime | None = None,
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

        self.vault.store_secret(path, credential.to_dict())
        # SECURITY: Audit log credential storage
        logger.info(f"Credential stored: {path} (type={credential_type.value})")

    def delete_credential(
        self,
        name: str,
        scope: CredentialScope = CredentialScope.GLOBAL,
        scope_id: str | None = None,
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

        self.vault.delete_secret(path, destroy=permanent)
        # SECURITY: Audit log credential deletion
        logger.info(f"Credential deleted: {path} (permanent={permanent})")

    def list_credentials(
        self,
        scope: CredentialScope = CredentialScope.GLOBAL,
        scope_id: str | None = None,
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

        return self.vault.list_secrets(path)

    def credential_exists(
        self,
        name: str,
        scope: CredentialScope = CredentialScope.GLOBAL,
        scope_id: str | None = None,
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

    # =========================================================================
    # Messaging Integration Helpers
    # =========================================================================

    def store_telegram_credential(
        self,
        name: str,
        bot_token: str,
        scope: CredentialScope = CredentialScope.GLOBAL,
        scope_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Store Telegram bot credentials.

        Args:
            name: Credential name (e.g., "my_telegram_bot")
            bot_token: Bot token from @BotFather
            scope: Credential scope
            scope_id: Optional scope ID
            metadata: Additional metadata (e.g., bot_username)
        """
        path = self._build_path(name, scope, scope_id)
        now = datetime.now()

        credential = Credential(
            name=name,
            credential_type=CredentialType.TELEGRAM_BOT,
            bot_token=bot_token,
            metadata=metadata or {},
            created_at=now,
            updated_at=now,
        )

        self.vault.store_secret(path, credential.to_dict())
        logger.info(f"Telegram credential stored: {path}")

    def store_whatsapp_credential(
        self,
        name: str,
        access_token: str,
        phone_number_id: str,
        business_account_id: str | None = None,
        verify_token: str | None = None,
        scope: CredentialScope = CredentialScope.GLOBAL,
        scope_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Store WhatsApp Business credentials.

        Args:
            name: Credential name (e.g., "my_whatsapp_business")
            access_token: Meta Business permanent access token
            phone_number_id: WhatsApp Business phone number ID
            business_account_id: Optional business account ID (for media uploads)
            verify_token: Optional webhook verification token
            scope: Credential scope
            scope_id: Optional scope ID
            metadata: Additional metadata
        """
        path = self._build_path(name, scope, scope_id)
        now = datetime.now()

        credential = Credential(
            name=name,
            credential_type=CredentialType.WHATSAPP_BUSINESS,
            access_token=access_token,
            phone_number_id=phone_number_id,
            business_account_id=business_account_id,
            verify_token=verify_token,
            metadata=metadata or {},
            created_at=now,
            updated_at=now,
        )

        self.vault.store_secret(path, credential.to_dict())
        logger.info(f"WhatsApp credential stored: {path}")

    def get_telegram_credential(
        self,
        name: str,
        scope: CredentialScope = CredentialScope.GLOBAL,
        scope_id: str | None = None,
    ) -> Credential:
        """Get Telegram bot credentials.

        Args:
            name: Credential name
            scope: Credential scope
            scope_id: Optional scope ID

        Returns:
            Credential with bot_token populated

        Raises:
            VaultSecretNotFoundError: If credential doesn't exist
        """
        credential = self.get_credential(name, scope, scope_id)
        if credential.credential_type != CredentialType.TELEGRAM_BOT:
            logger.warning(
                f"Credential '{name}' is type {credential.credential_type.value}, "
                "expected telegram_bot"
            )
        return credential

    def get_whatsapp_credential(
        self,
        name: str,
        scope: CredentialScope = CredentialScope.GLOBAL,
        scope_id: str | None = None,
    ) -> Credential:
        """Get WhatsApp Business credentials.

        Args:
            name: Credential name
            scope: Credential scope
            scope_id: Optional scope ID

        Returns:
            Credential with access_token, phone_number_id populated

        Raises:
            VaultSecretNotFoundError: If credential doesn't exist
        """
        credential = self.get_credential(name, scope, scope_id)
        if credential.credential_type != CredentialType.WHATSAPP_BUSINESS:
            logger.warning(
                f"Credential '{name}' is type {credential.credential_type.value}, "
                "expected whatsapp_business"
            )
        return credential

    # NOTE: Local storage methods have been REMOVED for security reasons.
    # All credential storage now requires HashiCorp Vault.


# Convenience functions for quick access
# NOTE: These functions REQUIRE HashiCorp Vault to be configured.
# Set VAULT_ADDR and VAULT_TOKEN environment variables before use.

_default_manager: CredentialManager | None = None


def get_default_manager() -> CredentialManager:
    """Get or create the default credential manager.

    SECURITY: Requires HashiCorp Vault to be configured.

    Raises:
        VaultRequiredError: If Vault is not configured
    """
    global _default_manager
    if _default_manager is None:
        _default_manager = CredentialManager.create()
    return _default_manager


def get_credential(
    name: str,
    scope: CredentialScope = CredentialScope.GLOBAL,
    scope_id: str | None = None,
) -> Credential:
    """Convenience function to get a credential using default manager.

    SECURITY: Requires HashiCorp Vault to be configured.

    Raises:
        VaultRequiredError: If Vault is not configured
        VaultSecretNotFoundError: If credential doesn't exist
    """
    return get_default_manager().get_credential(name, scope, scope_id)


def store_credential(
    name: str,
    username: str | None = None,
    password: str | None = None,
    scope: CredentialScope = CredentialScope.GLOBAL,
    scope_id: str | None = None,
    **kwargs,
) -> None:
    """Convenience function to store a credential using default manager.

    SECURITY: Requires HashiCorp Vault to be configured.

    Raises:
        VaultRequiredError: If Vault is not configured
    """
    get_default_manager().store_credential(name, username, password, scope, scope_id, **kwargs)
