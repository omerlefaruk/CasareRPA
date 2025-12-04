# HttpRequestNode

HTTP Request node - makes HTTP/HTTPS requests to APIs and web services.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.utility_nodes`
**File:** `src\casare_rpa\nodes\utility_nodes.py:42`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `url` | INPUT | No | DataType.STRING |
| `headers` | INPUT | No | DataType.ANY |
| `body` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `response_body` | OUTPUT | DataType.STRING |
| `status_code` | OUTPUT | DataType.INTEGER |
| `headers` | OUTPUT | DataType.ANY |
| `success` | OUTPUT | DataType.BOOLEAN |
| `error` | OUTPUT | DataType.STRING |

## Inheritance

Extends: `BaseNode`
