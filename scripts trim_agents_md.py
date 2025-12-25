#!/usr/bin/env python3
"""Trim AGENTS.md to essentials to reduce token usage."""

AGENTS_TEMPLATE = """# CasareRPA Agent Guide

Windows RPA platform | Python 3.12 | PySide6 | Playwright | DDD 2025 architecture

## Quick Commands
```bash
pytest tests/ -v && ruff check src/ && black src/ tests/
python scripts/index_codebase.py && python scripts/chroma_search_mcp.py
python scripts/create_plan.py "feature" && python scripts/create_worktree.py "branch"
python run.py && python manage.py canvas
```

## Tech Stack
- Python 3.12+, PySide6 6.6.0+, NodeGraphQt 0.6.30+
- Playwright 1.50.0, FastAPI 0.109.0, Pydantic 2.6.0+
- Loguru 0.7.2, ChromaDB 0.4.0 (semantic search)

## Core Rules (Non-Negotiable)
| Rule | Description |
|------|-------------|
| index-first | Read _index.md before grep/glob |
| parallel | Launch independent reads in one block |
| worktrees-only | Never work on main/master |
| search-before-create | Check existing nodes/registries |
| no-silent-failures | Wrap external calls in try/except, log with loguru |
| domain-purity | Domain layer has no external deps or I/O |
| async-first | No blocking I/O in async; use qasync in Qt |
| http | Use UnifiedHttpClient, never raw aiohttp/httpx |
| theme-only | No hardcoded hex colors; use THEME constants |
| signal-slot | @Slot required; no lambdas; use functools.partial |
| nodes | Use @properties + get_parameter(); no self.config.get() |
| ports | Use add_exec_input()/add_exec_output() for exec; DataType for data |
| events | Typed domain events only via EventBus; pass serializable data |
| security | Never hardcode secrets; use env/credential store |

## 5-Phase Workflow
**RESEARCH → PLAN → EXECUTE → VALIDATE → DOCS**

| Phase | Gate | Agents |
|-------|------|--------|
| RESEARCH | Required | explore, researcher |
| PLAN | User approval | architect |
| EXECUTE | After approval | builder, ui, integrations, refactor |
| VALIDATE | Blocking loop | quality → reviewer (APPROVED/ISSUES) |
| DOCS | Required | docs |

## DDD Architecture
```
src/casare_rpa/
├── domain/         # Pure logic, entities, aggregates, events (NO deps)
├── application/    # Use cases, queries (CQRS)
├── infrastructure/ # Persistence, HTTP, adapters
└── presentation/   # Qt UI, coordinators
```

## Modern Node Standard (2025)
```python
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
        url = self.get_parameter("url")  # port → config fallback
        timeout = self.get_parameter("timeout", 30000)
```

## Typed Events (DDD 2025)
```python
from casare_rpa.domain.events import NodeCompleted, get_event_bus
bus = get_event_bus()
bus.publish(NodeCompleted(node_id="x", node_type="Y", execution_time_ms=100))
```

## Key Indexes (P0)
- `src/casare_rpa/nodes/_index.md`
- `src/casare_rpa/domain/_index.md`
- `.brain/_index.md`

## Knowledge Base
| Source | Description |
|--------|-------------|
| `.brain/` | projectRules.md, systemPatterns.md, errors.md, docs/ |
| `.opencode/rules/` | Core rules (primary) |
| `docs/` | Developer, user, security docs |

## Git Workflow
- Create worktree: `python scripts/create_worktree.py "feature-name"`
- Guardrail: `python scripts/check_not_main_branch.py`

## Commit Format
```
<type>: <short description>
Types: feat, fix, refactor, test, docs, chore
```

## Maintenance Automation

### Token Optimization (Monthly)
```bash
# Archive old .brain/analysis files
python scripts/archive_brain_analysis.py

# Archive completed plans (older than 30 days)
python scripts/archive_old_plans.py --days=30

# Trim AGENTS.md to essentials
python scripts/trim_agents_md.py

# Rebuild codebase index
python scripts/index_codebase.py
```

### MCP Server Audit (Quarterly)
Review `.mcp.json` and disable unused servers.

### Rules Cleanup (Monthly)
Review `opencode.json` - keep only essential 5-6 files.

---
*Last updated: {date} | See .brain/docs/ for full templates*
"""


def trim_agents_md() -> None:
    """Rewrite AGENTS.md with lean content."""
    from datetime import date

    content = AGENTS_TEMPLATE.format(date=date.today().isoformat())
    Path("AGENTS.md").write_text(content)
    print(f"Trimmed AGENTS.md to {len(content)} chars")


if __name__ == "__main__":
    trim_agents_md()
