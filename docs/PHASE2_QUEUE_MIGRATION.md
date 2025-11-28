# Project Aether - Phase 2: Queue Migration

**Status**: 🟡 IN PROGRESS
**Date**: 2025-11-28
**Phase**: Queue Migration (Week 3-4)

## Overview

Phase 2 replaces the in-memory `JobQueue` with PgQueuer - a high-performance PostgreSQL-based queue system that provides durable, distributed job queuing with 18k+ jobs/sec throughput.

## Completed Tasks ✅

### 1. Infrastructure Package Created

Created `src/casare_rpa/infrastructure/queue/` package with complete PgQueuer implementation:

**Files Created**:
- [`__init__.py`](src/casare_rpa/infrastructure/queue/__init__.py) - Package exports
- [`models.py`](src/casare_rpa/infrastructure/queue/models.py) - Job data models
- [`config.py`](src/casare_rpa/infrastructure/queue/config.py) - Configuration management
- [`producer.py`](src/casare_rpa/infrastructure/queue/producer.py) - Job queue producer
- [`consumer.py`](src/casare_rpa/infrastructure/queue/consumer.py) - Job queue consumer

### 2. Job Data Models

**JobModel** - Complete job lifecycle management:
- Status tracking (pending → claimed → running → completed/failed)
- Priority levels (0-20, higher = more urgent)
- Retry logic with configurable max attempts
- Visibility timeout pattern
- Multi-tenancy support (tenant_id)
- Metadata & tags for filtering

**JobStatus Enum**:
- `PENDING` - Waiting in queue
- `CLAIMED` - Claimed by robot (visibility timeout active)
- `RUNNING` - Currently executing
- `COMPLETED` - Successfully completed
- `FAILED` - Failed (moved to DLQ after max retries)
- `CANCELLED` - Cancelled by user/system

**JobPriority Enum**: LOW (0), NORMAL (5), HIGH (10), URGENT (15), CRITICAL (20)

### 3. Queue Configuration

**QueueConfig** class with support for:
- Environment variable loading
- Supabase connection configuration
- Local PostgreSQL development
- Configurable concurrency, timeouts, retries
- Connection pooling settings

**Configuration Options**:
```python
- database_url: PostgreSQL connection string
- queue_name: Queue identifier (allows multiple queues)
- max_concurrent_jobs: Concurrent jobs per robot (default: 3)
- visibility_timeout: Claim timeout in seconds (default: 30)
- poll_interval: Polling frequency (default: 1.0s)
- max_retries: Max attempts before DLQ (default: 3)
- enable_dlq: Dead Letter Queue enabled (default: true)
- batch_size: Jobs per poll (default: 10)
- connection_pool_size: DB pool size (default: 10)
```

### 4. PgQueuerProducer (Orchestrator)

**Features**:
- ✅ Priority-based job enqueueing
- ✅ Async job submission
- ✅ Connection pooling
- ✅ Batch job submission
- ✅ Queue depth monitoring
- ✅ Job status tracking
- ✅ Job cancellation
- ✅ Health checks
- ✅ Queue purging (admin)

**Key Methods**:
- `enqueue_job()` - Enqueue single job with priority
- `enqueue_batch()` - Batch job submission
- `get_queue_depth()` - Get pending job count
- `get_job_status()` - Check job status
- `cancel_job()` - Cancel pending/claimed job
- `health_check()` - Database connectivity check

### 5. PgQueuerConsumer (Robot)

**Features**:
- ✅ Priority-based job claiming
- ✅ Visibility timeout pattern (prevents duplicate processing)
- ✅ Heartbeat mechanism (extends timeout for long-running jobs)
- ✅ Dead Letter Queue integration
- ✅ Concurrent job execution
- ✅ Automatic retry logic
- ✅ Graceful shutdown with job release

**Key Methods**:
- `claim_job()` - Claim next job from queue (SKIP LOCKED)
- `complete_job()` - Mark job as completed
- `fail_job()` - Mark job as failed (retry or DLQ)
- `release_job()` - Release claimed job back to queue
- Heartbeat loop - Extends visibility timeout for active jobs

### 6. Integration Tests

Created [`tests/infrastructure/test_pgqueuer_integration.py`](tests/infrastructure/test_pgqueuer_integration.py):

**Test Coverage**:
- ✅ Configuration loading (env, Supabase, local)
- ✅ Job model lifecycle
- ✅ Job retry logic
- ✅ Producer lifecycle
- ✅ Consumer lifecycle
- ⏸️ Full producer-consumer flow (requires Postgres)

## Architecture

### Queue Flow

```
┌──────────────────┐
│   Orchestrator   │
│                  │
│  Producer.       │
│  enqueue_job()   │
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────────┐
│      PostgreSQL + PgQueuer      │
│                                 │
│  Queue: casare_rpa_jobs         │
│  - Priority ordering            │
│  - LISTEN/NOTIFY                │
│  - Visibility timeout           │
│  - Dead Letter Queue            │
└────────┬────────────────────────┘
         │
         ▼
┌──────────────────┐
│   Robot Agent    │
│                  │
│  Consumer.       │
│  claim_job()     │
│  → execute       │
│  → complete/fail │
└──────────────────┘
```

### Visibility Timeout Pattern

```
Job State Timeline:

PENDING → CLAIMED (30s timeout) → RUNNING → COMPLETED
    ↓                                ↓
    └──(timeout expires)──←──────────┘
         back to PENDING

Heartbeat extends timeout every 15s
```

### Dead Letter Queue

```
Job Retry Flow:

PENDING → CLAIMED → FAILED (retry 1/3)
     ↓         ↓
     └─(retry)─┘

PENDING → CLAIMED → FAILED (retry 2/3)
     ↓         ↓
     └─(retry)─┘

PENDING → CLAIMED → FAILED (retry 3/3)
                      ↓
                    DLQ (manual intervention)
```

## Pending Tasks 🔄

### 1. Migrate Orchestrator (Next)

**Files to Modify**:
- [src/casare_rpa/orchestrator/engine.py](src/casare_rpa/orchestrator/engine.py)
  - Replace `JobQueue` with `PgQueuerProducer`
  - Update dispatcher to use `enqueue_job()`
  - Add queue depth monitoring

- [src/casare_rpa/orchestrator/job_queue.py](src/casare_rpa/orchestrator/job_queue.py)
  - DELETE (in-memory queue no longer needed)

### 2. Migrate Robot Agent (Next)

**Files to Modify**:
- [src/casare_rpa/robot/agent.py](src/casare_rpa/robot/agent.py)
  - Replace polling logic with `PgQueuerConsumer`
  - Integrate `claim_job()` / `complete_job()` / `fail_job()`
  - Add heartbeat integration

- [src/casare_rpa/robot/job_executor.py](src/casare_rpa/robot/job_executor.py)
  - Track claimed jobs
  - Integrate with queue consumer lifecycle

### 3. Database Setup

**PostgreSQL Schema**:
```sql
-- Install PgQueuer extension
CREATE EXTENSION IF NOT EXISTS pgqueuer;

-- PgQueuer automatically creates these tables:
-- - pgqueuer.jobs (main queue)
-- - pgqueuer.dead_letter_queue
-- - pgqueuer.job_history

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_jobs_status_priority
ON pgqueuer.jobs(status, priority DESC, created_at);

CREATE INDEX IF NOT EXISTS idx_jobs_tenant
ON pgqueuer.jobs((payload->>'tenant_id'));
```

### 4. Configuration

**Environment Variables** (.env):
```bash
# Queue Configuration
PGQUEUER_DATABASE_URL=postgresql://postgres:password@localhost:5432/casare_rpa
PGQUEUER_QUEUE_NAME=casare_rpa_jobs
PGQUEUER_MAX_CONCURRENT=3
PGQUEUER_VISIBILITY_TIMEOUT=30
PGQUEUER_MAX_RETRIES=3
```

## Migration Strategy

### Backward Compatibility

- Keep old `JobQueue` available during transition
- Feature flag: `USE_PGQUEUER` (default: false initially)
- Gradual rollout per environment

### Data Migration

- No migration needed (in-memory queue has no persistent data)
- New jobs automatically use PgQueuer
- Existing in-flight jobs complete normally

### Testing Plan

1. Unit tests for producer/consumer (✅ Complete)
2. Integration tests with local Postgres (⏸️ Pending CI)
3. Load testing (10k jobs/sec)
4. Failure scenario testing (crashes, network issues)
5. Multi-robot coordination testing

## Performance Targets

- **Throughput**: 10k+ jobs/day per Postgres instance
- **Latency**: Job submission → claim < 100ms (p95)
- **Concurrency**: 100+ robots, 300+ concurrent jobs
- **Reliability**: Zero lost jobs, automatic retry
- **Visibility Timeout**: 30s default, extended via heartbeat

## Success Metrics

- ✅ PgQueuer infrastructure package created
- ✅ Producer implementation complete
- ✅ Consumer implementation complete
- ✅ Configuration system complete
- ✅ Unit tests passing
- ⏸️ Integration tests (requires Postgres setup)
- ⏸️ Orchestrator migration
- ⏸️ Robot migration
- ⏸️ Load testing

## Next Steps

1. **Commit Phase 2 infrastructure** ✅
2. **Setup test PostgreSQL** (Docker Compose)
3. **Migrate orchestrator/engine.py** to use PgQueuerProducer
4. **Migrate robot/agent.py** to use PgQueuerConsumer
5. **Integration testing** with producer + consumer
6. **Performance benchmarking**

## Resources

- **Plan**: [C:\Users\Rau\.claude\plans\tender-puzzling-ullman.md](file:///C:/Users/Rau/.claude/plans/tender-puzzling-ullman.md)
- **PgQueuer Docs**: https://github.com/janbjorge/pgqueuer
- **Postgres LISTEN/NOTIFY**: https://www.postgresql.org/docs/current/sql-notify.html
- **Previous Phase**: [PHASE1_FOUNDATION.md](PHASE1_FOUNDATION.md)

---

**Status**: Infrastructure complete, orchestrator migration next
**Blockers**: None
**ETA**: Phase 2 complete by end of Week 4
