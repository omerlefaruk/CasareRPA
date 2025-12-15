---
description: Node development workflow and templates
---

# Node Workflow

## Plan -> Search -> Implement

**Always follow this workflow for nodes:**

1. **PLAN**: Define atomic operation (one node = one responsibility)
2. **SEARCH**: Check existing nodes first (`src/casare_rpa/nodes/_index.md`, `NODE_REGISTRY`)
3. **IMPLEMENT**: Use existing -> Modify existing -> Create new (last resort)

## Node Categories

| Category | Path | Description |
|----------|------|-------------|
| Browser | `src/casare_rpa/nodes/browser/` | Web automation (Playwright) |
| Desktop | `src/casare_rpa/nodes/desktop_nodes/` | Windows UI automation |
| File | `src/casare_rpa/nodes/file/` | File system operations |
| Data | `src/casare_rpa/nodes/data/` | Data transformation |
| Flow | `src/casare_rpa/nodes/control_flow/` | Control flow |
| Google | `src/casare_rpa/nodes/google/` | Google services |
| HTTP | `src/casare_rpa/nodes/http/` | HTTP/API calls |

## Port Rules

- Use add_exec_input()/add_exec_output() - NEVER add_input_port(name, PortType.EXEC_*)
- Data ports: add_input_port(name, DataType.*)
- One node = one atomic operation

## Registration

1. Add to nodes/{category}/__init__.py
2. Register in `NODE_REGISTRY` (`src/casare_rpa/nodes/registry_data.py`)
3. Add visual node to `src/casare_rpa/presentation/canvas/visual_nodes/{category}/`
4. Register in `src/casare_rpa/presentation/canvas/visual_nodes/__init__.py`
