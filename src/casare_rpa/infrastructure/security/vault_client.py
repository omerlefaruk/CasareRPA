"""
CasareRPA - Vault Client Core Module.

Provides unified interface for secret management with multiple backend support.
Designed for enterprise RPA security requirements:
- Dynamic secret generation
- Automatic rotation handling
- Audit logging integration
- TTL-based caching with automatic refresh
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum, auto
from typing import Any, Dict, List, Optional, TypeVar, Generic
import asyncio
import hashlib
import secrets

from pydantic import BaseModel, Field, SecretStr, field_validator
from loguru import logger


# =============================================================================
# ENUMS
# =============================================================================


class VaultBackend(str, Enum):
    """Supported vault backend types."""

    HASHICORP = "hashicorp"
    SUPABASE = "supabase"
    SQLITE = "sqlite"  # Development fallback


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

    def __init__(self, message: str, path: Optional[str] = None) -> None:
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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = Field(
        default=None, description="Expiration time for dynamic secrets"
    )
    credential_type: CredentialType = Field(default=CredentialType.CUSTOM)
    is_dynamic: bool = Field(
        default=False, description="Whether this is a dynamically generated secret"
    )
    lease_id: Optional[str] = Field(
        default=None, description="Lease ID for dynamic secrets"
    )
    lease_duration: Optional[int] = Field(
        default=None, description="Lease duration in seconds"
    )
    renewable: bool = Field(
        default=False, description="Whether the lease can be renewed"
    )
    custom_metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """Check if the secret has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def time_until_expiry(self) -> Optional[timedelta]:
        """Get time remaining until expiration."""
        if self.expires_at is None:
            return None
        remaining = self.expires_at - datetime.now(timezone.utc)
        return remaining if remaining.total_seconds() > 0 else timedelta(0)


class SecretValue(BaseModel):
    """Container for secret data with metadata."""

    data: Dict[str, Any] = Field(..., description="Secret key-value pairs")
    metadata: SecretMetadata = Field(...)

    model_config = {"extra": "forbid"}

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the secret data."""
        return self.data.get(key, default)

    def get_username(self) -> Optional[str]:
        """Extract username from common credential formats."""
        for key in ["username", "user", "login", "email", "user_id"]:
            if key in self.data:
                return str(self.data[key])
        return None

    def get_password(self) -> Optional[str]:
        """Extract password from common credential formats."""
        for key in ["password", "pass", "secret", "pwd", "passwd"]:
            if key in self.data:
                return str(self.data[key])
        return None

    def get_api_key(self) -> Optional[str]:
        """Extract API key from common formats."""
        for key in ["api_key", "apikey", "key", "token", "access_token"]:
            if key in self.data:
                return str(self.data[key])
        return None


class AuditEvent(BaseModel):
    """Audit log event for secret operations."""

    event_id: str = Field(default_factory=lambda: secrets.token_hex(16))
    event_type: AuditEventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    path: Optional[str] = None
    workflow_id: Optional[str] = None
    robot_id: Optional[str] = None
    user_id: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    client_ip: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

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

    backend: VaultBackend = Field(
        default=VaultBackend.SQLITE, description="Vault backend to use"
    )

    # HashiCorp Vault settings
    hashicorp_url: Optional[str] = Field(
        default=None, description="HashiCorp Vault server URL"
    )
    hashicorp_token: Optional[SecretStr] = Field(
        default=None, description="HashiCorp Vault token"
    )
    hashicorp_namespace: Optional[str] = Field(
        default=None, description="Vault namespace for enterprise"
    )
    hashicorp_mount_point: str = Field(
        default="secret", description="KV secrets engine mount point"
    )
    hashicorp_kv_version: int = Field(
        default=2, ge=1, le=2, description="KV secrets engine version"
    )

    # Supabase Vault settings
    supabase_url: Optional[str] = Field(
        default=None, description="Supabase project URL"
    )
    supabase_key: Optional[SecretStr] = Field(
        default=None, description="Supabase service role key"
    )

    # SQLite fallback settings
    sqlite_path: str = Field(
        default=".casare/vault.db", description="Path to SQLite vault database"
    )
    sqlite_encryption_key: Optional[SecretStr] = Field(
        default=None, description="Encryption key for SQLite vault"
    )

    # Cache settings
    cache_enabled: bool = Field(default=True, description="Enable secret caching")
    cache_ttl_seconds: int = Field(
        default=300, ge=0, description="Cache TTL in seconds"
    )
    cache_max_size: int = Field(default=1000, ge=1, description="Maximum cache entries")

    # Retry settings
    max_retries: int = Field(default=3, ge=0, description="Max retry attempts")
    retry_delay_seconds: float = Field(
        default=1.0, ge=0, description="Delay between retries"
    )

    # Audit settings
    audit_enabled: bool = Field(default=True, description="Enable audit logging")
    audit_log_reads: bool = Field(
        default=True, description="Log secret read operations"
    )

    # TLS settings
    tls_verify: bool = Field(default=True, description="Verify TLS certificates")
    tls_ca_cert: Optional[str] = Field(
        default=None, description="Path to CA certificate"
    )
    tls_client_cert: Optional[str] = Field(
        default=None, description="Path to client certificate"
    )
    tls_client_key: Optional[str] = Field(
        default=None, description="Path to client private key"
    )

    @field_validator("hashicorp_url")
    @classmethod
    def validate_hashicorp_url(cls, v: Optional[str]) -> Optional[str]:
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
        age = (datetime.now(timezone.utc) - self.cached_at).total_seconds()
        return age > self.ttl_seconds


class SecretCache:
    """Thread-safe LRU cache for secrets."""

    def __init__(self, max_size: int = 1000, default_ttl: int = 300) -> None:
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = asyncio.Lock()
        self._hits = 0
        self._misses = 0

    async def get(self, path: str) -> Optional[SecretValue]:
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

    async def set(
        self, path: str, value: SecretValue, ttl: Optional[int] = None
    ) -> None:
        """Store secret in cache."""
        async with self._lock:
            # Evict if at capacity
            if len(self._cache) >= self._max_size and path not in self._cache:
                await self._evict_lru()

            self._cache[path] = CacheEntry(
                value=value,
                cached_at=datetime.now(timezone.utc),
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

    def get_stats(self) -> Dict[str, Any]:
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
    async def get_secret(self, path: str, version: Optional[int] = None) -> SecretValue:
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
        data: Dict[str, Any],
        credential_type: CredentialType = CredentialType.CUSTOM,
        metadata: Optional[Dict[str, Any]] = None,
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
    async def list_secrets(self, path_prefix: str) -> List[str]:
        """
        List secret paths under a prefix.

        Args:
            path_prefix: Path prefix to list

        Returns:
            List of secret paths
        """
        pass

    async def get_dynamic_secret(
        self, path: str, role: str, ttl: Optional[int] = None
    ) -> SecretValue:
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
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support dynamic secrets"
        )

    async def renew_lease(self, lease_id: str, increment: Optional[int] = None) -> int:
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
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support lease renewal"
        )

    async def revoke_lease(self, lease_id: str) -> None:
        """
        Revoke a secret lease.

        Args:
            lease_id: Lease ID to revoke

        Raises:
            NotImplementedError: If backend doesn't support leases
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support lease revocation"
        )

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
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support secret rotation"
        )


# =============================================================================
# AUDIT LOGGER
# =============================================================================


class AuditLogger:
    """Handles audit logging for vault operations."""

    def __init__(self, enabled: bool = True, log_reads: bool = True) -> None:
        self._enabled = enabled
        self._log_reads = log_reads
        self._events: List[AuditEvent] = []
        self._max_buffer_size = 1000

    def log(self, event: AuditEvent) -> None:
        """Log an audit event."""
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

        # Buffer event
        self._events.append(event)
        if len(self._events) > self._max_buffer_size:
            self._events = self._events[-self._max_buffer_size :]

    def log_read(
        self,
        path: str,
        success: bool = True,
        workflow_id: Optional[str] = None,
        robot_id: Optional[str] = None,
        error: Optional[str] = None,
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
        user_id: Optional[str] = None,
        error: Optional[str] = None,
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
                event_type=AuditEventType.CACHE_HIT
                if hit
                else AuditEventType.CACHE_MISS,
                path=path,
            )
        )

    def get_recent_events(self, count: int = 100) -> List[AuditEvent]:
        """Get recent audit events."""
        return self._events[-count:]

    async def flush(self) -> None:
        """Flush buffered events (for external audit systems)."""
        # In production, this would send to external audit system
        self._events.clear()


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
        provider: Optional[VaultProvider] = None,
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
        self._workflow_id: Optional[str] = None
        self._robot_id: Optional[str] = None

    def set_context(
        self,
        workflow_id: Optional[str] = None,
        robot_id: Optional[str] = None,
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
            logger.info(
                f"Connected to vault backend: {self._config.get_backend_display_name()}"
            )
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
        version: Optional[int] = None,
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
        last_error: Optional[Exception] = None
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
        data: Dict[str, Any],
        credential_type: CredentialType = CredentialType.CUSTOM,
        metadata: Optional[Dict[str, Any]] = None,
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
            result = await self._provider.put_secret(
                path, data, credential_type, metadata
            )
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

    async def list_secrets(self, path_prefix: str) -> List[str]:
        """List secrets under a path prefix."""
        if not self._connected:
            raise VaultConnectionError("Not connected to vault")
        return await self._provider.list_secrets(path_prefix)

    async def get_dynamic_secret(
        self,
        path: str,
        role: str,
        ttl: Optional[int] = None,
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
        increment: Optional[int] = None,
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

    async def invalidate_cache(self, path: Optional[str] = None) -> int:
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

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self._cache.get_stats()

    def get_audit_events(self, count: int = 100) -> List[AuditEvent]:
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
