"""
Vault Provider Factory.

Creates the appropriate vault provider based on configuration.
Handles automatic fallback when optional dependencies are missing.
"""

from loguru import logger

from casare_rpa.infrastructure.security.vault_client import (
    VaultBackend,
    VaultConfig,
    VaultConnectionError,
    VaultProvider,
)


def create_vault_provider(
    config: VaultConfig,
    fallback_to_sqlite: bool = True,
) -> VaultProvider:
    """
    Create a vault provider based on configuration.

    Args:
        config: Vault configuration
        fallback_to_sqlite: If True, fall back to SQLite when
                           the configured backend is unavailable

    Returns:
        Appropriate VaultProvider instance

    Raises:
        VaultConnectionError: If no provider can be created
        ImportError: If required dependencies are missing and no fallback
    """
    backend = config.backend
    last_error: Exception | None = None

    # Try the configured backend first
    if backend == VaultBackend.HASHICORP:
        try:
            from .hashicorp import HashiCorpVaultProvider

            logger.debug("Creating HashiCorp Vault provider")
            return HashiCorpVaultProvider(config)
        except ImportError as e:
            last_error = e
            logger.warning(
                f"HashiCorp Vault provider unavailable: {e}. Install with: pip install hvac"
            )

    elif backend == VaultBackend.SUPABASE:
        try:
            from .supabase_vault import SupabaseVaultProvider

            logger.debug("Creating Supabase Vault provider")
            return SupabaseVaultProvider(config)
        except ImportError as e:
            last_error = e
            logger.warning(
                f"Supabase Vault provider unavailable: {e}. Install with: pip install asyncpg"
            )

    elif backend == VaultBackend.SQLITE:
        try:
            from .sqlite_vault import EncryptedSQLiteProvider

            logger.debug("Creating SQLite Vault provider")
            return EncryptedSQLiteProvider(config)
        except ImportError as e:
            last_error = e
            logger.warning(
                f"SQLite Vault provider unavailable: {e}. "
                f"Install with: pip install aiosqlite cryptography"
            )

    elif backend == VaultBackend.AZURE_KEYVAULT:
        try:
            from .azure_keyvault import AzureKeyVaultProvider

            logger.debug("Creating Azure Key Vault provider")
            return AzureKeyVaultProvider(config)
        except ImportError as e:
            last_error = e
            logger.warning(
                f"Azure Key Vault provider unavailable: {e}. "
                f"Install with: pip install azure-identity azure-keyvault-secrets"
            )

    elif backend == VaultBackend.AWS_SECRETS_MANAGER:
        try:
            from .aws_secrets import AWSSecretsManagerProvider

            logger.debug("Creating AWS Secrets Manager provider")
            return AWSSecretsManagerProvider(config)
        except ImportError as e:
            last_error = e
            logger.warning(
                f"AWS Secrets Manager provider unavailable: {e}. Install with: pip install boto3"
            )

    # Fallback to SQLite if configured backend unavailable
    if fallback_to_sqlite and backend != VaultBackend.SQLITE:
        try:
            from .sqlite_vault import EncryptedSQLiteProvider

            logger.warning(
                f"Falling back to SQLite vault. "
                f"Configured backend ({backend.value}) is unavailable."
            )
            return EncryptedSQLiteProvider(config)
        except ImportError as e:
            logger.error(f"SQLite fallback also unavailable: {e}")

    # No provider available
    error_msg = (
        f"Failed to create vault provider for backend '{backend.value}'. Last error: {last_error}"
    )
    raise VaultConnectionError(error_msg)


def get_available_backends() -> dict[VaultBackend, bool]:
    """
    Check which vault backends are available.

    Returns:
        Dictionary mapping backend to availability status
    """
    available = {}

    # Check HashiCorp Vault
    try:
        import hvac  # noqa: F401

        available[VaultBackend.HASHICORP] = True
    except ImportError:
        available[VaultBackend.HASHICORP] = False

    # Check Supabase
    try:
        import asyncpg  # noqa: F401

        available[VaultBackend.SUPABASE] = True
    except ImportError:
        available[VaultBackend.SUPABASE] = False

    # Check SQLite
    try:
        import aiosqlite  # noqa: F401
        from cryptography.fernet import Fernet  # noqa: F401

        available[VaultBackend.SQLITE] = True
    except ImportError:
        available[VaultBackend.SQLITE] = False

    # Check Azure Key Vault
    try:
        from azure.identity import DefaultAzureCredential  # noqa: F401
        from azure.keyvault.secrets import SecretClient  # noqa: F401

        available[VaultBackend.AZURE_KEYVAULT] = True
    except ImportError:
        available[VaultBackend.AZURE_KEYVAULT] = False

    # Check AWS Secrets Manager
    try:
        import boto3  # noqa: F401

        available[VaultBackend.AWS_SECRETS_MANAGER] = True
    except ImportError:
        available[VaultBackend.AWS_SECRETS_MANAGER] = False

    return available


def get_recommended_backend() -> VaultBackend:
    """
    Get the recommended vault backend based on available dependencies.

    Priority (enterprise to development):
    1. HashiCorp Vault (enterprise standard)
    2. Azure Key Vault (Azure cloud)
    3. AWS Secrets Manager (AWS cloud)
    4. Supabase Vault (managed cloud)
    5. SQLite (local development)

    Returns:
        Recommended VaultBackend
    """
    available = get_available_backends()

    if available.get(VaultBackend.HASHICORP):
        return VaultBackend.HASHICORP
    if available.get(VaultBackend.AZURE_KEYVAULT):
        return VaultBackend.AZURE_KEYVAULT
    if available.get(VaultBackend.AWS_SECRETS_MANAGER):
        return VaultBackend.AWS_SECRETS_MANAGER
    if available.get(VaultBackend.SUPABASE):
        return VaultBackend.SUPABASE
    if available.get(VaultBackend.SQLITE):
        return VaultBackend.SQLITE

    # Default to SQLite even if not available
    # (will fail later with clear error message)
    return VaultBackend.SQLITE
