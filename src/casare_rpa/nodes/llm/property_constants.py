"""
Property constants for LLM nodes.

Provides reusable PropertyDef definitions to ensure consistency
across all LLM-related nodes (completion, chat, extraction, agents).

Usage:
    from casare_rpa.nodes.llm.property_constants import (
        LLM_MODEL,
        LLM_TEMPERATURE,
        LLM_MAX_TOKENS,
    )

    @properties(
        PropertyDef("prompt", PropertyType.TEXT, essential=True),
        LLM_MODEL,
        LLM_TEMPERATURE,
        LLM_MAX_TOKENS,
    )
    @node(category="llm")
    class MyLLMNode(LLMBaseNode):
        ...
"""

from casare_rpa.domain.schemas import PropertyDef, PropertyType


# =============================================================================
# Model Selection Properties
# =============================================================================

LLM_MODEL = PropertyDef(
    "model",
    PropertyType.STRING,
    default="gpt-4o-mini",
    label="Model",
    tooltip="LLM model to use",
)

LLM_MODEL_EMBEDDING = PropertyDef(
    "model",
    PropertyType.STRING,
    default="text-embedding-3-small",
    label="Model",
    tooltip="Embedding model to use",
)


# =============================================================================
# Generation Parameters
# =============================================================================

LLM_TEMPERATURE = PropertyDef(
    "temperature",
    PropertyType.FLOAT,
    default=0.7,
    min_value=0.0,
    max_value=2.0,
    label="Temperature",
    tooltip="Creativity/randomness (0-2)",
)

LLM_TEMPERATURE_LOW = PropertyDef(
    "temperature",
    PropertyType.FLOAT,
    default=0.0,
    min_value=0.0,
    max_value=2.0,
    label="Temperature",
    tooltip="Low temperature for consistent evaluation",
)

LLM_TEMPERATURE_MEDIUM = PropertyDef(
    "temperature",
    PropertyType.FLOAT,
    default=0.5,
    min_value=0.0,
    max_value=2.0,
    label="Temperature",
    tooltip="Balanced temperature for creative yet consistent output",
)

LLM_TEMPERATURE_TRANSLATION = PropertyDef(
    "temperature",
    PropertyType.FLOAT,
    default=0.3,
    min_value=0.0,
    max_value=2.0,
    label="Temperature",
    tooltip="Low temperature for accurate translation",
)

LLM_MAX_TOKENS = PropertyDef(
    "max_tokens",
    PropertyType.INTEGER,
    default=1000,
    min_value=1,
    label="Max Tokens",
    tooltip="Maximum response length",
)


# =============================================================================
# System/Context Properties
# =============================================================================

LLM_SYSTEM_PROMPT = PropertyDef(
    "system_prompt",
    PropertyType.TEXT,
    default="",
    label="System Prompt",
    tooltip="Optional system prompt for context",
)


# =============================================================================
# Input Content Properties
# =============================================================================

LLM_PROMPT = PropertyDef(
    "prompt",
    PropertyType.TEXT,
    default="",
    label="Prompt",
    placeholder="Enter your prompt...",
    tooltip="The prompt to send to the LLM",
    essential=True,
)

LLM_MESSAGE = PropertyDef(
    "message",
    PropertyType.TEXT,
    default="",
    label="Message",
    placeholder="Enter your message...",
    tooltip="The message to send to the LLM",
    essential=True,
)

LLM_TEXT_INPUT = PropertyDef(
    "text",
    PropertyType.TEXT,
    default="",
    label="Text",
    placeholder="Text to process...",
    tooltip="The text to process",
    essential=True,
)

LLM_QUESTION = PropertyDef(
    "question",
    PropertyType.TEXT,
    default="",
    label="Question",
    placeholder="Ask a question...",
    tooltip="Question to answer",
    essential=True,
)

LLM_CONDITION = PropertyDef(
    "condition",
    PropertyType.TEXT,
    default="",
    label="Condition",
    placeholder="Is the email about a complaint?",
    tooltip="Natural language condition to evaluate",
    essential=True,
)

LLM_GOAL = PropertyDef(
    "goal",
    PropertyType.TEXT,
    default="",
    label="Goal",
    placeholder="Find the order status for customer 12345...",
    tooltip="The goal for the AI agent to accomplish",
    essential=True,
)


# =============================================================================
# Agent/Workflow Properties
# =============================================================================

LLM_MAX_STEPS = PropertyDef(
    "max_steps",
    PropertyType.INTEGER,
    default=10,
    min_value=1,
    max_value=50,
    label="Max Steps",
    tooltip="Maximum reasoning steps",
)

LLM_TIMEOUT = PropertyDef(
    "timeout",
    PropertyType.FLOAT,
    default=300.0,
    min_value=10.0,
    label="Timeout (sec)",
    tooltip="Maximum execution time in seconds",
)

LLM_AVAILABLE_TOOLS = PropertyDef(
    "available_tools",
    PropertyType.STRING,
    default="",
    label="Available Tools",
    placeholder="read_file, http_request, calculate",
    tooltip="Comma-separated list of tools the agent can use",
)


# =============================================================================
# Classification/Switch Properties
# =============================================================================

LLM_OPTIONS = PropertyDef(
    "options",
    PropertyType.STRING,
    default="",
    label="Options",
    placeholder="invoice, receipt, contract, other",
    tooltip="Comma-separated list of options/categories",
    essential=True,
)

LLM_CATEGORIES = PropertyDef(
    "categories",
    PropertyType.STRING,
    default="",
    label="Categories",
    placeholder="positive, negative, neutral",
    tooltip="Comma-separated list of categories",
    essential=True,
)

LLM_MULTI_LABEL = PropertyDef(
    "multi_label",
    PropertyType.BOOLEAN,
    default=False,
    label="Multi-label",
    tooltip="Allow multiple categories per text",
)


# =============================================================================
# RAG/Vector Properties
# =============================================================================

LLM_COLLECTION = PropertyDef(
    "collection",
    PropertyType.STRING,
    default="default",
    label="Collection",
    placeholder="my_collection",
    tooltip="Vector store collection name",
)

LLM_TOP_K = PropertyDef(
    "top_k",
    PropertyType.INTEGER,
    default=5,
    min_value=1,
    max_value=100,
    label="Top K",
    tooltip="Number of results to return",
)

LLM_TOP_K_CONTEXT = PropertyDef(
    "top_k",
    PropertyType.INTEGER,
    default=3,
    min_value=1,
    max_value=20,
    label="Context Documents",
    tooltip="Number of context documents to retrieve",
)


# =============================================================================
# Translation Properties
# =============================================================================

LLM_TARGET_LANGUAGE = PropertyDef(
    "target_language",
    PropertyType.STRING,
    default="",
    label="Target Language",
    placeholder="Spanish, French, German...",
    tooltip="Language to translate to",
    essential=True,
)

LLM_SOURCE_LANGUAGE = PropertyDef(
    "source_language",
    PropertyType.STRING,
    default="",
    label="Source Language",
    placeholder="Auto-detect if empty",
    tooltip="Optional source language (auto-detect if empty)",
)


# =============================================================================
# Template Properties
# =============================================================================

LLM_TEMPLATE_ID = PropertyDef(
    "template_id",
    PropertyType.STRING,
    default="",
    label="Template ID",
    placeholder="my_template",
    tooltip="ID of the prompt template to use",
    essential=True,
)

LLM_EXECUTE = PropertyDef(
    "execute",
    PropertyType.BOOLEAN,
    default=True,
    label="Execute with LLM",
    tooltip="Execute the rendered prompt with LLM (or just render)",
)


# =============================================================================
# Summarization Properties
# =============================================================================

LLM_MAX_LENGTH = PropertyDef(
    "max_length",
    PropertyType.INTEGER,
    default=200,
    min_value=10,
    label="Max Length (words)",
    tooltip="Maximum length of summary in words",
)

LLM_SUMMARY_STYLE = PropertyDef(
    "style",
    PropertyType.CHOICE,
    default="paragraph",
    choices=["paragraph", "bullet_points", "key_points"],
    label="Style",
    tooltip="Summarization style",
)


# =============================================================================
# Chat Properties
# =============================================================================

LLM_CONVERSATION_ID = PropertyDef(
    "conversation_id",
    PropertyType.STRING,
    default="",
    label="Conversation ID",
    tooltip="Optional ID to continue a conversation",
)


# =============================================================================
# Decision Table Properties
# =============================================================================

LLM_DECISION_TABLE = PropertyDef(
    "decision_table",
    PropertyType.TEXT,
    default="",
    label="Decision Table",
    placeholder='{"rules": [...], "default_action": "..."}',
    tooltip="JSON decision table with rules and default action",
    essential=True,
)


# =============================================================================
# Schema Properties
# =============================================================================

LLM_SCHEMA = PropertyDef(
    "schema",
    PropertyType.TEXT,
    default="",
    label="JSON Schema",
    placeholder='{"name": "string", "age": "integer"}',
    tooltip="JSON schema defining the structure to extract",
    essential=True,
)


# =============================================================================
# Helper Functions for Common Property Groups
# =============================================================================


def get_llm_base_properties() -> list[PropertyDef]:
    """Get common LLM base properties (model, temperature, max_tokens)."""
    return [LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS]


def get_llm_completion_properties() -> list[PropertyDef]:
    """Get standard LLM completion properties."""
    return [
        LLM_PROMPT,
        LLM_MODEL,
        LLM_SYSTEM_PROMPT,
        LLM_TEMPERATURE,
        LLM_MAX_TOKENS,
    ]


def get_llm_chat_properties() -> list[PropertyDef]:
    """Get standard LLM chat properties."""
    return [
        LLM_MESSAGE,
        LLM_CONVERSATION_ID,
        LLM_MODEL,
        LLM_SYSTEM_PROMPT,
        LLM_TEMPERATURE,
        LLM_MAX_TOKENS,
    ]


def get_llm_condition_properties() -> list[PropertyDef]:
    """Get standard AI condition properties."""
    return [LLM_CONDITION, LLM_MODEL, LLM_TEMPERATURE_LOW]


def get_llm_switch_properties() -> list[PropertyDef]:
    """Get standard AI switch properties."""
    return [LLM_QUESTION, LLM_OPTIONS, LLM_MODEL, LLM_TEMPERATURE_LOW]


def get_llm_agent_properties() -> list[PropertyDef]:
    """Get standard AI agent properties."""
    return [LLM_GOAL, LLM_AVAILABLE_TOOLS, LLM_MODEL, LLM_MAX_STEPS, LLM_TIMEOUT]


def get_llm_classification_properties() -> list[PropertyDef]:
    """Get standard classification properties."""
    return [
        LLM_TEXT_INPUT,
        LLM_CATEGORIES,
        LLM_MULTI_LABEL,
        LLM_MODEL,
        LLM_TEMPERATURE_LOW,
    ]


def get_llm_translation_properties() -> list[PropertyDef]:
    """Get standard translation properties."""
    return [
        LLM_TEXT_INPUT,
        LLM_TARGET_LANGUAGE,
        LLM_SOURCE_LANGUAGE,
        LLM_MODEL,
        LLM_TEMPERATURE_TRANSLATION,
    ]


def get_llm_rag_properties() -> list[PropertyDef]:
    """Get standard RAG properties."""
    return [
        LLM_QUESTION,
        LLM_COLLECTION,
        LLM_TOP_K_CONTEXT,
        LLM_MODEL,
        LLM_TEMPERATURE,
        LLM_MAX_TOKENS,
    ]


__all__ = [
    # Model properties
    "LLM_MODEL",
    "LLM_MODEL_EMBEDDING",
    # Generation parameters
    "LLM_TEMPERATURE",
    "LLM_TEMPERATURE_LOW",
    "LLM_TEMPERATURE_MEDIUM",
    "LLM_TEMPERATURE_TRANSLATION",
    "LLM_MAX_TOKENS",
    # System/context
    "LLM_SYSTEM_PROMPT",
    # Input content
    "LLM_PROMPT",
    "LLM_MESSAGE",
    "LLM_TEXT_INPUT",
    "LLM_QUESTION",
    "LLM_CONDITION",
    "LLM_GOAL",
    # Agent/workflow
    "LLM_MAX_STEPS",
    "LLM_TIMEOUT",
    "LLM_AVAILABLE_TOOLS",
    # Classification/switch
    "LLM_OPTIONS",
    "LLM_CATEGORIES",
    "LLM_MULTI_LABEL",
    # RAG/vector
    "LLM_COLLECTION",
    "LLM_TOP_K",
    "LLM_TOP_K_CONTEXT",
    # Translation
    "LLM_TARGET_LANGUAGE",
    "LLM_SOURCE_LANGUAGE",
    # Template
    "LLM_TEMPLATE_ID",
    "LLM_EXECUTE",
    # Summarization
    "LLM_MAX_LENGTH",
    "LLM_SUMMARY_STYLE",
    # Chat
    "LLM_CONVERSATION_ID",
    # Decision table
    "LLM_DECISION_TABLE",
    # Schema
    "LLM_SCHEMA",
    # Helper functions
    "get_llm_base_properties",
    "get_llm_completion_properties",
    "get_llm_chat_properties",
    "get_llm_condition_properties",
    "get_llm_switch_properties",
    "get_llm_agent_properties",
    "get_llm_classification_properties",
    "get_llm_translation_properties",
    "get_llm_rag_properties",
]
