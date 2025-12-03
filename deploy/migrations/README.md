# Database Migrations

Centralized database migration system for CasareRPA using PostgreSQL/Supabase.

## Overview

All migrations are consolidated in `deploy/migrations/versions/` directory. The migration system:
- Tracks applied migrations in `_migrations` table
- Supports up/down rollbacks with version tracking
- Verifies checksums to detect modified migrations
- Works with both PostgreSQL and Supabase

## Directory Structure

```
deploy/migrations/
├── versions/                    # Canonical migration files (numbered 001-999)
├── down/                        # Rollback scripts (optional)
├── migrate.py                   # Migration runner (production-ready)
├── setup_db.sql                 # Database initialization template
└── README.md                    # This file
```

## Migrations

| Version | Name | Purpose | Tables |
|---------|------|---------|--------|
| 001 | initial_schema | Core tables (robots, workflows, users, environments) | robots, workflows, workflow_nodes, users, environments |
| 002 | job_queue | Job queue + pgqueuer schema | job_queue, pgqueuer.jobs, pgqueuer.queue_config |
| 003 | heartbeats | Robot heartbeat monitoring | robot_heartbeats |
| 004 | schedules | Workflow scheduling | workflow_schedules, schedule_history |
| 005 | rbac_tenancy | Multi-tenant RBAC | organizations, org_members, org_api_keys, role_permissions |
| 006 | templates | Workflow templates | workflow_templates, template_versions |
| 007 | audit_log | Audit trail with Merkle tree | audit_log, merkle_proofs |
| 008 | dlq | Dead-letter queue management | dlq, dlq_retry_history |
| 009 | healing_events | Event healing for recovery | healing_events, healing_rules |
| 010 | robot_api_keys | Robot API authentication | robot_api_keys |
| 011 | robot_logs | Robot execution logs | robot_logs |

## Usage

### Prerequisites

```bash
pip install asyncpg
export DATABASE_URL="postgresql://user:password@localhost/casare_rpa"
# OR for Supabase:
export SUPABASE_DB_URL="postgresql://postgres:password@host/postgres"
```

### Apply All Pending Migrations

```bash
python -m deploy.migrations.migrate up
```

**Output:**
```
Found 3 pending migration(s):

  [009] healing_events
      Applied in 125ms
  [010] robot_api_keys
      Applied in 87ms
  [011] robot_logs
      Applied in 156ms

Applied 3 migration(s).
```

### Check Migration Status

```bash
python -m deploy.migrations.migrate status
```

**Output:**
```
Migration Status:

Version    Name                                     Status       Applied At          Checksum
--------------------------------------------------------------------------------------------------------------
001        initial_schema                           APPLIED      2024-11-30 10:45:23 OK
002        job_queue                                APPLIED      2024-11-30 10:45:24 OK
003        heartbeats                               APPLIED      2024-11-30 10:45:25 OK
004        schedules                                APPLIED      2024-11-30 10:45:26 OK
005        rbac_tenancy                             APPLIED      2024-11-30 10:45:27 OK
006        templates                                APPLIED      2024-11-30 10:45:28 OK
007        audit_log                                APPLIED      2024-11-30 10:45:29 OK
008        dlq                                      APPLIED      2024-11-30 10:45:30 OK
009        healing_events                           PENDING      -                   -
010        robot_api_keys                           PENDING      -                   -
011        robot_logs                               PENDING      -                   -

Total: 11 | Applied: 8 | Pending: 3
```

### Rollback Last Migration

```bash
python -m deploy.migrations.migrate down
```

Rollback last 3 migrations:
```bash
python -m deploy.migrations.migrate down --steps 3
```

### Verify Migration Integrity

```bash
python -m deploy.migrations.migrate verify
```

Detects modifications to applied migrations via checksum validation.

### Preview Changes (Dry Run)

```bash
python -m deploy.migrations.migrate up --dry-run
```

### Reset Database (All Migrations Down)

```bash
python -m deploy.migrations.migrate reset
# Requires confirmation: Type 'RESET' to confirm
```

### Override Database URL

```bash
python -m deploy.migrations.migrate status --database "postgresql://user:pass@host/db"
```

## Migration Files

### Adding a New Migration

1. Create a new file in `versions/`:
   ```bash
   touch deploy/migrations/versions/012_new_feature.sql
   ```

2. Write SQL (use transactions):
   ```sql
   -- deploy/migrations/versions/012_new_feature.sql
   BEGIN;

   CREATE TABLE my_new_table (
       id SERIAL PRIMARY KEY,
       name VARCHAR(255) NOT NULL,
       created_at TIMESTAMPTZ DEFAULT NOW()
   );

   CREATE INDEX idx_my_new_table_name ON my_new_table(name);

   COMMIT;
   ```

3. (Optional) Create rollback script:
   ```bash
   touch deploy/migrations/down/012_new_feature_down.sql
   ```
   ```sql
   -- deploy/migrations/down/012_new_feature_down.sql
   DROP INDEX IF EXISTS idx_my_new_table_name;
   DROP TABLE IF EXISTS my_new_table;
   ```

4. Apply migration:
   ```bash
   python -m deploy.migrations.migrate up
   ```

### Migration Naming

- **Files**: `NNN_description.sql` (001-999, zero-padded)
- **Rollback**: `NNN_description_down.sql` in `down/` directory
- **Description**: snake_case, descriptive (e.g., `005_rbac_tenancy`, not `005_alter_tables`)

## Migrations Tracking

The `_migrations` table tracks:
- `version` - Migration number (001-999)
- `name` - Description
- `checksum` - SHA256(first 16 chars) of file content
- `applied_at` - Timestamp
- `execution_time_ms` - Duration
- `git_commit` - Git commit hash (if available)

Query applied migrations:
```sql
SELECT version, name, applied_at, execution_time_ms
FROM _migrations
ORDER BY version;
```

## Consolidation Status

All SQL migrations from scattered locations have been consolidated:

| Location | Status | Notes |
|----------|--------|-------|
| `deploy/migrations/versions/` | **Primary** | All numbered migrations (001-011) |
| `deploy/migrations/down/` | **Primary** | Rollback scripts (optional) |
| `src/casare_rpa/infrastructure/database/migrations/` | DEPRECATED | Old location (migrate to versions/) |
| `src/casare_rpa/infrastructure/queue/migrations/` | DEPRECATED | Old location (migrate to versions/) |
| `src/casare_rpa/infrastructure/persistence/migrations/` | DEPRECATED | Old location (migrate to versions/) |
| `deploy/supabase/migrations/` | DEPRECATED | Old location (migrate to versions/) |

### Cleanup Task

Remove deprecated migration directories after verifying consolidation:
```bash
# After backup
rm -r src/casare_rpa/infrastructure/database/migrations/
rm -r src/casare_rpa/infrastructure/queue/migrations/
rm -r src/casare_rpa/infrastructure/persistence/migrations/
rm -r deploy/supabase/migrations/  # Keep schema file if needed
```

## Architecture Patterns

### Migration Best Practices

1. **Idempotent Operations**
   ```sql
   -- Good: Safe for re-runs
   CREATE TABLE IF NOT EXISTS users (...);
   DROP TABLE IF EXISTS deprecated_table;

   -- Bad: Will fail if table already exists
   CREATE TABLE users (...);
   ```

2. **Explicit Transactions**
   ```sql
   BEGIN;
   -- All changes atomic
   COMMIT;
   ```

3. **Descriptive Comments**
   ```sql
   -- Migration: Add email notification system
   -- Reason: Support email alerts for workflow errors
   -- Rollback: Drop email tables, remove trigger

   CREATE TABLE email_templates (...);
   ```

4. **Zero-Downtime Deployments**
   ```sql
   -- Step 1: Add new column with default
   ALTER TABLE workflows ADD COLUMN version INT DEFAULT 1;

   -- Step 2: Backfill data
   UPDATE workflows SET version = 1 WHERE version IS NULL;

   -- Step 3: Add constraint
   ALTER TABLE workflows ALTER COLUMN version SET NOT NULL;
   ```

### Error Handling

- Migrations run in transactions (all-or-nothing)
- Rollback scripts must be idempotent
- Checksum verification prevents manual edits
- Dry-run mode (`--dry-run`) previews without executing

## Integration

### CI/CD Pipeline

```bash
# In GitHub Actions / deployment scripts
export DATABASE_URL="${{ secrets.DATABASE_URL }}"
python -m deploy.migrations.migrate up

# Verify integrity
python -m deploy.migrations.migrate verify
```

### Local Development

```bash
# Start local Postgres
docker run -e POSTGRES_PASSWORD=password -p 5432:5432 postgres:15

# Set URL
export DATABASE_URL="postgresql://postgres:password@localhost/casare_rpa"

# Apply all migrations
python -m deploy.migrations.migrate up
```

### Supabase

```bash
# Set Supabase URL
export SUPABASE_DB_URL="postgresql://postgres:[password]@[host].supabase.co/postgres"

# Apply migrations
python -m deploy.migrations.migrate up
```

## Troubleshooting

### Migration Failed

1. Check error message:
   ```bash
   python -m deploy.migrations.migrate up
   ```

2. Verify connection:
   ```bash
   psql $DATABASE_URL -c "SELECT version();"
   ```

3. Check migration table:
   ```sql
   SELECT * FROM _migrations WHERE version = '009';
   ```

4. Review SQL file:
   ```bash
   cat deploy/migrations/versions/009_healing_events.sql
   ```

### Checksum Mismatch

Migration file was modified after being applied:
```bash
python -m deploy.migrations.migrate verify
```

**Resolution:**
- Revert file to original: `git checkout deploy/migrations/versions/NNN_*.sql`
- OR create new migration for the change (recommended)

### Database Connection Issues

```bash
# Test connection
python -c "import asyncpg; asyncio.run(asyncpg.connect('$DATABASE_URL'))"

# Verify DATABASE_URL format
echo $DATABASE_URL
# Expected: postgresql://user:password@host:5432/dbname
```

### Rollback Safety

Always test rollback script before using in production:
```bash
# Test on backup database
export DATABASE_URL="postgresql://user:password@backup-host/dbname"
python -m deploy.migrations.migrate down --steps 1
python -m deploy.migrations.migrate up
```

## Commands Reference

| Command | Purpose | Example |
|---------|---------|---------|
| `up` | Apply all pending | `python -m deploy.migrations.migrate up` |
| `down` | Rollback N migrations | `python -m deploy.migrations.migrate down --steps 3` |
| `status` | Show all migrations | `python -m deploy.migrations.migrate status` |
| `verify` | Validate checksums | `python -m deploy.migrations.migrate verify` |
| `reset` | Rollback all | `python -m deploy.migrations.migrate reset` |
| `--dry-run` | Preview (no execution) | `python -m deploy.migrations.migrate up --dry-run` |
| `--database` | Override URL | `python -m deploy.migrations.migrate status --database "..."` |
| `--steps` | Rollback count | `python -m deploy.migrations.migrate down --steps 5` |

## See Also

- `.brain/projectRules.md` - CasareRPA coding standards
- `src/casare_rpa/infrastructure/database/` - ORM models
- `deploy/supabase/supabase_schema.sql` - Reference schema (Supabase format)

---
**Last Updated:** 2025-12-03
**Maintained by:** CasareRPA Core Team
**Status:** Production Ready
