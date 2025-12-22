# Workflow Loading Performance Optimization Plan

**Created**: 2025-12-14
**Status**: IMPLEMENTED (Phase C Complete)
**Priority**: HIGH
**Estimated Total Impact**: 300-500ms reduction on typical workflow load

## Implementation Status

| Phase | Status | Files |
|-------|--------|-------|
| Phase A | PENDING | Quick wins not yet implemented |
| Phase B | PENDING | Medium effort not yet implemented |
| **Phase C** | **COMPLETE** | Advanced optimizations implemented |

### Phase C Implementation (2025-12-14)

**Files Created:**
- `src/casare_rpa/utils/workflow/incremental_loader.py` - Skeleton loading for previews
- `tests/performance/test_workflow_loading.py` - 70 comprehensive tests
- `tests/performance/conftest.py` - Test fixtures

**Files Modified:**
- `src/casare_rpa/utils/performance/object_pool.py` - Added NodeInstancePool
- `src/casare_rpa/utils/workflow/workflow_loader.py` - Added parallel instantiation

**Test Results:** 70/70 tests passing

## Executive Summary

This plan addresses workflow loading bottlenecks identified in:
- `src/casare_rpa/utils/workflow/workflow_loader.py` (479 lines)
- `src/casare_rpa/presentation/canvas/serialization/workflow_deserializer.py` (509 lines)
- `src/casare_rpa/nodes/__init__.py` (lazy loading)
- `src/casare_rpa/utils/workflow/compressed_io.py` (file I/O)

### Key Bottlenecks Identified

| Bottleneck | Impact | Effort |
|------------|--------|--------|
| Full Node Class Loading via `get_all_node_classes()` | HIGH (~500ms) | LOW |
| Multiple Validation Passes | MEDIUM (~100ms) | LOW |
| Sequential Node Instantiation | MEDIUM (~150ms) | MEDIUM |
| No Workflow Caching | MEDIUM (~200ms) | MEDIUM |
| Non-streaming File I/O | LOW (~50ms) | HIGH |

### Existing Optimizations (Leverage These)

1. **Lazy Module Loading** - `NODE_REGISTRY` with `__getattr__` (already working)
2. **Class Caching** - `_loaded_modules` and `_loaded_classes` dicts
3. **Background Preloader** - `preloader.py` with priority-ordered loading
4. **Object Pooling** - `ObjectPool` and `WeakNodeCache` in `utils/performance/`
5. **Variable Resolution Cache** - `VariableResolutionCache` pattern to follow
6. **Compression Support** - gzip/zstandard already implemented

---

## Phase A: Quick Wins (1-2 days)

**Target: 200-300ms reduction**

### A1: Eliminate Redundant Validation Passes

**Problem**: Workflow validated 2-3 times:
1. `validate_workflow_structure()` in `workflow_loader.py`
2. `validate_workflow_json()` in `workflow_deserializer.py`
3. Individual node validation during instantiation

**Solution**: Single-pass validation with result caching.

**Files to Modify**:
- `src/casare_rpa/utils/workflow/workflow_loader.py`
- `src/casare_rpa/presentation/canvas/serialization/workflow_deserializer.py`

**Implementation**:
```python
# Add validation result marker to workflow_data
def validate_workflow_structure(workflow_data: Dict) -> Dict:
    """Validate and mark workflow as validated."""
    # ... existing validation ...
    workflow_data["__validated__"] = True  # Internal marker
    return workflow_data

# In deserializer - skip if already validated
def deserialize(self, workflow_data: Dict) -> bool:
    if not workflow_data.get("__validated__"):
        validate_workflow_json(workflow_data)
    # ...
```

**Expected Gain**: 50-100ms

### A2: Batch Node Type Resolution

**Problem**: `_resolve_node_type_alias()` called for each node individually.

**Solution**: Pre-resolve all node types in batch before instantiation.

**Files to Modify**:
- `src/casare_rpa/utils/workflow/workflow_loader.py`

**Implementation**:
```python
def load_workflow_from_dict(workflow_data: Dict, skip_validation: bool = False) -> WorkflowSchema:
    # ... validation ...

    nodes_data = workflow_data.get("nodes", {})

    # Batch resolve all node types first
    resolved_types = _batch_resolve_node_types(nodes_data)

    # Now instantiate with pre-resolved types
    for node_id, node_data in nodes_data.items():
        node_type, config = resolved_types[node_id]
        # ...
```

**Expected Gain**: 20-30ms

### A3: Avoid NODE_TYPE_MAP Full Build

**Problem**: `_NodeTypeMapProxy.items()` and `values()` call `_get_node_type_map()` which loads ALL 400+ nodes.

**Solution**: Make proxy methods lazy - only load requested nodes.

**Files to Modify**:
- `src/casare_rpa/utils/workflow/workflow_loader.py`

**Implementation**:
```python
class _NodeTypeMapProxy:
    """Lazy proxy that avoids loading all nodes."""

    def items(self):
        # Only load nodes that were previously accessed
        for name in self._accessed_names:
            yield name, _lazy_import(name)

    def values(self):
        for name in self._accessed_names:
            yield _lazy_import(name)
```

**Expected Gain**: 100-200ms (prevents accidental full load)

### A4: Cache Node Type Map in Deserializer

**Problem**: `_build_node_type_map()` scans all registered nodes on each load.

**Solution**: Cache the node type map after first build.

**Files to Modify**:
- `src/casare_rpa/presentation/canvas/serialization/workflow_deserializer.py`

**Implementation**:
```python
# Module-level cache
_NODE_TYPE_MAP_CACHE: Optional[Dict[str, str]] = None

class WorkflowDeserializer:
    def _get_node_type_map(self) -> Dict[str, str]:
        global _NODE_TYPE_MAP_CACHE
        if _NODE_TYPE_MAP_CACHE is not None:
            return _NODE_TYPE_MAP_CACHE
        if self._node_type_map is None:
            self._node_type_map = self._build_node_type_map()
            _NODE_TYPE_MAP_CACHE = self._node_type_map
        return self._node_type_map
```

**Expected Gain**: 30-50ms on subsequent loads

---

## Phase B: Medium Effort (3-5 days)

**Target: 100-200ms additional reduction**

### B1: Workflow Schema Caching

**Problem**: Same workflows re-parsed from scratch on each load.

**Solution**: Create `WorkflowCache` that caches parsed workflows by content hash.

**Files to Create**:
- `src/casare_rpa/infrastructure/caching/workflow_cache.py`

**Implementation**:
```python
"""
Workflow Cache for CasareRPA.

Caches parsed workflow schemas to avoid redundant parsing.
Uses content fingerprinting for cache invalidation.
"""

import hashlib
from typing import Optional, Dict, Any
from collections import OrderedDict
import threading

from casare_rpa.domain.entities.workflow import WorkflowSchema


class WorkflowCache:
    """
    LRU cache for parsed workflow schemas.

    Cache key: SHA-256 hash of workflow JSON content
    Cache value: Parsed WorkflowSchema

    Thread-safe with configurable max size.
    """

    def __init__(self, max_size: int = 20):
        self._max_size = max_size
        self._cache: OrderedDict[str, WorkflowSchema] = OrderedDict()
        self._lock = threading.RLock()

        # Statistics
        self._hits = 0
        self._misses = 0

    @staticmethod
    def compute_fingerprint(workflow_data: Dict[str, Any]) -> str:
        """Compute content hash for workflow data."""
        import orjson
        content = orjson.dumps(workflow_data, option=orjson.OPT_SORT_KEYS)
        return hashlib.sha256(content).hexdigest()[:16]

    def get(self, fingerprint: str) -> Optional[WorkflowSchema]:
        """Get cached workflow by fingerprint."""
        with self._lock:
            if fingerprint in self._cache:
                self._hits += 1
                self._cache.move_to_end(fingerprint)
                # Return a shallow copy to prevent mutation
                return self._cache[fingerprint]
            self._misses += 1
            return None

    def put(self, fingerprint: str, workflow: WorkflowSchema) -> None:
        """Cache a parsed workflow."""
        with self._lock:
            if len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)  # LRU eviction
            self._cache[fingerprint] = workflow

    def invalidate(self, fingerprint: str) -> None:
        """Invalidate a specific cache entry."""
        with self._lock:
            self._cache.pop(fingerprint, None)

    def clear(self) -> None:
        """Clear all cached workflows."""
        with self._lock:
            self._cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total = self._hits + self._misses
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": self._hits / total if total > 0 else 0.0,
            }


# Global instance
_workflow_cache: Optional[WorkflowCache] = None


def get_workflow_cache() -> WorkflowCache:
    """Get global workflow cache singleton."""
    global _workflow_cache
    if _workflow_cache is None:
        _workflow_cache = WorkflowCache()
    return _workflow_cache
```

**Files to Modify**:
- `src/casare_rpa/utils/workflow/workflow_loader.py`

**Integration**:
```python
from casare_rpa.infrastructure.caching.workflow_cache import (
    get_workflow_cache,
    WorkflowCache
)

def load_workflow_from_dict(workflow_data: Dict, skip_validation: bool = False) -> WorkflowSchema:
    cache = get_workflow_cache()
    fingerprint = cache.compute_fingerprint(workflow_data)

    # Check cache first
    cached = cache.get(fingerprint)
    if cached is not None:
        logger.debug(f"Workflow cache hit: {fingerprint}")
        return cached

    # Parse workflow
    workflow = _parse_workflow(workflow_data, skip_validation)

    # Cache result
    cache.put(fingerprint, workflow)
    return workflow
```

**Expected Gain**: 150-200ms on cache hits (common during development)

### B2: Batch Node Preloading During Load

**Problem**: Nodes loaded one-by-one as they're encountered.

**Solution**: Extract unique node types first, batch preload them.

**Files to Modify**:
- `src/casare_rpa/utils/workflow/workflow_loader.py`
- `src/casare_rpa/nodes/__init__.py`

**Implementation**:
```python
# In workflow_loader.py
def _preload_workflow_nodes(nodes_data: Dict[str, Dict]) -> None:
    """Preload all node types used in workflow."""
    unique_types = {
        node_data.get("node_type")
        for node_data in nodes_data.values()
    }
    # Remove None and resolve aliases
    unique_types = {t for t in unique_types if t}
    resolved_types = {
        _resolve_node_type_alias(t, {})[0]
        for t in unique_types
    }

    # Batch preload
    preload_nodes(list(resolved_types))

# In nodes/__init__.py - add batch variant
def preload_nodes_batch(node_names: List[str]) -> Dict[str, Type]:
    """Preload multiple nodes and return loaded classes."""
    result = {}
    for name in node_names:
        if name in NODE_REGISTRY:
            result[name] = _lazy_import(name)
    return result
```

**Expected Gain**: 30-50ms (reduces import overhead)

### B3: Streaming Decompression

**Problem**: Entire file read into memory before decompression.

**Solution**: Use streaming decompression for large files.

**Files to Modify**:
- `src/casare_rpa/utils/workflow/compressed_io.py`

**Implementation**:
```python
def load_workflow_streaming(path: Path) -> Optional[Dict[str, Any]]:
    """
    Load workflow with streaming decompression.

    More memory efficient for large workflows (>1MB).
    """
    if not path.exists():
        return None

    suffix = "".join(path.suffixes).lower()

    try:
        if suffix.endswith(".json.zst"):
            if not ZSTD_AVAILABLE:
                return None
            dctx = zstd.ZstdDecompressor()
            with open(path, "rb") as f:
                with dctx.stream_reader(f) as reader:
                    json_bytes = reader.read()
            return orjson.loads(json_bytes)

        if suffix.endswith(".json.gz"):
            with gzip.open(path, "rb") as f:
                json_bytes = f.read()
            return orjson.loads(json_bytes)

        # Uncompressed - use memory mapping for large files
        file_size = path.stat().st_size
        if file_size > 1_000_000:  # >1MB
            import mmap
            with open(path, "rb") as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    return orjson.loads(mm[:])

        return orjson.loads(path.read_bytes())

    except Exception as e:
        logger.error(f"Failed to load workflow: {e}")
        return None
```

**Expected Gain**: 20-50ms for large workflows

---

## Phase C: Advanced Optimizations (5-10 days)

**Target: 50-100ms additional reduction**

### C1: Incremental Node Loading

**Problem**: All nodes in workflow loaded even if only subset needed.

**Solution**: Support partial workflow loading for quick preview.

**Files to Create**:
- `src/casare_rpa/utils/workflow/incremental_loader.py`

**Implementation**:
```python
"""
Incremental Workflow Loader.

Loads workflow metadata and node skeleton first,
defers full node instantiation until execution.
"""

from dataclasses import dataclass
from typing import Dict, Optional, List

@dataclass
class WorkflowSkeleton:
    """Lightweight workflow representation for preview."""
    name: str
    description: str
    node_count: int
    connection_count: int
    node_types: List[str]
    variables: Dict[str, any]

    # Deferred loading
    _full_data: Optional[Dict] = None
    _loaded: bool = False

class IncrementalLoader:
    """Load workflows incrementally."""

    def load_skeleton(self, workflow_data: Dict) -> WorkflowSkeleton:
        """Fast load - just metadata and counts."""
        metadata = workflow_data.get("metadata", {})
        nodes = workflow_data.get("nodes", {})
        connections = workflow_data.get("connections", [])

        return WorkflowSkeleton(
            name=metadata.get("name", "Untitled"),
            description=metadata.get("description", ""),
            node_count=len(nodes),
            connection_count=len(connections),
            node_types=list({n.get("node_type") for n in nodes.values()}),
            variables=workflow_data.get("variables", {}),
            _full_data=workflow_data,
        )

    def load_full(self, skeleton: WorkflowSkeleton) -> WorkflowSchema:
        """Full load when needed."""
        if skeleton._loaded:
            return skeleton._workflow

        from casare_rpa.utils.workflow.workflow_loader import load_workflow_from_dict
        workflow = load_workflow_from_dict(skeleton._full_data)
        skeleton._workflow = workflow
        skeleton._loaded = True
        return workflow
```

**Use Cases**:
- Recent files list (show skeleton only)
- Workflow browser (preview without full load)
- Search across workflows (index from skeleton)

**Expected Gain**: 200ms+ for preview scenarios

### C2: Node Instance Pooling

**Problem**: Node instances created fresh for each workflow load.

**Solution**: Pool node instances by type, reset config for reuse.

**Files to Modify**:
- `src/casare_rpa/utils/performance/object_pool.py`
- `src/casare_rpa/utils/workflow/workflow_loader.py`

**Implementation**:
```python
# In object_pool.py
class NodeInstancePool:
    """Pool node instances by type for reuse."""

    def __init__(self, max_per_type: int = 10):
        self._pools: Dict[str, deque] = {}
        self._max_per_type = max_per_type
        self._lock = threading.Lock()

    def acquire(self, node_type: str, node_class: Type, node_id: str) -> BaseNode:
        """Get or create node instance."""
        with self._lock:
            pool = self._pools.get(node_type)
            if pool and pool:
                node = pool.pop()
                node.reset(node_id)  # Reset for reuse
                return node

        # Create new
        return node_class(node_id)

    def release(self, node: BaseNode) -> None:
        """Return node to pool."""
        with self._lock:
            node_type = node.node_type
            if node_type not in self._pools:
                self._pools[node_type] = deque()

            pool = self._pools[node_type]
            if len(pool) < self._max_per_type:
                node.clear_ports()  # Clear for reuse
                pool.append(node)
```

**Note**: Requires BaseNode.reset() method.

**Expected Gain**: 30-50ms on repeated loads

### C3: Parallel Node Instantiation

**Problem**: Nodes instantiated sequentially.

**Solution**: Use thread pool for parallel instantiation.

**Files to Modify**:
- `src/casare_rpa/utils/workflow/workflow_loader.py`

**Implementation**:
```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def _instantiate_nodes_parallel(
    nodes_data: Dict[str, Dict],
    resolved_types: Dict[str, tuple],
    max_workers: int = 4
) -> Dict[str, BaseNode]:
    """Instantiate nodes in parallel."""

    def create_node(node_id: str, node_type: str, config: Dict) -> tuple:
        node_class = get_node_class(node_type)
        if node_class is None:
            return node_id, None
        return node_id, node_class(node_id, config=config)

    nodes_dict = {}

    # For small workflows, sequential is faster
    if len(nodes_data) < 20:
        for node_id, node_data in nodes_data.items():
            node_type, config = resolved_types[node_id]
            _, node = create_node(node_id, node_type, config)
            if node:
                nodes_dict[node_id] = node
        return nodes_dict

    # Parallel for large workflows
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for node_id, node_data in nodes_data.items():
            node_type, config = resolved_types[node_id]
            future = executor.submit(create_node, node_id, node_type, config)
            futures.append(future)

        for future in as_completed(futures):
            node_id, node = future.result()
            if node:
                nodes_dict[node_id] = node

    return nodes_dict
```

**Expected Gain**: 50-100ms for workflows with 50+ nodes

---

## Test Plan

### Performance Benchmarks

Create benchmark suite in `tests/performance/`:

```python
# tests/performance/test_workflow_loading.py

import pytest
import time
from pathlib import Path

from casare_rpa.utils.workflow.workflow_loader import load_workflow_from_dict
from casare_rpa.utils.workflow.compressed_io import load_workflow

# Test workflows of various sizes
SMALL_WORKFLOW = "tests/fixtures/workflows/small_10_nodes.json"
MEDIUM_WORKFLOW = "tests/fixtures/workflows/medium_50_nodes.json"
LARGE_WORKFLOW = "tests/fixtures/workflows/large_200_nodes.json"

@pytest.mark.benchmark
class TestWorkflowLoadingPerformance:
    """Workflow loading performance benchmarks."""

    def test_small_workflow_load_time(self):
        """Small workflow should load in <100ms."""
        data = load_workflow(Path(SMALL_WORKFLOW))

        start = time.perf_counter()
        workflow = load_workflow_from_dict(data)
        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 100, f"Small workflow took {elapsed:.1f}ms"

    def test_medium_workflow_load_time(self):
        """Medium workflow should load in <300ms."""
        data = load_workflow(Path(MEDIUM_WORKFLOW))

        start = time.perf_counter()
        workflow = load_workflow_from_dict(data)
        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 300, f"Medium workflow took {elapsed:.1f}ms"

    def test_large_workflow_load_time(self):
        """Large workflow should load in <500ms."""
        data = load_workflow(Path(LARGE_WORKFLOW))

        start = time.perf_counter()
        workflow = load_workflow_from_dict(data)
        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 500, f"Large workflow took {elapsed:.1f}ms"

    def test_cache_hit_performance(self):
        """Cache hits should be <50ms."""
        data = load_workflow(Path(MEDIUM_WORKFLOW))

        # First load (cache miss)
        load_workflow_from_dict(data)

        # Second load (cache hit)
        start = time.perf_counter()
        workflow = load_workflow_from_dict(data)
        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 50, f"Cache hit took {elapsed:.1f}ms"
```

### Regression Tests

```python
# tests/workflow/test_loader_regression.py

def test_migrated_nodes_preserve_config():
    """Ensure node type migration preserves config."""
    workflow_data = {
        "nodes": {
            "n1": {
                "node_type": "ReadFileNode",  # Legacy
                "config": {"path": "/test/file.txt"}
            }
        }
    }

    workflow = load_workflow_from_dict(workflow_data)
    node = workflow.nodes["n1"]

    assert node.node_type == "FileSystemSuperNode"
    assert node.config["action"] == "Read File"
    assert node.config["path"] == "/test/file.txt"

def test_validation_only_runs_once():
    """Ensure validation doesn't run multiple times."""
    # This would require instrumentation/mocking
    pass
```

---

## Risks and Mitigation

### R1: Cache Invalidation Issues
**Risk**: Stale workflow loaded from cache.
**Mitigation**: Content-based fingerprinting ensures any change invalidates cache.

### R2: Memory Pressure from Caching
**Risk**: Large workflows consume significant memory in cache.
**Mitigation**: LRU eviction with configurable max size (default: 20 workflows).

### R3: Thread Safety in Parallel Loading
**Risk**: Race conditions during parallel node instantiation.
**Mitigation**: Node classes should be stateless until execute(); use locks for shared state.

### R4: Breaking Changes in NODE_TYPE_MAP
**Risk**: External code relies on full NODE_TYPE_MAP behavior.
**Mitigation**: Maintain backward compatibility proxy; only optimize internal paths.

### R5: Preloader Conflicts
**Risk**: Preloader and workflow loader compete for node loading.
**Mitigation**: Use shared `_loaded_classes` cache; preloader populates, loader reads.

---

## Implementation Order

### Week 1: Phase A (Quick Wins)
| Day | Task | Files |
|-----|------|-------|
| 1 | A1: Single-pass validation | workflow_loader.py, workflow_deserializer.py |
| 1 | A2: Batch node type resolution | workflow_loader.py |
| 2 | A3: Lazy NODE_TYPE_MAP proxy | workflow_loader.py |
| 2 | A4: Node type map caching | workflow_deserializer.py |

### Week 2: Phase B (Medium Effort)
| Day | Task | Files |
|-----|------|-------|
| 1-2 | B1: Workflow schema caching | NEW: workflow_cache.py |
| 3 | B2: Batch node preloading | workflow_loader.py, nodes/__init__.py |
| 4 | B3: Streaming decompression | compressed_io.py |

### Week 3: Phase C (Advanced)
| Day | Task | Files |
|-----|------|-------|
| 1-2 | C1: Incremental loading | NEW: incremental_loader.py |
| 3-4 | C2: Node instance pooling | object_pool.py, workflow_loader.py |
| 5 | C3: Parallel instantiation | workflow_loader.py |

---

## Expected Performance Gains Summary

| Phase | Optimization | Best Case | Typical Case |
|-------|--------------|-----------|--------------|
| A1 | Single validation | 100ms | 50ms |
| A2 | Batch resolution | 30ms | 20ms |
| A3 | Lazy proxy | 200ms | 100ms |
| A4 | Map caching | 50ms | 30ms |
| B1 | Workflow cache | 200ms | 150ms (hits) |
| B2 | Batch preload | 50ms | 30ms |
| B3 | Streaming I/O | 50ms | 20ms |
| C1 | Incremental | 200ms+ | Preview only |
| C2 | Node pooling | 50ms | 30ms |
| C3 | Parallel | 100ms | 50ms |
| **Total** | | **1030ms** | **480ms** |

**Realistic Expected Improvement**: 300-500ms for typical medium workflows (50 nodes).

---

## Success Criteria

1. **P95 Load Time**: Medium workflow loads in <300ms
2. **Cache Hit Rate**: >70% cache hits during typical development session
3. **Memory Overhead**: Cache uses <50MB for 20 workflows
4. **No Regressions**: All existing workflow tests pass
5. **Thread Safety**: No race conditions in parallel tests

---

## Related Documentation

- `.brain/systemPatterns.md` - DDD architecture patterns
- `src/casare_rpa/nodes/_index.md` - Node registry documentation
- `.brain/plans/performance-optimization-plan.md` - Overall performance plan
- `src/casare_rpa/utils/performance/object_pool.py` - Existing pooling patterns
- `src/casare_rpa/infrastructure/execution/variable_cache.py` - Cache pattern reference
