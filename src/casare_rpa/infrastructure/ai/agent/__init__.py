"""
AI agent package.
"""

from casare_rpa.infrastructure.ai.agent.core import (
    SmartWorkflowAgent,
    generate_smart_workflow,
)
from casare_rpa.infrastructure.ai.agent.exceptions import (
    WorkflowGenerationError,
    LLMCallError,
    JSONParseError,
    ValidationError,
    MaxRetriesExceededError,
)
from casare_rpa.infrastructure.ai.agent.sandbox import HeadlessWorkflowSandbox
from casare_rpa.infrastructure.ai.agent.types import (
    GenerationAttempt,
    WorkflowGenerationResult,
)
from casare_rpa.infrastructure.ai.agent.prompts import (
    MULTI_TURN_SYSTEM_PROMPT as _MULTI_TURN_SYSTEM_PROMPT,
    REFINE_SYSTEM_PROMPT as _REFINE_SYSTEM_PROMPT,
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
