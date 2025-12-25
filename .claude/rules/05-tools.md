---
description: Tool usage guidelines
---

# Tool Usage

## Local Tools (Preferred)
- Read files with `read`; edit with `edit`; create with `write`.
- List directories with `list`; find files with `rg --files`; search contents with `rg`.
- Run commands with `bash` only when needed (tests, linters, build steps).

## Search Order (Token-Optimized)
- **Known symbol**: Use `cclsp.find_definition` (LSP) for go-to-definition, accurate positions.
- **Unknown concept**: Use `search_codebase(query, top_k=...)` (MCP via ChromaDB) for "find code by meaning".
- **Find references**: Use `cclsp.find_references` to find all symbol usages.
- **Rename**: Use `cclsp.rename_symbol` for safe refactoring.
- **Exact string**: Fall back to `rg` for exact matches and `rg --files` for filenames.
- Index/rebuild: `python scripts/index_codebase.py`
- cclsp config: `.claude/cclsp.json` (Python pylsp, TypeScript typescript-language-server)

## MCP Servers
- Config: `.opencode/mcp_config.json` and `.claude/cclsp.json`
- Core local servers:
  - `cclsp`: LSP integration (go-to-definition, find-references, rename, diagnostics)
  - `filesystem`: safe file operations within allowed roots.
  - `git`: inspect and manipulate the Git repository.
  - `codebase`: semantic search via ChromaDB.
- Optional external-context servers (when needed): `exa`, `ref`, `playwright`, `sequential-thinking`.
- Always use MCP servers when the task matches the capability.

### cclsp Tools
| Tool | Purpose |
|------|---------|
| `find_definition` | Jump to symbol definitions |
| `find_references` | Find all usages across workspace |
| `rename_symbol` | Rename by symbol name |
| `rename_symbol_strict` | Rename at specific position |
| `get_diagnostics` | Error/warning checking |
| `restart_server` | Restart LSP servers |

## Claude Mirror
- Keep the Claude mirror synced via `python scripts/sync_claude_dir.py`.
- Never edit the mirror directly; treat it as generated.

## Safety
- Never hardcode secrets in configs; use environment variables (e.g., `${EXA_API_KEY}`).
- Avoid destructive commands unless explicitly requested.
