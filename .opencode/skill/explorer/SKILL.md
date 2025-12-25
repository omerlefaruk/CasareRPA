---
name: explorer
description: Codebase exploration using semantic search and MCP tools
license: MIT
compatibility: opencode
metadata:
  audience: developers
  workflow: discovery
---

## What I do

- Explore codebases using semantic search (MCP codebase)
- Find files, patterns, and implementations quickly
- Trace execution flows and dependencies
- Provide structured findings with file references

## When to use me

Use this when you need to:
- Find all implementations of a pattern
- Understand codebase structure
- Trace how a feature works
- Discover related code patterns

## ⚠️ CRITICAL: MCP-First Rule

**Always use `search_codebase` FIRST - never start with grep!**

## MCP-First Workflow

1. **codebase** - Semantic search for concepts (FIRST!)
   ```python
   search_codebase("browser automation click node patterns", top_k=10)
   ```

2. **sequential-thinking** - Plan the exploration
   ```python
   think_step_by_step("Analyze the codebase structure...")
   ```

3. **filesystem** - view_file index files first
   ```python
   read_file("src/casare_rpa/domain/_index.md")
   ```

4. **git** - Check recent changes
   ```python
   git_log("--oneline", path="src/casare_rpa/nodes/")
   ```

## MCP Tool Commands

```python
# FIRST: Semantic search for concepts (not grep!)
search_codebase("query", top_k=10)

# THEN: Follow up with specific searches
search_codebase("related concept", top_k=5)

# THEN: view_file related files
read_file("src/casare_rpa/domain/entities/base_node.py")

# THEN: Check git history
git_diff("HEAD~10..HEAD", path="src/casare_rpa/")
```

## CasareRPA Structure

```
src/casare_rpa/
├── domain/           # Core entities (BaseNode, Workflow, schemas)
├── nodes/            # Node implementations by category
│   ├── browser/      # Playwright browser nodes
│   ├── data/         # Data manipulation nodes
│   ├── file/         # File system nodes
│   ├── flow/         # Control flow nodes
│   ├── google/       # Google API nodes
│   └── ...
├── application/      # Use cases, services
├── infrastructure/   # External systems
│   ├── orchestrator/ # API server (FastAPI)
│   └── robot/        # Execution engine
└── presentation/     # PySide6 UI
    └── canvas/       # Node graph UI
```

## Key Index Files

Always read these first:
- `src/casare_rpa/domain/_index.md`
- `src/casare_rpa/nodes/_index.md`
- `src/casare_rpa/infrastructure/_index.md`
- `src/casare_rpa/presentation/_index.md`

## Common Search Queries

| Query | Purpose |
|-------|---------|
| "BaseNode execute node implementation" | Node execution patterns |
| "event bus implementation" | Event system patterns |
| "workflow execution graph" | Workflow engine |
| "OAuth2 async client" | Authentication patterns |
| "PySide6 widget dark theme" | UI patterns |
