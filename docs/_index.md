# Docs Index

Start here for all documentation. Read this index before searching under `docs/`.

## Top-Level Entry Points
| File | Purpose |
|------|---------|
| [index.md](index.md) | Docs landing page |
| [README.md](README.md) | Repository docs overview |
| [unified-system-spec.md](unified-system-spec.md) | Target architecture + design system rules (“golden paths”) |
| [refactor-program.md](refactor-program.md) | Refactor charter, governance, rollout + rollback rules |
| [migration-registry.md](migration-registry.md) | Migration tracking (what’s migrated, legacy remaining, owners, ETA) |
| [ci-quality-gates.md](ci-quality-gates.md) | CI gates for Python + dashboard |
| [websocket-contract.md](websocket-contract.md) | WebSocket protocol reference |
| [rules-map.md](rules-map.md) | Agent rules map and sources |

## Sections
| Directory | Purpose | Entry |
|-----------|---------|-------|
| [developer-guide/](developer-guide/) | Developer onboarding and internals | [developer-guide/index.md](developer-guide/index.md) |
| [adr/](adr/) | Architecture Decision Records (ADRs) | [adr/_index.md](adr/_index.md) |
| [agent/](agent/) | On-demand AI agent docs (kept out of always-loaded memory) | [agent/_index.md](agent/_index.md) |
| [operations/](operations/) | Ops runbooks and troubleshooting | [operations/index.md](operations/index.md) |
| [reference/](reference/) | Node/property/data reference | [reference/index.md](reference/index.md) |
| [security/](security/) | Security architecture and policies | [security/index.md](security/index.md) |
| [user-guide/](user-guide/) | User docs and tutorials | [user-guide/index.md](user-guide/index.md) |

## Update Protocol
1. Add new docs in the correct section
2. Update this index for new top-level files/dirs
3. Update relevant section index (e.g., `developer-guide/index.md`)
