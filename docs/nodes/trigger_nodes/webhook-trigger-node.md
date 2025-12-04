# WebhookTriggerNode

Webhook trigger node that listens for HTTP requests.

`:material-bell: Trigger`


**Module:** `casare_rpa.nodes.trigger_nodes.webhook_trigger_node`
**File:** `src\casare_rpa\nodes\trigger_nodes\webhook_trigger_node.py:152`


## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `payload` | DICT | Request Payload |
| `headers` | DICT | Request Headers |
| `query_params` | DICT | Query Parameters |
| `method` | STRING | HTTP Method |
| `path` | STRING | Request Path |
| `client_ip` | STRING | Client IP |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `endpoint` | STRING | `` | No | Custom endpoint path (e.g., /my-webhook). Auto-generated if empty. |
| `methods` | STRING | `POST` | No | Comma-separated HTTP methods to accept (GET,POST,PUT,DELETE,PATCH) |
| `auth_type` | CHOICE | `none` | No | Authentication method for webhook requests Choices: none, basic, header, jwt |
| `auth_header_name` | STRING | `X-API-Key` | No | Header name for header-based auth |
| `auth_header_value` | STRING | `` | No | Expected header value (secret) |
| `basic_username` | STRING | `` | No | Basic Auth Username |
| `basic_password` | STRING | `` | No | Basic Auth Password |
| `jwt_secret` | STRING | `` | No | Secret for JWT token validation |
| `cors_enabled` | BOOLEAN | `False` | No | Allow cross-origin requests |
| `cors_origins` | STRING | `*` | No | Comma-separated allowed origins (* for all) |
| `ip_whitelist` | STRING | `` | No | Comma-separated IPs/CIDRs to allow (empty = all) |
| `ip_blacklist` | STRING | `` | No | Comma-separated IPs/CIDRs to block |
| `response_mode` | CHOICE | `immediate` | No | When to send HTTP response Choices: immediate, wait_for_workflow, custom |
| `response_code` | INTEGER | `200` | No | HTTP response code for immediate/custom mode |
| `response_body` | STRING | `{"status": "recei...` | No | JSON response body for immediate/custom mode |
| `binary_data_enabled` | BOOLEAN | `False` | No | Accept binary file uploads |
| `max_payload_size` | INTEGER | `16777216` | No | Max Payload Size (bytes) |

## Inheritance

Extends: `BaseTriggerNode`
