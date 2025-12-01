# CasareRPA Orchestrator API Error Codes Reference

This document provides a comprehensive reference for all error codes returned by the Orchestrator API, including HTTP status codes, descriptions, probable causes, and troubleshooting steps.

---

## Table of Contents

- [Authentication Errors (401, 403)](#authentication-errors)
- [Validation Errors (400)](#validation-errors)
- [Resource Errors (404)](#resource-errors)
- [Rate Limiting Errors (429)](#rate-limiting-errors)
- [Server Errors (500, 501, 503)](#server-errors)
- [WebSocket Errors](#websocket-errors)

---

## Authentication Errors

### AUTH_TOKEN_MISSING

| Property | Value |
|----------|-------|
| HTTP Status | 401 Unauthorized |
| Message | `Authentication required` |
| Header | `WWW-Authenticate: Bearer` |

**Probable Causes**:
- No `Authorization` header provided
- No `X-Api-Token` header for robot endpoints

**Troubleshooting**:
1. Include `Authorization: Bearer <token>` header
2. For robots, include `X-Api-Token: <api_token>` header
3. In dev mode (`JWT_DEV_MODE=true`), authentication is bypassed

**Prevention**:
```python
headers = {"Authorization": f"Bearer {access_token}"}
response = await client.get(url, headers=headers)
```

---

### AUTH_TOKEN_EXPIRED

| Property | Value |
|----------|-------|
| HTTP Status | 401 Unauthorized |
| Message | `Token has expired` |
| Header | `WWW-Authenticate: Bearer` |

**Probable Causes**:
- Access token older than `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` (default: 60)
- Refresh token older than `JWT_REFRESH_TOKEN_EXPIRE_DAYS` (default: 7)
- System clock skew between client and server

**Troubleshooting**:
1. Use the `/auth/refresh` endpoint to get a new access token
2. If refresh token expired, re-authenticate via `/auth/login`
3. Check system clocks are synchronized (NTP)

**Prevention**:
```python
async def refresh_token_if_needed(refresh_token: str) -> str:
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    return response.json()["access_token"]
```

---

### AUTH_TOKEN_INVALID

| Property | Value |
|----------|-------|
| HTTP Status | 401 Unauthorized |
| Message | `Invalid authentication token` |
| Header | `WWW-Authenticate: Bearer` |

**Probable Causes**:
- Token is malformed or corrupted
- Token signed with different secret key
- Token algorithm mismatch
- Token modified after issuance

**Troubleshooting**:
1. Re-authenticate via `/auth/login`
2. Verify `JWT_SECRET_KEY` is consistent across services
3. Check token is not being modified in transit

---

### AUTH_TOKEN_WRONG_TYPE

| Property | Value |
|----------|-------|
| HTTP Status | 401 Unauthorized |
| Message | `Invalid token type. Use access token.` |

**Probable Causes**:
- Using refresh token where access token required
- Token `type` claim is not `access`

**Troubleshooting**:
1. Use the `access_token` from login response, not `refresh_token`
2. Refresh tokens are only valid for `/auth/refresh` endpoint

---

### AUTH_REFRESH_TOKEN_INVALID

| Property | Value |
|----------|-------|
| HTTP Status | 400 Bad Request |
| Message | `Invalid token type. Expected refresh token.` |

**Probable Causes**:
- Using access token in `/auth/refresh` endpoint
- Token `type` claim is not `refresh`

**Troubleshooting**:
1. Use the `refresh_token` from login response
2. Access tokens cannot be used to refresh

---

### AUTH_INSUFFICIENT_PERMISSIONS

| Property | Value |
|----------|-------|
| HTTP Status | 403 Forbidden |
| Message | `Insufficient permissions. Required role: <role>` |

**Probable Causes**:
- User lacks required role (admin, developer, operator, viewer)
- Role removed from user account
- Endpoint requires higher privilege level

**Troubleshooting**:
1. Check user roles via `/auth/me` endpoint
2. Contact administrator to grant required role
3. Use account with appropriate privileges

**Role Hierarchy**:
- `admin` - Full access (includes all other roles)
- `developer` - Create/modify workflows
- `operator` - Execute workflows
- `viewer` - Read-only access

---

### AUTH_ROBOT_TOKEN_INVALID

| Property | Value |
|----------|-------|
| HTTP Status | 401 Unauthorized |
| Message | `Invalid or expired API token` |

**Probable Causes**:
- Robot API token not configured in `ROBOT_TOKENS`
- Token hash mismatch
- Token revoked or rotated

**Troubleshooting**:
1. Verify `ROBOT_TOKENS` environment variable includes robot:hash pair
2. Regenerate token using `tools/generate_robot_token.py`
3. Ensure token is SHA-256 hashed correctly

---

## Validation Errors

### VALIDATION_WORKFLOW_NO_NODES

| Property | Value |
|----------|-------|
| HTTP Status | 400 Bad Request |
| Message | `workflow_json must contain 'nodes' key` |

**Probable Causes**:
- Missing `nodes` key in workflow JSON
- Workflow JSON is empty object

**Troubleshooting**:
```json
{
  "workflow_json": {
    "nodes": [],  // Required key
    "connections": []
  }
}
```

---

### VALIDATION_WORKFLOW_NODES_FORMAT

| Property | Value |
|----------|-------|
| HTTP Status | 400 Bad Request |
| Message | `workflow_json.nodes must be a dict or list` |

**Probable Causes**:
- `nodes` is not an array or object
- `nodes` is null or string

**Troubleshooting**:
```json
// Valid formats:
{"nodes": [{"id": "1", "type": "StartNode"}]}
{"nodes": {"node1": {"type": "StartNode"}}}
```

---

### VALIDATION_WORKFLOW_TOO_LARGE

| Property | Value |
|----------|-------|
| HTTP Status | 400 Bad Request |
| Message | `Workflow exceeds maximum node count (<count> > 1000)` |

**Probable Causes**:
- Workflow has more than 1000 nodes
- Malicious payload attempting resource exhaustion

**Troubleshooting**:
1. Split large workflow into sub-workflows
2. Use workflow composition patterns
3. Contact administrator to increase limit if legitimate use case

---

### VALIDATION_TRIGGER_TYPE_INVALID

| Property | Value |
|----------|-------|
| HTTP Status | 400 Bad Request |
| Message | `trigger_type must be one of ['manual', 'scheduled', 'webhook']` |

**Troubleshooting**:
```python
# Valid trigger types
trigger_type="manual"     # Execute immediately
trigger_type="scheduled"  # Cron-based execution
trigger_type="webhook"    # HTTP trigger
```

---

### VALIDATION_EXECUTION_MODE_INVALID

| Property | Value |
|----------|-------|
| HTTP Status | 400 Bad Request |
| Message | `execution_mode must be one of ['lan', 'internet']` |

**Troubleshooting**:
```python
execution_mode="lan"       # Local network robots
execution_mode="internet"  # Internet-connected robots
```

---

### VALIDATION_CRON_EXPRESSION_INVALID

| Property | Value |
|----------|-------|
| HTTP Status | 400 Bad Request |
| Message | `Invalid cron expression: <details>` |

**Probable Causes**:
- Malformed cron syntax
- Invalid field values (e.g., month 13)
- Missing required fields

**Troubleshooting**:
```python
# Valid cron expressions
"0 9 * * 1-5"      # 9 AM weekdays
"*/15 * * * *"    # Every 15 minutes
"0 0 1 * *"       # First day of month
```

**Cron Format**: `minute hour day-of-month month day-of-week`

---

### VALIDATION_FILE_TYPE_INVALID

| Property | Value |
|----------|-------|
| HTTP Status | 400 Bad Request |
| Message | `File must be a .json file` |

**Probable Causes**:
- Uploaded file lacks `.json` extension
- Filename is empty

**Troubleshooting**:
1. Rename file to have `.json` extension
2. Verify file is valid JSON

---

### VALIDATION_FILE_CONTENT_TYPE_INVALID

| Property | Value |
|----------|-------|
| HTTP Status | 400 Bad Request |
| Message | `Invalid content type: <type>. Allowed: application/json, text/plain, application/octet-stream` |

**Probable Causes**:
- Client sent unsupported Content-Type header
- File processed as non-JSON type

**Troubleshooting**:
```bash
curl -F "file=@workflow.json;type=application/json" ...
```

---

### VALIDATION_FILE_TOO_LARGE

| Property | Value |
|----------|-------|
| HTTP Status | 413 Payload Too Large |
| Message | `File too large. Maximum size: 50MB` |

**Probable Causes**:
- Uploaded file exceeds 50MB limit
- Large embedded data in workflow

**Troubleshooting**:
1. Remove unnecessary data from workflow
2. Store large assets externally, reference by URL
3. Split into multiple workflows

---

### VALIDATION_JSON_INVALID

| Property | Value |
|----------|-------|
| HTTP Status | 400 Bad Request |
| Message | `Invalid JSON: <parse_error>` |

**Probable Causes**:
- Syntax error in JSON
- Encoding issues
- Truncated file

**Troubleshooting**:
1. Validate JSON with linter
2. Check for trailing commas (not valid JSON)
3. Verify UTF-8 encoding

---

## Resource Errors

### RESOURCE_WORKFLOW_NOT_FOUND

| Property | Value |
|----------|-------|
| HTTP Status | 404 Not Found |
| Message | `Workflow not found: <workflow_id>` |

**Probable Causes**:
- Workflow deleted
- Workflow ID typo
- Looking in wrong environment

**Troubleshooting**:
1. Verify workflow ID is correct UUID
2. Check workflow exists via listing endpoint
3. Verify database/filesystem storage is accessible

---

### RESOURCE_SCHEDULE_NOT_FOUND

| Property | Value |
|----------|-------|
| HTTP Status | 404 Not Found |
| Message | `Schedule not found: <schedule_id>` |

**Probable Causes**:
- Schedule deleted
- Schedule ID typo
- Using in-memory storage (data lost on restart)

**Troubleshooting**:
1. List schedules to verify existence
2. Note: In-memory storage loses data on restart

---

### RESOURCE_ROBOT_NOT_FOUND

| Property | Value |
|----------|-------|
| HTTP Status | 404 Not Found |
| Message | `Robot <robot_id> not found` |

**Probable Causes**:
- Robot never registered
- Robot ID typo
- Robot data expired

---

### RESOURCE_JOB_NOT_FOUND

| Property | Value |
|----------|-------|
| HTTP Status | 404 Not Found |
| Message | `Job <job_id> not found` |

**Probable Causes**:
- Job completed and archived
- Job ID typo
- Database query failed

---

## Rate Limiting Errors

### RATE_LIMIT_EXCEEDED

| Property | Value |
|----------|-------|
| HTTP Status | 429 Too Many Requests |
| Message | `Rate limit exceeded` |
| Header | `Retry-After: <seconds>` |

**Probable Causes**:
- Too many requests from same IP
- Client not respecting rate limits
- Polling too frequently

**Rate Limits by Endpoint**:
| Endpoint | Limit |
|----------|-------|
| `/metrics/fleet` | 100/min |
| `/metrics/robots` | 100/min |
| `/metrics/robots/{id}` | 200/min |
| `/metrics/jobs` | 50/min |
| `/metrics/jobs/{id}` | 200/min |
| `/metrics/analytics` | 20/min |
| `/metrics/activity` | 60/min |

**Troubleshooting**:
1. Implement exponential backoff
2. Cache responses client-side
3. Use WebSocket for real-time updates instead of polling
4. Check `Retry-After` header for wait time

**Prevention**:
```python
import asyncio
from tenacity import retry, wait_exponential, stop_after_attempt

@retry(
    wait=wait_exponential(multiplier=1, min=1, max=60),
    stop=stop_after_attempt(5)
)
async def api_call_with_retry():
    response = await client.get(url)
    if response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 60))
        await asyncio.sleep(retry_after)
        raise Exception("Rate limited")
    return response
```

---

## Server Errors

### SERVER_INTERNAL_ERROR

| Property | Value |
|----------|-------|
| HTTP Status | 500 Internal Server Error |
| Message | `<operation> failed: <details>` |

**Probable Causes**:
- Database connection failed
- Unhandled exception
- Resource exhaustion

**Troubleshooting**:
1. Check API logs for stack trace
2. Verify database connectivity via `/health/detailed`
3. Check system resources (CPU, memory, disk)

---

### SERVER_DATABASE_UNAVAILABLE

| Property | Value |
|----------|-------|
| HTTP Status | 500 Internal Server Error |
| Message | `Failed to fetch <resource>` |

**Probable Causes**:
- Database pool exhausted
- PostgreSQL server down
- Network connectivity issues

**Troubleshooting**:
1. Check `/health/detailed` for database status
2. Verify PostgreSQL is running
3. Check connection string configuration

---

### SERVER_NOT_IMPLEMENTED

| Property | Value |
|----------|-------|
| HTTP Status | 501 Not Implemented |
| Message | `Production authentication not yet implemented. Enable JWT_DEV_MODE=true for testing.` |

**Probable Causes**:
- Feature marked as TODO
- Production auth database not configured

**Troubleshooting**:
1. Enable dev mode for testing: `JWT_DEV_MODE=true`
2. Implement production user database integration

---

### SERVER_DEGRADED_MODE

| Property | Value |
|----------|-------|
| HTTP Status | 200 OK |
| Status Field | `"status": "degraded"` |

**Probable Causes**:
- Database unavailable but API still running
- Fallback to in-memory/filesystem storage

**Troubleshooting**:
1. Check `/health/detailed` for dependency status
2. API continues serving from fallback storage
3. Some features may be unavailable

---

## WebSocket Errors

### WS_CONNECTION_TIMEOUT

| Property | Value |
|----------|-------|
| Event | Connection closed by server |
| Timeout | 1 second per message |

**Probable Causes**:
- Client too slow to receive messages
- Network congestion
- Client buffer full

**Troubleshooting**:
1. Implement faster message processing
2. Add message buffering on client
3. Use faster network connection

---

### WS_INVALID_MESSAGE

| Property | Value |
|----------|-------|
| Response | Connection closed |

**Probable Causes**:
- Sent non-text message
- Malformed ping/pong

**Expected Messages**:
- Client sends: `ping`
- Server responds: `pong`

---

## Error Response Format

All REST API errors follow this structure:

```json
{
  "detail": "Human-readable error message"
}
```

For validation errors with multiple fields:
```json
{
  "detail": [
    {
      "loc": ["body", "workflow_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Best Practices

### Implementing Error Handling

```python
import httpx
from typing import Optional

class OrchestratorAPIError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")

async def handle_response(response: httpx.Response) -> dict:
    if response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 60))
        raise OrchestratorAPIError(429, f"Rate limited. Retry after {retry_after}s")

    if response.status_code == 401:
        raise OrchestratorAPIError(401, "Authentication failed. Re-login required.")

    if response.status_code == 403:
        raise OrchestratorAPIError(403, "Insufficient permissions.")

    if response.status_code == 404:
        raise OrchestratorAPIError(404, "Resource not found.")

    if response.status_code >= 500:
        raise OrchestratorAPIError(
            response.status_code,
            "Server error. Check API health endpoint."
        )

    response.raise_for_status()
    return response.json()
```

### Retry Strategy

```python
from tenacity import (
    retry,
    retry_if_exception_type,
    wait_exponential,
    stop_after_attempt,
)

@retry(
    retry=retry_if_exception_type((httpx.TransportError, OrchestratorAPIError)),
    wait=wait_exponential(multiplier=1, min=1, max=60),
    stop=stop_after_attempt(5),
)
async def resilient_api_call(client: httpx.AsyncClient, url: str) -> dict:
    response = await client.get(url)
    return await handle_response(response)
```
