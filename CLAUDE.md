# CasareRPA

Windows Desktop RPA platform with visual node-based workflow editor.

**Stack**: Python 3.12 | PySide6 | Playwright | NodeGraphQt | DDD Clean Architecture

## Rules Reference

Rules are modularized in `.claude/rules/`. All `.md` files are auto-loaded.

| Topic | File |
|-------|------|
| Role & Philosophy | `00-role.md` |
| 5-Phase Workflow | `01-workflow.md` |
| Coding Standards | `02-coding-standards.md` |
| Architecture | `03-architecture.md` |
| Agent Registry | `04-agents.md` |
| Workflow Triggers | `05-triggers.md` |
| Enforcement | `06-enforcement.md` |
| MCP Tools | `07-mcp-tools.md` |
| Token Optimization | `08-token-optimization.md` |
| Brain Protocol | `09-brain-protocol.md` |

### Path-Specific Rules
| Scope | File |
|-------|------|
| Node development | `nodes/node-registration.md` |
| UI/Presentation | `ui/theme-rules.md` |

## Commands

```bash
python run.py          # Run application
pytest tests/ -v       # Run tests
pip install -e .       # Install in dev mode
```

## Documentation

Detailed docs in `.brain/`:
- `projectRules.md` - Full coding standards
- `systemPatterns.md` - Architecture patterns
- `docs/` - Implementation checklists

## Quick Start

1. Read `.brain/context/current.md` for session state
2. Rules auto-load from `.claude/rules/`
3. Follow 5-phase workflow: RESEARCH -> PLAN -> EXECUTE -> VALIDATE -> DOCS
