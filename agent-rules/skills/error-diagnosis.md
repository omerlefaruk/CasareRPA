# Error Diagnosis Skill

Systematic approach to diagnosing and fixing errors.

## Error Categories

| Category | Examples |
|:---|:---|
| Import | `ModuleNotFoundError`, `ImportError` |
| Type | `TypeError`, `AttributeError` |
| Runtime | `RuntimeError`, `ValueError` |
| Async | `asyncio` errors, `RuntimeWarning` |
| Network | `ConnectionError`, `TimeoutError` |
| Workflow | `CIRCULAR_DEPENDENCY`, JSON errors |

## Diagnosis Workflow

1. **Read** - Full error message + traceback
2. **Locate** - Find the exact file:line
3. **Context** - View surrounding code
4. **Search** - Use `search_codebase` or `grep_search`
5. **Fix** - Apply targeted fix
6. **Verify** - Run tests

## Common CasareRPA Issues

### 1. Silent Visual Node Failure
**Symptom:** New node doesn't appear in Canvas/Tab menu.
**Cause:** Import error in the visual node file (suppressed by lazy loader).
**Fix:**
- Manually try importing the node in a python shell: `from casare_rpa.presentation.canvas.visual_nodes.category.node import VisualMyNode`
- Check imports for non-existent widgets (e.g., `NodeTextWidget`).

### 2. Invalid JSON in Workflow
**Symptom:** `unexpected control character in string` error on load.
**Cause:** Unescaped newlines in JSON strings (common in `script` properties).
**Fix:** Use `\n` for newlines within JSON string values.

### 3. Circular Dependency
**Symptom:** `CIRCULAR_DEPENDENCY` validation error.
**Cause:** Workflow graph has a cycle (e.g., `IfNode` looping back).
**Fix:** Use `WhileLoop` or `ForLoop` nodes. These handle loops internally without creating static graph cycles.

### 4. Event Instantiation Error
**Symptom:** `unexpected keyword argument` when publishing event.
**Cause:** Passing raw objects (e.g., `page=page`) to a Domain Event dataclass.
**Fix:** Pass only serializable fields defined in the event class (e.g., `url=page.url`).

## Quick Fixes

### Import Errors
```bash
# Check if module exists
python -c "import module_name"

# Verify package installed
pip show package_name
```

### Type Errors
- Check function signatures
- Verify return types
- Use `isinstance()` guards

### Async Errors
- Ensure `await` on async calls
- Use `asyncio.run()` at top level
- Check for blocking code in async functions

## Debugging Commands

```bash
# Run with verbose output
python -m pytest tests/ -v --tb=long

# Type check
mypy src/casare_rpa --show-error-codes

# Lint for issues
ruff check src/
```

## Best Practices

1. Never guess - always trace the error
2. Fix root cause, not symptoms
3. Add tests to prevent regression
4. Document non-obvious fixes
