"""
CasareRPA - Data Masker Module.

Provides automatic detection and masking of sensitive data in logs, UI displays,
and API responses. Protects passwords, API keys, tokens, and other credentials
from accidental exposure.

Features:
- Pattern-based detection of sensitive data in strings
- Key-based detection in dictionaries
- Recursive masking for nested structures
- Configurable mask character and length
- Thread-safe operation
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple, Union

from loguru import logger


@dataclass(frozen=True)
class MaskingConfig:
    """Configuration for data masking behavior."""

    mask_char: str = "*"
    mask_length: int = 6
    partial_mask: bool = False
    partial_visible_chars: int = 2


class DataMasker:
    """
    Masks sensitive data in strings, dictionaries, and complex objects.

    Thread-safe implementation for use in logging and UI display.
    Detects common patterns for passwords, API keys, tokens, and credentials.

    Usage:
        masker = DataMasker()

        # Mask strings
        masked = masker.mask_string("password=secret123")
        # Returns: "password=******"

        # Mask dictionaries
        masked = masker.mask_dict({"api_key": "sk-abc123"})
        # Returns: {"api_key": "******"}

        # Safe logging
        safe_text = masker.mask_for_logging(complex_object)
    """

    # Sensitive key names (lowercase for comparison)
    SENSITIVE_KEYS: frozenset[str] = frozenset(
        {
            "password",
            "passwd",
            "pwd",
            "pass",
            "secret",
            "secrets",
            "api_key",
            "apikey",
            "api-key",
            "access_token",
            "accesstoken",
            "access-token",
            "refresh_token",
            "refreshtoken",
            "refresh-token",
            "auth_token",
            "authtoken",
            "auth-token",
            "bearer",
            "bearer_token",
            "authorization",
            "auth",
            "private_key",
            "privatekey",
            "private-key",
            "secret_key",
            "secretkey",
            "secret-key",
            "credential",
            "credentials",
            "cred",
            "creds",
            "token",
            "tokens",
            "key",
            "keys",
            "session_id",
            "sessionid",
            "session-id",
            "cookie",
            "cookies",
            "jwt",
            "jwt_token",
            "client_secret",
            "clientsecret",
            "client-secret",
            "encryption_key",
            "encryptionkey",
            "signing_key",
            "signingkey",
            "database_password",
            "db_password",
            "dbpassword",
            "connection_string",
            "connectionstring",
            "pin",
            "otp",
            "totp",
            "mfa_code",
            "ssn",
            "social_security",
            "credit_card",
            "creditcard",
            "cc_number",
            "cvv",
            "cvc",
        }
    )

    # Patterns for detecting sensitive values in strings
    # Each tuple: (compiled_regex, group_index_to_mask)
    SENSITIVE_PATTERNS: list[tuple[re.Pattern, int]] = [
        # Password patterns
        (
            re.compile(r'password["\']?\s*[:=]\s*["\']?([^"\'}\s,\n]+)', re.IGNORECASE),
            1,
        ),
        (re.compile(r'passwd["\']?\s*[:=]\s*["\']?([^"\'}\s,\n]+)', re.IGNORECASE), 1),
        (re.compile(r'pwd["\']?\s*[:=]\s*["\']?([^"\'}\s,\n]+)', re.IGNORECASE), 1),
        # API key patterns
        (
            re.compile(r'api[_-]?key["\']?\s*[:=]\s*["\']?([^"\'}\s,\n]+)', re.IGNORECASE),
            1,
        ),
        (re.compile(r'apikey["\']?\s*[:=]\s*["\']?([^"\'}\s,\n]+)', re.IGNORECASE), 1),
        # Secret patterns
        (re.compile(r'secret["\']?\s*[:=]\s*["\']?([^"\'}\s,\n]+)', re.IGNORECASE), 1),
        (
            re.compile(r'client[_-]?secret["\']?\s*[:=]\s*["\']?([^"\'}\s,\n]+)', re.IGNORECASE),
            1,
        ),
        # Token patterns
        (re.compile(r'token["\']?\s*[:=]\s*["\']?([^"\'}\s,\n]+)', re.IGNORECASE), 1),
        (
            re.compile(r'access[_-]?token["\']?\s*[:=]\s*["\']?([^"\'}\s,\n]+)', re.IGNORECASE),
            1,
        ),
        (
            re.compile(r'refresh[_-]?token["\']?\s*[:=]\s*["\']?([^"\'}\s,\n]+)', re.IGNORECASE),
            1,
        ),
        (
            re.compile(r'auth[_-]?token["\']?\s*[:=]\s*["\']?([^"\'}\s,\n]+)', re.IGNORECASE),
            1,
        ),
        # Bearer token in headers
        (re.compile(r'bearer\s+([^\s"\']+)', re.IGNORECASE), 1),
        # Authorization header
        (
            re.compile(r'authorization["\']?\s*[:=]\s*["\']?([^"\'}\s,\n]+)', re.IGNORECASE),
            1,
        ),
        # Connection strings (database)
        (
            re.compile(r"(mongodb|postgres|mysql|redis|amqp)://[^:]+:([^@]+)@", re.IGNORECASE),
            2,
        ),
        # AWS credentials
        (
            re.compile(
                r'aws[_-]?secret[_-]?access[_-]?key["\']?\s*[:=]\s*["\']?([^"\'}\s,\n]+)',
                re.IGNORECASE,
            ),
            1,
        ),
        (
            re.compile(
                r"AKIA[0-9A-Z]{16}",  # AWS Access Key ID format
            ),
            0,
        ),
        # Private keys (PEM format indicator)
        (
            re.compile(
                r"-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----",
            ),
            0,
        ),
        # JWT tokens
        (
            re.compile(
                r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+",
            ),
            0,
        ),
        # Generic key=value for sensitive keys
        (
            re.compile(
                r'(credential|cred|auth)[s]?["\']?\s*[:=]\s*["\']?([^"\'}\s,\n]+)',
                re.IGNORECASE,
            ),
            2,
        ),
    ]

    def __init__(self, config: MaskingConfig | None = None) -> None:
        """
        Initialize the data masker.

        Args:
            config: Optional masking configuration
        """
        self._config = config or MaskingConfig()
        self._mask_string = self._config.mask_char * self._config.mask_length

    @property
    def mask_value(self) -> str:
        """Get the mask replacement string."""
        return self._mask_string

    def is_sensitive_key(self, key: str) -> bool:
        """
        Check if a key name indicates sensitive data.

        Args:
            key: Key name to check

        Returns:
            True if key indicates sensitive data
        """
        if not key:
            return False

        key_lower = key.lower().strip()

        # Direct match
        if key_lower in self.SENSITIVE_KEYS:
            return True

        # Partial match for compound keys
        for sensitive_key in self.SENSITIVE_KEYS:
            if sensitive_key in key_lower:
                return True

        return False

    def mask_string(self, text: str) -> str:
        """
        Mask sensitive values in a string.

        Detects patterns like password=xxx, api_key: xxx, Bearer xxx
        and replaces the sensitive values with mask characters.

        Args:
            text: Input string that may contain sensitive data

        Returns:
            String with sensitive values masked
        """
        if not text or not isinstance(text, str):
            return text

        result = text

        for pattern, group_index in self.SENSITIVE_PATTERNS:

            def replacer(match: re.Match) -> str:
                groups = match.groups()
                if group_index == 0:
                    # Replace entire match
                    return self._mask_string
                elif group_index <= len(groups):
                    # Replace specific group
                    original = match.group(0)
                    sensitive_value = groups[group_index - 1]
                    if sensitive_value:
                        return original.replace(sensitive_value, self._mask_string)
                return match.group(0)

            result = pattern.sub(replacer, result)

        return result

    def mask_dict(
        self,
        data: dict[str, Any],
        deep_copy: bool = True,
    ) -> dict[str, Any]:
        """
        Mask sensitive values in a dictionary.

        Recursively processes nested dictionaries and lists.
        Keys matching sensitive patterns have their values masked.

        Args:
            data: Dictionary that may contain sensitive data
            deep_copy: If True, returns a new dict; if False, modifies in place

        Returns:
            Dictionary with sensitive values masked
        """
        if not isinstance(data, dict):
            return data

        result = {} if deep_copy else data

        for key, value in data.items():
            masked_value = self._mask_value(key, value)
            if deep_copy:
                result[key] = masked_value
            else:
                data[key] = masked_value

        return result

    def _mask_value(self, key: str, value: Any) -> Any:
        """
        Mask a value based on its key and type.

        Args:
            key: The key name
            value: The value to potentially mask

        Returns:
            Masked value if sensitive, original otherwise
        """
        if value is None:
            return None

        # Check if key indicates sensitive data
        if self.is_sensitive_key(key):
            if isinstance(value, str):
                if (
                    self._config.partial_mask
                    and len(value) > self._config.partial_visible_chars * 2
                ):
                    visible = self._config.partial_visible_chars
                    return value[:visible] + self._mask_string + value[-visible:]
                return self._mask_string
            elif isinstance(value, (int, float)):
                return self._mask_string
            elif isinstance(value, (list, tuple)):
                return [self._mask_string] * len(value)
            elif isinstance(value, dict):
                return {k: self._mask_string for k in value}
            else:
                return self._mask_string

        # Recursively process nested structures
        if isinstance(value, dict):
            return self.mask_dict(value)
        elif isinstance(value, list):
            return [
                self._mask_value("", item) if isinstance(item, dict) else item for item in value
            ]
        elif isinstance(value, str):
            return self.mask_string(value)

        return value

    def mask_for_logging(self, obj: Any) -> str:
        """
        Create a safe string representation for logging.

        Handles any object type and ensures sensitive data is masked.

        Args:
            obj: Object to convert to safe string

        Returns:
            Safe string representation
        """
        try:
            if obj is None:
                return "None"

            if isinstance(obj, str):
                return self.mask_string(obj)

            if isinstance(obj, dict):
                masked = self.mask_dict(obj)
                return str(masked)

            if isinstance(obj, (list, tuple)):
                masked_items = []
                for item in obj:
                    if isinstance(item, dict):
                        masked_items.append(self.mask_dict(item))
                    elif isinstance(item, str):
                        masked_items.append(self.mask_string(item))
                    else:
                        masked_items.append(item)
                return str(masked_items)

            if hasattr(obj, "__dict__"):
                return self.mask_for_logging(obj.__dict__)

            return self.mask_string(str(obj))

        except Exception as e:
            logger.warning(f"Error masking object for logging: {e}")
            return "<masked due to error>"

    def get_sensitive_keys_in_dict(self, data: dict[str, Any]) -> set[str]:
        """
        Find all sensitive keys in a dictionary.

        Useful for auditing what data would be masked.

        Args:
            data: Dictionary to scan

        Returns:
            Set of sensitive key names found
        """
        sensitive_found: set[str] = set()

        def scan(d: dict[str, Any], prefix: str = "") -> None:
            for key, value in d.items():
                full_key = f"{prefix}.{key}" if prefix else key
                if self.is_sensitive_key(key):
                    sensitive_found.add(full_key)
                if isinstance(value, dict):
                    scan(value, full_key)
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            scan(item, f"{full_key}[{i}]")

        if isinstance(data, dict):
            scan(data)

        return sensitive_found


class MaskedLogger:
    """
    Logger wrapper that automatically masks sensitive data.

    Wraps loguru logger calls to ensure all logged data is masked
    before being written to log files or console.

    Usage:
        masked_logger = MaskedLogger()
        masked_logger.info("User logged in with password=secret123")
        # Logs: "User logged in with password=******"
    """

    def __init__(
        self,
        masker: DataMasker | None = None,
    ) -> None:
        """
        Initialize masked logger.

        Args:
            masker: DataMasker instance (creates default if None)
        """
        self._masker = masker or DataMasker()

    def _mask_args(self, message: str, **kwargs: Any) -> tuple[str, dict[str, Any]]:
        """Mask message and keyword arguments."""
        masked_msg = self._masker.mask_string(str(message))
        masked_kwargs = self._masker.mask_dict(dict(kwargs))
        return masked_msg, masked_kwargs

    def trace(self, message: str, **kwargs: Any) -> None:
        """Log trace message with masking."""
        msg, kw = self._mask_args(message, **kwargs)
        logger.trace(msg, **kw)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message with masking."""
        msg, kw = self._mask_args(message, **kwargs)
        logger.debug(msg, **kw)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message with masking."""
        msg, kw = self._mask_args(message, **kwargs)
        logger.info(msg, **kw)

    def success(self, message: str, **kwargs: Any) -> None:
        """Log success message with masking."""
        msg, kw = self._mask_args(message, **kwargs)
        logger.success(msg, **kw)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message with masking."""
        msg, kw = self._mask_args(message, **kwargs)
        logger.warning(msg, **kw)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message with masking."""
        msg, kw = self._mask_args(message, **kwargs)
        logger.error(msg, **kw)

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message with masking."""
        msg, kw = self._mask_args(message, **kwargs)
        logger.critical(msg, **kw)

    def exception(self, message: str, **kwargs: Any) -> None:
        """Log exception with masking."""
        msg, kw = self._mask_args(message, **kwargs)
        logger.exception(msg, **kw)


# Global default masker instance
_default_masker: DataMasker | None = None


def get_masker() -> DataMasker:
    """
    Get the global default DataMasker instance.

    Returns:
        Global DataMasker instance
    """
    global _default_masker
    if _default_masker is None:
        _default_masker = DataMasker()
    return _default_masker


def mask_sensitive_data(data: str | dict | Any) -> str | dict | Any:
    """
    Convenience function to mask sensitive data.

    Args:
        data: Data to mask (string, dict, or any object)

    Returns:
        Masked data
    """
    masker = get_masker()
    if isinstance(data, str):
        return masker.mask_string(data)
    elif isinstance(data, dict):
        return masker.mask_dict(data)
    else:
        return masker.mask_for_logging(data)


__all__ = [
    "DataMasker",
    "MaskedLogger",
    "MaskingConfig",
    "get_masker",
    "mask_sensitive_data",
]
