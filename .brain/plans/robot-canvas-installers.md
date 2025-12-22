# Plan: Robot EXE + Canvas EXE + “Do-nothing” Client Installer (Orchestrator-first)

**Date**: 2025-12-15

## Goal
Deliver:
1) A **Robot executable** (`CasareRPA-Robot.exe`) that connects to the **Orchestrator API**, **pulls workflows/jobs**, executes them, and reports status.
2) A **Canvas executable** (`CasareRPA.exe`) for designing workflows and managing robots/jobs via Orchestrator.
3) A **client-friendly installer** (single `.exe`) that installs the robot and auto-starts it with minimal/no manual steps.

Orchestrator is expected to run in the cloud later; clients should not run DB/orchestrator locally.

## Non-negotiables (from repo rules)
- **No hardcoded secrets** shipped to clients. (The current robot NSIS includes DB password; this must be removed.)
- **No silent failures** for external calls; log with `loguru`.
- **Keep UX minimal**: don’t add extra pages or “nice-to-have” features beyond what’s described.

## Current State (what exists)
- Build tooling exists: `deploy/installer/build.py`, `deploy/installer/build.ps1`, PyInstaller specs:
  - `deploy/installer/casarerpa.spec` → `CasareRPA.exe` (Canvas) + `CasareRPA-Robot.exe` (robot)
  - `deploy/installer/casarerpa_robot.spec` → robot-only build (currently includes `supabase`)
- NSIS scripts exist:
  - `deploy/installer/casarerpa.nsi` (combined installer)
  - `deploy/installer/casarerpa_robot.nsi` (robot-only installer) **currently hardcodes Supabase + DB password** (must be removed)
- Client-facing docs exist: `deploy/CLIENT_DEPLOYMENT.md` (partially accurate but mentions Supabase/DB details that should not be client concerns).

## Target UX (installer)
### Interactive install (non-technical user)
- User runs `CasareRPA-Robot-Setup.exe`
- Installer asks for:
  - `Orchestrator URL` (https://…)
  - `Robot API Key` (crpa_…)
  - Optional: `Robot Name` (default: COMPUTERNAME)
- Installer configures auto-start on boot (scheduled task preferred).
- Done. No terminal steps.

### Silent install (IT / mass deployment)
- Allow:
  - `CasareRPA-Robot-Setup.exe /S /ORCH_URL=... /ROBOT_KEY=... /ROBOT_NAME=...`
- This enables “do nothing else” deployment in enterprise environments.

## Key Design Decision: eliminate robot_id from client setup
To make onboarding truly minimal, the robot should not require the user to input `robot_id`.

Plan option (recommended):
- Add `POST /api/v1/robots/self-register` that uses `X-Api-Key` to identify the robot_id, and accepts metadata (name/capabilities/env/max_concurrent_jobs/tags).
- Robot Agent uses this endpoint during startup.

This allows the client installer to request only URL + robot API key + optional name.

## Execution Plan (phased)

### Phase 1 — Robot execution flow audit
- Confirm exact sequence in Robot Agent:
  - registration/update
  - job claiming (`/api/v1/jobs/claim` uses `X-Api-Key` today)
  - workflow fetch endpoint(s)
  - status reporting endpoints
- Confirm config precedence for installed mode:
  - `%APPDATA%\CasareRPA\config.yaml` / `.env` / environment variables

### Phase 2 — Orchestrator enrollment endpoint (if needed)
- Implement `/api/v1/robots/self-register` (robot-authenticated via `X-Api-Key`).
- Update Robot Agent to call it.
- Add orchestrator tests.

### Phase 3 — Build outputs
- Robot:
  - Ensure `CasareRPA-Robot.exe` is produced from a single, authoritative spec.
  - Remove unnecessary `supabase` dependency from robot-only spec if orchestrator-first.
- Canvas:
  - Ensure `CasareRPA.exe` continues to launch Canvas and connects to Orchestrator.

### Phase 4 — Installer modernization (robot-first)
- Replace `deploy/installer/casarerpa_robot.nsi` with orchestrator-first logic:
  - Remove Supabase settings and DB password entirely.
  - Write `%APPDATA%\CasareRPA\config.yaml` (or `.env`) with orchestrator URL + robot API key + name.
  - Create scheduled task (or service) to run `CasareRPA-Robot.exe start` at boot.
  - Uninstall cleans scheduled task + config (or preserves config; decide and document).
- Update combined installer (`deploy/installer/casarerpa.nsi`) to align (same orchestrator-first config).

### Phase 5 — Documentation updates
- Add `deploy/installer/README.md` with:
  - prerequisites (Python, PyInstaller, NSIS)
  - exact build commands (portable + NSIS)
  - where artifacts appear under `dist/`
  - signing notes
- Update `DEPLOY.md` to point at the unified installer builder and remove client DB/Supabase guidance.
- Update `deploy/CLIENT_DEPLOYMENT.md` to match the new “URL + robot key only” onboarding.

### Phase 6 — Validation
- `pytest tests/infrastructure/orchestrator/ -v` for auth/enrollment
- Add a minimal smoke script (optional) that hits `/health` and tries self-register with a test key.

## Deliverables
- Robot exe: `dist/CasareRPA-Robot/CasareRPA-Robot.exe`
- Canvas exe: `dist/CasareRPA/CasareRPA.exe`
- Robot installer: `dist/CasareRPA-Robot-<version>-Setup.exe`
- Updated docs: `deploy/installer/README.md`, `DEPLOY.md`, `deploy/CLIENT_DEPLOYMENT.md`

## Open Questions (need your call)
1) Do you want the client installer to install **Robot only**, or **Robot + Canvas** by default?
2) Auto-start method: Scheduled Task (recommended) vs Windows Service (requires extra tooling).
3) Should uninstall **preserve** `%APPDATA%\CasareRPA\config.yaml` (so reinstall keeps enrollment) or wipe it?
