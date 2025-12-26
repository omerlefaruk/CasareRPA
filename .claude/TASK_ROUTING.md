# Task Routing Guide

Quick reference for routing tasks to agents and skills. **Auto-chain is enabled by default** for all primary agents.

## Task → Agent → Skill Routing

| Task Type | Agent | Skills Used | Auto-Chain |
|-----------|-------|-------------|------------|
| **Implement feature** | `architect` | node-template-generator, mcp-server | Full chain |
| **Design system** | `architect` | rpa-patterns | Full chain |
| **Add node** | `architect` | node-template-generator | Full chain |
| **Fix bug** | `builder` | commit-message-generator | quality → reviewer |
| **Refactor code** | `refactor` | import-fixer | Full chain |
| **Design UI** | `ui` | rpa-patterns, selector-strategies | Full chain |
| **API integration** | `integrations` | mcp-server | Full chain |
| **Write tests** | `quality` | test-generator | reviewer |
| **Code review** | `reviewer` | code-reviewer | None (gate) |
| **Research only** | `researcher` | - | None |
| **Explore codebase** | `explore` | - | None |
| **Write docs** | `docs` | - | None |

## Quick Invocation

### For Implementation (Auto-Chains Full Workflow)
```python
Task(subagent_type="architect", prompt="Implement login feature")
# Runs: EXPLORE×3 → ARCHITECT → BUILDER+UI+INTEGRATIONS → QUALITY+DOCS → REVIEWER
```

### For Bug Fixes (Auto-Chains Quality+Reviewer)
```python
Task(subagent_type="builder", prompt="Fix null pointer in auth module")
# Runs: BUILDER → QUALITY → REVIEWER
```

### For Refactoring
```python
Task(subagent_type="refactor", prompt="Extract common validation logic")
# Runs: EXPLORE → REFACTOR → QUALITY → REVIEWER
```

### For UI Design
```python
Task(subagent_type="ui", prompt="Design settings dialog with dark theme")
# Runs: EXPLORE → UI → QUALITY → REVIEWER
```

### For API Integrations
```python
Task(subagent_type="integrations", prompt="Integrate with Slack API")
# Runs: EXPLORE → INTEGRATIONS → QUALITY → REVIEWER
```

## Skill-Only Invocations

For specialized tasks, invoke skills directly:

| Skill | Usage |
|-------|-------|
| `test-generator` | Generate test suites |
| `code-reviewer` | Structured code review |
| `commit-message-generator` | Generate commit messages |
| `node-template-generator` | Generate node boilerplate |
| `import-fixer` | Fix import violations |
| `mcp-server` | Build MCP servers |
| `rpa-patterns` | RPA workflow patterns |
| `selector-strategies` | Element selector strategies |
| `workflow-validator` | Validate workflow JSON |
| `playwright-testing` | Browser testing patterns |
| `brain-updater` | Update .brain/ context |
| `changelog-updater` | Update CHANGELOG.md |

### Direct Skill Invocation
```python
Skill(skill="test-generator", args="node: ScreenshotCaptureNode")
Skill(skill="commit-message-generator", args="")
Skill(skill="import-fixer", args="src/casare_rpa/nodes/browser/")
```

## Skip Auto-Chain (Single Agent Mode)

Add `single=true` to run just the agent without chaining:

```python
Task(subagent_type="architect", prompt="single=true: Just review this design")
Task(subagent_type="builder", prompt="single=true: Write only this one function")
```

## Command Invocations

### Chain Command (Full Control)
```bash
/chain implement "Add OAuth2 support" --parallel --priority=high
/chain fix "Memory leak in browser pool" --max-iterations=5
/chain refactor "Extract validation layer"
```

### Parallel Exec (Auto-Decomposition)
```python
Skill(skill="parallel-exec", args="Implement login with UI, backend, tests")
```

## Agent Capability Matrix

| Agent | Implementation | Design | Testing | Review | Refactor | UI | Integration |
|-------|----------------|--------|---------|--------|----------|-----|-------------|
| `architect` | ✅ | ✅ | - | - | - | - | - |
| `builder` | ✅ | - | - | - | - | - | - |
| `refactor` | - | - | - | - | ✅ | - | - |
| `ui` | - | ✅ | - | - | - | ✅ | - |
| `integrations` | ✅ | - | - | - | - | - | ✅ |
| `quality` | - | - | ✅ | - | - | - | - |
| `reviewer` | - | - | - | ✅ | - | - | - |
| `explore` | - | - | - | - | - | - | - |
| `docs` | - | - | - | - | - | - | - |
| `researcher` | - | ✅ | - | - | - | - | - |

## Parallel Execution Phases

### Architect Chain (Most Parallel)
```
Phase 1: EXPLORE×3 (codebase, tests, docs) - PARALLEL
Phase 2: ARCHITECT (plan) - SEQUENTIAL
Phase 3: BUILDER + UI + INTEGRATIONS - PARALLEL
Phase 4: QUALITY + DOCS - PARALLEL
Phase 5: REVIEWER - GATE (loops if ISSUES)
```

### Builder Chain (Fast)
```
Phase 1: BUILDER - SEQUENTIAL
Phase 2: QUALITY - SEQUENTIAL
Phase 3: REVIEWER - GATE
```

### Refactor Chain
```
Phase 1: EXPLORE - SEQUENTIAL
Phase 2: REFACTOR - SEQUENTIAL
Phase 3: QUALITY - SEQUENTIAL
Phase 4: REVIEWER - GATE
```

## Error Recovery Loop

All chains with REVIEWER gate automatically loop on ISSUES:

```
Iteration 1: BUILDER → QUALITY → REVIEWER (ISSUES: 2)
    ↓ Loop back to BUILDER
Iteration 2: BUILDER → QUALITY → REVIEWER (APPROVED)
✓ Complete
```

Max iterations: 3 (configurable via `--max-iterations`)

## Choosing the Right Agent

| Your Task | Use Agent |
|-----------|-----------|
| "Implement X" | `architect` |
| "Add feature X" | `architect` |
| "Design X" | `architect` |
| "Fix bug X" | `builder` |
| "Write code for X" | `builder` |
| "Clean up X" | `refactor` |
| "Restructure X" | `refactor` |
| "Design UI for X" | `ui` |
| "Create dialog X" | `ui` |
| "Integrate with X API" | `integrations` |
| "Connect to X service" | `integrations` |
| "Write tests for X" | `quality` |
| "Review this code" | `reviewer` |
| "Find files like X" | `explore` |
| "Document X" | `docs` |
| "Research X" | `researcher` |
