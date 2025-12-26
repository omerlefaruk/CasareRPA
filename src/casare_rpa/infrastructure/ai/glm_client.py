"""
CasareRPA - Infrastructure: GLM (Z.ai) Client

Client for Z.ai GLM Coding Plan API.
OpenAI-compatible API with Bearer token authentication.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# API endpoints
GLM_API_BASE_CODING = "https://api.z.ai/api/coding/paas/v4"
GLM_API_BASE_GENERAL = "https://api.z.ai/api/paas/v4"

# Model constants
MODEL_GLM_4_7 = "glm-4.7"
MODEL_GLM_4_6 = "glm-4.6"
MODEL_GLM_4_5 = "glm-4.5"
MODEL_GLM_4_FLASH = "glm-4-flash"
MODEL_GLM_4_FLASHX = "glm-4-flashx"

# Default timeout (seconds)
DEFAULT_TIMEOUT = 60


@dataclass(frozen=True)
class GLMResponse:
    """Response from GLM API."""

    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    finish_reason: str
    raw_response: dict[str, Any] | None = None


class GLMClientError(Exception):
    """Base exception for GLM client errors."""


class RateLimitError(GLMClientError):
    """Raised when rate limit is exceeded."""


class GLMClient:
    """
    Client for Z.ai GLM Coding Plan API.

    Uses OpenAI-compatible API format with Bearer token authentication.
    """

    def __init__(
        self,
        api_key: str,
        model: str = MODEL_GLM_4_7,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        use_coding_endpoint: bool = True,
    ) -> None:
        """
        Initialize GLM client.

        Args:
            api_key: Z.ai API key (format: id.secret)
            model: Model to use (glm-4.7, glm-4.6, etc.)
            base_url: Custom base URL (defaults to coding endpoint)
            timeout: Request timeout in seconds
            temperature: Default sampling temperature
            max_tokens: Default max tokens
            use_coding_endpoint: Use coding-specific endpoint
        """
        self._api_key = api_key
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._timeout = timeout

        if base_url:
            self.base_url = base_url
        else:
            self.base_url = GLM_API_BASE_CODING if use_coding_endpoint else GLM_API_BASE_GENERAL

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        model: str | None = None,
    ) -> GLMResponse:
        """
        Generate text completion from prompt.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            model: Model override

        Returns:
            GLMResponse with generated content

        Raises:
            GLMClientError: On API errors
            RateLimitError: On rate limit exceeded
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        return await self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model,
        )

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        model: str | None = None,
    ) -> GLMResponse:
        """
        Chat completion with message history.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            model: Model override

        Returns:
            GLMResponse with generated content

        Raises:
            GLMClientError: On API errors
            RateLimitError: On rate limit exceeded
        """
        from casare_rpa.infrastructure.http import UnifiedHttpClient, UnifiedHttpClientConfig

        model = model or self._model
        temperature = temperature if temperature is not None else self._temperature
        max_tokens = max_tokens if max_tokens is not None else self._max_tokens

        body = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        # Configure client for GLM API
        config = UnifiedHttpClientConfig(
            enable_ssrf_protection=True,  # External API
            max_retries=2,
            default_timeout=self._timeout,
            rate_limit_requests=60,  # GLM rate limit
            rate_limit_window=60.0,
        )

        async with UnifiedHttpClient(config) as client:
            try:
                response = await client.post(url, json=body, headers=headers)

                # Handle rate limiting
                if response.status == 429:
                    retry_after = response.headers.get("Retry-After", "60")
                    raise RateLimitError(
                        f"GLM rate limit exceeded. Retry after {retry_after} seconds."
                    )

                # Handle other errors
                if response.status not in (200, 201):
                    error_text = await response.text()
                    raise GLMClientError(
                        f"GLM API error: status={response.status}, response={error_text}"
                    )

                data = await response.json()

            except Exception as e:
                if isinstance(e, RateLimitError | GLMClientError):
                    raise
                raise GLMClientError(f"GLM network error: {e}") from e

        # Parse response
        try:
            choice = data["choices"][0]
            message = choice["message"]
            usage = data.get("usage", {})

            return GLMResponse(
                content=message.get("content", ""),
                model=data.get("model", model),
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                finish_reason=choice.get("finish_reason", "stop"),
                raw_response=data,
            )

        except (KeyError, IndexError) as e:
            raise GLMClientError(f"Invalid GLM response format: {e}") from e

    async def analyze_image(
        self,
        prompt: str,
        image_base64: str,
        model: str | None = None,
    ) -> GLMResponse:
        """
        Analyze an image with vision model.

        Args:
            prompt: Analysis prompt
            image_base64: Base64-encoded image data
            model: Model override (must support vision)

        Returns:
            GLMResponse with analysis

        Raises:
            GLMClientError: On API errors or if model doesn't support vision
        """
        # GLM-4.7 and above support vision
        vision_models = {MODEL_GLM_4_7, MODEL_GLM_4_6, MODEL_GLM_4_5}
        model = model or self._model

        if model not in vision_models:
            raise GLMClientError(f"Model {model} does not support vision. Use {MODEL_GLM_4_7}")

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_base64}"},
                    },
                ],
            }
        ]

        return await self.chat(messages=messages, model=model)

    async def close(self) -> None:
        """Close any open sessions (no-op for UnifiedHttpClient context manager)."""
        pass

    @property
    def model(self) -> str:
        """Get current model."""
        return self._model

    def __repr__(self) -> str:
        """String representation."""
        return f"GLMClient(model={self._model}, base_url={self.base_url})"


__all__ = [
    "GLMClient",
    "GLMClientError",
    "GLMResponse",
    "RateLimitError",
    "MODEL_GLM_4_7",
    "MODEL_GLM_4_6",
    "MODEL_GLM_4_5",
    "MODEL_GLM_4_FLASH",
    "MODEL_GLM_4_FLASHX",
]
