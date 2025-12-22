# Performance Optimizer Skill

Identify and fix performance bottlenecks.

## Profiling Commands

```bash
# Time script execution
python -m cProfile -s cumtime script.py

# Memory profiling
python -m memory_profiler script.py

# Line-by-line timing
kernprof -l -v script.py
```

## Common Bottlenecks

| Issue | Solution |
|:---|:---|
| Sync I/O in async | Use `aiohttp`, `aiofiles` |
| N+1 queries | Batch operations |
| Large loops | Use generators, `itertools` |
| Repeated computation | Cache with `@lru_cache` |
| Blocking calls | Use `asyncio.to_thread()` |

## Async Patterns

```python
# Good: Concurrent execution
results = await asyncio.gather(*tasks)

# Good: Streaming
async for chunk in response.content.iter_chunked(8192):
    process(chunk)

# Bad: Sequential async
for item in items:
    await process(item)  # One at a time!
```

## Caching

```python
from functools import lru_cache

@lru_cache(maxsize=256)
def expensive_computation(key: str) -> Result:
    ...
```

## Database Optimization

- Use connection pooling
- Batch inserts/updates
- Add indexes for frequent queries
- Use `EXPLAIN ANALYZE` for slow queries

## Benchmarking

```python
import time
start = time.perf_counter()
# ... code ...
elapsed = time.perf_counter() - start
print(f"Elapsed: {elapsed:.3f}s")
```

## Best Practices

1. Measure before optimizing
2. Focus on hot paths
3. Prefer async patterns
4. Cache expensive operations
5. Use generators for large data
