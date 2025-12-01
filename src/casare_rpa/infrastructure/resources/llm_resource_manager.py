"""
CasareRPA - Infrastructure: LLM Resource Manager

Manages LLM client connections and provides unified API access via LiteLLM.
Supports OpenAI, Anthropic, Azure, and local models (Ollama).
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    pass


class LLMProvider(Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE = "azure"
    OLLAMA = "ollama"
    CUSTOM = "custom"


@dataclass
class LLMConfig:
    """Configuration for LLM client."""

    provider: LLMProvider = LLMProvider.OPENAI
    model: str = "gpt-4o-mini"
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    api_version: Optional[str] = None  # For Azure
    organization: Optional[str] = None  # For OpenAI
    timeout: float = 60.0
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class LLMUsageMetrics:
    """Track token usage and costs."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    total_requests: int = 0
    total_errors: int = 0
    total_cost_usd: float = 0.0
    last_request_time: Optional[float] = None

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
class ChatMessage:
    """Represents a chat message."""

    role: str  # "system", "user", "assistant"
    content: str
    name: Optional[str] = None

    def to_dict(self) -> Dict[str, str]:
        """Convert to LiteLLM message format."""
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
    raw_response: Optional[Dict[str, Any]] = None


@dataclass
class ConversationHistory:
    """Maintains conversation history for chat sessions."""

    conversation_id: str
    messages: List[ChatMessage] = field(default_factory=list)
    system_prompt: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation."""
        self.messages.append(ChatMessage(role=role, content=content))
        self.last_updated = time.time()

    def get_messages(self) -> List[Dict[str, str]]:
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
    _COST_PER_1K_TOKENS: Dict[str, Dict[str, float]] = {
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "claude-3-5-sonnet-latest": {"input": 0.003, "output": 0.015},
        "claude-3-opus-latest": {"input": 0.015, "output": 0.075},
        "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
    }

    # Model prefix to provider mapping for auto-detection
    _MODEL_TO_PROVIDER: Dict[str, str] = {
        "gpt-": "openai",
        "o1-": "openai",
        "claude-": "anthropic",
        "gemini-": "google",
        "mistral-": "mistral",
        "codestral-": "mistral",
        "llama-": "groq",
        "mixtral-": "groq",
        "deepseek-": "deepseek",
        "ollama/": "ollama",
    }

    def __init__(self) -> None:
        """Initialize LLM resource manager."""
        self._config: Optional[LLMConfig] = None
        self._metrics = LLMUsageMetrics()
        self._conversations: Dict[str, ConversationHistory] = {}
        self._litellm: Optional[Any] = None
        self._initialized = False
        self._api_key_store: Optional[Any] = None

    def configure(self, config: LLMConfig) -> None:
        """
        Configure the LLM client.

        Args:
            config: LLM configuration
        """
        self._config = config
        self._initialized = False
        logger.debug(
            f"LLM configured: provider={config.provider.value}, model={config.model}"
        )

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
                "LiteLLM is required for LLM nodes. "
                "Install it with: pip install litellm"
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

    def _get_api_key_for_provider(self, provider: LLMProvider) -> Optional[str]:
        """Get API key for a provider from the secure store."""
        provider_map = {
            LLMProvider.OPENAI: "openai",
            LLMProvider.ANTHROPIC: "anthropic",
            LLMProvider.AZURE: "azure",
            LLMProvider.OLLAMA: None,  # Ollama doesn't need API key
            LLMProvider.CUSTOM: None,
        }

        provider_name = provider_map.get(provider)
        if not provider_name:
            return None

        store = self._get_api_key_store()
        if store:
            return store.get_key(provider_name)
        return None

    def _detect_provider_from_model(self, model: str) -> Optional[str]:
        """Detect the provider from model name."""
        model_lower = model.lower()
        for prefix, provider in self._MODEL_TO_PROVIDER.items():
            if model_lower.startswith(prefix):
                return provider
        return None

    def _get_api_key_for_model(self, model: str) -> Optional[str]:
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
        return None

    def _get_model_string(self, model: Optional[str] = None) -> str:
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
            elif provider == LLMProvider.OLLAMA:
                # Ollama format: ollama/<model>
                return f"ollama/{model_name}"

        return model_name

    def _calculate_cost(
        self, model: str, prompt_tokens: int, completion_tokens: int
    ) -> float:
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
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
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

        # Get API key for this specific model (may differ from configured provider)
        api_key = self._get_api_key_for_model(model_str)

        try:
            # Pass API key directly if we have one for this model
            call_kwargs = {
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
                f"LLM completion: model={model_str}, "
                f"tokens={total_tokens}, cost=${cost:.4f}"
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
        conversation_id: Optional[str] = None,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
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

        # Get API key for this specific model
        api_key = self._get_api_key_for_model(model_str)

        try:
            call_kwargs = {
                "model": model_str,
                "messages": conv.get_messages(),
                "temperature": temperature,
                "max_tokens": max_tokens,
                **kwargs,
            }
            if api_key:
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
                f"LLM chat: conv={conversation_id}, model={model_str}, "
                f"tokens={total_tokens}"
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

    async def extract_structured(
        self,
        text: str,
        schema: Dict[str, Any],
        model: Optional[str] = None,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> Dict[str, Any]:
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

    def get_conversation(self, conversation_id: str) -> Optional[ConversationHistory]:
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
    def config(self) -> Optional[LLMConfig]:
        """Get current configuration."""
        return self._config

    async def cleanup(self) -> None:
        """Clean up resources."""
        self._conversations.clear()
        logger.debug("LLM resource manager cleaned up")

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
]
