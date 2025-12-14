# Optimization Pattern Integration Map

## Where Optimizations Are Currently Used

### 1. WorkflowLoader (Primary Optimization Hub)
**File:** `/src/casare_rpa/utils/workflow/workflow_loader.py`

**Active Optimizations:**

#### Workflow Caching
```python
from casare_rpa.infrastructure.caching.workflow_cache import get_workflow_cache

cache = get_workflow_cache()
cache_fingerprint = cache.compute_fingerprint(workflow_data)
cached_workflow = cache.get(cache_fingerprint)
if cached_workflow is not None:
    load_elapsed = (time.perf_counter() - load_start) * 1000
    logger.info(f"Loaded workflow from cache in {load_elapsed:.1f}ms")
    return cached_workflow
```
- Caches entire parsed workflow schemas
- Uses SHA-256 fingerprinting for cache key
- Eliminates JSON parsing + validation on repeated loads
- **Impact:** 50-200ms savings per cached workflow

#### Node Instance Pooling
```python
from casare_rpa.utils.performance.object_pool import get_node_instance_pool

try:
    pool = get_node_instance_pool()
    node_instance = pool.acquire(node_type, node_class, node_id, config)
except Exception as e:
    logger.debug(f"Pool acquire failed for {node_type}, using direct instantiation: {e}")
    node_instance = node_class(node_id, config=config)
```
- Reuses node instances across workflow loads
- Graceful fallback to direct instantiation
- **Impact:** Reduces allocation overhead on hot paths

#### Lazy Node Loading
```python
# In node_registry.py
from casare_rpa.nodes import _lazy_import

node_class = _lazy_import(node_type)
```
- Defers node class loading until instantiation
- **Impact:** Faster node registry initialization

---

### 2. SelectorManager (Selector Caching)
**File:** `/src/casare_rpa/utils/selectors/selector_manager.py`

**Active Optimizations:**

#### Selector Validation Caching
```python
from casare_rpa.utils.selectors.selector_cache import get_selector_cache

self._cache = cache or get_selector_cache()

# Later when validating selectors...
cached_result = self._cache.get(selector_value, selector_type, page_url)
if cached_result:
    return cached_result  # Avoid DOM query!

# If not cached, query and cache
count = await query_dom(selector)
self._cache.put(selector_value, selector_type, page_url, count, exec_time)
```

**Features:**
- URL-aware caching (different pages have different DOMs)
- 60-second TTL for automatic invalidation
- Hit/miss tracking for performance monitoring
- Enable/disable toggle for cache control

**Impact:**
- Eliminates repeated DOM queries
- Typical DOM query: 10-50ms
- Cache hit: <1ms

---

### 3. Node Registry (Lazy Loading)
**File:** `/src/casare_rpa/presentation/canvas/graph/node_registry.py`

**Active Optimizations:**

#### Visual Node Lazy Loading
```python
from casare_rpa.presentation.canvas.visual_nodes import _lazy_import as visual_lazy_import

visual_cls = visual_lazy_import(visual_name)
```

#### Domain Node Lazy Loading
```python
from casare_rpa.nodes import _lazy_import as nodes_lazy_import

casare_class = nodes_lazy_import(casare_name)
```

**Impact:** Defers loading of 400+ node classes until needed

---

### 4. AI Agent Tools (Lazy Node Loading)
**File:** `/src/casare_rpa/infrastructure/ai/agent_tools.py`

**Active Optimizations:**

```python
from casare_rpa.nodes import _lazy_import

node_class = _lazy_import(tool.node_type)
# Node class only loaded when AI needs to create tool instance
```

**Impact:** Lazy initialization of AI tool registry

---

## Optimization Opportunities (Where They Could Be Used)

### High Impact - Desktop Automation Nodes
**Current State:** Heavy modules loaded immediately
```python
import uiautomation  # 200-400ms
import win32gui      # 100-200ms
import win32api      # Additional overhead
import win32con      # Additional overhead
```

**Opportunity:** Defer until node execution
```python
from casare_rpa.utils.lazy_imports import get_uiautomation, get_win32gui

def execute(self):
    uiautomation = get_uiautomation()  # Loaded on first execute
    # ... rest of execution ...
```

**Files to Update:**
- `nodes/desktop_automation/` - all desktop nodes
- `nodes/window_automation/` - window nodes
- Any node using uiautomation, win32*, pythoncom

**Estimated Savings:** 300-600ms startup time

---

### High Impact - Browser Automation Pools
**Current State:** Contexts created on demand
```python
# No pooling currently observed
context = await browser.new_context()  # Creates new context (500-1000ms)
```

**Opportunity:** Implement context pooling
```python
from casare_rpa.utils.pooling.browser_pool import BrowserContextPool

pool = BrowserContextPool(browser, min_size=3, max_size=10)
context = await pool.acquire()  # Reuses cached context
```

**Files to Update:**
- Any browser automation executor
- Robot execution engine
- Browser factory classes

**Estimated Savings:** 500-1000ms per concurrent workflow

---

### Medium Impact - HTTP Request Pooling
**Current State:** New sessions created per request
```python
# Likely creating new aiohttp sessions or httpx clients
response = await httpx.get(url)
```

**Opportunity:** Implement session pooling
```python
from casare_rpa.utils.pooling.http_session_pool import HttpSessionPool

pool = HttpSessionPool(min_size=5, max_size=20)
session = await pool.acquire()
response = await session.get(url)
await pool.release(session)
```

**Files to Update:**
- `infrastructure/http/` modules
- UnifiedHttpClient implementation
- Any HTTP-based node

**Estimated Savings:** 100-300ms per request (SSL negotiation)

---

### Medium Impact - Result Dict Pooling
**Current State:** New dicts allocated per node execution
```python
def execute(self):
    result = {"success": False, "data": None, "error": None}
    # ... populate result ...
    return result
```

**Opportunity:** Use pooled dicts in hot paths
```python
from casare_rpa.utils.performance.object_pool import (
    get_result_dict,
    return_result_dict
)

def execute(self):
    result = get_result_dict()
    try:
        result["data"] = do_work()
        result["success"] = True
        return result.copy()  # Copy before returning
    finally:
        return_result_dict(result)
```

**Files to Update:**
- All node execute() methods (400+ nodes)
- Workflow executor
- Any result-producing function

**Estimated Savings:** Reduces GC pressure on hot paths

---

### Low Impact - Selector Manager Lazy Caching
**Current State:** Already implemented

**Opportunity:** Extend to more selector types
- Currently caches CSS and XPath selectors
- Could extend to image/pixel selectors

---

### Low Impact - Async Cache Warmup
**Current State:** Caches are populated on-demand

**Opportunity:** Pre-warm critical caches
```python
async def warmup_caches():
    # Pre-load common workflows
    common_workflows = get_common_workflows()
    for workflow in common_workflows:
        cache = get_workflow_cache()
        fp = cache.compute_fingerprint(workflow)
        cache.put(fp, parse_workflow(workflow))
```

---

## Cross-Module Optimization Path

```
Application Startup
    └── Load Node Registry
        ├── [LAZY] Load visual node classes
        └── [LAZY] Load domain node classes

User Creates Workflow
    └── Load Workflow Schema
        ├── [CACHED] Check workflow cache
        └── If miss → Parse and cache

Execute Workflow
    ├── For each node:
    │   ├── [LAZY] Load node class if needed
    │   ├── [POOLED] Acquire node instance (or create)
    │   └── Execute node
    │       ├── [LAZY] Load uiautomation on desktop nodes
    │       ├── [POOLED] Acquire browser context
    │       ├── [CACHED] Check selector cache
    │       └── [POOLED] Return browser context
    └── [POOLED] Return node instance

Browser Operations
    ├── [POOLED] Acquire browser context
    ├── [POOLED] Acquire HTTP session for API calls
    ├── [CACHED] Validate selectors
    └── [POOLED] Release resources
```

---

## Usage Statistics

### Currently Active
| Pattern | Count | Example |
|---------|-------|---------|
| Workflow caching | 1 | WorkflowLoader |
| Selector caching | 1 | SelectorManager |
| Node instance pooling | 1 | WorkflowLoader |
| Lazy node imports | 3 | WorkflowLoader, NodeRegistry, AITools |

### Implemented But Not Used
| Pattern | Location | Reason |
|---------|----------|--------|
| Result dict pool | `utils/performance/` | Not integrated into core |
| List pool | `utils/performance/` | Not integrated into core |
| WeakRef cache | `utils/performance/` | Not integrated into core |
| Browser context pool | `utils/pooling/` | Not integrated into executor |
| HTTP session pool | `utils/pooling/` | Not integrated into HTTP client |
| Lazy imports (uiautomation) | `utils/lazy_imports.py` | Not used in desktop nodes |

---

## Integration Checklist

To maximize optimization benefits, integrate in this order:

### Phase 1: High-Impact (Already Active)
- [x] Workflow caching in WorkflowLoader
- [x] Selector caching in SelectorManager
- [x] Node instance pooling in WorkflowLoader
- [x] Lazy node imports in registries

### Phase 2: High-Impact (Low Effort)
- [ ] Lazy imports for uiautomation/win32 in desktop nodes
- [ ] Browser context pooling in robot executor
- [ ] HTTP session pooling in UnifiedHttpClient

### Phase 3: Medium-Impact
- [ ] Result dict pooling in node execute hot paths
- [ ] Database connection pooling in persistence layer
- [ ] Performance metrics dashboard integration

### Phase 4: Monitoring
- [ ] Export cache/pool statistics to metrics
- [ ] Add performance dashboard widget
- [ ] Create performance baseline tests

---

## Code Snippet Template

### Adding Lazy Import to a Class
```python
from casare_rpa.utils.lazy_loader import LazyImport

class DesktopNode(BaseNode):
    """Node that uses desktop automation."""

    # Defer expensive imports until first use
    uiautomation = LazyImport("uiautomation")
    win32gui = LazyImport("win32gui")

    def execute(self):
        """Execute node - imports loaded here on first call."""
        element = self.uiautomation.GetFocusedElement()
        # ... rest of execution ...
```

### Adding Cache Check
```python
from casare_rpa.infrastructure.caching import get_workflow_cache

def load_workflow(workflow_json):
    cache = get_workflow_cache()

    # Compute fingerprint
    fingerprint = cache.compute_fingerprint(workflow_json)

    # Check cache first
    cached = cache.get(fingerprint)
    if cached:
        logger.info(f"Loaded from cache")
        return cached

    # Cache miss - parse and cache
    parsed = parse_workflow(workflow_json)
    cache.put(fingerprint, parsed)
    return parsed
```

### Adding Pool Acquisition
```python
from casare_rpa.utils.performance.object_pool import (
    get_node_instance_pool
)

pool = get_node_instance_pool()

# Acquire with fallback
try:
    node = pool.acquire(
        node_type=node_type,
        node_class=node_class,
        node_id=node_id,
        config=node_config
    )
except Exception as e:
    logger.debug(f"Pool acquisition failed: {e}")
    node = node_class(node_id, config=node_config)

# Use node...
result = node.execute()

# Always return to pool
pool.release(node)
```

---

## Monitoring Commands

```python
# Check all optimization metrics
from casare_rpa.infrastructure.caching import get_workflow_cache
from casare_rpa.utils.selectors.selector_cache import get_selector_cache
from casare_rpa.utils.performance.object_pool import (
    get_node_instance_pool,
    get_node_cache
)
from casare_rpa.utils.lazy_loader import get_import_stats

print("=== Workflow Cache ===")
print(get_workflow_cache().get_stats())

print("\n=== Selector Cache ===")
print(get_selector_cache().get_stats())

print("\n=== Node Instance Pool ===")
print(get_node_instance_pool().get_stats())

print("\n=== Node Cache ===")
print(get_node_cache().get_stats())

print("\n=== Import Metrics ===")
print(get_import_stats())
```

---

## Summary

**Active Optimizations:** 4 patterns integrated across 3 modules
**Potential Savings:** 500-1500ms per workflow (with Phase 2 integration)
**High Priority:** Lazy loading for desktop automation (300-600ms)
**Medium Priority:** Browser/HTTP pooling (500-1000ms cumulative)
**Effort:** Low (most infrastructure already built, just needs integration)
