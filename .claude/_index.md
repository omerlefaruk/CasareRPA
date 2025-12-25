# Claude Code Configuration

Claude Code configuration for CasareRPA. Official format with optimized model assignments.

## Directory Structure

```
.claude/
├── agents/              # 10 specialized agents (opus/sonnet/haiku)
├── commands/            # Slash commands
├── rules/               # Development rules and patterns
├── skills/              # 10 reusable capabilities (gerund naming)
├── workflows/           # Multi-step processes
└── _index.md            # This file
```

## Agents (Model-Optimized)

All agents use official YAML frontmatter with `allowed-tools`:

| Agent | Model | Purpose |
|-------|-------|---------|
| architect | opus | System design |
| builder | sonnet | Code implementation |
| docs | haiku | Documentation |
| explore | haiku | Codebase search |
| integrations | opus | External APIs |
| quality | sonnet | Testing & QA |
| refactor | sonnet | Code cleanup |
| researcher | opus | Investigation |
| reviewer | opus | Code review gate |
| ui | sonnet | PySide6 UI |

See `@.claude/agents/_index.md` for complete list.

## Skills (Official Format)

All skills use official YAML frontmatter with gerund naming:

| Skill | Purpose |
|-------|---------|
| generating-commit-messages | Git commits |
| generating-node-templates | Node scaffolding |
| generating-tests | Test files |
| validating-workflows | Workflow validation |
| fixing-imports | Import cleanup |
| updating-changelog | Release notes |
| updating-dependencies | Package updates |
| reviewing-code | Code review format |
| updating-brain | Knowledge base |
| testing-chains | Integration tests |

See `@.claude/skills/_index.md` for complete list.

## Rules

Core development rules and patterns. See `@.claude/rules/_index.md`.

## MCP Servers

| Server | Purpose |
|--------|---------|
| codebase | Semantic search (ChromaDB) |
| exa | Web search + code context |
| filesystem | File operations |
| git | Repository operations |
| ref | API documentation |
| web-search-prime | Web results |
| zai-mcp-server | Image analysis |
| zread | GitHub repo reader |

## Hierarchical CLAUDE.md

Layer-specific rules via `@` file references:

| Layer | Reference |
|-------|-----------|
| Domain | `@src/casare_rpa/domain/CLAUDE.md` |
| Application | `@src/casare_rpa/application/CLAUDE.md` |
| Infrastructure | `@src/casare_rpa/infrastructure/CLAUDE.md` |
| Presentation | `@src/casare_rpa/presentation/CLAUDE.md` |
| Nodes | `@src/casare_rpa/nodes/CLAUDE.md` |
| Dashboard | `@monitoring-dashboard/CLAUDE.md` |

## 2025-12-25 Modernization

- Skills: Official YAML format, gerund names, third-person descriptions
- Agents: Optimized models, `allowed-tools`, color coding
- Structure: Hierarchical CLAUDE.md, `@` file-references
- Tokens: Progressive disclosure for verbose skills

## Related Files

- `CLAUDE.md` - Main agent guide (canonical)
- `.mcp.json` - MCP server configuration
