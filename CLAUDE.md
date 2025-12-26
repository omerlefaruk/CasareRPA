# CasareRPA Agent Guide (Canonical)

Windows RPA platform | Python 3.12 | PySide6 | Playwright | DDD 2025 architecture

**Note**: CLAUDE.md is generated from AGENTS.md via `python scripts/sync_agent_guides.py`. Edit AGENTS.md, not this file.

## Quick Commands

```bash
# Development
pip install -e ".[dev]"
pytest tests/ -v
mypy src/casare_rpa
ruff check src/
black src/ tests/

# Scripts
python scripts/create_worktree.py "feature-branch"
python scripts/sync_agent_guides.py
python scripts/audit_node_modernization.py

# Run
python run.py
python manage.py canvas
```

## Tech Stack

- Python >=3.12, PySide6 >=6.6, Playwright >=1.50, FastAPI, Pydantic, Loguru
- See `pyproject.toml` for full dependencies

## Project Structure

```
src/casare_rpa/           # Domain, application, infrastructure, presentation, nodes
monitoring-dashboard/     # React/Vite monitoring UI
docs/                     # Documentation
scripts/                  # Tooling and audits
tests/                    # Tests
.claude/                   # Rules, commands, workflows (primary)
.brain/                   # Knowledge base, context, plans
```

## Core Rules (Non-Negotiable)

| Rule | Reference |
|------|-----------|
| INDEX-FIRST | `.claude/rules/01-core.md` |
| PARALLEL | `.claude/rules/01-core.md` |
| WORKTREES ONLY | `.claude/rules/01-core.md` |
| NO SILENT FAILURES | `.claude/rules/01-core.md` |
| DOMAIN PURITY | `.claude/rules/06-enforcement.md` |
| ASYNC FIRST | `.claude/rules/06-enforcement.md` |
| HTTP (UnifiedHttpClient) | `.claude/rules/01-core.md` |
| THEME ONLY | `.claude/rules/ui/theme-rules.md` |
| POPUP (PopupManager) | `.claude/rules/ui/popup-rules.md` |
| SIGNAL/SLOT (@Slot) | `.claude/rules/ui/signal-slot-rules.md` |
| NODES (@properties) | `.claude/rules/03-nodes.md` |
| EVENTS (Typed) | `.claude/rules/12-ddd-events.md` |
| TESTING (pytest) | `.claude/rules/testing-standards.md` |

## 5-Phase Workflow

**PRE-CHECK → RESEARCH → PLAN → EXECUTE → VALIDATE → DOCS**

1. **PRE-CHECK**: Create worktree (never work on main)
2. **RESEARCH**: Read `_index.md` files, check existing patterns
3. **PLAN**: Create plan in `.brain/plans/`, get approval
4. **EXECUTE**: Tests first, implement, code review
5. **VALIDATE**: Run tests, verify no regressions
6. **DOCS**: Update relevant docs (skip for small fixes)

See `.claude/rules/01-workflow-default.md` for full workflow.

## Subagents

| Phase | Agent |
|-------|-------|
| RESEARCH | `explore` + `researcher` |
| PLAN | `architect` |
| REVIEW PLAN | `reviewer` |
| TESTS FIRST | `quality` |
| IMPLEMENT | `builder` / `ui` / `integrations` / `refactor` |
| CODE REVIEW | `reviewer` |
| QA | `quality` |
| DOCS | `docs` |

## Git Workflow (Worktrees)

```bash
# Create worktree for feature work
python scripts/create_worktree.py "feature-name"

# Manual creation
git worktree add .worktrees/feature-name -b feature-name main

# After merge, prune worktree
git worktree remove ".worktrees/feature-name"
git branch -D feature-name
```

## Search Strategy

- **Semantic**: `search_codebase("concept", top_k=5)` via MCP ChromaDB
- **Exact**: `rg "ClassName"` or `rg "def execute" src/`
- **Decision**: Unknown concept → semantic search; known symbol → ripgrep

## MCP Servers

Always use when task matches capability:
- `filesystem` - file operations
- `git` - repository operations
- `codebase` - semantic search
- `exa` - web research
- `ref` - API docs

## Key Indexes (P0)

- `src/casare_rpa/nodes/_index.md`
- `src/casare_rpa/presentation/canvas/visual_nodes/_index.md`
- `src/casare_rpa/domain/_index.md`
- `src/casare_rpa/presentation/canvas/_index.md`
- `.brain/_index.md`
- `.claude/rules/01-core.md`

## Knowledge Base

- Brain: `.brain/projectRules.md`, `.brain/systemPatterns.md`
- Rules: `.claude/rules/`
- Docs: `docs/`

## Commit Message Format

```
<type>: <short description>

Types: feat, fix, refactor, test, docs, chore
```

## Small Change Exception

Skip docs phase for <50 line changes (UI fixes, typos, small refactor). Use prefix:
- `fix(ui):` - UI behavior fix
- `chore(typo):` - Typo correction
