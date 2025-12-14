"""
LLM Model Provider Service.

Fetches and caches available models from LLM provider APIs.
Provides model filtering by provider based on stored credentials.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import threading

from loguru import logger

from casare_rpa.infrastructure.http import UnifiedHttpClient, UnifiedHttpClientConfig


@dataclass
class ModelInfo:
    """Information about an LLM model."""

    id: str
    name: str
    provider: str
    context_length: Optional[int] = None
    created: Optional[int] = None
    description: Optional[str] = None


@dataclass
class ModelCache:
    """Cache for provider models."""

    models: List[ModelInfo] = field(default_factory=list)
    last_updated: float = 0
    ttl: float = 3600  # 1 hour cache


# Provider name to credential provider ID mapping
PROVIDER_ID_MAP = {
    "openai": "openai",
    "anthropic": "anthropic",
    "google": "google",
    "mistral": "mistral",
    "groq": "groq",
    "deepseek": "deepseek",
    "cohere": "cohere",
    "together": "together",
    "perplexity": "perplexity",
    "azure": "azure",
    "ollama": "ollama",
}

# Default fallback models when API is unavailable
DEFAULT_MODELS: Dict[str, List[str]] = {
    "openai": [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-4",
        "gpt-3.5-turbo",
        "o1-preview",
        "o1-mini",
        "o3-mini",
    ],
    "anthropic": [
        "claude-3-5-sonnet-latest",
        "claude-3-5-haiku-latest",
        "claude-3-opus-latest",
        "claude-sonnet-4-20250514",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
    ],
    "google": [
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b",
    ],
    "mistral": [
        "mistral-large-latest",
        "mistral-small-latest",
        "codestral-latest",
        "ministral-8b-latest",
        "ministral-3b-latest",
        "pixtral-large-latest",
    ],
    "groq": [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "llama-3.2-90b-vision-preview",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
    ],
    "deepseek": [
        "deepseek-chat",
        "deepseek-coder",
        "deepseek-reasoner",
    ],
    "cohere": [
        "command-r-plus",
        "command-r",
        "command",
        "command-light",
    ],
    "together": [
        "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo",
        "Qwen/Qwen2.5-72B-Instruct-Turbo",
        "mistralai/Mixtral-8x22B-Instruct-v0.1",
    ],
    "perplexity": [
        "llama-3.1-sonar-small-128k-online",
        "llama-3.1-sonar-large-128k-online",
        "llama-3.1-sonar-huge-128k-online",
    ],
    "ollama": [
        "ollama/llama3.2",
        "ollama/llama3.1",
        "ollama/mistral",
        "ollama/codellama",
        "ollama/phi3",
        "ollama/gemma2",
    ],
}


class LLMModelProvider:
    """
    Service for fetching and caching LLM models from providers.

    Features:
    - Fetches live models from provider APIs
    - Caches results with configurable TTL
    - Falls back to defaults on API failure
    - Filters models by credential provider
    """

    _instance: Optional["LLMModelProvider"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "LLMModelProvider":
        """Singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Initialize the model provider."""
        if self._initialized:
            return

        self._cache: Dict[str, ModelCache] = {}
        self._executor = ThreadPoolExecutor(max_workers=3)
        self._initialized = True
        logger.debug("LLMModelProvider initialized")

    def get_models_for_provider(
        self, provider: str, api_key: Optional[str] = None, use_cache: bool = True
    ) -> List[str]:
        """
        Get available models for a provider.

        Args:
            provider: Provider name (openai, anthropic, google, etc.)
            api_key: Optional API key for fetching live models
            use_cache: Whether to use cached models

        Returns:
            List of model IDs
        """
        provider = provider.lower()

        # Check cache
        if use_cache and provider in self._cache:
            cache = self._cache[provider]
            if time.time() - cache.last_updated < cache.ttl:
                return [m.id for m in cache.models]

        # Try to fetch live models if we have an API key
        if api_key:
            try:
                models = self._fetch_models(provider, api_key)
                if models:
                    self._cache[provider] = ModelCache(
                        models=[
                            ModelInfo(id=m, name=m, provider=provider) for m in models
                        ],
                        last_updated=time.time(),
                    )
                    return models
            except Exception as e:
                logger.warning(f"Failed to fetch models for {provider}: {e}")

        # Return defaults
        return DEFAULT_MODELS.get(provider, [])

    def get_models_for_credential(self, credential_name: str) -> List[str]:
        """
        Get models filtered by credential's provider.

        Args:
            credential_name: Name of the stored credential

        Returns:
            List of model IDs for that provider
        """
        if credential_name == "Auto-detect from model":
            # Return all models
            return self.get_all_models()

        # Get provider from credential
        provider, api_key = self._get_provider_from_credential(credential_name)
        if not provider:
            return self.get_all_models()

        return self.get_models_for_provider(provider, api_key)

    def get_all_models(self) -> List[str]:
        """Get all available models from all providers."""
        all_models = []
        for provider_models in DEFAULT_MODELS.values():
            all_models.extend(provider_models)
        return all_models

    def get_provider_for_credential(self, credential_name: str) -> Optional[str]:
        """Get the provider associated with a credential."""
        if credential_name == "Auto-detect from model":
            return None

        provider, _ = self._get_provider_from_credential(credential_name)
        return provider

    def _get_provider_from_credential(
        self, credential_name: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """Get provider and API key from credential store."""
        try:
            from casare_rpa.infrastructure.security.credential_store import (
                get_credential_store,
            )

            store = get_credential_store()
            credentials = store.list_credentials(category="llm")

            for cred in credentials:
                if cred["name"] == credential_name:
                    data = store.get_credential(cred["id"])
                    if data:
                        provider = data.get("provider")
                        api_key = data.get("api_key")
                        return provider, api_key

        except Exception as e:
            logger.warning(f"Failed to get credential info: {e}")

        return None, None

    def _fetch_models(self, provider: str, api_key: str) -> List[str]:
        """Fetch live models from provider API using UnifiedHttpClient."""
        fetch_configs = {
            "openai": {
                "url": "https://api.openai.com/v1/models",
                "headers": {"Authorization": f"Bearer {api_key}"},
                "parser": self._parse_openai_models,
            },
            "anthropic": {
                # Anthropic doesn't have a models endpoint, use defaults
                "skip": True,
            },
            "google": {
                "url": "https://generativelanguage.googleapis.com/v1/models",
                "headers": {"X-Goog-Api-Key": api_key},
                "parser": self._parse_google_models,
            },
            "mistral": {
                "url": "https://api.mistral.ai/v1/models",
                "headers": {"Authorization": f"Bearer {api_key}"},
                "parser": self._parse_openai_models,  # Same format
            },
            "groq": {
                "url": "https://api.groq.com/openai/v1/models",
                "headers": {"Authorization": f"Bearer {api_key}"},
                "parser": self._parse_openai_models,
            },
            "deepseek": {
                "url": "https://api.deepseek.com/v1/models",
                "headers": {"Authorization": f"Bearer {api_key}"},
                "parser": self._parse_openai_models,
            },
            "cohere": {
                "url": "https://api.cohere.ai/v1/models",
                "headers": {"Authorization": f"Bearer {api_key}"},
                "parser": self._parse_cohere_models,
            },
            "together": {
                "url": "https://api.together.xyz/v1/models",
                "headers": {"Authorization": f"Bearer {api_key}"},
                "parser": self._parse_together_models,
            },
        }

        config = fetch_configs.get(provider)
        if not config or config.get("skip"):
            return DEFAULT_MODELS.get(provider, [])

        try:
            # Run async request in sync context
            return self._fetch_models_async(config)
        except Exception as e:
            logger.warning(f"API request failed for {provider}: {e}")
            return DEFAULT_MODELS.get(provider, [])

    def _fetch_models_async(self, config: Dict[str, Any]) -> List[str]:
        """Execute async HTTP request in sync context."""

        async def _do_fetch() -> List[str]:
            client_config = UnifiedHttpClientConfig(
                default_timeout=10.0,
                max_retries=2,
            )
            async with UnifiedHttpClient(client_config) as client:
                response = await client.get(
                    config["url"],
                    headers=config["headers"],
                )
                if response.status == 200:
                    data = await response.json()
                    return config["parser"](data)
                return []

        # Create new event loop for sync context (called from ThreadPoolExecutor)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, use run_coroutine_threadsafe
                import concurrent.futures

                future = asyncio.run_coroutine_threadsafe(_do_fetch(), loop)
                return future.result(timeout=15.0)
            else:
                return loop.run_until_complete(_do_fetch())
        except RuntimeError:
            # No event loop - create a new one
            return asyncio.run(_do_fetch())

    def _parse_openai_models(self, data: Dict[str, Any]) -> List[str]:
        """Parse OpenAI-style models response."""
        models = []
        for model in data.get("data", []):
            model_id = model.get("id", "")
            # Filter to chat/completion models only
            if any(
                prefix in model_id
                for prefix in ["gpt-", "o1-", "o3-", "chatgpt-", "text-"]
            ):
                models.append(model_id)
        return sorted(models, reverse=True)[:20]  # Latest first, limit to 20

    def _parse_google_models(self, data: Dict[str, Any]) -> List[str]:
        """Parse Google AI models response."""
        models = []
        for model in data.get("models", []):
            name = model.get("name", "")
            # Extract model ID from "models/gemini-1.5-pro"
            if name.startswith("models/"):
                model_id = name.replace("models/", "")
                # Filter to generative models
                if "gemini" in model_id:
                    models.append(model_id)
        return sorted(models, reverse=True)[:15]

    def _parse_cohere_models(self, data: Dict[str, Any]) -> List[str]:
        """Parse Cohere models response."""
        models = []
        for model in data.get("models", []):
            model_id = model.get("name", "")
            if model_id:
                models.append(model_id)
        return models[:15]

    def _parse_together_models(self, data: Dict[str, Any]) -> List[str]:
        """Parse Together AI models response."""
        models = []
        for model in data:
            model_id = model.get("id", "")
            # Filter to chat models
            if model.get("type") == "chat":
                models.append(model_id)
        return models[:20]

    def refresh_cache(self, provider: Optional[str] = None) -> None:
        """
        Refresh the model cache.

        Args:
            provider: Specific provider to refresh, or None for all
        """
        if provider:
            if provider in self._cache:
                del self._cache[provider]
        else:
            self._cache.clear()

        logger.debug(f"Model cache refreshed for: {provider or 'all providers'}")


def get_model_provider() -> LLMModelProvider:
    """Get the singleton model provider instance."""
    return LLMModelProvider()


# Convenience functions for visual nodes
def get_models_for_credential(credential_name: str) -> List[str]:
    """Get models filtered by credential's provider."""
    return get_model_provider().get_models_for_credential(credential_name)


def get_all_models() -> List[str]:
    """Get all available models."""
    return get_model_provider().get_all_models()


def get_provider_for_credential(credential_name: str) -> Optional[str]:
    """Get the provider for a credential."""
    return get_model_provider().get_provider_for_credential(credential_name)
