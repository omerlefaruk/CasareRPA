# Concept 3: Variable/Expression Resolution Unification

## Current State Analysis

### Architecture Overview
```
Domain Layer:
├── domain/services/variable_resolver.py    # Core resolution logic
│   ├── resolve_variables()                  # {{var}} pattern replacement
│   ├── resolve_dict_variables()             # Resolve in dicts
│   └── extract_variable_names()             # Find variable references
└── domain/entities/execution_state.py      # ExecutionState.resolve_value()

Infrastructure Layer:
├── infrastructure/execution/variable_cache.py
│   ├── VariableResolutionCache              # LRU cache with version invalidation
│   └── CachedVariableResolver               # Wrapper with caching
└── infrastructure/execution/execution_context.py
    └── ExecutionContext.resolve_value()     # Adds caching layer
```

### Current Node Usage Pattern
```python
# 485+ locations use this pattern:
async def execute(self, context):
    selector = self.get_parameter("selector")
    selector = context.resolve_value(selector)  # Manual resolution
    url = self.get_parameter("url")
    url = context.resolve_value(url)  # Manual resolution
    # ... repeat for every parameter
```

### Issues
1. **Manual calls everywhere**: 485+ `context.resolve_value()` calls
2. **Inconsistent**: Some nodes check `hasattr(context, "resolve_value")`, others don't
3. **Boilerplate**: Same 2-line pattern repeated everywhere
4. **Easy to forget**: New nodes might miss calling resolve_value

---

## Unification Goal

Simplify to automatic resolution through `get_parameter()`:

```python
# After unification:
async def execute(self, context):
    # Auto-resolved! No manual context.resolve_value() needed
    selector = self.get_parameter("selector")
    url = self.get_parameter("url")
```

---

## Implementation Plan

### Phase 1: Enhance get_parameter with Context-Aware Resolution
**Goal**: Make `get_parameter()` automatically resolve `{{variables}}` when context is available

#### Task 1.1: Add resolve flag to get_parameter
Location: `src/casare_rpa/domain/entities/base_node.py`

```python
def get_parameter(
    self,
    name: str,
    default: Any = None,
    context: Any = None,  # NEW: Optional context for resolution
    resolve: bool = True,  # NEW: Auto-resolve by default
) -> Any:
    """
    Get a parameter value from input ports or config.

    Args:
        name: Parameter name
        default: Default value if not found
        context: Optional execution context for variable resolution
        resolve: If True and context provided, auto-resolve {{variables}}
    """
    value = ... # existing logic

    if resolve and context and hasattr(context, 'resolve_value'):
        value = context.resolve_value(value)

    return value
```

#### Task 1.2: Alternative - Context injection pattern
Instead of passing context to every get_parameter call, inject context during execute:

```python
class BaseNode:
    _current_context: Any = None  # Thread-local or instance

    def execute(self, context):
        self._current_context = context
        try:
            return self._execute_impl(context)
        finally:
            self._current_context = None

    def get_parameter(self, name: str, default: Any = None) -> Any:
        value = ... # existing logic
        if self._current_context and hasattr(self._current_context, 'resolve_value'):
            value = self._current_context.resolve_value(value)
        return value
```

### Phase 2: Update BaseNode Implementation
**File**: `src/casare_rpa/domain/entities/base_node.py`

1. Store context reference during execute
2. Update get_parameter to use stored context
3. Add `get_raw_parameter()` for cases where resolution is not wanted

### Phase 3: Gradual Node Migration
**Strategy**: Remove manual `context.resolve_value()` calls from nodes

1. Start with low-risk utility nodes
2. Test thoroughly
3. Roll out to browser, system, and other node categories

### Phase 4: Documentation and Tests
<<<<<<< HEAD
1. Update GEMINI.md with new pattern
=======
1. Update AGENTS.md (and sync CLAUDE.md + GEMINI.md) with new pattern
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
2. Add integration tests for resolution
3. Update existing tests if needed

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Double resolution | Check if value contains `{{` before resolving |
| Breaking changes | Keep `context.resolve_value()` working for backward compat |
| Performance | Caching already in place, minimal impact |
| Type preservation | Already handled in domain resolver |

---

## Implementation Order

1. [x] **Phase 1.2**: Implement context injection in BaseNode ✅
2. [x] **Phase 2**: Update get_parameter with auto-resolution ✅
3. [x] **Phase 3a**: Test with a few nodes (pilot) ✅ - Added 7 unit tests
4. [ ] **Phase 3b**: Mass update remaining nodes (optional - backward compatible)
<<<<<<< HEAD
5. [x] **Phase 4**: Documentation update ✅ - Updated GEMINI.md
=======
5. [x] **Phase 4**: Documentation update ✅ - Updated AGENTS.md/CLAUDE.md/GEMINI.md
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e

---

## Success Criteria

1. ✅ New nodes can use `get_parameter()` without manual resolution
2. ✅ Existing nodes continue to work unchanged
3. ✅ No performance regression
4. ✅ Test suite passes (671 tests)

---

## Completion Summary

### Files Modified

| File | Change |
|------|--------|
| `src/casare_rpa/domain/entities/base_node.py` | Added `_execution_context`, updated `get_parameter()` with auto-resolution, added `get_raw_parameter()` and `set_execution_context()` |
| `src/casare_rpa/application/use_cases/node_executor.py` | Added context injection in `_execute_with_timeout()` and `execute_with_timeout_safe()` |
<<<<<<< HEAD
| `GEMINI.md` | Updated Modern Node Standard to reflect AUTO-RESOLUTION pattern |
=======
| `AGENTS.md` / `CLAUDE.md` / `GEMINI.md` | Updated Modern Node Standard to reflect AUTO-RESOLUTION pattern |
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
| `tests/domain/test_auto_resolution.py` | Added 7 unit tests for auto-resolution |

### Key APIs Added

```python
# NEW: Auto-resolves {{variables}} when context is set
value = self.get_parameter("name")

# NEW: Get raw un-resolved value
raw = self.get_raw_parameter("name")

# NEW: Explicit resolve flag
value = self.get_parameter("name", resolve=False)

# INTERNAL: Context injection (called by NodeExecutor)
node.set_execution_context(context)
```

### Backward Compatibility

- Existing `context.resolve_value()` calls continue to work
- Nodes that don't use auto-resolution are unaffected
- New nodes can use simpler pattern without manual resolution

### Next Steps (Optional)

- **Phase 3b**: Gradually remove 485+ manual `context.resolve_value()` calls from nodes
- This can be done incrementally as nodes are touched for other reasons
