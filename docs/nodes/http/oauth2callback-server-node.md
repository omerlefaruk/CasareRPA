# OAuth2CallbackServerNode

Start a local server to receive OAuth 2.0 callback.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.http.http_auth`
**File:** `src\casare_rpa\nodes\http\http_auth.py:638`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `expected_state` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `code` | OUTPUT | DataType.STRING |
| `state` | OUTPUT | DataType.STRING |
| `access_token` | OUTPUT | DataType.STRING |
| `error` | OUTPUT | DataType.STRING |
| `error_description` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `port` | INTEGER | `8080` | No | Local port for callback server (min: 1024, max: 65535) |
| `timeout` | INTEGER | `120` | No | Maximum time to wait for callback (min: 10, max: 600) |
| `path` | STRING | `/callback` | No | URL path for the callback |

## Inheritance

Extends: `BaseNode`
