"""
Domain-level cache key generation.

This is a pure, deterministic implementation intended to be used by the application
layer without depending on infrastructure modules.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


class StableCacheKeyGenerator:
    """Generate deterministic cache keys for structured data."""

    @staticmethod
    def generate(
        namespace: str,
        data: Any,
        tenant_id: str | None = None,
        version: str = "v1",
    ) -> str:
        try:
            import orjson  # type: ignore[import-not-found]

            serialized = orjson.dumps(
                data,
                option=orjson.OPT_SORT_KEYS | orjson.OPT_NON_STR_KEYS | orjson.OPT_SERIALIZE_NUMPY,
            )
        except Exception:
            serialized = json.dumps(
                data,
                sort_keys=True,
                default=str,
                separators=(",", ":"),
                ensure_ascii=True,
            ).encode("utf-8")

        data_hash = hashlib.sha256(serialized).hexdigest()[:16]

        components: list[str] = [namespace]
        if tenant_id:
            components.append(tenant_id)
        components.append(version)
        components.append(data_hash)
        return ":".join(components)
