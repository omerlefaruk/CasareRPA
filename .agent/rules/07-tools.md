---
description: Tool usage guidelines
---

# Tool Usage

## Local Tools (Preferred)
- Read files with `read`; edit with `edit`; create with `write`.
<<<<<<< HEAD
- List directories with `list`; find files with `glob`; search contents with `grep`.
=======
- List directories with `list`; find files with `rg --files`; search contents with `rg`.
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
- Run commands with `bash` only when needed (tests, linters, build steps).

## Search Order (Token-Optimized)
- Prefer semantic search first: `search_codebase(query, top_k=...)` (MCP via ChromaDB) for "find code by meaning".
<<<<<<< HEAD
- Fall back to `grep` for exact strings and `glob` for filenames/patterns.
=======
- Index/rebuild: `python scripts/index_codebase.py`
- MCP server: `python scripts/chroma_search_mcp.py`
- Fall back to `rg` for exact strings and `rg --files` for filenames/patterns.
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e

## MCP Servers
- MCP servers are configured in `.mcp.json` at repo root.
- Core local servers:
  - `filesystem`: safe file operations within allowed roots.
  - `git`: inspect and manipulate the Git repository.
  - `sequential-thinking`: structured step-by-step reasoning.
<<<<<<< HEAD
- Optional external-context servers (when needed): `exa`, `context7`, `ref`, `playwright`.
=======
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
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e

## Safety
- Never hardcode secrets in configs; use environment variables (e.g., `${EXA_API_KEY}`).
- Avoid destructive commands unless explicitly requested.
