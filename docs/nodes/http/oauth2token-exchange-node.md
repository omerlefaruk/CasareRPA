# OAuth2TokenExchangeNode

Exchange OAuth 2.0 authorization code for access token.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.http.http_auth`
**File:** `src\casare_rpa\nodes\http\http_auth.py:433`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `code` | INPUT | No | DataType.STRING |
| `code_verifier` | INPUT | No | DataType.STRING |
| `refresh_token` | INPUT | No | DataType.STRING |
| `username` | INPUT | No | DataType.STRING |
| `password` | INPUT | No | DataType.STRING |
| `scope` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `access_token` | OUTPUT | DataType.STRING |
| `refresh_token` | OUTPUT | DataType.STRING |
| `token_type` | OUTPUT | DataType.STRING |
| `expires_in` | OUTPUT | DataType.INTEGER |
| `scope` | OUTPUT | DataType.STRING |
| `id_token` | OUTPUT | DataType.STRING |
| `full_response` | OUTPUT | DataType.DICT |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `client_id` | STRING | `` | No | OAuth 2.0 client ID |
| `client_secret` | STRING | `` | No | OAuth 2.0 client secret (optional for public clients) |
| `token_url` | STRING | `` | No | OAuth 2.0 token endpoint URL |
| `redirect_uri` | STRING | `http://localhost:...` | No | OAuth redirect URI (must match authorization request) |
| `grant_type` | CHOICE | `authorization_code` | No | OAuth 2.0 grant type Choices: authorization_code, client_credentials, refresh_token, password |

## Inheritance

Extends: `BaseNode`
