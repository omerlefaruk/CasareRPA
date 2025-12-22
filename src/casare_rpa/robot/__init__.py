"""
CasareRPA Robot Agent

Distributed robot agent for workflow execution with full lifecycle management.

Main Components:
- RobotAgent: Unified robot agent
- RobotConfig: Configuration for robot agent
- CLI: Command-line interface for starting/stopping robots
- Windows Service: Run robot as Windows service

Usage:
    # Start robot via CLI
    python -m casare_rpa.robot.cli start

    # Or programmatically
    from casare_rpa.robot import RobotAgent, RobotConfig

    config = RobotConfig.from_env()
    agent = RobotAgent(config)
    await agent.start()
"""

# Unified agent
from casare_rpa.robot.agent import (
    AgentCheckpoint,
    AgentState,
    RobotAgent,
    RobotCapabilities,
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

# Metrics
from casare_rpa.robot.metrics import (
    JobMetrics,
    MetricsCollector,
    NodeMetrics,
    ResourceSnapshot,
    get_metrics_collector,
)

__all__ = [
    # Agent
    "RobotAgent",
    "RobotConfig",
    "RobotCapabilities",
    "AgentState",
    "AgentCheckpoint",
    "run_agent",
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
