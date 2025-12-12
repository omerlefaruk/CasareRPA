"""
CasareRPA - AI Domain Module.

Provides system prompts, templates, and configuration for the Genius AI Assistant.
This module contains prompt engineering artifacts for workflow generation.

Entry Points:
    - GENIUS_SYSTEM_PROMPT: Core AI persona and protocol
    - ROBUSTNESS_INSTRUCTIONS: Paranoid engineering guidelines
    - JSON_SCHEMA_TEMPLATE: Expected workflow JSON structure
    - REPAIR_PROMPT_TEMPLATE: Error correction template
    - NODE_CONTEXT_PROMPT: Node manifest injection template
    - PERFORMANCE_OPTIMIZED_PROMPT: No hardcoded waits, parallel execution

Configuration:
    - AgentConfig: Complete agent configuration
    - PerformanceConfig: Wait strategy, parallelization settings
    - PromptRules: Custom rules and constraints
    - RetryConfig: Retry behavior configuration
    - WaitStrategy: NO_HARDCODED_WAITS, SMART_WAITS, etc.
    - ParallelizationMode: AGGRESSIVE, OPTIMIZED, SEQUENTIAL
    - ErrorHandlingMode: PARANOID, CRITICAL_ONLY, MINIMAL

Pre-configured Profiles:
    - PERFORMANCE_OPTIMIZED_CONFIG: Maximum speed, no waits
    - RELIABILITY_FOCUSED_CONFIG: Maximum robustness
    - SIMPLE_FAST_CONFIG: Minimal complexity

Helper Functions:
    - get_workflow_generation_prompt: Build full generation prompt
    - get_repair_prompt: Build error repair prompt
    - get_append_prompt: Build workflow append prompt
    - get_performance_optimized_prompt: Performance-focused prompt

Related:
    - domain.schemas.workflow_ai: Pydantic validation schemas
    - infrastructure.ai: LLM client implementations
    - presentation.canvas.genius: UI integration
"""

from casare_rpa.domain.ai.prompts import (
    GENIUS_SYSTEM_PROMPT,
    ROBUSTNESS_INSTRUCTIONS,
    JSON_SCHEMA_TEMPLATE,
    REPAIR_PROMPT_TEMPLATE,
    NODE_CONTEXT_PROMPT,
    PERFORMANCE_OPTIMIZED_PROMPT,
    MINIMAL_WAIT_PROMPT,
    SMART_WAIT_PROMPT,
    PARANOID_ERROR_HANDLING_PROMPT,
    CRITICAL_ONLY_ERROR_HANDLING_PROMPT,
    MINIMAL_ERROR_HANDLING_PROMPT,
    MISSING_NODE_PROTOCOL,
    VARIABLE_SYNTAX_DOCUMENTATION,
    CONTROL_FLOW_PORT_DOCUMENTATION,
    PromptBuilder,
    get_workflow_generation_prompt,
    get_repair_prompt,
    get_append_prompt,
    get_performance_optimized_prompt,
)

from casare_rpa.domain.ai.config import (
    AgentConfig,
    PerformanceConfig,
    PromptRules,
    RetryConfig,
    WaitStrategy,
    ParallelizationMode,
    ErrorHandlingMode,
    PERFORMANCE_OPTIMIZED_CONFIG,
    RELIABILITY_FOCUSED_CONFIG,
    SIMPLE_FAST_CONFIG,
)

from casare_rpa.domain.ai.prompt_templates import (
    PromptTemplate,
    TemplateVariable,
    TemplateCategory,
    FewShotExample,
    BUILTIN_TEMPLATES,
    EXTRACT_ENTITIES_TEMPLATE,
    CLASSIFY_DOCUMENT_TEMPLATE,
    SUMMARIZE_MEETING_TEMPLATE,
    TRANSLATE_FORMAL_TEMPLATE,
    GENERATE_EMAIL_TEMPLATE,
    ANALYZE_SENTIMENT_TEMPLATE,
    EXTRACT_INVOICE_TEMPLATE,
    DATA_CONVERSION_TEMPLATE,
    get_builtin_template,
    list_builtin_templates,
    list_templates_by_category,
)

__all__ = [
    # Prompt Constants
    "GENIUS_SYSTEM_PROMPT",
    "ROBUSTNESS_INSTRUCTIONS",
    "JSON_SCHEMA_TEMPLATE",
    "REPAIR_PROMPT_TEMPLATE",
    "NODE_CONTEXT_PROMPT",
    "PERFORMANCE_OPTIMIZED_PROMPT",
    "MINIMAL_WAIT_PROMPT",
    "SMART_WAIT_PROMPT",
    "PARANOID_ERROR_HANDLING_PROMPT",
    "CRITICAL_ONLY_ERROR_HANDLING_PROMPT",
    "MINIMAL_ERROR_HANDLING_PROMPT",
    "MISSING_NODE_PROTOCOL",
    # Variable Syntax Documentation (CRITICAL for correct array access)
    "VARIABLE_SYNTAX_DOCUMENTATION",
    # Control Flow Port Documentation (CRITICAL for correct connections)
    "CONTROL_FLOW_PORT_DOCUMENTATION",
    # Prompt Builder
    "PromptBuilder",
    # Helper Functions
    "get_workflow_generation_prompt",
    "get_repair_prompt",
    "get_append_prompt",
    "get_performance_optimized_prompt",
    # Configuration
    "AgentConfig",
    "PerformanceConfig",
    "PromptRules",
    "RetryConfig",
    "WaitStrategy",
    "ParallelizationMode",
    "ErrorHandlingMode",
    # Pre-configured Profiles
    "PERFORMANCE_OPTIMIZED_CONFIG",
    "RELIABILITY_FOCUSED_CONFIG",
    "SIMPLE_FAST_CONFIG",
    # Prompt Templates
    "PromptTemplate",
    "TemplateVariable",
    "TemplateCategory",
    "FewShotExample",
    "BUILTIN_TEMPLATES",
    "EXTRACT_ENTITIES_TEMPLATE",
    "CLASSIFY_DOCUMENT_TEMPLATE",
    "SUMMARIZE_MEETING_TEMPLATE",
    "TRANSLATE_FORMAL_TEMPLATE",
    "GENERATE_EMAIL_TEMPLATE",
    "ANALYZE_SENTIMENT_TEMPLATE",
    "EXTRACT_INVOICE_TEMPLATE",
    "DATA_CONVERSION_TEMPLATE",
    "get_builtin_template",
    "list_builtin_templates",
    "list_templates_by_category",
]
