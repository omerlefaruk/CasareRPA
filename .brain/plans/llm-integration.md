# LLM Integration Plan

**Status**: COMPLETE
**Created**: 2025-12-01
**Priority**: HIGHEST (competitive gap)

## Overview

Implement LLM nodes for AI-powered workflow automation. Supports OpenAI, Anthropic, and local models via LiteLLM.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                      │
├─────────────────────────────────────────────────────────────┤
│  LLMResourceManager                                          │
│  - Connection pooling                                        │
│  - API key management (via CredentialManager)                │
│  - Rate limiting integration                                 │
│  - Token counting & cost tracking                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Node Layer                              │
├─────────────────────────────────────────────────────────────┤
│  LLMBaseNode (abstract)                                      │
│  ├── LLMCompletionNode    - Single prompt → response         │
│  ├── LLMChatNode          - Multi-turn conversation          │
│  ├── LLMExtractDataNode   - Structured data extraction       │
│  ├── LLMSummarizeNode     - Text summarization               │
│  ├── LLMClassifyNode      - Text classification              │
│  └── LLMTranslateNode     - Language translation             │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Tasks

### Phase 1: Infrastructure (Day 1) - COMPLETE
- [x] Create `.brain/plans/llm-integration.md`
- [x] Create `src/casare_rpa/infrastructure/resources/llm_resource_manager.py`
  - LiteLLM client wrapper
  - Provider enum (OpenAI, Anthropic, Azure, Local)
  - Rate limit tracking
  - Token/cost metrics

### Phase 2: Base Node (Day 1-2) - COMPLETE
- [x] Create `src/casare_rpa/nodes/llm/__init__.py`
- [x] Create `src/casare_rpa/nodes/llm/llm_base.py`
  - Abstract base with shared logic
  - Provider selection
  - Error handling
  - Token counting output

### Phase 3: Core Nodes (Day 2-3) - COMPLETE
- [x] `LLMCompletionNode` - Simple prompt/response
- [x] `LLMChatNode` - Multi-turn with history
- [x] `LLMExtractDataNode` - JSON/structured output
- [x] `LLMSummarizeNode` - Text summarization
- [x] `LLMClassifyNode` - Classification with labels
- [x] `LLMTranslateNode` - Translation with target language

### Phase 4: Visual Nodes (Day 3) - DEFERRED
- [ ] Register visual nodes in canvas
- [ ] Add to node palette under "AI/ML" category
- [ ] Create node icons

### Phase 5: Tests (Day 4) - COMPLETE
- [x] Unit tests with mocked LiteLLM (59 tests)
- [x] Resource manager tests
- [ ] Integration tests (optional, requires API keys)

## Provider Support (via LiteLLM)

| Provider | Models | Config |
|----------|--------|--------|
| OpenAI | gpt-4o, gpt-4-turbo, gpt-3.5-turbo | `OPENAI_API_KEY` |
| Anthropic | claude-3-5-sonnet, claude-3-opus | `ANTHROPIC_API_KEY` |
| Azure OpenAI | deployment-based | `AZURE_API_*` |
| Ollama (local) | llama3, mistral, codellama | `OLLAMA_API_BASE` |

## Node Specifications

### LLMCompletionNode
```python
Inputs:
  - prompt: STRING (required)
  - model: STRING (default: "gpt-4o-mini")
  - temperature: FLOAT (default: 0.7)
  - max_tokens: INTEGER (default: 1000)
  - system_prompt: STRING (optional)

Outputs:
  - response: STRING
  - tokens_used: INTEGER
  - model_used: STRING
  - success: BOOLEAN
  - error: STRING
```

### LLMChatNode
```python
Inputs:
  - message: STRING (required)
  - conversation_id: STRING (optional, for history)
  - model: STRING
  - temperature: FLOAT
  - max_tokens: INTEGER
  - system_prompt: STRING

Outputs:
  - response: STRING
  - conversation_id: STRING
  - tokens_used: INTEGER
  - success: BOOLEAN
  - error: STRING
```

### LLMExtractDataNode
```python
Inputs:
  - text: STRING (required)
  - schema: DICT (JSON schema for output)
  - model: STRING
  - temperature: FLOAT (default: 0.0 for determinism)

Outputs:
  - extracted_data: DICT
  - raw_response: STRING
  - success: BOOLEAN
  - error: STRING
```

### LLMSummarizeNode
```python
Inputs:
  - text: STRING (required)
  - max_length: INTEGER (target summary length)
  - style: STRING (bullet_points, paragraph, key_points)
  - model: STRING

Outputs:
  - summary: STRING
  - original_length: INTEGER
  - summary_length: INTEGER
  - success: BOOLEAN
```

### LLMClassifyNode
```python
Inputs:
  - text: STRING (required)
  - categories: LIST[STRING] (required)
  - model: STRING
  - multi_label: BOOLEAN (default: False)

Outputs:
  - classification: STRING | LIST[STRING]
  - confidence: FLOAT | DICT
  - success: BOOLEAN
```

### LLMTranslateNode
```python
Inputs:
  - text: STRING (required)
  - target_language: STRING (required)
  - source_language: STRING (optional, auto-detect)
  - model: STRING

Outputs:
  - translated_text: STRING
  - detected_language: STRING
  - success: BOOLEAN
```

## Dependencies

```toml
# Add to pyproject.toml
litellm = "^1.40.0"  # Unified LLM API
tiktoken = "^0.5.0"  # Token counting for OpenAI
```

## Error Handling

- Rate limit errors → automatic retry with backoff
- Invalid API key → clear error message with setup instructions
- Context length exceeded → truncate or error with suggestion
- Network errors → retry with exponential backoff

## Security

- API keys stored via CredentialManager (never in workflow JSON)
- No PII logging in LLM requests
- Optional prompt/response logging (disabled by default)

## Unresolved Questions

1. Should conversation history be stored in workflow variables or separate storage?
2. Token cost tracking - display in UI or just logs?
3. Support for streaming responses in future iteration?
