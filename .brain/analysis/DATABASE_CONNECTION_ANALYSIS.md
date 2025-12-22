# Archived Analysis (Non-Normative)

This file is archived analysis. Do not treat as current rules. See .agent/, .claude/, and .brain/_index.md for active guidance.

---

# Database Connection Handling Analysis - CasareRPA

## Overview

This document provides a comprehensive analysis of database connection handling in the CasareRPA robot agent and infrastructure code, including connection establishment, pooling, error handling, and recovery mechanisms.

---

## 1. Environment Variable Configuration

### DATABASE_URL Reading Locations

#### Primary Source: `src/casare_rpa/robot/agent.py`

**Lines 237-238:**
```python
postgres_url=os.getenv("POSTGRES_URL", os.getenv("DATABASE_URL", ""))
or _get_default_postgres_url(),
```

**Configuration Class: `RobotConfig.from_env()` (Lines 229-268)**
- Reads `POSTGRES_URL` environment variable first
- Falls back to `DATABASE_URL` if `POSTGRES_URL` not set
- Falls back to `_get_default_postgres_url()` if both empty

#### Frozen App Handling (Lines 672-682)

For frozen applications (compiled with PyInstaller):
```python
if not self.config.postgres_url and getattr(sys, "frozen", False):
    logger.info("Frozen app detected, building database URL from DB_PASSWORD...")
    db_url = await _fetch_database_url_from_env()
    if db_url:
        self.config.postgres_url = db_url
```

#### DB_PASSWORD Environment Variable (Lines 106-129)

**Function: `_fetch_database_url_from_env()`**
- Reads `DB_PASSWORD` from environment
- Constructs PostgreSQL URL for Supabase transaction pooler
- URL Format: `postgresql://postgres.{project_ref}:{password}@{pooler_region}.pooler.supabase.com:6543/postgres`
- **Supabase Configuration (Lines 77-80):**
  - Project Reference: `znaauaswqmurwfglantv`
  - Supabase URL: `https://znaauaswqmurwfglantv.supabase.co`
  - Pooler Region: `aws-1-eu-central-1`

#### URL Masking for Security (Lines 83-96)

**Function: `_mask_url(url: str) -> str`**
- Masks password in logs using `urllib.parse.urlparse`
- Returns `(invalid URL)` on parsing errors
- Replaces password with `****` for display

---

## 2. Connection Establishment & Pooling

### Primary Pool Implementation: `PgQueuerConsumer`

**Location:** `src/casare_rpa/infrastructure/queue/pgqueuer_consumer.py`

#### Connection Pool Creation (Lines 450-480)

**Method: `_connect()`**
```python
self._pool = await asyncpg.create_pool(
    self._config.postgres_url,
    min_size=self._config.pool_min_size,      # Default: 2
    max_size=self._config.pool_max_size,      # Default: 10
    command_timeout=30,
    statement_cache_size=0,  # Required for pgbouncer/Supabase
)
```

**Pool Configuration (ConsumerConfig - Lines 128-143):**
| Parameter | Default | Purpose |
|-----------|---------|---------|
| `pool_min_size` | 2 | Minimum connections to maintain |
| `pool_max_size` | 10 | Maximum concurrent connections |
| `max_reconnect_attempts` | 10 | Retry limit before failure |
| `reconnect_base_delay_seconds` | 1.0 | Initial retry backoff |
| `reconnect_max_delay_seconds` | 60.0 | Maximum retry backoff |
| `command_timeout` | 30 | Query timeout (seconds) |
| `statement_cache_size` | 0 | Disabled for pgbouncer/Supabase compatibility |

### Secondary Pool: DBOS Executor

**Location:** `src/casare_rpa/infrastructure/execution/dbos_executor.py`

**Lines 225-231:**
```python
self._pool = await asyncpg.create_pool(
    self.config.postgres_url,
    min_size=1,
    max_size=3,
    command_timeout=60.0,
    statement_cache_size=0,
)
```

### Tertiary Pool: Monitoring API

**Location:** `src/casare_rpa/infrastructure/orchestrator/api/database.py`

**Function: `create_db_pool()` (Lines 684-705)**
```python
pool = await asyncpg.create_pool(
    database_url,
    min_size=2,
    max_size=10,
    command_timeout=60,
    server_settings={"application_name": "casare-rpa-monitoring"},
)
```

### Generic Database Pool Manager

**Location:** `src/casare_rpa/utils/pooling/database_pool.py`

**Features:**
- Supports PostgreSQL, SQLite, MySQL
- Configurable minimum/maximum pool sizes
- Health checking before returning connections
- Connection age tracking and recycling
- Idle connection cleanup
- Statistics collection (wait times, errors, recycling)

**PostgreSQL Pool Creation (Lines 248-277):**
```python
self._pg_pool = await asyncpg.create_pool(
    self._connection_string,
    min_size=self._min_size,
    max_size=self._max_size,
    max_inactive_connection_lifetime=self._idle_timeout,
    statement_cache_size=0,
    **self._extra_options,
)
```

---

## 3. Error Handling & Connection Failures

### Reconnection Strategy: Exponential Backoff

**Location:** `PgQueuerConsumer._reconnect()` (Lines 482-526)

**Exponential Backoff Algorithm:**
```python
delay = min(
    self._config.reconnect_base_delay_seconds * (2 ** (self._reconnect_attempts - 1)),
    self._config.reconnect_max_delay_seconds,
)
# Add jitter (10-30% of delay)
jitter = delay * random.uniform(0.1, 0.3)
delay += jitter
```

**Behavior:**
- Attempt 1: ~1.1s (base 1s + 10-30% jitter)
- Attempt 2: ~2.2s (base 2s + jitter)
- Attempt 3: ~4.4s (base 4s + jitter)
- ... exponential growth up to 60s maximum
- After 10 failed attempts: marked as `FAILED`

### Connection State Management

**ConnectionState Enum (Lines 81-88):**
```python
DISCONNECTED = "disconnected"
CONNECTING = "connecting"
CONNECTED = "connected"
RECONNECTING = "reconnecting"
FAILED = "failed"
```

**State Callbacks (Lines 367-396):**
- Clients can subscribe to state change events
- Called when connection state transitions
- Used for monitoring and alerting

### Query-Level Retry Logic

**Method: `_execute_with_retry()` (Lines 545-591)**

**Handles:**
- `ConnectionDoesNotExistError` → triggers reconnect
- `InterfaceError` → triggers reconnect
- `PostgresError` (other) → bubbles up (non-connection errors don't retry)

**Max Retries:** 3 attempts per query

**Error Handling:**
```python
for attempt in range(max_retries):
    if not await self._ensure_connection():
        raise ConnectionError("Unable to establish database connection")

    try:
        # Execute query
        result: Sequence[DatabaseRecord] = await conn.fetch(query, *args)
        return list(result)
    except asyncpg.exceptions.ConnectionDoesNotExistError:
        logger.warning(f"Connection lost, attempting reconnect (attempt {attempt + 1})")
        await self._reconnect()
    except asyncpg.exceptions.InterfaceError as e:
        logger.warning(f"Interface error: {e}, attempting reconnect")
        await self._reconnect()
    except PostgresError:
        raise  # Non-connection errors propagate immediately
```

### DBOS Executor Connection Error Handling

**Location:** `dbos_executor.py` (Lines 223-239)

```python
if self.config.postgres_url and self.config.enable_checkpointing:
    try:
        self._pool = await asyncpg.create_pool(...)
        await self._ensure_checkpoint_table()
        logger.info("Checkpoint storage connected")
    except Exception as e:
        logger.warning(
            f"Failed to connect checkpoint storage: {e}. "
            "Continuing without persistence."
        )
        self._pool = None  # Graceful degradation: continue without checkpointing
```

---

## 4. Retry & Fallback Logic

### Robot Agent Fallback Strategy

**1. Configuration Source Hierarchy:**
   - Check `POSTGRES_URL` env var
   - Check `DATABASE_URL` env var
   - For frozen apps: build from `DB_PASSWORD` via Supabase API
   - Return empty string if none available

**2. Component Initialization Fallback (Lines 669-742):**
   ```python
   # PgQueuer consumer: Optional if postgres_url missing
   if self.config.postgres_url:
       consumer_config = ConsumerConfig(postgres_url=self.config.postgres_url, ...)
       self._consumer = PgQueuerConsumer(consumer_config)
       await self._consumer.start()

   # DBOS executor: Can work without database
   executor_config = DBOSExecutorConfig(
       postgres_url=self.config.postgres_url if self.config.enable_checkpointing else None,
       enable_checkpointing=self.config.enable_checkpointing,
   )
   self._executor = DBOSWorkflowExecutor(executor_config)
   ```

**3. Job Loop Circuit Breaker (Lines 857-861):**
   ```python
   if self._circuit_breaker and self._circuit_breaker.is_open:
       logger.debug("Circuit breaker open, waiting...")
       await asyncio.sleep(self.config.poll_interval_seconds)
       continue
   ```

### Visibility Timeout & Lease Extension

**Location:** `PgQueuerConsumer._heartbeat_loop()` (Lines 950-980)

**Purpose:** Prevent job timeout during long-running workflows

**Heartbeat Interval:** Default 10 seconds (configurable)

**Implementation:**
```python
async def _heartbeat_loop(self) -> None:
    while self._running:
        try:
            await asyncio.sleep(self._config.heartbeat_interval_seconds)

            async with self._lock:
                job_ids = list(self._active_jobs.keys())

            for job_id in job_ids:
                try:
                    await self.extend_lease(job_id)
                except Exception as e:
                    logger.warning(f"Heartbeat failed for job {job_id[:8]}...: {e}")
```

**Lease Extension SQL (Lines 230-237):**
```sql
UPDATE job_queue
SET visible_after = NOW() + INTERVAL '1 second' * $2
WHERE id = $1 AND status = 'running' AND robot_id = $3
RETURNING id
```

### Job Timeout & Requeue

**Timeout Detection (Lines 288-302):**
```sql
UPDATE job_queue
SET status = CASE
        WHEN retry_count < max_retries THEN 'pending'
        ELSE 'failed'
    END,
    error_message = COALESCE(error_message, '') || ' [Visibility timeout exceeded]',
    retry_count = retry_count + 1,
    visible_after = NOW()
WHERE status = 'running'
  AND visible_after < NOW()
  AND robot_id = $1
```

**Backoff Strategy (Lines 262-264):**
```python
visible_after = NOW() + INTERVAL '1 second' * (retry_count + 1) * 5
```
- Retry 1: 5s delay
- Retry 2: 10s delay
- Retry 3: 15s delay

---

## 5. Job Claiming & Lock Management

### Non-Blocking Job Claiming with SKIP LOCKED

**Location:** `PgQueuerConsumer` (Lines 202-228)

**SQL Query:**
```sql
UPDATE job_queue
SET status = 'running',
    robot_id = $3,
    started_at = NOW(),
    visible_after = NOW() + INTERVAL '1 second' * $4
WHERE id IN (
    SELECT id FROM job_queue
    WHERE status = 'pending'
      AND visible_after <= NOW()
      AND (environment = $1 OR environment = 'default' OR $1 = 'default')
    ORDER BY priority DESC, created_at ASC
    LIMIT $2
    FOR UPDATE SKIP LOCKED  -- Non-blocking, prevents contention
)
RETURNING id, workflow_id, workflow_name, ...
```

**Benefits:**
- No lock waits
- Multiple robots can claim jobs in parallel
- Atomic UPDATE with SKIP LOCKED inside WHERE clause
- Prevents TOCTOU (Time-Of-Check-Time-Of-Use) race condition

### Job Status Transitions

**Claim (Pending → Running):** Lines 202-228
**Complete (Running → Completed):** Lines 239-247
**Fail (Running → Pending or Failed):** Lines 250-273
**Release (Running → Pending):** Lines 276-285

---

## 6. Security Features

### Credential Masking

**Locations:**
- `_mask_url()` (Lines 83-96) - For logs
- `ConsumerConfig.to_dict()` (Lines 145-166) - Uses `sanitize_log_value()`
- `DBOSExecutorConfig.to_dict()` (Lines 151-169) - Uses `sanitize_log_value()`
- `RobotConfig.to_dict()` (Lines 282-300) - Returns `***` for postgres_url

### SQL Injection Prevention

**1. Parameterized Queries:**
   - All user inputs via `$1, $2, $3...` parameters
   - Never string concatenation

**2. SQL Identifier Validation (DBOS Executor):**
   ```python
   table_name = validate_sql_identifier(
       self.config.checkpoint_table, "checkpoint_table"
   )
   ```

**3. Robot ID Validation (PgQueuerConsumer):**
   ```python
   from casare_rpa.infrastructure.security.validators import validate_robot_id
   validate_robot_id(config.robot_id)
   ```

### Input Validation

- Error message truncation to 4000 chars (Lines 798)
- Variable parsing with fallback handling (Lines 638-651)
- Workflow validation in DBOS executor startup (Lines 385-390)

---

## 7. Monitoring & Statistics

### Pool Statistics

**Location:** `DatabaseConnectionPool.get_stats()` (Lines 524-541)

**Tracked Metrics:**
- Available connections
- In-use connections
- Total connections
- Total created/closed/recycled
- Acquire/release count
- Wait count and average wait time
- Error count

### Consumer Statistics

**Location:** `PgQueuerConsumer.get_stats()` (Lines 982-1004)

**Returned Data:**
```python
{
    "robot_id": str,
    "environment": str,
    "state": str,  # Connection state
    "is_connected": bool,
    "active_jobs": int,
    "active_job_ids": list,
    "reconnect_attempts": int,
    "config": {
        "batch_size": int,
        "visibility_timeout_seconds": int,
        "heartbeat_interval_seconds": int,
    }
}
```

### Audit Logging

**Location:** `robot/agent.py`

**Events Logged:**
- Robot started/stopped
- Connection established
- Checkpoint restored
- Circuit breaker state change
- Job started/completed/failed/cancelled

---

## 8. Graceful Shutdown

### Consumer Cleanup (Lines 418-448)

```python
async def stop(self) -> None:
    logger.info("Stopping PgQueuerConsumer...")
    self._running = False

    # Cancel heartbeat task
    if self._heartbeat_task and not self._heartbeat_task.done():
        self._heartbeat_task.cancel()
        try:
            await self._heartbeat_task
        except asyncio.CancelledError:
            pass

    # Release active jobs back to queue
    await self._release_all_active_jobs()

    # Close pool
    if self._pool:
        try:
            await self._pool.close()
        except Exception as e:
            logger.warning(f"Error closing connection pool: {e}")
        self._pool = None
```

### Robot Agent Shutdown (Lines 572-641)

1. **Wait for active jobs:** Max `graceful_shutdown_seconds` (default 60s)
2. **Save checkpoint:** Preserves execution state
3. **Cancel tasks:** Job loop, heartbeat, presence, metrics loops
4. **Update registration:** Mark robot as offline/paused
5. **Stop components:** Consumer, executor, resource manager, metrics

---

## 9. Connection Pooling Comparison

| Component | Driver | Pool Size (Min-Max) | Timeout | Cache | Pgbouncer Support |
|-----------|--------|-------------------|---------|-------|------------------|
| PgQueuerConsumer | asyncpg | 2-10 | 30s | 0 (disabled) | Yes |
| DBOSExecutor | asyncpg | 1-3 | 60s | 0 (disabled) | Yes |
| MonitoringAPI | asyncpg | 2-10 | 60s | N/A | Yes |
| Generic Pool | asyncpg/aiomysql/aiosqlite | Configurable | Configurable | N/A | Yes (PG) |

**All PostgreSQL pools:** `statement_cache_size=0` (required for Supabase pgbouncer compatibility)

---

## 10. Code Locations - Quick Reference

| Feature | File | Lines |
|---------|------|-------|
| Environment Variable Reading | `robot/agent.py` | 106-129, 237-238 |
| URL Masking | `robot/agent.py` | 83-96 |
| RobotConfig | `robot/agent.py` | 154-227, 229-268 |
| PgQueuerConsumer Pool | `infrastructure/queue/pgqueuer_consumer.py` | 450-480 |
| Reconnection Logic | `infrastructure/queue/pgqueuer_consumer.py` | 482-526 |
| Query Retry | `infrastructure/queue/pgqueuer_consumer.py` | 545-591 |
| Heartbeat Loop | `infrastructure/queue/pgqueuer_consumer.py` | 950-980 |
| Job Claiming SQL | `infrastructure/queue/pgqueuer_consumer.py` | 202-228 |
| DBOS Pool | `infrastructure/execution/dbos_executor.py` | 225-231 |
| Checkpoint Table | `infrastructure/execution/dbos_executor.py` | 257-290 |
| Monitoring Pool | `infrastructure/orchestrator/api/database.py` | 684-705 |
| Generic Pool | `utils/pooling/database_pool.py` | 214-280 |
| Robot Agent Init | `robot/agent.py` | 669-742 |
| Robot Agent Shutdown | `robot/agent.py` | 572-641 |
| Graceful Shutdown | `infrastructure/queue/pgqueuer_consumer.py` | 418-448 |

---

## 11. Key Insights & Recommendations

### Strengths
1. **Multiple layers of retry/fallback:** Connection drops handled at 3 levels (connection pool, query retry, circuit breaker)
2. **Pgbouncer-optimized:** Disabled statement cache for Supabase compatibility
3. **Graceful degradation:** Continues without database when unavailable
4. **Security-first:** Credential masking, SQL injection prevention, input validation
5. **Comprehensive monitoring:** Detailed statistics and audit logging
6. **DBOS durability:** Checkpointing ensures exactly-once semantics

### Areas for Improvement
1. **Connection pool size:** Generic pool defaults (min=1, max=10) may be undersized for high-concurrency scenarios
2. **Reconnect timing:** Exponential backoff could be tuned based on production metrics
3. **Idle connection cleanup:** Generic pool only cleans idle connections, doesn't detect stale connections during use
4. **Health checking:** Only basic `SELECT 1` check; could validate more thoroughly
5. **Monitoring gaps:** No alerting on connection pool saturation or frequent reconnects

### Configuration Tuning Recommendations

For high-throughput deployments:
```python
ConsumerConfig(
    pool_min_size=5,           # Increase from 2
    pool_max_size=20,          # Increase from 10
    reconnect_max_delay_seconds=30,  # Reduce from 60 for faster recovery
    max_reconnect_attempts=5,   # Reduce from 10 to fail faster
)
```

---

## Summary

CasareRPA implements a robust, multi-layered database connection handling system with:
- **3 independent connection pools** (PgQueuer, DBOS, Monitoring)
- **Exponential backoff reconnection** with jitter
- **Non-blocking job claiming** using SKIP LOCKED
- **Automatic lease extension** via heartbeat loops
- **Graceful degradation** when database unavailable
- **Security-hardened** credential handling and SQL parameterization
- **Comprehensive audit trails** for all database operations
