# OAuth2AuthorizeNode

Build OAuth 2.0 authorization URL for user authentication.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.http.http_auth`
**File:** `src\casare_rpa\nodes\http\http_auth.py:259`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `client_id` | INPUT | No | DataType.STRING |
| `auth_url` | INPUT | No | DataType.STRING |
| `scope` | INPUT | No | DataType.STRING |
| `redirect_uri` | INPUT | No | DataType.STRING |
| `extra_params` | INPUT | No | DataType.DICT |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `auth_url` | OUTPUT | DataType.STRING |
| `state` | OUTPUT | DataType.STRING |
| `code_verifier` | OUTPUT | DataType.STRING |
| `code_challenge` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `client_id` | STRING | `` | No | OAuth 2.0 client ID |
| `auth_url` | STRING | `` | No | OAuth 2.0 authorization endpoint URL |
| `scope` | STRING | `` | No | OAuth 2.0 scope (space-separated) |
| `redirect_uri` | STRING | `http://localhost:...` | No | OAuth redirect URI (must match app registration) |
| `state` | STRING | `` | No | CSRF protection state parameter (auto-generated if empty) |
| `response_type` | CHOICE | `code` | No | Authorization code flow (code) or implicit flow (token) Choices: code, token |
| `pkce_enabled` | BOOLEAN | `True` | No | Enable PKCE (Proof Key for Code Exchange) for enhanced security |

## Inheritance

Extends: `BaseNode`
