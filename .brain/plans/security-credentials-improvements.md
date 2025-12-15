# Security and Credentials Management: Research and Recommendations

**Date**: 2025-12-11
**Status**: Research Complete
**Priority**: High

---

## Executive Summary

CasareRPA has a **solid security foundation** with HashiCorp Vault integration, DPAPI-protected local storage, and comprehensive credential types. However, several gaps exist compared to enterprise RPA platforms like UiPath and Power Automate Desktop. This document outlines specific, actionable improvements with implementation priorities.

---

## 1. Current Security Assessment

### 1.1 Existing Strengths

| Component | Implementation | Status |
|-----------|---------------|--------|
| HashiCorp Vault Integration | Full KV v2 support, AppRole/Token/LDAP/Kubernetes auth | Excellent |
| Local Encrypted Storage | Fernet (AES-128-CBC) with DPAPI on Windows | Good |
| Credential Types | Username/Password, API Key, OAuth2, SSH, Certificates, Telegram, WhatsApp | Comprehensive |
| Credential Scoping | Global, Project, Workflow, Robot, Asset scopes | Good |
| Dynamic Secrets | Lease management, auto-renewal, revocation | Good |
| Basic Audit Logging | Loguru-based event logging | Basic |
| Secret Caching | TTL-based LRU cache with automatic refresh | Good |
| Multiple Backends | HashiCorp, Supabase, SQLite (dev) | Good |

### 1.2 Security Files Analyzed

| File | Purpose |
|------|---------|
| `src/casare_rpa/utils/security/credential_manager.py` | High-level credential management (Vault-only) |
| `src/casare_rpa/utils/security/secrets_manager.py` | Environment variable / .env file handling |
| `src/casare_rpa/utils/security/vault_client.py` | Legacy Vault client (utils layer) |
| `src/casare_rpa/infrastructure/security/vault_client.py` | Modern Vault client with multi-backend support |
| `src/casare_rpa/infrastructure/security/credential_store.py` | Local encrypted credential storage |
| `src/casare_rpa/infrastructure/security/credential_provider.py` | Workflow credential injection |
| `src/casare_rpa/infrastructure/security/providers/sqlite_vault.py` | Encrypted SQLite backend |

### 1.3 Encryption Details

- **Local Storage**: Fernet (AES-128-CBC) with HMAC
- **Key Derivation**: PBKDF2-HMAC-SHA256, 480,000 iterations (OWASP compliant)
- **Master Key Protection**: Windows DPAPI (CryptProtectData) or machine-derived fallback
- **Vault Communication**: TLS with optional client certificates

---

## 2. Competitor Analysis

### 2.1 UiPath Orchestrator

**Credential Store Integrations:**
- HashiCorp Vault (read-write and read-only modes)
- Azure Key Vault (with RBAC authentication)
- CyberArk CCP (with client certificates)
- AWS Secrets Manager
- Thycotic Secret Server
- BeyondTrust

**Key Security Features:**
| Feature | UiPath | CasareRPA |
|---------|--------|-----------|
| Multi-vault integration | 7+ vaults | 3 backends |
| Orchestrator Credentials Proxy | Yes | No |
| Robot-specific credentials | Yes | Partial (scope) |
| Certificate-based vault auth | Yes | Partial |
| Tenant isolation | Yes | No (single-tenant) |
| Built-in credential rotation | Vault-dependent | SQLite only |

**UiPath Best Practices:**
1. Use separate credential stores per tenant
2. Minimum 2048-bit certificates for CyberArk auth
3. HTTPS-only for credential proxy
4. Role-based credential access per robot

### 2.2 Power Automate Desktop

**Azure Key Vault Integration:**
- Environment variable-based secret references
- Automatic password rotation support
- ALM (Application Lifecycle Management) integration
- RBAC through Azure AD

**Key Features:**
| Feature | Power Automate | CasareRPA |
|---------|----------------|-----------|
| Azure Key Vault native | Yes | No |
| CyberArk integration | Yes (Get credential) | No |
| Credential rotation | Automatic via Azure | Manual |
| MFA for admin access | Azure AD | No |
| Secure input/output masking | Yes | No |
| Desktop flow credential injection | Automatic | Manual config |

### 2.3 Gap Analysis Summary

| Gap | Impact | Priority |
|-----|--------|----------|
| No Role-Based Access Control (RBAC) | High | P1 |
| Missing audit trail persistence | High | P1 |
| No Azure Key Vault integration | Medium | P2 |
| No CyberArk/BeyondTrust support | Medium | P2 |
| No credential rotation policies | Medium | P2 |
| No MFA for credential access | Medium | P2 |
| Missing input/output masking in logs | Medium | P2 |
| No compliance reporting (SOC2/GDPR) | Medium | P3 |

---

## 3. Security Best Practices for RPA Platforms

### 3.1 Credential Management

Based on industry standards:

1. **Never hardcode credentials** - Enforce via static analysis
2. **Use centralized vault** - Already implemented (HashiCorp)
3. **Implement least privilege** - Need RBAC
4. **Rotate credentials regularly** - Need policy engine
5. **Separate dev/test/prod credentials** - Need environment awareness
6. **Use unique bot identities** - Need bot identity management

### 3.2 Access Control (OWASP/NIST)

1. **RBAC**: Admin, Developer, Operator, Viewer roles
2. **MFA**: For credential management operations
3. **Session management**: Token expiration, refresh limits
4. **IP restrictions**: Allow-list for sensitive operations

### 3.3 Encryption Standards

1. **At rest**: AES-256 (upgrade from AES-128)
2. **In transit**: TLS 1.3 with certificate pinning
3. **Key management**: HSM support for enterprise
4. **Key rotation**: Automatic master key rotation

### 3.4 Audit and Compliance

1. **Immutable audit logs**: Tamper-proof storage
2. **Event correlation**: Link credential access to workflow execution
3. **Retention policies**: Configurable log retention
4. **Export formats**: SIEM integration (Splunk, ELK)

---

## 4. Recommendations

### 4.1 Priority 1: Critical (Implement First)

#### 4.1.1 Role-Based Access Control (RBAC)

**Problem**: Any user can access any credential in the system.

**Solution**: Implement RBAC with the following roles:

```python
class CredentialRole(Enum):
    ADMIN = "admin"           # Full access, manage roles
    CREDENTIAL_MANAGER = "credential_manager"  # Create/edit/delete credentials
    DEVELOPER = "developer"   # Read credentials for development
    OPERATOR = "operator"     # Use credentials in production workflows
    VIEWER = "viewer"         # View credential metadata only
```

**Implementation:**

```python
@dataclass
class CredentialPermission:
    credential_id: str
    role: CredentialRole
    user_id: str
    granted_at: datetime
    expires_at: Optional[datetime] = None

class RBACCredentialManager:
    async def get_credential(
        self,
        credential_id: str,
        user_context: UserContext
    ) -> Credential:
        # Check user has appropriate role
        if not await self._check_permission(credential_id, user_context):
            raise CredentialAccessDeniedError(
                f"User {user_context.user_id} does not have access to credential {credential_id}"
            )
        # Audit log the access
        await self._audit_log.log_access(credential_id, user_context)
        return await self._vault.get_credential(credential_id)
```

**Files to modify:**
- `src/casare_rpa/infrastructure/security/credential_provider.py`
- `src/casare_rpa/domain/entities/` (add User, Role entities)
- New: `src/casare_rpa/infrastructure/security/rbac_manager.py`

**Estimated effort**: 3-5 days

---

#### 4.1.2 Persistent Audit Trail

**Problem**: Current audit logging uses in-memory buffer with limited retention.

**Solution**: Implement persistent, tamper-evident audit logging.

**Schema:**

```python
@dataclass
class AuditRecord:
    id: str                          # UUID
    timestamp: datetime              # UTC
    event_type: AuditEventType
    actor_id: str                    # User or Robot ID
    actor_type: Literal["user", "robot", "system"]
    resource_type: str               # "credential", "workflow", etc.
    resource_id: str
    action: str                      # "read", "write", "delete", "rotate"
    result: Literal["success", "failure", "denied"]
    details: Dict[str, Any]          # Sanitized details (no secrets)
    workflow_id: Optional[str]
    execution_id: Optional[str]
    ip_address: Optional[str]
    checksum: str                    # SHA-256 of previous record (chain)
```

**Features:**
- SQLite/PostgreSQL storage with encryption
- Hash chain for tamper detection
- SIEM export (JSON, CEF formats)
- Retention policy configuration
- Query API for compliance reports

**Files to create:**
- `src/casare_rpa/infrastructure/security/audit_store.py`
- `src/casare_rpa/infrastructure/security/audit_exporter.py`

**Estimated effort**: 2-3 days

---

#### 4.1.3 Sensitive Data Masking

**Problem**: Credentials may appear in logs or workflow history.

**Solution**: Implement automatic masking of sensitive fields.

```python
SENSITIVE_PATTERNS = [
    r"password",
    r"secret",
    r"api[_-]?key",
    r"token",
    r"bearer",
    r"authorization",
]

class SensitiveDataMasker:
    def mask_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive values in dictionary."""
        masked = {}
        for key, value in data.items():
            if self._is_sensitive_key(key):
                masked[key] = "***MASKED***"
            elif isinstance(value, dict):
                masked[key] = self.mask_dict(value)
            else:
                masked[key] = value
        return masked
```

**Integration points:**
- Workflow execution logs
- Node property display
- Export/import operations
- Error messages

**Estimated effort**: 1-2 days

---

### 4.2 Priority 2: Important (Near-term)

#### 4.2.1 Azure Key Vault Integration

**Rationale**: Many enterprise customers use Azure; native integration reduces friction.

**Implementation:**

```python
class AzureKeyVaultProvider(VaultProvider):
    """Azure Key Vault provider using azure-identity and azure-keyvault-secrets."""

    def __init__(self, config: VaultConfig):
        self._vault_url = config.azure_vault_url
        self._credential = DefaultAzureCredential()
        self._client = SecretClient(
            vault_url=self._vault_url,
            credential=self._credential
        )
```

**Authentication methods:**
- Managed Identity (Azure VMs/App Service)
- Service Principal (client ID/secret)
- Azure CLI (development)
- Interactive (browser-based)

**Dependencies:**
```
azure-identity>=1.15.0
azure-keyvault-secrets>=4.8.0
```

**Estimated effort**: 2-3 days

---

#### 4.2.2 AWS Secrets Manager Integration

**Implementation:**

```python
class AWSSecretsManagerProvider(VaultProvider):
    """AWS Secrets Manager provider using boto3."""

    def __init__(self, config: VaultConfig):
        self._client = boto3.client(
            'secretsmanager',
            region_name=config.aws_region,
        )
```

**Dependencies:**
```
boto3>=1.34.0
```

**Estimated effort**: 2 days

---

#### 4.2.3 Credential Rotation Policies

**Problem**: No automated credential rotation.

**Solution**: Implement rotation policy engine.

```python
@dataclass
class RotationPolicy:
    credential_id: str
    rotation_interval_days: int
    notification_before_days: int
    auto_rotate: bool
    rotation_handler: Optional[str]  # Custom rotation script
    last_rotated: Optional[datetime]
    next_rotation: Optional[datetime]

class RotationManager:
    async def check_rotations(self):
        """Check and execute pending rotations."""
        policies = await self._get_due_policies()
        for policy in policies:
            if policy.auto_rotate:
                await self._execute_rotation(policy)
            else:
                await self._send_notification(policy)
```

**Estimated effort**: 3 days

---

#### 4.2.4 Multi-Factor Authentication for Admin Operations

**Implementation options:**
1. TOTP (Time-based One-Time Password) - Recommended
2. SMS/Email verification
3. Hardware tokens (FIDO2)

```python
class MFAManager:
    def generate_totp_secret(self, user_id: str) -> str:
        """Generate TOTP secret for user."""
        secret = pyotp.random_base32()
        # Store encrypted in user profile
        return secret

    def verify_totp(self, user_id: str, code: str) -> bool:
        """Verify TOTP code."""
        totp = pyotp.TOTP(self._get_user_secret(user_id))
        return totp.verify(code)
```

**Dependencies:**
```
pyotp>=2.9.0
qrcode>=7.4.0
```

**Estimated effort**: 2 days

---

### 4.3 Priority 3: Enhancement (Long-term)

#### 4.3.1 Compliance Reporting Module

**Features:**
- SOC 2 control evidence collection
- GDPR data access reports
- HIPAA audit trail reports
- Custom report templates

**Report types:**
1. Credential Access Report
2. Failed Authentication Report
3. Permission Change Report
4. Credential Lifecycle Report

**Estimated effort**: 5 days

---

#### 4.3.2 CyberArk Integration

**Rationale**: Enterprise requirement for large organizations.

```python
class CyberArkProvider(VaultProvider):
    """CyberArk Central Credential Provider (CCP) integration."""

    async def get_secret(self, path: str, version: Optional[int] = None) -> SecretValue:
        # Use REST API with client certificate auth
        response = await self._http_client.get(
            f"{self._base_url}/AIMWebService/api/Accounts",
            params={"AppID": self._app_id, "Safe": self._safe, "Object": path},
            cert=(self._client_cert, self._client_key),
        )
```

**Requirements:**
- Client certificate (2048-bit minimum)
- CyberArk application ID
- Safe and folder configuration

**Estimated effort**: 3-4 days

---

#### 4.3.3 Hardware Security Module (HSM) Support

**Use cases:**
- Enterprise key management
- FIPS 140-2 compliance
- High-security deployments

**Options:**
- AWS CloudHSM
- Azure Dedicated HSM
- Thales Luna Network HSM
- Software HSM (SoftHSM2 for testing)

**Estimated effort**: 5-7 days

---

#### 4.3.4 Encryption Upgrade to AES-256

**Current**: AES-128-CBC (Fernet)
**Recommended**: AES-256-GCM

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class AES256GCMEncryption:
    def __init__(self, key: bytes):
        assert len(key) == 32  # 256 bits
        self._aesgcm = AESGCM(key)

    def encrypt(self, plaintext: bytes) -> bytes:
        nonce = os.urandom(12)
        ciphertext = self._aesgcm.encrypt(nonce, plaintext, None)
        return nonce + ciphertext
```

**Migration plan:**
1. Add version field to encrypted data
2. Support both AES-128 and AES-256
3. Auto-upgrade on read/write
4. Deprecate AES-128 after migration period

**Estimated effort**: 2 days

---

## 5. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
- [ ] RBAC implementation
- [ ] Persistent audit logging
- [ ] Sensitive data masking

### Phase 2: Enterprise Integrations (Weeks 3-4)
- [ ] Azure Key Vault provider
- [ ] AWS Secrets Manager provider
- [ ] Credential rotation policies

### Phase 3: Security Hardening (Weeks 5-6)
- [ ] MFA for admin operations
- [ ] AES-256 encryption upgrade
- [ ] IP restriction support

### Phase 4: Compliance (Weeks 7-8)
- [ ] Compliance reporting module
- [ ] CyberArk integration
- [ ] Documentation and security guide

---

## 6. Configuration Schema Enhancement

Proposed additions to `VaultConfig`:

```python
class VaultConfig(BaseModel):
    # ... existing fields ...

    # RBAC
    rbac_enabled: bool = True
    rbac_default_role: CredentialRole = CredentialRole.VIEWER

    # Azure Key Vault
    azure_vault_url: Optional[str] = None
    azure_tenant_id: Optional[str] = None
    azure_client_id: Optional[str] = None
    azure_client_secret: Optional[SecretStr] = None

    # AWS Secrets Manager
    aws_region: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[SecretStr] = None

    # Rotation
    rotation_check_interval_hours: int = 24
    default_rotation_days: int = 90

    # Compliance
    audit_retention_days: int = 365
    compliance_mode: Optional[Literal["soc2", "gdpr", "hipaa"]] = None
```

---

## 7. Security Checklist for Code Review

When reviewing credential-related code:

- [ ] No hardcoded credentials in source
- [ ] Credentials retrieved from vault only
- [ ] Proper error handling (no secret leakage in errors)
- [ ] Audit logging for all credential access
- [ ] Input validation on credential names/paths
- [ ] Timeouts on vault operations
- [ ] Secure memory handling (clear after use)
- [ ] TLS verification enabled
- [ ] Appropriate scope/role checks

---

## Sources

### UiPath Documentation
- [Managing credential stores](https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/managing-credential-stores)
- [HashiCorp Vault Integration](https://docs.uipath.com/orchestrator/standalone/2022.4/user-guide/hashicorp-vault-integration)
- [Azure Key Vault Integration](https://docs.uipath.com/orchestrator/standalone/2022.4/user-guide/azure-key-vault-integration)
- [Security Best Practices](https://docs.uipath.com/installation-and-upgrade/docs/security-best-practices)

### Power Automate Documentation
- [Create an Azure Key Vault credential](https://learn.microsoft.com/en-us/power-automate/desktop-flows/create-azurekeyvault-credential)
- [Announcing Azure Key Vault credentials](https://www.microsoft.com/en-us/power-platform/blog/power-automate/announcing-azure-key-vault-credentials-for-desktop-flow-connections-preview/)
- [March 2025 update](https://www.microsoft.com/en-us/power-platform/blog/power-automate/march-2025-update-of-power-automate-for-desktop/)

### RPA Security Best Practices
- [10 RPA Security Best Practices for Compliance](https://optiblack.com/insights/10-rpa-security-best-practices-for-compliance)
- [RPA Security and Compliance Best Practices](https://www.foundingminds.com/securing-the-automation-rpa-security-and-compliance-best-practices/)
- [RPA Security Best Practices - LinkedIn](https://www.linkedin.com/advice/1/what-best-practices-rpa-security-access-control-u5wwc)
- [RPA Security - RPATech](https://www.rpatech.ai/rpa-security/)

### Windows DPAPI
- [Data Protection API - Wikipedia](https://en.wikipedia.org/wiki/Data_Protection_API)
- [Windows Data Protection - Microsoft](https://learn.microsoft.com/en-us/previous-versions/ms995355(v=msdn.10))
- [Secure Secret Management with DPAPI](https://premr.dev/blog/windows-secure-secrets-using-dpapi-c/)

---

## Appendix A: Node Mapping for Credential Access

| Node Type | Credential Requirement | Recommended Scope |
|-----------|----------------------|-------------------|
| BrowserNode | Username/Password | Workflow |
| DatabaseNode | Connection String | Project |
| APINode | API Key | Global |
| EmailNode | OAuth2 / SMTP credentials | Project |
| TelegramNode | Bot Token | Global |
| WhatsAppNode | Access Token | Global |
| SFTPNode | SSH Key / Password | Project |
| AWSNode | AWS Credentials | Global |

---

## Appendix B: Environment Variables Reference

| Variable | Purpose | Required |
|----------|---------|----------|
| `VAULT_ADDR` | HashiCorp Vault URL | For Vault backend |
| `VAULT_TOKEN` | Vault authentication token | For token auth |
| `VAULT_ROLE_ID` | AppRole role ID | For AppRole auth |
| `VAULT_SECRET_ID` | AppRole secret ID | For AppRole auth |
| `AZURE_VAULT_URL` | Azure Key Vault URL | For Azure backend |
| `AZURE_TENANT_ID` | Azure AD tenant | For Azure auth |
| `AWS_REGION` | AWS region | For AWS backend |
| `CASARE_VAULT_KEY` | Local SQLite encryption key | For local dev |
| `CASARE_AUDIT_PATH` | Audit log storage path | Optional |
