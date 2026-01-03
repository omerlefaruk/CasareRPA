from typing import Any

from casare_rpa.domain.services.cache_keys import StableCacheKeyGenerator


class CacheKeyGenerator:
    """
    Generates deterministic cache keys for complex objects.
    Uses orjson for stable serialization (sorted keys) and SHA-256 for hashing.
    """

    @staticmethod
    def generate(
        namespace: str, data: Any, tenant_id: str | None = None, version: str = "v1"
    ) -> str:
        """Generate a stable cache key (delegates to the domain implementation)."""
        return StableCacheKeyGenerator.generate(
            namespace=namespace,
            data=data,
            tenant_id=tenant_id,
            version=version,
        )
