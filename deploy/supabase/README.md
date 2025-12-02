# CasareRPA Supabase Fleet Management Setup

This guide covers setting up Supabase for CasareRPA's robot fleet management, including database schema, realtime subscriptions, and optional Edge Functions.

## Quick Start (Unified CLI)

The recommended way to set up Supabase is using the unified setup CLI:

```bash
# Interactive first-time setup wizard
python -m deploy.supabase.setup quickstart

# Or individual commands:
python -m deploy.supabase.setup init --project-ref REF --service-key KEY  # Create .env
python -m deploy.supabase.setup migrate                                    # Run migrations
python -m deploy.supabase.setup functions                                  # Deploy edge functions
python -m deploy.supabase.setup rls                                        # Show RLS policies
python -m deploy.supabase.setup verify                                     # Verify setup
python -m deploy.supabase.setup all --db-password PWD                      # Complete setup
python -m deploy.supabase.setup types                                      # Generate Python types
```

For help with any command:
```bash
python -m deploy.supabase.setup --help
python -m deploy.supabase.setup migrate --help
```

---

## Table of Contents

1. [Project Setup](#1-project-setup)
2. [Database Schema](#2-database-schema)
3. [Realtime Configuration](#3-realtime-configuration)
4. [Environment Variables](#4-environment-variables)
5. [Row Level Security](#5-row-level-security)
6. [Edge Functions](#6-edge-functions)
7. [Client Integration](#7-client-integration)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Project Setup

### Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign in
2. Click **New Project**
3. Configure:
   - **Organization**: Select or create organization
   - **Name**: `casarerpa-fleet` (or your preferred name)
   - **Database Password**: Generate a strong password (save this!)
   - **Region**: Choose closest to your robots
   - **Pricing Plan**: Free tier works for development

4. Wait for project provisioning (~2 minutes)

### Get API Keys

After project creation, go to **Settings > API**:

| Key | Usage | Security |
|-----|-------|----------|
| **Project URL** | Base URL for all API calls | Public |
| **anon (public)** | Robot client connections | Public (safe to expose) |
| **service_role** | Orchestrator admin operations | SECRET (server-side only) |

> **Warning**: Never expose the `service_role` key in client-side code or version control.

---

## 2. Database Schema

### Run Migration

**Option A: SQL Editor (Recommended for first setup)**

1. Go to **SQL Editor** in Supabase Dashboard
2. Create new query
3. Copy contents of `migrations/001_initial_schema.sql`
4. Click **Run**

**Option B: Supabase CLI**

```bash
# Install Supabase CLI
npm install -g supabase

# Login
supabase login

# Link to your project
supabase link --project-ref YOUR_PROJECT_REF

# Push migrations
supabase db push
```

### Schema Overview

The migration creates these tables:

| Table | Purpose | Realtime |
|-------|---------|----------|
| `workflows` | Workflow definitions (JSON) | No |
| `robots` | Robot fleet registry | Yes |
| `jobs` | Job queue and execution state | Yes |
| `robot_api_keys` | API key authentication | No |
| `robot_logs` | Partitioned log storage | Optional |
| `schedules` | Cron-based scheduling | No |
| `workflow_robot_assignments` | Workflow-to-robot mapping | No |
| `node_robot_overrides` | Node-level robot targeting | No |
| `robot_heartbeats` | Historical heartbeat data | No |

### Verify Installation

Run this query to verify tables were created:

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_type = 'BASE TABLE'
ORDER BY table_name;
```

Expected tables: `jobs`, `robot_api_key_audit`, `robot_api_keys`, `robot_heartbeats`, `robot_logs`, `robot_logs_cleanup_history`, `robots`, `schedules`, `workflow_robot_assignments`, `workflow_versions`, `workflows`, `node_robot_overrides`

---

## 3. Realtime Configuration

### Enable Realtime for Tables

1. Go to **Database > Replication**
2. Enable realtime for:
   - `robots` (status updates, heartbeats)
   - `jobs` (job queue changes)

Or run this SQL:

```sql
-- Enable realtime for robots table
ALTER PUBLICATION supabase_realtime ADD TABLE robots;

-- Enable realtime for jobs table
ALTER PUBLICATION supabase_realtime ADD TABLE jobs;
```

### Configure Presence Channel

Presence enables tracking which robots are currently online. Configure in the Orchestrator:

```python
# Python example for Orchestrator
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Subscribe to robot fleet presence
channel = supabase.channel("robot-fleet")

async def on_presence_sync(payload):
    """Handle robot presence updates."""
    presences = payload["presences"]
    for robot_id, presence in presences.items():
        print(f"Robot {robot_id}: {presence}")

channel.on_presence_sync(on_presence_sync)
channel.subscribe()
```

### Realtime Events

| Event | Channel | Payload |
|-------|---------|---------|
| Robot online/offline | `robot-fleet` | `{robot_id, status, hostname}` |
| Job claimed | `jobs` | `{job_id, robot_uuid, status}` |
| Job progress | `jobs` | `{job_id, progress, current_node}` |
| Job completed | `jobs` | `{job_id, status, result}` |

---

## 4. Environment Variables

Copy `.env.example` to `.env` and configure:

### Required Variables

```bash
# Supabase connection
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=eyJ...  # From Settings > API
SUPABASE_SERVICE_KEY=eyJ...  # From Settings > API (keep secret!)
```

### Robot Configuration

```bash
# Robot identity
ROBOT_API_KEY=crpa_...  # Generated via Orchestrator
ROBOT_NAME=robot-01
ROBOT_ENVIRONMENT=production

# Heartbeat settings
ROBOT_HEARTBEAT_INTERVAL=30  # seconds
```

### Orchestrator Configuration

```bash
# Multi-tenancy
TENANT_ID=00000000-0000-0000-0000-000000000000

# Job queue
JOB_POLL_INTERVAL=5  # seconds
ROBOT_OFFLINE_THRESHOLD=90  # seconds without heartbeat

# Retention
LOG_RETENTION_DAYS=30
```

---

## 5. Row Level Security

### Enable RLS

After testing basic connectivity, enable Row Level Security:

```sql
-- Enable RLS on sensitive tables
ALTER TABLE robots ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE robot_api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE robot_logs ENABLE ROW LEVEL SECURITY;
```

### Example Policies

**Service Role Access (Orchestrator)**

```sql
-- Full access for service role (server-side operations)
CREATE POLICY "Service role full access" ON robots
    FOR ALL
    USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access" ON jobs
    FOR ALL
    USING (auth.role() = 'service_role');
```

**Robot Self-Access**

```sql
-- Robots can only update their own records
CREATE POLICY "Robots can read own record" ON robots
    FOR SELECT
    USING (robot_id = auth.uid());

CREATE POLICY "Robots can update own status" ON robots
    FOR UPDATE
    USING (robot_id = auth.uid())
    WITH CHECK (robot_id = auth.uid());
```

**Tenant Isolation**

```sql
-- Multi-tenant log isolation
CREATE POLICY "Tenant isolation" ON robot_logs
    FOR ALL
    USING (tenant_id = auth.uid());
```

---

## 6. Edge Functions

### Deploy Functions

```bash
# Navigate to supabase directory
cd deploy/supabase

# Deploy cleanup function
supabase functions deploy cleanup-logs

# Deploy notification function
supabase functions deploy job-notification
```

### Log Cleanup Function

Automatically removes old log partitions based on retention policy.

**Manual Invocation:**

```bash
# Run cleanup with 30-day retention
supabase functions invoke cleanup-logs --data '{"retention_days": 30}'

# Dry run (see what would be deleted)
supabase functions invoke cleanup-logs --data '{"retention_days": 30, "dry_run": true}'
```

**Schedule via pg_cron:**

```sql
-- Install pg_cron extension (if not enabled)
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Schedule daily cleanup at 2 AM UTC
SELECT cron.schedule(
    'cleanup-robot-logs',
    '0 2 * * *',
    $$SELECT drop_old_robot_logs_partitions(30)$$
);
```

### Job Notification Function

Sends webhooks when job status changes.

**Configure Webhook:**

1. Go to **Database > Webhooks**
2. Create webhook:
   - **Name**: `job-status-notifications`
   - **Table**: `jobs`
   - **Events**: `UPDATE`
   - **URL**: `https://<project-ref>.supabase.co/functions/v1/job-notification`

**Set Environment Variables:**

```bash
# In Supabase Dashboard > Edge Functions > job-notification > Secrets
JOB_NOTIFICATION_WEBHOOK=https://your-webhook-endpoint.com/webhooks
NOTIFICATION_EVENTS=job.completed,job.failed
```

---

## 7. Client Integration

### Python (Robot/Orchestrator)

```bash
pip install supabase
```

```python
from supabase import create_client, Client
import os

# Initialize client
supabase: Client = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_ANON_KEY"]  # or SERVICE_KEY for orchestrator
)

# Register robot
robot_data = {
    "name": "robot-01",
    "hostname": "workstation-01.local",
    "status": "online",
    "capabilities": ["browser", "desktop"],
    "max_concurrent_jobs": 1
}
result = supabase.table("robots").insert(robot_data).execute()
robot_id = result.data[0]["robot_id"]

# Send heartbeat
supabase.table("robots").update({
    "last_heartbeat": "now()",
    "status": "online"
}).eq("robot_id", robot_id).execute()

# Claim job from queue
job = supabase.table("jobs")\
    .update({"status": "claimed", "robot_uuid": robot_id})\
    .eq("status", "queued")\
    .order("priority", desc=True)\
    .order("created_at")\
    .limit(1)\
    .execute()
```

### Realtime Subscriptions

```python
# Subscribe to job changes
def handle_job_change(payload):
    print(f"Job {payload['new']['job_id']}: {payload['new']['status']}")

supabase.channel("jobs-channel")\
    .on_postgres_changes("*", schema="public", table="jobs", callback=handle_job_change)\
    .subscribe()
```

---

## 8. Troubleshooting

### Common Issues

**"relation does not exist"**

Migration not run. Execute `migrations/001_initial_schema.sql` in SQL Editor.

**Realtime not working**

1. Check table is in replication: `SELECT * FROM pg_publication_tables`
2. Verify client subscription is active
3. Check Supabase Dashboard > Realtime for connection status

**API Key validation fails**

1. Verify key hash matches: `SELECT * FROM robot_api_keys WHERE api_key_hash = 'your_hash'`
2. Check key not revoked/expired
3. Ensure using SHA-256 hash of raw key

**Log partitions not created**

Run manually:
```sql
SELECT * FROM ensure_robot_logs_partitions(2);
```

**High database usage**

1. Check log volume: `SELECT * FROM robot_logs_daily_summary`
2. Reduce retention: `SELECT * FROM drop_old_robot_logs_partitions(7)`
3. Optimize queries with EXPLAIN ANALYZE

### Support Resources

- [Supabase Documentation](https://supabase.com/docs)
- [CasareRPA GitHub Issues](https://github.com/your-org/casarerpa/issues)
- [Supabase Discord](https://discord.supabase.com)

---

## Quick Reference

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/rest/v1/robots` | GET/POST/PATCH | Robot CRUD |
| `/rest/v1/jobs` | GET/POST/PATCH | Job queue operations |
| `/rest/v1/rpc/validate_api_key_hash` | POST | Validate robot API key |
| `/functions/v1/cleanup-logs` | POST | Trigger log cleanup |

### Database Functions

```sql
-- Validate API key
SELECT * FROM validate_api_key_hash('sha256_hash_here');

-- Update key usage
SELECT update_api_key_last_used('sha256_hash_here', '192.168.1.1'::inet);

-- Ensure log partitions
SELECT * FROM ensure_robot_logs_partitions(2);

-- Cleanup old logs
SELECT * FROM drop_old_robot_logs_partitions(30);

-- Query logs with filtering
SELECT * FROM query_robot_logs(
    p_tenant_id := 'uuid-here',
    p_robot_id := 'uuid-here',
    p_min_level := 'WARNING',
    p_limit := 100
);
```

### Views

```sql
-- Robot statistics
SELECT * FROM robot_stats;

-- Workflow assignments
SELECT * FROM workflow_assignment_stats;

-- Active API keys
SELECT * FROM robot_api_keys_active;

-- Log statistics
SELECT * FROM robot_logs_daily_summary;
```
