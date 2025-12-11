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
]
