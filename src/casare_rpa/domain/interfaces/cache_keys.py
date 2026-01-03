"""Cache key generation interface."""

from typing import Any, Protocol


class ICacheKeyGenerator(Protocol):
    """Protocol for generating stable cache keys."""

    @staticmethod
    def generate(
        namespace: str,
        data: Any,
        tenant_id: str | None = None,
        version: str = "v1",
    ) -> str:
        """Generate a stable cache key string from structured data."""
