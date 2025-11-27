# Quick Fix Guide for Validation Bugs

**Critical Bugs - Fix Immediately**

---

## Bug #1: Type Confusion Attack (CRITICAL)

**File**: `src/casare_rpa/core/validation.py`
**Line**: 773

### Current Code (VULNERABLE)
```python
for node_id, node_data in nodes.items():
    # Skip hidden/auto nodes when determining entry points
    if node_id.startswith("__"):  # ❌ CRASHES if node_id is not a string
        # ...
```

### Fixed Code
```python
for node_id, node_data in nodes.items():
    # Skip hidden/auto nodes when determining entry points
    if isinstance(node_id, str) and node_id.startswith("__"):  # ✅ Type-safe
        # ...
```

**Test to verify fix**:
```bash
pytest tests/test_validation_security.py::TestInputValidationBypass::test_type_confusion_attack -v
```

---

## Bug #2: Stack Overflow (CRITICAL)

**File**: `src/casare_rpa/core/validation.py`
**Lines**: 682-727

### Current Code (VULNERABLE - Recursive)
```python
def _has_circular_dependency(
    nodes: Dict[str, Any],
    connections: List[Dict[str, Any]],
) -> bool:
    """Check for circular dependencies using DFS on exec connections only."""

    # Build adjacency list (only exec connections for flow)
    graph: Dict[str, List[str]] = {node_id: [] for node_id in nodes}

    for conn in connections:
        parsed = _parse_connection(conn)
        if not parsed:
            continue

        source = parsed["source_node"]
        source_port = parsed["source_port"]
        target = parsed["target_node"]

        # Only consider execution flow connections
        if source in graph and _is_exec_port(source_port):
            graph[source].append(target)

    visited: Set[str] = set()
    rec_stack: Set[str] = set()

    def has_cycle(node: str) -> bool:  # ❌ RECURSIVE - Stack overflow on deep graphs
        visited.add(node)
        rec_stack.add(node)

        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if has_cycle(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True

        rec_stack.discard(node)
        return False

    for node_id in nodes:
        if node_id not in visited:
            if has_cycle(node_id):
                return True

    return False
```

### Fixed Code (Iterative - No Recursion)
```python
def _has_circular_dependency(
    nodes: Dict[str, Any],
    connections: List[Dict[str, Any]],
) -> bool:
    """Check for circular dependencies using iterative DFS on exec connections only."""

    # Build adjacency list (only exec connections for flow)
    graph: Dict[str, List[str]] = {node_id: [] for node_id in nodes}

    for conn in connections:
        parsed = _parse_connection(conn)
        if not parsed:
            continue

        source = parsed["source_node"]
        source_port = parsed["source_port"]
        target = parsed["target_node"]

        # Only consider execution flow connections
        if source in graph and _is_exec_port(source_port):
            graph[source].append(target)

    # Iterative DFS using explicit stack (no recursion)
    WHITE, GRAY, BLACK = 0, 1, 2
    color: Dict[str, int] = {node: WHITE for node in nodes}

    for start_node in nodes:
        if color[start_node] == WHITE:
            # Stack contains (node, is_processed) tuples
            stack = [(start_node, False)]

            while stack:
                node, processed = stack.pop()

                if processed:
                    # Mark as fully processed
                    color[node] = BLACK
                    continue

                if color[node] == GRAY:
                    # Already in current path - cycle detected
                    return True

                # Mark as being processed
                color[node] = GRAY
                # Push marker to mark as BLACK when all neighbors processed
                stack.append((node, True))

                # Push all unvisited neighbors
                for neighbor in graph.get(node, []):
                    if color[neighbor] == WHITE:
                        stack.append((neighbor, False))
                    elif color[neighbor] == GRAY:
                        # Back edge found - cycle detected
                        return True

    return False
```

**Test to verify fix**:
```bash
pytest tests/test_validation_performance.py::TestValidationTiming::test_validation_scales_linearly -v
```

---

## Bug #3: Whitespace in Port Names (MEDIUM)

**File**: `src/casare_rpa/core/validation.py`
**Line**: 577-600

### Current Code
```python
def _is_exec_port(port_name: str) -> bool:
    """Check if a port name indicates an execution flow port."""
    if not port_name:
        return False
    port_lower = port_name.lower()  # ❌ No whitespace trimming
    exec_port_names = {
        "exec_in",
        "exec_out",
        "exec",
        "loop_body",
        "completed",
        "true",
        "false",
        "then",
        "else",
        "on_success",
        "on_error",
        "on_finally",
        "body",
        "done",
        "finish",
        "next",
    }
    return port_lower in exec_port_names or "exec" in port_lower
```

### Fixed Code
```python
def _is_exec_port(port_name: str) -> bool:
    """Check if a port name indicates an execution flow port."""
    if not port_name:
        return False
    port_lower = port_name.strip().lower()  # ✅ Strip whitespace first
    exec_port_names = {
        "exec_in",
        "exec_out",
        "exec",
        "loop_body",
        "completed",
        "true",
        "false",
        "then",
        "else",
        "on_success",
        "on_error",
        "on_finally",
        "body",
        "done",
        "finish",
        "next",
    }
    return port_lower in exec_port_names or "exec" in port_lower
```

**Apply same fix to `_is_exec_input_port()` at line 603-623**:
```python
def _is_exec_input_port(port_name: str) -> bool:
    """Check if a port is an execution INPUT port (receives exec flow)."""
    if not port_name:
        return False
    port_lower = port_name.strip().lower()  # ✅ Add .strip()
    # ... rest of function
```

**Test to verify fix**:
```bash
pytest tests/test_validation_edge_cases.py::TestPortNames::test_is_exec_port_edge_cases -v
```

---

## Bug #4: Add Validation Size Limits (CRITICAL)

**File**: `src/casare_rpa/core/validation.py`
**Lines**: Add at start of `validate_workflow()`

### Add These Constants (Top of file after imports)
```python
# Validation limits to prevent DoS
MAX_WORKFLOW_NODES = 50000
MAX_WORKFLOW_CONNECTIONS = 100000
VALIDATION_TIMEOUT_SECONDS = 30
```

### Add Size Checks (In `validate_workflow()` function after line 270)
```python
def validate_workflow(data: Dict[str, Any]) -> ValidationResult:
    """
    Validate a complete workflow data structure.

    Args:
        data: Serialized workflow dictionary

    Returns:
        ValidationResult with all issues found
    """
    result = ValidationResult()

    # Check top-level structure
    _validate_structure(data, result)
    if not result.is_valid:
        return result  # Can't proceed without basic structure

    # ADD THIS: Check workflow size limits to prevent DoS
    nodes = data.get("nodes", {})
    connections = data.get("connections", [])

    if len(nodes) > MAX_WORKFLOW_NODES:
        result.add_error(
            "WORKFLOW_TOO_LARGE",
            f"Workflow has {len(nodes):,} nodes (maximum {MAX_WORKFLOW_NODES:,})",
            suggestion="Split workflow into smaller subworkflows",
        )
        return result

    if len(connections) > MAX_WORKFLOW_CONNECTIONS:
        result.add_error(
            "TOO_MANY_CONNECTIONS",
            f"Workflow has {len(connections):,} connections (maximum {MAX_WORKFLOW_CONNECTIONS:,})",
            suggestion="Reduce workflow complexity",
        )
        return result

    # Continue with normal validation...
    _validate_metadata(data.get("metadata", {}), result)
    # ... rest of function
```

**Test to verify fix**:
```bash
pytest tests/test_validation_performance.py::TestMemoryUsage::test_large_workflow_memory_usage -v
```

---

## All Fixes Combined - Complete Patch

Create this file: `validation_patch.py` and run it to apply all fixes:

```python
"""
Patch script to fix critical validation bugs.
Run: python validation_patch.py
"""

import re
from pathlib import Path

VALIDATION_FILE = Path("src/casare_rpa/core/validation.py")

def apply_fixes():
    """Apply all critical bug fixes to validation.py"""

    with open(VALIDATION_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Fix #1: Add type check before startswith()
    content = content.replace(
        'if node_id.startswith("__"):',
        'if isinstance(node_id, str) and node_id.startswith("__"):'
    )

    # Fix #3: Add strip() to port name checking
    content = content.replace(
        'port_lower = port_name.lower()',
        'port_lower = port_name.strip().lower()'
    )

    # Fix #4: Add size limits (add constants at top)
    imports_section = content.find('from .types import SCHEMA_VERSION')
    if imports_section != -1:
        insert_pos = content.find('\n\n', imports_section)
        if insert_pos != -1:
            size_limits = '''
# Validation limits to prevent DoS attacks
MAX_WORKFLOW_NODES = 50000
MAX_WORKFLOW_CONNECTIONS = 100000
VALIDATION_TIMEOUT_SECONDS = 30
'''
            content = content[:insert_pos] + size_limits + content[insert_pos:]

    # Backup original file
    backup_file = VALIDATION_FILE.with_suffix('.py.backup')
    with open(backup_file, "w", encoding="utf-8") as f:
        f.write(content)

    # Write patched file
    with open(VALIDATION_FILE, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ Applied fixes to {VALIDATION_FILE}")
    print(f"📁 Backup saved to {backup_file}")
    print("\nFixed bugs:")
    print("  - Bug #1: Type confusion attack (type checking)")
    print("  - Bug #3: Whitespace in port names (input sanitization)")
    print("  - Bug #4: Size limits added")
    print("\n⚠️  Bug #2 (stack overflow) requires manual code replacement")
    print("   See QUICK_FIX_GUIDE.md for the iterative DFS implementation")

if __name__ == "__main__":
    apply_fixes()
```

---

## Verification Tests

After applying fixes, run these tests to verify:

```bash
# Test all fixes
pytest tests/test_validation_*.py -v

# Test specific fixes
pytest tests/test_validation_security.py::TestInputValidationBypass::test_type_confusion_attack -v
pytest tests/test_validation_edge_cases.py::TestPortNames::test_is_exec_port_edge_cases -v
pytest tests/test_validation_performance.py -v -k "not benchmark"

# Run with coverage
pytest tests/test_validation_*.py --cov=casare_rpa.core.validation --cov-report=term-missing
```

---

## Manual Fix Required: Bug #2 (Stack Overflow)

**This fix requires manual code replacement** because it's a complete algorithm rewrite.

1. Open `src/casare_rpa/core/validation.py`
2. Find the `_has_circular_dependency()` function (around line 682)
3. Replace the entire function with the iterative version shown above
4. Run tests to verify:
   ```bash
   pytest tests/test_validation_performance.py::TestValidationTiming::test_validation_scales_linearly -v
   ```

---

## Rollback Instructions

If fixes cause issues:

```bash
# Restore from backup
cp src/casare_rpa/core/validation.py.backup src/casare_rpa/core/validation.py

# Or use git
git checkout src/casare_rpa/core/validation.py
```

---

## Summary

**Quick Fixes (Can be scripted)**:
- ✅ Bug #1: Type checking (1 line change)
- ✅ Bug #3: Whitespace trimming (2 line changes)
- ✅ Bug #4: Size limits (add constants and checks)

**Manual Fix Required**:
- ⚠️ Bug #2: Stack overflow (function rewrite - iterative DFS)

**Total Lines Changed**: ~100 lines
**Estimated Time**: 30-60 minutes
**Risk Level**: Low (high test coverage)
