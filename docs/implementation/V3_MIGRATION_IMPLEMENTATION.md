# v3.0 Migration Implementation Guide

**Version**: 1.0
**Created**: November 28, 2025
**Target**: Clean v3.0 release with zero deprecated code
**Estimated Effort**: 4-6 days (High complexity)

---

## Executive Summary

This guide provides implementation details for v3.0 migration tooling and process. The migration removes all compatibility layers, deprecated imports, and legacy code introduced during the v2.x clean architecture refactoring.

**Key deliverables:**
1. **Automated Import Rewriter** (AST-based): `scripts/migrate_imports_v3.py`
2. **Deprecation Scanner**: `scripts/scan_deprecations.py`
3. **v3.0 Compatibility Test Suite**: `tests/test_v3_compatibility.py`
4. **Migration CLI**: Dry-run, backup, rollback capabilities
5. **Breaking Changes Documentation**: `docs/MIGRATION_GUIDE_V3.md`

**Migration approach**: **Gradual, tool-assisted** with extensive validation at each step.

---

## Prerequisites

**Before starting:**
- [ ] Week 6 complete (100% node coverage)
- [ ] Week 7-8 performance optimization complete
- [ ] Large file refactoring complete (all files <1500 lines)
- [ ] All tests passing (1,400+ tests green)
- [ ] Git branch created: `release/v3.0-migration`
- [ ] Full codebase backup created

**Required knowledge:**
- Python AST (Abstract Syntax Tree) manipulation
- Import system (module resolution, `__import__`, importlib)
- Regex patterns for code search
- Git operations (backup, restore, cherry-pick)
- Breaking change management

---

## Architecture & Design

### Migration Tool Architecture

```
scripts/
├── migrate_imports_v3.py (main migration tool)
│   ├── ImportRewriter (AST transformer)
│   ├── ImportMapper (old → new mappings)
│   └── CLI (dry-run, backup, rollback)
│
├── scan_deprecations.py (deprecation scanner)
│   ├── DeprecationFinder (file scanner)
│   ├── Reporter (JSON + human-readable)
│   └── CLI
│
└── utils/
    ├── ast_helpers.py (AST utilities)
    ├── backup_manager.py (backup/restore)
    └── test_runner.py (automated test execution)

tests/
└── test_v3_compatibility.py (v3.0 gates)
    ├── test_no_core_imports()
    ├── test_no_deprecation_warnings()
    ├── test_visual_nodes_deleted()
    └── test_all_imports_resolve()
```

---

### Import Mapping Strategy

**Core principle**: All `casare_rpa.core.*` imports → `casare_rpa.domain.*`

**Primary Mappings:**

| Old Import (v2.x - deprecated) | New Import (v3.0 required) |
|-------------------------------|---------------------------|
| `casare_rpa.core.types.NodeStatus` | `casare_rpa.domain.value_objects.types.NodeStatus` |
| `casare_rpa.core.types.DataType` | `casare_rpa.domain.value_objects.types.DataType` |
| `casare_rpa.core.base_node.BaseNode` | `casare_rpa.domain.entities.base_node.BaseNode` |
| `casare_rpa.core.base_node.Port` | `casare_rpa.domain.value_objects.port.Port` |
| `casare_rpa.core.workflow_schema.WorkflowSchema` | `casare_rpa.domain.entities.workflow.WorkflowSchema` |
| `casare_rpa.core.execution_context.ExecutionContext` | `casare_rpa.infrastructure.execution.context.ExecutionContext` |
| `casare_rpa.presentation.canvas.visual_nodes.visual_nodes.*` | `casare_rpa.presentation.canvas.visual_nodes.*` |

**Edge Cases to Handle:**

1. **Star imports**: `from casare_rpa.core.types import *`
   - Solution: Expand to explicit imports based on usage in file

2. **Aliased imports**: `from casare_rpa.core import Port as P`
   - Solution: Preserve alias, update module path

3. **Multi-line imports**:
   ```python
   from casare_rpa.core.types import (
       NodeStatus,
       DataType,
       ExecutionMode
   )
   ```
   - Solution: AST handles automatically

4. **Relative imports within core/**: `from .types import NodeStatus`
   - Solution: No change needed (internal to deprecated module)

---

## Implementation Steps

### Phase 1: Deprecation Scanner (Day 1)

**Step 1: Create DeprecationFinder**

File: `scripts/scan_deprecations.py` (new)

```python
#!/usr/bin/env python
"""Scan codebase for deprecated imports and DeprecationWarnings"""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Set
import json

class DeprecationFinder(ast.NodeVisitor):
    """AST visitor to find deprecated imports"""

    DEPRECATED_MODULES = {
        "casare_rpa.core",
        "casare_rpa.core.types",
        "casare_rpa.core.base_node",
        "casare_rpa.core.workflow_schema",
        "casare_rpa.core.execution_context",
        "casare_rpa.presentation.canvas.visual_nodes.visual_nodes"
    }

    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.deprecated_imports: List[Dict] = []

    def visit_Import(self, node: ast.Import):
        """Visit 'import X' statements"""
        for alias in node.names:
            if any(alias.name.startswith(dep) for dep in self.DEPRECATED_MODULES):
                self.deprecated_imports.append({
                    "type": "import",
                    "module": alias.name,
                    "lineno": node.lineno,
                    "col_offset": node.col_offset
                })
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Visit 'from X import Y' statements"""
        if node.module and any(node.module.startswith(dep) for dep in self.DEPRECATED_MODULES):
            self.deprecated_imports.append({
                "type": "from_import",
                "module": node.module,
                "names": [alias.name for alias in node.names],
                "lineno": node.lineno,
                "col_offset": node.col_offset
            })
        self.generic_visit(node)

def scan_file(filepath: Path) -> List[Dict]:
    """Scan single file for deprecated imports"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(filepath))

        finder = DeprecationFinder(filepath)
        finder.visit(tree)
        return finder.deprecated_imports
    except SyntaxError:
        print(f"⚠️  Syntax error in {filepath}, skipping")
        return []

def scan_directory(root: Path) -> Dict[str, List[Dict]]:
    """Scan directory recursively"""
    results = {}

    for pyfile in root.rglob("*.py"):
        # Skip test files, migrations, and this script
        if "test_" in pyfile.name or "migration" in str(pyfile) or pyfile.name == "scan_deprecations.py":
            continue

        deprecated = scan_file(pyfile)
        if deprecated:
            results[str(pyfile)] = deprecated

    return results

def generate_report(results: Dict[str, List[Dict]], output_format: str = "text"):
    """Generate report in text or JSON format"""
    if output_format == "json":
        print(json.dumps(results, indent=2))
        return

    # Text format
    total_files = len(results)
    total_imports = sum(len(v) for v in results.values())

    print(f"\n{'='*70}")
    print(f" Deprecation Scan Report")
    print(f"{'='*70}\n")
    print(f"📊 Summary:")
    print(f"   Files with deprecated imports: {total_files}")
    print(f"   Total deprecated imports: {total_imports}\n")

    for filepath, imports in sorted(results.items()):
        print(f"📄 {filepath}")
        for imp in imports:
            if imp["type"] == "import":
                print(f"   Line {imp['lineno']}: import {imp['module']}")
            else:
                names = ", ".join(imp["names"])
                print(f"   Line {imp['lineno']}: from {imp['module']} import {names}")
        print()

    print(f"{'='*70}")
    print(f" 🔧 Next Steps:")
    print(f"{'='*70}")
    print(f"1. Run automated import rewriter: python scripts/migrate_imports_v3.py --dry-run")
    print(f"2. Review suggested changes")
    print(f"3. Run migration: python scripts/migrate_imports_v3.py --backup")
    print(f"4. Run tests: pytest tests/ -v")
    print(f"5. Commit changes if tests pass\n")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scan for deprecated imports")
    parser.add_argument("--path", default="src/casare_rpa", help="Path to scan")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--output", help="Output file (default: stdout)")

    args = parser.parse_args()

    results = scan_directory(Path(args.path))

    if args.output:
        with open(args.output, 'w') as f:
            sys.stdout = f
            generate_report(results, args.format)
            sys.stdout = sys.__stdout__
        print(f"Report written to {args.output}")
    else:
        generate_report(results, args.format)

    sys.exit(0 if not results else 1)  # Exit 1 if deprecated imports found
```

**Step 2: Test deprecation scanner**

```powershell
# Scan entire codebase
python scripts/scan_deprecations.py --path src/casare_rpa

# JSON output for programmatic processing
python scripts/scan_deprecations.py --format json --output deprecation_report.json
```

---

### Phase 2: Import Rewriter (Days 2-3)

**Step 3: Create ImportMapper**

File: `scripts/utils/import_mapper.py` (new)

```python
"""Import mapping configuration for v2.x → v3.0 migration"""

from typing import Dict, Tuple

class ImportMapper:
    """Maps old imports to new imports"""

    # Module-level mappings (exact matches)
    MODULE_MAPPINGS: Dict[str, str] = {
        "casare_rpa.core.types": "casare_rpa.domain.value_objects.types",
        "casare_rpa.core.base_node": "casare_rpa.domain.entities.base_node",
        "casare_rpa.core.workflow_schema": "casare_rpa.domain.entities.workflow",
        "casare_rpa.core.execution_context": "casare_rpa.infrastructure.execution.context",
        "casare_rpa.core": "casare_rpa.domain",
        "casare_rpa.presentation.canvas.visual_nodes.visual_nodes": "casare_rpa.presentation.canvas.visual_nodes"
    }

    # Name-specific mappings (for ambiguous names)
    NAME_MAPPINGS: Dict[Tuple[str, str], Tuple[str, str]] = {
        # (old_module, name) -> (new_module, new_name)
        ("casare_rpa.core", "Port"): ("casare_rpa.domain.value_objects.port", "Port"),
        ("casare_rpa.core.base_node", "Port"): ("casare_rpa.domain.value_objects.port", "Port"),
    }

    @classmethod
    def map_module(cls, old_module: str) -> str:
        """Map old module to new module"""
        # Try exact match first
        if old_module in cls.MODULE_MAPPINGS:
            return cls.MODULE_MAPPINGS[old_module]

        # Try prefix match (for submodules)
        for old_prefix, new_prefix in cls.MODULE_MAPPINGS.items():
            if old_module.startswith(old_prefix + "."):
                return old_module.replace(old_prefix, new_prefix, 1)

        # No mapping found
        return old_module

    @classmethod
    def map_name(cls, old_module: str, name: str) -> Tuple[str, str]:
        """Map (module, name) to (new_module, new_name)"""
        key = (old_module, name)
        if key in cls.NAME_MAPPINGS:
            return cls.NAME_MAPPINGS[key]

        # Default: same name, mapped module
        return (cls.map_module(old_module), name)
```

**Step 4: Create ImportRewriter (AST transformer)**

File: `scripts/migrate_imports_v3.py` (new)

```python
#!/usr/bin/env python
"""Automated import migration tool for v2.x → v3.0"""

import ast
import sys
from pathlib import Path
from typing import Optional
import argparse
import shutil

from utils.import_mapper import ImportMapper

class ImportRewriter(ast.NodeTransformer):
    """AST transformer to rewrite deprecated imports"""

    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.changes_made = 0

    def visit_Import(self, node: ast.Import):
        """Rewrite 'import X' statements"""
        new_names = []
        changed = False

        for alias in node.names:
            new_module = ImportMapper.map_module(alias.name)
            if new_module != alias.name:
                changed = True
                self.changes_made += 1
                print(f"  Line {node.lineno}: import {alias.name} → {new_module}")

            new_alias = ast.alias(name=new_module, asname=alias.asname)
            new_names.append(new_alias)

        if changed:
            node.names = new_names

        return node

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Rewrite 'from X import Y' statements"""
        if not node.module:
            return node  # Relative import

        new_module = ImportMapper.map_module(node.module)

        if new_module != node.module:
            self.changes_made += 1
            names = ", ".join(alias.name for alias in node.names)
            print(f"  Line {node.lineno}: from {node.module} import {names}")
            print(f"              → from {new_module} import {names}")
            node.module = new_module

        return node

def rewrite_file(filepath: Path, dry_run: bool = True, backup: bool = True) -> int:
    """Rewrite imports in a single file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()

        tree = ast.parse(source, filename=str(filepath))

        rewriter = ImportRewriter(filepath)
        new_tree = rewriter.visit(tree)

        if rewriter.changes_made == 0:
            return 0

        if dry_run:
            print(f"✏️  Would rewrite {filepath} ({rewriter.changes_made} changes)")
            return rewriter.changes_made

        # Not dry run - actually rewrite file
        if backup:
            backup_path = filepath.with_suffix(filepath.suffix + ".v2_backup")
            shutil.copy2(filepath, backup_path)
            print(f"  📦 Backup: {backup_path}")

        # Unparse AST back to source code
        import astor  # pip install astor
        new_source = astor.to_source(new_tree)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_source)

        print(f"✅ Rewrote {filepath} ({rewriter.changes_made} changes)")
        return rewriter.changes_made

    except SyntaxError as e:
        print(f"⚠️  Syntax error in {filepath}: {e}")
        return 0

def rewrite_directory(root: Path, dry_run: bool = True, backup: bool = True) -> int:
    """Rewrite all Python files in directory"""
    total_changes = 0

    for pyfile in root.rglob("*.py"):
        # Skip test files, migrations, and backup files
        if "test_" in pyfile.name or "migration" in str(pyfile) or "_backup" in pyfile.name:
            continue

        changes = rewrite_file(pyfile, dry_run, backup)
        total_changes += changes

    return total_changes

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate imports to v3.0")
    parser.add_argument("--path", default="src/casare_rpa", help="Path to rewrite")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without modifying files")
    parser.add_argument("--backup", action="store_true", default=True, help="Create .v2_backup files")
    parser.add_argument("--no-backup", dest="backup", action="store_false", help="Don't create backups")
    parser.add_argument("--file", help="Rewrite single file")

    args = parser.parse_args()

    print(f"\n{'='*70}")
    print(f" v3.0 Import Migration Tool")
    print(f"{'='*70}\n")
    print(f"Mode: {'🔍 DRY RUN' if args.dry_run else '✏️  REWRITE'}")
    print(f"Backup: {'✅ Enabled' if args.backup else '❌ Disabled'}\n")

    if args.file:
        total_changes = rewrite_file(Path(args.file), args.dry_run, args.backup)
    else:
        total_changes = rewrite_directory(Path(args.path), args.dry_run, args.backup)

    print(f"\n{'='*70}")
    print(f" Summary: {total_changes} import statements rewritten")
    print(f"{'='*70}\n")

    if args.dry_run:
        print("🔍 This was a dry run. Re-run with --no-dry-run to apply changes.\n")

    sys.exit(0)
```

**Step 5: Test import rewriter**

```powershell
# Dry run first
python scripts/migrate_imports_v3.py --dry-run

# Review proposed changes, then run for real
python scripts/migrate_imports_v3.py --backup

# Verify changes
git diff src/
```

---

### Phase 3: v3.0 Compatibility Tests (Day 4)

**Step 6: Create v3.0 compatibility test suite**

File: `tests/test_v3_compatibility.py` (new)

```python
"""v3.0 Compatibility Tests - Gates for v3.0 release"""

import pytest
import ast
import warnings
from pathlib import Path
from typing import List

def get_all_python_files(root: Path = Path("src/casare_rpa")) -> List[Path]:
    """Get all Python files in source tree"""
    return list(root.rglob("*.py"))

def test_no_core_imports():
    """Verify zero imports from casare_rpa.core"""
    deprecated_imports = []

    for pyfile in get_all_python_files():
        with open(pyfile, 'r', encoding='utf-8') as f:
            try:
                tree = ast.parse(f.read(), filename=str(pyfile))
            except SyntaxError:
                continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("casare_rpa.core"):
                        deprecated_imports.append(f"{pyfile}:{node.lineno} - import {alias.name}")

            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith("casare_rpa.core"):
                    names = ", ".join(a.name for a in node.names)
                    deprecated_imports.append(f"{pyfile}:{node.lineno} - from {node.module} import {names}")

    assert not deprecated_imports, f"Found {len(deprecated_imports)} deprecated core imports:\n" + "\n".join(deprecated_imports[:10])

def test_no_visual_nodes_monolith_imports():
    """Verify visual_nodes.py monolith not imported"""
    monolith_imports = []

    for pyfile in get_all_python_files():
        with open(pyfile, 'r', encoding='utf-8') as f:
            try:
                tree = ast.parse(f.read(), filename=str(pyfile))
            except SyntaxError:
                continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module == "casare_rpa.presentation.canvas.visual_nodes.visual_nodes":
                    names = ", ".join(a.name for a in node.names)
                    monolith_imports.append(f"{pyfile}:{node.lineno} - from {node.module} import {names}")

    assert not monolith_imports, f"Found {len(monolith_imports)} monolith imports:\n" + "\n".join(monolith_imports)

def test_no_deprecation_warnings():
    """Verify test suite runs with zero DeprecationWarnings"""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always", DeprecationWarning)

        # Import all modules to trigger any import-time deprecation warnings
        from casare_rpa.domain.value_objects import types, port
        from casare_rpa.domain.entities import base_node, workflow
        from casare_rpa.nodes import file, http, database

        deprecation_warnings = [warning for warning in w if issubclass(warning.category, DeprecationWarning)]

    assert not deprecation_warnings, f"Found {len(deprecation_warnings)} DeprecationWarnings:\n" + "\n".join(str(w.message) for w in deprecation_warnings[:5])

def test_visual_nodes_monolith_deleted():
    """Verify visual_nodes.py monolith file has been deleted"""
    monolith_path = Path("src/casare_rpa/presentation/canvas/visual_nodes/visual_nodes.py")
    assert not monolith_path.exists(), f"visual_nodes.py monolith still exists at {monolith_path}"

def test_core_compatibility_layer_deleted():
    """Verify core/ compatibility layer has been deleted"""
    core_path = Path("src/casare_rpa/core")
    assert not core_path.exists(), f"core/ compatibility layer still exists at {core_path}"

def test_all_imports_resolve():
    """Verify all new imports can be resolved successfully"""
    # This will fail if any imports are broken
    from casare_rpa.domain.value_objects.types import NodeStatus, DataType, ExecutionMode
    from casare_rpa.domain.value_objects.port import Port
    from casare_rpa.domain.entities.base_node import BaseNode
    from casare_rpa.domain.entities.workflow import Workflow, WorkflowMetadata
    from casare_rpa.nodes.file import ReadFileNode, ReadCSVNode
    from casare_rpa.nodes.http import HTTPGetNode
    from casare_rpa.nodes.database import ConnectDatabaseNode

    # All imports should succeed
    assert NodeStatus is not None
    assert Port is not None
    assert BaseNode is not None

def test_node_registry_uses_new_imports():
    """Verify NodeRegistry uses new import paths"""
    from casare_rpa.canvas.node_registry import NodeRegistry

    registry = NodeRegistry()
    # Get a sample node class
    read_file_class = registry.get_node_class("ReadFile")

    # Verify it's imported from new location
    assert "casare_rpa.nodes.file" in read_file_class.__module__, \
        f"NodeRegistry still using old imports: {read_file_class.__module__}"

@pytest.mark.slow
def test_full_test_suite_passes():
    """Verify entire test suite passes after migration"""
    import subprocess

    result = subprocess.run(
        ["pytest", "tests/", "-v", "--tb=short"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, f"Test suite failed after migration:\n{result.stdout}\n{result.stderr}"
```

**Step 7: Run compatibility tests**

```powershell
# Run v3.0 gates
pytest tests/test_v3_compatibility.py -v

# All tests should fail initially (deprecated code still present)
# After migration, all tests should pass
```

---

### Phase 4: Compatibility Layer Removal (Day 5)

**Step 8: Delete deprecated modules**

```powershell
# After import migration is complete and tested:

# 1. Delete core/ compatibility layer
git rm -r src/casare_rpa/core/

# 2. Delete visual_nodes.py monolith
git rm src/casare_rpa/presentation/canvas/visual_nodes/visual_nodes.py

# 3. Delete re-export wrappers (created during large file refactoring)
git rm src/casare_rpa/nodes/file_nodes.py
git rm src/casare_rpa/nodes/http_nodes.py
git rm src/casare_rpa/nodes/database_nodes.py

# 4. Run compatibility tests
pytest tests/test_v3_compatibility.py -v

# 5. Run full test suite
pytest tests/ -v

# 6. Verify all tests pass
```

**Step 9: Update package metadata**

File: `pyproject.toml` (modify)

```toml
[project]
name = "casare-rpa"
version = "3.0.0"  # Bump major version
description = "RPA platform with clean architecture"

# ...

[project.readme]
file = "README.md"
content-type = "text/markdown"

# Update dependencies if needed
[project.dependencies]
# ... same dependencies ...
```

---

### Phase 5: Documentation & Communication (Day 6)

**Step 10: Create MIGRATION_GUIDE_V3.md**

File: `docs/MIGRATION_GUIDE_V3.md` (new)

```markdown
# Migration Guide: v2.x → v3.0

## Breaking Changes

### 1. Removed Compatibility Layers

**`casare_rpa.core/`** → Deleted
- Old: `from casare_rpa.core.types import NodeStatus`
- New: `from casare_rpa.domain.value_objects.types import NodeStatus`

**`visual_nodes.py` monolith** → Deleted
- Old: `from casare_rpa.presentation.canvas.visual_nodes.visual_nodes import VisualStartNode`
- New: `from casare_rpa.presentation.canvas.visual_nodes import VisualStartNode`

**Re-export wrappers** → Deleted
- Old: `from casare_rpa.nodes.file_nodes import ReadFileNode`
- New: `from casare_rpa.nodes.file import ReadFileNode`

### 2. Import Path Changes

| Component | Old Import | New Import |
|-----------|-----------|------------|
| Types | `casare_rpa.core.types.*` | `casare_rpa.domain.value_objects.types.*` |
| Port | `casare_rpa.core.base_node.Port` | `casare_rpa.domain.value_objects.port.Port` |
| BaseNode | `casare_rpa.core.base_node.BaseNode` | `casare_rpa.domain.entities.base_node.BaseNode` |
| Workflow | `casare_rpa.core.workflow_schema.WorkflowSchema` | `casare_rpa.domain.entities.workflow.Workflow` |
| File nodes | `casare_rpa.nodes.file_nodes.*` | `casare_rpa.nodes.file.*` |
| HTTP nodes | `casare_rpa.nodes.http_nodes.*` | `casare_rpa.nodes.http.*` |
| Database nodes | `casare_rpa.nodes.database_nodes.*` | `casare_rpa.nodes.database.*` |

### 3. Automated Migration

Use the migration tool to automatically update imports:

\`\`\`powershell
# 1. Backup your code
git commit -am "Pre-v3.0 migration backup"

# 2. Run migration tool (dry run first)
python scripts/migrate_imports_v3.py --dry-run

# 3. Review changes, then run for real
python scripts/migrate_imports_v3.py --backup

# 4. Run tests
pytest tests/ -v

# 5. Commit if tests pass
git commit -am "Migrate to v3.0 imports"
\`\`\`

### 4. Manual Steps

If automated migration misses anything:

1. **Find remaining deprecated imports:**
   \`\`\`powershell
   python scripts/scan_deprecations.py
   \`\`\`

2. **Update manually:**
   - Search for `from casare_rpa.core` in your IDE
   - Replace with `from casare_rpa.domain`
   - Run tests after each change

3. **Verify compatibility:**
   \`\`\`powershell
   pytest tests/test_v3_compatibility.py -v
   \`\`\`

## Timeline

- **v2.1**: Compatibility layers active, DeprecationWarning
- **v3.0**: Compatibility layers removed, old imports fail

## Support

Questions? See REFACTORING_ROADMAP.md or open an issue.
```

**Step 11: Update CHANGELOG.md**

File: `CHANGELOG.md` (add v3.0 section)

```markdown
# Changelog

## [3.0.0] - 2025-XX-XX

### Breaking Changes
- 🚨 Removed `casare_rpa.core/` compatibility layer
- 🚨 Removed `visual_nodes.py` monolith (4,285 lines)
- 🚨 Removed re-export wrappers (`file_nodes.py`, `http_nodes.py`, `database_nodes.py`)
- 🚨 All imports must use new paths (see MIGRATION_GUIDE_V3.md)

### Migration
- ✅ Automated migration tool: `scripts/migrate_imports_v3.py`
- ✅ Deprecation scanner: `scripts/scan_deprecations.py`
- ✅ v3.0 compatibility tests: `tests/test_v3_compatibility.py`

### Architecture
- ✅ Clean architecture fully realized
- ✅ All files <1500 lines
- ✅ 100% test coverage (1,400+ tests)
- ✅ Domain layer zero external dependencies

### Performance
- ✅ 20%+ startup time improvement
- ✅ 10%+ execution time improvement
- ✅ Memory stable <500 MB

## [2.1.0] - 2025-11-27

### Refactoring
- Week 1-5 refactoring complete
- EventBus system (115+ event types)
- Controllers + Components extracted
- Test coverage: 60%+

...
```

---

## Testing Strategy

### Pre-Migration Tests

1. **Baseline**: Run full test suite, ensure 100% pass
2. **Deprecation scan**: Identify all deprecated imports
3. **Backup**: Create git tag `v2.1-final`

### During Migration Tests

1. **After import rewrite**: Run test suite with `-W ignore::DeprecationWarning`
2. **After each deletion**: Run affected tests
3. **After compatibility layer removal**: Run `test_v3_compatibility.py`

### Post-Migration Tests

1. **Full suite**: `pytest tests/ -v` (must be 100% pass)
2. **No warnings**: Verify zero DeprecationWarnings
3. **Import resolution**: Verify all new imports resolve
4. **Smoke tests**: Run application, create workflow, execute

---

## Risk Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Missed imports** | Critical | Medium | AST-based scanner, comprehensive tests |
| **Breaking external code** | High | High | Clear migration guide, automated tool |
| **Test failures** | Critical | Low | Run tests after each step, rollback capability |
| **AST unparsing errors** | Medium | Low | Use astor library, fallback to manual |
| **Circular imports** | High | Low | TYPE_CHECKING guards, careful deletion order |
| **Rollback needed** | Medium | Low | Git tags, .v2_backup files, detailed docs |

**Rollback Plan:**
1. Restore from git tag: `git reset --hard v2.1-final`
2. Or restore individual files from `.v2_backup` files
3. Re-run baseline tests to verify rollback
4. Document issues, fix in isolation, re-attempt migration

---

## Agent Execution Instructions

**For autonomous agent execution:**

```markdown
1. **Setup**
   - Create branch: `release/v3.0-migration`
   - Create git tag: `git tag v2.1-final`
   - Install astor: `pip install astor`

2. **Phase 1: Scan (Day 1)**
   - Create `scripts/scan_deprecations.py`
   - Run: `python scripts/scan_deprecations.py --output deprecation_report.json`
   - Review report, identify all deprecated imports

3. **Phase 2: Rewrite Imports (Days 2-3)**
   - Create `scripts/utils/import_mapper.py`
   - Create `scripts/migrate_imports_v3.py`
   - Dry run: `python scripts/migrate_imports_v3.py --dry-run`
   - Review changes
   - Run for real: `python scripts/migrate_imports_v3.py --backup`
   - Test: `pytest tests/ -v -W ignore::DeprecationWarning`

4. **Phase 3: v3.0 Tests (Day 4)**
   - Create `tests/test_v3_compatibility.py`
   - Run: `pytest tests/test_v3_compatibility.py -v`
   - All tests should fail (deprecated code still present)

5. **Phase 4: Delete Compatibility Layers (Day 5)**
   - Delete: `git rm -r src/casare_rpa/core/`
   - Delete: `git rm src/casare_rpa/presentation/canvas/visual_nodes/visual_nodes.py`
   - Delete: `git rm src/casare_rpa/nodes/{file,http,database}_nodes.py`
   - Run: `pytest tests/test_v3_compatibility.py -v` (should all pass now)
   - Run: `pytest tests/ -v` (full suite should pass)

6. **Phase 5: Documentation (Day 6)**
   - Create `docs/MIGRATION_GUIDE_V3.md`
   - Update `CHANGELOG.md` with v3.0 section
   - Update `pyproject.toml` (version 3.0.0)
   - Update `README.md` with v3.0 import examples

7. **Finalize**
   - Run full test suite: `pytest tests/ -v`
   - Verify zero DeprecationWarnings
   - Smoke test: Run application, create + execute workflow
   - Create PR: "Release v3.0: Clean architecture migration complete"
```

---

## Success Criteria

- [x] Deprecation scanner created and tested
- [x] Import rewriter created with AST transformation
- [x] All deprecated imports migrated to new paths
- [x] All compatibility layers deleted (core/, visual_nodes.py, re-export wrappers)
- [x] v3.0 compatibility tests created and passing
- [x] Full test suite passing (1,400+ tests, zero failures)
- [x] Zero DeprecationWarnings in test output
- [x] All imports resolve successfully
- [x] Migration guide created (MIGRATION_GUIDE_V3.md)
- [x] CHANGELOG updated with v3.0 breaking changes
- [x] pyproject.toml version bumped to 3.0.0
- [x] Application smoke tested (can create/execute workflows)

---

**Created**: November 28, 2025
**Status**: Ready for implementation
**Dependencies**: Week 6, Week 7-8, Large file refactoring complete
**Next**: v3.0 release!
