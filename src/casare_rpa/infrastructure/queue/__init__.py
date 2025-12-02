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
"""

from .pgqueuer_consumer import (
    PgQueuerConsumer,
    ClaimedJob,
    ConsumerConfig,
    ConnectionState,
)

from .pgqueuer_producer import (
    PgQueuerProducer,
    EnqueuedJob,
    JobSubmission,
    ProducerConfig,
    ProducerConnectionState,
)

from .dlq_manager import (
    DLQManager,
    DLQManagerConfig,
    DLQEntry,
    FailedJob,
    RetryAction,
    RetryResult,
    RETRY_SCHEDULE,
    JITTER_FACTOR,
)

from .memory_queue import (
    MemoryQueue,
    MemoryJob,
    JobStatus,
    get_memory_queue,
    initialize_memory_queue,
    shutdown_memory_queue,
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
]
