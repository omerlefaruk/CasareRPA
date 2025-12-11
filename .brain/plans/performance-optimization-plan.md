# Performance Optimization Plan: Node Creation & Boot Time

## Executive Summary

After analyzing the codebase, I've identified several performance bottlenecks in both **node creation** and **application boot time**. The good news is that significant optimization work has already been done (lazy widget initialization, LOD rendering, etc.), but there are still opportunities for improvement.

---

## Part 1: Node Creation Performance

### Current State Analysis

Node creation flow:
1. User right-clicks → context menu → selects node
2. `graph.create_node()` called in [node_registry.py:674-686](src/casare_rpa/presentation/canvas/graph/node_registry.py#L674-L686)
3. `VisualNode.__init__()` called in [base_visual_node.py:37-125](src/casare_rpa/presentation/canvas/visual_nodes/base_visual_node.py#L37-L125)
4. CasareNodeItem created as graphics item
5. Auto-create CasareRPA node via `_auto_create_casare_node()`
6. Setup ports, widgets, colors

### Identified Bottlenecks

#### 1. **CasareRPA Node Mapping Lookup (Medium Impact)**
- Location: [base_visual_node.py:540-547](src/casare_rpa/presentation/canvas/visual_nodes/base_visual_node.py#L540-L547)
- Issue: `get_casare_node_mapping()` is called for EVERY node creation
- The mapping is cached globally, but the lookup itself happens in `_auto_create_casare_node()`

#### 2. **Port Type Registry Access (Low-Medium Impact)**
- Location: [base_visual_node.py:61](src/casare_rpa/presentation/canvas/visual_nodes/base_visual_node.py#L61)
- Issue: `get_port_type_registry()` called per node creation
- This is a function call that could be a direct reference

#### 3. **Color Initialization on Every Node (Low Impact)**
- Location: [base_visual_node.py:72](src/casare_rpa/presentation/canvas/visual_nodes/base_visual_node.py#L72)
- Issue: `_apply_category_colors()` imports and looks up colors per node
- Category colors are static and could be cached at class level

#### 4. **Schema Widget Auto-Creation (Medium Impact)**
- Location: [base_visual_node.py:108](src/casare_rpa/presentation/canvas/visual_nodes/base_visual_node.py#L108)
- Issue: `_auto_create_widgets_from_schema()` iterates schema properties
- Already optimized with lazy widget embedding, but schema parsing still happens

#### 5. **CasareNodeItem Color Initialization (Low Impact)**
- Location: [custom_node_item.py:487-495](src/casare_rpa/presentation/canvas/graph/custom_node_item.py#L487-L495)
- Issue: Theme colors fetched per node via `Theme.get_*()` calls
- These are cached internally but still involve function call overhead

### Optimization Recommendations

#### Priority 1: Cache Class-Level Lookups
```python
# In VisualNode class - cache mapping at class level
_cached_casare_class: Optional[Type] = None

@classmethod
def _get_casare_class(cls) -> Optional[Type]:
    if cls._cached_casare_class is None:
        mapping = get_casare_node_mapping()
        cls._cached_casare_class = mapping.get(cls)
    return cls._cached_casare_class
```

#### Priority 2: Pre-compute Category Colors
```python
# In VisualNode - compute once per class
_cached_category_color: Optional[tuple] = None

def _apply_category_colors(self) -> None:
    if type(self)._cached_category_color is None:
        from casare_rpa.presentation.canvas.graph.node_icons import CATEGORY_COLORS
        type(self)._cached_category_color = CATEGORY_COLORS.get(
            self.NODE_CATEGORY, QColor(62, 62, 66)
        )
    # Use cached value...
```

#### Priority 3: Defer Schema Parsing
```python
# Move schema widget creation to lazy initialization
def _auto_create_widgets_from_schema(self) -> None:
    # Skip during construction - do on first expand
    if not self._widgets_initialized:
        return
    # ... existing logic
```

#### Priority 4: Use Direct Module References
```python
# Instead of function calls, use direct references
from casare_rpa.application.services.port_type_service import _port_type_registry
# Use _port_type_registry directly instead of get_port_type_registry()
```

---

## Part 2: Application Boot Time

### Current State Analysis

Boot sequence in [app.py](src/casare_rpa/presentation/canvas/app.py):
1. `setup_logging()` - Fast
2. `_setup_qt_application()` - Fast
3. `ensure_playwright_ready()` - **SLOW** (checks browser installation)
4. `_create_ui()` - Medium (creates MainWindow, NodeGraphWidget)
5. `_initialize_components()` - **SLOW**:
   - NodeController → `_initialize_node_registry()` → registers ALL node types
   - Icon atlas preloading
   - Multiple controller initializations

### Identified Bottlenecks

#### 1. **Node Registry Initialization (HIGH Impact)**
- Location: [node_controller.py:56-82](src/casare_rpa/presentation/canvas/controllers/node_controller.py#L56-L82)
- Issue: `register_all_nodes()` loads ALL ~300+ visual node classes at startup
- This triggers module imports for every category

#### 2. **ALL_VISUAL_NODE_CLASSES Loading (HIGH Impact)**
- Location: [visual_nodes/__init__.py:543-575](src/casare_rpa/presentation/canvas/visual_nodes/__init__.py#L543-L575)
- Issue: `get_all_visual_node_classes()` imports ALL node modules on first access
- Called during node registration

#### 3. **CasareRPA Node Mapping Build (HIGH Impact)**
- Location: [node_registry.py:26-127](src/casare_rpa/presentation/canvas/graph/node_registry.py#L26-L127)
- Issue: `_build_casare_node_mapping()` iterates all visual classes and imports their CasareRPA counterparts
- Called in `get_casare_node_mapping()` during `_initialize_node_registry()`

#### 4. **Icon Atlas Preloading (Medium Impact)**
- Location: [app.py:191-200](src/casare_rpa/presentation/canvas/app.py#L191-L200)
- Issue: Preloads all node icons into GPU texture atlas
- Good for runtime performance but adds to boot time

#### 5. **Playwright Browser Check (Medium Impact)**
- Location: [app.py:88](src/casare_rpa/presentation/canvas/app.py#L88)
- Issue: `ensure_playwright_ready()` checks browser installation
- Can be slow on first run or if browsers need downloading

### Optimization Recommendations

#### Priority 1: True Lazy Node Loading
**Current:** All nodes loaded at startup
**Proposed:** Load nodes on-demand when category is first expanded

```python
# In node_registry.py - register category stubs, not full nodes
def register_all_nodes(self, graph: NodeGraph) -> None:
    # Only register frequently-used nodes immediately
    ESSENTIAL_NODES = ["VisualStartNode", "VisualEndNode", "VisualCommentNode"]
    for name in ESSENTIAL_NODES:
        cls = _lazy_import(name)
        self.register_node(cls, graph)

    # Register other categories lazily via menu aboutToShow
    self._pending_categories = set(_VISUAL_NODE_REGISTRY.keys())
```

#### Priority 2: Background Node Registration
```python
# In app.py - use QTimer.singleShot for deferred loading
def _initialize_components(self) -> None:
    # Register essential nodes only
    self._node_controller.initialize_essential()

    # Defer full registration to after window shows
    QTimer.singleShot(100, self._complete_node_registration)
```

#### Priority 3: Parallel Icon Preloading
```python
# Move icon preloading to background thread
from concurrent.futures import ThreadPoolExecutor

def _preload_icons_async():
    executor = ThreadPoolExecutor(max_workers=1)
    executor.submit(preload_node_icons)
```

#### Priority 4: Cache Node Mapping to Disk
```python
# In node_registry.py - cache built mapping to JSON
import json
from pathlib import Path

CACHE_FILE = Path.home() / ".casare_rpa" / "node_mapping_cache.json"

def get_casare_node_mapping() -> Dict[Type, Type]:
    global _casare_node_mapping
    if _casare_node_mapping is None:
        # Try loading from cache first
        if CACHE_FILE.exists():
            _casare_node_mapping = _load_from_cache()
        else:
            _casare_node_mapping = _build_casare_node_mapping()
            _save_to_cache(_casare_node_mapping)
    return _casare_node_mapping
```

#### Priority 5: Defer Playwright Check
```python
# In app.py - check Playwright lazily on first browser node use
def _setup_qt_application(self) -> None:
    # ... existing code ...
    # DON'T call ensure_playwright_ready() here

# Instead, call it when first browser node is created
```

---

## Implementation Plan

### Phase 1: Quick Wins (1-2 hours)
1. Cache category colors at class level in VisualNode
2. Cache CasareRPA class mapping at class level
3. Use direct module references instead of getter functions

### Phase 2: Boot Time Optimization (2-3 hours)
1. Implement essential-only node registration at startup
2. Defer full node registration via QTimer.singleShot
3. Move icon preloading to background

### Phase 3: Advanced Optimization (3-4 hours)
1. Implement disk caching for node mapping
2. True lazy loading per category (on menu expand)
3. Defer Playwright check to first browser node use

---

## Expected Results

| Metric | Current (Est.) | After Phase 1 | After Phase 2 | After Phase 3 |
|--------|---------------|---------------|---------------|---------------|
| Node Creation | ~50-100ms | ~30-50ms | ~30-50ms | ~20-30ms |
| App Boot Time | ~3-5s | ~3-5s | ~1-2s | ~0.5-1s |

---

## Files to Modify

### Phase 1
- [base_visual_node.py](src/casare_rpa/presentation/canvas/visual_nodes/base_visual_node.py) - Class-level caching
- [custom_node_item.py](src/casare_rpa/presentation/canvas/graph/custom_node_item.py) - Direct color references

### Phase 2
- [app.py](src/casare_rpa/presentation/canvas/app.py) - Deferred initialization
- [node_controller.py](src/casare_rpa/presentation/canvas/controllers/node_controller.py) - Split registration
- [node_registry.py](src/casare_rpa/presentation/canvas/graph/node_registry.py) - Essential-only registration

### Phase 3
- [visual_nodes/__init__.py](src/casare_rpa/presentation/canvas/visual_nodes/__init__.py) - Per-category lazy loading
- [node_registry.py](src/casare_rpa/presentation/canvas/graph/node_registry.py) - Disk caching
