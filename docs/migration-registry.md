# Migration Registry

This registry tracks all incremental migrations and legacy deprecations. It is the single view of “what is migrated”, “what remains”, and “who owns it”.

## Rules

- Every migration has: **owner**, **target state**, **status**, **ETA**, **quality gates**, **rollback strategy**.
- If a migration introduces a temporary compatibility layer, it must also include a **removal task** with a deadline.

## Status legend

- **Not started**
- **In progress**
- **Blocked**
- **Done**

---

# Current Registry (initial snapshot)

| Area | Legacy / Problem | Target | Status | Flag / Adapter | Owner | ETA | Quality gates | Rollback |
|---|---|---|---|---|---|---|---|---|
| Desktop window | `MainWindow` v1 | `NewMainWindow` v2 only | In progress | `CASARE_UI_V1` escape hatch | UI Specialist | Week 6 + 1 stable release | UI smoke tests for hot paths | restore flag |
| Desktop theme/tokens | legacy token naming drift | Design System 2025 (`theme`) | In progress | mapping table as needed | UI Specialist | Week 3 | `scripts/check_theme_colors.py` | keep aliases |
| Desktop icons | legacy/fallback icon paths | single icon pipeline | Not started | adapters in UI only | UI Specialist | Week 5 | snapshot checks, visual QA | revert adapter |
| Dashboard tokens | `tailwind.config.js` hardcoded palette | generated semantic tokens | Not started | generator output | UI Specialist | Week 4 | lint bans raw colors | freeze generator output |
| Dashboard components | one-off page styling | primitives + templates | Not started | page-by-page migration | UI Specialist | Week 8 | lint bans inline styles | keep legacy pages |
| Dashboard linting | ESLint config missing | enforce rules + conventions | Not started | n/a | QA Specialist | Week 3 | `npm run lint` in CI | allow-fail temporarily |
| Backend API errors | per-router variations | unified error envelope | Not started | compat response adapter | Architect | Week 4 | contract tests | per-router fallback |
| OpenAPI → TS | hand-rolled TS types | generated client/types | Not started | compat types layer | Architect | Week 6 | build fails on drift | keep old types temporarily |
| WebSocket events | doc-only drift risk | versioned schema + TS gen | Not started | dual event versions | Architect | Week 6 | contract tests | support v1+v2 |
| Architecture boundaries | partially enforced | CI enforced (domain/app/pres) | In progress | allowlists + incremental scripts | Architect | Week 2 | boundary scripts in CI | changed-files mode |
| Workflow validation | domain imported presentation | workflow validation stays in presentation | Done | n/a | Architect | Week 2 | unit tests | restore previous validators |
| Application storage use cases | application imported infra storages | domain storage interfaces + DI-resolved storages | Done | DI keys: `folder_storage`, `environment_storage`, `template_storage` | Architect | Week 2 | ruff + unit tests | revert use-case constructors and DI keys |
| Application execution use cases | application imported infra cache/LLM/manifest | domain ports + DI-resolved adapters | Done | DI keys: `cache_manager`, `cache_key_generator`, `llm_manager`, `node_manifest_provider` | Architect | Week 2 | `python scripts/check_application_purity.py` + unit tests | revert to direct imports |
| Orchestrator use-case repos | application imported infra repositories | domain orchestrator repository interfaces | In progress | new domain interfaces for workflow assignments + node overrides | Architect | Week 3 | ruff + unit tests | revert imports to infra repositories |
| Node system | modernization drift | 98%+ modern standard | Not started | generator + audits | Node Specialist | Week 10 | modernization audit | none |
| Repo hygiene | committed `monitoring-dashboard/node_modules` | lockfile-only installs | Not started | n/a | Architect | Week 10 | CI uses `npm ci` | none |

---

# How to update this registry

- Add a new row when you introduce a new migration or compatibility adapter.
- Update status/ETA weekly.
- Link migrations to tasks in `plans/refactor-program-backlog.md`.

