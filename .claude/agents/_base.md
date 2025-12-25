# Agent Base Template

**Parent:** `.claude/agents/_index.md` | **Last Updated:** 2025-12-25

All agents follow a common structure for consistency and token efficiency.

## Standard Frontmatter

```yaml
---
name: agent-name
description: One-line description of purpose
model: opus|sonnet|haiku
context-scope: [current] | [current, rules] | [current, patterns]
---
```

**Fields:**
- `name`: Agent identifier (used in Task() calls)
- `description`: What this agent does
- `model`: Preferred Claude model (opus=complex, sonnet=balanced, haiku=fast)
- `context-scope`: What .brain files to load on startup

## Context-Scope Values

| Scope | Loads | Use When |
|-------|-------|----------|
| `[current]` | current.md only | Testing, simple tasks |
| `[current, rules]` | current.md + projectRules.md | Implementation |
| `[current, patterns]` | current.md + systemPatterns.md | Architecture, design |

## Standard Sections

### 1. .brain Protocol (REQUIRED)

All agents must include:

```markdown
## .brain Protocol (Token-Optimized)

On startup, read:
- `.brain/context/current.md` - Active session state (~25 lines)
```

**Optional additions:**
- `projectRules.md` - For coding standards (builder, refactor)
- `systemPatterns.md` - For architecture patterns (architect)
- Existing tests - For patterns (quality)

### 2. Semantic Search (RECOMMENDED)

```markdown
## Semantic Search (Internal Codebase)

Use `search_codebase()` MCP tool:
search_codebase("query", top_k=5)
```

### 3. Core Architecture (RECOMMENDED)

```markdown
## Core Architecture

Three applications:
- **Canvas** (Designer): `presentation/canvas/`
- **Robot** (Executor): `infrastructure/robot/`
- **Orchestrator** (Manager): `infrastructure/orchestrator/`

Clean DDD Layers:
- `domain/` - Pure logic, NO external dependencies
- `application/` - Use cases
- `infrastructure/` - External adapters
- `presentation/` - UI
```

### 4. Agent-Specific Content (REQUIRED)

Each agent defines its own:
- Expertise areas
- Coding standards
- Workflow/modes
- Tool usage patterns

## Agent Workflow Chains

```
Feature:   explore → architect → builder → quality → reviewer
Bug fix:   explore → builder → quality → reviewer
Refactor:  explore → refactor → quality → reviewer
Research:  explore → researcher → docs
UI:        explore → ui → quality → reviewer
Security:  explore → security-auditor → reviewer
```

## Quick Reference

| Agent | Context-Scope | Specializes In |
|-------|---------------|----------------|
| architect | `[current, patterns]` | System design, planning |
| builder | `[current, rules]` | Code implementation |
| quality | `[current]` | Testing, performance |
| reviewer | `[current]` | Code review gate |
| docs | `[current]` | Documentation |
| ui | `[current]` | PySide6/Qt widgets |
| refactor | `[current, rules]` | Code improvement |
| integrations | `[current]` | External APIs |
| researcher | `[current]` | Investigation |
| explore | `[current]` | Codebase search |
