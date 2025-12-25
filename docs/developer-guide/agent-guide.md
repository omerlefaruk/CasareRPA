# Agent Guide

Comprehensive guide for using agents and skills in CasareRPA.

## Overview

CasareRPA supports a **dual-agent system** compatible with both **OpenCode** and **Claude** AI assistants. This guide covers:

- Available agents and their purposes
- Skill templates for common tasks
- How to invoke agents and skills
- Best practices for agent orchestration

## Agent System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CasareRPA Agent System                │
├─────────────────────────────────────────────────────────┤
│  Dual Compatibility: OpenCode + Claude                   │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   OpenCode  │  │   Claude    │  │   Shared    │    │
│  │   .opencode │  │   .claude   │  │   .agent/   │    │
│  │   format    │  │   format    │  │   canonical │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │              MCP-First Standard                  │  │
│  │  codebase → sequential-thinking → filesystem     │  │
│  └─────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Available Agents

Agents are specialized AI assistants for specific tasks. See `.agent/agents/` for definitions.

### Primary Agents

| Agent | Path | Purpose |
|-------|------|---------|
| `builder` | `.agent/agents/builder.md` | Code writing (follows KISS & DDD) |
| `docs` | `.agent/agents/docs.md` | Documentation generation |
| `quality` | `.agent/agents/quality.md` | Testing and performance |
| `reviewer` | `.agent/agents/reviewer.md` | Code review gate |

### Specialized Agents

| Agent | Path | Purpose |
|-------|------|---------|
| `architect` | `.agent/agents/architect.md` | Implementation and system design |
| `explorer` | `.agent/agents/explorer.md` | Fast codebase exploration |
| `integrations` | `.agent/agents/integrations.md` | External system integrations |
| `node-creator` | `.agent/agents/node-creator.md` | New automation nodes |
| `refactor` | `.agent/agents/refactor.md` | Code cleanup and modernization |
| `ui-specialist` | `.agent/agents/ui-specialist.md` | UI/UX design |
| `workflow-expert` | `.agent/agents/workflow-expert.md` | AI-powered RPA workflows |

### Research & Analysis

| Agent | Path | Purpose |
|-------|------|---------|
| `researcher` | `.agent/agents/researcher.md` | Technical research and competitive analysis |
| `playwright` | `.agent/agents/playwright.md` | Browser automation investigations |

## Available Skills

Skills are reusable task templates. They can be invoked via the Skill tool.

### Development Skills

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `node-template-generator.md` | "Generate node template" | Generate node scaffolding |
| `test-generator.md` | "Generate tests" | Generate test files |
| `import-fixer.md` | "Fix imports" | Fix import statements |
| `refactor.md` | "Refactor" | Code refactoring |

### Quality Skills

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `code-reviewer.md` | "Review code" | Automated code review |
| `workflow-validator.md` | "Validate workflow" | Validate workflow files |
| `chain-tester.md` | "Test chain" | Test agent chains |
| `security-auditor.md` | "Security audit" | Security audits |
| `performance.md` | "Performance" | Performance optimization |

### Documentation Skills

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `brain-updater.md` | "Update brain" | Update .brain/ files |
| `changelog-updater.md` | "Update changelog" | Update changelog |

### Operations Skills

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `commit-message-generator.md` | "Generate commit" | Generate commit messages |
| `dependency-updater.md` | "Update deps" | Update dependencies |
| `agent-invoker.md` | "Invoke agent" | Invoke agents |
| `ci-cd.md` | "CI/CD" | CI/CD pipeline management |

### Integration Skills

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `explorer.md` | "Explore" | Codebase exploration |
| `integrations.md` | "Integrations" | External integrations |
| `error-doctor.md` | "Error doctor" | Debug and fix errors |
| `ui-specialist.md` | "UI specialist" | UI/UX development |

## How to Use Agents

### Using the Task Tool

Agents are invoked via the Task tool:

```python
Task(
    subagent_type="builder",
    description="Implement feature X",
    prompt="Implement feature X following DDD patterns..."
)
```

### Agent Workflow

All agents follow the **5-phase workflow**:

```
1. Research  → Explore codebase, gather requirements
2. Plan      → Design solution, create plan
3. Execute   → Implement code
4. Validate  → Run tests, verify functionality
5. Docs      → Update documentation
```

### Feature Lifecycle

```
Plan → Review Plan → Tests First → Implement → Code Review → QA → Docs
```

If any errors appear, loop back to the appropriate step until clean.

## How to Use Skills

### Using the Skill Tool

Skills are invoked via the Skill tool:

```python
Skill(skill="node-template-generator")
Skill(skill="test-generator")
Skill(skill="explorer")
```

### Skill Parameters

Skills accept parameters as keyword arguments:

```python
Skill(
    skill="node-template-generator",
    category="browser",
    name="Click Element"
)
```

## Best Practices

### MCP-First Standard

Always use MCP servers in this order:

1. **`codebase`** - Semantic code search (use FIRST for unknown concepts)
2. **`sequential-thinking`** - Complex reasoning or multi-step planning
3. **`filesystem`** - view_file/write files
4. **`git`** - Inspect history, diffs, branches
5. **`exa`** - Web research
6. **`ref`** - Library documentation

### Index-First

Before searching or grepping, read relevant `_index.md` files:

- `.agent/rules/_index.md`
- `.agent/rules/01-core.md`
- `src/casare_rpa/*/_index.md`
- `docs/_index.md`

### Parallel Operations

Launch independent reads and searches in parallel:

```python
# Good: Parallel reads
read("src/casare_rpa/domain/entities/base_node.py")
read("src/casare_rpa/nodes/browser/browser_base.py")

# Bad: Sequential reads
read("src/casare_rpa/domain/entities/base_node.py")
read("src/casare_rpa/nodes/browser/browser_base.py")
```

### Interactive Status

Always state current phase and progress:

```
Phase: Execute
- In progress: Implementing Click node
- Completed: Research, Plan, Review Plan
- Next: Tests First
```

## Agent Invocation Examples

### New Feature Implementation

```python
# 1. Research phase
Task(subagent_type="explorer", description="Research click patterns", prompt="Find all click-related node implementations...")

# 2. Plan phase
Task(subagent_type="architect", description="Design click node", prompt="Design a new browser click node...")

# 3. Review plan
Task(subagent_type="reviewer", description="Review plan", prompt="Review the architect's plan...")

# 4. Tests first
Task(subagent_type="quality", description="Create tests", prompt="Create tests for the new click node...")

# 5. Implement
Task(subagent_type="builder", description="Implement click node", prompt="Implement the click node...")

# 6. Code review
Task(subagent_type="reviewer", description="Review implementation", prompt="Review the implementation...")

# 7. QA
Task(subagent_type="quality", description="Run tests", prompt="Run all tests for the click node...")

# 8. Docs
Task(subagent_type="docs", description="Update docs", prompt="Update documentation for the new click node...")
```

### Code Refactoring

```python
Task(
    subagent_type="refactor",
    description="Refactor old nodes",
    prompt="Refactor legacy nodes to use the modern @properties pattern..."
)
```

### Performance Optimization

```python
Task(
    subagent_type="performance",
    description="Profile execution",
    prompt="Profile the workflow execution and identify bottlenecks..."
)
```

## File Locations

| Purpose | Path |
|---------|------|
| Agent definitions | `.agent/agents/` |
| Agent rules | `.agent/rules/` |
| Skills | `.claude/skills/` |
| OpenCode skills | `.opencode/skill/<name>/SKILL.md` |
| Knowledge base | `.brain/` |
| MCP config | `.mcp.json` |

## See Also

- [MCP Guide](mcp-guide.md) - MCP server usage
- [Development Guide](../developer-guide/index.md) - Project development
- [Architecture](../developer-guide/architecture/index.md) - System architecture
- [Testing](../developer-guide/contributing/testing.md) - Testing patterns
