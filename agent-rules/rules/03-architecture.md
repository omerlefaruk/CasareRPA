# Architecture

CasareRPA follows **Clean Architecture** (DDD).

## Layer Structure
```
presentation/ → UI (PySide6, Canvas)
     ↓
application/ → Use Cases, Services
     ↓
domain/      → Entities, Value Objects (PURE)
     ↑
infrastructure/ → Adapters (Playwright, DB, HTTP)
```

## Dependency Rule
- Dependencies point **inward**
- Domain has **ZERO** external dependencies
- Infrastructure implements domain interfaces

## Key Locations
| Layer | Path | Purpose |
|-------|------|---------|
| Domain | `domain/entities/` | Business entities |
| Domain | `domain/services/` | Domain services |
| App | `application/use_cases/` | Business operations |
| Infra | `infrastructure/browser/` | Playwright |
| Infra | `infrastructure/persistence/` | File I/O |
| UI | `presentation/canvas/` | Qt widgets |

## Node Architecture
- `nodes/` - Automation logic (uses infrastructure)
- Each node inherits from `domain.entities.BaseNode`
- Nodes are registered via `@executable_node` decorator
