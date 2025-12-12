# REST API Integration Tutorial

Learn to interact with REST APIs: make HTTP requests, parse JSON responses, handle authentication, and implement error handling.

**Time required:** 25 minutes

**What you will build:**
A workflow that fetches data from a public API, processes the response, posts data to another endpoint, and handles common API errors.

## Prerequisites

- CasareRPA installed and running
- Internet connection
- Basic understanding of REST APIs and JSON

## Goals

By the end of this tutorial, you will:
- Make GET, POST, PUT, and DELETE requests
- Handle API authentication (API keys, OAuth)
- Parse JSON responses
- Handle pagination
- Implement retry logic for transient failures
- Log API interactions

---

## Step 1: Create New Workflow

1. Open CasareRPA Canvas
2. **File** > **New Workflow**
3. Save as `api_integration_tutorial.json`

---

## Step 2: Add Start Node

1. Drag **Start** from **Basic** to position (100, 300)

---

## Part 1: Simple GET Request

### Step 3: Make a GET Request

We'll use the JSONPlaceholder API (free test API).

1. Drag **HTTP Request** from **HTTP** category
2. Position at (400, 300)
3. Connect: Start -> HTTP Request

### Configure HTTP Request (GET)

| Property | Value |
|----------|-------|
| method | `GET` |
| url | `https://jsonplaceholder.typicode.com/posts/1` |
| timeout | `30000` |

### Output Ports

- `response_body` (ANY) - Parsed JSON response
- `status_code` (INTEGER) - HTTP status code
- `headers` (DICT) - Response headers
- `success` (BOOLEAN) - Request succeeded

---

## Step 4: Check Response Status

1. Drag **If** from **Control Flow**
2. Position at (700, 300)
3. Connect: HTTP Request -> If

### Configure If Node

| Property | Value |
|----------|-------|
| expression | `{{status_code}} == 200` |

---

## Step 5: Handle Success

For the `true` branch:

1. Drag **Log** from **Basic**
2. Connect: If `true` -> Log

| Property | Value |
|----------|-------|
| message | `Received post: {{response_body.title}}` |
| level | `info` |

---

## Step 6: Handle Error

For the `false` branch:

1. Drag **Log** from **Basic**
2. Connect: If `false` -> Log

| Property | Value |
|----------|-------|
| message | `API error: Status {{status_code}}` |
| level | `error` |

---

## Part 2: POST Request with JSON Body

### Step 7: Prepare Request Data

1. Drag **Create Dict** from **Data Operations**
2. Position at (400, 500)

### Build the Request Body

```
[Create Dict]
    |
[Dict Set: title]
    value: "My New Post"
    |
[Dict Set: body]
    value: "This is the post content created by CasareRPA"
    |
[Dict Set: userId]
    value: 1
    |
    +---> post_data
```

---

## Step 8: Make POST Request

1. Drag **HTTP Request** from **HTTP**
2. Position at (1000, 500)

### Configure HTTP Request (POST)

| Property | Value |
|----------|-------|
| method | `POST` |
| url | `https://jsonplaceholder.typicode.com/posts` |
| headers | `{"Content-Type": "application/json"}` |
| timeout | `30000` |

Connect `post_data` to the `body` input port.

### Expected Response

```json
{
  "id": 101,
  "title": "My New Post",
  "body": "This is the post content created by CasareRPA",
  "userId": 1
}
```

---

## Step 9: Extract Created ID

1. Drag **Dict Get** from **Data Operations**
2. Position at (1300, 500)

| Property | Value |
|----------|-------|
| key | `id` |

Connect `response_body` from POST request.

### Store ID

1. Drag **Set Variable**

| Property | Value |
|----------|-------|
| name | `created_id` |

---

## Part 3: API Authentication

### Method 1: API Key in Header

```
[HTTP Request]
    method: "GET"
    url: "https://api.example.com/data"
    headers: {"X-API-Key": "{{api_key}}"}
```

### Method 2: API Key in Query Parameter

```
[HTTP Request]
    method: "GET"
    url: "https://api.example.com/data?api_key={{api_key}}"
```

### Method 3: Bearer Token (OAuth)

```
[HTTP Request]
    method: "GET"
    url: "https://api.example.com/data"
    headers: {"Authorization": "Bearer {{access_token}}"}
```

### Method 4: Basic Authentication

```
[HTTP Request]
    method: "GET"
    url: "https://api.example.com/data"
    auth_type: "basic"
    auth_username: "{{username}}"
    auth_password: "{{password}}"
```

---

## Part 4: OAuth 2.0 Flow

### Step 10: Get Access Token

```
[HTTP Request]
    method: "POST"
    url: "https://oauth.example.com/token"
    headers: {"Content-Type": "application/x-www-form-urlencoded"}
    body: "grant_type=client_credentials&client_id={{client_id}}&client_secret={{client_secret}}"
        |
        +---> token_response

[Dict Get]
    dict: {{token_response}}
    key: "access_token"
        |
        +---> access_token

[Set Variable: access_token]
```

### Step 11: Use Access Token

```
[HTTP Request]
    method: "GET"
    url: "https://api.example.com/protected/resource"
    headers: {"Authorization": "Bearer {{access_token}}"}
```

---

## Part 5: Handling Pagination

Many APIs return paginated results. Here's how to fetch all pages:

### Step 12: Initialize Pagination Variables

```
[Set Variable: page]
    value: 1

[Set Variable: all_results]
    value: []

[Set Variable: has_more]
    value: true
```

### Step 13: Pagination Loop

```
[While Loop Start]
    expression: "{{has_more}} == true"
    max_iterations: 100
        |
      body
        |
    [HTTP Request]
        method: "GET"
        url: "https://api.example.com/items?page={{page}}&limit=100"
            |
            +---> response_body
            |
    [Dict Get: items]  # Extract items array
            |
    [List Append]  # Add to all_results
            |
    [If: items.length < 100]  # Check if last page
        |
      true --> [Set Variable: has_more = false]
      false --> [Math Operation: page + 1]
                    |
                [Set Variable: page]
        |
    [While Loop End]
        |
    completed
        |
[Log: "Fetched {{all_results.length}} total items"]
```

---

## Part 6: Error Handling and Retries

### Step 14: Retry on Transient Errors

Use the Retry node for handling transient failures:

```
[Retry]
    max_attempts: 3
    delay_ms: 1000
    backoff_multiplier: 2.0
        |
    retry_body
        |
    [HTTP Request]
        method: "GET"
        url: "https://api.example.com/data"
            |
    [If: status_code >= 500]  # Server error
        |
      true --> [Throw Error: "Server error"]  # Triggers retry
      false --> (continue)
        |
    [Retry End]
        |
    success --> [Process Response]
    failure --> [Log: "API unavailable after 3 attempts"]
```

### Retry Timing

| Attempt | Delay |
|---------|-------|
| 1 | 1000ms |
| 2 | 2000ms (1000 * 2) |
| 3 | 4000ms (2000 * 2) |

---

## Step 15: Handle Specific HTTP Status Codes

```
[HTTP Request]
    |
    +---> status_code
    |
[Switch]
    expression: "{{status_code}}"
    cases: [200, 201, 400, 401, 404, 500]
        |
    +---+---+---+---+---+---+
    |   |   |   |   |   |   |
  200 201 400 401 404 500 default
    |   |   |   |   |   |   |
[OK][Created][BadReq][Auth][NotFound][Server][Unknown]
```

### Status Code Handlers

| Status | Handler Action |
|--------|----------------|
| 200 | Process response normally |
| 201 | Log created resource ID |
| 400 | Log validation errors from response |
| 401 | Refresh token and retry |
| 404 | Log "Resource not found" |
| 429 | Wait and retry (rate limited) |
| 500+ | Retry with backoff |

---

## Part 7: Rate Limiting

### Step 16: Respect Rate Limits

```
[For Loop Start]
    items: {{items_to_process}}
        |
      body
        |
    [HTTP Request]
        |
    [Wait]
        seconds: 0.5  # 2 requests per second max
        |
    [For Loop End]
```

### Handle 429 Too Many Requests

```
[HTTP Request]
    |
[If: status_code == 429]
    |
  true
    |
[Dict Get: retry_after]  # From response headers
    default: 60
    |
[Wait]
    seconds: {{retry_after}}
    |
[HTTP Request]  # Retry the request
```

---

## Complete Workflow Example

### Fetch Users and Create Report

```
[Start]
    |
[Set Variable: api_base_url]
    value: "https://jsonplaceholder.typicode.com"
    |
[HTTP Request: GET /users]
    url: "{{api_base_url}}/users"
    |
[Set Variable: users]
    |
[For Loop Start]
    items: {{users}}
    item_var: "user"
        |
      body
        |
    [HTTP Request: GET /posts?userId=X]
        url: "{{api_base_url}}/posts?userId={{user.id}}"
            |
    [List Reduce: count]  # Count user's posts
            |
    [Dict Set: post_count]
        dict: {{user}}
            |
    [List Append: to enriched_users]
            |
    [Wait: 0.1]  # Rate limiting
            |
    [For Loop End]
        |
    completed
        |
[Write JSON]
    file_path: "C:\data\user_report.json"
    data: {{enriched_users}}
        |
[Log: "Report generated for {{users.length}} users"]
        |
[End]
```

---

## Working with Different Content Types

### JSON (Default)

```
[HTTP Request]
    headers: {"Content-Type": "application/json"}
    body: {"key": "value"}  # Automatically serialized
```

### Form Data

```
[HTTP Request]
    headers: {"Content-Type": "application/x-www-form-urlencoded"}
    body: "name=John&email=john@example.com"
```

### Multipart Form (File Upload)

```
[HTTP Request]
    method: "POST"
    url: "https://api.example.com/upload"
    content_type: "multipart/form-data"
    files: [{"field": "document", "path": "C:\\files\\report.pdf"}]
```

### XML

```
[HTTP Request]
    headers: {"Content-Type": "application/xml"}
    body: "<request><item>value</item></request>"
```

---

## Parsing Complex Responses

### Nested JSON

```json
{
  "data": {
    "users": [
      {"id": 1, "name": "Alice"},
      {"id": 2, "name": "Bob"}
    ],
    "metadata": {
      "total": 100,
      "page": 1
    }
  }
}
```

Extract users:

```
[Dict Get]
    key: "data.users"  # Use dot notation for nested access
        |
        +---> users_list
```

### Handle Missing Fields

```
[Dict Get]
    key: "optional_field"
    default: "N/A"  # Return default if missing
```

---

## Logging API Interactions

### Request/Response Logging

```
[Log]
    message: "API Request: {{method}} {{url}}"
    level: "debug"
    |
[HTTP Request]
    |
[Log]
    message: "API Response: {{status_code}} - {{response_body}}"
    level: "debug"
```

### Audit Trail

```
[Create Dict]
    |
[Dict Set: timestamp]
[Dict Set: method]
[Dict Set: url]
[Dict Set: status_code]
[Dict Set: response_time_ms]
    |
[List Append: to api_log]
```

---

## Best Practices

### 1. Use Variables for Base URLs

```
[Set Variable: api_base]
    value: "{{env.API_BASE_URL}}"

# Then use:
url: "{{api_base}}/endpoint"
```

### 2. Store Credentials Securely

```
[Get Credential]
    name: "api_service_key"
        |
        +---> api_key

# Never hardcode API keys in workflows
```

### 3. Set Appropriate Timeouts

| API Type | Timeout |
|----------|---------|
| Fast APIs | 10-15 seconds |
| Standard APIs | 30 seconds |
| Slow/Complex operations | 60-120 seconds |

### 4. Validate Responses

```
[If: response_body is None]
    |
  true --> [Throw Error: "Empty response"]

[If: response_body.error exists]
    |
  true --> [Throw Error: "{{response_body.error.message}}"]
```

### 5. Use Idempotency Keys

For POST requests that might be retried:

```
[HTTP Request]
    method: "POST"
    headers: {
        "Content-Type": "application/json",
        "Idempotency-Key": "{{unique_request_id}}"
    }
```

---

## Troubleshooting

### Connection Refused

**Causes:**
- Wrong URL/port
- API server down
- Firewall blocking

**Solutions:**
- Verify URL is correct
- Check API status page
- Test with curl/Postman first

### 401 Unauthorized

**Causes:**
- Invalid credentials
- Expired token
- Wrong authentication method

**Solutions:**
- Verify API key/token
- Refresh OAuth token
- Check authentication documentation

### 403 Forbidden

**Causes:**
- Insufficient permissions
- IP not whitelisted
- Rate limit exceeded

**Solutions:**
- Check API permissions
- Verify IP whitelist
- Implement rate limiting

### Timeout

**Causes:**
- Server slow to respond
- Large response payload
- Network issues

**Solutions:**
- Increase timeout
- Use pagination for large datasets
- Check network connectivity

---

## Node Reference

### HttpRequestNode

| Property | Type | Description |
|----------|------|-------------|
| method | CHOICE | GET/POST/PUT/PATCH/DELETE |
| url | STRING | Request URL |
| headers | JSON | Request headers |
| body | ANY | Request body |
| timeout | INTEGER | Timeout in ms |
| auth_type | CHOICE | none/basic/bearer |
| auth_username | STRING | Basic auth username |
| auth_password | STRING | Basic auth password |
| auth_token | STRING | Bearer token |
| follow_redirects | BOOLEAN | Follow 3xx redirects |
| verify_ssl | BOOLEAN | Verify SSL certificates |

### Output Ports

| Port | Type | Description |
|------|------|-------------|
| response_body | ANY | Parsed response |
| status_code | INTEGER | HTTP status |
| headers | DICT | Response headers |
| success | BOOLEAN | Request succeeded |
| elapsed_ms | INTEGER | Request duration |

---

## Next Steps

- [Data Processing](data-processing.md) - Process API responses
- [Error Handling](error-handling.md) - Handle API failures gracefully
- [Scheduled Workflows](scheduled-workflows.md) - Schedule API polling
- [Google Workspace](google-workspace.md) - Google API integration

---

## Summary

You learned how to:
1. Make GET, POST, PUT, DELETE requests
2. Handle API authentication (API keys, OAuth)
3. Parse JSON responses and extract data
4. Handle pagination for large datasets
5. Implement retry logic for transient failures
6. Respect rate limits
7. Log API interactions

API integration is essential for connecting CasareRPA to external services, databases, and cloud platforms.
