---
description: Index of OpenCode slash commands for CasareRPA
---

# OpenCode Commands

This directory contains OpenCode slash commands for CasareRPA development.

## Available Commands

| Command | Description |
|---------|-------------|
| `/chain` | Execute automatic agent chaining with loop-based error recovery |
| `/implement-feature` | Implement a new feature with full agent orchestration |
| `/implement-node` | Implement a new automation node |
| `/fix-feature` | Fix bugs and issues in existing features |

## Usage

```bash
# Execute a chain with task type and description
/chain implement "Add OAuth2 authentication for Google APIs"

/chain fix "Null pointer in workflow loader"

/chain refactor "Clean up legacy HTTP client code"

# With options
/chain implement "New feature" --parallel=security --max-iterations=5
```

## See Also

- `.opencode/rules/13-agent-chaining.md` - Agent chaining guide
- `.opencode/rules/14-agent-chaining-enhanced.md` - Enhanced chaining features
- `.claude/commands/` - Claude Code commands
