# Credential Management

CasareRPA provides secure credential storage with support for multiple backend providers and credential types.

## Overview

Credentials are the foundation of RPA automation, enabling robots to authenticate with websites, APIs, databases, and enterprise systems. CasareRPA's credential management system provides:

- **Encrypted storage** for all credential types
- **Multiple backend providers** (built-in, Vault, Azure, AWS)
- **Automatic rotation** support
- **Access auditing** for compliance
- **Secure injection** into workflows

## Credential Types

CasareRPA supports the following credential types:

| Type | Use Case | Fields |
|------|----------|--------|
| `USERNAME_PASSWORD` | Web login, database auth | username, password |
| `API_KEY` | REST APIs, SaaS services | api_key |
| `OAUTH2_TOKEN` | Google, Microsoft services | access_token, refresh_token, client_id, client_secret |
| `SSH_KEY` | Server access, Git | private_key, passphrase |
| `CERTIFICATE` | mTLS, code signing | certificate, private_key |
| `DATABASE_CONNECTION` | Database access | host, port, database, username, password |
| `AWS_CREDENTIALS` | AWS services | access_key_id, secret_access_key |
| `AZURE_CREDENTIALS` | Azure services | client_id, client_secret, tenant_id |
| `CUSTOM` | Any other credentials | user-defined fields |

## Built-in Credential Store

The built-in credential store provides AES-256-GCM encrypted storage suitable for development and small deployments.

### Setup

```python
from casare_rpa.infrastructure.security.credential_store import (
    CredentialStore,
    CredentialType,
    get_credential_store
)

# Get default store (uses application encryption key)
store = get_credential_store()

# Or create with custom key
store = CredentialStore(
    encryption_key=your_master_key,
    store_path="~/.casare/credentials.enc"
)
```

### Storing Credentials

```python
from casare_rpa.infrastructure.security.credential_store import (
    CredentialStore,
    CredentialType
)

store = get_credential_store()

# Store username/password credential
credential_id = store.save_credential(
    name="Production Database",
    credential_type=CredentialType.USERNAME_PASSWORD,
    category="database",
    data={
        "username": "app_user",
        "password": "secure_password_123"
    },
    description="Production PostgreSQL database",
    tags=["production", "database", "postgres"]
)

# Store API key
api_key_id = store.save_credential(
    name="OpenAI API Key",
    credential_type=CredentialType.API_KEY,
    category="ai",
    data={
        "api_key": "sk-xxxxxxxxxxxx"
    }
)

# Store OAuth2 tokens
oauth_id = store.save_credential(
    name="Google Workspace",
    credential_type=CredentialType.GOOGLE_OAUTH,
    category="google",
    data={
        "client_id": "xxx.apps.googleusercontent.com",
        "client_secret": "your_secret",
        "access_token": "ya29.xxx",
        "refresh_token": "1//xxx",
        "token_expiry": "2025-01-15T12:00:00Z",
        "scopes": ["gmail.readonly", "drive.readonly"]
    }
)
```

### Retrieving Credentials

```python
# Get credential by ID
credential = store.get_credential(credential_id)
# Returns: {"username": "app_user", "password": "secure_password_123"}

# Get credential info (without sensitive data)
info = store.get_credential_info(credential_id)
# Returns: {"name": "Production Database", "type": "username_password", ...}

# List credentials by category
db_credentials = store.list_credentials(category="database")

# Search by tags
production_creds = store.list_credentials(tags=["production"])
```

### Using Credentials in Workflows

```python
from casare_rpa.infrastructure.security.credential_store import get_credential_store

async def browser_login_node(credential_id: str, page: Page) -> None:
    """Login to website using stored credentials."""
    store = get_credential_store()
    creds = store.get_credential(credential_id)

    await page.fill("#username", creds["username"])
    await page.fill("#password", creds["password"])
    await page.click("#login-button")
```

## HashiCorp Vault Integration

For enterprise deployments, CasareRPA integrates with HashiCorp Vault for dynamic secrets and centralized credential management.

### Configuration

```python
from casare_rpa.infrastructure.security.vault_client import (
    VaultClient,
    VaultConfig,
    VaultBackend
)

config = VaultConfig(
    backend=VaultBackend.HASHICORP_VAULT,
    url="https://vault.example.com:8200",
    token="hvs.xxxxx",  # Or use other auth methods
    namespace="casare-rpa",  # Vault Enterprise namespace
    mount_path="secret"
)

async with VaultClient(config) as vault:
    # Operations here
    pass
```

### Authentication Methods

```python
# Token authentication
config = VaultConfig(
    backend=VaultBackend.HASHICORP_VAULT,
    url="https://vault.example.com:8200",
    token="hvs.xxxxx"
)

# AppRole authentication (recommended for robots)
config = VaultConfig(
    backend=VaultBackend.HASHICORP_VAULT,
    url="https://vault.example.com:8200",
    vault_role_id="role-id-xxx",
    vault_secret_id="secret-id-xxx"
)

# Kubernetes authentication (for K8s deployments)
config = VaultConfig(
    backend=VaultBackend.HASHICORP_VAULT,
    url="https://vault.example.com:8200",
    vault_role="casare-robot",
    # Uses mounted service account token
)
```

### Reading and Writing Secrets

```python
from casare_rpa.infrastructure.security.vault_client import VaultClient

async with VaultClient(config) as vault:
    # Write secret
    await vault.put_secret(
        path="casare/credentials/db-prod",
        data={
            "username": "app_user",
            "password": "secure_password"
        },
        credential_type=CredentialType.USERNAME_PASSWORD,
        metadata={"environment": "production"}
    )

    # Read secret
    secret = await vault.get_secret("casare/credentials/db-prod")
    print(secret.data["username"])
    print(secret.metadata.credential_type)

    # List secrets
    secrets = await vault.list_secrets("casare/credentials/")

    # Delete secret
    await vault.delete_secret("casare/credentials/old-cred")
```

### Secret Rotation

```python
async with VaultClient(config) as vault:
    # Rotate secret (generates new values based on type)
    new_metadata = await vault.rotate_secret("casare/credentials/api-key")
    print(f"Rotated at: {new_metadata.updated_at}")

    # For database credentials, Vault can manage rotation automatically
    # Configure Vault's database secrets engine separately
```

## Azure Key Vault Integration

For Azure deployments, CasareRPA integrates with Azure Key Vault.

### Configuration

```python
from casare_rpa.infrastructure.security.providers.azure_keyvault import (
    AzureKeyVaultProvider
)
from casare_rpa.infrastructure.security.vault_client import VaultConfig, VaultBackend

config = VaultConfig(
    backend=VaultBackend.AZURE_KEY_VAULT,
    azure_vault_url="https://casare-vault.vault.azure.net",
    # Authentication options:
    azure_client_id="app-client-id",
    azure_client_secret="app-secret",
    azure_tenant_id="tenant-id"
    # Or use managed identity (no credentials needed in Azure)
)
```

### Authentication Options

```python
# Service Principal (client credentials)
config = VaultConfig(
    backend=VaultBackend.AZURE_KEY_VAULT,
    azure_vault_url="https://vault.vault.azure.net",
    azure_client_id="xxx",
    azure_client_secret="xxx",
    azure_tenant_id="xxx"
)

# Managed Identity (Azure VMs, App Service, AKS)
config = VaultConfig(
    backend=VaultBackend.AZURE_KEY_VAULT,
    azure_vault_url="https://vault.vault.azure.net"
    # No credentials - uses managed identity automatically
)

# Azure CLI credentials (development)
config = VaultConfig(
    backend=VaultBackend.AZURE_KEY_VAULT,
    azure_vault_url="https://vault.vault.azure.net"
    # Falls back to Azure CLI if no other credentials
)
```

### Usage

```python
from casare_rpa.infrastructure.security.vault_client import VaultClient

async with VaultClient(config) as vault:
    # Azure Key Vault stores secrets by name (no path hierarchy)
    await vault.put_secret(
        path="db-prod-password",
        data={"value": "secure_password"},
        metadata={"tags": {"environment": "production"}}
    )

    secret = await vault.get_secret("db-prod-password")
    password = secret.data["value"]
```

## AWS Secrets Manager Integration

For AWS deployments, CasareRPA integrates with AWS Secrets Manager.

### Configuration

```python
from casare_rpa.infrastructure.security.providers.aws_secrets import (
    AWSSecretsManagerProvider
)
from casare_rpa.infrastructure.security.vault_client import VaultConfig, VaultBackend

config = VaultConfig(
    backend=VaultBackend.AWS_SECRETS_MANAGER,
    aws_region="us-east-1",
    # Optional: explicit credentials (otherwise uses default chain)
    aws_access_key_id="AKIAXXXXXXXX",
    aws_secret_access_key="secret_key",
    # Or use profile
    aws_profile="casare-prod"
)
```

### Authentication Options

```python
# Explicit credentials
config = VaultConfig(
    backend=VaultBackend.AWS_SECRETS_MANAGER,
    aws_region="us-east-1",
    aws_access_key_id="AKIAXXXXXXXX",
    aws_secret_access_key="xxxxx"
)

# Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
config = VaultConfig(
    backend=VaultBackend.AWS_SECRETS_MANAGER,
    aws_region="us-east-1"
)

# IAM Role (EC2, Lambda, ECS)
config = VaultConfig(
    backend=VaultBackend.AWS_SECRETS_MANAGER,
    aws_region="us-east-1"
    # Uses instance/task role automatically
)

# Profile from ~/.aws/credentials
config = VaultConfig(
    backend=VaultBackend.AWS_SECRETS_MANAGER,
    aws_region="us-east-1",
    aws_profile="casare-production"
)
```

### Usage

```python
from casare_rpa.infrastructure.security.vault_client import VaultClient

async with VaultClient(config) as vault:
    # Store secret
    await vault.put_secret(
        path="casare/db-prod",
        data={
            "username": "app_user",
            "password": "secure_password",
            "host": "db.example.com"
        },
        credential_type=CredentialType.DATABASE_CONNECTION
    )

    # Retrieve secret
    secret = await vault.get_secret("casare/db-prod")

    # AWS supports secret versioning
    secret_v1 = await vault.get_secret("casare/db-prod", version="v1")

    # Trigger rotation (if Lambda rotation configured)
    await vault.rotate_secret("casare/db-prod")

    # Get rotation status
    status = await vault.get_rotation_status("casare/db-prod")
    print(f"Rotation enabled: {status['rotation_enabled']}")
    print(f"Next rotation: {status['next_rotation_date']}")
```

### Secret Rotation with Lambda

```python
# AWS Secrets Manager can automatically rotate secrets using Lambda
# Configure in AWS Console or Terraform:
#
# resource "aws_secretsmanager_secret_rotation" "db_rotation" {
#   secret_id           = aws_secretsmanager_secret.db_prod.id
#   rotation_lambda_arn = aws_lambda_function.rotate_db.arn
#   rotation_rules {
#     automatically_after_days = 30
#   }
# }

# Check rotation status from CasareRPA
async with VaultClient(config) as vault:
    status = await vault.get_rotation_status("casare/db-prod")
    if status["rotation_enabled"]:
        print(f"Next rotation: {status['next_rotation_date']}")
```

## Credential Usage in Nodes

### Browser Nodes

```python
from casare_rpa.nodes.browser import LoginNode

# In workflow JSON
{
    "id": "login_step",
    "type": "LoginNode",
    "properties": {
        "credential_id": "${credentials.web_login}",
        "username_selector": "#username",
        "password_selector": "#password",
        "submit_selector": "#login"
    }
}
```

### HTTP Nodes

```python
from casare_rpa.nodes.http import HttpRequestNode

# API key authentication
{
    "type": "HttpRequestNode",
    "properties": {
        "url": "https://api.example.com/data",
        "headers": {
            "Authorization": "Bearer ${credentials.api_key.api_key}"
        }
    }
}

# Basic auth
{
    "type": "HttpRequestNode",
    "properties": {
        "url": "https://api.example.com/data",
        "auth": {
            "type": "basic",
            "credential_id": "${credentials.api_cred}"
        }
    }
}
```

### Database Nodes

```python
from casare_rpa.nodes.database import SqlQueryNode

{
    "type": "SqlQueryNode",
    "properties": {
        "credential_id": "${credentials.db_prod}",
        "query": "SELECT * FROM users WHERE status = 'active'"
    }
}
```

## Credential Security Best Practices

### 1. Use External Vault in Production

```python
# Development: built-in store
if settings.environment == "development":
    config = VaultConfig(backend=VaultBackend.LOCAL_FILE)

# Production: HashiCorp Vault or cloud provider
else:
    config = VaultConfig(
        backend=VaultBackend.HASHICORP_VAULT,
        url=settings.vault_url,
        vault_role_id=settings.vault_role_id,
        vault_secret_id=settings.vault_secret_id
    )
```

### 2. Implement Credential Rotation

```python
from datetime import datetime, timedelta

async def check_credential_age():
    """Alert on credentials older than 90 days."""
    store = get_credential_store()

    for cred in store.list_credentials():
        age = datetime.now() - cred.created_at
        if age > timedelta(days=90):
            await send_rotation_reminder(cred.name, cred.owner)
```

### 3. Audit Credential Access

```python
from casare_rpa.infrastructure.security.merkle_audit import (
    log_audit_event,
    AuditAction,
    ResourceType
)

# Automatically logged when credentials are accessed
async def get_credential_with_audit(credential_id: str, user_id: UUID) -> dict:
    store = get_credential_store()
    cred = store.get_credential(credential_id)

    await log_audit_event(
        action=AuditAction.CREDENTIAL_ACCESS,
        actor_id=user_id,
        resource_type=ResourceType.CREDENTIAL,
        resource_id=credential_id,
        details={"purpose": "workflow_execution"}
    )

    return cred
```

### 4. Use Least Privilege

```python
# Create scoped credentials
store.save_credential(
    name="Gmail - Read Only",
    credential_type=CredentialType.GOOGLE_OAUTH,
    data={
        "scopes": ["gmail.readonly"]  # Only read access
    }
)

# Separate credentials per environment
store.save_credential(name="DB - Production", ...)
store.save_credential(name="DB - Staging", ...)
```

### 5. Never Log Credentials

```python
from casare_rpa.infrastructure.security.data_masker import DataMasker

masker = DataMasker()

# Safe logging
logger.info(masker.mask_for_logging({
    "username": "app_user",
    "password": "secret123"
}))
# Output: {"username": "app_user", "password": "******"}
```

## Credential Migration

### From File to Vault

```python
async def migrate_credentials_to_vault():
    """Migrate credentials from local store to HashiCorp Vault."""
    local_store = get_credential_store()
    vault_config = VaultConfig(
        backend=VaultBackend.HASHICORP_VAULT,
        url="https://vault.example.com:8200",
        token=os.environ["VAULT_TOKEN"]
    )

    async with VaultClient(vault_config) as vault:
        for cred_info in local_store.list_credentials():
            cred_data = local_store.get_credential(cred_info.id)

            await vault.put_secret(
                path=f"casare/credentials/{cred_info.name}",
                data=cred_data,
                credential_type=cred_info.credential_type,
                metadata={"migrated_from": "local", "original_id": cred_info.id}
            )

            logger.info(f"Migrated: {cred_info.name}")
```

## Related Documentation

- [Security Architecture](./architecture.md)
- [Authentication Methods](./authentication.md)
- [Security Best Practices](./best-practices.md)
