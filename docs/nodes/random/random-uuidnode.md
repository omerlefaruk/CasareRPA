# RandomUUIDNode

Generate a random UUID.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.random_nodes`
**File:** `src\casare_rpa\nodes\random_nodes.py:318`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `result` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `version` | INTEGER | `4` | No | UUID version (4 for random, 1 for time-based) (default: 4) Choices: 1, 4 |
| `format` | CHOICE | `standard` | No | Output format - 'standard', 'hex', 'urn' (default: standard) Choices: standard, hex, urn |

## Inheritance

Extends: `BaseNode`
