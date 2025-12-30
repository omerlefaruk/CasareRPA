# CasareRPA Agent Guide (Lean)

See @docs/agent/_index.md for full documentation.

## Quick Commands
```bash
pip install -e ".[dev]"
pytest tests/ -v
python run.py
python manage.py canvas
python scripts/create_worktree.py "feature-name"
```

## Start Here
- Agent docs: @docs/agent/_index.md
- Brain context: @.brain/context/current.md
- **Rules**: `get_rules(category="core")` *(MCP tool)*

## Non-Negotiable Rules
Load via `get_rules(category="core", urgency="critical")`:
- **INDEX-FIRST**: Read relevant _index.md first
- **SEARCH BEFORE CREATE**: Check existing code before writing new
- **DOMAIN PURITY**: Domain has no external dependencies
- **NO SILENT FAILURES**: Log external failures with context
- **ASYNC FIRST**: No blocking I/O in async contexts
- **HTTP**: Use UnifiedHttpClient
- **UI THEME**: No hardcoded colors (use THEME)
- **QT**: @Slot required; no lambdas
- **NODES**: Schema-driven (@properties + get_parameter)
- **EVENTS**: Typed domain events only

## MCP Fallback
If `get_rules` tool unavailable:
1. Read @.claude/rules/00-minimal.md
2. Read @docs/agent/_index.md
3. Proceed with task

## Module Indexes
- @src/casare_rpa/domain/_index.md
- @src/casare_rpa/nodes/_index.md
- @src/casare_rpa/application/_index.md
- @src/casare_rpa/infrastructure/_index.md
- @src/casare_rpa/presentation/canvas/_index.md

*Last updated: 2025-12-29 | MCP Rules v1.0*
