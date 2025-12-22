# Archived Analysis (Non-Normative)

This file is archived analysis. Do not treat as current rules. See .agent/, .claude/, and .brain/_index.md for active guidance.

---

# Optimization Patterns - Quick Reference

## File Locations

```
Lazy Imports:
  - utils/lazy_imports.py              [Simple LRU-based lazy imports]
  - utils/lazy_loader.py               [Advanced lazy loading system]
  - nodes/__init__.py                  [_lazy_import() for node classes]
  - presentation/canvas/visual_nodes/  [_lazy_import() for visual nodes]

Caching:
  - infrastructure/caching/workflow_cache.py    [Workflow schema cache]
  - utils/selectors/selector_cache.py          [Selector validation cache]

Object Pooling:
  - utils/performance/object_pool.py   [Generic pools + specialized]

Resource Pooling:
  - utils/pooling/browser_pool.py      [Browser context pool]
  - utils/pooling/http_session_pool.py [HTTP connection pool]
  - utils/pooling/database_pool.py     [DB connection pool]

Metrics:
  - utils/performance/performance_metrics.py
```

---

## Quick Import Cheat Sheet

### Lazy Imports
```python
# Simple function-based lazy imports
from casare_rpa.utils.lazy_imports import (
    get_uiautomation,      # 200-400ms saved
    get_win32gui,          # 100-200ms saved
    get_win32con,
    get_win32api,
    get_pythoncom,
    uiautomation_lazy,     # Pre-configured LazyModule
    win32gui_lazy,
)

# Advanced lazy loading
from casare_rpa.utils.lazy_loader import (
    LazyModule,            # Module proxy with metrics
    LazyImport,            # Descriptor for class attributes
    lazy_import,           # Function-based lazy loader
    get_import_stats,      # Get import timing metrics
    reset_import_stats,
)

# Node lazy imports
from casare_rpa.nodes import _lazy_import
from casare_rpa.presentation.canvas.visual_nodes import _lazy_import as visual_lazy_import
```

### Caching
```python
# Workflow caching
from casare_rpa.infrastructure.caching import get_workflow_cache

# Selector caching
from casare_rpa.utils.selectors.selector_cache import get_selector_cache
```

### Object Pooling
```python
# Specialized pools
from casare_rpa.utils.performance.object_pool import (
    get_result_dict,        # Pre-allocated dicts for results
    return_result_dict,
    get_list,               # Pre-allocated lists
    return_list,
    get_node_instance_pool, # Node reuse pool
    get_node_cache,         # WeakRef cache
    ObjectPool,             # Generic pool
)
```

### Resource Pooling
```python
from casare_rpa.utils.pooling.browser_pool import BrowserContextPool
from casare_rpa.utils.pooling.http_session_pool import HttpSessionPool
from casare_rpa.utils.pooling.database_pool import DatabaseConnectionPool
```

---

## Usage Snippets

### Defer Expensive Imports
```python
# BEFORE: Blocks startup for 200-400ms
import uiautomation
import win32gui

# AFTER: No startup overhead
from casare_rpa.utils.lazy_imports import get_uiautomation, get_win32gui

def my_function():
    uiautomation = get_uiautomation()  # Loaded once, cached forever
    # ...
```

### Class-Level Lazy Imports
```python
from casare_rpa.utils.lazy_loader import LazyImport

class DesktopAutomation:
    uiautomation = LazyImport("uiautomation")
    win32gui = LazyImport("win32gui")

    def get_element(self):
        return self.uiautomation.GetFocusedElement()
```

### Cache Workflow Parsing
```python
from casare_rpa.infrastructure.caching import get_workflow_cache

cache = get_workflow_cache()
fp = cache.compute_fingerprint(workflow_json)

# Try cache first
parsed = cache.get(fp)
if parsed:
    return parsed

# Parse and cache
parsed = parse_workflow(workflow_json)
cache.put(fp, parsed)
return parsed
```

### Cache Selector Queries
```python
from casare_rpa.utils.selectors.selector_cache import get_selector_cache

cache = get_selector_cache()

# Check cache
result = cache.get(selector, "css", page_url)
if result:
    return result  # Cache hit - no DOM query!

# Query DOM
count = await query_dom(selector)
cache.put(selector, "css", page_url, count, exec_time_ms)
```

### Pool Pre-Allocated Objects
```python
from casare_rpa.utils.performance.object_pool import (
    get_result_dict,
    return_result_dict
)

# In node execution hot path
result = get_result_dict()
try:
    result["success"] = True
    result["data"] = execute_node()
    return result
finally:
    return_result_dict(result)  # Return to pool
```

### Pool Node Instances
```python
from casare_rpa.utils.performance.object_pool import get_node_instance_pool

pool = get_node_instance_pool()

# Reuse node instance across workflow loads
node = pool.acquire(
    node_type="ClickElement",
    node_class=ClickElementNode,
    node_id="node_123",
    config={"selector": "#button"}
)

# Use node...
result = node.execute()

# Return to pool for reuse
pool.release(node)
```

### Browse Context Pool
```python
from casare_rpa.utils.pooling.browser_pool import BrowserContextPool

pool = BrowserContextPool(
    browser=playwright_browser,
    min_size=2,
    max_size=10,
    max_context_age=300.0  # 5 min
)

context = await pool.acquire()
page = await context.new_page()
# ... use page ...
await pool.release(context)
```

---

## Performance Monitoring

### Check Cache Stats
```python
from casare_rpa.infrastructure.caching import get_workflow_cache

cache = get_workflow_cache()
stats = cache.get_stats()
print(f"Workflow cache hit rate: {stats['hit_rate']*100:.1f}%")

# Output:
# {
#   "size": 8,           # Currently cached
#   "max_size": 20,      # Max capacity
#   "hits": 156,         # Cache hits
#   "misses": 42,        # Cache misses
#   "hit_rate": 0.788    # 78.8% hit rate
# }
```

### Check Pool Stats
```python
from casare_rpa.utils.performance.object_pool import get_node_instance_pool

pool = get_node_instance_pool()
stats = pool.get_stats()

print(f"Node pool hit rate: {stats['hit_rate']*100:.1f}%")
# Output:
# {
#   "total_pooled": 42,
#   "pools": {"ClickElementNode": 5, ...},
#   "hits": 156,         # Reused from pool
#   "misses": 42,        # Created new
#   "hit_rate": 0.788
# }
```

### Check Import Metrics
```python
from casare_rpa.utils.lazy_loader import get_import_stats

stats = get_import_stats()
print(f"Total lazy import time: {stats['total_time_ms']:.1f}ms")
print(f"Slowest imports: {stats['slowest_imports']}")

# Output:
# {
#   "total_imports": 42,
#   "total_time_ms": 1234.5,
#   "slowest_imports": {
#     "uiautomation": 380.2,
#     "playwright": 245.1,
#     ...
#   }
# }
```

---

## Performance Impact

### Lazy Imports
- **uiautomation**: 200-400ms saved from startup
- **win32gui**: 100-200ms saved from startup
- **playwright**: 150-250ms saved from startup (if not immediately needed)

### Caching
- **Workflow cache**: Eliminates JSON parsing + schema validation (typical 50-200ms)
- **Selector cache**: Eliminates DOM queries (typical 10-50ms per query)

### Object Pooling
- **Result dict pool**: Reduces GC pressure on hot paths (allocation cost ~0.01ms per dict)
- **Node instance pool**: Eliminates node construction overhead (typical 0.5-2ms per node)

### Resource Pools
- **Browser context pool**: Reuses contexts instead of creating new (saves 500-1000ms per context)
- **HTTP session pool**: Connection keep-alive + no SSL renegotiation

---

## Best Practices

1. **Use LazyImport for class-level module dependencies** - minimal code change
2. **Use lazy_imports for simple deferred imports** - for backward compatibility
3. **Use LazyModule when needing metrics/callbacks** - for profiling
4. **Always return pooled objects** - use try/finally to ensure returns
5. **Enable caching for expensive operations** - but invalidate appropriately
6. **Monitor pool hit rates** - adjust pool sizes if hit rate is too low (<50%)
7. **Clean up expired cache entries** - periodically call cleanup_expired()
8. **Use WeakRef cache for temporary lookups** - won't block garbage collection

---

## Statistics Commands

```bash
# Check if modules are lazy-loaded vs imported
python -c "import sys; print('uiautomation' in sys.modules)"

# Profile import times
python -c "
from casare_rpa.utils.lazy_loader import get_import_stats, reset_import_stats
import time

reset_import_stats()
# ... do your import ...
stats = get_import_stats()
print(stats)
"
```

---

## Common Patterns Found in Codebase

### WorkflowLoader
- Uses **workflow cache** for parsed schemas
- Uses **node instance pool** for node reuse
- Uses **lazy imports** for node classes

### SelectorManager
- Uses **selector cache** for validation results
- URL-aware caching for different pages
- 60-second TTL for cache entries

### Node Registry
- Uses **lazy imports** for dynamic node loading
- Separate functions for visual vs domain nodes

### DesktopAutomation Nodes
- Could use **lazy imports** for uiautomation/win32gui (HIGH IMPACT)
- Already uses **LazyImport** descriptor pattern

---

## Anti-Patterns to Avoid

```python
# AVOID: Importing all modules at startup
import uiautomation
import win32gui
import win32api
import pythoncom

# DO: Lazy import on first use
from casare_rpa.utils.lazy_imports import get_uiautomation, get_win32gui

# AVOID: Not returning pooled objects
result = get_result_dict()
# ... forget to return_result_dict(result)

# DO: Always return in finally
result = get_result_dict()
try:
    # use result
finally:
    return_result_dict(result)

# AVOID: Cache without TTL/invalidation
cache.put(key, value)  # May serve stale data forever

# DO: Use TTL and invalidation
if cache.is_expired(ttl_seconds=60):
    cache.invalidate()
```
