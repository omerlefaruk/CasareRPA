# Architecture Rules

**Part of:** `.brain/projectRules.md` | **See also:** `coding-standards.md`, `testing.md`

## Clean DDD Layers

```
Presentation (GUI) → Application (Use Cases) → Domain (Entities/VOs)
                           ↓
                   Infrastructure (Adapters)
```

**Dependency Flow:** ONLY this direction. NO reverse dependencies.

## Layer Definitions

### Domain Layer (`src/casare_rpa/domain/`)
- **Responsibility:** Pure business logic, no external dependencies
- **Contains:** Entities, Value Objects, Domain Services, Exceptions
- **Rules:**
  - NO imports from `infrastructure`, `presentation`, `application`
  - NO I/O operations (sync or async)
  - State changes via methods, not property assignment

### Application Layer (`src/casare_rpa/application/`)
- **Responsibility:** Use case orchestration, transaction management
- **Contains:** Use Cases, DTOs, Interfaces, Exceptions
- **Rules:**
  - Import from `domain` (always)
  - Import from `infrastructure` ONLY via dependency injection
  - Async by default (await infrastructure calls)

### Infrastructure Layer (`src/casare_rpa/infrastructure/`)
- **Responsibility:** Implement domain interfaces, adapt external APIs
- **Contains:** Adapters, Repositories, Resource Managers, Configuration
- **Rules:**
  - Import from `domain` + `application` (interfaces)
  - All I/O here (Playwright, DB, HTTP, win32)
  - Translate external errors to domain exceptions

### Presentation Layer (`src/casare_rpa/presentation/`)
- **Responsibility:** UI/UX, user interaction, event handling
- **Contains:** MainWindow, Canvas, Controllers, EventBus, Widgets
- **Rules:**
  - Import from `application` (Use Cases) only
  - DO NOT import from `infrastructure`
  - Async operations via qasync (Qt event loop + asyncio)

## Dependency Injection

- Use constructor injection (not global singletons)
- Container managed by `Application` (main entry point)
- Avoid circular dependencies by injecting interfaces

## Layer Dependency Diagram

```
┌─────────────────────────────────────┐
│         Presentation (UI)           │
│  MainWindow, Canvas, Controllers    │
└────────────┬────────────────────────┘
             │ depends on
             v
┌─────────────────────────────────────┐
│     Application (Use Cases)         │
│  ExecuteWorkflow, SaveWorkflow      │
└────────────┬──────────┬─────────────┘
             │ depends  │ depends
             │ on       │ on
             v          v
┌──────────────────┐  ┌──────────────────────┐
│  Domain (Logic)  │  │  Infrastructure      │
│  Entities, VOs   │  │  Repositories,       │
│  NO deps!        │  │  Adapters, Resources │
└──────────────────┘  └──────────────────────┘
```

---

**See:** `testing.md` for layer-specific test patterns
