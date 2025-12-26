# Infrastructure AI Index

Quick reference for AI-powered workflow generation.

## Overview

Provides LLM-powered workflow generation with validation, retry logic, and node manifest services.
Includes GLM (Z.ai) client for OpenAI-compatible API access.

## Files

| File | Description | Lines |
|------|-------------|-------|
| `__init__.py` | Module exports (32 items) | 130 |
| `glm_client.py` | GLM (Z.ai) API client | 190 |
| `registry_dumper.py` | Node manifest generation for LLM | 17KB |
| `smart_agent.py` | SmartWorkflowAgent with retries | 54KB |

## Key Exports

### GLM Client (Z.ai)

| Export | Type | Description |
|--------|------|-------------|
| `GLMClient` | Class | GLM Coding Plan API client |
| `GLMResponse` | Dataclass | GLM API response structure |
| `GLMClientError` | Exception | Base GLM client error |
| `RateLimitError` | Exception | Rate limit exceeded |
| `MODEL_GLM_4_7` | str | glm-4.7 model constant |
| `MODEL_GLM_4_6` | str | glm-4.6 model constant |
| `MODEL_GLM_4_5` | str | glm-4.5 model constant |

### Registry Dumper

| Export | Type | Description |
|--------|------|-------------|
| `dump_node_manifest` | Function | Generate complete node manifest |
| `manifest_to_markdown` | Function | Convert manifest to markdown |
| `manifest_to_compact_markdown` | Function | Compact markdown format |
| `manifest_to_json` | Function | JSON export |
| `get_nodes_by_category` | Function | Filter nodes by category |
| `get_cached_manifest` | Function | Cached manifest retrieval |
| `clear_manifest_cache` | Function | Clear manifest cache |
| `NodeManifest` | TypedDict | Manifest structure |
| `NodeManifestEntry` | TypedDict | Node entry structure |
| `PortManifestEntry` | TypedDict | Port entry structure |

### Smart Agent

| Export | Type | Description |
|--------|------|-------------|
| `SmartWorkflowAgent` | Class | Main workflow generation agent |
| `WorkflowGenerationResult` | Dataclass | Generation result with metadata |
| `GenerationAttempt` | Dataclass | Single attempt record |
| `HeadlessWorkflowSandbox` | Class | Validation sandbox |
| `generate_smart_workflow` | Function | Convenience wrapper |

### Exceptions

| Exception | Description |
|-----------|-------------|
| `WorkflowGenerationError` | Base generation error |
| `LLMCallError` | LLM API call failed |
| `JSONParseError` | JSON extraction/parsing failed |
| `ValidationError` | Workflow validation failed |
| `MaxRetriesExceededError` | All retry attempts exhausted |

## Entry Points

```python
# Node Manifest Generation
from casare_rpa.infrastructure.ai import (
    dump_node_manifest,
    manifest_to_markdown,
    manifest_to_compact_markdown,
    NodeManifest,
)

# Generate manifest for all registered nodes
manifest = dump_node_manifest()
md_content = manifest_to_markdown(manifest)

# Smart Workflow Generation
from casare_rpa.infrastructure.ai import (
    SmartWorkflowAgent,
    WorkflowGenerationResult,
    generate_smart_workflow,
)

# With configuration
from casare_rpa.domain.ai import PERFORMANCE_OPTIMIZED_CONFIG

agent = SmartWorkflowAgent(config=PERFORMANCE_OPTIMIZED_CONFIG)
result = await agent.generate("Login to website and scrape data")

# Convenience wrapper
result = await generate_smart_workflow(
    prompt="Create invoice processing workflow",
    llm_client=my_llm_client,
)

# Error handling
from casare_rpa.infrastructure.ai import (
    WorkflowGenerationError,
    LLMCallError,
    JSONParseError,
    ValidationError,
    MaxRetriesExceededError,
)

try:
    result = await agent.generate(prompt)
except LLMCallError as e:
    logger.error(f"LLM API failed: {e}")
except JSONParseError as e:
    logger.error(f"Could not parse workflow: {e}")
except MaxRetriesExceededError as e:
    logger.error(f"All {e.attempts} attempts failed")
```

## Architecture

```
infrastructure/ai/
    __init__.py           # Module exports
    glm_client.py         # GLM (Z.ai) API client
    registry_dumper.py    # Node manifest -> LLM context
    smart_agent.py        # LLM workflow generation
```

### GLM Client Usage

```python
from casare_rpa.infrastructure.ai import GLMClient, MODEL_GLM_4_7

client = GLMClient(
    api_key="your_zai_api_key",
    model=MODEL_GLM_4_7,
)

# Simple completion
response = await client.generate_text(
    prompt="What is 2 + 2?",
    max_tokens=100,
)

# Chat with history
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"},
]
response = await client.chat(messages=messages)

# Vision (glm-4.7 only)
response = await client.analyze_image(
    prompt="Describe this image",
    image_base64="base64_encoded_image_data",
)
```

### SmartWorkflowAgent Flow

1. Build prompt with node manifest context
2. Call LLM API with retry logic
3. Extract JSON from response
4. Validate workflow structure
5. Optional: Headless validation sandbox
6. Return WorkflowGenerationResult

### Retry Strategy

- Exponential backoff with jitter
- Configurable max retries (default: 3)
- Error-specific repair prompts
- Preserves attempt history

## Configuration

Uses `domain.ai.AgentConfig`:

```python
from casare_rpa.domain.ai import (
    AgentConfig,
    PerformanceConfig,
    WaitStrategy,
    ErrorHandlingMode,
)

config = AgentConfig(
    performance=PerformanceConfig(
        wait_strategy=WaitStrategy.NO_HARDCODED_WAITS,
        parallelization_enabled=True,
    ),
    error_handling_mode=ErrorHandlingMode.PARANOID,
    max_retries=3,
)
```

## Related Indexes

- `domain/ai/_index.md` - Prompts and configuration
- `domain/schemas/workflow_ai.py` - Validation schemas
- `nodes/_index.md` - Node registry for manifest
- `infrastructure/_index.md` - Parent index
