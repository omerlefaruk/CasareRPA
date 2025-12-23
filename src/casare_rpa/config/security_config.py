"""
Security configuration with sensible defaults.

Centralizes cryptographic parameters like PBKDF2 iteration counts
to allow environment-based tuning without code changes.
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class CryptoSecurityConfig:
    """
    Security-related configuration values for cryptographic operations.

    This is separate from the Pydantic SecurityConfig in schema.py which
    handles auth/JWT settings. This focuses on crypto parameters.
    """

    # PBKDF2 iterations for standard key derivation
    # 100,000 is a reasonable balance of security and performance
    pbkdf2_iterations: int = 100_000

    # PBKDF2 iterations for high-security vault operations
    # OWASP recommends 600,000+ for SHA-256, we use 480,000 as baseline
    pbkdf2_owasp_iterations: int = 480_000

    # Token expiry buffer in seconds (for early refresh)
    token_expiry_buffer_seconds: int = 300

    @classmethod
    def from_env(cls) -> "CryptoSecurityConfig":
        """
        Load config from environment variables with fallbacks.

        Environment variables:
            SECURITY_PBKDF2_ITERATIONS: Standard PBKDF2 iterations (default: 100000)
            SECURITY_PBKDF2_OWASP_ITERATIONS: High-security iterations (default: 480000)
            SECURITY_TOKEN_EXPIRY_BUFFER_S: Token expiry buffer in seconds (default: 300)

        Returns:
            CryptoSecurityConfig instance with values from env or defaults
        """
        return cls(
            pbkdf2_iterations=int(os.getenv("SECURITY_PBKDF2_ITERATIONS", "100000")),
            pbkdf2_owasp_iterations=int(os.getenv("SECURITY_PBKDF2_OWASP_ITERATIONS", "480000")),
            token_expiry_buffer_seconds=int(os.getenv("SECURITY_TOKEN_EXPIRY_BUFFER_S", "300")),
        )


# Singleton instance
_crypto_security_config: CryptoSecurityConfig | None = None


def get_crypto_security_config() -> CryptoSecurityConfig:
    """
    Get the crypto security configuration singleton.

    Lazily loads from environment on first access.
    Thread-safe for reads after initialization.

    Returns:
        CryptoSecurityConfig singleton instance
    """
    global _crypto_security_config
    if _crypto_security_config is None:
        _crypto_security_config = CryptoSecurityConfig.from_env()
    return _crypto_security_config


def reset_crypto_security_config() -> None:
    """
    Reset the singleton for testing purposes.

    Allows tests to reinitialize config with different env vars.
    """
    global _crypto_security_config
    _crypto_security_config = None


__all__ = [
    "CryptoSecurityConfig",
    "get_crypto_security_config",
    "reset_crypto_security_config",
]
