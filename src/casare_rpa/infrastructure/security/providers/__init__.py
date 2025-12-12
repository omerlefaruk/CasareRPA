"""
Vault Provider Implementations.

Supports multiple vault backends:
- HashiCorp Vault (enterprise production)
- Supabase Vault (managed cloud)
- Encrypted SQLite (local development)
- Azure Key Vault (Azure cloud)
- AWS Secrets Manager (AWS cloud)
"""

from casare_rpa.infrastructure.security.providers.factory import (
    create_vault_provider,
    get_available_backends,
    get_recommended_backend,
)
from casare_rpa.infrastructure.security.providers.hashicorp import (
    HashiCorpVaultProvider,
)
from casare_rpa.infrastructure.security.providers.sqlite_vault import (
    EncryptedSQLiteProvider,
)
from casare_rpa.infrastructure.security.providers.supabase_vault import (
    SupabaseVaultProvider,
)

# Lazy imports for cloud providers (optional dependencies)
try:
    from casare_rpa.infrastructure.security.providers.azure_keyvault import (
        AzureKeyVaultProvider,
    )
except ImportError:
    AzureKeyVaultProvider = None  # type: ignore

try:
    from casare_rpa.infrastructure.security.providers.aws_secrets import (
        AWSSecretsManagerProvider,
    )
except ImportError:
    AWSSecretsManagerProvider = None  # type: ignore

__all__ = [
    "HashiCorpVaultProvider",
    "SupabaseVaultProvider",
    "EncryptedSQLiteProvider",
    "AzureKeyVaultProvider",
    "AWSSecretsManagerProvider",
    "create_vault_provider",
    "get_available_backends",
    "get_recommended_backend",
]
