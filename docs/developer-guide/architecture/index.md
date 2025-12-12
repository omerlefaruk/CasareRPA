# Architecture Documentation

CasareRPA follows Domain-Driven Design (DDD) 2025 patterns with clean layer separation and typed domain events.

---

## In This Section

| Document | Description |
|----------|-------------|
| [Overview](overview.md) | High-level architecture introduction |
| [Layers](layers.md) | DDD layer responsibilities and boundaries |
| [Events](events.md) | Typed domain event system |
| [Aggregates](aggregates.md) | Aggregate roots and consistency boundaries |
| [Diagrams](diagrams.md) | Visual architecture representations |

---

## Architecture Principles

### Clean Architecture

```
┌─────────────────────────────────────────┐
│           Presentation Layer            │
│     (Canvas, CLI, REST Controllers)     │
├─────────────────────────────────────────┤
│           Application Layer             │
│      (Use Cases, Commands, Queries)     │
├─────────────────────────────────────────┤
│             Domain Layer                │
│   (Entities, Aggregates, Events, VOs)   │
├─────────────────────────────────────────┤
│          Infrastructure Layer           │
│   (Repositories, HTTP, Browser, Queue)  │
└─────────────────────────────────────────┘
```

### Dependency Rule

Dependencies always point **inward** toward the domain:

- **Presentation** → Application → Domain
- **Infrastructure** → Domain
- **Domain** → Nothing (pure business logic)

### Key Patterns

| Pattern | Purpose | Location |
|---------|---------|----------|
| **EventBus** | Decoupled event publishing | `domain/events.py` |
| **Typed Events** | Type-safe event contracts | `domain/events/*.py` |
| **Aggregates** | Transaction boundaries | `domain/aggregates/` |
| **Unit of Work** | Transactional consistency | `infrastructure/persistence/` |
| **CQRS** | Separate read/write models | `application/queries/` |

---

## Quick Navigation

- **New to the architecture?** Start with [Overview](overview.md)
- **Understanding layers?** Read [Layers](layers.md)
- **Working with events?** See [Events](events.md)
- **Designing aggregates?** Check [Aggregates](aggregates.md)

---

## Related Documentation

- [Creating Custom Nodes](../extending/creating-nodes.md)
- [API Reference](../api-reference/index.md)
- [Internals Deep Dives](../internals/index.md)
