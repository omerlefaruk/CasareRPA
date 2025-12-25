# Coding Standards

**Part of:** `.brain/projectRules.md` | **See also:** `architecture.md`, `testing.md`

## General Principles

- **BE EXTREMELY CONCISE**: Sacrifice grammar. No flowery prose.
- **NO TIME ESTIMATES**: Never provide effort/complexity ratings.
- **AUTO-IMPORTS**: Add missing imports without asking.
- **TERSE OUTPUT**: Skip preamble ("Here is the code"), just show the block.
- **READABLE CODE**: Comments only for "why", never "what" (code is self-documenting).

## Naming Conventions

| Category | Style | Example |
|----------|-------|---------|
| Classes | PascalCase | `ExecutionOrchestrator`, `ClickElementNode` |
| Functions/Methods | snake_case | `execute_workflow()`, `get_by_id()` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRIES`, `DEFAULT_TIMEOUT` |
| Private members | _leading_underscore | `_internal_state`, `_cache` |
| Type vars | PascalCase | `T`, `NodeType` |

## Type Hints (Python 3.12+)

**REQUIRED** for all public APIs:
```python
from typing import Optional, Dict, Any
from casare_rpa.core.types import NodeId, PortId

def execute_node(
    node_id: NodeId,
    context: ExecutionContext,
    timeout: int = 5000
) -> Dict[str, Any]:
    """Execute a single node in a workflow."""
    ...
```

**Rules:**
- Use `Optional[T]` instead of `T | None` (compatibility)
- Use `Dict[K, V]` not `dict[K, V]` (stdlib)
- Private/internal functions: type hints optional

## Code Formatting

- **Line Length:** 100 characters max
- **Indentation:** 4 spaces (not tabs)
- **Imports:** Alphabetical within groups
  ```python
  # Standard library
  import json
  from pathlib import Path

  # Third-party
  import aiohttp
  from loguru import logger

  # Local
  from casare_rpa.domain.workflow import Workflow
  from casare_rpa.infrastructure.persistence import WorkflowRepository
  ```
- **Format Tool:** Ruff (auto-run in CI, informational)

---

**See:** `documentation.md` for docstring format
