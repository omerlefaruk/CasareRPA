---
description: Minimal bootstrap instructions (for low-token sessions/configs)
paths:
  - .claude/claude-minimal.json
  - .claude/claude-standard.json
  - .claude/claude-full.json
---

# Minimal Bootstrap

**Use only when MCP rules server is unavailable.**

## If MCP Works
Use `get_rules(category="core", urgency="critical")` for full rules.

## Non-Negotiables (Fallback)
- **INDEX-FIRST**: Read _index.md before grep/glob
- **DOMAIN PURITY**: Domain: no external imports
- **NO SECRETS**: Never commit credentials

## Fallback Path
1. Read @docs/agent/_index.md
2. Read relevant module _index.md
3. Check @.brain/decisions/ for patterns
4. Proceed with task

## Categories
- `get_rules(category="core")` - Core rules
- `get_rules(category="workflow")` - 5-phase workflow
- `get_rules(category="nodes")` - Node development
- `get_rules(category="ui")` - UI development
- `get_rules(category="testing")` - Testing standards
