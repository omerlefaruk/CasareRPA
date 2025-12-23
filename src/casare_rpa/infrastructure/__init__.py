"""
CasareRPA - Infrastructure Layer

Framework integrations, external adapters, and technical implementations.

Entry Points:
    - agent.RobotAgent: Standalone robot agent for headless execution
    - agent.JobExecutor: Job execution engine
    - auth.RobotApiKeyService: API key management for robot authentication
    - tunnel.AgentTunnel: Secure WebSocket tunnel for on-prem robots
    - http.UnifiedHttpClient: Resilient HTTP client with retry/circuit breaker
    - http.get_unified_http_client: Factory for HTTP client singleton

Key Patterns:
    - Adapters: Wrap external libraries (Playwright, UIAutomation, aiohttp)
    - Repository Pattern: Persistence abstraction for workflows, credentials
    - Factory Pattern: Create complex objects (HTTP clients, browser contexts)
    - Singleton: Shared resources (HTTP client, credential cache)
    - Circuit Breaker: Resilience for external API calls
    - mTLS: Mutual TLS for secure robot-orchestrator communication

Related:
    - Domain layer: Implements domain protocols (CredentialProviderProtocol)
    - Application layer: Provides implementations for use case dependencies
    - Presentation layer: Shares event bus, configuration services
    - Robot application: Uses agent, tunnel, auth components

Depends on: Domain layer (via protocols)
Independent of: Presentation layer
"""

# Agent exports
from casare_rpa.infrastructure.agent import (
    HeartbeatService,
    JobExecutionError,
    JobExecutionResult,
    JobExecutor,
)

# AI exports
from casare_rpa.infrastructure.ai import (
    SmartWorkflowAgent,
    WorkflowGenerationResult,
    generate_smart_workflow,
)

# Analytics exports
from casare_rpa.infrastructure.analytics import (
    MetricsAggregator,
    ProcessMiner,
)

# Auth exports
from casare_rpa.infrastructure.auth import (
    ApiKeyValidationResult,
    RobotApiKey,
    RobotApiKeyError,
    RobotApiKeyService,
    generate_api_key_raw,
    hash_api_key,
)

# Browser exports
from casare_rpa.infrastructure.browser import (
    PlaywrightManager,
    get_playwright_singleton,
)

# Caching exports
from casare_rpa.infrastructure.caching import (
    WorkflowCache,
    get_workflow_cache,
)

# HTTP exports
from casare_rpa.infrastructure.http import (
    RequestStats,
    UnifiedHttpClient,
    UnifiedHttpClientConfig,
    close_unified_http_client,
    get_unified_http_client,
)

# Observability exports
from casare_rpa.infrastructure.observability import (
    Observability,
    configure_observability,
)

# Queue exports
from casare_rpa.infrastructure.queue import (
    PgQueuerConsumer,
    PgQueuerProducer,
)

# Security exports
from casare_rpa.infrastructure.security import (
    AuthorizationService,
    VaultClient,
)

# Tunnel exports
from casare_rpa.infrastructure.tunnel import (
    AgentTunnel,
    CertificateManager,
    MTLSConfig,
    TunnelConfig,
    TunnelState,
)

# Robot agent (canonical location)
from casare_rpa.robot.agent import RobotAgent, RobotConfig

__all__ = [
    # Agent
    "RobotConfig",
    "RobotAgent",
    "JobExecutor",
    "JobExecutionError",
    "JobExecutionResult",
    "HeartbeatService",
    # Auth
    "RobotApiKey",
    "RobotApiKeyService",
    "RobotApiKeyError",
    "ApiKeyValidationResult",
    "generate_api_key_raw",
    "hash_api_key",
    # Tunnel
    "AgentTunnel",
    "TunnelConfig",
    "TunnelState",
    "MTLSConfig",
    "CertificateManager",
    # AI
    "SmartWorkflowAgent",
    "generate_smart_workflow",
    "WorkflowGenerationResult",
    # Browser
    "PlaywrightManager",
    "get_playwright_singleton",
    # Observability
    "Observability",
    "configure_observability",
    # Analytics
    "MetricsAggregator",
    "ProcessMiner",
    # Security
    "VaultClient",
    "AuthorizationService",
    # Queue
    "PgQueuerConsumer",
    "PgQueuerProducer",
    # HTTP
    "UnifiedHttpClient",
    "UnifiedHttpClientConfig",
    "RequestStats",
    "get_unified_http_client",
    "close_unified_http_client",
    # Caching
    "WorkflowCache",
    "get_workflow_cache",
]
