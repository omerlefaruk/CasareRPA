# RandomNumberNode

Generate a random number within a specified range.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.random_nodes`
**File:** `src\casare_rpa\nodes\random_nodes.py:38`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `min_value` | INPUT | No | DataType.FLOAT |
| `max_value` | INPUT | No | DataType.FLOAT |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `result` | OUTPUT | DataType.FLOAT |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `integer_only` | BOOLEAN | `False` | No | Generate integers only (default: False) |

## Inheritance

Extends: `BaseNode`
