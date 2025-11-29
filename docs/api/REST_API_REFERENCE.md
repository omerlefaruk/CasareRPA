# CasareRPA API Reference

This document provides complete API reference for the CasareRPA platform, including WebSocket protocols and REST endpoints.

## Table of Contents

1. [Overview](#overview)
2. [WebSocket Protocol](#websocket-protocol)
3. [Orchestrator API](#orchestrator-api)
4. [Trigger Webhook API](#trigger-webhook-api)
5. [Data Models](#data-models)
6. [Error Handling](#error-handling)

---

## Overview

CasareRPA uses a hybrid communication model:

| Protocol | Purpose | Port |
|----------|---------|------|
| WebSocket | Robot-Orchestrator communication | 8765 |
| HTTP | Trigger webhooks | 8766 |
| Supabase Realtime | Progress updates | Cloud |

### Authentication

All connections require authentication:

```
API Key: Bearer token in Authorization header
WebSocket: Token in registration message
```

---

## WebSocket Protocol

### Connection URL

```
ws://orchestrator-host:8765
```

### Message Format

All messages follow this JSON structure:

```json
{
  "type": "message_type",
  "id": "uuid-v4",
  "timestamp": "2024-01-15T10:30:00Z",
  "payload": {},
  "correlation_id": "request-uuid"
}
```

### Message Types

#### Connection Messages

##### REGISTER

Robot registration with the orchestrator.

**Direction:** Robot -> Orchestrator

```json
{
  "type": "register",
  "id": "msg-uuid",
  "timestamp": "2024-01-15T10:30:00Z",
  "payload": {
    "robot_id": "robot-uuid",
    "robot_name": "Production Robot 1",
    "environment": "production",
    "max_concurrent_jobs": 3,
    "tags": ["browser", "desktop"],
    "capabilities": {
      "playwright": true,
      "uiautomation": true,
      "office": false
    }
  }
}
```

##### REGISTER_ACK

Registration acknowledgment.

**Direction:** Orchestrator -> Robot

```json
{
  "type": "register_ack",
  "id": "msg-uuid",
  "timestamp": "2024-01-15T10:30:01Z",
  "payload": {
    "robot_id": "robot-uuid",
    "success": true,
    "message": "Registration successful",
    "config": {
      "heartbeat_interval": 30,
      "log_batch_size": 100
    }
  },
  "correlation_id": "original-register-msg-id"
}
```

##### HEARTBEAT

Periodic health check from robot.

**Direction:** Robot -> Orchestrator

```json
{
  "type": "heartbeat",
  "id": "msg-uuid",
  "timestamp": "2024-01-15T10:31:00Z",
  "payload": {
    "robot_id": "robot-uuid",
    "status": "online",
    "current_jobs": 2,
    "cpu_percent": 45.2,
    "memory_percent": 68.5,
    "disk_percent": 35.0,
    "active_job_ids": ["job-1-uuid", "job-2-uuid"]
  }
}
```

##### HEARTBEAT_ACK

Heartbeat acknowledgment.

**Direction:** Orchestrator -> Robot

```json
{
  "type": "heartbeat_ack",
  "id": "msg-uuid",
  "timestamp": "2024-01-15T10:31:00Z",
  "payload": {
    "robot_id": "robot-uuid"
  },
  "correlation_id": "heartbeat-msg-id"
}
```

##### DISCONNECT

Graceful disconnection notification.

**Direction:** Robot -> Orchestrator

```json
{
  "type": "disconnect",
  "id": "msg-uuid",
  "timestamp": "2024-01-15T10:32:00Z",
  "payload": {
    "robot_id": "robot-uuid",
    "reason": "Scheduled maintenance"
  }
}
```

---

#### Job Management Messages

##### JOB_ASSIGN

Assign a job to a robot.

**Direction:** Orchestrator -> Robot

```json
{
  "type": "job_assign",
  "id": "msg-uuid",
  "timestamp": "2024-01-15T10:30:00Z",
  "payload": {
    "job_id": "job-uuid",
    "workflow_id": "workflow-uuid",
    "workflow_name": "Customer Data Extraction",
    "workflow_json": "{...serialized workflow...}",
    "priority": 2,
    "timeout_seconds": 3600,
    "parameters": {
      "customer_id": "CUST-001",
      "date_range": "2024-01"
    }
  }
}
```

##### JOB_ACCEPT

Robot accepts the job assignment.

**Direction:** Robot -> Orchestrator

```json
{
  "type": "job_accept",
  "id": "msg-uuid",
  "timestamp": "2024-01-15T10:30:01Z",
  "payload": {
    "job_id": "job-uuid",
    "robot_id": "robot-uuid"
  },
  "correlation_id": "job-assign-msg-id"
}
```

##### JOB_REJECT

Robot rejects the job assignment.

**Direction:** Robot -> Orchestrator

```json
{
  "type": "job_reject",
  "id": "msg-uuid",
  "timestamp": "2024-01-15T10:30:01Z",
  "payload": {
    "job_id": "job-uuid",
    "robot_id": "robot-uuid",
    "reason": "At maximum capacity"
  },
  "correlation_id": "job-assign-msg-id"
}
```

##### JOB_PROGRESS

Job execution progress update.

**Direction:** Robot -> Orchestrator

```json
{
  "type": "job_progress",
  "id": "msg-uuid",
  "timestamp": "2024-01-15T10:35:00Z",
  "payload": {
    "job_id": "job-uuid",
    "robot_id": "robot-uuid",
    "progress": 45,
    "current_node": "extract_data_node",
    "message": "Extracting customer records..."
  }
}
```

##### JOB_COMPLETE

Job completed successfully.

**Direction:** Robot -> Orchestrator

```json
{
  "type": "job_complete",
  "id": "msg-uuid",
  "timestamp": "2024-01-15T10:45:00Z",
  "payload": {
    "job_id": "job-uuid",
    "robot_id": "robot-uuid",
    "result": {
      "records_processed": 1500,
      "output_file": "/output/customers_2024-01.csv"
    },
    "duration_ms": 900000
  }
}
```

##### JOB_FAILED

Job execution failed.

**Direction:** Robot -> Orchestrator

```json
{
  "type": "job_failed",
  "id": "msg-uuid",
  "timestamp": "2024-01-15T10:40:00Z",
  "payload": {
    "job_id": "job-uuid",
    "robot_id": "robot-uuid",
    "error_message": "Element not found: #submit-button",
    "error_type": "ElementNotFoundError",
    "stack_trace": "...",
    "failed_node": "click_submit_node"
  }
}
```

##### JOB_CANCEL

Cancel a running job.

**Direction:** Orchestrator -> Robot

```json
{
  "type": "job_cancel",
  "id": "msg-uuid",
  "timestamp": "2024-01-15T10:38:00Z",
  "payload": {
    "job_id": "job-uuid",
    "reason": "Cancelled by user"
  }
}
```

##### JOB_CANCELLED

Job cancellation confirmation.

**Direction:** Robot -> Orchestrator

```json
{
  "type": "job_cancelled",
  "id": "msg-uuid",
  "timestamp": "2024-01-15T10:38:01Z",
  "payload": {
    "job_id": "job-uuid",
    "robot_id": "robot-uuid"
  },
  "correlation_id": "job-cancel-msg-id"
}
```

---

#### Status Messages

##### STATUS_REQUEST

Request robot status.

**Direction:** Orchestrator -> Robot

```json
{
  "type": "status_request",
  "id": "msg-uuid",
  "timestamp": "2024-01-15T10:30:00Z",
  "payload": {
    "robot_id": "robot-uuid"
  }
}
```

##### STATUS_RESPONSE

Robot status response.

**Direction:** Robot -> Orchestrator

```json
{
  "type": "status_response",
  "id": "msg-uuid",
  "timestamp": "2024-01-15T10:30:01Z",
  "payload": {
    "robot_id": "robot-uuid",
    "status": "online",
    "current_jobs": 2,
    "active_job_ids": ["job-1", "job-2"],
    "uptime_seconds": 86400,
    "system_info": {
      "os": "Windows 11",
      "python_version": "3.12.0",
      "playwright_version": "1.40.0"
    }
  },
  "correlation_id": "status-request-msg-id"
}
```

---

#### Logging Messages

##### LOG_ENTRY

Single log entry.

**Direction:** Robot -> Orchestrator

```json
{
  "type": "log_entry",
  "id": "msg-uuid",
  "timestamp": "2024-01-15T10:35:00Z",
  "payload": {
    "job_id": "job-uuid",
    "robot_id": "robot-uuid",
    "level": "INFO",
    "message": "Successfully clicked element",
    "node_id": "click_button_node",
    "extra": {
      "selector": "#submit-btn",
      "element_text": "Submit"
    }
  }
}
```

##### LOG_BATCH

Batch log entries for efficiency.

**Direction:** Robot -> Orchestrator

```json
{
  "type": "log_batch",
  "id": "msg-uuid",
  "timestamp": "2024-01-15T10:35:00Z",
  "payload": {
    "job_id": "job-uuid",
    "robot_id": "robot-uuid",
    "entries": [
      {
        "level": "INFO",
        "message": "Starting node execution",
        "node_id": "node-1",
        "timestamp": "2024-01-15T10:34:58Z"
      },
      {
        "level": "DEBUG",
        "message": "Element located",
        "node_id": "node-1",
        "timestamp": "2024-01-15T10:34:59Z"
      }
    ]
  }
}
```

---

#### Control Messages

##### PAUSE

Pause robot operations.

**Direction:** Orchestrator -> Robot

```json
{
  "type": "pause",
  "id": "msg-uuid",
  "timestamp": "2024-01-15T10:30:00Z",
  "payload": {
    "robot_id": "robot-uuid"
  }
}
```

##### RESUME

Resume robot operations.

**Direction:** Orchestrator -> Robot

```json
{
  "type": "resume",
  "id": "msg-uuid",
  "timestamp": "2024-01-15T10:35:00Z",
  "payload": {
    "robot_id": "robot-uuid"
  }
}
```

##### SHUTDOWN

Graceful shutdown command.

**Direction:** Orchestrator -> Robot

```json
{
  "type": "shutdown",
  "id": "msg-uuid",
  "timestamp": "2024-01-15T10:30:00Z",
  "payload": {
    "robot_id": "robot-uuid",
    "graceful": true
  }
}
```

---

#### Error Messages

##### ERROR

Error notification.

**Direction:** Both

```json
{
  "type": "error",
  "id": "msg-uuid",
  "timestamp": "2024-01-15T10:30:00Z",
  "payload": {
    "error_code": "INVALID_MESSAGE",
    "error_message": "Unknown message type: unknown_type",
    "details": {
      "received_type": "unknown_type"
    }
  },
  "correlation_id": "original-msg-id"
}
```

---

## Orchestrator API

### Python API

The Orchestrator Engine provides programmatic access:

#### OrchestratorEngine

```python
from casare_rpa.orchestrator.engine import OrchestratorEngine
from casare_rpa.orchestrator.models import JobPriority

# Initialize
engine = OrchestratorEngine(
    load_balancing="least_loaded",
    dispatch_interval=5,
    default_job_timeout=3600
)

# Start
await engine.start()
await engine.start_server(host="0.0.0.0", port=8765)
```

#### Submit Job

```python
job = await engine.submit_job(
    workflow_id="workflow-uuid",
    workflow_name="Data Extraction",
    workflow_json='{"nodes": [...], "connections": [...]}',
    robot_id=None,  # Any available robot
    priority=JobPriority.HIGH,
    scheduled_time=None,  # Immediate
    params={"customer_id": "CUST-001"},
    check_duplicate=True
)

print(f"Job ID: {job.id}")
```

#### Cancel Job

```python
success = await engine.cancel_job(
    job_id="job-uuid",
    reason="Cancelled by administrator"
)
```

#### Retry Job

```python
new_job = await engine.retry_job(job_id="failed-job-uuid")
```

#### Register Robot

```python
robot = await engine.register_robot(
    robot_id="robot-uuid",
    name="Production Robot 1",
    environment="production",
    max_concurrent_jobs=3,
    tags=["browser", "desktop"]
)
```

#### Create Schedule

```python
from casare_rpa.orchestrator.models import ScheduleFrequency

schedule = await engine.create_schedule(
    name="Daily Report",
    workflow_id="workflow-uuid",
    workflow_name="Generate Daily Report",
    frequency=ScheduleFrequency.CRON,
    cron_expression="0 9 * * MON-FRI",
    robot_id=None,
    priority=JobPriority.NORMAL,
    timezone="America/New_York",
    enabled=True
)
```

#### Get Statistics

```python
# Queue statistics
queue_stats = engine.get_queue_stats()
# Returns: {"queued": 5, "running": 2, "by_priority": {...}}

# Dispatcher statistics
dispatch_stats = engine.get_dispatcher_stats()

# Upcoming schedules
schedules = engine.get_upcoming_schedules(limit=10)
```

---

## Trigger Webhook API

### Webhook Endpoint

**URL:** `http://orchestrator-host:8766/webhook/{trigger_id}`

**Method:** POST

**Headers:**
```
Content-Type: application/json
X-Webhook-Secret: <shared-secret>
```

### Request

```json
{
  "event_type": "new_order",
  "data": {
    "order_id": "ORD-12345",
    "customer_id": "CUST-001",
    "amount": 1500.00
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Response

**Success (200 OK)**
```json
{
  "status": "accepted",
  "trigger_id": "trigger-uuid",
  "job_id": "job-uuid",
  "message": "Workflow execution triggered"
}
```

**Rate Limited (429 Too Many Requests)**
```json
{
  "status": "rate_limited",
  "trigger_id": "trigger-uuid",
  "cooldown_remaining": 45,
  "message": "Trigger is in cooldown period"
}
```

**Error (400 Bad Request)**
```json
{
  "status": "error",
  "error_code": "INVALID_PAYLOAD",
  "message": "Missing required field: event_type"
}
```

**Not Found (404)**
```json
{
  "status": "error",
  "error_code": "TRIGGER_NOT_FOUND",
  "message": "Trigger with ID trigger-uuid not found"
}
```

---

## Data Models

### Job

```json
{
  "id": "uuid",
  "workflow_id": "uuid",
  "workflow_name": "string",
  "robot_id": "uuid | null",
  "robot_name": "string",
  "status": "pending | queued | running | completed | failed | cancelled | timeout",
  "priority": 0-3,
  "environment": "string",
  "workflow_json": "string",
  "scheduled_time": "ISO-8601 | null",
  "started_at": "ISO-8601 | null",
  "completed_at": "ISO-8601 | null",
  "duration_ms": "integer",
  "progress": 0-100,
  "current_node": "string",
  "result": {},
  "logs": "string",
  "error_message": "string",
  "created_at": "ISO-8601",
  "created_by": "string"
}
```

### Robot

```json
{
  "id": "uuid",
  "name": "string",
  "status": "offline | online | busy | error | maintenance",
  "environment": "string",
  "max_concurrent_jobs": "integer",
  "current_jobs": "integer",
  "last_seen": "ISO-8601",
  "last_heartbeat": "ISO-8601",
  "tags": ["string"],
  "metrics": {
    "cpu_percent": "float",
    "memory_percent": "float",
    "disk_percent": "float"
  }
}
```

### Schedule

```json
{
  "id": "uuid",
  "name": "string",
  "workflow_id": "uuid",
  "workflow_name": "string",
  "robot_id": "uuid | null",
  "frequency": "once | hourly | daily | weekly | monthly | cron",
  "cron_expression": "string",
  "timezone": "string",
  "enabled": "boolean",
  "priority": 0-3,
  "last_run": "ISO-8601 | null",
  "next_run": "ISO-8601",
  "run_count": "integer",
  "success_count": "integer",
  "created_at": "ISO-8601"
}
```

### Workflow

```json
{
  "id": "uuid",
  "name": "string",
  "description": "string",
  "version": "integer",
  "status": "draft | published | archived",
  "json_definition": "string",
  "created_by": "string",
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601",
  "tags": ["string"],
  "execution_count": "integer",
  "success_count": "integer",
  "avg_duration_ms": "integer"
}
```

### TriggerEvent

```json
{
  "trigger_id": "uuid",
  "trigger_type": "manual | scheduled | webhook | file_watch | email | form | chat | workflow_call",
  "workflow_id": "uuid",
  "scenario_id": "uuid",
  "timestamp": "ISO-8601",
  "payload": {},
  "metadata": {},
  "priority": 0-3
}
```

---

## Error Handling

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_JSON` | 400 | Malformed JSON in request |
| `INVALID_MESSAGE` | 400 | Unknown or malformed message type |
| `INVALID_PAYLOAD` | 400 | Missing required fields |
| `AUTHENTICATION_FAILED` | 401 | Invalid or missing credentials |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMITED` | 429 | Too many requests |
| `HANDLER_ERROR` | 500 | Internal processing error |
| `CONNECTION_ERROR` | 502 | Backend connection failed |
| `TIMEOUT` | 504 | Operation timed out |

### Error Response Format

```json
{
  "type": "error",
  "payload": {
    "error_code": "ERROR_CODE",
    "error_message": "Human-readable description",
    "details": {
      "field": "additional context"
    }
  },
  "correlation_id": "original-request-id"
}
```

### Retry Strategy

For transient errors, implement exponential backoff:

```python
import asyncio
import random

async def retry_with_backoff(operation, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await operation()
        except TransientError as e:
            if attempt == max_retries - 1:
                raise
            delay = min(2 ** attempt + random.random(), 60)
            await asyncio.sleep(delay)
```

---

## Rate Limiting

### Default Limits

| Endpoint | Requests | Window |
|----------|----------|--------|
| WebSocket messages | 100 | 60s |
| Webhook triggers | 10 | 60s |
| Job submissions | 50 | 60s |

### Rate Limit Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1705318800
```

---

## Related Documentation

- [System Overview](../architecture/SYSTEM_OVERVIEW.md)
- [Security Architecture](../security/SECURITY_ARCHITECTURE.md)
- [Troubleshooting Guide](../operations/TROUBLESHOOTING.md)
