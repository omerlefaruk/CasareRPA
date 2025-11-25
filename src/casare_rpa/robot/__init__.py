"""
CasareRPA Robot Agent

Phase 8B: Hardened robot with connection resilience, job management,
checkpointing, and comprehensive observability.
"""

from .agent import RobotAgent, run_robot
from .config import (
    RobotConfig,
    ConnectionConfig,
    CircuitBreakerConfig,
    JobExecutionConfig,
    ObservabilityConfig,
    get_config,
    get_robot_id,
    get_robot_name,
    validate_credentials,
    validate_credentials_async,
    # Legacy exports
    ROBOT_NAME,
    SUPABASE_URL,
    SUPABASE_KEY,
)
from .connection import (
    ConnectionManager,
    ConnectionState,
    ConnectionConfig as ConnectionManagerConfig,
    ConnectionStats,
)
from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig as CBConfig,
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
    "RobotAgent",
    "run_robot",
    # Configuration
    "RobotConfig",
    "ConnectionConfig",
    "CircuitBreakerConfig",
    "JobExecutionConfig",
    "ObservabilityConfig",
    "get_config",
    "get_robot_id",
    "get_robot_name",
    "validate_credentials",
    "validate_credentials_async",
    # Legacy
    "ROBOT_NAME",
    "SUPABASE_URL",
    "SUPABASE_KEY",
    # Connection
    "ConnectionManager",
    "ConnectionState",
    "ConnectionManagerConfig",
    "ConnectionStats",
    # Circuit breaker
    "CircuitBreaker",
    "CBConfig",
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
