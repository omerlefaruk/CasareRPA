---
skill: performance
description: Optimize CasareRPA workflows and nodes for performance including async optimization, caching, connection pooling, and memory efficiency.
---

## Performance Optimization Areas

### Async Concurrency

**Sequential vs Concurrent Execution**
```python
# BAD: Sequential execution (SLOW)
for node in nodes:
    result = await node.execute(context)

# GOOD: Concurrent execution (FAST)
results = await asyncio.gather(*[
    node.execute(context)
    for node in nodes
])
```

**Semaphore for Concurrency Limits**
```python
from asyncio import Semaphore

# Limit to 10 concurrent operations
sem = Semaphore(10)

async def limited_execute(node):
    async with sem:
        return await node.execute(context)

# Execute with limits
results = await asyncio.gather(*[
    limited_execute(node) for node in nodes
])
```

**Bounded Semaphore Pattern**
```python
from asyncio import BoundedSemaphore

# Prevent semaphore drift
sem = BoundedSemaphore(10)

async def safe_concurrent_task():
    async with sem:
        # Your concurrent operation
        await some_async_operation()
```

### Connection Pooling

**Browser Connection Pool**
```python
class BrowserResourceManager:
    """Pool of browser instances for reuse."""
    _pool: list[Browser] = []
    _max_size: int = 5
    _lock: asyncio.Lock = asyncio.Lock()

    async def get_browser(self) -> Browser:
        """Get or create browser instance."""
        async with self._lock:
            if len(self._pool) > 0:
                return self._pool.pop()
            # Create new if under limit
            if len(self._pool) < self._max_size:
                browser = await self._create_browser()
                return browser
            # Wait for available browser
            await asyncio.sleep(0.1)
            return await self.get_browser()

    async def release_browser(self, browser: Browser):
        """Return browser to pool."""
        async with self._lock:
            if len(self._pool) < self._max_size:
                self._pool.append(browser)
            else:
                await browser.close()
```

**Database Connection Pool (asyncpg)**
```python
import asyncpg

class DatabasePool:
    """PostgreSQL connection pool."""
    _pool: asyncpg.Pool = None

    async def initialize(self, dsn: str):
        """Initialize connection pool."""
        self._pool = await asyncpg.create_pool(
            dsn,
            min_size=5,
            max_size=20,
            command_timeout=60
        )

    async def execute_query(self, query: str, *args):
        """Execute query with connection from pool."""
        async with self._pool.acquire() as conn:
            return await conn.fetch(query, *args)
```

**HTTP Session Pooling (aiohttp)**
```python
import aiohttp

class HTTPClient:
    """Pooled HTTP client."""
    _session: aiohttp.ClientSession | None = None
    _connector: aiohttp.TCPConnector | None = None

    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create session."""
        if self._session is None:
            self._connector = aiohttp.TCPConnector(
                limit=100,  # Max connections
                limit_per_host=10
            )
            self._session = aiohttp.ClientSession(
                connector=self._connector,
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self._session

    async def close(self):
        """Cleanup sessions."""
        if self._session:
            await self._session.close()
```

### Caching Strategies

**LRU Cache for Expensive Operations**
```python
from functools import lru_cache

@lru_cache(maxsize=256)
def expensive_computation(input_data: str) -> Result:
    """Cache computation results."""
    # Expensive operation
    return process(input_data)

# Clear cache when needed
expensive_computation.cache_clear()
```

**Async Cache with TTL**
```python
import time
from typing import Dict, Any

class TTLCache:
    """Time-based cache for async operations."""
    def __init__(self, ttl_seconds: int = 300):
        self._cache: Dict[str, tuple[Any, float]] = {}
        self._ttl = ttl_seconds

    async def get(self, key: str) -> Any | None:
        """Get cached value if not expired."""
        if key not in self._cache:
            return None
        value, timestamp = self._cache[key]
        if time.time() - timestamp > self._ttl:
            del self._cache[key]
            return None
        return value

    async def set(self, key: str, value: Any) -> None:
        """Set cached value with timestamp."""
        self._cache[key] = (value, time.time())

# Usage
cache = TTLCache(ttl_seconds=60)
result = await cache.get("api_data")
if result is None:
    result = await fetch_api_data()
    await cache.set("api_data", result)
```

### Memory Efficiency

**Generator for Large Data**
```python
def process_large_file(file_path: str):
    """Process file one line at a time."""
    with open(file_path) as f:
        for line in f:
            yield process_line(line)

# Usage
for result in process_large_file("large_file.txt"):
    handle_result(result)
```

**__slots__ for Object Memory**
```python
class NodeExecution:
    """Memory-optimized execution result."""
    __slots__ = ['node_id', 'status', 'result', 'error']

    def __init__(self, node_id: str, status: str, result: Any, error: str | None):
        self.node_id = node_id
        self.status = status
        self.result = result
        self.error = error
```

**Weak References for Caches**
```python
import weakref

class WeakCache:
    """Cache that doesn't prevent garbage collection."""
    def __init__(self):
        self._cache: weakref.WeakValueDictionary = weakref.WeakValueDictionary()

    def get(self, key: str):
        return self._cache.get(key)

    def set(self, key: str, value: Any):
        self._cache[key] = value
```

### Profiling Tools

**CPU Profiling**
```bash
# Profile CPU usage
python -m cProfile -s cumtime -o profile.stats run_workflow.py

# Analyze profile
python -m pstats profile.stats
```

**Memory Profiling**
```bash
# Install memory_profiler
pip install memory-profiler

# Profile memory
python -m memory_profiler src/casare_rpa/infrastructure/robot/executor.py
```

**Async Profiling with aiomonitor**
```bash
# Install aiomonitor
pip install aiomonitor

# Profile async operations
python -m aiomonitor run.py
```

**Line-by-Line Timing**
```bash
# Install line_profiler
pip install line_profiler

# Profile function
kernprof -l -v src/casare_rpa/nodes/browser/click_node.py
```

### Performance Benchmarks

**Node Execution Benchmark**
```python
import time
import asyncio
from statistics import mean

async def benchmark_node(node: Node, iterations: int = 100):
    """Benchmark node execution time."""
    times = []
    context = create_test_context()

    for _ in range(iterations):
        start = time.perf_counter()
        await node.execute(context)
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    return {
        'mean': mean(times),
        'min': min(times),
        'max': max(times),
        'total': sum(times)
    }
```

**Workflow Execution Benchmark**
```python
async def benchmark_workflow(workflow_path: str, iterations: int = 10):
    """Benchmark full workflow execution."""
    times = []

    for _ in range(iterations):
        start = time.perf_counter()
        await execute_workflow(workflow_path)
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    return {
        'avg_time': mean(times),
        'throughput': 3600 / mean(times)  # executions per hour
    }
```

### Common Performance Anti-Patterns

**Avoid: Blocking Calls in Async**
```python
# BAD: Blocks event loop
async def bad_async():
    time.sleep(1)  # Blocking
    result = requests.get("https://api.com")  # Blocking

# GOOD: Async operations
async def good_async():
    await asyncio.sleep(1)  # Non-blocking
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.com") as response:
            return await response.text()
```

**Avoid: N+1 Query Problem**
```python
# BAD: N+1 queries
for user_id in user_ids:
    user = await db.fetch("SELECT * FROM users WHERE id = $1", user_id)

# GOOD: Single batch query
users = await db.fetch("SELECT * FROM users WHERE id = ANY($1)", user_ids)
```

**Avoid: Synchronous File I/O in Async**
```python
# BAD: Sync file I/O
async def bad_file_read():
    data = open("file.txt").read()  # Blocking

# GOOD: Async file I/O
import aiofiles
async def good_file_read():
    data = await aiofiles.open("file.txt").read()  # Non-blocking
```

### Performance Checklist

When optimizing CasareRPA workflows:

- [ ] Use `asyncio.gather()` for parallel operations
- [ ] Implement connection pooling for browsers/DB/HTTP
- [ ] Cache expensive operations
- [ ] Use generators for large datasets
- [ ] Profile bottlenecks before optimizing
- [ ] Avoid blocking calls in async functions
- [ ] Use semaphores to limit concurrency
- [ ] Implement proper cleanup in `finally` blocks
- [ ] Benchmark after optimization
- [ ] Monitor memory usage for leaks

### Performance Monitoring

**Key Metrics to Track**
- Workflow execution time
- Node execution time (per node type)
- Memory usage (peak, average)
- Connection pool utilization
- Cache hit rate
- Error rate (retries, timeouts)

**Performance Targets**
- Workflow execution: < 5s for 10-node workflows
- Node execution: < 500ms average
- Memory: < 512MB per workflow
- Connection pool: < 10% idle connections
- Cache hit rate: > 70%

### CasareRPA-Specific Optimizations

**Browser Nodes**
- Reuse browser contexts across workflows
- Use `page.wait_for_*()` instead of `time.sleep()`
- Batch DOM queries with `page.locator()`
- Disable unnecessary browser features for speed

**Database Nodes**
- Use connection pooling
- Batch insert/update operations
- Create indexes for frequent queries
- Use JSONB for flexible schemas

**File System Nodes**
- Use async file operations (aiofiles)
- Stream large files instead of loading into memory
- Use efficient encoding (orjson > json)

**Workflow Executor**
- Topological sort for node execution order
- Parallelize independent node branches
- Cache workflow metadata
- Lazy load node classes

## Usage

Invoke this skill when:
- User requests performance optimization
- Workflow execution is slow
- Memory usage is high
- Need to benchmark code

```python
Task(subagent_type="quality", prompt="""
mode: perf

Optimize the workflow executor for better performance:
- File: src/casare_rpa/infrastructure/robot/executor.py
- Focus: Node parallelization, connection pooling
- Benchmark: Before and after optimization
""")
```
