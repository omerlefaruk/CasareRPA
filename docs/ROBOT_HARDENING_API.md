# Phase 8B: Robot Hardening API Documentation

This document describes the APIs and usage patterns for the Robot Hardening features implemented in Phase 8B.

## Overview

Phase 8B adds enterprise-grade resilience and observability to the Robot Agent:

- **Connection Resilience**: Exponential backoff, circuit breaker, offline queue
- **Job Execution**: Locking, progress reporting, cancellation, concurrent limits
- **Observability**: Metrics, resource monitoring, audit logging

---

## Quick Start

```python
import asyncio
from casare_rpa.robot import RobotAgent, RobotConfig

async def main():
    # Create robot with custom config
    config = RobotConfig()
    config.job_execution.max_concurrent_jobs = 5
    config.observability.audit_enabled = True

    agent = RobotAgent(config)

    try:
        await agent.start()
    except KeyboardInterrupt:
        pass
    finally:
        await agent.stop()

asyncio.run(main())
```

---

## Configuration

### RobotConfig

The main configuration class with nested configs for each subsystem.

```python
from casare_rpa.robot import RobotConfig

config = RobotConfig()

# Connection settings
config.connection.url = "https://your-project.supabase.co"
config.connection.key = "your-api-key"
config.connection.initial_delay = 1.0        # Initial reconnect delay (seconds)
config.connection.max_delay = 300.0          # Max reconnect delay (5 minutes)
config.connection.backoff_multiplier = 2.0   # Exponential backoff factor
config.connection.connection_timeout = 30.0  # Connection timeout

# Circuit breaker settings
config.circuit_breaker.failure_threshold = 5  # Failures before opening
config.circuit_breaker.success_threshold = 2  # Successes to close
config.circuit_breaker.timeout = 60.0         # Time in open state

# Job execution settings
config.job_execution.max_concurrent_jobs = 3       # Max parallel jobs
config.job_execution.checkpoint_enabled = True     # Enable checkpointing
config.job_execution.progress_reporting_enabled = True
config.job_execution.cancellation_check_interval = 2.0

# Observability settings
config.observability.metrics_enabled = True
config.observability.resource_monitoring_enabled = True
config.observability.audit_enabled = True
```

### Environment Variables

Configuration can also be set via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `SUPABASE_URL` | Supabase project URL | - |
| `SUPABASE_KEY` | Supabase API key | - |
| `CASARE_ROBOT_NAME` | Robot display name | `Robot-{COMPUTERNAME}` |
| `CASARE_MAX_CONCURRENT_JOBS` | Max concurrent jobs | `3` |

---

## Connection Manager

Handles resilient connections to Supabase with automatic reconnection.

### Basic Usage

```python
from casare_rpa.robot import ConnectionManager, ConnectionConfig

config = ConnectionConfig(
    initial_delay=1.0,
    max_delay=300.0,
    backoff_multiplier=2.0,
)

manager = ConnectionManager(
    url="https://your-project.supabase.co",
    key="your-api-key",
    config=config,
    on_connected=lambda: print("Connected!"),
    on_disconnected=lambda: print("Disconnected!"),
)

# Connect
await manager.connect()

# Execute operations with automatic reconnection
result = await manager.execute(
    lambda client: client.table("jobs").select("*").execute()
)

# Check status
status = manager.get_status()
print(f"State: {status['state']}")
print(f"Connected: {status['is_connected']}")
```

### Connection States

| State | Description |
|-------|-------------|
| `DISCONNECTED` | Not connected |
| `CONNECTING` | Attempting to connect |
| `CONNECTED` | Successfully connected |
| `RECONNECTING` | Attempting to reconnect after failure |
| `FAILED` | Max reconnection attempts reached |

---

## Circuit Breaker

Prevents cascading failures by stopping requests when a service is unhealthy.

### Basic Usage

```python
from casare_rpa.robot import CircuitBreaker, CircuitBreakerConfig

config = CircuitBreakerConfig(
    failure_threshold=5,   # Open after 5 failures
    success_threshold=2,   # Close after 2 successes
    timeout=60.0,          # Stay open for 60 seconds
)

breaker = CircuitBreaker("supabase", config=config)

# Execute through circuit breaker
try:
    result = await breaker.call(some_async_function)
except CircuitBreakerOpenError as e:
    print(f"Circuit open, retry in {e.remaining_seconds}s")
```

### Circuit States

```
CLOSED → (failures >= threshold) → OPEN
OPEN → (timeout elapsed) → HALF_OPEN
HALF_OPEN → (success) → CLOSED
HALF_OPEN → (failure) → OPEN
```

### Manual Control

```python
# Force reset to closed
await breaker.reset()

# Force open
await breaker.force_open()

# Get status
status = breaker.get_status()
```

---

## Offline Queue

SQLite-based local queue for offline operation.

### Basic Usage

```python
from casare_rpa.robot import OfflineQueue
from pathlib import Path

queue = OfflineQueue(
    db_path=Path.home() / ".casare_rpa" / "offline.db",
    robot_id="robot-123"
)

# Cache a job
await queue.cache_job(
    job_id="job-456",
    workflow_json='{"nodes": [...]}',
    original_status="pending"
)

# Mark in progress
await queue.mark_in_progress("job-456")

# Save checkpoint
await queue.save_checkpoint(
    job_id="job-456",
    checkpoint_id="cp-1",
    node_id="node-3",
    state={"variables": {"x": 1}}
)

# Mark completed
await queue.mark_completed(
    "job-456",
    success=True,
    result={"status": "done"}
)

# Get jobs to sync when back online
jobs_to_sync = await queue.get_jobs_to_sync()

# Mark synced
await queue.mark_synced("job-456")
```

### Crash Recovery

```python
# Get jobs that were in progress when robot crashed
in_progress = await queue.get_in_progress_jobs()

for job in in_progress:
    # Get latest checkpoint
    checkpoint = await queue.get_latest_checkpoint(job["id"])
    if checkpoint:
        # Resume from checkpoint
        print(f"Resume from node {checkpoint['node_id']}")
```

---

## Checkpoint Manager

Manages per-node checkpointing for crash recovery.

### Basic Usage

```python
from casare_rpa.robot import CheckpointManager, OfflineQueue

queue = OfflineQueue(robot_id="robot-123")
checkpoint_mgr = CheckpointManager(queue, auto_save=True)

# Start tracking a job
checkpoint_mgr.start_job("job-456", "My Workflow")

# After each node completes
await checkpoint_mgr.save_checkpoint(
    node_id="node-1",
    context=execution_context  # Your ExecutionContext
)

# Check if node was already executed (for resume)
if checkpoint_mgr.is_node_executed("node-1"):
    print("Skip node-1, already executed")

# End job
checkpoint_mgr.end_job()
```

### Resume from Checkpoint

```python
# Get checkpoint for crashed job
checkpoint = await checkpoint_mgr.get_checkpoint("job-456")

if checkpoint:
    # Restore state
    await checkpoint_mgr.restore_from_checkpoint(
        checkpoint,
        execution_context
    )

    # Get nodes to skip
    executed = checkpoint_mgr.get_executed_nodes()
```

---

## Metrics Collector

Collects execution metrics and resource usage.

### Basic Usage

```python
from casare_rpa.robot import MetricsCollector, get_metrics_collector

# Get global collector
metrics = get_metrics_collector()

# Start tracking a job
metrics.start_job("job-456", "My Workflow", total_nodes=10)

# Record node execution
metrics.record_node(
    node_id="node-1",
    node_type="ClickNode",
    duration_ms=150.0,
    success=True,
    retry_count=0
)

# End job
metrics.end_job(success=True)

# Get summary
summary = metrics.get_summary()
print(f"Total jobs: {summary['total_jobs']}")
print(f"Success rate: {summary['success_rate_percent']}%")

# Get node statistics
node_stats = metrics.get_node_stats()
for node_type, stats in node_stats.items():
    print(f"{node_type}: {stats['total_executions']} executions")

# Get full report
report = metrics.get_full_report()
```

### Resource Monitoring

```python
# Start resource monitoring (requires psutil)
await metrics.start_resource_monitoring()

# Get current resources
resources = metrics.get_current_resources()
print(f"CPU: {resources['cpu_percent']}%")
print(f"Memory: {resources['memory_mb']} MB")

# Get historical data
history = metrics.get_resource_history(minutes=10)

# Stop monitoring
await metrics.stop_resource_monitoring()
```

---

## Audit Logger

Structured audit logging for compliance and debugging.

### Basic Usage

```python
from casare_rpa.robot import AuditLogger, AuditEventType, AuditSeverity

logger = AuditLogger(
    robot_id="robot-123",
    log_dir=Path.home() / ".casare_rpa" / "audit"
)

# Log events
logger.robot_started()
logger.connection_established()
logger.job_received("job-456", "My Workflow")
logger.job_started("job-456", total_nodes=10)
logger.node_completed("node-1", "ClickNode", duration_ms=150.0)
logger.job_completed("job-456", duration_ms=5000.0)

# Log custom events
logger.log(
    AuditEventType.ERROR_TRANSIENT,
    "Connection timeout",
    severity=AuditSeverity.WARNING,
    job_id="job-456",
    details={"retry_count": 2}
)
```

### Context Managers

```python
# Automatic job_id in all logs
with logger.job_context("job-456"):
    logger.log(AuditEventType.NODE_STARTED, "Starting node")
    # job_id automatically set to "job-456"
```

### Query Logs

```python
# Get recent entries
recent = logger.get_recent(limit=100)

# Query with filters
errors = logger.query(
    event_types=[AuditEventType.ERROR_TRANSIENT, AuditEventType.ERROR_PERMANENT],
    severity=AuditSeverity.ERROR,
    job_id="job-456",
    limit=50
)
```

---

## Job Executor

Manages concurrent job execution.

### Basic Usage

```python
from casare_rpa.robot import JobExecutor

executor = JobExecutor(
    max_concurrent_jobs=3,
    checkpoint_manager=checkpoint_mgr,
    metrics_collector=metrics,
    audit_logger=audit,
    on_job_complete=handle_job_complete
)

# Start executor
await executor.start()

# Submit jobs
await executor.submit_job("job-1", workflow_json_1)
await executor.submit_job("job-2", workflow_json_2)

# Check status
status = executor.get_status()
print(f"Running: {status['running_count']}")
print(f"At capacity: {status['is_at_capacity']}")

# Cancel a job
await executor.cancel_job("job-1", reason="User requested")

# Update concurrency limit
executor.set_max_concurrent(5)

# Stop executor
await executor.stop()
```

---

## Progress Reporter

Reports job progress to Orchestrator via Supabase.

### Basic Usage

```python
from casare_rpa.robot import ProgressReporter, ConnectionManager

reporter = ProgressReporter(
    connection=connection_manager,
    robot_id="robot-123",
    update_interval=1.0  # Batch updates every 1 second
)

# Start job
await reporter.start_job("job-456", "My Workflow", total_nodes=10)

# Report node progress
await reporter.report_node_start("node-1", "ClickNode")
await reporter.report_node_complete("node-1", success=True, duration_ms=150.0)

# End job
await reporter.end_job(success=True)
```

### Cancellation Checker

```python
from casare_rpa.robot import CancellationChecker

checker = CancellationChecker(connection_manager, check_interval=2.0)

# Start checking
checker.start("job-456")

# In execution loop
while executing:
    if checker.is_cancelled:
        print("Job was cancelled!")
        break
    # ... execute node

# Stop checking
checker.stop()
```

### Job Locker

```python
from casare_rpa.robot import JobLocker

locker = JobLocker(
    connection=connection_manager,
    robot_id="robot-123",
    lock_timeout=300.0
)

# Try to claim job
if await locker.try_claim("job-456"):
    try:
        # Execute job
        pass
    finally:
        # Release on completion
        await locker.release("job-456", status="completed")
else:
    print("Job already claimed by another robot")

# Send heartbeat to prevent lock expiry
await locker.heartbeat("job-456")
```

---

## Database Schema

Run the migration to add required columns:

```sql
-- See migrations/001_robot_hardening.sql

-- Key new columns on jobs table:
ALTER TABLE jobs ADD COLUMN claimed_by UUID;
ALTER TABLE jobs ADD COLUMN claimed_at TIMESTAMPTZ;
ALTER TABLE jobs ADD COLUMN cancel_requested BOOLEAN DEFAULT FALSE;
ALTER TABLE jobs ADD COLUMN progress JSONB DEFAULT '{}';

-- Atomic job claiming function
SELECT claim_job('job-uuid', 'robot-uuid');
```

---

## Error Handling

### Transient vs Permanent Errors

```python
from casare_rpa.utils.retry import classify_error, ErrorCategory

try:
    await some_operation()
except Exception as e:
    category = classify_error(e)

    if category == ErrorCategory.TRANSIENT:
        # Retry with backoff
        pass
    elif category == ErrorCategory.PERMANENT:
        # Fail immediately
        pass
```

### Retry Configuration

```python
from casare_rpa.utils.retry import RetryConfig, retry_async

config = RetryConfig(
    max_attempts=3,
    initial_delay=1.0,
    max_delay=30.0,
    backoff_multiplier=2.0,
    jitter=True
)

result = await retry_async(
    some_async_function,
    arg1, arg2,
    config=config
)
```

---

## Best Practices

### 1. Always Use Checkpointing for Long Workflows

```python
config.job_execution.checkpoint_enabled = True
config.job_execution.checkpoint_on_every_node = True
```

### 2. Set Appropriate Timeouts

```python
config.connection.connection_timeout = 30.0
config.job_execution.node_timeout = 120.0
```

### 3. Monitor Resource Usage

```python
if config.observability.resource_monitoring_enabled:
    await metrics.start_resource_monitoring()
```

### 4. Handle Offline Gracefully

```python
if not connection.is_connected:
    # Queue jobs locally
    await offline_queue.cache_job(job_id, workflow_json)
```

### 5. Use Audit Logging for Compliance

```python
with audit.job_context(job_id):
    audit.job_started(job_id, total_nodes)
    # All subsequent logs include job_id
```

---

## Troubleshooting

### Connection Issues

```python
# Check connection status
status = connection.get_status()
print(f"State: {status['state']}")
print(f"Failures: {status['consecutive_failures']}")

# Check circuit breaker
cb_status = circuit_breaker.get_status()
print(f"Circuit: {cb_status['state']}")
```

### Job Stuck

```python
# Check if job has checkpoint
checkpoint = await offline_queue.get_latest_checkpoint(job_id)
if checkpoint:
    print(f"Last checkpoint at node: {checkpoint['node_id']}")
```

### High Memory Usage

```python
# Check current resources
resources = metrics.get_current_resources()
if resources['memory_percent'] > 80:
    print("Warning: High memory usage")
```

---

## API Reference

See the source code docstrings for detailed API documentation:

- `casare_rpa/robot/connection.py` - ConnectionManager
- `casare_rpa/robot/circuit_breaker.py` - CircuitBreaker
- `casare_rpa/robot/offline_queue.py` - OfflineQueue
- `casare_rpa/robot/checkpoint.py` - CheckpointManager
- `casare_rpa/robot/metrics.py` - MetricsCollector
- `casare_rpa/robot/audit.py` - AuditLogger
- `casare_rpa/robot/job_executor.py` - JobExecutor
- `casare_rpa/robot/progress_reporter.py` - ProgressReporter
- `casare_rpa/robot/config.py` - RobotConfig
