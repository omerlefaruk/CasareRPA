"""
CasareRPA Infrastructure Layer - Queue Adapters

Provides distributed queue implementations for job processing:
- PgQueuer: PostgreSQL-based queue for production (high-throughput, persistence)
- MemoryQueue: In-memory fallback for development/testing (no persistence)

Components:
- PgQueuerConsumer: Robot-side job claiming with SKIP LOCKED
- PgQueuerProducer: Orchestrator-side job enqueuing
- DLQManager: Dead Letter Queue with exponential backoff retry
- MemoryQueue: In-memory queue fallback for local development

Type Definitions:
- TypedDicts for job payloads, queue messages, results, and statistics
- Protocols for state callbacks and event handlers
- Type aliases for common patterns (JobId, WorkflowId, etc.)
"""

from casare_rpa.infrastructure.queue.dlq_manager import (
    JITTER_FACTOR,
    RETRY_SCHEDULE,
    DLQEntry,
    DLQManager,
    DLQManagerConfig,
    FailedJob,
    RetryAction,
    RetryResult,
)
from casare_rpa.infrastructure.queue.memory_queue import (
    JobStatus,
    MemoryJob,
    MemoryQueue,
    get_memory_queue,
    initialize_memory_queue,
    shutdown_memory_queue,
)
from casare_rpa.infrastructure.queue.pgqueuer_consumer import (
    ClaimedJob,
    ConnectionState,
    ConsumerConfig,
    PgQueuerConsumer,
)
from casare_rpa.infrastructure.queue.pgqueuer_producer import (
    EnqueuedJob,
    JobSubmission,
    PgQueuerProducer,
    ProducerConfig,
    ProducerConnectionState,
)
from casare_rpa.infrastructure.queue.types import (
    # Job Payload Types
    ClaimedJobPayload,
    # Consumer/Producer Statistics Types
    ConsumerConfigStats,
    ConsumerStats,
    # Type Aliases
    DatabaseRecord,
    DatabaseRecordList,
    # Queue Message Types
    EnqueueRequest,
    EnqueueResponse,
    Environment,
    # Callback Protocols
    HeartbeatCallback,
    JobClaimedCallback,
    JobCompletedCallback,
    # Job Status Types
    JobDetailedStatus,
    JobFailedCallback,
    # Job Result Types
    JobFailureResult,
    JobId,
    JobPayload,
    JobResult,
    JobResultData,
    JobStatusInfo,
    JobVariables,
    Priority,
    ProducerConfigStats,
    ProducerStats,
    # Error Types
    QueueError,
    QueueMessage,
    # Queue Statistics Types
    QueueStats,
    RobotId,
    StateChangeCallback,
    WorkflowId,
)

__all__ = [
    # Consumer (Robot-side)
    "PgQueuerConsumer",
    "ClaimedJob",
    "ConsumerConfig",
    "ConnectionState",
    # Producer (Orchestrator-side)
    "PgQueuerProducer",
    "EnqueuedJob",
    "JobSubmission",
    "ProducerConfig",
    "ProducerConnectionState",
    # DLQ Manager
    "DLQManager",
    "DLQManagerConfig",
    "DLQEntry",
    "FailedJob",
    "RetryAction",
    "RetryResult",
    "RETRY_SCHEDULE",
    "JITTER_FACTOR",
    # Memory Queue (fallback)
    "MemoryQueue",
    "MemoryJob",
    "JobStatus",
    "get_memory_queue",
    "initialize_memory_queue",
    "shutdown_memory_queue",
    # Type Definitions - Job Payloads
    "JobPayload",
    "ClaimedJobPayload",
    "JobVariables",
    # Type Definitions - Queue Messages
    "QueueMessage",
    "EnqueueRequest",
    "EnqueueResponse",
    # Type Definitions - Job Results
    "JobResult",
    "JobResultData",
    "JobFailureResult",
    # Type Definitions - Job Status
    "JobStatusInfo",
    "JobDetailedStatus",
    # Type Definitions - Statistics
    "QueueStats",
    "ConsumerStats",
    "ConsumerConfigStats",
    "ProducerStats",
    "ProducerConfigStats",
    # Type Definitions - Protocols
    "StateChangeCallback",
    "JobClaimedCallback",
    "JobCompletedCallback",
    "JobFailedCallback",
    "HeartbeatCallback",
    # Type Definitions - Errors
    "QueueError",
    # Type Aliases
    "JobId",
    "WorkflowId",
    "RobotId",
    "Environment",
    "Priority",
    "DatabaseRecord",
    "DatabaseRecordList",
]
