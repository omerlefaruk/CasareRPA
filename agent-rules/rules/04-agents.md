# Agent Registry

Specialized agents for different task types.

## Available Agents

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| `architect` | System design | New features, refactoring |
| `builder` | Implementation | Writing code |
| `docs` | Documentation | README, docstrings |
| `explore` | Codebase navigation | Understanding code |
| `integrations` | External services | APIs, databases |
| `quality` | Testing, QA | Test writing, review |
| `refactor` | Code improvement | Performance, cleanup |
| `researcher` | Investigation | Bugs, requirements |
| `reviewer` | Code review | PR review |
| `ui` | UI development | PySide6 widgets |

## Agent Selection
1. Identify task type
2. Load agent prompt from `agent-rules/agents/{agent}.md`
3. Follow agent-specific guidelines

## Multi-Agent Workflows
For complex tasks, chain agents:
1. `researcher` → Understand problem
2. `architect` → Design solution
3. `builder` → Implement
4. `quality` → Test
5. `reviewer` → Review
