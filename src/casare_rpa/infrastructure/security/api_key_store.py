"""
CasareRPA - Secure API Key Store

Encrypted storage for API keys using Fernet (AES-128-CBC).
Keys are encrypted at rest and protected by a machine-specific master key.

On Windows: Uses DPAPI for master key protection
On other OS: Falls back to file-based key with restricted permissions
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import sys
from dataclasses import dataclass
from datetime import UTC
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from loguru import logger

from casare_rpa.config.security_config import get_crypto_security_config


@dataclass
class APIKeyEntry:
    """Represents a stored API key."""

    provider: str  # e.g., "openai", "anthropic", "azure"
    key_name: str  # e.g., "default", "production"
    encrypted_key: str  # Base64 encoded encrypted key
    created_at: str
    last_used: str | None = None


class APIKeyStore:
    """
    Secure storage for API keys with encryption at rest.

    Features:
    - AES-128-CBC encryption via Fernet
    - Machine-specific master key (DPAPI on Windows)
    - JSON storage in user data directory
    - In-memory caching of decrypted keys

    Usage:
        store = APIKeyStore()
        store.set_key("openai", "sk-xxx...")
        key = store.get_key("openai")
    """

    SERVICE_NAME = "CasareRPA"
    STORE_FILENAME = "api_keys.enc"

    # Supported providers and their environment variable names
    PROVIDERS = {
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
    }

    def __init__(self, store_path: Path | None = None) -> None:
        """
        Initialize the API key store.

        Args:
            store_path: Custom path for the encrypted store file.
                       Defaults to user's app data directory.
        """
        self._store_path = store_path or self._get_default_store_path()
        self._fernet: Fernet | None = None
        self._cache: dict[str, str] = {}  # provider -> decrypted key
        self._entries: dict[str, APIKeyEntry] = {}
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
        """
        Get or create the master encryption key.

        On Windows: Uses DPAPI to protect the key
        On other OS: Uses a file-based key with restrictive permissions
        """
        key_file = self._store_path.parent / ".master_key"

        if key_file.exists():
            encrypted_key = key_file.read_bytes()
            return self._unprotect_key(encrypted_key)

        # Generate new key
        raw_key = Fernet.generate_key()
        protected_key = self._protect_key(raw_key)

        # Save with restrictive permissions
        key_file.write_bytes(protected_key)
        if sys.platform != "win32":
            os.chmod(key_file, 0o600)

        logger.info("Generated new master encryption key")
        return raw_key

    def _protect_key(self, key: bytes) -> bytes:
        """Protect the master key using platform-specific encryption."""
        if sys.platform == "win32":
            try:
                import win32crypt

                return win32crypt.CryptProtectData(
                    key,
                    "CasareRPA Master Key",
                    None,
                    None,
                    None,
                    0,
                )
            except ImportError:
                pass  # Fall through to file-based

        # Fallback: Use machine-specific derivation
        # This is less secure but works cross-platform
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

                _, key = win32crypt.CryptUnprotectData(
                    protected_key,
                    None,
                    None,
                    None,
                    0,
                )
                return key
            except ImportError:
                pass

        # Fallback decryption
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
        """Get a machine-specific identifier for key derivation."""
        import platform
        import uuid

        # Combine multiple identifiers for uniqueness
        parts = [
            platform.node(),  # Hostname
            str(uuid.getnode()),  # MAC address
            platform.machine(),  # Architecture
        ]

        # On Windows, try to get machine GUID
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
        """Initialize encryption and load existing keys."""
        if self._initialized:
            return

        master_key = self._get_master_key()
        self._fernet = Fernet(master_key)
        self._load_store()
        self._initialized = True

    def _load_store(self) -> None:
        """Load encrypted store from disk."""
        if not self._store_path.exists():
            self._entries = {}
            return

        try:
            encrypted_data = self._store_path.read_bytes()
            decrypted_data = self._fernet.decrypt(encrypted_data)
            store_data = json.loads(decrypted_data.decode("utf-8"))

            self._entries = {
                provider: APIKeyEntry(**entry)
                for provider, entry in store_data.get("keys", {}).items()
            }
            logger.debug(f"Loaded {len(self._entries)} API key entries")

        except (InvalidToken, json.JSONDecodeError) as e:
            logger.error(f"Failed to load API key store: {e}")
            self._entries = {}

    def _save_store(self) -> None:
        """Save encrypted store to disk."""
        store_data = {
            "version": 1,
            "keys": {
                provider: {
                    "provider": entry.provider,
                    "key_name": entry.key_name,
                    "encrypted_key": entry.encrypted_key,
                    "created_at": entry.created_at,
                    "last_used": entry.last_used,
                }
                for provider, entry in self._entries.items()
            },
        }

        json_data = json.dumps(store_data, indent=2).encode("utf-8")
        encrypted_data = self._fernet.encrypt(json_data)
        self._store_path.write_bytes(encrypted_data)
        logger.debug("Saved API key store")

    def set_key(
        self,
        provider: str,
        api_key: str,
        key_name: str = "default",
    ) -> None:
        """
        Store an API key securely.

        Args:
            provider: Provider name (e.g., "openai", "anthropic")
            api_key: The API key to store
            key_name: Optional key name for multiple keys per provider
        """
        self._ensure_initialized()

        from datetime import datetime

        # Encrypt the key
        encrypted = self._fernet.encrypt(api_key.encode("utf-8"))

        self._entries[provider] = APIKeyEntry(
            provider=provider,
            key_name=key_name,
            encrypted_key=base64.b64encode(encrypted).decode("ascii"),
            created_at=datetime.now(UTC).isoformat(),
        )

        # Clear cache
        self._cache.pop(provider, None)

        self._save_store()
        logger.info(f"Stored API key for provider: {provider}")

    def get_key(self, provider: str, check_env: bool = True) -> str | None:
        """
        Retrieve an API key.

        Args:
            provider: Provider name
            check_env: If True, also check environment variables

        Returns:
            Decrypted API key or None if not found
        """
        self._ensure_initialized()

        # Check cache first
        if provider in self._cache:
            return self._cache[provider]

        # Check stored keys
        if provider in self._entries:
            try:
                entry = self._entries[provider]
                encrypted = base64.b64decode(entry.encrypted_key)
                decrypted = self._fernet.decrypt(encrypted).decode("utf-8")

                # Update last used
                from datetime import datetime

                entry.last_used = datetime.now(UTC).isoformat()
                self._save_store()

                # Cache the decrypted key
                self._cache[provider] = decrypted
                return decrypted

            except (InvalidToken, Exception) as e:
                logger.error(f"Failed to decrypt key for {provider}: {e}")

        # Fallback to environment variable
        if check_env:
            env_var = self.PROVIDERS.get(provider)
            if env_var:
                env_key = os.environ.get(env_var)
                if env_key:
                    logger.debug(f"Using {provider} key from environment")
                    return env_key

        return None

    def delete_key(self, provider: str) -> bool:
        """
        Delete a stored API key.

        Args:
            provider: Provider name

        Returns:
            True if key was deleted
        """
        self._ensure_initialized()

        if provider in self._entries:
            del self._entries[provider]
            self._cache.pop(provider, None)
            self._save_store()
            logger.info(f"Deleted API key for provider: {provider}")
            return True

        return False

    def list_providers(self) -> list[str]:
        """Get list of providers with stored keys."""
        self._ensure_initialized()
        return list(self._entries.keys())

    def has_key(self, provider: str, check_env: bool = True) -> bool:
        """Check if a key exists for a provider."""
        self._ensure_initialized()

        if provider in self._entries:
            return True

        if check_env:
            env_var = self.PROVIDERS.get(provider)
            if env_var and os.environ.get(env_var):
                return True

        return False

    def clear_cache(self) -> None:
        """Clear the in-memory key cache."""
        self._cache.clear()

    def get_key_info(self, provider: str) -> dict | None:
        """Get metadata about a stored key (without the key itself)."""
        self._ensure_initialized()

        if provider in self._entries:
            entry = self._entries[provider]
            return {
                "provider": entry.provider,
                "key_name": entry.key_name,
                "created_at": entry.created_at,
                "last_used": entry.last_used,
                "source": "stored",
            }

        env_var = self.PROVIDERS.get(provider)
        if env_var and os.environ.get(env_var):
            return {
                "provider": provider,
                "key_name": "environment",
                "source": "environment",
                "env_var": env_var,
            }

        return None


# Global instance for convenience
_default_store: APIKeyStore | None = None


def get_api_key_store() -> APIKeyStore:
    """Get the global API key store instance."""
    global _default_store
    if _default_store is None:
        _default_store = APIKeyStore()
    return _default_store


def get_api_key(provider: str) -> str | None:
    """Convenience function to get an API key."""
    return get_api_key_store().get_key(provider)


def set_api_key(provider: str, api_key: str) -> None:
    """Convenience function to set an API key."""
    get_api_key_store().set_key(provider, api_key)


__all__ = [
    "APIKeyStore",
    "APIKeyEntry",
    "get_api_key_store",
    "get_api_key",
    "set_api_key",
]
