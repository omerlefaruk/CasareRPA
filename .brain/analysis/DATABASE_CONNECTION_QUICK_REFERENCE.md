# Database Connection Quick Reference Guide

## Environment Variables

```bash
# Primary: PostgreSQL connection URL
export POSTGRES_URL="postgresql://user:pass@host:5432/database"

# Fallback 1: Generic DATABASE_URL
export DATABASE_URL="postgresql://user:pass@host:5432/database"

# Fallback 2: For frozen apps - builds URL from this
export DB_PASSWORD="your_supabase_password"

# Result for frozen app (auto-constructed):
# postgresql://postgres.{project_ref}:{DB_PASSWORD}@aws-1-eu-central-1.pooler.supabase.com:6543/postgres
```

---

## Connection Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Robot Agent Start                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │  Load Configuration from Env       │
        │  • POSTGRES_URL                    │
        │  • DATABASE_URL                    │
        │  • DB_PASSWORD (frozen apps)       │
        └────────────┬───────────────────────┘
                     │
                     ▼
        ┌────────────────────────────────────┐
        │  Component Initialization          │
        │  ├─ PgQueuerConsumer               │
        │  │  └─ asyncpg pool (2-10 conn)   │
        │  ├─ DBOSExecutor                   │
        │  │  └─ asyncpg pool (1-3 conn)    │
        │  └─ ResourceManager                │
        │     └─ UnifiedHttpClient           │
        └────────────┬───────────────────────┘
                     │
      ┌──────────────┴──────────────┐
      ▼                             ▼
  ✓ Connected              ✗ Failed (Graceful)
  Start Job Loop           Continue without DB
  (Can claim/execute       (Checkpointing disabled,
   jobs from queue)        jobs not persisted)
```

---

## Connection Pool Summary

### Pool 1: PgQueuerConsumer
```
Location: infrastructure/queue/pgqueuer_consumer.py
Purpose:  Job claiming and heartbeat management
Min Size: 2 connections
Max Size: 10 connections
Timeout:  30 seconds
Retry:    3 attempts with exponential backoff
State:    DISCONNECTED → CONNECTING → CONNECTED → RECONNECTING → FAILED
```

### Pool 2: DBOSExecutor
```
Location: infrastructure/execution/dbos_executor.py
Purpose:  Workflow checkpoint persistence
Min Size: 1 connection
Max Size: 3 connections
Timeout:  60 seconds
Fallback: Continues without checkpointing if connection fails
```

### Pool 3: MonitoringAPI
```
Location: infrastructure/orchestrator/api/database.py
Purpose:  Fleet monitoring and analytics queries
Min Size: 2 connections
Max Size: 10 connections
Timeout:  60 seconds
```

---

## Error Handling Decision Tree

```
Database Operation Attempt
        │
        ▼
    Connected?
    /        \
   Y          N → Retry Pool.acquire() (up to 3×)
   │              with exponential backoff
   │              │
   │              ├─ Max retries exceeded?
   │              │  └─ Y → Raise ConnectionError
   │              │
   │              └─ N → Wait & retry
   │
   ▼
Execute Query
   │
   ├─ ConnectionDoesNotExistError?
   │  └─ Trigger reconnect (exponential backoff)
   │     └─ Retry query (up to 3× total)
   │
   ├─ InterfaceError?
   │  └─ Trigger reconnect (exponential backoff)
   │     └─ Retry query (up to 3× total)
   │
   ├─ PostgresError (other)?
   │  └─ Raise immediately (no retry)
   │
   └─ ✓ Success
      └─ Return result
```

---

## Reconnection Backoff Algorithm

```
Attempt 1: delay = 1 * (2^0) = 1s      + jitter = ~1.1s
Attempt 2: delay = 1 * (2^1) = 2s      + jitter = ~2.2s
Attempt 3: delay = 1 * (2^2) = 4s      + jitter = ~4.4s
Attempt 4: delay = 1 * (2^3) = 8s      + jitter = ~8.8s
Attempt 5: delay = 1 * (2^4) = 16s     + jitter = ~17.6s
Attempt 6: delay = 1 * (2^5) = 32s     + jitter = ~35.2s
Attempt 7-10: delay = 60s (capped)     + jitter = ~60-78s

Total time after 10 failed attempts: ~195 seconds (3.25 minutes)
Final state: FAILED (operator intervention required)
```

---

## Job Lifecycle with Visibility Timeout

```
Step 1: Job Created
        job_queue.status = 'pending'
        visible_after = NOW()

Step 2: Robot Claims Job (SKIP LOCKED)
        job_queue.status = 'running'
        job_queue.robot_id = 'robot-001'
        visible_after = NOW() + 30s (visibility_timeout_seconds)

Step 3: Heartbeat Extension (Every 10s)
        visible_after = NOW() + 30s (heartbeat_interval_seconds)

Step 4a: Job Completes
         job_queue.status = 'completed'
         completed_at = NOW()

Step 4b: Job Fails (< max_retries)
         job_queue.status = 'pending'
         retry_count += 1
         visible_after = NOW() + (retry_count * 5)s

Step 4c: Visibility Timeout Exceeded
         (no heartbeat, robot crashed)
         job_queue.status = 'pending' (if retries left)
         retry_count += 1
         visible_after = NOW() + (retry_count * 5)s

Step 5: Job Retried
        Robot claims again from queue
        visible_after = NOW() + 30s
```

---

## Configuration Defaults

```python
# PgQueuerConsumer Configuration
ConsumerConfig(
    postgres_url="postgresql://...",
    robot_id="robot-001",
    environment="default",
    batch_size=1,
    visibility_timeout_seconds=30,      # Lease duration
    heartbeat_interval_seconds=10,      # Heartbeat interval
    max_reconnect_attempts=10,          # Total retry attempts
    reconnect_base_delay_seconds=1.0,   # Initial backoff
    reconnect_max_delay_seconds=60.0,   # Maximum backoff
    pool_min_size=2,
    pool_max_size=10,
    claim_poll_interval_seconds=1.0,
)

# DBOSExecutorConfig
DBOSExecutorConfig(
    postgres_url="postgresql://...",
    checkpoint_table="workflow_checkpoints",
    enable_checkpointing=True,
    checkpoint_interval=0,              # 0 = checkpoint every node
    execution_timeout_seconds=3600,     # 1 hour
    node_timeout_seconds=120.0,         # 2 minutes per node
    continue_on_error=False,
)

# RobotConfig
RobotConfig(
    postgres_url="postgresql://...",
    db_pool_size=10,                    # Resource manager pool
    poll_interval_seconds=1.0,          # Job claiming poll
    heartbeat_interval_seconds=10.0,    # Lease extension
    visibility_timeout_seconds=30,      # Job visibility timeout
    max_concurrent_jobs=1,
    graceful_shutdown_seconds=60,
    enable_checkpointing=True,
)
```

---

## SQL Queries at a Glance

### Job Claiming (Non-blocking)
```sql
UPDATE job_queue
SET status = 'running', robot_id = $3, visible_after = NOW() + interval '30s'
WHERE id IN (
    SELECT id FROM job_queue
    WHERE status = 'pending' AND visible_after <= NOW()
    ORDER BY priority DESC, created_at ASC
    LIMIT 1
    FOR UPDATE SKIP LOCKED
)
RETURNING ...;
```

### Lease Extension (Heartbeat)
```sql
UPDATE job_queue
SET visible_after = NOW() + interval '30s'
WHERE id = $1 AND status = 'running' AND robot_id = $2
RETURNING id;
```

### Job Completion
```sql
UPDATE job_queue
SET status = 'completed', completed_at = NOW(), result = $2
WHERE id = $1 AND status = 'running' AND robot_id = $2
RETURNING id;
```

### Job Failure with Retry
```sql
UPDATE job_queue
SET status = CASE WHEN retry_count < max_retries THEN 'pending' ELSE 'failed' END,
    error_message = $2,
    retry_count = retry_count + 1,
    robot_id = CASE WHEN retry_count < max_retries THEN NULL ELSE robot_id END,
    visible_after = CASE WHEN retry_count < max_retries THEN NOW() + interval '5s' * (retry_count + 1) ELSE visible_after END
WHERE id = $1 AND status = 'running' AND robot_id = $2
RETURNING id, status, retry_count;
```

---

## Debugging Checklist

### Connection Issues

- [ ] Environment variables set?
  ```bash
  echo $POSTGRES_URL
  echo $DATABASE_URL
  echo $DB_PASSWORD
  ```

- [ ] Database reachable?
  ```bash
  psql "postgresql://..." -c "SELECT 1"
  ```

- [ ] Pool size sufficient?
  - Check `pool.get_stats()` for `in_use` near `max_size`
  - Increase `pool_max_size` if saturation detected

- [ ] Connection timeout?
  - Default 30s query timeout for PgQueuer
  - Default 60s query timeout for DBOS/Monitoring
  - Check slow query logs

- [ ] Pgbouncer compatibility?
  - All pools use `statement_cache_size=0`
  - Check pgbouncer `max_client_conn` setting

### Job Claiming Issues

- [ ] No jobs claimed?
  - Check `job_queue.status = 'pending' AND visible_after <= NOW()`
  - Verify robot `environment` matches job `environment`
  - Check circuit breaker status

- [ ] Jobs timing out?
  - Heartbeat interval too long? (should be < visibility_timeout)
  - Job execution exceeding timeout?
  - Check `visible_after` timestamps in job_queue

- [ ] Duplicate job execution?
  - SKIP LOCKED prevents this (use atomic UPDATE)
  - Verify `robot_id` in `WHERE` clause of completion queries

### Performance Issues

- [ ] Connection pool exhaustion?
  - Monitor `available_count` and `in_use_count`
  - Increase `pool_max_size` if needed
  - Check for connection leaks

- [ ] Slow heartbeats?
  - Monitor heartbeat loop latency
  - Check `extend_lease` query performance
  - Verify index on `(id, status, robot_id)`

---

## Log Patterns

### Normal Operation
```
INFO - Database connection established
INFO - PgQueuerConsumer started for robot 'robot-001'
INFO - Claimed job xyz... workflow='MyWorkflow' priority=1 retry=0
INFO - Extended lease for job xyz... by 30s
INFO - Completed job xyz...
```

### Connection Failure & Recovery
```
ERROR - Failed to connect to database: Connection refused
INFO - Reconnect attempt 1/10 in 1.1s
INFO - Connection lost, attempting reconnect (attempt 1)
INFO - Database connection established
INFO - Job loop resumed
```

### Timeout & Retry
```
WARNING - Failed to extend lease for job xyz... (job not found or not owned)
INFO - Job xyz... failed, re-queued for retry (1 retries): Connection timeout
INFO - Requeued 1 timed-out jobs
```

### Graceful Shutdown
```
INFO - Stopping PgQueuerConsumer...
INFO - Released job xyz... back to queue
INFO - PgQueuerConsumer stopped
INFO - Robot Agent stopped. Completed: 10, Failed: 1
```

---

## File Structure Reference

```
src/casare_rpa/
├── robot/
│   └── agent.py                              # Main agent, env var reading
├── infrastructure/
│   ├── queue/
│   │   └── pgqueuer_consumer.py              # Job queue consumer + pool
│   ├── execution/
│   │   └── dbos_executor.py                  # Checkpoint pool + persistence
│   ├── orchestrator/api/
│   │   └── database.py                       # Monitoring pool
│   └── resources/
│       └── unified_resource_manager.py       # Resource pooling coordinator
└── utils/pooling/
    ├── database_pool.py                      # Generic pool manager
    ├── browser_pool.py                       # Browser session pooling
    └── http_session_pool.py                  # HTTP connection pooling
```

---

## Performance Tuning Guidelines

### For Low Concurrency (1-2 jobs)
```python
pool_min_size = 1
pool_max_size = 3
heartbeat_interval_seconds = 10
visibility_timeout_seconds = 30
```

### For Medium Concurrency (5-10 jobs)
```python
pool_min_size = 3
pool_max_size = 15
heartbeat_interval_seconds = 5
visibility_timeout_seconds = 30
```

### For High Concurrency (20+ jobs)
```python
pool_min_size = 5
pool_max_size = 25
heartbeat_interval_seconds = 3
visibility_timeout_seconds = 60
max_reconnect_attempts = 5      # Fail faster
reconnect_max_delay_seconds = 30  # Recover faster
```

---

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| "Connection refused" | DB unreachable | Check host/port, DB running, firewall |
| "Pool exhausted" | All connections in use | Increase `pool_max_size` |
| "Command timeout" | Slow queries | Increase timeout, optimize query, scale DB |
| "Job not claimed" | Status not 'pending' | Check `visible_after <= NOW()` |
| "Lease extension failed" | Robot lost ownership | Job already claimed by another robot |
| "Visibility timeout exceeded" | Heartbeat failed | Check robot status, increase timeout |
| "Reconnect stuck at max attempts" | Network issues | Manual intervention needed, check DB logs |
