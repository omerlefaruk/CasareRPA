"""Domain-level interface for LLM interactions used by the application layer."""

from __future__ import annotations

from typing import Any, Protocol


class ILLMResponse(Protocol):
    """Minimal response contract needed by application use cases."""

    content: str


class ILLMManager(Protocol):
    """Protocol for an LLM client/manager."""

    async def completion(
        self,
        prompt: str,
        model: str | None = None,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs: Any,
    ) -> ILLMResponse: ...
