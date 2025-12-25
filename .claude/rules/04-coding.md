---
description: Coding standards, error handling, and enforcement rules
---

# Coding Standards

## General Principles

- **BE EXTREMELY CONCISE**: Sacrifice grammar. No flowery prose.
- **NO TIME ESTIMATES**: Never provide effort/complexity ratings.
- **AUTO-IMPORTS**: Add missing imports without asking.
- **TERSE OUTPUT**: Skip preamble, just show the code block.
- **READABLE CODE**: Comments only for why, never what.

## Naming Conventions

| Category | Style | Example |
|----------|-------|---------|
| Classes | PascalCase | ExecutionOrchestrator, ClickElementNode |
| Functions/Methods | snake_case | execute_workflow(), get_by_id() |
| Constants | UPPER_SNAKE_CASE | MAX_RETRIES, DEFAULT_TIMEOUT |
| Private members | _leading_underscore | _internal_state, _cache |
| Type vars | PascalCase | T, NodeType |

## Type Hints (Python 3.12+)

REQUIRED for all public APIs:

- Use `Optional[T]` instead of `T | None` (compatibility)
- Use `Dict[K, V]` not `dict[K, V]` (stdlib)
- Private/internal functions: type hints optional

## Code Formatting

- Line Length: 100 characters max
- Indentation: 4 spaces (not tabs)
- Imports: Alphabetical within groups (stdlib, third-party, local)
- Format Tool: Ruff (auto-run in CI)

## Import Order

1. Standard library
2. Third-party (aiohttp, loguru)
3. Local (casare_rpa.*)

## Error Handling

- NEVER silent failures
- Use loguru for logging
- Wrap external calls in try/except
- Translate external errors to domain exceptions

### Examples

```python
# GOOD
from loguru import logger

try:
    response = await client.get(url)
except Exception as exc:
    logger.error(f"HTTP failed for {url}: {exc}")
    raise

# BAD
response = await client.get(url)
```

```python
# GOOD
timeout = self.get_parameter("timeout", 30000)

# BAD
timeout = self.config.get("timeout", 30000)
```

## Hard Constraints

1. **No External Imports in Domain**: The domain layer must remain pure
2. **No Synchronous I/O in Async Contexts**: Do not block the event loop
3. **No Hardcoded Secrets**: Use the credential manager

## Boundaries (Never)

1. **No Main Branch Work**: Do not work directly on `main`/`master` (use worktrees)
2. **No Destructive Commands**: No `git reset --hard`, `git checkout --`, `rm -rf` without explicit request
3. **No Secret Leakage**: Never commit or print secrets/tokens
4. **No Silent Errors**: Always log external failures with context
5. **No Domain Violations**: Domain must not import infrastructure/presentation
