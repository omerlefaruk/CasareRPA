# Fleet Dashboard (Robots, Jobs, API Keys)

This guide shows how to operate CasareRPA with the **Canvas Fleet Dashboard** backed by the **Orchestrator API**.

## Prerequisites

- Orchestrator running and reachable
  - Local origin: `http://127.0.0.1:8000`
  - If using Cloudflare named tunnel (example): `https://api.casare.net` must forward to the running origin.
- Canvas configured to talk to Orchestrator (URL + admin API key)
- PostgreSQL recommended (for persistent robots + API keys)

## 1) Connect Canvas to Orchestrator

1. Start Orchestrator.
2. Start Canvas.
3. In Canvas, set:
   - **Orchestrator URL**: `https://api.casare.net` (or your origin URL)
   - **API Key**: use your long-lived admin key (for example `ORCHESTRATOR_ADMIN_API_KEY` or `API_SECRET`).

Canvas uses this key as:
- `Authorization: Bearer <key>` for REST
- `token=<key>` for WebSockets (connects to `/ws/...`)

## 2) Add a Robot (two options)

### Option A (recommended): start the Robot Agent (auto-register)

1. On the robot machine, set:
   - `CASARE_ORCHESTRATOR_URL` to your Orchestrator URL
   - `CASARE_ORCHESTRATOR_API_KEY` (robot API key, used as `X-Api-Key`)
   - `CASARE_ROBOT_ID` (unique string)
   - `CASARE_ROBOT_NAME`
2. Start the Robot Agent.
3. In Canvas -> **Fleet Dashboard** -> **Robots**, click **Refresh**. The robot should appear as **ONLINE/IDLE** after it heartbeats.

Windows helper script (sets env vars and can start the agent):

```powershell
PowerShell -ExecutionPolicy Bypass -File .\deploy\windows\enroll-orchestrator-robot.ps1 `
   -OrchestratorUrl "https://api.casare.net" `
   -RobotId "robot-01" `
   -RobotName "PC-01" `
   -RobotApiKey "crpa_..." `
   -Scope User `
   -StartRobotAgent
```

### Option B: create a robot record from Canvas (manual)

1. Canvas -> **Fleet Dashboard** -> **Robots**.
2. Click **Add Robot**.
3. Fill in:
   - **Name**
   - **Environment** (production/staging/dev)
   - **Max Concurrent Jobs**
   - **Capabilities** (Browser/Desktop/GPU/High Memory)
4. Click **Save**.

Canvas will create a robot id automatically and show it in a status message. Next, create an API key for it (below).

## 3) Create a Robot API Key (for `X-Api-Key` auth)

Robot agents authenticate to Orchestrator with `X-Api-Key`.

1. Canvas -> **Fleet Dashboard** -> **API Keys**.
2. Select the target robot.
3. Click **Generate**.
4. Copy the generated key immediately (it is shown once).

On the robot machine, set the key (example):

- `CASARE_ORCHESTRATOR_API_KEY=<crpa_...>`

Then restart the Robot Agent.

## 4) Run multiple robots on the same PC

Run multiple Robot Agent processes, each with:
- a different `CASARE_ROBOT_ID`
- a different `CASARE_ORCHESTRATOR_API_KEY`
- optionally different `CASARE_ROBOT_NAME` and capabilities

Note: global environment variables only support one active configuration at a time. For multiple agents on the same PC, prefer launching each agent with its own `.env`/config or its own PowerShell session that sets `$env:...` variables before starting.

Practical approach:
- Create 2+ robots in Canvas (Option B)
- Generate one API key per robot
- Launch one agent per robot with its own environment/config file or `.env`

## 5) Categories: capabilities and tags

In the Robots tab you can model "categories" using:
- **Capabilities**: `browser`, `desktop`, `gpu`, `high_memory`
- **Tags**: supported at the Orchestrator level and in Robot Agent config, but the current Robots "Add/Edit" dialog only edits capabilities.

If you need category routing today, use capabilities as the primary filter.

## 6) Priorities (job submission)

Workflow submission supports a `priority` field:
- `0` = highest
- `20` = lowest

Use higher priority for urgent workflows and lower priority for background workloads.

## 7) Monitoring status and operations

In Canvas -> **Fleet Dashboard**:

- **Robots tab**: shows online/offline/busy state, environment, concurrency, last seen.
- **Jobs tab**: shows running/completed/failed jobs and their status.
- **Schedules tab**: shows scheduled workflows.

### Pause / Resume / Fail

Robot pause/resume/restart controls are not currently implemented end-to-end.

- The Robots table supports **Add/Edit/Delete** and basic status visibility.
- The backend does not currently expose robot pause/resume/restart endpoints.

For "continue/fail" operational control today, use **Jobs** actions instead:

- **Cancel Job** is supported via `POST /api/v1/jobs/{job_id}/cancel`.
- **Retry Job** is supported via `POST /api/v1/jobs/{job_id}/retry` (creates a new job).

If you need "pause robot" semantics right now, the practical workaround is stopping the Robot Agent process to stop taking new jobs.

## Notes (robustness)

- **Database schema drift:** the Orchestrator performs best-effort schema compatibility on startup (adds missing `robot_api_keys` columns like `last_used_ip` / `is_revoked`). If you see 500s mentioning missing columns, restart the Orchestrator after updating, or run `deploy/migrations`.
- **Duplicate robot names:** some databases enforce unique robot names. If you start multiple agents with the same `CASARE_ROBOT_NAME`, the system may auto-suffix the name (for example `Robot-R (b486ee59)`). You can rename robots in the dashboard.
- **Cloudflare tunnel:** start the Orchestrator origin first, then `cloudflared`. A tunnel started before the origin is listening will log `connectex: actively refused`.
