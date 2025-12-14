"""AI/ML Visual Nodes Package.

Visual node wrappers for LLM and AI operations.
Includes:
- Basic LLM nodes (completion, chat, extract, summarize, classify, translate)
- AI condition nodes for natural language workflow control
- AI agent node for autonomous multi-step reasoning
- RAG nodes (embedding, vector store, semantic search)
- Prompt template nodes
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
    # RAG nodes
    VisualEmbeddingNode,
    VisualVectorStoreAddNode,
    VisualVectorSearchNode,
    VisualRAGNode,
    VisualVectorStoreDeleteNode,
    # Prompt Template nodes
    VisualPromptTemplateNode,
    VisualListTemplatesNode,
    VisualGetTemplateInfoNode,
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
    # RAG nodes
    "VisualEmbeddingNode",
    "VisualVectorStoreAddNode",
    "VisualVectorSearchNode",
    "VisualRAGNode",
    "VisualVectorStoreDeleteNode",
    # Prompt Template nodes
    "VisualPromptTemplateNode",
    "VisualListTemplatesNode",
    "VisualGetTemplateInfoNode",
]
