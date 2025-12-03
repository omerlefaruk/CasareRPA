# Migration System Architecture

Visual reference for the consolidated migration infrastructure.

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    CasareRPA Database Migrations                │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│   migrate.py         │ Production-ready migration runner
│   (async, robust)    │ - Discovers migrations in versions/
└──────┬───────────────┘ - Tracks in _migrations table
       │                 - Supports up/down/status/verify/reset
       │
       ├─→ versions/            Canonical migration files
       │   ├─ 001_*.sql         (numbered, sequential)
       │   ├─ 002_*.sql
       │   └─ ...011_*.sql
       │
       └─→ down/                Rollback scripts (optional)
           └─ NNN_*_down.sql
```

## Migration Execution Flow

```
┌──────────────────────────────────────────────────────────────────┐
│ python -m deploy.migrations.migrate up                           │
└──────────────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │ 1. Discover migrations in versions/│
        │    (find all .sql files)          │
        └───────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │ 2. Connect to database            │
        │    (PostgreSQL or Supabase)       │
        └───────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │ 3. Ensure _migrations table       │
        │    (create if missing)            │
        └───────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │ 4. Get applied migrations         │
        │    (from _migrations table)       │
        └───────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │ 5. Find pending (not applied)     │
        │    (discovered vs applied)        │
        └───────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │ FOR EACH PENDING MIGRATION        │
        └───────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
        ┌─────────────────┐    ┌─────────────────┐
        │ Dry-run Mode    │    │ Execute Mode    │
        │ (preview)       │    │ (apply)         │
        └─────────────────┘    └────────┬────────┘
                                        │
                                        ▼
                        ┌───────────────────────────────┐
                        │ BEGIN TRANSACTION             │
                        └───────────────────────────────┘
                                        │
                                        ▼
                        ┌───────────────────────────────┐
                        │ Execute SQL from migration    │
                        └───────────────────────────────┘
                                        │
                                        ▼
                        ┌───────────────────────────────┐
                        │ Record in _migrations         │
                        │ - version, name, checksum    │
                        │ - applied_at, exec_time_ms   │
                        │ - git_commit (if available)   │
                        └───────────────────────────────┘
                                        │
                                        ▼
                        ┌───────────────────────────────┐
                        │ COMMIT TRANSACTION            │
                        └───────────────────────────────┘
                                        │
        ┌───────────────────────────────┴───────────────────┐
        │ Continue to next pending migration                 │
        └───────────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │ Report: N migrations applied      │
        │ Summary: success/failure count    │
        └───────────────────────────────────┘
```

## Rollback Flow

```
┌──────────────────────────────────────────────────────────────────┐
│ python -m deploy.migrations.migrate down --steps N               │
└──────────────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │ 1. Get applied migrations (DESC)  │
        │    (in reverse order)             │
        └───────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │ 2. Take last N applied            │
        └───────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │ FOR EACH MIGRATION TO ROLLBACK    │
        └───────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
        ┌─────────────────┐    ┌─────────────────────┐
        │ Has rollback    │    │ No rollback script  │
        │ script?         │    │ - Show warning      │
        └────────┬────────┘    │ - Skip migration    │
                 │             └─────────────────────┘
                 ▼
        ┌──────────────────────────────────┐
        │ Read down/NNN_*_down.sql         │
        └──────────────────────────────────┘
                 │
                 ▼
        ┌──────────────────────────────────┐
        │ BEGIN TRANSACTION                │
        └──────────────────────────────────┘
                 │
                 ▼
        ┌──────────────────────────────────┐
        │ Execute rollback SQL             │
        └──────────────────────────────────┘
                 │
                 ▼
        ┌──────────────────────────────────┐
        │ Remove from _migrations          │
        └──────────────────────────────────┘
                 │
                 ▼
        ┌──────────────────────────────────┐
        │ COMMIT TRANSACTION               │
        └──────────────────────────────────┘
```

## Data Structure: _migrations Table

```
CREATE TABLE _migrations (
    ┌────────────────────────────────────────────┐
    │ Column           │ Type        │ Purpose    │
    ├────────────────────────────────────────────┤
    │ id               │ SERIAL PK   │ Auto ID    │
    │ version          │ VARCHAR(10) │ 001-999    │
    │ name             │ VARCHAR(255)│ Description│
    │ checksum         │ VARCHAR(32) │ SHA256[16] │
    │ applied_at       │ TIMESTAMPTZ │ When      │
    │ execution_time_ms│ INTEGER     │ How long   │
    │ git_commit       │ VARCHAR(40) │ Git hash   │
    └────────────────────────────────────────────┘

Example Record:
┌──────────┬──────────────────┬──────────────────────┬───────────────┐
│ version  │ name             │ applied_at           │ checksum      │
├──────────┼──────────────────┼──────────────────────┼───────────────┤
│ 001      │ initial_schema   │ 2024-11-30 10:45:23  │ a1b2c3d4... │
│ 002      │ job_queue        │ 2024-11-30 10:45:24  │ e5f6g7h8... │
│ 009      │ healing_events   │ 2024-12-01 14:22:01  │ i9j0k1l2... │
└──────────┴──────────────────┴──────────────────────┴───────────────┘
```

## Directory Structure

```
deploy/migrations/
│
├── __init__.py
│   Package marker for Python imports
│   from deploy.migrations.migrate import ...
│
├── migrate.py
│   ┌─────────────────────────────────────────────┐
│   │ Core Components:                            │
│   ├─────────────────────────────────────────────┤
│   │ - MigrationFile: Parse filename + checksum  │
│   │ - AppliedMigration: DB record representation│
│   │ - get_connection(): Async DB connect        │
│   │ - discover_migrations(): Find .sql files    │
│   │ - cmd_up(): Apply pending                   │
│   │ - cmd_down(): Rollback N                    │
│   │ - cmd_status(): Show status                 │
│   │ - cmd_verify(): Check checksums             │
│   │ - cmd_reset(): Rollback all                 │
│   └─────────────────────────────────────────────┘
│
├── versions/
│   ├── 001_initial_schema.sql
│   ├── 002_job_queue.sql
│   ├── 003_heartbeats.sql
│   ├── 004_schedules.sql
│   ├── 005_rbac_tenancy.sql
│   ├── 006_templates.sql
│   ├── 007_audit_log.sql
│   ├── 008_dlq.sql
│   ├── 009_healing_events.sql
│   ├── 010_robot_api_keys.sql
│   └── 011_robot_logs.sql
│
├── down/ (optional rollback scripts)
│   └── 001_initial_schema_down.sql
│       (pattern: NNN_name_down.sql)
│
├── setup_db.sql (legacy reference)
│
├── README.md
│   Comprehensive production guide
│   - Usage (up/down/status/verify)
│   - Best practices
│   - Integration examples
│   - Troubleshooting
│
├── QUICKSTART.md
│   Fast developer reference
│   - Setup instructions
│   - Common tasks
│   - Create new migration
│   - File naming
│
├── CONSOLIDATION.md
│   Historical record
│   - Before/after comparison
│   - Mapping of old locations
│   - Files ready for removal
│   - Verification checklist
│
└── ARCHITECTURE.md (this file)
    Visual reference & design
```

## Migration File Format

```sql
-- deploy/migrations/versions/NNN_description.sql

-- Comments explaining the migration
-- Reason: Why this change?
-- Impact: What tables affected?

BEGIN;

-- Idempotent operations (safe for re-runs)
CREATE TABLE IF NOT EXISTS my_table (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_my_table_name
ON my_table(name);

-- Update tracking
CREATE INDEX IF NOT EXISTS idx_migrations_version
ON _migrations(version);

COMMIT;
```

## Command Flow Diagram

```
User Input
    │
    ├─ up              Apply pending
    │                  ├─ Discover
    │                  ├─ Filter (pending)
    │                  ├─ Execute (transactional)
    │                  └─ Record
    │
    ├─ down            Rollback N
    │                  ├─ Get applied (DESC)
    │                  ├─ Take last N
    │                  ├─ Execute rollback
    │                  └─ Remove record
    │
    ├─ status          Show migration state
    │                  ├─ Discover
    │                  ├─ Get applied
    │                  └─ Display (table)
    │
    ├─ verify          Check checksums
    │                  ├─ Discover
    │                  ├─ Get applied
    │                  └─ Compare hashes
    │
    └─ reset           Rollback all
                       └─ down --steps N (all)
                          + confirmation
```

## Sequence Diagram: Migration Application

```
Client                Database           Migrate.py         File System
  │                       │                    │                   │
  ├─ migrate up ──────────→├─ Connect          │                   │
  │                       │                    │                   │
  │                       │                    ├─ discover ────────→
  │                       │                    │                   │
  │                       │                    │← [001, 002, ...]──┤
  │                       │                    │                   │
  │                       │← Create _migrations if missing          │
  │                       │                    │                   │
  │                       │← Get applied       │                   │
  │                       │                    │                   │
  │                       │                    ├─ filter pending   │
  │                       │                    │                   │
  │                       │← BEGIN TRANSACTION │                   │
  │                       │                    │                   │
  │                       │← Execute 003       ├─ read ───────────→
  │                       │                    │                   │
  │                       │← 003.sql ─────────→                   │
  │                       │                    │                   │
  │                       │← INSERT _migrations│                   │
  │                       │                    │                   │
  │                       │← COMMIT            │                   │
  │                       │                    │                   │
  │ ← Report:             │                    │                   │
  │   Applied in Xms      │                    │                   │
```

## Error Handling

```
Migration Execution
        │
        ├─ Connection Error
        │  → Retry with backoff
        │  → Display DB error
        │  → Exit
        │
        ├─ File Not Found
        │  → Skip invalid files
        │  → Log warning
        │  → Continue
        │
        ├─ SQL Syntax Error
        │  → Rollback transaction
        │  → Display error
        │  → Exit
        │
        ├─ Duplicate Migration
        │  → Skip (already applied)
        │  → Display (already applied)
        │
        └─ Checksum Mismatch
           → Display warning
           → Suggest revert
           → Block application
```

## Performance Characteristics

```
Operation              │ Time     │ Complexity │ Notes
───────────────────────┼──────────┼────────────┼─────────────────
discover_migrations()  │ < 10ms   │ O(N)       │ File I/O only
connect()              │ < 100ms  │ O(1)       │ Network I/O
get_applied()          │ < 50ms   │ O(N)       │ DB query
apply_migration()      │ Varies   │ Varies     │ Depends on SQL
checksum_verify()      │ < 5ms    │ O(N)       │ In-memory hash

Total (typical):       │ < 500ms  │ O(N)       │ For 11 migrations
```

## Integration Points

### With Application Startup
```python
# app/main.py
async def startup():
    await migrate_database()  # Run migrations
    await initialize_app()
```

### With CI/CD
```yaml
# .github/workflows/deploy.yml
- name: Apply Migrations
  run: |
    export DATABASE_URL=${{ secrets.DATABASE_URL }}
    python -m deploy.migrations.migrate up
```

### With Docker
```dockerfile
FROM python:3.12
RUN pip install asyncpg
COPY deploy/migrations/ /app/deploy/migrations/
CMD ["python", "-m", "deploy.migrations.migrate", "up"]
```

## State Machine

```
┌─────────────────────────────┐
│    Database States          │
└─────────────────────────────┘

No _migrations Table
        │
        ▼
    [Initial]──────→ _migrations table created
        │           │
        ▼           ▼
    [Empty]────────→ 001 applied
        │           │
        ▼           ▼
    [001]─────────→ 002 applied
        │           │
        ▼           ▼
    [002]─────────→ ...
        │           │
        ▼           ▼
    [011]←─────── Rollback
        │
        ▼
    [010]──────→ Reapply
```

---

**Last Updated:** 2025-12-03
**Version:** 1.0.0
**Status:** Stable
