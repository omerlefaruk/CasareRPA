---
name: agent-invoker
description: Quick reference for invoking CasareRPA agents via Task tool.
---

# Agent Invoker

Reference for invoking CasareRPA agents.

## Agent Catalog

| Agent | System Name | Purpose |
|-------|-------------|---------|
| `explore` | `Explore` | Fast codebase search |
| `architect` | `rpa-engine-architect` | Implementation + design |
| `builder` | `rpa-engine-architect` | Code writing |
| `quality` | `chaos-qa-engineer` | Testing + performance |
| `reviewer` | `code-security-auditor` | Code review gate |
| `refactor` | `rpa-refactoring-engineer` | Code cleanup |
| `researcher` | `rpa-research-specialist` | Research |
| `docs` | `rpa-docs-writer` | Documentation |
| `ui` | `rpa-ui-designer` | Canvas UI design |
| `integrations` | `rpa-integration-specialist` | External APIs |

## Invocation Patterns

### Exploration

```python
Task(subagent_type="Explore", prompt="""
Find all files matching pattern: src/**/*node*.py
Focus: Browser automation nodes
""")
```

### Implementation Flow

```python
# 1. Architect implements
Task(subagent_type="rpa-engine-architect", prompt="""
Implement HTTPRequestNode for browser automation.
- Location: src/casare_rpa/nodes/browser/
- Follow BaseNode pattern
""")

# 2. Quality tests
Task(subagent_type="chaos-qa-engineer", prompt="""
mode: test
Create test suite for HTTPRequestNode.
Cover: success, errors, edge cases.
""")

# 3. MANDATORY Review
Task(subagent_type="code-security-auditor", prompt="""
Review HTTPRequestNode implementation:
- src/casare_rpa/nodes/browser/http_node.py
- tests/nodes/browser/test_http_node.py

Output: APPROVED or ISSUES (with file:line)
""")
```

### Quality Agent Modes

```python
# Testing mode (default)
Task(subagent_type="chaos-qa-engineer", prompt="mode: test\n...")

# Performance mode
Task(subagent_type="chaos-qa-engineer", prompt="mode: perf\n...")

# Stress testing mode
Task(subagent_type="chaos-qa-engineer", prompt="mode: stress\n...")
```

## Quick Lookup

| Task | Agent |
|------|-------|
| Find files/code | `explore` |
| Implement feature | `architect` / `builder` |
| Design system | `architect` |
| Write tests | `quality` |
| Performance test | `quality` (mode: perf) |
| Code review | `reviewer` |
| Refactor code | `refactor` |
| Design UI | `ui` |
| API integration | `integrations` |
| Research | `researcher` |
| Write docs | `docs` |
