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

from casare_rpa.infrastructure.ai.agent import (
    GenerationAttempt,
    HeadlessWorkflowSandbox,
    JSONParseError,
    LLMCallError,
    MaxRetriesExceededError,
    SmartWorkflowAgent,
    ValidationError,
    WorkflowGenerationError,
    WorkflowGenerationResult,
    generate_smart_workflow,
)
from casare_rpa.infrastructure.ai.agent_executor import (
    AgentExecutor,
    AgentResult,
    AgentStep,
    StepType,
)
from casare_rpa.infrastructure.ai.agent_tools import (
    AgentTool,
    AgentToolRegistry,
    ParameterSpec,
    get_default_tool_registry,
)
from casare_rpa.infrastructure.ai.ai_recovery_analyzer import (
    AIRecoveryAnalyzer,
    ErrorContext,
    RecoveryRecommendation,
    RecoveryStrategy,
)
from casare_rpa.infrastructure.ai.embedding_manager import (
    BatchEmbeddingResult,
    EmbeddingConfig,
    EmbeddingManager,
    EmbeddingMetrics,
    EmbeddingResult,
    get_embedding_manager,
)
from casare_rpa.infrastructure.ai.glm_client import (
    MODEL_GLM_4_5,
    MODEL_GLM_4_6,
    MODEL_GLM_4_7,
    MODEL_GLM_4_FLASH,
    MODEL_GLM_4_FLASHX,
    GLMClient,
    GLMClientError,
    GLMResponse,
    RateLimitError,
)
from casare_rpa.infrastructure.ai.page_analyzer import (
    FormField,
    FormInfo,
    PageAnalyzer,
    PageContext,
    analyze_page,
)
from casare_rpa.infrastructure.ai.playwright_mcp import (
    MCPToolResult,
    PlaywrightMCPClient,
    fetch_page_context,
)
from casare_rpa.infrastructure.ai.prompt_template_manager import (
    PromptTemplateManager,
    get_prompt_template_manager,
)
from casare_rpa.infrastructure.ai.registry_dumper import (
    NodeManifest,
    NodeManifestEntry,
    PortManifestEntry,
    clear_manifest_cache,
    dump_node_manifest,
    get_cached_manifest,
    get_nodes_by_category,
    manifest_to_compact_markdown,
    manifest_to_json,
    manifest_to_markdown,
)
from casare_rpa.infrastructure.ai.smart_selector_generator import (
    GeneratedSelector,
    SmartSelectorGenerator,
)
from casare_rpa.infrastructure.ai.vector_store import (
    Document,
    SearchResult,
    VectorStore,
    VectorStoreMetrics,
    get_default_persist_path,
    get_vector_store,
)

__all__ = [
    # GLM Client
    "GLMClient",
    "GLMClientError",
    "GLMResponse",
    "MODEL_GLM_4_5",
    "MODEL_GLM_4_6",
    "MODEL_GLM_4_7",
    "MODEL_GLM_4_FLASH",
    "MODEL_GLM_4_FLASHX",
    "RateLimitError",
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
