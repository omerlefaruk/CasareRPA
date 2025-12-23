"""
HTTP Infrastructure Module for CasareRPA.

Provides the UnifiedHttpClient facade that composes all resilience patterns:
- Connection pooling (HttpSessionPool)
- Exponential backoff retry
- Per-domain rate limiting
- Per-base-URL circuit breaker
"""

from casare_rpa.infrastructure.http.unified_http_client import (
    RETRY_STATUS_CODES,
    RequestStats,
    UnifiedHttpClient,
    UnifiedHttpClientConfig,
    close_unified_http_client,
    get_unified_http_client,
)

__all__ = [
    "UnifiedHttpClient",
    "UnifiedHttpClientConfig",
    "RequestStats",
    "RETRY_STATUS_CODES",
    "get_unified_http_client",
    "close_unified_http_client",
]
