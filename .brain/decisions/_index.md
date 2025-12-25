# Decision Trees Index

Quick navigation for common development tasks.

## Available Decision Trees

| Task | File | When to Use |
|------|------|-------------|
| **Add a Node** | [add-node.md](add-node.md) | Creating new automation nodes |
| **Add a Feature** | [add-feature.md](add-feature.md) | Adding UI, API, or business logic |
| **Fix a Bug** | [fix-bug.md](fix-bug.md) | Debugging crashes, wrong output, UI issues |
| **Modify Execution** | [modify-execution.md](modify-execution.md) | Changing workflow execution flow |

## Quick Decision Matrix

```
What do you need to do?
│
├─ Add something new?
│   ├─ New node for automation → add-node.md
│   ├─ New UI widget/panel → add-feature.md#step-1
│   ├─ New API integration → add-feature.md#step-2
│   └─ New business rule → add-feature.md#step-3
│
├─ Fix something broken?
│   ├─ App crashes → fix-bug.md#step-1
│   ├─ Wrong output → fix-bug.md#step-2
│   ├─ UI not updating → fix-bug.md#step-3
│   └─ Slow performance → fix-bug.md#step-4
│
├─ Modify existing behavior?
│   ├─ Change execution order → modify-execution.md
│   ├─ Add retry/error handling → modify-execution.md#error-handling
│   └─ Change event flow → modify-execution.md#events
│
└─ Refactor/cleanup?
    └─ See .brain/projectRules.md for standards
```

## Common Starting Points

### "I need to add a new node that..."

1. Read [add-node.md](add-node.md)
2. Check `nodes/_index.md` for similar nodes
3. Use template from `.brain/docs/node-templates-core.md` (or data/services)

### "I need to fix a bug where..."

1. Read [fix-bug.md](fix-bug.md)
2. Find the error type in the decision tree
3. Follow debugging steps

### "I need to integrate with external API..."

1. Read [add-feature.md#step-2](add-feature.md#step-2)
2. Create infrastructure client
3. Create domain protocol
4. Create node that uses client

### "I need to change how workflows execute..."

1. Read [modify-execution.md](modify-execution.md)
2. Understand current flow in `domain/services/`
3. Check event handlers in `application/handlers/`

---

## Related Documentation

| Topic | File |
|-------|------|
| Symbol lookup | `.brain/symbols.md` |
| System patterns | `.brain/systemPatterns.md` |
| Coding standards | `.brain/projectRules.md` |
| Error catalog | `.brain/errors.md` |
| Dependencies | `.brain/dependencies.md` |

## Used By

| Command/Agent | Uses Decision Tree |
|---------------|-------------------|
| `/implement-feature` | add-feature.md |
| `/implement-node` | add-node.md |
| `/fix-feature` | fix-bug.md |
| `architect` agent | All trees for planning |
| `explore` agent | Navigation reference |

---

*Parent: [../_index.md](../_index.md)*
*Referenced from: CLAUDE.md, agent-rules/commands/, .claude/commands/*
*Last updated: 2025-12-14*
