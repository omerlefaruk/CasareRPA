"""
CasareRPA - AI Infrastructure Module

Provides AI-powered workflow generation and node manifest services.

Components:
    - registry_dumper: Generate node manifests for LLM consumption
    - smart_agent: LLM-powered workflow generation with validation

Features:
    - Configurable agent behavior via AgentConfig
    - Performance-optimized workflow generation
    - Comprehensive error handling and logging
    - Retry logic with exponential backoff

Usage:
    from casare_rpa.infrastructure.ai import (
        # Manifest generation
        dump_node_manifest,
        manifest_to_markdown,
        manifest_to_compact_markdown,
        NodeManifest,
        NodeManifestEntry,
        # Smart workflow agent
        SmartWorkflowAgent,
        WorkflowGenerationResult,
        HeadlessWorkflowSandbox,
        generate_smart_workflow,
        # Exceptions
        WorkflowGenerationError,
        LLMCallError,
        JSONParseError,
        ValidationError,
    )

    # Performance-optimized generation
    from casare_rpa.domain.ai import PERFORMANCE_OPTIMIZED_CONFIG
    agent = SmartWorkflowAgent(config=PERFORMANCE_OPTIMIZED_CONFIG)
"""

from casare_rpa.infrastructure.ai.registry_dumper import (
    dump_node_manifest,
    manifest_to_markdown,
    manifest_to_compact_markdown,
    manifest_to_json,
    get_nodes_by_category,
    get_cached_manifest,
    clear_manifest_cache,
    NodeManifest,
    NodeManifestEntry,
    PortManifestEntry,
)

from casare_rpa.infrastructure.ai.smart_agent import (
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
)

from casare_rpa.infrastructure.ai.ai_recovery_analyzer import (
    AIRecoveryAnalyzer,
    RecoveryRecommendation,
    RecoveryStrategy,
    ErrorContext,
)

from casare_rpa.infrastructure.ai.smart_selector_generator import (
    SmartSelectorGenerator,
    GeneratedSelector,
)

from casare_rpa.infrastructure.ai.agent_tools import (
    ParameterSpec,
    AgentTool,
    AgentToolRegistry,
    get_default_tool_registry,
)

from casare_rpa.infrastructure.ai.agent_executor import (
    StepType,
    AgentExecutor,
    AgentStep,
    AgentResult,
)

from casare_rpa.infrastructure.ai.embedding_manager import (
    EmbeddingManager,
    EmbeddingConfig,
    EmbeddingResult,
    BatchEmbeddingResult,
    EmbeddingMetrics,
    get_embedding_manager,
)

from casare_rpa.infrastructure.ai.vector_store import (
    VectorStore,
    Document,
    SearchResult,
    VectorStoreMetrics,
    get_vector_store,
    get_default_persist_path,
)

from casare_rpa.infrastructure.ai.prompt_template_manager import (
    PromptTemplateManager,
    get_prompt_template_manager,
)

from casare_rpa.infrastructure.ai.playwright_mcp import (
    PlaywrightMCPClient,
    MCPToolResult,
    fetch_page_context,
)

from casare_rpa.infrastructure.ai.page_analyzer import (
    PageAnalyzer,
    PageContext,
    FormInfo,
    FormField,
    analyze_page,
)

__all__ = [
    # Registry dumper
    "dump_node_manifest",
    "manifest_to_markdown",
    "manifest_to_compact_markdown",
    "manifest_to_json",
    "get_nodes_by_category",
    "get_cached_manifest",
    "clear_manifest_cache",
    "NodeManifest",
    "NodeManifestEntry",
    "PortManifestEntry",
    # Smart agent
    "SmartWorkflowAgent",
    "WorkflowGenerationResult",
    "GenerationAttempt",
    "HeadlessWorkflowSandbox",
    "generate_smart_workflow",
    # Exceptions
    "WorkflowGenerationError",
    "LLMCallError",
    "JSONParseError",
    "ValidationError",
    "MaxRetriesExceededError",
    # AI Recovery
    "AIRecoveryAnalyzer",
    "RecoveryRecommendation",
    "RecoveryStrategy",
    "ErrorContext",
    # Smart Selector
    "SmartSelectorGenerator",
    "GeneratedSelector",
    # Agent Tools
    "ParameterSpec",
    "AgentTool",
    "AgentToolRegistry",
    "get_default_tool_registry",
    # Agent Executor
    "StepType",
    "AgentExecutor",
    "AgentStep",
    "AgentResult",
    # Embedding Manager
    "EmbeddingManager",
    "EmbeddingConfig",
    "EmbeddingResult",
    "BatchEmbeddingResult",
    "EmbeddingMetrics",
    "get_embedding_manager",
    # Vector Store
    "VectorStore",
    "Document",
    "SearchResult",
    "VectorStoreMetrics",
    "get_vector_store",
    "get_default_persist_path",
    # Prompt Template Manager
    "PromptTemplateManager",
    "get_prompt_template_manager",
    # Playwright MCP
    "PlaywrightMCPClient",
    "MCPToolResult",
    "fetch_page_context",
    # Page Analyzer
    "PageAnalyzer",
    "PageContext",
    "FormInfo",
    "FormField",
    "analyze_page",
]
