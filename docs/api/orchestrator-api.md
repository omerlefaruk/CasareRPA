# CasareRPA Orchestrator API Reference

**Version**: 1.0.0
**Base URL**: `http://localhost:8000/api/v1`
**WebSocket URL**: `ws://localhost:8000/ws`

The Orchestrator API provides REST and WebSocket endpoints for submitting workflows, managing schedules, monitoring fleet health, and receiving real-time updates.

---

## Table of Contents

- [Authentication](#authentication)
- [Endpoints Overview](#endpoints-overview)
- [Authentication Endpoints](#authentication-endpoints)
- [Workflow Endpoints](#workflow-endpoints)
- [Schedule Endpoints](#schedule-endpoints)
- [Metrics Endpoints](#metrics-endpoints)
- [WebSocket Endpoints](#websocket-endpoints)
- [Health Endpoints](#health-endpoints)
- [Rate Limiting](#rate-limiting)

---

## Authentication

The API supports two authentication methods:

### JWT Authentication (Dashboard Users)

For web dashboard access. Include the Bearer token in the Authorization header:

```
Authorization: Bearer <access_token>
```

**Token Lifecycle**:
- Access token expires in 60 minutes (configurable via `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`)
- Refresh token expires in 7 days (configurable via `JWT_REFRESH_TOKEN_EXPIRE_DAYS`)

**Roles**:
- `admin` - Full access to all endpoints
- `developer` - Create/modify workflows and schedules
- `operator` - Execute workflows, view metrics
- `viewer` - Read-only access to metrics

### Robot API Token Authentication

For robot-to-orchestrator connections. Include the token in the `X-Api-Token` header:

```
X-Api-Token: <robot_api_token>
```

**Configuration**:
```bash
ROBOT_AUTH_ENABLED=true
ROBOT_TOKENS=robot-001:sha256hash1,robot-002:sha256hash2
```

### Development Mode

Set `JWT_DEV_MODE=true` to bypass authentication for testing. All requests receive admin privileges.

> **Warning:** Never enable dev mode in production.

---

## Endpoints Overview

| Category | Method | Endpoint | Description |
|----------|--------|----------|-------------|
| Auth | POST | `/auth/login` | Login with credentials |
| Auth | POST | `/auth/refresh` | Refresh access token |
| Auth | POST | `/auth/logout` | Logout (revoke tokens) |
| Auth | GET | `/auth/me` | Get current user info |
| Workflows | POST | `/workflows` | Submit workflow |
| Workflows | POST | `/workflows/upload` | Upload workflow JSON file |
| Workflows | GET | `/workflows/{workflow_id}` | Get workflow details |
| Workflows | DELETE | `/workflows/{workflow_id}` | Delete workflow |
| Schedules | POST | `/schedules` | Create schedule |
| Schedules | GET | `/schedules` | List schedules |
| Schedules | GET | `/schedules/{schedule_id}` | Get schedule details |
| Schedules | PUT | `/schedules/{schedule_id}/enable` | Enable schedule |
| Schedules | PUT | `/schedules/{schedule_id}/disable` | Disable schedule |
| Schedules | PUT | `/schedules/{schedule_id}/trigger` | Trigger schedule now |
| Schedules | DELETE | `/schedules/{schedule_id}` | Delete schedule |
| Metrics | GET | `/metrics/fleet` | Fleet-wide metrics |
| Metrics | GET | `/metrics/robots` | List all robots |
| Metrics | GET | `/metrics/robots/{robot_id}` | Robot details |
| Metrics | GET | `/metrics/jobs` | Job history |
| Metrics | GET | `/metrics/jobs/{job_id}` | Job details |
| Metrics | GET | `/metrics/analytics` | Analytics summary |
| Metrics | GET | `/metrics/activity` | Activity feed |
| WebSocket | WS | `/ws/live-jobs` | Real-time job updates |
| WebSocket | WS | `/ws/robot-status` | Robot heartbeats |
| WebSocket | WS | `/ws/queue-metrics` | Queue depth updates |
| Health | GET | `/health` | Basic health check |
| Health | GET | `/health/detailed` | Detailed health with dependencies |
| Health | GET | `/health/ready` | Kubernetes readiness probe |
| Health | GET | `/health/live` | Kubernetes liveness probe |

---

## Authentication Endpoints

### POST /auth/login

Authenticate user and receive JWT tokens.

**Request Body**:
```json
{
  "username": "admin",
  "password": "secret",
  "tenant_id": "optional-tenant-id"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**curl Example**:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "secret"}'
```

**Python Example**:
```python
import httpx

async def login(username: str, password: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/auth/login",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        return response.json()
```

---

### POST /auth/refresh

Refresh access token using refresh token.

**Request Body**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Error Responses**:
- `400 Bad Request` - Invalid token type (not a refresh token)
- `401 Unauthorized` - Token expired or invalid

---

### POST /auth/logout

Logout user (requires authentication).

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "message": "Successfully logged out"
}
```

---

### GET /auth/me

Get current authenticated user information.

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "user_id": "admin",
  "roles": ["admin", "developer", "operator", "viewer"],
  "tenant_id": null,
  "dev_mode": false
}
```

---

## Workflow Endpoints

### POST /workflows

Submit a workflow for execution.

**Request Body**:
```json
{
  "workflow_name": "My Workflow",
  "workflow_json": {
    "nodes": [
      {"id": "start", "type": "StartNode"},
      {"id": "end", "type": "EndNode"}
    ],
    "connections": []
  },
  "trigger_type": "manual",
  "execution_mode": "lan",
  "schedule_cron": null,
  "priority": 10,
  "metadata": {
    "description": "Example workflow"
  }
}
```

**Parameters**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `workflow_name` | string | Yes | Workflow name (1-255 chars) |
| `workflow_json` | object | Yes | Workflow graph definition with `nodes` key |
| `trigger_type` | string | No | `manual`, `scheduled`, or `webhook` (default: `manual`) |
| `execution_mode` | string | No | `lan` or `internet` (default: `lan`) |
| `schedule_cron` | string | No | Cron expression if trigger_type=scheduled |
| `priority` | integer | No | 0-20, 0=highest (default: 10) |
| `metadata` | object | No | Additional metadata |

**Response** (200 OK):
```json
{
  "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
  "job_id": "660e8400-e29b-41d4-a716-446655440001",
  "schedule_id": null,
  "status": "success",
  "message": "Workflow submitted and queued for lan execution",
  "created_at": "2025-12-01T10:30:00Z"
}
```

**curl Example**:
```bash
curl -X POST http://localhost:8000/api/v1/workflows \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "workflow_name": "Web Scraper",
    "workflow_json": {"nodes": [{"id": "1", "type": "StartNode"}]},
    "trigger_type": "manual",
    "priority": 5
  }'
```

**Python Example**:
```python
import httpx
from typing import Any

async def submit_workflow(
    token: str,
    workflow_name: str,
    workflow_json: dict[str, Any],
    priority: int = 10
) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/workflows",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "workflow_name": workflow_name,
                "workflow_json": workflow_json,
                "trigger_type": "manual",
                "priority": priority,
            }
        )
        response.raise_for_status()
        return response.json()
```

**Security Limits**:
- Max payload size: 10MB
- Max nodes per workflow: 1000

---

### POST /workflows/upload

Upload workflow as JSON file.

**Form Data**:
- `file`: JSON file (required, .json extension, max 50MB)
- `trigger_type`: string (optional, default: `manual`)
- `execution_mode`: string (optional, default: `lan`)
- `priority`: integer (optional, default: 10)

**Response**: Same as POST /workflows

**curl Example**:
```bash
curl -X POST http://localhost:8000/api/v1/workflows/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@my_workflow.json" \
  -F "trigger_type=manual" \
  -F "priority=5"
```

---

### GET /workflows/{workflow_id}

Get workflow details by ID.

**Path Parameters**:
- `workflow_id`: Workflow UUID

**Response** (200 OK):
```json
{
  "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
  "workflow_name": "My Workflow",
  "workflow_json": {"nodes": [], "connections": []},
  "version": 1,
  "description": "Example workflow",
  "created_at": "2025-12-01T10:30:00Z",
  "updated_at": "2025-12-01T10:30:00Z"
}
```

**Error Responses**:
- `404 Not Found` - Workflow not found

---

### DELETE /workflows/{workflow_id}

Delete a workflow.

**Path Parameters**:
- `workflow_id`: Workflow UUID

**Response** (200 OK):
```json
{
  "status": "success",
  "message": "Workflow deleted: 550e8400-e29b-41d4-a716-446655440000"
}
```

---

## Schedule Endpoints

### POST /schedules

Create a cron-based workflow schedule.

**Request Body**:
```json
{
  "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
  "schedule_name": "Daily Report",
  "cron_expression": "0 9 * * 1-5",
  "enabled": true,
  "priority": 10,
  "execution_mode": "lan",
  "metadata": {}
}
```

**Parameters**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `workflow_id` | string | Yes | Workflow to schedule |
| `schedule_name` | string | Yes | Schedule name (1-255 chars) |
| `cron_expression` | string | Yes | Cron expression (e.g., `0 9 * * 1-5`) |
| `enabled` | boolean | No | Enable immediately (default: true) |
| `priority` | integer | No | 0-20 (default: 10) |
| `execution_mode` | string | No | `lan` or `internet` (default: `lan`) |

**Response** (200 OK):
```json
{
  "schedule_id": "770e8400-e29b-41d4-a716-446655440002",
  "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
  "schedule_name": "Daily Report",
  "cron_expression": "0 9 * * 1-5",
  "enabled": true,
  "priority": 10,
  "execution_mode": "lan",
  "next_run": "2025-12-02T09:00:00Z",
  "last_run": null,
  "run_count": 0,
  "failure_count": 0,
  "created_at": "2025-12-01T10:30:00Z",
  "updated_at": "2025-12-01T10:30:00Z"
}
```

**curl Example**:
```bash
curl -X POST http://localhost:8000/api/v1/schedules \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
    "schedule_name": "Hourly Sync",
    "cron_expression": "0 * * * *"
  }'
```

---

### GET /schedules

List all schedules with optional filtering.

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `workflow_id` | string | Filter by workflow ID |
| `enabled` | boolean | Filter by enabled status |
| `limit` | integer | Max results (1-1000, default: 100) |

**Response** (200 OK):
```json
[
  {
    "schedule_id": "770e8400-e29b-41d4-a716-446655440002",
    "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
    "schedule_name": "Daily Report",
    "cron_expression": "0 9 * * 1-5",
    "enabled": true,
    "priority": 10,
    "execution_mode": "lan",
    "next_run": "2025-12-02T09:00:00Z",
    "last_run": null,
    "run_count": 0,
    "failure_count": 0,
    "created_at": "2025-12-01T10:30:00Z",
    "updated_at": "2025-12-01T10:30:00Z"
  }
]
```

---

### GET /schedules/{schedule_id}

Get schedule details by ID.

**Response**: Same structure as individual schedule in list response.

---

### PUT /schedules/{schedule_id}/enable

Enable a disabled schedule.

**Response**: Updated schedule object.

---

### PUT /schedules/{schedule_id}/disable

Disable a schedule.

**Response**: Updated schedule object.

---

### PUT /schedules/{schedule_id}/trigger

Manually trigger a schedule execution immediately.

**Response** (200 OK):
```json
{
  "status": "success",
  "message": "Schedule triggered: 770e8400-e29b-41d4-a716-446655440002",
  "job_id": "880e8400-e29b-41d4-a716-446655440003"
}
```

---

### DELETE /schedules/{schedule_id}

Delete a schedule.

**Response** (200 OK):
```json
{
  "status": "success",
  "message": "Schedule deleted: 770e8400-e29b-41d4-a716-446655440002"
}
```

---

## Metrics Endpoints

### GET /metrics/fleet

Get fleet-wide metrics summary.

**Rate Limit**: 100 requests/minute per IP

**Response** (200 OK):
```json
{
  "total_robots": 10,
  "active_robots": 3,
  "idle_robots": 5,
  "offline_robots": 2,
  "total_jobs_today": 156,
  "active_jobs": 3,
  "queue_depth": 12,
  "average_job_duration_seconds": 45.5
}
```

**curl Example**:
```bash
curl http://localhost:8000/api/v1/metrics/fleet \
  -H "Authorization: Bearer $TOKEN"
```

---

### GET /metrics/robots

List all robots with optional status filter.

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter: `idle`, `busy`, `offline` |

**Rate Limit**: 100 requests/minute per IP

**Response** (200 OK):
```json
[
  {
    "robot_id": "robot-001",
    "hostname": "desktop-abc123",
    "status": "busy",
    "cpu_percent": 45.2,
    "memory_mb": 1024.5,
    "current_job_id": "job-123",
    "last_heartbeat": "2025-12-01T10:30:00Z"
  }
]
```

---

### GET /metrics/robots/{robot_id}

Get detailed metrics for a single robot.

**Path Parameters**:
- `robot_id`: Robot identifier (alphanumeric, underscore, hyphen, max 64 chars)

**Rate Limit**: 200 requests/minute per IP

**Response** (200 OK):
```json
{
  "robot_id": "robot-001",
  "hostname": "desktop-abc123",
  "status": "busy",
  "cpu_percent": 45.2,
  "memory_mb": 1024.5,
  "memory_percent": 65.3,
  "current_job_id": "job-123",
  "last_heartbeat": "2025-12-01T10:30:00Z",
  "jobs_completed_today": 42,
  "jobs_failed_today": 2,
  "average_job_duration_seconds": 38.5
}
```

---

### GET /metrics/jobs

Get job execution history.

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | integer | Max results (1-500, default: 50) |
| `status` | string | Filter: `pending`, `claimed`, `completed`, `failed` |
| `workflow_id` | string | Filter by workflow ID |
| `robot_id` | string | Filter by robot ID |

**Rate Limit**: 50 requests/minute per IP

**Response** (200 OK):
```json
[
  {
    "job_id": "job-123",
    "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
    "workflow_name": "Daily Report",
    "robot_id": "robot-001",
    "status": "completed",
    "created_at": "2025-12-01T10:00:00Z",
    "completed_at": "2025-12-01T10:01:30Z",
    "duration_ms": 90000
  }
]
```

---

### GET /metrics/jobs/{job_id}

Get detailed job execution information.

**Rate Limit**: 200 requests/minute per IP

**Response** (200 OK):
```json
{
  "job_id": "job-123",
  "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
  "workflow_name": "Daily Report",
  "robot_id": "robot-001",
  "status": "completed",
  "created_at": "2025-12-01T10:00:00Z",
  "claimed_at": "2025-12-01T10:00:05Z",
  "completed_at": "2025-12-01T10:01:30Z",
  "duration_ms": 90000,
  "error_message": null,
  "error_type": null,
  "retry_count": 0,
  "node_executions": [
    {"node_id": "start", "duration_ms": 5, "status": "completed"},
    {"node_id": "scrape", "duration_ms": 85000, "status": "completed"}
  ]
}
```

---

### GET /metrics/analytics

Get aggregated analytics and statistics.

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `days` | integer | Number of days (1-90, default: 7) |

**Rate Limit**: 20 requests/minute per IP

**Response** (200 OK):
```json
{
  "total_jobs": 1247,
  "success_rate": 94.5,
  "failure_rate": 5.5,
  "average_duration_ms": 45000,
  "p50_duration_ms": 38000,
  "p90_duration_ms": 95000,
  "p99_duration_ms": 180000,
  "slowest_workflows": [
    {"workflow_id": "wf-1", "workflow_name": "Heavy Report", "average_duration_ms": 120000}
  ],
  "error_distribution": [
    {"error_type": "TimeoutError", "count": 23},
    {"error_type": "SelectorNotFound", "count": 12}
  ],
  "self_healing_success_rate": 85.5
}
```

---

### GET /metrics/activity

Get activity feed for dashboard.

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | integer | Max events (1-200, default: 50) |
| `since` | datetime | Events after this timestamp (ISO format) |
| `event_type` | string | Filter: `job_started`, `job_completed`, `job_failed`, `robot_online`, `robot_offline`, `schedule_triggered` |

**Rate Limit**: 60 requests/minute per IP

**Response** (200 OK):
```json
{
  "events": [
    {
      "id": "evt-001",
      "type": "job_completed",
      "timestamp": "2025-12-01T10:30:00Z",
      "title": "Job completed successfully",
      "details": "Daily Report finished in 90s",
      "robot_id": "robot-001",
      "job_id": "job-123"
    }
  ],
  "total": 156
}
```

---

## WebSocket Endpoints

### WS /ws/live-jobs

Real-time job status updates.

**Connection**:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/live-jobs');
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log(`Job ${update.job_id}: ${update.status}`);
};
```

**Message Format** (Server to Client):
```json
{
  "job_id": "job-123",
  "status": "completed",
  "timestamp": "2025-12-01T10:30:00Z"
}
```

**Keep-Alive**: Send `ping` to receive `pong`.

**Python Example**:
```python
import asyncio
import websockets
import json

async def monitor_jobs():
    async with websockets.connect("ws://localhost:8000/ws/live-jobs") as ws:
        async def send_pings():
            while True:
                await ws.send("ping")
                await asyncio.sleep(30)

        asyncio.create_task(send_pings())

        async for message in ws:
            if message != "pong":
                update = json.loads(message)
                print(f"Job {update['job_id']}: {update['status']}")
```

---

### WS /ws/robot-status

Robot heartbeat stream (every 5-10 seconds).

**Message Format**:
```json
{
  "robot_id": "robot-001",
  "status": "busy",
  "cpu_percent": 45.2,
  "memory_mb": 1024.5,
  "timestamp": "2025-12-01T10:30:00Z"
}
```

---

### WS /ws/queue-metrics

Queue depth updates (every 5 seconds).

**Message Format**:
```json
{
  "depth": 42,
  "timestamp": "2025-12-01T10:30:00Z"
}
```

---

## Health Endpoints

### GET /health

Basic health check for load balancers.

**Response** (200 OK):
```json
{
  "status": "healthy",
  "service": "casare-rpa-monitoring"
}
```

---

### GET /health/detailed

Detailed health check including dependencies.

**Response** (200 OK):
```json
{
  "status": "healthy",
  "service": "casare-rpa-monitoring",
  "dependencies": {
    "database": {
      "healthy": true,
      "pool_size": 10,
      "pool_free": 8,
      "error": null
    }
  }
}
```

**Degraded Response** (200 OK with `status: degraded`):
```json
{
  "status": "degraded",
  "service": "casare-rpa-monitoring",
  "dependencies": {
    "database": {
      "healthy": false,
      "pool_size": 0,
      "pool_free": 0,
      "error": "Connection refused"
    }
  }
}
```

---

### GET /health/ready

Kubernetes readiness probe. Returns 200 only if all critical dependencies are healthy.

**Response** (200 OK):
```json
{
  "ready": true
}
```

**Not Ready**:
```json
{
  "ready": false,
  "reason": "Database unhealthy"
}
```

---

### GET /health/live

Kubernetes liveness probe. Returns 200 if process is alive.

**Response** (200 OK):
```json
{
  "alive": true
}
```

---

## Rate Limiting

Rate limits are enforced per IP address using the `slowapi` library.

| Endpoint | Limit |
|----------|-------|
| `/metrics/fleet` | 100/minute |
| `/metrics/robots` | 100/minute |
| `/metrics/robots/{id}` | 200/minute |
| `/metrics/jobs` | 50/minute |
| `/metrics/jobs/{id}` | 200/minute |
| `/metrics/analytics` | 20/minute |
| `/metrics/activity` | 60/minute |

**Rate Limit Headers**:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1701432000
```

**429 Too Many Requests**:
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 60
}
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET_KEY` | (required) | JWT signing secret |
| `JWT_ALGORITHM` | HS256 | JWT algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | 60 | Access token TTL |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | 7 | Refresh token TTL |
| `JWT_DEV_MODE` | false | Bypass auth for testing |
| `ROBOT_AUTH_ENABLED` | false | Enable robot token auth |
| `ROBOT_TOKENS` | - | robot-id:hash pairs |
| `DB_ENABLED` | true | Enable database |
| `WORKFLOWS_DIR` | ./workflows | Workflow file storage |
| `WORKFLOW_BACKUP_ENABLED` | true | Enable filesystem backup |
| `USE_MEMORY_QUEUE` | false | Use in-memory queue |

---

## Error Response Format

All API errors follow this structure:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common HTTP status codes:
- `400 Bad Request` - Invalid request body or parameters
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `413 Payload Too Large` - Request body exceeds limits
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server-side error
- `501 Not Implemented` - Feature not yet implemented

See [Error Codes Reference](./error-codes.md) for detailed error handling.
