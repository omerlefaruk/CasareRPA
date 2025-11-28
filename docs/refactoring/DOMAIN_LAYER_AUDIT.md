# Domain Layer Refactoring Analysis

**Date:** 2025-11-28
**Status:** Analysis Complete
**Priority:** HIGH

---

## Executive Summary

Analyzed `src/casare_rpa/domain/` directory:
- **3 HIGH priority** issues (god classes/modules)
- **3 MEDIUM priority** issues (architecture violations)
- **2 deprecated files** ready for deletion
- **Architecture violations** found

---

## HIGH PRIORITY Issues

### 1. God Module - validation.py (856 lines)

**File:** `src/casare_rpa/domain/validation.py`
**Issue:** Mixes validation types, schemas, and functions in a single file
**Impact:** Hard to maintain, test, and extend

**Recommended Solution:**
```
domain/validation/
├── __init__.py
├── types.py          # ValidationResult, ErrorType, etc.
├── schemas.py        # Pydantic schemas
├── validators.py     # Validation functions
└── rules.py          # Validation rules
```

### 2. God File - project.py (819 lines, 10 classes)

**File:** `src/casare_rpa/domain/entities/project.py`
**Issue:** Contains 10 classes in one file
**Classes:** Project, ProjectMetadata, ProjectVariable, VariableScope, ProjectSettings, etc.

**Recommended Solution:**
```
domain/entities/project/
├── __init__.py
├── project.py           # Main Project entity
├── metadata.py          # ProjectMetadata
├── variables.py         # ProjectVariable, VariableScope
├── settings.py          # ProjectSettings
└── dependencies.py      # ProjectDependency
```

### 3. God Class - execution_orchestrator.py (539 lines)

**File:** `src/casare_rpa/domain/services/execution_orchestrator.py`
**Issue:** Too many responsibilities (graph traversal, control flow, state management)

**Recommended Extraction:**
- `GraphTraversalService` - for node ordering and dependency resolution
- `ControlFlowService` - for conditional logic and loops
- `ExecutionStateManager` - for state tracking

---

## MEDIUM PRIORITY Issues

### 4. Architecture Violation - port_type_system.py

**File:** `src/casare_rpa/domain/port_type_system.py:19-25`
**Issue:** Domain layer imports from Application layer
```python
from casare_rpa.application.services.port_type_service import PortTypeService
```

**Impact:** Violates clean architecture (Domain should not depend on Application)
**Fix:** Move `PortTypeService` to infrastructure or remove this file

### 5. Global Singleton - events.py

**File:** `src/casare_rpa/domain/events.py:196-218`
**Issue:** `_global_event_bus` breaks dependency injection
```python
_global_event_bus: Optional[EventBus] = None

def get_global_event_bus() -> EventBus:
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus
```

**Impact:** Testing issues, hidden dependencies
**Fix:** Move EventBus to application layer with proper DI

### 6. Complex Method - workflow.py

**File:** `src/casare_rpa/domain/entities/workflow.py:279-328`
**Issue:** `from_dict()` method is 50 lines with inline repair logic

**Fix:** Extract repair logic to separate method or service

---

## LOW PRIORITY Issues

### 7. Empty Repository Module

**File:** `src/casare_rpa/domain/repositories/__init__.py`
**Issue:** No repository interfaces defined
**Fix:** Add `ProjectRepositoryProtocol`, `WorkflowRepositoryProtocol`, etc.

### 8. Code Duplication

**Files:** `workflow.py` and `project.py`
**Issue:** `VariableDefinition` and `ProjectVariable` are nearly identical
**Question:** Is this distinction intentional?

### 9. Inconsistent Type Hints

**File:** `src/casare_rpa/domain/entities/base_node.py`
**Issue:** Mixes `tuple` vs `Tuple` usage
**Fix:** Standardize to `tuple` (Python 3.9+)

---

## Deprecated Files to Remove

### After Migration

1. **domain/variable_resolver.py**
   - Re-exports from `domain.services.variable_resolver`
   - Update 1 import, then delete

2. **domain/project_schema.py**
   - Re-exports from `domain.entities.project`
   - Update 4 imports, then delete

---

## Import Migration Required

| Current Import | Should Be | Affected Files |
|----------------|-----------|----------------|
| `domain.variable_resolver` | `domain.services.variable_resolver` | 1 |
| `domain.project_schema` | `domain.entities.project` | 4 |
| `domain.port_type_system` | Direct layer-appropriate imports | 5 |

---

## Critical Files Summary

1. **HIGH** - `validation.py` (856 lines) - Split into package
2. **HIGH** - `entities/project.py` (819 lines) - Split into package
3. **HIGH** - `services/execution_orchestrator.py` (539 lines) - Extract services
4. **MEDIUM** - `port_type_system.py` - Fix architecture violation
5. **MEDIUM** - `events.py` - Remove global singleton
6. **LOW** - `variable_resolver.py` - Delete re-export wrapper
7. **LOW** - `project_schema.py` - Delete re-export wrapper

---

## Unresolved Questions

1. Where should `ProjectContext` live? Domain or Infrastructure?
2. Should `EventBus` singleton move to application layer DI?
3. Is `VariableDefinition` vs `ProjectVariable` distinction intentional?

---

## Next Steps

1. Decide on architectural questions above
2. Split validation.py into package structure
3. Split project.py into package structure
4. Fix architecture violation in port_type_system.py
5. Move EventBus to application layer
6. Delete deprecated wrapper files
