# Workflow Loading Performance Optimization Research

**Research Date**: 2025-12-14
**Applicable To**: CasareRPA workflow loading, serialization, and data persistence

---

## Executive Summary

This research provides concrete recommendations for optimizing workflow/data loading performance in CasareRPA. Key findings:

1. **orjson is already in use** - CasareRPA uses orjson correctly for high-performance scenarios
2. **msgspec offers further gains** - Up to 6-10x faster with schema validation included
3. **Lazy loading patterns exist** - Good foundation in `lazy_imports.py`
4. **Async I/O is implemented** - `async_file_ops.py` provides solid async foundation
5. **Connection pooling is partially implemented** - Needs centralization
6. **Memory-mapped files are not yet used** - Opportunity for very large workflows

---

## 1. JSON/YAML Serialization Optimization

### Current State Analysis

CasareRPA currently uses:
- **Standard `json`** in `workflow_loader.py`, query files, and `async_file_ops.py`
- **`orjson`** in robot agent, checkpoint, CLI, settings, compressed_io, and validators

### Library Comparison Matrix

| Criteria | json (stdlib) | orjson | msgspec | ujson |
|----------|---------------|--------|---------|-------|
| **Speed (decode)** | 1x baseline | 6x faster | 10x faster (with schema) | 3x faster |
| **Speed (encode)** | 1x baseline | 6x faster | 10x faster (with schema) | 3x faster |
| **Memory** | baseline | 6-9x more | lowest | moderate |
| **Validation** | separate pass | separate pass | **included** | separate pass |
| **Type Safety** | none | none | **built-in** | none |
| **Python 3.12+** | Yes | Yes | Yes | Yes |
| **Maintenance** | Python team | Active | Active | Moderate |

### Recommendation: Adopt msgspec for Schema-Defined Types

**Why msgspec over orjson?**
- Zero-cost validation during decode (orjson requires separate validation pass)
- 5-60x faster struct operations vs dataclasses
- Smaller binary footprint
- Decodes + validates faster than orjson decodes alone

**Migration Strategy:**

```python
# BEFORE: Current pattern in workflow_loader.py
import json
from pydantic import BaseModel

class WorkflowSchema(BaseModel):
    metadata: WorkflowMetadata
    nodes: dict[str, NodeData]
    connections: list[ConnectionData]

# Load and validate separately
with open(path) as f:
    data = json.load(f)  # 1st pass: decode
workflow = WorkflowSchema(**data)  # 2nd pass: validate

# AFTER: msgspec pattern (recommended)
import msgspec

class WorkflowSchema(msgspec.Struct):
    metadata: WorkflowMetadata
    nodes: dict[str, NodeData]
    connections: list[ConnectionData]

# Decode and validate in single pass
workflow = msgspec.json.decode(path.read_bytes(), type=WorkflowSchema)
```

**Installation:**
```toml
# pyproject.toml - add to dependencies
"msgspec>=0.20.0",
```

### When to Use Each Library

| Use Case | Recommended Library |
|----------|---------------------|
| Known schema (workflows, configs) | **msgspec** |
| Dynamic/unknown JSON | **orjson** |
| Inter-service binary | **msgspec (MessagePack)** |
| Human debugging | json (with indent) |
| Existing compressed_io.py | Keep orjson (working well) |

---

## 2. Lazy Loading Patterns for Large Data Structures

### Current State

CasareRPA has excellent lazy loading foundation in `src/casare_rpa/utils/lazy_imports.py`:
- Module-level lazy loading with `@lru_cache(maxsize=1)`
- `LazyModule` wrapper for deferred imports
- Pre-configured wrappers for heavy modules (uiautomation, win32gui)

### Recommended Patterns for Workflow Loading

#### Pattern 1: Generator-Based Chunked Loading

For workflows with many nodes, load nodes on-demand:

```python
from typing import Generator, Dict, Any
import msgspec

class LazyWorkflowLoader:
    """Load workflow nodes on-demand to reduce memory pressure."""

    def __init__(self, path: Path):
        self._path = path
        self._raw_data: bytes | None = None
        self._metadata: WorkflowMetadata | None = None
        self._node_offsets: dict[str, tuple[int, int]] | None = None

    def _ensure_loaded(self) -> None:
        """Load raw data and build node offset index."""
        if self._raw_data is None:
            self._raw_data = self._path.read_bytes()
            # Parse only metadata on first load
            # Build index of node positions for lazy access

    @property
    def metadata(self) -> WorkflowMetadata:
        """Lazy metadata access."""
        if self._metadata is None:
            self._ensure_loaded()
            # Extract only metadata section
        return self._metadata

    def get_node(self, node_id: str) -> NodeData:
        """Load single node on-demand."""
        self._ensure_loaded()
        # Use offset index to read only this node

    def iter_nodes(self, chunk_size: int = 50) -> Generator[Dict[str, NodeData], None, None]:
        """Iterate nodes in chunks for memory efficiency."""
        self._ensure_loaded()
        node_ids = list(self._node_offsets.keys())

        for i in range(0, len(node_ids), chunk_size):
            chunk_ids = node_ids[i:i + chunk_size]
            yield {nid: self.get_node(nid) for nid in chunk_ids}
```

#### Pattern 2: Lazy Property Decorator

For class attributes that are expensive to compute:

```python
from typing import TypeVar, Callable, Any
from functools import cached_property

T = TypeVar('T')

class LazyProperty:
    """Descriptor for lazy-loaded properties with optional TTL."""

    def __init__(self, func: Callable[[Any], T], ttl_seconds: float | None = None):
        self.func = func
        self.ttl_seconds = ttl_seconds
        self.attr_name = None

    def __set_name__(self, owner, name):
        self.attr_name = f"_lazy_{name}"
        self.time_attr = f"_lazy_{name}_time"

    def __get__(self, obj, objtype=None) -> T:
        if obj is None:
            return self

        # Check if value exists and not expired
        cached = getattr(obj, self.attr_name, None)
        if cached is not None:
            if self.ttl_seconds is None:
                return cached
            cached_time = getattr(obj, self.time_attr, 0)
            if time.time() - cached_time < self.ttl_seconds:
                return cached

        # Compute and cache
        value = self.func(obj)
        setattr(obj, self.attr_name, value)
        setattr(obj, self.time_attr, time.time())
        return value

# Usage
class WorkflowSchema:
    @LazyProperty
    def connection_graph(self) -> dict[str, list[str]]:
        """Build connection graph only when needed."""
        graph = {}
        for conn in self.connections:
            graph.setdefault(conn.source_node, []).append(conn.target_node)
        return graph
```

#### Pattern 3: Lazy Node Registry Loading

Enhance the existing `_NodeTypeMapProxy` in `workflow_loader.py`:

```python
class LazyNodeRegistry:
    """Load node classes only when first accessed."""

    _instance = None
    _loaded_modules: set[str] = set()
    _node_cache: dict[str, type] = {}

    @classmethod
    def get_node_class(cls, node_type: str) -> type | None:
        # Check cache first
        if node_type in cls._node_cache:
            return cls._node_cache[node_type]

        # Determine module from node type
        module_name = cls._get_module_for_node(node_type)

        # Lazy load module if not yet loaded
        if module_name not in cls._loaded_modules:
            cls._load_module(module_name)
            cls._loaded_modules.add(module_name)

        return cls._node_cache.get(node_type)
```

---

## 3. Caching Strategies

### Current State

CasareRPA uses `@lru_cache` in several places:
- `lazy_imports.py` - module caching (maxsize=1)
- `selector_normalizer.py` - selector caching (maxsize=512)
- `node_registry.py` - node class lookups (maxsize=256)

### Recommended Caching Patterns

#### Pattern 1: TTL Cache for Workflow Metadata

```python
from cachetools import TTLCache, cached
from threading import RLock

# Workflow metadata cache - expires after 5 minutes
_workflow_cache = TTLCache(maxsize=100, ttl=300)
_cache_lock = RLock()

@cached(cache=_workflow_cache, lock=_cache_lock)
def get_workflow_metadata(path: Path) -> WorkflowMetadata:
    """Cache workflow metadata with 5-minute TTL."""
    # Check file modification time for invalidation
    mtime = path.stat().st_mtime
    return _load_metadata_impl(path), mtime
```

#### Pattern 2: File-Based Cache with Modification Tracking

```python
from dataclasses import dataclass
from pathlib import Path
import time

@dataclass
class CacheEntry:
    value: Any
    mtime: float
    accessed: float

class FileCache:
    """Cache that invalidates on file modification."""

    def __init__(self, maxsize: int = 100):
        self._cache: dict[Path, CacheEntry] = {}
        self._maxsize = maxsize

    def get(self, path: Path) -> Any | None:
        entry = self._cache.get(path)
        if entry is None:
            return None

        # Check if file was modified
        try:
            current_mtime = path.stat().st_mtime
            if current_mtime > entry.mtime:
                del self._cache[path]
                return None
        except OSError:
            del self._cache[path]
            return None

        entry.accessed = time.time()
        return entry.value

    def set(self, path: Path, value: Any) -> None:
        # Evict oldest if at capacity
        if len(self._cache) >= self._maxsize:
            oldest = min(self._cache.items(), key=lambda x: x[1].accessed)
            del self._cache[oldest[0]]

        self._cache[path] = CacheEntry(
            value=value,
            mtime=path.stat().st_mtime,
            accessed=time.time()
        )

# Usage
_workflow_cache = FileCache(maxsize=50)

def load_workflow_cached(path: Path) -> WorkflowSchema:
    cached = _workflow_cache.get(path)
    if cached is not None:
        return cached

    workflow = load_workflow_from_file(path)
    _workflow_cache.set(path, workflow)
    return workflow
```

#### Pattern 3: Two-Level Cache (Memory + Disk)

```python
import hashlib
from pathlib import Path
import tempfile

class TwoLevelCache:
    """Memory cache backed by disk for large workflows."""

    def __init__(self, memory_maxsize: int = 20, disk_dir: Path = None):
        self._memory = TTLCache(maxsize=memory_maxsize, ttl=300)
        self._disk_dir = disk_dir or Path(tempfile.gettempdir()) / "casare_cache"
        self._disk_dir.mkdir(exist_ok=True)

    def _disk_path(self, key: str) -> Path:
        hash_key = hashlib.sha256(key.encode()).hexdigest()[:16]
        return self._disk_dir / f"{hash_key}.cache"

    def get(self, key: str) -> Any | None:
        # Level 1: Memory
        if key in self._memory:
            return self._memory[key]

        # Level 2: Disk
        disk_path = self._disk_path(key)
        if disk_path.exists():
            import orjson
            value = orjson.loads(disk_path.read_bytes())
            self._memory[key] = value  # Promote to memory
            return value

        return None

    def set(self, key: str, value: Any) -> None:
        import orjson

        # Memory cache
        self._memory[key] = value

        # Disk cache (async for large values)
        disk_path = self._disk_path(key)
        disk_path.write_bytes(orjson.dumps(value))
```

### Cache Configuration Recommendations

| Cache Type | Use Case | maxsize | TTL |
|------------|----------|---------|-----|
| Node classes | Registry lookups | 256 | None (immutable) |
| Selectors | Selector normalization | 512 | None |
| Workflow metadata | Recent file info | 100 | 300s |
| Full workflows | Frequently accessed | 20 | 600s |
| Connection graphs | Execution planning | 50 | 120s |

---

## 4. Async I/O for File Operations

### Current State

CasareRPA has excellent async file support in `src/casare_rpa/utils/async_file_ops.py`:
- `aiofiles` integration with fallback to `asyncio.to_thread`
- Async JSON read/write with large file detection (100KB threshold)
- Async CSV operations with thread pool for CPU-bound parsing

### Recommended Enhancements

#### Enhancement 1: Async Workflow Loading

```python
# src/casare_rpa/utils/workflow/async_workflow_loader.py

from casare_rpa.utils.async_file_ops import AsyncFileOperations
import msgspec

class AsyncWorkflowLoader:
    """Async workflow loading with validation."""

    @staticmethod
    async def load(path: Path) -> WorkflowSchema:
        """Load and validate workflow asynchronously."""
        # Read file content (non-blocking)
        content = await AsyncFileOperations.read_binary(path)

        # Decode + validate in one pass (CPU-bound, offload to thread)
        return await asyncio.to_thread(
            msgspec.json.decode,
            content,
            type=WorkflowSchema
        )

    @staticmethod
    async def save(workflow: WorkflowSchema, path: Path) -> None:
        """Save workflow asynchronously."""
        # Encode (CPU-bound, offload to thread)
        content = await asyncio.to_thread(
            msgspec.json.encode,
            workflow
        )

        # Write file (non-blocking)
        await AsyncFileOperations.write_binary(path, content)

    @staticmethod
    async def load_multiple(paths: list[Path]) -> list[WorkflowSchema]:
        """Load multiple workflows concurrently."""
        tasks = [AsyncWorkflowLoader.load(p) for p in paths]
        return await asyncio.gather(*tasks, return_exceptions=True)
```

#### Enhancement 2: Streaming Large Workflows

```python
import ijson  # Streaming JSON parser

async def stream_workflow_nodes(path: Path) -> AsyncGenerator[NodeData, None]:
    """Stream workflow nodes without loading entire file."""

    async def _stream():
        async with aiofiles.open(path, 'rb') as f:
            parser = ijson.parse_async(f)
            current_node = {}
            in_node = False
            node_id = None

            async for prefix, event, value in parser:
                if prefix.startswith('nodes.') and event == 'map_key':
                    if in_node and current_node:
                        yield NodeData(**current_node)
                    node_id = prefix.split('.')[1]
                    current_node = {'node_id': node_id}
                    in_node = True
                elif in_node and prefix.startswith(f'nodes.{node_id}'):
                    key = prefix.split('.')[-1]
                    if event in ('string', 'number', 'boolean'):
                        current_node[key] = value

            # Yield last node
            if current_node:
                yield NodeData(**current_node)

    async for node in _stream():
        yield node
```

#### Enhancement 3: Parallel File Discovery

```python
async def discover_workflows(
    directory: Path,
    pattern: str = "*.json"
) -> list[WorkflowMetadata]:
    """Discover workflows in directory with parallel metadata loading."""

    # Find all workflow files
    workflow_files = list(directory.glob(pattern))

    async def load_metadata(path: Path) -> WorkflowMetadata | None:
        try:
            content = await AsyncFileOperations.read_text(path)
            # Parse only metadata section (lightweight)
            data = msgspec.json.decode(content)
            return WorkflowMetadata.from_dict(data.get('metadata', {}))
        except Exception:
            return None

    # Load metadata concurrently (limit concurrency)
    semaphore = asyncio.Semaphore(10)

    async def bounded_load(path: Path):
        async with semaphore:
            return await load_metadata(path)

    results = await asyncio.gather(*[bounded_load(p) for p in workflow_files])
    return [r for r in results if r is not None]
```

---

## 5. Connection Pooling for Database Operations

### Current State

CasareRPA has connection pooling mentions in:
- `application/services/orchestrator_client.py` - aiohttp session pooling
- `infrastructure/auth/robot_api_keys.py` - asyncpg pool usage
- `nodes/database/sql_nodes.py` - connection pool support

### Centralized Connection Pool Manager

```python
# src/casare_rpa/infrastructure/persistence/pool_manager.py

from contextlib import asynccontextmanager
from typing import Optional
import asyncpg
import aiohttp

class ConnectionPoolManager:
    """Centralized connection pool management."""

    _instance: Optional['ConnectionPoolManager'] = None

    def __init__(self):
        self._pg_pools: dict[str, asyncpg.Pool] = {}
        self._http_sessions: dict[str, aiohttp.ClientSession] = {}
        self._initialized = False

    @classmethod
    def get_instance(cls) -> 'ConnectionPoolManager':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def initialize(self, config: dict) -> None:
        """Initialize all connection pools."""
        if self._initialized:
            return

        # PostgreSQL pools
        for name, db_config in config.get('databases', {}).items():
            self._pg_pools[name] = await asyncpg.create_pool(
                dsn=db_config['dsn'],
                min_size=db_config.get('min_size', 5),
                max_size=db_config.get('max_size', 20),
                max_queries=db_config.get('max_queries', 50000),
                max_inactive_connection_lifetime=db_config.get('max_idle', 300),
                command_timeout=db_config.get('timeout', 60),
            )

        # HTTP session pools
        for name, http_config in config.get('http_services', {}).items():
            connector = aiohttp.TCPConnector(
                limit=http_config.get('max_connections', 100),
                limit_per_host=http_config.get('max_per_host', 30),
                keepalive_timeout=http_config.get('keepalive', 30),
            )
            self._http_sessions[name] = aiohttp.ClientSession(
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=http_config.get('timeout', 30))
            )

        self._initialized = True

    @asynccontextmanager
    async def acquire_db(self, name: str = 'default'):
        """Acquire database connection from pool."""
        pool = self._pg_pools.get(name)
        if pool is None:
            raise ValueError(f"Unknown database pool: {name}")

        async with pool.acquire() as conn:
            yield conn

    def get_http_session(self, name: str = 'default') -> aiohttp.ClientSession:
        """Get HTTP session for service."""
        session = self._http_sessions.get(name)
        if session is None:
            raise ValueError(f"Unknown HTTP service: {name}")
        return session

    async def close_all(self) -> None:
        """Close all connection pools."""
        for pool in self._pg_pools.values():
            await pool.close()

        for session in self._http_sessions.values():
            await session.close()

        self._pg_pools.clear()
        self._http_sessions.clear()
        self._initialized = False

# Configuration example
POOL_CONFIG = {
    'databases': {
        'default': {
            'dsn': 'postgresql://user:pass@localhost/casare',
            'min_size': 5,
            'max_size': 20,
            'max_queries': 50000,
            'max_idle': 300,
            'timeout': 60,
        },
        'readonly': {
            'dsn': 'postgresql://user:pass@replica/casare',
            'min_size': 2,
            'max_size': 10,
        }
    },
    'http_services': {
        'orchestrator': {
            'max_connections': 100,
            'max_per_host': 30,
            'keepalive': 30,
            'timeout': 30,
        }
    }
}
```

### Pool Size Guidelines

| Workload Type | min_size | max_size | max_queries | max_idle |
|---------------|----------|----------|-------------|----------|
| Light (UI app) | 2 | 10 | 50000 | 300s |
| Medium (API) | 5 | 20 | 50000 | 300s |
| Heavy (batch) | 10 | 50 | 50000 | 600s |
| Read replica | 2 | 10 | 50000 | 120s |

### Best Practices

1. **Always use async context managers** - Ensures connections return to pool
2. **Set appropriate timeouts** - Prevent connection leaks
3. **Monitor pool metrics** - Track `pool.get_size()`, `pool.get_idle_size()`
4. **Use separate pools for read/write** - Better resource utilization
5. **Parameterize all queries** - Prevent SQL injection

---

## 6. Memory-Mapped Files for Large Workflows

### When to Use mmap

Memory-mapped files are beneficial when:
- Workflows exceed 10MB in size
- Only portions of the workflow are accessed at a time
- Multiple processes need to read the same workflow
- Search/pattern matching across large workflow files

### Implementation Pattern

```python
# src/casare_rpa/utils/workflow/mmap_loader.py

import mmap
from pathlib import Path
from typing import Optional
import re

class MmapWorkflowReader:
    """Memory-mapped workflow reader for large files."""

    def __init__(self, path: Path):
        self._path = path
        self._file = None
        self._mmap: Optional[mmap.mmap] = None
        self._node_index: dict[str, tuple[int, int]] = {}

    def __enter__(self):
        self._file = open(self._path, 'rb')
        self._mmap = mmap.mmap(
            self._file.fileno(),
            0,  # Map entire file
            access=mmap.ACCESS_READ
        )
        self._build_index()
        return self

    def __exit__(self, *args):
        if self._mmap:
            self._mmap.close()
        if self._file:
            self._file.close()

    def _build_index(self) -> None:
        """Build index of node positions for O(1) access."""
        # Use regex to find node boundaries
        pattern = rb'"(\w+)":\s*\{\s*"node_type"'

        for match in re.finditer(pattern, self._mmap):
            node_id = match.group(1).decode('utf-8')
            start = match.start()

            # Find end of this node (matching braces)
            depth = 0
            pos = match.end()
            while pos < len(self._mmap):
                char = self._mmap[pos:pos+1]
                if char == b'{':
                    depth += 1
                elif char == b'}':
                    if depth == 0:
                        end = pos + 1
                        break
                    depth -= 1
                pos += 1

            self._node_index[node_id] = (start, end)

    def get_node_raw(self, node_id: str) -> bytes:
        """Get raw JSON bytes for a specific node."""
        if node_id not in self._node_index:
            raise KeyError(f"Node not found: {node_id}")

        start, end = self._node_index[node_id]
        return self._mmap[start:end]

    def search_in_workflow(self, pattern: str) -> list[tuple[str, int]]:
        """Search for pattern across entire workflow efficiently."""
        results = []
        pattern_bytes = pattern.encode('utf-8')

        pos = 0
        while True:
            pos = self._mmap.find(pattern_bytes, pos)
            if pos == -1:
                break

            # Find which node this belongs to
            for node_id, (start, end) in self._node_index.items():
                if start <= pos < end:
                    results.append((node_id, pos - start))
                    break

            pos += 1

        return results

    @property
    def file_size(self) -> int:
        """Get file size without reading entire file."""
        return len(self._mmap)

    @property
    def node_count(self) -> int:
        """Get node count without parsing."""
        return len(self._node_index)

# Usage
def load_large_workflow_efficiently(path: Path) -> dict:
    """Load large workflow with memory mapping."""
    file_size = path.stat().st_size

    # Use mmap for files > 5MB
    if file_size > 5 * 1024 * 1024:
        with MmapWorkflowReader(path) as reader:
            # Access only needed nodes
            metadata_raw = reader.get_node_raw('metadata')
            # Parse only what we need
            return {
                'file_size': reader.file_size,
                'node_count': reader.node_count,
                'metadata': msgspec.json.decode(metadata_raw)
            }
    else:
        # Standard loading for smaller files
        return msgspec.json.decode(path.read_bytes())
```

### mmap Performance Characteristics

| File Size | mmap Advantage | Notes |
|-----------|----------------|-------|
| < 1MB | None | Standard I/O faster |
| 1-10MB | Marginal | Consider for frequent partial access |
| 10-100MB | Significant | Recommended for partial reads |
| > 100MB | Essential | Avoid loading entire file |

### Limitations

1. **Contiguous address space required** - May fail on 32-bit systems with large files
2. **Not suitable for compressed files** - Must decompress first
3. **Read-only recommended** - Write operations are complex
4. **Platform differences** - Windows vs Unix behavior varies

---

## 7. Implementation Priority

### Phase 1: Quick Wins (1-2 days)

1. **Standardize on orjson** for all JSON operations not using schemas
   - Update `async_file_ops.py` to use orjson
   - Update `workflow_loader.py` JSON parsing

2. **Add workflow metadata cache**
   - Implement `FileCache` for recently opened workflows
   - Cache workflow metadata with mtime invalidation

### Phase 2: Architecture Improvements (1 week)

1. **Introduce msgspec for typed structures**
   - Convert `WorkflowSchema` to `msgspec.Struct`
   - Convert `NodeData`, `ConnectionData`
   - Benchmark against current approach

2. **Centralize connection pooling**
   - Implement `ConnectionPoolManager`
   - Update database nodes to use centralized pools

### Phase 3: Advanced Optimizations (2-3 weeks)

1. **Async workflow loading**
   - Implement `AsyncWorkflowLoader`
   - Add parallel workflow discovery

2. **Memory-mapped large workflow support**
   - Implement `MmapWorkflowReader`
   - Add intelligent switching based on file size

3. **Two-level caching**
   - Implement memory + disk cache
   - Configure appropriate TTLs

---

## 8. Benchmarking Methodology

### Recommended Benchmarks

```python
# tests/benchmarks/test_serialization.py

import pytest
import json
import orjson
import msgspec
from pathlib import Path

@pytest.fixture
def sample_workflow():
    """Generate workflow with 100 nodes."""
    return {
        'metadata': {'name': 'benchmark', 'version': '1.0.0'},
        'nodes': {f'node_{i}': {'node_type': 'ClickNode', 'config': {'selector': f'.btn{i}'}} for i in range(100)},
        'connections': [{'source': f'node_{i}', 'target': f'node_{i+1}'} for i in range(99)]
    }

def test_json_decode(benchmark, sample_workflow):
    data = json.dumps(sample_workflow).encode()
    result = benchmark(json.loads, data)
    assert result['metadata']['name'] == 'benchmark'

def test_orjson_decode(benchmark, sample_workflow):
    data = orjson.dumps(sample_workflow)
    result = benchmark(orjson.loads, data)
    assert result['metadata']['name'] == 'benchmark'

def test_msgspec_decode(benchmark, sample_workflow):
    data = msgspec.json.encode(sample_workflow)
    result = benchmark(msgspec.json.decode, data)
    assert result['metadata']['name'] == 'benchmark'

def test_msgspec_typed_decode(benchmark, sample_workflow):
    """msgspec with schema validation."""
    data = msgspec.json.encode(sample_workflow)

    class WorkflowSchema(msgspec.Struct):
        metadata: dict
        nodes: dict
        connections: list

    result = benchmark(msgspec.json.decode, data, type=WorkflowSchema)
    assert result.metadata['name'] == 'benchmark'
```

### Expected Results

| Library | 100 nodes | 500 nodes | 1000 nodes |
|---------|-----------|-----------|------------|
| json | 1.0x | 1.0x | 1.0x |
| orjson | 4-6x | 5-7x | 6-8x |
| msgspec | 4-6x | 5-7x | 6-8x |
| msgspec (typed) | 8-10x | 9-12x | 10-15x |

---

## Sources

### JSON/Serialization
- [orjson vs json benchmarks 2025](https://morethanmonkeys.medium.com/comparing-json-and-orjson-in-python-which-json-library-should-you-use-in-2025-850cd39ecb7d)
- [orjson GitHub](https://github.com/ijl/orjson)
- [msgspec Benchmarks](https://jcristharif.com/msgspec/benchmarks.html)
- [msgspec GitHub](https://github.com/jcrist/msgspec)
- [Python JSON serialization comparison](https://dev.to/dollardhingra/benchmarking-python-json-serializers-json-vs-ujson-vs-orjson-1o16)

### Lazy Loading
- [Python lazy loading patterns](https://medium.com/@codingmatheus/lazy-loading-in-python-99c44f416aa0)
- [Lazy loading data structures](https://www.pythontutorials.net/blog/how-to-lazy-load-a-data-structure-python/)
- [Pandas chunking for large datasets](https://pandas.pydata.org/docs/user_guide/scale.html)

### Caching
- [cachetools documentation](https://cachetools.readthedocs.io/en/stable/)
- [LRU cache Python guide](https://realpython.com/lru-cache-python/)
- [Time-based LRU cache](https://jamesg.blog/2024/08/18/time-based-lru-cache-python)

### Connection Pooling
- [asyncpg usage guide](https://magicstack.github.io/asyncpg/current/usage.html)
- [SQLAlchemy asyncpg best practices](https://www.codingeasypeasy.com/blog/sqlalchemy-and-asyncpg-connection-pooling-best-practices-for-performance-and-reliability)

### Memory-Mapped Files
- [Python mmap guide](https://realpython.com/python-mmap/)
- [mmap documentation](https://docs.python.org/3/library/mmap.html)
- [Processing large JSON files](https://pythonspeed.com/articles/json-memory-streaming/)
