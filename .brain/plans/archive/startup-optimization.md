# Application Startup Time Optimization Plan

**Created**: 2025-12-14
**Status**: FULLY IMPLEMENTED (Phase A + B + C)
**Priority**: HIGH
**Target**: Reduce time from launch to interactive window by 40-60%

## Implementation Status

| Phase | Status | Changes |
|-------|--------|---------|
| **A1** | ✅ DONE | Removed early `get_casare_node_mapping()` call |
| **A2** | ✅ DONE | Added module-level stylesheet cache |
| **A3** | ✅ DONE | Staggered controller init (critical → support deferred) |
| **A4** | ✅ DONE | Lazy SearchIndex creation |
| **B1** | ✅ DONE | Incremental node registration (batches of 40) |
| **B2** | ✅ DONE | Two-phase context menu (minimal → full) |
| **C1** | ✅ DONE | Stylesheet disk cache (`~/.casare_rpa/cache/`) |
| **C3** | ✅ DONE | Lazy imports (controllers, NodeGraphWidget) |

## Current Startup Flow Analysis

### Sequence Diagram
```
launch.py
    |
    v
__main__.py -----> imports app.py
    |
    v
CasareRPAApp.__init__()
    |
    +-> setup_logging()
    +-> _setup_qt_application()  [~50ms - QApplication creation, qasync loop]
    +-> _create_ui()             [~150ms - MainWindow + NodeGraphWidget]
    |       |
    |       +-> MainWindow.__init__()
    |       |     +-> ActionManager, MenuBuilder, ToolbarBuilder
    |       |     +-> get_canvas_stylesheet()  [theme parsing]
    |       |     +-> _init_controllers()
    |       +-> WorkflowSerializer/Deserializer
    |       +-> CanvasWorkflowRunner
    |
    +-> window.show() + processEvents()
    +-> _initialize_components()  [~300-500ms - MAIN BOTTLENECK]
    |       |
    |       +-> NodeController.initialize()
    |       |     +-> register_essential_nodes() [~8 nodes, fast]
    |       |     +-> get_casare_node_mapping() [EXPENSIVE - builds full mapping]
    |       +-> Sequential controller init (5 controllers)
    |       +-> set_controllers() on MainWindow
    |       +-> QTimer.singleShot(100, _complete_deferred_initialization)
    |
    +-> _connect_components()
    +-> _connect_ui_signals()
    +-> Restore window title
    |
    v
QTimer.singleShot(100) fires:
    +-> _complete_deferred_initialization()
    |     +-> complete_node_registration()  [~200-400ms - ALL 300+ nodes]
    |           +-> register_remaining_nodes()
    |                 +-> get_all_visual_node_classes()  [imports 40+ modules]
    |                 +-> _rebuild_context_menu()  [builds SearchIndex]
    |
QTimer.singleShot(150) fires:
    +-> load_normal_components() [via UIComponentInitializer]
    |     +-> create_bottom_panel()
    |     +-> create_side_panel()
    |     +-> create_credentials_panel()
    |
QTimer.singleShot(200) fires:
    +-> _start_node_preload() [background thread - non-blocking]
    |
QTimer.singleShot(500) fires:
    +-> _preload_icons_background() [icon atlas - non-blocking]
```

### Existing Optimizations Already in Place
1. Lazy node loading via `NODE_REGISTRY` with `__getattr__`
2. Lazy visual node loading via `_VISUAL_NODE_REGISTRY` with `_lazy_import`
3. Deferred node registration (8 essential nodes first, rest after 100ms)
4. Playwright check deferred to first browser node use
5. Icon preloading moved to background (500ms delay)
6. Node mapping disk cache (`~/.casare_rpa/cache/node_mapping_cache.json`)
7. Background node preloader thread (`preloader.py`)
8. 3-tier UI component loading (CRITICAL/NORMAL/DEFERRED)

### Key Bottlenecks Identified

| Bottleneck | Location | Impact | When |
|------------|----------|--------|------|
| **get_casare_node_mapping()** | node_registry.py:349 | ~150-250ms | During init (line 79 in node_controller.py) |
| **get_all_visual_node_classes()** | visual_nodes/__init__.py | ~200-400ms | When register_remaining_nodes() called |
| **_rebuild_context_menu()** | node_registry.py:1237 | ~100-150ms | After deferred registration |
| **Sequential controller init** | app.py:316-331 | ~50-100ms | 5 controllers one-by-one |
| **get_canvas_stylesheet()** | theme.py:100 | ~20-50ms | MainWindow setup |
| **SearchIndex creation** | node_registry.py (fuzzy_search) | ~30-50ms | During menu build |

---

## Phase A: Quick Wins (1-2 days)

**Target: 150-250ms reduction**

### A1: Defer get_casare_node_mapping() Call

**Problem**: `get_casare_node_mapping()` called during NodeController.initialize() BEFORE window is responsive.

**Current Code** (`node_controller.py:78-79`):
```python
def _initialize_node_registry(self) -> None:
    # ...
    node_registry.register_essential_nodes(graph)
    get_casare_node_mapping()  # EXPENSIVE - called too early
```

**Solution**: Remove the early call - mapping is built lazily anyway when needed.

**Files to Modify**:
- `src/casare_rpa/presentation/canvas/controllers/node_controller.py`

**Implementation**:
```python
def _initialize_node_registry(self) -> None:
    """Initialize node registry with essential nodes only."""
    try:
        from ..graph.node_registry import get_node_registry
        # REMOVED: get_casare_node_mapping() - now built on-demand when first node created

        graph = self._get_graph()
        if not graph:
            return

        node_registry = get_node_registry()
        node_registry.register_essential_nodes(graph)

        logger.debug("Essential nodes registered - mapping deferred to first use")
    except Exception as e:
        logger.error(f"Failed to initialize node registry: {e}")
```

**Expected Gain**: 100-200ms
**Risk**: LOW - mapping is already lazy, just removing redundant call

---

### A2: Cache Stylesheet at Module Level

**Problem**: `get_canvas_stylesheet()` rebuilds stylesheet string each time called.

**Current Flow**:
```python
# main_window.py:185
self.setStyleSheet(get_canvas_stylesheet())  # Called fresh each time
```

**Solution**: Cache the stylesheet at module level since theme doesn't change.

**Files to Modify**:
- `src/casare_rpa/presentation/canvas/theme.py`

**Implementation**:
```python
# At module level
_CACHED_STYLESHEET: Optional[str] = None

def get_canvas_stylesheet() -> str:
    """Get the canvas stylesheet (cached after first call)."""
    global _CACHED_STYLESHEET
    if _CACHED_STYLESHEET is not None:
        return _CACHED_STYLESHEET

    # Build stylesheet (existing logic)
    stylesheet = _get_canvas_stylesheet(THEME)
    _CACHED_STYLESHEET = stylesheet
    return stylesheet

def invalidate_stylesheet_cache() -> None:
    """Invalidate the stylesheet cache (call if theme changes)."""
    global _CACHED_STYLESHEET
    _CACHED_STYLESHEET = None
```

**Expected Gain**: 15-30ms
**Risk**: VERY LOW - theme is static

---

### A3: Parallel Controller Initialization

**Problem**: 5 controllers initialized sequentially.

**Current Code** (`app.py:316-331`):
```python
phase_2_controllers = [
    self._workflow_controller,
    self._execution_controller,
    self._selector_controller,
    self._preferences_controller,
    self._autosave_controller,
]

for controller in phase_2_controllers:
    controller.initialize()  # Sequential
```

**Solution**: Initialize independent controllers in parallel using ThreadPoolExecutor.

**Files to Modify**:
- `src/casare_rpa/presentation/canvas/app.py`

**Implementation**:
```python
def _initialize_components(self) -> None:
    from PySide6.QtCore import QTimer
    from concurrent.futures import ThreadPoolExecutor, as_completed

    # Phase 1: Node registry (must be first, sequential)
    self._node_controller = NodeController(self._main_window)
    self._node_controller.initialize()

    # Phase 2: Other controllers (can be parallelized - no cross-deps)
    logger.debug("Phase 2: Initializing controllers in parallel...")

    # Create all controllers first (fast)
    self._workflow_controller = WorkflowController(self._main_window)
    self._execution_controller = ExecutionController(self._main_window)
    self._selector_controller = SelectorController(self._main_window)
    self._preferences_controller = PreferencesController(self._main_window)
    self._autosave_controller = AutosaveController(self._main_window)

    controllers = [
        self._workflow_controller,
        self._execution_controller,
        self._selector_controller,
        self._preferences_controller,
        self._autosave_controller,
    ]

    # Initialize in parallel (most init work is I/O or computation)
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(c.initialize): c for c in controllers}
        for future in as_completed(futures):
            controller = futures[future]
            try:
                future.result()
                logger.debug(f"{controller.__class__.__name__} initialized")
            except Exception as e:
                error_msg = f"Failed to init {controller.__class__.__name__}: {e}"
                logger.error(error_msg)
                raise RuntimeError(error_msg) from e

    # Rest continues as before...
```

**Expected Gain**: 30-50ms
**Risk**: MEDIUM - need to verify controllers are thread-safe during init
**Note**: May need to skip if any controller touches Qt widgets during init

---

### A4: Lazy SearchIndex in Context Menu

**Problem**: SearchIndex built immediately when context menu is created.

**Current Code** (`node_registry.py:921`):
```python
# Pre-build SearchIndex for lightning-fast search
qmenu._search_index = SearchIndex(qmenu._node_items)
```

**Solution**: Build SearchIndex on first search, not on menu creation.

**Files to Modify**:
- `src/casare_rpa/presentation/canvas/graph/node_registry.py`

**Implementation**:
```python
# In register_all_nodes() and _rebuild_context_menu()

# Replace immediate SearchIndex creation:
qmenu._search_index = None  # Build on first search
qmenu._node_items = []  # Still collect items for later indexing

# Modify on_search_changed():
def on_search_changed(text):
    # Lazy build SearchIndex on first search
    if qmenu._search_index is None and qmenu._node_items:
        from casare_rpa.utils.fuzzy_search import SearchIndex
        qmenu._search_index = SearchIndex(qmenu._node_items)

    # Rest of search logic...
```

**Expected Gain**: 20-40ms (moved from startup to first context menu search)
**Risk**: LOW - slight delay on first search, unnoticeable

---

## Phase B: Medium Effort (2-3 days)

**Target: 100-200ms additional reduction**

### B1: Incremental Visual Node Registration

**Problem**: `register_remaining_nodes()` imports ALL 300+ visual node modules at once.

**Current Code** (`node_registry.py:1218-1232`):
```python
def register_remaining_nodes(self, graph: NodeGraph) -> None:
    from casare_rpa.presentation.canvas.visual_nodes import ALL_VISUAL_NODE_CLASSES
    # This triggers loading ALL visual node modules

    for node_class in ALL_VISUAL_NODE_CLASSES:
        if node_class.NODE_NAME not in already_registered:
            self.register_node(node_class, graph)
```

**Solution**: Batch registration over multiple frames to avoid UI freeze.

**Files to Modify**:
- `src/casare_rpa/presentation/canvas/graph/node_registry.py`
- `src/casare_rpa/presentation/canvas/controllers/node_controller.py`

**Implementation**:
```python
# In node_registry.py

def register_remaining_nodes_incremental(
    self,
    graph: NodeGraph,
    batch_size: int = 50,
    callback: Optional[callable] = None
) -> None:
    """
    Register remaining nodes incrementally in batches.

    Args:
        graph: NodeGraph to register with
        batch_size: Number of nodes per batch
        callback: Called after each batch with (completed, total)
    """
    from casare_rpa.presentation.canvas.visual_nodes import (
        _VISUAL_NODE_REGISTRY,
        _lazy_import,
    )

    already_registered = set(self._registered_nodes.keys())
    remaining = [
        name for name in _VISUAL_NODE_REGISTRY.keys()
        if name not in already_registered
    ]

    self._pending_registration = remaining
    self._registration_graph = graph
    self._registration_callback = callback
    self._batch_size = batch_size

    # Start first batch
    self._register_next_batch()

def _register_next_batch(self) -> None:
    """Register next batch of nodes."""
    if not self._pending_registration:
        # All done - rebuild context menu
        self._rebuild_context_menu(self._registration_graph)
        if self._registration_callback:
            total = len(self._registered_nodes)
            self._registration_callback(total, total)
        return

    from casare_rpa.presentation.canvas.visual_nodes import _lazy_import
    from PySide6.QtCore import QTimer

    batch = self._pending_registration[:self._batch_size]
    self._pending_registration = self._pending_registration[self._batch_size:]

    for name in batch:
        try:
            node_class = _lazy_import(name)
            self.register_node(node_class, self._registration_graph)
        except Exception as e:
            logger.warning(f"Failed to register {name}: {e}")

    # Progress callback
    if self._registration_callback:
        done = len(self._registered_nodes)
        total = done + len(self._pending_registration)
        self._registration_callback(done, total)

    # Schedule next batch (yield to event loop)
    QTimer.singleShot(0, self._register_next_batch)
```

**Files to Modify** (`node_controller.py`):
```python
def complete_node_registration(self) -> None:
    """Complete node registration incrementally."""
    try:
        from ..graph.node_registry import get_node_registry

        graph = self._get_graph()
        if not graph:
            return

        node_registry = get_node_registry()

        # Use incremental registration to avoid UI freeze
        node_registry.register_remaining_nodes_incremental(
            graph,
            batch_size=40,  # ~40 nodes per frame
            callback=self._on_registration_progress,
        )
    except Exception as e:
        logger.error(f"Failed to complete node registration: {e}")

def _on_registration_progress(self, completed: int, total: int) -> None:
    """Handle registration progress updates."""
    if completed == total:
        logger.info(f"Full node registration completed: {total} nodes")
```

**Expected Gain**: 150-300ms (spread over time, no UI freeze)
**Risk**: MEDIUM - context menu may show incomplete list briefly

---

### B2: Two-Phase Context Menu

**Problem**: Full context menu rebuilt after all nodes registered.

**Solution**: Build minimal menu first, then enhance with all nodes later.

**Files to Modify**:
- `src/casare_rpa/presentation/canvas/graph/node_registry.py`

**Implementation**:
```python
def register_essential_nodes(self, graph: NodeGraph) -> None:
    """Register essential nodes and create minimal context menu."""
    # ... existing registration ...

    # Build minimal menu with just essential nodes
    self._build_minimal_context_menu(graph)
    logger.debug(f"Registered {registered_count} essential nodes with minimal menu")

def _build_minimal_context_menu(self, graph: NodeGraph) -> None:
    """Build a minimal context menu with just essential nodes."""
    graph_menu = graph.get_context_menu("graph")
    qmenu = graph_menu.qmenu
    qmenu.clear()

    # Add search input (same as full menu)
    self._add_search_widget(qmenu, graph)

    # Add essential categories only
    essential_categories = {"basic", "control_flow", "variable", "utility"}
    for category, nodes in self._categories.items():
        root_cat = category.split("/")[0]
        if root_cat in essential_categories:
            # Add category and nodes...
            pass

    # Add "Loading more nodes..." placeholder
    loading_action = qmenu.addAction("Loading more nodes...")
    loading_action.setEnabled(False)
    qmenu._loading_action = loading_action
```

**Expected Gain**: 50-100ms (user sees functional menu immediately)
**Risk**: LOW - clear UX that more nodes are loading

---

### B3: Deferred Theme Import Chain

**Problem**: Theme module imports entire `theme_system` package upfront.

**Current Code** (`theme.py:24-91`):
```python
# Re-export colors module
from casare_rpa.presentation.canvas.theme_system.colors import (...)
# Re-export constants module
from casare_rpa.presentation.canvas.theme_system.constants import (...)
# Re-export styles module
from casare_rpa.presentation.canvas.theme_system.styles import (...)
# Re-export utils module
from casare_rpa.presentation.canvas.theme_system.utils import (...)
```

**Solution**: Lazy import theme submodules.

**Files to Modify**:
- `src/casare_rpa/presentation/canvas/theme.py`

**Implementation**:
```python
"""Theme compatibility layer with lazy imports."""

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Import for type hints only - not at runtime
    from casare_rpa.presentation.canvas.theme_system.colors import CanvasThemeColors
    # ... other type imports

# Lazy loading helpers
_colors_module = None
_constants_module = None
_styles_module = None
_utils_module = None

def _get_colors():
    global _colors_module
    if _colors_module is None:
        from casare_rpa.presentation.canvas.theme_system import colors
        _colors_module = colors
    return _colors_module

def _get_styles():
    global _styles_module
    if _styles_module is None:
        from casare_rpa.presentation.canvas.theme_system import styles
        _styles_module = styles
    return _styles_module

# Main exports (computed properties)
@property
def THEME():
    return _get_colors().CanvasThemeColors()

def get_canvas_stylesheet() -> str:
    return _get_styles().get_canvas_stylesheet(THEME)
```

**Expected Gain**: 10-20ms
**Risk**: LOW - maintains compatibility

---

## Phase C: Advanced Optimizations (3-5 days)

**Target: 50-100ms additional reduction**

### C1: Compiled Stylesheet Cache

**Problem**: Stylesheet string built and parsed by Qt on each startup.

**Solution**: Pre-compile stylesheet to QSS and cache to disk.

**Files to Create**:
- `src/casare_rpa/presentation/canvas/theme_system/stylesheet_cache.py`

**Implementation**:
```python
"""
Stylesheet disk cache for faster startup.

Caches the compiled stylesheet to avoid rebuilding on each startup.
Cache invalidated when theme version changes.
"""

import hashlib
from pathlib import Path
from typing import Optional

from loguru import logger

_CACHE_DIR = Path.home() / ".casare_rpa" / "cache"
_STYLESHEET_CACHE_FILE = _CACHE_DIR / "stylesheet_cache.qss"
_STYLESHEET_HASH_FILE = _CACHE_DIR / "stylesheet_hash.txt"
_THEME_VERSION = "1.0.0"  # Bump when theme changes


def _compute_theme_hash() -> str:
    """Compute hash of theme configuration."""
    from casare_rpa.presentation.canvas.theme_system.colors import CanvasThemeColors
    theme = CanvasThemeColors()
    theme_str = f"{_THEME_VERSION}:{theme.__dict__}"
    return hashlib.md5(theme_str.encode()).hexdigest()[:12]


def get_cached_stylesheet() -> Optional[str]:
    """Load stylesheet from cache if valid."""
    try:
        if not _STYLESHEET_CACHE_FILE.exists():
            return None
        if not _STYLESHEET_HASH_FILE.exists():
            return None

        # Check hash
        stored_hash = _STYLESHEET_HASH_FILE.read_text().strip()
        current_hash = _compute_theme_hash()
        if stored_hash != current_hash:
            logger.debug("Stylesheet cache invalidated (theme changed)")
            return None

        stylesheet = _STYLESHEET_CACHE_FILE.read_text()
        logger.debug("Loaded stylesheet from cache")
        return stylesheet
    except Exception as e:
        logger.debug(f"Stylesheet cache miss: {e}")
        return None


def cache_stylesheet(stylesheet: str) -> None:
    """Save stylesheet to cache."""
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        _STYLESHEET_CACHE_FILE.write_text(stylesheet)
        _STYLESHEET_HASH_FILE.write_text(_compute_theme_hash())
        logger.debug("Stylesheet cached to disk")
    except Exception as e:
        logger.warning(f"Failed to cache stylesheet: {e}")
```

**Integration** (`theme.py`):
```python
def get_canvas_stylesheet() -> str:
    """Get the canvas stylesheet (with disk caching)."""
    from .theme_system.stylesheet_cache import (
        get_cached_stylesheet,
        cache_stylesheet,
    )

    # Try cache first
    cached = get_cached_stylesheet()
    if cached is not None:
        return cached

    # Build stylesheet
    stylesheet = _get_canvas_stylesheet(THEME)

    # Cache for next time
    cache_stylesheet(stylesheet)
    return stylesheet
```

**Expected Gain**: 15-25ms (on cache hit)
**Risk**: LOW - fallback to fresh build

---

### C2: Background Context Menu Build

**Problem**: Full context menu built on main thread.

**Solution**: Build menu structure in background, apply to QMenu on main thread.

**Files to Modify**:
- `src/casare_rpa/presentation/canvas/graph/node_registry.py`

**Implementation**:
```python
import threading
from dataclasses import dataclass
from typing import List, Dict, Callable

@dataclass
class MenuItemData:
    """Pre-computed menu item data."""
    category: str
    name: str
    identifier: str
    node_class: type
    is_internal: bool


class BackgroundMenuBuilder:
    """Builds menu structure data in background thread."""

    def __init__(self, categories: Dict[str, List[type]]):
        self._categories = categories
        self._items: List[MenuItemData] = []
        self._ready = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start_build(self) -> None:
        """Start background menu data computation."""
        self._thread = threading.Thread(
            target=self._build_worker,
            daemon=True,
        )
        self._thread.start()

    def _build_worker(self) -> None:
        """Background worker that computes menu structure."""
        try:
            for category, nodes in sorted(self._categories.items()):
                for node_class in sorted(nodes, key=lambda x: x.NODE_NAME):
                    self._items.append(MenuItemData(
                        category=category,
                        name=node_class.NODE_NAME,
                        identifier=f"{node_class.__identifier__}.{node_class.__name__}",
                        node_class=node_class,
                        is_internal=getattr(node_class, "INTERNAL_NODE", False),
                    ))
        finally:
            self._ready.set()

    def get_items(self, timeout: float = 2.0) -> List[MenuItemData]:
        """Get computed menu items (blocks until ready)."""
        self._ready.wait(timeout=timeout)
        return self._items
```

**Expected Gain**: 30-50ms (overlaps with other init)
**Risk**: MEDIUM - thread synchronization complexity

---

### C3: Import-Time Optimization

**Problem**: Module imports at startup take significant time.

**Solution**: Audit and optimize import chains.

**Files to Audit**:
- `src/casare_rpa/presentation/canvas/app.py`
- `src/casare_rpa/presentation/canvas/main_window.py`

**Implementation**: Use lazy imports for heavy dependencies.

```python
# Before (top of app.py):
from casare_rpa.presentation.canvas.controllers import (
    WorkflowController,
    ExecutionController,
    NodeController,
    SelectorController,
    PreferencesController,
    AutosaveController,
)

# After (inside _initialize_components):
def _initialize_components(self) -> None:
    # Defer heavy imports until needed
    from casare_rpa.presentation.canvas.controllers import (
        WorkflowController,
        ExecutionController,
        NodeController,
        SelectorController,
        PreferencesController,
        AutosaveController,
    )
    # ... rest of init
```

**Expected Gain**: 20-40ms
**Risk**: LOW - just import timing changes

---

## Implementation Priority Matrix

| Optimization | Impact | Effort | Risk | Priority |
|--------------|--------|--------|------|----------|
| A1: Defer mapping call | 100-200ms | 0.5 day | LOW | P0 |
| A2: Cache stylesheet | 15-30ms | 0.25 day | VERY LOW | P0 |
| A4: Lazy SearchIndex | 20-40ms | 0.25 day | LOW | P0 |
| B1: Incremental registration | 150-300ms | 1.5 days | MEDIUM | P1 |
| B2: Two-phase menu | 50-100ms | 1 day | LOW | P1 |
| A3: Parallel controllers | 30-50ms | 0.5 day | MEDIUM | P2 |
| C1: Stylesheet disk cache | 15-25ms | 0.5 day | LOW | P2 |
| B3: Lazy theme imports | 10-20ms | 0.5 day | LOW | P3 |
| C2: Background menu build | 30-50ms | 1 day | MEDIUM | P3 |
| C3: Import optimization | 20-40ms | 1 day | LOW | P3 |

---

## Implementation Order

### Day 1: Quick Wins (P0)
1. **A1**: Remove `get_casare_node_mapping()` early call
2. **A2**: Add module-level stylesheet cache
3. **A4**: Lazy SearchIndex creation

**Expected Total Gain**: 135-270ms

### Days 2-3: Medium Effort (P1)
4. **B1**: Implement incremental node registration
5. **B2**: Two-phase context menu

**Expected Additional Gain**: 200-400ms

### Days 4-5: Advanced (P2-P3)
6. **A3**: Parallel controller initialization (if safe)
7. **C1**: Stylesheet disk cache
8. **C3**: Import chain optimization

**Expected Additional Gain**: 65-115ms

---

## Test Plan

### Performance Benchmarks

```python
# tests/performance/test_startup.py

import time
import subprocess
import sys

def test_startup_time():
    """Application should be interactive within 2 seconds."""
    start = time.perf_counter()

    # Launch app with startup marker
    proc = subprocess.Popen(
        [sys.executable, "-m", "casare_rpa.presentation.canvas"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for "ready" marker or timeout
    # ... implementation details ...

    elapsed = time.perf_counter() - start
    assert elapsed < 2.0, f"Startup took {elapsed:.2f}s"


def test_node_registration_time():
    """Full node registration should complete within 500ms."""
    from casare_rpa.presentation.canvas.graph.node_registry import (
        get_node_registry,
        NodeRegistry,
    )

    registry = NodeRegistry()
    # ... mock graph setup ...

    start = time.perf_counter()
    registry.register_all_nodes(mock_graph)
    elapsed = (time.perf_counter() - start) * 1000

    assert elapsed < 500, f"Registration took {elapsed:.1f}ms"
```

### Regression Tests

```python
def test_context_menu_has_all_nodes():
    """Context menu should show all non-internal nodes."""
    # ... test that after registration, all nodes are in menu

def test_essential_nodes_registered_first():
    """Essential nodes should be available immediately."""
    # ... test StartNode, EndNode, IfNode available before full registration
```

---

## Risk Mitigation

### R1: Thread Safety During Parallel Init
**Risk**: Controllers may touch Qt widgets during initialize().
**Mitigation**: Audit each controller's init method. If any touches Qt, fall back to sequential.

### R2: Incomplete Context Menu
**Risk**: User right-clicks before all nodes registered.
**Mitigation**: Show "Loading more nodes..." indicator, essential nodes always available.

### R3: Stylesheet Cache Invalidation
**Risk**: Stale cached stylesheet after theme change.
**Mitigation**: Version-based cache key, invalidate on theme module change.

### R4: Race Conditions in Background Menu Build
**Risk**: Main thread accesses menu items before ready.
**Mitigation**: Use threading.Event for synchronization, timeout fallback to sync build.

---

## Success Criteria

1. **Time to Interactive**: Window responsive in <1.5 seconds (down from ~2.5s)
2. **Context Menu Latency**: First context menu shows in <100ms
3. **No UI Freeze**: No perceptible freeze during startup
4. **Full Functionality**: All 300+ nodes available within 3 seconds
5. **No Regressions**: All existing tests pass

---

## Related Documentation

- `.brain/plans/workflow-loading-optimization.md` - Workflow loading optimizations
- `src/casare_rpa/presentation/canvas/app.py` - Main application class
- `src/casare_rpa/presentation/canvas/graph/node_registry.py` - Node registration
- `src/casare_rpa/presentation/canvas/visual_nodes/__init__.py` - Visual node registry
- `src/casare_rpa/nodes/preloader.py` - Background node preloader
