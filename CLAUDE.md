# CasareRPA

Windows RPA platform | Python 3.12 | PySide6 | Playwright | DDD Clean Architecture

## Quick Commands
```bash
python run.py          # Run app
pytest tests/ -v       # Tests
pip install -e .       # Dev install
```

## Core Rules (Non-Negotiable)

1. **INDEX-FIRST**: Read `_index.md` before grep/glob. See `.claude/rules/01-core.md`
2. **PARALLEL**: Launch independent agents/reads in ONE message block
3. **SEARCH BEFORE CREATE**: Check existing code before writing new
4. **NO SILENT FAILURES**: Wrap external calls in try/except, use loguru
5. **THEME.* ONLY**: No hardcoded colors - use `presentation/canvas/ui/theme.py`
6. **UnifiedHttpClient**: No raw httpx/aiohttp

## DDD Layers
| Layer | Path | Dependencies |
|-------|------|--------------|
| Domain | `domain/` | None |
| Application | `application/` | Domain |
| Infrastructure | `infrastructure/` | Domain, App |
| Presentation | `presentation/` | All |

## Key Indexes (P0 - Always Check First)
- `nodes/_index.md` - Node registry
- `presentation/canvas/visual_nodes/_index.md` - Visual nodes
- `domain/_index.md` - Core entities
- `.brain/context/current.md` - Session state

## Rules Reference
| Topic | File |
|-------|------|
| Core workflow & standards | `.claude/rules/01-core.md` |
| Architecture & agents | `.claude/rules/02-architecture.md` |
| Node development | `.claude/rules/03-nodes.md` |

### Path-Specific (auto-loaded)
| Scope | File |
|-------|------|
| UI/Presentation | `.claude/rules/ui/theme-rules.md` |
| Node files | `.claude/rules/nodes/node-registration.md` |

## On-Demand Docs (Load When Needed)
- `.brain/docs/node-templates.md` - Full node templates
- `.brain/docs/node-checklist.md` - Node implementation steps
- `.brain/projectRules.md` - Full coding standards
- `.brain/systemPatterns.md` - Architecture patterns
