"""
CasareRPA - LLM Nodes

AI-powered nodes for language model operations.
Supports OpenAI, Anthropic, Azure, and local models via LiteLLM.

Includes:
- Basic LLM operations (completion, chat, extract, summarize, classify, translate)
- AI condition nodes for natural language workflow control
- AI agent node for autonomous multi-step reasoning
- RAG nodes (embeddings, vector store, semantic search)
- Prompt template nodes (reusable AI tasks)
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
from casare_rpa.nodes.llm.ai_condition_node import AIConditionNode
from casare_rpa.nodes.llm.ai_switch_node import AISwitchNode
from casare_rpa.nodes.llm.ai_decision_table_node import AIDecisionTableNode
from casare_rpa.nodes.llm.ai_agent_node import AIAgentNode
from casare_rpa.nodes.llm.rag_nodes import (
    EmbeddingNode,
    RAGNode,
    VectorSearchNode,
    VectorStoreAddNode,
    VectorStoreDeleteNode,
)
from casare_rpa.nodes.llm.prompt_template_node import (
    GetTemplateInfoNode,
    ListTemplatesNode,
    PromptTemplateNode,
)

__all__ = [
    # Base
    "LLMBaseNode",
    # Basic LLM operations
    "LLMCompletionNode",
    "LLMChatNode",
    "LLMExtractDataNode",
    "LLMSummarizeNode",
    "LLMClassifyNode",
    "LLMTranslateNode",
    # AI Condition nodes
    "AIConditionNode",
    "AISwitchNode",
    "AIDecisionTableNode",
    # AI Agent
    "AIAgentNode",
    # RAG nodes
    "EmbeddingNode",
    "VectorStoreAddNode",
    "VectorSearchNode",
    "RAGNode",
    "VectorStoreDeleteNode",
    # Prompt template nodes
    "PromptTemplateNode",
    "ListTemplatesNode",
    "GetTemplateInfoNode",
]
