---
description: Tool usage guidelines
---

# Tool Usage

## Local Tools (Preferred)
- Read files with `read`; edit with `edit`; create with `write`.
- List directories with `list`; find files with `glob`; search contents with `grep`.
- Run commands with `bash` only when needed (tests, linters, build steps).

## Search Order (Token-Optimized)
- Prefer semantic search first: `search_codebase(query, top_k=...)` (MCP via ChromaDB) for "find code by meaning".
- Fall back to `grep` for exact strings and `glob` for filenames/patterns.

## MCP Servers
- MCP servers are configured in `.mcp.json` at repo root.
- Core local servers:
  - `filesystem`: safe file operations within allowed roots.
  - `git`: inspect and manipulate the Git repository.
  - `sequential-thinking`: structured step-by-step reasoning.
- Optional external-context servers (when needed): `exa`, `context7`, `ref`, `playwright`.

## Safety
- Never hardcode secrets in configs; use environment variables (e.g., `${EXA_API_KEY}`).
- Avoid destructive commands unless explicitly requested.
