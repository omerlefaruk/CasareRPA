"""
Encrypted SQLite Vault Provider Implementation.

Development-friendly local vault using SQLite with AES-256 encryption.
Suitable for:
- Local development without external vault dependencies
- Testing and CI/CD environments
- Offline operation
- Small deployments

Encryption uses Fernet (AES-128-CBC with HMAC) from cryptography library.
"""

import base64
import hashlib
import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from casare_rpa.infrastructure.security.vault_client import (
    VaultProvider,
    VaultConfig,
    SecretValue,
    SecretMetadata,
    CredentialType,
    SecretNotFoundError,
    VaultConnectionError,
)

# Optional aiosqlite import
try:
    import aiosqlite

    AIOSQLITE_AVAILABLE = True
except ImportError:
    AIOSQLITE_AVAILABLE = False
    aiosqlite = None

# Optional cryptography import
try:
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    Fernet = None
    InvalidToken = Exception


class EncryptedSQLiteProvider(VaultProvider):
    """
    Local encrypted SQLite vault for development and testing.

    Secrets are encrypted at rest using AES via the Fernet scheme.
    The encryption key is derived from a master password using PBKDF2.

    Database schema:
    - secrets: Stores encrypted secret data with versioning
    - metadata: Stores secret metadata (unencrypted)
    """

    # Salt for key derivation (should be unique per installation)
    DEFAULT_SALT = b"casare_rpa_vault_salt_v1"

    def __init__(self, config: VaultConfig) -> None:
        """
        Initialize SQLite vault provider.

        Args:
            config: Vault configuration with SQLite settings
        """
        if not AIOSQLITE_AVAILABLE:
            raise ImportError(
                "SQLite vault support requires aiosqlite library. "
                "Install with: pip install aiosqlite"
            )

        self._config = config
        self._db_path = Path(config.sqlite_path)
        self._conn: Optional["aiosqlite.Connection"] = None
        self._fernet: Optional["Fernet"] = None

    async def connect(self) -> None:
        """Initialize SQLite database and encryption."""
        try:
            # Ensure directory exists
            self._db_path.parent.mkdir(parents=True, exist_ok=True)

            # Derive encryption key
            self._fernet = self._create_fernet()

            # Connect to database
            self._conn = await aiosqlite.connect(str(self._db_path))
            self._conn.row_factory = aiosqlite.Row

            # Enable WAL mode for better concurrency
            await self._conn.execute("PRAGMA journal_mode=WAL")
            await self._conn.execute("PRAGMA foreign_keys=ON")

            # Create schema
            await self._create_schema()

            logger.info(f"Connected to SQLite vault at {self._db_path}")

        except Exception as e:
            raise VaultConnectionError(f"Failed to initialize SQLite vault: {e}") from e

    async def disconnect(self) -> None:
        """Close SQLite connection."""
        if self._conn:
            await self._conn.close()
            self._conn = None
            self._fernet = None
            logger.info("Disconnected from SQLite vault")

    async def is_connected(self) -> bool:
        """Check if database is connected."""
        if not self._conn:
            return False
        try:
            await self._conn.execute("SELECT 1")
            return True
        except Exception:
            return False

    def _create_fernet(self) -> "Fernet":
        """Create Fernet instance for encryption/decryption."""
        if not CRYPTOGRAPHY_AVAILABLE:
            raise ImportError(
                "Encryption requires cryptography library. "
                "Install with: pip install cryptography"
            )

        # Get or generate encryption key
        if self._config.sqlite_encryption_key:
            password = self._config.sqlite_encryption_key.get_secret_value().encode()
        else:
            # Generate a default key (NOT SECURE for production)
            logger.warning(
                "No encryption key configured for SQLite vault. "
                "Using machine-specific default. "
                "Set CASARE_VAULT_KEY for production use."
            )
            # Use a machine-specific identifier as password
            machine_id = self._get_machine_id()
            password = machine_id.encode()

        # Derive a proper key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.DEFAULT_SALT,
            iterations=480000,  # OWASP recommended minimum
        )

        key = base64.urlsafe_b64encode(kdf.derive(password))
        return Fernet(key)

    def _get_machine_id(self) -> str:
        """Get a machine-specific identifier for default key generation."""
        # Combine various machine identifiers
        identifiers = [
            os.environ.get("COMPUTERNAME", ""),
            os.environ.get("USERNAME", ""),
            str(Path.home()),
        ]
        combined = "|".join(identifiers)
        return hashlib.sha256(combined.encode()).hexdigest()

    async def _create_schema(self) -> None:
        """Create database schema if not exists."""
        await self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS secrets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE NOT NULL,
                encrypted_data BLOB NOT NULL,
                credential_type TEXT DEFAULT 'custom',
                version INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS secret_metadata (
                secret_id INTEGER PRIMARY KEY REFERENCES secrets(id) ON DELETE CASCADE,
                description TEXT,
                custom_metadata TEXT,
                expires_at TEXT,
                is_dynamic INTEGER DEFAULT 0
            );

            CREATE INDEX IF NOT EXISTS idx_secrets_path ON secrets(path);

            CREATE TABLE IF NOT EXISTS vault_config (
                key TEXT PRIMARY KEY,
                value TEXT
            );
        """)
        await self._conn.commit()

    def _ensure_connected(self) -> tuple["aiosqlite.Connection", "Fernet"]:
        """Ensure database is connected and return connection and fernet."""
        if not self._conn or not self._fernet:
            raise VaultConnectionError("Not connected to SQLite vault")
        return self._conn, self._fernet

    def _encrypt(self, data: Dict[str, Any]) -> bytes:
        """Encrypt secret data."""
        _, fernet = self._ensure_connected()
        json_data = json.dumps(data, default=str)
        return fernet.encrypt(json_data.encode())

    def _decrypt(self, encrypted: bytes) -> Dict[str, Any]:
        """Decrypt secret data."""
        _, fernet = self._ensure_connected()
        try:
            decrypted = fernet.decrypt(encrypted)
            return json.loads(decrypted.decode())
        except InvalidToken as e:
            raise VaultConnectionError(
                "Failed to decrypt secret. Invalid encryption key."
            ) from e

    async def get_secret(self, path: str, version: Optional[int] = None) -> SecretValue:
        """Get secret from SQLite vault."""
        conn, _ = self._ensure_connected()

        async with conn.execute(
            """
            SELECT
                s.id,
                s.path,
                s.encrypted_data,
                s.credential_type,
                s.version,
                s.created_at,
                s.updated_at,
                m.description,
                m.custom_metadata,
                m.expires_at,
                m.is_dynamic
            FROM secrets s
            LEFT JOIN secret_metadata m ON s.id = m.secret_id
            WHERE s.path = ?
            """,
            (path,),
        ) as cursor:
            row = await cursor.fetchone()

        if not row:
            raise SecretNotFoundError(f"Secret not found: {path}", path=path)

        # Decrypt the data
        data = self._decrypt(row["encrypted_data"])

        # Parse metadata
        custom_metadata = {}
        if row["custom_metadata"]:
            try:
                custom_metadata = json.loads(row["custom_metadata"])
            except json.JSONDecodeError:
                pass

        expires_at = None
        if row["expires_at"]:
            try:
                expires_at = datetime.fromisoformat(row["expires_at"])
            except ValueError:
                pass

        metadata = SecretMetadata(
            path=path,
            version=row["version"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            expires_at=expires_at,
            credential_type=CredentialType(row["credential_type"]),
            is_dynamic=bool(row["is_dynamic"]),
            custom_metadata=custom_metadata,
        )

        return SecretValue(data=data, metadata=metadata)

    async def put_secret(
        self,
        path: str,
        data: Dict[str, Any],
        credential_type: CredentialType = CredentialType.CUSTOM,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SecretMetadata:
        """Store secret in SQLite vault."""
        conn, _ = self._ensure_connected()

        now = datetime.now(timezone.utc).isoformat()
        encrypted = self._encrypt(data)

        # Check if secret exists
        async with conn.execute(
            "SELECT id, version FROM secrets WHERE path = ?",
            (path,),
        ) as cursor:
            existing = await cursor.fetchone()

        if existing:
            # Update existing secret
            new_version = existing["version"] + 1
            await conn.execute(
                """
                UPDATE secrets SET
                    encrypted_data = ?,
                    credential_type = ?,
                    version = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (encrypted, credential_type.value, new_version, now, existing["id"]),
            )
            secret_id = existing["id"]
        else:
            # Insert new secret
            cursor = await conn.execute(
                """
                INSERT INTO secrets (path, encrypted_data, credential_type, version, created_at, updated_at)
                VALUES (?, ?, ?, 1, ?, ?)
                """,
                (path, encrypted, credential_type.value, now, now),
            )
            secret_id = cursor.lastrowid
            new_version = 1

        # Upsert metadata
        description = (metadata or {}).get("description", "")
        custom_meta = json.dumps(metadata) if metadata else None
        expires_at = (metadata or {}).get("expires_at")

        await conn.execute(
            """
            INSERT INTO secret_metadata (secret_id, description, custom_metadata, expires_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(secret_id) DO UPDATE SET
                description = excluded.description,
                custom_metadata = excluded.custom_metadata,
                expires_at = excluded.expires_at
            """,
            (secret_id, description, custom_meta, expires_at),
        )

        await conn.commit()

        logger.debug(f"Stored secret at {path} (version {new_version})")

        return SecretMetadata(
            path=path,
            version=new_version,
            created_at=datetime.fromisoformat(now),
            updated_at=datetime.fromisoformat(now),
            credential_type=credential_type,
            custom_metadata=metadata or {},
        )

    async def delete_secret(self, path: str) -> bool:
        """Delete secret from SQLite vault."""
        conn, _ = self._ensure_connected()

        cursor = await conn.execute(
            "DELETE FROM secrets WHERE path = ?",
            (path,),
        )
        await conn.commit()

        deleted = cursor.rowcount > 0
        if deleted:
            logger.debug(f"Deleted secret: {path}")
        return deleted

    async def list_secrets(self, path_prefix: str) -> List[str]:
        """List secrets under a path prefix."""
        conn, _ = self._ensure_connected()

        # Ensure prefix ends with / for proper matching
        prefix = path_prefix.rstrip("/") + "/" if path_prefix else ""

        async with conn.execute(
            """
            SELECT path FROM secrets
            WHERE path LIKE ? || '%'
            ORDER BY path
            """,
            (prefix,),
        ) as cursor:
            rows = await cursor.fetchall()

        return [row["path"] for row in rows]

    async def rotate_secret(self, path: str) -> SecretMetadata:
        """
        Rotate a secret by generating new random values.

        For password-type secrets, generates a new secure password.
        For API keys, generates a new random key.
        """
        # Get current secret to understand its structure
        current = await self.get_secret(path)

        # Generate new values based on credential type
        new_data = self._generate_rotated_values(
            current.data, current.metadata.credential_type
        )

        # Store with incremented version
        return await self.put_secret(
            path=path,
            data=new_data,
            credential_type=current.metadata.credential_type,
            metadata=current.metadata.custom_metadata,
        )

    def _generate_rotated_values(
        self, current_data: Dict[str, Any], cred_type: CredentialType
    ) -> Dict[str, Any]:
        """Generate new secret values based on type."""
        new_data = current_data.copy()

        if cred_type == CredentialType.USERNAME_PASSWORD:
            # Generate new password, keep username
            new_data["password"] = self._generate_password()

        elif cred_type == CredentialType.API_KEY:
            # Generate new API key
            for key in ["api_key", "apikey", "key", "token"]:
                if key in new_data:
                    new_data[key] = self._generate_api_key()
                    break
            else:
                new_data["api_key"] = self._generate_api_key()

        elif cred_type == CredentialType.OAUTH2_TOKEN:
            # Can't rotate OAuth tokens automatically
            logger.warning(
                "OAuth2 tokens cannot be rotated automatically. "
                "Re-authentication required."
            )

        else:
            # For custom types, try to rotate common password fields
            for key in ["password", "secret", "key"]:
                if key in new_data:
                    new_data[key] = self._generate_password()

        return new_data

    def _generate_password(self, length: int = 32) -> str:
        """Generate a secure random password."""
        # Mix of letters, digits, and special chars
        alphabet = (
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        )
        return "".join(secrets.choice(alphabet) for _ in range(length))

    def _generate_api_key(self, length: int = 32) -> str:
        """Generate a secure random API key."""
        return secrets.token_urlsafe(length)


# Convenience function for quick local development setup
async def create_development_vault(
    path: str = ".casare/vault.db",
    encryption_key: Optional[str] = None,
) -> EncryptedSQLiteProvider:
    """
    Create a development vault with sensible defaults.

    Usage:
        vault = await create_development_vault()
        await vault.connect()

        # Store a secret
        await vault.put_secret(
            "my-app/db-creds",
            {"username": "admin", "password": "secret123"},
            CredentialType.USERNAME_PASSWORD,
        )

        # Retrieve it
        secret = await vault.get_secret("my-app/db-creds")
    """
    from pydantic import SecretStr

    config = VaultConfig(
        sqlite_path=path,
        sqlite_encryption_key=SecretStr(encryption_key) if encryption_key else None,
    )

    provider = EncryptedSQLiteProvider(config)
    await provider.connect()
    return provider
