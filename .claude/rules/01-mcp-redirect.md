# MCP Rules System

CasareRPA rules are served on-demand via MCP server for token efficiency.

## Usage
```python
# Get core non-negotiables
get_rules(category="core", urgency="critical")

# Get workflow rules
get_rules(category="workflow", urgency="normal")

# Auto-detect from task
get_rules(user_prompt="Implement a new browser automation node")

# List all available rules
list_rules()
```

## Categories
| Category | Description |
|----------|-------------|
| `core` | Index-first, domain purity, enforcement, tools |
| `workflow` | 5-phase workflow, gates |
| `nodes` | Modern Node Standard 2025, registration |
| `ui` | Theme, popup, signals |
| `testing` | Organization, fixtures, standards |

## Urgency Levels
| Level | Tokens | Description |
|-------|--------|-------------|
| `critical` | ~300 | Non-negotiable rules only |
| `normal` | ~800 | Standard rules for category |
| `optional` | ~2000 | Full rules with references |

## Server Location
`src/casare_rpa/infrastructure/rules_server/`

## Rule Files
`.claude/rules_mcp/` - XML-formatted rules (30-40% token savings)
