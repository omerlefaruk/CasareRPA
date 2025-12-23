import hashlib
from typing import Any

import orjson
from loguru import logger


class CacheKeyGenerator:
    """
    Generates deterministic cache keys for complex objects.
    Uses orjson for stable serialization (sorted keys) and SHA-256 for hashing.
    """

    @staticmethod
    def generate(
        namespace: str, data: Any, tenant_id: str | None = None, version: str = "v1"
    ) -> str:
        """
        Generates a stable cache key.

        Args:
            namespace: The logical grouping (e.g., 'api', 'node', 'db').
            data: The data to hash (dict, list, string, etc.).
            tenant_id: Optional tenant ID for multi-tenant isolation.
            version: Cache version to allow breaking changes in key format.

        Returns:
            A string key in the format: namespace:tenant_id:version:hash
        """
        try:
            # Serialize with sorted keys for determinism
            serialized = orjson.dumps(
                data,
                option=orjson.OPT_SORT_KEYS | orjson.OPT_NON_STR_KEYS | orjson.OPT_SERIALIZE_NUMPY,
            )

            # Generate SHA-256 hash
            data_hash = hashlib.sha256(serialized).hexdigest()[:16]

            # Build key components
            components = [namespace]
            if tenant_id:
                components.append(tenant_id)
            components.append(version)
            components.append(data_hash)

            return ":".join(components)

        except Exception as e:
            logger.error(f"Failed to generate cache key for {namespace}: {e}")
            # Fallback to a random-ish but safe key if serialization fails
            return f"{namespace}:error:{hash(str(data))}"
