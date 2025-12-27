# Domain Layer Rules

**Pure business logic with zero external dependencies.**

## Core Principles

1. **No External Imports**: Never import from Infrastructure or Presentation
2. **No I/O Operations**: No file, network, or database calls
3. **Framework Agnostic**: No PySide6, Playwright, aiohttp
4. **Testable in Isolation**: All logic testable without mocks

## Allowed Imports

```python
# ALLOWED
from dataclasses import dataclass
from typing import Optional, Dict
from enum import Enum

# DOMAIN-INTERNAL
from casare_rpa.domain.entities import BaseNode
from casare_rpa.domain.value_objects import DataType

# PROHIBITED
from casare_rpa.infrastructure.http import UnifiedHttpClient  # NO
from casare_rpa.presentation.canvas.theme_system import THEME, TOKENS
import aiohttp  # NO
from PySide6.QtWidgets import QWidget  # NO
```

## Event System (DDD 2025)

```python
from casare_rpa.domain.events import NodeCompleted, get_event_bus

bus = get_event_bus()
bus.publish(NodeCompleted(node_id="x", execution_time_ms=100))
```

See `@events/` for event types, `@aggregates/` for aggregate patterns.

## Schema-Driven Logic

```python
@properties(
    PropertyDef("url", PropertyType.STRING, required=True),
    PropertyDef("timeout", PropertyType.INTEGER, default=30000),
)
@node(category="browser")
class MyNode(BaseNode):
    async def execute(self, context):
        url = self.get_parameter("url")  # port or config fallback
```

See decorators, schemas in `@/index.md`.

## Cross-References

- Application layer: `../application/_index.md`
- Infrastructure adapters: `../infrastructure/_index.md`
- Root guide: `../../../../CLAUDE.md`
