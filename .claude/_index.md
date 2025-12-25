# Claude Code Configuration

This directory contains the Claude Code configuration for CasareRPA, migrated from `.opencode/` with enhanced features.

## Directory Structure

```
.claude/
├── agents/              # 18 specialized agents
├── commands/            # Slash commands including /chain
├── rules/               # Development rules and patterns
├── skills/              # 18 reusable capabilities
├── workflows/           # Multi-step processes
├── context-optimization.md   # Token optimization strategy
├── claude-minimal.json       # Minimal mode config (~2KB)
├── claude-standard.json      # Standard mode config (~10KB)
├── claude-full.json          # Full mode config (~30KB)
└── _index.md                 # This file
```

## Token Optimization Modes

Switch between modes using the mode switcher script:

```bash
# Check current status
python scripts/switch_claude_mode.py status

# Switch to minimal mode (fastest)
python scripts/switch_claude_mode.py minimal

# Switch to standard mode (balanced, default)
python scripts/switch_claude_mode.py standard

# Switch to full mode (maximum context)
python scripts/switch_claude_mode.py full
```

| Mode | Tokens | Use Case |
|------|--------|----------|
| **minimal** | ~2KB | Quick sessions, debugging |
| **standard** | ~10-12KB | Normal development |
| **full** | ~30KB+ | Deep research, documentation |

## New Agents (from .opencode)

| Agent | Description |
|-------|-------------|
| `ci-cd` | CI/CD pipelines and GitHub Actions |
| `code-reviewer` | Code review with APPROVED/ISSUES format |
| `docs-writer` | Documentation writing specialist |
| `ui-specialist` | PySide6 UI development specialist |
| `test-generator` | Test generation with tier-based approach |
| `general` | General purpose fallback |
| `pm` | Project management and effort estimation |

See [agents/_index.md](agents/_index.md) for the complete agent list.

## New Rules (from .opencode)

| Rule | Purpose |
|------|---------|
| `00-minimal.md` | Minimal core instructions for low-token mode |
| `13-agent-chaining.md` | Basic agent chaining with loop-based error recovery |
| `14-agent-chaining-enhanced.md` | Enhanced features (ML, dynamic loops, cost optimization) |

See [rules/_index.md](rules/_index.md) for the complete rule list.

## New Command

| Command | Description |
|---------|-------------|
| `/chain` | Automatic agent chaining with error recovery loops |

## Skills

All skills have been restructured into subdirectories with `SKILL.md` format:

```
skills/
├── agent-invoker/
├── brain-updater/
├── chain-tester/
├── ci-cd/
├── error-doctor/       # NEW
├── performance/        # NEW
├── ui-specialist/      # NEW
└── ...
```

See [skills/_index.md](skills/_index.md) for the complete skill list.

## MCP Servers

The following MCP servers are configured in `.mcp.json`:

| Server | Purpose |
|--------|---------|
| `codebase` | Semantic search via ChromaDB |
| `filesystem` | File operations |
| `git` | Git repository operations |
| `glob` | File pattern matching |
| `exa` | Web search |
| `ref` | API documentation lookup |
| `sequential-thinking` | Complex reasoning (disabled) |

## Migration Notes

- Migrated from `.opencode/` on 2025-12-25
- All agents now have proper YAML frontmatter
- Skills restructured to use subdirectories with `{name}.md` files
- Added token optimization modes with switching capability
- AGENTS.md is the canonical source; CLAUDE.md is synced via `scripts/sync_agent_guides.py`

## Related Files

- `CLAUDE.md` - Main agent guide (synced from AGENTS.md)
- `.mcp.json` - MCP server configuration
- `scripts/switch_claude_mode.py` - Mode switcher script
