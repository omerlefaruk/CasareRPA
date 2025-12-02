"""
CasareRPA Robot Agent

Distributed robot agent for workflow execution with full lifecycle management.

Main Components:
- RobotAgent: Unified robot agent (recommended)
- RobotConfig: Configuration for robot agent
- DistributedRobotAgent: Legacy agent (deprecated, use RobotAgent)
- CLI: Command-line interface for starting/stopping robots
- Windows Service: Run robot as Windows service

Usage:
    # Start robot via CLI
    python -m casare_rpa.robot.cli start

    # Or programmatically (recommended)
    from casare_rpa.robot import RobotAgent, RobotConfig

    config = RobotConfig.from_env()
    agent = RobotAgent(config)
    await agent.start()

    # Legacy (deprecated)
    from casare_rpa.robot import DistributedRobotAgent, DistributedRobotConfig
"""

# New unified agent (recommended)
from .agent import (
    RobotAgent,
    RobotConfig,
    RobotCapabilities as UnifiedRobotCapabilities,
    AgentState as UnifiedAgentState,
    AgentCheckpoint,
    run_agent,
)

# Legacy imports (deprecated - for backward compatibility)
from .distributed_agent import (
    DistributedRobotAgent,
    DistributedRobotConfig,
    RobotCapabilities,
    RobotRegistration,
    AgentState,
)

# Circuit breaker
from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    CircuitBreakerRegistry,
    CircuitState,
    get_circuit_breaker,
    get_circuit_breaker_registry,
)

# Metrics
from .metrics import (
    MetricsCollector,
    JobMetrics,
    NodeMetrics,
    ResourceSnapshot,
    get_metrics_collector,
)

# Audit
from .audit import (
    AuditLogger,
    AuditEntry,
    AuditEventType,
    AuditSeverity,
    get_audit_logger,
    init_audit_logger,
)

__all__ = [
    # Unified agent (recommended)
    "RobotAgent",
    "RobotConfig",
    "UnifiedRobotCapabilities",
    "UnifiedAgentState",
    "AgentCheckpoint",
    "run_agent",
    # Legacy agent (deprecated)
    "DistributedRobotAgent",
    "DistributedRobotConfig",
    "RobotCapabilities",
    "RobotRegistration",
    "AgentState",
    # Circuit breaker
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerOpenError",
    "CircuitBreakerRegistry",
    "CircuitState",
    "get_circuit_breaker",
    "get_circuit_breaker_registry",
    # Metrics
    "MetricsCollector",
    "JobMetrics",
    "NodeMetrics",
    "ResourceSnapshot",
    "get_metrics_collector",
    # Audit
    "AuditLogger",
    "AuditEntry",
    "AuditEventType",
    "AuditSeverity",
    "get_audit_logger",
    "init_audit_logger",
]
