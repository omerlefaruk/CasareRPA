"""
Tests for Vault Client and Security Infrastructure.

Tests the vault client core, encrypted SQLite provider (development fallback),
credential provider integration, and rotation manager.
"""

import asyncio
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from casare_rpa.infrastructure.security.vault_client import (
    VaultClient,
    VaultConfig,
    VaultBackend,
    VaultProvider,
    SecretValue,
    SecretMetadata,
    CredentialType,
    SecretCache,
    AuditLogger,
    AuditEvent,
    AuditEventType,
    VaultError,
    SecretNotFoundError,
    VaultConnectionError,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_db_path(tmp_path: Path) -> str:
    """Create a temporary database path."""
    return str(tmp_path / "test_vault.db")


@pytest.fixture
def sqlite_config(temp_db_path: str) -> VaultConfig:
    """Create SQLite vault configuration."""
    from pydantic import SecretStr

    return VaultConfig(
        backend=VaultBackend.SQLITE,
        sqlite_path=temp_db_path,
        sqlite_encryption_key=SecretStr("test-key-12345"),
        cache_enabled=True,
        cache_ttl_seconds=60,
        audit_enabled=True,
    )


@pytest.fixture
def mock_provider() -> AsyncMock:
    """Create a mock vault provider."""
    provider = AsyncMock(spec=VaultProvider)
    provider.is_connected = AsyncMock(return_value=True)
    return provider


# =============================================================================
# UNIT TESTS - SecretMetadata
# =============================================================================


class TestSecretMetadata:
    """Tests for SecretMetadata model."""

    def test_metadata_defaults(self) -> None:
        """Test default values for metadata."""
        meta = SecretMetadata(path="secret/test")
        assert meta.path == "secret/test"
        assert meta.version == 1
        assert meta.credential_type == CredentialType.CUSTOM
        assert meta.is_dynamic is False
        assert meta.is_expired is False

    def test_metadata_expiration(self) -> None:
        """Test expiration detection."""
        # Not expired
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        meta = SecretMetadata(path="test", expires_at=future)
        assert meta.is_expired is False
        assert meta.time_until_expiry is not None
        assert meta.time_until_expiry.total_seconds() > 0

        # Expired
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        meta_expired = SecretMetadata(path="test", expires_at=past)
        assert meta_expired.is_expired is True
        assert meta_expired.time_until_expiry == timedelta(0)


# =============================================================================
# UNIT TESTS - SecretValue
# =============================================================================


class TestSecretValue:
    """Tests for SecretValue model."""

    def test_get_username(self) -> None:
        """Test username extraction from various formats."""
        meta = SecretMetadata(path="test")

        # Standard format
        secret = SecretValue(
            data={"username": "admin", "password": "secret"}, metadata=meta
        )
        assert secret.get_username() == "admin"

        # Alternative formats
        assert (
            SecretValue(data={"user": "admin"}, metadata=meta).get_username() == "admin"
        )
        assert (
            SecretValue(data={"login": "admin"}, metadata=meta).get_username()
            == "admin"
        )
        assert (
            SecretValue(data={"email": "admin@test.com"}, metadata=meta).get_username()
            == "admin@test.com"
        )

        # No username
        assert (
            SecretValue(data={"api_key": "xyz"}, metadata=meta).get_username() is None
        )

    def test_get_password(self) -> None:
        """Test password extraction."""
        meta = SecretMetadata(path="test")

        secret = SecretValue(data={"password": "secret123"}, metadata=meta)
        assert secret.get_password() == "secret123"

        secret2 = SecretValue(data={"pass": "secret"}, metadata=meta)
        assert secret2.get_password() == "secret"

    def test_get_api_key(self) -> None:
        """Test API key extraction."""
        meta = SecretMetadata(path="test")

        secret = SecretValue(data={"api_key": "key123"}, metadata=meta)
        assert secret.get_api_key() == "key123"

        secret2 = SecretValue(data={"token": "tok_abc"}, metadata=meta)
        assert secret2.get_api_key() == "tok_abc"


# =============================================================================
# UNIT TESTS - SecretCache
# =============================================================================


class TestSecretCache:
    """Tests for SecretCache."""

    @pytest.mark.asyncio
    async def test_cache_set_get(self) -> None:
        """Test basic cache operations."""
        cache = SecretCache(max_size=10, default_ttl=60)

        meta = SecretMetadata(path="test/secret")
        secret = SecretValue(data={"key": "value"}, metadata=meta)

        await cache.set("test/secret", secret)
        result = await cache.get("test/secret")

        assert result is not None
        assert result.data["key"] == "value"

    @pytest.mark.asyncio
    async def test_cache_miss(self) -> None:
        """Test cache miss returns None."""
        cache = SecretCache()
        result = await cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_expiration(self) -> None:
        """Test cache TTL expiration."""
        cache = SecretCache(default_ttl=0)  # Immediate expiration

        meta = SecretMetadata(path="test")
        secret = SecretValue(data={"key": "value"}, metadata=meta)

        await cache.set("test", secret, ttl=0)

        # Should be expired
        result = await cache.get("test")
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_invalidate(self) -> None:
        """Test cache invalidation."""
        cache = SecretCache()

        meta = SecretMetadata(path="test")
        secret = SecretValue(data={"key": "value"}, metadata=meta)

        await cache.set("test", secret)
        assert await cache.get("test") is not None

        removed = await cache.invalidate("test")
        assert removed is True
        assert await cache.get("test") is None

    @pytest.mark.asyncio
    async def test_cache_stats(self) -> None:
        """Test cache statistics."""
        cache = SecretCache()

        meta = SecretMetadata(path="test")
        secret = SecretValue(data={"key": "value"}, metadata=meta)

        await cache.set("test", secret)
        await cache.get("test")  # Hit
        await cache.get("test")  # Hit
        await cache.get("missing")  # Miss

        stats = cache.get_stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["size"] == 1


# =============================================================================
# UNIT TESTS - AuditLogger
# =============================================================================


class TestAuditLogger:
    """Tests for AuditLogger."""

    def test_audit_logging(self) -> None:
        """Test audit event logging."""
        audit = AuditLogger(enabled=True, log_reads=True)

        audit.log_read("secret/test", success=True, workflow_id="wf_123")

        events = audit.get_recent_events()
        assert len(events) == 1
        assert events[0].event_type == AuditEventType.SECRET_READ
        assert events[0].path == "secret/test"
        assert events[0].workflow_id == "wf_123"

    def test_audit_disabled(self) -> None:
        """Test audit logging when disabled."""
        audit = AuditLogger(enabled=False)

        audit.log_read("secret/test", success=True)

        events = audit.get_recent_events()
        assert len(events) == 0

    def test_audit_skip_reads(self) -> None:
        """Test skipping read events."""
        audit = AuditLogger(enabled=True, log_reads=False)

        audit.log_read("secret/test", success=True)
        audit.log_write("secret/test", success=True)

        events = audit.get_recent_events()
        assert len(events) == 1
        assert events[0].event_type == AuditEventType.SECRET_WRITE


# =============================================================================
# INTEGRATION TESTS - VaultClient with MockProvider
# =============================================================================


class TestVaultClient:
    """Tests for VaultClient."""

    @pytest.mark.asyncio
    async def test_client_connect_disconnect(self, mock_provider: AsyncMock) -> None:
        """Test client connection lifecycle."""
        config = VaultConfig(backend=VaultBackend.SQLITE)
        client = VaultClient(config, provider=mock_provider)

        await client.connect()
        assert await client.is_connected()

        await client.disconnect()
        mock_provider.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_client_get_secret(self, mock_provider: AsyncMock) -> None:
        """Test secret retrieval."""
        meta = SecretMetadata(path="test/secret")
        secret = SecretValue(
            data={"username": "admin", "password": "secret"}, metadata=meta
        )
        mock_provider.get_secret = AsyncMock(return_value=secret)

        config = VaultConfig(backend=VaultBackend.SQLITE)
        client = VaultClient(config, provider=mock_provider)
        client._connected = True

        result = await client.get_secret("test/secret")

        assert result.data["username"] == "admin"
        mock_provider.get_secret.assert_called_once_with("test/secret", None)

    @pytest.mark.asyncio
    async def test_client_caching(self, mock_provider: AsyncMock) -> None:
        """Test secret caching."""
        meta = SecretMetadata(path="test/secret")
        secret = SecretValue(data={"key": "value"}, metadata=meta)
        mock_provider.get_secret = AsyncMock(return_value=secret)

        config = VaultConfig(backend=VaultBackend.SQLITE, cache_enabled=True)
        client = VaultClient(config, provider=mock_provider)
        client._connected = True

        # First call - fetches from provider
        await client.get_secret("test/secret")
        # Second call - should hit cache
        await client.get_secret("test/secret")

        # Provider should only be called once
        assert mock_provider.get_secret.call_count == 1

    @pytest.mark.asyncio
    async def test_client_bypass_cache(self, mock_provider: AsyncMock) -> None:
        """Test bypassing cache."""
        meta = SecretMetadata(path="test/secret")
        secret = SecretValue(data={"key": "value"}, metadata=meta)
        mock_provider.get_secret = AsyncMock(return_value=secret)

        config = VaultConfig(backend=VaultBackend.SQLITE, cache_enabled=True)
        client = VaultClient(config, provider=mock_provider)
        client._connected = True

        await client.get_secret("test/secret")
        await client.get_secret("test/secret", bypass_cache=True)

        # Provider should be called twice
        assert mock_provider.get_secret.call_count == 2

    @pytest.mark.asyncio
    async def test_client_not_connected_error(self) -> None:
        """Test error when not connected."""
        config = VaultConfig(backend=VaultBackend.SQLITE)
        client = VaultClient(config)

        with pytest.raises(VaultConnectionError):
            await client.get_secret("test")

    @pytest.mark.asyncio
    async def test_client_context_manager(self, mock_provider: AsyncMock) -> None:
        """Test async context manager."""
        config = VaultConfig(backend=VaultBackend.SQLITE)

        async with VaultClient(config, provider=mock_provider) as client:
            assert await client.is_connected()

        mock_provider.disconnect.assert_called()


# =============================================================================
# INTEGRATION TESTS - EncryptedSQLiteProvider
# =============================================================================


class TestEncryptedSQLiteProvider:
    """Tests for EncryptedSQLiteProvider."""

    @pytest.mark.asyncio
    async def test_sqlite_connect(self, sqlite_config: VaultConfig) -> None:
        """Test SQLite vault connection."""
        try:
            from casare_rpa.infrastructure.security.providers.sqlite_vault import (
                EncryptedSQLiteProvider,
            )
        except ImportError:
            pytest.skip("aiosqlite or cryptography not available")

        provider = EncryptedSQLiteProvider(sqlite_config)
        await provider.connect()

        assert await provider.is_connected()

        await provider.disconnect()
        assert not await provider.is_connected()

    @pytest.mark.asyncio
    async def test_sqlite_crud_operations(self, sqlite_config: VaultConfig) -> None:
        """Test CRUD operations on SQLite vault."""
        try:
            from casare_rpa.infrastructure.security.providers.sqlite_vault import (
                EncryptedSQLiteProvider,
            )
        except ImportError:
            pytest.skip("aiosqlite or cryptography not available")

        provider = EncryptedSQLiteProvider(sqlite_config)
        await provider.connect()

        try:
            # Create
            metadata = await provider.put_secret(
                path="test/creds",
                data={"username": "admin", "password": "secret123"},
                credential_type=CredentialType.USERNAME_PASSWORD,
            )
            assert metadata.path == "test/creds"
            assert metadata.version == 1

            # Read
            secret = await provider.get_secret("test/creds")
            assert secret.data["username"] == "admin"
            assert secret.data["password"] == "secret123"

            # Update
            await provider.put_secret(
                path="test/creds",
                data={"username": "admin", "password": "new_password"},
            )
            updated = await provider.get_secret("test/creds")
            assert updated.data["password"] == "new_password"
            assert updated.metadata.version == 2

            # List
            paths = await provider.list_secrets("test/")
            assert "test/creds" in paths

            # Delete
            deleted = await provider.delete_secret("test/creds")
            assert deleted is True

            with pytest.raises(SecretNotFoundError):
                await provider.get_secret("test/creds")

        finally:
            await provider.disconnect()

    @pytest.mark.asyncio
    async def test_sqlite_encryption(self, tmp_path: Path) -> None:
        """Test that secrets are encrypted at rest."""
        try:
            from casare_rpa.infrastructure.security.providers.sqlite_vault import (
                EncryptedSQLiteProvider,
            )
            from pydantic import SecretStr
        except ImportError:
            pytest.skip("aiosqlite or cryptography not available")

        db_path = str(tmp_path / "encrypted_test.db")
        config = VaultConfig(
            backend=VaultBackend.SQLITE,
            sqlite_path=db_path,
            sqlite_encryption_key=SecretStr("encryption-key"),
        )

        provider = EncryptedSQLiteProvider(config)
        await provider.connect()

        await provider.put_secret(
            path="secret/test",
            data={"password": "super_secret_password"},
        )

        await provider.disconnect()

        # Read the raw database and verify password is not in plaintext
        raw_content = Path(db_path).read_bytes()
        assert b"super_secret_password" not in raw_content


# =============================================================================
# INTEGRATION TESTS - VaultCredentialProvider
# =============================================================================


class TestVaultCredentialProvider:
    """Tests for VaultCredentialProvider."""

    @pytest.mark.asyncio
    async def test_credential_provider_basic(self, sqlite_config: VaultConfig) -> None:
        """Test basic credential provider operations."""
        try:
            from casare_rpa.infrastructure.security.credential_provider import (
                VaultCredentialProvider,
            )
            from casare_rpa.infrastructure.security.providers.sqlite_vault import (
                EncryptedSQLiteProvider,
            )
        except ImportError:
            pytest.skip("Required dependencies not available")

        # Setup vault with test secret
        provider_impl = EncryptedSQLiteProvider(sqlite_config)
        await provider_impl.connect()

        await provider_impl.put_secret(
            path="secret/prod/erp",
            data={"username": "erp_user", "password": "erp_pass"},
            credential_type=CredentialType.USERNAME_PASSWORD,
        )

        client = VaultClient(sqlite_config, provider=provider_impl)
        client._connected = True

        cred_provider = VaultCredentialProvider(vault_client=client)
        await cred_provider.initialize()

        try:
            # Register alias
            cred_provider.register_alias("erp_login", "secret/prod/erp")

            # Resolve credential
            cred = await cred_provider.get_credential("erp_login")

            assert cred is not None
            assert cred.username == "erp_user"
            assert cred.password == "erp_pass"
            assert cred.credential_type == CredentialType.USERNAME_PASSWORD

        finally:
            await cred_provider.shutdown()
            await provider_impl.disconnect()

    @pytest.mark.asyncio
    async def test_credential_provider_missing_alias(
        self, sqlite_config: VaultConfig
    ) -> None:
        """Test handling of missing credential alias."""
        try:
            from casare_rpa.infrastructure.security.credential_provider import (
                VaultCredentialProvider,
            )
            from casare_rpa.infrastructure.security.providers.sqlite_vault import (
                EncryptedSQLiteProvider,
            )
        except ImportError:
            pytest.skip("Required dependencies not available")

        provider_impl = EncryptedSQLiteProvider(sqlite_config)
        await provider_impl.connect()

        client = VaultClient(sqlite_config, provider=provider_impl)
        client._connected = True

        cred_provider = VaultCredentialProvider(vault_client=client)
        await cred_provider.initialize()

        try:
            # Required credential that doesn't exist
            with pytest.raises(SecretNotFoundError):
                await cred_provider.get_credential("nonexistent", required=True)

            # Optional credential returns None
            result = await cred_provider.get_credential("nonexistent", required=False)
            assert result is None

        finally:
            await cred_provider.shutdown()
            await provider_impl.disconnect()


# =============================================================================
# INTEGRATION TESTS - SecretRotationManager
# =============================================================================


class TestSecretRotationManager:
    """Tests for SecretRotationManager."""

    @pytest.mark.asyncio
    async def test_rotation_manager_basic(self, sqlite_config: VaultConfig) -> None:
        """Test basic rotation manager functionality."""
        try:
            from casare_rpa.infrastructure.security.rotation import (
                SecretRotationManager,
                RotationPolicy,
                RotationFrequency,
                RotationStatus,
            )
            from casare_rpa.infrastructure.security.providers.sqlite_vault import (
                EncryptedSQLiteProvider,
            )
        except ImportError:
            pytest.skip("Required dependencies not available")

        provider_impl = EncryptedSQLiteProvider(sqlite_config)
        await provider_impl.connect()

        # Store initial secret
        await provider_impl.put_secret(
            path="secret/rotate-test",
            data={"password": "initial_password"},
            credential_type=CredentialType.USERNAME_PASSWORD,
        )

        client = VaultClient(sqlite_config, provider=provider_impl)
        client._connected = True

        rotation_manager = SecretRotationManager(client)

        try:
            # Register rotation policy
            policy = RotationPolicy(
                path="secret/rotate-test",
                frequency=RotationFrequency.DAILY,
            )
            rotation_manager.register_policy(policy)

            # Manually trigger rotation
            record = await rotation_manager.rotate_secret("secret/rotate-test")

            assert record.status == RotationStatus.COMPLETED
            assert record.old_version == 1
            assert record.new_version == 2

            # Verify password changed
            new_secret = await provider_impl.get_secret("secret/rotate-test")
            assert new_secret.data["password"] != "initial_password"

        finally:
            await rotation_manager.stop()
            await provider_impl.disconnect()


# =============================================================================
# FACTORY TESTS
# =============================================================================


class TestProviderFactory:
    """Tests for provider factory."""

    def test_get_available_backends(self) -> None:
        """Test checking available backends."""
        from casare_rpa.infrastructure.security.providers.factory import (
            get_available_backends,
        )

        available = get_available_backends()

        assert VaultBackend.HASHICORP in available
        assert VaultBackend.SUPABASE in available
        assert VaultBackend.SQLITE in available

    def test_get_recommended_backend(self) -> None:
        """Test getting recommended backend."""
        from casare_rpa.infrastructure.security.providers.factory import (
            get_recommended_backend,
        )

        backend = get_recommended_backend()
        assert backend in VaultBackend


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
