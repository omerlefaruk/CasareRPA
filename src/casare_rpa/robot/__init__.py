"""
CasareRPA Robot Agent

Distributed robot agent for workflow execution with PostgreSQL/PgQueuer backend.

Main Components:
- DistributedRobotAgent: Enterprise robot agent with job queue integration
- CLI: Command-line interface for starting/stopping robots

Usage:
    # Start robot via CLI
    python -m casare_rpa.robot.cli start

    # Or programmatically
    from casare_rpa.robot import DistributedRobotAgent, DistributedRobotConfig

    config = DistributedRobotConfig(
        postgres_url="postgresql://user:pass@localhost/casare_rpa",
        robot_id="worker-01",
    )
    agent = DistributedRobotAgent(config)
    await agent.start()
"""

from .distributed_agent import (
    DistributedRobotAgent,
    DistributedRobotConfig,
    RobotCapabilities,
    RobotRegistration,
    AgentState,
)
from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    CircuitBreakerRegistry,
    CircuitState,
    get_circuit_breaker,
    get_circuit_breaker_registry,
)
from .offline_queue import (
    OfflineQueue,
    CachedJobStatus,
)
from .checkpoint import (
    CheckpointManager,
    CheckpointState,
    ResumableRunner,
    create_checkpoint_state,
)
from .metrics import (
    MetricsCollector,
    JobMetrics,
    NodeMetrics,
    ResourceSnapshot,
    get_metrics_collector,
)
from .audit import (
    AuditLogger,
    AuditEntry,
    AuditEventType,
    AuditSeverity,
    get_audit_logger,
    init_audit_logger,
)
from .progress_reporter import (
    ProgressReporter,
    ProgressStage,
    CancellationChecker,
    JobLocker,
)
from .job_executor import (
    JobExecutor,
    JobExecutorConfig,
    JobInfo,
    JobStatus,
)

__all__ = [
    # Main agent
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
    # Offline queue
    "OfflineQueue",
    "CachedJobStatus",
    # Checkpoint
    "CheckpointManager",
    "CheckpointState",
    "ResumableRunner",
    "create_checkpoint_state",
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
    # Progress
    "ProgressReporter",
    "ProgressStage",
    "CancellationChecker",
    "JobLocker",
    # Job executor
    "JobExecutor",
    "JobExecutorConfig",
    "JobInfo",
    "JobStatus",
]
