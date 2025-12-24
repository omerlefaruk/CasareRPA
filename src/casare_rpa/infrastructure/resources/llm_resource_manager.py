"""
CasareRPA - Infrastructure: LLM Resource Manager

Manages LLM client connections and provides unified API access via LiteLLM.
Supports OpenAI, Anthropic, Azure, and local models (Ollama).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

from loguru import logger

if TYPE_CHECKING:
    pass


class LLMProvider(Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE = "azure"
    OLLAMA = "ollama"
    OPENROUTER = "openrouter"
    CUSTOM = "custom"


@dataclass
class LLMConfig:
    """Configuration for LLM client."""

    provider: LLMProvider = LLMProvider.OPENROUTER
    model: str = "openrouter/google/gemini-3-flash-preview"
    api_key: str | None = None
    api_base: str | None = None
    api_version: str | None = None  # For Azure
    organization: str | None = None  # For OpenAI
    timeout: float = 60.0
    max_retries: int = 3
    retry_delay: float = 1.0
    credential_id: str | None = None  # Store credential ID for dynamic token refresh


@dataclass
class LLMUsageMetrics:
    """Track token usage and costs."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    total_requests: int = 0
    total_errors: int = 0
    total_cost_usd: float = 0.0
    last_request_time: float | None = None

    def add_usage(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        cost_usd: float = 0.0,
    ) -> None:
        """Record token usage from a request."""
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.total_tokens += prompt_tokens + completion_tokens
        self.total_requests += 1
        self.total_cost_usd += cost_usd
        self.last_request_time = time.time()

    def record_error(self) -> None:
        """Record a failed request."""
        self.total_errors += 1
        self.last_request_time = time.time()


@dataclass
class ImageContent:
    """Represents an image in a message for vision models."""

    base64_data: str
    media_type: str = "image/png"  # image/png, image/jpeg, image/gif, image/webp

    def to_dict(self) -> dict[str, Any]:
        """Convert to LiteLLM image_url format."""
        return {
            "type": "image_url",
            "image_url": {
                "url": f"data:{self.media_type};base64,{self.base64_data}",
            },
        }


@dataclass
class ChatMessage:
    """Represents a chat message."""

    role: str  # "system", "user", "assistant"
    content: str
    name: str | None = None
    images: list[ImageContent] | None = None  # For vision models

    def to_dict(self) -> dict[str, Any]:
        """Convert to LiteLLM message format."""
        if self.images:
            # Multi-modal message with text and images
            content_parts: list[dict[str, Any]] = [{"type": "text", "text": self.content}]
            for img in self.images:
                content_parts.append(img.to_dict())
            msg: dict[str, Any] = {"role": self.role, "content": content_parts}
        else:
            # Text-only message
            msg = {"role": self.role, "content": self.content}

        if self.name:
            msg["name"] = self.name
        return msg


@dataclass
class LLMResponse:
    """Standardized LLM response."""

    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    finish_reason: str
    raw_response: dict[str, Any] | None = None


@dataclass
class ConversationHistory:
    """Maintains conversation history for chat sessions."""

    conversation_id: str
    messages: list[ChatMessage] = field(default_factory=list)
    system_prompt: str | None = None
    created_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation."""
        self.messages.append(ChatMessage(role=role, content=content))
        self.last_updated = time.time()

    def get_messages(self) -> list[dict[str, str]]:
        """Get all messages in LiteLLM format."""
        msgs = []
        if self.system_prompt:
            msgs.append({"role": "system", "content": self.system_prompt})
        msgs.extend([m.to_dict() for m in self.messages])
        return msgs

    def clear(self) -> None:
        """Clear conversation history (keep system prompt)."""
        self.messages.clear()
        self.last_updated = time.time()


class LLMResourceManager:
    """
    LLM resource manager - manages LiteLLM client and API access.

    This infrastructure component is responsible for:
    - Managing LLM API connections
    - Tracking token usage and costs
    - Handling rate limits with backoff
    - Managing conversation histories
    - Secure API key retrieval from encrypted store

    It contains NO domain logic - only infrastructure concerns.
    """

    # Cost per 1K tokens (approximate, varies by model)
    _COST_PER_1K_TOKENS: dict[str, dict[str, float]] = {
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "claude-3-5-sonnet-latest": {"input": 0.003, "output": 0.015},
        "claude-3-opus-latest": {"input": 0.015, "output": 0.075},
        "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
    }

    # Model prefix to provider mapping for auto-detection
    _MODEL_TO_PROVIDER: dict[str, str] = {
        "gpt-": "openai",
        "o1-": "openai",
        "claude-": "anthropic",
        "gemini-": "google",
        "mistral-": "mistral",
        "codestral-": "mistral",
        "llama-": "groq",
        "mixtral-": "groq",
        "deepseek-": "deepseek",
        "gemini": "google",
        "google": "google",
        "ollama/": "ollama",
        "openrouter/": "openrouter",
    }

    def __init__(self) -> None:
        """Initialize LLM resource manager."""
        self._config: LLMConfig | None = None
        self._metrics = LLMUsageMetrics()
        self._conversations: dict[str, ConversationHistory] = {}
        self._litellm: Any | None = None
        self._initialized = False
        self._api_key_store: Any | None = None

    def configure(self, config: LLMConfig) -> None:
        """
        Configure the LLM client.

        Args:
            config: LLM configuration
        """
        self._config = config
        self._initialized = False
        logger.debug(f"LLM configured: provider={config.provider.value}, model={config.model}")

    def _ensure_initialized(self) -> Any:
        """Ensure LiteLLM is imported and configured."""
        if self._initialized and self._litellm is not None:
            return self._litellm

        try:
            import litellm

            self._litellm = litellm

            # Configure LiteLLM based on provider
            if self._config:
                api_key = self._config.api_key or self._get_api_key_for_provider(
                    self._config.provider
                )

                if api_key:
                    if self._config.provider == LLMProvider.OPENAI:
                        litellm.api_key = api_key
                    elif self._config.provider == LLMProvider.ANTHROPIC:
                        litellm.anthropic_key = api_key

                if self._config.api_base:
                    litellm.api_base = self._config.api_base

            self._initialized = True
            logger.debug("LiteLLM initialized successfully")
            return litellm

        except ImportError as e:
            raise ImportError(
                "LiteLLM is required for LLM nodes. " "Install it with: pip install litellm"
            ) from e

    def _get_api_key_store(self) -> Any:
        """Get or create the credential store instance."""
        if self._api_key_store is None:
            try:
                # Try new unified credential store first
                from casare_rpa.infrastructure.security.credential_store import (
                    get_credential_store,
                )

                self._api_key_store = get_credential_store()
            except ImportError:
                try:
                    # Fall back to legacy API key store
                    from casare_rpa.infrastructure.security.api_key_store import (
                        get_api_key_store,
                    )

                    self._api_key_store = get_api_key_store()
                except ImportError:
                    logger.warning("No credential store available")
                    return None
        return self._api_key_store

    async def _resolve_api_key(self, config: LLMConfig | None = None) -> str | None:
        """
        Resolve the API key or Access Token to use.

        Handles:
        1. Explicit API key in config
        2. Dynamic OAuth token refresh via Credential ID
        3. Static API key from Credential Store
        4. Environment variables (fallback)

        Args:
            config: Optional config override

        Returns:
            Valid API key/token or None
        """
        cfg = config or self._config
        if not cfg:
            return None

        # 1. Explicit API key in config
        if cfg.api_key:
            return cfg.api_key

        # 2. Dynamic OAuth Token (if credential_id is present)
        if cfg.credential_id and cfg.credential_id != "auto":
            try:
                # Get credential info to determine type
                store = self._get_api_key_store()
                if not store:
                    return None

                info = store.get_credential_info(cfg.credential_id)
                if not info:
                    return None

                cred_type = info.get("type")
                self._using_google_oauth = cred_type == "google_oauth"  # Track for model string

                # Handle Google OAuth
                if cred_type == "google_oauth":
                    from casare_rpa.infrastructure.security.google_oauth import (
                        get_google_oauth_manager,
                    )

                    oauth_manager = await get_google_oauth_manager()
                    access_token = await oauth_manager.get_access_token(cfg.credential_id)
                    logger.debug("Got Google OAuth access token for Vertex AI")
                    return access_token

                # Handle API Key credential
                elif cred_type == "api_key":
                    return store.get_api_key(cfg.credential_id)

                # Handle OpenAI / Azure OAuth
                elif cred_type == "openai_oauth":
                    from casare_rpa.infrastructure.security.openai_oauth import (
                        get_openai_oauth_manager,
                    )

                    oauth_manager = await get_openai_oauth_manager()
                    return await oauth_manager.get_access_token(cfg.credential_id)

            except ImportError:
                pass
            except Exception as e:
                logger.warning(f"Failed to resolve OAuth token: {e}")

        # 3. Static API Key from Store (using provider)
        return self._get_api_key_for_provider(cfg.provider)

    def _get_api_key_for_provider(self, provider: LLMProvider) -> str | None:
        """Get API key for a provider from the secure store."""
        provider_map = {
            LLMProvider.OPENAI: "openai",
            LLMProvider.ANTHROPIC: "anthropic",
            LLMProvider.AZURE: "azure",
            LLMProvider.OLLAMA: None,  # Ollama doesn't need API key
            LLMProvider.OPENROUTER: "openrouter",
            LLMProvider.CUSTOM: None,
        }

        provider_name = provider_map.get(provider)
        if not provider_name:
            return None

        store = self._get_api_key_store()
        if store:
            # Check if we have a specific credential_id in config to look up directly
            if self._config and self._config.credential_id and self._config.credential_id != "auto":
                return store.get_api_key(self._config.credential_id)

            return store.get_key(provider_name)
        return None

    def _detect_provider_from_model(self, model: str) -> str | None:
        """Detect the provider from model name."""
        model_lower = model.lower()
        for prefix, provider in self._MODEL_TO_PROVIDER.items():
            if model_lower.startswith(prefix):
                return provider
        return None

    def _get_api_key_for_model(self, model: str) -> str | None:
        """Get API key based on model name auto-detection."""
        provider = self._detect_provider_from_model(model)
        if not provider or provider == "ollama":
            return None

        store = self._get_api_key_store()
        if store:
            # Try new credential store method first
            if hasattr(store, "get_api_key_by_provider"):
                return store.get_api_key_by_provider(provider)
            # Fall back to legacy get_key method
            return store.get_key(provider)

    def is_google_oauth(self) -> bool:
        """Check if currently configured/resolved to use Google OAuth."""
        return getattr(self, "_using_google_oauth", False)

    def _get_model_string(self, model: str | None = None) -> str:
        """Get the full model string for LiteLLM."""
        model_name = model or (self._config.model if self._config else "gpt-4o-mini")

        if self._config:
            provider = self._config.provider
            if provider == LLMProvider.AZURE:
                # Azure format: azure/<deployment-name>
                return f"azure/{model_name}"
            elif provider == LLMProvider.ANTHROPIC:
                # Anthropic models work directly
                return model_name
            elif provider == LLMProvider.OPENROUTER:
                # OpenRouter format: openrouter/<model>
                if not model_name.startswith("openrouter/"):
                    return f"openrouter/{model_name}"
                return model_name
            elif provider == LLMProvider.OLLAMA:
                # Ollama format: ollama/<model>
                return f"ollama/{model_name}"

        # Check if using Google OAuth
        if getattr(self, "_using_google_oauth", False):
            # Use gemini/ prefix but we will handle auth via headers
            if "gemini" in model_name.lower():
                clean_name = model_name
                for prefix in ["gemini/", "models/", "vertex_ai/"]:
                    if clean_name.startswith(prefix):
                        clean_name = clean_name[len(prefix) :]
                return f"gemini/{clean_name}"

        # Heuristic for Gemini models (often passed as "gemini-..." but need "gemini/" prefix for LiteLLM)
        if (
            (model_name.startswith("gemini") or "gemini" in model_name)
            and not model_name.startswith("gemini/")
            and not model_name.startswith("models/")
            and not model_name.startswith("vertex_ai/")
        ):
            return f"gemini/{model_name}"

        # Handle 'models/' prefix (Google AI Studio format) -> map to 'gemini/' for LiteLLM if needed,
        # but LiteLLM might handle 'vertex_ai/' or just 'gemini/'.
        # Usually LiteLLM expects `gemini/gemini-pro` etc.
        # If input is `models/gemini-1.5-pro`, LiteLLM with Google provider often takes just the model name or `gemini/...`.
        # Let's strip 'models/' and prepend 'gemini/' to be safe for the Google provider path.
        if model_name.startswith("models/"):
            clean_name = model_name.replace("models/", "")
            return f"gemini/{clean_name}"

        return model_name

    def _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate estimated cost for token usage."""
        # Normalize model name for lookup
        model_key = model.lower().replace("azure/", "").replace("ollama/", "")

        costs = self._COST_PER_1K_TOKENS.get(model_key, {"input": 0, "output": 0})
        input_cost = (prompt_tokens / 1000) * costs["input"]
        output_cost = (completion_tokens / 1000) * costs["output"]
        return input_cost + output_cost

    async def completion(
        self,
        prompt: str,
        model: str | None = None,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Generate a completion from a prompt.

        Args:
            prompt: User prompt
            model: Model to use (defaults to configured model)
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response
            **kwargs: Additional LiteLLM parameters

        Returns:
            LLMResponse with generated content
        """
        litellm = self._ensure_initialized()
        model_str = self._get_model_string(model)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Priority: 1) Configured/Resolved API key, 2) Auto-detected from model
        api_key = await self._resolve_api_key() or self._get_api_key_for_model(model_str)

        try:
            # Pass API key directly if we have one for this model
            call_kwargs = {
                "model": model_str,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                **kwargs,
            }

            if self.is_google_oauth():
                # For Google OAuth, we must pass the token as a Bearer header
                # and NOT as the api_key param (which LiteLLM uses for header/query param)
                call_kwargs["extra_headers"] = {"Authorization": f"Bearer {api_key}"}
                # LiteLLM needs a non-empty key to proceed for some providers, but for Gemini it might check.
                # We can pass safe dummy if needed, but let's try clean first.
            elif api_key:
                call_kwargs["api_key"] = api_key

            response = await litellm.acompletion(**call_kwargs)

            # Extract usage
            usage = response.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

            # Calculate cost
            cost = self._calculate_cost(model_str, prompt_tokens, completion_tokens)
            self._metrics.add_usage(prompt_tokens, completion_tokens, cost)

            # Extract content
            content = response["choices"][0]["message"]["content"]
            finish_reason = response["choices"][0].get("finish_reason", "stop")

            logger.debug(
                f"LLM completion: model={model_str}, " f"tokens={total_tokens}, cost=${cost:.4f}"
            )

            return LLMResponse(
                content=content,
                model=model_str,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                finish_reason=finish_reason,
                raw_response=response,
            )

        except Exception as e:
            self._metrics.record_error()
            logger.error(f"LLM completion failed: {e}")
            raise

    async def chat(
        self,
        message: str,
        conversation_id: str | None = None,
        model: str | None = None,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs: Any,
    ) -> tuple[LLMResponse, str]:
        """
        Send a chat message with conversation history.

        Args:
            message: User message
            conversation_id: Optional conversation ID for history
            model: Model to use
            system_prompt: System prompt (used for new conversations)
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            **kwargs: Additional parameters

        Returns:
            Tuple of (LLMResponse, conversation_id)
        """
        import uuid

        litellm = self._ensure_initialized()
        model_str = self._get_model_string(model)

        # Get or create conversation
        if conversation_id and conversation_id in self._conversations:
            conv = self._conversations[conversation_id]
        else:
            conversation_id = conversation_id or str(uuid.uuid4())[:8]
            conv = ConversationHistory(
                conversation_id=conversation_id,
                system_prompt=system_prompt,
            )
            self._conversations[conversation_id] = conv

        # Add user message
        conv.add_message("user", message)

        # Priority: 1) Configured/Resolved API key, 2) Auto-detected from model
        api_key = await self._resolve_api_key() or self._get_api_key_for_model(model_str)

        try:
            call_kwargs = {
                "model": model_str,
                "messages": conv.get_messages(),
                "temperature": temperature,
                "max_tokens": max_tokens,
                "max_tokens": max_tokens,
                **kwargs,
            }
            if self.is_google_oauth():
                call_kwargs["extra_headers"] = {"Authorization": f"Bearer {api_key}"}
            elif api_key:
                call_kwargs["api_key"] = api_key

            response = await litellm.acompletion(**call_kwargs)

            # Extract content and add to history
            content = response["choices"][0]["message"]["content"]
            conv.add_message("assistant", content)

            # Extract usage
            usage = response.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

            cost = self._calculate_cost(model_str, prompt_tokens, completion_tokens)
            self._metrics.add_usage(prompt_tokens, completion_tokens, cost)

            finish_reason = response["choices"][0].get("finish_reason", "stop")

            logger.debug(
                f"LLM chat: conv={conversation_id}, model={model_str}, " f"tokens={total_tokens}"
            )

            return (
                LLMResponse(
                    content=content,
                    model=model_str,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    finish_reason=finish_reason,
                    raw_response=response,
                ),
                conversation_id,
            )

        except Exception as e:
            self._metrics.record_error()
            # Remove failed user message from history
            if conv.messages and conv.messages[-1].role == "user":
                conv.messages.pop()
            logger.error(f"LLM chat failed: {e}")
            raise

    async def vision_completion(
        self,
        prompt: str,
        images: list[ImageContent],
        model: str | None = None,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Generate a completion from a prompt with images (vision).

        Args:
            prompt: User prompt describing what to analyze
            images: List of ImageContent objects with base64 encoded images
            model: Vision model to use (defaults to gpt-4o or configured model)
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response
            **kwargs: Additional LiteLLM parameters

        Returns:
            LLMResponse with generated content
        """
        litellm = self._ensure_initialized()

        # Default to vision-capable model
        if model is None:
            model = self._config.model if self._config else "gpt-4o"

        model_str = self._get_model_string(model)

        # Build multi-modal message with images
        user_content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        for img in images:
            user_content.append(img.to_dict())

        messages: list[dict[str, Any]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_content})

        # Priority: 1) Configured/Resolved API key, 2) Auto-detected from model
        api_key = await self._resolve_api_key() or self._get_api_key_for_model(model_str)

        try:
            call_kwargs: dict[str, Any] = {
                "model": model_str,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                **kwargs,
            }
            if api_key:
                call_kwargs["api_key"] = api_key

            response = await litellm.acompletion(**call_kwargs)

            # Extract usage
            usage = response.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

            # Calculate cost
            cost = self._calculate_cost(model_str, prompt_tokens, completion_tokens)
            self._metrics.add_usage(prompt_tokens, completion_tokens, cost)

            # Extract content
            content = response["choices"][0]["message"]["content"]
            finish_reason = response["choices"][0].get("finish_reason", "stop")

            logger.debug(
                f"LLM vision completion: model={model_str}, "
                f"images={len(images)}, tokens={total_tokens}, cost=${cost:.4f}"
            )

            return LLMResponse(
                content=content,
                model=model_str,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                finish_reason=finish_reason,
                raw_response=response,
            )

        except Exception as e:
            self._metrics.record_error()
            logger.error(f"LLM vision completion failed: {e}")
            raise

    async def extract_structured(
        self,
        text: str,
        schema: dict[str, Any],
        model: str | None = None,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Extract structured data from text using JSON schema.

        Args:
            text: Input text to extract from
            schema: JSON schema describing expected output
            model: Model to use
            temperature: Low for deterministic extraction
            **kwargs: Additional parameters

        Returns:
            Extracted data as dictionary
        """
        import json

        system_prompt = (
            "You are a data extraction assistant. Extract information from the provided text "
            "according to the JSON schema. Return ONLY valid JSON matching the schema, no explanation."
        )

        schema_str = json.dumps(schema, indent=2)
        prompt = f"""Extract data from the following text according to this JSON schema:

Schema:
```json
{schema_str}
```

Text to extract from:
```
{text}
```

Return ONLY the extracted JSON, no other text."""

        response = await self.completion(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
            temperature=temperature,
            **kwargs,
        )

        # Parse JSON from response
        content = response.content.strip()
        # Remove markdown code blocks if present
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

        return json.loads(content)

    def get_conversation(self, conversation_id: str) -> ConversationHistory | None:
        """Get a conversation by ID."""
        return self._conversations.get(conversation_id)

    def clear_conversation(self, conversation_id: str) -> bool:
        """Clear a conversation's history."""
        if conversation_id in self._conversations:
            self._conversations[conversation_id].clear()
            return True
        return False

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation entirely."""
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            return True
        return False

    @property
    def metrics(self) -> LLMUsageMetrics:
        """Get usage metrics."""
        return self._metrics

    @property
    def config(self) -> LLMConfig | None:
        """Get current configuration."""
        return self._config

    async def cleanup(self) -> None:
        """Clean up resources including litellm async HTTP clients."""
        self._conversations.clear()

        # Clean up litellm's internal async HTTP clients
        if self._initialized:
            try:
                from litellm.llms.custom_httpx.async_client_cleanup import (
                    close_litellm_async_clients,
                )

                await close_litellm_async_clients()
                logger.debug("litellm async clients cleaned up")
            except ImportError:
                # Cleanup module not available in this litellm version
                pass
            except Exception as e:
                logger.debug(f"litellm cleanup: {e}")

        self._initialized = False
        logger.debug("LLM resource manager cleaned up")

    def dispose(self) -> None:
        """
        Synchronous disposal for DI container cleanup.

        This method is called by DIContainer during application shutdown.
        It runs the async cleanup in a new event loop since the main loop
        may already be closed.
        """
        import asyncio

        self._conversations.clear()

        if self._initialized:
            try:
                from litellm.llms.custom_httpx.async_client_cleanup import (
                    close_litellm_async_clients,
                )

                # Try to run cleanup - create new event loop if needed
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Can't run sync in running loop, schedule it
                        loop.create_task(close_litellm_async_clients())
                    else:
                        loop.run_until_complete(close_litellm_async_clients())
                except RuntimeError:
                    # No event loop, create a temporary one
                    loop = asyncio.new_event_loop()
                    try:
                        loop.run_until_complete(close_litellm_async_clients())
                    finally:
                        loop.close()

                logger.debug("litellm async clients disposed")
            except ImportError:
                pass
            except Exception as e:
                logger.debug(f"litellm dispose: {e}")

        self._initialized = False
        logger.debug("LLM resource manager disposed")

    def __repr__(self) -> str:
        """String representation."""
        provider = self._config.provider.value if self._config else "not configured"
        model = self._config.model if self._config else "none"
        return (
            f"LLMResourceManager("
            f"provider={provider}, "
            f"model={model}, "
            f"conversations={len(self._conversations)}, "
            f"total_requests={self._metrics.total_requests})"
        )


__all__ = [
    "LLMResourceManager",
    "LLMConfig",
    "LLMProvider",
    "LLMResponse",
    "LLMUsageMetrics",
    "ChatMessage",
    "ConversationHistory",
    "ImageContent",
]
