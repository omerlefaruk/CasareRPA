# GetVariableNode

Get variable node - retrieves a value from the execution context.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.variable_nodes`
**File:** `src\casare_rpa\nodes\variable_nodes.py:202`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `variable_name` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `value` | OUTPUT | DataType.ANY |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `variable_name` | STRING | `-` | Yes | Name of the variable to get |
| `default_value` | ANY | `-` | No | Default value if variable not found |

## Inheritance

Extends: `BaseNode`
