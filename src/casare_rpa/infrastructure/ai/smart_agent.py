"""
Shim for backward compatibility.
Moved to casare_rpa.infrastructure.ai.agent package.
"""

from casare_rpa.infrastructure.ai.agent import (
    SmartWorkflowAgent,
    WorkflowGenerationResult,
    GenerationAttempt,
    HeadlessWorkflowSandbox,
    generate_smart_workflow,
    WorkflowGenerationError,
    LLMCallError,
    JSONParseError,
    ValidationError,
    MaxRetriesExceededError,
    _MULTI_TURN_SYSTEM_PROMPT,
    _REFINE_SYSTEM_PROMPT,
)

__all__ = [
    "SmartWorkflowAgent",
    "WorkflowGenerationResult",
    "GenerationAttempt",
    "HeadlessWorkflowSandbox",
    "generate_smart_workflow",
    "WorkflowGenerationError",
    "LLMCallError",
    "JSONParseError",
    "ValidationError",
    "MaxRetriesExceededError",
    "_MULTI_TURN_SYSTEM_PROMPT",
    "_REFINE_SYSTEM_PROMPT",
]
