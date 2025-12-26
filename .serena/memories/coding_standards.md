# Coding Standards - CasareRPA

## Naming Conventions
| Category | Style | Example |
|----------|-------|---------|
| Classes | PascalCase | ExecutionOrchestrator, ClickElementNode |
| Functions/Methods | snake_case | execute_workflow(), get_by_id() |
| Constants | UPPER_SNAKE_CASE | MAX_RETRIES, DEFAULT_TIMEOUT |
| Private members | _leading_underscore | _internal_state, _cache |
| Type vars | PascalCase | T, NodeType |

## Code Style
- **Line Length**: 100 characters max
- **Indentation**: 4 spaces (no tabs)
- **Import Order**: stdlib → third-party → local (alphabetical within groups)
- **Formatter**: Ruff (auto-run in CI)

## Type Hints
- REQUIRED for all public APIs
- Use `Optional[T]` instead of `T | None` (compatibility)
- Use `Dict[K, V]` not `dict[K, V]` (stdlib)
- Private/internal functions: type hints optional

## Error Handling (MANDATORY)
```python
# CORRECT
from loguru import logger

try:
    response = await client.get(url)
except Exception as exc:
    logger.error(f"HTTP failed for {url}: {exc}")
    raise

# WRONG
response = await client.get(url)
```

## Node Parameters
```python
# CORRECT (Modern)
timeout = self.get_parameter("timeout", 30000)

# WRONG (Legacy)
timeout = self.config.get("timeout", 30000)
```

## Async Patterns
- All Playwright operations MUST be async
- Use async/await consistently
- Qt event loop via qasync

## UI Rules
- Use `THEME.*` from `presentation/canvas/theme.py` (unified)
- NO hardcoded hex colors
- Use `PopupManager` for all popups
- Use `@Slot` decorator for Qt signals

## HTTP Rules
- Use `UnifiedHttpClient` from `infrastructure/http/`
- NO raw httpx/aiohttp calls

## General Principles
- **KISS**: Minimal code that works
- **NO SILENT FAILURES**: Always log errors
- **Complete code**: No TODO, pass, or placeholders
- **Remove unused**: Clean up imports/variables after changes
