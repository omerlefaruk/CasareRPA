---
name: agent-invoker
description: Quick reference for invoking the 11 CasareRPA agents. Shows agent names, capabilities, and example Task tool invocations.
license: MIT
compatibility: opencode
metadata:
  audience: developers
  workflow: agent-chaining
---

Quick reference for invoking CasareRPA agents via the Task tool.

## IMPORTANT: Agent Name Mapping

The Task tool uses **system agent names**, not custom names. Always use the system name:

| Custom Name | System subagent_type | Purpose |
|-------------|---------------------|---------|
| `explore` | `Explore` | Fast codebase search |
| `plan` | `Plan` | Architecture planning |
| `architect` | `rpa-engine-architect` | Implementation + system design |
| `quality` | `chaos-qa-engineer` | Testing + performance |
| `reviewer` | `code-security-auditor` | Code review gate |
| `security` | `security-architect` | Security audits |
| `docs` | `rpa-docs-writer` | Documentation |
| `refactor` | `rpa-refactoring-engineer` | Code cleanup |
| `ui` | `rpa-ui-designer` | Canvas UI design |
| `integrations` | `rpa-integration-specialist` | External APIs |
| `researcher` | `rpa-research-specialist` | Research |
| `pm` | `mvp-product-manager` | Product scope |

## Agent Catalog

| Agent | Purpose | Model |
|-------|---------|-------|
| `explore` | Fast codebase search | haiku |
| `reviewer` | MANDATORY code review gate | sonnet |
| `architect` | Implementation + system design | opus |
| `quality` | Testing + performance | sonnet |
| `security` | All security concerns | sonnet |
| `researcher` | Research + competitive analysis | sonnet |
| `docs` | Documentation | sonnet |
| `refactor` | Code cleanup | opus |
| `ui` | Canvas UI design | opus |
| `integrations` | External API integration | sonnet |
| `pm` | Product scope management | sonnet |

## Invocation Patterns

### Exploration (Read-Only)

```python
# Quick file search (uses system name: Explore)
Task(subagent_type="Explore", prompt="""
Find all files matching pattern: src/**/*node*.py
Focus: Browser automation nodes
""")

# Code search
Task(subagent_type="Explore", prompt="""
Search for: "async def execute"
Scope: src/casare_rpa/nodes/
Return: File paths and line numbers
""")
```

### Implementation Flow

```python
# Step 1: Architect implements (system: rpa-engine-architect)
Task(subagent_type="rpa-engine-architect", prompt="""
Implement HTTPRequestNode for browser automation.
- Location: src/casare_rpa/nodes/browser/
- Follow BaseNode pattern
- Include proper error handling
""")

# Step 2: Quality tests (system: chaos-qa-engineer)
Task(subagent_type="chaos-qa-engineer", prompt="""
mode: test
Create test suite for HTTPRequestNode.
Cover: success, errors, edge cases.
Location: tests/nodes/browser/test_http_node.py
""")

# Step 3: MANDATORY Review (system: code-security-auditor)
Task(subagent_type="code-security-auditor", prompt="""
Review HTTPRequestNode implementation:
- src/casare_rpa/nodes/browser/http_node.py
- tests/nodes/browser/test_http_node.py

Output: APPROVED or ISSUES (with file:line references)
""")
```

### Review Loop Pattern

```python
# If reviewer returns ISSUES, fix and re-review:

# architect fixes
Task(subagent_type="rpa-engine-architect", prompt="""
Fix reviewer issues:
1. src/http_node.py:45 - Add timeout handling
2. src/http_node.py:78 - Fix type hint

Re-submit for review after fixing.
""")

# quality re-runs tests
Task(subagent_type="chaos-qa-engineer", prompt="""
mode: test
Re-run tests after fixes.
Verify all pass.
""")

# reviewer re-reviews
Task(subagent_type="code-security-auditor", prompt="""
Re-review after fixes:
- src/casare_rpa/nodes/browser/http_node.py
- tests/nodes/browser/test_http_node.py
""")
```

### Parallel Execution

```python
# Launch multiple independent tasks in parallel
Task(subagent_type="Explore", prompt="Find browser node patterns...")
Task(subagent_type="Explore", prompt="Find test fixtures...")
Task(subagent_type="Explore", prompt="Find similar implementations...")

# Or mix different agents (use system names!)
Task(subagent_type="rpa-engine-architect", prompt="Implement feature A...")
Task(subagent_type="rpa-docs-writer", prompt="Document feature B...")
Task(subagent_type="chaos-qa-engineer", prompt="Test feature C...")
```

### Specialized Agents

```python
# Security audit (system: security-architect)
Task(subagent_type="security-architect", prompt="""
Audit credential handling in Robot executor.
Focus: secrets, sandboxing, input validation.
""")

# Research (system: rpa-research-specialist)
Task(subagent_type="rpa-research-specialist", prompt="""
Compare UiPath vs CasareRPA selector strategies.
Recommend approach for desktop automation.
""")

# UI Design (system: rpa-ui-designer)
Task(subagent_type="rpa-ui-designer", prompt="""
Design properties panel for IfNode.
Include: condition editor, true/false labels.
""")

# Performance (system: chaos-qa-engineer with mode)
Task(subagent_type="chaos-qa-engineer", prompt="""
mode: perf
Profile workflow execution for 100-node workflows.
Identify bottlenecks.
""")

# Refactoring (system: rpa-refactoring-engineer)
Task(subagent_type="rpa-refactoring-engineer", prompt="""
Break up MainWindow (1200 lines) into focused controllers.
Follow controller pattern from systemPatterns.md.
""")
```

## Agent Modes

### Quality Agent Modes (chaos-qa-engineer)

```python
# Testing mode (default)
Task(subagent_type="chaos-qa-engineer", prompt="mode: test\n...")

# Performance mode
Task(subagent_type="chaos-qa-engineer", prompt="mode: perf\n...")

# Stress testing mode
Task(subagent_type="chaos-qa-engineer", prompt="mode: stress\n...")
```

## Common Mistakes

### Wrong

```python
# Don't skip the reviewer
Task(subagent_type="architect", prompt="Implement and merge...")  # NO!

# Don't use wrong agent for task
Task(subagent_type="docs", prompt="Fix this bug...")  # Use architect!

# Don't forget .brain protocol
Task(subagent_type="architect", prompt="Just implement...")  # Missing context!
```

### Right

```python
# Always follow the flow: architect -> quality -> reviewer
# Always reference .brain/ for context
# Use explore for research, architect for implementation
```

## Quick Lookup

| Task | Agent |
|------|-------|
| Find files/code | `explore` |
| Implement feature | `architect` |
| Design system | `architect` |
| Write tests | `quality` |
| Performance testing | `quality` (mode: perf) |
| Code review | `reviewer` |
| Security audit | `security` |
| Write docs | `docs` |
| Refactor code | `refactor` |
| Design UI | `ui` |
| API integration | `integrations` |
| Scope management | `pm` |
| Competitive research | `researcher`
