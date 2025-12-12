# Orchestrator REST API Reference

Complete REST API reference for the CasareRPA Orchestrator. The orchestrator manages workflow distribution, robot coordination, and job execution across your RPA fleet.

## Base URL

```
http://localhost:8000/api/v1
```

For production deployments, use HTTPS:
```
https://orchestrator.your-domain.com/api/v1
```

## Authentication

The Orchestrator supports two authentication methods:

### JWT Tokens (Users)

Obtain tokens via the login endpoint, then include in requests:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

Use the access token in subsequent requests:
```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  http://localhost:8000/api/v1/workflows
```

### Robot API Keys

Robots authenticate using API keys with the `crpa_` prefix:

```bash
curl -H "X-Api-Key: crpa_your_api_key_here" \
  http://localhost:8000/api/v1/robots/robot-001/heartbeat
```

## Rate Limiting

All endpoints are rate-limited to prevent abuse. Limits are per IP address:

| Endpoint Category | Limit |
|------------------|-------|
| Authentication | 5/min (lockout after exceed) |
| List endpoints | 100/min |
| Detail endpoints | 200/min |
| Job operations | 60/min |
| Heartbeat/Progress | 600/min |
| Analytics | 20/min |

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests per window
- `X-RateLimit-Remaining`: Requests remaining
- `Retry-After`: Seconds until retry (when limited)

---

## Authentication Endpoints

### POST /auth/login

Authenticate and obtain JWT tokens.

**Rate Limit:** 5 attempts per 5 minutes, then 15-minute lockout.

**Request Body:**
```json
{
  "username": "string",
  "password": "string",
  "tenant_id": "string (optional)"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid credentials
- `429 Too Many Requests` - Rate limit exceeded

**Python Example:**
```python
import httpx
from typing import Optional

async def login(
    base_url: str,
    username: str,
    password: str,
    tenant_id: Optional[str] = None,
) -> dict:
    """Login and obtain JWT tokens."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/api/v1/auth/login",
            json={
                "username": username,
                "password": password,
                "tenant_id": tenant_id,
            },
        )
        response.raise_for_status()
        return response.json()

# Usage
tokens = await login("http://localhost:8000", "admin", "password")
access_token = tokens["access_token"]
```

---

### POST /auth/refresh

Refresh an access token using a refresh token.

**Request Body:**
```json
{
  "refresh_token": "string"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Error Responses:**
- `400 Bad Request` - Invalid token type
- `401 Unauthorized` - Expired or invalid refresh token

---

### POST /auth/logout

Logout and optionally revoke tokens.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200 OK):**
```json
{
  "message": "Successfully logged out"
}
```

---

### GET /auth/me

Get current authenticated user information.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200 OK):**
```json
{
  "user_id": "admin",
  "roles": ["admin", "developer", "operator", "viewer"],
  "tenant_id": "default",
  "dev_mode": false
}
```

---

## Workflow Endpoints

### POST /workflows

Submit a workflow for execution or scheduling.

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "workflow_name": "My Automation Workflow",
  "workflow_json": {
    "nodes": {},
    "connections": [],
    "metadata": {}
  },
  "trigger_type": "manual|scheduled|webhook",
  "execution_mode": "lan|internet",
  "schedule_cron": "0 9 * * 1-5",
  "priority": 10,
  "metadata": {
    "description": "Optional workflow description"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `workflow_name` | string | Yes | Name (1-255 chars) |
| `workflow_json` | object | Yes | Workflow definition with `nodes` key |
| `trigger_type` | string | No | `manual`, `scheduled`, or `webhook` (default: `manual`) |
| `execution_mode` | string | No | `lan` or `internet` (default: `lan`) |
| `schedule_cron` | string | No | Cron expression (required if `trigger_type=scheduled`) |
| `priority` | integer | No | 0-20, lower = higher priority (default: 10) |
| `metadata` | object | No | Additional metadata |

**Response (200 OK):**
```json
{
  "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
  "job_id": "660e8400-e29b-41d4-a716-446655440001",
  "schedule_id": null,
  "status": "success",
  "message": "Workflow submitted and queued for lan execution",
  "created_at": "2025-01-15T10:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid workflow JSON or missing required fields
- `500 Internal Server Error` - Storage or queue failure

**Python Example:**
```python
import httpx
from typing import Any

async def submit_workflow(
    base_url: str,
    access_token: str,
    workflow_name: str,
    workflow_json: dict[str, Any],
    trigger_type: str = "manual",
    priority: int = 10,
) -> dict:
    """Submit a workflow for execution."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/api/v1/workflows",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "workflow_name": workflow_name,
                "workflow_json": workflow_json,
                "trigger_type": trigger_type,
                "priority": priority,
            },
        )
        response.raise_for_status()
        return response.json()

# Usage
result = await submit_workflow(
    base_url="http://localhost:8000",
    access_token=access_token,
    workflow_name="Invoice Processing",
    workflow_json={"nodes": {}, "connections": []},
)
print(f"Job ID: {result['job_id']}")
```

**curl Example:**
```bash
curl -X POST http://localhost:8000/api/v1/workflows \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_name": "My Workflow",
    "workflow_json": {"nodes": {}, "connections": []},
    "trigger_type": "manual"
  }'
```

---

### POST /workflows/upload

Upload a workflow JSON file.

**Headers:** `Authorization: Bearer <access_token>`

**Form Data:**
- `file`: Workflow JSON file (.json extension required)

**Query Parameters:**
- `trigger_type`: `manual`, `scheduled`, or `webhook` (default: `manual`)
- `execution_mode`: `lan` or `internet` (default: `lan`)
- `priority`: 0-20 (default: 10)

**Limits:**
- Maximum file size: 50MB
- Maximum nodes: 1000

**Response (200 OK):** Same as POST /workflows

**curl Example:**
```bash
curl -X POST http://localhost:8000/api/v1/workflows/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@my_workflow.json" \
  -F "trigger_type=manual"
```

---

### GET /workflows/{workflow_id}

Get workflow details by ID.

**Headers:** `Authorization: Bearer <access_token>`

**Path Parameters:**
- `workflow_id`: UUID of the workflow

**Response (200 OK):**
```json
{
  "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
  "workflow_name": "My Automation Workflow",
  "workflow_json": {
    "nodes": {},
    "connections": []
  },
  "version": 1,
  "description": "Optional description",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid UUID format
- `404 Not Found` - Workflow not found

---

### DELETE /workflows/{workflow_id}

Delete a workflow and associated schedules/triggers.

**Headers:** `Authorization: Bearer <access_token>`

**Path Parameters:**
- `workflow_id`: UUID of the workflow

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "Workflow deleted: 550e8400-e29b-41d4-a716-446655440000",
  "deleted_from": {
    "database": true,
    "filesystem": true
  }
}
```

---

## Job Endpoints

### POST /jobs/{job_id}/cancel

Cancel a pending or running job.

**Headers:** `Authorization: Bearer <access_token>`

**Path Parameters:**
- `job_id`: ID of the job to cancel (max 64 chars)

**Rate Limit:** 60 requests/minute

**Response (200 OK):**
```json
{
  "job_id": "job-12345",
  "cancelled": true,
  "previous_status": "running",
  "message": "Job cancelled successfully"
}
```

If job cannot be cancelled:
```json
{
  "job_id": "job-12345",
  "cancelled": false,
  "previous_status": "completed",
  "message": "Job already completed, cannot cancel"
}
```

**Error Responses:**
- `404 Not Found` - Job not found
- `503 Service Unavailable` - Database not available

---

### POST /jobs/{job_id}/retry

Retry a failed or cancelled job.

**Headers:** `Authorization: Bearer <access_token>`

**Path Parameters:**
- `job_id`: ID of the job to retry

**Rate Limit:** 30 requests/minute

> **Note:** Only jobs with status `failed`, `cancelled`, or `timeout` can be retried.

**Response (200 OK):**
```json
{
  "original_job_id": "job-12345",
  "new_job_id": "job-67890",
  "message": "Job queued for retry"
}
```

**Error Responses:**
- `400 Bad Request` - Job status does not allow retry
- `404 Not Found` - Job not found

---

### PUT /jobs/{job_id}/progress

Update job execution progress (used by robot agents).

**Headers:** `X-Api-Key: crpa_...` or `Authorization: Bearer <access_token>`

**Path Parameters:**
- `job_id`: ID of the running job

**Rate Limit:** 600 requests/minute

**Request Body:**
```json
{
  "progress": 75,
  "current_node": "node-456",
  "message": "Processing page 3 of 4"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `progress` | integer | Yes | 0-100 percentage |
| `current_node` | string | No | Currently executing node ID |
| `message` | string | No | Progress message |

**Response (200 OK):**
```json
{
  "job_id": "job-12345",
  "progress": 75,
  "current_node": "node-456"
}
```

---

## Robot Endpoints

### POST /robots/register

Register a new robot or update existing registration.

**Headers:** `X-Api-Key: crpa_...`

**Rate Limit:** 30 requests/minute

**Request Body:**
```json
{
  "robot_id": "robot-prod-001",
  "name": "Production Robot 1",
  "hostname": "robot-server-01.example.com",
  "capabilities": ["browser", "desktop", "high_memory"],
  "environment": "production",
  "max_concurrent_jobs": 3,
  "tags": ["invoice-processing", "high-priority"]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `robot_id` | string | Yes | Unique robot identifier (1-64 chars) |
| `name` | string | Yes | Human-readable name (1-128 chars) |
| `hostname` | string | Yes | Robot hostname/IP (1-256 chars) |
| `capabilities` | array | No | List of capability strings |
| `environment` | string | No | Environment name (default: `default`) |
| `max_concurrent_jobs` | integer | No | 1-100 (default: 1) |
| `tags` | array | No | Tags for filtering |

**Response (200 OK):**
```json
{
  "robot_id": "robot-prod-001",
  "name": "Production Robot 1",
  "hostname": "robot-server-01.example.com",
  "status": "idle",
  "environment": "production",
  "max_concurrent_jobs": 3,
  "capabilities": ["browser", "desktop", "high_memory"],
  "tags": ["invoice-processing", "high-priority"],
  "current_job_ids": [],
  "last_seen": "2025-01-15T10:30:00Z",
  "last_heartbeat": "2025-01-15T10:30:00Z",
  "created_at": "2025-01-15T10:30:00Z",
  "metrics": {}
}
```

---

### GET /robots

List all registered robots with optional filtering.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
- `status`: Filter by status (`idle`, `busy`, `offline`, `error`, `maintenance`)
- `environment`: Filter by environment name
- `limit`: Max results (1-500, default: 100)
- `offset`: Pagination offset (default: 0)

**Rate Limit:** 100 requests/minute

**Response (200 OK):**
```json
{
  "robots": [
    {
      "robot_id": "robot-prod-001",
      "name": "Production Robot 1",
      "hostname": "robot-server-01.example.com",
      "status": "busy",
      "environment": "production",
      "max_concurrent_jobs": 3,
      "capabilities": ["browser", "desktop"],
      "tags": ["invoice-processing"],
      "current_job_ids": ["job-12345"],
      "last_seen": "2025-01-15T10:30:00Z",
      "last_heartbeat": "2025-01-15T10:30:00Z",
      "created_at": "2025-01-15T10:00:00Z",
      "metrics": {"cpu_percent": 45.2, "memory_mb": 1024}
    }
  ],
  "total": 1
}
```

**Python Example:**
```python
async def list_robots(
    base_url: str,
    access_token: str,
    status: str | None = None,
    environment: str | None = None,
) -> dict:
    """List robots with optional filtering."""
    params = {}
    if status:
        params["status"] = status
    if environment:
        params["environment"] = environment

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{base_url}/api/v1/robots",
            headers={"Authorization": f"Bearer {access_token}"},
            params=params,
        )
        response.raise_for_status()
        return response.json()

# Get all idle robots in production
robots = await list_robots(
    base_url="http://localhost:8000",
    access_token=access_token,
    status="idle",
    environment="production",
)
```

---

### GET /robots/{robot_id}

Get detailed information for a specific robot.

**Headers:** `Authorization: Bearer <access_token>`

**Rate Limit:** 200 requests/minute

**Response (200 OK):** Same as robot object in list response.

**Error Responses:**
- `404 Not Found` - Robot not found

---

### PUT /robots/{robot_id}

Update robot configuration.

**Headers:** `Authorization: Bearer <access_token>`

**Rate Limit:** 60 requests/minute

**Request Body (all fields optional):**
```json
{
  "name": "Updated Robot Name",
  "hostname": "new-hostname.example.com",
  "capabilities": ["browser"],
  "environment": "staging",
  "max_concurrent_jobs": 2,
  "tags": ["new-tag"]
}
```

**Response (200 OK):** Updated robot object.

---

### PUT /robots/{robot_id}/status

Update robot status.

**Headers:** `X-Api-Key: crpa_...`

**Rate Limit:** 120 requests/minute

**Request Body:**
```json
{
  "status": "idle|busy|offline|error|maintenance"
}
```

**Response (200 OK):** Updated robot object.

---

### DELETE /robots/{robot_id}

Delete/deregister a robot.

**Headers:** `Authorization: Bearer <access_token>`

**Rate Limit:** 30 requests/minute

**Response (200 OK):**
```json
{
  "deleted": true,
  "robot_id": "robot-prod-001"
}
```

---

### POST /robots/{robot_id}/heartbeat

Record robot heartbeat with optional metrics.

**Headers:** `X-Api-Key: crpa_...`

**Rate Limit:** 600 requests/minute

**Request Body (optional):**
```json
{
  "cpu_percent": 45.2,
  "memory_mb": 1024.5,
  "disk_free_gb": 50.0,
  "active_jobs": 2
}
```

**Response (200 OK):**
```json
{
  "ok": true,
  "timestamp": "2025-01-15T10:30:00Z"
}
```

---

## Schedule Endpoints

### POST /schedules

Create a cron-based workflow schedule.

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
  "schedule_name": "Daily Invoice Processing",
  "cron_expression": "0 9 * * 1-5",
  "enabled": true,
  "priority": 10,
  "execution_mode": "lan",
  "metadata": {
    "workflow_name": "Invoice Processing"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `workflow_id` | string | Yes | UUID of workflow to schedule |
| `schedule_name` | string | Yes | Name (1-255 chars) |
| `cron_expression` | string | Yes | Standard cron expression |
| `enabled` | boolean | No | Active status (default: true) |
| `priority` | integer | No | 0-20 (default: 10) |
| `execution_mode` | string | No | `lan` or `internet` (default: `lan`) |
| `metadata` | object | No | Additional metadata |

**Response (200 OK):**
```json
{
  "schedule_id": "770e8400-e29b-41d4-a716-446655440002",
  "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
  "schedule_name": "Daily Invoice Processing",
  "cron_expression": "0 9 * * 1-5",
  "enabled": true,
  "priority": 10,
  "execution_mode": "lan",
  "next_run": "2025-01-16T09:00:00Z",
  "last_run": null,
  "run_count": 0,
  "failure_count": 0,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

**Cron Expression Examples:**
| Expression | Description |
|-----------|-------------|
| `0 9 * * *` | Every day at 9:00 AM |
| `0 9 * * 1-5` | Weekdays at 9:00 AM |
| `0 */2 * * *` | Every 2 hours |
| `0 0 1 * *` | First day of month at midnight |
| `*/15 * * * *` | Every 15 minutes |

---

### GET /schedules

List all schedules with optional filtering.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
- `workflow_id`: Filter by workflow UUID
- `enabled`: Filter by enabled status (`true`/`false`)
- `limit`: Max results (1-1000, default: 100)

**Response (200 OK):** Array of schedule objects.

---

### GET /schedules/{schedule_id}

Get schedule details.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200 OK):** Schedule object.

---

### PUT /schedules/{schedule_id}/enable

Enable a schedule.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200 OK):** Updated schedule object with `enabled: true` and updated `next_run`.

---

### PUT /schedules/{schedule_id}/disable

Disable a schedule.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200 OK):** Updated schedule object with `enabled: false` and `next_run: null`.

---

### DELETE /schedules/{schedule_id}

Delete a schedule.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "Schedule deleted: 770e8400-e29b-41d4-a716-446655440002"
}
```

---

### PUT /schedules/{schedule_id}/trigger

Trigger a schedule immediately (manual override).

**Headers:** `Authorization: Bearer <access_token>`

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "Schedule triggered: 770e8400-e29b-41d4-a716-446655440002",
  "job_id": "manual_770e8400_abc12345",
  "triggered_via": "apscheduler|direct|event"
}
```

---

### GET /schedules/upcoming

Get upcoming scheduled runs.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
- `limit`: Max results (1-100, default: 20)
- `workflow_id`: Filter by workflow UUID

**Response (200 OK):**
```json
[
  {
    "schedule_id": "770e8400-e29b-41d4-a716-446655440002",
    "schedule_name": "Daily Invoice Processing",
    "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
    "workflow_name": "Invoice Processing",
    "next_run": "2025-01-16T09:00:00Z",
    "type": "cron",
    "status": "active"
  }
]
```

---

## Metrics Endpoints

### GET /metrics/fleet

Get fleet-wide metrics summary.

**Headers:** `Authorization: Bearer <access_token>`

**Rate Limit:** 100 requests/minute

**Response (200 OK):**
```json
{
  "total_robots": 10,
  "active_robots": 8,
  "idle_robots": 5,
  "busy_robots": 3,
  "offline_robots": 2,
  "active_jobs": 3,
  "queue_depth": 15
}
```

---

### GET /metrics/robots

Get robot metrics summary.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
- `status`: Filter by robot status

**Rate Limit:** 100 requests/minute

**Response (200 OK):** Array of robot summaries with metrics.

---

### GET /metrics/robots/{robot_id}

Get detailed metrics for a specific robot.

**Headers:** `Authorization: Bearer <access_token>`

**Rate Limit:** 200 requests/minute

**Response (200 OK):**
```json
{
  "robot_id": "robot-prod-001",
  "name": "Production Robot 1",
  "status": "busy",
  "cpu_percent": 45.2,
  "memory_mb": 1024.5,
  "current_job": "job-12345",
  "jobs_completed_today": 25,
  "jobs_failed_today": 2,
  "avg_job_duration_ms": 45000
}
```

---

### GET /metrics/jobs

Get job execution history.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
- `limit`: Max results (1-500, default: 50)
- `status`: Filter by job status
- `workflow_id`: Filter by workflow
- `robot_id`: Filter by robot

**Rate Limit:** 50 requests/minute

**Response (200 OK):** Array of job summaries.

---

### GET /metrics/jobs/{job_id}

Get detailed job execution information.

**Headers:** `Authorization: Bearer <access_token>`

**Rate Limit:** 200 requests/minute

**Response (200 OK):**
```json
{
  "job_id": "job-12345",
  "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
  "workflow_name": "Invoice Processing",
  "robot_id": "robot-prod-001",
  "status": "completed",
  "progress": 100,
  "started_at": "2025-01-15T10:30:00Z",
  "completed_at": "2025-01-15T10:31:30Z",
  "duration_ms": 90000,
  "error_message": null,
  "node_execution": [
    {
      "node_id": "node-1",
      "status": "completed",
      "duration_ms": 5000
    }
  ]
}
```

---

### GET /metrics/analytics

Get aggregated analytics and statistics.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
- `days`: Analysis period (1-90, default: 7)

**Rate Limit:** 20 requests/minute

**Response (200 OK):**
```json
{
  "success_rate": 95.5,
  "failure_rate": 4.5,
  "duration_p50_ms": 30000,
  "duration_p90_ms": 60000,
  "duration_p99_ms": 120000,
  "slowest_workflows": [
    {
      "workflow_id": "...",
      "workflow_name": "Complex Report",
      "avg_duration_ms": 300000
    }
  ],
  "error_distribution": {
    "SELECTOR_NOT_FOUND": 15,
    "TIMEOUT": 8,
    "NETWORK_ERROR": 3
  },
  "self_healing_success_rate": 78.5
}
```

---

### GET /metrics/activity

Get recent activity events.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
- `limit`: Max events (1-200, default: 50)
- `since`: Only events after this ISO timestamp
- `event_type`: Filter by event type

**Rate Limit:** 60 requests/minute

**Response (200 OK):**
```json
{
  "events": [
    {
      "event_type": "job_completed",
      "timestamp": "2025-01-15T10:31:30Z",
      "data": {
        "job_id": "job-12345",
        "workflow_name": "Invoice Processing"
      }
    }
  ],
  "total": 150
}
```

---

### GET /metrics/prometheus

Get metrics in Prometheus exposition format.

**Query Parameters:**
- `environment`: Environment name for labels (default: `development`)

**Response (200 OK):** Plain text Prometheus format

```
# HELP casare_rpa_jobs_total Total number of jobs
# TYPE casare_rpa_jobs_total counter
casare_rpa_jobs_total{status="completed",environment="development"} 1234
casare_rpa_jobs_total{status="failed",environment="development"} 56

# HELP casare_rpa_robots_active Number of active robots
# TYPE casare_rpa_robots_active gauge
casare_rpa_robots_active{environment="development"} 8
```

**Prometheus Scrape Config:**
```yaml
scrape_configs:
  - job_name: 'casare-rpa'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/api/v1/metrics/prometheus'
```

---

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Human-readable error message"
}
```

| HTTP Code | Description |
|-----------|-------------|
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid or missing credentials |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource does not exist |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server-side failure |
| 503 | Service Unavailable - Database or service down |

---

## Security Considerations

1. **HTTPS Required**: Always use HTTPS in production
2. **Token Expiry**: Access tokens expire in 1 hour, refresh tokens in 7 days
3. **API Key Security**: Robot API keys should be rotated regularly
4. **Rate Limiting**: Implement client-side backoff on 429 responses
5. **Input Validation**: All UUIDs and IDs are validated server-side

---

## Related Documentation

- [WebSocket API Reference](orchestrator-websocket.md) - Real-time updates
- [Event Bus Reference](event-bus.md) - Domain events
- [Robot Setup Guide](../../../user-guide/deployment/robot-setup.md) - Agent configuration
- [Orchestrator Setup Guide](../../../user-guide/deployment/orchestrator-setup.md) - Server deployment
