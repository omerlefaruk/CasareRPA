# Coding Standards

This document defines the coding standards for CasareRPA. All contributions must adhere to these guidelines.

## Core Principles

1. **KISS** - Keep It Simple, Stupid. Minimal code that works.
2. **BE CONCISE** - Sacrifice grammar for brevity. No flowery prose.
3. **READABLE CODE** - Code is self-documenting. Comments explain "why", not "what".
4. **TYPE SAFETY** - All public APIs must have type hints.
5. **NO SILENT FAILURES** - Wrap external calls in try/except, log context.

## Python Style Guide

Follow [PEP 8](https://peps.python.org/pep-0008/) with these project-specific rules:

### Naming Conventions

| Category | Style | Example |
|----------|-------|---------|
| Classes | PascalCase | `ExecutionOrchestrator`, `ClickElementNode` |
| Functions/Methods | snake_case | `execute_workflow()`, `get_by_id()` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRIES`, `DEFAULT_TIMEOUT` |
| Private members | _leading_underscore | `_internal_state`, `_cache` |
| Type variables | PascalCase | `T`, `NodeType` |

### Formatting

- **Line length:** 100 characters max
- **Indentation:** 4 spaces (no tabs)
- **Formatter:** Ruff (auto-run by pre-commit)

```bash
# Format code
ruff format src/ tests/

# Lint and fix
ruff check src/ tests/ --fix
```

## Type Hints (Required)

All public APIs **must** have type hints. Private/internal functions are optional.

```python
from typing import Optional, Dict, Any, List
from casare_rpa.domain.value_objects import NodeId, PortId

def execute_node(
    node_id: NodeId,
    context: ExecutionContext,
    timeout: int = 5000
) -> Dict[str, Any]:
    """Execute a single node in a workflow."""
    ...
```

### Type Hint Rules

- Use `Optional[T]` instead of `T | None` (compatibility)
- Use `Dict[K, V]` not `dict[K, V]` (stdlib consistency)
- Use `List[T]` not `list[T]` for return types
- Complex types: Create type aliases

```python
# Type aliases for complex types
NodeResult = Dict[str, Any]
PortMapping = Dict[PortId, Any]
ConnectionList = List[Tuple[NodeId, PortId, NodeId, PortId]]
```

## Import Order

Organize imports in three groups, alphabetical within each:

```python
# 1. Standard library
import json
from pathlib import Path
from typing import Optional, Dict, Any

# 2. Third-party
import aiohttp
from loguru import logger
from PySide6.QtWidgets import QWidget

# 3. Local imports
from casare_rpa.domain.workflow import Workflow
from casare_rpa.infrastructure.persistence import WorkflowRepository
```

> **Note:** Ruff auto-organizes imports. Run `ruff check --fix` to fix order.

## Docstrings (Google Style)

Use Google-style docstrings for all public functions and classes:

```python
def execute_node(
    node_id: NodeId,
    context: ExecutionContext,
    timeout: int = 5000
) -> Dict[str, Any]:
    """Execute a single node in a workflow.

    Executes the node identified by node_id within the given execution
    context. Respects the provided timeout for the operation.

    Args:
        node_id: Unique identifier of the node to execute.
        context: Current execution context with variables and resources.
        timeout: Maximum execution time in milliseconds. Defaults to 5000.

    Returns:
        Dictionary with keys:
            - success (bool): Whether execution succeeded
            - result (Any): Node output value
            - error (str): Error message if failed

    Raises:
        NodeNotFoundError: If node_id does not exist in workflow.
        ExecutionTimeoutError: If execution exceeds timeout.

    Example:
        >>> context = ExecutionContext(variables={}, resources={})
        >>> result = await execute_node(NodeId("n1"), context)
        >>> print(result["success"])
        True
    """
    ...
```

### Docstring Rules

- First line: Brief summary (imperative mood: "Execute", not "Executes")
- Blank line after summary
- Args section: Parameter name + description
- Returns section: Describe structure
- Raises section: List all exceptions
- Example section: Working code (optional but encouraged)

## Error Handling

### Always Wrap External Calls

```python
from loguru import logger

async def fetch_workflow(workflow_id: str) -> Workflow:
    """Fetch workflow from repository."""
    try:
        workflow = await self._repository.get_by_id(workflow_id)
        if not workflow:
            raise WorkflowNotFoundError(f"Workflow {workflow_id} not found")
        return workflow
    except RepositoryError as e:
        logger.error(f"Failed to fetch workflow {workflow_id}: {e}")
        raise ApplicationError(f"Database error: {e}") from e
```

### Exception Hierarchy

```
CasareRPAError (base)
├── DomainError
│   ├── WorkflowValidationError
│   ├── DuplicateNodeError
│   └── NodeExecutionError
├── ApplicationError
│   ├── WorkflowNotFoundError
│   ├── ExecutionFailedError
│   └── InvalidInputError
└── InfrastructureError
    ├── RepositoryError
    ├── ResourceNotAvailableError
    └── ExternalServiceError
```

### Logging with Loguru

```python
from loguru import logger

# Good: Context-rich logging
logger.info(f"Starting workflow execution: {workflow_id}")
logger.warning(f"Node {node_id} timeout after {timeout}ms, retrying...")
logger.error(f"Failed to click element: selector={selector}, error={e}")

# Bad: Vague logging
logger.info("Starting...")
logger.error("Failed")
```

## No Hardcoded Values

### Theme Colors

Use `THEME` constants for all colors:

```python
# CORRECT
from casare_rpa.presentation.canvas.ui.theme import THEME

widget.setStyleSheet(f"background: {THEME['background']};")

# INCORRECT - No hardcoded colors!
widget.setStyleSheet("background: #1e1e1e;")  # NO!
```

### Configuration Values

```python
# CORRECT - Use constants
from casare_rpa.core.constants import MAX_RETRIES, DEFAULT_TIMEOUT

retry_count = MAX_RETRIES
timeout = DEFAULT_TIMEOUT

# INCORRECT - No magic numbers!
retry_count = 3  # NO!
timeout = 5000  # NO!
```

## DDD Architecture Patterns

### Layer Dependencies

```
Presentation (UI) --> Application (Use Cases) --> Domain (Entities/VOs)
                              |
                              v
                      Infrastructure (Adapters)
```

**Dependency Rule:** ONLY downward dependencies. NO reverse dependencies.

| Layer | Can Import | Cannot Import |
|-------|-----------|---------------|
| Domain | Nothing | Everything else |
| Application | Domain | Infrastructure (directly), Presentation |
| Infrastructure | Domain, Application interfaces | Presentation |
| Presentation | Application | Infrastructure (directly) |

### Typed Events

Use typed domain events for all event-driven communication:

```python
from casare_rpa.domain.events import NodeCompleted, get_event_bus

# Publishing events
bus = get_event_bus()
bus.publish(NodeCompleted(
    node_id="node-1",
    node_type="ClickElementNode",
    execution_time_ms=150
))

# Subscribing to events
def handle_node_completed(event: NodeCompleted) -> None:
    logger.info(f"Node {event.node_id} completed in {event.execution_time_ms}ms")

bus.subscribe(NodeCompleted, handle_node_completed)
```

### Use UnifiedHttpClient

All HTTP operations must use `UnifiedHttpClient`:

```python
# CORRECT
from casare_rpa.infrastructure.http import UnifiedHttpClient

async with UnifiedHttpClient() as client:
    response = await client.get(url)

# INCORRECT - Never use raw aiohttp/httpx!
import aiohttp
async with aiohttp.ClientSession() as session:
    response = await session.get(url)  # NO!
```

**Why:** UnifiedHttpClient provides rate limiting, circuit breaker, retry logic, and SSRF protection.

## Qt/PySide6 Patterns

### Signal-Slot Rules

All signal handlers require `@Slot()` decorator:

```python
from PySide6.QtCore import Slot

class MyWidget(QWidget):
    @Slot()
    def on_button_clicked(self) -> None:
        """Handle button click."""
        ...

    @Slot(str)
    def on_text_changed(self, text: str) -> None:
        """Handle text change."""
        ...
```

### No Lambda Connections

Use named methods or `functools.partial`:

```python
from functools import partial

# CORRECT
button.clicked.connect(self.on_button_clicked)
button.clicked.connect(partial(self.handle_click, node_id))

# INCORRECT - No lambdas!
button.clicked.connect(lambda: self.do_something())  # NO!
```

## Code Quality Checklist

Before committing, verify:

- [ ] All public functions have type hints
- [ ] All public functions have docstrings
- [ ] No hardcoded colors (use `THEME`)
- [ ] No hardcoded magic numbers (use constants)
- [ ] External calls wrapped in try/except
- [ ] Errors logged with context
- [ ] No unused imports (Ruff will catch this)
- [ ] No debug statements (`print`, `pdb`)
- [ ] No commented-out code
- [ ] No TODO without GitHub issue link

## Linting Commands

```bash
# Format code
ruff format src/ tests/

# Lint and fix
ruff check src/ tests/ --fix

# Type check
mypy src/

# Security audit
pip-audit
```

## Related Documentation

- [Testing Guide](testing.md) - TDD practices and test structure
- [Pull Request Guidelines](pull-requests.md) - PR requirements
- [DDD Architecture](../architecture/) - Clean architecture details

---

**Reference:** Full coding rules are in `.brain/projectRules.md`.
