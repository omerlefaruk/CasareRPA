# Infrastructure Security Index

Quick reference for enterprise security features. Use for fast discovery.

## Overview

| Aspect | Description |
|--------|-------------|
| Purpose | Enterprise security: vault, RBAC, OAuth, multi-tenancy |
| Files | 18 files |
| Exports | 91 total exports |

## Vault / Credentials

### Core Client

| Export | Source | Description |
|--------|--------|-------------|
| `VaultClient` | `vault_client.py` | Main vault client |
| `VaultConfig` | `vault_client.py` | Vault configuration |
| `VaultBackend` | `vault_client.py` | Backend enum (HashiCorp, Supabase, SQLite) |

### Data Models

| Export | Source | Description |
|--------|--------|-------------|
| `SecretMetadata` | `vault_client.py` | Secret metadata |
| `SecretValue` | `vault_client.py` | Secret value wrapper |
| `CredentialType` | `vault_client.py` | Credential type enum |

### Errors

| Export | Source | Description |
|--------|--------|-------------|
| `VaultError` | `vault_client.py` | Base vault error |
| `SecretNotFoundError` | `vault_client.py` | Secret not found |
| `VaultConnectionError` | `vault_client.py` | Connection failed |
| `VaultAuthenticationError` | `vault_client.py` | Auth failed |

### Audit

| Export | Source | Description |
|--------|--------|-------------|
| `AuditEvent` | `vault_client.py` | Audit event data |
| `AuditEventType` | `vault_client.py` | Event type enum |

### Providers

| Export | Source | Description |
|--------|--------|-------------|
| `HashiCorpVaultProvider` | `providers/hashicorp.py` | HashiCorp Vault (production) |
| `SupabaseVaultProvider` | `providers/supabase_vault.py` | Supabase Vault (managed cloud) |
| `EncryptedSQLiteProvider` | `providers/sqlite_vault.py` | SQLite (development) |
| `create_vault_provider()` | `providers/factory.py` | Factory function |

### Integration

| Export | Source | Description |
|--------|--------|-------------|
| `VaultCredentialProvider` | `credential_provider.py` | Workflow credential resolver |
| `ResolvedCredential` | `credential_provider.py` | Resolved credential data |
| `create_credential_resolver()` | `credential_provider.py` | Factory function |
| `resolve_credentials_for_node()` | `credential_provider.py` | Node credential injection |

### Secret Rotation

| Export | Source | Description |
|--------|--------|-------------|
| `SecretRotationManager` | `rotation.py` | Rotation management |
| `RotationPolicy` | `rotation.py` | Rotation policy |
| `RotationFrequency` | `rotation.py` | Frequency enum |
| `RotationStatus` | `rotation.py` | Status enum |
| `RotationRecord` | `rotation.py` | Rotation record |
| `RotationHook` | `rotation.py` | Custom rotation hook |
| `setup_rotation_for_credentials()` | `rotation.py` | Setup helper |

## RBAC (Role-Based Access Control)

### Enums

| Export | Source | Description |
|--------|--------|-------------|
| `SystemRole` | `rbac.py` | ADMIN, DEVELOPER, VIEWER, etc. |
| `ResourceType` | `rbac.py` | WORKFLOW, ROBOT, CREDENTIAL, etc. |
| `ActionType` | `rbac.py` | CREATE, READ, UPDATE, DELETE, EXECUTE |

### Exceptions

| Export | Source | Description |
|--------|--------|-------------|
| `RBACError` | `rbac.py` | Base RBAC error |
| `PermissionDeniedError` | `rbac.py` | Permission denied |
| `RoleNotFoundError` | `rbac.py` | Role not found |
| `InvalidRoleConfigError` | `rbac.py` | Invalid config |

### Data Models

| Export | Source | Description |
|--------|--------|-------------|
| `Permission` | `rbac.py` | Permission definition |
| `PermissionCondition` | `rbac.py` | Conditional permission |
| `RolePermission` | `rbac.py` | Role-permission mapping |
| `Role` | `rbac.py` | Role definition |
| `UserPermissions` | `rbac.py` | User permission set |

### Services

| Export | Source | Description |
|--------|--------|-------------|
| `PermissionRegistry` | `rbac.py` | Permission registry |
| `RoleManager` | `rbac.py` | Role CRUD |
| `AuthorizationService` | `rbac.py` | Authorization checks |

### Decorators & Factories

| Export | Source | Description |
|--------|--------|-------------|
| `require_permission` | `rbac.py` | Permission decorator |
| `create_permission_registry()` | `rbac.py` | Factory |
| `create_authorization_service()` | `rbac.py` | Factory |
| `get_default_permissions()` | `rbac.py` | Default permissions |

## OAuth 2.0 Base Infrastructure

### Base Classes

| Export | Source | Description |
|--------|--------|-------------|
| `BaseOAuth2Manager` | `oauth2_base.py` | Abstract base for OAuth managers |
| `OAuth2CredentialData` | `oauth2_base.py` | Base credential dataclass |
| `OAuth2Error` | `oauth2_base.py` | Base OAuth exception |

### PKCE (RFC 7636)

| Export | Source | Description |
|--------|--------|-------------|
| `PKCEPair` | `oauth2_base.py` | Code verifier + challenge |
| `generate_pkce_pair()` | `oauth2_base.py` | Generate PKCE pair |
| `encode_state()` | `oauth2_base.py` | Encode OAuth state |
| `decode_state()` | `oauth2_base.py` | Decode OAuth state |
| `build_oauth_url()` | `oauth2_base.py` | Build authorization URL |

## Google OAuth

### Data Classes

| Export | Source | Description |
|--------|--------|-------------|
| `GoogleOAuthCredentialData` | `google_oauth.py` | OAuth credential data |

### Manager

| Export | Source | Description |
|--------|--------|-------------|
| `GoogleOAuthManager` | `google_oauth.py` | OAuth flow manager |

### Exceptions

| Export | Source | Description |
|--------|--------|-------------|
| `GoogleOAuthError` | `google_oauth.py` | Base OAuth error |
| `TokenRefreshError` | `google_oauth.py` | Token refresh failed |
| `TokenExpiredError` | `google_oauth.py` | Token expired |
| `InvalidCredentialError` | `google_oauth.py` | Invalid credential |

### Constants

| Export | Source | Description |
|--------|--------|-------------|
| `GOOGLE_TOKEN_ENDPOINT` | `google_oauth.py` | Token endpoint URL |
| `GOOGLE_USERINFO_ENDPOINT` | `google_oauth.py` | User info URL |
| `GOOGLE_REVOKE_ENDPOINT` | `google_oauth.py` | Revoke URL |
| `TOKEN_EXPIRY_BUFFER_SECONDS` | `google_oauth.py` | Expiry buffer |

### Convenience Functions

| Export | Source | Description |
|--------|--------|-------------|
| `get_google_oauth_manager()` | `google_oauth.py` | Get manager singleton |
| `get_google_access_token()` | `google_oauth.py` | Get valid access token |
| `get_google_user_info()` | `google_oauth.py` | Get user info |

### OAuth Server

| Export | Source | Description |
|--------|--------|-------------|
| `LocalOAuthServer` | `oauth_server.py` | Local callback server |
| `OAuthCallbackHandler` | `oauth_server.py` | Callback handler |
| `build_google_auth_url()` | `oauth_server.py` | Build auth URL |

## Gemini AI Studio OAuth

### Data Classes

| Export | Source | Description |
|--------|--------|-------------|
| `GeminiTokenData` | `gemini_oauth.py` | OAuth token data |
| `GeminiAuthorizationRequest` | `gemini_oauth.py` | Auth request data |
| `GeminiTokenExchangeResult` | `gemini_oauth.py` | Token exchange result |

### Manager

| Export | Source | Description |
|--------|--------|-------------|
| `GeminiOAuthManager` | `gemini_oauth.py` | Gemini AI Studio OAuth manager |

### Exceptions

| Export | Source | Description |
|--------|--------|-------------|
| `GeminiOAuthError` | `gemini_oauth.py` | Base OAuth error |
| `TokenExpiredError` | `gemini_oauth.py` | Token expired |
| `InvalidCredentialError` | `gemini_oauth.py` | Invalid credential |
| `TokenRefreshError` | `gemini_oauth.py` | Token refresh failed |

### Constants

| Export | Source | Description |
|--------|--------|-------------|
| `GEMINI_CLIENT_ID` | `gemini_oauth.py` | OAuth client ID |
| `GEMINI_CLIENT_SECRET` | `gemini_oauth.py` | OAuth client secret |
| `GEMINI_API_BASE` | `gemini_oauth.py` | API endpoint |
| `GEMINI_SCOPES` | `gemini_oauth.py` | OAuth scopes |

### PKCE Helpers

| Export | Source | Description |
|--------|--------|-------------|
| `generate_code_verifier()` | `gemini_oauth.py` | Generate PKCE verifier |
| `generate_code_challenge()` | `gemini_oauth.py` | Generate PKCE challenge |
| `encode_state()` | `gemini_oauth.py` | Encode OAuth state |
| `decode_state()` | `gemini_oauth.py` | Decode OAuth state |

### OAuth Flow Functions

| Export | Source | Description |
|--------|--------|-------------|
| `build_gemini_auth_url()` | `gemini_oauth.py` | Build authorization URL |
| `exchange_gemini_code()` | `gemini_oauth.py` | Exchange code for tokens |
| `refresh_gemini_token()` | `gemini_oauth.py` | Refresh access token |
| `call_gemini_api()` | `gemini_oauth.py` | Direct API call |

### Convenience Functions

| Export | Source | Description |
|--------|--------|-------------|
| `get_gemini_oauth_manager()` | `gemini_oauth.py` | Get manager singleton |
| `get_gemini_access_token()` | `gemini_oauth.py` | Get valid access token |

### UI Integration

| Export | Source | Description |
|--------|--------|-------------|
| `GeminiStudioOAuthDialog` | `canvas.ui.dialogs.gemini_studio_oauth_dialog` | OAuth dialog UI |

## Gemini Subscription

### Enums

| Export | Source | Description |
|--------|--------|-------------|
| `GeminiRoute` | `gemini_subscription.py` | Route type (Vertex AI, Google AI Studio, Antigravity, OpenRouter) |
| `GeminiQuotaPool` | `gemini_subscription.py` | Quota pool (gemini-antigravity, gemini-cli) |

### Data Classes

| Export | Source | Description |
|--------|--------|-------------|
| `GeminiRouteConfig` | `gemini_subscription.py` | Route configuration |
| `GeminiAuthConfig` | `gemini_subscription.py` | Authentication configuration |

### Utilities

| Export | Source | Description |
|--------|--------|-------------|
| `detect_gemini_route()` | `gemini_subscription.py` | Detect optimal route for model |
| `is_gemini_model()` | `gemini_subscription.py` | Check if model is Gemini |
| `normalize_gemini_model_name()` | `gemini_subscription.py` | Normalize for LiteLLM |
| `get_vertex_project_id()` | `gemini_subscription.py` | Get GCP project ID |
| `get_vertex_location()` | `gemini_subscription.py` | Get Vertex AI location |

### Antigravity Integration

| Export | Source | Description |
|--------|--------|-------------|
| `build_antigravity_auth_url()` | `antigravity_oauth.py` | Build Antigravity auth URL |
| `exchange_antigravity_token()` | `antigravity_oauth.py` | Exchange auth code |
| `fetch_project_id()` | `antigravity_oauth.py` | Fetch GCP project ID |
| `parse_refresh_parts()` | `antigravity_oauth.py` | Parse refresh token format |
| `format_refresh_parts()` | `antigravity_oauth.py` | Format refresh token |

## Multi-Tenancy

### Enums

| Export | Source | Description |
|--------|--------|-------------|
| `TenantStatus` | `tenancy.py` | ACTIVE, SUSPENDED, DELETED |
| `SubscriptionTier` | `tenancy.py` | FREE, PRO, ENTERPRISE |
| `SSOProvider` | `tenancy.py` | GOOGLE, AZURE_AD, OKTA |
| `APIKeyStatus` | `tenancy.py` | ACTIVE, REVOKED, EXPIRED |
| `AuditAction` | `tenancy.py` | CREATE, UPDATE, DELETE, LOGIN |

### Exceptions

| Export | Source | Description |
|--------|--------|-------------|
| `TenancyError` | `tenancy.py` | Base tenancy error |
| `TenantNotFoundError` | `tenancy.py` | Tenant not found |
| `TenantSuspendedError` | `tenancy.py` | Tenant suspended |
| `QuotaExceededError` | `tenancy.py` | Quota exceeded |
| `RateLimitExceededError` | `tenancy.py` | Rate limit exceeded |
| `InvalidAPIKeyError` | `tenancy.py` | Invalid API key |

### Data Models

| Export | Source | Description |
|--------|--------|-------------|
| `ResourceQuotas` | `tenancy.py` | Quota limits |
| `ResourceUsage` | `tenancy.py` | Usage tracking |
| `SSOConfig` | `tenancy.py` | SSO configuration |
| `Tenant` | `tenancy.py` | Tenant data |
| `Workspace` | `tenancy.py` | Workspace data |
| `APIKey` | `tenancy.py` | API key data |
| `AuditLogEntry` | `tenancy.py` | Audit log entry |

### Context

| Export | Source | Description |
|--------|--------|-------------|
| `TenantContext` | `tenancy.py` | Current tenant context |
| `TenantContextManager` | `tenancy.py` | Context manager |

### Services

| Export | Source | Description |
|--------|--------|-------------|
| `TenantService` | `tenancy.py` | Tenant CRUD |
| `APIKeyService` | `tenancy.py` | API key management |
| `AuditService` | `tenancy.py` | Audit logging |

### Factory Functions

| Export | Source | Description |
|--------|--------|-------------|
| `create_tenant_context_manager()` | `tenancy.py` | Factory |
| `create_tenant_service()` | `tenancy.py` | Factory |
| `create_api_key_service()` | `tenancy.py` | Factory |
| `create_audit_service()` | `tenancy.py` | Factory |

## Usage Patterns

```python
# Vault usage
from casare_rpa.infrastructure.security import (
    VaultClient, VaultConfig, VaultBackend,
    create_vault_provider,
)

config = VaultConfig(backend=VaultBackend.SQLITE)
vault = VaultClient(config)
secret = await vault.get_secret("my-credential")

# RBAC
from casare_rpa.infrastructure.security import (
    AuthorizationService, require_permission,
    SystemRole, ResourceType, ActionType,
)

@require_permission(ResourceType.WORKFLOW, ActionType.EXECUTE)
async def run_workflow(workflow_id: str):
    ...

# Google OAuth
from casare_rpa.infrastructure.security import (
    GoogleOAuthManager, get_google_access_token,
)

manager = GoogleOAuthManager()
token = await get_google_access_token("my-credential")

# Multi-tenancy
from casare_rpa.infrastructure.security import (
    TenantContext, TenantService, create_tenant_service,
)

service = create_tenant_service()
tenant = await service.get_tenant("tenant-123")
```

## Related Modules

| Module | Relation |
|--------|----------|
| `infrastructure.resources` | Uses credentials |
| `canvas.ui.dialogs.credential_manager_dialog` | Credential UI |
| `canvas.ui.panels.credentials_panel` | Credentials panel |
