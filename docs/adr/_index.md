# Architecture Decision Records (ADRs)

ADRs capture decisions that affect long-lived contracts and developer "golden paths".

## Active ADRs

| ID | Title | Status | Date |
|----|-------|--------|------|
| [0001](0001-architecture-boundary-enforcement.md) | Architecture Boundary Enforcement | Accepted | 2025-12-30 |

## When an ADR is required

- Token contract / theming strategy (Desktop + Dashboard)
- API error envelope, OpenAPI generation, WebSocket event schemas
- Clean Architecture boundary rules and enforcement strategy
- DI/composition root strategy
- Persistence/eventing/cancellation lifecycle contracts

## How to add an ADR

1. Copy `docs/adr/0000-template.md`
2. Assign the next available number (e.g., `0002-...`)
3. Keep it short and actionable
4. Link it from any PR that implements it
5. Update this index with a reference

