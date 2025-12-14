# .brain/docs Index

Technical documentation and development guides.

## Node Development

| File | Purpose | When to Use |
|------|---------|-------------|
| [node-templates.md](node-templates.md) | Full node implementation templates | Creating new nodes |
| [node-checklist.md](node-checklist.md) | Step-by-step node checklist | Verify node implementation |
| [super-node-pattern.md](super-node-pattern.md) | Super Node consolidation pattern | Multi-action nodes |
| [trigger-checklist.md](trigger-checklist.md) | Trigger node checklist | Creating trigger nodes |

## UI Development

| File | Purpose | When to Use |
|------|---------|-------------|
| [ui-standards.md](ui-standards.md) | UI/UX standards and patterns | PySide6 widget development |
| [widget-rules.md](widget-rules.md) | Widget implementation rules | Creating custom widgets |

## Testing & Quality

| File | Purpose | When to Use |
|------|---------|-------------|
| [tdd-guide.md](tdd-guide.md) | Test-driven development guide | Writing tests first |

## Qdrant Semantic Search

| File | Purpose | When to Use |
|------|---------|-------------|
| [QDRANT_INDEX.md](QDRANT_INDEX.md) | Qdrant system overview | Understanding semantic search |
| [QDRANT_DOCS_README.md](QDRANT_DOCS_README.md) | Qdrant documentation guide | Setup and usage |
| [QDRANT_UNDERSTANDING.md](QDRANT_UNDERSTANDING.md) | Deep dive into Qdrant | Architecture details |
| [qdrant-quick-reference.md](qdrant-quick-reference.md) | Quick command reference | Daily usage |
| [qdrant-debugging.md](qdrant-debugging.md) | Troubleshooting guide | Fixing search issues |

## Quick Reference

### For Node Developers
1. Start with [node-checklist.md](node-checklist.md)
2. Use templates from [node-templates.md](node-templates.md)
3. For multi-action nodes, see [super-node-pattern.md](super-node-pattern.md)

### For UI Developers
1. Read [ui-standards.md](ui-standards.md) first
2. Follow rules in [widget-rules.md](widget-rules.md)
3. Check `.claude/rules/ui/theme-rules.md` for theming

### For Test Writers
1. Follow [tdd-guide.md](tdd-guide.md)
2. Run: `pytest tests/ -v`

## Cross-References

| Topic | Also See |
|-------|----------|
| Node creation workflow | [../decisions/add-node.md](../decisions/add-node.md) |
| UI patterns | `.claude/rules/ui/` |
| Testing patterns | `agent-rules/agents/quality.md` |
| Architecture | [../systemPatterns.md](../systemPatterns.md) |

---

*Parent: [../_index.md](../_index.md)*
*Last updated: 2025-12-14*
