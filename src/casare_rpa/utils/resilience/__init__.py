"""Resilience patterns and utilities."""

from casare_rpa.utils.resilience.retry import (
    ErrorCategory,
    RetryConfig,
    RetryResult,
    RetryStats,
    DEFAULT_RETRY_CONFIG,
    TRANSIENT_EXCEPTIONS,
    TRANSIENT_PATTERNS,
    classify_error,
    retry_async,
    retry_operation,
    retry_with_timeout,
    with_retry,
    with_timeout,
)
from casare_rpa.utils.resilience.rate_limiter import RateLimiter
from casare_rpa.utils.resilience.error_handler import GlobalErrorHandler

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
