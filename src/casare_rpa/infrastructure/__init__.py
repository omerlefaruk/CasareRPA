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

# Agent exports (lazy import to avoid circular dependencies)
from casare_rpa.infrastructure.agent import (
    RobotConfig,
    RobotAgent,
    JobExecutor,
    HeartbeatService,
    ConfigurationError,
    RobotAgentError,
    JobExecutionError,
)

# Auth exports
from casare_rpa.infrastructure.auth import (
    RobotApiKey,
    RobotApiKeyService,
    RobotApiKeyError,
    ApiKeyValidationResult,
    generate_api_key_raw,
    hash_api_key,
)

# Tunnel exports
from casare_rpa.infrastructure.tunnel import (
    AgentTunnel,
    TunnelConfig,
    TunnelState,
    MTLSConfig,
    CertificateManager,
)

# HTTP exports
from casare_rpa.infrastructure.http import (
    UnifiedHttpClient,
    UnifiedHttpClientConfig,
    RequestStats,
    get_unified_http_client,
    close_unified_http_client,
)

__all__ = [
    # Agent
    "RobotConfig",
    "RobotAgent",
    "JobExecutor",
    "HeartbeatService",
    "ConfigurationError",
    "RobotAgentError",
    "JobExecutionError",
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
    # HTTP
    "UnifiedHttpClient",
    "UnifiedHttpClientConfig",
    "RequestStats",
    "get_unified_http_client",
    "close_unified_http_client",
]
