# Unified System Spec (Target)

This document defines the target “golden paths” and non-negotiable rules for CasareRPA’s unified Python system and unified design system (Desktop Canvas + Monitoring Dashboard).

It is intentionally prescriptive: when in doubt, follow this spec over legacy patterns.

## Scope

- **Python system:** `src/casare_rpa/{domain,application,infrastructure,presentation}/`
- **Desktop Canvas (PySide6):** `src/casare_rpa/presentation/canvas/`
- **Monitoring Dashboard (React/Vite/Tailwind):** `monitoring-dashboard/`

## Goals

- Enforce Clean Architecture boundaries automatically.
- Provide one obvious “how to do X” for cross-cutting concerns (HTTP, config, logging, errors, DI, async lifecycle).
- Unify UI/UX using a single design token contract and shared component primitives.
- Migrate incrementally (strangler), with quality gates and rollback paths.

---

# 1) Architecture Rules (Python)

## 1.1 Layer dependency direction (hard rule)

| Layer | Path | May import | Must not import |
|---|---|---|---|
| Domain | `src/casare_rpa/domain/` | `domain` (+ stdlib) | `application`, `infrastructure`, `presentation`, any framework/IO libs |
| Application | `src/casare_rpa/application/` | `domain` (+ stdlib) | `infrastructure`, `presentation` |
| Infrastructure | `src/casare_rpa/infrastructure/` | `domain`, `application` | `presentation` |
| Presentation | `src/casare_rpa/presentation/` | `application` (and optionally `domain` for *types only*) | direct `infrastructure` imports (use application ports/DI) |

**Important:** the repository has legacy exceptions today; the target is to eliminate them via the migration registry (see `docs/migration-registry.md`).

## 1.2 Domain purity (hard rule)

Domain code must be:

- **Framework-agnostic:** no `PySide6`, `fastapi`, `playwright`, `aiohttp/httpx`, etc.
- **No I/O:** no file/network/db access, no environment reads, no clocks except through injected time providers.
- **No globals / singletons** that hide dependencies.
- **Explicit errors:** domain errors are typed, stable, and serializable where needed.

Reference: `src/casare_rpa/domain/_index.md`.

## 1.3 Application responsibilities (hard rule)

Application layer owns:

- Use cases and orchestration around domain operations.
- Ports as `Protocol`s (what infrastructure must implement).
- Transaction boundaries and coordination (UoW, event dispatch, retries as *policy*, not as IO).

Application must not:

- Import infrastructure or presentation modules.
- Perform framework I/O directly (HTTP/db/filesystem/UI).

Reference: `src/casare_rpa/application/_index.md`.

## 1.4 Infrastructure responsibilities (hard rule)

Infrastructure layer owns:

- Implementations of application/domain ports using frameworks.
- Resilience patterns (retries, circuit breakers) around external I/O.
- Adapters for external services, persistence, realtime, browser automation, etc.

Infrastructure must not import presentation.

Reference: `src/casare_rpa/infrastructure/_index.md`.

## 1.5 Presentation responsibilities (target rule)

Presentation layer owns:

- UI composition, state, and user interaction.
- Mapping UI events → application use cases.
- Rendering domain/application state.

Presentation must not:

- Call infrastructure directly (no `from casare_rpa.infrastructure...` in UI code).
- Define its own config/logging/error conventions.

**Migration stance:** if presentation currently imports infrastructure in hot paths, introduce a compatibility adapter in application (port + default infra implementation) and migrate call sites incrementally.

---

# 2) Golden Paths (Python)

## 2.1 HTTP (outbound)

**Single mandatory client:** `src/casare_rpa/infrastructure/http/unified_http_client.py`

- Do not use raw `aiohttp` / `httpx` for ordinary requests.
- Exceptions must be explicitly documented (e.g., streaming/SSE where the unified client is not suitable).

## 2.2 Config

**Single config API:** `src/casare_rpa/config/loader.py` (+ `src/casare_rpa/config/startup.py`)

Rules:

- No `os.environ.get()` outside `src/casare_rpa/config/`.
- Prefer typed config objects over dicts.
- Define configuration precedence: env > config file > defaults.

## 2.3 Logging + correlation

**Single logger:** loguru (configured in one place).

- Configure once: `src/casare_rpa/config/logging_setup.py`.
- Bind correlation context (request ID, job ID, workflow run ID) near entrypoints/middleware.
- Never use `print()` in infrastructure/nodes (enforced by hooks).

## 2.4 Errors + Result

Target:

- Domain owns the stable error contract and result types:
  - `src/casare_rpa/domain/errors/`
  - `src/casare_rpa/domain/errors/result.py`
- Application returns typed failures (or `Result`) rather than framework exceptions.
- Infrastructure/presentation map errors to transport-specific shapes:
  - FastAPI: `src/casare_rpa/infrastructure/orchestrator/api/responses.py`
  - Desktop: consistent dialog/toast mapping (no ad-hoc message boxes).

## 2.5 Dependency Injection (DI)

Target:

- All wiring lives under `src/casare_rpa/application/dependency_injection/`.
- Composition roots (CLI entrypoints, FastAPI app factory, Desktop app bootstrap) construct the container and pass dependencies downward.
- No implicit runtime singletons except explicitly approved ones (e.g., pooled HTTP client) and they must have lifecycle management.

## 2.6 Async + cancellation

Target:

- Cancellation-first: `asyncio.CancelledError` propagates (do not swallow).
- Standard timeout strategy across node execution, browser automation, orchestrator jobs.
- No blocking I/O inside `async def` (enforced via the existing hook).

## 2.7 Cache + keying

Target:

- Application uses domain ports: `ICacheManager` and `ICacheKeyGenerator` (no direct imports from `infrastructure.cache`).
- Default deterministic keying lives in domain: `src/casare_rpa/domain/services/cache_keys.py` (`StableCacheKeyGenerator`).
- Infrastructure may provide tiered implementations and register them via DI keys (`cache_manager`, `cache_key_generator`).

## 2.8 AI / LLM ports

Target:

- Application depends on domain ports only: `ILLMManager` + `INodeManifestProvider`.
- Infrastructure provides implementations via DI (`llm_manager`, `node_manifest_provider`).
- No LLM or registry dumping imports in application modules (enforced by application purity checks).

---

# 3) Unified Design System Spec (Desktop + Dashboard)

## 3.1 Token contract (semantic-first)

Tokens must be semantic, stable, and product-facing:

- **Background:** `bg.canvas`, `bg.surface`, `bg.elevated`
- **Text:** `text.primary`, `text.secondary`, `text.muted`, `text.disabled`
- **Brand:** `brand.primary`, `brand.secondary`
- **Status:** `status.success`, `status.warning`, `status.error`, `status.info`
- **Sizing:** spacing (4px base), radii, typography scale, z-index, shadows, transitions

Reference implementation exists today in Desktop:

- `src/casare_rpa/presentation/canvas/theme/`
- `.brain/docs/design-system-2025.md`

## 3.2 Desktop Canvas rules (hard rule)

- No hardcoded hex colors (`"#..."`) in `src/casare_rpa/presentation/` except token/theme definitions.
- Use only `THEME.*` and `TOKENS.*`:
  - `from casare_rpa.presentation.canvas.theme import THEME, TOKENS`
- QSS must be generated via theme (do not embed random QSS snippets with raw colors).

Enforcement hook: `scripts/check_theme_colors.py` (currently staged-files incremental).

## 3.3 Dashboard rules (hard rule)

- No inline `style={...}` except for documented, unavoidable cases (must be lint-suppressed with an explanation).
- No ad-hoc color usage (raw hex, or raw Tailwind palette classes like `text-blue-500`) in app code; use semantic token utilities and component primitives.
- Components must be built from a small primitives library (Button, Card, Table, Input, Modal, etc.) wired to tokens.

## 3.4 Single source of truth (strangler migration)

Target end-state:

- One canonical token file (recommended: `design-tokens/tokens.json`).
- Codegen outputs:
  - Desktop: Python token/theme modules + QSS artifacts.
  - Dashboard: CSS variables + Tailwind theme extension + typed token access.

Transition plan (no big-bang):

1. Treat Desktop `theme` as canonical (already close to “Design System 2025”).
2. Introduce token export generation for the dashboard (no manual duplication).
3. Move canonical source to `design-tokens/tokens.json` once generation is stable.

---

# 4) Strangler Migration Rules

## 4.1 Feature flags and compatibility adapters

Use:

- Feature flags for UI switches and behavior changes (remove after a stable release window).
- Compatibility adapters when the target contract differs from legacy (adapters live in application/infrastructure, not domain).

## 4.2 Migration registry (mandatory)

Every migration has:

- Owner
- Scope and target state
- Current status (Not started / In progress / Done)
- Quality gate(s)
- Rollback plan

See `docs/migration-registry.md`.

---

# 5) Enforcement (Quality Gates)

## 5.1 Existing enforcement hooks (today)

- Domain purity: `scripts/check_domain_purity.py`
- Theme “no raw hex”: `scripts/check_theme_colors.py`
- Node registry sync / modernization audits: see `.pre-commit-config.yaml`

## 5.2 Target enforcement (near-term)

- Add “application purity” (application must not import infrastructure/presentation).
- Add “presentation direction” (presentation must not import infrastructure directly).
- Run key scripts in CI, not just in pre-commit/staged mode.

See `docs/ci-quality-gates.md`.
