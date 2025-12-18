# Orchestrator + Robot + Dashboard Unification (VM/EXE, Supabase, Cloudflare)

Date: 2025-12-16

Status: Active (Phase 1 ✅, Phase 2 ✅, Phase 3 pending)

## Goal
Deliver a single, modular, scalable, deployment-friendly CasareRPA “platform”:
- **One Orchestrator** (FastAPI) deployed behind **Cloudflare Tunnel (HTTPS/WSS)**
- **One Robot runtime** (Windows `.exe`) that pulls jobs from the orchestrator over the internet and executes workflows (desktop UI automation + headless)
- **One Fleet Dashboard** (web UI) as the primary operational UX

## Constraints (repo rules)
- DDD layers: `.agent/rules/02-architecture.md`
- No silent failures; log via `loguru`: `AGENT.md`
- Strict typing; validate with `pytest`: `AGENT.md`
- Canvas UI must use theme tokens if/when modified: `.brain/plans/fleet-dashboard-ux.md`

## Key Decisions (Locked)
- **Database**: Supabase Postgres is the system database (single project for all tenants).
  - Robots do **not** connect to DB directly.
  - Orchestrator connects via `DATABASE_URL`.
- **Connectivity**: Orchestrator is reachable via **Cloudflare Tunnel HTTPS**.
  - Robots use **REST polling** (job lease model). Monitoring uses **WebSockets**.
- **Access model**: **Admin-only dashboard** (behind Cloudflare Access recommended). No tenant self-serve in Phase 1.
- **Scale target**: 50–100 robots, ~100 jobs, 1s-level realtime is sufficient.
- **Unification policy**: Force new path; remove redundant orchestrator(s) and robot agent(s).
- **Retention**: 30-day retention for jobs/logs (cleanup jobs).

## Canonical Components

### Orchestrator (Canonical)
- **Keep**: `src/casare_rpa/infrastructure/orchestrator/api/main.py` as the only FastAPI app.
  - REST control plane (jobs, robots, API keys)
  - WS monitoring plane (job/robot/queue events)
  - Serves the web dashboard build under `api/static/`

### Orchestrator (Deprecated / Removed) ✅ PHASE 2 COMPLETE
- **REMOVED**:
  - `src/casare_rpa/infrastructure/orchestrator/server.py` ✅
  - `src/casare_rpa/infrastructure/orchestrator/robot_manager.py` ✅
  - `src/casare_rpa/infrastructure/orchestrator/websocket_handlers.py` ✅
  - `src/casare_rpa/infrastructure/orchestrator/rest_endpoints.py` ✅
  - `src/casare_rpa/infrastructure/orchestrator/health_endpoints.py` ✅
  - `src/casare_rpa/infrastructure/orchestrator/server_auth.py` ✅
- **server_lifecycle.py**: Refactored to remove RobotManager dependency

### Robot (Canonical)
- **Keep** (as the canonical robot application entry): `src/casare_rpa/robot/cli.py`
- **Refactor** (make orchestrator REST pull the only mode): `src/casare_rpa/robot/agent.py`
- **Keep/Use** (robot-side orchestrator REST consumer):
  - `src/casare_rpa/infrastructure/orchestrator/robot_job_consumer.py`

### Robot (Deprecated / Removed) ✅ PHASE 2 COMPLETE
- **REMOVED** the WS control-plane robot agent:
  - `src/casare_rpa/infrastructure/agent/robot_agent.py` ✅
  - `src/casare_rpa/infrastructure/agent/robot_config.py` ✅
- **Updated**: `infrastructure/agent/__init__.py` exports (removed deprecated classes)
- **Updated**: `infrastructure/__init__.py` exports (removed deprecated classes)
- **Updated**: `agent_main.py` to redirect to canonical CLI

### Dashboard (Canonical)
- Web dashboard served from orchestrator.
- Ensure the dashboard has a source-of-truth code directory (currently only built assets appear to be committed).

## Unified API Contract

### Auth
- **Robots**: `X-Api-Key: crpa_...` (robot API key)
- **Admins**: Admin API key (recommended behind Cloudflare Access); JWT is optional/future.

### Robot lifecycle (REST)
- `POST /api/v1/robots/self-register` (robot-auth): Upsert metadata and mark online.
- `POST /api/v1/robots/heartbeat` (robot-auth): Update last_seen/metrics/status.
- `GET /api/v1/robots` (admin): List robots (filter by tenant/workspace/env/status).

### Jobs (REST)
- `POST /api/v1/jobs/claim` (robot-auth): Lease next job for robot.
- `POST /api/v1/jobs/{job_id}/extend-lease` (robot-auth)
- `POST /api/v1/jobs/{job_id}/progress` (robot-auth)
- `POST /api/v1/jobs/{job_id}/complete` (robot-auth)
- `POST /api/v1/jobs/{job_id}/fail` (robot-auth)
- `POST /api/v1/jobs/{job_id}/release` (robot-auth)

### Monitoring (WebSockets)
- WS endpoints for admin dashboard:
  - Job status updates
  - Robot status/heartbeat
  - Queue depth + metrics
- Standardize an event envelope `{type, ts, tenant_id, workspace_id, data}`.

## Data Model (Supabase Postgres)

### Tenancy
- Use `tenants` + `workspaces` (already in `deploy/migrations/versions/005_rbac_tenancy.sql`).
- Add `tenant_id` + `workspace_id` to operational tables:
  - `robots`, `workflows`, `job_queue`, `robot_api_keys`
- Phase 1 can be admin-only but still stores tenant/workspace for future.

### Status normalization
- `job_queue.status` canonical set: `pending|running|completed|failed|cancelled`
- `robots.status` canonical set: `offline|idle|busy|error|maintenance`
- Align API queries and dashboard metrics to these.

### Retention (30 days)
- Add cleanup job(s) to purge:
  - Completed/failed/cancelled jobs older than 30 days
  - Robot logs older than 30 days

## Phased Implementation Plan

### Phase 1 — Stabilize and Make Internet-Ready (Force New Path)
Success criteria:
- Robot runs with only `ORCHESTRATOR_URL` + `ORCHESTRATOR_API_KEY` and no DB creds.
- Cloudflare Tunnel deployment works for REST + WS.
- 100 robots polling at 1s does not trip rate limiting.
- Admin-only dashboard works.

Tasks:
- Fix job status consistency (`claimed` vs `running`) across API + dashboard queries.
- Add robot-authenticated `self-register` + `heartbeat` endpoints.
- Make robot endpoints rate-limit by robot key/id (not Cloudflare IP).
- Make robots table updates consistent (last_seen/last_heartbeat).
- Remove direct Supabase/DB credential paths from robot runtime.
- Add pytest coverage for: auth, claim/lease correctness, robot heartbeat.

### Phase 2 — Consolidate and Delete Duplicates
Success criteria:
- Only one orchestrator FastAPI app remains.
- Only one robot runtime path remains (REST pull).

Tasks:
- Remove `infrastructure/orchestrator/server.py` and WS robot manager stack.
- Remove WS robot agent under `infrastructure/agent/`.
- Refactor stale app-layer orchestrator engine references.

### Phase 3 — Dashboard Source + UX
Success criteria:
- Dashboard is maintainable and matches API contract.

Tasks:
- Reintroduce dashboard source (Vite/React) into repo, build into `api/static/`.
- Add tenant/workspace filtering UI (admin-only).
- Make Canvas link out to the web dashboard (optional simplification).

### Phase 4 — Hardening
Success criteria:
- Secure, observable, and operable under load.

Tasks:
- Add 30-day retention cleanup job.
- Improve audit logs for robot key usage.
- Add structured logging, correlation IDs.
- Load/perf tests (claim throughput, WS fanout).

## Expected File Areas to Touch
- Orchestrator core:
  - `src/casare_rpa/infrastructure/orchestrator/api/main.py`
  - `src/casare_rpa/infrastructure/orchestrator/api/auth.py`
  - `src/casare_rpa/infrastructure/orchestrator/api/dependencies.py`
  - `src/casare_rpa/infrastructure/orchestrator/api/adapters.py`
  - `src/casare_rpa/infrastructure/orchestrator/api/routers/jobs.py`
  - `src/casare_rpa/infrastructure/orchestrator/api/routers/robots.py`
  - `src/casare_rpa/infrastructure/orchestrator/api/routers/websockets.py`
  - `src/casare_rpa/infrastructure/orchestrator/api/routers/robot_api_keys.py`
- Robot runtime:
  - `src/casare_rpa/robot/agent.py`
  - `src/casare_rpa/robot/cli.py`
  - `src/casare_rpa/infrastructure/orchestrator/robot_job_consumer.py`
- Migrations:
  - `deploy/migrations/versions/012_*.sql` (new)
- Installer:
  - `deploy/installer/casarerpa_robot.nsi`
  - `deploy/installer/config.template.yaml`
- Deprecated removals:
  - `src/casare_rpa/infrastructure/orchestrator/server.py`
  - `src/casare_rpa/infrastructure/agent/robot_agent.py`

## Test Strategy
- Add/extend pytest tests for orchestrator:
  - robot key auth
  - claim/lease transitions
  - heartbeat updates
  - tenant/workspace scoping
- Minimal smoke test: robot polls and completes a job end-to-end.
