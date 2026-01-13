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

from casare_rpa.infrastructure.security.credential_provider import (
    ResolvedCredential,
    VaultCredentialProvider,
    create_credential_resolver,
    resolve_credentials_for_node,
)
from casare_rpa.infrastructure.security.data_masker import (
    DataMasker,
    MaskedLogger,
    MaskingConfig,
    get_masker,
    mask_sensitive_data,
)

from casare_rpa.infrastructure.security.gemini_subscription import (
    GeminiAuthConfig,
    GeminiRoute,
    GeminiRouteConfig,
    detect_gemini_route,
    get_vertex_location,
    get_vertex_project_id,
    is_gemini_model,
    normalize_gemini_model_name,
)
from casare_rpa.infrastructure.security.google_oauth import (
    GOOGLE_REVOKE_ENDPOINT,
    GOOGLE_TOKEN_ENDPOINT,
    GOOGLE_USERINFO_ENDPOINT,
    TOKEN_EXPIRY_BUFFER_SECONDS,
    GoogleOAuthCredentialData,
    GoogleOAuthError,
    GoogleOAuthManager,
    InvalidCredentialError,
    TokenExpiredError,
    TokenRefreshError,
    get_google_access_token,
    get_google_oauth_manager,
    get_google_user_info,
)
from casare_rpa.infrastructure.security.oauth2_base import (
    BaseOAuth2Manager,
    OAuth2CredentialData,
    OAuth2Error,
    build_oauth_url,
    decode_state,
    encode_state,
    generate_pkce_pair,
)
from casare_rpa.infrastructure.security.oauth_server import (
    LocalOAuthServer,
    OAuthCallbackHandler,
    build_google_auth_url,
)
from casare_rpa.infrastructure.security.providers import (
    EncryptedSQLiteProvider,
    HashiCorpVaultProvider,
    SupabaseVaultProvider,
    create_vault_provider,
)
from casare_rpa.infrastructure.security.rbac import (
    ActionType,
    AuthorizationService,
    InvalidRoleConfigError,
    # Data models
    Permission,
    PermissionCondition,
    PermissionDeniedError,
    # Services
    PermissionRegistry,
    # Exceptions
    RBACError,
    ResourceType,
    Role,
    RoleManager,
    RoleNotFoundError,
    RolePermission,
    # Enums
    SystemRole,
    UserPermissions,
    create_authorization_service,
    # Factory functions
    create_permission_registry,
    get_default_permissions,
    # Decorators
    require_permission,
)
from casare_rpa.infrastructure.security.rotation import (
    RotationFrequency,
    RotationHook,
    RotationPolicy,
    RotationRecord,
    RotationStatus,
    SecretRotationManager,
    setup_rotation_for_credentials,
)
from casare_rpa.infrastructure.security.tenancy import (
    APIKey,
    APIKeyService,
    APIKeyStatus,
    AuditAction,
    AuditLogEntry,
    AuditService,
    InvalidAPIKeyError,
    QuotaExceededError,
    RateLimitExceededError,
    # Data models
    ResourceQuotas,
    ResourceUsage,
    SSOConfig,
    SSOProvider,
    SubscriptionTier,
    # Exceptions
    TenancyError,
    Tenant,
    # Context
    TenantContext,
    TenantContextManager,
    TenantNotFoundError,
    # Services
    TenantService,
    # Enums
    TenantStatus,
    TenantSuspendedError,
    Workspace,
    create_api_key_service,
    create_audit_service,
    # Factory functions
    create_tenant_context_manager,
    create_tenant_service,
)
from casare_rpa.infrastructure.security.vault_client import (
    AuditEvent,
    AuditEventType,
    AuditLogger,
    CredentialType,
    SecretMetadata,
    SecretNotFoundError,
    SecretValue,
    VaultAuthenticationError,
    VaultBackend,
    VaultClient,
    VaultConfig,
    VaultConnectionError,
    VaultError,
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
    "AuditLogger",
    # Data Masking
    "DataMasker",
    "MaskedLogger",
    "MaskingConfig",
    "get_masker",
    "mask_sensitive_data",
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
    # OAUTH 2.0 BASE
    # ==========================================================================
    # Base classes
    "BaseOAuth2Manager",
    "OAuth2CredentialData",
    "OAuth2Error",
    # PKCE and state utilities
    "generate_pkce_pair",
    "encode_state",
    "decode_state",
    "build_oauth_url",

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
    # GEMINI SUBSCRIPTION
    # ==========================================================================
    # Enums
    "GeminiRoute",

    # Data classes
    "GeminiRouteConfig",
    "GeminiAuthConfig",
    # Utilities
    "detect_gemini_route",
    "is_gemini_model",
    "normalize_gemini_model_name",
    "get_vertex_project_id",
    "get_vertex_location",
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
