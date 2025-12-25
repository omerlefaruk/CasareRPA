---
name: performance
description: Performance optimization with async patterns, caching, and connection pooling
license: MIT
compatibility: opencode
metadata:
  audience: developers
  workflow: optimization
---

## What I do

- Optimize code for performance using async patterns
- Implement caching strategies (lru_cache, Redis)
- Configure connection pooling for HTTP clients
- Profile and measure performance improvements

## When to use me

Use this when you need to:
- Optimize slow API calls
- Add caching to expensive operations
- Configure connection pooling
- Profile code performance

## MCP-First Workflow

Always use MCP servers in this order:

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
    return requests.get(url).json()

# AFTER (async)
async def fetch_data(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        return (await client.get(url)).json()
```

### Caching
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_computation(input: str) -> dict:
    return result
```

### Connection Pooling
```python
async with httpx.AsyncClient(
    limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
) as client:
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
