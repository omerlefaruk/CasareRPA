"""AI/ML Visual Nodes Package.

Visual node wrappers for LLM and AI operations.
Includes:
- Basic LLM nodes (completion, chat, extract, summarize, classify, translate)
- AI condition nodes for natural language workflow control
- AI agent node for autonomous multi-step reasoning
"""

from casare_rpa.presentation.canvas.visual_nodes.ai_ml.nodes import (
    # LLM nodes
    VisualLLMCompletionNode,
    VisualLLMChatNode,
    VisualLLMExtractDataNode,
    VisualLLMSummarizeNode,
    VisualLLMClassifyNode,
    VisualLLMTranslateNode,
    # AI Condition nodes
    VisualAIConditionNode,
    VisualAISwitchNode,
    VisualAIDecisionTableNode,
    # AI Agent
    VisualAIAgentNode,
)

__all__ = [
    # LLM nodes
    "VisualLLMCompletionNode",
    "VisualLLMChatNode",
    "VisualLLMExtractDataNode",
    "VisualLLMSummarizeNode",
    "VisualLLMClassifyNode",
    "VisualLLMTranslateNode",
    # AI Condition nodes
    "VisualAIConditionNode",
    "VisualAISwitchNode",
    "VisualAIDecisionTableNode",
    # AI Agent
    "VisualAIAgentNode",
]
