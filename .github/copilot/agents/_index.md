````markdown
# GitHub Copilot Agent Directory

GitHub Copilot reuses the canonical agent briefs stored in `.agent/agents/`. This index maps Copilot intents to those briefs so the same responsibilities and workflows apply regardless of tooling.

| Copilot Intent | Canonical Brief |
| -------------- | --------------- |
| Architecture & planning | `.agent/agents/architect.md` |
| Feature implementation | `.agent/agents/builder.md` |
| Documentation | `.agent/agents/docs.md` |
| Code exploration | `.agent/agents/explore.md` |
| External integrations | `.agent/agents/integrations.md` |
| Testing & QA | `.agent/agents/quality.md` |
| Refactoring | `.agent/agents/refactor.md` |
| Research & comparisons | `.agent/agents/researcher.md` |
| Code review | `.agent/agents/reviewer.md` |
| UI/UX work | `.agent/agents/ui.md` |

Follow the workflow chains defined in `.agent/agents/_index.md`. Copilot does not need separate copies of each brief; refer directly to the originals to stay current when rules evolve.

---
*See also: `.github/copilot/AGENT.md` for overall configuration and `.agent/rules/04-agents.md` for workflow policies.*
````
