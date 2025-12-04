# HttpAuthNode

Configure HTTP authentication headers.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.http.http_auth`
**File:** `src\casare_rpa\nodes\http\http_auth.py:84`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `credential_name` | INPUT | No | DataType.STRING |
| `auth_type` | INPUT | No | DataType.STRING |
| `token` | INPUT | No | DataType.STRING |
| `username` | INPUT | No | DataType.STRING |
| `password` | INPUT | No | DataType.STRING |
| `api_key_name` | INPUT | No | DataType.STRING |
| `base_headers` | INPUT | No | DataType.DICT |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `headers` | OUTPUT | DataType.DICT |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `auth_type` | CHOICE | `Bearer` | No | Type of authentication (Bearer, Basic, or API Key) Choices: Bearer, Basic, ApiKey |
| `api_key_name` | STRING | `X-API-Key` | No | Header name for API key authentication |

## Inheritance

Extends: `CredentialAwareMixin`, `BaseNode`
