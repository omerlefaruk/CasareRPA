---
description: Tool usage guidelines
---

# Tool Usage

## Local Tools (Preferred)
- Read files with `read`; edit with `edit`; create with `write`.
- List directories with `list`; find files with `rg --files`; search contents with `rg`.
- Run commands with `bash` only when needed (tests, linters, build steps).

## Search Order (Token-Optimized)
- Prefer semantic search first: `search_codebase(query, top_k=...)` (MCP via ChromaDB) for "find code by meaning".
- Index/rebuild: `python scripts/index_codebase.py`
- MCP server: `python scripts/chroma_search_mcp.py`
- Fall back to `rg` for exact strings and `rg --files` for filenames/patterns.

## MCP Servers
- MCP servers are configured in `.mcp.json` at repo root.
- Core local servers:
  - `filesystem`: safe file operations within allowed roots.
  - `git`: inspect and manipulate the Git repository.
  - `sequential-thinking`: structured step-by-step reasoning.
  - `codebase`: semantic search via ChromaDB.
- Optional external-context servers (when needed): `exa`, `ref`, `playwright`.
- Always use MCP servers when the task matches the capability (filesystem for file reads/writes, git for repo ops, sequential-thinking for multi-step planning, exa/ref for research, playwright for browser automation).

## Claude Mirror
- Keep the Claude mirror synced via `python scripts/sync_claude_dir.py`.
- Never edit the mirror directly; treat it as generated.
- Optional: `python scripts/sync_claude_dir.py --link` to create junctions/symlinks.

## Agent-Rules Mirror
- Keep `agent-rules/` synced via `python scripts/sync_agent_rules.py`.
- Never edit `agent-rules/` directly; treat it as generated.

## Safety
- Never hardcode secrets in configs; use environment variables (e.g., `${EXA_API_KEY}`).
- Avoid destructive commands unless explicitly requested.
