"""
Antigravity API client for LLM requests.

Handles request transformation, SSE streaming, and response processing
for the Antigravity Cloud Code Assist API.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING, AsyncIterator

from loguru import logger

from casare_rpa.infrastructure.security.antigravity_accounts import (
    AntigravityAccountManager,
    ManagedAccount,
    get_antigravity_account_manager,
)
from casare_rpa.infrastructure.security.antigravity_constants import (
    ANTIGRAVITY_DEFAULT_PROJECT_ID,
    ANTIGRAVITY_ENDPOINT,
    ANTIGRAVITY_ENDPOINT_FALLBACKS,
    ANTIGRAVITY_HEADERS,
    GEMINI_CLI_HEADERS,
    AntigravityModel,
    HeaderStyle,
    ModelFamily,
    get_headers_for_style,
    get_model_family,
    is_claude_model,
)

if TYPE_CHECKING:
    from typing import Any


@dataclass
class AntigravityRequest:
    model: str
    messages: list[dict[str, Any]]
    max_tokens: int = 4096
    temperature: float = 0.7
    stream: bool = True
    tools: list[dict[str, Any]] | None = None
    system: str | None = None


@dataclass
class AntigravityStreamChunk:
    content: str | None = None
    thinking: str | None = None
    tool_call: dict[str, Any] | None = None
    finish_reason: str | None = None
    usage: dict[str, int] | None = None


@dataclass
class AntigravityResponse:
    content: str
    thinking: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    finish_reason: str = "stop"
    usage: dict[str, int] | None = None


def _generate_synthetic_project_id() -> str:
    adjectives = ["useful", "bright", "swift", "calm", "bold"]
    nouns = ["fuze", "wave", "spark", "flow", "core"]
    import random

    adj = random.choice(adjectives)
    noun = random.choice(nouns)
    random_part = uuid.uuid4().hex[:5].lower()
    return f"{adj}-{noun}-{random_part}"


def _transform_messages_to_contents(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    contents = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        if role == "system":
            continue

        gemini_role = "model" if role == "assistant" else "user"

        if isinstance(content, str):
            parts = [{"text": content}]
        elif isinstance(content, list):
            parts = []
            for block in content:
                if isinstance(block, str):
                    parts.append({"text": block})
                elif isinstance(block, dict):
                    if block.get("type") == "text":
                        parts.append({"text": block.get("text", "")})
                    elif block.get("type") == "image_url":
                        url = block.get("image_url", {}).get("url", "")
                        if url.startswith("data:"):
                            mime_end = url.find(";")
                            data_start = url.find(",") + 1
                            if mime_end > 5 and data_start > 0:
                                mime_type = url[5:mime_end]
                                data = url[data_start:]
                                parts.append(
                                    {
                                        "inline_data": {
                                            "mime_type": mime_type,
                                            "data": data,
                                        }
                                    }
                                )
        else:
            parts = [{"text": str(content)}]

        contents.append({"role": gemini_role, "parts": parts})

    return contents


def _extract_system_instruction(messages: list[dict[str, Any]]) -> dict[str, Any] | None:
    for msg in messages:
        if msg.get("role") == "system":
            content = msg.get("content", "")
            if isinstance(content, str):
                return {"parts": [{"text": content}]}
    return None


def _transform_tools(tools: list[dict[str, Any]] | None) -> list[dict[str, Any]] | None:
    if not tools:
        return None

    function_declarations = []
    for tool in tools:
        func = tool.get("function", tool)
        name = func.get("name", f"tool-{len(function_declarations)}")
        name = str(name).replace(" ", "_")[:64]
        description = func.get("description", "")
        parameters = func.get(
            "parameters",
            func.get(
                "input_schema",
                {
                    "type": "object",
                    "properties": {},
                },
            ),
        )

        function_declarations.append(
            {
                "name": name,
                "description": str(description),
                "parameters": parameters,
            }
        )

    if function_declarations:
        return [{"functionDeclarations": function_declarations}]
    return None


def _build_antigravity_request_body(
    request: AntigravityRequest,
    project_id: str,
) -> dict[str, Any]:
    contents = _transform_messages_to_contents(request.messages)
    system_instruction = _extract_system_instruction(request.messages)

    inner_request: dict[str, Any] = {
        "contents": contents,
        "generationConfig": {
            "maxOutputTokens": request.max_tokens,
            "temperature": request.temperature,
        },
    }

    if system_instruction:
        inner_request["systemInstruction"] = system_instruction

    tools = _transform_tools(request.tools)
    if tools:
        inner_request["tools"] = tools
        if is_claude_model(request.model):
            inner_request["toolConfig"] = {"functionCallingConfig": {"mode": "VALIDATED"}}

    if is_claude_model(request.model) and "thinking" in request.model.lower():
        inner_request["generationConfig"]["thinkingConfig"] = {
            "include_thoughts": True,
            "thinking_budget": 10000,
        }
        inner_request["generationConfig"]["maxOutputTokens"] = 64000

    effective_project_id = project_id or _generate_synthetic_project_id()

    return {
        "project": effective_project_id,
        "model": request.model,
        "request": inner_request,
        "userAgent": "antigravity",
        "requestId": f"agent-{uuid.uuid4()}",
    }


def _parse_sse_line(line: str) -> dict[str, Any] | None:
    if not line.startswith("data:"):
        return None
    json_str = line[5:].strip()
    if not json_str:
        return None
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None


def _extract_chunk_content(data: dict[str, Any]) -> AntigravityStreamChunk:
    response = data.get("response", data)

    candidates = response.get("candidates", [])
    if not candidates:
        return AntigravityStreamChunk()

    candidate = candidates[0]
    content = candidate.get("content", {})
    parts = content.get("parts", [])

    text_parts = []
    thinking_parts = []
    tool_call = None

    for part in parts:
        if part.get("thought") or part.get("type") == "thinking":
            thinking_text = part.get("text", part.get("thinking", ""))
            if thinking_text:
                thinking_parts.append(thinking_text)
        elif part.get("functionCall"):
            tool_call = part["functionCall"]
        elif part.get("text"):
            text_parts.append(part["text"])

    finish_reason = candidate.get("finishReason")

    usage = None
    usage_meta = response.get("usageMetadata")
    if usage_meta:
        usage = {
            "prompt_tokens": usage_meta.get("promptTokenCount", 0),
            "completion_tokens": usage_meta.get("candidatesTokenCount", 0),
            "total_tokens": usage_meta.get("totalTokenCount", 0),
        }

    return AntigravityStreamChunk(
        content="".join(text_parts) if text_parts else None,
        thinking="".join(thinking_parts) if thinking_parts else None,
        tool_call=tool_call,
        finish_reason=finish_reason,
        usage=usage,
    )


class AntigravityClient:
    def __init__(self, account_manager: AntigravityAccountManager | None = None) -> None:
        self._account_manager = account_manager
        self._current_endpoint: str = ANTIGRAVITY_ENDPOINT
        self._endpoint_failures: dict[str, int] = {}

    async def _get_account_manager(self) -> AntigravityAccountManager:
        if self._account_manager is None:
            self._account_manager = await get_antigravity_account_manager()
        return self._account_manager

    def _get_next_endpoint(self) -> str:
        for endpoint in ANTIGRAVITY_ENDPOINT_FALLBACKS:
            if self._endpoint_failures.get(endpoint, 0) < 3:
                return endpoint
        self._endpoint_failures.clear()
        return ANTIGRAVITY_ENDPOINT

    def _mark_endpoint_failure(self, endpoint: str) -> None:
        self._endpoint_failures[endpoint] = self._endpoint_failures.get(endpoint, 0) + 1

    async def _get_account_for_model(self, model: str) -> tuple[ManagedAccount, HeaderStyle] | None:
        manager = await self._get_account_manager()
        family = get_model_family(model)

        account = manager.get_current_or_next_for_family(family)
        if not account:
            return None

        account = await manager.ensure_valid_token(account)
        header_style = manager.get_available_header_style(account, family)

        if header_style is None:
            next_account = manager.get_current_or_next_for_family(family)
            if next_account and next_account != account:
                next_account = await manager.ensure_valid_token(next_account)
                header_style = manager.get_available_header_style(next_account, family)
                if header_style:
                    return next_account, header_style
            return None

        return account, header_style

    async def stream(
        self,
        request: AntigravityRequest,
    ) -> AsyncIterator[AntigravityStreamChunk]:
        from casare_rpa.infrastructure.http import UnifiedHttpClient, UnifiedHttpClientConfig

        account_info = await self._get_account_for_model(request.model)
        if not account_info:
            raise RuntimeError("No available Antigravity account for this model")

        account, header_style = account_info
        project_id = account.project_id or ANTIGRAVITY_DEFAULT_PROJECT_ID

        body = _build_antigravity_request_body(request, project_id)
        endpoint = self._get_next_endpoint()
        action = "streamGenerateContent" if request.stream else "generateContent"
        url = (
            f"{endpoint}/v1internal:{action}?alt=sse"
            if request.stream
            else f"{endpoint}/v1internal:{action}"
        )

        headers = get_headers_for_style(header_style)
        headers["Authorization"] = f"Bearer {account.access_token}"
        headers["Content-Type"] = "application/json"
        if request.stream:
            headers["Accept"] = "text/event-stream"

        if is_claude_model(request.model) and "thinking" in request.model.lower():
            headers["anthropic-beta"] = "interleaved-thinking-2025-05-14"

        config = UnifiedHttpClientConfig(default_timeout=120.0, max_retries=1)

        async with UnifiedHttpClient(config) as client:
            response = await client.post(url, headers=headers, json=body)

            if response.status == 429:
                manager = await self._get_account_manager()
                retry_after = int(response.headers.get("Retry-After", "60")) * 1000
                family = get_model_family(request.model)
                manager.mark_rate_limited(account, retry_after, family, header_style)
                raise RuntimeError(f"Rate limited. Retry after {retry_after // 1000}s")

            if response.status != 200:
                error_text = await response.text()
                self._mark_endpoint_failure(endpoint)
                raise RuntimeError(f"Antigravity API error {response.status}: {error_text[:500]}")

            if request.stream:
                async for line in response.content:
                    line_str = line.decode("utf-8").strip()
                    if not line_str:
                        continue

                    data = _parse_sse_line(line_str)
                    if data:
                        chunk = _extract_chunk_content(data)
                        yield chunk
            else:
                data = await response.json()
                chunk = _extract_chunk_content(data)
                yield chunk

    async def complete(self, request: AntigravityRequest) -> AntigravityResponse:
        request.stream = False

        content_parts = []
        thinking_parts = []
        tool_calls = []
        finish_reason = "stop"
        usage = None

        async for chunk in self.stream(request):
            if chunk.content:
                content_parts.append(chunk.content)
            if chunk.thinking:
                thinking_parts.append(chunk.thinking)
            if chunk.tool_call:
                tool_calls.append(chunk.tool_call)
            if chunk.finish_reason:
                finish_reason = chunk.finish_reason
            if chunk.usage:
                usage = chunk.usage

        return AntigravityResponse(
            content="".join(content_parts),
            thinking="".join(thinking_parts) if thinking_parts else None,
            tool_calls=tool_calls if tool_calls else None,
            finish_reason=finish_reason,
            usage=usage,
        )


_client: AntigravityClient | None = None


async def get_antigravity_client() -> AntigravityClient:
    global _client
    if _client is None:
        _client = AntigravityClient()
    return _client


__all__ = [
    "AntigravityRequest",
    "AntigravityStreamChunk",
    "AntigravityResponse",
    "AntigravityClient",
    "get_antigravity_client",
    "AntigravityModel",
]
