# Research: JSON Serialization Performance

**Date**: 2025-12-05
**Status**: COMPLETE
**Focus**: Optimize workflow serialization in CasareRPA

---

## Executive Summary

CasareRPA already uses **orjson** in critical paths. The codebase has mixed usage:
- **orjson**: workflow serialization, settings, executor, checkpoint
- **json**: XML nodes, variable parsing, tunnel communication, TUF updater

Recommendation: **Standardize on orjson** for all JSON operations except where stdlib json is required (e.g., canonical JSON for signatures).

---

## Library Comparison Matrix

| Criteria | json (stdlib) | ujson | orjson | msgspec |
|----------|---------------|-------|--------|---------|
| **Speed (serialize)** | 1x (baseline) | 2-4x | 5-10x | 10-15x |
| **Speed (deserialize)** | 1x (baseline) | 2-3x | 4-8x | 8-12x |
| **Memory usage** | High | Medium | Low | Lowest |
| **Output type** | str | str | bytes | bytes |
| **Dataclass support** | Manual | Manual | Native (40-50x faster) | Native |
| **Datetime support** | Manual | Manual | Native (RFC 3339) | Native |
| **NumPy support** | No | No | Native (OPT_SERIALIZE_NUMPY) | Native |
| **Pydantic support** | Manual | Manual | Native | Native |
| **Custom encoder** | default= | default= | default= | Limited |
| **Schema validation** | No | No | No | Yes (built-in) |
| **Dependencies** | None | C compiler | Rust (prebuilt wheels) | C (prebuilt wheels) |

### Benchmark Data (typical values)

**Serialize 1KB dict:**
- json: ~50us
- ujson: ~15us
- orjson: ~5us
- msgspec: ~3us

**Serialize 1MB nested dict:**
- json: ~80ms
- ujson: ~25ms
- orjson: ~8ms
- msgspec: ~5ms

**Deserialize 1KB JSON:**
- json: ~30us
- ujson: ~12us
- orjson: ~8us
- msgspec: ~4us

---

## CasareRPA Current Usage Analysis

### Files Using orjson (GOOD)
```
src/casare_rpa/domain/workflow/versioning.py          # Hash computation
src/casare_rpa/domain/entities/execution_state.py     # Runtime vars
src/casare_rpa/utils/settings_manager.py              # Settings I/O
src/casare_rpa/infrastructure/execution/dbos_executor.py  # Checkpoints
src/casare_rpa/infrastructure/persistence/file_system_project_repository.py
src/casare_rpa/application/orchestrator/use_cases/submit_job.py
src/casare_rpa/application/orchestrator/use_cases/execute_local.py
src/casare_rpa/robot/cli.py                           # Status files
src/casare_rpa/robot/agent.py                         # Capabilities
src/casare_rpa/robot/audit.py                         # Audit logs
src/casare_rpa/presentation/canvas/serialization/workflow_deserializer.py
```

### Files Still Using stdlib json (MIGRATE)
```
src/casare_rpa/nodes/variable_nodes.py:135-155        # Variable parsing
src/casare_rpa/nodes/utility_nodes.py:123-656         # HTTP nodes
src/casare_rpa/nodes/xml_nodes.py:634-711             # XML conversion
src/casare_rpa/triggers/manager.py:299                # Webhook payload
src/casare_rpa/infrastructure/tunnel/agent_tunnel.py:312-342
src/casare_rpa/infrastructure/logging/log_streaming_service.py:355
src/casare_rpa/presentation/setup/config_manager.py:214-247
src/casare_rpa/config/file_loader.py:338
```

### Files Requiring stdlib json (KEEP)
```
src/casare_rpa/infrastructure/updater/tuf_updater.py  # Canonical JSON for signatures
src/casare_rpa/application/use_cases/validate_workflow.py  # Hash with sort_keys
```

---

## Streaming/Large File Patterns

### When to Use Streaming

Use streaming JSON parsing when:
1. Workflow files > 10MB
2. Processing large result sets
3. Memory-constrained environments

### ijson (Recommended for streaming)

```python
import ijson

# Stream large workflow file
with open("large_workflow.json", "rb") as f:
    for node in ijson.items(f, "nodes.item"):
        process_node(node)
```

### JsonSlicer (Faster alternative)

```python
from jsonslicer import JsonSlicer

# 35x faster than ijson
with open("large.json", "rb") as f:
    for node in JsonSlicer(f, ("nodes", None)):
        process_node(node)
```

### Recommendation for CasareRPA

Current workflow files are typically <1MB. Streaming not needed now.
Monitor for large workflows (100+ nodes) and add streaming if needed.

---

## Binary Format Alternatives

| Format | Speed | Size | Cross-lang | Python Types | Use Case |
|--------|-------|------|------------|--------------|----------|
| **JSON** | Baseline | Large | Yes | Limited | Interchange |
| **MessagePack** | 2-3x | ~60% | Yes | Good | API comms |
| **Protobuf** | 3-5x | ~40% | Yes | Requires schema | Strict APIs |
| **Pickle** | 3-4x | Variable | Python only | All | Internal cache |

### Recommendation

Keep JSON for workflows (human-readable, editable).
Consider MessagePack for:
- Robot-Orchestrator communication
- Checkpoint serialization (internal only)
- Large result sets

---

## orjson Options Reference

```python
import orjson

# Serialize with options
data = orjson.dumps(
    workflow_dict,
    option=(
        orjson.OPT_INDENT_2 |           # Pretty print
        orjson.OPT_SORT_KEYS |          # Deterministic output
        orjson.OPT_SERIALIZE_NUMPY |    # NumPy support
        orjson.OPT_OMIT_MICROSECONDS    # Cleaner timestamps
    )
)

# Deserialize (no options)
parsed = orjson.loads(json_bytes)
```

### Key Options

| Option | Purpose | Performance Impact |
|--------|---------|-------------------|
| `OPT_INDENT_2` | Pretty print | ~10% slower |
| `OPT_SORT_KEYS` | Deterministic | ~15% slower |
| `OPT_SERIALIZE_NUMPY` | NumPy arrays | Fast |
| `OPT_NAIVE_UTC` | Treat naive datetime as UTC | None |
| `OPT_PASSTHROUGH_DATACLASS` | Custom dataclass serialization | Much slower |
| `OPT_NON_STR_KEYS` | Allow int/UUID keys | Slight overhead |

---

## Migration Guide: json to orjson

### Key Differences

1. **Output type**: `orjson.dumps()` returns `bytes`, not `str`
2. **No ensure_ascii**: Always UTF-8
3. **No indent parameter**: Use `OPT_INDENT_2` (only 2-space indent supported)
4. **No sort_keys parameter**: Use `OPT_SORT_KEYS`
5. **No default factory**: Use `default=` function

### Migration Pattern

**Before (stdlib json):**
```python
import json

# Serialize
json_str = json.dumps(data, indent=2, sort_keys=True, default=str)

# Deserialize
parsed = json.loads(json_str)

# Write file
with open("file.json", "w") as f:
    json.dump(data, f, indent=2)
```

**After (orjson):**
```python
import orjson

def default_encoder(obj):
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    raise TypeError(f"Cannot serialize {type(obj)}")

# Serialize
json_bytes = orjson.dumps(
    data,
    option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS,
    default=default_encoder
)

# Deserialize
parsed = orjson.loads(json_bytes)  # Accepts bytes or str

# Write file
with open("file.json", "wb") as f:  # Note: binary mode
    f.write(json_bytes)
```

### Files to Migrate (Priority Order)

1. **High-frequency**: `variable_nodes.py`, `utility_nodes.py`
2. **Medium-frequency**: `agent_tunnel.py`, `triggers/manager.py`
3. **Low-frequency**: `config_manager.py`, `file_loader.py`, `xml_nodes.py`

---

## Serialization Caching Patterns

### LRU Cache for Repeated Serialization

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def serialize_schema(schema_tuple):
    """Cache JSON schema serialization."""
    return orjson.dumps(dict(schema_tuple))
```

### Precomputed Serialization

```python
class Node:
    def __init__(self, config):
        self.config = config
        # Pre-serialize immutable parts
        self._serialized_schema = orjson.dumps(self.get_schema())
```

### Incremental Serialization for Large Workflows

```python
def serialize_workflow_incremental(workflow, output_path):
    """Serialize large workflows incrementally."""
    with open(output_path, "wb") as f:
        f.write(b'{"nodes":{')

        for i, (node_id, node) in enumerate(workflow["nodes"].items()):
            if i > 0:
                f.write(b',')
            f.write(orjson.dumps(node_id))
            f.write(b':')
            f.write(orjson.dumps(node))

        f.write(b'},"connections":')
        f.write(orjson.dumps(workflow["connections"]))
        f.write(b'}')
```

---

## msgspec Consideration

### Advantages over orjson

1. **Schema validation during deserialization** (Pydantic replacement)
2. **10-30% faster** in many benchmarks
3. **Lower memory usage**
4. **Struct types** for typed deserialization

### Example

```python
import msgspec

class NodeConfig(msgspec.Struct):
    node_id: str
    node_type: str
    position: list[float]
    config: dict

# Decode with validation
decoder = msgspec.json.Decoder(NodeConfig)
node = decoder.decode(json_bytes)
```

### Recommendation

**Not recommended for CasareRPA now.** Reasons:
1. orjson already provides excellent performance
2. CasareRPA uses Pydantic for validation (different pattern)
3. Migration effort not justified for marginal gains

Consider msgspec if:
- Building new high-throughput service
- Need combined serialization + validation
- Processing 10k+ workflows/second

---

## Recommendations for CasareRPA

### Immediate Actions

1. **Migrate remaining stdlib json to orjson** (8 files)
   - Low effort, immediate performance gain
   - Exception: Keep stdlib for TUF canonical JSON

2. **Add orjson utility module**:
   ```python
   # src/casare_rpa/utils/json_utils.py
   import orjson

   def dumps(obj, pretty=False, sort_keys=False):
       opts = 0
       if pretty:
           opts |= orjson.OPT_INDENT_2
       if sort_keys:
           opts |= orjson.OPT_SORT_KEYS
       return orjson.dumps(obj, option=opts)

   def loads(data):
       return orjson.loads(data)
   ```

3. **Use binary mode for file I/O** with orjson

### Future Considerations

1. **Streaming**: Add ijson/jsonslicer if workflows exceed 10MB
2. **Binary format**: Consider msgpack for robot-orchestrator comms
3. **msgspec**: Evaluate when building new high-throughput services

---

## Performance Benchmarks to Run

```python
# tests/benchmarks/test_json_performance.py
import pytest
import orjson
import json

@pytest.fixture
def workflow_data():
    # Load a typical workflow
    return {...}

def test_orjson_serialize(benchmark, workflow_data):
    result = benchmark(orjson.dumps, workflow_data)
    assert result

def test_json_serialize(benchmark, workflow_data):
    result = benchmark(json.dumps, workflow_data)
    assert result

def test_orjson_deserialize(benchmark):
    data = orjson.dumps(workflow_data)
    result = benchmark(orjson.loads, data)
    assert result
```

---

## Sources

- [orjson GitHub](https://github.com/ijl/orjson) - Fast, correct Python JSON library
- [ijson PyPI](https://pypi.org/project/ijson/) - Iterative JSON parser
- [Processing large JSON files](https://pythonspeed.com/articles/json-memory-streaming/)
- [json-stream PyPI](https://pypi.org/project/json-stream/)
- [JsonSlicer PyPI](https://pypi.org/project/jsonslicer/)
