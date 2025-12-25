# Error Handling Standards

**Part of:** `.brain/projectRules.md` | **See also:** `testing.md`

## Exception Hierarchy

```
Exception
├── CasareRPAError (base)
│   ├── DomainError
│   │   ├── WorkflowValidationError
│   │   ├── DuplicateNodeError
│   │   └── NodeExecutionError
│   ├── ApplicationError
│   │   ├── WorkflowNotFoundError
│   │   ├── ExecutionFailedError
│   │   └── InvalidInputError
│   └── InfrastructureError
│       ├── RepositoryError
│       ├── ResourceNotAvailableError
│       └── ExternalServiceError
```

## Exception Handling Pattern

```python
# Domain: Raise domain-specific errors
if not self._name:
    raise WorkflowValidationError("Workflow name required")

# Application: Catch + translate
try:
    workflow = await self._repository.get(workflow_id)
except RepositoryError as e:
    raise ApplicationError(f"Failed to fetch workflow: {e}") from e

# Infrastructure: Catch external errors
try:
    response = await client.get(url)
except aiohttp.ClientError as e:
    raise ExternalServiceError(f"HTTP error: {e}") from e

# Presentation: Log + show to user
try:
    await use_case.execute()
except CasareRPAError as e:
    logger.error(f"Operation failed: {e}")
    self._event_bus.emit("error", {"message": str(e)})
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Test hangs | Missing `@pytest.mark.asyncio` | Add decorator to async tests |
| Flaky tests | Timing dependencies | Use event/signal waits, not sleep |
| Import errors | Circular dependency | Check layer rules, use interfaces |
| Mock not tracking calls | Using `Mock()` for async | Use `AsyncMock()` instead |

---

**See:** `documentation.md` for docstring format
