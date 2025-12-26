"""Cached OpenAI client implementation.

Wraps OpenAI API with LLMResponseCache.
"""

try:
    import anthropic
except ImportError:
    anthropic = None
