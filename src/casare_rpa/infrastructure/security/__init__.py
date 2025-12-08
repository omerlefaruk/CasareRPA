"""
CasareRPA Infrastructure Security Layer.

Provides enterprise security features:
- Secure credential management with multiple backend support
  - HashiCorp Vault (production)
  - Supabase Vault (managed cloud)
  - Encrypted SQLite (development fallback)
- Role-Based Access Control (RBAC)
- Multi-tenancy with data isolation
- API key management
- Audit logging

Integrates with workflow execution for transparent credential injection.
"""

from casare_rpa.infrastructure.security.vault_client import (
    VaultClient,
    VaultConfig,
    VaultBackend,
    SecretMetadata,
    SecretValue,
    CredentialType,
    VaultError,
    SecretNotFoundError,
    VaultConnectionError,
    VaultAuthenticationError,
    AuditEvent,
    AuditEventType,
)
from casare_rpa.infrastructure.security.providers import (
    HashiCorpVaultProvider,
    SupabaseVaultProvider,
    EncryptedSQLiteProvider,
    create_vault_provider,
)
from casare_rpa.infrastructure.security.credential_provider import (
    VaultCredentialProvider,
    ResolvedCredential,
    create_credential_resolver,
    resolve_credentials_for_node,
)
from casare_rpa.infrastructure.security.rotation import (
    SecretRotationManager,
    RotationPolicy,
    RotationFrequency,
    RotationStatus,
    RotationRecord,
    RotationHook,
    setup_rotation_for_credentials,
)
from casare_rpa.infrastructure.security.rbac import (
    # Enums
    SystemRole,
    ResourceType,
    ActionType,
    # Exceptions
    RBACError,
    PermissionDeniedError,
    RoleNotFoundError,
    InvalidRoleConfigError,
    # Data models
    Permission,
    PermissionCondition,
    RolePermission,
    Role,
    UserPermissions,
    # Services
    PermissionRegistry,
    RoleManager,
    AuthorizationService,
    # Decorators
    require_permission,
    # Factory functions
    create_permission_registry,
    create_authorization_service,
    get_default_permissions,
)
from casare_rpa.infrastructure.security.google_oauth import (
    GoogleOAuthCredentialData,
    GoogleOAuthManager,
    GoogleOAuthError,
    TokenRefreshError,
    TokenExpiredError,
    InvalidCredentialError,
    GOOGLE_TOKEN_ENDPOINT,
    GOOGLE_USERINFO_ENDPOINT,
    GOOGLE_REVOKE_ENDPOINT,
    TOKEN_EXPIRY_BUFFER_SECONDS,
    get_google_oauth_manager,
    get_google_access_token,
    get_google_user_info,
)
from casare_rpa.infrastructure.security.oauth_server import (
    LocalOAuthServer,
    OAuthCallbackHandler,
    build_google_auth_url,
)
from casare_rpa.infrastructure.security.tenancy import (
    # Enums
    TenantStatus,
    SubscriptionTier,
    SSOProvider,
    APIKeyStatus,
    AuditAction,
    # Exceptions
    TenancyError,
    TenantNotFoundError,
    TenantSuspendedError,
    QuotaExceededError,
    RateLimitExceededError,
    InvalidAPIKeyError,
    # Data models
    ResourceQuotas,
    ResourceUsage,
    SSOConfig,
    Tenant,
    Workspace,
    APIKey,
    AuditLogEntry,
    # Context
    TenantContext,
    TenantContextManager,
    # Services
    TenantService,
    APIKeyService,
    AuditService,
    # Factory functions
    create_tenant_context_manager,
    create_tenant_service,
    create_api_key_service,
    create_audit_service,
)

__all__ = [
    # ==========================================================================
    # VAULT / CREDENTIALS
    # ==========================================================================
    # Core client
    "VaultClient",
    "VaultConfig",
    "VaultBackend",
    # Data models
    "SecretMetadata",
    "SecretValue",
    "CredentialType",
    # Errors
    "VaultError",
    "SecretNotFoundError",
    "VaultConnectionError",
    "VaultAuthenticationError",
    # Audit
    "AuditEvent",
    "AuditEventType",
    # Providers
    "HashiCorpVaultProvider",
    "SupabaseVaultProvider",
    "EncryptedSQLiteProvider",
    "create_vault_provider",
    # Integration
    "VaultCredentialProvider",
    "ResolvedCredential",
    "create_credential_resolver",
    "resolve_credentials_for_node",
    # Rotation
    "SecretRotationManager",
    "RotationPolicy",
    "RotationFrequency",
    "RotationStatus",
    "RotationRecord",
    "RotationHook",
    "setup_rotation_for_credentials",
    # ==========================================================================
    # RBAC
    # ==========================================================================
    # Enums
    "SystemRole",
    "ResourceType",
    "ActionType",
    # Exceptions
    "RBACError",
    "PermissionDeniedError",
    "RoleNotFoundError",
    "InvalidRoleConfigError",
    # Data models
    "Permission",
    "PermissionCondition",
    "RolePermission",
    "Role",
    "UserPermissions",
    # Services
    "PermissionRegistry",
    "RoleManager",
    "AuthorizationService",
    # Decorators
    "require_permission",
    # Factory functions
    "create_permission_registry",
    "create_authorization_service",
    "get_default_permissions",
    # ==========================================================================
    # GOOGLE OAUTH
    # ==========================================================================
    # Data classes
    "GoogleOAuthCredentialData",
    # Manager
    "GoogleOAuthManager",
    # Exceptions
    "GoogleOAuthError",
    "TokenRefreshError",
    "TokenExpiredError",
    "InvalidCredentialError",
    # Constants
    "GOOGLE_TOKEN_ENDPOINT",
    "GOOGLE_USERINFO_ENDPOINT",
    "GOOGLE_REVOKE_ENDPOINT",
    "TOKEN_EXPIRY_BUFFER_SECONDS",
    # Convenience functions
    "get_google_oauth_manager",
    "get_google_access_token",
    "get_google_user_info",
    # OAuth Server
    "LocalOAuthServer",
    "OAuthCallbackHandler",
    "build_google_auth_url",
    # ==========================================================================
    # MULTI-TENANCY
    # ==========================================================================
    # Enums
    "TenantStatus",
    "SubscriptionTier",
    "SSOProvider",
    "APIKeyStatus",
    "AuditAction",
    # Exceptions
    "TenancyError",
    "TenantNotFoundError",
    "TenantSuspendedError",
    "QuotaExceededError",
    "RateLimitExceededError",
    "InvalidAPIKeyError",
    # Data models
    "ResourceQuotas",
    "ResourceUsage",
    "SSOConfig",
    "Tenant",
    "Workspace",
    "APIKey",
    "AuditLogEntry",
    # Context
    "TenantContext",
    "TenantContextManager",
    # Services
    "TenantService",
    "APIKeyService",
    "AuditService",
    # Factory functions
    "create_tenant_context_manager",
    "create_tenant_service",
    "create_api_key_service",
    "create_audit_service",
]
