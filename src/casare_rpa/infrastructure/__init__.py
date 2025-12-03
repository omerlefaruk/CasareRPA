"""
CasareRPA Infrastructure Layer - Framework & External Dependencies

This layer contains:
- Execution: Concrete execution engine implementations
- Persistence: File I/O, database adapters
- Adapters: Wrappers for external libraries (Playwright, UIAutomation)
- Agent: Standalone robot agent components
- Auth: Robot API key authentication
- Tunnel: Secure WebSocket tunnel for on-prem robots

Depends on: Domain layer (via ports)
Independent of: Presentation
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
]
