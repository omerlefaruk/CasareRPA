"""
CasareRPA Orchestrator Module.

Provides centralized management for:
- Robot fleet management
- Job queue and scheduling
- Workflow library
- Monitoring and analytics
"""

from .models import (
    Robot,
    RobotStatus,
    Workflow,
    WorkflowStatus,
    Job,
    JobStatus,
    JobPriority,
    Schedule,
    ScheduleFrequency,
    DashboardMetrics,
    JobHistoryEntry,
)
from .services import OrchestratorService, LocalStorageService
from .monitor_window import OrchestratorMonitor, run_orchestrator

# Job Queue Components
from .job_queue import (
    JobQueue,
    JobStateMachine,
    JobStateError,
    JobDeduplicator,
    JobTimeoutManager,
)

# Scheduler Components
try:
    from .scheduler import JobScheduler, ScheduleManager, calculate_next_run

    HAS_SCHEDULER = True
except ImportError:
    HAS_SCHEDULER = False

# Dispatcher Components
try:
    from .dispatcher import JobDispatcher, LoadBalancingStrategy, RobotPool

    HAS_DISPATCHER = True
except ImportError:
    HAS_DISPATCHER = False

# Engine
from .engine import OrchestratorEngine

# Protocol
from .protocol import Message, MessageType, MessageBuilder

# Server and Client
try:
    from .server import OrchestratorServer, RobotConnection

    HAS_SERVER = True
except ImportError:
    HAS_SERVER = False

try:
    from .client import RobotClient

    HAS_CLIENT = True
except ImportError:
    HAS_CLIENT = False

# Distribution
from .distribution import (
    DistributionStrategy,
    DistributionRule,
    DistributionResult,
    RobotSelector,
    WorkflowDistributor,
    JobRouter,
)

# Result Collection
from .results import (
    JobResult,
    ExecutionStatistics,
    ResultCollector,
    ResultExporter,
)

# Resilience (Error Recovery, Health Monitoring, Security)
from .resilience import (
    RecoveryStrategy,
    RecoveryAction,
    RetryPolicy,
    ErrorRecoveryManager,
    HealthStatus,
    HealthMetrics,
    HealthThresholds,
    HealthMonitor,
    TokenType,
    AuthToken,
    SecurityManager,
)


def main():
    """Entry point for orchestrator application."""
    return run_orchestrator()


__all__ = [
    # Models
    "Robot",
    "RobotStatus",
    "Workflow",
    "WorkflowStatus",
    "Job",
    "JobStatus",
    "JobPriority",
    "Schedule",
    "ScheduleFrequency",
    "DashboardMetrics",
    "JobHistoryEntry",
    # Services
    "OrchestratorService",
    "LocalStorageService",
    # Job Queue
    "JobQueue",
    "JobStateMachine",
    "JobStateError",
    "JobDeduplicator",
    "JobTimeoutManager",
    # Scheduler
    "JobScheduler",
    "ScheduleManager",
    "calculate_next_run",
    # Dispatcher
    "JobDispatcher",
    "LoadBalancingStrategy",
    "RobotPool",
    # Engine
    "OrchestratorEngine",
    # Protocol
    "Message",
    "MessageType",
    "MessageBuilder",
    # Server/Client
    "OrchestratorServer",
    "RobotConnection",
    "RobotClient",
    # Distribution
    "DistributionStrategy",
    "DistributionRule",
    "DistributionResult",
    "RobotSelector",
    "WorkflowDistributor",
    "JobRouter",
    # Result Collection
    "JobResult",
    "ExecutionStatistics",
    "ResultCollector",
    "ResultExporter",
    # Resilience
    "RecoveryStrategy",
    "RecoveryAction",
    "RetryPolicy",
    "ErrorRecoveryManager",
    "HealthStatus",
    "HealthMetrics",
    "HealthThresholds",
    "HealthMonitor",
    "TokenType",
    "AuthToken",
    "SecurityManager",
    # UI
    "OrchestratorMonitor",
    "run_orchestrator",
    "main",
]
