---
description: DDD Clean Architecture patterns for CasareRPA
---

# Architecture

## DDD 2025 Layers

| Layer | Path | Dependencies |
|-------|------|--------------|
| Domain | domain/ | None |
| Application | application/ | Domain |
| Infrastructure | infrastructure/ | Domain, App |
| Presentation | presentation/ | All |

Dependency Flow: ONLY this direction. NO reverse dependencies.

## Layer Responsibilities

### Domain Layer (domain/)
- Pure business logic, no external dependencies
- Entities, Value Objects, Domain Services, Exceptions
- NO imports from infrastructure, presentation, application
- NO I/O operations
- NO external library calls (except dataclasses, typing)

### Application Layer (application/)
- Use case orchestration, transaction management
- Use Cases, DTOs, Interfaces, Exceptions
- Import from domain (always)
- Import from infrastructure ONLY via dependency injection
- Async by default

### Infrastructure Layer (infrastructure/)
- Implement domain interfaces, adapt external APIs
- Adapters, Repositories, Resource Managers, Configuration
- All I/O here (Playwright, DB, HTTP, win32)
- Handle retries, connection pooling, resource cleanup

### Presentation Layer (presentation/)
- UI/UX, user interaction, event handling
- Main Window, Canvas, Controllers, EventBus, Widgets
- Async via qasync (Qt event loop + asyncio)
- Emit events for side effects via EventBus

## Key Patterns

| Pattern | Location | Usage |
|---------|----------|-------|
| Typed Events | domain/events/ | NodeCompleted, WorkflowStarted (frozen dataclasses) |
| EventBus | domain/events/__init__.py | get_event_bus() singleton |
| Aggregates | domain/aggregates/ | Workflow aggregate root |
| Unit of Work | infrastructure/persistence/unit_of_work.py | Transaction + event publishing |
| CQRS Queries | application/queries/ | Read-optimized DTOs |
| Qt Event Bridge | presentation/canvas/coordinators/event_bridge.py | Domain to Qt signals |
