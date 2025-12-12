# HTTP Nodes

HTTP nodes enable REST API integration, file transfers, authentication, and web service communication. All HTTP nodes use the `UnifiedHttpClient` for connection pooling, rate limiting, and circuit breaker protection.

## Overview

| Node | Description |
|------|-------------|
| [HttpRequestNode](#httprequestnode) | Generic HTTP request (GET, POST, PUT, PATCH, DELETE) |
| [SetHttpHeadersNode](#sethttpheadersnode) | Configure headers for requests |
| [ParseJsonResponseNode](#parsejsonresponsenode) | Parse and extract JSON data |
| [HttpDownloadFileNode](#httpdownloadfilenode) | Download files from URLs |
| [HttpUploadFileNode](#httpuploadfilenode) | Upload files via HTTP |
| [BuildUrlNode](#buildurlnode) | Construct URLs with query parameters |
| [HttpAuthNode](#httpauthnode) | Configure authentication (Bearer, Basic, API Key) |
| [OAuth2AuthorizeNode](#oauth2authorizenode) | Generate OAuth 2.0 authorization URLs |
| [OAuth2TokenExchangeNode](#oauth2tokenexchangenode) | Exchange auth codes for tokens |
| [OAuth2CallbackServerNode](#oauth2callbackservernode) | Receive OAuth callbacks |
| [OAuth2TokenValidateNode](#oauth2tokenvalidatenode) | Validate tokens via introspection |

---

## HttpRequestNode

Generic HTTP request node supporting all standard HTTP methods.

### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `url` | STRING | (required) | Target URL for the request |
| `method` | CHOICE | `GET` | HTTP method: GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS |
| `headers` | JSON | `{}` | Request headers as JSON object |
| `body` | STRING | `""` | Request body (for POST, PUT, PATCH) |
| `params` | JSON | `{}` | URL query parameters |
| `timeout` | FLOAT | `30.0` | Request timeout in seconds |
| `verify_ssl` | BOOLEAN | `true` | Verify SSL certificates |
| `follow_redirects` | BOOLEAN | `true` | Follow HTTP redirects |
| `max_redirects` | INTEGER | `10` | Maximum redirects to follow |
| `content_type` | STRING | `application/json` | Content-Type header |
| `proxy` | STRING | `""` | Proxy URL (optional) |
| `retry_count` | INTEGER | `0` | Number of retry attempts |
| `retry_delay` | FLOAT | `1.0` | Delay between retries (seconds) |
| `response_encoding` | STRING | `""` | Force response encoding |

### Ports

**Inputs:**
- `url` (STRING) - Target URL
- `method` (STRING) - HTTP method override
- `headers` (DICT) - Headers override
- `body` (ANY) - Request body
- `params` (DICT) - Query parameters
- `timeout` (FLOAT) - Timeout override

**Outputs:**
- `response_body` (STRING) - Raw response body
- `response_json` (ANY) - Parsed JSON response
- `status_code` (INTEGER) - HTTP status code
- `response_headers` (DICT) - Response headers
- `success` (BOOLEAN) - Request success status
- `error` (STRING) - Error message if failed

### Example: REST API Call

```python
# GET request to fetch user data
http_request = HttpRequestNode(
    node_id="get_user",
    config={
        "url": "https://api.example.com/users/{{user_id}}",
        "method": "GET",
        "headers": {"Authorization": "Bearer {{api_token}}"},
        "timeout": 30.0
    }
)

# POST request with JSON body
create_user = HttpRequestNode(
    node_id="create_user",
    config={
        "url": "https://api.example.com/users",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": '{"name": "{{user_name}}", "email": "{{email}}"}'
    }
)
```

---

## SetHttpHeadersNode

Configure HTTP headers for subsequent requests.

### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `header_name` | STRING | `""` | Single header name |
| `header_value` | STRING | `""` | Single header value |
| `headers_json` | JSON | `{}` | Multiple headers as JSON |

### Ports

**Inputs:**
- `base_headers` (DICT) - Existing headers to extend
- `header_name` (STRING) - Header name override
- `header_value` (STRING) - Header value override
- `headers_json` (DICT) - JSON headers override

**Outputs:**
- `headers` (DICT) - Combined headers

### Example

```python
# Set multiple headers
set_headers = SetHttpHeadersNode(
    node_id="set_headers",
    config={
        "headers_json": {
            "X-API-Version": "2.0",
            "Accept-Language": "en-US",
            "Cache-Control": "no-cache"
        }
    }
)
```

---

## ParseJsonResponseNode

Parse JSON response and extract data using JSONPath-like expressions.

### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `path` | STRING | `""` | Path to extract (e.g., `data.users[0].name`) |
| `default` | STRING | `""` | Default value if path not found |

### Ports

**Inputs:**
- `json_data` (ANY) - JSON string or dict to parse
- `path` (STRING) - Path override
- `default` (ANY) - Default value override

**Outputs:**
- `value` (ANY) - Extracted value
- `success` (BOOLEAN) - Extraction success
- `error` (STRING) - Error message if failed

### Example

```python
# Extract nested data from API response
parse_json = ParseJsonResponseNode(
    node_id="extract_data",
    config={
        "path": "data.results[0].id",
        "default": "not_found"
    }
)
```

---

## HttpDownloadFileNode

Download files from URLs with streaming support.

### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `url` | STRING | (required) | URL to download from |
| `save_path` | FILE_PATH | (required) | Local path to save file |
| `headers` | JSON | `{}` | Request headers |
| `timeout` | FLOAT | `300.0` | Download timeout (seconds) |
| `overwrite` | BOOLEAN | `true` | Overwrite existing file |
| `verify_ssl` | BOOLEAN | `true` | Verify SSL certificates |
| `proxy` | STRING | `""` | Proxy URL |
| `retry_count` | INTEGER | `0` | Retry attempts |
| `retry_delay` | FLOAT | `2.0` | Delay between retries |
| `chunk_size` | INTEGER | `8192` | Download chunk size (bytes) |

### Ports

**Inputs:**
- `url` (STRING) - Download URL
- `save_path` (STRING) - Save path override
- `headers` (DICT) - Headers override
- `timeout` (FLOAT) - Timeout override
- `allow_internal_urls` (BOOLEAN) - Allow internal URLs

**Outputs:**
- `file_path` (STRING) - Downloaded file path
- `file_size` (INTEGER) - File size in bytes
- `success` (BOOLEAN) - Download success
- `error` (STRING) - Error message

### Example

```python
# Download a PDF report
download = HttpDownloadFileNode(
    node_id="download_report",
    config={
        "url": "https://reports.example.com/{{report_id}}.pdf",
        "save_path": "C:\\Downloads\\report_{{report_id}}.pdf",
        "timeout": 60.0,
        "overwrite": True
    }
)
```

---

## HttpUploadFileNode

Upload files via HTTP POST multipart/form-data.

### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `url` | STRING | (required) | Upload endpoint URL |
| `file_path` | FILE_PATH | (required) | File to upload |
| `field_name` | STRING | `file` | Form field name |
| `headers` | JSON | `{}` | Additional headers |
| `extra_fields` | JSON | `{}` | Extra form fields |
| `timeout` | FLOAT | `300.0` | Upload timeout |
| `verify_ssl` | BOOLEAN | `true` | Verify SSL |
| `retry_count` | INTEGER | `0` | Retry attempts |
| `retry_delay` | FLOAT | `2.0` | Delay between retries |

### Ports

**Inputs:**
- `url` (STRING) - Upload URL
- `file_path` (STRING) - File path override
- `field_name` (STRING) - Field name override
- `headers` (DICT) - Headers override
- `extra_fields` (DICT) - Extra fields override
- `timeout` (FLOAT) - Timeout override

**Outputs:**
- `response_body` (STRING) - Response body
- `response_json` (ANY) - Parsed JSON response
- `status_code` (INTEGER) - HTTP status code
- `success` (BOOLEAN) - Upload success
- `error` (STRING) - Error message

### Example

```python
# Upload a document
upload = HttpUploadFileNode(
    node_id="upload_doc",
    config={
        "url": "https://api.example.com/upload",
        "file_path": "C:\\Documents\\report.pdf",
        "field_name": "document",
        "extra_fields": {"description": "Monthly report"}
    }
)
```

---

## BuildUrlNode

Build URLs with query parameters.

### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `base_url` | STRING | (required) | Base URL |
| `path` | STRING | `""` | Path to append |
| `params` | JSON | `{}` | Query parameters |

### Ports

**Inputs:**
- `base_url` (STRING) - Base URL override
- `path` (STRING) - Path override
- `params` (DICT) - Parameters override

**Outputs:**
- `url` (STRING) - Complete URL with parameters

### Example

```python
# Build API URL with query parameters
build_url = BuildUrlNode(
    node_id="build_search_url",
    config={
        "base_url": "https://api.example.com",
        "path": "/search",
        "params": {
            "q": "{{search_term}}",
            "limit": 50,
            "offset": "{{page_offset}}"
        }
    }
)
# Result: https://api.example.com/search?q=test&limit=50&offset=0
```

---

## HttpAuthNode

Configure HTTP authentication headers.

### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `credential_name` | STRING | `""` | Vault credential name |
| `auth_type` | CHOICE | `Bearer` | Auth type: Bearer, Basic, ApiKey |
| `token` | STRING | `""` | Bearer token or API key |
| `username` | STRING | `""` | Username (Basic auth) |
| `password` | STRING | `""` | Password (Basic auth) |
| `api_key_name` | STRING | `X-API-Key` | API key header name |

### Credential Resolution Order

1. Vault lookup (via `credential_name`)
2. Direct parameters (`token`, `username`, `password`)
3. Environment variables (`HTTP_TOKEN`, `HTTP_USERNAME`, `HTTP_PASSWORD`)

### Ports

**Inputs:**
- `credential_name` (STRING) - Credential alias
- `auth_type` (STRING) - Authentication type
- `token` (STRING) - Token override
- `username` (STRING) - Username override
- `password` (STRING) - Password override
- `api_key_name` (STRING) - Header name override
- `base_headers` (DICT) - Existing headers

**Outputs:**
- `headers` (DICT) - Headers with authentication

### Example

```python
# Bearer token authentication
bearer_auth = HttpAuthNode(
    node_id="bearer_auth",
    config={
        "auth_type": "Bearer",
        "token": "{{api_token}}"
    }
)

# Basic authentication
basic_auth = HttpAuthNode(
    node_id="basic_auth",
    config={
        "auth_type": "Basic",
        "username": "{{username}}",
        "password": "{{password}}"
    }
)

# API Key authentication
api_key_auth = HttpAuthNode(
    node_id="api_auth",
    config={
        "auth_type": "ApiKey",
        "token": "{{api_key}}",
        "api_key_name": "X-Custom-API-Key"
    }
)
```

---

## OAuth2AuthorizeNode

Build OAuth 2.0 authorization URL for user authentication.

### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `client_id` | STRING | `""` | OAuth client ID |
| `auth_url` | STRING | `""` | Authorization endpoint URL |
| `scope` | STRING | `""` | OAuth scopes (space-separated) |
| `redirect_uri` | STRING | `http://localhost:8080/callback` | Callback URL |
| `state` | STRING | `""` | CSRF state (auto-generated if empty) |
| `response_type` | CHOICE | `code` | Flow type: code, token |
| `pkce_enabled` | BOOLEAN | `true` | Enable PKCE security |

### Ports

**Inputs:**
- `client_id` (STRING) - Client ID override
- `auth_url` (STRING) - Auth URL override
- `scope` (STRING) - Scope override
- `redirect_uri` (STRING) - Redirect URI override
- `extra_params` (DICT) - Extra parameters

**Outputs:**
- `auth_url` (STRING) - Complete authorization URL
- `state` (STRING) - State for CSRF verification
- `code_verifier` (STRING) - PKCE code verifier
- `code_challenge` (STRING) - PKCE code challenge

### Example

```python
# Generate OAuth authorization URL
oauth_auth = OAuth2AuthorizeNode(
    node_id="oauth_start",
    config={
        "client_id": "{{client_id}}",
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "scope": "openid email profile",
        "redirect_uri": "http://localhost:8080/callback",
        "pkce_enabled": True
    }
)
```

---

## OAuth2TokenExchangeNode

Exchange authorization code for access tokens.

### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `client_id` | STRING | `""` | OAuth client ID |
| `client_secret` | STRING | `""` | Client secret |
| `token_url` | STRING | `""` | Token endpoint URL |
| `redirect_uri` | STRING | `http://localhost:8080/callback` | Callback URL |
| `grant_type` | CHOICE | `authorization_code` | Grant type |

### Grant Types

- `authorization_code` - Standard code exchange
- `client_credentials` - Server-to-server
- `refresh_token` - Refresh expired tokens
- `password` - Resource owner password (legacy)

### Ports

**Inputs:**
- `code` (STRING) - Authorization code
- `code_verifier` (STRING) - PKCE verifier
- `refresh_token` (STRING) - Refresh token
- `username` (STRING) - Username (password flow)
- `password` (STRING) - Password (password flow)
- `scope` (STRING) - Scope override

**Outputs:**
- `access_token` (STRING) - Access token
- `refresh_token` (STRING) - Refresh token
- `token_type` (STRING) - Token type (Bearer)
- `expires_in` (INTEGER) - Token lifetime (seconds)
- `scope` (STRING) - Granted scope
- `id_token` (STRING) - ID token (OIDC)
- `full_response` (DICT) - Complete response

### Example

```python
# Exchange authorization code for tokens
token_exchange = OAuth2TokenExchangeNode(
    node_id="exchange_token",
    config={
        "client_id": "{{client_id}}",
        "client_secret": "{{client_secret}}",
        "token_url": "https://oauth2.googleapis.com/token",
        "grant_type": "authorization_code"
    }
)
```

---

## OAuth2CallbackServerNode

Start a local server to receive OAuth callbacks.

### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `port` | INTEGER | `8080` | Local port (1024-65535) |
| `timeout` | INTEGER | `120` | Wait timeout (seconds) |
| `path` | STRING | `/callback` | Callback URL path |

### Ports

**Inputs:**
- `expected_state` (STRING) - Expected state for CSRF verification

**Outputs:**
- `code` (STRING) - Authorization code
- `state` (STRING) - Received state
- `access_token` (STRING) - Access token (implicit flow)
- `error` (STRING) - OAuth error
- `error_description` (STRING) - Error description

---

## OAuth2TokenValidateNode

Validate access tokens using RFC 7662 introspection.

### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `introspection_url` | STRING | `""` | Introspection endpoint |
| `client_id` | STRING | `""` | Client ID |
| `client_secret` | STRING | `""` | Client secret |

### Ports

**Inputs:**
- `token` (STRING) - Access token to validate

**Outputs:**
- `active` (BOOLEAN) - Token is active
- `client_id` (STRING) - Token's client ID
- `username` (STRING) - Resource owner
- `scope` (STRING) - Token scope
- `expires_at` (INTEGER) - Expiration timestamp
- `token_type` (STRING) - Token type
- `full_response` (DICT) - Complete response

---

## Best Practices

### Connection Pooling

All HTTP nodes use `UnifiedHttpClient` which provides:
- Connection pooling and reuse
- Per-domain rate limiting
- Circuit breaker protection
- SSRF protection

### Error Handling

```python
# Chain HTTP request with error handling
http_request = HttpRequestNode(
    node_id="api_call",
    config={"url": "https://api.example.com/data"}
)

# Check success output before proceeding
# success output is False if request failed
# error output contains the error message
```

### Security

> **Warning:** Never hardcode credentials. Use:
> - Credential vault lookup via `credential_name`
> - Environment variables
> - Variable placeholders (`{{token}}`)

### Retry Strategy

For unreliable APIs, configure retries:

```python
http_request = HttpRequestNode(
    node_id="unreliable_api",
    config={
        "url": "https://flaky-api.example.com/data",
        "retry_count": 3,
        "retry_delay": 2.0,
        "timeout": 30.0
    }
)
```

## Related Documentation

- [Variable Nodes](variable.md) - Store and manage API responses
- [Data Operations](data-operations.md) - Process JSON data
- [Control Flow](control-flow.md) - Handle API errors
