# Infrastructure Layer Rules

**Framework integrations and external adapters.**

## Core Principles

1. **Implement Domain Interfaces**: Never import from Presentation
2. **Wrap External Libraries**: Playwright, UIAutomation, aiohttp
3. **Resilience**: Retry, circuit breaker, timeout
4. **No Business Logic**: Only orchestration and technical concerns

## HTTP Client (MANDATORY)

```python
# CORRECT
from casare_rpa.infrastructure.http import UnifiedHttpClient
client = await get_unified_http_client()
result = await client.get(url)

# WRONG
import aiohttp
async with aiohttp.ClientSession() as session:  # NO
```

See `@http/` for UnifiedHttpClient patterns.

## Browser Management

```python
from casare_rpa.infrastructure.browser import (
    PlaywrightManager, get_playwright_singleton
)
manager = get_playwright_singleton()
page = await manager.get_page(page_id)
```

## Persistence (Unit of Work)

```python
from casare_rpa.infrastructure.persistence import JsonUnitOfWork

async with JsonUnitOfWork(path, event_bus) as uow:
    workflow = await uow.workflows.get(id)
    uow.track(workflow)
    await uow.commit()  # Publishes domain events
```

## Security

```python
from casare_rpa.infrastructure.security import VaultClient
vault = VaultClient()
credential = await vault.get_credential(name)
```

## Cross-References

- Domain interfaces: `../domain/_index.md`
- Use cases: `../application/_index.md`
- Root guide: `../../../../CLAUDE.md`
