# Application Layer Rules

**Orchestrates domain operations via use cases.**

## Core Principles

1. **Domain Only**: Never import from Infrastructure or Presentation
2. **Use Cases**: Single-responsibility operations (CQRS Command side)
3. **Query Services**: Read-optimized views (CQRS Query side)
4. **Result Types**: Explicit success/failure returns

## Dependencies

```
Domain ← Application ← Infrastructure/Presentation
```

## Use Case Pattern

```python
class ExecuteWorkflowUseCase:
    def __init__(self, uow: AbstractUnitOfWork, event_bus: EventBus):
        self._uow = uow
        self._event_bus = event_bus

    async def execute(self, workflow_id: str) -> Result:
        async with self._uow as uow:
            workflow = await uow.workflows.get(workflow_id)
            # Business logic...
```

## CQRS Pattern

```python
# COMMAND (write)
from casare_rpa.application.use_cases import CreateProjectUseCase

# QUERY (read)
from casare_rpa.application.queries import WorkflowQueryService
dto = await query_service.list_workflows(filter=WorkflowFilter(...))
```

## Common Imports

```python
# Use cases
from casare_rpa.application.use_cases import (
    ExecuteWorkflowUseCase, NodeExecutor, VariableResolver
)

# DI Container
from casare_rpa.application.dependency_injection import DIContainer
```

## Cross-References

- Domain entities: `../domain/_index.md`
- Infrastructure adapters: `../infrastructure/_index.md`
- Root guide: `../../../../CLAUDE.md`
