# CI Quality Gates (Python + Dashboard)

This document defines the required quality gates for merges. It is written as a target spec and includes a phased rollout strategy to avoid blocking the team on legacy debt.

## Principles

- Gates prevent *new* debt first (changed-files enforcement), then expand to the whole repo.
- Hot paths require tests before behavior refactors.
- CI must be deterministic and reasonably fast.

---

# 1) Python gates

## 1.1 Required checks (target)

### Lint + format

- `ruff check src/ tests/`
- `ruff format --check src/ tests/`

Note: the repo currently runs Black in CI; the target is to converge on Ruff formatting (to match `.pre-commit-config.yaml`) and remove duplicate formatters.

### Types

- Phase 1 (minimum): `mypy src/casare_rpa/domain`
- Phase 2 (expand): `mypy src/casare_rpa` (incremental strictness per package)

### Tests

- `pytest -m "unit"`
- Add a small “hot path smoke” subset as needed (API contracts, node registry, execution runtime).

## 1.2 Architecture + safety scripts (required)

Run key scripts in CI (not only pre-commit), at least:

- Domain purity: `python scripts/check_domain_purity.py`
- Application purity: `python scripts/check_application_purity.py`
- Presentation dependency direction: `python scripts/check_presentation_dependency_direction.py`
- Blocking I/O in async: `python scripts/check_blocking_io.py`
- HTTP client usage: `python scripts/check_http_client_usage.py`
- Node registry sync: `python scripts/check_node_registry_sync.py`
- Secrets scanning: `python scripts/check_secrets.py`
- Theme rules (Desktop): `python scripts/check_theme_colors.py` (see phased approach below)

## 1.3 Phased enforcement strategy

Because some scripts are incremental (e.g., `check_theme_colors.py` checks staged files), use a phased approach:

- **Phase A (now):** changed-files only enforcement in CI (no new violations).
- **Phase B:** expand to full-tree scanning after legacy debt is reduced.

---

# 2) Dashboard gates

## 2.1 Required checks (target)

In `monitoring-dashboard/`:

- Install: `npm ci`
- Typecheck + build: `npm run build` (already runs `tsc -b && vite build`)
- Lint: `npm run lint`

## 2.2 Design system enforcement (target)

Add rules that align with `docs/unified-system-spec.md`:

- Ban inline styles (with a documented escape hatch).
- Ban raw colors (hex) and raw palette utilities in app code; require semantic token utilities and primitives.

## 2.3 Repo hygiene gate

- `monitoring-dashboard/node_modules` must not be committed going forward.
- CI installs from lockfile only (`npm ci`).

---

# 3) GitHub Actions (recommended shape)

## 3.1 Python job

- Setup Python 3.12
- Install `pip install -e ".[dev]"`
- Run ruff, formatter check, mypy, unit tests
- Run required scripts (section 1.2)

## 3.2 Dashboard job

- Setup Node (pin LTS)
- `npm ci` in `monitoring-dashboard/`
- `npm run lint`
- `npm run build`

## 3.3 Optional jobs (phase-in)

- Contract tests: OpenAPI + WebSocket schema compatibility
- Visual regression for dashboard key pages
- Desktop UI smoke tests in CI only when stable (may require Xvfb)
