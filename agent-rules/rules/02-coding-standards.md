---
description: Coding standards for CasareRPA development
---

# Coding Standards

## 1. General Principles

- BE EXTREMELY CONCISE: Sacrifice grammar. No flowery prose.
- NO TIME ESTIMATES: Never provide effort/complexity ratings.
- AUTO-IMPORTS: Add missing imports without asking.
- TERSE OUTPUT: Skip preamble, just show the code block.
- READABLE CODE: Comments only for why, never what.

## 2. Naming Conventions

| Category | Style | Example |
|----------|-------|---------|
| Classes | PascalCase | ExecutionOrchestrator, ClickElementNode |
| Functions/Methods | snake_case | execute_workflow(), get_by_id() |
| Constants | UPPER_SNAKE_CASE | MAX_RETRIES, DEFAULT_TIMEOUT |
| Private members | _leading_underscore | _internal_state, _cache |
| Type vars | PascalCase | T, NodeType |

## 3. Type Hints (Python 3.12+)

REQUIRED for all public APIs:

- Use Optional[T] instead of T | None (compatibility)
- Use Dict[K, V] not dict[K, V] (stdlib)
- Private/internal functions: type hints optional

## 4. Code Formatting

- Line Length: 100 characters max
- Indentation: 4 spaces (not tabs)
- Imports: Alphabetical within groups (stdlib, third-party, local)
- Format Tool: Ruff (auto-run in CI)

## 5. Import Order

1. Standard library
2. Third-party (aiohttp, loguru)
3. Local (casare_rpa.*)

## 6. Error Handling

- NEVER silent failures
- Use loguru for logging
- Wrap external calls in try/except
- Translate external errors to domain exceptions

## Examples (Good/Bad)

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

<<<<<<< HEAD
## Error Handling
- Use custom exceptions from `domain/errors/`
- Always log errors with context
- Return result objects, don't raise for control flow

## Browser Automation (Playwright)
- **NO HARDCODED WAITS**: Never use `asyncio.sleep()` or `time.sleep()` with fixed durations
- Use smart waiting strategies instead:
  - `page.wait_for_load_state('networkidle')` - Wait for network idle
  - `page.wait_for_load_state('domcontentloaded')` - Wait for DOM ready
  - `locator.wait_for(state='visible')` - Wait for element visibility
  - `page.wait_for_selector(selector)` - Wait for element to appear
  - `page.expect_download()` - Wait for download events
  - `page.wait_for_url(pattern)` - Wait for URL change
  - Polling with exponential backoff for custom conditions
=======
# BAD
timeout = self.config.get("timeout", 30000)
```
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
