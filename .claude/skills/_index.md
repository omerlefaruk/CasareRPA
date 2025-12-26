# Skills Index

CasareRPA skills for Claude Code. Follows official Anthropic pattern with folder structure.

## Available Skills

### Folder-Based Skills (Progressive Disclosure)

| Skill | Description | Structure |
|-------|-------------|-----------|
| **test-generator** | Generate pytest test suites | `references/` for node/controller/domain tests |
| **node-template-generator** | Generate new node boilerplate | `templates/` for browser/desktop nodes |
| **workflow-validator** | Validate workflow JSON | `schemas/` for JSON schema definitions |
| **rpa-patterns** | Retry, polling, circuit breaker | `examples/` with pattern code |
| **error-recovery** | RPA error handling patterns | `examples/` with recovery strategies |
| **selector-strategies** | CSS/XPath best practices | `examples/` with selector patterns |
| **mcp-server** | MCP server development | `references/` for best practices |
| **playwright-testing** | Test browser nodes | `examples/`, `scripts/` for helpers |

### Single-File Skills (Simple)

| Skill | Description |
|-------|-------------|
| **code-reviewer** | Structured code review format |
| **commit-message-generator** | Conventional commit messages |
| **changelog-updater** | Keep a Changelog format |
| **chain-tester** | Node chain testing templates |
| **dependency-updater** | Manage Python dependencies |
| **import-fixer** | Fix imports for clean architecture |
| **brain-updater** | Update .brain/ context files |
| **agent-invoker** | Agent invocation reference |

## Skill Structure

Folder-based skills follow official Anthropic pattern:

```
skill-name/
├── SKILL.md          (ALL CAPS - main entry point, lean ~100 lines)
├── LICENSE.txt       (optional)
├── scripts/          (optional - black-box helpers)
├── references/       (optional - detailed docs loaded on demand)
├── examples/         (optional - usage examples)
└── templates/        (optional - code/file templates)
```

## Categories

| Category | Skills |
|----------|--------|
| **Testing** | test-generator, chain-tester, code-reviewer, playwright-testing |
| **Code Gen** | node-template-generator |
| **RPA Patterns** | rpa-patterns, error-recovery, selector-strategies |
| **Validation** | workflow-validator |
| **Integration** | mcp-server |
| **DevOps** | commit-message-generator, changelog-updater, dependency-updater |
| **Context** | brain-updater, agent-invoker, import-fixer |

## Token Efficiency

Progressive disclosure pattern:
- SKILL.md: ~100-150 lines (always loaded)
- references/: Loaded only when needed
- examples/: Concrete code samples

**Result**: ~67% reduction in base skill context load.

## Usage

Skills are auto-discovered by Claude Code:

```
"Use the test-generator skill to create tests for ClickNode"
"Use the rpa-patterns skill for retry logic"
"Use the selector-strategies skill for robust CSS selectors"
```

## Cross-References

| Topic | See Also |
|-------|----------|
| Agent definitions | `../agents/_index.md` |
| Commands | `../commands/_index.md` |
| Node templates | `.brain/docs/node-templates.md` |

---

*Parent: [../_index.md](../_index.md)*
*Last updated: 2025-12-26*
