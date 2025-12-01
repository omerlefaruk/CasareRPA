"""
CasareRPA - Infrastructure Resources
Resource managers for external infrastructure (browser, desktop, LLM, etc.).
"""

from .browser_resource_manager import BrowserResourceManager
from .llm_resource_manager import (
    LLMResourceManager,
    LLMConfig,
    LLMProvider,
    LLMResponse,
    LLMUsageMetrics,
)

__all__ = [
    "BrowserResourceManager",
    "LLMResourceManager",
    "LLMConfig",
    "LLMProvider",
    "LLMResponse",
    "LLMUsageMetrics",
]
