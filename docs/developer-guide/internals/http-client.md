# HTTP Client Internals

This document describes CasareRPA's UnifiedHttpClient for resilient HTTP operations.

## Overview

The UnifiedHttpClient is a facade composing multiple resilience patterns:
- Connection pooling via HttpSessionPool
- Exponential backoff retry
- Per-domain rate limiting
- Per-base-URL circuit breaker
- SSRF protection

**Location:** `src/casare_rpa/infrastructure/http/unified_http_client.py`

## Architecture

```
UnifiedHttpClient
    |
    +-> HttpSessionPool         - Connection reuse
    +-> RetryConfig             - Exponential backoff
    +-> SlidingWindowRateLimiter - Per-domain rate limiting
    +-> CircuitBreaker          - Failure isolation
    +-> SSRF Protection         - Security validation
```

## Basic Usage

### Context Manager (Preferred)

```python
from casare_rpa.infrastructure.http import UnifiedHttpClient

async with UnifiedHttpClient() as client:
    response = await client.get("https://api.example.com/data")
    data = await response.json()
```

### Manual Lifecycle

```python
from casare_rpa.infrastructure.http import (
    UnifiedHttpClient,
    UnifiedHttpClientConfig,
)

config = UnifiedHttpClientConfig(max_retries=5)
client = UnifiedHttpClient(config)

await client.start()
try:
    response = await client.post(
        "https://api.example.com/submit",
        json={"key": "value"}
    )
finally:
    await client.close()
```

### Singleton Instance

```python
from casare_rpa.infrastructure.http import (
    get_unified_http_client,
    close_unified_http_client,
)

# Get shared instance (creates if needed)
client = await get_unified_http_client()

response = await client.get("https://api.example.com/data")

# On app shutdown
await close_unified_http_client()
```

---

## Configuration

### UnifiedHttpClientConfig

```python
from casare_rpa.infrastructure.http import UnifiedHttpClientConfig

config = UnifiedHttpClientConfig(
    # Session pool settings
    max_sessions=10,              # Max concurrent sessions
    max_connections_per_host=10,  # Connections per host
    session_max_age=300.0,        # Session lifetime (seconds)
    session_idle_timeout=60.0,    # Idle timeout

    # Request defaults
    default_timeout=30.0,         # Request timeout
    connect_timeout=10.0,         # Connection timeout

    # Retry settings
    max_retries=3,
    retry_initial_delay=1.0,      # First retry delay
    retry_max_delay=30.0,         # Max retry delay
    retry_backoff_multiplier=2.0, # Exponential multiplier
    retry_jitter=True,            # Add randomization

    # Rate limiting (per domain)
    rate_limit_requests=10,       # Requests per window
    rate_limit_window=1.0,        # Window size (seconds)
    rate_limit_max_wait=60.0,     # Max wait before exception

    # Circuit breaker (per base URL)
    circuit_failure_threshold=5,  # Failures before open
    circuit_success_threshold=2,  # Successes to close
    circuit_timeout=60.0,         # Time in open state

    # Headers
    user_agent="CasareRPA/1.0",
    default_headers={},

    # SSRF Protection
    enable_ssrf_protection=True,
    allow_private_ips=False,
    additional_blocked_hosts=None,
)
```

---

## HTTP Methods

### GET Request

```python
response = await client.get(
    "https://api.example.com/users",
    headers={"Authorization": "Bearer token"},
    timeout=10.0,
)

# Read response
status = response.status
data = await response.json()
text = await response.text()
```

### POST Request

```python
# JSON body
response = await client.post(
    "https://api.example.com/users",
    json={"name": "John", "email": "john@example.com"},
)

# Form data
response = await client.post(
    "https://api.example.com/upload",
    data={"file": open("document.pdf", "rb")},
)
```

### Other Methods

```python
# PUT
response = await client.put(url, json=data)

# PATCH
response = await client.patch(url, json=partial_data)

# DELETE
response = await client.delete(url)

# HEAD
response = await client.head(url)

# OPTIONS
response = await client.options(url)
```

---

## Retry Logic

### Automatic Retry

Requests are automatically retried for:
- HTTP status codes: 429, 500, 502, 503, 504
- Network errors: connection refused, timeout
- Transient failures

```python
# Retry behavior
response = await client.get(
    "https://api.example.com/data",
    retry_count=5,  # Override default retries
)
```

### Retry Configuration

```python
from casare_rpa.utils.resilience.retry import RetryConfig

# Built internally:
retry_config = RetryConfig(
    max_attempts=3,
    initial_delay=1.0,
    max_delay=30.0,
    backoff_multiplier=2.0,
    jitter=True,
)

# Delay calculation:
# Attempt 1 failed: delay = 1.0 * (1 + random(0, 0.1))
# Attempt 2 failed: delay = 2.0 * (1 + random(0, 0.1))
# Attempt 3 failed: delay = 4.0 * (1 + random(0, 0.1))
```

### Retryable Status Codes

```python
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}
```

---

## Circuit Breaker

### Pattern

The circuit breaker prevents repeated failures by "opening" when a service is unhealthy:

```
CLOSED (normal operation)
    |
    +-- failure_threshold reached --> OPEN (fail fast)
                                        |
                                        +-- timeout elapsed --> HALF_OPEN
                                                                    |
                                                    success --> CLOSED
                                                    failure --> OPEN
```

### Per-Base-URL Isolation

Each base URL gets its own circuit breaker:

```python
# These use different circuit breakers:
await client.get("https://api.example.com/users")    # Circuit A
await client.get("https://api.example.com/products") # Circuit A (same)
await client.get("https://other.com/data")           # Circuit B (different)
```

### Circuit Breaker Error

```python
from casare_rpa.robot.circuit_breaker import CircuitBreakerOpenError

try:
    response = await client.get(url)
except CircuitBreakerOpenError as e:
    # Service is unavailable, fail fast
    logger.warning(f"Circuit open for {url}: {e}")
```

### Skip Circuit Breaker

```python
# For critical requests that must be attempted
response = await client.get(
    url,
    skip_circuit_breaker=True,
)
```

---

## Rate Limiting

### Per-Domain Limiting

Rate limits are applied per domain to prevent API throttling:

```python
# All requests to api.example.com share the same rate limiter
await client.get("https://api.example.com/users")
await client.get("https://api.example.com/products")

# Different domain, different limiter
await client.get("https://other.com/data")
```

### Sliding Window Algorithm

```python
from casare_rpa.utils.resilience.rate_limiter import SlidingWindowRateLimiter

limiter = SlidingWindowRateLimiter(
    max_requests=10,      # 10 requests
    window_seconds=1.0,   # per second
    max_wait_time=60.0,   # max wait before exception
)

# Internally:
# - Tracks request timestamps in sliding window
# - If limit exceeded, waits until slot available
# - Raises RateLimitExceeded if wait exceeds max_wait_time
```

### Skip Rate Limiting

```python
# For burst operations
response = await client.get(
    url,
    skip_rate_limit=True,
)

# Custom rate limit key
response = await client.get(
    url,
    rate_limit_key="custom_bucket",
)
```

### Rate Limit Error

```python
from casare_rpa.utils.resilience.rate_limiter import RateLimitExceeded

try:
    response = await client.get(url)
except RateLimitExceeded as e:
    logger.warning(f"Rate limited: {e}")
```

---

## SSRF Protection

### Security Validation

All URLs are validated against SSRF attacks:

```python
# Allowed schemes
ALLOWED_URL_SCHEMES = {"http", "https"}

# Blocked hosts
BLOCKED_HOSTS = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "[::1]",
    "::1",
}

# Blocked IP ranges
BLOCKED_IP_RANGES = [
    "127.0.0.0/8",      # Loopback
    "10.0.0.0/8",       # Private Class A
    "172.16.0.0/12",    # Private Class B
    "192.168.0.0/16",   # Private Class C
    "169.254.0.0/16",   # Link-local / AWS metadata
    # IPv6 equivalents...
]
```

### Allow Internal Networks

```python
# For internal services
config = UnifiedHttpClientConfig(
    enable_ssrf_protection=True,
    allow_private_ips=True,  # Allow 10.x, 192.168.x, etc.
)
```

### Blocked Request Error

```python
try:
    response = await client.get("http://localhost:8080/admin")
except ValueError as e:
    # "SSRF Protection: Blocked host 'localhost'"
    pass
```

---

## Statistics and Monitoring

### Request Statistics

```python
stats = client.stats

print(f"Total requests: {stats.total_requests}")
print(f"Successful: {stats.successful_requests}")
print(f"Failed: {stats.failed_requests}")
print(f"Retried: {stats.retried_requests}")
print(f"Rate limited: {stats.rate_limited_requests}")
print(f"Circuit broken: {stats.circuit_broken_requests}")
print(f"Success rate: {stats.success_rate}%")
print(f"Total retry delay: {stats.total_retry_delay_ms}ms")
```

### Component Stats

```python
# Session pool stats
pool_stats = client.get_pool_stats()

# Rate limiter stats per domain
rate_stats = client.get_rate_limiter_stats()

# Circuit breaker status per base URL
circuit_status = client.get_circuit_breaker_status()

# All combined
all_stats = client.get_all_stats()
```

---

## Connection Pooling

### HttpSessionPool

**Location:** `src/casare_rpa/utils/pooling/http_session_pool.py`

Manages aiohttp ClientSession instances:

```python
class HttpSessionPool:
    def __init__(
        self,
        max_sessions: int = 10,
        max_connections_per_host: int = 10,
        max_session_age: float = 300.0,
        idle_timeout: float = 60.0,
    ):
        # Sessions are reused for connection keep-alive
        # Old sessions are recycled based on age/idle time
```

### Benefits

- **Connection Reuse**: TCP connections kept alive
- **DNS Caching**: Avoids repeated DNS lookups
- **Memory Efficiency**: Shared session pool
- **Graceful Recycling**: Old sessions replaced automatically

---

## Error Handling

### Exception Types

| Exception | Cause | Retryable |
|-----------|-------|-----------|
| `aiohttp.ClientError` | Network error | Yes |
| `asyncio.TimeoutError` | Request timeout | Yes |
| `RateLimitExceeded` | Rate limit wait exceeded | No |
| `CircuitBreakerOpenError` | Circuit is open | No |
| `ValueError` | SSRF protection blocked | No |

### Error Handling Pattern

```python
from casare_rpa.robot.circuit_breaker import CircuitBreakerOpenError
from casare_rpa.utils.resilience.rate_limiter import RateLimitExceeded

try:
    response = await client.get(url)
    if response.status >= 400:
        # Handle HTTP error
        logger.error(f"HTTP {response.status}")
except CircuitBreakerOpenError:
    # Service unavailable, use fallback
    pass
except RateLimitExceeded:
    # Rate limited, queue for later
    pass
except ValueError as e:
    # SSRF protection or invalid URL
    pass
except Exception as e:
    # Network error after retries
    logger.error(f"Request failed: {e}")
```

---

## Integration with Nodes

### HTTP Nodes Pattern

```python
from casare_rpa.infrastructure.http import get_unified_http_client

class HttpGetNode(BaseNode):
    async def execute(self, context):
        client = await get_unified_http_client()

        url = self.get_input_value("url")
        # MODERN: Use get_parameter() for optional config values
        headers = self.get_parameter("headers", {})
        timeout = self.get_parameter("timeout", 30.0)

        try:
            response = await client.get(
                url,
                headers=headers,
                timeout=timeout,
            )

            data = await response.json()
            self.set_output_value("response", data)
            self.set_output_value("status_code", response.status)

            return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}
```

---

## Best Practices

### 1. Use Singleton for Shared Operations

```python
# Node execution (shared client)
client = await get_unified_http_client()

# NOT: UnifiedHttpClient() in each node
```

### 2. Configure Appropriately for API

```python
# For APIs with strict rate limits
config = UnifiedHttpClientConfig(
    rate_limit_requests=5,
    rate_limit_window=1.0,
)

# For reliable internal services
config = UnifiedHttpClientConfig(
    enable_ssrf_protection=False,
    allow_private_ips=True,
    circuit_failure_threshold=10,
)
```

### 3. Handle Circuit Breaker States

```python
# Check circuit status before critical operations
status = client.get_circuit_breaker_status()
if status.get(base_url, {}).get("state") == "open":
    # Use fallback strategy
    pass
```

### 4. Monitor Statistics

```python
# Log stats periodically
stats = client.stats
if stats.success_rate < 90:
    logger.warning(f"Low success rate: {stats.success_rate}%")
```

---

## Related Documentation

- [Execution Engine](execution-engine.md) - Workflow execution
- [Error Codes Reference](../../reference/error-codes.md) - HTTP error codes
