"""
CasareRPA Retry Configuration.

Centralized retry and backoff settings for resilient operations.
Uses frozen dataclasses for immutability with environment variable overrides.

Usage:
    from casare_rpa.config.retry_config import get_retry_config

    config = get_retry_config()
    max_attempts = config.max_attempts
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Final


def _parse_float(value: str | None, default: float) -> float:
    """Parse float from environment variable string."""
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _parse_int(value: str | None, default: int) -> int:
    """Parse integer from environment variable string."""
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class RetryConfig:
    """
    Centralized retry configuration for all CasareRPA operations.

    All retry values are extracted from hardcoded defaults across the codebase.
    Implements exponential backoff pattern with configurable parameters.

    Attributes:
        max_attempts: Default maximum retry attempts for general operations.
            Used by resilience decorators and HTTP clients.
            Default: 3

        ai_max_attempts: Maximum retry attempts for AI/LLM operations.
            Lower to avoid excessive API costs.
            Default: 2

        node_max_attempts: Maximum retry attempts for node execution.
            Configurable per-node, this is the default.
            Default: 3

        websocket_reconnect_max: Maximum reconnection attempts for WebSocket.
            Used by orchestrator communication layer.
            Default: 10

        base_delay_ms: Initial delay between retries in milliseconds.
            Starting point for exponential backoff.
            Default: 1000

        max_delay_ms: Maximum delay between retries in milliseconds.
            Cap to prevent excessive wait times.
            Default: 30000

        backoff_multiplier: Multiplier for exponential backoff.
            Each retry delay = previous_delay * multiplier.
            Default: 2.0

        jitter_factor: Random jitter factor to prevent thundering herd.
            Adds randomness to delay: delay * (1 + random(0, jitter_factor)).
            Default: 0.1

        http_retry_statuses: HTTP status codes that trigger retry.
            Typically 429 (rate limit), 500, 502, 503, 504 (server errors).
            Stored as tuple for immutability.
    """

    # Attempt limits
    max_attempts: int = 3
    ai_max_attempts: int = 2
    node_max_attempts: int = 3
    websocket_reconnect_max: int = 10

    # Backoff timing
    base_delay_ms: int = 1000
    max_delay_ms: int = 30000
    backoff_multiplier: float = 2.0
    jitter_factor: float = 0.1

    # HTTP retry configuration
    http_retry_statuses: tuple[int, ...] = (429, 500, 502, 503, 504)

    @classmethod
    def from_env(cls) -> RetryConfig:
        """
        Create RetryConfig from environment variables.

        Environment variable names follow the pattern:
        CASARE_RETRY_{SETTING}

        Example:
            CASARE_RETRY_MAX_ATTEMPTS=5
            CASARE_RETRY_BASE_DELAY_MS=500

        Returns:
            RetryConfig with values from environment or defaults
        """
        # Parse HTTP retry statuses from comma-separated string
        http_statuses_str = os.getenv("CASARE_RETRY_HTTP_STATUSES")
        if http_statuses_str:
            try:
                http_statuses = tuple(
<<<<<<< HEAD
                    int(s.strip())
                    for s in http_statuses_str.split(",")
                    if s.strip().isdigit()
=======
                    int(s.strip()) for s in http_statuses_str.split(",") if s.strip().isdigit()
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
                )
            except ValueError:
                http_statuses = (429, 500, 502, 503, 504)
        else:
            http_statuses = (429, 500, 502, 503, 504)

        return cls(
            max_attempts=_parse_int(os.getenv("CASARE_RETRY_MAX_ATTEMPTS"), 3),
            ai_max_attempts=_parse_int(os.getenv("CASARE_RETRY_AI_MAX_ATTEMPTS"), 2),
<<<<<<< HEAD
            node_max_attempts=_parse_int(
                os.getenv("CASARE_RETRY_NODE_MAX_ATTEMPTS"), 3
            ),
=======
            node_max_attempts=_parse_int(os.getenv("CASARE_RETRY_NODE_MAX_ATTEMPTS"), 3),
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
            websocket_reconnect_max=_parse_int(
                os.getenv("CASARE_RETRY_WEBSOCKET_RECONNECT_MAX"), 10
            ),
            base_delay_ms=_parse_int(os.getenv("CASARE_RETRY_BASE_DELAY_MS"), 1000),
            max_delay_ms=_parse_int(os.getenv("CASARE_RETRY_MAX_DELAY_MS"), 30000),
<<<<<<< HEAD
            backoff_multiplier=_parse_float(
                os.getenv("CASARE_RETRY_BACKOFF_MULTIPLIER"), 2.0
            ),
=======
            backoff_multiplier=_parse_float(os.getenv("CASARE_RETRY_BACKOFF_MULTIPLIER"), 2.0),
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
            jitter_factor=_parse_float(os.getenv("CASARE_RETRY_JITTER_FACTOR"), 0.1),
            http_retry_statuses=http_statuses,
        )

    def get_base_delay_s(self) -> float:
        """Get base delay in seconds."""
        return self.base_delay_ms / 1000.0

    def get_max_delay_s(self) -> float:
        """Get max delay in seconds."""
        return self.max_delay_ms / 1000.0

    def calculate_delay_ms(self, attempt: int) -> int:
        """
        Calculate delay for a specific retry attempt using exponential backoff.

        Args:
            attempt: The attempt number (0-indexed, where 0 is the first retry)

        Returns:
            Delay in milliseconds, capped at max_delay_ms
        """
        import random

        # Calculate exponential delay
        delay = self.base_delay_ms * (self.backoff_multiplier**attempt)

        # Apply jitter
        if self.jitter_factor > 0:
            jitter = random.uniform(0, self.jitter_factor)
            delay = delay * (1 + jitter)

        # Cap at maximum
        return min(int(delay), self.max_delay_ms)

    def should_retry_http_status(self, status_code: int) -> bool:
        """
        Check if an HTTP status code should trigger a retry.

        Args:
            status_code: HTTP response status code

        Returns:
            True if the status code is in the retry list
        """
        return status_code in self.http_retry_statuses


# Module-level singleton
_retry_config: RetryConfig | None = None


def get_retry_config() -> RetryConfig:
    """
    Get the retry configuration singleton.

    Configuration is loaded once from environment variables
    and cached for subsequent calls.

    Returns:
        RetryConfig instance
    """
    global _retry_config
    if _retry_config is None:
        _retry_config = RetryConfig.from_env()
    return _retry_config


def reset_retry_config() -> None:
    """Reset the retry configuration singleton (for testing)."""
    global _retry_config
    _retry_config = None


# Convenience constants for backward compatibility
DEFAULT_MAX_ATTEMPTS: Final[int] = 3
DEFAULT_BASE_DELAY_MS: Final[int] = 1000
DEFAULT_MAX_DELAY_MS: Final[int] = 30000
DEFAULT_BACKOFF_MULTIPLIER: Final[float] = 2.0


__all__ = [
    "RetryConfig",
    "get_retry_config",
    "reset_retry_config",
    "DEFAULT_MAX_ATTEMPTS",
    "DEFAULT_BASE_DELAY_MS",
    "DEFAULT_MAX_DELAY_MS",
    "DEFAULT_BACKOFF_MULTIPLIER",
]
