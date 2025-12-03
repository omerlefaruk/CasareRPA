"""
CasareRPA - LLM Nodes

AI-powered nodes for language model operations.
Supports OpenAI, Anthropic, Azure, and local models via LiteLLM.
"""

from casare_rpa.nodes.llm.llm_base import LLMBaseNode
from casare_rpa.nodes.llm.llm_nodes import (
    LLMChatNode,
    LLMClassifyNode,
    LLMCompletionNode,
    LLMExtractDataNode,
    LLMSummarizeNode,
    LLMTranslateNode,
)

__all__ = [
    "LLMBaseNode",
    "LLMCompletionNode",
    "LLMChatNode",
    "LLMExtractDataNode",
    "LLMSummarizeNode",
    "LLMClassifyNode",
    "LLMTranslateNode",
]
