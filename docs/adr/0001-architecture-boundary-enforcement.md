# ADR 0001: Architecture Boundary Enforcement

**Status:** Accepted
**Date:** 2025-12-30
**Context:** Refactor Program - Phase 1 (GOV-001, ARCH-001, ARCH-002, ARCH-003)
**Related:** [docs/unified-system-spec.md](../unified-system-spec.md), [docs/refactor-program.md](../refactor-program.md)

---

## Context

CasareRPA follows Clean Architecture principles with four distinct layers:

```
┌─────────────────────────────────────────────────────────┐
│  Presentation (UI)                                       │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Application (Use Cases, Orchestration)         │   │
│  │  ┌─────────────────────────────────────────┐   │   │
│  │  │  Domain (Business Logic, Entities)      │   │   │
│  │  │  - No external dependencies             │   │   │
│  │  │  - Pure Python, framework-agnostic      │   │   │
│  │  └─────────────────────────────────────────┘   │   │
│  │                                                  │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Infrastructure (Frameworks, Adapters) ◄──────────────┘
│  (implements interfaces defined by inner layers)
└─────────────────────────────────────────────────────────┘
```

**Dependency Rule:** Dependencies must point **inward** only. Inner layers never depend on outer layers.

### Problem

Prior to this ADR, architecture boundaries were documented but not enforced. This led to:
- **Domain violations:** External imports (`casare_rpa.infrastructure`, `PySide6`) in domain layer
- **Application violations:** Direct imports from infrastructure/presentation in application layer
- **Presentation violations:** Direct infrastructure imports bypassing application layer

These violations created tight coupling, made testing difficult, and violated the core principle of Clean Architecture.

---

## Decision

Enforce architecture boundaries through automated scripts that run in:
1. **Pre-commit hooks** - Catch violations before commit
2. **CI pipeline** - Block PRs with violations
3. **Manual KPI tracking** - Measure progress over time

### Enforcement Scripts

| Script | Layer | Rule | Exit Code |
|--------|-------|------|-----------|
| `check_domain_purity.py` | Domain | No imports from `infrastructure`, `presentation`, `nodes`, external frameworks | 1 |
| `check_application_purity.py` | Application | Only import from `domain` (no `infrastructure`, `presentation`, `nodes`) | 1 |
| `check_presentation_dependency_direction.py` | Presentation | No direct `infrastructure` imports (use `application` ports) | 1 |

### CI Integration

Updated `.github/workflows/ci.yml` to run architecture checks before standard linting:

```yaml
# Architecture boundary enforcement (GOV-001, ARCH-001, ARCH-002, ARCH-003)
- name: Enforce domain purity (no external deps)
  run: python scripts/check_domain_purity.py

- name: Enforce application purity (only imports from domain)
  run: python scripts/check_application_purity.py

- name: Enforce presentation dependency direction (no direct infra imports)
  run: python scripts/check_presentation_dependency_direction.py
```

### Pre-commit Integration

Updated `.pre-commit-config.yaml` to run on every commit:

```yaml
- id: application-purity
  name: Enforce application layer purity (only imports from domain)
  entry: python scripts/check_application_purity.py

- id: presentation-dependency-direction
  name: Enforce presentation dependency direction (no direct infra imports)
  entry: python scripts/check_presentation_dependency_direction.py
```

### KPI Tracking

`scripts/measure_kpi_baselines.py` measures:
- Boundary violation counts (domain, application, presentation)
- Lint/type error counts
- Bundle size
- Test runtime

Output format: JSON for tracking deltas over time.

---

## Consequences

### Positive

- **Automated enforcement** prevents new violations
- **Fast feedback** via pre-commit hooks (catch before push)
- **CI gates** block PRs that introduce violations
- **KPI tracking** enables measurement of refactor progress
- **Clear error messages** guide developers to correct patterns

### Negative

- **Pre-commit overhead** adds ~2-5 seconds to commit time
- **Migration work** required to fix existing violations
- **Exclusions needed** for legitimate edge cases (composition roots, TYPE_CHECKING blocks)

### Mitigations

- **Incremental enforcement:** Start with warnings, migrate to errors
- **Explicit exclusions:** Document and minimize allowed exceptions
- **KPI baselines:** Track reduction in violations over time

---

## Migration Plan

### Phase 1: Baseline (Week 1)
- [x] Create enforcement scripts
- [x] Add to CI with non-blocking status (warnings only)
- [x] Measure baseline violation counts
- [x] Document this ADR

### Phase 2: Fix Critical Violations (Week 2-3)
- [ ] Fix domain layer violations (highest priority)
- [ ] Fix application layer violations
- [ ] Update pre-commit hooks to blocking

### Phase 3: Fix Presentation Violations (Week 4-6)
- [ ] Refactor direct infrastructure imports to use application ports
- [ ] Enable CI blocking on all checks

### Phase 4: Monitoring (Ongoing)
- [ ] Track violation reduction via KPI baselines
- [ ] Update migration registry with progress

---

## Rollback Plan

If enforcement causes significant developer friction:

1. **Immediate:** Disable CI blocking (change exit code handling)
2. **Short-term:** Add specific file exclusions to scripts
3. **Long-term:** Revisit ADR and adjust rules

Rollback command:
```bash
# Temporarily disable architecture checks in CI
git revert <commit-that-added-checks>
```

---

## Alternatives Considered

### Alternative 1: Manual Code Review
**Pros:** No tooling overhead, human judgment
**Cons:** Slow, error-prone, inconsistent, doesn't scale
**Decision:** Automated enforcement chosen for consistency

### Alternative 2: Runtime Import Hooks
**Pros:** Catches violations at runtime
**Cons:** Only catches executed code, performance overhead
**Decision:** Static analysis chosen for comprehensive coverage

### Alternative 3: Monorepo with Separate Packages
**Pros:** Physical separation enforces boundaries
**Cons:** Complex setup, slower iteration, tooling overhead
**Decision:** Single repo with static analysis chosen for simplicity

---

## References

- [docs/unified-system-spec.md](../unified-system-spec.md) - Target architecture
- [docs/refactor-program.md](../refactor-program.md) - Governance and process
- [docs/migration-registry.md](../migration-registry.md) - Migration tracking
- [plans/refactor-program-backlog.md](../plans/refactor-program-backlog.md) - Detailed tasks

---

**Next ADR:** [0002-domain-event-serialization](0002-domain-event-serialization.md) (proposed)
