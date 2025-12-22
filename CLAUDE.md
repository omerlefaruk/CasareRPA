# CLAUDE.md

This repository is configured for MCP-enabled AI coding (Claude Code / OpenCode / Codex-style agents).

## Required Reading (Project Rules)

- `AGENTS.md` (repo-wide conventions)
- `AGENT.md` (agent identity + lifecycle)
- `.agent/workflows/opencode_lifecycle.md` (5-phase workflow)
- `.agent/rules/` (coding standards, enforcement, tools)

## MCP Servers

MCP servers are defined in `./.mcp.json`.

### Installed/Configured Servers

- `filesystem` (Node, via `npx`) — safe file operations within the allowed repo roots.
- `git` (Python, via `mcp-server-git`) — Git repository inspection and operations.
- `sequential-thinking` (Node, via `npx`) — structured reasoning/thought sequencing.

Other optional servers may also be configured (e.g., `exa`, `context7`, `ref`, `playwright`).

### One-Time Setup

The Git MCP server is Python-based and must be installed:

- `python -m pip install mcp-server-git`

Node-based MCP servers are launched via `npx` from `.mcp.json` and do not require committing any Node dependencies to this repo.

### Quick Sanity Checks

Run these from the repo root to verify the MCP servers can start:

- `npx -y @modelcontextprotocol/server-filesystem .`
- `python -m mcp_server_git --repository . --help`
- `npx -y @modelcontextprotocol/server-sequential-thinking`

### Client Notes

Some MCP clients read repo-local `.mcp.json` automatically; others require you to copy the server definitions into a user-level config. Use `.mcp.json.example` as a starting point.

## Security

- Do not commit API keys or tokens.
- Prefer environment variables (e.g., `${EXA_API_KEY}`, `${CONTEXT7_API_KEY}`) for MCP server credentials.
