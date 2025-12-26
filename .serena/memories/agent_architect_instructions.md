# Agent Instructions - Architect Agent

## Your Role
High-level design, pattern definition, implementation planning.

## Serena Tools (USE AGGRESSIVELY)

### Architecture Discovery

1. **find_symbol** - Find architectural patterns
```python
mcp__plugin_serena_serena__find_symbol(
    name_path_pattern="*Aggregate*",
    relative_path="src/casare_rpa/domain/aggregates/",
    include_body=False,
    depth=1
)
```

2. **get_symbols_overview** - Layer structure analysis
```python
mcp__plugin_serena_serena__get_symbols_overview(
    relative_path="src/casare_rpa/domain/",
    depth=1
)
```

3. **find_referencing_symbols** - Understand dependencies
```python
mcp__plugin_serena_serena__find_referencing_symbols(
    name_path="EventBus",
    relative_path="src/casare_rpa/domain/events.py"
)
```

### Pattern Analysis

4. **search_for_pattern** - Find pattern usage
```python
# Find all domain events
mcp__plugin_serena_serena__search_for_pattern(
    substring_pattern=r"@dataclass\(frozen=True\).*Event.*DomainEvent",
    relative_path="src/casare_rpa/domain/events/",
    context_lines_before=2,
    context_lines_after=5
)

# Find CQRS patterns
mcp__plugin_serena_serena__search_for_pattern(
    substring_pattern=r"class.*Query.*:",
    relative_path="src/casare_rpa/application/queries/"
)
```

## DDD 2025 Architecture

### Layer Responsibilities
| Layer | Responsibility | Path |
|-------|----------------|------|
| Domain | Pure logic, entities, aggregates, events | `domain/` |
| Application | Use cases, queries (CQRS) | `application/` |
| Infrastructure | Persistence, HTTP, adapters | `infrastructure/` |
| Presentation | Qt UI, coordinators | `presentation/` |

### Key Patterns
| Pattern | Location | Purpose |
|---------|----------|---------|
| EventBus | `domain/events.py` | Event-driven communication |
| Typed Events | `domain/events/*.py` | Frozen dataclass events |
| Aggregates | `domain/aggregates/` | Consistency boundaries |
| Unit of Work | `infrastructure/persistence/` | Transactions + events |
| CQRS | `application/queries/` | Read-optimized queries |

### Boundary Rules
- **Domain**: NO imports from infrastructure/presentation
- **Application**: Can import domain, NOT presentation
- **Infrastructure**: Can import domain, application
- **Presentation**: Can import all layers

## Planning Workflow

1. **Research**: Use Serena tools to understand existing patterns
2. **Design**: Define changes within DDD boundaries
3. **Verify**: Check for violations with `search_for_pattern`
4. **Document**: Create plan in `.brain/plans/`

## Design Principles

- **Domain Purity**: Domain layer has ZERO external dependencies
- **Event-Driven**: Use typed events for cross-layer communication
- **Async First**: All I/O operations must be async
- **Dependency Inversion**: Depend on abstractions, not concretions
