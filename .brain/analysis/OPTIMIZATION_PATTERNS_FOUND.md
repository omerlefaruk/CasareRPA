# Archived Analysis (Non-Normative)

This file is archived analysis. Do not treat as current rules. See .agent/, .claude/, and .brain/_index.md for active guidance.

---

# Performance Optimization Patterns in CasareRPA

## Overview

CasareRPA implements comprehensive performance optimization patterns across multiple layers, focusing on lazy loading, caching, object pooling, and resource management. These patterns significantly reduce startup overhead and improve runtime efficiency.

---

## 1. Lazy Import Patterns

### 1.1 Simple Lazy Imports (LRU Cache)
**Location:** `/c/Users/Rau/Desktop/CasareRPA/src/casare_rpa/utils/lazy_imports.py`

**Pattern:** Function-level lazy imports with `@lru_cache(maxsize=1)`

```python
@lru_cache(maxsize=1)
def get_uiautomation():
    """Lazily import uiautomation module (200-400ms overhead)."""
    logger.debug("Lazy loading uiautomation module...")
    import uiautomation
    return uiautomation

@lru_cache(maxsize=1)
def get_win32gui():
    """Lazily import win32gui module (100-200ms overhead)."""
    logger.debug("Lazy loading win32gui module...")
    import win32gui
    return win32gui
```

**Supported Modules:**
- `get_uiautomation()` - Desktop automation (200-400ms)
- `get_win32gui()` - Windows GUI API (100-200ms)
- `get_win32con()` - Windows constants
- `get_win32api()` - Windows API
- `get_pythoncom()` - COM interface

**Pre-configured Lazy Modules:**
```python
uiautomation_lazy = LazyModule("uiautomation")
win32gui_lazy = LazyModule("win32gui")
win32con_lazy = LazyModule("win32con")
win32api_lazy = LazyModule("win32api")
```

**Usage:**
```python
from casare_rpa.utils.lazy_imports import get_uiautomation, get_playwright
from casare_rpa.utils.lazy_imports import uiautomation_lazy

# Function approach
uiautomation = get_uiautomation()

# Module wrapper approach
desktop_element = uiautomation_lazy.GetFocusedElement()
```

---

### 1.2 Advanced Lazy Loading System
**Location:** `/c/Users/Rau/Desktop/CasareRPA/src/casare_rpa/utils/lazy_loader.py`

**Pattern:** Thread-safe lazy module proxy with import metrics

#### LazyModule Class
```python
from casare_rpa.utils.lazy_loader import LazyModule

browser_nodes = LazyModule("casare_rpa.nodes.browser_nodes")
# Module NOT imported yet

node = browser_nodes.NavigateNode()  # Module loaded on first access
```

**Features:**
- Thread-safe with double-checked locking
- Import timing metrics collection
- Tracks slowest imports
- Configurable import callbacks

#### LazyImport Descriptor (Class-level)
```python
from casare_rpa.utils.lazy_loader import LazyImport

class BrowserAutomation:
    playwright = LazyImport("playwright.async_api")

    async def navigate(self, url: str):
        # playwright module imported on first access
        browser = await self.playwright.async_playwright().start()
```

#### lazy_import Function
```python
from casare_rpa.utils.lazy_loader import lazy_import

# Lazy module
browser_nodes = lazy_import("casare_rpa.nodes.browser_nodes")
node = browser_nodes.NavigateNode()  # Import happens here

# Lazy attribute
NavigateNode = lazy_import("casare_rpa.nodes.browser_nodes", "NavigateNode")
node = NavigateNode()  # Import happens here
```

#### Import Metrics
```python
from casare_rpa.utils.lazy_loader import get_import_stats, reset_import_stats

stats = get_import_stats()
# Returns: {
#   "total_imports": 42,
#   "total_time_ms": 1234.5,
#   "slowest_imports": {...},
#   "all_imports": {...}
# }

reset_import_stats()  # Reset metrics
```

---

### 1.3 Node Lazy Imports
**Location:** `/c/Users/Rau/Desktop/CasareRPA/src/casare_rpa/nodes/__init__.py`

**Pattern:** Dynamic node class loading on demand

```python
from casare_rpa.nodes import _lazy_import

# Lazy load any node class by full module path
ClickElementNode = _lazy_import("casare_rpa.nodes.browser.click_element_node")
node = ClickElementNode("node_id")
```

**Visual Node Lazy Imports:**
```python
from casare_rpa.presentation.canvas.visual_nodes import _lazy_import

# Lazy load visual node classes
VisualClickNode = _lazy_import("casare_rpa.presentation.canvas.visual_nodes.browser.ClickElement")
visual_node = VisualClickNode()
```

---

## 2. Caching Patterns

### 2.1 Workflow Schema Cache
**Location:** `/c/Users/Rau/Desktop/CasareRPA/src/casare_rpa/infrastructure/caching/workflow_cache.py`

**Pattern:** LRU cache with content-based fingerprinting

```python
from casare_rpa.infrastructure.caching import get_workflow_cache

cache = get_workflow_cache()

# Compute fingerprint from workflow JSON
fingerprint = cache.compute_fingerprint(workflow_data)

# Try to get from cache
cached_workflow = cache.get(fingerprint)
if cached_workflow:
    return cached_workflow  # Cache hit!

# Parse workflow and cache it
parsed = parse_workflow(workflow_data)
cache.put(fingerprint, parsed)

# Invalidate specific entry
cache.invalidate(fingerprint)

# Clear all
cache.clear()

# Get stats
stats = cache.get_stats()
# {
#   "size": 8,
#   "max_size": 20,
#   "hits": 156,
#   "misses": 42,
#   "hit_rate": 0.788
# }
```

**Features:**
- Content-based cache key (SHA-256 hash of JSON)
- Excludes internal marker keys from fingerprint
- Thread-safe with RLock
- Configurable max size (default 20 workflows)
- LRU eviction policy
- Hit/miss statistics

**Usage in WorkflowLoader:**
```python
# In /src/casare_rpa/utils/workflow/workflow_loader.py
cache = get_workflow_cache()
cache_fingerprint = cache.compute_fingerprint(workflow_data)
cached_workflow = cache.get(cache_fingerprint)
if cached_workflow is not None:
    logger.info(f"Loaded workflow from cache in {elapsed:.1f}ms")
    return cached_workflow
```

---

### 2.2 Selector Validation Cache
**Location:** `/c/Users/Rau/Desktop/CasareRPA/src/casare_rpa/utils/selectors/selector_cache.py`

**Pattern:** LRU cache with TTL-based expiration

```python
from casare_rpa.utils.selectors.selector_cache import get_selector_cache

cache = get_selector_cache()

# Check cache before DOM query
result = cache.get(
    selector_value="#my-button",
    selector_type="css",
    page_url="https://example.com"
)

if result:
    count = result.count
    is_unique = result.is_unique
    exec_time = result.execution_time_ms
else:
    # Query DOM and cache result
    count = await query_dom(selector)
    exec_time = measure_time(query_dom)
    cache.put(
        selector_value="#my-button",
        selector_type="css",
        page_url="https://example.com",
        count=count,
        execution_time_ms=exec_time
    )

# Invalidate all entries for a URL
cache.invalidate(page_url="https://example.com")

# Clean up expired entries
cache.cleanup_expired()

# Get stats
stats = cache.get_stats()
# {
#   "enabled": True,
#   "size": 245,
#   "max_size": 500,
#   "ttl_seconds": 60.0,
#   "hits": 1024,
#   "misses": 256,
#   "hit_rate_percent": 80.0
# }
```

**Features:**
- LRU eviction with configurable size (default 500)
- TTL-based expiration (default 60s)
- URL-aware caching (different pages have different DOMs)
- Thread-safe operations
- Enable/disable toggle
- Hit/miss tracking
- Tracks hit count per entry

**Usage in SelectorManager:**
```python
# In /src/casare_rpa/utils/selectors/selector_manager.py
self._cache = cache or get_selector_cache()

# Later...
cached_result = self._cache.get(selector_value, selector_type, page_url)
```

---

## 3. Object Pooling Patterns

### 3.1 Generic Object Pool
**Location:** `/c/Users/Rau/Desktop/CasareRPA/src/casare_rpa/utils/performance/object_pool.py`

**Pattern:** Reusable object pool with stats tracking

```python
from casare_rpa.utils.performance.object_pool import ObjectPool

# Create a pool
class CustomObject:
    def __init__(self):
        self.data = None

def reset_custom(obj):
    obj.data = None

pool = ObjectPool(
    factory=CustomObject,
    reset_fn=reset_custom,
    max_size=100
)

# Acquire from pool
obj = pool.acquire()

# Use object
obj.data = "value"

# Return to pool
pool.release(obj)

# Get stats
stats = pool.get_stats()
# {
#   "pool_size": 45,
#   "max_size": 100,
#   "hits": 523,
#   "misses": 77,
#   "hit_rate": 0.872
# }
```

---

### 3.2 Specialized Pools

#### Result Dictionary Pool
```python
from casare_rpa.utils.performance.object_pool import (
    get_result_dict,
    return_result_dict
)

# Get pre-allocated result dict
result = get_result_dict()
result["success"] = True
result["data"] = {"value": 42}
result["error"] = None

# Return to pool when done
return_result_dict(result)
```

**Pool Config:**
- Factory: `_create_result_dict()` → `{"success": False, "data": None, "error": None}`
- Reset: Clears dict and sets defaults
- Max size: 200 dicts

#### List Pool
```python
from casare_rpa.utils.performance.object_pool import (
    get_list,
    return_list
)

# Get pre-allocated list
items = get_list()
items.append("item1")
items.append("item2")

# Return to pool
return_list(items)
```

#### Node Instance Pool
```python
from casare_rpa.utils.performance.object_pool import get_node_instance_pool

pool = get_node_instance_pool()

# Acquire node (reuses if available)
node = pool.acquire(
    node_type="ClickElementNode",
    node_class=ClickElementNode,
    node_id="node_123",
    config={"selector": "#button"}
)

# Use node...

# Release back to pool
pool.release(node)

# Release multiple
pool.release_all(nodes_dict)

# Get stats
stats = pool.get_stats()
# {
#   "total_pooled": 42,
#   "pools": {"ClickElementNode": 5, "NavigateNode": 3},
#   "hits": 156,
#   "misses": 42,
#   "hit_rate": 0.788
# }
```

**Features:**
- Reuses node instances across workflow loads
- Resets node state before reuse (config, port values)
- Configurable max per node type (default 20)
- Thread-safe with lock
- Hit/miss/returns tracking

**Usage in WorkflowLoader:**
```python
# In /src/casare_rpa/utils/workflow/workflow_loader.py
try:
    pool = get_node_instance_pool()
    node_instance = pool.acquire(node_type, node_class, node_id, config)
except Exception as e:
    logger.debug(f"Pool acquire failed, using direct instantiation: {e}")
    node_instance = node_class(node_id, config=config)
```

---

### 3.3 WeakRef Node Cache
```python
from casare_rpa.utils.performance.object_pool import get_node_cache

cache = get_node_cache()

# Cache node without preventing GC
cache.set("node_123", node_obj)

# Get cached node (returns None if GC'd)
node = cache.get("node_123")

# Remove from cache
cache.remove("node_123")

# Clear all
cache.clear()

# Get stats
stats = cache.get_stats()
# {
#   "size": 42,
#   "hits": 234,
#   "misses": 56,
#   "hit_rate": 0.807
# }
```

**Features:**
- Uses `WeakValueDictionary` for automatic GC
- Caches without preventing garbage collection
- Hit/miss tracking
- Thread-safe (implicit via WeakValueDictionary)

---

## 4. Resource Pool Patterns

### 4.1 Browser Context Pool
**Location:** `/c/Users/Rau/Desktop/CasareRPA/src/casare_rpa/utils/pooling/browser_pool.py`

**Pattern:** Reusable browser context pool with lifecycle management

```python
from casare_rpa.utils.pooling.browser_pool import BrowserContextPool

# Create pool
pool = BrowserContextPool(
    browser=playwright_browser,
    min_size=2,           # Pre-warm 2 contexts
    max_size=10,          # Max 10 concurrent
    max_context_age=300.0,  # Recycle after 5 min
    idle_timeout=60.0,    # Close if idle >1 min
    context_options={"viewport": {"width": 1920, "height": 1080}}
)

# Get a context
context = await pool.acquire()

# Use context
page = await context.new_page()
await page.goto("https://example.com")

# Release back to pool
await pool.release(context)

# Cleanup
await pool.cleanup()
```

**Features:**
- Pre-warm pool with minimum size
- Dynamic scaling up to max_size
- Lifecycle management (age, idle timeout)
- Automatic cleanup of stale contexts
- Thread-safe async operations

---

### 4.2 HTTP Session Pool
**Location:** `/c/Users/Rau/Desktop/CasareRPA/src/casare_rpa/utils/pooling/http_session_pool.py`

**Pattern:** Reusable HTTP session pool with connection keep-alive

```python
from casare_rpa.utils.pooling.http_session_pool import HttpSessionPool

# Create pool
pool = HttpSessionPool(
    min_size=2,
    max_size=10,
    base_urls=["https://api1.example.com", "https://api2.example.com"],
    max_session_age=600.0,  # 10 min
    idle_timeout=120.0      # 2 min
)

# Get a session
session = await pool.acquire(base_url="https://api1.example.com")

# Make request
response = await session.get("/endpoint")

# Release session
await pool.release(session)

# Get stats
stats = pool.get_stats()
# {
#   "sessions_created": 42,
#   "requests_made": 5234,
#   "success_rate": 99.5,
#   "avg_request_time_ms": 124.3
# }
```

**Features:**
- Connection pooling with keep-alive
- Base URL support for multiple API endpoints
- Session reuse reduces SSL handshakes
- Lifecycle management
- Request statistics

---

### 4.3 Database Connection Pool
**Location:** `/c/Users/Rau/Desktop/CasareRPA/src/casare_rpa/utils/pooling/database_pool.py`

**Pattern:** Thread-safe database connection pooling

Features similar to HTTP Session Pool for database connections.

---

## 5. Performance Metrics System
**Location:** `/c/Users/Rau/Desktop/CasareRPA/src/casare_rpa/utils/performance/performance_metrics.py`

**Pattern:** Unified metrics collection and reporting

```python
from casare_rpa.utils.performance.performance_metrics import PerformanceMetrics

metrics = PerformanceMetrics()

# Timer context manager
with metrics.timer("workflow_load", labels={"workflow": "my_workflow"}):
    load_workflow()

# Manual timing
metrics.record_timing("node_execute", 245.5, labels={"node_type": "Click"})

# Get statistics
stats = metrics.get_stats("workflow_load")
```

---

## Summary Table

| Pattern | Location | Purpose | Key Feature |
|---------|----------|---------|------------|
| **Lazy Imports (LRU)** | `utils/lazy_imports.py` | Defer module load (200-400ms) | `@lru_cache(maxsize=1)` |
| **Lazy Module Proxy** | `utils/lazy_loader.py` | Thread-safe module loading | Double-check locking + metrics |
| **Lazy Import Descriptor** | `utils/lazy_loader.py` | Class-level lazy imports | Per-instance caching |
| **Workflow Cache** | `infrastructure/caching/workflow_cache.py` | Cache parsed workflows | Content fingerprint key |
| **Selector Cache** | `utils/selectors/selector_cache.py` | Cache DOM queries | TTL + URL-aware |
| **Object Pool** | `utils/performance/object_pool.py` | Reuse objects | Generic with reset_fn |
| **Result Dict Pool** | `utils/performance/object_pool.py` | Pre-alloc result dicts | 200 dict pool |
| **List Pool** | `utils/performance/object_pool.py` | Pre-alloc lists | 100 list pool |
| **Node Instance Pool** | `utils/performance/object_pool.py` | Reuse node instances | Per-type pools |
| **WeakRef Node Cache** | `utils/performance/object_pool.py` | Cache without blocking GC | WeakValueDictionary |
| **Browser Pool** | `utils/pooling/browser_pool.py` | Reuse browser contexts | Context lifecycle mgmt |
| **HTTP Session Pool** | `utils/pooling/http_session_pool.py` | Connection pooling | Keep-alive + stats |
| **DB Connection Pool** | `utils/pooling/database_pool.py` | Connection pooling | Thread-safe |

---

## Integration Points

### WorkflowLoader (Primary Consumer)
- **Workflow caching** via `get_workflow_cache()`
- **Node pooling** via `get_node_instance_pool()`

### SelectorManager
- **Selector caching** via `get_selector_cache()`

### Node Registry
- **Lazy imports** via `_lazy_import()` for dynamic class loading

### AI Agent Tools
- **Lazy node loading** via `_lazy_import()`

---

## Recommended Usage Patterns

### For Startup Performance
```python
# Use lazy imports for heavy modules
from casare_rpa.utils.lazy_imports import get_uiautomation
from casare_rpa.utils.lazy_loader import LazyImport

class MyClass:
    uiautomation = LazyImport("uiautomation")
```

### For Hot Path Optimization
```python
# Use object pooling for frequently allocated objects
from casare_rpa.utils.performance.object_pool import (
    get_result_dict,
    return_result_dict
)

def execute_node(node_id):
    result = get_result_dict()
    try:
        result["data"] = do_work()
        result["success"] = True
    finally:
        return_result_dict(result)
```

### For Data-Heavy Operations
```python
# Use caching for expensive computations
from casare_rpa.infrastructure.caching import get_workflow_cache

cache = get_workflow_cache()
fingerprint = cache.compute_fingerprint(workflow_data)
if not cache.get(fingerprint):
    parsed = expensive_parse(workflow_data)
    cache.put(fingerprint, parsed)
```

### For Selector Operations
```python
# Cache selector validation to reduce DOM queries
from casare_rpa.utils.selectors.selector_cache import get_selector_cache

cache = get_selector_cache()
result = cache.get(selector, selector_type, page_url)
if not result:
    count = await validate_selector(selector)
    cache.put(selector, selector_type, page_url, count, exec_time)
```
