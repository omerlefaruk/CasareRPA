"""
Supabase Vault Provider Implementation.

Supabase Vault provides managed secret storage using Postgres with
transparent encryption. Secrets are stored in the vault schema and
accessed via Postgres functions.

Reference: https://supabase.com/docs/guides/database/vault
"""

from datetime import UTC, datetime
from typing import Any

from loguru import logger

from casare_rpa.infrastructure.security.vault_client import (
    CredentialType,
    SecretMetadata,
    SecretNotFoundError,
    SecretValue,
    VaultAuthenticationError,
    VaultConfig,
    VaultConnectionError,
    VaultProvider,
)

# Optional asyncpg import
try:
    import asyncpg

    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False
    asyncpg = None


class SupabaseVaultProvider(VaultProvider):
    """
    Supabase Vault provider using Postgres vault extension.

    Secrets are stored encrypted at rest using Supabase's Vault extension.
    Access is controlled via RLS policies and Postgres roles.

    The vault uses a simple key-value model where:
    - Secrets are stored in the `vault.secrets` table
    - Each secret has a name (path), encrypted value, and description
    - Secrets can have associated metadata as JSONB
    """

    def __init__(self, config: VaultConfig) -> None:
        """
        Initialize Supabase Vault provider.

        Args:
            config: Vault configuration with Supabase settings
        """
        if not ASYNCPG_AVAILABLE:
            raise ImportError(
                "Supabase Vault support requires asyncpg library. "
                "Install with: pip install asyncpg"
            )

        self._config = config
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        """Connect to Supabase database."""
        if not self._config.supabase_url:
            raise VaultConnectionError("Supabase URL not configured")

        if not self._config.supabase_key:
            raise VaultConnectionError("Supabase service key not configured")

        try:
            # Parse Supabase URL to get Postgres connection string
            # Supabase URLs are typically: https://project.supabase.co
            # We need to convert to: postgres://...
            postgres_url = self._build_postgres_url()

            self._pool = await asyncpg.create_pool(
                postgres_url,
                min_size=1,
                max_size=10,
                command_timeout=30.0,
                statement_cache_size=0,  # Required for pgbouncer/Supabase
            )

            # Verify vault extension is available
            async with self._pool.acquire() as conn:
                result = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'supabase_vault')"
                )
                if not result:
                    logger.warning(
                        "Supabase Vault extension not found. " "Using fallback table-based storage."
                    )
                    await self._ensure_fallback_tables(conn)

            logger.info(f"Connected to Supabase Vault at {self._config.supabase_url}")

        except asyncpg.InvalidPasswordError as e:
            raise VaultAuthenticationError(f"Supabase authentication failed: {e}") from e
        except Exception as e:
            raise VaultConnectionError(f"Failed to connect to Supabase: {e}") from e

    async def disconnect(self) -> None:
        """Disconnect from Supabase."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("Disconnected from Supabase Vault")

    async def is_connected(self) -> bool:
        """Check if connected to Supabase."""
        if not self._pool:
            return False
        try:
            async with self._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception:
            return False

    def _ensure_pool(self) -> "asyncpg.Pool":
        """Ensure connection pool is available."""
        if not self._pool:
            raise VaultConnectionError("Not connected to Supabase")
        return self._pool

    def _build_postgres_url(self) -> str:
        """Build Postgres connection URL from Supabase config."""
        # Supabase URL format: https://project-ref.supabase.co
        # Postgres format: postgres://postgres.project-ref:password@pooler.supabase.com:6543/postgres
        url = self._config.supabase_url
        key = self._config.supabase_key.get_secret_value()

        # Extract project ref from URL
        if "supabase.co" in url:
            # Remove https:// prefix
            host = url.replace("https://", "").replace("http://", "")
            # Convert to db host
            project_ref = host.split(".")[0]

            # Use EU central region pooler for IPv4 compatibility
            # Format: postgres://postgres.PROJECT_REF:PASSWORD@REGION.pooler.supabase.com:6543/postgres
            pooler_region = "aws-1-eu-central-1"  # EU region
            return f"postgres://postgres.{project_ref}:{key}@{pooler_region}.pooler.supabase.com:6543/postgres"

        # Fallback: assume it's already a postgres URL
        return url

    async def _ensure_fallback_tables(self, conn: "asyncpg.Connection") -> None:
        """Create fallback tables if vault extension is not available."""
        await conn.execute("""
            CREATE SCHEMA IF NOT EXISTS casare_vault;

            CREATE TABLE IF NOT EXISTS casare_vault.secrets (
                id SERIAL PRIMARY KEY,
                path TEXT UNIQUE NOT NULL,
                data JSONB NOT NULL,
                credential_type TEXT DEFAULT 'custom',
                description TEXT,
                metadata JSONB DEFAULT '{}',
                version INTEGER DEFAULT 1,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS idx_secrets_path
            ON casare_vault.secrets (path);
        """)
        logger.info("Created fallback vault tables")

    async def get_secret(self, path: str, version: int | None = None) -> SecretValue:
        """Get secret from Supabase Vault."""
        pool = self._ensure_pool()

        async with pool.acquire() as conn:
            # Try native vault first, then fallback
            try:
                # Native Supabase Vault query
                row = await conn.fetchrow(
                    """
                    SELECT
                        name,
                        decrypted_secret,
                        description,
                        created_at,
                        updated_at
                    FROM vault.decrypted_secrets
                    WHERE name = $1
                    """,
                    path,
                )

                if row:
                    # Parse the decrypted secret (stored as text)
                    import json

                    try:
                        data = json.loads(row["decrypted_secret"])
                    except (json.JSONDecodeError, TypeError):
                        # Plain text secret
                        data = {"value": row["decrypted_secret"]}

                    metadata = SecretMetadata(
                        path=path,
                        version=1,
                        created_at=row["created_at"] or datetime.now(UTC),
                        updated_at=row["updated_at"] or datetime.now(UTC),
                        credential_type=self._infer_credential_type(data),
                    )

                    return SecretValue(data=data, metadata=metadata)

            except asyncpg.UndefinedTableError:
                # Vault extension not available, use fallback
                pass

            # Fallback table query
            row = await conn.fetchrow(
                """
                SELECT
                    path,
                    data,
                    credential_type,
                    description,
                    metadata,
                    version,
                    created_at,
                    updated_at
                FROM casare_vault.secrets
                WHERE path = $1
                """,
                path,
            )

            if not row:
                raise SecretNotFoundError(f"Secret not found: {path}", path=path)

            import json

            data = json.loads(row["data"]) if isinstance(row["data"], str) else dict(row["data"])

            custom_metadata = (
                json.loads(row["metadata"])
                if isinstance(row["metadata"], str)
                else dict(row["metadata"] or {})
            )

            metadata = SecretMetadata(
                path=path,
                version=row["version"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                credential_type=CredentialType(row["credential_type"]),
                custom_metadata=custom_metadata,
            )

            return SecretValue(data=data, metadata=metadata)

    async def put_secret(
        self,
        path: str,
        data: dict[str, Any],
        credential_type: CredentialType = CredentialType.CUSTOM_KIND,
        metadata: dict[str, Any] | None = None,
    ) -> SecretMetadata:
        """Store secret in Supabase Vault."""
        pool = self._ensure_pool()
        import json

        async with pool.acquire() as conn:
            # Try native vault first
            try:
                # Check if secret exists
                existing = await conn.fetchval(
                    "SELECT id FROM vault.secrets WHERE name = $1",
                    path,
                )

                secret_value = json.dumps(data)
                description = (metadata or {}).get("description", "")

                if existing:
                    # Update existing secret
                    await conn.execute(
                        """
                        UPDATE vault.secrets
                        SET secret = $2, description = $3, updated_at = NOW()
                        WHERE name = $1
                        """,
                        path,
                        secret_value,
                        description,
                    )
                else:
                    # Insert new secret
                    await conn.execute(
                        """
                        INSERT INTO vault.secrets (name, secret, description)
                        VALUES ($1, $2, $3)
                        """,
                        path,
                        secret_value,
                        description,
                    )

                return SecretMetadata(
                    path=path,
                    version=1,
                    credential_type=credential_type,
                    custom_metadata=metadata or {},
                )

            except asyncpg.UndefinedTableError:
                # Fallback to custom tables
                pass

            # Fallback storage
            result = await conn.fetchrow(
                """
                INSERT INTO casare_vault.secrets
                    (path, data, credential_type, description, metadata, version)
                VALUES ($1, $2, $3, $4, $5, 1)
                ON CONFLICT (path) DO UPDATE SET
                    data = EXCLUDED.data,
                    credential_type = EXCLUDED.credential_type,
                    description = EXCLUDED.description,
                    metadata = EXCLUDED.metadata,
                    version = casare_vault.secrets.version + 1,
                    updated_at = NOW()
                RETURNING version, created_at, updated_at
                """,
                path,
                json.dumps(data),
                credential_type.value,
                (metadata or {}).get("description", ""),
                json.dumps(metadata or {}),
            )

            return SecretMetadata(
                path=path,
                version=result["version"],
                created_at=result["created_at"],
                updated_at=result["updated_at"],
                credential_type=credential_type,
                custom_metadata=metadata or {},
            )

    async def delete_secret(self, path: str) -> bool:
        """Delete secret from Supabase Vault."""
        pool = self._ensure_pool()

        async with pool.acquire() as conn:
            # Try native vault first
            try:
                result = await conn.execute(
                    "DELETE FROM vault.secrets WHERE name = $1",
                    path,
                )
                if result != "DELETE 0":
                    logger.info(f"Deleted secret from native vault: {path}")
                    return True
            except asyncpg.UndefinedTableError:
                pass

            # Fallback
            result = await conn.execute(
                "DELETE FROM casare_vault.secrets WHERE path = $1",
                path,
            )

            deleted = result != "DELETE 0"
            if deleted:
                logger.info(f"Deleted secret: {path}")
            return deleted

    async def list_secrets(self, path_prefix: str) -> list[str]:
        """List secrets under a path prefix."""
        pool = self._ensure_pool()

        async with pool.acquire() as conn:
            # Try native vault first
            try:
                rows = await conn.fetch(
                    """
                    SELECT name FROM vault.secrets
                    WHERE name LIKE $1 || '%'
                    ORDER BY name
                    """,
                    path_prefix,
                )
                if rows:
                    return [row["name"] for row in rows]
            except asyncpg.UndefinedTableError:
                pass

            # Fallback
            rows = await conn.fetch(
                """
                SELECT path FROM casare_vault.secrets
                WHERE path LIKE $1 || '%'
                ORDER BY path
                """,
                path_prefix,
            )

            return [row["path"] for row in rows]

    async def rotate_secret(self, path: str) -> SecretMetadata:
        """
        Rotate a secret by generating new random values.

        For password-type secrets, generates a new secure password.
        For API keys, generates a new random key.

        Args:
            path: Secret path to rotate

        Returns:
            SecretMetadata for the new secret version
        """
        # Get current secret to understand its structure
        current = await self.get_secret(path)

        # Generate new values based on credential type
        new_data = self._generate_rotated_values(current.data, current.metadata.credential_type)

        # Store with incremented version
        return await self.put_secret(
            path=path,
            data=new_data,
            credential_type=current.metadata.credential_type,
            metadata=current.metadata.custom_metadata,
        )

    def _generate_rotated_values(
        self, current_data: dict[str, Any], cred_type: CredentialType
    ) -> dict[str, Any]:
        """Generate new secret values based on type."""
        import secrets as secrets_module

        new_data = current_data.copy()

        if cred_type == CredentialType.USER_PASS_KIND:
            # Generate new password, keep username
            new_data["password"] = self._generate_password()

        elif cred_type == CredentialType.API_KEY_KIND:
            # Generate new API key
            for key in ["api_key", "apikey", "key", "token"]:
                if key in new_data:
                    new_data[key] = secrets_module.token_urlsafe(32)
                    break
            else:
                new_data["api_key"] = secrets_module.token_urlsafe(32)

        elif cred_type == CredentialType.OAUTH2_TOKEN_KIND:
            # Can't rotate OAuth tokens automatically
            logger.warning(
                "OAuth2 tokens cannot be rotated automatically. " "Re-authentication required."
            )

        else:
            # For custom types, try to rotate common password fields
            for key in ["password", "secret", "key"]:
                if key in new_data:
                    new_data[key] = self._generate_password()

        return new_data

    def _generate_password(self, length: int = 32) -> str:
        """Generate a secure random password."""
        import secrets as secrets_module

        # Mix of letters, digits, and special chars
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        return "".join(secrets_module.choice(alphabet) for _ in range(length))

    def _infer_credential_type(self, data: dict[str, Any]) -> CredentialType:
        """Infer credential type from data keys."""
        keys = set(data.keys())

        if "username" in keys and "password" in keys:
            return CredentialType.USER_PASS_KIND
        if "api_key" in keys or "apikey" in keys:
            return CredentialType.API_KEY_KIND
        if "access_token" in keys:
            return CredentialType.OAUTH2_TOKEN_KIND
        if "private_key" in keys:
            return CredentialType.SSH_KEY
        if "connection_string" in keys:
            return CredentialType.DATABASE_CONNECTION

        return CredentialType.CUSTOM_KIND
