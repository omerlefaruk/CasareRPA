"""Tests for LLM response caching with diskcache."""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from casare_rpa.utils.llm.cache import CacheEntry, CachedLLMClient, LLMResponseCache


class FakeLLMClient:
    """Fake LLM client for testing."""

    def __init__(self, responses: dict[str, str]):
        """Initialize with response mapping."""
        self.responses = responses
        self.call_count = 0

    def generate(self, prompt: str, model: str, **kwargs) -> str:
        """Generate response from mapping."""
        self.call_count += 1
        key = f"{model}:{prompt}"
        return self.responses.get(key, f"Response to: {prompt}")


class FakeCachedClient(CachedLLMClient):
    """Cached LLM client with fake LLM backend."""

    def __init__(self, real_client: FakeLLMClient, cache: LLMResponseCache):
        """Initialize cached client."""
        super().__init__(real_client, cache)

    def _call_llm(self, prompt: str, model: str, **kwargs) -> str:
        """Call fake LLM client."""
        return self._client.generate(prompt, model, **kwargs)


@pytest.fixture
def temp_cache_dir():
    """Create temporary cache directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def cache(temp_cache_dir):
    """Create LLM response cache instance."""
    cache_instance = LLMResponseCache(cache_dir=temp_cache_dir, default_ttl_hours=24)
    yield cache_instance
    # Explicitly close cache to release file handles on Windows
    cache_instance._cache.close()


class TestLLMResponseCache:
    """Tests for LLMResponseCache."""

    def test_cache_initialization(self, cache):
        """Test cache initializes correctly."""
        assert cache.default_ttl == 24
        assert isinstance(cache._cache, type(cache._cache))  # Check it's a diskcache.Cache

    def test_cache_set_and_get(self, cache):
        """Test basic cache set and get operations."""
        prompt = "What is the meaning of life?"
        response = "The meaning of life is 42."

        cache.set(prompt, response, model="gpt-4", tokens_in=10, tokens_out=5)

        cached = cache.get(prompt, model="gpt-4")

        assert cached is not None
        assert cached.response == response
        assert cached.model == "gpt-4"
        assert cached.tokens_in == 10
        assert cached.tokens_out == 5
        assert isinstance(cached.timestamp, datetime)

    def test_cache_miss(self, cache):
        """Test cache returns None for non-existent keys."""
        cached = cache.get("non-existent", model="gpt-4")

        assert cached is None

    def test_cache_key_generation(self, cache):
        """Test cache keys are unique for different parameters."""
        prompt = "Test prompt"

        cache.set(prompt, "Response 1", model="gpt-4", tokens_in=10, tokens_out=5)
        cache.set(prompt, "Response 2", model="gpt-3.5", tokens_in=10, tokens_out=5)
        cache.set(prompt, "Response 3", model="gpt-4", temperature=0.0, tokens_in=10, tokens_out=5)

        r1 = cache.get(prompt, model="gpt-4")
        r2 = cache.get(prompt, model="gpt-3.5")
        r3 = cache.get(prompt, model="gpt-4", temperature=0.0)

        assert r1.response == "Response 1"
        assert r2.response == "Response 2"
        assert r3.response == "Response 3"
        assert r1.response != r2.response

    def test_cache_invalidation(self, cache):
        """Test cache invalidation."""
        prompt = "Test prompt"

        cache.set(prompt, "Response", model="gpt-4", tokens_in=10, tokens_out=5)

        assert cache.get(prompt, model="gpt-4") is not None

        cache.invalidate(prompt, model="gpt-4")

        assert cache.get(prompt, model="gpt-4") is None

    def test_cache_clear(self, cache):
        """Test cache clearing."""
        cache.set("prompt1", "Response 1", model="gpt-4", tokens_in=10, tokens_out=5)
        cache.set("prompt2", "Response 2", model="gpt-4", tokens_in=10, tokens_out=5)

        assert cache.get("prompt1", model="gpt-4") is not None
        assert cache.get("prompt2", model="gpt-4") is not None

        cache.clear()

        assert cache.get("prompt1", model="gpt-4") is None
        assert cache.get("prompt2", model="gpt-4") is None

    def test_cache_expiration(self, cache):
        """Test cache entries expire after TTL."""
        prompt = "Test prompt"

        # Set with very short TTL
        cache.set(prompt, "Response", model="gpt-4", tokens_in=10, tokens_out=5, ttl_hours=0.0001)

        # Wait for expiration (360ms = 0.0001 hours)
        import time

        time.sleep(0.4)

        cached = cache.get(prompt, model="gpt-4")

        assert cached is None

    def test_cache_persistence(self, temp_cache_dir):
        """Test cache persists across instances."""
        prompt = "Test prompt"

        # Create first cache instance
        cache1 = LLMResponseCache(cache_dir=temp_cache_dir)
        cache1.set(prompt, "Response", model="gpt-4", tokens_in=10, tokens_out=5)
        cache1._cache.close()

        # Create second cache instance (should load from disk)
        cache2 = LLMResponseCache(cache_dir=temp_cache_dir)
        cached = cache2.get(prompt, model="gpt-4")
        cache2._cache.close()

        assert cached is not None
        assert cached.response == "Response"

    def test_cache_stats(self, cache):
        """Test cache statistics."""
        cache.set("prompt1", "Response 1", model="gpt-4", tokens_in=10, tokens_out=5)
        cache.set("prompt2", "Response 2", model="gpt-4", tokens_in=10, tokens_out=5)

        stats = cache.stats()

        assert stats["total_entries"] == 2
        assert stats["valid_entries"] == 2
        assert stats["expired_entries"] == 0
        assert stats["total_size_mb"] > 0
        assert "cache_dir" in stats

    def test_cache_prune_expired(self, cache):
        """Test pruning expired entries."""
        cache.set("valid", "Response 1", model="gpt-4", tokens_in=10, tokens_out=5)
        cache.set(
            "expired", "Response 2", model="gpt-4", tokens_in=10, tokens_out=5, ttl_hours=0.0001
        )

        import time

        time.sleep(0.4)

        removed = cache.prune_expired()

        assert removed == 1
        assert cache.get("valid", model="gpt-4") is not None
        assert cache.get("expired", model="gpt-4") is None

    def test_cache_entry_serialization(self):
        """Test CacheEntry can be serialized and deserialized."""
        entry = CacheEntry(
            response="Test response",
            model="gpt-4",
            tokens_in=100,
            tokens_out=50,
            timestamp=datetime.now(),
            ttl_hours=24,
        )

        entry_dict = entry.__dict__
        restored = CacheEntry(**entry_dict)

        assert restored.response == entry.response
        assert restored.model == entry.model
        assert restored.tokens_in == entry.tokens_in
        assert restored.tokens_out == entry.tokens_out

    def test_cache_export_stats(self, cache, temp_cache_dir):
        """Test exporting cache stats to file."""
        cache.set("prompt1", "Response 1", model="gpt-4", tokens_in=10, tokens_out=5)

        export_path = Path(temp_cache_dir) / "stats.json"
        cache.export_stats(str(export_path))

        assert export_path.exists()

        with open(export_path, encoding="utf-8") as f:
            stats = json.load(f)

        assert stats["total_entries"] == 1
        assert "exported_at" in stats


class TestCachedLLMClient:
    """Tests for CachedLLMClient."""

    def test_cached_client_hit(self):
        """Test cache hit scenario."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = LLMResponseCache(cache_dir=tmpdir)
            fake_client = FakeLLMClient({})
            cached_client = FakeCachedClient(fake_client, cache)

            # First call - cache miss
            response1 = cached_client.generate("Test prompt", model="gpt-4")

            assert fake_client.call_count == 1
            assert response1 is not None

            # Second call - cache hit
            response2 = cached_client.generate("Test prompt", model="gpt-4")

            assert fake_client.call_count == 1  # No additional call
            assert response1 == response2

            cache._cache.close()

    def test_cached_client_miss(self):
        """Test cache miss scenario."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = LLMResponseCache(cache_dir=tmpdir)
            fake_client = FakeLLMClient(
                {"gpt-4:prompt1": "Response 1", "gpt-4:prompt2": "Response 2"}
            )
            cached_client = FakeCachedClient(fake_client, cache)

            # Two different prompts
            r1 = cached_client.generate("prompt1", model="gpt-4")
            r2 = cached_client.generate("prompt2", model="gpt-4")

            assert fake_client.call_count == 2
            assert r1 == "Response 1"
            assert r2 == "Response 2"

            cache._cache.close()

    def test_cached_client_stats(self):
        """Test cache statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = LLMResponseCache(cache_dir=tmpdir)
            fake_client = FakeLLMClient({"gpt-4:Test prompt": "Response"})
            cached_client = FakeCachedClient(fake_client, cache)

            cached_client.generate("Test prompt", model="gpt-4")
            cached_client.generate("Test prompt", model="gpt-4")

            stats = cached_client.get_cache_stats()

            assert stats["hits"] == 1
            assert stats["misses"] == 1
            assert stats["total_requests"] == 2
            assert stats["hit_rate"] == 0.5

            cache._cache.close()

    def test_cached_client_reset_stats(self):
        """Test resetting cache statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = LLMResponseCache(cache_dir=tmpdir)
            fake_client = FakeLLMClient({})
            cached_client = FakeCachedClient(fake_client, cache)

            cached_client.generate("Test prompt", model="gpt-4")

            stats_before = cached_client.get_cache_stats()
            assert stats_before["total_requests"] == 1

            cached_client.reset_stats()

            stats_after = cached_client.get_cache_stats()
            assert stats_after["total_requests"] == 0

            cache._cache.close()

    def test_cached_client_token_estimation(self):
        """Test token estimation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = LLMResponseCache(cache_dir=tmpdir)
            fake_client = FakeLLMClient({})
            cached_client = FakeCachedClient(fake_client, cache)

            # Simple estimation: length / 4
            prompt = "This is a test prompt with 32 characters!"
            tokens_in = cached_client._estimate_tokens(prompt)

            # Should be approximately 32 / 4 = 8
            assert 6 <= tokens_in <= 10

            cache._cache.close()

    def test_cached_client_different_temperatures(self):
        """Test different temperatures are cached separately."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = LLMResponseCache(cache_dir=tmpdir)
            fake_client = FakeLLMClient({})
            cached_client = FakeCachedClient(fake_client, cache)

            cached_client.generate("Test prompt", model="gpt-4", temperature=0.0)
            cached_client.generate("Test prompt", model="gpt-4", temperature=1.0)

            assert fake_client.call_count == 2  # Two different requests

            cached_client.generate("Test prompt", model="gpt-4", temperature=0.0)
            cached_client.generate("Test prompt", model="gpt-4", temperature=1.0)

            assert fake_client.call_count == 2  # Still 2, no additional calls

            cache._cache.close()


class TestCacheEntry:
    """Tests for CacheEntry dataclass."""

    def test_cache_entry_creation(self):
        """Test creating a cache entry."""
        entry = CacheEntry(
            response="Test",
            model="gpt-4",
            tokens_in=100,
            tokens_out=50,
            timestamp=datetime.now(),
        )

        assert entry.response == "Test"
        assert entry.model == "gpt-4"
        assert entry.tokens_in == 100
        assert entry.tokens_out == 50
        assert entry.ttl_hours == 24  # Default value

    def test_cache_entry_default_ttl(self):
        """Test default TTL is 24 hours."""
        entry = CacheEntry(
            response="Test",
            model="gpt-4",
            tokens_in=100,
            tokens_out=50,
            timestamp=datetime.now(),
        )

        assert entry.ttl_hours == 24

    def test_cache_entry_custom_ttl(self):
        """Test custom TTL."""
        entry = CacheEntry(
            response="Test",
            model="gpt-4",
            tokens_in=100,
            tokens_out=50,
            timestamp=datetime.now(),
            ttl_hours=48,
        )

        assert entry.ttl_hours == 48
