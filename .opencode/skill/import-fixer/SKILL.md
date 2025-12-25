---
name: import-fixer
description: Fix import statements across the codebase to use correct module paths, resolve circular dependencies, and align with clean architecture layer boundaries.
license: MIT
compatibility: opencode
metadata:
  audience: developers
  workflow: imports
---

When fixing imports, follow these systematic steps:

## Import Analysis Process

### 1. Identify Import Issues

```bash
# Find all import statements
grep -r "^from " src/ --include="*.py"
grep -r "^import " src/ --include="*.py"

# Find deprecated imports
grep -r "from casare_rpa.core" src/ --include="*.py"
grep -r "from casare_rpa.runner" src/ --include="*.py"

# Find circular dependency candidates
# Look for imports between modules at same level
grep -r "from casare_rpa.presentation" src/casare_rpa/presentation --include="*.py"
```

### 2. Common Import Issues

**Issue 1: Deprecated Imports (Core Layer)**
```python
# DEPRECATED (v3.0 removal):
from casare_rpa.core.types import DataType, NodeId
from casare_rpa.core.base_node import Port
from casare_rpa.core import Port

# CORRECT:
from casare_rpa.domain.value_objects.types import DataType, NodeId
from casare_rpa.domain.value_objects.port import Port
from casare_rpa.domain.value_objects import Port
```

**Issue 2: Layer Violations**
```python
# WRONG: Presentation importing from Infrastructure
from casare_rpa.infrastructure.resources import BrowserResourceManager

# CORRECT: Presentation imports from Application
from casare_rpa.application.use_cases import ExecuteWorkflowUseCase

# WRONG: Domain importing from Infrastructure
from casare_rpa.infrastructure.persistence import FileStorage

# CORRECT: Domain defines interface, Application coordinates
from casare_rpa.domain.repositories import WorkflowRepository
# (Infrastructure implements WorkflowRepository)
```

**Issue 3: Circular Dependencies**
```python
# Before: Circular dependency
# module_a.py
from module_b import ClassB  # Imports B

class ClassA:
    def use_b(self):
        return ClassB()

# module_b.py
from module_a import ClassA  # Imports A - CIRCULAR!

class ClassB:
    def use_a(self):
        return ClassA()

# FIX: Use TYPE_CHECKING for type hints only
# module_a.py
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from module_b import ClassB

class ClassA:
    def use_b(self) -> 'ClassB':  # Forward reference
        from module_b import ClassB  # Import at runtime
        return ClassB()

# module_b.py
from module_a import ClassA  # No circular dependency

class ClassB:
    def use_a(self) -> ClassA:
        return ClassA()
```

**Issue 4: Relative vs Absolute Imports**
```python
# WRONG: Relative imports in src/
from ..domain.entities import Workflow
from .base_node import BaseNode

# CORRECT: Always use absolute imports
from casare_rpa.domain.entities import Workflow
from casare_rpa.nodes.base_node import BaseNode
```

**Issue 5: Import Order**
```python
# WRONG: Unorganized imports
from casare_rpa.nodes.base_node import BaseNode
import sys
from typing import Any
import os
from PySide6.QtWidgets import QWidget

# CORRECT: Follow PEP 8 import order
# 1. Standard library
import os
import sys
from typing import Any

# 2. Third-party
from PySide6.QtWidgets import QWidget

# 3. Local application
from casare_rpa.domain.value_objects import ExecutionResult
from casare_rpa.nodes.base_node import BaseNode
```

## Import Fix Templates

### Fix 1: Update Deprecated Core Imports

```python
# Before:
from casare_rpa.core.types import DataType, NodeId, PortId, ExecutionStatus
from casare_rpa.core.base_node import Port, BaseNode
from casare_rpa.core import Port

# After:
from casare_rpa.domain.value_objects.types import (
    DataType,
    NodeId,
    PortId,
    ExecutionStatus,
)
from casare_rpa.domain.value_objects.port import Port
from casare_rpa.nodes.base_node import BaseNode
```

### Fix 2: Resolve Layer Violations

**Domain Layer** (zero external dependencies):
```python
# domain/entities/workflow.py - CORRECT
from dataclasses import dataclass
from typing import List
from casare_rpa.domain.value_objects import ExecutionResult

# NO imports from infrastructure or presentation!
```

**Application Layer** (coordinates domain + infrastructure):
```python
# application/use_cases/execute_workflow.py - CORRECT
from casare_rpa.domain.entities import Workflow
from casare_rpa.domain.repositories import WorkflowRepository  # Interface
from casare_rpa.domain.services import ExecutionOrchestrator

class ExecuteWorkflowUseCase:
    def __init__(self, repository: WorkflowRepository):  # Dependency injection
        self.repository = repository
```

**Infrastructure Layer** (implements domain interfaces):
```python
# infrastructure/persistence/file_workflow_repository.py - CORRECT
from casare_rpa.domain.entities import Workflow
from casare_rpa.domain.repositories import WorkflowRepository  # Interface

class FileWorkflowRepository(WorkflowRepository):
    async def save(self, workflow: Workflow) -> None:
        # Implementation
        pass
```

**Presentation Layer** (uses application layer):
```python
# presentation/canvas/main_window.py - CORRECT
from PySide6.QtWidgets import QMainWindow
from casare_rpa.application.use_cases import ExecuteWorkflowUseCase
from casare_rpa.presentation.canvas.controllers import NodeController

# NO direct imports from infrastructure!
```

### Fix 3: Break Circular Dependencies

```python
# Before: Circular dependency
# event_bus.py
from casare_rpa.presentation.canvas.controllers import NodeController

class EventBus:
    def emit(self, event):
        NodeController.handle_event(event)  # Direct dependency

# node_controller.py
from casare_rpa.presentation.canvas.event_bus import EventBus

class NodeController:
    def __init__(self):
        self.event_bus = EventBus()  # Circular!

# After: Use dependency injection
# event_bus.py
class EventBus:
    def __init__(self):
        self.subscribers = {}

    def subscribe(self, event_type, handler):
        self.subscribers.setdefault(event_type, []).append(handler)

    def emit(self, event):
        for handler in self.subscribers.get(event.type, []):
            handler(event)

# node_controller.py
from casare_rpa.presentation.canvas.event_bus import EventBus

class NodeController:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.event_bus.subscribe('node_created', self.handle_node_created)

    def handle_node_created(self, event):
        # Handle event
        pass
```

### Fix 4: Organize Import Order

```python
# Before: Unorganized
from casare_rpa.nodes.base_node import BaseNode
from typing import Any
import asyncio
from PySide6.QtCore import Qt
from loguru import logger
from casare_rpa.domain.value_objects import ExecutionResult

# After: PEP 8 organized
# Standard library
import asyncio
from typing import Any

# Third-party
from loguru import logger
from PySide6.QtCore import Qt

# Local application
from casare_rpa.domain.value_objects import ExecutionResult
from casare_rpa.nodes.base_node import BaseNode
```

## Bulk Import Fix Script

```python
#!/usr/bin/env python3
"""
Script to fix imports across the codebase.
Usage: python scripts/fix_imports.py
"""

import re
from pathlib import Path
from typing import List, Tuple

# Mapping of deprecated imports to new imports
IMPORT_MIGRATIONS = {
    # Core types to domain
    r'from casare_rpa\.core\.types import (.+)':
        r'from casare_rpa.domain.value_objects.types import \1',

    # Core Port to domain
    r'from casare_rpa\.core\.base_node import Port':
        r'from casare_rpa.domain.value_objects.port import Port',

    r'from casare_rpa\.core import Port':
        r'from casare_rpa.domain.value_objects import Port',

    # Runner to application
    r'from casare_rpa\.runner import WorkflowRunner':
        r'from casare_rpa.application.use_cases import ExecuteWorkflowUseCase',
}


def fix_imports_in_file(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Fix imports in a single file.

    Returns:
        (modified, changes) - Whether file was modified and list of changes made
    """
    content = file_path.read_text(encoding='utf-8')
    original_content = content
    changes = []

    for old_pattern, new_replacement in IMPORT_MIGRATIONS.items():
        matches = re.findall(old_pattern, content)
        if matches:
            content = re.sub(old_pattern, new_replacement, content)
            changes.append(f"{old_pattern} → {new_replacement}")

    if content != original_content:
        file_path.write_text(content, encoding='utf-8')
        return (True, changes)

    return (False, [])


def fix_imports_in_directory(directory: Path) -> None:
    """Fix imports in all Python files in directory."""
    python_files = directory.rglob('*.py')

    total_files = 0
    modified_files = 0

    for file_path in python_files:
        total_files += 1
        modified, changes = fix_imports_in_file(file_path)

        if modified:
            modified_files += 1
            print(f"✓ {file_path}")
            for change in changes:
                print(f"  - {change}")

    print(f"\nFixed {modified_files}/{total_files} files")


if __name__ == '__main__':
    src_dir = Path('src/casare_rpa')
    tests_dir = Path('tests')

    print("Fixing imports in src/...")
    fix_imports_in_directory(src_dir)

    print("\nFixing imports in tests/...")
    fix_imports_in_directory(tests_dir)
```

## Verification

After fixing imports:

```bash
# 1. Check for syntax errors
python -m py_compile src/casare_rpa/**/*.py

# 2. Run tests to ensure no breaking changes
pytest tests/ -v

# 3. Check for type errors (if using mypy)
mypy src/casare_rpa

# 4. Search for remaining deprecated imports
grep -r "from casare_rpa.core" src/ tests/
grep -r "from casare_rpa.runner" src/ tests/

# 5. Verify no circular dependencies
# (Use tools like pydeps or import-linter)
pip install pydeps
pydeps src/casare_rpa --show-cycles
```

## Layer Dependency Rules

**Allowed Dependencies**:
```
Presentation → Application → Domain ← Infrastructure
                        ↑
                        └─ Application
```

**Forbidden Dependencies**:
- ❌ Domain → Infrastructure
- ❌ Domain → Application
- ❌ Domain → Presentation
- ❌ Infrastructure → Presentation
- ❌ Application → Presentation

**Check Layer Violations**:
```bash
# Domain should not import from other layers
grep -r "from casare_rpa.infrastructure" src/casare_rpa/domain/
grep -r "from casare_rpa.application" src/casare_rpa/domain/
grep -r "from casare_rpa.presentation" src/casare_rpa/domain/

# Should return no results
```

## Usage

When user requests import fixes:

1. Analyze current import patterns with grep
2. Identify deprecated imports, layer violations, circular dependencies
3. Create a fix plan with before/after examples
4. Apply fixes using search/replace or bulk script
5. Verify with syntax check and test suite
6. Commit with message:
   ```bash
   refactor: fix imports to align with clean architecture

   - Update deprecated core imports to domain layer
   - Resolve circular dependencies in presentation layer
   - Fix layer violations (presentation → infrastructure)
   - Organize imports following PEP 8

   Verified: All tests pass, no syntax errors
   ```
