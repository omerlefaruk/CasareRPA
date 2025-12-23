"""
CasareRPA - Infrastructure: Embedding Manager

Manages text embeddings via LiteLLM for vector similarity operations.
Supports OpenAI, Azure, and local embedding models.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from loguru import logger

if TYPE_CHECKING:
    pass


@dataclass
class EmbeddingResult:
    """Result of an embedding operation."""

    embedding: list[float]
    model: str
    tokens_used: int
    cached: bool = False


@dataclass
class BatchEmbeddingResult:
    """Result of a batch embedding operation."""

    embeddings: list[list[float]]
    model: str
    total_tokens: int
    count: int


@dataclass
class EmbeddingMetrics:
    """Track embedding usage metrics."""

    total_requests: int = 0
    total_tokens: int = 0
    total_texts: int = 0
    cache_hits: int = 0
    total_errors: int = 0
    last_request_time: float | None = None

    def add_request(self, tokens: int, texts: int, cached: bool = False) -> None:
        """Record an embedding request."""
        self.total_requests += 1
        self.total_tokens += tokens
        self.total_texts += texts
        if cached:
            self.cache_hits += 1
        self.last_request_time = time.time()

    def record_error(self) -> None:
        """Record a failed request."""
        self.total_errors += 1
        self.last_request_time = time.time()


@dataclass
class EmbeddingConfig:
    """Configuration for embedding operations."""

    model: str = "text-embedding-3-small"
    api_key: str | None = None
    api_base: str | None = None
    dimensions: int | None = None  # For models that support dimension reduction
    batch_size: int = 100
    max_retries: int = 3
    retry_delay: float = 1.0
    enable_cache: bool = True
    cache_ttl: int = 3600  # 1 hour


class EmbeddingManager:
    """
    Manages text embeddings via LiteLLM.

    Features:
    - Multiple embedding model support (OpenAI, Azure, local)
    - Batch embedding for efficiency
    - Optional caching for repeated texts
    - Token usage tracking
    - Retry logic with exponential backoff
    """

    # Model to dimension mapping (approximate)
    _MODEL_DIMENSIONS: dict[str, int] = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }

    def __init__(self, config: EmbeddingConfig | None = None) -> None:
        """
        Initialize embedding manager.

        Args:
            config: Embedding configuration
        """
        self._config = config or EmbeddingConfig()
        self._metrics = EmbeddingMetrics()
        self._cache: dict[str, dict[str, Any]] = {}  # hash -> {embedding, timestamp}
        self._litellm: Any | None = None
        self._initialized = False

    def configure(self, config: EmbeddingConfig) -> None:
        """Update configuration."""
        self._config = config
        self._initialized = False
        logger.debug(f"EmbeddingManager configured: model={config.model}")

    def _ensure_initialized(self) -> Any:
        """Ensure LiteLLM is imported and available."""
        if self._initialized and self._litellm is not None:
            return self._litellm

        try:
            import litellm

            self._litellm = litellm

            # Configure API key if provided
            if self._config.api_key:
                litellm.api_key = self._config.api_key

            if self._config.api_base:
                litellm.api_base = self._config.api_base

            self._initialized = True
            logger.debug("LiteLLM embedding support initialized")
            return litellm

        except ImportError as e:
            raise ImportError(
                "LiteLLM is required for embedding operations. "
                "Install it with: pip install litellm"
            ) from e

    def _get_cache_key(self, text: str, model: str) -> str:
        """Generate cache key for text+model combination."""
        content = f"{model}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()[:32]

    def _check_cache(self, text: str, model: str) -> list[float] | None:
        """Check if embedding is cached and not expired."""
        if not self._config.enable_cache:
            return None

        key = self._get_cache_key(text, model)
        if key not in self._cache:
            return None

        entry = self._cache[key]
        if time.time() - entry["timestamp"] > self._config.cache_ttl:
            del self._cache[key]
            return None

        return entry["embedding"]

    def _store_cache(self, text: str, model: str, embedding: list[float]) -> None:
        """Store embedding in cache."""
        if not self._config.enable_cache:
            return

        key = self._get_cache_key(text, model)
        self._cache[key] = {
            "embedding": embedding,
            "timestamp": time.time(),
        }

    async def embed_text(
        self,
        text: str,
        model: str | None = None,
    ) -> EmbeddingResult:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed
            model: Model to use (defaults to configured model)

        Returns:
            EmbeddingResult with embedding vector
        """
        model = model or self._config.model

        # Check cache
        cached = self._check_cache(text, model)
        if cached is not None:
            self._metrics.add_request(0, 1, cached=True)
            return EmbeddingResult(
                embedding=cached,
                model=model,
                tokens_used=0,
                cached=True,
            )

        litellm = self._ensure_initialized()

        try:
            # Build request kwargs
            kwargs: dict[str, Any] = {
                "model": model,
                "input": [text],
            }

            if self._config.api_key:
                kwargs["api_key"] = self._config.api_key

            if self._config.dimensions and "text-embedding-3" in model:
                kwargs["dimensions"] = self._config.dimensions

            response = await litellm.aembedding(**kwargs)

            # Extract embedding
            embedding = response["data"][0]["embedding"]
            tokens = response.get("usage", {}).get("total_tokens", 0)

            # Cache result
            self._store_cache(text, model, embedding)

            self._metrics.add_request(tokens, 1)
            logger.debug(f"Embedding generated: model={model}, tokens={tokens}")

            return EmbeddingResult(
                embedding=embedding,
                model=model,
                tokens_used=tokens,
                cached=False,
            )

        except Exception as e:
            self._metrics.record_error()
            logger.error(f"Embedding error: {e}")
            raise

    async def embed_batch(
        self,
        texts: list[str],
        model: str | None = None,
    ) -> BatchEmbeddingResult:
        """
        Generate embeddings for multiple texts efficiently.

        Handles batching automatically based on configured batch_size.

        Args:
            texts: List of texts to embed
            model: Model to use

        Returns:
            BatchEmbeddingResult with all embeddings
        """
        if not texts:
            return BatchEmbeddingResult(
                embeddings=[],
                model=model or self._config.model,
                total_tokens=0,
                count=0,
            )

        model = model or self._config.model
        litellm = self._ensure_initialized()

        all_embeddings: list[list[float]] = []
        total_tokens = 0

        # Process in batches
        for i in range(0, len(texts), self._config.batch_size):
            batch = texts[i : i + self._config.batch_size]

            # Check cache for each text
            batch_to_embed = []
            batch_indices = []
            cached_results: dict[int, list[float]] = {}

            for j, text in enumerate(batch):
                cached = self._check_cache(text, model)
                if cached is not None:
                    cached_results[j] = cached
                else:
                    batch_to_embed.append(text)
                    batch_indices.append(j)

            # Embed non-cached texts
            if batch_to_embed:
                try:
                    kwargs: dict[str, Any] = {
                        "model": model,
                        "input": batch_to_embed,
                    }

                    if self._config.api_key:
                        kwargs["api_key"] = self._config.api_key

                    if self._config.dimensions and "text-embedding-3" in model:
                        kwargs["dimensions"] = self._config.dimensions

                    response = await litellm.aembedding(**kwargs)

                    # Extract and cache embeddings
                    for idx, data in enumerate(response["data"]):
                        embedding = data["embedding"]
                        original_idx = batch_indices[idx]
                        cached_results[original_idx] = embedding
                        self._store_cache(batch_to_embed[idx], model, embedding)

                    total_tokens += response.get("usage", {}).get("total_tokens", 0)

                except Exception as e:
                    self._metrics.record_error()
                    logger.error(f"Batch embedding error: {e}")
                    raise

            # Reconstruct ordered results
            for j in range(len(batch)):
                all_embeddings.append(cached_results[j])

        self._metrics.add_request(total_tokens, len(texts))
        logger.debug(
            f"Batch embedding: {len(texts)} texts, " f"tokens={total_tokens}, model={model}"
        )

        return BatchEmbeddingResult(
            embeddings=all_embeddings,
            model=model,
            total_tokens=total_tokens,
            count=len(texts),
        )

    def get_model_dimensions(self, model: str | None = None) -> int:
        """Get the embedding dimensions for a model."""
        model = model or self._config.model

        if self._config.dimensions:
            return self._config.dimensions

        return self._MODEL_DIMENSIONS.get(model, 1536)

    def clear_cache(self) -> int:
        """Clear the embedding cache. Returns number of entries cleared."""
        count = len(self._cache)
        self._cache.clear()
        logger.debug(f"Embedding cache cleared: {count} entries")
        return count

    @property
    def metrics(self) -> EmbeddingMetrics:
        """Get usage metrics."""
        return self._metrics

    @property
    def config(self) -> EmbeddingConfig:
        """Get current configuration."""
        return self._config

    @property
    def cache_size(self) -> int:
        """Get current cache size."""
        return len(self._cache)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"EmbeddingManager("
            f"model={self._config.model}, "
            f"requests={self._metrics.total_requests}, "
            f"cache_size={len(self._cache)})"
        )


# Module-level singleton for convenience
_default_manager: EmbeddingManager | None = None


def get_embedding_manager() -> EmbeddingManager:
    """Get or create the default embedding manager."""
    global _default_manager
    if _default_manager is None:
        _default_manager = EmbeddingManager()
    return _default_manager


__all__ = [
    "EmbeddingManager",
    "EmbeddingConfig",
    "EmbeddingResult",
    "BatchEmbeddingResult",
    "EmbeddingMetrics",
    "get_embedding_manager",
]
