"""Resilience patterns and utilities."""

from casare_rpa.utils.resilience.error_handler import GlobalErrorHandler
from casare_rpa.utils.resilience.rate_limiter import RateLimiter
from casare_rpa.utils.resilience.retry import (
    DEFAULT_RETRY_CONFIG,
    TRANSIENT_EXCEPTIONS,
    TRANSIENT_PATTERNS,
    ErrorCategory,
    RetryConfig,
    RetryResult,
    RetryStats,
    classify_error,
    retry_async,
    retry_operation,
    retry_with_timeout,
    with_retry,
    with_timeout,
)

__all__ = [
    # retry.py
    "ErrorCategory",
    "RetryConfig",
    "RetryResult",
    "RetryStats",
    "DEFAULT_RETRY_CONFIG",
    "TRANSIENT_EXCEPTIONS",
    "TRANSIENT_PATTERNS",
    "classify_error",
    "retry_async",
    "retry_operation",
    "retry_with_timeout",
    "with_retry",
    "with_timeout",
    # rate_limiter.py
    "RateLimiter",
    # error_handler.py
    "GlobalErrorHandler",
]
