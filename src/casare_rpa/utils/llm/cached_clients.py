"""Cached OpenAI client implementation.

Wraps OpenAI API with LLMResponseCache.
"""

from typing import Optional

from casare_rpa.utils.llm.cache import CachedLLMClient, LLMResponseCache

try:
    import anthropic
except ImportError:
    anthropic = None
