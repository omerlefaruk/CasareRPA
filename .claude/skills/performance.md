# Performance Skill

Optimize code for performance using async patterns, caching, and connection pooling.

## MCP-First Workflow

1. **codebase** - Search for performance patterns
   ```python
   search_codebase("async performance patterns caching", top_k=10)
   ```

2. **filesystem** - view_file the code to optimize
   ```python
   read_file("src/module.py")
   ```

3. **git** - Check for performance-related changes
   ```python
   git_diff("HEAD~10..HEAD", path="src/")
   ```

## Optimization Techniques

### Async Patterns
```python
# BEFORE (blocking)
def fetch_data(url):
    response = requests.get(url)
    return response.json()

# AFTER (async)
async def fetch_data(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        return resp.json()
```

### Caching
```python
from functools import lru_cache
from typing import Optional

@lru_cache(maxsize=128)
def expensive_computation(input: str) -> dict:
    # Expensive operation
    return result
```

### Connection Pooling
```python
async with httpx.AsyncClient(
    limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
) as client:
    # Reuse connection
    pass
```

## Common Optimizations

| Issue | Solution |
|-------|----------|
| Blocking I/O | Convert to async with `httpx.AsyncClient` |
| Repeated computation | Add `@lru_cache` or use Redis cache |
| N+1 queries | Batch queries or use `asyncio.gather()` |
| Large data transfers | Stream data, use pagination |
| Slow regex | Compile patterns with `re.compile()` |

## Metrics to Track

- Response time (latency)
- Throughput (requests/second)
- Memory usage
- Database query count
- Cache hit rate

## Example Usage

```python
Skill(skill="performance", prompt="""
Optimize the API client for better performance:

1. codebase: Search for "async httpx connection pooling patterns"
2. filesystem: Read src/casare_rpa/infrastructure/clients/api.py
3. git: Check recent performance issues

Apply:
- Add async/await patterns
- Implement connection pooling
- Add caching where appropriate
""")
```
