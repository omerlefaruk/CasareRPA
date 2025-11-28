"""
PgQueuer-based Job Queue Infrastructure.

Provides durable, distributed job queuing using PostgreSQL via PgQueuer.
Replaces the in-memory JobQueue with a persistent, scalable solution.

Key Components:
- PgQueuerProducer: Enqueue jobs from Orchestrator
- PgQueuerConsumer: Dequeue jobs in Robot agents
- QueueConfig: Configuration management
- JobModel: Job data model with priority, status tracking

Features:
- 18k+ jobs/sec throughput
- Sub-100ms LISTEN/NOTIFY latency
- Priority queue support
- Visibility timeout pattern
- Dead Letter Queue for failures
- Multi-robot coordination

References:
- https://github.com/janbjorge/pgqueuer
- Plan: C:\\Users\\Rau\\.claude\\plans\\tender-puzzling-ullman.md
"""

from .config import QueueConfig
from .models import JobModel, JobStatus, JobPriority
from .producer import PgQueuerProducer
from .consumer import PgQueuerConsumer

__all__ = [
    "QueueConfig",
    "JobModel",
    "JobStatus",
    "JobPriority",
    "PgQueuerProducer",
    "PgQueuerConsumer",
]
