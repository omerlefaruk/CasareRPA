"""
CasareRPA - Vault Credential Provider.

Integrates vault with workflow execution context for transparent
credential injection into nodes that require authentication.

Design goals:
- Zero-friction credential access for nodes
- Automatic lease management for dynamic secrets
- Cached credentials with TTL refresh
- Audit trail for compliance
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

from loguru import logger

from .vault_client import (
    VaultClient,
    VaultConfig,
    VaultBackend,
    SecretValue,
    CredentialType,
    VaultError,
    SecretNotFoundError,
)


@dataclass
class CredentialLease:
    """Tracks a dynamic credential lease for automatic renewal."""

    lease_id: str
    path: str
    expires_at: datetime
    renewable: bool
    renewal_task: Optional[asyncio.Task] = None


@dataclass
class ResolvedCredential:
    """Credential data resolved from vault."""

    alias: str
    vault_path: str
    credential_type: CredentialType
    data: Dict[str, Any]
    username: Optional[str] = None
    password: Optional[str] = None
    api_key: Optional[str] = None
    connection_string: Optional[str] = None
    is_dynamic: bool = False
    expires_at: Optional[datetime] = None
    lease: Optional[CredentialLease] = None


class VaultCredentialProvider:
    """
    Provides credential resolution for workflow execution.

    Integrates with the execution context to:
    - Resolve credential aliases to vault paths
    - Fetch and cache credentials
    - Manage dynamic secret leases
    - Provide structured access to credential components

    Usage:
        provider = VaultCredentialProvider(config)
        await provider.initialize()

        # Set execution context for audit
        provider.set_execution_context(
            workflow_id="wf_123",
            robot_id="robot_01"
        )

        # Resolve a credential by alias
        cred = await provider.get_credential("erp_login")
        username = cred.username
        password = cred.password

        # Or resolve by direct vault path
        cred = await provider.get_credential_by_path("secret/prod/db")
    """

    def __init__(
        self,
        config: Optional[VaultConfig] = None,
        vault_client: Optional[VaultClient] = None,
    ) -> None:
        """
        Initialize credential provider.

        Args:
            config: Vault configuration (uses default SQLite if None)
            vault_client: Optional pre-configured vault client
        """
        if vault_client:
            self._client = vault_client
            self._owns_client = False
        else:
            self._config = config or VaultConfig(backend=VaultBackend.SQLITE)
            self._client = VaultClient(self._config)
            self._owns_client = True

        self._initialized = False
        self._leases: Dict[str, CredentialLease] = {}
        self._resolved_cache: Dict[str, ResolvedCredential] = {}
        self._alias_to_path: Dict[str, str] = {}
        self._workflow_id: Optional[str] = None
        self._robot_id: Optional[str] = None

        # Lease renewal settings
        self._lease_renewal_threshold = 0.8  # Renew at 80% of TTL
        self._lease_check_interval = 30  # Check leases every 30s
        self._lease_check_task: Optional[asyncio.Task] = None

    async def initialize(self) -> None:
        """Initialize the provider and connect to vault."""
        if self._initialized:
            return

        if self._owns_client:
            await self._client.connect()

        # Start lease monitoring
        self._lease_check_task = asyncio.create_task(self._lease_monitor_loop())

        self._initialized = True
        logger.info("VaultCredentialProvider initialized")

    async def shutdown(self) -> None:
        """Shutdown the provider and cleanup resources."""
        if not self._initialized:
            return

        # Cancel lease monitoring
        if self._lease_check_task:
            self._lease_check_task.cancel()
            try:
                await self._lease_check_task
            except asyncio.CancelledError:
                pass

        # Revoke active leases
        for lease in list(self._leases.values()):
            await self._revoke_lease(lease)

        # Disconnect client if we own it
        if self._owns_client:
            await self._client.disconnect()

        self._initialized = False
        self._resolved_cache.clear()
        self._leases.clear()
        logger.info("VaultCredentialProvider shutdown complete")

    def set_execution_context(
        self,
        workflow_id: Optional[str] = None,
        robot_id: Optional[str] = None,
    ) -> None:
        """
        Set execution context for audit logging.

        Args:
            workflow_id: Current workflow ID
            robot_id: Current robot ID
        """
        self._workflow_id = workflow_id
        self._robot_id = robot_id
        self._client.set_context(workflow_id, robot_id)

    def register_alias(self, alias: str, vault_path: str) -> None:
        """
        Register a credential alias mapping.

        Args:
            alias: Local alias (e.g., "erp_login")
            vault_path: Vault path (e.g., "secret/prod/erp")
        """
        self._alias_to_path[alias] = vault_path
        logger.debug(f"Registered credential alias: {alias} -> {vault_path}")

    def register_bindings(self, bindings: Dict[str, str]) -> None:
        """
        Register multiple credential bindings.

        Args:
            bindings: Dictionary mapping alias to vault path
        """
        self._alias_to_path.update(bindings)
        logger.debug(f"Registered {len(bindings)} credential bindings")

    async def get_credential(
        self,
        alias: str,
        required: bool = True,
    ) -> Optional[ResolvedCredential]:
        """
        Get credential by alias.

        Args:
            alias: Credential alias
            required: If True, raises error when not found

        Returns:
            ResolvedCredential or None if not required and not found

        Raises:
            SecretNotFoundError: If required and alias not registered
            VaultError: If vault operation fails
        """
        # Resolve alias to path
        vault_path = self._alias_to_path.get(alias)
        if not vault_path:
            if required:
                raise SecretNotFoundError(
                    f"Credential alias not registered: {alias}",
                    path=alias,
                )
            return None

        return await self.get_credential_by_path(vault_path, alias=alias)

    async def get_credential_by_path(
        self,
        vault_path: str,
        alias: Optional[str] = None,
    ) -> ResolvedCredential:
        """
        Get credential by direct vault path.

        Args:
            vault_path: Full vault path
            alias: Optional alias for reference

        Returns:
            ResolvedCredential with all extracted fields
        """
        # Check cache first
        cache_key = vault_path
        if cache_key in self._resolved_cache:
            cached = self._resolved_cache[cache_key]
            # Check if still valid
            if not cached.expires_at or cached.expires_at > datetime.utcnow():
                return cached

        # Fetch from vault
        secret = await self._client.get_secret(vault_path)

        # Build resolved credential
        resolved = self._build_resolved_credential(
            secret=secret,
            alias=alias or vault_path,
            vault_path=vault_path,
        )

        # Handle dynamic secret lease
        if secret.metadata.is_dynamic and secret.metadata.lease_id:
            lease = CredentialLease(
                lease_id=secret.metadata.lease_id,
                path=vault_path,
                expires_at=secret.metadata.expires_at or datetime.utcnow(),
                renewable=secret.metadata.renewable,
            )
            self._leases[vault_path] = lease
            resolved.lease = lease

        # Cache the resolved credential
        self._resolved_cache[cache_key] = resolved

        return resolved

    async def get_dynamic_credential(
        self,
        engine_path: str,
        role: str,
        alias: Optional[str] = None,
        ttl: Optional[int] = None,
    ) -> ResolvedCredential:
        """
        Get dynamically generated credentials.

        Args:
            engine_path: Dynamic secrets engine path (e.g., "database")
            role: Role name for credential generation
            alias: Optional alias for reference
            ttl: Optional TTL in seconds

        Returns:
            ResolvedCredential with generated credentials
        """
        secret = await self._client.get_dynamic_secret(engine_path, role, ttl)

        full_path = f"{engine_path}/creds/{role}"
        resolved = self._build_resolved_credential(
            secret=secret,
            alias=alias or f"{engine_path}_{role}",
            vault_path=full_path,
        )
        resolved.is_dynamic = True

        # Track lease for renewal
        if secret.metadata.lease_id:
            lease = CredentialLease(
                lease_id=secret.metadata.lease_id,
                path=full_path,
                expires_at=secret.metadata.expires_at or datetime.utcnow(),
                renewable=secret.metadata.renewable,
            )
            self._leases[full_path] = lease
            resolved.lease = lease

            logger.info(
                f"Acquired dynamic credential for {role} "
                f"(expires: {secret.metadata.expires_at})"
            )

        return resolved

    def _build_resolved_credential(
        self,
        secret: SecretValue,
        alias: str,
        vault_path: str,
    ) -> ResolvedCredential:
        """Build ResolvedCredential from SecretValue."""
        data = secret.data

        return ResolvedCredential(
            alias=alias,
            vault_path=vault_path,
            credential_type=secret.metadata.credential_type,
            data=data,
            username=secret.get_username(),
            password=secret.get_password(),
            api_key=secret.get_api_key(),
            connection_string=data.get("connection_string") or data.get("dsn"),
            is_dynamic=secret.metadata.is_dynamic,
            expires_at=secret.metadata.expires_at,
        )

    async def _lease_monitor_loop(self) -> None:
        """Background task to monitor and renew leases."""
        while True:
            try:
                await asyncio.sleep(self._lease_check_interval)
                await self._check_leases()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Lease monitor error: {e}")

    async def _check_leases(self) -> None:
        """Check all leases and renew if needed."""
        now = datetime.utcnow()
        to_remove: List[str] = []

        for path, lease in self._leases.items():
            if not lease.renewable:
                continue

            # Calculate renewal threshold
            total_duration = (lease.expires_at - now).total_seconds()
            if total_duration <= 0:
                # Lease expired
                to_remove.append(path)
                logger.warning(f"Lease expired for {path}")
                continue

            # Check if we should renew
            remaining_pct = total_duration / max(total_duration, 1)
            if remaining_pct < (1 - self._lease_renewal_threshold):
                await self._renew_lease(lease)

        # Remove expired leases
        for path in to_remove:
            del self._leases[path]
            self._resolved_cache.pop(path, None)

    async def _renew_lease(self, lease: CredentialLease) -> None:
        """Renew a credential lease."""
        try:
            new_duration = await self._client.renew_lease(lease.lease_id)
            lease.expires_at = datetime.utcnow() + timedelta(seconds=new_duration)
            logger.info(f"Renewed lease for {lease.path} (new TTL: {new_duration}s)")
        except Exception as e:
            logger.error(f"Failed to renew lease for {lease.path}: {e}")

    async def _revoke_lease(self, lease: CredentialLease) -> None:
        """Revoke a credential lease."""
        try:
            await self._client.revoke_lease(lease.lease_id)
            logger.info(f"Revoked lease for {lease.path}")
        except Exception as e:
            logger.warning(f"Failed to revoke lease for {lease.path}: {e}")

    async def invalidate_credential(self, alias_or_path: str) -> bool:
        """
        Invalidate a cached credential.

        Args:
            alias_or_path: Credential alias or vault path

        Returns:
            True if credential was invalidated
        """
        # Resolve alias to path if needed
        vault_path = self._alias_to_path.get(alias_or_path, alias_or_path)

        # Remove from cache
        removed = vault_path in self._resolved_cache
        self._resolved_cache.pop(vault_path, None)

        # Revoke lease if present
        lease = self._leases.pop(vault_path, None)
        if lease:
            await self._revoke_lease(lease)

        # Invalidate in vault client cache
        await self._client.invalidate_cache(vault_path)

        return removed

    def get_registered_aliases(self) -> Dict[str, str]:
        """Get all registered credential aliases and their paths."""
        return self._alias_to_path.copy()

    def get_active_leases(self) -> List[Dict[str, Any]]:
        """Get information about active credential leases."""
        return [
            {
                "path": lease.path,
                "lease_id": lease.lease_id,
                "expires_at": lease.expires_at.isoformat(),
                "renewable": lease.renewable,
                "time_remaining": (
                    lease.expires_at - datetime.utcnow()
                ).total_seconds(),
            }
            for lease in self._leases.values()
        ]

    async def __aenter__(self) -> "VaultCredentialProvider":
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        """Async context manager exit."""
        await self.shutdown()
        return False


# =============================================================================
# INTEGRATION HELPERS
# =============================================================================


def create_credential_resolver(
    config: Optional[VaultConfig] = None,
) -> VaultCredentialProvider:
    """
    Create a credential resolver with default configuration.

    Args:
        config: Optional vault configuration

    Returns:
        VaultCredentialProvider instance (not initialized)
    """
    return VaultCredentialProvider(config)


async def resolve_credentials_for_node(
    provider: VaultCredentialProvider,
    credential_requirements: Dict[str, Dict[str, Any]],
) -> Dict[str, ResolvedCredential]:
    """
    Resolve all credentials required by a node.

    Args:
        provider: VaultCredentialProvider instance
        credential_requirements: Dict mapping alias to requirement spec:
            {
                "db_creds": {"required": True, "type": "database"},
                "api_key": {"required": False, "path": "secret/api/key"}
            }

    Returns:
        Dict mapping alias to ResolvedCredential
    """
    results: Dict[str, ResolvedCredential] = {}

    for alias, spec in credential_requirements.items():
        required = spec.get("required", True)

        # Check if direct path specified
        if "path" in spec:
            try:
                cred = await provider.get_credential_by_path(spec["path"], alias=alias)
                results[alias] = cred
            except SecretNotFoundError:
                if required:
                    raise
        else:
            # Use alias resolution
            cred = await provider.get_credential(alias, required=required)
            if cred:
                results[alias] = cred

    return results
