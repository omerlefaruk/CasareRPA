# IncrementVariableNode

Increment variable node - increments a numeric variable.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.variable_nodes`
**File:** `src\casare_rpa\nodes\variable_nodes.py:296`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `variable_name` | INPUT | No | DataType.STRING |
| `increment` | INPUT | No | DataType.FLOAT |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `value` | OUTPUT | DataType.FLOAT |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `variable_name` | STRING | `-` | Yes | Name of the variable to increment |
| `increment` | FLOAT | `1.0` | No | Amount to increment by |

## Inheritance

Extends: `BaseNode`
