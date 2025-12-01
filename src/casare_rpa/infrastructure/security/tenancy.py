"""
CasareRPA - Multi-Tenancy Module.

Provides comprehensive multi-tenancy support for enterprise deployments:
- Tenant isolation with PostgreSQL Row-Level Security (RLS)
- Resource quotas and usage tracking
- SSO integration (SAML, OAuth2, OIDC)
- API key management
- Workspace/team support
- Audit logging
"""

import asyncio
import hashlib
import secrets
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional, Set, TypeVar
from uuid import UUID, uuid4

from loguru import logger
from pydantic import BaseModel, EmailStr, Field, SecretStr, field_validator

from casare_rpa.infrastructure.security.merkle_audit import (
    MerkleAuditService,
    AuditEntry as MerkleAuditEntry,
    AuditAction as MerkleAuditAction,
    ResourceType as MerkleResourceType,
    get_audit_service as get_merkle_audit_service,
)


# =============================================================================
# ENUMS
# =============================================================================


class TenantStatus(str, Enum):
    """Tenant account status."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"
    ARCHIVED = "archived"


class SubscriptionTier(str, Enum):
    """Subscription tiers with different quotas."""

    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class SSOProvider(str, Enum):
    """Supported SSO providers."""

    SAML = "saml"
    OAUTH2 = "oauth2"
    OIDC = "oidc"


class APIKeyStatus(str, Enum):
    """API key status."""

    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class AuditAction(str, Enum):
    """Audit log action types."""

    # Tenant actions
    TENANT_CREATED = "tenant.created"
    TENANT_UPDATED = "tenant.updated"
    TENANT_SUSPENDED = "tenant.suspended"
    TENANT_ACTIVATED = "tenant.activated"

    # User actions
    USER_INVITED = "user.invited"
    USER_JOINED = "user.joined"
    USER_REMOVED = "user.removed"
    USER_ROLE_CHANGED = "user.role_changed"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_LOGIN_FAILED = "user.login_failed"

    # Workspace actions
    WORKSPACE_CREATED = "workspace.created"
    WORKSPACE_UPDATED = "workspace.updated"
    WORKSPACE_DELETED = "workspace.deleted"
    WORKSPACE_MEMBER_ADDED = "workspace.member_added"
    WORKSPACE_MEMBER_REMOVED = "workspace.member_removed"

    # Workflow actions
    WORKFLOW_CREATED = "workflow.created"
    WORKFLOW_UPDATED = "workflow.updated"
    WORKFLOW_DELETED = "workflow.deleted"
    WORKFLOW_PUBLISHED = "workflow.published"
    WORKFLOW_EXECUTED = "workflow.executed"

    # Robot actions
    ROBOT_REGISTERED = "robot.registered"
    ROBOT_UPDATED = "robot.updated"
    ROBOT_DELETED = "robot.deleted"

    # API key actions
    APIKEY_CREATED = "apikey.created"
    APIKEY_REVOKED = "apikey.revoked"

    # Credential actions
    CREDENTIAL_CREATED = "credential.created"
    CREDENTIAL_UPDATED = "credential.updated"
    CREDENTIAL_DELETED = "credential.deleted"
    CREDENTIAL_ACCESSED = "credential.accessed"

    # Settings actions
    SETTINGS_UPDATED = "settings.updated"
    SSO_CONFIGURED = "sso.configured"
    QUOTA_UPDATED = "quota.updated"


# =============================================================================
# EXCEPTIONS
# =============================================================================


class TenancyError(Exception):
    """Base exception for tenancy operations."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(message)


class TenantNotFoundError(TenancyError):
    """Raised when tenant does not exist."""

    def __init__(self, tenant_id: UUID) -> None:
        super().__init__(
            f"Tenant not found: {tenant_id}", {"tenant_id": str(tenant_id)}
        )
        self.tenant_id = tenant_id


class TenantSuspendedError(TenancyError):
    """Raised when tenant is suspended."""

    def __init__(self, tenant_id: UUID) -> None:
        super().__init__(
            f"Tenant is suspended: {tenant_id}", {"tenant_id": str(tenant_id)}
        )
        self.tenant_id = tenant_id


class QuotaExceededError(TenancyError):
    """Raised when tenant exceeds resource quota."""

    def __init__(
        self,
        tenant_id: UUID,
        resource_type: str,
        current: int,
        limit: int,
    ) -> None:
        super().__init__(
            f"Quota exceeded for {resource_type}: {current}/{limit}",
            {
                "tenant_id": str(tenant_id),
                "resource_type": resource_type,
                "current": current,
                "limit": limit,
            },
        )
        self.tenant_id = tenant_id
        self.resource_type = resource_type
        self.current = current
        self.limit = limit


class RateLimitExceededError(TenancyError):
    """Raised when tenant exceeds rate limit."""

    def __init__(
        self,
        tenant_id: UUID,
        limit_type: str,
        retry_after_seconds: int,
    ) -> None:
        super().__init__(
            f"Rate limit exceeded: {limit_type}. Retry after {retry_after_seconds}s",
            {
                "tenant_id": str(tenant_id),
                "limit_type": limit_type,
                "retry_after_seconds": retry_after_seconds,
            },
        )
        self.tenant_id = tenant_id
        self.limit_type = limit_type
        self.retry_after_seconds = retry_after_seconds


class InvalidAPIKeyError(TenancyError):
    """Raised when API key is invalid or revoked."""

    def __init__(self, reason: str = "Invalid API key") -> None:
        super().__init__(reason)


# =============================================================================
# DATA MODELS
# =============================================================================


class ResourceQuotas(BaseModel):
    """Resource quotas for a tenant."""

    max_workflows: int = Field(default=100, ge=0)
    max_robots: int = Field(default=10, ge=0)
    max_executions_per_hour: int = Field(default=1000, ge=0)
    max_storage_mb: int = Field(default=10240, ge=0)
    max_team_members: int = Field(default=50, ge=0)
    max_workspaces: int = Field(default=10, ge=0)
    max_api_keys: int = Field(default=20, ge=0)
    max_concurrent_executions: int = Field(default=5, ge=0)

    @classmethod
    def for_tier(cls, tier: SubscriptionTier) -> "ResourceQuotas":
        """Get default quotas for a subscription tier."""
        tier_quotas = {
            SubscriptionTier.FREE: cls(
                max_workflows=5,
                max_robots=1,
                max_executions_per_hour=50,
                max_storage_mb=512,
                max_team_members=3,
                max_workspaces=1,
                max_api_keys=2,
                max_concurrent_executions=1,
            ),
            SubscriptionTier.STARTER: cls(
                max_workflows=25,
                max_robots=3,
                max_executions_per_hour=200,
                max_storage_mb=2048,
                max_team_members=10,
                max_workspaces=3,
                max_api_keys=5,
                max_concurrent_executions=2,
            ),
            SubscriptionTier.PROFESSIONAL: cls(
                max_workflows=100,
                max_robots=10,
                max_executions_per_hour=1000,
                max_storage_mb=10240,
                max_team_members=50,
                max_workspaces=10,
                max_api_keys=20,
                max_concurrent_executions=5,
            ),
            SubscriptionTier.ENTERPRISE: cls(
                max_workflows=10000,
                max_robots=100,
                max_executions_per_hour=100000,
                max_storage_mb=102400,
                max_team_members=1000,
                max_workspaces=100,
                max_api_keys=100,
                max_concurrent_executions=50,
            ),
        }
        return tier_quotas.get(tier, cls())


class ResourceUsage(BaseModel):
    """Current resource usage for a tenant."""

    workflow_count: int = 0
    robot_count: int = 0
    storage_mb: int = 0
    team_member_count: int = 0
    workspace_count: int = 0
    api_key_count: int = 0
    executions_this_hour: int = 0
    concurrent_executions: int = 0


class SSOConfig(BaseModel):
    """SSO configuration for a tenant."""

    provider: SSOProvider
    enabled: bool = True

    # SAML settings
    saml_entity_id: Optional[str] = None
    saml_sso_url: Optional[str] = None
    saml_slo_url: Optional[str] = None
    saml_certificate: Optional[str] = None
    saml_attribute_mapping: Optional[Dict[str, str]] = None

    # OAuth2/OIDC settings
    oauth_client_id: Optional[str] = None
    oauth_client_secret: Optional[SecretStr] = None
    oauth_authorize_url: Optional[str] = None
    oauth_token_url: Optional[str] = None
    oauth_userinfo_url: Optional[str] = None
    oauth_scopes: List[str] = Field(
        default_factory=lambda: ["openid", "email", "profile"]
    )

    # OIDC-specific
    oidc_issuer: Optional[str] = None
    oidc_jwks_uri: Optional[str] = None

    # Common settings
    domain_restriction: Optional[str] = None
    auto_provision_users: bool = True
    default_role_id: Optional[UUID] = None

    def validate_config(self) -> List[str]:
        """Validate SSO configuration and return any errors."""
        errors: List[str] = []

        if self.provider == SSOProvider.SAML:
            if not self.saml_entity_id:
                errors.append("SAML Entity ID is required")
            if not self.saml_sso_url:
                errors.append("SAML SSO URL is required")
            if not self.saml_certificate:
                errors.append("SAML Certificate is required")

        elif self.provider in (SSOProvider.OAUTH2, SSOProvider.OIDC):
            if not self.oauth_client_id:
                errors.append("OAuth Client ID is required")
            if not self.oauth_client_secret:
                errors.append("OAuth Client Secret is required")

            if self.provider == SSOProvider.OIDC:
                if not self.oidc_issuer:
                    errors.append("OIDC Issuer is required")
            else:
                if not self.oauth_authorize_url:
                    errors.append("OAuth Authorize URL is required")
                if not self.oauth_token_url:
                    errors.append("OAuth Token URL is required")

        return errors


class Tenant(BaseModel):
    """Represents a tenant organization."""

    id: UUID = Field(default_factory=uuid4)
    name: str
    slug: str
    display_name: str
    admin_email: EmailStr
    billing_email: Optional[EmailStr] = None

    status: TenantStatus = TenantStatus.ACTIVE
    subscription_tier: SubscriptionTier = SubscriptionTier.FREE
    subscription_expires_at: Optional[datetime] = None

    sso_enabled: bool = False
    sso_config: Optional[SSOConfig] = None

    quotas: ResourceQuotas = Field(default_factory=ResourceQuotas)
    usage: ResourceUsage = Field(default_factory=ResourceUsage)
    settings: Dict[str, Any] = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[UUID] = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Ensure slug is URL-safe."""
        import re

        if not re.match(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$", v):
            raise ValueError(
                "Slug must be lowercase alphanumeric with optional hyphens"
            )
        return v

    @property
    def is_active(self) -> bool:
        """Check if tenant is active."""
        return self.status == TenantStatus.ACTIVE

    @property
    def is_subscription_valid(self) -> bool:
        """Check if subscription is valid."""
        if self.subscription_expires_at is None:
            return True
        return datetime.now(timezone.utc) < self.subscription_expires_at

    def check_quota(self, resource_type: str) -> bool:
        """
        Check if tenant has quota for resource type.

        Args:
            resource_type: Type of resource (workflow, robot, etc.)

        Returns:
            True if within quota
        """
        quota_checks = {
            "workflow": (self.usage.workflow_count, self.quotas.max_workflows),
            "robot": (self.usage.robot_count, self.quotas.max_robots),
            "team_member": (self.usage.team_member_count, self.quotas.max_team_members),
            "workspace": (self.usage.workspace_count, self.quotas.max_workspaces),
            "api_key": (self.usage.api_key_count, self.quotas.max_api_keys),
            "storage": (self.usage.storage_mb, self.quotas.max_storage_mb),
        }

        if resource_type not in quota_checks:
            return True

        current, limit = quota_checks[resource_type]
        return current < limit

    def get_quota_remaining(self, resource_type: str) -> int:
        """Get remaining quota for resource type."""
        quota_map = {
            "workflow": (self.usage.workflow_count, self.quotas.max_workflows),
            "robot": (self.usage.robot_count, self.quotas.max_robots),
            "team_member": (self.usage.team_member_count, self.quotas.max_team_members),
            "workspace": (self.usage.workspace_count, self.quotas.max_workspaces),
            "api_key": (self.usage.api_key_count, self.quotas.max_api_keys),
            "execution": (
                self.usage.executions_this_hour,
                self.quotas.max_executions_per_hour,
            ),
        }

        if resource_type not in quota_map:
            return -1

        current, limit = quota_map[resource_type]
        return max(0, limit - current)


class Workspace(BaseModel):
    """Represents a workspace/team within a tenant."""

    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    is_default: bool = False
    settings: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[UUID] = None


class APIKey(BaseModel):
    """Represents an API key for programmatic access."""

    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    user_id: Optional[UUID] = None
    name: str
    description: Optional[str] = None

    key_prefix: str
    key_hash: str

    role_id: Optional[UUID] = None
    scopes: List[str] = Field(default_factory=list)

    allowed_ips: Optional[List[str]] = None
    allowed_origins: Optional[List[str]] = None
    rate_limit_per_minute: Optional[int] = None

    status: APIKeyStatus = APIKeyStatus.ACTIVE
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    use_count: int = 0

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[UUID] = None

    @property
    def is_valid(self) -> bool:
        """Check if API key is valid."""
        if self.status != APIKeyStatus.ACTIVE:
            return False
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return False
        return True

    @classmethod
    def generate(
        cls,
        tenant_id: UUID,
        name: str,
        prefix: str = "crpa",
        **kwargs: Any,
    ) -> tuple["APIKey", str]:
        """
        Generate a new API key.

        Returns:
            Tuple of (APIKey instance, raw key string)
        """
        raw_key = f"{prefix}_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_prefix = raw_key[:12]

        api_key = cls(
            tenant_id=tenant_id,
            name=name,
            key_prefix=key_prefix,
            key_hash=key_hash,
            **kwargs,
        )

        return api_key, raw_key

    def verify(self, raw_key: str) -> bool:
        """Verify a raw API key against this key's hash."""
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        return secrets.compare_digest(key_hash, self.key_hash)


class AuditLogEntry(BaseModel):
    """Represents an audit log entry."""

    id: int = 0
    tenant_id: UUID
    user_id: Optional[UUID] = None
    api_key_id: Optional[UUID] = None
    actor_type: str = "user"
    actor_ip: Optional[str] = None
    user_agent: Optional[str] = None

    action: AuditAction
    resource_type: str
    resource_id: Optional[str] = None

    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    success: bool = True
    error_message: Optional[str] = None

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# =============================================================================
# TENANT CONTEXT
# =============================================================================


@dataclass
class TenantContext:
    """
    Holds current tenant context for request processing.

    Used to set PostgreSQL session variables for RLS.
    """

    tenant_id: UUID
    user_id: Optional[UUID] = None
    workspace_id: Optional[UUID] = None
    api_key_id: Optional[UUID] = None
    role_ids: List[UUID] = None
    permissions: Set[str] = None
    is_system: bool = False

    def __post_init__(self) -> None:
        if self.role_ids is None:
            self.role_ids = []
        if self.permissions is None:
            self.permissions = set()


class TenantContextManager:
    """
    Manages tenant context for database operations.

    Sets PostgreSQL session variables for Row-Level Security.
    """

    def __init__(self) -> None:
        self._current_context: Optional[TenantContext] = None
        self._context_stack: List[TenantContext] = []
        self._lock = asyncio.Lock()

    @property
    def current(self) -> Optional[TenantContext]:
        """Get current tenant context."""
        return self._current_context

    async def set_context(self, context: TenantContext) -> None:
        """
        Set current tenant context.

        Args:
            context: Tenant context to set
        """
        async with self._lock:
            if self._current_context:
                self._context_stack.append(self._current_context)
            self._current_context = context
            logger.debug(f"Set tenant context: tenant={context.tenant_id}")

    async def clear_context(self) -> None:
        """Clear current tenant context."""
        async with self._lock:
            if self._context_stack:
                self._current_context = self._context_stack.pop()
            else:
                self._current_context = None
            logger.debug("Cleared tenant context")

    @asynccontextmanager
    async def with_context(
        self,
        context: TenantContext,
    ) -> AsyncGenerator[TenantContext, None]:
        """
        Context manager for temporary tenant context.

        Usage:
            async with context_manager.with_context(ctx) as ctx:
                # Operations use ctx's tenant
                ...
        """
        await self.set_context(context)
        try:
            yield context
        finally:
            await self.clear_context()

    @asynccontextmanager
    async def with_tenant(
        self,
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
    ) -> AsyncGenerator[TenantContext, None]:
        """
        Convenience method to set context by tenant ID.

        Args:
            tenant_id: Tenant ID
            user_id: Optional user ID
        """
        context = TenantContext(tenant_id=tenant_id, user_id=user_id)
        async with self.with_context(context) as ctx:
            yield ctx

    def get_rls_parameters(self) -> Dict[str, str]:
        """
        Get parameters for PostgreSQL RLS.

        Returns:
            Dict with session parameter values
        """
        if not self._current_context:
            return {}

        params = {
            "app.current_tenant_id": str(self._current_context.tenant_id),
        }
        if self._current_context.user_id:
            params["app.current_user_id"] = str(self._current_context.user_id)

        return params


# =============================================================================
# TENANT SERVICE
# =============================================================================


class TenantService:
    """
    Service for tenant management operations.

    Handles tenant CRUD, quota management, and SSO configuration.
    """

    def __init__(self, context_manager: TenantContextManager) -> None:
        self._context_manager = context_manager
        self._tenants: Dict[UUID, Tenant] = {}
        self._tenants_by_slug: Dict[str, UUID] = {}
        self._lock = asyncio.Lock()

    async def create_tenant(
        self,
        name: str,
        slug: str,
        admin_email: str,
        subscription_tier: SubscriptionTier = SubscriptionTier.FREE,
        created_by: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Tenant:
        """
        Create a new tenant.

        Args:
            name: Tenant name
            slug: URL-safe slug (unique)
            admin_email: Admin email address
            subscription_tier: Subscription tier
            created_by: Creating user ID
            **kwargs: Additional tenant fields

        Returns:
            Created Tenant

        Raises:
            TenancyError: If slug already exists
        """
        async with self._lock:
            if slug in self._tenants_by_slug:
                raise TenancyError(f"Tenant with slug '{slug}' already exists")

            quotas = ResourceQuotas.for_tier(subscription_tier)

            tenant = Tenant(
                name=name,
                slug=slug,
                display_name=kwargs.pop("display_name", name),
                admin_email=admin_email,
                subscription_tier=subscription_tier,
                quotas=quotas,
                created_by=created_by,
                **kwargs,
            )

            self._tenants[tenant.id] = tenant
            self._tenants_by_slug[slug] = tenant.id

            logger.info(
                f"Created tenant: {tenant.name} (id={tenant.id}, tier={subscription_tier.value})"
            )

            return tenant

    async def get_tenant(self, tenant_id: UUID) -> Tenant:
        """
        Get tenant by ID.

        Args:
            tenant_id: Tenant ID

        Returns:
            Tenant

        Raises:
            TenantNotFoundError: If tenant doesn't exist
        """
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            raise TenantNotFoundError(tenant_id)
        return tenant

    async def get_tenant_by_slug(self, slug: str) -> Tenant:
        """
        Get tenant by slug.

        Args:
            slug: Tenant slug

        Returns:
            Tenant

        Raises:
            TenantNotFoundError: If tenant doesn't exist
        """
        tenant_id = self._tenants_by_slug.get(slug)
        if not tenant_id:
            raise TenantNotFoundError(UUID(int=0))
        return await self.get_tenant(tenant_id)

    async def update_tenant(
        self,
        tenant_id: UUID,
        **updates: Any,
    ) -> Tenant:
        """
        Update tenant fields.

        Args:
            tenant_id: Tenant ID
            **updates: Fields to update

        Returns:
            Updated Tenant
        """
        tenant = await self.get_tenant(tenant_id)

        async with self._lock:
            for key, value in updates.items():
                if hasattr(tenant, key):
                    setattr(tenant, key, value)

            tenant.updated_at = datetime.now(timezone.utc)
            logger.info(f"Updated tenant {tenant_id}: {list(updates.keys())}")

            return tenant

    async def suspend_tenant(
        self,
        tenant_id: UUID,
        reason: Optional[str] = None,
    ) -> Tenant:
        """
        Suspend a tenant.

        Args:
            tenant_id: Tenant ID
            reason: Suspension reason

        Returns:
            Suspended Tenant
        """
        tenant = await self.get_tenant(tenant_id)

        async with self._lock:
            tenant.status = TenantStatus.SUSPENDED
            tenant.updated_at = datetime.now(timezone.utc)
            if reason:
                tenant.settings["suspension_reason"] = reason
                tenant.settings["suspended_at"] = datetime.now(timezone.utc).isoformat()

            logger.warning(f"Suspended tenant {tenant_id}: {reason}")
            return tenant

    async def activate_tenant(self, tenant_id: UUID) -> Tenant:
        """
        Activate a suspended tenant.

        Args:
            tenant_id: Tenant ID

        Returns:
            Activated Tenant
        """
        tenant = await self.get_tenant(tenant_id)

        async with self._lock:
            tenant.status = TenantStatus.ACTIVE
            tenant.updated_at = datetime.now(timezone.utc)
            tenant.settings.pop("suspension_reason", None)
            tenant.settings.pop("suspended_at", None)

            logger.info(f"Activated tenant {tenant_id}")
            return tenant

    async def check_and_enforce_quota(
        self,
        tenant_id: UUID,
        resource_type: str,
        raise_on_exceed: bool = True,
    ) -> bool:
        """
        Check if tenant has quota for a resource.

        Args:
            tenant_id: Tenant ID
            resource_type: Resource type to check
            raise_on_exceed: If True, raises QuotaExceededError

        Returns:
            True if within quota

        Raises:
            QuotaExceededError: If quota exceeded and raise_on_exceed=True
        """
        tenant = await self.get_tenant(tenant_id)

        if not tenant.is_active:
            raise TenantSuspendedError(tenant_id)

        if tenant.check_quota(resource_type):
            return True

        if raise_on_exceed:
            quota_map = {
                "workflow": (tenant.usage.workflow_count, tenant.quotas.max_workflows),
                "robot": (tenant.usage.robot_count, tenant.quotas.max_robots),
                "team_member": (
                    tenant.usage.team_member_count,
                    tenant.quotas.max_team_members,
                ),
            }
            current, limit = quota_map.get(resource_type, (0, 0))
            raise QuotaExceededError(tenant_id, resource_type, current, limit)

        return False

    async def increment_usage(
        self,
        tenant_id: UUID,
        resource_type: str,
        amount: int = 1,
    ) -> None:
        """
        Increment resource usage counter.

        Args:
            tenant_id: Tenant ID
            resource_type: Resource type
            amount: Amount to increment
        """
        tenant = await self.get_tenant(tenant_id)

        async with self._lock:
            if resource_type == "workflow":
                tenant.usage.workflow_count += amount
            elif resource_type == "robot":
                tenant.usage.robot_count += amount
            elif resource_type == "team_member":
                tenant.usage.team_member_count += amount
            elif resource_type == "workspace":
                tenant.usage.workspace_count += amount
            elif resource_type == "api_key":
                tenant.usage.api_key_count += amount
            elif resource_type == "storage":
                tenant.usage.storage_mb += amount
            elif resource_type == "execution":
                tenant.usage.executions_this_hour += amount

    async def decrement_usage(
        self,
        tenant_id: UUID,
        resource_type: str,
        amount: int = 1,
    ) -> None:
        """Decrement resource usage counter."""
        tenant = await self.get_tenant(tenant_id)

        async with self._lock:
            if resource_type == "workflow":
                tenant.usage.workflow_count = max(
                    0, tenant.usage.workflow_count - amount
                )
            elif resource_type == "robot":
                tenant.usage.robot_count = max(0, tenant.usage.robot_count - amount)
            elif resource_type == "team_member":
                tenant.usage.team_member_count = max(
                    0, tenant.usage.team_member_count - amount
                )
            elif resource_type == "workspace":
                tenant.usage.workspace_count = max(
                    0, tenant.usage.workspace_count - amount
                )
            elif resource_type == "api_key":
                tenant.usage.api_key_count = max(0, tenant.usage.api_key_count - amount)
            elif resource_type == "storage":
                tenant.usage.storage_mb = max(0, tenant.usage.storage_mb - amount)

    async def configure_sso(
        self,
        tenant_id: UUID,
        config: SSOConfig,
    ) -> Tenant:
        """
        Configure SSO for a tenant.

        Args:
            tenant_id: Tenant ID
            config: SSO configuration

        Returns:
            Updated Tenant

        Raises:
            TenancyError: If configuration is invalid
        """
        errors = config.validate_config()
        if errors:
            raise TenancyError(f"Invalid SSO configuration: {', '.join(errors)}")

        tenant = await self.get_tenant(tenant_id)

        async with self._lock:
            tenant.sso_enabled = config.enabled
            tenant.sso_config = config
            tenant.updated_at = datetime.now(timezone.utc)

            logger.info(
                f"Configured {config.provider.value} SSO for tenant {tenant_id}"
            )
            return tenant

    async def update_subscription(
        self,
        tenant_id: UUID,
        tier: SubscriptionTier,
        expires_at: Optional[datetime] = None,
    ) -> Tenant:
        """
        Update tenant subscription.

        Args:
            tenant_id: Tenant ID
            tier: New subscription tier
            expires_at: Subscription expiration

        Returns:
            Updated Tenant
        """
        tenant = await self.get_tenant(tenant_id)

        async with self._lock:
            tenant.subscription_tier = tier
            tenant.subscription_expires_at = expires_at
            tenant.quotas = ResourceQuotas.for_tier(tier)
            tenant.updated_at = datetime.now(timezone.utc)

            logger.info(
                f"Updated subscription for tenant {tenant_id}: tier={tier.value}"
            )
            return tenant


# =============================================================================
# API KEY SERVICE
# =============================================================================


class APIKeyService:
    """Service for API key management."""

    def __init__(self, tenant_service: TenantService) -> None:
        self._tenant_service = tenant_service
        self._keys: Dict[UUID, APIKey] = {}
        self._keys_by_prefix: Dict[str, UUID] = {}
        self._lock = asyncio.Lock()

    async def create_key(
        self,
        tenant_id: UUID,
        name: str,
        user_id: Optional[UUID] = None,
        role_id: Optional[UUID] = None,
        scopes: Optional[List[str]] = None,
        expires_in_days: Optional[int] = None,
        **kwargs: Any,
    ) -> tuple[APIKey, str]:
        """
        Create a new API key.

        Args:
            tenant_id: Tenant ID
            name: Key name
            user_id: Creating user ID
            role_id: Role to assign to key
            scopes: Permission scopes
            expires_in_days: Days until expiration
            **kwargs: Additional key properties

        Returns:
            Tuple of (APIKey, raw key string)

        Raises:
            QuotaExceededError: If tenant exceeds API key quota
        """
        await self._tenant_service.check_and_enforce_quota(tenant_id, "api_key")

        expires_at = None
        if expires_in_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

        api_key, raw_key = APIKey.generate(
            tenant_id=tenant_id,
            name=name,
            user_id=user_id,
            role_id=role_id,
            scopes=scopes or [],
            expires_at=expires_at,
            **kwargs,
        )

        async with self._lock:
            self._keys[api_key.id] = api_key
            self._keys_by_prefix[api_key.key_prefix] = api_key.id

        await self._tenant_service.increment_usage(tenant_id, "api_key")

        logger.info(f"Created API key '{name}' for tenant {tenant_id}")
        return api_key, raw_key

    async def validate_key(self, raw_key: str) -> APIKey:
        """
        Validate an API key.

        Args:
            raw_key: Raw API key string

        Returns:
            APIKey if valid

        Raises:
            InvalidAPIKeyError: If key is invalid
        """
        if not raw_key or len(raw_key) < 12:
            raise InvalidAPIKeyError("Invalid API key format")

        prefix = raw_key[:12]
        key_id = self._keys_by_prefix.get(prefix)
        if not key_id:
            raise InvalidAPIKeyError("API key not found")

        api_key = self._keys.get(key_id)
        if not api_key:
            raise InvalidAPIKeyError("API key not found")

        if not api_key.verify(raw_key):
            raise InvalidAPIKeyError("Invalid API key")

        if not api_key.is_valid:
            if api_key.status == APIKeyStatus.REVOKED:
                raise InvalidAPIKeyError("API key has been revoked")
            if api_key.status == APIKeyStatus.EXPIRED:
                raise InvalidAPIKeyError("API key has expired")
            raise InvalidAPIKeyError("API key is not active")

        async with self._lock:
            api_key.last_used_at = datetime.now(timezone.utc)
            api_key.use_count += 1

        return api_key

    async def revoke_key(
        self,
        key_id: UUID,
        revoked_by: Optional[UUID] = None,
    ) -> APIKey:
        """
        Revoke an API key.

        Args:
            key_id: API key ID
            revoked_by: User who revoked the key

        Returns:
            Revoked APIKey
        """
        api_key = self._keys.get(key_id)
        if not api_key:
            raise TenancyError(f"API key not found: {key_id}")

        async with self._lock:
            api_key.status = APIKeyStatus.REVOKED
            api_key.revoked_at = datetime.now(timezone.utc)
            api_key.revoked_by = revoked_by

        await self._tenant_service.decrement_usage(api_key.tenant_id, "api_key")

        logger.info(f"Revoked API key {key_id}")
        return api_key

    async def list_keys(self, tenant_id: UUID) -> List[APIKey]:
        """List all API keys for a tenant."""
        return [k for k in self._keys.values() if k.tenant_id == tenant_id]

    async def get_key(self, key_id: UUID) -> Optional[APIKey]:
        """Get API key by ID."""
        return self._keys.get(key_id)


# =============================================================================
# AUDIT SERVICE
# =============================================================================


class AuditService:
    """
    Service for audit logging.

    Supports optional Merkle tree integration for tamper-proof compliance logging.
    When merkle_enabled=True, all audit entries are also written to the
    hash-chained Merkle audit log for cryptographic verification.
    """

    def __init__(
        self,
        context_manager: TenantContextManager,
        merkle_enabled: bool = False,
    ) -> None:
        self._context_manager = context_manager
        self._logs: List[AuditLogEntry] = []
        self._max_buffer = 10000
        self._lock = asyncio.Lock()
        self._merkle_enabled = merkle_enabled
        self._merkle_service: Optional[MerkleAuditService] = None

        if merkle_enabled:
            self._merkle_service = get_merkle_audit_service()

    async def log(
        self,
        tenant_id: UUID,
        action: AuditAction,
        resource_type: str,
        resource_id: Optional[str] = None,
        user_id: Optional[UUID] = None,
        api_key_id: Optional[UUID] = None,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        actor_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLogEntry:
        """
        Create an audit log entry.

        Args:
            tenant_id: Tenant ID
            action: Action performed
            resource_type: Type of resource affected
            resource_id: ID of affected resource
            user_id: User who performed action
            api_key_id: API key used (if any)
            old_value: Previous value (for updates)
            new_value: New value (for creates/updates)
            metadata: Additional metadata
            success: Whether action succeeded
            error_message: Error message if failed
            actor_ip: Client IP address
            user_agent: Client user agent

        Returns:
            Created AuditLogEntry
        """
        actor_type = "user"
        if api_key_id:
            actor_type = "api_key"
        elif not user_id:
            actor_type = "system"

        entry = AuditLogEntry(
            tenant_id=tenant_id,
            user_id=user_id,
            api_key_id=api_key_id,
            actor_type=actor_type,
            actor_ip=actor_ip,
            user_agent=user_agent,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_value=old_value,
            new_value=new_value,
            metadata=metadata or {},
            success=success,
            error_message=error_message,
        )

        async with self._lock:
            self._logs.append(entry)
            if len(self._logs) > self._max_buffer:
                self._logs = self._logs[-self._max_buffer :]

        log_level = "info" if success else "warning"
        getattr(logger, log_level)(
            f"AUDIT: {action.value} on {resource_type}"
            f"{f'/{resource_id}' if resource_id else ''} "
            f"by {actor_type} in tenant {tenant_id}"
        )

        # Write to Merkle audit log for tamper-proof compliance
        if self._merkle_enabled and self._merkle_service:
            try:
                await self._append_to_merkle_log(entry)
            except Exception as e:
                logger.error(f"Failed to write to Merkle audit log: {e}")

        return entry

    async def _append_to_merkle_log(self, entry: AuditLogEntry) -> None:
        """Append entry to Merkle hash-chained audit log."""
        if not self._merkle_service:
            return

        # Map tenancy action to Merkle audit action
        merkle_action = self._map_to_merkle_action(entry.action)

        # Create Merkle audit entry
        merkle_entry = MerkleAuditEntry(
            action=merkle_action,
            actor_id=entry.user_id or entry.api_key_id or UUID(int=0),
            actor_type=entry.actor_type,
            resource_type=entry.resource_type,
            resource_id=UUID(entry.resource_id) if entry.resource_id else None,
            tenant_id=entry.tenant_id,
            details={
                "old_value": entry.old_value,
                "new_value": entry.new_value,
                "success": entry.success,
                "error_message": entry.error_message,
                **(entry.metadata or {}),
            },
            ip_address=entry.actor_ip,
            user_agent=entry.user_agent,
        )

        await self._merkle_service.append_entry(merkle_entry)

    def _map_to_merkle_action(self, action: AuditAction) -> MerkleAuditAction:
        """Map tenancy AuditAction to Merkle AuditAction."""
        # Map based on action prefix
        action_str = action.value

        if action_str.startswith("user.login"):
            return MerkleAuditAction.USER_LOGIN
        elif action_str.startswith("user.logout"):
            return MerkleAuditAction.USER_LOGOUT
        elif "created" in action_str:
            return MerkleAuditAction.CREATE
        elif "updated" in action_str or "changed" in action_str:
            return MerkleAuditAction.UPDATE
        elif "deleted" in action_str or "removed" in action_str:
            return MerkleAuditAction.DELETE
        elif "executed" in action_str:
            return MerkleAuditAction.EXECUTE
        elif "accessed" in action_str:
            return MerkleAuditAction.ACCESS
        elif "configured" in action_str:
            return MerkleAuditAction.CONFIGURE
        elif "suspended" in action_str or "revoked" in action_str:
            return MerkleAuditAction.REVOKE
        elif "activated" in action_str or "published" in action_str:
            return MerkleAuditAction.APPROVE
        else:
            # Default fallback
            return MerkleAuditAction.ACCESS

    async def query(
        self,
        tenant_id: UUID,
        action: Optional[AuditAction] = None,
        resource_type: Optional[str] = None,
        user_id: Optional[UUID] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditLogEntry]:
        """
        Query audit logs.

        Args:
            tenant_id: Tenant ID
            action: Filter by action
            resource_type: Filter by resource type
            user_id: Filter by user
            since: Filter by start time
            until: Filter by end time
            limit: Max results
            offset: Result offset

        Returns:
            List of matching AuditLogEntry
        """
        results: List[AuditLogEntry] = []

        for entry in reversed(self._logs):
            if entry.tenant_id != tenant_id:
                continue
            if action and entry.action != action:
                continue
            if resource_type and entry.resource_type != resource_type:
                continue
            if user_id and entry.user_id != user_id:
                continue
            if since and entry.timestamp < since:
                continue
            if until and entry.timestamp > until:
                continue

            results.append(entry)

        return results[offset : offset + limit]

    async def flush(self) -> int:
        """
        Flush audit log buffer.

        Returns:
            Number of entries flushed
        """
        async with self._lock:
            count = len(self._logs)
            self._logs.clear()
            return count


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================


def create_tenant_context_manager() -> TenantContextManager:
    """Create a new tenant context manager."""
    return TenantContextManager()


def create_tenant_service(
    context_manager: Optional[TenantContextManager] = None,
) -> TenantService:
    """
    Create a new tenant service.

    Args:
        context_manager: Optional existing context manager

    Returns:
        Configured TenantService
    """
    ctx_manager = context_manager or create_tenant_context_manager()
    return TenantService(ctx_manager)


def create_api_key_service(tenant_service: TenantService) -> APIKeyService:
    """Create API key service."""
    return APIKeyService(tenant_service)


def create_audit_service(
    context_manager: Optional[TenantContextManager] = None,
    merkle_enabled: bool = False,
) -> AuditService:
    """
    Create audit service.

    Args:
        context_manager: Optional tenant context manager
        merkle_enabled: Enable Merkle tree hash-chained logging for compliance

    Returns:
        Configured AuditService
    """
    ctx_manager = context_manager or create_tenant_context_manager()
    return AuditService(ctx_manager, merkle_enabled=merkle_enabled)
