# CasareRPA WebSocket Contract

## Overview

The CasareRPA Orchestrator uses WebSockets for real-time bidirectional communication between:
- **Robots** ↔ **Orchestrator**: Job execution, heartbeats, logs
- **Dashboard** ↔ **Orchestrator**: Live monitoring, status updates

All WebSocket endpoints are served by a **single unified FastAPI application** at the orchestrator URL.

---

## Authentication

All WebSocket connections require authentication via **query parameters**:

| Endpoint Type | Auth Parameter | Value |
|---------------|----------------|-------|
| Robot connections | `api_key` | Robot API key (`crpa_xxxxx`) |
| Admin/Dashboard | `api_secret` | Admin secret key |
| Monitoring streams | `token` | JWT token or Robot API key |

**Example URLs:**
```
ws://orchestrator:8000/ws/robot/robot-123?api_key=crpa_abc123...
ws://orchestrator:8000/ws/admin?api_secret=your-admin-secret
ws://orchestrator:8000/ws/monitoring/live-jobs?token=eyJhbG...
```

---

## Endpoint Reference

### Robot Endpoints (`/ws/*`)

#### `/ws/robot/{robot_id}`
Robot ↔ Orchestrator bidirectional channel.

**Auth:** `api_key` query parameter

**Inbound Messages (Robot → Orchestrator):**

```json
{
  "type": "heartbeat",
  "payload": {
    "robot_id": "robot-123",
    "status": "idle|busy|offline",
    "cpu_percent": 45.2,
    "memory_mb": 1024,
    "timestamp": "2025-12-22T14:30:00Z"
  }
}
```

```json
{
  "type": "job_status",
  "payload": {
    "job_id": "job-abc123",
    "status": "claimed|running|completed|failed",
    "progress": 75,
    "message": "Processing step 3/4",
    "timestamp": "2025-12-22T14:30:00Z"
  }
}
```

```json
{
  "type": "log",
  "payload": {
    "robot_id": "robot-123",
    "level": "INFO|DEBUG|WARNING|ERROR",
    "message": "Log message text",
    "timestamp": "2025-12-22T14:30:00Z",
    "job_id": "job-abc123"
  }
}
```

**Outbound Messages (Orchestrator → Robot):**

```json
{
  "type": "job_assign",
  "payload": {
    "job_id": "job-abc123",
    "workflow_id": "workflow-xyz",
    "priority": 5,
    "parameters": { ... },
    "timeout_seconds": 3600
  }
}
```

```json
{
  "type": "job_cancel",
  "payload": {
    "job_id": "job-abc123",
    "reason": "User requested cancellation"
  }
}
```

```json
{
  "type": "ping",
  "payload": {
    "timestamp": "2025-12-22T14:30:00Z"
  }
}
```

---

#### `/ws/admin`
Admin dashboard bidirectional channel.

**Auth:** `api_secret` query parameter

**Inbound Messages (Dashboard → Orchestrator):**

```json
{
  "type": "subscribe",
  "payload": {
    "channels": ["robots", "jobs", "queue"]
  }
}
```

```json
{
  "type": "command",
  "payload": {
    "action": "cancel_job|restart_robot|pause_queue",
    "target_id": "job-abc123"
  }
}
```

**Outbound Messages (Orchestrator → Dashboard):**

```json
{
  "type": "robot_status",
  "payload": {
    "robot_id": "robot-123",
    "status": "idle|busy|offline",
    "cpu_percent": 45.2,
    "memory_mb": 1024,
    "current_job": "job-abc123",
    "timestamp": "2025-12-22T14:30:00Z"
  }
}
```

```json
{
  "type": "job_update",
  "payload": {
    "job_id": "job-abc123",
    "status": "pending|claimed|running|completed|failed",
    "robot_id": "robot-123",
    "progress": 75,
    "timestamp": "2025-12-22T14:30:00Z"
  }
}
```

```json
{
  "type": "queue_metrics",
  "payload": {
    "pending": 42,
    "running": 5,
    "completed_24h": 156,
    "failed_24h": 3,
    "timestamp": "2025-12-22T14:30:00Z"
  }
}
```

---

#### `/ws/logs/{robot_id}`
Stream logs from a specific robot.

**Auth:** `api_secret` query parameter

**Query Parameters:**
- `min_level`: Minimum log level to stream (`DEBUG`, `INFO`, `WARNING`, `ERROR`)

**Outbound Messages (Orchestrator → Dashboard):**

```json
{
  "type": "log",
  "payload": {
    "robot_id": "robot-123",
    "level": "INFO",
    "message": "Starting workflow execution",
    "timestamp": "2025-12-22T14:30:00.123Z",
    "job_id": "job-abc123",
    "node_id": "node-xyz"
  }
}
```

---

#### `/ws/logs`
Stream all logs (admin view).

**Auth:** `api_secret` query parameter

**Query Parameters:**
- `tenant_id`: Filter by tenant (optional)
- `min_level`: Minimum log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`)

Same message format as `/ws/logs/{robot_id}`.

---

### Monitoring Endpoints (`/ws/monitoring/*`)

These endpoints provide lightweight, focused streams for dashboard widgets.

#### `/ws/monitoring/live-jobs`
Real-time job status updates.

**Auth:** `token` query parameter (JWT or API key)

**Outbound Messages:**

```json
{
  "type": "job_update",
  "job_id": "job-abc123",
  "status": "completed",
  "timestamp": "2025-12-22T14:30:00Z"
}
```

---

#### `/ws/monitoring/robot-status`
Robot heartbeat stream.

**Auth:** `token` query parameter

**Outbound Messages (every 5 seconds):**

```json
{
  "type": "robot_heartbeat",
  "robot_id": "robot-123",
  "status": "idle",
  "cpu_percent": 45.2,
  "memory_mb": 1024.5,
  "timestamp": "2025-12-22T14:30:00Z"
}
```

---

#### `/ws/monitoring/queue-metrics`
Queue depth updates.

**Auth:** `token` query parameter

**Outbound Messages (every 5 seconds):**

```json
{
  "type": "queue_metrics",
  "depth": 42,
  "timestamp": "2025-12-22T14:30:00Z"
}
```

---

## Error Handling

All endpoints use a consistent error message format:

```json
{
  "type": "error",
  "payload": {
    "code": "AUTH_FAILED|INVALID_MESSAGE|RATE_LIMITED|INTERNAL_ERROR",
    "message": "Human-readable error description",
    "timestamp": "2025-12-22T14:30:00Z"
  }
}
```

**Error Codes:**
- `AUTH_FAILED`: Invalid or missing authentication
- `INVALID_MESSAGE`: Malformed message payload
- `RATE_LIMITED`: Too many messages (slow down)
- `INTERNAL_ERROR`: Server-side error

---

## Connection Lifecycle

### Robot Connection

1. **Connect** with `api_key` in query string
2. **Authenticate** (server validates API key, sends `connected` message)
3. **Heartbeat** every 30 seconds (robot → orchestrator)
4. **Receive jobs** when available (orchestrator → robot)
5. **Send job updates** during execution (robot → orchestrator)
6. **Reconnect** on disconnect with exponential backoff

### Dashboard Connection

1. **Connect** with `api_secret` or `token` in query string
2. **Subscribe** to desired channels
3. **Receive updates** for subscribed channels
4. **Send commands** as needed (cancel jobs, etc.)
5. **Handle disconnection** gracefully

---

## Rate Limits

| Endpoint | Max Messages/sec | Burst |
|----------|------------------|-------|
| Robot connections | 100 | 200 |
| Admin connections | 200 | 500 |
| Monitoring streams | 50 | 100 |

Exceeding limits results in `RATE_LIMITED` error and temporary slowdown.

---

## Client Libraries

**Python (Robot):**
```python
from casare_rpa.infrastructure.orchestrator.communication.websocket_client import (
    OrchestratorWebSocketClient,
)

client = OrchestratorWebSocketClient(
    robot_id="robot-123",
    api_key="crpa_abc123...",
    orchestrator_url="ws://localhost:8000",
)
await client.connect()
await client.send_heartbeat()
```

**TypeScript (Dashboard):**
```typescript
const ws = new WebSocket(
  'ws://localhost:8000/ws/monitoring/live-jobs?token=' + authToken
);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'job_update') {
    updateJobStatus(data.job_id, data.status);
  }
};
```

---

## Server Implementation

All WebSocket endpoints are implemented in the unified FastAPI application:

```
src/casare_rpa/infrastructure/orchestrator/
├── server.py                 # FastAPI app factory
├── websocket_handlers.py     # Robot/Admin/Logs WS endpoints (/ws/*)
└── api/routers/
    └── websockets.py         # Monitoring WS endpoints (/ws/monitoring/*)
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-22 | Initial unified contract |
