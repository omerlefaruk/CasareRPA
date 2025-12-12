# AI Domain Index

Quick reference for AI/Genius workflow generation module. Use for fast discovery.

## Overview

| Aspect | Description |
|--------|-------------|
| Purpose | System prompts, templates, and configuration for Genius AI Assistant |
| Files | 3 files (prompts.py, config.py, __init__.py) |
| Exports | 31 total exports |

## Key Files

| File | Contains |
|------|----------|
| `prompts.py` | System prompts, templates, PromptBuilder class |
| `config.py` | AgentConfig, enums, pre-configured profiles |
| `__init__.py` | Re-exports all public symbols |

## Prompt Constants

| Export | Description |
|--------|-------------|
| `GENIUS_SYSTEM_PROMPT` | Core AI persona and protocol |
| `ROBUSTNESS_INSTRUCTIONS` | Paranoid engineering guidelines |
| `JSON_SCHEMA_TEMPLATE` | Expected workflow JSON structure |
| `REPAIR_PROMPT_TEMPLATE` | Error correction template |
| `NODE_CONTEXT_PROMPT` | Node manifest injection template |
| `PERFORMANCE_OPTIMIZED_PROMPT` | No hardcoded waits, parallel execution |
| `MINIMAL_WAIT_PROMPT` | Minimal waits strategy |
| `SMART_WAIT_PROMPT` | Smart element detection |
| `PARANOID_ERROR_HANDLING_PROMPT` | Wrap all operations in try/catch |
| `CRITICAL_ONLY_ERROR_HANDLING_PROMPT` | Wrap critical operations only |
| `MINIMAL_ERROR_HANDLING_PROMPT` | Minimal error handling |
| `MISSING_NODE_PROTOCOL` | Protocol for requesting new nodes |
| `VARIABLE_SYNTAX_DOCUMENTATION` | Variable syntax rules (CRITICAL for array access) |
| `CONTROL_FLOW_PORT_DOCUMENTATION` | Exact port names for control flow nodes |

## Configuration Classes

| Export | Description |
|--------|-------------|
| `AgentConfig` | Complete agent configuration dataclass |
| `PerformanceConfig` | Wait strategy, parallelization settings |
| `PromptRules` | Custom rules and constraints |
| `RetryConfig` | Retry behavior configuration |

## Enums

| Export | Values |
|--------|--------|
| `WaitStrategy` | NO_HARDCODED_WAITS, MINIMAL_WAITS, SMART_WAITS, DEFAULT |
| `ParallelizationMode` | AGGRESSIVE, OPTIMIZED, SEQUENTIAL, AUTO |
| `ErrorHandlingMode` | PARANOID, CRITICAL_ONLY, MINIMAL, NONE |

## Pre-configured Profiles

| Export | Use Case |
|--------|----------|
| `PERFORMANCE_OPTIMIZED_CONFIG` | Maximum speed, no waits, aggressive parallel |
| `RELIABILITY_FOCUSED_CONFIG` | Maximum robustness, paranoid error handling |
| `SIMPLE_FAST_CONFIG` | Minimal complexity, fast generation |

## Helper Functions

| Function | Description |
|----------|-------------|
| `get_workflow_generation_prompt(request, manifest)` | Build full generation prompt |
| `get_repair_prompt(json, error)` | Build error repair prompt |
| `get_append_prompt(workflow, request, manifest)` | Build workflow append prompt |
| `get_performance_optimized_prompt(request, manifest)` | Performance-focused prompt |

## PromptBuilder Class

| Method | Description |
|--------|-------------|
| `build_system_prompt(manifest)` | Build complete system prompt |
| `build_generation_prompt(request, manifest)` | Build workflow generation prompt |
| `build_repair_prompt(json, error)` | Build error repair prompt |

## Usage Patterns

```python
# Basic workflow generation
from casare_rpa.domain.ai import (
    get_workflow_generation_prompt,
    GENIUS_SYSTEM_PROMPT,
)

prompt = get_workflow_generation_prompt(
    user_request="Login to website and extract data",
    node_manifest=manifest_json,
)

# Custom configuration
from casare_rpa.domain.ai import (
    AgentConfig,
    PerformanceConfig,
    WaitStrategy,
    PromptBuilder,
)

config = AgentConfig(
    performance=PerformanceConfig(
        wait_strategy=WaitStrategy.NO_HARDCODED_WAITS,
    ),
)
builder = PromptBuilder(config=config)
prompt = builder.build_generation_prompt(request, manifest)

# Pre-configured profile
from casare_rpa.domain.ai import PERFORMANCE_OPTIMIZED_CONFIG
agent = SmartWorkflowAgent(config=PERFORMANCE_OPTIMIZED_CONFIG)
```

## Related Modules

| Module | Relation |
|--------|----------|
| `domain.schemas.workflow_ai` | Pydantic validation schemas for generated workflows |
| `infrastructure.ai` | LLM client implementations |
| `presentation.canvas.ui.widgets.ai_assistant` | UI integration |
