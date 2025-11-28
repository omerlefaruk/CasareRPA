# Migration Guide: v2.x to v3.0

This guide covers breaking changes and migration steps for upgrading CasareRPA from v2.x to v3.0.

## v3.0 Migration Status: COMPLETE

**Validation Date**: 2025-11-28

### Final Statistics
- **Compatibility tests**: 17/17 PASSED
- **DeprecationWarnings**: 0 (zero)
- **Smoke test**: PASSED (app starts without errors)
- **core/ directory**: Deleted
- **Files migrated**: ~40 files updated to domain imports

### Success Criteria Checklist
- [x] core/ compatibility layer deleted
- [x] All imports use domain/infrastructure paths
- [x] Zero DeprecationWarning on import
- [x] 17/17 v3.0 compatibility tests pass
- [x] Application starts successfully
- [x] BaseNode moved to domain/entities/
- [x] PortTypeRegistry moved to infrastructure/adapters/
- [x] ExecutionContext alias added to domain/entities/

---

## Breaking Changes

### 1. Removed Compatibility Layers

**`casare_rpa.core/`** - Deleted

The entire `core/` package is removed. All exports now come from `domain/`.

```python
# v2.x (deprecated)
from casare_rpa.core.types import NodeStatus, DataType
from casare_rpa.core.base_node import BaseNode
from casare_rpa.core import Port, ExecutionContext

# v3.0 (required)
from casare_rpa.domain.value_objects.types import NodeStatus, DataType
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects import Port
from casare_rpa.domain.entities import ExecutionContext  # or ExecutionState
```

**`visual_nodes.py` monolith** - Deleted

The 4,285-line monolithic file is removed. Visual nodes are now organized by category.

```python
# v2.x (deprecated)
from casare_rpa.presentation.canvas.visual_nodes.visual_nodes import VisualStartNode

# v3.0 (required)
from casare_rpa.presentation.canvas.visual_nodes import VisualStartNode
# Or specific category:
from casare_rpa.presentation.canvas.visual_nodes.basic import VisualStartNode
```

**Re-export wrappers** - Deleted

Old wrapper modules (`*_nodes.py`) are removed in favor of package imports.

```python
# v2.x (deprecated)
from casare_rpa.nodes.file_nodes import ReadFileNode
from casare_rpa.nodes.http_nodes import HttpGetNode
from casare_rpa.nodes.database_nodes import DatabaseConnectNode

# v3.0 (required)
from casare_rpa.nodes.file import ReadFileNode
from casare_rpa.nodes.http import HttpGetNode
from casare_rpa.nodes.database import DatabaseConnectNode
```

---

## Import Path Changes

### Core Types and Enums

| Component | v2.x Import | v3.0 Import |
|-----------|-------------|-------------|
| NodeStatus | `casare_rpa.core.types.NodeStatus` | `casare_rpa.domain.value_objects.types.NodeStatus` |
| DataType | `casare_rpa.core.types.DataType` | `casare_rpa.domain.value_objects.types.DataType` |
| PortType | `casare_rpa.core.types.PortType` | `casare_rpa.domain.value_objects.types.PortType` |
| ExecutionMode | `casare_rpa.core.types.ExecutionMode` | `casare_rpa.domain.value_objects.types.ExecutionMode` |
| ExecutionResult | `casare_rpa.core.types.ExecutionResult` | `casare_rpa.domain.value_objects.types.ExecutionResult` |

### Base Classes

| Component | v2.x Import | v3.0 Import |
|-----------|-------------|-------------|
| BaseNode | `casare_rpa.core.base_node.BaseNode` | `casare_rpa.domain.entities.base_node.BaseNode` |
| Port | `casare_rpa.core.base_node.Port` | `casare_rpa.domain.value_objects.port.Port` |

### Workflow Entities

| Component | v2.x Import | v3.0 Import |
|-----------|-------------|-------------|
| WorkflowSchema | `casare_rpa.core.workflow_schema.WorkflowSchema` | `casare_rpa.domain.entities.workflow.WorkflowSchema` |
| WorkflowMetadata | `casare_rpa.core.workflow_schema.WorkflowMetadata` | `casare_rpa.domain.entities.workflow_metadata.WorkflowMetadata` |
| NodeConnection | `casare_rpa.core.workflow_schema.NodeConnection` | `casare_rpa.domain.entities.node_connection.NodeConnection` |
| VariableDefinition | `casare_rpa.core.workflow_schema.VariableDefinition` | `casare_rpa.domain.entities.workflow.VariableDefinition` |

### Node Packages

| Category | v2.x Import | v3.0 Import |
|----------|-------------|-------------|
| File nodes | `casare_rpa.nodes.file_nodes.*` | `casare_rpa.nodes.file.*` |
| HTTP nodes | `casare_rpa.nodes.http_nodes.*` | `casare_rpa.nodes.http.*` |
| Database nodes | `casare_rpa.nodes.database_nodes.*` | `casare_rpa.nodes.database.*` |

### Infrastructure

| Component | v2.x Import | v3.0 Import |
|-----------|-------------|-------------|
| ExecutionContext | `casare_rpa.core.execution_context.ExecutionContext` | `casare_rpa.domain.entities.ExecutionContext` (alias for ExecutionState) |
| ExecutionState | N/A (new) | `casare_rpa.domain.entities.ExecutionState` |
| PortTypeRegistry | `casare_rpa.core.port_type_system.PortTypeRegistry` | `casare_rpa.infrastructure.adapters.PortTypeRegistry` |
| BrowserResourceManager | N/A (new) | `casare_rpa.infrastructure.resources.BrowserResourceManager` |

---

## Automated Migration

### Step 1: Backup

```powershell
git commit -am "Pre-v3.0 migration backup"
```

### Step 2: Run Migration Tool (Dry Run)

```powershell
python scripts/migrate_imports_v3.py --dry-run
```

Review output for changes that will be made.

### Step 3: Run Migration

```powershell
python scripts/migrate_imports_v3.py --backup
```

The `--backup` flag creates `.bak` files before modification.

### Step 4: Verify

```powershell
pytest tests/ -v
```

### Step 5: Commit

```powershell
git commit -am "Migrate to v3.0 imports"
```

---

## Manual Migration Steps

If automated migration misses anything:

### 1. Find Remaining Deprecated Imports

```powershell
python scripts/scan_deprecations.py
```

Or manually search:

```powershell
# PowerShell
Select-String -Path "src/**/*.py" -Pattern "from casare_rpa\.core" -Recurse
Select-String -Path "src/**/*.py" -Pattern "from casare_rpa\.nodes\.\w+_nodes" -Recurse
```

### 2. Update Imports Manually

**Pattern: core.types**
```python
# Find:
from casare_rpa.core.types import NodeStatus, DataType

# Replace:
from casare_rpa.domain.value_objects.types import NodeStatus, DataType
```

**Pattern: core.base_node**
```python
# Find:
from casare_rpa.core.base_node import BaseNode
from casare_rpa.core import Port

# Replace:
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects import Port
```

**Pattern: *_nodes wrappers**
```python
# Find:
from casare_rpa.nodes.file_nodes import ReadFileNode

# Replace:
from casare_rpa.nodes.file import ReadFileNode
```

### 3. Verify Compatibility

```powershell
pytest tests/test_v3_compatibility.py -v
```

---

## Common Migration Issues

### Issue: ImportError for core module

**Error:**
```
ModuleNotFoundError: No module named 'casare_rpa.core'
```

**Fix:** Update imports to use `domain/` path.

### Issue: Missing Port class

**Error:**
```
ImportError: cannot import name 'Port' from 'casare_rpa.core.base_node'
```

**Fix:**
```python
from casare_rpa.domain.value_objects import Port
```

### Issue: Workflow schema not found

**Error:**
```
ImportError: cannot import name 'WorkflowSchema' from 'casare_rpa.core.workflow_schema'
```

**Fix:**
```python
from casare_rpa.domain.entities.workflow import WorkflowSchema
```

---

## Timeline

| Version | Status | Compatibility Layer |
|---------|--------|---------------------|
| v2.0 | Released | Active (no warnings) |
| v2.1 | Previous | Active + DeprecationWarning |
| v3.0 | **Current** | **Removed** - old imports fail |

### Known Issues (v3.0)

1. **Legacy node module paths in node_registry.py**: Warning messages about missing `database_nodes`, `file_nodes`, `http_nodes` modules. These are cosmetic - nodes are correctly loaded from package paths (`nodes/file/`, `nodes/http/`, `nodes/database/`).

2. **None**: All v3.0 migration objectives have been completed.

---

## Checklist

- [x] Backup codebase (git commit)
- [x] Run migration tool (`--dry-run` first)
- [x] Update remaining imports manually
- [x] Run full test suite
- [x] Verify no deprecation warnings
- [x] Commit migrated code

---

## Support

- **Documentation**: See [REFACTORING_ROADMAP.md](../REFACTORING_ROADMAP.md)
- **Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md)
- **Issues**: Open a GitHub issue with `v3-migration` label
