# .claude/agents Index

Agent definitions for Claude Code. Full versions in `agent-rules/agents/`.

## Available Agents

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| [architect.md](architect.md) | System design | Implementation plans, cross-component features |
| [builder.md](builder.md) | Code implementation | Writing features after planning |
| [docs.md](docs.md) | Documentation | API docs, guides, error dictionaries |
| [explore.md](explore.md) | Codebase navigation | Finding files, patterns, architecture |
| [integrations.md](integrations.md) | External services | APIs, databases, cloud, auth |
| [quality.md](quality.md) | Testing & QA | Unit tests, perf testing, stress tests |
| [refactor.md](refactor.md) | Code improvement | DRY, patterns, modernization |
| [researcher.md](researcher.md) | Investigation | Library comparison, competitor analysis |
| [reviewer.md](reviewer.md) | Code review | Quality gate, approval/issues |
| [ui.md](ui.md) | UI development | PySide6/Qt widgets, panels |

## Agent Workflow Chains

Standard chains for different tasks:

```
Feature: explore → architect → builder → quality → reviewer
Bug fix: explore → builder → quality → reviewer
Refactor: explore → refactor → quality → reviewer
Research: explore → researcher → docs
```

## Usage Pattern

```python
# In Claude Code:
Task(subagent_type="explore", prompt="Find authentication code")
Task(subagent_type="architect", prompt="Design login feature")
Task(subagent_type="builder", prompt="Implement login per plan")
```

## Cross-References

| Topic | See Also |
|-------|----------|
| Full agent details | `agent-rules/agents/` |
| Agent workflow rules | `agent-rules/rules/04-agents.md` |
| Command workflows | `.claude/commands/` |

---

*Parent: [../_index.md](../_index.md)*
*Full reference: [../../agent-rules/agents/](../../agent-rules/agents/)*
*Last updated: 2025-12-14*
