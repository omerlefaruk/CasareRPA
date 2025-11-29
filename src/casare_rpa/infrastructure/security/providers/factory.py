"""
Vault Provider Factory.

Creates the appropriate vault provider based on configuration.
Handles automatic fallback when optional dependencies are missing.
"""

from typing import Optional

from loguru import logger

from ..vault_client import (
    VaultProvider,
    VaultConfig,
    VaultBackend,
    VaultConnectionError,
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
    last_error: Optional[Exception] = None

    # Try the configured backend first
    if backend == VaultBackend.HASHICORP:
        try:
            from .hashicorp import HashiCorpVaultProvider

            logger.debug("Creating HashiCorp Vault provider")
            return HashiCorpVaultProvider(config)
        except ImportError as e:
            last_error = e
            logger.warning(
                f"HashiCorp Vault provider unavailable: {e}. "
                f"Install with: pip install hvac"
            )

    elif backend == VaultBackend.SUPABASE:
        try:
            from .supabase_vault import SupabaseVaultProvider

            logger.debug("Creating Supabase Vault provider")
            return SupabaseVaultProvider(config)
        except ImportError as e:
            last_error = e
            logger.warning(
                f"Supabase Vault provider unavailable: {e}. "
                f"Install with: pip install asyncpg"
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
        f"Failed to create vault provider for backend '{backend.value}'. "
        f"Last error: {last_error}"
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

    return available


def get_recommended_backend() -> VaultBackend:
    """
    Get the recommended vault backend based on available dependencies.

    Priority:
    1. HashiCorp Vault (if hvac available)
    2. Supabase Vault (if asyncpg available)
    3. SQLite (if aiosqlite and cryptography available)

    Returns:
        Recommended VaultBackend
    """
    available = get_available_backends()

    if available.get(VaultBackend.HASHICORP):
        return VaultBackend.HASHICORP
    if available.get(VaultBackend.SUPABASE):
        return VaultBackend.SUPABASE
    if available.get(VaultBackend.SQLITE):
        return VaultBackend.SQLITE

    # Default to SQLite even if not available
    # (will fail later with clear error message)
    return VaultBackend.SQLITE
