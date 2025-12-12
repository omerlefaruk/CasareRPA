# Webhook Trigger

The **WebhookTriggerNode** creates an HTTP endpoint that triggers workflows when external systems send requests. It supports multiple HTTP methods, authentication options, CORS, and IP filtering.

## Overview

| Property | Value |
|----------|-------|
| Node Type | `WebhookTriggerNode` |
| Trigger Type | `WEBHOOK` |
| Icon | webhook |
| Category | triggers |

## Configuration Properties

### Basic Settings

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| endpoint | string | `""` | Custom endpoint path (e.g., `/my-webhook`). Auto-generated if empty |
| methods | string | `POST` | Comma-separated HTTP methods to accept (`GET`, `POST`, `PUT`, `DELETE`, `PATCH`) |

### Authentication

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| auth_type | choice | `none` | Authentication method: `none`, `basic`, `header`, `jwt` |
| auth_header_name | string | `X-API-Key` | Header name for header-based auth |
| auth_header_value | string | `""` | Expected header value (secret) |
| basic_username | string | `""` | Username for basic auth |
| basic_password | string | `""` | Password for basic auth |
| jwt_secret | string | `""` | Secret for JWT token validation |

### CORS Settings

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| cors_enabled | boolean | `false` | Allow cross-origin requests |
| cors_origins | string | `*` | Comma-separated allowed origins (`*` for all) |

### IP Filtering

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| ip_whitelist | string | `""` | Comma-separated IPs/CIDRs to allow (empty = all) |
| ip_blacklist | string | `""` | Comma-separated IPs/CIDRs to block |

### Response Settings

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| response_mode | choice | `immediate` | When to respond: `immediate`, `wait_for_workflow`, `custom` |
| response_code | integer | `200` | HTTP response code |
| response_body | string | `{"status": "received"}` | JSON response body |

### Advanced Settings

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| binary_data_enabled | boolean | `false` | Accept binary file uploads |
| max_payload_size | integer | `16777216` | Maximum payload size in bytes (16MB default) |

## Output Ports (Payload)

| Port | Type | Description |
|------|------|-------------|
| payload | dict | Request body (JSON parsed if applicable) |
| headers | dict | Request headers |
| query_params | dict | URL query parameters |
| method | string | HTTP method used (GET, POST, etc.) |
| path | string | Request path |
| client_ip | string | Client IP address |
| exec_out | exec | Execution flow continues |

## HTTP Methods

Configure which methods your webhook accepts:

```json
{
  "methods": "POST,PUT"
}
```

| Method | Use Case |
|--------|----------|
| `GET` | Simple triggers without body |
| `POST` | Standard webhook payloads |
| `PUT` | Update operations |
| `DELETE` | Deletion notifications |
| `PATCH` | Partial updates |

## Authentication Options

### No Authentication

```json
{
  "auth_type": "none"
}
```

> **Warning:** Only use for internal/testing webhooks. Production webhooks should always be authenticated.

### Header Authentication

Validate a custom header value:

```json
{
  "auth_type": "header",
  "auth_header_name": "X-Webhook-Secret",
  "auth_header_value": "my-secret-token-12345"
}
```

**Caller must include:**
```bash
curl -X POST https://your-server/webhook \
  -H "X-Webhook-Secret: my-secret-token-12345" \
  -d '{"event": "test"}'
```

### Basic Authentication

Standard HTTP Basic Auth:

```json
{
  "auth_type": "basic",
  "basic_username": "webhook_user",
  "basic_password": "secure_password"
}
```

**Caller must include:**
```bash
curl -X POST https://your-server/webhook \
  -u webhook_user:secure_password \
  -d '{"event": "test"}'
```

### JWT Authentication

Validate JWT tokens:

```json
{
  "auth_type": "jwt",
  "jwt_secret": "your-jwt-secret-key"
}
```

**Caller must include:**
```bash
curl -X POST https://your-server/webhook \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -d '{"event": "test"}'
```

## Request Body Handling

The webhook automatically parses JSON request bodies:

```bash
# JSON body becomes accessible as dict
curl -X POST https://your-server/webhook \
  -H "Content-Type: application/json" \
  -d '{"user_id": 123, "action": "signup"}'
```

In subsequent nodes:
```python
user_id = inputs["payload"]["user_id"]  # 123
action = inputs["payload"]["action"]     # "signup"
```

### Form Data

Form-encoded data is also parsed:

```bash
curl -X POST https://your-server/webhook \
  -d "user_id=123&action=signup"
```

### Binary Data

Enable binary uploads for file handling:

```json
{
  "binary_data_enabled": true,
  "max_payload_size": 52428800
}
```

## Headers Access

Access request headers in your workflow:

```python
# Access specific headers
content_type = inputs["headers"]["Content-Type"]
user_agent = inputs["headers"]["User-Agent"]

# GitHub webhook signature
signature = inputs["headers"]["X-Hub-Signature-256"]
```

## Response Configuration

### Immediate Response (Default)

Respond immediately when the webhook is received:

```json
{
  "response_mode": "immediate",
  "response_code": 200,
  "response_body": "{\"status\": \"received\", \"message\": \"Processing started\"}"
}
```

### Wait for Workflow

Wait for workflow completion before responding (synchronous):

```json
{
  "response_mode": "wait_for_workflow"
}
```

The response will include workflow execution results.

### Custom Response

Use workflow output as response:

```json
{
  "response_mode": "custom",
  "response_code": 201
}
```

## CORS Configuration

Enable CORS for browser-based integrations:

```json
{
  "cors_enabled": true,
  "cors_origins": "https://app.example.com,https://admin.example.com"
}
```

For development (allow all origins):
```json
{
  "cors_enabled": true,
  "cors_origins": "*"
}
```

## IP Filtering

### Whitelist (Allow List)

Only allow requests from specific IPs:

```json
{
  "ip_whitelist": "192.168.1.0/24,10.0.0.5,203.0.113.42"
}
```

### Blacklist (Block List)

Block specific IPs:

```json
{
  "ip_blacklist": "192.168.1.100,10.0.0.0/8"
}
```

## Complete Examples

### GitHub Webhook Integration

```json
{
  "endpoint": "/github/push",
  "methods": "POST",
  "auth_type": "header",
  "auth_header_name": "X-Hub-Signature-256",
  "auth_header_value": "sha256=<computed-signature>",
  "cors_enabled": false
}
```

### Stripe Webhook

```json
{
  "endpoint": "/stripe/events",
  "methods": "POST",
  "auth_type": "header",
  "auth_header_name": "Stripe-Signature",
  "auth_header_value": "<your-endpoint-secret>",
  "response_mode": "immediate",
  "response_code": 200,
  "response_body": "{\"received\": true}"
}
```

### Public Form Submission

```json
{
  "endpoint": "/contact-form",
  "methods": "POST",
  "auth_type": "none",
  "cors_enabled": true,
  "cors_origins": "https://mywebsite.com",
  "ip_blacklist": "",
  "response_mode": "immediate",
  "response_code": 200,
  "response_body": "{\"message\": \"Thank you for your submission\"}"
}
```

### Internal Microservice

```json
{
  "endpoint": "/internal/process-order",
  "methods": "POST",
  "auth_type": "jwt",
  "jwt_secret": "${JWT_SECRET}",
  "ip_whitelist": "10.0.0.0/8",
  "response_mode": "wait_for_workflow"
}
```

## Webhook URL

The full webhook URL depends on your deployment:

| Deployment | URL Pattern |
|------------|-------------|
| Canvas (dev) | `http://localhost:8766/webhooks/my-endpoint` |
| Robot | `http://robot-host:8766/webhooks/my-endpoint` |
| Orchestrator | `https://orchestrator.example.com/webhooks/my-endpoint` |

For auto-generated endpoints (empty `endpoint` property):
```
http://localhost:8766/hooks/{node_id}
```

## Python Example

```python
from casare_rpa.nodes.trigger_nodes import WebhookTriggerNode

trigger = WebhookTriggerNode(
    node_id="order_webhook",
    config={
        "endpoint": "/orders/new",
        "methods": "POST",
        "auth_type": "header",
        "auth_header_name": "X-API-Key",
        "auth_header_value": "secret-key-12345",
        "response_mode": "immediate",
        "response_code": 202,
        "response_body": '{"status": "accepted"}',
    }
)

# Get the full webhook URL
url = trigger.get_webhook_url("https://api.example.com")
# -> "https://api.example.com/webhooks/orders/new"
```

## Workflow JSON Example

```json
{
  "nodes": [
    {
      "id": "webhook_1",
      "type": "WebhookTriggerNode",
      "config": {
        "endpoint": "/orders",
        "methods": "POST",
        "auth_type": "header",
        "auth_header_name": "X-API-Key",
        "auth_header_value": "my-secret"
      },
      "position": {"x": 100, "y": 200}
    },
    {
      "id": "log_1",
      "type": "LogNode",
      "config": {
        "message": "Received order from {{client_ip}}: {{payload}}"
      },
      "position": {"x": 400, "y": 200}
    }
  ],
  "connections": [
    {
      "source_node": "webhook_1",
      "source_port": "exec_out",
      "target_node": "log_1",
      "target_port": "exec_in"
    },
    {
      "source_node": "webhook_1",
      "source_port": "payload",
      "target_node": "log_1",
      "target_port": "payload"
    }
  ]
}
```

## Testing with cURL

```bash
# Basic POST request
curl -X POST http://localhost:8766/webhooks/orders \
  -H "Content-Type: application/json" \
  -H "X-API-Key: my-secret" \
  -d '{"order_id": "12345", "amount": 99.99}'

# With query parameters
curl -X POST "http://localhost:8766/webhooks/orders?source=web" \
  -H "X-API-Key: my-secret" \
  -d '{"order_id": "12345"}'
```

## Best Practices

1. **Always Use Authentication:** Even for internal webhooks, use at least header auth
2. **Validate Payloads:** Check payload structure before processing
3. **Use HTTPS:** Always use HTTPS in production
4. **Implement Idempotency:** Design workflows to handle duplicate webhook deliveries
5. **Log Client IPs:** Track `client_ip` for security auditing
6. **Set Reasonable Timeouts:** For `wait_for_workflow` mode, ensure workflow completes quickly
7. **Respond Quickly:** Return 200/202 immediately, process asynchronously

## Related

- [Schedule Trigger](schedule.md) - Time-based triggering
- [File Watch Trigger](file-watch.md) - File system event triggering
- [Trigger Overview](index.md) - All available triggers
