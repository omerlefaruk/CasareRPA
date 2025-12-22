"""
CasareRPA - Unified Credential Store

Encrypted storage for all credential types:
- API Keys (LLM providers, services)
- Username/Password pairs (databases, applications)
- Connection strings
- Custom secrets

Uses Fernet encryption (AES-128-CBC) with DPAPI protection on Windows.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from loguru import logger

from casare_rpa.config.security_config import get_crypto_security_config


class CredentialType(Enum):
    """Types of credentials."""

    API_KEY = "api_key"
    USERNAME_PASSWORD = "username_password"
    CONNECTION_STRING = "connection_string"
    OAUTH_TOKEN = "oauth_token"
    GOOGLE_OAUTH = "google_oauth"
    OPENAI_OAUTH = "openai_oauth"
    CUSTOM = "custom"


@dataclass
class Credential:
    """Represents a stored credential."""

    id: str  # Unique identifier
    name: str  # Display name
    credential_type: CredentialType
    category: str  # e.g., "llm", "database", "email", "custom"
    encrypted_data: str  # Base64 encoded encrypted JSON
    description: str = ""
    created_at: str = ""
    updated_at: str = ""
    last_used: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "credential_type": self.credential_type.value,
            "category": self.category,
            "encrypted_data": self.encrypted_data,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_used": self.last_used,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Credential":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            credential_type=CredentialType(data["credential_type"]),
            category=data["category"],
            encrypted_data=data["encrypted_data"],
            description=data.get("description", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            last_used=data.get("last_used"),
            tags=data.get("tags", []),
        )


# Predefined categories with their credential types and fields
CREDENTIAL_CATEGORIES = {
    "llm": {
        "name": "LLM Providers",
        "type": CredentialType.API_KEY,
        "providers": [
            "openai",
            "anthropic",
            "azure",
            "google",
            "mistral",
            "cohere",
            "groq",
            "together",
            "perplexity",
            "deepseek",
            "openrouter",
        ],
        "fields": ["api_key"],
        "env_vars": {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "azure": "AZURE_OPENAI_API_KEY",
            "google": "GOOGLE_API_KEY",
            "mistral": "MISTRAL_API_KEY",
            "cohere": "COHERE_API_KEY",
            "groq": "GROQ_API_KEY",
            "together": "TOGETHER_API_KEY",
            "perplexity": "PERPLEXITY_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
        },
    },
    "database": {
        "name": "Database",
        "type": CredentialType.USERNAME_PASSWORD,
        "providers": ["postgresql", "mysql", "sqlserver", "oracle", "mongodb", "redis"],
        "fields": ["username", "password", "host", "port", "database"],
    },
    "email": {
        "name": "Email",
        "type": CredentialType.USERNAME_PASSWORD,
        "providers": ["smtp", "imap", "outlook", "gmail"],
        "fields": ["username", "password", "server", "port"],
    },
    "cloud": {
        "name": "Cloud Services",
        "type": CredentialType.API_KEY,
        "providers": ["aws", "azure", "gcp", "digitalocean"],
        "fields": ["api_key", "secret_key", "region"],
    },
    "custom": {
        "name": "Custom",
        "type": CredentialType.CUSTOM,
        "providers": [],
        "fields": [],
    },
    "google": {
        "name": "Google Workspace",
        "type": CredentialType.GOOGLE_OAUTH,
        "providers": [
            "google_workspace",
            "gmail",
            "drive",
            "sheets",
            "docs",
            "calendar",
        ],
        "fields": [
            "client_id",
            "client_secret",
            "access_token",
            "refresh_token",
            "token_expiry",
            "scopes",
        ],
        "auto_refresh": True,
    },
    "openai_oauth": {
        "name": "OpenAI / Azure OAuth",
        "type": CredentialType.OPENAI_OAUTH,
        "providers": [
            "openai",
            "azure_openai",
        ],
        "fields": [
            "client_id",
            "client_secret",
            "authorization_url",
            "token_url",
            "access_token",
            "refresh_token",
            "token_expiry",
            "scopes",
        ],
        "auto_refresh": True,
    },
}


class CredentialStore:
    """
    Unified credential store with encryption at rest.

    Features:
    - Multiple credential types (API keys, username/password, etc.)
    - Categorized storage
    - AES-128-CBC encryption via Fernet
    - Machine-specific master key (DPAPI on Windows)
    - Named credentials for easy reference in workflows
    """

    SERVICE_NAME = "CasareRPA"
    STORE_FILENAME = "credentials.enc"

    def __init__(self, store_path: Optional[Path] = None) -> None:
        """Initialize the credential store."""
        self._store_path = store_path or self._get_default_store_path()
        self._fernet: Optional[Fernet] = None
        self._credentials: Dict[str, Credential] = {}
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._initialized = False

    def _get_default_store_path(self) -> Path:
        """Get the default store path in user's app data."""
        if sys.platform == "win32":
            base = Path(os.environ.get("LOCALAPPDATA", "~"))
        elif sys.platform == "darwin":
            base = Path("~/Library/Application Support")
        else:
            base = Path(os.environ.get("XDG_DATA_HOME", "~/.local/share"))

        store_dir = base.expanduser() / "CasareRPA" / "credentials"
        store_dir.mkdir(parents=True, exist_ok=True)
        return store_dir / self.STORE_FILENAME

    def _get_master_key(self) -> bytes:
        """Get or create the master encryption key."""
        # Use different key file name to avoid conflict with legacy api_key_store
        key_file = self._store_path.parent / ".credential_master_key"

        if key_file.exists():
            encrypted_key = key_file.read_bytes()
            try:
                return self._unprotect_key(encrypted_key)
            except Exception as e:
                # Key file corrupted, regenerate
                logger.warning(f"Master key corrupted, regenerating: {e}")
                key_file.unlink()

        raw_key = Fernet.generate_key()
        protected_key = self._protect_key(raw_key)

        key_file.write_bytes(protected_key)
        if sys.platform != "win32":
            os.chmod(key_file, 0o600)

        logger.info("Generated new master encryption key for credential store")
        return raw_key

    def _protect_key(self, key: bytes) -> bytes:
        """Protect the master key using platform-specific encryption."""
        if sys.platform == "win32":
            try:
                import win32crypt

                return win32crypt.CryptProtectData(key, "CasareRPA Master Key", None, None, None, 0)
            except ImportError:
                pass

        machine_id = self._get_machine_identifier()
        salt = hashlib.sha256(machine_id.encode()).digest()[:16]
        crypto_config = get_crypto_security_config()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=crypto_config.pbkdf2_iterations,
        )
        derived_key = base64.urlsafe_b64encode(kdf.derive(machine_id.encode()))
        fernet = Fernet(derived_key)
        return fernet.encrypt(key)

    def _unprotect_key(self, protected_key: bytes) -> bytes:
        """Unprotect the master key."""
        if sys.platform == "win32":
            try:
                import win32crypt

                _, key = win32crypt.CryptUnprotectData(protected_key, None, None, None, 0)
                return key
            except ImportError:
                pass

        machine_id = self._get_machine_identifier()
        salt = hashlib.sha256(machine_id.encode()).digest()[:16]
        crypto_config = get_crypto_security_config()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=crypto_config.pbkdf2_iterations,
        )
        derived_key = base64.urlsafe_b64encode(kdf.derive(machine_id.encode()))
        fernet = Fernet(derived_key)
        return fernet.decrypt(protected_key)

    def _get_machine_identifier(self) -> str:
        """Get a machine-specific identifier."""
        import platform
        import uuid

        parts = [
            platform.node(),
            str(uuid.getnode()),
            platform.machine(),
        ]

        if sys.platform == "win32":
            try:
                import winreg

                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\Cryptography",
                )
                machine_guid, _ = winreg.QueryValueEx(key, "MachineGuid")
                parts.append(machine_guid)
                winreg.CloseKey(key)
            except Exception:
                pass

        return "|".join(parts)

    def _ensure_initialized(self) -> None:
        """Initialize encryption and load existing credentials."""
        if self._initialized:
            return

        master_key = self._get_master_key()
        self._fernet = Fernet(master_key)
        self._load_store()
        self._initialized = True

    def _load_store(self) -> None:
        """Load encrypted store from disk."""
        if not self._store_path.exists():
            self._credentials = {}
            return

        try:
            encrypted_data = self._store_path.read_bytes()
            decrypted_data = self._fernet.decrypt(encrypted_data)
            store_data = json.loads(decrypted_data.decode("utf-8"))

            self._credentials = {
                cred_id: Credential.from_dict(cred_data)
                for cred_id, cred_data in store_data.get("credentials", {}).items()
            }
            logger.debug(f"Loaded {len(self._credentials)} credentials")

        except InvalidToken:
            # Store encrypted with different key - start fresh
            logger.warning("Credential store encrypted with different key, starting fresh")
            self._credentials = {}
            # Remove corrupted file
            try:
                self._store_path.unlink()
            except Exception:
                pass
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse credential store: {e}")
            self._credentials = {}

    def _save_store(self) -> None:
        """Save encrypted store to disk."""
        store_data = {
            "version": 2,
            "credentials": {cred_id: cred.to_dict() for cred_id, cred in self._credentials.items()},
        }

        json_data = json.dumps(store_data, indent=2).encode("utf-8")
        encrypted_data = self._fernet.encrypt(json_data)
        self._store_path.write_bytes(encrypted_data)
        logger.debug("Saved credential store")

    def _encrypt_data(self, data: Dict[str, Any]) -> str:
        """Encrypt credential data."""
        json_str = json.dumps(data).encode("utf-8")
        encrypted = self._fernet.encrypt(json_str)
        return base64.b64encode(encrypted).decode("ascii")

    def _decrypt_data(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt credential data."""
        encrypted = base64.b64decode(encrypted_data)
        decrypted = self._fernet.decrypt(encrypted)
        return json.loads(decrypted.decode("utf-8"))

    def _generate_id(self) -> str:
        """Generate a unique credential ID."""
        import uuid

        return f"cred_{uuid.uuid4().hex[:12]}"

    # =========================================================================
    # Public API
    # =========================================================================

    def save_credential(
        self,
        name: str,
        credential_type: CredentialType,
        category: str,
        data: Dict[str, Any],
        description: str = "",
        tags: Optional[List[str]] = None,
        credential_id: Optional[str] = None,
    ) -> str:
        """
        Save a credential securely.

        Args:
            name: Display name for the credential
            credential_type: Type of credential
            category: Category (llm, database, email, etc.)
            data: Credential data to encrypt (e.g., {"api_key": "sk-..."})
            description: Optional description
            tags: Optional tags for organization
            credential_id: Optional ID for updating existing credential

        Returns:
            Credential ID
        """
        self._ensure_initialized()

        now = datetime.now(timezone.utc).isoformat()
        cred_id = credential_id or self._generate_id()

        # Check if updating existing
        existing = self._credentials.get(cred_id)
        created_at = existing.created_at if existing else now

        credential = Credential(
            id=cred_id,
            name=name,
            credential_type=credential_type,
            category=category,
            encrypted_data=self._encrypt_data(data),
            description=description,
            created_at=created_at,
            updated_at=now,
            tags=tags or [],
        )

        self._credentials[cred_id] = credential
        self._cache.pop(cred_id, None)
        self._save_store()

        logger.info(f"Saved credential: {name} ({category})")
        return cred_id

    def get_credential(self, credential_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve decrypted credential data.

        Args:
            credential_id: Credential ID

        Returns:
            Decrypted credential data or None
        """
        self._ensure_initialized()

        # Check cache
        if credential_id in self._cache:
            return self._cache[credential_id]

        credential = self._credentials.get(credential_id)
        if not credential:
            return None

        try:
            data = self._decrypt_data(credential.encrypted_data)

            # Update last used timestamp in memory only (don't block with file I/O)
            # The timestamp will be persisted on next explicit save operation
            credential.last_used = datetime.now(timezone.utc).isoformat()
            # NOTE: Removed _save_store() call here to prevent blocking the event loop
            # during async workflow execution (e.g., Gmail sends). The last_used
            # timestamp is informational and not critical for functionality.

            # Cache
            self._cache[credential_id] = data
            return data

        except (InvalidToken, Exception) as e:
            logger.error(f"Failed to decrypt credential {credential_id}: {e}")
            return None

    def get_credential_info(self, credential_id: str) -> Optional[Dict[str, Any]]:
        """Get credential metadata without decrypting."""
        self._ensure_initialized()

        credential = self._credentials.get(credential_id)
        if not credential:
            return None

        return {
            "id": credential.id,
            "name": credential.name,
            "type": credential.credential_type.value,
            "category": credential.category,
            "description": credential.description,
            "created_at": credential.created_at,
            "updated_at": credential.updated_at,
            "last_used": credential.last_used,
            "tags": credential.tags,
        }

    def delete_credential(self, credential_id: str) -> bool:
        """Delete a credential."""
        self._ensure_initialized()

        if credential_id in self._credentials:
            name = self._credentials[credential_id].name
            del self._credentials[credential_id]
            self._cache.pop(credential_id, None)
            self._save_store()
            logger.info(f"Deleted credential: {name}")
            return True
        return False

    def list_credentials(
        self,
        category: Optional[str] = None,
        credential_type: Optional[CredentialType] = None,
    ) -> List[Dict[str, Any]]:
        """List all credentials (metadata only)."""
        self._ensure_initialized()

        results = []
        for cred in self._credentials.values():
            if category and cred.category != category:
                continue
            if credential_type and cred.credential_type != credential_type:
                continue

            results.append(
                {
                    "id": cred.id,
                    "name": cred.name,
                    "type": cred.credential_type.value,
                    "category": cred.category,
                    "description": cred.description,
                    "created_at": cred.created_at,
                    "last_used": cred.last_used,
                    "tags": cred.tags,
                }
            )

        return sorted(results, key=lambda x: x["name"].lower())

    def get_credentials_for_dropdown(self, category: Optional[str] = None) -> List[tuple[str, str]]:
        """Get credentials formatted for dropdown: [(id, display_name), ...]"""
        self._ensure_initialized()

        results = []
        for cred in self._credentials.values():
            if category and cred.category != category:
                continue
            results.append((cred.id, f"{cred.name} ({cred.category})"))

        return sorted(results, key=lambda x: x[1].lower())

    def search_credentials(self, query: str) -> List[Dict[str, Any]]:
        """Search credentials by name, description, or tags."""
        self._ensure_initialized()

        query_lower = query.lower()
        results = []

        for cred in self._credentials.values():
            if (
                query_lower in cred.name.lower()
                or query_lower in cred.description.lower()
                or any(query_lower in tag.lower() for tag in cred.tags)
            ):
                results.append(self.get_credential_info(cred.id))

        return results

    def rename_credential(self, credential_id: str, new_name: str) -> bool:
        """Rename a credential."""
        self._ensure_initialized()

        if credential_id in self._credentials:
            self._credentials[credential_id].name = new_name
            self._credentials[credential_id].updated_at = datetime.now(timezone.utc).isoformat()
            self._save_store()
            return True
        return False

    def clear_cache(self) -> None:
        """Clear the in-memory cache."""
        self._cache.clear()

    # =========================================================================
    # Convenience methods for specific credential types
    # =========================================================================

    def save_api_key(
        self,
        name: str,
        provider: str,
        api_key: str,
        description: str = "",
    ) -> str:
        """Save an API key credential."""
        return self.save_credential(
            name=name,
            credential_type=CredentialType.API_KEY,
            category="llm",
            data={"api_key": api_key, "provider": provider},
            description=description,
            tags=[provider],
        )

    def save_username_password(
        self,
        name: str,
        category: str,
        username: str,
        password: str,
        extra_fields: Optional[Dict[str, str]] = None,
        description: str = "",
    ) -> str:
        """Save a username/password credential."""
        data = {"username": username, "password": password}
        if extra_fields:
            data.update(extra_fields)

        return self.save_credential(
            name=name,
            credential_type=CredentialType.USERNAME_PASSWORD,
            category=category,
            data=data,
            description=description,
        )

    def get_api_key(self, credential_id: str) -> Optional[str]:
        """Get API key from credential."""
        data = self.get_credential(credential_id)
        if data:
            return data.get("api_key")
        return None

    def get_api_key_by_provider(self, provider: str) -> Optional[str]:
        """Get first API key for a provider."""
        for cred in self._credentials.values():
            if cred.category == "llm":
                data = self.get_credential(cred.id)
                if data and data.get("provider") == provider:
                    return data.get("api_key")

        # Fallback to environment
        env_vars = CREDENTIAL_CATEGORIES["llm"].get("env_vars", {})
        env_var = env_vars.get(provider)
        if env_var:
            return os.environ.get(env_var)

        return None

    def save_google_oauth(
        self,
        name: str,
        client_id: str,
        client_secret: str,
        access_token: str,
        refresh_token: str,
        scopes: List[str],
        token_expiry: Optional[str] = None,
        user_email: Optional[str] = None,
        project_id: Optional[str] = None,
        description: str = "",
        credential_id: Optional[str] = None,
    ) -> str:
        """
        Save a Google OAuth credential.

        Args:
            name: Display name for the credential
            client_id: OAuth 2.0 client ID from Google Cloud Console
            client_secret: OAuth 2.0 client secret
            access_token: Current access token
            refresh_token: Refresh token for obtaining new access tokens
            scopes: List of OAuth scopes granted
            token_expiry: ISO format datetime string when token expires
            user_email: Email of authenticated user (optional)
            project_id: Google Cloud project ID (optional)
            description: Optional description
            credential_id: Optional ID for updating existing credential

        Returns:
            Credential ID
        """
        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "scopes": scopes,
        }

        if token_expiry:
            data["token_expiry"] = token_expiry

        if user_email:
            data["user_email"] = user_email

        if project_id:
            data["project_id"] = project_id

        # Determine provider from scopes
        provider = "google_workspace"
        scope_str = " ".join(scopes).lower()
        if "gmail" in scope_str:
            provider = "gmail"
        elif "sheets" in scope_str or "spreadsheets" in scope_str:
            provider = "sheets"
        elif "drive" in scope_str:
            provider = "drive"
        elif "docs" in scope_str or "documents" in scope_str:
            provider = "docs"
        elif "calendar" in scope_str:
            provider = "calendar"

        return self.save_credential(
            name=name,
            credential_type=CredentialType.GOOGLE_OAUTH,
            category="google",
            data=data,
            description=description,
            tags=[provider, "oauth"],
            credential_id=credential_id,
        )

    def list_google_credentials(self) -> List[Dict[str, Any]]:
        """
        List all Google OAuth credentials.

        Returns:
            List of credential metadata dictionaries.
        """
        return self.list_credentials(
            category="google",
            credential_type=CredentialType.GOOGLE_OAUTH,
        )

    def save_openai_oauth(
        self,
        name: str,
        client_id: str,
        client_secret: str,
        authorization_url: str,
        token_url: str,
        access_token: str,
        refresh_token: str,
        scopes: List[str],
        token_expiry: Optional[str] = None,
        tenant_id: Optional[str] = None,
        description: str = "",
        credential_id: Optional[str] = None,
    ) -> str:
        """
        Save an OpenAI/Azure OAuth credential.

        Args:
            name: Display name
            client_id: Client ID
            client_secret: Client Secret
            authorization_url: Auth URL
            token_url: Token URL
            access_token: Access Token
            refresh_token: Refresh Token
            scopes: Scopes
            token_expiry: Expiry
            tenant_id: Azure Tenant ID (optional)
            description: Description
            credential_id: Update ID

        Returns:
            Credential ID
        """
        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "authorization_url": authorization_url,
            "token_url": token_url,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "scopes": scopes,
        }

        if token_expiry:
            data["token_expiry"] = token_expiry

        if tenant_id:
            data["tenant_id"] = tenant_id

        return self.save_credential(
            name=name,
            credential_type=CredentialType.OPENAI_OAUTH,
            category="openai_oauth",
            data=data,
            description=description,
            tags=["openai", "azure", "oauth"],
            credential_id=credential_id,
        )

    def list_openai_credentials(self) -> List[Dict[str, Any]]:
        """List all OpenAI OAuth credentials."""
        return self.list_credentials(
            category="openai_oauth",
            credential_type=CredentialType.OPENAI_OAUTH,
        )

    def get_google_credential_for_dropdown(self) -> List[tuple[str, str]]:
        """
        Get Google credentials formatted for dropdown: [(id, display_name), ...]

        The display name includes the user email if available.
        """
        self._ensure_initialized()

        results = []
        for cred in self._credentials.values():
            if cred.category == "google":
                # Try to get user email for display
                display_name = cred.name
                try:
                    data = self.get_credential(cred.id)
                    if data and data.get("user_email"):
                        display_name = f"{cred.name} ({data['user_email']})"
                except Exception:
                    pass
                results.append((cred.id, display_name))

        return sorted(results, key=lambda x: x[1].lower())


# Global instance
_default_store: Optional[CredentialStore] = None


def get_credential_store() -> CredentialStore:
    """Get the global credential store instance."""
    global _default_store
    if _default_store is None:
        _default_store = CredentialStore()
    return _default_store


__all__ = [
    "CredentialStore",
    "Credential",
    "CredentialType",
    "CREDENTIAL_CATEGORIES",
    "get_credential_store",
]
