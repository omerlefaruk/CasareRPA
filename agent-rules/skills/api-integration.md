# API Integration Skill

Guide for integrating external APIs and services.

## HTTP Client

Use `UnifiedHttpClient` for all HTTP requests:

```python
from casare_rpa.infrastructure.http import UnifiedHttpClient

async with UnifiedHttpClient() as client:
    response = await client.post(
        "https://api.example.com/endpoint",
        json={"key": "value"},
        headers={"Authorization": f"Bearer {token}"}
    )
    data = response.json()
```

## Authentication Patterns

### API Key
```python
headers = {"X-API-Key": api_key}
```

### Bearer Token
```python
headers = {"Authorization": f"Bearer {token}"}
```

### OAuth2
```python
from casare_rpa.infrastructure.auth import OAuth2Client
client = OAuth2Client(client_id, client_secret)
token = await client.get_access_token()
```

## Error Handling

```python
from httpx import HTTPStatusError, TimeoutException

try:
    response = await client.get(url)
    response.raise_for_status()
except HTTPStatusError as e:
    logger.error(f"HTTP {e.response.status_code}: {e.response.text}")
except TimeoutException:
    logger.error("Request timed out")
```

## Rate Limiting

```python
# Built into UnifiedHttpClient
client = UnifiedHttpClient(
    rate_limit=100,  # requests per minute
    retry_count=3
)
```

## Response Handling

```python
# JSON
data = response.json()

# Text
text = response.text

# Binary
content = response.content

# Streaming
async for chunk in response.aiter_bytes():
    process(chunk)
```

## Best Practices

1. Always use async HTTP clients
2. Handle errors gracefully
3. Implement retry logic
4. Respect rate limits
5. Log requests for debugging
6. Use environment variables for secrets
