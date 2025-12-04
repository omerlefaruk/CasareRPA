# OAuth2TokenValidateNode

Validate an OAuth 2.0 access token using introspection endpoint.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.http.http_auth`
**File:** `src\casare_rpa\nodes\http\http_auth.py:836`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `token` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `active` | OUTPUT | DataType.BOOLEAN |
| `client_id` | OUTPUT | DataType.STRING |
| `username` | OUTPUT | DataType.STRING |
| `scope` | OUTPUT | DataType.STRING |
| `expires_at` | OUTPUT | DataType.INTEGER |
| `token_type` | OUTPUT | DataType.STRING |
| `full_response` | OUTPUT | DataType.DICT |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `introspection_url` | STRING | `` | No | Token introspection endpoint URL (RFC 7662) |
| `client_id` | STRING | `` | No | Client ID for introspection authentication |
| `client_secret` | STRING | `` | No | Client secret for introspection authentication |

## Inheritance

Extends: `BaseNode`
