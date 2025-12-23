"""
CasareRPA - Role-Based Access Control (RBAC) Module.

Provides comprehensive RBAC implementation for enterprise deployments:
- Permission-based authorization
- System and custom role management
- Hierarchical role inheritance
- Conditional permissions with JSONB rules
- Audit logging integration
"""

import asyncio
import secrets
from collections.abc import Callable
from datetime import UTC, datetime
from enum import Enum
from typing import Any, TypeVar
from uuid import UUID

from loguru import logger
from pydantic import BaseModel, Field

# =============================================================================
# ENUMS
# =============================================================================


class SystemRole(str, Enum):
    """Built-in system roles with predefined permissions."""

    ADMIN = "admin"
    DEVELOPER = "developer"
    OPERATOR = "operator"
    VIEWER = "viewer"


class ResourceType(str, Enum):
    """Resource types that can be protected by RBAC."""

    WORKFLOW = "workflow"
    EXECUTION = "execution"
    ROBOT = "robot"
    USER = "user"
    WORKSPACE = "workspace"
    CREDENTIAL = "credential"
    API_KEY = "apikey"
    AUDIT = "audit"
    TENANT = "tenant"
    ROLE = "role"


class ActionType(str, Enum):
    """Action types that can be performed on resources."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    PUBLISH = "publish"
    CANCEL = "cancel"
    RETRY = "retry"
    INVITE = "invite"
    REMOVE = "remove"
    USE = "use"
    REVOKE = "revoke"
    EXPORT = "export"
    SETTINGS = "settings"
    BILLING = "billing"
    MANAGE = "manage"


# =============================================================================
# EXCEPTIONS
# =============================================================================


class RBACError(Exception):
    """Base exception for RBAC operations."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(message)


class PermissionDeniedError(RBACError):
    """Raised when a user lacks required permission."""

    def __init__(
        self,
        user_id: UUID,
        resource: ResourceType,
        action: ActionType,
        resource_id: str | None = None,
    ) -> None:
        message = f"Permission denied: {action.value} on {resource.value}"
        if resource_id:
            message += f" (id: {resource_id})"
        super().__init__(
            message,
            {
                "user_id": str(user_id),
                "resource": resource.value,
                "action": action.value,
                "resource_id": resource_id,
            },
        )
        self.user_id = user_id
        self.resource = resource
        self.action = action
        self.resource_id = resource_id


class RoleNotFoundError(RBACError):
    """Raised when a role does not exist."""

    def __init__(self, role_id: UUID) -> None:
        super().__init__(f"Role not found: {role_id}", {"role_id": str(role_id)})
        self.role_id = role_id


class InvalidRoleConfigError(RBACError):
    """Raised when role configuration is invalid."""

    pass


# =============================================================================
# DATA MODELS
# =============================================================================


class Permission(BaseModel):
    """Represents a single permission."""

    id: UUID
    name: str
    display_name: str
    description: str | None = None
    resource: ResourceType
    action: ActionType
    category: str = "general"

    @property
    def permission_key(self) -> str:
        """Get the canonical permission key (resource.action)."""
        return f"{self.resource.value}.{self.action.value}"

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Permission):
            return self.id == other.id
        return False


class PermissionCondition(BaseModel):
    """Conditional permission with JSONB rules."""

    field: str = Field(..., description="Field to check (e.g., 'workspace_id')")
    operator: str = Field(..., description="Comparison operator (eq, in, gt, lt, etc.)")
    value: Any = Field(..., description="Value to compare against")

    def evaluate(self, context: dict[str, Any]) -> bool:
        """
        Evaluate condition against context.

        Args:
            context: Dictionary with context values to check

        Returns:
            True if condition is satisfied
        """
        actual_value = context.get(self.field)

        if self.operator == "eq":
            return actual_value == self.value
        elif self.operator == "neq":
            return actual_value != self.value
        elif self.operator == "in":
            return actual_value in self.value
        elif self.operator == "not_in":
            return actual_value not in self.value
        elif self.operator == "gt":
            return actual_value is not None and actual_value > self.value
        elif self.operator == "gte":
            return actual_value is not None and actual_value >= self.value
        elif self.operator == "lt":
            return actual_value is not None and actual_value < self.value
        elif self.operator == "lte":
            return actual_value is not None and actual_value <= self.value
        elif self.operator == "contains":
            return self.value in (actual_value or "")
        elif self.operator == "starts_with":
            return (actual_value or "").startswith(self.value)
        elif self.operator == "is_null":
            return actual_value is None
        elif self.operator == "is_not_null":
            return actual_value is not None
        else:
            logger.warning(f"Unknown condition operator: {self.operator}")
            return False


class RolePermission(BaseModel):
    """Permission assigned to a role with optional conditions."""

    permission: Permission
    conditions: list[PermissionCondition] | None = None

    def is_granted(self, context: dict[str, Any] | None = None) -> bool:
        """
        Check if permission is granted given context.

        Args:
            context: Optional context for conditional evaluation

        Returns:
            True if permission is granted
        """
        if not self.conditions:
            return True

        if context is None:
            return False

        return all(cond.evaluate(context) for cond in self.conditions)


class Role(BaseModel):
    """Represents a role with assigned permissions."""

    id: UUID
    tenant_id: UUID | None = None
    name: str
    display_name: str
    description: str | None = None
    is_system: bool = False
    is_default: bool = False
    priority: int = 0
    permissions: list[RolePermission] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def has_permission(
        self,
        resource: ResourceType,
        action: ActionType,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """
        Check if role has a specific permission.

        Args:
            resource: Resource type to check
            action: Action to check
            context: Optional context for conditional permissions

        Returns:
            True if role has the permission
        """
        for role_perm in self.permissions:
            if role_perm.permission.resource == resource and role_perm.permission.action == action:
                if role_perm.is_granted(context):
                    return True
        return False

    def get_permission_keys(self) -> set[str]:
        """Get all permission keys for this role."""
        return {rp.permission.permission_key for rp in self.permissions}

    def __hash__(self) -> int:
        return hash(self.id)


class UserPermissions(BaseModel):
    """Aggregated permissions for a user within a tenant."""

    user_id: UUID
    tenant_id: UUID
    roles: list[Role] = Field(default_factory=list)
    effective_permissions: set[str] = Field(default_factory=set)
    cached_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    cache_ttl_seconds: int = 300

    @property
    def is_cache_valid(self) -> bool:
        """Check if permission cache is still valid."""
        age = (datetime.now(UTC) - self.cached_at).total_seconds()
        return age < self.cache_ttl_seconds

    @property
    def highest_priority_role(self) -> Role | None:
        """Get the role with highest priority."""
        if not self.roles:
            return None
        return max(self.roles, key=lambda r: r.priority)

    def has_permission(
        self,
        resource: ResourceType,
        action: ActionType,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """
        Check if user has a specific permission.

        Args:
            resource: Resource type to check
            action: Action to check
            context: Optional context for conditional permissions

        Returns:
            True if any of the user's roles grant the permission
        """
        for role in self.roles:
            if role.has_permission(resource, action, context):
                return True
        return False

    def has_any_permission(
        self,
        permissions: list[tuple[ResourceType, ActionType]],
        context: dict[str, Any] | None = None,
    ) -> bool:
        """Check if user has any of the specified permissions."""
        return any(
            self.has_permission(resource, action, context) for resource, action in permissions
        )

    def has_all_permissions(
        self,
        permissions: list[tuple[ResourceType, ActionType]],
        context: dict[str, Any] | None = None,
    ) -> bool:
        """Check if user has all specified permissions."""
        return all(
            self.has_permission(resource, action, context) for resource, action in permissions
        )


# =============================================================================
# PERMISSION REGISTRY
# =============================================================================


class PermissionRegistry:
    """
    Registry of all available permissions.

    Provides fast lookup and validation for permission operations.
    """

    def __init__(self) -> None:
        self._permissions: dict[str, Permission] = {}
        self._by_resource: dict[ResourceType, list[Permission]] = {}
        self._by_category: dict[str, list[Permission]] = {}
        self._lock = asyncio.Lock()

    async def register(self, permission: Permission) -> None:
        """Register a permission."""
        async with self._lock:
            key = permission.permission_key
            self._permissions[key] = permission

            if permission.resource not in self._by_resource:
                self._by_resource[permission.resource] = []
            self._by_resource[permission.resource].append(permission)

            if permission.category not in self._by_category:
                self._by_category[permission.category] = []
            self._by_category[permission.category].append(permission)

    async def register_many(self, permissions: list[Permission]) -> None:
        """Register multiple permissions."""
        for perm in permissions:
            await self.register(perm)

    def get(self, resource: ResourceType, action: ActionType) -> Permission | None:
        """Get permission by resource and action."""
        key = f"{resource.value}.{action.value}"
        return self._permissions.get(key)

    def get_by_key(self, key: str) -> Permission | None:
        """Get permission by canonical key."""
        return self._permissions.get(key)

    def get_by_resource(self, resource: ResourceType) -> list[Permission]:
        """Get all permissions for a resource type."""
        return self._by_resource.get(resource, [])

    def get_by_category(self, category: str) -> list[Permission]:
        """Get all permissions in a category."""
        return self._by_category.get(category, [])

    def get_all(self) -> list[Permission]:
        """Get all registered permissions."""
        return list(self._permissions.values())

    def exists(self, resource: ResourceType, action: ActionType) -> bool:
        """Check if a permission exists."""
        key = f"{resource.value}.{action.value}"
        return key in self._permissions


# =============================================================================
# ROLE MANAGER
# =============================================================================


class RoleManager:
    """
    Manages role definitions and assignments.

    Handles system roles, custom roles, and role hierarchies.
    """

    def __init__(self, permission_registry: PermissionRegistry) -> None:
        self._permission_registry = permission_registry
        self._system_roles: dict[UUID, Role] = {}
        self._custom_roles: dict[UUID, dict[UUID, Role]] = {}  # tenant_id -> role_id -> role
        self._lock = asyncio.Lock()

    async def load_system_roles(self, roles: list[Role]) -> None:
        """Load system roles into memory."""
        async with self._lock:
            for role in roles:
                if role.is_system:
                    self._system_roles[role.id] = role
                    logger.debug(f"Loaded system role: {role.name}")

    async def load_tenant_roles(self, tenant_id: UUID, roles: list[Role]) -> None:
        """Load custom roles for a tenant."""
        async with self._lock:
            if tenant_id not in self._custom_roles:
                self._custom_roles[tenant_id] = {}
            for role in roles:
                self._custom_roles[tenant_id][role.id] = role
                logger.debug(f"Loaded tenant role: {role.name} for tenant {tenant_id}")

    def get_system_role(self, role_id: UUID) -> Role | None:
        """Get a system role by ID."""
        return self._system_roles.get(role_id)

    def get_system_role_by_name(self, name: str) -> Role | None:
        """Get a system role by name."""
        for role in self._system_roles.values():
            if role.name == name:
                return role
        return None

    def get_tenant_role(self, tenant_id: UUID, role_id: UUID) -> Role | None:
        """Get a custom role for a tenant."""
        tenant_roles = self._custom_roles.get(tenant_id, {})
        return tenant_roles.get(role_id)

    def get_role(self, role_id: UUID, tenant_id: UUID | None = None) -> Role | None:
        """Get a role by ID, checking both system and tenant roles."""
        if role_id in self._system_roles:
            return self._system_roles[role_id]

        if tenant_id:
            return self.get_tenant_role(tenant_id, role_id)

        for tenant_roles in self._custom_roles.values():
            if role_id in tenant_roles:
                return tenant_roles[role_id]

        return None

    def get_all_system_roles(self) -> list[Role]:
        """Get all system roles."""
        return list(self._system_roles.values())

    def get_tenant_roles(self, tenant_id: UUID) -> list[Role]:
        """Get all custom roles for a tenant."""
        return list(self._custom_roles.get(tenant_id, {}).values())

    def get_available_roles(self, tenant_id: UUID) -> list[Role]:
        """Get all roles available to a tenant (system + custom)."""
        roles = list(self._system_roles.values())
        roles.extend(self.get_tenant_roles(tenant_id))
        return sorted(roles, key=lambda r: r.priority, reverse=True)

    async def create_custom_role(
        self,
        tenant_id: UUID,
        name: str,
        display_name: str,
        description: str | None = None,
        permission_keys: list[str] | None = None,
        priority: int = 0,
    ) -> Role:
        """
        Create a custom role for a tenant.

        Args:
            tenant_id: Tenant ID
            name: Role name (unique within tenant)
            display_name: Human-readable name
            description: Role description
            permission_keys: List of permission keys to assign
            priority: Role priority (higher = more permissions)

        Returns:
            Created Role
        """
        async with self._lock:
            if tenant_id not in self._custom_roles:
                self._custom_roles[tenant_id] = {}

            for existing in self._custom_roles[tenant_id].values():
                if existing.name == name:
                    raise InvalidRoleConfigError(
                        f"Role with name '{name}' already exists in tenant"
                    )

            role_id = UUID(int=int.from_bytes(secrets.token_bytes(16), "big"))
            permissions: list[RolePermission] = []

            if permission_keys:
                for key in permission_keys:
                    perm = self._permission_registry.get_by_key(key)
                    if perm:
                        permissions.append(RolePermission(permission=perm))
                    else:
                        logger.warning(f"Unknown permission key: {key}")

            role = Role(
                id=role_id,
                tenant_id=tenant_id,
                name=name,
                display_name=display_name,
                description=description,
                is_system=False,
                is_default=False,
                priority=priority,
                permissions=permissions,
            )

            self._custom_roles[tenant_id][role_id] = role
            logger.info(f"Created custom role: {name} for tenant {tenant_id}")

            return role

    async def update_role_permissions(
        self,
        role_id: UUID,
        tenant_id: UUID,
        permission_keys: list[str],
    ) -> Role:
        """
        Update permissions for a custom role.

        Args:
            role_id: Role ID
            tenant_id: Tenant ID
            permission_keys: New list of permission keys

        Returns:
            Updated Role
        """
        async with self._lock:
            role = self.get_tenant_role(tenant_id, role_id)
            if not role:
                raise RoleNotFoundError(role_id)

            if role.is_system:
                raise InvalidRoleConfigError("Cannot modify system role permissions")

            permissions: list[RolePermission] = []
            for key in permission_keys:
                perm = self._permission_registry.get_by_key(key)
                if perm:
                    permissions.append(RolePermission(permission=perm))

            role.permissions = permissions
            role.updated_at = datetime.now(UTC)

            logger.info(f"Updated permissions for role {role.name}: {len(permissions)} permissions")
            return role

    async def delete_custom_role(self, role_id: UUID, tenant_id: UUID) -> bool:
        """
        Delete a custom role.

        Args:
            role_id: Role ID
            tenant_id: Tenant ID

        Returns:
            True if deleted
        """
        async with self._lock:
            tenant_roles = self._custom_roles.get(tenant_id)
            if not tenant_roles or role_id not in tenant_roles:
                return False

            role = tenant_roles[role_id]
            if role.is_system:
                raise InvalidRoleConfigError("Cannot delete system role")

            del tenant_roles[role_id]
            logger.info(f"Deleted custom role: {role.name} from tenant {tenant_id}")
            return True


# =============================================================================
# AUTHORIZATION SERVICE
# =============================================================================


class AuthorizationService:
    """
    Main service for authorization decisions.

    Provides high-level API for checking permissions and managing user access.
    """

    def __init__(
        self,
        role_manager: RoleManager,
        permission_registry: PermissionRegistry,
    ) -> None:
        self._role_manager = role_manager
        self._permission_registry = permission_registry
        self._user_cache: dict[tuple[UUID, UUID], UserPermissions] = {}
        self._cache_ttl = 300
        self._lock = asyncio.Lock()

    async def get_user_permissions(
        self,
        user_id: UUID,
        tenant_id: UUID,
        role_ids: list[UUID],
        force_refresh: bool = False,
    ) -> UserPermissions:
        """
        Get aggregated permissions for a user in a tenant.

        Args:
            user_id: User ID
            tenant_id: Tenant ID
            role_ids: List of role IDs assigned to user
            force_refresh: Bypass cache

        Returns:
            UserPermissions with all granted permissions
        """
        cache_key = (user_id, tenant_id)

        if not force_refresh:
            cached = self._user_cache.get(cache_key)
            if cached and cached.is_cache_valid:
                return cached

        roles: list[Role] = []
        effective_permissions: set[str] = set()

        for role_id in role_ids:
            role = self._role_manager.get_role(role_id, tenant_id)
            if role:
                roles.append(role)
                effective_permissions.update(role.get_permission_keys())

        user_perms = UserPermissions(
            user_id=user_id,
            tenant_id=tenant_id,
            roles=roles,
            effective_permissions=effective_permissions,
            cache_ttl_seconds=self._cache_ttl,
        )

        async with self._lock:
            self._user_cache[cache_key] = user_perms

        return user_perms

    async def check_permission(
        self,
        user_id: UUID,
        tenant_id: UUID,
        role_ids: list[UUID],
        resource: ResourceType,
        action: ActionType,
        context: dict[str, Any] | None = None,
        raise_on_deny: bool = True,
    ) -> bool:
        """
        Check if user has permission for an action.

        Args:
            user_id: User ID
            tenant_id: Tenant ID
            role_ids: User's role IDs
            resource: Resource type
            action: Action to perform
            context: Optional context for conditional permissions
            raise_on_deny: If True, raises PermissionDeniedError on denial

        Returns:
            True if permitted

        Raises:
            PermissionDeniedError: If permission denied and raise_on_deny=True
        """
        user_perms = await self.get_user_permissions(user_id, tenant_id, role_ids)
        granted = user_perms.has_permission(resource, action, context)

        if not granted:
            logger.warning(
                f"Permission denied: user={user_id} action={action.value} "
                f"resource={resource.value} tenant={tenant_id}"
            )
            if raise_on_deny:
                resource_id = context.get("resource_id") if context else None
                raise PermissionDeniedError(user_id, resource, action, resource_id)

        return granted

    async def check_any_permission(
        self,
        user_id: UUID,
        tenant_id: UUID,
        role_ids: list[UUID],
        permissions: list[tuple[ResourceType, ActionType]],
        context: dict[str, Any] | None = None,
    ) -> bool:
        """Check if user has any of the specified permissions."""
        user_perms = await self.get_user_permissions(user_id, tenant_id, role_ids)
        return user_perms.has_any_permission(permissions, context)

    async def check_all_permissions(
        self,
        user_id: UUID,
        tenant_id: UUID,
        role_ids: list[UUID],
        permissions: list[tuple[ResourceType, ActionType]],
        context: dict[str, Any] | None = None,
    ) -> bool:
        """Check if user has all specified permissions."""
        user_perms = await self.get_user_permissions(user_id, tenant_id, role_ids)
        return user_perms.has_all_permissions(permissions, context)

    async def invalidate_user_cache(
        self,
        user_id: UUID | None = None,
        tenant_id: UUID | None = None,
    ) -> int:
        """
        Invalidate permission cache.

        Args:
            user_id: Specific user to invalidate (None = all users)
            tenant_id: Specific tenant to invalidate (None = all tenants)

        Returns:
            Number of cache entries invalidated
        """
        async with self._lock:
            if user_id is None and tenant_id is None:
                count = len(self._user_cache)
                self._user_cache.clear()
                return count

            keys_to_remove: list[tuple[UUID, UUID]] = []
            for key in self._user_cache:
                cache_user_id, cache_tenant_id = key
                if user_id is not None and cache_user_id != user_id:
                    continue
                if tenant_id is not None and cache_tenant_id != tenant_id:
                    continue
                keys_to_remove.append(key)

            for key in keys_to_remove:
                del self._user_cache[key]

            return len(keys_to_remove)

    def get_available_permissions(
        self,
        resource: ResourceType | None = None,
        category: str | None = None,
    ) -> list[Permission]:
        """
        Get available permissions with optional filtering.

        Args:
            resource: Filter by resource type
            category: Filter by category

        Returns:
            List of matching permissions
        """
        if resource:
            return self._permission_registry.get_by_resource(resource)
        if category:
            return self._permission_registry.get_by_category(category)
        return self._permission_registry.get_all()


# =============================================================================
# DECORATORS
# =============================================================================

T = TypeVar("T")


def require_permission(
    resource: ResourceType,
    action: ActionType,
    get_context: Callable[..., dict[str, Any]] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to require permission for a function.

    Usage:
        @require_permission(ResourceType.WORKFLOW, ActionType.EXECUTE)
        async def execute_workflow(self, workflow_id: str, auth_context: AuthContext):
            ...

    Args:
        resource: Required resource type
        action: Required action
        get_context: Optional function to extract context from args
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            auth_context = kwargs.get("auth_context")
            if not auth_context:
                for arg in args:
                    if hasattr(arg, "auth_context"):
                        auth_context = arg.auth_context
                        break

            if not auth_context:
                raise RBACError("No authentication context provided")

            permission_context: dict[str, Any] | None = None
            if get_context:
                permission_context = get_context(*args, **kwargs)

            auth_service: AuthorizationService = auth_context.auth_service
            await auth_service.check_permission(
                user_id=auth_context.user_id,
                tenant_id=auth_context.tenant_id,
                role_ids=auth_context.role_ids,
                resource=resource,
                action=action,
                context=permission_context,
                raise_on_deny=True,
            )

            return await func(*args, **kwargs)

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper

    return decorator


# =============================================================================
# MFA-REQUIRED OPERATIONS
# =============================================================================


# Operations that require MFA verification
MFA_REQUIRED_OPERATIONS: list[tuple[ResourceType, ActionType]] = [
    # Credential management
    (ResourceType.CREDENTIAL, ActionType.CREATE),
    (ResourceType.CREDENTIAL, ActionType.UPDATE),
    (ResourceType.CREDENTIAL, ActionType.DELETE),
    # User management
    (ResourceType.USER, ActionType.INVITE),
    (ResourceType.USER, ActionType.UPDATE),
    (ResourceType.USER, ActionType.REMOVE),
    # System configuration
    (ResourceType.TENANT, ActionType.SETTINGS),
    (ResourceType.TENANT, ActionType.BILLING),
    # Role management
    (ResourceType.ROLE, ActionType.MANAGE),
    # Workflow deletion
    (ResourceType.WORKFLOW, ActionType.DELETE),
    # API Key management
    (ResourceType.API_KEY, ActionType.CREATE),
    (ResourceType.API_KEY, ActionType.REVOKE),
]


class MFARequiredError(RBACError):
    """Raised when MFA verification is required but not provided."""

    def __init__(
        self,
        resource: ResourceType,
        action: ActionType,
    ) -> None:
        message = f"MFA verification required for {action.value} on {resource.value}"
        super().__init__(
            message,
            {
                "resource": resource.value,
                "action": action.value,
                "mfa_required": True,
            },
        )
        self.resource = resource
        self.action = action


def is_mfa_required(resource: ResourceType, action: ActionType) -> bool:
    """
    Check if an operation requires MFA verification.

    Args:
        resource: Resource type
        action: Action type

    Returns:
        True if MFA is required for this operation
    """
    return (resource, action) in MFA_REQUIRED_OPERATIONS


def require_mfa(
    resource: ResourceType,
    action: ActionType,
    get_context: Callable[..., dict[str, Any]] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to require both permission and MFA verification.

    Usage:
        @require_mfa(ResourceType.CREDENTIAL, ActionType.DELETE)
        async def delete_credential(self, credential_id: str, auth_context: AuthContext):
            ...

    Args:
        resource: Required resource type
        action: Required action
        get_context: Optional function to extract context from args
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            auth_context = kwargs.get("auth_context")
            if not auth_context:
                for arg in args:
                    if hasattr(arg, "auth_context"):
                        auth_context = arg.auth_context
                        break

            if not auth_context:
                raise RBACError("No authentication context provided")

            # Check MFA status
            if not getattr(auth_context, "mfa_verified", False):
                raise MFARequiredError(resource, action)

            permission_context: dict[str, Any] | None = None
            if get_context:
                permission_context = get_context(*args, **kwargs)

            # Check permission
            auth_service: AuthorizationService = auth_context.auth_service
            await auth_service.check_permission(
                user_id=auth_context.user_id,
                tenant_id=auth_context.tenant_id,
                role_ids=auth_context.role_ids,
                resource=resource,
                action=action,
                context=permission_context,
                raise_on_deny=True,
            )

            return await func(*args, **kwargs)

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper

    return decorator


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================


def create_permission_registry() -> PermissionRegistry:
    """Create a new permission registry with default permissions."""
    return PermissionRegistry()


async def create_authorization_service(
    permission_registry: PermissionRegistry | None = None,
) -> AuthorizationService:
    """
    Create authorization service with default configuration.

    Args:
        permission_registry: Optional existing registry

    Returns:
        Configured AuthorizationService
    """
    registry = permission_registry or create_permission_registry()
    role_manager = RoleManager(registry)
    return AuthorizationService(role_manager, registry)


def get_default_permissions() -> list[Permission]:
    """
    Get the default set of permissions matching the database schema.

    Returns:
        List of default Permission objects
    """
    from uuid import uuid4

    permissions = [
        # Workflow permissions
        Permission(
            id=uuid4(),
            name="workflow.create",
            display_name="Create Workflows",
            description="Create new workflows",
            resource=ResourceType.WORKFLOW,
            action=ActionType.CREATE,
            category="workflows",
        ),
        Permission(
            id=uuid4(),
            name="workflow.read",
            display_name="View Workflows",
            description="View workflow definitions",
            resource=ResourceType.WORKFLOW,
            action=ActionType.READ,
            category="workflows",
        ),
        Permission(
            id=uuid4(),
            name="workflow.update",
            display_name="Edit Workflows",
            description="Modify workflow definitions",
            resource=ResourceType.WORKFLOW,
            action=ActionType.UPDATE,
            category="workflows",
        ),
        Permission(
            id=uuid4(),
            name="workflow.delete",
            display_name="Delete Workflows",
            description="Delete workflows",
            resource=ResourceType.WORKFLOW,
            action=ActionType.DELETE,
            category="workflows",
        ),
        Permission(
            id=uuid4(),
            name="workflow.execute",
            display_name="Execute Workflows",
            description="Run workflow executions",
            resource=ResourceType.WORKFLOW,
            action=ActionType.EXECUTE,
            category="workflows",
        ),
        Permission(
            id=uuid4(),
            name="workflow.publish",
            display_name="Publish Workflows",
            description="Publish workflows for production",
            resource=ResourceType.WORKFLOW,
            action=ActionType.PUBLISH,
            category="workflows",
        ),
        # Execution permissions
        Permission(
            id=uuid4(),
            name="execution.read",
            display_name="View Executions",
            description="View execution history and logs",
            resource=ResourceType.EXECUTION,
            action=ActionType.READ,
            category="executions",
        ),
        Permission(
            id=uuid4(),
            name="execution.cancel",
            display_name="Cancel Executions",
            description="Cancel running executions",
            resource=ResourceType.EXECUTION,
            action=ActionType.CANCEL,
            category="executions",
        ),
        Permission(
            id=uuid4(),
            name="execution.retry",
            display_name="Retry Executions",
            description="Retry failed executions",
            resource=ResourceType.EXECUTION,
            action=ActionType.RETRY,
            category="executions",
        ),
        # Robot permissions
        Permission(
            id=uuid4(),
            name="robot.create",
            display_name="Create Robots",
            description="Register new robots",
            resource=ResourceType.ROBOT,
            action=ActionType.CREATE,
            category="robots",
        ),
        Permission(
            id=uuid4(),
            name="robot.read",
            display_name="View Robots",
            description="View robot status and details",
            resource=ResourceType.ROBOT,
            action=ActionType.READ,
            category="robots",
        ),
        Permission(
            id=uuid4(),
            name="robot.update",
            display_name="Manage Robots",
            description="Update robot configuration",
            resource=ResourceType.ROBOT,
            action=ActionType.UPDATE,
            category="robots",
        ),
        Permission(
            id=uuid4(),
            name="robot.delete",
            display_name="Delete Robots",
            description="Remove robots",
            resource=ResourceType.ROBOT,
            action=ActionType.DELETE,
            category="robots",
        ),
        # User permissions
        Permission(
            id=uuid4(),
            name="user.read",
            display_name="View Users",
            description="View user profiles",
            resource=ResourceType.USER,
            action=ActionType.READ,
            category="users",
        ),
        Permission(
            id=uuid4(),
            name="user.invite",
            display_name="Invite Users",
            description="Invite new team members",
            resource=ResourceType.USER,
            action=ActionType.INVITE,
            category="users",
        ),
        Permission(
            id=uuid4(),
            name="user.update",
            display_name="Manage Users",
            description="Update user roles and settings",
            resource=ResourceType.USER,
            action=ActionType.UPDATE,
            category="users",
        ),
        Permission(
            id=uuid4(),
            name="user.remove",
            display_name="Remove Users",
            description="Remove users from tenant",
            resource=ResourceType.USER,
            action=ActionType.REMOVE,
            category="users",
        ),
        # Workspace permissions
        Permission(
            id=uuid4(),
            name="workspace.create",
            display_name="Create Workspaces",
            description="Create new workspaces",
            resource=ResourceType.WORKSPACE,
            action=ActionType.CREATE,
            category="workspaces",
        ),
        Permission(
            id=uuid4(),
            name="workspace.read",
            display_name="View Workspaces",
            description="View workspace details",
            resource=ResourceType.WORKSPACE,
            action=ActionType.READ,
            category="workspaces",
        ),
        Permission(
            id=uuid4(),
            name="workspace.update",
            display_name="Manage Workspaces",
            description="Update workspace settings",
            resource=ResourceType.WORKSPACE,
            action=ActionType.UPDATE,
            category="workspaces",
        ),
        Permission(
            id=uuid4(),
            name="workspace.delete",
            display_name="Delete Workspaces",
            description="Delete workspaces",
            resource=ResourceType.WORKSPACE,
            action=ActionType.DELETE,
            category="workspaces",
        ),
        # Credential permissions
        Permission(
            id=uuid4(),
            name="credential.create",
            display_name="Create Credentials",
            description="Add new credentials",
            resource=ResourceType.CREDENTIAL,
            action=ActionType.CREATE,
            category="credentials",
        ),
        Permission(
            id=uuid4(),
            name="credential.read",
            display_name="View Credentials",
            description="View credential metadata",
            resource=ResourceType.CREDENTIAL,
            action=ActionType.READ,
            category="credentials",
        ),
        Permission(
            id=uuid4(),
            name="credential.update",
            display_name="Update Credentials",
            description="Modify credentials",
            resource=ResourceType.CREDENTIAL,
            action=ActionType.UPDATE,
            category="credentials",
        ),
        Permission(
            id=uuid4(),
            name="credential.delete",
            display_name="Delete Credentials",
            description="Remove credentials",
            resource=ResourceType.CREDENTIAL,
            action=ActionType.DELETE,
            category="credentials",
        ),
        Permission(
            id=uuid4(),
            name="credential.use",
            display_name="Use Credentials",
            description="Use credentials in workflows",
            resource=ResourceType.CREDENTIAL,
            action=ActionType.USE,
            category="credentials",
        ),
        # API Key permissions
        Permission(
            id=uuid4(),
            name="apikey.create",
            display_name="Create API Keys",
            description="Generate new API keys",
            resource=ResourceType.API_KEY,
            action=ActionType.CREATE,
            category="apikeys",
        ),
        Permission(
            id=uuid4(),
            name="apikey.read",
            display_name="View API Keys",
            description="View API key metadata",
            resource=ResourceType.API_KEY,
            action=ActionType.READ,
            category="apikeys",
        ),
        Permission(
            id=uuid4(),
            name="apikey.revoke",
            display_name="Revoke API Keys",
            description="Revoke API keys",
            resource=ResourceType.API_KEY,
            action=ActionType.REVOKE,
            category="apikeys",
        ),
        # Audit permissions
        Permission(
            id=uuid4(),
            name="audit.read",
            display_name="View Audit Logs",
            description="Access audit history",
            resource=ResourceType.AUDIT,
            action=ActionType.READ,
            category="audit",
        ),
        Permission(
            id=uuid4(),
            name="audit.export",
            display_name="Export Audit Logs",
            description="Export audit data",
            resource=ResourceType.AUDIT,
            action=ActionType.EXPORT,
            category="audit",
        ),
        # Admin permissions
        Permission(
            id=uuid4(),
            name="tenant.settings",
            display_name="Tenant Settings",
            description="Manage tenant configuration",
            resource=ResourceType.TENANT,
            action=ActionType.SETTINGS,
            category="admin",
        ),
        Permission(
            id=uuid4(),
            name="tenant.billing",
            display_name="Billing Management",
            description="Manage subscription and billing",
            resource=ResourceType.TENANT,
            action=ActionType.BILLING,
            category="admin",
        ),
        Permission(
            id=uuid4(),
            name="role.manage",
            display_name="Manage Roles",
            description="Create and modify custom roles",
            resource=ResourceType.ROLE,
            action=ActionType.MANAGE,
            category="admin",
        ),
    ]

    return permissions
