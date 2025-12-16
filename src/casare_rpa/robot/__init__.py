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

    # Legacy (deprecated) - Removed
    # from casare_rpa.robot import DistributedRobotAgent, DistributedRobotConfig
"""

# New unified agent (recommended)
from casare_rpa.robot.agent import (
    AgentCheckpoint,
    AgentState as UnifiedAgentState,
    RobotAgent,
    RobotCapabilities as UnifiedRobotCapabilities,
    RobotConfig,
    run_agent,
)

# Audit
from casare_rpa.robot.audit import (
    AuditEntry,
    AuditEventType,
    AuditLogger,
    AuditSeverity,
    get_audit_logger,
    init_audit_logger,
)

# Circuit breaker
from casare_rpa.robot.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    CircuitBreakerRegistry,
    CircuitState,
    get_circuit_breaker,
    get_circuit_breaker_registry,
)

# Legacy imports (deprecated - for backward compatibility)
# Legacy imports removed


# Metrics
from casare_rpa.robot.metrics import (
    JobMetrics,
    MetricsCollector,
    NodeMetrics,
    ResourceSnapshot,
    get_metrics_collector,
)

# Note: coordination.py has been removed. For fleet coordination functionality, use:
# - infrastructure/orchestrator/scheduling/job_assignment.py - JobAssignmentEngine
# - infrastructure/orchestrator/scheduling/state_affinity.py - StateAffinityManager

__all__ = [
    # Unified agent (recommended)
    "RobotAgent",
    "RobotConfig",
    "UnifiedRobotCapabilities",
    "UnifiedAgentState",
    "AgentCheckpoint",
    "run_agent",
    # Legacy agent (deprecated)
    # "DistributedRobotAgent", - Removed
    # "DistributedRobotConfig", - Removed
    # "RobotCapabilities", - Removed
    # "RobotRegistration", - Removed
    # "AgentState", - Removed
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
