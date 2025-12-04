# SSETriggerNode

SSE trigger node that listens to Server-Sent Events.

`:material-bell: Trigger`


**Module:** `casare_rpa.nodes.trigger_nodes.sse_trigger_node`
**File:** `src\casare_rpa\nodes\trigger_nodes\sse_trigger_node.py:67`


## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `event_type` | STRING | Event Type |
| `data` | ANY | Data (parsed) |
| `raw_data` | STRING | Raw Data |
| `event_id` | STRING | Event ID |
| `retry` | INTEGER | Retry |
| `timestamp` | STRING | Timestamp |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `sse_url` | STRING | `-` | Yes | URL of the SSE endpoint |
| `event_types` | STRING | `` | No | Comma-separated event types to listen for (empty = all) |
| `headers` | JSON | `{}` | No | JSON object of headers to send with request |
| `reconnect_delay_seconds` | INTEGER | `5` | No | Delay before reconnecting on disconnect |
| `max_reconnect_attempts` | INTEGER | `10` | No | Maximum reconnection attempts (0 = unlimited) |
| `timeout_seconds` | INTEGER | `0` | No | Connection timeout (0 = no timeout) |

## Inheritance

Extends: `BaseTriggerNode`
