# Refactor Program (Charter + Governance)

This document is the operating system for the CasareRPA refactor program: scope, rules of engagement, quality gates, and rollback policy.

## Mission

- Unify architecture conventions and golden paths across the Python system (domain/app/infra boundaries, config, logging, errors, DI, async patterns).
- Modernize and unify UI/UX across Desktop Canvas and Monitoring Dashboard using one design language and token source of truth.
- Remove legacy/duplicate systems via incremental migrations with safety rails.

## Hard constraints

- No big-bang rewrite. Use strangler migrations, feature flags, and compatibility adapters.
- No regressions. Add tests around hot paths before refactoring them.
- Enforce boundaries:
  - Domain has zero framework/IO imports.
  - Application imports domain only.
- UI rules remain true:
  - Desktop: no hardcoded hex; tokens only via theme system.
  - Dashboard: no ad-hoc inline styles; design tokens + component primitives only.

## Definition of Done (global)

- Desktop Canvas runs purely on v2 UI (v1 escape hatch removed after a stable release window).
- One design-token source of truth drives:
  - Desktop: `src/casare_rpa/presentation/canvas/theme/`
  - Dashboard: Tailwind theme + component primitives
- Architecture boundaries are enforced automatically (lint/CI).
- Golden paths exist for: HTTP, auth, logging, config, events, persistence, orchestrator client.
- Node ecosystem conforms to “Modern Node Standard 2025” (`src/casare_rpa/nodes/_index.md`) with high automation for schema/tests/registration.

## Non-goals (for this program window)

- Replacing core frameworks (PySide6, FastAPI, Vite) unless explicitly approved via ADR.
- Large-scale UI redesign without token/component foundations.
- “Perfect” strict typing everywhere on day 1; typing is phased with clear gates.

---

# Operating Rules

## Work structure: Epics → Tasks

- Every change maps to exactly one **task ID** in `plans/refactor-program-backlog.md`.
- Each task includes:
  - Scope and directory footprint
  - Acceptance criteria
  - Rollback strategy
  - Quality gates (tests/checks) required before merging

## Quality policy: tests before refactors on hot paths

“Hot paths” include:

- Desktop startup, open/save workflow, execute workflow, undo/redo, node add/delete.
- Orchestrator API error envelope, OpenAPI schema generation, WebSocket events.
- Node registry, schema validation, node execution runtime.

Rule:

- If a task touches a hot path, add targeted tests (or contract tests) **before** refactoring behavior.

## Rollout policy

- Use feature flags for behavior changes that are risky or user-visible.
- Default behavior must remain stable unless the task explicitly changes it and has a rollback path.
- Prefer additive changes (new module + adapter) over invasive edits.

## Rollback policy

Every task must declare a rollback strategy that is one of:

- Revert commit(s) cleanly.
- Flip a feature flag back to legacy behavior.
- Keep both contracts (v1/v2) temporarily via adapters while migrating.

Rollback must be possible without data migration whenever feasible.

---

# KPI Baselines (required)

Record baseline values before major work begins, and track deltas weekly:

| KPI | How measured | Baseline | Target | Notes |
|---|---|---:|---:|---|
| Desktop startup time | timed from app entry → main window ready | TBD | -20% | keep same machine |
| Desktop UI responsiveness | interaction latency on key actions | TBD | “no regressions” | define test script |
| Dashboard bundle size | `vite build` output (gz) | TBD | -15% | after token/primitives |
| Python test runtime | `pytest -m unit` | TBD | stable | prevent creep |
| Lint/type issues | ruff + mypy counts | TBD | trending down | phased strictness |
| Boundary violations | boundary scripts / lints | TBD | 0 new | changed-files gates |

---

# Decision process (ADRs)

- Any decision that changes a contract (tokens, API, events, architecture boundaries, DI strategy) must be captured as an ADR.
- ADRs are lightweight and must include: decision, context, consequences, migration plan.

See `docs/adr/0000-template.md`.

---

# References

- Target architecture and UI rules: `docs/unified-system-spec.md`
- Migration tracking: `docs/migration-registry.md`
- CI gates: `docs/ci-quality-gates.md`
- Existing UI rules: `docs/agent/ui-theme.md`
- Design tokens guidance: `.brain/docs/design-system-2025.md`


