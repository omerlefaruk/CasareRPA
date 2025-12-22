# Agent Rules Map

This map defines the authoritative sources for agent rules and how they sync.

## Sources
| Location | Status | Purpose | Sync |
|----------|--------|---------|------|
| `.agent/` | Primary | Canonical agent rules, commands, workflows | Source of truth |
| `.claude/` | Mirror | Claude Code compatible structure | `python scripts/sync_claude_dir.py` |
| `agent-rules/` | Mirror | Reference rules for legacy tooling | `python scripts/sync_agent_rules.py` |

## Editing Rules
- Edit `.agent/` only.
- Re-sync mirrors after changes.
- Never edit `.claude/` or `agent-rules/` directly.
