"""
Vault Provider Implementations.

Supports multiple vault backends:
- HashiCorp Vault (enterprise production)
- Supabase Vault (managed cloud)
- Encrypted SQLite (local development)
"""

from casare_rpa.infrastructure.security.providers.factory import create_vault_provider
from casare_rpa.infrastructure.security.providers.hashicorp import (
    HashiCorpVaultProvider,
)
from casare_rpa.infrastructure.security.providers.sqlite_vault import (
    EncryptedSQLiteProvider,
)
from casare_rpa.infrastructure.security.providers.supabase_vault import (
    SupabaseVaultProvider,
)

__all__ = [
    "HashiCorpVaultProvider",
    "SupabaseVaultProvider",
    "EncryptedSQLiteProvider",
    "create_vault_provider",
]
