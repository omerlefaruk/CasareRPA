# Gemini Auth Refactor - Implementation Plan

**Goal**: Refactor AI assistant and LLM infrastructure to remove litellm dependency and use Google Gemini Pro subscription via OAuth (opencode-gemini-auth pattern).

**Status**: PLANNING
**Created**: 2025-12-25

---

## Executive Summary

Remove `litellm` dependency and replace with direct Gemini AI Studio API calls using existing `GeminiOAuthManager`. This reduces dependencies, simplifies the codebase, and aligns with the opencode-gemini-auth pattern already implemented in `gemini_oauth.py`.

### Key Benefits
- **Reduced dependencies**: Remove litellm (~20MB transitive deps)
- **Simplified code**: Direct API calls vs adapter abstraction
- **Consistent auth**: Use same OAuth flow across all Gemini features
- **Better performance**: Fewer layers = faster calls

### Current State
- `GeminiOAuthManager` already implements PKCE OAuth flow
- `call_gemini_api()` function exists for direct API calls
- `LLMResourceManager` has `_call_gemini_api_directly()` bypass for litellm
- `SmartWorkflowAgent` uses `LLMResourceManager` for AI workflow generation
- `SolveCaptchaAINode` uses `LLMResourceManager` with direct API fallback

---

## Phase Breakdown

### Phase 1: Planning & Approval
- [x] Research existing architecture
- [x] Identify all litellm usage points
- [x] Document current GeminiOAuthManager capabilities
- [x] Create implementation plan (this document)
- [ ] Get user approval

### Phase 2: Create GeminiClient (New Infrastructure)
- [ ] Create `GeminiClient` class
- [ ] Implement text generation (completion)
- [ ] Implement chat with history
- [ ] Implement vision/image analysis
- [ ] Implement streaming support (optional)
- [ ] Add error handling and retry logic

### Phase 3: Refactor LLMResourceManager
- [ ] Replace litellm imports with GeminiClient
- [ ] Update `completion()` method
- [ ] Update `chat()` method
- [ ] Update `vision_completion()` method
- [ ] Remove litellm-specific code paths
- [ ] Update `cleanup()` and `dispose()`

### Phase 4: Update SmartWorkflowAgent
- [ ] Update imports (no litellm)
- [ ] Verify `_call_llm_with_retry()` works with new client
- [ ] Test workflow generation

### Phase 5: Update AI Assistant UI
- [ ] Verify `AIAssistantDock` works with refactored backend
- [ ] Update credential selection (Google only)
- [ ] Test multi-turn conversations

### Phase 6: Update SolveCaptchaAINode
- [ ] Remove litellm fallback
- [ ] Use direct Gemini API calls only
- [ ] Test CAPTCHA solving

### Phase 7: Remove litellm Dependency
- [ ] Remove from `pyproject.toml`
- [ ] Update imports
- [ ] Run full test suite

### Phase 8: Documentation & Cleanup
- [ ] Update AGENTS.md
- [ ] Update CLAUDE.md
- [ ] Add decision tree to `.brain/decisions/`
- [ ] Run tests and QA

---

## Files to Create/Modify/Delete

### New Files (Create)

| File | Purpose | Lines (est) |
|------|---------|-------------|
| `infrastructure/ai/gemini_client.py` | Direct Gemini API client | 400 |

### Modify Files

| File | Changes | Impact |
|------|---------|--------|
| `pyproject.toml` | Remove `litellm>=1.50.0` | Dependency removal |
| `infrastructure/resources/llm_resource_manager.py` | Replace litellm with GeminiClient | Major refactor |
| `infrastructure/ai/agent/core.py` | Verify no litellm imports | Minor - verification |
| `presentation/canvas/ui/widgets/ai_assistant/dock.py` | Update model defaults, provider handling | Minor |
| `nodes/browser/captcha_ai.py` | Remove litellm fallback | Minor |
| `.brain/context/current.md` | Document refactor status | Update |
| `AGENTS.md` | Reflect litellm removal | Update |

### Delete Files (None)
No files deleted, only code removed from existing files.

---

## New Gemini Client Architecture

### Class Design

```python
# infrastructure/ai/gemini_client.py

class GeminiClient:
    """
    Direct Google Gemini AI Studio API client.

    Uses OAuth tokens from GeminiOAuthManager.
    Supports text, chat, and vision requests.
    """

    API_BASE = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(
        self,
        credential_id: str | None = None,
        model: str = "gemini-2.0-flash-exp",
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ):
        self._credential_id = credential_id
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._oauth_manager: GeminiOAuthManager | None = None

    async def _get_oauth_manager(self) -> GeminiOAuthManager:
        """Lazy load OAuth manager."""
        ...

    async def _get_access_token(self) -> str:
        """Get fresh access token."""
        ...

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> GeminiResponse:
        """Generate text from prompt."""
        ...

    async def chat(
        self,
        messages: list[ChatMessage],
        system_prompt: str | None = None,
    ) -> GeminiResponse:
        """Chat with conversation history."""
        ...

    async def analyze_image(
        self,
        prompt: str,
        image_data: str,  # base64
        mime_type: str = "image/png",
    ) -> GeminiResponse:
        """Analyze image with vision."""
        ...

@dataclass
class GeminiResponse:
    """Standardized Gemini API response."""
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    finish_reason: str
    raw_response: dict[str, Any]
```

### API Mapping

| LiteLLM Method | GeminiClient Method | Notes |
|----------------|---------------------|-------|
| `acompletion(messages)` | `generate_text(prompt, system_prompt)` | Simplified signature |
| `acompletion(messages)` | `chat(messages)` | Multi-turn |
| `acompletion(images)` | `analyze_image(prompt, image_data)` | Vision |

---

## Credential Management

### Existing Infrastructure (Keep)

```python
# infrastructure/security/gemini_oauth.py (KEEP)

class GeminiOAuthManager:
    async def get_access_token(credential_id: str) -> str:
        """Get valid access token, refresh if needed."""
```

### Credential Flow

```
User selects "google_oauth" credential
    ↓
AIAssistantDock passes credential_id to LLMResourceManager
    ↓
LLMResourceManager creates GeminiClient(credential_id=...)
    ↓
GeminiClient calls GeminiOAuthManager.get_access_token(credential_id)
    ↓
Direct API call with Bearer token
```

---

## Model Support

### Recommended Models

| Model | Use Case | Speed | Quality |
|-------|----------|-------|---------|
| `gemini-2.0-flash-exp` | General workflow generation | Fast | Good |
| `gemini-3-flash-preview` | Fast responses | Very Fast | Good |
| `gemini-1.5-flash` | Fallback | Fast | Good |
| `gemini-1.5-pro` | Complex reasoning | Medium | Better |
| `gemini-2.5-pro` (future) | High-quality generation | Slow | Best |

### Model Naming

- **API format**: `models/gemini-2.0-flash-exp`
- **Display format**: `gemini-2.0-flash-exp`
- **Client strips `models/` prefix for API calls**

---

## Detailed Changes by File

### 1. `infrastructure/ai/gemini_client.py` (NEW)

```python
"""
Direct Gemini AI Studio API client.

Uses OAuth tokens from GeminiOAuthManager.
No LiteLLM dependency.
"""

from dataclasses import dataclass
from typing import Any

import aiohttp
from loguru import logger

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"

@dataclass
class GeminiResponse:
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    finish_reason: str
    raw_response: dict[str, Any] | None = None

class GeminiClient:
    # Implementation (see design above)
    ...
```

### 2. `infrastructure/resources/llm_resource_manager.py`

**Remove:**
- `import litellm` (line 305)
- `_ensure_initialized()` method
- `_get_model_string()` LiteLLM-specific logic
- Vertex AI patching logic
- LiteLLM cleanup code

**Replace with:**
- Import `GeminiClient`
- Update `completion()` to use `GeminiClient`
- Update `chat()` to use `GeminiClient`
- Update `vision_completion()` to use `GeminiClient`

### 3. `pyproject.toml`

```diff
dependencies = [
    ...
-   "litellm>=1.50.0",  # Unified LLM API (OpenAI, Anthropic, Azure, local)
    ...
]
```

### 4. `nodes/browser/captcha_ai.py`

**Remove:**
- LiteLLM fallback in `_analyze_challenge()`

**Simplify:**
- Always use `_call_google_ai_direct()`
- Remove LLMResourceManager dependency

---

## Risk Analysis

### High Risk Items

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing workflows | High | Keep same API signatures in LLMResourceManager |
| OAuth token expiry during call | Medium | GeminiOAuthManager auto-refreshes |
| Response format changes | Medium | Map to existing LLMResponse format |
| Missing features (streaming) | Low | Not currently used |

### Mitigation Strategies

1. **API Compatibility**: Keep `LLMResourceManager` public signatures unchanged
2. **Graceful Degradation**: If API call fails, log and return error
3. **Comprehensive Testing**: Test all 3 use cases (workflow gen, CAPTCHA, chat)

---

## Test Strategy

### Unit Tests

| Test | Target | Coverage |
|------|--------|----------|
| `test_gemini_client_text_generation` | GeminiClient | Text completion |
| `test_gemini_client_chat` | GeminiClient | Multi-turn chat |
| `test_gemini_client_vision` | GeminiClient | Image analysis |
| `test_gemini_client_token_refresh` | GeminiClient | OAuth expiry handling |
| `test_llm_manager_completion` | LLMResourceManager | Text via new client |
| `test_llm_manager_vision` | LLMResourceManager | Vision via new client |

### Integration Tests

| Test | Target | Description |
|------|--------|-------------|
| `test_smart_workflow_agent_generation` | SmartWorkflowAgent | Full workflow generation |
| `test_captcha_ai_node` | SolveCaptchaAINode | End-to-end CAPTCHA solve |
| `test_ai_assistant_dock` | AIAssistantDock | UI integration |

### Manual Testing

1. **OAuth Flow**: Connect Google account, verify token refresh
2. **Workflow Generation**: Generate sample workflows in Canvas
3. **CAPTCHA Solving**: Test with reCAPTCHA challenges
4. **Multi-turn Chat**: Test conversation history in AI Assistant

---

## Rollback Approach

If critical issues arise:

1. **Revert pyproject.toml**: Add `litellm>=1.50.0` back
2. **Git revert**: Revert commits for this feature
3. **Hotfix**: Branch `hotfix/restore-litellm`

**Rollback command**:
```bash
git revert <commit-range> --no-commit
pip install -e .
```

---

## Implementation Order (Recommended)

1. Create `GeminiClient` (standalone, testable)
2. Write unit tests for `GeminiClient`
3. Refactor `LLMResourceManager` (use `GeminiClient` internally)
4. Update `SmartWorkflowAgent` (should just work)
5. Update `SolveCaptchaAINode` (simplify to direct calls)
6. Update `AIAssistantDock` (verify UI still works)
7. Remove `litellm` from `pyproject.toml`
8. Run full test suite
9. Update documentation

---

## Success Criteria

- [ ] All existing tests pass
- [ ] `litellm` removed from dependencies
- [ ] Workflow generation works with Google OAuth
- [ ] CAPTCHA solving works with Google OAuth
- [ ] AI Assistant chat works
- [ ] No performance regression
- [ ] Documentation updated

---

## Dependencies

### Internal Dependencies
- `infrastructure/security/gemini_oauth.py` (KEEP - already implemented)
- `infrastructure/security/credential_store.py` (KEEP - unchanged)
- `domain/schemas/` (KEEP - unchanged)

### External Dependencies (Removed)
- `litellm>=1.50.0` (REMOVE)

### External Dependencies (Kept)
- `aiohttp>=3.8.0` (HTTP client)
- `loguru>=0.7.2` (Logging)
- `pydantic>=2.6.0` (Data validation)

---

## References

- **opencode-gemini-auth**: https://github.com/jenslys/opencode-gemini-auth
- **Gemini API Docs**: https://ai.google.dev/gemini-api/docs
- **Current OAuth implementation**: `infrastructure/security/gemini_oauth.py`
- **LLMResourceManager**: `infrastructure/resources/llm_resource_manager.py`

---

## Next Steps

1. **Review this plan** with user
2. **Create worktree branch**: `python scripts/create_worktree.py "gemini-auth-refactor"`
3. **Begin Phase 2**: Create `GeminiClient`
4. **Update**: `.brain/context/current.md` with progress

---

*Last updated: 2025-12-25*
