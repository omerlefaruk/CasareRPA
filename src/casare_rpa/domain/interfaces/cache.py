"""Domain-level cache interface."""

from typing import Any, Protocol


class ICacheManager(Protocol):
    """Protocol for cache operations used by the application layer."""

    async def get(self, key: str) -> Any | None:
        """Get a cached value."""

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set a cached value."""

    async def delete_by_prefix(self, prefix: str) -> None:
        """Delete all cache keys matching a prefix."""
