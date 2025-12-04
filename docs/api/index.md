# API Reference

Complete API documentation for CasareRPA v3.1.

**Total:** 382 modules, 1,445 classes, 10,015 functions

## Architecture Layers

CasareRPA follows Clean Architecture (DDD):

```
Presentation → Application → Domain ← Infrastructure
```

| Layer | Modules | Classes | Description |
|-------|---------|---------|-------------|
| [Domain](domain/index.md) | 55 | 118 | Pure business logic, entities, value objects, and domain services |
| [Application](application/index.md) | 37 | 120 | Use cases, orchestration, and application services |
| [Infrastructure](infrastructure/index.md) | 128 | 576 | External integrations, persistence, security, and resources |
| [Presentation](presentation/index.md) | 162 | 631 | UI components, canvas, controllers, and panels |

## Orchestrator REST API

FastAPI backend with Swagger documentation at http://localhost:8000/docs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/workflows` | POST | Submit workflow for execution |
| `/api/v1/workflows/{id}` | GET | Get workflow details |
| `/api/v1/workflows/{id}` | DELETE | Delete workflow |
| `/api/v1/schedules` | POST | Create cron schedule |
| `/api/v1/schedules` | GET | List all schedules |
| `/api/v1/schedules/{id}/enable` | PUT | Enable schedule |
| `/api/v1/schedules/{id}/disable` | PUT | Disable schedule |
| `/api/v1/jobs` | GET | List job queue |
| `/api/v1/robots` | GET | List connected robots |
| `/api/v1/analytics/bottlenecks` | GET | Bottleneck detection |
| `/api/v1/analytics/execution-timeline` | GET | Execution timeline |
| `/health` | GET | Health check |

### WebSocket Endpoints

| Endpoint | Description |
|----------|-------------|
| `/ws/live-jobs` | Real-time job status updates |
| `/ws/robot-status` | Robot heartbeat monitoring |
| `/ws/queue-metrics` | Queue depth metrics |

[View Full Orchestrator API Reference](infrastructure/orchestrator-api.md)

## Quick Links

### Domain Layer
- [Entities](domain/entities.md) - Core domain objects (Workflow, Node, Project)
- [Value Objects](domain/value-objects.md) - Immutable values (Port, DataType)
- [Services](domain/services.md) - Domain services (ExecutionOrchestrator)
- [Decorators](domain/decorators.md) - Node decorators (@executable_node, @node_schema)

### Application Layer
- [Use Cases](application/use-cases.md) - Application use cases
- [Services](application/services.md) - Application services

### Infrastructure Layer
- [Resources](infrastructure/resources.md) - Resource managers (Browser, Desktop)
- [Persistence](infrastructure/persistence.md) - Data persistence (PostgreSQL, filesystem)
- [Security](infrastructure/security.md) - Security components (JWT, credentials)
- [Orchestrator API](infrastructure/orchestrator-api.md) - FastAPI REST API
- [Analytics](infrastructure/analytics.md) - Bottleneck detection, process mining

### Presentation Layer
- [Controllers](presentation/controllers.md) - UI controllers (Workflow, Execution, Menu)
- [Panels](presentation/panels.md) - UI panels (Analytics, Debug, Variables, Node Library)
