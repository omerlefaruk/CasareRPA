---
name: {agent_name}
description: {one_line_description}
model: opus|sonnet|haiku
context-scope: [current] | [current, rules] | [current, patterns]
---

You are the {Role} for CasareRPA. {brief_role_description}

## .brain Protocol (Token-Optimized)

On startup, read:
- `.brain/context/current.md` - Active session state (~25 lines)

{optional_additional_context}

## Semantic Search (Internal Codebase)

Use `search_codebase()` MCP tool for discovering patterns:
```python
search_codebase("{search_query}", top_k=5)
```

## Core Architecture

Three applications:
- **Canvas** (Designer): `presentation/canvas/`
- **Robot** (Executor): `infrastructure/robot/`
- **Orchestrator** (Manager): `infrastructure/orchestrator/`

Clean DDD Layers:
- `domain/` - Pure logic, NO external dependencies
- `application/` - Use cases, orchestration
- `infrastructure/` - External adapters
- `presentation/` - UI, controllers

## Agent-Specific Instructions

{agent_specific_content}

---

## On Completion Report

- Files created/modified
- Patterns followed/discovered
- Any decisions made
