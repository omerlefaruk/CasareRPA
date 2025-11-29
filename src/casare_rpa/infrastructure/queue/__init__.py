"""
CasareRPA Infrastructure Layer - Queue Adapters

Provides PostgreSQL-based distributed queue implementations using the pgqueuer pattern
for high-throughput job processing with guaranteed delivery.

Components:
- PgQueuerConsumer: Robot-side job claiming with SKIP LOCKED
- PgQueuerProducer: Orchestrator-side job enqueuing (TODO)
- DLQManager: Dead Letter Queue with exponential backoff retry
"""

from .pgqueuer_consumer import (
    PgQueuerConsumer,
    ClaimedJob,
    ConsumerConfig,
    ConnectionState,
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

__all__ = [
    # Consumer
    "PgQueuerConsumer",
    "ClaimedJob",
    "ConsumerConfig",
    "ConnectionState",
    # DLQ Manager
    "DLQManager",
    "DLQManagerConfig",
    "DLQEntry",
    "FailedJob",
    "RetryAction",
    "RetryResult",
    "RETRY_SCHEDULE",
    "JITTER_FACTOR",
]
