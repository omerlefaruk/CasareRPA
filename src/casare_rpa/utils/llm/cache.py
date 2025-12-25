"""LLM response caching with diskcache.

Caches LLM API responses to reduce tokens and improve latency.
"""

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import diskcache


@dataclass
class CacheEntry:
    """Cache entry with metadata."""

    response: str
    model: str
    tokens_in: int
    tokens_out: int
    timestamp: datetime
    ttl_hours: int = 24


class LLMResponseCache:
    """Cache for LLM API responses.

    Features:
    - Disk-based persistence (diskcache)
    - Automatic TTL expiration
    - Token counting for budgeting
    - Cache key generation from prompts

    Usage:
        cache = LLMResponseCache(cache_dir='.llm_cache')
        response = cache.get(prompt, model='gpt-4')

        if not response:
            response = llm.generate(prompt)
            cache.set(prompt, response, model='gpt-4', tokens_in=100, tokens_out=200)
    """

    def __init__(
        self, cache_dir: str = ".llm_cache", default_ttl_hours: int = 24, max_size_mb: int = 1024
    ):
        """Initialize LLM response cache.

        Args:
            cache_dir: Directory for cache storage.
            default_ttl_hours: Default TTL in hours.
            max_size_mb: Maximum cache size in MB.
        """
        self._cache = diskcache.Cache(
            cache_dir, size_limit=max_size_mb * 1024 * 1024, eviction_policy="least-recently-used"
        )
        self.default_ttl = default_ttl_hours

    def _generate_key(self, prompt: str, model: str, temperature: float = 0.7, **kwargs) -> str:
        """Generate cache key from request parameters.

        Args:
            prompt: The prompt text.
            model: Model identifier.
            temperature: Generation temperature.
            **kwargs: Additional parameters.

        Returns:
            SHA256 hash key.
        """
        key_data = f"{model}:{temperature}:{prompt}:"

        for k, v in sorted(kwargs.items()):
            key_data += f"{k}={v}:"

        return hashlib.sha256(key_data.encode()).hexdigest()

    def get(
        self, prompt: str, model: str, temperature: float = 0.7, **kwargs
    ) -> Optional[CacheEntry]:
        """Get cached response.

        Args:
            prompt: The prompt text.
            model: Model identifier.
            temperature: Generation temperature.
            **kwargs: Additional parameters.

        Returns:
            CacheEntry if found and not expired, else None.
        """
        key = self._generate_key(prompt, model, temperature, **kwargs)

        try:
            entry_data, _ = self._cache.get(key, default=(None, None))

            if not entry_data:
                return None

            entry_dict = json.loads(entry_data)
            timestamp = datetime.fromisoformat(entry_dict["timestamp"])

            if datetime.now() - timestamp > timedelta(hours=entry_dict["ttl_hours"]):
                self._cache.delete(key)
                return None

            return CacheEntry(
                response=entry_dict["response"],
                model=entry_dict["model"],
                tokens_in=entry_dict["tokens_in"],
                tokens_out=entry_dict["tokens_out"],
                timestamp=timestamp,
                ttl_hours=entry_dict["ttl_hours"],
            )

        except (json.JSONDecodeError, KeyError, TypeError):
            return None

    def set(
        self,
        prompt: str,
        response: str,
        model: str,
        tokens_in: int,
        tokens_out: int,
        temperature: float = 0.7,
        ttl_hours: Optional[int] = None,
        **kwargs,
    ) -> None:
        """Cache LLM response.

        Args:
            prompt: The prompt text.
            response: LLM response text.
            model: Model identifier.
            tokens_in: Input token count.
            tokens_out: Output token count.
            temperature: Generation temperature.
            ttl_hours: Custom TTL (uses default if None).
            **kwargs: Additional parameters.
        """
        if ttl_hours is None:
            ttl_hours = self.default_ttl

        key = self._generate_key(prompt, model, temperature, **kwargs)

        entry = CacheEntry(
            response=response,
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            timestamp=datetime.now(),
            ttl_hours=ttl_hours,
        )

        entry_dict = asdict(entry)
        entry_dict["timestamp"] = entry.timestamp.isoformat()

        self._cache.set(key, json.dumps(entry_dict))

    def invalidate(self, prompt: str, model: str, **kwargs) -> None:
        """Invalidate cache entry.

        Args:
            prompt: The prompt text.
            model: Model identifier.
            **kwargs: Additional parameters.
        """
        key = self._generate_key(prompt, model, **kwargs)
        self._cache.delete(key)

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()

    def stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats.
        """
        total_size = 0
        entries = []

        for key in self._cache.iterkeys():
            try:
                value, _ = self._cache.get(key, default=(None, None))
                if value:
                    total_size += len(value)
                    entries.append(json.loads(value))
            except (json.JSONDecodeError, TypeError):
                pass

        now = datetime.now()
        expired = sum(
            1
            for e in entries
            if now - datetime.fromisoformat(e["timestamp"]) > timedelta(hours=e["ttl_hours"])
        )

        return {
            "total_entries": len(entries),
            "valid_entries": len(entries) - expired,
            "expired_entries": expired,
            "total_size_mb": total_size / (1024 * 1024),
            "cache_dir": self._cache.directory,
        }

    def prune_expired(self) -> int:
        """Remove expired cache entries.

        Returns:
            Number of entries removed.
        """
        removed = 0

        for key in list(self._cache.iterkeys()):
            try:
                entry_data, _ = self._cache.get(key, default=(None, None))
                if entry_data:
                    entry_dict = json.loads(entry_data)
                    timestamp = datetime.fromisoformat(entry_dict["timestamp"])

                    if datetime.now() - timestamp > timedelta(hours=entry_dict["ttl_hours"]):
                        self._cache.delete(key)
                        removed += 1
            except (json.JSONDecodeError, KeyError, TypeError):
                pass

        return removed

    def export_stats(self, path: str) -> None:
        """Export cache statistics to file.

        Args:
            path: Output file path.
        """
        stats = self.stats()
        stats["exported_at"] = datetime.now().isoformat()

        with open(path, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2)


class CachedLLMClient:
    """LLM client wrapper with automatic caching.

    Wraps any LLM client (OpenAI, Anthropic, etc.) with caching.

    Usage:
        cache = LLMResponseCache()
        client = CachedLLMClient(real_client, cache)

        response = client.generate(
            prompt="Hello",
            model="gpt-4",
            temperature=0.7
        )
    """

    def __init__(self, real_client, cache: LLMResponseCache):
        """Initialize cached LLM client.

        Args:
            real_client: Actual LLM client (e.g., OpenAI client).
            cache: LLMResponseCache instance.
        """
        self._client = real_client
        self._cache = cache
        self._stats = {"hits": 0, "misses": 0}

    def generate(self, prompt: str, model: str, temperature: float = 0.7, **kwargs) -> str:
        """Generate response with caching.

        Args:
            prompt: The prompt text.
            model: Model identifier.
            temperature: Generation temperature.
            **kwargs: Additional parameters.

        Returns:
            Generated response text.
        """
        cached = self._cache.get(prompt, model, temperature, **kwargs)

        if cached:
            self._stats["hits"] += 1
            return cached.response

        self._stats["misses"] += 1

        response = self._call_llm(prompt, model, temperature, **kwargs)

        tokens_in = self._estimate_tokens(prompt)
        tokens_out = self._estimate_tokens(response)

        self._cache.set(
            prompt=prompt,
            response=response,
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            temperature=temperature,
            **kwargs,
        )

        return response

    def _call_llm(self, prompt: str, model: str, **kwargs) -> str:
        """Call underlying LLM client.

        Args:
            prompt: The prompt text.
            model: Model identifier.
            **kwargs: Additional parameters.

        Returns:
            Generated response.
        """
        raise NotImplementedError("Subclass must implement _call_llm")

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation."""
        return len(text) // 4

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache hit/miss statistics.

        Returns:
            Dictionary with hit_rate, hits, misses.
        """
        total = self._stats["hits"] + self._stats["misses"]

        if total == 0:
            hit_rate = 0.0
        else:
            hit_rate = self._stats["hits"] / total

        return {
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "total_requests": total,
            "hit_rate": hit_rate,
        }

    def reset_stats(self) -> None:
        """Reset cache statistics."""
        self._stats = {"hits": 0, "misses": 0}
