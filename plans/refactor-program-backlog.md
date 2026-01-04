# Refactor Program Backlog (Single Source of Truth)

This backlog is the authoritative execution tracker for the refactor program.

Rules:

- Every PR references at least one task ID from this file.
- Every task has acceptance criteria and a rollback strategy.
- Prefer small, reversible changes (strangler).

Owners use role names from `docs/agent/agents.md` until specific names are assigned.

## Status legend

- **Not started**
- **In progress**
- **Blocked**
- **Done**

---

# Epic 0 — Program Governance + Safety Rails

## GOV-001 — Refactor charter + rollout/rollback rules

- **Owner:** Architect
- **Status:** Done
- **Scope:** `docs/refactor-program.md` (keep current as source of truth)
- **Acceptance criteria:**
  - Charter defines scope, non-goals, DoD, rollout rules, rollback policy
  - All subsequent tasks link back to the charter
- **Rollback:** revert docs change (docs-only)

## GOV-002 — Migration registry (initial + ongoing updates)

- **Owner:** Architect
- **Status:** Done
- **Scope:** `docs/migration-registry.md`
- **Acceptance criteria:**
  - Registry lists each legacy system and its target replacement
  - Each migration has an owner, ETA, gates, rollback path
- **Rollback:** docs-only

## GOV-003 — ADR process + template

- **Owner:** Architect
- **Status:** Done
- **Scope:** `docs/adr/`
- **Acceptance criteria:** ADR template exists and is referenced from governance docs
- **Rollback:** docs-only

## GOV-004 — KPI baselines and measurement scripts

- **Owner:** QA Specialist
- **Status:** In progress
- **Scope:** `scripts/` + `docs/refactor-program.md`
- **Acceptance criteria:**
  - Baselines recorded (startup time, dashboard size, test runtime, lint/type counts)
  - KPI measurement is repeatable and documented
- **Rollback:** keep reporting only (no gating)

---

# Epic 1 — Architecture Unification (Python Clean Architecture Hardening)

## ARCH-001 — Boundary enforcement: domain purity (CI)

- **Owner:** Architect
- **Status:** Done
- **Scope:** CI + `scripts/check_domain_purity.py`
- **Acceptance criteria:** CI fails on domain purity violations
- **Rollback:** change to “changed-files only” mode for one sprint

## ARCH-002 — Boundary enforcement: application purity

- **Owner:** Architect
- **Status:** Done
- **Scope:** add `scripts/check_application_purity.py` + CI hook
- **Acceptance criteria:** CI fails if `application/` imports `infrastructure/` or `presentation/`
- **Rollback:** changed-files only; allowlisted exceptions with explicit TODOs

## ARCH-003 — Boundary enforcement: presentation dependency direction

- **Owner:** Architect
- **Status:** Done
- **Scope:** add `scripts/check_presentation_dependency_direction.py` + CI hook
- **Acceptance criteria:** presentation does not import infrastructure directly (except allowlist during migration)
- **Rollback:** changed-files only; temporary allowlist

## ARCH-004 — Golden path: outbound HTTP client mandate

- **Owner:** Architect
- **Status:** In progress (pre-commit hook exists)
- **Scope:** `src/casare_rpa/infrastructure/http/` + `scripts/check_http_client_usage.py`
- **Acceptance criteria:** no new raw `aiohttp/httpx` usage outside allowlisted modules
- **Rollback:** allowlist specific modules with documented exceptions (streaming, etc.)

## ARCH-005 — Golden path: config API unification

- **Owner:** Architect
- **Status:** Not started
- **Scope:** `src/casare_rpa/config/` + refactors in callers
- **Acceptance criteria:**
  - No `os.environ` reads outside config package
  - Typed config objects for core runtime paths
- **Rollback:** adapter that preserves legacy reads temporarily

## ARCH-006 — Golden path: logging + correlation conventions

- **Owner:** Architect
- **Status:** Not started
- **Scope:** `src/casare_rpa/config/logging_setup.py` + entrypoint binding
- **Acceptance criteria:** request/job/workflow IDs appear in logs consistently
- **Rollback:** keep previous formatting; preserve old keys while adding new ones

## ARCH-007 — Error + Result contract consolidation

- **Owner:** Architect
- **Status:** Not started
- **Scope:** `src/casare_rpa/domain/errors/` + backend mapping
- **Acceptance criteria:** one canonical error envelope for API + consistent UI mapping
- **Rollback:** per-router mapping adapters while migrating

## ARCH-008 — DI unification: composition root only

- **Owner:** Architect
- **Status:** Not started
- **Scope:** `src/casare_rpa/application/dependency_injection/`
- **Acceptance criteria:** wiring is centralized; no hidden singletons outside approved infra lifecycles
- **Rollback:** keep legacy accessors behind adapters while migrating

---

# Epic 2 — Unified Design Tokens (Desktop + Dashboard)

## TOK-001 — Token contract ADR (names, scales, semantics)

- **Owner:** UI Specialist
- **Status:** Not started
- **Scope:** ADR + `docs/unified-system-spec.md` contract section
- **Acceptance criteria:** contract is approved and referenced from both UIs
- **Rollback:** keep existing Desktop tokens, postpone Dashboard unification

## TOK-002 — Token export: Desktop → Dashboard bridge (Phase 1)

- **Owner:** UI Specialist
- **Status:** Not started
- **Scope:** generator script + `monitoring-dashboard/` theme config
- **Acceptance criteria:** a token change propagates to both UIs via generation
- **Rollback:** freeze generator output and revert to manual Tailwind values temporarily

## TOK-003 — “No raw colors” enforcement (Desktop + Dashboard)

- **Owner:** Architect
- **Status:** Not started
- **Scope:** existing Desktop hook + new Dashboard lint rules
- **Acceptance criteria:** new violations fail CI; legacy is handled via incremental gates
- **Rollback:** warn-only mode for one sprint

---

# Epic 3 — Desktop Canvas UI Unification (finish v2, delete v1)

## DESK-001 — v1 → v2 migration inventory + execution tracker

- **Owner:** UI Specialist
- **Status:** Not started
- **Scope:** `docs/migration-registry.md` entries + per-feature checklist
- **Acceptance criteria:** all remaining v1 dependencies are listed and prioritized
- **Rollback:** none (tracking only)

## DESK-002 — Hot-path tests before removing bridges

- **Owner:** QA Specialist
- **Status:** Not started
- **Scope:** `tests/` (unit + UI smoke where feasible)
- **Acceptance criteria:** tests cover startup/open/save/execute/undo and prevent regressions
- **Rollback:** keep legacy bridges until stable

## DESK-003 — Remove v1 escape hatch after stable release window

- **Owner:** UI Specialist
- **Status:** Not started
- **Scope:** `src/casare_rpa/presentation/canvas/app.py` and v1 modules
- **Acceptance criteria:** Desktop runs without v1 imports; env flag removed
- **Rollback:** restore env flag in a revert PR

---

# Epic 4 — Monitoring Dashboard UI Modernization + Unification

## WEB-001 — Component primitives aligned to shared tokens

- **Owner:** UI Specialist
- **Status:** Not started
- **Scope:** `monitoring-dashboard/src/components/`
- **Acceptance criteria:** pages use primitives; consistent states (loading/error/empty)
- **Rollback:** migrate page-by-page; keep primitives optional temporarily

## WEB-002 — Data layer conventions (single client + react-query conventions)

- **Owner:** Architect
- **Status:** Not started
- **Scope:** `monitoring-dashboard/src/api/`, `hooks/`
- **Acceptance criteria:** no ad-hoc fetch; consistent error mapping
- **Rollback:** adapter wrapper around legacy calls

## WEB-003 — Visual regression strategy

- **Owner:** QA Specialist
- **Status:** Not started
- **Scope:** `monitoring-dashboard/` test tooling
- **Acceptance criteria:** baseline screenshots for key pages; diffs reviewed in PRs
- **Rollback:** manual-only snapshots (no CI enforcement) for one sprint

---

# Epic 5 — API Contract + Typed SDK (Orchestrator ↔ Dashboard)

## API-001 — Normalize API error envelope across routers

- **Owner:** Architect
- **Status:** Not started
- **Scope:** `src/casare_rpa/infrastructure/orchestrator/api/`
- **Acceptance criteria:** all routers emit the same error contract
- **Rollback:** per-router compatibility mapping

## API-002 — Generate TypeScript client/types from OpenAPI

- **Owner:** Integrations (Architect)
- **Status:** Not started
- **Scope:** backend OpenAPI + `monitoring-dashboard/`
- **Acceptance criteria:** dashboard builds using generated types; breaking changes caught
- **Rollback:** temporary “compat types” layer while migrating

## API-003 — WebSocket contract versioning + generated TS events

- **Owner:** Integrations (Architect)
- **Status:** Not started
- **Scope:** `docs/websocket-contract.md` + schema + TS generation
- **Acceptance criteria:** events are versioned and typed; contract tests cover compatibility
- **Rollback:** dual support for v1/v2 events temporarily

---

# Epic 6 — Node System Unification (schema-driven, test-driven)

## NODES-001 — Node modernization audit → actionable report

- **Owner:** Node Specialist
- **Status:** Not started
- **Scope:** `scripts/audit_node_modernization.py` outputs + backlog items
- **Acceptance criteria:** top offenders prioritized; target 98% modern
- **Rollback:** none (report only)

## NODES-002 — Automated node creation pipeline

- **Owner:** Node Specialist
- **Status:** Not started
- **Scope:** `scripts/` + templates + registry updates
- **Acceptance criteria:** generating a node produces schema, ports, tests, visual wrapper, registrations
- **Rollback:** keep manual creation as fallback

---

# Epic 7 — Execution Runtime + Reliability Unification

## RUN-001 — Unified cancellation/timeout strategy

- **Owner:** Architect
- **Status:** Not started
- **Scope:** `src/casare_rpa/application/use_cases/` + runtime infra
- **Acceptance criteria:** consistent cancellation behavior; no swallowed cancellations
- **Rollback:** feature flag per subsystem timeout policy

## RUN-002 — Normalize event emission (domain events vs legacy dict events)

- **Owner:** Architect
- **Status:** Not started
- **Scope:** execution controller/event bridge
- **Acceptance criteria:** single event contract; legacy adapter until migrated
- **Rollback:** keep legacy dict events behind adapter

---

# Epic 8 — Desktop Automation + Recording Unification

## AUTO-001 — Selector model standardization (desktop/browser)

- **Owner:** Node Specialist
- **Status:** Not started
- **Scope:** selector serialization + recorder output
- **Acceptance criteria:** selectors serialize uniformly and replay reliably
- **Rollback:** dual selector formats with adapter

---

# Epic 9 — Testing + CI/CD Unification (Python + Dashboard)

## CI-001 — Python gates in CI (lint/type/tests + key scripts)

- **Owner:** QA Specialist
- **Status:** Not started
- **Scope:** `.github/workflows/ci.yml`
- **Acceptance criteria:** CI runs fast unit suite and required scripts
- **Rollback:** split into required vs allow-fail jobs temporarily

## CI-002 — Dashboard gates in CI (install/lint/build)

- **Owner:** QA Specialist
- **Status:** Not started
- **Scope:** `.github/workflows/ci.yml`, `monitoring-dashboard/`
- **Acceptance criteria:** CI builds dashboard; lint/typecheck run
- **Rollback:** allow-fail dashboard job for one sprint

---

# Epic 10 — Deprecation + Cleanup

## CLEAN-001 — Remove committed `monitoring-dashboard/node_modules` going forward

- **Owner:** Architect
- **Status:** Not started
- **Scope:** repo hygiene + CI install via lockfile
- **Acceptance criteria:** `node_modules` not committed; CI uses `npm ci`
- **Rollback:** none (should not be needed)

## CLEAN-002 — Delete legacy Desktop UI v1 after cutover

- **Owner:** UI Specialist
- **Status:** Not started
- **Scope:** v1 modules removal + references cleanup
- **Acceptance criteria:** v1 code removed; no imports remain
- **Rollback:** restore from prior release tag if needed

---

# Sequencing (fastest path to visible impact)

1. **Week 1–2:** GOV-001..004 + ARCH-001..003 (safety rails + boundaries) + start TOK-001
2. **Week 2–6:** DESK-001..003 (Desktop v2 completion) in parallel with API-001..003 (contracts)
3. **Week 4–8:** WEB-001..003 once TOK-002 and API-002 foundations exist
4. **Week 6–12:** NODES/AUTO/RUN hardening, then CLEAN cleanups
