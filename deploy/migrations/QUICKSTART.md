# Migration Quick Start Guide

Fast reference for common migration tasks.

## Setup (First Time)

```bash
# 1. Install dependency
pip install asyncpg

# 2. Set database URL
export DATABASE_URL="postgresql://user:password@localhost/casare_rpa"
# OR for Supabase:
export SUPABASE_DB_URL="postgresql://postgres:password@db.supabase.co/postgres"

# 3. Apply all migrations
python -m deploy.migrations.migrate up
```

## Common Tasks

### Check Current State
```bash
python -m deploy.migrations.migrate status
```

### Apply New Migrations
```bash
python -m deploy.migrations.migrate up
```

### Rollback Last Migration
```bash
python -m deploy.migrations.migrate down
```

### Rollback Last 3 Migrations
```bash
python -m deploy.migrations.migrate down --steps 3
```

### Verify Integrity
```bash
python -m deploy.migrations.migrate verify
```

### Preview Changes (No Execution)
```bash
python -m deploy.migrations.migrate up --dry-run
```

## Create New Migration

1. **Create migration file:**
   ```bash
   touch deploy/migrations/versions/012_my_feature.sql
   ```

2. **Write SQL:**
   ```sql
   BEGIN;

   CREATE TABLE my_table (
       id SERIAL PRIMARY KEY,
       name VARCHAR(255) NOT NULL,
       created_at TIMESTAMPTZ DEFAULT NOW()
   );

   CREATE INDEX idx_my_table_name ON my_table(name);

   COMMIT;
   ```

3. **(Optional) Create rollback:**
   ```bash
   touch deploy/migrations/down/012_my_feature_down.sql
   ```
   ```sql
   DROP INDEX IF EXISTS idx_my_table_name;
   DROP TABLE IF EXISTS my_table;
   ```

4. **Apply it:**
   ```bash
   python -m deploy.migrations.migrate up
   ```

## File Naming

- **Migration:** `NNN_description.sql` (zero-padded)
  - `001_initial_schema.sql`
  - `012_new_feature.sql` (not `new_feature.sql`)

- **Rollback:** `NNN_description_down.sql` in `down/` folder
  - `001_initial_schema_down.sql`
  - `012_new_feature_down.sql`

- **Description:** Use snake_case, be specific
  - Good: `010_robot_api_keys`, `007_audit_log`
  - Bad: `010_updates`, `007_fix`

## Tips

### Pre-flight Check
```bash
# Test dry-run before applying
python -m deploy.migrations.migrate up --dry-run
# Then apply
python -m deploy.migrations.migrate up
```

### Verify After Apply
```bash
python -m deploy.migrations.migrate verify
```

### Connect to Database
```sql
-- Check migrations table
SELECT version, name, applied_at FROM _migrations ORDER BY version;

-- Check table exists
SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='my_table');
```

### Troubleshoot
```bash
# Check connection
psql $DATABASE_URL -c "SELECT version();"

# Check migration errors
python -m deploy.migrations.migrate up  # See error message

# View migration file
cat deploy/migrations/versions/NNN_*.sql
```

## All Commands

```bash
# Apply pending
python -m deploy.migrations.migrate up

# Rollback 1
python -m deploy.migrations.migrate down

# Rollback 3
python -m deploy.migrations.migrate down --steps 3

# Check status
python -m deploy.migrations.migrate status

# Verify integrity
python -m deploy.migrations.migrate verify

# Preview
python -m deploy.migrations.migrate up --dry-run

# Reset all
python -m deploy.migrations.migrate reset

# Custom DB URL
python -m deploy.migrations.migrate status --database "postgresql://..."
```

## Current Migrations

```
001 - initial_schema          robots, workflows, users
002 - job_queue              job_queue, pgqueuer schema
003 - heartbeats             robot_heartbeats
004 - schedules              workflow_schedules
005 - rbac_tenancy           organizations, roles
006 - templates              workflow_templates
007 - audit_log              audit_log, merkle_proofs
008 - dlq                    dlq (dead-letter queue)
009 - healing_events         healing_events
010 - robot_api_keys         robot_api_keys
011 - robot_logs             robot_logs
```

## See Also

- **README.md** - Full documentation
- **CONSOLIDATION.md** - Migration history
- `.brain/projectRules.md` - Project standards

---
Last Updated: 2025-12-03
