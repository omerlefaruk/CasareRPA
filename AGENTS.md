# CasareRPA Agent Guide (Canonical)

This file is the canonical agent guide for CasareRPA. CLAUDE.md and GEMINI.md are generated from AGENTS.md via `python scripts/sync_agent_guides.py` with tool-specific path rewrites. Remove AGENT.md.

Windows RPA platform | Python 3.12 | PySide6 | Playwright | DDD 2025 architecture | Reroute Stability 1.0 | Updated: 2025-12-25

## Recent Changes (2025-12-25)
- **OAuth Threading**: Fixed cross-event-loop singleton issue with `threading.Lock`
- **Vertex AI Routing**: Google OAuth now routes to Vertex AI endpoint (cloud-platform scope)
- **Vertex AI Auth**: Passing explicit `google.oauth2.credentials.Credentials` object to LiteLLM to support `vertex_ai/` models with OAuth token.
- **AI Performance**: Added manifest prewarm at startup, reduced verbose logging
- **Model Dropdown**: Updated with latest Gemini models (flash-lite, flash, 3-flash, 3-pro)

## Pre-commit and Quality Standards
The project strictly enforces architectural integrity and code quality via pre-commit hooks:
- **Node Registry**: All nodes must be registered in `src/casare_rpa/nodes/registry_data.py`.
- **Modern Typing**: Use built-in collection types (PEP 585) and union operators (PEP 604).
- **Theme Consistency**: Presentation layer must use `THEME` constants instead of hardcoded hex colors.
- **Async Safety**: Avoid blocking I/O in async contexts; use `await asyncio.sleep` and `anyio`.
- **Quality Fixes 2025**: Ongoing maintenance to resolve pre-commit hook violations including node registry sync, theme colors, signal/slot best practices, restored/modernized Profiler panel, tab navigation type hint fixes, and **default collapsed side/bottom panels**.
- **Signal/Slot**: All slots must be decorated with `@Slot()`; use `functools.partial` for captures.
- **Qt Lifetime Safety**: Guard delayed callbacks (eg `QTimer.singleShot`) against deleted widgets/objects.
- **Headless Stability**: Skip OpenGL setup and expensive visual effects when running with `QT_QPA_PLATFORM=offscreen`.
- **Node Collision Safety**: Use `_safe_create_property` and `has_property` checks to prevent redundant property creation.
- **Unused Imports**: Remove unused imports after changes (especially Qt types).
- **Cache Hydration**: Avoid eager visual node imports on cache hits; hydrate only missing mappings.
- **Test Isolation**: Only evict `casare_rpa` modules loaded outside the current worktree.

## Quick Commands
```bash
pip install -e ".[dev]"
pytest tests/ -v
pytest tests/nodes/ -v
pytest tests/domain/ -v
mypy src/casare_rpa
ruff check src/
black src/ tests/
python scripts/index_codebase.py
python scripts/chroma_search_mcp.py
python scripts/audit_node_modernization.py
python scripts/sync_agent_guides.py
python scripts/sync_claude_dir.py
python scripts/sync_agent_rules.py
python scripts/create_plan.py "feature-name"
python scripts/update_context_status.py --phase Plan --status "in progress"
python scripts/phase_report.py --phase Execute --in-progress "editing X"
python scripts/create_worktree.py "feature-branch"
python scripts/check_not_main_branch.py
python run.py
python manage.py canvas
```

## Tech Stack (Versions)
<tech-stack>
  <item name="Python" version=">=3.12" note="project requires" />
  <item name="PySide6" version=">=6.6.0" />
  <item name="PySide6-Addons" version=">=6.6.0" />
  <item name="NodeGraphQt" version=">=0.6.30" />
  <item name="Playwright" version=">=1.50.0" />
  <item name="FastAPI" version=">=0.109.0" />
  <item name="Uvicorn" version=">=0.27.0" />
  <item name="Pydantic" version=">=2.6.0" />
  <item name="Loguru" version=">=0.7.2" />
  <item name="ChromaDB" version=">=0.4.0" note="semantic search" />
  <item name="React" version="18.3.1" note="monitoring-dashboard/" />
  <item name="Vite" version="6.0.1" note="monitoring-dashboard/" />
  <item name="Tailwind" version="3.4.15" note="monitoring-dashboard/" />
</tech-stack>

## Project Structure (Key Paths)
```
src/casare_rpa/           # Domain, application, infrastructure, presentation, nodes
monitoring-dashboard/     # React/Vite monitoring UI
docs/                     # Developer, user, security, operations docs
scripts/                  # Tooling and audits
tests/                    # Unit/integration/e2e/perf tests
deploy/                   # Installers, migrations, infra helpers
config/                   # Settings, globals, projects
Projects/                 # Example projects/workflows
.agent/                   # Agent rules, commands, workflows (primary)
agent-rules/              # Legacy agent rules (still referenced)
.brain/                   # Knowledge base, context, plans
```

## Guide Variants
- AGENTS.md references `.agent/` paths.
- CLAUDE.md references `.claude/` paths.
- GEMINI.md mirrors AGENTS.md for non-Claude tools.

## Search Strategy (Semantic vs Exact)
Semantic (ChromaDB via MCP):
- Use `search_codebase("browser automation click", top_k=5)` for concepts and related patterns.
- First query ~800ms, follow-ups <100ms.
Commands:
- Index: `python scripts/index_codebase.py`
- MCP server: `python scripts/chroma_search_mcp.py`
Exact (ripgrep):
- Use `rg "ClassName"` or `rg "def execute" src/` for precise matches.
- Use `rg --files` for file discovery.
Decision flow:
- Unknown concept -> `search_codebase` then `rg`.
- Known symbol -> `rg` directly.
- Always read `_index.md` before wide grep (see `.agent/rules/01-core.md`).

## MCP Usage (Required)
Always use MCP servers when the task matches the capability:
- `filesystem`: file reads/writes and directory operations
- `git`: repository inspection and diffs
- `sequential-thinking`: complex reasoning or multi-step planning
- `exa`: web search and external research
- `ref`: API/library docs lookup
- `playwright`: browser automation investigations
- `codebase`: semantic search (`search_codebase`)

## Core Rules (Non-Negotiable)
- INDEX-FIRST: Read `_index.md` before grep/glob. See `.agent/rules/_index.md`, `.agent/rules/01-core.md`, `.agent/rules/01-workflow-default.md`, `src/casare_rpa/*/_index.md`, `docs/_index.md`.
- PARALLEL: Launch independent reads/searches in one block. See `.agent/rules/01-core.md`.
- INTERACTIVE STATUS: Always state current phase and progress (in progress/completed/next) and keep plans updated.
- CLAUDE MIRROR: Never edit the Claude mirror directly; keep it synced via `python scripts/sync_claude_dir.py`.
- DOCS COUPLING: If `src/` changes, update AGENTS.md and relevant `.agent/`, `.brain/`, `agent-rules/`, or `docs/` files. Enforced by `scripts/enforce_doc_updates.py`.
- WORKTREES ONLY: Never work on `main`/`master`. Create a worktree branch for every task.
- SEARCH BEFORE CREATE: Check existing nodes/registries first. See `.agent/rules/03-nodes.md`, `src/casare_rpa/nodes/_index.md`, `src/casare_rpa/nodes/registry_data.py`.
- NO SILENT FAILURES: Wrap external calls in try/except and log via loguru. See `.agent/rules/01-core.md`, `.agent/rules/02-coding-standards.md`.
- DOMAIN PURITY: Domain layer has no external deps or I/O. See `.agent/rules/06-enforcement.md`, `.brain/projectRules.md`, `src/casare_rpa/domain/`.
- ASYNC FIRST: No blocking I/O in async contexts; use qasync in Qt. See `.agent/rules/06-enforcement.md`, `.brain/projectRules.md`.
- HTTP: Use `UnifiedHttpClient`, never raw aiohttp/httpx. See `.agent/rules/01-core.md`, `.brain/projectRules.md`, `docs/developer-guide/internals/http-client.md`, `src/casare_rpa/infrastructure/http/`.
- THEME ONLY: No hardcoded hex colors; use Theme/THEME. See `.agent/rules/ui/theme-rules.md`, `.brain/docs/ui-standards.md`, `src/casare_rpa/presentation/canvas/ui/theme.py`, `src/casare_rpa/presentation/canvas/theme.py`.
- SIGNAL/SLOT: @Slot required; no lambdas; use functools.partial for captures; queued connection cross-thread. See `.agent/rules/ui/signal-slot-rules.md`.
- NODES: Use `@properties` + `get_parameter()` (auto-resolves), `get_raw_parameter()` for templates; no `self.config.get()` or manual `context.resolve_value()`. See `.agent/rules/03-nodes.md`, `.agent/rules/10-node-workflow.md`, `.agent/artifacts/concept3_variable_resolution.md`, `src/casare_rpa/domain/entities/base_node.py`.
- PORTS: Use `add_exec_input()`/`add_exec_output()` for exec ports; explicit `DataType` for data ports. See `.agent/rules/03-nodes.md`.
- EVENTS: Typed domain events only; publish via EventBus; pass serializable data. See `.agent/rules/12-ddd-events.md`, `src/casare_rpa/domain/events/`, `docs/developer-guide/architecture/events.md`.
- WAITING: No hardcoded sleeps; use Playwright waiters. See `agent-rules/rules/02-coding-standards.md`, `docs/user-guide/guides/best-practices.md`.
- SECURITY: Never hardcode secrets; use env/credential store. See `docs/security/best-practices.md`, `docs/security/credentials.md`.

## Agent Workflow and Output
- 5-phase workflow: Research -> Plan -> Execute -> Validate -> Docs. See `.agent/rules/01-workflow-default.md`, `.agent/workflows/opencode_lifecycle.md`.
- For complex tasks, create/update plans in `.brain/plans/` and update `.brain/context/current.md`. See `.agent/rules/09-brain-protocol.md`, `.brain/_index.md`.
- Always plan for non-trivial tasks, then review/confirm the plan with the user before execution.
- Before implementation, re-read the relevant rules/design docs and cite the files being followed.
- During work, report the current phase and what is in progress/completed/next; keep plans updated.
- Always perform a self code review and QA (tests/verification) before docs; if not run, state why.
- Explicit flow: Plan -> Review Plan -> Tests First -> Implement -> Code Review -> QA -> Docs.
- RULE UPDATES: If a new problem is solved or a new reusable pattern emerges, update this canonical guide and any relevant `.agent/`, `.brain/`, `agent-rules/`, or `docs/` files in the same change.
- Output style: concise, no time estimates, auto-add missing imports. See `.agent/rules/02-coding-standards.md`, `.brain/projectRules.md`.
- Do not commit unless explicitly asked. See `.agent/rules/01-core.md`.

## Subagents (Required)
- RESEARCH: `explore` + `researcher`
- PLAN: `architect`
- REVIEW PLAN: `reviewer`
- TESTS FIRST: `quality`
- IMPLEMENT: `builder` / `ui` / `integrations` / `refactor`
- CODE REVIEW: `reviewer`
- QA: `quality`
- DOCS: `docs`

## Feature Lifecycle (Mandatory)
Plan -> Review Plan -> Tests First -> Implement -> Code Review -> QA -> Docs.
If any errors or review issues appear, loop back to the appropriate step until clean.

## Git Workflow (Worktrees)
- Always create a worktree branch; never work on `main`/`master`.
- Create: `python scripts/create_worktree.py "feature-name"`
- Manual: `git worktree add .worktrees/feature-name -b feature-name main`
- Guardrail: `python scripts/check_not_main_branch.py`

## Boundaries (Never)
- Never work directly on `main`/`master` or commit from it.
- Never run destructive commands (e.g., `git reset --hard`, `git checkout --`, `rm -rf`) without explicit approval.
- Never commit secrets, tokens, or credentials.
- Never bypass security rules, lint failures, or failing tests silently.
- Never introduce infrastructure or UI dependencies into the domain layer.
- Never disable logging/error handling for external calls.

## Token-Friendly Docs
- Keep rules concise and avoid duplicate statements.
- Prefer tables and short lists over long prose.
- Use XML blocks for repeated structured data when it reduces tokens.

## Coding Standards (Python)
- Type hints required for public APIs; use `Optional[T]` and `Dict[K, V]`. See `.agent/rules/02-coding-standards.md`, `.brain/projectRules.md`.
- Line length 100; import order: stdlib -> third-party -> local. See `.agent/rules/02-coding-standards.md`, `.brain/projectRules.md`.
- Ruff for linting; Black for formatting. See `pyproject.toml`, `.agent/rules/02-coding-standards.md`.

## Code Style Examples (Good/Bad)
Type hints:
```python
# GOOD
def get_robot(robot_id: str) -> Optional[Robot]:
    ...

# BAD
def get_robot(id):
    ...
```

Error handling + logging:
```python
# GOOD
try:
    result = await client.get(url)
except Exception as exc:
    logger.error(f"HTTP failed for {url}: {exc}")
    raise

# BAD
result = await client.get(url)
```

Node parameters:
```python
# GOOD
timeout = self.get_parameter("timeout", 30000)

# BAD
timeout = self.config.get("timeout", 30000)
```

Theme usage:
```python
# GOOD
widget.setStyleSheet(f"color: {THEME.text_primary};")

# BAD
widget.setStyleSheet("color: #ffffff;")
```

## DDD 2025 Architecture
Layers:
| Layer | Path | Dependencies |
| Domain | `src/casare_rpa/domain/` | None |
| Application | `src/casare_rpa/application/` | Domain |
| Infrastructure | `src/casare_rpa/infrastructure/` | Domain, Application interfaces |
| Presentation | `src/casare_rpa/presentation/` | Application |

Key patterns (see `.agent/rules/02-architecture.md`, `.brain/systemPatterns.md`, `docs/developer-guide/architecture/index.md`):
- EventBus: `src/casare_rpa/domain/events.py`
- Typed events: `src/casare_rpa/domain/events/`
- Aggregates: `src/casare_rpa/domain/aggregates/`
- Unit of Work: `src/casare_rpa/infrastructure/persistence/unit_of_work.py`
- CQRS queries: `src/casare_rpa/application/queries/`
- Qt event bridge: `src/casare_rpa/presentation/canvas/coordinators/event_bridge.py`
- Domain interfaces: `src/casare_rpa/domain/interfaces/` (Application depends on these, Infrastructure implements)

Three apps:
- Canvas (Designer): `src/casare_rpa/presentation/canvas/`
- Robot (Executor): `src/casare_rpa/infrastructure/robot/`
- Orchestrator (Manager): `src/casare_rpa/infrastructure/orchestrator/`

Typed events quick reference:
```python
from casare_rpa.domain.events import NodeCompleted, get_event_bus
bus = get_event_bus()
bus.subscribe(NodeCompleted, handler)
bus.publish(NodeCompleted(node_id="x", node_type="Y", workflow_id="wf1", execution_time_ms=100))
```

## Node Development (Modern Node Standard 2025)
Schema-driven logic (see `.agent/rules/03-nodes.md`, `.agent/rules/10-node-workflow.md`, `.brain/docs/node-templates.md`):
```python
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import DataType

@properties(
    PropertyDef("url", PropertyType.STRING, required=True),
    PropertyDef("timeout", PropertyType.INTEGER, default=30000),
)
@node(category="browser")
class MyNode(BaseNode):
    def _define_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_input_port("url", DataType.STRING)
        self.add_output_port("result", DataType.STRING)

    async def execute(self, context) -> dict:
        url = self.get_parameter("url")
        timeout = self.get_parameter("timeout", 30000)
        raw = self.get_raw_parameter("url")
        ...
```

Registration (see `.agent/rules/nodes/node-registration.md`, `.brain/docs/node-checklist.md`):
1. Export in `src/casare_rpa/nodes/<category>/__init__.py`
2. Register in `src/casare_rpa/nodes/registry_data.py`
3. Add to `NODE_TYPE_MAP` in `src/casare_rpa/utils/workflow/workflow_loader.py`
4. Create visual node in `src/casare_rpa/presentation/canvas/visual_nodes/<category>/`
5. Register in `src/casare_rpa/presentation/canvas/visual_nodes/__init__.py`

Notes:
- Browser nodes extend `BrowserBaseNode` in `src/casare_rpa/nodes/browser/browser_base.py` (see `.brain/systemPatterns.md`).
- Do not duplicate auto-generated property widgets in visual nodes; use `_replace_widget()` only for custom widgets. See `.agent/rules/nodes/node-registration.md`, `.brain/docs/widget-rules.md`.
- Audit modernization: `python scripts/audit_node_modernization.py` (target 98%+).

## UI and Qt Rules
- Theme: use Theme/THEME constants, no hardcoded colors. See `.agent/rules/ui/theme-rules.md`, `.brain/docs/ui-standards.md`.
- Dialogs: use `dialog_styles.py` helpers, not `QMessageBox.*` static methods. See `.brain/docs/ui-standards.md`, `src/casare_rpa/presentation/canvas/ui/dialogs/dialog_styles.py`.
- Signal/slot: @Slot required; no lambdas; use partial; queued connection cross-thread. See `.agent/rules/ui/signal-slot-rules.md`.
- MainWindow delegation: use `SignalCoordinator` and `PanelManager`. See `.brain/docs/ui-standards.md`, `src/casare_rpa/presentation/canvas/coordinators/signal_coordinator.py`, `src/casare_rpa/presentation/canvas/managers/panel_manager.py`.
- File path properties: replace auto widgets with `NodeFilePathWidget`/`NodeDirectoryPathWidget` and `_replace_widget()`. See `.brain/docs/widget-rules.md`, `src/casare_rpa/presentation/canvas/graph/node_widgets.py`.

## Testing
- Use pytest with fixtures in `tests/conftest.py`. See `.brain/systemPatterns.md`, `.brain/projectRules.md`, `docs/developer-guide/contributing/testing.md`.
- Domain tests: no mocks (`tests/domain/`). Application tests: mock infrastructure. Presentation tests: mock heavy Qt pieces. See `.brain/systemPatterns.md`.
- Headless Qt tests: `QT_QPA_PLATFORM=offscreen` is set in `tests/conftest.py` (see `.agent/artifacts/baseline_test_report.md`).

## Triggers
- Trigger types: manual, schedule, event, API. See `.agent/rules/05-triggers.md`, `.brain/docs/trigger-checklist.md`, `docs/user-guide/core-concepts/triggers.md`.

## Key Indexes (P0)
- `src/casare_rpa/nodes/_index.md`
- `src/casare_rpa/nodes/workflow/subflow_io.py`
- `src/casare_rpa/presentation/canvas/visual_nodes/_index.md`
- `src/casare_rpa/presentation/canvas/visual_nodes/subflows/io_nodes.py`
- `src/casare_rpa/domain/_index.md`
- `src/casare_rpa/presentation/canvas/_index.md`
- `src/casare_rpa/application/_index.md`
- `src/casare_rpa/infrastructure/_index.md`
- `.brain/_index.md`
- `.agent/rules/01-core.md`

## Knowledge Base and Docs
- Brain: `.brain/projectRules.md`, `.brain/systemPatterns.md`, `.brain/errors.md`, `.brain/dependencies.md`, `.brain/docs/_index.md`
- Agent rules: `.agent/rules/`, `.agent/agents/_index.md`, `.agent/skills/_index.md`, `.agent/commands/_index.md`
- Legacy agent rules: `agent-rules/_index.md` (still referenced by some tooling)
- Docs: `docs/index.md`, `docs/developer-guide/index.md`, `docs/user-guide/index.md`, `docs/security/index.md`, `docs/operations/index.md`

## MCP Servers
- Config: `.mcp.json` (see `.agent/rules/07-tools.md`)
- Core local servers: `filesystem`, `git`, `sequential-thinking`, `codebase`
- Optional external-context servers: `exa`, `ref`, `playwright` (when configured)

## Commit Message Format
```
<type>: <short description>

Types: feat, fix, refactor, test, docs, chore
```
