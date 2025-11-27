"""
Secrets Manager for CasareRPA.

This module provides secure handling of sensitive configuration values
such as API keys, database credentials, and other secrets.

Secrets are loaded from environment variables or a .env file,
but the .env file should NEVER be committed to version control.
"""

import os
from pathlib import Path
from typing import Dict, Optional
from loguru import logger


class SecretsManager:
    """
    Manages sensitive configuration values securely.

    Loads secrets from:
    1. Environment variables (highest priority)
    2. .env file in project root (if exists)
    3. .env.local file (for local overrides)

    Usage:
        secrets = SecretsManager()
        api_key = secrets.get("API_KEY")
        # Or with default:
        api_key = secrets.get("API_KEY", "default_value")
    """

    _instance: Optional["SecretsManager"] = None
    _initialized: bool = False

    def __new__(cls) -> "SecretsManager":
        """Singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize the secrets manager."""
        if SecretsManager._initialized:
            return

        self._secrets: Dict[str, str] = {}
        self._load_secrets()
        SecretsManager._initialized = True

    def _find_project_root(self) -> Path:
        """Find the project root directory by looking for common markers."""
        current = Path(__file__).resolve()

        # Walk up the directory tree looking for project markers
        for parent in [current] + list(current.parents):
            # Check for common project root markers
            if (parent / "pyproject.toml").exists():
                return parent
            if (parent / "setup.py").exists():
                return parent
            if (parent / ".git").exists():
                return parent
            if (parent / "requirements.txt").exists():
                return parent

        # Fallback to the src parent directory
        return Path(__file__).resolve().parent.parent.parent.parent

    def _load_env_file(self, env_path: Path) -> None:
        """
        Load environment variables from a .env file.

        Args:
            env_path: Path to the .env file
        """
        if not env_path.exists():
            return

        logger.debug(f"Loading secrets from {env_path}")

        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()

                    # Skip empty lines and comments
                    if not line or line.startswith("#"):
                        continue

                    # Parse KEY=VALUE format
                    if "=" not in line:
                        logger.warning(
                            f"Invalid line {line_num} in {env_path}: missing '='"
                        )
                        continue

                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip()

                    # Remove quotes if present
                    if (value.startswith('"') and value.endswith('"')) or (
                        value.startswith("'") and value.endswith("'")
                    ):
                        value = value[1:-1]

                    # Only set if not already in environment (env vars take priority)
                    if key not in os.environ:
                        self._secrets[key] = value

        except Exception as e:
            logger.error(f"Error loading {env_path}: {e}")

    def _load_secrets(self) -> None:
        """Load all secrets from environment and .env files."""
        project_root = self._find_project_root()

        # Load .env file (lower priority)
        self._load_env_file(project_root / ".env")

        # Load .env.local file (higher priority, for local overrides)
        self._load_env_file(project_root / ".env.local")

        # Environment variables have highest priority
        # They're accessed directly in get() method

        logger.info(
            f"Secrets manager initialized with {len(self._secrets)} secrets from files"
        )

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a secret value.

        Environment variables take priority over .env file values.

        Args:
            key: The secret key name
            default: Default value if secret not found

        Returns:
            The secret value, or default if not found
        """
        # Environment variables have highest priority
        env_value = os.environ.get(key)
        if env_value is not None:
            return env_value

        # Then check loaded secrets from .env files
        if key in self._secrets:
            return self._secrets[key]

        # Return default if not found
        if default is None:
            logger.warning(f"Secret '{key}' not found and no default provided")

        return default

    def get_required(self, key: str) -> str:
        """
        Get a required secret value.

        Raises an error if the secret is not found.

        Args:
            key: The secret key name

        Returns:
            The secret value

        Raises:
            ValueError: If the secret is not found
        """
        value = self.get(key)
        if value is None:
            raise ValueError(
                f"Required secret '{key}' not found. "
                f"Please set it as an environment variable or in .env file."
            )
        return value

    def has(self, key: str) -> bool:
        """
        Check if a secret exists.

        Args:
            key: The secret key name

        Returns:
            True if the secret exists
        """
        return key in os.environ or key in self._secrets

    def reload(self) -> None:
        """Reload secrets from .env files."""
        self._secrets.clear()
        self._load_secrets()
        logger.info("Secrets reloaded")

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance (useful for testing)."""
        cls._instance = None
        cls._initialized = False


# Convenience functions for quick access
_default_manager: Optional[SecretsManager] = None


def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get a secret value using the default manager.

    Args:
        key: The secret key name
        default: Default value if secret not found

    Returns:
        The secret value, or default if not found
    """
    global _default_manager
    if _default_manager is None:
        _default_manager = SecretsManager()
    return _default_manager.get(key, default)


def get_required_secret(key: str) -> str:
    """
    Get a required secret value using the default manager.

    Args:
        key: The secret key name

    Returns:
        The secret value

    Raises:
        ValueError: If the secret is not found
    """
    global _default_manager
    if _default_manager is None:
        _default_manager = SecretsManager()
    return _default_manager.get_required(key)
