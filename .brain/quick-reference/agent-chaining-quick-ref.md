# Agent Chaining Quick Reference

**Last Updated**: 2025-12-25 | **Version**: 1.0

---

## Command Syntax

```bash
/chain <task-type> "<description>" [options]
```

---

## Task Types & Chains

| Task Type | Chain | When to Use |
|-----------|-------|-------------|
| **implement** | explore → architect → builder → quality → reviewer | New features, components |
| **fix** | explore → builder → quality → reviewer | Bug fixes, error resolution |
| **research** | explore → researcher | Investigation, analysis |
| **refactor** | explore → refactor → quality → reviewer | Code cleanup, optimization |
| **extend** | explore → architect → builder → quality → reviewer | Add features to existing |
| **clone** | explore → builder → quality → reviewer | Duplicate patterns |
| **test** | explore → quality → reviewer | Add/verify tests |
| **docs** | explore → docs → reviewer | Documentation |
| **ui** | explore → ui → quality → reviewer | UI components, widgets |
| **integration** | explore → integrations → quality → reviewer | External APIs |
| **security** | explore → security → reviewer | Security audits |

---

## Options

| Option | Example | Description |
|--------|---------|-------------|
| `--parallel=agents` | `--parallel=docs,security` | Run in parallel |
| `--priority=level` | `--priority=high` | high, normal, low |
| `--max-iterations=n` | `--max-iterations=5` | Max loop count |
| `--timeout=seconds` | `--timeout=900` | Agent timeout |
| `--dry-run` | `--dry-run` | Preview only |
| `--skip-review` | `--skip-review` | Skip reviewer |

---

## Examples

```bash
# Implement new feature
/chain implement "OAuth2 authentication node"

# Fix a bug (high priority)
/chain fix "Null pointer in workflow loader" --priority=high

# Research a topic
/chain research "AI integration patterns for RPA"

# Refactor legacy code
/chain refactor "Clean up HTTP client"

# Add tests
/chain test "Edge case tests for Click node"

# Update documentation
/chain docs "API reference for HTTP nodes"

# UI work
/chain ui "New file picker widget"

# Integration
/chain integration "Google Sheets API"

# Security audit
/chain security "OAuth2 security review"
```

---

## Loop Recovery

When `reviewer` returns `ISSUES`:
1. System auto-loops back to fix issues
2. Max 3 iterations by default
3. Issues are categorized and routed:
   - **Type errors** → `builder`
   - **Logic errors** → `architect`
   - **Security issues** → `security`
   - **Style issues** → `refactor`
4. If max iterations reached → Human escalation

---

## Parallel Execution

**Can run together:**
- `explore` + `docs`
- `explore` + `security`
- `quality` + `docs`
- `quality` + `security`

**Must run alone:**
- `builder` (sequential)
- `reviewer` (must be last)

---

## Status Commands

```bash
/chain status              # View running chains
/chain status <id>         # View specific chain
/chain history             # Recent chains
/chain kill <id>           # Cancel chain
/chain resume <id>         # Resume stuck chain
```

---

## Quick Selection Guide

```
What's the task?

├─ Create something new?
│  └─ /chain implement "..."
│
├─ Fix a bug?
│  └─ /chain fix "..."
│
├─ Investigate/research?
│  └─ /chain research "..."
│
├─ Clean up code?
│  └─ /chain refactor "..."
│
├─ Add to existing?
│  └─ /chain extend "..."
│
├─ Add tests?
│  └─ /chain test "..."
│
├─ Write docs?
│  └─ /chain docs "..."
│
├─ UI work?
│  └─ /chain ui "..."
│
├─ Connect external API?
│  └─ /chain integration "..."
│
└─ Security review?
   └─ /chain security "..."
```

---

## Files Reference

| File | Purpose |
|------|---------|
| `.agent/rules/13-agent-chaining.md` | Full chaining guide |
| `.brain/plans/agent-chaining-master-plan.md` | Detailed plan |
| `.brain/context/current.md` | Active session state |

---

## Chain Execution Flow

```
START
  │
  ▼
EXPLORE ──► ARCHITECT ──► BUILDER ──► QUALITY ──► REVIEWER
  │         │           │           │           │
  │         │           │           │           │
  │         │           │           │     ┌─────┴─────┐
  │         │           │           │     │           │
  │         │           │           │  APPROVED   ISSUES
  │         │           │           │     │           │
  │         │           │           │     ▼           ▼
  │         │           │           │    DONE     LOOP BACK
  │         │           │           │                   │
  │         │           │           │                   │
  │         │           │           │    Max iterations?───�Yes──► HUMAN
  │         │           │           │         │ No           ESCALATION
  │         │           │           │         ▼
  │         │           │           │    Fix & Retry
  │         │           │           │         │
  │         │           │           │         └────────────►
  │         │           │           │
  │         │           │           │
  ▼         ▼           ▼           ▼
END
```

---

## Tips

1. **Always start with EXPLORE** - Finds existing patterns
2. **Use parallel when possible** - Speeds up execution
3. **Don't skip REVIEWER** - Quality gate is mandatory
4. **Set appropriate priority** - High priority = tighter timeouts
5. **Check chain status** - Monitor progress during execution
6. **Use --dry-run first** - Preview chain before execution
