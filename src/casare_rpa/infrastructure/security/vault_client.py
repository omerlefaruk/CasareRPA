"""
CasareRPA - Vault Client Core Module.

Provides unified interface for secret management with multiple backend support.
Designed for enterprise RPA security requirements:
- Dynamic secret generation
- Automatic rotation handling
- Audit logging integration
- TTL-based caching with automatic refresh
"""

import asyncio
import secrets
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from loguru import logger
from pydantic import BaseModel, Field, SecretStr, field_validator

# =============================================================================
# ENUMS
# =============================================================================


class VaultBackend(str, Enum):
    """Supported vault backend types."""

    HASHICORP = "hashicorp"
    SUPABASE = "supabase"
    SQLITE = "sqlite"  # Development fallback
    AZURE_KEYVAULT = "azure_keyvault"  # Azure Key Vault
    AWS_SECRETS_MANAGER = "aws_secrets_manager"  # AWS Secrets Manager


class CredentialType(str, Enum):
    """Types of credentials supported by the vault."""

    USERNAME_PASSWORD = "username_password"
    API_KEY = "api_key"
    OAUTH2_TOKEN = "oauth2_token"
    SSH_KEY = "ssh_key"
    CERTIFICATE = "certificate"
    DATABASE_CONNECTION = "database_connection"
    AWS_CREDENTIALS = "aws_credentials"
    AZURE_CREDENTIALS = "azure_credentials"
    CUSTOM = "custom"


class AuditEventType(str, Enum):
    """Types of audit events for secret operations."""

    SECRET_READ = "secret_read"
    SECRET_WRITE = "secret_write"
    SECRET_DELETE = "secret_delete"
    SECRET_ROTATE = "secret_rotate"
    SECRET_LEASE_RENEW = "secret_lease_renew"
    SECRET_LEASE_REVOKE = "secret_lease_revoke"
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"


# =============================================================================
# EXCEPTIONS
# =============================================================================


class VaultError(Exception):
    """Base exception for all vault operations."""

    def __init__(self, message: str, path: str | None = None) -> None:
        self.message = message
        self.path = path
        super().__init__(message)


class SecretNotFoundError(VaultError):
    """Raised when a secret is not found at the specified path."""

    pass


class VaultConnectionError(VaultError):
    """Raised when connection to vault fails."""

    pass


class VaultAuthenticationError(VaultError):
    """Raised when vault authentication fails."""

    pass


class SecretAccessDeniedError(VaultError):
    """Raised when access to a secret is denied."""

    pass


class SecretExpiredError(VaultError):
    """Raised when attempting to use an expired dynamic secret."""

    pass


# =============================================================================
# DATA MODELS
# =============================================================================


class SecretMetadata(BaseModel):
    """Metadata associated with a secret."""

    path: str = Field(..., description="Vault path for the secret")
    version: int = Field(default=1, ge=1, description="Secret version number")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = Field(
        default=None, description="Expiration time for dynamic secrets"
    )
    credential_type: CredentialType = Field(default=CredentialType.CUSTOM)
    is_dynamic: bool = Field(
        default=False, description="Whether this is a dynamically generated secret"
    )
    lease_id: str | None = Field(default=None, description="Lease ID for dynamic secrets")
    lease_duration: int | None = Field(default=None, description="Lease duration in seconds")
    renewable: bool = Field(default=False, description="Whether the lease can be renewed")
    custom_metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """Check if the secret has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(UTC) > self.expires_at

    @property
    def time_until_expiry(self) -> timedelta | None:
        """Get time remaining until expiration."""
        if self.expires_at is None:
            return None
        remaining = self.expires_at - datetime.now(UTC)
        return remaining if remaining.total_seconds() > 0 else timedelta(0)


class SecretValue(BaseModel):
    """Container for secret data with metadata."""

    data: dict[str, Any] = Field(..., description="Secret key-value pairs")
    metadata: SecretMetadata = Field(...)

    model_config = {"extra": "forbid"}

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the secret data."""
        return self.data.get(key, default)

    def get_username(self) -> str | None:
        """Extract username from common credential formats."""
        for key in ["username", "user", "login", "email", "user_id"]:
            if key in self.data:
                return str(self.data[key])
        return None

    def get_password(self) -> str | None:
        """Extract password from common credential formats."""
        for key in ["password", "pass", "secret", "pwd", "passwd"]:
            if key in self.data:
                return str(self.data[key])
        return None

    def get_api_key(self) -> str | None:
        """Extract API key from common formats."""
        for key in ["api_key", "apikey", "key", "token", "access_token"]:
            if key in self.data:
                return str(self.data[key])
        return None


class AuditEvent(BaseModel):
    """Audit log event for secret operations."""

    event_id: str = Field(default_factory=lambda: secrets.token_hex(16))
    event_type: AuditEventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    path: str | None = None
    workflow_id: str | None = None
    robot_id: str | None = None
    user_id: str | None = None
    success: bool = True
    error_message: str | None = None
    client_ip: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_log_string(self) -> str:
        """Format as log string for structured logging."""
        status = "SUCCESS" if self.success else "FAILURE"
        return (
            f"[{self.event_type.value}] {status} path={self.path} "
            f"workflow={self.workflow_id} robot={self.robot_id}"
        )


# =============================================================================
# CONFIGURATION
# =============================================================================


class VaultConfig(BaseModel):
    """Configuration for vault client."""

    backend: VaultBackend = Field(default=VaultBackend.SQLITE, description="Vault backend to use")

    # HashiCorp Vault settings
    hashicorp_url: str | None = Field(default=None, description="HashiCorp Vault server URL")
    hashicorp_token: SecretStr | None = Field(default=None, description="HashiCorp Vault token")
    hashicorp_namespace: str | None = Field(
        default=None, description="Vault namespace for enterprise"
    )
    hashicorp_mount_point: str = Field(
        default="secret", description="KV secrets engine mount point"
    )
    hashicorp_kv_version: int = Field(
        default=2, ge=1, le=2, description="KV secrets engine version"
    )

    # Supabase Vault settings
    supabase_url: str | None = Field(default=None, description="Supabase project URL")
    supabase_key: SecretStr | None = Field(default=None, description="Supabase service role key")

    # SQLite fallback settings
    sqlite_path: str = Field(
        default=".casare/vault.db", description="Path to SQLite vault database"
    )
    sqlite_encryption_key: SecretStr | None = Field(
        default=None, description="Encryption key for SQLite vault"
    )

    # Cache settings
    cache_enabled: bool = Field(default=True, description="Enable secret caching")
    cache_ttl_seconds: int = Field(default=300, ge=0, description="Cache TTL in seconds")
    cache_max_size: int = Field(default=1000, ge=1, description="Maximum cache entries")

    # Retry settings
    max_retries: int = Field(default=3, ge=0, description="Max retry attempts")
    retry_delay_seconds: float = Field(default=1.0, ge=0, description="Delay between retries")

    # Audit settings
    audit_enabled: bool = Field(default=True, description="Enable audit logging")
    audit_log_reads: bool = Field(default=True, description="Log secret read operations")

    # TLS settings
    tls_verify: bool = Field(default=True, description="Verify TLS certificates")
    tls_ca_cert: str | None = Field(default=None, description="Path to CA certificate")
    tls_client_cert: str | None = Field(default=None, description="Path to client certificate")
    tls_client_key: str | None = Field(default=None, description="Path to client private key")

    # Azure Key Vault settings
    azure_vault_url: str | None = Field(
        default=None,
        description="Azure Key Vault URL (e.g., https://myvault.vault.azure.net/)",
    )
    azure_tenant_id: str | None = Field(
        default=None, description="Azure AD tenant ID for Service Principal auth"
    )
    azure_client_id: str | None = Field(
        default=None, description="Azure AD client ID for Service Principal auth"
    )
    azure_client_secret: SecretStr | None = Field(
        default=None, description="Azure AD client secret for Service Principal auth"
    )
    azure_use_managed_identity: bool = Field(
        default=False, description="Use Azure Managed Identity for authentication"
    )
    azure_managed_identity_client_id: str | None = Field(
        default=None, description="Client ID for user-assigned managed identity"
    )

    # AWS Secrets Manager settings
    aws_region: str | None = Field(default=None, description="AWS region for Secrets Manager")
    aws_access_key_id: str | None = Field(
        default=None,
        description="AWS access key ID (optional, uses env/IAM if not set)",
    )
    aws_secret_access_key: SecretStr | None = Field(
        default=None, description="AWS secret access key"
    )
    aws_session_token: SecretStr | None = Field(
        default=None, description="AWS session token for temporary credentials"
    )
    aws_profile: str | None = Field(
        default=None, description="AWS profile name from ~/.aws/credentials"
    )
    aws_endpoint_url: str | None = Field(
        default=None, description="Custom AWS endpoint URL (for LocalStack, testing)"
    )

    @field_validator("hashicorp_url")
    @classmethod
    def validate_hashicorp_url(cls, v: str | None) -> str | None:
        """Ensure HashiCorp URL has proper scheme."""
        if v is not None and not v.startswith(("http://", "https://")):
            return f"https://{v}"
        return v

    def get_backend_display_name(self) -> str:
        """Get human-readable backend name."""
        names = {
            VaultBackend.HASHICORP: "HashiCorp Vault",
            VaultBackend.SUPABASE: "Supabase Vault",
            VaultBackend.SQLITE: "Local Encrypted SQLite",
            VaultBackend.AZURE_KEYVAULT: "Azure Key Vault",
            VaultBackend.AWS_SECRETS_MANAGER: "AWS Secrets Manager",
        }
        return names.get(self.backend, self.backend.value)


# =============================================================================
# CACHE
# =============================================================================


@dataclass
class CacheEntry:
    """Cache entry for secrets."""

    value: SecretValue
    cached_at: datetime
    ttl_seconds: int
    access_count: int = 0

    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        age = (datetime.now(UTC) - self.cached_at).total_seconds()
        return age > self.ttl_seconds


class SecretCache:
    """Thread-safe LRU cache for secrets."""

    def __init__(self, max_size: int = 1000, default_ttl: int = 300) -> None:
        self._cache: dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = asyncio.Lock()
        self._hits = 0
        self._misses = 0

    async def get(self, path: str) -> SecretValue | None:
        """Get secret from cache if valid."""
        async with self._lock:
            entry = self._cache.get(path)
            if entry is None:
                self._misses += 1
                return None

            if entry.is_expired:
                del self._cache[path]
                self._misses += 1
                return None

            # Check if underlying secret is expired
            if entry.value.metadata.is_expired:
                del self._cache[path]
                self._misses += 1
                return None

            entry.access_count += 1
            self._hits += 1
            return entry.value

    async def set(self, path: str, value: SecretValue, ttl: int | None = None) -> None:
        """Store secret in cache."""
        async with self._lock:
            # Evict if at capacity
            if len(self._cache) >= self._max_size and path not in self._cache:
                await self._evict_lru()

            self._cache[path] = CacheEntry(
                value=value,
                cached_at=datetime.now(UTC),
                ttl_seconds=ttl or self._default_ttl,
            )

    async def invalidate(self, path: str) -> bool:
        """Remove secret from cache."""
        async with self._lock:
            if path in self._cache:
                del self._cache[path]
                return True
            return False

    async def invalidate_prefix(self, prefix: str) -> int:
        """Remove all secrets matching a path prefix."""
        async with self._lock:
            to_remove = [k for k in self._cache if k.startswith(prefix)]
            for key in to_remove:
                del self._cache[key]
            return len(to_remove)

    async def clear(self) -> None:
        """Clear all cached secrets."""
        async with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    async def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self._cache:
            return
        # Find entry with lowest access count
        lru_key = min(self._cache, key=lambda k: self._cache[k].access_count)
        del self._cache[lru_key]

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0.0
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate_percent": round(hit_rate, 2),
        }


# =============================================================================
# ABSTRACT PROVIDER
# =============================================================================


class VaultProvider(ABC):
    """Abstract base class for vault providers."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to vault backend."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to vault backend."""
        pass

    @abstractmethod
    async def is_connected(self) -> bool:
        """Check if connection is active."""
        pass

    @abstractmethod
    async def get_secret(self, path: str, version: int | None = None) -> SecretValue:
        """
        Retrieve a secret from the vault.

        Args:
            path: Secret path in vault
            version: Optional specific version (for versioned backends)

        Returns:
            SecretValue with data and metadata

        Raises:
            SecretNotFoundError: If secret doesn't exist
            VaultConnectionError: If connection fails
        """
        pass

    @abstractmethod
    async def put_secret(
        self,
        path: str,
        data: dict[str, Any],
        credential_type: CredentialType = CredentialType.CUSTOM,
        metadata: dict[str, Any] | None = None,
    ) -> SecretMetadata:
        """
        Store a secret in the vault.

        Args:
            path: Secret path in vault
            data: Secret key-value pairs
            credential_type: Type of credential
            metadata: Optional custom metadata

        Returns:
            SecretMetadata for the stored secret
        """
        pass

    @abstractmethod
    async def delete_secret(self, path: str) -> bool:
        """
        Delete a secret from the vault.

        Args:
            path: Secret path in vault

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def list_secrets(self, path_prefix: str) -> list[str]:
        """
        List secret paths under a prefix.

        Args:
            path_prefix: Path prefix to list

        Returns:
            List of secret paths
        """
        pass

    async def get_dynamic_secret(self, path: str, role: str, ttl: int | None = None) -> SecretValue:
        """
        Get a dynamically generated secret (e.g., database credentials).

        Args:
            path: Dynamic secret engine path
            role: Role name for credential generation
            ttl: Optional TTL in seconds

        Returns:
            SecretValue with generated credentials

        Raises:
            NotImplementedError: If backend doesn't support dynamic secrets
        """
        raise NotImplementedError(f"{self.__class__.__name__} does not support dynamic secrets")

    async def renew_lease(self, lease_id: str, increment: int | None = None) -> int:
        """
        Renew a secret lease.

        Args:
            lease_id: Lease ID to renew
            increment: Optional TTL increment in seconds

        Returns:
            New lease duration in seconds

        Raises:
            NotImplementedError: If backend doesn't support leases
        """
        raise NotImplementedError(f"{self.__class__.__name__} does not support lease renewal")

    async def revoke_lease(self, lease_id: str) -> None:
        """
        Revoke a secret lease.

        Args:
            lease_id: Lease ID to revoke

        Raises:
            NotImplementedError: If backend doesn't support leases
        """
        raise NotImplementedError(f"{self.__class__.__name__} does not support lease revocation")

    async def rotate_secret(self, path: str) -> SecretMetadata:
        """
        Trigger rotation of a secret.

        Args:
            path: Secret path to rotate

        Returns:
            New secret metadata

        Raises:
            NotImplementedError: If backend doesn't support rotation
        """
        raise NotImplementedError(f"{self.__class__.__name__} does not support secret rotation")


# =============================================================================
# AUDIT LOGGER
# =============================================================================


class AuditLogger:
    """
    Handles audit logging for vault operations.

    Supports both in-memory buffering for fast access and persistent
    storage via AuditRepository for compliance and analysis.

    Features:
    - Hybrid storage: in-memory for recent events, database for history
    - Async database writes to avoid blocking
    - Configurable logging of read operations
    - Hash chain integrity through repository
    """

    def __init__(
        self,
        enabled: bool = True,
        log_reads: bool = True,
        use_persistent_storage: bool = True,
    ) -> None:
        """
        Initialize the audit logger.

        Args:
            enabled: Enable/disable audit logging
            log_reads: Log secret read operations
            use_persistent_storage: Enable persistent database storage
        """
        self._enabled = enabled
        self._log_reads = log_reads
        self._use_persistent_storage = use_persistent_storage
        self._events: list[AuditEvent] = []
        self._max_buffer_size = 1000
        self._pending_events: list[AuditEvent] = []
        self._flush_task: asyncio.Task | None = None
        self._repository = None

    async def _get_repository(self):
        """Get or create the audit repository."""
        if self._repository is None and self._use_persistent_storage:
            try:
                from casare_rpa.infrastructure.persistence.repositories.audit_repository import (
                    AuditRepository,
                )

                self._repository = AuditRepository()
                await self._repository.initialize()
            except Exception as e:
                logger.warning(f"Failed to initialize audit repository: {e}")
                self._use_persistent_storage = False
        return self._repository

    def log(self, event: AuditEvent) -> None:
        """
        Log an audit event.

        Stores in memory immediately and queues for async database write.

        Args:
            event: Audit event to log
        """
        if not self._enabled:
            return

        # Skip read events if not logging reads
        if event.event_type == AuditEventType.SECRET_READ and not self._log_reads:
            return

        # Log to structured logger
        if event.success:
            logger.info(f"VAULT_AUDIT: {event.to_log_string()}")
        else:
            logger.warning(f"VAULT_AUDIT: {event.to_log_string()}")

        # Buffer event in memory
        self._events.append(event)
        if len(self._events) > self._max_buffer_size:
            self._events = self._events[-self._max_buffer_size :]

        # Queue for persistent storage
        if self._use_persistent_storage:
            self._pending_events.append(event)
            self._schedule_flush()

    def _schedule_flush(self) -> None:
        """Schedule async flush of pending events."""
        if self._flush_task is None or self._flush_task.done():
            try:
                loop = asyncio.get_running_loop()
                self._flush_task = loop.create_task(self._flush_pending())
            except RuntimeError:
                # No running event loop - will flush on next async operation
                pass

    async def _flush_pending(self) -> None:
        """Flush pending events to persistent storage."""
        if not self._pending_events:
            return

        try:
            repository = await self._get_repository()
            if repository:
                events_to_flush = self._pending_events.copy()
                self._pending_events.clear()
                await repository.log_events_batch(events_to_flush)
        except Exception as e:
            logger.error(f"Failed to flush audit events to storage: {e}")

    def log_read(
        self,
        path: str,
        success: bool = True,
        workflow_id: str | None = None,
        robot_id: str | None = None,
        error: str | None = None,
    ) -> None:
        """Log a secret read operation."""
        self.log(
            AuditEvent(
                event_type=AuditEventType.SECRET_READ,
                path=path,
                workflow_id=workflow_id,
                robot_id=robot_id,
                success=success,
                error_message=error,
            )
        )

    def log_write(
        self,
        path: str,
        success: bool = True,
        user_id: str | None = None,
        error: str | None = None,
    ) -> None:
        """Log a secret write operation."""
        self.log(
            AuditEvent(
                event_type=AuditEventType.SECRET_WRITE,
                path=path,
                user_id=user_id,
                success=success,
                error_message=error,
            )
        )

    def log_cache_event(self, path: str, hit: bool) -> None:
        """Log cache hit or miss."""
        self.log(
            AuditEvent(
                event_type=AuditEventType.CACHE_HIT if hit else AuditEventType.CACHE_MISS,
                path=path,
            )
        )

    def get_recent_events(self, count: int = 100) -> list[AuditEvent]:
        """Get recent audit events from memory."""
        return self._events[-count:]

    async def get_events_from_storage(
        self,
        event_type: str | None = None,
        resource: str | None = None,
        workflow_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """
        Query events from persistent storage.

        Args:
            event_type: Filter by event type
            resource: Filter by resource path
            workflow_id: Filter by workflow ID
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum events to return

        Returns:
            List of matching audit events
        """
        repository = await self._get_repository()
        if not repository:
            return self._events[-limit:]

        return await repository.get_events(
            event_type=event_type,
            resource=resource,
            workflow_id=workflow_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

    async def get_statistics(self) -> dict[str, Any]:
        """
        Get audit statistics.

        Returns:
            Dictionary with event counts and statistics
        """
        repository = await self._get_repository()
        if not repository:
            return {
                "total_events": len(self._events),
                "successful_events": sum(1 for e in self._events if e.success),
                "failed_events": sum(1 for e in self._events if not e.success),
            }

        return await repository.get_statistics()

    async def verify_integrity(self, limit: int = 1000) -> dict[str, Any]:
        """
        Verify audit chain integrity.

        Args:
            limit: Maximum events to verify

        Returns:
            Dictionary with verification results
        """
        repository = await self._get_repository()
        if not repository:
            return {"valid": True, "message": "No persistent storage configured"}

        return await repository.verify_integrity(limit)

    async def export_events(
        self,
        output_path: str,
        format_type: str = "json",
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> int:
        """
        Export audit events to file.

        Args:
            output_path: Path for output file
            format_type: Export format (json, csv)
            start_time: Filter by start time
            end_time: Filter by end time

        Returns:
            Number of events exported
        """
        repository = await self._get_repository()
        if not repository:
            return 0

        if format_type == "csv":
            return await repository.export_to_csv(output_path, start_time, end_time)
        else:
            return await repository.export_to_json(output_path, start_time, end_time)

    async def cleanup_old_events(self, retention_days: int = 90) -> dict[str, Any]:
        """
        Remove old events per retention policy.

        Args:
            retention_days: Days to retain events

        Returns:
            Cleanup results
        """
        repository = await self._get_repository()
        if not repository:
            return {"events_deleted": 0, "message": "No persistent storage configured"}

        return await repository.cleanup_old_events(retention_days)

    async def flush(self) -> None:
        """Flush all buffered events to persistent storage."""
        await self._flush_pending()

    async def close(self) -> None:
        """Close the audit logger and repository."""
        await self.flush()
        if self._repository:
            await self._repository.close()
            self._repository = None


# =============================================================================
# VAULT CLIENT
# =============================================================================


class VaultClient:
    """
    Unified vault client with caching, auditing, and multiple backend support.

    Usage:
        config = VaultConfig(backend=VaultBackend.HASHICORP, ...)
        client = VaultClient(config)
        await client.connect()

        try:
            secret = await client.get_secret("secret/my-app/db-creds")
            username = secret.get_username()
            password = secret.get_password()
        finally:
            await client.disconnect()
    """

    def __init__(
        self,
        config: VaultConfig,
        provider: VaultProvider | None = None,
    ) -> None:
        """
        Initialize vault client.

        Args:
            config: Vault configuration
            provider: Optional custom provider (uses config.backend if not provided)
        """
        self._config = config
        self._provider = provider
        self._cache = SecretCache(
            max_size=config.cache_max_size,
            default_ttl=config.cache_ttl_seconds,
        )
        self._audit = AuditLogger(
            enabled=config.audit_enabled,
            log_reads=config.audit_log_reads,
        )
        self._connected = False
        self._workflow_id: str | None = None
        self._robot_id: str | None = None

    def set_context(
        self,
        workflow_id: str | None = None,
        robot_id: str | None = None,
    ) -> None:
        """Set execution context for audit logging."""
        self._workflow_id = workflow_id
        self._robot_id = robot_id

    async def connect(self) -> None:
        """Connect to vault backend."""
        if self._provider is None:
            from .providers import create_vault_provider

            self._provider = create_vault_provider(self._config)

        try:
            await self._provider.connect()
            self._connected = True
            logger.info(f"Connected to vault backend: {self._config.get_backend_display_name()}")
            self._audit.log(
                AuditEvent(
                    event_type=AuditEventType.AUTH_SUCCESS,
                    metadata={"backend": self._config.backend.value},
                )
            )
        except Exception as e:
            self._audit.log(
                AuditEvent(
                    event_type=AuditEventType.AUTH_FAILURE,
                    success=False,
                    error_message=str(e),
                    metadata={"backend": self._config.backend.value},
                )
            )
            raise VaultConnectionError(f"Failed to connect to vault: {e}") from e

    async def disconnect(self) -> None:
        """Disconnect from vault backend."""
        if self._provider:
            await self._provider.disconnect()
        self._connected = False
        await self._cache.clear()
        logger.info("Disconnected from vault backend")

    async def is_connected(self) -> bool:
        """Check if connected to vault."""
        if not self._connected or not self._provider:
            return False
        return await self._provider.is_connected()

    async def get_secret(
        self,
        path: str,
        version: int | None = None,
        bypass_cache: bool = False,
    ) -> SecretValue:
        """
        Get a secret from vault with caching.

        Args:
            path: Secret path
            version: Optional specific version
            bypass_cache: Skip cache lookup

        Returns:
            SecretValue with data and metadata
        """
        if not self._connected:
            raise VaultConnectionError("Not connected to vault")

        # Check cache first
        if self._config.cache_enabled and not bypass_cache and version is None:
            cached = await self._cache.get(path)
            if cached is not None:
                self._audit.log_cache_event(path, hit=True)
                return cached
            self._audit.log_cache_event(path, hit=False)

        # Fetch from provider with retry
        last_error: Exception | None = None
        for attempt in range(self._config.max_retries + 1):
            try:
                secret = await self._provider.get_secret(path, version)

                # Cache the result
                if self._config.cache_enabled and version is None:
                    # Use secret expiry or default TTL
                    ttl = self._config.cache_ttl_seconds
                    if secret.metadata.expires_at:
                        remaining = secret.metadata.time_until_expiry
                        if remaining:
                            ttl = min(ttl, int(remaining.total_seconds()))
                    await self._cache.set(path, secret, ttl)

                self._audit.log_read(
                    path=path,
                    success=True,
                    workflow_id=self._workflow_id,
                    robot_id=self._robot_id,
                )
                return secret

            except SecretNotFoundError:
                self._audit.log_read(
                    path=path,
                    success=False,
                    workflow_id=self._workflow_id,
                    robot_id=self._robot_id,
                    error="Secret not found",
                )
                raise

            except Exception as e:
                last_error = e
                if attempt < self._config.max_retries:
                    logger.warning(
                        f"Vault read attempt {attempt + 1} failed for {path}: {e}. "
                        f"Retrying in {self._config.retry_delay_seconds}s..."
                    )
                    await asyncio.sleep(self._config.retry_delay_seconds)

        self._audit.log_read(
            path=path,
            success=False,
            workflow_id=self._workflow_id,
            robot_id=self._robot_id,
            error=str(last_error),
        )
        raise VaultError(
            f"Failed to read secret after {self._config.max_retries + 1} attempts: {last_error}",
            path=path,
        )

    async def put_secret(
        self,
        path: str,
        data: dict[str, Any],
        credential_type: CredentialType = CredentialType.CUSTOM,
        metadata: dict[str, Any] | None = None,
    ) -> SecretMetadata:
        """
        Store a secret in vault.

        Args:
            path: Secret path
            data: Secret data
            credential_type: Type of credential
            metadata: Optional custom metadata

        Returns:
            SecretMetadata for stored secret
        """
        if not self._connected:
            raise VaultConnectionError("Not connected to vault")

        try:
            result = await self._provider.put_secret(path, data, credential_type, metadata)
            await self._cache.invalidate(path)
            self._audit.log_write(path=path, success=True)
            logger.info(f"Secret stored at {path} (version {result.version})")
            return result
        except Exception as e:
            self._audit.log_write(path=path, success=False, error=str(e))
            raise

    async def delete_secret(self, path: str) -> bool:
        """Delete a secret from vault."""
        if not self._connected:
            raise VaultConnectionError("Not connected to vault")

        try:
            result = await self._provider.delete_secret(path)
            await self._cache.invalidate(path)
            self._audit.log(
                AuditEvent(
                    event_type=AuditEventType.SECRET_DELETE,
                    path=path,
                    success=True,
                )
            )
            return result
        except Exception as e:
            self._audit.log(
                AuditEvent(
                    event_type=AuditEventType.SECRET_DELETE,
                    path=path,
                    success=False,
                    error_message=str(e),
                )
            )
            raise

    async def list_secrets(self, path_prefix: str) -> list[str]:
        """List secrets under a path prefix."""
        if not self._connected:
            raise VaultConnectionError("Not connected to vault")
        return await self._provider.list_secrets(path_prefix)

    async def get_dynamic_secret(
        self,
        path: str,
        role: str,
        ttl: int | None = None,
    ) -> SecretValue:
        """Get a dynamically generated secret."""
        if not self._connected:
            raise VaultConnectionError("Not connected to vault")

        secret = await self._provider.get_dynamic_secret(path, role, ttl)
        self._audit.log_read(
            path=f"{path}/{role}",
            success=True,
            workflow_id=self._workflow_id,
            robot_id=self._robot_id,
        )
        return secret

    async def renew_lease(
        self,
        lease_id: str,
        increment: int | None = None,
    ) -> int:
        """Renew a secret lease."""
        if not self._connected:
            raise VaultConnectionError("Not connected to vault")

        duration = await self._provider.renew_lease(lease_id, increment)
        self._audit.log(
            AuditEvent(
                event_type=AuditEventType.SECRET_LEASE_RENEW,
                metadata={"lease_id": lease_id, "new_duration": duration},
            )
        )
        return duration

    async def revoke_lease(self, lease_id: str) -> None:
        """Revoke a secret lease."""
        if not self._connected:
            raise VaultConnectionError("Not connected to vault")

        await self._provider.revoke_lease(lease_id)
        self._audit.log(
            AuditEvent(
                event_type=AuditEventType.SECRET_LEASE_REVOKE,
                metadata={"lease_id": lease_id},
            )
        )

    async def rotate_secret(self, path: str) -> SecretMetadata:
        """Trigger secret rotation."""
        if not self._connected:
            raise VaultConnectionError("Not connected to vault")

        result = await self._provider.rotate_secret(path)
        await self._cache.invalidate(path)
        self._audit.log(
            AuditEvent(
                event_type=AuditEventType.SECRET_ROTATE,
                path=path,
                metadata={"new_version": result.version},
            )
        )
        return result

    async def invalidate_cache(self, path: str | None = None) -> int:
        """
        Invalidate cache entries.

        Args:
            path: Specific path or prefix to invalidate. If None, clears all.

        Returns:
            Number of entries invalidated
        """
        if path is None:
            size = len(self._cache._cache)
            await self._cache.clear()
            return size
        elif path.endswith("/"):
            return await self._cache.invalidate_prefix(path)
        else:
            return 1 if await self._cache.invalidate(path) else 0

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return self._cache.get_stats()

    def get_audit_events(self, count: int = 100) -> list[AuditEvent]:
        """Get recent audit events."""
        return self._audit.get_recent_events(count)

    async def __aenter__(self) -> "VaultClient":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        """Async context manager exit."""
        await self.disconnect()
        return False
