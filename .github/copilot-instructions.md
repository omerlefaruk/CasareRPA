# CasareRPA: AI Coding Agent Instructions

## Project Overview
- **CasareRPA** is a Windows RPA platform with a visual, node-based workflow editor.
- Follows **Clean Architecture** (Domain-Driven Design):
  - `domain/` (pure logic), `application/` (use cases), `infrastructure/` (adapters/resources), `presentation/` (UI), `nodes/` (automation logic).
- Major components: Canvas Designer (UI), Robot Agent (execution), Orchestrator API (FastAPI), Monitoring Dashboard (React/Vite).

## Key Developer Workflows
- **Run Canvas Designer:** `python manage.py canvas`
- **Run Robot Agent:** `python manage.py robot start`
- **Run Orchestrator API:** `python manage.py orchestrator start`
- **Run All Tests:** `pytest tests/ -v`
- **Build Installer:** `python installer/build_dev_installer.py`
- **Dashboard Dev Server:** `python manage.py dashboard`

## Project-Specific Conventions
- **Type hints required**; all I/O is async/await.
- **Ruff** for linting, **Black** for formatting.
- **Test structure:**
  - `tests/domain/`: pure logic, no mocks
  - `tests/application/`: mock infra, real domain
  - `tests/infrastructure/`: mock all external APIs
  - `tests/presentation/`: pytest-qt for Qt widgets
  - `tests/nodes/`: use category fixtures
- **Node instantiation:** Application layer must convert workflow dicts to node objects before execution (see integration test README).
- **UI:** All new components inherit from `BaseWidget` and use signal/slot patterns.
- **EventBus:** Used for decoupled communication between layers.

## Integration & Data Flow
- **Web automation:** Playwright; **Desktop:** UIAutomation.
- **Orchestrator API:** FastAPI REST/WebSocket, serves dashboard static files.
- **Dashboard:** Connects via REST/WebSocket to Orchestrator.
- **Database:** PostgreSQL for job queue and persistence.
- **Async:** All I/O is async-first (qasync for Qt).

## Patterns & Examples
- **Controller pattern:** MainWindow delegates to controllers.
- **Trigger system:** Registry-based (manual, scheduled, webhook, file, etc).
- **Testing:**
  - Mark async tests with `@pytest.mark.asyncio`.
  - Use `AsyncMock` for async dependencies.
  - Use fixtures from `tests/conftest.py` and category-specific conftests.
- **Installer:** Built with PyInstaller + Inno Setup; see `installer/README.md`.

## References
- [GEMINI.md](../GEMINI.md) — **Primary context for AI Agents** (Architecture & CLI)
- [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) — architecture details
- [tests/integration/README.md](../tests/integration/README.md) — integration test patterns & known gaps
- [src/casare_rpa/presentation/canvas/ui/README.md](../src/casare_rpa/presentation/canvas/ui/README.md) — UI component conventions
- [monitoring-dashboard/README.md](../monitoring-dashboard/README.md) — dashboard setup & API
- [installer/README.md](../installer/README.md) — installer build system
- [CLAUDE.md](../CLAUDE.md) — agent workflow & rules

## AI Agent Guidance
- **Reuse, don't reinvent:** Extend existing patterns, especially in `.brain/` if present.
- **Update `.brain/` and plans after major changes.**
- **Follow agent workflow:** explore → plan → architect → quality → reviewer (see CLAUDE.md).
- **Document unresolved questions at end of plans.**
- **For new nodes/features:** Always create plan in `.brain/plans/`.

---
For unclear or missing conventions, check referenced READMEs or ask for clarification.
